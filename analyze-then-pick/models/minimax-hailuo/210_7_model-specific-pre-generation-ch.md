## 7. Model-specific pre-generation checklist
- [ ] 9:16 start frame ready (text-free, ≥300 px short edge); no text-to-video for deliverables.
- [ ] Variant chosen (2.3 quality, 2.3-fast drafts, `minimax` for first+last); `"768"` or `"1080"` (6 s); never
      `"512"` for deliverables.
- [ ] First/last frames identical size; `end_image` only on `minimax`.
- [ ] Prompt 20–70 words, physical verbs, bracket after each clause, end state.
- [ ] One short no-text sentence; captions/hooks planned for post (`atp.py captions`); no Edit Mode on this id.
- [ ] Grip, light and end states written (§3.14); slop guards (§5); silence accepted; `get_cost: true`.
- [ ] After generation: `atp.py conform` to 720×1280, then `atp.py qc --mode analyze` (size, freezes, pseudo-text,
      corner marks), identity and product shape.

