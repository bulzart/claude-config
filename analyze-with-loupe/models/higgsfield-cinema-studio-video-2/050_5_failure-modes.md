## 5. Failure modes
| Failure | Trigger | Mitigation |
|---|---|---|
| Unmotivated speed changes | `speedramp:"auto"` | `linear` by default |
| Shot plan ignores intent | `multi_shot_mode:"auto"` with vague beats | Explicit ordered beats, or separate clips |
| Output not 720×1280 | No resolution parameter | `conform` + `qc` |
| Character drift between clips | No shared reference | The same Element / hero frame source |

