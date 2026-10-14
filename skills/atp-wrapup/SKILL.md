---
name: atp-wrapup
description: /analyze-then-pick final phase: wrap-up report, flag reconcile, feedback question, Topaz upscale (§6–6b). Internal to that command.
user-invocable: false
---

# atp-wrapup — Wrap-up (§6) and Topaz upscale (§6b)

> `ATP` = `C:/Users/Glaresquare1/.claude/analyze-then-pick` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$ATP/scripts/atp.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `ATP/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `ATP/reference/<file>/` (models: `ATP/models/<guide>/`, Higgsfield: `ATP/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- the run folder, `state.json`, the deliverables and the briefs are the sources
- *Analyze Mode with CapCut projects still pending:*
  - capcut-assembly §1: `ATP/reference/capcut-assembly/010_1_tools-and-rules.md` (1.9 KB)
  - capcut-assembly §2: `ATP/reference/capcut-assembly/020_2_create-the-project.md` (0.8 KB)
  - capcut-assembly §3: `ATP/reference/capcut-assembly/030_3_build-the-timeline.md` (4.6 KB)
  - capcut-assembly §4: `ATP/reference/capcut-assembly/050_4_after-every-save-capcut-cli.md` (2.3 KB)
  - capcut-assembly §5: `ATP/reference/capcut-assembly/060_5_qc-of-the-project.md` (1.2 KB)
  - production-agents §5: `ATP/reference/production-agents/050_5_this-session-as-agents-report.md` (2.0 KB)

## 6. Wrap-up (both modes)

Report in a short table: video → direction/edit → model → duration → credits → verdict → file path.
In Edit Mode the file paths point into `<given path>/final/`; state that folder once.
In Analyze Mode the table also names each video's **CapCut project**:
- First assemble any projects still pending. If CapCut is running, ask the user once to close it
  (a blocker, not a permission), then assemble them.
- Then say: "open CapCut → the projects are listed by name → review → Export".
Then give:
- the total credits used (`transactions` / `balance`);
- the run folder (keep it: the CapCut projects use its files);
- the examples used ("6 examples → house approach applied") or "no examples";
- the guardrails applied ("G1–G5 from brand-rules.pdf; 2 references dismissed: V04 (G1, the gore
  is the prank), V09 (G3, a taste test); 3 picks edited: counts, de-branding, face swaps") or
  "no guardrails supplied";
- only if `config.json → capcut.text_style.learned` is ever empty (it holds the user's locked
  preset): "To copy CapCut's exact text preset, add a text in any CapCut project, pick the preset,
  close CapCut, and run `T capcut-text-style --learn --draft "<store>/<that project>"`";
- the flags (item 23): "N flags recorded in `caught_flags.html` (CF-…): M cleared, K persistent",
  and that `T caught-flag open` shows them grouped and searchable,
  each persistent or open one with its video, the flagged prompt or video and what was tried;
  or "no flags this run";
- any open issues.

Both modes: reconcile the flags before the table. Run `T caught-flag reconcile --run RUN`; every
`flagged_unrecorded` row gets `T caught-flag add` now, each `failed_to_judge` row is read and
marked or dismissed (a validation or credit error is not a flag), and every entry of the run is
`cleared` (with its accepted request) or `persistent`; none is left `open` without a reason.

Analyze Mode: check the briefs before the feedback question. Every `result.json` whose `qc` says
RESIDUAL FAILURE or regenerated has an attempt block in its video's brief, so no flagged delivery leaves
the run unexplained.

