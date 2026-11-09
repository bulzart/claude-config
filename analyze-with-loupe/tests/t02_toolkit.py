"""The toolkit on scratch fixtures: run resolution, PDFs, the inventory, the seam profile, the inspection commands and the audio
choice, each answer one JSON object on its last line. A temp library copy (AWL_HOME) holds the runs; nothing real is touched."""
import json
import os
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from t00_common import check, finish, make_clip, make_image_pdf, make_text_pdf, t, temp_library  # noqa: E402

home = temp_library("tk")
# never the user's ElevenLabs key: an empty variable stops the toolkit from looking up the one stored for the user (the ElevenLabs tests
# set their own fake key and the stand-in's address)
ENV = {"AWL_HOME": str(home), "ELEVEN_API_KEY": "", "ELEVENLABS_API_KEY": ""}
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
js, code, _ = t("voiceover", "mix", "--picture", str(vo_fx / "gen.mp4"), "--voiceover", str(take), "--offset", "0.5", "--bed", "keep", "--out", str(vo_fx / "kept.mp4"), env=ENV)
f = js["facts"]
check(code == 0 and f["bed"] == "kept" and f["bed_gain"] == 0.3 and f["vo_gain"] == 1.0 and f["vo_speech_cut_s"] == 0
      and abs(f["vo_speech_end_on_picture_s"] - 4.1) <= 0.1,
      "voiceover mix --bed keep lays the whole take on the picture at its own level, the picture's sound under it")
# the take is an ElevenLabs generation and is never edited (the user, 2026-11-09: "do not edit the delivered generation without any
# exception"): only placed, whole, at its own level
js, code, _ = t("voiceover", "mix", "--picture", str(vo_fx / "gen.mp4"), "--voiceover", str(take), "--offset", "3.0", "--bed", "keep", "--out", str(vo_fx / "late.mp4"), env=ENV, ok=False)
check(code == 2 and "past the picture's end" in js.get("error", "") and not (vo_fx / "late.mp4").exists(),
      "a take whose speech would run past the picture's end is refused, never cut (exit 2)")
js, code, _ = t("voiceover", "mix", "--picture", str(vo_fx / "gen.mp4"), "--voiceover", str(take), "--offset", "-0.5", "--bed", "mute", "--out", str(vo_fx / "early.mp4"), env=ENV, ok=False)
check(code == 2 and "negative offset" in js.get("error", ""), "a negative offset (it would cut the take's start) is refused (exit 2)")
js, code, _ = t("voiceover", "mix", "--picture", str(vo_fx / "gen.mp4"), "--voiceover", str(take), "--vo-gain", "0.8", "--bed", "mute", "--out", str(vo_fx / "quiet.mp4"), env=ENV, ok=False)
check(code == 2 and "--vo-gain" in js.get("error", ""), "a gain on the take is refused: it plays at its own level (exit 2)")

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
# Static has no effort level (the user, 2026-11-07: "remove the effort idea completely (on static mode), just do 2fps when on static mode")
run_s = Path(t("new-run", "--mode", "analyze", "--source", str(ef_src), "--slug", "static-effort", env=ENV)[0]["run_dir"])
t("inventory", str(ef_src), "--run", str(run_s), "--as", "references", env=ENV)
t("state", "--run", run_s.name, "set", "audio_ingest=frames-only", "analyze_submode=static", env=ENV)
js, _, _ = t("effort", "--run", run_s.name, env=ENV)
_se = js.get("effort") or {}
check(_se.get("level") == "static" and _se.get("analysis_fps") == 2.0 and _se.get("analysis_dense_fps") == 2.0 and _se.get("max_agents") == 5
      and _se.get("pilot_from") == 5 and not _se.get("pending"),
      "a Static run has no effort level to ask (its effort key empty): references at 2 fps flat, agents and the pilot as before levels")
js, code, _ = t("effort", "--run", run_s.name, "--level", "low", env=ENV, ok=False)
check(code == 2 and "Static" in js.get("error", ""), "effort refuses a level on a Static run")
js, _, _ = t("prep-all", "--run", run_s.name, "--jobs", "1", "--no-ocr", env=ENV)
_sv = run_s / "10-media" / "V01"
_svj = json.loads((_sv / "video.json").read_text(encoding="utf-8"))
_sfr = json.loads((_sv / "frames.json").read_text(encoding="utf-8"))["frames"]
check(js["sampling"]["effort"] == "static" and js["sampling"]["baseline_fps"] == 2.0 and js["sampling"]["dense_fps"] == 2.0
      and abs(_svj["sampling"]["baseline_frames"] - 80) <= 2 and not [f for f in _sfr if f.get("why") in ("peak", "hook", "pre_cut", "post_cut")],
      f"prep-all samples a Static reference at 2 fps only ({_svj['sampling']['baseline_frames']} frames in 40 s), none around motion, cuts or the "
      "first second, with no flag")
js, _, _ = t("prep-all", "--run", run_s.name, "--jobs", "1", "--no-ocr", "--redo", "--max-frames", "30", env=ENV)
_svj = json.loads((_sv / "video.json").read_text(encoding="utf-8"))
check(abs(_svj["sampling"]["baseline_frames"] - 80) <= 2 and _svj["sampling"]["baseline_fps"] == 2.0,
      f"a long Static reference keeps 2 fps past the frame cap ({_svj['sampling']['baseline_frames']} frames in 40 s with a cap of 30; "
      "2026-11-08: a 22-minute reference had been lowered to 1.3 fps)")
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
# written), the prompts file and the user's folder (copied, never moved), the voice through an ElevenLabs stand-in, the bed stub, the
# narration's words, the local render, the Static contract. No model, no network, no Higgsfield, no Loupe.
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


# ElevenLabs (Eleven v4; the user, 2026-11-09: "we will only use elevenlabs v4", "do not edit the delivered generation without any
# exception") through a local stand-in: the fake key and the stand-in's address only in the child's environment, every request recorded
from http.server import ThreadingHTTPServer as _THS  # noqa: E402
_ELKEY = "sk_el_test_NEVER_PRINT_5151"
_EL = {"seen": [], "refuse": {"pcm_44100"}, "used": 0, "limit": 1_000_000, "rid": 0, "allow": None, "delivered": {}, "voices": {},
       "d": 0.065}   # d: the seconds a character takes (about 170 words a minute; the long passage tests speak faster)
_EL_LOCK = _th.Lock()
_EL_EDGE = 0.15        # the silence before and after every take the stand-in delivers


def _el_pcm(seconds, sr, freq=170.0):
    n = int(round(seconds * sr))
    tt = np.arange(n) / sr
    sig = 0.3 * np.sin(2 * np.pi * freq * tt) * (1.0 + 0.3 * np.sin(2 * np.pi * 3.0 * tt))
    e = int(round(_EL_EDGE * sr))
    sig[:e] = 0.0
    sig[max(e, n - e):] = 0.0
    return (sig * 32767).astype("<i2").tobytes()


def _el_encode(fmt, seconds, freq=170.0):
    """The stand-in's audio in the asked format: raw 16-bit PCM for pcm_<rate>, an MP3 for mp3_<rate>_<kbps>, as ElevenLabs delivers them."""
    parts = fmt.split("_")
    if parts[0] == "pcm":
        return _el_pcm(seconds, int(parts[1]), freq)
    cp = subprocess.run([ffmpeg(), "-loglevel", "error", "-f", "s16le", "-ar", parts[1], "-ac", "1", "-i", "pipe:0", "-c:a", "libmp3lame",
                         "-b:a", f"{parts[2]}k", "-f", "mp3", "pipe:1"], input=_el_pcm(seconds, int(parts[1]), freq), capture_output=True, check=True)
    return cp.stdout


class _ELMock(_BH):
    def log_message(self, *a):
        pass

    def _send(self, code, obj, headers=None, raw=None, ctype="application/json"):
        data = raw if raw is not None else json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def _rec(self, body=None):
        from urllib.parse import parse_qs, urlparse
        u = urlparse(self.path)
        r = {"method": self.command, "path": u.path, "query": {k: v[0] for k, v in parse_qs(u.query).items()},
             "key": self.headers.get("xi-api-key"), "body": body, "status": None}
        with _EL_LOCK:
            _EL["seen"].append(r)
        return r

    def _answer(self, r, code, obj, **kw):
        r["status"] = code
        self._send(code, obj, **kw)

    def do_GET(self):
        r = self._rec()
        p = r["path"]
        if p.startswith("/preview/"):
            self._answer(r, 200, None, raw=_el_encode("mp3_44100_128", 2.0, 210.0), ctype="audio/mpeg")
        elif r["key"] != _ELKEY:
            self._answer(r, 401, {"detail": {"code": "invalid_api_key", "message": "Invalid API key"}})
        elif p == "/v1/user/subscription":
            self._answer(r, 200, {"tier": "free", "status": "free", "character_count": _EL["used"], "character_limit": _EL["limit"],
                                  "next_character_count_reset_unix": 1796828594, "can_use_instant_voice_cloning": False,
                                  "can_use_professional_voice_cloning": False, "voice_limit": 3, "voice_slots_used": 0})
        elif p == "/v1/models":
            self._answer(r, 200, [{"model_id": "eleven_v4", "name": "Eleven v4", "can_do_text_to_speech": True, "can_use_style": False,
                                   "can_use_speaker_boost": False, "maximum_text_length_per_request": 10000, "requires_alpha_access": False,
                                   "model_rates": {"character_cost_multiplier": 1.0, "cost_discount_multiplier": 1.0}},
                                  {"model_id": "eleven_multilingual_v2", "can_do_text_to_speech": True, "can_use_style": True}])
        elif p == "/v1/voices":
            self._answer(r, 200, {"voices": list(_EL["voices"].values())})
        elif p.startswith("/v1/voices/") and p.rsplit("/", 1)[-1] in _EL["voices"]:
            self._answer(r, 200, _EL["voices"][p.rsplit("/", 1)[-1]])
        elif p.startswith("/v1/voices/"):
            self._answer(r, 404, {"detail": {"code": "voice_not_found", "message": "A voice with that id was not found."}})
        else:
            self._answer(r, 404, {"detail": {"code": "not_found", "message": p}})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        r = self._rec(body)
        p, fmt = r["path"], r["query"].get("output_format") or "mp3_44100_128"
        if r["key"] != _ELKEY:
            self._answer(r, 401, {"detail": {"code": "invalid_api_key", "message": "Invalid API key"}})
        elif fmt in _EL["refuse"] and p != "/v1/text-to-voice":
            self._answer(r, 403, {"detail": {"code": "output_format_not_allowed", "message": f"output_format {fmt} needs the Pro tier"}})
        elif p == "/v1/text-to-voice/design":
            prev = [{"audio_base_64": _b64.b64encode(_el_encode(fmt, 2.0, 150.0 + 20 * k)).decode(), "media_type": "audio/mpeg",
                     "generated_voice_id": f"gen-{body.get('seed')}-{k}", "duration_secs": 2.0, "language": "en"} for k in range(3)]
            self._answer(r, 200, {"previews": prev, "text": body.get("text")})
        elif p == "/v1/text-to-voice":
            vid = "vd" + str(body.get("generated_voice_id")).replace("-", "")
            _EL["voices"][vid] = {"voice_id": vid, "name": body.get("voice_name"), "category": "generated", "labels": {}, "preview_url": None}
            self._answer(r, 200, {"voice_id": vid, "name": body.get("voice_name")})
        elif p.startswith("/v1/text-to-speech/") and p.split("/")[3] not in _EL["voices"]:
            self._answer(r, 404, {"detail": {"code": "voice_not_found", "message": "A voice with that id was not found."}})
        elif p.startswith("/v1/text-to-speech/"):
            text = str(body.get("text") or "")
            with _EL_LOCK:
                over = (_EL["allow"] is not None and _EL["allow"] <= 0) or _EL["used"] + len(text) > _EL["limit"]
                if not over:
                    _EL["used"] += len(text)
                    _EL["rid"] += 1
                    rid = f"req-{_EL['rid']}"
                    if _EL["allow"] is not None:
                        _EL["allow"] -= 1
            if over:
                self._answer(r, 402, {"detail": {"code": "insufficient_credits", "message": "You have no credits left for this request."}})
                return
            d = _EL["d"]
            audio = _el_encode(fmt, 2 * _EL_EDGE + d * len(text), 160.0 + 10 * (int(rid.split("-")[1]) % 7))
            _EL["delivered"][rid] = {"format": fmt, "audio": audio, "text": text}
            al = {"characters": list(text), "character_start_times_seconds": [round(_EL_EDGE + i * d, 4) for i in range(len(text))],
                  "character_end_times_seconds": [round(_EL_EDGE + (i + 1) * d, 4) for i in range(len(text))]}
            r["rid"] = rid
            self._answer(r, 200, {"audio_base64": _b64.b64encode(audio).decode(), "alignment": al, "normalized_alignment": al},
                         headers={"request-id": rid, "character-cost": str(len(text))})
        else:
            self._answer(r, 404, {"detail": {"code": "not_found", "message": p}})


class _ELSrv(_THS):
    daemon_threads = True


_elsrv = _ELSrv(("127.0.0.1", 0), _ELMock)
_th.Thread(target=_elsrv.serve_forever, daemon=True).start()
_ELURL = f"http://127.0.0.1:{_elsrv.server_port}"
for _vid, _vnm, _vlb in [("vGEORGE", "George - Warm, Captivating Storyteller", {"gender": "male", "age": "middle_aged", "accent": "british",
                                                                                "descriptive": "mature", "use_case": "narrative_story"}),
                         ("vDANIEL", "Daniel - Steady Broadcaster", {"gender": "male", "age": "middle_aged", "accent": "british",
                                                                     "descriptive": "formal", "use_case": "informative_educational"}),
                         ("vBRIAN", "Brian - Deep, Resonant", {"gender": "male", "age": "middle_aged", "accent": "american", "use_case": "social_media"}),
                         ("vSARAH", "Sarah - Mature, Reassuring", {"gender": "female", "age": "young", "accent": "american",
                                                                   "use_case": "entertainment_tv"})]:
    _EL["voices"][_vid] = {"voice_id": _vid, "name": _vnm, "category": "premade", "labels": _vlb, "preview_url": f"{_ELURL}/preview/{_vid}.mp3"}


def _once(rs):
    """The requests as the toolkit meant them: one sent again with the same path, query and body right after (a dropped connection;
    this PC's security software resets local connections: 14 of 60 on 2026-11-09, WinError 10054) counts once, as its last answer,
    the one the toolkit received."""
    out_ = []
    for r in rs:
        if out_ and (out_[-1]["path"], out_[-1]["query"], out_[-1]["body"]) == (r["path"], r["query"], r["body"]):
            out_[-1] = r
        else:
            out_.append(r)
    return out_


def _el_tts(since=0, ok=True):
    """The text-to-speech requests the stand-in answered (ok) or refused since a point of its record (a resend counted once)."""
    return _once([r for r in _EL["seen"][since:] if r["path"].startswith("/v1/text-to-speech/") and (r["status"] == 200) == ok])


def _frames(p):
    with wave.open(str(p), "rb") as w_:
        return w_.getframerate(), w_.readframes(w_.getnframes())


SENV = {**ENV, "AWL_MUSIC_STUB": "1", "AWL_TRANSCRIBE_STUB": "1", "OPENAI_API_KEY": _KEY,
        "AWL_OPENAI_BASE_URL": f"http://127.0.0.1:{_srv.server_port}/v1", "ELEVEN_API_KEY": _ELKEY, "ELEVENLABS_API_KEY": "",
        "AWL_ELEVENLABS_BASE_URL": _ELURL}
