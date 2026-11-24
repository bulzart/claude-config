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
# One frame of every shot, for every reference (the content review needs them; analysis-plan counts them).
python "$HOME/.claude/static-studio/scripts/static_core.py" content-review --run "RUN" --ref V001 --shot-sheets
# Split the analysis between agents by reading work alone (01): batches, one brief and one to-do file per agent.
python "$HOME/.claude/static-studio/scripts/static_core.py" analysis-plan --run "RUN"
#   -> spawn one analysis agent per batch, all at once, each with its spawn_prompt only.
# Each agent, per reference: where to look closer, then the content review (01): what is excluded and what stays useful.
python "$HOME/.claude/static-studio/scripts/static_core.py" content-review --run "RUN" --ref V001 --signals
python "$HOME/.claude/static-studio/scripts/static_core.py" inspect-window --run "RUN" --ref V001 --from 12:03 --to 12:09 --why "a fast insert"
python "$HOME/.claude/static-studio/scripts/static_core.py" content-review --run "RUN" --ref V001 --file "RUN/20-analysis/content/V001-draft.json"
# Agents write evidence-grounded 20-analysis/cards/V###.json, notes and content reviews. Then the niches (01):
python "$HOME/.claude/static-studio/scripts/static_core.py" niche-evidence --run "RUN"
#   -> read 20-analysis/niche-evidence.md whole; write 20-analysis/niche-map.json and niche-synthesis.md.
python "$HOME/.claude/static-studio/scripts/static_core.py" niche-check --run "RUN"
#   -> present the niches; the user picks one (or delegates the pick).
python "$HOME/.claude/static-studio/scripts/static_core.py" niche-lock --run "RUN" --niche N2 \
  --user-words "the engineering one"
# The length: Standard from one comparable cohort of the locked niche (its why_comparable goes in as forms_why).
# Never pass --pace-wpm here: length computes it automatically from the references' own
# Whisper transcripts (pure narration time, timestamps stripped). A manual number is a guess: it needs --pace-why (03).
python "$HOME/.claude/static-studio/scripts/static_core.py" length --run "RUN" --video 1 \
  --mode standard --cohort-id "engineering-investigations-12min" --refs V001,V002 --language en
# Own length: --mode own --minutes 18 (its references from the locked niche). A run made before niche discovery
# (no niche_discovery in state.json) still matches labels: --niche "..." --story-form "..." or --cohort-id.
# Creative direction FIRST (10): 40-plans/video-01/direction.json (evidence, two or more approaches, strategy,
# two to four treatments with sample moments), a blind read of the treatments, the decision, the lock.
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
# Every planned pause next to the gap the voice really left there; previews of one moment for the user's ears:
python "$HOME/.claude/static-studio/scripts/static_core.py" holds --run "RUN" --video 1
python "$HOME/.claude/static-studio/scripts/static_core.py" holds --run "RUN" --video 1 --preview L042 --totals 1.1,1.8
# Each one decided: the WHOLE silence after the line (the voice's own gap included), or --no-hold, and why.
python "$HOME/.claude/static-studio/scripts/static_core.py" hold-decide --run "RUN" --video 1 --line L042 \
  --stage narration --total 1.4 --reason "the map finishes drawing the route; longer and the next line waits"
# The look every still carries, after direction-lock and the style bible (example words, not a default; a change: --why):
python "$HOME/.claude/static-studio/scripts/static_core.py" style-lock --run "RUN" --video 1 \
  --style-prompt "gouache illustration, warm muted palette" --departs-when "photorealistic, flat vector, neon" \
  --palette "#8A5A3C,#D9C7A3"
python "$HOME/.claude/static-studio/scripts/static_core.py" shot-check --run "RUN" --video 1   # before stills; retime-shots refuses a failing plan
# The same gate the image and music workers run before they load anything (free), and the direction each item carries out:
python "$HOME/.claude/static-studio/scripts/static_core.py" media-check --job "RUN/60-visuals/video-01/stills-job.json" --kind stills
# After a meaningful direction change (direction-lock --revise lists outdated_now): update each piece, or keep it on record:
python "$HOME/.claude/static-studio/scripts/static_core.py" direction-reapprove --run "RUN" --video 1 \
  --artifact shot-plan --reason "why it still serves the locked treatment"
python "$HOME/.claude/static-studio/scripts/static_core.py" retime-shots --run "RUN" --video 1   # only decided holds
# With the stills: each held silence decided again with its shot (holds --preview shows the still); a changed
# length is retimed before the project is built.
python "$HOME/.claude/static-studio/scripts/static_core.py" hold-decide --run "RUN" --video 1 --line L042 \
  --stage picture --total 1.4 --bed continues --reason "the route is still being drawn for the whole silence; it holds"
# Agent makes/records CapCut project (edit-plan narration_for_edit at 0 s, speed 1, untrimmed; stills at the retimed
# shot times) and writes project-derived timeline.json, naming the project in capcut_draft.
python "$HOME/.claude/static-studio/scripts/static_core.py" timeline-check --run "RUN" --video 1
# The export's sound to the loudness the references are mastered at (the picture copied, the export kept):
python "$HOME/.claude/static-studio/scripts/static_core.py" master-sound --run "RUN" --video 1 \
  --file "RUN/80-deliverables/video-01/export/final.mp4" --out "C:/videos/final.mp4" --target-lufs -14 \
  --refs V006,V030 --why "both length-lock references are mastered at -14 LUFS; the export plays at -23.5"
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

