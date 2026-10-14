---
name: atp-postprocess
description: /analyze-then-pick per-video step X8: download, restore audio, conform, join, sync check, CapCut assembly. Internal to that command.
user-invocable: false
---

# atp-postprocess — Step X8: download and post-process, CapCut project

> `ATP` = `C:/Users/Glaresquare1/.claude/analyze-then-pick` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$ATP/scripts/atp.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `ATP/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `ATP/reference/<file>/` (models: `ATP/models/<guide>/`, Higgsfield: `ATP/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- capcut-assembly §1: `ATP/reference/capcut-assembly/010_1_tools-and-rules.md` (1.9 KB)
- capcut-assembly §2: `ATP/reference/capcut-assembly/020_2_create-the-project.md` (0.8 KB)
- capcut-assembly §3: `ATP/reference/capcut-assembly/030_3_build-the-timeline.md` (4.6 KB)
- capcut-assembly §4: `ATP/reference/capcut-assembly/050_4_after-every-save-capcut-cli.md` (2.3 KB)
- capcut-assembly §5: `ATP/reference/capcut-assembly/060_5_qc-of-the-project.md` (1.2 KB)
- capcut-assembly §6: `ATP/reference/capcut-assembly/070_6_deliverables-analyze-mode.md` (0.8 KB)
- *Create (the sound layer):*
  - capcut-assembly §3b: `ATP/reference/capcut-assembly/040_3b_sound-layer-create.md` (3.9 KB)
- text-and-format §1: `ATP/reference/text-and-format/010_1_text-policy-depends-on-the-mode.md` (5.7 KB)
- text-and-format §3: `ATP/reference/text-and-format/030_3_analyze-mode-planning-text-and-p.md` (3.5 KB)
- *a multi-clip video:*
  - generation-system §3b.3: `ATP/reference/generation-system/070_3b.3_seam-discipline.md` (2.4 KB)
- *a video with inserts:*
  - generation-system §3c: `ATP/reference/generation-system/090_3c_reference-inserts-memes-cut-from.md` (3.2 KB)
- *Edit Mode or Recreate (the sync check):*
  - generation-system §5c.5: `ATP/reference/generation-system/290_5c.5_measure-it-after-the-merge.md` (1.3 KB)

Notes on the order. (1) An Edit Mode source cut into segments (E5): concat the edited pictures first, then run step 1 (restore the original audio) once over the joined picture. (2) Recreate: `--audio` is the reference's `files_audio` file and `--audio-offset` its inventory `audio_offset` (fields `audio_path` and `audio_offset` of `RUN/00-inventory/inventory.json`, linked by `T split-audio`); a reference with inserts uses `T restore-audio --generated <edit> --source <own.mp4>` as the plan says. (3) Analyze Mode: stop after step 5 (the clean video) and go to `atp-qc` for the picture checks; once the picture passes, come back here for step 6 (the CapCut project), then `atp-qc` again for the project checks.

## Step X8

- **X8 — Download and post-process.** `T hf-get` into `60-outputs/video-NN/aK/raw.mp4` (K = the
  attempt number; the raw Higgsfield output is always kept), then as needed, in this order:
  1. **Edit Mode and Recreate — original audio back:**
     `T restore-audio --generated <raw or joined> --audio "<files_audio file>" --audio-offset <audio_offset> [--start <segment start>] --out <aK>/with-original-audio.mp4`.
     The picture is Higgsfield's and the sound is the original's. A clip that is slightly shorter
     keeps sync from the start and cuts the audio at its end; the tool reports it. A source that had
     no audio gives a silent final.
  2. `T conform` → exactly 720×1280;
  3. `T trim` (generated dead head or tail);
  4. `T concat` (multi-clip videos):
     - each clip is downloaded to `60-outputs/video-NN/cK/aJ/raw.mp4`, conformed, trimmed and
       QC'd (X9) **before** the next clip is submitted;
     - after the last clip:
       `T concat --clips <c1> <c2> … --seams <cut|continuous,…> --out 60-outputs/video-NN/joined.mp4`.
       Seams are `cut` on planned cuts and `continuous` on chained or extended joins. Edit Mode
       segments (E5) are always `cut`;
  5. **Sync check** (item 19; Edit Mode and Recreate), once the picture is final and the original
     audio is on it:
     `T sync-check --source <the prepared source; own-silent for a Recreate> --output <final> [--start <segment start>] --out <aK>/sync`.
     View `sync-sheet.jpg` and the sync anchors densified (mouths on their words, contact on its
     impacts). Then act on the verdict:
     - `in_sync` (within ±0.1 s everywhere) → continue;
     - `constant_offset` → apply its `fix`, with no new generation: trim the picture's head when the
       output is late, or re-run `restore-audio` with `--start` increased when it is early. Then
       merge and check again;
     - `drift` or `out_of_sync` (faster, slower, or an action added, skipped or moved) → a
       regenerate reason in X9;
     - `inconclusive` (motion too different to measure, e.g. a heavy restyle) → judge it on the
       sheet and the densified anchors.
  6. **Analyze Mode:** the result is the **clean video** `60-outputs/video-NN/clean.mp4`: conformed,
     trimmed, joined, with no overlay text. After it passes X9, assemble its CapCut project
     (`reference/capcut-assembly.md` §2–§5):
     - `T capcut-name --video NN` → `capcut_clone_draft` (empty) → `T capcut-prep`;
     - the inserts cut from the reference (`generation-system.md` §3c);
     - the generation placed, split at each insert point, with each insert in its gap;
     - every overlay text as a text layer;
     - `capcut_validate` → `capcut_save` → the capcut-cli repair lines → the preview.
     If CapCut is running, keep going and assemble all pending projects at the wrap-up.

