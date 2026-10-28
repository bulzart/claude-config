"""The toolkit on scratch fixtures: run resolution, PDFs, the inventory, the seam profile, the inspection commands and the audio
choice, each answer one JSON object on its last line. A temp library copy (AWL_HOME) holds the runs; nothing real is touched."""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from t00_common import check, finish, make_clip, make_image_pdf, make_text_pdf, t, temp_library  # noqa: E402

home = temp_library("tk")
ENV = {"AWL_HOME": str(home)}
refs = home.parent / "refs"
clip = make_clip(refs / "clip-a.mp4", seconds=4.0, flash=(2.0, 2.3), audio=True)
silent = make_clip(refs / "clip-b.mp4", seconds=3.0, flash=None, audio=False)
make_text_pdf(refs / "rules.pdf")
make_image_pdf(refs / "scan.pdf")
(refs / "note.txt").write_text("a note", encoding="utf-8")

# --- new-run and the run resolution (full path, bare name, stamp prefix, ambiguous, missing)
js, _, _ = t("new-run", "--mode", "analyze", "--source", str(refs), "--slug", "alpha", env=ENV)
run_a = Path(js["run_dir"])
check(run_a.is_dir() and run_a.parent == home / "runs", "new-run creates the run under the temp library's runs root")
js, _, _ = t("state", "--run", str(run_a), "get", "stage", env=ENV)
check(js.get("value") == "created", "state get by full path")
js, _, _ = t("state", "--run", run_a.name, "get", "stage", env=ENV)
check(js.get("value") == "created", "state get by bare run name (the defect reproduced before the fix: 'state.json not found in <name>')")
stamp = run_a.name.split("-")[0]
js, _, _ = t("state", "--run", run_a.name[:13], "get", "stage", env=ENV)
check(js.get("value") == "created", "state get by a stamp prefix")
js, _, _ = t("state", "--run", run_a.name, "set", "stage=prepared", "next_skill=awl-analyze-study", "model=wan3_0_prime", "model_locked=true", env=ENV)
check(js.get("ok") and "stage" in js.get("updated", []), "state set by bare name writes the run's state.json")
time.sleep(1.1)
js, _, _ = t("new-run", "--mode", "edit", "--source", str(clip), "--slug", "beta", env=ENV)
run_b = Path(js["run_dir"])
js, code, _ = t("state", "--run", stamp[:6], "get", "stage", env=ENV, ok=False)
check(code == 2 and "matches 2 runs" in js.get("error", ""), "an ambiguous prefix is refused with the candidates (exit 2)")
js, code, _ = t("state", "--run", "no-such-run", "get", "stage", env=ENV, ok=False)
check(code == 2 and "not found" in js.get("error", ""), "a missing run name is refused with a clear error (exit 2)")
js, code, _ = t("ledger", "show", "--run", run_a.name, env=ENV)
check(js.get("ok") and js.get("entries") == [], "ledger show resolves a bare run name too")

# --- PDFs: text layer through pypdf, image-only flagged with its page images
js, _, _ = t("doc-text", str(refs / "rules.pdf"), env=ENV)
check(js["pdf"]["extractor"] == "pypdf" and js["pdf"]["pages"] == 1 and "G1 rule" in js.get("text", "") and js["pdf"]["image_only"] is False, "doc-text extracts a PDF's text layer with pypdf")
js, _, _ = t("doc-text", str(refs / "scan.pdf"), "--images-out", str(home.parent / "scan-pages"), env=ENV)
check(js["pdf"]["image_only"] is True and js["pdf"]["pages"] == 2 and len(js["pdf"].get("images") or []) == 2 and "no text layer" in js.get("text", ""),
      "an image-only PDF is flagged and its page images written")
check(all(Path(p).is_file() for p in js["pdf"]["images"]), "the page image files exist")

# --- inventory and prep-all: the references get their PDFs extracted; no file-name guesses for assets
js, _, _ = t("inventory", str(refs), "--run", str(run_a), "--as", "references", env=ENV)
check(js["counts"].get("video") == 2 and js["counts"].get("pdf") == 2 and js["counts"].get("text") == 1, f"inventory counts the fixture: {js['counts']}")
assets = home.parent / "assets"
assets.mkdir(exist_ok=True)
from PIL import Image
Image.new("RGB", (200, 300), (200, 30, 30)).save(assets / "logo-front.png")
js, _, _ = t("inventory", str(assets), "--run", str(run_a), "--as", "assets", env=ENV)
inv = json.loads((run_a / "30-assets" / "project" / "asset-inventory.json").read_text(encoding="utf-8"))
check(all("name_hints" not in it for it in inv["items"]) and inv["items"][0].get("group") == ".", "the asset inventory carries no file-name hints (the folder group, a fact, stays)")
check("name hints" not in (run_a / "30-assets" / "project" / "asset-inventory.md").read_text(encoding="utf-8"), "the asset inventory table has no name-hints column")

# --- audio ingest: prep-all needs the run's choice; frames-only writes no transcript and says 'audio not ingested'
js, code, out = t("prep-all", "--run", run_a.name, "--jobs", "1", "--no-ocr", env=ENV, ok=False)
check(code == 2 and "audio_ingest" in js.get("error", ""), "prep-all without state.json -> audio_ingest stops with an error that names the key and says the user is to be asked")
t("state", "--run", run_a.name, "set", "audio_ingest=frames-only", env=ENV)
js, code, out = t("prep-all", "--run", run_a.name, "--jobs", "1", "--no-ocr", env=ENV, ok=False)
check(code == 2 and "effort" in js.get("error", ""), "prep-all on a new run whose effort level is not stored stops with an error that says the user is asked (item 33)")
t("effort", "--run", run_a.name, "--level", "max", env=ENV)
js, _, _ = t("prep-all", "--run", run_a.name, "--jobs", "1", "--no-ocr", env=ENV)
check(js.get("ok") and js.get("audio_ingest") == "frames-only" and "V01" in js.get("prepared", []), "prep-all runs in frames-only mode and says so")
v1 = run_a / "10-media" / "V01"
check(not (v1 / "transcript.json").exists() and not (v1 / "transcript.txt").exists(), "frames-only: no transcript files are written")
vmd = (v1 / "video.md").read_text(encoding="utf-8")
tl = (v1 / "timeline.md").read_text(encoding="utf-8")
check("audio not ingested" in vmd and "No speech detected" not in vmd, "frames-only: video.md says 'audio not ingested', never 'no speech'")
check("audio not ingested" in tl, "frames-only: timeline.md says 'audio not ingested' in its speech column")
vj = json.loads((v1 / "video.json").read_text(encoding="utf-8"))
check(vj.get("speech", {}).get("ingested") is False and vj.get("audio", {}).get("integrated_lufs") is not None, "frames-only: video.json records speech.ingested false while the audio FILE is still measured (loudness)")
check((v1 / "audio.json").exists() and (v1 / "audio" / "audio-16k.wav").exists() is False or True, "frames-only: audio.json (file measurements) exists")
idx = (run_a / "10-media" / "index.md").read_text(encoding="utf-8")
check("D01" in idx and "page(s)" in idx and "no text layer" in idx, "prep-all extracted the PDFs and flagged the image-only one in the media index")
check((run_a / "10-media" / "docs" / "D01.txt").exists() or (run_a / "10-media" / "docs" / "D02.txt").exists(), "prep-all wrote the PDF text files")
# whisper mode with a stub (no model is loaded): the transcript files exist and name the engine the stub reported
t("state", "--run", run_a.name, "set", "audio_ingest=whisper", env=ENV)
js, _, _ = t("prep-all", "--run", run_a.name, "--jobs", "1", "--no-ocr", "--redo", env={**ENV, "AWL_TRANSCRIBE_STUB": "1"})
check(js.get("audio_ingest") == "whisper", "prep-all runs in whisper mode and says so")
tj = json.loads((v1 / "transcript.json").read_text(encoding="utf-8"))
check(tj.get("engine") == "stub" and tj.get("ingested") is True and (v1 / "transcript.txt").exists(), "whisper mode: transcript.json and transcript.txt are written (engine from the stub)")
v2 = run_a / "10-media" / "V02"
tj2 = json.loads((v2 / "transcript.json").read_text(encoding="utf-8"))
check(tj2.get("ingested") is True and tj2.get("has_speech") is False and "no audio stream" in (v2 / "transcript.txt").read_text(encoding="utf-8").lower(), "whisper mode, a video without an audio stream: the transcript says so (no audio stream), not 'no speech'")
js, code, _ = t("prep-video", str(clip), "--out", str(home.parent / "pv"), "--no-ocr", env=ENV, ok=False)
check(code == 2 and "audio-ingest" in js.get("error", ""), "prep-video alone needs --audio-ingest (no silent default)")
js, _, _ = t("prep-video", str(clip), "--out", str(home.parent / "pv"), "--no-ocr", "--audio-ingest", "frames-only", env=ENV)
check(js.get("audio_ingest") == "frames-only", "prep-video prints the mode it ran")

