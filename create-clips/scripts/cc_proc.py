"""Chunk processing commands of the create-clips toolkit: new-run, ingest, watch, status, doctor, chunks, locate, window, frame, sheet, stream-table.

The contract is ../README.md (sections 2 to 4). Gather-only: these commands measure, extract, record and tabulate; they never judge or rank.
A chunk is ingested in stages (move, probe, audio, sheets, transcript, digest); every stage is recorded in 00-inventory/chunks.json and a
finished stage is skipped on the next run, so an interrupted chunk resumes where it stopped.
"""
from __future__ import annotations

import ctypes
import json
import math
import os
import re
import shutil
import sys
import time
import traceback
from pathlib import Path

from cc_common import (CHUNK_RE, SCHEMA, FileLock, cfg_get, chunk_dir, chunk_id, chunk_to_rec, fail, ffprobe_facts, find_tool, fmt_hms,
                       free_gb, inbox_dir, load_chunks, load_config, load_state, now_iso, out, parse_time, read_json, rec_to_chunk,
                       resolve_run, run_cmd, run_paths, runs_root, say, update_state, write_json, write_text)

STAGES = ("move", "probe", "audio", "sheets", "transcript", "digest")
RUN_DIRS = ("00-inventory", "10-media", "20-analysis", "30-assets", "40-briefs", "60-outputs", "deliverables", "logs")
CHUNK_FILE_RE = re.compile(r"^chunk-(\d{4,})\.mp4$", re.I)


# --------------------------------------------------------------------------- the chunk table

def recompute_rec_starts(rows: list) -> None:
    """rec_start_s of every chunk = the sum of the real durations before it (chunks sorted by number); flags chunks whose sheets and
    text views were made with another rec start (a lower number arrived late)."""
    rows.sort(key=lambda r: r["index"])
    t = 0.0
    for r in rows:
        r["rec_start_s"] = round(t, 3)
        if r.get("duration_s"):
            t += float(r["duration_s"])
        base = r.get("rec_base_s")
        r["stale_rec"] = bool(base is not None and abs(float(base) - r["rec_start_s"]) > 1e-3)


def mutate_rows(run: Path, fn) -> list:
    """Read-modify-write of chunks.json under the lock (the same lock file cc_common.save_chunks uses); recomputes the rec starts."""
    with FileLock(Path(run) / ".chunks.lock", timeout=120):
        rows = load_chunks(run)
        fn(rows)
        recompute_rec_starts(rows)
        write_json(Path(run) / "00-inventory" / "chunks.json", rows)
    return rows


def new_row(cid: str, index: int) -> dict:
    return {"id": cid, "index": index, "file": f"10-media/{cid}/chunk.mp4", "rec_start_s": None, "duration_s": None, "t0_utc": None,
            "t1_utc": None, "gap_before_s": None, "ads_skipped_s": None, "ended_by": None, "quality": None, "stream": None,
            "status": "pending", "stages": {s: False for s in STAGES}, "sheets": None, "frames": None, "words": None,
            "speech_seconds": None, "language": None, "model": None, "device": None, "seconds": {}, "error": None,
            "processed_at": None, "rec_base_s": None, "stale_rec": False}


def put_row(run: Path, row: dict) -> dict:
    """Store `row` in the table (replacing the same id) and return the stored copy (with its current rec_start_s)."""
    def fn(rows):
        for i, r in enumerate(rows):
            if r["id"] == row["id"]:
                rows[i] = row
                return
        rows.append(row)
    rows = mutate_rows(run, fn)
    return next(r for r in rows if r["id"] == row["id"])


# --------------------------------------------------------------------------- runs

def ensure_run(session: str, channel: str, inbox_session: Path | None = None, whisper_override: dict | None = None) -> tuple:
    run = runs_root() / session
    created = not (run / "state.json").is_file()
    for d in RUN_DIRS:
        (run / d).mkdir(parents=True, exist_ok=True)
    if created:
        f = cfg_get("frames", {}) or {}
        w = cfg_get("whisper", {}) or {}
        state = {"schema": SCHEMA, "channel": channel, "session": session, "run": str(run), "created": now_iso(),
                 "inbox": str(inbox_session) if inbox_session else None,
                 "settings": {"frame_interval_s": f.get("interval_s", 0.75), "frames_per_sheet": int(f.get("cols", 5)) * int(f.get("rows", 6)),
                              "cols": f.get("cols", 5), "rows": f.get("rows", 6), "cell": [f.get("cell_w", 240), f.get("cell_h", 135)],
                              "audio_window_s": cfg_get("audio.rms_window_s", 0.5),
                              "whisper": {k: w.get(k) for k in ("model", "device", "compute_type", "language")},
                              "whisper_override": whisper_override or {}},
                 "chunks": {}, "stage": None, "next_skill": None, "videos": {}}
        write_json(run / "state.json", state)
        write_json(run / "00-inventory" / "chunks.json", [])
        write_json(run / "00-inventory" / "stream-meta.json", {"schema": SCHEMA, "channel": channel, "session": session, "per_chunk": [], "changes": []})
    return run, created


def _session_from_chunk_path(p: Path) -> tuple:
    """(session, channel, session_dir) for <inbox>/<channel>/<session>/chunk-NNNN.mp4, else (None, None, None)."""
    sd = p.parent
    if sd.parent != sd and sd.parent.parent != sd.parent and CHUNK_FILE_RE.match(p.name):
        return sd.name, sd.parent.name, sd
    return None, None, None


# --------------------------------------------------------------------------- logging

class Log:
    def __init__(self, run: Path, cid: str, mirror: bool = True):
        self.path = Path(run) / "logs" / f"ingest-{cid}.log"
        self.cid, self.mirror = cid, mirror
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def __call__(self, msg: str, show: bool = False) -> None:
        line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
        try:
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except OSError:
            pass
        if show and self.mirror:
            say(f"[{self.cid}] {msg}")


# --------------------------------------------------------------------------- ingest

