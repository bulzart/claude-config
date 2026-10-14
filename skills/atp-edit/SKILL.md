---
name: atp-edit
description: /analyze-then-pick Edit Mode phase: intake, operations, source preparation and the per-edit review (E1–E7, X9-R). Internal to that command.
user-invocable: false
---

# atp-edit — Edit Mode: intake to review (E1–E7, X9-R)

> `ATP` = `C:/Users/Glaresquare1/.claude/analyze-then-pick` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$ATP/scripts/atp.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `ATP/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `ATP/reference/<file>/` (models: `ATP/models/<guide>/`, Higgsfield: `ATP/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- analysis-protocol §3: `ATP/reference/analysis-protocol/040_3_per-video-card-20-analysis-cards.md` (5.2 KB)
- analysis-protocol §9: `ATP/reference/analysis-protocol/100_9_examples-the-user-s-own-videos-t.md` (3.1 KB)
- brand-guardrails §3: `ATP/reference/brand-guardrails/030_3_the-guardrail-audit-per-referenc.md` (3.2 KB)
- text-and-format §2: `ATP/reference/text-and-format/020_2_edit-mode-removing-source-text.md` (2.3 KB)
- text-and-format §4: `ATP/reference/text-and-format/040_4_fixed-output-format-9-16-at-720p.md` (2.4 KB)
- generation-system §5c.1: `ATP/reference/generation-system/240_5c.1_the-source-action-script-card-th.md` (1.2 KB)
- generation-system §5c.2: `ATP/reference/generation-system/250_5c.2_the-most-preserving-input-and-pa.md` (2.4 KB)
- generation-system §5c.2b: `ATP/reference/generation-system/260_5c.2b_prepare-the-source-before-it-rid.md` (2.2 KB)
- anomaly-catalog §1: `ATP/reference/anomaly-catalog/020_1_the-affordance-sheet-asset-regis.md` (7.6 KB)
- assets-and-substitution §4: `ATP/reference/assets-and-substitution/040_4_substitution-map-per-video.md` (2.4 KB)
- creative-direction §9: `ATP/reference/creative-direction/120_9_edit-mode.md` (0.3 KB)
- model guide sections: the locked model's guide (`T model-entry --id <model>` prints `guide` and `sections_dir`; see `atp-model-guide`) — §1 at a glance, §2.4 call recipes, §4.4 video edit / extension / motion transfer (the preserving mode and settings), §6 features
- the locked model's `edit_kind`: `T model-entry --id <model>`

## 4. Edit Mode

### E1. Intake
- `T inventory "<video path>" … --run RUN --as sources`: only videos are processed. Any other file
  there is ignored and never used as an asset.
- `T split-audio "<video path>" … --run RUN`. For every original video, **inside the given path**
  (sub-folders mirrored), it writes:
  - the audio to `files_audio/<name>.<ext>` (stream copy);
  - a silent copy to `videos_without_audio/<name>`.
  It links both to the inventory (`silent_path`, `audio_path`, `audio_offset`) and is idempotent.
  Report it in one line.
  - Only silent copies are ever uploaded to Higgsfield for replace, swap and other edits: there is
    less chance of flagging.
  - The approved result gets the original audio from `files_audio` (X8), and then goes to a `final`
    folder in the same path (X10).
- Then `T prep-all --run RUN --jobs 2`. The analysis uses the originals, with audio, for transcripts.
- **Examples, when given** (contract item 18): `T inventory "<examples folder>" --run RUN --as
  examples` and `T prep-all --run RUN --set examples`, then one card each and
  `20-analysis/house-approach.md` (protocol §9), once per run, before the first edit. Every edit
  follows it for how a replacement is held, placed and blended.