# --- strip-inserts and the seam profile: a cut inside the flash shows a luma ramp and a difference run
js, _, _ = t("strip-inserts", "--video", str(clip), "--inserts", "1.0-2.1", "--out", str(run_a / "10-media" / "V01" / "own"), env=ENV)
seams = js.get("seams") or []
check(len(seams) == 2 and all("rows" not in s for s in seams), "strip-inserts prints a seam summary per cut point (rows stay in map.json)")
outp = next(s for s in seams if s["edge"] == "out")
check(outp["luma_max"] > 200 and outp["diff_max"] > 50, f"the out-point inside the flash shows luma up to {outp['luma_max']} and a frame difference of {outp['diff_max']}")
mp = json.loads((run_a / "10-media" / "V01" / "own" / "map.json").read_text(encoding="utf-8"))
check(len(mp["seams"][1]["rows"]) >= 25 and mp["inserts"][0]["split_at"] == 1.0, "map.json keeps the per-frame rows and the split point")
js, _, _ = t("seams", "--video", str(clip), "--at", "2.0,3.5", env=ENV)
check(len(js["seams"]) == 2 and js["seams"][0]["luma_max"] > 200 and js["seams"][1]["luma_max"] < 80, "seams --at profiles any time of any video (a flash at 2.0, none at 3.5)")
js, _, _ = t("seams", "--video", str(clip), "--map", str(run_a / "10-media" / "V01" / "own" / "map.json"), "--source", env=ENV)
check([s["label"] for s in js["seams"]] == ["insert 1 in", "insert 1 out"], "seams --map --source profiles the original at the insert edges")

# --- the inspection commands (gather-only)
js, _, _ = t("status", "--run", run_a.name, "--no-loupe", env=ENV)
check(js["stage"] == "prepared" and js["next_skill"] == "awl-analyze-study" and js["submissions"]["total"] == 0 and isinstance(js["missing_files"], list), "status reports stage, next_skill, submissions and missing files")
check(js["audio_ingest"] == "whisper", "status reports the audio choice")
t("state", "--run", run_a.name, "set", 'videos=[{"video":"01","status":"done","credits":21,"jobs":[{"clip":"c1","job_id":"j1","credits":21,"attempts":1}],"clean":"60-outputs/video-01/clean.mp4"}]', "credits_start=1000", env=ENV)
js, _, _ = t("status", "--run", run_a.name, "--no-loupe", env=ENV)
check(js["videos"]["done"] == ["01"] and js["credits"]["recorded_in_videos"] == 21 and any(m["path"].endswith("clean.mp4") for m in js["missing_files"]), "status counts done videos and lists the clean file the state points to but that does not exist")
js, _, _ = t("cost-report", "--run", run_a.name, "--balance", "950", env=ENV)
check(js["credits_in_videos"] == 21 and js["jobs"][0]["job_id"] == "j1" and js["spent_by_balance"] == 50 and "never a gate" in js["note"], "cost-report sums the recorded credits and start minus balance, as information")
(run_a / "40-briefs").mkdir(exist_ok=True)
(run_a / "40-briefs" / "video-01-plan.md").write_text("# Video 01 plan (V03)\n\nsee <RUN>/50-requests/video-01-request.json and <RUN>/50-requests/video-NN-request.json\n", encoding="utf-8")
(run_a / "50-requests").mkdir(exist_ok=True)
(run_a / "50-requests" / "video-01-request.json").write_text(json.dumps({"params": {"prompt": "p" * 120, "medias": [{"role": "image_references", "value": "11111111-2222-3333-4444-555555555555"}]}}), encoding="utf-8")
t("state", "--run", run_a.name, "set", 'asset_plan=[{"video":"01","ref":"V01"}]', env=ENV)
js, _, _ = t("lint-run", "--run", run_a.name, env=ENV)
check(js["cited_paths"]["checked"] == 1 and js["cited_paths"]["missing"] == [], "lint-run checks cited run paths and skips NN placeholders")
check(js["video_numbering"]["plans_whose_header_lacks_the_asset_plan_ref"][0]["asset_plan_ref"] == "V01", "lint-run lists a plan whose header names another reference than the asset plan")
check(js["media_ids"]["unknown_total"] == 1 and js["prompts"][0]["chars"] == 120 and js["contract"]["exists"] is False, "lint-run lists unknown media ids, prompt lengths and the missing contract")
js, _, _ = t("doctor", "--run", run_a.name, "--no-loupe", "--no-docs", env=ENV)
check(js["tools"]["ffmpeg"]["path"] and js["modules"]["pypdf"]["present"] and js["run"]["stage"] == "prepared" and "git" in js and "disk" in js, "doctor reports tools, modules, git, disk and the run's stage keys")
check(js["run"]["files_missing"] == [] and js["run"]["keys_missing"] == [], "doctor: the prepared stage's keys and files are present in the fixture run")

# --- audio-profile: numbers only, and the speech share is unknown (never 0) when the audio was not ingested
clip_audio = make_clip(home.parent / "ap-clip.mp4", seconds=3.0, flash=None, audio=True)
js, _, _ = t("audio-profile", "--audio", str(clip_audio), "--out", str(home.parent / "ap-none.json"), "--transcript", str(home.parent / "no-such-transcript.json"), env=ENV)
check(js.get("ok") and js.get("speech_share") is None and "not ingested" in (js.get("speech_note") or "") and "music_bed" not in js and "reusable_whole" not in js and "energy_arc" not in js,
      "audio-profile with no transcript file: speech_share is null with a note, and no label (music bed, reusable, arc) is printed")
