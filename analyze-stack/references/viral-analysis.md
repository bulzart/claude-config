# Viral analysis rules — narrative structure, viral mechanics, beat scoring (Stage 2c → `beat-map.md`)

Owner brief: "understand the video completely: what it is about, what is being told, the narrative
structure (hook, setup, escalation, climax, payoff or ending or CTA), the main frames and iconic
moments, the key lines of dialogue, and what made it viral and engaging (the hook, the retention
mechanics, the emotional triggers, the payoff)". Everything below is evidence-based: cite times, frames
and transcript lines; hypothesise function, never claim measured performance.

## 1. Narrative structure (every video gets all five rows, even if a row is 0.3 s or "absent")

| Beat | Definition | Evidence to cite |
|---|---|---|
| Hook | the first 1–3 s: what stops the scroll (visual, line, text overlay, sound) | first cut time, first spoken words, overlay text, first frame |
| Setup | who / where / what is promised; the premise or question | shots, lines |
| Escalation | the build: steps, complications, repetition with variation, tension | shot cadence, beat count |
| Climax | the peak: reveal, transformation, punchline, the "moment" | iconic frame(s) |
| Payoff / ending / CTA | the resolution, result, joke landing, call to action, loop back to the hook | last lines, end frame, on-screen CTA |

## 2. Viral mechanics checklist (write a line for each that applies, with evidence; "not observed" otherwise)

- **Hook type**: visual shock · bold claim · question · "POV:" framing · in-media-res action · text overlay promise · sound hook · pattern interrupt · face-to-camera address · product-in-hand at 0 s.
- **Retention mechanics**: open loop ("wait for it"), countdown / list, show-while-telling, escalating stakes, rapid cuts (≤ 1.5 s), transformation before/after, ASMR / satisfying process, reveal held back to the last seconds, on-screen progress, re-hook every 5–8 s, dialogue that asks a question.
- **Emotional triggers**: curiosity, surprise, satisfaction, relatability, humour, aspiration, disgust/shock, nostalgia, awe, tension/relief, tribal identity ("if you know you know").
- **Payoff / reason to share**: result shown, joke lands, useful takeaway, identity signal, "tag someone who…", loop-ability (end frame ≈ start frame).
- **Format signals**: POV, GRWM, taste test, unboxing, tutorial, skit, duet-bait, trend sound lip-sync, before/after, day-in-the-life, "things that…" list.

## 3. Beat map (`20-analysis\beat-map.md` + the same table as JSON in `beat-map.json`)

A beat = the smallest unit that a re-cut could keep or drop (typically 1–6 s, aligned to cuts and/or
sentences). Beats cover the whole timeline with no gaps.

```markdown
| id | start | end | dur | shot(s) | what happens (visible) | dialogue (verbatim) | S | V | X | Q | importance | role | anchor? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| b01 | 00m00.00s | 00m02.10s | 2.10 | 1 | she lifts the can to camera, label out | "okay this is the one everyone…" | 5 | 5 | 3 | 4 | 4.6 | hook | candidate |
```

Scoring rubric — four scores, each 0–5, integers:

| Score | Name | 0 | 3 | 5 |
|---|---|---|---|---|
| S | story-necessary | removable without loss | helps understanding | the story breaks without it |
| V | viral-trigger | none | a mild retention/emotional cue | the hook, the reveal, the punchline |
| X | signature-visual | generic | recognisable | the iconic frame people remember/screenshot |
| Q | quotable | no speech / filler | a good line | the line people repeat in comments |

`importance = 0.40·S + 0.30·V + 0.20·X + 0.10·Q` (one decimal). `role` ∈ hook · setup · escalation ·
climax · payoff · cta · filler · repetition · detour · dead-air. Filler/repetition/detour/dead-air beats
must have S ≤ 2. `anchor?` = `candidate` when V ≥ 4 or X ≥ 4 (these are the Q4c candidates).

## 4. How the scores feed the modes

- **Mode 1** ignores scores (everything is replicated); scores still inform the continuity sheet (which
  beats need exact framing).
- **Mode 2 (segment selection)**: candidate windows = every contiguous run of beats whose total
  duration ≤ target; rank by `sum(importance × dur)`; the top window must contain the hook beat or a
  beat with V ≥ 4 in its first 3 s, else it is re-ranked below one that does; up to 3 windows may be
  proposed when the owner's target allows several segments (see `mode-rules.md` §2).
- **Mode 3 (compression)**: kept = importance ≥ 3.5 or role ∈ {hook, climax, payoff, cta}; merged =
  2.0–3.4 with the same role as a neighbour; dropped = < 2.0 or role ∈ {filler, repetition, detour,
  dead-air} unless the owner pinned them as anchors (see `compression-planning.md`).
- **Anchors** (Q4c) are replicated exactly (source slice → clip, like Mode 1); everything around them is
  compressed.

## 5. Quality bar

- Every beat row cites at least one shot number; every hook/climax/payoff cites a keyframe path.
- Dialogue in the table is verbatim from `transcript.json`; uncertain words as `[word?]`.
- The narrative analyst LOOKS at the contact sheets and the cited keyframes (Read tool) before scoring X.
- No score is justified with "feels"; justify V/X with the mechanic name from §2.
- If speech is absent, Q = 0 everywhere and the report says "no speech".
