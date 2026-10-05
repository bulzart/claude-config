---
name: analyze-stack
description: Analyze a viral video (file or link) frame by frame and by audio, show the full report, then ask product swap → approach (replicate or Seedance 2.5 edit) → mode/edit intent → duration → style → platform and produce Seedance 2.5 prompts with anomaly checks; optionally generate on Higgsfield via MCP; when clips exist, QA them and, if asked, edit in an editable project and render. Use when the user runs /analyze-stack or drops a video and asks to replicate or edit it.
user-invocable: true
argument-hint: <video path or link> [product images...]
---

# /analyze-stack — viral sample → Seedance 2.5 prompts → (optional) generation → clip QA → (optional) edit

Engine: this file is the step-by-step procedure for the MAIN SESSION; every worker is spawned with the
**Agent** tool. `/analyze-stack` is the ONLY command: it never runs as a Workflow and never generates one
(owner decision, 2026-09-17 and 2026-09-19). Detailed rules live in the reference files named at each step —
load a file when its step is reached, not before. Questions are asked by the main session only, in the fixed
order, verbatim from `references\questions.md`.

## 0. Contract

| Item | Value |
|---|---|
| Stack home `STACK` | `C:\Users\Glaresquare1\.claude\analyze-stack\` — read `STACK\LAYOUT.md` first on every run |
| `REFS` / `BRIEFS` | `STACK\references\` / `STACK\references\agent-briefs\` |
| `SPEC` / `EDITSPEC` | `STACK\seedance\SEEDANCE-SPEC.md` / `STACK\seedance\SEEDANCE-EDIT.md` — **read-only**; every limit (clip seconds, resolutions, ratios, reference counts, edit input length, credits) is READ from them at run time, never assumed |
| `DIRECTOR` | `STACK\seedance\director\` — the owner-supplied **Seedance 2.5 Director** bundle (rev 2.1.0, from `seedance-2-5-agent-guide.zip`; installed 2026-09-19; **read-only**, never refreshed by a run). Its method governs HOW prompts are built and audited: `SKILL.md` §1–§7 (intent contract → world state → causal action plan → audit → compile → release gate), `references\prompt-playbook.md` §7–§8 (compile + release gate), `references\continuity-and-causality.md` §4–§5 (ledger, 15 anomaly categories, cross-cutting safeguards), `references\examples.md`, `references\provider-checks.md` §10 (per-operation checks), `references\quality-and-iteration.md` §12 (defect record), `assets\*.md` (ledger / prompt / review templates). Hard numbers (seconds, pixels, reference counts, syntax) still come from SPEC/EDITSPEC — SPEC §14 states the precedence and the cross-check |
| `CAPCUT` | CapCut 9.4 is THE editing app. Two access paths, both direct on this machine: (1) the **`capcut` MCP server** (user scope; tools `capcut_*`, discovered with `ToolSearch "capcut_read_timeline"` — never hard-code the prefix): read, clone, add video/image/audio/text/sticker, move/trim(ripple)/split/delete, props, filters (474), transitions (116), masks (9), keyframes, audio fades, mute, undo, validate, save (refuses while CapCut.exe runs or the draft changed on disk); env `CAPCUT_DRAFTS_DIR` = the live store, `CAPCUT_TEMPLATE_DRAFT` = `_analyze-stack-template` (text/audio/transition shapes); (2) the **direct path**: `TOOLS\edit\build_capcut_draft.py` (registered draft from `edit-plan.json`) + `capcut-cli 0.25.0` (`capcut register --apply --materials`, `sync-timelines --nested --apply`, `lint`, `export-timeline`, `add-text`, `transition`, `keyframe`). After EVERY `capcut_save`: run the three capcut-cli repair lines (§0.2) because the MCP leaves new media unregistered in `draft_meta_info.json` and writes no `Timelines\` mirror. MCP absent → the direct path alone is the whole CapCut layer. Never `capcut_transcribe` / `capcut_add_captions` (speech-caption rule) |
| `TOOLS` | `STACK\tools\` — the lines in §0.2 were validated against every script's `--help` on 2026-09-16; if `tools\README.md` / `tools\edit\README.md` exist and differ, the README wins and the difference goes to DELIVERABLES "Known risks" |
| `RUN` | `STACK\runs\<YYYYMMDD-HHMMSS-slug>\` — every stage writes files here, then updates `state.json` |
| Shell | Windows PowerShell 5.1; every command starts with `$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')`; chain with `;` only (no `&&`/`\|\|`); no colons in file names (`00m12.40s`) |
| Agents | Agent tool; `prompt` = `BRIEFS\LAUNCH-PROMPT.md` template filled verbatim (role, brief path, run dir, inputs, outputs, answers, notes); `description` = `"<role> — <notes>"`; independent agents are launched in ONE message (parallel); agents never ask questions and write files first |
| Questions | asked by the main session only, with **AskUserQuestion**: one question per call; `header`, `question`, `options[{label, description}]` copied verbatim from `REFS\questions.md` with `{…}` filled from run files; `multiSelect: true` only for P3; an "Other" free text is the answer. After EVERY answer: append `{"key":"Q1","question":"<verbatim>","answer":"<label or text>","at":"<iso>"}` to `RUN\30-decisions\answers.json` (`{"answers":[…]}`) and run `python TOOLS\state.py "<RUN>" set answers.Q1="<answer>"` before the next question |
| Principle | realism beats length: a clean 30 s output is worth more than 2 min with anomalies — recommend shorter/simpler whenever that keeps every shot physically feasible |