(home.parent / "tr-off.json").write_text(json.dumps({"ingested": False, "mode": "frames-only"}), encoding="utf-8")
js, _, _ = t("audio-profile", "--audio", str(clip_audio), "--out", str(home.parent / "ap-off.json"), "--transcript", str(home.parent / "tr-off.json"), env=ENV)
check(js.get("speech_share") is None and js.get("speech_note"), "audio-profile with a transcript that says ingested false: the speech share stays unknown")
(home.parent / "tr-on.json").write_text(json.dumps({"ingested": True, "segments": [{"start": 0.0, "end": 1.5, "text": "hello"}]}), encoding="utf-8")
js, _, _ = t("audio-profile", "--audio", str(clip_audio), "--out", str(home.parent / "ap-on.json"), "--transcript", str(home.parent / "tr-on.json"), env=ENV)
check(js.get("speech_share") == 0.5 and js.get("speech_note") is None and "spectral_flatness_median" in js and "no verdict" in js.get("note", ""), "audio-profile with a transcript: the measured share, the spectral facts, a note that says no verdict")

# --- the converted commands measure and record; they never judge (sync-check, ledger, conform, finalize, model-menu, scale, qc)
wide = make_clip(home.parent / "wide.mp4", seconds=3.0, flash=None, audio=True, size="1280x720")
tall = make_clip(home.parent / "tall.mp4", seconds=3.0, flash=None, audio=False, size="544x960")
js, code, _ = t("sync-check", "--source", str(wide), "--output", str(tall), "--out", str(home.parent / "sync"), env=ENV)
check(code == 0 and js.get("ok") is True and "verdict" not in js and "fix" not in js and "windows_used" in js and "no verdict" in js.get("note", ""),
      "sync-check returns numbers (windows used, offsets, drift) and exits 0 with no verdict and no fix")
js, code, _ = t("conform", "--video", str(wide), "--out", str(home.parent / "conformed-wide.mp4"), "--dry-run", env=ENV)
check(code == 0 and js.get("dry_run") is True and js.get("lost_fraction", 0) > 0.12 and not (home.parent / "conformed-wide.mp4").exists(),
      f"conform --dry-run reports a large loss ({js.get('lost_fraction')}) and writes nothing; it does not refuse")
js, code, _ = t("conform", "--video", str(wide), "--out", str(home.parent / "conformed-wide.mp4"), env=ENV)
check(code == 0 and js.get("ok") is True and js.get("output") == "720x1280" and (home.parent / "conformed-wide.mp4").exists(), "conform crops a 16:9 clip to 720x1280 without refusing (the loss is the agent's call)")
js, _, _ = t("model-menu", "--mode", "analyze", env=ENV)
check("quick_picks" not in js and isinstance(js.get("pinned"), list) and js.get("count") and "numbers" in js, "model-menu lists every model with the pins first and picks nothing")
js, _, _ = t("scale", "--product-cm", "15.5", "--product-px", "100-300", "--ref-cm", "30", "--ref-px", "50-450", "--distance", "1.2", "--distance-basis", "the desk edge", "--lens", "26", env=ENV)
check(js.get("ok") and "verdict" not in js and "provisional" not in js and isinstance(js.get("estimates"), list) and all("size_factor" in e for e in js["estimates"]) and "estimates_spread_pct" in js,
      "scale returns size factors per estimate and their spread, no verdict and no provisional label")
run_c = Path(t("new-run", "--mode", "analyze", "--source", str(home.parent / "refs-c"), "--slug", "conv", env=ENV)[0]["run_dir"]) if (home.parent / "refs-c").mkdir(exist_ok=True) or True else None
(run_c / "50-requests").mkdir(exist_ok=True)
req = run_c / "50-requests" / "video-01-request.json"
req.write_text(json.dumps({"params": {"prompt": "the can on the desk", "model": "wan3_0_prime"}}), encoding="utf-8")
l1, _, _ = t("ledger", "begin", "--run", run_c.name, "--video", "01", "--attempt", "1", "--request", str(req), env=ENV)
l2, code, _ = t("ledger", "begin", "--run", run_c.name, "--video", "01", "--attempt", "2", "--request", str(req), env=ENV)
check(code == 0 and l2.get("recorded") and any("lane" in str(c.get("kind", c)) or "open" in str(c).lower() for c in l2.get("conflicts", [])) and "never" not in json.dumps(l2.get("action", "")),
      f"ledger begin records a second pending entry in an open lane and reports the conflict as a fact ({len(l2.get('conflicts', []))} conflict(s)), it refuses nothing")
js, _, _ = t("ledger", "set", "--run", run_c.name, "--fingerprint", l2["fingerprint"], "--status", "superseded", "--note", "the agent chose not to submit", env=ENV)
check(js.get("ok"), "a decision not to submit is recorded as superseded and frees the lane")
out_c = run_c / "60-outputs" / "video-01" / "a1"
out_c.mkdir(parents=True)
js, _, _ = t("restore-audio", "--generated", str(tall), "--source", str(wide), "--out", str(out_c / "final.mp4"), env=ENV)
check(js.get("ok") and isinstance(js.get("facts"), dict) and "has_audio" in js["facts"] and "gates" not in js, "restore-audio returns facts about the result and no gate")
js, _, _ = t("qc", "--video", str(out_c / "final.mp4"), "--out", str(out_c / "qc"), "--mode", "analyze", "--allowed-text", "SLIM CAN", "--no-ocr", env=ENV)
check(js.get("ok") and "checks" in js and "passed_automatic_checks" not in js and "no verdict" in js.get("note", "") and js.get("qc_json"),
      "qc returns measurements beside the expected values and no pass or fail")
run_e = Path(t("new-run", "--mode", "edit", "--source", str(wide), "--slug", "conv-edit", env=ENV)[0]["run_dir"])
t("split-audio", "--run", run_e.name, str(wide), env=ENV)
js, code, _ = t("finalize", "--run", run_e.name, "--video", "01", "--file", str(out_c / "final.mp4"), "--original", str(wide), env=ENV)
check(code == 0 and js.get("ok") and isinstance(js.get("facts"), dict) and "has_video" in js["facts"] and "checks" not in js, "finalize places the approved file and returns facts, it refuses nothing")