def guess_index(src: Path | None, sidecar: Path | None) -> int | None:
    if src:
        m = CHUNK_FILE_RE.match(src.name)
        if m:
            return int(m.group(1))
        m = CHUNK_RE.match(src.parent.name)
        if m:
            return int(m.group(1))
    if sidecar and Path(sidecar).is_file():
        j = read_json(sidecar, {}) or {}
        if isinstance(j.get("chunk"), int):
            return int(j["chunk"])
    return None


def _apply_sidecar(row: dict, side: dict | None) -> None:
    for k in ("t0_utc", "t1_utc", "gap_before_s", "ads_skipped_s", "ended_by", "quality", "stream"):
        if side and k in side:
            row[k] = side[k]


def _outputs_ok(name: str, cdir: Path, row: dict) -> bool:
    rec0 = row.get("rec_start_s")
    if name == "move":
        return (cdir / "chunk.mp4").is_file()
    if name == "probe":
        p = read_json(cdir / "probe.json")
        return bool(p and p.get("duration_s"))
    if name == "audio":
        return (cdir / "audio.json").is_file() and (cdir / "audio-profile.json").is_file()
    if name == "sheets":
        fj = read_json(cdir / "frames.json")
        if not fj or not fj.get("frames_deleted") or fj.get("leftover_frames"):
            return False
        sheets = list((cdir / "sheets").glob("sheet-*.jpg"))
        return len(sheets) == fj.get("sheets") and (not fj.get("overview") or (cdir / "sheets" / "overview.jpg").is_file()) and \
            abs(float(fj.get("rec_start_s", 0)) - float(rec0 or 0)) < 1e-3
    if name == "transcript":
        t = read_json(cdir / "transcript.json")
        return bool(t) and (bool(t.get("engine")) or bool(t.get("note")))
    if name == "digest":
        d = read_json(cdir / "digest.json")
        return bool(d) and (cdir / "timeline.md").is_file() and (cdir / "transcript.txt").is_file() and \
            abs(float(d.get("rec_start_s", 0)) - float(rec0 or 0)) < 1e-3
    return False


def _sync_rec_fields(cdir: Path, rec0: float) -> None:
    """audio.json and transcript.json carry rec_start_s; keep them equal to the table's after a late lower chunk shifted it."""
    for fn in ("audio.json", "transcript.json"):
        j = read_json(cdir / fn)
        if j is not None and abs(float(j.get("rec_start_s", 0)) - rec0) > 1e-3:
            j["rec_start_s"] = round(rec0, 3)
            write_json(cdir / fn, j, indent=None)
    ap = read_json(cdir / "audio-profile.json")
    if ap and ap.get("loud_jumps"):
        for e in ap["loud_jumps"]:
            e["rec"] = round(rec0 + e["t"], 2)
        write_json(cdir / "audio-profile.json", ap)