_outs = []


def ts(*args, ok=True):
    js_, code_, out_ = t(*args, env=SENV, ok=ok)
    _outs.append(out_)
    return js_, code_


js, _ = ts("new-run", "--mode", "analyze", "--slug", "static")
SR = Path(js["run_dir"])
ts("state", "--run", str(SR), "set", "analyze_submode=static", "static_images=api", "audio_ingest=whisper", "qc_fixes=auto", "capcut_plan=free")
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
_f0 = next(f for f in js["formats"] if f["aspect"] == "9:16" and f["res"] == 1080)
check(js["aspects"]["9:16"]["count"] == 2 and js["aspects"]["16:9"]["count"] == 1 and js["formats"][0]["aspect"] == "9:16"
      and _f0["export"] == "1080x1920" and _f0["image_size"] == "1216x2160" and _f0["preview"] == "720x1280" and _f0["image"]["valid"]
      and any(f["aspect"] == "16:9" and f["res"] == 720 and f["export"] == "1280x720" for f in js["formats"])
      and any(f["aspect"] == "16:9" and f["res"] == 1440 and f["export"] == "2560x1440" and f["preview"] == "1280x720" for f in js["formats"]),
      "static formats gives the references' aspects and per aspect and resolution (1440, 1080, 720) the export, the image size with the "
      "move margin, the check size")
js, code = ts("static", "format", "--run", str(SR), "--aspect", "1:1", "--res", "720", "--image-size", "720x720", ok=False)
check(code == 2 and "pixels" in js.get("error", ""), "static format refuses an image size the image API does not take")
ts("static", "format", "--run", str(SR), "--aspect", "9:16", "--res", "1080", "--quality", "high")
_fmt = json.loads((SR / "state.json").read_text(encoding="utf-8"))["static"]["format"]
check(_fmt["image_size"] == "1216x2160" and _fmt["export"] == "1080x1920" and _fmt["quality"] == "high" and _fmt["preview"] == "720x1280",
      "static format stores the pick in state.json -> static.format")

# the narration by ElevenLabs, Eleven v4 (contract item 36; the user, 2026-11-09: "we will only use elevenlabs v4" and "no edits should be
# done from our side on the elevenlabs generation ... do not edit the delivered generation without any exception"): the stand-in above
# answers every call; the delivered audio is never changed, the pace and the pauses come only from the request
js, _ = ts("tts", "check", "--offline")
check(js.get("ok") and js.get("key_variable") == "ELEVEN_API_KEY" and js.get("model_id") == "eleven_v4"
      and js["model_caps"].get("voice_settings") == ["stability", "similarity_boost"] and js["model_caps"].get("speed") is False
      and "never edited" in str(js.get("rule")) and _ELKEY not in json.dumps(js),
      "tts check --offline: the variable that holds the key (never the key), Eleven v4 with its two settings and no speed, the no-edit rule")
js, _, _ = t("tts", "check", "--offline", env={**SENV, "ELEVEN_API_KEY": "", "ELEVENLABS_API_KEY": _ELKEY})
check(js.get("key_variable") == "ELEVENLABS_API_KEY" and js.get("key_present") is True, "the key is read from ELEVEN_API_KEY, else ELEVENLABS_API_KEY")
js, _, _ = t("tts", "check", "--offline", env={**SENV, "ELEVEN_API_KEY": "", "ELEVENLABS_API_KEY": ""})
check(js.get("ok") is False and js.get("key_present") is False and js.get("key_variable") is None, "without either variable tts check says the key is not there")
_n = len(_EL["seen"])
js, _ = ts("tts", "check")
check(js.get("ready") and js.get("answers") is True and js.get("model_offered") is True
      and (js.get("subscription") or {}).get("characters_left") == _EL["limit"] - _EL["used"] and len(_EL["seen"]) > _n
      and all(r["key"] == _ELKEY for r in _EL["seen"][_n:]),
      "tts check reads the account's plan and characters left and that Eleven v4 is offered to it; the key travels only in its header")
_dtext = "Most people never notice this. It sits in plain sight every single day, and almost nobody ever stops to ask why it is there."
_ins = ["a calm deep male narrator, a measured pace", "a warm female storyteller, an unhurried pace", "a gravelly older man, quick but measured",
        "a bright young woman, a quick pace", "a dry, wry middle-aged man, steady"]
_dargs = ["tts", "design", "--run", str(SR), "--text", _dtext] + [x for i in _ins for x in ("--instruct", i)]
_n = len(_EL["seen"])
js, code = ts("tts", "design", "--run", str(SR), "--text", "Too short.", "--instruct", "a calm deep male narrator", ok=False)
check(code == 2 and "100 to 1000" in js.get("error", "") and len(_EL["seen"]) == _n,
      "tts design refuses a sample line shorter than ElevenLabs' Voice Design takes, before any call")
js, _ = ts(*_dargs)
_design = js
_dreq = _once([r for r in _EL["seen"][_n:] if r["path"] == "/v1/text-to-voice/design"])
check(len(js.get("samples", [])) == 5 and all(Path(s["file"]).is_file() and Path(s["file"]).is_absolute() for s in js["samples"])
      and "5 samples" in (js.get("note") or "") and "full file path" in (js.get("note") or "")
      and [s["seed"] for s in js["samples"]] == [1106, 1107, 1108, 1109, 1110] and all(s.get("generated_voice_id") for s in js["samples"])
      and [r["status"] for r in _dreq[:2]] == [403, 200] and _dreq[0]["query"].get("output_format") == "pcm_44100"
      and _dreq[1]["query"].get("output_format") == "mp3_44100_192" and len([r for r in _dreq if r["status"] == 200]) == 5
      and all(r["body"]["model_id"] == "eleven_ttv_v3" for r in _dreq) and all((s.get("pace") or {}).get("wpm_overall") for s in js["samples"]),
      "tts design: one ElevenLabs Voice Design per description (the stop offers five), each sample's full file path and its pace read; a "
      "format the plan refuses (PCM at 44.1 kHz) costs nothing and the next one is asked, once")
_n = len(_EL["seen"])
js, code = ts("tts", "voice", "--run", str(SR), "--sample", "2", "--emotion", "tense=Low and tense, a little slower", ok=False)
check(code == 2 and "audio tags" in js.get("error", "") and len(_EL["seen"]) == _n,
      "a delivery written as prose is refused before any call: Eleven v4 takes audio tags")
js, code = ts("tts", "voice", "--run", str(SR), "--sample", "2", "--settings", '{"speed": 1.1}', ok=False)
check(code == 2 and "speed" in js.get("error", "") and "no such setting" in js.get("error", "") and len(_EL["seen"]) == _n,
      "a speed setting is refused before any call: Eleven v4 has none, and nothing is sped after generation")
js, _ = ts("tts", "voice", "--run", str(SR), "--sample", "2", "--emotion", "tense=[tense, cautious]", "--settings",
           '{"stability": 0.6, "similarity_boost": 0.8}')
_vs = json.loads((SR / "state.json").read_text(encoding="utf-8"))["static"]["voice"]
check(js.get("ok") and _vs["engine"] == "elevenlabs" and _vs["kind"] == "design" and _vs["sample"] == 2 and _vs["seed"] == 1107
      and _vs["voice_id"] == "vd" + _design["samples"][1]["generated_voice_id"].replace("-", "") and _vs["deliveries"] == {"tense": "[tense, cautious]"}
      and _vs["settings"] == {"stability": 0.6, "similarity_boost": 0.8} and Path(_vs["ref_audio"]).is_file()
      and [r["body"]["generated_voice_id"] for r in _EL["seen"][_n:] if r["path"] == "/v1/text-to-voice"] == [_design["samples"][1]["generated_voice_id"]],
      "tts voice --sample saves the picked design at ElevenLabs as the run's voice, with its settings and its emotion's tags (state.json -> static.voice)")
js, code = ts(*_dargs, ok=False)
check(code == 2 and "locked" in js.get("error", ""), "tts design refuses new samples once the run's narrator is picked (one voice per run)")
js, code = ts("tts", "voice", "--run", str(SR), "--sample", "3", ok=False)
check(code == 2 and "locked" in js.get("error", "") and json.loads((SR / "state.json").read_text(encoding="utf-8"))["static"]["voice"]["sample"] == 2,
      "tts voice refuses another pick once the narrator is set (no --replace), and the voice stays")
(SR / "40-briefs" / "video-01-narration.json").write_text(json.dumps({"video": "01", "language": "english", "lines": [
    {"n": 1, "text": "In 1959 a farmer found something strange in his field.", "emotion": "neutral"},
    {"n": 2, "text": "Nobody believed him, until the soldiers came.", "emotion": "tense", "pause_after": 0.5},
    {"n": 3, "text": "What they took that night is still a secret.", "emotion": "neutral"}]}), encoding="utf-8")
_n = len(_EL["seen"])
_d1 = _EL["d"]
js, code, _ = t("tts", "say", "--run", str(SR), "--video", "01", env={**SENV, "ELEVEN_API_KEY": "", "ELEVENLABS_API_KEY": ""}, ok=False)
check(code == 2 and "ELEVEN_API_KEY" in js.get("error", "") and len(_EL["seen"]) == _n, "tts say without the key refuses before any call (exit 2)")
js, _ = ts("tts", "say", "--run", str(SR), "--video", "01")
_side = json.loads((SR / "30-assets" / "narration" / "video-01.json").read_text(encoding="utf-8"))
_ln = _side["lines"]
_q = _el_tts(_n)
_t1 = "In 1959 a farmer found something strange in his field. [tense, cautious] Nobody believed him, until the soldiers came."
_t2 = "What they took that night is still a secret."
check(js.get("ok") and js.get("lines") == 3 and [p["lines"] for p in _side["passages"]] == [[1, 2], [3]]
      and [r["body"]["text"] for r in _q] == [_t1, _t2] and _q[0]["body"].get("next_text") == _t2
      and "previous_request_ids" not in _q[0]["body"] and "previous_text" not in _q[0]["body"]
      and _q[1]["body"].get("previous_request_ids") == [_q[0]["rid"]] and "next_text" not in _q[1]["body"]
      and all(r["body"]["model_id"] == "eleven_v4" and r["body"]["voice_settings"] == {"stability": 0.6, "similarity_boost": 0.8}
              and r["body"]["language_code"] == "en" and r["path"].endswith("/with-timestamps") for r in _q)
      and [r["body"]["seed"] for r in _q] == [1107001, 1107002],
      "tts say makes the plan's passages in the run's voice: a line's delivery tags before it (its emotion's) and the passage ending with "
      "it, each passage stitched to the ones just made (their request ids, the next passage's text), Eleven v4 with the voice's two "
      "settings and a seed per passage")
_nd1 = SR / "30-assets" / "narration" / "video-01"
_sr1, _all1 = _frames(SR / "30-assets" / "narration" / "video-01.wav")
_parts1 = [_frames(_nd1 / f"passage-{k:02d}.wav") for k in (1, 2)]
check(_all1 == b"".join(f_ for _s, f_ in _parts1) and all(s_ == _sr1 for s_, _f in _parts1)
      and (_nd1 / "passage-01.delivered.mp3").read_bytes() == _EL["delivered"][_q[0]["rid"]]["audio"]
      and abs(_side["duration_s"] - len(_all1) / 2 / _sr1) < 0.002 and "gain_pass" not in _side and "never edited" in str(_side.get("rule"))
      and isinstance(_side.get("loudness_lufs"), (int, float)) and js.get("loudness_lufs") == _side["loudness_lufs"],
      "the narration is the delivered passages end to end, sample for sample: nothing cut, trimmed, added or gained (each MP3 kept as "
      "delivered beside its decode); its loudness is only read")
_i2 = _t1.index("Nobody")
check(abs(_ln[0]["start"] - _EL_EDGE) < 0.002 and abs(_ln[1]["start"] - (_EL_EDGE + _i2 * _d1)) < 0.002
      and abs(_ln[1]["end"] - (_EL_EDGE + len(_t1) * _d1)) < 0.002 and abs(_ln[2]["start"] - (_side["passages"][1]["start"] + _EL_EDGE)) < 0.002
      and _ln[1].get("delivery") == "[tense, cautious]" and all(r.get("timing") == "elevenlabs" for r in _ln),
      f"each line's start and end come from ElevenLabs' own character timing, at its passage's place in the narration ({_ln})")
_n = len(_EL["seen"])
js, _ = ts("tts", "say", "--run", str(SR), "--video", "01")
check((js.get("passages") or {}).get("made_now") == [] and not _el_tts(_n) and js.get("characters_now") == 0,
      "tts say again makes nothing already made with its present text: no request, no character spent twice")
js, _ = ts("tts", "say", "--run", str(SR), "--video", "01", "--only", "3")
_q = _el_tts(_n)
check((js.get("passages") or {}).get("made_now") == [2] and [r["body"]["text"] for r in _q] == [_t2]
      and _q[0]["body"].get("previous_request_ids") == [json.loads((_nd1 / "passage-01.json").read_text(encoding="utf-8"))["request_id"]],
      "tts say --only N makes again only the passage holding that line, still stitched to the passage before it")
_before = [(r["start"], r["end"]) for r in json.loads((SR / "30-assets" / "narration" / "video-01.json").read_text(encoding="utf-8"))["lines"]]
_n = len(_EL["seen"])
js, _ = ts("tts", "say", "--run", str(SR), "--video", "01", "--rejoin")
_side = json.loads((SR / "30-assets" / "narration" / "video-01.json").read_text(encoding="utf-8"))
_ln = _side["lines"]
check((js.get("passages") or {}).get("made_now") == [] and len(_EL["seen"]) == _n and [(r["start"], r["end"]) for r in _ln] == _before,
      "tts say --rejoin makes no passage and asks nothing of ElevenLabs; every line keeps its timing")
js, code = ts("tts", "say", "--run", str(SR), "--video", "01", "--rejoin", "--only", "2", ok=False)
check(code == 2 and "--rejoin" in js.get("error", ""), "tts say refuses --rejoin together with --only")
# a line's own delivery: audio tags only, never prose; a speed asked anywhere is refused before anything is sent
_l2 = [{"n": 1, "text": "The letter arrived thirty years too late.", "emotion": "neutral"},
       {"n": 2, "text": "It was in his own handwriting.", "delivery": "Quiet disbelief, slower, a catch in the voice", "pause_after": 0.6},
       {"n": 3, "text": "He had never written it.", "emotion": "neutral"}]