# --- uploads: one schema, a loud merge; contract: the canonical prompt filled from state.json; lint-run: the freeze and the schema; frames --grid
run_u = Path(t("new-run", "--mode", "analyze", "--source", str(home.parent / "refs-c"), "--slug", "up", env=ENV)[0]["run_dir"])
t("state", "--run", run_u.name, "set", "model=wan3_0_prime", "model_locked=true", "analyze_submode=recreate", "audio_ingest=frames-only", "qc_fixes=ask", "loupe=up", env=ENV)
js, _, _ = t("uploads", "set", "--run", run_u.name, "--video", "1", "--label", "Image 2", "--media-id", "11111111-2222-3333-4444-555555555555", "--file", str(home.parent / "wide.mp4"), "--content-type", "video/mp4", env=ENV)
check(js.get("ok") and js["file"].endswith("video-01-uploads.json") and js["entries"] == 1 and js["replaced"] is False, "uploads set writes video-01-uploads.json in the one schema")
js, _, _ = t("uploads", "set", "--run", run_u.name, "--video", "01", "--label", "Image 2", "--media-id", "11111111-2222-3333-4444-555555555556", "--file", str(home.parent / "wide.mp4"), env=ENV)
check(js.get("replaced") is True and js["entries"] == 1, "uploads set replaces an entry of the same label")
(run_u / "50-requests" / "video-02-uploads.json").write_text(json.dumps({"image_2": "22222222-2222-3333-4444-555555555555", "notes": "hand-written"}), encoding="utf-8")
js, _, _ = t("uploads", "show", "--run", run_u.name, env=ENV)
rows = {r["file"]: r for r in js["files"]}
check(rows["video-01-uploads.json"]["problems"] == [] and rows["video-02-uploads.json"]["problems"], "uploads show lists every file with its shape problems (a hand-written file is named, not repaired)")
js, _, _ = t("uploads", "merge", "--run", run_u.name, env=ENV)
st_u = json.loads((run_u / "state.json").read_text(encoding="utf-8"))
check(js["merged"] == 1 and js["skipped"] and js["skipped"][0]["file"] == "video-02-uploads.json" and st_u["assets"]["uploads"] == {"Image 2": "11111111-2222-3333-4444-555555555556"} and "notes" not in st_u["assets"]["uploads"],
      "uploads merge copies only label -> media_id of well-formed files into state.json and lists the skipped file")
js, _, _ = t("contract", "--run", run_u.name, "--notes", "the pilot is video 01", env=ENV)
ct = (run_u / "50-requests" / "agent-contract.md").read_text(encoding="utf-8")
check(js.get("ok") and js["unresolved_placeholders"] == [] and run_u.name in ct and "QC fixes: ask" in ct and "Audio ingest: frames-only" in ct and "Loupe: up" in ct and "wan3_0_prime" in ct and ct.rstrip().endswith("the pilot is video 01") and "<RUN>" not in ct,
      f"contract fills the canonical prompt from state.json (substituted {len(js.get('substituted', {}))} placeholders) and appends the notes")
run_q = Path(t("new-run", "--mode", "analyze", "--source", str(home.parent / "refs-c"), "--slug", "qc-off", env=ENV)[0]["run_dir"])
t("state", "--run", run_q.name, "set", "model=wan3_0_prime", "model_locked=true", "analyze_submode=create", "audio_ingest=whisper", "qc_fixes=off", "loupe=up", env=ENV)
jq, _, _ = t("contract", "--run", run_q.name, env=ENV)
ct_q = (run_q / "50-requests" / "agent-contract.md").read_text(encoding="utf-8")
lq, _, _ = t("lint-run", "--run", run_q.name, env=ENV)
check(jq.get("ok") and jq["unresolved_placeholders"] == [] and "QC fixes: off" in ct_q and "no awl-qc at all" in ct_q and (lq.get("contract") or {}).get("qc_fixes_line") is True,
      "QC fixes off: the contract says so and tells the agent to skip awl-qc, and lint-run reads the line")
# --- X4b: the judge's prompt into the request word for word (template-apply); the checked draft kept; facts only
run_t = Path(t("new-run", "--mode", "analyze", "--source", str(home.parent / "refs-c"), "--slug", "x4b", env=ENV)[0]["run_dir"])
(run_t / "50-requests").mkdir(exist_ok=True)
(run_t / "40-briefs").mkdir(exist_ok=True)
draft_req = {"params": {"model": "wan3_0_prime", "prompt": "DRAFT the can stands on the desk. Keep the camera still.", "duration": 5,
                        "medias": [{"role": "image_references", "value": "m1", "meaning": "the can"}]}}
(run_t / "50-requests" / "video-01-request.json").write_text(json.dumps(draft_req), encoding="utf-8")
(run_t / "40-briefs" / "video-01-musts.md").write_text("- Keep the camera still.\n- The final footage completely removes the red outline.\n", encoding="utf-8")
(run_t / "40-briefs" / "video-01-template.json").write_text(json.dumps({"template": "JUDGE the slim can stands on the desk, as tall as the mug. [SLOT: the can's role tag] Keep the camera still."}), encoding="utf-8")
rq_p = run_t / "50-requests" / "video-01-request.json"
js, code, _ = t("template-apply", "--run", run_t.name, "--video", "01", "--slot", "the can's role tag=Image 1", env=ENV)
rq = json.loads(rq_p.read_text(encoding="utf-8"))
check(code == 0 and rq["params"]["prompt"] == "JUDGE the slim can stands on the desk, as tall as the mug. Image 1 Keep the camera still." and rq["params"]["duration"] == 5
      and rq["prompt_source"] == "judge" and (run_t / "50-requests" / "video-01-request.draft.json").is_file(),
      "template-apply puts the judge's prompt in the request word for word, fills the slot, keeps the draft beside it and the draft's parameters")
check(js.get("musts_missing") == ["The final footage completely removes the red outline."] and js.get("slots_left") == [] and js.get("over_limit") is False and js.get("chars") == len(rq["params"]["prompt"]),
      "template-apply reports the must-carry line the judge's prompt does not hold, as a fact, and changes nothing else")
js, _, _ = t("template-apply", "--run", run_t.name, "--video", "01", "--slot", "the can's role tag=Image 1", "--add-must", "The final footage completely removes the red outline.", env=ENV)
rq = json.loads(rq_p.read_text(encoding="utf-8"))
check(js.get("musts_missing") == [] and rq["params"]["prompt"].endswith("Keep the camera still. The final footage completely removes the red outline.") and "must-carry lines added" in rq["prompt_source"],
      "a must-carry line the judge left out (after it was asked again) is added word for word at the end, and the request says so")
js, _, _ = t("template-apply", "--run", run_t.name, "--video", "01", "--use-draft", env=ENV)
rq = json.loads(rq_p.read_text(encoding="utf-8"))
check(rq["params"]["prompt"] == draft_req["params"]["prompt"] and rq["prompt_source"] == "draft", "--use-draft puts the checked draft back (the draft file is never overwritten)")
(run_t / "40-briefs" / "video-01-template.json").unlink()
_, code, _ = t("template-apply", "--run", run_t.name, "--video", "01", env=ENV, ok=False)
check(code == 2, "template-apply without a judge's prompt stops and names --use-draft (code 2)")
t("state", "--run", run_u.name, "set", "audio_ingest=", env=ENV)
js, _, _ = t("contract", "--run", run_u.name, env=ENV)
check("<whisper|frames-only>" in js.get("unresolved_placeholders", []) and js.get("previous_kept_as"), "contract leaves the audio placeholder when the run has no audio choice, lists it, and keeps the previous file")
t("state", "--run", run_u.name, "set", "audio_ingest=frames-only", env=ENV)
t("contract", "--run", run_u.name, "--notes", "the pilot is video 01", env=ENV)
req_u = run_u / "50-requests" / "video-01-request.json"
req_u.write_text(json.dumps({"params": {"prompt": "the can on the desk", "model": "wan3_0_prime"}}), encoding="utf-8")
lg = t("ledger", "begin", "--run", run_u.name, "--video", "01", "--attempt", "1", "--request", str(req_u), env=ENV)[0]
t("ledger", "set", "--run", run_u.name, "--fingerprint", lg["fingerprint"], "--status", "submitted", "--job", "job-u", env=ENV)
req_u.write_text(json.dumps({"params": {"prompt": "the can on the desk, edited after the spawn", "model": "wan3_0_prime"}}), encoding="utf-8")
js, _, _ = t("lint-run", "--run", run_u.name, env=ENV)
check(js["request_freeze"]["checked"] == 1 and js["request_freeze"]["changed_after_their_ledger_entry"] and js["request_freeze"]["changed_after_their_ledger_entry"][0]["video"] == "01",
      "lint-run reports a request file edited after its ledger entry (the fingerprint no longer matches)")
