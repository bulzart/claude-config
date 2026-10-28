---
name: awl-inputs
description: /analyze-with-loupe per-video step X3: upload inputs, hand-off frames, start frames, the original reference. Internal to that command.
user-invocable: false
---

# awl-inputs — Step X3: inputs

> `AWL` = `C:/Users/Glaresquare1/.claude/analyze-with-loupe` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$AWL/scripts/awl.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `AWL/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `AWL/reference/<file>/` (models: `AWL/models/<guide>/`, Higgsfield: `AWL/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

Load the Higgsfield tools first (below). A production agent starts its lane here. Provenance labels: **[E]** evidence · **[I]** inference · **[U]** user instruction · **[A]** client asset · **[M]** model knowledge · **[G]** generation instruction.

### Higgsfield tools

**Higgsfield tools** are deferred.
- Load them before first use:
  `ToolSearch "select:mcp__higgsfield__models_explore,mcp__higgsfield__balance,mcp__higgsfield__list_workspaces,mcp__higgsfield__create_project,mcp__higgsfield__media_upload,mcp__higgsfield__media_confirm,mcp__higgsfield__media_import_url,mcp__higgsfield__show_reference_elements,mcp__higgsfield__generate_image,mcp__higgsfield__generate_video,mcp__higgsfield__jobs_wait,mcp__higgsfield__show_generations,mcp__higgsfield__transactions,mcp__higgsfield__reframe"`.
- If they are missing or only `authenticate` tools exist, ask the user to run `/mcp` → higgsfield →
  Authenticate, then continue.
- Never call widget-only tools (`media_upload_widget`, `show_marketing_studio_v2`).

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- higgsfield-mcp §4: `AWL/higgsfield/higgsfield-mcp/040_4_local-file-upload-terminal-path.md` (2.0 KB)
- higgsfield-mcp §5: `AWL/higgsfield/higgsfield-mcp/050_5_media-roles-how-the-catalog-name.md` (2.3 KB)
- higgsfield-mcp §6: `AWL/higgsfield/higgsfield-mcp/060_6_elements-reusable-project-assets.md` (1.3 KB)
- assets-and-substitution §5: `AWL/reference/assets-and-substitution/050_5_getting-references-into-the-mode.md` (2.9 KB)
- *a multi-clip video (hand-off inputs):*
  - generation-system §3b.3: `AWL/reference/generation-system/070_3b.3_seam-discipline.md` (2.4 KB)
- *a placed product (the original is the only video reference; spot and size in the prompt):*
  - generation-system §4b.5: `AWL/reference/generation-system/190_4b.5_expressing-it-to-the-model-with.md` (6.5 KB)
- *a production agent (the `blocked` path and the QC `continuity` text are defined here):*
  - production-agents §4: `AWL/reference/production-agents/040_4_60-outputs-video-nn-result-json.md` (2.1 KB)
