## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Untargeted captions/watermarks survive | text not named; Kling preserves detected text | name every element in a remove sentence; removal-only pass first [OFFICIAL S2, S7; INFERRED] |
| Replaced object gains pseudo-text | text-free instruction missing | "No new text…"; name the only permitted label [INFERRED] |
| Reference background or lighting bleeds in | unscoped `@Image` | "ignore the background and lighting of @Image1"; crop references [INFERRED] |
| Wrong object replaced | ambiguous target | position + colour + hand + action [INFERRED] |
| Original person visible in a reflection or later | replacement scoped to one moment | "must not appear in any frame" sentence [HF S8 pattern] |
| **Morphing** of the replacement | size/form-factor mismatch, fast motion | similar-size replacement; "one rigid object"; grip and size stated [INFERRED] |
| **Identity drift** of a replaced person | single low-quality reference | clean front-facing image (+ second angle) [INFERRED] |
| **Duplicated objects** | "add" without count/position | exact count and placement [INFERRED] |
| **Clothing changes** on untouched people | broad style/background edits | preservation sentence naming untouched people and clothing [INFERRED] |
| **Flicker / unmotivated re-framing** | "Generate another angle" or restyle | one operation per call; QA; avoid angle regeneration for continuity-critical shots [OFFICIAL S2; INFERRED] |
| Output audio missing or altered | edits don't regenerate audio | restore source track locally [OFFICIAL S1; INFERRED] |
| Rejected or truncated source | >10 s, >200 MB, >2K | trim to 3–10 s on hard cuts; transcode ≤2K [OFFICIAL S1] |
| Tags not bound | Higgsfield tag handling unknown | describe targets in words as well [INFERRED] |