Analyze Mode: before the table, check the run's deliverables and text. Every video in `state.json` →
`videos[]` has `video-NN-clean.mp4` and `video-NN-preview.mp4` in `<RUN>/deliverables/` (all videos in that
one folder; a with-inserts clean built from the pieces, the inserts and the original audio, never
overwritten by a generated-only clip) and a row in `deliverables/README.md`; the plan and brief files carry
every attempt; no CapCut text layer of any project contains an emoji (the user's rule, strict); and every
size figure in the table was viewed on a frame with its method (two estimates, a derived distance), never
repeated from an agent's provisional number. What is missing is fixed before the table is shown.

Offer, in one line, the next useful step (more videos, a different direction, regenerate a flagged
video). Then, once every video is delivered, **ask for feedback** with AskUserQuestion (header
"Feedback"), "Watch the videos: is any of them not right?": **"All good"**; **"I'll watch them
later"** (any later message about them is handled as item 22 says); **"Some need fixes"** → ask in plain
chat which video and what is wrong, disliked or illogical. "Other" lets the user type it
directly. Each problem named, now or in a later session, is handled as item 22 says: their words verbatim
and the diagnosis go into the video's brief before the fix is offered. When a problem is a kind the
references do not hold, add one line: "Run `/update-from-errors analyze-then-pick "<their words>"` to
generalise this into the prompting and QC."

### 6b. Upscale the finals with Topaz (after the user's approval, both modes)

Once the generated videos and the editing are done, and after the feedback question, offer the
upscale. It runs only on the user's yes, never on its own, and never before the finals exist.
- **The folder.** Edit Mode: `<given path>/final/`. Analyze Mode: the folder the user exported
  the CapCut projects to; the pipeline does not know it, so the question asks for it (the clean
  videos in `60-outputs` are not the finals and are never upscaled unless the user names that
  folder).
- **Ask** with AskUserQuestion (header "Upscale"), "Upscale the final videos 1.5x with Topaz?":
  **"Yes, <folder>"** (Edit Mode: the final folder; Analyze Mode: "Yes, after I export: here is
  the folder" and the user types the path under "Other"); **"Not now"** (say the two commands so
  the user can run them later). Never run on "Not now".
- **Run**, in one PowerShell call, exactly these two commands with the folder filled in (the
  `-notmatch` filter skips files already upscaled, `…_1.5x.mp4`, so a rerun is safe; the script
  writes `<name>_1.5x.mp4` beside each source and `-Yes` skips its cost prompt):
  ```powershell
  cd "$env:USERPROFILE\Scripts"
  Get-ChildItem -Path "<folder>" -Filter *.mp4 | Where-Object { $_.Name -notmatch '_[\d.]+x\.mp4$' } | ForEach-Object { .\topaz-upscale.ps1 -InputFile $_.FullName -Scale 1.5 -Yes }
  ```
  The script needs `ffprobe` on PATH and `TOPAZ_API_KEY` set; if it stops on either, report the
  real error and the fix (`winget install Gyan.FFmpeg`; `setx TOPAZ_API_KEY "<key>"`, then a new
  window). It polls Topaz itself; run it in the foreground with a long timeout (10 minutes), and
  if the call times out, check the folder for `_1.5x.mp4` files before anything is rerun.
- **Report** the upscaled files (name → size → path) and any file that failed, with its error.
  Never retry a failed upscale on its own: say what failed and ask.

## Rules this phase owns (contract items 22)

22. **No error ledger: the rules live in the pipeline.** Every lesson learned from a video that went wrong
    (the user's reports, the agents' regenerate reasons) is written, generalised, in the section that owns
    it (`reference/`, the model guides): as a kind (what to achieve, what to avoid) with the miss, its
    cause, the corrected wording and what worked as the sample beside it. There is no `caught_errors.md`,
    no `T caught-error`, no per-run digest of past errors, and nothing in a run reads an error file: the
    plan, the prompt and QC follow the references. The only error text a run writes is a video's own
    attempt block in its brief, `result.json`, and the Higgsfield flag record of item 23; no later run
    reads any of it. `CE-nnn` in the references are case labels of
    those lessons (`README.md`). **When a delivered video is wrong**, in the run or in a later session:
    take the user's words verbatim, diagnose them in pipeline terms (the stage that made the miss and the
    stage that should have caught it), say which section already holds the rule and why it did not
    prevent this video, and offer the fix (a re-edit or a regeneration of that video in its mode); when the
    miss is a kind the references do not hold, say so in one line and name `/update-from-errors
    analyze-then-pick` with the user's words as its argument, which generalises them into the owning
    sections. A user's word outranks the agents' QC on the same point: the user saw what QC passed. **The
    agents** write a regenerate reason or a flagged delivery in the video's brief (an attempt block with the
    failed request, the verdict and what changed) and in `result.json` (`reference/production-agents.md` §3
    item 12); nothing else is written to the library but the Higgsfield flag record of item 23.

## Never (this phase)

- Never run the Topaz upscale without the user's explicit yes in the wrap-up, never run it on
  the clean generations instead of the finals, and never rerun or retry it on your own (§6b).
- Never create or read an error ledger (item 22): a video the user reports as wrong is diagnosed with their
  words verbatim, in its brief, and fixed only after the diagnosis.
- Never close a run with a RESIDUAL FAILURE or a regenerated video that has no attempt block in its
  brief (A9b, §6). Never copy an agent contract from an earlier run: it is generated at A9 from
  `reference/production-agents.md` §2.

## Hand-off

`T state --run RUN set stage=done`. A video the user later reports as wrong: invoke Skill `atp-feedback`.
