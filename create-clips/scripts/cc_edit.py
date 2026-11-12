"""create-clips editing helpers (used by /create-clips agents). Gather-only: they measure, convert, write what an agent decided; they never judge.

Commands (see README.md for the contract; times are rec times):
  config         show the effective folders and free space, or set config.json keys (e.g. after a new drive is installed)
  state          read/write run state (dotted keys)
  blocks         split the recorded chunks into blocks of N chunks (for scan agents), with the numbers that size them
  sfx-scan       catalogue the sound-effects folder (name, duration, levels) -> RUN/30-assets/sfx.json + sfx.md
  layout-calc    CapCut scale/posX/posY for a 16:9 source on a canvas (fill around a focus, or fit)
  grid-frame     one full-resolution frame with a 10% grid (and an optional region box) to read coordinates from
  censor         blurred/pixelated copy of a span (only that span, optionally only a region): the file replaces the span in the edit
  edl-check      resolve an EDL (cuts, layouts, zooms, sfx, transitions, censor) into pieces, the MCP plan and the finish plan; facts at every cut
  captions       caption cues from the transcript words of the resolved pieces -> captions.json + captions.srt
  capcut-name    a free CapCut project name
  capcut-finish  after the last MCP save: zoom keyframes, transitions, background blur, captions, font, intro, repair
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import re
import shutil
import sys
import time
import uuid
from pathlib import Path

from cc_common import (CC_HOME, cfg_get, chunk_dir, fail, ffprobe_facts, find_tool, fmt_hms, load_chunks, load_state,  # noqa: F401
                       now_iso, out, parse_time, read_json, resolve_run, run_cmd, run_paths, say, split_across_chunks,
                       update_state, write_json, write_text)

EDL_SCHEMA = "cc-edl/1"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def awl_home() -> Path:
    return Path(cfg_get("awl_home", "C:/Users/Bulzart/.claude/analyze-with-loupe"))


def capcut_cli() -> str:
    exe = shutil.which("capcut")
    if exe:
        return exe
    cand = Path(os.environ.get("APPDATA", "")) / "npm" / "capcut.cmd"
    if cand.exists():
        return str(cand)
    fail("capcut-cli not found on PATH (npm i -g capcut-cli)", 1)
    return "capcut"


def capcut_running() -> bool:
    try:
        cp = run_cmd(["tasklist", "/FI", "IMAGENAME eq CapCut.exe", "/NH"], timeout=30)
        return "capcut.exe" in (cp.stdout or "").lower()
    except Exception:  # noqa: BLE001
        return False


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-") or "x"


def last_json(text: str):
    for line in reversed((text or "").strip().splitlines()):
        line = line.strip()
        if line.startswith("{") or line.startswith("["):
            try:
                return json.loads(line)
            except ValueError:
                continue
    return None


def parse_wh(text: str) -> tuple:
    m = re.match(r"^\s*(\d+)\s*[xX*,]\s*(\d+)\s*$", str(text))
    if not m:
        fail(f"cannot read the size {text!r} (use WxH)")
    return int(m.group(1)), int(m.group(2))


def parse_floats(text: str, n: int) -> list:
    try:
        v = [float(x) for x in str(text).replace(";", ",").split(",")]
    except ValueError:
        fail(f"cannot read {text!r}")
    if len(v) != n:
        fail(f"expected {n} numbers in {text!r}")
    return v


# --------------------------------------------------------------------------- config

def cmd_config(a):
    """Show the effective folders and free space, or set config.json keys (dotted; values JSON or text): e.g. after a new drive is installed,
    `config set inbox_dir=D:/twitch-chunks runs_root=D:/stream-clips/runs` (existing runs stay where they are; /create-clips takes any run path)."""
    from cc_common import CONFIG_PATH, free_gb, inbox_dir, runs_root
    cfg = read_json(CONFIG_PATH, {}) or {}
    if a.action == "set":
        pairs = ([a.key] if a.key else []) + list(a.pairs or [])
        if not pairs:
            fail("config set needs key=value pairs")
        notes = []
        for kv in pairs:
            if "=" not in kv:
                fail(f"config set needs key=value, got {kv!r}")
            k, v = kv.split("=", 1)
            try:
                v = json.loads(v)
            except ValueError:
                pass
            cur = cfg
            parts = k.split(".")
            for p in parts[:-1]:
                cur = cur.setdefault(p, {})
            old = cur.get(parts[-1])
            cur[parts[-1]] = v
            if k in ("runs_root", "inbox_dir", "sfx_dir") and isinstance(v, str):
                try:
                    Path(v).mkdir(parents=True, exist_ok=True) if k != "sfx_dir" else None
                    notes.append(f"{k}: {old} -> {v} ({free_gb(v)} GB free there)")
                except OSError as e:
                    notes.append(f"{k}: could not create {v}: {e}")
        write_json(CONFIG_PATH, cfg)
        notes.append("existing runs and chunks are not moved; the browser's download folder (chrome://settings/downloads) decides where new chunks land: set it to the same drive as inbox_dir")
        out({"ok": True, "set": [kv.split("=", 1)[0] for kv in pairs], "notes": notes})
    out({"ok": True, "config": str(CONFIG_PATH), "runs_root": str(runs_root()), "runs_free_gb": free_gb(runs_root()), "inbox_dir": str(inbox_dir()),
         "inbox_free_gb": free_gb(inbox_dir()), "min_free_gb": cfg.get("min_free_gb"), "sfx_dir": cfg.get("sfx_dir"),
         "whisper": {k: (cfg.get("whisper") or {}).get(k) for k in ("model", "device", "compute_type", "language")}})


# --------------------------------------------------------------------------- state / blocks

def cmd_state(a):
    run = resolve_run(a.run)
    if a.action == "get":
        st = load_state(run)
        if a.key:
            cur = st
            for p in a.key.split("."):
                cur = cur.get(p) if isinstance(cur, dict) else None
            out({"ok": True, "key": a.key, "value": cur})
        out({"ok": True, "state": st})
    changes = {}
    pairs = ([a.key] if a.key else []) + list(a.pairs or [])       # `set k=v k2=v2`: the first pair lands in `key`
    for kv in pairs:
        if "=" not in kv:
            fail(f"set needs key=value, got {kv!r}")
        k, v = kv.split("=", 1)
        if v.startswith("@") and Path(v[1:]).is_file():            # k=@file.json : the value is that JSON file (no shell quoting)
            v = read_json(v[1:])
        else:
            try:
                v = json.loads(v)
            except ValueError:
                pass
        changes[k] = v
    st = update_state(run, **changes)
    out({"ok": True, "set": list(changes), "stage": st.get("stage"), "next_skill": st.get("next_skill")})


def cmd_blocks(a):
    run = resolve_run(a.run)
    rows = [r for r in load_chunks(run) if r.get("duration_s")]
    rows.sort(key=lambda r: r["rec_start_s"])
    n = max(1, int(a.chunks))
    blocks = []
    for i in range(0, len(rows), n):
        part = rows[i:i + n]
        words = 0
        for r in part:
            words += int(r.get("words") or 0)
        blocks.append({"block": len(blocks) + 1, "chunks": [r["id"] for r in part],
                       "rec_from": part[0]["rec_start_s"], "rec_to": round(part[-1]["rec_start_s"] + part[-1]["duration_s"], 2),
                       "from_hms": fmt_hms(part[0]["rec_start_s"], False),
                       "to_hms": fmt_hms(part[-1]["rec_start_s"] + part[-1]["duration_s"], False), "words": words,
                       "done": sum(1 for r in part if r.get("status") == "done")})
    out({"ok": True, "run": str(run), "chunks": len(rows), "block_size": n, "blocks": blocks,
         "total_s": round(sum(r["duration_s"] for r in rows), 1)})


def cmd_words(a):
    """The spoken words of a rec span with their start times (for exact cut points): `1234.50 Hello 1234.90 chat, ...`."""
    run = resolve_run(a.run)
    rows = [r for r in load_chunks(run) if r.get("duration_s")]
    t0, t1 = parse_time(a.from_, rows), parse_time(a.to, rows)
    cache, words = {}, []
    for pc in split_across_chunks(rows, t0, t1):
        base = next(r["rec_start_s"] for r in rows if r["id"] == pc["chunk"])
        for s, e, w in load_words(run, pc["chunk"], cache):
            if pc["offset_from"] - 0.05 <= s < pc["offset_to"]:
                words.append((round(base + s, 2), round(base + e, 2), w))
    line = []
    for i, (s, e, w) in enumerate(words):
        line.append(f"{s:.2f} {w}")
        if len(line) == 6 or i == len(words) - 1:
            sys.stdout.write("  ".join(line) + "\n")
            line = []
    out({"ok": True, "rec_from": t0, "rec_to": t1, "words": len(words), "first": words[0][0] if words else None,
         "last_end": words[-1][1] if words else None})


# --------------------------------------------------------------------------- sfx

AUDIO_EXT = {".mp3", ".wav", ".ogg", ".m4a", ".flac", ".aac"}


def _volumedetect(path: Path) -> dict:
    cp = run_cmd([find_tool("ffmpeg"), "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af", "volumedetect", "-f", "null", "-"], timeout=180)
    mean = re.search(r"mean_volume:\s*(-?[\d.]+) dB", cp.stderr or "")
    peak = re.search(r"max_volume:\s*(-?[\d.]+) dB", cp.stderr or "")
    return {"mean_db": float(mean.group(1)) if mean else None, "max_db": float(peak.group(1)) if peak else None}


def cmd_sfx_scan(a):
    folder = Path(a.folder or cfg_get("sfx_dir", ""))
    if not folder.is_dir():
        fail(f"sound-effects folder not found: {folder}")
    cache_p = CC_HOME / "data" / "sfx-cache.json"
    cache = read_json(cache_p, {}) or {}
    files = sorted(p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in AUDIO_EXT)
    rows, seen = [], {}
    for p in files:
        st = p.stat()
        key = str(p)
        c = cache.get(key)
        if not (c and c.get("size") == st.st_size and c.get("mtime") == int(st.st_mtime)):
            facts = ffprobe_facts(p)
            c = {"size": st.st_size, "mtime": int(st.st_mtime), "duration_s": facts.get("duration_s"), **_volumedetect(p)}
            cache[key] = c
        name = slug(p.stem)
        seen[name] = seen.get(name, 0) + 1
        if seen[name] > 1:
            name = f"{name}-{seen[name]}"
        rows.append({"name": name, "file": str(p).replace("\\", "/"), "duration_s": c["duration_s"], "mean_db": c["mean_db"], "max_db": c["max_db"]})
    write_json(cache_p, cache, indent=None)
    res = {"ok": True, "folder": str(folder), "count": len(rows), "sfx": rows}
    if a.run:
        run = resolve_run(a.run)
        p = run_paths(run)["assets"]
        write_json(p / "sfx.json", {"folder": str(folder), "scanned": now_iso(), "sfx": rows})
        lines = ["# sound effects (measured: duration, mean and peak level in dBFS; the name is the file name)", "",
                 "| name | s | mean dB | peak dB |", "|---|---|---|---|"]
        lines += [f"| {r['name']} | {r['duration_s']} | {r['mean_db']} | {r['max_db']} |" for r in rows]
        write_text(p / "sfx.md", "\n".join(lines) + "\n")
        res["written"] = [str(p / "sfx.json"), str(p / "sfx.md")]
        res["rows"] = len(rows)
        res.pop("sfx")
    out(res)


# --------------------------------------------------------------------------- layout

def layout_calc(src: tuple, canvas: tuple, mode: str = "fill", focus=(0.5, 0.5), zoom: float = 1.0, y_offset: float = 0.0) -> dict:
    """CapCut transform for a source of src (w, h) on a canvas (w, h). CapCut draws a clip fitted inside the canvas at scale 1.0
    (contain); posX/posY are in half-canvas units (right +, up +). fill: the crop around `focus` (fractions of the source) fills the
    canvas, `zoom` >= 1 zooms further; the position is clamped so no canvas edge shows an empty border. fit: the whole source inside the
    canvas (scale = zoom), centred, moved up by y_offset (half-canvas units)."""
    sw, sh = src
    cw, ch = canvas
    f1 = min(cw / sw, ch / sh)
    fx, fy = float(focus[0]), float(focus[1])
    if mode == "fit":
        s = max(0.05, zoom)
        return {"mode": "fit", "scale": round(s, 5), "posX": 0.0, "posY": round(y_offset, 5), "clamped": False,
                "display_px": [round(sw * f1 * s), round(sh * f1 * s)]}
    f = (max(cw / sw, ch / sh) if mode == "fill" else f1) * max(1.0, zoom)
    s = f / f1
    dw, dh = sw * f, sh * f
    dx, dy = (0.5 - fx) * dw, (0.5 - fy) * dh            # px the picture moves right / down to bring the focus to the middle
    mx, my = max(0.0, (dw - cw) / 2), max(0.0, (dh - ch) / 2)
    cx, cy = max(-mx, min(mx, dx)), max(-my, min(my, dy))
    return {"mode": mode, "scale": round(s, 5), "posX": round(cx / (cw / 2), 5), "posY": round(-cy / (ch / 2), 5),
            "clamped": abs(cx - dx) > 0.5 or abs(cy - dy) > 0.5, "display_px": [round(dw), round(dh)],
            "visible_x": [round(0.5 - cw / dw / 2 - cx / dw, 4), round(0.5 + cw / dw / 2 - cx / dw, 4)] if dw else None,
            "visible_y": [round(0.5 - ch / dh / 2 + cy / dh, 4), round(0.5 + ch / dh / 2 + cy / dh, 4)] if dh else None}


def cmd_layout_calc(a):
    src, canvas = parse_wh(a.src), parse_wh(a.canvas)
    focus = parse_floats(a.focus, 2) if a.focus else [0.5, 0.5]
    out({"ok": True, **layout_calc(src, canvas, a.mode, focus, a.zoom, a.y_offset),
         "note": "capcut_add_video scale/posX/posY; check the first frame in CapCut: scale 1.0 = the clip fitted inside the canvas"})


# --------------------------------------------------------------------------- frames with a grid

def chunk_probe(run: Path, cid: str) -> dict:
    p = chunk_dir(run, cid) / "probe.json"
    pr = read_json(p, None)
    if not pr or not pr.get("width"):
        pr = ffprobe_facts(chunk_dir(run, cid) / "chunk.mp4")
    return pr


def _extract_frame(chunk_file: Path, offset: float, dest: Path, max_width: int | None = None) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    args = [find_tool("ffmpeg"), "-hide_banner", "-loglevel", "error", "-nostdin", "-y", "-ss", f"{max(0.0, offset):.3f}", "-i", str(chunk_file),
            "-frames:v", "1", "-q:v", "2"]
    if max_width:
        args += ["-vf", f"scale='min({int(max_width)},iw)':-2"]
    cp = run_cmd(args + [str(dest)], timeout=120)
    return cp.returncode == 0 and dest.is_file()


def cmd_grid_frame(a):
    run = resolve_run(a.run)
    rows = load_chunks(run)
    t = parse_time(a.at, rows)
    from cc_common import rec_to_chunk
    cid, off = rec_to_chunk(rows, t)
    if not cid:
        fail(f"rec time {t} is not inside a recorded chunk")
    dest = run_paths(run)["assets"] / "frames" / f"grid-{int(round(t * 100)):08d}.jpg"
    tmp = dest.with_name("raw-" + dest.name)
    if not _extract_frame(chunk_dir(run, cid) / "chunk.mp4", off, tmp):
        fail("could not extract the frame")
    from PIL import Image, ImageDraw, ImageFont
    im = Image.open(tmp).convert("RGB")
    if im.width > 1600:
        im = im.resize((1600, round(im.height * 1600 / im.width)))
    dr = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", max(12, im.width // 90))
    except OSError:
        font = ImageFont.load_default()
    for k in range(1, 10):
        x, y = round(im.width * k / 10), round(im.height * k / 10)
        dr.line([(x, 0), (x, im.height)], fill=(255, 255, 0), width=1)
        dr.line([(0, y), (im.width, y)], fill=(255, 255, 0), width=1)
        dr.text((x + 3, 2), f"{k / 10:.1f}", fill=(255, 255, 0), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
        dr.text((3, y + 2), f"{k / 10:.1f}", fill=(255, 255, 0), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    if a.region:
        rx, ry, rw, rh = parse_floats(a.region, 4)
        dr.rectangle([rx * im.width, ry * im.height, (rx + rw) * im.width, (ry + rh) * im.height], outline=(255, 0, 0), width=4)
    dr.text((6, im.height - 6 - font.size if hasattr(font, "size") else im.height - 20), f"rec {fmt_hms(t)}  {cid} +{off:.2f}  grid every 0.1 of width and height",
            fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    im.save(dest, quality=88)
    tmp.unlink(missing_ok=True)
    out({"ok": True, "file": str(dest).replace("\\", "/"), "rec": t, "chunk": cid, "offset": off, "size": [im.width, im.height],
         "note": "regions are x,y,w,h as fractions of the frame (0..1), measured on the yellow grid"})


# --------------------------------------------------------------------------- censor (blur only the span, optionally only a region)

def _even(v: float) -> int:
    return max(2, int(round(v / 2.0)) * 2)


def censor_filter(width: int, height: int, region, style: str, strength: float) -> str:
    if region:
        rx, ry, rw, rh = region
        cw, ch = _even(rw * width), _even(rh * height)
        cx, cy = min(max(0, int(round(rx * width))), width - cw), min(max(0, int(round(ry * height))), height - ch)
    else:
        cw, ch, cx, cy = width - width % 2, height - height % 2, 0, 0
    if style == "pixel":
        block = max(6, round(min(cw, ch) / 14 * max(0.3, strength)))
        eff = f"scale=max(2\\,iw/{block}):max(2\\,ih/{block}):flags=neighbor,scale={cw}:{ch}:flags=neighbor"
    else:
        sigma = max(6, round(0.05 * min(cw, ch) * max(0.3, strength)))
        eff = f"gblur=sigma={sigma}:steps=3"
    return f"[0:v]split=2[base][r];[r]crop={cw}:{ch}:{cx}:{cy},{eff}[b];[base][b]overlay={cx}:{cy},format=yuv420p[v]"


def make_censor(run: Path, rows: list, rec_from: float, rec_to: float, region, style: str = "blur", strength: float = 1.0,
                force: bool = False) -> list:
    """One blurred copy per chunk piece of the span, same size, fps and audio as the chunk. Returns the pieces with their files."""
    pieces = split_across_chunks(rows, rec_from, rec_to)
    if not pieces:
        fail(f"no recorded content in rec {rec_from}-{rec_to}")
    tag = hashlib.sha1(json.dumps([region, style, strength], sort_keys=True).encode()).hexdigest()[:6]
    made = []
    for pc in pieces:
        pr = chunk_probe(run, pc["chunk"])
        w, h, fps = int(pr["width"]), int(pr["height"]), float(pr.get("fps") or 30)
        dst = run_paths(run)["assets"] / "censor" / f"{pc['chunk']}-{int(round(pc['offset_from'] * 1000)):07d}-{int(round(pc['offset_to'] * 1000)):07d}-{tag}.mp4"
        if force or not dst.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            args = [find_tool("ffmpeg"), "-hide_banner", "-loglevel", "error", "-nostdin", "-y", "-ss", f"{pc['offset_from']:.3f}", "-t",
                    f"{pc['offset_to'] - pc['offset_from']:.3f}", "-i", str(chunk_dir(run, pc["chunk"]) / "chunk.mp4"),
                    "-filter_complex", censor_filter(w, h, region, style, strength), "-map", "[v]", "-map", "0:a:0?",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-r", f"{fps:g}", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", str(dst)]
            cp = run_cmd(args, timeout=1800)
            if cp.returncode != 0 or not dst.is_file():
                fail("ffmpeg could not make the blurred copy: " + (cp.stderr or "")[-400:], 1)
        made.append({**pc, "file": str(dst).replace("\\", "/"), "duration_s": ffprobe_facts(dst).get("duration_s"),
                     "region": region, "style": style, "strength": strength})
    return made


def cmd_censor(a):
    run = resolve_run(a.run)
    rows = load_chunks(run)
    t0, t1 = parse_time(a.from_, rows), parse_time(a.to, rows)
    region = parse_floats(a.region, 4) if a.region else None
    if a.preview_only:
        mid = (t0 + t1) / 2
        from cc_common import rec_to_chunk
        cid, off = rec_to_chunk(rows, mid)
        if not cid:
            fail("the span is not inside a recorded chunk")
        pr = chunk_probe(run, cid)
        dest = run_paths(run)["assets"] / "censor" / f"preview-{int(round(mid * 100)):08d}.jpg"
        dest.parent.mkdir(parents=True, exist_ok=True)
        cp = run_cmd([find_tool("ffmpeg"), "-hide_banner", "-loglevel", "error", "-nostdin", "-y", "-ss", f"{off:.3f}", "-t", "0.2", "-i",
                      str(chunk_dir(run, cid) / "chunk.mp4"), "-filter_complex", censor_filter(int(pr["width"]), int(pr["height"]), region, a.style, a.strength),
                      "-map", "[v]", "-frames:v", "1", "-q:v", "2", str(dest)], timeout=120)
        if cp.returncode != 0:
            fail("preview failed: " + (cp.stderr or "")[-300:], 1)
        out({"ok": True, "preview": str(dest).replace("\\", "/"), "rec": mid, "region": region, "style": a.style})
    made = make_censor(run, rows, t0, t1, region, a.style, a.strength, force=a.force)
    log = run_paths(run)["assets"] / "censor" / "censor.json"
    prev = read_json(log, []) or []
    prev += [{**m, "reason": a.why, "made": now_iso()} for m in made]
    write_json(log, prev)
    out({"ok": True, "pieces": made, "note": "the span is replaced in the edit by these files (edl-check does it for an EDL censor entry)"})


# --------------------------------------------------------------------------- the EDL

DEFAULT_CAPTIONS = {
    "short": {"font_file": "Montserrat-Bold.otf", "size": 15, "color": "#FFFFFF", "stroke_color": "#000000", "stroke_width": 0.1, "y_rel": 0.66,
              "max_words": 3, "max_chars": 18, "case": "upper", "highlight_words": [], "highlight_color": "#FFD700", "highlight_size": 1.15,
              "intro": "fade-in", "intro_s": 0.1, "mask_terms": [], "replace": [], "min_cue_s": 0.25, "gap_break_s": 0.5},
    "long": {"font_file": "Montserrat-Bold.otf", "size": 6, "color": "#FFFFFF", "stroke_color": "#000000", "stroke_width": 0.08, "y_rel": 0.88,
             "max_words": 7, "max_chars": 42, "case": "as-is", "highlight_words": [], "highlight_color": "#FFD700", "highlight_size": 1.1,
             "intro": None, "intro_s": 0.0, "mask_terms": [], "replace": [], "min_cue_s": 0.4, "gap_break_s": 0.8},
}


def load_catalogue() -> dict:
    return read_json(awl_home() / "data" / "capcut-catalogue.json", {}) or {}


def transition_refusal(slug_: str, catalogue: dict) -> str | None:
    rows = {str(x.get("slug")): x for x in catalogue.get("transitions") or []}
    x = rows.get(slug_)
    if x is None:
        return f"{slug_!r} is not in the measured catalogue (AWL data/capcut-catalogue.md): not verified on this PC's CapCut"
    if not x.get("visible_transition"):
        return f"{slug_!r}: CapCut drew nothing for it in the CapCut check"
    if x.get("pro"):
        return f"{slug_!r} is CapCut Pro and this PC has no Pro: the export would be blocked"
    return None


def load_words(run: Path, cid: str, cache: dict) -> list:
    if cid not in cache:
        tr = read_json(chunk_dir(run, cid) / "transcript.json", {}) or {}
        words = []
        for seg in tr.get("segments") or []:
            for w in seg.get("words") or []:
                words.append((float(w["s"]), float(w["e"]), str(w["w"])))
        cache[cid] = words
    return cache[cid]


def cut_facts(run: Path, cid: str, off: float, cache: dict) -> dict:
    """Facts about a cut point at chunk offset `off`: is it inside a spoken word, the distance to the word before and after."""
    words = load_words(run, cid, cache)
    inside, before, after = None, None, None
    for s, e, w in words:
        if s + 0.02 < off < e - 0.02:
            inside = w
        if e <= off + 0.02:
            before = (off - e, w)
        if s >= off - 0.02 and after is None:
            after = (s - off, w)
    return {"inside_word": inside,
            "gap_after_prev_word_s": round(before[0], 2) if before else None, "prev_word": before[1] if before else None,
            "gap_before_next_word_s": round(after[0], 2) if after else None, "next_word": after[1] if after else None}


def zoom_envelope(zooms: list, base_focus) -> list:
    """Breakpoints (t, zoom, focus) of a segment's zoom entries: {"at","to","in","hold","out","focus"}; t in segment seconds."""
    pts = [(0.0, 1.0, base_focus)]
    for z in sorted(zooms or [], key=lambda x: float(x.get("at", 0))):
        at, to = float(z.get("at", 0)), float(z.get("to", 1.15))
        tin, hold, tout = float(z.get("in", 0.2)), float(z.get("hold", 1.0)), float(z.get("out", 0.2))
        foc = z.get("focus") or base_focus
        pts += [(at, 1.0, base_focus), (at + tin, to, foc), (at + tin + hold, to, foc), (at + tin + hold + tout, 1.0, base_focus)]
    pts.sort(key=lambda p: p[0])
    clean = []
    for p in pts:
        if clean and abs(clean[-1][0] - p[0]) < 1e-6:
            clean[-1] = p
        else:
            clean.append(p)
    return clean


