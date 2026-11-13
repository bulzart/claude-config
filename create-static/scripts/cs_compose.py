"""cs_compose.py - /create-static's CapCut composition: the whole project of one video in ONE `capcut compile`, one pass of writes, one read-back.

The older way of this toolkit built a Static video's project one tool call at a time (a still, an audio clip, then motion, transitions, effects, the word-box captions
track by track, labels, a font and an entrance per track, the repair). This module builds the same project in one process:

  1. the timeline (`T slideshow plan`: images, moves, joins, effects, drawings, captions, labels) becomes a `capcut compile` spec: the stills on the main track, the narration
     and the bed, every effect overlay, drawing clip and sound, the caption texts (one text per word and state in the word-box look) and the labels, with the transitions and the
     text styles as operations (the very functions capcut-cli's single commands call: addVideo, addAudio, addText, addTransition, setTextStyle, setAudioFade);
  2. stills and the two long audio files are given the 350 KB black placeholder and pointed at their real files afterwards (compile copies every media file into the draft);
  3. what compile has no operation for (the moves as KFTypeScaleX/KFTypePositionX/Y keys, the overlays' keys, the font, the entrance, the box field) is written in ONE load and
     ONE save of each copy of the timeline, then `register`, the media links, `sync-timelines` and `lint` run under the machine-wide store lock;
  4. the project is read back against the timeline (clips, spans, joins, moves, transitions, audio, effects, texts, fonts, entrances, media on disk, lint) into one answer with a
     `problems` list.

Gather-only: nothing here judges; every look, move, join and effect is the timeline's (the plan's). `HOST` is the toolkit module (cs.py), set by register()."""
from __future__ import annotations

import copy
import datetime as dt
import json
import math
import os
import re
import shutil
import sys
import time
import uuid
from pathlib import Path

HOST = None                      # the toolkit module (cs.py)
US = 1_000_000
MOVE_PROPS = ("UNIFORM_SCALE", "KFTypeScaleX", "KFTypeScaleY", "KFTypePositionX", "KFTypePositionY")
WORD_BOX_PREFIX = "wordcap"
LABEL_TRACK = "labels"
PLAIN_TRACK = "subtitle"
MAIN_TRACK = "main"
NARRATION_TRACK = "narration"
BED_TRACK = "bed"


def _fail(msg: str, code: int = 1, **extra):
    HOST.fail(msg, code, **extra)


def _norm(p) -> str:
    return str(p).replace("\\", "/")


def _us(sec) -> int:
    return int(round(float(sec) * US))


