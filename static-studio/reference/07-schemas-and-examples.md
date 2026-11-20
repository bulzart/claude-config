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
# Watch the references as films: measurements + one watch sheet per minute (frames with their words).
python "$HOME/.claude/static-studio/scripts/static_core.py" av-profile --run "RUN" --refs V001,V002,V003
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
# Creative direction FIRST (10): 40-plans/video-01/direction.json (evidence, five approaches, strategy,
# two or three treatments with sample moments), a blind read of the treatments, the decision, the lock.
python "$HOME/.claude/static-studio/scripts/static_core.py" review-packet --run "RUN" --video 1 --kind treatment
#   -> spawn ONE fresh agent: "Read only <packet> and follow it exactly." It writes the findings file.
python "$HOME/.claude/static-studio/scripts/static_core.py" review-record --run "RUN" --video 1 --kind treatment
#   -> answer every finding in reviews/treatment-r1-answers.json; write direction.json -> decision.
python "$HOME/.claude/static-studio/scripts/static_core.py" direction-lock --run "RUN" --video 1
# Agent writes blueprint, beat-map (with each beat's direction), script and editorial-review from the treatment.
# The cold read: a fresh agent reads only the bare script.
python "$HOME/.claude/static-studio/scripts/static_core.py" review-packet --run "RUN" --video 1 --kind script
python "$HOME/.claude/static-studio/scripts/static_core.py" review-record --run "RUN" --video 1 --kind script
#   -> answer every finding; a major one: revise, then a round-2 packet for a NEW agent.
python "$HOME/.claude/static-studio/scripts/static_core.py" plan-check --run "RUN" --video 1
# How the comparable narrators speak and pause (same yardstick later used on the voice):
python "$HOME/.claude/static-studio/scripts/static_core.py" pace-profile --run "RUN" --video 1
# Voice: five candidates described by the narrator this story needs (character, register, age,
# accent: the locked treatment's narrator). A preview's pace does not predict the real pace; the agents
# can't listen: compare descriptions, transcripts and measured_delivery; the user may listen and overrule.
python "$HOME/.claude/static-studio/scripts/static_core.py" voice-candidates --run "RUN" --video 1 \
  --count 5 --design 2 --design-description "<the locked treatment's narrator: character, register, age, accent, delivery>" \
  --design-text "A sample of the actual script, 100-1000 characters, read exactly as it will be sent."
#   (Voice Design is billed: without --execute the designs are only priced.)
# The narrator for THIS video's treatment: voice, model, both settings and the reason (an example value, not a default).
python "$HOME/.claude/static-studio/scripts/static_core.py" voice-pick --run "RUN" --video 1 \
  --voice-id "ID_FROM_CANDIDATES_JSON" --name "Narrator name" --settings '{"stability":0.65,"similarity_boost":0.8}' \
  --reason "the treatment's narrator: warm, dry, unhurried; this voice holds that register without strain"
# Optional, billed, approved first: a controlled trial (each question changes one thing). Priced without --execute.
python "$HOME/.claude/static-studio/scripts/static_core.py" narration-trial --run "RUN" --video 1 \
  --plan "RUN/60-voice/video-01/trials/trial-01/plan.json" --check-balance
# After the user's yes: one take at a time; the same command again continues after any stop.
python "$HOME/.claude/static-studio/scripts/static_core.py" narration-trial --run "RUN" --video 1 \
  --plan "RUN/60-voice/video-01/trials/trial-01/plan.json" --execute [--takes P1-A,P1-B]
