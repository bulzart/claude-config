#!/usr/bin/env python3
"""atp.py - deterministic local toolkit for the /analyze-then-pick Claude Code command.

Everything here is local and deterministic: FFmpeg/ffprobe do all media work; Pillow builds the
contact sheets; faster-whisper (optional, local) transcribes speech; RapidOCR (optional, local)
samples on-screen text. Nothing in this file calls Higgsfield's MCP tools: uploads use the presigned
URL that `media_upload` returns, downloads use the public result URL that `jobs_wait` returns.

Video sampling policy (see pipeline/preprocessing.md):
  * baseline: ~5 frames per second over the whole video (one FFmpeg fps pass);
  * densify:  last/first frame at every cut, ~10 fps around motion peaks and in the first second;
              more on demand with `frames --range a-b --fps N`;
  * thin:     static stretches keep >= 1 frame per second (near-duplicate frames are dropped and
              reported as static runs, never silently).

Subcommands (python atp.py <cmd> -h):
  new-run        create a run workspace and state.json
  state          read or update state.json (get [key] | set key=value ... | append key=value ...)
  inventory      recursive inventory of files/folders --as references | sources (edit videos) | assets
                 | examples (your own finished videos: study only)
  prep-assets    previews, doc text, font names and a labelled contact sheet of USER-SUPPLIED assets
  model-menu     numbered table of EVERY available video model (pinned first) + quick picks
  model-entry    ONE model's index.json entry + its guide path and section folder (index.json is 40 KB: never read it whole)
  ledger        anti-duplicate guard for paid generations (begin before, set after every call)
  caught-flag    flag record caught_flags.html (data + viewer page): prompts and videos Higgsfield flagged or refused
                 (add | set | list | reconcile | open | render)
  open           open a finished video in the default player for the user's review
  prep-video     probe, cuts, activity, 5 fps adaptive frames, storyboard sheets, audio, transcript,
                 OCR sample, per-second timeline, summary
  prep-all       prep-video for every inventoried video + image previews + document text (--set examples)
  frames         targeted extraction (timestamps or dense ranges) with an optional sheet
  prep-image     image metadata + orientation-corrected preview
  doc-text       plain-text extraction (txt/md/csv/json/srt/vtt/html/docx/pptx/xlsx)
  hf-put         HTTP PUT of a local file to a Higgsfield presigned upload URL
  hf-get         download a generated result URL and verify it with ffprobe
  fetch-audio    download a soundtrack / sound effect (Analyze Create) and record its source and license
  audio-profile  sound design of a reference: music bed, tempo, beat strength, energy arc, hits on cuts
  split-audio    per original video: audio → <path>/files_audio/, silent copy → <path>/videos_without_audio/
                 (--audio-only: files_audio/ only, for Analyze Create)
  restore-audio  generated picture + ORIGINAL audio (from files_audio or the original video)
  sync-check     do the output's actions happen at the source's moments (the original audio's timing)?
                 offset, drift, duration difference, side-by-side sheet; fix hint (trim / audio start / regenerate)
  finalize       approved Edit Mode result → <given path>/final/<original name>.mp4
  conform        exact 720x1280 (9:16) output without stretching: scale-to-cover + focus crop, or pad
  captions       burn exact, frame-consistent text with libass (explicit events or speech-timed)
  clean          local Edit-Mode clean-up: delogo small static overlays, crop away static text bands
  trim           frame-accurate trim (removes generated dead space at head/tail)
  concat         normalise clips to 720x1280 and join them in order (multi-clip videos; cut or continuous seams)
  last-frame     exact last frame of a clip as a lossless PNG: the hand-off start frame for the next clip
  capcut-name    free CapCut project name DD_Mon_YYYY_vNN for an Analyze Mode video
  capcut-prep    after capcut_clone_draft: set aside the template's identity/layout so `capcut register` rebuilds them
  capcut-repair  after capcut_save: house text style + register + sync-timelines + lint (one machine-wide lock),
                 then a proxy preview
  capcut-text-style  every CapCut text layer → the user's locked house preset (config capcut.text_style.learned)
                 (--check reports; --learn copies the exact preset from a text styled once in CapCut;
                 a locked preset is only replaced with --learn --replace)
  strip-inserts  a reference minus its inserts (memes) in one pass + silent copy + map of the split points
  qc             storyboard + checks (size, duration, black, freeze, mode-aware visible text) for an output

Every command prints one JSON object on its last stdout line. Exit codes: 0 ok, 1 failure,
2 bad arguments.
"""
from __future__ import annotations

import argparse
import base64
import concurrent.futures as cf
import datetime as dt
import glob
import hashlib
import html
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
import threading
import time
import webbrowser
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ATP_HOME = Path(__file__).resolve().parent.parent
CONFIG_PATH = ATP_HOME / "config.json"

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi", ".wmv", ".flv", ".mpg", ".mpeg",
             ".3gp", ".ts", ".mts", ".m2ts"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".heic", ".heif", ".avif"}
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".wma"}
TEXT_EXT = {".txt", ".md", ".markdown", ".csv", ".tsv", ".json", ".yaml", ".yml", ".srt", ".vtt",
            ".html", ".htm", ".xml", ".rtf", ".log"}
OFFICE_EXT = {".docx", ".pptx", ".xlsx"}
PDF_EXT = {".pdf"}
FONT_EXT = {".ttf", ".otf", ".woff", ".woff2"}
VECTOR_EXT = {".svg", ".eps", ".ai"}

# Filename / folder-name hints for USER-SUPPLIED assets only (non-authoritative; the command confirms
# every role by looking at the asset). Never used to find assets inside a references folder.
ASSET_HINTS = [
    (r"canonical|template|master|source.?of.?truth|dieline|blueprint|dimension", "canonical-template?"),
    (r"(^|[^a-z])front([^a-z]|$)", "view:front"), (r"(^|[^a-z])(back|rear)([^a-z]|$)", "view:back"),
    (r"(^|[^a-z])(side|left|right|profile|three.?quarter|3.?4)([^a-z]|$)", "view:side"),
    (r"(^|[^a-z])(top|overhead|bottom)([^a-z]|$)", "view:top/bottom"),
    (r"variant|flavou?r|colou?rway|edition|version|sku", "variant?"),
    (r"logo|wordmark|brandmark|monogram", "logo?"),
    (r"character|avatar|mascot|talent|actor|actress|influencer|creator|person|face|headshot|turnaround|model.?sheet", "character?"),
    (r"screen|screenshot|(^|[^a-z])ui([^a-z]|$)|interface|dashboard|app", "interface?"),
    (r"environment|location|background|(^|[^a-z])set([^a-z]|$)|room|studio|scene", "environment?"),
    (r"palette|brand.?guide|guideline|style.?guide|brandbook", "brand-guide?"),
    (r"pack|packaging|box|label|wrapper", "packaging?"),
    (r"voice|vo|narration", "voice?"), (r"music|track|song|bgm", "music?"),
]
DERIVED_DIRS = {"files_audio", "videos_without_audio"}      # created by split-audio inside the user's path
FINAL_DIR = "final"                                          # approved Edit Mode results, inside the user's path
FINAL_MARKER = ".atp-final"                                  # hidden marker: only OUR final folder is skipped
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".idea", ".vscode",
             "$RECYCLE.BIN", "System Volume Information", ".analyze-then-pick"} | DERIVED_DIRS
AUDIO_EXT_FOR_CODEC = {"aac": ".m4a", "alac": ".m4a", "mp3": ".mp3", "opus": ".opus", "vorbis": ".ogg",
                       "flac": ".flac", "pcm_s16le": ".wav", "pcm_s24le": ".wav", "pcm_f32le": ".wav"}

CONTENT_TYPES = {
    ".mp4": "video/mp4", ".mov": "video/quicktime", ".m4v": "video/mp4", ".webm": "video/webm",
    ".mkv": "video/x-matroska", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    ".webp": "image/webp", ".gif": "image/gif", ".mp3": "audio/mpeg", ".wav": "audio/wav",
    ".m4a": "audio/mp4", ".aac": "audio/aac", ".flac": "audio/flac", ".ogg": "audio/ogg",
}


# --------------------------------------------------------------------------- utilities

def load_config() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def cfg_get(path: str, default=None):
    cur = load_config()
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def out(obj: dict, code: int = 0):
    # one JSON object on the last line: U+2028/2029 are escaped so a line-splitting reader never cuts it in two
    print(json.dumps(obj, ensure_ascii=False).replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))
    sys.exit(code)


def fail(msg: str, code: int = 1, **extra):
    out({"ok": False, "error": msg, **extra}, code)


def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def slugify(text: str, maxlen: int = 40) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return (s or "run")[:maxlen]


def ts_label(t: float) -> str:
    m, s = divmod(max(0.0, t), 60)
    return f"{int(m):02d}:{s:05.2f}"


def ts_name(t: float) -> str:
    m, s = divmod(max(0.0, t), 60)
    return f"{int(m):02d}m{s:05.2f}s"


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def find_tool(name: str) -> str:
    cfg = load_config().get("tools", {})
    if cfg.get(name) and Path(cfg[name]).exists():
        return cfg[name]
    found = shutil.which(name)
    if found:
        return found
    local = os.environ.get("LOCALAPPDATA", "")
    patterns = [
        os.path.join(local, "Microsoft", "WinGet", "Packages", "*FFmpeg*", "*", "bin", name + ".exe"),
        os.path.join(local, "Microsoft", "WinGet", "Links", name + ".exe"),
        os.path.join("C:\\", "ffmpeg", "bin", name + ".exe"),
        os.path.join("C:\\", "Program Files", "ffmpeg", "bin", name + ".exe"),
    ]
    for pat in patterns:
        hits = sorted(glob.glob(pat), reverse=True)
        if hits:
            return hits[0]
    raise FileNotFoundError(f"{name} not found on PATH or in the usual install folders")


def run(cmd: list, cwd=None, timeout=None, check=False) -> subprocess.CompletedProcess:
    cp = subprocess.run([str(c) for c in cmd], cwd=cwd, capture_output=True, text=True,
                        encoding="utf-8", errors="replace", timeout=timeout)
    if check and cp.returncode != 0:
        raise RuntimeError(f"command failed ({cp.returncode}): {' '.join(map(str, cmd))[:300]}\n"
                           f"{cp.stderr[-1500:]}")
    return cp


def ffprobe_json(path) -> dict:
    cp = run([find_tool("ffprobe"), "-v", "error", "-show_streams", "-show_format", "-of", "json",
              str(path)], timeout=120)
    if cp.returncode != 0:
        raise RuntimeError(f"ffprobe failed on {path}: {cp.stderr.strip()[:400]}")
    return json.loads(cp.stdout or "{}")


def _ratio(s: str | None) -> float | None:
    if not s or s in ("0/0", "N/A"):
        return None
    try:
        if "/" in s:
            a, b = s.split("/", 1)
            return float(a) / float(b) if float(b) else None
        return float(s)
    except Exception:
        return None


def _rotation(stream: dict) -> int:
    rot = 0
    try:
        rot = int(float(stream.get("tags", {}).get("rotate", 0)))
    except Exception:
        rot = 0
    for sd in stream.get("side_data_list", []) or []:
        if "rotation" in sd:
            try:
                rot = int(float(sd["rotation"]))
            except Exception:
                pass
    return rot % 360


def nearest_aspect(w: int, h: int) -> str:
    if not w or not h:
        return "unknown"
    r = w / h
    common = {"9:16": 9 / 16, "16:9": 16 / 9, "1:1": 1.0, "4:5": 0.8, "3:4": 0.75, "4:3": 4 / 3,
              "21:9": 21 / 9, "2:3": 2 / 3, "3:2": 1.5, "2:1": 2.0}
    best = min(common.items(), key=lambda kv: abs(kv[1] - r))
    if abs(best[1] - r) / best[1] < 0.04:
        return best[0]
    g = math.gcd(int(w), int(h)) or 1
    return f"{int(w) // g}:{int(h) // g}"


def media_summary(path) -> dict:
    """Rotation- and SAR-aware summary following Higgsfield's media-pipeline normalisation."""
    pj = ffprobe_json(path)
    streams = pj.get("streams", [])
    fmt = pj.get("format", {})
    vids = [s for s in streams if s.get("codec_type") == "video"
            and not (s.get("disposition", {}) or {}).get("attached_pic")]
    auds = [s for s in streams if s.get("codec_type") == "audio"]
    v = next((s for s in vids if (s.get("disposition", {}) or {}).get("default") == 1), vids[0] if vids else None)
    a = next((s for s in auds if (s.get("disposition", {}) or {}).get("default") == 1), auds[0] if auds else None)
    dur = None
    for cand in (fmt.get("duration"), (v or {}).get("duration"), (a or {}).get("duration")):
        try:
            if cand is not None and math.isfinite(float(cand)) and float(cand) > 0:
                dur = float(cand)
                break
        except Exception:
            pass
    res = {"path": str(path), "duration_s": round(dur, 3) if dur else None,
           "size_bytes": int(fmt.get("size", 0) or 0), "format": fmt.get("format_name"),
           "bitrate": int(fmt.get("bit_rate", 0) or 0), "has_video": bool(v), "has_audio": bool(a)}
    if v:
        w, h = int(v.get("width", 0) or 0), int(v.get("height", 0) or 0)
        sar = _ratio(v.get("sample_aspect_ratio")) or 1.0
        rot = _rotation(v)
        dw, dh = (round(w * sar), h)
        if rot in (90, 270):
            dw, dh = dh, dw
        fps = _ratio(v.get("avg_frame_rate")) or _ratio(v.get("r_frame_rate")) or 24.0
        res.update({"codec": v.get("codec_name"), "width": w, "height": h, "rotation": rot,
                    "display_width": dw, "display_height": dh, "fps": round(fps, 3),
                    "aspect": nearest_aspect(dw, dh),
                    "orientation": "portrait" if dh > dw * 1.05 else ("landscape" if dw > dh * 1.05 else "square"),
                    "pix_fmt": v.get("pix_fmt"), "nb_frames": int(v.get("nb_frames", 0) or 0),
                    "video_start": float(v.get("start_time", 0) or 0)})
    if a:
        res.update({"audio_codec": a.get("codec_name"), "audio_index": int(a.get("index", 0)),
                    "audio_channels": a.get("channels"), "audio_rate": a.get("sample_rate"),
                    "audio_start": float(a.get("start_time", 0) or 0)})
    return res


def quick_hash(path: Path) -> str:
    h = hashlib.sha1()
    size = path.stat().st_size
    h.update(str(size).encode())
    with open(path, "rb") as f:
        h.update(f.read(1 << 20))
        if size > (2 << 20):
            f.seek(-(1 << 20), os.SEEK_END)
            h.update(f.read(1 << 20))
    return h.hexdigest()[:16]


def classify(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in VIDEO_EXT:
        return "video"
    if ext == ".gif":
        try:
            s = media_summary(path)
            return "video" if (s.get("nb_frames") or 0) > 1 else "image"
        except Exception:
            return "image"
    if ext in IMAGE_EXT:
        return "image"
    if ext in AUDIO_EXT:
        return "audio"
    if ext in PDF_EXT:
        return "pdf"
    if ext in OFFICE_EXT:
        return "office"
    if ext in TEXT_EXT:
        return "text"
    if ext in FONT_EXT:
        return "font"
    if ext in VECTOR_EXT:
        return "vector"
    return "other"


# --------------------------------------------------------------------------- frame extraction

def _scale_vf(max_side: int) -> str:
    return (f"scale='if(gt(iw,ih),min({max_side},iw),-2)':'if(gt(iw,ih),-2,min({max_side},ih))'")


def extract_frame(video: str, t: float, dest: Path, max_side: int = 1280) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt_t in (t, max(0.0, t - 0.15), max(0.0, t - 0.4)):
        cp = run([find_tool("ffmpeg"), "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                  "-ss", f"{attempt_t:.3f}", "-i", video, "-frames:v", "1", "-vf", _scale_vf(max_side),
                  "-q:v", "3", str(dest)], timeout=120)
        if cp.returncode == 0 and dest.exists() and dest.stat().st_size > 0:
            return True
    return False


def extract_many(video: str, items: list, max_side: int = 1280, workers: int = 4) -> list:
    """items: [(t, dest_path, extra_dict)] -> [{t, file, ok, **extra}] sorted by t."""
    results = []
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(extract_frame, video, t, d, max_side): (t, d, extra) for t, d, extra in items}
        for fut in cf.as_completed(futs):
            t, d, extra = futs[fut]
            try:
                ok = fut.result()
            except Exception:
                ok = False
            results.append({"t": round(t, 3), "file": str(d), "ok": ok, **(extra or {})})
    results.sort(key=lambda r: (r["t"], r["file"]))
    return results


def extract_baseline(video: str, fps: float, dest: Path, dur: float, max_side: int = 720,
                     max_frames: int = 1800) -> tuple[list, float, str | None]:
    """One FFmpeg pass on a regular grid: frame n shows the source frame nearest to n / fps."""
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True, exist_ok=True)
    eff, note = fps, None
    if dur and dur * fps > max_frames:
        eff = max_frames / dur
        note = (f"baseline lowered from {fps} to {eff:.2f} fps to respect max_frames={max_frames}; "
                f"densify segments of interest with `frames --range a-b --fps {fps:g}`")
    run([find_tool("ffmpeg"), "-hide_banner", "-loglevel", "error", "-nostdin", "-y", "-i", video,
         "-map", "0:v:0", "-vf", f"fps={eff:.6f},{_scale_vf(max_side)}", "-q:v", "4",
         "-start_number", "0", str(dest / "base_%06d.jpg")], timeout=3600, check=True)
    files = sorted(dest.glob("base_*.jpg"))
    frames = []
    for p in files:
        n = int(p.stem.split("_")[1])
        t = n / eff
        if dur and t > dur:
            break
        frames.append({"t": round(t, 3), "file": str(p), "ok": True, "kind": "base"})
    return frames, eff, note


def thin_static(frames: list, threshold: float = 2.5, max_gap: float = 1.0, min_run: int = 3) -> list:
    """Drop near-duplicate baseline frames inside static stretches, keeping >= 1 frame per max_gap
    seconds. Compares each frame with the last KEPT frame (48x48 grey, mean abs difference 0-255), so
    slow continuous motion accumulates and is kept. Only runs of >= min_run consecutive duplicates
    count as a static stretch; shorter runs are restored so ordinary footage keeps its full 5 fps.
    Returns the static runs actually thinned [{start, end, dropped}]."""
    if threshold <= 0:
        for f in frames:
            f["kept"] = True
        return []
    try:
        from PIL import Image
        import numpy as np
    except Exception:
        for f in frames:
            f["kept"] = True
        return []
    ref, ref_t, runs, cur = None, -1e9, [], None
    for f in frames:
        with Image.open(f["file"]) as im:
            g = np.asarray(im.convert("L").resize((48, 48)), dtype="float32")
        if ref is None:
            keep, diff = True, None
        else:
            diff = float(np.mean(np.abs(g - ref)))
            keep = diff >= threshold or (f["t"] - ref_t) >= max_gap - 1e-6
        f["diff_prev_kept"] = None if diff is None else round(diff, 2)
        f["kept"] = keep
        if keep:
            ref, ref_t = g, f["t"]
            if cur:
                runs.append(cur)
                cur = None
        else:
            if cur is None:
                cur = {"start": f["t"], "end": f["t"], "dropped": 0}
            cur["end"] = f["t"]
            cur["dropped"] += 1
    if cur:
        runs.append(cur)
    thinned = []
    for r in runs:
        if r["dropped"] >= min_run:
            thinned.append(r)
        else:                                   # too short to be a static stretch: keep those frames
            for f in frames:
                if r["start"] - 1e-6 <= f["t"] <= r["end"] + 1e-6:
                    f["kept"] = True
    return thinned


# --------------------------------------------------------------------------- sheets

