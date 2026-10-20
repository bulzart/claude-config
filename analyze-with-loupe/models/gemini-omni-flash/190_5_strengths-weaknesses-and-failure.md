## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Unmotivated cuts (slop) | Multi-shot default [OFFICIAL] | "In a single continuous shot / No scene cuts" |
| Unintended changes in edits (untouched regions morph) | Long, descriptive edit prompts [OFFICIAL] | One operation plus "Keep everything else the same."; separate passes |
| Source text survives an edit | Not named (preserved by design) [OFFICIAL] | Dedicated removal pass naming every element (§3.11d) |
| Garbled or unwanted text | Text-inviting words; accuracy caveat [OFFICIAL] | Blank-surface clause, "No on-screen text…", colon dialogue; scene text via `says: "…"` |
| Morphing shapes, floating, extra limbs | Complex motion or insertion [OFFICIAL model card] | Higgsfield ANTI-SLOP line: "No robotic/CGI look, no floating, and no morphing shapes or extra limbs" [HF]; contact shadows |
| Dead space or arbitrary slow motion | Duration longer than the action; unpaced prompt [INFERRED] | Pick duration 3–10 to fit; timecodes; "real-time pace" |
| Sudden speed changes | Several moves or beats without timing [INFERRED] | Timecoded beats; one camera move |
| Identity drift or clothing changes | Default cuts, text-only people, stateless chains [INFERRED] | Single shot; references plus description; short chains |
| Duplicated objects | Object described twice, no count [INFERRED] | "a single …", then "the same …" |
| Reference shown as a literal frame | Ambiguous image role [OFFICIAL] | "should not be used as literal initial frames" |
| Wrong reference bound | Undocumented tag mapping [INFERRED] | Tag plus description; consistent `medias` order |
| Unwanted music or speech | Automatic soundtrack [OFFICIAL] | Describe audio; "No dialogue"; strip in post |
| Rejected request | Recognizable people, minors, region, edit source over 10 s [OFFICIAL] | Approved adult references; trim to ≤10 s |

