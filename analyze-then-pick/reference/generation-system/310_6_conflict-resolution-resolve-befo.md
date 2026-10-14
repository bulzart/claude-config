## 6. Conflict resolution (resolve before sending)

| conflict | resolution |
|---|---|
| A camera move would hide the key interaction | Change the camera: a slower move, a different angle, or locked-off |
| The reference grip or placement does not fit the client asset | Adapt the interaction to the asset's real geometry |
| The replacement would produce wrong reflections or shadows | Restage it (angle, distance, surface) or specify the lighting explicitly |
| The sequence is too complex for the model's reliability | Simplify or split it into clips and keep the core mechanism. Fewer simultaneous movers, one camera move, real-time processes |
| The duration exceeds the model's range | Split per §3b (on the reference's cuts first, continuations only where the take is continuous). The model stays locked. Analyze Mode: a video over 30 s needs the user's permission first (command A7b) |
| Overlay text is needed | Always a clean plate plus CapCut text layers (Analyze Mode; `capcut-assembly.md`). Never model-rendered |
| The reference is wrong or weak for the need | Replace or improve the reference (new start frame, better asset view). Do not compensate with prompt text |
| A dedicated parameter exists (duration, aspect, audio, genre, mode, frames) | Use the parameter. Do not describe it only in prose |
| The house approach (the user's examples) differs from a default here | Follow the house approach (`20-analysis/house-approach.md`) and note it in the brief. It never overrides physics and logic, §9b, the permission rule or the house text style |