def _font(size: int):
    from PIL import ImageFont
    for cand in (r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf",
                 "/System/Library/Fonts/Helvetica.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(cand, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _layout(orientation: str, dense: bool = True) -> tuple:
    """(cols, rows, cell_w, cell_h). 30 frames per sheet, sized to ≤ 1.15 MP and ≤ 1568 px on the
    long side so Claude's vision reads it at full size: nothing is downscaled, every cell shows at
    its real pixels. Portrait 6 × 5 = 1.2 s per row at 5 fps (828 × 1351); landscape 5 × 6 (1200 ×
    952); square 5 × 6 (920 × 1246). The old 50-cell 1500 px sheets were 2.2 MP and came back
    shrunk by ~0.73, so a 150 px cell showed at ~109 px."""
    if orientation == "landscape":
        return (5, 6, 240, 135) if dense else (3, 4, 480, 270)
    if orientation == "square":
        return (5, 6, 184, 184) if dense else (4, 3, 360, 360)
    return (6, 5, 138, 245) if dense else (4, 3, 300, 533)


STORYBOARD_LEGEND = ("left to right, top to bottom | white = baseline | cyan + = densified | "
                     "red bar = first frame after a cut | grey = static stretch thinned")


def build_storyboard(items: list, dest_prefix: Path, title: str, orientation: str,
                     dense: bool = True, legend: str | None = None, show_times: bool = True) -> list:
    """Chronological flow layout. items: frame dicts {t, file, ok, kind base|extra, shot, flags[],
    label?} or static markers {kind: 'static', start, end, dropped}. An item's 'label' replaces the
    computed time label (used for asset sheets). Returns [{sheet, start, end, cells}]."""
    try:
        from PIL import Image, ImageDraw, ImageOps
    except Exception:
        return []
    cells = [it for it in items if it.get("kind") == "static" or (it.get("ok") and Path(it["file"]).exists())]
    if not cells:
        return []
    cols, rows, cw, ch = _layout(orientation, dense)
    label_h, head_h = 16 if dense else 24, 46
    per = cols * rows
    font, hfont, sfont = _font(12 if dense else 15), _font(17), _font(12)
    pages = math.ceil(len(cells) / per)
    per_page = math.ceil(len(cells) / pages / cols) * cols      # balanced pages, whole rows
    res = []
    for pi in range(pages):
        chunk = cells[pi * per_page:(pi + 1) * per_page]
        if not chunk:
            break
        nrows = math.ceil(len(chunk) / cols)
        sheet = Image.new("RGB", (cols * cw, head_h + nrows * (ch + label_h)), (16, 16, 16))
        dr = ImageDraw.Draw(sheet)
        t_first = chunk[0].get("t", chunk[0].get("start", 0.0))
        t_last = chunk[-1].get("t", chunk[-1].get("end", 0.0))
        span = f"  {ts_label(t_first)}-{ts_label(t_last)}" if show_times else ""
        dr.text((8, 4), f"{title}{span}  (sheet {pi + 1}/{pages})", fill=(240, 240, 240), font=hfont)
        dr.text((8, 25), legend or STORYBOARD_LEGEND, fill=(170, 170, 170), font=sfont)
        for i, it in enumerate(chunk):
            r, c = divmod(i, cols)
            x0, y0 = c * cw, head_h + r * (ch + label_h)
            if it.get("kind") == "static":
                dr.rectangle([x0 + 2, y0 + 2, x0 + cw - 3, y0 + ch - 3], fill=(58, 58, 58))
                dr.text((x0 + 8, y0 + 10), "static", fill=(220, 220, 220), font=font)
                dr.text((x0 + 8, y0 + 28), f"{it['start']:.2f}-{it['end']:.2f}s", fill=(220, 220, 220), font=font)
                dr.text((x0 + 8, y0 + 46), f"{it['dropped']} near-duplicate", fill=(200, 200, 200), font=font)
                dr.text((x0 + 8, y0 + 62), "frames omitted", fill=(200, 200, 200), font=font)
                continue
            try:
                with Image.open(it["file"]) as im:
                    im = ImageOps.exif_transpose(im).convert("RGB")
                    im.thumbnail((cw - 2, ch - 2))
                    sheet.paste(im, (x0 + (cw - im.width) // 2, y0 + (ch - im.height) // 2))
            except Exception:
                dr.rectangle([x0 + 2, y0 + 2, x0 + cw - 2, y0 + ch - 2], outline=(200, 0, 0))
            flags = it.get("flags", [])
            if "after_cut" in flags:
                dr.rectangle([x0, y0, x0 + 4, y0 + ch], fill=(235, 40, 40))
            dr.rectangle([x0, y0 + ch, x0 + cw, y0 + ch + label_h], fill=(0, 0, 0))
            extra = it.get("kind") == "extra"
            if it.get("label"):
                lab = it["label"]
                max_chars = max(8, int(cw / (7 if dense else 8.5)))
                lab = lab if len(lab) <= max_chars else lab[:max_chars - 1] + "…"
            else:
                lab = f"{'+' if extra else ''}{it['t']:.2f}"
                if it.get("shot"):
                    lab += f" S{it['shot']:02d}"
                if "after_cut" in flags:
                    lab += " CUT"
                elif "peak" in flags:
                    lab += " pk"
                if it.get("tag"):
                    lab += f" {it['tag']}"
            dr.text((x0 + 5, y0 + ch + 1), lab, fill=(90, 220, 255) if extra else (245, 245, 245), font=font)
        p = Path(f"{dest_prefix}-{pi + 1:02d}.jpg")
        p.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(p, quality=86)
        res.append({"sheet": str(p), "start": round(t_first, 2), "end": round(t_last, 2), "cells": len(chunk)})
    return res


# --------------------------------------------------------------------------- analysis pieces

def scene_scores(video: str, workdir: Path) -> list:
    """Per-frame ffmpeg scene-change score (0..1) -> [(t, score)]."""
    workdir.mkdir(parents=True, exist_ok=True)
    fname = "scene-scores.txt"
    (workdir / fname).unlink(missing_ok=True)
    cp = run([find_tool("ffmpeg"), "-hide_banner", "-loglevel", "error", "-nostdin", "-i", video,
              "-map", "0:v:0", "-vf", f"scale=192:-2,select='gte(scene,0)',metadata=print:file={fname}",
              "-an", "-f", "null", "-"], cwd=str(workdir), timeout=3600)
    if cp.returncode != 0:
        raise RuntimeError("scene scoring failed: " + cp.stderr[-600:])
    pts, cur_t = [], None
    for line in (workdir / fname).read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.search(r"pts_time:([0-9.eE+-]+)", line)
        if m:
            cur_t = float(m.group(1))
            continue
        m = re.search(r"lavfi\.scene_score=([0-9.eE+-]+)", line)
        if m and cur_t is not None:
            pts.append((cur_t, float(m.group(1))))
            cur_t = None
    return pts


def detect_cuts(scores: list, duration: float, hard: float = 0.30, soft: float = 0.14,
                ratio: float = 4.0, min_gap: float = 0.25) -> list:
    if not scores:
        return []
    times = [t for t, _ in scores]
    vals = [s for _, s in scores]
    n = len(vals)
    cand = []
    for i in range(1, n):
        s = vals[i]
        if s < soft:
            continue
        lo, hi = max(0, i - 8), min(n, i + 9)
        neigh = [vals[j] for j in range(lo, hi) if j != i]
        med = statistics.median(neigh) if neigh else 0.0
        is_peak = s >= max(vals[i - 1], vals[i + 1] if i + 1 < n else 0)
        if s >= hard or (is_peak and s >= ratio * max(med, 0.01)):
            cand.append((times[i], s))
    cuts = []
    for t, s in sorted(cand, key=lambda x: -x[1]):
        if t < 0.1 or t > duration - 0.1:
            continue
        if all(abs(t - c[0]) >= min_gap for c in cuts):
            cuts.append((t, s))
    return sorted(cuts)


def activity_windows(scores: list, cuts: list, duration: float, win: float = 0.5) -> list:
    nwin = max(1, math.ceil(duration / win))
    buckets = [[] for _ in range(nwin)]
    cut_ts = [c[0] for c in cuts]
    for t, s in scores:
        if any(abs(t - c) < 0.07 for c in cut_ts):
            continue
        buckets[min(nwin - 1, int(t / win))].append(s)
    res = []
    for k, b in enumerate(buckets):
        res.append({"start": round(k * win, 2), "end": round(min(duration, (k + 1) * win), 2),
                    "mean_change": round(statistics.fmean(b), 4) if b else 0.0,
                    "max_change": round(max(b), 4) if b else 0.0,
                    "has_cut": any(k * win <= c < (k + 1) * win for c in cut_ts)})
    return res


def activity_peaks(windows: list, k: int = 6) -> list:
    vals = [w["mean_change"] for w in windows]
    if not vals:
        return []
    med = statistics.median(vals)
    mad = statistics.median([abs(v - med) for v in vals]) or 0.001
    thr = med + 2.0 * mad
    peaks = []
    for i, w in enumerate(windows):
        if w["has_cut"]:
            continue
        left = vals[i - 1] if i > 0 else -1
        right = vals[i + 1] if i + 1 < len(vals) else -1
        if vals[i] >= thr and vals[i] >= left and vals[i] >= right:
            peaks.append({"t": round((w["start"] + w["end"]) / 2, 2), "mean_change": vals[i],
                          "z": round((vals[i] - med) / mad, 2)})
    peaks.sort(key=lambda p: -p["mean_change"])
    chosen = []
    for p in peaks:
        if all(abs(p["t"] - c["t"]) >= 1.0 for c in chosen):
            chosen.append(p)
        if len(chosen) >= k:
            break
    return sorted(chosen, key=lambda p: p["t"])


def densify_plan(cuts: list, peaks: list, dur: float, native_fps: float, base_fps: float,
                 dense_fps: float = 10.0, hook_dense_s: float = 1.0) -> list:
    """Adaptive extra timestamps: last/first frame around every cut, dense_fps around motion peaks
    and over the first hook_dense_s seconds. Skips points already on the baseline grid."""
    eps = 1.0 / max(native_fps, 1.0)
    tmax = max(0.0, dur - 1.5 * eps)
    want = []
    for i, (ct, _) in enumerate(cuts):
        want.append((ct - 0.75 * eps, f"c{i + 1:02d}<", "pre_cut"))
        want.append((ct + 0.25 * eps, f"c{i + 1:02d}>", "post_cut"))
    for i, p in enumerate(peaks):
        for k in range(-5, 6):
            want.append((p["t"] + k / dense_fps, f"m{i + 1}", "peak"))
    for k in range(int(round(hook_dense_s * dense_fps))):
        want.append((k / dense_fps, "hook", "hook"))
    grid = 1.0 / base_fps
    picked = []
    for t, tag, why in sorted(want):
        t = min(tmax, max(0.0, t))
        on_grid = abs(t / grid - round(t / grid)) * grid < min(0.03, 0.4 * eps + 0.01)
        if on_grid and why not in ("pre_cut", "post_cut"):
            continue
        if any(abs(t - q[0]) < 0.45 / dense_fps and why == q[2] for q in picked):
            continue
        picked.append((round(t, 3), tag, why))
    return picked


def audio_analysis(video: str, info: dict, workdir: Path) -> dict:
    res = {"has_audio": bool(info.get("has_audio"))}
    if not info.get("has_audio"):
        return res
    ff = find_tool("ffmpeg")
    workdir.mkdir(parents=True, exist_ok=True)
    wav = workdir / "audio-16k.wav"
    run([ff, "-hide_banner", "-loglevel", "error", "-nostdin", "-y", "-i", video, "-map", "0:a:0",
         "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(wav)], timeout=1800)
    res["wav_16k"] = str(wav) if wav.exists() else None
    cp = run([ff, "-hide_banner", "-nostdin", "-i", video, "-map", "0:a:0", "-af", "ebur128=peak=true",
              "-f", "null", "-"], timeout=1800)
    summ = cp.stderr[cp.stderr.rfind("Summary:"):] if "Summary:" in cp.stderr else ""
    for key, pat in (("integrated_lufs", r"I:\s*(-?[0-9.]+)\s*LUFS"), ("lra_lu", r"LRA:\s*(-?[0-9.]+)\s*LU"),
                     ("true_peak_dbfs", r"Peak:\s*(-?[0-9.]+)\s*dBFS")):
        m = re.search(pat, summ)
        res[key] = float(m.group(1)) if m else None
    cp = run([ff, "-hide_banner", "-nostdin", "-i", video, "-map", "0:a:0",
              "-af", "silencedetect=n=-35dB:d=0.4", "-f", "null", "-"], timeout=1800)
    sil, start = [], None
    for line in cp.stderr.splitlines():
        m = re.search(r"silence_start:\s*(-?[0-9.]+)", line)
        if m:
            start = max(0.0, float(m.group(1)))
        m = re.search(r"silence_end:\s*([0-9.]+)", line)
        if m and start is not None:
            sil.append({"start": round(start, 2), "end": round(float(m.group(1)), 2)})
            start = None
    if start is not None:
        sil.append({"start": round(start, 2), "end": info.get("duration_s")})
    res["silences"] = sil
    fname = "rms.txt"
    (workdir / fname).unlink(missing_ok=True)
    run([ff, "-hide_banner", "-loglevel", "error", "-nostdin", "-i", video, "-map", "0:a:0", "-ac", "1",
         "-ar", "16000", "-af",
         f"asetnsamples=n=8000:p=0,astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level:file={fname}",
         "-f", "null", "-"], cwd=str(workdir), timeout=1800)
    curve, cur = [], None
    if (workdir / fname).exists():
        for line in (workdir / fname).read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.search(r"pts_time:([0-9.]+)", line)
            if m:
                cur = float(m.group(1))
                continue
            m = re.search(r"RMS_level=(-?[0-9.]+|-inf)", line)
            if m and cur is not None:
                v = m.group(1)
                curve.append({"t": round(cur, 2), "rms_db": -120.0 if v == "-inf" else round(float(v), 1)})
                cur = None
    res["rms_per_0.5s"] = curve
    if res.get("integrated_lufs") is not None and res["integrated_lufs"] < -50:
        res["note"] = "audio stream present but near-silent"
    return res


def transcribe(wav: str, workdir: Path, model_name: str = "small", language: str = "auto") -> dict:
    res = {"engine": None, "has_speech": False, "segments": []}
    try:
        from faster_whisper import WhisperModel  # type: ignore
        model = None
        for name in [model_name] + [m for m in ("small", "base", "tiny") if m != model_name]:
            try:
                model = WhisperModel(name, device="cpu", compute_type="int8", local_files_only=True)
                res["model"] = name
                break
            except Exception:
                continue
        if model is None:
            raise RuntimeError("no cached faster-whisper model")
        segs, info = model.transcribe(wav, language=None if language == "auto" else language,
                                      word_timestamps=True, vad_filter=True, beam_size=5)
        for s in segs:
            res["segments"].append({
                "start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip(),
                "words": [{"w": w.word.strip(), "s": round(w.start, 2), "e": round(w.end, 2),
                           "p": round(w.probability, 2)} for w in (s.words or [])]})
        res.update({"engine": "faster-whisper", "language": info.language,
                    "language_probability": round(info.language_probability, 3)})
    except Exception as e:  # fallback: ffmpeg's built-in whisper.cpp filter
        res["faster_whisper_error"] = str(e)[:300]
        model_file = None
        for cand in ("ggml-base.en.bin", "ggml-small.bin", "ggml-base.bin", "ggml-tiny.en.bin"):
            p = Path.home() / ".cache" / "whisper-cpp" / cand
            if p.exists():
                model_file = p
                break
        if model_file:
            esc = str(model_file).replace("\\", "/").replace(":", "\\:")
            srt = "whisper-ffmpeg.srt"
            run([find_tool("ffmpeg"), "-hide_banner", "-loglevel", "error", "-nostdin", "-i", wav, "-af",
                 f"whisper=model='{esc}':language=auto:queue=10:use_gpu=false:format=srt:destination={srt}",
                 "-f", "null", "-"], cwd=str(workdir), timeout=3600)
            p = workdir / srt
            if p.exists():
                for b in re.split(r"\n\s*\n", p.read_text(encoding="utf-8", errors="replace").strip()):
                    m = re.search(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)\s*\n(.*)", b, re.S)
                    if m:
                        g = [int(x) for x in m.groups()[:8]]
                        st = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
                        en = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
                        res["segments"].append({"start": round(st, 2), "end": round(en, 2),
                                                "text": " ".join(m.group(9).split()), "words": []})
                res.update({"engine": "ffmpeg-whisper", "model": model_file.name})
    words = sum(len(s["text"].split()) for s in res["segments"])
    res["has_speech"] = words >= 2
    res["n_words"] = words
    speech = sum(s["end"] - s["start"] for s in res["segments"])
    res["speech_seconds"] = round(speech, 2)
    res["wpm_speech_only"] = round(words / (speech / 60), 1) if speech > 1 else None
    return res


_OCR = None
_OCR_LOCK = threading.Lock()


def ocr_frames(frames: list) -> dict:
    """RapidOCR over frame files -> detections + spans with a coarse kind hint. Thread-safe."""
    with _OCR_LOCK:
        return _ocr_frames_locked(frames)


def _ocr_frames_locked(frames: list) -> dict:
    global _OCR
    try:
        if _OCR is None:
            from rapidocr_onnxruntime import RapidOCR  # type: ignore
            _OCR = RapidOCR()
        from PIL import Image
        import numpy as np
    except Exception as e:
        return {"available": False, "error": str(e)[:200]}
    dets, n_frames = [], 0
    for fr in frames:
        if not fr.get("ok", True) or not Path(fr["file"]).exists():
            continue
        try:
            with Image.open(fr["file"]) as im:
                im = im.convert("RGB")
                im.thumbnail((736, 736))          # overlay text stays legible; detection is 2x faster
                arr = np.asarray(im)[:, :, ::-1].copy()   # RGB -> BGR as RapidOCR expects
                height = im.height
            result, _ = _OCR(arr)
        except Exception:
            continue
        n_frames += 1
        for box, text, score in (result or []):
            if score < 0.6 or not text.strip():
                continue
            ys = [p[1] for p in box]
            dets.append({"t": fr["t"], "text": text.strip(), "score": round(float(score), 2),
                         "y_rel": round(sum(ys) / 4 / max(1, height), 3)})
    # many different texts at one height over time = caption/subtitle track;
    # the same text in most scanned frames = persistent overlay (title, handle, watermark).
    bands = {}
    for d in dets:
        bands.setdefault(round(d["y_rel"] / 0.08), []).append(d)
    band_kind = {}
    for b, ds in bands.items():
        texts = {re.sub(r"\W+", "", d["text"].lower()) for d in ds}
        if len(texts) >= 3 and len({d["t"] for d in ds}) >= 3:
            band_kind[b] = "caption/subtitle track"
    spans = {}
    for d in dets:
        key = re.sub(r"\W+", "", d["text"].lower())
        if len(key) < 2:
            continue
        sp = spans.setdefault(key, {"text": d["text"], "first_t": d["t"], "last_t": d["t"], "hits": 0,
                                    "y_rel": d["y_rel"], "band": round(d["y_rel"] / 0.08)})
        sp["first_t"], sp["last_t"] = min(sp["first_t"], d["t"]), max(sp["last_t"], d["t"])
        sp["hits"] += 1
    for sp in spans.values():
        tx = sp["text"]
        if tx.startswith("@") or re.search(r"@\w{2,}", tx):
            kind = "handle/username"
        elif tx.startswith("#"):
            kind = "hashtag"
        elif re.search(r"(www\.|https?:|\.com\b|\.co\b|\.io\b)", tx, re.I):
            kind = "url"
        elif n_frames >= 4 and sp["hits"] >= max(3, 0.6 * n_frames):
            kind = "persistent overlay (title, handle, watermark or fixed label)"
        elif sp["band"] in band_kind:
            kind = band_kind[sp["band"]]
        elif len(tx.split()) >= 3:
            kind = "caption/overlay-like"
        else:
            kind = "short text (logo, product label, UI or sign?)"
        sp["kind_hint"] = kind
        # one-frame, very short detections are usually OCR noise on texture; keep but flag them
        sp["likely_noise"] = sp["hits"] == 1 and len(re.sub(r"\W+", "", tx)) <= 3
    return {"available": True, "frames_scanned": n_frames, "detections": dets,
            "caption_bands_y_rel": sorted(round(b * 0.08, 2) for b in band_kind),
            "spans": sorted(spans.values(), key=lambda s: (s["first_t"], -s["hits"]))}


def loop_similarity(first: str, last: str) -> float | None:
    try:
        from PIL import Image
        import numpy as np
        with Image.open(first) as a, Image.open(last) as b:
            da = np.asarray(a.convert("L").resize((64, 64)), dtype="float32")
            db = np.asarray(b.convert("L").resize((64, 64)), dtype="float32")
            return round(1.0 - float(np.mean(np.abs(da - db))) / 255.0, 3)
    except Exception:
        return None


def second_timeline(dur: float, shots: list, cuts: list, peaks: list, statics: list, aud: dict,
                    trans: dict, ocr: dict) -> list:
    """One row per second: the audio-visual sequence read together."""
    n = max(1, math.ceil(dur))
    rows = [{"sec": s, "shot": None, "events": [], "words": [], "rms_db": None, "text": []} for s in range(n)]
    for s in range(n):
        mid = min(dur - 1e-3, s + 0.5)
        rows[s]["shot"] = next((x["shot"] for x in shots if x["start"] <= mid < x["end"]), shots[-1]["shot"] if shots else 1)
    for ct, _ in cuts:
        rows[min(n - 1, int(ct))]["events"].append(f"CUT {ct:.2f}")
    for p in peaks:
        rows[min(n - 1, int(p["t"]))]["events"].append(f"motion peak {p['t']:.2f}")
    for st in statics:
        for s in range(int(st["start"]), min(n, int(st["end"]) + 1)):
            if "static" not in rows[s]["events"]:
                rows[s]["events"].append("static")
    for sil in aud.get("silences") or []:
        a, b = sil["start"], sil["end"] if sil["end"] is not None else dur
        for s in range(int(a), min(n, int(b) + 1)):
            if "silence" not in rows[s]["events"]:
                rows[s]["events"].append("silence")
    for c in aud.get("rms_per_0.5s") or []:
        s = min(n - 1, int(c["t"]))
        rows[s]["rms_db"] = c["rms_db"] if rows[s]["rms_db"] is None else max(rows[s]["rms_db"], c["rms_db"])
    for seg in trans.get("segments") or []:
        if seg.get("words"):
            for w in seg["words"]:
                rows[min(n - 1, int(w["s"]))]["words"].append(w["w"])
        else:
            rows[min(n - 1, int(seg["start"]))]["words"].append(seg["text"])
    for d in (ocr.get("detections") or []) if ocr.get("available") else []:
        row = rows[min(n - 1, int(d["t"]))]
        if d["text"] not in row["text"]:
            row["text"].append(d["text"])
    return rows


# --------------------------------------------------------------------------- prep-video

def prep_video(video: str, odir: Path, vid: str = "V", base_fps: float = 5.0, dense_fps: float = 10.0,
               static_threshold: float = 2.5, whisper_model: str = "small", language: str = "auto",
               do_transcript: bool = True, do_ocr: bool = True, ocr_budget: int = 12,
               max_frames: int = 1800, hook_s: float = 3.0) -> dict:
    t0 = time.time()
    odir.mkdir(parents=True, exist_ok=True)
    for stale in ("frames", "sheets", "_work"):
        shutil.rmtree(odir / stale, ignore_errors=True)
    info = media_summary(video)
    if not info.get("has_video"):
        raise RuntimeError("no video stream")
    dur = info["duration_s"] or 0.0
    fps = info.get("fps") or 24.0
    write_json(odir / "probe.json", info)
    timings = {}

    # structure: scene-change score per native frame -> cuts, shots, pacing, activity
    t = time.time()
    scores = scene_scores(video, odir / "_work")
    cuts = detect_cuts(scores, dur)
    bounds = [0.0] + [c[0] for c in cuts] + [dur]
    shots = [{"shot": i + 1, "start": round(bounds[i], 3), "end": round(bounds[i + 1], 3),
              "dur": round(bounds[i + 1] - bounds[i], 3)} for i in range(len(bounds) - 1)]
    lens = [s["dur"] for s in shots]
    pacing = {"shots": len(shots), "cuts": len(cuts),
              "median_shot_s": round(statistics.median(lens), 2) if lens else None,
              "mean_shot_s": round(statistics.fmean(lens), 2) if lens else None,
              "min_shot_s": round(min(lens), 2) if lens else None,
              "max_shot_s": round(max(lens), 2) if lens else None,
              "cuts_per_10s": round(len(cuts) / dur * 10, 2) if dur else None,
              "first_cut_s": round(cuts[0][0], 2) if cuts else None,
              "cuts_in_first_3s": sum(1 for c in cuts if c[0] <= hook_s)}
    windows = activity_windows(scores, cuts, dur)
    peaks = activity_peaks(windows, k=min(8, max(2, math.ceil(dur / 5))))
    write_json(odir / "cuts.json", {"detector": "ffmpeg select scene score on 192 px frames; cut = score>=0.30 "
                                                "or local peak >=4x neighbourhood median (>=0.14); NMS 0.25 s",
                                    "cuts": [{"t": round(c[0], 3), "score": round(c[1], 3)} for c in cuts],
                                    "shots": shots, "pacing": pacing})
    write_json(odir / "activity.json", {"window_s": 0.5, "windows": windows, "peaks": peaks})
    timings["structure"] = round(time.time() - t, 1)

    # frames: 5 fps baseline, static thinning, adaptive densification
    t = time.time()
    fr_dir = odir / "frames"
    base, eff_fps, fps_note = extract_baseline(video, base_fps, fr_dir / "base", dur, max_frames=max_frames)
    statics = thin_static(base, static_threshold)
    plan = densify_plan(cuts, peaks, dur, fps, eff_fps, dense_fps)
    extra = extract_many(video, [(tt, fr_dir / "extra" / f"x-{ts_name(tt)}.jpg", {"kind": "extra", "tag": tag, "why": why})
                                 for tt, tag, why in plan], max_side=720)
    shot_of = lambda tt: next((s["shot"] for s in shots if s["start"] <= tt < s["end"]), shots[-1]["shot"] if shots else 1)
    frames_all = [f for f in base if f.get("kept")] + [f for f in extra if f["ok"]]
    for f in frames_all:
        f["shot"] = shot_of(f["t"])
        f.setdefault("flags", [])
        if f.get("why") == "peak" or any(abs(f["t"] - p["t"]) <= 0.5 for p in peaks):
            f["flags"].append("peak")
    frames_all.sort(key=lambda f: (f["t"], f["kind"] != "base"))
    for ct, _ in cuts:
        nxt = next((f for f in frames_all if f["t"] >= ct - 1e-3), None)
        if nxt:
            nxt["flags"].append("after_cut")
    story = list(frames_all)
    for st in statics:                                     # static markers sit where the run starts
        story.append({"kind": "static", "start": st["start"], "end": st["end"], "dropped": st["dropped"],
                      "t": st["start"] - 1e-4})
    story.sort(key=lambda f: f["t"])
    timings["frames"] = round(time.time() - t, 1)

    t = time.time()
    orient = info.get("orientation", "portrait")
    sheets = build_storyboard(story, odir / "sheets" / "storyboard", f"{vid} storyboard", orient)
    timings["sheets"] = round(time.time() - t, 1)

    # audio and speech, aligned to the same clock
    t = time.time()
    aud = audio_analysis(video, info, odir / "audio")
    write_json(odir / "audio.json", aud)
    trans = {"engine": None, "has_speech": False, "segments": [], "skipped": not do_transcript}
    if do_transcript and aud.get("wav_16k"):
        trans = transcribe(aud["wav_16k"], odir / "audio", whisper_model, language)
    write_json(odir / "transcript.json", trans)
    txt = [f"[{ts_label(s['start'])}-{ts_label(s['end'])}] {s['text']}" for s in trans.get("segments", [])]
    write_text(odir / "transcript.txt", "\n".join(txt) if txt else "No speech detected.")
    timings["audio"] = round(time.time() - t, 1)

    # on-screen text sample (feeds the no-visible-text rule and the source-artifact exclusion list)
    t = time.time()
    ocr = {"available": False, "skipped": not do_ocr}
    kept_base = [f for f in base if f.get("kept")]
    if do_ocr and ocr_budget > 0 and kept_base:
        step = max(1, math.ceil(len(kept_base) / ocr_budget))
        sample = kept_base[::step][:ocr_budget - 1] + kept_base[-1:]
        ocr = ocr_frames(sample)
    write_json(odir / "ocr.json", ocr)
    timings["ocr"] = round(time.time() - t, 1)

    loop = loop_similarity(base[0]["file"], base[-1]["file"]) if len(base) > 1 else None
    rows = second_timeline(dur, shots, cuts, peaks, statics, aud, trans, ocr)
    write_json(odir / "frames.json", {"baseline_fps": eff_fps, "baseline_note": fps_note,
                                      "static_threshold": static_threshold, "dense_fps": dense_fps,
                                      "static_runs": statics, "extra_frames": len([f for f in extra if f['ok']]),
                                      "frames": [{k: f.get(k) for k in ("t", "file", "kind", "shot", "flags", "why",
                                                                        "diff_prev_kept")} for f in frames_all]})
    first_word = None
    for s in trans.get("segments", []):
        first_word = s["words"][0]["s"] if s.get("words") else s["start"]
        break
    base_kept = len(kept_base)
    summary = {"id": vid, "video": video, "probe": info, "pacing": pacing, "peaks": peaks,
               "sampling": {"baseline_fps": round(eff_fps, 3), "baseline_frames": len(base),
                            "kept_after_static_thinning": base_kept,
                            "static_runs": len(statics), "extra_frames": len([f for f in extra if f["ok"]]),
                            "storyboard_cells": sum(s["cells"] for s in sheets), "note": fps_note},
               "hook": {"first_cut_s": pacing["first_cut_s"], "cuts_in_first_3s": pacing["cuts_in_first_3s"],
                        "speech_starts_s": first_word,
                        "mean_change_first_1s": round(statistics.fmean([w["mean_change"] for w in windows[:2]]), 4) if windows else None},
               "audio": {k: aud.get(k) for k in ("has_audio", "integrated_lufs", "lra_lu", "true_peak_dbfs", "note")},
               "speech": {k: trans.get(k) for k in ("engine", "model", "language", "has_speech", "n_words",
                                                    "speech_seconds", "wpm_speech_only")},
               "loop_similarity_first_last": loop,
               "ocr_spans": (ocr.get("spans") or [])[:40] if ocr.get("available") else None,
               "sheets": sheets, "timings_s": timings, "elapsed_s": round(time.time() - t0, 1)}
    write_json(odir / "video.json", summary)

    # human-readable companions
    T = [f"# {vid} — per-second timeline (sheets + this table = one continuous sequence)", "",
         "| sec | shot | events | speech in this second | audio max dB | on-screen text (OCR sample) |",
         "|---|---|---|---|---|---|"]
    for r in rows:
        T.append(f"| {r['sec']:>3} | S{r['shot']:02d} | {'; '.join(r['events'])} | {' '.join(r['words'])} | "
                 f"{'' if r['rms_db'] is None else r['rms_db']} | {' / '.join(r['text'])[:120]} |")
    write_text(odir / "timeline.md", "\n".join(T))

    L = [f"# {vid} — {Path(video).name}", "",
         f"- **Specs**: {dur:.2f} s · {info.get('display_width')}x{info.get('display_height')} ({info.get('aspect')}, "
         f"{orient}) · {fps} fps · audio {'yes' if info.get('has_audio') else 'no'}",
         f"- **Sampling**: baseline {eff_fps:g} fps ({len(base)} frames) → {base_kept} kept after static thinning "
         f"({len(statics)} static run(s)) + {summary['sampling']['extra_frames']} densified frames "
         f"(cuts, motion peaks, first second) = {summary['sampling']['storyboard_cells']} storyboard cells"
         + (f" — NOTE: {fps_note}" if fps_note else ""),
         f"- **Pacing** (measured): {pacing['shots']} shots, {pacing['cuts']} cuts, median shot {pacing['median_shot_s']} s, "
         f"{pacing['cuts_per_10s']} cuts/10 s, first cut at {pacing['first_cut_s']} s, {pacing['cuts_in_first_3s']} cut(s) in the first 3 s",
         f"- **Speech**: {trans.get('n_words', 0)} words via {trans.get('engine')} ({trans.get('language')}); "
         f"speech starts at {first_word} s; {trans.get('wpm_speech_only')} wpm (speech-only)",
         f"- **Audio**: {aud.get('integrated_lufs')} LUFS integrated, LRA {aud.get('lra_lu')}, "
         f"{len(aud.get('silences') or [])} silence span(s) ≥0.4 s{(' — ' + aud['note']) if aud.get('note') else ''}",
         f"- **Loop similarity** (first vs last frame, 0–1): {loop}",
         f"- **Motion peaks** (non-cut visual change): " + (", ".join(f"{p['t']}s (z {p['z']})" for p in peaks) or "none"),
         f"- **Static runs thinned**: " + (", ".join(f"{s['start']:.2f}–{s['end']:.2f}s ({s['dropped']})" for s in statics) or "none"),
         "", "## Storyboard sheets (read in order, with timeline.md open)", ""]
    L += [f"- `{s['sheet']}` — {ts_label(s['start'])}–{ts_label(s['end'])} ({s['cells']} cells)" for s in sheets]
    L += ["", "## Shots (heuristic cut detector — confirm on the storyboard)", "",
          "| shot | start | end | dur |", "|---|---|---|---|"]
    L += [f"| S{s['shot']:02d} | {s['start']:.2f} | {s['end']:.2f} | {s['dur']:.2f} |" for s in shots[:120]]
    L += ["", "## Transcript (machine ASR — evidence to verify, not verbatim truth)", ""]
    L += txt[:150] or ["No speech detected."]
    if ocr.get("available"):
        L += ["", f"## On-screen text sample (OCR on {ocr.get('frames_scanned')} frames)", ""]
        for sp in (ocr.get("spans") or [])[:40]:
            L.append(f"- {ts_label(sp['first_t'])}–{ts_label(sp['last_t'])} · {sp['kind_hint']} · \"{sp['text']}\" ×{sp['hits']}")
        if not ocr.get("spans"):
            L.append("- none detected")
    L += ["", f"Machine data in `{odir}`: video.json, frames.json, cuts.json, activity.json, audio.json, "
              f"transcript.json, ocr.json, timeline.md · densify on demand: "
              f"`atp.py frames \"{video}\" --out <dir> --range a-b --fps 15 --sheet` · elapsed {summary['elapsed_s']} s"]
    write_text(odir / "video.md", "\n".join(L))
    shutil.rmtree(odir / "_work", ignore_errors=True)
    return summary


def _media_kwargs(a) -> dict:
    return dict(base_fps=a.fps, dense_fps=a.dense_fps, static_threshold=a.static_threshold,
                whisper_model=a.whisper_model, language=a.language, do_transcript=not a.no_transcript,
                do_ocr=not a.no_ocr, ocr_budget=a.ocr_frames, max_frames=a.max_frames)


def cmd_prep_video(a):
    try:
        s = prep_video(a.video, Path(a.out), a.id or "V", **_media_kwargs(a))
    except Exception as e:
        fail(f"{type(e).__name__}: {e}")
    out({"ok": True, "summary_md": str(Path(a.out) / "video.md"), "timeline_md": str(Path(a.out) / "timeline.md"),
         "sheets": s["sheets"], "sampling": s["sampling"], "elapsed_s": s["elapsed_s"]})


# --------------------------------------------------------------------------- other media

def prep_image(path: str, dest: Path, max_side: int = 1280) -> dict:
    from PIL import Image, ImageOps
    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im)
        info = {"path": path, "width": im.width, "height": im.height, "mode": im.mode,
                "aspect": nearest_aspect(im.width, im.height),
                "has_alpha": im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)}
        prev = im.convert("RGB")
        prev.thumbnail((max_side, max_side))
        prev.save(dest, quality=88)
    info["preview"] = str(dest)
    return info


def cmd_prep_image(a):
    try:
        out({"ok": True, **prep_image(a.image, Path(a.out), a.max_side)})
    except Exception as e:
        fail(str(e))


def _xml_text(data: bytes, para_tag: str, text_tag: str) -> str:
    s = data.decode("utf-8", errors="replace")
    lines = []
    for p in re.split(rf"</{para_tag}>", s):
        texts = re.findall(rf"<{text_tag}(?:\s[^>]*)?>(.*?)</{text_tag}>", p, re.S)
        line = html.unescape("".join(texts)).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def doc_text(path: str) -> str:
    p = Path(path)
    ext = p.suffix.lower()
    if ext in (".html", ".htm", ".xml"):
        raw = p.read_text(encoding="utf-8", errors="replace")
        raw = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
        return html.unescape(re.sub(r"<[^>]+>", " ", raw))
    if ext in TEXT_EXT:
        return p.read_text(encoding="utf-8", errors="replace")
    if ext == ".docx":
        with zipfile.ZipFile(p) as z:
            parts = [n for n in z.namelist() if re.match(r"word/(document|header\d*|footer\d*|footnotes)\.xml$", n)]
            return "\n\n".join(_xml_text(z.read(n), "w:p", "w:t") for n in sorted(parts))
    if ext == ".pptx":
        with zipfile.ZipFile(p) as z:
            slides = sorted((n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)),
                            key=lambda n: int(re.findall(r"\d+", n)[-1]))
            notes = {int(re.findall(r"\d+", n)[-1]): n for n in z.namelist()
                     if re.match(r"ppt/notesSlides/notesSlide\d+\.xml$", n)}
            outp = []
            for n in slides:
                k = int(re.findall(r"\d+", n)[-1])
                outp.append(f"--- slide {k} ---\n" + _xml_text(z.read(n), "a:p", "a:t"))
                if k in notes:
                    outp.append("[notes] " + _xml_text(z.read(notes[k]), "a:p", "a:t"))
            return "\n".join(outp)
    if ext == ".xlsx":
        with zipfile.ZipFile(p) as z:
            shared = []
            if "xl/sharedStrings.xml" in z.namelist():
                s = z.read("xl/sharedStrings.xml").decode("utf-8", errors="replace")
                for si in re.findall(r"<si>(.*?)</si>", s, re.S):
                    shared.append(html.unescape("".join(re.findall(r"<t[^>]*>(.*?)</t>", si, re.S))))
            outp = []
            sheets = sorted((n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n)),
                            key=lambda n: int(re.findall(r"\d+", n)[-1]))
            for n in sheets:
                outp.append(f"--- {Path(n).stem} ---")
                s = z.read(n).decode("utf-8", errors="replace")
                for row in re.findall(r"<row[^>]*>(.*?)</row>", s, re.S):
                    vals = []
                    for attrs, body in re.findall(r"<c ([^>]*)>(.*?)</c>", row, re.S):
                        v = re.search(r"<v>(.*?)</v>", body, re.S)
                        tt = re.search(r't="(\w+)"', attrs)
                        if tt and tt.group(1) == "s" and v:
                            idx = int(v.group(1))
                            vals.append(shared[idx] if idx < len(shared) else "")
                        elif tt and tt.group(1) == "inlineStr":
                            vals.append(html.unescape("".join(re.findall(r"<t[^>]*>(.*?)</t>", body, re.S))))
                        else:
                            vals.append(html.unescape(v.group(1)) if v else "")
                    if any(x.strip() for x in vals):
                        outp.append("\t".join(vals))
            return "\n".join(outp)
    if ext == ".pdf":
        return "[PDF — read it directly with the Read tool (pages parameter for long files).]"
    return "[unsupported format for text extraction]"


def cmd_doc_text(a):
    try:
        text = doc_text(a.file)
    except Exception as e:
        fail(str(e))
    if a.out:
        write_text(Path(a.out), text)
    out({"ok": True, "chars": len(text), "out": a.out, **({} if a.out else {"text": text[:20000]})})


# --------------------------------------------------------------------------- run management

def cmd_new_run(a):
    root = Path(a.runs_root or cfg_get("runs_root") or (ATP_HOME / "runs")).expanduser()
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    sources = [str(Path(s).expanduser().resolve()) for s in (a.source or [])]
    assets = [str(Path(s).expanduser().resolve()) for s in (a.assets or [])]
    examples = [str(Path(s).expanduser().resolve()) for s in (a.examples or [])]
    missing = [p for p in sources + assets + examples if not Path(p).exists()]
    if missing:
        fail("path(s) not found: " + "; ".join(missing), 2)
    slug = slugify(a.slug or (Path(sources[0]).stem if sources else a.mode))
    run_dir = root / f"{stamp}-{slug}"
    for sub in ("00-inventory", "10-media", "20-analysis", "30-assets", "40-briefs", "50-requests",
                "60-outputs", "logs"):
        (run_dir / sub).mkdir(parents=True, exist_ok=True)
    state = {"run_id": run_dir.name, "mode": a.mode,
             "source": sources[0] if len(sources) == 1 else sources,   # references folder (analyze) / videos (edit)
             "assets_paths": assets,        # user-supplied client assets (analyze: whole project, given up front)
             "examples_paths": examples,    # optional: the user's own finished videos (study only, never inputs)
             "created": now_iso(), "updated": now_iso(), "stage": "created", "next_step": "inventory",
             "model": None, "requested_videos": None, "directions": [], "assets": {}, "videos": [], "notes": []}
    write_json(run_dir / "state.json", state)
    out({"ok": True, "run_dir": str(run_dir), "state": str(run_dir / "state.json"),
         "sources": sources, "assets_paths": assets, "examples_paths": examples})


def _set_dotted(d: dict, key: str, value):
    parts = key.split(".")
    for p in parts[:-1]:
        d = d.setdefault(p, {})
    d[parts[-1]] = value


def _get_dotted(d, key: str):
    for p in key.split("."):
        if isinstance(d, dict) and p in d:
            d = d[p]
        elif isinstance(d, list) and p.isdigit() and int(p) < len(d):
            d = d[int(p)]
        else:
            return None
    return d


class FileLock:
    """Cross-process lock (O_EXCL lock file). Production agents run in parallel (one per video), so every
    read-modify-write of a shared file (state.json, CapCut's store index) holds one of these."""

    def __init__(self, path, timeout: float = 120.0, stale: float = 600.0):
        self.path, self.timeout, self.stale, self.fd = Path(path), timeout, stale, None

    def __enter__(self):
        import time
        t0 = time.time()
        while True:
            try:
                self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(self.fd, f"{os.getpid()} {now_iso()}".encode())
                return self
            except FileExistsError:
                try:
                    if time.time() - self.path.stat().st_mtime > self.stale:
                        self.path.unlink()          # left behind by a killed process
                        continue
                except FileNotFoundError:
                    continue
                if time.time() - t0 > self.timeout:
                    fail(f"lock busy: {self.path} (another agent is writing; retry)", 4)
                time.sleep(0.1)

    def __exit__(self, *exc):
        try:
            os.close(self.fd)
        finally:
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass


def cmd_state(a):
    p = Path(a.run) / "state.json"
    if not p.exists():
        fail(f"state.json not found in {a.run}", 2)
    if a.action == "get":
        st = json.loads(p.read_text(encoding="utf-8"))
        out({"ok": True, "value": _get_dotted(st, a.pairs[0]) if a.pairs else st})
    with FileLock(p.with_name("state.json.lock")):
        st = json.loads(p.read_text(encoding="utf-8"))
        for pair in a.pairs:
            if "=" not in pair:
                fail(f"expected key=value, got {pair!r}", 2)
            k, v = pair.split("=", 1)
            try:
                val = json.loads(v)
            except Exception:
                val = v
            if a.action == "append":
                cur = _get_dotted(st, k)
                if not isinstance(cur, list):
                    cur = []
                    _set_dotted(st, k, cur)
                cur.append(val)
            else:
                _set_dotted(st, k, val)
        st["updated"] = now_iso()
        write_json(p, st)
    out({"ok": True, "updated": [x.split("=", 1)[0] for x in a.pairs]})


def _collect_files(paths: list, run_dir, max_depth) -> list:
    """(file, base) for every file under the given files/folders, in stable order, no duplicates."""
    found, seen = [], set()
    for raw in paths:
        p = Path(raw).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"not found: {p}")
        if p.is_file():
            if p not in seen:
                seen.add(p)
                found.append((p, p.parent))
            continue
        base_depth = len(p.parts)
        for root, dirs, fnames in os.walk(p):
            rp = Path(root)
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")
                             and not (rp / d / FINAL_MARKER).exists()          # our own final/ folder
                             and not (run_dir and (rp / d).resolve() == run_dir))
            if max_depth is not None and len(rp.parts) - base_depth >= max_depth:
                dirs[:] = []
            for fn in sorted(fnames):
                if fn.startswith(".") or fn.lower() in ("thumbs.db", "desktop.ini"):
                    continue
                f = rp / fn
                if f not in seen:
                    seen.add(f)
                    found.append((f, p))
    return found


