#!/usr/bin/env python3
"""The director's kit: the parts a director's own working scripts are built from (manual 04, "The director's kit").

A film's plan files (the shot plan, each still's job, each still's framing, the drawings, the sound cues) are written
by the director. On a full film that is 80 stills, 80 drawings and 40 sounds, each placed on a spoken word, so it is
done with a few short scripts of the director's own, kept in RUN/workbench/ (never outside the run). This module gives
those scripts what is the same for every film: where a spoken phrase falls on the edit's clock, the drawn parts as
draw_tool elements, one job and one worker run per still, a still's framing, and the sound plan that bed-levels bakes.

Nothing here decides anything creative. It holds no palette, no position, no motion rule and no cue: each film brings
its own (a different look, another way of moving, another sound), and a film that needs none of this uses none of it.

    import sys; sys.path.insert(0, r"<STUDIO>/scripts")
    from director_kit import Kit, Overlay, Drawings, Stills, Framing, Sound

    python director_kit.py word-time --run RUN --video 1 --line L051 --phrase "Lift the pipes" [--shot S036b]
    python director_kit.py still-jobs --run RUN --video 1
    python director_kit.py stills --run RUN --video 1 status | run S001 S004 | run --todo [N]   [--wait-commit-gb 15]
    python director_kit.py margins --run RUN --video 1
    python director_kit.py frames --run RUN --video 1 --file FILM.mp4 --out PREFIX S001:0.5 @12.3 ...
    python director_kit.py edges --run RUN --video 1 --file FILM.mp4
    python director_kit.py tone --out tone.wav --seconds 96        python director_kit.py loop --src a.mp3 --out a-loop.wav --times 6

First made for one film (2026-11-28) in a folder outside the system; installed here so the next film starts with it."""
import argparse
import ctypes
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
STUDIO = SCRIPTS.parent
# The picture engine of this PC (manual 04): the .cmd that runs ComfyUI's own Python inside the memory guard, and the
# ComfyUI portable folder. The environment names are the image worker's own.
IMAGE_PYTHON = os.environ.get("AWL_IMAGE_PYTHON") or r"C:\Users\Bulzart\Documents\AI\tools\flux3_python.cmd"
IMAGE_ROOT = os.environ.get("AWL_IMAGE_ROOT") or r"C:\Users\Bulzart\Documents\AI\ComfyUI_windows_portable"


class KitError(ValueError):
    """Something the plan files do not hold (a phrase that is not in its line, a shot that is not in the edit)."""


def read_json(path, default=None):
    p = Path(path)
    if not p.is_file():
        if default is not None:
            return default
        raise KitError(f"missing: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def write_json(path, doc):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8", newline="")
    return p


def norm(word):
    """A word as it is compared: letters and digits only, lower case (any script)."""
    return re.sub(r"[\W_]", "", word.lower())


# ------------------------------------------------------------------------------------------------ the run's own files
class Kit:
    """One video of one run: its timed words, its shots on the edit's clock, its stills."""

    def __init__(self, run, video=1, canvas=(1920, 1080), fps=30):
        self.run, self.video, self.canvas, self.fps = Path(run), int(video), tuple(canvas), fps
        v = f"video-{self.video:02d}"
        self.plans, self.audio = self.run / "40-plans" / v, self.run / "50-audio" / v
        self.vis, self.edit = self.run / "60-visuals" / v, self.run / "70-edit" / v
        self.sfx = self.run / "50-audio" / "sfx" / v
        self._c = {}

    def _get(self, key, make):
        if key not in self._c:
            self._c[key] = make()
        return self._c[key]

    @property
    def edit_plan(self):
        """edit-plan.json (retime-shots): empty before the shots are timed to the real narration."""
        return self._get("ep", lambda: read_json(self.edit / "edit-plan.json", {}))

    @property
    def shots(self):
        return self._get("shots", lambda: {s["id"]: s for s in self.edit_plan.get("shots") or []})

    @property
    def plan(self):
        return self._get("plan", lambda: {s["id"]: s for s in read_json(self.vis / "shot-plan.json")["shots"]})

    @property
    def lines(self):
        return self._get("lines", lambda: {x["id"]: x for x in read_json(self.audio / "line-times.json")["lines"]})

    @property
    def text(self):
        """Each line's spoken words, its delivery tags left out."""
        return self._get("text", lambda: {x["id"]: re.sub(r"\[[^\]]*\]", "", x["text"]).split()
                                           for x in read_json(self.plans / "script.json")["lines"]})

    @property
    def holds(self):
        return self._get("holds", lambda: [(h["at_audio_s"], h["hold_s"]) for h in self.edit_plan.get("holds") or []])

    def pause(self, line):
        """A held silence's times on the edit's clock ({silence_from_s, silence_to_s, next_line_s})."""
        line = line if isinstance(line, str) else f"L{line:03d}"
        for p in self.edit_plan.get("pauses") or []:
            if p.get("after_line") == line:
                return p["times_in_edit"]
        raise KitError(f"no decided pause after {line}")

    def beats_of(self, a, b):
        """The beats a stretch of the edit lies in (what a sound's record names)."""
        return [x["id"] for x in self.edit_plan.get("beats") or [] if a < x["end_s"] - 0.05 and b > x["start_s"] + 0.05]

    def edit_t(self, a):
        """A time in the narration's own file, moved onto the edit's clock (every hold before it added)."""
        return a + sum(h for at, h in self.holds if at <= a + 1e-6)

    def word_time(self, line, phrase=None, end=False, rev=False, clock="edit"):
        """The second a phrase of a line starts (or ends) at; with no phrase, the line's first (or last) word.

        The timed words come from the narration's own transcript, which writes a spoken number as one word
        ("thirty-five" is "35"): in a line with a figure the timed words are fewer than the script's, so a phrase
        that comes after the figure is counted from the line's end (rev=True)."""
        line = line if isinstance(line, str) else f"L{line:03d}"
        if line not in self.lines or line not in self.text:
            raise KitError(f"{line}: not a recorded line of this video")
        words, wt = [norm(w) for w in self.text[line]], self.lines[line]["word_times"]
        if not wt:
            raise KitError(f"{line}: no timed words (narration-measure)")
        to = self.edit_t if clock == "edit" else (lambda t: t)
        if phrase is None:
            return to(wt[-1][1] if end else wt[0][0])
        ph = [norm(w) for w in phrase.split()]
        hits = [i for i in range(len(words) - len(ph) + 1) if words[i:i + len(ph)] == ph]
        if not hits:
            raise KitError(f"{line}: phrase not in the line: {phrase!r}")
        i = hits[-1] if rev else hits[0]
        j = i + len(ph) - 1 if end else i
        k = j - (len(words) - len(wt)) if rev else j
        k = max(0, min(len(wt) - 1, k))
        return to(wt[k][1] if end else wt[k][0])

    # ---- stills
    def still_of(self, sid):
        """The still a shot shows: its own, or the earlier one it returns to (`reuses`)."""
        return self.plan[sid].get("reuses") or sid

    def root_of(self, still):
        """The first still of a family: a still made from another by reference belongs to that one's frame."""
        refs = self.plan[still].get("refs") or []
        return Path(refs[0]).stem if refs else still

    def still_path(self, sid):
        return self.vis / "stills" / f"{self.still_of(sid)}.png"

    def frame_of(self, sid, default_scale=1.0):
        """The still's own move in the edit (capcut-images.json), or a held default before that file exists."""
        f = self.edit / "capcut-images.json"
        if f.is_file():
            for r in read_json(f)["images"]:
                if r.get("shot_id") == sid:
                    return {"scale": r["scale"], "x": r["x"], "y": r["y"]}
        return {"scale": [default_scale, default_scale], "x": [0.0, 0.0], "y": [0.0, 0.0]}


