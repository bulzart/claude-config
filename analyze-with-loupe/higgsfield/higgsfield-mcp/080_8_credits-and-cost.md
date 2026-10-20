## 8. Credits and cost

- Always preflight with `get_cost`. Prices vary by model, duration, resolution, mode and time.
  Observed 2026-09-30 [VERIFIED]:
  - `seedance_2_5` t2v, 5 s, 720p, 9:16: 35 credits
  - `cinematic_studio_3_0`, 8 s, 720p: 40 credits
  - `marketing_studio_video`, 15 s, 720p: 75 credits
- Higgsfield's pages list Genjutsu at 15 s = 40 / 104 / 144 credits (480 / 720 / 1080p). A
  Seedance 2.5 edit at 10 s 1080p = 90 [HF-DOC, Sept 2026].
- Seedance 2.5 `video_edit` is billed by the **source** video's duration [HF-TOOL].
- Before starting a set, sum the preflights. If the total is above ~2/3 of `balance`, say so in the
  plan.
- **Who asks before spending:**
  - **Analyze Mode** never pauses on cost. Its only permission question is a video over 30 s that
    needs 2+ generations (command A7b).
  - **Edit Mode** asks its "Go" question before the first submission, then pauses before any
    attempt whose preflight exceeds the config key `higgsfield.confirm_cost_above_credits`.
- `use_unlim`: omit it. If the response contains `unlim_choice`, ask the user and resubmit with their
  answer. Pass `true` only on an explicit request [HF-TOOL].

