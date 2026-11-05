# analyze-stack — architecture contract (every agent reads this first)

Owner context: US AI video-marketing company. Input = a viral sample video in our niche.
Output = a set of Seedance 2.5 prompts that reproduce that video's format (optionally with our
product swapped in), then a post-generation phase that QA's the generated clips, edits them
with trend boosts, and renders while keeping the project editable. Realism beats length:
a clean 30 s output is worth more than a 2 min output with anomalies.

## Locations (absolute; Windows 11; shell = Windows PowerShell 5.1 — no `&&`, no `||`)

Stack home: `C:\Users\Bulzart\.claude\analyze-stack\`

| Path | Purpose |
|---|---|
| `LAYOUT.md` | this contract |
| `research\` | build-time research: `miko-analysis.md`, `tool-audit.md`, `editing-tooling.md`, `trend-sources.md`, `capcut-draft-sample\` (a real CapCut 9.4 draft, plaintext JSON) |
| `seedance\` | **Seedance notes — READ-ONLY at run time.** `SEEDANCE-SPEC.md` (structured spec notes; §14 = precedence over the director bundle), `SEEDANCE-EDIT.md` (video_edit notes), `sources.md` (URLs + version the notes are based on), and `director\` = the owner-supplied **Seedance 2.5 Director** bundle (rev 2.1.0, installed 2026-09-19 from `C:\Users\Bulzart\Documents\prompts\seedance-2-5-agent-guide.zip`; validator: `python seedance\director\scripts\validate_bundle.py seedance\director --integrity`): the prompt-engineering method (intent contract, world-state ledger, causal action expansion, 15 anomaly categories, release gate, review record) that writers, the continuity author, the anomaly checkers and clip QA load. Never refreshed or edited by `/analyze-stack`; only when the owner explicitly asks for an update. |
| `references\` | rule files loaded by `/analyze-stack` (single source of truth): questions, pipeline stages, agent briefs, physics/blending/continuity rules, style taxonomy, viral analysis, compression planning, prompt template, anomaly checklist, product-spec template, deliverables spec, post-generation playbook |
| `tools\` | analysis scripts (Python). `tools\edit\` = post-generation scripts (editable project builders + render). Invoked as `python <script>` |
| `product-library\` | persistent product spec sheets reused across runs: `<product-slug>\spec.md`, `<product-slug>\images\`, `index.json` |
| `samples\` | sample videos for tests (`sample-62s-laemekiia.mp4`, `sample-40s-sophiesnowscents.mp4`, `sample-27s-roofingpov.mp4`) and `generated-clips\` (four 15 s clips that stand in for generated clips) |
| `runs\<run-id>\` | one folder per analysis run; every agent writes files here, never only to chat, so the pipeline can resume from any stage |

Skill (slash command) — the ONLY command. It is never executed as a Workflow and never generates one
(owner decision 2026-09-17, reaffirmed 2026-09-19); every worker is an Agent-tool subagent:

| Path | Engine |
|---|---|
| `C:\Users\Bulzart\.claude\skills\analyze-stack\SKILL.md` | the main session runs the procedure step by step and spawns every worker with the **Agent** tool; questions and gates stay in the main session |

`/analyze-stack` loads the `references\*` files and `seedance\SEEDANCE-SPEC.md`, asks the questions
in the fixed order (verbatim from `references\questions.md`), and writes the run-folder files below.

## Tool paths (PATH inside a fresh shell may be stale; scripts must fall back to these)

| Tool | Path |
|---|---|
| ffmpeg 9.0.1 | `C:\Users\Bulzart\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe` |
| ffprobe 9.0.1 | same folder, `ffprobe.exe` |
| Python 3.12.10 | `C:\Users\Bulzart\AppData\Local\Programs\Python\Python312\python.exe` (also `py.exe` launcher) |
| Git 2.55 | `C:\Program Files\Git\cmd\git.exe` |
| Node 24.21 / npm 11.19 | `C:\Program Files\nodejs\` |
| Visual C++ 2015-2022 x64 runtime | installed 2026-09-16 via winget (`Microsoft.VCRedist.2015+.x64`); required by ctranslate2 (faster-whisper) and onnxruntime (RapidOCR) — without it their DLLs fail to load |
| Nested headless Claude | `claude -p "<prompt>" --output-format text` works from a shell inside this session (~7 s round trip) — usable to verify that skills register |
| CapCut 9.4.0.4015 | `C:\Users\Bulzart\AppData\Local\CapCut\Apps\9.4.0.4015\CapCut.exe`; drafts in `C:\Users\Bulzart\AppData\Local\CapCut\User Data\Projects\com.lveditor.draft\<name>\draft_content.json` (plaintext JSON, `version` 360000, `new_version` "185.0.0"; index in `root_meta_info.json`). **CapCut is THE editing app** (owner, 2026-09-19). |
| CapCut MCP server `capcut` | `tools\mcp\capcut-mcp\src\server.js` (Gusmares/MCP-CapCut fork of JmsLdrn/capcut-mcp, commit bbe4c21, MIT; `tools\mcp\capcut-mcp\PROVENANCE.md`). Registered 2026-09-19 at user scope: `claude mcp add --scope user capcut -e CAPCUT_DRAFTS_DIR=<live store> -e CAPCUT_TEMPLATE_DRAFT=_analyze-stack-template -- node <server.js>`. Tools `capcut_list_drafts / read_timeline / clone_draft / add_video / add_image / add_audio / add_text / add_track / set_track_mute / move_segment / trim_segment (ripple) / split_segment / delete_segment / set_props / list_filters / add_filter / list_transitions / add_transition / list_masks / add_mask / add_keyframe / remove_keyframes / add_audio_fade / add_sticker / undo / raw_patch / validate / save / discard`. Session model: open → edits in memory → `capcut_validate` → `capcut_save` (`.mcpbak` backup, atomic write, refuses while CapCut.exe runs or the draft changed on disk). Forbidden: `capcut_transcribe`, `capcut_review_transcript`, `capcut_add_captions`, `capcut_list_caption_styles`, `capcut_clear_captions` (speech-caption rule). Discover with `ToolSearch "capcut_read_timeline"`; never hard-code the tool prefix. Smoke script: `tools\mcp\capcut-mcp\smoke.mjs` (verified 2026-09-19; local validator patch documented in PROVENANCE.md). Overlays always go on their OWN text track (`capcut_add_track type:text` first) — the validator rejects two texts overlapping on one track; transition/filter names must come from `capcut_list_*` |
| `_analyze-stack-template` draft | `<live store>\_analyze-stack-template\` — a permanent CapCut 9.4 draft with text, audio, transition and video materials (copied 2026-09-19 from the `analyze-stack-verify` run draft); the MCP harvests its text/audio/track shapes for `capcut_add_text` / `capcut_add_audio`. Never delete or edit it; if CapCut rewrites it on open that is harmless |
| capcut-cli 0.25.0 | `capcut` on PATH via `%APPDATA%\npm` (upgraded 2026-09-19 from 0.23.0). Direct CapCut path and the repair layer after every MCP save: `capcut register "<draft dir>" --apply --materials` (registers media in `draft_meta_info.json` + the `root_meta_info.json` entry), `capcut sync-timelines "<draft dir>" --nested --apply` (writes the `Timelines\` mirror CapCut 9.x treats as authoritative), `capcut lint "<draft dir>" -H`, `capcut export-timeline "<draft dir>" --out <file.otio> --captions skip`, `capcut add-text / transition / keyframe / add-filter / add-effect / trim / speed / volume`, `capcut version "<draft dir>" -H` (write guard: refuses CapCut 10.x and schema > 360000). Every mutating command refuses while CapCut.exe runs; `--force-write` is never used on the live store |

PATH refresh one-liner for PowerShell:
`$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')`

