## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Identity drift / face swap mid-clip | mixed reference sheet; small face area | headshot + full body, headshot first [OFFICIAL S3] |
| Twins / duplicated characters or objects | multi-view sheets; undefined subjects; pasted script | single-person images, labels at every mention, no-twin sentence, counts [OFFICIAL S3] |
| Wrong head count | >4 referenced people | group stills of ≤4 first [OFFICIAL S3] |
| Timing ignored / abnormal pacing | numeric timestamps | `Shot N`, natural pacing [OFFICIAL S3] |
| Jitter / instability | several camera moves in one shot | one move per shot [OFFICIAL S3] |
| **Dead space** | one sparse shot stretched over 15 s | 2–3 shots with one event each; shorter duration [INFERRED] |
| **Arbitrary slow motion / sudden speed changes** | vague "cinematic" wording; bursts | "real-time speed"; slow continuous actions with transitions [OFFICIAL S3; INFERRED] |
| **Unmotivated cuts** | long shot lists for a short clip | fewer shots; "fixed camera position" when continuous [OFFICIAL S3; INFERRED] |
| **Morphing** | fast rotations; single weak product view | multiple product views; slow rotation [OFFICIAL S3; INFERRED] |
| **Clothing changes** | wardrobe not tied to a reference | full-body reference + label reused per shot [OFFICIAL S3] |
| Unwanted subtitles / text | portrait frame; text in references | subtitle constraints, clean references, QA [OFFICIAL S3] |
| Foreign logo / watermark | references from other platforms | "Do not generate watermarks / Logos" [OFFICIAL S3] |
| Style drift toward live action | realistic references + stylised prompt | explicit style; pre-convert references [OFFICIAL S3] |
| Effect behaves wrongly | effect described only in text | effect reference clip [OFFICIAL S3] |
| Voice ≠ reference | vague timbre | describe timbre; keep lines' tone close [OFFICIAL S3] |
| Asset overload | all 9/3/3 slots used | 4–5 assets [OFFICIAL S3] |
| Element/image numbering confusion | Elements + `@ImageN` | one mechanism per call [INFERRED] |

