---
guide: higgsfield-mcp
title: Higgsfield MCP — operations guide for /analyze-then-pick
last_verified: 2026-09-30
server: higgsfield → https://mcp.higgsfield.ai/mcp (HTTP transport, OAuth; no API key)
catalog_snapshot: higgsfield/catalog-snapshot-2026-09-30.json
---

# Higgsfield MCP — operations guide

Everything here was taken from the tool contracts loaded in Claude Code on 2026-09-30, the live
`models_explore` catalog, Higgsfield's first-party recipes (copied to `first-party/`), Higgsfield's
public pages, and **zero-cost calls actually made**: `models_explore list/get`, `get_cost` preflights,
`balance`, `show_generations`, `jobs_wait` on a completed job, `show_reference_elements list`,
`get_workflow_instructions`, `get_workflow_bundle_file`, `get_preset_instructions`. Tags:
**[HF-TOOL]** tool schema or description · **[HF-DOC]** first-party recipe or page ·
**[VERIFIED]** observed in a real response · **[INFERRED]** engineering inference.

## 1. Connection and conventions

| Item | Value |
|---|---|
| MCP server | `higgsfield` (user scope, `~/.claude.json`), `https://mcp.higgsfield.ai/mcp`, OAuth through the Higgsfield account [VERIFIED] |
| Tool names | `mcp__higgsfield__<tool>`. All are **deferred**: load their schemas first with `ToolSearch "select:mcp__higgsfield__generate_video,…"`. If the account uses the claude.ai connector instead, the prefix differs (e.g. `mcp__claude_ai_Higgsfield__`); discover it with `ToolSearch "+higgsfield generate_video"` and never hard-code it |
| Auth problems | The tools are missing, or the only ones are `authenticate` / `complete_authentication` → ask the user to run `/mcp`, pick **higgsfield**, then **Authenticate** (or run `! claude mcp login higgsfield`). Then reload the tool schemas |
| Client type | Claude Code has **no Apps UI**. Never call widget-only tools: `media_upload_widget`, `show_marketing_studio_v2`, the `get_presets` widget flow. `generate_video` still returns job ids; the widget part is simply not shown [HF-TOOL] |
| "Workflows" | Higgsfield calls its server-side instruction bundles "workflows" (`get_workflow_instructions`). They are documentation recipes, not Claude Code Workflows. The knowledge /analyze-then-pick needs is already copied in `first-party/`. The command never calls the Claude Code Workflow tool |
| Remote sandbox | `sandbox_exec` is a remote Linux sandbox with ffmpeg. /analyze-then-pick does not use it: every media operation runs locally with FFmpeg (`scripts/atp.py`) |

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

## 3. Standard execution sequence for one video

Every video is a **lane** with one job in flight. Inside a lane, finish, download and QC each clip
before submitting the next.
- **Edit Mode** runs one video at a time.
- **Analyze Mode** runs one production agent per video, at most 5 at once
  (`reference/production-agents.md`).
- The ledger caps the run at `production.max_parallel_jobs` (5) jobs in flight.

1. **Model entry.** Read `models/index.json` for the selected `model_id`, then read its guide.
   Call `models_explore {action:"get", model_id}` once per run. If the live parameters, roles or ranges
   differ from the guide, the live catalog wins; note the drift in the run log.
2. **Project folder, once per run.** `list_workspaces` → the `is_selected` workspace. Then
   `create_project {name:"atp <run-id>", workspace_id, idempotency_key:"<run-id>"}` and store
   `project_id` and `default_folder_id` in `state.json`. Retry an uncertain create only with the same
   idempotency key.
3. **Inputs.** Upload each needed file once per run (§4) and store `{local path, sha1 → media_id, url}`
   in `state.json → assets.uploads`. Reuse media ids and completed job ids across videos.
4. **Params.** Assemble them from the model guide's call recipe:
   - `model`, `prompt`, `medias[{value: media_id | job_id, role}]`
   - `duration`, `aspect_ratio:"9:16"` and the model's own 720p setting (§7)
   - the model-specific parameters, and `folder_id`
   `medias[].value` is **never a URL** [HF-TOOL].
5. **Preflight.** `generate_video {params:{…, get_cost:true}}` → `{cost:{credits}, adjustments}`
   [VERIFIED]. Read `adjustments`: it names every parameter the server defaulted or changed. If it
   changed something that matters (e.g. audio default, duration clamp), fix the params and preflight
   again. Show the cost in the per-video brief.