def _mark_final_dir(d: Path) -> None:
    marker = d / FINAL_MARKER
    if not marker.exists():
        marker.write_text("Created by /analyze-then-pick: approved results. This folder is skipped when the "
                          "parent folder is scanned again.\n", encoding="utf-8")
        if sys.platform.startswith("win"):
            try:
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(str(marker), 0x02)   # FILE_ATTRIBUTE_HIDDEN
            except Exception:
                pass


def _asset_hints(rel: str) -> list:
    low = rel.lower().replace("\\", "/")
    return sorted({hint for pat, hint in ASSET_HINTS if re.search(pat, low)})


def cmd_inventory(a):
    """--as references : Analyze Mode reference material (everything is REFERENCE material, never a client asset)
       --as sources    : Edit Mode — only videos are edit sources; every other file is ignored
       --as assets     : user-supplied client assets (the ONLY source of client assets), per --scope
       --as examples   : the user's own finished videos: how THEY place, use, continue and blend their products.
                         Study material only (never uploaded, recreated, cut in or used as assets). May be empty."""
    run_dir = Path(a.run).resolve() if a.run else None
    try:
        files = _collect_files(a.paths, run_dir, a.max_depth)
    except FileNotFoundError as e:
        fail(str(e), 2)
    role = a.role
    if role in ("assets", "examples"):
        letter = "A" if role == "assets" else "E"
        prefix = {k: letter for k in ("video", "image", "audio", "pdf", "office", "text", "font", "vector", "other")}
    else:
        prefix = {"video": "V", "image": "I", "audio": "S", "pdf": "D", "office": "D", "text": "D",
                  "font": "F", "vector": "G", "other": "X"}
    seq = {k: 0 for k in set(prefix.values())}
    items, seen = [], {}
    multi_base = len({str(b) for _, b in files}) > 1
    for f, base in files:
        kind = classify(f)
        if role == "sources" and kind != "video":
            items.append({"id": "-", "kind": kind, "path": str(f), "rel": f.name, "ignored": True,
                          "reason": "Edit Mode processes only videos; name this file explicitly if it is an asset"})
            continue
        pre = prefix[kind]
        seq[pre] += 1
        rel = str(f.relative_to(base))
        if multi_base:
            rel = str(Path(base.name) / rel)
        item = {"id": f"{pre}{seq[pre]:02d}", "kind": kind, "path": str(f), "rel": rel,
                "ext": f.suffix.lower(), "size_bytes": f.stat().st_size,
                "folder": str(Path(rel).parent) if str(Path(rel).parent) != "." else "."}
        if role == "assets":
            item["group"] = item["folder"]           # sub-folders usually separate products / characters / sets
            item["name_hints"] = _asset_hints(rel)   # hints only — roles are confirmed by viewing
        try:
            item["hash"] = quick_hash(f)
            if item["hash"] in seen:
                item["duplicate_of"] = seen[item["hash"]]
            else:
                seen[item["hash"]] = item["id"]
        except Exception:
            pass
        if kind in ("video", "audio"):
            try:
                s = media_summary(f)
                item.update({k: s.get(k) for k in ("duration_s", "display_width", "display_height", "fps",
                                                   "aspect", "orientation", "has_audio", "codec")})
            except Exception as e:
                item["probe_error"] = str(e)[:200]
        elif kind == "image":
            try:
                from PIL import Image, ImageOps
                with Image.open(f) as im:
                    im = ImageOps.exif_transpose(im)
                    item.update({"display_width": im.width, "display_height": im.height,
                                 "aspect": nearest_aspect(im.width, im.height), "mode": im.mode})
            except Exception as e:
                item["probe_error"] = str(e)[:200]
        items.append(item)
    used = [it for it in items if not it.get("ignored")]
    by_kind = {}
    for it in used:
        by_kind.setdefault(it["kind"], []).append(it)
    titles = {"references": "Reference material (analysis only — never client assets)",
              "sources": "Edit sources (videos only)",
              "assets": f"User-supplied client assets — scope '{a.scope or 'project'}'",
              "examples": "Examples: your own finished videos (study only — never generation inputs, never client assets)"}
    inv = {"role": role, "scope": a.scope or ("project" if role == "assets" else None),
           "inputs": [str(Path(p).expanduser().resolve()) for p in a.paths], "created": now_iso(),
           "counts": {k: len(v) for k, v in by_kind.items()},
           "total_video_seconds": round(sum(i.get("duration_s") or 0 for i in by_kind.get("video", [])), 1),
           "items": items}
    lines = [f"# {titles[role]}", "", "Inputs: " + "; ".join(f"`{p}`" for p in inv["inputs"]), "",
             f"Created {inv['created']}. Counts: " + ", ".join(f"{k} {v}" for k, v in sorted(inv["counts"].items())) +
             f". Total video: {inv['total_video_seconds']} s.", ""]
    for kind in ("video", "image", "audio", "pdf", "office", "text", "font", "vector", "other"):
        rows = by_kind.get(kind, [])
        if not rows:
            continue
        extra_col = " group | name hints |" if role == "assets" else ""
        lines += [f"## {kind} ({len(rows)})", "", "| id | file | details |" + extra_col,
                  "|---|---|---|" + ("---|---|" if role == "assets" else "")]
        for it in rows:
            if kind == "video":
                det = (f"{it.get('duration_s')} s, {it.get('display_width')}x{it.get('display_height')} "
                       f"({it.get('aspect')}), {it.get('fps')} fps, audio {'yes' if it.get('has_audio') else 'no'}")
            elif kind == "image":
                det = f"{it.get('display_width')}x{it.get('display_height')} ({it.get('aspect')})"
            elif kind == "audio":
                det = f"{it.get('duration_s')} s"
            else:
                det = f"{round(it['size_bytes'] / 1024, 1)} KB"
            if it.get("duplicate_of"):
                det += f" — duplicate of {it['duplicate_of']}"
            if it.get("probe_error"):
                det += f" — PROBE ERROR: {it['probe_error'][:80]}"
            row = f"| {it['id']} | `{it['rel']}` | {det} |"
            if role == "assets":
                row += f" {it.get('group')} | {', '.join(it.get('name_hints') or []) or '—'} |"
            lines.append(row)
        lines.append("")
    ignored = [it for it in items if it.get("ignored")]
    if ignored:
        lines += [f"## ignored ({len(ignored)})", ""] + [f"- `{it['path']}` ({it['kind']}): {it['reason']}" for it in ignored]
    if run_dir:
        if role == "assets":
            dest = run_dir / "30-assets" / (a.scope or "project")
            jp, mp = dest / "asset-inventory.json", dest / "asset-inventory.md"
        elif role == "examples":
            jp, mp = run_dir / "00-inventory" / "examples-inventory.json", run_dir / "00-inventory" / "examples-inventory.md"
        else:
            jp, mp = run_dir / "00-inventory" / "inventory.json", run_dir / "00-inventory" / "inventory.md"
        write_json(jp, inv)
        write_text(mp, "\n".join(lines))
    else:
        jp = mp = None
    out({"ok": True, "role": role, "counts": inv["counts"], "ignored": len(ignored),
         "total_video_seconds": inv["total_video_seconds"],
         "inventory_json": str(jp) if jp else None, "inventory_md": str(mp) if mp else None,
         **({} if run_dir else {"items": items})})


def cmd_prep_assets(a):
    """Previews, document text, font names and ONE labelled contact sheet of the user-supplied assets of
    a scope, so the command can see and classify exactly what the user provided (nothing else)."""
    run_dir = Path(a.run)
    scope = a.scope or "project"
    adir = run_dir / "30-assets" / scope
    inv_p = adir / "asset-inventory.json"
    if not inv_p.exists():
        fail(f"run `inventory --as assets --scope {scope}` first", 2)
    inv = json.loads(inv_p.read_text(encoding="utf-8"))
    sheet_items, lines, errors = [], [f"# Asset previews — scope '{scope}'", ""], []
    for it in inv["items"]:
        if it.get("ignored"):
            continue
        aid, kind, name = it["id"], it["kind"], it["rel"].replace("\\", "/")
        if it.get("duplicate_of"):
            lines.append(f"- {aid} `{name}` — duplicate of {it['duplicate_of']} (skipped)")
            continue
        try:
            if kind == "image":
                info = prep_image(it["path"], adir / "previews" / f"{aid}.jpg")
                sheet_items.append({"t": 0.0, "file": info["preview"], "ok": True, "kind": "base",
                                    "label": f"{aid} {name}"})
                lines.append(f"- {aid} image `{name}` {info['width']}x{info['height']}"
                             f"{' (alpha)' if info['has_alpha'] else ''} → `{info['preview']}`")
            elif kind == "video":
                s = media_summary(it["path"])
                d = s.get("duration_s") or 0
                marks = [0.0, d / 2, max(0.0, d - 0.2)]
                fr = extract_many(it["path"], [(t, adir / "previews" / f"{aid}-{ts_name(t)}.jpg",
                                                {"kind": "base", "label": f"{aid} {name} @{t:.1f}s"}) for t in marks], 720)
                sheet_items += [f for f in fr if f["ok"]]
                lines.append(f"- {aid} video `{name}` {d} s {s.get('display_width')}x{s.get('display_height')} "
                             f"(first/middle/last frames on the sheet; densify with `frames` if needed)")
            elif kind in ("text", "office"):
                dest = adir / "docs" / f"{aid}.txt"
                write_text(dest, doc_text(it["path"]))
                lines.append(f"- {aid} document `{name}` → `{dest}`")
            elif kind == "pdf":
                lines.append(f"- {aid} PDF `{name}` → read directly with the Read tool")
            elif kind == "font":
                fam = None
                try:
                    from PIL import ImageFont
                    fam = " ".join(ImageFont.truetype(it["path"], 20).getname())
                except Exception:
                    pass
                lines.append(f"- {aid} font `{name}` family: {fam or 'unknown'} → usable in captions as "
                             f"`\"font_file\": \"{it['path']}\"`")
            elif kind == "vector":
                lines.append(f"- {aid} vector `{name}` (not previewable here; ask for a PNG export if it must be "
                             f"shown to a model, or use it for post overlays)")
            elif kind == "audio":
                s = media_summary(it["path"])
                lines.append(f"- {aid} audio `{name}` {s.get('duration_s')} s (voice/music/sound reference)")
            else:
                lines.append(f"- {aid} other `{name}` — not processed")
        except Exception as e:
            errors.append({"id": aid, "error": str(e)[:200]})
            lines.append(f"- {aid} `{name}` ERROR: {str(e)[:160]}")
    sheets = build_storyboard(sheet_items, adir / "assets-sheet", f"Assets '{scope}'", "square", dense=False,
                              legend="user-supplied assets only | label = asset id + path", show_times=False)
    lines += ["", "## Contact sheets", ""] + [f"- `{s['sheet']}` ({s['cells']} cells)" for s in sheets]
    write_text(adir / "asset-previews.md", "\n".join(lines))
    out({"ok": not errors, "scope": scope, "sheets": sheets, "summary": str(adir / "asset-previews.md"),
         "errors": errors}, 0 if not errors else 1)


def cmd_prep_all(a):
    run_dir = Path(a.run)
    examples = a.inv_set == "examples"
    inv_p = run_dir / "00-inventory" / ("examples-inventory.json" if examples else "inventory.json")
    if not inv_p.exists():
        fail("run inventory first" + (" --as examples" if examples else ""), 2)
    inv = json.loads(inv_p.read_text(encoding="utf-8"))
    only = set(x.strip() for x in a.only.split(",")) if a.only else None
    media = run_dir / "10-media"
    kw = _media_kwargs(a)
    lines, errors, done = {}, [], []

    def do_item(it):
        if it.get("duplicate_of"):
            return f"- {it['id']} skipped (duplicate of {it['duplicate_of']})"
        if it["kind"] == "video":
            d = media / it["id"]
            if (d / "video.json").exists() and not a.redo:
                return f"- {it['id']} video — already prepared: `{d / 'video.md'}`"
            s = prep_video(it["path"], d, it["id"], **kw)
            done.append(it["id"])
            sm = s["sampling"]
            return (f"- {it['id']} video `{it['rel']}` → `{d / 'video.md'}` · {len(s['sheets'])} storyboard sheet(s), "
                    f"{sm['storyboard_cells']} cells ({sm['baseline_fps']} fps baseline) · {s['elapsed_s']} s")
        if it["kind"] == "image" and not a.skip_images:
            info = prep_image(it["path"], media / "images" / f"{it['id']}.jpg")
            done.append(it["id"])
            return (f"- {it['id']} image `{it['rel']}` → preview `{info['preview']}` "
                    f"({info['width']}x{info['height']}{', alpha' if info['has_alpha'] else ''})")
        if it["kind"] in ("text", "office"):
            dest = media / "docs" / f"{it['id']}.txt"
            write_text(dest, doc_text(it["path"]))
            done.append(it["id"])
            return f"- {it['id']} document `{it['rel']}` → text `{dest}`"
        if it["kind"] == "pdf":
            return f"- {it['id']} PDF `{it['rel']}` → read directly with the Read tool"
        if it["kind"] == "audio":
            return f"- {it['id']} audio `{it['rel']}` ({it.get('duration_s')} s) → transcribe on demand"
        return f"- {it['id']} {it['kind']} `{it['rel']}` → not processed ({'example' if examples else 'reference material'})"

    todo = [it for it in inv["items"] if not it.get("ignored") and (not only or it["id"] in only)]
    with cf.ThreadPoolExecutor(max_workers=max(1, a.jobs)) as ex:
        futs = {ex.submit(do_item, it): it for it in todo}
        for fut in cf.as_completed(futs):
            it = futs[fut]
            try:
                lines[it["id"]] = fut.result()
            except Exception as e:
                errors.append({"id": it["id"], "error": f"{type(e).__name__}: {str(e)[:300]}"})
                lines[it["id"]] = f"- {it['id']} ERROR: {str(e)[:160]}"
    order = [it["id"] for it in todo]
    index = media / ("examples-index.md" if examples else "index.md")
    write_text(index, ("# Examples index (study only)" if examples else "# Media index") + "\n\n" +
               "\n".join(lines[i] for i in order if i in lines))
    out({"ok": not errors, "set": a.inv_set, "prepared": sorted(done), "errors": errors, "index": str(index)},
        0 if not errors else 1)


# --------------------------------------------------------------------------- targeted frames

def _parse_times(s: str) -> list:
    return [float(x) for x in re.split(r"[,\s]+", s.strip()) if x]


def cmd_frames(a):
    info = media_summary(a.video)
    dur = info.get("duration_s") or 0
    tmax = max(0.0, dur - 1.5 / (info.get("fps") or 24))
    ts = []
    if a.at:
        ts += _parse_times(a.at)
    for rg in a.range or []:
        m = re.match(r"^\s*([0-9.]+)\s*-\s*([0-9.]+)\s*$", rg)
        if not m:
            fail(f"bad --range {rg!r}; use start-end in seconds", 2)
        st, en = float(m.group(1)), float(m.group(2))
        k = 0
        while st + k / a.fps <= en + 1e-6:
            ts.append(st + k / a.fps)
            k += 1
    if not ts:
        fail("give --at and/or --range", 2)
    ts = sorted(set(round(min(tmax, max(0.0, x)), 3) for x in ts))
    od = Path(a.out)
    pre = a.label or "f"
    res = extract_many(a.video, [(t, od / f"{pre}-{ts_name(t)}.jpg", {"kind": "extra"}) for t in ts], a.max_side)
    sheets = []
    if a.sheet:
        sheets = build_storyboard(res, od / f"sheet-{pre}", a.title or f"{Path(a.video).name} {pre}",
                                  info.get("orientation", "portrait"), dense=len(res) > 12)
    out({"ok": all(r["ok"] for r in res), "frames": [{"t": r["t"], "file": r["file"], "ok": r["ok"]} for r in res],
         "sheets": sheets})


# --------------------------------------------------------------------------- Higgsfield transfer helpers

def cmd_hf_put(a):
    p = Path(a.file)
    if not p.exists():
        fail(f"file not found: {p}", 2)
    ct = a.content_type or CONTENT_TYPES.get(p.suffix.lower(), "application/octet-stream")
    last = None
    for attempt in range(a.retries):
        try:
            import requests  # type: ignore
            with open(p, "rb") as f:
                r = requests.put(a.url, data=f, headers={"Content-Type": ct}, timeout=a.timeout)
            if r.status_code == 200:
                out({"ok": True, "status": 200, "bytes": p.stat().st_size, "content_type": ct,
                     "etag": r.headers.get("ETag")})
            last = f"HTTP {r.status_code}: {r.text[:300]}"
            if r.status_code in (400, 403):
                break  # signature / content-type mismatch or expired slot: request a fresh media_upload slot
        except Exception as e:
            last = str(e)[:300]
        time.sleep(2 ** attempt)
    fail(f"upload failed: {last}", 1, content_type=ct)


