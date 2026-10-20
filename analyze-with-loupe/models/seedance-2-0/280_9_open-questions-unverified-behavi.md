## 9. Open questions / unverified behaviour

- What `genre` changes and whether it overrides prompt style.
- Whether an edit/extension-intent prompt with `video_references` triggers ByteDance's 2.0 edit/extension subtasks through Higgsfield.
- Actual Higgsfield reference cap (12 vs 9 + 3 + 3) and whether `start_image` can be mixed with `*_references`.
- Numbering of Element images relative to `@ImageN` in the same call.
- Whether Higgsfield returns exactly 720×1280 for `9:16` + `720p` (official grid says yes) and how a non-9:16 start frame is handled there.
- Real-face reference handling on Higgsfield for this id; spurious-subtitle rate at 9:16.
