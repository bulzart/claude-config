"""create-clips on-screen reading for game matches (CS2, Dota 2 and other broadcasts): hud-read, hud-scan, region-series.

Gather-only: they crop a region of the recorded chunks, read the text in it (OCR) or measure it (mean colour, change from one sample to the
next) and write the numbers. No label, rank or verdict comes out of them (no "round started", no "highlight"): the agent decides what a
text or a change means. A region is x,y,w,h as FRACTIONS of the frame (0..1); measure it on a `cc.py grid-frame` picture.

Frames are never kept: the crop and the scale are done by ffmpeg and the samples travel through a pipe, one at a time; `hud-read` alone
writes one small PNG (the cropped, preprocessed region) so the agent can look at what the OCR saw. hud-scan reads several regions in ONE
pass over the video (--spec), because decoding the video is most of the time.
Details: docs/hud.md.
"""
from __future__ import annotations

import heapq
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from cc_common import (chunk_dir, fail, ffprobe_facts, find_tool, fmt_hms, load_chunks, out, parse_time, read_json, rec_to_chunk,
                       resolve_run, run_paths, say, split_across_chunks)

KINDS = ("digits", "text", "auto")
DIGIT_FIX = str.maketrans({"O": "0", "o": "0", "Q": "0", "D": "0", "I": "1", "l": "1", "|": "1", "i": "1", "S": "5", "s": "5", "B": "8", "Z": "2", "z": "2"})
NUMERIC_CHARS = set("0123456789:.,/-+% $") | set("OoQDIl|iSsBZz")
CHANGE_LEVELS = 40          # a pixel counts as changed when it moved by more than this (of 255)
_DIMS: dict = {}


def _np():
    import numpy as np
    return np


# --------------------------------------------------------------------------- arguments

def parse_region(text) -> tuple:
    try:
        v = [float(x) for x in (str(text).replace(";", ",").split(",") if isinstance(text, str) else list(text))]
    except (ValueError, TypeError):
        fail(f"cannot read the region {text!r}: use x,y,w,h as fractions of the frame, e.g. 0.40,0.05,0.20,0.10")
    if len(v) != 4:
        fail(f"a region is four numbers x,y,w,h (fractions of the frame), got {len(v)} in {text!r}")
    x, y, w, h = v
    if not (0 <= x < 1 and 0 <= y < 1 and 0 < w <= 1 and 0 < h <= 1 and x + w <= 1.0001 and y + h <= 1.0001):
        fail(f"the region {text!r} is outside the frame: x,y,w,h are fractions inside 0..1 and x+w and y+h are at most 1 (measure it on `cc.py grid-frame`)")
    return x, y, w, h


def region_px(region: tuple, width: int, height: int) -> tuple:
    """(x, y, w, h) in pixels: even sizes of at least 2, kept inside the frame."""
    x, y, w, h = region
    cw = min(width - width % 2, max(2, int(round(w * width / 2)) * 2))
    ch = min(height - height % 2, max(2, int(round(h * height / 2)) * 2))
    cx = max(0, min(width - cw, int(round(x * width / 2)) * 2))
    cy = max(0, min(height - ch, int(round(y * height / 2)) * 2))
    return cx, cy, cw, ch


def scaled_size(cw: int, ch: int, scale: float) -> tuple:
    return max(2, int(round(cw * scale / 2)) * 2), max(2, int(round(ch * scale / 2)) * 2)


def safe_name(name) -> str:
    n = re.sub(r"[^A-Za-z0-9_.-]", "_", str(name or "").strip())[:60].strip("._")
    if not n:
        fail("a name is needed (letters, digits, - and _)")
    return n


def chunk_dims(run: Path, cid: str) -> tuple:
    key = (str(run), cid)
    if key not in _DIMS:
        pr = read_json(chunk_dir(run, cid) / "probe.json", None) or {}
        if not pr.get("width"):
            pr = ffprobe_facts(chunk_dir(run, cid) / "chunk.mp4")
        if not pr.get("width") or not pr.get("height"):
            fail(f"cannot read the frame size of {cid}")
        _DIMS[key] = (int(pr["width"]), int(pr["height"]))
    return _DIMS[key]


def clamp_range(rows: list, a_from, a_to) -> tuple:
    done = [r for r in rows if r.get("duration_s") and r.get("rec_start_s") is not None]
    if not done:
        fail("the run has no processed chunks")
    start = min(r["rec_start_s"] for r in done)
    end = max(r["rec_start_s"] + r["duration_s"] for r in done)
    t0 = start if a_from in (None, "") else parse_time(a_from, rows)
    t1 = end if a_to in (None, "") else parse_time(a_to, rows)
    t0, t1 = max(t0, start), min(t1, end)
    if t1 - t0 <= 1e-6:
        fail(f"no recorded content in that range (the recording runs from {fmt_hms(start)} to {fmt_hms(end)})")
    return t0, t1