def env_at(env: list, t: float):
    if t <= env[0][0]:
        return env[0][1], env[0][2]
    for (t0, z0, f0), (t1, z1, f1) in zip(env, env[1:]):
        if t0 <= t <= t1:
            k = 0 if t1 == t0 else (t - t0) / (t1 - t0)
            return z0 + (z1 - z0) * k, [f0[0] + (f1[0] - f0[0]) * k, f0[1] + (f1[1] - f0[1]) * k]
    return env[-1][1], env[-1][2]


def plan_edl(run: Path, edl: dict, make_files: bool) -> tuple:
    rows = [r for r in load_chunks(run) if r.get("duration_s")]
    if not rows:
        fail("the run has no processed chunks yet")
    kind = edl.get("kind", "short")
    vid = str(edl.get("video") or "").strip()
    if not vid:
        fail("the EDL needs a `video` id (S01, L01 ...)")
    cw, ch = (edl.get("canvas") or {}).get("width"), (edl.get("canvas") or {}).get("height")
    canvas = (int(cw), int(ch)) if cw and ch else tuple(cfg_get("capcut.short_canvas" if kind == "short" else "capcut.long_canvas"))
    fps = int((edl.get("canvas") or {}).get("fps") or cfg_get("capcut.fps", 30))
    base_layout = edl.get("layout") or {"mode": "fill" if kind == "short" else "native"}
    words_cache, warnings, pieces = {}, [], []
    at = 0.0
    seg_info = []
    for si, seg in enumerate(edl.get("segments") or [], 1):
        sid = str(seg.get("id") or f"s{si}")
        t0, t1 = parse_time(seg["rec_from"], rows), parse_time(seg["rec_to"], rows)
        if t1 <= t0:
            warnings.append({"seg": sid, "warning": "rec_to is not after rec_from"})
            continue
        speed = float(seg.get("speed") or 1.0)
        volume = float(seg.get("volume") if seg.get("volume") is not None else 1.0)
        lay = {**base_layout, **(seg.get("layout") or {})}
        # the plain and the censored parts of the span, in order
        cuts = sorted(([parse_time(c["rec_from"], rows), parse_time(c["rec_to"], rows), c] for c in seg.get("censor") or []), key=lambda x: x[0])
        parts, cur = [], t0
        for c0, c1, c in cuts:
            c0, c1 = max(c0, t0), min(c1, t1)
            if c1 <= c0:
                continue
            if c0 > cur + 1e-6:
                parts.append(("plain", cur, c0, None))
            parts.append(("censor", c0, c1, c))
            cur = max(cur, c1)
        if cur < t1 - 1e-6:
            parts.append(("plain", cur, t1, None))
        seg_at0, seg_pieces = at, []
        for ptype, a0, a1, c in parts:
            if ptype == "censor":
                region = c.get("region")
                style = c.get("style", "blur")
                strength = float(c.get("strength", 1.0))
                if make_files:
                    made = make_censor(run, rows, a0, a1, region, style, strength)
                else:
                    made = []
                    tag = hashlib.sha1(json.dumps([region, style, strength], sort_keys=True).encode()).hexdigest()[:6]
                    for pc in split_across_chunks(rows, a0, a1):
                        f = run_paths(run)["assets"] / "censor" / f"{pc['chunk']}-{int(round(pc['offset_from'] * 1000)):07d}-{int(round(pc['offset_to'] * 1000)):07d}-{tag}.mp4"
                        made.append({**pc, "file": str(f).replace("\\", "/"), "exists": f.is_file()})
                for m in made:
                    pieces.append({"seg": sid, "kind": "censor", "chunk": m["chunk"], "file": m["file"], "src_from": 0.0,
                                   "src_to": round(m["offset_to"] - m["offset_from"], 3), "rec_from": m["rec_from"], "rec_to": m["rec_to"],
                                   "chunk_offset_from": m["offset_from"], "chunk_offset_to": m["offset_to"], "exists": m.get("exists", True),
                                   "why": c.get("why")})
                    seg_pieces.append(pieces[-1])
            else:
                for pc in split_across_chunks(rows, a0, a1):
                    pieces.append({"seg": sid, "kind": "plain", "chunk": pc["chunk"], "file": str(chunk_dir(run, pc["chunk"]) / "chunk.mp4").replace("\\", "/"),
                                   "src_from": pc["offset_from"], "src_to": pc["offset_to"], "rec_from": pc["rec_from"], "rec_to": pc["rec_to"],
                                   "chunk_offset_from": pc["offset_from"], "chunk_offset_to": pc["offset_to"], "exists": True})
                    seg_pieces.append(pieces[-1])
        got = sum(p["rec_to"] - p["rec_from"] for p in seg_pieces)
        if got < (t1 - t0) - 0.05:
            warnings.append({"seg": sid, "warning": f"{round((t1 - t0) - got, 2)} s of the span is not recorded (a gap between chunks)"})
        # layout, zoom, timing of the pieces
        zooms = seg.get("zoom") or []
        base_focus = lay.get("focus") or [0.5, 0.5]
        env = zoom_envelope(zooms, base_focus) if zooms else None
        seg_t = 0.0
        for p in seg_pieces:
            pr = chunk_probe(run, p["chunk"])
            src = (int(pr["width"]), int(pr["height"]))
            mode = lay.get("mode", "fill")
            cmode = "fit" if mode in ("fit-blur", "fit") else ("fill" if mode == "fill" else "native")
            base = layout_calc(src, canvas, "fill" if cmode == "fill" else ("fit" if cmode == "fit" else "native"), base_focus,
                               float(lay.get("zoom", 1.0)), float(lay.get("y_offset", 0.0)))
            p["layout"] = {"mode": mode, "scale": base["scale"], "posX": base["posX"], "posY": base["posY"], "clamped": base["clamped"]}
            dur_src = round(p["src_to"] - p["src_from"], 6)
            p.update({"speed": speed, "volume": volume, "dur_src": dur_src, "dur_out": round(dur_src / speed, 6), "at": round(at, 6),
                      "src_size": list(src)})
            if env:
                a_, b_ = seg_t, seg_t + dur_src / speed
                bps = [x for x in env if a_ < x[0] < b_]
                times = [a_] + [x[0] for x in bps] + [b_]
                keys = []
                for tt in times:
                    z, foc = env_at(env, tt)
                    lc = layout_calc(src, canvas, "fill" if cmode == "fill" else ("fit" if cmode == "fit" else "native"), foc,
                                     float(lay.get("zoom", 1.0)) * z, float(lay.get("y_offset", 0.0)))
                    keys.append({"t_us": int(round((tt - a_) * 1e6)), "scale": lc["scale"], "x": lc["posX"], "y": lc["posY"]})
                if any(abs(k["scale"] - keys[0]["scale"]) > 1e-4 or abs(k["x"] - keys[0]["x"]) > 1e-4 or abs(k["y"] - keys[0]["y"]) > 1e-4 for k in keys):
                    p["keys"] = keys
            at += p["dur_out"]
            seg_t += p["dur_out"]
        seg_info.append({"seg": sid, "at": round(seg_at0, 3), "dur_out": round(at - seg_at0, 3), "transition_in": seg.get("transition_in"),
                         "note": seg.get("note")})
    for i, p in enumerate(pieces, 1):
        p["piece"] = i
    # facts at every join of non-contiguous source moments
    joins = []
    for a_, b_ in zip(pieces, pieces[1:]):
        if a_["seg"] == b_["seg"] or abs(a_["rec_to"] - b_["rec_from"]) < 0.02:      # a continuation, not a cut
            continue
        joins.append({"after_piece": a_["piece"], "at_out_s": round(b_["at"], 3),
                      "out": {"rec": a_["rec_to"], **cut_facts(run, a_["chunk"], a_["chunk_offset_to"], words_cache)},
                      "in": {"rec": b_["rec_from"], **cut_facts(run, b_["chunk"], b_["chunk_offset_from"], words_cache)}})
    # a hole between two chunks used by one contiguous run
    for a_, b_ in zip(pieces, pieces[1:]):
        if a_["seg"] != b_["seg"] or a_["chunk"] == b_["chunk"]:
            continue
        gap = next((r.get("gap_before_s") for r in rows if r["id"] == b_["chunk"]), 0) or 0
        if gap and gap > 0.5:
            warnings.append({"seg": a_["seg"], "warning": f"the recording has a gap of {gap} s between {a_['chunk']} and {b_['chunk']} inside this span"})
    # sfx
    sfx_rows = {r["name"]: r for r in (read_json(run_paths(run)["assets"] / "sfx.json", {}) or {}).get("sfx", [])}
    seg_at = {s["seg"]: s for s in seg_info}
    sfx_ops, sfx_busy = [], []
    for k, e in enumerate(edl.get("sfx") or [], 1):
        row = sfx_rows.get(str(e.get("name") or e.get("file") or ""))
        f = e.get("file") if e.get("file") and Path(str(e["file"])).is_file() else (row or {}).get("file")
        if not f:
            warnings.append({"sfx": e.get("name") or e.get("file"), "warning": "not in the sound-effects catalogue (run sfx-scan) and not a file"})
            continue
        if isinstance(e.get("at"), dict):
            s = seg_at.get(str(e["at"].get("seg")))
            if not s:
                warnings.append({"sfx": f, "warning": f"no segment {e['at'].get('seg')}"})
                continue
            t_at = s["at"] + float(e["at"].get("t", 0.0))
        else:
            t_at = float(e.get("at", 0.0))
        dur = float(e.get("dur") or (row or {}).get("duration_s") or ffprobe_facts(f).get("duration_s") or 1.0)
        lane = 0
        while lane < len(sfx_busy) and sfx_busy[lane] > t_at + 1e-6:
            lane += 1
        if lane == len(sfx_busy):
            sfx_busy.append(0.0)
        sfx_busy[lane] = t_at + dur
        sfx_ops.append({"op": "add_audio", "track": f"sfx{lane + 1}", "file": f, "atSec": round(t_at, 3), "durSec": round(dur, 3),
                        "volume": float(e.get("volume", 0.8)), "name": (row or {}).get("name"), "why": e.get("why")})
    # transitions: on the clip before the join
    cat = load_catalogue()
    transitions = []
    first_piece_of = {}
    for p in pieces:
        first_piece_of.setdefault(p["seg"], p)
    for s_prev, s_next in zip(seg_info, seg_info[1:]):
        tr = s_next.get("transition_in")
        if not tr:
            continue
        sl = slug(tr.get("slug", ""))
        why = transition_refusal(sl, cat) if cat else None
        last_prev = [p for p in pieces if p["seg"] == s_prev["seg"]][-1]
        transitions.append({"slug": sl, "dur_s": float(tr.get("dur", 0.3)), "on_clip_at_s": last_prev["at"], "refused": why})
    totals = {"duration_s": round(at, 3), "pieces": len(pieces), "segments": len(seg_info), "sfx": len(sfx_ops),
              "chunks_used": sorted({p["chunk"] for p in pieces if p["kind"] == "plain"}),
              "censored_spans": sum(1 for p in pieces if p["kind"] == "censor")}
    caps = {**DEFAULT_CAPTIONS["short" if kind == "short" else "long"], **(edl.get("captions") or {})}
    resolved = {"schema": "cc-resolved/1", "video": vid, "kind": kind, "canvas": {"width": canvas[0], "height": canvas[1], "fps": fps},
                "segments": seg_info, "pieces": pieces, "joins": joins, "totals": totals, "warnings": warnings, "captions": caps}
    ops = [{"op": "add_video", "track": "main", "file": p["file"], "srcStartSec": round(p["src_from"], 3), "durSec": round(p["dur_src"], 3),
            "scale": p["layout"]["scale"], "posX": p["layout"]["posX"], "posY": p["layout"]["posY"], "speed": p["speed"], "volume": p["volume"],
            "piece": p["piece"], "seg": p["seg"], "atSec_for_reference": p["at"]} for p in pieces] + sfx_ops
    plan = {"schema": "cc-mcp-plan/1", "video": vid, "canvas": resolved["canvas"],
            "how": ["capcut_clone_draft base=_analyze-stack-template newName=<capcut-name> empty=true",
                    "awl.py capcut-prep --draft <draft> --canvas <WxH>   (right after the clone)",
                    "capcut_read_timeline -> the main video track index; capcut_add_track type=audio for each sfx lane (sfx1, sfx2 ...)",
                    "execute `ops` in order: add_video on `main` WITHOUT atSec (it appends right after the last clip: no gaps or overlaps); add_audio with atSec",
                    "capcut_validate, capcut_save (CapCut closed, never force); then cc.py capcut-finish"],
            "ops": ops}
    finish = {"schema": "cc-finish/1", "video": vid, "canvas": resolved["canvas"],
              "zoom": [{"piece": p["piece"], "at_s": p["at"], "dur_s": p["dur_out"], "keys": p["keys"]} for p in pieces if p.get("keys")],
              "transitions": transitions,
              "bg_blur": (edl.get("layout") or {}).get("bg_blur", 3) if any(p["layout"]["mode"] == "fit-blur" for p in pieces) else None,
              "main_pieces": [{"piece": p["piece"], "at_s": p["at"], "dur_s": p["dur_out"], "layout": p["layout"]["mode"]} for p in pieces],
              "captions": caps}
    return resolved, plan, finish


