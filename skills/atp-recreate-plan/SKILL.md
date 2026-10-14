---
name: atp-recreate-plan
description: /analyze-then-pick Analyze Mode / Recreate phase: pick the references and plan the edits (A6r). Internal to that command.
user-invocable: false
---

# atp-recreate-plan — Recreate: pick the references, plan the edits (A6r)

> `ATP` = `C:/Users/Glaresquare1/.claude/analyze-then-pick` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$ATP/scripts/atp.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `ATP/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `ATP/reference/<file>/` (models: `ATP/models/<guide>/`, Higgsfield: `ATP/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- brand-guardrails §3: `ATP/reference/brand-guardrails/030_3_the-guardrail-audit-per-referenc.md` (3.2 KB)
- brand-guardrails §4: `ATP/reference/brand-guardrails/040_4_the-audit-in-the-pipeline.md` (3.8 KB)
- analysis-protocol §5: `ATP/reference/analysis-protocol/060_5_cross-video-synthesis.md` (5.1 KB)
- generation-system §3c: `ATP/reference/generation-system/090_3c_reference-inserts-memes-cut-from.md` (3.2 KB)
- generation-system §4b.1c: `ATP/reference/generation-system/150_4b.1c_is-the-spot-feasible-read-the-so.md` (3.1 KB)
- generation-system §5c.1: `ATP/reference/generation-system/240_5c.1_the-source-action-script-card-th.md` (1.2 KB)
- generation-system §5c.2: `ATP/reference/generation-system/250_5c.2_the-most-preserving-input-and-pa.md` (2.4 KB)
- generation-system §5c.2b: `ATP/reference/generation-system/260_5c.2b_prepare-the-source-before-it-rid.md` (2.2 KB)
- *a source with many hard cuts (item 7: separate clips on its own cuts):*
  - generation-system §3b.1: `ATP/reference/generation-system/050_3b.1_plan-the-clips-in-the-video-plan.md` (2.3 KB)
- creative-direction §5.2: `ATP/reference/creative-direction/080_5.2_the-best-approach-both-sub-modes.md` (1.0 KB)
- text-and-format §2: `ATP/reference/text-and-format/020_2_edit-mode-removing-source-text.md` (2.3 KB)
- text-and-format §4: `ATP/reference/text-and-format/040_4_fixed-output-format-9-16-at-720p.md` (2.4 KB)
- *a person is swapped for a supplied character:*
  - anomaly-catalog §2.17: `ATP/reference/anomaly-catalog/200_2.17_identity-the-swapped-face-matche.md` (3.2 KB)
- the locked model's `edit_kind` and edit range: `T model-entry --id <model>`
- model guide sections: the locked model's guide (`T model-entry --id <model>` prints `guide` and `sections_dir`; see `atp-model-guide`) — §1 at a glance, §2.4 call recipes, §4.4 video edit (the preserving mode and settings), §6 features

### A6r. Recreate: pick the references and plan the edits (Recreate only, autonomous)
- **Use the recreate ranking from A4** (protocol §5). It weighs:
  - the integration form available for the product (swap / contents / placement);
  - for a placement, the anchor class the locked model renders at size: where its guide lists size
    as a model limit (`wan3_0_prime`, `wan-3-0.md` §5), an in-hand, swap or large same-plane
    neighbour anchor (the last only where `generation-system.md` §4b.1c holds, and with a guide) ranks
    above a surface anchor that only paper, a notebook or a head can size;
  - the placement's feasibility and the source's flags (`generation-system.md` §4b.1c, §5c.2b; protocol
    §5): a spot that is bare at frame 0, stays in frame along the path, lies outside every hand's lane and
    is wider than the product; a reference with many hard cuts, a person alternating with person-free shots
    or a baked face effect ranks low;
  - the number of people against the supplied characters;
  - the own-content length after stripping inserts, against the locked model's edit range. A longer
    one is split, which may need the A7b permission;
  - the load of text and overlays;
  - the motion complexity for the model's `edit_kind`;
  - its creative potential (`creative-direction.md` §5.2): mechanism strength, fit to the goal and
    the audience, how natural the product's integration can be, the freshness of its surface
    elements, and the risk of reading as a copy;
  - and, before all of these, the **guardrail audit** (item 21; `brand-guardrails.md` §3–§4): a
    reference with a core hit is dismissed and never picked; a pick-and-edit reference carries
    its guardrail operations into the edit load.
- **Take the top N.** Show one line per pick plus two runners-up, then proceed; the user may swap
  picks by replying. Store `recreate_picks`. Name the dismissed references with their rule in one
  line each.