def _download(url: str, dest: Path, retries: int, headers=None) -> int:
    """Stream a public URL to dest (via .part, verified length). Returns the byte count; raises after the
    last retry. Refuses HTML pages: the URL must point at the media file itself."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    last = None
    for attempt in range(retries):
        try:
            import requests  # type: ignore
            with requests.get(url, stream=True, timeout=(15, 180), headers=headers or {}) as r:
                r.raise_for_status()
                if "text/html" in r.headers.get("Content-Type", ""):
                    raise IOError("got an HTML page instead of media")
                expected = int(r.headers.get("Content-Length", 0) or 0)
                n = 0
                with open(part, "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
                        n += len(chunk)
            if expected and n != expected:
                raise IOError(f"short read {n}/{expected}")
            os.replace(part, dest)
            return n
        except Exception as e:
            last = str(e)[:300]
            time.sleep(2 ** attempt)
    raise IOError(f"download failed: {last}")


def cmd_hf_get(a):
    dest = Path(a.out)
    try:
        n = _download(a.url, dest, a.retries)
        s = media_summary(dest)
        if not s.get("has_video") and dest.suffix.lower() in VIDEO_EXT:
            raise IOError("downloaded file has no video stream")
    except Exception as e:
        fail(str(e)[:300])
    out({"ok": True, "file": str(dest), "bytes": n, **{k: s.get(k) for k in
         ("duration_s", "display_width", "display_height", "aspect", "fps", "has_audio")}})


def cmd_fetch_audio(a):
    """Download a soundtrack or sound effect (the direct audio-file URL, not the web page) for an
    Analyze Create video, verify it decodes, and record its origin and license beside it
    (<file>.source.json). Only audio with a known license goes into a deliverable."""
    dest = Path(a.out)
    try:
        n = _download(a.url, dest, a.retries, headers={"User-Agent": "Mozilla/5.0 (analyze-then-pick)"})
        s = media_summary(dest)
    except Exception as e:
        fail(str(e)[:300])
    if not s.get("has_audio"):
        fail("the downloaded file has no audio stream", 1, file=str(dest))
    meta = {"file": str(dest), "url": a.url, "page": a.page, "license": a.license, "title": a.title,
            "author": a.author, "role": a.role, "fetched": now_iso(), "duration_s": s.get("duration_s")}
    write_json(dest.with_name(dest.name + ".source.json"), meta)
    out({"ok": True, "bytes": n, **meta})


def cmd_audio_profile(a):
    """Sound-design profile of one reference for Analyze Create: what sits under and around the speech,
    so the new video's soundtrack can be matched or reused. Measured with librosa (no listening):
    - speech share (from the transcript);
    - music bed likelihood (harmonic energy outside speech, beat strength);
    - tempo and beat strength;
    - energy per second and its arc;
    - "hits" (strong transients: stings, booms, whooshes) and whether they land on a cut.
    The ROLE (dramatic, comic, suspense, hype) is the agent's inference from these numbers plus the
    visuals. Writes --out (JSON)."""
    try:
        import numpy as np
        import librosa
    except ImportError:
        fail("librosa and numpy are required for audio-profile", 1)
    src, dst = Path(a.audio), Path(a.out)
    dst.parent.mkdir(parents=True, exist_ok=True)
    wav = dst.with_suffix(".22k.wav")
    cp = run([find_tool("ffmpeg"), "-nostdin", "-y", "-loglevel", "error", "-i", str(src), "-vn", "-ac", "1",
              "-ar", "22050", str(wav)], timeout=900)
    if cp.returncode != 0 or not wav.exists():
        fail("could not decode the audio: " + cp.stderr[-400:])
    y, sr = librosa.load(str(wav), sr=22050, mono=True)
    wav.unlink(missing_ok=True)
    dur = len(y) / sr if sr else 0
    if dur < 0.5 or not np.any(y):
        out({"ok": True, "file": str(src), "duration_s": round(dur, 2), "silent": True})
    hop = 512
    speech = []
    if a.transcript and Path(a.transcript).exists():
        tj = json.loads(Path(a.transcript).read_text(encoding="utf-8"))
        speech = [(float(s.get("start", 0)), float(s.get("end", 0))) for s in tj.get("segments", [])
                  if s.get("end") is not None]
    cuts = []
    if a.cuts and Path(a.cuts).exists():
        cuts = [float(c["t"]) for c in json.loads(Path(a.cuts).read_text(encoding="utf-8")).get("cuts", [])]
    harm, perc = librosa.effects.hpss(y)
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    rms_h = librosa.feature.rms(y=harm, hop_length=hop)[0]
    t = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
    in_speech = np.zeros(len(t), dtype=bool)
    for s0, s1 in speech:
        in_speech |= (t >= s0) & (t <= s1)
    db = 20 * np.log10(np.maximum(rms, 1e-6))
    audible = db > -45
    non_speech = audible & ~in_speech
    harm_ratio = float(np.median((rms_h[non_speech] / np.maximum(rms[non_speech], 1e-6)))) if non_speech.any() else None
    onset = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    try:
        tempo, _beats = librosa.beat.beat_track(onset_envelope=onset, sr=sr, hop_length=hop)
        tempo = float(np.atleast_1d(tempo)[0])
    except Exception:
        tempo = float(np.atleast_1d(librosa.feature.tempo(onset_envelope=onset, sr=sr, hop_length=hop))[0])
    ac = librosa.autocorrelate(onset - onset.mean())
    lag = int(round(60.0 / tempo * sr / hop)) if tempo > 0 else 0
    pulse = float(ac[lag] / ac[0]) if 0 < lag < len(ac) and ac[0] > 0 else 0.0
    speech_share = (sum(max(0.0, min(e, dur) - max(s, 0.0)) for s, e in speech) / dur) if dur else 0.0
    nonspeech_share = float(non_speech.mean()) if len(non_speech) else 0.0
    if speech_share > 0.85 and (harm_ratio is None or nonspeech_share < 0.1):
        music = "unknown: speech covers almost all of it"
    elif ((harm_ratio or 0) >= 0.55 and nonspeech_share >= 0.15) or pulse >= 0.35:
        music = "likely"
    else:
        music = "unlikely"
    thr = onset.mean() + 2.5 * onset.std()
    pk = librosa.util.peak_pick(onset, pre_max=8, post_max=8, pre_avg=40, post_avg=40, delta=float(onset.std()), wait=20)
    hits = []
    for i in pk:
        if onset[i] < thr:
            continue
        ht = float(librosa.frames_to_time(i, sr=sr, hop_length=hop))
        near = min(cuts, key=lambda c: abs(c - ht)) if cuts else None
        hits.append({"t": round(ht, 2), "strength": round(float(onset[i] / (onset.max() or 1)), 2),
                     "in_speech": bool(any(s0 <= ht <= s1 for s0, s1 in speech)),
                     "on_cut": bool(near is not None and abs(near - ht) <= 0.25)})
    per_s = [round(float(db[(t >= k) & (t < k + 1)].mean()), 1) for k in range(int(math.ceil(dur)))
             if ((t >= k) & (t < k + 1)).any()]
    q = max(1, len(per_s) // 3)
    first, last = (statistics.mean(per_s[:q]), statistics.mean(per_s[-q:])) if per_s else (0, 0)
    arc = "rising" if last - first > 3 else ("falling" if first - last > 3 else "steady")
    centroid = float(np.median(librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop)))
    prof = {"ok": True, "file": str(src), "duration_s": round(dur, 2),
            "speech_share": round(speech_share, 2), "non_speech_audible_share": round(nonspeech_share, 2),
            "music_bed": music, "harmonic_ratio_non_speech": None if harm_ratio is None else round(harm_ratio, 2),
            "tempo_bpm": round(tempo, 1), "beat_strength": round(pulse, 2),
            "energy_db_per_s": per_s, "energy_arc": arc,
            "hits": sorted(hits, key=lambda h: -h["strength"])[:12], "brightness_hz": round(centroid),
            "reusable_whole": bool(music == "likely" and speech_share < 0.1),
            "note": "measured cues, not listening: infer the role (dramatic / comic / suspense / hype) from these "
                    "numbers plus the visuals; 'reusable_whole' means no speech over it (rights still apply)"}
    write_json(dst, prof)
    out(prof)


def cmd_split_audio(a):
    """For every ORIGINAL video under the given folder(s)/file(s): extract its audio (stream copy) into
    <root>/files_audio/<rel>.<ext> and write a silent copy (video stream copy, no audio) into
    <root>/videos_without_audio/<rel>. <root> is the given folder (or a given file's folder). The silent
    copies are what gets uploaded to Higgsfield; the audio files are merged back into approved results.
    --audio-only (Analyze Create) writes files_audio/ only: no silent copies, because no reference is
    ever uploaded; the audio feeds the sound-design analysis and the soundtrack choice.
    Idempotent (existing outputs are kept unless --redo). Writes a manifest into the run when --run."""
    ff = find_tool("ffmpeg")
    entries, errors = [], []
    for raw in a.paths:
        p = Path(raw).expanduser().resolve()
        if not p.exists():
            fail(f"not found: {p}", 2)
        root = p if p.is_dir() else p.parent
        if p.is_dir():
            vids = [f for f, _ in _collect_files([str(p)], None, None) if classify(f) == "video"]
        else:
            vids = [p] if classify(p) == "video" else []
        for f in vids:
            rel = f.relative_to(root)
            silent = None if a.audio_only else root / "videos_without_audio" / rel
            e = {"original": str(f), "silent": str(silent) if silent else None, "audio": None, "audio_offset": 0.0,
                 "root": str(root), "rel": str(rel), "final": str(root / FINAL_DIR / rel.with_suffix(".mp4"))}
            try:
                s = media_summary(f)
                e.update({"duration_s": s.get("duration_s"), "has_audio": bool(s.get("has_audio"))})
                if s.get("has_audio"):
                    codec = s.get("audio_codec") or ""
                    audio = root / "files_audio" / rel.with_suffix(AUDIO_EXT_FOR_CODEC.get(codec, ".mka"))
                    audio.parent.mkdir(parents=True, exist_ok=True)
                    if a.redo or not audio.exists():
                        cp = run([ff, "-nostdin", "-y", "-loglevel", "error", "-i", str(f), "-map",
                                  f"0:{s['audio_index']}", "-vn", "-c:a", "copy", str(audio)], timeout=1800)
                        if cp.returncode != 0 or not audio.exists():
                            audio = audio.with_suffix(".wav")
                            run([ff, "-nostdin", "-y", "-loglevel", "error", "-i", str(f), "-map",
                                 f"0:{s['audio_index']}", "-vn", "-c:a", "pcm_s24le", str(audio)], timeout=1800, check=True)
                    e["audio"] = str(audio)
                    # audio/video start offset of the ORIGINAL, applied again when merging back
                    e["audio_offset"] = round((s.get("audio_start") or 0.0) - (s.get("video_start") or 0.0), 4)
                if silent:
                    silent.parent.mkdir(parents=True, exist_ok=True)
                    if a.redo or not silent.exists():
                        extra = ["-movflags", "+faststart"] if silent.suffix.lower() in (".mp4", ".mov", ".m4v") else []
                        run([ff, "-nostdin", "-y", "-loglevel", "error", "-i", str(f), "-map", "0:v:0", "-c:v", "copy",
                             "-an", *extra, str(silent)], timeout=1800, check=True)
                    sv = media_summary(silent)
                    e["silent_ok"] = bool(sv.get("has_video")) and not sv.get("has_audio") and \
                        abs((sv.get("duration_s") or 0) - (s.get("duration_s") or 0)) <= 0.15
                    if not e["silent_ok"]:
                        errors.append({"original": str(f), "error": "silent copy failed verification"})
            except Exception as ex:
                e["error"] = str(ex)[:300]
                errors.append({"original": str(f), "error": str(ex)[:300]})
            entries.append(e)
    manifest = {"created": now_iso(), "entries": entries}
    if a.run:
        run_dir = Path(a.run)
        write_json(run_dir / "00-inventory" / "audio-split.json", manifest)
        inv_p = run_dir / "00-inventory" / "inventory.json"
        if inv_p.exists():                       # link the originals in the inventory to their pieces
            inv = json.loads(inv_p.read_text(encoding="utf-8"))
            by_orig = {str(Path(e["original"]).resolve()).lower(): e for e in entries}
            for it in inv["items"]:
                m = by_orig.get(str(Path(it["path"]).resolve()).lower())
                if m:
                    it.update({"silent_path": m["silent"], "audio_path": m["audio"], "audio_offset": m["audio_offset"],
                               "final_path": m["final"]})
            write_json(inv_p, inv)
    out({"ok": not errors, "videos": len(entries), "with_audio": sum(1 for e in entries if e.get("audio")),
         "folders": sorted({str(Path(e["silent"]).parent) for e in entries if e.get("silent")}
                           | {str(Path(e["audio"]).parent) for e in entries if e.get("audio")}),
         "audio_only": bool(a.audio_only),
         "errors": errors, "manifest": str(Path(a.run) / "00-inventory" / "audio-split.json") if a.run else None},
        0 if not errors else 1)


def cmd_finalize(a):
    """Place an APPROVED Edit Mode result (generated picture + original audio) into
    <given path>/final/<original name>.mp4 (sub-folders mirrored). Call only after the user approved it.
    A previous final of the same video is moved into the run folder first, never silently lost."""
    run_dir = Path(a.run)
    src = Path(a.file)
    if not src.exists():
        fail(f"file not found: {src}", 2)
    man_p = run_dir / "00-inventory" / "audio-split.json"
    if not man_p.exists():
        fail("no split-audio manifest in this run: run `split-audio` first", 2)
    man = json.loads(man_p.read_text(encoding="utf-8"))
    key = str(Path(a.original).resolve()).lower()
    entry = next((e for e in man["entries"] if str(Path(e["original"]).resolve()).lower() == key), None)
    if not entry:
        fail(f"original not found in the split-audio manifest: {a.original}", 2)
    dest = Path(entry.get("final") or (Path(entry["root"]) / FINAL_DIR / Path(entry["rel"]).with_suffix(".mp4")))
    final_root = Path(entry["root"]) / FINAL_DIR
    info = media_summary(src)
    ew, eh = [int(x) for x in a.expect_size.lower().split("x")]
    checks = {"has_video": bool(info.get("has_video")),
              "size_ok": (info.get("display_width"), info.get("display_height")) == (ew, eh),
              "audio_matches_original": bool(info.get("has_audio")) == bool(entry.get("has_audio"))}
    if not all(checks.values()) and not a.force:
        fail("the approved file does not pass the final checks (fix it, or --force if the user insists)", 1,
             checks=checks)
    dest.parent.mkdir(parents=True, exist_ok=True)
    _mark_final_dir(final_root)
    replaced = None
    if dest.exists():
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        replaced = run_dir / "60-outputs" / "replaced-finals" / f"{dest.stem}-{stamp}{dest.suffix}"
        replaced.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(dest), str(replaced))
    shutil.copy2(src, dest)
    st_p = run_dir / "state.json"
    if st_p.exists():
        st = json.loads(st_p.read_text(encoding="utf-8"))
        vids = st.setdefault("videos", [])
        rec = {"video": a.video, "original": entry["original"], "final": str(dest), "approved_file": str(src.resolve()),
               "finalized": now_iso()}
        for i, v in enumerate(vids):
            if isinstance(v, dict) and v.get("original") == entry["original"]:
                vids[i] = {**v, **rec}
                break
        else:
            vids.append(rec)
        st["updated"] = now_iso()
        write_json(st_p, st)
    out({"ok": True, "final": str(dest), "checks": checks,
         "replaced_previous_final": str(replaced) if replaced else None})


def cmd_restore_audio(a):
    """Put the ORIGINAL audio under a generated (edited) video: the generated picture, the original sound.
    Audio source: --audio <files_audio file> (+ --audio-offset from the split manifest), or --source
    <original video> (audio extracted from it). --start selects the segment of the original timeline
    when a trimmed segment was edited. Any audio in the generated file is discarded."""
    gen, dst = Path(a.generated), Path(a.out)
    g_info = media_summary(gen)
    ff = find_tool("ffmpeg")
    work = dst.parent / "_restore"
    work.mkdir(parents=True, exist_ok=True)
    ref_info = None
    audio, off = None, 0.0
    if a.audio:
        audio = Path(a.audio)
        if not audio.exists():
            fail(f"audio file not found: {audio}", 2)
        off = a.audio_offset or 0.0
        src_dur = media_summary(audio).get("duration_s")
    elif a.source:
        ref_info = media_summary(a.source)
        src_dur = ref_info.get("duration_s")
        if ref_info.get("has_audio"):
            audio = work / "source-audio.mka"
            cp = run([ff, "-nostdin", "-y", "-loglevel", "error", "-i", str(a.source), "-map",
                      f"0:{ref_info['audio_index']}", "-vn", "-c:a", "copy", str(audio)])
            if cp.returncode != 0:
                audio = work / "source-audio.wav"
                run([ff, "-nostdin", "-y", "-loglevel", "error", "-i", str(a.source), "-map",
                     f"0:{ref_info['audio_index']}", "-vn", "-c:a", "pcm_s24le", str(audio)], check=True)
            off = (ref_info.get("audio_start") or 0.0) - (ref_info.get("video_start") or 0.0)
    else:
        fail("give --audio (from files_audio) or --source", 2)
    g_dur = g_info.get("duration_s") or 0
    want = a.duration or (src_dur - (a.start or 0.0) if src_dur else g_dur)
    dur = round(min(g_dur, want), 3) if g_dur else want          # never loop or freeze frames to pad
    if audio:
        start = a.start or 0.0
        tail = f"apad=whole_dur={dur},atrim=duration={dur}"
        shift = off - start                                        # >0: audio starts late; <0: skip into it
        if shift > 0.0005:
            af = f"adelay={int(round(shift * 1000))}:all=1,asetpts=PTS-STARTPTS,{tail}"
        elif shift < -0.0005:
            af = f"atrim=start={abs(shift):.4f},asetpts=PTS-STARTPTS,{tail}"
        else:
            af = f"asetpts=PTS-STARTPTS,{tail}"
        cp = run([ff, "-nostdin", "-y", "-loglevel", "error", "-i", str(gen), "-i", str(audio),
                  "-filter_complex", f"[1:a:0]{af}[sa]", "-map", "0:v:0", "-map", "[sa]", "-t", f"{dur}",
                  "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", str(dst)])
    else:                                                          # the original had no audio → silent final
        cp = run([ff, "-nostdin", "-y", "-loglevel", "error", "-i", str(gen), "-map", "0:v:0", "-t", f"{dur}",
                  "-c:v", "copy", "-an", "-movflags", "+faststart", str(dst)])
    shutil.rmtree(work, ignore_errors=True)
    if cp.returncode != 0:
        fail("mux failed: " + cp.stderr[-600:])
    f_info = media_summary(dst)
    tol = max(1 / (f_info.get("fps") or 24), 0.10)
    short_by = round(want - g_dur, 3) if want and g_dur else 0.0
    gates = {"has_video": bool(f_info.get("has_video")),
             "audio_ok": bool(f_info.get("has_audio")) == bool(audio),
             "duration_ok": abs((f_info.get("duration_s") or 0) - dur) <= tol}
    if ref_info:
        src_ar = ref_info["display_width"] / ref_info["display_height"]
        out_ar = f_info["display_width"] / f_info["display_height"]
        gates["aspect_ok"] = abs(out_ar - src_ar) / src_ar <= 0.015
    ok = all(gates.values())
    out({"ok": ok, "file": str(dst), "duration_s": f_info.get("duration_s"), "original_segment_s": want,
         "generated_shorter_by_s": short_by if short_by > tol else 0.0,
         "note": ("generated clip is shorter than the original segment; the original audio was cut at the "
                  "generated length (start stays in sync)") if short_by > max(tol, 0.25) else None,
         "gates": gates}, 0 if ok else 1)


def _motion_curve(video, start: float, dur, fps: float):
    """Per-frame motion energy of a video at a fixed rate: log(1 + mean |frame - previous frame|) on
    tiny grayscale frames. Index i is the change into frame i+1, i.e. time (i+1)/fps."""
    import numpy as np
    w, h = 36, 64
    cmd = [find_tool("ffmpeg"), "-hide_banner", "-loglevel", "error", "-nostdin"]
    if start and start > 0:
        cmd += ["-ss", f"{start:.3f}"]
    cmd += ["-i", str(video)]
    if dur:
        cmd += ["-t", f"{dur:.3f}"]
    cmd += ["-an", "-vf", f"fps={fps},scale={w}:{h}:flags=area,format=gray", "-f", "rawvideo", "-"]
    cp = subprocess.run([str(c) for c in cmd], capture_output=True, timeout=900)
    if cp.returncode != 0:
        raise RuntimeError(f"ffmpeg decode failed on {video}: {cp.stderr.decode('utf-8', 'replace')[-400:]}")
    n = len(cp.stdout) // (w * h)
    if n < 4:
        raise RuntimeError(f"too few frames decoded from {video}")
    fr = np.frombuffer(cp.stdout[: n * w * h], dtype=np.uint8).reshape(n, h, w).astype(np.float32)
    return np.log1p(np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2)))


def _corr_at(a, b, k: int, i0: int = 0, i1: int | None = None, min_len: int = 8):
    """Pearson correlation of a[i] with b[i+k] over i in [i0, i1); None when the overlap is too short."""
    i1 = len(a) if i1 is None else min(i1, len(a))
    lo, hi = max(i0, -k), min(i1, len(b) - k)
    if hi - lo < min_len:
        return None
    x, y = a[lo:hi], b[lo + k:hi + k]
    sx, sy = float(x.std()), float(y.std())
    if sx < 1e-6 or sy < 1e-6:
        return None
    return float(((x - x.mean()) * (y - y.mean())).mean() / (sx * sy))


def _best_lag(a, b, max_k: int, i0: int = 0, i1: int | None = None, min_len: int = 8):
    """(k, corr) maximising corr(a[i], b[i+k]); ties go to the smaller |k|."""
    best_k, best_c = None, -2.0
    for k in range(-max_k, max_k + 1):
        c = _corr_at(a, b, k, i0, i1, min_len)
        if c is None:
            continue
        if c > best_c + 1e-9 or (abs(c - best_c) <= 1e-9 and abs(k) < abs(best_k or 0)):
            best_k, best_c = k, c
    return best_k, (best_c if best_k is not None else None)


def cmd_sync_check(a):
    """Do the generated picture's actions happen at the same moments as the source's? The original audio
    is laid over the generated picture (restore-audio), so every action, mouth movement and impact must
    land where its sound is. Compares per-frame motion energy of the source segment and the output:
    global offset, per-window offsets (drift), duration difference, and a side-by-side sheet (source |
    output at the same timestamps) for visual confirmation."""
    import numpy as np
    src, outv = Path(a.source), Path(a.output)
    for p in (src, outv):
        if not p.exists():
            fail(f"file not found: {p}", 2)
    od = Path(a.out)
    od.mkdir(parents=True, exist_ok=True)
    s_info, o_info = media_summary(src), media_summary(outv)
    start = a.start or 0.0
    seg = (s_info.get("duration_s") or 0.0) - start
    if a.duration:
        seg = min(seg, a.duration)
    o_dur = o_info.get("duration_s") or 0.0
    span = round(min(seg, o_dur), 3)
    if span < 1.0:
        fail(f"too little overlap to compare ({span}s)", 1)
    fps, tol = float(a.fps), float(a.tol)
    max_k = int(round(a.max_lag * fps))
    sc = _motion_curve(src, start, span, fps)
    oc = _motion_curve(outv, 0.0, span, fps)
    n = min(len(sc), len(oc))
    sc, oc = sc[:n], oc[:n]
    g_k, g_c = _best_lag(sc, oc, max_k, min_len=int(fps))
    g_off = round((g_k or 0) / fps, 3)
    # per-window offsets: a steady offset is fixable in post, a changing one (drift) is not
    W, hop = int(round(a.window * fps)), int(round(1.0 * fps))
    s_std = float(sc.std()) or 1e-6
    windows = []
    for i0 in range(0, max(1, n - W + 1), hop):
        x = sc[i0:i0 + W]
        k, c = _best_lag(sc, oc, max_k, i0, i0 + W, min_len=max(8, W // 2))
        moving = float(x.std()) >= 0.25 * s_std
        reliable = bool(k is not None and moving and c >= 0.5)
        windows.append({"t": round((i0 + W / 2) / fps, 2),
                        "offset_s": None if k is None else round(k / fps, 3),
                        "corr": None if k is None else round(c, 3), "reliable": reliable})
    rel = [w for w in windows if w["reliable"]]
    lags = [w["offset_s"] for w in rel]
    drift = None
    if len(rel) >= 3:
        ts, ls = np.array([w["t"] for w in rel]), np.array(lags)
        if float(ts.var()) > 0:
            drift = round(float(((ts - ts.mean()) * (ls - ls.mean())).mean() / ts.var()) * 10.0, 3)
    med = round(float(np.median(lags)), 3) if lags else g_off
    spread = round(max(lags) - min(lags), 3) if lags else None
    bad = [w for w in rel if abs(w["offset_s"]) > tol]
    if g_c is None or g_c < 0.3 or not rel:
        verdict = "inconclusive"
    elif not bad and abs(g_off) <= tol:
        verdict = "in_sync"
    elif spread is not None and spread <= 2 * tol:
        verdict = "constant_offset"
    elif drift is not None and abs(drift) * (span / 10.0) > tol:
        verdict = "drift"
    else:
        verdict = "out_of_sync"
    fix = None
    if verdict == "constant_offset":
        if med > 0:
            fix = {"kind": "trim_head", "seconds": med,
                   "how": "the output is late: T trim its head by this much, then restore-audio again"}
        else:
            fix = {"kind": "audio_start", "seconds": round(-med, 3),
                   "how": "the output is early: re-run restore-audio with --start increased by this much"}
    elif verdict in ("drift", "out_of_sync"):
        fix = {"kind": "regenerate",
               "how": "post-production cannot fix it: diagnose (duration, speed, added/skipped/reordered "
                      "action) and regenerate with the timing lock (generation-system.md 5c)"}
    # anchors for the side-by-side sheet, on the output timeline (source time = start + t)
    if a.at:
        anchors = sorted(float(x) for x in re.split(r"[,\s]+", a.at.strip()) if x)
    else:
        anchors, gap = [], max(0.5, span / 16)
        for i in np.argsort(sc)[::-1]:
            t = round((int(i) + 1) / fps, 3)
            if t < span - 0.05 and all(abs(t - u) >= gap for u in anchors):
                anchors.append(t)
            if len(anchors) >= a.anchors:
                break
        anchors.sort()
    sheet = None
    if anchors:
        from PIL import Image, ImageDraw
        fd = od / "sync-frames"
        rs = extract_many(str(src), [(min(start + t, start + span - 0.04), fd / f"s{j:02d}.jpg",
                                      {"j": j, "side": "source"}) for j, t in enumerate(anchors)], max_side=360)
        ro = extract_many(str(outv), [(min(t, span - 0.04), fd / f"o{j:02d}.jpg",
                                       {"j": j, "side": "output"}) for j, t in enumerate(anchors)], max_side=360)
        got = {(r["side"], r["j"]): r for r in rs + ro if r["ok"]}
        cw, ch, cols = 180, 320, min(4, len(anchors))
        rows = math.ceil(len(anchors) / cols)
        img = Image.new("RGB", (cols * (2 * cw + 12), rows * (ch + 28)), (18, 18, 18))
        dr, fnt = ImageDraw.Draw(img), _font(15)
        for j, t in enumerate(anchors):
            x0, y0 = (j % cols) * (2 * cw + 12), (j // cols) * (ch + 28)
            dr.text((x0 + 4, y0 + 5), f"{ts_label(t)}   source | output", fill=(235, 235, 235), font=fnt)
            for side, dx in (("source", 0), ("output", cw)):
                r = got.get((side, j))
                if r:
                    with Image.open(r["file"]) as im:
                        im = im.convert("RGB")
                        im.thumbnail((cw, ch))
                        img.paste(im, (x0 + dx + (cw - im.width) // 2, y0 + 26 + (ch - im.height) // 2))
        sheet = od / "sync-sheet.jpg"
        img.save(sheet, quality=88)
    res = {"ok": verdict == "in_sync", "verdict": verdict, "source": str(src), "output": str(outv),
           "start_s": start, "compared_s": span, "source_segment_s": round(seg, 3), "output_s": o_dur,
           "duration_diff_s": round(o_dur - seg, 3), "tolerance_s": tol,
           "global_offset_s": g_off, "global_corr": None if g_c is None else round(g_c, 3),
           "median_window_offset_s": med, "window_spread_s": spread, "drift_s_per_10s": drift,
           "windows_reliable": len(rel), "windows_total": len(windows),
           "off_windows": [{"t": w["t"], "offset_s": w["offset_s"]} for w in bad][:12],
           "fix": fix, "anchors_s": anchors, "sheet": str(sheet) if sheet else None,
           "note": "times are on the output timeline; positive offset = the output's action happens later "
                   "than in the source (so after its sound)"}
    (od / "sync-check.json").write_text(json.dumps({**res, "windows": windows}, indent=1), encoding="utf-8")
    out(res, 0 if res["ok"] else 1)


def cmd_qc(a):
    v = a.video
    info = media_summary(v)
    od = Path(a.out)
    shutil.rmtree(od / "frames", ignore_errors=True)
    od.mkdir(parents=True, exist_ok=True)
    dur = info.get("duration_s") or 0
    base, eff, _ = extract_baseline(v, a.fps, od / "frames", dur, max_side=720)
    sheets = build_storyboard(base, od / "qc-storyboard", f"QC {Path(v).name}", info.get("orientation", "portrait"))
    # QC checkpoints at the full frame rate (reference/anomaly-catalog.md §4): use beats, exits and
    # re-entries, occlusions, cuts, hand-offs, pours, seams. One sheet per checkpoint under <out>/dense/.
    dense = []
    shutil.rmtree(od / "dense", ignore_errors=True)
    tmax = max(0.0, dur - 1.5 / (info.get("fps") or 24))
    for i, spec in enumerate(a.dense or [], 1):
        m = re.match(r"^\s*(?:(.*?)\s*:)?\s*([0-9.]+)\s*-\s*([0-9.]+)\s*$", spec)
        if not m:
            fail(f"bad --dense {spec!r}; use label:start-end in seconds (e.g. sip:3.5-5.6)", 2)
        label = slugify(m.group(1) or f"cp{i}", 24) or f"cp{i}"
        st, en = sorted((float(m.group(2)), float(m.group(3))))
        ts, k = [], 0
        while st + k / a.dense_fps <= en + 1e-6:
            ts.append(round(min(tmax, max(0.0, st + k / a.dense_fps)), 3))
            k += 1
        ts = sorted(set(ts))
        pre = f"{i:02d}-{label}"
        res = extract_many(v, [(t, od / "dense" / f"{pre}-{ts_name(t)}.jpg", {"kind": "extra"}) for t in ts], 1280)
        dsheets = build_storyboard(res, od / "dense" / f"sheet-{pre}",
                                   f"QC checkpoint {label} {st:.2f}-{en:.2f}s @{a.dense_fps:g} fps",
                                   info.get("orientation", "portrait"), dense=len(res) > 12)
        dense.append({"label": label, "start": st, "end": en, "fps": a.dense_fps, "frames": len(res),
                      "ok": all(r["ok"] for r in res), "sheets": dsheets})
    ff = find_tool("ffmpeg")
    cp = run([ff, "-hide_banner", "-nostdin", "-i", v, "-map", "0:v:0", "-vf",
              "blackdetect=d=0.2:pix_th=0.10,freezedetect=n=-60dB:d=0.6", "-an", "-f", "null", "-"], timeout=1800)
    blacks = [{"start": float(m.group(1)), "end": float(m.group(2))}
              for m in re.finditer(r"black_start:([0-9.]+)\s+black_end:([0-9.]+)", cp.stderr)]
    freezes = [float(m.group(1)) for m in re.finditer(r"freeze_start:\s*([0-9.]+)", cp.stderr)]
    checks = {"duration_s": dur, "aspect": info.get("aspect"),
              "resolution": f"{info.get('display_width')}x{info.get('display_height')}",
              "has_audio": info.get("has_audio"), "black_spans": blacks, "freeze_starts": freezes}
    if a.expect_duration:
        checks["duration_delta_s"] = round(dur - a.expect_duration, 3)
    if a.expect_aspect:
        ew, eh = [float(x) for x in a.expect_aspect.split(":")]
        ar = info["display_width"] / info["display_height"]
        checks["aspect_error_pct"] = round(abs(ar - ew / eh) / (ew / eh) * 100, 2)
    ew, eh = [int(x) for x in a.expect_size.lower().split("x")]
    checks["size_ok"] = (info.get("display_width"), info.get("display_height")) == (ew, eh)
    text = {"available": False, "skipped": True}
    if not a.no_ocr and base:
        step = max(1, math.ceil(len(base) / 12))
        text = ocr_frames(base[::step][:11] + base[-1:])
    spans = text.get("spans") or [] if text.get("available") else []
    allowed = [_norm_word(x) for x in re.split(r"[|\n]", a.allowed_text or "") if _norm_word(x)]
    def is_allowed(s):
        k = _norm_word(s["text"])
        return any(k and (k in al or al in k) for al in allowed)
    unexpected = [f"{s['text']} @{s['first_t']:.2f}-{s['last_t']:.2f}s ({s['kind_hint']})" for s in spans
                  if not is_allowed(s) and not s.get("likely_noise")]
    checks["ocr_noise_ignored"] = [s["text"] for s in spans if s.get("likely_noise") and not is_allowed(s)]
    checks["visible_text_detected"] = [f"{s['text']} @{s['first_t']:.2f}-{s['last_t']:.2f}s" for s in spans] if text.get("available") else None
    checks["unexpected_text"] = unexpected if text.get("available") else None
    checks["text_policy"] = ("edit: no source text may remain unless explicitly kept" if a.mode == "edit"
                             else "analyze: only planned text may appear; anything else is pseudo-text or a copied artifact")
    problems = []
    if not checks["size_ok"]:
        problems.append(f"size {checks['resolution']} != {a.expect_size}")
    if unexpected:
        problems.append(f"{len(unexpected)} unexpected text span(s) - inspect the storyboard")
    if blacks:
        problems.append("black frames")
    if freezes:
        problems.append("frozen stretches")
    if a.expect_duration and abs(checks["duration_delta_s"]) > max(0.25, 0.05 * a.expect_duration):
        problems.append(f"duration off by {checks['duration_delta_s']} s")
    checks["problems"] = problems
    checks["dense_checkpoints"] = [{"label": d["label"], "start": d["start"], "end": d["end"], "frames": d["frames"]}
                                   for d in dense]
    write_json(od / "qc.json", {"info": info, "checks": checks, "ocr": text, "sheets": sheets, "dense": dense})
    out({"ok": True, "passed_automatic_checks": not problems, "qc_json": str(od / "qc.json"),
         "sheets": sheets, "dense": dense, "checks": checks})


# --------------------------------------------------------------------------- output format: 9:16 720p

def _encode_args(crf: int = 18) -> list:
    return ["-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart"]


def cmd_conform(a):
    """Bring a clip to exactly WxH (default 720x1280) without stretching: scale-to-cover + focus crop.
    Refuses when more than --max-crop of the picture would be lost (use Higgsfield `reframe` or
    regenerate from a 9:16 start frame instead), unless --allow-large-crop or --mode pad."""
    src = Path(a.video)
    info = media_summary(src)
    W, H = a.width, a.height
    iw, ih = info["display_width"], info["display_height"]
    if (iw, ih) == (W, H) and info.get("rotation", 0) == 0:
        if str(src.resolve()) != str(Path(a.out).resolve()):
            shutil.copyfile(src, a.out)
        out({"ok": True, "file": a.out, "action": "none (already exact)", "lost_fraction": 0.0})
    ff = find_tool("ffmpeg")
    if a.mode == "pad":
        s = min(W / iw, H / ih)
        vf = (f"split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},gblur=sigma=30,"
              f"eq=brightness=-0.06[bg];[b]scale={int(round(iw * s / 2)) * 2}:{int(round(ih * s / 2)) * 2}:flags=lanczos[fg];"
              f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1")
        lost, action = 0.0, "scale-to-fit + blurred fill (no crop, no stretch)"
        cmd = [ff, "-nostdin", "-y", "-loglevel", "error", "-i", str(src), "-filter_complex", vf,
               "-map", "0:a?", *_encode_args(a.crf), "-c:a", "aac", "-b:a", "192k", a.out]
    else:
        s = max(W / iw, H / ih)
        sw, sh = math.ceil(iw * s / 2) * 2, math.ceil(ih * s / 2) * 2
        lost = round(1 - (W * H) / (sw * sh), 4)
        if lost > a.max_crop and not a.allow_large_crop:
            fail(f"conform would crop {lost:.1%} of the picture (> {a.max_crop:.0%}); reframe with Higgsfield "
                 f"`reframe` (aspect_ratio 9:16, resolution 720p), regenerate from a 9:16 start frame, or rerun "
                 f"with --focus-x/--focus-y and --allow-large-crop after checking the subject stays in frame",
                 1, lost_fraction=lost, input=f"{iw}x{ih}")
        cx = min(max(a.focus_x * sw - W / 2, 0), sw - W)
        cy = min(max(a.focus_y * sh - H / 2, 0), sh - H)
        vf = f"scale={sw}:{sh}:flags=lanczos,crop={W}:{H}:{int(cx)}:{int(cy)},setsar=1"
        action = f"scale-to-cover {iw}x{ih}->{sw}x{sh} + crop {W}x{H} at focus ({a.focus_x},{a.focus_y})"
        cmd = [ff, "-nostdin", "-y", "-loglevel", "error", "-i", str(src), "-vf", vf, "-map", "0:v:0",
               "-map", "0:a?", *_encode_args(a.crf), "-c:a", "aac", "-b:a", "192k", a.out]
    cp = run(cmd, timeout=3600)
    if cp.returncode != 0:
        fail("ffmpeg failed: " + cp.stderr[-600:])
    o = media_summary(a.out)
    ok = (o["display_width"], o["display_height"]) == (W, H)
    out({"ok": ok, "file": a.out, "action": action, "lost_fraction": lost,
         "output": f"{o['display_width']}x{o['display_height']}", "duration_s": o.get("duration_s")}, 0 if ok else 1)


# --------------------------------------------------------------------------- deterministic text (captions / overlays)

FONT_FILES = {
    "arial": ["arial.ttf", "arialbd.ttf"], "arial black": ["ariblk.ttf"], "impact": ["impact.ttf"],
    "segoe ui": ["segoeui.ttf", "segoeuib.ttf"], "segoe ui black": ["seguibl.ttf"],
    "segoe ui semibold": ["seguisb.ttf"], "verdana": ["verdana.ttf", "verdanab.ttf"],
    "tahoma": ["tahoma.ttf", "tahomabd.ttf"], "trebuchet ms": ["trebuc.ttf", "trebucbd.ttf"],
    "calibri": ["calibri.ttf", "calibrib.ttf"], "georgia": ["georgia.ttf", "georgiab.ttf"],
}
FONT_DIRS = [Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts",
             Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "Fonts",
             Path("/usr/share/fonts"), Path("/Library/Fonts")]

CAPTION_PRESETS = {   # tuned for 720x1280; safe zones keep text clear of platform UI
    "hook":    {"font": "Arial Black", "size": 62, "primary": "#FFFFFF", "outline": "#000000", "outline_width": 5,
                "shadow": 0, "align": "top", "margin_v": 0.12, "bold": True},
    "caption": {"font": "Arial Black", "size": 52, "primary": "#FFFFFF", "outline": "#000000", "outline_width": 4,
                "shadow": 0, "align": "lower", "margin_v": 0.26, "bold": True},
    "label":   {"font": "Arial", "size": 38, "primary": "#FFFFFF", "outline": "#000000", "outline_width": 0,
                "shadow": 0, "align": "center", "margin_v": 0.0, "bold": True, "box": True,
                "box_color": "#000000", "box_alpha": 0.45},
    "callout": {"font": "Arial Black", "size": 46, "primary": "#FFE14D", "outline": "#000000", "outline_width": 4,
                "shadow": 0, "align": "center", "margin_v": 0.0, "bold": True},
}


def _ass_color(hexcol: str, alpha: float = 0.0) -> str:
    h = hexcol.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"&H{int(round(alpha * 255)):02X}{b:02X}{g:02X}{r:02X}"


def _ass_time(t: float) -> str:
    t = max(0.0, t)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def _resolve_font(style: dict, fonts_out: Path) -> str:
    """Copy the font file(s) next to the .ass so libass never depends on system font configuration."""
    fonts_out.mkdir(parents=True, exist_ok=True)
    if style.get("font_file"):
        p = Path(style["font_file"])
        shutil.copyfile(p, fonts_out / p.name)
        try:
            from PIL import ImageFont
            return ImageFont.truetype(str(p), 20).getname()[0]
        except Exception:
            return style.get("font", p.stem)
    fam = style.get("font", "Arial Black")
    for fn in FONT_FILES.get(fam.lower(), []):
        for d in FONT_DIRS:
            if (d / fn).exists():
                shutil.copyfile(d / fn, fonts_out / fn)
                break
    return fam


def _house_caption_look() -> dict:
    """The fallback burn-in imitates the CapCut house text style: CapCut's System font, white fill, black
    outline, not bold (capcut.text_style in config.json). Sizes stay the presets' own."""
    st = _house_text_style()
    look = {"primary": st["fill"], "outline": st["stroke"]["color"], "bold": False}
    font = _capcut_system_font()
    if font:
        look["font_file"] = font
    return look


def build_ass(spec: dict, W: int, H: int, fonts_out: Path) -> str:
    base = spec.get("style", {})
    styles, used = {}, set(e.get("preset", "caption") for e in spec["events"])
    for name in sorted(used):
        st = {**CAPTION_PRESETS.get(name, CAPTION_PRESETS["caption"]), **_house_caption_look(),
              **base, **spec.get("presets", {}).get(name, {})}
        st["family"] = _resolve_font(st, fonts_out)
        styles[name] = st
    align_map = {"top": 8, "upper": 8, "center": 5, "middle": 5, "lower": 2, "bottom": 2}
    lines = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 0",
             "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
             "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, "
             "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
             "MarginL, MarginR, MarginV, Encoding"]
    safe = {"left": 0.06, "right": 0.12, **spec.get("safe_area", {})}
    for name, st in styles.items():
        box = st.get("box")
        back = _ass_color(st.get("box_color", "#000000"), 1 - st.get("box_alpha", 0.5)) if box else "&H00000000"
        lines.append(
            f"Style: {name},{st['family']},{st['size']},{_ass_color(st['primary'])},&H000000FF,"
            f"{_ass_color(st.get('outline', '#000000'))},{back},{-1 if st.get('bold', True) else 0},0,0,0,100,100,0,0,"
            f"{3 if box else 1},{st.get('box_pad', 8) if box else st.get('outline_width', 4)},{st.get('shadow', 0)},"
            f"{align_map.get(st.get('align', 'lower'), 2)},{int(safe['left'] * W)},{int(safe['right'] * W)},"
            f"{int(st.get('margin_v', 0.26) * H)},1")
    lines += ["", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for e in sorted(spec["events"], key=lambda e: e["start"]):
        txt = str(e["text"]).replace("{", "(").replace("}", ")").replace("\\", "/").replace("\n", "\\N")
        if spec.get("uppercase") or e.get("uppercase"):
            txt = txt.upper()
        tags = ""
        if e.get("pos"):
            x, y = e["pos"]
            tags += f"\\pos({int(x * W if x <= 1 else x)},{int(y * H if y <= 1 else y)})"
        anim = e.get("animation", spec.get("animation", "pop"))
        if anim == "pop":
            tags += "\\fscx85\\fscy85\\t(0,90,\\fscx100\\fscy100)"
        elif anim == "fade":
            tags += "\\fad(120,120)"
        lines.append(f"Dialogue: {e.get('layer', 0)},{_ass_time(e['start'])},{_ass_time(e['end'])},"
                     f"{e.get('preset', 'caption')},,0,0,0,,{('{' + tags + '}') if tags else ''}{txt}")
    return "\n".join(lines) + "\n"


def _norm_word(w: str) -> str:
    return re.sub(r"[^\w']+", "", w.lower())


def align_script(words: list, script: str) -> list:
    """Keep the intended wording, borrow timing from ASR words (difflib alignment + interpolation)."""
    import difflib
    target = script.split()
    if not words:
        return []
    a = [_norm_word(w["w"]) for w in words]
    b = [_norm_word(t) for t in target]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    timed = [None] * len(target)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal" or (tag == "replace" and (i2 - i1) == (j2 - j1)):
            for k in range(j2 - j1):
                timed[j1 + k] = (words[i1 + k]["s"], words[i1 + k]["e"])
        elif tag == "replace" and i2 > i1:
            s0, e0 = words[i1]["s"], words[i2 - 1]["e"]
            step = (e0 - s0) / max(1, j2 - j1)
            for k in range(j2 - j1):
                timed[j1 + k] = (s0 + k * step, s0 + (k + 1) * step)
    last_e = words[0]["s"]
    for i in range(len(timed)):             # fill gaps (inserted words) between neighbours
        if timed[i] is None:
            nxt = next((timed[j][0] for j in range(i + 1, len(timed)) if timed[j]), last_e + 0.3)
            timed[i] = (last_e, max(last_e + 0.12, min(nxt, last_e + 0.35)))
        last_e = timed[i][1]
    return [{"w": target[i], "s": round(timed[i][0], 2), "e": round(timed[i][1], 2)} for i in range(len(target))]


def chunk_words(words: list, max_words: int = 3, max_gap: float = 0.35, max_dur: float = 1.8) -> list:
    events, cur = [], []
    for w in words:
        if cur and (len(cur) >= max_words or w["s"] - cur[-1]["e"] > max_gap or w["e"] - cur[0]["s"] > max_dur
                    or re.search(r"[.!?,;:]$", cur[-1]["w"])):
            events.append(cur)
            cur = []
        cur.append(w)
    if cur:
        events.append(cur)
    res = []
    for i, ev in enumerate(events):
        end = ev[-1]["e"]
        if i + 1 < len(events):
            end = min(max(end, ev[-1]["e"] + 0.05), events[i + 1][0]["s"])   # never overlap the next caption
        res.append({"start": round(ev[0]["s"], 2), "end": round(max(end, ev[0]["s"] + 0.25), 2),
                    "text": " ".join(w["w"] for w in ev), "preset": "caption"})
    return res


def cmd_captions(a):
    """Burn exact, frame-consistent text with libass: explicit events (--spec) and/or speech-timed
    captions (--from-speech, optionally forced to the intended wording with --script)."""
    video = Path(a.video)
    info = media_summary(video)
    W, H = info["display_width"], info["display_height"]
    spec = {"events": []}
    if a.spec:
        spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
        spec.setdefault("events", [])
    work = Path(a.out).parent / (Path(a.out).stem + "-captions")
    work.mkdir(parents=True, exist_ok=True)
    if a.from_speech:
        aud = audio_analysis(str(video), info, work / "audio")
        if not aud.get("wav_16k"):
            fail("no audio stream to time captions against")
        tr = transcribe(aud["wav_16k"], work / "audio", a.whisper_model, a.language)
        words = [w for s in tr["segments"] for w in s.get("words", [])]
        script = Path(a.script_file).read_text(encoding="utf-8") if a.script_file else a.script
        if script:
            words = align_script(words, script)
        spec["events"] += chunk_words(words, a.words_per_caption)
    if not spec["events"]:
        fail("no caption events (give --spec and/or --from-speech)", 2)
    ass = build_ass(spec, W, H, work / "fonts")
    ass_path = work / "captions.ass"
    ass_path.write_text(ass, encoding="utf-8")
    write_json(work / "caption-events.json", spec["events"])
    cp = run([find_tool("ffmpeg"), "-nostdin", "-y", "-loglevel", "error", "-i", str(video.resolve()),
              "-vf", "subtitles=captions.ass:fontsdir=fonts", "-map", "0:v:0", "-map", "0:a?",
              *_encode_args(a.crf), "-c:a", "copy", str(Path(a.out).resolve())], cwd=str(work), timeout=3600)
    if cp.returncode != 0:
        fail("burn-in failed: " + cp.stderr[-800:])
    out({"ok": True, "file": a.out, "events": len(spec["events"]), "ass": str(ass_path),
         "events_json": str(work / "caption-events.json")})


# --------------------------------------------------------------------------- deterministic clean-up (Edit Mode)

def _rect(spec: str, W: int, H: int) -> tuple:
    body, _, rng = spec.partition("@")
    x, y, w, h = [float(v) for v in body.split(",")]
    if max(x, y, w, h) <= 1.0:
        x, y, w, h = x * W, y * H, w * W, h * H
    t0 = t1 = None
    if rng:
        t0, t1 = [float(v) for v in rng.split("-")]
    return int(x), int(y), int(w), int(h), t0, t1


def cmd_clean(a):
    """Local clean-up before an edit: delogo small static overlays (handles, watermarks, corner bugs)
    and/or crop away a static text band. Large captions over the subject belong to the edit model."""
    info = media_summary(a.video)
    W, H = info["display_width"], info["display_height"]
    filters = []
    for d in a.delogo or []:
        x, y, w, h, t0, t1 = _rect(d, W, H)
        x, y = max(1, x), max(1, y)
        w, h = min(w, W - x - 2), min(h, H - y - 2)
        f = f"delogo=x={x}:y={y}:w={w}:h={h}"
        if t0 is not None:
            f += f":enable='between(t,{t0},{t1})'"
        filters.append(f)
    if a.crop:
        x, y, w, h, _, _ = _rect(a.crop, W, H)
        filters.append(f"crop={w // 2 * 2}:{h // 2 * 2}:{x}:{y}")
    if not filters:
        fail("give --delogo and/or --crop", 2)
    cp = run([find_tool("ffmpeg"), "-nostdin", "-y", "-loglevel", "error", "-i", a.video, "-vf",
              ",".join(filters + ["setsar=1"]), "-map", "0:v:0", "-map", "0:a?", *_encode_args(a.crf),
              "-c:a", "copy", a.out], timeout=3600)
    if cp.returncode != 0:
        fail("ffmpeg failed: " + cp.stderr[-600:])
    o = media_summary(a.out)
    out({"ok": True, "file": a.out, "filters": filters, "output": f"{o['display_width']}x{o['display_height']}"})


# --------------------------------------------------------------------------- trim / concat

def cmd_trim(a):
    """Frame-accurate trim (re-encode) — removes generated dead space at the head or tail."""
    info = media_summary(a.video)
    end = a.end if a.end is not None else info["duration_s"]
    if not (0 <= a.start < end):
        fail("need 0 <= start < end", 2)
    cp = run([find_tool("ffmpeg"), "-nostdin", "-y", "-loglevel", "error", "-i", a.video, "-ss", f"{a.start:.3f}",
              "-to", f"{end:.3f}", "-map", "0:v:0", "-map", "0:a?", *_encode_args(a.crf), "-c:a", "aac", "-b:a",
              "192k", a.out], timeout=3600)
    if cp.returncode != 0:
        fail("ffmpeg failed: " + cp.stderr[-600:])
    o = media_summary(a.out)
    out({"ok": True, "file": a.out, "duration_s": o.get("duration_s")})


def _count_frames(path) -> tuple[int, float]:
    """Exact decoded frame count and frame rate of the first video stream (decodes the whole clip)."""
    cp = run([find_tool("ffprobe"), "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
              "stream=nb_read_frames,avg_frame_rate,r_frame_rate", "-of", "json", str(path)], timeout=900)
    if cp.returncode != 0:
        raise RuntimeError(f"ffprobe failed on {path}: {cp.stderr.strip()[:400]}")
    s = (json.loads(cp.stdout or "{}").get("streams") or [{}])[0]
    fps = _ratio(s.get("avg_frame_rate")) or _ratio(s.get("r_frame_rate")) or 24.0
    return int(s.get("nb_read_frames", 0) or 0), fps


# ----------------------------------------------------------------------------------------------------------------
# Caught flags. ATP/caught_flags.html is the flag record AND its viewer in one self-contained page: the data is a
# JSON block inside it, scripts/caught_flags_template.html is the viewer (search, filters, grouping, detail).
# `caught-flag` is the only writer (add | set | reconcile | render); no step of a run and no agent reads the page
# (command item 23): it is for the person who opens it. The script gathers what the run already knows (the video,
# the attempt, the request's prompt and parameters, every input with its file, type and thumbnail, the reference
# and its source segment, the job and its ledger row); the agent adds the judgement (Higgsfield's reply, the
# suspected trigger, which input, which words, which part of a video, the grouping tags).


def _cf_text_or_file(v):
    """A literal text, or a file path: a .md/.txt file is read whole; a request .json gives its prompt."""
    if not v:
        return ""
    p = Path(str(v))
    try:
        if p.is_file():
            raw = p.read_bytes().decode("utf-8", "replace").replace("\r\n", "\n")
            if p.suffix.lower() == ".json":
                try:
                    j = json.loads(raw)
                    if isinstance(j, dict):
                        if isinstance(j.get("prompt"), str):
                            return j["prompt"].strip()
                        if isinstance(j.get("params"), dict) and isinstance(j["params"].get("prompt"), str):
                            return j["params"]["prompt"].strip()
                except ValueError:
                    pass
            return raw.strip("\n")
    except OSError:
        pass
    return str(v)


def _cf_sentence_diff(old: str, new: str, cap: int = 14) -> str:
    """What changed between the failed and the accepted prompt, sentence by sentence (- removed, + added)."""
    import difflib
    def sp(t):
        return [s.strip() for s in re.split(r"(?<=[.;!?])\s+|\n+", t or "") if s.strip()]
    a_, b_ = sp(old), sp(new)
    lines = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a_, b_, autojunk=False).get_opcodes():
        if op in ("replace", "delete"):
            lines += ["- " + s[:300] for s in a_[i1:i2]]
        if op in ("replace", "insert"):
            lines += ["+ " + s[:300] for s in b_[j1:j2]]
    if len(lines) > cap:
        lines = lines[:cap] + [f"… {len(lines) - cap} more changed sentences"]
    return "\n".join(lines)


