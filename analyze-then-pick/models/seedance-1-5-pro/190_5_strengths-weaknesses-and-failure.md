## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Lines on the wrong speaker | speakers not described distinctly | gender, age, clothing and an action per speaker before the line [OFFICIAL S1] |
| Flat or wrong delivery | line without delivery cues | "In a <emotion> state, with a <tone> and a <pace>, say: …" [OFFICIAL S1] |
| Unwanted music | BGM on by default | explicit music policy or `generate_audio:false` + post audio [OFFICIAL S1; INFERRED] |
| Spurious subtitles / pseudo-text | quoted strings, text in the start frame, portrait framing | clean frames, blank carriers, constraint sentence, QA [INFERRED; OFFICIAL S8] |
| **Dead space** | 12 s with one small action | 12 s only for 3–5 beats; otherwise 4 or 8 s [INFERRED] |
| **Arbitrary slow motion / speed jumps** | vague pacing | degree adverbs for every movement; "real-time speed" [OFFICIAL S1 pattern; INFERRED] |
| **Unmotivated cuts** | multi-sentence scene read as shots | "a single continuous shot" when no cuts are wanted; explicit "The shot cuts to…" when they are [OFFICIAL S1; INFERRED] |
| **Morphing / invented product sides** | fast rotation from one frontal frame | slow moves; end frame for the final pose [INFERRED] |
| **Identity drift / clothing change across clips** | new clip without a frame | chain last frame → `start_image`; identical description [INFERRED] |
| **Duplicated objects** | object not counted | "one <object> only" with its position [INFERRED] |
| Wrong duration | value other than 4/8/12 | request 4, 8 or 12 [HF S6] |
| Model unavailable | retired upstream | check `models_explore`; fall back to Seedance 2.0 [OFFICIAL S4] |

