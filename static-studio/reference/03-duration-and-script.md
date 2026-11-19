# 03 — Runtime promise, architecture and narration script

## Why previous Standard attempts failed

The old command recognized a reference-length average, but a later script/voice-edit path could lose that target. An 11-minute median can become a 2–4-minute narration if an agent writes only the summary, the voice recording runs short, the account runs out of credits or the editor simply stops with the available audio. An analytical estimate is **not** a production contract until every downstream stage checks it independently.

The new system stores a **video-level immutable `length-lock.json`** before scriptwriting. Standard is derived from IDs selected by the user-visible niche + story form + long-form runtime family. Mean, median, min, max, and spread are shown. Short-form or other niches can contribute transferable ideas, *never runtime defaults*. Long-form baseline here is at least 8 minutes (configurable at `init --min-longform`); you can select a higher floor for your channel. For long-form references in different duration clusters, split them. A 9-minute detailed how-to should not inherit the runtime of a 43-minute military epic.

Example:

```bash
python "$HOME/.claude/static-studio/scripts/static_core.py" cohorts --run "RUN"
python "$HOME/.claude/static-studio/scripts/static_core.py" length --run "RUN" --video 1 \
  --mode standard --niche "military history" --story-form "historical narrative" \
  --refs V004,V005,V006 --language en --pace-wpm 143
```

The locked Standard is the comparable cohort **median** rounded to five seconds. Own length uses `--mode own --minutes 18`. Neither can be changed automatically by audio/edit outputs. If the subject genuinely cannot fill the requested runtime with meaning, research a richer adjacent angle or ask the user **before paid generation** whether to explicitly revise length; document revision, do not silently overwrite the original lock. The CLI deliberately rejects overwriting a lock; new video ID/new plan or an explicit, auditable manual revision is required.

## Length arithmetic in service of quality, not padding

An English conversational narration can often be estimated with an explicitly chosen words-per-minute pace, but **measure the selected reference voices and the narrator's sample**. Other languages need their own pacing method; a whitespace word count is not a reliable timing model for every script. Include planned meaningful silence and reaction space as seconds, not a blanket slowdown of the entire voice. A simple budget is:

`expected_s = (number_of_narrated_words × 60 / expected_WPM) + planned_pause_s`

If an intended 12:00 narration runs at about 145 WPM and has 16 seconds of meaningful pause, it needs roughly `(720 - 16) × 145 / 60 ≈ 1701 words`. A 430-word script will not magically become 12 minutes by giving every image a slow zoom. For per-language estimates with characters or syllables, manually calibrate the voice sample and record an alternate estimate; do not mislabel English WPM as native pacing. Generated audio is ultimately authoritative, with hard checks after creation.

Use **content-rich length**: chapters earn runtime through explanation, examples, cause-and-effect, character decisions, counterarguments, concrete research and room to think. If an agent is short by 900 words, don't append 900 words of reiteration; identify missing substance and revise the chapter questions.

## Macro arc and micro arcs

Before writing the full narration, choose a flexible structure of **movements**, not a preordained 3-act or “hook every 15 seconds” rule. For each movement decide:

- what the viewer currently understands, wants to know and may be feeling;
- what **new information, action, evidence, or meaningful contrast** it delivers;
- how a specific visual can convey something the narration leaves open;
- how it changes stakes/interpretation and where the viewer can think for themself;
- what early promise it fulfills or new question it genuinely raises.

Let some moments breathe. In a long video, too much forced tension becomes tiring; a funny human detail or quietly revealing image can reset the experience. Each chapter should have a mini-arc, but it should also feed the main narrative. Plant and pay off specific details with causal continuity, not an arbitrary twist. For history, guard chronology, geography, actors and evolving knowledge. For an instructional topic, guard step dependency; a later step cannot assume an unshown setup or material.

## Exact file structures, in `40-plans/video-NN/`

`blueprint.json` has two tiers. **Universally required:** `audience_promise`, `narrative_approach` (a brief description of the specific creative strategy—e.g. `"decision-reconstruction narrative"`, `"step-by-step tutorial with failure modes"`, `"reflective essay comparing two outcomes"`), `why_this_length`, `original_angle`, `ending_payoff`, `visual_grammar`, `factuality` (`factual`, `hypothetical`, `fiction`), and a nonempty `research_sources` array for factual pieces. **Conditional (include when the format calls for it):** `central_question` for curiosity-driven or investigative structures; `human_lens` for biographical, decision-based, or witness-led narratives. Add optional `title_options`, `chapter_outline`, `character_map`, `scene_world_rules`, `viewer_thought_space`, `sources_for_facts`, `pacing_notes`, `story_risks`.

`script.json` contains `language` matching the lock, calibrated `pace_wpm`, and `lines`: one object per numbered narration line, with `id` (`L001`...), `text` and optional `pause_after_s`. For long-form, line = spoken sentence or short group of connected sentences, not individual words. Write for the ear: vary syntax, believable phrasing, breathing and emotional pacing. No voiceover of arbitrary on-screen design direction. Reading time is estimated from the final exact text, never an outline.

`beat-map.json` contains `target_length_s` equal to lock and `beats` with `id`, `start_s`, `end_s`, `line_start`, `line_end`, `narrative_job`, `visual_intent`. Add `viewer_question`, `new_value`, `emotional_shift`, `evidence_ids`, `planned_silence_s`, `shot_family`, `callback_to`, `risk` where valuable. Time spans cover **0 → target** without gaps or overlaps; line ranges cover **every script line exactly once**. Don't auto-fill empty minutes with rest footage. When actual narration is available, retime stills while preserving the lock and story's intent.

`editorial-review.md` is a frank written self-audit (not a numeric-only scoreboard): 5 best passages, 5 likely viewer exit/boring/confusing risks, claims requiring checking, missing texture, beat-to-beat repetition, visual argument opportunities, and revisions made. Prefer one fresh cold read from another agent with no access to prior justifications when resources permit. A reviewer must critique the *actual script*, not the prose of its plan.

Command gates:

```bash
python "$HOME/.claude/static-studio/scripts/static_core.py" plan-check --run "RUN" --video 1
```

This validates lock, chapter/line map, basic blueprint completeness, script language and predicted duration against an 8% early forecast tolerance. **A passed machine check is not an approval to make a boring 1700-word text**; it only means the length promise and coverage are structurally plausible. The producer then confirms true informational substance and natural voice flow. No paid narration or stills before both gates pass.

## A note on title and thumbnail

Develop several accurate **package concepts** around the promise while researching. The title/thumbnail should invite curiosity without falsely promising an event not actually explained. The first 30–60s must provide early evidence of value. Prepare `70-edit/video-NN/publishing.md` with proposed titles, final description, chapters with exported timestamps, sources/credits/licensing and thumbnail prompt/assets. Thumbnail composition may be more striking than the body style but should not misrepresent the actual subject or falsely depict a photo of a historical event. Evaluate packaging with the *finished* video, not in isolation.
