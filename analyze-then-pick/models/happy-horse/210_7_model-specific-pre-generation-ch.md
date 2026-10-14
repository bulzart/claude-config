## 7. Model-specific pre-generation checklist
- [ ] `aspect_ratio:"9:16"`, `resolution:"720p"`; start frame exactly 9:16 and text-free; `atp.py conform` (§2.6).
- [ ] Prompt 20–60 words: subject, one paced action, setting/light, background movement, sound, camera cue last.
- [ ] Dialogue with lip-sync wording or "no dialogue"; "no music" if needed.
- [ ] One clean-plate clause; captions/hooks planned for post (`atp.py captions`); no Edit Mode on this model.
- [ ] Grip, light and end states (§3.14); slop guards (§5); `get_cost: true`.
- [ ] First output of the session through `atp.py qc --mode analyze` for the provider watermark (§3.11e).

