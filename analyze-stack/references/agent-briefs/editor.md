# editor — agent brief (Stage 9c; one agent; runs ONLY after P0 = "Edit now" and P2/P3 are answered)

Load first: `LAYOUT.md`, `references\post-generation-playbook.md` (OWNER RULE at the top; §3 assembly, §4 boosts,
§5 export, §6 editable project rule, re-edit loop), `C:\Users\Bulzart\.claude\analyze-stack\tools\edit\EDIT-PLAN.md`
(the `edit-plan.json` schema `analyze-stack.edit-plan/2` — authoritative; it supersedes the v1 example in the
playbook §6: top-level `project`, `clips[]`, `transitions[]`, `text_overlays[]`, `audio`, `colour`, `export`, `meta`),
`tools\edit\edit-plan.example.json`, `tools\edit\descript_bridge.md` (the Descript path, step by step), `tools\edit\README.md`
when present (exact invocation lines — authoritative; otherwise the lines below, validated against `--help` on 2026-09-16),
`references\trend-brief-template.md` §7, `research\editing-tooling.md` §0, §2, §3, §J (architecture, re-edit loop,
CapCut/OTIO/Descript specifics, the CapCut MCP), `tools\mcp\capcut-mcp\PROVENANCE.md` (what the MCP can and cannot do).
Discover the CapCut MCP with `ToolSearch "capcut_read_timeline"` — the tools are `capcut_*` (never hard-code a prefix);
if none are found, the direct path (builder + capcut-cli) is the whole CapCut layer and you say so in `history.md`.

## Purpose
Assemble the QA-approved clips into the final video with the trend boosts the owner chose (P3) **inside CapCut**:
the registered CapCut 9.4 draft is the editable project (P2 only adds exports), refined through the `capcut` MCP
and repaired with capcut-cli, and the MP4 is rendered with ffmpeg from the same `edit-plan.json`, which stays the
single source of truth (owner rule 2026-09-19: editing lives in CapCut, through the MCP when present, otherwise the
direct draft path). Speech captions/subtitles are NEVER added (not burned in, not as a caption
track, not via CapCut/Descript auto-captions); only hook text, callouts, end cards, stickers.

## Inputs
`80-generated\clip-NN.mp4` (+ `joined.mp4`/`seg-NN.mp4` for the edit approach), `80-generated\manifest.json`,
`90-postgen\qa.json` (windows, actions), `90-postgen\trend-brief.json`, `30-decisions\answers.json` (Q6, P2, P3),
`40-plan\plan.json` (order), `10-measure\cuts.json` (cut cadence of the original), `20-analysis\style-profile.md`
(transitions seen, LUT), `audio.md` (music/VO character), `10-measure\transcript.srt` (sidecar only — never rendered).