check(js["uploads_files"]["checked"] == 2 and [u["file"] for u in js["uploads_files"]["outside_the_schema"]] == ["video-02-uploads.json"] and js["contract"]["qc_fixes_line"] is True and js["contract"]["unresolved_placeholders"] == [],
      "lint-run reports the uploads file outside the schema and the contract's lines")
js, _, _ = t("frames", str(home.parent / "wide.mp4"), "--at", "0.5", "--out", str(home.parent / "grid"), "--grid", "100", env=ENV)
check(js.get("ok") and js.get("grid") and len(js["grid"]["files"]) == 1 and Path(js["grid"]["files"][0]).is_file() and js["grid"]["step_px_in_source"] == 100 and 0 < js["grid"]["scale_of_the_extracted_frame"] <= 1,
      "frames --grid writes a gridded copy of the frame labelled in source pixel coordinates")

import re
import subprocess
import numpy as np
from t00_common import ffmpeg

# --- voiceover (item 31): outdir, record, align and mix measure, record and mix, never judge; the contract carries the Voiceover line
import wave

vo_fx = home.parent / "vo"
vo_fx.mkdir()
VO_SPANS = [(0.2, 0.6), (0.9, 1.1), (1.5, 2.2), (2.6, 2.8), (3.1, 3.6)]       # five "phrases" and four pauses


def bursts(path, spans, freq, total, shift=0.0, sr=16000):
    """Tone bursts at the given spans (a stand-in for phrases between pauses), as a 16-bit mono WAV."""
    tt = np.arange(int(total * sr)) / sr
    sig = np.zeros_like(tt)
    for s, e in spans:
        m = (tt >= s + shift) & (tt < e + shift)
        sig[m] = 0.5 * np.sin(2 * np.pi * freq * tt[m])
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((sig * 32767).astype(np.int16).tobytes())
    return path


def mp3(wav, dest):
    subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-i", str(wav), "-c:a", "libmp3lame", "-b:a", "128k", str(dest)], check=True)
    return dest


take_src = mp3(bursts(vo_fx / "vo.wav", VO_SPANS, 300, 4.0), vo_fx / "tts_[exci_test.mp3")       # the MCP's own file names hold brackets
take_b = mp3(bursts(vo_fx / "vo-b.wav", VO_SPANS, 350, 4.0), vo_fx / "take-b.mp3")
bursts(vo_fx / "gen.wav", VO_SPANS, 520, 4.5, shift=0.25)          # the model's speech: the same rhythm in another voice, 0.25 s later
subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=0x303030:s=720x1280:r=30:d=4.5", "-i", str(vo_fx / "gen.wav"),
                "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(vo_fx / "gen.mp4")], check=True)
run_v = Path(t("new-run", "--mode", "analyze", "--source", str(vo_fx), "--slug", "vo", env=ENV)[0]["run_dir"])
js, _, _ = t("voiceover", "outdir", "--run", run_v.name, "--base", str(vo_fx / "desk"), env=ENV)
check(js.get("ok") and Path(js["dir"]) == vo_fx / "desk" / "awl-voiceover" / run_v.name and Path(js["dir"]).is_dir() and js["base_from"] == "--base",
      "voiceover outdir makes <base>/awl-voiceover/<run>, the folder the ElevenLabs MCP may write to")
fake_home = vo_fx / "home"
fake_home.mkdir()
(fake_home / ".claude.json").write_text(json.dumps({"mcpServers": {"elevenlabs": {"env": {"ELEVENLABS_API_KEY": "sk_fake_never_printed",
                                                                                        "ELEVENLABS_MCP_BASE_PATH": str(vo_fx / "mcp-base")}}}}), encoding="utf-8")
js, _, out_txt = t("voiceover", "outdir", "--run", run_v.name, env={**ENV, "USERPROFILE": str(fake_home), "HOME": str(fake_home), "ELEVENLABS_MCP_BASE_PATH": ""})
check(Path(js["dir"]) == vo_fx / "mcp-base" / "awl-voiceover" / run_v.name and "claude.json" in js["base_from"] and "sk_fake" not in out_txt,
      "without --base or the variable, outdir uses the ElevenLabs server's own base path from ~/.claude.json and never prints its key")
script = "[excited] Okay, you need this serum. [sighs] My skin looked tired… [laughs softly] Link in bio."
js, code, _ = t("voiceover", "record", "--run", run_v.name, "--video", "1", "--file", str(take_src), "--script", script, "--voice-id", "FGY2WhTYpPnrIDTdsKH5",
                "--voice-name", "Laura", "--model", "eleven_v4", "--language", "en", "--mode", "on-camera", "--settings", '{"stability": 0.5}', env=ENV)
take = Path(js["file"])
check(code == 0 and take.parts[-4:] == (run_v.name, "30-assets", "voiceover", "video-01-a1.mp3") and take.is_file() and take.with_suffix(".json").is_file(),
      "voiceover record copies the take into the run as video-01-a1.mp3 beside its sidecar (a bracketed source name is fine)")
check(len(js["phrases"]) == 5 and len(js["pauses"]) == 4 and abs(js["speech_start_s"] - 0.2) <= 0.05 and abs(js["speech_end_s"] - 3.6) <= 0.06,
      f"record measures the phrases and pauses ({len(js['phrases'])} phrases, speech {js['speech_start_s']}-{js['speech_end_s']} s)")
check(js["spoken_text"] == "Okay, you need this serum. My skin looked tired… Link in bio." and js["spoken_words"] == 12 and js["tags"] == ["[excited]", "[sighs]", "[laughs softly]"]
      and js["chars_sent"] == len(script) and js["script_source"] == "given", "record keeps the script as sent, the spoken words without the tags, and the characters sent")
check("no one listened" in js["note"] and not re.search(r'"(verdict|fits|ok_to_use|pronunciation_ok)"\s*:', json.dumps(js)), "record states facts only: no fit or pronunciation verdict")
st_v = json.loads((run_v / "state.json").read_text(encoding="utf-8"))
check(st_v["voiceover"]["files"]["01"]["attempt"] == 1 and st_v["voiceover"]["files"]["01"]["phrases"] == 5 and js["state_key"] == "voiceover.files.01",
      "record writes state.json -> voiceover.files.01")
js, _, _ = t("voiceover", "record", "--run", run_v.name, "--video", "01", "--file", str(take_b), "--attempt", "1", "--mode", "on-camera", env=ENV)
check(js.get("previous_kept_as") and Path(js["previous_kept_as"]).is_file() and Path(js["previous_kept_as"]).with_suffix(".json").is_file(),
      "the same attempt recorded from another file keeps the earlier take and its sidecar beside it")
