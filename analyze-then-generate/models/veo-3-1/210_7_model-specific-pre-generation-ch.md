## 7. Model-specific pre-generation checklist

- [ ] Catalog re-checked; upstream preview shutdown (2026-10-22) considered.
- [ ] `aspect_ratio: "9:16"`; `veo3_1` uses `quality: "basic"`; Lite never `auto`.
- [ ] Start and end frames conformed to 9:16 (≥720×1280), adults only, no famous people, subject centered.
- [ ] Shot fits 4/6/8 s with one action spanning the duration (no dead space); "real-time pace".
- [ ] Start-frame prompt is motion-only, with separate camera, subject and environment sentences.
- [ ] Dialogue in colon form with a visible speaker, sized to duration, or none.
- [ ] Clean plate: blank surfaces plus closing sentence. Analyze-Mode text planned for post, not in-frame.
- [ ] Integration phrases: scale, contact, grip, light direction and temperature, shadow, persistent states.
- [ ] `get_cost` done. Output ffprobed (720×1280? audio as intended?) and QC'd for text, identity, geometry and cuts.

