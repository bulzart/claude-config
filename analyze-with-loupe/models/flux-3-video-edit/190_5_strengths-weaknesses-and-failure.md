## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Source captions, usernames, watermarks survive | Not named; untargeted text persists [OFFICIAL] | Removal pass naming each element (§3.11d); 9:16 reframe first |
| Text residue or ghosting after removal | Animated or stylized captions [INFERRED] | Second removal pass; local `delogo` for static marks; regenerate if it persists |
| Added element lands small or far | Unplaced add [OFFICIAL] | Size, look, landmark placement |
| Floating or sliding subject after a re-set | No contact surfaces [OFFICIAL] | Name the surfaces touched |
| Unrequested detail changes (morphing, slop) | Over-long or shot-describing prompt [OFFICIAL] | Shortest change-only prompt; "Keep <x> exactly as it is"; compare frames |
| Duplicated added objects | No count [INFERRED] | "a single …" |
| Replacement identity or clothing drift | Text-only replacement [OFFICIAL: no image input] | State kept wardrobe ("the same yellow apron…"); route approved identities elsewhere |
| Truncated dialogue | Line longer than the source speech [OFFICIAL] | Match word count and duration |
| Judder or timing mismatch | 30/60 fps source converted to 24 fps [OFFICIAL + INFERRED] | Conform and remux carefully; check duration |
| Rejected source | >15 s (BFL), <0.7 s, side <160 px, >50 MiB [OFFICIAL] | Trim and conform locally |
| Dependent edits conflict | Two dependent changes in one request [OFFICIAL] | Sequential passes |

Dead space, slow motion, speed changes and cuts are inherited from the source, not generated. Fix them in the source cut [INFERRED].