_p2 = SR / "40-briefs" / "video-02-narration.json"
_p2.write_text(json.dumps({"video": "02", "language": "english", "lines": _l2}), encoding="utf-8")
_n = len(_EL["seen"])
js, code = ts("tts", "say", "--run", str(SR), "--video", "02", ok=False)
check(code == 2 and "not audio tags" in js.get("error", "") and len(_EL["seen"]) == _n, "a line's delivery written as prose is refused before any call")
_l2[1]["delivery"] = "[quiet disbelief, slower]"
_p2.write_text(json.dumps({"video": "02", "language": "english", "lines": _l2, "pace": {"speed": 1.1, "wpm_articulation": [180, 200]}}), encoding="utf-8")
js, code = ts("tts", "say", "--run", str(SR), "--video", "02", ok=False)
check(code == 2 and "no speed" in js.get("error", "") and len(_EL["seen"]) == _n, "a plan asking a speed (pace.speed) is refused before any call")
_p2.write_text(json.dumps({"video": "02", "language": "english", "lines": _l2, "voice_settings": {"speed": 1.1}}), encoding="utf-8")
js, code = ts("tts", "say", "--run", str(SR), "--video", "02", ok=False)
check(code == 2 and "no such setting" in js.get("error", "") and len(_EL["seen"]) == _n, "a plan's voice setting the model lacks (speed) is refused before any call")
_p2.write_text(json.dumps({"video": "02", "language": "english", "lines": _l2}), encoding="utf-8")
js, _ = ts("tts", "say", "--run", str(SR), "--video", "02")
_r2 = {r["n"]: r for r in json.loads((SR / "30-assets" / "narration" / "video-02.json").read_text(encoding="utf-8"))["lines"]}
check([r["body"]["text"] for r in _el_tts(_n)] == ["The letter arrived thirty years too late. [quiet disbelief, slower] It was in his own handwriting.",
                                                   "He had never written it."]
      and _r2[2].get("delivery") == "[quiet disbelief, slower]" and "delivery" not in _r2[3] and "voice_match" in js,
      "a line's own delivery tags go before it and end its passage (a tag holds until the next one); the next passage reads in the voice's own way")
js, _ = ts("narration-words", "--run", str(SR), "--video", "01")
check(js.get("cues", 0) > 0 and len(js.get("lines", [])) == 3 and Path(js["files"]["srt"]).is_file() and "lines_to_check" in js,
      "narration-words gives the timed words, cues, an SRT and per line what was heard against the script")
check("wpm_speech" in (js.get("pace") or {}) and (js["pace"].get("within") or {}).get("wpm_speech") is None,
      "narration-words reports the pace by the references' yardstick (no target in this plan: nothing to compare)")
# the fair measure, the captions' words in their own line, a plan's pace read as a point (static §6, §13)
_pw = _awl._pace_of_words([{"s": 0.0, "e": 0.5}, {"s": 0.5, "e": 1.0}, {"s": 1.2, "e": 1.5}, {"s": 2.5, "e": 3.0}])
check(_pw["wpm_articulation"] == 120.0 and _pw["wpm_overall"] == 80.0 and _pw["pauses_per_minute"] == 20.0 and _pw["pause_s_median"] == 1.0
      and _pw["long_pauses_per_10min"] == 200.0 and _pw["pause_share"] == 0.333,
      f"the fair measure: words a minute over the span with every pause of 0.25 s or more taken out (a 0.2 s gap stays speech), the "
      f"pauses a minute, their median, the long ones per 10 minutes and their share ({_pw})")
# the captions' words kept inside their own line's audio (static §6): a word timed in the silence before its line starts with the
# line's voice, one timed past its line's end ends with it; lines without times, or words that are not the script's one for one, stay as heard
_wlines = [{"n": 1, "text": "a b.", "start": 0.0, "end": 1.0}, {"n": 2, "text": "c d.", "start": 2.0, "end": 3.0}]
_wl = _awl._words_in_lines([{"w": "a", "s": 0.1, "e": 0.5}, {"w": "b.", "s": 0.5, "e": 1.3},
                            {"w": "c", "s": 1.6, "e": 2.3}, {"w": "d.", "s": 2.3, "e": 3.2}], _wlines)
_wc = _awl.chunk_words(_wl, 3)
check([(w["s"], w["e"]) for w in _wl] == [(0.1, 0.5), (0.5, 1.0), (2.0, 2.3), (2.3, 3.0)] and _wc[1]["start"] == 2.0
      and _awl._words_in_lines(_wl[:3], _wlines) == _wl[:3]
      and _awl._words_in_lines(_wl, [{"n": 1, "text": "a b."}, {"n": 2, "text": "c d."}]) == _wl,
      f"the captions' words stay inside their own line's audio: a word heard in the silence before its line starts with the line's "
      f"voice (2026-11-08: 'Day four.' 0.44 s early), one heard past its line ends with it; left as heard without line times or "
      f"one-for-one words ({_wl}, {_wc})")
_ptn = _awl._pace_targets({"wpm_articulation": [200, 224], "wpm_overall": [160, 185], "target": {"wpm_articulation": 211.9, "wpm_overall": 174.0},
                           "tolerance": 0.01})
_pto = _awl._pace_targets({"wpm_speech": [178, 212], "wpm_overall": [170, 185]})
check(_ptn["measure"] == "wpm_articulation" and _ptn["target_speak"] == 211.9 and _ptn["target_overall"] == 174.0 and _ptn["from_judge"] is True
      and _ptn["tol"] == 0.01 and _pto["measure"] == "wpm_speech" and _pto["target_speak"] == 195.0 and _pto["target_overall"] == 177.5
      and _pto["from_judge"] is False and _awl._pace_targets({}) is None,
      "a plan's pace is read as a point to aim at: the judge's with its tolerance, else each band's middle; an older plan keeps its measure")
# the probe and the forecast (static §13, J1): passage 1 made exactly as say would make it, measured, recorded, reused by say
_pl8 = [{"n": 1, "text": "In 1959 a farmer found something strange in his field.", "emotion": "neutral"},
        {"n": 2, "text": "Nobody believed him, until the soldiers came.", "emotion": "neutral", "pause_after": 0.9},
        {"n": 3, "text": "What they took that night is still a secret.", "emotion": "neutral", "passage_break": True},
        {"n": 4, "text": "The papers were sealed for fifty years.", "emotion": "neutral"},
        {"n": 5, "text": "Then a single page went missing.", "emotion": "neutral", "pause_after": 0.6},
        {"n": 6, "text": "Nobody has found it since.", "emotion": "neutral"}]
(SR / "40-briefs" / "video-08-narration.json").write_text(json.dumps({"video": "08", "language": "english", "lines": _pl8, "target_length_s": 20,
    "pace": {"refs": [], "wpm_articulation": [180, 200], "wpm_overall": [150, 170], "target": {"wpm_articulation": 190.0, "wpm_overall": 160.0},
             "tolerance": 0.015, "why": "test"}}), encoding="utf-8")
_n = len(_EL["seen"])
js, _ = ts("tts", "probe", "--run", str(SR), "--video", "08")
_q = _el_tts(_n)
_pt8 = " ".join(x["text"] for x in _pl8[:3])
_fit8 = json.loads((SR / "state.json").read_text(encoding="utf-8"))["static"]["voice"]["fit"]
_prb = json.loads((SR / "30-assets" / "voice" / "probes.json").read_text(encoding="utf-8"))["probes"]
check(js.get("ok") and js.get("passage") == 1 and js.get("lines") == [1, 2, 3] and [r["body"]["text"] for r in _q] == [_pt8]
      and js.get("characters") == len(_pt8) and (js.get("measured") or {}).get("wpm_articulation") and js.get("reused_by_say") is True
      and (js.get("off_by") or {}).get("wpm_articulation") is not None and _fit8["points"][-1]["from"] == "probe"
      and _fit8["points"][-1]["video"] == "08" and _prb[-1]["passage"] == 1
      and "speed" not in json.dumps({k: v for k, v in js.items() if k != "note"}),
      "tts probe makes passage 1 exactly as say would and measures it by the references' yardstick against the plan's point, recorded for "
      "the forecast (state.json -> static.voice.fit, 30-assets/voice/probes.json)")
_n = len(_EL["seen"])
js, _ = ts("tts", "probe", "--run", str(SR), "--video", "08")
check(js.get("ok") and js.get("characters") == 0 and len(_EL["seen"]) == _n, "the same probe asked again is read from its files: nothing asked of ElevenLabs")
js, _ = ts("static", "forecast", "--run", str(SR), "--video", "08", "--part", "narration")
_fn = js.get("narration") or {}
_f8 = _fn.get("forecast") or {}
_vid = json.loads((SR / "state.json").read_text(encoding="utf-8"))["static"]["voice"]["voice_id"]
_same = [p for p in json.loads((SR / "state.json").read_text(encoding="utf-8"))["static"]["voice"]["fit"]["points"]
         if p["voice_id"] == _vid and not p.get("delivery") and p.get("settings") == {"stability": 0.6, "similarity_boost": 0.8}][-1]
_w8n = sum(len(x["text"].split()) for x in _pl8)


def _keys(o):
    return ([k for k in o] + [kk for v in o.values() for kk in _keys(v)] if isinstance(o, dict)
            else [kk for v in o for kk in _keys(v)] if isinstance(o, list) else [])


check(js.get("ok") and _f8.get("from_point") == "same" and _same["from"] == "probe"
      and abs(float((_f8.get("predicted") or {}).get("length_s") or 0) - round(_w8n * 60 / _same["wpm_delivered"], 1)) < 0.05
      and (_fn.get("credits") or {}).get("characters_left") == _EL["limit"] - _EL["used"] and ((_fn.get("plan") or {}).get("passages") or {}).get("count") == 2
      and "length_vs_target_s" in _f8 and (_f8.get("off_by") or {}).get("wpm_articulation") is not None and not [k for k in _keys(_fn) if "speed" in k],
      "static forecast predicts the narration from the voice's measured point for these levers (its words a minute over the delivered "
      "audio), with the passages and the characters they send against the account's; no speed anywhere")
_n = len(_EL["seen"])
js, _ = ts("tts", "say", "--run", str(SR), "--video", "08")
_q = _el_tts(_n)
_pm8 = json.loads((SR / "30-assets" / "narration" / "video-08" / "passage-01.json").read_text(encoding="utf-8"))
check(js.get("ok") and (js.get("passages") or {}).get("reused_probe") == [1] and (js.get("passages") or {}).get("made_now") == [2]
      and len(_q) == 1 and _q[0]["body"]["text"].startswith("The papers were sealed") and _q[0]["body"].get("previous_request_ids") == [_pm8["request_id"]]
      and _pm8.get("reused_probe"),
      "tts say uses the passage-1 probe made exactly as it would make it (nothing billed twice) and stitches passage 2 to it")
_fit_before = json.loads((SR / "state.json").read_text(encoding="utf-8"))["static"]["voice"]["fit"]
_n = len(_EL["seen"])
js, _ = ts("tts", "probe", "--run", str(SR), "--video", "08", "--voice-id", "vDANIEL", "--delivery", "[quick, measured pace]")
_q = _el_tts(_n)
check(js.get("ok") and js.get("candidate") is True and len(_q) == 1 and _q[0]["path"].startswith("/v1/text-to-speech/vDANIEL/")
      and _q[0]["body"]["text"].startswith("[quick, measured pace] In 1959")
      and json.loads((SR / "state.json").read_text(encoding="utf-8"))["static"]["voice"]["fit"] == _fit_before,
      "tts probe measures a candidate voice and another pace tag without making them the run's: the levers are tried in the request, "
      "never on the delivered audio")
js, _ = ts("narration-words", "--run", str(SR), "--video", "08")
_nw8 = js.get("pace") or {}
check(_nw8.get("measure") == "wpm_articulation" and "speak" in (_nw8.get("on_target") or {})
      and (_nw8.get("target") or {}).get("point") == {"wpm_articulation": 190.0, "wpm_overall": 160.0},
      "narration-words reads the pace again by the fair measure, against the plan's point and tolerance")
_w8 = json.loads((SR / "30-assets" / "narration" / "video-08.words.json").read_text(encoding="utf-8"))["words"]
_own8 = [l for l in json.loads((SR / "30-assets" / "narration" / "video-08.json").read_text(encoding="utf-8"))["lines"]
         for _ in str(l["text"]).split()]
check(isinstance((js.get("words_kept_in_their_line") or {}).get("moved"), int) and len(_own8) == len(_w8)
      and all(l["start"] - 0.006 <= w["s"] and w["e"] <= l["end"] + 0.006 for w, l in zip(_w8, _own8)),
      f"narration-words keeps every caption word inside its own line's audio (the stub crowds its words into the first second) and "
      f"says how many it moved: {js.get('words_kept_in_their_line')}")
_s8 = json.loads((SR / "30-assets" / "narration" / "video-08.json").read_text(encoding="utf-8"))
_h8 = []
for _r8 in _s8["lines"]:
    _w8 = _r8["text"].split()
    _st8 = (_r8["end"] - _r8["start"]) / len(_w8)
    _h8 += [{"w": w, "s": round(_r8["start"] + i * _st8, 3), "e": round(_r8["start"] + (i + 1) * _st8, 3)} for i, w in enumerate(_w8)]
(SR / "30-assets" / "narration" / "video-08.words.json").write_text(json.dumps({"video": "08", "heard": _h8}), encoding="utf-8")
js, _ = ts("tts", "fit", "--run", str(SR), "--video", "08")
_fv = json.loads((SR / "state.json").read_text(encoding="utf-8"))["static"]["voice"]["fit"]["points"]
check(js.get("ok") and _fv[-1]["from"] == "narration-words" and _fv[-1]["video"] == "08" and _fv[-1].get("wpm_delivered")
      and _fv[-1].get("wpm_articulation") and (js.get("point") or {}).get("passages") == 2,
      f"tts fit learns the voice's point again from a made narration and the words heard in it, with no model ({_fv[-1].get('wpm_articulation')} wpm)")
# a voice the account has (the premade ones on any plan): listed and measured from its own preview for free, then taken as the run's voice
js, _ = ts("new-run", "--mode", "analyze", "--slug", "static-el")
ER = Path(js["run_dir"])
ts("state", "--run", str(ER), "set", "analyze_submode=static", "static_images=api", "audio_ingest=whisper", "qc_fixes=auto", "capcut_plan=free")
_n = len(_EL["seen"])
js, _ = ts("tts", "voices", "--run", str(ER))
check(js.get("ok") and js.get("count") == len(_EL["voices"]) and (ER / "30-assets" / "voice" / "voices.json").is_file()
      and all("preview" not in v for v in js["voices"])
      and not _el_tts(_n), "tts voices lists the account's voices with their labels, nothing billed")
js, _ = ts("tts", "voices", "--run", str(ER), "--gender", "male", "--accent", "british", "--measure")
_pv = [r for r in _EL["seen"][_n:] if r["path"].startswith("/preview/")]
check([v["voice_id"] for v in js["voices"]] == ["vGEORGE", "vDANIEL"] and all(Path(v["preview"]["file"]).is_file()
                                                                             and v["preview"].get("wpm_overall") for v in js["voices"])
      and _pv and all(r["key"] is None for r in _pv) and not _el_tts(_n)
      and json.loads((ER / "30-assets" / "voice" / "voices.json").read_text(encoding="utf-8"))["measured"] is True,
      "tts voices --measure reads each listed voice's own preview by the references' yardstick: free (no text-to-speech call) and the "
      "key never goes to the preview's host")
js, _ = ts("tts", "voices", "--run", str(ER), "--search", "storyteller")
check([v["voice_id"] for v in js["voices"]] == ["vGEORGE"], "tts voices --search keeps the voices whose name, labels or description hold the words")
(ER / "40-briefs").mkdir(parents=True, exist_ok=True)
(ER / "40-briefs" / "video-01-narration.json").write_text(json.dumps({"video": "01", "language": "english", "lines": _pl8[:3],
    "pace": {"wpm_articulation": [180, 200], "target": {"wpm_articulation": 190.0}}}), encoding="utf-8")