CAUGHT_FLAGS = ATP_HOME / "caught_flags.html"
CF_TEMPLATE = ATP_HOME / "scripts" / "caught_flags_template.html"
CF_KINDS = ["moderation-block", "refused-no-reason", "media-flagged", "output-flagged", "preset-notice", "other"]
CF_CAUSES = ["prompt-wording", "reference-video", "image-reference", "output", "parameter", "unknown"]
CF_STATUS = ["open", "cleared", "persistent"]
CF_TERMS = re.compile(r"moderat|flag|nsfw|refus|polic|safety|blocked|copyright|\bip\b|celebrit|likeness|preset_recommendation|"
                      r"rejected before creation|no reason|no error", re.I)
CF_DATA_RE = re.compile(r'(<script id="flags-data" type="application/json">)(.*?)(</script>)', re.S)
CF_ROLE_LABEL = {"image_references": "Image", "video_references": "Video", "audio_references": "Audio"}
CF_PARAM_KEYS = ("model", "mode", "duration", "duration_policy", "aspect_ratio", "resolution", "generate_audio",
                 "enable_thinking", "count", "declined_preset_id")


def _cf_load() -> list:
    """The entries stored in the page's flags-data block ([] when the page does not exist yet)."""
    if not CAUGHT_FLAGS.exists():
        return []
    page = CAUGHT_FLAGS.read_bytes().decode("utf-8")
    m = CF_DATA_RE.search(page)
    if not m:
        fail(f"{CAUGHT_FLAGS.name} has no flags-data block (restore it from git)", 2)
    try:
        return list((json.loads(m.group(2)) or {}).get("entries", []))
    except ValueError as e:
        fail(f"{CAUGHT_FLAGS.name}: the flags-data block is not valid JSON ({e})", 2)


def _cf_save(entries: list):
    """Write the page: the viewer template with the entries injected as one JSON block (atomic)."""
    if not CF_TEMPLATE.is_file():
        fail(f"the viewer template is missing: {CF_TEMPLATE}", 2)
    tpl = CF_TEMPLATE.read_bytes().decode("utf-8")
    if tpl.count("__FLAGS_JSON__") != 1:
        fail("the viewer template must contain __FLAGS_JSON__ exactly once", 2)
    blob = json.dumps({"version": 1, "generated": now_iso(), "entries": entries}, ensure_ascii=False, separators=(",", ":"))
    blob = blob.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    tmp = CAUGHT_FLAGS.with_suffix(".html.tmp")
    tmp.write_bytes(tpl.replace("__FLAGS_JSON__", blob).encode("utf-8"))
    os.replace(tmp, CAUGHT_FLAGS)


def _cf_run_dir(run):
    if not run:
        return None
    rd = Path(str(run))
    if not rd.exists():
        rd = ATP_HOME / "runs" / str(run)
    return rd if rd.exists() else None


def _cf_nn(video) -> str:
    m = re.search(r"(\d{1,3})", str(video or ""))
    return m.group(1).zfill(2) if m else str(video or "")


def _cf_request_file(rd, video, attempt):
    """The request json of this video and attempt (the newest one when the attempt is not given or not found)."""
    d = rd / "50-requests" if rd else None
    if not d or not d.is_dir() or not video:
        return None
    nn = _cf_nn(video)
    reqs = sorted(d.glob(f"video-{nn}*-request.json"), key=lambda p: p.stat().st_mtime)
    if not reqs:
        return None
    tok = re.sub(r"[^a-z0-9]+", "-", str(attempt or "").lower()).strip("-")
    if tok:
        exact = [p for p in reqs if f"-{tok}-" in p.name.lower()]
        if exact:
            return exact[-1]
        if tok in ("a1", "1"):
            plain = [p for p in reqs if p.name.lower() == f"video-{nn}-request.json"]
            if plain:
                return plain[-1]
    return reqs[-1]


def _cf_request_json(src) -> dict:
    if not src:
        return {}
    p = Path(str(src))
    if not (p.is_file() and p.suffix.lower() == ".json"):
        return {}
    try:
        j = json.loads(p.read_bytes().decode("utf-8"))
    except (ValueError, OSError):
        return {}
    return j if isinstance(j, dict) else {}


def _cf_params_dict(req: dict) -> dict:
    """The generation parameters of a request (model, duration, format, flags) plus a summary of the media roles."""
    prm = req.get("params") if isinstance(req.get("params"), dict) else req
    d = {k: str(prm[k]) for k in CF_PARAM_KEYS if k in prm and prm[k] not in (None, "")}
    roles = {}
    for m in prm.get("medias") or []:
        if isinstance(m, dict):
            roles[m.get("role", "?")] = roles.get(m.get("role", "?"), 0) + 1
    if roles:
        d["medias"] = ", ".join(f"{r}×{n}" if n > 1 else r for r, n in roles.items())
    return d


def _cf_params_text(s: str) -> dict:
    """'model=x · duration=15 · medias=a, b' -> {'model': 'x', ...} (a --params text)."""
    d = {}
    for part in re.split(r"\s+·\s+", s or ""):
        k, sep, v = part.partition("=")
        if sep and k.strip():
            d[k.strip()] = v.strip()
    return d


def _cf_uploads(rd) -> dict:
    """media id -> {'name', 'type'} from the run's uploads maps (what each uploaded file was)."""
    res = {}
    if not rd:
        return res
    for fn in ("uploads.json", "uploads-map.json"):
        p = rd / "30-assets" / fn
        if not p.is_file():
            continue
        try:
            j = json.loads(p.read_bytes().decode("utf-8"))
        except (ValueError, OSError):
            continue
        for name, v in (j.items() if isinstance(j, dict) else []):
            mid, typ = (v.get("media_id"), v.get("content_type", "")) if isinstance(v, dict) else (v, "")
            if mid and mid not in res:
                res[mid] = {"name": name, "type": typ}
    return res


def _cf_asset_path(rd, name, req):
    """The local file behind an uploaded input: the prepared source for a src-* video, else the staged asset."""
    if not rd or not name:
        return None
    sp = req.get("source_prepared") if isinstance(req, dict) else None
    if sp and name.lower().startswith("src-"):
        p = rd / str(sp)
        if p.is_file():
            return p
    for base in (rd / "30-assets" / "stage", rd / "30-assets", rd / "10-media"):
        p = base / name
        if p.is_file():
            return p
    return None


def _cf_ref(name: str) -> str:
    """A reference video (V20) or asset (A12) id read from a file name such as src-V20.mp4 or char-A12-head.jpg."""
    for pat in (r"(?<![A-Za-z0-9])(V\d{1,3})(?![0-9])", r"(?<![A-Za-z0-9])(A\d{1,4})(?![0-9])"):
        m = re.search(pat, name or "")
        if m:
            return m.group(1)
    return ""


def _cf_type(name: str) -> str:
    import mimetypes
    return mimetypes.guess_type(name or "")[0] or ""


def _cf_thumb(path, width: int = 200, t=None) -> str:
    """A small JPEG of an image, or of a video at time t, as a data URI ('' when it cannot be made)."""
    try:
        cmd = [find_tool("ffmpeg"), "-hide_banner", "-loglevel", "error", "-nostdin", "-y"]
        if t:
            cmd += ["-ss", f"{max(0.0, float(t)):.2f}"]
        cmd += ["-i", str(path), "-frames:v", "1", "-vf", f"scale={int(width)}:-2", "-pix_fmt", "yuvj420p", "-q:v", "7",
                "-f", "image2pipe", "-vcodec", "mjpeg", "-"]
        cp = subprocess.run(cmd, capture_output=True, timeout=90)
        if cp.returncode == 0 and cp.stdout:
            return "data:image/jpeg;base64," + base64.b64encode(cp.stdout).decode("ascii")
    except Exception:
        pass
    return ""


