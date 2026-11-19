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
# How the comparable narrators speak and pause (same yardstick later used on the voice):
python "$HOME/.claude/static-studio/scripts/static_core.py" pace-profile --run "RUN" --video 1
# Voice: five candidates described by the narrator this story needs (character, register, age,
# accent). A preview's pace does not predict the real pace; choose by ear.
python "$HOME/.claude/static-studio/scripts/static_core.py" voice-candidates --run "RUN" --video 1 \
  --count 5 --design 2 --design-description "A grave, warm documentary narrator in his 50s, American, close to the listener, restrained rather than theatrical" \
  --design-text "A sample of the actual script, 100-1000 characters, read exactly as it will be sent."
python "$HOME/.claude/static-studio/scripts/static_core.py" voice-pick --run "RUN" --video 1 \
  --voice-id "ID_FROM_CANDIDATES_JSON" --name "Narrator name" --settings '{"stability":0.65,"similarity_boost":0.8}'
# Dry run NEVER charges money. The ID below is a placeholder, not a valid voice.
python "$HOME/.claude/static-studio/scripts/static_core.py" tts --run "RUN" --video 1 \
  --voice-id "REPLACE_WITH_REAL_VOICE_ID" --model-id eleven_v4 \
  --settings '{"stability":0.65,"similarity_boost":0.8}'
# Only after the user has approved the voice, model and credit cost: the FIRST real part is the
# calibration (paid once, kept). The tool refuses more parts before this voice is measured.
#   tts ... --max-parts 1 --execute
python "$HOME/.claude/static-studio/scripts/static_core.py" narration-measure --run "RUN" --video 1
python "$HOME/.claude/static-studio/scripts/static_core.py" plan-check --run "RUN" --video 1   # real_forecast_s
#   tts ... --execute                      (the rest; finished parts are kept)
#   tts ... --rerecord-changed --execute   (after editing lines: only the parts that hold them)
python "$HOME/.claude/static-studio/scripts/static_core.py" audio-check --run "RUN" --video 1
python "$HOME/.claude/static-studio/scripts/static_core.py" narration-measure --run "RUN" --video 1   # line times
python "$HOME/.claude/static-studio/scripts/static_core.py" retime-shots --run "RUN" --video 1 --render-narration
# Agent makes/records CapCut project (narration-edit.wav, stills at the retimed shot times) and
# writes project-derived timeline.json.
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
    {"id": "L001", "text": "Start with a meaningful, specific opening line."},
    {"id": "L002", "text": "A turn the story wants to land.", "pause_after_s": 2, "pause_via": "tag"},
    {"id": "L003", "text": "[pause] The next line opens after it, as the review decided."},
    {"id": "L004", "text": "The closing line.", "pause_after_s": 4, "pause_via": "edit"}
  ]
}
```

`pace_wpm` above (190) is an example number, not a universal default. Write this run's own measured value: `length-lock.json`'s reference-measured figure before a voice is picked, then the voice's real one (`voice-lock.json` → `measured.wpm`) once its first part is measured. The two genuinely differ: this niche's references measured 195–206 WPM, the voice 186–187. `text` is sent exactly as written, inline tags included, and tags are not counted as words. `pause_after_s` up to 1 s needs nothing, since the voice's own gap gives it. A longer one names `pause_via`: `"tag"` means a pause tag at this line's end or the next line's start; `"edit"` means a hold inserted by `retime-shots`. Each tag and realised pause gets a line under "Delivery and tags" in `editorial-review.md`, and each `content_flags` hit gets one under "Content flags".

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

Under `50-audio/video-01/`, the TTS tool creates `manifest.json` (voice/model/language/chunks and SHA256 text hashes, line ranges, `finished_parts`, `status`). Completed parts reside in `part-001.mp3` etc. An all-parts-complete pass generates `narration.wav`. Parts keep their line boundaries once recorded. An edited line marks only its part as changed: the dry run lists `changed_recorded_parts`, and `--rerecord-changed` re-records just those, with old takes in `superseded/` and the change in `history`. Adding or removing lines, or changing the voice, model or language, needs `--rechunk`/`--archive-existing` (the folder moves to `video-NN-archive-<time>`). `audio-check` disallows a partial or missing line/audio, rejects a duration outside the audio tolerance, and rejects a narration that, with its planned edit holds, cannot fit the export window. `tts --max-parts 1 --execute` stops after the first part (`mode: partial_by_design_max_parts`) so it can be measured before paying for the rest.

## Voice lock (`voice-pick` writes the voice; `narration-measure` writes `measured`; `tts` and `plan-check` read both)

`60-voice/voice-lock.json`:

```json
{
  "voice_id": "REAL_ACCOUNT_VOICE_ID",
  "generated_voice_id": "REAL_ACCOUNT_VOICE_ID",
  "name": "Narrator name",
  "settings": {"stability": 0.65, "similarity_boost": 0.8},
  "preview_wpm": 195,
  "measured": {"voice_id": "REAL_ACCOUNT_VOICE_ID", "model_id": "eleven_v4",
               "settings": {"stability": 0.65, "similarity_boost": 0.8},
               "wpm": 187, "words": 1356, "speech_s": 435.1, "duration_s": 486.2, "lines": 122,
               "per_line_overhead_s": 0.41, "tag_costs_s": {"[pause]": 1.9},
               "parts": [1], "measured_at": "2026-11-19T15:30:00+00:00"},
  "locked_at": "2026-11-19T13:22:38+00:00",
  "rule": "One voice per run across every video and language; --replace required to deliberately change it."
}
```

`preview_wpm` is information only, since a short preview reads fast and scatters. `measured` comes from a real part of 300+ words recorded with exactly this voice, model and settings. It supersedes the references' pace for the forecast (`plan-check` → `real_forecast_s`) and is what unlocks recording more than one part. `per_line_overhead_s` is the voice's natural silence per script line with the measured tag time taken out. `tag_costs_s` holds the median extra seconds each tag really added on this voice. `voice-pick --replace` keeps `measured` only when the voice and settings are unchanged.

## Line times and edit plan (written by `narration-measure` and `retime-shots`)

`50-audio/video-01/line-times.json` (from `narration-measure`) contains:
- `complete`, `script_sha256` (stale once the script changes), `parts[]` (offset, duration, words, speech, WPM, alignment);
- `wpm`, `per_line_overhead_s`, `natural_line_gap_median_s`, `tags_measured[]` (line, tag, gap, excess), `pause_profile` (the same keys `pace-profile` gives for the references);
- `lines[]`: `{id, index, start_s, end_s, matched_words, words}`.

`70-edit/video-01/edit-plan.json` (from `retime-shots`) contains:
- `narration_duration_s` and `holds[]` (`after_line`, `at_audio_s`, `hold_s`);
- `edit_duration_s`, `edit_narration` (`narration-edit.wav` and its probed duration), `export_window_s`, `within_export_window`;
- `shots[]` (`id`, `beat_id`, `start_s`, `end_s`, `duration_s`) and `notes` (shots the real timing made very short or long).

`retime-shots` also rewrites `60-visuals/video-01/shot-plan.json`'s `start_s`/`end_s`, keeping the planned values once as `planned_start_s`/`planned_end_s`.

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
