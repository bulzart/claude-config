#!/usr/bin/env python3
"""awl.py - deterministic local toolkit for the /analyze-with-loupe Claude Code command.

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

Subcommands (python awl.py <cmd> -h):
  new-run        create a run workspace and state.json
  state          read or update state.json (get [key] | set key=value ... | append key=value ...)
  inventory      recursive inventory of files/folders --as references | sources (edit videos) | assets
                 | examples (your own finished videos: study only)
  prep-assets    previews, doc text, font names and a labelled contact sheet of USER-SUPPLIED assets
  model-menu     numbered table of EVERY available video model (pinned first) + quick picks
  model-entry    ONE model's index.json entry + its guide path and section folder (index.json is 40 KB: never read it whole)
  ledger        anti-duplicate guard for paid generations (begin before, set after every call)
  caught-flag    flag record in Loupe (the web app): prompts and videos Higgsfield flagged or refused, with gathered evidence
                 (add | set | list | reconcile | open)
  loupe          ensure | status | open: the Loupe web app (flags, generation misses, QC samples)
  qc-consult     QC phase only: ask the QC keeper which samples (generation misses) apply to the video under QC
  qc-brief       QC phase only: the matching samples as a plain brief (no model call)
  prompt-template first request of a video (X4b, after X1-X4): the whole checked brief to the judge; it answers the final prompt
  template-apply X4b: the judge's prompt into the request word for word (draft kept); reports must-carry lines missing, slots left, length
  plan-hints     (older runs; X2 now uses prompt-template) the keeper's few text-only hints for a plan
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
  concat         normalise clips to 720x1280 and join them in order (multi-clip videos; cut or continuous seams; pieces cut from a
                 clip, e.g. c1a c2 c1b, are fine) + <out>.join.json: which seconds each piece (its clip and attempt) fills, for Loupe
  last-frame     exact last frame of a clip as a lossless PNG: the hand-off start frame for the next clip
  capcut-name    free CapCut project name DD_Mon_YYYY_vNN for an Analyze Mode video
  capcut-prep    after capcut_clone_draft: set aside the template's identity/layout so `capcut register` rebuilds them
  capcut-font    Static: list the fonts on this PC (CapCut's own, then Windows') | set one font on a draft's texts (nothing else)
  capcut-repair  after capcut_save: house text style + register + sync-timelines + lint (one machine-wide lock),
                 then a proxy preview
  capcut-text-style  every CapCut text layer → the user's locked house preset (config capcut.text_style.learned),
                 size 10, or 11 when the video has only a little text (capcut.text_style.short_text)
                 (--check reports; --learn copies the exact preset from a text styled once in CapCut;
                 a locked preset is only replaced with --learn --replace)
  strip-inserts  a reference minus its inserts (memes) in one pass + silent copy + map of the split points
  qc             storyboard + checks (size, duration, black, freeze, mode-aware visible text) for an output
  voiceover      own voiceover (contract item 31): outdir (the folder the ElevenLabs MCP may write to) | record (a take into the run,
                 measured: phrases, pauses, spoken words; state.json -> voiceover.files) | align (where the model's own speech lies
                 against the take) | mix (the take over the picture, plus a placed track for CapCut); facts, no verdict
  effort         the run's effort level (contract item 33): low | medium | high | xhigh | max, custom values held to the floors;
                 prep-all (the reference sampling) and the produce phase (agents at once, the pilot) read it; never QC
  static         Static (contract item 36): check the setup on this PC (key present, image model, FLUX 3 Klein, TTS, music, whisper,
                 ffmpeg, capcut-cli) | formats (facts for the format question: the references' aspects, sizes per aspect and resolution)
                 | format (store the pick)
  image          Static stills: generate (OpenAI Images API with the key only from OPENAI_API_KEY, or FLUX 3 Klein on this PC with
                 static_images=klein; ledgered) | prompts (the file a user makes them from) | intake (the user's folder, copied in) | use
                 (which attempt the edit takes)
  tts            Static voice (Qwen3-TTS in its own environment): check | design (voice samples) | voice (the run's voice) | say (narration)
  narration-words Static: a narration's timed words, caption cues, SRT and per-line differences from the script
  music          Static bed (ACE-Step 1.5 in its own environment), only when planned: check | make
  slideshow      Static: plan (timeline from the image plan and the narration) | render (clean and captioned preview mp4)

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

AWL_HOME = Path(os.environ.get("AWL_HOME") or Path(__file__).resolve().parent.parent)   # the library; AWL_HOME points tests at a temp copy
CONFIG_PATH = AWL_HOME / "config.json"

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

DERIVED_DIRS = {"files_audio", "videos_without_audio"}      # created by split-audio inside the user's path
FINAL_DIR = "final"                                          # approved Edit Mode results, inside the user's path
FINAL_MARKER = ".awl-final"                                  # hidden marker: only OUR final folder is skipped
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".idea", ".vscode",
             "$RECYCLE.BIN", "System Volume Information", ".analyze-with-loupe"} | DERIVED_DIRS
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


def _replace(tmp: Path, path: Path) -> None:
    """os.replace that waits out a reader: on Windows a file another process holds open without FILE_SHARE_DELETE (a hook, Loupe, an editor
    reading it) refuses to be replaced for as long as it is held; short retries let the write through instead of failing the step."""
    for i in range(60):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if i == 59:
                raise
            time.sleep(0.05)


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    _replace(tmp, path)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    _replace(tmp, path)


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
        half = max(1, int(round(0.5 * dense_fps)))      # +-0.5 s around a peak at every level (5 frames each side at 10 fps)
        for k in range(-half, half + 1):
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


AUDIO_INGEST = ("whisper", "frames-only")      # state.json -> audio_ingest: the user's choice at the start (contract item 24); no default anywhere
AUDIO_INGEST_HELP = ("state.json -> audio_ingest is not set (whisper | frames-only): the user is asked once at the start (awl-start step 6, contract item 24); "
                     "store the answer with `T state --run RUN set audio_ingest=whisper|frames-only`")


def audio_ingest_of(run_dir: Path) -> str:
    """The run's speech-to-text choice from its state.json; a missing or unknown value stops with the error that names the key."""
    p = Path(run_dir) / "state.json"
    try:
        v = json.loads(p.read_text(encoding="utf-8")).get("audio_ingest")
    except (OSError, ValueError):
        v = None
    if v not in AUDIO_INGEST:
        fail(AUDIO_INGEST_HELP + (f" (found {v!r})" if v else ""), 2)
    return v


# The run's effort level (contract item 33, reference/effort.md): how densely the references are sampled at analysis, how many production
# agents run at once and from how many videos the pilot runs first. QC and Loupe are never part of it (the judges stay stable). Coverage
# never drops: every second of every reference is sampled, every cut keeps its last and first frame, the first second and the motion
# peaks are dense. The floors are where the analysis would lose what it needs; the ceilings keep a typo from flooding a run. None = no cap.
EFFORT_KEYS = ("analysis_fps", "analysis_dense_fps", "motion_peaks", "densify_ranges", "max_agents", "pilot_from")
_EL = lambda af, adf, mp, dr, ag, pf: {"analysis_fps": af, "analysis_dense_fps": adf, "motion_peaks": mp, "densify_ranges": dr,
                                       "max_agents": ag, "pilot_from": pf}
EFFORT_LEVELS = {             # max = the pipeline's settings before item 33, and what a run without the key keeps
    "low":    _EL(2.0, 6.0, 4, 2, 2, 2),
    "medium": _EL(3.0, 8.0, 5, 4, 3, 3),
    "high":   _EL(4.0, 10.0, 6, 6, 4, 5),
    "xhigh":  _EL(5.0, 10.0, 8, 8, 5, 5),
    "max":    _EL(5.0, 10.0, 8, None, 5, 5),
}
EFFORT_BOUNDS = {"analysis_fps": (2.0, 10.0), "analysis_dense_fps": (6.0, 30.0), "motion_peaks": (4, 8), "densify_ranges": (2, 50),
                 "max_agents": (1, 5), "pilot_from": (2, 5)}
EFFORT_LEGACY = {"level": "max", **EFFORT_LEVELS["max"], "note": "no effort key: the rates before contract item 33 (max)"}
EFFORT_HELP = ("state.json -> effort is empty: the user's effort level is not stored yet. The user picks it once at the start, from all five "
               "levels in plain chat (awl-start step 5d, reference/effort.md §1); store the answer with "
               "`T effort --run RUN --level low|medium|high|xhigh|max`")


def effort_of_state(st: dict) -> dict:
    """The run's effort settings: state.json -> effort. A run made before item 33 has no key and keeps its rates (max); new-run writes the
    key empty (null) until the user's answer is stored, and such a run is pending: what needs the level stops on it."""
    e = st.get("effort") if isinstance(st, dict) else None
    if isinstance(e, dict) and e.get("level"):
        base = dict(EFFORT_LEVELS.get(e["level"], EFFORT_LEVELS["max"]))
        base.update({k: e[k] for k in EFFORT_KEYS if k in e})
        base["level"] = e["level"]
        return base
    if isinstance(st, dict) and "effort" in st:
        return {"level": None, "pending": True, "note": EFFORT_HELP}
    return dict(EFFORT_LEGACY)


def effort_of(run_dir) -> dict:
    try:
        st = json.loads((Path(run_dir) / "state.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        st = {}
    return effort_of_state(st)


def effort_required(run_dir) -> dict:
    """The run's effort settings for a step that uses them: a pending level stops here, with the error that says the user is asked."""
    eff = effort_of(run_dir)
    if eff.get("pending"):
        fail(EFFORT_HELP, 2)
    return eff


def _effort_clamp(key: str, value):
    """(value held to the key's floor and ceiling, 'floor' | 'ceiling' | None). None stays None (no cap) where the level allows it."""
    if value is None:
        return None, None
    lo, hi = EFFORT_BOUNDS[key]
    v = int(value) if isinstance(lo, int) else float(value)
    if v < lo:
        return lo, "floor"
    if v > hi:
        return hi, "ceiling"
    return v, None


def transcribe(wav: str, workdir: Path, model_name: str = "small", language: str = "auto") -> dict:
    res = {"engine": None, "has_speech": False, "segments": []}
    if os.environ.get("AWL_TRANSCRIBE_STUB"):           # tests: no model is downloaded or run; the shape of a real answer
        res.update({"engine": "stub", "model": "stub", "language": "en", "language_probability": 1.0,
                    "segments": [{"start": 0.5, "end": 1.5, "text": "stub words here",
                                  "words": [{"w": "stub", "s": 0.5, "e": 0.8, "p": 1.0}, {"w": "words", "s": 0.8, "e": 1.1, "p": 1.0}, {"w": "here", "s": 1.1, "e": 1.5, "p": 1.0}]}]})
        res.update({"has_speech": True, "n_words": 3, "speech_seconds": 1.0, "wpm_speech_only": 180.0})
        return res
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
    """RapidOCR over frame files -> detections + spans with the numbers that describe them (frames seen, row, confidence, spelling facts). Thread-safe."""
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
            if score < 0.6 or not text.strip():          # the engine's own confidence floor: a detection setting, not a judgement of the text
                continue
            ys = [p[1] for p in box]
            dets.append({"t": fr["t"], "text": text.strip(), "score": round(float(score), 2),
                         "y_rel": round(sum(ys) / 4 / max(1, height), 3)})
    # Numbers about what was seen, and no label on any of it. Whether a text is a caption, a persistent overlay, a watermark, a product label
    # or noise is for the reader to judge from these numbers and the picture: a row of the frame (a "band") with many different texts over
    # several frames reads like a caption track, a text seen in most scanned frames reads like a fixed overlay.
    bands = {}
    for d in dets:
        bands.setdefault(round(d["y_rel"] / 0.08), []).append(d)
    band_stats = {b: {"y_rel": round(b * 0.08, 2), "detections": len(ds),
                      "distinct_texts": len({re.sub(r"\W+", "", d["text"].lower()) for d in ds}),
                      "frames": len({d["t"] for d in ds})} for b, ds in bands.items()}
    spans = {}
    for d in dets:
        key = re.sub(r"\W+", "", d["text"].lower())
        if len(key) < 2:
            continue
        sp = spans.setdefault(key, {"text": d["text"], "first_t": d["t"], "last_t": d["t"], "hits": 0, "score_sum": 0.0,
                                    "y_rel": d["y_rel"], "band": round(d["y_rel"] / 0.08)})
        sp["first_t"], sp["last_t"] = min(sp["first_t"], d["t"]), max(sp["last_t"], d["t"])
        sp["hits"] += 1
        sp["score_sum"] += d["score"]
    for sp in spans.values():
        tx = sp["text"]
        bs = band_stats[sp["band"]]
        sp["score_mean"] = round(sp.pop("score_sum") / sp["hits"], 2)
        sp["share_of_frames_scanned"] = round(sp["hits"] / n_frames, 2) if n_frames else None
        sp["chars"] = len(re.sub(r"\W+", "", tx))
        sp["words"] = len(tx.split())
        sp["band_distinct_texts"], sp["band_frames"] = bs["distinct_texts"], bs["frames"]
        sp["has_at_handle"] = bool(tx.startswith("@") or re.search(r"@\w{2,}", tx))        # spelling facts of the text itself
        sp["has_hashtag"] = tx.startswith("#")
        sp["has_url_pattern"] = bool(re.search(r"(www\.|https?:|\.com\b|\.co\b|\.io\b)", tx, re.I))
    return {"available": True, "frames_scanned": n_frames, "detections": dets,
            "bands": sorted(band_stats.values(), key=lambda b: b["y_rel"]),
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
               audio_ingest: str = None, do_ocr: bool = True, ocr_budget: int = 12,
               max_frames: int = 1800, hook_s: float = 3.0, peaks_max: int = 8, extras: bool = True) -> dict:
    t0 = time.time()
    if audio_ingest not in AUDIO_INGEST:
        raise RuntimeError(AUDIO_INGEST_HELP)
    whisper = audio_ingest == "whisper"
    odir.mkdir(parents=True, exist_ok=True)
    for stale in ("frames", "sheets", "_work", "transcript.json", "transcript.txt"):
        if (odir / stale).is_dir():
            shutil.rmtree(odir / stale, ignore_errors=True)
        else:
            (odir / stale).unlink(missing_ok=True)
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
    peaks = activity_peaks(windows, k=min(int(peaks_max), max(2, math.ceil(dur / 5))))
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
    # a still stretch counts from 3 duplicates in a row at 4 fps and up (the rates before item 33); at 3 fps from the 2 a still second holds,
    # so Medium never keeps more frames of a still shot than High; at 2 fps a still second holds 1, and thinning it would save no cell
    statics = thin_static(base, static_threshold, min_run=max(2, min(3, math.ceil(base_fps) - 1)))
    plan = densify_plan(cuts, peaks, dur, fps, eff_fps, dense_fps) if extras else []     # --no-extras: the baseline rate only (Static: 1 fps)
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
    # speech-to-text only when the run chose it; frames only = no transcript file at all, and every reader is told 'audio not ingested'
    if whisper:
        trans = {"ingested": True, "mode": "whisper", "has_audio": bool(aud.get("wav_16k")), "engine": None, "has_speech": False, "segments": []}
        if aud.get("wav_16k"):
            trans.update(transcribe(aud["wav_16k"], odir / "audio", whisper_model, language))
        else:
            trans["note"] = "no audio stream in this video: nothing to transcribe"
        write_json(odir / "transcript.json", trans)
        txt = [f"[{ts_label(s['start'])}-{ts_label(s['end'])}] {s['text']}" for s in trans.get("segments", [])]
        write_text(odir / "transcript.txt", "\n".join(txt) if txt else
                   ("No audio stream in this video (nothing to transcribe)." if not aud.get("wav_16k") else
                    f"No speech recognised: {trans.get('engine') or 'no speech engine ran (' + str(trans.get('faster_whisper_error', ''))[:120] + ')'} found 0 words."))
    else:
        trans = {"ingested": False, "mode": "frames-only", "has_audio": bool(aud.get("wav_16k")), "engine": None, "segments": []}
        txt = []
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
               "speech": ({k: trans.get(k) for k in ("ingested", "mode", "has_audio", "engine", "model", "language", "has_speech", "n_words",
                                                     "speech_seconds", "wpm_speech_only", "note")} if whisper
                          else {"ingested": False, "mode": "frames-only", "has_audio": bool(aud.get("wav_16k")), "note": "audio not ingested (frames only): what was said is unknown, not absent"}),
               "loop_similarity_first_last": loop,
               "ocr_spans": (ocr.get("spans") or [])[:40] if ocr.get("available") else None,
               "sheets": sheets, "timings_s": timings, "elapsed_s": round(time.time() - t0, 1)}
    write_json(odir / "video.json", summary)

    # human-readable companions
    T = [f"# {vid} — per-second timeline (sheets + this table = one continuous sequence)", "",
         ("| sec | shot | events | speech in this second | audio max dB | on-screen text (OCR sample) |" if whisper else
          "| sec | shot | events | speech (audio not ingested: frames only) | audio max dB | on-screen text (OCR sample) |"),
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
         (f"- **Speech**: {trans.get('n_words', 0)} words via {trans.get('engine')} ({trans.get('language')}); "
          f"speech starts at {first_word} s; {trans.get('wpm_speech_only')} wpm (speech-only)" + (f" — {trans['note']}" if trans.get('note') else "")) if whisper else
         "- **Speech**: audio not ingested (frames only, `state.json → audio_ingest`): what is said is unknown, not absent; hook, address and sync anchors come from the frames, the cuts, the sound numbers and the on-screen text",
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
    if whisper:
        L += ["", "## Transcript (machine ASR — evidence to verify, not verbatim truth)", ""]
        L += txt[:150] or [("No audio stream in this video (nothing to transcribe)." if not aud.get("wav_16k") else "No speech recognised (the speech engine found 0 words).")]
    else:
        L += ["", "## Transcript: audio not ingested (frames only)", "", "No speech-to-text ran for this run; the speech column above is empty by choice. Never write 'no speech' or 'silent' for this video."]
    if ocr.get("available"):
        L += ["", f"## On-screen text sample (OCR on {ocr.get('frames_scanned')} frames)", ""]
        for sp in (ocr.get("spans") or [])[:40]:
            L.append(f"- {ts_label(sp['first_t'])}–{ts_label(sp['last_t'])} · seen in {sp['hits']} of {ocr.get('frames_scanned')} scanned frame(s) · "
                     f"row y {sp['y_rel']} ({sp['band_distinct_texts']} different text(s) in that row) · \"{sp['text']}\"")
        if not ocr.get("spans"):
            L.append("- none detected")
    L += ["", f"Machine data in `{odir}`: video.json, frames.json, cuts.json, activity.json, audio.json, "
              f"transcript.json, ocr.json, timeline.md · densify on demand: "
              f"`awl.py frames \"{video}\" --out <dir> --range a-b --fps 15 --sheet` · elapsed {summary['elapsed_s']} s"]
    write_text(odir / "video.md", "\n".join(L))
    shutil.rmtree(odir / "_work", ignore_errors=True)
    return summary


def _media_kwargs(a, audio_ingest: str, eff: dict | None = None) -> dict:
    """The sampling rates: the command line's when given, else the run's effort level (prep-all), else the config's defaults."""
    base = a.fps if a.fps is not None else (eff["analysis_fps"] if eff else cfg_get("analysis.baseline_fps", 5.0))
    dense = a.dense_fps if a.dense_fps is not None else (eff["analysis_dense_fps"] if eff else cfg_get("analysis.dense_fps", 10.0))
    return dict(base_fps=float(base), dense_fps=float(max(dense, base)), static_threshold=a.static_threshold,
                whisper_model=a.whisper_model, language=a.language, audio_ingest=audio_ingest,
                do_ocr=not a.no_ocr, ocr_budget=a.ocr_frames, max_frames=a.max_frames,
                peaks_max=int(eff["motion_peaks"]) if eff and eff.get("motion_peaks") else 8, extras=not getattr(a, "no_extras", False))


def cmd_prep_video(a):
    if a.audio_ingest not in AUDIO_INGEST:
        fail("prep-video needs --audio-ingest whisper|frames-only (the run's choice, state.json -> audio_ingest; prep-all reads it by itself)", 2)
    try:
        s = prep_video(a.video, Path(a.out), a.id or "V", **_media_kwargs(a, a.audio_ingest))
    except Exception as e:
        fail(f"{type(e).__name__}: {e}")
    out({"ok": True, "audio_ingest": a.audio_ingest, "summary_md": str(Path(a.out) / "video.md"), "timeline_md": str(Path(a.out) / "timeline.md"),
         "sheets": s["sheets"], "sampling": s["sampling"], "speech": s.get("speech"), "elapsed_s": s["elapsed_s"]})


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



def pdf_text(path, images_dir=None, max_images: int = 40):
    """(text, facts) of a PDF through pypdf: the text layer page by page (layout mode, so words of one line stay on one line), and
    facts about the file: pages, characters, and whether it has no text layer at all (a scan or image-only export). With images_dir,
    the embedded page images of an image-only PDF are written there so the pages can be viewed one by one (the Read tool renders at
    most 10 pages of a PDF on this machine). Nothing is judged here: an image-only PDF is a fact about the file."""
    p = Path(path)
    try:
        from pypdf import PdfReader
    except ImportError:
        return ("[PDF: pypdf is not installed (pip install pypdf): view the pages with the Read tool, `pages` for long files]",
                {"extractor": None, "pages": None, "chars": None, "image_only": None})
    rd = PdfReader(str(p))
    if rd.is_encrypted:
        try:
            rd.decrypt("")
        except Exception:  # noqa: BLE001  a protected file: the pages below may still fail, and the facts say so
            pass
    pages, chars = [], 0
    for i, pg in enumerate(rd.pages, 1):
        try:
            try:
                t = pg.extract_text(extraction_mode="layout") or ""
            except TypeError:                                   # an older pypdf without extraction_mode
                t = pg.extract_text() or ""
            t = re.sub(r"[ \t]{3,}", "  ", t).strip()
        except Exception as e:  # noqa: BLE001  a damaged page
            t = f"[page {i}: the text could not be extracted: {str(e)[:80]}]"
        chars += len(t)
        pages.append(f"--- page {i} ---\n{t}")
    n = len(rd.pages)
    facts = {"extractor": "pypdf", "pages": n, "chars": chars, "image_only": n > 0 and chars == 0}
    if images_dir and facts["image_only"]:
        d = Path(images_dir)
        d.mkdir(parents=True, exist_ok=True)
        written = []
        for i, pg in enumerate(rd.pages, 1):
            try:
                imgs = list(pg.images)
            except Exception:  # noqa: BLE001
                imgs = []
            for j, im in enumerate(imgs, 1):
                if len(written) >= max_images:
                    break
                ext = Path(im.name).suffix.lower() or ".png"
                dst = d / f"page-{i:03d}-{j:02d}{ext}"
                try:
                    dst.write_bytes(im.data)
                    written.append(str(dst))
                except Exception:  # noqa: BLE001
                    pass
        facts["images"] = written
        facts["images_truncated"] = len(written) >= max_images
        facts["images_dir"] = str(d)
    if facts["image_only"]:
        where = f"; its page images are in {facts.get('images_dir')}" if facts.get("images") else ""
        text = f"[PDF with no text layer (image-only): {n} page(s){where}; view the pages as images (the Read tool renders at most 10 pages)]"
    else:
        text = "\n".join(pages)
    return text, facts


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
        return pdf_text(p)[0]
    return "[unsupported format for text extraction]"


def cmd_doc_text(a):
    facts = None
    try:
        if Path(a.file).suffix.lower() == ".pdf":
            text, facts = pdf_text(a.file, a.images_out)
        else:
            text = doc_text(a.file)
    except Exception as e:
        fail(str(e))
    if a.out:
        write_text(Path(a.out), text)
    out({"ok": True, "chars": len(text), "out": a.out, **({"pdf": facts} if facts else {}), **({} if a.out else {"text": text[:20000]})})


# --------------------------------------------------------------------------- run management

def runs_root() -> Path:
    """Where the runs live: config `runs_root`, else <library>/runs."""
    return Path(cfg_get("runs_root") or (AWL_HOME / "runs")).expanduser()


def resolve_run(run, must_exist: bool = True):
    """The run folder named by --run: a full path, a bare run name (`20261019-235823-19`) or a stamp prefix (`20261019-235823`)
    under the runs root. A prefix that matches several runs is refused with their names (the choice is the agent's). With
    must_exist False, nothing matching gives None instead of an error."""
    s = str(run or "").strip().strip('"')
    if not s:
        return None
    p = Path(s).expanduser()
    if p.is_dir():
        return p.resolve()
    root = runs_root()
    if "/" not in s and "\\" not in s:
        if (root / s).is_dir():
            return (root / s).resolve()
        hits = sorted(d for d in root.glob(s + "*") if d.is_dir()) if root.is_dir() else []
        if len(hits) == 1:
            return hits[0].resolve()
        if len(hits) > 1:
            fail(f"--run {s!r} matches {len(hits)} runs under {root}: " + ", ".join(d.name for d in hits[:8]) + " (name one)", 2)
    if must_exist:
        fail(f"run {s!r} not found: not a folder, and no run under {root} has that name or prefix", 2)
    return None


def cmd_new_run(a):
    root = Path(a.runs_root or cfg_get("runs_root") or (AWL_HOME / "runs")).expanduser()
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
             "model": None, "requested_videos": None, "directions": [], "assets": {}, "videos": [], "notes": [],
             "effort": None}                # the user's effort level (item 33): empty until the start stores it; prep-all stops on empty
    write_json(run_dir / "state.json", state)
    out({"ok": True, "run_dir": str(run_dir), "state": str(run_dir / "state.json"),
         "sources": sources, "assets_paths": assets, "examples_paths": examples})


def _set_dotted(d: dict, key: str, value):
    parts = key.split(".")
    for p in parts[:-1]:
        if d.get(p) is None:            # missing, or kept empty until set (effort: null)
            d[p] = {}
        d = d[p]
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
        marker.write_text("Created by /analyze-with-loupe: approved results. This folder is skipped when the "
                          "parent folder is scanned again.\n", encoding="utf-8")
        if sys.platform.startswith("win"):
            try:
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(str(marker), 0x02)   # FILE_ATTRIBUTE_HIDDEN
            except Exception:
                pass


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
            item["group"] = item["folder"]           # the folder it came in (a fact); what the asset is, is decided by viewing it
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
        extra_col = " group |" if role == "assets" else ""
        lines += [f"## {kind} ({len(rows)})", "", "| id | file | details |" + extra_col,
                  "|---|---|---|" + ("---|" if role == "assets" else "")]
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
                row += f" {it.get('group')} |"
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
                dest = adir / "docs" / f"{aid}.txt"
                txt, pf = pdf_text(it["path"], adir / "docs" / f"{aid}-pages")
                write_text(dest, txt)
                lines.append(f"- {aid} PDF `{name}` ({pf.get('pages')} page(s), {pf.get('chars')} characters of text) → `{dest}`"
                             + (f" · no text layer: {len(pf.get('images') or [])} page image(s) in `{pf.get('images_dir')}` (view them)" if pf.get("image_only") else ""))
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
    audio_ingest = audio_ingest_of(run_dir)          # the user's choice; no default: a run without it stops here
    eff = effort_required(run_dir)                   # the user's effort level (item 33): stops while empty; a run made before it keeps its old rates
    kw = _media_kwargs(a, audio_ingest, eff)
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
            dest = media / "docs" / f"{it['id']}.txt"
            txt, pf = pdf_text(it["path"], media / "docs" / f"{it['id']}-pages")
            write_text(dest, txt)
            done.append(it["id"])
            return (f"- {it['id']} PDF `{it['rel']}` ({pf.get('pages')} page(s), {pf.get('chars')} characters of text) → text `{dest}`"
                    + (f" · no text layer: {len(pf.get('images') or [])} page image(s) in `{pf.get('images_dir')}` (view them)" if pf.get("image_only") else ""))
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
    out({"ok": not errors, "set": a.inv_set, "audio_ingest": audio_ingest,
         "sampling": {"effort": eff["level"], "baseline_fps": kw["base_fps"], "dense_fps": kw["dense_fps"], "motion_peaks": kw["peaks_max"]},
         "prepared": sorted(done), "errors": errors, "index": str(index)}, 0 if not errors else 1)



# --------------------------------------------------------------------------- run inspection (gather-only: facts for the agent, no verdict)

_PATH_HINT = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\|/|(?:00-inventory|10-media|20-analysis|30-assets|40-briefs|50-requests|60-outputs|deliverables|logs)[\\/])")


def _walk_paths(obj, run_dir, prefix="", out=None):
    """Every string of a JSON document that looks like a file path (absolute, or a run sub-folder path), with the dotted key it sits under."""
    out = [] if out is None else out
    if isinstance(obj, dict):
        for k, v in obj.items():
            _walk_paths(v, run_dir, f"{prefix}.{k}" if prefix else str(k), out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _walk_paths(v, run_dir, f"{prefix}[{i}]", out)
    elif isinstance(obj, str) and len(obj) < 400 and _PATH_HINT.match(obj) and "://" not in obj and "<" not in obj:
        p = Path(obj)
        if not p.is_absolute():
            p = run_dir / obj
        out.append((prefix, obj, p))
    return out


# what the skills' hand-offs have written by each stage (facts to compare with, not a gate): (state keys, run files)
STAGE_EXPECTS = {
    "created": (["run_id", "mode", "source"], []),
    "started": (["model", "model_locked", "loupe"], []),
    "prepared": (["model"], ["00-inventory/inventory.json", "10-media/index.md"]),
    "analyzed": (["model"], ["20-analysis/cards"]),
    "counted": (["requested_videos"], ["20-analysis/cards"]),
    "planned": (["requested_videos"], ["20-analysis/cards"]),
    "asset_planned": (["asset_plan"], ["30-assets/asset-plan.md"]),
    "producing": (["asset_plan", "higgsfield.folder_id", "assets.uploads"], ["50-requests/agent-contract.md"]),
    "produced": (["videos"], ["deliverables/README.md"]),
    "editing": (["video"], ["00-inventory/inventory.json"]),
    "edited": (["videos"], []),
    "done": (["videos"], []),
}


def _state_of(run) -> tuple:
    rd = resolve_run(run)
    p = rd / "state.json"
    if not p.is_file():
        fail(f"state.json not found in {rd}", 2)
    return rd, json.loads(p.read_text(encoding="utf-8"))


def cmd_status(a):
    """Where a run stands, from its files only: stage, next_skill, next_step, the current video, videos and submissions by status,
    flagged rows (a count), credits recorded, the Loupe flag of the run (and whether Loupe answers now), the QC consults and hints
    saved, and every file a state.json key points to that does not exist. Reads; writes nothing; decides nothing."""
    rd, st = _state_of(a.run)
    vids = [v for v in st.get("videos") or [] if isinstance(v, dict)]
    subs = [s for s in st.get("submissions") or [] if isinstance(s, dict)]
    by_v = {}
    for v in vids:
        by_v[str(v.get("status") or "?")] = by_v.get(str(v.get("status") or "?"), 0) + 1
    by_s = {}
    for s in subs:
        by_s[str(s.get("status") or "?")] = by_s.get(str(s.get("status") or "?"), 0) + 1
    missing = [{"key": k, "path": raw} for k, raw, p in _walk_paths(st, rd) if not p.exists()]
    loupe = {"recorded": st.get("loupe") if "loupe" in st else "none (counts as up)"}
    if not a.no_loupe:
        try:
            lc = _lc()
            h = lc.health()
            loupe["running"] = bool(h)
            if h:
                st_, d_ = lc.call("GET", "/api/qc/keeper/state", key_name="qc", timeout=10)
                loupe["keeper"] = {k: d_.get(k) for k in ("in_sync", "turns", "library", "model", "last_synced", "understanding")} if st_ == 200 and isinstance(d_, dict) else {"note": "not readable: " + str((d_ or {}).get("error", st_))}
        except Exception as e:  # noqa: BLE001
            loupe["running"] = False
            loupe["error"] = str(e)[:120]
    plans = sorted(p.name for p in (rd / "40-briefs").glob("video-*-plan.md")) if (rd / "40-briefs").is_dir() else []
    briefs = sorted(p.name for p in (rd / "40-briefs").glob("video-*-brief.md")) if (rd / "40-briefs").is_dir() else []
    reqs = [p.name for p in _cf_requests_named(rd / "50-requests", "video-")]
    out({"ok": True, "run": rd.name, "run_dir": str(rd), "mode": st.get("mode"), "analyze_submode": st.get("analyze_submode"),
         "model": st.get("model"), "stage": st.get("stage"), "next_skill": st.get("next_skill"), "next_step": st.get("next_step"),
         "video": st.get("video"), "updated": st.get("updated"), "requested_videos": st.get("requested_videos"),
         "audio_ingest": st.get("audio_ingest"), "memes": st.get("memes"), "effort": effort_of_state(st),
         "static": ({"images": st.get("static_images"), "voice_sample": ((st.get("static") or {}).get("voice") or {}).get("sample"),
                     "subjects": (st.get("static") or {}).get("subjects"), "format": _static_fmt(st) or None}
                    if st.get("analyze_submode") == "static" else None),
         "voiceover": ({"enabled": st["voiceover"].get("enabled"), "method": st["voiceover"].get("method"), "source": st["voiceover"].get("source"),
                        "voice": st["voiceover"].get("voice_name"),
                        "language": st["voiceover"].get("language"), "preference": st["voiceover"].get("preference"),
                        "takes": sorted((st["voiceover"].get("files") or {}).keys()) if isinstance(st["voiceover"].get("files"), dict) else []}
                       if isinstance(st.get("voiceover"), dict) else None),
         "videos": {"recorded": len(vids), "by_status": by_v, "done": [v.get("video") for v in vids if v.get("status") == "done"],
                    "blocked": [{"video": v.get("video"), "blocker": v.get("blocker")} for v in vids if v.get("status") == "blocked"]},
         "submissions": {"total": len(subs), "by_status": by_s, "open": sum(1 for s in subs if s.get("status") in LEDGER_OPEN),
                         "flagged": sum(1 for s in subs if s.get("flagged"))},
         "credits": {"start": st.get("credits_start"), "recorded_in_videos": round(sum(float(v.get("credits") or 0) for v in vids), 2)},
         "loupe": loupe, "files": {"plans": len(plans), "briefs": len(briefs), "requests": len(reqs),
                                   "qc_consults": len(list((rd / "60-outputs").glob("video-*/qc-consult.json"))) if (rd / "60-outputs").is_dir() else 0,
                                   "hints": len(list((rd / "40-briefs").glob("video-*-hints.json"))) if (rd / "40-briefs").is_dir() else 0,
                                   "templates": len(list((rd / "40-briefs").glob("video-*-template.json"))) if (rd / "40-briefs").is_dir() else 0,
                                   "agent_contract": (rd / "50-requests" / "agent-contract.md").is_file()},
         "missing_files": missing[:40], "missing_files_total": len(missing)})


def _git_dirty(paths: list) -> dict:
    try:
        cp = subprocess.run(["git", "-C", str(AWL_HOME.parent), "status", "--porcelain", "--", *paths], capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=30)
        head = subprocess.run(["git", "-C", str(AWL_HOME.parent), "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=30)
        rows = [ln for ln in cp.stdout.splitlines() if ln.strip()]
        return {"head": head.stdout.strip(), "dirty_paths": len(rows), "first": [r[:80] for r in rows[:5]]}
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)[:120]}


def cmd_doctor(a):
    """What this machine and this library have, as facts on one JSON line: the interpreter, ffmpeg/ffprobe, the optional Python
    modules, the cached speech models, the config paths, the MCP servers registered in ~/.claude.json (read only; nothing is called),
    the hooks, Loupe (health and library size), the docs check, git (dirty paths of this library), free disk under the runs root; with
    --run, the state keys and files the skills' hand-offs have written by the run's stage. Nothing here is a verdict."""
    import importlib.util
    import importlib.metadata as im
    import platform

    def mod(name, dist=None):
        ok = importlib.util.find_spec(name) is not None
        ver = None
        if ok:
            try:
                ver = im.version(dist or name)
            except Exception:  # noqa: BLE001
                ver = "?"
        return {"present": ok, "version": ver}

    def tool(name):
        try:
            p = find_tool(name)
        except Exception:  # noqa: BLE001
            p = None
        v = None
        if p:
            try:
                cp = subprocess.run([p, "-version"], capture_output=True, text=True, timeout=10)
                v = (cp.stdout or cp.stderr).splitlines()[0][:60] if (cp.stdout or cp.stderr) else None
            except Exception:  # noqa: BLE001
                v = None
        return {"path": p, "version": v}

    cfg = load_config()
    cache = Path.home() / ".cache" / "huggingface" / "hub"
    whisper_models = sorted(d.name.split("--")[-1] for d in cache.glob("models--*faster-whisper*")) if cache.is_dir() else []
    drafts = Path(cfg_get("capcut.drafts_dir") or "")
    cfg_facts = {"python_in_config_exists": Path(str(cfg.get("python") or "")).is_file(), "runs_root": str(runs_root()), "runs_root_exists": runs_root().is_dir(),
                 "capcut_drafts_dir_exists": drafts.is_dir(), "capcut_template_exists": (drafts / str(cfg_get("capcut.template_draft") or "")).is_dir() if drafts.is_dir() else False,
                 "text_style_learned": bool(cfg_get("capcut.text_style.learned")), "text_style_locked": bool(cfg_get("capcut.text_style.locked")),
                 "whisper_model": cfg.get("whisper_model")}
    try:
        idx = json.loads((AWL_HOME / "models" / "index.json").read_text(encoding="utf-8"))
        cfg_facts["models_in_index"] = len(idx.get("models", {}))
    except Exception as e:  # noqa: BLE001
        cfg_facts["models_index_error"] = str(e)[:100]
    mcp = {}
    try:
        cj = json.loads((Path.home() / ".claude.json").read_text(encoding="utf-8"))
        names = sorted((cj.get("mcpServers") or {}).keys())
        mcp = {"registered": names, "higgsfield": "higgsfield" in names, "capcut": "capcut" in names, "elevenlabs": "elevenlabs" in names}
        if "elevenlabs" in names:              # an own voiceover (item 31): only the base path is read from its env, never the key
            env_ = (cj["mcpServers"]["elevenlabs"] or {}).get("env") or {}
            mcp["elevenlabs_base_path"] = env_.get("ELEVENLABS_MCP_BASE_PATH") or "default: ~/Desktop"
    except Exception as e:  # noqa: BLE001
        mcp = {"error": str(e)[:100]}
    hooks = {}
    try:
        sj = json.loads((AWL_HOME.parent / "settings.json").read_text(encoding="utf-8"))
        for ev, groups in (sj.get("hooks") or {}).items():
            for g in groups:
                for h in g.get("hooks", []):
                    m = re.search(r"([A-Za-z0-9_]+\.py)", str(h.get("command", "")))
                    if m:
                        hooks.setdefault(m.group(1), []).append(ev)
        hooks = {k: {"events": sorted(set(v)), "exists": (AWL_HOME.parent / "hooks" / k).is_file()} for k, v in hooks.items()}
    except Exception as e:  # noqa: BLE001
        hooks = {"error": str(e)[:100]}
    loupe = {"skipped": True}
    if not a.no_loupe:
        try:
            lc = _lc()
            h = lc.health()
            loupe = {"running": bool(h), "url": lc.base_url()}
            if h:
                st_, d = lc.call("GET", "/api/qc/samples?limit=1", key_name="qc", timeout=10)
                loupe["library_size"] = d.get("library_size") if st_ == 200 and isinstance(d, dict) else None
                loupe["qc_key_ok"] = st_ == 200
            st_, d_ = lc.call("GET", "/api/qc/keeper/state", key_name="qc", timeout=10) if h else (0, {})
            loupe["keeper"] = {k: d_.get(k) for k in ("in_sync", "turns", "library", "library_sig", "model", "last_synced", "claude_found", "understanding")} if st_ == 200 and isinstance(d_, dict) else {"note": "not readable: " + str((d_ or {}).get("error", st_))}
        except Exception as e:  # noqa: BLE001
            loupe = {"running": False, "error": str(e)[:120]}
    docs = {"skipped": True}
    if not a.no_docs:
        try:
            cp = subprocess.run([sys.executable, "-X", "utf8", str(AWL_HOME / "scripts" / "docs_tool.py"), "check"], capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=120)
            last = [ln for ln in cp.stdout.splitlines() if ln.strip()]
            docs = {"exit": cp.returncode, "summary": last[-1][:160] if last else None}
        except Exception as e:  # noqa: BLE001
            docs = {"error": str(e)[:120]}
    try:
        du = shutil.disk_usage(str(runs_root() if runs_root().is_dir() else AWL_HOME))
        disk = {"free_gb": round(du.free / 1e9, 1), "total_gb": round(du.total / 1e9, 1)}
    except Exception as e:  # noqa: BLE001
        disk = {"error": str(e)[:100]}
    res = {"ok": True, "python": {"executable": sys.executable, "version": platform.python_version()},
           "tools": {"ffmpeg": tool("ffmpeg"), "ffprobe": tool("ffprobe"), "capcut_cli": shutil.which("capcut"), "claude_cli": shutil.which("claude") or shutil.which("claude.cmd")},
           "modules": {"pypdf": mod("pypdf"), "PIL": mod("PIL", "Pillow"), "numpy": mod("numpy"), "faster_whisper": mod("faster_whisper", "faster-whisper"),
                       "rapidocr": mod("rapidocr_onnxruntime", "rapidocr-onnxruntime"), "librosa": mod("librosa"), "requests": mod("requests")},
           "whisper_models_cached": whisper_models, "config": cfg_facts, "mcp": mcp, "hooks": hooks, "loupe": loupe, "docs_check": docs,
           "git": _git_dirty([str(AWL_HOME), str(AWL_HOME.parent / "commands" / "analyze-with-loupe.md"), str(AWL_HOME.parent / "skills")]), "disk": disk}
    if a.run:
        rd, st = _state_of(a.run)
        stage = str(st.get("stage") or "")
        keys, files = STAGE_EXPECTS.get(stage, ([], []))
        res["run"] = {"run": rd.name, "stage": stage, "next_skill": st.get("next_skill"),
                      "keys_expected_by_stage": keys, "keys_missing": [k for k in keys if _get_dotted(st, k) in (None, "", [], {})],
                      "files_expected_by_stage": files, "files_missing": [f for f in files if not (rd / f).exists()],
                      "note": "expected = what the skills' hand-offs have written by this stage; a missing one is a fact to explain, not a verdict",
                      "stage_known": stage in STAGE_EXPECTS}
    out(res)


_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


def _ids_in(obj, acc: set):
    if isinstance(obj, dict):
        for v in obj.values():
            _ids_in(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            _ids_in(v, acc)
    elif isinstance(obj, str):
        for m in _UUID.finditer(obj):
            acc.add(m.group(0))
    return acc


def cmd_lint_run(a):
    """Cross-checks of a run's own files, as facts: run paths that a plan, pattern card, brief, request or the contract cites and that
    do not exist (NN placeholders skipped); the reference id a plan's header names against state.json -> asset_plan for that video
    number; media ids in a request that no uploads record of the run knows; the length of every request prompt; the preset notice
    bookkeeping (ledger rows mentioning a preset against higgsfield.declined_preset_id); whether the agent contract exists and names
    the run. The agent reads the lists and decides what, if anything, is wrong."""
    rd, st = _state_of(a.run)
    plan_refs = {str(r.get("video")): r.get("ref") for r in st.get("asset_plan") or [] if isinstance(r, dict)}
    pat = re.compile(r"(?:<RUN>|\bRUN|[A-Za-z]:[\\/](?:[^\s`'\"<>|]+[\\/])*?" + re.escape(rd.name) + r")[\\/]([0-9A-Za-z_./\\-]+\.(?:md|json|mp4|png|jpg|jpeg|txt|wav|mka|m4a))")
    cited, missing = 0, []
    docs = []
    for sub, glob_ in (("40-briefs", "*.md"), ("50-requests", "*.md"), ("50-requests", "*.txt")):
        if (rd / sub).is_dir():
            docs += sorted((rd / sub).glob(glob_))
    for f in docs:
        try:
            t = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in pat.finditer(t):
            rel = m.group(1).replace("\\", "/")
            if "NN" in rel or "<" in rel:
                continue
            cited += 1
            if not (rd / rel).exists():
                missing.append({"file": f.name, "path": rel})
    numbering = []
    for f in sorted((rd / "40-briefs").glob("video-*-plan.md")) if (rd / "40-briefs").is_dir() else []:
        nn = f.name.split("-")[1]
        head = f.read_text(encoding="utf-8", errors="replace")[:600]
        refs = sorted(set(re.findall(r"\bV\d{2}\b", head)))
        want = plan_refs.get(nn)
        if want and want not in refs:
            numbering.append({"file": f.name, "video": nn, "asset_plan_ref": want, "refs_in_header": refs})
    known = _ids_in(st.get("assets", {}).get("uploads") or {}, set()) | _ids_in(st.get("higgsfield") or {}, set())
    ledger_jobs = _ids_in([s.get("job_id") for s in st.get("submissions") or [] if isinstance(s, dict)], set())   # a sync pass names its clip's job
    known |= ledger_jobs
    for f in (rd / "50-requests").glob("video-*-uploads.json") if (rd / "50-requests").is_dir() else []:
        try:
            _ids_in(json.loads(f.read_text(encoding="utf-8")), known)
        except (OSError, ValueError):
            pass
    unknown, prompts = [], []
    in_checked, no_source, not_last = 0, [], []
    for f in _cf_requests_named(rd / "50-requests", "video-"):
        try:
            j = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            unknown.append({"file": f.name, "error": str(e)[:80]})
            continue
        params = j.get("params") if isinstance(j.get("params"), dict) else j
        ids = _ids_in(params, set())
        for i in sorted(ids - known):
            unknown.append({"file": f.name, "id": i})
        if ".draft." not in f.name and "frame-request" not in f.name:
            imgs = _pi_images(j, rd)
            in_checked += len(imgs)
            for x in imgs:
                if not x["source"]:
                    no_source.append({"file": f.name, "image": x["label"]})
            pl = [k for k, x in enumerate(imgs) if x["product"]]
            if pl and pl != list(range(len(imgs) - len(pl), len(imgs))):
                not_last.append({"file": f.name, "order": "".join("P" if x["product"] else "-" for x in imgs)})
        pr = params.get("prompt") if isinstance(params, dict) else None
        if isinstance(pr, str):
            prompts.append({"file": f.name, "chars": len(pr)})
    preset_rows = []
    for s in st.get("submissions") or []:
        notes = " ".join(str(h.get("note") or "") for h in (s.get("history") or []) if isinstance(h, dict))
        if "preset" in notes.lower():
            preset_rows.append({"video": s.get("video"), "attempt": s.get("attempt"), "status": s.get("status")})
    contract = rd / "50-requests" / "agent-contract.md"
    ct = contract.read_text(encoding="utf-8", errors="replace") if contract.is_file() else ""
    up_checked, up_bad = 0, []
    for f in sorted((rd / "50-requests").glob("video-*-uploads.json")) if (rd / "50-requests").is_dir() else []:
        up_checked += 1
        try:
            probs = _uploads_problems(json.loads(f.read_text(encoding="utf-8")))
        except (OSError, ValueError) as e:
            probs = ["not JSON: " + str(e)[:80]]
        if probs:
            up_bad.append({"file": f.name, "problems": probs[:6]})
    fr_checked, fr_changed = 0, []
    for sub in st.get("submissions") or []:
        if not isinstance(sub, dict) or sub.get("status") not in (LEDGER_OPEN | LEDGER_DONE_OK) or not sub.get("request_file"):
            continue
        rf = Path(str(sub["request_file"]))
        if not rf.is_file():
            continue
        fr_checked += 1
        try:
            fp_now = _fingerprint(json.loads(rf.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
        if fp_now != sub.get("fingerprint"):
            fr_changed.append({"video": sub.get("video"), "attempt": sub.get("attempt"), "status": sub.get("status"), "file": rf.name,
                               "ledger_fingerprint": sub.get("fingerprint"), "file_fingerprint_now": fp_now})
    out({"ok": True, "run": rd.name,
         "cited_paths": {"documents": len(docs), "checked": cited, "missing": missing[:40], "missing_total": len(missing)},
         "video_numbering": {"asset_plan_videos": len(plan_refs), "plans_whose_header_lacks_the_asset_plan_ref": numbering},
         "media_ids": {"known_from_uploads_and_higgsfield": len(known), "known_ledger_job_ids": len(ledger_jobs), "unknown_in_requests": unknown[:40],
                       "unknown_total": len(unknown)},
         "prompts": prompts, "prompt_note": "the agent contract names 5000 characters as the service's limit; compare",
         "preset": {"declined_preset_id": (st.get("higgsfield") or {}).get("declined_preset_id"), "ledger_rows_mentioning_preset": preset_rows},
         "uploads_files": {"checked": up_checked, "outside_the_schema": up_bad, "schema": "video-NN-uploads.json = {video, schema: 1, uploads: {label: {media_id, file, content_type?, url?, at?}}} (written by `uploads set`)"},
         "inputs": {"image_inputs_checked": in_checked, "without_a_recorded_source": no_source[:40], "without_source_total": len(no_source),
                    "product_images_not_last": not_last[:40],
                    "note": "X2 records where each input came from (params.medias[].source: original, asset_id, prepared, kind) and puts the product images "
                            "last among the image inputs, so the judge can choose them (the admin, 2026-10-30)"},
         "request_freeze": {"checked": fr_checked, "changed_after_their_ledger_entry": fr_changed,
                            "note": "a request file whose content no longer matches the fingerprint of its open or finished ledger entry was edited after the submission (item 29)"},
         "contract": {"exists": contract.is_file(), "names_this_run": rd.name in ct, "loupe_line": bool(re.search(r"^Loupe: (up|down|not used)", ct, re.M)),
                      "audio_line": bool(re.search(r"^Audio ingest: ", ct, re.M)), "qc_fixes_line": bool(re.search(r"^QC fixes: (ask|auto|off)", ct, re.M)),
                      "voiceover_line": bool(re.search(r"^Voiceover: (off|on)", ct, re.M)),
                      "memes_line": bool(re.search(r"^Memes: (n/a|none|include|as your plan)", ct, re.M)),
                      "unresolved_placeholders": sorted(set(re.findall(r"<(?:RUN|AWL|model id|guide path|recreate\|create|ask\|auto\|off|ask\|auto|up\|down|whisper\|frames-only|voiceover|memes|api\|prompts)>", ct)))}})


UPLOAD_KEYS = {"media_id", "file", "content_type", "url", "at", "role", "note"}


def _uploads_problems(d) -> list:
    """What does not fit the one shape of video-NN-uploads.json (facts, no repair): {video, schema: 1, uploads: {label: {media_id, file, ...}}}."""
    probs = []
    if not isinstance(d, dict):
        return [f"the file is a {type(d).__name__}, not an object"]
    if d.get("schema") != 1:
        probs.append("schema is not 1")
    if not isinstance(d.get("video"), str):
        probs.append("video is not a string")
    ups = d.get("uploads")
    if not isinstance(ups, dict):
        probs.append("uploads is not an object of label -> entry")
        ups = {}
    for k in sorted(set(d) - {"video", "schema", "uploads"}):
        probs.append(f"unknown top-level key {k}")
    for label, e in ups.items():
        if not isinstance(e, dict):
            probs.append(f"{label}: entry is not an object")
            continue
        if not re.fullmatch(r"[0-9a-f-]{20,60}", str(e.get("media_id") or "")):
            probs.append(f"{label}: media_id is not an id")
        if not isinstance(e.get("file"), str) or not e.get("file"):
            probs.append(f"{label}: file is missing")
        for k in sorted(set(e) - UPLOAD_KEYS):
            probs.append(f"{label}: unknown key {k}")
    return probs


def _uploads_file(rd, video) -> Path:
    return rd / "50-requests" / f"video-{_cf_nn(video)}-uploads.json"


def cmd_uploads(a):
    """One record per video of what was uploaded to Higgsfield for it (the planners and the agents wrote three shapes by hand in a real run,
    and merging them polluted state.json). set: add or replace one entry {label -> media_id, file (as a full path), content_type, url}; show: the entries of
    one video or of every video, with any shape problem; merge: copy every well-formed entry's media id into state.json -> assets.uploads
    (label -> media_id) under the state lock, listing the files it skipped and why. It records; it never decides which upload a request uses."""
    rd, st = _state_of(a.run)
    if a.action == "set":
        if not (a.video and a.label and a.media_id and a.file):
            fail("uploads set needs --video, --label, --media-id and --file", 2)
        f = _uploads_file(rd, a.video)
        f.parent.mkdir(parents=True, exist_ok=True)
        d = {"video": _cf_nn(a.video), "schema": 1, "uploads": {}}
        if f.is_file():
            try:
                old = json.loads(f.read_text(encoding="utf-8"))
            except ValueError as e:
                fail(f"{f.name} is not JSON ({e}); move it aside before writing", 1)
            if _uploads_problems(old):
                fail(f"{f.name} is not in the schema ({'; '.join(_uploads_problems(old)[:3])}); move it aside before writing", 1)
            d = old
        fp, hit = Path(str(a.file)), None
        if not fp.is_absolute():      # a full path, so every reader finds the file whatever folder it works from (Loupe reads the run's records so)
            hit = next((b / fp for b in (Path.cwd(), rd) if (b / fp).is_file()), None)
        entry = {"media_id": a.media_id, "file": str(hit.resolve()) if hit else str(a.file), "at": now_iso()}
        if a.content_type:
            entry["content_type"] = a.content_type
        if a.url:
            entry["url"] = a.url
        if a.role:
            entry["role"] = a.role
        replaced = a.label in d["uploads"]
        d["uploads"][a.label] = entry
        f.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        out({"ok": True, "file": str(f), "label": a.label, "replaced": replaced, "entries": len(d["uploads"])})
    if a.action == "show":
        files = [_uploads_file(rd, a.video)] if a.video else sorted((rd / "50-requests").glob("video-*-uploads.json")) if (rd / "50-requests").is_dir() else []
        rows = []
        for f in files:
            if not f.is_file():
                rows.append({"file": f.name, "exists": False})
                continue
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
            except ValueError as e:
                rows.append({"file": f.name, "exists": True, "problems": ["not JSON: " + str(e)[:80]]})
                continue
            rows.append({"file": f.name, "exists": True, "video": d.get("video") if isinstance(d, dict) else None, "problems": _uploads_problems(d),
                         "uploads": d.get("uploads") if isinstance(d, dict) and isinstance(d.get("uploads"), dict) else None})
        out({"ok": True, "run": rd.name, "files": rows})
    # merge
    p_state = rd / "state.json"
    merged, skipped = {}, []
    for f in sorted((rd / "50-requests").glob("video-*-uploads.json")) if (rd / "50-requests").is_dir() else []:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except ValueError as e:
            skipped.append({"file": f.name, "problems": ["not JSON: " + str(e)[:80]]})
            continue
        probs = _uploads_problems(d)
        if probs:
            skipped.append({"file": f.name, "problems": probs[:6]})
            continue
        for label, e in d["uploads"].items():
            merged[label] = e["media_id"]
    with FileLock(p_state.with_name("state.json.lock")):
        st2 = json.loads(p_state.read_text(encoding="utf-8"))
        assets = st2.setdefault("assets", {}) if isinstance(st2.get("assets"), dict) or "assets" not in st2 else None
        if assets is None:
            fail("state.json -> assets is not an object; nothing merged", 1)
        ups = assets.setdefault("uploads", {})
        if not isinstance(ups, dict):
            fail("state.json -> assets.uploads is not an object; nothing merged", 1)
        changed = {k: v for k, v in merged.items() if ups.get(k) != v}
        ups.update(merged)
        write_json(p_state, st2)
    out({"ok": True, "run": rd.name, "merged": len(merged), "changed": sorted(changed), "skipped": skipped,
         "note": "only label -> media_id reaches state.json; a file outside the schema is listed here and left alone (fix it with `uploads set`)"})


CONTRACT_SUBS = (("<RUN>", "run"), ("<AWL>", "library"), ("<model id>", "model"), ("<guide path>", "guide path"), ("<recreate|create>", "analyze_submode"),
                 ("<ask|auto|off>", "qc_fixes"), ("<up|down>", "loupe"), ("<whisper|frames-only>", "audio_ingest"), ("<voiceover>", "voiceover"),
                 ("<memes>", "memes"), ("<api|klein|prompts>", "static_images"))


def _contract_memes(st: dict) -> str:
    """The contract's Memes line from state.json -> memes (contract item 32): Create include | none (a Create run without the key includes
    them, as its plans were made); Recreate keeps its references' own inserts; Free follows its plan."""
    sub, m = str(st.get("analyze_submode") or ""), str(st.get("memes") or "")
    if sub == "recreate":
        return "n/a (Recreate keeps each reference's own inserts)"
    if sub == "static":
        return "n/a (Static: no inserts)"
    if m == "none":
        return "none (pure generation: no insert, meme still or meme sound of any kind)"
    if m == "include" or (sub == "create" and not m):
        return "include (only the inserts your plan names)"
    return "as your plan says"


def _contract_voiceover(st: dict, rd: Path) -> str:
    """The contract's Voiceover line from state.json -> voiceover (contract item 31): 'off' when the run has none."""
    vo = st.get("voiceover")
    if not isinstance(vo, dict) or vo.get("enabled") is not True:
        return "off"
    method = {"native": "native (the take is the driving audio)", "lipsync": "lipsync (then a sync_so pass with the take)",
              "overlay": "overlay (no dialogue; the take over the picture)"}.get(vo.get("method"), f"{vo.get('method') or '?'}")
    bits = [f"method {method}"]
    if vo.get("source") == "file":
        bits.append("the user's own voiceover files (source file)")
    else:
        bits.append(f"ElevenLabs voice {vo.get('voice_name') or '?'} ({vo.get('voice_id') or '?'}), model {vo.get('model_id') or 'eleven_v4'}")
    lang = f"language {vo.get('language_name') or vo.get('language') or '?'} ({vo.get('language') or '?'})"
    if vo.get("language_official") is False:
        lang += ", outside the model's official list: pronunciation not checked"
    bits.append(lang)
    if vo.get("preference"):
        bits.append(f"preference: {vo['preference']}")
    if isinstance(vo.get("voices"), dict) and vo["voices"]:
        bits.append("per character: " + ", ".join(f"{k} = {(v.get('voice_name') or v.get('voice_id')) if isinstance(v, dict) else v}"
                                                  for k, v in vo["voices"].items()))
    if isinstance(vo.get("videos"), list) and vo["videos"]:
        bits.append("only videos " + ", ".join(str(x) for x in vo["videos"]))
    return "on: " + "; ".join(bits) + f". Your take: {rd}/30-assets/voiceover/video-NN*.* (state.json -> voiceover.files.NN, with its .json sidecar)"


def cmd_contract(a):
    """Write 50-requests/agent-contract.md from the canonical prompt of production-agents section 2 and this run's state.json: the run and
    library paths, the locked model and its guide path, the sub-mode, the QC-fixes, Loupe, audio-ingest and voiceover lines. A placeholder whose value
    state.json does not hold stays as it is and is listed (the agents must not be spawned with it). Run-specific notes go under their own
    heading at the end, never into the rules. The previous file, when different, is kept beside it with a stamp."""
    rd, st = _state_of(a.run)
    tpl_name = "025_2s_spawning-static.md" if str(st.get("analyze_submode") or "") == "static" else "020_2_spawning.md"    # Static: its own block (item 36)
    tpl_p = AWL_HOME / "reference" / "production-agents" / tpl_name
    if not tpl_p.is_file():            # a temp home (tests) holds no references: the library beside this script does
        tpl_p = Path(__file__).resolve().parent.parent / "reference" / "production-agents" / tpl_name
    tpl = tpl_p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"```\n(.*?)\n```", tpl.replace("\r\n", "\n"), re.S)
    if not m:
        fail("no fenced prompt block in production-agents section 2", 1)
    body = m.group(1)
    model = str(st.get("model") or "")
    guide = ""
    try:
        idx = json.loads((AWL_HOME / "models" / "index.json").read_text(encoding="utf-8"))
        ent = (idx.get("models") if isinstance(idx.get("models"), dict) else idx).get(model) or {}
        guide = str(ent.get("guide") or ent.get("guide_path") or ent.get("doc") or "")
    except (OSError, ValueError, AttributeError):
        guide = ""
    values = {"run": str(rd), "library": str(AWL_HOME), "model": model, "guide path": guide, "analyze_submode": str(st.get("analyze_submode") or ""),
              "qc_fixes": str(st.get("qc_fixes") or "auto"), "loupe": str(st.get("loupe") or "up"), "audio_ingest": str(st.get("audio_ingest") or ""),
              "voiceover": _contract_voiceover(st, rd), "memes": _contract_memes(st), "static_images": str(st.get("static_images") or "")}
    substituted, unresolved = {}, []
    for token, key in CONTRACT_SUBS:
        if values[key]:
            body = body.replace(token, values[key])
            substituted[token] = values[key]
        elif token in body:
            unresolved.append(token)
    if a.notes:
        body += "\n\nRun-specific notes\n" + a.notes.strip() + "\n"
    outp = Path(a.out) if a.out else rd / "50-requests" / "agent-contract.md"
    outp.parent.mkdir(parents=True, exist_ok=True)
    kept = None
    if outp.is_file() and outp.read_text(encoding="utf-8", errors="replace") != body:
        kept = outp.with_name(f"agent-contract.prev-{time.strftime('%Y%m%d-%H%M%S')}.md")
        outp.replace(kept)
    outp.write_text(body, encoding="utf-8")
    out({"ok": True, "file": str(outp), "bytes": len(body.encode("utf-8")), "substituted": substituted, "unresolved_placeholders": unresolved,
         "previous_kept_as": str(kept) if kept else None, "note": "spawn no agent while unresolved_placeholders is not empty (the audio and QC-fixes lines are the user's choices)"})


def cmd_cost_report(a):
    """Credits as the run recorded them, as information (never a gate): credits_start, every job's credits from videos[] (result.json
    as appended by the main session), the submissions by status, the numbers each brief states beside the word 'credits' (as written,
    not summed as truth), and, when --balance is given (the Higgsfield balance tool's answer), start minus balance."""
    rd, st = _state_of(a.run)
    vids = [v for v in st.get("videos") or [] if isinstance(v, dict)]
    jobs = []
    for v in vids:
        for j in v.get("jobs") or []:
            if isinstance(j, dict):
                jobs.append({"video": v.get("video"), "clip": j.get("clip"), "job_id": j.get("job_id"), "credits": j.get("credits"), "attempts": j.get("attempts")})
    subs = [s for s in st.get("submissions") or [] if isinstance(s, dict)]
    by_s = {}
    for s in subs:
        by_s[str(s.get("status") or "?")] = by_s.get(str(s.get("status") or "?"), 0) + 1
    briefs = {}
    for f in sorted((rd / "40-briefs").glob("video-*-brief.md")) if (rd / "40-briefs").is_dir() else []:
        t = f.read_text(encoding="utf-8", errors="replace")
        nums = [float(m.group(1)) for m in re.finditer(r"(\d+(?:\.\d+)?)\s*credits?\b", t)]
        if nums:
            briefs[f.name.split("-")[1]] = nums[:12]
    start = st.get("credits_start")
    res = {"ok": True, "run": rd.name, "credits_start": start, "videos_recorded": len(vids),
           "credits_in_videos": round(sum(float(v.get("credits") or 0) for v in vids), 2), "jobs": jobs,
           "submissions": {"total": len(subs), "by_status": by_s},
           "brief_credit_mentions": briefs, "balance": a.balance,
           "spent_by_balance": round(float(start) - float(a.balance), 2) if a.balance is not None and isinstance(start, (int, float)) else None,
           "note": "information only, never a gate: the ledger records no cost; videos[].credits comes from each result.json; pass --balance <n> from the balance tool to see start minus balance"}
    out(res)


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
    grid = None
    if a.grid:
        from PIL import Image, ImageDraw
        sw = info.get("display_width") or info.get("width") or 0
        files = []
        for r in res:
            if not r["ok"]:
                continue
            with Image.open(r["file"]) as im:
                im = im.convert("RGB")
                sc = im.width / sw if sw else 1.0
                d = ImageDraw.Draw(im)
                step = a.grid * sc
                x = 0.0
                while x < im.width:
                    d.line((x, 0, x, im.height), fill=(255, 255, 0), width=1)
                    d.text((x + 2, 2), str(int(round(x / sc))), fill=(255, 255, 0))
                    x += step
                y = 0.0
                while y < im.height:
                    d.line((0, y, im.width, y), fill=(0, 255, 255), width=1)
                    d.text((2, y + 2), str(int(round(y / sc))), fill=(0, 255, 255))
                    y += step
                d.text((4, im.height - 14), f"t={r['t']}", fill=(255, 0, 0))
                gf = Path(r["file"]).with_name(Path(r["file"]).stem + "-grid.jpg")
                im.save(gf, quality=90)
            files.append(str(gf))
        grid = {"step_px_in_source": a.grid, "scale_of_the_extracted_frame": round(sc, 4) if res else None, "files": files,
                "note": "the labels are source pixel coordinates (x in yellow, y in cyan): read a crop box or a product base off them"}
    sheets = []
    if a.sheet:
        sheets = build_storyboard(res, od / f"sheet-{pre}", a.title or f"{Path(a.video).name} {pre}",
                                  info.get("orientation", "portrait"), dense=len(res) > 12)
    out({"ok": all(r["ok"] for r in res), "frames": [{"t": r["t"], "file": r["file"], "ok": r["ok"]} for r in res],
         "sheets": sheets, **({"grid": grid} if grid else {})})


# --------------------------------------------------------------------------- Higgsfield transfer helpers

def _capture_full(cid) -> tuple:
    """(status, answer, capture) for one hook capture by id, with its payload. Loupe lists captures newest first and has no route for one id:
    the row is found in the plain list (no payloads, any age), then its payload comes from the listing of its job, or from the shortest
    newest-first listing that holds it."""
    import urllib.parse
    s, d = _cf_api("GET", "/api/captures?limit=1000000")
    if s != 200:
        return s, d or {}, None
    rows = d.get("captures", [])
    k = next((i for i, c in enumerate(rows) if str(c.get("id")) == str(cid)), None)
    if k is None:
        return 200, d, None

    def pick(dd):
        return next((c for c in (dd.get("captures", []) if isinstance(dd, dict) else []) if str(c.get("id")) == str(cid)), None)
    job = str(rows[k].get("job") or "").strip()
    if job:
        s2, d2 = _cf_api("GET", "/api/captures?full=1&limit=100&job=" + urllib.parse.quote(job))
        cap = pick(d2) if s2 == 200 else None
        if cap:
            return 200, d2, cap
    s3, d3 = _cf_api("GET", f"/api/captures?full=1&limit={k + 51}")      # + 51: captures that arrived since the first listing
    return s3, d3 or {}, (pick(d3) if s3 == 200 else None)


def _capture_slot(a, p: Path) -> tuple[str, str, str]:
    """The upload slot (upload_url, content_type, media_id) of a hook capture: the one whose filename matches the file, else --slot (default 0)."""
    s, d, cap = _capture_full(a.capture)
    if s != 200:
        fail(f"Loupe did not answer for capture {a.capture}: " + str((d or {}).get("error", s)), 2)
    if not cap:
        fail(f"capture {a.capture} is not in Loupe (the hook keeps every media_upload answer; `caught-flag list` and Loupe's Flags page show the ids)", 2)
    raw = (cap.get("payload") or {}).get("response", "")
    try:
        resp = json.loads(raw) if isinstance(raw, str) else raw
    except ValueError:
        resp = None
    slots = []
    if isinstance(resp, dict):
        slots = resp.get("uploads") if isinstance(resp.get("uploads"), list) else ([resp] if resp.get("upload_url") else [])
    elif isinstance(resp, list):
        slots = [x for x in resp if isinstance(x, dict) and x.get("upload_url")]
    if not slots:
        for m in re.finditer(r'"upload_url"\s*:\s*"([^"]+)"', raw if isinstance(raw, str) else ""):
            slots.append({"upload_url": m.group(1)})
    if not slots:
        fail(f"capture {a.capture} holds no upload_url (tool {cap.get('tool')}, signals {(cap.get('payload') or {}).get('signals')})", 2)
    k = next((i for i, x in enumerate(slots) if str(x.get("filename") or "") == p.name), None)
    if a.slot is not None:
        k = a.slot
    if k is None:
        if len(slots) > 1:
            fail(f"capture {a.capture} holds {len(slots)} upload slots and none is named {p.name}: give --slot N (0-based)", 2)
        k = 0
    if not 0 <= k < len(slots):
        fail(f"--slot {k} is out of range: capture {a.capture} holds {len(slots)} slot(s)", 2)
    x = slots[k]
    return str(x.get("upload_url")), str(x.get("content_type") or ""), str(x.get("media_id") or "")


def cmd_hf_put(a):
    p = Path(a.file)
    if not p.exists():
        fail(f"file not found: {p}", 2)
    media_id = ""
    if a.capture:
        a.url, ct_cap, media_id = _capture_slot(a, p)
        a.content_type = a.content_type or ct_cap
    elif not a.url:
        fail("give --url (the upload_url of the media_upload answer) or --capture <id> (the hook's capture of that answer)", 2)
    ct = a.content_type or CONTENT_TYPES.get(p.suffix.lower(), "application/octet-stream")
    last = None
    for attempt in range(a.retries):
        try:
            import requests  # type: ignore
            with open(p, "rb") as f:
                r = requests.put(a.url, data=f, headers={"Content-Type": ct}, timeout=a.timeout)
            if r.status_code == 200:
                out({"ok": True, "status": 200, "bytes": p.stat().st_size, "content_type": ct,
                     "etag": r.headers.get("ETag"), **({"media_id": media_id, "capture": a.capture} if a.capture else {})})
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
        n = _download(a.url, dest, a.retries, headers={"User-Agent": "Mozilla/5.0 (analyze-with-loupe)"})
        s = media_summary(dest)
    except Exception as e:
        fail(str(e)[:300])
    if not s.get("has_audio"):
        fail("the downloaded file has no audio stream", 1, file=str(dest))
    meta = {"file": str(dest), "url": a.url, "page": a.page, "license": a.license, "title": a.title,
            "author": a.author, "role": a.role, "fetched": now_iso(), "duration_s": s.get("duration_s")}
    write_json(dest.with_name(dest.name + ".source.json"), meta)
    out({"ok": True, "bytes": n, **meta})


def _voice_numbers(src: Path, transcript=None) -> dict:
    """The narrator's voice as numbers (Static writes the voice description from them): pitch median and spread over the voiced frames of the
    first 90 s, the voiced share, energy variation, and from a transcript the words per minute of speech and the pauses between words.
    Measured, never listened to; no verdict."""
    try:
        import numpy as np
        import librosa
    except ImportError:
        return {"error": "librosa and numpy are required"}
    work = Path(os.environ.get("TEMP") or os.environ.get("TMP") or ".") / f"awl-voice-{os.getpid()}.wav"
    cp = run([find_tool("ffmpeg"), "-nostdin", "-y", "-loglevel", "error", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000", "-t", "90", str(work)], timeout=600)
    if cp.returncode != 0 or not work.exists():
        return {"error": "could not decode the audio"}
    try:
        y, sr = librosa.load(str(work), sr=16000, mono=True)
    finally:
        work.unlink(missing_ok=True)
    res = {"analysed_s": round(len(y) / sr, 1) if sr else 0}
    if len(y) < sr:
        return {**res, "error": "under one second of audio"}
    f0, vflag, _p = librosa.pyin(y, fmin=65, fmax=400, sr=sr, frame_length=1024)
    v = f0[~np.isnan(f0)]
    res["voiced_share"] = round(float(np.mean(vflag)), 3) if len(vflag) else None
    if len(v):
        p10, p50, p90 = (float(np.percentile(v, q)) for q in (10, 50, 90))
        res.update({"pitch_hz_median": round(p50, 1), "pitch_hz_p10": round(p10, 1), "pitch_hz_p90": round(p90, 1),
                    "pitch_spread_semitones": round(12 * math.log2(p90 / p10), 2) if p10 > 0 else None})
    rms = librosa.feature.rms(y=y)[0]
    res["energy_cv"] = round(float(np.std(rms) / (np.mean(rms) + 1e-9)), 3)
    if transcript:
        try:
            tr = json.loads(Path(transcript).read_text(encoding="utf-8"))
            ws = [w for s in tr.get("segments", []) for w in s.get("words", [])]
            if len(ws) >= 2:
                span = ws[-1]["e"] - ws[0]["s"]
                gaps = [ws[i]["s"] - ws[i - 1]["e"] for i in range(1, len(ws))]
                pauses = [g for g in gaps if g >= 0.25]
                res.update({"words": len(ws), "words_per_minute": round(len(ws) / (span / 60), 1) if span > 0 else None,
                            "pauses_per_minute": round(len(pauses) / (span / 60), 1) if span > 0 else None,
                            "pause_s_median": round(statistics.median(pauses), 2) if pauses else None,
                            "pause_s_max": round(max(pauses), 2) if pauses else None})
        except (OSError, ValueError, KeyError):
            res["transcript_error"] = "not read"
    return res


def cmd_audio_profile(a):
    prof, err = _audio_profile(Path(a.audio), Path(a.out), a.transcript, a.cuts)
    if err:
        fail(err, 1)
    if getattr(a, "voice", False):
        prof["voice"] = _voice_numbers(Path(a.audio), a.transcript)
        write_json(Path(a.out), prof)
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
    # the user approved this file; the facts are recorded beside it for the agent to read, nothing here refuses the user's approval
    facts = {"has_video": bool(info.get("has_video")), "size": f"{info.get('display_width')}x{info.get('display_height')}", "expected_size": a.expect_size,
             "has_audio": bool(info.get("has_audio")), "original_has_audio": bool(entry.get("has_audio"))}
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
    out({"ok": True, "final": str(dest), "facts": facts,
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
    short_by = round(want - g_dur, 3) if want and g_dur else 0.0
    facts = {"has_video": bool(f_info.get("has_video")), "has_audio": bool(f_info.get("has_audio")), "audio_was_available": bool(audio),
             "duration_s": f_info.get("duration_s"), "requested_duration_s": dur,
             "size": f"{f_info.get('display_width')}x{f_info.get('display_height')}"}
    if ref_info:
        facts["source_size"] = f"{ref_info['display_width']}x{ref_info['display_height']}"
    if _carry_join(gen, dst, end=f_info.get("duration_s")):          # the picture's timeline is kept: so is its join record
        facts["join_record"] = str(dst) + JOIN_SUFFIX
    out({"ok": True, "file": str(dst), "duration_s": f_info.get("duration_s"), "original_segment_s": want,
         "generated_shorter_by_s": max(short_by, 0.0),
         "note": ("the generated clip is shorter than the original segment; the original audio was cut at the "
                  "generated length (start stays in sync)") if short_by > 0.0005 else None,
         "facts": facts})


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
    """Where do the generated picture's actions happen compared with the source's? The original audio
    is laid over the generated picture (restore-audio), so every action, mouth movement and impact must
    land where its sound is. Measures per-frame motion energy of the source segment and the output:
    global offset, per-window offsets (a steady offset can be fixed in post, a changing one cannot),
    duration difference, and a side-by-side sheet (source | output at the same timestamps) for visual
    confirmation. It reports numbers and never a verdict or a fix: the agent decides."""
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
        windows.append({"t": round((i0 + W / 2) / fps, 2),
                        "offset_s": None if k is None else round(k / fps, 3),
                        "corr": None if k is None else round(c, 3),
                        "motion_ratio": round(float(x.std()) / s_std, 2)})          # the window's motion against the whole segment's
    # the summary below uses the windows that pass the two filters the caller names (--min-corr, --min-motion); every window is listed in sync-check.json
    rel = [w for w in windows if w["offset_s"] is not None and w["corr"] >= a.min_corr and w["motion_ratio"] >= a.min_motion]
    lags = [w["offset_s"] for w in rel]
    drift = None
    if len(rel) >= 3:
        ts, ls = np.array([w["t"] for w in rel]), np.array(lags)
        if float(ts.var()) > 0:
            drift = round(float(((ts - ts.mean()) * (ls - ls.mean())).mean() / ts.var()) * 10.0, 3)
    med = round(float(np.median(lags)), 3) if lags else g_off
    spread = round(max(lags) - min(lags), 3) if lags else None
    bad = [w for w in rel if abs(w["offset_s"]) > tol]          # a list on request: the windows whose offset is beyond the --tol the caller gave
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
    res = {"ok": True, "source": str(src), "output": str(outv),
           "start_s": start, "compared_s": span, "source_segment_s": round(seg, 3), "output_s": o_dur,
           "duration_diff_s": round(o_dur - seg, 3),
           "global_offset_s": g_off, "global_corr": None if g_c is None else round(g_c, 3),
           "filters": {"min_corr": a.min_corr, "min_motion_ratio": a.min_motion},
           "windows_used": len(rel), "windows_total": len(windows),
           "median_window_offset_s": med, "window_spread_s": spread, "drift_s_per_10s": drift,
           "tolerance_s": tol, "windows_beyond_tolerance": [{"t": w["t"], "offset_s": w["offset_s"]} for w in bad][:12],
           "windows": windows if len(windows) <= 60 else None,
           "anchors_s": anchors, "sheet": str(sheet) if sheet else None,
           "note": "measurements only, no verdict: whether the output is in sync, carries a steady offset (fixable by trimming its head or moving the audio start), "
                   "drifts (the offset changes along the clip) or cannot be told is for the agent to read from these numbers and the side-by-side sheet. "
                   "Times are on the output timeline; a positive offset = the output's action happens later than in the source (so after its sound)"}
    (od / "sync-check.json").write_text(json.dumps({**res, "windows": windows}, indent=1), encoding="utf-8")
    out(res)


def cmd_qc(a):
    """Storyboard and MEASUREMENTS of an output, beside what was expected: size, duration, aspect, audio, black and frozen stretches, and the
    on-screen text the OCR saw (how often, where, how confident) beside the text that was planned. It reports numbers and lists and says nothing
    about whether the video is good enough: reading the storyboard and these numbers against the mode's rules, and deciding, is the agent's job."""
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
                      "all_frames_extracted": all(r["ok"] for r in res), "sheets": dsheets})
    ff = find_tool("ffmpeg")
    cp = run([ff, "-hide_banner", "-nostdin", "-i", v, "-map", "0:v:0", "-vf",
              "blackdetect=d=0.2:pix_th=0.10,freezedetect=n=-60dB:d=0.6", "-an", "-f", "null", "-"], timeout=1800)
    blacks = [{"start": float(m.group(1)), "end": float(m.group(2))}
              for m in re.finditer(r"black_start:([0-9.]+)\s+black_end:([0-9.]+)", cp.stderr)]
    freezes = [float(m.group(1)) for m in re.finditer(r"freeze_start:\s*([0-9.]+)", cp.stderr)]
    ew, eh = [int(x) for x in a.expect_size.lower().split("x")]
    checks = {"duration_s": dur, "aspect": info.get("aspect"), "size": f"{info.get('display_width')}x{info.get('display_height')}",
              "has_audio": info.get("has_audio"), "black_spans": blacks, "freeze_starts": freezes,
              "expected": {"size": a.expect_size, "aspect": a.expect_aspect, "duration_s": a.expect_duration}}
    checks["size_delta_px"] = [(info.get("display_width") or 0) - ew, (info.get("display_height") or 0) - eh]
    if a.expect_duration:
        checks["duration_delta_s"] = round(dur - a.expect_duration, 3)
    if a.expect_aspect:
        xw, xh = [float(x) for x in a.expect_aspect.split(":")]
        ar = info["display_width"] / info["display_height"]
        checks["aspect_error_pct"] = round(abs(ar - xw / xh) / (xw / xh) * 100, 2)
    text = {"available": False, "skipped": True}
    if not a.no_ocr and base:
        step = max(1, math.ceil(len(base) / 12))
        text = ocr_frames(base[::step][:11] + base[-1:])
    spans = (text.get("spans") or []) if text.get("available") else []
    checks["mode"] = a.mode
    checks["planned_text"] = [x.strip() for x in re.split(r"[|\n]", a.allowed_text or "") if x.strip()]
    checks["visible_text"] = ([{k: s.get(k) for k in ("text", "first_t", "last_t", "hits", "share_of_frames_scanned", "y_rel", "score_mean", "chars", "band_distinct_texts")}
                               for s in spans] if text.get("available") else None)
    checks["frames_scanned_for_text"] = text.get("frames_scanned") if text.get("available") else None
    checks["dense_checkpoints"] = [{"label": d["label"], "start": d["start"], "end": d["end"], "frames": d["frames"]}
                                   for d in dense]
    write_json(od / "qc.json", {"info": info, "checks": checks, "ocr": text, "sheets": sheets, "dense": dense})
    out({"ok": True, "qc_json": str(od / "qc.json"),
         "sheets": sheets, "dense": dense, "checks": checks,
         "note": "measurements beside the expectations, no verdict: compare planned_text with visible_text and read the storyboard yourself"})


# --------------------------------------------------------------------------- output format: 9:16 720p

def _encode_args(crf: int = 18) -> list:
    return ["-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart"]


def cmd_conform(a):
    """Bring a clip to exactly WxH (default 720x1280) without stretching: scale-to-cover + focus crop (or --mode pad).
    It reports `lost_fraction`, the share of the picture the crop removes, and never refuses a crop: --dry-run reports it
    without writing anything, so that the agent can decide first (a large loss is a reason to use Higgsfield `reframe` or to
    regenerate from a 9:16 start frame instead)."""
    src = Path(a.video)
    info = media_summary(src)
    W, H = a.width, a.height
    iw, ih = info["display_width"], info["display_height"]
    if (iw, ih) == (W, H) and info.get("rotation", 0) == 0:
        if not a.dry_run and str(src.resolve()) != str(Path(a.out).resolve()):
            shutil.copyfile(src, a.out)
            _carry_join(src, a.out)
        out({"ok": True, "file": a.out, "action": "none (already exact)", "lost_fraction": 0.0, **({"dry_run": True} if a.dry_run else {})})
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
        cx = min(max(a.focus_x * sw - W / 2, 0), sw - W)
        cy = min(max(a.focus_y * sh - H / 2, 0), sh - H)
        vf = f"scale={sw}:{sh}:flags=lanczos,crop={W}:{H}:{int(cx)}:{int(cy)},setsar=1"
        action = f"scale-to-cover {iw}x{ih}->{sw}x{sh} + crop {W}x{H} at focus ({a.focus_x},{a.focus_y})"
        cmd = [ff, "-nostdin", "-y", "-loglevel", "error", "-i", str(src), "-vf", vf, "-map", "0:v:0",
               "-map", "0:a?", *_encode_args(a.crf), "-c:a", "aac", "-b:a", "192k", a.out]
    if a.dry_run:
        out({"ok": True, "dry_run": True, "action": action, "lost_fraction": lost, "input": f"{iw}x{ih}", "output_size": f"{W}x{H}"})
    cp = run(cmd, timeout=3600)
    if cp.returncode != 0:
        fail("ffmpeg failed: " + cp.stderr[-600:])
    o = media_summary(a.out)
    ok = (o["display_width"], o["display_height"]) == (W, H)          # did the tool produce the size it was asked for
    _carry_join(src, a.out)          # the timeline is kept: so is the join record
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


_NUM_PARTS = sorted(("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen "
                     "eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred thousand million billion oh").split(),
                    key=len, reverse=True)
_SPOKEN_ABBR = {"st": "saint", "mt": "mount", "mr": "mister", "mrs": "missus", "dr": "doctor", "vs": "versus"}


def _is_number_token(w: str) -> bool:
    """A normalised word that only spells a number ("seventeen", "sixtynine", "oh") or is written in digits ("1769", "600")."""
    if not w:
        return False
    if re.fullmatch(r"\d[\d,.]*(?:st|nd|rd|th|s)?", w):
        return True
    rest = w
    while rest:
        part = next((p for p in _NUM_PARTS if rest.startswith(p)), None)
        if part is None:
            return False
        rest = rest[len(part):]
    return True


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
    starts = [round(ev[0]["s"], 2) for ev in events]
    for i, ev in enumerate(events):
        start = starts[i]
        end = max(ev[-1]["e"] + (0.05 if i + 1 < len(events) else 0.0), start + 0.25)   # at least 0.25 s on screen ...
        if i + 1 < len(events):
            end = min(end, starts[i + 1])   # ... but never overlapping the next caption (a short word next to a quick one stays shorter)
        res.append({"start": start, "end": round(max(end, start + 0.01), 2), "text": " ".join(w["w"] for w in ev), "preset": "caption"})
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
        mode = audio_ingest_of(resolve_run(a.run)) if a.run else a.audio_ingest
        if mode not in AUDIO_INGEST:
            fail("--from-speech runs speech-to-text: name the run (--run RUN, reads state.json -> audio_ingest) or pass --audio-ingest whisper", 2)
        if mode != "whisper":
            fail("--from-speech runs speech-to-text and this run is frames-only (state.json -> audio_ingest): time the captions with --spec from the frames and the cuts", 2)
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
    _carry_join(a.video, a.out)          # the timeline is kept: so is the join record
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
    _carry_join(a.video, a.out)          # the timeline is kept: so is the join record
    out({"ok": True, "file": a.out, "filters": filters, "output": f"{o['display_width']}x{o['display_height']}"})


# --------------------------------------------------------------------------- trim / concat

# The join record (the user, 2026-10-29: a frame of a joined video is tied to the generation that made it, and a Loupe prompt box holds only the prompts
# of the generations its frames come from). `concat` writes <output>.join.json beside what it joins: the output's sha1 and every piece in order with
# the clip and attempt it sits in (60-outputs/video-NN/c1/a2/...) and the seconds of the output it fills. A command that keeps the timeline of a joined
# file (restore-audio, conform, clean, captions) or trims it (trim, shifted) writes one for its output too, so the clean video and its copies carry it.
# Loupe reads it by the file's own bytes; it is a fact of the join, nothing judged.
JOIN_SUFFIX = ".join.json"


def _file_sha1(p: Path) -> str:
    h = hashlib.sha1()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _clip_of_path(p) -> tuple[str, int]:
    """The clip (c1 ...) and attempt (2 for a2 ...) a file of a video's output folder sits in: .../video-NN/c1/a2/c1a.mp4 is ('c1', 2); ('', 0) for a
    file outside every clip folder (an insert, another joined file)."""
    parts = Path(p).resolve().parts
    vi = next((i for i, x in enumerate(parts) if re.fullmatch(r"video-\d+", x)), None)
    rest = parts[vi + 1:-1] if vi is not None else ()
    clip = next((x for x in rest if re.fullmatch(r"c\d+", x)), "")
    att = next((int(x[1:]) for x in rest[rest.index(clip) + 1:] if re.fullmatch(r"a\d+", x)), 0) if clip else 0
    return clip, att


def _join_record_of(p: Path) -> dict | None:
    """The join record beside a file (<file>.join.json) when it is that file's (same sha1)."""
    rec = Path(str(p) + JOIN_SUFFIX)
    try:
        j = json.loads(rec.read_text(encoding="utf-8"))
        return j if isinstance(j, dict) and j.get("sha1") == _file_sha1(Path(p)) else None
    except (OSError, ValueError):
        return None


def _carry_join(src, out, shift: float = 0.0, end: float | None = None) -> bool:
    """A video made from a joined one with its timeline kept (shifted by `shift` and cut at `end` for a trim) keeps the join record: <out>.join.json with
    the output's own sha1 and the same pieces.  False when the source has none."""
    j = _join_record_of(Path(src))
    if not j or not Path(out).is_file():
        return False
    pieces = []
    for x in j.get("pieces") or []:
        a, b = float(x["t_from"]) - shift, float(x["t_to"]) - shift
        if end is not None:
            b = min(b, end - shift)
        a = max(a, 0.0)
        if b > a + 1e-6:
            pieces.append({**x, "t_from": round(a, 3), "t_to": round(b, 3)})
    write_text(Path(str(out) + JOIN_SUFFIX), json.dumps({**j, "file": Path(out).name, "sha1": _file_sha1(Path(out)), "made_from": str(Path(src).resolve()),
                                                         "written": now_iso(), "pieces": pieces}, ensure_ascii=False, indent=1))
    return True


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
    carried = _carry_join(a.video, a.out, shift=a.start, end=end)
    out({"ok": True, "file": a.out, "duration_s": o.get("duration_s"), **({"join_record": a.out + JOIN_SUFFIX} if carried else {})})


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
# Caught flags. The flag record lives in Loupe (~/.claude/loupe, the web app); `caught-flag` is how the pipeline writes to it
# (add | set | reconcile | list | open). No step of a run and no agent reads the record (command item 23): it is for the person
# who opens Loupe. The script gathers what the run already knows (the video, the attempt, the request's prompt and parameters,
# every input with its file, type, thumbnail and file facts, the reference and its source segment, the job and its ledger row,
# the raw response a hook captured); the agent adds the judgement (Higgsfield's reply, the suspected trigger, which input, which
# words, which part of a video, the grouping tags). Loupe adds the history evidence (the same input elsewhere, similar flags).
# If Loupe cannot be reached a new flag is queued in loupe/data/outbox and recorded when it starts: nothing is lost.

LOUPE_HOME = Path(os.environ.get("LOUPE_HOME") or (Path.home() / ".claude" / "loupe"))
KEEPER_SYNC_WAIT = int(os.environ.get("AWL_KEEPER_SYNC_WAIT") or 25)   # seconds `loupe ensure` waits for the keeper sync before reporting `syncing`
# How a sample's prompts are named wherever the pipeline hands them on (the user, 2026-10-29: every agent, the QC, the keeper and the judge understand
# which prompt is wrong, which is correct and which is just an example): Loupe's boxes, as its record names them.
LOUPE_PROMPTS_WORDS = ("a sample marked prompts (pair, wrong or fixed) keeps, each named by what it is: the flawed version's prompt (the prompt of each generation the "
                       "frames called WRONG come from: they generated the flawed version) and the correct version's prompt (the prompt of each generation the frames "
                       "called RIGHT come from, from either video: they generated the correct version), only the boxes it has frames for (frames called RIGHT only: "
                       "the correct version's prompt alone; frames called WRONG only: the flawed version's alone); an Examples sample keeps one box, the example "
                       "prompt of each generation of its one video its Example frames come from (where prompt_roles says example: a suggestion of what could have "
                       "changed or how it could have been done another way, neither a bad generation nor a correct one); a box holds no other generation, and each "
                       "prompt in it sits under the line that says what it is, the seconds of which video it generated and the frames it made (S12-P1 in the record)")


def _lc():
    if str(LOUPE_HOME) not in sys.path:
        sys.path.insert(0, str(LOUPE_HOME))
    import loupe_client
    return loupe_client


# How long a consult (QC, plan or template) may take: Loupe waits up to 120 s for a running keeper call (its LOCK_WAIT), then makes keeper calls of up
# to 240 s each (KEEPER_CALL_TIMEOUT, the admin, 2026-10-30; 150 s before: a boot, the question, the template's second step, up to two rounds of the
# keeper's requests, the round that hands it the prompts of the samples it cites: 1440 s at worst), plus a margin of 60 s; a consult of 209 s was cut
# at the old 190 s and its answer lost. A Bash call that outlasts its own timeout goes on in the background, so the agent still gets the answer.
CONSULT_TIMEOUT = float(os.environ.get("AWL_CONSULT_TIMEOUT") or 1620)
TEMPLATE_BUSY_RETRIES = int(os.environ.get("AWL_TEMPLATE_BUSY_RETRIES") or 3)   # a template asked while another keeper call holds the lock is asked again
# The brief to the judge (the agent's words, the checked draft request's prompt and its must-carry lines) and the locked model's request structure go
# whole: a video generation prompt is never cut (the user, 2026-10-29).
UPLOAD_ONLY_CAPTURE = re.compile(r"^signals: upload( \||$)")    # a media_upload answer the hook keeps for `hf-put --capture`, never a flag


def _cf_api(method, path, body=None, key="pipeline", timeout=60):
    lc = _lc()
    if not lc.ensure():
        return 0, {"ok": False, "error": "Loupe is not running and could not be started (python ~/.claude/loupe/loupe.py serve)"}
    return lc.call(method, path, body, key_name=key, timeout=timeout)


def _cf_facts(path, ocr=True):
    """File facts for a flag input: sha1, size, dimensions, duration, perceptual hash, text seen on screen (Loupe's facts module)."""
    try:
        if str(LOUPE_HOME) not in sys.path:
            sys.path.insert(0, str(LOUPE_HOME))
        from loupe_app import facts as lf
        return lf.file_facts(path, ocr=ocr)
    except Exception as e:  # noqa: BLE001
        return {"facts_error": str(e)[:160]}


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


def _cf_sentence_diff(old: str, new: str) -> str:
    """What changed between the failed and the accepted prompt, sentence by sentence (- removed, + added), every changed sentence whole and all of
    them (the user, 2026-10-29: a video generation prompt is never trimmed)."""
    import difflib
    def sp(t):
        return [s.strip() for s in re.split(r"(?<=[.;!?])\s+|\n+", t or "") if s.strip()]
    a_, b_ = sp(old), sp(new)
    lines = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a_, b_, autojunk=False).get_opcodes():
        if op in ("replace", "delete"):
            lines += ["- " + s for s in a_[i1:i2]]
        if op in ("replace", "insert"):
            lines += ["+ " + s for s in b_[j1:j2]]
    return "\n".join(lines)


_CF_SNAP = {}
CF_KINDS = ["moderation-block", "refused-no-reason", "media-flagged", "output-flagged", "preset-notice", "other"]
CF_CAUSES = ["prompt-wording", "reference-video", "image-reference", "output", "parameter", "unknown"]
CF_STATUS = ["open", "cleared", "persistent"]
CF_TERMS = re.compile(r"moderat|flag|nsfw|refus|polic|safety|blocked|copyright|\bip\b|celebrit|likeness|preset_recommendation|"
                      r"rejected before creation|no reason|no error", re.I)
CF_ROLE_LABEL = {"image_references": "Image", "video_references": "Video", "audio_references": "Audio"}
CF_PARAM_KEYS = ("model", "mode", "duration", "duration_policy", "aspect_ratio", "resolution", "generate_audio",
                 "enable_thinking", "count", "declined_preset_id")


def _cf_outbox_find(eid):
    ob = Path(os.environ.get("LOUPE_DATA") or (LOUPE_HOME / "data")) / "outbox"
    for p in sorted(ob.glob("*.json")) if ob.is_dir() else []:
        try:
            j = json.loads(p.read_bytes().decode("utf-8"))
        except (OSError, ValueError):
            continue
        if (j.get("doc") or {}).get("id") == eid:
            return p, j
    return None, None


def _cf_load(eid=None, q="") -> list:
    """Flag entries from Loupe: one by id, or those matching a search (the web app's operators: status:open run:... tag:...)."""
    import urllib.parse
    if eid:
        if str(eid).startswith("CF-Q"):
            p, j = _cf_outbox_find(eid)
            if j:
                _CF_SNAP[eid] = json.dumps(j["doc"], sort_keys=True)
                return [j["doc"]]
            # Loupe has ingested the queued flag and given it its own number; the queue note in its log names the provisional id
            s, d = _cf_api("GET", "/api/flags?limit=50&q=" + urllib.parse.quote(str(eid)))
            ents = [e for e in (d.get("entries", []) if s == 200 else [])
                    if any(str(eid).lower() in str(n.get("note", "")).lower() for n in e.get("log") or [])][:1]
            if not ents:
                fail(f"{eid} not found: it is not in Loupe's outbox, and no recorded flag names it in its log", 1)
        else:
            s, d = _cf_api("GET", f"/api/flags/{eid}")
            if s != 200:
                fail(f"{eid}: {d.get('error', 'not found')}", 1)
            ents = [d["entry"]]
    else:
        s, d = _cf_api("GET", "/api/flags?limit=5000&q=" + urllib.parse.quote(q or ""))
        if s != 200:
            fail("cannot read the flags: " + str(d.get("error")), 1)
        ents = d["entries"]
    for e in ents:
        _CF_SNAP[e["id"]] = json.dumps(e, sort_keys=True)
    return ents


def _cf_save(entries: list):
    """Push what changed since _cf_load to Loupe: a new entry is created (Loupe assigns its id), a changed one replaced."""
    lc = _lc()
    for e in entries:
        cur = json.dumps(e, sort_keys=True)
        eid = e.get("id", "")
        if eid in _CF_SNAP:
            if _CF_SNAP[eid] == cur:
                continue
            if str(eid).startswith("CF-Q"):
                p, j = _cf_outbox_find(eid)
                try:
                    if not p:
                        raise FileNotFoundError(eid)
                    j["doc"] = e
                    with open(p, "r+b") as fh:          # the queued file itself only: one Loupe has just ingested is never written again (a duplicate)
                        fh.write(json.dumps(j, ensure_ascii=False).encode("utf-8"))
                        fh.truncate()
                except OSError:
                    fail(f"{eid} was recorded by Loupe while this change was saved: run the same command again (it finds the flag under its new number)", 1)
                continue
            s, d = _cf_api("PUT", f"/api/flags/{eid}", e)
            if s != 200:
                fail(f"Loupe refused the update of {eid}: {d.get('error')}", 1)
        else:
            s, d = _cf_api("POST", "/api/flags", e)
            if s == 200:
                e["id"] = d["id"]
            else:
                e["id"] = "CF-Q" + os.urandom(4).hex()
                e["queued"] = True
                why = "could not be reached" if s == 0 else f"answered {s}"
                # Loupe gives a queued flag its own number when it ingests it; this note keeps the provisional id findable (`caught-flag set --id CF-Q…`)
                e.setdefault("log", []).append({"at": now_iso(), "note": f"queued as {e['id']} (Loupe {why})", "by": "pipeline"})
                lc.queue("add", e)
                print(f"WARNING: Loupe {why} ({(d or {}).get('error')}); the flag is queued as {e['id']} and recorded from Loupe's outbox "
                      f"(about 20 s while Loupe runs, else when it starts); `caught-flag set --id {e['id']}` finds it before and after.", file=sys.stderr)
        _CF_SNAP[e["id"]] = json.dumps(e, sort_keys=True)


def _cf_run_dir(run):
    return resolve_run(run, must_exist=False) if run else None


def _cf_nn(video) -> str:
    m = re.search(r"(\d{1,3})", str(video or ""))
    return m.group(1).zfill(2) if m else str(video or "")


CF_REQUEST_ATTEMPT_LAST = re.compile(r"^(?P<head>video-.+?)-request-(?P<att>a\d+)\.json$", re.I)


def _cf_req_canon(name) -> str:
    """A request file's name in the usual form: video-06-request-a2.json (the attempt last, as some runs wrote it) is read as
    video-06-a2-request.json; the file keeps its own name. Loupe reads names the same way (runs.request_canon)."""
    m = CF_REQUEST_ATTEMPT_LAST.match(str(name))
    return f"{m.group('head')}-{m.group('att')}-request.json" if m else str(name)


def _cf_requests_named(d, prefix: str) -> list:
    """The request files of a folder whose name starts with `prefix`, in both forms (…-request.json and …-request-aN.json); a kept copy or a
    draft is not one."""
    d = Path(d)
    if not d.is_dir():
        return []
    files = list(d.glob(f"{prefix}*request.json")) + [f for f in d.glob(f"{prefix}*request-a*.json") if CF_REQUEST_ATTEMPT_LAST.match(f.name)]
    return sorted(set(files), key=lambda f: _cf_req_canon(f.name))


def _cf_req_tag(name, nn) -> str:
    """The generation a request file is for, from its name, as Loupe reads it (runs._request_tag): video-03-c1-a2-request.json is c1-a2, and a name
    with no attempt is the first (video-03-request.json is a1, video-03-c1-request.json c1-a1); a name with the attempt last reads the same."""
    name = _cf_req_canon(name)
    t = name[len(f"video-{nn}"):] if name.startswith(f"video-{nn}") else name
    t = (t[:-len("request.json")] if t.endswith("request.json") else t).strip("-")
    return t if re.search(r"(?:^|-)a\d+", t) else (t + "-a1" if t else "a1")


def _cf_request_file(rd, video, attempt):
    """The request json of this video and attempt (the newest one when the attempt is not given or not found)."""
    d = rd / "50-requests" if rd else None
    if not d or not d.is_dir() or not video:
        return None
    nn = _cf_nn(video)
    reqs = sorted((p for p in _cf_requests_named(d, f"video-{nn}") if _cf_req_canon(p.name).endswith("-request.json")
                   and _cf_req_canon(p.name) != f"video-{nn}request.json"), key=lambda p: p.stat().st_mtime)
    if not reqs:
        return None
    tok = re.sub(r"[^a-z0-9]+", "-", str(attempt or "").lower()).strip("-")
    tok = "a" + tok if tok.isdigit() else tok
    if tok:
        # the attempt's own request by its tag (a clip's first take, c2-a1, is video-NN-c2-request.json, as Loupe reads it), else a name holding it
        exact = [p for p in reqs if _cf_req_tag(p.name.lower(), nn) == tok or f"-{tok}-" in _cf_req_canon(p.name).lower()]
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
            mid, typ = (v.get("media_id"), v.get("content_type") or v.get("type") or "") if isinstance(v, dict) else (v, "")
            if mid and mid not in res:
                res[mid] = {"name": name, "type": typ, "file": (v.get("file") if isinstance(v, dict) else "") or ""}
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
        _uf = ups.get(mid, {}).get("file")
        if not path and _uf and Path(_uf).is_file():
            path = Path(_uf)             # the file the uploads map recorded for this media id
        item["file"] = ups.get(mid, {}).get("name", "")
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
    """An entry without thumbnails for the terminal; its prompts (the flagged request's and the cleared one's) and the diff stay whole, never cut
    (the user, 2026-10-29: a video generation prompt is never trimmed)."""
    c = json.loads(json.dumps(e, ensure_ascii=False))
    for i in c.get("inputs", []):
        i.pop("thumb", None)
    (c.get("trigger", {}).get("part") or {}).pop("frame", None)
    return c


def cmd_caught_flag(a):
    """The flag record, kept in Loupe (the web app: search, filters, grouping, evidence)
    of every prompt and video that made Higgsfield flag, refuse, withhold or reroute something during a run (a
    moderation block, a job that failed within seconds with no reason, an upload or element marked nsfw / ip_checking
    / failed, an output withheld, a preset notice instead of a job). Written only through this command; no step of a
    run and no agent reads it (command item 23). The script gathers what the run knows (the video, the request, every
    input with its file, thumbnail and file facts, the reference, the source segment, the ledger row, the hook's raw capture); the
    agent writes the judgement (the reply, the suspected trigger, --asset, --prompt-span, --part-*, --tags). Loupe adds the history
    evidence.
      add        write a CF-nnn entry (--run and --video attach the request, inputs, plan, ledger row by themselves)
      set        update an entry: status (cleared needs the accepted request or job), notes, tags, assets, outcome
      list       entries as JSON for the terminal (filters; --full keeps the long texts)
      reconcile  the run's ledger (state.json) against the page: rows marked --flagged with no entry, and failed
                 rows with no job id or a flag-like note, for the agent to judge
      open       open Loupe's flag page in the default browser (sign in there)"""
    if a.action == "open":
        lc = _lc()
        if not lc.ensure():
            fail("Loupe is not running and could not be started (python ~/.claude/loupe/loupe.py serve)", 1)
        url = lc.base_url() + "/#/flags" + (f"/{a.id}" if a.id else "")
        webbrowser.open(url)
        out({"ok": True, "url": url, "opened": True})
    _ld = Path(os.environ.get("LOUPE_DATA") or (LOUPE_HOME / "data"))
    _ld.mkdir(parents=True, exist_ok=True)
    lock = FileLock(_ld / "flags-client.lock")
    if a.action == "reconcile":
        if not a.run:
            fail("reconcile needs --run", 2)
        rd = _cf_run_dir(a.run)
        if not rd or not (rd / "state.json").exists():
            fail(f"state.json not found for run {a.run}", 2)
        led = json.loads((rd / "state.json").read_text(encoding="utf-8")).get("submissions", [])
        ents = [e for e in _cf_load(q=f"run:{rd.name}") if rd.name in str(e.get("where", {}).get("run", "")) or str(a.run) in str(e.get("where", {}).get("run", ""))]
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
        _s, _cd = _cf_api("GET", "/api/captures?unclaimed=1&limit=1000000")
        _rows = _cd.get("captures", []) if _s == 200 else []
        _uploads = [c for c in _rows if UPLOAD_ONLY_CAPTURE.match(str(c.get("summary") or ""))]
        caps = [{"id": c["id"], "at": c["ts"], "tool": str(c.get("tool") or "").replace("mcp__higgsfield__", ""), "job": c.get("job"),
                 "summary": str(c.get("summary") or "")[:200]} for c in _rows if c not in _uploads][:50]
        out({"ok": True, "run": rd.name, "entries_for_run": [c["id"] for c in ents],
             "unclaimed_captures": caps, "unclaimed_upload_answers": len(_uploads),
             "flagged_unrecorded": [r for r in marked if not r["entry"]],
             "flagged_recorded": [r for r in marked if r["entry"]],
             "failed_to_judge": [r for r in check if not r["entry"]],
             "note": "flagged_unrecorded must each get `caught-flag add`; failed_to_judge rows are the agent's call "
                     "(a flag or a validation/credit error); mark a row's ledger entry with `ledger set --flagged`. "
                     "unclaimed_captures are raw Higgsfield responses the hook saved that no flag claimed yet: one that is a flag of this run gets "
                     "`caught-flag add ... --capture <id>`; the others are for the admin to dismiss in Loupe. The media_upload answers the hook keeps for "
                     "`hf-put --capture` are only counted (unclaimed_upload_answers): they are never a flag."})
    if a.action == "list":
        qs = " ".join(x for x in ((f"status:{a.status}" if a.status else ""), (f"run:{a.run}" if a.run else ""), (f"video:{a.video}" if a.video else ""),
                                  (f"model:{a.model}" if a.model else ""), (f"kind:{a.kind}" if a.kind else "")) if x)
        entries = _cf_load(q=qs)
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
        out({"ok": True, "url": _lc().base_url() + "/#/flags", "total": len(entries), "count": len(sel), "entries": sel})
    if a.action == "set":
        if not a.id:
            fail("--id CF-nnn is required", 2)
        with lock:
            entries = _cf_load(a.id)
            e = next((x for x in entries if x.get("id") == a.id), None)
            if e is None and str(a.id).startswith("CF-Q") and len(entries) == 1:
                e = entries[0]                     # a queued flag Loupe has since recorded under its own number (its log names the CF-Q id)
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
                _crq = _cf_request_json(a.cleared_prompt)
                if _crq:
                    _crd = _cf_run_dir(e.get("where", {}).get("run"))
                    cl["inputs"] = [{"label": i["label"], "role": i["role"], "name": i.get("name", ""),
                                     "sha1": (_cf_facts(i["path"], ocr=False).get("sha1", "") if i.get("path") else "")}
                                    for i in _cf_inputs(_crq, _crd, False)]
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
        out({"ok": True, "id": e.get("id") or a.id, **({"queued_as": a.id} if e.get("id") and e.get("id") != a.id else {}), "status": e.get("status"),
             "url": _lc().base_url() + f"/#/flags/{e.get('id') or a.id}"})
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
        entries = []
        cid = ""            # Loupe assigns the CF-nnn id
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
        for _it in inputs:      # file facts: sha1, size, dimensions, duration, text seen on screen (OCR)
            if _it.get("path"):
                _f = _cf_facts(_it["path"], ocr=not a.no_facts)
                if _f:
                    _it["facts"] = _f
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
        # the raw response a hook captured the moment it came back (by job id, or the one named with --capture)
        _cap = None
        _jobs = [j for j in re.split(r"[,\s]+", str(entry.get("job") or "")) if j]
        if a.capture:
            _s, _d, _cap = _capture_full(a.capture)
            if not _cap:
                print(f"WARNING: capture {a.capture} is not in Loupe ({(_d or {}).get('error') or 'no such id'}); the flag is recorded without it.", file=sys.stderr)
        elif _jobs:
            _s, _d = _cf_api("GET", "/api/captures?full=1&limit=10&job=" + _jobs[0])
            _cap = next(iter(_d.get("captures", []) if _s == 200 else []), None)
        if _cap:
            _pl = _cap.get("payload") or {}
            entry["captured"] = {"id": _cap["id"], "at": _cap["ts"], "tool": _cap["tool"], "response": str(_pl.get("response", ""))[:12000],
                                 "agent": _cap.get("agent", "")}
        entries.append(entry)
        _cf_save(entries)
        cid = entry["id"]
        if _cap and not str(cid).startswith("CF-Q"):
            _cf_api("POST", f"/api/captures/{_cap['id']}/claim", {"flag": cid})
    gaps = []
    if not (trig.get("assets") or trig.get("assets_unmatched")):
        gaps.append("asset: say which input you suspect with --asset (an 'Image 2' label, a media id, a file name or an A/V id)")
    if not trig.get("prompt_span"):
        gaps.append("prompt words: --prompt-span \"<the exact words>\" when a wording is suspected")
    if not trig.get("part"):
        gaps.append("video part: --part-of / --part-from / --part-to when a part of a video is suspected")
    out({"ok": True, "id": cid, "title": entry["title"], "url": _lc().base_url() + f"/#/flags/{cid}", "capture": (entry.get("captured") or {}).get("id"),
         "attached": [k for k, v in (("request", rq), ("prompt", prompt), ("params", params), ("inputs", inputs), ("plan", plan),
                                     ("ledger row", sub), ("thumbnails", any(i.get("thumb") for i in inputs)),
                                     ("file facts", any(i.get("facts") for i in inputs)), ("raw response", entry.get("captured"))) if v],
         "inputs": [{"label": i["label"], "name": i.get("name"), "suspect": bool(i.get("suspect"))} for i in inputs],
         "unmatched_assets": trig.get("assets_unmatched", []), "not_given": gaps,
         "note": "after the changed request is accepted: `caught-flag set --id %s --status cleared --cleared-prompt <request.json>`; "
                 "if the flag stays, `--status persistent`; `caught-flag open --id %s` shows it in Loupe" % (cid, cid)})


def cmd_loupe(a):
    """The Loupe web app: ensure (start it if needed) | status | open."""
    lc = _lc()
    if a.action == "ensure":
        ok = lc.ensure()
        size = None
        if ok:
            try:
                st, d = lc.call("GET", "/api/qc/samples?limit=1", key_name="qc", timeout=10)
                size = d.get("library_size") if st == 200 and isinstance(d, dict) else None
            except Exception:  # noqa: BLE001
                size = None
        keeper = None
        if ok and size:                      # the keeper boots, or re-reads the library, now: the first consult then finds it current
            try:
                st, d = lc.call("POST", "/api/qc/keeper/sync", {}, key_name="qc", timeout=KEEPER_SYNC_WAIT)
                if st == 200 and isinstance(d, dict):
                    keeper = d
                    if d.get("reading_started"):
                        u_ = d.get("understanding") or {}
                        keeper["reading_note"] = (f"{len(u_.get('missing') or []) + len(u_.get('stale') or [])} new or changed sample(s) are being read from their pictures "
                                                  "in the background; Loupe tells the keeper when they are done (until then it judges them from the admin's words)")
                elif st == 0 and "timed out" in str((d or {}).get("error", "")).lower():
                    # Loupe goes on booting or re-feeding the keeper after this call gave up: the sync holds the keeper lock until it is
                    # done and a consult waits on that same lock, so the first qc-consult or plan-hints still meets a current keeper
                    keeper = {"state": "syncing", "waited_s": KEEPER_SYNC_WAIT,
                              "note": "the keeper is being booted or brought up to date inside Loupe; the first consult waits for it"}
                else:
                    keeper = {"state": "failed", "error": str(d)[:200]}
            except Exception as e:  # noqa: BLE001
                keeper = {"state": "failed", "error": str(e)[:200]}
        out({"ok": ok, "url": lc.base_url(), "library_size": size, "keeper": keeper,
             "note": "" if ok else "Loupe could not be started: python ~/.claude/loupe/loupe.py serve"}, 0 if ok else 1)
    if a.action == "status":
        h = lc.health()
        out({"ok": bool(h), "url": lc.base_url(), "running": bool(h), **(h or {})})
    if a.action == "open":
        if not lc.ensure():
            fail("Loupe could not be started", 1)
        webbrowser.open(lc.base_url() + (a.path or "/"))
        out({"ok": True, "url": lc.base_url() + (a.path or "/")})


def _qc_ctx(a) -> dict:
    ctx = {"run": a.run or "", "video": a.video or "", "model": a.model or "", "mode": a.mode or "", "product": a.product or "",
           "product_details": (getattr(a, "product_details", "") or "")[:600], "note": (getattr(a, "note", "") or "")[:600],
           "kinds": [k.strip() for k in (a.kinds or "").split(",") if k.strip()]}
    rd = _cf_run_dir(a.run) if a.run else None
    if rd:
        mode_, model_ = _cf_state_info(rd)
        ctx["run"] = rd.name
        ctx["mode"] = ctx["mode"] or mode_
        ctx["model"] = ctx["model"] or model_
    return ctx


def _qc_sample_files(res, rd, video, name="qc-consult.json"):
    """Where the answer is kept for the video's record (the agent reads it from the JSON line, the file is the audit): a consult as
    qc-consult.json, a brief as qc-brief.json, so a brief never stands in for the video's consult."""
    try:
        if rd and video:
            d = rd / "60-outputs" / f"video-{_cf_nn(video)}"
            d.mkdir(parents=True, exist_ok=True)
            (d / name).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
            return str(d / name)
    except OSError:
        pass
    return ""


def cmd_qc_consult(a):
    """QC phase only. qc-consult asks the QC keeper (a separate read-only Claude session that holds the sample library: the generation
    misses the admin marked, each as one image of the frames the admin chose, tagged WRONG, RIGHT or EXAMPLE with their times and sources); qc-brief returns the
    matching samples with no model call. Both print the samples' image paths: view them, then compare the marked region with the same
    place in the video under QC. Loupe unreachable: the answer says so and the QC goes on without samples."""
    ctx = _qc_ctx(a)
    ctx["q"] = a.question or ""
    sent = {}
    if a.cmd == "qc-consult":
        if not a.question:
            fail("qc-consult needs --question (the errors you caught in the video under QC: what, where, at which beat; or none caught)", 2)
        ev, sent = _qc_evidence(a, ctx)
        s, d = _cf_api("POST", "/api/qc/consult", {**ctx, **ev, "question": a.question, "checkpoints": a.checkpoint or []}, key="qc", timeout=CONSULT_TIMEOUT)
    else:
        s, d = _cf_api("POST", "/api/qc/brief", ctx, key="qc", timeout=60)
    if s != 200:
        out({"ok": True, "mode": "unavailable", "samples": [], "note": "no QC samples for this check: " + str((d or {}).get("error"))})
    if a.cmd == "qc-consult":
        d["evidence_sent"] = sent
        if d.get("cause") or d.get("template_fix"):
            d["judge_rule"] = ("cause (which part of the prompt or of the judge's template let the error happen) and template_fix (that part rewritten) are the "
                               "judge's: write both into the verdict and result.json judge, for the user's review at the end")
    rd = _cf_run_dir(a.run) if a.run else None
    d["saved"] = _qc_sample_files(d, rd, a.video, "qc-consult.json" if a.cmd == "qc-consult" else "qc-brief.json")
    items = d.get("relevant") or d.get("samples") or []
    if a.cmd == "qc-brief" and any(x.get("prompts") for x in items if isinstance(x, dict)):
        d["prompts_rule"] = (LOUPE_PROMPTS_WORDS + " (prompt_note: the admin's one line on what made the difference). This is Loupe's brief, with no "
                             "model call: no keeper read or judged these prompts and none is written for you; `T sample-prompts --id S.. --run RUN` "
                             "writes a sample's whole record, its prompts included, when your phase reads one.")
    elif any(x.get("prompts") for x in items if isinstance(x, dict)):
        d["prompts_files"] = _prompts_files(items, rd)
        who = (("the keeper read whole, before it answered, the prompts of the samples in prompts_judged"
                + (" and not those in prompts_unread (it reads the prompts of at most ten cited samples per answer): weigh those as unjudged"
                   if d.get("prompts_unread") else ""))
               if d.get("mode") == "keeper" else f"no keeper read or judged them (mode {d.get('mode')}: Loupe's brief answered)")
        d["prompts_rule"] = (LOUPE_PROMPTS_WORDS + " (prompt_note: the admin's one line on what made the difference); " + who + "; "
                             "they are written whole for you at prompts_files[<id>], from Loupe's record, compared or judged by no one. For a "
                             "sample you judged relevant to THIS video, read that file and judge yourself what the correct version's prompt did differently from the flawed "
                             "version's at the frames each made (a sample with one box: what that prompt secured, or let happen, at the frames it made; an "
                             "example prompt: what it suggests, never a flawed or a correct prompt). It is a lead for the diagnosed cause and the corrected "
                             "request, written in the model's own "
                             "structure and your words, never a sentence to paste, never a verdict on the video, and not read for a sample you did not judge relevant.")
    if a.cmd == "qc-consult" and d.get("product_images"):
        d["product_images_rule"] = ("product_images is the judge's choice of the product images the regeneration carries, which and how many (the character, "
                                    "the original reference and every other input stay): write the regeneration's request as awl-write-request says "
                                    "(template_fix in place of the part it names), then `T product-images --run RUN --video NN --request <that request> "
                                    "--apply` puts them in it (only after the last image or by leaving out the last ones, never both: the images the prompt names keep "
                                    "their numbers); prepare and upload an image it adds (awl-inputs) before X5; record them in result.json judge")
    if d.get("needs_unmet"):
        d["unmet_rule"] = ("the keeper asked for something Loupe cannot fetch (a question only you can answer by looking at your own video, or a file that does not "
                           "exist): answer it from the video in words and ask again ONCE with --note '<what you saw>'; if it still has needs_unmet, go on without it "
                           "and write in the verdict what was not answered")
    if any(x.get("reading_path") for x in items if isinstance(x, dict)):
        d["reading_rule"] = ("a relevant sample's reading (marked, right_version) and reading_path are what a data collector saw in its picture, collected once by a session "
                             "that opened it and gave no verdict: view the picture itself first; Read the whole collection only when the picture leaves the marked place "
                             "unclear; the judgement (what went wrong, what to check) is the keeper's and yours, never the collector's")
    if (d.get("library_read") or {}).get("not_read"):
        d["not_read_rule"] = ("the samples in library_read.not_read have no reading of their picture yet (new or changed): the keeper judged them from the admin's words "
                              "alone, so view the picture of any of them it named before you rely on it")
    if d.get("flags"):
        d["flags_rule"] = ("flags are what the judge found missing, contradictory or ambiguous in the records of the samples it used (id, what, effect): weigh "
                           "its answer by them, never settle one by guessing, and write each into result.json keeper_gaps, one line ('flag S12: <what>'), for "
                           "the admin at the wrap-up")
    if d.get("not_covered") or d.get("needs_unmet"):
        d["gaps_rule"] = ("write what the library does not cover (not_covered) and any need still unmet after your --note into result.json keeper_gaps, one line each: "
                          "the main session reports them in the wrap-up so the admin can add a sample in Loupe")
    out(d)


def cmd_plan_hints(a):
    """First request of a video only (X2). Asks the keeper (the same separate read-only session that holds the sample library) which past
    misses could matter for the plan of a video that has not been generated. The answer is a few text-only hints, usually none: each has
    the plan situation that triggers it, what the right version shows, the writer's own tool to use at that beat, and when it does not apply.
    A hint is a risk to check the plan against, never prompt text. Keeper unavailable or library empty: no hints, and the request is written
    as always. Nothing here changes a request."""
    ctx = _qc_ctx(a)
    beats = (a.beats or "").strip()
    if not beats:
        fail("plan-hints needs --beats (one line per beat of the plan: what happens, the product's form and state, the camera)", 2)
    cut = len(beats) > 2000
    beats = beats[:2000]
    s, d = _cf_api("POST", "/api/qc/consult", {**ctx, "purpose": "plan", "question": beats}, key="qc", timeout=CONSULT_TIMEOUT)
    if s != 200:
        out({"ok": True, "mode": "unavailable", "hints": [], "note": "no sample hints: " + str((d or {}).get("error"))})
    rd = _cf_run_dir(a.run) if a.run else None
    res = {"ok": True, "mode": d.get("mode"), "hints": d.get("hints", []), "held_back": d.get("held_back", 0), "held_back_why": d.get("held_back_why", []),
           "none_reason": d.get("none_reason", ""), "beats_cut": cut}
    for k in ("needs_asked", "needs_unmet", "prompts_judged", "prompts_unread", "library_read", "keeper_error", "keeper_restarted", "flags"):
        if d.get(k):
            res[k] = d[k]
    if res.get("flags"):
        res["flags_rule"] = ("flags are what the judge found missing, contradictory or ambiguous in the records of the samples it used (id, what, effect): weigh "
                             "its hints by them, never settle one by guessing, and write each as a keeper gap in the 'Sample hints' block ('flag S12: <what>')")
    if d.get("needs_unmet"):
        res["unmet_rule"] = ("the keeper asked for something Loupe cannot fetch (a question only you can answer from your plan, or a file that does not exist): answer it "
                             "from the plan in words and ask again ONCE with --note '<your answer>' (the same --beats); if it still has needs_unmet, go on without it and "
                             "write it as a keeper gap in the 'Sample hints' block")
    if any(h.get("reading_path") for h in res["hints"] if isinstance(h, dict)):
        res["reading_rule"] = ("a hint's reading_path is what a data collector saw in its sample's picture (what each frame shows, what the marks point at, the product "
                               "and scene; no verdict): Read it only when you cannot tell from the hint whether its trigger matches a beat of your plan; it is "
                               "evidence, never prompt text")
    if res["hints"]:
        res["rules"] = ("Hints are risks to check the plan against, never prompt text: do not copy their words, do not name the wrong behaviour in the "
                        "prompt, add no negative list. Apply one only to the beat its trigger matches and only if its caveat does not exclude it, by the "
                        "smallest change inside the existing prompting stack, written positively as its right_outcome. At most two per video. "
                        "Record each (applied to which beat, or why not) under 'Sample hints' in the brief.")
        if any(h.get("prompts") for h in res["hints"] if isinstance(h, dict)):
            res["prompts_files"] = _prompts_files(res["hints"], rd)
            res["prompts_rule"] = ("a hint marked prompts rests on a sample whose prompts the admin kept: " + LOUPE_PROMPTS_WORDS + " (and prompt_note, the admin's one "
                                   "line on what made the difference); the keeper read them whole before hinting (prompts_judged), "
                                   "and they are written whole for you at prompts_files[<id>], from Loupe's record, compared or judged by no one. When you apply that hint, read "
                                   "that file, judge yourself what the correct version's prompt did differently from the flawed version's (a sample with one box: "
                                   "what that prompt secured, or let happen, at the frames it made; an example prompt: what it suggests, never a flawed or a correct "
                                   "prompt) and whether that is the mechanism of the matching beat, and apply the mechanism at "
                                   "that beat in the locked model's own structure and your own words. Never a sentence of any of those prompts in the request, never the wrong behaviour "
                                   "named, never the correct version's prompt as a rule for another video; a hint you do not apply is not read.")
    try:
        if rd and a.video:
            f = rd / "40-briefs" / f"video-{_cf_nn(a.video)}-hints.json"
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps({**res, "beats": beats}, ensure_ascii=False, indent=1), encoding="utf-8")
            res["saved"] = str(f)
    except OSError:
        pass
    out(res)


VIDEO_MODEL_KEYS = ("name", "provider", "guide", "operations", "edit_kind", "duration_s", "text_rendering", "best_for", "avoid_for")


def _video_model_info(model: str) -> dict:
    """The generation video model as the judge needs it: its id and its entry of models/index.json (name, provider, guide, operations, limits)."""
    if not model:
        return {}
    try:
        e = json.loads((AWL_HOME / "models" / "index.json").read_text(encoding="utf-8"))["models"].get(model) or {}
    except (OSError, ValueError, KeyError):
        e = {}
    return {"id": model, **{k: e[k] for k in VIDEO_MODEL_KEYS if e.get(k) not in (None, "", [])}}


def _video_request_prompt(rd, video, attempt, model) -> tuple[str, str, dict]:
    """The prompt the video under QC was generated from: the newest request of the video (of the attempt when given) made for the locked video model,
    else the newest one with a prompt that is no start frame, plate, guide or marker. (prompt, file name, its model and parameters), or ("", "", {})."""
    d = rd / "50-requests" if rd else None
    if not d or not d.is_dir() or not video:
        return "", "", {}
    nn = _cf_nn(video)
    reqs = sorted((p for p in _cf_requests_named(d, f"video-{nn}") if _cf_req_canon(p.name) != f"video-{nn}request.json"),
                  key=lambda p: p.stat().st_mtime, reverse=True)
    tok = re.sub(r"[^a-z0-9]+", "-", str(attempt or "").lower()).strip("-")
    if tok:
        tok = "a" + tok if tok.isdigit() else tok
        reqs = [p for p in reqs if _cf_req_tag(p.name.lower(), nn) == tok or f"-{tok}-" in _cf_req_canon(p.name).lower()
                or (tok == "a1" and p.name.lower() == f"video-{nn}-request.json")] or reqs
    found = []
    for p in reqs:
        j = _cf_request_json(p)
        prm = j.get("params") if isinstance(j.get("params"), dict) else j
        pr = str((prm or {}).get("prompt") or "").strip()
        if pr:
            found.append((p, str((prm or {}).get("model") or ""), pr, _cf_params_dict(j)))
    for p, m, pr, prm in found:
        if model and m == model:
            return pr, p.name, prm
    for p, m, pr, prm in found:
        if not re.search(r"frame|plate|guide|marker|-g\d", p.name.lower()):
            return pr, p.name, prm
    return "", "", {}


def _same_prompt(template: str, prompt: str) -> bool:
    """Whether a prompt is the judge's template word for word, its [SLOT: ...] markers filled and nothing added before, between or after."""
    tn, pn = _norm_ws(template), _norm_ws(prompt)
    if not tn or not pn:
        return False
    parts = [x.strip() for x in re.split(r"\[SLOT:[^\]]*\]", tn)]
    if len(parts) == 1:
        return tn == pn
    if not (pn.startswith(parts[0]) and pn.endswith(parts[-1])):
        return False
    pos = 0
    for part in parts:
        if part:
            k = pn.find(part, pos)
            if k < 0:
                return False
            pos = k + len(part)
    return True


def _qc_evidence(a, ctx) -> tuple[dict, dict]:
    """What the judge needs to judge an error accurately (the user, 2026-10-28), read from the run's own files: the prompt the video under QC was
    generated from with that request's video model and parameters, its inputs (each with the client's original it was made from) and product images,
    the model's entry of the index, the template the judge gave at X2 and the agent's brief then. ({fields sent}, {where each came from})."""
    rd = _cf_run_dir(a.run) if a.run else None
    ev, sent = {}, {}
    if not (rd and a.video):
        vm = _video_model_info(ctx.get("model"))
        if vm:
            ev["video_model"], sent["video_model"] = vm, vm["id"]
        return ev, sent
    pr, name, prm = _video_request_prompt(rd, a.video, getattr(a, "attempt", None), ctx.get("model"))
    if pr:
        ev["request_prompt"], sent["request_prompt"] = pr, name
    if prm:
        ev["request_params"], sent["request_params"] = prm, name
    jq = _cf_request_json(rd / "50-requests" / name) if name else {}
    itext = _pi_inputs_text(jq, rd) if jq else ""
    if itext:          # which inputs the video was given, each with the client's original it was made from, and its product images (the admin, 2026-10-30)
        ptext = _pi_product_text(jq, rd)
        ev["request_inputs"], sent["request_inputs"] = itext + (f"\n{ptext}" if ptext else ""), name
    vm = _video_model_info(prm.get("model") or ctx.get("model"))
    if vm:
        ev["video_model"], sent["video_model"] = vm, vm["id"]
    nn = _cf_nn(a.video)
    tjs = [p for p in [rd / "40-briefs" / f"video-{nn}-template.json"] + sorted((rd / "40-briefs").glob(f"video-{nn}-c*-template.json")) if p.is_file()]
    got = {"template": [], "brief": []}
    for tj in tjs:
        try:
            t = json.loads(tj.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for k in got:
            if isinstance(t, dict) and str(t.get(k) or "").strip():
                got[k].append((tj.name, str(t[k])))
    for k, items in got.items():
        if items:
            text = "\n\n".join((f"{name.replace('-template.json', '')}:\n" if len(items) > 1 else "") + v for name, v in items)
            if k == "template" and len(items) == 1 and _same_prompt(text, ev.get("request_prompt", "")):
                text = "(the same as the prompt this video was generated from" + (", its slots filled)" if "[SLOT:" in text else ", word for word)")
            ev[k], sent[k] = text, ", ".join(name for name, _v in items)
    return ev, sent


PROMPT_LIMIT = 5000         # the service refuses a prompt over 5000 characters before any job exists (the agent contract)


def _tpl_files(rd, video, clip="") -> dict:
    """The files of one video's (or clip's) judge's prompt, by name."""
    tag = f"video-{_cf_nn(video)}" + (f"-{str(clip).strip().lower()}" if clip else "")
    b, r = rd / "40-briefs", rd / "50-requests"
    return {"json": b / f"{tag}-template.json", "md": b / f"{tag}-template.md", "judgement": b / f"{tag}-judgement.md",
            "brief": b / f"{tag}-judge-brief.md", "musts": b / f"{tag}-musts.md",
            "request": r / f"{tag}-request.json", "draft": r / f"{tag}-request.draft.json"}


def _musts_of(path) -> list[str]:
    """The lines a prompt must carry word for word: one per line of the file (a list marker is dropped, a heading line is left out)."""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    out_ = []
    for ln in text.splitlines():
        t = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s+", "", ln).strip()
        if t and not t.startswith("#"):
            out_.append(t)
    return out_


def _norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip()


# ------------------------------------------------------------------ product images (the admin, 2026-10-30)
# "the judge should be able to tell and decide to how many asset sample references should be used in the generation based on what it thinks the best use
# is ... (i am talking only for the product ...)", and the names "as they were in their original files ... just the exact file/image name".  Every input
# of a request records the client's original it was made from: params.medias[].source {original, asset_id, prepared, kind} (X2 writes it).  The product
# images ride last among the image inputs, so the judge can choose which and how many without renumbering any other input.  An input's source is read as
# Loupe reads it (runs._source_of): the source record, else a 'build' note ("from <file> (A82): <how it was prepared>"), else the one asset id or the one
# original file name what the request says of the input names; never guessed.
PI_BUILD_NOTE = re.compile(r"^\s*(byte copy of|from)\s+(.+?\.(?:png|jpe?g|webp|bmp|tiff?|gif|mp4|mov|m4v|webm|mkv))\s*(?:\((A\d{1,4})\))?\s*(?:\(([^)]*)\))?\s*:?\s*(.*)$",
                           re.I | re.S)
PI_A_ID = re.compile(r"\bA\d{2,4}\b")
PI_MEDIA_FILE = re.compile(r"\.(?:png|jpe?g|webp|bmp|tiff?|gif|mp4|mov|m4v|webm|mkv)$", re.I)      # a value that names a file
PI_IMAGE_REF = re.compile(r"(@?)\bImage( ?)(\d+)\b")
PI_ROLE = {"image_references": "Image", "video_references": "Video", "audio_references": "Audio"}
PI_PRODUCT_NAME = re.compile(r"(?:^|[\s=/\\_:-])product(?:[\s._:/\\\d-]|$)", re.I)      # 'image2-product-EF6-PM-front-padded.png': the pipeline names a product view so (also product/..., key:product, product2...; Loupe's runs.PRODUCT_FILE is the same pattern)


PI_FINGERPRINTS: dict = {}


def _pi_fingerprint(path) -> str:
    """A short fingerprint of a file's content, the first 8 hex digits of its SHA-1, so one photo is known as one file in every run whatever asset id a
    run gave it (the admin, 2026-11-03: one run's A274 IMG_6917.jpg was another run's A273); '' when the file cannot be read. Loupe computes it the
    same way (runs.file_fingerprint) and names each sample's images with it."""
    if not path:
        return ""
    p = Path(str(path))
    try:
        stt = p.stat()
        if not p.is_file():
            return ""
    except (OSError, ValueError):
        return ""
    key = (os.path.normcase(str(p)), stt.st_size, stt.st_mtime_ns)
    if key not in PI_FINGERPRINTS:
        try:
            PI_FINGERPRINTS[key] = hashlib.sha1(p.read_bytes()).hexdigest()[:8]
        except OSError:
            return ""
    return PI_FINGERPRINTS[key]


def _pi_fp_tag(path) -> str:
    """' #3f9a1c2b' after a file's name, or '' when the file cannot be read."""
    mk = _pi_fingerprint(path)
    return f" #{mk}" if mk else ""


def _pi_by_fingerprint(inv: dict, mk: str, fname: str = ""):
    """The inventory item whose file has the fingerprint mk (of two copies, the one of that file name, else the first), or None."""
    hits = [it for it in inv.values() if it.get("path") and _pi_fingerprint(it["path"]) == mk]
    return next((h for h in hits if fname and Path(str(h["path"]).replace("\\", "/")).name.lower() == fname.lower()), hits[0] if hits else None)


def _pi_inventory(rd) -> tuple[dict, dict]:
    """The run's asset inventory by asset id, and by lower-cased file name (a name two items share names neither)."""
    try:
        j = json.loads((Path(rd) / "30-assets" / "project" / "asset-inventory.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        j = {}
    items = [it for it in (j.get("items") or [] if isinstance(j, dict) else []) if isinstance(it, dict) and it.get("id")]
    names: dict = {}
    for it in items:
        n = Path(str(it.get("path") or it.get("rel") or "").replace("\\", "/")).name.lower()
        if n:
            names.setdefault(n, []).append(it)
    return {str(it["id"]): it for it in items}, {n: v[0] for n, v in names.items() if len(v) == 1}


def _pi_registry_rows(rd) -> list[tuple[str, str, list]]:
    """The product rows of the run's asset registry (30-assets/registry.md, in either form runs write: a table row whose id starts with P-, or whose
    type cell says product): (id, the row's text, its asset ids).  Loupe reads them the same way (runs._registry_product_rows)."""
    try:
        text = (Path(rd) / "30-assets" / "registry.md").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    rows = []
    for ln in text.splitlines():
        cells = [c.strip().strip("`").strip() for c in ln.strip().strip("|").split("|")] if ln.lstrip().startswith("|") else []
        if not cells or not re.fullmatch(r"[A-Za-z][\w-]*", cells[0]) or cells[0].lower() == "id":
            continue
        if cells[0].startswith("P-") or any(c.lower() == "product" for c in cells[1:3]):
            rows.append((cells[0], ln.strip(), list(dict.fromkeys(PI_A_ID.findall(ln)))))
    return rows


def _pi_names_product(m: dict, codes) -> bool:
    """Whether an input's own file name or label names it a product view: the pipeline's 'imageN-product-...' names, or a product row's id of the
    run's registry in it ('NG-EF6-SPE-angled')."""
    own = _pi_media_names(m) | {str(m.get("label") or "").lower()}
    return any(PI_PRODUCT_NAME.search(x) for x in own) or any(re.search(r"(?<![a-z0-9])" + re.escape(str(c).lower()) + r"(?![a-z0-9])", x)
                                                              for c in codes for x in own)


def _pi_source(m: dict, said: str, inv: dict, names: dict, prod_ids: set) -> dict:
    """What a request's records say one input was made from: {original, name, asset_id, prepared, kind, recorded}; {} when no record names it."""
    s = m.get("source") if isinstance(m.get("source"), dict) else None
    orig = aid = prep = kind = how = ""
    said_path = next((str(m[k]).strip() for k in ("source", "source_file", "from") if isinstance(m.get(k), str) and PI_MEDIA_FILE.search(str(m[k]).strip())), "")
    if s and str(s.get("original") or "").strip():
        orig, aid, how = str(s["original"]).strip(), str(s.get("asset_id") or "").strip(), "source"
        prep, kind = str(s.get("prepared") or "").strip(), str(s.get("kind") or "").strip()
    elif said_path:          # the forms runs wrote before the source record: the client's file in source, source_file or from, its prepare words
        orig, how, prep = said_path, "source", str(m.get("prepare") or "").strip()
    else:
        b = PI_BUILD_NOTE.match(str(m.get("build") or ""))
        if b:
            orig, aid, how = b.group(2).strip(), b.group(3) or next(iter(PI_A_ID.findall(b.group(4) or "")), ""), "build"
            prep = ("a byte copy" + (f" ({b.group(4)})" if b.group(4) else "")) if b.group(1).lower().startswith("byte") else (b.group(5) or b.group(4) or "").strip()
        else:
            text = " ".join(str(x or "") for x in (m.get("meaning"), said, m.get("label"), m.get("source") if isinstance(m.get("source"), str) else "",
                                                   m.get("source_file"), m.get("from")))
            ids = list(dict.fromkeys(a for a in PI_A_ID.findall(text) if a in inv))
            hit = inv[ids[0]] if len(ids) == 1 else None
            if not ids:
                tl = text.lower()
                found = [n for n in names if n in tl]
                found = [n for n in found if not any(n != o and n in o for o in found)]
                hit = names[found[0]] if len(found) == 1 else None
            if hit:
                orig, aid, how = str(hit.get("path") or ""), str(hit.get("id") or ""), "named"
                prep = str(m.get("meaning") or said or "").strip()
    if not orig:
        return {}
    if not aid:
        key = os.path.normcase(os.path.normpath(orig))
        aid = next((k for k, it in inv.items() if it.get("path") and os.path.normcase(os.path.normpath(str(it["path"]))) == key), "")
    if not kind and aid and aid in prod_ids:
        kind = "product"
    return {"original": orig, "name": Path(orig.replace("\\", "/")).name, "asset_id": aid, "prepared": prep, "kind": kind, "recorded": how}


def _pi_media_names(m: dict) -> set:
    """The names a request gives one input's file: the file it names, its placeholder ('<X3: image2-product-...png>') and its label's name after '='."""
    out = set()
    for v in (m.get("file"), m.get("value")):
        v = str(v or "").strip().strip("<>")
        v = v.split(":", 1)[1].strip() if v.lower().startswith("x3:") else v
        if v:
            out.add(Path(v.replace("\\", "/")).name.lower())
    lab = str(m.get("label") or "")
    if "=" in lab:
        out.add(lab.split("=", 1)[1].strip().split(" (")[0].lower())
    return {x for x in out if x}


def _pi_images(j: dict, rd) -> list[dict]:
    """The image inputs of a request in order: [{label ('Image 2'), media, source, product, names}]; a product image is one its source calls a product,
    else one whose asset id sits in a product row of the run's registry, else one whose own file name or label names it so (the pipeline's
    'imageN-product-...' names, or a product row's id)."""
    prm = j.get("params") if isinstance(j.get("params"), dict) else j
    inv, names = _pi_inventory(rd) if rd else ({}, {})
    rows = _pi_registry_rows(rd) if rd else []
    prod_ids, codes = {a for _id, _row, ids in rows for a in ids}, [rid for rid, _row, _ids in rows]
    mm = j.get("medias_meaning") or j.get("media_meaning")
    meaning = dict(mm) if isinstance(mm, dict) else {}
    out, k = [], 0
    for m in (prm or {}).get("medias") or []:
        if isinstance(m, dict) and m.get("role") == "image_references":
            k += 1
            lab = f"Image {k}"
            src = _pi_source(m, str(meaning.get(lab) or ""), inv, names, prod_ids)
            own = _pi_media_names(m)
            kind = src.get("kind") or ("product" if _pi_names_product(m, codes) else "")
            out.append({"label": lab, "media": m, "source": src, "product": kind == "product", "names": own})
    return out


def _pi_inputs_text(j: dict, rd) -> str:
    """Every input of a request as the judge reads it: its label and role, what the request says of it, and where it came from."""
    prm = j.get("params") if isinstance(j.get("params"), dict) else j
    mm = j.get("medias_meaning") or j.get("media_meaning")
    meaning = dict(mm) if isinstance(mm, dict) else {}
    inv, names = _pi_inventory(rd) if rd else ({}, {})
    rows = _pi_registry_rows(rd) if rd else []
    prod_ids, codes = {a for _id, _row, ids in rows for a in ids}, [rid for rid, _row, _ids in rows]
    counts, lines = {}, []
    for m in (prm or {}).get("medias") or []:
        if not isinstance(m, dict):
            continue
        role = str(m.get("role") or "?")
        counts[role] = counts.get(role, 0) + 1
        lab = f"{PI_ROLE.get(role, role)} {counts[role]}"
        src = _pi_source(m, str(meaning.get(lab) or ""), inv, names, prod_ids)
        what = str(m.get("meaning") or meaning.get(lab) or "").strip()
        if role == "image_references" and not src.get("kind") and _pi_names_product(m, codes):
            src = {**src, "kind": "product"} if src else src
        made = (f"; {'a product image; ' if src.get('kind') == 'product' else (src['kind'] + '; ' if src.get('kind') else '')}made from "
                + " · ".join(x for x in (src.get("asset_id"), src.get("name")) if x) + _pi_fp_tag(src.get("original"))
                + (f", prepared: {src['prepared']}" if src.get("prepared") else "")) if src else "; its original is not recorded"
        lines.append(f"- {lab} ({role}{made})" + (f": {what}" if what else ""))
    return "\n".join(lines)


def _pi_product_text(j: dict, rd) -> str:
    """The product images of a request and the client's images of that product (its registry row and the inventory's file names), for the judge;
    each file's name is followed by the fingerprint of its content (#3f9a1c2b), the same for the same file in every run."""
    imgs = _pi_images(j, rd) if rd else []
    prod = [x for x in imgs if x["product"]]
    if not imgs:
        return ""
    if not prod:
        return ("Product images: no image input of this draft records that it is a product image, so the product images cannot be changed here: keep "
                "them as they are (product_images empty).")
    last = imgs.index(prod[0]) >= len(imgs) - len(prod) and all(x["product"] for x in imgs[imgs.index(prod[0]):])
    head = ("Product images (yours to decide, see PRODUCT IMAGES): "
            + ", ".join(f"{x['label']} ({x['source'].get('asset_id') or '?'} · {x['source'].get('name') or '?'}{_pi_fp_tag(x['source'].get('original'))})" for x in prod)
            + ("; they are the last image inputs, so the inputs before them keep their numbers." if last else
               "; they are NOT the last image inputs of this draft, so they cannot be changed here: keep them as they are (product_images empty)."))
    inv, _names = _pi_inventory(rd)
    used = {x["source"].get("asset_id") for x in prod if x["source"].get("asset_id")}
    rows = [(rid, ids) for rid, _row, ids in _pi_registry_rows(rd) if used & set(ids)]
    lines = [head]
    for rid, ids in rows:
        lines.append(f"The client's images of {rid} (the run's registry row and asset inventory): "
                     + ", ".join(f"{a} {Path(str(inv.get(a, {}).get('path') or inv.get(a, {}).get('rel') or '?').replace(chr(92), '/')).name}"
                                 f"{_pi_fp_tag(inv.get(a, {}).get('path'))}" for a in ids))
    return "\n".join(lines)


def _pi_renumber(text: str, mapping: dict) -> str:
    """A text with each 'Image N' (or '@ImageN') the mapping moves given its new number, all at once."""
    def f(mm):
        old = f"Image {mm.group(3)}"
        if old not in mapping:
            return mm.group(0)
        return f"{mm.group(1)}Image{mm.group(2)}{mapping[old].split()[-1]}"
    return PI_IMAGE_REF.sub(f, str(text or ""))


def _pi_named(text: str) -> set:
    """The image numbers a text names ('Image 2', '@Image3')."""
    return {int(g) for _a, _s, g in PI_IMAGE_REF.findall(str(text or ""))}


def _product_plan(rd, j: dict, judge: list, musts=None, fixed: bool = False) -> dict:
    """What the judge's product images do to a request, as facts, before anything is written: the image inputs now and after, the product images kept,
    added (with the source to prepare them from) and left out, the numbers that change, the must-carry lines that name a product image (renumbered, or no
    longer the request's), the medias to write; and the problems that stop it (then nothing is applied).  fixed (a regeneration): the images its prompt
    names keep their numbers, so only images after the last one may be added or the last ones left out.  An image the judge gives its fingerprint
    (the 8 characters after # in what it read) is the file with that content: an asset id is the run's own number, and one copied from a
    sample of another run can name another file here (the admin, 2026-11-03); notes say where the fingerprint decided.  Without one, an asset id and a
    file name that name two different files of this run are a problem."""
    prm = j.get("params") if isinstance(j.get("params"), dict) else j
    medias = list((prm or {}).get("medias") or [])
    imgs = _pi_images(j, rd)
    inv, names = _pi_inventory(rd)
    res = {"ok": True, "problems": [], "notes": [], "changed": False, "medias": medias, "kept": [], "added": [], "dropped": [], "renumbered": {},
           "musts_renumbered": [], "musts_superseded": [],
           "now": [{"image": x["label"], "product": x["product"], "asset": x["source"].get("asset_id", ""), "file": x["source"].get("name", ""),
                    "recorded": bool(x["source"])} for x in imgs]}
    if not judge:
        res["final"] = res["now"]
        return res
    want = []
    for e in judge:
        aid, fname = str(e.get("asset") or "").strip(), Path(str(e.get("file") or "").replace("\\", "/")).name.strip()
        mk = re.sub(r"[^0-9a-f]", "", str(e.get("fingerprint") or "").lower())
        mk = mk if len(mk) == 8 else ""
        named = (aid + " " + fname).strip()
        it = inv.get(aid) if aid else None
        if not it and fname:
            it = names.get(fname.lower())
        cur_m = next((x for x in imgs if mk and x["source"].get("original") and _pi_fingerprint(x["source"]["original"]) == mk), None)
        sure = bool(mk) and it is not None and _pi_fingerprint(it.get("path")) == mk       # the file its id or name gives has that fingerprint
        if mk and not sure:
            hit = _pi_by_fingerprint(inv, mk, fname)
            if hit is not None or cur_m is not None:
                old = it
                if hit is not None:
                    it, aid, fname = hit, str(hit["id"]), Path(str(hit["path"]).replace("\\", "/")).name
                else:
                    it, aid, fname = None, cur_m["source"].get("asset_id", ""), cur_m["source"].get("name", "")
                sure = True
                res["notes"].append(f"the judge named {named} #{mk}: by its fingerprint it is {(aid + ' ' + fname).strip()} in this run"
                                    + (f" ({old['id']} {Path(str(old.get('path') or '').replace(chr(92), '/')).name} here is another file)"
                                       if old is not None and old is not it else ""))
            else:
                res["notes"].append(f"the judge named {named} #{mk}: no file of this run has that fingerprint, so its asset id and file name decide")
        if not sure and aid and fname and inv.get(aid) is not None and names.get(fname.lower()) is not None and names[fname.lower()] is not inv[aid]:
            res["problems"].append(f"the judge named {aid} {fname}, two files of this run ({aid} is "
                                   f"{Path(str(inv[aid].get('path') or '').replace(chr(92), '/')).name}, {fname} is {names[fname.lower()]['id']}) and no "
                                   "fingerprint to tell which: an asset id is the run's own number, so ask the judge again for the fingerprint of the one it means")
            continue
        cur = cur_m or next((x for x in imgs if (x["source"] and ((aid and x["source"].get("asset_id") == aid)
                                                                  or (fname and x["source"].get("name", "").lower() == fname.lower())))
                             or (fname and fname.lower() in x["names"])), None)
        if not it and not cur:
            res["problems"].append(f"the judge named {(aid + ' ' + fname).strip()}: no image of the run's asset inventory and no input of this request is that file")
            continue
        if cur is not None and any(w["cur"] is cur for w in want):
            res["problems"].append(f"the judge named {cur['label']} twice")
            continue
        wid = aid or str((it or {}).get("id") or "") or (cur["source"].get("asset_id", "") if cur is not None else "")
        want.append({"e": e, "item": it, "cur": cur, "aid": wid})
    prod = [x for x in imgs if x["product"] or any(w["cur"] is x for w in want)]
    non = [x for x in imgs if not any(x is p for p in prod)]
    if prod and non and imgs.index(prod[0]) < max(imgs.index(x) for x in non):
        res["problems"].append("the product images (" + ", ".join(x["label"] for x in prod) + ") are not the last image inputs ("
                               + ", ".join(x["label"] for x in non) + " come after one): X2 puts the product images last; until then the judge's product images "
                               "cannot be applied")
    if res["problems"]:
        res["ok"] = False
        res["final"] = res["now"]
        return res
    final_media, final = [x["media"] for x in non], [dict(r) for r in res["now"] if not r["product"] and r["image"] in {x["label"] for x in non}]
    for k, w in enumerate(want, len(non) + 1):
        lab, e, cur = f"Image {k}", w["e"], w["cur"]
        if cur is not None and not str(e.get("prepare") or "").strip():
            m = dict(cur["media"])
            if cur["label"] != lab:
                res["renumbered"][cur["label"]] = lab
                if isinstance(m.get("label"), str):
                    m["label"] = re.sub(r"^\s*Image ?\d+", lab, m["label"])
            res["kept"].append({"image": lab, "was": cur["label"], "asset": cur["source"].get("asset_id", ""), "file": cur["source"].get("name", "")})
            final.append({"image": lab, "product": True, "asset": cur["source"].get("asset_id", ""), "file": cur["source"].get("name", ""), "recorded": True})
        else:
            orig = str((w["item"] or {}).get("path") or (cur["source"].get("original") if cur else "") or "")
            name = Path(orig.replace("\\", "/")).name
            prep = str(e.get("prepare") or "").strip()
            m = {"role": "image_references", "value": f"<X3: prepare {name} for {lab}>", "label": f"{lab} = {name} (the judge's product image, to prepare)",
                 "meaning": str(e.get("why") or "").strip(), "source": {"original": orig, "asset_id": w["aid"], "prepared": prep, "kind": "product"}}
            res["added"].append({"image": lab, "asset": w["aid"], "file": name, "original": orig, "prepare": prep, "why": str(e.get("why") or ""),
                                 "replaces": cur["label"] if cur is not None else ""})
            if cur is not None and cur["label"] != lab:
                res["renumbered"][cur["label"]] = lab
            final.append({"image": lab, "product": True, "asset": w["aid"], "file": name, "recorded": True})
        final_media.append(m)
    res["dropped"] = [x["label"] for x in prod if not any(w["cur"] is x for w in want)]
    res["final"] = final
    if fixed:          # a regeneration: what each image number means in its prompt stays; re-preparing an image in its place is fine
        new = [a for a in res["added"] if not a["replaces"]]
        if res["renumbered"] or (new and res["dropped"]):
            res["problems"].append("a regeneration keeps what each image number its prompt names means: add product images after the last one, or leave "
                                   "out the last ones, never both and never moving one ("
                                   + (", ".join(f"{o} would become {n}" for o, n in res["renumbered"].items()) or
                                      f"{', '.join(res['dropped'])} left out while " + ", ".join(f"{a['asset'] or a['file']} would take {a['image']}" for a in new)) + ")")
            res["ok"] = False
            res["final"] = res["now"]
            return res
    for line in musts or []:
        nums = {f"Image {n}" for n in _pi_named(line)}
        if nums & set(res["dropped"]):
            res["musts_superseded"].append(line)
        elif nums & set(res["renumbered"]):
            res["musts_renumbered"].append({"line": line, "as": _pi_renumber(line, res["renumbered"])})
    out_m, placed = [], False
    for m in medias:
        if isinstance(m, dict) and m.get("role") == "image_references":
            if not placed:
                out_m.extend(final_media)
                placed = True
            continue
        out_m.append(m)
    if not placed:
        out_m.extend(final_media)
    res["medias"] = out_m
    res["changed"] = out_m != medias
    return res


def _draft_section(path) -> tuple[str, str]:
    """The checked draft request as the judge reads it: its prompt, its parameters and its inputs with what each is and where it came from (the
    client's asset id and original file name, how it was prepared), its product images and the client's images of that product. (text, prompt)."""
    j = _cf_request_json(path)
    prm = j.get("params") if isinstance(j.get("params"), dict) else j
    prompt = str((prm or {}).get("prompt") or j.get("prompt") or "")
    mm = j.get("medias_meaning") or j.get("media_meaning")
    meaning = dict(mm) if isinstance(mm, dict) else {}
    counts, inputs = {}, []
    for m in (prm or {}).get("medias") or []:
        if isinstance(m, dict):
            role = str(m.get("role") or "?")
            counts[role] = counts.get(role, 0) + 1
            lab = f"{({'image_references': 'Image', 'video_references': 'Video', 'audio_references': 'Audio'}).get(role, role)} {counts[role]}"
            inputs.append(f"{lab} ({role}): {m.get('meaning') or meaning.get(lab) or '-'}")
    params = ", ".join(f"{k}={v}" for k, v in _cf_params_dict(j).items() if k != "medias")
    rd = Path(path).resolve().parent.parent
    rd = rd if (rd / "state.json").is_file() else None
    inputs_text = _pi_inputs_text(j, rd) if rd else "; ".join(inputs)
    prod_text = _pi_product_text(j, rd) if rd else ""
    return (f"The checked draft request ({Path(path).name}; written by the pipeline's rules and checked at X4):\nPrompt:\n{prompt}\n"
            f"Parameters: {params or '-'}\nInputs:\n{inputs_text or '-'}" + (f"\n{prod_text}" if prod_text else "")), prompt


def _judgement_md(run: str, video: str, clip: str, d: dict, model_id: str, note: str = "", kept: list | None = None) -> str:
    """The judge's whole judgement for one video's (or clip's) prompt, as the file the run keeps beside its template (the admin, 2026-11-03: "for each
    product answer what and why and decide judgement let it do a .md file that will be saved for each video", never in the chat): the samples whose
    prompts it read and what it took from each, every other sample whose miss could happen in this video and where its prompt designs it out, the
    samples it set aside and why, the product images (the draft's, named, when it keeps them: `kept`), its changes to the plan, its notes, what the
    library does not cover and its flags."""
    head = f"# The judge's judgement: video {_cf_nn(video)}" + (f", clip {clip}" if clip else "") + f" of run {run}"
    meta = (f"{now_iso()} · video model {model_id or '?'} · {d.get('library_size', '?')} sample{'' if d.get('library_size') == 1 else 's'} in the library · prompts read: "
            f"{', '.join(d.get('read') or []) or 'none'}" + (f" · asked again with the note: {note}" if note else ""))
    lines = [head, "", meta, ""]

    def sect(title, items, empty="- none"):
        lines.extend([f"## {title}", ""] + (items or [empty]) + [""])

    def entry(x, fields, title=""):
        return (f"- **{x.get('id', '')}**" + (f": {title or x.get('title')}" if (title or x.get("title")) else "")
                + "".join(f"\n  - {label}: {x[k]}" for k, label in fields if str(x.get(k) or "").strip()))
    sect("Read and used (basis)", [entry(b, (("worked", "worked"), ("failed", "failed"), ("where", "where the prompt carries it")),
                                         " ".join(v for v in ((f"({b['model']})" if b.get("model") else ""), str(b.get("title") or "")) if v))
                                   for b in d.get("basis") or []])
    sect("Designed out: misses that could happen in this video", [entry(x, (("mechanism", "what this video shares with it"), ("why", "why it applies here"),
                                                                           ("where", "designed out in"))) for x in d.get("avoided") or []])
    sect("Set aside", [entry(x, (("why", "why it cannot happen here"),)) for x in d.get("set_aside") or []])
    if d.get("unjudged"):
        sect("Not judged (named in none of the three)", ["- " + ", ".join(str(x) for x in d["unjudged"])])
    sect("Product images", ["- " + " · ".join(str(v) for v in (p.get("asset"), p.get("file")) if v) + (f" #{p['fingerprint']}" if p.get("fingerprint") else "")
                            + (f" (prepare: {p['prepare']})" if p.get("prepare") else "")
                            + (f": {p['why']}" if p.get("why") else "") for p in d.get("product_images") or [] if isinstance(p, dict)],
         "\n".join(f"- kept from the draft: {k}" for k in kept) if kept else "- the draft's product images, as they are")
    sect("Changes to the plan", [f"- {c.get('what', '')}" + (f": {c['why']}" if c.get("why") else "") + (f" ({c['id']})" if c.get("id") else "")
                                 for c in d.get("changes") or [] if isinstance(c, dict)])
    for title, k in (("Notes", "notes"), ("Not covered by the library", "not_covered"), ("No template", "none_reason")):
        if str(d.get(k) or "").strip():
            sect(title, [str(d[k]).strip()])
    if d.get("flags"):
        sect("Flags", [f"- {f.get('id') or 'the library'}: {f.get('what', '')}" + (f" ({f['effect']})" if f.get("effect") else "")
                       for f in d["flags"] if isinstance(f, dict)])
    return "\n".join(lines).rstrip() + "\n"


def cmd_prompt_template(a):
    """X4b, after X1-X4 of the first request of a video (the user, 2026-10-28). The whole checked brief goes to the judge (Loupe's keeper, one separate Opus
    session that holds the samples of earlier generations): the agent's brief (what it is working on, what the video is about, what it wants to achieve),
    the checked draft request (its prompt, parameters and inputs), the lines the prompt must carry word for word, the locked model's request structure and
    the video model's entry of the model index. The judge chooses which samples' saved prompts to read, Loupe sends each one's saved prompts whole, and the answer is the final
    prompt, which `template-apply` puts in the request word for word. Saved beside the plan; no template (empty library, Loupe or the keeper unavailable)
    means the checked draft is the request."""
    ctx = _qc_ctx(a)
    rd = _cf_run_dir(a.run) if a.run else None
    tf = _tpl_files(rd, a.video, a.clip) if (rd and a.video) else {}
    brief_file = a.brief_file or (str(tf["brief"]) if tf and not a.brief and tf["brief"].is_file() else "")
    draft_file = a.draft_file or (str(tf["draft"]) if tf and tf["draft"].is_file() else (str(tf["request"]) if tf and tf["request"].is_file() else ""))
    musts_file = a.musts_file or (str(tf["musts"]) if tf and tf["musts"].is_file() else "")
    for f, what in ((brief_file, "--brief-file"), (a.structure_file, "--structure-file"), (draft_file, "--draft-file"), (musts_file, "--musts-file")):
        if f and not Path(f).is_file():
            fail(f"{what} {f} is not a file", 2)
    brief = (a.brief or "").strip()
    if brief_file:
        brief = (brief + "\n\n" if brief else "") + Path(brief_file).read_text(encoding="utf-8", errors="replace").strip()
    if not brief:
        fail("prompt-template needs --brief or --brief-file (what you are working on, what the video is about, what it wants to achieve, one line per beat)", 2)
    draft_text, draft_prompt = _draft_section(draft_file) if draft_file else ("", "")
    musts = _musts_of(musts_file) if musts_file else []
    question = "\n\n".join(x for x in (brief, draft_text, ("Lines the prompt must carry, word for word (checked at X4):\n" + "\n".join(f"- {m}" for m in musts)) if musts else "",
                                       f"The service refuses a prompt over {PROMPT_LIMIT} characters.") if x)
    structure = Path(a.structure_file).read_text(encoding="utf-8", errors="replace").strip() if a.structure_file else ""
    vm = _video_model_info(ctx.get("model"))
    body = {**ctx, "purpose": "template", "question": question, "structure": structure, "video_model": vm}
    tries = 0
    while True:
        s, d = _cf_api("POST", "/api/qc/consult", body, key="qc", timeout=CONSULT_TIMEOUT)
        if not (s == 200 and (d or {}).get("mode") == "busy") or tries >= TEMPLATE_BUSY_RETRIES:
            break
        tries += 1
    if s != 200:
        out({"ok": True, "mode": "unavailable", "template": "", "basis": [], "note": "no template: " + str((d or {}).get("error") or f"HTTP {s}"),
             "none_rule": "the checked draft is the request, as always: record it with `T template-apply --use-draft` and write 'no template: Loupe unavailable' in the pattern card"})
    res = {"ok": True, "mode": d.get("mode"), "template": d.get("template", ""), "basis": d.get("basis", []),
           "notes": d.get("notes", ""), "changes": d.get("changes", []), "read": d.get("read", []), "not_covered": d.get("not_covered", ""),
           "none_reason": d.get("none_reason", ""), "product_images": d.get("product_images") or [],
           "video_model": vm.get("id", ""), "draft_file": draft_file, "musts": len(musts), "clip": a.clip or "", "busy_retries": tries}
    if d.get("mode") == "keeper":      # what the judge decided for every sample of its library: counted here, written whole to the judgement file
        res["judged"] = {"basis": len(res["basis"]), "avoided": len(d.get("avoided") or []), "set_aside": len(d.get("set_aside") or []),
                         "unjudged": len(d.get("unjudged") or [])}
    if res["product_images"]:
        res["product_images_rule"] = ("product_images is the judge's choice of the product images this request carries, which and how many (the "
                                      "character, the original reference and every other input stay): `T template-apply` puts them in the request with its "
                                      "prompt (the inputs before them keep their numbers; an image it adds gets a placeholder value and its source: prepare it "
                                      "from that original as source.prepared says, else as the pipeline prepares product views, and upload it at X3 before X5); "
                                      "a problem it reports (an image not in the run's inventory, product images that are not the last inputs) is asked of "
                                      "the judge once more with --note. Record the product images in the pattern card's \"Judge's template\" block.")
    for k in ("needs_asked", "needs_unmet", "prompts_judged", "prompts_unread", "library_read", "keeper_error", "keeper_restarted", "library_size", "flags"):
        if d.get(k):
            res[k] = d[k]
    if res.get("flags"):
        res["flags_rule"] = ("flags are what the judge found missing, contradictory or ambiguous in the records of the samples it used (id, what, effect): "
                             "its prompt already weighs them; write each as a judge gap in the \"Judge's template\" block ('flag S12: <what>')")
    clip_arg = f" --clip {a.clip}" if a.clip else ""
    if res["template"]:
        res["rules"] = ("This is the judge's final prompt. Put it in the request word for word: `T template-apply --run RUN --video NN" + clip_arg + "` (fill a "
                        "[SLOT: ...] only with what the plan already decided, --slot). Never rewrite, trim, reorder or improve it; X4 does not run again on its "
                        "wording. When template-apply reports a must-carry line missing, a slot left or a length over the limit, ask the judge once more with "
                        "--note; only then add a missing must-carry line word for word (--add-must) or keep the checked draft (--use-draft). Record it in the "
                        "pattern card's \"Judge's template\" block. The judge is not asked again before the generation.")
    else:
        res["none_rule"] = ("no template (" + (res["none_reason"] or res.get("keeper_error") or str(res["mode"])) + "): the checked draft is the request, as "
                            "always; record it with `T template-apply --use-draft" + clip_arg + "` and write 'no template: <why>' in the pattern card's \"Judge's template\" block")
    if d.get("needs_unmet"):
        res["unmet_rule"] = ("the judge asked for something Loupe cannot fetch (a question only you can answer from your plan, or a file that does not exist): "
                             "answer it from the plan in words and ask again ONCE with --note '<your answer>' (the same files); if it is still unmet, go on "
                             "and write it as a judge gap in the \"Judge's template\" block")
    try:
        if tf:
            write_json(tf["json"], {**res, "avoided": d.get("avoided") or [], "set_aside": d.get("set_aside") or [], "unjudged": d.get("unjudged") or [],
                                    "brief": brief, "draft_prompt": draft_prompt, "musts_list": musts, "structure_file": a.structure_file or "", "at": now_iso()})
            res["saved"] = str(tf["json"])
            if d.get("mode") == "keeper":      # the judge's whole judgement, kept for this video and never printed into the conversation
                jd = _cf_request_json(Path(draft_file)) if draft_file and not res["product_images"] else {}
                kept = [" · ".join(str(v) for v in (x["label"], (x.get("source") or {}).get("asset_id"),
                                                     (x.get("source") or {}).get("name") or next(iter(sorted(x.get("names") or [])), "")) if v)
                        for x in (_pi_images(jd, rd) if jd else []) if x.get("product")]
                write_text(tf["judgement"], _judgement_md(rd.name, a.video, a.clip or "", d, vm.get("id", ""), a.note or "", kept))
                res["judgement_file"] = str(tf["judgement"])
                res["judgement_rule"] = ("judgement_file holds the judge's whole judgement for this video: the samples whose prompts it read and what it took "
                                         "from each, every other sample whose miss could happen here and where its prompt designs it out, and the samples it "
                                         "set aside and why. Never paste it into the chat: name the file (and in the pattern card's \"Judge's template\" "
                                         "block); read it only when a part of the prompt is unclear to you.")
            if res["template"]:
                write_text(tf["md"], res["template"] + "\n")
                res["template_file"] = str(tf["md"])
            pf = _prompts_files(res["basis"], rd)
            if pf:
                res["prompts_files"] = pf
                res["prompts_rule"] = ("the saved prompts of each basis sample (every box its frames speak through, named flawed, correct or example), whole "
                                       "from Loupe's record, to read only when a part of the judge's prompt is unclear to you; its prompt already carries "
                                       "what worked, adapted to this video")
    except OSError:
        pass
    out(res)


def cmd_product_images(a):
    """A regeneration takes the judge's product images from its QC answer (the admin, 2026-10-30: the judge decides which product images and how many).
    The judge's list (60-outputs/video-NN/qc-consult.json product_images, or --answer) is planned against the regeneration's request: the images its prompt
    names keep their numbers, so images are only added after the last one or the last ones left out, never both; an added image gets a placeholder value and the source
    to prepare it from. Prints the plan as facts; --apply writes it (the request as it was kept beside it once, .pre-product-images.json). Refuses a request
    the ledger already holds."""
    rd, st = _state_of(a.run)
    nn = _cf_nn(a.video)
    req_p = Path(a.request)
    j = _cf_request_json(req_p)
    if not j:
        fail(f"{req_p} is not a request JSON", 2)
    ans_p = Path(a.answer) if a.answer else rd / "60-outputs" / f"video-{nn}" / "qc-consult.json"
    try:
        ans = json.loads(ans_p.read_text(encoding="utf-8")) if ans_p.is_file() else {}
    except (OSError, ValueError):
        ans = {}
    pims = list(ans.get("product_images") or []) if isinstance(ans, dict) else []
    if not pims:
        out({"ok": True, "changed": False, "answer": str(ans_p), "note": "the judge's answer lists no product images: the regeneration keeps the product images it has"})
    held = [s for s in st.get("submissions") or [] if isinstance(s, dict) and s.get("request_file")
            and os.path.normcase(os.path.abspath(str(s["request_file"]))) == os.path.normcase(os.path.abspath(str(req_p)))]
    if held:
        out({"ok": False, "changed": False, "problems": [f"{req_p.name} is in the ledger ({held[0].get('status')}): a regeneration writes its own request; this one stays as submitted"]})
    musts = _musts_of(a.musts_file) if a.musts_file else []
    plan = _product_plan(rd, j, pims, musts, fixed=True)
    prm = j.get("params") if isinstance(j.get("params"), dict) else j
    res = {"ok": plan["ok"], "request": str(req_p), "answer": str(ans_p), "applied": False, "problems": plan["problems"], "notes": plan["notes"],
           **{k: plan[k] for k in ("now", "final", "kept", "added", "dropped", "renumbered", "musts_superseded", "musts_renumbered")}}
    n_img = sum(1 for m in plan["medias"] if isinstance(m, dict) and m.get("role") == "image_references")
    res["prompt_names_images_beyond_the_inputs"] = [f"Image {n}" for n in sorted(_pi_named(str((prm or {}).get("prompt") or ""))) if n > n_img]
    if a.apply and plan["ok"] and plan["changed"]:
        keep = req_p.with_name(req_p.stem + ".pre-product-images.json")
        if not keep.is_file():
            write_json(keep, j)
        tgt = j["params"] if isinstance(j.get("params"), dict) else j
        tgt["medias"] = plan["medias"]
        j["product_images"] = {"by": "the judge (QC, for this regeneration)", "final": plan["final"], "kept": plan["kept"], "added": plan["added"],
                               "dropped": plan["dropped"], "at": now_iso()}
        write_json(req_p, j)
        res.update({"applied": True, "kept_as": str(keep)})
    res["note"] = ("facts only: an image added has a placeholder value and its source (prepare it from that original as source.prepared says, else as the "
                   "pipeline prepares product views, and upload it at X3 before X5); an image the prompt names that the request does not carry, or a problem, "
                   "means the regeneration keeps the product images it had: record it as a judge gap")
    out(res)


def cmd_template_apply(a):
    """X4b: the judge's prompt becomes the request's prompt word for word (the user, 2026-10-28: nothing after the judge deforms its prompt). The checked
    draft is kept as <request>.draft.json the first time and is the base of every apply: only its prompt is replaced. --slot "<slot words>=<value>" fills
    [SLOT: <slot words>] with a value the plan already decided; --add-must "<line>" adds, word for word at the end, a must-carry line the judge left out
    after it was asked again; --use-draft puts the checked draft back (no usable template). Reports facts, decides nothing: the must-carry lines the
    prompt does not hold word for word, the slots left, the length against the service's limit."""
    rd, _st = _state_of(a.run)
    tf = _tpl_files(rd, a.video, a.clip)
    req_p = Path(a.request) if a.request else tf["request"]
    if not req_p.is_file():
        fail(f"no request file {req_p}", 2)
    draft_p = req_p.with_name(req_p.stem + ".draft.json")
    if not draft_p.is_file():
        j0 = _cf_request_json(req_p)
        if not j0:
            fail(f"{req_p.name} is not a request JSON", 2)
        write_json(draft_p, j0)                  # the checked draft, kept as X4 left it
    draft = _cf_request_json(draft_p)
    dprm = draft.get("params") if isinstance(draft.get("params"), dict) else draft
    filled, added = [], []
    if a.use_draft:
        final, source = str((dprm or {}).get("prompt") or ""), "draft"
    else:
        try:
            t = json.loads(tf["json"].read_text(encoding="utf-8")) if tf["json"].is_file() else {}
        except (OSError, ValueError):
            t = {}
        final = str((t or {}).get("template") or "").strip()
        if not final:
            fail("no judge's prompt for this video (prompt-template answered none, or was not asked): the checked draft stays the request; record it with --use-draft", 2)
        source = "judge"
        for sv in a.slot or []:
            k, sep, v = sv.partition("=")
            if not sep or not k.strip():
                fail('--slot takes "<slot words>=<value>"', 2)
            final, n = re.subn(r"\[SLOT:\s*" + re.escape(k.strip()) + r"\s*\]", lambda _m, v=v.strip(): v, final)
            filled.append({"slot": k.strip(), "filled": n})
        for m in a.add_must or []:
            final = final.rstrip() + ("\n" if "\n" in final else " ") + m.strip()
            added.append(m.strip())
    musts = _musts_of(a.musts_file) if a.musts_file else (_musts_of(tf["musts"]) if tf["musts"].is_file() else [])
    pims = [] if a.use_draft else list((t or {}).get("product_images") or [])      # the judge's product images (the admin, 2026-10-30)
    plan = _product_plan(rd, draft, pims, musts) if pims else None
    newj = json.loads(json.dumps(draft))
    tgt = newj["params"] if isinstance(newj.get("params"), dict) else newj
    tgt["prompt"] = final
    expect = musts
    if plan and plan["ok"]:
        tgt["medias"] = plan["medias"]
        newj["product_images"] = {"by": "the judge (X4b)", "final": plan["final"], "kept": plan["kept"], "added": plan["added"],
                                  "dropped": plan["dropped"], "renumbered": plan["renumbered"], "at": now_iso()}
        renum = {r["line"]: r["as"] for r in plan["musts_renumbered"]}
        expect = [renum.get(m, m) for m in musts if m not in set(plan["musts_superseded"])]
    nf = _norm_ws(final)
    missing = [m for m in expect if _norm_ws(m) not in nf]
    n_img = sum(1 for m in (tgt.get("medias") or []) if isinstance(m, dict) and m.get("role") == "image_references")
    beyond = sorted(n for n in _pi_named(final) if n > n_img)
    newj["prompt_source"] = source + (" + must-carry lines added: " + " | ".join(added) if added else "")
    write_json(req_p, newj)
    out({"ok": True, "request": str(req_p), "draft": str(draft_p), "prompt_source": newj["prompt_source"], "chars": len(final), "limit": PROMPT_LIMIT,
         "over_limit": len(final) > PROMPT_LIMIT, "musts_checked": len(expect), "musts_missing": missing,
         "slots_left": re.findall(r"\[SLOT:[^\]]*\]", final), "slots_filled": filled, "musts_added": added,
         "product_images": ({k: plan[k] for k in ("final", "kept", "added", "dropped", "renumbered")} if plan and plan["ok"] else None),
         "product_images_problems": (plan["problems"] if plan and not plan["ok"] else []),
         "product_images_notes": (plan["notes"] if plan else []),
         "musts_renumbered": (plan["musts_renumbered"] if plan and plan["ok"] else []),
         "musts_superseded": (plan["musts_superseded"] if plan and plan["ok"] else []),
         "prompt_names_images_beyond_the_inputs": [f"Image {n}" for n in beyond],
         "note": "facts only: a must-carry line missing, a slot left, a length over the limit, a product-images problem or an image the prompt names that "
                 "the request does not carry is asked of the judge once more (prompt-template --note); only then --add-must or --use-draft. A must-carry "
                 "line that names a product image is checked in the numbers of the judge's product images (musts_renumbered; --add-must takes that "
                 "form); one that names an image the judge left out is no longer the request's (musts_superseded)"})


def _sample_prompts_file(sid: str, rd) -> dict:
    """The prompts of one sample, whole from Loupe's record, written to RUN/40-briefs/samples/<id>-prompts.md; {saved} or {note} (nothing saved,
    Loupe unreachable): the boxes the sample has frames for (prompt_sides), each named by what it is (LOUPE_PROMPTS_WORDS): the flawed version's prompt,
    the correct version's, or an Examples sample's one example box, each holding only the generations the sample's frames come from. Nothing is
    compared, cut or summarised."""
    s, d = _cf_api("GET", f"/api/qc/samples/{sid}?prompts=1", key="qc", timeout=30)
    if s != 200:
        return {"ok": True, "mode": "unavailable", "id": sid, "prompts": "", "note": "no prompts: " + str((d or {}).get("error") or f"HTTP {s}")}
    smp = d.get("sample") or {}
    kind = str(smp.get("prompts") or "")
    wrong, fixed, note = str(smp.get("wrong_prompt") or ""), str(smp.get("fixed_prompt") or ""), str(smp.get("prompt_note") or "")
    res = {"ok": True, "id": sid, "prompts": kind, "title": smp.get("title", ""), "model": smp.get("model", ""), "run": smp.get("run", ""), "video": smp.get("video", ""),
           "prompt_note": note, "chars": {"wrong": len(wrong), "fixed": len(fixed)}, "prompt_roles": smp.get("prompt_roles") or {},
           "prompt_sides": [x for x in (smp.get("prompt_sides") or ["wrong", "fixed"]) if x in ("wrong", "fixed")],
           "miss_id": smp.get("miss_id"), "record": bool(smp.get("record")),
           "generations": {side: max([int(x.get("of") or 0) for x in smp.get(f"{side}_segments") or [] if isinstance(x, dict)] or [1 if txt else 0])
                           for side, txt in (("wrong", wrong), ("fixed", fixed))}}
    if not kind:
        res["note"] = "the admin saved no prompt for this sample"
        return res
    sides = res["prompt_sides"]          # the boxes the sample has frames for: an Examples sample's one box, the flawed / correct version's
    one_box = bool(smp.get("examples_only")) and len(sides) == 1
    head = (f"the example prompt of {'Video A' if sides[0] == 'wrong' else 'Video B'} (an Examples sample has one prompt box: the generations its Example frames come from)" if one_box
            else "the flawed version's prompt and the correct version's prompt" if sides == ["wrong", "fixed"]
            else "the correct version's prompt alone (none of its frames is called WRONG: no flawed version's prompt)" if sides == ["fixed"]
            else "the flawed version's prompt alone (none of its frames is called RIGHT: no correct version's prompt)")
    lines = [f"# {sid} · " + head, "", f"Title: {smp.get('title', '')}",
             f"Model: {smp.get('model') or 'any'} · from run {smp.get('run') or '-'} video {smp.get('video') or '-'} · kinds: {', '.join(smp.get('kinds') or []) or '-'}"]
    if note:
        lines += ["", "## The admin's note on the prompt", "", note]
    role_word = {"wrong": "WRONG", "right": "RIGHT", "example": "EXAMPLE"}
    video_name = {"wrong": "Video A", "fixed": "Video B"}
    secs = lambda x: f"{float(x or 0):.3f}".rstrip("0").rstrip(".")  # noqa: E731
    mmss = lambda t: f"{int(float(t or 0) // 60)}:{float(t or 0) - int(float(t or 0) // 60) * 60:05.2f}"  # noqa: E731
    roles = smp.get("prompt_roles") or {}        # a side that speaks only for Example frames (or a sample of Examples only) has an Example prompt
    ex_title = "the example prompt of {v} (its frames are called EXAMPLE: a suggestion of what could have changed or been done another way, neither a bad generation nor a correct one)"
    what_of = {"wrong": "a prompt of the flawed version", "right": "a prompt of the correct version", "example": "an example prompt"}
    for side, text, title, none in (("wrong", wrong, ex_title.format(v="Video A") if roles.get("wrong") == "example" else "the flawed version (the generations the frames called WRONG come from)",
                                     "_not saved by the admin_"),
                                    ("fixed", fixed, ex_title.format(v="Video B") if roles.get("fixed") == "example" else "the correct version (the generations the frames called RIGHT come from)",
                                     "_not saved by the admin_")):
        if side not in sides:
            continue          # a box this sample has no frame for: never this sample's prompt
        segs = [x for x in (smp.get(f"{side}_segments") or []) if isinstance(x, dict)]
        if segs:          # a take made of several generations (clips joined): Loupe gives the prompt of each generation this sample's frames come from, and no other
            of = max(int(x.get("of") or 0) for x in segs) or len(segs)
            lines += ["", f"## Prompts of {title}: the prompt of each generation this sample's frames come from ({len(segs)} of the {of} its take was made of)"]
            for k, sg in enumerate(segs, 1):
                # the frames as the sample's image tags them (FRAME n, the role, the time; VIDEO A or B and the generation under it)
                fl = [f"Frame {f.get('n')} ({role_word.get(f.get('role'), str(f.get('role')).upper())}, {mmss(f.get('t'))})" for f in sg.get("frames") or []]
                fr = fl[0] if len(fl) == 1 else ", ".join(fl[:-1]) + " and " + fl[-1] if fl else ""
                spans = sg.get("spans") or [[sg.get("t_from"), sg.get("t_to")]]
                where = " and ".join(f"second {secs(a)} to second {secs(b)}" for a, b in spans) + f" of {video_name.get(sg.get('src'), 'that video')}"
                kinds = list(dict.fromkeys(f.get("role") for f in sg.get("frames") or []))
                what = " and ".join(what_of[x] for x in kinds if x in what_of) or "the prompt"
                lines += ["", f"### Generation {sg.get('gen') or k} of {of} · clip {sg.get('clip') or '-'} · {sg.get('request') or 'request not named'}",
                          (f"_This is {what}: it generated {where}, and made {fr} of this sample._" if fr
                           else f"_This is the prompt that generated {where}; no frame of this sample comes from it._"),
                          "", str(sg.get("prompt") or "").strip() or "_not saved_"]
        elif text:
            lines += ["", f"## Prompt of {title}", "", text]
        else:
            lines += ["", f"## Prompt of {title.split(' (')[0]}", "", none]
    rec = str(smp.get("record") or "")
    if rec:          # Loupe's whole record of the sample: its generation miss, the admin's words, its frames with the prompt that made each, every prompt under its label
        lines = [lines[0] + f" · its whole record from Loupe (generation miss R{smp.get('miss_id') or '?'})", "",
                 f"_Everything from the record's === SAMPLE line to its === END OF SAMPLE line belongs to {sid} alone: its generation miss, the admin's words, "
                 f"its frames and every prompt, each prompt under its label ({sid}-P1 ...) with the frames it made._", "", rec]
    if one_box:
        lines += ["", "_This sample's frames are all Examples, each a suggestion of what could have changed or how it could have been done another way, neither a bad generation nor a correct one; "
                  "an Examples sample takes all its frames from one video and keeps one box: the example prompt of each generation its Example frames come from, under the seconds it made. Read it "
                  "with the admin's words for what the example suggests; never take it as a flawed or a correct prompt, never paste a sentence of it, "
                  "never take it as a rule for another video._", ""]
    elif smp.get("examples_only"):
        lines += ["", "_This sample's frames are all Examples, each a suggestion of what could have changed or how it could have been done another way, neither a bad generation nor a correct one. Read these prompts "
                  "with the admin's words for what the example suggests; never take either as a flawed or a correct prompt, never paste a sentence of either, "
                  "never take one as a rule for another video._", ""]
    else:
        lines += ["", ("_Read both and judge what the correct version's prompt did differently from the flawed version's at the frames each made" if sides == ["wrong", "fixed"]
                       else "_Read it for what " + ("the correct version's prompt secured at the frames it made (this sample shows the correct version only)" if sides == ["fixed"]
                                                    else "the flawed version's prompt let happen at the frames it made (nothing of this sample shows the correct version)"))
                  + " and whether that is the mechanism of the beat you are writing or checking. Apply the "
                  "mechanism in the locked model's own structure and in your own words; never paste a sentence of any prompt, never name the wrong behaviour in a prompt, "
                  "never take the correct version's prompt as a rule for another video._" + (" A prompt named an example made frames the admin keeps as Examples: a "
                                                                                          "suggestion, read it as one, never as the flawed or the correct prompt." if "example" in roles.values() else ""), ""]
    f = Path(rd) / "40-briefs" / "samples" / f"{sid}-prompts.md"
    f.parent.mkdir(parents=True, exist_ok=True)
    write_text(f, "\n".join(lines))
    res["saved"] = str(f)
    res["rule"] = "read the file only for a sample you judged relevant to this video; judge what changed yourself; the mechanism goes into the request in the model's structure and your words, never a sentence of either prompt"
    return res


def _prompts_files(items, rd) -> dict:
    """For every cited sample marked `prompts`, its saved prompts (every box its frames speak through) written whole for the agent: {S..: path}. The answer itself never carries their text."""
    res = {}
    for x in items or []:
        if isinstance(x, dict) and x.get("prompts") and x.get("id") and rd:
            r = _sample_prompts_file(str(x["id"]), rd)
            if r.get("saved"):
                res[str(x["id"])] = r["saved"]
    return res


def cmd_sample_prompts(a):
    """The prompts of ONE sample, each named by what it is (the flawed version's prompt: the generations its frames called WRONG come from; the correct
    version's: those its frames called RIGHT come from; an Examples sample's one example box, a suggestion of what could have changed or how it could have
    been done another way, neither a bad generation nor a correct one; only the boxes it has frames for; and the admin's note on what made the
    difference, as the admin saved them in Loupe), fetched whole and written to a file of the run (qc-consult and plan-hints write them by themselves for
    every sample they cite). Nothing is compared, cut or summarised here: read the file and judge what the correct version's prompt did differently from the flawed version's."""
    sid = (a.id or "").strip().upper()
    if not re.fullmatch(r"S\d+", sid):
        fail("sample-prompts needs --id S<number> (a sample id from qc-consult, qc-brief or plan-hints)", 2)
    out(_sample_prompts_file(sid, _cf_run_dir(a.run)))


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
    """Size reckoning for a product in a frame (anomaly-catalog.md §2.7): arithmetic only, no verdict.

    Before generation (plan): `scale --product-cm 15.7 --distance 1.5 --lens 26` gives the fraction
    of the frame height and the pixel height the product should have at that depth, plus a table
    over the usual shot distances, so the prompt and a start frame can be built at the right size.
    After generation (QC): add `--product-px <y0-y1 | px>` measured on a full-resolution frame, and
    a neighbour of known size at (about) the same depth: `--ref-cm 22 --ref-px <y0-y1 | px>`
    (`--depth-ratio` = product distance / neighbour distance when they differ). It then gives the
    observed size as a multiple of the expected one for each estimate that could be made (against the
    neighbour, against the distance and the lens) and, when there are two, how far they are from each
    other. What those numbers mean (within what deviation a size is acceptable, when two estimates agree
    enough, whether a distance was assumed) is the agent's reading, guided by anomaly-catalog.md §2.7.

    The distance is never assumed (CE-028): derive it from the frame (the surface the product stands
    on, a same-plane neighbour of known size) and say how with `--distance-basis "<how d was
    derived>"`; the text is recorded with the numbers.

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
    frac = exp_ratio = None
    # 1. expected size from distance + lens
    if a.distance:
        frac = H * f / (36.0 * a.distance)
        res["distance_m"] = a.distance
        res["expected_fraction_of_frame_height"] = round(frac, 4)
        res["expected_px"] = round(frac * frame_h, 1)
        res["distance_basis"] = a.distance_basis or None
    shots = [("extreme close-up", 0.4), ("close-up", 0.7), ("medium close-up", 1.0), ("medium", 1.5),
             ("medium-wide", 2.5), ("wide", 4.0)]
    res["table"] = [{"shot": s, "distance_m": d, "fraction": round(H * f / (36.0 * d), 4),
                     "px": round(H * f / (36.0 * d) * frame_h, 1)} for s, d in shots]
    # 2. expected ratio to a neighbour of known size
    if a.ref_cm:
        ratio = exp_ratio = (a.product_cm / a.ref_cm) / max(1e-6, a.depth_ratio)
        res["neighbour_cm"] = a.ref_cm
        res["depth_ratio"] = a.depth_ratio
        res["expected_ratio_to_neighbour"] = round(ratio, 3)
    # 3. observed, as a multiple of the expected size, per estimate
    estimates = []
    if a.product_px:
        ppx = _px_span(a.product_px, "--product-px")
        res["observed_px"] = round(ppx, 1)
        res["observed_fraction_of_frame_height"] = round(ppx / frame_h, 4)
        if a.ref_cm and a.ref_px:
            rpx = _px_span(a.ref_px, "--ref-px")
            obs_ratio = ppx / max(1e-6, rpx)
            res["neighbour_px"] = round(rpx, 1)
            res["observed_ratio_to_neighbour"] = round(obs_ratio, 3)
            res["size_vs_neighbour"] = round(obs_ratio / exp_ratio, 3)
            estimates.append({"basis": "neighbour ratio", "size_factor": res["size_vs_neighbour"],
                              "deviation_pct": round((res["size_vs_neighbour"] - 1.0) * 100.0, 1)})
        if a.distance:
            res["size_vs_distance"] = round((ppx / frame_h) / frac, 3)
            estimates.append({"basis": "distance+lens fraction", "size_factor": res["size_vs_distance"],
                              "deviation_pct": round((res["size_vs_distance"] - 1.0) * 100.0, 1)})
        if not estimates:
            res["notes"].append("observed size given, but nothing to compare it with: add --ref-cm/--ref-px or --distance")
    res["estimates"] = estimates
    if len(estimates) == 2:
        lo, hi = sorted(e["size_factor"] for e in estimates)
        res["estimates_spread_pct"] = round((hi / max(1e-6, lo) - 1.0) * 100.0, 1)
    if a.distance and not a.distance_basis:
        res["notes"].append("--distance-basis not stated: say how the distance was derived from the frame")
    if estimates:
        line = "; ".join(f"{e['basis']}: {e['size_factor']}x ({e['deviation_pct']:+.1f} %)" for e in estimates)
        print(f"size of {res['label']} as a multiple of the expected size - {line}", file=sys.stderr)
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
    parts, heads = [], []
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
        heads.append(t0)          # the seconds dropped from this part's head (the join record shifts its pieces by them)
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
    pieces, t = [], 0.0          # the join record: which seconds of the output each piece fills, with the clip and attempt it sits in
    for c, p, t0 in zip(a.clips, parts, heads):
        secs = float(media_summary(p).get("duration_s") or 0)
        sub = _join_record_of(Path(c))          # an input that is itself a join (a piece cut from the clean video): its own pieces, in this output's seconds
        if sub and sub.get("pieces"):
            for x in sub["pieces"]:
                a0, b0 = max(float(x["t_from"]) - t0, 0.0), min(float(x["t_to"]) - t0, secs)
                if b0 > a0 + 1e-6:
                    pieces.append({**x, "t_from": round(t + a0, 3), "t_to": round(t + b0, 3)})
        else:
            clip, att = _clip_of_path(c)
            pieces.append({"file": str(Path(c).resolve()), "clip": clip, "attempt": att, "t_from": round(t, 3), "t_to": round(t + secs, 3)})
        t += secs
    shutil.rmtree(work, ignore_errors=True)
    rec = Path(str(a.out) + JOIN_SUFFIX)
    write_text(rec, json.dumps({"file": Path(a.out).name, "sha1": _file_sha1(Path(a.out)), "duration_s": o.get("duration_s"), "written": now_iso(),
                                "by": "awl.py concat", "seams": seams, "pieces": pieces}, ensure_ascii=False, indent=1))
    out({"ok": True, "file": a.out, "duration_s": o.get("duration_s"), "size": f"{o['display_width']}x{o['display_height']}",
         "fps": o.get("fps"), "seams": seams, "join_record": str(rec),
         "pieces": [{k: x[k] for k in ("clip", "attempt", "t_from", "t_to")} for x in pieces]})


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
    and folder) and its timeline_layout.json (the template's timeline id). Set both aside (*.awlbak), drop
    the template's build artefacts, and point the layout at the new timeline id, so that
    `capcut register --apply --materials` (after capcut_save) recreates a correct identity.
    --canvas WxH sets the project's canvas (Static: the format's export size), labelled as capcut-cli labels its presets."""
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
    canvas = None
    if getattr(a, "canvas", None):
        cw, ch = _parse_size(a.canvas)
        if cw % 2 or ch % 2:
            fail(f"the canvas needs even edges, got {a.canvas}", 2)
        cc = dict(content.get("canvas_config") or {})
        cc.update({"width": cw, "height": ch,
                   "ratio": next((k for k in CAPCUT_RATIO_LABELS if STATIC_ASPECTS[k][0] * ch == STATIC_ASPECTS[k][1] * cw), "original")})
        content["canvas_config"] = cc
        cp.write_text(json.dumps(content, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        canvas = cc
    moved = []
    for fn in ("draft_meta_info.json", "timeline_layout.json", "build-report.json", "build.log", "lint.json"):
        f = d / fn
        if f.exists():
            os.replace(f, d / (fn + ".awlbak"))
            moved.append(fn)
    write_json(d / "timeline_layout.json", {"dockItems": [{"dockIndex": 0, "ratio": 1, "timelineIds": [tid],
                                                           "timelineNames": ["Timeline 01"]}], "layoutOrientation": 1})
    out({"ok": True, "draft": str(d), "timeline_id": tid, "name": name, "set_aside": moved, "canvas": canvas,
         "next": "capcut_read_timeline → edits → capcut_validate → capcut_save, then: awl.py capcut-repair "
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
    projects in parallel. --preview then renders capcut-cli's low-res proxy (outside the lock). --keep-text leaves every text as it is
    (Static: the text look is the references', never the house style)."""
    d = Path(a.draft)
    if not (d / "draft_content.json").is_file():
        fail(f"not a CapCut draft (no draft_content.json): {d}", 2)
    cli = _capcut_cli()
    if (d / ".locked").exists() or _capcut_running():
        out({"ok": False, "draft": str(d), "steps": [],
             "action": "CapCut is running: close it and run this again (nothing was changed)"}, 1)
    lock = Path(cfg_get("runs_root", str(Path(__file__).resolve().parent.parent / "runs"))) / ".capcut-store.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    steps = ([{"step": "text-style", "exit": 0, "result": "kept: the draft's own text look (--keep-text)"}] if getattr(a, "keep_text", False)
             else [{"step": "text-style", "exit": 0, "result": _text_style_pass(d, write=True)}])   # before sync-timelines
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


def _font_files() -> list:
    """Font files on this PC the edit can use, as facts: CapCut's own (bundled with the newest app, then the ones it downloaded), then
    Windows' and the user's. One row per family and style (the first file found), never a judgement of which fits."""
    la = Path(os.environ.get("LOCALAPPDATA", ""))
    apps = []
    for p in (la / "CapCut" / "Apps").glob("*"):
        try:
            apps.append((tuple(int(x) for x in p.name.split(".")), p))
        except ValueError:
            continue
    roots = ([("capcut", max(apps)[1] / "Resources" / "Font")] if apps else []) + [
        ("capcut-downloaded", la / "CapCut" / "User Data" / "Cache"),
        ("windows", Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"),
        ("user", la / "Microsoft" / "Windows" / "Fonts")]
    try:
        from PIL import ImageFont
    except ImportError:
        return []
    seen, rows = set(), []
    for src, root in roots:
        if not root.is_dir():
            continue
        for f in sorted(root.rglob("*")):
            if f.suffix.lower() not in (".ttf", ".otf", ".ttc") or "__MACOSX" in f.parts or f.name.startswith("._"):
                continue
            try:
                fam, sty = ImageFont.truetype(str(f), 20).getname()
            except Exception:  # noqa: BLE001
                continue
            key = (str(fam).lower(), str(sty).lower())
            if key not in seen:
                seen.add(key)
                rows.append({"family": fam, "style": sty, "file": str(f).replace("\\", "/"), "source": src})
    return rows


def cmd_capcut_font(a):
    """Static (contract item 36): --list the fonts on this PC (CapCut's own first), or set one font file on every text of a draft (or of
    one track), the text's own size, colours, outline, box and ranges kept: the font family capcut-cli's text flags cannot set."""
    if a.list:
        rows = _font_files()
        if a.family:
            rows = [r for r in rows if a.family.lower() in str(r["family"]).lower()]
        out({"ok": True, "count": len(rows), "fonts": rows,
             "note": "CapCut draws its own fonts (capcut, capcut-downloaded) for sure; a Windows font is used when CapCut finds it"})
    if not a.draft or not a.font_file:
        fail("capcut-font needs --list, or --draft and --font-file", 2)
    d, ff = Path(a.draft), Path(a.font_file)
    if not (d / "draft_content.json").is_file():
        fail(f"not a CapCut draft (no draft_content.json): {d}", 2)
    if not ff.is_file():
        fail(f"font file not found: {ff}", 2)
    if (d / ".locked").exists() or _capcut_running():
        fail("CapCut is running: close it, then run this again", 3)
    try:
        from PIL import ImageFont
        family = ImageFont.truetype(str(ff), 20).getname()[0]
    except Exception:  # noqa: BLE001
        family = ff.stem
    font = str(ff).replace("\\", "/")
    files, names = [], set()
    for p in _draft_contents(d):
        content = json.loads(p.read_text(encoding="utf-8"))
        tracks = content.get("tracks", [])
        names.update(str(tr.get("name") or "") for tr in tracks if tr.get("type") == "text")
        ids = None
        if a.track:
            ids = {seg.get("material_id") for tr in tracks if str(tr.get("name") or "") == a.track for seg in tr.get("segments", [])}
        n = 0
        for m in content.get("materials", {}).get("texts", []):
            if ids is not None and m.get("id") not in ids:
                continue
            m.update({"font_name": "", "font_title": "none", "font_id": "", "font_resource_id": "", "font_category_id": "",
                      "font_category_name": "", "font_source_platform": 0, "font_team_id": "", "font_url": "", "fonts": [],
                      "font_path": font})
            try:
                c = json.loads(m.get("content") or "{}")
            except Exception:  # noqa: BLE001
                c = {}
            for s in c.get("styles") or []:
                s["font"] = {"id": "", "path": font}
            if c:
                m["content"] = json.dumps(c, ensure_ascii=False, separators=(",", ":"))
            n += 1
        if n:
            shutil.copyfile(p, p.with_name(p.name + ".font.bak"))
            write_text(p, json.dumps(content, ensure_ascii=False))
        files.append({"file": str(p), "texts_set": n})
    if a.track and not any(f["texts_set"] for f in files):
        fail(f"no text on a track named {a.track!r}; the draft's text tracks: {sorted(names)}", 2)
    out({"ok": True, "draft": str(d), "font": font, "family": family, "track": a.track, "files": files,
         "note": "then capcut_save is not needed (the file is written); run `T capcut-repair --draft ... --keep-text` after the last save"})


# --------------------------------------------------------------------------- CapCut house text style

HOUSE_TEXT_DEFAULT = {"font": "System", "size": 10, "fill": "#FFFFFF",
                      "stroke": {"color": "#000000", "width": 0.08},
                      # the user, 2026-10-29: "our standard text size is 10 but when there's only few text to be placed then use
                      # font size 11" (one size per video; config capcut.text_style.short_text, null turns it off)
                      "short_text": {"size": 11, "max_words_at_once": 5, "max_line_width": 0.82}}
# CapCut draws a size-s text with a font of CAPCUT_FONT_PER_SIZE * s * (canvas width) px. Measured on the covers CapCut itself
# rendered with its System font: 03_Oct_2026_v09 (size 10, lines 956 and 942 px wide on 1080) and 06_Oct_2026_v14 (size 9, 954 px).
CAPCUT_FONT_PER_SIZE = 0.00575
# material-level keys that a CapCut font / preset choice sets (copied by --learn from a text the user styled)
_TEXT_STYLE_KEY = re.compile(r"^(font_|fonts$|text_color$|text_alpha$|has_border$|border_|has_shadow$|shadow_|"
                             r"background_|bold_width$|italic_degree$|underline|letter_spacing$|line_spacing$|"
                             r"preset_|style_name$|check_flag$|use_effect_default_color$|text_preset_resource_id$|"
                             r"global_alpha$|ktv_color$|effect_style$)")


def _house_text_style() -> dict:
    cfg = cfg_get("capcut.text_style") or {}
    st = {**HOUSE_TEXT_DEFAULT, **cfg}
    st["stroke"] = {**HOUSE_TEXT_DEFAULT["stroke"], **(st.get("stroke") or {})}
    off = "short_text" in cfg and not cfg["short_text"]
    st["short_text"] = None if off else {**HOUSE_TEXT_DEFAULT["short_text"], **(cfg.get("short_text") or {})}
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


def _house_text_material(m: dict, st: dict, font_path: str, size: float) -> bool:
    """Rewrite one text material to the house style at `size` (the video's, _house_text_size); True when it changed. The text,
    its ranges, position and timing stay; font, size, fill, outline, shadow, background and preset fields become the house ones."""
    before = json.dumps(m, sort_keys=True)
    size = float(size)
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


def _timeline_texts(content: dict) -> list:
    """The text events a timeline shows: every segment that uses a text material, with its text, in and out (s) and scale."""
    mats = {m.get("id"): m for m in content.get("materials", {}).get("texts", [])}
    out = []
    for tr in content.get("tracks", []):
        for seg in tr.get("segments", []):
            m = mats.get(seg.get("material_id"))
            r = seg.get("target_timerange") or {}
            start, dur = int(r.get("start") or 0), int(r.get("duration") or 0)
            if m is None or dur <= 0:
                continue
            try:
                text = json.loads(m.get("content") or "{}").get("text", "")
            except Exception:
                text = ""
            scale = ((seg.get("clip") or {}).get("scale") or {}).get("x")
            out.append({"text": text, "start": start / 1e6, "end": (start + dur) / 1e6, "scale": float(scale or 1.0)})
    return out


_FONT100 = {}


def _line_width_frac(text: str, size: float, font_path: str, scale: float = 1.0) -> float:
    """The widest line of `text` at CapCut `size`, as a fraction of the canvas width (the font's ink extent, CAPCUT_FONT_PER_SIZE)."""
    if font_path not in _FONT100:
        from PIL import ImageFont
        _FONT100[font_path] = ImageFont.truetype(font_path, 100)
    f, widest = _FONT100[font_path], 0
    for line in text.split("\n"):
        if line.strip():
            left, _, right, _ = f.getbbox(line)
            widest = max(widest, right - left)
    return widest / 100 * CAPCUT_FONT_PER_SIZE * float(size) * float(scale or 1.0)


def _house_text_size(events: list, st: dict, font_path: str) -> dict:
    """One size for every text of a video: the house size (10), or short_text.size (11) when the video has only a little text,
    that is at no moment more than short_text.max_words_at_once words on screen (every text shown at that moment counted, so a
    caption split into two layers counts whole) and, at that size, every line within short_text.max_line_width of the frame
    width. Counted and measured from the timeline (the user, 2026-10-29)."""
    base = float(st["size"])
    rule = st.get("short_text")
    res = {"size": base, "base_size": base, "texts_on_timeline": len(events)}
    if not rule:
        res["short_text"] = "off (config capcut.text_style.short_text is null)"
        return res
    short, max_words, max_width = float(rule["size"]), int(rule["max_words_at_once"]), float(rule["max_line_width"])
    res["short_text"] = {"size": short, "max_words_at_once": max_words, "max_line_width": max_width}
    if not events:
        return res
    peak, at = 0, 0.0
    for e in events:
        n = sum(len(x["text"].split()) for x in events if x["start"] <= e["start"] < x["end"])
        if n > peak:
            peak, at = n, e["start"]
    try:
        widest = max(((_line_width_frac(e["text"], short, font_path, e["scale"]), e["text"]) for e in events), key=lambda w: w[0])
    except Exception as ex:   # the font cannot be measured: the house size stays
        res.update({"words_at_once_max": peak, "measure_error": str(ex)[:200]})
        return res
    little, fits = peak <= max_words, widest[0] <= max_width
    res.update({"size": short if little and fits else base, "words_at_once_max": peak, "words_at_once_max_at_s": round(at, 2),
                "widest_line_at_short_size": round(widest[0], 3), "widest_text": widest[1],
                "why": (f"{peak} word(s) at most on screen at once ({'<=' if little else '>'} {max_words}); widest line "
                        f"{widest[0]:.0%} of the frame width at size {short:g} ({'<=' if fits else '>'} {max_width:.0%})")})
    return res


def _text_style_pass(d: Path, write: bool) -> dict:
    st = _house_text_style()
    font = _capcut_system_font() or (st.get("learned") or {}).get("font_path") or ""
    if not font:
        fail("CapCut's System font was not found (<LOCALAPPDATA>/CapCut/Apps/<version>/Resources/Font/SystemFont/en.ttf)", 1)
    paths = _draft_contents(d)
    contents = {p: json.loads(p.read_text(encoding="utf-8")) for p in paths}
    newest = max(paths, key=lambda p: p.stat().st_mtime)   # the copy written last (the save, or CapCut) holds the timeline
    sizing = _house_text_size(_timeline_texts(contents[newest]), st, font)
    files, changed_ids = [], set()
    for p in paths:
        content = contents[p]
        changed = [m.get("id") for m in content.get("materials", {}).get("texts", [])
                   if _house_text_material(m, st, font, sizing["size"])]
        changed_ids.update(changed)
        if changed and write:
            shutil.copyfile(p, p.with_name(p.name + ".textstyle.bak"))
            write_text(p, json.dumps(content, ensure_ascii=False))
        files.append({"file": str(p), "texts_off_style": len(changed)})
    return {"font": font, "size": sizing["size"], "sizing": sizing,
            "preset": "learned" if st.get("learned") else "default (not calibrated)",
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
    """House style for every CapCut text layer: font System, size 10 (11 when the video has only a little text: at most
    short_text.max_words_at_once words on screen at once and every line within short_text.max_line_width of the frame at
    11; one size per video, reported in `sizing`), and the user's chosen preset, stored in config.json
    (capcut.text_style.learned; locked). Rewrites every text material of the draft (root and nested timeline copies);
    capcut-repair runs it before register/sync. --check only reports. --learn copies the exact preset fields from a
    text the user styled once in CapCut; a locked preset needs --replace."""
    d = Path(a.draft)
    if not (d / "draft_content.json").is_file():
        fail(f"not a CapCut draft (no draft_content.json): {d}", 2)
    if a.learn:
        out({"ok": True, **_learn_text_style(d, a.text, a.replace)})
    if not a.check and ((d / ".locked").exists() or _capcut_running()):
        fail("CapCut is running: close it, then run this again", 3)
    res = _text_style_pass(d, write=not a.check)
    out({"ok": True, "draft": str(d), **res}, 1 if a.check and res["texts_off_style"] else 0)



def seam_profile(video, at: float, fps: float, half: float = 0.5, size=(72, 128)) -> dict:
    """Per-frame mean luma and frame-to-frame mean absolute difference of `video` from at-half to at+half, at the video's own frame
    rate (frames downscaled to `size`, grey). Numbers for the agent to read before a cut is trusted: a flash, a dissolve or a held
    frame shows as a luma ramp or a difference run; nothing is judged here. rows = [t, luma, diff]."""
    ff = find_tool("ffmpeg")
    W, H = size
    t0 = max(0.0, at - half)
    cp = subprocess.run([ff, "-v", "error", "-nostdin", "-ss", f"{t0:.4f}", "-to", f"{at + half:.4f}", "-i", str(video),
                         "-vf", f"scale={W}:{H},format=gray", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, timeout=300)
    raw = cp.stdout
    n = len(raw) // (W * H)
    rows, prev = [], None
    for i in range(n):
        fr = raw[i * W * H:(i + 1) * W * H]
        luma = sum(fr) / (W * H)
        diff = (sum(abs(x - y) for x, y in zip(fr, prev)) / (W * H)) if prev is not None else 0.0
        rows.append([round(t0 + i / (fps or 30.0), 3), round(luma, 1), round(diff, 1)])
        prev = fr
    if not rows:
        return {"at": at, "frames": 0, "error": cp.stderr.decode("utf-8", "replace")[-200:] or "no frames decoded"}
    lum = [r[1] for r in rows]
    dif = [r[2] for r in rows[1:]] or [0.0]
    k = max(range(1, len(rows)), key=lambda j: rows[j][2]) if len(rows) > 1 else 0
    return {"at": at, "frames": n, "from": rows[0][0], "to": rows[-1][0], "luma_min": min(lum), "luma_max": max(lum),
            "luma_at_cut": next((r[1] for r in rows if r[0] >= at - 1e-6), rows[-1][1]), "diff_max": max(dif), "diff_max_at": rows[k][0],
            "rows": rows}


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
    fps = info.get("fps") or 30.0
    seams = []
    for ins in inserts:
        for edge, t in (("in", ins["source_in"]), ("out", ins["source_out"])):
            seams.append({"insert": ins["insert"], "edge": edge, **seam_profile(a.video, t, fps)})
    mp = {"source": str(a.video), "source_duration": round(dur, 3), "own_duration": o.get("duration_s"),
          "expected_own_duration": round(dur - removed, 3), "inserts": inserts,
          "own": str(own), "own_silent": str(silent), "seams": seams,
          "seams_note": "per cut point of the SOURCE, 0.5 s either side at its own frame rate: rows = [t, mean luma 0-255, mean abs frame difference]; "
                        "a luma ramp or a difference run across the cut means the cut sits inside a flash, a dissolve or a held frame (read it, then decide)"}
    write_json(od / "map.json", mp)
    out({"ok": True, **{k: v for k, v in mp.items() if k != "seams"}, "seams": [{k: v for k, v in s.items() if k != "rows"} for s in seams],
         "seam_rows_in": str(od / "map.json"), "map": str(od / "map.json")})


# --------------------------------------------------------------------------- submission ledger (anti-duplicate)

LEDGER_OPEN = {"pending", "submitted", "unknown"}          # outcome not final yet → blocks new submissions
LEDGER_DONE_OK = {"completed", "accepted"}                  # a finished, usable job for this exact request


def cmd_seams(a):
    """Seam profile of any video at the given times (or at the split points of a strip-inserts map.json): per-frame luma and frame
    difference 0.5 s either side, numbers only. For a prepared source: `--map <own/map.json>` reads split_at (the own timeline) and,
    with `--source`, source_in/source_out of the original."""
    info = media_summary(a.video)
    fps = info.get("fps") or 30.0
    times = []
    if a.at:
        times += [("at", t) for t in _parse_times(a.at)]
    if a.map:
        mp = json.loads(Path(a.map).read_text(encoding="utf-8"))
        for ins in mp.get("inserts", []):
            if a.source:
                times += [(f"insert {ins['insert']} in", ins["source_in"]), (f"insert {ins['insert']} out", ins["source_out"])]
            else:
                times.append((f"insert {ins['insert']} split", ins["split_at"]))
    if not times:
        fail("seams needs --at <seconds,…> or --map <map.json>", 2)
    res = [{"label": lab, **seam_profile(a.video, t, fps, a.half)} for lab, t in times]
    if a.out:
        write_json(Path(a.out), {"video": str(a.video), "fps": fps, "seams": res})
    out({"ok": True, "video": str(a.video), "fps": fps, "seams": [{k: v for k, v in s.items() if k != "rows" or a.rows} for s in res],
         "out": a.out, "note": "rows = [t, mean luma 0-255, mean abs frame difference]; a luma ramp or a difference run across the cut means a flash, a dissolve or a held frame at the cut (read it, then decide)"})


def _fingerprint(req: dict) -> str:
    params = dict(req.get("params", req))
    params.pop("get_cost", None)
    blob = json.dumps(params, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:20]


def _lane(video) -> str:
    """Ledger lane = the video number: '03', '03-c2' (clip 2) and '03-frame' share lane '03'."""
    return str(video).split("-")[0]


def cmd_ledger(a):
    """Record of every paid Higgsfield generation (generate_video, and generate_image for start frames), kept so that parallel production
    agents can see each other. state.json is written under a lock. The ledger RECORDS and REPORTS; it never refuses and never decides: whether to
    submit is the agent's decision, taken from the production rules of the mode.
    begin  : records a 'pending' entry (call it immediately BEFORE the generation call) and reports what the ledger already holds that bears on
             it, as facts: `conflicts` lists, with the entries involved, an open submission (pending/submitted/unknown) in this video's lane, the
             number of open submissions in the run against `production.max_parallel_jobs` (config, default 5; `--max-open` overrides), the
             number of times this exact request (the same fingerprint) failed, and a finished job (completed/accepted) of this exact request.
             An agent that decides not to submit records that with `set --status superseded --note "why"`, which also frees the lane.
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
        cap = a.max_open or int(cfg_get("production.max_parallel_jobs", 5))
        failed = [e for e in led if e["fingerprint"] == fp and e["status"] == "failed"]
        dup = [e for e in led if e["fingerprint"] == fp and e["status"] in LEDGER_DONE_OK]
        conflicts = []
        if open_lane:
            conflicts.append({"what": "an open submission in this video's lane", "entries": open_lane})
        if len(open_all) >= cap:
            conflicts.append({"what": "submissions in flight in this run against the cap", "open": len(open_all), "cap": cap})
        if failed:
            conflicts.append({"what": "this exact request failed before", "times": len(failed), "entries": failed})
        if dup:
            conflicts.append({"what": "this exact request already produced a finished job", "entry": dup[-1]})
        entry = {"video": a.video, "lane": lane, "attempt": a.attempt, "fingerprint": fp, "status": "pending",
                 "job_id": None, "model": (req.get("params", req)).get("model"),
                 "request_file": str(Path(a.request).resolve()), "created": now_iso(), "history": [],
                 "conflicts_seen": [c["what"] for c in conflicts]}
        led.append(entry)
        st["updated"] = now_iso()
        write_json(p, st)
        out({"ok": True, "recorded": True, "fingerprint": fp, "entry": entry, "conflicts": conflicts,
             "open_in_run": len(open_all) + 1, "cap": cap,
             "note": "recorded as pending, nothing was refused: whether to submit is your decision from the conflicts listed, under the mode's production rules "
                     "(one job in flight per video; not past the cap; not the same request again once it produced a finished job; diagnose before another attempt). "
                     "If you decide not to submit, record it: ledger set --fingerprint ... --status superseded --note \"why\""})
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
    with the numbering and the pinned ids. Live catalog ids (from models_explore) mark availability and add
    models that have no guide yet. It does not pick a model: which ones to offer is the agent's decision."""
    idx = json.loads((AWL_HOME / "models" / "index.json").read_text(encoding="utf-8"))
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
    out({"ok": True, "count": len(rows), "pinned": [r["id"] for r in rows if r["star"]],
         "numbers": {str(r["n"]): r["id"] for r in rows}, "unavailable": unavailable})


def cmd_model_entry(a):
    """Print one model's entry of models/index.json with its guide path and section folder, so the 40 KB index is never
    read whole. An id with no guide returns the fallback guide."""
    idx = json.loads((AWL_HOME / "models" / "index.json").read_text(encoding="utf-8"))
    e = idx["models"].get(a.id)
    if e is None:
        fail(f"unknown model id {a.id}", known=sorted(idx["models"]))
    guide = e.get("guide") or idx.get("fallback_guide")
    g = AWL_HOME / guide
    sec = g.with_suffix("")
    out({"ok": True, "id": a.id, "entry": e, "guide": guide, "guide_exists": g.is_file(),
         "sections_dir": str(sec).replace("\\", "/") if sec.is_dir() else None,
         "higgsfield_guide": idx.get("higgsfield_guide"), "fixed_output": idx.get("fixed_output")})


# --------------------------------------------------------------------------- CLI

def _audio_profile(src: Path, dst: Path, transcript=None, cuts_path=None):
    """Sound-design measurements of one reference: what sits under and around the speech, so that the sound can be understood and, in Create, matched or
    reused. Measured with librosa (no listening), as NUMBERS and no verdict:
    - speech share (from the transcript) and the audible share outside it;
    - the harmonic share of the sound outside the speech (high = tonal, music-like; low = noise, percussion, ambience);
    - tempo and beat strength;
    - spectral flatness (tonal or noise-like) and the strongest frequency with how steady it is (one steady tone, such as a beep, or not);
    - energy per second, and the mean of the first and the last third of it;
    - "hits" (strong transients: stings, booms, whooshes) and whether they land on a cut.
    Whether there is a music bed, what role the sound plays (dramatic, comic, suspense, hype) and whether it could be reused are the agent's judgement from
    these numbers, the transcript and the picture. Writes dst (JSON).
    Returns (profile | None, error | None)."""
    try:
        import numpy as np
        import librosa
    except ImportError:
        return None, "librosa and numpy are required for audio-profile"
    dst.parent.mkdir(parents=True, exist_ok=True)
    wav = dst.with_suffix(".22k.wav")
    cp = run([find_tool("ffmpeg"), "-nostdin", "-y", "-loglevel", "error", "-i", str(src), "-vn", "-ac", "1",
              "-ar", "22050", str(wav)], timeout=900)
    if cp.returncode != 0 or not wav.exists():
        return None, "could not decode the audio: " + cp.stderr[-400:]
    y, sr = librosa.load(str(wav), sr=22050, mono=True)
    wav.unlink(missing_ok=True)
    dur = len(y) / sr if sr else 0
    if dur < 0.5 or not np.any(y):
        prof = {"ok": True, "format": 2, "file": str(src), "duration_s": round(dur, 2), "silent": True}
        write_json(dst, prof)
        return prof, None
    hop = 512
    speech = []
    speech_known = bool(transcript)            # no transcript named: the caller did not ask for a speech share
    if transcript:
        tp = Path(transcript)
        if not tp.exists():
            speech_known = False               # frames only: no transcript file exists; the speech share is unknown, not zero
        else:
            tj = json.loads(tp.read_text(encoding="utf-8"))
            if tj.get("ingested") is False:
                speech_known = False
            speech = [(float(s.get("start", 0)), float(s.get("end", 0))) for s in tj.get("segments", [])
                      if s.get("end") is not None]
    cuts = []
    if cuts_path and Path(cuts_path).exists():
        cuts = [float(c["t"]) for c in json.loads(Path(cuts_path).read_text(encoding="utf-8")).get("cuts", [])]
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
    first, last = (statistics.mean(per_s[:q]), statistics.mean(per_s[-q:])) if per_s else (None, None)
    centroid = float(np.median(librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop)))
    # tonal or noisy, and is it one steady tone: the median spectral flatness (near 0 = tonal, near 1 = noise-like) and the median frequency of the
    # strongest spectral peak with the share of audible frames within 3 % of it (a share near 1 = one steady tone, such as a beep)
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop))
    flat = librosa.feature.spectral_flatness(S=S)[0]
    pk_hz = librosa.fft_frequencies(sr=sr, n_fft=2048)[np.argmax(S, axis=0)]
    m_len = min(len(audible), flat.shape[0], pk_hz.shape[0])
    sel = audible[:m_len]
    if sel.any():
        flat_med = float(np.median(flat[:m_len][sel]))
        pk_med = float(np.median(pk_hz[:m_len][sel]))
        pk_steady = float(np.mean(np.abs(pk_hz[:m_len][sel] - pk_med) <= 0.03 * max(pk_med, 1.0)))
    else:
        flat_med = pk_med = pk_steady = None
    prof = {"ok": True, "format": 2, "file": str(src), "duration_s": round(dur, 2),
            "speech_share": round(speech_share, 2) if speech_known else None, "non_speech_audible_share": round(nonspeech_share, 2),
            "speech_note": None if speech_known else ("audio not ingested (frames only): the speech share is not measured; the shares below treat every audible second as non-speech"
                                                      if transcript else "no transcript was given: the speech share is not measured"),
            "harmonic_ratio_non_speech": None if harm_ratio is None else round(harm_ratio, 2),
            "tempo_bpm": round(tempo, 1), "beat_strength": round(pulse, 2),
            "energy_db_per_s": per_s, "energy_first_third_db": None if first is None else round(first, 1),
            "energy_last_third_db": None if last is None else round(last, 1),
            "energy_change_db": None if first is None else round(last - first, 1),
            "hits": sorted(hits, key=lambda h: -h["strength"])[:12], "brightness_hz": round(centroid),
            "spectral_flatness_median": None if flat_med is None else round(flat_med, 3),
            "peak_frequency_hz_median": None if pk_med is None else round(pk_med),
            "peak_frequency_steady_share": None if pk_steady is None else round(pk_steady, 2),
            "note": "measured numbers, not listening, and no verdict: whether there is a music bed, what role the sound plays (dramatic, comic, suspense, hype ...) "
                    "and whether it could be reused (rights still apply) are for the agent to decide from these numbers, the transcript and the picture"}
    write_json(dst, prof)
    return prof, None


# --------------------------------------------------------------------------- own voiceover (contract item 31)

VO_MODES = ("on-camera", "off-screen")
VO_SOURCES = ("elevenlabs", "file")
VO_RATE = 100                                       # loudness-curve frames per second (10 ms hop over 25 ms windows)
_VO_TAG = re.compile(r"\[[^\[\]\n]{1,60}\]")        # an ElevenLabs audio tag: [excited], [Scottish accent], [laughs softly]


def _vo_key(video) -> str:
    """'1' -> '01', '01-c2' -> '01-c2'; anything else stops (exit 2)."""
    m = re.match(r"^\s*(\d{1,3})(?:-(c\d+))?\s*$", str(video or ""))
    if not m:
        fail(f"--video must be NN or NN-cK, got {video!r}", 2)
    return f"{int(m.group(1)):02d}" + (f"-{m.group(2)}" if m.group(2) else "")


def _vo_curve(path):
    """Loudness of a file's first audio stream, mono 16 kHz: (dBFS per 10 ms frame over 25 ms windows, as a numpy array; duration in s)."""
    import numpy as np
    cp = subprocess.run([find_tool("ffmpeg"), "-hide_banner", "-loglevel", "error", "-nostdin", "-i", str(path), "-map", "0:a:0",
                         "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True, timeout=900)
    if cp.returncode != 0:
        raise RuntimeError(f"no decodable audio stream in {path}: {cp.stderr.decode('utf-8', 'replace')[-300:]}")
    x = np.frombuffer(cp.stdout, dtype=np.float32).astype(np.float64)
    hop, win = 16000 // VO_RATE, 400
    n = (len(x) - win) // hop + 1 if len(x) >= win else 0
    if n < 8:
        raise RuntimeError(f"too little audio in {path} ({len(x) / 16000:.2f} s)")
    cs = np.concatenate([[0.0], np.cumsum(x * x)])
    st = np.arange(n) * hop
    rms = np.sqrt(np.maximum(cs[st + win] - cs[st], 0.0) / win)
    return 20.0 * np.log10(rms + 1e-9), round(len(x) / 16000.0, 3)


def _vo_speech(curve, gap_s: float = 0.15, min_s: float = 0.08):
    """Speech in a loudness curve, as facts: (threshold dBFS, phrases, pauses, speech start s, speech end s). A frame counts as speech when it is
    louder than -50 dBFS and than the curve's loud level (its 95th percentile) minus 30 dB; a quieter gap shorter than gap_s joins two phrases,
    and a phrase shorter than min_s is left out."""
    import numpy as np
    thr = max(-50.0, float(np.percentile(curve, 95)) - 30.0)
    act = np.concatenate([[False], curve > thr, [False]])
    edges = np.flatnonzero(np.diff(act.astype(np.int8)))
    spans = [[int(edges[i]), int(edges[i + 1])] for i in range(0, len(edges) - 1, 2)]     # [first speech frame, last speech frame + 1)
    merged = []
    for s, e in spans:
        if merged and (s - merged[-1][1]) / VO_RATE < gap_s:
            merged[-1][1] = e
        else:
            merged.append([s, e])
    merged = [(s, e) for s, e in merged if (e - s) / VO_RATE >= min_s]
    phrases = [{"start": round(s / VO_RATE, 2), "end": round((e - 1) / VO_RATE + 0.025, 2)} for s, e in merged]
    pauses = [{"start": phrases[k]["end"], "end": phrases[k + 1]["start"], "s": round(phrases[k + 1]["start"] - phrases[k]["end"], 2)}
              for k in range(len(phrases) - 1)]
    return round(thr, 1), phrases, pauses, (phrases[0]["start"] if phrases else None), (phrases[-1]["end"] if phrases else None)


def _vo_shape(curve, thr: float):
    """The loudness above (speech threshold - 10 dB), lightly smoothed: the syllable rhythm two voices saying the same words share."""
    import numpy as np
    y = np.maximum(curve, thr - 10.0) - (thr - 10.0)
    return np.convolve(y, np.ones(3) / 3.0, mode="same")


def _vo_lufs(path):
    """Integrated loudness (LUFS) of a file's audio, by ffmpeg's ebur128 filter; None when it cannot be read."""
    cp = run([find_tool("ffmpeg"), "-hide_banner", "-nostdin", "-i", str(path), "-map", "0:a:0", "-af", "ebur128", "-f", "null", "-"], timeout=900)
    summ = cp.stderr[cp.stderr.rfind("Summary:"):] if "Summary:" in cp.stderr else ""
    m = re.search(r"I:\s*(-?[0-9.]+)\s*LUFS", summ)
    return float(m.group(1)) if m else None


def _vo_text(v):
    """--script: the text of an existing file, else the value itself (None when empty)."""
    if not v:
        return None
    try:
        if len(v) < 400 and Path(v).is_file():
            return Path(v).read_text(encoding="utf-8-sig", errors="replace").strip() or None
    except (OSError, ValueError):
        pass
    return v.strip() or None


def _vo_plot(vc, gc, off_s: float, dest: Path):
    """Two loudness curves on one time axis: the take (shifted by off_s) above, the generation's own sound below."""
    import numpy as np
    from PIL import Image, ImageDraw
    W, H, padx = 1200, 320, 50
    span = max(len(vc) / VO_RATE + max(off_s, 0.0), len(gc) / VO_RATE, 1.0)
    img = Image.new("RGB", (W, H), (18, 18, 18))
    d, fnt = ImageDraw.Draw(img), _font(14)
    lane_h = (H - 40) // 2
    lanes = ((vc, off_s, (90, 220, 120), f"the take, shifted by {off_s:+.2f} s"), (gc, 0.0, (240, 160, 60), "the generation's own sound"))
    for li, (c, sh, col, lab) in enumerate(lanes):
        y0 = 8 + li * lane_h
        d.text((padx, y0), lab, fill=(230, 230, 230), font=fnt)
        lo, hi = float(np.percentile(c, 5)), float(np.percentile(c, 99.5))
        rng = max(hi - lo, 1e-6)
        pts = []
        for i in range(0, len(c), 2):
            t = i / VO_RATE + sh
            if 0.0 <= t <= span:
                pts.append((padx + (W - 2 * padx) * t / span,
                            y0 + lane_h - 6 - (lane_h - 30) * min(max((float(c[i]) - lo) / rng, 0.0), 1.0)))
        if len(pts) > 1:
            d.line(pts, fill=col, width=2)
    for s in range(int(span) + 1):
        x = padx + (W - 2 * padx) * s / span
        d.line((x, H - 30, x, H - 24), fill=(160, 160, 160))
        d.text((x - 4, H - 22), f"{s}s", fill=(160, 160, 160), font=fnt)
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest)
    return dest


def _vo_mcp_base():
    """ELEVENLABS_MCP_BASE_PATH as the ElevenLabs MCP server itself is configured (~/.claude.json -> mcpServers.elevenlabs.env), or None.
    Only that one key is read; the API key beside it never is."""
    try:
        cj = json.loads((Path.home() / ".claude.json").read_text(encoding="utf-8"))
        return ((((cj.get("mcpServers") or {}).get("elevenlabs") or {}).get("env") or {}).get("ELEVENLABS_MCP_BASE_PATH")) or None
    except (OSError, ValueError, AttributeError):
        return None


def _vo_outdir(a):
    if not a.run:
        fail("outdir needs --run", 2)
    rd, _st = _state_of(a.run)
    env = os.environ.get("ELEVENLABS_MCP_BASE_PATH")
    cfg = None if (a.base or env) else _vo_mcp_base()      # the server's own setting, when this shell has none
    base = Path(a.base) if a.base else (Path(env) if env else (Path(cfg).expanduser() if cfg else Path.home() / "Desktop"))
    d = base / "awl-voiceover" / rd.name
    d.mkdir(parents=True, exist_ok=True)
    out({"ok": True, "dir": str(d), "base": str(base),
         "base_from": "--base" if a.base else ("ELEVENLABS_MCP_BASE_PATH" if env else
                                              ("the elevenlabs server's env in ~/.claude.json" if cfg else "the default (~/Desktop)")),
         "note": "pass this folder as text_to_speech's output_directory (the ElevenLabs MCP writes only under its base path), then copy each take "
                 "into the run with `voiceover record`"})


def _vo_record(a):
    if not (a.run and a.video and a.file):
        fail("record needs --run, --video and --file", 2)
    rd, _st = _state_of(a.run)
    key = _vo_key(a.video)
    src = Path(a.file)
    if not src.is_file():
        fail(f"--file not found: {src}", 2)
    if a.attempt < 1:
        fail("--attempt starts at 1", 2)
    settings = None
    if a.settings:
        try:
            settings = json.loads(a.settings)
        except ValueError as e:
            fail(f"--settings is not JSON: {e}", 2)
    span = None
    if a.span:                              # a clip's part of one longer file (a user's own file over several clips): cut losslessly to WAV
        m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*$", a.span)
        if not m or float(m.group(1)) >= float(m.group(2)):
            fail(f"--span must be START-END in seconds with START < END, got {a.span!r}", 2)
        span = [float(m.group(1)), float(m.group(2))]
    vdir = rd / "30-assets" / "voiceover"
    vdir.mkdir(parents=True, exist_ok=True)
    dst = vdir / f"video-{key}-a{a.attempt}{'.wav' if span else (src.suffix or '.mp3').lower()}"
    new = src
    if span:
        new = vdir / f"_span-{key}-a{a.attempt}.wav"
        cp = run([find_tool("ffmpeg"), "-hide_banner", "-loglevel", "error", "-nostdin", "-y", "-i", str(src), "-ss", f"{span[0]:.3f}",
                  "-to", f"{span[1]:.3f}", "-map", "0:a:0", "-c:a", "pcm_s16le", str(new)], timeout=900)
        if cp.returncode != 0 or not new.is_file():
            fail("--span cut failed: " + cp.stderr[-400:], 1)
    same = dst.exists() and dst.resolve() == new.resolve()
    kept = None
    if dst.exists() and not same and quick_hash(dst) != quick_hash(new):   # the same attempt recorded again from another file: the earlier one is kept beside it
        kept = dst.with_name(f"{dst.stem}.prev-{time.strftime('%Y%m%d-%H%M%S')}{dst.suffix}")
        dst.replace(kept)
        if dst.with_suffix(".json").exists():
            dst.with_suffix(".json").replace(kept.with_suffix(".json"))
    if span:
        new.replace(dst)
    elif not same:
        shutil.copy2(src, dst)
    info = media_summary(dst)
    if not info.get("has_audio"):
        fail(f"no audio stream in {dst}", 2)
    try:
        curve, dur = _vo_curve(dst)
    except RuntimeError as e:
        fail(str(e), 1)
    thr, phrases, pauses, s0, s1 = _vo_speech(curve)
    script, script_source, transcript = _vo_text(a.script), None, None
    if script:
        script_source = "given"
    elif a.transcribe:                      # a client's own voiceover file: its words, by local speech-to-text (not the references' audio, item 24)
        work = vdir / f"_transcribe-{key}"
        work.mkdir(parents=True, exist_ok=True)
        wav = work / "take-16k.wav"
        run([find_tool("ffmpeg"), "-hide_banner", "-loglevel", "error", "-nostdin", "-y", "-i", str(dst), "-map", "0:a:0", "-ac", "1",
             "-ar", "16000", "-c:a", "pcm_s16le", str(wav)], check=True, timeout=900)
        transcript = transcribe(str(wav), work, a.whisper_model, a.language or "auto")
        script = " ".join(s.get("text", "") for s in transcript.get("segments", [])).strip() or None
        script_source = f"transcribed ({transcript.get('engine') or 'no engine'}{(' ' + str(transcript['model'])) if transcript.get('model') else ''})"
        shutil.rmtree(work, ignore_errors=True)
    spoken = " ".join(_VO_TAG.sub(" ", script).split()) if script else None
    words = len(spoken.split()) if spoken else 0
    speech_s = round(s1 - s0, 2) if s0 is not None else 0.0
    side = {"ok": True, "video": key, "attempt": a.attempt, "source": a.source, "mode": a.mode, "file": str(dst), "source_file": str(src), "span_s": span,
            "sha1_16": quick_hash(dst), "duration_s": dur, "codec": info.get("audio_codec"), "sample_rate": info.get("audio_rate"),
            "channels": info.get("audio_channels"), "speech_threshold_dbfs": thr, "speech_start_s": s0, "speech_end_s": s1, "speech_s": speech_s,
            "trailing_quiet_s": round(dur - s1, 2) if s1 is not None else None, "phrases": phrases, "pauses": pauses,
            "integrated_lufs": _vo_lufs(dst), "script": script, "script_source": script_source,
            "tags": _VO_TAG.findall(script) if script else [], "spoken_text": spoken, "spoken_words": words,
            "chars_sent": len(script) if (script and a.source == "elevenlabs") else None,
            "words_per_speech_s": round(words / speech_s, 2) if words and speech_s > 0 else None,
            "voice_id": a.voice_id, "voice_name": a.voice_name, "model": a.model, "language": a.language, "preference": a.preference,
            "settings": settings, "recorded": now_iso(),
            "note": "measured facts and the words as given or transcribed; whether the take fits the plan, sounds right or is pronounced right "
                    "is not judged here (no one listened)"}
    if transcript is not None:
        side["transcript_segments"] = transcript.get("segments", [])
    write_json(dst.with_suffix(".json"), side)
    rec = {"file": str(dst), "sidecar": str(dst.with_suffix(".json")), "attempt": a.attempt, "source": a.source, "mode": a.mode,
           "duration_s": dur, "speech_start_s": s0, "speech_end_s": s1, "phrases": len(phrases), "recorded": side["recorded"]}
    p = rd / "state.json"
    with FileLock(p.with_name("state.json.lock")):
        st = json.loads(p.read_text(encoding="utf-8"))
        vo = st.get("voiceover") if isinstance(st.get("voiceover"), dict) else {}
        if not isinstance(vo.get("files"), dict):
            vo["files"] = {}
        vo["files"][key] = rec
        st["voiceover"] = vo
        st["updated"] = now_iso()
        write_json(p, st)
    res = {k: v for k, v in side.items() if k != "transcript_segments"}
    res.update({"sidecar": str(dst.with_suffix(".json")), "state_key": f"voiceover.files.{key}", "previous_kept_as": str(kept) if kept else None,
                "voiceover_enabled_in_state": vo.get("enabled")})
    out(res)


def _vo_align(a):
    import numpy as np
    if not (a.generated and a.voiceover and a.out):
        fail("align needs --generated, --voiceover and --out", 2)
    gen, vo = Path(a.generated), Path(a.voiceover)
    for p in (gen, vo):
        if not p.is_file():
            fail(f"file not found: {p}", 2)
    if not media_summary(gen).get("has_audio"):
        fail("the generated file has no audio stream: there is no model speech to align the take against (an off-screen take needs no alignment)", 1)
    try:
        vc, vdur = _vo_curve(vo)
        gc, gdur = _vo_curve(gen)
    except RuntimeError as e:
        fail(str(e), 1)
    vthr, vph, _vpa, vs0, vs1 = _vo_speech(vc)
    gthr, gph, _gpa, gs0, gs1 = _vo_speech(gc)
    vx, gx = _vo_shape(vc, vthr), _vo_shape(gc, gthr)
    max_k = max(1, int(round(a.max_lag * VO_RATE)))
    g_k, g_c = _best_lag(vx, gx, max_k, min_len=VO_RATE)
    g_off = round((g_k or 0) / VO_RATE, 3)
    wn = max(8, int(round(a.window * VO_RATE)))
    v_std = float(vx.std()) or 1e-6
    windows = []
    for i0 in range(0, max(1, len(vx) - wn + 1), VO_RATE):
        seg = vx[i0:i0 + wn]
        k, c = _best_lag(vx, gx, max_k, i0, i0 + wn, min_len=max(8, wn // 2))
        windows.append({"t": round((i0 + wn / 2) / VO_RATE, 2), "offset_s": None if k is None else round(k / VO_RATE, 3),
                        "corr": None if k is None else round(c, 3), "voice_ratio": round(float(seg.std()) / v_std, 2)})
    # the summary uses the windows that pass the caller's two filters (--min-corr, --min-voice); every window is listed in vo-align.json
    rel = [w for w in windows if w["offset_s"] is not None and w["corr"] >= a.min_corr and w["voice_ratio"] >= a.min_voice]
    lags = [w["offset_s"] for w in rel]
    drift = None
    if len(rel) >= 3:
        ts, ls = np.array([w["t"] for w in rel]), np.array(lags)
        if float(ts.var()) > 0:
            drift = round(float(((ts - ts.mean()) * (ls - ls.mean())).mean() / ts.var()) * 10.0, 3)
    od = Path(a.out)
    od.mkdir(parents=True, exist_ok=True)
    png = _vo_plot(vc, gc, g_off, od / "vo-align.png")
    end_on = round(vs1 + g_off, 2) if vs1 is not None else None
    res = {"ok": True, "generated": str(gen), "voiceover": str(vo), "generated_s": gdur, "voiceover_s": vdur,
           "global_offset_s": g_off, "global_corr": None if g_c is None else round(g_c, 3),
           "filters": {"min_corr": a.min_corr, "min_voice_ratio": a.min_voice}, "windows_used": len(rel), "windows_total": len(windows),
           "median_window_offset_s": round(float(np.median(lags)), 3) if lags else None,
           "window_spread_s": round(max(lags) - min(lags), 3) if lags else None, "drift_s_per_10s": drift, "tolerance_s": a.tol,
           "windows_off_global": [{"t": w["t"], "offset_s": w["offset_s"]} for w in rel if abs(w["offset_s"] - g_off) > a.tol][:12],
           "voiceover_speech": {"start_s": vs0, "end_s": vs1, "phrases": len(vph)},
           "generated_speech": {"start_s": gs0, "end_s": gs1, "phrases": len(gph)},
           "voiceover_speech_end_on_generated_s": end_on,
           "voiceover_overrun_s": round(max(0.0, end_on - gdur), 2) if end_on is not None else None,
           "plot": str(png), "windows_file": str(od / "vo-align.json"),
           "note": "measurements only, no verdict (every window is in windows_file); a positive offset = the file's speech comes later than "
                   "the take (delay the take by that much when mixing)"}
    (od / "vo-align.json").write_text(json.dumps({**res, "windows": windows}, indent=1), encoding="utf-8")
    out(res)


def _vo_mix(a):
    if not (a.picture and a.voiceover and a.out):
        fail("mix needs --picture, --voiceover and --out", 2)
    pic, vo, dst = Path(a.picture), Path(a.voiceover), Path(a.out)
    for p in (pic, vo):
        if not p.is_file():
            fail(f"file not found: {p}", 2)
    if not 0.5 <= a.tempo <= 2.0:
        fail("--tempo must be between 0.5 and 2.0", 2)
    pi = media_summary(pic)
    if not pi.get("has_video"):
        fail(f"no video stream in {pic}", 2)
    dur = pi.get("duration_s") or 0.0
    if dur <= 0:
        fail(f"no duration for {pic}", 1)
    try:
        vc, vdur = _vo_curve(vo)
    except RuntimeError as e:
        fail(str(e), 1)
    _thr, _ph, _pa, vs0, vs1 = _vo_speech(vc)
    off = a.offset or 0.0
    chain = [f"atempo={a.tempo:.4f}"] if abs(a.tempo - 1.0) > 1e-6 else []
    if off > 0.0005:
        chain.append(f"adelay={int(round(off * 1000))}:all=1")
    elif off < -0.0005:
        chain += [f"atrim=start={abs(off):.4f}", "asetpts=PTS-STARTPTS"]
    chain += [f"volume={a.vo_gain:.3f}", f"apad=whole_dur={dur:.3f}", f"atrim=duration={dur:.3f}"]
    vo_chain = ",".join(chain)
    keep = a.bed == "keep" and bool(pi.get("has_audio"))
    if keep:
        fc = (f"[1:a:0]{vo_chain}[vo];[0:a:0]volume={a.bed_gain:.3f},apad=whole_dur={dur:.3f},atrim=duration={dur:.3f}[bed];"
              f"[bed][vo]amix=inputs=2:duration=longest:normalize=0[mix]")
        amap = "[mix]"
    else:
        fc, amap = f"[1:a:0]{vo_chain}[vo]", "[vo]"
    dst.parent.mkdir(parents=True, exist_ok=True)
    ff = find_tool("ffmpeg")
    cp = run([ff, "-nostdin", "-y", "-loglevel", "error", "-i", str(pic), "-i", str(vo), "-filter_complex", fc, "-map", "0:v:0",
              "-map", amap, "-t", f"{dur:.3f}", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", str(dst)], timeout=1800)
    if cp.returncode != 0:
        fail("mix failed: " + cp.stderr[-600:])
    track = dst.with_name(dst.stem + ".vo-track.wav")
    cp2 = run([ff, "-nostdin", "-y", "-loglevel", "error", "-i", str(vo), "-af", vo_chain, "-t", f"{dur:.3f}", "-ar", "48000",
               "-c:a", "pcm_s16le", str(track)], timeout=900)
    o = media_summary(dst)
    sp_start = (vs0 / a.tempo + off) if vs0 is not None else None
    sp_end = (vs1 / a.tempo + off) if vs1 is not None else None
    facts = {"has_video": bool(o.get("has_video")), "has_audio": bool(o.get("has_audio")), "duration_s": o.get("duration_s"), "picture_s": dur,
             "bed": "kept" if keep else ("muted" if a.bed == "mute" else "none: the picture has no audio stream"),
             "bed_gain": a.bed_gain if keep else None, "vo_gain": a.vo_gain, "tempo": a.tempo, "offset_s": off, "vo_s": vdur,
             "vo_start_on_picture_s": round(max(0.0, off), 3), "vo_end_on_picture_s": round(off + vdur / a.tempo, 3),
             "vo_speech_start_on_picture_s": None if sp_start is None else round(sp_start, 3),
             "vo_speech_end_on_picture_s": None if sp_end is None else round(sp_end, 3),
             "vo_speech_head_cut_s": None if sp_start is None else round(max(0.0, -sp_start), 3),
             "vo_speech_cut_s": None if sp_end is None else round(max(0.0, sp_end - dur), 3)}
    out({"ok": True, "file": str(dst), "track": str(track) if cp2.returncode == 0 else None, "facts": facts,
         "note": "facts of the mix, no verdict: whether the voice lands on the mouths and is heard whole is for the agent to check (X9)"})


def cmd_effort(a):
    """Show or set the run's effort level (contract item 33). --level takes the level's table; custom values replace single settings
    and are held to the floors (a check would lose what it needs below them) and the ceilings; nothing else is decided here."""
    rd, st = _state_of(a.run)
    custom = {k: getattr(a, k) for k in EFFORT_KEYS if getattr(a, k, None) is not None}
    cur = effort_of_state(st)
    if not a.level and not custom:
        if cur.get("pending"):
            fail(EFFORT_HELP, 2)
        out({"ok": True, "run": rd.name, "effort": cur, "levels": EFFORT_LEVELS, "bounds": EFFORT_BOUNDS})
    if cur.get("pending") and not a.level:
        fail("this run has no effort level yet: give --level (the level nearest the user's numbers) with the custom values", 2)
    level = a.level or (cur["level"] if cur["level"] in EFFORT_LEVELS else "max")
    eff = dict(EFFORT_LEVELS[level]) if a.level else {k: cur[k] for k in EFFORT_KEYS}
    held = []
    for k, v in custom.items():
        nv, why = _effort_clamp(k, v)
        if why:
            held.append({"key": k, "asked": v, "set": nv, "held_to": why})
        eff[k] = nv
    if eff["analysis_dense_fps"] < eff["analysis_fps"]:
        eff["analysis_dense_fps"] = eff["analysis_fps"]
    eff["level"] = level
    eff["custom"] = sorted(custom) or None
    eff["set_at"] = now_iso()
    p = rd / "state.json"
    with FileLock(p.with_name("state.json.lock")):
        st = json.loads(p.read_text(encoding="utf-8"))
        st["effort"] = eff
        st["updated"] = now_iso()
        write_json(p, st)
    out({"ok": True, "run": rd.name, "effort": eff, "held_to_bounds": held,
         "note": "prep-all reads the sampling, the produce phase the agents at once and the pilot; QC and Loupe never change (reference/effort.md)"})


def cmd_voiceover(a):
    """Own voiceover (contract item 31): outdir | record | align | mix. It measures, records and mixes; it never judges."""
    {"outdir": _vo_outdir, "record": _vo_record, "align": _vo_align, "mix": _vo_mix}[a.action](a)


# --------------------------------------------------------------------------- Static (Analyze → Static, contract item 36)
# Narrated still-image videos: stills from the OpenAI Images API, from a local FLUX 3 Image Klein (static_images=klein) or the user's own
# files, the narration from a local Qwen3-TTS voice, an optional bed from a local ACE-Step 1.5, all joined by ffmpeg and in CapCut. No
# Higgsfield call and no Loupe call anywhere here.
# Every command gathers, records and measures; the agent decides (contract item 25). The OpenAI key comes only from the environment
# (OPENAI_API_KEY): it is never printed, never written to a run, and scrubbed from every error text.

STATIC_IMG_NAME = re.compile(r"(?i)(?:^|[^a-z0-9])v(\d{1,3})[-_ ]?i(\d{1,3})(?:[^0-9]|$)")
STATIC_MOTIONS = ("zoom-in", "zoom-out", "pan-left", "pan-right", "pan-up", "pan-down", "none")
STATIC_TRANSITIONS = {"cut": "fade", "fade": "fade", "dissolve": "dissolve", "fadeblack": "fadeblack", "fadewhite": "fadewhite",
                      "slideleft": "slideleft", "slideright": "slideright", "slideup": "slideup", "slidedown": "slidedown",
                      "smoothleft": "smoothleft", "smoothright": "smoothright", "circleopen": "circleopen", "zoomin": "zoomin"}
STATIC_LANG_ISO = {"english": "en", "spanish": "es", "german": "de", "italian": "it", "portuguese": "pt", "french": "fr",
                   "russian": "ru", "japanese": "ja", "korean": "ko", "chinese": "zh"}


def _scfg(key: str, default=None):
    return cfg_get(f"static.{key}", default)


def _sha1_file(p: Path) -> str:
    h = hashlib.sha1()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _oa_key() -> str:
    return (os.environ.get("OPENAI_API_KEY") or "").strip()


def _oa_base() -> str:
    return (os.environ.get("AWL_OPENAI_BASE_URL") or _scfg("images.api_base") or "https://api.openai.com/v1").rstrip("/")


def _scrub(text, key: str) -> str:
    s = str(text or "")
    return s.replace(key, "<OPENAI_API_KEY>") if key else s


def _oa_call(method: str, path: str, body, key: str, timeout: float) -> tuple:
    """(http status, parsed JSON or None, raw text with the key scrubbed) of one OpenAI API call. The key travels only in the
    Authorization header. A timeout or a dropped connection raises (the caller records the outcome as unknown)."""
    import urllib.error
    import urllib.request
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(_oa_base() + path, data=data, method=method,
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            status, raw = r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        status = e.code
        try:
            raw = e.read().decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            raw = ""
    try:
        js = json.loads(raw) if raw else None
    except ValueError:
        js = None
    return status, js, _scrub(raw, key)[:2000]


def _data_url(p: Path) -> str:
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(p.suffix.lower(), "image/png")
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode("ascii")


def _img_size(p: Path) -> list:
    try:
        from PIL import Image
        with Image.open(p) as im:
            return [im.width, im.height]
    except Exception:  # noqa: BLE001
        return []


def _img_cost(usage: dict) -> float | None:
    """An ESTIMATE in USD from the token usage the API returned and the prices in config.json -> static.images.prices_usd_per_1m (dated)."""
    if not isinstance(usage, dict) or not usage:
        return None
    pr = _scfg("images.prices_usd_per_1m", {}) or {}
    det = usage.get("input_tokens_details") or {}
    txt = det.get("text_tokens", usage.get("input_tokens", 0) if not det else 0) or 0
    img = det.get("image_tokens", 0) or 0
    outp = usage.get("output_tokens", 0) or 0
    try:
        return round(txt * float(pr.get("text_in", 0)) / 1e6 + img * float(pr.get("image_in", 0)) / 1e6
                     + outp * float(pr.get("image_out", 0)) / 1e6, 4)
    except (TypeError, ValueError):
        return None


def _img_where(rd: Path, nn: str, anchor: str | None) -> tuple:
    """(folder of the files, the record file, the record's key of this image) for a video's image or a character anchor."""
    if anchor:
        d = rd / "30-assets" / "characters"
        return d, d / "anchors.json"
    d = rd / "60-outputs" / f"video-{nn}" / "images"
    return d, d.parent / "images.json"


def _img_record_add(rec_p: Path, key: str, attempt: dict | None = None, use: str | None = None) -> dict:
    """Append an attempt to an image's record and/or set the file it uses, under a lock (images.json / anchors.json)."""
    rec_p.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(rec_p.with_name(rec_p.name + ".lock")):
        try:
            rec = json.loads(rec_p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            rec = {"images": {}}
        slot = rec.setdefault("images", {}).setdefault(key, {"attempts": []})
        if attempt:
            slot["attempts"].append(attempt)
        if use:
            slot["use"] = use
        write_json(rec_p, rec)
    return slot


def _img_ledger(rd: Path, action: str, **kw) -> dict:
    """The image calls in the run's ledger (state.json -> submissions), the same rows paid video generations keep, with kind 'image'
    and provider 'openai' (or 'klein', made on this PC). Records and reports; it never refuses."""
    p = rd / "state.json"
    with FileLock(p.with_name("state.json.lock")):
        st = json.loads(p.read_text(encoding="utf-8"))
        led = st.setdefault("submissions", [])
        if action == "begin":
            e = {"video": kw["video"], "lane": _lane(kw["video"]), "attempt": kw["attempt"], "fingerprint": kw["fp"], "status": "pending",
                 "job_id": None, "model": kw["model"], "request_file": kw["request_file"], "created": now_iso(), "history": [],
                 "conflicts_seen": [], "kind": "image", "provider": kw.get("provider") or "openai"}
            led.append(e)
        else:
            hits = [e for e in led if e.get("fingerprint") == kw["fp"] and e.get("kind") == "image"]
            if not hits:
                return {}
            e = hits[-1]
            e["history"].append({"at": now_iso(), "from": e["status"], "to": kw["status"], "note": kw.get("note")})
            e["status"] = kw["status"]
            if kw.get("job"):
                e["job_id"] = kw["job"]
        st["updated"] = now_iso()
        write_json(p, st)
    return e


def _img_generate(a):
    rd, st = _state_of(a.run)
    anchor = re.sub(r"[^A-Za-z0-9_-]+", "", a.anchor or "") or None
    nn = "00" if anchor else _cf_nn(a.video)
    if not anchor and (not a.video or not a.image):
        fail("generate needs --video NN and --image K (or --anchor ID for a character's anchor image)", 2)
    key_name = anchor or f"{int(a.image):02d}"
    prompt = (Path(a.prompt_file).read_text(encoding="utf-8") if a.prompt_file else (a.prompt or "")).strip()
    if not prompt:
        fail("generate needs --prompt-file (or --prompt)", 2)
    refs = [Path(r) for r in (a.ref or [])]
    missing = [str(r) for r in refs if not r.is_file()]
    if missing:
        fail("reference image(s) not found: " + "; ".join(missing), 2)
    engine = a.engine or ("klein" if st.get("static_images") == "klein" else "api")
    if engine == "klein":
        _img_generate_klein(a, rd, st, anchor, nn, key_name, prompt, refs)
    if len(refs) > 16:
        fail("the image API takes at most 16 reference images per request", 2)
    key = _oa_key()
    if not key:
        fail("OPENAI_API_KEY is not set in this environment: set it once on this PC (reference/static §9). Nothing was sent.", 2)
    model = a.model or _scfg("images.model", "gpt-image-2.5-sunburst")
    fmt = _static_fmt(st)
    size = a.size or fmt.get("image_size") or _scfg("images.size", "1088x1920")
    quality = a.quality or fmt.get("quality") or _scfg("images.quality", "high")
    params = {"model": model, "prompt": prompt, "size": size, "quality": quality, "n": 1, "output_format": "png",
              "refs": [{"file": str(r.resolve()), "sha1": _sha1_file(r)} for r in refs]}
    fp = _fingerprint({"params": params})
    folder, rec_p = _img_where(rd, nn, anchor)
    try:
        slot = (json.loads(rec_p.read_text(encoding="utf-8")).get("images") or {}).get(key_name) or {"attempts": []}
    except (OSError, ValueError):
        slot = {"attempts": []}
    done = [x for x in slot["attempts"] if x.get("fingerprint") == fp and x.get("status") == "completed" and Path(x.get("file") or "").is_file()]
    if done and not a.again:
        out({"ok": True, "reused": True, "file": done[-1]["file"], "attempt": done[-1]["attempt"], "fingerprint": fp,
             "note": "this exact request already made this image: nothing was sent (--again asks for a new draw of the same request)"})
    attempt = 1 + max([int(x.get("attempt") or 0) for x in slot["attempts"]] or [0])
    tag = f"{anchor}-a{attempt}" if anchor else f"i{key_name}-a{attempt}"
    reqf = rd / "50-requests" / (f"anchor-{anchor}-a{attempt}-image-request.json" if anchor else f"video-{nn}-i{key_name}-a{attempt}-image-request.json")
    write_json(reqf, {"video": nn, "image": key_name, "attempt": attempt, "kind": "image", "provider": "openai",
                      "endpoint": "edits" if refs else "generations", "params": params})
    _img_ledger(rd, "begin", video=nn, attempt=tag, fp=fp, model=model, request_file=str(reqf))
    body = {"model": model, "prompt": prompt, "size": size, "quality": quality, "n": 1, "output_format": "png"}
    if refs:
        body["images"] = [{"image_url": _data_url(r)} for r in refs]
    timeout = float(a.timeout or _scfg("images.timeout_s", 300))
    t0, tries, status, js, raw = time.time(), [], None, None, ""
    for wait in (0, 5, 20):          # only rate limits and server errors are sent again, twice at most; a refusal never is
        if wait:
            time.sleep(wait)
        try:
            status, js, raw = _oa_call("POST", "/images/edits" if refs else "/images/generations", body, key, timeout)
        except Exception as e:  # noqa: BLE001  (a timeout or a dropped connection: whether an image was made and billed is unknown)
            _img_ledger(rd, "set", fp=fp, status="unknown", note=type(e).__name__)
            _img_record_add(rec_p, key_name, {"attempt": attempt, "status": "unknown", "fingerprint": fp, "at": now_iso(),
                                              "request_file": str(reqf), "note": f"{type(e).__name__}: {_scrub(e, key)[:200]}"})
            fail(f"no answer from the image API ({type(e).__name__} after {round(time.time() - t0)} s): the ledger says unknown, whether an image "
                 "was made and billed is not known. Decide before sending it again (the same request: --again).", 1,
                 timeout=True, fingerprint=fp, tries=tries)
        tries.append(status)
        if status not in (429, 500, 502, 503, 504):
            break
    data = (js or {}).get("data") if isinstance(js, dict) else None
    b64 = (data or [{}])[0].get("b64_json") if isinstance(data, list) and data else None
    if status != 200 or not b64:
        err = (js or {}).get("error") if isinstance(js, dict) else None
        err = err if isinstance(err, dict) else {}
        code = err.get("code") or (f"http {status}" if status else "no image in the answer")
        _img_ledger(rd, "set", fp=fp, status="failed", note=str(code))
        _img_record_add(rec_p, key_name, {"attempt": attempt, "status": "moderation_blocked" if code == "moderation_blocked" else "failed",
                                          "fingerprint": fp, "at": now_iso(), "http": status, "request_file": str(reqf),
                                          "error": _scrub(err.get("message") or raw[:300], key), "moderation": err.get("moderation_details")})
        hint = ("the service refused the request (moderation_blocked): change the prompt or the reference images before any new attempt; "
                "never send it again unchanged") if code == "moderation_blocked" else (
               "the key was refused (401): check OPENAI_API_KEY on this PC" if status == 401 else
               "the model or a parameter was refused: read the error" if status == 400 else
               "rate limited or the service failed, after two retries" if status in (429, 500, 502, 503, 504) else "read the error")
        fail(f"no image: {code}. {hint}", 1, http=status, error_code=code, error=_scrub(err.get("message") or raw[:300], key),
             moderation=err.get("moderation_details"), tries=tries, fingerprint=fp)
    folder.mkdir(parents=True, exist_ok=True)
    f = folder / f"{tag}.png"
    f.write_bytes(base64.b64decode(b64))
    usage = js.get("usage") or {}
    cost = _img_cost(usage)
    wh = _img_size(f)
    _img_record_add(rec_p, key_name, {"attempt": attempt, "status": "completed", "source": "api", "file": str(f), "fingerprint": fp,
                                      "at": now_iso(), "model": model, "size": wh, "quality": quality, "refs": [r["file"] for r in params["refs"]],
                                      "request_file": str(reqf), "usage": usage, "cost_usd_estimate": cost}, use=f.name)
    _img_ledger(rd, "set", fp=fp, status="completed", note=f.name, job=str(js.get("created") or ""))
    out({"ok": True, "file": str(f), "attempt": attempt, "size": wh, "model": model, "quality": quality, "refs": len(refs),
         "usage": usage, "cost_usd_estimate": cost, "elapsed_s": round(time.time() - t0, 1), "tries": tries, "fingerprint": fp,
         "note": "view the image before you use it (the QC of reference/static §8); this attempt is now the one the edit uses"})


def _kcfg(key: str, default=None):
    return _scfg(f"klein.{key}", default)


def _klein_size_facts(w: int, h: int) -> dict:
    """Whether FLUX 3 Klein takes this size (config static.klein.limits: edges of a multiple of 16, from 64 to 4096), as facts."""
    lim = {"multiple": 16, "min_edge": 64, "max_edge": 4096, **(_kcfg("limits", {}) or {})}
    m, why = int(lim["multiple"]), []
    if w % m or h % m:
        why.append(f"both edges must be divisible by {m}")
    if min(w, h) < int(lim["min_edge"]) or max(w, h) > int(lim["max_edge"]):
        why.append(f"each edge must be between {lim['min_edge']} and {lim['max_edge']}")
    return {"valid": not why, "why_not": why, "pixels": w * h, "megapixels": round(w * h / 1e6, 2)}


def _klein_stub_png(dest: Path, w: int, h: int, seed: int) -> None:
    """Tests and dry runs (AWL_IMAGE_STUB): a flat picture stands in for a FLUX 3 Klein image."""
    from PIL import Image
    dest.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (w, h), ((seed * 53) % 256, (seed * 97) % 256, (seed * 29) % 256)).save(dest, format="PNG")


def _img_generate_klein(a, rd: Path, st: dict, anchor, nn: str, key_name: str, prompt: str, refs: list):
    """One still made on this PC by FLUX 3 Image Klein (static_images=klein): the worker (scripts/image_worker.py) in the ComfyUI
    install's own Python (AWL_IMAGE_PYTHON, AWL_IMAGE_ROOT), one GPU job at a time, ledgered like an API call (provider klein, no cost).
    The seed comes from the request and the attempt unless --seed names one, so a draw can be made again exactly."""
    max_refs = int(_kcfg("max_refs", 10))
    if len(refs) > max_refs:
        fail(f"FLUX 3 Klein takes at most {max_refs} reference images per image", 2)
    fmt = _static_fmt(st)
    w, h = _parse_size(a.size or fmt.get("image_size") or _scfg("images.size", "1088x1920"))
    facts = _klein_size_facts(w, h)
    if not facts["valid"]:
        fail(f"FLUX 3 Klein does not take {w}x{h}: " + "; ".join(facts["why_not"]), 2)
    engine = _kcfg("engine", "flux3-image-klein-int8")
    models = dict(_kcfg("models", {}) or {})
    steps, alpha = int(_kcfg("steps", 16)), _kcfg("alpha", 16.0)
    # a character's anchor is drawn from its sheet prompt as written: the upsampler adds plausible props (a veil, a tool) that every
    # later image of that character then copies from the anchor (seen 2026-11-06); the plan's images keep the upsampler
    upsample = bool(_kcfg("anchor_upsample", False) if anchor else _kcfg("upsample", True)) and not a.no_upsample
    params = {"engine": engine, "models": models, "prompt": prompt, "size": f"{w}x{h}", "steps": steps, "alpha": alpha,
              "upsample": upsample, "seed": a.seed, "refs": [{"file": str(r.resolve()), "sha1": _sha1_file(r)} for r in refs]}
    fp = _fingerprint({"params": params})
    folder, rec_p = _img_where(rd, nn, anchor)
    try:
        slot = (json.loads(rec_p.read_text(encoding="utf-8")).get("images") or {}).get(key_name) or {"attempts": []}
    except (OSError, ValueError):
        slot = {"attempts": []}
    done = [x for x in slot["attempts"] if x.get("fingerprint") == fp and x.get("status") == "completed" and Path(x.get("file") or "").is_file()]
    if done and not a.again:
        out({"ok": True, "reused": True, "file": done[-1]["file"], "attempt": done[-1]["attempt"], "seed": done[-1].get("seed"),
             "fingerprint": fp, "note": "this exact request already made this image: nothing was made (--again asks for a new draw)"})
    attempt = 1 + max([int(x.get("attempt") or 0) for x in slot["attempts"]] or [0])
    seed = int(a.seed) if a.seed is not None else int(hashlib.sha256(f"{fp}:{attempt}".encode("utf-8")).hexdigest(), 16) % 2 ** 32
    tag = f"{anchor}-a{attempt}" if anchor else f"i{key_name}-a{attempt}"
    reqf = rd / "50-requests" / (f"anchor-{anchor}-a{attempt}-image-request.json" if anchor else f"video-{nn}-i{key_name}-a{attempt}-image-request.json")
    write_json(reqf, {"video": nn, "image": key_name, "attempt": attempt, "kind": "image", "provider": "klein", "params": params, "seed": seed})
    _img_ledger(rd, "begin", video=nn, attempt=tag, fp=fp, model=engine, request_file=str(reqf), provider="klein")
    f = folder / f"{tag}.png"
    timeout = float(a.timeout or _kcfg("timeout_s", 1800))
    job = {"op": "generate", "root": os.environ.get("AWL_IMAGE_ROOT") or _kcfg("root") or "", "models": models, "alpha": alpha,
           "reserve_vram_gb": _kcfg("reserve_vram_gb", 5), "comfy_args": list(_kcfg("comfy_args", []) or []),
           "timeout_per_image": timeout, "images": [{"prompt": prompt, "out": str(f), "width": w, "height": h, "seed": seed,
                                                     "steps": steps, "upsample": upsample, "refs": [str(r.resolve()) for r in refs]}]}
    t0 = time.time()
    if os.environ.get("AWL_IMAGE_STUB"):
        _klein_stub_png(f, w, h, seed)
        res = {"ok": True, "stub": True, "engine": engine, "images": [{"ok": True, "out": str(f), "seed": seed, "caption": prompt, "seconds": 0.0}]}
    else:
        with _gpu_lock():
            res = _worker("image", job, timeout=timeout + 600)
    one = (res.get("images") or [{}])[0] if isinstance(res.get("images"), list) else {}
    if not res.get("ok") or not one.get("ok") or not f.is_file():
        err = str(one.get("error") or res.get("error") or "no image")[:600]
        _img_ledger(rd, "set", fp=fp, status="failed", note=err[:200])
        _img_record_add(rec_p, key_name, {"attempt": attempt, "status": "failed", "fingerprint": fp, "at": now_iso(), "request_file": str(reqf),
                                          "engine": engine, "seed": seed, "error": err})
        fail(f"no image from FLUX 3 Klein: {err}", 1, fingerprint=fp, seed=seed, log_tail=str(res.get("log_tail") or "")[-1200:] or None)
    wh = _img_size(f)
    _img_record_add(rec_p, key_name, {"attempt": attempt, "status": "completed", "source": "klein", "file": str(f), "fingerprint": fp,
                                      "at": now_iso(), "model": engine, "size": wh, "seed": seed, "steps": steps, "alpha": alpha,
                                      "upsampled": upsample, "caption": one.get("caption"), "refs": [r["file"] for r in params["refs"]],
                                      "request_file": str(reqf), "seconds": one.get("seconds"), "cost_usd_estimate": 0.0,
                                      "stub": bool(res.get("stub"))}, use=f.name)
    _img_ledger(rd, "set", fp=fp, status="completed", note=f.name)
    out({"ok": True, "file": str(f), "attempt": attempt, "size": wh, "engine": engine, "seed": seed, "upsampled": upsample,
         "caption": one.get("caption"), "refs": len(refs), "cost_usd_estimate": 0.0, "elapsed_s": round(time.time() - t0, 1),
         "fingerprint": fp, "stub": bool(res.get("stub")),
         "note": "view the image before you use it (the QC of reference/static §8); caption is what the image model received; this attempt "
                 "is now the one the edit uses"})


def _img_plan(rd: Path, nn: str) -> dict:
    p = rd / "40-briefs" / f"video-{nn}-images.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _img_prompts(a):
    """The prompts file a user generates the images from (Static, prompts mode): one prompt per image, the file name to save it as, the
    character images to attach, the size, and how to hand the folder back."""
    rd, _st = _state_of(a.run)
    vids = [_cf_nn(a.video)] if a.video else sorted({p.name[6:-12] for p in (rd / "40-briefs").glob("video-*-images.json")})
    if not vids:
        fail("no image plan: write 40-briefs/video-NN-images.json first (reference/static §5)", 2)
    files, total = [], 0
    for nn in vids:
        plan = _img_plan(rd, nn)
        imgs = plan.get("images") or []
        if not imgs:
            fail(f"40-briefs/video-{nn}-images.json has no images", 2)
        size = plan.get("size") or _static_fmt(_st).get("image_size") or _scfg("images.size", "1088x1920")
        _w, _h = _parse_size(size)
        asp = _static_fmt(_st).get("aspect") or _aspect_of(_w, _h)[0]
        shape = "vertical" if _h > _w else ("horizontal" if _w > _h else "square")
        L = [f"# Video {nn}: {len(imgs)} image prompts", "",
             f"Make every image **{shape} {asp}, {size}** (or the nearest {shape} size your tool offers) with GPT Image 2.5 or the image tool "
             f"you use. Save each image under the name in its heading (`v{nn}-iKK`, png, jpg or webp). When the images of every video are done, "
             "put them all in ONE folder (sub-folders are fine) and send me its path: I copy them in and never move or change your files.", ""]
        chars = plan.get("characters") or []
        if chars:
            L += ["## Characters (keep each one the same in every image)", ""]
            for c in chars:
                L.append(f"- **{c.get('id')}** {c.get('name') or ''}: " + (f"attach `{Path(c['photo']).name}` (`{c['photo']}`) to every image that shows "
                         "them" if c.get("photo") else "no photo: make its sheet first from the prompt below, then attach that sheet to every image that shows them"))
                if c.get("sheet_prompt") and not c.get("photo"):
                    L += ["", f"### {c.get('id')} character sheet (save as `{c.get('id')}-sheet`)", "", "```", str(c["sheet_prompt"]).strip(), "```", ""]
            L.append("")
        for im in imgs:
            kk = f"{int(im.get('image') or 0):02d}"
            L += [f"## v{nn}-i{kk}" + (f"  ·  {ts_label(float(im['start']))}–{ts_label(float(im['end']))}" if im.get("start") is not None and im.get("end") is not None else ""), ""]
            if im.get("line"):
                L.append(f"Narration over it: “{str(im['line']).strip()}”")
            if im.get("characters"):
                L.append("Attach: " + ", ".join(str(c) for c in im["characters"]) + " (their photo or sheet, above)")
            L += ["", "```", str(im.get("prompt") or "").strip(), "```", ""]
        dest = rd / "deliverables" / "prompts" / f"video-{nn}-image-prompts.md"
        write_text(dest, "\n".join(L))
        files.append(str(dest))
        total += len(imgs)
    out({"ok": True, "files": files, "images": total, "naming": "vNN-iKK (png, jpg or webp), all in one folder; sub-folders fine",
         "note": "give the user these files' paths and how to hand back the folder; `T image intake --folder <path>` copies them in"})


def _img_intake(a):
    """Copy the user's images (Static, prompts mode) into the run, by their names vNN-iKK; never moves or changes the user's files.
    Reports, as facts, what each video's plan expects and does not have, what came in that no plan names, names seen twice, files whose
    name holds no vNN-iKK, and each image's size and how far its aspect is from the run's format (9:16 when none is stored)."""
    rd, _st = _state_of(a.run)
    src = Path(a.folder)
    if not src.is_dir():
        fail(f"folder not found: {src}", 2)
    found, unmatched = {}, []
    for f in sorted(src.rglob("*")):
        if f.is_file() and f.suffix.lower() in IMAGE_EXT:
            m = STATIC_IMG_NAME.search(f.stem)
            if m:
                found.setdefault((f"{int(m.group(1)):02d}", f"{int(m.group(2)):02d}"), []).append(f)
            else:
                unmatched.append(str(f))
    want = {}
    for p in sorted((rd / "40-briefs").glob("video-*-images.json")):
        nn = p.name[6:-12]
        if a.video and nn != _cf_nn(a.video):
            continue
        want[nn] = {f"{int(im.get('image') or 0):02d}" for im in (_img_plan(rd, nn).get("images") or [])}
    t_asp = _static_fmt(_st).get("aspect") if _static_fmt(_st).get("aspect") in STATIC_ASPECTS else "9:16"
    t_ratio = STATIC_ASPECTS[t_asp][0] / STATIC_ASPECTS[t_asp][1]
    copied, dupes, extra = [], [], []
    for (nn, kk), fs in sorted(found.items()):
        if a.video and nn != _cf_nn(a.video):
            continue
        if kk not in want.get(nn, set()):
            extra.append({"video": nn, "image": kk, "files": [str(x) for x in fs]})
            continue
        f = max(fs, key=lambda x: x.stat().st_mtime)
        if len(fs) > 1:
            dupes.append({"video": nn, "image": kk, "files": [str(x) for x in fs], "taken": str(f)})
        folder, rec_p = _img_where(rd, nn, None)
        folder.mkdir(parents=True, exist_ok=True)
        dest = folder / f"i{kk}-user{f.suffix.lower()}"
        shutil.copy2(f, dest)
        wh = _img_size(dest)
        aspect_off = round(abs((wh[0] / wh[1]) - t_ratio) / t_ratio, 3) if len(wh) == 2 and wh[1] else None
        try:
            prev = (json.loads(rec_p.read_text(encoding="utf-8")).get("images") or {}).get(kk) or {}
        except (OSError, ValueError):
            prev = {}
        att = 1 + max([int(x.get("attempt") or 0) for x in prev.get("attempts", [])] or [0])
        _img_record_add(rec_p, kk, {"attempt": att, "status": "completed", "source": "user", "file": str(dest), "from": str(f),
                                    "sha1": _sha1_file(dest), "at": now_iso(), "size": wh}, use=dest.name)
        copied.append({"video": nn, "image": kk, "file": str(dest), "from": str(f), "size": wh, "off_aspect": aspect_off})
    missing = [{"video": nn, "image": kk} for nn, ks in sorted(want.items()) for kk in sorted(ks) if (nn, kk) not in found]
    out({"ok": True, "folder": str(src), "copied": copied, "missing": missing, "not_in_any_plan": extra, "named_twice": dupes,
         "names_without_vNN_iKK": unmatched[:60], "unmatched_total": len(unmatched),
         "aspect": t_asp, "note": f"copies only (your folder is untouched); off_aspect is the share each image's aspect differs from the run's "
                                  f"{t_asp} (the edit crops to fill); view each image before the edit"})


def _img_use(a):
    rd, _st = _state_of(a.run)
    anchor = re.sub(r"[^A-Za-z0-9_-]+", "", a.anchor or "") or None
    nn = "00" if anchor else _cf_nn(a.video)
    key_name = anchor or f"{int(a.image or 0):02d}"
    folder, rec_p = _img_where(rd, nn, anchor)
    try:
        slot = (json.loads(rec_p.read_text(encoding="utf-8")).get("images") or {}).get(key_name) or {}
    except (OSError, ValueError):
        slot = {}
    pick = next((x for x in slot.get("attempts", []) if int(x.get("attempt") or 0) == int(a.attempt or 0) and Path(x.get("file") or "").is_file()), None)
    if not pick:
        fail(f"no finished attempt {a.attempt} of {key_name} with a file on disk", 2)
    _img_record_add(rec_p, key_name, None, use=Path(pick["file"]).name)
    out({"ok": True, "image": key_name, "uses": pick["file"]})


def cmd_image(a):
    """Static stills (contract item 36): generate (OpenAI Images API, ledgered) | prompts (the file a user makes them from) | intake (the
    user's folder, copied in) | use (which attempt the edit takes). Facts only; the agent views and judges every image."""
    {"generate": _img_generate, "prompts": _img_prompts, "intake": _img_intake, "use": _img_use}[a.action](a)


# ---- the local workers (Qwen3-TTS, ACE-Step 1.5): each runs in its own Python, one model load per call, one JSON line back

WORKER_ENV = {"tts": "AWL_TTS_PYTHON", "music": "AWL_MUSIC_PYTHON", "image": "AWL_IMAGE_PYTHON"}


def _worker_python(kind: str) -> str:
    return (os.environ.get(WORKER_ENV[kind]) or _scfg(f"{kind}.python") or "").strip().strip('"')


def _worker(kind: str, job: dict, timeout: float = 7200, cwd=None) -> dict:
    """Run scripts/<kind>_worker.py with the job in the tool's own interpreter; its last stdout line is the answer."""
    py = _worker_python(kind)
    if not py or not Path(py).is_file():
        return {"ok": False, "error": f"{WORKER_ENV[kind]} is not set to an existing python.exe (or guarded .cmd) of the {kind} environment "
                                      "(reference/static §9)"}
    script = Path(__file__).resolve().parent / f"{kind}_worker.py"
    jf = runs_root() / ".workers" / f"{kind}-{os.getpid()}-{int(time.time() * 1000)}.json"
    jf.parent.mkdir(parents=True, exist_ok=True)
    jf.write_text(json.dumps(job, ensure_ascii=False), encoding="utf-8")
    try:
        cp = run([py, "-X", "utf8", str(script), str(jf)], cwd=cwd, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"the {kind} worker ran past {int(timeout)} s"}
    finally:
        jf.unlink(missing_ok=True)
    last = [ln for ln in (cp.stdout or "").strip().splitlines() if ln.strip()]
    try:
        res = json.loads(last[-1]) if last else {}
    except ValueError:
        res = {}
    if not res:
        res = {"ok": False, "error": f"the {kind} worker gave no answer (exit {cp.returncode}): " + (cp.stderr or "")[-800:]}
    return res


def _gpu_lock():
    """One local model on the GPU at a time (Qwen3-TTS and ACE-Step share it), across every agent of this library."""
    return FileLock(runs_root() / ".gpu.lock", timeout=7200.0, stale=14400.0)


def _tone(dest: Path, seconds: float, freq: int = 220, rate: int = 24000) -> float:
    """Tests and dry runs (AWL_TTS_STUB / AWL_MUSIC_STUB): a plain tone stands in for a model's audio."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    run([find_tool("ffmpeg"), "-nostdin", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"sine=frequency={freq}:duration={seconds:.3f}",
         "-ac", "1", "-ar", str(rate), "-c:a", "pcm_s16le", str(dest)], check=True, timeout=120)
    return round(seconds, 3)


def _voice_dir(rd: Path) -> Path:
    return rd / "30-assets" / "voice"


def _tts_job_base() -> dict:
    return {"device": os.environ.get("AWL_TTS_DEVICE") or _scfg("tts.device", "cuda:0"), "dtype": _scfg("tts.dtype", "bfloat16"),
            "attn": _scfg("tts.attn", "sdpa")}


def _state_set(rd: Path, **pairs):
    p = rd / "state.json"
    with FileLock(p.with_name("state.json.lock")):
        st = json.loads(p.read_text(encoding="utf-8"))
        for k, v in pairs.items():
            _set_dotted(st, k, v)
        st["updated"] = now_iso()
        write_json(p, st)


def _tts_check(a):
    if os.environ.get("AWL_TTS_STUB"):
        out({"ok": True, "stub": True, "ready": True})
    res = _worker("tts", {"op": "check", "models": [_scfg("tts.design_model"), _scfg("tts.clone_model")], **_tts_job_base()}, timeout=600)
    out({"ok": bool(res.get("ok")), "ready": bool(res.get("ok")), **res})


def _tts_design(a):
    """Static voice samples: one VoiceDesign load, one short sample per --instruct (the voice described in words), all speaking --text."""
    rd, _st = _state_of(a.run)
    if not a.text or not a.instruct:
        fail("design needs --text (the line every sample speaks) and one --instruct per sample (the voice in words)", 2)
    vd = _voice_dir(rd)
    lang = a.language or _scfg("tts.language", "english")
    base = int(_scfg("tts.seed", 1105))
    items = [{"n": i + 1, "text": a.text, "instruct": ins, "out": str(vd / f"sample-{i + 1}.wav"), "seed": base + i + 1}
             for i, ins in enumerate(a.instruct)]
    if os.environ.get("AWL_TTS_STUB"):
        for it in items:
            it["duration_s"] = _tone(Path(it["out"]), max(1.5, len(a.text.split()) / 2.6), 180 + 40 * it["n"])
        res = {"ok": True, "items": items, "stub": True}
    else:
        with _gpu_lock():
            res = _worker("tts", {"op": "design", "model": _scfg("tts.design_model"), "language": lang, "items": items, **_tts_job_base()})
    if not res.get("ok"):
        fail("voice design failed: " + str(res.get("error"))[:600], 1, worker=res)
    write_json(vd / "samples.json", {"text": a.text, "language": lang, "samples": res.get("items") or items, "made": now_iso(),
                                     "model": _scfg("tts.design_model")})
    out({"ok": True, "samples": [{"n": it["n"], "file": it["out"], "instruct": it["instruct"], "seed": it.get("seed"), "duration_s": it.get("duration_s")}
                                 for it in (res.get("items") or items)],
         "note": "give the user the three files to listen to; their pick is stored with `T tts voice --sample K`"})


def _tts_voice(a):
    """The run's one voice (Static): the picked sample becomes the clone reference (Base model, design then clone), saved as a reusable
    prompt; each --emotion NAME=TEXT adds a reference clip of the same voice speaking that line, and its own prompt."""
    rd, _st = _state_of(a.run)
    vd = _voice_dir(rd)
    try:
        samples = json.loads((vd / "samples.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        fail("no voice samples in this run: `T tts design` first", 2)
    pick = next((s for s in samples.get("samples", []) if int(s.get("n") or 0) == int(a.sample or 0)), None)
    if not pick or not Path(pick.get("out") or "").is_file():
        fail(f"sample {a.sample} not found in 30-assets/voice/samples.json", 2)
    ref = vd / "ref-neutral.wav"
    shutil.copy2(pick["out"], ref)
    write_text(vd / "ref-neutral.txt", samples["text"])
    emotions = []
    for e in a.emotion or []:
        if "=" not in e:
            fail(f"--emotion takes NAME=TEXT, got {e!r}", 2)
        name, text = e.split("=", 1)
        name = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
        emotions.append({"name": name, "text": text.strip(), "out_wav": str(vd / f"ref-{name}.wav"), "out_prompt": str(vd / f"prompt-{name}.pt")})
    lang = samples.get("language") or _scfg("tts.language", "english")
    job = {"op": "voice", "model": _scfg("tts.clone_model"), "language": lang, "ref_audio": str(ref), "ref_text": samples["text"],
           "out_prompt": str(vd / "prompt-neutral.pt"), "emotions": emotions, **_tts_job_base()}
    if os.environ.get("AWL_TTS_STUB"):
        Path(job["out_prompt"]).write_text("stub", encoding="utf-8")
        for e in emotions:
            _tone(Path(e["out_wav"]), max(1.2, len(e["text"].split()) / 2.6), 300)
            Path(e["out_prompt"]).write_text("stub", encoding="utf-8")
        res = {"ok": True, "stub": True}
    else:
        with _gpu_lock():
            res = _worker("tts", job)
    if not res.get("ok"):
        fail("the voice could not be built: " + str(res.get("error"))[:600], 1, worker=res)
    prompts = {"neutral": job["out_prompt"], **{e["name"]: e["out_prompt"] for e in emotions}}
    _state_set(rd, **{"static.voice": {"sample": int(a.sample), "instruct": pick.get("instruct"), "seed": pick.get("seed"),
                                        "ref_text": samples["text"], "language": lang,
                                        "ref_audio": str(ref), "prompts": prompts, "design_model": _scfg("tts.design_model"),
                                        "clone_model": _scfg("tts.clone_model"), "set_at": now_iso()}})
    out({"ok": True, "voice": {"sample": int(a.sample), "prompts": prompts}, "emotion_clips": [e["out_wav"] for e in emotions],
         "note": "every narration of this run uses this voice (state.json -> static.voice)"})


def _wav_read(p: Path) -> tuple:
    import wave
    with wave.open(str(p), "rb") as w:
        return w.getframerate(), w.getnchannels(), w.getsampwidth(), w.readframes(w.getnframes())


def _ebur128(p: Path) -> float | None:
    cp = run([find_tool("ffmpeg"), "-nostdin", "-hide_banner", "-i", str(p), "-af", "ebur128=framelog=quiet", "-f", "null", "-"], timeout=900)
    m = re.findall(r"I:\s+(-?\d+(?:\.\d+)?)\s+LUFS", cp.stderr or "")
    return float(m[-1]) if m else None


def _voice_match(ref: Path, files: dict) -> dict:
    """Each line against the run's voice, as numbers: its pitch median and how many semitones it sits from the voice's, and a timbre
    similarity (the cosine of the mean MFCCs, 0 to 1). Measured, never listened to; the agent compares a strong line with the cloned ones."""
    try:
        import numpy as np
        import librosa
    except ImportError:
        return {}

    def feats(p):
        try:
            y, sr = librosa.load(str(p), sr=16000, mono=True)
        except Exception:  # noqa: BLE001
            return None
        if len(y) < 1600:
            return None
        f0, _vf, _vp = librosa.pyin(y, fmin=60, fmax=500, sr=sr, frame_length=1024)
        f0 = f0[~np.isnan(f0)] if f0 is not None else []
        mf = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)[1:].mean(axis=1)
        return (float(np.median(f0)) if len(f0) else None), mf
    r = feats(ref)
    if not r:
        return {}
    res = {}
    for n, p in files.items():
        f = feats(p)
        if not f:
            continue
        sim = float(np.dot(f[1], r[1]) / ((np.linalg.norm(f[1]) * np.linalg.norm(r[1])) or 1.0))
        st_ = round(12 * math.log2(f[0] / r[0]), 2) if f[0] and r[0] else None
        res[n] = {"pitch_hz": round(f[0], 1) if f[0] else None, "pitch_st": st_, "timbre_sim": round(sim, 3)}
    return res


def _strong_instruct(base: str, delivery: str) -> str:
    """The run's voice description word for word, then the line's delivery."""
    b = str(base or "").strip().rstrip(".")
    d = str(delivery or "").strip().rstrip(".")
    return f"{b}. {d}." if d else f"{b}."


def _tts_say(a):
    """A video's narration (Static): every line in the run's voice (its emotion's reference clip when the line names one; a line marked
    strong by the voice-design model, from the run's voice description plus the line's delivery and the picked sample's seed), joined with
    the planned pauses, brought to the target loudness. The sidecar holds each line's exact start and end in the narration file and its
    numbers against the run's voice."""
    rd, st = _state_of(a.run)
    nn = _cf_nn(a.video)
    lines_p = Path(a.lines_file) if a.lines_file else rd / "40-briefs" / f"video-{nn}-narration.json"
    try:
        spec = json.loads(lines_p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        fail(f"narration lines not found or not JSON: {lines_p} (reference/static §4)", 2)
    voice = (st.get("static") or {}).get("voice") or {}
    if not voice.get("prompts"):
        fail("the run has no voice yet: `T tts voice --sample K` after the user picked one", 2)
    lines = [ln for ln in spec.get("lines") or [] if str(ln.get("text") or "").strip()]
    if not lines:
        fail(f"{lines_p.name} has no lines", 2)
    nd = rd / "30-assets" / "narration" / f"video-{nn}"
    only = {int(x) for x in re.findall(r"\d+", a.only or "")}
    todo = []
    for i, ln in enumerate(lines, 1):
        n = int(ln.get("n") or i)
        ln["n"] = n
        ln["file"] = str(nd / f"line-{n:02d}.wav")
        if not only or n in only or not Path(ln["file"]).is_file():
            todo.append({"n": n, "text": str(ln["text"]).strip(), "emotion": str(ln.get("emotion") or "neutral"), "out": ln["file"],
                         "strong": bool(ln.get("strong")), "delivery": str(ln.get("delivery") or "").strip(), "seed": ln.get("seed")})
    lang = spec.get("language") or voice.get("language") or _scfg("tts.language", "english")
    strong = [x for x in todo if x["strong"]]
    if strong and not voice.get("instruct"):
        fail("a strong line needs the run's voice description (state.json -> static.voice.instruct): `T tts voice --sample K` again", 2)
    for x in strong:
        x["instruct"] = _strong_instruct(voice["instruct"], x["delivery"])
        x["seed"] = int(x["seed"]) if x.get("seed") is not None else voice.get("seed")
    cloned = [x for x in todo if not x["strong"]]
    t0 = time.time()
    if todo:
        if os.environ.get("AWL_TTS_STUB"):
            for it in todo:
                _tone(Path(it["out"]), max(0.8, len(it["text"].split()) / 2.6), 230 if it["strong"] else 200)
            res = {"ok": True, "stub": True}
        else:
            res = {"ok": True}
            with _gpu_lock():
                if cloned:
                    res = _worker("tts", {"op": "say", "model": voice.get("clone_model") or _scfg("tts.clone_model"), "language": lang,
                                          "prompts": voice["prompts"], "lines": cloned, **_tts_job_base()})
                if res.get("ok") and strong:
                    res = _worker("tts", {"op": "design", "model": voice.get("design_model") or _scfg("tts.design_model"), "language": lang,
                                          "items": [{"n": x["n"], "text": x["text"], "instruct": x["instruct"], "out": x["out"], "seed": x["seed"]}
                                                    for x in strong], **_tts_job_base()})
        if not res.get("ok"):
            fail("narration failed: " + str(res.get("error"))[:600], 1, worker=res)
    pause_default = float(_scfg("narration.pause_s", 0.35))
    sr0, frames, rows, pos = None, bytearray(), [], 0.0
    for ln in lines:
        sr, ch, sw, data = _wav_read(Path(ln["file"]))
        if sr0 is None:
            sr0, ch0, sw0 = sr, ch, sw
        if (sr, ch, sw) != (sr0, ch0, sw0):
            fail(f"line {ln['n']} has another sample format ({sr} Hz, {ch} ch) than line 1 ({sr0} Hz): re-make it", 1)
        dur = len(data) / (sr * ch * sw)
        rows.append({"n": ln["n"], "text": ln["text"], "emotion": ln.get("emotion") or "neutral", "file": ln["file"],
                     "made_by": "design" if ln.get("strong") else "clone", "start": round(pos, 3), "end": round(pos + dur, 3)})
        if ln.get("strong"):
            rows[-1].update({"delivery": str(ln.get("delivery") or "").strip(),
                             "seed": int(ln["seed"]) if ln.get("seed") is not None else voice.get("seed")})
        frames += data
        pos += dur
        gap = float(ln.get("pause_after", pause_default) or 0) if ln is not lines[-1] else 0.0
        frames += b"\x00" * (int(round(gap * sr)) * ch * sw)
        pos += round(int(round(gap * sr)) / sr, 6)
    import wave
    raw = rd / "30-assets" / "narration" / f"video-{nn}.raw.wav"
    with wave.open(str(raw), "wb") as w:
        w.setnchannels(ch0)
        w.setsampwidth(sw0)
        w.setframerate(sr0)
        w.writeframes(bytes(frames))
    final = rd / "30-assets" / "narration" / f"video-{nn}.wav"
    target = float(_scfg("narration.loudness_lufs", -14.0))
    cp = run([find_tool("ffmpeg"), "-nostdin", "-y", "-loglevel", "error", "-i", str(raw), "-af", f"loudnorm=I={target}:TP=-1.5:LRA=11",
              "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(final)], timeout=900)
    if cp.returncode != 0:
        fail("loudness pass failed: " + cp.stderr[-400:])
    vm = _voice_match(Path(voice.get("ref_audio") or ""), {r["n"]: r["file"] for r in rows}) if voice.get("ref_audio") else {}
    for r in rows:
        r.update(vm.get(r["n"]) or {})
    cl = [r for r in rows if r["made_by"] == "clone" and r.get("timbre_sim") is not None]
    match = {"clone_lines": {"pitch_st": [min((r["pitch_st"] for r in cl if r.get("pitch_st") is not None), default=None),
                                          max((r["pitch_st"] for r in cl if r.get("pitch_st") is not None), default=None)],
                             "timbre_sim_min": min((r["timbre_sim"] for r in cl), default=None)},
             "strong_lines": [{"n": r["n"], "pitch_st": r.get("pitch_st"), "timbre_sim": r.get("timbre_sim"), "seed": r.get("seed")}
                              for r in rows if r["made_by"] == "design"]}
    side = {"video": nn, "file": str(final), "raw": str(raw), "duration_s": round(pos, 3), "language": lang, "lines": rows, "voice_match": match,
            "voice": {"sample": voice.get("sample"), "instruct": voice.get("instruct")}, "loudness_lufs": _ebur128(final),
            "made": now_iso(), "stub": bool(os.environ.get("AWL_TTS_STUB"))}
    write_json(final.with_suffix(".json"), side)
    out({"ok": True, "file": str(final), "sidecar": str(final.with_suffix(".json")), "duration_s": side["duration_s"], "lines": len(rows),
         "made_now": [t["n"] for t in todo], "loudness_lufs": side["loudness_lufs"], "elapsed_s": round(time.time() - t0, 1),
         "voice_match": match,
         "note": "next: `T narration-words` (the words, the cues and the check against the script); a strong line far from the cloned "
                 "lines' numbers is made again with another seed (reference/static §6)"})


def cmd_tts(a):
    """Static's voice (contract item 36): check | design (voice samples) | voice (the picked sample becomes the run's voice) | say (a video's
    narration). Qwen3-TTS runs in its own environment (AWL_TTS_PYTHON); one GPU job at a time."""
    if a.action != "check" and not a.run:
        fail(f"tts {a.action} needs --run", 2)
    {"check": _tts_check, "design": _tts_design, "voice": _tts_voice, "say": _tts_say}[a.action](a)


def cmd_narration_words(a):
    """The words of a video's narration with their times (speech-to-text timing, the script's wording), the caption cues and an SRT, and how
    the heard words differ from the script per line (missing, extra, repeated): facts for the narration QC."""
    import difflib
    rd, _st = _state_of(a.run)
    nn = _cf_nn(a.video)
    side_p = rd / "30-assets" / "narration" / f"video-{nn}.json"
    try:
        side = json.loads(side_p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        fail(f"no narration for video {nn}: `T tts say` first", 2)
    work = rd / "30-assets" / "narration" / f"video-{nn}-words"
    work.mkdir(parents=True, exist_ok=True)
    wav16 = work / "narration-16k.wav"
    run([find_tool("ffmpeg"), "-nostdin", "-y", "-loglevel", "error", "-i", side["file"], "-ac", "1", "-ar", "16000", str(wav16)], check=True, timeout=600)
    lang = STATIC_LANG_ISO.get(str(side.get("language") or "").lower(), "auto")
    tr = transcribe(str(wav16), work, a.whisper_model, lang)
    heard = [w for s in tr.get("segments", []) for w in s.get("words", [])]
    script = " ".join(r["text"] for r in side["lines"])
    timed = align_script(heard, script) if heard else []
    per_line, k = [], 0
    for r in side["lines"]:
        hw = [_norm_word(w["w"]) for w in heard if r["start"] - 0.15 <= w["s"] <= r["end"] + 0.15]
        sw = [_norm_word(x) for x in r["text"].split()]
        # numbers are compared apart: speech-to-text writes a spoken "seventeen sixty-nine" as "1769" (and "Saint" as "St")
        sc = [_SPOKEN_ABBR.get(x, x) for x in sw if not _is_number_token(x)]
        hc = [_SPOKEN_ABBR.get(x, x) for x in hw if not _is_number_token(x)]
        sm = difflib.SequenceMatcher(a=sc, b=hc, autojunk=False)
        miss = [x for tag, i1, i2, _j1, _j2 in sm.get_opcodes() if tag in ("delete", "replace") for x in sc[i1:i2]]
        extra = [x for tag, _i1, _i2, j1, j2 in sm.get_opcodes() if tag in ("insert", "replace") for x in hc[j1:j2]]
        rep = [w for i, w in enumerate(hw[1:], 1) if w and w == hw[i - 1]]
        per_line.append({"n": r["n"], "script_words": len(sw), "heard_words": len(hw), "missing": miss[:12], "extra": extra[:12],
                         "repeated": rep[:6], "match": round(sm.ratio(), 3) if (sc or hc) else 1.0,
                         "numbers": {"script": [x for x in sw if _is_number_token(x)], "heard": [x for x in hw if _is_number_token(x)]}})
        k += len(sw)
    plan_words = (_img_plan(rd, nn).get("captions") or {}).get("words")   # the plan's text look sets the words at once (static §2)
    cues = chunk_words(timed, int(a.words or plan_words or _scfg("captions.words", 3))) if timed else []
    write_json(work.parent / f"video-{nn}.words.json", {"video": nn, "engine": tr.get("engine"), "words": timed, "heard": heard})
    write_json(work.parent / f"video-{nn}.cues.json", cues)
    srt = []
    for i, c in enumerate(cues, 1):
        srt += [str(i), f"{_srt_time(c['start'])} --> {_srt_time(c['end'])}", c["text"], ""]
    write_text(work.parent / f"video-{nn}.srt", "\n".join(srt))
    off = [x for x in per_line if x["match"] < float(a.min_match)]
    out({"ok": True, "video": nn, "engine": tr.get("engine"), "words": len(timed), "cues": len(cues), "lines": per_line,
         "lines_to_check": [x["n"] for x in off], "files": {"words": str(work.parent / f"video-{nn}.words.json"),
                                                             "cues": str(work.parent / f"video-{nn}.cues.json"), "srt": str(work.parent / f"video-{nn}.srt")},
         "note": "match is the share of a line's script words heard in its span (speech-to-text, not a verdict), numbers apart (each line's "
                 "`numbers` lists the script's and the heard ones: speech-to-text writes spoken numbers as digits): judge the lines it lists; "
                 "a line made again: `T tts say --only N`, then this again"})


def _srt_time(t: float) -> str:
    ms = int(round(max(0.0, t) * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def cmd_music(a):
    """Static's bed (contract item 36), only when the plan calls for one: every track of --plan in one ACE-Step 1.5 load (instrumental, the
    narration's length plus a tail, fades), saved as 30-assets/music/video-NN.wav with a sidecar."""
    if a.action == "check":
        if os.environ.get("AWL_MUSIC_STUB"):
            out({"ok": True, "stub": True, "ready": True})
        res = _worker("music", {"op": "check", "root": os.environ.get("AWL_MUSIC_ROOT") or _scfg("music.root"),
                                "config": _scfg("music.config", "acestep-v15-turbo")}, timeout=600,
                      cwd=os.environ.get("AWL_MUSIC_ROOT") or _scfg("music.root") or None)
        out({"ok": bool(res.get("ok")), "ready": bool(res.get("ok")), **res})
    if not a.run:
        fail("music make needs --run", 2)
    rd, _st = _state_of(a.run)
    plan_p = Path(a.plan) if a.plan else rd / "40-briefs" / "music.json"
    try:
        plan = json.loads(plan_p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        fail(f"music plan not found or not JSON: {plan_p} (reference/static §6)", 2)
    md = rd / "30-assets" / "music"
    tracks = []
    for tr in plan.get("tracks") or []:
        nn = _cf_nn(tr.get("video"))
        if a.video and nn != _cf_nn(a.video):
            continue
        if not tr.get("caption") or not tr.get("duration"):
            fail(f"track of video {nn} needs caption and duration", 2)
        tracks.append({"video": nn, "caption": str(tr["caption"])[:500], "duration": float(tr["duration"]), "bpm": tr.get("bpm"),
                       "seed": int(tr.get("seed") or 1234), "fade_in": float(tr.get("fade_in", _scfg("music.fade_in_s", 1.0))),
                       "fade_out": float(tr.get("fade_out", _scfg("music.fade_out_s", 3.0))), "out": str(md / f"video-{nn}.wav")})
    if not tracks:
        fail("no track to make (the plan is empty, or --video names none of it)", 2)
    if os.environ.get("AWL_MUSIC_STUB"):
        for t_ in tracks:
            _tone(Path(t_["out"]), t_["duration"], 110, 48000)
        res = {"ok": True, "stub": True, "tracks": tracks}
    else:
        root = os.environ.get("AWL_MUSIC_ROOT") or _scfg("music.root") or ""
        with _gpu_lock():
            res = _worker("music", {"op": "generate", "root": root, "config": _scfg("music.config", "acestep-v15-turbo"),
                                    "device": _scfg("music.device", "cuda"), "steps": int(_scfg("music.inference_steps", 8)), "tracks": tracks},
                          cwd=root or None)
    if not res.get("ok"):
        fail("music failed: " + str(res.get("error"))[:600], 1, worker=res)
    made = []
    for t_ in tracks:
        f = Path(t_["out"])
        if f.is_file():
            write_json(f.with_suffix(".json"), {**t_, "made": now_iso(), "model": _scfg("music.config", "acestep-v15-turbo"),
                                                "stub": bool(os.environ.get("AWL_MUSIC_STUB"))})
            made.append({"video": t_["video"], "file": str(f), "duration_s": (media_summary(f) or {}).get("duration_s")})
    out({"ok": bool(made), "made": made, "asked": len(tracks), "note": "listen before use; the bed goes under the narration ducked (slideshow render)"})


def _static_check(a):
    """Static's setup on this PC (contract item 36), as facts per part: the OpenAI key (present or not; never printed) and whether the image
    model answers, FLUX 3 Klein's install and model files, the TTS and music environments (their workers' own checks), faster-whisper's
    cached models, ffmpeg's filters, capcut-cli."""
    parts = {}
    key = _oa_key()
    model = _scfg("images.model", "gpt-image-2.5-sunburst")
    img = {"key_present": bool(key), "model": model, "needed_for": "images by the API (static_images=api)"}
    if key and not a.offline:
        try:
            st_, js, raw = _oa_call("GET", f"/models/{model}", None, key, 30)
            img["model_answers"] = st_ == 200
            if st_ != 200:
                img["http"] = st_
                img["error"] = _scrub((((js or {}).get("error") or {}) if isinstance(js, dict) else {}).get("message") or raw[:200], key)
        except Exception as e:  # noqa: BLE001
            img["model_answers"] = False
            img["error"] = type(e).__name__
    parts["images"] = img
    if os.environ.get("AWL_IMAGE_STUB"):
        parts["images_klein"] = {"ready": True, "stub": True, "needed_for": "images by FLUX 3 Klein on this PC (static_images=klein)"}
    else:
        r = _worker("image", {"op": "check", "root": os.environ.get("AWL_IMAGE_ROOT") or _kcfg("root") or "",
                              "models": _kcfg("models", {}) or {}}, timeout=600)
        parts["images_klein"] = {"ready": bool(r.get("ok")), "python": _worker_python("image") or None,
                                 "root": os.environ.get("AWL_IMAGE_ROOT") or _kcfg("root") or None,
                                 "needed_for": "images by FLUX 3 Klein on this PC (static_images=klein)", **r}
    if os.environ.get("AWL_TTS_STUB"):
        parts["tts"] = {"ready": True, "stub": True}
    else:
        r = _worker("tts", {"op": "check", "models": [_scfg("tts.design_model"), _scfg("tts.clone_model")], **_tts_job_base()}, timeout=600)
        parts["tts"] = {"ready": bool(r.get("ok")), "python": _worker_python("tts") or None, **r}
    if os.environ.get("AWL_MUSIC_STUB"):
        parts["music"] = {"ready": True, "stub": True}
    else:
        root = os.environ.get("AWL_MUSIC_ROOT") or _scfg("music.root") or ""
        r = _worker("music", {"op": "check", "root": root, "config": _scfg("music.config", "acestep-v15-turbo")}, timeout=600, cwd=root or None)
        parts["music"] = {"ready": bool(r.get("ok")), "python": _worker_python("music") or None, "root": root or None,
                          "needed_for": "a bed, only when the plan calls for one", **r}
    try:
        import faster_whisper  # noqa: F401
        hub = Path(os.environ.get("HF_HOME") or Path.home() / ".cache" / "huggingface") / "hub"
        cached = sorted(p.name.split("--")[-1] for p in hub.glob("models--*faster-whisper*")) if hub.is_dir() else []
        parts["whisper"] = {"ready": bool(cached) or bool(os.environ.get("AWL_TRANSCRIBE_STUB")), "cached_models": cached}
    except ImportError:
        parts["whisper"] = {"ready": bool(os.environ.get("AWL_TRANSCRIBE_STUB")), "error": "faster_whisper is not installed in this Python"}
    try:
        fl = run([find_tool("ffmpeg"), "-hide_banner", "-filters"], timeout=60).stdout
        need = ["zoompan", "xfade", "loudnorm", "sidechaincompress", "subtitles", "ebur128"]
        parts["ffmpeg"] = {"ready": all(re.search(rf"\b{n}\b", fl) for n in need), "missing_filters": [n for n in need if not re.search(rf"\b{n}\b", fl)]}
    except Exception as e:  # noqa: BLE001
        parts["ffmpeg"] = {"ready": False, "error": str(e)[:200]}
    parts["capcut_cli"] = {"ready": bool(shutil.which("capcut")), "path": shutil.which("capcut")}
    out({"ok": True, "parts": parts, "note": "facts per part; which part a run needs (the API key only with static_images=api, images_klein only with "
                                             "static_images=klein, music only when a bed is "
                                             "planned) and what is a blocker are the agent's call (reference/static §9 has the setup)"})


# ---- the format (A5): the aspect, the export size the CapCut project is made at (its export is the final), the image size, the quality

STATIC_ASPECTS = {"9:16": (9, 16), "16:9": (16, 9), "1:1": (1, 1), "4:5": (4, 5), "3:4": (3, 4), "4:3": (4, 3)}
CAPCUT_RATIO_LABELS = ("16:9", "9:16", "1:1", "4:3", "3:4")     # capcut-cli's canvas presets; any other canvas is labelled "original"
IMG_LIMITS_DEFAULT = {"multiple": 16, "max_edge": 3840, "min_pixels": 655360, "max_pixels": 8294400, "experimental_above_pixels": 3686400,
                      "ratio_min": 1 / 3, "ratio_max": 3.0}


def _aspect_of(w: float, h: float) -> tuple:
    """The nearest named aspect of a size and how far the real one is from it (a share)."""
    r = float(w) / float(h)
    best = min(STATIC_ASPECTS, key=lambda k: abs(r - STATIC_ASPECTS[k][0] / STATIC_ASPECTS[k][1]))
    tr = STATIC_ASPECTS[best][0] / STATIC_ASPECTS[best][1]
    return best, round(abs(r - tr) / tr, 3)


def _parse_size(s) -> tuple:
    m = re.fullmatch(r"\s*(\d+)\s*[xX×]\s*(\d+)\s*", str(s or ""))
    if not m:
        fail(f"a size is WIDTHxHEIGHT, got {s!r}", 2)
    return int(m.group(1)), int(m.group(2))


def _img_limits() -> dict:
    return {**IMG_LIMITS_DEFAULT, **(_scfg("images.limits", {}) or {})}


def _img_size_facts(w: int, h: int) -> dict:
    """Whether the image API takes this size, by its documented rules (config static.images.limits), as facts."""
    lim = _img_limits()
    m, px, why = int(lim["multiple"]), w * h, []
    if w % m or h % m:
        why.append(f"both edges must be divisible by {m}")
    if max(w, h) > int(lim["max_edge"]):
        why.append(f"no edge over {lim['max_edge']}")
    if not (float(lim["ratio_min"]) <= w / h <= float(lim["ratio_max"])):
        why.append("the aspect must be between 1:3 and 3:1")
    if not (int(lim["min_pixels"]) <= px <= int(lim["max_pixels"])):
        why.append(f"the total pixels must be between {lim['min_pixels']} and {lim['max_pixels']}")
    return {"valid": not why, "why_not": why, "pixels": px, "experimental": px > int(lim["experimental_above_pixels"])}


def _fit_size(min_w: float, min_h: float, ratio: float, m: int) -> tuple:
    """The smallest size of multiples of m that covers min_w x min_h and keeps the ratio closest."""
    ws = [int(math.ceil(min_w / m - 1e-9)) * m + k * m for k in range(3)]
    hs = [int(math.ceil(min_h / m - 1e-9)) * m + k * m for k in range(3)]
    return min(((w, h) for w in ws for h in hs), key=lambda wh: (round(abs(wh[0] / wh[1] - ratio) / ratio, 3), wh[0] * wh[1]))


def _format_sizes(aspect: str, res: int, margin: float) -> dict:
    """For an aspect and a resolution (its short side: 1080, 720 ...): the export size (the CapCut canvas, even edges), the image size that
    stays sharp in that export through the stills' moves (each edge times 1 + the move's amount), the same without that margin, and the
    local check render's size (720 on the short side)."""
    aw, ah = STATIC_ASPECTS[aspect]
    ratio = aw / ah

    def by_short(short):
        return (short, int(round(short * ah / aw / 2.0)) * 2) if aw <= ah else (int(round(short * aw / ah / 2.0)) * 2, short)
    ew, eh = by_short(int(res))
    m = int(_img_limits()["multiple"])
    iw, ih = _fit_size(ew * (1 + margin), eh * (1 + margin), ratio, m)
    pw, ph = _fit_size(ew, eh, ratio, m)
    vw, vh = by_short(720)
    return {"aspect": aspect, "res": int(res), "export": f"{ew}x{eh}", "image_size": f"{iw}x{ih}", "image_size_no_margin": f"{pw}x{ph}",
            "preview": f"{vw}x{vh}", "image": _img_size_facts(iw, ih), "image_no_margin": _img_size_facts(pw, ph),
            "klein": _klein_size_facts(iw, ih), "klein_no_margin": _klein_size_facts(pw, ph)}


def _static_fmt(st: dict) -> dict:
    return ((st or {}).get("static") or {}).get("format") or {}


def _static_formats(a):
    """Facts for the format question (A5): each reference's size and aspect, the aspects by count and seconds, and per aspect (the
    references' own, then 9:16 and 16:9) and resolution (1080, 720) the export, the image sizes and whether the image API takes them."""
    rd, st = _state_of(a.run)
    try:
        inv = json.loads((rd / "00-inventory" / "inventory.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        inv = {}
    refs, by = [], {}
    for it in inv.get("items") or []:
        w, h = it.get("display_width"), it.get("display_height")
        if it.get("kind") != "video" or it.get("ignored") or not w or not h:
            continue
        asp, off = _aspect_of(w, h)
        refs.append({"id": it.get("id"), "file": it.get("rel") or it.get("path"), "size": f"{int(w)}x{int(h)}", "aspect": asp,
                     "aspect_off": off, "short_side": min(int(w), int(h)), "duration_s": it.get("duration_s")})
        b = by.setdefault(asp, {"count": 0, "seconds": 0.0, "short_sides": []})
        b["count"] += 1
        b["seconds"] = round(b["seconds"] + float(it.get("duration_s") or 0), 1)
        b["short_sides"].append(min(int(w), int(h)))
    margin = float(_scfg("render.motion_amount", 0.12))
    order = sorted(by, key=lambda k: (-by[k]["count"], -by[k]["seconds"]))
    aspects = list(dict.fromkeys(order + ["9:16", "16:9"]))
    out({"ok": True, "references": refs, "aspects": by, "move_margin": margin,
         "formats": [_format_sizes(asp, r, margin) for asp in aspects for r in (1080, 720)],
         "qualities": list(_scfg("images.qualities", ["low", "medium", "high", "xhigh", "max"])), "images": st.get("static_images"),
         "current": _static_fmt(st) or None,
         "note": "facts for the format question (reference/static §2): the export is the CapCut canvas (its export is the final), image_size "
                 "keeps it sharp through the moves, image_size_no_margin is smaller; `T static format` stores the pick"})


def _static_format_set(a):
    """Store the user's format pick in state.json -> static.format; the sizes follow from the aspect and the resolution."""
    rd, st = _state_of(a.run)
    if a.aspect not in STATIC_ASPECTS:
        fail("format needs --aspect " + " | ".join(STATIC_ASPECTS), 2)
    margin = float(_scfg("render.motion_amount", 0.12))
    fs = _format_sizes(a.aspect, int(a.res or 1080), margin)
    iw, ih = _parse_size(a.image_size or fs["image_size"])
    klein = st.get("static_images") == "klein"
    facts = _klein_size_facts(iw, ih) if klein else _img_size_facts(iw, ih)
    if not facts["valid"]:
        fail(f"{'FLUX 3 Klein' if klein else 'the image API'} does not take {iw}x{ih}: " + "; ".join(facts["why_not"]), 2, sizes=fs)
    ew, eh = _parse_size(a.export or fs["export"])
    if ew % 2 or eh % 2:
        fail(f"the export size needs even edges, got {ew}x{eh}", 2)
    quals = list(_scfg("images.qualities", ["low", "medium", "high", "xhigh", "max"]))
    q = a.quality or (None if st.get("static_images") in ("prompts", "klein") else _scfg("images.quality", "high"))
    if q and q not in quals:
        fail(f"--quality is one of {', '.join(quals)}", 2)
    fmt = {"aspect": a.aspect, "res": int(a.res or 1080), "export": f"{ew}x{eh}", "image_size": f"{iw}x{ih}", "quality": q,
           "preview": fs["preview"], "move_margin": margin,
           "image_aspect_off": round(abs(iw / ih - STATIC_ASPECTS[a.aspect][0] / STATIC_ASPECTS[a.aspect][1])
                                     / (STATIC_ASPECTS[a.aspect][0] / STATIC_ASPECTS[a.aspect][1]), 3),
           "image_experimental": bool(facts.get("experimental")), "set_at": now_iso()}
    _state_set(rd, **{"static.format": fmt})
    out({"ok": True, "format": fmt, "note": "the images (API or prompts file), the CapCut canvas (`T capcut-prep --canvas`) and the check render "
                                            "follow it; the final is the CapCut project exported at the export size"})


def cmd_static(a):
    """Static (contract item 36): check (the setup on this PC) | formats (facts for the format question) | format (store the pick)."""
    if a.action != "check" and not a.run:
        fail(f"static {a.action} needs --run", 2)
    {"check": _static_check, "formats": _static_formats, "format": _static_format_set}[a.action](a)


# ---- the local render: stills with motion, transitions, the narration and the bed, loudness; the preview with the captions burned

def _static_line_starts(side: dict) -> dict:
    return {int(r["n"]): float(r["start"]) for r in side.get("lines") or []}


def _slideshow_plan(a):
    """40-briefs/video-NN-timeline.json from the image plan (each image starts at its narration line) and the narration's exact line times;
    also the captions shifted onto the video's timeline (60-outputs/video-NN/captions.srt and .json) for CapCut and the preview."""
    rd, _st = _state_of(a.run)
    nn = _cf_nn(a.video)
    plan = _img_plan(rd, nn)
    imgs = plan.get("images") or []
    if not imgs:
        fail(f"no image plan for video {nn} (40-briefs/video-{nn}-images.json)", 2)
    try:
        side = json.loads((rd / "30-assets" / "narration" / f"video-{nn}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        fail(f"no narration for video {nn}: `T tts say` first", 2)
    lead = float(plan.get("lead_s", _scfg("narration.lead_s", 0.3)))
    tail = float(plan.get("tail_s", _scfg("narration.tail_s", 0.8)))
    starts = _static_line_starts(side)
    try:
        rec = json.loads((rd / "60-outputs" / f"video-{nn}" / "images.json").read_text(encoding="utf-8")).get("images") or {}
    except (OSError, ValueError):
        rec = {}
    folder = rd / "60-outputs" / f"video-{nn}" / "images"
    total = round(lead + float(side["duration_s"]) + tail, 3)
    cyc = list(_scfg("render.motions", ["zoom-in", "pan-right", "zoom-out", "pan-left"]))
    rows, missing_files, unknown_lines = [], [], []
    for i, im in enumerate(sorted(imgs, key=lambda x: int(x.get("image") or 0))):
        kk = f"{int(im.get('image') or 0):02d}"
        if im.get("start") is not None and im.get("from_line") is None:
            st_ = float(im["start"])
        elif int(im.get("from_line") or 0) in starts:
            st_ = lead + starts[int(im["from_line"])]
        else:
            unknown_lines.append(kk)
            st_ = None
        use = (rec.get(kk) or {}).get("use")
        f = folder / use if use else None
        if not f or not f.is_file():
            missing_files.append(kk)
        rows.append({"image": int(kk), "file": str(f) if f else None, "start": st_, "line": im.get("from_line"),
                     "motion": im.get("motion") or cyc[i % len(cyc)], "amount": float(im.get("amount", _scfg("render.motion_amount", 0.12))),
                     "transition": im.get("transition") or plan.get("transition") or _scfg("render.transition", "fade"),
                     "trans_s": float(im.get("trans_s", plan.get("trans_s", _scfg("render.transition_s", 0.4))))})
    if unknown_lines:
        fail("images whose from_line is not a narration line: " + ", ".join(unknown_lines), 2)
    rows[0]["start"] = 0.0
    for i, r in enumerate(rows):
        r["end"] = rows[i + 1]["start"] if i + 1 < len(rows) else total
    short = [r["image"] for r in rows if r["end"] - r["start"] < 0.5]
    music = rd / "30-assets" / "music" / f"video-{nn}.wav"
    cap = plan.get("captions") or {}
    tl = {"video": nn, "size": plan.get("render_size") or _static_fmt(_st).get("preview") or _scfg("render.size", "720x1280"),
          "export": _static_fmt(_st).get("export"), "fps": int(_scfg("render.fps", 30)),
          "narration": side["file"], "narration_offset": lead, "duration_s": total,
          "music": {"file": str(music), "gain": float(plan.get("music_gain", _scfg("music.gain", 0.22)))} if music.is_file() and plan.get("music", True) else None,
          "captions": {**cap, "y_rel": float(cap.get("y_rel", _scfg("captions.y_rel", 0.72))), "words": int(cap.get("words", _scfg("captions.words", 3)))},
          "images": rows, "made": now_iso()}
    tlp = rd / "40-briefs" / f"video-{nn}-timeline.json"
    write_json(tlp, tl)
    try:   # the cues are grouped again from the timed words at the plan's words at once, whatever narration-words was run with
        timed_words = json.loads((rd / "30-assets" / "narration" / f"video-{nn}.words.json").read_text(encoding="utf-8")).get("words") or []
    except (OSError, ValueError):
        timed_words = []
    try:
        cues = (chunk_words(timed_words, tl["captions"]["words"]) if timed_words else
                json.loads((rd / "30-assets" / "narration" / f"video-{nn}.cues.json").read_text(encoding="utf-8")))
    except (OSError, ValueError):
        cues = []
    upper = str(cap.get("case") or "").lower() == "upper"
    shifted = [{**c, "start": round(c["start"] + lead, 3), "end": round(c["end"] + lead, 3), "text": str(c["text"]).upper() if upper else c["text"]}
               for c in cues]
    od = rd / "60-outputs" / f"video-{nn}"
    write_json(od / "captions.json", shifted)
    srt = []
    for i, c in enumerate(shifted, 1):
        srt += [str(i), f"{_srt_time(c['start'])} --> {_srt_time(c['end'])}", c["text"], ""]
    write_text(od / "captions.srt", "\n".join(srt))
    out({"ok": not missing_files, "timeline": str(tlp), "duration_s": total, "images": len(rows), "image_spans": [[r["image"], r["start"], r["end"]] for r in rows],
         "shorter_than_0_5s": short, "images_without_a_file": missing_files, "captions": len(shifted), "captions_srt": str(od / "captions.srt"),
         "music": bool(tl["music"]), "note": "edit motions or transitions in the timeline file if the spec asks for others, then `T slideshow render`"})


def _zoompan(motion: str, amount: float, n: int) -> str:
    A, N = max(0.0, float(amount)), max(1, n - 1)
    cx, cy = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    z = {"zoom-in": f"1+{A}*on/{N}", "zoom-out": f"{1 + A}-{A}*on/{N}"}.get(motion, f"{1 + A}" if motion != "none" else "1")
    x = {"pan-right": f"(iw-iw/zoom)*on/{N}", "pan-left": f"(iw-iw/zoom)*(1-on/{N})"}.get(motion, cx)
    y = {"pan-down": f"(ih-ih/zoom)*on/{N}", "pan-up": f"(ih-ih/zoom)*(1-on/{N})"}.get(motion, cy)
    return f"z='{z}':x='{x}':y='{y}'"


def _static_caption_look(cap: dict, W: int) -> dict:
    """The references' caption look (the plan's captions block, static §2) for the check copy's burn: CapCut's size turned into pixels of
    this render (CAPCUT_FONT_PER_SIZE x size x width), the fill, the outline, the box, the font file. Empty: the house look stays."""
    look = {}
    if cap.get("font_file") and Path(str(cap["font_file"])).is_file():
        look["font_file"] = str(cap["font_file"])
    if cap.get("size"):
        look["size"] = max(8, int(round(CAPCUT_FONT_PER_SIZE * float(cap["size"]) * W)))
    if cap.get("fill"):
        look["primary"] = cap["fill"]
    if cap.get("stroke_color"):
        look["outline"] = cap["stroke_color"]
    if cap.get("stroke_width") is not None:
        look["outline_width"] = max(0, int(round(float(cap["stroke_width"]) * look.get("size", 40))))
    if cap.get("box_color"):
        look.update({"box": True, "box_color": cap["box_color"], "box_alpha": float(cap.get("box_alpha", 0.6))})
    if cap.get("bold") is not None:
        look["bold"] = bool(cap["bold"])
    if cap.get("shadow") is not None:
        look["shadow"] = 2 if cap["shadow"] else 0
    return look


def _slideshow_render(a):
    """The local render of a Static video from its timeline: each still scaled to cover the timeline's size (the format's check size), moved (zoom
    or pan), joined by its transitions
    so every image still starts on its line; the narration at its offset, the bed under it ducked, the whole at the target loudness.
    Writes deliverables/video-NN-clean.mp4 and, with the captions burned in the house look, video-NN-preview.mp4 (the complete video)."""
    rd, _st = _state_of(a.run)
    nn = _cf_nn(a.video)
    tlp = rd / "40-briefs" / f"video-{nn}-timeline.json"
    try:
        tl = json.loads(tlp.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        fail(f"no timeline for video {nn}: `T slideshow plan` first", 2)
    W, H = (int(x) for x in str(tl.get("size") or "720x1280").lower().split("x"))
    fps = int(tl.get("fps") or 30)
    rows = tl["images"]
    bad = [r["image"] for r in rows if not r.get("file") or not Path(r["file"]).is_file()]
    if bad:
        fail("images without a file: " + ", ".join(str(b) for b in bad), 2)
    empty = [r["image"] for r in rows if float(r["end"]) - float(r["start"]) <= 0]
    if empty:
        fail("images whose span is empty or negative (their start lines are out of order): " + ", ".join(str(b) for b in empty), 2)
    T = float(tl["duration_s"])
    args, fc = [find_tool("ffmpeg"), "-nostdin", "-y", "-loglevel", "error"], []
    for r in rows:
        args += ["-i", str(r["file"])]
    for k, r in enumerate(rows):
        d_in = 0.0 if k == 0 else max(1.0 / fps, float(rows[k]["trans_s"]) if rows[k]["transition"] != "cut" else 1.0 / fps)
        r["_d_in"] = d_in
        L = (float(r["end"]) - float(r["start"])) + d_in
        n = max(2, int(round(L * fps)))
        fc.append(f"[{k}:v]scale={2 * W}:{2 * H}:force_original_aspect_ratio=increase,crop={2 * W}:{2 * H},setsar=1,"
                  f"zoompan={_zoompan(r['motion'], r['amount'], n)}:d={n}:s={W}x{H}:fps={fps},trim=duration={L:.4f},setpts=PTS-STARTPTS,"
                  f"format=yuv420p[v{k}]")
    last = "v0"
    for k in range(1, len(rows)):
        tr = STATIC_TRANSITIONS.get(str(rows[k]["transition"]).lower(), "fade")
        off = float(rows[k - 1]["end"]) - rows[k]["_d_in"]
        fc.append(f"[{last}][v{k}]xfade=transition={tr}:duration={rows[k]['_d_in']:.4f}:offset={off:.4f}[x{k}]")
        last = f"x{k}"
    fc.append(f"[{last}]trim=duration={T:.4f},setpts=PTS-STARTPTS[vout]")
    ni = len(rows)
    args += ["-i", tl["narration"]]
    lead_ms = int(round(float(tl.get("narration_offset") or 0) * 1000))
    target = float(_scfg("narration.loudness_lufs", -14.0))
    mus = tl.get("music") or None
    if mus and Path(mus["file"]).is_file():
        args += ["-i", mus["file"]]
        fo = float(_scfg("music.fade_out_s", 3.0))
        fc.append(f"[{ni}:a]aresample=48000,adelay={lead_ms}|{lead_ms},apad=whole_dur={T:.3f},atrim=0:{T:.3f},asplit=2[narr][nsc]")
        fc.append(f"[{ni + 1}:a]aresample=48000,volume={float(mus.get('gain') or 0.22)},atrim=0:{T:.3f},apad=whole_dur={T:.3f},"
                  f"afade=t=out:st={max(0.0, T - fo):.3f}:d={fo:.3f}[mus]")
        fc.append("[mus][nsc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=350[duck]")
        fc.append(f"[narr][duck]amix=inputs=2:normalize=0:duration=first,loudnorm=I={target}:TP=-1.5:LRA=11,aresample=48000[aout]")
    else:
        fc.append(f"[{ni}:a]aresample=48000,adelay={lead_ms}|{lead_ms},apad=whole_dur={T:.3f},atrim=0:{T:.3f},"
                  f"loudnorm=I={target}:TP=-1.5:LRA=11,aresample=48000[aout]")
    dl = rd / "deliverables"
    dl.mkdir(parents=True, exist_ok=True)
    clean = dl / f"video-{nn}-clean.mp4"
    work = rd / "60-outputs" / f"video-{nn}" / "render"
    work.mkdir(parents=True, exist_ok=True)
    (work / "filter.txt").write_text(";\n".join(fc), encoding="utf-8")
    t0 = time.time()
    cp = run(args + ["-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]", "-r", str(fps), *_encode_args(18),
                     "-c:a", "aac", "-b:a", "192k", "-t", f"{T:.3f}", str(clean)], timeout=7200)
    if cp.returncode != 0 or not clean.is_file():
        fail("render failed: " + (cp.stderr or "")[-900:], 1, filter=str(work / "filter.txt"))
    res = {"ok": True, "clean": str(clean), "seconds": round(time.time() - t0, 1)}
    if not a.no_captions:
        try:
            cues = json.loads((rd / "60-outputs" / f"video-{nn}" / "captions.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            cues = []
        if cues:
            capl = tl.get("captions") or {}
            y = float(capl.get("y_rel", 0.72))
            spec = {"events": [{"start": c["start"], "end": c["end"], "text": c["text"], "preset": "caption", "pos": [0.5, y]} for c in cues]}
            look = _static_caption_look(capl, W)
            if look:
                spec["style"] = look
            if "animation" in capl:
                spec["animation"] = {"pop-up": "pop", "pop": "pop", "fade-in": "fade", "fade": "fade"}.get(str(capl.get("animation") or "").lower(), "none")
            (work / "fonts").mkdir(exist_ok=True)
            (work / "captions.ass").write_text(build_ass(spec, W, H, work / "fonts"), encoding="utf-8")
            prev = dl / f"video-{nn}-preview.mp4"
            cp = run([find_tool("ffmpeg"), "-nostdin", "-y", "-loglevel", "error", "-i", str(clean.resolve()), "-vf",
                      "subtitles=captions.ass:fontsdir=fonts", "-map", "0:v:0", "-map", "0:a?", *_encode_args(18), "-c:a", "copy",
                      str(prev.resolve())], cwd=str(work), timeout=7200)
            if cp.returncode != 0:
                fail("caption burn failed: " + cp.stderr[-600:], 1, clean=str(clean))
            res["preview"] = str(prev)
            res["captions"] = len(cues)
        else:
            res["preview"] = None
            res["captions"] = 0
    info = media_summary(clean)
    res.update({"duration_s": info.get("duration_s"), "size": f"{info.get('display_width')}x{info.get('display_height')}", "fps": info.get("fps"),
                "loudness_lufs": _ebur128(clean), "images": len(rows), "timeline": str(tlp)})
    write_json(rd / "60-outputs" / f"video-{nn}" / "slideshow.json", {**res, "made": now_iso()})
    out({**res, "note": "watch the preview: the captions, each image on its line, the motion; the CapCut project mirrors this timeline (reference/static §7)"})


def cmd_slideshow(a):
    """Static's local render (contract item 36): plan (the timeline from the image plan and the narration's line times; the captions on the
    video's timeline) | render (clean and preview mp4)."""
    {"plan": _slideshow_plan, "render": _slideshow_render}[a.action](a)


def main():
    ap = argparse.ArgumentParser(prog="awl.py", description=__doc__.split("\n\n")[0])
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
    p.add_argument("--note")
    p.add_argument("--flagged", action="store_true", help="set: mark this submission as flagged/refused by Higgsfield (then `caught-flag add`)")
    p.add_argument("--lane", help="lane override (default: the video number before any '-')")
    p.add_argument("--max-open", type=int, help="the cap that begin reports the open submissions against (default production.max_parallel_jobs)")
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
        p.add_argument("--fps", type=float, default=None,
                       help="baseline sampling rate (default: prep-all the run's effort level, state.json -> effort; else 5)")
        p.add_argument("--dense-fps", type=float, default=None,
                       help="rate around motion peaks and in the first second (default: the run's effort level; else 10)")
        p.add_argument("--static-threshold", type=float, default=cfg_get("analysis.static_threshold", 2.5),
                       help="mean abs grey difference (0-255) below which a frame counts as a static duplicate; 0 disables thinning")
        p.add_argument("--max-frames", type=int, default=cfg_get("analysis.max_baseline_frames", 1800))
        p.add_argument("--whisper-model", default=cfg_get("whisper_model", "small"))
        p.add_argument("--language", default="auto")
        p.add_argument("--no-ocr", action="store_true")
        p.add_argument("--ocr-frames", type=int, default=cfg_get("analysis.ocr_frames", 12))
        p.add_argument("--no-extras", action="store_true",
                       help="exactly --fps: no extra frames around cuts and motion peaks (Static samples the references at 1 fps only)")

    p = sp.add_parser("prep-video"); p.add_argument("video"); p.add_argument("--out", required=True)
    p.add_argument("--id")
    p.add_argument("--audio-ingest", choices=list(AUDIO_INGEST), help="the run's choice (state.json -> audio_ingest): whisper transcribes the audio; frames-only writes no transcript and says 'audio not ingested'")
    media_opts(p); p.set_defaults(fn=cmd_prep_video)

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
    p.add_argument("--grid", type=int, nargs="?", const=100, help="also write a gridded copy of each frame (lines every N source pixels, default 100, labelled in source coordinates)")
    p.add_argument("--max-side", type=int, default=1280); p.set_defaults(fn=cmd_frames)

    p = sp.add_parser("prep-image"); p.add_argument("image"); p.add_argument("--out", required=True)
    p.add_argument("--max-side", type=int, default=1280); p.set_defaults(fn=cmd_prep_image)

    p = sp.add_parser("doc-text"); p.add_argument("file"); p.add_argument("--out")
    p.add_argument("--images-out", help="PDF without a text layer: write its embedded page images into this folder (to view them one by one)")
    p.set_defaults(fn=cmd_doc_text)

    p = sp.add_parser("hf-put", help="upload a local file to a Higgsfield upload slot: --url (the presigned upload_url) or --capture (the hook's capture of the media_upload answer, so the URL is never copied by hand)")
    p.add_argument("--file", required=True); p.add_argument("--url", help="the upload_url of the media_upload answer")
    p.add_argument("--capture", help="the id of the hook capture that holds the media_upload answer (the hook prints it); the slot whose filename matches --file is used")
    p.add_argument("--slot", type=int, help="with --capture: which upload slot of the answer (0-based) when the filenames do not tell")
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
    p.add_argument("--voice", action="store_true", help="also the narrator's voice as numbers: pitch, voiced share, energy, words per minute, pauses (Static)")
    p.add_argument("--out", required=True); p.add_argument("--transcript", help="10-media/<V>/transcript.json")
    p.add_argument("--cuts", help="10-media/<V>/cuts.json"); p.set_defaults(fn=cmd_audio_profile)

    p = sp.add_parser("split-audio"); p.add_argument("paths", nargs="+", help="the given video folder(s)/file(s)")
    p.add_argument("--run"); p.add_argument("--redo", action="store_true")
    p.add_argument("--audio-only", action="store_true", help="files_audio/ only, no silent copies (Analyze Create)")
    p.set_defaults(fn=cmd_split_audio)

    p = sp.add_parser("finalize"); p.add_argument("--run", required=True); p.add_argument("--file", required=True)
    p.add_argument("--original", required=True, help="the ORIGINAL video path (as in the inventory)")
    p.add_argument("--video", help="V id, for the run record"); p.add_argument("--expect-size", default="720x1280")
    p.set_defaults(fn=cmd_finalize)

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
    p.add_argument("--fps", type=float, default=30.0)
    p.add_argument("--tol", type=float, default=0.10, help="list the windows whose offset is beyond this many seconds (a list on request, not a verdict)")
    p.add_argument("--min-corr", type=float, default=0.5, help="the summary uses only the windows whose correlation is at least this (all windows stay listed)")
    p.add_argument("--min-motion", type=float, default=0.25, help="the summary uses only the windows whose motion is at least this share of the whole segment's")
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
    p.add_argument("--dry-run", action="store_true", help="report lost_fraction (the share of the picture a crop removes) and write nothing")
    p.add_argument("--crf", type=int, default=18); p.set_defaults(fn=cmd_conform)

    p = sp.add_parser("captions"); p.add_argument("--video", required=True); p.add_argument("--out", required=True)
    p.add_argument("--spec", help="JSON: {style, presets, safe_area, uppercase, animation, events:[{start,end,text,preset,pos,animation}]}")
    p.add_argument("--from-speech", action="store_true", help="time captions to the clip's own speech (speech-to-text: only when the run chose whisper)")
    p.add_argument("--run", help="the run (reads state.json -> audio_ingest for --from-speech)")
    p.add_argument("--audio-ingest", choices=list(AUDIO_INGEST), help="without --run: the choice --from-speech must honour")
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
    p.add_argument("--label", help="product name for the printed line")
    p.add_argument("--distance", type=float, help="camera-to-product distance in metres (from the shot size)")
    p.add_argument("--distance-basis", help="how --distance was derived from the frame (surface, neighbour, depth order); recorded with the numbers")
    p.add_argument("--lens", type=float, default=26.0, help="35 mm-equivalent focal length (phone main lens ≈ 26)")
    p.add_argument("--frame-h", type=int, default=1280, help="frame height in px (default 1280 for 720×1280)")
    p.add_argument("--frame", help="a full-resolution frame; its height overrides --frame-h")
    p.add_argument("--product-px", help="observed product height on the frame: 'y0-y1' rows or a pixel height")
    p.add_argument("--ref-cm", type=float, help="a neighbour's real height in cm (hand, bottle, phone, mug …)")
    p.add_argument("--ref-px", help="the neighbour's observed height on the same frame: 'y0-y1' or px")
    p.add_argument("--depth-ratio", type=float, default=1.0, help="product distance / neighbour distance (1 = same depth)")
    p.add_argument("--out", help="write the result as JSON")
    p.set_defaults(fn=cmd_scale)

    p = sp.add_parser("caught-flag", help="the flag record in Loupe (the web app): add | list | set | reconcile | open")
    p.add_argument("action", choices=["add", "list", "set", "reconcile", "open"])
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
    p.add_argument("--no-facts", action="store_true", help="add: skip the on-screen-text (OCR) facts of the inputs (hashes and sizes are still gathered)")
    p.add_argument("--capture", help="add: the id of a hook capture (the raw Higgsfield response saved when it came back) to attach; a capture whose job id matches --job is attached by itself")
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

    p = sp.add_parser("loupe", help="the Loupe web app: ensure | status | open")
    p.add_argument("action", choices=["ensure", "status", "open"]); p.add_argument("--path", help="open: a page, e.g. /#/misses")
    p.set_defaults(fn=cmd_loupe)

    for _nm, _h in (("qc-consult", "QC phase only: ask the QC keeper which generation-miss samples apply to the video under QC"),
                    ("qc-brief", "QC phase only: the matching generation-miss samples as a plain brief (no model call)")):
        p = sp.add_parser(_nm, help=_h)
        p.add_argument("--run", help="run id or folder (reads the model and mode from its state.json)"); p.add_argument("--video", help="video number")
        p.add_argument("--model"); p.add_argument("--mode"); p.add_argument("--product", help="the product and its form, free text")
        p.add_argument("--product-details", help="its shape, size, opening and natural posture, from its registry row: samples are matched to this video by what the products have in common")
        p.add_argument("--kinds", help="comma-separated kinds you suspect (counts, openings-use, permanence, scale-size, label-orientation, solidity, blend-paste, posture-place, identity, continuity …)")
        p.add_argument("--question", help="what you see or suspect in the video under QC, in words (needed for qc-consult)")
        p.add_argument("--checkpoint", action="append", help="a QC checkpoint of the plan to check against the samples; repeatable")
        p.add_argument("--note", help="only when a first answer came back with needs_unmet: what you saw when you looked at your own video, in words (the keeper asked for it)")
        p.add_argument("--attempt", help="qc-consult: the take under QC (a1, a2, c2-a1 ...): picks the request whose prompt is sent to the judge (the newest otherwise)")
        p.set_defaults(fn=cmd_qc_consult, cmd=_nm)

    p = sp.add_parser("prompt-template", help="first request of a video (X4b, after X1-X4): the whole checked brief (your words, the checked draft request, its must-carry lines, the model's structure) to the judge (Loupe's keeper, Opus); it reads the saved prompts of the samples it chooses and answers the final prompt")
    p.add_argument("--run", help="run id or folder (reads the model and mode from its state.json)"); p.add_argument("--video", help="video number")
    p.add_argument("--model"); p.add_argument("--mode"); p.add_argument("--product", help="the product and its form, free text")
    p.add_argument("--product-details", help="its shape, size, opening and natural posture, from its registry row")
    p.add_argument("--brief", help="the brief, in words (or --brief-file)")
    p.add_argument("--brief-file", help="the brief as a file (default RUN/40-briefs/video-NN[-cK]-judge-brief.md): what you are working on, what the video is about, what it wants to achieve, one line per beat")
    p.add_argument("--clip", help="a clip of a multi-clip video (c1, c2 ...): its own draft, must-carry lines and prompt")
    p.add_argument("--draft-file", help="the checked draft request (default RUN/50-requests/video-NN[-cK]-request.draft.json, else the request)")
    p.add_argument("--musts-file", help="the lines the prompt must carry word for word, one per line (default RUN/40-briefs/video-NN[-cK]-musts.md)")
    p.add_argument("--structure-file", help="the locked model's request structure: the pattern card RUN/50-requests/video-NN-pattern.md")
    p.add_argument("--note", help="only when a first answer came back with needs_unmet: your answer from the plan, in words (the judge asked for it)")
    p.set_defaults(fn=cmd_prompt_template, kinds=None)

    p = sp.add_parser("template-apply", help="X4b: the judge's final prompt into the request word for word (the checked draft kept beside it); fills slots; reports the must-carry lines missing, the slots left and the length")
    p.add_argument("--run", required=True); p.add_argument("--video", required=True)
    p.add_argument("--clip", help="a clip of a multi-clip video (c1, c2 ...)")
    p.add_argument("--request", help="the request file (default RUN/50-requests/video-NN[-cK]-request.json)")
    p.add_argument("--musts-file", help="the must-carry lines (default RUN/40-briefs/video-NN[-cK]-musts.md)")
    p.add_argument("--slot", action="append", help='"<slot words>=<value>": fills [SLOT: <slot words>] with a value the plan already decided; repeatable')
    p.add_argument("--add-must", action="append", help="a must-carry line the judge left out after being asked again: added word for word at the end; repeatable")
    p.add_argument("--use-draft", action="store_true", help="put the checked draft back as the request (no usable judge's prompt)")
    p.set_defaults(fn=cmd_template_apply)

    p = sp.add_parser("product-images", help="a regeneration (QC fix): the judge's product images from its QC answer into the regeneration's request (images added after the last one or the last ones left out, never both; facts first, --apply writes)")
    p.add_argument("--run", required=True); p.add_argument("--video", required=True)
    p.add_argument("--request", required=True, help="the regeneration's own request file (never one the ledger holds)")
    p.add_argument("--answer", help="the QC answer with the judge's product_images (default RUN/60-outputs/video-NN/qc-consult.json)")
    p.add_argument("--musts-file", help="the must-carry lines, to see which name a product image")
    p.add_argument("--apply", action="store_true", help="write the plan into the request (the request as it was is kept beside it once)")
    p.set_defaults(fn=cmd_product_images)

    p = sp.add_parser("plan-hints", help="first request of a video only (X2): ask the keeper which past misses could matter for the plan (text-only hints, usually none)")
    p.add_argument("--run", help="run id or folder (reads the model and mode from its state.json)"); p.add_argument("--video", help="video number")
    p.add_argument("--model"); p.add_argument("--mode"); p.add_argument("--product", help="the product and its form, free text")
    p.add_argument("--product-details", help="its shape, size, opening and natural posture, from its registry row")
    p.add_argument("--beats", help="one line per beat of the plan: what happens, the product's form and state, the camera (2000 characters at most)")
    p.add_argument("--note", help="only when a first answer came back with needs_unmet: your answer from the plan, in words (the keeper asked for it)")
    p.set_defaults(fn=cmd_plan_hints, kinds=None)

    p = sp.add_parser("sample-prompts", help="the prompts of ONE sample, each named by what it is (the flawed version's, the correct version's, or an Examples sample's one example box; only the boxes and generations its frames come from; as the admin saved them in Loupe), written whole to RUN/40-briefs/samples/<id>-prompts.md for you to read and judge; only for a sample you judged relevant")
    p.add_argument("--id", required=True, help="the sample id (S12) from qc-consult, qc-brief or plan-hints")
    p.add_argument("--run", required=True, help="run id or folder: the file is written under its 40-briefs/samples/")
    p.set_defaults(fn=cmd_sample_prompts)

    p = sp.add_parser("status", help="where a run stands, from its files (gather-only): stage, next_skill, videos and submissions by status, credits recorded, Loupe, missing files")
    p.add_argument("--run", required=True); p.add_argument("--no-loupe", action="store_true", help="do not ask Loupe whether it is running")
    p.set_defaults(fn=cmd_status)

    p = sp.add_parser("doctor", help="what this machine and library have (read-only, one JSON line): python, ffmpeg, modules, config paths, MCP registration, hooks, Loupe, docs check, git, disk; --run adds the run's stage keys")
    p.add_argument("--run"); p.add_argument("--no-loupe", action="store_true"); p.add_argument("--no-docs", action="store_true", help="skip docs_tool check")
    p.set_defaults(fn=cmd_doctor)

    p = sp.add_parser("lint-run", help="cross-checks of a run's files as facts (gather-only): cited paths that do not exist, video numbers vs asset_plan, media ids vs uploads, prompt lengths, preset bookkeeping, the contract")
    p.add_argument("--run", required=True); p.set_defaults(fn=cmd_lint_run)

    p = sp.add_parser("uploads", help="one record per video of the uploads made for it (video-NN-uploads.json, one schema): set | show | merge into state.json -> assets.uploads")
    p.add_argument("action", choices=["set", "show", "merge"]); p.add_argument("--run", required=True); p.add_argument("--video")
    p.add_argument("--label", help="set: the input's label as the request names it (e.g. 'Image 2' or the asset id)")
    p.add_argument("--media-id", help="set: the media id Higgsfield returned"); p.add_argument("--file", help="set: the local file that was uploaded")
    p.add_argument("--content-type"); p.add_argument("--url", help="set: the public url Higgsfield returned"); p.add_argument("--role", help="set: the role the request gives it")
    p.set_defaults(fn=cmd_uploads)

    p = sp.add_parser("contract", help="write 50-requests/agent-contract.md from the canonical prompt (production-agents section 2) and state.json; lists the placeholders it could not fill")
    p.add_argument("--run", required=True); p.add_argument("--notes", help="run-specific notes, appended under their own heading at the end")
    p.add_argument("--out", help="write elsewhere than 50-requests/agent-contract.md"); p.set_defaults(fn=cmd_contract)

    p = sp.add_parser("voiceover", help="own voiceover (contract item 31): outdir (the folder the ElevenLabs MCP may write to) | record (a take into the run, "
                                        "measured; its sidecar; state.json -> voiceover.files) | align (where the model's own speech lies against the take) | "
                                        "mix (the take over the picture, plus a placed track for CapCut); facts, no verdict")
    p.add_argument("action", choices=["outdir", "record", "align", "mix"])
    p.add_argument("--run", help="outdir, record: the run")
    p.add_argument("--base", help="outdir: the ElevenLabs MCP's base path (default: ELEVENLABS_MCP_BASE_PATH, else ~/Desktop)")
    p.add_argument("--video", help="record: the video, NN or NN-cK")
    p.add_argument("--file", help="record: the take the ElevenLabs MCP saved, or the user's own voiceover file (source file)")
    p.add_argument("--attempt", type=int, default=1, help="record: the take's number (a1, a2 ...)")
    p.add_argument("--span", help="record: START-END seconds of --file to take (a clip's part of one longer file, cut at a pause; written as WAV)")
    p.add_argument("--script", help="record: the text sent to ElevenLabs, tags included (a file path or the text); for a user's file, its words")
    p.add_argument("--transcribe", action="store_true", help="record, a user's file without a script: its words by local speech-to-text (a client asset, not the references' audio)")
    p.add_argument("--whisper-model", default=cfg_get("whisper_model", "small"), help="record --transcribe: the faster-whisper model")
    p.add_argument("--language", help="record: the take's ISO 639-1 code (also the speech-to-text hint)")
    p.add_argument("--voice-id", help="record: the ElevenLabs voice id"); p.add_argument("--voice-name", help="record: the voice's name")
    p.add_argument("--model", help="record: the ElevenLabs model id (eleven_v4 ...)")
    p.add_argument("--preference", help="record: the accent, dialect or delivery preference the take follows")
    p.add_argument("--settings", help="record: the voice settings sent, as JSON")
    p.add_argument("--mode", choices=list(VO_MODES), help="record: on-camera (lip-synced) or off-screen")
    p.add_argument("--source", choices=list(VO_SOURCES), default="elevenlabs", help="record: elevenlabs (voiced by the pipeline) or file (the user's own file)")
    p.add_argument("--generated", help="align: the clean picture that still carries the generation's own sound (or a raw, trimmed or joined clip)")
    p.add_argument("--voiceover", help="align, mix: the take")
    p.add_argument("--out", help="align: a folder for vo-align.json and vo-align.png; mix: the output .mp4 (a .vo-track.wav goes beside it)")
    p.add_argument("--max-lag", type=float, default=1.0, help="align: largest offset searched, seconds")
    p.add_argument("--window", type=float, default=2.0, help="align: window for the per-window offsets, seconds")
    p.add_argument("--tol", type=float, default=0.10, help="align: list the used windows whose offset differs from the global one by more than this (a list, not a verdict)")
    p.add_argument("--min-corr", type=float, default=0.3, help="align: the summary uses the windows whose correlation is at least this")
    p.add_argument("--min-voice", type=float, default=0.25, help="align: ... and whose loudness variation is at least this share of the whole take's (pauses are left out)")
    p.add_argument("--picture", help="mix: the clean picture (720x1280) the take goes over")
    p.add_argument("--offset", type=float, default=0.0, help="mix: where the take starts on the picture's timeline, seconds (negative: its head is cut)")
    p.add_argument("--tempo", type=float, default=1.0, help="mix: the take's speed without a pitch change (atempo), e.g. 1.05")
    p.add_argument("--bed", choices=["mute", "keep"], default="mute", help="mix: the picture's own sound: mute (on-camera: the model's voice never stays) or keep (off-screen: ambience under the voice)")
    p.add_argument("--bed-gain", type=float, default=0.3, help="mix --bed keep: the picture's own sound level")
    p.add_argument("--vo-gain", type=float, default=1.0, help="mix: the take's level")
    p.set_defaults(fn=cmd_voiceover)

    p = sp.add_parser("effort", help="the run's effort level (contract item 33): show it, or set --level low|medium|high|xhigh|max and custom "
                                     "values (held to the floors); prep-all and the produce phase read it from state.json -> effort")
    p.add_argument("--run", required=True); p.add_argument("--level", choices=list(EFFORT_LEVELS))
    p.add_argument("--analysis-fps", type=float, help="references: baseline frames per second (floor 2)")
    p.add_argument("--analysis-dense-fps", type=float, help="references: around motion peaks and in the first second (floor 6)")
    p.add_argument("--densify-ranges", type=int, help="references: densified ranges per video at analysis time (floor 2)")
    p.add_argument("--motion-peaks", type=int, help="references: motion peaks densified per video, +-0.5 s each (floor 4)")
    p.add_argument("--max-agents", type=int, help="production agents at once (1 to 5)")
    p.add_argument("--pilot-from", type=int, help="the pilot runs first from this many videos (2 to 5)")
    p.set_defaults(fn=cmd_effort)

    p = sp.add_parser("cost-report", help="credits as the run recorded them (information, never a gate): credits_start, jobs from videos[], submissions, brief mentions, --balance")
    p.add_argument("--run", required=True); p.add_argument("--balance", type=float, help="the Higgsfield balance now (from the balance tool), to print start minus balance")
    p.set_defaults(fn=cmd_cost_report)

    p = sp.add_parser("capcut-name"); p.add_argument("--video", required=True, help="the run's video number")
    p.add_argument("--date", help="YYYY-MM-DD (default: today)"); p.add_argument("--store", help="CapCut drafts dir")
    p.set_defaults(fn=cmd_capcut_name)

    p = sp.add_parser("capcut-font", help="Static: --list the fonts on this PC (CapCut's own first) | set one font file on a draft's texts")
    p.add_argument("--list", action="store_true", help="list the font files (family, style, file, source)")
    p.add_argument("--family", help="list: only families containing this")
    p.add_argument("--draft", help="the CapCut draft folder"); p.add_argument("--font-file", help="the font file (from --list)")
    p.add_argument("--track", help="only the texts on the track with this name (e.g. subtitle, the import-srt default)")
    p.set_defaults(fn=cmd_capcut_font)

    p = sp.add_parser("capcut-prep"); p.add_argument("--draft", required=True, help="the freshly cloned draft folder")
    p.add_argument("--canvas", help="WxH: the project's canvas (Static: state.json -> static.format.export); default: the template's")
    p.set_defaults(fn=cmd_capcut_prep)

    p = sp.add_parser("capcut-repair"); p.add_argument("--draft", required=True)
    p.add_argument("--keep-text", action="store_true", help="leave every text as it is (Static: the references' look, never the house style)")
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

    p = sp.add_parser("seams", help="per-frame luma and frame difference 0.5 s around cut points (numbers only): a flash or a dissolve at a cut shows here")
    p.add_argument("--video", required=True); p.add_argument("--at", help="times in seconds, comma-separated")
    p.add_argument("--map", help="a strip-inserts map.json: profile its split points (the own timeline), or with --source its source_in/out in the original")
    p.add_argument("--source", action="store_true", help="with --map: --video is the ORIGINAL; profile source_in and source_out")
    p.add_argument("--half", type=float, default=0.5, help="seconds either side of each point (default 0.5)")
    p.add_argument("--rows", action="store_true", help="print every frame row (default: the summary; rows always go to --out)")
    p.add_argument("--out", help="write the full profile as JSON"); p.set_defaults(fn=cmd_seams)

    p = sp.add_parser("clean"); p.add_argument("--video", required=True); p.add_argument("--out", required=True)
    p.add_argument("--delogo", action="append", help="x,y,w,h[@t0-t1] (0-1 fractions or pixels); repeatable")
    p.add_argument("--crop", help="x,y,w,h (0-1 fractions or pixels) — keep this region")
    p.add_argument("--crf", type=int, default=18); p.set_defaults(fn=cmd_clean)

    p = sp.add_parser("static", help="Static (contract item 36): check (key present, image model answers, FLUX 3 Klein's install and files, TTS "
                                     "and music environments, whisper, ffmpeg filters, capcut-cli) | formats (facts for the format question "
                                     "at A5) | format (store the pick)")
    p.add_argument("action", choices=["check", "formats", "format"]); p.add_argument("--run")
    p.add_argument("--offline", action="store_true", help="check: do not ask the image API whether the model answers")
    p.add_argument("--aspect", help="format: 9:16 | 16:9 | 1:1 | 4:5 | 3:4 | 4:3")
    p.add_argument("--res", type=int, help="format: the export's short side, e.g. 1080 or 720 (default 1080)")
    p.add_argument("--quality", help="format: the image API's quality, low | medium | high | xhigh | max (prompts mode: none)")
    p.add_argument("--image-size", help="format: WxH instead of the computed image size (e.g. the size without the move margin)")
    p.add_argument("--export", help="format: WxH instead of the computed export size")
    p.set_defaults(fn=cmd_static)

    p = sp.add_parser("image", help="Static stills (contract item 36): generate (OpenAI Images API, or FLUX 3 Klein on this PC with "
                                    "static_images=klein; ledgered) | prompts (the file a user makes them from) | intake (the user's folder, "
                                    "copied in) | use (which attempt the edit takes)")
    p.add_argument("action", choices=["generate", "prompts", "intake", "use"]); p.add_argument("--run", required=True)
    p.add_argument("--video", help="the video, NN"); p.add_argument("--image", type=int, help="generate, use: the image's number in the video's plan")
    p.add_argument("--anchor", help="generate, use: a character's anchor image (its id, e.g. C1) instead of a video's image")
    p.add_argument("--prompt-file", help="generate: the prompt, a text file"); p.add_argument("--prompt", help="generate: the prompt as text")
    p.add_argument("--ref", action="append", help="generate: a reference image (a character photo or anchor), repeatable, at most 16 "
                                                  "(FLUX 3 Klein: 10)")
    p.add_argument("--engine", choices=["api", "klein"], help="generate: default the run's state.json -> static_images (klein, else api)")
    p.add_argument("--seed", type=int, help="generate, FLUX 3 Klein: a seed (default one from the request and the attempt, recorded)")
    p.add_argument("--no-upsample", action="store_true", help="generate, FLUX 3 Klein: the prompt already is a full scene caption, so "
                                                              "Black Forest Labs' prompt upsampler is skipped")
    p.add_argument("--model", help="generate: default config static.images.model")
    p.add_argument("--size", help="generate: WxH, both divisible by 16 (default the run's format, state.json -> static.format)")
    p.add_argument("--quality", help="generate: low | medium | high | xhigh | max (default the run's format)")
    p.add_argument("--again", action="store_true", help="generate: a new draw of a request that already made an image")
    p.add_argument("--timeout", type=float, help="generate: seconds to wait for the answer (default config: 300 for the API, 1800 for FLUX 3 Klein)")
    p.add_argument("--folder", help="intake: the folder holding the user's images (named vNN-iKK)")
    p.add_argument("--attempt", type=int, help="use: the attempt the edit takes")
    p.set_defaults(fn=cmd_image)

    p = sp.add_parser("tts", help="Static's voice (contract item 36): check | design (voice samples) | voice (the picked sample becomes the run's "
                                  "voice) | say (a video's narration); Qwen3-TTS in its own environment (AWL_TTS_PYTHON), one GPU job at a time")
    p.add_argument("action", choices=["check", "design", "voice", "say"]); p.add_argument("--run")
    p.add_argument("--text", help="design: the line every sample speaks")
    p.add_argument("--instruct", action="append", help="design: one voice described in words, repeatable (one sample each)")
    p.add_argument("--language", help="design: english | spanish | ... (default config static.tts.language)")
    p.add_argument("--sample", type=int, help="voice: the sample the user picked")
    p.add_argument("--emotion", action="append", help="voice: NAME=TEXT, a reference clip of the same voice for lines tagged NAME, repeatable")
    p.add_argument("--video", help="say: the video, NN"); p.add_argument("--lines-file", help="say: default 40-briefs/video-NN-narration.json")
    p.add_argument("--only", help="say: make only these line numbers again, e.g. 3,7")
    p.set_defaults(fn=cmd_tts)

    p = sp.add_parser("narration-words", help="Static: a narration's words and times (speech-to-text timing, the script's wording), caption cues, "
                                              "an SRT, and per line how the heard words differ from the script (facts)")
    p.add_argument("--run", required=True); p.add_argument("--video", required=True)
    p.add_argument("--words", type=int, help="words per caption (default config static.captions.words)")
    p.add_argument("--min-match", type=float, default=0.85, help="list the lines whose heard share of their script words is below this")
    p.add_argument("--whisper-model", default=cfg_get("whisper_model", "small"))
    p.set_defaults(fn=cmd_narration_words)

    p = sp.add_parser("music", help="Static's bed (contract item 36), only when the plan calls for one: check | make (ACE-Step 1.5 in its own "
                                    "environment, AWL_MUSIC_PYTHON and AWL_MUSIC_ROOT)")
    p.add_argument("action", choices=["check", "make"]); p.add_argument("--run")
    p.add_argument("--plan", help="make: default 40-briefs/music.json"); p.add_argument("--video", help="make: only this video's track")
    p.set_defaults(fn=cmd_music)

    p = sp.add_parser("slideshow", help="Static's local render (contract item 36): plan (the timeline from the image plan and the narration's line "
                                        "times) | render (clean and captioned preview mp4)")
    p.add_argument("action", choices=["plan", "render"]); p.add_argument("--run", required=True); p.add_argument("--video", required=True)
    p.add_argument("--no-captions", action="store_true", help="render: the clean file only")
    p.set_defaults(fn=cmd_slideshow)

    a = ap.parse_args()
    if getattr(a, "run", None) and a.cmd not in ("caught-flag", "qc-consult", "qc-brief", "plan-hints", "prompt-template"):
        a.run = str(resolve_run(a.run))     # a bare run name or a stamp prefix becomes the run folder (caught-flag list keeps the text filter)
    try:
        a.fn(a)
    except SystemExit:
        raise
    except Exception as e:
        fail(f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