def _cf_inputs(req: dict, rd, thumbs: bool = True) -> list:
    """Every media the request carried: label (Image 2, Video 1), role, media id, file, type, V/A id, thumbnail."""
    prm = req.get("params") if isinstance(req.get("params"), dict) else req
    meaning = next((req[k] for k in ("medias_meaning", "media_meaning") if isinstance(req.get(k), dict)), {})
    ups = _cf_uploads(rd)
    counts, res = {}, []
    for m in (prm.get("medias") or []):
        if not isinstance(m, dict):
            continue
        role, mid = str(m.get("role", "?")), str(m.get("value", ""))
        counts[role] = counts.get(role, 0) + 1
        base = CF_ROLE_LABEL.get(role)
        label = f"{base} {counts[role]}" if base else role
        name = str(meaning.get(label) or ups.get(mid, {}).get("name") or "")
        item = {"label": label, "role": role, "media_id": mid, "name": name,
                "type": ups.get(mid, {}).get("type") or _cf_type(name), "ref": _cf_ref(name)}
        path = _cf_asset_path(rd, name, req)
        if not path and role == "video_references" and item["ref"].startswith("V"):
            path = _cf_video_file(item["ref"], rd, req, None)
        if path:
            item["path"] = str(path)
            if thumbs:
                th = _cf_thumb(path, 200)
                if th:
                    item["thumb"] = th
        res.append(item)
    return res


def _cf_inputs_from_text(text: str, rd) -> list:
    """'role: media id' lines (a --inputs text) as inputs; names come from the run's uploads map when known."""
    ups, counts, res = _cf_uploads(rd), {}, []
    for line in (text or "").splitlines():
        m = re.match(r"^\s*([a-z_]+)\s*:\s*(\S+)", line)
        if not m:
            continue
        role, mid = m.group(1), m.group(2)
        counts[role] = counts.get(role, 0) + 1
        base = CF_ROLE_LABEL.get(role)
        name = ups.get(mid, {}).get("name", "")
        res.append({"label": f"{base} {counts[role]}" if base else role, "role": role, "media_id": mid, "name": name,
                    "type": ups.get(mid, {}).get("type") or _cf_type(name), "ref": _cf_ref(name)})
    return res


def _cf_submission(rd, video, attempt) -> dict:
    """The run ledger row (state.json submissions) the agent marked `ledger set --flagged` for this video (and attempt):
    its job id and fingerprint. Never a row that was not marked: the attempt's later, accepted retry is not the flagged call."""
    sp = rd / "state.json" if rd else None
    if not sp or not sp.is_file() or not video:
        return {}
    try:
        st = json.loads(sp.read_bytes().decode("utf-8"))
    except (ValueError, OSError):
        return {}
    rows = [e for e in st.get("submissions", []) if e.get("flagged") and _cf_nn(_lane(e.get("video", ""))) == _cf_nn(video)]
    m = re.search(r"(\d+)\s*$", str(attempt or ""))
    if m:
        sel = [e for e in rows if e.get("attempt") == int(m.group(1))]
        rows = sel or rows
    return rows[-1] if rows else {}


def _cf_state_info(rd):
    """(mode, model) of the run: 'analyze-recreate', 'wan3_0_prime'."""
    sp = rd / "state.json" if rd else None
    if not sp or not sp.is_file():
        return "", ""
    try:
        st = json.loads(sp.read_bytes().decode("utf-8"))
    except (ValueError, OSError):
        return "", ""
    mode = str(st.get("mode") or "")
    sub = str(st.get("analyze_submode") or "")
    return (f"{mode}-{sub}" if mode and sub else mode), str(st.get("model") or "")


def _cf_tags(v) -> list:
    """Grouping tags: lower-case words joined by hyphens, no duplicates."""
    res = []
    for t in re.split(r"[,;]", v or ""):
        t = re.sub(r"[^a-z0-9]+", "-", t.strip().lower()).strip("-")
        if t and t not in res:
            res.append(t)
    return res


def _cf_mark_assets(entry: dict, wanted, thumbs: bool = True):
    """Mark the inputs the agent named (by label, media id, file name or V/A id). A name that matches no input is kept
    as given (assets_unmatched); an existing file path that matches none becomes an input of its own (an upload flag)."""
    trig = entry["trigger"]
    assets, unmatched = trig.setdefault("assets", []), trig.setdefault("assets_unmatched", [])
    for w in wanted or []:
        x = str(w).strip()
        if not x:
            continue
        hit = False
        for i in entry["inputs"]:
            nm = str(i.get("name") or "")
            if (str(i.get("label", "")).lower() == x.lower()
                    or (len(x) >= 8 and str(i.get("media_id", "")).lower().startswith(x.lower()))
                    or (len(x) >= 3 and nm and x.lower() in nm.lower())
                    or (i.get("ref") and x.upper() == str(i["ref"]).upper())):
                i["suspect"] = True
                hit = True
                if i["label"] not in assets:
                    assets.append(i["label"])
        if hit:
            continue
        p = Path(x)
        if p.is_file():
            it = {"label": p.name, "role": "upload", "media_id": "", "name": p.name, "type": _cf_type(p.name),
                  "ref": _cf_ref(p.name), "path": str(p), "suspect": True}
            if thumbs:
                th = _cf_thumb(p, 200)
                if th:
                    it["thumb"] = th
            entry["inputs"].append(it)
            assets.append(it["label"])
        elif x not in unmatched:
            unmatched.append(x)


def _cf_video_file(of: str, rd, req, output):
    """The video file a --part-of names: 'reference V10', 'clip a2' / 'output', or a path."""
    of = str(of or "")
    if not of:
        return None
    p = Path(of)
    if p.is_file():
        return p
    m = re.search(r"\bV(\d{1,3})\b", of, re.I)
    if m and rd:
        d = rd / "10-media" / f"V{int(m.group(1)):02d}"
        if not d.is_dir():
            d = rd / "10-media" / f"V{int(m.group(1))}"
        for cand in (d / "prepared" / "src.mp4", d / "own" / "own-silent.mp4", d / "own-silent.mp4", d / "own.mp4"):
            if cand.is_file():
                return cand
        vids = (sorted(d.glob("prepared/*.mp4")) + sorted(d.glob("own/*.mp4")) + sorted(d.glob("*.mp4"))) if d.is_dir() else []
        if vids:
            return vids[0]
    if re.search(r"output|clip|generated|result", of, re.I) and output and Path(str(output)).is_file():
        return Path(str(output))
    sp = req.get("source_prepared") if isinstance(req, dict) else None
    if sp and rd and re.search(r"reference|source", of, re.I) and (rd / str(sp)).is_file():
        return rd / str(sp)
    return None


def _cf_part(a, existing, rd, req, output, thumbs: bool = True):
    """The part of a video the agent suspects: which video, from/to seconds, a note, and a frame of it."""
    if not any([a.part_of, a.part_from is not None, a.part_to is not None, a.part_note]):
        return existing
    part = dict(existing or {})
    if a.part_of:
        part["of"] = a.part_of.strip()
    if a.part_from is not None:
        part["from"] = a.part_from
    if a.part_to is not None:
        part["to"] = a.part_to
    if a.part_note:
        part["note"] = a.part_note.strip()
    if thumbs and part.get("of"):
        vf = _cf_video_file(part["of"], rd, req, output)
        if vf:
            t0, t1 = part.get("from"), part.get("to")
            t = (t0 + t1) / 2.0 if (t0 is not None and t1 is not None) else (t0 if t0 is not None else 0)
            th = _cf_thumb(vf, 320, t)
            if th:
                part["frame"] = th
    return part


def _cf_compact(e: dict, full: bool = False) -> dict:
    """An entry without thumbnails (and with long texts cut, unless full) for the terminal."""
    c = json.loads(json.dumps(e, ensure_ascii=False))
    for i in c.get("inputs", []):
        i.pop("thumb", None)
    (c.get("trigger", {}).get("part") or {}).pop("frame", None)
    if not full:
        if len(c.get("prompt", "")) > 400:
            c["prompt"] = c["prompt"][:399] + "…"
        cl = c.get("cleared") or {}
        for k in ("prompt", "diff"):
            if len(cl.get(k, "")) > 400:
                cl[k] = cl[k][:399] + "…"
    return c


def cmd_caught_flag(a):
    """The flag record: ATP/caught_flags.html, a self-contained page (data + viewer with search, filters, grouping)
    of every prompt and video that made Higgsfield flag, refuse, withhold or reroute something during a run (a
    moderation block, a job that failed within seconds with no reason, an upload or element marked nsfw / ip_checking
    / failed, an output withheld, a preset notice instead of a job). Written only through this command; no step of a
    run and no agent reads it (command item 23). The script gathers what the run knows (the video, the request, every
    input with its file and thumbnail, the reference, the source segment, the ledger row); the agent writes the
    judgement (the reply, the suspected trigger, --asset, --prompt-span, --part-*, --tags).
      add        write a CF-nnn entry (--run and --video attach the request, inputs, plan, ledger row by themselves)
      set        update an entry: status (cleared needs the accepted request or job), notes, tags, assets, outcome
      list       entries as JSON for the terminal (filters; --full keeps the long texts)
      reconcile  the run's ledger (state.json) against the page: rows marked --flagged with no entry, and failed
                 rows with no job id or a flag-like note, for the agent to judge
      open       open the page in the default browser
      render     rewrite the page from its own data with the current viewer template"""
    if a.action == "open":
        if not CAUGHT_FLAGS.exists():
            _cf_save([])
        webbrowser.open(CAUGHT_FLAGS.as_uri())
        out({"ok": True, "file": str(CAUGHT_FLAGS), "opened": True})
    lock = FileLock(CAUGHT_FLAGS.with_suffix(".lock"))
    if a.action == "render":
        with lock:
            ents = _cf_load()
            _cf_save(ents)
        out({"ok": True, "file": str(CAUGHT_FLAGS), "entries": len(ents)})
    if a.action == "reconcile":
        if not a.run:
            fail("reconcile needs --run", 2)
        rd = _cf_run_dir(a.run)
        if not rd or not (rd / "state.json").exists():
            fail(f"state.json not found for run {a.run}", 2)
        led = json.loads((rd / "state.json").read_text(encoding="utf-8")).get("submissions", [])
        ents = [e for e in _cf_load() if rd.name in str(e.get("where", {}).get("run", "")) or str(a.run) in str(e.get("where", {}).get("run", ""))]
        def recorded(e):
            vid = _lane(e["video"])
            for c in ents:
                cw = c.get("where", {})
                same_v = re.sub(r"\D", "", str(cw.get("video", ""))).lstrip("0") == vid.lstrip("0")
                att = re.sub(r"\D", "", str(cw.get("attempt", "")))[-1:]
                jobs = str(c.get("job", "")) + " " + str(c.get("fingerprint", ""))
                if same_v and (att in ("", str(e.get("attempt"))) or (e.get("job_id") and e["job_id"] in jobs) or e["fingerprint"] in jobs):
                    return c["id"]
            return None
        marked, check = [], []
        for e in led:
            notes = [h.get("note") or "" for h in e.get("history", [])]
            row = {"video": e["video"], "attempt": e.get("attempt"), "status": e["status"], "job_id": e.get("job_id"),
                   "fingerprint": e["fingerprint"], "notes": [n[:200] for n in notes if n], "entry": recorded(e)}
            if e.get("flagged"):
                marked.append(row)
            elif e["status"] == "failed" and (not e.get("job_id") or any(CF_TERMS.search(n) for n in notes)):
                check.append(row)
        out({"ok": True, "run": rd.name, "entries_for_run": [c["id"] for c in ents],
             "flagged_unrecorded": [r for r in marked if not r["entry"]],
             "flagged_recorded": [r for r in marked if r["entry"]],
             "failed_to_judge": [r for r in check if not r["entry"]],
             "note": "flagged_unrecorded must each get `caught-flag add`; failed_to_judge rows are the agent's call "
                     "(a flag or a validation/credit error); mark a row's ledger entry with `ledger set --flagged`."})
    if a.action == "list":
        entries = _cf_load()
        def keep(e):
            w, t = e.get("where", {}), e.get("trigger", {})
            if a.mode and a.mode.lower() not in (str(w.get("mode", "")) + " any all").lower(): return False
            if a.model and a.model.lower() not in (str(w.get("model", "")) + " any all unknown").lower(): return False
            if a.kind and a.kind.lower() != str(e.get("kind", "")).lower(): return False
            if a.status and str(e.get("status", "")).lower() != a.status.lower(): return False
            if a.run and a.run.lower() not in str(w.get("run", "")).lower(): return False
            if a.video and re.sub(r"\D", "", a.video).lstrip("0") != re.sub(r"\D", "", str(w.get("video", ""))).lstrip("0"): return False
            if a.tags and not set(_cf_tags(a.tags)) <= set(t.get("tags", [])): return False
            if a.asset and " ".join(a.asset).lower() not in json.dumps([i for i in e.get("inputs", []) if i.get("suspect")] + t.get("assets_unmatched", []),
                                                                      ensure_ascii=False).lower(): return False
            if a.grep and a.grep.lower() not in json.dumps(_cf_compact(e, True), ensure_ascii=False).lower(): return False
            return True
        sel = [_cf_compact(e, a.full) for e in entries if keep(e)]
        out({"ok": True, "file": str(CAUGHT_FLAGS), "total": len(entries), "count": len(sel), "entries": sel})
    if a.action == "set":
        if not a.id:
            fail("--id CF-nnn is required", 2)
        with lock:
            entries = _cf_load()
            e = next((x for x in entries if x.get("id") == a.id), None)
            if e is None:
                fail(f"{a.id} not found", 1)
            if a.status == "cleared" and not (a.cleared_prompt or a.cleared_job):
                fail("--status cleared needs --cleared-prompt (the request .json or text that Higgsfield accepted) "
                     "or --cleared-job (the job that ran): a flag counts as cleared only once a request went through", 2)
            e.setdefault("trigger", {})
            e.setdefault("inputs", [])
            cl = e.setdefault("cleared", {})
            if a.cleared_prompt:
                cp = _cf_text_or_file(a.cleared_prompt)
                old = (e.get("prompt") or "").strip()
                if old and cp.strip() == old:
                    cl.update({"same_as_flagged": True})
                    cl.pop("prompt", None); cl.pop("diff", None)
                else:
                    cl.update({"same_as_flagged": False, "prompt": cp, "diff": _cf_sentence_diff(old, cp) if old else ""})
                prm = _cf_params_dict(_cf_request_json(a.cleared_prompt))
                if prm:
                    cl["params"] = prm
            if a.cleared_job:
                cl["job"] = a.cleared_job
            if a.note:
                e.setdefault("log", []).append({"at": now_iso(), "note": a.note.strip()})
            for key, val in (("status", a.status), ("outcome", a.outcome), ("changed", a.changed), ("rule", a.rule),
                             ("promoted_to", a.promoted_to)):
                if val:
                    e[key] = val
            if a.status == "cleared" and not a.outcome and not e.get("outcome"):
                e["outcome"] = "cleared: a changed request was accepted"
            if a.trigger:
                m = re.match(r"^\[(E|I)\]\s*", a.trigger.strip(), re.I)
                e["trigger"]["text"] = a.trigger.strip()[m.end():] if m else a.trigger.strip()
                if m:
                    e["trigger"]["evidence"] = m.group(1).upper()
            if a.tags:
                e["trigger"]["tags"] = e["trigger"].get("tags", []) + [t for t in _cf_tags(a.tags) if t not in e["trigger"].get("tags", [])]
            if a.asset:
                _cf_mark_assets(e, a.asset, not a.no_thumbs)
            if a.prompt_span:
                e["trigger"]["prompt_span"] = a.prompt_span.strip()
                e["trigger"]["span_in_prompt"] = a.prompt_span.strip().lower() in (e.get("prompt") or "").lower()
            rd = _cf_run_dir(e.get("where", {}).get("run"))
            e["trigger"]["part"] = _cf_part(a, e["trigger"].get("part"), rd, {}, e.get("where", {}).get("output"), not a.no_thumbs)
            if not e["trigger"]["part"]:
                e["trigger"].pop("part", None)
            e["updated"] = now_iso()
            _cf_save(entries)
        out({"ok": True, "id": a.id, "status": e.get("status"), "file": str(CAUGHT_FLAGS)})
    # add
    need = ("title", "kind", "response", "trigger")
    missing = [k for k in need if not getattr(a, k)]
    if missing:
        fail("missing " + ", ".join("--" + k for k in missing)
             + " (the verbatim Higgsfield response, the kind and the agent's suspected trigger are required;"
               " write 'none given' for a response that came back empty)", 2)
    tags = _cf_tags(a.tags)
    if not tags:
        fail("missing --tags: 1 to 4 grouping labels for the trigger (for example real-person-face, video-reference, "
             "celebrity-name, brand-name, protected-ip, nsfw-image, element, prompt-wording, preset-notice, output-withheld, "
             "unknown-trigger); the page groups and filters by them", 2)
    thumbs = not a.no_thumbs
    with lock:
        entries = _cf_load()
        ids = [int(re.sub(r"\D", "", x.get("id", "0")) or 0) for x in entries]
        cid = f"CF-{(max(ids) + 1) if ids else 1:03d}"
        rd = _cf_run_dir(a.run)
        given_json = bool(a.prompt) and str(a.prompt).lower().endswith(".json") and Path(str(a.prompt)).is_file()
        rq = Path(str(a.prompt)) if given_json else (_cf_request_file(rd, a.video, a.attempt) if rd and a.video else None)
        req = _cf_request_json(rq)
        prm = req.get("params") if isinstance(req.get("params"), dict) else req
        prompt = _cf_text_or_file(a.prompt) if (a.prompt and not given_json) else str(prm.get("prompt") or "").strip()
        params = _cf_params_text(a.params) if a.params else _cf_params_dict(req)
        inputs = _cf_inputs(req, rd, thumbs) if req else []
        if not inputs and a.inputs:
            inputs = _cf_inputs_from_text(_cf_text_or_file(a.inputs), rd)
        sub = _cf_submission(rd, a.video, a.attempt)
        mode_, model_ = _cf_state_info(rd)
        nn = _cf_nn(a.video)
        output = a.output or ""
        clip = a.clip or ""
        if not clip and str(req.get("clip") or "").lower() not in ("", "none", "null"):
            clip = str(req["clip"])
        plan = a.plan or (str(rd / "40-briefs" / f"video-{nn}-plan.md") if rd and (rd / "40-briefs" / f"video-{nn}-plan.md").is_file() else "")
        brief = str(rd / "40-briefs" / f"video-{nn}-brief.md") if rd and (rd / "40-briefs" / f"video-{nn}-brief.md").is_file() else ""
        where = {"run": rd.name if rd else (a.run or ""), "video": a.video or "", "attempt": a.attempt or "", "clip": clip,
                 "mode": a.mode or mode_, "model": a.model or model_ or str(prm.get("model") or ""), "tool": a.tool or "",
                 "stage": a.stage or "", "product": a.product or "", "reference": a.flagged_video or str(req.get("reference") or ""),
                 "segment": str(req.get("duration_basis") or ""), "plan": plan, "brief": brief, "request": str(rq) if rq else "",
                 "output": output}
        where = {k: v for k, v in where.items() if v not in ("", None)}
        trig_text, ev = a.trigger.strip(), "I"
        m = re.match(r"^\[(E|I)\]\s*", trig_text, re.I)
        if m:
            ev, trig_text = m.group(1).upper(), trig_text[m.end():]
        trig = {"text": trig_text, "evidence": ev, "cause": a.cause, "tags": tags}
        entry = {"id": cid, "created": a.date or now_iso(), "updated": now_iso(), "title": a.title.strip(), "source": a.source,
                 "status": a.status or "open", "kind": a.kind, "where": where, "response": _cf_text_or_file(a.response),
                 "job": a.job or str(sub.get("job_id") or ""), "fingerprint": a.fingerprint or str(sub.get("fingerprint") or ""),
                 "credits": a.credits or "", "prompt": prompt, "params": params, "inputs": inputs, "trigger": trig,
                 "changed": a.changed or "", "outcome": a.outcome or "", "cleared": {}, "rule": (a.rule or "").strip(),
                 "promoted_to": a.promoted_to or "", "log": []}
        _cf_mark_assets(entry, a.asset, thumbs)
        if a.prompt_span:
            trig["prompt_span"] = a.prompt_span.strip()
            trig["span_in_prompt"] = a.prompt_span.strip().lower() in prompt.lower()
        part = _cf_part(a, None, rd, req, output, thumbs)
        if part:
            trig["part"] = part
        if not trig["assets"]:
            trig.pop("assets")
        if not trig["assets_unmatched"]:
            trig.pop("assets_unmatched")
        entries.append(entry)
        _cf_save(entries)
    gaps = []
    if not (trig.get("assets") or trig.get("assets_unmatched")):
        gaps.append("asset: say which input you suspect with --asset (an 'Image 2' label, a media id, a file name or an A/V id)")
    if not trig.get("prompt_span"):
        gaps.append("prompt words: --prompt-span \"<the exact words>\" when a wording is suspected")
    if not trig.get("part"):
        gaps.append("video part: --part-of / --part-from / --part-to when a part of a video is suspected")
    out({"ok": True, "id": cid, "title": entry["title"], "file": str(CAUGHT_FLAGS),
         "attached": [k for k, v in (("request", rq), ("prompt", prompt), ("params", params), ("inputs", inputs), ("plan", plan),
                                     ("ledger row", sub), ("thumbnails", any(i.get("thumb") for i in inputs))) if v],
         "inputs": [{"label": i["label"], "name": i.get("name"), "suspect": bool(i.get("suspect"))} for i in inputs],
         "unmatched_assets": trig.get("assets_unmatched", []), "not_given": gaps,
         "note": "after the changed request is accepted: `caught-flag set --id %s --status cleared --cleared-prompt <request.json>`; "
                 "if the flag stays, `--status persistent`; `caught-flag open` shows the page" % cid})


def _px_span(spec: str, what: str) -> float:
    """'y0-y1' (pixel rows) or a plain pixel height."""
    s = (spec or "").strip()
    m = re.match(r"^\s*([0-9.]+)\s*-\s*([0-9.]+)\s*$", s)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        return abs(b - a)
    try:
        return float(s)
    except ValueError:
        fail(f"bad {what} {spec!r}: give pixel rows 'y0-y1' or a pixel height", 2)


def cmd_scale(a):
    """Size reckoning for a product in a frame (anomaly-catalog.md §2.7).

    Before generation (plan): `scale --product-cm 15.7 --distance 1.5 --lens 26` gives the fraction
    of the frame height and the pixel height the product should have at that depth, plus a table
    over the usual shot distances, so the prompt and a start frame can be built at the right size.
    After generation (QC): add `--product-px <y0-y1 | px>` measured on a full-resolution frame, and
    a neighbour of known size at (about) the same depth: `--ref-cm 22 --ref-px <y0-y1 | px>`
    (`--depth-ratio` = product distance / neighbour distance when they differ). The verdict compares
    the observed size with the expected one: within 15 % ok, 15-25 % a note, over 25 % regenerate.

    The distance is never assumed (CE-028): derive it from the frame (the surface the product stands
    on, a same-plane neighbour of known size) and say how with `--distance-basis "<how d was
    derived>"`. A verdict computed from --distance/--lens alone (no --ref-cm/--ref-px neighbour) is
    PROVISIONAL: the JSON carries `"provisional": true` and `"provisional_reason"`, `verdict` reads
    e.g. "regenerate (provisional: distance assumed)", `verdict_base` keeps the bare word, and the
    human line starts with "PROVISIONAL (distance assumed)". Given both estimates, an oversize verdict
    needs them to agree within --note-pct of each other; otherwise the verdict is "inconclusive".

    Geometry (approximate, 9:16 portrait, 35 mm-equivalent focal length f): the frame height covers
    36·d/f metres at distance d, so a product of height H fills H·f/(36·d) of the frame height."""
    if a.product_cm is None or a.product_cm <= 0:
        fail("--product-cm (the product's real height in cm, from the registry) is required", 2)
    H = a.product_cm / 100.0
    f = a.lens
    frame_h = a.frame_h
    if a.frame:
        im = media_summary(Path(a.frame))
        if im.get("display_height"):
            frame_h = int(im["display_height"])
    res = {"ok": True, "product_cm": a.product_cm, "lens_mm_eq": f, "frame_h_px": frame_h,
           "label": a.label or "product", "notes": []}
    # 1. expected size from distance + lens
    if a.distance:
        frac = H * f / (36.0 * a.distance)
        res["distance_m"] = a.distance
        res["expected_fraction_of_frame_height"] = round(frac, 4)
        res["expected_px"] = round(frac * frame_h, 1)
    shots = [("extreme close-up", 0.4), ("close-up", 0.7), ("medium close-up", 1.0), ("medium", 1.5),
             ("medium-wide", 2.5), ("wide", 4.0)]
    res["table"] = [{"shot": s, "distance_m": d, "fraction": round(H * f / (36.0 * d), 4),
                     "px": round(H * f / (36.0 * d) * frame_h, 1)} for s, d in shots]
    # 2. expected ratio to a neighbour of known size
    if a.ref_cm:
        ratio = (a.product_cm / a.ref_cm) / max(1e-6, a.depth_ratio)
        res["neighbour_cm"] = a.ref_cm
        res["depth_ratio"] = a.depth_ratio
        res["expected_ratio_to_neighbour"] = round(ratio, 3)
    # 3. observed
    verdicts = []
    if a.product_px:
        ppx = _px_span(a.product_px, "--product-px")
        res["observed_px"] = round(ppx, 1)
        res["observed_fraction_of_frame_height"] = round(ppx / frame_h, 4)
        if a.ref_cm and a.ref_px:
            rpx = _px_span(a.ref_px, "--ref-px")
            obs_ratio = ppx / max(1e-6, rpx)
            res["neighbour_px"] = round(rpx, 1)
            res["observed_ratio_to_neighbour"] = round(obs_ratio, 3)
            dev = obs_ratio / res["expected_ratio_to_neighbour"] - 1.0
            res["size_vs_neighbour"] = round(1.0 + dev, 3)
            verdicts.append(("vs neighbour", dev))
        if a.distance:
            dev = (ppx / frame_h) / res["expected_fraction_of_frame_height"] - 1.0
            res["size_vs_distance"] = round(1.0 + dev, 3)
            verdicts.append(("vs distance+lens", dev))
        if not verdicts:
            res["notes"].append("observed size given, but nothing to compare it with: add --ref-cm/--ref-px or --distance")
    if verdicts:
        worst = max(verdicts, key=lambda v: abs(v[1]))
        dev = worst[1]
        pct = abs(dev) * 100.0
        if pct <= a.ok_pct:
            verdict = "ok"
        elif pct <= a.note_pct:
            verdict = "note"
        else:
            verdict = "regenerate"
        res["deviation_pct"] = round(dev * 100.0, 1)
        res["deviation_basis"] = worst[0]
        res["verdict"] = verdict
        res["reading"] = (f"{res['label']} renders at {1 + dev:.2f}x its expected size "
                          f"({'too big' if dev > 0 else 'too small'} by {pct:.0f} %, {worst[0]})")
        if verdict == "regenerate":
            res["notes"].append("size is a regenerate reason; no post-fix can resize a product in the scene")
    # 4. provenance of the verdict (CE-028): a number from an assumed distance is provisional
    have_nb = "size_vs_neighbour" in res
    have_dist = "size_vs_distance" in res
    if a.distance:
        res["distance_basis"] = a.distance_basis or "not stated (assumed)"
    res["estimates"] = [k for k, h in (("neighbour ratio", have_nb), ("distance+lens fraction", have_dist)) if h]
    prov = None
    if verdicts and have_dist and not have_nb:
        prov = "distance assumed: no neighbour ratio (--ref-cm/--ref-px) to cross-check it"
    elif verdicts and have_dist and have_nb:
        lo, hi = sorted((res["size_vs_neighbour"], res["size_vs_distance"]))
        spread = (hi / max(1e-6, lo) - 1.0) * 100.0
        res["estimates_spread_pct"] = round(spread, 1)
        if spread > a.note_pct:
            res["verdict_base"] = res.get("verdict")
            res["verdict"] = "inconclusive"
            prov = (f"the two estimates disagree by {spread:.0f} % (neighbour {res['size_vs_neighbour']}x, "
                    f"distance {res['size_vs_distance']}x): re-derive the distance and the neighbour on the frame")
            res["notes"] = [n for n in res["notes"] if not n.startswith("size is a regenerate reason")]
            res["notes"].append("no oversize verdict while the estimates disagree; view the full-resolution frame and re-measure")
        elif not a.distance_basis:
            res["notes"].append("state --distance-basis: how the distance was derived from the frame")
    elif verdicts and have_nb and not have_dist:
        res["notes"].append("one estimate only (neighbour ratio): cross-check it with a frame fraction from a distance derived "
                            "from a different object or the surface (--distance --distance-basis)")
    if prov:
        res["provisional"] = True
        res["provisional_reason"] = prov
        if res.get("verdict") != "inconclusive":
            res["verdict_base"] = res.get("verdict")
            res["verdict"] = f"{res['verdict']} (provisional: distance assumed)"
            res["notes"].append("PROVISIONAL: not a regenerate reason, not a RESIDUAL FAILURE and not to be repeated until a "
                                "second estimate agrees; view the full-resolution frame first (anomaly-catalog.md 2.7)")
            res["notes"] = [n for n in res["notes"] if not n.startswith("size is a regenerate reason")]
        res["reading"] = f"PROVISIONAL ({prov}): " + res.get("reading", "")
    elif verdicts:
        res["provisional"] = False
    if a.distance and not a.product_px and not a.distance_basis:
        res["notes"].append("plan sketch only: the distance must be derived from the frame, not from the shot size (--distance-basis)")
    if verdicts and res.get("reading"):
        print(f"size: {res['reading']} -> {res['verdict']}", file=sys.stderr)
    if a.out:
        write_json(Path(a.out), res)
        res["file"] = a.out
    out(res)


