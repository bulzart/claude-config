"""plan_from_clips.py — first edit-plan.json from the generated clips + clip-QA verdicts + trend brief.

    python plan_from_clips.py --run-dir <run> [--clip-qa <qa.json>] [--trend-brief <trend-brief.json>]
        [--manifest <manifest.json>] [--clips-dir <dir>] [--out <edit-plan.json>] [--name <project name>]
        [--platform universal|tiktok|tiktok-ads|reels|shorts] [--max-duration S] [--cta "text"]
        [--music <file> --music-gain-db -18] [--sfx-dir <dir>] [--handle-frames 6] [--json]

Defaults (run-relative): 80-generated\\manifest.json (else clip-*.mp4 in 80-generated\\ numbered by the first 1-2
digit group), 90-postgen\\qa.json, 90-postgen\\trend-brief.json, 10-measure\\cuts.json (cut cadence),
30-decisions\\answers.json (platform from Q6), 40-plan\\plan.json (planned seconds per clip), output
90-postgen\\edit-plan.json. Missing inputs are skipped with a note - the script never blocks on them - EXCEPT
that a missing qa.json / trend-brief.json falls back to 90-postgen\\clip-qa.md / trend-brief.md (the
references\\clip-qa-template.md and trend-brief-template.md formats; parsers qa_from_markdown / brief_from_markdown)
so QA verdicts are never silently lost; `--clip-qa x.md` / `--trend-brief x.md` select the Markdown explicitly.

Rules applied (references\\post-generation-playbook.md sections 2.4, 3, 4; contract "realism beats length"):
  * clip QA: S0/S1 or action=use -> whole clip; S2 or action=trim -> longest clean window (>= 1.5 s) with a
    6-frame handle where the window borders a flagged one; S3/S4, action=drop/regenerate or MISSING -> excluded
    (shorter and clean beats longer with anomalies; the planned duration is a ceiling, not a target).
  * order = prompt number (the plan order); every decision is written to meta.decisions[].
  * trend brief (references\\trend-brief-template.md JSON): hook_candidates[0] / text.hook recommendation ->
    hook_text overlay 0 - min(2.0 s, first cut); text.cta recommendation or --cta -> end card over the last 2 s;
    sounds[0] -> music (organic: attach in-app, never baked in; paid: licensed alternative or --music file);
    effects with use=true -> punch_in on the hook (zoom/punch), whip transition into the named clip or the
    reveal (last clip), xfade for crossfade/dissolve, speed-ramp -> note for the editor; recommendations that
    target captions are IGNORED and logged (owner rule: no speech captions in the edit).
  * colour: realism-v1 grain 7, or `clean` when the brief's do_not list mentions grain / the niche is clean studio.
  * cut cadence from cuts.json (median shot length, first cut) is recorded in meta.source_reference and any kept
    clip longer than 2x the median gets a note; nothing is cut automatically - the editor agent refines the plan.
The output is validated with common_edit.load_plan (so it can never carry caption-shaped content).

Exit codes: 0 ok, 1 usage/input error, 2 no usable clip.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_edit as ce  # noqa: E402

NUM_RE = re.compile(r"(?<!\d)(\d{1,2})(?!\d)")


def load_optional(path: str | None, notes: list[str], label: str):
    if not path:
        return None
    if not os.path.isfile(path):
        notes.append(f"{label}: not found ({path}) - skipped")
        return None
    try:
        return ce.load_json(path)
    except Exception as e:
        notes.append(f"{label}: unreadable ({e}) - skipped")
        return None


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8-sig") as f:
        return f.read()


_RANGE_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(?:s)?\s*[–—\-]\s*(\d+(?:\.\d+)?)\s*(?:s\b)?\s*(.*?)\s*$")
_ACTION_WORDS = {"REGENERATE": "regenerate", "REGEN": "regenerate", "TRIM": "trim", "DROP": "drop", "USE": "use",
                 "KEEP": "use", "MISSING": "missing"}


def qa_from_markdown(path: str) -> dict:
    """Fallback when qa.json is missing: parse clip-qa.md (references\\clip-qa-template.md) into the qa.json shape.
    Reads, per '## Clip NN' section: the file, the 'Windows:' line (ranges separated by the middle dot or ';',
    each 'a-b verdict' with 'clean' or an anomaly id), the 'Verdict:' line (severity S0-S4 + REGENERATE / TRIM /
    DROP / USE; 'TRIM to a-b' without a Windows line becomes the clean window), the A## ids in the section and a
    fix-prompts.md anchor. A section whose body says MISSING is dropped. qa.json remains the primary contract;
    this parser only stops a missing JSON from silently keeping flagged material."""
    text = _read_text(path)
    clips = []
    for m in re.finditer(r"^##\s+Clip\s+(\d{1,2})\b([^\n]*)\n(.*?)(?=^##\s+Clip\s+\d|\Z)", text, re.S | re.M):
        pn, header, body = int(m.group(1)), m.group(2), m.group(3)
        fm = re.search(r"(80-generated[\\/][^\s|]+?\.mp4)", header + " " + body)
        entry = {"prompt_no": pn, "file": fm.group(1).replace("\\", "/") if fm else f"80-generated/clip-{pn:02d}.mp4",
                 "severity": "S0", "anomalies": [], "windows": [], "action": "use", "fix_prompt": None, "source": "clip-qa.md"}
        if re.search(r"^\s*MISSING\b", body, re.M) or "MISSING" in header.upper():
            entry.update({"severity": "MISSING", "action": "drop", "note": "MISSING in clip-qa.md"})
            clips.append(entry)
            continue
        wm = re.search(r"^Windows:\s*(.+)$", body, re.M)
        if wm:
            for part in re.split(r"\s*[·;]\s*", wm.group(1).strip()):
                rm = _RANGE_RE.match(part)
                if not rm:
                    continue
                verdict = (rm.group(3) or "clean").strip().rstrip(".")
                verdict = "clean" if verdict.lower().startswith("clean") or not verdict else verdict
                entry["windows"].append({"t_in": float(rm.group(1)), "t_out": float(rm.group(2)), "verdict": verdict})
        vm = re.search(r"^Verdict:\s*(S[0-4]|MISSING)?\s*(?:→|->|=>|-|:)?\s*([A-Za-z]+)?(.*)$", body, re.M)
        if vm:
            if vm.group(1):
                entry["severity"] = vm.group(1).upper()
            word = (vm.group(2) or "").upper()
            entry["action"] = _ACTION_WORDS.get(word, entry["action"])
            if entry["action"] == "missing":
                entry.update({"severity": "MISSING", "action": "drop"})
            if entry["action"] == "trim" and not entry["windows"]:
                for rm in re.finditer(r"(\d+(?:\.\d+)?)\s*[–—\-]\s*(\d+(?:\.\d+)?)", vm.group(3) or ""):
                    entry["windows"].append({"t_in": float(rm.group(1)), "t_out": float(rm.group(2)), "verdict": "clean"})
        if entry["action"] == "use" and entry["severity"] in ("S2", "S3", "S4"):
            entry["action"] = {"S2": "trim", "S3": "regenerate", "S4": "drop"}[entry["severity"]]
        entry["anomalies"] = sorted({f"A{x}" for x in re.findall(r"\bA(\d{2})\b", body)})
        fp = re.search(r"fix-prompts\.md#[\w.-]+", body)
        if fp:
            entry["fix_prompt"] = "90-postgen/" + fp.group(0)
        clips.append(entry)
    clean = sum(1 for c in clips if c["severity"] in ("S0", "S1"))
    missing = sum(1 for c in clips if c["severity"] == "MISSING")
    return {"clips": clips, "summary": {"clean": clean, "flagged": len(clips) - clean - missing, "missing": missing},
            "source": path}


def _md_rows(section: str) -> list[list[str]]:
    rows = []
    for line in section.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c) or not any(cells):
            continue
        rows.append(cells)
    return rows


def _md_section(text: str, number: int) -> str:
    m = re.search(r"^##\s*" + str(number) + r"\.[^\n]*\n(.*?)(?=^##\s*\d+\.|\Z)", text, re.S | re.M)
    return m.group(1) if m else ""


def brief_from_markdown(path: str) -> dict:
    """Fallback when trend-brief.json is missing: parse trend-brief.md (references\\trend-brief-template.md) into the
    JSON companion's shape - fields table (niche, deliverable type), section 1 sounds (id, title, license, fit) +
    the licensed alternative, section 2 hook-text candidates, section 4 effects (use = 'yes ...'), section 6 duration
    sweet spot, section 7 recommendations (rank, text, edit-plan field) and the do-not-do list. Caption
    recommendations are still ignored downstream (owner rule)."""
    text = _read_text(path)
    b = {"schema": "analyze-stack.trend-brief/1", "source": path, "parsed_from": "markdown", "niche": "",
         "deliverable_type": "organic", "sounds": [], "licensed_alternative": {}, "hook_candidates": [], "effects": [],
         "posting": {}, "recommendations": [], "do_not": []}
    fm = re.search(r"^\|\s*Niche\s*\|\s*(.+?)\s*\|\s*$", text, re.M)
    if fm:
        b["niche"] = fm.group(1)
    dm = re.search(r"^\|\s*Deliverable type\s*\|\s*(.+?)\s*\|\s*$", text, re.M)
    if dm:
        v = dm.group(1).lower()
        b["deliverable_type"] = "paid" if ("paid" in v and "organic" not in v) else "organic"
    for cells in _md_rows(_md_section(text, 1)):
        if len(cells) >= 9 and re.fullmatch(r"tb-s\d+", cells[1]):
            fit = cells[8].split()[0].lower().strip(",;") if cells[8] else ""
            lic = next((w for w in re.findall(r"[a-z-]+", cells[7].lower())
                        if w in ("organic-only", "tiktok-cml", "meta-sound-collection", "owned", "unknown")), cells[7].lower() or "unknown")
            b["sounds"].append({"id": cells[1], "title": cells[2], "platform": cells[3], "momentum": cells[4], "source": cells[5],
                                "fetched_at": cells[6], "license": lic, "fit": fit, "fit_reason": cells[8]})
    am = re.search(r"Licensed alternative[^:\n]*:\s*(.+)", text)
    if am:
        alt = am.group(1)
        idm = re.search(r"\b(tb-alt\d+)\b", alt)
        lm = re.search(r"license\s+([a-z-]+)", alt, re.I)
        b["licensed_alternative"] = {"id": idm.group(1) if idm else "tb-alt1", "title": alt.split(" — ")[0].strip(),
                                     "license": (lm.group(1).lower() if lm else "unknown"), "url": ""}
    hm = re.search(r"Hook-text candidates[^:\n]*:\s*(.+)", text)
    if hm:
        b["hook_candidates"] = [h.strip().strip('"“”') for h in re.split(r"\s*\d+\.\s+", hm.group(1))
                                if h.strip() and h.strip() not in ("…", "...")]
    for cells in _md_rows(_md_section(text, 4)):
        if len(cells) >= 5 and re.fullmatch(r"tb-e\d+", cells[0]):
            use_cell = cells[4]
            use = use_cell.lower().startswith("yes")
            where = re.sub(r"^yes\s*[—\-:,]*\s*", "", use_cell, flags=re.I) if use else ""
            b["effects"].append({"id": cells[0], "name": cells[1], "frequency": cells[3], "use": use, "where": where})
    sm = re.search(r"Duration sweet spot[^:\n]*:\s*(\d+(?:\.\d+)?)\s*[–—\-]\s*(\d+(?:\.\d+)?)", text)
    if sm:
        b["posting"]["duration_sweet_spot_s"] = [float(sm.group(1)), float(sm.group(2))]
    for cells in _md_rows(_md_section(text, 7)):
        if len(cells) >= 5 and cells[0].isdigit():
            b["recommendations"].append({"rank": int(cells[0]), "text": cells[1], "evidence": [cells[2]], "risk": cells[3],
                                         "edit_plan_field": cells[4]})
    dnm = re.search(r"Do-not-do list[^:\n]*:\s*(.+)", text)
    if dnm:
        b["do_not"] = [x.strip() for x in dnm.group(1).split(";") if x.strip() and x.strip() not in ("<…>", "…")]
    return b


def load_qa(arg: str | None, run_dir: str, notes: list[str]) -> dict | None:
    """qa.json first (primary contract); clip-qa.md parsed as a fallback so a missing JSON never keeps flagged clips."""
    if arg and arg.lower().endswith(".md"):
        if os.path.isfile(arg):
            qa = qa_from_markdown(arg)
            qa["_loaded_from"] = os.path.abspath(arg)
            notes.append(f"clip QA: parsed from markdown {arg} ({len(qa['clips'])} sections)")
            return qa
        notes.append(f"clip QA: not found ({arg}) - skipped")
        return None
    src = arg or os.path.join(run_dir, "90-postgen", "qa.json")
    qa = load_optional(src, notes, "clip QA")
    if qa is None:
        md = os.path.join(run_dir, "90-postgen", "clip-qa.md")
        if os.path.isfile(md):
            qa = qa_from_markdown(md)
            qa["_loaded_from"] = os.path.abspath(md)
            notes.append(f"clip QA: qa.json missing - verdicts parsed from {md} ({len(qa['clips'])} sections); "
                         f"the main session should still write 90-postgen\\qa.json")
    elif isinstance(qa, dict):
        qa["_loaded_from"] = os.path.abspath(src)
    return qa


def load_brief(arg: str | None, run_dir: str, notes: list[str]) -> dict | None:
    """trend-brief.json first; trend-brief.md parsed as a fallback."""
    if arg and arg.lower().endswith(".md"):
        if os.path.isfile(arg):
            notes.append(f"trend brief: parsed from markdown {arg}")
            brief = brief_from_markdown(arg)
            brief["_loaded_from"] = os.path.abspath(arg)
            return brief
        notes.append(f"trend brief: not found ({arg}) - skipped")
        return None
    src = arg or os.path.join(run_dir, "90-postgen", "trend-brief.json")
    brief = load_optional(src, notes, "trend brief")
    if brief is None:
        md = os.path.join(run_dir, "90-postgen", "trend-brief.md")
        if os.path.isfile(md):
            brief = brief_from_markdown(md)
            brief["_loaded_from"] = os.path.abspath(md)
            notes.append(f"trend brief: trend-brief.json missing - parsed from {md} "
                         f"({len(brief['recommendations'])} recommendations, {len(brief['hook_candidates'])} hook candidates)")
    elif isinstance(brief, dict):
        brief["_loaded_from"] = os.path.abspath(src)
    return brief


def discover_clips(run_dir: str, manifest: dict | None, clips_dir: str, notes: list[str]) -> list[dict]:
    clips = []
    if manifest and isinstance(manifest.get("clips"), list):
        for m in manifest["clips"]:
            f = m.get("file")
            if not f:
                continue
            p = ce.resolve_path(f, run_dir)
            clips.append({"prompt_no": int(m.get("prompt_no") or 0), "path": p, "manifest": m})
        notes.append(f"clips from manifest: {len(clips)}")
    if not clips:
        files = sorted(glob.glob(os.path.join(clips_dir, "*.mp4")))
        for f in files:
            m = NUM_RE.search(os.path.basename(f))
            if not m:
                notes.append(f"no clip number in file name, skipped: {os.path.basename(f)}")
                continue
            clips.append({"prompt_no": int(m.group(1)), "path": os.path.abspath(f), "manifest": None})
        notes.append(f"clips from {clips_dir}: {len(clips)} (numbered by file name)")
    clips.sort(key=lambda c: (c["prompt_no"], c["path"]))
    return clips


def qa_for(qa: dict | None, prompt_no: int, path: str) -> dict | None:
    if not qa:
        return None
    for q in qa.get("clips") or []:
        if int(q.get("prompt_no") or -1) == prompt_no:
            return q
        if q.get("file") and os.path.basename(str(q["file"])).lower() == os.path.basename(path).lower():
            return q
    return None


def decide_window(q: dict | None, duration: float, fps: int, handle_frames: int) -> tuple[str, float, float, str]:
    """Returns (decision, in, out, reason). decision in use|trim|drop."""
    if not q:
        return "use", 0.0, duration, "no QA entry: whole clip"
    sev = str(q.get("severity", "S0")).upper()
    action = str(q.get("action", "")).lower()
    if action in ("drop",) or sev == "S4":
        return "drop", 0, 0, f"{sev} {','.join(q.get('anomalies') or [])}: dropped ({action or 'S4'})"
    if action == "regenerate" or sev == "S3":
        return "drop", 0, 0, f"{sev} {','.join(q.get('anomalies') or [])}: excluded until regenerated (fix prompt: {q.get('fix_prompt') or 'see fix-prompts.md'}) - shorter and clean beats longer"
    windows = [w for w in (q.get("windows") or []) if w.get("t_in") is not None and w.get("t_out") is not None]
    if action == "trim" or sev == "S2" or (windows and any(str(w.get("verdict", "clean")).lower() != "clean" for w in windows)):
        clean = [w for w in windows if str(w.get("verdict", "clean")).lower() == "clean"]
        if not clean:
            return "drop", 0, 0, f"{sev}: no clean window recorded - dropped"
        best = max(clean, key=lambda w: float(w["t_out"]) - float(w["t_in"]))
        a, b = float(best["t_in"]), min(float(best["t_out"]), duration)
        h = handle_frames / fps
        if a > 1e-3:
            a += h
        if b < duration - 1e-3:
            b -= h
        if b - a < 1.5:
            return "drop", 0, 0, f"{sev}: longest clean window {b - a:.2f}s < 1.5 s - dropped"
        return "trim", round(a, 3), round(b, 3), f"{sev} {','.join(q.get('anomalies') or [])}: trimmed to clean window {a:.2f}-{b:.2f}s (+{handle_frames}-frame handles)"
    return "use", 0.0, duration, f"{sev}: whole clip"


def cadence(cuts: dict | None) -> dict:
    if not cuts:
        return {}
    ts = sorted(float(c.get("t", 0)) for c in (cuts.get("cuts") or []) if c.get("t") is not None)
    dur = float(cuts.get("duration_s") or 0)
    if not ts:
        return {"cuts": 0, "duration_s": dur}
    bounds = [0.0] + ts + ([dur] if dur > ts[-1] else [])
    shots = [b - a for a, b in zip(bounds, bounds[1:]) if b - a > 0.05]
    return {"cuts": len(ts), "duration_s": dur, "first_cut_s": ts[0],
            "median_shot_s": round(statistics.median(shots), 3) if shots else None}


def platform_from_answers(answers: dict | None) -> str | None:
    if not answers:
        return None
    items = answers if isinstance(answers, list) else answers.get("answers") or list(answers.values())
    for a in items:
        if not isinstance(a, dict):
            continue
        if str(a.get("key", "")).upper() == "Q6" or "platform" in str(a.get("question", "")).lower():
            txt = str(a.get("answer", "")).lower()
            if "reels" in txt:
                return "reels"
            if "shorts" in txt:
                return "shorts"
            if "tiktok" in txt:
                return "tiktok"
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="first edit-plan.json from clips + clip QA + trend brief")
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--clip-qa")
    ap.add_argument("--trend-brief")
    ap.add_argument("--manifest")
    ap.add_argument("--clips-dir")
    ap.add_argument("--out")
    ap.add_argument("--name")
    ap.add_argument("--platform", choices=sorted(ce.PLATFORM_SAFE_BOXES.keys()))
    ap.add_argument("--max-duration", type=float)
    ap.add_argument("--cta")
    ap.add_argument("--music")
    ap.add_argument("--music-gain-db", type=float, default=-18.0)
    ap.add_argument("--sfx-dir")
    ap.add_argument("--handle-frames", type=int, default=6)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    run_dir = os.path.abspath(args.run_dir)
    if not os.path.isdir(run_dir):
        print(f"run dir not found: {run_dir}", file=sys.stderr)
        return 1
    notes: list[str] = []
    fps = int(args.fps)
    manifest_src = os.path.abspath(args.manifest or os.path.join(run_dir, "80-generated", "manifest.json"))
    manifest = load_optional(manifest_src, notes, "manifest")
    qa = load_qa(args.clip_qa, run_dir, notes)
    brief = load_brief(args.trend_brief, run_dir, notes)
    cuts = load_optional(os.path.join(run_dir, "10-measure", "cuts.json"), notes, "cuts.json")
    answers = load_optional(os.path.join(run_dir, "30-decisions", "answers.json"), notes, "answers.json")
    plan40 = load_optional(os.path.join(run_dir, "40-plan", "plan.json"), notes, "40-plan/plan.json")
    clips_dir = args.clips_dir or os.path.join(run_dir, "80-generated")
    found = discover_clips(run_dir, manifest, clips_dir, notes)
    if not found:
        print("no generated clips found", file=sys.stderr)
        return 2
    platform = args.platform or platform_from_answers(answers) or "universal"
    cad = cadence(cuts)
    # ---- clips
    plan_clips, decisions = [], []
    order = 0
    for c in found:
        pn, path = c["prompt_no"], c["path"]
        if not os.path.isfile(path):
            decisions.append(f"clip {pn:02d}: MISSING ({path}) - excluded")
            continue
        pr = ce.probe_media(path)
        q = qa_for(qa, pn, path)
        decision, a, b, reason = decide_window(q, pr["duration"], fps, args.handle_frames)
        decisions.append(f"clip {pn:02d}: {decision} - {reason}")
        if decision == "drop":
            continue
        order += 1
        note = reason
        if cad.get("median_shot_s") and (b - a) > 2.0 * cad["median_shot_s"]:
            note += f"; runs {b - a:.1f}s > 2x original median shot {cad['median_shot_s']}s - consider a punch-in or a split (editor)"
        plan_clips.append({"id": f"c{pn:02d}", "path": path, "prompt_no": pn, "in": round(a, 3), "out": round(b, 3),
                           "order": order, "speed": 1.0, "speed_ramps": [],
                           "transform": {"fit": "cover", "scale": 1.0, "x": 0, "y": 0}, "volume": 1.0, "notes": note})
    if not plan_clips:
        print("every clip was dropped by the QA verdicts - nothing to plan (regenerate first)", file=sys.stderr)
        ce.save_json(args.out or os.path.join(run_dir, "90-postgen", "edit-plan.decisions.json"), {"decisions": decisions, "notes": notes})
        return 2
    # ---- transitions (default cut), effects, overlays from the brief
    transitions = [{"between": [x["id"], y["id"]], "type": "cut"} for x, y in zip(plan_clips, plan_clips[1:])]
    overlays = []
    audio = {"original_gain": 1.0, "music": {"path": None, "gain_db": -18, "start": 0.0, "ducking": {"enabled": True},
                                             "license": None, "trending_sound_id": None, "attach_in_app": False},
             "sfx": [], "loudness_target": {"i": -14, "tp": -1.0, "lra": 11}}
    colour = {"preset": "realism-v1", "grain": 7}
    first_len = float(plan_clips[0]["out"]) - float(plan_clips[0]["in"])
    hook_text, cta_text = None, args.cta
    max_dur = args.max_duration
    if brief:
        recs = brief.get("recommendations") or []
        for r in recs:
            field = str(r.get("edit_plan_field", "")).lower()
            if "caption" in field or "caption" in str(r.get("text", "")).lower():
                decisions.append(f"trend-brief recommendation #{r.get('rank')} targets captions - IGNORED (owner rule: no speech captions in the edit)")
        hooks = [h for h in (brief.get("hook_candidates") or []) if str(h).strip()]
        if hooks:
            hook_text = str(hooks[0]).strip()
        for r in recs:
            if str(r.get("edit_plan_field", "")).lower().startswith("text.hook") and not hook_text:
                m = re.search(r'"([^"]{3,60})"', str(r.get("text", "")))
                if m:
                    hook_text = m.group(1)
        for r in recs:
            if str(r.get("edit_plan_field", "")).lower().startswith("text.cta") and not cta_text:
                m = re.search(r'"([^"]{2,60})"', str(r.get("text", "")))
                if m:
                    cta_text = m.group(1)
        # sound
        sounds = [s for s in (brief.get("sounds") or []) if str(s.get("fit", "")).lower() in ("high", "med", "medium")]
        deliverable = str(brief.get("deliverable_type", "organic")).lower()
        if args.music and os.path.isfile(args.music):
            audio["music"].update({"path": os.path.abspath(args.music), "gain_db": args.music_gain_db, "license": "owned", "attach_in_app": False})
            decisions.append(f"music bed from --music ({os.path.basename(args.music)}), ducked under the clip audio")
        elif sounds:
            s = sounds[0]
            lic = str(s.get("license", "unknown"))
            if deliverable == "paid" and lic in ("organic-only", "unknown"):
                alt = brief.get("licensed_alternative") or {}
                audio["music"].update({"trending_sound_id": alt.get("id") or s.get("id"), "license": alt.get("license") or lic,
                                       "attach_in_app": True})
                decisions.append(f"paid deliverable: trending sound {s.get('id')} is {lic} - use licensed alternative {alt.get('id')} ({alt.get('license')}) attached at publish, or pass --music with an owned bed")
            else:
                audio["music"].update({"trending_sound_id": s.get("id"), "license": lic, "attach_in_app": True})
                decisions.append(f"sound {s.get('id')} ({s.get('title')}) attached IN-APP at posting (license {lic}); nothing baked in")
        # effects
        for e in brief.get("effects") or []:
            if not e.get("use"):
                continue
            name = str(e.get("name", "")).lower()
            where = str(e.get("where", "")).lower()
            if "punch" in name or "zoom" in name:
                plan_clips[0]["transform"]["punch_in"] = {"to": 1.08, "frames": 9}
                if "cta" in where or "end" in where:
                    plan_clips[-1]["transform"]["punch_in"] = {"to": 1.06, "frames": 10}
                decisions.append(f"{e.get('id')}: punch-in on the hook clip" + (" and the CTA clip" if plan_clips[-1]["transform"].get("punch_in") else ""))
            elif "whip" in name or "slide" in name or "swipe" in name:
                target = None
                m = re.search(r"clip\s*(\d{1,2})", where)
                if m:
                    target = f"c{int(m.group(1)):02d}"
                if not target or target not in [c["id"] for c in plan_clips]:
                    target = plan_clips[-1]["id"]
                for t in transitions:
                    if t["between"][1] == target:
                        t.update({"type": "whip", "duration": 0.2})
                        decisions.append(f"{e.get('id')}: whip transition into {target}")
            elif "crossfade" in name or "dissolve" in name or "fade" in name:
                for t in transitions[-1:]:
                    t.update({"type": "xfade", "duration": 0.4})
                    decisions.append(f"{e.get('id')}: crossfade into {t['between'][1]}")
            elif "speed" in name or "ramp" in name:
                decisions.append(f"{e.get('id')}: speed ramp recommended - editor to add speed_ramps on the montage clip (not automated)")
        dn = " ".join(str(x).lower() for x in (brief.get("do_not") or []))
        if "grain" in dn or "clean" in str(brief.get("niche", "")).lower():
            colour = {"preset": "clean", "grain": 0}
            decisions.append("colour: clean preset (brief do-not list / clean niche)")
        sweet = ((brief.get("posting") or {}).get("duration_sweet_spot_s") or [None, None])
        if max_dur is None and isinstance(sweet, list) and len(sweet) == 2 and sweet[1]:
            max_dur = float(sweet[1])
    if hook_text:
        overlays.append({"id": "hook", "type": "hook_text", "text": hook_text, "t_start": 0.0,
                         "t_end": round(min(2.0, first_len), 3), "position": {"anchor": "top"}, "style": "hook-v1"})
        decisions.append(f'hook text "{hook_text}" 0-{min(2.0, first_len):.1f}s (leaves at the first cut or 2.0 s)')
    # ---- SFX for whips
    if args.sfx_dir and os.path.isdir(args.sfx_dir):
        whoosh = sorted(glob.glob(os.path.join(args.sfx_dir, "*whoosh*.wav")) + glob.glob(os.path.join(args.sfx_dir, "*whoosh*.mp3")))
        if whoosh:
            probes = {c["path"]: ce.probe_media(c["path"]) for c in plan_clips}
            tmp = {"clips": plan_clips, "transitions": transitions}
            placed, _ = ce.compute_timeline(tmp, probes)
            for p in placed:
                t = p["transition_in"]
                if t and t.get("type") == "whip" and p["start"] >= 0.5:
                    audio["sfx"].append({"path": os.path.abspath(whoosh[0]), "at": round(p["start"], 3), "gain_db": -14, "label": f"whoosh into {p['clip']['id']}"})
    # ---- totals
    probes = {c["path"]: ce.probe_media(c["path"]) for c in plan_clips}
    placed, total = ce.compute_timeline({"clips": plan_clips, "transitions": transitions}, probes)
    if cta_text:
        t1 = round(total, 3)
        t0 = round(max(0.0, total - 2.0), 3)
        overlays.append({"id": "endcard", "type": "end_card", "text": cta_text, "t_start": t0, "t_end": t1,
                         "position": {"anchor": "middle"}, "style": "endcard-v1"})
        decisions.append(f'end card "{cta_text}" over the last 2 s')
    if max_dur and total > max_dur + 0.05:
        decisions.append(f"total {total:.1f}s exceeds the target ceiling {max_dur:.0f}s - editor: tighten trims or drop the weakest clip (never keep flagged material to fill time)")
    planned_secs = None
    if plan40 and isinstance(plan40.get("clips"), list):
        try:
            planned_secs = sum(float(c.get("duration") or c.get("duration_s") or 0) for c in plan40["clips"])
        except Exception:
            planned_secs = None
    name = args.name or os.path.basename(run_dir)
    plan = {
        "schema": ce.PLAN_SCHEMA,
        "project": {"name": name, "run_dir": run_dir.replace("\\", "/"), "fps": fps, "width": 1080, "height": 1920,
                    "platform": platform, "safe_zones": dict(ce.PLATFORM_SAFE_BOXES.get(platform, ce.UNIVERSAL_SAFE_BOX))},
        "clips": plan_clips,
        "transitions": transitions,
        "text_overlays": overlays,
        "audio": audio,
        "colour": colour,
        "export": {"codec": "libx264", "profile": "high", "level": "4.1", "preset": "medium", "crf": 18,
                   "audio_bitrate": "192k", "faststart": True, "name": f"final-A-{platform if platform != 'universal' else 'all'}.mp4"},
        # provenance = the files actually loaded (V2 fix 2026-09-17: defaults used to be recorded as null)
        "meta": {"run_id": os.path.basename(run_dir), "source": "plan_from_clips",
                 "clip_qa": (qa or {}).get("_loaded_from") if isinstance(qa, dict) else None,
                 "trend_brief": (brief or {}).get("_loaded_from") if isinstance(brief, dict) else None,
                 "manifest": manifest_src if manifest else None,
                 "platform_source": "arg" if args.platform else ("answers" if platform_from_answers(answers) else "default"),
                 "source_reference": cad, "planned_total_s": planned_secs, "max_duration_s": max_dur,
                 "planned_render_s": total, "decisions": decisions, "notes": notes,
                 "no_captions": "speech captions are never planned here (owner rule); the owner captions afterwards",
                 "projects": {"capcut_draft": None, "otio": None, "descript": None},
                 "updated": ce.now_iso(), "history": [f"{ce.now_iso()} plan_from_clips"]},
    }
    out = os.path.abspath(args.out or os.path.join(run_dir, "90-postgen", "edit-plan.json"))
    ce.save_json(out, plan)
    try:
        ce.load_plan(out)  # round-trip validation (refuses caption-shaped content)
    except ce.PlanError as e:
        print(f"generated plan failed validation: {e}", file=sys.stderr)
        return 1
    ce.history_line(os.path.dirname(out), f"plan_from_clips: {len(plan_clips)} clips kept, {total:.2f}s, {len(overlays)} overlays")
    summary = {"out": out, "clips_kept": [c["id"] for c in plan_clips], "planned_render_s": total, "max_duration_s": max_dur,
               "overlays": [o["id"] for o in overlays], "transitions": [t for t in transitions if t["type"] != "cut"],
               "music": audio["music"], "decisions": decisions, "notes": notes}
    print(json.dumps(summary, ensure_ascii=False, indent=2 if args.json else None))
    return 0


if __name__ == "__main__":
    sys.exit(main())
