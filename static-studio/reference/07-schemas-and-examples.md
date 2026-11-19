# 07 — Durable hand-offs and CLI examples

This package intentionally relies on **on-disk contracts** rather than agents remembering a chat. The program enforces structural and duration invariants; the creative agent owns nuance, story quality, proof checking and real CapCut work. File paths are UTF-8; use quoted absolute paths (especially Windows paths containing spaces).

## Steps that must run

```bash
# The user has named a references directory.
python "$HOME/.claude/static-studio/scripts/static_core.py" doctor
python "$HOME/.claude/static-studio/scripts/static_core.py" init --references "C:/videos/references" --slug history
# Copy the returned RUN path; the following examples use literal RUN as a placeholder.
python "$HOME/.claude/static-studio/scripts/static_core.py" scan --run "RUN"
python "$HOME/.claude/static-studio/scripts/static_core.py" prepare --run "RUN" --dry-run
python "$HOME/.claude/static-studio/scripts/static_core.py" prepare --run "RUN" --whisper-model medium
# Agent writes evidence-grounded 20-analysis/cards/V###.json and niche synthesis.
python "$HOME/.claude/static-studio/scripts/static_core.py" cohorts --run "RUN"
# User selected a niche/length; examples only after cards exist.
# Option A: group by niche + story-form (exact string match)
# Never pass --pace-wpm here: length computes it automatically from the references' own
# Whisper transcripts (pure narration time, timestamps stripped). A manual number is a guess.
python "$HOME/.claude/static-studio/scripts/static_core.py" length --run "RUN" --video 1 \
  --mode standard --niche "military history" --story-form "historical narrative" \
  --refs V001,V002,V003 --language en
# Option B: group by cohort_id when labels vary across cards
python "$HOME/.claude/static-studio/scripts/static_core.py" length --run "RUN" --video 1 \
  --mode standard --cohort-id "long-military-history" \
  --refs V001,V002,V003 --language en
# Agent writes blueprint/script/beat-map/editorial-review, then validates.
python "$HOME/.claude/static-studio/scripts/static_core.py" plan-check --run "RUN" --video 1
# Voice: five candidates, pace stated IN the design description (a voice reads about as fast
# as the audio it was made from -- do not plan to fix pace later with a --delivery tag).
python "$HOME/.claude/static-studio/scripts/static_core.py" voice-candidates --run "RUN" --video 1 \
  --count 5 --design 2 --design-description "A grave, warm documentary narrator in his 50s, speaks at a brisk, measured pace of about 190 words a minute, clearly and without rushing" \
  --design-text "A sample of the actual script, 100-1000 characters, read exactly as it will be sent."
python "$HOME/.claude/static-studio/scripts/static_core.py" voice-pick --run "RUN" --video 1 \
  --voice-id "ID_FROM_CANDIDATES_JSON" --name "Narrator name"
# Dry run NEVER charges money. The ID below is a placeholder, not a valid voice.
python "$HOME/.claude/static-studio/scripts/static_core.py" tts --run "RUN" --video 1 \
  --voice-id "REPLACE_WITH_REAL_VOICE_ID" --model-id eleven_v4 \
  --settings '{"stability":0.65,"similarity_boost":0.8}'
# Only after the user has approved the selected voice, model and credit cost. --max-parts 1
# makes the FIRST chunk the real calibration check (paid once, kept if good -- never a
# separate short throwaway sample): transcribe/measure it before continuing to the rest.
# ... repeat with --max-parts 1 --execute, measure, then repeat again without --max-parts
python "$HOME/.claude/static-studio/scripts/static_core.py" audio-check --run "RUN" --video 1
# Agent makes/records CapCut project and writes project-derived timeline.json.
python "$HOME/.claude/static-studio/scripts/static_core.py" timeline-check --run "RUN" --video 1
# Only after an actual MP4 is accessible:
python "$HOME/.claude/static-studio/scripts/static_core.py" export-check \
  --run "RUN" --video 1 --file "C:/videos/final.mp4" --deep
python "$HOME/.claude/static-studio/scripts/static_core.py" status --run "RUN"
```

