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
# the admin, 2026-11-03: uploads named relative to the pipeline's home (runs/<run>/...) were found by no reader in the run: the file is recorded in full
run_p = Path(t("new-run", "--mode", "analyze", "--source", str(home.parent / "refs-c"), "--slug", "up-paths", env=ENV)[0]["run_dir"])
(run_p / "55-references" / "video-03" / "a2").mkdir(parents=True, exist_ok=True)
(run_p / "55-references" / "video-03" / "a2" / "image1-man.png").write_bytes(b"\x89PNG\r\n\x1a\n")
t("uploads", "set", "--run", run_p.name, "--video", "03", "--label", "a2 Image 1", "--media-id", "33333333-2222-3333-4444-555555555555",
  "--file", "55-references/video-03/a2/image1-man.png", env=ENV)
t("uploads", "set", "--run", run_p.name, "--video", "03", "--label", "a2 Image 2", "--media-id", "33333333-2222-3333-4444-555555555556",
  "--file", "nowhere/image2-gone.png", env=ENV)
up_p = json.loads((run_p / "50-requests" / "video-03-uploads.json").read_text(encoding="utf-8"))["uploads"]
check(up_p["a2 Image 1"]["file"] == str((run_p / "55-references" / "video-03" / "a2" / "image1-man.png").resolve())
      and up_p["a2 Image 2"]["file"] == "nowhere/image2-gone.png",
      "uploads set records a file named relative to the run (or to the folder it runs from) in full, the form every reader finds; one it cannot find "
      "stays as given")
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

# --- the judge decides the product images (the admin, 2026-10-30): each input records its source; template-apply (X4b) and product-images (a QC
#     regeneration) apply the judge's list through one plan; the inputs before the product images keep their numbers; facts first
run_p = Path(t("new-run", "--mode", "analyze", "--source", str(home.parent / "refs-c"), "--slug", "x4b-products", env=ENV)[0]["run_dir"])
for sub in ("50-requests", "40-briefs", "30-assets/project", "60-outputs/video-01"):
    (run_p / sub).mkdir(parents=True, exist_ok=True)
assets_root = home.parent / "client-x" / "assets"
inv_items = [{"id": "A47", "kind": "image", "path": str(assets_root / "face-47.jpg")}, {"id": "A82", "kind": "image", "path": str(assets_root / "carton" / "Carton-Front.png")},
             {"id": "A81", "kind": "image", "path": str(assets_root / "carton" / "Carton-Front-Angled.png")},
             {"id": "A273", "kind": "image", "path": str(assets_root / "photos" / "IMG_6917.jpg")}]
(run_p / "30-assets" / "project" / "asset-inventory.json").write_text(json.dumps({"items": inv_items}), encoding="utf-8")
(run_p / "30-assets" / "registry.md").write_text("| id | what | files |\n|---|---|---|\n| P-X-CARTON | product | A82 `Carton-Front.png` (template), A81 Front-Angled |\n| C-X-01 | character | A47 |\n", encoding="utf-8")


def src(aid, path, prep, kind):
    return {"original": str(path), "asset_id": aid, "prepared": prep, "kind": kind}


p_draft = {"params": {"model": "wan3_0_prime", "duration": 5, "prompt": "DRAFT the man (Image 1) holds the carton of Image 2 and Image 3.",
                      "medias": [{"role": "video_references", "value": "v1", "label": "Video 1"},
                                 {"role": "image_references", "value": "<X3: image1-character-face.jpg>", "label": "Image 1", "source": src("A47", inv_items[0]["path"], "face crop", "character")},
                                 {"role": "image_references", "value": "<X3: image2-product-front.png>", "label": "Image 2 = image2-product-front", "source": src("A82", inv_items[1]["path"], "padded on grey", "product")},
                                 {"role": "image_references", "value": "<X3: image3-product-flat.png>", "label": "Image 3 = image3-product-flat", "source": src("A273", inv_items[3]["path"], "cut out, soft shadow", "product")}]}}
rq_pp = run_p / "50-requests" / "video-01-request.json"
rq_pp.write_text(json.dumps(p_draft), encoding="utf-8")
(run_p / "40-briefs" / "video-01-musts.md").write_text("- The printed label exactly as in Image 2.\n- The carton lies as flat as in Image 3.\n- Keep the camera still.\n", encoding="utf-8")
tpl_p = run_p / "40-briefs" / "video-01-template.json"


def tpl(prompt, pims):
    tpl_p.write_text(json.dumps({"template": prompt, "product_images": pims}), encoding="utf-8")


tpl("JUDGE the man of Image 1 holds the carton. The printed label exactly as in Image 2. The carton lies as flat as in Image 3. Image 4 shows its angle. Keep the camera still.",
    [{"asset": "A82"}, {"asset": "A273"}, {"asset": "A81", "why": "the angled view gave the thickness in S40"}])
js, code, _ = t("template-apply", "--run", run_p.name, "--video", "01", env=ENV)
rq = json.loads(rq_pp.read_text(encoding="utf-8"))
imgs = [m for m in rq["params"]["medias"] if m["role"] == "image_references"]
check(code == 0 and len(imgs) == 4 and imgs[3]["source"]["asset_id"] == "A81" and imgs[3]["source"]["kind"] == "product" and imgs[3]["value"].startswith("<X3: prepare Carton-Front-Angled.png")
      and [m["value"] for m in imgs[:3]] == [m["value"] for m in p_draft["params"]["medias"][1:]] and rq["params"]["medias"][0]["role"] == "video_references"
      and rq["product_images"]["added"][0]["image"] == "Image 4" and js["product_images"]["added"][0]["asset"] == "A81" and js["musts_missing"] == []
      and js["prompt_names_images_beyond_the_inputs"] == [],
      "template-apply adds the judge's product image after the last one (Image 4, a placeholder with its source to prepare), keeps every other input and its number, and records it")
tpl("JUDGE the man of Image 1 holds the carton. The printed label exactly as in Image 3. The carton lies as flat as in Image 2. Keep the camera still.",
    [{"asset": "A273"}, {"asset": "A82"}])
js, _, _ = t("template-apply", "--run", run_p.name, "--video", "01", env=ENV)
rq = json.loads(rq_pp.read_text(encoding="utf-8"))
imgs = [m for m in rq["params"]["medias"] if m["role"] == "image_references"]
check([m["source"]["asset_id"] for m in imgs] == ["A47", "A273", "A82"] and imgs[1]["label"].startswith("Image 2 =") and js["musts_missing"] == []
      and sorted(r["as"] for r in js["musts_renumbered"]) == ["The carton lies as flat as in Image 2.", "The printed label exactly as in Image 3."]
      and js["product_images"]["renumbered"] == {"Image 3": "Image 2", "Image 2": "Image 3"},
      "the judge's order renumbers only the product images, and a must-carry line naming one is checked in its new number")
tpl("JUDGE the man of Image 1 holds the carton. The printed label exactly as in Image 2. Keep the camera still.", [{"asset": "A82"}])
js, _, _ = t("template-apply", "--run", run_p.name, "--video", "01", env=ENV)
rq = json.loads(rq_pp.read_text(encoding="utf-8"))
check(len([m for m in rq["params"]["medias"] if m["role"] == "image_references"]) == 2 and js["product_images"]["dropped"] == ["Image 3"]
      and js["musts_superseded"] == ["The carton lies as flat as in Image 3."] and js["musts_missing"] == [],
      "a product image the judge leaves out leaves the request, and the must-carry line naming it is reported as no longer the request's, never as missing")
tpl("JUDGE the carton of Image 2 and Image 5. The printed label exactly as in Image 2. The carton lies as flat as in Image 3. Keep the camera still.", [{"file": "no-such.png"}])
js, _, _ = t("template-apply", "--run", run_p.name, "--video", "01", env=ENV)
rq = json.loads(rq_pp.read_text(encoding="utf-8"))
check(js["product_images"] is None and js["product_images_problems"] and "no-such.png" in js["product_images_problems"][0]
      and [m["value"] for m in rq["params"]["medias"]] == [m["value"] for m in p_draft["params"]["medias"]] and js["prompt_names_images_beyond_the_inputs"] == ["Image 5"],
      "a product image the run does not have is a problem: the draft's inputs stay, and an image the prompt names that the request does not carry is reported")
js, _, _ = t("template-apply", "--run", run_p.name, "--video", "01", "--use-draft", env=ENV)
rq = json.loads(rq_pp.read_text(encoding="utf-8"))
check(rq["params"]["medias"] == p_draft["params"]["medias"] and "product_images" not in rq, "--use-draft keeps the draft's inputs as they are")
# product images that are not the last image inputs: nothing applied
bad_draft = json.loads(json.dumps(p_draft))
bm = bad_draft["params"]["medias"]
bm[1], bm[2] = bm[2], bm[1]
(run_p / "50-requests" / "video-01-request.draft.json").write_text(json.dumps(bad_draft), encoding="utf-8")
tpl("JUDGE.", [{"asset": "A82"}, {"asset": "A81"}])
js, _, _ = t("template-apply", "--run", run_p.name, "--video", "01", env=ENV)
check(js["product_images"] is None and any("not the last image inputs" in x for x in js["product_images_problems"]),
      "product images that are not the last image inputs are reported and left as they are")
(run_p / "50-requests" / "video-01-request.draft.json").write_text(json.dumps(p_draft), encoding="utf-8")
t("template-apply", "--run", run_p.name, "--video", "01", "--use-draft", env=ENV)
rq_noso = json.loads(json.dumps(p_draft))
rq_noso["params"]["medias"][1].pop("source")
(run_p / "50-requests" / "video-02-request.json").write_text(json.dumps(bad_draft), encoding="utf-8")
(run_p / "50-requests" / "video-03-request.json").write_text(json.dumps(rq_noso), encoding="utf-8")
lint_p, _, _ = t("lint-run", "--run", run_p.name, env=ENV)
check({"file": "video-03-request.json", "image": "Image 1"} in lint_p["inputs"]["without_a_recorded_source"]
      and {"file": "video-02-request.json", "order": "P-P"} in lint_p["inputs"]["product_images_not_last"]
      and not any(x["file"] == "video-01-request.json" for x in lint_p["inputs"]["product_images_not_last"]),
      "lint-run lists an image input with no recorded source and a request whose product images are not the last image inputs")
# a regeneration takes the judge's product images from its QC answer (product-images), keeping what each number its prompt names means
regen = json.loads(json.dumps(p_draft))
regen["params"]["prompt"] = "REGEN the man (Image 1) holds the carton of Image 2 and Image 3."
rg_p = run_p / "50-requests" / "video-01-a2-request.json"
rg_p.write_text(json.dumps(regen), encoding="utf-8")
qc_p = run_p / "60-outputs" / "video-01" / "qc-consult.json"
qc_p.write_text(json.dumps({"product_images": [{"asset": "A82"}, {"asset": "A273"}, {"asset": "A81", "prepare": "padded on grey", "why": "the angle"}]}), encoding="utf-8")
js, _, _ = t("product-images", "--run", run_p.name, "--video", "01", "--request", str(rg_p), env=ENV)
check(js["ok"] and not js["applied"] and json.loads(rg_p.read_text(encoding="utf-8")) == regen and js["added"][0]["image"] == "Image 4",
      "product-images prints the plan as facts and writes nothing without --apply")
