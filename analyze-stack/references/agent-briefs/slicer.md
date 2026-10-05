# slicer — agent brief (Stage 4, Mode 1 full replication; also slices confirmed Mode 2 segments; one agent)

Load first: `LAYOUT.md`, `references\mode-rules.md` §1 (slicing rules), §6 (feasibility), §7 (`plan.json`),
`references\continuity-rules.md` §3 (which reference frames a clip needs), `seedance\SEEDANCE-SPEC.md` §2.1
(duration limits — read the values, never assume), `tools\README.md` if present.

## Purpose
Cut the original timeline into consecutive clip slices of the owner's chosen length (Q3b, equal or
uneven per Q3c), inside the spec's duration limits, each slice listing its beats, shots, internal cuts,
verbatim dialogue with local timestamps and the reference frames to extract; compute feasibility flags
for A3; write `plan.json`.

## Inputs
`10-measure\probe.json`, `cuts.json`, `shots.json`, `transcript.json`, `20-analysis\beat-map.json`, `audio.md`,
`30-decisions\answers.json` (Q2m, Q3b, Q3c; for Mode 2 the confirmed segment list from A1), `swap-map.json`
(moments per clip), `30-decisions\product-spec.md` when a swap exists.

## Outputs
`40-plan\slicing.md`, `40-plan\plan.json` (schema in mode-rules §7; `approach: "replicate"`, `mode: 1` or `2`),
`50-prompts\references\clip-NN-start-<00m00.00s>.jpg` (one per clip) and `clip-NN-shot-K-<t>.jpg` (one per
internal shot), `state.json` files index updated.

### `slicing.md` skeleton
```markdown
# Slicing — <run-id> · Mode 1 · original 62.40 s · clip length 15 s (Q3b) · equal (Q3c) · spec limits read: 4–30 s
Plan: 5 clips → 13, 13, 12, 12, 12 s (= 62 s; the last 0.40 s is a held frame in clip 05)
| clip | source in | source out | dur | beats | shots | cuts inside (local s) | dialogue (local s, verbatim) | swap moments | references |
| 01 | 00m00.00s | 00m13.00s | 13 | b01–b03 | 1–3 | 1.40, 3.40 | 0.30 "okay this is the one…" | M01, M02 | clip-01-start-00m00.00s.jpg, clip-01-shot-2-00m01.40s.jpg, clip-01-shot-3-00m03.40s.jpg |
## Feasibility (for A3)
| clip | risks | recommendation |
| 03 | two people + pour; handheld whip pan at 00m34.10s | split at the cut 00m34.10s → 10 s + 5 s (uneven) or lock the camera |
```

## Method
1. Read the limits from `SEEDANCE-SPEC.md` §2.1 (min/max seconds, integer durations). Refuse a Q3b value
   outside them (write the refusal in `slicing.md` and return; the main session re-asks).
2. Run the slicer script (one call per window; Mode 2 = one call per A1-confirmed segment with `--start`
   and `--number-from` so numbering continues):
   `python C:\Users\Glaresquare1\.claude\analyze-stack\tools\slicer.py --duration <D> --clip-seconds <Q3b> --min-clip <MIN> --max-clip <MAX> [--uneven --shots "<run>\10-measure\shots.json" --snap-window 3] [--start <s>] [--number-from <n>] --out "<run>\40-plan\plan-slices.json"`
   (MIN/MAX are the values you read from the spec; exit 2 = Q3b outside the limits → write the refusal).
   Output: `{clips:[{number,start,end,duration,gen_duration_s,snapped,cut_t}], warnings}` — `gen_duration_s`
   is the integer duration for the generation call. If the script is absent, compute by hand exactly as
   mode-rules §1: equal → `N = ceil(D/L)`, integer durations summing to `round(D)`, the last clip absorbs
   rounding; uneven → boundaries snap to hard cuts (confidence ≥ 2) within ±3 s or to beat boundaries,
   never mid-word, every slice within the limits. Check the mid-word rule yourself in both cases
   (`transcript.json` word timestamps) and move a boundary to the nearest word gap when needed.
3. For every clip: beats covered, shots, cuts inside (local seconds), dialogue lines with local
   timestamps (verbatim from `audio.md`), swap-map moments inside, and the reference frames to extract.
4. Extract frames (PATH refresh first; `$ff` = ffmpeg path from LAYOUT):
   `& $ff -hide_banner -loglevel error -y -ss <t> -i "<run>\00-input\source.mp4" -frames:v 1 -update 1 -q:v 2 "<run>\50-prompts\references\clip-01-start-00m00.00s.jpg"`
   (one line per frame; `clip_frames.py` is for whole clips, not for single source timestamps).
5. Feasibility per clip (mode-rules §6; cues from `beat-map.json.beats[].feasibility`): ≥ 2 risky items →
   a row with a concrete recommendation (split at cut X / lock camera / shorter target / drop shot).
6. Write `plan.json` (`items[]` with `kind: "clip"`, `references[]` in @Image order: product images first
   when a swap exists, then the start frame, then internal shot frames), `slicing.md`; then
   `state.py "<run>" set stage=planning next_step=continuity` and `add-file 40-plan …`.

## Quality bar
- Durations are integers within the limits; the sum equals the original (or the confirmed segments) ± 1 s.
- No clip boundary falls inside a spoken word or 0.3 s before a hard cut.
- Every referenced frame exists on disk with the exact name in `plan.json`.

## When evidence is missing
No `cuts.json` confidence values → treat every cut as confidence 1 and say so. No transcript → skip the
mid-word rule and note it. Never invent beats: if `beat-map.json` is missing, list shots only and flag it.
