---
name: awl-precheck
description: /analyze-with-loupe per-video steps X4-X6: pre-generation QC, preflight cost, brief. Internal to that command.
user-invocable: false
---

# awl-precheck — Steps X4–X6: pre-generation QC, preflight, brief

> `AWL` = `C:/Users/Glaresquare1/.claude/analyze-with-loupe` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$AWL/scripts/awl.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `AWL/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `AWL/reference/<file>/` (models: `AWL/models/<guide>/`, Higgsfield: `AWL/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

Callers. Edit Mode: X4, X5, X6 in sequence for the video. Analyze Mode, this session (A9): **X4 only** at A9 step 1 for each video; **X5 and X6** at A9 step 3 for each video, after the shared uploads of step 2. Production agents do not use this skill.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- generation-system §6: `AWL/reference/generation-system/310_6_conflict-resolution-resolve-befo.md` (4.3 KB)
- generation-system §8: `AWL/reference/generation-system/330_8_pre-generation-qc-pass-mental-re.md` (7.4 KB)
- generation-system §10: `AWL/reference/generation-system/360_10_the-short-brief-printed-at-x6.md` (3.2 KB)
- *Edit Mode or Recreate:*
  - generation-system §5c.2: `AWL/reference/generation-system/250_5c.2_the-most-preserving-input-and-pa.md` (2.4 KB)
  - generation-system §5c.4: `AWL/reference/generation-system/280_5c.4_check-before-spending-x4.md` (0.5 KB)
- *a contents or placement video:*
  - generation-system §4b.1b: `AWL/reference/generation-system/140_4b.1b_posture-support-and-place-every.md` (2.6 KB)
  - generation-system §4b.1c: `AWL/reference/generation-system/150_4b.1c_is-the-spot-feasible-read-the-so.md` (3.1 KB)
- *a placed product (the original is the only video reference):*
  - generation-system §4b.5: `AWL/reference/generation-system/190_4b.5_expressing-it-to-the-model-with.md` (6.5 KB)
- anomaly-catalog §3: `AWL/reference/anomaly-catalog/210_3_the-prompting-stack-in-order-per.md` (2.4 KB)
- *a placed or contents product (size, label, posture checks):*
  - anomaly-catalog §2.7: `AWL/reference/anomaly-catalog/100_2.7_scale-and-proportion-the-size-re.md` (12.3 KB)
  - anomaly-catalog §2.9: `AWL/reference/anomaly-catalog/120_2.9_orientation-label-and-parts.md` (3.4 KB)
  - anomaly-catalog §2.16: `AWL/reference/anomaly-catalog/190_2.16_posture-support-and-place.md` (3.9 KB)
- higgsfield-mcp §8: `AWL/higgsfield/higgsfield-mcp/080_8_credits-and-cost.md` (1.1 KB)
- higgsfield-mcp §9: `AWL/higgsfield/higgsfield-mcp/090_9_errors-and-recovery.md` (2.5 KB)
- model guide sections: the locked model's guide (`T model-entry --id <model>` prints `guide` and `sections_dir`; see `awl-model-guide`) — §5 (failure table), §7 (pre-generation checklist)
- *an own voiceover (the plan has a Voiceover block; item 31):*
  - voiceover §6: `AWL/reference/voiceover/060_6_in-the-request-x2-by-what-the-lo.md` (3.3 KB)
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
    fidelity and sync at risk) is planned before the first submission. Nothing here lists or opens the flag record.
  - **Counts, openings and permanence** (`anomaly-catalog.md` §3): walk every use beat (the
    preparation step, the part, the contact point, the head and hands), every multiple's number at
    every event, every effect's cause, every restatement after an exit, occlusion, cut, hand-off or
    seam, and the path of every thrown, dropped or passing thing relative to the product (§2.14).
  - **Rules that pull apart** (`generation-system.md` §6): read the final prompt as the model will, beat by beat. No two sentences ask
    opposite things of the same beat, no "never" or "always" stands outside the product's one targeted exclusion and the fidelity
    lock's scoped "only", and every placement, posture and use line follows from the product's own details and what the source scene
    offers, not from an example. A line that fights another is dropped by the §6 order of authority, with its reason in the brief.
  - **Must carry** (the first request of a video): the pattern card's "Must carry" block and `RUN/40-briefs/video-NN-musts.md`
    hold, word for word and one per line, every sentence the prompt must carry exactly (the fidelity lock, the clean-plate lines, the camera lock, the targeted exclusion, a guardrail operation, the voiceover line), and the
    draft carries each of them. The judge builds the final prompt on this checked draft and these lines (X4b).
  - **Size** (`anomaly-catalog.md` §2.7): every product's reckoning, its distance derived from the
    frame and not assumed, is in the plan and in the prompt for every shot; a start frame was measured
    with `T scale` and its size factors read (X9 gives the bands); the size ladder holds between products;
    nothing in the prompt or the references invites a bigger product (a tight crop, "hero",
    "prominent", a packshot pose).
  - **Posture, support and place** (`generation-system.md` §4b.1b; `anomaly-catalog.md` §2.16): every
    anchor is a posture its shape allows, on a visible support, where a person would leave it, with
    its story reason; no lean on a prop the model has to invent, nothing on a thin sheet, no source
    beat taken over. Where the guide lists size as a model limit, the anchor is from its passing list or the
    size risk is written in the brief.
  - **Spot** (`generation-system.md` §4b.1c, §4b.5; `anomaly-catalog.md` §2.9): the spot passes the feasibility
    lines and the prompt pins it to a fixed neighbour. In Recreate and Edit Mode, whatever the model, the request
    binds the original reference (silent, unmarked, the plan's span) in the model's most preserving input, for
    the scene and the keep-list, as its only video reference, within the model's own limits (its guide §2.2,
    §2.5); nothing that places the product rides beside it, no exclusion of the original's content covers the
    product, and no guide image cut from a source frame is in the request. A start or end frame's product is
    photoreal and passed the paste test. The wordmark's pixel height from the size reckoning is at least about
    25 px, or the limit is written in the brief.
  - **Source surfaces:** each printed surface a guardrail or §9b names is a "replace / remove only …
    reconstruct as <named content>" sentence, never a description of blankness, with the original in
    the exclusion line.
  - **Own voiceover** (item 31): the take is recorded (`state.json → voiceover.files.NN`) and the request binds it by the run's method
    exactly as `voiceover.md` §6 says (the audio role, the dialogue or no-dialogue line, the duration); nothing asks for music.
  - **Memes** (Create, item 32): with `memes=none`, no insert, split point or meme sound in the plan or the request, and no imitated meme.
  - Fix any conflict in the plan and the request before continuing.