## Reference cards (agent generated)

Create `20-analysis/cards/V001.json` for every unique video in `00-inventory/references.json`. Required minimum for CLI grouping: `reference_id`, `niches` (list of category names), `story_form` (one primary form), and `viewer_experience` (list of timed meaningful moments). Optionally add `cohort_id` (a stable lowercase slug, e.g. `"long-military-history"`) when niche/story_form labels may vary across cards for comparable videos—any cards sharing a `cohort_id` form their own cohort group and can be used directly with `length --cohort-id`. The detailed suggested schema is in manual 01; include actual timestamps, source vs interpretation, script delivery, shot/form analysis and tradeoffs.

**Important:** `cohorts` only groups by reported niche/form and measured ffprobe duration. Agents, not a keyword regex, decide what a video is actually about. A video can be in two niches, but a 50-second Short and a 15-minute episode must not share one Standard duration lock. If group spread is large, explicitly choose a narrow set of comparable IDs for `length`.

## Blueprint and exact script (agent generated)

Minimal `40-plans/video-01/blueprint.json`:

```json
{
  "audience_promise": "An answer specific enough to be worth a 12-minute watch",
  "narrative_approach": "Decision-reconstruction narrative following a commander through incomplete information",
  "why_this_length": "The answer requires three meaningful discoveries and context",
  "original_angle": "Follow the overlooked supply decision, not just the battle",
  "ending_payoff": "Return to the opening dilemma with new evidence",
  "visual_grammar": "Earth-tone maps, aerial diagrams, restrained artifact illustration",
  "factuality": "factual",
  "research_sources": ["S1", "S2", "S3"],
  "central_question": "What did the participants know at the decisive moment?",
  "human_lens": "What a planner can and cannot know from one report",
  "chapter_outline": [{"id": "B01", "purpose": "orient"}, {"id": "B02", "purpose": "complicate"}]
}
```

`narrative_approach` is universally required. `central_question` and `human_lens` are conditional: include them when the format is investigative or decision-driven; omit them for tutorials, essays, or other formats where they would be forced.

`40-plans/video-01/script.json`:

```json
{
  "language": "en",
  "pace_wpm": 190,
  "lines": [
    {"id": "L001", "text": "Start with a meaningful, specific opening line.", "pause_after_s": 0.5},
    {"id": "L002", "text": "Continue naturally, with context and a real reason to care.", "pause_after_s": 0.2}
  ]
}
```

`pace_wpm` above (190) is an example number, not a universal default — write this run's own measured value: `length-lock.json`'s reference-measured figure before a voice is picked, then `voice-lock.json`'s `measured_wpm` (the voice's own real pace) once one is, since the two can genuinely differ (real pov-military-narrative references measured ~198-200 WPM; a real selected voice in that same niche measured ~186-187 WPM — not interchangeable).

`40-plans/video-01/beat-map.json`:

```json
{
  "target_length_s": 720,
  "beats": [
    {"id": "B01", "start_s": 0, "end_s": 92,
     "line_start": 1, "line_end": 18,
     "narrative_job": "Present a real dilemma and its stakes",
     "visual_intent": "Show relative position and scale via a map",
     "viewer_question": "Why did the obvious solution fail?"},
    {"id": "B02", "start_s": 92, "end_s": 220,
     "line_start": 19, "line_end": 55,
     "narrative_job": "Reveal the first hidden constraint",
     "visual_intent": "Reconstruct logistics and compare alternatives"}
  ]
}
```

**These snippets are schema examples, not executable complete 12-minute scripts**. A real plan must have sufficient original words, all lines covered by a gap-free map to exactly the locked target, independent sources for all consequential facts, an actual editorial review and complete audio. Copying these snippets alone should correctly fail `plan-check`.

## Audio manifest (automatically produced with paid TTS)

