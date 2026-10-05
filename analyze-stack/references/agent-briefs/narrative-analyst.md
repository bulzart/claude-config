# narrative-analyst — agent brief (Stage 2c; one agent, after the visual and audio analysts)

Load first: `LAYOUT.md`, `references\viral-analysis.md` (structure, mechanics checklist, beat scoring,
how scores feed the modes), `references\report-template.md` (§3–§6 — what the report needs from you),
`references\mode-rules.md` §2 and §6 (Mode 2 windows; recommendation rule), `references\compression-planning.md` §1.

## Purpose
Understand the video completely: what it is about, what is being told, the narrative structure
(hook, setup, escalation, climax, payoff/ending/CTA), the main frames and iconic moments, the key
lines, and why it went viral (hook, retention mechanics, emotional triggers, payoff). Produce the
scored beat map that Mode 2 and Mode 3 planning use, the anchor candidates for Q4c, the Mode 2
proposal for Q2m, and the duration recommendation for Q3a.

## Inputs
`20-analysis\visual.md`, `audio.md`, `entities.json`, `style-profile.md`, `10-measure\transcript.json`,
`shots.json`, `cuts.json`, `contact-sheets\`, `keyframes\shots\`, `measure-summary.md`.

## Outputs
`20-analysis\narrative.md`, `20-analysis\beat-map.md`, `20-analysis\beat-map.json`.

### `narrative.md` skeleton
```markdown
# Narrative + virality — <run-id>
Log-line (one sentence, what the video is and what it tells): …
Tone / humour / register: …
## 1. Narrative structure
| Beat | Time | What happens (visible + heard) | Function | Evidence |
| Hook | 00m00.00s–00m02.10s | … | stops the scroll because … | shot 1, kf shots\shot-01-first-00m00.00s.jpg, line 1 |
| Setup | … | Escalation | … | Climax | … | Payoff / ending / CTA | … |
## 2. Main frames and iconic moments
| id | time | frame | why it matters (mechanic) |
| I1 | 00m07.50s | 10-measure\keyframes\shots\shot-03-mid-00m07.50s.jpg | the pour + colour change — signature visual (X=5) |
## 3. Key lines
| time | speaker | line (verbatim) | why it matters |
## 4. Why it went viral
- Hook (first 1–3 s): type + evidence
- Retention mechanics: … (named from viral-analysis §2, each with evidence)
- Emotional triggers: …
- Payoff / reason to share: …
- Format signals: …
## 5. Mode 2 proposal (for Q2m): top window(s) by Σ(importance × dur), snapped to hard cuts
| rank | window | dur | beats | why | what is lost |
## 6. Duration recommendation (for Q3a) — realism beats length
recommended_s: 30 · reason: "keeps b01, b04–b07 and b18 (hook, pour, payoff) at their real speed; drops the two repeated jokes and the 12 s detour; every kept shot has ≤ 2 movers and one camera move"
alt_1: 45 s — adds the second joke (b09) and the walk-in (b12: handheld + two people: risky) · alt_2: 62 s (full length) — every shot, including the crowd shot b14 (4 people: unstable)
## 7. Feasibility cues per beat (people, simultaneous movers, liquids, small text, camera moves, high-burst actions)
## 8. Uncertainties
```

### `beat-map.md` / `beat-map.json`
Table exactly as `viral-analysis.md` §3 (columns id, start, end, dur, shot(s), what happens, dialogue,
S, V, X, Q, importance, role, anchor?). JSON:
```json
{"schema":"analyze-stack.beat-map/1","run_id":"…","duration_s":62.4,
 "beats":[{"id":"b01","start_s":0.0,"end_s":2.1,"dur_s":2.1,"shots":[1],"what":"she lifts the can to camera","dialogue":"okay this is the one everyone [keeps?] talking about","S":5,"V":5,"X":3,"Q":4,"importance":4.6,"role":"hook","anchor_candidate":true,"keyframe":"10-measure/keyframes/shots/shot-01-first-00m00.00s.jpg","feasibility":{"people":1,"movers":1,"liquid":false,"small_text":false,"camera_moves":0,"high_burst":false}}],
 "mode2_proposal":[{"rank":1,"start_s":0.0,"end_s":31.4,"dur_s":31.4,"beats":["b01","b07"],"why":"…","lost":"…"}],
 "recommendation":{"recommended_s":30,"reason":"…","alt_1_s":45,"alt_1_reason":"…","alt_2_s":62,"alt_2_reason":"…"},
 "anchor_candidates":[{"beat":"b04","start_s":6.2,"end_s":9.5,"what":"the pour","why":"signature visual X=5"}]}
```

## Method
1. Read `visual.md`, `audio.md` fully; then LOOK at every contact sheet and at each keyframe you cite
   (Read tool) — X scores and iconic moments are judged by looking, not by reading the shot table.
2. Build beats: smallest units a re-cut could keep or drop (1–6 s), aligned to cuts and/or sentences,
   tiling the whole duration with no gaps (sum = duration ± 0.05 s).
3. Score S, V, X, Q (0–5 integers) with the rubric; `importance = 0.40·S + 0.30·V + 0.20·X + 0.10·Q`;
   assign `role`; filler/repetition/detour/dead-air must have S ≤ 2; anchor candidate = V ≥ 4 or X ≥ 4.
4. Fill the five structure rows (a row may be "absent (0 s)" but never omitted), iconic moments, key lines
   (verbatim from `audio.md`), the mechanics checklist with evidence.
5. Mode 2 proposal: contiguous windows per `viral-analysis.md` §4 / `mode-rules.md` §2; include the
   next-best set for A1 "Show alternatives".
6. Duration recommendation: the shortest length at which every kept beat plays at real speed with ≤ 2
   simultaneous movers, ≤ 2 acting people, one camera move per shot, no small text, no high-burst action,
   and the hook + climax + payoff survive; explain in one sentence; give two alternatives with their
   one-line consequence. Feasibility cues per beat feed the planners' `feasibility[]`.

## Quality bar
- Every claim cites a time and a frame or line; "feels viral" is not evidence — name the mechanic.
- Quotable lines are string-identical to `audio.md`.
- The recommendation names which beats it keeps and which risk it removes.

## When evidence is missing
No speech → Q = 0 for every beat and "no speech" in §3. If a mechanic cannot be supported, write
"not observed". Never claim measured performance (views, retention) — only hypothesised function.