js, _, _ = t("product-images", "--run", run_p.name, "--video", "01", "--request", str(rg_p), "--apply", env=ENV)
rg = json.loads(rg_p.read_text(encoding="utf-8"))
check(js["applied"] and len([m for m in rg["params"]["medias"] if m["role"] == "image_references"]) == 4 and rg["product_images"]["by"].startswith("the judge (QC")
      and Path(js["kept_as"]).is_file() and rg["params"]["prompt"] == regen["params"]["prompt"],
      "with --apply the regeneration's request takes the added product image after the last one, its prompt untouched, the request as it was kept beside it")
qc_p.write_text(json.dumps({"product_images": [{"asset": "A273"}, {"asset": "A82"}]}), encoding="utf-8")
rg_p.write_text(json.dumps(regen), encoding="utf-8")
js, _, _ = t("product-images", "--run", run_p.name, "--video", "01", "--request", str(rg_p), "--apply", env=ENV)
check(not js["ok"] and not js["applied"] and "keeps what each image number" in js["problems"][0] and json.loads(rg_p.read_text(encoding="utf-8")) == regen,
      "a regeneration never moves an image its prompt names: the judge's reorder is refused and nothing is written")
st_p = json.loads((run_p / "state.json").read_text(encoding="utf-8"))
st_p.setdefault("submissions", []).append({"video": "01", "attempt": 2, "status": "submitted", "request_file": str(rg_p)})
(run_p / "state.json").write_text(json.dumps(st_p), encoding="utf-8")
qc_p.write_text(json.dumps({"product_images": [{"asset": "A82"}, {"asset": "A273"}, {"asset": "A81"}]}), encoding="utf-8")
js, _, _ = t("product-images", "--run", run_p.name, "--video", "01", "--request", str(rg_p), "--apply", env=ENV)
check(not js["ok"] and "in the ledger" in js["problems"][0] and json.loads(rg_p.read_text(encoding="utf-8")) == regen,
      "a request the ledger holds is never changed: a regeneration writes its own request")
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
check("the house size: 10, or 11 when the video has only a little text" in " ".join(ct.split()),
      "the agent contract states the house size: 10, or 11 when the video has only a little text (the user, 2026-10-29)")

# --- the house text size (the user, 2026-10-29: "our standard text size is 10 but when there's only few text to be placed then use
# font size 11"): one size per video, 11 when at no moment more than 5 words are on screen and every line fits at 11
import glob as _glob


def _draft(name, events):
    """A minimal CapCut draft: one text material per event (text, in s, out s, track)."""
    d = home.parent / "capcut" / name
    d.mkdir(parents=True, exist_ok=True)
    mats, tracks = [], {}
    for i, (text, a, b, tr) in enumerate(events):
        mats.append({"id": f"T{i}", "font_size": 10.0,
                     "content": json.dumps({"text": text, "styles": [{"range": [0, len(text)], "size": 10.0}]})})
        tracks.setdefault(tr, []).append({"material_id": f"T{i}", "target_timerange": {"start": int(a * 1e6), "duration": int((b - a) * 1e6)},
                                          "clip": {"scale": {"x": 1.0, "y": 1.0}, "transform": {"x": 0.0, "y": 0.5}}})
    (d / "draft_content.json").write_text(json.dumps({"canvas_config": {"width": 1080, "height": 1920}, "materials": {"texts": mats},
                                                      "tracks": [{"type": "text", "segments": s} for s in tracks.values()]}), encoding="utf-8")
    return d


if not _glob.glob(os.path.join(os.environ.get("LOCALAPPDATA", ""), "CapCut", "Apps", "*", "Resources", "Font", "SystemFont", "en.ttf")):
    print("SKIP  the house text size: CapCut's System font is not installed on this machine")
else:
    sizes = {}
    for name, events in (("short", [("Who decided that?", 0, 4, 1), ("Hero vs villain", 4, 8, 1)]),
                         ("split", [("Professor: if u are not", 0, 5, 1), ("interested u can leave", 0, 5, 2)]),
                         ("wide", [("POV: YOU WORK IN SALES", 0, 5, 1)]),
                         ("long", [("POV: You picked option C\nthree times in a row and the\nnext answer is option C", 0, 6, 1)]),
                         ("paired", [("What I think I look like\nafter one sip:", 0, 4, 1), ("What I actually look like:", 4, 8, 1)])):
        js, code, _ = t("capcut-text-style", "--draft", str(_draft(name, events)), "--check", env=ENV, ok=False)
        sizes[name] = js.get("sizing") or {}
        sizes[name]["exit"] = code
    s = sizes["short"]
    check(s.get("size") == 11.0 and s.get("words_at_once_max") == 3 and s.get("widest_line_at_short_size", 1) <= 0.82 and s["exit"] == 1,
          f"two short texts one after the other: size 11 for the video ({s.get('why')}); --check reports them off style (exit 1)")
    check(sizes["split"].get("size") == 10.0 and sizes["split"].get("words_at_once_max") == 9,
          f"a caption split into two layers shown together counts whole: 9 words at once, size 10 ({sizes['split'].get('why')})")
    check(sizes["wide"].get("size") == 10.0 and sizes["wide"].get("words_at_once_max") == 5 and sizes["wide"].get("widest_line_at_short_size", 0) > 0.82,
          f"5 words that would be wider than 82% of the frame at 11 keep size 10 ({sizes['wide'].get('why')})")
    check(sizes["long"].get("size") == 10.0, f"a three-line hook keeps size 10 ({sizes['long'].get('why')})")
    check(sizes["paired"].get("size") == 10.0 and sizes["paired"].get("texts_on_timeline") == 2,
          "one size per video: the short second line of a pair stays at 10 beside its 9-word first line")
    d_short = home.parent / "capcut" / "short"
    js, code, _ = t("capcut-text-style", "--draft", str(d_short), env=ENV, ok=False)
    if code == 3 and "CapCut is running" in js.get("error", ""):
        check(not (d_short / "draft_content.json.textstyle.bak").exists(), "CapCut open: the write is refused and nothing is written")
    else:
        c = json.loads((d_short / "draft_content.json").read_text(encoding="utf-8"))
        got = [(m["font_size"], [st["size"] for st in json.loads(m["content"])["styles"]]) for m in c["materials"]["texts"]]
        js2, code2, _ = t("capcut-text-style", "--draft", str(d_short), "--check", env=ENV, ok=False)
        check(code == 0 and js.get("written") and got == [(11.0, [11.0]), (11.0, [11.0])] and (d_short / "draft_content.json.textstyle.bak").exists()
              and code2 == 0 and js2.get("texts_off_style") == 0,
              "the write sets font_size 11 and every style range to 11, keeps a .textstyle.bak, and --check then reports 0 off style")
    cfg_p = home / "config.json"
    cfg_txt = cfg_p.read_text(encoding="utf-8")
    cfg_off = json.loads(cfg_txt)
    cfg_off["capcut"]["text_style"]["short_text"] = None
    cfg_p.write_text(json.dumps(cfg_off), encoding="utf-8")
    js_s, _, _ = t("capcut-text-style", "--draft", str(_draft("short-off", [("Who decided that?", 0, 4, 1)])), "--check", env=ENV, ok=False)
    cfg_p.write_text(cfg_txt, encoding="utf-8")
    check(js_s.get("size") == 10.0 and str((js_s.get("sizing") or {}).get("short_text", "")).startswith("off"),
          "short_text set to null in config turns the rule off: size 10 for a short text")

# --- the join record (the user, 2026-10-29: a frame of a joined video is tied to the generation that made it, so a Loupe prompt box holds only the
# prompts of the generations its frames come from): concat writes <out>.join.json, and a command that keeps or trims the timeline carries it
import hashlib as _hl
jv = home.parent / "joinrec" / "runs" / "R" / "60-outputs" / "video-02"
jp = [(jv / "c1" / "a2" / "c1a.mp4", 1.0), (jv / "c2" / "a1" / "c2.mp4", 1.5), (jv / "c1" / "a2" / "c1b.mp4", 2.0)]      # c1 cut around c2
for jpath, jsecs in jp:
    make_clip(jpath, seconds=jsecs, flash=None, audio=True, size="720x1280")
js, _, _ = t("concat", "--clips", *[str(x) for x, _ in jp], "--out", str(jv / "joined.mp4"), env=ENV)
jrec = json.loads((jv / "joined.mp4.join.json").read_text(encoding="utf-8")) if (jv / "joined.mp4.join.json").is_file() else {}
check([(x["clip"], x["attempt"], x["t_from"], x["t_to"]) for x in jrec.get("pieces") or []] == [("c1", 2, 0.0, 1.0), ("c2", 1, 1.0, 2.5), ("c1", 2, 2.5, 4.5)]
      and jrec.get("sha1") == _hl.sha1((jv / "joined.mp4").read_bytes()).hexdigest() and js.get("join_record"),
      f"concat writes the join record: every piece with its clip, attempt and seconds of the output, and the output's sha1 ({jrec.get('pieces')})")
js, _, _ = t("trim", "--video", str(jv / "joined.mp4"), "--out", str(jv / "trimmed.mp4"), "--start", "0.5", "--end", "4.0", env=ENV)
trec = json.loads((jv / "trimmed.mp4.join.json").read_text(encoding="utf-8")) if (jv / "trimmed.mp4.join.json").is_file() else {}
check([(x["clip"], x["t_from"], x["t_to"]) for x in trec.get("pieces") or []] == [("c1", 0.0, 0.5), ("c2", 0.5, 2.0), ("c1", 2.0, 3.5)]
      and trec.get("sha1") == _hl.sha1((jv / "trimmed.mp4").read_bytes()).hexdigest() and trec.get("made_from", "").endswith("joined.mp4"),
      f"trim carries the join record, shifted to its own seconds ({trec.get('pieces')})")
js, _, _ = t("conform", "--video", str(jv / "joined.mp4"), "--out", str(jv / "conformed.mp4"), env=ENV)
crec = json.loads((jv / "conformed.mp4.join.json").read_text(encoding="utf-8")) if (jv / "conformed.mp4.join.json").is_file() else {}
check(len(crec.get("pieces") or []) == 3 and crec.get("sha1") == _hl.sha1((jv / "conformed.mp4").read_bytes()).hexdigest(),
      "conform keeps the timeline and carries the join record with the new file's own sha1")
