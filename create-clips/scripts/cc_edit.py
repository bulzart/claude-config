"""create-clips editing helpers (used by /create-clips agents). Gather-only: they measure, convert, write what an agent decided; they never judge.

Commands (see README.md for the contract; times are rec times):
  config         show the effective folders and free space, or set config.json keys (e.g. after a new drive is installed)
  state          read/write run state (dotted keys)
  blocks         split the recorded chunks into blocks of N chunks (for scan agents; --min-blocks M gives a short recording at least M blocks), with the numbers that size them
  sfx-scan       catalogue the sound-effects folder (name, duration, levels) -> RUN/30-assets/sfx.json + sfx.md
  layout-calc    CapCut scale/posX/posY for a 16:9 source on a canvas (fill around a focus, or fit)
  grid-frame     one full-resolution frame with a 10% grid (and an optional region box) to read coordinates from
  censor         blurred/pixelated copy of a span (only that span, optionally only a region): the file replaces the span in the edit
  edl-check      resolve an EDL (cuts, layouts, zooms, sfx, transitions, censor) into pieces, the MCP plan and the finish plan; facts at every cut
  captions       caption cues from the transcript words of the resolved pieces -> captions.json + captions.srt (nothing when the run's captions setting is off); the look is the
                 word-box one by default (the spoken word on a rounded colour box, cc_wordbox.py) or plain
  fonts          the font files the captions can use (family, style, file, where kept)
  capcut-name    a free CapCut project name
  capcut-compose the whole CapCut project in ONE `capcut compile`: the clips on their real chunk files, the sound-effect lanes, the transitions and the word-box caption texts
  capcut-finish  after compose (or the last MCP save): zoom keyframes, background blur, the caption font and entrance, repair, clean-up (what compose did not put in)
  capcut-build   compose + finish + the read-back in one command, one JSON answer: the way every video is built (the user, 2026-11-13: the composition for everything)
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

from cc_common import (CC_HOME, FileLock, cfg_get, chunk_dir, fail, ffprobe_facts, find_tool, fmt_hms, load_chunks, load_state,  # noqa: F401
                       now_iso, out, parse_time, read_json, resolve_run, run_cmd, run_paths, say, split_across_chunks,
                       update_state, write_json, write_text)
import cc_wordbox as wb  # noqa: E402  (the word-box caption look: planning and the draft writer)

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


def captions_on(run) -> bool:
    """The run's captions setting (state.json -> captions): 'on' (the default, also when the key is missing) or 'off' (the user picked no captions at the start)."""
    v = (load_state(run) or {}).get("captions")
    if v is None or v == "":
        return True
    if isinstance(v, bool):                           # `state set captions=false` is read as JSON false
        return v
    return str(v).strip().lower() not in ("off", "no", "false", "0", "none")


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
    if a.key:                                                       # `config get agents.scan_model`: one value of config.json, dotted
        cur = cfg
        for part in a.key.split("."):
            cur = cur.get(part) if isinstance(cur, dict) else None
        out({"ok": True, "key": a.key, "value": cur})
    out({"ok": True, "config": str(CONFIG_PATH), "runs_root": str(runs_root()), "runs_free_gb": free_gb(runs_root()), "inbox_dir": str(inbox_dir()),
         "inbox_free_gb": free_gb(inbox_dir()), "min_free_gb": cfg.get("min_free_gb"), "sfx_dir": cfg.get("sfx_dir"),
         "whisper": {k: (cfg.get("whisper") or {}).get(k) for k in ("model", "device", "compute_type", "language")}, "agents": cfg.get("agents")})


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
    mb = max(1, int(getattr(a, "min_blocks", 1) or 1))
    if mb > 1 and rows:                      # a short recording still gets at least `mb` blocks, so that scan agents can work side by side
        n = max(1, min(n, math.ceil(len(rows) / mb)))
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
    out({"ok": True, "run": str(run), "chunks": len(rows), "block_size": n, "min_blocks": mb, "blocks": blocks,
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

_PROBES: dict = {}


def chunk_probe(run: Path, cid: str) -> dict:
    """The ffprobe facts of a chunk: its probe.json, else one ffprobe (remembered for the rest of this command: an hour-long EDL asks for it once per piece)."""
    key = (str(run), cid)
    if key in _PROBES:
        return _PROBES[key]
    pr = read_json(chunk_dir(run, cid) / "probe.json", None)
    if not pr or not pr.get("width"):
        pr = ffprobe_facts(chunk_dir(run, cid) / "chunk.mp4")
    _PROBES[key] = pr
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

# The default look (the user, 2026-11-13): COPIED FROM LOUPE VIDEO 04 (run 20261106-063422-static-klein): Luckiest Guy (the one font, always: the box numbers were tuned for it),
# upper case, white words with a thick black outline (0.18) and a shadow, the word being spoken on a rounded colour box that moves from word to word (`style: "word-box"`,
# the box's numbers in `box`, its colour `highlight_color`, which stays free: the agent picks it to match the video). `style: "plain"` is the old one-text-per-caption look
# (keyword colouring with `highlight_words`) in the same font and outline; it is also what a language the word box cannot take (written without spaces, or right to left)
# falls back to. `size: "auto"` puts the em at `size_em_pct` percent of the picture's smaller side (cc_wordbox.auto_size): small/normal for phones and tablets.
_HOUSE = {"style": "word-box", "font_file": wb.HOUSE_FONT_FILE, "size": "auto", "size_em_pct": wb.DEFAULT_EM_PCT, "color": "#FFFFFF", "stroke_color": "#000000",
          "stroke_width": wb.HOUSE_STROKE_WIDTH, "shadow": True, "case": "upper", "highlight_words": [], "highlight_color": wb.DEFAULT_COLOR, "box": dict(wb.DEFAULT_BOX),
          "word_box_max_words": 3000, "mask_terms": [], "replace": []}
DEFAULT_CAPTIONS = {
    "short": {**_HOUSE, "y_rel": 0.66, "max_words": 3, "max_chars": 18, "highlight_size": 1.15, "intro": "fade-in", "intro_s": 0.1, "min_cue_s": 0.25, "gap_break_s": 0.5},
    "long": {**_HOUSE, "y_rel": 0.88, "max_words": 5, "max_chars": 32, "highlight_size": 1.1, "intro": None, "intro_s": 0.0, "min_cue_s": 0.4, "gap_break_s": 0.8},
}
PLAIN_CAPTIONS = {"short": {"highlight_color": "#FFD700"},
                  "long": {"max_words": 7, "max_chars": 42, "highlight_color": "#FFD700"}}


def whisper_language(run) -> str | None:
    st = load_state(run) or {}
    lang = ((st.get("settings") or {}).get("whisper") or {}).get("language")
    return lang or (cfg_get("whisper", {}) or {}).get("language")


def merge_captions(run, kind: str, edl_caps: dict | None) -> dict:
    """The captions block of a video: the default look for its kind (the Loupe video 04 look, the font always Luckiest Guy), the EDL's own keys over it, the user's colour pick at the
    start (state.json captions_color) filling what the EDL leaves open, `style` settled (a language the word box cannot take falls back to plain) and `enabled` = the run's setting.
    An EDL that names another font (`font_family`, `font_file`) is kept, and `captions` reports it as a fact (`house_font` false): the one reason is a character the house font cannot draw."""
    k = "short" if kind == "short" else "long"
    edl_caps = dict(edl_caps or {})
    style = str(edl_caps.get("style") or "word-box").strip().lower()
    if style not in ("word-box", "plain"):
        style = "word-box"
    reason = None
    if style == "word-box":
        ok, why = wb.language_support(whisper_language(run))
        if not ok:
            style, reason = "plain", f"the captions' language is {why}: the word box needs spaces between words and left to right, so the plain caption look is used"
    base = {**DEFAULT_CAPTIONS[k], **(PLAIN_CAPTIONS[k] if style == "plain" else {})}
    caps = {**base, **edl_caps, "style": style}
    caps["box"] = {**wb.DEFAULT_BOX, **(edl_caps.get("box") or {})}
    st = load_state(run) or {}
    if st.get("captions_color") and "highlight_color" not in edl_caps:
        caps["highlight_color"] = str(st["captions_color"])
    if reason:
        caps["style_reason"] = reason
    caps["enabled"] = captions_on(run)
    return caps


def awl_cmd() -> list:
    return [sys.executable, str(awl_home() / "scripts" / "awl.py")]


def font_rows(family: str | None = None) -> list:
    """The font files on this PC the edit can use (the Loupe toolkit's list: its fonts folder first, then CapCut's own, then Windows'), optionally only the
    families containing `family`: facts, never a judgement of which fits."""
    r = sh([*awl_cmd(), "capcut-font", "--list", *(["--family", family] if family else [])], 120)
    res = r.get("result")
    return (res or {}).get("fonts", []) if isinstance(res, dict) else []


_STYLE_PREFERENCE = ("bold", "extrabold", "extra bold", "black", "semibold", "medium", "regular")
FONT_CACHE = CC_HOME / "data" / "font-cache.json"      # derived data (git-ignored like sfx-cache.json): a family lookup costs a Python start and a scan of the PC's fonts, about 3 s


def _font_cache_get(key: str):
    e = (read_json(FONT_CACHE, {}) or {}).get(key)
    try:
        if e and Path(str(e["file"])).is_file() and Path(str(e["file"])).stat().st_size == int(e["size"]):
            return str(e["file"])
    except (KeyError, OSError, ValueError, TypeError):
        pass
    return None


def _font_cache_put(key: str, file: str) -> None:
    try:
        j = read_json(FONT_CACHE, {}) or {}
        j[key] = {"file": file, "size": Path(file).stat().st_size, "when": now_iso()}
        write_json(FONT_CACHE, j)
    except OSError:
        pass                                          # a cache that cannot be written only costs the next lookup its 3 s


def caption_font(caps: dict) -> str:
    """The caption font's file: `font_family` (looked up on this PC, the style in `font_style` or else Bold first; the answer is kept in data/font-cache.json while the file
    is still there, so compose, finish and the next video do not scan the fonts again) or `font_file` (a name in the Loupe fonts folder or an absolute path)."""
    fam = str(caps.get("font_family") or "").strip()
    if fam:
        key = f"{fam.lower()}|{str(caps.get('font_style') or '').strip().lower()}"
        hit = _font_cache_get(key)
        if hit:
            return hit
        rows = font_rows(fam)
        exact = [r for r in rows if str(r["family"]).lower() == fam.lower()] or rows
        if not exact:
            fail(f"no font family matching {fam!r} on this PC: `T fonts --family <part of the name>` lists them", 2, families=sorted({r["family"] for r in font_rows()})[:60])
        want = str(caps.get("font_style") or "").strip().lower()

        def rank(r):
            sty = str(r.get("style") or "").lower()
            if want and sty == want:
                return -1
            return next((i for i, p in enumerate(_STYLE_PREFERENCE) if sty == p), len(_STYLE_PREFERENCE))
        chosen = str(sorted(exact, key=rank)[0]["file"])
        _font_cache_put(key, chosen)
        return chosen
    p = Path(str(caps["font_file"]))
    if not p.is_absolute():
        p = awl_home() / "fonts" / p
    if not p.is_file():
        fail(f"captions.font_file not found: {p} (a name from the Loupe fonts folder, an absolute path, or captions.font_family: `T fonts` lists the fonts)", 2)
    return str(p).replace("\\", "/")


def caption_size(caps: dict, canvas: dict, font_file: str) -> tuple:
    """(the CapCut size to use, facts about it): `size: "auto"` puts the font's em at `size_em_pct` percent of the picture's smaller side, a number is taken as given."""
    W, H = int(canvas["width"]), int(canvas["height"])
    raw = caps.get("size", "auto")
    size = wb.auto_size(font_file, W, H, float(caps.get("size_em_pct") or wb.DEFAULT_EM_PCT)) if str(raw).strip().lower() == "auto" else float(raw)
    return size, wb.size_facts(font_file, size, W, H)


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
    caps = merge_captions(run, kind, edl.get("captions"))         # the look, the user's picks at the start and the run's captions setting (finish.json and resolved.json carry them)
    if caps["style"] == "word-box" and caps["enabled"]:
        n_spoken = len(_resolved_words(run, {"pieces": pieces}))
        if n_spoken > int(caps.get("word_box_max_words") or 3000):    # one CapCut text per word and state: an hour of speech would be tens of thousands of texts
            caps = merge_captions(run, kind, {**(edl.get("captions") or {}), "style": "plain"})
            caps["style_reason"] = (f"{n_spoken} spoken words would need about {int(n_spoken * 2.5)} CapCut texts for the word box, over captions.word_box_max_words "
                                    f"({int((edl.get('captions') or {}).get('word_box_max_words') or 3000)}): the plain look is used (raise the limit in the EDL's captions block to force the word box)")
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


def _resolved_words(run: Path, resolved: dict) -> list:
    """The spoken words of the resolved pieces on the OUTPUT timeline: [{"w", "s", "e"}] sorted by start."""
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
    return words


def build_cues_word_box(run: Path, resolved: dict, caps: dict, font_file: str) -> dict:
    """The captions for the word-box look: the words masked and spelled (the lexicon works on word sequences here, so a phrase Whisper split across a caption's
    edge still matches and keeps its time), grouped into captions by the same rules as the plain look, a caption whose line would be wider than the frame
    split in two, then the plan of CapCut texts (one per word and state) as facts."""
    words = _resolved_words(run, resolved)
    tokens = wb.tokens_from_words(words, caps, _mask_word)
    groups = wb.group_words(tokens, caps)
    cues = [{"start": s, "end": e, "words": ws} for ws, (s, e) in zip(groups, wb.cue_times(groups, caps["min_cue_s"]))]
    canvas = resolved["canvas"]
    W, fps = int(canvas["width"]), int(canvas.get("fps") or 30)
    box = wb.box_params(caps)
    probe = wb.Probe(font_file, float(caps["size"]), W, float(box["gap_em"]))
    limit = wb.FIT_FRACTION * W - 2 * wb.EDGE_EM * probe.em - 0.04 * W
    split = wb.fit_cues(cues, probe, limit, float(caps["min_cue_s"]))
    out_cues = [{"i": i + 1, "start": round(c["start"], 3), "end": round(c["end"], 3), "text": " ".join(w["w"] for w in c["words"]), "words": c["words"]}
                for i, c in enumerate(split)]
    rows = wb.plan_rows(out_cues, fps)
    groups_t, geo = wb.plan_texts(rows, probe, W)
    return {"cues": out_cues, "n_words": len(words), "split_for_width": len(split) - len(cues),
            "params": {k: caps[k] for k in ("max_words", "max_chars", "case", "gap_break_s", "min_cue_s")},
            "word_box": {"font_file": font_file, "size": float(caps["size"]), "box": box, **wb.plan_summary(groups_t), "geometry": geo}}


def build_cues(run: Path, resolved: dict) -> dict:
    caps = resolved["captions"]
    terms = {str(t).lower() for t in caps.get("mask_terms") or []}
    words = _resolved_words(run, resolved)
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
    if not captions_on(run):
        out({"ok": True, "video": resolved["video"], "skipped": True, "cues": 0, "silent_stretches_over_4s": [], "files": [],
             "note": "captions are OFF for this run (state.json captions=off, picked at the start): nothing was written and capcut-finish adds no caption track"})
    caps = resolved["captions"]
    font_file = caption_font(caps)
    size, size_info = caption_size(caps, resolved["canvas"], font_file)
    if caps.get("style") == "word-box":
        res = build_cues_word_box(run, resolved, {**caps, "size": size}, font_file)
    else:
        res = build_cues(run, resolved)
    d = rp.resolve().parent
    frep = wb.font_report(font_file, " ".join(c["text"] for c in res["cues"]))      # the characters of the captions the font has no glyph for (a fact, known before the build)
    house = Path(font_file).name == wb.HOUSE_FONT_FILE
    write_json(d / "captions.json", {"video": resolved["video"], "style": caps.get("style"), "font_file": font_file, "house_font": house, "size": size_info, **frep, **res})
    srt = []
    for c in res["cues"]:
        srt.append(f"{c['i']}\n{_srt_time(c['start'])} --> {_srt_time(c['end'])}\n{c['text']}\n")
    write_text(d / "captions.srt", "\n".join(srt))
    out({"ok": True, "video": resolved["video"], "style": caps.get("style"), "style_reason": caps.get("style_reason"), "cues": len(res["cues"]), "words": res["n_words"],
         "duration_s": resolved["totals"]["duration_s"], "silent_stretches_over_4s": _silent(res["cues"], resolved["totals"]["duration_s"]),
         "font_file": font_file, "house_font": house, **frep, "size": size_info, "highlight_color": caps.get("highlight_color") if caps.get("style") == "word-box" else None,
         **({"word_box": res["word_box"], "split_for_width": res["split_for_width"]} if caps.get("style") == "word-box" else {}),
         "files": [str(d / "captions.json"), str(d / "captions.srt")],
         "note": "captions are ON for this run (the default): every second of speech is captioned; a stretch without speech has none unless the agent adds a text line. "
                 "The look is the Loupe video 04 look: `style` word-box (the spoken word on a rounded colour box, one CapCut text per word) in the house font, Luckiest Guy, ALWAYS "
                 "(the box numbers are tuned for it; `house_font` says whether this video uses it); the highlight colour is the EDL's own pick; the size is auto = the em at "
                 "size_em_pct of the picture's smaller side. `font_missing_glyphs` lists the characters of the captions the font cannot draw: a font other than the house font "
                 "is for that reason only"})


def cmd_fonts(a):
    rows = font_rows(a.family)
    out({"ok": True, "count": len(rows), "family_filter": a.family, "fonts": rows, "house_font": {"family": wb.HOUSE_FONT_FAMILY, "file": wb.HOUSE_FONT_FILE},
         "note": "facts only. The captions use the house font, Luckiest Guy, always (the Loupe video 04 look; the box numbers are tuned for it). This list is for the one exception: "
                 "`captions` says `font_missing_glyphs` for a character the house font cannot draw (Slavic and Turkish letters, Cyrillic, Greek); then name another family in "
                 "the EDL's captions.font_family (captions.font_style picks Bold, Black ... when a family has several) or a file in captions.font_file; the library's own copy "
                 "is the one a project keeps (kept_by). Its line height differs from Luckiest Guy's, so look at the box in the first frame"})


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


def clean_media_pool(d: Path) -> list:
    """`capcut compile` lists the placeholder in the draft's media pool (draft_meta_info.json -> draft_materials), and a template may list media of its own. The files
    are not there (the placeholder copy is deleted after the clips are pointed at the real chunks), and CapCut shows 'Media lost / Link media' for every pool entry
    whose file is missing when the project opens. Drop each entry whose file does not exist; the real media are added to the pool by capcut-finish (repair)."""
    p = d / "draft_meta_info.json"
    j = read_json(p)
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
        write_text(p, json.dumps(j, ensure_ascii=False))
    return removed


def make_cover(d: Path, piece: dict, canvas: dict) -> bool:
    """The project's thumbnail on CapCut's home screen: a frame of the first clip on the canvas's shape. Without it the template's own cover (a blue 'Template text'
    tile) would stand for every project until it is opened and saved in CapCut."""
    w, h = int(canvas["width"]), int(canvas["height"])
    sc = 540.0 / max(w, h)
    cw, ch = max(2, int(w * sc) // 2 * 2), max(2, int(h * sc) // 2 * 2)
    t = float(piece["src_from"]) + min(1.0, float(piece["dur_src"]) / 2)
    cp = run_cmd([find_tool("ffmpeg"), "-hide_banner", "-loglevel", "error", "-nostdin", "-y", "-ss", f"{t:.3f}", "-i", piece["file"], "-frames:v", "1",
                  "-vf", f"scale={cw}:{ch}:force_original_aspect_ratio=decrease,pad={cw}:{ch}:(ow-iw)/2:(oh-ih)/2:black", "-q:v", "3", str(d / "draft_cover.jpg")], timeout=120)
    return cp.returncode == 0 and (d / "draft_cover.jpg").is_file()


def capcut_store_lock_path() -> Path:
    """The machine-wide lock of CapCut's shared project index (root_meta_info.json): the Loupe toolkit's repair takes this very file (same O_EXCL protocol) around its `register`
    step, so a build of this command and a repair of another run never write the index together."""
    acfg = read_json(awl_home() / "config.json", {}) or {}
    return Path(acfg.get("runs_root") or (awl_home() / "runs")) / ".capcut-store.lock"


def locked_compile(args: list):
    """`capcut compile` creates the draft AND adds it to the store's shared root_meta_info.json (a read, a change and a write): production agents build their videos side by side,
    so the call holds the store lock; it lasts a few seconds. The lock is only the compile call: the rest of the build touches this draft's own folder."""
    try:
        with FileLock(capcut_store_lock_path(), timeout=900, stale_s=300):
            return run_cmd(args, timeout=600)
    except TimeoutError as e:
        fail(f"{e}: another build is writing CapCut's project index; run this again", 4)


def probe_pool(files: list) -> dict:
    """ffprobe facts of every distinct file, several at a time (a long video draws on dozens of chunks and each probe is a process of its own)."""
    from concurrent.futures import ThreadPoolExecutor
    files = sorted(set(files))
    if not files:
        return {}
    with ThreadPoolExecutor(max_workers=min(8, len(files))) as ex:
        return dict(zip(files, ex.map(ffprobe_facts, files)))


def word_box_parts(vdir: Path, caps: dict, canvas: dict, total_s: float):
    """The word-box captions of a video as the plan and the compile parts, from its captions.json and the resolved look; None when the file holds no word-box cues.
    Compose and finish both call it, so what finish expects is what compose wrote (the fingerprint of the parts tells)."""
    cj = read_json(vdir / "captions.json") or {}
    if cj.get("style") != "word-box" or not cj.get("cues"):
        return None
    font_path = caption_font(caps)
    size, _info = caption_size(caps, canvas, font_path)
    c2 = {**caps, "size": size}
    plan = wb.plan_word_box(c2, cj["cues"], canvas, font_path)
    return {"font_path": font_path, "size": size, "caps": c2, "plan": plan, "parts": None if plan["error"] else wb.compose_parts(plan, c2, total_s)}


def parts_fingerprint(parts: dict) -> str:
    return hashlib.sha1(json.dumps([parts["tracks"], parts["operations"]], sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def compose_extras(run: Path, vdir: Path, finish: dict, pieces: list, canvas: dict) -> dict:
    """What goes into the same `capcut compile` call as the clips and the sound-effect lanes, so the whole project is ONE composition (the user, 2026-11-13: use the
    composition for everything, for faster delivery): the transitions (an operation on the clip before each join: the very function capcut-cli's `transition` command
    calls) and, when the captions are on and in the word-box look, the caption texts with their styles (wb.compose_parts: the functions import-srt calls, without a process
    and a draft write per track). Compile has no operation for the caption font, the entrance, the zoom keys, the background blur or the repair: capcut-finish writes those."""
    res = {"tracks": [], "operations": [], "transitions": None, "captions": None}
    half = 0.5 / max(1, int(canvas.get("fps") or 30))
    trs = finish.get("transitions") or []
    if trs:
        done, failed, used = [], [], set()
        for t in trs:
            if t.get("refused"):
                failed.append({"slug": t["slug"], "error": t["refused"]})
                continue
            p = next((q for q in pieces if abs(float(q["at"]) - float(t["on_clip_at_s"])) <= half), None)
            if p is None:
                failed.append({"slug": t["slug"], "error": f"no clip starts at {t['on_clip_at_s']} s"})
                continue
            if p["piece"] in used:
                failed.append({"slug": t["slug"], "error": f"clip {p['piece']} already has a transition"})
                continue
            used.add(p["piece"])
            res["operations"].append({"op": "transition", "target": f"p{p['piece']}", "slug": t["slug"], "duration": round(float(t["dur_s"]), 3)})
            done.append({"slug": t["slug"], "at_s": t["on_clip_at_s"]})
        res["transitions"] = {"done": done, "failed": failed}
    caps = finish.get("captions") or {}
    if captions_on(run) and caps.get("style") == "word-box" and pieces:
        total_s = max(float(p["at"]) + float(p["dur_out"]) for p in pieces)
        w = word_box_parts(vdir, caps, canvas, total_s)
        if w and w["parts"]:
            parts = w["parts"]
            res["tracks"] += parts["tracks"]
            res["operations"] += parts["operations"]
            res["captions"] = {"composed": True, "style": "word-box", "tracks": len(parts["tracks"]), "texts": parts["texts"], "clipped_at_end": parts["clipped_at_end"],
                               "dropped": parts["dropped"], "fingerprint": parts_fingerprint(parts), "plan_tracks": parts["plan_tracks"],
                               "track_list": [{"track": t["track"], "boxed": t["boxed"], "entrance": t["entrance"], "texts": len(t["entries"])} for t in parts["plan_tracks"]]}
        elif w:
            res["captions"] = {"composed": False, "error": w["plan"]["error"]}
    return res


def compose_run(a) -> dict:
    """The whole CapCut project in one command (no per-tool calls): resolved.json -> a `capcut compile` spec (the main video track, one audio track per sound-effect lane,
    the transitions and, in the word-box look, the caption texts with their styles) -> the draft in the CapCut drafts store -> the placeholder media replaced by the real
    chunk files. `--bare` leaves the transitions and the captions to `capcut-finish`. Then `capcut-finish` (or `capcut-build`, which does both and the read-back)."""
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
    probes = probe_pool([p["file"] for p in pieces])    # one ffprobe per distinct file, side by side (a long video has hundreds of pieces over a few dozen chunks)
    missing = [f for f, pr in probes.items() if not pr.get("duration_s")]
    if missing:
        fail(f"media not readable: {missing[:3]}")
    finish = read_json(vdir / "finish.json") or {}
    extra = {"tracks": [], "operations": [], "transitions": None, "captions": None}
    if not getattr(a, "bare", False) and finish:
        extra = compose_extras(run, vdir, finish, pieces, canvas)
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
    spec = {"name": name, "width": canvas["width"], "height": canvas["height"], "fps": canvas["fps"], "ratio": ratio, "tracks": tracks + extra["tracks"]}
    if extra["operations"]:
        spec["operations"] = extra["operations"]
    spec_path = vdir / "compose-spec.json"
    write_json(spec_path, spec, indent=None)
    # The default template is data/compose-template: an EMPTY draft that carries this PC's CapCut 9.7 version markers (a copy of the _analyze-stack-template
    # with its four segments removed and its media files dropped; 60 KB). capcut-cli's own `auto` falls back to its bundled CapCut 6.5.0 (mac) skeleton when
    # the store has no app-authored project, which is the case here, and a template folder that still holds clips would keep them and push the main track aside.
    own = CC_HOME / "data" / "compose-template"
    tmpl = a.template or (str(own) if (own / "draft_content.json").is_file() else None)
    args = [cli, "compile", str(spec_path), "--out", str(store / name)]
    if tmpl:
        args += ["--template", str(tmpl)]
    t_started_compile = time.time()
    cp = locked_compile(args)
    d = store / name
    extras_error = None
    if (cp.returncode != 0 or not (d / "draft_content.json").is_file()) and (extra["tracks"] or extra["operations"]):
        # the transitions or the captions were refused by compile (an unknown transition name, a text it cannot take): the half-made folder is this very command's own (the name
        # was free a moment ago), removed by its exact path, and the clips and sound effects are composed alone; capcut-finish then writes the rest the older way
        extras_error = ((cp.stderr or "") + (cp.stdout or ""))[-400:]
        if d.is_dir():
            shutil.rmtree(d, ignore_errors=True)
        extra = {"tracks": [], "operations": [], "transitions": None, "captions": None}
        spec.pop("operations", None)
        spec["tracks"] = tracks
        write_json(spec_path, spec, indent=None)
        cp = locked_compile(args)
    if cp.returncode != 0 or not (d / "draft_content.json").is_file():
        fail("capcut compile failed: " + ((cp.stderr or "") + (cp.stdout or ""))[-500:], 1)
    t_compiled = time.time()
    res = retarget_media(d, pieces, probes)
    t_retargeted = time.time()
    # the placeholder copy is not referenced any more
    try:
        (d / "assets" / "video" / ph.name).unlink(missing_ok=True)
        if not any((d / "assets" / "video").iterdir()):
            (d / "assets" / "video").rmdir()
    except OSError:
        pass
    left = [str(x) for x in (d / "assets").rglob("*") if x.is_file() and x.suffix.lower() in (".mp4", ".mov") and x.stat().st_size > 5_000_000] if (d / "assets").is_dir() else []
    pool_removed = clean_media_pool(d)
    cover = bool(pieces) and make_cover(d, pieces[0], canvas)
    cap = extra["captions"]
    cap_check = None
    if cap and cap.get("composed"):                  # the texts compile wrote against the plan, and the one box field compile cannot set
        cap_check = wb.check_composed(d, cap["plan_tracks"], True, draft_files)
    composed = {"draft": str(d), "name": name, "when": now_iso(), "bare": bool(getattr(a, "bare", False)), "transitions": extra["transitions"],
                "captions": ({k: v for k, v in cap.items() if k != "plan_tracks"} | {"check": cap_check}) if cap else None, "extras_error": extras_error}
    write_json(vdir / "composed.json", composed)     # what is already in this draft: capcut-finish writes only the rest
    in_comp = {"transitions": len((extra["transitions"] or {}).get("done") or []), "transitions_refused": len((extra["transitions"] or {}).get("failed") or []),
               "caption_texts": (cap or {}).get("texts") if cap and cap.get("composed") else 0, "caption_tracks": (cap or {}).get("tracks") if cap and cap.get("composed") else 0,
               "caption_check_ok": None if cap_check is None else cap_check["ok"]}
    return {"ok": res["video_segments_retargeted"] == len(pieces) and not left and (cap_check is None or cap_check["ok"]), "draft": str(d), "name": name, "pieces": len(pieces),
            "sfx_lanes": len(lanes), "composed_in_the_same_call": in_comp, **({"extras_error_then_composed_bare": extras_error} if extras_error else {}),
            "template": str(tmpl) if tmpl else "auto (capcut-cli's own choice)", **res, "big_media_copied_into_the_draft": left, "media_pool_entries_dropped": pool_removed,
            "cover_from_first_clip": cover, "seconds": round(time.time() - t_start, 1),
            "seconds_by_stage": {"before_compile": round(t_started_compile - t_start, 1), "compile": round(t_compiled - t_started_compile, 1), "retarget_media": round(t_retargeted - t_compiled, 1),
                                 "tidy_and_checks": round(time.time() - t_retargeted, 1)},
            "next": f"T capcut-finish --run RUN --draft \"{d}\" --video {a.video}"}


def cmd_capcut_compose(a):
    out(compose_run(a))


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


BLUR_LEVELS = (0.0625, 0.375, 0.75, 1.0)      # CapCut's four-step background blur (capcut-cli's own table)


def write_bg_blur(d: Path, level: int, ats: list, fps: int) -> dict:
    """The background blur of the fit-blur clips, written into the draft the way capcut-cli's `bg-blur` does it (setBgBlur: a `canvas_blur` material in the draft's `canvases`, its id
    in the clip's extra_material_refs, an earlier canvas of that clip replaced), for every clip at once instead of one process per clip. `ats` are the clips' starts in output seconds."""
    lvl = min(max(int(level), 1), 4)
    half = 500000 / max(1, int(fps))
    ids, files, unmatched = {}, [], set()
    for p in draft_files(d):
        content = json.loads(p.read_text(encoding="utf-8"))
        main = next((t for t in content.get("tracks", []) if t.get("type") == "video"), None)
        segs = (main or {}).get("segments") or []
        canvases = content.setdefault("materials", {}).setdefault("canvases", [])
        done = 0
        for at in ats:
            seg = next((s for s in segs if abs(int((s.get("target_timerange") or {}).get("start") or 0) - at * 1e6) <= half), None)
            if seg is None:
                unmatched.add(at)
                continue
            old = {c.get("id") for c in canvases}
            seg["extra_material_refs"] = [r for r in (seg.get("extra_material_refs") or []) if r not in old]
            cid = ids.setdefault(round(at, 6), str(uuid.uuid4()))          # the same id in every copy of the timeline
            canvases.append({"album_image": "", "blur": BLUR_LEVELS[lvl - 1], "color": "", "id": cid, "image": "", "image_id": "", "image_name": "",
                             "source_platform": 0, "team_id": "", "type": "canvas_blur"})
            seg["extra_material_refs"].append(cid)
            done += 1
        if done:
            shutil.copyfile(p, p.with_name(p.name + ".blur.bak"))
            write_text(p, json.dumps(content, ensure_ascii=False))
        files.append({"file": p.name, "clips_blurred": done})
    return {"files": files, "level": lvl, "blur": BLUR_LEVELS[lvl - 1], "clips_without_a_match": sorted(unmatched), "blurred": files[0]["clips_blurred"] if files else 0}


def main_clips(d: Path) -> list:
    content = json.loads((d / "draft_content.json").read_text(encoding="utf-8"))
    main = next((t for t in content.get("tracks", []) if t.get("type") == "video"), None)
    return (main or {}).get("segments") or []


def sh(args: list, timeout: float = 900):
    cp = run_cmd(args, timeout=timeout)
    return {"exit": cp.returncode, "result": last_json(cp.stdout) or (cp.stdout or "").strip()[-500:], "stderr": (cp.stderr or "").strip()[-300:]}


def prune_draft_history(d: Path) -> int:
    """capcut-cli keeps an undo snapshot of the WHOLE draft (3 documents) after every write, in <draft>/.capcut-cli-history: with one `import-srt` per caption track
    that made the first word-box project 74 MB of snapshots for a 5 MB draft, and an hour-long one would fill the drive. Nothing here uses `capcut restore`: the
    snapshots of THIS draft folder are removed (only *.snap files directly inside .capcut-cli-history). Returns the bytes freed."""
    h = Path(d) / ".capcut-cli-history"
    freed = 0
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
    return freed


def prune_draft_backups(d: Path) -> int:
    """After a finish that succeeded: the *.bak copies the build tools left beside the draft's documents (draft_content.json.bak, .compose.bak, .font.bak, .link.bak and the
    same for draft_info.json and template-2.tmp) are dropped, because a draft with thousands of caption texts is tens of MB and a dozen copies of it are not worth the
    drive's space; the build can be redone from the plan files with `capcut-compose`. Only files directly in the draft folder whose name ends in .bak. Returns the bytes freed."""
    freed = 0
    for f in Path(d).glob("*.bak"):
        try:
            freed += f.stat().st_size
            f.unlink()
        except OSError:
            pass
    return freed + prune_draft_history(d)


def count_text_segments(d: Path, names: list) -> int:
    c = read_json(d / "draft_content.json") or {}
    return sum(len(t.get("segments") or []) for t in c.get("tracks", []) if t.get("type") == "text" and str(t.get("name") or "") in names)


def finish_run(a) -> dict:
    """The rest of the build, after capcut-compose: the zoom keys and the background blur (written straight into the draft: compile has no operation for them), the
    caption font and entrance and the repair (awl's helpers). What compose already put in the draft (composed.json: the transitions and the word-box texts, checked against
    the plan by a fingerprint) is not written again; a draft built another way (the MCP route, `--bare`, a changed EDL) still gets everything the older way."""
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
    composed = read_json(vdir / "composed.json") or {}
    if str(composed.get("draft") or "") != str(d):
        composed = {}                                 # compose wrote it for another draft (or not at all): nothing is assumed to be in this one
    steps = []
    fps = int(finish["canvas"].get("fps") or 30)
    if finish.get("zoom"):
        steps.append({"step": "zoom-keys", **write_zoom_keys(d, finish["zoom"], fps)})
    clips = main_clips(d)
    half = 500000 / fps
    done, failed = [], []
    ct = composed.get("transitions")
    if ct is not None:                                # the transitions are operations of the composition
        done, failed = list(ct.get("done") or []), list(ct.get("failed") or [])
        have = len((read_json(d / "draft_content.json") or {}).get("materials", {}).get("transitions") or [])
        if have < len(done):
            failed.append({"error": f"the draft holds {have} transitions and the composition made {len(done)}: compose it again"})
        steps.append({"step": "transitions", "composed": True, "done": done, "failed": failed, "in_draft": have})
    else:
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
        ats = [mp["at_s"] for mp in finish["main_pieces"] if mp["layout"] == "fit-blur"]
        r = write_bg_blur(d, int(finish["bg_blur"]), ats, fps)
        steps.append({"step": "bg-blur", **r, "exit": 0 if not r["clips_without_a_match"] else 1, "note": "unverified on this PC's CapCut: look at the first project"})
    caps = finish["captions"]
    srt = vdir / "captions.srt"
    if not captions_on(run):                          # the user picked no captions at the start: no caption track, no font, no entrance
        steps.append({"step": "captions", "skipped": "captions are off for this run (state.json captions=off)"})
    else:
        if not srt.is_file():
            fail(f"captions are on for this run and {srt} does not exist: run `captions` first")
        font_path = caption_font(caps)
        size, size_info = caption_size(caps, finish["canvas"], font_path)
        if caps.get("style") == "word-box":               # the spoken word on a rounded colour box: one CapCut text per word and state (cc_wordbox.py)
            cj = read_json(vdir / "captions.json") or {}
            if not cj.get("cues") or cj.get("style") != "word-box":
                fail(f"captions are on (word-box look) and {vdir / 'captions.json'} has no word-box cues: run `captions` again")
            cc_ = composed.get("captions") or {}
            total_s = max([float(m["at_s"]) + float(m["dur_s"]) for m in finish.get("main_pieces") or []] or [0.0])
            w = word_box_parts(vdir, caps, finish["canvas"], total_s) if cc_.get("composed") else None
            names = [t["track"] for t in (cc_.get("track_list") or [])]
            if (w and w["parts"] and cc_.get("fingerprint") == parts_fingerprint(w["parts"]) and (cc_.get("check") or {}).get("ok")
                    and count_text_segments(d, names) == w["parts"]["texts"]):
                # the texts are in the draft already, written by the composition and checked against this very plan: only the font and the entrance are left
                steps.append({"step": "captions-word-box", "composed": True, "captions": w["plan"]["captions"], "tracks": cc_["tracks"], "texts": cc_["texts"],
                              "boxed_texts": (cc_.get("check") or {}).get("boxed_texts"), "geometry": w["plan"]["geometry"], "box": w["plan"]["box"], "exit": 0})
                steps.extend(wb.font_and_entrance(d, w["caps"], [t for t in w["parts"]["plan_tracks"] if t["entrance"]], font_path, awl, run, sh))
            else:                                         # a draft built another way, or a plan that changed since compose: the older route drops any earlier caption tracks and imports again
                r = wb.apply_word_box(d, vdir, {**caps, "size": size}, cj["cues"], finish["canvas"], font_path, cli, awl, run, sh, draft_files, after_write=lambda: prune_draft_history(d))
                steps.extend(r["steps"])
                if not r["ok"] and r.get("error"):
                    steps.append({"step": "captions-word-box", "exit": 1, "error": r["error"], "geometry": r.get("geometry")})
        else:
            args = [cli, "import-srt", str(d), str(srt), "--track-name", "subtitle", "--font-size", str(size), "--color", caps["color"],
                    "--border-width", str(caps["stroke_width"]), "--border-color", caps["stroke_color"], "--align", "1", "--y", f"{1 - 2 * float(caps['y_rel']):.3f}"]
            if caps.get("shadow"):
                args.append("--shadow")
            hw = [w for w in caps.get("highlight_words") or [] if str(w).strip()]
            if hw:
                hf = vdir / "highlight-words.txt"
                write_text(hf, "\n".join(hw) + "\n")
                args += ["--highlight-words", f"@{hf}", "--keyword-color", caps["highlight_color"], "--keyword-size", str(caps["highlight_size"])]
            steps.append({"step": "captions-import", **sh(args, 900)})
            steps.append({"step": "captions-font", **sh([*awl, "capcut-font", "--draft", str(d), "--font-file", font_path, "--track", "subtitle"], 300)})
            if caps.get("intro"):
                steps.append({"step": "captions-intro", **sh([*awl, "capcut-text-anim", "--draft", str(d), "--track", "subtitle", "--intro", caps["intro"],
                                                                 "--intro-duration", str(caps.get("intro_s") or 0.1), "--run", str(run)], 300)})
    steps.append({"step": "repair", **sh([*awl, "capcut-repair", "--draft", str(d), "--keep-text"], 1800)})
    bad = [s for s in steps if s.get("exit") not in (None, 0) and s["step"] != "repair"] + ([s for s in steps if s["step"] == "repair" and s.get("exit") not in (0,)])
    ok = not bad and not failed and not any(s.get("pieces_without_a_clip") for s in steps)
    if ok:                                           # a finished build: the undo snapshots and the .bak copies are dropped (a draft with thousands of caption texts is tens of MB each)
        steps.append({"step": "cleanup", "freed_mb": round(prune_draft_backups(d) / 1048576, 1), "note": "capcut-cli's undo snapshots and the *.bak copies of this draft's documents; the plan files in the video's output folder rebuild it"})
    else:
        prune_draft_history(d)                       # the snapshots are never needed; the .bak copies stay for the failure
    return {"ok": ok, "draft": str(d), "video": a.video, "steps": steps}


def cmd_capcut_finish(a):
    out(finish_run(a))


def build_checks(d: Path, resolved: dict, composed: dict, cli: str) -> dict:
    """The read-back of a finished build in one pass (what the production agents ran as `capcut segments`, `capcut texts` and `capcut lint`, one command each): the clips of the
    main track against the plan, whether the joins are contiguous, the audio clips, the texts against the number the captions' plan made, the transitions and zoom keys the draft
    holds, every media file on disk, and capcut lint's counts. Facts only: `capcut-build` turns the ones that disagree with the plan into `problems`."""
    c = read_json(d / "draft_content.json") or {}
    tracks = c.get("tracks") or []
    main = next((t for t in tracks if t.get("type") == "video"), None)
    segs = sorted((main or {}).get("segments") or [], key=lambda s: int((s.get("target_timerange") or {}).get("start") or 0))
    ends = [int(s["target_timerange"]["start"]) + int(s["target_timerange"]["duration"]) for s in segs]
    off = sum(1 for s, e in zip(segs[1:], ends) if abs(int(s["target_timerange"]["start"]) - e) > 1)
    mats = c.get("materials") or {}
    missing = sorted({str(m.get("path")) for k in ("videos", "audios") for m in mats.get(k) or [] if m.get("path") and not Path(str(m["path"])).exists()})
    text_tracks = [t for t in tracks if t.get("type") == "text"]
    cap = composed.get("captions") or {}
    lint = sh([cli, "lint", str(d)], 600)
    lr = lint["result"] if isinstance(lint.get("result"), dict) else {}
    issues = lr.get("issues") or []
    codes = {}
    for i in issues:
        codes[f"{i.get('severity')}:{i.get('code')}"] = codes.get(f"{i.get('severity')}:{i.get('code')}", 0) + 1
    size = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
    return {"main_clips": len(segs), "planned_pieces": len(resolved["pieces"]), "main_end_s": round(max(ends, default=0) / 1e6, 3), "planned_s": float(resolved["totals"]["duration_s"]),
            "joins_not_contiguous": off, "audio_clips": sum(len(t.get("segments") or []) for t in tracks if t.get("type") == "audio"), "planned_sfx": int(resolved["totals"].get("sfx") or 0),
            "text_tracks": len(text_tracks), "texts": sum(len(t.get("segments") or []) for t in text_tracks), "composed_caption_texts": cap.get("texts") if cap.get("composed") else None,
            "transitions_in_draft": len(mats.get("transitions") or []), "zoomed_clips": sum(1 for s in segs if s.get("common_keyframes")), "media_missing": missing[:5],
            "draft_mb": round(size / 1048576, 1),
            "lint": {"errors": (lr.get("summary") or {}).get("errors"), "warnings": (lr.get("summary") or {}).get("warnings"), "by_code": codes,
                     "error_messages": [str(i.get("message"))[:160] for i in issues if i.get("severity") == "error"][:5], "exit": lint["exit"]}}


def cmd_capcut_build(a):
    """ONE command for the whole CapCut project (the user, 2026-11-13: the composition for everything, for faster delivery): capcut-compose (the clips, the sound-effect lanes, the
    transitions and the word-box captions in one `capcut compile`), capcut-finish (the zoom keys, the background blur, the caption font and entrance, the repair, the clean-up) and the
    read-back (clips, length, joins, texts, transitions, media on disk, capcut lint). One JSON answer; `problems` lists what disagrees with the plan."""
    run = resolve_run(a.run)
    vdir = run_paths(run)["outputs"] / a.video
    t0 = time.time()
    if captions_on(run):
        cap_files = [vdir / "captions.srt", vdir / "captions.json"]
        if not all(f.is_file() for f in cap_files):
            fail(f"captions are on for this run and {vdir / 'captions.srt'} or captions.json does not exist: run `captions` first (nothing was changed)")
        if (vdir / "resolved.json").is_file() and cap_files[1].stat().st_mtime < (vdir / "resolved.json").stat().st_mtime - 1:
            fail(f"{cap_files[1]} is older than the last edl-check ({vdir / 'resolved.json'}): the cues may not match the cuts; run `captions` again (nothing was changed)")
    cres = compose_run(argparse.Namespace(run=a.run, video=a.video, name=a.name, store=a.store, template=a.template, channel=a.channel, bare=a.bare))
    t1 = time.time()
    if not cres.get("draft"):
        out({"ok": False, "video": a.video, "compose": cres, "problems": ["compose failed"]}, 1)
    fres = finish_run(argparse.Namespace(run=a.run, draft=cres["draft"], video=a.video))
    t2 = time.time()
    d = Path(cres["draft"])
    resolved = read_json(vdir / "resolved.json") or {}
    chk = build_checks(d, resolved, read_json(vdir / "composed.json") or {}, capcut_cli())
    t3 = time.time()
    problems = []
    if not cres.get("ok"):
        problems.append("compose reported a problem (see compose)")
    for s in fres.get("steps") or []:
        if s.get("exit") not in (None, 0):
            problems.append(f"finish step {s.get('step')} failed: {str(s.get('error') or s.get('stderr') or s.get('result'))[:200]}")
        if s.get("failed"):
            problems.append(f"finish step {s.get('step')}: {len(s['failed'])} failed, first: {str(s['failed'][0])[:200]}")
        if s.get("pieces_without_a_clip"):
            problems.append(f"zoom keys: pieces without a clip: {s['pieces_without_a_clip']}")
    if chk["main_clips"] != chk["planned_pieces"]:
        problems.append(f"the main track has {chk['main_clips']} clips and the plan {chk['planned_pieces']} pieces")
    if abs(chk["main_end_s"] - chk["planned_s"]) > 0.1:
        problems.append(f"the main track ends at {chk['main_end_s']} s and the plan says {chk['planned_s']} s")
    if chk["joins_not_contiguous"]:
        problems.append(f"{chk['joins_not_contiguous']} clips do not start where the one before ends")
    if chk["composed_caption_texts"] is not None and chk["texts"] != chk["composed_caption_texts"]:
        problems.append(f"the draft holds {chk['texts']} texts and the composition made {chk['composed_caption_texts']}")
    if chk["media_missing"]:
        problems.append(f"media files missing on disk: {chk['media_missing']}")
    if chk["lint"]["errors"]:
        problems.append(f"capcut lint: {chk['lint']['errors']} errors: {chk['lint']['error_messages']}")
    elif chk["lint"]["errors"] is None:
        problems.append(f"capcut lint gave no summary (exit {chk['lint']['exit']})")
    cj = (read_json(vdir / "captions.json") or {}) if captions_on(run) else {}
    cfont = {"file": cj.get("font_file"), "house_font": cj.get("house_font"), "missing_glyphs": cj.get("font_missing_glyphs")} if cj else None
    if cfont and cfont["missing_glyphs"]:
        problems.append(f"the caption font cannot draw these characters of the captions: {''.join(cfont['missing_glyphs'])} (CapCut would show boxes or another font's letters)")
    slim = [{k: v for k, v in s.items() if k in ("step", "exit", "composed", "texts", "tracks", "boxed_texts", "keyed", "blurred", "done", "failed", "freed_mb", "animated", "in_draft")} for s in fres.get("steps") or []]
    out({"ok": not problems, "video": a.video, "draft": cres["draft"], "name": cres.get("name"), "seconds": round(time.time() - t0, 1),
         "seconds_by_part": {"compose": round(t1 - t0, 1), "finish": round(t2 - t1, 1), "read_back": round(t3 - t2, 1)},
         "compose": {k: cres.get(k) for k in ("ok", "pieces", "sfx_lanes", "composed_in_the_same_call", "extras_error_then_composed_bare", "video_segments_retargeted", "seconds")},
         "finish": {"ok": fres.get("ok"), "steps": slim}, "read_back": chk, "caption_font": cfont, "problems": problems,
         "note": "unverified by any tool here: how CapCut draws the project (the caption look, the zoom, a fill or fit-blur layout); the proxy frames and the first open in CapCut are the look-at-it checks"}, 0 if not problems else 1)


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

    p = sub.add_parser("blocks", help="split the chunks into blocks of N for scan agents (at least M blocks with --min-blocks, so a short recording still gets side-by-side agents)")
    p.add_argument("--run", required=True)
    p.add_argument("--chunks", type=int, default=10)
    p.add_argument("--min-blocks", dest="min_blocks", type=int, default=1, help="at least this many blocks: the block size becomes min(--chunks, ceil(chunks / M))")
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

    p = sub.add_parser("captions", help="caption cues from the transcript words of the resolved pieces (the word-box look's texts as facts; nothing when the run's captions setting is off)")
    p.add_argument("--run", required=True)
    p.add_argument("--resolved", required=True, help="the resolved.json next to the EDL")
    p.set_defaults(func=cmd_captions)

    p = sub.add_parser("fonts", help="the font files the captions can use (family, style, file, where it is kept): the Loupe fonts folder first, then CapCut's own, then Windows'; --family filters")
    p.add_argument("--family", help="only the families containing this text (e.g. luckiest, bangers, montserrat)")
    p.set_defaults(func=cmd_fonts)

    p = sub.add_parser("capcut-name", help="a free CapCut project name")
    p.add_argument("--channel", required=True)
    p.add_argument("--video", required=True)
    p.set_defaults(func=cmd_capcut_name)

    p = sub.add_parser("capcut-compose", help="the whole CapCut project in one `capcut compile` from resolved.json: the clips on the real chunk paths, the sound-effect lanes, the transitions and (word-box look) the caption texts")
    p.add_argument("--run", required=True)
    p.add_argument("--video", required=True)
    p.add_argument("--name", help="the project name (default: a free DD_Mon_YYYY_<channel>_<video>)")
    p.add_argument("--channel")
    p.add_argument("--store", help="the CapCut drafts folder (default: the real store)")
    p.add_argument("--template", help="a template folder, or auto/bundled (capcut-cli's own choices); default: data/compose-template, an empty draft with this PC's CapCut 9.7 version markers. A folder that holds clips keeps them")
    p.add_argument("--bare", action="store_true", help="only the clips and the sound-effect lanes (the older split: capcut-finish then writes the transitions and the captions)")
    p.set_defaults(func=cmd_capcut_compose)

    p = sub.add_parser("capcut-finish", help="after capcut-compose (or the last MCP save): zoom keys, bg blur, the caption font and entrance, repair, clean-up; transitions and captions only when compose did not put them in")
    p.add_argument("--run", required=True)
    p.add_argument("--draft", required=True)
    p.add_argument("--video", required=True)
    p.set_defaults(func=cmd_capcut_finish)

    p = sub.add_parser("capcut-build", help="ONE command for the whole project: capcut-compose + capcut-finish + the read-back (clips, length, joins, texts, media, capcut lint); `problems` lists what disagrees with the plan")
    p.add_argument("--run", required=True)
    p.add_argument("--video", required=True)
    p.add_argument("--name", help="the project name (default: a free DD_Mon_YYYY_<channel>_<video>)")
    p.add_argument("--channel")
    p.add_argument("--store", help="the CapCut drafts folder (default: the real store)")
    p.add_argument("--template", help="see capcut-compose")
    p.add_argument("--bare", action="store_true", help="see capcut-compose")
    p.set_defaults(func=cmd_capcut_build)