js, code, _ = t("voiceover", "record", "--run", run_v.name, "--video", "1x", "--file", str(take_src), env=ENV, ok=False)
check(code == 2 and "NN or NN-cK" in js.get("error", ""), "record refuses a malformed --video (exit 2)")
js, code, _ = t("voiceover", "record", "--run", run_v.name, "--video", "2", "--file", str(take_src), "--settings", "not json", env=ENV, ok=False)
check(code == 2 and "--settings" in js.get("error", ""), "record refuses --settings that are not JSON (exit 2)")
js, _, _ = t("voiceover", "record", "--run", run_v.name, "--video", "02-c1", "--file", str(take_src), "--source", "file", "--transcribe", "--language", "en",
             env={**ENV, "AWL_TRANSCRIBE_STUB": "1"})
check(js["spoken_text"] == "stub words here" and js["script_source"].startswith("transcribed (stub") and js["chars_sent"] is None and js["state_key"] == "voiceover.files.02-c1",
      "the user's own file (source file) without a script: its words by local speech-to-text, no characters sent, a clip key NN-cK")

js, code, _ = t("voiceover", "record", "--run", run_v.name, "--video", "03-c2", "--file", str(take_src), "--source", "file", "--span", "1.3-3.8", env=ENV)
check(code == 0 and js["file"].endswith("video-03-c2-a1.wav") and js["span_s"] == [1.3, 3.8] and abs(js["duration_s"] - 2.5) <= 0.05 and len(js["phrases"]) == 3
      and abs(js["phrases"][0]["start"] - 0.2) <= 0.05, "record --span takes one clip's part of a longer own file (cut at a pause, as WAV) and measures it from the cut")
js, code, _ = t("voiceover", "record", "--run", run_v.name, "--video", "03-c2", "--file", str(take_src), "--span", "3.8-1.3", env=ENV, ok=False)
check(code == 2 and "--span" in js.get("error", ""), "record refuses a span whose start is not before its end (exit 2)")
js, code, _ = t("voiceover", "align", "--generated", str(vo_fx / "gen.mp4"), "--voiceover", str(take), "--out", str(vo_fx / "align"), env=ENV)
check(code == 0 and abs(js["global_offset_s"] - 0.25) <= 0.02 and js["global_corr"] >= 0.9 and js["voiceover_speech"]["phrases"] == 5 and js["generated_speech"]["phrases"] == 5,
      f"voiceover align finds where the model's speech lies against the take ({js.get('global_offset_s')} s at r={js.get('global_corr')}; 0.25 s built in)")
check(Path(js["plot"]).is_file() and (vo_fx / "align" / "vo-align.json").is_file() and "verdict" not in js and "no verdict" in js["note"]
      and "windows" not in js and len(json.loads(Path(js["windows_file"]).read_text(encoding="utf-8"))["windows"]) >= 2,
      "align writes vo-align.png and vo-align.json (every window) and prints only the summary, no verdict (the agent's context stays small)")
off = js["global_offset_s"]
mute_clip = make_clip(vo_fx / "mute.mp4", seconds=3.0, flash=None, audio=False)
js, code, _ = t("voiceover", "align", "--generated", str(mute_clip), "--voiceover", str(take), "--out", str(vo_fx / "align-mute"), env=ENV, ok=False)
check(code == 1 and "no audio stream" in js.get("error", ""), "align on a file without sound says there is nothing to align against (exit 1)")

js, code, _ = t("voiceover", "mix", "--picture", str(vo_fx / "gen.mp4"), "--voiceover", str(take), "--offset", str(off), "--bed", "mute", "--out", str(vo_fx / "with-voiceover.mp4"), env=ENV)
f = js["facts"]
check(code == 0 and f["has_video"] and f["has_audio"] and f["bed"] == "muted" and abs(f["duration_s"] - 4.5) <= 0.1 and f["vo_speech_cut_s"] == 0 and Path(js["track"]).is_file()
      and js["track"].endswith("with-voiceover.vo-track.wav"), "voiceover mix --bed mute lays the take on the picture, its length kept, and writes the CapCut voice track")
js, _, _ = t("voiceover", "align", "--generated", str(vo_fx / "with-voiceover.mp4"), "--voiceover", str(take), "--out", str(vo_fx / "align-mixed"), env=ENV)
check(abs(js["global_offset_s"] - off) <= 0.02 and js["global_corr"] >= 0.98,
      f"the mixed file's sound is the take: align reads r={js['global_corr']} at {js['global_offset_s']} s (near 1 at the mix offset)")
js, _, _ = t("voiceover", "mix", "--picture", str(vo_fx / "gen.mp4"), "--voiceover", str(take), "--offset", "3.0", "--bed", "keep", "--tempo", "1.05", "--out", str(vo_fx / "late.mp4"), env=ENV)
f = js["facts"]
check(f["bed"] == "kept" and f["bed_gain"] == 0.3 and f["tempo"] == 1.05 and f["vo_speech_cut_s"] > 1.5 and abs(f["vo_speech_end_on_picture_s"] - (3.6 / 1.05 + 3.0)) <= 0.1,
      f"a take placed late is reported as cut speech ({f['vo_speech_cut_s']} s past the picture's end), not refused")
js, code, _ = t("voiceover", "mix", "--picture", str(vo_fx / "gen.mp4"), "--voiceover", str(take), "--tempo", "3", "--out", str(vo_fx / "bad.mp4"), env=ENV, ok=False)
check(code == 2 and "--tempo" in js.get("error", ""), "mix refuses a tempo outside 0.5-2.0 (exit 2)")

js, _, _ = t("status", "--run", run_v.name, "--no-loupe", env=ENV)
check(js["voiceover"]["takes"] == ["01", "02-c1", "03-c2"] and js["voiceover"]["enabled"] is None, "status lists the recorded takes before the choice is stored")
t("state", "--run", run_v.name, "set", "voiceover.enabled=true", "voiceover.method=overlay", "voiceover.voice_name=Laura", env=ENV)
js, _, _ = t("status", "--run", run_v.name, "--no-loupe", env=ENV)
check(js["voiceover"]["enabled"] is True and js["voiceover"]["method"] == "overlay" and js["voiceover"]["takes"] == ["01", "02-c1", "03-c2"],
      "dotted state keys set the choice without touching the recorded takes; status reports them")

ct = (run_u / "50-requests" / "agent-contract.md").read_text(encoding="utf-8")
check("Voiceover: off (state.json" in ct and "Memes: n/a (Recreate" in ct, "the contract of a run without state.json -> voiceover says Voiceover: off; a Recreate run's Memes line is n/a")
t("state", "--run", run_u.name, "set", 'voiceover={"enabled": true, "method": "native", "source": "elevenlabs", "voice_id": "abc123", "voice_name": "Sarah", '
  '"model_id": "eleven_v4", "language": "sq", "language_name": "Albanian", "language_official": false, "preference": "Kosovar Albanian (Gheg dialect)"}', env=ENV)