- **X4b — The judge writes the final prompt (the first request of a video; the user, 2026-10-28).** X1–X4 are done: the plan, the
  pattern card, the checked draft request and its must-carry lines. Now the whole brief goes to the judge (Loupe's keeper, one separate
  Opus session that holds the admin's samples of earlier generations, many with the flawed version's prompt and the correct version's prompt, each holding only the generations its frames come from; an example prompt is a suggestion, neither bad nor correct),
  and the judge's answer is the prompt this video is generated from. The prompt is the judge's: nothing after X4b improves it.
  1. Write the judge brief `RUN/40-briefs/video-NN-judge-brief.md`: what you are working on (run, video, mode, the locked model, the
     request kind and its inputs with their roles), what the video is about (one line per beat of the plan: what happens, the product's
     form and state, the camera), what it wants to achieve (the goal, the moment that must land, what it keeps of the source), and what
     X4 found the prompt must respect (a size, a count, a fallback).
  2. `T prompt-template --run RUN --video NN --structure-file RUN/50-requests/video-NN-pattern.md --product "<form>" --product-details
     "<its shape, size, opening and natural posture, from its registry row>"` (a clip: `--clip cK`). The toolkit sends that brief, the
     checked draft's prompt, parameters and inputs (each with the client's original it was made from: its asset id, its file name and how
     it was prepared), the client's images of the product (its registry row), the must-carry lines and the video model's entry of the model
     index. The judge reads the saved prompts of the samples it chooses and answers `template`: the final prompt in the locked model's
     structure, built on the checked draft and on what worked and what failed before, every must-carry line word for word. It also decides
     which of the product's images the request carries and how many (`product_images`, the admin 2026-10-30; empty keeps the draft's).
     It also goes through every sample of its library, read or not and whatever the product, and designs out of its prompt every miss
     that could happen in this video through the same mechanism (the admin, 2026-11-03). The toolkit writes that whole judgement (the
     samples read, every miss designed out with its mechanism and where, the samples set aside and why) to
     `RUN/40-briefs/video-NN[-cK]-judgement.md` and prints only its counts (`judged`) and the file. **Never paste the judgement into the
     chat:** name the file; read it only when a part of the prompt is unclear to you.
  3. `T template-apply --run RUN --video NN [--slot "<slot words>=<value>" …]` puts it in the request word for word (the draft is kept as
     `video-NN-request.draft.json`) and reports, as facts, the must-carry lines it does not hold word for word, the slots left and its
     length against the service's 5000 characters. With the judge's `product_images` it also puts them in the request: the inputs that are
     not product images keep their numbers and its product images follow in its order (`product_images`: `final`, `kept`, `added`,
     `dropped`, `renumbered`); a must-carry line naming a product image is checked in its new number (`musts_renumbered`; `--add-must`
     takes that form) and one naming an image the judge left out is no longer the request's (`musts_superseded`).
     `product_images_problems` (an image the run's inventory does not hold, product images that are not the last inputs, an asset id and a
     file name that name two files of this run with no fingerprint to tell which) applies none of them; `product_images_notes` says where
     a fingerprint (the 8 characters after # in what the judge read) decided which file an image is; and `prompt_names_images_beyond_the_inputs` lists an image the prompt names that the request does not carry: both are asked of
     the judge once more (step 4). An image it adds is prepared and uploaded in X3 (`awl-inputs`): in Analyze Mode with the shared uploads
     of A9 step 2, in Edit Mode now, before X5.
  4. **Never rewrite, trim, reorder or improve the judge's prompt**, and X4 does not run again on its wording (it ran on the draft). Fill a
     `[SLOT: …]` only with what the plan already decided. A must-carry line missing, a slot that cannot be filled or a length over the
     limit: ask the judge once more with the same arguments plus `--note "<what is missing or too long>"` and apply its new answer. Only if
     it is still missing, add that must-carry line word for word (`--add-must`) and nothing else; still over the limit, or no usable answer:
     the checked draft stays the request (`--use-draft`).
  5. What only you can answer comes back as `needs_unmet` with an `unmet_rule`: answer it from the plan in words and ask once more with
     `--note`. No answer at all (`mode: empty`, `unavailable`, `busy` after the toolkit's retries, an empty `template`): the checked draft is
     the request, as always (`T template-apply --use-draft`).
  6. Write the pattern card's "Judge's template" block: the prompt's file (or "no template: <why>"), the judgement file, the slots filled with what, each
     must-carry line added and why, a `--note` re-ask and its reason, the product images (each by its asset id and original file name;
     any the judge added, left out or renumbered, with its why), the judge's `changes` (parts of the plan earlier generations say should
     change; its prompt already carries them: add one line per change to the plan so QC checks the same), and any judge gap. X6 copies it.
  The judge is not asked again before the generation; after it, QC consults the judge with the prompt used and this brief (`awl-qc`).
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
  - The brief carries the pattern card's short "Judge's template" block (the judge's prompt's file or why there was none, the judgement file, the slots
    filled, any must-carry line added, any re-ask, the product images, the judge's changes), so QC and a reported miss can be read against it.
  - With an own voiceover (item 31) the brief names the method, the voice, the language, the form, the take and its length, the lipsync
    sync pass, and the untested lip risk (`voiceover.md` §6).
  - Save it as `40-briefs/video-NN-brief.md`; each attempt or clip appends its own block under the first
    (the failed request, the verdict, what changed), so a reported problem can be read against what was
    planned and asked (item 22).
  - Analyze Mode: no gate; the brief is information (item 15). Edit Mode: the E6 gate.

## Rules this phase owns (contract items 12)

12. **Generation discipline: no spam, no glitches.**
    - Every paid Higgsfield generation (`generate_video`, and `generate_image` for start frames)
      goes through the ledger (`T ledger begin` before, `T ledger set` after; X7: the ledger
      records and reports, the agent decides). There is at most **one job in flight per video lane**,
      at most 5 per run, one generation call per turn per agent, and never parallel calls inside a lane.
    - Never resubmit after a timeout or an unclear answer until the outcome has been checked, and
      never resubmit because a job is slow.
    - Never repeat an identical finished request.
    - Preflight (`get_cost`) once per distinct request.
    - Never call generation tools to "test" or "retry just in case".

## Never (this phase)

- Never list, search or read the flag record or hand it to an agent during a run (item 23: it is written, not read), never
  change or resend a request that Higgsfield flagged before its `T caught-flag add` entry exists (the verbatim
  response, the prompt, the media, the flagged video, the suspected trigger), never write an
  entry by hand, never mark one `cleared` before a changed request was accepted, never send a
  third identical request after two refunded flagged failures, and never re-upload a flagged
  asset or video unchanged (item 23).
- Never submit in parallel, never resubmit after an unknown outcome or a slow job, never repeat a
  finished request, never pass URLs or paths as media values, and never set `use_unlim` unasked.

## Hand-off

- Edit Mode: show the "Go" gate (E6) for the first video, then invoke Skill `awl-submit` (X7).
- Analyze Mode, A9 step 1 (X4 and X4b): next video's X1; when every video has its plan, its request with the judge's prompt (or the checked draft) and X4, continue A9 step 2 in `awl-analyze-produce` (shared uploads via `awl-inputs`).
- Analyze Mode, A9 step 3 (X5–X6 of every video): continue A9 steps 4–5 in `awl-analyze-produce`.
