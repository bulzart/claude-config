## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Corner watermark | upstream default `watermark:true` [OFFICIAL] | QC per §3.11e; reject and switch model |
| Generic faces, broken hands | long, over-detailed prompts [SECONDARY] | 20–60 words, one action |
| Steps merged into one motion | multi-step prose [SECONDARY] | one beat per clip or a short timecoded list |
| Wardrobe drift | fast action [SECONDARY] | slower action; shorter clips |
| Unwanted music or voices | audio always on [OFFICIAL] | describe audible sounds; "no music", "no dialogue" |
| Text or gibberish | text-bearing scenes or frames | §3.11 |
| Wrong format with start frame | frame not 9:16 [OFFICIAL] | 9:16 frames only (§2.6) |
| Weak camera adherence | camera cue buried mid-prompt [SECONDARY] | one camera cue last |

**AI-slop tendencies and prevention.** `atp.py qc` flags black and frozen spans; `atp.py trim` removes dead head/tail frames deterministically.

| slop tendency | prevention |
|---|---|
| Dead space / frozen background | 3–6 s for single actions; "subtle, natural movements" in the background [OFFICIAL example / INFERRED] |
| Arbitrary slow motion | don't request it (cues are unreliable) [SECONDARY]; "at real-time speed" [INFERRED] |
| Sudden speed changes | one action with one stated pace ("briskly", "slowly") [OFFICIAL style] |
| Unmotivated cuts / transitions | "one continuous shot"; timecodes only when cuts are wanted [INFERRED/SECONDARY] |
| Morphing | avoid "transforms/morphs" wording (official examples use it deliberately) [OFFICIAL/INFERRED] |
| Identity drift | short prompt, clear start frame [SECONDARY] |
| Duplicated objects | "only one <object>" [INFERRED] |
| Clothing changes | slower action; "clothing unchanged" [SECONDARY/INFERRED] |