def ingest_chunk(run: Path, src: Path | None, index: int | None = None, sidecar: Path | None = None, chat: Path | None = None,
                 force: bool = False, skip_whisper: bool = False, keep_wav: bool | None = None, mirror: bool = True) -> dict:
    """Ingest (or resume, or refresh) one chunk. Returns the result dict; never raises for a chunk's own failure."""
    from cc_audio import (audio_json, audio_profile, empty_transcript, extract_wav, get_transcriber, read_wav, window_levels)
    from cc_frames import build_chunk_sheets
    from cc_tables import build_digest, build_stream_md, build_stream_meta, load_data, render_timeline_md, render_transcript_txt, second_rows

    run = Path(run)
    src = Path(src) if src else None
    state = load_state(run)
    channel = state.get("channel") or "channel"
    if index is None:
        index = guess_index(src, sidecar)
    if index is None:
        return {"ok": False, "error": "cannot tell the chunk number: name the file chunk-NNNN.mp4 or pass --index", "status": None}
    cid = chunk_id(index)
    cdir = chunk_dir(run, cid)
    dest = cdir / "chunk.mp4"
    log = Log(run, cid, mirror)
    rows = load_chunks(run)
    row = next((r for r in rows if r["id"] == cid), None) or new_row(cid, index)
    if force:
        row["stages"] = {s: False for s in STAGES}
    row.setdefault("stages", {s: False for s in STAGES})
    for s in STAGES:
        row["stages"].setdefault(s, False)

    # what is still to do (outputs must exist; a stale rec start makes sheets and digest not ok)
    def todo(name):
        return not (row["stages"].get(name) is True and _outputs_ok(name, cdir, row))
    if not force and not any(todo(s) for s in STAGES if not (s == "transcript" and skip_whisper)) and row.get("status") == "done":
        return {"ok": True, "chunk": cid, "status": "done", "already_done": True, "skipped": list(STAGES), "seconds": {}}
    min_free = float(os.environ.get("CC_MIN_FREE_GB") or cfg_get("min_free_gb", 3))
    fg = free_gb(run)
    if fg < min_free:
        log(f"refused: {fg} GB free on the runs drive, below min_free_gb {min_free}", show=True)
        return {"ok": False, "chunk": cid, "refused": f"free space {fg} GB is below min_free_gb {min_free}", "free_gb": fg, "status": row.get("status")}

    row["status"] = "processing"
    row = put_row(run, row)
    update_state(run, **{f"chunks.{cid}": {"status": "processing"}})
    secs, skipped, errors = {}, [], []
    wav = cdir / "audio-16k.wav"
    log(f"ingest start (force={force}, skip_whisper={skip_whisper}) src={src}", show=True)

    def run_stage(name, fn, needs_ok=True) -> bool:
        nonlocal row
        if not todo(name):
            skipped.append(name)
            return True
        t0 = time.time()
        try:
            note = fn()
            row["stages"][name] = True
            secs[name] = round(time.time() - t0, 1)
            log(f"stage {name}: ok in {secs[name]} s" + (f" ({note})" if note else ""), show=True)
            ok = True
        except Exception as e:  # noqa: BLE001
            row["stages"][name] = f"failed: {type(e).__name__}: {str(e)[:240]}"
            secs[name] = round(time.time() - t0, 1)
            errors.append(f"{name}: {type(e).__name__}: {str(e)[:200]}")
            log(f"stage {name}: FAILED {type(e).__name__}: {e}\n{traceback.format_exc()[-1200:]}", show=True)
            ok = False
        row = put_row(run, row)
        return ok

    # ---- move
    def do_move():
        side_src = sidecar or (src.with_name(f"chunk-{index:04d}.json") if src else None)
        chat_src = chat or (src.with_name(f"chat-{index:04d}.json") if src else None)
        if not dest.is_file():
            if not src or not src.is_file():
                raise FileNotFoundError(f"no chunk file to move ({src})")
            cdir.mkdir(parents=True, exist_ok=True)
            try:
                os.replace(src, dest)                  # the inbox and the runs are on one drive: a rename, no copy
            except PermissionError:
                raise                                   # the file is still open elsewhere: this stage fails, the watcher tries again later
            except OSError:                             # another drive: copy to a .part file, rename it, then drop the source
                need = src.stat().st_size / 1e9 + min_free
                if free_gb(run) < need:
                    raise RuntimeError("the inbox and the runs are on different drives and there is no room to copy the chunk")
                part = dest.with_name("chunk.mp4.part")
                try:
                    shutil.copyfile(src, part)
                    os.replace(part, dest)
                finally:
                    part.unlink(missing_ok=True)
                try:
                    src.unlink()
                except OSError:
                    log(f"copied the chunk but could not delete {src}", show=True)
                row["moved_by_copy"] = True
        elif src and src.is_file() and src.resolve() != dest.resolve():
            log(f"duplicate: {dest} already exists, the file {src} is left where it is", show=True)
        cdir.mkdir(parents=True, exist_ok=True)
        for s_path, name in ((side_src, "chunk.json"), (chat_src, "chat.json")):
            if s_path and Path(s_path).is_file() and (force or not (cdir / name).is_file()):
                shutil.copyfile(s_path, cdir / name)
        if src and (src.parent / "session.json").is_file():
            shutil.copyfile(src.parent / "session.json", run / "00-inventory" / "session.json")
        _apply_sidecar(row, read_json(cdir / "chunk.json"))
        return "moved by copy" if row.get("moved_by_copy") else None

    run_stage("move", do_move)
    if not row["stages"]["move"] is True:
        return _finish(run, row, secs, skipped, errors, state, log)

    # ---- probe
    def do_probe():
        p = ffprobe_facts(dest)
        if not p.get("duration_s") or not p.get("has_video"):
            raise RuntimeError("ffprobe found no readable video duration (a corrupt or empty file)")
        write_json(cdir / "probe.json", p)
        row["duration_s"] = p["duration_s"]
        return f"{p['duration_s']} s {p.get('width')}x{p.get('height')} {p.get('fps')} fps"
    run_stage("probe", do_probe)
    if row["stages"]["probe"] is not True:
        return _finish(run, row, secs, skipped, errors, state, log)
    probe = read_json(cdir / "probe.json", {})
    row["duration_s"] = probe["duration_s"]
    row = put_row(run, row)                       # now every chunk after this one has its rec start shifted if need be
    rec0 = float(row["rec_start_s"] or 0.0)
    duration = float(row["duration_s"])
    _sync_rec_fields(cdir, rec0)
    win = float(cfg_get("audio.rms_window_s", 0.5))
    wcfg_override = (state.get("settings") or {}).get("whisper_override") or {}
    kw = keep_wav if keep_wav is not None else bool(cfg_get("audio.keep_wav", False))

    # ---- audio
    def do_audio():
        if not probe.get("has_audio"):
            write_json(cdir / "audio.json", audio_json(rec0, win, [], [], no_audio=True), indent=None)
            write_json(cdir / "audio-profile.json", audio_profile([], [], win, rec0))
            row["no_audio"] = True
            return "no audio track"
        r = extract_wav(dest, wav)
        if not r["ok"]:
            raise RuntimeError(f"audio extraction failed: {r['error']}")
        samples, rate = read_wav(wav)
        rms, peak = window_levels(samples, rate, win)
        write_json(cdir / "audio.json", audio_json(rec0, win, rms, peak), indent=None)
        write_json(cdir / "audio-profile.json", audio_profile(rms, peak, win, rec0))
        return f"{len(rms)} windows"
    run_stage("audio", do_audio)

    # ---- sheets (frames are deleted as each sheet is saved)
    def do_sheets():
        audio = read_json(cdir / "audio.json")
        chat_j = read_json(cdir / "chat.json")
        res = build_chunk_sheets(run, row, probe, audio, chat_j, channel, log)
        row["sheets"], row["frames"] = res["sheets"], res["frames"]
        row["rec_base_s"] = rec0
        if res["leftover_frames"]:
            raise RuntimeError(f"{res['leftover_frames']} frame files could not be deleted")
        return f"{res['frames']} frames, {res['sheets']} sheets, leftovers {res['leftover_frames']}"
    run_stage("sheets", do_sheets)

    # ---- transcript
    def do_transcript():
        if row.get("no_audio") or not probe.get("has_audio"):
            write_json(cdir / "transcript.json", empty_transcript(rec0, duration, "no audio track"), indent=None)
            return "no audio track"
        if not wav.is_file():
            r = extract_wav(dest, wav)
            if not r["ok"]:
                raise RuntimeError(f"audio extraction failed: {r['error']}")
        tr = get_transcriber(wcfg_override).transcribe(wav, rec0, duration)
        write_json(cdir / "transcript.json", tr, indent=None)
        row["words"], row["speech_seconds"], row["language"] = tr["n_words"], tr["speech_seconds"], tr["language"]
        row["model"], row["device"] = tr.get("model"), tr.get("device")
        return f"{tr['n_words']} words, {tr.get('model')} on {tr.get('device')}, {tr['transcribe_seconds']} s"
    if skip_whisper and todo("transcript"):
        log("transcript skipped (--skip-whisper)", show=True)
    else:
        run_stage("transcript", do_transcript)
    if not kw and wav.is_file() and (row["stages"].get("transcript") is True or skip_whisper is False):
        try:
            wav.unlink()
        except OSError:
            pass

    # ---- digest: transcript.txt, timeline.md, digest.json (from whatever exists)
    def do_digest():
        data = load_data(run, cid)
        if data["transcript"] is None:
            data["transcript"] = empty_transcript(rec0, duration, "transcript not made" if skip_whisper else "transcript failed")
        srows = second_rows(duration, data)
        write_text(cdir / "transcript.txt", render_transcript_txt(cid, rec0, data["transcript"]))
        write_text(cdir / "timeline.md", render_timeline_md(cid, rec0, duration, srows))
        dg = build_digest(row, rec0, duration, data, srows)
        write_json(cdir / "digest.json", dg)
        if row.get("rec_base_s") is None:
            row["rec_base_s"] = rec0
        return f"{len(srows)} seconds"
    run_stage("digest", do_digest)
    return _finish(run, row, secs, skipped, errors, state, log)


