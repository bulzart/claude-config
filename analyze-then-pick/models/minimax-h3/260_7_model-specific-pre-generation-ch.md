## 7. Model-specific pre-generation checklist
- [ ] One mode (never frames + references); Analyze vs Edit Mode known.
- [ ] `aspect_ratio:"9:16"`; `minimax_h3` `2K` or `minimax_h3_max` `768p`; frames 9:16; `atp.py conform` to
      720×1280 afterwards (§2.6).
- [ ] Reference limits (≤9 images, ≤3 videos ≤15 s, ≤3 audio ≤15 s, ≤12 total); every reference's role stated.
- [ ] Timeline fits `duration`; `[Shot 1]` untimed, later shots "At 00:0X.XXX"; camera as a sentence.
- [ ] Sound and music sentences present.
- [ ] Clean plate: no quoted non-dialogue strings, no symbols, no text-cueing genre words, closing sentence — or one
      deliberate short text event (§3.11c).
- [ ] Product: standalone refs, "never recolor", geometry lock; identity: one person per image.
- [ ] Asset size/grip, light and end states written (§3.14); slop guards (§5); `batch_size`; `get_cost: true`.
- [ ] QC with `atp.py qc --mode analyze|edit` (size, freezes, marks, text spelling), plus identity and product shape.

