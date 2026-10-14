---
name: atp-precheck
description: /analyze-then-pick per-video steps X4-X6: pre-generation QC, preflight cost, brief. Internal to that command.
user-invocable: false
---

# atp-precheck — Steps X4–X6: pre-generation QC, preflight, brief

> `ATP` = `C:/Users/Glaresquare1/.claude/analyze-then-pick` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$ATP/scripts/atp.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `ATP/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `ATP/reference/<file>/` (models: `ATP/models/<guide>/`, Higgsfield: `ATP/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

Callers. Edit Mode: X4, X5, X6 in sequence for the video. Analyze Mode, this session (A9): **X4 only** at A9 step 1 for each video; **X5 and X6** at A9 step 3 for each video, after the shared uploads of step 2. Production agents do not use this skill.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- generation-system §8: `ATP/reference/generation-system/330_8_pre-generation-qc-pass-mental-re.md` (7.0 KB)
- generation-system §10: `ATP/reference/generation-system/360_10_the-short-brief-printed-at-x6.md` (3.1 KB)
- *Edit Mode or Recreate:*
  - generation-system §5c.2: `ATP/reference/generation-system/250_5c.2_the-most-preserving-input-and-pa.md` (2.4 KB)
  - generation-system §5c.4: `ATP/reference/generation-system/280_5c.4_check-before-spending-x4.md` (0.5 KB)
- *a contents or placement video:*
  - generation-system §4b.1b: `ATP/reference/generation-system/140_4b.1b_posture-support-and-place-every.md` (3.1 KB)
  - generation-system §4b.1c: `ATP/reference/generation-system/150_4b.1c_is-the-spot-feasible-read-the-so.md` (3.1 KB)
- *the plan has a size-and-place guide:*
  - generation-system §4b.6: `ATP/reference/generation-system/200_4b.6_the-size-and-place-guide-a-refer.md` (4.1 KB)
- anomaly-catalog §3: `ATP/reference/anomaly-catalog/210_3_the-prompting-stack-in-order-per.md` (2.1 KB)
- *a placed or contents product (size, label, posture checks):*
  - anomaly-catalog §2.7: `ATP/reference/anomaly-catalog/100_2.7_scale-and-proportion-the-size-re.md` (11.1 KB)
  - anomaly-catalog §2.9: `ATP/reference/anomaly-catalog/120_2.9_orientation-label-and-parts.md` (3.3 KB)
  - anomaly-catalog §2.16: `ATP/reference/anomaly-catalog/190_2.16_posture-support-and-place.md` (4.3 KB)
- higgsfield-mcp §8: `ATP/higgsfield/higgsfield-mcp/080_8_credits-and-cost.md` (1.1 KB)
- higgsfield-mcp §9: `ATP/higgsfield/higgsfield-mcp/090_9_errors-and-recovery.md` (2.5 KB)
- model guide sections: the locked model's guide (`T model-entry --id <model>` prints `guide` and `sections_dir`; see `atp-model-guide`) — §5 (failure table), §7 (pre-generation checklist)
- the plan, the pattern card and the request(s) of this video

## Steps X4, X5, X6

