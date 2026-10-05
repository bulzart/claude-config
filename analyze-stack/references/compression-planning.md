# Compression planning — Mode 3 algorithm and the A2 gate (`40-plan\compression-plan.md`)

Owner brief: "This is not a highlight reel of random moments and not a new video 'inspired by' the
original. It is the same story, concept, message, characters, setting, style, tone, humor and payoff,
told in less time, the way a skilled editor would re-cut a 4-minute video into 1:30 without losing the
point." NEVER write a prompt before A2 = Approve.

## 1. Inputs
`20-analysis\beat-map.md/.json` (scores S/V/X/Q, importance, role, anchor candidates), `narrative.md`,
`audio.md` (dead air, music structure), `10-measure\transcript.json` (word timestamps), `cuts.json`,
`30-decisions\answers.json`: Q3a target T, Q3b clip length L, Q3c equal/uneven, Q4a dialogue verbatim
vs paraphrase, Q4b ending kept vs adapted, Q4c anchors; `swap-map.md` if a swap was chosen.

## 2. Algorithm (step by step; every step leaves a table in the plan file)

1. **Beat map check**: beats tile the original with no gaps; each has scores; sum of durations = D.
2. **Budget**: `budget = T − Σ anchors`; reserve `hook_s = min(3, 0.08·T)` for the hook beat at 0 s and
   `payoff_s` = the original payoff/CTA beat duration (Q4b keep) or 60 % of it (Q4b adapt).
3. **Classify** every non-anchor beat (viral-analysis §4): KEEP (importance ≥ 3.5 or role ∈ hook,
   climax, payoff, cta), MERGE (2.0–3.4, same role as a neighbour → one combined beat with the best
   line and the best visual of the group), DROP (< 2.0 or role ∈ filler, repetition, detour, dead-air).
   Repetition rule: when the original repeats a beat with variation (3 examples of the same joke), keep
   the strongest one and mark the others `DROP (repetition of bXX)`.
4. **Fit to budget**: `Σ kept + Σ merged` must equal `budget` ± 1 s. Too long → demote the lowest-
   importance KEEP to MERGE, then the lowest MERGE to DROP, never touching hook/climax/payoff/anchors;
   too short → promote the highest DROP/MERGE back, in importance order. Each kept beat gets a
   `planned_s` = its original duration, or its speech duration + 0.5 s when compressed (a line cannot be
   spoken faster than the original: word timestamps give the minimum), or the physical process minimum
   (physics-rules §7).
5. **Order**: kept beats stay in ORIGINAL order; anchors stay at their beat-order position.
6. **Dialogue**: Q4a verbatim → only original lines, cut whole lines, quotable lines (Q ≥ 4) survive
   word for word; paraphrase → lines may be shortened/merged keeping meaning and tone, quotable lines
   still verbatim. Every line in the script cites its transcript time.
7. **Ending**: Q4b keep → the final beat/CTA is replicated exactly (its planned_s = original); adapt →
   the payoff is kept, may be shortened/reworded (paraphrase rule) but the same message.
8. **Storyboard + script** at T: one row per kept/merged beat with new time `00m00.00s–…`, source
   beats, visual (what is seen, from the original frames), dialogue, sound, product state (swap-map
   moments carried over), transition to the next row (hard cut / continuous).
9. **Split into clips**: L seconds each (equal, or snapped to storyboard-row boundaries when uneven is
   allowed); a row never straddles a clip boundary mid-sentence; each clip lists its rows; continuity
   handoff rows are generated for the continuity author.
10. **Success test** (written as a checklist with a yes/no per item and the evidence):
    - same story (log-line identical to narrative.md's), same message, same emotional arc (hook → … → payoff), same reasons to share (the viral mechanics list);
    - no invented plot, characters, products (other than the approved swap), settings, jokes or messaging;
    - no drift from the original context (same tone, humour, register);
    - the hook lands in the first `hook_s` seconds; the ending/payoff is preserved per Q4b;
    - every quotable line with Q ≥ 4 present (verbatim);
    - every anchor present exactly.
    Any "no" → revise before presenting; if impossible at T, recommend a longer or shorter T with the reason.
11. **A2 gate**: the main session asks A2 with `{target}`, `{kept beats}`, `{merged}`, `{dropped}`,
    `{hook_s}`, ending preserved yes/no, anchors list. "Approve" → planning continues (continuity sheet,
    style bible, feasibility). "Change — I will describe edits" → apply, re-run steps 4–10, re-ask A2.
    "Recommend a shorter target" → re-plan at the recommended length from the feasibility pass
    (mode-rules §6) and re-ask A2.

## 3. Output — `40-plan\compression-plan.md`

```markdown
# Compression plan — <run-id> · original 240.0 s → target 90 s · clips 6 × 15 s · anchors: 00m31.00s–00m36.00s
Log-line (from narrative.md): "…"
Budget: 90 s = anchors 5 s + hook 3 s + payoff 8 s + body 74 s

## Keep / merge / drop
| beat | source time | role | imp. | decision | planned_s | reason |
|---|---|---|---|---|---|---|
| b01 | 00m00.00s–00m02.10s | hook | 4.6 | KEEP | 2.1 | the hook; V=5 |
| b02 | 00m02.10s–00m09.80s | setup | 3.1 | MERGE→b02+b03 | 5.0 | both establish the premise; keep b03's line |
| b07 | 00m31.00s–00m36.00s | climax | 4.9 | ANCHOR | 5.0 | pinned by owner |
| b11 | 01m10.00s–01m22.00s | detour | 1.4 | DROP | 0 | side story about the dog; not needed for the message |
| b18 | 03m50.00s–04m00.00s | cta | 4.0 | KEEP | 8.0 | ending kept as is (Q4b) |
Totals: kept 9 (61 s) · merged 4→2 (13 s) · dropped 12 (166 s) · anchors 1 (5 s) · hook at 0–2.1 s · ending preserved: yes

## Compressed storyboard + script (90 s)
| # | new time | source beats | visual | dialogue (verbatim/paraphrased: tag) | sound | product | transition |
|---|---|---|---|---|---|---|---|
| 1 | 00m00.00s–00m02.10s | b01 | MCU, she lifts the bottle to camera | "okay this is the one everyone…" (verbatim, 00m00.30s) | room tone | P1 in right hand, label to camera | hard cut |
…

## Clip split (6 × 15 s)
| clip | new time | rows | start state | end state |
…

## Success test
| Test | Pass | Evidence |
|---|---|---|
| Same story / message | yes | log-line preserved; beats 1,4,7,9,18 carry it |
…

## Feasibility flags (for A3)
…
```

## 4. Quality bar
- Every DROP has a reason naming what it is (filler, repetition of bXX, detour, dead air).
- Nothing in the storyboard lacks a source beat id; no row says "new".
- planned_s never below the speech/physics minimum; the sum equals T ± 1 s.
- Quotable lines and anchors are verbatim (string-compare with transcript).
- The plan is readable by the owner in under 3 minutes: totals line + tables, no prose walls.
