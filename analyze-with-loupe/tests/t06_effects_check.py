"""The CapCut effects check's measuring side (`T capcut-check effects-measure`), on synthetic files made to look like what CapCut exports
when every way of writing an effect plays: the check project's stills, overlays, caption and sounds composed by ffmpeg with the toolkit's
own effect chain. One run as an export, one as a full-screen screen recording of CapCut's player (lined up from the first click and
the stills' switches), and one where the green screen was not keyed (the measure must say so). Nothing of CapCut is needed."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from t00_common import AWL, check, finish, t, temp_library  # noqa: E402

sys.path.insert(0, str(Path(AWL).resolve().parent))
import awl as _awl  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageFilter  # noqa: E402

home = temp_library("fxcheck")
ENV = {"AWL_HOME": str(home)}
work = home.parent / "work"
work.mkdir()
media = home / "runs" / "_capcut-check" / "effects" / "media"
_awl._fx_check_media(media)
FF = _awl.find_tool("ffmpeg")
C = _awl.FX_CHECK
W, H, FPS, L = 1080, 1920, 30, float(C["length_s"])

# two textured stills: A warm, B cool (the stills the check project alternates every 3 s)
rng = np.random.default_rng(6)
for name, tint in (("A", (1.25, 1.0, 0.7)), ("B", (0.7, 1.0, 1.3))):
    base = rng.integers(40, 215, (H // 8, W // 8, 3)).astype(float)
    im = Image.fromarray(np.clip(base * np.array(tint), 0, 255).astype("uint8")).resize((W, H), Image.NEAREST).filter(ImageFilter.GaussianBlur(2))
    im.save(work / f"still-{name}.png")
shutil.copy(Path("C:/Windows/Fonts/arialbd.ttf") if Path("C:/Windows/Fonts/arialbd.ttf").is_file() else
            next(Path("C:/Windows/Fonts").glob("*.ttf")), work / "font.ttf")


def compose(out: Path, key_green: bool = True):
    """The check project as CapCut should export it: ten stills of 3 s, the overlays by the toolkit's own chain, the caption low on the
    canvas, the sounds (the first green wipe's tone at its volume, the second muted)."""
    args = [FF, "-nostdin", "-y", "-loglevel", "error"]
    for k in range(10):
        args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{C['still_s']}", "-i", str(work / f"still-{'AB'[k % 2]}.png")]
    fx = []
    for n, o in enumerate(C["overlays"], 1):
        f = media / o["file"]
        info = _awl.media_summary(f)
        dur = float(o.get("dur_s") or info.get("duration_s") or 2.0)
        blend = {"capcut-chroma": "chroma", "capcut-screen": "screen", "plain": "normal"}[o["method"]]
        if blend == "chroma" and not key_green:
            blend = "normal"
        fx.append({"n": n, "type": "overlay", "file": str(f), "kind": "image" if f.suffix == ".png" else "video", "start": o["start"],
                   "end": o["start"] + dur, "in_s": 0.0, "dur_s": dur, "blend": blend, "fit": o["fit"], "key_color": "#00FF00",
                   "key_intensity": o.get("key_intensity", 0.5), "scale": o.get("scale", 1.0), "x": o.get("x", 0.0), "y": o.get("y", 0.0),
                   "opacity": 1.0, "width": info.get("display_width"), "height": info.get("display_height"), "head_cut_s": 0.0})
        if fx[-1]["kind"] == "image":
            args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", str(f)]
        else:
            # vp9 alpha needs libvpx as the decoder (ffmpeg's own vp9 decoder drops alpha, as an app without it would)
            args += ["-ss", "0", "-t", f"{dur:.3f}", "-i", str(f)]
    fc = ["".join(f"[{k}:v]" for k in range(10)) + "concat=n=10:v=1:a=0,fps=30,format=yuv420p[vout]"]
    lines, label = _awl._fx_render_chain(fx, "vout", 10, W, H, FPS, L)
    fc += lines
    cy = int(H * (0.5 + 0.5 * abs(C["caption_y"])))
    fc.append(f"[{label}]drawtext=fontfile=font.ttf:text=CAPTION:fontsize=96:fontcolor=white:borderw=9:bordercolor=black:"
              f"x=(w-tw)/2:y={cy}-th/2[vcap]")
    na = 10 + len(fx)
    snd = [(media / s["file"], s["start"], s["volume"], float(s.get("fade_out_s") or 0)) for s in C["sounds"]]
    snd.append((media / "green-wipe.mp4", C["overlays"][0]["start"], C["overlays"][0]["volume"], 0.0))
    for k, (f, st, vol, fo) in enumerate(snd):
        args += ["-i", str(f)]
        dur = float(_awl.media_summary(f).get("duration_s") or 0.1)
        ch = f"[{na + k}:a]aresample=48000,aformat=channel_layouts=stereo"
        if fo:
            ch += f",afade=t=out:st={max(0.0, dur - fo):.3f}:d={fo:.3f}"
        ms = int(round(st * 1000))
        fc.append(ch + f",volume={vol},adelay={ms}|{ms},apad=whole_dur={L},atrim=0:{L}[s{k}]")
    fc.append("".join(f"[s{k}]" for k in range(len(snd))) + f"amix=inputs={len(snd)}:normalize=0:duration=first[aout]")
    cp = subprocess.run(args + ["-filter_complex", ";".join(fc), "-map", "[vcap]", "-map", "[aout]", "-t", f"{L}", "-r", str(FPS),
                               "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", str(out)],
                        capture_output=True, text=True, cwd=str(work))
    assert cp.returncode == 0, cp.stderr[-1500:]
    return out


(media.parent / "manifest.json").write_text(json.dumps({"draft": "synthetic", "made": "test", "settings": C, "canvas": [W, H],
                                                        "written": [], "failed": [], "capcut": "test"}), encoding="utf-8")
exp = compose(work / "export.mp4")
js, code, _ = t("capcut-check", "effects-measure", "--export", str(exp), env=ENV, ok=False, timeout=1800)
e = js.get("effects") or {}
want = ("chroma", "cover_scale", "captions_above_overlays", "screen", "alpha_video", "alpha_image", "overlay_keyframes", "overlay_sound",
        "mute", "sfx", "sfx_volume", "sfx_fade")
cat = json.loads((home / "data" / "capcut-catalogue.json").read_text(encoding="utf-8")).get("effects", {}) if (home / "data" / "capcut-catalogue.json").is_file() else {}
check(code == 0 and all(e.get(k) is True for k in want) and cat.get("alpha_video", {}).get("codec") == "prores4444"
      and cat.get("chroma", {}).get("intensity") in (0.3, 0.5),
      f"effects-measure reads an export where every way plays as playing, with the first alpha format and a chroma strength ({e}, "
      f"codec {cat.get('alpha_video', {}).get('codec')}, intensity {cat.get('chroma', {}).get('intensity')}, error {js.get('error')}, "
      f"chroma tested {json.dumps((cat.get('chroma') or {}).get('tested'))})")
check((home / "data" / "capcut-catalogue.md").is_file() and "## Effects" in (home / "data" / "capcut-catalogue.md").read_text(encoding="utf-8"),
      "effects-measure writes the Effects table into the catalogue")

# the same as a screen recording: CapCut's player column (608x1080 at x 656) on a 1920x1080 screen, 1.7 s of the paused first frame
# before the play, the desktop sound with it
rec = work / "recording.mp4"
cp = subprocess.run([FF, "-nostdin", "-y", "-loglevel", "error", "-i", str(exp), "-filter_complex",
                     "[0:v]scale=608:1080,tpad=start_duration=1.7:start_mode=clone,pad=1920:1080:656:0:color=0x202020,fps=60[v];"
                     "[0:a]adelay=1700|1700[a]", "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p",
                     "-c:a", "aac", str(rec)], capture_output=True, text=True)
assert cp.returncode == 0, cp.stderr[-800:]
js, code, _ = t("capcut-check", "effects-measure", "--export", str(rec), "--crop", "608:1080:656:0", env=ENV, ok=False, timeout=1800)
e = js.get("effects") or {}
check(code == 0 and abs(float(js.get("start_s") or 0) - 1.7) < 0.05 and all(e.get(k) is True for k in want),
      f"effects-measure lines a screen recording up from its first click and the stills' switches (start {js.get('start_s')} for 1.7) "
      f"and reads the same ways as playing ({e}, error {js.get('error')}, align {js.get('align')})")

# a project whose green screen was not keyed: the measure says so
bad = compose(work / "export-unkeyed.mp4", key_green=False)
js, code, _ = t("capcut-check", "effects-measure", "--export", str(bad), env=ENV, ok=False, timeout=1800)
e = js.get("effects") or {}
check(code == 0 and e.get("chroma") is False and e.get("screen") is True and e.get("sfx") is True,
      f"effects-measure reads a green screen left on the picture as chroma not playing ({e.get('chroma')}), the rest unchanged")
cat = json.loads((home / "data" / "capcut-catalogue.json").read_text(encoding="utf-8"))["effects"]
check(_awl._fx_method({"type": "overlay", "blend": "chroma", "fit": "cover", "has_audio": False}, cat)[0] == "keyed-file:prores4444"
      and _awl._fx_method({"type": "overlay", "blend": "screen", "fit": "cover", "has_audio": False}, cat)[0] == "capcut-screen"
      and _awl._fx_method({"type": "sfx", "volume": 0.5, "fade_in_s": 0, "fade_out_s": 0.3}, cat)[0] == "sound",
      "with CapCut's chroma key not playing, capcut-effects keys a green screen into an alpha file (prores4444) and keeps the verified ways")
from t00_common import fails  # noqa: E402
if fails:
    print(f"kept for a look: {home.parent}")
else:
    shutil.rmtree(home.parent, ignore_errors=True)
finish()