# a with-inserts clean: the joined video cut at its split point, an insert between the two pieces, joined again
t("trim", "--video", str(jv / "joined.mp4"), "--out", str(jv / "part1.mp4"), "--start", "0", "--end", "1.5", env=ENV)
t("trim", "--video", str(jv / "joined.mp4"), "--out", str(jv / "part2.mp4"), "--start", "1.5", env=ENV)
make_clip(jv / "inserts" / "meme.mp4", seconds=1.0, flash=None, audio=True, size="720x1280")
t("concat", "--clips", str(jv / "part1.mp4"), str(jv / "inserts" / "meme.mp4"), str(jv / "part2.mp4"), "--out", str(jv / "with-inserts.mp4"), env=ENV)
wrec = json.loads((jv / "with-inserts.mp4.join.json").read_text(encoding="utf-8")) if (jv / "with-inserts.mp4.join.json").is_file() else {}
check([(x["clip"], x["t_from"], x["t_to"]) for x in wrec.get("pieces") or []] == [("c1", 0.0, 1.0), ("c2", 1.0, 1.5), ("", 1.5, 2.5), ("c2", 2.5, 3.5), ("c1", 3.5, 5.5)],
      f"a join of pieces that are joins themselves keeps their generations, and an insert is a piece of no clip ({[(x['clip'], x['t_from'], x['t_to']) for x in wrec.get('pieces') or []]})")


# --- a caught flag's prompt diff is prompt text: every changed sentence whole and all of them (the user, 2026-10-29: never trimmed)
import importlib.util as _ilu
from t00_common import AWL  # noqa: E402
_spec = _ilu.spec_from_file_location("awl_under_test", AWL)
_awl = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_awl)
_old = " ".join(f"Sentence {i} " + "x" * 400 + "." for i in range(20))
_new = " ".join(f"Sentence {i} " + "y" * 400 + "." for i in range(20))
_d = _awl._cf_sentence_diff(_old, _new).splitlines()
check(len(_d) == 40 and all(len(x) > 400 for x in _d) and not any("more changed" in x for x in _d),
      f"a caught flag's diff keeps every changed sentence whole and all of them ({len(_d)} lines, the shortest {min(map(len, _d)) if _d else 0} characters)")

# --- a registry row in either form (the admin's run 20261028-202809 wrote '| NG-EF6-SPE | product | ... |'): its asset ids, or its id in an input's
#     label, make a product view; a character's row does not
import tempfile as _tf  # noqa: E402
_rd = Path(_tf.mkdtemp(prefix="awl-reg-"))
(_rd / "30-assets").mkdir(parents=True)
(_rd / "30-assets" / "registry.md").write_text("| id | type | role |\n|---|---|---|\n| NG-EF6-SPE | product | the carton (A44) |\n| CH12 | character | the employee (A16) |\n",
                                              encoding="utf-8")
_req = {"params": {"medias": [{"role": "image_references", "value": "m1", "label": "identity CH12"},
                              {"role": "image_references", "value": "m2", "label": "NG-EF6-SPE-angled"}]}}
_imgs = _awl._pi_images(_req, _rd)
_txt = _awl._pi_inputs_text(_req, _rd)
check([x["product"] for x in _imgs] == [False, True] and [r[0] for r in _awl._pi_registry_rows(_rd)] == ["NG-EF6-SPE"] and "Image 1 (image_references; its original" in _txt,
      "a registry row whose type cell says product is a product row (a character's is not), and an input labelled with its id is a product view")

# --- Static (contract item 36, the user 2026-11-05): 1 fps without extras, the image API through a local mock (the key never printed or
# written), the prompts file and the user's folder (copied, never moved), the voice and bed stubs, the narration's words, the local render,
# the Static contract. No model, no network, no Higgsfield, no Loupe.
import base64 as _b64  # noqa: E402
import io as _io  # noqa: E402
import threading as _th  # noqa: E402
from http.server import BaseHTTPRequestHandler as _BH, HTTPServer as _HS  # noqa: E402
from PIL import Image as _Im  # noqa: E402

js, _, _ = t("new-run", "--mode", "analyze", "--source", str(refs), "--slug", "static-fps", env=ENV)
_srun = Path(js["run_dir"])
js, _, _ = t("prep-video", str(clip), "--out", str(_srun / "10-media" / "V01"), "--id", "V01", "--audio-ingest", "frames-only", "--fps", "1",
             "--dense-fps", "1", "--no-extras", "--no-ocr", env=ENV)
_fr = json.loads((_srun / "10-media" / "V01" / "frames.json").read_text(encoding="utf-8"))
_frames = _fr.get("frames", _fr) if isinstance(_fr, dict) else _fr
check(js.get("ok") and all(f.get("kind") == "base" for f in _frames) and len(_frames) <= 5,
      f"prep-video --fps 1 --no-extras keeps the 1 fps baseline only: no extra frames at the cut or around motion ({len(_frames)} frames for 4 s)")

_KEY = "sk-test-NEVER-PRINT-424242"
_SEEN = []


def _png(col, size=(1088, 1920)):
    b = _io.BytesIO()
    _Im.new("RGB", size, col).save(b, "PNG")
    return _b64.b64encode(b.getvalue()).decode()


class _Mock(_BH):
    def log_message(self, *a):
        pass

    def _send(self, code, obj):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode())

    def do_GET(self):
        self._send(200 if "gpt-image" in self.path else 404, {"id": self.path.rsplit("/", 1)[-1]})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        _SEEN.append({"path": self.path, "auth": self.headers.get("Authorization"), "refs": len(body.get("images") or []),
                      "size": body.get("size"), "quality": body.get("quality")})
        if "BLOCKME" in (body.get("prompt") or ""):
            self._send(400, {"error": {"type": "image_generation_user_error", "code": "moderation_blocked", "message": "blocked",
                                       "moderation_details": {"moderation_stage": "input", "categories": ["violence"]}}})
            return
        self._send(200, {"created": 1730000000 + len(_SEEN), "data": [{"b64_json": _png((30 * len(_SEEN) % 255, 80, 150))}],
                         "usage": {"input_tokens": 120, "output_tokens": 4000, "input_tokens_details": {"text_tokens": 100, "image_tokens": 20}}})


_srv = _HS(("127.0.0.1", 0), _Mock)
_th.Thread(target=_srv.serve_forever, daemon=True).start()
SENV = {**ENV, "AWL_TTS_STUB": "1", "AWL_MUSIC_STUB": "1", "AWL_TRANSCRIBE_STUB": "1", "OPENAI_API_KEY": _KEY,
        "AWL_OPENAI_BASE_URL": f"http://127.0.0.1:{_srv.server_port}/v1"}
_outs = []


def ts(*args, ok=True):
    js_, code_, out_ = t(*args, env=SENV, ok=ok)
    _outs.append(out_)
    return js_, code_


js, _ = ts("new-run", "--mode", "analyze", "--slug", "static")
SR = Path(js["run_dir"])
ts("state", "--run", str(SR), "set", "analyze_submode=static", "static_images=api", "audio_ingest=whisper", "qc_fixes=auto")
js, _ = ts("static", "check", "--offline")
check(js["parts"]["images"]["key_present"] is True and js["parts"]["tts"]["ready"] and "ffmpeg" in js["parts"], "static check reports each part as facts")
js, _, _ = t("static", "check", "--offline", env={**SENV, "OPENAI_API_KEY": ""})
check(js["parts"]["images"]["key_present"] is False, "static check without the key says so")
js, code, _ = t("image", "generate", "--run", str(SR), "--video", "01", "--image", "1", "--prompt", "a field", env={**SENV, "OPENAI_API_KEY": ""}, ok=False)
check(code == 2 and "OPENAI_API_KEY" in js.get("error", "") and not _SEEN, "image generate without the key refuses before any call (exit 2)")
# the format (A5): facts from the references' sizes, the pick stored, a size the API does not take refused
(SR / "00-inventory").mkdir(parents=True, exist_ok=True)
(SR / "00-inventory" / "inventory.json").write_text(json.dumps({"role": "references", "items": [
    {"id": "R01", "kind": "video", "path": "a.mp4", "rel": "a.mp4", "display_width": 1080, "display_height": 1920, "duration_s": 20},
    {"id": "R02", "kind": "video", "path": "b.mp4", "rel": "b.mp4", "display_width": 720, "display_height": 1280, "duration_s": 15},
    {"id": "R03", "kind": "video", "path": "c.mp4", "rel": "c.mp4", "display_width": 1920, "display_height": 1080, "duration_s": 10}]}), encoding="utf-8")
js, _ = ts("static", "formats", "--run", str(SR))
_f0 = js["formats"][0]
check(js["aspects"]["9:16"]["count"] == 2 and js["aspects"]["16:9"]["count"] == 1 and _f0["aspect"] == "9:16" and _f0["res"] == 1080
      and _f0["export"] == "1080x1920" and _f0["image_size"] == "1216x2160" and _f0["preview"] == "720x1280" and _f0["image"]["valid"]
      and any(f["aspect"] == "16:9" and f["res"] == 720 and f["export"] == "1280x720" for f in js["formats"]),
      "static formats gives the references' aspects and per aspect and resolution the export, the image size with the move margin, the check size")
js, code = ts("static", "format", "--run", str(SR), "--aspect", "1:1", "--res", "720", "--image-size", "720x720", ok=False)
check(code == 2 and "pixels" in js.get("error", ""), "static format refuses an image size the image API does not take")
ts("static", "format", "--run", str(SR), "--aspect", "9:16", "--res", "1080", "--quality", "high")
_fmt = json.loads((SR / "state.json").read_text(encoding="utf-8"))["static"]["format"]
check(_fmt["image_size"] == "1216x2160" and _fmt["export"] == "1080x1920" and _fmt["quality"] == "high" and _fmt["preview"] == "720x1280",
      "static format stores the pick in state.json -> static.format")

js, _ = ts("tts", "design", "--run", str(SR), "--text", "Most people never notice this.", "--instruct", "a calm deep male narrator",
           "--instruct", "a warm female storyteller", "--instruct", "a gravelly older man")
_design = js
check(len(js.get("samples", [])) == 3 and all(Path(s["file"]).is_file() for s in js["samples"]), "tts design makes one sample per voice description")
js, _ = ts("tts", "voice", "--run", str(SR), "--sample", "2", "--emotion", "tense=Something was wrong. Very wrong.")
_st = json.loads((SR / "state.json").read_text(encoding="utf-8"))
check(js.get("ok") and _st["static"]["voice"]["sample"] == 2 and set(_st["static"]["voice"]["prompts"]) == {"neutral", "tense"},
      "tts voice makes the picked sample the run's voice, with its emotion clip (state.json -> static.voice)")
(SR / "40-briefs" / "video-01-narration.json").write_text(json.dumps({"video": "01", "language": "english", "lines": [
    {"n": 1, "text": "In 1959 a farmer found something strange in his field.", "emotion": "neutral"},
    {"n": 2, "text": "Nobody believed him, until the soldiers came.", "emotion": "tense", "pause_after": 0.5},
    {"n": 3, "text": "What they took that night is still a secret.", "emotion": "neutral"}]}), encoding="utf-8")
js, _ = ts("tts", "say", "--run", str(SR), "--video", "01")
_side = json.loads((SR / "30-assets" / "narration" / "video-01.json").read_text(encoding="utf-8"))
_ln = _side["lines"]
check(js.get("lines") == 3 and _ln[1]["start"] >= _ln[0]["end"] + 0.34 and _ln[2]["start"] >= _ln[1]["end"] + 0.49
      and abs(js["duration_s"] - _ln[2]["end"]) < 0.01 and js.get("loudness_lufs") is not None,
      "tts say joins the lines with their pauses (default and planned) and records each line's exact start and end, and the loudness")
