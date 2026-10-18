## 7. Model-specific pre-generation checklist

- [ ] `gemini_omni_flash_1_1` preferred; `gemini_omni` availability re-checked (upstream deprecation 2026-09-30).
- [ ] `aspect_ratio: "9:16"`, `resolution: "720p"`; `mode` matches the media.
- [ ] Edit Mode: source conformed to 9:16, ≤10 s, one video; text-removal pass first; "Keep everything else the same."
- [ ] Start/end frames conformed to 9:16; references ≤7, each bound by tag plus description; guiding sentence present.
- [ ] "Single continuous shot / No scene cuts" unless cuts are wanted; duration fits the action.
- [ ] Integration: scale, grip, contact shadow, light inheritance, persistent states; ANTI-SLOP line for inserts.
- [ ] Text: clean-plate negatives; intentional scene text as `says: "…"` (short) or in post; colon dialogue.
- [ ] `get_cost` done; output probed (720×1280) and QC'd (text residue, identity, geometry, cuts).

