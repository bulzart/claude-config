"""create-clips on-screen reading for game matches (CS2, Dota 2 and other broadcasts): hud-read, hud-scan, region-series.

Gather-only: they crop a region of the recorded chunks, read the text in it (OCR) or measure it (mean colour, change from one sample to the
next) and write the numbers. No label, rank or verdict comes out of them (no "round started", no "highlight"): the agent decides what a
text or a change means. A region is x,y,w,h as FRACTIONS of the frame (0..1); measure it on a `cc.py grid-frame` picture.

Frames are never kept: the crop and the scale are done by ffmpeg and the samples travel through a pipe, one at a time; `hud-read` alone
writes one small PNG (the cropped, preprocessed region) so the agent can look at what the OCR saw.
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
                       resolve_run, run_cmd, run_paths, say, split_across_chunks)

KINDS = ("digits", "text", "auto")
DIGIT_FIX = str.maketrans({"O": "0", "o": "0", "Q": "0", "D": "0", "I": "1", "l": "1", "|": "1", "i": "1", "S": "5", "s": "5", "B": "8", "Z": "2", "z": "2"})
NUMERIC_CHARS = set("0123456789:.,/-+% ") | set("OoQDIl|iSsBZz")


def _np():
    import numpy as np
    return np


# --------------------------------------------------------------------------- arguments

def parse_region(text) -> tuple:
    try:
        v = [float(x) for x in str(text).replace(";", ",").split(",")]
    except ValueError:
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


def safe_name(name: str) -> str:
    n = re.sub(r"[^A-Za-z0-9_.-]", "_", str(name or "").strip())[:60].strip("._")
    if not n:
        fail("--name is needed (letters, digits, - and _)")
    return n


def chunk_dims(run: Path, cid: str) -> tuple:
    pr = read_json(chunk_dir(run, cid) / "probe.json", None) or {}
    if not pr.get("width"):
        pr = ffprobe_facts(chunk_dir(run, cid) / "chunk.mp4")
    if not pr.get("width") or not pr.get("height"):
        fail(f"cannot read the frame size of {cid}")
    return int(pr["width"]), int(pr["height"])


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


# --------------------------------------------------------------------------- ffmpeg pipe

class PieceStream:
    """One ffmpeg process for one chunk piece, its samples read one at a time from a pipe (rawvideo). Nothing is written to disk."""

    def __init__(self, chunk_file: Path, offset: float, dur: float, vf: str, pix_fmt: str, shape: tuple, complex_graph: bool = False, step: float = 1.0):
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


def recognise(ocr, gray, kind: str) -> tuple:
    """(raw text, mean confidence, boxes) of a grayscale region. digits: recognition-only first (about 30 times faster than detect + recognise and
    right for one line of digits), detect + recognise when that finds nothing; text and auto: detect + recognise, recognition-only when no text
    is detected. Boxes are in the pixels of the image given."""
    np = _np()
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
        r, _ = ocr(bgr)
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
        return (t, c, b) if t.strip() else det_rec()
    t, c, b = det_rec()
    return (t, c, b) if t.strip() else rec_only()


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
    """'1:55' -> 115, '0:07.5' -> 7.5, '1:02:03' -> 3723, '7' -> 7, '12.5' -> 12.5; None when no number is in the text."""
    m = re.fullmatch(r"\s*(\d+):(\d{2}):(\d{2})\s*", t)
    if m:
        return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
    m = re.fullmatch(r"\s*(\d+):(\d{2})(?:[.,](\d+))?\s*", t)
    if m:
        v = int(m.group(1)) * 60 + int(m.group(2)) + (float("0." + m.group(3)) if m.group(3) else 0.0)
        return int(v) if float(v).is_integer() else v
    m = re.search(r"-?\d+(?:[.,]\d+)?", t)
    if m:
        v = float(m.group(0).replace(",", "."))
        return int(v) if v.is_integer() else v
    return None


def read_args(a) -> tuple:
    kind = str(a.kind or "digits").lower()
    if kind not in KINDS:
        fail(f"--kind is one of {', '.join(KINDS)}")
    scale = float(a.scale)
    if not 0.2 <= scale <= 12:
        fail("--scale is between 0.2 and 12 (the crop is enlarged by it before the OCR; 3 is the default)")
    thr = None if a.threshold is None else int(a.threshold)
    if thr is not None and not 0 <= thr <= 255:
        fail("--threshold is between 0 and 255")
    try:
        rx = re.compile(a.regex) if a.regex else None
    except re.error as e:
        fail(f"--regex is not a valid pattern: {e}")
    return kind, scale, thr, bool(a.invert), rx


def gray_vf(cx: int, cy: int, cw: int, ch: int, scale: float, fps: float | None) -> tuple:
    sw, sh = max(2, int(round(cw * scale / 2)) * 2), max(2, int(round(ch * scale / 2)) * 2)
    head = f"fps={fps:.9f}," if fps else ""
    return f"{head}crop={cw}:{ch}:{cx}:{cy},scale={sw}:{sh}:flags=lanczos,format=gray", (sh, sw)


# --------------------------------------------------------------------------- hud-read

def cmd_hud_read(a):
    t_start = time.time()
    run = resolve_run(a.run)
    rows = load_chunks(run)
    t = parse_time(a.at, rows)
    region = parse_region(a.region)
    kind, scale, thr, inv, rx = read_args(a)
    cid, off = rec_to_chunk(rows, t)
    if not cid:
        fail(f"rec time {t} is not inside a recorded chunk")
    ocr = get_ocr()
    W, H = chunk_dims(run, cid)
    cx, cy, cw, ch = region_px(region, W, H)
    vf, shape = gray_vf(cx, cy, cw, ch, scale, None)
    stream = PieceStream(chunk_dir(run, cid) / "chunk.mp4", off, 5.0, vf, "gray", shape)
    try:
        frame = next(stream.frames(), None)
    finally:
        err = stream.close()
    if frame is None:
        fail(f"ffmpeg could not read a frame of {cid} at +{off:.2f}: {err}", 1)
    g = preprocess(frame, thr, inv)
    from PIL import Image
    dest = run_paths(run)["assets"] / "frames" / f"hud-{int(round(t * 100)):08d}-{region[0]:.3f}_{region[1]:.3f}_{region[2]:.3f}_{region[3]:.3f}.png"
    dest.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(g).save(dest)
    raw, conf, boxes = recognise(ocr, g, kind)
    text = clean_text(raw, kind, rx)
    res = {"ok": True, "rec": round(t, 3), "rec_hms": fmt_hms(t), "chunk": cid, "offset": round(off, 3), "region": list(region), "region_px": [cx, cy, cw, ch],
           "source_size": [W, H], "kind": kind, "scale": scale, "invert": inv, "threshold": thr, "text": text, "raw": raw.strip(),
           "confidence": round(conf, 2), "boxes": boxes, "image": str(dest).replace("\\", "/"), "seconds": round(time.time() - t_start, 2),
           "note": "the image is what the OCR saw (cropped, enlarged, grayscale, thresholded or inverted when asked); adjust --scale/--threshold/--invert until the text reads right, then hud-scan"}
    if a.numeric:
        res["value"] = numeric_value(text)
    out(res)


# --------------------------------------------------------------------------- hud-scan

def cmd_hud_scan(a):
    t_start = time.time()
    run = resolve_run(a.run)
    rows = load_chunks(run)
    region = parse_region(a.region)
    step = float(a.step)
    if step <= 0:
        fail("--step is a positive number of seconds")
    kind, scale, thr, inv, rx = read_args(a)
    t0, t1 = clamp_range(rows, a.from_, a.to)
    name = safe_name(a.name)
    ocr = get_ocr()
    np = _np()
    hud_dir = run_paths(run)["analysis"] / "hud"
    hud_dir.mkdir(parents=True, exist_ok=True)
    json_path, txt_path = hud_dir / f"{name}.json", hud_dir / f"{name}.txt"
    eps = float(a.idle_eps)
    sj = StreamJson(json_path, {"name": name, "region": list(region), "step": step, "kind": kind, "scale": scale, "invert": inv, "threshold": thr,
                                "regex": a.regex, "numeric": bool(a.numeric), "idle_eps": eps, "from": round(t0, 3), "to": round(t1, 3)})
    txt = open(txt_path.with_name(txt_path.name + ".part"), "w", encoding="utf-8")
    samples = ocr_calls = reused = nchanges = 0
    ocr_seconds = 0.0
    changes_first = []
    first_rec = last_rec = None
    prev_text, last_ref, last_res = None, None, ("", 0.0)
    warnings = []
    ok = False
    try:
        for pc in sample_pieces(rows, t0, t1, step):
            W, H = chunk_dims(run, pc["chunk"])
            cx, cy, cw, ch = region_px(region, W, H)
            vf, shape = gray_vf(cx, cy, cw, ch, scale, 1.0 / step)
            say(f"[hud-scan] {name}: {pc['chunk']} from {fmt_hms(pc['first'])}, {pc['n']} samples")
            stream = PieceStream(chunk_dir(run, pc["chunk"]) / "chunk.mp4", pc["offset"], pc["dur"], vf, "gray", shape)
            got = 0
            try:
                for k, frame in enumerate(stream.frames()):
                    rec = pc["first"] + k * step
                    if rec >= pc["rec_to"] - 1e-6:
                        break
                    got += 1
                    g = preprocess(frame, thr, inv)
                    if last_ref is not None and float(np.abs(g.astype(np.int16) - last_ref.astype(np.int16)).mean()) < eps:
                        reused += 1
                        raw_text, conf, was_reused = last_res[0], last_res[1], True
                    else:
                        t_ocr = time.time()
                        raw_text, conf, _ = recognise(ocr, g, kind)
                        ocr_seconds += time.time() - t_ocr
                        ocr_calls += 1
                        last_ref, last_res, was_reused = g.copy(), (raw_text, conf), False
                    text = clean_text(raw_text, kind, rx)
                    row = {"rec": round(rec, 3), "chunk": pc["chunk"], "t_chunk": round(pc["offset"] + k * step, 3), "text": text, "conf": round(conf, 2),
                           "reused": was_reused}
                    if a.numeric:
                        row["value"] = numeric_value(text)
                    if raw_text.strip() != text:
                        row["raw"] = raw_text.strip()
                    sj.row(row)
                    if text != prev_text:
                        txt.write(f"{fmt_hms(rec)}  {text if text else '(none)'}\n")
                        if prev_text is not None:
                            nchanges += 1
                            if len(changes_first) < 20:
                                changes_first.append([round(rec, 3), prev_text, text])
                        prev_text = text
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
        txt.close()
        if not ok:
            sj.abort()
            txt_path.with_name(txt_path.name + ".part").unlink(missing_ok=True)
    wall = time.time() - t_start
    summary = {"samples": samples, "ocr_calls": ocr_calls, "reused": reused, "changes": nchanges, "ocr_seconds": round(ocr_seconds, 2),
               "first_rec": first_rec, "last_rec": last_rec, "seconds": round(wall, 2)}
    sj.close(summary)
    os.replace(txt_path.with_name(txt_path.name + ".part"), txt_path)
    out({"ok": True, "name": name, "files": [str(json_path), str(txt_path)], **summary, "changes_first": changes_first,
         "changes_note": "[rec, from, to] of the first 20 changes of the text; the full list is in the .txt (only the rows where the text changed)",
         "region": list(region), "step": step, "kind": kind, "warnings": warnings})


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
    warnings = []
    ok = False
    try:
        for pc in sample_pieces(rows, t0, t1, step):
            W, H = chunk_dims(run, pc["chunk"])
            pxs = [region_px(r, W, H) for r in regions]
            fps = f"fps={1.0 / step:.9f}"
            if n == 1:
                cx, cy, cw, ch = pxs[0]
                vf, complex_graph = f"{fps},crop={cw}:{ch}:{cx}:{cy},scale={sw}:{sh}:flags=area,format=rgb24", False
            else:
                split = f"[0:v]{fps},split={n}" + "".join(f"[s{i}]" for i in range(n))
                parts = [f"[s{i}]crop={px[2]}:{px[3]}:{px[0]}:{px[1]},scale={sw}:{sh}:flags=area,format=rgb24[r{i}]" for i, px in enumerate(pxs)]
                vf, complex_graph = split + ";" + ";".join(parts) + ";" + "".join(f"[r{i}]" for i in range(n)) + f"hstack=inputs={n}[out]", True
            say(f"[region-series] {name}: {pc['chunk']} from {fmt_hms(pc['first'])}, {pc['n']} samples")
            stream = PieceStream(chunk_dir(run, pc["chunk"]) / "chunk.mp4", pc["offset"], pc["dur"], vf, "rgb24", (sh, sw * n, 3), complex_graph, step)
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
    out({"ok": True, "name": name, "files": [str(json_path), str(txt_path)], **summary, "per_region": report, "step": step, "size": [sw, sh], "warnings": warnings,
         "note": "diff = mean absolute difference (0..255) of the reduced crop against the previous sample; numbers only, what a change means is for the agent to read from the frames"})


# --------------------------------------------------------------------------- register

def _common(p, scan: bool) -> None:
    p.add_argument("--run", required=True)
    p.add_argument("--kind", choices=list(KINDS), default="digits", help="digits (default: recognition-only first, about 30x faster, then detect+recognise), text or auto")
    p.add_argument("--scale", type=float, default=3.0, help="enlarge the crop by this factor before the OCR (default 3)")
    p.add_argument("--invert", action="store_true", help="invert the grayscale crop (after --threshold)")
    p.add_argument("--threshold", type=int, help="0..255: pixels at or above it become white, the rest black (before --invert)")
    p.add_argument("--regex", help="keep the first match of this pattern in the text, e.g. '^\\d{1,2}$' (a score) or '\\d{1,2}:\\d{2}' (a clock); no match = empty text")
    p.add_argument("--numeric", action="store_true", help="also give the number the text holds (a clock 1:55 = 115, a score 7 = 7)")


def register(sub) -> None:
    p = sub.add_parser("hud-read", help="OCR of one region at one rec time (calibrate a region before a scan); keeps the cropped image")
    _common(p, False)
    p.add_argument("--at", required=True, help="rec time (seconds, H:MM:SS.cc or C0012+45.75)")
    p.add_argument("--region", required=True, help="x,y,w,h as fractions of the frame (0..1)")
    p.set_defaults(func=cmd_hud_read)

    p = sub.add_parser("hud-scan", help="OCR of one region over a range of the recording (the HUD clock, the score ...): a text per sample and the changes")
    _common(p, True)
    p.add_argument("--region", required=True, help="x,y,w,h as fractions of the frame (0..1)")
    p.add_argument("--from", dest="from_", help="rec time to start at (default: the start of the recording)")
    p.add_argument("--to", help="rec time to stop at (default: the end of the recording)")
    p.add_argument("--step", type=float, default=1.0, help="seconds between samples (default 1.0)")
    p.add_argument("--name", required=True, help="the output name: 20-analysis/hud/<name>.json and .txt")
    p.add_argument("--idle-eps", dest="idle_eps", type=float, default=1.0, help="a sample whose pixels differ from the last read one by less than this (mean 0..255) is not read again (default 1.0)")
    p.set_defaults(func=cmd_hud_scan)

    p = sub.add_parser("region-series", help="mean colour and change from sample to sample of one or more regions over a range (no OCR)")
    p.add_argument("--run", required=True)
    p.add_argument("--region", action="append", required=True, help="x,y,w,h as fractions of the frame; repeat for several regions")
    p.add_argument("--from", dest="from_", help="rec time to start at (default: the start of the recording)")
    p.add_argument("--to", help="rec time to stop at (default: the end of the recording)")
    p.add_argument("--step", type=float, default=0.5, help="seconds between samples (default 0.5)")
    p.add_argument("--name", required=True, help="the output name: 20-analysis/hud/<name>-series.json and .txt")
    p.add_argument("--size", default="64x36", help="the reduced size each region is measured on (default 64x36)")
    p.set_defaults(func=cmd_region_series)