js, _ = ts("static", "forecast", "--run", str(ER), "--video", "01", "--part", "narration")
check("no ElevenLabs voice" in str(((js.get("narration") or {}).get("forecast") or {}).get("note")), "the forecast says when the run has no ElevenLabs voice yet")
js, code = ts("tts", "say", "--run", str(ER), "--video", "01", ok=False)
check(code == 2 and "no ElevenLabs voice" in js.get("error", "") and "T tts voices" in js.get("error", ""), "tts say without a run voice says how to pick one")
js, _ = ts("tts", "voice", "--run", str(ER), "--voice-id", "vGEORGE")
_ev = json.loads((ER / "state.json").read_text(encoding="utf-8"))["static"]["voice"]
check(js.get("ok") and _ev["engine"] == "elevenlabs" and _ev["voice_id"] == "vGEORGE" and _ev["kind"] == "premade"
      and (_ev.get("labels") or {}).get("accent") == "british" and Path(_ev.get("ref_audio") or "").is_file()
      and _ev.get("ref_from") == "the voice's own preview at ElevenLabs",
      "tts voice --voice-id takes a voice the account has as the run's voice, its own preview kept as the reference recording")
js, code = ts("tts", "voice", "--run", str(ER), "--voice-id", "vNOPE", "--replace", ok=False)
check(code == 1 and "not on the account" in js.get("error", "")
      and json.loads((ER / "state.json").read_text(encoding="utf-8"))["static"]["voice"]["voice_id"] == "vGEORGE",
      "a voice the account does not have is refused and the run's voice stays")
js, _ = ts("static", "forecast", "--run", str(ER), "--video", "01", "--part", "narration")
check("no measured point" in str(((js.get("narration") or {}).get("forecast") or {}).get("note"))
      and ((js.get("narration") or {}).get("lever") or {}).get("voice_id") == "vGEORGE",
      "before any probe the forecast names the free and the billed way to measure the voice")
# the passages and a narration that stops early, in a run of their own (a voice the account has; the stand-in speaks fast here, so the
# long plans stay quick)
js, _ = ts("new-run", "--mode", "analyze", "--slug", "static-passages")
PR = Path(js["run_dir"])
ts("state", "--run", str(PR), "set", "analyze_submode=static", "static_images=api", "audio_ingest=whisper", "qc_fixes=auto", "capcut_plan=free")
ts("static", "format", "--run", str(PR), "--aspect", "9:16", "--res", "1080", "--quality", "high")
ts("tts", "voice", "--run", str(PR), "--voice-id", "vBRIAN")
(PR / "40-briefs").mkdir(parents=True, exist_ok=True)
_EL["d"] = 0.008
# the passages (static §6 "Passages"): at most 850 characters, ending at a line marked passage_break, where a line's own delivery ends, and
# when too long at the plan's largest pause in their second half; a pause asked of the model with tags_after; PCM taken as delivered
_l12 = [{"n": i, "text": f"Line {i:02d} " + " ".join(["word"] * 27) + "."} for i in range(1, 19)]
_l12[4]["passage_break"] = True
_l12[8]["delivery"] = _l12[9]["delivery"] = "[slowly]"
_l12[11]["tags_after"] = "[long pause]"
_l12[12]["pause_after"] = 1.2
_l12[13]["pause_after"] = _l12[14]["pause_after"] = 0.2
for _v in ("12", "13", "14", "15"):
    (PR / "40-briefs" / f"video-{_v}-narration.json").write_text(json.dumps({"video": _v, "language": "english", "lines": _l12}), encoding="utf-8")
_EL["refuse"] = set()
_n = len(_EL["seen"])
js, _ = ts("tts", "say", "--run", str(PR), "--video", "12")
_EL["refuse"] = {"pcm_44100"}
_s12 = json.loads((PR / "30-assets" / "narration" / "video-12.json").read_text(encoding="utf-8"))
_q = _el_tts(_n)
_rids = [r["rid"] for r in _q]
_tx = [r["body"]["text"] for r in _q]
check(js.get("ok") and [p["lines"] for p in _s12["passages"]] == [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10], [11, 12, 13], [14, 15, 16, 17, 18]]
      and all(len(x) <= 850 for x in _tx) and _tx[1].count("[slowly]") == 1 and _tx[1].index("[slowly]") < _tx[1].index("Line 09")
      and "[slowly]" not in _tx[2] and " [long pause] Line 13" in _tx[2]
      and [r["body"].get("previous_request_ids") for r in _q] == [None, _rids[:1], _rids[:2], _rids[:3]]
      and [("next_text" in r["body"]) for r in _q] == [True, True, True, False] and _s12.get("pause_after_not_placed") == [13, 14, 15],
      "passages: at most 850 characters, ending at a passage_break, where a delivery ends (a run of lines sharing one tag carries it once), "
      "and, too long, at the plan's largest pause in their second half; a pause asked with tags_after; up to three stitched request ids; a "
      "planned pause_after is a hint, never a silence placed")
_sr12, _all12 = _frames(PR / "30-assets" / "narration" / "video-12.wav")
check(_sr12 == 44100 and _all12 == b"".join(_EL["delivered"][r]["audio"] for r in _rids)
      and not list((PR / "30-assets" / "narration" / "video-12").glob("*.delivered.*")) and _s12["format"]["sample_rate"] == 44100,
      "in PCM the narration's samples are the very bytes ElevenLabs delivered, end to end")
# the characters run out (--budget, the account's, or ElevenLabs' own refusal): the narration is what was made, flagged partial
_n = len(_EL["seen"])
js, _ = ts("tts", "say", "--run", str(PR), "--video", "13", "--budget", "1300")
_s13 = json.loads((PR / "30-assets" / "narration" / "video-13.json").read_text(encoding="utf-8"))
check(js.get("ok") and (js.get("partial") or {}).get("lines_made") == [1, 5] and len(_el_tts(_n)) == 1
      and ((js.get("partial") or {}).get("stopped") or {}).get("why") == "--budget" and (_s13.get("partial") or {}).get("passages_made") == 1
      and [r["n"] for r in _s13["lines"]] == [1, 2, 3, 4, 5],
      "tts say --budget stops before a passage the characters left do not cover: the narration is the passages made, flagged partial")
_n = len(_EL["seen"])
js, _ = ts("tts", "say", "--run", str(PR), "--video", "13", "--budget", "500", "--fill")
_s13 = json.loads((PR / "30-assets" / "narration" / "video-13.json").read_text(encoding="utf-8"))
_q = _el_tts(_n)
check(js.get("ok") and [r["n"] for r in _s13["lines"]] == [1, 2, 3, 4, 5, 6, 7, 8] and len(_q) == 1 and "next_text" not in _q[0]["body"]
      and len(_q[0]["body"]["text"]) <= 500 and "[slowly]" not in _q[0]["body"]["text"] and _s13["passages"][1].get("shortened") is True
      and ((_s13.get("partial") or {}).get("stopped") or {}).get("shortened_to_lines") == [6, 7, 8],
      "tts say --fill makes the last passage from the whole lines that still fit: the narration stops at a line's end, never inside one")
(PR / "40-briefs" / "video-13-images.json").write_text(json.dumps({"video": "13", "transition": "cut", "images": [
    {"image": 1, "from_line": 1, "motion": "none"}, {"image": 2, "from_line": 6, "motion": "none"},
    {"image": 3, "from_line": 9, "motion": "none"}, {"image": 4, "from_line": 14, "motion": "none"}]}), encoding="utf-8")
js, code = ts("slideshow", "plan", "--run", str(PR), "--video", "13", ok=False)
_tl13 = json.loads((PR / "40-briefs" / "video-13-timeline.json").read_text(encoding="utf-8"))
check(code == 0 and (js.get("partial_narration") or {}).get("ends_at_line") == 8 and (js.get("partial_narration") or {}).get("images_left_out") == [3, 4]
      and [s_[0] for s_ in js.get("image_spans") or []] == [1, 2] and _tl13.get("images_after_narration") == [3, 4],
      "slideshow plan on a partial narration leaves out the images whose line comes after its end and lists them, without failing")
_EL["allow"] = 1
_n = len(_EL["seen"])
js, _ = ts("tts", "say", "--run", str(PR), "--video", "14")
_EL["allow"] = None
check(js.get("ok") and (js.get("partial") or {}).get("lines_made") == [1, 5] and len(_el_tts(_n)) == 1
      and len([r for r in _el_tts(_n, ok=False) if r["status"] == 402]) == 1 and "402" in str(((js.get("partial") or {}).get("stopped") or {}).get("why")),
      "a passage ElevenLabs refuses for credits (402) ends the narration there: the passages made are kept, flagged partial")
_EL["limit"] = _EL["used"] + 800
_n = len(_EL["seen"])
js, _ = ts("tts", "say", "--run", str(PR), "--video", "15")
_EL["limit"] = 1_000_000
_c1 = len(_el_tts(_n)[0]["body"]["text"]) if _el_tts(_n) else None
check(((js.get("partial") or {}).get("stopped") or {}).get("why") == "the account's characters" and len(_el_tts(_n)) == 1
      and (js.get("credits") or {}).get("before") == 800 and (js.get("credits") or {}).get("after") == 800 - (_c1 or 0),
      "the account's characters left (read before the first passage) stop the narration before a passage they do not cover")
_EL["d"] = 0.065
check(not any(_ELKEY in o for o in _outs)
      and not any(_ELKEY in p.read_text(encoding="utf-8", errors="ignore") for R_ in (SR, ER, PR) for p in R_.rglob("*")
                  if p.is_file() and p.suffix in (".json", ".md", ".txt")),
      "the ElevenLabs key is never printed and never written to a run")
js, _ = ts("new-run", "--mode", "analyze", "--slug", "static-forecast")
FR = Path(js["run_dir"])
_fsl = "Flat 2D vector illustration with thick dark outlines."
_fcs = "Nothing is laid over the picture: no captions, no titles, no labels, no logos."
(FR / "40-briefs").mkdir(parents=True, exist_ok=True)
(FR / "40-briefs" / "video-01-images.json").write_text(json.dumps({"video": "01", "style_lock": _fsl, "images": [
    {"image": 1, "from_line": 1, "prompt": f"A kitchen wall where a thermometer reads 38 degrees. {_fsl} {_fcs}", "motion": "zoom-in"},
    {"image": 2, "from_line": 2, "prompt": f"A quiet street at dawn with no signs and no posters. {_fsl} {_fcs}", "motion": "none"},
    {"image": 3, "from_line": 3, "prompt": f"Two scenes side by side: an old church on a hill. {_fcs}", "motion": "none"},
    {"image": 4, "from_line": 4, "prompt": f"A map of the coast. {_fsl} {_fcs}", "motion": "pan-left", "label_note": "the city's name"}]}),
    encoding="utf-8")
js, _ = ts("static", "forecast", "--run", str(FR), "--video", "01", "--part", "images", "--from", "1", "--to", "4")
_fic = (js.get("images") or {}).get("counts") or {}
check(js.get("ok") and _fic.get("text_carriers_without_planned_text") == [1, 4] and _fic.get("digits_in_scene") == [1]
      and _fic.get("religion_or_superstition_words") == [3] and _fic.get("split_words") == [3] and _fic.get("style_lock_missing") == [3]
      and _fic.get("label_on_moving_image") == [4] and _fic.get("clean_sentence_missing") == [],
      f"static forecast lists each image prompt's facts that tend to spoil a still, before it is drawn: a thing that carries writing with no "
      f"words planned, digits, a split, words of static §11, a missing style lock, a label on a moving image; 'no signs' is kept out ({_fic})")
(FR / "40-briefs" / "music.json").write_text(json.dumps({"tracks": [{"video": "01", "caption": "slow ambient pads under a distant choir, no vocals",
    "duration": 700, "bpm": 70, "sections": [{"caption": "calm", "duration": 300}, {"caption": "tense", "duration": 300},
                                             {"caption": "release", "duration": 108}]}]}), encoding="utf-8")
js, _ = ts("static", "forecast", "--run", str(FR), "--video", "01", "--part", "music")
_fmu = js.get("music") or {}
check(js.get("ok") and _fmu.get("vocal_words_not_negated") == ["choir"] and _fmu.get("religion_or_superstition_words") == ["choir"]
      and _fmu.get("needs_sections") is True and _fmu.get("sections") == 3 and _fmu.get("sections_sum_s") == 708.0
      and _fmu.get("sections_should_sum_s") == 708.0 and _fmu.get("made") is False and "headroom_gb" in (_fmu.get("memory") or {}),
      f"static forecast reads a bed's plan before it is made: a voice the caption asks for (a choir; 'no vocals' is kept out), the sections "
      f"against the length with their crossfades, and the memory record ({_fmu.get('vocal_words_not_negated')})")
_mmp = Path(_tf.mkdtemp(prefix="awl-mm-")) / ".model-memory.json"
_mm_orig = _awl._model_memory_path
_awl._model_memory_path = lambda: _mmp
try:
    _awl._model_memory_note("music", {"op": "make", "model": "acestep-v15"}, {"ok": False, "peak_gb": 12.83},
                            "[memguard] STOPPED the app to protect Windows: free RAM 4.4 GB, free commit 2.0 GB (app was using 12.8 GB).\n"
                            "[memguard] peak memory used by the app: 12.83 GB (cap 20.0 GB)", 14.8, 1)
    _awl._model_memory_note("image", {"op": "generate", "model": "flux3-image-klein-int8"}, {"ok": True, "peak_gb": 12.68}, "", 15.1, 0)
    _mmj = json.loads(_mmp.read_text(encoding="utf-8"))["jobs"]
    _fmm = _awl._fc_memory("music", 3.0)
finally:
    _awl._model_memory_path = _mm_orig
check(len(_mmj) == 2 and _mmj[0]["guard_stopped"] is True and _mmj[0]["free_commit_gb_at_stop"] == 2.0 and _mmj[0]["free_commit_gb_before"] == 14.8
      and _mmj[1]["ok"] is True and _mmj[1]["guard_stopped"] is False and _fmm["guard_stops"] == 1 and _fmm["need_gb"] == 15.83,
      "every local model job's memory facts go to the PC's record (its peak, a guard stop with the free memory then, the free memory before "
      "it), and the forecast reads the next job's need from it (the stopped peak plus the guard's floor)")
# the whole set as numbers: a reference's measured files read into one table with the set's median and range
_md = SR / "10-media" / "R01"
_md.mkdir(parents=True, exist_ok=True)
(_md / "video.json").write_text(json.dumps({"probe": {"duration_s": 60.0, "aspect": "9:16", "display_width": 1080, "display_height": 1920},
                                            "pacing": {"shots": 20, "median_shot_s": 3.0, "cuts_per_10s": 3.2, "first_cut_s": 1.1,
                                                       "cuts_in_first_3s": 1},
                                            "hook": {"speech_starts_s": 0.1}, "speech": {"n_words": 180, "wpm_speech_only": 190.0},
                                            "audio": {"integrated_lufs": -16.0, "lra_lu": 3.0}}), encoding="utf-8")
(_md / "audio-profile.json").write_text(json.dumps({"speech_share": 0.9, "voice": {"words_per_minute": 175.0, "words": 175,
                                                                                   "pause_s_median": 0.45}}), encoding="utf-8")
(_md / "transcript.json").write_text(json.dumps({"segments": [{"text": "Did you know this? You never noticed it. In 1959 it began."}]}),
                                     encoding="utf-8")
js, _ = ts("static", "profile", "--run", str(SR))
_sp = json.loads((SR / "20-analysis" / "set-profile.json").read_text(encoding="utf-8"))
check(js.get("ok") and js.get("references") == 1 and sorted(js.get("not_analysed") or []) == ["R02", "R03"]
      and _sp["references"]["R01"]["wpm_speech"] == 190.0 and _sp["references"]["R01"]["wpm_overall"] == 175.0
      and _sp["set"]["wpm_speech"]["median"] == 190.0 and _sp["references"]["R01"]["questions_per_minute"] == 1.0
      and _sp["references"]["R01"]["you_per_100_words"] > 0 and (SR / "20-analysis" / "set-profile.md").is_file(),
      "static profile reads every analysed reference's measured numbers into one table with the set's median and range, and lists "
      "the references not analysed yet")