# ------------------------------------------------------------------------------------------------ the drawn layer
class Overlay:
    """One drawing: the elements drawn over one shot's still, as a draw_tool spec.

    Positions are fractions of the still (x to the right, y down); sizes are fractions of the short side. Times are
    seconds from the clip's start; at() gives the time of a spoken word. The palette is the film's own: `paper` and
    `ink` for plates and lines, and three roles a film may name (`main`, `alert`, `light`); with none given every
    mark is ink. Read every position off the finished still (draw_tool preview --grid), never from the prompt."""

    def __init__(self, kit, sid, palette=None, value_color=None, default_scale=1.0):
        if sid not in kit.shots:
            raise KitError(f"{sid}: not a shot of the edit plan (retime-shots first)")
        p = {"paper": "#F2EDE2", "ink": "#141414"}
        p.update(palette or {})
        self.kit, self.sid, self.s = kit, sid, kit.shots[sid]
        self.paper, self.ink = p["paper"], p["ink"]
        self.main, self.alert, self.light = p.get("main", self.ink), p.get("alert", self.ink), p.get("light", self.ink)
        self.value_color = value_color or (lambda value: self.ink)
        self.default_scale = default_scale
        self.t0, self.dur = self.s["start_s"], round(self.s["end_s"] - self.s["start_s"], 3)
        self.el, self.n = [], 0

    # ---- time
    def at(self, line, phrase=None, end=False, rev=False, lead=0.0):
        """Seconds from this clip's start to a spoken word (lead: that much earlier), kept inside the clip. A mark
        timed on a line's last words lands on the cut: time it on the start of its phrase."""
        t = self.kit.word_time(line, phrase, end, rev) - self.t0 - lead
        return round(max(0.05, min(self.dur - 0.25, t)), 2)

    def add(self, typ, **kw):
        self.n += 1
        e = {"id": kw.pop("id", f"{typ}{self.n}"), "type": typ}
        e.update({k: v for k, v in kw.items() if v is not None})
        self.el.append(e)
        return e

    @staticmethod
    def IN(kind, t, d, **kw):
        return dict({"kind": kind, "start_s": round(t, 2), "dur_s": d}, **kw)

    @staticmethod
    def OUT(t, d=0.3, kind="fade"):
        return None if t is None else {"kind": kind, "start_s": round(t, 2), "dur_s": d}

    def _c(self, color, role="ink"):
        return color if color is not None else getattr(self, role)

    # ---- words
    def tag(self, at, text, t, size=0.044, align="center", until=None, color=None, z=20):
        """A typed tag on a paper plate: a place, a date, one or two words. 4 % of the height or more reads on a
        phone; the caption line sits at 0.85 of the height, so a tag stands above 0.78."""
        return self.add("text", at=list(at), text=text, size=size, font="sans", fill=self._c(color), align=align, z=z,
                        plate={"fill": self.paper, "alpha": 0.96, "stroke": self.ink, "pad": 0.009, "radius": 0.002,
                               "width": 2.2},
                        **{"in": self.IN("type", t, min(0.5, 0.03 * len(text) + 0.12)), "out": self.OUT(until)})

    def word(self, at, text, t, size=0.06, color=None, until=None, align="center", z=20):
        """A big typed word with no plate."""
        return self.add("text", at=list(at), text=text, size=size, font="sans", fill=self._c(color), align=align, z=z,
                        **{"in": self.IN("type", t, 0.25), "out": self.OUT(until)})

    def hand(self, at, text, t, size=0.06, color=None, until=None, rotate=None, z=21):
        """Handwriting: a doubt, an aside."""
        return self.add("text", at=list(at), text=text, size=size, font="hand", fill=self._c(color), align="center",
                        z=z, rotate=rotate, **{"in": self.IN("write", t, min(0.6, 0.05 * len(text) + 0.2)),
                                               "out": self.OUT(until)})

    def q(self, at, t, size=0.11, color=None, until=None):
        return self.hand(at, "?", t, size=size, color=color, until=until, rotate=-6)

    # ---- the read-out
    def readout(self, at, seq, w=0.27, h=0.115, size=0.064, pin=None, until=None):
        """A flip-number card. seq: [(t, "-4 °C"), ...]; each value flips in over the one before, in the colour
        value_color gives it. pin: the point it reads (a thin leader and a dot). A value at t = 0 stands from the
        cut with no entrance: a drawing belongs to one shot, so a read-out that stays across a cut is drawn again,
        already in place, in the next shot. The drawing typeface has no true minus sign: a hyphen is drawn as an
        en dash."""
        if pin:
            t0 = seq[0][0]
            self.add("line", points=[list(pin), [at[0] - (w * 0.28 if pin[0] < at[0] else -w * 0.28), at[1]]],
                     stroke=self.ink, width=2.4, z=14,
                     **{"in": self.IN("draw", max(0.0, t0 - 0.25), 0.03 if t0 <= 0.02 else 0.25),
                        "out": self.OUT(until)})
            self.add("ellipse", center=list(pin), w=0.016, h=0.016, fill=self.ink, fill_alpha=1.0, z=14,
                     **{"in": self.IN("fade", max(0.0, t0 - 0.3), 0.03 if t0 <= 0.02 else 0.15),
                        "out": self.OUT(until)})
        for i, (t, val) in enumerate(seq):
            self.add("card", center=list(at), w=w, h=h, lines=[val.replace("-", "\u2013") if val.strip() else " "],
                     text_size=size, font="sans", fill=self.paper, stroke=self.ink, width=3.0, radius=0.006,
                     text_color=self.value_color(val), type_text=False, z=15 + i,
                     **{"in": self.IN("fade", 0, 0.03) if t <= 0.02 else self.IN("flip", t, 0.22),
                        "out": self.OUT(until)})

    # ---- marks
    def tick(self, at, t, size=0.04, color=None, until=None):
        return self.add("mark", kind="tick", center=list(at), size=size, stroke=self._c(color), width=5.5, z=22,
                        **{"in": self.IN("draw", t, 0.22), "out": self.OUT(until)})

    def cross(self, at, t, size=0.04, color=None, until=None):
        return self.add("mark", kind="cross", center=list(at), size=size, stroke=self._c(color, "alert"), width=5.5,
                        z=22, **{"in": self.IN("draw", t, 0.25), "out": self.OUT(until)})

    def ring(self, at, w, h, t, color=None, until=None, width=4.5):
        return self.add("ring", center=list(at), w=w, h=h, stroke=self._c(color), width=width, style="brush", z=18,
                        **{"in": self.IN("draw", t, 0.45), "out": self.OUT(until)})

    def arrow(self, pts, t, d=0.5, color=None, width=4.0, smooth=True, dash=None, until=None, head="filled"):
        return self.add("arrow", points=[list(p) for p in pts], smooth=smooth, stroke=self._c(color), width=width,
                        head=head, style="ink", dash=dash, z=18,
                        **{"in": self.IN("draw", t, d, ease="out"), "out": self.OUT(until)})

    def line(self, pts, t, d=0.4, color=None, width=3.0, dash=None, smooth=False, until=None, z=16, alpha=None):
        return self.add("path", points=[list(p) for p in pts], smooth=smooth, stroke=self._c(color), width=width,
                        dash=dash, alpha=alpha, style="plain", z=z,
                        **{"in": self.IN("draw", t, d), "out": self.OUT(until)})

    def bracket(self, x, y0, y1, t, label=None, side="right", lip=0.012, size=0.04, until=None):
        """A square bracket down a length, with its figure beside it."""
        sx = lip if side == "right" else -lip
        self.line([[x - sx, y0], [x, y0], [x, y1], [x - sx, y1]], t, 0.45, width=3.2, until=until)
        if label:
            self.tag([x + (0.012 if side == "right" else -0.012), (y0 + y1) / 2], label, t + 0.3, size=size,
                     align="left" if side == "right" else "right", until=until)

    def grip(self, x, y0, y1, close, open_=None, half=0.03, color=None, until=None, n=5):
        """n short bold marks closing on an upright thing at x (half: its half-width) between y0 and y1, from the
        left and the right in turn: a count the viewer can watch lose its members.
        close: one time for all, or n times; open_: {mark index: time} (the mark is undrawn: it lets go).
        A film's central measure is drawn bold enough to count on a phone: thin marks 10 px wide were seen as
        "a few thin white dashes"; a 17 px mark on a dark edge counts."""
        color = self._c(color)
        ts = close if isinstance(close, (list, tuple)) else [close + (0.12 * i if close > 0.02 else 0) for i in range(n)]
        for i in range(n):
            y = y0 + (y1 - y0) * (i + 0.5) / n
            sgn = -1 if i % 2 == 0 else 1
            out = (open_ or {}).get(i)
            pts = [[x + sgn * (half + 0.075), y], [x + sgn * (half + 0.004), y]]
            for k, (col, wd) in enumerate(((self.ink, 26.0), (color, 17.0)) if color != self.ink
                                          else ((self.ink, 20.0),)):
                self.add("line", id=f"grip{i}_{k}", points=pts, stroke=col, width=wd, style="plain", z=16 + k,
                         **{"in": self.IN("fade", 0, 0.03) if ts[i] <= 0.02 else self.IN("draw", ts[i], 0.2, ease="out"),
                            "out": self.OUT(out, 0.3, "undraw") if out is not None else self.OUT(until)})

    def panel(self, center, w, h, t, until=None, z=13, alpha=0.96):
        """A paper panel (w, h: fractions of the short side) for figures that would vanish on the picture's own
        colour (a blue mark on blue ground is not seen)."""
        return self.add("rect", center=list(center), w=w, h=h, fill=self.paper, fill_alpha=alpha, stroke=self.ink,
                        width=2.6, radius=0.006, z=z, **{"in": self.IN("fade", t, 0.2), "out": self.OUT(until)})

    def bar(self, x, base, unit, n, t, color=None, w=0.05, label=None, lose=None, extra=0.0, size=0.036,
            label_dy=0.035, until=None):
        """A bar of n stacked blocks standing on `base` (y), each `unit` high; `extra` a thin block on top.
        lose: {block index from the bottom: time} blocks that are taken away."""
        hs = [unit] * n + ([extra] if extra else [])
        y = base
        for i, hh in enumerate(hs):
            out = (lose or {}).get(i)
            self.add("rect", id=f"bar{self.n}_{i}", center=[x, y - hh / 2], w=w, h=hh - 0.004,
                     fill=self._c(color, "main"), fill_alpha=1.0, stroke=self.ink, width=2.2, z=16,
                     **{"in": self.IN("grow", t + 0.05 * i, 0.18),
                        "out": self.OUT(out, 0.35) if out is not None else self.OUT(until)})
            y -= hh
        if label:
            self.tag([x, base + label_dy], label, t, size=size, until=until)

    def strip(self, x0, x1, y, t0, t1, n=30, color=None, width=14.0, until=None):
        """A row of n small square marks appearing from left to right between t0 and t1 (a month or a year each)."""
        px = width * min(self.kit.canvas) / 1080.0
        on = 0.62
        off = max(0.25, (x1 - x0) * self.kit.canvas[0] / (n * px) - on)
        return self.add("path", points=[[x0, y], [x1, y]], stroke=self._c(color, "main"), width=width,
                        dash=[on, off], style="plain", z=16,
                        **{"in": self.IN("draw", t0, max(0.3, t1 - t0)), "out": self.OUT(until)})

    def scale(self, x, y_top, y_bottom, t, marks=(), d=1.0, until=None, size=0.044):
        """A scale down an edge. marks: [(y, "10 m", t)]."""
        self.line([[x, y_top], [x, y_bottom]], t, d, width=3.0, until=until)
        for y, lab, tm in marks:
            self.line([[x - 0.006, y], [x + 0.012, y]], tm, 0.15, width=3.0, until=until)
            if lab:
                self.add("text", at=[x + 0.02, y], text=lab, size=size, font="sans", fill=self.ink, align="left", z=20,
                         plate={"fill": self.paper, "alpha": 0.9, "pad": 0.005},
                         **{"in": self.IN("fade", tm, 0.2), "out": self.OUT(until)})

    def wind(self, x0, x1, y0, y1, t, n=3, color=None, until=None, d=1.2):
        """Flow through a gap: n long dashed strokes from left to right whose dashes keep running."""
        for i in range(n):
            y = y0 + (y1 - y0) * (i + 0.5) / n
            wob = 0.006 * (1 if i % 2 else -1)
            self.add("path", id=f"wind{i}", points=[[x0, y], [x0 + (x1 - x0) * 0.33, y + wob],
                                                     [x0 + (x1 - x0) * 0.66, y - wob], [x1, y]],
                     smooth=True, stroke=self._c(color, "light"), width=4.0, dash=[3.0, 2.2], march=True,
                     style="plain", z=12, **{"in": self.IN("draw", t + 0.18 * i, d, ease="out"),
                                             "out": self.OUT(until)})

    def stamp(self, at, text, t, size=0.075, color=None, rotate=-7, until=None):
        return self.add("stamp", at=list(at), text=text, size=size, color=self._c(color, "paper"), rotate=rotate, z=25,
                        **{"in": self.IN("slam", t, 0.22), "out": self.OUT(until)})

    def dots(self, pts, t, d, r=0.009, color=None, until=None, batches=10, z=15, alpha=1.0):
        """Many small points lighting up over d seconds, in batches (one group a batch keeps the render light)."""
        k = max(1, len(pts) // batches)
        for b in range(0, len(pts), k):
            kids = [{"type": "ellipse", "center": [x, y], "w": r, "h": r, "fill": self._c(color, "main"),
                     "fill_alpha": alpha} for x, y in pts[b:b + k]]
            self.add("group", children=kids, z=z, **{"in": self.IN("fade", t + d * b / max(1, len(pts)), 0.25),
                                                    "out": self.OUT(until)})

    def spec(self):
        """The draw_tool spec. It carries the still's own move (still_motion), so the drawing rides with its picture:
        write the images file (Framing) before the drawings, or the drawing slides against its still."""
        w, h = self.kit.canvas
        return {"canvas": f"{w}x{h}", "fps": self.kit.fps, "dur_s": self.dur, "shot": self.sid,
                "still_motion": self.kit.frame_of(self.sid, self.default_scale), "elements": self.el}


class Drawings:
    """The film's drawings: one maker per shot that has one, written as DNN.json in shot order and rendered.

        dr = Drawings(kit, palette={...})
        @dr.draw("S008")
        def _(d): d.tag([0.24, 0.15], "January", d.at(3, "minus thirty-seven"))
        dr.write(); dr.sheet(["S008"]); dr.render()

    A name follows the shot order, so a maker added in the middle renames the drawings after it: write and render
    them again. A render takes most of a minute: run two or three processes on separate lists of shots."""

    def __init__(self, kit, overlay=Overlay, **overlay_kw):
        self.kit, self.overlay, self.kw, self.makers = kit, overlay, overlay_kw, {}
        self.dir, self.tool = kit.vis / "drawings", SCRIPTS / "draw_tool.py"

    def draw(self, sid):
        def reg(fn):
            self.makers[sid] = fn
            return fn
        return reg

    def build(self):
        out = []
        for n, sid in enumerate([s["id"] for s in self.kit.edit_plan.get("shots") or [] if s["id"] in self.makers], 1):
            d = self.overlay(self.kit, sid, **self.kw)
            self.makers[sid](d)
            out.append((f"D{n:02d}", sid, d))
        return out

    def write(self):
        built = self.build()
        for name, _sid, d in built:
            write_json(self.dir / f"{name}.json", d.spec())
        return len(built)

    def _run(self, *args):
        return subprocess.run([sys.executable, "-X", "utf8", str(self.tool), *[str(a) for a in args]],
                              capture_output=True, text=True, encoding="utf-8", errors="replace")

    def sheet(self, ids=None, out_dir=None, grid=True):
        """Preview sheets over the real stills, with the still's own tenths drawn on them: where positions are read."""
        out_dir = Path(out_dir or self.kit.run / "workbench" / "sheets")
        out_dir.mkdir(parents=True, exist_ok=True)
        made = {}
        for _name, sid, d in self.build():
            if ids and sid not in ids:
                continue
            bg = self.kit.still_path(sid)
            if not bg.is_file():
                made[sid] = "no still yet"
                continue
            spec = write_json(out_dir / f"{sid}.json", d.spec())
            ts = sorted({round(min(d.dur - 0.1, e["in"]["start_s"] + e["in"]["dur_s"] + 0.15), 2) for e in d.el})
            ts = ts[:: max(1, len(ts) // 3)][:3] + [round(d.dur - 0.1, 2)]
            r = self._run("preview", "--spec", spec, "--bg", bg, "--times", ",".join(str(t) for t in ts),
                          "--out", out_dir / f"{sid}.jpg", *(["--grid"] if grid else []))
            made[sid] = str(out_dir / f"{sid}.jpg") if r.returncode == 0 else (r.stdout + r.stderr)[-300:]
        return made

    def render(self, ids=None, say=print):
        ok = True
        for name, sid, _d in self.build():
            if ids and sid not in ids:
                continue
            r = self._run("render", "--spec", self.dir / f"{name}.json", "--out", self.dir / f"{name}.mov")
            ok = ok and r.returncode == 0
            say(name, sid, "ok" if r.returncode == 0 else (r.stdout + r.stderr)[-300:], flush=True)
        return ok


# ------------------------------------------------------------------------------------------------ the stills
def free_memory_gb():
    """(free RAM, free commit) in GB as Windows reports them, or None where that cannot be read."""
    if not hasattr(ctypes, "windll"):
        return None

    class Stat(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    m = Stat()
    m.dwLength = ctypes.sizeof(m)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.ullAvailPhys / 2 ** 30, m.ullAvailPageFile / 2 ** 30


def wait_for_memory(need_commit_gb=15.0, min_ram_gb=2.5, hours=8.0, say=print, every_s=60):
    """Wait until the PC has the memory a picture or music maker needs, and say what is short while waiting.

    The picture maker here takes 13 to 15 GB of free commit; started with less it is stopped by the memory guard half
    a minute in. This only reads Windows' own figures: it closes no program, changes no setting and leaves the guard
    as it is. When it gives up it says how much is free: the user decides what to close or whether the page file
    grows. True when the memory is there."""
    t0 = last = 0.0
    t0 = time.time()
    while True:
        got = free_memory_gb()
        if got is None:
            return True
        ram, commit = got
        if commit >= need_commit_gb and ram >= min_ram_gb:
            say(f"memory is there (free RAM {ram:.1f} GB, free commit {commit:.1f} GB): starting", flush=True)
            return True
        if time.time() - last > 1800:
            say(f"waiting: free RAM {ram:.1f} GB, free commit {commit:.1f} GB (needs about {need_commit_gb:.0f} GB "
                "of free commit): close programs or enlarge the page file", flush=True)
            last = time.time()
        if time.time() - t0 > hours * 3600:
            say(f"gave up after {hours:g} h: free commit {commit:.1f} GB", flush=True)
            return False
        time.sleep(every_s)


class Stills:
    """One job file and one worker run per still (the user's rule: a failure costs one picture, never a batch).

    write_jobs() makes jobs/still-SNNN.json from the shot plan and the locked look; run_one() draws one, keeps a small
    preview to look at and adds a line to jobs/runs.jsonl. jobs/overrides.json holds changes for single stills
    ({"S003": {"seed": 11}}) and, under "_job", keys for every job. Every still is looked at before the next batch."""

    def __init__(self, kit, python_cmd=None, root=None):
        self.kit = kit
        self.jobs, self.stills, self.prev = kit.vis / "jobs", kit.vis / "stills", kit.vis / "previews"
        self.python_cmd, self.root = python_cmd or IMAGE_PYTHON, root or IMAGE_ROOT
        self.worker = SCRIPTS / "image_worker.py"

    def shots(self):
        return [s for s in read_json(self.kit.vis / "shot-plan.json")["shots"] if s.get("frame_prompt")]

    def overrides(self):
        return read_json(self.jobs / "overrides.json", {})

    def write_jobs(self, seed0=4100, seed_step=7, steps=16, width=1920, height=1088, alpha=16,
                   direct=("section", "map", "diagram", "chart"), out_dir=None):
        """direct: compositions drawn straight from their prompt ("upsample": false). The caption writer adds
        colours, people and objects to a diagram; places and scenes gain from it. A shot may say `upsample` itself."""
        style = read_json(self.kit.vis / "style-lock.json")["style_prompt"]
        jobs = Path(out_dir or self.jobs)
        for d in (jobs, self.stills, self.prev):
            d.mkdir(parents=True, exist_ok=True)
        ov = self.overrides()
        for n, s in enumerate(self.shots()):
            sid = s["id"]
            item = {"shot_id": sid, "prompt": s["frame_prompt"] + " " + style, "out": str(self.stills / f"{sid}.png"),
                    "width": width, "height": height, "seed": seed0 + n * seed_step, "steps": steps,
                    "upsample": s.get("upsample", not str(s.get("composition") or "").startswith(tuple(direct))),
                    "refs": s.get("refs") or []}
            if s.get("content_note"):
                item["content_note"] = s["content_note"]
            item.update(ov.get(sid) or {})
            job = {"op": "generate", "run": str(self.kit.run), "video": self.kit.video, "purpose": "shots",
                   "alpha": alpha, "log_out": str(self.kit.run / "logs" / f"still-{sid}-comfy.log"), "images": [item]}
            job.update(ov.get("_job") or {})
            write_json(jobs / f"still-{sid}.json", job)
        return len(self.shots())

    def todo(self, n=999):
        """The next stills with no picture yet whose reference stills exist or come earlier in this list."""
        ids = []
        for s in self.shots():
            if (self.stills / f"{s['id']}.png").exists():
                continue
            if all(Path(r).exists() or Path(r).stem in ids for r in s.get("refs") or []):
                ids.append(s["id"])
            if len(ids) >= n:
                break
        return ids

    def status(self):
        have = [s["id"] for s in self.shots() if (self.stills / f"{s['id']}.png").exists()]
        return have, [s["id"] for s in self.shots() if s["id"] not in have]

    def run_one(self, sid, say=print):
        job = self.jobs / f"still-{sid}.json"
        if not job.is_file():
            raise KitError(f"no job file for {sid}: write the jobs first (still-jobs)")
        env = dict(os.environ, AWL_IMAGE_ROOT=self.root, AWL_IMAGE_PYTHON=self.python_cmd, PYTHONIOENCODING="utf-8")
        t0 = time.time()
        p = subprocess.run(["cmd", "/c", self.python_cmd, str(self.worker), str(job)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env)
        last = next((ln for ln in reversed((p.stdout or "").strip().splitlines()) if ln.strip().startswith("{")), "{}")
        try:
            res = json.loads(last)
        except ValueError:
            res = {"ok": False, "error": "no JSON answer", "tail": (p.stdout or "")[-400:]}
        got = res.get("images") or res.get("results")
        item = got[0] if isinstance(got, list) and got else {}
        rec = {"shot": sid, "exit": p.returncode, "seconds": round(time.time() - t0, 1), "ok": bool(res.get("ok")),
               "error": res.get("error"), "issues": res.get("issues") or item.get("issues"),
               "item_error": item.get("error"), "caption_notes": item.get("caption_notes"),
               "people_question": item.get("people_question"), "drew_from": item.get("drew_from"),
               "caption_sha256": item.get("caption_sha256"),
               "stderr_tail": (p.stderr or "")[-300:] if p.returncode else None}
        out = self.stills / f"{sid}.png"
        if out.exists() and rec["ok"]:
            self.prev.mkdir(parents=True, exist_ok=True)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out), "-vf", "scale=960:-1", "-q:v", "4",
                            str(self.prev / f"{sid}.jpg")])
            rec["preview"] = str(self.prev / f"{sid}.jpg")
        with open(self.jobs / "runs.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        say(json.dumps({k: v for k, v in rec.items() if v not in (None, [], "")}, ensure_ascii=False)[:900], flush=True)
        return rec["ok"]


# ------------------------------------------------------------------------------------------------ framing
def paperish(px):
    """A pale paper colour: what an "illustration on paper" look leaves round its picture."""
    r, g, b = px[:3]
    return r > 205 and g > 200 and b > 185 and max(r, g, b) - min(r, g, b) < 34


def margin(im, side, is_border=paperish, picture_px=70):
    """How many pixels of border (and a drawn frame line just inside it) a still has on one side.

    A pale edge deeper than picture_px is the picture itself (snow, a white floor, a pale sky), not a margin. Any
    such measure is fooled both ways, so the framing is checked on the export (edges)."""
    w, h = im.size
    n_lines = h if side in ("top", "bottom") else w
    px = im.load()

    def line(i):
        if side == "top":
            return [px[x, i] for x in range(0, w, 6)]
        if side == "bottom":
            return [px[x, h - 1 - i] for x in range(0, w, 6)]
        if side == "left":
            return [px[i, y] for y in range(0, h, 6)]
        return [px[w - 1 - i, y] for y in range(0, h, 6)]

    m = 0
    for i in range(min(n_lines // 6, 160)):
        row = line(i)
        if sum(is_border(p) for p in row) / len(row) >= 0.9:
            m = i + 1
        else:
            break
    if m > picture_px:
        return 0
    if m:                                             # a frame line drawn just inside the border
        for i in range(m, min(m + 16, n_lines // 6)):
            row = line(i)
            if sum(1 for p in row if sum(p[:3]) < 200) / len(row) >= 0.5:
                m = i + 3
    return m


def hide_band_y(band_top, scale):
    """The `y` that puts a band whose top is at still-height `band_top` (0 = top, 1 = bottom) just under the frame,
    at this scale: y = 2((band_top - 0.5) * scale - 0.5), never past the picture's own top edge (y >= 1 - scale)."""
    return round(max(1.0 - scale, 2.0 * ((band_top - 0.5) * scale - 0.5)), 3)


class Framing:
    """Each still's framing and move in the edit: frame-crop.json (what each still needs to hide its own border) and
    capcut-images.json (what capcut-build reads; rows: scale, x, y as [start, end], x and y in half-canvas units,
    y up; scale 1 covers the frame).

    The kit keeps what is true of every film: the stills of one family (a still and those made from it by reference,
    or a return to it) share one framing so the frame never jumps between them; a variant dissolves in over its
    family; a framing set by hand wins. HOW a still moves is the film's own decision, given as `motion(info)`: it
    gets {shot, still, scale, dur, composition, chained, has_drawing} and returns the row's scale/x/y/kind. A still
    that carries a drawing holds still or moves very little, because the drawing rides on it."""

    def __init__(self, kit, min_scale=1.0, max_scale=1.14, mins=None, overrides=None, is_border=paperish):
        self.kit, self.min_scale, self.max_scale = kit, min_scale, max_scale
        self.mins, self.overrides, self.is_border = mins or {}, overrides or {}, is_border

    def measure(self):
        from PIL import Image
        crop = {}
        for f in sorted((self.kit.vis / "stills").glob("S*.png")):
            im = Image.open(f).convert("RGB")
            ms = {s: margin(im, s, self.is_border) for s in ("top", "bottom", "left", "right")}
            frac = max(ms["top"] / im.size[1], ms["bottom"] / im.size[1], ms["left"] / im.size[0],
                       ms["right"] / im.size[0])
            need = 1.0 / (1.0 - 2.0 * frac) if frac < 0.45 else self.max_scale
            crop[f.stem] = {"still": f.name, "margins_px": ms,
                            "min_scale": round(max(self.min_scale, need + 0.004, self.mins.get(f.stem, 0)), 3)}
        return crop

    def chained(self, i):
        """True when the shot before or after shows another member of the same family."""
        shots = self.kit.edit_plan["shots"]
        me = self.kit.root_of(self.kit.still_of(shots[i]["id"]))
        return any(0 <= j < len(shots) and self.kit.root_of(self.kit.still_of(shots[j]["id"])) == me
                   for j in (i - 1, i + 1))

    def rows(self, crop, motion, drawn=(), dissolve_s=0.5):
        k, out, prev = self.kit, [], None
        for i, s in enumerate(k.edit_plan["shots"]):
            sid, st = s["id"], k.still_of(s["id"])
            sc = min(self.max_scale, crop.get(st, {}).get("min_scale", self.min_scale))
            fam = [x for x in crop if x in k.plan and k.root_of(x) == k.root_of(st)]
            sc = min(self.max_scale, max([sc] + [crop[x]["min_scale"] for x in fam]))
            row = {"image": i + 1, "start": s["start_s"], "motion": "custom", "shot_id": sid}
            if sid in self.overrides:
                row.update(self.overrides[sid])
                row["kind"] = "set by hand"
            else:
                row.update(motion({"shot": sid, "still": st, "scale": sc, "dur": s["end_s"] - s["start_s"],
                                   "composition": str(k.plan[sid].get("composition") or ""),
                                   "chained": self.chained(i), "has_drawing": sid in drawn}))
            if dissolve_s and prev and k.root_of(prev) == k.root_of(st) and prev != st:
                row.update(transition="mix", trans_s=dissolve_s)
            out.append(row)
            prev = st
        return out

    def write(self, crop, rows):
        write_json(self.kit.edit / "frame-crop.json", crop)
        write_json(self.kit.edit / "capcut-images.json", {"fps": self.kit.fps, "images": rows})


def held(info):
    """A locked-off picture."""
    return {"scale": [info["scale"], info["scale"]], "x": [0.0, 0.0], "y": [0.0, 0.0], "kind": "held"}


def breathe(info, by, push_in=True):
    """A slow, small push in (or pull back) by `by` of scale over the shot."""
    a, b = info["scale"], round(info["scale"] + by, 3)
    return {"scale": [a, b] if push_in else [b, a], "x": [0.0, 0.0], "y": [0.0, 0.0],
            "kind": "slow push in" if push_in else "slow pull back"}


# ------------------------------------------------------------------------------------------------ sound
def media_seconds(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                 str(path)], capture_output=True, text=True).stdout.strip())


def loop(src, out, times):
    """A sound played `times` in a row as one file (an ambience long enough for its scene)."""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af", f"aloop=loop={int(times) - 1}:size=2147483647",
                    "-ar", "48000", "-ac", "2", str(out)], check=True)
    return media_seconds(out)


# A held low tone a small speaker can still play: the fundamental and its octave carry the weight on large speakers,
# the partials from 220 Hz up are what a phone gives (a tone on 55 and 110 Hz alone was silence there, 2026-11-28).
TONE_PARTIALS = ((55, 0.30, 0), (110.2, 0.21, 0), (165, 0.12, 0.5), (220.3, 0.105, 0), (330, 0.065, 1), (439.6, 0.04, 0),
                 (660, 0.018, 0))


def tone(out, seconds, partials=TONE_PARTIALS, sway_hz=0.07, sway=0.14, fade_s=3.0, volume=0.62, lowpass_hz=1200):
    """A synthesised sustained tone (the local music maker turns "one held note" into struck notes). Say in the
    music record that it is synthesised. partials: (Hz, amplitude, phase)."""
    seconds = float(seconds)
    body = "+".join(f"{a:g}*sin(2*PI*{hz:g}*t{'+' + format(ph, 'g') if ph else ''})" for hz, a, ph in partials)
    expr = f"({body})*({1 - sway:g}+{sway:g}*sin(2*PI*{sway_hz:g}*t))"
    af = (f"lowpass=f={lowpass_hz:g},afade=t=in:d={fade_s:g},afade=t=out:st={max(0.0, seconds - fade_s):g}:d={fade_s:g},"
          f"volume={volume:g}")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"aevalsrc='{expr}':s=48000:d={seconds:g}",
                    "-af", af, "-ac", "2", str(out)], check=True)
    return media_seconds(out)


def room_tone(out, seconds, volume=0.5):
    """A faint room tone: a voice over digital silence sounds like a recording booth."""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    f"anoisesrc=color=brown:duration={float(seconds):.1f}:seed=7", "-af",
                    f"highpass=f=60,lowpass=f=900,volume={volume:g}", "-ar", "48000", "-ac", "2", str(out)], check=True)
    return media_seconds(out)