`status` reports each video's stage from its recorded gates, never a stored guess: `planning`, `direction_locked`,
`script_checked`, `narration_recorded`, `narration_measured`, `stills`, `edit_checked`, `exported`, `released`. It moves
`state.json`'s `stage` forward when it lags (the run's stage is its least advanced video's), never backward; a passing
`plan-check` advances it too.

## Content review (agent written; `content-review` checks and saves it)

`20-analysis/content/V###.json`, one per reference, timestamps in `mm:ss` (or `h:mm:ss`, or seconds):

```json
{"looked_at": "every watch sheet and shot sheet, the whole transcript, full frames where it mattered; a closer look at 12:03-12:09",
 "segments": [
   {"id": "S1", "from": "12:03", "to": "12:41", "kind": "religion_superstition", "category": "superstition",
    "what": "a soldier reads an omen in the crows before the attack", "role": "sets up the dread of the night attack",
    "evidence": "said at 12:05-12:20; frames 12:10-12:30 show the birds", "confidence": "sure", "action": "exclude",
    "depends": [{"from": "18:40", "to": "18:55", "why": "the payoff recalls the omen"}],
    "avoid": ["omen", "crows foretelling death"]},
   {"id": "S2", "from": "25:10", "to": "25:30", "kind": "safety", "category": "graphic_injury", "severity": "high",
    "what": "a close view of a wounded soldier's injury", "role": "shows the cost of the crossing",
    "evidence": "frames 25:12-25:26 and a closer look at 10 fps", "confidence": "sure", "action": "restrict_visuals",
    "why": "the cost is told by the count and the faces, never the wound"}],
 "story_without_exclusions": {"status": "bridged", "note": "the dread before the attack comes from the weather and the silence instead"},
 "usable": "the cold open, the 6-second hold before each reveal, the map transitions"}
```

`kind` is `safety` (with a `category`: graphic_injury, distressing, self_harm, dangerous_acts,
sexual_violence_exploitation, sexual_content_minors (sexual content involving a minor, always excluded; a child in an
ordinary scene is not a safety segment by itself, since every person this pipeline pictures is a clearly adult
figure), hate_extremism, nudity_indecency, other; and a `severity`) or one of the user's
creative exclusions, `religion_superstition` (religious or superstition) and `holiday` (holiday), which carry no
severity: they are not harm. `action`: `exclude` (with `avoid`; `depends` for what goes with it), `restrict_visuals`
(safety only) or `keep`, each with `why` (an exclusion: why restricting is not enough, or why it is a device and not a
plain fact). `avoid` is required on an exclusion and optional on a restriction (what must never be shown); both are
then flagged in script lines and picture prompts (the readers get only the standing house rules, never these). Optional `not_segments`:
`[{"at": "mm:ss", "what": "...", "why": "..."}]`, things looked at and cleared. `sexual_content_minors` is always excluded; `high` is never kept as it is; `low` is never excluded;
`evidence` cites the times seen or heard (mm:ss); every `unsure` segment needs a closer look (`inspect-window`)
overlapping it; the shot sheets must exist
(`--shot-sheets`, `20-analysis/content/V###-shots/`: `sheet-NNN.jpg` and `index.json` with each shot's start, end and
the time of the frame shown). The saved file adds the frames the review was made on, the closer looks taken (found on
disk, not typed) and how many shot sheets there were. `content-review --status` lists every
reference's review.

A closer look (`inspect-window`) writes `20-analysis/inspect/V###/<from>-<to>@<rate>/` with its frames (each at its
own `t_s`), `sheet.jpg` and `index.json` (window, rate, why, the words said). `--remove` deletes the frames and keeps
the index. Every picture of an edit: `content-review --video NN --pictures --file looks.json` with
`{"never_show_checked": true, "looks": [{"file": "60-visuals/video-01/S01.png", "result": "clean", "people": "none",
"note": "a ridge road in snow at dawn, two trucks, nobody in sight"}]}` (an `issue` also names its `category`, which is
`people_not_asked_for` when someone appears that the still's prompt does not ask for; `people` is required for a still
whose record carries a `people_question`: `"none"`, or no one, nobody, no people, a note may follow, or who appears; `never_show_checked` is
required while the cited references' reviews rule anything out); `content-review --ref V### --archive` moves a review
and its closer looks to `20-analysis/content-archive/V###-r<n>/` before a blind second review; saved in `60-visuals/video-NN/content-looks.json`
with each file's hash and the content reviews it was checked against (`themes_sha256`: when those change, the timeline
asks for the looks again); `release-check --thumbnail FILE` requires the thumbnail's look clean. Treatment and
beat-map text that names what a cited reference's review cut is rewritten, or carries a recorded context:
`"content_context": [{"where": "treatment T1" | "beat B03", "theme": "excluded_theme:V001/S2", "context": "<six words or
more>"}]`, in direction.json for a treatment and in beat-map.json for a beat.

## Reference cards (agent generated)

