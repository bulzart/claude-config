## 2. Edit Mode: removing source text

### 2.1 Inventory (before planning the edit)
Sources: `10-media/<id>/ocr.json` (spans with `kind_hint`, `y_rel` and `caption_bands_y_rel`),
`timeline.md` (the text column per second), and the storyboard sheets (read every overlay by eye; OCR
misses stylised text and stickers).

For each element record:

| text | kind (overlay / in-scene) | position (y_rel, x) | time span | size vs. frame | over important content? | keep (user said so)? |
|---|---|---|---|---|---|---|

### 2.2 Choose the removal method (least destructive that fully removes it)

| situation | method |
|---|---|
| The edit model supports prompt-level removal (see the model guide §3.11d), e.g. `seedance_2_5` / `ad_multiplier` `video_edit`, `kling_video_edit`, `gemini_omni_flash_1_1` edit, `flux_3_video_edit` | One explicit **remove operation per text element** in the same edit request: "Remove only <the caption text band across the middle of the frame> from @Video1 and reconstruct the revealed area consistently with its immediate surroundings." Never include the first-party "Preserve every caption…" block |
| Small static overlay (handle, watermark, corner logo) on a simple background | Local `atp.py clean --delogo "x,y,w,h[@t0-t1]"` before upload. Inspect the result: `delogo` smears textured backgrounds, so if it does, use the model instead |
| The text sits in a removable band (meme bars, letterboxed title area) | `atp.py clean --crop "x,y,w,h"` keeping the picture, then `conform` / Higgsfield `reframe` back to 9:16 |
| Large or animated captions over the subject or the key action | **Clean-frame reconstruction:** regenerate the scene with a reference-to-video model, using the source as a video reference for motion, camera and timing only, with the edit's substitutions applied. Or run the edit model's removal first, then QC |
| A start-frame model is chosen | Pick a source moment without text, or clean the frame (image edit), and use it as the 9:16 start frame |
| The user asked to keep specific text | Preserve exactly that element; name it in the prompt as preserved, and remove everything else |

### 2.3 Verify
Run `atp.py qc --mode edit` (OCR) and view the storyboard. Any residual source text, ghosting or smear
means the check fails: pick the next method in §2.2.

