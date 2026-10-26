---
name: awl-free-plan
description: /analyze-with-loupe Analyze Mode / Free phase: the user's own requirement becomes the plan of the videos, with or without analysed references, confirmed once (A6f). Internal to that command.
user-invocable: false
---

# awl-free-plan — Free: the user's requirement becomes the plan (A6f)

> `AWL` = `C:/Users/Glaresquare1/.claude/analyze-with-loupe` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$AWL/scripts/awl.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `AWL/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `AWL/reference/<file>/` (models: `AWL/models/<guide>/`, Higgsfield: `AWL/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- `RUN/00-inventory/requirement.md` — the user's requirement, whole (written at the start, `awl-start` step 2; it is [U] and governs this phase)
- creative-direction §5.2: `AWL/reference/creative-direction/080_5.2_the-best-approach-both-sub-modes.md` (1.0 KB)
- creative-direction §6: `AWL/reference/creative-direction/090_6_the-sharpness-gate-before-a-conc.md` (1.0 KB)
- creative-direction §7: `AWL/reference/creative-direction/100_7_hook-payoff-loop-text-and-sound.md` (1.1 KB)
- brand-guardrails §4: `AWL/reference/brand-guardrails/040_4_the-audit-in-the-pipeline.md` (3.8 KB)
- generation-system §4b.0: `AWL/reference/generation-system/120_4b.0_choose-the-integration-form-the.md` (4.1 KB)
- *with references (`state.json → free_references = yes`):* `RUN/20-analysis/synthesis.md`, the cards the requirement names (`RUN/20-analysis/cards/`), and creative-direction §5.0: `AWL/reference/creative-direction/060_5.0_transfer-not-repetition-the-craf.md` (4.7 KB)
- *when a video will edit a reference (kind `recreate`, step 3):* the source-preparation steps E4–E5 of `C:/Users/Glaresquare1/.claude/skills/awl-recreate-plan/SKILL.md` (Read that file from its heading "Edit Mode's E4–E5, as Recreate uses them" to its end; nothing before it)
- *only when the requirement asks for an own voiceover (step 2b; item 31):*
  - voiceover §1: `AWL/reference/voiceover/010_1_the-state-and-the-files.md` (3.0 KB)
  - voiceover §2: `AWL/reference/voiceover/020_2_the-choice-at-the-start-create-f.md` (5.5 KB)
  - voiceover §5: `AWL/reference/voiceover/050_5_on-camera-or-off-screen-and-whic.md` (1.1 KB)

### A6f. Free: the requirement is the plan (Free only)

The user chose Free because the other sub-modes decide the shape of the videos for them. Here the user's requirement decides: what the
videos must achieve, how many, what happens in them, which product and how, whether references are edited, re-made or only studied, the
length, the text, the sound. The pipeline brings what the user did not decide: the locked model's own prompting (its official examples and
recipes, X2), the plan discipline (X1), the pre-generation check, the QC stack and Loupe's samples and misses (plan-hints at X2, the consult
at X9, the flag record), the CapCut assembly and the deliverables. Nothing is asked twice; one confirmation closes the plan.

1. **Read the requirement whole** (`RUN/00-inventory/requirement.md`). Every sentence of it is [U]. Where it is silent, the pipeline's own
   rules fill the gap; where it speaks, it wins over every preference, default or house approach, with one exception: the **hard rules**
   stay (fixed 9:16 at 720p, item 5; clean plates and CapCut text, item 6; client assets only from the user's paths, item 11; the ledger,
   item 12; the product in the video, item 14; the one permission for a long video, item 15; inserts cut and CapCut projects, item 16; the
   brand guardrails, item 21; the anomaly catalog; the user's standing product and text rules). When the requirement contradicts one of
   them, say so in one line in the plan and in the confirmation (step 4) and follow the rule.
2. **Write the free plan** `RUN/20-analysis/free-plan.md`:
   - **Goal** in the user's words (a quote), and the audience and the job the videos do, as the requirement implies ([U] or [I]).
   - **Count:** the number the requirement states; otherwise `state.json → requested_videos` (asked at A5), or 1.
   - **Per video NN:** the one-line idea; its **kind**: `recreate` when the requirement asks to edit, re-shoot, swap into or re-make a
     named reference (write which one, `V##`), else `create` (a new scene); the beats in order as the requirement implies, with the length
     (the requirement's, else the family's typical length with references, else what the beats need, at most 30 s without a permission);
     the product, its form and its integration (swap, contents or placement, `generation-system.md` §4b.0) as the requirement wants it;
     the characters; the overlay text (its wording when the requirement gives it, item 6); the sound; what the requirement explicitly
     wants and explicitly forbids, each as a line the plan, the request and QC will check. Label each line [U], [E] (a card or the
     synthesis) or [I] (your reading).
   - **With references:** write which reference patterns each video follows or must avoid (from the cards and `synthesis.md`), the way
     `creative-direction.md` §5.0 reads a reference (its craft, and its subject only when the user asks for the subject). A `create` video
     that re-uses a reference's subject because the user asked for it is the user's choice: write "[U] the user asked for the subject"
     and skip the copy test for that video.
   - **Without references:** the plan rests on the requirement, the asset registry and the product's affordance sheet alone; where the
     requirement leaves a beat open, write the simplest beat that serves the goal and mark it [I] so the user sees it in step 4.
   - The sharpness gate (§6) and the hook, payoff and share line (§7) are applied as checks of your reading, never to change what the
     user asked for: a weakness is written as a note in the plan and shown in step 4 for the user to decide.
   - **Guardrails** (`brand-guardrails.md` §4) hold as always.
2b. **Own voiceover: only when the requirement asks for it** (item 31; `voiceover.md` §1, §2, §5): ElevenLabs, a voice by name or id, "my
   voiceover", a voice, language, accent or dialect for the spoken words, or voiceover files the user names as such. Then those videos (all
   when it does not say which) get one: the method from its words ("drive the video with my voice" native, only with Wan 3.0, Wan 3.0
   Prime or Wan 2.7; "lip-synced" lipsync; "over the video", "narration" or "voice-over" overlay), the form and the lines' idea per
   video, [U] or [I]; what it leaves open is asked in step 4 (§2, Free). A `recreate`-kind video keeps its source's audio and mouths (a voice
   over it only when asked, never re-synced). Without such a requirement nothing about a voiceover is offered, asked or written.
