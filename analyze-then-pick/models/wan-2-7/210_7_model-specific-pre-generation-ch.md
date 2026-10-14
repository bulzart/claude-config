## 7. Model-specific pre-generation checklist
- [ ] Mode: text / text+audio / start frame / start+end frame (+audio); `end_image` only with `start_image`.
- [ ] `aspect_ratio:"9:16"`, `resolution:"720p"`; frames exactly 9:16, identical size, text-free; `atp.py conform`
      afterwards (§2.6).
- [ ] "Generate a single-shot video" or explicit timed shots with shot sizes.
- [ ] t2v covers entity, scene, motion, aesthetic control, style; i2v covers motion + camera only.
- [ ] Sound described or suppressed; audio length matches `duration`.
- [ ] Clean-plate sentence (§3.11b); captions/hooks planned for post (`atp.py captions`); no Edit Mode on this id.
- [ ] Asset size/grip, light continuity and end states written (§3.14); slop guards (§5).
- [ ] Prompt ≤5,000 characters; `get_cost: true`.
- [ ] QC with `atp.py qc --mode analyze`: size, freezes, pseudo-text, corner marks, identity, product shape.