def cmd_edl_check(a):
    run = resolve_run(a.run)
    edl = read_json(a.edl)
    if not edl:
        fail(f"cannot read the EDL {a.edl}")
    resolved, plan, finish = plan_edl(run, edl, a.make_censor)
    d = Path(a.edl).resolve().parent
    write_json(d / "resolved.json", resolved)
    write_json(d / "mcp-plan.json", plan)
    write_json(d / "finish.json", finish)
    missing = [p["file"] for p in resolved["pieces"] if not p.get("exists", True)]
    refused = [t for t in finish["transitions"] if t["refused"]]
    out({"ok": not resolved["warnings"] and not missing and not refused, "video": resolved["video"], "totals": resolved["totals"],
         "warnings": resolved["warnings"], "censor_files_missing": missing, "transitions_refused": refused,
         "joins": [{"after_piece": j["after_piece"], "at_out_s": j["at_out_s"], "cut_out_inside_word": j["out"]["inside_word"],
                    "cut_in_inside_word": j["in"]["inside_word"], "out_gap_after_word_s": j["out"]["gap_after_prev_word_s"],
                    "in_gap_before_word_s": j["in"]["gap_before_next_word_s"]} for j in resolved["joins"]],
         "files": [str(d / "resolved.json"), str(d / "mcp-plan.json"), str(d / "finish.json")],
         "note": "facts only: a cut inside a word, a refused transition or a missing censor file is for the agent to fix in the EDL"})


