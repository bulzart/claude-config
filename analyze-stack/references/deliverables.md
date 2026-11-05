# Deliverables — `70-deliverables\DELIVERABLES.md`, `prompts-final.md`, `state.json`, `GENERATE-YOURSELF.md` (Stage 7)

Owner brief deliverables: "the full analysis report, the beat map and viral breakdown, the style
profile, the product spec sheet and swap map (if a swap was chosen), the compression plan (Mode 3),
the numbered clip prompts with durations, reference attachments and continuity notes, the anomaly-check
results, and a session state file so the skill knows the context when I come back with the generated
clips." Plus (owner rules): the reference bundle, the sliced source segments for the edit approach,
the G1 gate, and the hand-off document when the owner generates elsewhere.

## 1. `70-deliverables\DELIVERABLES.md` (index + summary; written by the main session)

```markdown
# Deliverables — <run-id>
Source: <file/link> · <duration> s · approach: replicate (Mode 1) | Seedance 2.5 edit · product: <keep | e1 → slug> · style: keep | swap → <target> · platform: TikTok 9:16
Result: 5 clips × 13/12 s = 62 s | 4 edit segments (3 to edit, 1 passthrough) · anomaly check: clean after round 2

## What to generate, in what order, with which attachments
| # | item | duration | mode | attachments (upload order) | continuity |
|---|---|---|---|---|---|
| 1 | 50-prompts\clip-01.md | 13 s | omni_reference | product-front.jpg → @Image 1 · product-label.jpg → @Image 2 · clip-01-start-00m00.00s.jpg → @Image 3 | starts the video; ends: <end state summary> |
| 2 | 50-prompts\clip-02.md | 13 s | omni_reference | same product images · clip-02-start-00m13.00s.jpg → @Image 3 | starts from clip 1's end state |
…
Generate in this order (parallel is fine unless "chained" was requested); join in order with join_clips.py.

## Cost (Higgsfield, seedance_2_5; rates from the spec notes; preflight in generation-log.md when run)
| resolution | per item | total | balance |
|---|---|---|---|
| 480p | 39 / 36 | 189 | 1051 |
| 720p | 84.5 / 78 | 409.5 | |
| 1080p (default) | 117 / 108 | 567 | |

## Files
| Deliverable | Path |
|---|---|
| Analysis report | 20-analysis\report.md |
| Beat map + viral breakdown | 20-analysis\beat-map.md, narrative.md |
| Style profile (+ style bible) | 20-analysis\style-profile.md (40-plan\style-bible.md) |
| Product spec + swap map | 30-decisions\product-spec.md, swap-map.md |
| Edit intent (edit approach) | 30-decisions\edit-intent.md |
| Plan (slicing / segments / compression / edit segments) | 40-plan\… , plan.json, continuity-sheet.md |
| Prompts | 50-prompts\clip-NN.md | edit-NN.md, prompts.json; final list: 70-deliverables\prompts-final.md |
| Anomaly check | 60-qa\anomaly-check.md, fixes-round-N.md, qa.json |
| Reference bundle | 70-deliverables\references\ (product images, cited frames, motion slices; edit: seg-NN.mp4 + seg-NN-audio.mka) |
| Answers | 30-decisions\answers.json |
| State | state.json (stage awaiting-generation) |
| Hand-off (if "I will generate myself") | 70-deliverables\GENERATE-YOURSELF.md |

## Known risks / open items
- <from anomaly escalation, feasibility, swap-map needs-owner-decision, passthrough notes>
```

## 2. `70-deliverables\prompts-final.md`

Numbered items in generation order; per item: header line (number, duration, source slice, mode,
aspect, resolution, audio flag), the attachments table (tag → file → use only / do not use), the
prompt text in a fenced block (verbatim from the clip/edit file), the continuity note (from / to), and
for edit segments the source segment path + the mux instruction. Passthrough segments are listed with
"PASSTHROUGH — not generated; joined from the original". A one-line total at the top: items, seconds,
estimated credits.