# Dry run NEVER charges money. Voice, model and settings come from the video's voice lock.
python "$HOME/.claude/static-studio/scripts/static_core.py" tts --run "RUN" --video 1
# Only after the user has approved the voice and the credit cost: the FIRST real part is the
# calibration (paid once, kept). The tool refuses more parts before this voice is measured.
#   tts ... --max-parts 1 --execute
python "$HOME/.claude/static-studio/scripts/static_core.py" narration-measure --run "RUN" --video 1
python "$HOME/.claude/static-studio/scripts/static_core.py" plan-check --run "RUN" --video 1   # real_forecast_s
#   tts ... --execute                      (the rest; finished parts are kept)
#   tts ... --rerecord-changed --execute   (after editing lines, a pronunciation change, a voice revision or a
#                                           narrator change: only those parts)
#   tts ... --rerecord-parts 2 --reason "L105 not heard on its own window either" --execute
python "$HOME/.claude/static-studio/scripts/static_core.py" audio-check --run "RUN" --video 1
python "$HOME/.claude/static-studio/scripts/static_core.py" narration-measure --run "RUN" --video 1   # line times, every line heard
#   narration-measure ... --confirm L105 --reason "the user listened at 07:01 and heard the line"
python "$HOME/.claude/static-studio/scripts/static_core.py" shot-check --run "RUN" --video 1   # before stills; retime-shots refuses a failing plan
# The same gate the image and music workers run before they load anything (free), and the direction each item carries out:
python "$HOME/.claude/static-studio/scripts/static_core.py" media-check --job "RUN/60-visuals/video-01/stills-job.json" --kind stills
# After a meaningful direction change (direction-lock --revise lists outdated_now): update each piece, or keep it on record:
python "$HOME/.claude/static-studio/scripts/static_core.py" direction-reapprove --run "RUN" --video 1 \
  --artifact shot-plan --reason "why it still serves the locked treatment"
python "$HOME/.claude/static-studio/scripts/static_core.py" retime-shots --run "RUN" --video 1
# Agent makes/records CapCut project (edit-plan narration_for_edit at 0 s, speed 1, untrimmed; stills at the retimed
# shot times) and writes project-derived timeline.json, naming the project in capcut_draft.
python "$HOME/.claude/static-studio/scripts/static_core.py" timeline-check --run "RUN" --video 1
# Only after an actual MP4 is accessible:
python "$HOME/.claude/static-studio/scripts/static_core.py" export-check \
  --run "RUN" --video 1 --file "C:/videos/final.mp4" --deep