Under `50-audio/video-01/`, the TTS tool creates `manifest.json` (voice/model/language/chunks and SHA256 text hashes, line ranges, `finished_parts`, `status`). Completed parts reside in `part-001.mp3` etc. An all-parts-complete pass generates `narration.wav`. A model/voice/script change during a partial recording requires deliberate reconciliation; the tool will refuse silent reuse. `audio-check` disallows a partial or missing line/audio, and rejects a delivered duration far from lock. `tts --max-parts 1 --execute` stops after the first chunk instead (`mode: partial_by_design_max_parts`) so it can be measured before paying for the rest.

## Voice lock (`voice_id`/`settings`/`measured_wpm`/`locked_at`/`rule` written by `voice-pick`; `measured_overhead_*` hand-recorded by the agent; all of it read by `tts` and `plan-check`)

`60-voice/voice-lock.json`:

```json
{
  "voice_id": "REAL_ACCOUNT_VOICE_ID",
  "generated_voice_id": "REAL_ACCOUNT_VOICE_ID",
  "name": "Narrator name",
  "settings": {"stability": 0.65, "similarity_boost": 0.8},
  "measured_wpm": 187,
  "measured_overhead_s": 113.4,
  "measured_overhead_lines": 329,
  "measured_overhead_source": "How/when this was measured -- which real generation(s), at what line count.",
  "locked_at": "2026-11-19T13:22:38+00:00",
  "rule": "One voice per run across every video and language; --replace required to deliberately change it."
}
```

`measured_wpm` is this voice's own real measured pace (not the reference narrators') — it supersedes `length-lock.json`'s `pace_wpm` for sizing the script once it exists (`03-duration-and-script.md`). `measured_overhead_s`/`measured_overhead_lines` are the real ElevenLabs natural-pause overhead observed on an actual generation (for this many script lines) — `plan-check` uses them for `real_overhead_forecast_s`, a more accurate prediction than its plain `forecast_s` (which only counts the script's own *planned* pauses, never actually sent to ElevenLabs).

**No command writes `measured_overhead_s`/`measured_overhead_lines` yet** — after a `--max-parts 1` calibration chunk or a completed generation, the agent transcribes it, computes `overhead_s = real_duration_s - words*60/measured_wpm`, and adds the three fields into this file itself (merge, don't just overwrite — `voice-pick --replace` rewrites the whole file from scratch and does not preserve them, so re-add them after any `--replace`, and only reuse old overhead data if the voice itself didn't change; a different voice needs its own fresh measurement).

**Production agents must not manually toggle `status=complete`.** The manifest represents real provider responses. The tool saves chunks and updates the manifest after each successful response so a credit cutoff cannot masquerade as a short completed voiceover.

## Real CapCut timeline (agent measured from project)

`70-edit/video-01/timeline.json`:

```json
{
  "canvas": "1920x1080",
  "fps": 30,
  "project_file": "C:/path/to/the/real/capcut/project",
  "visual_segments": [
    {"start_s": 0, "end_s": 14.5,
     "asset_path": "C:/path/to/an/actual/still.png", "beat_id": "B01",
     "purpose": "Orient viewer to location before explaining constraints"},
    {"start_s": 14.5, "end_s": 28.2,
     "asset_path": "C:/path/to/a/diagram.png", "beat_id": "B01",
     "purpose": "Make distance and travel costs immediately visible"}
  ]
}
```

Again these are a small excerpt, not a passing whole-film timeline. Fill every segment until the actual project ends, with meaningful beat IDs and no gaps; base timestamps on CapCut project readback. Timeline gate success still requires a human watch/listen pass and an **independent MP4 export check**.

## Repeat or start a new channel

`/create-video more <RUN> [N]` continues the run, preserves its niche/voice/look and uses new video IDs. `/create-video clone <RUN>` creates a new run with **only reference inventory and analytical cards**, not shared source assets or an unearned approved script. Re-analyze newly added files; do not automatically duplicate a finished episode.