Create `20-analysis/cards/V001.json` for every unique video in `00-inventory/references.json`. Required minimum: `reference_id`, `niches` (what the video is about: its subject matter, a list), `story_form` (how it tells it: one primary form), and `viewer_experience` (list of timed meaningful moments); `viewer_reward` keeps what the viewer comes for apart from the rest (01). The analysing agent leaves `cohort_id` out: comparable cohorts are decided in the niche map, with every reference in view. (A run made before niche discovery may carry a director-set `cohort_id` on its cards, which its `length --cohort-id` matches; references of different story forms need `--forms-why`, 03.) The detailed suggested schema is in manual 01; include actual timestamps, source vs interpretation, script delivery, shot/form analysis and tradeoffs.

## Analysis plan and niche discovery (`analysis-plan`, `niche-evidence`, `niche-map.json`, `niche-check`, `niche-lock`)

`20-analysis/agents/plan-r<n>.json` (written by `analysis-plan`, one per round): `basis: "reading work only"`, the
`settings` used, `total_load`, and `batches` `[{agent: "r1-a1", refs: [{ref, duration_s, watch_sheets, shot_sheets,
transcript_words, inspect_candidates, load}], load, minutes, brief, todo, spawn_prompt}]`, with `balance` and
`not_measured_yet`. No subject, niche or format appears in a plan.

`20-analysis/niche-evidence.json` and `.md` (written by `niche-evidence`): `references` in reference order, each
`{ref, file, card, language, subject{niches, editorial_summary, title_promise}, format{story_form, hook},
viewer_reward{reward, from}, visual_style{visual_medium, cuts_per_min, shot_median_s, moving_time_share},
narration{narrator_character, speech_rate_wpm, pitch_range_st, longest_pause_s, pauses_0_8s_plus_per_min,
silence_share, gap_level_db}, runtime_and_pacing{duration_s, minutes, longform, words, rate_p10_p90_wpm},
content{excluded, excluded_n, restricted_n, story_without_exclusions}}`, plus `cards_sha256` (what the evidence was
made from). It holds no time and no batch: the same cards give the same evidence.

`20-analysis/niche-map.json` (the director writes it, 01):

```json
{"niches": [
  {"id": "N1", "name": "How great structures stand up",
   "identity": "the engineering of bridges, towers and dams, told through the problems their builders had to beat",
   "boundary": "stops being this niche when the structure is only a backdrop: travel, biography or architecture as style",
   "viewer_reward": "[I] a hidden force made visible, and seeing why the obvious design would have failed",
   "members": [{"ref": "V104", "role": "core", "why": "one suspension bridge's failure told as a puzzle about wind"},
               {"ref": "V109", "role": "core", "why": "a dam's near-collapse investigated hour by hour"},
               {"ref": "V107", "role": "core", "why": "the history of dams told through five floods they had to hold"},
               {"ref": "V102", "role": "overlap", "why": "a city's water system; it is also about public money"}],
   "formats": [{"form": "single-failure investigation", "refs": ["V104", "V109"]},
               {"form": "chronological history through test events", "refs": ["V107"]},
               {"form": "systems explainer", "refs": ["V102"]}],
   "comparable_cohorts": [{"id": "engineering-investigations-12min", "refs": ["V104", "V109"],
                           "why_comparable": "both single-case investigations told as a puzzle, 11-13 min"}],
   "evidence": [{"ref": "V104", "at": "02:10", "observed": "the obvious fix is drawn first, then crossed out as the wind diagram builds"}]}],
 "outliers": [{"ref": "V111", "why": "a 3-minute workshop tip whose audience no other reference shares"}],
 "shared_across_niches": [{"dimension": "format", "what": "second-person simulation", "refs": ["V103", "V106", "V110"],
                           "note": "a way of telling shared by three niches, not a niche"}],
 "notes": "anything the director wants the next reader of the map to know"}
```

(The values are an example of the form, not a niche to reuse.) `niche-check` writes `20-analysis/niche-check.json`:
`ok`, `issues` (form and traceability: every reference a member or an outlier, a reason per member, a core member per
niche, formats, evidence and cohorts naming members only, the evidence current), `warnings` (a niche that is exactly
one analysis batch, or all from one), and `facts`: `niches`, `outliers`, `in_several_niches`, `members` (core and
overlap per niche), `cohorts` (`{id: {niche, refs, durations_s, median_s, standard_s, standard_min, spread_ratio,
speech_rate_wpm, story_forms, languages, length_would_refuse}}`) and `batches_per_niche`.