def cmd_last_frame(a):
    """Hand-off frame for chaining clips: the exact LAST decoded frame of a clip (or the frame --back
    seconds earlier, when the final frames freeze, fade or morph) as a lossless PNG at native size.
    `frames --at` cannot do this: it stops short of the end and writes resized JPEGs."""
    try:
        n, fps = _count_frames(a.video)
    except RuntimeError as e:
        fail(str(e))
    if n < 1:
        fail("no decodable video frames", 1)
    back = int(round(max(0.0, a.back) * fps))
    k = n - 1 - back
    if k < 0:
        fail(f"--back {a.back} s goes before the first frame (clip has {n} frames at {fps:g} fps)", 2)
    dest = Path(a.out)
    if dest.suffix.lower() != ".png":
        fail("--out must be a .png file (lossless hand-off frame)", 2)
    dest.parent.mkdir(parents=True, exist_ok=True)
    cp = run([find_tool("ffmpeg"), "-nostdin", "-y", "-loglevel", "error", "-i", a.video, "-map", "0:v:0",
              "-vf", f"select=eq(n\\,{k})", "-fps_mode", "passthrough", "-frames:v", "1", str(dest)], timeout=900)
    if cp.returncode != 0 or not dest.exists():
        fail("ffmpeg failed: " + cp.stderr[-600:])
    im = media_summary(dest)
    res = {"ok": True, "file": str(dest), "frame_index": k, "total_frames": n, "fps": round(fps, 3),
           "t": round(k / fps, 3), "width": im.get("display_width"), "height": im.get("display_height"),
           "aspect": im.get("aspect")}
    if back:
        res["trim_end_s"] = round((k + 1) / fps, 3)
        res["note"] = (f"hand-off frame is {back} frame(s) before the end: trim the clip with "
                       f"`trim --end {res['trim_end_s']}` so it ends on this frame")
    out(res)


def cmd_concat(a):
    """Normalise clips to one format (WxH, fps, yuv420p, 48 kHz stereo AAC; silent track added when
    missing) and join them in the given order. Cuts are hard cuts: any transition must be planned.
    --seams marks each join: 'cut' (a planned hard cut, untouched) or 'continuous' (the next clip was
    chained from this clip's last frame): its first --seam-trim-frames frames, which repeat the
    hand-off frame, are dropped, and the audio gets a few-millisecond fade on both sides (no click)."""
    W, H = a.width, a.height
    joins = len(a.clips) - 1
    seams = [s.strip() for s in a.seams.split(",")] if a.seams else ["cut"] * joins
    if len(seams) != joins or any(s not in ("cut", "continuous") for s in seams):
        fail(f"--seams needs {joins} comma-separated value(s), each 'cut' or 'continuous'", 2)
    infos = [media_summary(c) for c in a.clips]
    rates = {round(i.get("fps") or 0, 2) for i in infos}
    fps = a.fps or (infos[0].get("fps") if len(rates) == 1 and infos[0].get("fps") else 30)
    work = Path(a.out).parent / "_concat"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)
    ff = find_tool("ffmpeg")
    parts = []
    for i, c in enumerate(a.clips):
        info = infos[i]
        if (info["display_width"], info["display_height"]) != (W, H):
            iw, ih = info["display_width"], info["display_height"]
            if abs(iw / ih - W / H) / (W / H) > 0.02:
                fail(f"clip {c} is {iw}x{ih}; conform it to {W}x{H} first (no stretching)", 2)
        p = work / f"part{i:02d}.mp4"
        after_cont = i > 0 and seams[i - 1] == "continuous"
        before_cont = i < joins and seams[i] == "continuous"
        head = a.seam_trim_frames if after_cont else 0
        t0 = head / (info.get("fps") or fps)
        vf = (f"trim=start_frame={head},setpts=PTS-STARTPTS," if head else "") + \
             f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1,fps={fps}"
        afl, d = [], a.audio_seam_fade_ms / 1000.0
        if head:
            afl.append(f"atrim=start={t0:.4f},asetpts=PTS-STARTPTS")
        part_dur = (info.get("duration_s") or 0) - t0
        if d > 0 and after_cont:
            afl.append(f"afade=t=in:st=0:d={d:.3f}")
        if d > 0 and before_cont and part_dur > 2 * d:
            afl.append(f"afade=t=out:st={part_dur - d:.3f}:d={d:.3f}")
        af = ["-af", ",".join(afl)] if afl else []
        if info.get("has_audio"):
            cmd = [ff, "-nostdin", "-y", "-loglevel", "error", "-i", c, "-vf", vf, *af, "-map", "0:v:0", "-map", "0:a:0",
                   *_encode_args(a.crf), "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "192k", str(p)]
        else:
            cmd = [ff, "-nostdin", "-y", "-loglevel", "error", "-i", c, "-f", "lavfi", "-i",
                   "anullsrc=channel_layout=stereo:sample_rate=48000", "-vf", vf, "-map", "0:v:0", "-map", "1:a:0",
                   "-shortest", *_encode_args(a.crf), "-c:a", "aac", "-b:a", "192k", str(p)]
        cp = run(cmd, timeout=3600)
        if cp.returncode != 0:
            fail(f"normalising {c} failed: " + cp.stderr[-500:])
        parts.append(p)
    lst = work / "list.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in parts), encoding="utf-8")
    cp = run([ff, "-nostdin", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy",
              "-movflags", "+faststart", str(Path(a.out).resolve())], cwd=str(work), timeout=3600)
    if cp.returncode != 0:
        fail("concat failed: " + cp.stderr[-500:])
    o = media_summary(a.out)
    shutil.rmtree(work, ignore_errors=True)
    out({"ok": True, "file": a.out, "duration_s": o.get("duration_s"), "size": f"{o['display_width']}x{o['display_height']}",
         "fps": o.get("fps"), "seams": seams})


# --------------------------------------------------------------------------- CapCut project helpers (Analyze Mode)

MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _capcut_store(explicit=None) -> Path:
    return Path(explicit or os.environ.get("CAPCUT_DRAFTS_DIR") or cfg_get("capcut.drafts_dir", "")
                or os.path.join(os.environ.get("LOCALAPPDATA", ""), "CapCut", "User Data", "Projects", "com.lveditor.draft"))


def cmd_capcut_name(a):
    """Free CapCut project name for one Analyze Mode video: DD_Mon_YYYY_vNN (e.g. 01_Oct_2026_v03), with
    -2, -3 … appended when that folder already exists in the drafts store. English month names, any locale."""
    try:
        d = dt.date.fromisoformat(a.date) if a.date else dt.date.today()
        nn = int(a.video)
    except ValueError:
        fail("--video must be a number and --date YYYY-MM-DD", 2)
    store = _capcut_store(a.store)
    if not store.is_dir():
        fail(f"CapCut drafts store not found: {store}", 2)
    base = f"{d.day:02d}_{MONTHS_EN[d.month - 1]}_{d.year}_v{nn:02d}"
    name, k = base, 1
    while (store / name).exists():
        k += 1
        name = f"{base}-{k}"
    out({"ok": True, "name": name, "path": str(store / name), "store": str(store)})


def cmd_capcut_prep(a):
    """Run right after capcut_clone_draft (empty:true) and before any other CapCut call on the new draft.
    The clone copies the template's identity sidecar (draft_meta_info.json: the TEMPLATE's draft id, name
    and folder) and its timeline_layout.json (the template's timeline id). Set both aside (*.atpbak), drop
    the template's build artefacts, and point the layout at the new timeline id, so that
    `capcut register --apply --materials` (after capcut_save) recreates a correct identity."""
    d = Path(a.draft)
    cp = d / "draft_content.json"
    if not cp.is_file():
        fail(f"not a CapCut draft (no draft_content.json): {d}", 2)
    if (d / ".locked").exists():
        fail("the draft is open in CapCut (.locked present): close CapCut first", 2)
    content = json.loads(cp.read_text(encoding="utf-8"))
    tid, name = content.get("id"), content.get("name")
    if not tid:
        fail("draft_content.json has no timeline id", 2)
    if name and name != d.name:
        fail(f"draft_content.json name {name!r} differs from the folder {d.name!r}: is this the fresh clone?", 2)
    moved = []
    for fn in ("draft_meta_info.json", "timeline_layout.json", "build-report.json", "build.log", "lint.json"):
        f = d / fn
        if f.exists():
            os.replace(f, d / (fn + ".atpbak"))
            moved.append(fn)
    write_json(d / "timeline_layout.json", {"dockItems": [{"dockIndex": 0, "ratio": 1, "timelineIds": [tid],
                                                           "timelineNames": ["Timeline 01"]}], "layoutOrientation": 1})
    out({"ok": True, "draft": str(d), "timeline_id": tid, "name": name, "set_aside": moved,
         "next": "capcut_read_timeline → edits → capcut_validate → capcut_save, then: atp.py capcut-repair "
                 "--draft \"<draft>\" --preview \"<run>/60-outputs/video-NN/capcut-preview.mp4\""})


def _capcut_cli() -> str:
    exe = shutil.which("capcut")
    if exe:
        return exe
    for cand in (os.path.join(os.environ.get("APPDATA", ""), "npm", "capcut.cmd"),):
        if os.path.exists(cand):
            return cand
    fail("capcut-cli not found on PATH (npm i -g capcut-cli)", 1)


def _last_json(text: str):
    for line in reversed((text or "").strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except Exception:
                continue
    return None


def cmd_capcut_repair(a):
    """After every capcut_save: the house text style on every text layer (capcut-text-style), then
    `capcut register --apply --materials` (identity from draft_content.json,
    the media list CapCut needs, the store index), `capcut sync-timelines --nested --apply` (the nested
    timeline copy CapCut 9.x reads first) and `capcut lint`. register rewrites the store's SHARED
    root_meta_info.json, so all three run under one machine-wide lock: production agents assemble their
    projects in parallel. --preview then renders capcut-cli's low-res proxy (outside the lock)."""
    d = Path(a.draft)
    if not (d / "draft_content.json").is_file():
        fail(f"not a CapCut draft (no draft_content.json): {d}", 2)
    cli = _capcut_cli()
    if (d / ".locked").exists() or _capcut_running():
        out({"ok": False, "draft": str(d), "steps": [],
             "action": "CapCut is running: close it and run this again (nothing was changed)"}, 1)
    lock = Path(cfg_get("runs_root", str(Path(__file__).resolve().parent.parent / "runs"))) / ".capcut-store.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    steps = [{"step": "text-style", "exit": 0, "result": _text_style_pass(d, write=True)}]   # before sync-timelines
    with FileLock(lock, timeout=900):
        for name, args in (("register", ["register", str(d), "--apply", "--materials"]),
                           ("sync-timelines", ["sync-timelines", str(d), "--nested", "--apply"]),
                           ("lint", ["lint", str(d)])):
            cp = run([cli, *args], timeout=900)
            steps.append({"step": name, "exit": cp.returncode,
                          "result": _last_json(cp.stdout) or (cp.stdout or "").strip()[-800:],
                          "stderr": (cp.stderr or "").strip()[-400:]})
            if name != "lint" and cp.returncode != 0:
                break
    codes = {s["step"]: s["exit"] for s in steps}
    ok = codes.get("register") == 0 and codes.get("sync-timelines") == 0 and codes.get("lint") in (0, 1)
    res = {"ok": ok, "draft": str(d), "steps": steps}
    if not ok:
        res["action"] = ("a step refused or lint found errors: CapCut running → close it and run this again; "
                         "lint errors → fix the timeline through the MCP, capcut_save, then run this again")
    elif a.preview:
        Path(a.preview).parent.mkdir(parents=True, exist_ok=True)
        cp = run([cli, "render", str(d), "--out", a.preview, "--burn-captions"], timeout=1800)
        res["preview"] = {"exit": cp.returncode, "file": a.preview if cp.returncode == 0 else None,
                          "result": _last_json(cp.stdout), "stderr": (cp.stderr or "").strip()[-400:]}
    out(res, 0 if ok else 1)


# --------------------------------------------------------------------------- CapCut house text style

HOUSE_TEXT_DEFAULT = {"font": "System", "size": 10, "fill": "#FFFFFF",
                      "stroke": {"color": "#000000", "width": 0.08}}
# material-level keys that a CapCut font / preset choice sets (copied by --learn from a text the user styled)
_TEXT_STYLE_KEY = re.compile(r"^(font_|fonts$|text_color$|text_alpha$|has_border$|border_|has_shadow$|shadow_|"
                             r"background_|bold_width$|italic_degree$|underline|letter_spacing$|line_spacing$|"
                             r"preset_|style_name$|check_flag$|use_effect_default_color$|text_preset_resource_id$|"
                             r"global_alpha$|ktv_color$|effect_style$)")


def _house_text_style() -> dict:
    st = {**HOUSE_TEXT_DEFAULT, **(cfg_get("capcut.text_style") or {})}
    st["stroke"] = {**HOUSE_TEXT_DEFAULT["stroke"], **(st.get("stroke") or {})}
    return st


def _capcut_system_font() -> str:
    """CapCut's 'System' font, the one a fresh text gets: <CapCut>/Apps/<newest version>/Resources/Font/SystemFont/en.ttf."""
    found = []
    for d in (Path(os.environ.get("LOCALAPPDATA", "")) / "CapCut" / "Apps").glob("*"):
        f = d / "Resources" / "Font" / "SystemFont" / "en.ttf"
        if f.is_file():
            try:
                found.append((tuple(int(x) for x in d.name.split(".")), f))
            except ValueError:
                continue
    return str(max(found)[1]).replace("\\", "/") if found else ""


def _capcut_running() -> bool:
    if os.name != "nt":
        return False
    try:
        return "capcut.exe" in (run(["tasklist", "/FI", "IMAGENAME eq CapCut.exe", "/NH"], timeout=30).stdout or "").lower()
    except Exception:
        return False


def _hex_rgb(h: str) -> list:
    h = h.lstrip("#")
    return [round(int(h[i:i + 2], 16) / 255, 6) for i in (0, 2, 4)]


def _house_text_material(m: dict, st: dict, font_path: str) -> bool:
    """Rewrite one text material to the house style; True when it changed. The text, its ranges, position
    and timing stay; font, size, fill, outline, shadow, background and preset fields become the house ones."""
    before = json.dumps(m, sort_keys=True)
    size = float(st["size"])
    learned = st.get("learned") or {}
    lmat, lsty = learned.get("material") or {}, learned.get("style")
    if lmat:
        for k, v in lmat.items():
            m[k] = json.loads(json.dumps(v))
    else:
        m.update({"font_name": "", "font_title": "none", "font_id": "", "font_resource_id": "",
                  "font_category_id": "", "font_category_name": "", "font_source_platform": 0,
                  "font_team_id": "", "font_url": "", "fonts": [],
                  "text_color": st["fill"], "text_alpha": 1.0, "has_border": True,
                  "border_color": st["stroke"]["color"], "border_width": st["stroke"]["width"], "border_alpha": 1.0,
                  "has_shadow": False, "background_alpha": 0.0, "background_style": 0})
    m["font_path"] = font_path
    m["font_size"] = size
    try:
        content = json.loads(m.get("content") or "{}")
    except Exception:
        content = {}
    text = content.get("text", "")
    styles = []
    for old in (content.get("styles") or [{"range": [0, len(text)]}]):
        if lsty is not None:
            ns = json.loads(json.dumps(lsty))
        else:
            ns = {"fill": {"alpha": 1.0, "content": {"render_type": "solid",
                                                     "solid": {"alpha": 1.0, "color": _hex_rgb(st["fill"])}}},
                  "strokes": [{"content": {"render_type": "solid",
                                           "solid": {"alpha": 1.0, "color": _hex_rgb(st["stroke"]["color"])}},
                               "width": st["stroke"]["width"]}],
                  "useLetterColor": True}
        ns["range"] = old.get("range", [0, len(text)])
        ns["size"] = size
        ns["font"] = {"id": "", "path": font_path}
        styles.append(ns)
    content["styles"] = styles
    m["content"] = json.dumps(content, ensure_ascii=False, separators=(",", ":"))
    return json.dumps(m, sort_keys=True) != before


def _draft_contents(d: Path) -> list:
    """The root draft_content.json plus CapCut 9.x's nested timeline copies."""
    return [p for p in [d / "draft_content.json", *sorted((d / "Timelines").glob("*/draft_content.json"))] if p.is_file()]


def _text_style_pass(d: Path, write: bool) -> dict:
    st = _house_text_style()
    font = _capcut_system_font() or (st.get("learned") or {}).get("font_path") or ""
    if not font:
        fail("CapCut's System font was not found (<LOCALAPPDATA>/CapCut/Apps/<version>/Resources/Font/SystemFont/en.ttf)", 1)
    files, changed_ids = [], set()
    for p in _draft_contents(d):
        content = json.loads(p.read_text(encoding="utf-8"))
        changed = [m.get("id") for m in content.get("materials", {}).get("texts", [])
                   if _house_text_material(m, st, font)]
        changed_ids.update(changed)
        if changed and write:
            shutil.copyfile(p, p.with_name(p.name + ".textstyle.bak"))
            write_text(p, json.dumps(content, ensure_ascii=False))
        files.append({"file": str(p), "texts_off_style": len(changed)})
    return {"font": font, "size": st["size"], "preset": "learned" if st.get("learned") else "default (not calibrated)",
            "files": files, "texts_off_style": len(changed_ids), "written": bool(write and changed_ids)}


def _learn_text_style(d: Path, which, replace: bool = False) -> dict:
    """Copy the exact style of a text the user styled once in CapCut (font System, the wanted preset).
    A learned preset the user locked (capcut.text_style.locked) is only replaced with --replace."""
    cur = cfg_get("capcut.text_style") or {}
    if cur.get("learned") and cur.get("locked") and not replace:
        fail(f"the house text preset is locked (learned from {cur['learned'].get('from')}); the user chose it for "
             "every video. Pass --replace only when the user asks for a different preset", 3)
    src = max(_draft_contents(d), key=lambda p: p.stat().st_mtime, default=None)
    if not src:
        fail(f"not a CapCut draft (no draft_content.json): {d}", 2)
    content = json.loads(src.read_text(encoding="utf-8"))
    texts = content.get("materials", {}).get("texts", [])
    if not texts:
        fail("no text in that draft: add one text in CapCut, pick the preset, close CapCut, then --learn again", 2)
    if which is not None:
        if not 1 <= which <= len(texts):
            fail(f"--text must be 1..{len(texts)}", 2)
        m = texts[which - 1]
    else:
        withp = [t for t in texts if t.get("preset_id") or t.get("preset_name") or t.get("style_name")]
        if len(withp) == 1 or len(texts) == 1:
            m = (withp or texts)[0]
        else:
            listing = []
            for i, t in enumerate(texts, 1):
                try:
                    txt = json.loads(t.get("content") or "{}").get("text", "")
                except Exception:
                    txt = ""
                listing.append(f"{i}: {txt[:30]!r}")
            fail("several texts in that draft; pick one with --text N: " + "; ".join(listing), 2)
    mat = {k: v for k, v in m.items() if _TEXT_STYLE_KEY.match(k) and k not in ("font_path", "font_size")}
    if m.get("preset_has_set_alignment"):
        mat["alignment"] = m.get("alignment")
    try:
        sty = dict((json.loads(m.get("content") or "{}").get("styles") or [{}])[0])
    except Exception:
        sty = {}
    for k in ("range", "size", "font"):
        sty.pop(k, None)
    refs = []
    for tr in content.get("tracks", []):
        for seg in tr.get("segments", []):
            if seg.get("material_id") == m.get("id"):
                for rid in seg.get("extra_material_refs", []):
                    for kind, lst in content.get("materials", {}).items():
                        if isinstance(lst, list):
                            for x in lst:
                                if isinstance(x, dict) and x.get("id") == rid:
                                    refs.append({"kind": kind, "type": x.get("type")})
    learned = {"from": f"{d.name} / text {m.get('id')}", "at": now_iso(), "font_path": m.get("font_path"),
               "material": mat, "style": sty, "segment_refs": refs}
    cfg = load_config()
    cfg.setdefault("capcut", {}).setdefault("text_style", {})["learned"] = learned
    write_text(CONFIG_PATH, json.dumps(cfg, ensure_ascii=False, indent=2) + "\n")
    extra = [r for r in refs if r["kind"] in ("effects", "text_templates") or "text" in str(r["type"]).lower()]
    return {"learned_from": learned["from"], "preset_fields": {k: v for k, v in mat.items() if k.startswith("preset_")},
            "style_keys": sorted(sty), "segment_refs": refs,
            "warning": ("the preset also uses extra material(s) " + json.dumps(extra) + ": tell Claude, they are not copied yet")
            if extra else None}


def cmd_capcut_text_style(a):
    """House style for every CapCut text layer: font System, size 10, and the user's chosen preset, stored in
    config.json (capcut.text_style.learned; locked). Rewrites every text material of the draft (root and nested
    timeline copies); capcut-repair runs it before register/sync. --check only reports. --learn copies the
    exact preset fields from a text the user styled once in CapCut; a locked preset needs --replace."""
    d = Path(a.draft)
    if not (d / "draft_content.json").is_file():
        fail(f"not a CapCut draft (no draft_content.json): {d}", 2)
    if a.learn:
        out({"ok": True, **_learn_text_style(d, a.text, a.replace)})
    if not a.check and ((d / ".locked").exists() or _capcut_running()):
        fail("CapCut is running: close it, then run this again", 3)
    res = _text_style_pass(d, write=not a.check)
    out({"ok": True, "draft": str(d), **res}, 1 if a.check and res["texts_off_style"] else 0)


def cmd_strip_inserts(a):
    """The reference minus its inserts (memes, film/TV snippets, reaction images from other sources), in
    ONE pass at the original resolution and fps: <out>/own.mp4 (original audio kept), <out>/own-silent.mp4
    (the copy to upload) and <out>/map.json (where each insert goes back: its split point in the stripped
    timeline, its source in/out). Used by Recreate (the edit source) and for split-point maths."""
    info = media_summary(a.video)
    dur = info.get("duration_s") or 0
    spans = []
    for s in a.inserts.split(","):
        m = re.match(r"^\s*([0-9.]+)\s*-\s*([0-9.]+)\s*$", s)
        if not m:
            fail(f"bad insert range {s!r}; use start-end in seconds, comma-separated", 2)
        t0, t1 = float(m.group(1)), min(float(m.group(2)), dur)
        if not (0 <= t0 < t1):
            fail(f"insert {s!r} is outside the video (0-{dur:.3f} s)", 2)
        spans.append((t0, t1))
    spans.sort()
    for (x0, x1), (y0, y1) in zip(spans, spans[1:]):
        if y0 < x1:
            fail(f"inserts overlap: {x0}-{x1} and {y0}-{y1}", 2)
    od = Path(a.out)
    od.mkdir(parents=True, exist_ok=True)
    expr = "+".join(f"gte(t\\,{t0:.4f})*lt(t\\,{t1:.4f})" for t0, t1 in spans)
    ff = find_tool("ffmpeg")
    own, silent = od / "own.mp4", od / "own-silent.mp4"
    cmd = [ff, "-nostdin", "-y", "-loglevel", "error", "-i", a.video, "-map", "0:v:0",
           "-vf", f"select=not({expr}),setpts=N/FRAME_RATE/TB"]
    if info.get("has_audio"):
        cmd += ["-map", "0:a:0", "-af", f"aselect=not({expr}),asetpts=N/SR/TB", "-c:a", "aac", "-b:a", "192k"]
    cmd += [*_encode_args(a.crf), str(own)]
    cp = run(cmd, timeout=3600)
    if cp.returncode != 0:
        fail("ffmpeg failed: " + cp.stderr[-600:])
    cp = run([ff, "-nostdin", "-y", "-loglevel", "error", "-i", str(own), "-map", "0:v:0", "-c:v", "copy", "-an",
              str(silent)], timeout=600)
    if cp.returncode != 0:
        fail("ffmpeg (silent copy) failed: " + cp.stderr[-600:])
    removed, inserts = 0.0, []
    for i, (t0, t1) in enumerate(spans, 1):
        inserts.append({"insert": i, "source_in": round(t0, 3), "source_out": round(t1, 3),
                        "duration": round(t1 - t0, 3), "split_at": round(t0 - removed, 3)})
        removed += t1 - t0
    o = media_summary(own)
    mp = {"source": str(a.video), "source_duration": round(dur, 3), "own_duration": o.get("duration_s"),
          "expected_own_duration": round(dur - removed, 3), "inserts": inserts,
          "own": str(own), "own_silent": str(silent)}
    write_json(od / "map.json", mp)
    out({"ok": True, **mp, "map": str(od / "map.json")})


# --------------------------------------------------------------------------- submission ledger (anti-duplicate)

LEDGER_OPEN = {"pending", "submitted", "unknown"}          # outcome not final yet → blocks new submissions
LEDGER_DONE_OK = {"completed", "accepted"}                  # a finished, usable job for this exact request


def _fingerprint(req: dict) -> str:
    params = dict(req.get("params", req))
    params.pop("get_cost", None)
    blob = json.dumps(params, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:20]


def _lane(video) -> str:
    """Ledger lane = the video number: '03', '03-c2' (clip 2) and '03-frame' share lane '03'."""
    return str(video).split("-")[0]


def cmd_ledger(a):
    """Deterministic guard around every paid Higgsfield generation (generate_video, and generate_image for
    start frames). state.json is written under a lock, because production agents run in parallel.
    begin  : refuses (exit 3) when
             - this video's lane already has an open submission (pending/submitted/unknown): one job in
               flight per video;
             - the run already has `production.max_parallel_jobs` open submissions (config, default 5;
               `--max-open 1` restores strictly one job per run);
             - this exact request already produced a completed/accepted job, or failed twice.
             Otherwise it records a 'pending' entry. Call it immediately BEFORE the generation call.
    set    : record the job id / outcome right AFTER the call and after polling
             (submitted | unknown | completed | failed | accepted | rejected | superseded).
    show   : list entries (optionally one video)."""
    p = Path(a.run) / "state.json"
    if not p.exists():
        fail(f"state.json not found in {a.run}", 2)
    if a.action == "show":
        led = json.loads(p.read_text(encoding="utf-8")).get("submissions", [])
        rows = [e for e in led if not a.video or e["video"] == a.video]
        out({"ok": True, "entries": rows, "open": [e for e in rows if e["status"] in LEDGER_OPEN]})
    with FileLock(p.with_name("state.json.lock")):
        _ledger_write(a, p)


def _ledger_write(a, p: Path):
    st = json.loads(p.read_text(encoding="utf-8"))
    led = st.setdefault("submissions", [])
    if a.action == "begin":
        if not a.request or not a.video:
            fail("begin needs --video and --request", 2)
        req = json.loads(Path(a.request).read_text(encoding="utf-8"))
        fp = _fingerprint(req)
        lane = a.lane or _lane(a.video)
        open_all = [e for e in led if e["status"] in LEDGER_OPEN]
        open_lane = [e for e in open_all if (e.get("lane") or _lane(e["video"])) == lane]
        if open_lane:
            out({"ok": False, "blocked": "open submission in this video's lane", "open": open_lane,
                 "action": "resolve it first: jobs_wait on its job_id, or for 'pending'/'unknown' without a "
                           "job id check show_generations/transactions — never submit again blindly"}, 3)
        cap = a.max_open or int(cfg_get("production.max_parallel_jobs", 5))
        if len(open_all) >= cap:
            out({"ok": False, "blocked": "parallel cap", "open": open_all, "cap": cap,
                 "action": f"{cap} jobs are already in flight in this run: wait (jobs_wait) until one finishes, "
                           "then begin again — never submit past the cap"}, 3)
        failed = [e for e in led if e["fingerprint"] == fp and e["status"] == "failed"]
        if len(failed) >= 2:
            out({"ok": False, "blocked": "failed twice", "failed": failed,
                 "action": "this exact request failed twice — diagnose and change it, or report the failure"}, 3)
        dup = [e for e in led if e["fingerprint"] == fp and e["status"] in LEDGER_DONE_OK]
        if dup and not a.allow_repeat:
            out({"ok": False, "blocked": "duplicate request", "existing": dup[-1],
                 "action": "reuse that job's result; change the request (e.g. the user's revision) to make "
                           "a new attempt, or pass --allow-repeat only on an explicit user request"}, 3)
        entry = {"video": a.video, "lane": lane, "attempt": a.attempt, "fingerprint": fp, "status": "pending",
                 "job_id": None, "model": (req.get("params", req)).get("model"),
                 "request_file": str(Path(a.request).resolve()), "created": now_iso(), "history": []}
        led.append(entry)
        st["updated"] = now_iso()
        write_json(p, st)
        out({"ok": True, "fingerprint": fp, "entry": entry})
    elif a.action == "set":
        if not a.fingerprint and not a.job:
            fail("set needs --fingerprint or --job", 2)
        hits = [e for e in led if (a.fingerprint and e["fingerprint"] == a.fingerprint)
                or (a.job and e.get("job_id") == a.job)]
        if not hits:
            fail("no ledger entry matches", 2)
        e = hits[-1]
        e["history"].append({"at": now_iso(), "from": e["status"], "to": a.status, "note": a.note})
        e["status"] = a.status
        if a.job:
            e["job_id"] = a.job
        if a.flagged:
            e["flagged"] = True
        st["updated"] = now_iso()
        write_json(p, st)
        out({"ok": True, "entry": e, **({"reminder": "flagged: record it now with `caught-flag add` (the verbatim response, your suspected trigger and --tags; "
                                                       "--asset, --prompt-span and --part-* when you can tell what caused it), then change the request"} if a.flagged else {})})


def cmd_open(a):
    """Open a finished video in the user's default player so they can review it."""
    f = Path(a.file)
    if not f.exists():
        fail(f"file not found: {f}", 2)
    if a.dry_run:
        out({"ok": True, "would_open": str(f.resolve())})
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(f.resolve()))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(f)])
        else:
            subprocess.Popen(["xdg-open", str(f)])
        out({"ok": True, "opened": str(f.resolve())})
    except Exception as e:
        fail(f"could not open: {e}", 1, file=str(f.resolve()))