6. **Submit (ledger-guarded).** Run `atp.py ledger begin --run <run> --video NN --attempt K
   --request <request.json>` first.
   - Exit 3 means **do not submit**: an open job must be resolved first, the request duplicates a
     finished job, or the request already failed twice.
   - Otherwise make exactly one `generate_video {params:{…}}` call, with `get_cost` removed and
     `count` 1.
   - Immediately record the job id with `atp.py ledger set --fingerprint F --job J --status
     submitted`, or `--status unknown` if no job id came back, **before** polling.
   - Nothing is ever submitted in parallel or "just in case".
   - `unlim_choice` in the response → nothing was submitted; ask the user its exact question, then
     resubmit with `use_unlim` set.
   - `recovery_tool` → call it immediately (e.g. `show_plans_and_credits` when credits are short).
   - A transport timeout → the outcome is unknown; **do not resubmit**. Check `show_generations`
     and `transactions` first [HF-TOOL].
7. **Poll.** `jobs_wait {jobs:[{index:0, job_id}], timeout_seconds:15}`; repeat while
   `all_terminal:false`, waiting `poll_after_seconds` when given. Typical jobs take 1–4 min; long 1080p
   jobs can take 10+ min.
8. **Download.** `atp.py hf-get --url <result_url> --out <run>/60-outputs/<nn>/raw.mp4`. It streams
   with retries and verifies with ffprobe. Result URLs are public CloudFront links
   (`https://d8j0ntlcm91z4.cloudfront.net/user_<id>/hf_<date>_<time>_<job_id>.mp4`) [VERIFIED];
   download immediately.
9. **Post-process locally.** In order, as the plan requires:
   - `restore-audio`: Edit Mode silent edits get the source audio back;
   - `conform`: exact 720×1280, no stretching;
   - Analyze Mode text and inserts: placed in the video's CapCut project
     (`reference/capcut-assembly.md`); `captions` is only the fallback;
   - `qc`.
   See `reference/text-and-format.md`.
10. **Failures.**
    - A failed job is refunded (it shows in `transactions`). Retry once with the same or corrected
      params, and never create a duplicate of a pending job.
    - A second failure → report it and continue with the next video.

## 4. Local file upload (terminal path)

```text
1. mcp__higgsfield__media_upload {files:[{filename:"<name>.png", content_type:"image/png"}, …]}   (≤ 20 per call)
   → uploads[i] = {upload_url (S3 presigned PUT, ~24 h), media_id (UUID), url (public CDN URL), content_type}
2. python atp.py hf-put --file "<local path>" --url "<upload_url>" --content-type "<exact content_type from step 1>"
   → {"ok": true, "status": 200}
3. mcp__higgsfield__media_confirm {type:"image", media_ids:[…]}   (one media type per call; only after HTTP 200)
```

- `Content-Type` is part of the signature and must equal the returned `content_type`. A mismatch returns
  S3 403 `SignatureDoesNotMatch`; request a fresh slot [VERIFIED in the 2026-09-16 research].
- Types: jpg/jpeg → `image/jpeg`, png → `image/png`, webp → `image/webp`, mp4 → `video/mp4`,
  mov → `video/quicktime`, mp3 → `audio/mpeg`, wav → `audio/wav`.
- Keep the returned `url`: Elements need both the `id` and the `url` (§6).
- Completed job ids (e.g. a generated start frame) can be passed directly as `medias[].value` without
  re-uploading [HF-DOC].
- Uploaded videos may be normalised server-side (stored params showed a `_trim.mp4` suffix) [VERIFIED].
- **Videos are uploaded without audio** (Edit Mode and Analyze Recreate; Analyze Create uploads no
  reference video at all). `atp.py split-audio` writes a silent copy of every original
  into `<given path>/videos_without_audio/` and its audio into `<given path>/files_audio/`. Only the
  silent copies (or their prepared derivatives) go to Higgsfield, which lowers the chance of
  moderation flags. Edit Mode finals get the original audio back with `atp.py restore-audio --audio`.
- Before uploading, prepare the input:
  - convert HEIC/AVIF to PNG/JPEG;
  - keep reference images ≤ 4K and < 30 MB;
  - put product cut-outs on a neutral background unless transparency is needed;
  - crop or trim source videos to the segment being edited (4–30 s for Seedance 2.5 / Genjutsu edits).