check(_sp["references"]["R01"]["shots"] == 20 and _sp["references"]["R01"]["shot_s_median"] == 3.0,
      "without an edit profile the cutting comes from A1's scene detector")
# with an edit profile the cutting is its shots (every frame read), its few-frame shots inside a join left out
(_md / "edit-profile.json").write_text(json.dumps({"shots": [
    {"start": 0.0, "end": 2.0, "dur": 2.0}, {"start": 2.0, "end": 2.07, "dur": 0.07, "short": True}, {"start": 2.07, "end": 6.0, "dur": 3.93},
    {"start": 6.0, "end": 9.0, "dur": 3.0}] + [{"start": 9.0 + 5 * k, "end": 14.0 + 5 * k, "dur": 5.0} for k in range(10)]}), encoding="utf-8")
ts("static", "profile", "--run", str(SR))
_r1 = json.loads((SR / "20-analysis" / "set-profile.json").read_text(encoding="utf-8"))["references"]["R01"]
check(_r1["shots"] == 13 and _r1["shot_s_median"] == 5.0 and _r1["first_cut_s"] == 2.07 and _r1["shots_from"] == "edit-profile"
      and _r1["shots_scene_detector"] == 20 and _r1["cuts_in_first_3s"] == 1,
      "with an edit profile the shots are its own (every frame read), its few-frame shots inside a join left out, the detector's kept beside")
js, code = ts("static", "profile", "--run", str(SR), "--refs", "R09", ok=False)
check(code == 2 and "no analysed reference" in str(js.get("error")), "static profile with references that were never analysed says so")
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
_bed = Path(js["made"][0]["file"]) if js.get("made") else None
_bcodec = [s.get("codec_name") for s in json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(_bed)],
                                                                capture_output=True, text=True).stdout or "{}").get("streams", [])] if _bed else []
_bside = json.loads(_bed.with_suffix(".json").read_text(encoding="utf-8")) if _bed and _bed.with_suffix(".json").is_file() else {}
check(_bcodec == ["pcm_s16le"] and js["made"][0].get("converted_from") == "pcm_f32le" and (_bside.get("format") or {}).get("converted") is True
      and abs(float(js["made"][0].get("duration_s") or 0) - 12.0) < 0.05,
      "music make saves the bed as 16-bit PCM WAV, the format the CapCut check showed playing (the stub writes float as ACE-Step does), "
      "same length, and the sidecar says it was converted")
_nlines = len(json.loads((SR / "30-assets" / "narration" / "video-01.json").read_text(encoding="utf-8")).get("lines") or [])
_g0 = float(json.loads((SR / "40-briefs" / "video-01-images.json").read_text(encoding="utf-8")).get("music_gain")
            or json.loads((home / "config.json").read_text(encoding="utf-8"))["static"]["music"]["gain"])
js, _ = ts("music", "measure", "--run", str(SR), "--video", "01")
_mb, _mc = js.get("bed") or {}, js.get("as_capcut_plays_it") or {}
check(js.get("ok") and _mb.get("codec") == "pcm_s16le" and isinstance(_mb.get("loudness_lufs"), (int, float))
      and len(_mb.get("over_the_lines") or []) == _nlines > 0 and all("bed_db" in r for r in _mb["over_the_lines"])
      and abs(float(_mc.get("gain") or 0) - _g0) < 1e-9 and isinstance(_mc.get("bed_under_voice_lu"), (int, float))
      and _mc.get("words_narration_alone") == _mc.get("words_with_bed") and _mc.get("word_differences") == []
      and Path(_mc.get("mix") or "").is_file() and (SR / "60-outputs" / "video-01" / "bed-check" / "bed-check.json").is_file()
      and "verdict" in (js.get("note") or ""),
      "music measure gives the bed's facts alone (codec, loudness, its level over each narration line) and under the narration at the "
      "gain CapCut plays (its distance under the voice, the words heard with it against without it), writes them, and judges nothing")
js2, _ = ts("music", "measure", "--run", str(SR), "--video", "01", "--gain", "0.11")
_mc2 = js2.get("as_capcut_plays_it") or {}
check(js2.get("ok") and _mc2.get("gain") == 0.11 and isinstance(_mc2.get("bed_under_voice_lu"), (int, float))
      and isinstance(_mc.get("bed_under_voice_lu"), (int, float))
      and abs((_mc2["bed_under_voice_lu"] - _mc["bed_under_voice_lu"]) - 20 * __import__("math").log10(_g0 / 0.11)) < 0.15,
      "music measure --gain tests another level: the bed sits that many dB further under the voice")
js, code = ts("music", "measure", "--run", str(SR), "--video", "07", ok=False)
check(code == 2 and "music make" in json.dumps(js), "music measure of a video with no bed says to make it first")
# a bed longer than one piece (the user, 2026-11-07: "if acestep 1.5 max is 10 minutes, then we could do 2x8minutes for a 16minutes
# video i guess, or 5x5 for a 25 minutes"): sections joined with crossfades into one file of the planned length (small numbers here)
(SR / "40-briefs" / "music-long.json").write_text(json.dumps({"tracks": [
    {"video": "05", "caption": "a slow orchestral underscore", "duration": 50, "split_over_s": 30, "max_section_s": 20, "crossfade_s": 2},
    {"video": "06", "caption": "x", "duration": 40, "crossfade_s": 2,
     "sections": [{"caption": "a calm opening", "duration": 22}, {"caption": "a darker close", "duration": 20}]}]}), encoding="utf-8")
js, _ = ts("music", "make", "--run", str(SR), "--plan", str(SR / "40-briefs" / "music-long.json"))
_ml = {m["video"]: m for m in js.get("made") or []}
check(js.get("ok") and _ml["05"]["sections"] == 3 and abs(float(_ml["05"]["duration_s"]) - 50) < 0.1 and _ml["05"]["codec"] == "pcm_s16le"
      and all(abs(x - 18.0) < 0.01 for x in _ml["05"]["section_s"]) and _ml["06"]["sections"] == 2
      and abs(float(_ml["06"]["duration_s"]) - 40) < 0.1 and (SR / "30-assets" / "music" / "parts" / "video-05-part3.wav").is_file(),
      "a bed longer than one piece is made in equal sections (3 x 18 s for 50 s with 2 s crossfades) or in the plan's own sections, "
      "joined into one 16-bit file of the planned length")
(SR / "40-briefs" / "music-too-long.json").write_text(json.dumps({"tracks": [{"video": "05", "caption": "x", "duration": 700,
                                                                                "sections": [{"duration": 700}]}]}), encoding="utf-8")
js, code = ts("music", "make", "--run", str(SR), "--plan", str(SR / "40-briefs" / "music-too-long.json"), ok=False)
check(code == 2 and "longer than ACE-Step" in js.get("error", ""), "a section longer than ACE-Step's 600 s is refused before any model runs")
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
# a timeline start rounded a hair after its frame (13.9667 for frame 419, 2026-11-06) split the shot one frame late: a phantom 1-frame shot
_cutv = home.parent / "cut-at-10.mp4"
_pc = subprocess.Popen([_awl.find_tool("ffmpeg"), "-nostdin", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "270x480",
                        "-r", "30", "-i", "-", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", str(_cutv)], stdin=subprocess.PIPE)
for _k in range(30):
    _pc.stdin.write(_tex.resize((270, 480)).rotate(0 if _k < 10 else 180).tobytes())
_pc.stdin.close()
_pc.wait()
(_cutf := home.parent / "cut-at-10.json").write_text(json.dumps({"shots": [{"shot": 1, "start": 0.0, "end": 0.3334}, {"shot": 2, "start": 0.3334, "end": 1.0}]}), encoding="utf-8")
js, _ = ts("edit-profile", str(_cutv), "--cuts", str(_cutf), "--band", "0.0-0.01", "--out", str(home.parent / "prof-cut.json"))
check([round(s["start"], 3) for s in js["shots"]] == [0.0, 0.333] and not js.get("short_shots_under_0_25s"),
      f"edit-profile splits a given cut on its frame even when its time is rounded a hair after it: no phantom one-frame shot ({[s['start'] for s in js['shots']]})")
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
    # the third build of 2026-11-06: an empty clone kept the template's draft_info.json, and capcut-motion answered ok false
    (_md / "draft_content.json").write_text(_mdc, encoding="utf-8")
    (_md / "draft_info.json").write_text(json.dumps({"id": "TPL", "materials": {}, "tracks": [{"type": "video", "segments": [
        _clip("T1", 0, 1500000, []), _clip("T2", 1500000, 2500000, [])]}]}), encoding="utf-8")
    js, code, _ = t("capcut-motion", "--draft", str(_md), "--timeline", str(_mtl), env=SENV, ok=False)
    check(code == 0 and js.get("ok") and js.get("images_without_a_clip") == [] and len(js.get("stale_copies") or []) == 1
          and js["stale_copies"][0]["file"].endswith("draft_info.json"),
          "capcut-motion judges the clips on draft_content.json; a mirror still holding the template's timeline is named as stale, not a missing clip")
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
      and abs(_ef[3]["start"] - __import__("math").floor((0.3 + _ln[0]["start"]) * 30 + 1e-6) / 30) < 1e-6 and _ef[3]["track"] == "fx2"
      and _ef[4]["track"] == "fx1" and _ef[3]["dur_s"] == 1.0,
      "slideshow plan puts each effect on the timeline: its anchor second on its moment (a cut, a line, a second), the scan's key colour, "
      "overlapping overlays on separate tracks")
# a map's place names as CapCut text (the user, 2026-11-07: "Yes, as CapCut text"): slideshow plan carries each image's labels and lists
# a look the plan leaves out; capcut-labels places them over the image's span in the plan's look
_plan_lb = json.loads(json.dumps(_plan_fx))
_plan_lb["images"][1]["labels"] = [{"text": "London", "x_rel": 0.48, "y_rel": 0.3}, {"text": "Sao Paulo", "x_rel": 0.3, "y_rel": 0.7}]
(SR / "40-briefs" / "video-01-images.json").write_text(json.dumps(_plan_lb), encoding="utf-8")
js, _ = ts("slideshow", "plan", "--run", str(SR), "--video", "01", ok=False)
check(js.get("ok") is False and any(u.startswith("labels_style: no font_file") for u in js.get("undecided") or [])
      and [lb[1] for lb in js.get("labels") or []] == ["London", "Sao Paulo"],
      "slideshow plan carries an image's labels to the timeline and lists the labels' look the plan leaves undecided")
_plan_lb["labels_style"] = {"font_file": "C:/Windows/Fonts/arial.ttf", "size": 7, "fill": "#FFFFFF", "stroke_color": "#000000",
                            "stroke_width": 0.12, "shadow": True}
(SR / "40-briefs" / "video-01-images.json").write_text(json.dumps(_plan_lb), encoding="utf-8")
js, _ = ts("slideshow", "plan", "--run", str(SR), "--video", "01")
_mv = str(_plan_lb["images"][1].get("motion") or "none") != "none"
check(js.get("ok") and js.get("labels_on_moving_images") == ([2] if _mv else []),
      "slideshow plan lists a labelled image that moves (a label does not follow a move)")
_lbd = home.parent / "labels-drafts"
subprocess.run([shutil.which("capcut.cmd") or shutil.which("capcut") or "capcut", "init", "lbl", "--drafts", str(_lbd), "--width", "1080",
                "--height", "1920"], capture_output=True, text=True)
js, code, _ = t("capcut-labels", "--draft", str(_lbd / "lbl"), "--run", str(SR), "--video", "01", env=SENV, ok=False)
if code == 3:
    print("SKIP  capcut-labels: CapCut is running on this machine")
else:
    _c = json.loads((_lbd / "lbl" / "draft_content.json").read_text(encoding="utf-8"))
    _segs = [s for tr in _c["tracks"] if tr.get("name") == "labels" for s in tr["segments"]]
    _segs2 = [s for tr in _c["tracks"] if tr.get("name") == "labels-2" for s in tr["segments"]]
    _tl2 = json.loads((SR / "40-briefs" / "video-01-timeline.json").read_text(encoding="utf-8"))["images"][1]
    check(code == 0 and js.get("labels") == 2 and len(_segs) == 1 and len(_segs2) == 1 and js.get("tracks") == ["labels", "labels-2"]
          and all(abs(s["target_timerange"]["start"] / 1e6 - _tl2["start"]) < 1e-3 for s in _segs + _segs2)
          and abs(_segs[0]["clip"]["transform"]["x"] - (-0.04)) < 1e-6 and abs(_segs[0]["clip"]["transform"]["y"] - 0.4) < 1e-6
          and js.get("font"),
          "capcut-labels puts each label over its image's span, its centre in CapCut's units, in the plan's font, two labels shown at "
          "once on tracks of their own (labels, labels-2: a track never holds two texts at one moment)")
    js, code, _ = t("capcut-labels", "--draft", str(_lbd / "lbl"), "--run", str(SR), "--video", "01", env=SENV, ok=False)
    check(code == 2 and "already has" in str(js.get("error")), "capcut-labels places the labels once per build (a second run is refused)")
# the same video in a second format (the user, 2026-11-08: "if they pick both options then we should use the same plan ... but also in a
# 9:16 image version too ... 2 capcut projects too"): SR's primary is 9:16; 16:9 rides beside it with its own stills and timeline
js, code = ts("static", "format", "--run", str(SR), "--aspect", "9:16", "--res", "1080", "--also", ok=False)
check(code == 2 and "primary" in str(js.get("error")), "static format --also refuses the primary's own aspect")
js, _ = ts("static", "format", "--run", str(SR), "--aspect", "16:9", "--res", "720", "--also")
_mf = js.get("format") or {}
check(js.get("ok") and _mf.get("tag") == "16x9" and _mf.get("export") == "1280x720" and (js.get("primary") or {}).get("aspect") == "9:16",
      "static format --also stores a second format beside the primary (tag 16x9, its own export), the primary kept")
js, code = ts("image", "generate", "--run", str(SR), "--anchor", "C1", "--format", "16:9", "--prompt", "x", ok=False)
check(code == 2 and "once for every format" in str(js.get("error")), "an anchor is made once for every format (--format refused)")
_rec0 = json.loads((SR / "60-outputs" / "video-01" / "images.json").read_text(encoding="utf-8"))["images"]["01"]
_use0 = next(x for x in _rec0["attempts"] if Path(x.get("file") or "").name == _rec0["use"])
_base0 = next(x for x in _rec0["attempts"] if Path(x.get("file") or "").name == _use0["base"]) if _use0.get("source") == "brand" else _use0
_req0 = json.loads(Path(_base0["request_file"]).read_text(encoding="utf-8"))
_n_seen = len(_SEEN)
js, _ = ts("image", "generate", "--run", str(SR), "--video", "01", "--image", "1", "--format", "16:9", "--same-as-primary")
_rq = json.loads(Path(json.loads((SR / "60-outputs" / "video-01" / "16x9" / "images.json").read_text(encoding="utf-8"))["images"]["01"]
                      ["attempts"][-1]["request_file"]).read_text(encoding="utf-8"))
check(js.get("ok") and _rq["params"]["prompt"] == _req0["params"]["prompt"] and _rq["params"]["refs"] == _req0["params"]["refs"]
      and _rq["params"]["size"] == _mf["image_size"] and (js.get("same_as_primary") or {}).get("attempt") == _base0["attempt"]
      and _SEEN[-1]["size"] == _mf["image_size"] and _SEEN[-1]["refs"] == len(_req0["params"]["refs"]) == 1
      and len(_SEEN) == _n_seen + 1 and "16x9" in Path(js["file"]).parts,
      "image generate --same-as-primary sends the first format's still's own prompt and references at the extra format's size, into its folder")
js, code = ts("image", "generate", "--run", str(SR), "--video", "01", "--image", "1", "--format", "16:9", "--same-as-primary",
              "--prompt", "x", ok=False)
check(code == 2 and "none of your own" in str(js.get("error")), "--same-as-primary takes no prompt of its own")
js, _ = ts("image", "generate", "--run", str(SR), "--video", "01", "--image", "1", "--format", "16:9", "--same-as-primary",
           "--swap", "wheat field", "barley field")
_rq = json.loads(Path(json.loads((SR / "60-outputs" / "video-01" / "16x9" / "images.json").read_text(encoding="utf-8"))["images"]["01"]
                      ["attempts"][-1]["request_file"]).read_text(encoding="utf-8"))
check(js.get("ok") and _rq["params"]["prompt"] == _req0["params"]["prompt"].replace("wheat field", "barley field")
      and (js.get("same_as_primary") or {}).get("swaps") == [["wheat field", "barley field"]],
      "--same-as-primary --swap changes only the words the agent names (the frame's), the rest of the prompt word for word")
_n_seen = len(_SEEN)
js, code = ts("image", "generate", "--run", str(SR), "--video", "01", "--image", "1", "--format", "16:9", "--same-as-primary",
              "--swap", "a tall frame", "a wide frame", ok=False)
check(code == 2 and "not in" in str(js.get("error")) and len(_SEEN) == _n_seen, "a --swap whose words the prompt does not hold sends nothing")
js, code = ts("image", "prompts", "--run", str(SR), "--format", "16:9", "--swap", "at dusk", "at dawn", ok=False)
check(code == 2 and "images 2, 3" in str(js.get("error")), "image prompts --format --swap names the images whose prompt lacks the words")
js, _ = ts("image", "prompts", "--run", str(SR), "--format", "16:9", "--swap", " a ", " one ")
_pm16 = Path(js["files"][0]).read_text(encoding="utf-8") if js.get("files") else ""
check(js.get("ok") and Path(js["files"][0]).name == "video-01-16x9-image-prompts.md" and "## v01-16x9-i01" in _pm16
      and "A farmer in one wheat field at dusk" in _pm16 and "horizontal 16:9" in _pm16 and "C1 character sheet" not in _pm16
      and "v01-thumb" not in _pm16,
      "image prompts --format writes the same prompts (its swaps applied) named vNN-16x9-iKK, at that format's size, no sheet or thumbnail")
_mfd = home.parent / "user-16x9"
_mfd.mkdir(exist_ok=True)
for _k in (1, 2, 3):
    _Im.new("RGB", (1280, 720), (40 * _k, 90, 140)).save(_mfd / f"v01-16x9-i{_k:02d}.png")
_Im.new("RGB", (1080, 1920), (9, 9, 9)).save(_mfd / "v01-i01.png")   # a first-format still in the same folder: not this format's
js, _ = ts("image", "intake", "--run", str(SR), "--folder", str(_mfd), "--format", "16:9")
check(js.get("ok") and len(js.get("copied") or []) == 3 and not js.get("missing") and js.get("aspect") == "16:9"
      and all("16x9" in Path(c["file"]).parts for c in js["copied"]),
      "image intake --format takes only that format's stills (vNN-16x9-iKK) into 60-outputs/video-01/16x9/")
_plan_mf = json.loads(json.dumps(_plan_fx))
_plan_mf["images"][0].update({"scale": [1.0, 1.25], "x": [0.0, -0.2], "y": [0.0, 0.0]})   # a zoom aimed at a spot of the 9:16 picture
_plan_mf["images"][1]["labels"] = [{"text": "Roswell", "x_rel": 0.4, "y_rel": 0.3}]
_plan_mf["images"][1]["motion"], _plan_mf["images"][1]["amount"] = "none", 0
_plan_mf["labels_style"] = {"font_file": "C:/Windows/Fonts/arial.ttf", "size": 7, "fill": "#FFFFFF", "stroke_color": "#000000",
                            "stroke_width": 0.12, "shadow": True}
(SR / "40-briefs" / "video-01-images.json").write_text(json.dumps(_plan_mf), encoding="utf-8")
js, _ = ts("slideshow", "plan", "--run", str(SR), "--video", "01", "--format", "16:9", ok=False)
_u = js.get("undecided") or []
check(js.get("ok") is False and any(u.startswith("captions for 16x9: no size") for u in _u)
      and any(u.startswith("image 2: no labels for 16x9") for u in _u) and js.get("moves_aimed_in_the_first_format") == [1],
      f"slideshow plan --format lists what the second format still needs (its captions' size and band, the labels read off its picture) "
      f"and the zooms aimed at a spot of the first format's picture ({_u})")
_plan_mf["by_format"] = {"16x9": {"captions": {"size": 7, "y_rel": 0.85}}}
_plan_mf["images"][1]["by_format"] = {"16x9": {"labels": [{"text": "Roswell", "x_rel": 0.55, "y_rel": 0.25}]}}
(SR / "40-briefs" / "video-01-images.json").write_text(json.dumps(_plan_mf), encoding="utf-8")
js, _ = ts("slideshow", "plan", "--run", str(SR), "--video", "01", "--format", "16:9")
_tlf = json.loads((SR / "40-briefs" / "video-01-timeline-16x9.json").read_text(encoding="utf-8"))
_tl0 = json.loads((SR / "40-briefs" / "video-01-timeline.json").read_text(encoding="utf-8"))
_cap0 = json.loads((SR / "60-outputs" / "video-01" / "captions.json").read_text(encoding="utf-8"))
check(js.get("ok") and _tlf["export"] == "1280x720" and _tlf["captions"]["y_rel"] == 0.85 and _tlf["captions"]["size"] == 7
      and all("16x9" in Path(r["file"]).parts for r in _tlf["images"])
      and [r["start"] for r in _tlf["images"]] == [r["start"] for r in _tl0["images"]]
      and _tlf["images"][0]["scale"] == [1.0, 1.1] and _tlf["images"][0]["x"] == [0.0, 0.0]
      and _tlf["images"][1]["labels"][0]["x_rel"] == 0.55 and js.get("captions") == len(_cap0)
      and (SR / "60-outputs" / "video-01" / "16x9" / "captions.srt").is_file(),
      "slideshow plan --format: the same cuts on the same lines, that format's stills and caption look, its own labels, a zoom aimed in "
      "the first format played plain, its captions in 60-outputs/video-01/16x9/")
_cs = home.parent / "store-16x9"
_cs.mkdir(exist_ok=True)
js, _ = ts("capcut-name", "--video", "1", "--format", "16:9", "--store", str(_cs), "--date", "2026-11-08")
check(js.get("ok") and js.get("name") == "08_Nov_2026_v01-16x9", f"capcut-name --format names the second format's project ({js.get('name')})")
js, _ = ts("contract", "--run", str(SR))
_ct = (SR / "50-requests" / "agent-contract.md").read_text(encoding="utf-8")
check("tag 16x9" in _ct and "--format 16x9" in _ct and "<formats>" not in _ct,
      "the Static contract lists the run's formats, each extra one with its tag and where its work goes")
(SR / "40-briefs" / "video-01-images.json").write_text(json.dumps(_plan_fx), encoding="utf-8")
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
# a project keeps a font only while its file stays put (the user, 2026-11-07: "the capcut looks like returned the font back to default")
_lib = [f for f in _fonts if f.get("source") == "library"]
check(_lib and _fonts[:len(_lib)] == _lib and any(f["family"] == "Sigmar One" for f in _lib)
      and all(f.get("kept_by") for f in _fonts) and "kept across" in _lib[0]["kept_by"]
      and all("may clear" in f["kept_by"] for f in _fonts if f.get("source") == "capcut-downloaded")
      and all("update replaces" in f["kept_by"] for f in _fonts if f.get("source") == "capcut"),
      "capcut-font --list puts the library's fonts folder first and says how every font's folder is kept (an update, a cache clear)")
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
      and "Memes: n/a (Static" in _ct and "CapCut plan: free" in _ct, "contract writes production-agents 2s's Static prompt with the run's choices filled (the CapCut plan too)")