def sample_pieces(rows: list, t0: float, t1: float, step: float) -> list:
    """The range cut per chunk, each piece with its first sample on the grid t0 + k*step (the grid runs on across chunk boundaries) and the
    chunk offset of that sample. A sample is taken at each grid time strictly before the end of its chunk."""
    pieces = []
    for pc in split_across_chunks(rows, t0, t1):
        k0 = max(0, math.ceil((pc["rec_from"] - t0) / step - 1e-9))
        first = t0 + k0 * step
        if first >= pc["rec_to"] - 1e-6:
            continue
        pieces.append({"chunk": pc["chunk"], "first": first, "offset": pc["offset_from"] + (first - pc["rec_from"]), "rec_to": pc["rec_to"],
                       "dur": pc["rec_to"] - first, "n": int(math.floor((pc["rec_to"] - first - 1e-6) / step)) + 1})
    return pieces


def coverage(rows: list, t0: float, t1: float) -> dict:
    got = sum(pc["rec_to"] - pc["rec_from"] for pc in split_across_chunks(rows, t0, t1))
    return {"range": [round(t0, 3), round(t1, 3)], "recorded_s": round(got, 3), "holes_s": round(max(0.0, (t1 - t0) - got), 3)}


# --------------------------------------------------------------------------- ffmpeg pipe

class PieceStream:
    """One ffmpeg process for one chunk piece, its samples read one at a time from a pipe (rawvideo). Nothing is written to disk."""

    def __init__(self, chunk_file: Path, offset: float, dur: float, vf: str, pix_fmt: str, shape: tuple, complex_graph: bool = False):
        self.shape = shape
        self.nbytes = int(shape[0]) * int(shape[1]) * (int(shape[2]) if len(shape) > 2 else 1)
        self.err = tempfile.TemporaryFile()
        cmd = [find_tool("ffmpeg"), "-hide_banner", "-loglevel", "error", "-nostdin", "-ss", f"{offset:.3f}", "-t", f"{dur:.3f}", "-i", str(chunk_file), "-an", "-sn", "-dn"]
        cmd += (["-filter_complex", vf, "-map", "[out]"] if complex_graph else ["-vf", vf])
        cmd += ["-f", "rawvideo", "-pix_fmt", pix_fmt, "pipe:1"]
        self.p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=self.err, stdin=subprocess.DEVNULL, bufsize=1 << 20)

    def frames(self):
        np = _np()
        while True:
            buf = self.p.stdout.read(self.nbytes)
            if len(buf) < self.nbytes:
                return
            yield np.frombuffer(buf, dtype=np.uint8).reshape(self.shape)

    def close(self) -> str:
        try:
            if self.p.poll() is None:
                self.p.kill()
            self.p.wait(timeout=30)
        except Exception:  # noqa: BLE001
            pass
        try:
            self.p.stdout.close()
        except Exception:  # noqa: BLE001
            pass
        try:
            self.err.seek(0)
            tail = self.err.read()[-300:].decode("utf-8", "replace").strip()
        except Exception:  # noqa: BLE001
            tail = ""
        try:
            self.err.close()
        except Exception:  # noqa: BLE001
            pass
        return tail


