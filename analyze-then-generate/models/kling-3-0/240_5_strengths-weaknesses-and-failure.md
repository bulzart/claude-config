## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Expected cuts don't happen | shot labels without the multi-shot switch | continuous shot with time markers, or one clip per shot [OFFICIAL S1; HF S9] |
| **Unmotivated cuts** | ambiguous multi-beat prose (if server-side multi-shot engages) | "one continuous shot, no cuts" wording; one camera move per beat [INFERRED] |
| **Dead space / empty opening** | long duration with few beats; unpopulated scene description | one beat per 3–4 s; say who is visible at the start [SECONDARY S13; INFERRED] |
| **Arbitrary slow motion / speed changes** | "cinematic" moods; no pacing words | "real-time speed"; slow motion only where written [OFFICIAL S1 pattern; INFERRED] |
| **Identity drift / character swaps** | similar characters, pronouns, crowded frame | Elements per person, distinct wardrobe, anchored positions, unique labels [SECONDARY S13; OFFICIAL S4] |
| **Duplicated objects / extra characters** | vague headcount | exact counts ("one person, one bottle") [SECONDARY S13; INFERRED] |
| **Morphing** | fast orbits around products | product Element + slow moves + steady hero frame [OFFICIAL S1; INFERRED] |
| **Clothing changes** | wardrobe stated once in long prompts | Element or repeated wardrobe noun at each beat [INFERRED] |
| Line on the wrong speaker | dialogue not tied to action; 3+ speakers | action first, `Name (tone): "line"`, ≤2 speakers per beat [OFFICIAL S4; SECONDARY S13] |
| Caption/logo from the input frame persists | text in start frame or Element image | clean inputs; Kling preserves image text [OFFICIAL S1] |
| Unwanted words rendered | quoted strings; described signage | quotes only for dialogue; blank carriers [OFFICIAL S6; INFERRED] |
| English words mispronounced | capitals in English lines | lowercase English [OFFICIAL S4] |
| End frame ignored / unnatural morph | prompt contradicts end state | describe the transition toward the end frame [HF S9] |
| Turbo returns unwanted audio | no toggle | strip audio locally [INFERRED] |
| Motion Control output shorter than the clip | fast or complex motion | steady moderate motion, single continuous shot [OFFICIAL S18] |

