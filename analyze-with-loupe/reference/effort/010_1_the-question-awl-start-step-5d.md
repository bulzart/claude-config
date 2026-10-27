## 1. The question (`awl-start` step 5d)

Print this table in chat, every row, with one line under it: "At every level every second of every video is sampled, every cut keeps
its last and first frame, the first second is dense, and the frame-exact checks look at every frame."

| level | references (fps; around motion and in the first second) | close-ups per reference | QC storyboard, checkpoint sheets (fps) | extra full-resolution frames per QC pass |
|---|---|---|---|---|
| Low | 2; 6 | 2 | 4, 15 | 4 |
| Medium | 3; 8 | 4 | 4, 20 | 8 |
| High | 4; 10 | 6 | 5, 24 | 12 |
| XHigh | 5; 10 | 8 | 5, 30 | 16 |
| Max | 5; 10 | no cap | 5, 30 | no cap |

Max is the pipeline's rates before this choice existed. Then ask with AskUserQuestion, header "Effort", "How densely should this run
sample and inspect? Lower levels use fewer frames and tokens. (XHigh, or your own numbers: in Other.)", none marked as recommended, with
four options (the question takes at most four, so XHigh is answered through Other, as the model menu does with its table):

- **"Low"**: "2 fps references, 15 fps QC checkpoints, the smallest budgets. The fewest tokens."
- **"Medium"**: "3 fps references, 20 fps QC checkpoints, moderate budgets."
- **"High"**: "4 fps references, 24 fps QC checkpoints, larger budgets."
- **"Max"**: "5 fps references, 30 fps QC checkpoints, no budgets: the rates before this choice existed. The most tokens."

Other: "XHigh", or the user's own numbers ("references 4 fps, checkpoints 24 fps"): take the nearest level and pass the numbers as the
options of `T effort` (`--analysis-fps`, `--analysis-dense-fps`, `--densify-ranges`, `--qc-storyboard-fps`, `--qc-dense-fps`,
`--qc-frames`); a value below its floor (§2) is raised to it, and the user is told in one line. `$ARGUMENTS` with
`effort low|medium|high|xhigh|max` answers the question. Store it in step 6: `T effort --run RUN --level <level> [the user's numbers]`.
A run without the key keeps the rates it was planned with (max) and is never asked; `T effort --run RUN --level …` changes a run's level
at any time, and the next prep or QC pass uses it.

