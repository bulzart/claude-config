## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Stretched or distorted subject | `aspect_ratio` differs from the start image [OFFICIAL] | Conform the frame to 9:16; request exactly 9:16 (classic) or omit it (1.5) |
| Wrong orientation on 1.5 | No aspect parameter; text or reference jobs [HF + INFERRED] | Mandatory 9:16 start frame; probe reference mode |
| 1080p rejected or ignored | References present [OFFICIAL][HF] | 720p always |
| Voice reference rejected | Gated custom audio [OFFICIAL] | Test; fall back to a described voice |
| Pseudo-text or subtitles | Text surfaces, dialogue [SECONDARY + INFERRED] | Clean start frame, blank surfaces, exclusion line, QC |
| Arbitrary slow motion (slop) | "slow motion" or quality-keyword prompts (xAI's own example requests it) [OFFICIAL example] | Leave it out; "real-time pace" |
| Dead space | Long duration (up to 15 s) for a short action [INFERRED] | Shortest duration that holds the action; add a second beat |
| Sudden speed changes | Several moves in one prompt [INFERRED] | One camera move; "steady" |
| Unmotivated cuts | Unspecified continuity [INFERRED] | "One continuous shot" |
| Morphing, duplicated objects, clothing changes, identity drift | Over-long clips, re-described frames, text-only people [INFERRED] | Start frame; motion-only prompt; "a single …"/"the same …"; restate wardrobe as unchanged |
| Unwanted sound | Always-on audio [OFFICIAL + HF] | Strip audio in post |

