# segment-selector — agent brief (Stage 4, Mode 2 best-segment replication; modes `propose` | `finalize`)

Load first: `LAYOUT.md`, `references\mode-rules.md` §2 (selection rules, A1), §6, §7,
`references\viral-analysis.md` §4, `seedance\SEEDANCE-SPEC.md` §2.1 (limits, read at run time).

## Purpose
`propose`: pick the strongest continuous segment(s) of the original that fit the target length (Q3a),
snapped to hard cuts, with reasons and a next-best alternative set, so the main session can ask A1.
`finalize`: after A1, turn the confirmed segment(s) into clip slices (like Mode 1) and write `plan.json`.

## Inputs
`20-analysis\beat-map.json` (scores, `mode2_proposal`), `narrative.md` §5, `10-measure\cuts.json`, `shots.json`,
`transcript.json`, `30-decisions\answers.json` (Q3a target, Q3b, Q3c; in `finalize` the A1 answer and any
owner timestamps), `swap-map.json`. Notes: mode; for `finalize` the confirmed segments `00m00.00s–00m31.40s, …`.

## Outputs
- `propose`: `40-plan\segments.md` with the proposal, the alternatives and the A1 placeholder text.
- `finalize`: `40-plan\segments.md` updated with "Confirmed: …", `40-plan\plan.json` (`mode: 2`), reference
  frames in `50-prompts\references\` (as the slicer brief §4), feasibility rows.

### `segments.md` skeleton
```markdown
# Segments — <run-id> · Mode 2 · target 30 s (Q3a) · original 62.40 s
## Proposal (A1)
| rank | window | dur | beats | Σ(importance×dur) | why (mechanics) | what is lost outside it |
| 1 | 00m00.00s–00m31.40s | 31.4 | b01–b07 | 118.2 | hook at 0 s (V5), the pour (X5), first punchline (Q4) | second joke b09, CTA b18 (moved: see note) |
A1 placeholders: {segments with timestamps} = "00m00.00s–00m31.40s"; {total} = 31; {why each} = "hook + pour + punchline; snapped to cuts 0.00/31.40"
## Alternatives (for "Show alternatives")
| rank | window | dur | beats | why |
## Confirmed (after A1)
window(s): … · source of change: owner timestamps 00m02.00s–00m32.00s snapped to 00m01.40s–00m31.40s (±0.5 s rule) | not snapped (owner values kept)
## Clip split (Q3b 15 s, Q3c equal) — same table as slicing.md
## Feasibility (for A3)
```

## Method (`propose`)
1. Candidate windows = every contiguous run of beats with duration ≤ T (target); rank by
   `Σ(importance × dur)`; demote windows whose first 3 s contain no beat with V ≥ 4 below any that do.
2. Snap window edges outward to the nearest hard cut (confidence ≥ 2) within ±1.5 s, never inside a
   spoken word; keep duration ≤ T + 1 s.
3. Multiple windows only when T ≥ 2 × the best single window and non-overlapping windows add ≥ 20 %
   to the score; then each join is a "hard cut: new setup" for the continuity sheet.
4. Write the proposal with reasons in mechanic names (viral-analysis §2) and what is lost; the
   next-best set as alternatives; the exact A1 placeholder strings.

## Method (`finalize`)
1. Take the confirmed window(s) (A1 "Confirm" → rank 1; "Change — I will give timestamps" → the owner's
   values, snapped to a cut only when within ±0.5 s, else kept as given; "Show alternatives" was handled
   by the main session, you receive the chosen set).
2. Slice each window like Mode 1 (slicer brief §2–§5: script or by hand, limits read from the spec,
   equal/uneven per Q3c, references extracted, feasibility computed).
3. Write `plan.json` (`mode: 2`, items reference source times inside the windows) and update `segments.md`;
   `state.py "<run>" set stage=planning next_step=continuity`.

## Quality bar
- The proposal never exceeds the target by more than 1 s and never starts mid-sentence.
- Reasons cite beat ids and scores; "what is lost" names beats, not vague content.

## When evidence is missing
Without a beat map, rank by shot cadence and dialogue density and say the ranking is weak. Never fill
A1 placeholders with approximations — the timestamps must be the snapped values you wrote.