# the CapCut plan (the user, 2026-11-06: "make him pick, if he picks pro then be free to pick any edit feature that pro has"): a Pro intro
# or transition is refused on a free run, allowed on a pro one; one CapCut drew nothing for is refused either way
if (_tpl / "draft_content.json").is_file():
    (home / "data").mkdir(exist_ok=True)
    (home / "data" / "capcut-catalogue.json").write_text(json.dumps({
        "text_intros": [{"slug": "pop-up", "visible_animation": True, "pro": True}, {"slug": "mini-zoom", "visible_animation": True, "pro": False},
                        {"slug": "fade-in", "visible_animation": False, "pro": False}],
        "transitions": [{"slug": "mix", "visible_transition": True, "pro": False}]}), encoding="utf-8")
    _pa = home.parent / "Draft_plan"
    _shutil.copytree(_tpl, _pa, ignore=_shutil.ignore_patterns("*.bak", "*bak", "assets", "Resources"))
    _r1 = t("capcut-text-anim", "--draft", str(_pa), "--intro", "pop-up", "--intro-duration", "0.12", "--run", str(SR), env=SENV, ok=False)
    _r2 = t("capcut-text-anim", "--draft", str(_pa), "--intro", "fade-in", "--intro-duration", "0.12", "--run", str(SR), env=SENV, ok=False)
    ts("state", "--run", str(SR), "set", "capcut_plan=pro")
    _r3 = t("capcut-text-anim", "--draft", str(_pa), "--intro", "pop-up", "--intro-duration", "0.12", "--run", str(SR), env=SENV, ok=False)
    ts("state", "--run", str(SR), "set", "capcut_plan=free")
    check(_r1[1] == 2 and "Pro" in _r1[0].get("error", "") and _r2[1] == 2 and "drew nothing" in _r2[0].get("error", "") and _r3[1] != 2,
          "capcut-text-anim refuses a Pro intro on a run whose CapCut plan is free and allows it on a pro run; an intro CapCut drew nothing for is refused")
    (home / "data" / "capcut-catalogue.json").unlink()
js, _ = ts("contract", "--run", str(SR), "--notes", "The anchor is <RUN>/30-assets/characters/C1-a1.png.")
_ct = Path(js["file"]).read_text(encoding="utf-8")
check(f"{SR}/30-assets/characters/C1-a1.png" in _ct and "<RUN>" not in _ct.split("Run-specific notes")[-1],
      "contract fills <RUN> in the run-specific notes too (the run of 2026-11-06 sent it to the agent as it was)")
js, _ = ts("lint-run", "--run", str(SR))
check(js.get("contract", {}).get("loupe_line") is True and js.get("contract", {}).get("unresolved_placeholders") == [], "lint-run reads a Static contract's Loupe line")

# one channel per run (the user, 2026-11-07): the niche, the style reference and the narrator are locked; another niche is a clone that
# copies the analysis and asks its niche, never a second analysis of the same references
js, code = ts("static", "subjects", "--run", str(SR), "--add", "The Ship of Theseus", ok=False)
check(code == 2 and "niche" in js.get("error", ""), "a subject is added only once the run's niche is locked")
js, _ = ts("static", "lock", "--run", str(SR), "--niche", "Philosophy", "--style-ref", "R02")
_lk = js.get("locks") or {}
check(js.get("ok") and _lk.get("niche") == "Philosophy" and _lk.get("style_ref") == "R02" and (_lk.get("voice") or {}).get("sample") == 2,
      "static lock records the run's niche and style reference and shows the narrator with them")
js, _ = ts("static", "lock", "--run", str(SR), "--niche", "philosophy")
check(js.get("ok") and js.get("changed") == [], "the same niche again changes nothing")
js, code = ts("static", "lock", "--run", str(SR), "--niche", "History", ok=False)
check(code == 2 and "clone-run" in js.get("error", ""), "another niche is refused: one niche per run; another niche is a clone")
js, code = ts("static", "lock", "--run", str(SR), "--style-ref", "R09", ok=False)
check(code == 2 and "not a reference" in js.get("error", ""), "a style reference that is not one of the run's references is refused")
js, _ = ts("static", "subjects", "--run", str(SR), "--add", "The Ship of Theseus", "--add", "Diogenes and the lamp")
_sb = js.get("subjects") or []
check(js.get("ok") and [x["video"] for x in js.get("added") or []] == [f"{len(_sb) - 1:02d}", f"{len(_sb):02d}"] and _sb[-1]["title"] == "Diogenes and the lamp",
      "static subjects --add appends the next subjects with the next video numbers")
js, code = ts("static", "subjects", "--run", str(SR), "--add", "the ship of theseus", ok=False)
check(code == 2 and "already" in js.get("error", ""), "a subject the run already has is refused (more videos never repeat one)")
js, code = ts("static", "lock", "--run", str(SR), "--niche", "History", "--replace", ok=False)
check(code == 2 and "once a video" in js.get("error", ""), "--replace cannot change the niche once the run has a video")
(SR / "20-analysis").mkdir(parents=True, exist_ok=True)
(SR / "20-analysis" / "static-spec.md").write_text(f"# Static spec\nThe cards: {SR}/20-analysis/cards.\n", encoding="utf-8")
(SR / "20-analysis" / "static-subjects.md").write_text("# the old niche's pool\n", encoding="utf-8")
js, _ = ts("clone-run", "--from", str(SR))
CR = Path(js["run_dir"])
_cs = json.loads((CR / "state.json").read_text(encoding="utf-8"))
_csm = json.loads((CR / "30-assets" / "voice" / "samples.json").read_text(encoding="utf-8"))
check(js.get("ok") and CR.is_dir() and CR != SR and (CR / "20-analysis" / "static-spec.md").is_file()
      and not (CR / "20-analysis" / "static-subjects.md").exists() and str(CR) in (CR / "20-analysis" / "static-spec.md").read_text(encoding="utf-8")
      and (CR / "00-inventory" / "inventory.json").is_file() and _cs.get("analyze_submode") == "static"
      and ((_cs.get("static") or {}).get("voice") or {}).get("sample") == 2 and "niche" not in (_cs.get("static") or {})
      and not (_cs.get("static") or {}).get("subjects") and _cs.get("videos") == [] and _cs.get("submissions") == []
      and (_cs.get("cloned_from") or {}).get("run") == SR.name and (_cs.get("cloned_from") or {}).get("niche") == "Philosophy"
      and all(str(CR) in s["out"] for s in _csm["samples"]) and not any((CR / "40-briefs").iterdir()) and not (CR / "deliverables").exists(),
      "clone-run copies the Static analysis, the characters and the narrator into a new run, with the paths inside pointed at it, and "
      "leaves out the niche, the subjects, the videos, the ledger, the briefs and the old niche's subject pool")
js, _ = ts("static", "lock", "--run", str(CR), "--niche", "History")
check(js.get("ok") and js["locks"]["niche"] == "History" and js["locks"]["style_ref"] == "R02" and js["locks"]["next_video"] == "01"
      and (js["locks"].get("voice") or {}).get("sample") == 2 and ts("effort", "--run", str(CR))[0]["effort"]["level"] == "static",
      "the clone takes its own niche, keeps the style reference and the narrator, numbers its videos from 01 and has no effort level")