class StreamJson:
    """{...header, "rows":[ one row per line ], "summary": {...}} written row by row to NAME.json.part and renamed at the end: memory stays flat
    for hours of samples."""

    def __init__(self, path: Path, header: dict):
        self.path = Path(path)
        self.part = self.path.with_name(self.path.name + ".part")
        self.part.parent.mkdir(parents=True, exist_ok=True)
        self.f = open(self.part, "w", encoding="utf-8")
        self.f.write(json.dumps(header, ensure_ascii=False)[:-1] + ',"rows":[\n')
        self.n = 0

    def row(self, obj) -> None:
        self.f.write(("," if self.n else "") + json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")
        self.n += 1

    def close(self, summary: dict) -> None:
        self.f.write('],"summary":' + json.dumps(summary, ensure_ascii=False) + "}\n")
        self.f.close()
        os.replace(self.part, self.path)

    def abort(self) -> None:
        try:
            self.f.close()
            self.part.unlink(missing_ok=True)
        except OSError:
            pass


# --------------------------------------------------------------------------- OCR

_OCR = None


def get_ocr():
    global _OCR
    if _OCR is not None:
        return _OCR
    try:
        from rapidocr_onnxruntime import RapidOCR  # type: ignore
        _OCR = RapidOCR()
    except Exception as e:  # noqa: BLE001
        fail(f"rapidocr-onnxruntime cannot be used in this Python ({type(e).__name__}: {str(e)[:120]}). It is part of the pipeline's Python312 tooling: "
             f"`& \"{sys.executable}\" -m pip install rapidocr-onnxruntime` (onnxruntime comes with it)", 3)
    return _OCR


def preprocess(gray, threshold, invert):
    """The grayscale sample as the OCR sees it: pixels at or above `threshold` white and the rest black, then optionally inverted."""
    np = _np()
    g = gray
    if threshold is not None:
        g = np.where(g >= int(threshold), 255, 0).astype(np.uint8)
    if invert:
        g = 255 - g
    return g


def _box_extent(box) -> tuple:
    xs, ys = [p[0] for p in box], [p[1] for p in box]
    return min(xs), min(ys), max(xs), max(ys)


def recognise(ocr, gray, kind: str, fallback: bool = True) -> tuple:
    """(raw text, mean confidence, boxes, method) of a grayscale region. digits: recognition-only first (about 30 times faster than detect + recognise
    and right for one line of digits, light on dark or dark on light); when that finds nothing or is unsure and `fallback` is on, detect + recognise
    too (about 0.5 s, and on a busy picture it is paid at every sample, so hud-scan has it off unless asked). text and auto: detect + recognise,
    recognition-only when no text is detected. Boxes are in the pixels of the image given; method is rec, det+rec or none."""
    np = _np()
    if float(gray.std()) < 5.0:          # no contrast in the crop (the box is hidden, or the threshold took everything): nothing to read, and no invented digit
        return "", 0.0, [], "none"
    bgr = np.repeat(gray[:, :, None], 3, axis=2)

    def rec_only():
        pad = max(6, gray.shape[0] // 8)
        img = np.pad(bgr, ((pad, pad), (pad, pad), (0, 0)), mode="edge")
        r, _ = ocr(img, use_det=False, use_cls=False, use_rec=True)
        if not r:
            return "", 0.0, []
        text = " ".join(str(x[0]).strip() for x in r if str(x[0]).strip())
        conf = sum(float(x[1]) for x in r) / len(r)
        return text, conf, [{"text": text, "conf": round(conf, 2), "box": [0, 0, int(gray.shape[1]), int(gray.shape[0])]}]

    def det_rec():
        r, _ = ocr(bgr, use_cls=False)
        if not r:
            return "", 0.0, []
        items = sorted(((_box_extent(b), str(t).strip(), float(s)) for b, t, s in r if str(t).strip()), key=lambda i: (i[0][0], i[0][1]))
        if not items:
            return "", 0.0, []
        text = " ".join(i[1] for i in items)
        conf = sum(i[2] for i in items) / len(items)
        return text, conf, [{"text": i[1], "conf": round(i[2], 2), "box": [int(v) for v in i[0]]} for i in items]
    if kind == "digits":
        t, c, b = rec_only()
        if not fallback or (t.strip() and c >= 0.5):
            return t, c, b, "rec"
        t2, c2, b2 = det_rec()
        return (t2, c2, b2, "det+rec") if (t2.strip() and (c2 > c or not t.strip())) else (t, c, b, "rec")
    t, c, b = det_rec()
    if t.strip():
        return t, c, b, "det+rec"
    t, c, b = rec_only()
    return t, c, b, "rec"


def clean_text(raw: str, kind: str, regex) -> str:
    t = " ".join(str(raw).split())
    numeric = kind == "digits" or (kind == "auto" and t and set(t) <= NUMERIC_CHARS and any(ch in "0123456789" for ch in t))
    if numeric:
        t = t.translate(DIGIT_FIX).replace(" ", "")
    if regex is not None:
        m = regex.search(t)
        t = m.group(0) if m else ""
    return t


def numeric_value(t: str):
    """'1:55' -> 115, '-0:45' -> -45, '0:07.5' -> 7.5, '1:02:03' -> 3723, '7' -> 7, '12.5' -> 12.5, '$4,750' -> 4750; None when no number is in the text."""
    s = t.strip()
    m = re.fullmatch(r"(-?)(\d+):(\d{2})(?::(\d{2}))?(?:[.,](\d+))?", s)
    if m:
        secs = (int(m.group(2)) * 3600 + int(m.group(3)) * 60 + int(m.group(4))) if m.group(4) is not None else (int(m.group(2)) * 60 + int(m.group(3)))
        if m.group(5):
            secs += float("0." + m.group(5))
        v = -secs if m.group(1) else secs
        return int(v) if float(v).is_integer() else v
    m = re.search(r"-?\d{1,3}(?:,\d{3})+(?:\.\d+)?", s) or re.search(r"-?\d+(?:[.,]\d+)?", s)
    if m:
        v = float(m.group(0).replace(",", "") if re.search(r",\d{3}", m.group(0)) else m.group(0).replace(",", "."))
        return int(v) if v.is_integer() else v
    return None


def reader_opts(raw: dict) -> dict:
    kind = str(raw.get("kind") or "digits").lower()
    if kind not in KINDS:
        fail(f"kind is one of {', '.join(KINDS)}")
    try:
        scale = float(3.0 if raw.get("scale") is None else raw["scale"])
        thr = None if raw.get("threshold") in (None, "") else int(raw["threshold"])
    except (TypeError, ValueError):
        fail("scale is a number and threshold an integer")
    if not 0.2 <= scale <= 12:
        fail("scale is between 0.2 and 12 (the crop is enlarged by it before the OCR; 3 is the default)")
    if thr is not None and not 0 <= thr <= 255:
        fail("threshold is between 0 and 255")
    src = raw.get("regex") or None
    try:
        rx = re.compile(src) if src else None
    except re.error as e:
        fail(f"regex is not a valid pattern: {e}")
    return {"kind": kind, "scale": scale, "threshold": thr, "invert": bool(raw.get("invert")), "regex_src": src, "regex": rx, "numeric": bool(raw.get("numeric")),
            "fallback": bool(raw.get("fallback"))}


def args_opts(a) -> dict:
    return reader_opts({"kind": a.kind, "scale": a.scale, "threshold": a.threshold, "invert": a.invert, "regex": a.regex, "numeric": a.numeric,
                        "fallback": getattr(a, "fallback", False)})


def idle_changed(ref, g, frac: float) -> bool:
    """True when the sample differs enough from the last read one to be read again: at least `frac` of its pixels moved by more than CHANGE_LEVELS."""
    if ref is None or frac <= 0 or ref.shape != g.shape:
        return True
    np = _np()
    d = np.abs(g.astype(np.int16) - ref.astype(np.int16))
    return int(np.count_nonzero(d > CHANGE_LEVELS)) >= max(1.0, frac * d.size)


# --------------------------------------------------------------------------- hud-read

def cmd_hud_read(a):
    t_start = time.time()
    run = resolve_run(a.run)
    rows = load_chunks(run)
    t = parse_time(a.at, rows)
    region = parse_region(a.region)
    o = args_opts(a)
    cid, off = rec_to_chunk(rows, t)
    if not cid:
        fail(f"rec time {t} is not inside a recorded chunk")
    ocr = get_ocr()
    W, H = chunk_dims(run, cid)
    cx, cy, cw, ch = region_px(region, W, H)
    sw, sh = scaled_size(cw, ch, o["scale"])
    vf = f"crop={cw}:{ch}:{cx}:{cy},scale={sw}:{sh}:flags=lanczos,format=gray"
    stream = PieceStream(chunk_dir(run, cid) / "chunk.mp4", off, 5.0, vf, "gray", (sh, sw))
    try:
        frame = next(stream.frames(), None)
    finally:
        err = stream.close()
    if frame is None:
        fail(f"ffmpeg could not read a frame of {cid} at +{off:.2f}: {err}", 1)
    g = preprocess(frame, o["threshold"], o["invert"])
    from PIL import Image
    tag = (f"-t{o['threshold']}" if o["threshold"] is not None else "") + ("-inv" if o["invert"] else "") + ("" if o["scale"] == 3.0 else f"-s{o['scale']:g}")
    dest = run_paths(run)["assets"] / "frames" / f"hud-{int(round(t * 100)):08d}-{region[0]:.3f}_{region[1]:.3f}_{region[2]:.3f}_{region[3]:.3f}{tag}.png"
    dest.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(g).save(dest)
    raw, conf, boxes, method = recognise(ocr, g, o["kind"], True)
    text = clean_text(raw, o["kind"], o["regex"])
    res = {"ok": True, "rec": round(t, 3), "rec_hms": fmt_hms(t), "chunk": cid, "offset": off, "region": list(region), "region_px": [cx, cy, cw, ch],
           "source_size": [W, H], "kind": o["kind"], "scale": o["scale"], "invert": o["invert"], "threshold": o["threshold"], "text": text, "raw": raw.strip(),
           "confidence": round(conf, 2), "method": method, "boxes": boxes, "image": str(dest).replace("\\", "/"), "seconds": round(time.time() - t_start, 2),
           "note": "the image is what the OCR saw (cropped, enlarged, grayscale, thresholded or inverted when asked); adjust --scale/--threshold/--invert until the text reads right, then hud-scan "
                   "(method rec = the quick digit read worked; det+rec = it needed the slow detect step: then scan with --fallback or --kind text)"}
    if o["numeric"]:
        res["value"] = numeric_value(text)
    out(res)


# --------------------------------------------------------------------------- hud-scan

class Reader:
    """One region read over the whole range: its options, its output files and its running state (the last read sample, the previous text)."""

    def __init__(self, name: str, region: tuple, opts: dict, idle: float, hud_dir: Path, header: dict):
        self.name, self.region, self.o, self.idle = name, region, opts, idle
        self.json_path, self.txt_path = hud_dir / f"{name}.json", hud_dir / f"{name}.txt"
        self.txt_part = self.txt_path.with_name(self.txt_path.name + ".part")
        self.sj = StreamJson(self.json_path, {"name": name, "region": list(region), "kind": opts["kind"], "scale": opts["scale"], "invert": opts["invert"],
                                              "threshold": opts["threshold"], "regex": opts["regex_src"], "numeric": opts["numeric"], "fallback": opts["fallback"],
                                              "idle_frac": idle, **header})
        self.txt = open(self.txt_part, "w", encoding="utf-8")
        self.samples = self.ocr_calls = self.reused = self.nchanges = 0
        self.ocr_seconds = 0.0
        self.changes_first: list = []
        self.first_rec = self.last_rec = None
        self.prev_text = None
        self.last_ref = None
        self.last_res = ("", 0.0)

    def feed(self, ocr, frame, rec: float, cid: str, t_chunk: float) -> None:
        g = preprocess(frame, self.o["threshold"], self.o["invert"])
        if idle_changed(self.last_ref, g, self.idle):
            t_ocr = time.time()
            raw, conf, _, _ = recognise(ocr, g, self.o["kind"], self.o["fallback"])
            self.ocr_seconds += time.time() - t_ocr
            self.ocr_calls += 1
            self.last_ref, self.last_res, was_reused = g.copy(), (raw, conf), False
        else:
            raw, conf = self.last_res
            self.reused += 1
            was_reused = True
        text = clean_text(raw, self.o["kind"], self.o["regex"])
        row = {"rec": round(rec, 3), "chunk": cid, "t_chunk": round(t_chunk, 3), "text": text, "conf": round(conf, 2), "reused": was_reused}
        if self.o["numeric"]:
            row["value"] = numeric_value(text)
        if raw.strip() != text:
            row["raw"] = raw.strip()
        self.sj.row(row)
        if text != self.prev_text:
            self.txt.write(f"{fmt_hms(rec)}  {text if text else '(none)'}\n")
            if self.prev_text is not None:
                self.nchanges += 1
                if len(self.changes_first) < 20:
                    self.changes_first.append([round(rec, 3), self.prev_text, text])
            self.prev_text = text
        self.samples += 1
        if self.first_rec is None:
            self.first_rec = round(rec, 3)
        self.last_rec = round(rec, 3)

    def finish(self, ok: bool, wall: float) -> dict:
        self.txt.close()
        if not ok:
            self.sj.abort()
            self.txt_part.unlink(missing_ok=True)
            return {}
        summary = {"samples": self.samples, "ocr_calls": self.ocr_calls, "reused": self.reused, "changes": self.nchanges, "ocr_seconds": round(self.ocr_seconds, 2),
                   "first_rec": self.first_rec, "last_rec": self.last_rec, "seconds": round(wall, 2)}
        self.sj.close(summary)
        os.replace(self.txt_part, self.txt_path)
        return {"name": self.name, "files": [str(self.json_path), str(self.txt_path)], "region": list(self.region), "kind": self.o["kind"], **summary,
                "changes_first": self.changes_first}


def load_readers(a, hud_dir: Path, header: dict) -> list:
    base = {"kind": a.kind, "scale": a.scale, "threshold": a.threshold, "invert": a.invert, "regex": a.regex, "numeric": a.numeric, "fallback": a.fallback}
    if a.spec:
        spec = read_json(a.spec, None)
        if isinstance(spec, dict):
            spec = spec.get("readers") or spec.get("regions")
        if not isinstance(spec, list) or not spec:
            fail(f"--spec {a.spec} must be a JSON list of {{name, region, [kind, scale, threshold, invert, regex, numeric]}} (or {{\"readers\": [...]}})")
    else:
        if not a.region or not a.name:
            fail("hud-scan needs --region and --name, or --spec FILE with several regions")
        spec = [{"name": a.name, "region": a.region}]
    readers, seen = [], set()
    for i, s in enumerate(spec):
        if not isinstance(s, dict) or "region" not in s:
            fail(f"reader {i + 1} of the spec needs a name and a region")
        name = safe_name(s.get("name"))
        if name in seen:
            fail(f"the name {name!r} is used twice")
        seen.add(name)
        readers.append((name, parse_region(s["region"]), reader_opts({**base, **{k: v for k, v in s.items() if k not in ("name", "region")}})))
    return [Reader(n, rg, op, float(a.idle_frac), hud_dir, header) for n, rg, op in readers]


def scan_graph(geoms: list, step: float) -> tuple:
    """(filter, is_complex, frame shape, [(x offset, w, h) of each reader in the frame]): one reader = one crop; several = crops padded to the
    tallest and joined side by side, so one decode serves all of them."""
    fps = f"fps={1.0 / step:.9f}"
    if len(geoms) == 1:
        (cx, cy, cw, ch), (sw, sh) = geoms[0]
        return f"{fps},crop={cw}:{ch}:{cx}:{cy},scale={sw}:{sh}:flags=lanczos,format=gray", False, (sh, sw), [(0, sw, sh)]
    n = len(geoms)
    hmax = max(sh for _, (sw, sh) in geoms)
    parts, slots, off = [], [], 0
    for i, ((cx, cy, cw, ch), (sw, sh)) in enumerate(geoms):
        parts.append(f"[s{i}]crop={cw}:{ch}:{cx}:{cy},scale={sw}:{sh}:flags=lanczos,pad={sw}:{hmax}:0:0[r{i}]")
        slots.append((off, sw, sh))
        off += sw
    graph = f"[0:v]{fps},split={n}" + "".join(f"[s{i}]" for i in range(n)) + ";" + ";".join(parts) + ";" + "".join(f"[r{i}]" for i in range(n)) + f"hstack=inputs={n},format=gray[out]"
    return graph, True, (hmax, off), slots


def cmd_hud_scan(a):
    t_start = time.time()
    run = resolve_run(a.run)
    rows = load_chunks(run)
    step = float(a.step)
    if step <= 0:
        fail("--step is a positive number of seconds")
    t0, t1 = clamp_range(rows, a.from_, a.to)
    hud_dir = run_paths(run)["analysis"] / "hud"
    hud_dir.mkdir(parents=True, exist_ok=True)
    readers = None
    ok = False
    warnings: list = []
    samples = 0
    try:
        readers = load_readers(a, hud_dir, {"step": step, "from": round(t0, 3), "to": round(t1, 3)})
        ocr = get_ocr()
        for pc in sample_pieces(rows, t0, t1, step):
            W, H = chunk_dims(run, pc["chunk"])
            geoms = []
            for r in readers:
                px = region_px(r.region, W, H)
                geoms.append((px, scaled_size(px[2], px[3], r.o["scale"])))
            vf, cplx, shape, slots = scan_graph(geoms, step)
            say(f"[hud-scan] {pc['chunk']} from {fmt_hms(pc['first'])}: {pc['n']} samples, {len(readers)} region(s)")
            stream = PieceStream(chunk_dir(run, pc["chunk"]) / "chunk.mp4", pc["offset"], pc["dur"], vf, "gray", shape, cplx)
            got = 0
            try:
                for k, frame in enumerate(stream.frames()):
                    rec = pc["first"] + k * step
                    if rec >= pc["rec_to"] - 1e-6:
                        break
                    got += 1
                    for r, (x0, w, h) in zip(readers, slots):
                        r.feed(ocr, frame[:h, x0:x0 + w], rec, pc["chunk"], pc["offset"] + k * step)
                    samples += 1
            finally:
                err = stream.close()
            if got < pc["n"] - 1:
                warnings.append(f"{pc['chunk']}: ffmpeg gave {got} of {pc['n']} samples" + (f" ({err})" if err else ""))
        ok = True
    finally:
        wall = time.time() - t_start
        results = [r.finish(ok, wall) for r in (readers or [])]
    out({"ok": True, "readers": results, "samples": samples, "step": step, **coverage(rows, t0, t1), "seconds": round(wall, 2), "warnings": warnings,
         "note": "[rec, from, to] in changes_first are the first 20 changes of each text; the full list is each reader's .txt (only the rows where the text changed)"})


# --------------------------------------------------------------------------- region-series

def cmd_region_series(a):
    t_start = time.time()
    run = resolve_run(a.run)
    rows = load_chunks(run)
    regions = [parse_region(r) for r in a.region]
    step = float(a.step)
    if step <= 0:
        fail("--step is a positive number of seconds")
    try:
        sw, sh = [int(v) for v in str(a.size).lower().split("x")]
        assert sw >= 2 and sh >= 2
    except (ValueError, AssertionError):
        fail("--size is WxH of the reduced crop each region is measured on (default 64x36)")
    t0, t1 = clamp_range(rows, a.from_, a.to)
    name = safe_name(a.name)
    np = _np()
    hud_dir = run_paths(run)["analysis"] / "hud"
    hud_dir.mkdir(parents=True, exist_ok=True)
    json_path, txt_path = hud_dir / f"{name}-series.json", hud_dir / f"{name}-series.txt"
    n = len(regions)
    sj = StreamJson(json_path, {"name": name, "regions": [list(r) for r in regions], "step": step, "size": [sw, sh], "columns": ["r", "g", "b", "luma", "diff"],
                                "from": round(t0, 3), "to": round(t1, 3)})
    diffs = [[] for _ in range(n)]
    tops = [[] for _ in range(n)]            # heaps of (diff, seq, rec, luma): the 30 largest
    prev = [None] * n
    seq = samples = 0
    first_rec = last_rec = None
    warnings: list = []
    ok = False
    try:
        for pc in sample_pieces(rows, t0, t1, step):
            W, H = chunk_dims(run, pc["chunk"])
            pxs = [region_px(r, W, H) for r in regions]
            fps = f"fps={1.0 / step:.9f}"
            if n == 1:
                cx, cy, cw, ch = pxs[0]
                vf, cplx = f"{fps},crop={cw}:{ch}:{cx}:{cy},scale={sw}:{sh}:flags=area,format=rgb24", False
            else:
                split = f"[0:v]{fps},split={n}" + "".join(f"[s{i}]" for i in range(n))
                parts = [f"[s{i}]crop={px[2]}:{px[3]}:{px[0]}:{px[1]},scale={sw}:{sh}:flags=area[r{i}]" for i, px in enumerate(pxs)]
                vf, cplx = split + ";" + ";".join(parts) + ";" + "".join(f"[r{i}]" for i in range(n)) + f"hstack=inputs={n},format=rgb24[out]", True
            say(f"[region-series] {pc['chunk']} from {fmt_hms(pc['first'])}: {pc['n']} samples, {n} region(s)")
            stream = PieceStream(chunk_dir(run, pc["chunk"]) / "chunk.mp4", pc["offset"], pc["dur"], vf, "rgb24", (sh, sw * n, 3), cplx)
            got = 0
            try:
                for k, frame in enumerate(stream.frames()):
                    rec = pc["first"] + k * step
                    if rec >= pc["rec_to"] - 1e-6:
                        break
                    got += 1
                    vals = []
                    for i in range(n):
                        crop = frame[:, i * sw:(i + 1) * sw, :]
                        r_, g_, b_ = (float(crop[:, :, c].mean()) for c in range(3))
                        luma = 0.299 * r_ + 0.587 * g_ + 0.114 * b_
                        d = None if prev[i] is None else float(np.abs(crop.astype(np.int16) - prev[i].astype(np.int16)).mean())
                        prev[i] = crop.copy()
                        vals.append([round(r_, 1), round(g_, 1), round(b_, 1), round(luma, 1), None if d is None else round(d, 2)])
                        if d is not None:
                            diffs[i].append(d)
                            item = (d, seq, round(rec, 3), round(luma, 1))
                            if len(tops[i]) < 30:
                                heapq.heappush(tops[i], item)
                            elif item > tops[i][0]:
                                heapq.heapreplace(tops[i], item)
                    seq += 1
                    sj.row({"rec": round(rec, 3), "chunk": pc["chunk"], "t": round(pc["offset"] + k * step, 3), "v": vals})
                    samples += 1
                    if first_rec is None:
                        first_rec = round(rec, 3)
                    last_rec = round(rec, 3)
            finally:
                err = stream.close()
            if got < pc["n"] - 1:
                warnings.append(f"{pc['chunk']}: ffmpeg gave {got} of {pc['n']} samples" + (f" ({err})" if err else ""))
        ok = True
    finally:
        if not ok:
            sj.abort()
    report, lines = [], []
    for i, rg in enumerate(regions):
        top = sorted(((rec, round(d, 2), luma) for d, _, rec, luma in tops[i]), key=lambda x: x[0])
        pct = {f"p{p}": round(float(np.percentile(diffs[i], p)), 2) for p in (50, 90, 99)} if diffs[i] else {}
        report.append({"region": list(rg), "samples_with_diff": len(diffs[i]), "diff_mean": round(float(np.mean(diffs[i])), 2) if diffs[i] else None,
                       "percentiles": pct, "top30_by_diff_in_time_order": [[r, d, l] for r, d, l in top]})
        lines.append(f"region {i + 1}: {','.join(f'{v:.4f}'.rstrip('0').rstrip('.') for v in rg)}  (rec, diff, luma of the {len(top)} samples with the largest diff, in time order)")
        lines += [f"{fmt_hms(r)}  diff {d:.2f}  luma {l:.1f}" for r, d, l in top]
        lines.append("")
    txt_path.write_text("\n".join(lines), encoding="utf-8")
    summary = {"samples": samples, "regions": n, "first_rec": first_rec, "last_rec": last_rec, "seconds": round(time.time() - t_start, 2)}
    sj.close({**summary, "per_region": report})
    out({"ok": True, "name": name, "files": [str(json_path), str(txt_path)], **summary, **coverage(rows, t0, t1), "per_region": report, "step": step, "size": [sw, sh],
         "warnings": warnings,
         "note": "diff = mean absolute difference (0..255) of the reduced crop against the previous sample; numbers only, what a change means is for the agent to read from the frames"})


# --------------------------------------------------------------------------- register

def _opts(p) -> None:
    p.add_argument("--kind", choices=list(KINDS), default="digits", help="digits (default: the quick recognition-only read, about 30x faster), text (detect + recognise) or auto")
    p.add_argument("--scale", type=float, default=3.0, help="enlarge the crop by this factor before the OCR (default 3)")
    p.add_argument("--invert", action="store_true", help="invert the grayscale crop (after --threshold)")
    p.add_argument("--threshold", type=int, help="0..255: pixels at or above it become white, the rest black (before --invert)")
    p.add_argument("--regex", help="keep the first match of this pattern in the text, e.g. '^\\d{1,2}$' (a score) or '\\d{1,2}:\\d{2}' (a clock); no match = empty text")
    p.add_argument("--numeric", action="store_true", help="also give the number the text holds (a clock 1:55 = 115, a score 7 = 7)")


def register(sub) -> None:
    p = sub.add_parser("hud-read", help="OCR of one region at one rec time (calibrate a region before a scan); keeps the cropped image")
    p.add_argument("--run", required=True)
    _opts(p)
    p.add_argument("--at", required=True, help="rec time (seconds, H:MM:SS.cc or C0012+45.75)")
    p.add_argument("--region", required=True, help="x,y,w,h as fractions of the frame (0..1)")
    p.set_defaults(func=cmd_hud_read)

    p = sub.add_parser("hud-scan", help="OCR of one or several regions over a range of the recording (clock, score ...) in one pass: a text per sample and the changes")
    p.add_argument("--run", required=True)
    _opts(p)
    p.add_argument("--region", help="x,y,w,h as fractions of the frame (0..1) of the one region; several regions: --spec")
    p.add_argument("--name", help="output name of the one region: 20-analysis/hud/<name>.json and .txt")
    p.add_argument("--spec", help="JSON list of regions to read in the same pass: [{name, region:[x,y,w,h], kind, scale, threshold, invert, regex, numeric, fallback}]; the options above are the defaults of each entry")
    p.add_argument("--from", dest="from_", help="rec time to start at (default: the start of the recording)")
    p.add_argument("--to", help="rec time to stop at, exclusive (default: the end of the recording)")
    p.add_argument("--step", type=float, default=1.0, help="seconds between samples (default 1.0)")
    p.add_argument("--idle-frac", dest="idle_frac", type=float, default=0.002,
                   help="a sample is not read again when fewer than this fraction of its pixels moved (by more than 40 of 255) against the last read one; 0 = read every sample (default 0.002)")
    p.add_argument("--fallback", action="store_true", help="digits: when the quick read is empty or unsure also try detect + recognise (about 0.5 s a sample, paid at every sample while the box is hidden: off by default)")
    p.set_defaults(func=cmd_hud_scan)

    p = sub.add_parser("region-series", help="mean colour and change from sample to sample of one or more regions over a range (no OCR)")
    p.add_argument("--run", required=True)
    p.add_argument("--region", action="append", required=True, help="x,y,w,h as fractions of the frame; repeat for several regions")
    p.add_argument("--from", dest="from_", help="rec time to start at (default: the start of the recording)")
    p.add_argument("--to", help="rec time to stop at, exclusive (default: the end of the recording)")
    p.add_argument("--step", type=float, default=0.5, help="seconds between samples (default 0.5)")
    p.add_argument("--name", required=True, help="the output name: 20-analysis/hud/<name>-series.json and .txt")
    p.add_argument("--size", default="64x36", help="the reduced size each region is measured on (default 64x36)")
    p.set_defaults(func=cmd_region_series)