# --------------------------------------------------------------------------- model menu

OPS_SHORT = {"t2v": "text", "start_frame": "first-frame", "end_frame": "last-frame", "image_refs": "image-refs",
             "video_refs": "video-refs", "audio_refs": "audio-refs", "elements": "Elements",
             "video_edit": "video-edit", "video_extension": "extend", "object_replace": "object-swap",
             "motion_transfer": "motion-transfer", "multi_shot": "multi-shot"}


def _edit_fit(e: dict) -> str:
    kind = (e.get("edit_kind") or "none").lower()
    if kind.startswith("pixel-preserving"):
        return "✓ edits video"
    if kind.startswith("recreate"):
        return "≈ recreates from video ref"
    if kind.startswith("motion-transfer"):
        return "↔ motion transfer"
    if kind.startswith("video continuation"):
        return "≈ continues/recreates"
    return "✗ frames only"


def cmd_model_menu(a):
    """Print EVERY available video model as one numbered table (pinned models first), plus a JSON line
    with the quick picks. Live catalog ids (from models_explore) mark availability and add models that
    have no guide yet."""
    idx = json.loads((ATP_HOME / "models" / "index.json").read_text(encoding="utf-8"))
    models = idx["models"]
    menu = idx.get("menu", {})
    order = [m for m in menu.get("order", []) if m in models] + [m for m in models if m not in menu.get("order", [])]
    pinned = set(menu.get("pinned", []))
    live = None
    if a.live_ids:
        live = {x.strip() for x in re.split(r"[,\s]+", a.live_ids) if x.strip()}
    elif a.live_file:
        data = json.loads(Path(a.live_file).read_text(encoding="utf-8"))
        items = data.get("items", data) if isinstance(data, dict) else data
        live = {it["id"] if isinstance(it, dict) else str(it) for it in items}
    skip = set(idx.get("not_selectable", {}).get("utility", [])) | {"higgsfield_preset"}
    rows, unavailable, n = [], [], 0
    for mid in order:
        e = models[mid]
        if live is not None and mid not in live:
            unavailable.append(mid)
            continue
        n += 1
        ops = [OPS_SHORT[o] for o in e.get("operations", []) if o in OPS_SHORT]
        dur = e.get("duration_s")
        dur = "/".join(map(str, dur)) if isinstance(dur, list) else str(dur)
        note = e.get("status", "active")
        note = "" if note == "active" else f"[{note}] "
        best = (e.get("best_for") or "")
        rows.append({"n": n, "id": mid, "star": mid in pinned, "name": e.get("name", mid),
                     "provider": e.get("provider", ""), "ops": ", ".join(ops), "dur": dur[:34],
                     "audio": "yes" if "native_audio" in e.get("operations", []) else "—",
                     "analyze": "✓" if "analyze" in e.get("modes", []) else "edit-only",
                     "edit": _edit_fit(e), "note": (note + best)[:90]})
    for mid in sorted((live or set()) - set(models) - skip):
        n += 1
        rows.append({"n": n, "id": mid, "star": False, "name": mid, "provider": "?", "ops": "see live catalog",
                     "dur": "?", "audio": "?", "analyze": "?", "edit": "?",
                     "note": "no guide yet — conservative fallback guide"})
    mode = a.mode or "analyze"
    lines = [f"**All available video models** ({len(rows)}) — mode: {mode}. ★ = pinned. Reply with a number or a name.",
             "", "| # | Model | id | What it can do | Length (s) | Audio | Analyze | Edit | Notes |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        star = "★ " if r["star"] else ""
        lines.append(f"| {r['n']} | {star}{r['name']} ({r['provider']}) | `{r['id']}` | {r['ops']} | {r['dur']} | "
                     f"{r['audio']} | {r['analyze']} | {r['edit']} | {r['note']} |")
    if unavailable:
        lines += ["", "Not in the live catalog right now: " + ", ".join(f"`{u}`" for u in unavailable)]
    print("\n".join(lines))
    if mode == "edit":   # true video editors first, then motion transfer, then recreation
        rank = {"✓": 0, "↔": 1, "≈": 2}
        fit = sorted([r for r in rows if r["edit"][:1] in rank], key=lambda r: (rank[r["edit"][:1]], r["n"]))
    else:
        fit = [r for r in rows if r["analyze"] == "✓"]
    quick = [r["id"] for r in rows if r["star"]] + [r["id"] for r in fit if not r["star"]]
    out({"ok": True, "count": len(rows), "quick_picks": quick[:4],
         "numbers": {str(r["n"]): r["id"] for r in rows}, "unavailable": unavailable})


def cmd_model_entry(a):
    """Print one model's entry of models/index.json with its guide path and section folder, so the 40 KB index is never
    read whole. An id with no guide returns the fallback guide."""
    idx = json.loads((ATP_HOME / "models" / "index.json").read_text(encoding="utf-8"))
    e = idx["models"].get(a.id)
    if e is None:
        fail(f"unknown model id {a.id}", known=sorted(idx["models"]))
    guide = e.get("guide") or idx.get("fallback_guide")
    g = ATP_HOME / guide
    sec = g.with_suffix("")
    out({"ok": True, "id": a.id, "entry": e, "guide": guide, "guide_exists": g.is_file(),
         "sections_dir": str(sec).replace("\\", "/") if sec.is_dir() else None,
         "higgsfield_guide": idx.get("higgsfield_guide"), "fixed_output": idx.get("fixed_output")})


# --------------------------------------------------------------------------- CLI

def main():
    ap = argparse.ArgumentParser(prog="atp.py", description=__doc__.split("\n\n")[0])
    sp = ap.add_subparsers(dest="cmd", required=True)

    p = sp.add_parser("new-run"); p.add_argument("--mode", choices=["analyze", "edit"], required=True)
    p.add_argument("--source", nargs="*", help="analyze: the references folder; edit: video file(s) or folder")
    p.add_argument("--assets", nargs="*", help="analyze: ALL client asset files/folders, given up front")
    p.add_argument("--examples", nargs="*", help="optional, both modes: your own finished videos (study only)")
    p.add_argument("--slug"); p.add_argument("--runs-root"); p.set_defaults(fn=cmd_new_run)

    p = sp.add_parser("state"); p.add_argument("--run", required=True)
    p.add_argument("action", choices=["get", "set", "append"]); p.add_argument("pairs", nargs="*")
    p.set_defaults(fn=cmd_state)

    p = sp.add_parser("inventory"); p.add_argument("paths", nargs="+", help="files and/or folders")
    p.add_argument("--run"); p.add_argument("--as", dest="role", choices=["references", "sources", "assets", "examples"],
                                            default="references")
    p.add_argument("--scope", help="asset scope: 'project' (analyze, default) or e.g. 'video-01' (edit)")
    p.add_argument("--max-depth", type=int); p.set_defaults(fn=cmd_inventory)

    p = sp.add_parser("prep-assets"); p.add_argument("--run", required=True); p.add_argument("--scope")
    p.set_defaults(fn=cmd_prep_assets)

    p = sp.add_parser("ledger"); p.add_argument("action", choices=["begin", "set", "show"])
    p.add_argument("--run", required=True); p.add_argument("--video"); p.add_argument("--attempt", type=int, default=1)
    p.add_argument("--request", help="the request JSON about to be submitted (begin)")
    p.add_argument("--fingerprint"); p.add_argument("--job")
    p.add_argument("--status", choices=["submitted", "unknown", "completed", "failed", "accepted", "rejected", "superseded"])
    p.add_argument("--note"); p.add_argument("--allow-repeat", action="store_true")
    p.add_argument("--flagged", action="store_true", help="set: mark this submission as flagged/refused by Higgsfield (then `caught-flag add`)")
    p.add_argument("--lane", help="lane override (default: the video number before any '-')")
    p.add_argument("--max-open", type=int, help="open submissions allowed in the run (default production.max_parallel_jobs)")
    p.set_defaults(fn=cmd_ledger)

    p = sp.add_parser("open"); p.add_argument("--file", required=True); p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_open)

    p = sp.add_parser("model-menu"); p.add_argument("--mode", choices=["analyze", "edit"])
    p.add_argument("--live-ids", help="comma/space separated model ids from models_explore list type=video")
    p.add_argument("--live-file", help="JSON file with the models_explore list output (items[].id)")
    p.set_defaults(fn=cmd_model_menu)

    p = sp.add_parser("model-entry"); p.add_argument("--id", required=True, help="model id from models_explore / the menu")
    p.set_defaults(fn=cmd_model_entry)

    def media_opts(p):
        p.add_argument("--fps", type=float, default=cfg_get("analysis.baseline_fps", 5.0),
                       help="baseline sampling rate (default 5)")
        p.add_argument("--dense-fps", type=float, default=cfg_get("analysis.dense_fps", 10.0),
                       help="rate used around motion peaks and in the first second (default 10)")
        p.add_argument("--static-threshold", type=float, default=cfg_get("analysis.static_threshold", 2.5),
                       help="mean abs grey difference (0-255) below which a frame counts as a static duplicate; 0 disables thinning")
        p.add_argument("--max-frames", type=int, default=cfg_get("analysis.max_baseline_frames", 1800))
        p.add_argument("--whisper-model", default=cfg_get("whisper_model", "small"))
        p.add_argument("--language", default="auto")
        p.add_argument("--no-transcript", action="store_true")
        p.add_argument("--no-ocr", action="store_true")
        p.add_argument("--ocr-frames", type=int, default=cfg_get("analysis.ocr_frames", 12))

    p = sp.add_parser("prep-video"); p.add_argument("video"); p.add_argument("--out", required=True)
    p.add_argument("--id"); media_opts(p); p.set_defaults(fn=cmd_prep_video)

    p = sp.add_parser("prep-all"); p.add_argument("--run", required=True); p.add_argument("--only")
    p.add_argument("--set", dest="inv_set", choices=["references", "examples"], default="references",
                   help="examples: prepare the examples inventory (10-media/E…, examples-index.md)")
    p.add_argument("--redo", action="store_true"); p.add_argument("--skip-images", action="store_true")
    p.add_argument("--jobs", type=int, default=cfg_get("analysis.jobs", 2)); media_opts(p)
    p.set_defaults(fn=cmd_prep_all)

    p = sp.add_parser("frames"); p.add_argument("video"); p.add_argument("--out", required=True)
    p.add_argument("--at"); p.add_argument("--range", action="append")
    p.add_argument("--fps", type=float, default=15.0, help="rate for --range (default 15)")
    p.add_argument("--label"); p.add_argument("--title"); p.add_argument("--sheet", action="store_true")
    p.add_argument("--max-side", type=int, default=1280); p.set_defaults(fn=cmd_frames)

    p = sp.add_parser("prep-image"); p.add_argument("image"); p.add_argument("--out", required=True)
    p.add_argument("--max-side", type=int, default=1280); p.set_defaults(fn=cmd_prep_image)

    p = sp.add_parser("doc-text"); p.add_argument("file"); p.add_argument("--out"); p.set_defaults(fn=cmd_doc_text)

    p = sp.add_parser("hf-put"); p.add_argument("--file", required=True); p.add_argument("--url", required=True)
    p.add_argument("--content-type"); p.add_argument("--retries", type=int, default=3)
    p.add_argument("--timeout", type=int, default=900); p.set_defaults(fn=cmd_hf_put)

    p = sp.add_parser("hf-get"); p.add_argument("--url", required=True); p.add_argument("--out", required=True)
    p.add_argument("--retries", type=int, default=4); p.set_defaults(fn=cmd_hf_get)

    p = sp.add_parser("fetch-audio"); p.add_argument("--url", required=True, help="direct audio-file URL")
    p.add_argument("--out", required=True); p.add_argument("--page", help="the source page the URL came from")
    p.add_argument("--license", required=True, help="license as stated on the source page")
    p.add_argument("--title"); p.add_argument("--author"); p.add_argument("--role", help="soundtrack | sfx:<name>")
    p.add_argument("--retries", type=int, default=3); p.set_defaults(fn=cmd_fetch_audio)

    p = sp.add_parser("audio-profile"); p.add_argument("--audio", required=True, help="files_audio file or the original video")
    p.add_argument("--out", required=True); p.add_argument("--transcript", help="10-media/<V>/transcript.json")
    p.add_argument("--cuts", help="10-media/<V>/cuts.json"); p.set_defaults(fn=cmd_audio_profile)

    p = sp.add_parser("split-audio"); p.add_argument("paths", nargs="+", help="the given video folder(s)/file(s)")
    p.add_argument("--run"); p.add_argument("--redo", action="store_true")
    p.add_argument("--audio-only", action="store_true", help="files_audio/ only, no silent copies (Analyze Create)")
    p.set_defaults(fn=cmd_split_audio)

    p = sp.add_parser("finalize"); p.add_argument("--run", required=True); p.add_argument("--file", required=True)
    p.add_argument("--original", required=True, help="the ORIGINAL video path (as in the inventory)")
    p.add_argument("--video", help="V id, for the run record"); p.add_argument("--expect-size", default="720x1280")
    p.add_argument("--force", action="store_true"); p.set_defaults(fn=cmd_finalize)

    p = sp.add_parser("restore-audio"); p.add_argument("--generated", required=True)
    p.add_argument("--audio", help="original audio from files_audio (preferred)")
    p.add_argument("--audio-offset", type=float, default=0.0, help="audio_offset from audio-split.json")
    p.add_argument("--source", help="original video (alternative to --audio)")
    p.add_argument("--start", type=float, default=0.0, help="segment start in the original timeline")
    p.add_argument("--out", required=True); p.add_argument("--duration", type=float)
    p.set_defaults(fn=cmd_restore_audio)

    p = sp.add_parser("sync-check", help="do the output's actions land where the original audio expects them?")
    p.add_argument("--source", required=True, help="the source picture the output must follow (silent copy / prepared source / own-silent.mp4)")
    p.add_argument("--output", required=True, help="the generated picture (raw, trimmed, joined or with-original-audio)")
    p.add_argument("--start", type=float, default=0.0, help="segment start in the source timeline (same as restore-audio --start)")
    p.add_argument("--duration", type=float, help="limit the compared span")
    p.add_argument("--out", required=True, help="folder for sync-check.json and sync-sheet.jpg")
    p.add_argument("--fps", type=float, default=30.0); p.add_argument("--tol", type=float, default=0.10, help="allowed offset in seconds")
    p.add_argument("--max-lag", type=float, default=1.5, help="largest offset searched, seconds")
    p.add_argument("--window", type=float, default=2.0, help="window for the per-window offsets, seconds")
    p.add_argument("--at", help="sheet timestamps on the output timeline, comma-separated (default: the source's strongest motion moments)")
    p.add_argument("--anchors", type=int, default=8, help="number of automatic sheet timestamps")
    p.set_defaults(fn=cmd_sync_check)

    p = sp.add_parser("qc"); p.add_argument("--video", required=True); p.add_argument("--out", required=True)
    p.add_argument("--fps", type=float, default=cfg_get("analysis.baseline_fps", 5.0))
    p.add_argument("--expect-duration", type=float); p.add_argument("--expect-aspect", default="9:16")
    p.add_argument("--expect-size", default=cfg_get("output.size", "720x1280"))
    p.add_argument("--mode", choices=["analyze", "edit"], default="analyze")
    p.add_argument("--allowed-text", help="planned/kept text, '|' separated (captions you burned in, real label text)")
    p.add_argument("--dense", action="append", metavar="LABEL:START-END",
                   help="QC checkpoint rendered at the full frame rate (seconds), e.g. sip:3.5-5.6 — a use beat, "
                        "exit/re-entry, occlusion, cut, hand-off, pour or seam (anomaly-catalog.md §4); repeatable")
    p.add_argument("--dense-fps", type=float, default=30.0, help="rate for --dense sheets (default 30)")
    p.add_argument("--no-ocr", action="store_true"); p.set_defaults(fn=cmd_qc)

    p = sp.add_parser("conform"); p.add_argument("--video", required=True); p.add_argument("--out", required=True)
    p.add_argument("--width", type=int, default=720); p.add_argument("--height", type=int, default=1280)
    p.add_argument("--mode", choices=["fill", "pad"], default="fill")
    p.add_argument("--focus-x", type=float, default=0.5); p.add_argument("--focus-y", type=float, default=0.5)
    p.add_argument("--max-crop", type=float, default=0.12); p.add_argument("--allow-large-crop", action="store_true")
    p.add_argument("--crf", type=int, default=18); p.set_defaults(fn=cmd_conform)

    p = sp.add_parser("captions"); p.add_argument("--video", required=True); p.add_argument("--out", required=True)
    p.add_argument("--spec", help="JSON: {style, presets, safe_area, uppercase, animation, events:[{start,end,text,preset,pos,animation}]}")
    p.add_argument("--from-speech", action="store_true", help="time captions to the clip's own speech")
    p.add_argument("--script", help="intended spoken wording (forces correct text onto ASR timing)")
    p.add_argument("--script-file"); p.add_argument("--words-per-caption", type=int, default=3)
    p.add_argument("--whisper-model", default=cfg_get("whisper_model", "small")); p.add_argument("--language", default="auto")
    p.add_argument("--crf", type=int, default=18); p.set_defaults(fn=cmd_captions)

    p = sp.add_parser("trim"); p.add_argument("--video", required=True); p.add_argument("--out", required=True)
    p.add_argument("--start", type=float, default=0.0); p.add_argument("--end", type=float)
    p.add_argument("--crf", type=int, default=18); p.set_defaults(fn=cmd_trim)

    p = sp.add_parser("concat"); p.add_argument("--clips", nargs="+", required=True); p.add_argument("--out", required=True)
    p.add_argument("--width", type=int, default=720); p.add_argument("--height", type=int, default=1280)
    p.add_argument("--fps", type=float, help="output fps (default: the clips' own fps when they all match, else 30)")
    p.add_argument("--seams", help="one per join, comma-separated: cut | continuous (default: all cut)")
    p.add_argument("--seam-trim-frames", type=int, default=1,
                   help="frames dropped from the head of a clip after a continuous seam (its repeat of the hand-off frame)")
    p.add_argument("--audio-seam-fade-ms", type=float, default=12.0, help="click-free audio fade at continuous seams")
    p.add_argument("--crf", type=int, default=18); p.set_defaults(fn=cmd_concat)

    p = sp.add_parser("last-frame"); p.add_argument("--video", required=True); p.add_argument("--out", required=True)
    p.add_argument("--back", type=float, default=0.0,
                   help="seconds before the end (use when the final frames freeze, fade or morph)")
    p.set_defaults(fn=cmd_last_frame)

    p = sp.add_parser("scale", help="size reckoning: expected vs observed product size (anomaly-catalog §2.7)")
    p.add_argument("--product-cm", type=float, required=True, help="the product's real height in cm (registry)")
    p.add_argument("--label", help="product name for the verdict")
    p.add_argument("--distance", type=float, help="camera-to-product distance in metres (from the shot size)")
    p.add_argument("--distance-basis", help="how --distance was derived from the frame (surface, neighbour, depth order); recorded in the verdict")
    p.add_argument("--lens", type=float, default=26.0, help="35 mm-equivalent focal length (phone main lens ≈ 26)")
    p.add_argument("--frame-h", type=int, default=1280, help="frame height in px (default 1280 for 720×1280)")
    p.add_argument("--frame", help="a full-resolution frame; its height overrides --frame-h")
    p.add_argument("--product-px", help="observed product height on the frame: 'y0-y1' rows or a pixel height")
    p.add_argument("--ref-cm", type=float, help="a neighbour's real height in cm (hand, bottle, phone, mug …)")
    p.add_argument("--ref-px", help="the neighbour's observed height on the same frame: 'y0-y1' or px")
    p.add_argument("--depth-ratio", type=float, default=1.0, help="product distance / neighbour distance (1 = same depth)")
    p.add_argument("--ok-pct", type=float, default=15.0); p.add_argument("--note-pct", type=float, default=25.0)
    p.add_argument("--out", help="write the result as JSON")
    p.set_defaults(fn=cmd_scale)

    p = sp.add_parser("caught-flag", help="the flag record caught_flags.html (data + viewer page): add | list | set | reconcile | open | render")
    p.add_argument("action", choices=["add", "list", "set", "reconcile", "open", "render"])
    p.add_argument("--id", help="set: the entry id (CF-nnn)")
    p.add_argument("--title", help="add: a short title"); p.add_argument("--date", help="add: YYYY-MM-DD (default: now)")
    p.add_argument("--run", help="run id or folder (add: attaches the request, inputs, plan and ledger row; list: filter; reconcile: required)")
    p.add_argument("--video", help="video number (add: attaches that video's files; list: filter)")
    p.add_argument("--attempt", help="add: the attempt (a1, a2, c2-a1 …); picks the request file")
    p.add_argument("--clip", help="add: the clip (c1, c2 …) of a multi-clip video")
    p.add_argument("--mode", help="analyze-recreate | analyze-create | edit (list: filter)")
    p.add_argument("--model", help="model id (list: filter)"); p.add_argument("--product", help="client product")
    p.add_argument("--kind", choices=CF_KINDS, help="add: what Higgsfield did (list: filter)")
    p.add_argument("--tool", help="add: generate_video | generate_image | media_upload | show_reference_elements | reframe | other")
    p.add_argument("--stage", help="add: preflight | submit | job | upload | result")
    p.add_argument("--response", help="add: Higgsfield's answer verbatim (error text, notice, status), text or file; 'none given' when empty")
    p.add_argument("--job", help="add: job id(s) that were flagged (default: the ledger row's)")
    p.add_argument("--fingerprint", help="add: the ledger fingerprint of the request (default: the ledger row's)")
    p.add_argument("--credits", help="add: charged / refunded credits")
    p.add_argument("--prompt", help="add: the flagged prompt as text, or the request .json (default: the run's request for this video and attempt)")
    p.add_argument("--params", help="add: generation params as 'k=v · k=v' (default: read from the request .json)")
    p.add_argument("--inputs", help="add: 'role: media id' lines or a file, when there is no request .json")
    p.add_argument("--flagged-video", help="add: the reference video that carried the flag (V id, file; default: the request's reference)")
    p.add_argument("--output", help="add: the output file when a job finished but was withheld or flagged")
    p.add_argument("--plan", help="add: the plan file path (default: <run>/40-briefs/video-NN-plan.md)")
    p.add_argument("--trigger", help="add/set: the agent's suspected trigger, labelled [E] evidence or [I] inference")
    p.add_argument("--cause", choices=CF_CAUSES, default="unknown")
    p.add_argument("--tags", help="add/set: 1 to 4 grouping labels for the trigger, comma-separated (real-person-face, video-reference, "
                                  "celebrity-name, brand-name, protected-ip, nsfw-image, element, prompt-wording, preset-notice, output-withheld, unknown-trigger …); list: filter")
    p.add_argument("--asset", action="append", help="add/set: the input you suspect: its label in the request (Image 2, Video 1), a media id, a file name "
                                                    "or an A/V id, or a file path for an upload flag; repeatable (list: text filter)")
    p.add_argument("--prompt-span", help="add/set: the exact words of the prompt you suspect")
    p.add_argument("--part-of", help="add/set: which video holds the suspected part: 'reference V10', 'clip a2' or a path")
    p.add_argument("--part-from", type=float, help="add/set: start of the suspected part, seconds")
    p.add_argument("--part-to", type=float, help="add/set: end of the suspected part, seconds")
    p.add_argument("--part-note", help="add/set: what is on screen in that part")
    p.add_argument("--no-thumbs", action="store_true", help="add/set: do not embed thumbnails of the inputs and of the part")
    p.add_argument("--changed", help="add/set: what was changed in the next request (reworded, video reference dropped, image replaced …)")
    p.add_argument("--outcome", help="add/set: what happened next")
    p.add_argument("--rule", help="add/set: the general rule, as a kind not an instance")
    p.add_argument("--status", choices=CF_STATUS, help="add: initial status (open); set: new status; list: filter")
    p.add_argument("--source", choices=["user", "agent"], default="agent")
    p.add_argument("--note", help="set: a dated note appended to the entry's log")
    p.add_argument("--cleared-prompt", help="set: the request .json or text Higgsfield accepted after the change")
    p.add_argument("--cleared-job", help="set: the job id that ran after the change")
    p.add_argument("--promoted-to", help="set: the reference and section the rule was written into")
    p.add_argument("--grep", help="list: substring over the whole entry")
    p.add_argument("--full", action="store_true", help="list: keep the long prompt texts")
    p.set_defaults(fn=cmd_caught_flag)

    p = sp.add_parser("capcut-name"); p.add_argument("--video", required=True, help="the run's video number")
    p.add_argument("--date", help="YYYY-MM-DD (default: today)"); p.add_argument("--store", help="CapCut drafts dir")
    p.set_defaults(fn=cmd_capcut_name)

    p = sp.add_parser("capcut-prep"); p.add_argument("--draft", required=True, help="the freshly cloned draft folder")
    p.set_defaults(fn=cmd_capcut_prep)

    p = sp.add_parser("capcut-repair"); p.add_argument("--draft", required=True)
    p.add_argument("--preview", help="also render capcut-cli's proxy preview to this .mp4")
    p.set_defaults(fn=cmd_capcut_repair)

    p = sp.add_parser("capcut-text-style"); p.add_argument("--draft", required=True, help="the CapCut draft folder")
    p.add_argument("--check", action="store_true", help="only report texts that are off the house style (exit 1)")
    p.add_argument("--learn", action="store_true", help="copy the exact preset from a text styled once in CapCut")
    p.add_argument("--text", type=int, help="--learn: which text of the draft (1-based) when it holds several")
    p.add_argument("--replace", action="store_true",
                   help="--learn: overwrite a locked learned preset (only when the user asks for a new one)")
    p.set_defaults(fn=cmd_capcut_text_style)

    p = sp.add_parser("strip-inserts"); p.add_argument("--video", required=True, help="the ORIGINAL reference (with audio)")
    p.add_argument("--inserts", required=True, help="in-out seconds, comma-separated, e.g. 13.0-15.0,20.4-21.2")
    p.add_argument("--out", required=True, help="output folder"); p.add_argument("--crf", type=int, default=18)
    p.set_defaults(fn=cmd_strip_inserts)

    p = sp.add_parser("clean"); p.add_argument("--video", required=True); p.add_argument("--out", required=True)
    p.add_argument("--delogo", action="append", help="x,y,w,h[@t0-t1] (0-1 fractions or pixels); repeatable")
    p.add_argument("--crop", help="x,y,w,h (0-1 fractions or pixels) — keep this region")
    p.add_argument("--crf", type=int, default=18); p.set_defaults(fn=cmd_clean)

    a = ap.parse_args()
    try:
        a.fn(a)
    except SystemExit:
        raise
    except Exception as e:
        fail(f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
