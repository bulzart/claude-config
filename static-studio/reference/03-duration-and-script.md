# 03 — Runtime promise, architecture and narration script

## Why previous Standard attempts failed

The old command recognized a reference-length average, but a later script/voice-edit path could lose that target. An 11-minute median can become a 2–4-minute narration if an agent writes only the summary, the voice recording runs short, the account runs out of credits or the editor simply stops with the available audio. An analytical estimate is **not** a production contract until every downstream stage checks it independently.

The new system stores a **video-level immutable `length-lock.json`** before scriptwriting. Standard is derived from IDs selected by the user-visible niche + story form + long-form runtime family. Mean, median, min, max, and spread are shown. Short-form or other niches can contribute transferable ideas, *never runtime defaults*. Long-form baseline here is at least 8 minutes (configurable at `init --min-longform`); you can select a higher floor for your channel. For long-form references in different duration clusters, split them. A 9-minute detailed how-to should not inherit the runtime of a 43-minute military epic.

Example:

```bash
python "$HOME/.claude/static-studio/scripts/static_core.py" cohorts --run "RUN"
python "$HOME/.claude/static-studio/scripts/static_core.py" length --run "RUN" --video 1 \
  --mode standard --niche "military history" --story-form "historical narrative" \
  --refs V004,V005,V006 --language en
```

Do **not** pass `--pace-wpm` manually. The `length` command computes it automatically from the word counts and durations of the selected reference transcripts in `10-media/`. The computed value and a per-reference breakdown are stored in `length-lock.json` and printed in the output. The lock also reports the script's target word count (`target_words`). Only override with `--pace-wpm` if you are explicitly calibrating to a specific narrator sample and have a measured reason to diverge from the references.

The locked Standard is the comparable cohort **median** rounded to five seconds. Own length uses `--mode own --minutes 18`. Neither can be changed automatically by audio/edit outputs. If the subject genuinely cannot fill the requested runtime with meaning, research a richer adjacent angle or ask the user **before paid generation** whether to explicitly revise length; document revision, do not silently overwrite the original lock. The CLI deliberately rejects overwriting a lock; new video ID/new plan or an explicit, auditable manual revision is required.

## Length arithmetic in service of quality, not padding

An English narration pace varies significantly by niche. The `length` command measures it from the selected reference transcripts and stores the result as `pace_wpm` in `length-lock.json` — use that number, not a generic estimate. Never assume 143–145 WPM as a planning default: real YouTube narrators have measured anywhere from about 170 to 210 WPM, and only this run's comparable references say where this video sits. Using a low estimate produces a script hundreds of words short of target.

`narration_s = spoken_words × 60 / pace_wpm + line_gap_s × lines + tag_time_s`  ·  `edit_s = narration_s + edit_holds_s`

Here `line_gap_s` is the voice's own silence after each line: about 0.4 s before this voice is measured, then its measured value. `tag_time_s` is what the inline tags add, and `edit_holds_s` covers the pauses realised as holds in the edit. Spoken words exclude `[tags]`. The `length` command output includes `target_words = target_s × pace_wpm / 60`. That is speech alone, so the real word budget is a little lower once the gaps between lines are counted (`plan-check` does the arithmetic). A 430-word script will not magically become 12 minutes by giving every image a slow zoom. For per-language estimates with characters or syllables, manually calibrate the voice sample and record an alternate estimate; do not mislabel English WPM as native pacing. Generated audio is ultimately authoritative, with hard checks after creation.

**This `pace_wpm` is a planning figure, not the final word-count authority.** It is measured from the *reference narrators*, before any TTS voice has been chosen for this video. A synthetic voice does not necessarily speak at the same rate as the humans in the references — on one run the references measured 200 WPM and the chosen ElevenLabs voice 186–187 WPM on real parts, a gap large enough to miss the locked duration by itself. Once a voice is picked and its first real part measured (`05-voice-and-edit.md`: `voice-pick`, `tts --max-parts 1`, `narration-measure`), its measured pace and line gap (`60-voice/voice-lock.json` → `measured`) **supersede** this reference figure. `plan-check` then reports `real_forecast_s` and requires it inside the export window. It also lists all three pace numbers (`pace_sources`: references, script, voice) and warns when the script's `pace_wpm` disagrees with the voice's. Writing the full script before a voice exists is fine; finalising it without re-checking against the voice that will speak it is how a correctly planned script ends up the wrong length. A voice preview's or a short probe's pace is never this number: short samples read fast and scatter.

Use **content-rich length**: chapters earn runtime through explanation, examples, cause-and-effect, character decisions, counterarguments, concrete research and room to think. If an agent is short by 900 words, don't append 900 words of reiteration; identify missing substance and revise the chapter questions. Cutting for length is a boredom pass, not a trim: take out first what a listener would drift through (the same point made again, a fact with no consequence for anyone, a list read aloud), and keep the vivid detail that carries a beat, even when it costs words.

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