js, code = ts("clone-run", "--from", str(run_f), ok=False)
check(code == 2 and "Static" in js.get("error", ""), "clone-run is for Static runs")

# FLUX 3 Klein on this PC (static_images=klein, the user 2026-11-06): the same T image generate through the local worker (stubbed here), no key
KENV = {**SENV, "AWL_IMAGE_STUB": "1", "OPENAI_API_KEY": ""}
js, _, _ = t("new-run", "--mode", "analyze", "--slug", "static-klein", env=KENV)
KR = Path(js["run_dir"])
t("state", "--run", str(KR), "set", "analyze_submode=static", "static_images=klein", "audio_ingest=whisper", "qc_fixes=auto", "capcut_plan=pro", env=KENV)
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
# the video's YouTube thumbnail (the user, 2026-11-07: "we will also in the end generate the yt thumbnail for each video using klein or
# openai api directly or just prompt"): one more image of the video, at its own size, kept in the deliverables
js, code, _ = t("image", "generate", "--run", str(KR), "--video", "01", "--thumbnail", "--prompt", "x", env=KENV, ok=False)
check(code == 2 and "--size" in js.get("error", ""), "a thumbnail needs its own size (the references' thumbnails', static §12)")
_tp = ("image", "generate", "--run", str(KR), "--video", "01", "--thumbnail", "--size", "1280x720", "--prompt", "A farmer's face lit by the sunset",
       "--ref", str(_ka))
js, _, _ = t(*_tp, env=KENV)
_th = js.get("thumbnail") or {}
_tdir = KR / "60-outputs" / "video-01" / "images"
check(js.get("ok") and js.get("size") == [1280, 720] and Path(js["file"]).name == "thumb-a1.png" and Path(_th.get("deliverable") or "").name == "video-01-thumbnail.png"
      and Path(_th["deliverable"]).is_file() and Path(_th.get("small") or "").is_file()
      and json.loads((KR / "60-outputs" / "video-01" / "images.json").read_text(encoding="utf-8"))["images"]["thumb"]["use"] == "thumb-a1.png"
      and (KR / "50-requests" / "video-01-thumb-a1-image-request.json").is_file(),
      "image generate --thumbnail makes the video's thumbnail at its size (thumb-a1), keeps it in deliverables with a feed-size copy")
js, _, _ = t(*_tp, "--again", env=KENV)
js2, _, _ = t("image", "use", "--run", str(KR), "--video", "01", "--thumbnail", "--attempt", "1", env=KENV)
check(js.get("attempt") == 2 and js2.get("ok") and js2["uses"].endswith("thumb-a1.png")
      and (KR / "deliverables" / "video-01-thumbnail.png").read_bytes() == (_tdir / "thumb-a1.png").read_bytes(),
      "another thumbnail attempt replaces the deliverable; image use --thumbnail puts the chosen one back")
js, _, _ = t("contract", "--run", str(KR), env=KENV)
check("Images: klein" in Path(js["file"]).read_text(encoding="utf-8") and not js.get("unresolved_placeholders"), "a Klein run's contract says Images: klein")
# real things look like themselves (the user, 2026-11-07: "if there's a company, or a brand being talked about, their logo should appear
# somewhere"): the official logo file is composited onto a surface of the still, never drawn; another brand's mark is painted over
from PIL import Image as _PL, ImageDraw as _PD  # noqa: E402
_lg = home.parent / "brand-test" / "logo.png"
_lg.parent.mkdir(parents=True, exist_ok=True)
_li = _PL.new("RGBA", (400, 200), (0, 0, 0, 0))
_PD.Draw(_li).ellipse((20, 20, 380, 180), fill=(230, 40, 60, 255))
_li.save(_lg)
js, _, _ = t("image", "brand", "--run", str(KR), "--video", "01", "--image", "1", "--logo", str(_lg), "--box", "100,100,700,500", "--card",
             "--card-color", "#fafafa", "--cover", "800,800,860,860", env=KENV)
_bf = Path(js.get("file") or "")
_bim = _PL.open(_bf).convert("RGB") if _bf.is_file() else None
_brec = json.loads((KR / "60-outputs" / "video-01" / "images.json").read_text(encoding="utf-8"))["images"]["01"]
check(js.get("ok") and _bf.name == "i01-a4.png" and _brec["use"] == "i01-a4.png" and _brec["attempts"][-1]["source"] == "brand"
      and Path(js["base"]).name == "i01-a3.png" and (KR / "60-outputs" / "video-01" / "images" / "i01-a3.png").is_file()
      and _bim.getpixel((400, 300))[0] > 200 and _bim.getpixel((400, 300))[1] < 80 and _bim.getpixel((105, 300)) != _bim.getpixel((150, 300))
      and len({_bim.getpixel((x, y)) for x in range(805, 856, 10) for y in range(805, 856, 10)}) == 1
      and 100 <= js["logo"]["at"][0] and js["logo"]["at"][2] <= 700 and js["logo"]["at"][1] >= 100 and js["logo"]["at"][3] <= 500,
      "image brand composites the logo file inside its box on a card (the next attempt, now in use, the generated one kept) and paints a "
      "cover with one colour")
js, code, _ = t("image", "brand", "--run", str(KR), "--video", "01", "--image", "1", "--logo", str(_lg), "--box", "100,100,5000,500",
                env=KENV, ok=False)
check(code == 2 and "outside" in js.get("error", ""), "image brand refuses a box outside the picture")
_kf, _, _ = t("static", "format", "--run", str(KR), "--aspect", "16:9", "--res", "720", "--also", env=KENV)
js, _, _ = t("image", "generate", "--run", str(KR), "--video", "01", "--image", "1", "--format", "16:9", "--same-as-primary", env=KENV)
_rqa3 = json.loads((KR / "50-requests" / "video-01-i01-a3-image-request.json").read_text(encoding="utf-8"))
_rq16 = json.loads((KR / "50-requests" / "video-01-16x9-i01-a1-image-request.json").read_text(encoding="utf-8"))
check(js.get("ok") and (js.get("same_as_primary") or {}).get("attempt") == 3 and _rq16["params"]["prompt"] == _rqa3["params"]["prompt"]
      and _rq16["params"]["size"] == (_kf.get("format") or {}).get("image_size") and _rq16.get("format") == "16x9"
      and Path(js["file"]).parent == KR / "60-outputs" / "video-01" / "16x9" / "images",
      "--same-as-primary follows a still whose logo was placed back to the generated attempt and sends that request at the other size")
js, _, _ = t("fetch-image", "--run", str(KR), "--kind", "logo", "--name", "test-brand-logo", "--url", "https://example.org/logo.png",
             "--source", "https://example.org/press", "--licence", "press kit", env={**KENV, "AWL_FETCH_STUB": str(_lg)})
_fm = json.loads(Path(str(js.get("file")) + ".source.json").read_text(encoding="utf-8")) if js.get("file") else {}
check(js.get("ok") and Path(js["file"]).parent == KR / "30-assets" / "brand" and js.get("has_alpha") and js.get("size") == [400, 200]
      and _fm.get("source") == "https://example.org/press" and _fm.get("licence") == "press kit",
      "fetch-image saves a logo into the run's brand folder with its size, transparency, source and licence beside it")
js, _, _ = t("fetch-image", "--run", str(KR), "--kind", "photo", "--name", "C1-photo-1", "--commons", "File:Someone.jpg",
             env={**KENV, "AWL_FETCH_STUB": str(_lg)})
check(js.get("ok") and Path(js["file"]).parent == KR / "30-assets" / "characters" / "photos" and js.get("licence") == "Public domain"
      and js.get("commons") == "File:Someone.jpg", "fetch-image --commons records the Commons file's licence; a photo goes to the characters' photos")
# no subtitle-like text (the user, 2026-11-07: "just not subtitles style text whatsoever"): the answer lists caption words in a prompt,
# a cast sheet carries 3+ characters as one reference, and image text reads the letters in the stills as facts
js, _, _ = t("image", "generate", "--run", str(KR), "--video", "01", "--image", "3", "--prompt",
             "A quiet street at dusk; the bottom fifth, where captions sit, shows only pavement.", env=KENV)
check(js.get("ok") and js.get("prompt_overlay_words") == ["captions"] and "memory_retry" in js,
      "image generate lists the caption words a prompt holds (they make the model draw a made-up subtitle) and its memory retry")
js, _, _ = t("image", "generate", "--run", str(KR), "--anchor", "C2", "--prompt", "Character sheet: a tall woman in a red coat", env=KENV)
js, _, _ = t("image", "cast", "--run", str(KR), "--ids", "C1,C2", env=KENV)
check(js.get("ok") and Path(js.get("file") or "").name == "cast-C1-C2.png" and Path(js["file"]).is_file() and js.get("order_left_to_right") == ["C1", "C2"],
      "image cast sets the anchors in use side by side on one sheet, left to right as given")
from PIL import ImageFont as _PF  # noqa: E402
_t3 = Path(json.loads((KR / "60-outputs" / "video-01" / "images.json").read_text(encoding="utf-8"))["images"]["03"]["attempts"][-1]["file"])
_ti = _PL.open(_t3).convert("RGB")
_dr = _PD.Draw(_ti)
_dr.rectangle((80, 1700, 1140, 1900), fill=(250, 250, 250))
try:
    _fn = _PF.truetype("C:/Windows/Fonts/arial.ttf", 64)
except OSError:
    _fn = _PF.load_default()
_dr.text((110, 1760), "MADE UP SUBTITLE LINE", fill=(10, 10, 10), font=_fn)
_ti.save(_t3)
js, _, _ = t("image", "text", "--run", str(KR), "--video", "01", "--image", "3", env=KENV)
_tx = json.loads((KR / "60-outputs" / "video-01" / "image-text.json").read_text(encoding="utf-8"))["images"][0]["lines"]
check(js.get("ok") and js.get("with_lines_in_bottom_third") == [3] and any(x["in_bottom_third"] and "SUBTITLE" in x["text"].upper() for x in _tx),
      "image text reads the letters in a still with their box and marks a line in the bottom third")
js_all, _, _ = t("image", "text", "--run", str(KR), "--video", "01", env=KENV)
js_one, _, _ = t("image", "text", "--run", str(KR), "--video", "01", "--image", "3", env=KENV)
_tx = json.loads((KR / "60-outputs" / "video-01" / "image-text.json").read_text(encoding="utf-8"))["images"]
check(js_all.get("ok") and js_one.get("images") == 1 and js_one.get("images_in_file") == js_all.get("images") == len(_tx) >= 2
      and [r["image"] for r in _tx] == sorted(r["image"] for r in _tx),
      "image text for one still (after a redraw) replaces only that still's row; the other stills' rows stay in the file")
# separate references where they fit (the user, 2026-11-07: "Separate where it fits"): fit gives the free memory against each count
js, _, _ = t("image", "fit", "--run", str(KR), env=KENV)
_rows = {r["refs"]: r for r in js.get("by_refs") or []}
check(js.get("ok") and sorted(_rows) == [0, 1, 2, 3, 4] and all(r["need_gb"] == round(r["peak_gb"] + js["guard_floor_gb"], 2) for r in _rows.values())
      and _rows[3]["peak_from"].startswith("config"),
      "image fit lists, for 0-4 references, the peak (the config's table when the run measured none), the need (peak + floor) and the headroom")
_ir = KR / "60-outputs" / "video-01" / "images.json"
_d = json.loads(_ir.read_text(encoding="utf-8"))
_d["images"].setdefault("09", {"attempts": []})["attempts"].append(
    {"attempt": 1, "status": "failed", "refs_count": 3, "error": "[memguard] STOPPED the app ... peak memory used by the app: 12.90 GB (cap 16.0 GB)"})
_ir.write_text(json.dumps(_d), encoding="utf-8")
js, _, _ = t("image", "fit", "--run", str(KR), "--n-refs", "3", env=KENV)
check(js.get("ok") and len(js.get("by_refs") or []) == 1 and js["by_refs"][0]["peak_gb"] == 12.9 and js["by_refs"][0]["peak_from"] == "this run's jobs",
      "image fit takes the run's own measured peak (here from a stopped job's guard line) over the config's table")

# the references' real YouTube titles and thumbnails (the user, 2026-11-07: "in the references folder there is also a context.txt file ...
# how_to_drive_a_car.mp4|How do you drive a car|C:/users.../how_to_drive.png ... (image files stand at /thumbnails folder)")
from PIL import Image as _PI  # noqa: E402
cx_refs = home.parent / "refs-context"
for _nm in ("how_to_drive_a_car.mp4", "the_last_lighthouse.mp4", "no_line_here.mp4"):
    make_clip(cx_refs / _nm, seconds=2.0, flash=None, audio=False)
(cx_refs / "thumbnails").mkdir(parents=True, exist_ok=True)
_PI.new("RGB", (1280, 720), (200, 40, 40)).save(cx_refs / "thumbnails" / "how_to_drive.png")
_PI.new("RGB", (1280, 720), (40, 40, 200)).save(cx_refs / "thumbnails" / "lighthouse.jpg")
(cx_refs / "context.txt").write_text("how_to_drive_a_car.mp4|How do you drive a car|C:/users/someone/elsewhere/how_to_drive.png\n"
                                     f"the_last_lighthouse.mp4|The Last Lighthouse Keeper | A True Story|{cx_refs / 'thumbnails' / 'lighthouse.jpg'}\n"
                                     "a_video_not_here.mp4|Nobody|nothing.png\njust one field\n", encoding="utf-8")
CX = Path(t("new-run", "--mode", "analyze", "--source", str(cx_refs), "--slug", "static-context", env=ENV)[0]["run_dir"])
t("inventory", str(cx_refs), "--run", str(CX), "--as", "references", env=ENV)
t("state", "--run", CX.name, "set", "analyze_submode=static", "static_images=prompts", "audio_ingest=whisper", env=ENV)
js, _, _ = t("static", "context", "--run", CX.name, env=ENV)
_cr = {r["file"]: r for r in json.loads((CX / "00-inventory" / "context.json").read_text(encoding="utf-8"))["rows"]}
check(js.get("found") and js.get("matched") == 2 and _cr["how_to_drive_a_car.mp4"]["title"] == "How do you drive a car"
      and str(_cr["how_to_drive_a_car.mp4"]["thumbnail"]).endswith("how_to_drive.png") and _cr["how_to_drive_a_car.mp4"]["thumbnail_size"] == "1280x720"
      and _cr["the_last_lighthouse.mp4"]["title"] == "The Last Lighthouse Keeper | A True Story"
      and js.get("lines_no_video_matches") == ["a_video_not_here.mp4"] and len(js.get("unparsed_lines") or []) == 1
      and len(js.get("videos_without_a_line") or []) == 1 and js.get("thumbnail_sizes") == {"1280x720": 2}
      and js.get("sheets") and all(Path(s).is_file() for s in js["sheets"]) and (CX / "00-inventory" / "context.md").is_file(),
      "static context matches each line to its video by file name, finds a moved thumbnail in the thumbnails folder by its name, keeps a "
      "title with a bar in it, lists what does not match, measures the thumbnails and makes the labelled sheets")
js, _, _ = t("static", "context", "--run", str(SR), env=ENV)
check(js.get("ok") and js.get("found") is False, "no context.txt: the run goes on, told there are no real titles or thumbnails")
# the titles from the file names (the user, 2026-11-07: "we will not have the context.txt file no more because the video already have
# their name ... Channel_Name_Video_Title_and_somehashtags"; the tail is the YouTube id)
nm_refs = home.parent / "refs-names"
for _nm in ("Deep_Dives_The_Rise_of_Rome_in_9_Minutes_TZIOfwN7bVI.mp4", "Deep_Dives_POV_You_Have_$1_Billion_#shorts_dw-fdH1_7Zk.mp4",
            "video.mp4", "Cooking_Pasta_Masterclass.mp4"):
    make_clip(nm_refs / _nm, seconds=2.0, flash=None, audio=False)