### 0.1 State (`REFS\deliverables.md` §3)
`python TOOLS\state.py "<RUN>" get` reads; `… set stage=<stage> next_step=<step> [approach=replicate|edit mode=1|2|3]`
writes; `… add-file <stage-dir> <path> …` indexes files. Stages in order: `intake → measured → analyzed →
questions → product → planning → prompts → qa → awaiting-generation → generating → generated →
awaiting-edit-decision → editing → done | re-edit`. `next_step` values are listed in `deliverables.md` §3.

### 0.2 Exact tool lines (B1/B4 scripts; `python` = Python 3.12 on PATH after the refresh)
| Purpose | Line |
|---|---|
| Intake | `python TOOLS\intake.py "<path-or-url>" [--slug <slug>] [--cookies-from-browser chrome]` → run dir = last stdout line |
| Measure | `python TOOLS\measure_all.py --run-dir "<RUN>" [--whisper-model small] [--language en]` (skips finished steps; `--redo` to repeat) |
| State | `python TOOLS\state.py "<RUN>" get \| set k=v … \| add-file <stage-dir> <paths>` |
| Slice | `python TOOLS\slicer.py --duration <D> --clip-seconds <L> --min-clip <MIN> --max-clip <MAX> [--uneven --shots "<RUN>\10-measure\shots.json"] [--start <s>] [--number-from <n>] --out "<RUN>\40-plan\plan-slices.json"` (MIN/MAX read from SPEC/EDITSPEC) |
| Cut segments (edit) | `python TOOLS\segment_source.py --run-dir "<RUN>" --plan "<RUN>\40-plan\plan-slices.json" [--reencode\|--copy]` → `00-input\segments\seg-NN.mp4` + `segments.json` |
| Frames of a clip | `python TOOLS\clip_frames.py "<clip.mp4>" --out "<dir>" [--fps 1]` → `first-*.jpg`, `last-*.jpg`, `f-*.jpg`, `sheet.jpg`, `frames.json` |
| Download | `python TOOLS\download.py "<url>" --out "<file.mp4>" --probe` |
| Join | `python TOOLS\join_clips.py --run-dir "<RUN>" --out "<RUN>\80-generated\joined.mp4"` or `--clips a.mp4 b.mp4 … --out …` (edit approach: explicit order incl. passthrough segments) |
| First edit plan | `python TOOLS\edit\plan_from_clips.py --run-dir "<RUN>" [--clip-qa "<RUN>\90-postgen\qa.json"] [--trend-brief "<RUN>\90-postgen\trend-brief.json"] [--manifest "<RUN>\80-generated\manifest.json"] --out "<RUN>\90-postgen\edit-plan.json" --name <run-id> [--platform tiktok\|reels\|shorts\|universal] [--max-duration <s>] [--cta "<text>"]` → draft `edit-plan.json` (kept clips, clean windows, cadence, hook/CTA from the brief) that the editor refines |
| Overlays / builders / render | `python TOOLS\edit\text_overlays.py "<plan>" --out "<RUN>\90-postgen\overlays.ass" --fonts-dir "<STACK>\tools\edit\fonts"` · `python TOOLS\edit\build_capcut_draft.py "<plan>" --name <run-id> [--no-register]` · `python TOOLS\edit\build_otio.py "<plan>" --out-dir "<RUN>\90-postgen\project\otio" --name final` · `python TOOLS\edit\render_ffmpeg.py "<plan>" --out "<RUN>\90-postgen\render\final-A.mp4" --overlays "<RUN>\90-postgen\overlays.ass" --verify` (plan schema: `TOOLS\edit\EDIT-PLAN.md`; Descript path: `TOOLS\edit\descript_bridge.md`) |
| Re-import an edited timeline | `python TOOLS\edit\reimport_otio.py "<edited .otio\|.xml\|.fcpxml\|.edl>" --plan "<RUN>\90-postgen\edit-plan.json" [--dry-run]` → trims/order written back into the plan (backup kept), then the render line again |
| CapCut repair after a save | `capcut register "<draft dir>" --apply --materials` ; `capcut sync-timelines "<draft dir>" --nested --apply` ; `capcut lint "<draft dir>" -H` (capcut-cli 0.25.0 on PATH via `%APPDATA%\npm`; all three refuse while CapCut.exe runs — never add `--force-write` on the live store). `capcut export-timeline "<draft dir>" --out "<RUN>\90-postgen\edited.otio" --captions skip` reads a re-saved draft back for the Re-import line |
| CapCut draft read-back (MCP) | `capcut_read_timeline {draft:"<name>"}` (tracks, segments, times, mute) — the first call of every edit and re-edit; `capcut_validate` before `capcut_save`; `capcut_discard` to drop a session |

## 1. Step 0 — Intake and routing (`REFS\pipeline-stages.md` row 0)