class Sound:
    """The film's beds and single sounds, each placed on a spoken word, then levelled and baked by bed-levels.

        so = Sound(kit)
        so.bed("wind", wind_file, 0.0, kit.shots["S004"]["start_s"] + 1.0, 20, "the wind the block is open to",
               kind="ambience")
        so.fx("winch", "winch.mp3", kit.pause(31)["silence_from_s"] - 3.4, 9, "the windlass lowering the bucket")
        so.plans(); so.bake()

    under: dB under the voice it is baked to sit at; lift: bed-levels' own (rises where nobody speaks). A bought or
    generated sound is looked at before it is placed, and sound-review then measures what really plays."""

    def __init__(self, kit, music_dir=None, sfx_dir=None):
        self.kit, self.beds, self.sounds = kit, [], []
        self.music, self.sfx = Path(music_dir or kit.edit / "music"), Path(sfx_dir or kit.sfx)

    def W(self, line, phrase=None, end=False, rev=False):
        return round(self.kit.word_time(line, phrase, end, rev), 2)

    def S(self, sid, end=False):
        return self.kit.shots[sid]["end_s" if end else "start_s"]

    def bed(self, i, file, at, end, under, why, src=0.0, fade_in=0.6, fade_out=1.2, kind="music", lift=None):
        self.beds.append({"id": i, "file": str(file), "at": round(at, 2), "end": round(end, 2), "under": under,
                          "why": why, "src": src, "fade_in": fade_in, "fade_out": fade_out, "kind": kind,
                          "lift": lift})

    def fx(self, i, name, at, under, purpose, dur=None, fade_out=0.0):
        f = Path(name)
        self.sounds.append({"id": i, "file": str(f if f.is_absolute() else self.sfx / name), "at": round(at, 2),
                            "under": under, "purpose": purpose, "dur": dur, "fade_out": fade_out})

    def plan_docs(self):
        narr = (self.kit.edit_plan.get("narration_for_edit") or {}).get("file")
        beds = {"narration": narr, "tracks": []}
        for b in self.beds:
            tr = {"id": b["id"], "file": b["file"], "under_speech_db": b["under"], "why": b["why"],
                  "src_start": b["src"], "dur": round(b["end"] - b["at"], 2), "fade_in": b["fade_in"],
                  "fade_out": b["fade_out"], "at": b["at"]}
            if b["lift"]:
                tr["lift"] = b["lift"]
            beds["tracks"].append(tr)
        sfx, seen = {"narration": narr, "tracks": []}, {}
        for f in self.sounds:
            key = (f["file"], f["under"])
            if key not in seen:                       # one baked copy per file and level
                seen[key] = f["id"]
                tr = {"id": f["id"], "file": f["file"], "under_speech_db": f["under"], "why": f["purpose"]}
                if f["dur"]:
                    tr.update(src_start=0.0, dur=f["dur"], fade_out=f["fade_out"])
                sfx["tracks"].append(tr)
            f["baked_as"] = seen[key]
        return beds, sfx

    def plans(self):
        beds, sfx = self.plan_docs()
        write_json(self.kit.edit / "bed-plan.json", beds)
        write_json(self.kit.edit / "sfx-plan.json", sfx)
        return beds, sfx

    def _levels(self, plan, bake, out):
        r = subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "static_core.py"), "bed-levels", "--plan",
                            str(plan), "--bake", str(bake), "--out", str(out), "--run", str(self.kit.run), "--video",
                            str(self.kit.video)], capture_output=True, text=True, encoding="utf-8", errors="replace")
        try:
            return json.loads(r.stdout[r.stdout.index("{"):])
        except ValueError:
            raise KitError("bed-levels: " + (r.stdout + r.stderr)[-1500:])

    def bake(self, say=print):
        """bed-levels for both plans, then sound-placements.json (what the project is built from)."""
        self.plans()
        e = self.kit.edit
        a = self._levels(e / "bed-plan.json", self.music / "baked", e / "bed-levels.json")
        b = self._levels(e / "sfx-plan.json", self.sfx / "baked", e / "sfx-levels.json")
        for ans in (a, b):
            if ans.get("issues") or ans.get("error"):
                say("ISSUES", json.dumps(ans.get("issues") or ans.get("error"), ensure_ascii=False)[:1500])
        baked = {t["id"]: t for t in (a.get("tracks") or []) + (b.get("tracks") or [])}
        out = {"beds": [], "sfx": []}
        for x in self.beds:
            out["beds"].append({"id": x["id"], "file": baked[x["id"]]["baked"]["file"], "at": x["at"], "end": x["end"],
                                "beats": self.kit.beats_of(x["at"], x["end"]), "kind": x["kind"], "why": x["why"]})
        for f in self.sounds:
            file = baked[f["baked_as"]]["baked"]["file"]
            out["sfx"].append({"id": f["id"], "file": file, "at": f["at"],
                               "beats": self.kit.beats_of(f["at"], f["at"] + media_seconds(file)),
                               "purpose": f["purpose"]})
        write_json(e / "sound-placements.json", out)
        return out