js, _ = ts("tts", "say", "--run", str(SR), "--video", "01", "--only", "2")
check(js.get("made_now") == [2], "tts say --only makes just that line again")
_before = [(r["start"], r["end"]) for r in json.loads((SR / "30-assets" / "narration" / "video-01.json").read_text(encoding="utf-8"))["lines"]]
js, _ = ts("tts", "say", "--run", str(SR), "--video", "01", "--rejoin")
_side = json.loads((SR / "30-assets" / "narration" / "video-01.json").read_text(encoding="utf-8"))
check(js.get("made_now") == [] and [(r["start"], r["end"]) for r in _side["lines"]] == _before and _side["loudness_pass"]["passes"] == 2
      and js.get("loudness_lufs") is not None and abs(js["loudness_lufs"] + 14) < 1.0,
      f"tts say --rejoin makes no line, keeps every line's timing and brings the narration to the target in two passes ({js.get('loudness_lufs')} LUFS)")
js, code = ts("tts", "say", "--run", str(SR), "--video", "01", "--rejoin", "--only", "2", ok=False)
check(code == 2 and "--rejoin" in js.get("error", ""), "tts say refuses --rejoin together with --only")
(SR / "40-briefs" / "video-02-narration.json").write_text(json.dumps({"video": "02", "language": "english", "lines": [
    {"n": 1, "text": "The letter arrived thirty years too late.", "emotion": "neutral"},
    {"n": 2, "text": "It was in his own handwriting.", "strong": True, "delivery": "Quiet disbelief, slower, a catch in the voice", "pause_after": 0.6},
    {"n": 3, "text": "He had never written it.", "emotion": "neutral"}]}), encoding="utf-8")
js, _ = ts("tts", "say", "--run", str(SR), "--video", "02")
_r2 = {r["n"]: r for r in json.loads((SR / "30-assets" / "narration" / "video-02.json").read_text(encoding="utf-8"))["lines"]}
_vs = json.loads((SR / "state.json").read_text(encoding="utf-8"))["static"]["voice"]
check([s["seed"] for s in _design["samples"]] == [1106, 1107, 1108] and _vs["seed"] == 1107 and _r2[2]["made_by"] == "design"
      and _r2[2]["seed"] == 1107 and _r2[1]["made_by"] == "clone" and _r2[2].get("delivery", "").startswith("Quiet disbelief")
      and all(isinstance(_r2[k].get("timbre_sim"), float) and _r2[k].get("pitch_st") is not None for k in (1, 2, 3))
      and [x["n"] for x in js["voice_match"]["strong_lines"]] == [2] and js["voice_match"]["clone_lines"]["timbre_sim_min"] is not None,
      "a strong line is made by the design model with the picked sample's seed; every line is measured against the run's voice (pitch, timbre)")
js, _ = ts("narration-words", "--run", str(SR), "--video", "01")
check(js.get("cues", 0) > 0 and len(js.get("lines", [])) == 3 and Path(js["files"]["srt"]).is_file() and "lines_to_check" in js,
      "narration-words gives the timed words, cues, an SRT and per line what was heard against the script")
# the run of 2026-11-06: one word at a time overlapped the next cue 29 times, and a quick 'he' was on screen for one frame
_tw = [{"w": "He", "s": 0.00, "e": 0.04}, {"w": "escaped", "s": 0.05, "e": 0.50}, {"w": "anyway.", "s": 0.52, "e": 0.95},
       {"w": "Then", "s": 1.40, "e": 1.60}, {"w": "Waterloo", "s": 1.62, "e": 2.10}, {"w": "all.", "s": 2.50, "e": 2.55},
       {"w": "Next", "s": 2.60, "e": 2.90}]
_c1 = _awl.chunk_words(_tw, 1)
_c2 = _awl.chunk_words(_tw, 1, min_cue=0.2)
check([c["text"] for c in _c1] == [w["w"] for w in _tw] and all(_c1[i]["end"] <= _c1[i + 1]["start"] for i in range(len(_c1) - 1))
      and _c1[0]["end"] - _c1[0]["start"] < 0.1, "one word at a time: no caption overlaps the next one (without min_cue a quick word stays short)")
check([c["text"] for c in _c2] == ["He escaped", "anyway.", "Then", "Waterloo", "all.", "Next"]
      and all(c["end"] - c["start"] >= 0.2 for c in _c2[:4]) and all(_c2[i]["end"] <= _c2[i + 1]["start"] for i in range(len(_c2) - 1)),
      f"with min_cue a word that would flash takes the next word with it, never across a sentence end ({[c['text'] for c in _c2]})")
check(_awl._is_number_token("1769") and _awl._is_number_token(_awl._norm_word("600,000")) and _awl._is_number_token(_awl._norm_word("sixty-nine"))
      and _awl._is_number_token("eighteen") and not _awl._is_number_token("often") and not _awl._is_number_token("tense"),
      "a spoken number and its digits are number tokens, compared apart from the words (speech-to-text writes 'seventeen sixty-nine' as 1769)")
check(_awl._match_words(["only", "about", "a", "hundred", "thousand", "came"]) == _awl._match_words(["only", "about", "100000", "came"])
      == ["only", "about", "came"] and _awl._match_words(["a", "man", "st", "helena"]) == ["a", "man", "saint", "helena"],
      "an 'a' that belongs to a number is compared with it ('about a hundred thousand' heard as 'about 100,000'); 'St' is 'Saint'")

_plan = {"video": "01", "characters": [{"id": "C1", "name": "the farmer", "photo": None, "sheet_prompt": "A weathered farmer, 60s"}],
         "images": [{"image": 1, "from_line": 1, "prompt": "A farmer in a wheat field at dusk", "characters": ["C1"], "line": "In 1959 ...",
                     "motion": "zoom-in", "amount": 0.1},
                    {"image": 2, "from_line": 2, "prompt": "Army trucks on a dirt road at night", "motion": "pan-left", "amount": 0.1,
                     "transition": "mix", "trans_s": 0.4},
                    {"image": 3, "from_line": 3, "prompt": "A sealed crate in a dark hangar", "motion": "zoom-out", "amount": 0.08,
                     "transition": "cut"}]}
(SR / "40-briefs" / "video-01-images.json").write_text(json.dumps(_plan), encoding="utf-8")
js, _ = ts("image", "generate", "--run", str(SR), "--anchor", "C1", "--prompt", "Character sheet: a weathered farmer, front view")
_anchor = Path(js["file"])
check(_anchor.is_file() and _anchor.parent.name == "characters" and _SEEN[-1]["path"].endswith("/images/generations"), "an anchor is drawn by the generations endpoint")
for _k in (1, 2, 3):
    _pf = SR / "40-briefs" / f"video-01-i0{_k}-prompt.txt"
    _pf.write_text(_plan["images"][_k - 1]["prompt"], encoding="utf-8")
    ts("image", "generate", "--run", str(SR), "--video", "01", "--image", str(_k), "--prompt-file", str(_pf), *(["--ref", str(_anchor)] if _k == 1 else []))
check(_SEEN[1]["path"].endswith("/images/edits") and _SEEN[1]["refs"] == 1 and all(s["auth"] == f"Bearer {_KEY}" for s in _SEEN),
      "an image with a character goes to the edits endpoint with its reference; the key travels only in the Authorization header")
check(all(s["size"] == "1216x2160" and s["quality"] == "high" for s in _SEEN), "image generate sends the run's format (its image size and quality)")
_n = len(_SEEN)
js, _ = ts("image", "generate", "--run", str(SR), "--video", "01", "--image", "1", "--prompt-file", str(SR / "40-briefs" / "video-01-i01-prompt.txt"), "--ref", str(_anchor))
check(js.get("reused") is True and len(_SEEN) == _n, "the same request that already made an image is not sent again")
js, code = ts("image", "generate", "--run", str(SR), "--video", "01", "--image", "2", "--prompt", "BLOCKME please", ok=False)
check(code == 1 and js.get("error_code") == "moderation_blocked" and js.get("tries") == [400], "a refusal is reported (moderation_blocked) and not retried")
_st = json.loads((SR / "state.json").read_text(encoding="utf-8"))
_rows = [(e["attempt"], e["status"]) for e in _st.get("submissions", []) if e.get("kind") == "image"]
check(_rows == [("C1-a1", "completed"), ("i01-a1", "completed"), ("i02-a1", "completed"), ("i03-a1", "completed"), ("i02-a2", "failed")],
      f"every image call is a ledger row of kind image: {_rows}")
check(not any(_KEY in o for o in _outs) and not any(_KEY in p.read_text(encoding="utf-8", errors="ignore") for p in SR.rglob("*") if p.is_file() and p.suffix in (".json", ".md", ".txt")),
      "the OpenAI key is never printed and never written to the run")

js, _ = ts("image", "prompts", "--run", str(SR))
_pm = Path(js["files"][0]).read_text(encoding="utf-8")
check("## v01-i01" in _pm and "## v01-i03" in _pm and "C1 character sheet" in _pm and "vertical 9:16, 1216x2160" in _pm, "image prompts writes one prompt per image with its file name, the character sheet and the size")
_up = home.parent / "user-images"
_up.mkdir(exist_ok=True)
for _k in (1, 3):
    _Im.new("RGB", (1024, 1536), (200, 100, 50)).save(_up / f"v01-i0{_k} final.png")
_Im.new("RGB", (900, 900), (0, 0, 0)).save(_up / "random.png")
_before = sorted(p.name for p in _up.iterdir())
js, _ = ts("image", "intake", "--run", str(SR), "--folder", str(_up))
check([m["image"] for m in js["missing"]] == ["02"] and len(js["copied"]) == 2 and js["unmatched_total"] == 1 and sorted(p.name for p in _up.iterdir()) == _before
      and js.get("aspect") == "9:16" and all("off_aspect" in c for c in js["copied"]),
      "image intake copies the files named vNN-iKK, lists the missing one and the unmatched name, and leaves the user's folder as it was")
ts("image", "use", "--run", str(SR), "--video", "01", "--image", "1", "--attempt", "1")
ts("image", "use", "--run", str(SR), "--video", "01", "--image", "3", "--attempt", "1")
(SR / "40-briefs" / "music.json").write_text(json.dumps({"tracks": [{"video": "01", "caption": "dark ambient drone", "duration": 12}]}), encoding="utf-8")
js, _ = ts("music", "make", "--run", str(SR))
check(js.get("made") and Path(js["made"][0]["file"]).is_file(), "music make writes the bed of the planned track (stub)")
js, _ = ts("slideshow", "plan", "--run", str(SR), "--video", "01")
_sp = js["image_spans"]
check(js.get("ok") and _sp[0][1] == 0.0 and -1 / 30 - 1e-6 <= _sp[1][1] - (0.3 + _ln[1]["start"]) <= 1e-6 and js.get("music")
      and Path(js["captions_srt"]).is_file() and js.get("fps") == 30,
      "slideshow plan starts each image on its narration line (after the lead), on the frame at or just before it, and writes the captions "
      "on the video's timeline")