def _finish(run: Path, row: dict, secs: dict, skipped: list, errors: list, state: dict, log) -> dict:
    from cc_tables import build_stream_md, build_stream_meta
    failed = [s for s, v in row["stages"].items() if isinstance(v, str) and v.startswith("failed")]
    row["status"] = "done" if all(row["stages"].get(s) is True for s in STAGES) else ("failed" if failed else "pending")
    row["error"] = "; ".join(f"{s}: {row['stages'][s]}" for s in failed) or None
    row["seconds"] = {**(row.get("seconds") or {}), **secs}
    row["processed_at"] = now_iso()
    row = put_row(run, row)
    update_state(run, **{f"chunks.{row['id']}": {"status": row["status"], "processed_at": row["processed_at"], "error": row["error"]}})
    try:
        rows = load_chunks(run)
        build_stream_meta(run, rows, load_state(run))
        build_stream_md(run, rows, load_state(run))
    except Exception as e:  # noqa: BLE001
        log(f"stream.md / stream-meta.json not updated: {type(e).__name__}: {e}", show=True)
    log(f"ingest end: {row['status']} {secs}", show=True)
    leftover = None
    fj = read_json(chunk_dir(run, row["id"]) / "frames.json")
    if fj:
        leftover = fj.get("leftover_frames")
    return {"ok": row["status"] != "failed", "chunk": row["id"], "run": str(run), "status": row["status"], "stages": row["stages"],
            "skipped": skipped, "seconds": secs, "rec_start_s": row.get("rec_start_s"), "duration_s": row.get("duration_s"),
            "frames": row.get("frames"), "sheets": row.get("sheets"), "words": row.get("words"), "language": row.get("language"),
            "model": row.get("model"), "device": row.get("device"), "frames_deleted": (leftover == 0) if leftover is not None else None,
            "leftover_frames": leftover, "stale_rec": row.get("stale_rec"), "error": row.get("error")}


def refresh_stale(run: Path, mirror: bool = True, limit: int | None = None) -> list:
    """Re-make the sheets and text views of chunks whose rec start moved because a lower-numbered chunk arrived after them."""
    done = []
    for r in load_chunks(run):
        if r.get("stale_rec") and (Path(run) / r["file"]).is_file():
            say(f"[{r['id']}] rec start moved: re-making its sheets and text views")
            done.append(ingest_chunk(run, Path(run) / r["file"], index=r["index"], mirror=mirror))
            if limit and len(done) >= limit:
                break
    return done


def cmd_ingest(a):
    src = Path(a.chunk) if a.chunk else None
    run = None
    if a.run:
        run = resolve_run(a.run)
    elif src:
        session, channel, sdir = _session_from_chunk_path(src)
        if not session:
            fail("--run is needed when the chunk is not in <inbox>/<channel>/<session>/chunk-NNNN.mp4")
        run, _ = ensure_run(session, channel, sdir)
    else:
        fail("--chunk FILE is needed")
    if src and not src.is_file():
        # in place already? (a re-run names the chunk folder's mp4 or only the number)
        pass
    res = ingest_chunk(run, src, index=a.index, sidecar=Path(a.sidecar) if a.sidecar else None, chat=Path(a.chat) if a.chat else None,
                       force=a.force, skip_whisper=a.skip_whisper, keep_wav=True if a.keep_wav else None)
    if res.get("ok") and not a.no_refresh:
        refreshed = refresh_stale(run)
        if refreshed:
            res["refreshed_stale"] = [x["chunk"] for x in refreshed]
    out(res, 0 if res.get("ok") else (3 if res.get("refused") else 1))


# --------------------------------------------------------------------------- new-run / status / chunks

def cmd_new_run(a):
    channel = re.sub(r"[^a-z0-9_]", "", (a.channel or "").lower())
    if not channel:
        fail("--channel is needed (letters, digits, underscore)")
    session = a.session or f"{time.strftime('%Y%m%d-%H%M%S')}-{channel}"
    ov = {}
    if a.language:
        ov["language"] = a.language
    if a.prompt:
        ov["initial_prompt"] = a.prompt
    run, created = ensure_run(session, channel, Path(a.inbox) if a.inbox else None, ov)
    out({"ok": True, "run": str(run), "session": session, "channel": channel, "created": created})


def _stage_letters(row: dict) -> str:
    sym = {True: "ok", False: "--"}
    return " ".join(f"{s}:{('FAIL' if isinstance(row['stages'].get(s), str) else sym.get(row['stages'].get(s), '--'))}" for s in STAGES)


