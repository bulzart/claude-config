## 1. The question (`awl-start` step 5d)

Print this table in chat, every row, with one line under it: "At every level every second of every video is sampled, every cut keeps
its last and first frame, the first second is dense, no frame or video is made smaller, and QC and Loupe check every video exactly as
always."

| setting | Low | Medium | High | XHigh | Max |
|---|---|---|---|---|---|
| references, frames per second | 2 | 3 | 4 | 5 | 5 |
| around motion and in the first second | 6 | 8 | 10 | 10 | 10 |
| motion peaks densified per reference (±0.5 s each) | 4 | 5 | 6 | 8 | 8 |
| close-ups an analyst may add per reference | 2 | 4 | 6 | 8 | no cap |
| production agents at once | 2 | 3 | 4 | 5 | 5 |
| pilot video first, from this many videos | 2 | 3 | 5 | 5 | 5 |

Max is the pipeline's settings before this choice existed. Then ask with AskUserQuestion, header "Effort", "How densely should this run
analyse the references, and how fast should it produce? Lower levels use fewer frames and tokens. (XHigh, or your own numbers: in
Other.)", none marked as recommended, with four options (the question takes at most four, so XHigh is answered through Other, as the
model menu does with its table):

- **"Low"**: "The Low column: the fewest frames and tokens, 2 agents at once, a pilot from 2 videos."
- **"Medium"**: "The Medium column."
- **"High"**: "The High column."
- **"Max"**: "The settings before this choice existed: the most frames and tokens."

Other: "XHigh", or the user's own numbers ("references 4 fps, 3 agents"): take the nearest level and pass the numbers as the options of
`T effort` (`--analysis-fps`, `--analysis-dense-fps`, `--motion-peaks`, `--densify-ranges`, `--max-agents`, `--pilot-from`); a value
outside its bounds (§2) is held to them, and the user is told in one line. `$ARGUMENTS` with `effort low|medium|high|xhigh|max` answers
the question. Store it in step 6: `T effort --run RUN --level <level> [the user's numbers]`. A run without the key keeps the settings it
was planned with (max) and is never asked; `T effort --run RUN --level …` changes a run's level at any time, and the next prep or spawn
uses it.