# The final watch review of THIS file: watch sheets, a fresh reviewer, answers, then every gate at once.
python "$HOME/.claude/static-studio/scripts/static_core.py" av-profile --run "RUN" --video 1 --file "C:/videos/final.mp4"
python "$HOME/.claude/static-studio/scripts/static_core.py" review-packet --run "RUN" --video 1 --kind final --file "C:/videos/final.mp4"
python "$HOME/.claude/static-studio/scripts/static_core.py" review-record --run "RUN" --video 1 --kind final
python "$HOME/.claude/static-studio/scripts/static_core.py" release-check --run "RUN" --video 1 --file "C:/videos/final.mp4"
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
    {"id": "L002", "text": "A turn the story wants to land.", "pause_after_s": 2, "pause_via": "tag",
     "pause_purpose": "the cost of the decision lands before anyone speaks again"},
    {"id": "L003", "text": "[pause] The next line opens after it, as the review decided.",
     "note": "for the team only: never sent, never spoken"},
    {"id": "L004", "text": "The closing line.", "pause_after_s": 4, "pause_via": "edit",
     "pause_purpose": "the last picture stays while the ending settles"}
  ]
}
```

`pace_wpm` above (190) is an example number, not a universal default. Write this run's own measured value: `length-lock.json`'s reference-measured figure before a voice is picked, then the voice's real one (`60-voice/video-NN/voice-lock.json` → `measured.wpm`) once its first part is measured. The two genuinely differ: on one run the references measured 195–206 WPM and the voice 186–187. `text` is sent exactly as written, inline tags included, and tags are not counted as words; it holds nothing else (no SSML, braces, asterisks, stage directions in parentheses, notes in brackets or IPA). `pause_after_s` up to 1 s needs nothing, since the voice's own gap gives it. A longer one names `pause_via` (`"tag"`: a pause tag at this line's end or the next line's start; `"edit"`: a hold inserted by `retime-shots`) and its `pause_purpose`. Each kept tag gets a line under "Delivery and tags" in `editorial-review.md` (plan-check checks it), and each `content_flags` hit gets one under "Content flags".

`40-plans/video-01/pronunciation.json` (optional; only the words the voice may say wrong):

```json
{"terms": [
  {"term": "Hagaru", "say": "/həˈɡɑːruː/", "how": "ipa", "confidence": "likely",
   "source": "the standard romanisation guide for Korean place names"},
  {"term": "Yudam-ni", "say": "Yoo-dahm-nee", "how": "respell", "confidence": "uncertain"}
]}
```

`ipa` goes between forward slashes (sent inside double quotes, as ElevenLabs' v4 examples write it); `respell` is plain letters. `confirmed` and `likely` name their `source`; `uncertain` is flagged for a probe and the user's ear. Only what is sent changes: the script and captions keep the canonical spelling.

`40-plans/video-01/beat-map.json`:

```json
{
  "target_length_s": 720,
  "beats": [
    {"id": "B01", "start_s": 0, "end_s": 92,
     "line_start": 1, "line_end": 18,
     "narrative_job": "Present a real dilemma and its stakes",
     "experience": "Curious and slightly uneasy: the easy answer is about to fail",
     "narration_direction": "Warm and quick, a friend setting up a puzzle; one dry aside",
     "visual_intent": "Show relative position and scale via a map; hold it while the words move on",
     "sound_direction": "Light bed, out at the last line",
     "pace": "brisk, then one held breath",
     "viewer_question": "Why did the obvious solution fail?"},
    {"id": "B02", "start_s": 92, "end_s": 220,
     "line_start": 19, "line_end": 55,
     "narrative_job": "Reveal the first hidden constraint",
     "experience": "The 'oh' of seeing why it was never going to work",
     "narration_direction": "Slower, plainer; let the picture explain",
     "visual_intent": "Reconstruct logistics and compare alternatives with a drawn overlay",
     "sound_direction": "No music under the explanation",
     "pace": "unhurried"}
  ]
}
```

**These snippets are schema examples, not executable complete 12-minute scripts**. A real plan must have sufficient original words, all lines covered by a gap-free map to exactly the locked target, independent sources for all consequential facts, an actual editorial review and complete audio. Copying these snippets alone should correctly fail `plan-check`.

## Audio manifest (automatically produced with paid TTS)

Under `50-audio/video-01/`, the TTS tool creates `manifest.json`: voice/model/language, `voice_lock` (the setup recorded with), `chunks` (line ranges, the `beats` each part carries, `text_sha256` of the canonical text and `sent_sha256` of exactly what was sent, characters), `finished_parts`, `part_revs` (the direction revision each part was recorded under), `part_records` (per finished part: voice, model, settings, voice revision, treatment, direction revision, both fingerprints, the context sent with it, the request id and the credits billed) and `status`. Completed parts reside in `part-001.mp3` etc. An all-parts-complete pass generates `narration.wav`. Parts keep their line boundaries once recorded. A part whose lines, pronunciation, voice setup or direction changed is listed by the dry run, and `--rerecord-changed` re-records just those, with old takes in `superseded/` and the change in `history`; `--rerecord-parts N --reason` redoes a part after listening. Adding or removing lines, or changing the voice, model or language, needs `--rechunk`/`--archive-existing` (the folder moves to `video-NN-archive-<time>`). `audio-check` disallows a partial or missing line/audio, mixed voice setups, a line not heard or a tag read aloud, rejects a duration outside the audio tolerance, and rejects a narration that, with its planned edit holds, cannot fit the export window. `tts --max-parts 1 --execute` stops after the first part (`mode: partial_by_design_max_parts`) so it can be measured before paying for the rest.

`logs/elevenlabs-ledger.jsonl` (the run's spend record, two lines per billed request: narration parts, probes, trials, Voice Design): first `{"phase": "pending", "attempt_id", "at", "kind", "video", "part" or "trial"/"run"/"budget", "model_id", "voice_id", "characters", "context_characters", "max_credits", "balance_before"}` before it is sent, then the same with `"phase": "done"`, `"ok", "error", "request_id", "character_cost_header", "balance_after", "delta"` and, for a trial, `"credits_billed"` (a request cut off by a crash keeps only its pending line; one recovered from the account history gets `"phase": "recovered"`). `delta` is the balance drop (other use of the account in between can only push it up), `character_cost_header` ElevenLabs' own `character-cost` reply header; `logs/elevenlabs-models.json` caches what ElevenLabs reports for each model (credits per character, maximum characters per request) for a day.

## Voice lock (`voice-pick` writes it; `narration-measure` writes `measured`; `tts`, `voice-probe` and `plan-check` read it)

`60-voice/video-01/voice-lock.json` (one per video; videos of a series may name the same voice):

```json
{
  "video": 1,
  "voice_id": "REAL_ACCOUNT_VOICE_ID",
  "generated_voice_id": "REAL_ACCOUNT_VOICE_ID",
  "name": "Narrator name",
  "model_id": "eleven_v4",
  "settings": {"stability": 0.65, "similarity_boost": 0.8},
  "reason": "the treatment's narrator: warm, dry, unhurried; this voice holds that register without strain",
  "treatment": "T1", "production_rev": 1, "narrator_sha256": "...", "voice_rev": 1, "same_voice_as": [],
  "preview_wpm": 195,
  "measured": {"voice_id": "REAL_ACCOUNT_VOICE_ID", "model_id": "eleven_v4",
               "settings": {"stability": 0.65, "similarity_boost": 0.8},
               "wpm": 187, "overall_wpm": 171.4, "words": 1356, "speech_s": 435.1, "duration_s": 486.2, "lines": 122,
               "per_line_overhead_s": 0.41, "tag_costs_s": {"[pause]": 1.9},
               "parts": [1], "measured_at": "2026-11-19T15:30:00+00:00"},
  "locked_at": "2026-11-19T13:22:38+00:00",
  "history": []
}
```

`preview_wpm` is information only, since a short preview reads fast and scatters. `measured` comes from a real part of 300+ words recorded with exactly this voice, model and settings (another episode's measurement of the same setup counts too). It supersedes the references' pace for the forecast (`plan-check` → `real_forecast_s`) and is what unlocks recording more than one part. `per_line_overhead_s` is the voice's natural silence per script line with the measured tag time taken out. `tag_costs_s` holds the median extra seconds each tag really added on this voice. `voice-pick --replace` keeps `measured` only when the voice, model and settings are unchanged. A video recorded before episodes had their own lock keeps the run's older `60-voice/voice-lock.json`.

`60-voice/video-01/trials/trial-01/plan.json` (a `narration-trial` plan; the agents choose the passages from the treatment's own moments):

```json
{"id": "trial-01",
 "budget": {"id": "calibration-2026-11", "max_credits": 3000, "authorised": "the user, on the day: up to 3,000 credits for these trials"},
 "passages": [{"id": "P1", "moment": "opening", "lines": "L001-L008",
               "intended_delivery": "curious and close, like telling a friend something strange"},
              {"id": "P2", "moment": "turning point", "lines": "L210-L216",
               "intended_delivery": "quieter, the weight of the choice landing"}],
 "variants": [{"id": "A"}, {"id": "B", "stability": 0.5}, {"id": "C", "stability": 0.5, "tags": "none"}],
 "runs": [["P1", "A"], ["P1", "B"], ["P1", "C"], ["P2", "A"]],
 "questions": [
   {"id": "Q1", "asks": "does a lower stability widen the delivery without losing the narrator", "compare": [["P1", "A"], ["P1", "B"]],
    "listen_for": "which take sounds more like a person telling you this"},
   {"id": "Q2", "asks": "do the tags add anything the writing does not carry", "compare": [["P1", "B"], ["P1", "C"]]},
   {"id": "Q3", "asks": "does the narrator stay the same person at the turn", "compare": [["P1", "A"], ["P2", "A"]]}]}