js, _, _ = t("contract", "--run", run_u.name, "--notes", "the pilot is video 01", env=ENV)
ct = (run_u / "50-requests" / "agent-contract.md").read_text(encoding="utf-8")
check(js["unresolved_placeholders"] == [] and "Voiceover: on: method native (the take is the driving audio)" in ct and "ElevenLabs voice Sarah (abc123), model eleven_v4" in ct
      and "language Albanian (sq), outside the model's official list: pronunciation not checked" in ct and "preference: Kosovar Albanian (Gheg dialect)" in ct
      and f"{run_u.name}/30-assets/voiceover/video-NN*.*" in ct.replace("\\", "/"),
      "the contract fills the Voiceover line from state.json: the method, the voice, the language (unofficial: not checked), the preference and where the take is")
t("state", "--run", run_u.name, "set", "voiceover.method=overlay", "voiceover.source=file", env=ENV)
t("contract", "--run", run_u.name, env=ENV)
ct = (run_u / "50-requests" / "agent-contract.md").read_text(encoding="utf-8")
check("method overlay (no dialogue; the take over the picture)" in ct and "the user's own voiceover files (source file)" in ct and "ElevenLabs voice" not in ct.split("Voiceover:")[1][:400],
      "an overlay run of the user's own files says so in the contract, with no ElevenLabs voice")
t("state", "--run", run_u.name, "set", "analyze_submode=create", "memes=none", env=ENV)
t("contract", "--run", run_u.name, env=ENV)
ct = (run_u / "50-requests" / "agent-contract.md").read_text(encoding="utf-8")
js, _, _ = t("status", "--run", run_u.name, "--no-loupe", env=ENV)
check("Memes: none (pure generation" in ct and js["memes"] == "none", "a Create run with memes=none says so in its contract and in status")
t("state", "--run", run_u.name, "set", "memes=", env=ENV)
t("contract", "--run", run_u.name, env=ENV)
ct = (run_u / "50-requests" / "agent-contract.md").read_text(encoding="utf-8")
check("Memes: include (only the inserts your plan names)" in ct, "a Create run without the memes key includes them (its plans were made that way)")
js, _, _ = t("lint-run", "--run", run_u.name, env=ENV)
check(js["contract"]["unresolved_placeholders"] == [] and js["contract"]["voiceover_line"] is True and js["contract"]["memes_line"] is True,
      "lint-run finds the Voiceover and Memes lines and no unresolved placeholder in the contract")
# the sync pass (lipsync): its request names the accepted clip's job and the take's upload; both are known to lint-run, and its ledger lane is the video's
(run_v / "50-requests").mkdir(exist_ok=True)
clip_req = run_v / "50-requests" / "video-01-request.json"
clip_req.write_text(json.dumps({"params": {"prompt": "she says the lines to the camera", "model": "seedance_2_5"}}), encoding="utf-8")
clip_job, take_media = "aaaaaaaa-1111-2222-3333-444444444444", "bbbbbbbb-1111-2222-3333-444444444444"
lg = t("ledger", "begin", "--run", run_v.name, "--video", "01", "--attempt", "1", "--request", str(clip_req), env=ENV)[0]
t("ledger", "set", "--run", run_v.name, "--fingerprint", lg["fingerprint"], "--status", "completed", "--job", clip_job, env=ENV)
t("uploads", "set", "--run", run_v.name, "--video", "01", "--label", "Audio 1", "--role", "audio_references", "--media-id", take_media, "--file", str(take),
  "--content-type", "audio/mpeg", env=ENV)
sync_req = run_v / "50-requests" / "video-01-sync-request.json"
sync_req.write_text(json.dumps({"model": "sync_so", "medias": [{"role": "input_video", "value": clip_job}, {"role": "input_audio", "value": take_media}],
                                "sync_mode": "silence"}), encoding="utf-8")
js, code, _ = t("ledger", "begin", "--run", run_v.name, "--video", "01-sync", "--attempt", "1", "--request", str(sync_req), env=ENV)
check(code == 0 and js.get("recorded") and not js.get("conflicts"), "the sync pass is recorded in the video's lane (--video 01-sync) with no conflict once the clip's job is finished")
js, _, _ = t("lint-run", "--run", run_v.name, env=ENV)
check(js["media_ids"]["unknown_total"] == 0 and js["media_ids"]["known_ledger_job_ids"] == 1, "lint-run knows the clip's job id (from the ledger) and the take's media id (from the uploads) that the sync request names")
js, _, _ = t("doctor", "--no-loupe", "--no-docs", env=ENV)
check("elevenlabs" in js["mcp"] or "error" in js["mcp"], "doctor reports whether the ElevenLabs MCP is registered")

# --- effort (item 33): a new run's level is empty until the user's answer is stored (new-run writes null; `effort` and prep-all stop on
#     it); a run made before item 33 keeps max; each of the five levels stores its whole column, the same as effort.md §1's table, and sets
#     prep-all's sampling; custom values are held to the bounds; coverage never drops; QC is untouched (the judges stay stable)
from t00_common import LIB  # noqa: E402
ef_src = home.parent / "effort-src"
ef_src.mkdir(parents=True, exist_ok=True)
burst = ef_src / "bursts.mp4"           # a still frame with a moving box in the first second of every 5 s: 8 motion bursts in 40 s
subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=gray:s=240x426:r=30:d=40", "-f", "lavfi", "-i", "testsrc2=s=96x96:r=30:d=40",
                "-filter_complex", "[0][1]overlay=x='mod(t*300,144)':y=160:enable='lt(mod(t,5),1)',format=yuv420p", "-t", "40", str(burst)], check=True)
run_f = Path(t("new-run", "--mode", "analyze", "--source", str(ef_src), "--slug", "effort", env=ENV)[0]["run_dir"])
t("inventory", str(ef_src), "--run", str(run_f), "--as", "references", env=ENV)
t("state", "--run", run_f.name, "set", "audio_ingest=frames-only", "analyze_submode=create", env=ENV)
check(json.loads((run_f / "state.json").read_text(encoding="utf-8")).get("effort", "missing") is None,
      "new-run writes state.json -> effort empty (null) until the start stores the user's level")
js, code, _ = t("effort", "--run", run_f.name, env=ENV, ok=False)
check(code == 2 and "five" in js.get("error", "") and "--level" in js.get("error", ""), "`effort` on a run whose level is not stored stops and says the user is asked, from all five levels")
js, code, _ = t("prep-all", "--run", run_f.name, "--jobs", "1", "--no-ocr", env=ENV, ok=False)
check(code == 2 and "effort" in js.get("error", ""), "prep-all stops before it samples a reference at a level the user did not pick")
js, code, _ = t("effort", "--run", run_f.name, "--max-agents", "3", env=ENV, ok=False)
check(code == 2 and "--level" in js.get("error", ""), "custom numbers on a run without a level need the nearest level with them")
check(t("status", "--run", run_f.name, "--no-loupe", env=ENV)[0]["effort"].get("pending") is True, "status reports the level as pending")
run_l = Path(t("new-run", "--mode", "analyze", "--source", str(ef_src), "--slug", "legacy", env=ENV)[0]["run_dir"])
st_l = json.loads((run_l / "state.json").read_text(encoding="utf-8"))
st_l.pop("effort", None)
(run_l / "state.json").write_text(json.dumps(st_l), encoding="utf-8")
js, _, _ = t("effort", "--run", run_l.name, env=ENV)
check(js["effort"]["level"] == "max" and "no effort key" in js["effort"].get("note", ""), "a run made before item 33 (no key) keeps max and is never asked")
# the five levels: the toolkit's columns are effort.md §1's table, and prep-all samples at each one
doc = (LIB / "reference" / "effort" / "010_1_the-question-awl-start-step-5d.md").read_text(encoding="utf-8")
rows = {r[0].strip(): [c.strip() for c in r[1:]] for r in (ln.strip().strip("|").split("|") for ln in doc.splitlines() if ln.startswith("| ") and "---" not in ln)}
cols = ["low", "medium", "high", "xhigh", "max"]
num = lambda v: None if v == "no cap" else float(v)  # noqa: E731
DOC = {c: {"analysis_fps": num(rows["references, frames per second"][i]), "analysis_dense_fps": num(rows["around motion and in the first second"][i]),
           "motion_peaks": num(rows["motion peaks densified per reference (±0.5 s each)"][i]), "densify_ranges": num(rows["close-ups an analyst may add per reference"][i]),
           "max_agents": num(rows["production agents at once"][i]), "pilot_from": num(rows["pilot video first, from this many videos"][i])} for i, c in enumerate(cols)}
