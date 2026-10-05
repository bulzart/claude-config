# compression-planner — agent brief (Stage 4, Mode 3 condensed remake; modes `plan` | `revise` | `replan-shorter`)

Load first: `LAYOUT.md`, `references\compression-planning.md` (the whole algorithm, output format, success
test, A2), `references\mode-rules.md` §3, §4 (anchors hybrid), §6, §7, `references\viral-analysis.md` §3–§4,
`references\physics-rules.md` §7 (minimum durations of physical processes), `seedance\SEEDANCE-SPEC.md` §2.1, and the
**Seedance 2.5 Director** bundle (read-only): `seedance\director\references\prompt-playbook.md` §2 ("preserve the
intended MEANS, not only the endpoint": a hand-operated action must not become automatic; several transfers must
not become one unexplained appearance; an instructional sequence must not become an aesthetic montage that omits
the operation) and §6 (budget time for preparation, contact, repeated operations, movement and settling; never
atomize ordinary motion; never introduce an ellipsis merely to skip a required action), `seedance\director\references\continuity-and-causality.md`
§4.3 (an intentional time jump / montage must be labelled and must not skip a required method).

## Purpose
Re-cut the whole story into the target length the way a skilled editor would: same story, concept,
message, characters, setting, style, tone, humour and payoff — not a highlight reel, not an "inspired
by" video. Produce the keep/merge/drop plan with reasons, the compressed storyboard + script, the clip
split with continuity handoffs, the success test, and the feasibility flags. NOTHING downstream is
written until the owner approves (A2).

## Inputs
`20-analysis\beat-map.json/.md`, `narrative.md`, `audio.md` (dead air, music structure), `10-measure\transcript.json`,
`cuts.json`, `shots.json`, `keyframes\shots\`, `30-decisions\answers.json` (Q3a T, Q3b L, Q3c, Q4a dialogue,
Q4b ending, Q4c anchors — as suggested candidates or the owner's `mm:ss–mm:ss` list), `swap-map.json`.
`revise`: the owner's described edits (Notes). `replan-shorter`: the recommended target from `narrative.md` §6.

## Outputs
`40-plan\compression-plan.md` (format: compression-planning.md §3), `40-plan\plan.json` (`mode: 3`,
`"approved": false` until the main session sets it after A2; items carry `beats[]` with per-beat source
times and `compressed: true|false`, anchor items `"anchor": true`), reference frames in `50-prompts\references\`
(start frame of each storyboard row's source beat), `40-plan\a2-summary.json`:
`{"target_s":90,"kept":9,"merged":4,"dropped":12,"hook_s":2.1,"ending_preserved":true,"anchors":["00m31.00s–00m36.00s"],"recommend_shorter_s":null|60,"reason":"…"}`.

## Method
Follow `compression-planning.md` §2 step by step; each step leaves its table in the plan file:
1. Beat-map check (tiling, scores, sum = D). 2. Budget with anchors, hook reserve, payoff reserve.
3. Classify KEEP / MERGE / DROP with the repetition rule. 4. Fit to budget with `planned_s` never below the
speech minimum (word timestamps) or the physical minimum (physics §7). 5. Original order; anchors at their
beat position, replicated exactly (Mode 1 slices of the anchor range). 6. Dialogue per Q4a (quotable Q ≥ 4
verbatim in both cases; every line cites its transcript time). 7. Ending per Q4b. 8. Storyboard + script at T
(LOOK at the keyframe of every kept beat before describing its visual). 9. Split into L-second clips
(Q3c equal/uneven; a row never straddles a clip boundary mid-sentence); handoff rows for the continuity
author. 10. Success test with yes/no + evidence; if any "no" is unfixable at T → `recommend_shorter_s`
(or longer) with the reason. 11. Feasibility flags (mode-rules §6).
`revise`: apply the owner's edits literally (beats they name, lines they want, target change), re-run
steps 4–10, keep a "Changes since round 1" list at the top. `replan-shorter`: T = the recommended length.

## Quality bar
- Every DROP names its kind (filler / repetition of bXX / detour / dead air); every storyboard row has
  a source beat id; nothing is "new".
- A MERGE never removes a method-critical step (acquire / transport / deposit / release, a mechanism being
  operated, a count the story depends on): merges compress waiting and repetition, never the operation itself;
  every declared time jump is labelled in the storyboard and lands on a cut.
- Σ planned_s = T ± 1 s; anchors and quotable lines are string-identical to the transcript.
- The A2 summary numbers equal the plan's totals line.

## When evidence is missing
If a physical process minimum is unknown, use physics §7 defaults and mark "estimate". If the target is
below the sum of hook + anchors + payoff minimums, do not force it — write the plan at the smallest
feasible T and set `recommend_shorter_s`/reason accordingly (the A2 option "Recommend a shorter target"
carries it).
