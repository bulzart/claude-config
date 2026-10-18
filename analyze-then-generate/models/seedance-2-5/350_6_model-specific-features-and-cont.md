## 6. Model-specific features and controls

- 30 s single pass, integer-second timestamps, multi-view subject images, locked vs unlocked tasks (edit/first-frame/extension lock the ratio) [OFFICIAL S2].
- Draft → final (`draft`, `draft_job_id`, `seedance_2_5` only): 480p preview, 1080p final within 7 days — needs a downscale for this project [OFFICIAL S3; HF S11].
- Clay-model rendering, storyboard grids (≤15 panels), multi-keyframe order, seamless transition between two videos ("Do not alter the two uploaded videos themselves"), one-click video [OFFICIAL S2].
- Editing: add/modify/remove incl. subtitles and watermarks, reference-image edits, audio edits and translation with lip re-sync, timestamp-scoped edits [OFFICIAL S2]; marketed as green-screen and camera-perspective editing [OFFICIAL S1].
- `bitrate_mode:"high"` for finals; `ad_multiplier` for Higgsfield's multi-variant edit workflow ("multiple edits of one clip") [HF S11, S12, S13].
- Official prompt optimizer `sd25-pe` (templates in §4) [OFFICIAL S2, S7]. Not on Higgsfield: seed, negative prompt, camera_fixed, MOV, last-frame return, Elements, watermark toggle [HF S11, S12].

