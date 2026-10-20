## 5. Strengths, weaknesses, failure modes

| Failure mode | Trigger | Mitigation |
|---|---|---|
| Prompt rejected or truncated | Long prompts (web limit 512 chars [SECONDARY]) | ≤ 500 chars; move style to `genre` |
| Character role swap | Two tagged characters in one action | Tag only characters that must be exact; hero first |
| Location drift across clips | No persistent location reference | Location Element or start frames from one location plate |
| Unwanted slow motion or dramatic ramping | Genre look plus no tempo cue | State "real-time speed, no slow motion"; `genre:"auto"` for everyday content |
| Dead air at the end | Too little action for the duration | Shorter duration, or an extra beat with an end state |
| Garbled signage | Legible text in the scene | Clean plate + post captions |

