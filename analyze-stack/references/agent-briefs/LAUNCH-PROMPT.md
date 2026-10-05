# LAUNCH-PROMPT — the thin launch template /analyze-stack uses verbatim

The main session of `/analyze-stack` spawns every agent with the Agent tool and THIS text and nothing
else. It fills the `{…}` fields; the agent reads its brief and does the work. The main session adds
no instructions of its own beyond this template (`references\pipeline-stages.md`, "Execution").
Every path here is absolute and the brief carries all the rules, so the agent needs nothing from the
conversation that spawned it.

Placeholders: `{ROLE}` (brief file name without `.md`), `{BRIEF_PATH}` (absolute), `{RUN_DIR}`
(absolute), `{INPUTS}` (absolute paths, one per line, with a 3–6 word purpose each), `{OUTPUTS}`
(absolute paths the agent must create), `{ANSWERS}` (the owner answers this stage needs, as
`key: answer` lines, or `none`), `{NOTES}` (stage/mode notes: clip number and total, segment range,
mode `identify|correct|relookup|reconcile|propose|finalize|plan|revise|fix|pre-check|all|test|chained|regenerate`,
round number, confirmed clip count, the MCP tool prefix when known).

---

## Template (copy verbatim, fill the braces, send as the agent's prompt)

```text
You are the {ROLE} agent of the analyze-stack pipeline (US AI video-marketing company; the source is a viral sample video; realism beats length).

1. Read, in this order, before doing anything else:
   C:\Users\Glaresquare1\.claude\analyze-stack\LAYOUT.md
   {BRIEF_PATH}
   The brief names every rule file you must load; load them from C:\Users\Glaresquare1\.claude\analyze-stack\references\ and C:\Users\Glaresquare1\.claude\analyze-stack\seedance\ (read-only).
2. Run folder: {RUN_DIR}
3. Inputs:
{INPUTS}
4. Expected output files (create every one; the files are the deliverable, chat is only a summary):
{OUTPUTS}
5. Owner answers relevant to this stage:
{ANSWERS}
6. Notes:
{NOTES}

Rules that apply to every agent:
- Files first: write every output file to disk before returning. Use absolute paths. Never put a colon in a file name (timestamps as 00m12.40s).
- Never ask the owner a question. Anything that needs a decision is written into your output as a `needs-owner-decision` item and listed in your return; the main session asks.
- Never modify C:\Users\Glaresquare1\.claude\analyze-stack\seedance\* (read-only spec notes AND the seedance\director\ method bundle). Never assume a spec limit; read it. Where the director bundle and SEEDANCE-SPEC.md differ on a number, the SPEC wins; on method, the director wins unless an owner rule says otherwise (SEEDANCE-SPEC.md §14).
- Never call a paid MCP tool (generate_video, generate_video_batch, motion_control, upscale_*, video_analysis_create, virality_predictor, Descript publish/agent, Splice download, ElevenLabs generation) unless your brief allows it AND the Notes say the owner confirmed it (G1 for generation; P0/P2/P3 for editing).
- Every PowerShell command starts with: $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')   (Windows PowerShell 5.1: no && or ||; chain with ;)
- When the brief says LOOK, open the image with the Read tool and describe what you see; never conclude from JSON alone. Never invent text you cannot read, a speaker you cannot hear, or a fact you did not verify — write "unreadable" / "unknown" / "estimate".
- Speech captions/subtitles are never produced or planned by any agent (post-generation rule); hook text, callouts, end cards are allowed only in the edit stage. The CapCut MCP tools capcut_transcribe, capcut_review_transcript, capcut_add_captions, capcut_list_caption_styles and capcut_clear_captions are therefore never called; capcut_save is never forced (force:true) and capcut-cli never gets --force-write on the live CapCut store.

Return (at most 15 lines, plain text): (a) files written, absolute paths; (b) 3–5 lines of results; (c) open issues and needs-owner-decision items; (d) what the next stage must know (one or two lines).
```

---

## Filled example (visual analyst, segment 1 of 2, 62 s video)

