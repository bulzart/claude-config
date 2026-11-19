---
description: Mine reference videos and make original, polished long-form YouTube stories using narrated stills.
argument-hint: "<references-folder> | resume <run> | more <run> [N] | clone <run>"
disable-model-invocation: true
---

# /create-video — STATIC ONLY · YOUTUBE LONG-FORM

Input: `$ARGUMENTS`. This is a **normal Claude Code command**, not a Claude workflow, automation, or multiple-mode selector. It has exactly one production pipeline: reference research → choose a niche → invent and research an original long-form story → fully narrated image-led video → CapCut project/export. Never ask which mode to run. Never load or invoke legacy phases, generic video-editing flows, browser inspection services, or video-to-video generation services. No external monitoring app is used.

**Paths.** `STUDIO = ~/.claude/static-studio/`; the executable is `python "$HOME/.claude/static-studio/scripts/static_core.py"` (on Windows, use the Python 3 installation already configured in Claude Code; `$HOME` is the Git Bash home directory). `RUN` is the absolute run folder returned by `init`, `clone`, or supplied on `resume`. The command is stored in `~/.claude/commands/create-video.md`. Keep all artifacts under `RUN`. Never modify the user's `references/` sources.

**Always read the specific stage manual before acting.** Read only what you need; do not dump every file into context. Manuals:

| Stage | Read |
|---|---|
| Intake and evidence mining | `STUDIO/reference/01-reference-forensics.md` |
| Niche → original premise and YouTube narrative | `STUDIO/reference/02-creative-editorial-engine.md` |
| Comparable length, plan and immutable runtime | `STUDIO/reference/03-duration-and-script.md` |
| Picture/art direction and still generation | `STUDIO/reference/04-visual-direction.md` |
| ElevenLabs, music, CapCut and exports | `STUDIO/reference/05-voice-and-edit.md`; to write the CapCut project: `STUDIO/reference/09-capcut-toolkit.md` |
| Whole-video skeptical review and release criteria | `STUDIO/reference/06-quality-controls.md` |
| File schemas and working examples | `STUDIO/reference/07-schemas-and-examples.md` |

## Entry / resume

1. If `$ARGUMENTS` starts with `resume`, read `RUN/state.json` and `RUN/todo.md`; call `static_core.py status --run "RUN"`. Verify real files rather than trusting conversation memory. Continue the earliest incomplete stage; **never re-ask a choice already present in the run**. This works across `/compact` or a new chat.
2. If it starts with `more`, use the existing `RUN` and its locked niche/look/narrator. Ask only for a count when absent, then use new video IDs, new original topics and new duration locks. First `scan` for newly added references and study only new ones. Never create a new run for more videos.
3. If it starts with `clone`, run `static_core.py clone --from-run "RUN"`; keep evidence/cards, start an independent new niche and new production. The old run remains untouched.
4. Otherwise, the **first requirement is a path to `references/`**. If `$ARGUMENTS` contains a path, use it; if not, ask exactly for that folder path. `static_core.py doctor`, then `static_core.py init --references "PATH" --slug "youtube"`, then `scan`. The returned run path is authoritative. `prepare --run "RUN" --dry-run`, then `prepare --run "RUN"` with local Whisper enabled. If files are corrupt/missing, report and skip those files explicitly; never silently treat missing speech as silence.

## Core execution contract

**A. Watch, listen, classify, understand.** Analyze each unique video as a cohesive whole: original audio/Whisper word-timestamps, 5 fps sampled visual coverage, high-fps windows for ambiguous transitions, transcript, story architecture, scene progression, emotional movement, narrator character, pacing, music, retention hypotheses, title/thumbnail promise. Create `20-analysis/cards/V###.json` and `20-analysis/V###-notes.md`. Cross-classify by **niche**, **story form**, **runtime family**, **language** and **visual medium**. Explicitly distinguish verified observation, plausible explanation and unknown metrics. Write niche-specific syntheses; never average unrelated formats. Run `cohorts --run "RUN"`. When a card is weak, inspect the actual reference again.

**B. Ask one intentional choice: niche.** Present the discovered niches and one short indication of what *makes each engaging*. The user picks a niche (or explicitly delegates that choice). From then on, **you invent the subject, premise, angle, chapters, and execution autonomously**. Do not ask users to choose one of your titles or scripts by default. Prompt only when their actual choice is necessary: custom vs comparable-reference Standard length, count (default one), language, narrator, generation engine and a material cost authorization. Persist those choices; no repeating.