def _read_json(p: Path, default=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return default


def _write_compact(p: Path, content: dict) -> None:
    """A timeline document written once, compact (CapCut and capcut-cli read both forms)."""
    Path(p).write_text(json.dumps(content, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def _last_json(text: str):
    for line in reversed((text or "").strip().splitlines()):
        line = line.strip()
        if line.startswith("{") or line.startswith("["):
            try:
                return json.loads(line)
            except ValueError:
                continue
    return None


# --------------------------------------------------------------------------- the machine-wide store lock, the placeholder, the name

def store_lock_path() -> Path:
    """The lock of CapCut's shared project index (root_meta_info.json), one file for every toolkit that writes it: config capcut.store_lock (the file the Loupe toolkit's repair
    and the clip toolkit's build also take), else <runs>/.capcut-store.lock."""
    p = os.environ.get("CS_STORE_LOCK") or HOST.cfg_get("capcut.store_lock")      # CS_STORE_LOCK: tests keep their lock out of the real one
    return Path(p) if p else Path(HOST.cfg_get("runs_root") or (HOST.CS_HOME / "runs")) / ".capcut-store.lock"


def locked_run(args: list, timeout: float):
    """A capcut-cli call that writes the store's index (compile, register) under the machine-wide lock."""
    lock = store_lock_path()
    lock.parent.mkdir(parents=True, exist_ok=True)
    with HOST.FileLock(lock, timeout=900, stale=300):
        return HOST.run(args, timeout=timeout)


def make_placeholder(rd: Path, need_s: float) -> Path:
    """A tiny black video with silent audio, long enough for the longest audio file: compile takes it as the media of the items that stay in place (the stills, the narration,
    the bed) and copies it into the draft (350 KB); the real files replace it afterwards."""
    dst = rd / "30-assets" / "compose" / "placeholder.mp4"
    have = 0.0
    if dst.is_file():
        try:
            have = float(HOST.media_summary(dst).get("duration_s") or 0)
        except Exception:  # noqa: BLE001
            have = 0.0
    if have and have >= need_s:
        return dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    secs = max(200, int(math.ceil(need_s)) + 10)
    cp = HOST.run([HOST.find_tool("ffmpeg"), "-hide_banner", "-loglevel", "error", "-nostdin", "-y", "-f", "lavfi", "-i", "color=c=black:s=64x36:r=30",
                   "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", str(secs), "-c:v", "libx264", "-preset", "veryfast", "-crf", "45",
                   "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "16k", str(dst)], timeout=300)
    if cp.returncode != 0 or not dst.is_file():
        _fail("could not make the placeholder media: " + (cp.stderr or "")[-300:], 1)
    return dst


def free_name(store: Path, nn: str, ftag: str, date: str | None = None) -> str:
    """DD_Mon_YYYY_vNN (-<tag> for an extra format), with -2, -3 ... when that folder exists."""
    d = dt.date.fromisoformat(date) if date else dt.date.today()
    base = f"{d.day:02d}_{HOST.MONTHS_EN[d.month - 1]}_{d.year}_v{int(nn):02d}" + HOST._fmt_sfx(ftag)
    name, k = base, 1
    while (store / name).exists():
        k += 1
        name = f"{base}-{k}"
    return name


def image_size(p: Path) -> tuple:
    from PIL import Image
    with Image.open(p) as im:
        return int(im.width), int(im.height)


def probe_many(files: list) -> dict:
    """ffprobe facts of every distinct file, several at a time."""
    from concurrent.futures import ThreadPoolExecutor
    files = sorted({str(f) for f in files})
    if not files:
        return {}
    with ThreadPoolExecutor(max_workers=min(8, len(files))) as ex:
        return dict(zip(files, ex.map(lambda f: HOST.media_summary(f), files)))


# --------------------------------------------------------------------------- reading the plan

def read_plan(a) -> dict:
    rd, st = HOST._state_of(a.run)
    nn = HOST._cf_nn(a.video)
    ftag = HOST._fmt_tag(st, getattr(a, "format", None))
    tlp = rd / "40-briefs" / f"video-{nn}-timeline{HOST._fmt_sfx(ftag)}.json"
    tl = _read_json(tlp)
    if not isinstance(tl, dict):
        _fail(f"no timeline: run `T slideshow plan --run RUN --video {nn}` first (with --format for an extra format); nothing was changed", 2)
    rows = sorted(tl.get("images") or [], key=lambda r: float(r["start"]))
    if not rows:
        _fail(f"the timeline {tlp} has no images; nothing was changed", 2)
    missing = [r["image"] for r in rows if not r.get("file") or not Path(str(r["file"])).is_file()]
    if missing:
        _fail("images without a file on disk: " + ", ".join(str(m) for m in missing[:12]) + " (the stills are made at S3); nothing was changed", 2)
    fmt = HOST._fmt_for(st, ftag)
    export = fmt.get("export") or tl.get("export")
    if not export:
        _fail("the run has no export size (state.json -> static.format.export; `T static format`); nothing was changed", 2)
    W, Ht = HOST._parse_size(export)
    if W % 2 or Ht % 2:
        _fail(f"the canvas needs even edges, got {export}", 2)
    out_dir = rd / "60-outputs" / f"video-{nn}" / (ftag or "")
    return {"rd": rd, "st": st, "nn": nn, "ftag": ftag, "tlp": tlp, "tl": tl, "rows": rows, "W": W, "H": Ht, "fps": int(tl.get("fps") or 30),
            "total": float(tl.get("duration_s") or rows[-1].get("end") or 0), "out_dir": out_dir, "fmt": fmt}


# --------------------------------------------------------------------------- the spec: stills, audio, joins

def plan_stills(P: dict, ctx: dict, ph: Path) -> tuple:
    """The main track: every still as a photo item on the placeholder (its real file, size and name kept for after compile), and the joins as transition operations."""
    rd, rows = P["rd"], P["rows"]
    pro_ok = HOST._capcut_pro_ok(rd)
    items, ops, done, failed, moves, stills = [], [], [], [], [], []
    for k, r in enumerate(rows):
        ref = f"i{r['image']}"
        s_us, e_us = _us(r["start"]), _us(r["end"])
        if e_us <= s_us:
            _fail(f"image {r['image']} has no span (start {r['start']}, end {r['end']}); fix the plan and run `T slideshow plan` again; nothing was changed", 2)
        w, h = image_size(Path(r["file"]))
        items.append({"ref": ref, "path": _norm(ph), "type": "photo", "start": s_us / US, "duration": (e_us - s_us) / US, "width": w, "height": h})
        ctx["inplace"][ref] = {"kind": "photo", "path": _norm(r["file"]), "name": Path(r["file"]).name, "width": w, "height": h}
        mv = {"scale": [float(x) for x in r["scale"]], "x": [float(x) for x in r["x"]], "y": [float(x) for x in r["y"]]} if "scale" in r else \
            HOST._still_motion(r)
        moves.append({"ref": ref, "image": r["image"], **{kk: mv[kk] for kk in ("scale", "x", "y")}})
        stills.append({"ref": ref, "image": r["image"], "start_us": s_us, "dur_us": e_us - s_us})
        if k:
            slug = str(r.get("transition") or "cut")
            if slug == "cut":
                continue
            why = HOST._catalogue_refusal("transition", slug, pro_ok)
            if why:
                failed.append({"image": r["image"], "slug": slug, "error": why})
                continue
            tr_s = float(r.get("trans_s") or 0.5)
            ops.append({"op": "transition", "target": f"i{rows[k - 1]['image']}", "slug": slug, "duration": round(tr_s, 3)})
            done.append({"into_image": r["image"], "transition": slug, "s": tr_s})
    ctx["moves"], ctx["stills"] = moves, stills
    ctx["transitions"] = {"done": done, "failed": failed}
    return [{"type": "video", "name": MAIN_TRACK, "items": items}], ops


def plan_audio(P: dict, ctx: dict, ph: Path) -> list:
    """The narration (at the timeline's offset, volume 1) and the bed (at 0, the timeline's gain), each on a track of its own, in place."""
    tl, tracks = P["tl"], []
    nar = Path(str(tl.get("narration") or ""))
    if not nar.is_file():
        _fail(f"the narration file is not there: {nar}; nothing was changed", 2)
    files = [nar] + ([Path(str(tl["music"]["file"]))] if tl.get("music") else [])
    for f in files[1:]:
        if not f.is_file():
            _fail(f"the bed file is not there: {f}; nothing was changed", 2)
    facts = probe_many(files)
    for f in files:
        if not float(facts[str(f)].get("duration_s") or 0):
            _fail(f"{f} has no readable length; nothing was changed", 2)
    off = float(tl.get("narration_offset") or 0.0)
    d_nar = _us(facts[str(nar)]["duration_s"])
    tracks.append({"type": "audio", "name": NARRATION_TRACK, "items": [{"ref": "nar", "path": _norm(ph), "start": _us(off) / US, "duration": d_nar / US, "volume": 1.0}]})
    ctx["inplace"]["nar"] = {"kind": "audio", "path": _norm(nar), "name": nar.name, "duration_us": d_nar}
    ctx["audio"] = {"narration": {"ref": "nar", "start_us": _us(off), "dur_us": d_nar, "volume": 1.0}}
    ctx["need_s"] = d_nar / US
    if tl.get("music"):
        bed = Path(str(tl["music"]["file"]))
        gain = float(tl["music"].get("gain") or 0.0)
        d_bed = _us(facts[str(bed)]["duration_s"])
        tracks.append({"type": "audio", "name": BED_TRACK, "items": [{"ref": "bed", "path": _norm(ph), "start": 0.0, "duration": d_bed / US, "volume": gain}]})
        ctx["inplace"]["bed"] = {"kind": "audio", "path": _norm(bed), "name": bed.name, "duration_us": d_bed}
        ctx["audio"]["bed"] = {"ref": "bed", "start_us": 0, "dur_us": d_bed, "volume": gain}
        ctx["need_s"] = max(ctx["need_s"], d_bed / US)
    return tracks


# --------------------------------------------------------------------------- the spec: effects, drawings, sounds

def _fx_keyed_pairs(v, off: float):
    return HOST._fx_keyed(v, off)


def plan_effects(P: dict, ctx: dict) -> tuple:
    """The timeline's effects: overlays (each on its own video track above the stills), drawing clips (draw1, draw2 ...), and sounds (an audio track each), by the way the CapCut
    effects check verified (T capcut-effects' own decision, `_fx_method`). An effect that needs something the check did not verify is refused and listed, never written."""
    tl, rd = P["tl"], P["rd"]
    fxs = tl.get("effects") or []
    ctx["effects"] = {"written": [], "refused": []}
    if not fxs:
        return [], []
    ver = HOST._fx_catalogue()
    if not ver:
        _fail("no verified effects in data/capcut-catalogue.json: the CapCut effects check has not been run (reference/static §9); nothing was changed", 2)
    W, Ht = P["W"], P["H"]
    scan = {str(f.get("id")): f for f in (_read_json(rd / "00-inventory" / "effects.json", {}) or {}).get("files") or []}
    prep = rd / "30-assets" / "effects" / f"video-{P['nn']}"
    pro_ok = HOST._capcut_pro_ok(rd)
    by_track, order = {}, []
    for e in sorted(fxs, key=lambda e: (e["type"] != "overlay", bool(e.get("drawing")), str(e.get("track")), e["start"])):
        e = {**e, "_facts": scan.get(str(e.get("id"))) or {}}
        method, why_not = HOST._fx_method(e, ver, pro_ok)
        if method is None:
            ctx["effects"]["refused"].append({"effect": e["n"], "file": Path(e["file"]).name, "not_verified": why_not})
            continue
        src, w, h, sound = Path(e["file"]), float(e.get("width") or W), float(e.get("height") or Ht), None
        try:
            if method.startswith(("keyed-file", "luma-file")):
                bx = (((e.get("_facts") or {}).get("picture") or {}).get("visible_box")) if e.get("fit") == "cover" else None
                src = HOST._fx_prepare(src, "keyed" if method.startswith("keyed") else "luma", method.split(":", 1)[1], prep / f"effect-{e['n']:02d}",
                                       e.get("key_color"), e.get("key_intensity"), tuple(bx) if bx else None)
                info = HOST.media_summary(src)
                w, h = float(info.get("display_width") or w), float(info.get("display_height") or h)
            elif e["type"] == "overlay" and e.get("has_audio"):
                src = HOST._fx_silent_copy(src, prep / f"effect-{e['n']:02d}")
            if e["type"] == "overlay" and e.get("has_audio") and float(e.get("volume") or 0) > 0:
                sound = HOST._fx_sound_of(Path(e["file"]), prep / f"effect-{e['n']:02d}")
        except (OSError, RuntimeError) as ex:
            ctx["effects"]["refused"].append({"effect": e["n"], "file": Path(e["file"]).name, "error": str(ex)[-300:]})
            continue
        if e["type"] == "overlay":
            ref = f"fx{e['n']}"
            it = {"ref": ref, "path": _norm(src), "start": _us(e["start"]) / US, "duration": _us(e["dur_s"]) / US, "sourceStart": round(float(e["in_s"]), 6),
                  "width": int(w), "height": int(h), "volume": 0.0}
            if e.get("kind") == "image":
                it["type"] = "photo"
            k = 1.0
            if e.get("fit") == "cover" and not method.startswith(("keyed-file", "luma-file")):
                k = max(W / w, Ht / h) / min(W / w, Ht / h)
            off = float(e.get("head_cut_s") or 0)
            sk, xk, yk = _fx_keyed_pairs(e.get("scale", 1.0), off), _fx_keyed_pairs(e.get("x", 0.0), off), _fx_keyed_pairs(e.get("y", 0.0), off)
            it["scale"], it["x"], it["y"] = round(k * sk[0][1], 6), round(xk[0][1], 6), round(yk[0][1], 6)
            it["opacity"] = float(e.get("opacity", 1.0))
            by_track.setdefault(("video", e["track"]), []).append(it)
            ctx["fx_posts"].append({"ref": ref, "kind": "overlay", "e": e, "k": k, "sk": sk, "xk": xk, "yk": yk, "method": method})
            if method in ("capcut-chroma", "capcut-screen"):
                ctx["cli_after"].append({"ref": ref, "method": method, "e": e})
            if sound is not None:
                sref = f"fxs{e['n']}"
                dur = HOST.media_summary(sound).get("duration_s")
                by_track.setdefault(("audio", f"{e['track']}-sound"), []).append(
                    {"ref": sref, "path": _norm(sound), "start": _us(e["start"]) / US, "duration": min(_us(e["dur_s"]), _us(dur or e["dur_s"])) / US, "volume": float(e["volume"])})
        else:
            ref = f"sfx{e['n']}"
            it = {"ref": ref, "path": _norm(src), "start": _us(e["start"]) / US, "duration": _us(e["dur_s"]) / US, "sourceStart": round(float(e["in_s"]), 6),
                  "volume": float(e["volume"])}
            by_track.setdefault(("audio", e["track"]), []).append(it)
            ctx["fx_posts"].append({"ref": ref, "kind": "sfx", "e": e, "method": method})
            if float(e.get("fade_in_s") or 0) or float(e.get("fade_out_s") or 0):
                ctx["fx_ops"].append({"op": "audio-fade", "target": ref, "fadeIn": float(e.get("fade_in_s") or 0) or None, "fadeOut": float(e.get("fade_out_s") or 0) or None})
        ctx["effects"]["written"].append({"effect": e["n"], "type": e["type"], "file": Path(e["file"]).name, "track": e["track"], "start": e["start"], "end": e["end"],
                                          "method": method, "sound_track": f"{e['track']}-sound" if sound is not None else None})
        if ("video" if e["type"] == "overlay" else "audio", e["track"]) not in order:
            order.append(("video" if e["type"] == "overlay" else "audio", e["track"]))
        if sound is not None and ("audio", f"{e['track']}-sound") not in order:
            order.append(("audio", f"{e['track']}-sound"))
    tracks = [{"type": typ, "name": name, "items": by_track[(typ, name)]} for typ, name in order if by_track.get((typ, name))]
    ops = []
    for o in ctx["fx_ops"]:
        ops.append({k: v for k, v in o.items() if v is not None})
    return tracks, ops


# --------------------------------------------------------------------------- the spec: captions and labels

def caption_state(P: dict) -> dict:
    """Which caption look this video takes and why, as facts: the plan's word box where the language takes it, else the plain look; an explicit --captions wins."""
    tl, rd, nn = P["tl"], P["rd"], P["nn"]
    cap = tl.get("captions") or {}
    out_dir = P["out_dir"]
    srt = out_dir / "captions.srt"
    res = {"cap": cap, "srt": srt, "wants": "word-box" if cap.get("word_box") else "plain", "language": None, "word_box_supported": None, "why_not": None}
    if not srt.is_file():
        return {**res, "error": f"no captions file: {srt} (`T slideshow plan` writes it)"}
    cues = HOST._read_srt(srt)
    said = (_read_json(rd / "30-assets" / "narration" / f"video-{nn}.json", {}) or {}).get("language")
    linfo = HOST._video_lang(P["st"], nn, said, text=" ".join(c["text"] for c in cues), soft=True)
    why_not = "written without spaces between words" if not linfo.get("spaced") else "written right to left" if linfo.get("direction") == "rtl" else None
    res.update({"cues": cues, "linfo": linfo, "word_box_supported": why_not is None, "why_not": why_not,
                "language": {k: linfo.get(k) for k in ("code", "name", "spaced", "direction", "scripts", "unit")}})
    return res


def plan_captions(P: dict, ctx: dict, mode: str, total_s: float) -> tuple:
    """The caption texts. word-box: one text per word and state on the plan's rounded colour box (the very plan T capcut-word-box makes, as compile text items with their
    style operations); plain: one text per cue in the references' outline look (a look with a box colour or highlight words keeps `capcut import-srt`, one call after compile)."""
    cs = caption_state(P)
    ctx["captions"] = {"mode": mode, "language": cs.get("language"), "word_box_supported": cs.get("word_box_supported"), "composed": False, "texts": 0, "tracks": 0}
    if mode == "none":
        return [], []
    if cs.get("error"):
        _fail(cs["error"] + "; nothing was changed", 2)
    cap = cs["cap"]
    for k in ("font_file", "size", "fill", "y_rel"):
        if k not in cap:
            _fail(f"captions leaves undecided: {k} (the plan's, static §5); nothing was changed", 2)
    font = str(cap["font_file"])
    if not Path(font).is_file():
        _fail(f"captions.font_file not found: {font}; nothing was changed", 2)
    y = round(1 - 2 * float(cap["y_rel"]), 4)
    outline = {}
    if cap.get("stroke_color") and float(cap.get("stroke_width") or 0) > 0:
        outline = {"borderWidth": float(cap["stroke_width"]), "borderColor": str(cap["stroke_color"])}
    if cap.get("shadow"):
        outline["shadow"] = True
    intro = cap.get("animation")
    if intro:
        why = HOST._catalogue_refusal("intro", str(intro), HOST._capcut_pro_ok(P["rd"]))
        if why:
            _fail(f"the caption entrance is refused: {why}; nothing was changed", 2, entrance=str(intro))
    ctx["intro"] = {"slug": str(intro), "dur": float(cap.get("animation_s") or 0.1)} if intro else None
    ctx["intro_plan"] = dict(ctx["intro"]) if ctx["intro"] else None
    tracks, ops, n = [], [], 0
    end_us = _us(total_s)
    ctx["text_tracks"] = {}
    if mode == "word-box":
        if not cs["word_box_supported"]:
            _fail(f"the word box does not take these captions: they are in {cs['language']['name']}, a language {cs['why_not']}. Nothing was changed; build again with "
                  "`--captions plain` (the plain caption look, static §7).", 2, word_box_supported=False, why=cs["why_not"], language=cs["language"])
        wb = cap.get("word_box") or {}
        miss = [k for k in HOST.WORD_BOX_KEYS if k not in wb]
        if miss:
            _fail("captions.word_box leaves undecided: " + ", ".join(miss) + " (the plan's, static §5); nothing was changed", 2)
        words = _read_json(P["rd"] / "30-assets" / "narration" / f"video-{P['nn']}.words.json")
        if words is None:
            _fail(f"no narration words: {P['rd'] / '30-assets' / 'narration' / ('video-' + P['nn'] + '.words.json')} (T narration-words); nothing was changed", 2)
        words = words.get("words", words) if isinstance(words, dict) else words
        rows, problems = HOST._word_box_plan(cs["cues"], words, float(P["tl"].get("narration_offset") or 0.0), P["fps"], info=cs["linfo"])
        if problems:
            _fail("the captions and the narration's words do not line up", 2, problems=problems[:8], count=len(problems))
        groups, geo = HOST._word_box_segments(rows, font, float(cap["size"]), P["W"], P["H"], float(wb["gap_em"]))
        if geo["widest_line_px"] > 0.92 * P["W"]:
            _fail("a caption line is wider than 92 % of the frame at this size; nothing was changed", 2, **geo)
        pad = float(wb.get("pad", HOST.WORD_BOX_PAD))
        ctx["box"] = {"pad": pad, "v_offset": float(wb.get("v_offset") or 0.0)}
        clipped = dropped = 0
        for key in sorted(groups, key=lambda k: (not k[1], k[0], not k[2])):
            i, boxed, first = key
            name = f"{WORD_BOX_PREFIX}-{i + 1}-{'box' if boxed else 'word'}{'-in' if first else ''}"
            items, entries = [], []
            for e in sorted(groups[key], key=lambda e: e["start"]):
                s_us, e_full = _us(e["start"]), _us(e["end"])
                e_us = min(e_full, end_us)
                if e_us - s_us < 1000:
                    dropped += 1
                    continue
                clipped += 1 if e_us < e_full else 0
                n += 1
                ref = f"cap{n}"
                items.append({"ref": ref, "text": e["text"], "start": s_us / US, "duration": (e_us - s_us) / US, "fontSize": float(cap["size"]),
                              "color": str(cap["fill"]), "x": e["x"], "y": y})
                entries.append({"ref": ref, "start_us": s_us, "dur_us": e_us - s_us})
                style = dict(outline)
                if boxed:
                    style.update({"bgColor": str(wb["color"]), "bgAlpha": float(wb["alpha"]), "bgStyle": int(wb["style"]), "bgRoundRadius": float(wb["round_radius"]),
                                  "bgWidth": pad, "bgHeight": pad, "bgHOffset": 0.0, "bgVOffset": ctx["box"]["v_offset"]})
                if style:
                    ops.append({"op": "text-style", "target": ref, "style": style})
            if items:
                tracks.append({"type": "text", "name": name, "items": items})
                ctx["text_tracks"][name] = {"font": font, "entrance": bool(first and intro), "boxed": boxed, "entries": entries}
        ctx["captions"].update({"composed": True, "texts": n, "tracks": len(tracks), "boxed_texts": sum(len(t["entries"]) for t in ctx["text_tracks"].values() if t["boxed"]),
                                "captions": len(rows), "geometry": geo, "clipped_at_end": clipped, "dropped": dropped, "word_box": {k: wb[k] for k in HOST.WORD_BOX_KEYS}})
        return tracks, ops
    # plain: one text per cue
    boxy = bool(cap.get("box_color")) or [w for w in cap.get("highlight_words") or [] if str(w).strip()]
    ctx["plain_info"] = {"font": font, "size": cap["size"], "fill": cap["fill"], "y": y, "cap": cap, "srt": str(cs["srt"])}
    if boxy:
        ctx["plain_import"] = ctx["plain_info"]
        ctx["captions"].update({"composed": False, "mode": "plain", "plain_import": True,
                                "note": "this look has a box colour or highlight words: `capcut import-srt` writes it (one call after compile)"})
        return [], []
    items, entries = [], []
    for c in cs["cues"]:
        s_us, e_full = _us(c["start"]), _us(c["end"])
        e_us = min(e_full, end_us)
        if e_us - s_us < 1000:
            continue
        n += 1
        ref = f"cap{n}"
        items.append({"ref": ref, "text": c["text"], "start": s_us / US, "duration": (e_us - s_us) / US, "fontSize": float(cap["size"]), "color": str(cap["fill"]),
                      "x": 0.0, "y": y})
        entries.append({"ref": ref, "start_us": s_us, "dur_us": e_us - s_us})
        if outline:
            ops.append({"op": "text-style", "target": ref, "style": dict(outline)})
    if items:
        tracks.append({"type": "text", "name": PLAIN_TRACK, "items": items})
        ctx["text_tracks"][PLAIN_TRACK] = {"font": font, "entrance": bool(intro), "boxed": False, "entries": entries}
    ctx["captions"].update({"composed": True, "mode": "plain", "texts": n, "tracks": len(tracks), "captions": len(cs["cues"])})
    return tracks, ops


def plan_labels(P: dict, ctx: dict, total_s: float) -> tuple:
    """The timeline's labels (a place's name on a map) as texts on the tracks labels, labels-2 ... over their images' spans, in the plan's labels_style."""
    tl = P["tl"]
    rows = [r for r in tl.get("images") or [] if r.get("labels")]
    ctx["labels"] = {"count": 0, "tracks": []}
    if not rows:
        return [], []
    style = tl.get("labels_style") or {}
    miss = [k for k in HOST.LABEL_STYLE_KEYS if k not in style]
    if miss:
        _fail("labels_style leaves undecided: " + ", ".join(miss) + " (the plan's, static §5); nothing was changed", 2)
    if not Path(str(style["font_file"])).is_file():
        _fail(f"labels_style.font_file not found: {style['font_file']}; nothing was changed", 2)
    lanes, by_lane, ops, n = [], {}, [], 0
    outline = {"borderWidth": float(style["stroke_width"]), "borderColor": str(style["stroke_color"])}
    if style.get("shadow"):
        outline["shadow"] = True
    for r in rows:
        start, dur = float(r["start"]), float(r["end"]) - float(r["start"])
        for lb in r["labels"]:
            x, y = round(2 * float(lb["x_rel"]) - 1, 4), round(1 - 2 * float(lb["y_rel"]), 4)
            lane = next((k for k, end in enumerate(lanes) if end <= start + 1e-6), None)
            if lane is None:
                lanes.append(0.0)
                lane = len(lanes) - 1
            lanes[lane] = start + dur
            track = LABEL_TRACK if lane == 0 else f"{LABEL_TRACK}-{lane + 1}"
            s_us, e_us = _us(start), min(_us(start + dur), _us(total_s))
            if e_us - s_us < 1000:
                continue
            n += 1
            ref = f"lab{n}"
            by_lane.setdefault(track, []).append({"ref": ref, "text": str(lb["text"]), "start": s_us / US, "duration": (e_us - s_us) / US, "fontSize": float(style["size"]),
                                                   "color": str(style["fill"]), "x": x, "y": y})
            ops.append({"op": "text-style", "target": ref, "style": dict(outline)})
    tracks = [{"type": "text", "name": t, "items": its} for t, its in by_lane.items()]
    ctx["labels"] = {"count": n, "tracks": sorted(by_lane), "font": str(style["font_file"]),
                     "on_moving_images": [r["image"] for r in rows if str(r.get("motion") or "none") != "none"]}
    for t in by_lane:
        ctx["text_tracks"][t] = {"font": str(style["font_file"]), "entrance": False, "boxed": False, "label": True,
                                 "entries": [{"ref": it["ref"], "start_us": _us(it["start"]), "dur_us": _us(it["duration"])} for it in by_lane[t]]}
    return tracks, ops


# --------------------------------------------------------------------------- one pass over each copy of the timeline

def kf_list(prop: str, dur_us: int, v0: float, v1: float) -> dict:
    def one(t, v):
        return {"id": str(uuid.uuid4()).upper(), "curveType": "Line", "time_offset": int(t), "left_control": {"x": 0.0, "y": 0.0}, "right_control": {"x": 0.0, "y": 0.0},
                "values": [float(v)], "string_value": "", "graphID": ""}
    return {"id": str(uuid.uuid4()).upper(), "material_id": "", "property_type": prop, "keyframe_list": [one(0, v0), one(dur_us, v1)]}


def kf_multi(prop: str, keys: list) -> dict:
    return {"id": str(uuid.uuid4()).upper(), "material_id": "", "property_type": prop,
            "keyframe_list": [{"id": str(uuid.uuid4()).upper(), "curveType": "Line", "time_offset": int(t), "left_control": {"x": 0.0, "y": 0.0},
                               "right_control": {"x": 0.0, "y": 0.0}, "values": [float(v)], "string_value": "", "graphID": ""} for t, v in keys]}


def _anim_template(content: dict, slug: str):
    for m in content.get("materials", {}).get("material_animations", []):
        for an in m.get("animations") or []:
            if an.get("type") == "in" and HOST._anim_slug(an.get("name")) == slug:
                return m, an
    return None, None


def _seg_has_in(content: dict, seg: dict) -> bool:
    refs = set(seg.get("extra_material_refs") or [])
    return any(m.get("id") in refs and any(an.get("type") == "in" for an in m.get("animations") or []) for m in content.get("materials", {}).get("material_animations", []))


def apply_font(m: dict, font: str) -> bool:
    """The font file on one text material (the family capcut-cli's text flags cannot set) and, with it, the outline, box and shadow where CapCut 9.x draws them from."""
    m.update({"font_name": "", "font_title": "none", "font_id": "", "font_resource_id": "", "font_category_id": "", "font_category_name": "", "font_source_platform": 0,
              "font_team_id": "", "font_url": "", "fonts": [], "font_path": font})
    try:
        c = json.loads(m.get("content") or "{}")
    except ValueError:
        c = {}
    HOST._text_outline_into_styles(m, c)
    for s in c.get("styles") or []:
        s["font"] = {"id": "", "path": font}
    if c:
        m["content"] = json.dumps(c, ensure_ascii=False, separators=(",", ":"))
    return True


def edit_copy(c: dict, ctx: dict, main_copy: bool) -> dict:
    """Everything compile cannot write, in one pass over one copy of the timeline: the real media behind the placeholders, the moves' keyframes, the overlays' sizes and keys, the
    font of every caption and label text, the box field and the entrance. Facts are returned from the main copy."""
    refs = ctx["refs"]
    tracks = c.get("tracks") or []
    segs = {s.get("id"): s for t in tracks for s in t.get("segments") or []}
    mats = c.get("materials") or {}
    mv = {m.get("id"): m for m in mats.get("videos") or []}
    ma = {m.get("id"): m for m in mats.get("audios") or []}
    mt = {m.get("id"): m for m in mats.get("texts") or []}
    facts = {"retargeted": 0, "keyed": 0, "unmatched": [], "fonts_set": 0, "box_fill": 0, "intro_cloned": 0, "intro_kept": 0, "overlays_set": 0}
    for ref, real in ctx["inplace"].items():
        seg = segs.get(refs.get(ref))
        m = None if seg is None else (ma if real["kind"] == "audio" else mv).get(seg.get("material_id"))
        if m is None:
            facts["unmatched"].append(ref)
            continue
        m["path"] = real["path"]
        if real["kind"] == "audio":
            m["name"], m["duration"] = real["name"], int(real["duration_us"])
        else:
            m["material_name"], m["width"], m["height"] = real["name"], int(real["width"]), int(real["height"])
        facts["retargeted"] += 1
    kfc = ctx["_kf"]
    for mvx in ctx["moves"]:
        seg = segs.get(refs.get(mvx["ref"]))
        if seg is None:
            facts["unmatched"].append(mvx["ref"])
            continue
        dur = int(seg["target_timerange"]["duration"])
        (s0, s1), (x0, x1), (y0, y1) = mvx["scale"], mvx["x"], mvx["y"]
        kfs = [k for k in seg.get("common_keyframes") or [] if k.get("property_type") not in MOVE_PROPS]
        for prop, pair, off in (("KFTypeScaleX", (s0, s1), (1.0, 1.0)), ("KFTypePositionX", (x0, x1), (0.0, 0.0)), ("KFTypePositionY", (y0, y1), (0.0, 0.0))):
            if tuple(pair) != off:
                key = (prop, mvx["ref"])
                if key not in kfc:
                    kfc[key] = kf_list(prop, dur, pair[0], pair[1])
                kfs.append(copy.deepcopy(kfc[key]))
        seg["common_keyframes"] = kfs
        seg["uniform_scale"] = {"on": True, "value": 1.0}
        clip = seg.setdefault("clip", {})
        clip["scale"] = {"x": float(s0), "y": float(s0)}
        clip["transform"] = {"x": float(x0), "y": float(y0)}
        facts["keyed"] += 1
    for fx in ctx["fx_posts"]:
        seg = segs.get(refs.get(fx["ref"]))
        if seg is None:
            facts["unmatched"].append(fx["ref"])
            continue
        e = fx["e"]
        fd = e.get("file_duration_s")
        if fd:
            m = (mv if fx["kind"] == "overlay" else ma).get(seg.get("material_id"))
            if m is not None:
                m["duration"] = int(round(float(fd) * US))
        if fx["kind"] == "overlay":
            kfs = [x for x in seg.get("common_keyframes") or [] if x.get("property_type") not in MOVE_PROPS]
            for prop, ks, mul in (("KFTypeScaleX", fx["sk"], fx["k"]), ("KFTypePositionX", fx["xk"], 1.0), ("KFTypePositionY", fx["yk"], 1.0)):
                if len(ks) > 1:
                    key = (prop, fx["ref"])
                    if key not in kfc:
                        kfc[key] = kf_multi(prop, [(t * US, v * mul) for t, v in ks])
                    kfs.append(copy.deepcopy(kfc[key]))
            seg["common_keyframes"] = kfs
            if len(fx["sk"]) > 1:
                seg["uniform_scale"] = {"on": True, "value": 1.0}
            facts["overlays_set"] += 1
    intro = ctx.get("intro")
    tmpl = ctx.get("_anim") if intro else None
    for name, tt in ctx["text_tracks"].items():
        for ent in tt["entries"]:
            seg = segs.get(refs.get(ent["ref"]))
            m = mt.get(seg.get("material_id")) if seg else None
            if seg is None or m is None:
                facts["unmatched"].append(ent["ref"])
                continue
            apply_font(m, tt["font"].replace("\\", "/"))
            facts["fonts_set"] += 1
            if tt["boxed"] and ctx.get("box"):
                bx = ctx["box"]
                m.update({"background_width": bx["pad"], "background_height": bx["pad"], "background_horizontal_offset": 0.0, "background_vertical_offset": bx["v_offset"],
                          "background_fill": ""})
                facts["box_fill"] += 1
            if tt["entrance"] and tmpl is not None:
                if _seg_has_in(c, seg):
                    facts["intro_kept"] += 1
                else:
                    am, an = tmpl
                    an = copy.deepcopy(an)
                    seg_us = int((seg.get("target_timerange") or {}).get("duration") or 0)
                    an["duration"] = max(1000, min(_us(intro["dur"]), seg_us))
                    an["start"] = 0
                    mid = ctx["_anim_ids"].setdefault(seg["id"], str(uuid.uuid4()))
                    mats.setdefault("material_animations", []).append({**copy.deepcopy(am), "id": mid, "animations": [an]})
                    seg.setdefault("extra_material_refs", []).append(mid)
                    facts["intro_cloned"] += 1
    return facts


# --------------------------------------------------------------------------- compile, the older fallbacks, repair

def make_cover(d: Path, first_image: Path, W: int, Ht: int) -> bool:
    """The project's thumbnail on CapCut's home screen: the first still on the canvas's shape."""
    sc = 540.0 / max(W, Ht)
    cw, ch = max(2, int(W * sc) // 2 * 2), max(2, int(Ht * sc) // 2 * 2)
    cp = HOST.run([HOST.find_tool("ffmpeg"), "-hide_banner", "-loglevel", "error", "-nostdin", "-y", "-i", str(first_image), "-frames:v", "1",
                   "-vf", f"scale={cw}:{ch}:force_original_aspect_ratio=increase,crop={cw}:{ch}", "-q:v", "3", str(d / "draft_cover.jpg")], timeout=120)
    return cp.returncode == 0 and (d / "draft_cover.jpg").is_file()


def clean_media_pool(d: Path) -> list:
    """compile lists the placeholder in the draft's media pool; drop every entry whose file is not there (the repair adds the real media)."""
    p = d / "draft_meta_info.json"
    j = _read_json(p)
    if not isinstance(j, dict):
        return []
    removed = []
    for g in j.get("draft_materials") or []:
        keep = []
        for e in g.get("value") or []:
            fp = str(e.get("file_Path") or "")
            path = Path(fp) if re.match(r"^[A-Za-z]:[\\/]", fp) else (d / fp)
            if path.is_file():
                keep.append(e)
            else:
                removed.append(str(e.get("extra_info") or fp))
        g["value"] = keep
    if removed:
        p.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
    return removed


def prune_backups(d: Path) -> float:
    """capcut-cli keeps an undo snapshot of the whole draft after every write (<draft>/.capcut-cli-history) and *.bak copies stay beside the documents: dropped after a good build."""
    freed = 0
    h = Path(d) / ".capcut-cli-history"
    if h.is_dir():
        for f in h.glob("*.snap"):
            try:
                freed += f.stat().st_size
                f.unlink()
            except OSError:
                pass
        try:
            h.rmdir()
        except OSError:
            pass
    for f in Path(d).glob("*.bak"):
        try:
            freed += f.stat().st_size
            f.unlink()
        except OSError:
            pass
    return round(freed / 1048576, 1)


def repair(d: Path) -> list:
    """`capcut register --apply --materials`, the media links CapCut 9.3+ opens a clip by, `sync-timelines --nested` and `lint`, under the machine-wide store lock (the text stays as
    set: the look is the references', never a house style)."""
    cli = HOST._capcut_cli()
    steps = []
    with HOST.FileLock(store_lock_path(), timeout=900, stale=300):
        for name, args in (("register", ["register", str(d), "--apply", "--materials"]), ("link", None),
                           ("sync-timelines", ["sync-timelines", str(d), "--nested", "--apply"]), ("lint", ["lint", str(d)])):
            if args is None:
                try:
                    steps.append({"step": name, "exit": 0, "result": HOST._link_local_materials(d)})
                except (OSError, ValueError) as e:
                    steps.append({"step": name, "exit": 1, "result": f"{type(e).__name__}: {e}"})
                    break
                continue
            cp = HOST.run([cli, *args], timeout=900)
            steps.append({"step": name, "exit": cp.returncode, "result": _last_json(cp.stdout) or (cp.stdout or "").strip()[-800:], "stderr": (cp.stderr or "").strip()[-400:]})
            if name != "lint" and cp.returncode != 0:
                break
    return steps


def run_cli_steps(d: Path, ctx: dict) -> list:
    """The few writes capcut-cli has a command for and compile has no operation for: CapCut's own chroma key or screen blend on an overlay (only when the effects check showed
    them playing), and the entrance animation's template (one call; the other texts take a copy of it in the one pass)."""
    cli, res = HOST._capcut_cli(), []
    for s in ctx["cli_after"]:
        sid, e = ctx["refs"].get(s["ref"]), s["e"]
        args = ["chroma", str(d), sid, "--color", str(e["key_color"]), "--intensity", f"{float(e['key_intensity']):.3f}"] if s["method"] == "capcut-chroma" \
            else ["mix-mode", str(d), sid, "screen"]
        cp = HOST.run([cli, *args], timeout=120)
        res.append({"step": args[0], "effect": e["n"], "exit": cp.returncode, **({} if cp.returncode == 0 else {"error": (cp.stdout or cp.stderr or "")[-300:]})})
    intro = ctx.get("intro")
    if intro:
        names = [n for n, t in ctx["text_tracks"].items() if t["entrance"]]
        first = next((ctx["text_tracks"][n]["entries"][0]["ref"] for n in names if ctx["text_tracks"][n]["entries"]), None)
        if first:
            dur = ctx["text_tracks"][next(n for n in names if ctx["text_tracks"][n]["entries"])]["entries"][0]["dur_us"] / US
            cp = HOST.run([cli, "text-anim", str(d), str(ctx["refs"][first]), "--intro", intro["slug"], "--intro-duration", f"{max(0.001, min(float(intro['dur']), dur)):.3f}s"], timeout=120)
            if cp.returncode != 0:
                res.append({"step": "text-anim", "exit": cp.returncode, "error": str((_last_json(cp.stdout) or {}).get("error") or cp.stderr or cp.stdout)[-300:]})
            else:
                res.append({"step": "text-anim", "exit": 0, "slug": intro["slug"]})
    return res


def _self(args: list, timeout: float):
    """This toolkit's own command (the older way's pieces), run as a process: (the completed process, its last JSON line)."""
    r = HOST.run([sys.executable, str(Path(HOST.__file__).resolve()), *args], timeout=timeout)
    return r, (_last_json(r.stdout) or {})


def older_steps(d: Path, P: dict, ctx: dict, mode: str, fallback: bool) -> list:
    """What the composition leaves to a command each, named in the answer: the plain caption look that has a box colour or highlight words (`capcut import-srt`, one call), and
    after a compile that refused the joins or the texts everything those carried (the joins one clip at a time, the word box and the labels by their commands, a font and an
    entrance per track)."""
    steps, rd, nn, ftag = [], P["rd"], P["nn"], P["ftag"]
    fmt_args = ["--format", ftag] if ftag else []
    intro = ctx.get("intro_plan")
    if fallback and ctx["transitions"]["done"]:
        ctx["transitions"] = legacy_transitions(d, ctx, P["rows"])
        steps.append({"step": "transitions", "exit": 0 if not ctx["transitions"]["failed"] else 1, "done": len(ctx["transitions"]["done"]),
                      "failed": ctx["transitions"]["failed"][:3]})
    cap = P["tl"].get("captions") or {}
    if fallback and mode == "word-box":
        r, js = _self(["capcut-word-box", "--draft", str(d), "--run", str(rd), "--video", nn, *fmt_args], 1800)
        steps.append({"step": "capcut-word-box", "exit": r.returncode, "texts": js.get("texts"), "error": js.get("error")})
        for tr in js.get("tracks") or []:
            r2, _ = _self(["capcut-font", "--draft", str(d), "--font-file", str(cap["font_file"]), "--track", tr["track"]], 600)
            steps.append({"step": "capcut-font:" + tr["track"], "exit": r2.returncode})
            if intro and tr.get("entrance"):
                r3, _ = _self(["capcut-text-anim", "--draft", str(d), "--track", tr["track"], "--intro", intro["slug"], "--intro-duration", str(intro["dur"]), "--run", str(rd)], 600)
                steps.append({"step": "capcut-text-anim:" + tr["track"], "exit": r3.returncode})
    pi = ctx.get("plain_import") or (ctx.get("plain_info") if fallback and mode == "plain" else None)
    if pi and mode == "plain":
        c = pi["cap"]
        cargs = [HOST._capcut_cli(), "import-srt", str(d), pi["srt"], "--track-name", PLAIN_TRACK, "--font-size", str(pi["size"]), "--color", str(pi["fill"]),
                 "--border-width", str(c.get("stroke_width") or 0), "--border-color", str(c.get("stroke_color") or "#000000"), "--align", "1", "--y", str(pi["y"])]
        if c.get("shadow"):
            cargs.append("--shadow")
        if c.get("box_color"):
            cargs += ["--bg-color", str(c["box_color"]), "--bg-alpha", str(c.get("box_alpha", 1.0))]
        hw = [w for w in c.get("highlight_words") or [] if str(w).strip()]
        if hw:
            hf = P["out_dir"] / "highlight-words.txt"
            hf.write_text("\n".join(hw) + "\n", encoding="utf-8")
            cargs += ["--highlight-words", f"@{hf}", "--keyword-color", str(c.get("highlight_color") or pi["fill"]), "--keyword-size", str(c.get("highlight_size") or pi["size"])]
        r = HOST.run(cargs, timeout=900)
        steps.append({"step": "import-srt", "exit": r.returncode, "result": _last_json(r.stdout) or (r.stdout or "")[-300:]})
        r2, _ = _self(["capcut-font", "--draft", str(d), "--font-file", pi["font"], "--track", PLAIN_TRACK], 600)
        steps.append({"step": "capcut-font:" + PLAIN_TRACK, "exit": r2.returncode})
        if intro:
            r3, _ = _self(["capcut-text-anim", "--draft", str(d), "--track", PLAIN_TRACK, "--intro", intro["slug"], "--intro-duration", str(intro["dur"]), "--run", str(rd)], 600)
            steps.append({"step": "capcut-text-anim:" + PLAIN_TRACK, "exit": r3.returncode})
    if fallback and ctx["labels"]["count"]:
        r, js = _self(["capcut-labels", "--draft", str(d), "--run", str(rd), "--video", nn, *fmt_args], 1800)
        steps.append({"step": "capcut-labels", "exit": r.returncode, "labels": js.get("labels"), "error": js.get("error")})
    return steps


def legacy_transitions(d: Path, ctx: dict, rows: list) -> dict:
    """Only after a compile that refused the joins: capcut-cli's `transition` per join, clip by clip (the older way)."""
    cli = HOST._capcut_cli()
    c = _read_json(d / "draft_content.json") or {}
    main = next((t for t in c.get("tracks", []) if t.get("type") == "video" and t.get("name") == MAIN_TRACK), None)
    segs = sorted((main or {}).get("segments") or [], key=lambda s: int(s["target_timerange"]["start"]))
    done, failed = [], list(ctx["transitions"]["failed"])
    for t in ctx["transitions"]["done"]:
        k = next((i for i, r in enumerate(rows) if int(r["image"]) == int(t["into_image"])), None)
        if not k or k - 1 >= len(segs):
            failed.append({"image": t["into_image"], "error": "no clip before this image"})
            continue
        cp = HOST.run([cli, "transition", str(d), str(segs[k - 1]["id"]), t["transition"], "--duration", f"{float(t['s']):.3f}s"], timeout=120)
        (done if cp.returncode == 0 else failed).append(t if cp.returncode == 0 else {"image": t["into_image"], "error": (cp.stdout or cp.stderr or "")[-300:]})
    return {"done": done, "failed": failed}


# --------------------------------------------------------------------------- the read-back

def read_back(d: Path, P: dict, ctx: dict, repair_steps: list) -> dict:
    """The finished project against the timeline, in one pass: facts only (build turns the ones that disagree into problems)."""
    c = _read_json(d / "draft_content.json") or {}
    tracks = c.get("tracks") or []
    mats = c.get("materials") or {}
    rows, fps = P["rows"], P["fps"]
    main = next((t for t in tracks if t.get("type") == "video" and str(t.get("name") or "") == MAIN_TRACK), None)
    segs = sorted((main or {}).get("segments") or [], key=lambda s: int(s["target_timerange"]["start"]))
    ends = [int(s["target_timerange"]["start"]) + int(s["target_timerange"]["duration"]) for s in segs]
    off_by = [{"image": r["image"], "planned_start_us": st["start_us"], "start_us": int(s["target_timerange"]["start"]), "planned_dur_us": st["dur_us"],
               "dur_us": int(s["target_timerange"]["duration"])}
              for r, st, s in zip(rows, ctx["stills"], segs)
              if abs(int(s["target_timerange"]["start"]) - st["start_us"]) > 1 or abs(int(s["target_timerange"]["duration"]) - st["dur_us"]) > 1]
    joins_bad = sum(1 for s, e in zip(segs[1:], ends) if abs(int(s["target_timerange"]["start"]) - e) > 1)
    keyed = sum(1 for s in segs if s.get("common_keyframes"))
    wanted_keyed = sum(1 for m in ctx["moves"] if tuple(m["scale"]) != (1.0, 1.0) or tuple(m["x"]) != (0.0, 0.0) or tuple(m["y"]) != (0.0, 0.0))
    byname = {}
    for t in tracks:
        byname.setdefault(str(t.get("name") or ""), []).extend(t.get("segments") or [])
    aud = {}
    for key, a_ in (ctx.get("audio") or {}).items():
        tr = byname.get(NARRATION_TRACK if key == "narration" else BED_TRACK) or []
        s = tr[0] if tr else None
        aud[key] = {"present": s is not None, "start_us": int(s["target_timerange"]["start"]) if s else None, "planned_start_us": a_["start_us"],
                    "volume": s.get("volume") if s else None, "planned_volume": a_["volume"]}
    mt = {m.get("id"): m for m in mats.get("texts") or []}
    texts_total = sum(len(t.get("segments") or []) for t in tracks if t.get("type") == "text")
    planned_texts = sum(len(t["entries"]) for t in ctx["text_tracks"].values())
    off_text = []
    for name, tt in ctx["text_tracks"].items():
        ss = sorted(byname.get(name) or [], key=lambda s: int(s["target_timerange"]["start"]))
        if len(ss) != len(tt["entries"]):
            off_text.append({"track": name, "texts": len(ss), "planned": len(tt["entries"])})
            continue
        for s, e in zip(ss, tt["entries"]):
            if abs(int(s["target_timerange"]["start"]) - e["start_us"]) > 2000:
                off_text.append({"track": name, "at_us": e["start_us"], "segment_start_us": int(s["target_timerange"]["start"])})
                break
    font_off = 0
    for name, tt in ctx["text_tracks"].items():
        for s in byname.get(name) or []:
            m = mt.get(s.get("material_id"))
            if m is not None and str(m.get("font_path") or "") != tt["font"].replace("\\", "/"):
                font_off += 1
    entr_planned = sum(len(t["entries"]) for t in ctx["text_tracks"].values() if t["entrance"])
    entr_have = sum(1 for n, t in ctx["text_tracks"].items() if t["entrance"] for s in byname.get(n) or [] if _seg_has_in(c, s))
    fx_missing = []
    for w in (ctx.get("effects") or {}).get("written") or []:
        tr = byname.get(w["track"]) or []
        if not any(abs(int(s["target_timerange"]["start"]) - _us(w["start"])) <= 2000 for s in tr):
            fx_missing.append({"effect": w["effect"], "track": w["track"], "start": w["start"]})
    missing = sorted({str(m.get("path")) for k in ("videos", "audios") for m in mats.get(k) or [] if m.get("path") and not Path(str(m["path"])).exists()})
    lint = next((s for s in repair_steps if s["step"] == "lint"), {})
    lr = lint.get("result") if isinstance(lint.get("result"), dict) else {}
    issues = lr.get("issues") or []
    codes = {}
    for i in issues:
        k = f"{i.get('severity')}:{i.get('code')}"
        codes[k] = codes.get(k, 0) + 1
    link = next((s for s in repair_steps if s["step"] == "link"), {})
    no_entry = ((link.get("result") or {}) if isinstance(link.get("result"), dict) else {}).get("media_without_entry") or []
    size = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
    return {"main_clips": len(segs), "planned_images": len(rows), "main_end_s": round(max(ends, default=0) / US, 3), "planned_s": float(P["total"]), "spans_off": off_by[:6],
            "joins_not_contiguous": joins_bad, "moves_keyed": keyed, "moves_planned": wanted_keyed, "transitions_in_draft": len(mats.get("transitions") or []),
            "transitions_planned": len(ctx["transitions"]["done"]), "audio": aud, "text_tracks": len([t for t in tracks if t.get("type") == "text"]), "texts": texts_total,
            "texts_planned": planned_texts, "texts_off": off_text[:6], "fonts_off": font_off, "entrances": entr_have, "entrances_planned": entr_planned, "effects_missing": fx_missing[:6],
            "media_missing": missing[:5], "media_without_entry": no_entry[:5], "draft_mb": round(size / 1048576, 1),
            "lint": {"errors": (lr.get("summary") or {}).get("errors"), "warnings": (lr.get("summary") or {}).get("warnings"), "by_code": codes,
                     "error_messages": [str(i.get("message"))[:160] for i in issues if i.get("severity") == "error"][:5], "exit": lint.get("exit")},
            "canvas": c.get("canvas_config"), "duration_us": c.get("duration")}


# --------------------------------------------------------------------------- the build

def build(a) -> dict:
    t0 = time.time()
    P = read_plan(a)
    mode_arg = str(getattr(a, "captions", None) or "auto")
    if mode_arg not in ("auto", "word-box", "plain", "none"):
        _fail("--captions is auto | word-box | plain | none", 2)
    spec_only = bool(getattr(a, "spec_only", False))
    if not spec_only and (HOST._capcut_running()):
        HOST.out({"ok": False, "action": "CapCut is running: close it and run this again (nothing was changed)"}, 3)
    store = Path(HOST._capcut_store(getattr(a, "store", None)))
    if not store.is_dir():
        _fail(f"CapCut drafts store not found: {store}", 2)
    name = getattr(a, "name", None) or free_name(store, P["nn"], P["ftag"])
    if (store / name).exists():
        _fail(f"{store / name} already exists (pick another --name)", 2)
    ctx = {"refs": {}, "inplace": {}, "moves": [], "stills": [], "fx_posts": [], "fx_ops": [], "cli_after": [], "text_tracks": {}, "intro": None, "box": None, "audio": {},
           "effects": {"written": [], "refused": []}, "need_s": 1.0, "_kf": {}, "_anim": None, "_anim_ids": {}, "transitions": {"done": [], "failed": []}}
    rd, tl = P["rd"], P["tl"]
    total_s = max(float(r["end"]) for r in P["rows"])
    # the whole timeline as one spec
    main_tracks, tr_ops = plan_stills(P, ctx, Path("."))      # the placeholder path is filled below
    audio_tracks = plan_audio(P, ctx, Path("."))
    ph = make_placeholder(rd, ctx["need_s"])
    for t in main_tracks + audio_tracks:
        for it in t["items"]:
            it["path"] = _norm(ph)
    fx_tracks, fx_ops = plan_effects(P, ctx)
    cs_ = caption_state(P) if mode_arg == "auto" else {"wants": mode_arg}
    mode = cs_["wants"] if mode_arg == "auto" else mode_arg
    cap_tracks, cap_ops = plan_captions(P, ctx, mode, total_s)
    lab_tracks, lab_ops = plan_labels(P, ctx, total_s)
    ratio = next((k for k in HOST.CAPCUT_RATIO_LABELS if HOST.STATIC_ASPECTS[k][0] * P["H"] == HOST.STATIC_ASPECTS[k][1] * P["W"]), "original")
    ops = tr_ops + fx_ops + cap_ops + lab_ops
    refused = {"joins_refused": ctx["transitions"]["failed"], "effects_refused": ctx["effects"]["refused"]}
    if (refused["joins_refused"] or refused["effects_refused"]) and not spec_only:
        _fail("the plan holds options the catalogue does not show this PC's CapCut drawing (or an effect it cannot write): plan those moments again without them, run "
              "`T slideshow plan`, and build again. Nothing was built.", 2, **refused)
    spec = {"name": name, "width": P["W"], "height": P["H"], "fps": P["fps"], "ratio": ratio, "tracks": main_tracks + audio_tracks + fx_tracks + cap_tracks + lab_tracks}
    if ops:
        spec["operations"] = ops
    P["out_dir"].mkdir(parents=True, exist_ok=True)
    spec_path = P["out_dir"] / "compose-spec.json"
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    facts_plan = {"images": len(P["rows"]), "tracks": len(spec["tracks"]), "items": sum(len(t["items"]) for t in spec["tracks"]), "operations": len(ops),
                  "transitions": len(ctx["transitions"]["done"]), "caption_mode": mode, "caption_texts": ctx["captions"].get("texts"), "labels": ctx["labels"]["count"],
                  "effects": len(ctx["effects"]["written"]), "effects_refused": ctx["effects"]["refused"]}
    if spec_only:
        return {"ok": not (refused["joins_refused"] or refused["effects_refused"]), "spec_only": True, "spec": str(spec_path), "name": name, "plan": facts_plan, **refused,
                "would_stop": bool(refused["joins_refused"] or refused["effects_refused"]),
                "captions": {k: v for k, v in ctx["captions"].items() if k not in ("geometry",)}, "labels": ctx["labels"],
                "effects": [{"effect": w["effect"], "type": w["type"], "track": w["track"], "method": w["method"]} for w in ctx["effects"]["written"]]}
    t_spec = time.time()
    # compile (the machine-wide lock around the index write); one retry without the joins and the texts when compile refuses them
    own = HOST.CS_HOME / "data" / "compose-template"
    tmpl = getattr(a, "template", None) or (str(own) if (own / "draft_content.json").is_file() else None)
    args = [HOST._capcut_cli(), "compile", str(spec_path), "--out", str(store / name)] + (["--template", str(tmpl)] if tmpl else [])
    d = store / name
    cp = locked_run(args, 900)
    extras_error, fallback = None, False
    if (cp.returncode != 0 or not (d / "draft_content.json").is_file()) and (ops or cap_tracks or lab_tracks):
        extras_error = ((cp.stderr or "") + (cp.stdout or ""))[-400:]
        if d.is_dir():
            shutil.rmtree(d, ignore_errors=True)       # this very command's own half-made folder (the name was free a moment ago), by its exact path
        fallback = True
        spec["tracks"] = main_tracks + audio_tracks + fx_tracks
        spec["operations"] = fx_ops
        if not fx_ops:
            spec.pop("operations", None)
        spec_path.write_text(json.dumps(spec, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        cp = locked_run(args, 900)
    if cp.returncode != 0 or not (d / "draft_content.json").is_file():
        if d.is_dir() and not (d / "draft_content.json").is_file():
            shutil.rmtree(d, ignore_errors=True)
        _fail("capcut compile failed: " + ((cp.stderr or "") + (cp.stdout or ""))[-500:], 1, spec=str(spec_path))
    t_comp = time.time()
    if fallback:                  # compile refused the joins or the texts: only the clips, the audio and the effects were composed; older_steps writes the rest
        ctx["text_tracks"], ctx["intro"] = {}, None
    res = _last_json(cp.stdout) or {}
    ctx["refs"] = dict(res.get("refs") or {})
    missing_refs = [r for r in ctx["inplace"] if r not in ctx["refs"]]
    if missing_refs:
        _fail(f"compile did not report its items' ids ({len(missing_refs)} missing, first {missing_refs[:3]}): is capcut-cli older than 0.25?", 1, draft=str(d))
    # the writes capcut-cli has a command for
    cli_steps = run_cli_steps(d, ctx) if not fallback else []
    if ctx.get("intro") and not fallback:
        c0 = _read_json(d / "draft_content.json") or {}
        ctx["_anim"] = _anim_template(c0, ctx["intro"]["slug"])
        if ctx["_anim"] == (None, None):
            ctx["_anim"] = None
    # one pass over every copy of the timeline
    facts, copies = {}, []
    for p in HOST._draft_contents(d):
        content = json.loads(p.read_text(encoding="utf-8"))
        f = edit_copy(content, ctx, p.name == "draft_content.json")
        _write_compact(p, content)
        copies.append(p.name)
        if p.name == "draft_content.json":
            facts = f
    # a placeholder's copy is not referenced any more
    for sub in ("video", "audio"):
        try:
            (d / "assets" / sub / ph.name).unlink(missing_ok=True)
            if (d / "assets" / sub).is_dir() and not any((d / "assets" / sub).iterdir()):
                (d / "assets" / sub).rmdir()
        except OSError:
            pass
    left = [str(x) for x in (d / "assets").rglob("*") if x.is_file() and x.suffix.lower() in (".mp4", ".mov", ".wav", ".png", ".jpg") and x.stat().st_size > 5_000_000] \
        if (d / "assets").is_dir() else []
    pool_removed = clean_media_pool(d)
    cover = make_cover(d, Path(P["rows"][0]["file"]), P["W"], P["H"])
    t_edit = time.time()
    legacy = older_steps(d, P, ctx, mode, fallback)
    rsteps = repair(d)
    chk = read_back(d, P, ctx, rsteps)
    cleanup_mb = None
    t_end = time.time()
    # problems: every fact that disagrees with the plan
    problems = []
    if facts.get("unmatched"):
        problems.append(f"{len(facts['unmatched'])} items of the composition have no clip in the draft: {facts['unmatched'][:5]}")
    if left:
        problems.append(f"big media files were copied into the draft instead of staying in place: {left[:3]}")
    if chk["main_clips"] != chk["planned_images"]:
        problems.append(f"the main track has {chk['main_clips']} clips and the timeline {chk['planned_images']} images")
    if chk["spans_off"]:
        problems.append(f"{len(chk['spans_off'])} clips are not at their image's start and span, first: {chk['spans_off'][0]}")
    if abs(chk["main_end_s"] - chk["planned_s"]) > 0.1:
        problems.append(f"the main track ends at {chk['main_end_s']} s and the timeline says {chk['planned_s']} s")
    if chk["joins_not_contiguous"]:
        problems.append(f"{chk['joins_not_contiguous']} clips do not start where the one before ends")
    if chk["moves_keyed"] < chk["moves_planned"]:
        problems.append(f"{chk['moves_planned']} images move and {chk['moves_keyed']} clips carry keyframes")
    if ctx["transitions"]["failed"]:
        problems.append(f"{len(ctx['transitions']['failed'])} joins were refused, first: {str(ctx['transitions']['failed'][0])[:200]}")
    elif chk["transitions_in_draft"] != chk["transitions_planned"] and not fallback:
        problems.append(f"the draft holds {chk['transitions_in_draft']} transitions and the timeline plans {chk['transitions_planned']}")
    for k, v in chk["audio"].items():
        if not v["present"]:
            problems.append(f"the {k} is not in the draft")
        elif v["start_us"] is not None and abs(v["start_us"] - v["planned_start_us"]) > 1:
            problems.append(f"the {k} starts at {v['start_us']} us, the timeline says {v['planned_start_us']} us")
    if ctx["effects"]["refused"]:
        problems.append(f"{len(ctx['effects']['refused'])} effects were not written, first: {str(ctx['effects']['refused'][0])[:200]}")
    if chk["effects_missing"]:
        problems.append(f"effects not on their track at their start: {chk['effects_missing'][:3]}")
    if not fallback and chk["texts"] != chk["texts_planned"] and not ctx.get("plain_import"):
        problems.append(f"the draft holds {chk['texts']} texts and the composition made {chk['texts_planned']}")
    if chk["texts_off"] and not fallback:
        problems.append(f"texts off their plan: {chk['texts_off'][:2]}")
    if chk["fonts_off"] and not fallback:
        problems.append(f"{chk['fonts_off']} texts do not carry their font")
    if chk["entrances"] < chk["entrances_planned"] and not fallback:
        problems.append(f"{chk['entrances_planned']} texts should start with the entrance and {chk['entrances']} do")
    for s in cli_steps + legacy:
        if s.get("exit") not in (None, 0):
            problems.append(f"step {s.get('step')} failed: {str(s.get('error') or s.get('result'))[:200]}")
    for s in rsteps:
        if s["step"] != "lint" and s.get("exit") not in (0, None):
            problems.append(f"repair step {s['step']} failed: {str(s.get('result') or s.get('stderr'))[:200]}")
    if chk["media_missing"]:
        problems.append(f"media files missing on disk: {chk['media_missing']}")
    if chk["media_without_entry"]:
        problems.append(f"media with no entry in the project's media list: {chk['media_without_entry']}")
    if chk["lint"]["errors"]:
        problems.append(f"capcut lint: {chk['lint']['errors']} errors: {chk['lint']['error_messages']}")
    elif chk["lint"]["errors"] is None:
        problems.append(f"capcut lint gave no summary (exit {chk['lint']['exit']})")
    cap_font = None
    if mode != "none":
        cs2 = ctx["captions"]
        font = (P["tl"].get("captions") or {}).get("font_file")
        txt = " ".join(c["text"] for c in (HOST._read_srt(P["out_dir"] / "captions.srt") if (P["out_dir"] / "captions.srt").is_file() else []))
        rep = HOST._font_report(font, txt) if font else {}
        cap_font = {"file": font, **rep}
        if rep.get("font_missing_glyphs"):
            problems.append(f"the caption font cannot draw these characters of the captions: {''.join(rep['font_missing_glyphs'])} (CapCut would show boxes or another font's letters)")
        del cs2
    if ctx["labels"]["count"]:
        lrep = HOST._font_report(str(tl["labels_style"]["font_file"]), "".join(str(lb.get("text") or "") for r in P["rows"] for lb in r.get("labels") or []))
        if lrep.get("font_missing_glyphs"):
            problems.append(f"the labels' font cannot draw these characters: {''.join(lrep['font_missing_glyphs'])}")
    if not problems:
        cleanup_mb = prune_backups(d)
    else:
        prune_backups_history_only(d)
    HOST.write_json(P["out_dir"] / "composed.json", {"draft": str(d), "name": name, "when": HOST.now_iso(), "spec": str(spec_path), "problems": problems,
                                                      "plan": facts_plan, "captions": {k: v for k, v in ctx["captions"].items() if k != "geometry"}})
    return {"ok": not problems, "video": P["nn"], "format": P["ftag"] or None, "draft": str(d), "name": name, "export": f"{P['W']}x{P['H']}", "seconds": round(t_end - t0, 1),
            "seconds_by_part": {"plan_and_spec": round(t_spec - t0, 1), "compile": round(t_comp - t_spec, 1), "write_pass": round(t_edit - t_comp, 1),
                                "repair_and_read_back": round(t_end - t_edit, 1)},
            "compose": {"images": len(P["rows"]), "tracks": len(spec["tracks"]), "items": facts_plan["items"], "operations": len(ops) if not fallback else len(fx_ops),
                        "transitions": len(ctx["transitions"]["done"]), "effects": ctx["effects"], "labels": ctx["labels"], "captions": {k: v for k, v in ctx["captions"].items()
                                                                                                                                         if k not in ("geometry", "word_box")},
                        "media_retargeted": facts.get("retargeted"), "moves_keyed": facts.get("keyed"), "fonts_set": facts.get("fonts_set"), "entrances_cloned": facts.get("intro_cloned"),
                        "copies_written": copies, "media_pool_entries_dropped": len(pool_removed), "cover_from_first_still": cover,
                        **({"extras_error_then_composed_bare": extras_error, "older_way": legacy} if fallback else {})},
            "cli_steps": cli_steps, "repair": [{"step": s["step"], "exit": s.get("exit")} for s in rsteps], "cleanup_mb": cleanup_mb, "read_back": chk, "caption_font": cap_font,
            "problems": problems,
            "note": "unverified by any tool here: how CapCut draws the project (the caption look, the box, the entrance, the moves, the joins, the drawings); open it in CapCut once "
                    "and look at the first frame, a move, a join and a caption before exporting"}


def prune_backups_history_only(d: Path) -> None:
    h = Path(d) / ".capcut-cli-history"
    if h.is_dir():
        for f in h.glob("*.snap"):
            try:
                f.unlink()
            except OSError:
                pass


def cmd_capcut_build(a):
    res = build(a)
    HOST.out(res, 0 if res.get("ok") else 1)


def register(sub, host) -> None:
    """Add `capcut-build` to the toolkit's parser."""
    global HOST
    HOST = host
    p = sub.add_parser("capcut-build", help="ONE command for a Static video's whole CapCut project (the user, 2026-11-13: the composition for everything): the stills, the narration and "
                                            "the bed, the effects and drawings, the joins, the moves, the captions and labels in one `capcut compile` and one write pass, the repair "
                                            "and a read-back with a `problems` list")
    p.add_argument("--run", required=True)
    p.add_argument("--video", required=True, help="NN")
    p.add_argument("--format", help="an extra format of the run (its aspect, e.g. 9:16, or its tag): its own timeline, stills and captions")
    p.add_argument("--name", help="the project's folder name (default DD_Mon_YYYY_vNN[-tag])")
    p.add_argument("--store", help="CapCut's drafts folder (default config capcut.drafts_dir)")
    p.add_argument("--template", help="an empty draft to start from (default data/compose-template: this PC's CapCut 9.7 version markers)")
    p.add_argument("--captions", choices=["auto", "word-box", "plain", "none"], default="auto",
                   help="auto: the plan's look (word box when captions.word_box is set); word-box stops with exit 2 for a language it cannot take (then plain)")
    p.add_argument("--spec-only", action="store_true", help="write the compile spec and the plan's facts and stop (nothing is built, CapCut may be open)")
    p.set_defaults(fn=cmd_capcut_build)