def cmd_status(a):
    if not a.run:
        root = runs_root()
        runs = []
        for d in sorted(root.glob("*")) if root.is_dir() else []:
            if (d / "state.json").is_file():
                rows = load_chunks(d)
                runs.append({"run": str(d), "session": d.name, "channel": (load_state(d) or {}).get("channel"), "chunks": len(rows),
                             "done": sum(1 for r in rows if r.get("status") == "done"),
                             "rec_total_s": round(sum(float(r.get("duration_s") or 0) for r in rows), 1)})
        for r in runs:
            print(f"{r['session']}: {r['done']}/{r['chunks']} chunks done, {fmt_hms(r['rec_total_s'], cs=False)} recorded")
        out({"ok": True, "runs_root": str(root), "runs": runs, "free_gb": free_gb(root)})
    run = resolve_run(a.run)
    st = load_state(run)
    rows = load_chunks(run)
    for r in rows:
        print(f"{r['id']} {r.get('status'):10s} {('%.1f s' % r['duration_s']) if r.get('duration_s') else '-':>9} rec {fmt_hms(r.get('rec_start_s'))} "
              f"sheets {r.get('sheets')} words {r.get('words')} [{_stage_letters(r)}]" + (f" ERROR {r['error']}" if r.get("error") else "") +
              (" STALE-REC" if r.get("stale_rec") else ""))
    newest = max(rows, key=lambda r: r["index"]) if rows else None
    counts = {}
    for r in rows:
        counts[r.get("status")] = counts.get(r.get("status"), 0) + 1
    inbox = (st.get("inbox") and Path(st["inbox"])) or None
    waiting = sorted(p.name for p in inbox.glob("chunk-*.mp4")) if inbox and inbox.is_dir() else []
    out({"ok": True, "run": str(run), "channel": st.get("channel"), "session": st.get("session"), "chunks": len(rows), "by_status": counts,
         "rec_total_s": round(sum(float(r.get("duration_s") or 0) for r in rows), 1), "newest": newest["id"] if newest else None,
         "newest_status": newest.get("status") if newest else None, "stale_rec": [r["id"] for r in rows if r.get("stale_rec")],
         "failed": [{"chunk": r["id"], "error": r.get("error")} for r in rows if r.get("status") == "failed"],
         "inbox_waiting": waiting, "free_gb": free_gb(run), "min_free_gb": cfg_get("min_free_gb", 3),
         "claude_stage": st.get("stage"), "next_skill": st.get("next_skill")})


def cmd_chunks(a):
    run = resolve_run(a.run)
    rows = load_chunks(run)
    for r in rows:
        q = r.get("quality") or {}
        print(f"{r['id']} {r.get('status'):10s} rec {fmt_hms(r.get('rec_start_s'))} len {r.get('duration_s')} t0 {r.get('t0_utc')} "
              f"gap {r.get('gap_before_s')} ads {r.get('ads_skipped_s')} {q.get('name') or ''} {(r.get('stream') or {}).get('game') or ''}")
    out({"ok": True, "run": str(run), "chunks": rows})


def cmd_stream_table(a):
    from cc_tables import build_stream_md, build_stream_meta
    run = resolve_run(a.run)
    rows = load_chunks(run)
    st = load_state(run)
    build_stream_meta(run, rows, st)
    build_stream_md(run, rows, st)
    out({"ok": True, "stream_md": str(run / "00-inventory" / "stream.md"), "stream_meta": str(run / "00-inventory" / "stream-meta.json"),
         "chunks": len(rows)})


# --------------------------------------------------------------------------- locate / window / frame / sheet

def cmd_locate(a):
    run = resolve_run(a.run)
    rows = load_chunks(run)
    if a.chunk:
        if a.offset is None:
            fail("--offset is needed with --chunk")
        rec = chunk_to_rec(rows, a.chunk.upper(), float(a.offset))
        out({"ok": True, "rec": rec, "rec_hms": fmt_hms(rec), "chunk": a.chunk.upper(), "offset": float(a.offset)})
    if a.at is None:
        fail("--at TIME or --chunk C0012 --offset 45.75 is needed")
    t = parse_time(a.at, rows)
    cid, off = rec_to_chunk(rows, t)
    if cid is None:
        total = max((r["rec_start_s"] + r["duration_s"] for r in rows if r.get("duration_s")), default=0)
        out({"ok": False, "error": f"rec {t} is outside the recording (0 - {total})", "rec": t, "recorded_s": total}, 1)
    r = next(x for x in rows if x["id"] == cid)
    out({"ok": True, "rec": t, "rec_hms": fmt_hms(t), "chunk": cid, "offset": off, "file": str(Path(run) / r["file"]),
         "chunk_rec_start_s": r["rec_start_s"], "chunk_duration_s": r["duration_s"]})


def cmd_window(a):
    from cc_tables import window_text
    run = resolve_run(a.run)
    rows = load_chunks(run)
    t0, t1 = parse_time(a.from_, rows), parse_time(a.to, rows)
    if t1 <= t0:
        fail("--to must be after --from")
    what = {w.strip() for w in a.what.split(",") if w.strip()}
    bad = what - {"transcript", "timeline", "chat", "audio"}
    if bad:
        fail(f"--what takes transcript, timeline, chat, audio (got {sorted(bad)})")
    lines, summary = window_text(run, rows, t0, t1, what)
    for ln in lines:
        print(ln)
    out({"ok": True, "from": t0, "to": t1, "from_hms": fmt_hms(t0), "to_hms": fmt_hms(t1), "what": sorted(what), **summary})


def cmd_frame(a):
    from cc_frames import extract_one
    run = resolve_run(a.run)
    rows = load_chunks(run)
    t = parse_time(a.at, rows)
    done = [r for r in rows if r.get("duration_s") and (r.get("stages") or {}).get("move") is True]
    cid, off = rec_to_chunk(done, t)
    if cid is None:
        fail(f"rec {t} is outside the recording")
    crop = None
    if a.crop:
        crop = [float(x) for x in a.crop.split(",")]
        if len(crop) != 4 or not all(0 <= v <= 1 for v in crop):
            fail("--crop takes x,y,w,h as fractions of the frame (0 to 1)")
    path = Path(a.out) if a.out else run / "30-assets" / "frames" / (f"frame-{cid}-{off:08.2f}s" + ("-crop" + "-".join(f"{v:g}" for v in crop) if crop else "") +
                                                                       (f"-w{a.max_width}" if a.max_width else "") + ".jpg")
    res = extract_one(chunk_dir(run, cid) / "chunk.mp4", off, path, a.max_width, crop)
    if not res["ok"]:
        out({"ok": False, "error": res["error"]}, 1)
    out({"ok": True, "path": str(path), "rec": t, "rec_hms": fmt_hms(t), "chunk": cid, "offset": off, "width": res.get("width"),
         "height": res.get("height")})


