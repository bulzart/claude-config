"""render_ffmpeg.py — deterministic ffmpeg 9 render of an edit plan.

    python render_ffmpeg.py <edit-plan.json> --out <final.mp4> [--overlays overlays.ass] [--no-overlays]
                            [--single-pass-loudnorm] [--no-loudnorm] [--preset medium] [--verify] [--dry-run]

What it does (all from the plan, nothing ad hoc):
  1. probes every clip (ffprobe) and clamps 'out' to the real duration;
  2. normalises every clip to the canvas (generated clips may be 480x854 @ 24 fps): cover-fit scale+crop
     (or contain-fit pad), fps=30, setsar=1, yuv420p; optional transform.scale/x/y and punch_in (zoompan);
  3. trims + speed ramps (setpts / atempo chains) per piece, pieces concatenated;
  4. transitions between consecutive clips: cut (concat) or xfade/whip/zoom (xfade with the correct
     offset = accumulated length - duration; audio acrossfade);
  5. colour preset (eq/unsharp/noise/vignette) BEFORE the text so overlays stay crisp;
  6. overlays: libass 'ass' filter with overlays.ass (Windows path escaped as C\\:/...) + fontsdir, and
     PNG stickers through overlay=enable='between(t,a,b)';
  7. audio: clip audio (or silence for mute clips) + music bed with sidechain ducking (sidechaincompress
     keyed by the clip mix) + SFX (adelay + amix), then loudnorm to the plan target (two-pass by default);
  8. export 1080x1920 30 fps H.264 High 4.1 CRF 18-20, AAC 192-256k, +faststart.
The filter graph is written to <out>.filter.txt and passed with "-/filter_complex <file>" (ffmpeg >= 7 option-from-file
form; -filter_complex_script no longer exists in ffmpeg 9) so there is no shell quoting at all;
the exact argv is logged to <out>.cmd.txt, ffmpeg stderr to <out>.log, a probe/verification summary to
<out>.report.json and one line to render\\history.md.

Speech captions are never rendered: the only text input is overlays.ass from text_overlays.py, which
refuses transcript-shaped input; a plan carrying a captions block is refused by common_edit.load_plan.

Exit codes: 0 ok, 1 plan/usage error, 2 ffmpeg or verification failure, 3 refused (caption-shaped plan).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_edit as ce  # noqa: E402

AUDIO_FMT = "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo"
COLOUR_PRESETS = {
    "none": "",
    "clean": "eq=saturation=0.97:contrast=1.02",
    "realism-v1": "eq=saturation=0.92:contrast=1.03:gamma=0.98,unsharp=3:3:0.35,noise=alls={grain}:allf=t+u,vignette=PI/5.5",
    "realism-soft": "eq=saturation=0.94:contrast=1.02,noise=alls={grain}:allf=t+u",
}


def atempo_chain(speed: float) -> str:
    """atempo accepts 0.5..100 per instance (ffmpeg >= 4.4 allows up to 100); chain for < 0.5."""
    if abs(speed - 1.0) < 1e-6:
        return ""
    parts = []
    s = speed
    while s < 0.5:
        parts.append("atempo=0.5")
        s /= 0.5
    while s > 2.0:
        parts.append("atempo=2.0")
        s /= 2.0
    parts.append(f"atempo={s:.6f}")
    return ",".join(parts)


def norm_chain(W: int, H: int, fps: int, transform: dict, probe: dict) -> str:
    fit = (transform or {}).get("fit", "cover")
    if fit == "contain":
        chain = (f"scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos,"
                 f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black")
    else:
        chain = f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}"
    sc = float((transform or {}).get("scale", 1.0) or 1.0)
    dx = float((transform or {}).get("x", 0.0) or 0.0)
    dy = float((transform or {}).get("y", 0.0) or 0.0)
    if abs(sc - 1.0) > 1e-6 or dx or dy:
        sc = max(sc, 1.0)
        chain += (f",scale=iw*{sc:.4f}:ih*{sc:.4f}:flags=lanczos,"
                  f"crop={W}:{H}:(iw-{W})/2+({dx:.1f}):(ih-{H})/2+({dy:.1f})")
    if probe.get("width", 0) and probe["width"] < W * 0.9:
        chain += ",unsharp=5:5:0.3"  # upscaled source: light sharpen (playbook 3.1)
    chain += f",fps={fps},setsar=1,format=yuv420p"
    pi = (transform or {}).get("punch_in")
    if pi:
        to = float(pi.get("to", 1.08))
        fr = int(pi.get("frames", 9))
        chain += (f",zoompan=z='if(lte(on,{fr}),1+({to:.4f}-1)*on/{fr},{to:.4f})':d=1:"
                  f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={fps}")
    # xfade refuses inputs whose timebases differ (zoompan/concat emit 1/1000000, fps emits 1/30):
    # pin every clip to 1/fps here and again after every concat / xfade (see build_graph).
    chain += f",settb=1/{fps}"
    return chain


def build_graph(plan: dict, base: str, placed: list[dict], total: float, probes: dict, overlays_ass: str | None,
                inputs: list[list[str]], measured: dict | None, single_pass: bool, no_loudnorm: bool,
                audio_only: bool = False) -> tuple[str, str, str]:
    """Return (filter_script_text, video_out_label, audio_out_label). `inputs` is filled with ffmpeg -i argv groups.
    audio_only=True builds just the audio side (loudnorm measurement pass): no video filters are configured."""
    proj = plan["project"]
    W, H, fps = int(proj["width"]), int(proj["height"]), int(proj["fps"])
    audio = plan.get("audio") or {}

    class _Lines(list):
        """video lines are dropped in audio_only mode; audio lines always kept."""
        def v(self, s: str) -> None:
            if not audio_only:
                self.append(s)

    lines = _Lines()
    idx = {}
    # --- inputs: clips in placed order, silence, music, sfx, stickers
    for i, p in enumerate(placed):
        path = ce.resolve_path(p["clip"]["path"], base)
        inputs.append(["-i", path])
        idx[("clip", i)] = len(inputs) - 1
    inputs.append(["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"])
    idx["silence"] = len(inputs) - 1
    music = audio.get("music") or None
    music_path = ce.resolve_path(music.get("path"), base) if music and music.get("path") else None
    if music_path and os.path.isfile(music_path):
        inputs.append(["-i", music_path])
        idx["music"] = len(inputs) - 1
    sfx_list = []
    for k, s in enumerate(audio.get("sfx") or []):
        sp = ce.resolve_path(s.get("path"), base)
        if sp and os.path.isfile(sp):
            inputs.append(["-i", sp])
            idx[("sfx", k)] = len(inputs) - 1
            sfx_list.append((k, s))
    stickers = []
    for k, ov in enumerate(plan.get("text_overlays") or []):
        if ov.get("type") == "sticker" and ov.get("image"):
            ip = ce.resolve_path(ov["image"], base)
            if ip and os.path.isfile(ip):
                inputs.append(["-i", ip])
                idx[("sticker", k)] = len(inputs) - 1
                stickers.append((k, ov))
    # --- per clip video/audio
    orig_gain = float(audio.get("original_gain", 1.0) if audio.get("original_gain") is not None else 1.0)
    for i, p in enumerate(placed):
        c = p["clip"]
        n = idx[("clip", i)]
        pr = probes[ce.resolve_path(c["path"], base)]
        vparts, aparts = [], []
        for j, (a, b, s) in enumerate(p["pieces"]):
            vl = f"v{i}_{j}"
            lines.v(f"[{n}:v]trim=start={a:.4f}:end={b:.4f},setpts=(PTS-STARTPTS)/{s:.6f}[{vl}]")
            vparts.append(vl)
            al = f"a{i}_{j}"
            if pr.get("has_audio"):
                chain = f"[{n}:a]atrim=start={a:.4f}:end={b:.4f},asetpts=PTS-STARTPTS"
                at = atempo_chain(s)
                if at:
                    chain += "," + at
                chain += f",{AUDIO_FMT}[{al}]"
            else:
                chain = f"[{idx['silence']}:a]atrim=0:{(b - a) / s:.4f},asetpts=PTS-STARTPTS,{AUDIO_FMT}[{al}]"
            lines.append(chain)
            aparts.append(al)
        if len(vparts) > 1:
            lines.v("".join(f"[{x}]" for x in vparts) + f"concat=n={len(vparts)}:v=1:a=0,settb=1/{fps}[v{i}raw]")
            lines.append("".join(f"[{x}]" for x in aparts) + f"concat=n={len(aparts)}:v=0:a=1[a{i}raw]")
        else:
            lines.v(f"[{vparts[0]}]null[v{i}raw]")
            lines.append(f"[{aparts[0]}]anull[a{i}raw]")
        lines.v(f"[v{i}raw]{norm_chain(W, H, fps, c.get('transform'), pr)}[v{i}]")
        gain = float(c.get("volume", 1.0) if c.get("volume") is not None else 1.0) * orig_gain
        lines.append(f"[a{i}raw]volume={gain:.4f}[a{i}]")
    # --- assembly with transitions
    vacc, aacc = "v0", "a0"
    L = placed[0]["duration"]
    for i in range(1, len(placed)):
        p = placed[i]
        tr = p["transition_in"]
        vo, ao = f"vx{i}", f"ax{i}"
        if not tr or tr.get("type", "cut") == "cut":
            lines.v(f"[{vacc}][v{i}]concat=n=2:v=1:a=0,settb=1/{fps}[{vo}]")
            lines.append(f"[{aacc}][a{i}]concat=n=2:v=0:a=1[{ao}]")
            L += p["duration"]
        else:
            name, _ = ce.XFADE_MAP.get(tr["type"], ("fade", 0.4))
            name = tr.get("xfade") or name
            d = float(tr["duration"])
            off = max(0.0, L - d)
            lines.v(f"[{vacc}][v{i}]xfade=transition={name}:duration={d:.4f}:offset={off:.4f},settb=1/{fps}[{vo}]")
            lines.append(f"[{aacc}][a{i}]acrossfade=d={d:.4f}:c1=tri:c2=tri[{ao}]")
            L += p["duration"] - d
        vacc, aacc = vo, ao
    # --- colour
    col = plan.get("colour") or {}
    preset = str(col.get("preset", "realism-v1") or "none")
    grain = int(col.get("grain", 7) if col.get("grain") is not None else 7)
    cchain = col.get("filters") or COLOUR_PRESETS.get(preset, COLOUR_PRESETS["none"])
    cchain = cchain.format(grain=grain) if cchain else ""
    if col.get("lut") and os.path.isfile(ce.resolve_path(col["lut"], base)):
        cchain = (cchain + "," if cchain else "") + f"lut3d=file='{ce.ffpath(ce.resolve_path(col['lut'], base))}'"
    if cchain:
        lines.v(f"[{vacc}]{cchain}[vcol]")
        vacc = "vcol"
    # --- overlays
    if overlays_ass:
        fd = ce.ffpath(ce.FONTS_DIR)
        lines.v(f"[{vacc}]ass=filename='{ce.ffpath(overlays_ass)}':fontsdir='{fd}'[vtxt]")
        vacc = "vtxt"
    for k, ov in stickers:
        n = idx[("sticker", k)]
        pos = ov.get("position") or {}
        sw = int(ov.get("width_px") or 300)
        x = float(pos.get("x_px", W / 2))
        y = float(pos.get("y_px", H / 2))
        t0, t1 = float(ov.get("t_start", 0)), float(ov.get("t_end", total))
        lines.v(f"[{n}:v]scale={sw}:-1:flags=lanczos,format=rgba[stk{k}]")
        lines.v(f"[{vacc}][stk{k}]overlay=x={x:.0f}-w/2:y={y:.0f}-h/2:enable='between(t,{t0:.3f},{t1:.3f})':"
                f"eof_action=repeat[vst{k}]")
        vacc = f"vst{k}"
    lines.v(f"[{vacc}]format=yuv420p[vout]")
    # --- audio mix
    mix_inputs = []
    main_label = aacc
    if "music" in idx:
        gain_db = ce.gain_db(music, -18.0)
        start = float(music.get("start", 0.0) or 0.0)
        ms = int(round(start * 1000))
        chain = f"[{idx['music']}:a]{AUDIO_FMT},volume={gain_db:.2f}dB"
        if ms > 0:
            chain += f",adelay={ms}|{ms}"
        chain += f",atrim=0:{L:.4f},asetpts=PTS-STARTPTS[mus]"
        lines.append(chain)
        duck = music.get("ducking") or {}
        if duck.get("enabled", True):
            thr = float(duck.get("threshold", 0.05))
            ratio = float(duck.get("ratio", 6))
            att = float(duck.get("attack", 20))
            rel = float(duck.get("release", 300))
            lines.append(f"[{main_label}]asplit=2[amain][akey]")
            lines.append(f"[mus][akey]sidechaincompress=threshold={thr}:ratio={ratio}:attack={att}:release={rel}:"
                         f"makeup=1[musd]")
            main_label = "amain"
            mix_inputs.append("musd")
        else:
            mix_inputs.append("mus")
    for k, s in sfx_list:
        n = idx[("sfx", k)]
        ms = int(round(float(s.get("at", 0.0)) * 1000))
        g = ce.gain_db(s, -12.0)
        lines.append(f"[{n}:a]{AUDIO_FMT},volume={g:.2f}dB,adelay={ms}|{ms}[sfx{k}]")
        mix_inputs.append(f"sfx{k}")
    if mix_inputs:
        lines.append(f"[{main_label}]" + "".join(f"[{x}]" for x in mix_inputs) +
                     f"amix=inputs={1 + len(mix_inputs)}:duration=first:normalize=0:dropout_transition=0[amix]")
        alabel = "amix"
    else:
        alabel = main_label
    ln = audio.get("loudness_target") or {}
    I = float(ln.get("i", -14.0)); TP = float(ln.get("tp", -1.0)); LRA = float(ln.get("lra", 11.0))
    if no_loudnorm:
        lines.append(f"[{alabel}]anull[aout]")
    elif measured:
        lines.append(f"[{alabel}]loudnorm=I={I}:TP={TP}:LRA={LRA}:measured_I={measured['input_i']}:"
                     f"measured_TP={measured['input_tp']}:measured_LRA={measured['input_lra']}:"
                     f"measured_thresh={measured['input_thresh']}:offset={measured['target_offset']}:linear=true[aout]")
    elif single_pass:
        lines.append(f"[{alabel}]loudnorm=I={I}:TP={TP}:LRA={LRA}[aout]")
    else:
        lines.append(f"[{alabel}]loudnorm=I={I}:TP={TP}:LRA={LRA}:print_format=json[aout]")
    return ";\n".join(lines) + "\n", "vout", "aout"


def parse_loudnorm_json(stderr: str) -> dict | None:
    m = re.search(r"\{\s*\"input_i\".*?\}", stderr, re.S)
    if not m:
        return None
    try:
        j = json.loads(m.group(0))
        return {k: j[k] for k in ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")}
    except Exception:
        return None


def faststart_ok(path: str) -> bool:
    """moov atom must come before mdat at the top level."""
    try:
        with open(path, "rb") as f:
            pos = 0
            size = os.path.getsize(path)
            order = []
            while pos < size and len(order) < 8:
                f.seek(pos)
                hdr = f.read(16)
                if len(hdr) < 8:
                    break
                alen, atype = struct.unpack(">I4s", hdr[:8])
                if alen == 1:
                    alen = struct.unpack(">Q", hdr[8:16])[0]
                elif alen == 0:
                    alen = size - pos
                order.append(atype.decode("latin1"))
                pos += max(alen, 8)
            return "moov" in order and "mdat" in order and order.index("moov") < order.index("mdat")
    except Exception:
        return False


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="ffmpeg 9 renderer for analyze-stack edit plans")
    ap.add_argument("plan")
    ap.add_argument("--out", required=True, help="output mp4 (absolute)")
    ap.add_argument("--overlays", help="overlays.ass (default <plan dir>\\overlays.ass; generated if missing)")
    ap.add_argument("--no-overlays", action="store_true")
    ap.add_argument("--single-pass-loudnorm", action="store_true")
    ap.add_argument("--no-loudnorm", action="store_true")
    ap.add_argument("--preset", default=None, help="x264 preset override (plan.export.preset)")
    ap.add_argument("--verify", action="store_true", help="ffprobe the output and fail on mismatch")
    ap.add_argument("--dry-run", action="store_true", help="write filter script + command, do not run ffmpeg")
    args = ap.parse_args(argv)
    try:
        plan, base = ce.load_plan(args.plan)
    except ce.PlanError as e:
        print(f"REFUSED/INVALID: {e}", file=sys.stderr)
        return 3 if "owner rule" in str(e) else 1
    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    stem = os.path.splitext(out)[0]
    log = stem + ".log"
    if os.path.exists(log):
        os.remove(log)
    # probes
    probes = {}
    for c in plan["clips"]:
        p = ce.resolve_path(c["path"], base)
        if not os.path.isfile(p):
            print(f"clip {c['id']}: file not found {p}", file=sys.stderr)
            return 1
        probes[p] = ce.probe_media(p)
    plan_for_tl = json.loads(json.dumps(plan))
    for c in plan_for_tl["clips"]:
        c["path"] = ce.resolve_path(c["path"], base)
    placed, total = ce.compute_timeline(plan_for_tl, probes)
    for p in placed:
        if "_clamped_out_from" in p["clip"]:
            print(f"note: clip {p['clip']['id']} out clamped {p['clip']['_clamped_out_from']} -> {p['clip']['out']} (media length)")
    # overlays
    overlays_ass = None
    if not args.no_overlays and (plan.get("text_overlays") or []):
        overlays_ass = os.path.abspath(args.overlays) if args.overlays else ce.default_overlays_path(args.plan)
        if not os.path.isfile(overlays_ass) or not args.overlays:
            import text_overlays
            rc = text_overlays.main([args.plan, "--out", overlays_ass, "--total-duration", f"{total:.3f}"])
            if rc != 0:
                print("overlay generation failed/refused; aborting render", file=sys.stderr)
                return 3 if rc == 3 else 1
        if not any((o.get("text") or "").strip() for o in plan["text_overlays"] if o.get("type") != "sticker" or not o.get("image")):
            overlays_ass = None
    # export settings
    ex = plan.get("export") or {}
    fps = int(plan["project"]["fps"])
    preset = args.preset or ex.get("preset", "medium")
    crf = int(ex.get("crf", 18))
    v_args = ["-c:v", ex.get("codec", "libx264"), "-profile:v", ex.get("profile", "high"), "-level", str(ex.get("level", "4.1")),
              "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p", "-r", str(fps), "-g", str(fps * 2),
              "-keyint_min", str(fps * 2), "-bf", "2"]
    if ex.get("tune"):
        v_args += ["-tune", str(ex["tune"])]
    a_args = ["-c:a", "aac", "-b:a", str(ex.get("audio_bitrate", "192k")), "-ar", "48000", "-ac", "2"]
    mov = ["-movflags", "+faststart"] if ex.get("faststart", True) else []

    def compose(measured, audio_only=False):
        inputs: list[list[str]] = []
        script, vl, al = build_graph(plan, base, placed, total, probes, overlays_ass, inputs, measured,
                                     args.single_pass_loudnorm, args.no_loudnorm, audio_only=audio_only)
        return script, inputs, vl, al

    measured = None
    if not (args.single_pass_loudnorm or args.no_loudnorm):
        script1, inputs1, vl, al = compose(None, audio_only=True)
        p1 = stem + ".pass1.filter.txt"
        ce.write_text(p1, script1)
        cmd1 = [ce.FFMPEG, "-y", "-hide_banner", "-nostats"]
        for g in inputs1:
            cmd1 += g
        cmd1 += ["-/filter_complex", p1, "-map", f"[{al}]", "-vn", "-f", "null", "-"]
        ce.write_text(stem + ".pass1.cmd.txt", " ".join(ce.ps_quote(a) for a in cmd1) + "\n")
        if not args.dry_run:
            cp = ce.run(cmd1, log_path=log)
            measured = parse_loudnorm_json(cp.stderr or "")
            if cp.returncode != 0 or not measured:
                print("loudnorm measurement pass failed; falling back to single-pass loudnorm", file=sys.stderr)
                args.single_pass_loudnorm = True
                measured = None
    script, inputs, vl, al = compose(measured)
    fpath = stem + ".filter.txt"
    ce.write_text(fpath, script)
    cmd = [ce.FFMPEG, "-y", "-hide_banner", "-loglevel", "info", "-nostats"]
    for g in inputs:
        cmd += g
    # ffmpeg >= 7 reads any option value from a file with the generic "-/opt <file>" form; the old
    # -filter_complex_script flag is gone in ffmpeg 9 ("Unrecognized option"). No shell quoting involved.
    cmd += ["-/filter_complex", fpath, "-map", f"[{vl}]", "-map", f"[{al}]"] + v_args + a_args + mov + [out]
    ce.write_text(stem + ".cmd.txt", " ".join(ce.ps_quote(a) for a in cmd) + "\n")
    report = {"plan": os.path.abspath(args.plan), "out": out, "planned_duration_s": total, "overlays_ass": overlays_ass,
              "loudnorm_measured": measured, "timeline": [{"id": p["clip"]["id"], "start": p["start"], "end": p["end"],
                                                           "pieces": p["pieces"], "transition_in": p["transition_in"]} for p in placed],
              "command_file": stem + ".cmd.txt", "filter_script": fpath, "log": log, "generated": ce.now_iso()}
    if args.dry_run:
        ce.save_json(stem + ".report.json", report)
        print(json.dumps({"dry_run": True, "planned_duration_s": total, "filter_script": fpath, "cmd": stem + ".cmd.txt"}))
        return 0
    cp = ce.run(cmd, log_path=log)
    if cp.returncode != 0:
        print(f"ffmpeg failed ({cp.returncode}); see {log}", file=sys.stderr)
        print((cp.stderr or "")[-3000:], file=sys.stderr)
        report["ffmpeg_exit"] = cp.returncode
        ce.save_json(stem + ".report.json", report)
        return 2
    pr = ce.probe_media(out)
    checks = {
        "width": pr["width"] == int(plan["project"]["width"]),
        "height": pr["height"] == int(plan["project"]["height"]),
        "fps": abs(pr["fps"] - fps) < 0.01,
        "duration": abs(pr["duration"] - total) <= 0.15,
        "audio": pr["has_audio"] and pr["sample_rate"] == 48000,
        "faststart": faststart_ok(out) if ex.get("faststart", True) else True,
    }
    report.update({"probe": pr, "checks": checks, "ffmpeg_exit": 0, "verified": all(checks.values())})
    ce.save_json(stem + ".report.json", report)
    ce.history_line(os.path.dirname(out), f"render {os.path.basename(out)} from {os.path.basename(args.plan)} "
                                          f"({pr['duration']:.2f}s, planned {total:.2f}s, checks {'ok' if all(checks.values()) else 'FAILED'})")
    print(json.dumps({"out": out, "duration_s": pr["duration"], "planned_s": total, "width": pr["width"], "height": pr["height"],
                      "fps": pr["fps"], "audio": pr["has_audio"], "checks": checks, "report": stem + ".report.json"}))
    if args.verify and not all(checks.values()):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
