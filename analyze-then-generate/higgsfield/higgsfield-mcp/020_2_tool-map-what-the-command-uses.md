## 2. Tool map (what the command uses)

| Purpose | Tool | Key parameters | Notes |
|---|---|---|---|
| Live catalog | `models_explore` | `action: list \| get \| search \| recommend`, `type:"video"`, `model_id`, `limit` | The source of truth for parameters, roles, durations and aspect ratios. Items carry `supports_unlim` [HF-TOOL] |
| Credits | `balance` | — | `{credits, subscription_plan_type}` [VERIFIED: 8,436 credits, "ultra", on 2026-09-30] |
| Spend ledger | `transactions` | `size`, `cursor` | spend / refund / grant / deduct rows; refunds appear for failed jobs |
| Upload a local file | `media_upload` → HTTP PUT → `media_confirm` | `files:[{filename, content_type}]` (1–20) → `upload_url`, `media_id`, `url` | See §4. The only upload path from Claude Code |
| Import a web file | `media_import_url` | `url` (HTTPS, ≤ 50 MB), `type` | Returns a confirmed `media_id` |
| List uploads | `show_medias` | `type:"image"\|"video"\|"audio"`, `size`, `cursor` | Reuse earlier uploads. **Observed 2026-09-30:** it failed in Claude Code with "Structured content does not match the tool's output schema" [VERIFIED], so keep your own `media_id` records in `state.json` and do not depend on this tool |
| Reusable references | `show_reference_elements` | `action: list \| get \| create`, `medias:[{id, url, type}]`, `category`, `name` ≤ 32 chars | "Elements": embed `<<<element_id>>>` in a prompt (§6) |
| Trained identity (images only) | `show_characters` | `action: list \| train \| status` | Soul ids work only with image models `soul_2` / `soul_cinematic`. Useful only to make start frames, never passed to video models [HF-TOOL] |
| Start frames / reference stills | `generate_image` | `model`, `prompt`, `medias`, `aspect_ratio`, `count` | For start-frame-only models (§7.3) and for turning several references into one consistent 9:16 first frame |
| Generate one video | `generate_video` | `params:{model, prompt, medias, duration, aspect_ratio, …model params, folder_id, get_cost, use_unlim}` | `get_cost:true` preflights **without submitting**. `count` 1 (2–4 = variants of identical settings, not used) [HF-TOOL] |
| Headless batch | `generate_video_batch` | `requests:[{index, params}]` (1–12, count fixed at 1, no `get_cost`) | Not used by default: the command runs one video at a time |
| Wait for jobs | `jobs_wait` | `jobs:[{index, job_id}]` (1–12), `timeout_seconds` 0–15 | Returns `status`, `result_url`, `thumbnail_url`, `all_terminal` [VERIFIED] |
| Inspect a past job | `show_generations`, `job_display`, `show_generation_by_ids` | — | History and gallery views. From the terminal, `show_generations {type:"video", size:5}` resolves an unknown submission outcome |
| Organise outputs | `list_workspaces`, `create_project`, `create_folder`, `list_projects`, `list_project_assets` | `create_project {name, workspace_id, idempotency_key}` → `project_id`, `default_folder_id` | One project per run. Pass `folder_id` on every generation |
| Reframe to 9:16 | `reframe` | `params:{medias:[{role:"video", value}], aspect_ratio:"9:16", resolution, duration_seconds, get_cost}` | AI expand/reframe of an existing video (≤ 60 s; over 15 s needs `duration_seconds` + `resolution` and only the source video) [HF-TOOL] |
| Motion transfer (legacy) | `motion_control` | `image_id`, `motion_video_id`, `resolution`, `scene_control` | Kling 3.0 Motion Control. Prefer `generate_video` with `hf_mult_motion_control` [HF-TOOL] |
| Scene analysis (optional) | `video_analysis_create` → `video_analysis_status` | `video_input_id` or `youtube_url` | Remote second opinion, 3–5 min, accuracy drops on long clips. Credit cost unknown, so use only when the user asks |
| Virality score (optional) | `virality_predictor` | `action:"create"`, `params:{model:"virality_predictor", medias:[{role:"video", id}]}` | Only on the user's request; cost unknown |
| Background removal | `remove_background` | `media_id`, `media_type` | E.g. a clean product cutout |
| Upscale | `upscale_video` | bytedance (needs source w/h) or topaz | Not needed for 720p deliverables |

Not used: websites, 3D scene builder, TikTok publishing, voices, presets, and Marketing Studio widgets.
Those need the user's explicit request.