def cmd_sheet(a):
    from cc_frames import build_dense
    run = resolve_run(a.run)
    rows = load_chunks(run)
    t0, t1 = parse_time(a.from_, rows), parse_time(a.to, rows)
    if t1 <= t0:
        fail("--to must be after --from")
    if a.step <= 0:
        fail("--step must be positive")
    try:
        res = build_dense(run, rows, load_state(run).get("channel") or "channel", t0, t1, a.step, a.cols, a.rows, a.cell_w,
                          Path(a.out_dir) if a.out_dir else run / "30-assets" / "sheets", max_frames=a.max_frames)
    except (RuntimeError, StopIteration) as e:
        out({"ok": False, "error": str(e) or "the window is outside the recording"}, 1)
    out({"ok": True, **res})


# --------------------------------------------------------------------------- doctor

def cmd_doctor(a):
    checks = []

    def chk(name, ok, detail, hard=True):
        checks.append({"name": name, "ok": bool(ok), "hard": hard, "detail": detail})
    for tool in ("ffmpeg", "ffprobe"):
        try:
            cp = run_cmd([find_tool(tool), "-version"], timeout=30)
            chk(tool, cp.returncode == 0, (cp.stdout or "").splitlines()[0][:90] if cp.stdout else cp.stderr[:90])
        except SystemExit:
            chk(tool, False, "not found on PATH")
    chk("python", True, f"{sys.version.split()[0]} {sys.executable}", hard=False)
    for mod, hard in (("PIL", True), ("numpy", True), ("faster_whisper", True), ("ctranslate2", False), ("av", False), ("cv2", False), ("librosa", False)):
        try:
            m = __import__(mod)
            v = getattr(m, "__version__", "ok")
            if mod == "av" and str(v).split(".")[0].isdigit() and int(str(v).split(".")[0]) >= 19:
                chk("av", False, f"{v}: PyAV 19 breaks faster-whisper 1.2.1; keep av<19")
            else:
                chk(mod, True, v, hard=hard)
        except Exception as e:  # noqa: BLE001
            chk(mod, False, f"{type(e).__name__}: {e}"[:120], hard=hard)
    w = cfg_get("whisper", {}) or {}
    model = os.environ.get("CC_WHISPER_MODEL") or w.get("model", "medium")
    hf = Path(os.environ.get("HF_HOME") or (Path.home() / ".cache" / "huggingface")) / "hub"
    found = sorted(hf.glob(f"models--*faster-whisper-{model}*/snapshots/*/model.bin"))
    chk("whisper model cached", bool(found), f"{model}: {found[-1].parent.parent.parent.name if found else 'not in ' + str(hf)}")
    try:
        import ctranslate2
        n = ctranslate2.get_cuda_device_count()
        dll = Path(w.get("cuda_dll_dir") or "") / "cublas64_12.dll"
        chk("cuda", True, f"{n} device(s); cuda dll dir {'has cublas64_12.dll' if dll.is_file() else 'missing'}; device in use: {w.get('device', 'cpu')} (opt-in)", hard=False)
    except Exception as e:  # noqa: BLE001
        chk("cuda", False, str(e)[:100], hard=False)
    root, inbox = runs_root(), inbox_dir()
    min_free = cfg_get("min_free_gb", 3)
    for name, p in (("runs drive free space", root), ("inbox drive free space", inbox)):
        g = free_gb(p)
        chk(name, g >= float(min_free), f"{g} GB free (min_free_gb {min_free}) at {p}")
    chk("runs root", True, f"{root} ({'exists' if root.is_dir() else 'will be created'})", hard=False)
    chk("inbox", True, f"{inbox} ({'exists' if inbox.is_dir() else 'not there yet: the extension creates it'})", hard=False)
    lock = root / ".watch.lock"
    pid = None
    if lock.is_file():
        try:
            pid = int(lock.read_text().strip() or 0)
        except ValueError:
            pid = None
    chk("watcher", True, f"running (pid {pid})" if pid and _pid_alive(pid) else "not running", hard=False)
    ok = all(c["ok"] for c in checks if c["hard"])
    out({"ok": ok, "checks": checks, "config": {"frames": cfg_get("frames"), "whisper": w, "audio": cfg_get("audio"), "min_free_gb": min_free,
                                                "runs_root": str(root), "inbox_dir": str(inbox)}})


# --------------------------------------------------------------------------- watch

def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        k32 = ctypes.windll.kernel32
        h = k32.OpenProcess(0x1000, False, pid)         # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong()
        ok = k32.GetExitCodeProcess(h, ctypes.byref(code))
        k32.CloseHandle(h)
        return bool(ok) and code.value == 259           # STILL_ACTIVE
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