Python packages installed 2026-09-16 (verified importable): opentimelineio 0.18.1 with adapters
`cmx_3600, fcpx_xml, fcp_xml, otio_json, otioz, otiod` (otio-fcp-adapter, otio-fcpx-xml-adapter,
otio-cmx3600-adapter), scenedetect 0.7.1, faster-whisper 1.2.1 (+ctranslate2 4.8.2; models
`small`, `small.en`, `base` already cached under `C:\Users\Bulzart\.cache\huggingface\hub`),
moviepy 2.2.1, pillow 11.3, numpy 2.5, opencv-python(-headless) 5.0, imageio-ffmpeg, yt-dlp
2026.8.19, librosa 1.0, soundfile, pydub, rapidocr-onnxruntime 1.4.4 (+onnxruntime 1.30),
pycapcut 0.0.3 (reference source only — its template is CapCut 6.7; do not use at run time),
pyJianYingDraft 0.3.0 (JianYing-only — do not use at run time), requests.
Node globals: capcut-cli 0.25.0 (`capcut` on PATH via `%APPDATA%\npm`; draft linter, `register`,
`sync-timelines`, `export-timeline`, `add-text`, `transition`, `keyframe` — see the tool-paths table). HyperFrames local skills
under `~\.claude\skills\hyperframes-*` (CLI download + pinned Chrome attempted at build time —
see `research\editing-tooling.md` section E; optional overlay tier only).
Overlay-text fonts (hook text / callouts / end cards only — never speech captions; no admin, use
libass `fontsdir`): `tools\edit\fonts\` = Montserrat-ExtraBold / Black / Bold, Anton-Regular,
BebasNeue-Regular; system fallbacks Arial Black, Impact, Bahnschrift.
Also installed 2026-09-16: trendspy (Google Trends client), ByteDance's official Seedance 2.5
prompt-optimisation skill at `C:\Users\Bulzart\.claude\skills\sd25-pe\SKILL.md` (rule source
for prompt writers), whisper.cpp ggml models `tiny.en` + `base.en` in
`C:\Users\Bulzart\.cache\whisper-cpp\` (ffmpeg built-in whisper filter fallback).
Higgsfield MCP: reachable two ways — the claude.ai connector "Higssfield" (tools
`mcp__claude_ai_Higssfield__*`, connected) and a persistent user-scope Claude Code server named
`higgsfield` (`https://mcp.higgsfield.ai/mcp`, HTTP; tools `mcp__higgsfield__*` once the owner
authenticates it with `/mcp`). Skills must discover whichever is present with ToolSearch
("higgsfield generate_video") and never hard-code the prefix.