- model guide sections: the locked model's guide (`T model-entry --id <model>` prints `guide` and `sections_dir`; see `awl-model-guide`) — §2.2 (media roles), §3.7 (references), §3.8 (frames)
- *an own voiceover with the native or lipsync method (the plan's Voiceover block; item 31):*
  - voiceover §7: `AWL/reference/voiceover/070_7_uploading-the-take-x3.md` (0.7 KB)

## Step X3

- **X3 — Inputs.** Upload without asking: no approval stop before a `media_upload` or a generation (item 15).
  - Take the assets only from this video's registry: scope `project` (Analyze Mode asset plan) or
    scope `video-NN` (Edit Mode files for this edit).
  - Upload the files this video needs, once per run: `media_upload` → `T hf-put --capture <id> --file <path>` (the hook keeps every
    `media_upload` answer in Loupe as a capture and prints its id when this library's run is the newest changed one; the presigned URL is
    never copied by hand; `--url` only when no capture id was printed) → `media_confirm` → `T uploads set --run RUN --video NN --label "<as the request names it>" --media-id <id>
    --file <path>` (one schema; the main session merges the records with `T uploads merge`). Reuse media ids recorded in `state.json`.
  - **Every video sent to Higgsfield is silent:** the `videos_without_audio` copy, or its prepared
    derivative from E5. Never upload an original video with its audio. (A clip this run generated
    may go back with its generated audio, as the input of a native extension.)
  - **Own voiceover** (item 31; native or lipsync): upload the take as `voiceover.md` §7 says (an audio upload, recorded as "Audio 1");
    overlay never uploads it. Native on Wan 2.7 also needs its start frame (the speaker with the product at t=0), built as below.
  - **Multi-clip continuous seam:** the input comes from the **accepted** previous clip
    (`generation-system.md` §3b.3):
    - last-frame chain: `T last-frame --video <clip> --out <…/cK/handoff.png>`, view it, upload it,
      and pass it as `start_image`;
    - native extension: the accepted clip itself as `@Video1`. Pass its job id directly; if the
      server refuses that for a video role, or the clip was trimmed, upload the file.
  - **Edit Mode and Recreate with a frames-only model (item 19):** the start frame is the source's
    own first frame with the operations applied, and the end frame, when the model takes one, is
    its last frame with the same operations. The model then interpolates the source's own action.
  - Create Elements when the model supports them and assets recur.
  - **The original reference** (Recreate and Edit Mode; `generation-system.md` §4b.5, [U] 2026-10-28), the only
    video reference: the original's silent footage of exactly the span the plan cut (`<references
    folder>/videos_without_audio/<name>` when there are no inserts, flip or padding, otherwise `own/own-silent.mp4`
    or the prepared `prepared/source.mp4` that had the same flip or padding), uploaded once per video and reused by
    every attempt, in the model's most preserving input (the edit source, the motion source or the first video
    reference), within the model's own limits (its guide §2.2, §2.5: video count and lengths), else the clip plan
    of X1 applies; record it with `T uploads set` ("original reference"). Nothing that places the product rides
    beside it, in any mode (no composited copy, no marked still, no layout image): the product's views ride
    padded and the prompt carries the spot and the size. Never a guide image cut from a source frame.
  - **Contents form:** upload the variant's contents sample with the product views, and bind it to
    the vessel's contents in the prompt ("the drink in the cup has the colour, clarity and bubbles
    of @ImageN", "the gum piece she takes has the shape and colour of @ImageN"). A start frame
    shows the vessel already holding it, and the opened package beside it.
  - For start-frame models, build and check the 9:16 start frame with an image model
    (`assets-and-substitution.md` §5). It must match the canonical geometry before it is used. It is the literal
    first frame, so its product is a photoreal render that passes the paste test (`anomaly-catalog.md` §2.15).
    That `generate_image` call is paid, so it follows the same ledger discipline as X7: its own
    request file `50-requests/video-NN[-aK]-frame-request.json`, `ledger begin`, one call, `ledger set`,
    then `jobs_wait`.

## Rules this phase owns (contract items 11)

11. **Client assets come only from paths the user gives.**
    - **Analyze Mode:** the user supplies all asset files and/or folders **once, at the start**. The
      command then understands them and uses them autonomously for every video.
    - **Edit Mode:** the user supplies the assets **for each edit**.
    - Never search for, detect, infer or pick client assets inside the references folder or the
      edit-source folder. Those can hold other products, samples or entirely different executions, so
      everything there is **reference material only**.
    - Never reuse one edit's assets for another edit unless the user says so.
    - The **examples folder** (item 18) is never a source of client assets either.

## Never (this phase)

- Never take client assets from the references folder or the edit-source folder: they are
  reference material, and may show other products or executions.
- Never upload an original video with its audio to Higgsfield: use the `videos_without_audio` copy
  (or its prepared derivative).
- Never build, upload or bind a guide image cut from a source frame, or any placement image beside the original
  (a copy of the source with the product composited in, a layout image, a marked still; `generation-system.md` §4b.5).
- Never upload the flawed take (a clip QC rejected) as an input of its regeneration: the retry reuses the
  media ids of the first attempt (the original source video, when the video has one). Only an accepted clip goes back, as the input
  of a native extension.

## Hand-off

- Edit Mode: invoke Skill `awl-precheck` (X4–X6).
- Analyze Mode main session, A9 step 2 (the shared uploads): return to `awl-analyze-produce` and continue A9 (step 3: `awl-precheck` for X5–X6 of every video).
- Production agent: invoke Skill `awl-submit` (X5 again if the request changed, then X7).
