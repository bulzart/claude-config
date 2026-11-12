"""Frames and sheets: ffmpeg frame batches, the chunk's contact sheets, dense sheets on demand, single frames.

A chunk's frames are taken every `frames.interval_s` (0.75 s: 4 per 3 s). They are written a sheet at a time (30 frames), the sheet is
composed, and those frames are deleted the moment the sheet is saved, so about one sheet of frames exists at any moment.
Frame i of a chunk is at chunk offset i * interval; ffmpeg's select filter (`gte(t, selected_n * step)`) takes the first frame at or
after each target time, which was checked against single-frame extraction (identical pixels).
"""
from __future__ import annotations

import math
import re
import time
from pathlib import Path

import numpy as np
from PIL import Image

from cc_common import (cfg_get, chunk_dir, chunk_to_rec, fmt_hms, find_tool, read_json, rec_to_chunk, run_cmd, write_json)
from cc_sheets import cell_label, layout_for, render_sheet

PTS_RE = re.compile(r"pts_time:\s*([0-9.eE+-]+)")


def n_frames(duration_s: float | None, interval: float) -> int:
    """Frames of a chunk: i = 0 .. floor((duration - 0.01) / interval)."""
    if not duration_s or duration_s <= 0.01:
        return 0
    return int(math.floor((duration_s - 0.01) / interval)) + 1