- Videos are edited **one at a time, in inventory order** (or the user's order).

### E2. For each video — understand it first
- Read `video.md` and `timeline.md` and view every storyboard sheet in order (densify contact
  moments).
- Write a compact card `20-analysis/cards/<V>.md` (protocol §3):
  - the full timeline;
  - actions, subjects and objects in the video (numbered, so E3 can point at them);
  - camera and staging;
  - continuity states;
  - the **source action script** (item 19, `generation-system.md` §5c.1): every beat in order, with
    who moves what and how (body, hands, head, gaze, face, mouth), the props and their contacts, the
    camera, the background action and the small details. Each beat gets its time range, and is
    marked keep or change once E3 has the operations;
  - its **sync anchors**: the beats whose sound is in the original audio (each spoken line and
    whose mouth says it, impacts, steps, pickups, sips, opens), with their times, from the
    transcript, the storyboards and, when it helps, `T audio-profile` hits;
  - the **source-text inventory** (`text-and-format.md` §2.1);
  - when guardrails were supplied with the assets (`30-assets/guardrails.md`), the **guardrail
    audit** (`brand-guardrails.md` §3): every hit, core or peripheral, and the operation the rule
    requires.
- Show the user a 4–6 line understanding of the video. With guardrails, add one line per hit:
  the required operation ("G4 requires a face swap for the man on the left"), or, for a core hit,
  that editing it would change the video ("this video's point is the taste test, which G3 bans").
  The user decides the operations in E3.

### E3. Choose the operations, then drop the files for each
1. **Operations.** Ask with AskUserQuestion (header "Edit", `multiSelect: true`), "What should happen
   in video N?":
   - **Replace an object / product**: swap an item (product, object, interface, logo…) for yours;
   - **Swap a person / face**: replace a person or character with your character;
   - **Remove something**: take an element out;
   - **Insert something**: add a new element.
   "Other" covers alter, restyle, relight, background change or recreate, described in words.
2. **Targets and files, per chosen operation.** Right after, ask in plain chat in **one** message,
   pre-filled with numbered candidates from the E2 understanding. Only include the lines for the
   operations the user chose:
   ```
   In video N I see: 1) <person A, where/when>  2) <object, where/when>  3) <…>
   Replace → which item(s)? Drop the replacement files (product samples: template + other views).
   Swap → which person(s)? Drop the character files for each (face close-up + full body if you have them).
   Insert → what, where, when? Drop its files.
   Remove → which item(s)? (no files needed)
   Reply like:  replace 2: <paths>   swap 1: <paths>   (or "same files as video 1")
   ```
   Then stop and wait.
3. **Register the files for this edit only.**
   - `T inventory <paths…> --run RUN --as assets --scope video-NN`, then
     `T prep-assets --run RUN --scope video-NN`; view the contact sheet.
   - **Bind each file to the operation and target it was given for.** The user's grouping is
     authoritative. If files arrive ungrouped, sort them by what they show (a person vs. an object).
     Ask only if that is still ambiguous.
   - Within each product, pick the canonical template and mark the other views and variants.
   - Write the replacement product's affordance sheet (`anomaly-catalog.md` §1) whenever the edit
     has it handled or used on screen (drunk, opened, applied, carried).
   - "Same files as video K" reuses that scope explicitly. Nothing else carries over.
4. Remind the user once that all source text (captions, usernames, watermarks, stickers, overlays…)
   is removed unless they name text to keep.

### E4. Locked model — how it performs this edit
- The model was picked at the start (§2.4) and does not change. Before the first edit invoke Skill `atp-model-guide` (once) and call `models_explore get` once; each per-video skill then names the guide and reference sections it reads.
- Map the chosen operations onto the model's edit capability (`index.json → edit_kind`):
  - **✓ edits video** (`video_edit`, `object_replace`): a true edit of the 9:16 source.
  - **↔ motion transfer:** the source drives motion; the supplied files define the subjects and
    scene.
  - **≈ recreate** (`video_refs`): regenerate the clip with the source as a motion, camera and timing
    reference, applying the operations.
  - **✗ frames only:** recreate from clean 9:16 frames of the source, with the operations applied to
    those frames through the supplied files, plus a prompt that rebuilds the source's action.
- **Fidelity (item 19).** Take the most preserving way the locked model can perform this edit,
  with the guide's preserving mode and settings (`generation-system.md` §5c.2). ✓ and ↔ keep the
  source's movements and timing by construction. ≈ keeps them only with the source as the video
  reference, the same duration and the action script written out. ✗ cannot guarantee them: use
  the source's own first frame, and its last frame when the model takes one, with the operations
  applied; write the action script out; and say in the brief that fidelity and sync are at risk.
- State the approach in the brief (one line). Never switch models.

### E5. Prepare the source (local, deterministic)
- **Start from the silent copy** (`videos_without_audio/…`), never from the original with audio.
  Every preparation below produces a silent file under `RUN/10-media/<V>/prepared/`. The user's
  folders keep only `files_audio` and `videos_without_audio`.
- **9:16.** If the source is not 9:16, choose (per `text-and-format.md` §4.1):
  - `T conform` with a focus point, when a crop keeps every important subject;
  - Higgsfield `reframe` (9:16, 720p; preflight first);
  - regeneration with the source as a video reference.
- **Length.** If the source exceeds the edit model's input range, split it at cuts with `T trim` into
  segments, edit them in order with identical references and wording, then `T concat` the edited
  pictures. The original audio is restored once over the joined result.
- **Duration (item 19).** Request each segment at its exact source duration, or at the nearest
  allowed duration above it and trim the extra afterwards. Never request a shorter one: the actions
  would be squeezed against the original sound.
- **Text.** Plan the removal per `text-and-format.md` §2.2:
  - local `T clean` for small static overlays;
  - otherwise explicit remove operations in the edit prompt;
  - otherwise clean-frame regeneration.
- **Source flags** (the card's "Source preparation flags", `generation-system.md` §5c.2b): plan for a baked
  face effect; burned-in text, names and patches are written as the edit prompt's remove or replace
  operations, never removed by a tool; a mirrored selfie is flipped only when the user asks (E3), since only
  the planned operations change.

### E6. Generate
Run **X1–X10** (§5) for this video, as an edit. The source video is the unique master, and the plan
holds:
- the operations;
- the substitution map;
- the integration analysis;
- the text removal;
- the audio:
  - request **no generated audio** whenever the model has a flag for it (`generate_audio:false` /
    `sound:"off"`);
  - the final **always** carries the original audio from `files_audio` (X8), and any audio the
    model returns is discarded.

Before the first submission of the run, show the estimated total against the balance: the
preflight of video 1 × the number of videos. Then ask with AskUserQuestion (header "Go"):
- "Start editing (≈X credits)";
- "Edit video 1 first, then decide";
- "Stop here".

Pause again before an attempt whose preflight exceeds
`config.json → higgsfield.confirm_cost_above_credits`, or when credits run low.
After every attempt, the finished video opens for the user's review (X9-R):
- **"Looks good"** moves on;
- **"Needs changes"** re-edits **the original source video** with the feedback, as a new attempt;
- the loop repeats until the user approves or stops.

### E7. Next video
Only after the user approved the current video (or chose to stop), repeat E2–E6 for the next one. Do
not re-ask for the model. Every video gets its own E3 (operations → files); the user can answer "same
files as video K".

### The per-video loop for one edit (E6)

At the start of each video (before E2): `T state --run RUN set stage=editing video=NN next_skill=atp-edit`; when E5 is done: `next_skill=atp-plan-video`; when the user approves it (X9-R): `next_skill=atp-record`. A resume lands on the video's step; the ledger and the files on disk show how far it got (`T ledger begin` exit 3 stops any double submission).

E6 runs the per-video steps for this video, in this order, each by invoking its skill when you get to it: `atp-plan-video` (X1) → `atp-write-request` (X2) → `atp-inputs` (X3) → `atp-precheck` (X4–X6, including the E6 "Go" gate for the first video) → `atp-submit` (X7) → `atp-postprocess` (X8) → `atp-qc` (X9) → the review below (X9-R) → `atp-record` (X10). At every preflight (X5, in `atp-precheck` or `atp-submit`) apply E6's pause rule above (cost above `confirm_cost_above_credits`, or credits running low).

**A re-edit** (X9-R item 3: a new attempt from the original source) runs `atp-write-request` (the feedback folded into the plan and the request, the fidelity lock kept) → `atp-inputs` only for files the user added or replaced → `atp-submit` (X5 again, X7) → `atp-postprocess` → `atp-qc` → this review again.

In Edit Mode the X9 findings are the QC notes of the review: there is no automatic regeneration, the user decides.

### X9-R — Edit Mode review (every edit, every attempt)

  1. Open the finished video for the user: `T open --file <final.mp4>`. This is the version with the
     **original audio** already merged, so the user judges exactly what will be delivered, lip-sync
     included. Also print:
     - its path and the raw Higgsfield file next to it;
     - the Higgsfield result URL;
     - 1–3 QC notes (e.g. leftover text or a duration difference, or "no issues found").
     - the sync verdict (item 19), always: the measured offset and the sheet's path. A `drift` or
       `out_of_sync` comes first, with the moments that miss their sound.
  2. Ask with AskUserQuestion (header "Review"), "Video N, attempt K — is it okay?":
     - **"Looks good — next video"** → `T ledger set --job J --status accepted`, then X10, which
       places the approved video in the `final` folder.
     - **"Needs changes"** → ask in plain chat what to change, and let them add or replace files.
       Write their words verbatim, and the diagnosis, in the video's brief as the next attempt's block
       before re-editing (item 22).
     - **"Stop here"** → keep the files, go to the wrap-up.
     "Other" lets the user type the changes directly.
  3. **Re-edit from the original.** A new attempt always starts from the **original source video**
     (the same prepared 9:16 source, already uploaded; its media id is reused), never from the
     previous output. It uses the same per-edit files plus any new ones: re-run `inventory` for scope
     `video-NN` with the full path list.
     - Fold the feedback into the plan and the request (the item 19 fidelity lock stays), and save them as
       `50-requests/video-NN-aK-request.json`.
     - The brief shows what changed versus the previous attempt, plus the preflight cost.
     - Then X5 → X7 → X8 → X9 → X9-R again.
     - Mark the rejected attempt with `T ledger set --job <old> --status rejected`.
     - Loop until the user says it is okay or stops. Every attempt is kept under
       `60-outputs/video-NN/aK/`.

## Rules this phase owns (contract items 13, 18, 19, 11)

13. **Edit Mode review.** After every edit attempt, the user sees the finished video and approves
    it or asks for changes. Changes are re-applied to the **original** source video. The next video
    starts only after approval (§5 X9-R).
18. **Examples: the user's own finished videos (optional, both modes).** They are asked for with the
    other inputs (§2.5). The folder may be empty or absent; then nothing changes.
    - They show the user's **house approach**: how their products are placed, used, continued across
      clips and blended, plus anything else they consistently do (text placement, pacing, sound,
      characters, endings).
    - When present, they are prepared and analysed (A1, A3; Edit Mode E1) into
      `20-analysis/house-approach.md`, and every plan follows it (A4–A7, X1, X9).
    - **Precedence:** the user's instructions for the run > the house approach > the pipeline's
      defaults. The house approach never overrides the hard rules: physical and logical correctness
      (`generation-system.md` §3, §4b, §5b), the §9b must-not-survive list, the permission rule
      (item 15) and the house text style (item 6).
    - Examples are **study material only**: never uploaded, recreated, cut into a new video, or used
      as client assets. Their own flaws (a physics cheat, a leftover watermark) are never copied.
19. **Source fidelity is pushed from the first attempt (Edit Mode and Analyze Mode Recreate).** The
    output is the source with only the planned operations changed: every other movement, action and
    detail stays exactly as it is. The original audio also goes back under the generated picture
    (X8), so every action happens at the same moment, at the same speed and in the same order as in
    the source: mouth movements on their words, contact on its impacts, steps on their footfalls, a
    pickup, sip or door on its sound. The **first** request is built for this, and QC only confirms
    it (`reference/generation-system.md` §5c):
    - the card holds the **source action script**: every beat in order, with who moves what and how
      (body, hands, head, gaze, face, mouth), the props and their contacts, the camera, the
      background action and the small details, each marked keep or change. Its **sync anchors** are
      the beats whose sound is in the original audio (§5c.1);
    - the request uses the most preserving input and parameters the locked model offers: the source
      as the edit input, then as the motion input, then as the video reference, then its own first
      and last frames. The guide's preserving mode is used, and the duration equals the source
      segment's (§5c.2);
    - the prompt carries the **fidelity lock** in the guide's wording: the change scoped with
      "only", the full keep-list, and exclusions against any added, skipped or reordered action.
      For models that rebuild the action (≈, ✗), the action script is also written out in order.
      The timing comes from the source video, never from timestamps in the prompt (§5c.3);
    - X4 checks the request against the action script before any credit is spent (§5c.4);
    - after the merge, `T sync-check` measures the timing (X8 step 5). A steady offset is fixed in
      post. Drift or a moved action is a regenerate reason in Recreate, or the first QC note in
      Edit Mode.
    Create is not affected: it makes new scenes, and its sound is built in CapCut on their own
    beats.
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

- Never upload, recreate or cut an example into a new video, never take client assets from the
  examples folder, and never copy an example's flaws. Never let the house approach override the
  hard rules (contract item 18).
- Never reuse one edit's files for another edit unless told to.
- Never keep source text in Edit Mode unless the user kept that specific text.
- Never upload an original video with its audio to Higgsfield: use the `videos_without_audio` copy
  (or its prepared derivative).
- Never deliver an Edit Mode result with generated audio. It always carries the original audio from
  `files_audio`, or no audio if the original had none.
- Never send an Edit Mode or Recreate request, the first one included, without the fidelity lock
  (item 19): the change scoped with "only", the full keep-list, the exclusions and, for models that
  rebuild the action, the source action script written out in order.
- Never move to the next Edit Mode video before the user approved the current one.
- Never re-edit an Edit Mode video from a previous output: re-edits always start from the original
  source.
- Edit Mode: never spend credits before the "Go" gate of the run.

## Hand-off

- Per video: after E5, invoke Skill `atp-plan-video` (the per-video loop above).
- After the last video is approved or the user stops: `T state --run RUN set stage=edited next_skill=atp-wrapup`, then invoke Skill `atp-wrapup`.

After a compaction, or on `resume`, re-invoke the skill named in `RUN/state.json → next_skill`: its text may have been summarised away.
