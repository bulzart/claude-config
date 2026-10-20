---
name: atp-product-colours-and-preview
description: "ATP videos: the client's pack must keep its printed colours at full strength (user rejected a \"faded\" Neurogum pack), and deliverable previews must be full 720x1280, never a 540x960 proxy"
metadata:
  node_type: memory
  type: feedback
  originSessionId: c526b948-969c-4e72-9f98-5c37655ed79a
  modified: 2026-10-20T19:26:13.559Z
---

On 2026-10-14 (run 20261013-230824-13, video 02) the user opened `deliverables/video-02-preview.mp4` and said: "the placement is good but the neurogums pack doesnt look correct and is a bit faded". Measured: the carton face was sat 0.38 / value 0.60 against the real render's 0.71 / 0.88, with wrong letters on the small label; the preview was also a soft 540x960 capcut-cli proxy.

**Why:** the blend wording in the plans ("matte paperboard", "colours no brighter than the room", "as muted as the room's") made Seedance/Wan render the product dull. The client rule is to copy the real packaging exactly (GN10), so only the product's light and contact shadow may follow the room, never its printed colours.

**How to apply:**
- In every product clause write the printed colours "exactly as in the image at full strength, not washed out, not faded"; never "muted" or "no brighter than the room". Measure the pack's face saturation/value against the render in QC (Neuro teal about sat 0.65 / value 0.85).
- If the model still renders it dull and the product is static in a locked shot, the allowed fix is the catalog's local recolour on the tracked product only (feathered mask, drift under 2 px); never paste the render, never upscale.
- `deliverables/video-NN-preview.mp4` is a 720x1280 ffmpeg burn of the CapCut text layer (CapCut en.ttf, crf 16-18, original audio stream-copied); `capcut render` crashes on fontconfig here and its proxy is 540x960.
- Caption size in that burn (calibrated 2026-10-20 on the user's real CapCut cover `03_Oct_2026_v09/draft_cover.jpg`, 1080x1920): the house text (size 10, System font) is about 52 px per em on a 720-wide frame, a 29-character line spans 89 % of the width, line pitch 0.034 of the frame height (43 px at 1280). `T captions` size 50, outline 2.5, one event per line at pitch 0.033 matches it within 3 %; capcut-cli's mapping "size 10 = 20 px at 720" is wrong (halves the block), and agents that picked their own sizes (20-52) made inconsistent previews. Plan every caption block at that real size: lines of at most 30 characters, block = lines x 43 px inside rows 180-832, off faces, hands and the can. Helper used in run 20261019: `atg-work/make_preview.py NN` (reads the CapCut draft's text layers).
- Lessons this run produced for the references (put them into the references when asked): Seedance `video_edit` replaces the whole person with the reference's complete look, so use the full-look photo and Higgsfield's person-replacement wording (a head crop swapped only the hair); a face of about 100 px does not follow the identity image at all.

Related: [[neurogum-package-forms]], [[atp-deliverables-one-folder]].