1. Parse the invocation / message: a video path (`.mp4 .mov .mkv .webm …`) or an `http(s)` link; optional
   product images (`.jpg .png .webp .heic`); optional run-id (`20260916-…`).
2. **Post-generation entry**: the message carries video files (or names generated clips / a Higgsfield
   generation) AND a run exists whose `state.json.stage` ∈ {`awaiting-generation`, `generating`, `generated`,
   `awaiting-edit-decision`} or stage `done` with `next_step` `P0` (the named run, else the newest such run under
   `STACK\runs\`) → go to Step 8 (§9).
   Several candidate runs → ask in plain chat which run (this is not a scripted question).
3. **Resume entry**: no new video, but a run-id was given or the newest run's `state.json` has a `next_step` → §10.
4. **New run**: run the Intake line (§0.2): copies/downloads to `RUN\00-input\source.mp4` (normalised to
   H.264/yuv420p), writes `input.json`, `state.json` (stage `intake`, next `measure`), `link.txt` for links.
   Copy any product images to `RUN\00-input\product-images\` (they still go through Q1a later).
   No video at all → ask in plain chat for the file or link, then stop.

## 2. Step 1 — Measure (scripts only; row 1)

Run the Measure line (§0.2) from the main session. For videos ≥ 3 min, or when a script fails, spawn ONE
`measurer` agent (`BRIEFS\measurer.md`) instead: it runs the scripts one by one, uses the ffmpeg fallbacks
from `research\miko-analysis.md` §4 for anything missing, LOOKS at the contact sheets, and writes the summary.
Required outputs in `RUN\10-measure\` (names as the scripts write them): `probe.json`, `cuts.json`, `shots.json`,
`keyframes.json` + `keyframes\shots\shot-NN-first|mid|last-<00m00.00s>.jpg` + `keyframes\sampled\t-<00m00.33s>.jpg`,
`contact-sheets\sheet-NN.jpg` + `contact-sheets\index.json` (sheet/cell → t/shot/frame), `audio.wav` + `audio-16k.wav`,
`transcript.json` (`has_speech`, `language`, `language_probability`, `segments[].words[]`) + `.srt` + `.txt`, `ocr.json`
(`spans[]`, `frames_text[]`, `brand_candidates[]`, `handles[]`, `hashtags[]`), `audio-features.json`, `visual-stats.json`,
`measure-summary.md` (§1–§10 written by the script). Verify each exists and is non-empty.
Then the **analysis-segment table** (not produced by the script): the main session (or the measurer agent) splits
the timeline into ≤ 60 s windows whose boundaries sit on hard cuts (`cuts.json` confidence ≥ 2, within ±5 s of
the equal split) and never inside a spoken word (`transcript.json`), writes `RUN\10-measure\analysis-segments.json`
(`{"segments":[{"no":1,"start_s":0.0,"end_s":31.4,"shots":[1,8],"sheets":["sheet-01","sheet-06"]}]}`) and appends the
same table as `## 11. Analysis segments` to `measure-summary.md`; a ≤ 60 s video is one segment. State `measured` → `analysis`.

## 3. Step 2 — Analysis agents → report (rows 2a–2d)

| Agent | Count | Brief | Inputs | Outputs |
|---|---|---|---|---|
| visual-analyst | one per row of `10-measure\analysis-segments.json`, in parallel; + one `reconcile` pass when > 1 | `BRIEFS\visual-analyst.md` | contact sheets + `index.json`, `keyframes\shots\` + `sampled\` + `keyframes.json`, shots/cuts/ocr/probe/visual-stats json, measure-summary | `20-analysis\visual.md`, `entities.json`, `style-profile.md` (segment files `-segNN` first) |
| audio-analyst | 1, parallel with the visual analysts | `BRIEFS\audio-analyst.md` | audio.wav, transcript, audio-features, cuts | `20-analysis\audio.md`, `audio.json` |
| narrative-analyst | 1, after both | `BRIEFS\narrative-analyst.md` | visual.md, audio.md, entities, transcript, keyframes | `20-analysis\narrative.md`, `beat-map.md`, `beat-map.json` (S/V/X/Q scores, importance, roles, Mode 2 proposal, duration recommendation, anchor candidates, feasibility cues) |

Then the main session reconciles into `RUN\20-analysis\report.md` using `REFS\report-template.md` (fixed
headings: specs; shot table + pacing; narrative structure hook/setup/escalation/climax/payoff-CTA; main frames
+ iconic moments with timestamps and contact-sheet refs; key lines; why it went viral: hook, retention
mechanics, emotional triggers, payoff; visual style + sub-style; setting/people/layout; audio; **numbered
entity & product inventory with screen time (§10, feeds Q1)**; disagreements). Analyst disagreements are
resolved in §11, never silently. SHOW THE WHOLE REPORT in chat (not a summary). State `analyzed` → `questions`.

## 4. Step 3 — Questions (row 3; `REFS\questions.md` verbatim; Q1 FIRST, before any other question)

Order: Q1 → (Q1a → Q1b) → Q2 → (Q2e | Q2m) → Q3a → Q3b → Q3c → (Q4a → Q4b → Q4c) → (Q5) → Q6. Skip a question
only when its condition is not met. Placeholders are never assumed; each comes from a run file:

| Q | Condition | Placeholders and what happens after the answer |
|---|---|---|
| **Q1** Product | always, right after the report | numbered list = report §10 rows `"{#}. {entity} — {what it is}, {where it appears}, {screen time}"`; options: 1–3 swappable entities → one `Replace {entity}` each; > 3 → the three with most screen time (the rest stay in the list, chosen via "Other" by number); last option always `Keep the video as it is` |
| **Q1a** Samples | a swap was chosen | `{list of library entries}` = `STACK\product-library\index.json` (`slug — brand name variant size`), or `library is empty`. After the answer: copy the dropped files/links into `RUN\00-input\product-images\` (+ `product-notes.txt` with any typed brand / product name / label text / variant / size / ID; wait for "done" when the owner is still attaching); Stage **3p**: spawn ONE `product-identifier` (`BRIEFS\product-identifier.md`; `REFS\product-library.md` lookup order samples → library → web by exact label/ID; `REFS\product-spec-template.md`; mode `identify`, or the chosen library slug) → `30-decisions\product-spec.md`, `product-spec.json`, `product-id-summary.json`, staged `product-library\<slug>\` (`confirmed: false`) |
| **Q1b** Confirm product | a swap was chosen; asked after identification | fill from `product-id-summary.json` (`{brand} {product name} {variant} {size}`, `{label text}`, `{id or "none found"}`, `{3–6 properties}`, `{source}`). `Yes, exact product` → set `"confirmed": true` in `product-library\index.json` and `Status: confirmed by owner (Q1b)` in both spec files (the library is updated on every confirmation). `Almost — I will correct details` → take the owner's text, re-spawn the identifier in mode `correct`, ask Q1b again. `No — look it up again` → mode `relookup` with the owner's details, ask Q1b again. Loop until `Yes` |
| **Q2** Approach | always | `{…}` = `"swapping <Q1 entity> for your product"` when a swap was chosen, else `"with the edits you describe"` |
| **Q2e** Edit intent | Q2 = Seedance 2.5 edit | `{"{entity} → your product" \| "no product swap chosen"}`. Then Stage **3e**: write `RUN\30-decisions\edit-intent.md` — what changes (per entity and per moment: product swap from the swap map; other changes from the owner's text: remove logos/text, colour, setting, restyle, replace another entity), what must stay exactly as filmed (people, motion, camera, lighting, audio, timing), audio change yes/no. If the intent names a product and Q1 was `Keep the video as it is` → re-ask Q1 for that entity, then Q1a → Q1b. The edit approach then asks Q3b → Q3c → Q6 (Q3a, Q4a–c, Q5 are skipped: a restyle is part of Q2e) |
| **Q2m** Mode | Q2 = replicate | `{duration}`, `{n_shots}` = report §1; `{max_clip_s}` = SPEC §2.1 maximum clip seconds; `{n_prompts_at_max}` = ceil(duration / max); `{proposed segments with timestamps and why}` = `beat-map.json.mode2_proposal[0]` |
| **Q3a** Target length | Mode 2 or Mode 3 | `{duration}` = report §1; `{recommended_s}`, `{reason}`, `{alt_1}`, `{alt_2}` and their one-line consequences = `beat-map.json.recommendation` — the shorter-target rule: the recommended value is the length at which every kept shot is physically feasible (≤ 2 simultaneous movers, ≤ 2 acting people, one camera move per shot, no small text, processes at real speed) |
| **Q3b** Clip length | all approaches | `{supported_clip_lengths}` and `{max_clip_s}` read at run time from SPEC §2.1 (replicate) or from EDITSPEC §2 (edit: the recommended maximum, because longer inputs reduce stability; larger values up to the hard limit are accepted via "Other" and the warning is written into the plan); the edit sentence `{"For the edit approach…" \| ""}`; `{target_or_original_duration}` = Q3a target (Mode 2/3) or the original duration (Mode 1 / edit); `{n}`, `{n_at_max}`, `{n_at_10}`, `{n_at_5}` = ceil(T / L). A value outside the spec limits is refused and Q3b re-asked. If `narrative.md` §7 flags risky beats, print ONE line before the question: `Recommendation: <L>s clips keep every shot feasible (see 20-analysis\narrative.md §6–7).` — the question text itself stays verbatim |
| **Q3c** Uneven clips | all approaches | none |
| **Q4a** Dialogue | Mode 3 | none |
| **Q4b** Ending | Mode 3 | none |
| **Q4c** Anchors | Mode 3 | candidates = `beat-map.json.anchor_candidates` as `t=mm:ss–mm:ss — what happens — why it matters`; `I will list anchors` → parse the owner's `mm:ss–mm:ss` list (snapped outward to cuts by the planner) |
| **Q5** Style | replicate only | `{style label}`, `{sub-style summary}` = report §7; `Swap to animation` → the follow-up `Which animation style?` (options `Anime`, `2D cartoon`, `3D animation`, `Sketch / drawing`; others via "Other": claymation, stop motion, pixel art, watercolour, comic) |
| **Q6** Platform | all approaches | none; `Other ratio` → the owner's ratio + platform become the aspect and platform of every later stage |

After Q6, when a swap was chosen → Stage **3s**: spawn `swap-planner` agents (`BRIEFS\swap-planner.md`;
`REFS\blending-rules.md`), one per ≤ 60 s segment where the product appears (`entities.json` appearances ×
the measure-summary segment table), in parallel, then one `reconcile` swap-planner → `30-decisions\swap-map.md`
+ `swap-map.json` (every moment the product appears: visual / audio / text / dialogue consequences, colour
results, grip, sounds, removals). Show the `needs-owner-decision` items in chat; they are folded into A3
(replication) or into `edit-intent.md` (edit). State `questions` → `planning` with `approach` and `mode` set.

## 5. Step 4 — Planning and approvals (rows 4, 4e; `REFS\mode-rules.md`)

| Branch | Agent(s) | Outputs | Gate |
|---|---|---|---|
| Mode 1 | `slicer` (`BRIEFS\slicer.md`; Slice line §0.2 → `plan-slices.json`, then the agent's `plan.json`) | `40-plan\slicing.md`, `plan.json`, start/shot frames in `50-prompts\references\`, `feasibility[]` | — |
| Mode 2 | `segment-selector` mode `propose` (`BRIEFS\segment-selector.md`) → **A1** → mode `finalize` | `40-plan\segments.md`, `plan.json`, frames | **A1** (`{segments with timestamps, total {total}s}`, `{why each}` from `segments.md`): `Confirm` → finalize rank 1; `Change — I will give timestamps` → finalize with the owner's timestamps; `Show alternatives` → print the alternatives table, ask A1 again |
| Mode 3 | `compression-planner` mode `plan` (`BRIEFS\compression-planner.md`; `REFS\compression-planning.md`; anchors from Q4c per mode-rules §4 — anchors replicated exactly, surroundings compressed) → **A2** | `40-plan\compression-plan.md` (beat map → importance → time budget → keep/merge/drop with reasons → compressed storyboard + script → clip split → success test), `plan.json` (`approved: false`), `a2-summary.json`, frames | **A2** (placeholders from `a2-summary.json`): `Approve` → set `plan.json.approved = true`; `Change — I will describe edits` → mode `revise`, ask A2 again; `Recommend a shorter target` → mode `replan-shorter`, ask A2 again. **No prompt is written before A2 = Approve** |
| Edit approach | `edit-segmenter` (`BRIEFS\edit-segmenter.md`; Slice line with MIN/MAX from EDITSPEC §2 → Cut-segments line §0.2 → the agent extracts `seg-NN-audio.mka` with ffmpeg, the script writes only the mp4 + `segments.json`) | `40-plan\edit-segments.md`, `plan.json` (passthrough marked), `00-input\segments\seg-NN.mp4` + `seg-NN-audio.mka` + `segments.json`, `seg-NN-start` frames, `feasibility[]` | — |

Then, in this order: `style-bible-author` (`BRIEFS\style-bible-author.md`; only when Q5 = swap →
`40-plan\style-bible.md`, one STYLE LINE for every prompt), then `continuity-author` (`BRIEFS\continuity-author.md`;
`REFS\continuity-rules.md` + `DIRECTOR\references\continuity-and-causality.md` §4 → `40-plan\continuity-sheet.md` + `.json`:
master layout, characters, product, props, wardrobe, lighting/camera language, audio bed, style line, per-clip
start/end states = handoffs, reference attachments in spec syntax, PLUS the director's long-range dependency
table (later use → required prior state → enabling event) and the cut/occlusion boundary table (a cut is not a
reset); references copied/extracted into `50-prompts\references\`).

Feasibility pre-check **A3**: if `plan.json.feasibility[]` is non-empty or swap-map `needs-owner-decision`
items exist → ask A3 (`{n}`, `{examples}`, the plan's recommendation: shorter target / simpler split / drop
shot X). `Apply recommendation` → re-run the planner with it (a shorter target replaces Q3a; a split makes
that clip uneven; a dropped shot is removed), then the continuity author again; `Proceed as planned` → the
items go to DELIVERABLES "Known risks". State `planning` → `prompts`.

## 6. Step 5 — Prompt writing (rows 5, 5e), all writers in parallel in one message

- Replicate: one `prompt-writer` per `plan.json` item (`BRIEFS\prompt-writer.md`; `REFS\prompt-template.md`,
  SPEC §3.5/§4/§5/§6/§12, `C:\Users\Glaresquare1\.claude\skills\sd25-pe\SKILL.md`, `DIRECTOR` SKILL.md §3–§5 +
  prompt-playbook §7–§8 + continuity-and-causality §4.2–§4.4, physics / blending / continuity rules; inputs: its
  plan item, its continuity row + the next row, swap-map, style bible or profile, its frames, its audio lines)
  → `50-prompts\clip-NN.md` (start state → second-by-second timeline → end state, camera, light, audio/dialogue,
  on-screen text logic, product invariants, references cited with the spec syntax, negatives, continuity
  handoff). Every essential action is expanded the director's way — preconditions → actor/mechanism →
  path/contact/transfer → observable consequence → updated state — and the writer re-reads the finished
  prompt through the director's release gate (intent/method, state/causality, feasibility, flow, contract,
  economy) before returning it.
- Edit: one `edit-prompt-writer` per non-passthrough segment (`BRIEFS\edit-prompt-writer.md`;
  `REFS\edit-prompt-template.md`, EDITSPEC §3–§7, sd25-pe editing template, `DIRECTOR` provider-checks §10
  "Edit" row (target, interval, protected content, dependent effects such as shadows/reflections/contact);
  inputs: its plan item, `edit-intent.md`, swap-map, continuity row, its segment file + frames) → `50-prompts\edit-NN.md` (source
  cited as `@Video1`, product images `@ImageN`, trigger word first, WHAT CHANGES timed to the segment's own
  seconds, WHAT STAYS EXACTLY AS FILMED, removals, negatives, `generate_audio false` + mux).
- When all return: the main session builds `50-prompts\prompts.json` (schema `REFS\prompt-template.md` §3;
  `prompt` = the `## Prompt` block verbatim, `references[]` in attachment order, platform parameters per item).
  State `prompts` → `anomaly-check`.

## 7. Step 6 — Anomaly check loop (row 6; `REFS\anomaly-checklist.md`)

1. Spawn SIX `anomaly-checker` agents in one message (`BRIEFS\anomaly-checker.md`; lenses L1 physics, L2
   space/layout, L3 timing, L4 continuity, L5 product consistency, L6 spec compliance; the edit approach adds
   ED01–ED04: stays-as-filmed completeness, no contradictory change, identical wording, complete removals),
   each over ALL prompts together → `60-qa\anomaly-L<n>-round-<N>.md`. Each lens also runs the director's
   anomaly categories mapped to it (`REFS\anomaly-checklist.md` §2b: identity/count, location/topology,
   custody/support, causality/knowledge, time/order, inventory/volume, solid geometry, mechanical function,
   force/motion, materials/phases, optics/visibility, body/environment, camera/edit, sound/emotion, production
   contract) with the director's severities (blocker → S3, major → S2, polish → S1).
2. Merge into `60-qa\anomaly-check.md` (round header with S3/S2/S1 counts, one table). Clean = zero S3 and
   zero S2 → write `60-qa\qa.json` (`clean: true`) → Step 7.
3. Not clean → `60-qa\fixes-round-<N>.md` grouped by clip → re-spawn ONLY the affected writers in mode `fix`
   (parallel) → rebuild `prompts.json` → re-run all six checkers (a fix in one clip can break its neighbour).
4. Max 3 rounds. Still not clean → the `## Escalation` section → ask **A3** with `{n}` = open S3+S2 findings
   and the recommendation (simpler split / shorter target / drop shot); `Apply recommendation` → back to
   Step 4 for the affected clips; `Proceed as planned` → open findings listed under "Known risks". State `qa`.

## 8. Step 7 — Deliverables, state, G1 gate, generation or hand-off (rows 7, 7g; `REFS\deliverables.md`, `REFS\generation-playbook.md`)

1. Write `RUN\70-deliverables\DELIVERABLES.md`: header line (source, duration, approach/mode, product, style,
   platform), result line, the **"What to generate, in what order, with which attachments"** table (`#`,
   item file, duration, mode, attachments in upload order → tags, continuity from/to; passthrough segments
   marked), the cost table (three resolutions), the files table, known risks. Write `prompts-final.md`
   (numbered items in generation order: duration, source slice, mode, aspect, resolution, audio flag, the
   attachments table, the prompt verbatim in a fenced block, the continuity note; edit segments add the
   source segment path and the mux instruction). Copy the reference bundle — product images, cited frames,
   motion slices, style refs, and for the edit approach `seg-NN.mp4` + `seg-NN-audio.mka` — into
   `70-deliverables\references\`. State `awaiting-generation`, `next_step: G1`. Chat summary ≤ 20 lines: result
   line, the first rows of the generate table + its path, the cost line, the paths, then G1.
2. **Cost estimate** (read-only calls only): `ToolSearch "select:mcp__higgsfield__balance,mcp__claude_ai_Higssfield__balance"`
   → whichever exists is the prefix `P` (never hard-coded); `P balance {}` → `{balance}`; rates from EDITSPEC §8 /
   `research\higgsfield-mcp.md` §A (credits per second per resolution × duration × count; edit segments by
   `ceil(source_s)`; passthrough = 0); preflight one representative item per (mode, duration, resolution) with
   `P generate_video {params:{…, get_cost:true}}` (submits nothing) — the preflight wins over the table.
   `{model id}` = `seedance_2_5` (SPEC §11.2), `{resolution}` = 1080p default, `{aspect}` = Q6 ratio or
   "source ratio (auto)" for edits. Total × 1.5 > balance → append "— exceeds 2/3 of the balance; a lower
   resolution or fewer clips is recommended" inside `{credits}`. MCP absent → `{balance}` = "Higgsfield MCP not
   connected (see research\higgsfield-mcp-install.md)"; only "I will generate myself" can then proceed.
3. Ask **G1**. Nothing is generated or spent before this answer.
   - `Generate all now` → ONE `generator` agent (`BRIEFS\generator.md`; mode `all`; Notes: prefix `P`,
     confirmed count = every non-passthrough item, resolution, chained yes/no) → uploads every cited attachment
     once (`media_upload` → presigned PUT → `media_confirm`; `75-generation\uploads.json`), submits each prompt
     with the right mode (`t2v` / `omni_reference` / `video_edit`) and the parameters from `prompts.json`
     (`jobs.json` written before polling), polls (`jobs_wait`), downloads (Download line §0.2) into
     `80-generated\clip-NN.mp4`, verifies with ffprobe, conforms + muxes edit segments (`generate_audio false`
     → source audio back) and joins them (Join line), writes `manifest.json`, `generation-log.md` (estimated vs
     charged from `transactions`); never more clips than confirmed. State `generated` → continue to §9.2.
   - `Generate clip 1 first as a test` → generator mode `test` (item 1 only) → show the test clip's `sheet.jpg`
     path; apply any prompt change the owner asks for (writer `fix` + the six checkers); re-ask G1 with `{n}` =
     remaining items and the updated cost (`next_step: G1-remaining`).
   - `I will generate myself` → write `70-deliverables\GENERATE-YOURSELF.md` (per item: model, mode, params,
     attachments to upload in order, prompt text verbatim; playbook §5), state `next_step: drop-clips`, STOP.
     The run resumes when the owner drops the clips back (§9.1).

## 9. Step 8 — Post-generation (rows 8, 8q, 9a–9d; `REFS\post-generation-playbook.md`)

1. **Entry (row 8)**: (a) continuation after the generator — `manifest.json` exists with `mapping_source:
   "manifest"` → no P1; (b) owner-dropped clips → copy them into `RUN\80-generated\` (never edit in place),
   ffprobe each, map to prompt numbers by the playbook §1 precedence (owner statement → number in the file
   name → mtime order), flag `duration_mismatch` beyond ±20 %, write `manifest.json`, ask **P1** (`{n}`, list
   with durations, `{mapping}`); `No — I will give the order` → apply the owner's order, rewrite the manifest.
   Clips arriving in several drops: repeat until every prompt has a clip or the owner says the set is complete
   (missing ones are `MISSING`). State `generated`, `next_step: clip-qa`.
2. **9a clip QA**: one `clip-qa` agent per clip in parallel (`BRIEFS\clip-qa.md`; `REFS\clip-qa-template.md`,
   `REFS\fix-prompt-template.md`, `DIRECTOR` quality-and-iteration §12 defect record + `assets\review-record.md`
   pass/fail/unknown discipline; Frames line §0.2) → `90-postgen\qa\clip-NN\{qa.md, qa.json, fix.md, frames}`;
   merge into `90-postgen\clip-qa.md`, `qa.json`, `fix-prompts.md`. State `awaiting-edit-decision`, `next_step: P0`.
3. **P0** (row 8q): `{n_ok}` = S0/S1 clips, `{n_flag}` = S2+ or missing, `{one-line summary}` from `clip-qa.md`.
   `Edit now` → §9.4. `Regenerate flagged clips first` → re-ask **G1** for the flagged set (`{n}` = flagged
   count, cost re-estimated; `I will generate myself` → append the fix prompts to GENERATE-YOURSELF.md and stop)
   → generator mode `regenerate` (fix prompts from `fix-prompts.md`) → clip QA again for those clips and their
   neighbours → P0 again. `Stop here — clips are in 80-generated` → state `done`, `next_step: P0` (re-asked on return).
4. **9b trend research**: ONE `trend-researcher` (`BRIEFS\trend-researcher.md`; `research\trend-sources.md`,
   `REFS\trend-brief-template.md`) → `90-postgen\trend-brief.md` + `.json`. Then ask **P2** (edit target), then
   **P3** (boosts; `{niche}`, `{platform}`, `{date}`, `{3-line summary}` = the brief's top three recommendations;
   multi-select). Captions are never offered, recommended or applied.
5. **9c edit + render — in CapCut**: ONE `editor` agent (`BRIEFS\editor.md`; playbook §3–§6; `TOOLS\edit\EDIT-PLAN.md`,
   `TOOLS\edit\descript_bridge.md`) → first the "First edit plan" line (§0.2) drafts the plan from `manifest.json` +
   `qa.json` + `trend-brief.json`, then the editor refines `90-postgen\edit-plan.json` (schema v2; no captions block — the loader refuses one),
   `overlays.ass` (hook text / callouts / end card ONLY), then the CapCut project: (a) `build_capcut_draft.py` writes the
   registered draft `<run-id>` into the live store (only while CapCut.exe is closed; else `--no-register` + our copy);
   (b) the `capcut` MCP refines it — `capcut_read_timeline` → trims with ripple, transitions from the catalog,
   keyframe punch-ins, audio fades, filters, hook/callout/end-card text via `capcut_add_text` — `capcut_validate` →
   `capcut_save`; (c) the CapCut repair lines (§0.2); (d) the P2 extras (OTIO + FCP7 XML + FCPXML + EDL / Descript via
   MCP) only when chosen; (e) `render\final-A.mp4` + one variant from the plan with ffmpeg, `render\history.md`.
   MCP absent → (a) + (c) + capcut-cli `add-text` / `transition` / `keyframe` lines are the CapCut layer. State `editing`.
6. **9d final check**: ONE `final-checker` (`BRIEFS\final-checker.md`; playbook §7) → `90-postgen\final-check.md`
   + `.json`; `re-edit` → editor again with the issues (max 2 loops, then show the owner); `done` → state `done`,
   `next_step: publish`; DELIVERABLES.md gets a "Post-generation" section. Final chat: render path, project
   path(s), DELIVERABLES path, and the reminder that speech captions are added with the owner's caption tool
   (`10-measure\transcript.srt` is available as a sidecar, never rendered).

## 10. Resume behaviour

On every invocation that names a run or finds no new video: `python TOOLS\state.py "<RUN>" get` → jump to
the section matching `next_step`: `measure` → §2 · `analysis` / `report` → §3 · `questions` / `product` → §4 ·
`planning` / `continuity` / `style-bible` / `feasibility` → §5 · `prompts` → §6 · `anomaly-check` → §7 ·
`deliverables` / `G1` / `G1-remaining` / `generate` → §8 · `drop-clips` / `P1` / `clip-qa` → §9.1–9.2 · `P0` → §9.3 ·
`trend` / `P2` / `P3` → §9.4 · `editor` → §9.5 · `final-check` → §9.6. Skip criteria per stage: the stage's
required outputs exist and are non-empty (§2 list; `20-analysis\report.md`; `30-decisions\answers.json` keys;
`40-plan\plan.json` (+ `approved: true` for Mode 3); `50-prompts\prompts.json`; `60-qa\qa.json.clean`;
`70-deliverables\DELIVERABLES.md`; `80-generated\manifest.json`; `90-postgen\qa.json`; `trend-brief.json`;
`edit-plan.json`; `final-check.json`). A skipped stage is announced in one line; the owner can say "redo <stage>".
Questions already in `answers.json` are not re-asked (their answers are shown in one line). A `*-failed`
stage → show `RUN\logs\<stage>.log` and retry that step once. Stage `re-edit` (final-check issues, or the owner
says they changed the project in CapCut / an NLE): re-read the edited timeline — CapCut: `capcut_read_timeline`
(MCP) for the current tracks/segments and `capcut export-timeline … --captions skip` (CLI) for the file the
"Re-import" line (§0.2) consumes; NLE: the exported timeline file — re-run the render line, then §9.6 again — every
re-render gets a new variant suffix and a `render\history.md` line. The owner may also export the MP4 from CapCut
directly; that file then goes through §9.6 as-is.

## 11. Agent-count policy (unbounded; scaled to the job; never minimised, never spawned for their own sake)

| Stage | Count rule |
|---|---|
| Measure | 0 (scripts run by the main session) or 1 measurer |
| Visual / audio / narrative | ceil(duration / 60 s) visual analysts (+ 1 reconcile when > 1) · 1 audio · 1 narrative |
| Product / swap | 1 identifier (re-spawned per Q1b loop) · 1 swap planner per ≤ 60 s segment with the product + 1 reconcile |
| Planning | 1 planner (mode-specific; re-spawned per A1/A2/A3 loop) · 1 continuity author · 1 style-bible author when swapped |
| Prompts | 1 writer per clip / per non-passthrough segment, parallel; fix rounds re-spawn only the affected writers |
| Anomaly check | 6 checkers per round (one per lens), parallel; ≤ 3 rounds |
| Generation | 1 generator per run (waves of ≤ 12 inside it); serial when chained |
| Post-generation | 1 clip-QA per clip, parallel · 1 trend researcher · 1 editor · 1 final checker |

## 12. NEVER

- Never run this pipeline as a Workflow, generate a Workflow script for it, or create a second command.
- Never modify `STACK\seedance\*` at run time — SPEC, EDITSPEC and the `director\` bundle change only on the
  owner's explicit request for an update.
- Never call `capcut_transcribe`, `capcut_review_transcript`, `capcut_add_captions`, `capcut_list_caption_styles`
  or `capcut_clear_captions` (speech-caption rule); never `capcut_save` with `force:true` into the live CapCut
  store, and never `--force-write` with capcut-cli there — close CapCut or wait.
- Never leave logos, labels, watermarks, wordmarks, hashtags, handles or brand mentions of the original product
  in any prompt, frame or dialogue after a swap (checked by L5 PR03 / ED04 and clip-QA A15).
- Never ask questions from a subagent; only the main session asks, verbatim from `REFS\questions.md`, in order.
- Never write a prompt before A2 = Approve in Mode 3 (and never before A1 = Confirm in Mode 2).
- Never hard-code a spec limit (clip seconds, resolution, ratio, reference counts, edit input length, credits)
  — read SPEC / EDITSPEC / the research notes at run time.
- **Never add speech captions or subtitles to an edit** — not burned in, not as a caption track, not via
  CapCut/Descript auto-captions; the owner uses a separate caption tool. Only hook text, callouts, end cards,
  stickers are allowed.
- **Never generate or spend anything before the owner answers G1** with the cost estimate in front of them;
  never submit more clips than confirmed; "I will generate myself" ends the run until clips are dropped back.
- **Never edit before P0 = "Edit now"**; never call paid MCP tools (generation, upscale, Descript agent/publish,
  Splice downloads, ElevenLabs generation) outside the stages the owner gated.
- Never present an estimate as a measurement, invent unreadable text, a speaker, a song title or a product fact.
- Never write results only to chat: every stage writes its files, then `state.json`.