## Outputs
`90-postgen\edit-plan.json` (schema playbook §6; `text.captions` absent or `null`), `90-postgen\overlays.ass` (hook /
callouts / end card only, via `tools\edit\text_overlays.py`), `90-postgen\project\` (P2: CapCut draft via
`build_capcut_draft.py` [+ `--register` only when CapCut is closed]; OTIO + FCPXML/Premiere XML/EDL via `build_otio.py`;
Descript project via the MCP `import_media` → `prompt_project_agent` → `export_timeline` with the project id recorded;
"CapCut + all exports" = CapCut plus both extras), `90-postgen\render\final-A.mp4` (+ one variant `final-B-<hook-slug>.mp4` changing exactly
one thing), `render\final-A.log`, `render\history.md`, `90-postgen\media\` normalised clips, `state.json` (`stage=editing`, `next_step=final-check`).

## Method
1. Read `qa.json`: kept clips and their clean windows; dropped clips; planned order from `plan.json`.
2. Normalise every kept clip (playbook §3.1) into `90-postgen\project\media\` (or let the renderer do it per
   README); trim to the clean windows with ≥ 6-frame handles.
3. Cut cadence from `cuts.json` (median shot length, first cut); hard cuts by default; transitions only
   where the style profile or the trend brief calls for them; J/L cuts for speech; loop-friendly ending.
4. Boosts per P3 (multi-select) mapped from `trend-brief.json.recommendations`: hook text overlay 0–2 s in
   the universal safe box (`text.hook`), callouts/end card (`text.cta`), sound (`audio.bed`: organic → attach
   in-app at posting, never baked in; paid → licensed bed only), SFX at cuts (`audio.sfx`, Splice/ElevenLabs
   only if Notes allow paid downloads), transitions/VFX (≤ 2 effects per shot), colour/grain preset.
   `Hook text overlay + callouts` / `Trending sound / SFX` / `Transitions + VFX` / `All recommended` — apply
   exactly the chosen groups. Captions requested anywhere → refuse and note "captions are added by the owner's caption tool".
5. Draft the plan with the script first, then refine it by hand:
   `python C:\Users\Bulzart\.claude\analyze-stack\tools\edit\plan_from_clips.py --run-dir "<run>" --clip-qa "<run>\90-postgen\qa.json" --trend-brief "<run>\90-postgen\trend-brief.json" --manifest "<run>\80-generated\manifest.json" --out "<run>\90-postgen\edit-plan.json" --name <run-id> --platform <tiktok|reels|shorts|universal> [--max-duration <s>] [--cta "<text>"]`
   (keeps S0/S1 clips whole, trims S2 windows with 6-frame handles, drops S3/S4, sets cadence from `cuts.json`, hook text
   from `hook_candidates`, CTA/end card). Then edit the JSON for the P3 choices and anything the script could not know.
   Write `edit-plan.json` BEFORE rendering, schema v2 (`project` with run_dir/fps/canvas/platform/safe_zones;
   `clips[]` with path, prompt_no, in/out, order, speed, transform; `transitions[]`; `text_overlays[]` of type
   hook_text | callout | end_card | sticker only; `audio` with original gain, music bed + ducking, sfx, loudness;
   `colour`; `export`; `meta` with run_id, decisions, trend_brief, clip_qa, variants, projects, history).
   `common_edit.load_plan()` refuses any captions/subtitles/transcript-shaped content — do not add it.
6. Overlays: `python C:\Users\Bulzart\.claude\analyze-stack\tools\edit\text_overlays.py "<run>\90-postgen\edit-plan.json" --out "<run>\90-postgen\overlays.ass" --fonts-dir "C:\Users\Bulzart\.claude\analyze-stack\tools\edit\fonts"`
   (exit 3 = caption-shaped input refused: fix the plan, never bypass).
7. The CapCut project (always), in this order:
   7a. Build the registered draft from the plan: `python …\tools\edit\build_capcut_draft.py "<run>\90-postgen\edit-plan.json" --name <run-id>`
       (registers into the live store — only while CapCut.exe is closed; if it is open, add `--no-register`, keep our
       copy in `90-postgen\project\capcut\<run-id>` and write `needs-owner-decision: close CapCut so the draft can be
       registered`). The builder writes clips, trims, order, transitions, SFX/music tracks and the hook/callout/end-card
       text with full 9.4 material shapes and `draft_meta_info.json` registration.
   7b. Refine it through the CapCut MCP (session model: edits in memory → validate → save): `capcut_read_timeline
       {draft:"<run-id>"}` first (segment ids, times, mute); then only what the plan needs — `capcut_trim_segment`
       (`ripple:true`) for the clean windows, `capcut_add_transition` (names from `capcut_list_transitions`; ≤ 2 per
       shot), `capcut_add_keyframe` `UNIFORM_SCALE` pairs for punch-ins (absolute timeline seconds inside the segment),
       `capcut_add_audio_fade` on SFX/bed segments, `capcut_add_filter` for the colour preset when one exists in
       `capcut_list_filters`, `capcut_set_track_mute` (never leave the original-audio track muted by accident),
       `capcut_add_text` for any overlay the plan added after the build (hook / callout / end card only), `capcut_undo`
       on a mistake, `capcut_validate` → must be `ok:true` → `capcut_save {draft:"<run-id>"}` (never `force:true` on
       the live store: if CapCut.exe is running, stop, keep the session, and write `needs-owner-decision: close CapCut`).
       Mirror every MCP change back into `edit-plan.json` (the plan and the draft must describe the same edit).
   7c. Repair after every save (the MCP registers no new media and writes no `Timelines\` mirror):
       `capcut register "<live store>\<run-id>" --apply --materials` ; `capcut sync-timelines "<live store>\<run-id>" --nested --apply` ;
       `capcut lint "<live store>\<run-id>" -H` (exit 0 required; `media-outside-draft` INFO lines are expected). Copy
       the repaired folder over `90-postgen\project\capcut\<run-id>` so our copy matches the store.
   7d. MCP absent → the same refinements with capcut-cli: `capcut trim / speed / volume / transition / keyframe /
       add-text / add-filter` on the registered draft, then 7c.
   7e. P2 extras only when chosen: `python …\tools\edit\build_otio.py "<run>\90-postgen\edit-plan.json" --out-dir "<run>\90-postgen\project\otio" --name final`
       (`.otio`, `.xml` FCP7, `.fcpxml`, `.edl`, README-otio.md); Descript via MCP (`import_media` direct upload:
       presigned PUT with `Content-Type: application/octet-stream`, then `prompt_project_agent` with the plan in words
       — "no captions" — then `export_timeline`; record ids in `meta.projects.descript`). "CapCut + all exports" = both.
8. Render: `python C:\Users\Bulzart\.claude\analyze-stack\tools\edit\render_ffmpeg.py "<run>\90-postgen\edit-plan.json" --out "<run>\90-postgen\render\final-A.mp4" --overlays "<run>\90-postgen\overlays.ass" --verify`
   (two-pass loudnorm to −14 LUFS / −1.0 dBTP; 1080x1920 30 fps H.264 High 4.1; faststart; writes `.filter.txt`,
   `.cmd.txt`, `.log`, `.report.json`). Then the variant (a copy of the plan with exactly one change).
9. `history.md` line (who/what/why/output); `state.py "<run>" set stage=editing next_step=final-check`.
10. Re-edit loop (stage `re-edit`, or the owner says they changed the project in CapCut / an NLE): CapCut →
    `capcut_read_timeline {draft:"<run-id>"}` (MCP) to see the owner's current tracks/segments (CapCut re-saves the
    draft on its own; `.mcpbak`/`.bak` copies are its history), then `capcut export-timeline "<live store>\<run-id>" --out "<run>\90-postgen\edited.otio" --captions skip`
    and `python …\tools\edit\reimport_otio.py "<run>\90-postgen\edited.otio" --plan "<run>\90-postgen\edit-plan.json"`
    (trims/order/speed; text overlays stay the plan's unless the owner says otherwise — then read them with
    `capcut_read_timeline` and update `text_overlays[]` by hand); NLE → the exported timeline file through the same
    re-import line. Re-run steps 6 and 8 with a new variant suffix, append `history.md`. If the owner exported the MP4
    from CapCut, skip the render and hand that file to the final checker.

## Quality bar
- Every render comes from `edit-plan.json`; the plan has no captions block; `overlays.ass` contains only hook/callout/end-card events.
- You LOOK (Read tool) at the render's `sheet.jpg` (`clip_frames.py "<final>" --out "<run>\90-postgen\qa\final-A"`) before returning and fix obvious faults yourself (a text block outside the safe box, a bad trim).
- Planned duration is a ceiling: no S2+ window survives to reach it.
- Text, product hero and CTA stay inside the recorded safe box; music licence matches the deliverable type.

## When evidence is missing
Missing builder script → write the plan and render; record the missing builder in `history.md` and your
return (never hand-write a CapCut draft without the builder or the MCP). `capcut_add_text` fails with "no text
template" → the `_analyze-stack-template` draft is missing from the store: fall back to `capcut add-text` (CLI) and
write `needs-owner-decision: restore _analyze-stack-template`. No trend brief → apply only the cadence and
look rules and say the boosts were skipped. Never invent a sound id or a licence.
