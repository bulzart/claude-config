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

Do **not** pass `--pace-wpm` manually. The `length` command computes it automatically from the word counts and durations of the selected reference transcripts in `10-media/`. The computed value and a per-reference breakdown are stored in `length-lock.json` and printed in the output, with the references' `pace_profile` (below). The lock also reports the script's word budget (`target_words`). Only override with `--pace-wpm` if you are explicitly calibrating to a specific narrator sample and have a measured reason to diverge from the references.

The locked Standard is the comparable cohort **median** rounded to five seconds. Own length uses `--mode own --minutes 18`. Neither can be changed automatically by audio/edit outputs. If the subject genuinely cannot fill the requested runtime with meaning, research a richer adjacent angle or ask the user **before paid generation** whether to explicitly revise length; document revision, do not silently overwrite the original lock. The CLI deliberately rejects overwriting a lock; new video ID/new plan or an explicit, auditable manual revision is required.

## Length arithmetic in service of quality, not padding

An English narration pace varies significantly by niche. The `length` command measures it from the selected reference transcripts and stores the result as `pace_wpm` in `length-lock.json` — use that number, not a generic estimate. Never assume 143–145 WPM as a planning default: real YouTube narrators have measured anywhere from about 170 to 210 WPM, and only this run's comparable references say where this video sits. Using a low estimate produces a script hundreds of words short of target.

`narration_s = spoken_words × 60 / pace_wpm + line_gap_s × lines + tag_time_s`  ·  `edit_s = narration_s + edit_holds_s`

Pace is measured three ways, always with the same functions for the references and for our voice (`pace_profile`, `pace-profile`):

- **active WPM** (`pace_wpm`): words over the time Whisper marks as speech, pauses between its speech segments left out. How fast a narrator talks *while talking*. This is the `pace_wpm` in the formula above, where the line gaps, tags and holds are added on top.
- **overall WPM**: words over the span from the first word to the last, every pause included. How many words a minute of the narration really holds.
- **runtime WPM**: words over the whole video, intro and outro included.

The word budget comes from the overall rate: `target_words = target_s × overall_wpm / 60`, the words a comparable narrator fits into this runtime with their own pauses. Never multiply the runtime by the active rate: that counts no pauses at all and overstates the budget (by about 11% on one run, which is why its first script ran long). `target_words_speech_only` is kept beside it as that upper bound. Here `line_gap_s` is the voice's own silence after each line: about 0.4 s before this voice is measured, then its measured value. `tag_time_s` is what the inline tags add, and `edit_holds_s` covers the pauses realised as holds in the edit. Spoken words exclude `[tags]`. A 430-word script will not magically become 12 minutes by giving every image a slow zoom, or by holding silence (below). For per-language estimates with characters or syllables, manually calibrate the voice sample and record an alternate estimate; do not mislabel English WPM as native pacing. Generated audio is ultimately authoritative, with hard checks after creation.

Speaking speed is not engagement. A faster narrator is not more entertaining and a slower one is not duller: the pace is the voice's (measured on its first part, never forced, since Eleven v4 has no speed control), and the script is sized to it.

