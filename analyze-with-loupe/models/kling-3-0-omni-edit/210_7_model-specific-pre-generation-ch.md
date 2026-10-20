## 7. Model-specific pre-generation checklist

- [ ] Source: one clip, 3–10 s, ≤200 MB, ≤2K, cut on hard cuts, reframed to 9:16 720×1280; text regions and times listed.
- [ ] `mode:"std"`; no `duration`/`aspect_ratio` sent.
- [ ] ≤4 reference images (≥300 px, ≤10 MB, jpg/png), cropped to the target, in citation order.
- [ ] Kling edit structures; `@Video1`/`@ImageN` plus plain-language targets; one or two operations per call.
- [ ] Every source text element named in a remove sentence (removal-only pass first if large); "No new text…" line; no Higgsfield preservation block.
- [ ] Integration line: size, grip, orientation, scene light, shadow; persistent states named.
- [ ] Person replacement has the exclusion sentence; product replacement states rigidity and size.
- [ ] `get_cost:true` preflight; post: ffprobe, conform ratio/duration, restore source audio, frame QA.