class WatchLock:
    """One watcher at a time: a lock file holding its pid; a dead pid's file is taken over."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.is_file():
            try:
                pid = int(self.path.read_text().strip() or 0)
            except (ValueError, OSError):
                pid = 0
            if pid and pid != os.getpid() and _pid_alive(pid):
                fail(f"another watcher is running (pid {pid}, lock {self.path})", 4)
        self.path.write_text(str(os.getpid()))
        return self

    def touch(self):
        try:
            os.utime(self.path)
        except OSError:
            pass

    def __exit__(self, *exc):
        try:
            if self.path.is_file() and self.path.read_text().strip() == str(os.getpid()):
                self.path.unlink()
        except OSError:
            pass


def scan_inbox(inbox: Path) -> list:
    found = []
    if not inbox.is_dir():
        return found
    for chd in sorted(p for p in inbox.iterdir() if p.is_dir()):
        for sess in sorted(p for p in chd.iterdir() if p.is_dir()):
            try:
                names = [f for f in sess.iterdir() if f.is_file()]
            except OSError:
                continue
            for f in names:
                m = CHUNK_FILE_RE.match(f.name)
                if not m:
                    continue
                idx = int(m.group(1))
                found.append({"path": f, "channel": chd.name, "session": sess.name, "index": idx, "session_dir": sess,
                              "sidecar": sess / f"chunk-{idx:04d}.json", "chat": sess / f"chat-{idx:04d}.json",
                              "crdownload": (sess / (f.name + ".crdownload")).exists() or any(sess.glob(glob_escape(f.stem) + "*.crdownload"))})
    found.sort(key=lambda c: (c["session"], c["index"]))
    return found


def glob_escape(s: str) -> str:
    return re.sub(r"([\[\]*?])", r"[\1]", s)


def sync_sessions(inbox: Path, root: Path) -> int:
    """The extension writes session.json when a recording starts and overwrites it when it ends (the stream ended, the user stopped it, a
    limit was reached). Copy a newer one into its run (00-inventory/session.json) and record the end in state.json (recording.ended_at,
    reason, chunks, stream_ended) so /create-clips knows whether the recording is complete. Returns the number of runs updated."""
    n = 0
    if not inbox.is_dir():
        return 0
    for chd in inbox.iterdir():
        if not chd.is_dir():
            continue
        for sess in chd.iterdir():
            sj, run = sess / "session.json", root / sess.name
            if not (sess.is_dir() and sj.is_file() and (run / "state.json").is_file()):
                continue
            dst = run / "00-inventory" / "session.json"
            try:
                if dst.is_file() and dst.stat().st_mtime_ns >= sj.stat().st_mtime_ns:
                    continue
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(sj, dst)
                data = read_json(sj, {}) or {}
                rec = {"started_at": data.get("started_at"), "ended_at": data.get("ended_at"), "reason": data.get("reason"),
                       "chunks": data.get("chunks"), "chunk_seconds": data.get("chunk_seconds"), "quality_pref": data.get("quality_pref")}
                update_state(run, recording=rec, stream_ended=bool(data.get("ended_at")))
                n += 1
            except OSError:
                continue
    return n


def _check_ready(c: dict, seen: dict, now: float, stable_s: float, sidecar_wait: float) -> str:
    p = c["path"]
    try:
        st = p.stat()
    except OSError:
        return "gone"
    sig = (st.st_size, st.st_mtime_ns)
    e = seen.get(p)
    if e is None or e["sig"] != sig:
        seen[p] = {"sig": sig, "since": now, "first": e["first"] if e else now}
        return "unstable"
    if c["crdownload"]:
        return "blocked"
    if now - e["since"] < stable_s:
        return "unstable"
    if not c["sidecar"].is_file() and now - e["first"] < sidecar_wait:
        return "waiting-sidecar"
    return "ready"


def cmd_watch(a):
    inbox = Path(a.inbox) if a.inbox else inbox_dir()
    seen, blocked_until, tries, dead = {}, {}, {}, set()
    processed, skipped_incomplete = [], []
    last_pause_msg = 0.0
    root = runs_root()
    root.mkdir(parents=True, exist_ok=True)
    say(f"[watch] inbox {inbox} -> runs {root} (whisper: {(cfg_get('whisper', {}) or {}).get('model')} on "
        f"{os.environ.get('CC_WHISPER_DEVICE') or (cfg_get('whisper', {}) or {}).get('device')}); Ctrl+C stops")
    interrupted = False
    last_work, last_sync = time.time(), 0.0
    idle_unload = float((cfg_get("whisper", {}) or {}).get("idle_unload_s", 600) or 0)
    with WatchLock(root / ".watch.lock") as lock:
        try:
            while True:
                lock.touch()
                now = time.time()
                if now - last_sync > 10:                                   # the recorder's session.json (start, end, reason) follows into the run
                    last_sync = now
                    for _ in range(sync_sessions(inbox, root)):
                        say("[watch] a recording's session.json changed: the run's recording info is updated")
                if idle_unload and now - last_work > idle_unload:        # a background watcher does not keep the 1.5 GB model while nothing arrives
                    from cc_audio import unload_transcriber
                    if unload_transcriber():
                        say(f"[watch] idle for {int(idle_unload)} s: Whisper model unloaded (the next chunk loads it again)")
                cands = scan_inbox(inbox)
                states = {c["path"]: _check_ready(c, seen, now, a.stable, a.sidecar_wait) for c in cands}
                ready = [c for c in cands if states[c["path"]] == "ready" and c["path"] not in dead and now >= blocked_until.get(c["path"], 0)]
                if ready:
                    c = ready[0]
                    t0 = time.time()
                    run, created = ensure_run(c["session"], c["channel"], c["session_dir"])
                    res = ingest_chunk(run, c["path"], index=c["index"], sidecar=c["sidecar"] if c["sidecar"].is_file() else None,
                                       chat=c["chat"] if c["chat"].is_file() else None, skip_whisper=a.skip_whisper)
                    if res.get("refused"):
                        blocked_until[c["path"]] = time.time() + 30
                        if time.time() - last_pause_msg > 60:
                            say(f"[watch] paused: {res['refused']} (waiting; free some space)")
                            last_pause_msg = time.time()
                    else:
                        if not res.get("ok") and c["path"].exists():
                            tries[c["path"]] = tries.get(c["path"], 0) + 1
                            blocked_until[c["path"]] = time.time() + 60
                            if tries[c["path"]] >= 5:
                                dead.add(c["path"])
                                say(f"[watch] giving up on {c['path']} after {tries[c['path']]} tries: {res.get('error')}")
                        processed.append({"session": c["session"], "chunk": res.get("chunk"), "status": res.get("status"),
                                          "seconds": round(time.time() - t0, 1), "error": res.get("error")})
                        say(f"[watch] {c['channel']}/{c['session']} {res.get('chunk')}: {res.get('status')} in {time.time() - t0:.1f} s "
                            f"{res.get('seconds')} free {free_gb(run)} GB")
                        if res.get("ok"):
                            refresh_stale(run, limit=1)
                    last_work = time.time()
                    continue
                waiting = any(s in ("unstable", "waiting-sidecar") for s in states.values())
                if not waiting:                 # idle: re-make one chunk whose rec start moved, if any
                    did = False
                    for rd in sorted(root.glob("*")):
                        if (rd / "state.json").is_file() and refresh_stale(rd, limit=1):
                            did = True
                            break
                    if did:
                        continue
                if a.once and not waiting:
                    skipped_incomplete = [str(c["path"]) for c in cands if states[c["path"]] in ("blocked", "gone") or c["path"] in dead]
                    break
                time.sleep(min(a.interval, max(0.3, a.stable / 2)) if (a.once and waiting) else a.interval)
        except KeyboardInterrupt:
            interrupted = True
            say("[watch] stopped (Ctrl+C); an interrupted chunk resumes at the next start")
    out({"ok": True, "processed": processed, "skipped_incomplete": skipped_incomplete, "interrupted": interrupted})


# --------------------------------------------------------------------------- register

def register(sub) -> None:
    p = sub.add_parser("new-run", help="create a run folder (session id = <YYYYMMDD-HHMMSS>-<channel>)")
    p.add_argument("--channel", required=True)
    p.add_argument("--session", help="session id (default: now + channel)")
    p.add_argument("--inbox", help="the session's inbox folder")
    p.add_argument("--language", help="whisper language for this run (default: config; 'auto' lets it detect)")
    p.add_argument("--prompt", help="whisper initial prompt for this run (names, terms)")
    p.set_defaults(func=cmd_new_run)

    p = sub.add_parser("ingest", help="process one chunk: move, probe, audio, sheets, transcript, digest (resumable)")
    p.add_argument("--run", help="run folder or session name (default: derived from <inbox>/<channel>/<session>/chunk-NNNN.mp4)")
    p.add_argument("--chunk", required=True, help="the chunk mp4 (in the inbox, or already in the run for a re-run)")
    p.add_argument("--sidecar", help="chunk-NNNN.json (default: next to the mp4)")
    p.add_argument("--chat", help="chat-NNNN.json (default: next to the mp4)")
    p.add_argument("--index", type=int, help="chunk number when the file name does not say it")
    p.add_argument("--force", action="store_true", help="redo every stage")
    p.add_argument("--skip-whisper", action="store_true", help="no transcript now (a later ingest makes it)")
    p.add_argument("--keep-wav", action="store_true", help="keep audio-16k.wav after the transcript")
    p.add_argument("--no-refresh", action="store_true", help="do not re-make chunks whose rec start moved")
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("watch", help="watch the inbox and ingest chunks as they land (Ctrl+C stops; resumes later)")
    p.add_argument("--inbox", help=f"default: config inbox_dir")
    p.add_argument("--once", action="store_true", help="process what is there and exit")
    p.add_argument("--interval", type=float, default=3.0, help="seconds between polls")
    p.add_argument("--stable", type=float, default=1.5, help="a file is landed when its size is unchanged for this many seconds")
    p.add_argument("--sidecar-wait", type=float, default=20.0, help="seconds to wait for chunk-NNNN.json before going on without it")
    p.add_argument("--skip-whisper", action="store_true")
    p.set_defaults(func=cmd_watch)

    p = sub.add_parser("status", help="stages per chunk of a run, free space; without --run: the list of runs")
    p.add_argument("--run")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("doctor", help="check ffmpeg, python modules, the Whisper model, disk space, the inbox")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("chunks", help="the chunk table of a run")
    p.add_argument("--run", required=True)
    p.set_defaults(func=cmd_chunks)

    p = sub.add_parser("locate", help="rec time <-> chunk and offset")
    p.add_argument("--run", required=True)
    p.add_argument("--at", help="rec time: 2025.75, 33:45.75, 0:33:45.75 or C0012+45.75")
    p.add_argument("--chunk", help="a chunk id (with --offset) to get its rec time")
    p.add_argument("--offset", type=float)
    p.set_defaults(func=cmd_locate)

    p = sub.add_parser("window", help="the transcript / per-second timeline / chat / audio of a rec window, across chunks")
    p.add_argument("--run", required=True)
    p.add_argument("--from", dest="from_", required=True, help="rec time")
    p.add_argument("--to", required=True, help="rec time")
    p.add_argument("--what", default="transcript,timeline", help="comma list of transcript, timeline, chat, audio")
    p.set_defaults(func=cmd_window)

    p = sub.add_parser("frame", help="one frame at a rec time, full size (or --max-width), optionally cropped")
    p.add_argument("--run", required=True)
    p.add_argument("--at", required=True)
    p.add_argument("--max-width", type=int)
    p.add_argument("--crop", help="x,y,w,h as fractions of the frame, e.g. 0.6,0.5,0.4,0.5")
    p.add_argument("--out")
    p.set_defaults(func=cmd_frame)

    p = sub.add_parser("sheet", help="a dense contact sheet of any rec window (frames deleted right after)")
    p.add_argument("--run", required=True)
    p.add_argument("--from", dest="from_", required=True)
    p.add_argument("--to", required=True)
    p.add_argument("--step", type=float, default=0.25, help="seconds between frames (default 0.25)")
    p.add_argument("--cols", type=int)
    p.add_argument("--rows", type=int)
    p.add_argument("--cell-w", type=int, help="cell width in px (default from config: 240)")
    p.add_argument("--max-frames", type=int, default=240)
    p.add_argument("--out-dir")
    p.set_defaults(func=cmd_sheet)

    p = sub.add_parser("stream-table", help="rebuild 00-inventory/stream.md and stream-meta.json")
    p.add_argument("--run", required=True)
    p.set_defaults(func=cmd_stream_table)