```

A variant left blank takes the voice lock's voice, model and settings; `tags` is `as_written` or `none`, `pronunciation` true or false, `context` `none` or `neighbours`. Passage and variant ids have no dashes (a take is named `P1-A`). `listen_for` is the neutral prompt the blind guide shows for that question (it never says which take is which). A plan may carry its own `pronunciation` list (`{"terms": [...]}`, the form of 05) to hear a form before the episode adopts it. Everything a trial makes goes to `60-voice/video-01/trials/<id>/`: the takes (`P1-A.mp3` and their transcripts), `report.json` (each take's exact request, fingerprint, cost and measurements; `sessions` lists each call that worked on it), `listening/` (`Q1-A.mp3` ... and `listening-guide.md`, blind), `answer-key.md` / `answer-key.json` (which label is which take; a take used by two questions is listed under `same_recording`).

## Line times and edit plan (written by `narration-measure` and `retime-shots`)

`50-audio/video-01/line-times.json` (from `narration-measure`) contains:
- `complete`, `script_sha256` (stale once the script changes), `parts[]` (offset, duration, fingerprint, words, speech, WPM, alignment);
- `wpm` (while speaking), `overall_wpm` (pauses included), `per_line_overhead_s`, `natural_line_gap_median_s`, `tags_measured[]` (line, tag, gap, excess), `pause_profile` (the same keys `pace-profile` gives for the references);
- `unheard_lines` (lines still missing after their own window was heard again), `rechecked_lines[]`, `tags_read_aloud[]`, `possible_repeats[]`, `seams[]` (each join: gap, natural gap, `seam_hold_s`, pace, level and pitch range on each side, words heard twice), `beats[]` (pace while speaking and overall, longest gap, numbers per minute, tags, what the beat asked for), `pronunciation_heard[]`;
- `lines[]`: `{id, index, part, start_s, end_s, matched_words, words, heard_on_recheck?, interpolated?}`.

`50-audio/video-01/listening-confirmations.json` holds the user's listening confirmations (`--confirm`), each tied to the part it was heard in.

`70-edit/video-01/edit-plan.json` (from `retime-shots`) contains:
- `narration_duration_s` and `holds[]` (`after_line`, `at_audio_s`, `hold_s`, `kind`: `script` with its `purpose`, or `seam`);
- `edit_duration_s`, `edit_narration` (`narration-edit.wav` and its probed duration), `narration_for_edit` (the file the project must carry, its `sha256` and duration), `export_window_s`, `within_export_window`;
- `shots[]` (`id`, `beat_id`, `start_s`, `end_s`, `duration_s`, and `direction`: its beat's `experience`, `visual_intent`, `sound_direction`, `pace`) and `notes` (shots the real timing made very short or long);
- `beats[]` (each beat's span in the edit, with its direction) and `direction` (the locked treatment's `visual_language`, `sound`, `audiovisual_relationship` and `structure_and_pace`, its `treatment` id and the `production_rev` it follows);
- `shot_structure_sha256` and `script_sha256`: `timeline-check` asks for a new retime when the shots' structure or the script changed.

`retime-shots` also rewrites `60-visuals/video-01/shot-plan.json`'s `start_s`/`end_s`, keeping the planned values once as `planned_start_s`/`planned_end_s`.

**Production agents must not manually toggle `status=complete`.** The manifest represents real provider responses. The tool saves chunks and updates the manifest after each successful response so a credit cutoff cannot masquerade as a short completed voiceover.

## Creative direction (agent written; `direction-lock` checks and locks it)

`40-plans/video-01/direction.json` (10). Every text field is real reasoning in a few sentences; the shape below is
what `plan-check` and `direction-lock` look for, not what makes it good.

```json
{
  "video": 1,
  "evidence": {
    "references": ["V017", "V018"],
    "observations": [{"ref": "V017", "at": "04:00-05:00", "what": "the voice confides while the picture holds one face", "label": "O"}],
    "unknowns": ["retention: no analytics supplied"]
  },
  "approaches": [
    {"id": "A1", "changes": ["structure"], "pitch": "...", "strongest_case": "...", "long_form_risk": "...",
     "challenges_reference_formula": true}
  ],
  "chosen_approach": {"id": "A1", "why": "...", "runner_up": "A3", "why_not_runner_up": "..."},
  "strategy": {"why_this_idea": "...", "viewer_experience": "...", "progression": "...", "fits_and_forced": "...",
               "facts_as_experience": "...", "picture_contribution": "...", "sound_and_breath": "...",
               "distinct_from_references": "..."},
  "treatments": [
    {"id": "T1", "name": "...", "narrator": "...", "writing_voice": "...", "structure_and_pace": "...",
     "visual_language": "...", "sound": "...", "audiovisual_relationship": "...", "emotional_course": "...",
     "evidence_used": "...", "departures": "...", "risks": "...",
     "samples": {"opening": {"narration": "50+ words as spoken", "picture": "what the viewer sees"},
                 "quiet_middle": {"narration": "...", "picture": "..."},
                 "turning_point": {"narration": "...", "picture": "..."}}}
  ],
  "decision": {"treatment": "T1", "why": "...", "taken_from_others": "..."}
}
```

Five approaches (at least three of perspective/scale/structure/voice/visualization among them, at least one that
challenges the references' formula), two or three treatments. `direction-lock.json` keeps the hash, the time, the
treatment, whether a script already existed (`late_reason`) and the history of `--revise`, plus what production
follows: `production_rev` (raised by a change that alters what production must do), `sections` (one hash per field,
so a revision knows exactly what changed), `required` (per artifact, the revision that last touched it and, for a
plan file, its content hash at that moment), `reapproved` (per artifact: the revision, the reason and, for a file, the
content approved) and `reviewed_treatments` (each treatment's words as its last blind read saw them).

## Review records (`review-packet`, a fresh agent, `review-record`, the director's answers)

In `40-plans/video-01/reviews/`: `packet-<kind>-r<N>.md` (what the reader got), `<kind>-r<N>-findings.json` (what it
wrote), `<kind>-r<N>.json` (sealed: the version it read, its findings and their hash), and
`<kind>-r<N>-answers.json` (yours):

```json
{"answers": {
  "F1": {"action": "revised", "lines": ["L003-L011"], "note": "Cut the recap to two lines; the question hangs."},
  "F2": {"action": "disputed", "note": "The repetition is the refrain the ending pays off; kept on purpose."},
  "F3": {"action": "kept", "note": "A minor rhythm note; this line is the breath before the turn."}
}}
```

A major finding is `revised` or `disputed`, never just `kept`, and gets a fresh read in the next round (until round 2
for the script and the final review, round 1 for the treatments).

## Measured evidence (`av-profile`, `narration-measure`)

`20-analysis/av/V###.json` per reference and `70-edit/video-NN/av/export-<id>.json` per export: `summary` (narration:
rate and its spread, pitch range and movement in semitones, loudness contrast, the level under the voice in its
gaps, by third of the film; picture: shots, cuts per minute, shot lengths, moving and still share, flashes, the same
picture again, brightness and saturation), `windows` (every 15 s: the words said and every measure), `shots`,
`sheets` (one JPEG per minute), `thresholds` and `unknowns`. `50-audio/video-NN/delivery.json` holds the same
narration measures for the recorded voice, per beat (`spans`, with what each beat asked for) and next to the
references'. All of it is measurement; none of it is a verdict.

