## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Line spoken by the wrong character | 3+ speakers; dialogue not tied to action | two speakers; action before each line; unique labels [OFFICIAL S1; SECONDARY S11] |
| Wrong language | Japanese/Korean/Spanish lines | only Chinese or English are voiced [OFFICIAL S1] |
| English words spelled out | capitals in English lines | lowercase English [OFFICIAL S1] |
| Audio doesn't match the image | prompt contradicts the start frame | keep text consistent with the image [OFFICIAL S1] |
| Busy, unstable result | "stacking too many elements" | one subject, one action, one camera move [OFFICIAL S1] |
| **Dead space** | 10 s with one small action | 5 s for one action; 10 s for dialogue or two beats [OFFICIAL S1; INFERRED] |
| **Arbitrary slow motion / speed changes** | no pacing words | "at natural real-time speed" [INFERRED] |
| **Unmotivated cuts** | multi-shot wording | one continuous shot per clip [HF S3] |
| **Morphing / identity drift / clothing change** | rotations to unseen sides; long motion | gentle motion; start frame; repeat the bracketed label and wardrobe [INFERRED] |
| **Duplicated objects** | object not counted | "one <object> only" [INFERRED] |
| Pseudo-text on signs/screens | visible text carriers | blank or out-of-frame carriers; exclusion line [INFERRED] |
| Caption/watermark from the start frame persists | uncleaned input | clean frames before upload [INFERRED] |
| Output not 720p | no resolution parameter | ffprobe + `atp.py conform` [INFERRED] |