`script.json` contains `language` matching the lock, calibrated `pace_wpm`, and `lines`: one object per numbered narration line, with `id` (`L001`...), `text` and optional `pause_after_s` and `pause_via`. For long-form, line = spoken sentence or short group of connected sentences, not individual words. Write for the ear: vary syntax, believable phrasing, breathing and emotional pacing. No voiceover of arbitrary on-screen design direction. Reading time is estimated from the final exact text, never an outline. `text` is sent to ElevenLabs exactly as written, so any inline audio tag the story calls for is written there (`"[pause] At ten o'clock..."`). Once audio exists, rewrite lines rather than adding or removing them: recorded parts keep their line boundaries, so only the part that holds an edited line is re-recorded.

`beat-map.json` contains `target_length_s` equal to lock and `beats` with `id`, `start_s`, `end_s`, `line_start`, `line_end`, `narrative_job`, `visual_intent`. Add `viewer_question`, `new_value`, `emotional_shift`, `evidence_ids`, `shot_family`, `callback_to`, `risk` where valuable (pauses live on the script's lines, below, not on beats). Time spans cover **0 → target** without gaps or overlaps; line ranges cover **every script line exactly once**. Don't auto-fill empty minutes with rest footage. When actual narration is available, retime stills while preserving the lock and story's intent.

**Pauses and delivery are decided here, by whoever judges the story's structure.** That means the turning point, the line a quote needs to breathe after, the closing beat. The audio stage never chooses its own moments. A line's `pause_after_s` is the silence the story wants after it, and it exists only if it is realised:

- **Up to 1 s**: nothing to do. The voice's own gap after a line (about 0.4 s) already gives it.
- **Longer**: say how with `pause_via`. `"tag"` means a pause tag at this line's end or the next line's start: the voice performs it and its cost is counted inside the narration. `"edit"` means a hold: `retime-shots` inserts it and the picture holds; it is exact, free, adjustable after recording, and added on top of the narration.

`plan-check` refuses a long pause that names neither, and a `"tag"` pause with no pause tag in place. Choose with the evidence: `pace-profile` shows how often and how long this run's comparable narrators pause. The story may still want something they never do: a longer silence at the end, a turn that must land. That is a creative decision; say why in the review.

**Delivery tags** (05's catalogue: `STUDIO/data/elevenlabs-audio-tags.json`) are chosen in the same pass, from the creative strategy's sense of how the narration should sound. They are written inline in `text`, and each kept tag gets one line in the review. Every tag costs measured time, which `plan-check` adds to the forecast. Budget pauses and tags out of the word count before the calibration part, not after a full recording runs long.

`editorial-review.md` is a frank written self-audit (not a numeric-only scoreboard). It has four sections `plan-check` reads:
- **"Creative strategy"**: 02's episode strategy, written before the full narration: why this idea at this length, the viewer's experience, how it moves without padding, how the narration sounds and breathes, what makes it different from the references, and the approaches explored (02) with why this one won.
- **"Self-audit"**: 5 best passages, 5 likely viewer exit/boring/confusing risks, devices repeated until they turn into a tic, claims requiring checking, missing texture, beat-to-beat repetition, visual argument opportunities, the cold read's findings and what was revised. `plan-check` only checks that these two sections exist and are written; whether they are honest is the writer's and the cold reader's job.
- **"Delivery and tags"**: one line per kept tag and per realised pause (line, tag or hold, why this moment, how it compares with the references).
- **"Content flags"**: one line per line `plan-check` lists under `content_flags`, saying whether it was rewritten or why it stays. These are words that may break 02's rules on holidays and religion, gore and distress, and swearing. A flag is a question, not a verdict; an unanswered flag blocks paid generation. Before the first paid narration, get one fresh cold read from an agent that sees only the title and the bare script text (06), and record what it found in "Self-audit". A reviewer must critique the *actual script*, not the prose of its plan.

Command gates:

```bash
python "$HOME/.claude/static-studio/scripts/static_core.py" plan-check --run "RUN" --video 1
```

This validates:
- the lock, the chapter/line map, basic blueprint completeness and the script language;
- the audio tags (refuses `not_for_narration` tags and broken brackets; lists every tag with its status);
- that every long pause names how it is realised;
- that every content flag is answered;
- that the "Creative strategy" and "Self-audit" sections exist and are written;
- the predicted duration: within 8% before the voice is measured, then `real_forecast_s` inside the export window. **A passed machine check is not an approval to make a boring 1700-word text**; it only means the length promise and coverage are structurally plausible. The producer then confirms true informational substance and natural voice flow. No paid narration or stills before both gates pass.

## A note on title and thumbnail

Develop several accurate **package concepts** around the promise while researching. The title/thumbnail should invite curiosity without falsely promising an event not actually explained. The first 30–60s must provide early evidence of value. Prepare `70-edit/video-NN/publishing.md` with proposed titles, final description, chapters with exported timestamps, sources/credits/licensing and thumbnail prompt/assets. Thumbnail composition may be more striking than the body style but should not misrepresent the actual subject or falsely depict a photo of a historical event. Evaluate packaging with the *finished* video, not in isolation.