`20-analysis/niche-lock.json` (written by `niche-lock`): `niche_id`, `name`, `identity`, `boundary`, `viewer_reward`,
`members` `[{ref, role, why}]`, `formats`, `comparable_cohorts` (with their facts and `why_comparable`), `map_sha256`,
`evidence_sha256`, `user_words`, `decided_by` (`user`, or `director` on the user's delegation with `why`),
`locked_at`, and `refreshed` (each `--refresh`: when, why, the members before). `state.json` carries
`selected_niche` (the name), `selected_niche_id` and `niche_discovery`. `length-lock.json` then records `niche` (the
name), `niche_id`, `niche_lock_sha256` and the `cohort_id` it used.

**Important:** `cohorts` only groups by reported niche/form and measured ffprobe duration. Agents, not a keyword regex, decide what a video is actually about. A video can be in two niches, but a 50-second Short and a 15-minute episode must not share one Standard duration lock. If group spread is large, explicitly choose a narrow set of comparable IDs for `length`.

## Blueprint and exact script (agent generated)

Minimal `40-plans/video-01/blueprint.json`:

```json
{
  "audience_promise": "An answer specific enough to be worth a 12-minute watch",
  "narrative_approach": "Decision-reconstruction narrative following a commander through incomplete information",
  "why_this_length": "The answer requires three meaningful discoveries and context",
  "original_angle": "Follow the overlooked supply decision, not just the battle",
  "audience_knows": "Knows the war happened and roughly when; not the units, the ground or how supply worked",
  "ending_payoff": "The constraint found in B02 settles the choice the viewer weighed in B01: the plan was never possible, so the blame moves from the commander to the map (from this story's own material; a video whose value builds up instead gives reward_shape)",
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
    {"id": "L002", "text": "A turn the story wants to land. [pause]", "pause_total_s": 1.5, "pause_via": "tag",
     "pause_purpose": "the narrator weighs the cost before going on: a hesitation in the telling",
     "pause_picture": "the same map, the crossing circled", "pause_sound": "the bed goes on, quieter"},
    {"id": "L003", "text": "The next line opens after it, as the review decided.",
     "note": "for the team only: never sent, never spoken"},
    {"id": "L004", "text": "The closing line.", "pause_total_s": 3.0, "pause_via": "edit",
     "pause_purpose": "the last picture stays while the ending settles",
     "pause_picture": "the supply road at dusk, empty, held while the last line settles",
     "pause_sound": "the bed resolves on its last phrase, then the end"}
  ]
}
```

`pace_wpm` above (190) is an example number, not a universal default. So are the pause lengths: each is set by its own moment and decided again on the recorded voice and the picture, never copied. Write this run's own measured value: `length-lock.json`'s reference-measured figure before a voice is picked, then the voice's real one (`60-voice/video-NN/voice-lock.json` → `measured.wpm`) once its first part is measured. The two genuinely differ: on one run the references measured 195–206 WPM and the voice 186–187. `text` is sent exactly as written, inline tags included, and tags are not counted as words; it holds nothing else (no SSML, braces, asterisks, stage directions in parentheses, notes in brackets or IPA). `pause_after_s` up to 1 s needs nothing, since the voice's own gap gives it. A longer one names `pause_via` (`"tag"`: a pause tag at this line's end or the next line's start; `"edit"`: a hold inserted by `retime-shots`) and its `pause_purpose`. Each kept tag gets a line under "Delivery and tags" in `editorial-review.md` (plan-check checks it), and each `content_flags` hit gets one under "Content flags". Each comprehension signal gets a line under "Comprehension", or shares one with signals of the same root (a name in common, or one beat): the ids, one kind and the reason (plan-check checks it; `comprehension_signals_grouped_without_a_shared_cause` names a line that groups unrelated ones). Each pace signal is examined under "Pace": a line naming the beat id (or `overall`), five words or more, which beats with one shared cause may share (the audio gate checks it).

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
     "pace": "unhurried",
     "key_moment": "the constraint revealed",
     "carries": ["R1"],
     "hedges": {},
     "significance": {"matters_because": "the plan everyone trusted could never have worked, so the choice the viewer weighed in B01 was made blind",
                      "reward": "the oh of seeing the hidden constraint",
                      "certainty": "established"},
     "depends_on": [{"what": "the choice and what it was meant to achieve", "from": "B01"}]}
  ]
}
```

A passing `plan-check` writes `40-plans/video-01/plan-check.json`: `{"checked_at", "beats": {"B02": {"sha", "lines_sha",
"lines"}}, "history": [{"at", "kept"}]}`, each beat's direction hash and its lines' text hash. A beat whose direction
changed since, while its lines did not, is flagged (`beat_B02_changed_since_its_lines_were_checked`) until its lines are
revised or `plan-check --keep "why they still fit"` is recorded in `history`.

**These snippets are schema examples, not executable complete 12-minute scripts**. A real plan must have sufficient original words, all lines covered by a gap-free map to exactly the locked target, independent sources for all consequential facts, an actual editorial review and complete audio. Copying these snippets alone should correctly fail `plan-check`.

**Examples from one kind of film.** Most examples in this manual follow one factual history story (a commander's supply
decision); the topic-discovery example below is a geography phenomenon. They show each file's shape, not how another
kind of video is built. How the same fields might read elsewhere (illustrations, not templates):

- A tutorial (fixing a door that will not close): `payoff.shape` `progressive`, each step leaving one cause found and
  fixed; the blueprint gives `reward_shape` ("each step removes one cause, so a viewer who stops at any step has
  something fixed"); no key moment is invented, and several beats carry the payoff value.
- A science explainer (why the sky is blue at noon and red at dusk): `builds_to` a mechanism understood; the
  `ending_payoff` is where one cause explains both colours, and that beat is the key moment, its `depends_on` naming the
  beat that showed sunlight holding every colour.
- A comedy (a man who cannot stop apologising): `several`, each escalation paying its own laugh; `factual: false`, its
  material `invented`; the blueprint's `reward_shape` says how the laughs grow, and the biggest turns are key moments
  whose `significance.reward` is the laugh and whose `depends_on` names the setup it pays.

## Audio manifest (automatically produced with paid TTS)

Under `50-audio/video-01/`, the TTS tool creates `manifest.json`: voice/model/language, `voice_lock` (the setup recorded with), `chunks` (line ranges, the `beats` each part carries, `text_sha256` of the canonical text and `sent_sha256` of exactly what was sent, characters), `finished_parts`, `part_revs` (the direction revision each part was recorded under), `part_records` (per finished part: voice, model, settings, voice revision, treatment, direction revision, both fingerprints, the context sent with it, the request id, the credits billed (`credits_billed`) and `recovered_from_history`) and `status`. Completed parts reside in `part-001.mp3` etc. An all-parts-complete pass generates `narration.wav`. Parts keep their line boundaries once recorded. A part whose lines, pronunciation, voice setup or direction changed is listed by the dry run, and `--rerecord-changed` re-records just those, with old takes in `superseded/` and the change in `history`; `--rerecord-parts N --reason` redoes a part after listening. Adding or removing lines, or changing the voice, model or language, needs `--rechunk`/`--archive-existing` (the folder moves to `video-NN-archive-<time>`). `audio-check` disallows a partial or missing line/audio, mixed voice setups, a line not heard or a tag read aloud, rejects a duration outside the audio tolerance, and rejects a narration that, with its planned edit holds, cannot fit the export window. `tts --max-parts 1 --execute` stops after the first part (`mode: partial_by_design_max_parts`) so it can be measured before paying for the rest.

`logs/elevenlabs-ledger.jsonl` (the run's spend record, two lines per billed request: narration parts, probes, trials, Voice Design): first `{"phase": "pending", "attempt_id", "at", "kind", "video", "part" or "trial"/"run"/"budget", "model_id", "voice_id", "characters", "context_characters", "max_credits", "balance_before", "request_sha256", "pid"}` before it is sent, then the same with `"phase": "done"`, `"ok", "error", "outcome", "request_id", "character_cost_header", "balance_after", "delta"` and, for a trial, `"credits_billed"` (a request cut off by a crash keeps only its pending line; one recovered from the account history gets `"phase": "recovered"`). `outcome` is `completed`, `failed` (a 4xx: answered before any work, never billed), `uncertain` (a timeout, a lost connection or a 5xx) or `charged_incomplete` (billed, the answer unusable). An attempt whose outcome is unknown is settled before the same request is sent again: from the account history, or by a `"phase": "reconciled"` row with the reason when the user allowed one new attempt (`--retry-unreconciled`). `delta` is the balance drop (other use of the account in between can only push it up), `character_cost_header` ElevenLabs' own `character-cost` reply header; `logs/elevenlabs-models.json` caches what ElevenLabs reports for each model (credits per character, maximum characters per request) for a day.

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
- `unheard_lines` (lines still missing after their own window was heard again), `missing_runs[]` (a run of four or more words of a heard line still not heard after its own listen: `line`, `words`, `count`), `rechecked_lines[]`, `tags_read_aloud[]`, `possible_repeats[]`, `seams[]` (each join: gap, natural gap, `seam_hold_s`, pace, level and pitch range on each side, `level_step_lu`: the voice's level step across it, from 3 s of speech on each side; words heard twice), `beats[]` (pace while speaking and overall, longest gap, numbers per minute, tags, what the beat asked for), `pronunciation_heard[]`, `pace_signals[]` (evidence, never verdicts: `beat` or `overall`; `kind`: `asked_slower_runs_faster_than_usual`, `asked_faster_runs_slower_than_usual`, `fast_where_densest` or `narration_outside_every_references_pace`; with `wpm_inside_lines`, `ratio`, `natural_variations_from_median`, `asked`, `asked_relative`, `numbers_per_min`, `narration_median_wpm`, `natural_variation_pct`, `variation_from`, `target_wpm`, `narrator_norm_wpm` and `references_wpm`; an older file's `pace_findings[]` is read the same way);
- `lines[]`: `{id, index, part, start_s, end_s, matched_words, words, word_times, gap_after_s, gap_span_s, gap_basis, gap_is_tail?, heard_on_recheck?, interpolated?}`; `gap_after_s` is the silence after the line read from the audio (`gap_basis` `audio`; `whisper` when no quiet run was found; `unknown`, with `null`, while the next line is not recorded); `gap_subrun_s` and `gap_insert_at_s` (the quiet stretch an added silence goes into and where: never into a word, a release or a breath), `gap_floor_under_speech_db` (the voice's own quiet there, dB under its speech), `gap_other_material_s` (a breath or a click inside the silence); `cadence` (with the delivery pass): how the line ends (`last_vowel_vs_line_st`, `last_vowel_fall_st`, `soft_end_s`, `end_level_db`) and the next begins (`next_reset_st`, `next_lead_in_s`, `next_onset_level_db`), and `cadence_usual` the same voice's medians; `line_gaps_from_audio` sums the gaps up (median, p10, p90, shortest, longest); `word_times` is each comparable token's `[start_s, end_s]` on the narration (`null` where Whisper did not hear it): what the captions are timed by.

`70-edit/video-01/captions.json` (from `captions-plan`): `{video, captions: "on"|"off", style: "luckiest-guy"|"montserrat-highlight", box_color?, box_color_why?, language, fps, words: [{w, s, e, line, timing}], timing_evidence: {whisper, shared, between, words, whisper_share}, holds_applied, made_from: {script_sha256, narration_for_edit_sha256, line_times_measured_at, edit_plan_made_at}}`. `w` is the word as the caption shows it (the script's spelling and punctuation), `s`/`e` its time on the edit's timeline; `timing` says where the time came from: `whisper` (its own word time), `shared` (a number written over two words, its time split by length) or `between` (no time from Whisper: placed between its timed neighbours by length). `captions-built.json` beside it records the last build (draft, canvas, size, tracks, texts, the read-back). `state.json` holds the choice: `captions` (`on`/`off`), `caption_style`, `captions_chosen_at`, and `captions_history[]` when the user changed it.

`40-plans/video-01/holds.json` (from `hold-decide`): `{video, decisions: {Lnnn: {...}}, history: [...]}`. Each decision: `line`, `beat`, `stage` (`narration` or `picture`), `total_s` (the whole silence; `null` with `no_hold`), `natural_gap_s` and `gap_basis` (the voice's gap there, from the audio), `added_s`, `resulting_gap_s`, `outcome`, `reason`, `listened` (the user's words, when they heard the previews), `previews` (the files rendered for it), `parts` (the fingerprint of each recorded part it was decided on: re-recorded, it no longer stands), `proposal` (what the script planned), `voice_gaps`, `transition` (`into` and `out_of`: `clean` or `fade`; `bed`: `continues`, `enters`, `stops`, `dips`, `swells` or `none`; `fades_on_narration_clock`), the facts it was decided on (`ending`, `endings_usual`, `inside_silence`), and at the picture stage `picture` (the shot on screen, its still and that still's fingerprint). A replaced decision moves to `history` with `superseded_at`.

`50-audio/video-01/listening-confirmations.json` holds the user's listening confirmations (`--confirm`), each tied to the part it was heard in.

`70-edit/video-01/edit-plan.json` (from `retime-shots`) contains:
- `narration_duration_s` and `holds[]`: each silence inserted (`after_line`, `at_audio_s`: inside the voice's own silence, `hold_s`: what was added, `kind`: `script` with its `purpose`, `total_s` decided, `natural_gap_s`, `expected_gap_s`, `resulting_gap_s` measured in `narration-edit.wav`, `stage`; or `seam`); `pauses[]`: every decided pause and what it became (`hold_s` 0 when the voice's own gap already gives it, or no hold was decided), its `transition` (with the fades applied) and `times_in_edit` (`silence_from_s`, `silence_to_s`, `next_line_s`: where the bed's move goes); `hold_decisions_sha256` (a later decision asks for a new retime); `voice_gaps`;
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
  "subject": {
    "scope": {"kind": "niche", "user_words": "geography", "niche": "geography",
              "understood_as": "how a place on Earth works: the forces that shape it and what they make it look like",
              "boundary": "it stops being geography when the place is only a backdrop for a person's story"},
    "audience_value": "this audience comes to understand how a place works, not to collect facts about it",
    "from_references": [{"ref": "V017", "at": "02:10-02:40", "observed": "the map zooms out as the cause is named",
                         "interpretation": "the relation is shown before it is explained, so it lands"}],
    "candidates": [
      {"id": "T1", "subject": "why one lake turns animals to stone", "value_form": "a natural phenomenon explained",
       "factual": true, "what_happens": "...", "why_it_matters": "...", "reward": "...",
       "strongest_material": [
         {"id": "M1", "what": "the water's chemistry preserves what falls in", "certainty": "established", "claims": ["C01"]},
         {"id": "M2", "what": "why so many birds land there", "certainty": "contested", "claims": ["C02"], "hedge": "..."},
         {"id": "M3", "what": "a bird would keep its shape for years", "certainty": "reasoned", "from": ["M1"],
          "reasoning": "..."}],
       "runtime": {"progression": [{"adds": "the eerie photographs, then the question they raise", "material": ["M1"]},
                                   {"adds": "...", "material": ["M2", "M3"]}],
                   "verdict": "sustains", "why": "...", "material_minutes": 9},
       "payoff": {"shape": "builds_to", "rests_on": ["M1", "M3"], "why_substantial": "...", "needs_first": "...",
                  "worth_the_buildup": "..."},
       "feasibility": "..."},
      {"id": "T2", "subject": "...", "...": "researched more lightly: sources may stand in for claims"}
    ],
    "selection": {"candidate": "T1", "why": "...", "decisive_material": ["M1"],
                  "over_alternatives": [{"candidate": "T2", "why_not": "..."}]},
    "value_to_carry": [{"id": "R1", "what": "...", "why_it_matters": "...", "certainty": "established",
                        "rests_on": ["M1"], "payoff": true},
                       {"id": "R2", "what": "...", "why_it_matters": "...", "certainty": "contested", "hedge": "...",
                        "rests_on": ["M2"], "needs_first": ["R1"]}],
    "dropped": []
  },
  "evidence": {
    "references": ["V017", "V018", "V031"],
    "observations": [{"ref": "V017", "at": "04:00-05:00", "what": "the voice confides while the picture holds one face", "label": "O"}],
    "borrowed": [{"ref": "V031", "technique": "a cutaway drawing that builds up one layer at a time as each is named",
                  "not_taken": "its subject (a kitchen recipe) and what a cooking video assumes"}],
    "unknowns": ["retention: no analytics supplied"]
  },
  "approaches": [
    {"id": "A1", "changes": ["structure"], "pitch": "...", "strongest_case": "...", "long_form_risk": "...",
     "challenges_reference_formula": true}
  ],
  "chosen_approach": {"id": "A1", "why": "...", "runner_up": "A3", "why_not_runner_up": "...", "exploration": "..."},
  "strategy": {"why_this_idea": "...", "viewer_experience": "...", "progression": "...", "fits_and_forced": "...",
               "facts_as_experience": "...", "picture_contribution": "...", "sound_and_breath": "...",
               "distinct_from_references": "..."},
  "treatments": [
    {"id": "T1", "name": "...", "narrator": "...", "writing_voice": "...", "structure_and_pace": "...",
     "visual_language": "...", "sound": "...", "audiovisual_relationship": "...", "emotional_course": "...",
     "evidence_used": "...", "departures": "...", "risks": "...",
     "carries_values": [{"value": "R1", "how": "..."}],
     "samples": {"opening": {"narration": "50+ words as spoken", "picture": "what the viewer sees"},
                 "quiet_middle": {"narration": "...", "picture": "..."},
                 "turning_point": {"narration": "...", "picture": "..."}}}
  ],
  "decision": {"treatment": "T1", "why": "...", "taken_from_others": "...", "carries_payoff": "..."}
}
```

