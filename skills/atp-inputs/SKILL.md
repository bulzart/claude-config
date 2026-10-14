---
name: atp-inputs
description: /analyze-then-pick per-video step X3: upload inputs, hand-off frames, start frames, guides. Internal to that command.
user-invocable: false
---

# atp-inputs — Step X3: inputs

> `ATP` = `C:/Users/Glaresquare1/.claude/analyze-then-pick` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$ATP/scripts/atp.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `ATP/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `ATP/reference/<file>/` (models: `ATP/models/<guide>/`, Higgsfield: `ATP/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

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

- higgsfield-mcp §4: `ATP/higgsfield/higgsfield-mcp/040_4_local-file-upload-terminal-path.md` (2.0 KB)
- higgsfield-mcp §5: `ATP/higgsfield/higgsfield-mcp/050_5_media-roles-how-the-catalog-name.md` (1.7 KB)
- higgsfield-mcp §6: `ATP/higgsfield/higgsfield-mcp/060_6_elements-reusable-project-assets.md` (1.3 KB)
- assets-and-substitution §5: `ATP/reference/assets-and-substitution/050_5_getting-references-into-the-mode.md` (2.3 KB)
- *a multi-clip video (hand-off inputs):*
  - generation-system §3b.3: `ATP/reference/generation-system/070_3b.3_seam-discipline.md` (2.4 KB)
- *the plan has a size-and-place guide, or a retry adds one:*
  - generation-system §4b.6: `ATP/reference/generation-system/200_4b.6_the-size-and-place-guide-a-refer.md` (4.1 KB)
- *a production agent (the `blocked` path and the QC `continuity` text are defined here):*
  - production-agents §4: `ATP/reference/production-agents/040_4_60-outputs-video-nn-result-json.md` (0.9 KB)
- model guide sections: the locked model's guide (`T model-entry --id <model>` prints `guide` and `sections_dir`; see `atp-model-guide`) — §2.2 (media roles), §3.7 (references), §3.8 (frames)

## Step X3

- **X3 — Inputs.**
  - Take the assets only from this video's registry: scope `project` (Analyze Mode asset plan) or
    scope `video-NN` (Edit Mode files for this edit).
  - Upload the files this video needs, once per run: `media_upload` → `T hf-put` (exact
    content type) → `media_confirm`. Reuse media ids recorded in `state.json`.
  - **Every video sent to Higgsfield is silent:** the `videos_without_audio` copy, or its prepared
    derivative from E5. Never upload an original video with its audio. (A clip this run generated
    may go back with its generated audio, as the input of a native extension.)
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
  - **The size-and-place guide** (`generation-system.md` §4b.6), when the plan has one: build it locally from
    the source's bare surface scrubbed of performer, clothing and lettering (Create: neutral texture only),
    check it at X4, upload it with this video's own inputs and bind it as the last `image_references`
    entry, for spot and size only.
  - **Contents form:** upload the variant's contents sample with the product views, and bind it to
    the vessel's contents in the prompt ("the drink in the cup has the colour, clarity and bubbles
    of @ImageN", "the gum piece she takes has the shape and colour of @ImageN"). A start frame
    shows the vessel already holding it, and the opened package beside it.
  - For start-frame models, build and check the 9:16 start frame with an image model
    (`assets-and-substitution.md` §5). It must match the canonical geometry before it is used.
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

## Hand-off

- Edit Mode: invoke Skill `atp-precheck` (X4–X6).
- Analyze Mode main session, A9 step 2 (the shared uploads): return to `atp-analyze-produce` and continue A9 (step 3: `atp-precheck` for X5–X6 of every video).
- Production agent: invoke Skill `atp-submit` (X5 again if the request changed, then X7).
