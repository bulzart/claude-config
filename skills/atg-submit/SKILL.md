---
name: atg-submit
description: /analyze-then-generate per-video steps X5/X7: ledger-recorded submit, wait, flags. Internal to that command.
user-invocable: false
---

# atg-submit — Steps X5/X7: preflight again, submit and wait, flags

> `ATG` = `C:/Users/Glaresquare1/.claude/analyze-then-generate` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$ATG/scripts/atg.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `ATG/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `ATG/reference/<file>/` (models: `ATG/models/<guide>/`, Higgsfield: `ATG/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

A production agent comes here after `atg-inputs`. The Higgsfield tools were loaded in `atg-inputs`. Provenance labels: **[E]** evidence · **[I]** inference · **[U]** user instruction · **[A]** client asset · **[M]** model knowledge · **[G]** generation instruction.
Changing a request (the one diagnosed retry of X7 step 5, or after a flag): invoke Skill `atg-write-request` for the rewrite, then return here for X5 and X7. A production agent never asks the user: where a line below or in a Higgsfield guide says to ask (`unlim_choice`, authentication, a permission), write `result.json` with `"status":"blocked"` and the blocker, then stop.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- higgsfield-mcp §3: `ATG/higgsfield/higgsfield-mcp/030_3_standard-execution-sequence-for.md` (3.9 KB)
- higgsfield-mcp §8: `ATG/higgsfield/higgsfield-mcp/080_8_credits-and-cost.md` (1.1 KB)
- higgsfield-mcp §9: `ATG/higgsfield/higgsfield-mcp/090_9_errors-and-recovery.md` (2.5 KB)
- *Edit Mode or Recreate (the moderation fallback after a refused request):*
  - generation-system §5c.2: `ATG/reference/generation-system/250_5c.2_the-most-preserving-input-and-pa.md` (2.4 KB)
- model guide sections: the locked model's guide (`T model-entry --id <model>` prints `guide` and `sections_dir`; see `atg-model-guide`) — §2.1 (parameters per id), §2.3 (duration/aspect/audio), §2.5 (parameter gotchas)

## Step X5 (again, only when the request changed)

- **X5 — Preflight.**
  - `generate_video {params:{…, get_cost:true}}` → cost and `adjustments`. **One** preflight per
    distinct request. Preflight again only after the request changed.
  - Reconcile every adjustment: an unsupported or dropped parameter means rethinking the request,
    not ignoring it.
  - Project folder: create it once per run (`list_workspaces` → `create_project`, keyed by the run
    id) and pass `folder_id`.

## Step X7