**C. Lock long-form duration BEFORE script, speech, images or CapCut.** Standard means median of **at least two user-visible, same-niche, same-story-form, comparable, long-form reference IDs**; use `length --mode standard --refs ...` after showing IDs/durations. A Short cannot set the length for a history narration. For custom length use `--mode own --minutes ...`. Defaults: YouTube **16:9, 1920×1080, 30 fps**, with a user-adjustable long-form minimum; no vertical templates. The lock is immutable without an explicitly authorized length revision; don't silently shrink it to match generated audio or sparse visuals.

**D. Make a genuine new story, not a reference remix.** Read stages 02–03. Explore at least five *different editorial approaches*; select on substance, credible evidence, distinctive viewpoint, human relevance, an earned ending and compatibility with runtime. Study source documents for factual topics independent of reference videos, create claim/source ledger; separate fictional hypothesis from fact. Write `40-plans/video-NN/blueprint.json`, `script.json`, `beat-map.json` and `editorial-review.md`, plus human-readable outline and title/thumbnail options. Each beat must move the story forward and be mapped to narration lines and a planned visual purpose. Do not pad or speed-read. Run `plan-check --run "RUN" --video NN`; **do not buy TTS or pictures if it fails**. Fix the *story*, not just the numbers.

**E. Narration and production.** Read stages 04–05. Select a good expressive narrator for the niche and keep the voice consistent inside a run (the spoken language may be chosen per video). ElevenLabs generations are paid; run `tts ...` without `--execute` first for the character/chunk/credit forecast. Only use `--execute` after the account, voice, model and charges are accepted. **Partial, exhausted, missing or short narration is a BLOCKER.** `audio-check` must pass before stills and edit. Preserve partial chunks for resuming; never cut chapters to make a failed recording look done. Create an image style bible and shot plan linked to beats; generate stills with available OpenAI Images or the optional local image worker, or prepare prompts for user-supplied stills. Add charts, maps, time lines, restrained illustration animation and on-screen text **when they improve comprehension**; do not turn every shot into a wallpaper slide or a frenetic montage. Optional instrumental music and sound design support the scene rather than bury it.

**F. CapCut and actual export.** Use connected CapCut MCP/CLI as available to create a *real editable project*, no unsupported invented operations. Create `70-edit/video-NN/timeline.json` from the actual project (shot ranges, beats and narrative purpose), then `timeline-check --run "RUN" --video NN`; listen at joins and watch the whole opening, chapter transitions and ending. A CapCut draft is **not** an exported file. After an accessible MP4 is exported, run `export-check --run "RUN" --video NN --file "actual.mp4" --deep` and manually review. If export is not available, report that as unverified; never claim to have watched a file not seen.

**G. Critical pass before delivery.** Read stage 06. Evaluate title/thumbnail promise, originality, human interest, factual honesty, macro/micro pacing, viewer's mental participation, audio quality, shot-purpose/continuity, rhythm/breathing room, final satisfaction. Fix unearned hooks, repetitive middle, weak ending, historical anachronisms, bad compositions, robotic narration, frame/caption clutter and incomplete runtime. The goal is exceptional work, not a fictitious guaranteed “10/10” score. Use up to two research agents and up to three production agents when useful, with non-overlapping responsibilities; do not spawn a judge bureaucracy. Verify artifacts; communicate blockers plainly.

## Non-negotiables

- One purpose only: **new long-form YouTube videos built from narrated still images/graphics**. No other generation or editing modes, no unrelated prompts/assets, no reuse of source-video images or speech as final footage.
- Ref clips are **evidence about craft**, not license to reproduce another creator's words, distinctive footage, visual identity or unsupported factual claims. Preserve provenance; independent research for facts.
- Source and final frame timing matter. 5 fps is a broad coverage rate, **not literally every native frame**. For exact transitions, extract a full-frame window or use `prepare --full-fps --ids V###`; record the difference rather than falsely claiming every frame was viewed.
- The author is responsible for decisions. Machine checks measure objective properties, not taste or truth. No hard formula for hooks, number of chapters, humor frequency, zoom every few seconds or cliffhangers.
- Keep a progressing `RUN/todo.md`; use files as durable handoffs. Resume from what exists. Never run a Claude workflow. Never spend credits on a failed preflight. Final product is an actual CapCut project and, when exported, a verified video.