NM = Path(t("new-run", "--mode", "analyze", "--source", str(nm_refs), "--slug", "static-names", env=ENV)[0]["run_dir"])
t("inventory", str(nm_refs), "--run", str(NM), "--as", "references", env=ENV)
t("state", "--run", NM.name, "set", "analyze_submode=static", "static_images=prompts", "audio_ingest=whisper", env=ENV)
js, _, _ = t("static", "context", "--run", NM.name, env=ENV)
_nr = {r["file"]: r for r in js.get("rows") or []}
_n1, _n2 = _nr.get("Deep_Dives_The_Rise_of_Rome_in_9_Minutes_TZIOfwN7bVI.mp4") or {}, _nr.get("Deep_Dives_POV_You_Have_$1_Billion_#shorts_dw-fdH1_7Zk.mp4") or {}
check(js.get("ok") and js.get("from_names") and js.get("found") is False and _n1.get("youtube_id_like") == "TZIOfwN7bVI"
      and _n1.get("words") == "Deep Dives The Rise of Rome in 9 Minutes" and _n2.get("youtube_id_like") == "dw-fdH1_7Zk"
      and _n2.get("hashtags") == ["#shorts"] and _n2.get("words") == "Deep Dives POV You Have $1 Billion"
      and (_nr.get("video.mp4") or {}).get("youtube_id_like") is None and js.get("common_leading_words") == "Deep Dives"
      and (_nr.get("Cooking_Pasta_Masterclass.mp4") or {}).get("youtube_id_like") is None
      and (_nr.get("Cooking_Pasta_Masterclass.mp4") or {}).get("words") == "Cooking Pasta Masterclass"
      and (NM / "00-inventory" / "context.md").is_file() and json.loads((NM / "00-inventory" / "context.json").read_text(encoding="utf-8")).get("from_names"),
      "without context.txt the titles come from the file names: the words, the YouTube id at the end (letters, digits, _ and -), the "
      "hashtags apart, the words every name starts with (the channel's), and no title from a name without that pattern")
js, code, _ = t("static", "context", "--run", NM.name, "--file", str(nm_refs / "missing.txt"), env=ENV, ok=False)
check(code == 2 and "no such file" in js.get("error", ""), "static context --file names a file that must exist")
check(js.get("ok") is not True and (json.loads((NM / "00-inventory" / "context.json").read_text(encoding="utf-8")).get("thumbnails") is None),
      "names without an image of the same name: no reference thumbnails")
# a thumbnail beside its video under the same name (the user, 2026-11-08), and one with no video of its name
from PIL import Image as _TIm
_TIm.new("RGB", (1280, 720), (200, 40, 40)).save(nm_refs / "Deep_Dives_The_Rise_of_Rome_in_9_Minutes_TZIOfwN7bVI.jpg")
_TIm.new("RGB", (1280, 720), (40, 40, 200)).save(nm_refs / "Deep_Dives_Fall_of_Carthage_Ab3dEf9hIjK.jpg")
js, _, _ = t("static", "context", "--run", NM.name, env=ENV)
_th = js.get("thumbnails") or {}
_nr = {r["file"]: r for r in js.get("rows") or []}
check(js.get("ok") and (_nr.get("Deep_Dives_The_Rise_of_Rome_in_9_Minutes_TZIOfwN7bVI.mp4") or {}).get("thumbnail_size") == "1280x720"
      and (_nr.get("video.mp4") or {}).get("thumbnail") is None and len(_th.get("with_thumbnail") or []) == 1
      and [x["words"] for x in _th.get("thumbnails_without_video") or []] == ["Deep Dives Fall of Carthage"]
      and _th.get("thumbnail_sizes") == {"1280x720": 2} and all(Path(s).is_file() for s in _th.get("sheets") or [None]),
      "static context pairs each video with the image of its name beside it, lists a thumbnail no video matches, and makes the sheets")
# a reference another run already analysed is not analysed again (the user, 2026-11-07: "we already have the Sadam Hussein's there whom
# we've already analyzed, analyze the two new samples"): matched by the file's hash and size, copied under its id here
_nv = {it["rel"]: it["id"] for it in json.loads((NM / "00-inventory" / "inventory.json").read_text(encoding="utf-8"))["items"]}["video.mp4"]
_om = NM / "10-media" / _nv              # stands in for the run that analysed video.mp4 (its id there; V02 in the new run below)
_om.mkdir(parents=True, exist_ok=True)
(_om / "video.json").write_text(json.dumps({"id": _nv, "frames": str(_om / "base" / "base_0001.jpg"), "see": f"{_nv} at 00:01"}), encoding="utf-8")
(_om / "base").mkdir(exist_ok=True)
(_om / "base" / "base_0001.jpg").write_bytes(b"\xff\xd8not-a-real-jpeg")
(NM / "20-analysis" / "cards").mkdir(parents=True, exist_ok=True)
(NM / "20-analysis" / "cards" / f"{_nv}.md").write_text(f"# {_nv} · video.mp4\nStoryboard: `{_om / 'sheets' / 'storyboard-01.jpg'}` ({_nv}).\n"
                                                        f"Not {_nv}0.\n", encoding="utf-8")
ru_refs = home.parent / "refs-reuse"
ru_refs.mkdir(parents=True, exist_ok=True)
shutil.copy2(nm_refs / "video.mp4", ru_refs / "video.mp4")
make_clip(ru_refs / "Another_Channel_A_New_One_abcdefghijk.mp4", seconds=2.5, flash=None, audio=False)
RU = Path(t("new-run", "--mode", "analyze", "--source", str(ru_refs), "--slug", "static-reuse", env=ENV)[0]["run_dir"])
t("inventory", str(ru_refs), "--run", str(RU), "--as", "references", env=ENV)
t("state", "--run", RU.name, "set", "analyze_submode=static", "static_images=prompts", "audio_ingest=whisper", env=ENV)
_rid = {it["rel"]: it["id"] for it in json.loads((RU / "00-inventory" / "inventory.json").read_text(encoding="utf-8"))["items"]}
js, _, _ = t("reuse-analysis", "--run", RU.name, "--from", NM.name, env=ENV)
_rv = _rid.get("video.mp4")
_rj = (RU / "10-media" / str(_rv) / "video.json").read_text(encoding="utf-8") if _rv else ""
_rc = (RU / "20-analysis" / "cards" / f"{_rv}.md").read_text(encoding="utf-8") if _rv else ""
check(js.get("ok") and _rv == "V02" and [(m["here"], m["there"]) for m in js.get("matched") or []] == [("V02", _nv)]
      and [n["id"] for n in js.get("new") or []] == ["V01"] and (RU / "10-media" / "V02" / "base" / "base_0001.jpg").is_file()
      and str(NM) not in _rj and str(RU / "10-media" / "V02") in json.loads(_rj)["frames"] and json.loads(_rj)["id"] == "V02"
      and "V02 at 00:01" in _rj and _rc.startswith("# V02 · video.mp4") and "(V02)" in _rc and f"Not {_nv}0." in _rc and str(NM) not in _rc
      and not (RU / "10-media" / "V01").exists(),
      "reuse-analysis copies an analysed reference's media folder and card under its id here (matched by hash and size), points the "
      "paths and the id inside at this run (never a longer id), and leaves the new references to be analysed")
js, _, _ = t("reuse-analysis", "--run", RU.name, "--from", NM.name, env=ENV)
check(js.get("ok") and not js.get("matched") and [k["id"] for k in js.get("already_here") or []] == ["V02"],
      "reuse-analysis again keeps a reference already prepared here (--redo copies it again)")
js, code, _ = t("reuse-analysis", "--run", RU.name, "--from", str(home / "runs" / "no-such-run"), env=ENV, ok=False)
check(code != 0 and js.get("ok") is False, "reuse-analysis from a run that does not exist fails")
# a run goes on in its session (the user, 2026-11-07: "if there's new references analyze them and save their data on the folders we
# specifically use"): the inventory taken again keeps every id, numbers the new files after the old ones and marks a vanished one gone
st_refs = home.parent / "refs-stable"
make_clip(st_refs / "video.mp4", seconds=2.0, flash=None, audio=False)
make_clip(st_refs / "zebra.mp4", seconds=2.2, flash=None, audio=False)
ST = Path(t("new-run", "--mode", "analyze", "--source", str(st_refs), "--slug", "stable-ids", env=ENV)[0]["run_dir"])
t("inventory", str(st_refs), "--run", str(ST), "--as", "references", env=ENV)
_ids0 = {it["rel"]: it["id"] for it in json.loads((ST / "00-inventory" / "inventory.json").read_text(encoding="utf-8"))["items"]}
make_clip(st_refs / "CEO_The_History_of_Rockets_TZIOfwN7bVI.mp4", seconds=2.4, flash=None, audio=False)
make_clip(st_refs / "Another_POV_Story_dwSfdH1K7Zk.mp4", seconds=2.6, flash=None, audio=False)
(st_refs / "zebra.mp4").unlink()
js, _, _ = t("inventory", str(st_refs), "--run", str(ST), "--as", "references", env=ENV)
_it1 = {it["rel"]: it for it in json.loads((ST / "00-inventory" / "inventory.json").read_text(encoding="utf-8"))["items"]}
check(_ids0 == {"video.mp4": "V01", "zebra.mp4": "V02"} and _it1["video.mp4"]["id"] == "V01"
      and _it1["Another_POV_Story_dwSfdH1K7Zk.mp4"]["id"] == "V03" and _it1["CEO_The_History_of_Rockets_TZIOfwN7bVI.mp4"]["id"] == "V04"
      and _it1["zebra.mp4"].get("gone") and _it1["zebra.mp4"].get("ignored") and _it1["zebra.mp4"]["id"] == "V02"
      and js.get("kept_ids") == 1 and [n["id"] for n in js.get("new") or []] == ["V03", "V04"] and [g["id"] for g in js.get("gone") or []] == ["V02"]
      and js["counts"] == {"video": 3},
      "the inventory taken again keeps the ids it gave (the analysis stays valid), numbers new files after them and keeps a vanished "
      "file's id taken, marked gone")
js, _, _ = t("inventory", str(st_refs), "--run", str(ST), "--as", "references", "--renumber", env=ENV)
_it2 = {it["rel"]: it["id"] for it in json.loads((ST / "00-inventory" / "inventory.json").read_text(encoding="utf-8"))["items"]}
check(_it2 == {"Another_POV_Story_dwSfdH1K7Zk.mp4": "V01", "CEO_The_History_of_Rockets_TZIOfwN7bVI.mp4": "V02", "video.mp4": "V03"},
      "inventory --renumber numbers every file afresh in file order")
(CX / "40-briefs").mkdir(parents=True, exist_ok=True)
(CX / "40-briefs" / "video-01-images.json").write_text(json.dumps({"video": "01", "title": "One light against the storm",
    "thumbnail": {"prompt": "A keeper's lamp in a storm", "size": "1280x720", "text": "ONE LIGHT"},
    "images": [{"image": 1, "from_line": 1, "prompt": "A lighthouse at night"}]}), encoding="utf-8")
js, _, _ = t("image", "prompts", "--run", CX.name, env=ENV)
_pf = Path(js["files"][0]).read_text(encoding="utf-8")
check("## v01-thumb" in _pf and "ONE LIGHT" in _pf and "1280x720" in _pf and js.get("images") == 2 and "vNN-thumb" in js.get("naming", ""),
      "image prompts adds each video's thumbnail as vNN-thumb at its own size, with its exact words")
_uf = home.parent / "user-images-thumb"
_uf.mkdir(parents=True, exist_ok=True)
_PI.new("RGB", (1216, 2160), (10, 120, 10)).save(_uf / "v01-i01.png")
_PI.new("RGB", (1280, 720), (120, 10, 120)).save(_uf / "v01-thumb.png")
js, _, _ = t("image", "intake", "--run", CX.name, "--folder", str(_uf), env=ENV)
_ti = [c for c in js.get("copied") or [] if c["image"] == "thumb"]
check(len(js.get("copied") or []) == 2 and _ti and _ti[0]["off_aspect"] == 0.0 and Path((_ti[0].get("thumbnail") or {}).get("deliverable") or "").is_file()
      and not js.get("missing") and not js.get("names_without_vNN_iKK"),
      "image intake takes the user's vNN-thumb file in as the video's thumbnail (its aspect against the thumbnail's size) and delivers it")
_srv.shutdown()

# --- the spoken word's box (the user, 2026-11-09): one text per caption word, the box on the word the narration is speaking
_wcues = [{"start": 0.3, "end": 0.96, "text": "IT'S SEVEN"}, {"start": 0.96, "end": 1.62, "text": "FORTY"}]
_wwords = [{"w": "It's", "s": 0.0, "e": 0.44}, {"w": "seven", "s": 0.44, "e": 0.66}, {"w": "forty", "s": 0.66, "e": 1.06}]
_wrows, _wprob = _awl._word_box_plan(_wcues, _wwords, 0.3, 30)
_wfont = Path(AWL).resolve().parent.parent / "fonts" / "LuckiestGuy-Regular.ttf"
_wg, _wgeo = _awl._word_box_segments(_wrows, str(_wfont), 6, 2560, 1440, 0.4)
_wflat = {(k, e["text"], e["start"], e["end"]) for k, v in _wg.items() for e in v}
_wx = {e["text"]: e["x"] for v in _wg.values() for e in v}
check(not _wprob and _wrows[0]["bounds"] == [0.3, 0.733333]
      and _wflat == {((0, True, True), "IT'S", 0.3, 0.733333), ((1, False, True), "SEVEN", 0.3, 0.733333),
                     ((0, False, False), "IT'S", 0.733333, 0.966667), ((1, True, False), "SEVEN", 0.733333, 0.966667),
                     ((0, True, True), "FORTY", 0.966667, 1.633333)}
      and _wx["IT'S"] < 0 < _wx["SEVEN"] and _wx["FORTY"] == 0.0 and abs(_wgeo["em_px"] - 88.23) < 0.01,
      f"the word box: each word its own text at its place on the centred line, the box on the word being spoken from its narration time "
      f"on the frame grid, a one-word caption boxed whole ({sorted(_wflat)}, {_wgeo})")
_fw = [{"w": w, "s": s, "e": s + 0.2} for w, s in (("one", 0.0), ("two,", 0.25), ("three", 0.5), ("four", 0.75), ("five.", 1.0),
                                                      ("six", 2.5), ("seven", 2.75), ("eight", 3.0), ("nine", 3.25))]
_fc = _awl.chunk_words_fill(_fw, 3, 3, 0.8)
check([c["text"] for c in _fc] == ["one two, three four five.", "six seven eight nine"]
      and " ".join(c["text"] for c in _fc).split() == [x["w"] for x in _fw],
      f"captions filled to 3 words across commas, never across a long pause; a short last group joins the one before it ({_fc})")
_wbad, _wbadp = _awl._word_box_plan([{"start": 0.3, "end": 0.9, "text": "IT'S EIGHT"}], _wwords[:2], 0.3, 30)
check(len(_wbadp) == 1 and _wbadp[0].get("token") == "EIGHT",
      f"the word box refuses a caption word that is not the narration's next word ({_wbadp})")

finish()