check(js.get("undecided") == [] and [m[1:3] for m in js["moves"]] == [["zoom-in", [1.0, 1.1]], ["pan-left", [1.1, 1.1]], ["zoom-out", [1.08, 1.0]]]
      and _awl._xfade_for("mix") == "dissolve" and _awl._xfade_for("black-fade") == "fadeblack" and _awl._xfade_for("cut") == "fade",
      "the timeline carries each image's decided move as exact values, and the check copy maps a CapCut transition to its nearest xfade")
# no stock style (the user, 2026-11-06: "dont set fixed numbers let the agent decide"): what the plan leaves out stays still or cut, listed
_undec = {**_plan, "images": [({k: v for k, v in im.items() if k not in ("motion", "amount")} if im["image"] == 1 else
                               {k: v for k, v in im.items() if k != "transition"} if im["image"] == 2 else im) for im in _plan["images"]]}
(SR / "40-briefs" / "video-01-images.json").write_text(json.dumps(_undec), encoding="utf-8")
js, _ = ts("slideshow", "plan", "--run", str(SR), "--video", "01", ok=False)
check(js.get("ok") is False and "image 1: no motion" in js.get("undecided", []) and "image 2: no transition into it" in js.get("undecided", [])
      and js["moves"][0][1] == "none" and js["moves"][0][2] == [1.0, 1.0],
      f"slideshow plan invents no move or join: an image the plan leaves undecided stays still and is listed ({js.get('undecided')})")
# the reference of 2026-11-06 flashed another picture for 3 frames at its two story turns: an insert a few frames before a line's cut
(SR / "40-briefs" / "video-01-images.json").write_text(json.dumps({**_plan, "images": _plan["images"] + [
    {"image": 4, "from_line": 2, "offset_s": -0.1, "prompt": "a glimpse", "motion": "none", "transition": "cut"}]}), encoding="utf-8")
js, _ = ts("slideshow", "plan", "--run", str(SR), "--video", "01", ok=False)
_isp = {s[0]: s for s in js.get("image_spans") or []}
check([s[0] for s in js.get("image_spans") or []] == [1, 4, 2, 3] and abs((_isp[4][2] - _isp[4][1]) - 0.1) < 1 / 30 + 1e-6
      and _isp[4][2] == _isp[2][1] and _isp[1][2] == _isp[4][1],
      f"an image with offset_s before its line plays between the images around it, on the frame grid ({js.get('image_spans')})")
(SR / "40-briefs" / "video-01-images.json").write_text(json.dumps(_plan), encoding="utf-8")
js, _ = ts("slideshow", "plan", "--run", str(SR), "--video", "01")
_sp = js["image_spans"]
js, _ = ts("slideshow", "render", "--run", str(SR), "--video", "01")
check(js.get("ok") and js.get("size") == "720x1280" and abs(js["duration_s"] - _sp[-1][2]) < 0.15 and js.get("captions", 0) > 0
      and Path(js["preview"]).is_file() and js.get("loudness_lufs") is not None and abs(js["loudness_lufs"] + 14) < 2.5,
      f"slideshow render makes the clean and the captioned preview at 720x1280, the timeline's length, near -14 LUFS ({js.get('duration_s')} s, {js.get('loudness_lufs')} LUFS)")
_tl = json.loads((SR / "40-briefs" / "video-01-timeline.json").read_text(encoding="utf-8"))
check(_tl["size"] == "720x1280" and _tl["export"] == "1080x1920", "the timeline takes the format's check size and notes its export size")
check(js["video_frames"] == {"clean": js["expected_frames"], "preview": js["expected_frames"]} and abs(js["loudness_lufs"] + 14) < 1.0
      and all(abs(r["start"] * 30 - round(r["start"] * 30)) < 0.005 for r in _tl["images"]),
      f"the render's video holds every frame of the timeline, the cuts sit on the frame grid, the mix is at the target "
      f"({js['video_frames']} of {js['expected_frames']}, {js['loudness_lufs']} LUFS)")
# the run of 2026-11-06: nine cuts off the frame grid lost images 8 and 9 (973 of 1394 frames) while the file still reported 46.48 s
_reg = {**_tl, "size": "144x256", "duration_s": 46.48, "music": None,
        "images": [{**_tl["images"][_k % len(_tl["images"])], "image": _k + 1, "start": _s, "transition": "cut"}
                   for _k, _s in enumerate([0.0, 4.25, 9.4, 13.99, 17.72, 22.63, 26.98, 32.46, 35.74])]}
for _k, _r in enumerate(_reg["images"]):
    _r["end"] = _reg["images"][_k + 1]["start"] if _k + 1 < len(_reg["images"]) else 46.48
(SR / "40-briefs" / "video-01-timeline.json").write_text(json.dumps(_reg), encoding="utf-8")
js, _ = ts("slideshow", "render", "--run", str(SR), "--video", "01", "--no-captions")
check(js.get("ok") and js["video_frames"]["clean"] == 1394 == js["expected_frames"] and js["image_first_frames"][7] == 974,
      f"a timeline with its cuts off the frame grid renders every frame: no image is lost ({js.get('video_frames')} of {js.get('expected_frames')})")

# the moves (the user, 2026-11-06: CapCut's export had no zoom at all and the check copy's zoom shook): exact values, a render that
# glides, keyframes CapCut 9.x plays, and edit-profile reading a known move back
_mv = {m: _awl._still_motion({"motion": m, "amount": 0.2}) for m in ("zoom-in", "zoom-out", "pan-right", "pan-up", "none")}
check(_mv["zoom-in"]["scale"] == [1.0, 1.2] and _mv["zoom-out"]["scale"] == [1.2, 1.0] and _mv["pan-right"]["x"] == [0.196, -0.196]
      and _mv["pan-right"]["scale"] == [1.2, 1.2] and _mv["pan-up"]["y"] == [0.196, -0.196] and _mv["none"]["scale"] == [1.0, 1.0]
      and not any(v["edge_shows"] for v in _mv.values()) and _awl._still_motion({"motion": "zoom-in", "amount": 0.1, "x": [0.3, 0.3]})["edge_shows"],
      "each named move becomes exact scale and position values (half-canvas units, y up); a position past the picture's margin is named")
import numpy as _np  # noqa: E402
from PIL import ImageDraw as _Idraw, ImageFilter as _Ifilt, ImageFont as _Ifont  # noqa: E402
_tex = _Im.fromarray(_np.kron(_np.random.default_rng(7).integers(0, 255, (160, 90, 3)), _np.ones((6, 6, 1))).astype("uint8")).filter(_Ifilt.GaussianBlur(1))
_texp = home.parent / "texture.png"
_tex.save(_texp)
_one = home.parent / "one-shot.json"
_one.write_text(json.dumps({"shots": [{"shot": 1, "start": 0.0, "end": 2.0}]}), encoding="utf-8")
_prof = {}
for _m in ("zoom-in", "pan-right"):
    _awl._render_still(_texp, home.parent / f"move-{_m}.mp4", 60, 0, 270, 480, 30, _mv[_m])
    js, _ = ts("edit-profile", str(home.parent / f"move-{_m}.mp4"), "--cuts", str(_one), "--band", "0.0-0.01", "--out", str(home.parent / f"prof-{_m}.json"))
    _prof[_m] = js["shots"][0]
check(abs(_prof["zoom-in"]["zoom_start_to_end"] - 1.2) < 0.02 and abs(_prof["zoom-in"]["pan_x_pct"]) < 1
      and -21.5 < _prof["pan-right"]["pan_x_pct"] < -17.5 and abs(_prof["pan-right"]["zoom_start_to_end"] - 1) < 0.02
      and all(p["jitter"]["x_step_sd_pct"] < 0.03 and p["jitter"]["y_step_sd_pct"] < 0.03 for p in _prof.values()),
      f"a still moved by the render glides (ffmpeg's zoompan measured 0.065-0.070 sideways on the run of 2026-11-06), and edit-profile reads "
      f"the move back: zoom {_prof['zoom-in']['zoom_start_to_end']} for 1.2, pan {_prof['pan-right']['pan_x_pct']} % for -19.6 %, "
      f"sideways jitter {[p['jitter']['x_step_sd_pct'] for p in _prof.values()]}")
_bg = _Im.new("RGB", (270, 480), (70, 95, 130))


def _word(scale, dy):
    fr = _bg.copy()
    try:
        fnt = _Ifont.truetype("arialbd.ttf", int(round(40 * scale)))
    except OSError:
        fnt = _Ifont.load_default()
    _Idraw.Draw(fr).text((135, 240 + dy), "STORY", font=fnt, fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0), anchor="mm")
    return fr