- **X4 — Pre-generation QC.**
  - Run the mental render of `generation-system.md` §8 from the first frame to the last.
  - **Fidelity check** (item 19; Edit Mode and Recreate; `generation-system.md` §5c.4): walk the
    source action script beat by beat. Every keep beat is carried by the source input or named in
    the prompt. Nothing in the prompt invites new motion. The duration matches the source segment.
    No change operation forces a motion change: a bigger product gets a planned grip that keeps the
    same hand path.
  - **Service blocks** (`generation-system.md` §5c.2 moderation fallback; `higgsfield/higgsfield-mcp.md` §9;
    the model guide's failure table): the request carries no trigger those rules name (a real person's
    face riding in the video reference without the planned fallback, protected IP or a real person's
    likeness claimed in the prompt, a flagged asset sent again unchanged). A trigger the plan cannot avoid
    is written in the brief as a risk, and the fallback request (for example without the video reference,
    fidelity and sync at risk) is planned before the first submission. Nothing here opens `caught_flags.html`.
  - **Counts, openings and permanence** (`anomaly-catalog.md` §3): walk every use beat (the
    preparation step, the part, the contact point, the head and hands), every multiple's number at
    every event, every effect's cause, every restatement after an exit, occlusion, cut, hand-off or
    seam, and the path of every thrown, dropped or passing thing relative to the product (§2.14).
  - **Size** (`anomaly-catalog.md` §2.7): every product's reckoning, its distance derived from the
    frame and not assumed, is in the plan and in the prompt for every shot; a start frame passed `T scale`; the size ladder holds between products;
    nothing in the prompt or the references invites a bigger product (a tight crop, "hero",
    "prominent", a packshot pose).
  - **Posture, support and place** (`generation-system.md` §4b.1b; `anomaly-catalog.md` §2.16): every
    anchor is a posture its shape allows, on a visible support, where a person would leave it, with
    its story reason; no lean on a prop the model has to invent, nothing on a thin sheet, no source
    beat taken over. Where the guide lists size as a model limit, the anchor is from its passing list or a
    size-and-place guide (§4b.6) carries spot and size.
  - **Spot and guide** (`generation-system.md` §4b.1c, §4b.6; `anomaly-catalog.md` §2.9): the spot passes the
    feasibility lines; a guide holds nothing of the performer, clothing or lettering, shows the product shaded in perspective with a
    sharp label and fits the reckoned size (`T scale --frame`); the wordmark's pixel height from the size
    reckoning is at least about 25 px, or the limit is written in the brief.
  - **Source surfaces:** each printed surface a guardrail or §9b names is a "replace / remove only …
    reconstruct as <named content>" sentence, never a description of blankness, with the original in
    the exclusion line.
  - Fix any conflict in the plan and the request before continuing.
- **X5 — Preflight.**
  - `generate_video {params:{…, get_cost:true}}` → cost and `adjustments`. **One** preflight per
    distinct request. Preflight again only after the request changed.
  - Reconcile every adjustment: an unsupported or dropped parameter means rethinking the request,
    not ignoring it.
  - Project folder: create it once per run (`list_workspaces` → `create_project`, keyed by the run
    id) and pass `folder_id`.
- **X6 — Brief.**
  - Print the short brief (`generation-system.md` §10): concept, why it works, reference pattern,
    characters/assets, substitutions, main action and states, style/camera, text plan, model /
    operation / duration / 9:16 720p, cost, adaptation logic. In Edit Mode and Recreate it also names
    the fidelity approach (input, mode, written-out script or not) and any risk to fidelity or sync.
  - Save it as `40-briefs/video-NN-brief.md`; each attempt or clip appends its own block under the first
    (the failed request, the verdict, what changed), so a reported problem can be read against what was
    planned and asked (item 22).
  - Analyze Mode: no gate; the brief is information (item 15). Edit Mode: the E6 gate.

## Rules this phase owns (contract items 12)

12. **Generation discipline: no spam, no glitches.**
    - Every paid Higgsfield generation (`generate_video`, and `generate_image` for start frames)
      goes through the ledger (`T ledger begin` before, `T ledger set` after; §5 X7). There is at
      most **one job in flight per video lane**, at most 5 per run, one generation call per turn
      per agent, and never parallel calls inside a lane.
    - Never resubmit after a timeout or an unclear answer until the outcome has been checked, and
      never resubmit because a job is slow.
    - Never repeat an identical finished request.
    - Preflight (`get_cost`) once per distinct request.
    - Never call generation tools to "test" or "retry just in case".

## Never (this phase)

- Never read `ATP/caught_flags.html` or hand it to an agent (item 23: it is written, not read), never
  change or resend a request that Higgsfield flagged before its `T caught-flag add` entry exists (the verbatim
  response, the prompt, the media, the flagged video, the suspected trigger), never write an
  entry by hand, never mark one `cleared` before a changed request was accepted, never send a
  third identical request after two refunded flagged failures, and never re-upload a flagged
  asset or video unchanged (item 23).
- Never submit in parallel, never resubmit after an unknown outcome or a slow job, never repeat a
  finished request, never pass URLs or paths as media values, and never set `use_unlim` unasked.

## Hand-off

- Edit Mode: show the "Go" gate (E6) for the first video, then invoke Skill `atp-submit` (X7).
- Analyze Mode, A9 step 1 (X4): next video's X1; when every video has its plan, request and X4, continue A9 step 2 in `atp-analyze-produce` (shared uploads via `atp-inputs`).
- Analyze Mode, A9 step 3 (X5–X6 of every video): continue A9 steps 4–5 in `atp-analyze-produce`.