- **Decide each pick's operations autonomously**, with no E3 questions:
  - **Person → character:** each person becomes a supplied character. Rotate characters across
    videos, one per person, using the guide's person-replacement contract.
  - **Product:** swap, contents or placement (item 14; `generation-system.md` §4b), written as edit
    operations ("Replace only …", "Add only … at …"). With examples, the house approach shapes the
    anchor, prominence and use.
  - **Source text:** every overlay text is removed in the edit (`text-and-format.md` §2) and comes
    back as CapCut layers, word for word. Usernames, handles, watermarks and source brands do not
    come back.
  - **Inserts** (memes) stay the reference's own: stripped before the edit, placed back in CapCut.
    An insert that shows an excluded person or a competitor's mark is cut and not placed back. Each
    insert is cut on frames that hold only its own content (edges past any dissolve or frame of the
    replaced performer), and the reference timeline and its original audio stay whole
    (`generation-system.md` §3c; CE-016, CE-024, CE-025).
  - **Guardrail edits** (`brand-guardrails.md` §2, §4), as change marks in the source action
    script and as operations in the first request: an untouched unit beyond the count limit is
    removed and the ledger holds the limit at every checkpoint; a competitor's name, logo and
    identifying mark are removed from its object, which stays as a plain unbranded one of the
    same shape, size, spot and light (never blurred, pixelated or covered); an excluded person is
    swapped completely (face, hair, marks, reflections), their name dropped from the text and
    their voice named in the brief; a caption that breaks a wording rule is rewritten minimally
    in CapCut, and a required disclaimer is added as a text layer in the house style; a peripheral
    banned prop is removed with its surface reconstructed.
  - **Audio:** the reference's original audio for its own content is restored onto the edited
    picture (X8 step 1); the inserts keep their own sound.
    - With inserts: `T restore-audio --generated <edit> --source <own.mp4>`.
    - Without: `--audio` from `files_audio`.
  - **Source fidelity (item 19):** the edit keeps the reference's movements, actions, details and
    timing, and only the operations above change. Add the pick's **source action script** with its
    keep / change marks and **sync anchors** to its card (`generation-system.md` §5c.1); the plan
    and the first request carry them.
- **Prepare each pick's source** as in Edit Mode E5, from its own content:
  - **With inserts:**
    `T strip-inserts --video "<original reference>" --inserts "<in-out,…>" --out <RUN>/10-media/<V>/own`
    gives `own-silent.mp4`, and `map.json` with the split points.
  - **Without inserts:** the silent copy from A1.
  - **Source flags** (the card's "Source preparation flags", `generation-system.md` §5c.2b): a mirrored
    selfie has its silent copy flipped (`hflip`) and its mirrored identity photos flipped too; burned-in
    text, names and patches are never removed by a tool: the prompt's clean-plate lines and, for a name or a
    patch, one named replace sentence carry them; a baked face effect is planned as flagged.
  - Then 9:16 (`T conform` / `reframe`). Split at cuts into the edit model's range when it is
    longer.

### Edit Mode's E4–E5, as Recreate uses them

### E4. Locked model — how it performs this edit (Recreate uses Edit Mode's machinery E4–E5)
- The model was picked at the start (§2.4) and does not change. Invoke Skill `atp-model-guide` (once) and call `models_explore get` once; each per-video skill then names the guide and reference sections it reads.
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

In Recreate (Analyze Mode) the tool methods that `text-and-format` §2 lists for removing source text (`--delogo`, `--crop`) are not used: a caption, a name or a patch is never removed by a tool, the prompt's clean-plate lines and the character-swap script carry it (see Never below).

## Rules this phase owns (contract items 16, 19)

16. **Analyze Mode: reference inserts are cut, never generated, and every video ends in CapCut.**
    - A meme or other insert that interrupts the reference (e.g. 13 s of footage + a 2 s meme with
      its sound + 12 s of footage) is cut from the reference with its sound. A video meme is never
      screenshotted.
    - Only the reference's own content is generated (Create) or edited (Recreate): 25 s in the
      example, with a beat boundary at the split.
    - Every video becomes its own CapCut project `DD_Mon_YYYY_vNN` (e.g. `01_Oct_2026_v03`). The
      project holds the clean video, split at each insert point with the insert placed in the gap,
      plus the overlay text as text layers (`reference/capcut-assembly.md`;
      `generation-system.md` §3c).
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

Item 21 (brand guardrails) is applied through the audit and operations above; its text sits in `atp-analyze-prepare` and `atp-plan-video`, and the rules are in `reference/brand-guardrails/` §3–§4 (read now).

## Never (this phase)

- Never generate a reference insert (meme, film snippet, reaction image). Cut it from the reference
  with its sound, and never reduce a video meme to a screenshot.
- Never place a product at a spot that is hidden at the source's frame 0, leaves the frame along the camera
  path, lies in a hand's lane, is narrower than the product or is the nearest plane unless the user marked
  it, and then only with a guide (`generation-system.md` §4b.1c); never build a size-and-place guide from an
  unscrubbed source frame (performer, clothing or lettering still in it), a flat packshot paste or a
  soft-labelled image (§4b.6); never upload a mirrored selfie source un-flipped in Recreate, or leave a baked
  face effect, a burned-in caption or an identifying name without its prompt sentence (§5c.2b); never try to
  remove a caption, a name or a patch from a source with a tool in Analyze Mode (inpaint, delogo, crop): the
  clean-plate lines and the character-swap script carry it.
- Never pick a reference whose core a guardrail bans, and never dismiss one for a peripheral hit
  that an edit removes without changing what the video is about; never blur, pixelate or cover a
  competitor's mark (remove it and keep the object); never leave an excluded person's face in any
  shot, reflection or placed-back insert; never leave more units than the limit in any frame;
  never invent a guardrail, and never let one relax a hard rule (`brand-guardrails.md`).
- Never send an Edit Mode or Recreate request, the first one included, without the fidelity lock
  (item 19): the change scoped with "only", the full keep-list, the exclusions and, for models that
  rebuild the action, the source action script written out in order.

## Hand-off

`T state --run RUN set stage=planned next_skill=atp-asset-plan`, then invoke Skill `atp-asset-plan`.

After a compaction, or on `resume`, re-invoke the skill named in `RUN/state.json → next_skill`: its text may have been summarised away.
