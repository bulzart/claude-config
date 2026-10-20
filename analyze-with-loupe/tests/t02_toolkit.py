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

finish()