MCP servers connected to this Claude Code session (agents reach them via ToolSearch):
**capcut** (local stdio, user scope — the editing app's draft engine, see the tool-paths table),
Higgsfield (video_analysis_create/status, virality_predictor, tiktok_music_trending,
shorts_studio_*, upscale_video, generate_video, models_explore, media_upload), Descript
(import_media, prompt_project_agent, publish_project, export_timeline → EDL/FCPXML/Premiere/
Resolve XML), ElevenLabs (creative_transcribe_audio, creative_generate_speech, sound design),
Splice (sounds/stacks), Adobe (video_create_quick_cut, video_render, video_resize, image tools),
HyperFrames by HeyGen (read tools only from CLI; local skills installed for authoring/render),
Google Drive, Linear, Claude Docs.

## Run folder layout: `runs\<run-id>\`  (run-id = `YYYYMMDD-HHMMSS-<slug>`)

```
00-input\        source.mp4 (copy) or link.txt + downloaded file; product-images\ ; input.json
10-measure\      probe.json, cuts.json, shots.json, keyframes\ , contact-sheets\ , audio.wav,
                 transcript.json + transcript.srt, ocr.json, audio-features.json, measure-summary.md
20-analysis\     visual.md, audio.md, narrative.md, style-profile.md, beat-map.md, entities.json,
                 report.md   (report.md is what the owner sees)
30-decisions\    answers.json (every answer, in order), product-spec.md, swap-map.md
40-plan\         slicing.md (Mode 1) | segments.md (Mode 2) | compression-plan.md (Mode 3),
                 continuity-sheet.md, style-bible.md (only when style is swapped), plan.json
50-prompts\      clip-01.md … clip-NN.md, prompts.json, references\ (frames + product images cited)
60-qa\           anomaly-check.md, fixes-round-N.md, qa.json
70-deliverables\ DELIVERABLES.md (index), prompts-final.md (numbered, durations, refs, continuity)
75-generation\   only when the owner chose G1 = generate on Higgsfield: uploads.json (local file → media
                 id), jobs.json (prompt → job id, model, params, status, credits), generation-log.md
80-generated\    generated clips (downloaded by 7g, or dropped back by the owner) clip-01.mp4 … +
                 manifest.json
90-postgen\      clip-qa.md, fix-prompts.md, trend-brief.md, edit-plan.json, project\ (editable),
                 overlays.ass (hook text / callouts / end card ONLY — speech captions/subtitles are
                 never added in the edit; the owner uses a separate caption tool), render\final.mp4,
                 final-check.md
state.json       {run_id, stage, mode, answers, files, next_step, updated}
```

## Fixed process (what is fixed is the process, not the agent count)

Stage 1 measure (scripts) → Stage 2 analysis (visual, audio, narrative+virality; reconciled by
the main session into `report.md`) → Stage 3 questions (product swap FIRST, then approach:
replicate with generated clips OR Seedance 2.5 edit of the original video; then edit intent or
mode, duration + seconds-per-prompt, Mode 3 extras, style (replicate only), platform/aspect) →
product identification + swap/blend planning if a swap was chosen → Stage 4 planning (slicing /
segment selection with confirmation / compression plan with approval / edit segmenting;
continuity sheet; style bible if style swapped) → Stage 5 prompt writing in parallel (one writer
per clip or per edit segment) → Stage 6 anomaly check of all prompts together, fixes looped back
to writers until clean → deliverables + state.json → G1 gate: generate now on Higgsfield through
the MCP (optional; enhanced prompts + product samples + cited frames / source segments uploaded
and attached; cost shown first) or hand the prompts back for the owner to generate elsewhere.
Post-generation: clip QA → P0 gate (edit now / regenerate / stop) → trend research → editing **in CapCut**
(registered draft from `build_capcut_draft.py`, refined through the `capcut` MCP, repaired with capcut-cli,
rendered from `edit-plan.json` with ffmpeg; the draft stays editable in CapCut and is read back through the
MCP on every re-edit; never speech captions) → final check.
Prompt method: every prompt is planned, written and audited with the Seedance 2.5 Director method in
`seedance\director\` (intent → world state → causal actions → audit → compile → release gate) on top of the
stack's physics / blending / continuity rules; SPEC/EDITSPEC numbers always win over the bundle's numbers.
Agent count at run time is unbounded: scale to video length, mode, clip count and swap.

Seedance on Higgsfield (from `seedance\SEEDANCE-SPEC.md` + `research\higgsfield-mcp.md`, always
re-read them — never assume): model `seedance_2_5`, modes t2v | omni_reference | video_edit |
video_extension; 4–30 s; 480p/720p/1080p; 24 fps; ratios auto/9:16/16:9/…; media roles
start_image, end_image, image_references, video_references, audio_references; video_edit keeps the
source duration. HyperFrames CLI 0.8.43 + Chrome Headless Shell are installed ("Ready to render").