## Rules this phase owns (contract items 6, 16)

6. **Text policy depends on the mode** (`reference/text-and-format.md`):
   - Edit Mode removes all source text unless the user keeps specific text.
   - **Analyze Mode generates every video clean.** It places all overlay text ("POV: …", "when …",
     hooks, captions) afterwards as **CapCut text layers** at the reference text's height and
     timing, always **horizontally centred** (posX 0; when centred text would cover the product, a
     face or an insert, it moves up or down, never sideways; CE-010)
     (`reference/capcut-assembly.md`).
     - The wording keeps the reference's role and format.
     - A generic meme line may stay as written; source-specific wording is rewritten.
     - Usernames, handles, watermarks and source brands are never copied.
     - A reference's short keyword or tag that is its hook, or any text the user keeps, is placed word
       for word at the same height (CE-027); a guardrail rewrite is minimal and keeps the reference's
       subject and meaning (CE-022).
     - A source overlay that carries the joke's context (a notification, a message, a banner) is the
       original element reused as a picture overlay, not re-typed text (CE-017, CE-023).
     - No text layer contains an emoji (the user's rule, strict).
   - **Every CapCut text layer uses the house text style:** font System, size 10, and **the user's
     chosen preset**, learned from their project `03_Oct_2026_v09` on 2026-10-03 and locked in
     `config.json → capcut.text_style.learned` (white text, black outline). `T capcut-repair` applies
     it to every text layer after each save (`reference/capcut-assembly.md` §3). Never re-learn or
     replace it unless the user explicitly asks for a different preset.
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

## Never (this phase)

- Never copy usernames, handles, watermarks or source brand names. Reuse reference caption wording
  only as a generic meme line (`text-and-format.md` §1).
- Never re-type a context-bearing source overlay as text (CE-017, CE-023), never drop a keyword the user
  keeps (CE-027), never change a caption's subject to clear a guardrail (CE-022), and never give a brand a
  scene it has no tie to when the other brand fits (CE-020).
- Never let the video model render overlay text in Analyze Mode. Generate clean and place the text
  in CapCut. Never burn it in with `atp.py captions`, except as the stated fallback.
- Never give a CapCut text layer another font, size, colour or preset than the house text style
  (font System, size 10, the user's locked preset in `capcut.text_style.learned`), unless the user
  asks for it in the run. Never re-learn or replace that preset (`--learn --replace`) unless the
  user explicitly asks for a new one. Never place a text layer off-centre horizontally (posX ≠ 0):
  only its height follows the reference.
- Never generate a reference insert (meme, film snippet, reaction image). Cut it from the reference
  with its sound, and never reduce a video meme to a screenshot.
- Never `capcut_save` with `force:true` or run capcut-cli with `--force-write` on the live CapCut
  store, and never write a project while CapCut is open.
- Never deliver a with-inserts video whose timeline or original audio was shortened, spliced or held on a
  frozen frame (CE-024, CE-025), whose insert edges show the replaced performer (CE-016), whose overlay
  outlives its element or its fade (CE-026), or whose text layer holds an emoji.
- Never stretch to reach 9:16, never ask for aspect ratio or resolution, and never deliver anything
  other than 720×1280.
- Never deliver an Edit Mode result with generated audio. It always carries the original audio from
  `files_audio`, or no audio if the original had none.
- Never deliver a video that carries the original audio without its sync check (X8 step 5), and
  never leave drift or a moved action unreported. Never fix sync by stretching or looping the
  original audio.

## Hand-off

Invoke Skill `atp-qc` (X9) on the final picture. In Analyze Mode, when `atp-qc` returns you here for step 6, assemble the CapCut project and invoke `atp-qc` again for the project checks.