**This `pace_wpm` is a planning figure, not the final word-count authority.** It is measured from the *reference narrators*, before any TTS voice has been chosen for this video. A synthetic voice does not necessarily speak at the same rate as the humans in the references — on one run the references measured 200 WPM and the chosen ElevenLabs voice 186–187 WPM on real parts, a gap large enough to miss the locked duration by itself. Once a voice is picked and its first real part measured (`05-voice-and-edit.md`: `voice-pick`, `tts --max-parts 1`, `narration-measure`), its measured pace and line gap (the video's `60-voice/video-NN/voice-lock.json` → `measured`) **supersede** this reference figure. `plan-check` then reports `real_forecast_s` and requires it inside the export window. It also lists the pace numbers (`pace_sources`: references while speaking and overall, script, voice while speaking and overall) and warns when the script's `pace_wpm` disagrees with the voice's. Writing the full script before a voice exists is fine; finalising it without re-checking against the voice that will speak it is how a correctly planned script ends up the wrong length. A voice preview's or a short probe's pace is never this number: short samples read fast and scatter.

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

`script.json` is written **after** `direction-lock` (10): the locked treatment decides how the narration sounds, so the words are written in its voice. It contains `language` matching the lock, calibrated `pace_wpm`, and `lines`: one object per numbered narration line, with `id` (`L001`...), `text`, and optional `pause_after_s`, `pause_via`, `pause_purpose` and `note`. For long-form, line = spoken sentence or short group of connected sentences, not individual words. Write for the ear: vary syntax, believable phrasing, breathing and emotional pacing. No voiceover of arbitrary on-screen design direction. Reading time is estimated from the final exact text, never an outline. Once audio exists, rewrite lines rather than adding or removing them: recorded parts keep their line boundaries, so only the part that holds an edited line is re-recorded.

Each thing lives in its own place. `text` is the canonical narration, exactly the words the viewer hears (captions come from it), plus any inline delivery tag the story calls for (`"[pause] At ten o'clock..."`); it is sent to ElevenLabs as written. Pronunciation goes in `pronunciation.json` (05), applied only to what is sent. A note for the team goes in the line's `note`, never sent. plan-check refuses anything else in `text` that would reach the voice as markup: SSML (`<break>`: v4 doesn't support it), `{braces}`, `*asterisks*`, a stage direction in parentheses, a note in brackets, IPA.