## 5. Media roles — how the catalog names them

| Role (catalog) | Meaning | Models (2026-09-30) |
|---|---|---|
| `start_image` / `end_image` | First / last frame anchors | Seedance 1.5/2.0/2.5, Kling 3.0 (end too), Kling 3.0 Turbo / 2.6 / Happy Horse / Grok (start only), Veo 3 / 3.1 (start only), Veo 3.1 Lite, Wan 2.7 / 3.0, MiniMax H3 / Hailuo, FLUX 3 Video, Gemini Omni 1.1, Cinema Studio |
| `image` | Generic image input | Cinema Studio (all), Marketing Studio, `higgsfield_preset` |
| `image_references` | Identity, product, prop or scene references | Seedance 2.0/2.5, Wan 2.6 / 3.0, MiniMax H3, FLUX 3 Video, Gemini Omni, Grok 1.5, Kling Omni Edit, Genjutsu |
| `video_references` | Motion, camera or timing reference, or the source video to edit or extend | Seedance 2.0/2.5, Wan 2.6 / 3.0, MiniMax H3, FLUX 3 Video (+ Edit), Gemini Omni, Kling Omni Edit, Genjutsu |
| `audio_references` | Voice, music or sound reference | Seedance 2.0/2.5, Wan 2.6 / 2.7 / 3.0, MiniMax H3, Grok 1.5 |
| `input_video` / `input_audio` | Utility inputs | `sync_so` lipsync, `video_upscale`, `video_deflicker` |

- The server auto-coerces unambiguous roles. Higgsfield's own recipes pass `"video"` / `"image"`, and
  stored params show `"audio"` for an audio reference [VERIFIED]. Prefer the exact catalog role names.
- **Order matters.** Prompt tags such as `@Image1`, `@Video1` and `@Audio1` count per media type in
  `medias` order (Seedance convention; see each model guide for its own tag syntax). In edits, the
  source video goes first and images follow in `@ImageN` order [HF-DOC].
- Hidden stored keys (`multi_shots`, `speedramp`, `reference_elements`, `prompt_language`, …) appear
  in stored params as server defaults. Do not set them unless a model guide says they are honoured.

## 6. Elements — reusable project assets

`show_reference_elements` stores a character, prop or environment once per workspace; prompts cite it
as `<<<element_id>>>` and the backend injects the image [HF-TOOL].

- **Create.** `show_reference_elements {action:"create", medias:[{id:<media_id>, url:<upload url>, type:"media_input"}], category:"character"|"prop"|"environment"|"auto", name:"<≤32 chars>", description:"<optional>"}`.
  It returns synchronously. A completed image job can serve as the source (`type:"image_job"`).
- **Video models that accept Elements**: Cinema Studio Video 2 / 3.0, Seedance 2.0, Kling 3.0 (per the
  tool description). Several placeholders per prompt are allowed:
  `"<<<A>>> hands <<<B>>> to the person on the left"`.
- **When to use.** Analyze Mode collects project-level characters and products once. Create Elements
  for them when the selected model is on the list above; this matters most for Kling 3.0 and Cinema
  Studio, whose catalog entries have no `image_references` role. Store element ids in
  `state.json → assets`.
- **Ambiguity guard.** The tool asks the agent to choose between a Soul (5–20 photos, image models
  only) and an Element (instant, one image, multi-subject). For video generation, Elements are the
  relevant path.

## 7. Fixed output: vertical 9:16 at 720p

Every generation in both modes is 9:16 at 720p. It is never asked. `models/index.json →
output_9x16_720p` holds the exact per-model parameters. Rules:

1. **Native models.** Send `aspect_ratio:"9:16"` plus the model's 720p setting: `resolution:"720p"`,
   `quality:"720p"` (Wan 2.6), or `mode:"std"` (Kling 3.0 / Cinema Studio Video 2, [INFERRED]
   standard tier = 720p). Seedance 2.0 at 9:16 / 720p stored `width 720, height 1280` [VERIFIED].
2. **Models without a 720p option.** Minimax Hailuo 768 / 1080, MiniMax H3 2K, H3 Max 768p, and the
   Veo tiers are generated at the closest tier. Then `atp.py conform` downscales to 720×1280:
   scale-to-cover plus a crop of a few pixels, never a stretch.