# ------------------------------------------------------------------------------------------------ looking at the export
def frames(kit, film, out_prefix, items):
    """Contact sheets of frames from the exported film: items are "S001" (near the shot's end), "S001:0.5" (that
    far through it) or "@12.3" (a second). Nine frames a sheet. For looking at what changed after a revision."""
    from PIL import Image, ImageDraw, ImageFont
    out_prefix = Path(out_prefix)
    tmp = out_prefix.parent / "frames-tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    try:
        font = ImageFont.truetype("arialbd.ttf", 18)
    except OSError:
        font = ImageFont.load_default()
    cells = []
    for it in items:
        sid, _, fr = it.partition(":")
        if sid.startswith("@"):
            t = float(sid[1:])
            lab = f"{t:.1f}s"
        else:
            if sid not in kit.shots:
                raise KitError(f"{sid}: not a shot of the edit plan")
            s = kit.shots[sid]
            t = s["start_s"] + (s["end_s"] - s["start_s"]) * float(fr or 0.88)
            lab = f"{sid} {t:.1f}s"
        f = tmp / f"{lab.replace(' ', '_')}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(film), "-frames:v", "1", "-vf",
                        "scale=640:360", "-q:v", "3", str(f)], check=True)
        im = Image.open(f).convert("RGB")
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 150, 22], fill=(0, 0, 0))
        d.text((4, 1), lab, fill=(255, 235, 60), font=font)
        cells.append(im)
    made = []
    for n in range(0, len(cells), 9):
        part = cells[n:n + 9]
        sheet = Image.new("RGB", (1920, 360 * ((len(part) + 2) // 3)), (20, 20, 20))
        for i, im in enumerate(part):
            sheet.paste(im, ((i % 3) * 640, (i // 3) * 360))
        p = f"{out_prefix}-{n // 9 + 1:02d}.jpg"
        sheet.save(p, quality=84)
        made.append(p)
    return made


def edges(kit, film):
    """Shots whose still shows its own border in the exported frame: a pale band at an edge that stops, or a drawn
    line along it. {shot: ["bottom:paper12", "left:line@2"]}. Places to look, never a verdict: snow, a white floor
    or a dark thing at the edge read the same, and each one named is looked at (frames)."""
    import numpy as np
    from PIL import Image
    tmp = kit.edit / "edges-tmp.png"

    def side_rows(a, side, n=18):
        if side == "top":
            return [a[i, ::4] for i in range(n)]
        if side == "bottom":
            return [a[-1 - i, ::4] for i in range(n)]
        if side == "left":
            return [a[::4, i] for i in range(n)]
        return [a[::4, -1 - i] for i in range(n)]

    found = {}
    try:
        for s in kit.edit_plan["shots"]:
            for fr in (0.08, 0.92):
                t = s["start_s"] + (s["end_s"] - s["start_s"]) * fr
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(film), "-frames:v", "1",
                                str(tmp)], check=True)
                a = np.asarray(Image.open(tmp).convert("RGB")).astype(int)
                for side in ("top", "bottom", "left", "right"):
                    rows = side_rows(a, side)
                    dark = [float((r.sum(axis=1) < 160).mean()) for r in rows]
                    pale = [float(((r[:, 0] > 205) & (r[:, 1] > 198) & (r[:, 2] > 180)
                                   & (r.max(axis=1) - r.min(axis=1) < 40)).mean()) for r in rows]
                    line = next((i for i, d in enumerate(dark[:12]) if d >= 0.6), None)
                    # a drawn line is thin: the dark stops within a few rows. A dark picture at the edge (a night
                    # street, a shaft) goes on being dark and is not a line.
                    thin = line is not None and any(d < 0.3 for d in dark[line + 1:line + 7])
                    if thin and (line == 0 or max(pale[:line]) >= 0.8 or line <= 3):
                        found.setdefault(s["id"], set()).add(f"{side}:line@{line}")
                    elif pale[0] >= 0.9 and min(pale[8:]) < 0.35:
                        k = next(i for i, p in enumerate(pale) if p < 0.5)
                        found.setdefault(s["id"], set()).add(f"{side}:paper{k}")
    finally:
        if tmp.exists():
            tmp.unlink()
    return {k: sorted(v) for k, v in found.items()}


# ------------------------------------------------------------------------------------------------ command line
def main(argv=None):
    ap = argparse.ArgumentParser(description="The director's kit (manual 04).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def runp(name, help_):
        p = sub.add_parser(name, help=help_)
        p.add_argument("--run", required=True)
        p.add_argument("--video", type=int, default=1)
        return p

    p = runp("word-time", "when a spoken phrase falls: in the narration's file, on the edit's clock, inside a shot")
    p.add_argument("--line", required=True)
    p.add_argument("--phrase")
    p.add_argument("--end", action="store_true")
    p.add_argument("--rev", action="store_true", help="count from the line's end (a phrase after a spoken figure)")
    p.add_argument("--shot")
    p = runp("still-jobs", "one job file per still, from the shot plan and the locked look")
    p.add_argument("--direct", default="section,map,diagram,chart")
    p = runp("stills", "status | run S001 S004 ... | run --todo [N]: one worker run per still")
    p.add_argument("--wait-commit-gb", type=float, default=0.0)
    p.add_argument("--hours", type=float, default=8.0)
    p.add_argument("--todo", type=int, nargs="?", const=999, default=None,
                   help="with run: the next N stills that have no picture yet (all of them with no N)")
    p.add_argument("what", nargs="+")
    runp("margins", "each still's border and the scale that hides it")
    p = runp("frames", "contact sheets of frames from an exported film")
    p.add_argument("--file", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("items", nargs="+")
    p = runp("edges", "shots whose still shows its own border in the exported frame")
    p.add_argument("--file", required=True)
    p = sub.add_parser("tone", help="a synthesised sustained tone a small speaker can play")
    p.add_argument("--out", required=True)
    p.add_argument("--seconds", type=float, required=True)
    p = sub.add_parser("loop", help="a sound played several times in a row as one file")
    p.add_argument("--src", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--times", type=int, required=True)
    a = ap.parse_args(argv)

    def emit(doc):
        print(json.dumps(doc, ensure_ascii=False, indent=1))
        return 0 if doc.get("ok", True) else 1
    try:
        if a.cmd == "tone":
            return emit({"ok": True, "file": a.out, "seconds": tone(a.out, a.seconds), "synthesised": True})
        if a.cmd == "loop":
            return emit({"ok": True, "file": a.out, "seconds": loop(a.src, a.out, a.times)})
        kit = Kit(a.run, a.video)
        if a.cmd == "word-time":
            line = a.line if a.line.upper().startswith("L") else f"L{int(a.line):03d}"
            out = {"ok": True, "line": line.upper(), "phrase": a.phrase,
                   "narration_s": round(kit.word_time(line.upper(), a.phrase, a.end, a.rev, clock="narration"), 3),
                   "edit_s": round(kit.word_time(line.upper(), a.phrase, a.end, a.rev), 3)}
            if a.shot:
                if a.shot not in kit.shots:
                    raise KitError(f"{a.shot}: not a shot of the edit plan")
                s = kit.shots[a.shot]
                out["in_shot_s"] = round(out["edit_s"] - s["start_s"], 3)
                out["shot"] = {"id": a.shot, "start_s": s["start_s"], "end_s": s["end_s"],
                               "holds_the_phrase": s["start_s"] <= out["edit_s"] < s["end_s"]}
            return emit(out)
        if a.cmd == "still-jobs":
            n = Stills(kit).write_jobs(direct=tuple(x for x in a.direct.split(",") if x))
            return emit({"ok": True, "jobs": n, "folder": str(kit.vis / "jobs")})
        if a.cmd == "stills":
            st = Stills(kit)
            if a.what[0] == "status":
                have, todo = st.status()
                return emit({"ok": True, "made": len(have), "to_make": todo})
            if a.what[0] != "run":
                raise KitError("stills: status, or run")
            ids = a.what[1:] + (st.todo(a.todo) if a.todo is not None else [])
            if not ids:
                return emit({"ok": True, "results": {}, "note": "nothing to draw: name the stills, or --todo"})
            if a.wait_commit_gb and not wait_for_memory(a.wait_commit_gb, hours=a.hours):
                return emit({"ok": False, "error": "the memory the picture maker needs did not come free"})
            return emit({"ok": True, "results": {sid: st.run_one(sid) for sid in ids}})
        if a.cmd == "margins":
            crop = Framing(kit).measure()
            return emit({"ok": True, "stills": len(crop),
                         "border_to_hide": {k: {"scale": v["min_scale"], "px": v["margins_px"]}
                                            for k, v in crop.items() if any(v["margins_px"].values())},
                         "note": "a measure, fooled both ways by snow or a pale sky at the edge: check the framing "
                                 "on the export (edges)"})
        if a.cmd == "frames":
            return emit({"ok": True, "sheets": frames(kit, a.file, a.out, a.items)})
        if a.cmd == "edges":
            found = edges(kit, a.file)
            return emit({"ok": True, "shots_to_look_at": found, "count": len(found),
                         "note": "places to look, never a verdict: snow or a dark thing at the edge reads the same"})
    except KitError as e:
        return emit({"ok": False, "error": str(e)})
    return 0


if __name__ == "__main__":
    sys.exit(main())