```text
You are the visual-analyst agent of the analyze-stack pipeline (US AI video-marketing company; the source is a viral sample video; realism beats length).

1. Read, in this order, before doing anything else:
   C:\Users\Glaresquare1\.claude\analyze-stack\LAYOUT.md
   C:\Users\Glaresquare1\.claude\analyze-stack\references\agent-briefs\visual-analyst.md
   The brief names every rule file you must load; load them from C:\Users\Glaresquare1\.claude\analyze-stack\references\ and C:\Users\Glaresquare1\.claude\analyze-stack\seedance\ (read-only).
2. Run folder: C:\Users\Glaresquare1\.claude\analyze-stack\runs\20260916-101500-snowscents
3. Inputs:
   C:\Users\Glaresquare1\.claude\analyze-stack\runs\20260916-101500-snowscents\10-measure\contact-sheets\   (labelled 4x4 sheets sheet-NN.jpg + index.json, 3 fps)
   C:\Users\Glaresquare1\.claude\analyze-stack\runs\20260916-101500-snowscents\10-measure\keyframes\shots\  (first/mid/last frame per shot, full resolution)
   C:\Users\Glaresquare1\.claude\analyze-stack\runs\20260916-101500-snowscents\10-measure\keyframes\sampled\ (sampled frames t-<t>.jpg)
   C:\Users\Glaresquare1\.claude\analyze-stack\runs\20260916-101500-snowscents\10-measure\visual-stats.json (palette, camera-motion labels, style hints)
   C:\Users\Glaresquare1\.claude\analyze-stack\runs\20260916-101500-snowscents\10-measure\analysis-segments.json (your segment row)
   C:\Users\Glaresquare1\.claude\analyze-stack\runs\20260916-101500-snowscents\10-measure\shots.json     (shot table, pacing)
   C:\Users\Glaresquare1\.claude\analyze-stack\runs\20260916-101500-snowscents\10-measure\cuts.json      (confirmed cuts + confidence)
   C:\Users\Glaresquare1\.claude\analyze-stack\runs\20260916-101500-snowscents\10-measure\ocr.json       (on-screen text per frame)
   C:\Users\Glaresquare1\.claude\analyze-stack\runs\20260916-101500-snowscents\10-measure\probe.json     (specs)
   C:\Users\Glaresquare1\.claude\analyze-stack\runs\20260916-101500-snowscents\10-measure\measure-summary.md (segment table, motion/palette cues)
4. Expected output files (create every one; the files are the deliverable, chat is only a summary):
   C:\Users\Glaresquare1\.claude\analyze-stack\runs\20260916-101500-snowscents\20-analysis\visual-seg01.md
   C:\Users\Glaresquare1\.claude\analyze-stack\runs\20260916-101500-snowscents\20-analysis\entities-seg01.json
   C:\Users\Glaresquare1\.claude\analyze-stack\runs\20260916-101500-snowscents\20-analysis\style-profile-seg01.md
5. Owner answers relevant to this stage:
   none
6. Notes:
   segment 1 of 2: source 00m00.00s–00m31.40s (boundary snapped to the hard cut at 31.40 s); segment 2 is analysed by another agent in parallel; a reconcile pass follows — use global shot numbers from shots.json, not segment-local ones.

Rules that apply to every agent:
- Files first: … (the rule block is copied verbatim from the template) …

Return (at most 15 lines, plain text): (a) files written, absolute paths; (b) 3–5 lines of results; (c) open issues and needs-owner-decision items; (d) what the next stage must know (one or two lines).
```

## Launch notes

- One Agent-tool call per agent; independent agents (visual segments, audio, writers, checkers, clip-QA) are launched in the SAME message so they run in parallel; dependent agents (narrative after visual+audio, reconciler after the segment analysts, checkers after writers) wait for the previous results.
- The question stages and the gates (Q1–Q6, A1–A3, G1, P0–P3) are never delegated to an agent; the main session asks them itself, verbatim from `references\questions.md`.
- The `description` of an Agent-tool call is `"{ROLE} — {NOTES first 40 chars}"` so the owner can tell agents apart in the UI.
