## 7. Model-specific pre-generation checklist
- [ ] Mode chosen (never frames + references; never frames + audio); Analyze vs Edit Mode known.
- [ ] `aspect_ratio:"9:16"`, `resolution:"720p"`; frames/sources already 9:16; `atp.py conform` afterwards (§2.6).
- [ ] Reference limits (≤10 images, ≤5 videos ≤15 s, ≤5 audio ≤15 s); input + output ≤30 s.
- [ ] References cited as "Image N / Video N / Audio N" in attach order, each with an adoption scope.
- [ ] "Generate single shot." or contiguous 3–5 s timed shots; camera clause before subject clause.
- [ ] Dialogue quoted with speaker or "No dialogue."; BGM specified or "No background music."
- [ ] Clean-plate line (§3.11b); in-frame text only if short and scene-bound; Edit Mode: removal pass first.
- [ ] Asset size/grip/occlusion, light direction and end states written (§3.14); slop exclusions included (§5).
- [ ] Size: the anchor is from the §5 passing list, or a size-and-place guide (§4.0 items 13–14) carries spot and size; the reckoning (neighbour ratio, depth, fraction of the frame, "No scale drift") is written as a check, and no wording retry follows a miss (`reference/anomaly-catalog.md` §2.7).
- [ ] Spot and camera: the spot passes `reference/generation-system.md` §4b.1c; a camera-lock sentence when the product is near a frame edge or the shot is handheld or an orbit; per-shot desk state; the one hand in frame named with the bare empty area, and the object a hand picks up.
- [ ] Identity image: cropped to the face when its clothing differs from the kept garment, the kept garment in positive words, a mirrored selfie flipped (`reference/anomaly-catalog.md` §2.17); the prepared source flipped as its card flags, captions and names left to the prompt (`reference/generation-system.md` §5c.2b).
- [ ] Label pixel budget (`reference/anomaly-catalog.md` §2.9): the wordmark at least about 25 px upright, or the limit written in the brief before generating.
- [ ] Posture, support and place (§3.14): flat on a bare surface by default, upright only for a reason the plan states, on a visible surface, out of a working hand's way, with the story reason; no lean on an invented prop; nothing on a thin sheet; the object that is picked up is named (`reference/anomaly-catalog.md` §2.16).
- [ ] Source surfaces: each printed surface of Video 1 that a guardrail or `generation-system.md` §9b names is replaced with a named concrete thing in the edit grammar, and the original is in the exclusion line (§3.14).
- [ ] Counts with numbers per shot; every use beat names the part, the preparation step and the contact point; one "Negative prompt list:" item per product for its own wrong use and count; no reference shows a later state than t=0 (`reference/anomaly-catalog.md` §3).
- [ ] `duration`, `generate_audio`, `enable_thinking` set deliberately; `get_cost: true`.
- [ ] QC with `atp.py qc --mode analyze|edit`: size, freezes, pseudo-text, corner marks, identity, product geometry; `--dense` on the plan's checkpoints: counts, the part and contact of every use, permanence across exits and cuts (`reference/anomaly-catalog.md` §4).