# --------------------------------------------------------------------------- captions

MASK = re.compile(r"[A-Za-z0-9]")


def _mask_word(w: str, terms: set) -> str:
    core = re.sub(r"[^A-Za-z0-9']", "", w).lower()
    if core in terms and len(core) > 1:
        out_, first = [], True
        for ch in w:
            if MASK.match(ch):
                out_.append(ch if first else "*")
                first = False
            else:
                out_.append(ch)
        return "".join(out_)
    return w


def _srt_time(t: float) -> str:
    t = max(0.0, t)
    ms = int(round(t * 1000))
    h, r = divmod(ms, 3600000)
    m, r = divmod(r, 60000)
    s, ms = divmod(r, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_cues(run: Path, resolved: dict) -> dict:
    caps = resolved["captions"]
    terms = {str(t).lower() for t in caps.get("mask_terms") or []}
    cache = {}
    words = []
    for p in resolved["pieces"]:
        if p["kind"] == "censor":
            cid, off0 = p["chunk"], p["chunk_offset_from"]
        else:
            cid, off0 = p["chunk"], p["src_from"]
        span = p["src_to"] - p["src_from"]
        for s, e, w in load_words(run, cid, cache):
            mid = (s + e) / 2
            if off0 <= mid < off0 + span:
                a, b = max(s, off0), min(e, off0 + span)
                words.append({"w": w, "s": round(p["at"] + (a - off0) / p["speed"], 3), "e": round(p["at"] + (b - off0) / p["speed"], 3)})
    words.sort(key=lambda x: x["s"])
    mx_words, mx_chars, gap = int(caps["max_words"]), int(caps["max_chars"]), float(caps["gap_break_s"])
    cues, cur = [], []

    def flush():
        if cur:
            cues.append(list(cur))
            cur.clear()
    for w in words:
        if cur:
            text_len = sum(len(x["w"]) + 1 for x in cur) + len(w["w"])
            if len(cur) >= mx_words or text_len > mx_chars or w["s"] - cur[-1]["e"] > gap or re.search(r"[.!?]$", cur[-1]["w"]):
                flush()
        cur.append(w)
    flush()
    out_cues = []
    for i, ws in enumerate(cues):
        start = ws[0]["s"]
        end = ws[-1]["e"]
        nxt = cues[i + 1][0]["s"] if i + 1 < len(cues) else None
        end = max(end, start + float(caps["min_cue_s"]))
        if nxt is not None:
            end = min(end, nxt)           # cues never overlap
        text = " ".join(_mask_word(x["w"], terms) for x in ws)
        for pair in caps.get("replace") or []:           # the agents' lexicon: how Whisper misheard a name or a term -> the right spelling
            try:
                text = re.sub(r"(?i)\b" + re.escape(str(pair[0])) + r"\b", str(pair[1]), text)
            except (IndexError, re.error):
                continue
        if caps.get("case") == "upper":
            text = text.upper()
        elif caps.get("case") == "lower":
            text = text.lower()
        out_cues.append({"i": i + 1, "start": round(start, 3), "end": round(end, 3), "text": text, "words": ws})
    return {"cues": out_cues, "n_words": len(words), "params": {k: caps[k] for k in ("max_words", "max_chars", "case", "gap_break_s", "min_cue_s")}}


def cmd_captions(a):
    run = resolve_run(a.run)
    rp = Path(a.resolved)
    resolved = read_json(rp)
    if not resolved:
        fail(f"cannot read {rp} (run edl-check first)")
    res = build_cues(run, resolved)
    d = rp.resolve().parent
    write_json(d / "captions.json", {"video": resolved["video"], **res})
    srt = []
    for c in res["cues"]:
        srt.append(f"{c['i']}\n{_srt_time(c['start'])} --> {_srt_time(c['end'])}\n{c['text']}\n")
    write_text(d / "captions.srt", "\n".join(srt))
    out({"ok": True, "video": resolved["video"], "cues": len(res["cues"]), "words": res["n_words"], "duration_s": resolved["totals"]["duration_s"],
         "silent_stretches_over_4s": _silent(res["cues"], resolved["totals"]["duration_s"]),
         "files": [str(d / "captions.json"), str(d / "captions.srt")],
         "note": "captions are always added (non-negotiable); a stretch without speech has none unless the agent adds a text line"})


def _silent(cues: list, total: float) -> list:
    spans, t = [], 0.0
    for c in cues:
        if c["start"] - t > 4:
            spans.append([round(t, 2), round(c["start"], 2)])
        t = max(t, c["end"])
    if total - t > 4:
        spans.append([round(t, 2), round(total, 2)])
    return spans


# --------------------------------------------------------------------------- CapCut: names, finish

def capcut_store() -> Path:
    explicit = cfg_get("capcut.drafts_dir")
    if explicit:
        return Path(explicit)
    awl_cfg = read_json(awl_home() / "config.json", {}) or {}
    d = (awl_cfg.get("capcut") or {}).get("drafts_dir")
    return Path(os.environ.get("CAPCUT_DRAFTS_DIR") or d or os.path.join(os.environ.get("LOCALAPPDATA", ""), "CapCut", "User Data", "Projects", "com.lveditor.draft"))


def cmd_capcut_name(a):
    store = capcut_store()
    if not store.is_dir():
        fail(f"CapCut drafts store not found: {store}")
    d = dt.date.today()
    base = f"{d.day:02d}_{MONTHS[d.month - 1]}_{d.year}_{slug(a.channel).replace('-', '')}_{a.video}"
    name, k = base, 1
    while (store / name).exists():
        k += 1
        name = f"{base}-{k}"
    out({"ok": True, "name": name, "path": str(store / name), "store": str(store)})


def draft_files(d: Path) -> list:
    return [p for p in (d / "draft_content.json", d / "draft_info.json", d / "template-2.tmp") if p.is_file()]


def make_placeholder(run: Path, need_s: float) -> Path:
    """A tiny black video with silent audio, long enough for any piece: `capcut compile` takes it as the media of every video item (its
    copy into the draft is 350 KB), and the real chunk path replaces it afterwards. The chunk files are never copied into a draft."""
    dst = run_paths(run)["assets"] / "compose" / "placeholder.mp4"
    have = ffprobe_facts(dst).get("duration_s") if dst.is_file() else 0
    if have and have >= need_s:
        return dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    secs = max(200, int(math.ceil(need_s)) + 10)
    cp = run_cmd([find_tool("ffmpeg"), "-hide_banner", "-loglevel", "error", "-nostdin", "-y", "-f", "lavfi", "-i", "color=c=black:s=64x36:r=30",
                  "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", str(secs), "-c:v", "libx264", "-preset", "veryfast", "-crf", "45",
                  "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "16k", str(dst)], timeout=300)
    if cp.returncode != 0 or not dst.is_file():
        fail("could not make the placeholder media: " + (cp.stderr or "")[-300:], 1)
    return dst


def retarget_media(d: Path, pieces: list, probes: dict) -> dict:
    """After `capcut compile`: every video segment of the main track points at its real chunk file, with the real duration and size. The pieces
    are matched to the main track's segments by their start time (compile builds a track's items one after the other)."""
    done = 0
    for p in draft_files(d):
        content = json.loads(p.read_text(encoding="utf-8"))
        main = next((t for t in content.get("tracks", []) if t.get("type") == "video"), None)
        segs = sorted((main or {}).get("segments") or [], key=lambda s: int((s.get("target_timerange") or {}).get("start") or 0))
        mats = {m.get("id"): m for m in content.get("materials", {}).get("videos") or []}
        n = 0
        for piece, seg in zip(pieces, segs):
            m = mats.get(seg.get("material_id"))
            if not m:
                continue
            pr = probes[piece["file"]]
            m["path"] = piece["file"]
            m["material_name"] = Path(piece["file"]).name if piece["kind"] == "censor" else f"{piece['chunk']}.mp4"
            m["duration"] = int(round(float(pr.get("duration_s") or 0) * 1e6))
            m["width"], m["height"] = int(pr.get("width") or m.get("width") or 0), int(pr.get("height") or m.get("height") or 0)
            if pr.get("has_audio") is not None:
                m["has_audio"] = bool(pr["has_audio"])
            n += 1
        if n:
            shutil.copyfile(p, p.with_name(p.name + ".compose.bak"))
            write_text(p, json.dumps(content, ensure_ascii=False))
        if p.name == "draft_content.json":
            done = n
    return {"video_segments_retargeted": done}


def cmd_capcut_compose(a):
    """The whole CapCut project in one command (no per-tool calls): resolved.json -> a `capcut compile` spec (main video track, one audio track
    per sound-effect lane) -> the draft in the CapCut drafts store -> the placeholder media replaced by the real chunk files. Then `capcut-finish`."""
    run = resolve_run(a.run)
    vdir = run_paths(run)["outputs"] / a.video
    resolved, plan = read_json(vdir / "resolved.json"), read_json(vdir / "mcp-plan.json")
    if not resolved or not plan:
        fail(f"no resolved.json / mcp-plan.json in {vdir} (run edl-check)")
    if capcut_running():
        out({"ok": False, "action": "CapCut is running: close it and run this again (nothing was changed)"}, 3)
    t_start = time.time()
    store = Path(a.store) if a.store else capcut_store()
    if not store.is_dir():
        fail(f"CapCut drafts store not found: {store}")
    cli = capcut_cli()
    name = a.name
    if not name:
        d_ = dt.date.today()
        base = f"{d_.day:02d}_{MONTHS[d_.month - 1]}_{d_.year}_{slug(a.channel or load_state(run).get('channel') or 'stream').replace('-', '')}_{a.video}"
        name, k = base, 1
        while (store / name).exists():
            k += 1
            name = f"{base}-{k}"
    elif (store / name).exists():
        fail(f"{store / name} already exists")
    canvas = resolved["canvas"]
    ratio = {(1080, 1920): "9:16", (1920, 1080): "16:9"}.get((canvas["width"], canvas["height"]), "original")
    pieces = resolved["pieces"]
    ph = make_placeholder(run, max(p["dur_src"] for p in pieces) if pieces else 1.0)
    probes = {p["file"]: ffprobe_facts(p["file"]) for p in pieces}
    missing = [f for f, pr in probes.items() if not pr.get("duration_s")]
    if missing:
        fail(f"media not readable: {missing[:3]}")
    items = []
    for p in pieces:
        it = {"ref": f"p{p['piece']}", "path": str(ph).replace("\\", "/"), "start": p["at"], "duration": p["dur_out"], "sourceStart": round(p["src_from"], 6),
              "width": int(probes[p["file"]].get("width") or 0), "height": int(probes[p["file"]].get("height") or 0),
              "scale": p["layout"]["scale"], "x": p["layout"]["posX"], "y": p["layout"]["posY"]}
        if abs(float(p.get("speed") or 1.0) - 1.0) > 1e-6:
            it["speed"] = float(p["speed"])
        if abs(float(p.get("volume") if p.get("volume") is not None else 1.0) - 1.0) > 1e-6:
            it["volume"] = float(p["volume"])
        items.append(it)
    tracks = [{"type": "video", "name": "main", "items": items}]
    lanes = {}
    for o in plan["ops"]:
        if o["op"] == "add_audio":
            lanes.setdefault(o["track"], []).append({"ref": f"{o['track']}-{len(lanes.get(o['track'], [])) + 1}", "path": o["file"].replace("\\", "/"),
                                                      "start": o["atSec"], "duration": o["durSec"], "volume": o["volume"]})
    for lane in sorted(lanes):
        tracks.append({"type": "audio", "name": lane, "items": lanes[lane]})
    spec = {"name": name, "width": canvas["width"], "height": canvas["height"], "fps": canvas["fps"], "ratio": ratio, "tracks": tracks}
    spec_path = vdir / "compose-spec.json"
    write_json(spec_path, spec)
    # No --template by default: capcut-cli then seeds the draft from the store's newest app-authored project (its version markers and settings, none of its
    # content: the way `capcut init` seeded this PC's CapCut 9.7 skeleton). A template FOLDER keeps its own clips (the _analyze-stack-template has two),
    # which is why it is not the default here.
    args = [cli, "compile", str(spec_path), "--out", str(store / name)]
    if a.template:
        args += ["--template", str(a.template)]
    cp = run_cmd(args, timeout=600)
    d = store / name
    if cp.returncode != 0 or not (d / "draft_content.json").is_file():
        fail("capcut compile failed: " + ((cp.stderr or "") + (cp.stdout or ""))[-500:], 1)
    res = retarget_media(d, pieces, probes)
    # the placeholder copy is not referenced any more
    try:
        (d / "assets" / "video" / ph.name).unlink(missing_ok=True)
        if not any((d / "assets" / "video").iterdir()):
            (d / "assets" / "video").rmdir()
    except OSError:
        pass
    left = [str(x) for x in (d / "assets").rglob("*") if x.is_file() and x.suffix.lower() in (".mp4", ".mov") and x.stat().st_size > 5_000_000] if (d / "assets").is_dir() else []
    out({"ok": res["video_segments_retargeted"] == len(pieces) and not left, "draft": str(d), "name": name, "pieces": len(pieces), "sfx_lanes": len(lanes),
         **res, "big_media_copied_into_the_draft": left, "seconds": round(time.time() - t_start, 1),
         "next": f"T capcut-finish --run RUN --draft \"{d}\" --video {a.video}"})


def kf_multi(prop: str, keys: list) -> dict:
    return {"id": str(uuid.uuid4()).upper(), "material_id": "", "property_type": prop,
            "keyframe_list": [{"id": str(uuid.uuid4()).upper(), "curveType": "Line", "time_offset": int(t), "left_control": {"x": 0.0, "y": 0.0},
                               "right_control": {"x": 0.0, "y": 0.0}, "values": [float(v)], "string_value": "", "graphID": ""} for t, v in keys]}


MOVE_PROPS = ("UNIFORM_SCALE", "KFTypeScaleX", "KFTypeScaleY", "KFTypePositionX", "KFTypePositionY")


def write_zoom_keys(d: Path, zooms: list, fps: int) -> dict:
    half = 500000 / fps
    files, unmatched = [], set()
    for p in draft_files(d):
        content = json.loads(p.read_text(encoding="utf-8"))
        main = next((t for t in content.get("tracks", []) if t.get("type") == "video"), None)
        segs = (main or {}).get("segments") or []
        keyed = 0
        for z in zooms:
            want = z["at_s"] * 1e6
            seg = next((s for s in segs if abs(int((s.get("target_timerange") or {}).get("start") or 0) - want) <= half), None)
            if seg is None:
                unmatched.add(z["piece"])
                continue
            keys = z["keys"]
            kfs = [k for k in seg.get("common_keyframes") or [] if k.get("property_type") not in MOVE_PROPS]
            kfs.append(kf_multi("KFTypeScaleX", [(k["t_us"], k["scale"]) for k in keys]))
            if any(abs(k["x"]) > 1e-6 for k in keys):
                kfs.append(kf_multi("KFTypePositionX", [(k["t_us"], k["x"]) for k in keys]))
            if any(abs(k["y"]) > 1e-6 for k in keys):
                kfs.append(kf_multi("KFTypePositionY", [(k["t_us"], k["y"]) for k in keys]))
            seg["common_keyframes"] = kfs
            seg["uniform_scale"] = {"on": True, "value": 1.0}
            clip = seg.setdefault("clip", {})
            clip["scale"] = {"x": float(keys[0]["scale"]), "y": float(keys[0]["scale"])}
            clip["transform"] = {"x": float(keys[0]["x"]), "y": float(keys[0]["y"])}
            keyed += 1
        if keyed:
            shutil.copyfile(p, p.with_name(p.name + ".zoom.bak"))
            write_text(p, json.dumps(content, ensure_ascii=False))
        files.append({"file": p.name, "clips_keyed": keyed, "clips_on_main_track": len(segs)})
    first = files[0]["clips_keyed"] if files else 0
    return {"files": files, "pieces_without_a_clip": sorted(unmatched), "keyed": first}


def main_clips(d: Path) -> list:
    content = json.loads((d / "draft_content.json").read_text(encoding="utf-8"))
    main = next((t for t in content.get("tracks", []) if t.get("type") == "video"), None)
    return (main or {}).get("segments") or []


def sh(args: list, timeout: float = 900):
    cp = run_cmd(args, timeout=timeout)
    return {"exit": cp.returncode, "result": last_json(cp.stdout) or (cp.stdout or "").strip()[-500:], "stderr": (cp.stderr or "").strip()[-300:]}


def cmd_capcut_finish(a):
    run = resolve_run(a.run)
    d = Path(a.draft)
    if not (d / "draft_content.json").is_file():
        fail(f"not a CapCut draft: {d}")
    if (d / ".locked").exists() or capcut_running():
        out({"ok": False, "action": "CapCut is running: close it and run this again (nothing was changed)"}, 3)
    vdir = run_paths(run)["outputs"] / a.video
    finish = read_json(vdir / "finish.json")
    if not finish:
        fail(f"no finish.json in {vdir} (run edl-check)")
    cli, awl = capcut_cli(), [sys.executable, str(awl_home() / "scripts" / "awl.py")]
    steps = []
    fps = int(finish["canvas"].get("fps") or 30)
    if finish.get("zoom"):
        steps.append({"step": "zoom-keys", **write_zoom_keys(d, finish["zoom"], fps)})
    clips = main_clips(d)
    half = 500000 / fps
    done, failed = [], []
    for t in finish.get("transitions") or []:
        if t.get("refused"):
            failed.append({"slug": t["slug"], "error": t["refused"]})
            continue
        seg = next((s for s in clips if abs(int(s["target_timerange"]["start"]) - t["on_clip_at_s"] * 1e6) <= half), None)
        if not seg:
            failed.append({"slug": t["slug"], "error": f"no clip starts at {t['on_clip_at_s']} s"})
            continue
        r = sh([cli, "transition", str(d), str(seg["id"]), t["slug"], "--duration", f"{t['dur_s']:.3f}s"], 120)
        (done if r["exit"] == 0 else failed).append({"slug": t["slug"], "at_s": t["on_clip_at_s"], **({} if r["exit"] == 0 else {"error": r["stderr"] or r["result"]})})
    if finish.get("transitions"):
        steps.append({"step": "transitions", "done": done, "failed": failed})
    if finish.get("bg_blur"):
        res = []
        for mp in finish["main_pieces"]:
            if mp["layout"] != "fit-blur":
                continue
            seg = next((s for s in clips if abs(int(s["target_timerange"]["start"]) - mp["at_s"] * 1e6) <= half), None)
            if seg:
                res.append(sh([cli, "bg-blur", str(d), str(seg["id"]), str(int(finish["bg_blur"]))], 60)["exit"])
        steps.append({"step": "bg-blur", "level": finish["bg_blur"], "exits": res, "note": "unverified on this PC's CapCut: look at the first project"})
    caps = finish["captions"]
    srt = vdir / "captions.srt"
    if not srt.is_file():
        fail(f"captions are non-negotiable and {srt} does not exist: run `captions` first")
    cw, ch = finish["canvas"]["width"], finish["canvas"]["height"]
    args = [cli, "import-srt", str(d), str(srt), "--track-name", "subtitle", "--font-size", str(caps["size"]), "--color", caps["color"],
            "--border-width", str(caps["stroke_width"]), "--border-color", caps["stroke_color"], "--align", "1", "--y", f"{1 - 2 * float(caps['y_rel']):.3f}"]
    hw = [w for w in caps.get("highlight_words") or [] if str(w).strip()]
    if hw:
        hf = vdir / "highlight-words.txt"
        write_text(hf, "\n".join(hw) + "\n")
        args += ["--highlight-words", f"@{hf}", "--keyword-color", caps["highlight_color"], "--keyword-size", str(caps["highlight_size"])]
    steps.append({"step": "captions-import", **sh(args, 900)})
    font = Path(str(caps["font_file"]))
    if not font.is_absolute():
        font = awl_home() / "fonts" / font
    steps.append({"step": "captions-font", **sh([*awl, "capcut-font", "--draft", str(d), "--font-file", str(font), "--track", "subtitle"], 300)})
    if caps.get("intro"):
        steps.append({"step": "captions-intro", **sh([*awl, "capcut-text-anim", "--draft", str(d), "--track", "subtitle", "--intro", caps["intro"],
                                                         "--intro-duration", str(caps.get("intro_s") or 0.1), "--run", str(run)], 300)})
    steps.append({"step": "repair", **sh([*awl, "capcut-repair", "--draft", str(d), "--keep-text"], 1800)})
    bad = [s for s in steps if s.get("exit") not in (None, 0) and s["step"] != "repair"] + ([s for s in steps if s["step"] == "repair" and s.get("exit") not in (0,)])
    out({"ok": not bad and not failed and not any(s.get("pieces_without_a_clip") for s in steps), "draft": str(d), "video": a.video, "steps": steps})


# --------------------------------------------------------------------------- register

def register(sub) -> None:
    p = sub.add_parser("state", help="read or set run state keys (dotted)")
    p.add_argument("--run", required=True)
    p.add_argument("action", choices=["get", "set"])
    p.add_argument("key", nargs="?")
    p.add_argument("pairs", nargs="*", help="set: key=value (value JSON or text)")
    p.set_defaults(func=cmd_state)

    p = sub.add_parser("config", help="show the effective folders and free space, or `set key=value ...` in config.json (e.g. a new drive)")
    p.add_argument("action", nargs="?", choices=["get", "set"], default="get")
    p.add_argument("key", nargs="?")
    p.add_argument("pairs", nargs="*")
    p.set_defaults(func=cmd_config)

    p = sub.add_parser("blocks", help="split the chunks into blocks of N for scan agents")
    p.add_argument("--run", required=True)
    p.add_argument("--chunks", type=int, default=10)
    p.set_defaults(func=cmd_blocks)

    p = sub.add_parser("words", help="the spoken words of a rec span with their start times (exact cut points)")
    p.add_argument("--run", required=True)
    p.add_argument("--from", dest="from_", required=True)
    p.add_argument("--to", required=True)
    p.set_defaults(func=cmd_words)

    p = sub.add_parser("sfx-scan", help="catalogue the sound-effects folder")
    p.add_argument("--folder")
    p.add_argument("--run")
    p.set_defaults(func=cmd_sfx_scan)

    p = sub.add_parser("layout-calc", help="CapCut scale/posX/posY for a source on a canvas")
    p.add_argument("--src", required=True, help="source WxH, e.g. 1280x720")
    p.add_argument("--canvas", required=True, help="canvas WxH, e.g. 1080x1920")
    p.add_argument("--mode", choices=["fill", "fit", "native"], default="fill")
    p.add_argument("--focus", help="fx,fy as fractions of the source (default 0.5,0.5)")
    p.add_argument("--zoom", type=float, default=1.0)
    p.add_argument("--y-offset", type=float, default=0.0, dest="y_offset")
    p.set_defaults(func=cmd_layout_calc)

    p = sub.add_parser("grid-frame", help="a full-resolution frame with a 10%% grid")
    p.add_argument("--run", required=True)
    p.add_argument("--at", required=True)
    p.add_argument("--region", help="x,y,w,h fractions: draws the box")
    p.set_defaults(func=cmd_grid_frame)

    p = sub.add_parser("censor", help="blurred copy of a span (only that span, optionally only a region)")
    p.add_argument("--run", required=True)
    p.add_argument("--from", dest="from_", required=True)
    p.add_argument("--to", required=True)
    p.add_argument("--region", help="x,y,w,h as fractions of the frame; omit for the whole frame")
    p.add_argument("--style", choices=["blur", "pixel"], default="blur")
    p.add_argument("--strength", type=float, default=1.0)
    p.add_argument("--why", default="")
    p.add_argument("--force", action="store_true")
    p.add_argument("--preview-only", action="store_true", help="one blurred frame to look at, nothing else")
    p.set_defaults(func=cmd_censor)

    p = sub.add_parser("edl-check", help="resolve an EDL into pieces, the MCP plan and the finish plan; facts at every cut")
    p.add_argument("--run", required=True)
    p.add_argument("--edl", required=True)
    p.add_argument("--make-censor", action="store_true", help="make the blurred files the EDL's censor entries need")
    p.set_defaults(func=cmd_edl_check)

    p = sub.add_parser("captions", help="caption cues from the transcript words of the resolved pieces")
    p.add_argument("--run", required=True)
    p.add_argument("--resolved", required=True, help="the resolved.json next to the EDL")
    p.set_defaults(func=cmd_captions)

    p = sub.add_parser("capcut-name", help="a free CapCut project name")
    p.add_argument("--channel", required=True)
    p.add_argument("--video", required=True)
    p.set_defaults(func=cmd_capcut_name)

    p = sub.add_parser("capcut-compose", help="the whole CapCut project in one command from resolved.json (capcut compile + the real chunk paths)")
    p.add_argument("--run", required=True)
    p.add_argument("--video", required=True)
    p.add_argument("--name", help="the project name (default: a free DD_Mon_YYYY_<channel>_<video>)")
    p.add_argument("--channel")
    p.add_argument("--store", help="the CapCut drafts folder (default: the real store)")
    p.add_argument("--template", help="a template folder (it keeps its own clips); default: capcut-cli seeds from the store's newest app-authored project")
    p.set_defaults(func=cmd_capcut_compose)

    p = sub.add_parser("capcut-finish", help="after capcut-compose (or the last MCP save): zoom keys, transitions, bg blur, captions, font, intro, repair")
    p.add_argument("--run", required=True)
    p.add_argument("--draft", required=True)
    p.add_argument("--video", required=True)
    p.set_defaults(func=cmd_capcut_finish)
