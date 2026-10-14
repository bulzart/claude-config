## 7. Model-specific pre-generation checklist
- [ ] `aspect_ratio:"9:16"`, `quality:"720p"` (not `resolution`); 9:16 reference images; `atp.py conform` (§2.6).
- [ ] Duration 5 or 10 s when references are attached.
- [ ] Prompt ≤1,500 characters, one continuous shot, events in order.
- [ ] Each reference = one subject, free of captions/usernames/watermarks; tags `character1…` in `medias` order; ≤3.
- [ ] Voice from a reference video wanted? Clean-speech clip; otherwise describe the voice.
- [ ] Clean-plate sentence; captions/hooks planned for post (`atp.py captions`); no Edit Mode on this model.
- [ ] Grip, light and end states written (§3.14); slop guards (§5).
- [ ] `get_cost: true`; QC with `atp.py qc --mode analyze` (size, freezes, pseudo-text, corner marks, identity).

