## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Garbled subtitles or captions | Dialogue, especially in quotation marks [SECONDARY][OFFICIAL] | Colon dialogue, fewer lines, clean-plate sentence, QC; Lite silent mode |
| Pseudo-text on props | Text-bearing surfaces [OFFICIAL] | Blank/unbranded surfaces; real text only via start frame |
| Unmotivated cuts or dramatic angles (slop) | Documented cinematic bias [OFFICIAL] | "One continuous shot, no cuts"; one named camera move; no editing vocabulary |
| Dead space (action ends early, clip idles) | 8 s default with a short action [INFERRED] | Pick 4/6 s, or give the action a beginning, middle and end across the duration ("keep clip length in mind" [OFFICIAL]) |
| Arbitrary slow motion | "Cinematic/epic" wording without a pace [INFERRED] | "real-time pace"; avoid "slow-motion" unless wanted [OFFICIAL vocabulary] |
| Sudden speed changes | Mixed pace words, several moves [INFERRED] | One camera move at one speed; "steady pace" |
| Morphing or geometry drift | Complex motion, rotation, occlusion [OFFICIAL model card] | Camera moves over object spins; Lite end frame; clear silhouette |
| Identity drift or clothing changes | Cuts, occlusion, text-only people [INFERRED] | Start frame; single shot; identical description block [OFFICIAL] |
| Duplicated objects | Object mentioned several ways, or no count [INFERRED] | "a single …", then "the same …" consistently |
| Muddled multi-event clip | A→B→C chains [OFFICIAL] | One action per clip; at most 4 × 2 s timestamps |
| Re-imagined start frame | Prompt re-describes the image [OFFICIAL] | Motion-only prompt |
| Cropped subject | Start frame not 9:16 [OFFICIAL] | `atp.py conform` before upload |
| Garbled short speech | Crammed or very short lines [OFFICIAL] | Size lines to duration; visible speaker |
| Blocked generation | Audio/safety filters, minors, prominent people [OFFICIAL] | Rephrase audio; approved adult references only |