def extract_batch(chunk, start_s: float, step_s: float, count: int, out_dir: Path, w: int, h: int, timeout: float = 900) -> dict:
    """Up to `count` frames at start_s + k * step_s, scaled to fit w x h, as out_dir/f_001.jpg ... {files, pts (offsets in the chunk), error}."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("f_*.jpg"):
        old.unlink()
    vf = (f"select='gte(t,selected_n*{step_s:.6f})',scale={w}:{h}:force_original_aspect_ratio=decrease:force_divisible_by=2:flags=area,"
          f"showinfo")
    cp = run_cmd([find_tool("ffmpeg"), "-hide_banner", "-loglevel", "info", "-nostdin", "-y", "-ss", f"{start_s:.3f}", "-i", str(chunk),
                  "-an", "-sn", "-dn", "-vf", vf, "-fps_mode", "vfr", "-frames:v", str(count), "-q:v", "2",
                  str(out_dir / "f_%03d.jpg")], timeout=timeout)
    files = sorted(out_dir.glob("f_*.jpg"))
    pts = [start_s + float(m.group(1)) for line in (cp.stderr or "").splitlines() if "showinfo" in line for m in [PTS_RE.search(line)] if m]
    err = None
    if not files:
        err = (cp.stderr or "ffmpeg wrote no frame")[-300:].strip()
    return {"files": files, "pts": pts if len(pts) == len(files) else [None] * len(files), "error": err}


def extract_one(chunk, offset_s: float, out_path, max_width: int | None = None, crop=None, quality: int = 2) -> dict:
    """One frame at a chunk offset, full size unless max_width; crop = normalized (x, y, w, h) of the frame."""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    chain = []
    if crop:
        x, y, cw, chh = [float(v) for v in crop]
        chain.append(f"crop=w='iw*{cw:.5f}':h='ih*{chh:.5f}':x='iw*{x:.5f}':y='ih*{y:.5f}'")
    if max_width:
        chain.append(f"scale=w='min(iw,{int(max_width)})':h=-2")
    args = [find_tool("ffmpeg"), "-hide_banner", "-loglevel", "error", "-nostdin", "-y", "-ss", f"{max(0.0, offset_s):.3f}", "-i", str(chunk),
            "-an", "-sn", "-dn"]
    if chain:
        args += ["-vf", ",".join(chain)]
    args += ["-frames:v", "1", "-q:v", str(quality), str(out_path)]
    cp = run_cmd(args, timeout=300)
    p = Path(out_path)
    ok = cp.returncode == 0 and p.is_file() and p.stat().st_size > 0
    res = {"ok": ok, "error": None if ok else (cp.stderr or "no frame")[-300:].strip()}
    if ok:
        with Image.open(p) as im:
            res["width"], res["height"] = im.size
    return res


# --------------------------------------------------------------------------- per-frame numbers

def frame_rms(audio: dict | None, t: float, interval: float):
    """Largest RMS (dB) of the audio windows that overlap [t, t + interval)."""
    if not audio or audio.get("no_audio") or not audio.get("rms_db"):
        return None
    win = float(audio.get("window_s") or 0.5)
    rms = audio["rms_db"]
    k0 = int(t / win)
    k1 = int((t + interval - 1e-9) / win)
    seg = rms[min(k0, len(rms) - 1):min(k1, len(rms) - 1) + 1]
    return max(seg) if seg else None


def frame_chat(chat: dict | None, t: float):
    if not chat:
        return None
    per = chat.get("per_second") or []
    i = int(t)
    return int(per[i]) if 0 <= i < len(per) else None


def _gray(im: Image.Image) -> np.ndarray:
    return np.asarray(im.convert("L").resize((64, 36), Image.BILINEAR), dtype=np.int16)


def _clear_dir(d: Path) -> int:
    """Remove frame files in d (and d itself when empty); returns how many files are left."""
    left = 0
    if d.is_dir():
        for p in d.glob("*"):
            try:
                p.unlink()
            except OSError:
                left += 1
        try:
            d.rmdir()
        except OSError:
            pass
    return left


# --------------------------------------------------------------------------- the chunk's sheets

def build_chunk_sheets(run: Path, row: dict, probe: dict, audio: dict | None, chat: dict | None, channel: str, log=None) -> dict:
    """Frames -> sheets (one sheet of frames on disk at a time), overview.jpg and frames.json. Returns the summary."""
    t_start = time.time()
    cid = row["id"]
    cdir = chunk_dir(run, cid)
    chunk = cdir / "chunk.mp4"
    f = cfg_get("frames", {}) or {}
    interval = float(f.get("interval_s", 0.75))
    q = int(f.get("jpeg_quality", 86))
    ov_every = int(f.get("overview_every", 10))
    ov_cols = int(f.get("overview_cols", 6))
    lay = layout_for(probe.get("width"), probe.get("height"))
    cols, cw, ch, per = lay["cols"], lay["cell_w"], lay["cell_h"], lay["per_sheet"]
    dur = float(probe.get("duration_s") or 0)
    total = n_frames(dur, interval)
    if total <= 0:
        raise RuntimeError("the chunk has no duration to take frames from")
    pages = math.ceil(total / per)
    rec0 = float(row.get("rec_start_s") or 0.0)
    sheets_dir = cdir / "sheets"
    sheets_dir.mkdir(parents=True, exist_ok=True)
    for old in list(sheets_dir.glob("sheet-*.jpg")) + list(sheets_dir.glob("overview.jpg")):
        old.unlink()
    tmp = cdir / "frames"
    _clear_dir(tmp)
    frames, ov_cells = [], []
    prev = None
    leftover = 0
    missing = 0
    img_w, img_h = cw - 2, ch - 2
    for s in range(pages):
        i0, i1 = s * per, min(total, (s + 1) * per)
        got = extract_batch(chunk, i0 * interval, interval, i1 - i0, tmp, img_w, img_h)
        cells = []
        for j, i in enumerate(range(i0, i1)):
            t = round(i * interval, 3)
            im = None
            tp = None
            if j < len(got["files"]):
                try:
                    with Image.open(got["files"][j]) as fh:
                        im = fh.convert("RGB")
                    tp = got["pts"][j]
                except Exception:  # noqa: BLE001
                    im = None
            diff = None
            if im is not None:
                g = _gray(im)
                diff = round(float(np.abs(g - prev).mean()), 2) if prev is not None else None
                prev = g
            else:
                missing += 1
            rms = frame_rms(audio, t, interval)
            cnt = frame_chat(chat, t)
            label = cell_label(rec0 + t, t)
            cells.append({"img": im, "label": label, "rms_db": rms, "chat": cnt})
            if ov_every and i % ov_every == 0:
                ov_cells.append({"img": im.copy() if im is not None else None, "label": label, "rms_db": rms, "chat": cnt})
            frames.append({"i": i, "t": t, "rec": round(rec0 + t, 3), "sheet": s + 1, "cell": j, "rms_db": rms, "chat_per_s": cnt,
                           "diff_prev": diff, "t_pts": round(tp, 3) if tp is not None else None, "label": label, "missing": im is None})
        a, b = rec0 + i0 * interval, rec0 + min(dur, i1 * interval)
        title = f"{channel} | {cid} | rec {fmt_hms(a)}-{fmt_hms(b)} | sheet {s + 1}/{pages} | {interval:g} s per frame"
        render_sheet(cells, title=title, legend=None, cols=cols, cw=cw, ch=ch, path=sheets_dir / f"sheet-{s + 1:02d}.jpg", quality=q)
        for p in got["files"]:                      # the sheet is saved: its frames go now
            try:
                p.unlink()
            except OSError:
                leftover += 1
        if log:
            log(f"sheet {s + 1}/{pages}: {len(cells)} frames drawn, {len(got['files'])} frame files removed")
    leftover += _clear_dir(tmp)
    overview = None
    if ov_cells:
        ov_title = (f"{channel} | {cid} | overview | rec {fmt_hms(rec0)}-{fmt_hms(rec0 + dur)} | every {ov_every}th frame "
                    f"({ov_every * interval:g} s)")
        render_sheet(ov_cells, title=ov_title, legend=None, cols=ov_cols, cw=cw, ch=ch, path=sheets_dir / "overview.jpg", quality=q)
        overview = "sheets/overview.jpg"
    meta = {"interval_s": interval, "cols": cols, "rows": lay["rows"], "per_sheet": per, "cell": [cw, ch], "rec_start_s": round(rec0, 3),
            "duration_s": dur, "source": {"width": probe.get("width"), "height": probe.get("height"), "fps": probe.get("fps")},
            "sheets": pages, "overview": overview, "overview_every": ov_every, "frames_deleted": leftover == 0,
            "leftover_frames": leftover, "frames_missing": missing, "frames": frames}
    write_json(cdir / "frames.json", meta, indent=None)
    return {"sheets": pages, "frames": total, "leftover_frames": leftover, "missing": missing, "overview": bool(overview),
            "seconds": round(time.time() - t_start, 1)}


# --------------------------------------------------------------------------- dense sheets on demand

def build_dense(run: Path, rows: list, channel: str, t_from: float, t_to: float, step: float, cols: int | None, rws: int | None,
                cell_w: int | None, out_dir: Path, max_frames: int = 240, log=None) -> dict:
    """A dense sheet of any rec window: frames every `step` s from t_from up to (not including) t_to, a sheet per cols*rows frames."""
    q = int(cfg_get("frames.jpeg_quality", 86))
    done = [r for r in rows if r.get("duration_s") and (r.get("stages") or {}).get("move") is True]
    if not done:
        raise RuntimeError("no chunk with a duration in the table")
    end = max(r["rec_start_s"] + r["duration_s"] for r in done)
    t_from = max(0.0, t_from)
    t_to = min(t_to, end)
    if t_to <= t_from:
        raise RuntimeError(f"the window is outside the recording (0 - {fmt_hms(end)})")
    times = []
    k = 0
    while t_from + k * step < t_to - 1e-9 and len(times) < max_frames:
        times.append(round(t_from + k * step, 3))
        k += 1
    first = next(r for r in done if r["rec_start_s"] - 1e-6 <= times[0] < r["rec_start_s"] + r["duration_s"])
    pr = read_json(chunk_dir(run, first["id"]) / "probe.json", {}) or {}
    lay = layout_for(pr.get("width"), pr.get("height"), cols, rws, cell_w)
    c, cw, ch, per = lay["cols"], lay["cell_w"], lay["cell_h"], lay["per_sheet"]
    pages = math.ceil(len(times) / per)
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = out_dir / f".tmp-{int(time.time() * 1000) % 10_000_000}"
    cache: dict = {}

    def side(cid):
        if cid not in cache:
            cd = chunk_dir(run, cid)
            cache[cid] = (read_json(cd / "audio.json", None), read_json(cd / "chat.json", None))
        return cache[cid]
    interval_hint = step
    files_out, leftover = [], 0
    for pg in range(pages):
        tp = times[pg * per:(pg + 1) * per]
        located = [(t,) + tuple(rec_to_chunk(done, t)) for t in tp]
        cells, j = [], 0
        while j < len(located):
            cid = located[j][1]
            k = j
            while k < len(located) and located[k][1] == cid:
                k += 1
            group = located[j:k]
            if cid is None:
                cells += [{"img": None, "label": cell_label(g[0], 0), "rms_db": None, "chat": None} for g in group]
            else:
                got = extract_batch(chunk_dir(run, cid) / "chunk.mp4", group[0][2], step, len(group), tmp, cw - 2, ch - 2)
                audio, chat = side(cid)
                for n, (t, _cid, off) in enumerate(group):
                    im = None
                    if n < len(got["files"]):
                        with Image.open(got["files"][n]) as fh:
                            im = fh.convert("RGB")
                    cells.append({"img": im, "label": cell_label(t, off), "rms_db": frame_rms(audio, off, interval_hint),
                                  "chat": frame_chat(chat, off)})
                for p in got["files"]:
                    try:
                        p.unlink()
                    except OSError:
                        leftover += 1
            j = k
        cids = sorted({g[1] for g in located if g[1]})
        title = (f"{channel} | {'-'.join(cids) if len(cids) < 3 else cids[0] + '..' + cids[-1]} | rec {fmt_hms(tp[0])}-{fmt_hms(tp[-1] + step)} | "
                 f"dense {step:g} s per frame | sheet {pg + 1}/{pages}")
        path = out_dir / f"dense-{t_from:09.2f}-{t_to:09.2f}-s{step:g}-{pg + 1:02d}.jpg"
        render_sheet(cells, title=title, legend=None, cols=c, cw=cw, ch=ch, path=path, quality=q)
        files_out.append(str(path))
    leftover += _clear_dir(tmp)
    return {"sheets": files_out, "frames": len(times), "rec_from": times[0], "rec_to": round(times[-1] + step, 3), "step_s": step,
            "cols": c, "cell": [cw, ch], "leftover_frames": leftover}