3. **Aspect follows an input.** Start-frame-locked models and edit models inherit the input's aspect.
   - Supply a 9:16 start frame, generated or prepared at 720×1280.
   - Or bring the source video to 9:16 **before** editing:
     - `atp.py conform --focus-x/--focus-y` when a crop keeps every important subject; the tool
       refuses to crop more than 12% unless told to;
     - otherwise Higgsfield `reframe` (AI expansion to 9:16, 720p, `get_cost` supported);
     - otherwise regenerate with the source as a video reference.
4. **Verify.** `atp.py qc --expect-size 720x1280` on every final. Never deliver a stretched or
   letterboxed result unless the user explicitly asked for padding (`conform --mode pad`).
5. **Stored `width`/`height` in generation params are not the output size.** A `wan3_0_prime` job at
   9:16 / 480p stored `768×1344`, but the delivered file measured **480×854 at 30 fps** [VERIFIED
   2026-09-30]. Seedance 2.0 at 9:16 / 720p stored and delivered 720×1280 [VERIFIED]. Always measure
   the downloaded file (`hf-get` reports the dimensions).

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

## 9. Errors and recovery

| Situation | Response |
|---|---|
| Transport timeout on submit | The outcome is unknown. Do not resubmit. Check `show_generations {type:"video", size:5}` / `transactions` for a matching job, then continue polling or resubmit once it is known that nothing was created |
| `adjustments` in a response | The server applied defaults or clamped values. Check each one against the plan |
| `recovery_tool` | Call it immediately (credits / plan flows), then wait for the user |
| `unlim_choice` | Nothing was submitted. Ask, then resubmit with `use_unlim` |
| Validation error naming a field | Fix that field only (role name, parameter name, value out of range) and resubmit. The creative intent stays unchanged. Log the correction |
| Unsupported feature for the model | Do not fake it in prose. Switch the operation (e.g. start frame instead of references), or tell the user the model cannot do it and suggest a model from `index.json` that can |
| PUT not 200 | Do not confirm. Request a new `media_upload` slot (URLs are single-use, signed per content type) |
| Job `failed` | A refund appears in `transactions`. Read `fail_reason` if present, adjust (content filter → rephrase; input → fix), and retry once. A failure within seconds, with no reason or a filter text, is a **flag**: record it first (`T ledger set --flagged`, `T caught-flag add`, command item 23), then change the request |
| Content protection block ("May contain protected content") | Remove real-person likeness claims or protected IP from the prompt and references, then ask the user if the asset itself is the cause [HF-DOC]. It is a flag: `T caught-flag add` with the verbatim text before the change |
| An uploaded image, video or Element comes back `nsfw`, `ip_checking` or `failed`; an output is withheld; a `preset_recommendation` notice comes back instead of a job | Flags: record with `T caught-flag add` (`--stage upload` / `result` / `submit`), then replace the input with another supplied asset, or retry the one literal request with `declined_preset_id`; never re-upload a flagged file unchanged |
| Result shorter than planned | Report it. Never loop or freeze frames to pad a result |

## 10. Utility operations (on Higgsfield, only when the plan needs them)

`reframe` (aspect conversion), `remove_background` (image/video cut-outs), `sync_so` (lipsync:
`input_video` + `input_audio`, `sync_mode`), `video_deflicker`, `fps_boost`, `upscale_video` /
`topaz_video` / `bytedance_video_upscale`, `topaz_hyperion_2_5` (SDR→HDR), `depth_anything_video`,
`sam_3_video` (masking). None is part of the default path. Each costs credits: preflight where
`get_cost` is supported and mention the use in the brief.

## 11. Model availability (2026-09-30)

31 generative video model ids across 23 guides; see `models/index.json` for the id → guide mapping,
capabilities and the 9:16/720p parameters. Not selectable for prompting:
- `higgsfield_preset` (legacy preset id path);
- utility models (§10).
`marketing_studio_video` is only partly usable from Claude Code: its hook, setting, avatar and product
ids are listed by widget tools that are unavailable here (see its guide).

## 12. Never

- Never pass URLs, local paths or sandbox paths in `medias[].value`.
- Never call widget-only tools from Claude Code, and never use `sandbox_exec` for local files.
- Never resubmit after an unknown outcome, never launch uncontrolled batches, and never spend credits
  before the brief for that video has been shown.
- Never set `use_unlim` on your own initiative.
- Never treat Higgsfield "workflows" as Claude Code Workflows, and never call the Claude Code Workflow
  tool.
