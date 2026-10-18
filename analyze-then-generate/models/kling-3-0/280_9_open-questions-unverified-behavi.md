## 9. Open questions / unverified behaviour

- Exact output dimensions of `kling3_0` `std` and Turbo `720p` at 9:16 (720×1280 expected) and whether `4k` is native.
- Whether prompt-level `Shot N` labels produce cuts without the multi-shot switch, and whether undocumented multi-shot keys are accepted.
- Whether `start_image` + Elements is accepted and how Elements count toward Kling's image limits.
- Whether Turbo returns an audio track on Higgsfield and whether it can be muted server-side.
- Whether `end_image` without `start_image` is accepted.
- Behaviour when the start frame's ratio differs from `aspect_ratio` (crop, pad or reject).
- Semantics of `motion_control` `scene_control` vs Kling's orientation option, its duration caps and output aspect.
- Spelling accuracy of newly generated text (no independent test found).
