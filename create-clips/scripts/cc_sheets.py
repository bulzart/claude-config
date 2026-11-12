"""Contact sheets: layout, cell labels and drawing (Pillow only; no ffmpeg here).

A sheet is a header (title + legend), then a grid of cells. Under every cell sits its OWN label (rec time h:mm:ss.cc and the
chunk offset), a 3-px loudness bar and a 3-px chat bar. The layout idea is analyze-with-loupe's build_storyboard (header 46 px,
label strip under each frame, JPEG 86); 30 frames per sheet at 5 x 6 cells of 240 x 135.
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from cc_common import cfg_get, fmt_hms, fmt_off

HEAD_H = 46
LABEL_H = 20          # text row 14 px, loudness bar 3 px, chat bar 3 px
TEXT_H = 14
BAR_H = 3
BG = (16, 16, 16)
LOUD_MIN_DB = -60.0
LOUD_COLOR = (70, 205, 100)
CHAT_COLOR = (255, 150, 40)
TRACK_COLOR = (48, 48, 48)

LEGEND = ("left to right, top to bottom | under each frame: its time, rec h:mm:ss.cc and chunk offset | "
          "bars: loudness -60..0 dB (green), chat msgs/s 0..{ref} (orange)")

_FONTS: dict = {}


def font(size: int, bold: bool = True):
    key = (size, bold)
    if key in _FONTS:
        return _FONTS[key]
    cands = ([r"C:\Windows\Fonts\arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"] if bold
             else [r"C:\Windows\Fonts\arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
    f = None
    for c in cands:
        try:
            f = ImageFont.truetype(c, size)
            break
        except Exception:  # noqa: BLE001
            continue
    _FONTS[key] = f or ImageFont.load_default()
    return _FONTS[key]


def chat_ref() -> float:
    return float(cfg_get("frames.chat_bar_ref", 20))


def layout_for(width: int | None, height: int | None, cols=None, rows=None, cell_w=None) -> dict:
    """cols, rows, cell size for a source: the configured landscape grid (5 x 6 of 240 x 135), analyze-with-loupe's grids for a
    portrait source (6 x 5 of 138 x 245) and a square one (5 x 6 of 184 x 184). The arguments override."""
    f = cfg_get("frames", {}) or {}
    c, r = int(f.get("cols", 5)), int(f.get("rows", 6))
    cw, ch = int(f.get("cell_w", 240)), int(f.get("cell_h", 135))
    if width and height:
        ar = width / height
        if ar < 0.95:
            c, r, cw, ch = 6, 5, 138, 245
        elif ar <= 1.1:
            c, r, cw, ch = 5, 6, 184, 184
    if cols:
        c = int(cols)
    if rows:
        r = int(rows)
    if cell_w:
        base_ar = (cw / ch) if ch else 16 / 9
        cw = int(cell_w)
        ch = int(round(cw / base_ar))
    return {"cols": c, "rows": r, "cell_w": cw, "cell_h": ch, "per_sheet": c * r}


def cell_label(rec_s: float, off_s: float) -> str:
    """'0:33:45.75  +45.75': the cell's own timestamp."""
    return f"{fmt_hms(rec_s)}  {fmt_off(off_s)}"


def _fit(draw: ImageDraw.ImageDraw, text: str, fnt, max_w: int) -> str:
    if draw.textlength(text, font=fnt) <= max_w:
        return text
    parts = text.split(" | ")
    while len(parts) > 1:
        parts.pop()
        cand = " | ".join(parts)
        if draw.textlength(cand, font=fnt) <= max_w:
            return cand
    while text and draw.textlength(text + "...", font=fnt) > max_w:
        text = text[:-1]
    return text + "..."


def _bar(dr: ImageDraw.ImageDraw, x0: int, y: int, w: int, frac: float | None, color) -> None:
    if frac is None:
        return
    dr.rectangle([x0, y, x0 + w - 1, y + BAR_H - 1], fill=TRACK_COLOR)
    n = int(round(w * max(0.0, min(1.0, frac))))
    if n > 0:
        dr.rectangle([x0, y, x0 + n - 1, y + BAR_H - 1], fill=color)


def render_sheet(cells: list, *, title: str, legend: str | None, cols: int, cw: int, ch: int, path, quality: int = 86) -> list:
    """Draw one sheet. cells: [{img: PIL RGB or None, label: str, rms_db: float|None, chat: int|None}]. Returns the placements
    [{i, label, x, y, w, h}] (x, y = top-left of the cell, h = its picture height; the label strip is directly under it)."""
    n = len(cells)
    nrows = max(1, math.ceil(n / cols))
    sheet = Image.new("RGB", (cols * cw, HEAD_H + nrows * (ch + LABEL_H)), BG)
    dr = ImageDraw.Draw(sheet)
    hf, lf, tf = font(17), font(12), font(12)
    dr.text((8, 4), _fit(dr, title, hf, cols * cw - 16), fill=(240, 240, 240), font=hf)
    leg = (legend or LEGEND).replace("{ref}", f"{chat_ref():g}")
    dr.text((8, 25), _fit(dr, leg, lf, cols * cw - 16), fill=(170, 170, 170), font=lf)
    placements = []
    for i, c in enumerate(cells):
        r, col = divmod(i, cols)
        x0, y0 = col * cw, HEAD_H + r * (ch + LABEL_H)
        im = c.get("img")
        if im is None:
            dr.rectangle([x0 + 1, y0 + 1, x0 + cw - 2, y0 + ch - 2], fill=(58, 58, 58))
            dr.text((x0 + 8, y0 + 8), "no frame", fill=(220, 220, 220), font=lf)
        else:
            if im.width > cw - 2 or im.height > ch - 2:
                im = im.copy()
                im.thumbnail((cw - 2, ch - 2))
            sheet.paste(im, (x0 + (cw - im.width) // 2, y0 + (ch - im.height) // 2))
        dr.rectangle([x0, y0 + ch, x0 + cw - 1, y0 + ch + LABEL_H - 1], fill=(0, 0, 0))
        dr.text((x0 + 5, y0 + ch), _fit(dr, c["label"], tf, cw - 8), fill=(245, 245, 245), font=tf)
        db = c.get("rms_db")
        _bar(dr, x0, y0 + ch + TEXT_H, cw, None if db is None else (db - LOUD_MIN_DB) / (-LOUD_MIN_DB), LOUD_COLOR)
        ch_n = c.get("chat")
        _bar(dr, x0, y0 + ch + TEXT_H + BAR_H, cw, None if ch_n is None else ch_n / chat_ref(), CHAT_COLOR)
        placements.append({"i": i, "label": c["label"], "x": x0, "y": y0, "w": cw, "h": ch})
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(p, quality=int(quality))
    return placements