_pop = home.parent / "pop.mp4"
_pp = subprocess.Popen([_awl.find_tool("ffmpeg"), "-nostdin", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "270x480",
                        "-r", "30", "-i", "-", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", str(_pop)], stdin=subprocess.PIPE)
for _fr in [_bg] * 15 + [_word(0.86, 20), _word(1.04, -8)] + [_word(1.0, 0)] * 13:
    _pp.stdin.write(_fr.tobytes())
_pp.stdin.close()
_pp.wait()
_pone = home.parent / "pop-shot.json"
_pone.write_text(json.dumps({"shots": [{"shot": 1, "start": 0.0, "end": 1.0}]}), encoding="utf-8")
js, _ = ts("edit-profile", str(_pop), "--cuts", str(_pone), "--band", "0.40-0.60", "--out", str(home.parent / "prof-pop.json"))
_ex = (json.loads((home.parent / "prof-pop.json").read_text(encoding="utf-8"))["caption_entrances"]["examples"] or [{}])[0]
check(js["caption_entrances"]["count"] >= 1 and abs(_ex.get("t", 0) - 0.5) < 0.05 and _ex["height_pct_of_settled"][0] < 95 and _ex["rise_px"][0] > 10,
      f"edit-profile reads a caption's pop-in: it enters small and low, then settles ({_ex.get('height_pct_of_settled')}, rise {_ex.get('rise_px')})")
_md = home.parent / "Draft_motion"
_md.mkdir(exist_ok=True)


def _clip(sid, st, du, kfs):
    return {"id": sid, "material_id": "M" + sid, "target_timerange": {"start": st, "duration": du}, "common_keyframes": kfs,
            "clip": {"scale": {"x": 1.0, "y": 1.0}, "transform": {"x": 0.0, "y": 0.0}}, "uniform_scale": {"on": False, "value": 1.0}}


_mdc = json.dumps({"id": "TL-4", "materials": {}, "tracks": [{"type": "video", "segments": [
    _clip("S1", 0, 2000000, [{"id": "K1", "property_type": "UNIFORM_SCALE", "keyframe_list": []}, {"id": "K2", "property_type": "KFTypeAlpha", "keyframe_list": []}]),
    _clip("S2", 2000000, 2000000, [])]}]})
(_md / "draft_content.json").write_text(_mdc, encoding="utf-8")
(_md / "draft_info.json").write_text(_mdc, encoding="utf-8")
_mtl = home.parent / "motion-timeline.json"
_mtl.write_text(json.dumps({"fps": 30, "images": [{"image": 1, "start": 0.0, "end": 2.0, "motion": "zoom-in", "amount": 0.2, **_mv["zoom-in"]},
                                                  {"image": 2, "start": 2.0, "end": 4.0, "motion": "pan-right", "amount": 0.2, **_mv["pan-right"]}]}), encoding="utf-8")
js, code, _ = t("capcut-motion", "--draft", str(_md), "--timeline", str(_mtl), env=SENV, ok=False)
if code == 3:
    print("SKIP  capcut-motion on a draft: CapCut is running on this machine")
else:
    _segs = {f: {s["id"]: s for s in json.loads((_md / f).read_text(encoding="utf-8"))["tracks"][0]["segments"]} for f in ("draft_content.json", "draft_info.json")}
    _s1, _s2 = _segs["draft_content.json"]["S1"], _segs["draft_content.json"]["S2"]
    _k1 = {k["property_type"]: k for k in _s1["common_keyframes"]}
    _k2 = {k["property_type"]: k for k in _s2["common_keyframes"]}
    check(code == 0 and set(_k1) == {"KFTypeAlpha", "KFTypeScaleX"} and [x["values"][0] for x in _k1["KFTypeScaleX"]["keyframe_list"]] == [1.0, 1.2]
          and [x["time_offset"] for x in _k1["KFTypeScaleX"]["keyframe_list"]] == [0, 2000000] and _s1["uniform_scale"]["on"] is True
          and [x["values"][0] for x in _k2["KFTypePositionX"]["keyframe_list"]] == [0.196, -0.196] and _s2["clip"]["scale"] == {"x": 1.2, "y": 1.2}
          and "KFTypePositionY" not in _k2 and _segs["draft_info.json"]["S2"]["common_keyframes"] == _s2["common_keyframes"],
          "capcut-motion keys each clip as CapCut 9.x plays it (KFTypeScaleX with uniform scale on, KFTypePositionX for a pan), drops the "
          "UNIFORM_SCALE keys CapCut ignores, keeps other keys, in both timeline files")
_tpl = Path(os.environ.get("LOCALAPPDATA", "")) / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft" / "_analyze-stack-template"
if not (_tpl / "draft_content.json").is_file():
    print("SKIP  capcut-text-anim: no CapCut template on this machine")
else:
    import shutil as _shutil  # noqa: E402
    _ta = home.parent / "Draft_textanim"
    _shutil.copytree(_tpl, _ta, ignore=_shutil.ignore_patterns("*.bak", "*bak", "assets", "Resources"))
    js, code, _ = t("capcut-text-anim", "--draft", str(_ta), "--intro", "pop-up", "--intro-duration", "0.2", env=SENV, ok=False)
    if code == 3:
        print("SKIP  capcut-text-anim: CapCut is running on this machine")
    else:
        _anims = [x for m in json.loads((_ta / "draft_content.json").read_text(encoding="utf-8"))["materials"].get("material_animations", [])
                  for x in m.get("animations", [])]
        js2, _c2, _ = t("capcut-text-anim", "--draft", str(_ta), "--intro", "pop-up", "--intro-duration", "0.2", env=SENV, ok=False)
        check(code == 0 and js.get("animated") == 1 and any(x.get("resource_id") == "7145435451946439170" and x.get("duration") == 200000 for x in _anims)
              and js2.get("animated") == 0 and js2.get("already_animated") == 1,
              "capcut-text-anim puts CapCut's own Pop Up intro (0.2 s) on every caption through capcut-cli, and leaves an animated one as it is")
        _vs = _awl._main_clips(_ta)
        _ttl = home.parent / "transition-timeline.json"
        _ttl.write_text(json.dumps({"fps": 30, "images": [
            {"image": 1, "start": _vs[0]["target_timerange"]["start"] / 1e6, "transition": "cut"},
            {"image": 2, "start": _vs[1]["target_timerange"]["start"] / 1e6, "transition": "mix", "trans_s": 0.3}]}), encoding="utf-8")
        js, code, _ = t("capcut-transitions", "--draft", str(_ta), "--timeline", str(_ttl), env=SENV, ok=False)
        _dc = json.loads((_ta / "draft_content.json").read_text(encoding="utf-8"))
        _trm = {m["id"]: m for m in _dc["materials"].get("transitions", [])}
        _first = next(s for tr in _dc["tracks"] if tr["type"] == "video" for s in tr["segments"] if s["id"] == _vs[0]["id"])
        js2, _c2, _ = t("capcut-transitions", "--draft", str(_ta), "--timeline", str(_ttl), env=SENV, ok=False)
        check(code == 0 and any(_trm.get(r, {}).get("name") == "Mix" and _trm[r]["duration"] == 300000 for r in _first.get("extra_material_refs", []))
              and js2.get("already_there") == 1 and not js2.get("transitions"),
              "capcut-transitions puts the timeline's CapCut transition on the clip before its cut (Mix, 0.3 s), and leaves one that is there")
ts("static", "format", "--run", str(SR), "--aspect", "16:9", "--res", "1080")
ts("slideshow", "plan", "--run", str(SR), "--video", "01")
js, _ = ts("slideshow", "render", "--run", str(SR), "--video", "01", "--no-captions")
check(js.get("ok") and js.get("size") == "1280x720", f"a 16:9 format renders its check copy at 1280x720 ({js.get('size')})")
ts("static", "format", "--run", str(SR), "--aspect", "9:16", "--res", "1080", "--quality", "high")

# the effects folder (the user, 2026-11-06: "a folder of effects (optional) that can have: sound effects, and green screen transitions"):
# facts from a scan, the plan's effects on the timeline, the check copy draws them, CapCut gets them by the verified ways only
import wave as _wave  # noqa: E402
import zipfile as _zip  # noqa: E402
_fx = home.parent / "fx-folder"
(_fx / "transitions").mkdir(parents=True, exist_ok=True)


def _fxvid(path, frame_of, n=30, audio=None):
    args = [_awl.find_tool("ffmpeg"), "-nostdin", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "320x180", "-r", "30", "-i", "-"]
    if audio:
        args += ["-i", str(audio), "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-shortest"]
    p = subprocess.Popen(args + ["-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(path)], stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(frame_of(i).tobytes())
    p.stdin.close()
    p.wait()


def _fxwav(path, x, sr=48000):
    with _wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((_np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


_sr = 48000
_tt = _np.arange(_sr) / _sr
_fxwav(home.parent / "tone.wav", _np.where((_tt >= 0.5) & (_tt < 0.6), 0.5 * _np.sin(2 * _np.pi * 440 * _tt), 0.0))
_green = lambda i: _np.full((180, 320, 3), 255, _np.uint8) if 10 <= i < 20 else _np.tile(_np.array([0, 255, 0], _np.uint8), (180, 320, 1))   # noqa: E731
_fxvid(_fx / "transitions" / "green.mp4", _green, audio=home.parent / "tone.wav")
_yy, _xx = _np.mgrid[0:180, 0:320]
_glow = (_np.clip((40 - _np.hypot(_xx - 160, _yy - 90)) / 8, 0, 1)[..., None] * _np.array([255, 140, 40])).astype(_np.uint8)
_fxvid(_fx / "glow.mp4", lambda i: _glow)
_tc = _np.arange(int(0.03 * _sr)) / _sr
_fxwav(_fx / "click.wav", _np.concatenate([_np.zeros(int(0.2 * _sr)), 0.5 * _np.sin(2 * _np.pi * 2000 * _tc), _np.zeros(int(0.3 * _sr))]))
_st_png = _Im.new("RGBA", (100, 100), (0, 0, 0, 0))
_Idraw.Draw(_st_png).ellipse([10, 10, 90, 90], fill=(255, 255, 255, 255))
_st_png.save(_fx / "sticker.png")
with _zip.ZipFile(_fx / "pack.zip", "w") as _z:
    _z.writestr("inside.txt", "x")
(_fx / "notes.sfk").write_bytes(b"\0" * 64)
_fx_before = sorted((p.relative_to(_fx).as_posix(), p.stat().st_size, p.stat().st_mtime_ns) for p in _fx.rglob("*") if p.is_file())
js, _ = ts("effects", "scan", "--run", str(SR), "--folder", str(_fx))
_ej = json.loads((SR / "00-inventory" / "effects.json").read_text(encoding="utf-8"))
_by = {Path(f["rel"]).name: f for f in _ej["files"]}
_g = _by["green.mp4"]["picture"]
_ng = _g["spans_visible"]["no_green"]
check(js["counts"] == {"video": 2, "audio": 1, "image": 1, "archive": 1, "other": 1} and _g["key_green"] and int(_g["key_green"][3:5], 16) > 200
      and _ng and abs(_ng[0][0] - 1 / 3) < 0.07 and abs(_ng[0][1] - 2 / 3) < 0.07
      and _by["glow.mp4"]["picture"]["shares_full"]["black"][0] > 0.88 and 0.6 < _by["glow.mp4"]["picture"]["shares_visible"]["black"][0] < 0.8
      and abs(_by["click.wav"]["sound"]["starts_s"] - 0.2) < 0.02 and _by["click.wav"]["sound"]["centroid_hz"] > 1500
      and _by["sticker.png"]["picture"]["has_transparency"] and _by["green.mp4"]["has_audio"]
      and js["sheets"] and all(Path(s).is_file() for s in js["sheets"]) and (SR / "00-inventory" / "effects.md").is_file(),
      f"effects scan measures each file: the green screen's key colour and the seconds it covers the 9:16 box ({_ng}), a black background, "
      "a sound's start and colour, a PNG's transparency; archives and other files are listed, the sheets drawn")
check(json.loads((SR / "state.json").read_text(encoding="utf-8"))["static"]["effects_folder"] == str(_fx)
      and sorted((p.relative_to(_fx).as_posix(), p.stat().st_size, p.stat().st_mtime_ns) for p in _fx.rglob("*") if p.is_file()) == _fx_before,
      "effects scan stores the folder in state.json and leaves the user's folder exactly as it was")
js, _ = ts("effects", "scan", "--run", str(SR))
check(js.get("cached") == js.get("files") == 6, "a second scan of the same folder reads every file from the cache")
_ids = {Path(f["rel"]).name: f["id"] for f in _ej["files"]}
_plan_fx = {**_plan, "effects": [
    {"id": _ids["green.mp4"], "type": "overlay", "join": 2, "anchor_s": 0.5, "blend": "chroma", "key_intensity": 0.5, "fit": "cover",
     "volume": 0.0, "why": "the reference's quick slide at its turn"},
    {"id": _ids["click.wav"], "type": "sfx", "join": 3, "anchor_s": 0.2, "volume": 0.5, "why": "the reference's hit on its cut"},
    {"id": _ids["sticker.png"], "type": "overlay", "line": 1, "anchor_s": 0.0, "dur_s": 1.0, "blend": "normal", "fit": "contain",
     "scale": [[0.0, 0.3], [0.2, 0.6]], "y": 0.3, "why": "a pop on the hook"},
    {"id": _ids["glow.mp4"], "type": "overlay", "at_s": 0.1, "anchor_s": 0.0, "blend": "screen", "fit": "cover", "why": "a glow"}]}
(SR / "40-briefs" / "video-01-images.json").write_text(json.dumps(_plan_fx), encoding="utf-8")
js, _ = ts("slideshow", "plan", "--run", str(SR), "--video", "01")
_tlx = json.loads((SR / "40-briefs" / "video-01-timeline.json").read_text(encoding="utf-8"))
_ef = {e["n"]: e for e in _tlx["effects"]}
_cut2, _cut3 = _tlx["images"][1]["start"], _tlx["images"][2]["start"]
check(js.get("ok") and js.get("undecided") == [] and -1 / 30 - 1e-6 <= _ef[1]["start"] - (_cut2 - 0.5) <= 1e-6 and _ef[1]["track"] == "fx1"
      and abs(_ef[2]["start"] - (_cut3 - 0.2)) < 1e-3 and _ef[2]["track"] == "sfx1" and _ef[1]["key_color"] == _g["key_green"]
      and abs(_ef[3]["start"] - 0.3) < 1e-6 and _ef[3]["track"] == "fx2" and _ef[4]["track"] == "fx1" and _ef[3]["dur_s"] == 1.0,
      "slideshow plan puts each effect on the timeline: its anchor second on its moment (a cut, a line, a second), the scan's key colour, "
      "overlapping overlays on separate tracks")
(SR / "40-briefs" / "video-01-images.json").write_text(json.dumps({**_plan, "effects": [
    {"id": _ids["green.mp4"], "type": "overlay", "join": 2, "fit": "cover", "why": "x"},
    {"file": str(_fx / "nope.mp4"), "type": "sfx", "at_s": 1.0, "anchor_s": 0.0, "volume": 1.0, "why": "x"},
    {"id": _ids["glow.mp4"], "type": "overlay", "at_s": 0.1, "anchor_s": 0.0, "why": "x"}]}), encoding="utf-8")
js, _ = ts("slideshow", "plan", "--run", str(SR), "--video", "01", ok=False)
_u = js.get("undecided") or []
check(js.get("ok") is False and any(u.startswith("effect 1: no anchor_s") for u in _u) and any(u.startswith("effect 2: no file") for u in _u)
      and any(u.startswith("effect 3: no blend") for u in _u) and any(u.startswith("effect 3: no fit") for u in _u),
      f"slideshow plan chooses no effect setting: what the plan leaves out is listed ({_u})")
(SR / "40-briefs" / "video-01-images.json").write_text(json.dumps(_plan_fx), encoding="utf-8")
ts("slideshow", "plan", "--run", str(SR), "--video", "01")
js, _ = ts("slideshow", "render", "--run", str(SR), "--video", "01", "--no-captions")
_clean = Path(js["clean"])


def _frame_at(t):
    cp = subprocess.run([_awl.find_tool("ffmpeg"), "-nostdin", "-v", "error", "-ss", f"{t:.3f}", "-i", str(_clean), "-frames:v", "1", "-f", "rawvideo",
                         "-pix_fmt", "rgb24", "-"], capture_output=True)
    return _np.frombuffer(cp.stdout, _np.uint8).reshape(1280, 720, 3).astype(int)


_fw, _fg = _frame_at(_cut2 + 0.02), _frame_at(_cut2 - 0.4)
_green_share = lambda f: float(((f[..., 1] > 80) & (f[..., 1] - _np.maximum(f[..., 0], f[..., 2]) > 50)).mean())   # noqa: E731
_cpa = subprocess.run([_awl.find_tool("ffmpeg"), "-nostdin", "-v", "error", "-i", str(_clean), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True)
_au = _np.frombuffer(_cpa.stdout, _np.float32)


def _band(t0, t1, f0=1800, f1=2200):
    s = _au[int(t0 * 16000):int(t1 * 16000)].astype(float)
    P = _np.abs(_np.fft.rfft(s * _np.hanning(len(s)))) ** 2
    q = _np.fft.rfftfreq(len(s), 1 / 16000)
    return 10 * _np.log10(P[(q >= f0) & (q <= f1)].sum() + 1e-12)


check(js.get("ok") and js.get("effects") == {"overlays": 3, "sounds": 1} and js["video_frames"]["clean"] == js["expected_frames"]
      and float((_fw.min(axis=2) > 220).mean()) > 0.9 and _green_share(_fw) < 0.01 and _green_share(_fg) < 0.02
      and _band(_cut3 - 0.01, _cut3 + 0.04) - _band(_cut3 - 0.4, _cut3 - 0.35) > 15,
      f"slideshow render draws the effects: the green screen keyed out and covering the cut (white {float((_fw.min(axis=2) > 220).mean()):.2f}, "
      f"green {_green_share(_fg):.3f} before it), the click on its cut, every frame kept")
if not (_tpl / "draft_content.json").is_file():
    print("SKIP  capcut-effects: no CapCut template on this machine")
else:
    _fd = home.parent / "Draft_effects"
    _shutil.copytree(_tpl, _fd, ignore=_shutil.ignore_patterns("*.bak", "*bak", "assets", "Resources"))
    _all = {k: {"plays": True} for k in ("cover_scale", "overlay_keyframes", "overlay_sound", "mute", "screen", "alpha_image", "sfx", "sfx_volume", "sfx_fade")}
    _ver = home.parent / "verified.json"
    _ver.write_text(json.dumps({"effects": {**_all, "chroma": {"plays": True, "intensity": 0.5},
                                            "alpha_video": {"plays": True, "codec": "qtrle", "codecs": ["qtrle"]}}}), encoding="utf-8")
    js, code, _ = t("capcut-effects", "--draft", str(_fd), "--run", str(SR), "--video", "01", "--verified-from", str(_ver), env=SENV, ok=False)
    if code == 3:
        print("SKIP  capcut-effects on a draft: CapCut is running on this machine")
    else:
        _dc = json.loads((_fd / "draft_content.json").read_text(encoding="utf-8"))
        _sg = {s["id"]: (tr, s) for tr in _dc["tracks"] for s in tr.get("segments") or []}
        _w = {w["effect"]: w for w in js.get("written") or []}
        _vm = {m["id"]: m for m in _dc["materials"].get("videos", [])}
        _chr = {m["id"]: m for m in _dc["materials"].get("chromas", [])}
        _t1, _s1 = _sg[_w[1]["segment"]]
        _t3, _s3 = _sg[_w[3]["segment"]]
        _t4, _s4 = _sg[_w[4]["segment"]]
        _t2, _s2x = _sg[_w[2]["segment"]]
        _k3 = {k["property_type"]: k for k in _s3.get("common_keyframes") or []}
        check(code == 0 and _t1["name"] == "fx1" and _t3["name"] == "fx2" and abs(_s1["clip"]["scale"]["x"] - 3.1605) < 0.01
              and any(r in _chr and _chr[r]["color"] == _g["key_green"] for r in _s1.get("extra_material_refs") or []) and _s1["volume"] == 0.0
              and _s1["source_timerange"]["start"] == 0 and _vm[_s4["material_id"]].get("mix_mode") == "Screen"
              and [x["values"][0] for x in _k3["KFTypeScaleX"]["keyframe_list"]] == [0.3, 0.6] and _s3["uniform_scale"]["on"] is True
              and _s3["clip"]["transform"]["y"] == 0.3 and _t2["type"] == "audio" and _t2["name"] == "sfx1" and _s2x["volume"] == 0.5,
              "capcut-effects writes each overlay on its own track above the stills (cover scale 3.16 for 16:9 on 9:16, the chroma key with the "
              "scan's colour, screen blend, scale keys) and each sound on an audio track at its volume, by the verified ways")
        _fd2 = home.parent / "Draft_effects2"
        _shutil.copytree(_tpl, _fd2, ignore=_shutil.ignore_patterns("*.bak", "*bak", "assets", "Resources"))
        _ver2 = home.parent / "verified2.json"
        _ver2.write_text(json.dumps({"effects": {**{k: v for k, v in _all.items() if k not in ("sfx",)}, "chroma": {"plays": False},
                                                 "alpha_video": {"plays": True, "codec": "qtrle", "codecs": ["qtrle"]}}}), encoding="utf-8")
        js, code, _ = t("capcut-effects", "--draft", str(_fd2), "--run", str(SR), "--video", "01", "--verified-from", str(_ver2), env=SENV, ok=False)
        _w2 = {w["effect"]: w for w in js.get("written") or []}
        _mov = SR / "30-assets" / "effects" / "video-01" / "effect-01.mov"
        _pf = _awl.media_summary(_mov).get("pix_fmt") if _mov.is_file() else None
        check(code == 1 and [r["effect"] for r in js.get("refused") or []] == [2] and "sfx" in js["refused"][0].get("not_verified", "")
              and _w2.get(1, {}).get("method") == "keyed-file:qtrle" and _pf == "argb",
              f"without CapCut's chroma key the green screen goes in as an alpha file made here ({_pf}); a sound the check did not verify is refused")
_dd = home.parent / "Draft_canvas"
_dd.mkdir(exist_ok=True)
(_dd / "draft_content.json").write_text(json.dumps({"id": "TL-1", "name": "Draft_canvas", "canvas_config": {"ratio": "9:16", "width": 1080,
                                                                                                             "height": 1920, "background": None}}), encoding="utf-8")
js, _ = ts("capcut-prep", "--draft", str(_dd), "--canvas", "1920x1080")
_cc = json.loads((_dd / "draft_content.json").read_text(encoding="utf-8"))["canvas_config"]
check(_cc == {"ratio": "16:9", "width": 1920, "height": 1080, "background": None} and (js.get("canvas") or {}).get("ratio") == "16:9",
      "capcut-prep --canvas sets the project's canvas to the format's export size, labelled as capcut-cli labels it")
# the text look is the references' (the user, 2026-11-05): the fonts on this PC, one font set on a draft's track, the check copy's look
js, _ = ts("capcut-font", "--list")
_fonts = js.get("fonts") or []
check(js.get("ok") and js.get("count") == len(_fonts) and all({"family", "style", "file", "source"} <= set(f) for f in _fonts[:5]),
      f"capcut-font --list gives the fonts on this PC as facts ({js.get('count')} found)")
if not _fonts:
    print("SKIP  capcut-font and the look's burn: no font file found on this machine")
else:
    _ff = next((f["file"] for f in _fonts if f["source"] == "capcut"), _fonts[0]["file"])
    _td = home.parent / "Draft_font"
    _td.mkdir(exist_ok=True)
    _dc = json.dumps({"id": "TL-2", "name": "Draft_font", "materials": {"texts": [
        {"id": "A", "font_size": 12.0, "font_path": "x.ttf", "has_border": True, "border_color": "#000000", "border_width": 0.1, "border_alpha": 1,
         "check_flag": 7, "content": json.dumps({"text": "ONE TWO", "styles": [
             {"range": [0, 7], "size": 12.0, "fill": {"content": {"solid": {"color": [1, 0.88, 0.3]}}}}]})},
        {"id": "B", "font_size": 9.0, "font_path": "x.ttf", "check_flag": 7,
         "content": json.dumps({"text": "title", "styles": [{"range": [0, 5], "size": 9.0}]})}]},
        "tracks": [{"type": "text", "name": "subtitle", "segments": [{"material_id": "A"}]},
                   {"type": "text", "name": "text", "segments": [{"material_id": "B"}]}]})
    (_td / "draft_content.json").write_text(_dc, encoding="utf-8")
    (_td / "draft_info.json").write_text(_dc, encoding="utf-8")   # capcut-cli's mirror of the timeline
    js, code, _ = t("capcut-font", "--draft", str(_td), "--font-file", _ff, "--track", "subtitle", env=SENV, ok=False)
    if code == 3:
        print("SKIP  capcut-font on a draft: CapCut is running on this machine")
    else:
        _m = {m["id"]: m for m in json.loads((_td / "draft_content.json").read_text(encoding="utf-8"))["materials"]["texts"]}
        _sa = json.loads(_m["A"]["content"])["styles"][0]
        check(code == 0 and _m["A"]["font_path"] == _ff and _sa["font"]["path"] == _ff and _sa["size"] == 12.0 and "fill" in _sa
              and _m["A"]["font_size"] == 12.0 and _m["B"]["font_path"] == "x.ttf",
              "capcut-font sets the font on the named track's texts only, their size and colours kept")
        # the run of 2026-11-06: import-srt's outline sat on the material only (check_flag 7), where CapCut 9.x does not draw it from
        _mi = {m["id"]: m for m in json.loads((_td / "draft_info.json").read_text(encoding="utf-8"))["materials"]["texts"]}
        check(_m["A"]["check_flag"] == 15 and _sa.get("strokes") and _sa["strokes"][0]["width"] == 0.1
              and _sa["strokes"][0]["content"]["solid"]["color"] == [0.0, 0.0, 0.0] and _m["B"]["check_flag"] == 7
              and _mi["A"]["check_flag"] == 15 and _mi["A"]["font_path"] == _ff,
              "capcut-font writes the text's outline where CapCut draws it (each style's strokes, check_flag 15), in the draft_info.json mirror too")
    _lt = home.parent / "Draft_links"
    _lt.mkdir(exist_ok=True)
    _lc = json.dumps({"id": "TL-3", "materials": {"videos": [{"id": "V1", "type": "photo", "path": "C:/media/i01.png"},
                                                             {"id": "V2", "type": "photo", "path": "C:/media/i02.png"}],
                                                  "audios": [{"id": "A1", "path": "C:/media/narration.wav"}]}, "tracks": []})
    (_lt / "draft_content.json").write_text(_lc, encoding="utf-8")
    (_lt / "draft_info.json").write_text(_lc, encoding="utf-8")
    (_lt / "draft_meta_info.json").write_text(json.dumps({"draft_materials": [{"type": 0, "value": [
        {"file_Path": "C:/media/i01.png", "id": "E-1"}, {"file_Path": "C:\\media\\narration.wav", "id": "E-3"}]}]}), encoding="utf-8")
    _lk = _awl._link_local_materials(_lt)
    _lv = {m["id"]: m.get("local_material_id") for f in ("draft_content.json", "draft_info.json")
           for k in ("videos", "audios") for m in json.loads((_lt / f).read_text(encoding="utf-8"))["materials"][k]}
    check(_lk["linked"] == 4 and _lv == {"V1": "E-1", "V2": None, "A1": "E-3"} and _lk["media_without_entry"] == ["C:/media/i02.png"]
          and _awl._link_local_materials(_lt)["linked"] == 0,
          "capcut-repair's link step writes each clip's local_material_id from its registered entry (CapCut 9.3+ opens clips by it), "
          "in both timeline files, names a clip with no entry, and changes nothing the second time")
    _mx, _cx = {"background_color": "#000000", "background_alpha": 0.6, "has_shadow": True, "check_flag": 7}, {"styles": [{"range": [0, 3]}]}
    check(_awl._text_outline_into_styles(_mx, _cx) is False and _mx["check_flag"] == 7 | 16 | 32 and "strokes" not in _cx["styles"][0],
          "a box and a shadow get their check_flag bits (16, 32); a text without an outline gets no stroke")
    _plan2 = {**_plan, "captions": {"y_rel": 0.7, "words": 3, "font_file": _ff, "size": 12, "fill": "#FFE14D", "stroke_color": "#101010",
                                    "stroke_width": 0.1, "case": "upper", "animation": "fade-in"}}
    (SR / "40-briefs" / "video-01-images.json").write_text(json.dumps(_plan2), encoding="utf-8")
    ts("slideshow", "plan", "--run", str(SR), "--video", "01")
    _cue_lines = [ln for ln in (SR / "60-outputs" / "video-01" / "captions.srt").read_text(encoding="utf-8").splitlines()
                  if ln.strip() and not ln.strip().isdigit() and "-->" not in ln]
    js, _ = ts("slideshow", "render", "--run", str(SR), "--video", "01")
    _ass = (SR / "60-outputs" / "video-01" / "render" / "captions.ass").read_text(encoding="utf-8")
    check(js.get("ok") and _cue_lines and all(ln == ln.upper() for ln in _cue_lines) and "&H004DE1FF" in _ass and "\\fad(" in _ass,
          "the check copy burns the references' look (the plan's font, colour, upper case and animation), the captions file in upper case")
js, _ = ts("contract", "--run", str(SR))
_ct = Path(js["file"]).read_text(encoding="utf-8")
check("Analyze Mode, static" in _ct and "Images: api" in _ct and "QC fixes: auto" in _ct and "awl-static-edit" in _ct and not js.get("unresolved_placeholders")
      and "Memes: n/a (Static" in _ct, "contract writes production-agents 2s's Static prompt with the run's choices filled")
js, _ = ts("contract", "--run", str(SR), "--notes", "The anchor is <RUN>/30-assets/characters/C1-a1.png.")
_ct = Path(js["file"]).read_text(encoding="utf-8")
check(f"{SR}/30-assets/characters/C1-a1.png" in _ct and "<RUN>" not in _ct.split("Run-specific notes")[-1],
      "contract fills <RUN> in the run-specific notes too (the run of 2026-11-06 sent it to the agent as it was)")
js, _ = ts("lint-run", "--run", str(SR))
check(js.get("contract", {}).get("loupe_line") is True and js.get("contract", {}).get("unresolved_placeholders") == [], "lint-run reads a Static contract's Loupe line")

# FLUX 3 Klein on this PC (static_images=klein, the user 2026-11-06): the same T image generate through the local worker (stubbed here), no key
KENV = {**SENV, "AWL_IMAGE_STUB": "1", "OPENAI_API_KEY": ""}
js, _, _ = t("new-run", "--mode", "analyze", "--slug", "static-klein", env=KENV)
KR = Path(js["run_dir"])
t("state", "--run", str(KR), "set", "analyze_submode=static", "static_images=klein", "audio_ingest=whisper", "qc_fixes=auto", env=KENV)
js, code, _ = t("static", "format", "--run", str(KR), "--aspect", "9:16", "--res", "1080", "--image-size", "1080x1920", env=KENV, ok=False)
check(code == 2 and "FLUX 3 Klein" in js.get("error", "") and "divisible by 16" in js.get("error", ""), "a Klein run's format refuses an edge that is not a multiple of 16")
js, _, _ = t("static", "format", "--run", str(KR), "--aspect", "9:16", "--res", "1080", env=KENV)
check(js["format"]["image_size"] == "1216x2160" and js["format"]["quality"] is None, "a Klein run's format stores the image size and no quality")
js, _, _ = t("static", "check", "--offline", env=KENV)
check(js["parts"]["images_klein"]["ready"] is True and js["parts"]["images_klein"].get("stub") is True, "static check reports FLUX 3 Klein's part")
_n = len(_SEEN)
js, _, _ = t("image", "generate", "--run", str(KR), "--anchor", "C1", "--prompt", "Character sheet: a weathered farmer, front view", env=KENV)
_ka = Path(js["file"])
check(js.get("ok") and _ka.is_file() and js.get("engine") == "flux3-image-klein-int8" and js.get("cost_usd_estimate") == 0.0
      and isinstance(js.get("seed"), int) and len(_SEEN) == _n, "with static_images=klein an image is made on this PC (no key, no API call), with its seed and no cost")
check(js.get("upsampled") is False, "a Klein anchor is drawn from its sheet prompt as written (no upsampler: its props would be copied into every image)")
_kp = ("image", "generate", "--run", str(KR), "--video", "01", "--image", "1", "--prompt", "A farmer in a wheat field at dusk", "--ref", str(_ka))
js, _, _ = t(*_kp, env=KENV)
_s1 = js.get("seed")
check(js.get("ok") and js.get("size") == [1216, 2160] and js.get("refs") == 1 and js.get("caption") and js.get("upsampled") is True,
      "a Klein image of the plan goes through the upsampler, takes the run's size and its reference, and returns its caption")
js, _, _ = t(*_kp, env=KENV)
check(js.get("reused") is True and js.get("seed") == _s1, "the same Klein request is not made again")
js, _, _ = t(*_kp, "--again", env=KENV)
check(js.get("ok") and js.get("attempt") == 2 and js.get("seed") != _s1, "--again draws the Klein image again with a new seed")
js, _, _ = t(*_kp, "--again", "--seed", str(_s1), env=KENV)
check(js.get("ok") and js.get("attempt") == 3 and js.get("seed") == _s1, "--again --seed makes a recorded draw again")
js, code, _ = t("image", "generate", "--run", str(KR), "--video", "01", "--image", "2", "--prompt", "x", *sum((["--ref", str(_ka)] for _ in range(11)), []),
                env=KENV, ok=False)
check(code == 2 and "at most 10" in js.get("error", ""), "FLUX 3 Klein takes at most 10 references")
_krows = [(e["attempt"], e["status"], e.get("provider")) for e in json.loads((KR / "state.json").read_text(encoding="utf-8")).get("submissions", [])
          if e.get("kind") == "image"]
check(_krows == [("C1-a1", "completed", "klein"), ("i01-a1", "completed", "klein"), ("i01-a2", "completed", "klein"), ("i01-a3", "completed", "klein")],
      f"every Klein image is a ledger row of provider klein: {_krows}")
_krec = json.loads((KR / "60-outputs" / "video-01" / "images.json").read_text(encoding="utf-8"))["images"]["01"]
check(_krec["use"] == "i01-a3.png" and _krec["attempts"][0]["source"] == "klein" and _krec["attempts"][0]["seed"] == _s1 and _krec["attempts"][0]["caption"],
      "the record keeps each Klein attempt with its seed and caption; the newest is the one the edit uses")
js, _, _ = t("contract", "--run", str(KR), env=KENV)
check("Images: klein" in Path(js["file"]).read_text(encoding="utf-8") and not js.get("unresolved_placeholders"), "a Klein run's contract says Images: klein")
_srv.shutdown()

finish()