## 3. `state.json` (root of the run folder; updated at the end of every stage by `tools\state.py`)

Written only through `python C:\Users\Bulzart\.claude\analyze-stack\tools\state.py "<run>" set key=value …`
(dotted keys write nested values, e.g. `answers.Q1="Replace red 12 oz can"`; values parse as JSON when
possible) and `state.py "<run>" add-file <stage-dir> <path> …` (`files` is keyed by the run-folder stage
directory, exactly as `tools\common.state_add_files` writes it). `intake.py` creates the file.

```json
{
  "run_id": "20260916-101500-snowscents",
  "stage": "awaiting-generation",
  "approach": "replicate",
  "mode": 1,
  "answers": {"Q1": "Replace red 12 oz can", "Q1a": "Attached — identify it", "Q1b": "Yes, exact product", "Q2": "Replicate with generated clips (default)", "Q2m": "Mode 1 — full replication", "Q3b": "15s (default)", "Q3c": "Equal lengths only (default)", "Q5": "Keep the original style (default)", "Q6": "TikTok 9:16 (default)", "A3": null, "G1": null},
  "files": {"00-input": ["00-input/input.json", "00-input/source.mp4"], "10-measure": ["10-measure/probe.json", "10-measure/cuts.json", "10-measure/shots.json", "10-measure/measure-summary.md"], "20-analysis": ["20-analysis/report.md", "20-analysis/beat-map.json"], "30-decisions": ["30-decisions/answers.json", "30-decisions/swap-map.md"], "40-plan": ["40-plan/plan.json", "40-plan/continuity-sheet.md"], "50-prompts": ["50-prompts/prompts.json"], "60-qa": ["60-qa/qa.json"], "70-deliverables": ["70-deliverables/DELIVERABLES.md", "70-deliverables/prompts-final.md"]},
  "counts": {"items": 5, "passthrough": 0, "generated": 0},
  "next_step": "G1",
  "source": "00-input/source.mp4",
  "input": {"duration_s": 62.4, "width": 1080, "height": 1920, "fps": 30.0, "video_codec": "h264", "has_audio": true},
  "created": "2026-09-16T10:15:00+02:00",
  "updated": "2026-09-16T16:40:00+02:00"
}
```

`next_step` values `/analyze-stack` understands: `measure` · `analysis` · `report` · `questions` · `product` ·
`planning` · `continuity` · `style-bible` · `feasibility` · `prompts` · `anomaly-check` · `deliverables` ·
`G1` · `G1-remaining` (after a test clip) · `generate` · `drop-clips` (owner generates elsewhere) ·
`P1` · `clip-qa` · `P0` · `trend` · `P2` · `P3` · `editor` · `final-check` · `publish`.

Stage values, in order: `intake` → `measured` → `analyzed` → `questions` → `product` (swap only) →
`planning` → `prompts` → `qa` → `awaiting-generation` → `generating` → `generated` →
`awaiting-edit-decision` → `editing` → `done` (or `re-edit`). Resume: the main session reads
`stage` + `next_step` and continues from there; stages whose outputs exist are skipped unless the owner
asks to redo them.

`30-decisions\answers.json`: `{"answers":[{"key":"Q1","question":"<verbatim>","answer":"<label or Other text>","at":"…"}]}` appended after each answer, before the next question.

## 4. `GENERATE-YOURSELF.md`
Format in `generation-playbook.md` §5. Written only when G1 = "I will generate myself"; then
`state.json.next_step = "drop generated clips in chat (any names; P1 will confirm the mapping)"`.

## 5. Owner-facing summary in chat (after the files are written)
≤ 20 lines: result line, the "what to generate" table (or its first 5 rows + path), the cost line,
the paths to DELIVERABLES.md and prompts-final.md, then the G1 question.
