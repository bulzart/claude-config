# Pipeline stage contract — /analyze-stack (the only command; every stage is run by the main session spawning agents with the Agent tool)

What is fixed is the PROCESS (stages, inputs, outputs, question order, file names). What is
free is the agent count: scale to video length, mode, clip count and swap (one analyst per
segment on long videos, one writer per clip, one QA agent per generated clip, …). Never
minimise agents for their own sake; never spawn them for their own sake either.

Every stage reads `state.json` and writes its outputs to the run folder before reporting.
The pipeline can resume from any stage: if the stage outputs already exist and
`state.json.stage` is past that stage, skip it unless the owner asks to redo it.

Shared inputs loaded read-only by every run: `LAYOUT.md`, `references\*.md`,
`seedance\SEEDANCE-SPEC.md` (never modified at run time), `product-library\index.json`.

| # | Stage | Who runs it | Inputs | Outputs (run folder) |
|---|---|---|---|---|
| 0 | Intake | main session | video path or link dropped in chat; optional product images | `00-input\source.mp4` (copy; links downloaded with yt-dlp), `00-input\input.json`, `state.json` (stage=intake) |
| 1 | Measure (scripts only) | one agent per script group, or the main session running `tools\measure_all.py` | `00-input\source.mp4` | `10-measure\probe.json, cuts.json, shots.json, keyframes\, contact-sheets\, audio.wav, transcript.json/.srt, ocr.json, audio-features.json, measure-summary.md` |
| 2a | Visual analysis | 1 analyst per ≤60 s segment (long videos: several in parallel, boundaries reconciled) | contact sheets, keyframes, shots.json, ocr.json | `20-analysis\visual.md` (shot table, people & setups, spatial layout, entity & product inventory, camera, lighting), `entities.json`, `style-profile.md` |
| 2b | Audio analysis | 1 agent | audio.wav, transcript, audio-features.json | `20-analysis\audio.md` (reconciled transcript with speakers, music, SFX, sync points, dead air, timing) |
| 2c | Narrative + virality | 1 agent (after 2a/2b) | visual.md, audio.md, transcript | `20-analysis\narrative.md`, `beat-map.md` (timestamped beats with importance scores: story-necessary / viral trigger / signature visual), iconic moments, key lines, viral mechanics (hook, retention, emotional triggers, payoff) |
| 2d | Reconcile → report | main session | 2a–2c outputs | `20-analysis\report.md` shown to the owner (specs, structure, style, entities, viral breakdown) |
| 3 | Questions | main session, `references\questions.md` verbatim order: Q1 product → Q1a/Q1b → Q2 approach (replicate \| Seedance 2.5 edit) → Q2e edit intent or Q2m mode → Q3a/b/c → Q4 (Mode 3) → Q5 style (replicate only) → Q6 platform | report.md, entities.json, SEEDANCE-SPEC / SEEDANCE-EDIT limits | `30-decisions\answers.json` |
| 3e | Edit intent (Seedance edit approach only) | main session (Q2e), then 3p + 3s below when a product is involved | answers, entities.json | `30-decisions\edit-intent.md` (what changes, what must stay exactly as filmed, per entity and per moment) |
| 3p | Product identification (swap only) | 1 agent (samples → product library → web) | product images, answers | `30-decisions\product-spec.md` (identity + physical properties + behaviours), copy saved to `product-library\<slug>\spec.md` + images; Q1b confirmation |
| 3s | Swap & blend planning (swap only) | 1 agent per ≤60 s segment where the product appears + 1 reconciler | product-spec.md, visual.md, audio.md, beat-map.md | `30-decisions\swap-map.md`: every moment the original product appears (timestamp, shot, what changes visually / audibly / in text and dialogue), colour-mixing results, container/grip differences, sound changes, brand/text removals |
| 4 | Planning | Mode 1: slicer (1 agent); Mode 2: segment selector (1 agent) + owner confirmation A1; Mode 3: compression planner (1 agent) + owner approval A2; then continuity author (1 agent) and, if style swapped, style-bible author (1 agent) | beat-map, answers, swap-map, style-profile, SEEDANCE-SPEC | `40-plan\slicing.md` / `segments.md` / `compression-plan.md`, `continuity-sheet.md` (fixed spatial layout, characters, wardrobe, product, lighting, camera language, per-clip start/end states), `style-bible.md`, `plan.json` (clip list: number, source time slice, duration, beats, references) |
| 4e | Edit segmenting (Seedance edit approach) | slicer (1 agent, uses `tools\slicer.py`) + continuity author | probe.json, shots.json, answers (Q3b/Q3c), SEEDANCE-EDIT input limits | `40-plan\edit-segments.md` + `plan.json` (source time slices ≤ the video-input limit, snapped to cuts when uneven is allowed), `00-input\segments\seg-NN.mp4` (cut with ffmpeg, stream copy where possible), `continuity-sheet.md` |
| 5 | Prompt writing | 1 writer per clip, in parallel | plan.json, continuity-sheet, swap-map, style-bible, SEEDANCE-SPEC, `references\prompt-template.md`, physics/blending/continuity rules | `50-prompts\clip-NN.md` + `prompts.json`; each prompt: start state → second-by-second timeline → end state, camera, lighting, audio/dialogue, on-screen text logic, references cited with the spec syntax, negative list, continuity handoff |
| 5e | Edit-prompt writing (Seedance edit approach) | 1 writer per source segment, in parallel | plan.json, edit-intent.md, swap-map, continuity-sheet, SEEDANCE-EDIT, `references\edit-prompt-template.md`, physics/blending/continuity rules | `50-prompts\edit-NN.md` + `prompts.json`; each edit prompt: the source segment cited with the spec syntax, product/reference images cited, what changes (every visual/audio/text consequence from the swap map), what stays exactly as filmed, timing anchored to the segment's own seconds, continuity handoff to the next segment |
| 6 | Anomaly check | 1 checker per lens (physics, space/layout, timing, continuity, product consistency, spec compliance) over ALL prompts together, then fixes routed to the affected writers; loop until clean (max 3 rounds, then escalate to the owner) | all clip prompts | `60-qa\anomaly-check.md`, `fixes-round-N.md`, `qa.json` |
| 7 | Deliverables | main session | everything | `70-deliverables\DELIVERABLES.md` (index + summary), `prompts-final.md` (numbered clips or edit segments, durations, reference attachments, continuity notes), `references\` bundle (product images, cited frames, and for the edit approach the sliced source segments), `state.json` (stage=awaiting-generation, next_step) |
| 7g | Generation gate + generation (OPTIONAL, both approaches) | main session asks G1 (with cost estimate and balance). "Generate all now" / "test clip 1": a generator agent uploads every attachment the prompts cite (product samples, cited frames, source segments) through the Higgsfield MCP, submits each prompt with the parameters from the spec notes (model id, duration, aspect, resolution, seed reuse), polls jobs, downloads outputs to `80-generated\clip-NN.mp4`, writes `manifest.json`. "I will generate myself": the pipeline stops after the deliverables, the owner generates elsewhere and drops the clips back later (Stage 8). | prompts-final.md, references bundle, SEEDANCE-SPEC / SEEDANCE-EDIT platform parameters, `research\higgsfield-mcp.md` | `75-generation\uploads.json` (local path → media id), `jobs.json` (prompt → job id, params, status, cost), `generation-log.md`; `80-generated\clip-NN.mp4` + `manifest.json`; `state.json` (stage=generated) |
| 8 | Post-gen intake | main session | generated clips dropped in chat (only when the owner generated elsewhere) | `80-generated\clip-NN.mp4` + `manifest.json`; question P1 mapping |
| 8q | Edit gate | main session asks P0 after clip QA (9a): edit now / regenerate flagged / stop | clip-qa.md | `state.json` (stage=awaiting-edit-decision → editing or done) |
| 9a | Clip QA | 1 agent per generated clip | clip, its prompt, neighbours' end/start states | `90-postgen\clip-qa.md`, `fix-prompts.md` |
| 9b | Trend research | 1 agent (sources per `research\trend-sources.md`) | niche, platform, date | `90-postgen\trend-brief.md` (format: `references\trend-brief-template.md`); question P3 |
| 9c | Edit + render (in CapCut) | 1 agent (edit plan) + the CapCut draft builder + the `capcut` MCP (refine in place; capcut-cli repair after every save; direct capcut-cli path when the MCP is absent) + optional OTIO / Descript exports (P2) + ffmpeg renderer | clips, clip-qa, trend-brief, answers P2/P3 | `90-postgen\edit-plan.json`, the registered CapCut draft `<run-id>` (editable in the app; copy in `project\capcut\`), `render\final.mp4`, `overlays.ass` (hook text / callouts / end card only — NEVER speech captions or subtitles) |
| 9d | Final check | 1 agent | final.mp4, edit-plan | `90-postgen\final-check.md`; `state.json` (stage=done or re-edit) |

## Execution

Every stage is run by the main session of `/analyze-stack`, which spawns the stage's agents with the
Agent tool (independent agents in one message so they run in parallel; dependent agents once their
inputs exist). The question stages and every gate (Q1–Q6, A1–A3, G1, P0–P3) stay in the main
session. There is no other engine.

Every agent is spawned from its brief in `references\agent-briefs\*.md` (one file per role:
measurer, visual-analyst, audio-analyst, narrative-analyst, product-identifier, swap-planner,
slicer, segment-selector, compression-planner, edit-segmenter, continuity-author,
style-bible-author, prompt-writer, edit-prompt-writer, anomaly-checker, generator, clip-qa,
trend-researcher, editor, final-checker) with the same thin launch prompt
(`references\agent-briefs\LAUNCH-PROMPT.md`): role name, absolute path of the brief to read
first, run folder, stage inputs (file paths), expected output files, and any owner answers the
stage needs. The agent reads its brief and does the work; the main session adds no instructions
of its own beyond that template.

## Non-negotiable rules

1. Files first: every agent writes its output file(s) before returning; chat is a summary.
2. Questions are asked only by the main session, verbatim from `references\questions.md`.
3. `seedance\SEEDANCE-SPEC.md` is read-only at run time.
4. The product library is updated whenever a product is identified/confirmed.
5. No logos, labels, watermarks or brand mentions of the original product may remain in any
   prompt when a swap was chosen (checked by the product-consistency lens in Stage 6).
6. Realism over length: recommend a shorter target when that is what keeps every shot feasible.
7. Every clip prompt carries: start state, second-by-second timeline, end state, camera, light,
   audio, references (spec syntax), negatives, continuity handoff to the next clip.
8. `state.json` is updated at the end of every stage with `stage`, `next_step`, and the file index.
9. Speech captions / subtitles are NEVER planted into the edited video — not burned in, not as a
   caption track in the editable project. The owner adds them afterwards with a separate caption
   tool. The edit may still add non-speech text: hook text overlays, callouts, end cards,
   stickers. The measurement transcript (`10-measure\transcript.srt`) may be handed over as a
   sidecar file for that external tool, never rendered.
10. Higgsfield MCP is OPTIONAL per run. Nothing is generated or spent before the owner answers G1
    with the cost estimate in front of them. If the owner declines, the deliverables (prompts +
    reference bundle + sliced source segments for the edit approach) are the end of the run until
    clips are dropped back. If the owner accepts, the generator attaches everything the prompts
    cite (enhanced prompt text, product samples, cited frames, source segments) and never submits
    more clips than confirmed. Editing afterwards happens only when P0 = "Edit now".
11. The Seedance 2.5 edit approach uses the same blending, physics, continuity and anomaly rules as
    replication; its prompts describe what changes AND what must stay exactly as filmed.
