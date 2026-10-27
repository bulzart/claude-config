## 1. The question (`awl-start` step 5d)

All five levels are offered every time (the user, 2026-10-27: "they need to be 5: low,medium,high,xhigh and max"). The question is asked
in plain chat, never with AskUserQuestion: a question dialog holds at most four options and hides the text printed above it, which is
how XHigh went missing. It is a message of its own, after the start's question dialogs, and the last thing in that turn: the table,
every row, the line under it and the numbered levels; then stop and wait for the reply.

| setting | Low | Medium | High | XHigh | Max |
|---|---|---|---|---|---|
| references, frames per second | 2 | 3 | 4 | 5 | 5 |
| around motion and in the first second | 6 | 8 | 10 | 10 | 10 |
| motion peaks densified per reference (±0.5 s each) | 4 | 5 | 6 | 8 | 8 |
| close-ups an analyst may add per reference | 2 | 4 | 6 | 8 | no cap |
| production agents at once | 2 | 3 | 4 | 5 | 5 |
| pilot video first, from this many videos | 2 | 3 | 5 | 5 | 5 |

"At every level every second of every video is sampled, every cut keeps its last and first frame, the first second is dense,
no frame or video is made smaller, and QC and Loupe check every video exactly as always."

**Effort level for this run? Reply with its number or its name, or with your own numbers ("references 4 fps, 3 agents").**

1. **Low**: the fewest frames and tokens: references at 2 fps, 2 agents at once, a pilot from 2 videos.
2. **Medium**: references at 3 fps, 3 agents at once, a pilot from 3 videos.
3. **High**: references at 4 fps, 4 agents at once, a pilot from 5 videos.
4. **XHigh**: the Max rates, with at most 8 close-ups per reference.
5. **Max**: the settings before this choice existed: the most frames and tokens.

None is marked as recommended and none is taken for the user: a reply that names no level is asked again. Own numbers: take the nearest
level and pass the numbers as the options of `T effort` (`--analysis-fps`, `--analysis-dense-fps`, `--motion-peaks`, `--densify-ranges`,
`--max-agents`, `--pilot-from`); a value outside its bounds (§2) is held to them, and the user is told in one line. `$ARGUMENTS` with
`effort low|medium|high|xhigh|max` answers the question. Store it in step 6: `T effort --run RUN --level <level> [the user's numbers]`.
`T new-run` writes `state.json → effort` empty (`null`) until then, and `T prep-all` and `T effort --run RUN` stop on an empty one, so a
skipped question can never run at rates the user did not pick. A run made before this choice has no key: it keeps the settings it was
planned with (max) and is never asked. `T effort --run RUN --level …` changes a run's level at any time; the next prep or spawn uses it.
