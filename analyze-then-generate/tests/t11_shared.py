import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t11_common import *
import importlib.util as _iu

_spec = _iu.spec_from_file_location("atg_inproc", ATG)
atg = _iu.module_from_spec(_spec)
_spec.loader.exec_module(atg)
FF = atg.find_tool("ffmpeg")
W = Path(tempfile.mkdtemp(prefix="atg-shared-"))


def sh(*cmd):
    cp = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding="utf-8")
    if cp.returncode != 0:
        print("ffmpeg failed:", cp.stderr[-500:])
        sys.exit(1)


# ---- test material: a moving picture with a sound, the same picture late, a landscape one, a picture with big text
sh(FF, "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=s=360x640:d=5:r=15", "-f", "lavfi", "-i", "sine=frequency=330:duration=5", "-shortest", "-pix_fmt", "yuv420p", W / "src.mp4")
sh(FF, "-y", "-loglevel", "error", "-i", W / "src.mp4", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", W / "same.mp4")
sh(FF, "-y", "-loglevel", "error", "-i", W / "src.mp4", "-an", "-vf", "tpad=start_duration=0.4:start_mode=clone", "-t", "5", "-c:v", "libx264", "-pix_fmt", "yuv420p", W / "late.mp4")
sh(FF, "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=s=640x360:d=3:r=15", "-pix_fmt", "yuv420p", W / "wide.mp4")
from PIL import Image, ImageDraw
im = Image.new("RGB", (360, 640), (20, 20, 20))
dr = ImageDraw.Draw(im)
dr.text((20, 300), "SALE 50 OFF", fill=(255, 255, 255), font=atg._font(46))
im.save(W / "text.png")
sh(FF, "-y", "-loglevel", "error", "-loop", "1", "-i", W / "text.png", "-t", "3", "-r", "10", "-pix_fmt", "yuv420p", W / "text.mp4")

# ================================================================ sync-check: numbers, no verdict, no fix
ok_, rc, _ = t("sync-check", "--source", W / "src.mp4", "--output", W / "same.mp4", "--out", W / "sync-same", "--fps", "15")
late, rc2, _ = t("sync-check", "--source", W / "src.mp4", "--output", W / "late.mp4", "--out", W / "sync-late", "--fps", "15")
check(rc == 0 and rc2 == 0, "sync-check exits 0 whenever it measured (a late output is not an error)")
check(not any(k in ok_ or k in late for k in ("verdict", "fix")) and "reliable" not in json.dumps(late) and late["ok"] is True, "no verdict, no fix, no 'reliable' label")
check(abs(ok_["global_offset_s"]) <= 0.07 and ok_["windows_beyond_tolerance"] == [], "the same picture: offset about 0 and no window beyond the tolerance: " + str(ok_["global_offset_s"]))
check(0.3 <= late["global_offset_s"] <= 0.5 and 0.3 <= late["median_window_offset_s"] <= 0.5 and late["windows_beyond_tolerance"], "the picture 0.4 s late: the offsets say about +0.4 s (positive = the output is later): " + str((late["global_offset_s"], late["median_window_offset_s"])))
check(late["filters"] == {"min_corr": 0.5, "min_motion_ratio": 0.25} and late["windows_used"] <= late["windows_total"] and all("motion_ratio" in w and "corr" in w for w in (late["windows"] or [])),
      "every window is listed with its correlation and motion; the filters that select the summary are stated")
late2, rc, _ = t("sync-check", "--source", W / "src.mp4", "--output", W / "late.mp4", "--out", W / "sync-late2", "--fps", "15", "--tol", "0.6", "--min-corr", "0.0", "--min-motion", "0.0")
check(late2["windows_beyond_tolerance"] == [] and late2["windows_used"] == late2["windows_total"], "--tol only changes the LIST of windows beyond it; --min-corr 0 and --min-motion 0 use every window")
check((W / "sync-late" / "sync-sheet.jpg").exists(), "the side-by-side sheet is written")

# ================================================================ qc: measurements beside expectations
q, rc, _ = t("qc", "--video", W / "src.mp4", "--out", W / "qc1", "--expect-size", "360x640", "--expect-aspect", "9:16", "--expect-duration", "4", "--allowed-text", "SALE|20%", "--no-ocr")
ck = q["checks"]
check(rc == 0 and q["ok"] is True and not any(k in q for k in ("passed_automatic_checks", "problems")) and not any(k in ck for k in ("problems", "size_ok", "unexpected_text", "ocr_noise_ignored", "text_policy")),
      "qc has no pass/fail, no problems list, no 'unexpected text' comparison")
check(ck["size"] == "360x640" and ck["size_delta_px"] == [0, 0] and ck["duration_delta_s"] == 1.0 and ck["expected"]["size"] == "360x640" and ck["planned_text"] == ["SALE", "20%"] and ck["mode"] == "analyze",
      "qc reports the size, the delta against the expected size, the duration delta and the planned text beside each other: " + str((ck["size"], ck["size_delta_px"], ck["duration_delta_s"])))
q2, rc, _ = t("qc", "--video", W / "text.mp4", "--out", W / "qc2", "--expect-size", "720x1280", "--allowed-text", "SALE")
ck2 = q2["checks"]
vt = ck2["visible_text"]
check(ck2["size_delta_px"] == [-360, -640] and ck2["black_spans"] is not None and isinstance(ck2["freeze_starts"], list), "a video of another size: the delta is just the numbers, nothing is refused")
check(vt and any("SALE" in s["text"].upper() for s in vt) and all(k in vt[0] for k in ("first_t", "last_t", "hits", "share_of_frames_scanned", "y_rel", "score_mean", "chars")) and not any("kind_hint" in s or "likely_noise" in s for s in vt),
      "the on-screen text the OCR saw comes with how often, where and how confident, and no label: " + str(vt[:1]))

# ================================================================ OCR spans: numbers, no labels
frames = [{"t": float(i), "file": str(W / "text.png"), "ok": True} for i in range(5)]
oc = atg.ocr_frames(frames)
sp = oc["spans"][0] if oc.get("spans") else {}
check(oc.get("available") and sp and all(k in sp for k in ("hits", "share_of_frames_scanned", "band_distinct_texts", "band_frames", "score_mean", "chars", "words", "has_at_handle", "has_hashtag", "has_url_pattern"))
      and "kind_hint" not in sp and "likely_noise" not in sp and "caption_bands_y_rel" not in oc and "bands" in oc and sp["share_of_frames_scanned"] == 1.0, "OCR spans carry numbers and spelling facts, no kind_hint / likely_noise / caption-band label: " + str(sp))

# ================================================================ scale: arithmetic, no verdict
s1, rc, _ = t("scale", "--product-cm", "15.7", "--distance", "1.5", "--lens", "26", "--product-px", "100", "--ref-cm", "22", "--ref-px", "140", "--distance-basis", "the table edge")
check(not any(k in s1 for k in ("verdict", "verdict_base", "provisional", "provisional_reason", "reading", "deviation_basis")), "scale has no verdict, no provisional flag, no reading")
exp_frac = 0.157 * 26 / (36 * 1.5)
check(abs(s1["expected_fraction_of_frame_height"] - round(exp_frac, 4)) < 1e-4 and abs(s1["size_vs_distance"] - round((100 / 1280) / exp_frac, 3)) < 1e-3 and abs(s1["size_vs_neighbour"] - round((100 / 140) / (15.7 / 22), 3)) < 1e-3,
      "the geometry is plain arithmetic: " + str((s1["size_vs_distance"], s1["size_vs_neighbour"])))
check([e["basis"] for e in s1["estimates"]] == ["neighbour ratio", "distance+lens fraction"] and "estimates_spread_pct" in s1 and s1["distance_basis"] == "the table edge", "two estimates, how far apart they are, and the basis of the distance as stated")
s2, rc, _ = t("scale", "--product-cm", "15.7", "--distance", "1.5", "--product-px", "400")
check(len(s2["estimates"]) == 1 and s2["estimates"][0]["size_factor"] > 4 and s2["distance_basis"] is None and any("distance-basis" in n for n in s2["notes"]), "a huge product is just a big number (4x), no 'regenerate'; the missing basis is a form note")

# ================================================================ conform: reports the loss, never refuses
c1, rc, _ = t("conform", "--video", W / "wide.mp4", "--out", W / "conf-dry.mp4", "--dry-run")
check(c1["dry_run"] is True and c1["lost_fraction"] > 0.6 and not (W / "conf-dry.mp4").exists(), "--dry-run reports the share of the picture a crop would lose (" + str(c1["lost_fraction"]) + ") and writes nothing")
c2, rc, _ = t("conform", "--video", W / "wide.mp4", "--out", W / "conf.mp4")
check(c2["ok"] and c2["output"] == "720x1280" and c2["lost_fraction"] > 0.6 and (W / "conf.mp4").exists(), "a big crop is NOT refused: the agent decides; the output is exactly 720x1280")
t_ = t("conform", "--video", W / "wide.mp4", "--out", W / "conf2.mp4", "--max-crop", "0.1", ok=False)
check(t_[1] == 2, "--max-crop no longer exists")

# ================================================================ split-audio, restore-audio, finalize: facts, no gates
folder = W / "editsrc"
folder.mkdir()
shutil.copy2(W / "src.mp4", folder / "clip.mp4")
nr, rc, _ = t("new-run", "--mode", "edit", "--source", folder, "--slug", "shared", "--runs-root", W / "runs")
RUN = nr["run_dir"]
sp_, rc, _ = t("split-audio", folder, "--run", RUN)
man = json.loads((Path(RUN) / "00-inventory" / "audio-split.json").read_text(encoding="utf-8"))["entries"][0]
ra, rc, _ = t("restore-audio", "--generated", W / "same.mp4", "--audio", man["audio"], "--audio-offset", man["audio_offset"], "--out", W / "restored.mp4")
fa = ra["facts"]
check(ra["ok"] and "gates" not in ra and fa["has_video"] and fa["has_audio"] and fa["audio_was_available"] and fa["size"] == "360x640" and ra["generated_shorter_by_s"] == 0.0, "restore-audio reports facts, not gates: " + str(fa))
fz, rc, _ = t("finalize", "--run", RUN, "--file", W / "restored.mp4", "--original", man["original"], "--video", "01")
check(fz["ok"] and fz["facts"]["size"] == "360x640" and fz["facts"]["expected_size"] == "720x1280" and "checks" not in fz and Path(fz["final"]).exists(), "finalize does not refuse a file of another size: it places it and reports the facts beside the expectation")
fz2, rc, _ = t("finalize", "--run", RUN, "--file", W / "restored.mp4", "--original", man["original"], "--video", "01", "--force", ok=False)
check(rc == 2, "--force no longer exists (there is nothing to force)")

# ================================================================ ledger: records and reports, never refuses
req = W / "req.json"
req.write_text(json.dumps({"params": {"model": "m1", "prompt": "a"}}), encoding="utf-8")
req2 = W / "req2.json"
req2.write_text(json.dumps({"params": {"model": "m1", "prompt": "b"}}), encoding="utf-8")
b1, rc, _ = t("ledger", "begin", "--run", RUN, "--video", "01", "--request", req)
check(b1["ok"] and b1["recorded"] and b1["conflicts"] == [] and b1["open_in_run"] == 1, "the first submission is recorded with no conflict")
b2, rc, _ = t("ledger", "begin", "--run", RUN, "--video", "01-c2", "--request", req2)
check(rc == 0 and b2["ok"] and b2["recorded"] and [c["what"] for c in b2["conflicts"]] == ["an open submission in this video's lane"] and "blocked" not in b2, "a second submission in the same lane is RECORDED and the conflict is reported (exit 0): the agent decides")
t("ledger", "set", "--run", RUN, "--fingerprint", b2["fingerprint"], "--status", "superseded", "--note", "I decided not to submit: one job per video")
t("ledger", "set", "--run", RUN, "--fingerprint", b1["fingerprint"], "--status", "completed", "--job", "job-1")
b3, rc, _ = t("ledger", "begin", "--run", RUN, "--video", "01", "--request", req)
check(rc == 0 and b3["recorded"] and any("finished job" in c["what"] for c in b3["conflicts"]), "the same request again after a finished job: recorded, with the finished job named in the conflicts")
t("ledger", "set", "--run", RUN, "--fingerprint", b3["fingerprint"], "--status", "failed", "--job", "job-2")
t("ledger", "set", "--run", RUN, "--fingerprint", b3["fingerprint"], "--status", "failed", "--job", "job-3")
b4, rc, _ = t("ledger", "begin", "--run", RUN, "--video", "02", "--request", req, "--max-open", "1")
check(rc == 0 and b4["cap"] == 1 and b4["recorded"], "begin reports against a cap the caller names (and refuses nothing)")
sw, rc, _ = t("ledger", "show", "--run", RUN)
check(len(sw["entries"]) == 4, "all four entries are on record: " + str(len(sw["entries"])))
t_ = t("ledger", "begin", "--run", RUN, "--video", "03", "--request", req, "--allow-repeat", ok=False)
check(t_[1] == 2, "--allow-repeat no longer exists")

# ================================================================ model menu and inventory
mm, rc, out_ = t("model-menu", "--mode", "edit")
check("quick_picks" not in mm and isinstance(mm["pinned"], list) and mm["numbers"] and "quick picks" not in out_.lower(), "the model menu is a table plus the pins: no quick picks")
assets = W / "assets"
assets.mkdir()
for nm in ("logo.png", "front.jpg"):
    Image.new("RGB", (40, 40), (200, 10, 10)).save(assets / nm)
(assets / "brand-guide.txt").write_text("colours", encoding="utf-8")
iv, rc, _ = t("inventory", assets, "--run", RUN, "--as", "assets", "--scope", "project")
items = json.loads((Path(RUN) / "30-assets" / "project" / "asset-inventory.json").read_text(encoding="utf-8"))["items"]
md_inv = (Path(RUN) / "30-assets" / "project" / "asset-inventory.md").read_text(encoding="utf-8")
check(items and not any("name_hints" in it for it in items) and "name hints" not in md_inv and "logo?" not in md_inv, "the inventory does not guess what a file is from its name")

finish()