`subject` comes first (02 "Finding the subject"): the user's scope (`understood_as` and `boundary` for every kind, a
niche included; for a subject, topic or story also `selection.how_scope_kept`; in a run grouped by `--cohort-id`,
`niche` is the cohort id or a niche its references' cards name, never the internal `__cohort__:` label), what this
audience values, what the references show
(observed apart from interpreted), the researched candidates (at least two in an open scope; each material item with
its `id` and certainty: established on `claims` whose sources the ledger says were read, reasoned `from` established
items, contested with its `hedge`, speculative or assumed with its `framed_as`, invented only when not factual), each
candidate's `runtime` (`progression` of what the viewer newly gets on which material, `verdict`, `why`, `shortfall`;
`runtime_decision` with the user's words when the chosen one is short or uncertain) and `payoff` (`shape`: `builds_to`,
`several` or `progressive`; `rests_on`, the candidate's own material ids in a factual subject; `why_substantial`;
`needs_first`; `worth_the_buildup`; required for the chosen one, a warning for an alternative), the choice
(`decisive_material`,
confirmed when established; `over_alternatives`, one reason per alternative) and `value_to_carry` (`rests_on`,
`needs_first`; the value the payoff delivers marked `"payoff": true`, resting on the payoff's material: never dropped,
reaching a key moment for `builds_to` or `several` and more than one beat for `progressive`), which the beat map
`carries` in that order (with `hedges` for a contested, speculative or assumed value
in an ordinary beat), the script says (a claim's `line_refs` inside the carrying beat) and the key moments' shots show
(`carries_significance`; every shot of a beat that carries an uncertain value says how its picture keeps it so,
`uncertainty_shown`, 04). A direction locked before `subject` existed keeps working, with a warning.

`30-research/video-01/sources.md`, one entry per source (the `Access` line is what the checks read):

```markdown
### S1. <author/issuer>, <title>, <journal or publisher>, <date>
- Primary: the study itself (peer-reviewed). URL: <url>
- Access: read (abstract, methods and results)
- Supports: C01, C02. Counterevidence: none on the finding; whether it matters in the living animal is open (C03).
- Status: primary record.
```

`30-research/video-01/claims.json`: `{"claims": [{"id": "C01", "claim": "...", "sources": ["S1"], "confidence":
"confirmed", "note": "...", "line_refs": ["L034"]}]}`; confidence is confirmed (a primary record, or two or more
independent credible sources, read), likely (one credible source), disputed or legend. At least two approaches
(between them at least three of perspective/scale/structure/voice/visualization, at least one that challenges the
references' formula), with `chosen_approach.exploration`: what range of ways to tell it was considered and why these
approaches cover it. Two to four treatments, each with `carries_values` (`[{value, how}]`: how it delivers every payoff
value, in its own terms), and the `decision` with `carries_payoff` (how the chosen treatment makes the payoff land); a
change to the chosen treatment's `carries_values` marks the beat map and script. Evidence that cites a reference
outside the locked niche declares it in `evidence.borrowed` (`[{ref, technique, not_taken}]`: the technique borrowed,
and the subject assumptions not taken). `direction-lock.json` keeps the hash, the time, `planning_rules` (2 on a lock made since 2026-11-24, kept through
`--revise`; a lock without it was approved before them, and the planning rules added that day are advisory for it,
10 §3), `planning_migration` on such an older lock once a substantive revision reached something (`{to, sections,
artifacts, history}`: where the current rules now apply), the treatment, whether a script already existed (`late_reason`) and the history of `--revise`, plus what production
follows: `production_rev` (raised by a change that alters what production must do), `sections` (one hash per field,
so a revision knows exactly what changed; the chosen subject's own description, its research, the other
candidates and each researched value apart), `required` (per artifact, the revision that last touched it and, for a
plan file, its content hash at that moment, or, for a change scoped to a researched value, the hash of each beat, line
or shot it reaches: `parts`), `research` (each ledger entry and claim as the direction was locked on them, renewed by
`--research-rechecked`), `reapproved` (per artifact: the revision, the reason and, for a file, the
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
 },
 "revision_notes": {"L045": "Reworded for the ear only: the same fact, the same order, the same hedge."}}
```

A major finding is `revised` or `disputed`, never just `kept`, and gets a fresh read in the next round (until round 2
for the script and the final review, round 1 for the treatments). A fresh read also follows a changed line the
reader's verdict rested on (`script_revised_where_it_matters_since_its_last_read:L045(key_moment:B05),...`: a key
moment's lines and what they depend on, a hedge, a value's beat, a claim's line, a comprehension gap), however few its
words; the share of words changed is only a warning. `revision_notes` says, per line and in five words or more, that
a change is wording only: that line then forces no fresh read, and it leaves the count of lines edited after review.

## Measured evidence (`av-profile`, `narration-measure`)

`20-analysis/av/V###.json` per reference and `70-edit/video-NN/av/export-<id>.json` per export: `summary` (narration:
rate and its spread, pitch range and movement in semitones, loudness contrast, the level under the voice in its
gaps, by third of the film; picture: shots, cuts per minute, shot lengths, moving and still share, flashes, the same
picture again, brightness and saturation), `windows` (every 15 s: the words said and every measure), `shots`,
`sheets` (one JPEG per minute; each tile names its frame's own time and the words of its five seconds), for an
export also `shot_sheets` (one frame of every shot, for the final reviewer), `sampled_fps` and `sampler` (how the frames were taken: cut counts compare only between videos sampled alike), `inspect_candidates` (stretches the samples cannot settle), `thresholds` (the picture's are seconds turned into frame pairs at that rate) and `unknowns`. `10-media/V###/frame-index.json` (2 fps run): `{mode: "source_pts", sampler, fps, interval_s, clock_origin_s, max_gap_s, frames: [{file, t_s, pts_s, slot_s, approx_s}]}` (`approx_s` repeats `t_s` for older readers; a run made before keeps `mode: "nominal_sample_time"`). `preparation.json` keeps the frames' and the transcript's cache keys apart (`frames_signature`: source, rate, width, sampler; `transcript_signature`: source, Whisper model), so new frames never re-run Whisper. `transcript.json` records the `engine` Whisper really ran on (device, compute type, GPU) with `elapsed_s` and `realtime_x`. `50-audio/video-NN/delivery.json` holds the same
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
"uncertainty_shown", "style_lock_rev", "style_note", "style_departure", "frame_prompt_sha256", "production_rev", "treatment", "engine", "submitted_prompt",
"submitted_prompt_sha256", "drew_from", "file_sha256", "made_at"}}}`; a FLUX still adds `precision` (int8), `comfyui`
(its version), `models` and `model_bytes`, `request_sha256`, `caption_checks`, `caption_notes`, `caption_sha256`, `seed`, `steps`,
`size` and `refs` (each with its path and sha256: the run's own material or a style-lock reference, refused otherwise
as `item_N_reference_outside_the_run`), and, when there is one, `caption_accepted` (`issues`, `why`, `sha256`: a
stopped caption drawn on the director's word, from the job item's `accept_caption`, `{"sha256": "<the stopped
caption's>", "why": "<five words or more>"}`) and `people_question` (`prompt_excludes_people`, `hints`: what the
still's look must answer). A stills job item may also carry `style_note`, `style_departure`, `content_note` and
`on_caption_refused` (04). `submitted_prompt` is what the image model drew (the upsampler's caption, or the
approved request itself); `drew_from` says which: `caption`, `request`, or `request (its caption was refused)`;
`uncertainty_shown` appears for a shot that has one (04), and `style_lock_rev` names the style lock the still
was made under. `60-visuals/video-01/style-lock.json` (from `style-lock`, 04): `{video, rev, style_prompt, departs_when, palette, refs:
[{file, sha256}], visual_language_sha256, style_bible_sha256, locked_at, why, history}` (`departs_when`: the
phrases that would be another look, kept in `history` too). `70-edit/video-01/music-provenance.json`: the same with
`beats`, `caption_sha256`, `serves` and `direction` (the treatment's `sound`, and per beat its `sound_direction`,
`experience` and `pace`, with a key moment's meaning) per track, and its `config`, `steps`, `seed`, `duration` and
`caption_sent_sha256` (exactly what ACE-Step got: the worker sends at most 500 characters of a caption, and the gate
refuses a longer one, `track_N_caption_longer_than_the_music_model_reads`). `timeline-check` and `release-check` trace the project through
them. Pictures made any other way (supplied by the user, drawn) are accepted as a set with `direction-reapprove
--artifact stills --reason "..."`, on record.

Again these are a small excerpt, not a passing whole-film timeline. Fill every segment until the actual project ends, with meaningful beat IDs and no gaps; base timestamps on CapCut project readback. Timeline gate success still requires a human watch/listen pass and an **independent MP4 export check**.

## Repeat or start a new channel

`/create-video more <RUN> [N]` continues the run, preserves its niche and uses new video IDs; each new video chooses its own direction and narrator (keeping the series' voice and look is a recorded choice). `/create-video clone <RUN>` creates a new run with **only reference inventory and analytical cards**, not shared source assets or an unearned approved script. Re-analyze newly added files; do not automatically duplicate a finished episode.