## Real CapCut timeline (agent measured from project)

`70-edit/video-01/timeline.json`:

```json
{
  "canvas": "1920x1080",
  "fps": 30,
  "project_file": "C:/path/to/the/real/capcut/project",
  "capcut_draft": "C:/path/to/the/real/capcut/project",
  "visual_segments": [
    {"start_s": 0, "end_s": 14.5, "shot_id": "S001",
     "asset_path": "C:/path/to/an/actual/still.png", "beat_id": "B01",
     "purpose": "Orient viewer to location before explaining constraints"},
    {"start_s": 14.5, "end_s": 28.2, "shot_id": "S002",
     "asset_path": "C:/path/to/a/diagram.png", "beat_id": "B01",
     "purpose": "Make distance and travel costs immediately visible"}
  ],
  "audio_tracks": [
    {"kind": "narration", "file": "C:/path/to/narration-edit.wav", "start_s": 0, "end_s": 1150.2,
     "source_start_s": 0, "source_end_s": 1150.2, "speed": 1},
    {"kind": "music", "file": "C:/path/to/bed-01.wav", "start_s": 0, "end_s": 96.0, "beats": ["B01", "B02"]}
  ]
}
```

With `capcut_draft`, `timeline-check` reads the narration's segments (file, timeline and source ranges, speed) from the CapCut project itself; the `audio_tracks` narration entry is then only a note. Either way the narration must be the edit plan's `narration_for_edit` file, unchanged, at 0 s, at speed 1, covering the file once from start to end.

## Media records (written by the gated workers, never by hand)

`60-visuals/video-01/stills-provenance.json`: `{"video": 1, "images": {"<file>": {"shot_id", "beat_id",
"frame_prompt_sha256", "production_rev", "treatment", "engine", "made_at"}}}`. `70-edit/video-01/music-provenance.json`:
the same with `beats` and `caption_sha256` per track. `timeline-check` and `release-check` trace the project through
them. Pictures made any other way (supplied by the user, drawn) are accepted as a set with `direction-reapprove
--artifact stills --reason "..."`, on record.

Again these are a small excerpt, not a passing whole-film timeline. Fill every segment until the actual project ends, with meaningful beat IDs and no gaps; base timestamps on CapCut project readback. Timeline gate success still requires a human watch/listen pass and an **independent MP4 export check**.

## Repeat or start a new channel

`/create-video more <RUN> [N]` continues the run, preserves its niche and uses new video IDs; each new video chooses its own direction and narrator (keeping the series' voice and look is a recorded choice). `/create-video clone <RUN>` creates a new run with **only reference inventory and analytical cards**, not shared source assets or an unearned approved script. Re-analyze newly added files; do not automatically duplicate a finished episode.
