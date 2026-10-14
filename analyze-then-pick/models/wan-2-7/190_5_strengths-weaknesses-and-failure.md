## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Wrong output ratio | non-9:16 start frame [OFFICIAL] | 9:16 frames only (§2.6) |
| Unwanted music or voices | audio always generated [OFFICIAL] | describe the soundscape; "No background music."; strip locally |
| Audio cut off / silent tail | audio length ≠ `duration` [OFFICIAL] | match duration to audio |
| Gibberish text or subtitles | signage, screens, quoted non-dialogue text, text in the frame | §3.11 |
| Product warping | spins, extreme close moves | slow rotations, geometry sentence |
| Spatial distortion | wide orbits [OFFICIAL] | arcs ≤45°, slower camera |
| Muddled actions | too many actions per shot [OFFICIAL] | one or two actions per 3–5 s |
| Implausible FLF path | first/last frames too different [INFERRED] | compatible frames; describe the path |
| Lip-sync mismatch | exact-word expectations [OFFICIAL] | short lines; driving audio |
| Request rejected | `end_image` without `start_image` [OFFICIAL] | always pair |

**AI-slop tendencies and prevention.** `atp.py qc` flags black and frozen spans; `atp.py trim` removes dead head/tail frames deterministically.

| slop tendency | prevention |
|---|---|
| Dead space | shortest `duration` that fits the beats; one visible change every 2–3 s [INFERRED] |
| Arbitrary slow motion | "at real-time speed"; Alibaba's Wan 3.0 wording "No slow motion" [OFFICIAL Wan 3.0 / INFERRED transfer] |
| Sudden speed changes / abrupt stops | state pacing; "slows and comes to rest naturally"; or pin the end with `end_image` [INFERRED] |
| Unmotivated cuts | "Generate a single-shot video" [OFFICIAL] |
| Morphing | "keeps its exact shape throughout"; end frame as anchor [INFERRED] |
| Identity drift | clear start frame, moderate motion, shorter shots [INFERRED] |
| Duplicated objects | "only one <object> in the scene" [INFERRED] |
| Clothing changes | "clothing unchanged throughout" [INFERRED] |