`beat-map.json` contains `target_length_s` equal to lock and `beats` with `id`, `start_s`, `end_s`, `line_start`, `line_end`, `narrative_job` and the beat's direction from the locked treatment (10 §4): `experience` (what the viewer should feel or understand by its end), `narration_direction` (register, energy and what the words do here), `visual_intent` (what the pictures show that the words don't; composition, motion, atmosphere), `sound_direction` and `pace`. The treatment evolves beat by beat; it is not one setting for the whole film. Add `viewer_question`, `new_value`, `emotional_shift`, `evidence_ids`, `shot_family`, `callback_to`, `risk` where valuable, and `key_moment` (a few words: "the reveal", "the climax") on the beats where a change of timing would change the film (held silences changed there after the script read are read again) (pauses live on the script's lines, below, not on beats). Time spans cover **0 → target** without gaps or overlaps; line ranges cover **every script line exactly once**. Don't auto-fill empty minutes with rest footage. When actual narration is available, retime stills while preserving the lock and story's intent.

**Pauses and delivery are decided here, by whoever judges the story's structure.** That means the turning point, the line a quote needs to breathe after, the closing beat. The audio stage never chooses its own moments. A line's `pause_after_s` is the silence the story wants after it, and it exists only if it is realised:

- **Up to 1 s**: nothing to do. The voice's own gap after a line (about 0.4 s) already gives it.
- **Longer**: say how with `pause_via`, and what it is for with `pause_purpose` (what the viewer takes in, feels or looks at while it lasts). `"tag"` means a pause tag at this line's end or the next line's start: the voice performs it and its cost is counted inside the narration. `"edit"` means a hold: `retime-shots` inserts it and the picture holds; it is exact, free, adjustable after recording, and added on top of the narration.

`plan-check` refuses a long pause that names neither, a pause without its purpose, and a `"tag"` pause with no pause tag in place. Choose with the evidence: `pace-profile` shows how often and how long this run's comparable narrators pause. The story may still want something they never do: a longer silence at the end, a turn that must land, a picture that needs time. That is a creative decision; say why.

**Silence never stands in for story.** There is no fixed limit on held silence: some films want long reflective holds. But a video earns its runtime with what it says and shows, and an underwritten script does not become a full one by adding holds. So the holds are part of what the cold reader reads: the script packet shows every one ("the picture holds 3.2 s in silence") with their total and share of the runtime next to the comparable narrators' longest pause, and the reader judges whether each earns its moment. Holds changed after the last read beyond a small tweak need a new read. The tweak is counted from that read, all changes together (two lines and about five seconds in all, every nudge added, however small), so a run of small edits can't pass one at a time. A hold changed in the opening (the first beat: the hook), the ending (the last beat) or a beat the map marks `key_moment` (a reveal, the climax, an emotional turn) needs a new read whatever its size: a six-second closing hold added after the read is read again. An older script whose holds were written before every hold had to say what it is for: when it resumes, look at each one and write the purpose it really serves; a hold that only fills runtime is removed and the plan fixed (the story, not an invented reason). `plan-check` shows how much of the runtime the words alone fill (`holds.content_forecast_s`) and how much the holds carry (`runtime_carried_by_holds_s`, warned). When the planned content cannot justify the runtime, the answer is the story: research a richer angle or strengthen the beats, never pad.

**Delivery tags** (05's catalogue: `STUDIO/data/elevenlabs-audio-tags.json`) are chosen in the same pass, from the creative strategy's sense of how the narration should sound, and only where the writing alone can't carry a change of register. They are written inline in `text`, and each kept tag gets one line under "Delivery and tags" in the review (plan-check refuses a tag without one). Every tag costs measured time, which `plan-check` adds to the forecast. Budget pauses and tags out of the word count before the calibration part, not after a full recording runs long.

`editorial-review.md` is the writer's frank self-audit (not a numeric-only scoreboard): 5 best passages, 5 likely viewer exit/boring/confusing risks, devices repeated until they turn into a tic (`writing_signals`), claims requiring checking, missing texture, beat-to-beat repetition, visual argument opportunities, and what was revised. Do it before asking for the cold read, so the reader's attention goes to what you could not see yourself. The creative strategy lives in `direction.json` (02, 10), not here. Two sections are read by `plan-check`:
- **"Delivery and tags"**: one line per kept tag and per realised pause (line, tag or hold, why this moment, how it compares with the references).
- **"Content flags"**: one line per line `plan-check` lists under `content_flags`, saying whether it was rewritten or why it stays. These are words that may break 02's rules on holidays and religion, gore and distress, and swearing. A flag is a question, not a verdict; an unanswered flag blocks paid generation.

**The cold read (06, 10 §7).** Before the first paid narration: `review-packet --kind script` writes the title and the bare script (no plan, no rationale) for ONE fresh agent, whose whole prompt is to read that file and follow it; `review-record` seals its findings; you answer each in the answers file (`revised` with its lines, `kept` for a minor one with why, `disputed` with why). A major finding gets a fresh round-2 read of the revised script by a new agent; after round 2 you decide and the reasons stay on record. Edits after the last read that no finding asked for pass only when small (a length trim); anything more needs a new read, because the approval no longer describes the script. A reviewer critiques the *actual script*, not the prose of its plan.

Command gates:

```bash
python "$HOME/.claude/static-studio/scripts/static_core.py" plan-check --run "RUN" --video 1
```

This validates:
- the lock, the chapter/line map, basic blueprint completeness and the script language;
- the audio tags (refuses `not_for_narration` tags, broken brackets, opposite qualities on the same words, and a kept tag with no line under "Delivery and tags"; lists every tag with its status);
- what reaches the voice: no SSML, braces, asterisks, stage directions in parentheses, notes in brackets or IPA in `text`; a valid `pronunciation.json` (05);
- that every long pause names how it is realised and what it is for, and that the cold reader saw the holds as they are;
- that every content flag is answered;
- that `direction.json` is complete (measured evidence, five approaches on at least three axes, the strategy, two or three treatments with their sample moments, the decision) and locked, unchanged since its lock, with the lock made before the script (or recorded as late);
- that every beat carries its direction (`experience`, `narration_direction`, `visual_intent`, `sound_direction`, `pace`);
- that the script had its cold read, every finding is answered, a major finding got its round-2 read, and the read still describes the current script;
- and it lists `writing_signals` (never blocking): repeated phrases and sentence shapes, fragment runs, long sentences, number-dense lines, echoes;
- the predicted duration: within 8% before the voice is measured, then `real_forecast_s` inside the export window. **A passed machine check is not an approval to make a boring 1700-word text**; it only means the length promise and coverage are structurally plausible. The producer then confirms true informational substance and natural voice flow. No paid narration or stills before both gates pass.

## A note on title and thumbnail

Develop several accurate **package concepts** around the promise while researching. The title/thumbnail should invite curiosity without falsely promising an event not actually explained. The first 30–60s must provide early evidence of value. Prepare `70-edit/video-NN/publishing.md` with proposed titles, final description, chapters with exported timestamps, sources/credits/licensing and thumbnail prompt/assets. Thumbnail composition may be more striking than the body style but should not misrepresent the actual subject or falsely depict a photo of a historical event. Evaluate packaging with the *finished* video, not in isolation.