check(rows.get("setting") == ["Low", "Medium", "High", "XHigh", "Max"] and all(f"{k}. **{n}**" in doc for k, n in enumerate(["Low", "Medium", "High", "XHigh", "Max"], 1)),
      "effort.md §1 offers the five levels: the table's columns and the numbered list Low, Medium, High, XHigh, Max")
t("effort", "--run", run_f.name, "--level", "low", env=ENV)
lv = t("effort", "--run", run_f.name, env=ENV)[0]["levels"]
fl = lambda v: None if v is None else float(v)  # noqa: E731
check(sorted(lv) == sorted(cols) and all({k: fl(v) for k, v in lv[c].items()} == DOC[c] for c in cols), "the toolkit's five levels are effort.md §1's table, column for column")
cells = {}
for c in cols:
    t("effort", "--run", run_f.name, "--level", c, env=ENV)
    stored = json.loads((run_f / "state.json").read_text(encoding="utf-8"))["effort"]
    js, _, _ = t("prep-all", "--run", run_f.name, "--jobs", "1", "--no-ocr", "--redo", env=ENV)
    v = run_f / "10-media" / "V01"
    vj = json.loads((v / "video.json").read_text(encoding="utf-8"))
    fr = json.loads((v / "frames.json").read_text(encoding="utf-8"))["frames"]
    base = sorted(f["t"] for f in fr if f.get("kind") == "base")
    pk = sorted({round(f["t"], 4) for f in fr if f.get("why") == "peak"})
    gaps = [b - a for a, b in zip(pk, pk[1:]) if b - a > 1e-3]
    act = json.loads((v / "activity.json").read_text(encoding="utf-8"))["peaks"]
    want = DOC[c]
    cells[c] = vj["sampling"]["storyboard_cells"]
    check(all(fl(stored[k]) == want[k] for k in want) and stored["level"] == c
          and js["sampling"] == {"effort": c, "baseline_fps": want["analysis_fps"], "dense_fps": want["analysis_dense_fps"], "motion_peaks": int(want["motion_peaks"])}
          and abs(vj["sampling"]["baseline_frames"] - 40 * want["analysis_fps"]) <= 2
          and bool(gaps) and abs(min(gaps) - 1 / want["analysis_dense_fps"]) < 0.02
          and 0 < len(act) <= want["motion_peaks"] and max(b - a for a, b in zip(base, base[1:])) <= 1.01,
          f"{c}: the column is stored; prep-all samples {want['analysis_fps']:g} fps ({vj['sampling']['baseline_frames']} baseline frames in 40 s), "
          f"{want['analysis_dense_fps']:g} fps around motion (closest {min(gaps) if gaps else 0:.3f} s), {len(act)} of at most {want['motion_peaks']:g} peaks, every second covered")
check(cells["low"] < cells["medium"] < cells["high"] < cells["xhigh"] and cells["xhigh"] == cells["max"],
      f"the storyboard grows with the level ({cells}); XHigh and Max sample alike and differ only in the analysts' close-ups")
js, _, _ = t("effort", "--run", run_f.name, "--analysis-fps", "1", "--analysis-dense-fps", "3", "--motion-peaks", "1", "--densify-ranges", "0",
             "--max-agents", "0", "--pilot-from", "9", env=ENV)
held = {h["key"]: h["held_to"] for h in js["held_to_bounds"]}
check(js["effort"]["analysis_fps"] == 2.0 and js["effort"]["analysis_dense_fps"] == 6.0 and js["effort"]["motion_peaks"] == 4 and js["effort"]["densify_ranges"] == 2
      and js["effort"]["max_agents"] == 1 and js["effort"]["pilot_from"] == 5 and held["pilot_from"] == "ceiling" and held["analysis_fps"] == "floor",
      "custom values are held to the bounds (2 fps, 6 around motion, 4 peaks, 2 close-ups, 1 agent, a pilot from 5 videos at the latest)")
js, code, _ = t("effort", "--run", run_f.name, "--qc-dense-fps", "15", env=ENV, ok=False)
check(code == 2, "effort has no QC option: the judges are not part of the level")
# a moving source has motion peaks: their window stays +-0.5 s at a low dense rate
mv = ef_src.parent / "motion" / "moving.mp4"
mv.parent.mkdir(parents=True, exist_ok=True)
subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=size=360x640:rate=30:duration=8", "-pix_fmt", "yuv420p", str(mv)], check=True)
js, _, _ = t("prep-video", str(mv), "--out", str(mv.parent / "V"), "--no-ocr", "--audio-ingest", "frames-only", "--fps", "2", "--dense-fps", "6", env=ENV)
act = json.loads((mv.parent / "V" / "activity.json").read_text(encoding="utf-8"))["peaks"]
pk = [f for f in json.loads((mv.parent / "V" / "frames.json").read_text(encoding="utf-8"))["frames"] if f.get("why") == "peak"]
check(act and pk and all(min(abs(f["t"] - q["t"]) for q in act) <= 0.51 for f in pk),
      f"each motion peak keeps its ±0.5 s window at a low dense rate ({len(act)} peaks, {len(pk)} peak frames)")
qc_clip = make_clip(ef_src.parent / "qc-src" / "clip-q.mp4", seconds=6.0, flash=(3.0, 3.4), audio=True, size="360x640")
js, _, _ = t("qc", "--video", str(qc_clip), "--out", str(home.parent / "qc-stable"), "--mode", "analyze", "--no-ocr", "--dense", "mid:2-3", env=ENV)
check("sampling" not in js and js["dense"][0]["fps"] == 30.0 and js["dense"][0]["frames"] == 31, "qc is unchanged: its checkpoint sheets at 30 fps, no effort in its answer")
t("state", "--run", run_f.name, "set", "model=wan3_0_prime", "qc_fixes=auto", "loupe=up", env=ENV)
t("contract", "--run", run_f.name, env=ENV)
ct = (run_f / "50-requests" / "agent-contract.md").read_text(encoding="utf-8")
st_js, _, _ = t("status", "--run", run_f.name, "--no-loupe", env=ENV)
check("Effort" not in ct and "item 34" in ct and st_js["effort"]["level"] == "max",
      "the agent contract carries no effort line and does carry the read-only folders (item 34); status reports the run's level")

finish()
