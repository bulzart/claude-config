## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Multi-shot request returns one shot | upstream `shot_type` default `single` [OFFICIAL] | single continuous shots; test before relying on cuts |
| Prompt tail ignored | >1,500 characters truncated [OFFICIAL] | ≤220 words; exclusions early |
| Wrong person gets a line/action | pronouns, unclear tags, mixed reference order | tags only, one subject per reference, visual reminder |
| Reference bleed | group photos, cluttered references [OFFICIAL single-subject rule] | crop to one subject per file |
| 15 s fails/clamps with references | r2v 2–10 s [OFFICIAL] | 5 or 10 s |
| Unwanted soundtrack | audio on by default [OFFICIAL] | describe sound; strip locally |
| Text/gibberish, leaked overlays | text in prompt or references | §3.11 |
| Unclear first-frame behaviour | `image_references` routing unknown [HF silent] | test; strict frames on `wan2_7`/`wan3_0` |
| Lower overall fidelity | older generation [SECONDARY] | draft here, finish on a newer model |

**AI-slop tendencies and prevention.** `atp.py qc` flags black and frozen spans; `atp.py trim` removes dead head/tail frames deterministically.

| slop tendency | prevention |
|---|---|
| Dead space | 5 s unless the beats need 10 s; a visible change every 2–3 s [INFERRED] |
| Arbitrary slow motion / speed jumps | "at real-time speed", "steady pace" [INFERRED] |
| Unmotivated cuts | one continuous shot; upstream default `single` helps [OFFICIAL] |
| Morphing | "character2 keeps its exact shape"; no transformations [INFERRED] |
| Identity drift / swaps | one subject per reference; tags, never pronouns [OFFICIAL] |
| Duplicated objects | "only one character2 in the scene" [INFERRED] |
| Clothing changes | "clothing exactly as in the reference" [INFERRED] |

