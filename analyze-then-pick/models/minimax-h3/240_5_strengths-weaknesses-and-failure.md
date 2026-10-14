## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Unwanted typography, titles, labels | genre words, quoted strings, symbols, logo images | §3.11b |
| Intentional text misspelled | long or small text, several text events | 1–5 words, one per shot, 2K, QC; else post |
| Request rejected | frames mixed with references; T2V with `auto` [OFFICIAL] | one mode per call; `9:16` always |
| Panel layout reproduced | grid references [OFFICIAL] | standalone photos; declare storyboards |
| Wrong reference used for a role | ambiguous numbering (§3.7) | number + descriptor + explicit role |
| Source performer or overlays leak | motion clip without exclusion; Edit Mode context | "take only motion…"; QC after regeneration |
| Product recolored or reshaped | style words overriding product | "Never recolor"; geometry lock [OFFICIAL/INFERRED] |
| Timeline overrun/compression | beats exceed duration [OFFICIAL] | fit beats to 4–15 s |
| Stiff complex action | demanding performance [OFFICIAL] | simplify; consider another model |
| Unwanted music/voice | audio always on [OFFICIAL] | "Music: no background music"; strip locally |
| Draft ≠ final look | Max vs H3 are different models [INFERRED] | final check on `minimax_h3` |

**AI-slop tendencies and prevention.** `atp.py qc` flags black and frozen spans; `atp.py trim` removes dead head/tail frames deterministically.

| slop tendency | prevention |
|---|---|
| Dead space, empty openings | "Avoid fake tech decoration, mirrored white stages, and empty openings"; match the timeline to the duration [OFFICIAL] |
| Random flashes, particles, light effects | "Do not use meaningless white flashes, abstract particles, random light effects, or random cuts to fake premium motion" [OFFICIAL] |
| Unmotivated cuts / transitions | cut only for new information; transitions only when requested [OFFICIAL] |
| Arbitrary slow motion, speed jumps | "at normal real-time speed" for action; camera speed stated explicitly ("at slow speed") [OFFICIAL vocabulary / INFERRED] |
| Morphing, recoloring | geometry lock; "Never recolor the product body" [OFFICIAL/INFERRED] |
| Identity drift | stable subject labels and speaker IDs; "retains identity, hair, outfit" statements [OFFICIAL IR] |
| Duplicated objects | "only one <object> in the scene" [INFERRED] |
| Clothing changes | "keeps the same outfit in every shot" [INFERRED] |