2c. **Memes and other cut-in clips: the requirement decides** (item 32): `memes=include` when it asks for them, `none` when it forbids
   them; silent, a `create`-kind video plans one only as a visible [I] line of step 4 (the user's yes makes it `include`), else `none`. A
   `recreate`-kind video keeps its reference's own inserts; when the requirement forbids memes for one, step 4 says so in one line.
3. **Past misses that touch this requirement (Loupe, no model call):** for every product of the plan run
   `T qc-brief --run RUN --product "<form>" --product-details "<shape, size, opening, posture from its registry row>" --question "<the
   requirement's actions with that product, in one line>"` and write the matching samples (id and title; a sample marked `prompts` also keeps the prompts of its
   two takes, which X2 reads with `T sample-prompts` only for a hint it applies, never this phase) under "Past misses that touch
   this requirement" in the free plan, as leads for X1 and QC. They are information: nothing of them goes into a prompt as a negative
   (`generation-system.md` §4, §5c.2b); X2 asks the keeper for hints as always and X9 consults it once per video. A `recreate` video
   also needs its prepared source: `T split-audio "<references folder>" --run RUN` once, then the E4–E5 steps of `awl-recreate-plan` for
   that reference (the own/ folder with `strip-inserts` and `seams`).
4. **Confirm once.** Ask with AskUserQuestion (header "Your plan"): show one line per video (number, kind, length, product and its
   integration, the idea) plus every [I] line that fills a gap, every hard rule the requirement crossed, and any sharpness note; the
   options are **"Yes, produce it"** and **"Change it"** ("Other" takes the user's words: apply them to the plan, show it again, until
   the user says yes). A change that asks for more generations than the plan priced is shown with its cost. When step 2b turned an own
   voiceover on and the requirement left the method, the voice or the language open, the same AskUserQuestion call also carries the open
   ones of step 2b ("Voiceover", "Voice", "Language", "Voice style" as `voiceover.md` §2 has them for Free, the voice list printed
   above it, at most four questions; a voiceover asked for in the "Change it" answer the same way). Nothing else is asked in this phase, and the per-video loop asks nothing (item 15).
5. **Store it:** `T state --run RUN set directions=<one line per video, JSON list> videos_kind=<{"NN": "recreate|create"} JSON>
   free_plan_confirmed=true` (and `requested_videos` when the requirement set the count); with an own voiceover also the `voiceover` keys of
   `voiceover.md` §1, as `awl-start` step 6 writes them, plus `voiceover.videos='["01","03"]'` when only some videos have one (a requirement
   that asks for none writes no `voiceover` key), and `memes=include|none` (step 2c). The free plan file is the direction of every
   video: X1 reads its video's lines as the plan's brief (`awl-plan-video`), X2 translates them into the locked model's own prompting
   structure, X9 checks the explicit wants and forbids as checkpoints.

## Rules this phase owns (contract items 15, 17, 31)

31. **Own voiceover in Free: the user's decision, never the pipeline's suggestion.** Only the requirement (or the "Change it" answer)
    turns it on (step 2b); the pipeline never offers, recommends or asks it on its own, runs it as in Create, and asks what is left open
    inside the one confirmation.

15. **One confirmation, then no questions.** Free adds exactly one question to Analyze Mode, the confirmation of the plan (step 4); the
    long-video permission (A7b) and the QC-fix question (item 27, when the user chose `ask`) are the only others. Blockers are reported,
    not asked.
17. **Free.** The user's own requirement, with or without references to analyse first. The requirement governs the plan (what the videos
    achieve, how many, what happens, the product and its use, references edited or re-made or only studied, length, text, sound); the
    pipeline keeps the hard rules, the locked model's own prompting, the plan discipline, the QC stack, Loupe's samples and misses, the
    CapCut assembly and the deliverables. Every video carries its own kind (`state.json → videos_kind`): wherever a per-video skill says
    "Recreate:" or "Create:", the video follows its kind's branch.

## Never (this phase)

- Never add, drop or reshape what the user asked for without showing it in the confirmation; never invent a requirement the user did not
  state (a gap is a visible [I] line, not a silent default).
- Never ask more than the one confirmation; a change the user wants comes as the answer to it.
- Never break a hard rule to satisfy the requirement; say where they cross and follow the rule.
- Never paste the requirement's sentences into a prompt as they are: X2 writes the request in the locked model's own structure
  (`awl-write-request`) and carries the requirement's intent.
- Never read Loupe's data folder or its database; the samples reach this phase only through `T qc-brief` here and the keeper later.
- Never offer, suggest or ask an own voiceover the requirement did not ask for (item 31), never pick its voice or language for the user
  when the requirement leaves them open (they are asked in the confirmation), and never re-sync a `recreate`-kind video's lips to a new voice.

## Hand-off

`T state --run RUN set stage=planned next_skill=awl-asset-plan`, then invoke Skill `awl-asset-plan`.

After a compaction, or on `resume`, re-invoke the skill named in `RUN/state.json → next_skill`: its text may have been summarised away.