- **X7 — Submit and wait (ledger-recorded; no spam, no glitches).**
  1. `T ledger begin --run RUN --video NN --attempt K --request 50-requests/video-NN[-aK]-request.json`
     (a clip: `--video NN-cK` with its own request file).
     - It **records a `pending` entry every time** and exits 0; it never refuses. It reports `conflicts[]`
       as facts, with the entries involved: an open submission (pending / submitted / unknown) in this
       video's lane; the submissions in flight in the run against the cap (`open_in_run`, `cap`); this
       exact request failed before; this exact request already produced a finished job. **You decide
       whether to submit**, under the production rules: one job in flight per video, none past
       `production.max_parallel_jobs`, never the same request again once it produced a finished job, and a
       diagnosis before another attempt. Act on what it shows:
       - an open job exists → resolve it with `jobs_wait`, or for `pending` / `unknown` via
         `show_generations {type:"video", only_completed:false, size:5}` and `transactions`;
       - the request is a duplicate of a finished job → reuse that job;
       - the request failed before → diagnose it first; one retry of the identical request is allowed,
         and after a second failure change it or report the failure;
       - if you decide **not** to submit, record that: `T ledger set --run RUN --fingerprint F --status
         superseded --note "<why>"`, which frees the lane.
  2. Exactly **one** `generate_video {params}` call: `count` 1, no `get_cost`, never in parallel with
     anything, never twice in one turn, never inside a retry loop.
  3. Record the outcome at once:
     - a job id came back → `T ledger set --run RUN --fingerprint F --job J --status submitted`;
     - a transport error or timeout with no job id → `--status unknown`. Then find out what happened
       (history and transactions), and set `submitted` with the found job id, or `failed` with the
       note "not created". Only then begin a new attempt (an `unknown` entry counts as an open
       submission in the lane).
     - Handle `unlim_choice` (ask), `recovery_tool` (call it), and validation errors. A validation
       error means nothing was created: set `failed` with the note "rejected before creation", fix
       only the named field, and begin a new attempt.
  4. Poll `jobs_wait {jobs:[{index:0, job_id}], timeout_seconds:15}`, respecting
     `poll_after_seconds`.
     - Terminal → `T ledger set --job J --status completed|failed`.
     - Still running after ~25 min → tell the user, and keep waiting on that same job. Never
       resubmit because a job is slow.
  5. A failed job is refunded. Diagnose it before any retry; retry an identical request at most once
     (`begin` reports a request that failed before, and the decision is yours).
  6. **A flag is recorded before the request changes** (item 23). When Higgsfield blocks, refuses,
     withholds or reroutes (a moderation or policy message; a job failed within seconds with no
     reason; an upload, video or Element marked `nsfw` / `ip_checking` / `failed`; an output
     withheld; a `preset_recommendation` notice instead of a job):
     - `T ledger set --run RUN --job J --status failed --flagged --note "<what came back>"` (no job id:
       `--fingerprint F`);
     - `T caught-flag add --run RUN --video NN --attempt aK --kind <…> --tool <…> --stage <…>
       --response "<verbatim | none given>" --credits "<refunded n>" --trigger "[E|I] <suspected
       trigger>" --cause <…> --tags <1 to 4 labels> [--asset "Image 2"] [--prompt-span "<the exact
       words>"] [--part-of "reference V10" --part-from 3.2 --part-to 6.0] --product …` (the request's
       prompt and params, every input with its file and thumbnail, the reference, the source segment,
       the plan and the flagged ledger row are attached from the run; name the asset, the words and the
       part only when you can tell). The flag is stored in Loupe (it assigns the `CF-nnn`). The script also
       reads each input's file facts (sha1, size, dimensions, printed words) and whether the same file went
       through earlier runs, and attaches the raw answer that the Higgsfield hook saved when it came back
       (matched by job id; otherwise name it with `--capture <id>` from the hook's reminder). Loupe down: the
       entry waits in its outbox and the call still succeeds;
     - then change the request (the one diagnosed retry of X7 step 5; after the second identical
       refunded failure, never a third: plan without the trigger, for example without the video
       reference, `generation-system.md` §5c.2), say what changed with `caught-flag set --changed`,
       and once that request is accepted `caught-flag set --id CF-nnn --status cleared
       --cleared-prompt <request.json> --cleared-job J`. A flag that stays is `--status
       persistent --note "<what was tried>"` and the video is reported in the wrap-up;
     - a flagged **input** (an asset or a reference video that came back marked) is recorded the
       same way with `--stage upload` and the file's path, and is replaced by another supplied
       asset, never re-uploaded unchanged.

## Rules this phase owns (contract items 3, 12, 23)

3. **Generation lanes.** Every video is a lane with **one job in flight at a time**:
   plan → preflight → brief → submit → wait → download → post-process → QC.
   - The ledger records every submission and reports what is already in flight; the agents keep to at
     most `production.max_parallel_jobs` (5) jobs in flight per run, across the production agents
     (`T ledger begin` reports the open submissions against that cap; whether to submit is the
     agent's decision, X7).
   - Never use `generate_video_batch`, never submit twice in one lane, and never start an
     uncontrolled batch.
   - A multi-clip video runs **clip by clip** inside its lane: a clip is submitted only after the
     previous clip passed QC (`generation-system.md` §3b).
   - Edit Mode runs one video at a time.
12. **Generation discipline: no spam, no glitches.**
    - Every paid Higgsfield generation (`generate_video`, and `generate_image` for start frames)
      goes through the ledger (`T ledger begin` before, `T ledger set` after; §5 X7: the ledger
      records and reports, the agent decides). There is at most **one job in flight per video lane**, at
      most 5 per run, one generation call per turn per agent, and never parallel calls inside a lane.
    - Never resubmit after a timeout or an unclear answer until the outcome has been checked, and
      never resubmit because a job is slow.
    - Never repeat an identical finished request.
    - Preflight (`get_cost`) once per distinct request.
    - Never call generation tools to "test" or "retry just in case".
23. **Caught flags: every prompt and video that Higgsfield flagged is recorded**
    (in Loupe, the pipeline's web app at `http://127.0.0.1:8787`: a database with a viewer that searches,
    filters and groups, written only with `T caught-flag`; `T loupe open --path /#/flags` shows it to the user).
    A flag is any time Higgsfield refuses, blocks, withholds or reroutes something during the run: a
    moderation or policy block, a job that fails within seconds with no reason (refunded), an upload,
    video or Element marked `nsfw`, `ip_checking` or `failed`, an output withheld, or a notice returned
    instead of a job (`preset_recommendation`). Validation errors (a prompt over 5000
    characters, out of credits) are not flags. **Whoever made the call records it at once,
    before changing the request** (agents and this session alike, in both modes): mark the
    submission with `T ledger set … --flagged`, then `T caught-flag add --run RUN --video NN --attempt aK`.
    **The script gathers** what the run already knows: the request's prompt and parameters, every input
    with its file, type, V or A id and a thumbnail, the reference video and the source segment it covered,
    the plan and the brief, and the job and fingerprint of the ledger row marked flagged. **The agent
    supplies the judgement:** Higgsfield's response verbatim (or "none given"), the kind, the tool and
    stage, the credits, its **suspected trigger** labelled [E] or [I], and what Loupe searches and
    groups by: `--tags` (1 to 4 labels for the trigger, for example `real-person-face`, `celebrity-name`,
    `brand-name`, `protected-ip`, `nsfw-image`, `video-reference`, `element`, `prompt-wording`,
    `preset-notice`, `output-withheld`, `unknown-trigger`), `--asset` (which input: `"Image 2"`,
    `"Video 1"`, a media id, a file name or an A or V id; a file path for an upload flag),
    `--prompt-span` (the exact words of the prompt) and `--part-of` / `--part-from` / `--part-to` (which
    video, which seconds). Name what can be told and leave the rest out: the script lists what was not
    given and never guesses. After the changed request is accepted:
    `T caught-flag set --id CF-nnn --status cleared --cleared-prompt <the accepted request.json>
    --cleared-job J` (never `cleared` before a request went through; a flag that stays is
    `persistent` and the video is planned another way or reported). **The record is written, never
    read during a run:** no step of a run (A1, E1, a plan, X4) and no agent contract lists, searches or opens it,
    and no digest or copy of it is made, because a growing record read at every run start rots the agents'
    context. (Only the sample library is read: by QC through `T qc-consult` and by the first request of a video through `T plan-hints`; never the flags.) What a flag
    teaches is held as a general rule in the references (`generation-system.md` §5c.2, the model guides'
    failure tables, `higgsfield/higgsfield-mcp.md` §9), and X4 tests the plan against those rules. The
    main session runs `T caught-flag reconcile --run RUN` as each agent reports and in the wrap-up; it
    only lists the calls marked flagged that have no entry yet, so no flagged call leaves the run
    unrecorded. A flag whose rule is general or recurs is written into those references as a rule when the user asks for it; the entry stays as the record.
    The user opens Loupe to see the flags grouped by trigger, asset, video, kind, run or model and searched
    by field, with the evidence Loupe gathered next to each.

## Never (this phase)

- Never list, search or read the flag record or hand it to an agent during a run (item 23: it is written, not read), never
  change or resend a request that Higgsfield flagged before its `T caught-flag add` entry exists (the verbatim
  response, the prompt, the media, the flagged video, the suspected trigger), never write an
  entry by hand, never mark one `cleared` before a changed request was accepted, never send a
  third identical request after two refunded flagged failures, and never re-upload a flagged
  asset or video unchanged (item 23).
- Never call a generation tool outside the ledger (`T ledger begin` / `set`), and never take the ledger's silence for
  permission or its `conflicts[]` for a refusal: read them, decide, and when you do not submit record why
  (`ledger set --status superseded --note`).
- Never submit in parallel, never resubmit after an unknown outcome or a slow job, never repeat a
  finished request, never pass URLs or paths as media values, and never set `use_unlim` unasked.

## Hand-off

When the job is terminal: invoke Skill `atg-postprocess` (X8; its first step downloads the result).
