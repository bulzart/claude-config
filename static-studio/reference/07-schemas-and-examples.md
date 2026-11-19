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
python "$HOME/.claude/static-studio/scripts/static_core.py" length --run "RUN" --video 1 \
  --mode standard --niche "military history" --story-form "historical narrative" \
  --refs V001,V002,V003 --language en --pace-wpm 143
# Agent writes blueprint/script/beat-map/editorial-review, then validates.
python "$HOME/.claude/static-studio/scripts/static_core.py" plan-check --run "RUN" --video 1
# Dry run NEVER charges money. The ID below is a placeholder, not a valid voice.
python "$HOME/.claude/static-studio/scripts/static_core.py" tts --run "RUN" --video 1 \
  --voice-id "REPLACE_WITH_REAL_VOICE_ID" --model-id eleven_v4
# Only after the user has approved the selected voice, model and credit cost:
# ... repeat the same command with --execute
python "$HOME/.claude/static-studio/scripts/static_core.py" audio-check --run "RUN" --video 1
# Agent makes/records CapCut project and writes project-derived timeline.json.
python "$HOME/.claude/static-studio/scripts/static_core.py" timeline-check --run "RUN" --video 1
# Only after an actual MP4 is accessible:
python "$HOME/.claude/static-studio/scripts/static_core.py" export-check \
  --run "RUN" --video 1 --file "C:/videos/final.mp4" --deep
python "$HOME/.claude/static-studio/scripts/static_core.py" status --run "RUN"
```

## Reference cards (agent generated)

Create `20-analysis/cards/V001.json` for every unique video in `00-inventory/references.json`. Required minimum for CLI grouping: `reference_id`, `niches` (list of category names), `story_form` (one primary form), and `viewer_experience` (list of timed meaningful moments). The detailed suggested schema is in manual 01; include actual timestamps, source vs interpretation, script delivery, shot/form analysis and tradeoffs.

**Important:** `cohorts` only groups by reported niche/form and measured ffprobe duration. Agents, not a keyword regex, decide what a video is actually about. A video can be in two niches, but a 50-second Short and a 15-minute episode must not share one Standard duration lock. If group spread is large, explicitly choose a narrow set of comparable IDs for `length`.

## Blueprint and exact script (agent generated)

Minimal `40-plans/video-01/blueprint.json`:

```json
{
  "audience_promise": "An answer specific enough to be worth a 12-minute watch",
  "central_question": "What did the participants know at the decisive moment?",
  "why_this_length": "The answer requires three meaningful discoveries and context",
  "original_angle": "Follow the overlooked supply decision, not just the battle",
  "human_lens": "What a planner can and cannot know from one report",
  "ending_payoff": "Return to the opening dilemma with new evidence",
  "visual_grammar": "Earth-tone maps, aerial diagrams, restrained artifact illustration",
  "factuality": "factual",
  "research_sources": ["S1", "S2", "S3"],
  "chapter_outline": [{"id": "B01", "purpose": "orient"}, {"id": "B02", "purpose": "complicate"}]
}
```

`40-plans/video-01/script.json`:

```json
{
  "language": "en",
  "pace_wpm": 143,
  "lines": [
    {"id": "L001", "text": "Start with a meaningful, specific opening line.", "pause_after_s": 0.5},
    {"id": "L002", "text": "Continue naturally, with context and a real reason to care.", "pause_after_s": 0.2}
  ]
}
```

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

Under `50-audio/video-01/`, the TTS tool creates `manifest.json` (voice/model/language/chunks and SHA256 text hashes, line ranges, `finished_parts`, `status`). Completed parts reside in `part-001.mp3` etc. An all-parts-complete pass generates `narration.wav`. A model/voice/script change during a partial recording requires deliberate reconciliation; the tool will refuse silent reuse. `audio-check` disallows a partial or missing line/audio, and rejects a delivered duration far from lock.

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
