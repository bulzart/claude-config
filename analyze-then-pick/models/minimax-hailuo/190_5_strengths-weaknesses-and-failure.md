## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Landscape output | text-to-video, or non-9:16 start frame [SECONDARY/OFFICIAL] | 9:16 start frame always (§2.6) |
| Request rejected / snapped | `"1080"` with 10 s; `"512"` with 2.3 variants or `end_image` [OFFICIAL/HF] | 1080 → 6 s; 512 drafts only |
| End frame ignored or error | `end_image` on 2.3 variants [OFFICIAL] | variant `minimax` |
| Fast variant fails on text-only | image-to-video only upstream [OFFICIAL] | attach `start_image` |
| Camera ignores intent | vague prose camera | bracket commands (≤3 per bracket) [OFFICIAL] |
| Last frame cropped | first/last sizes differ [OFFICIAL] | identical dimensions |
| Text/gibberish | text in frames or prompt | §3.11 |
| Expecting sound | silent model [INFERRED] | audio in post, or `minimax_h3` |
| Look differs between variants | mixing variants | one variant per sequence |

**AI-slop tendencies and prevention.** `atp.py qc` flags black and frozen spans; `atp.py trim` removes dead head/tail frames deterministically.

| slop tendency | prevention |
|---|---|
| Dead space | 6 s unless two actions need 10 s; the action should fill the clip [INFERRED] |
| Arbitrary slow motion / speed jumps | "at real-time speed", "one steady pace" [INFERRED] |
| Unmotivated cuts | none documented (single-shot model); keep one continuous action [INFERRED] |
| Camera drift | explicit `[Static shot]` or one command per clause [OFFICIAL syntax] |
| Morphing | avoid transformation verbs ("melt", "morph" — which Higgsfield's own examples promote) unless wanted [HF]; FLF anchors |
| Identity drift | clear start frame, moderate motion, 6 s close-ups [INFERRED] |
| Duplicated objects / clothing changes | "only one <object>"; "clothing unchanged" [INFERRED] |

