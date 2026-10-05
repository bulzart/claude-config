# final-checker — agent brief (Stage 9d; one agent; after every render)

Load first: `LAYOUT.md`, `references\post-generation-playbook.md` §7 (the check table), §5 (export spec), §4.3
(safe zones), `references\deliverables.md` §1 (what DELIVERABLES.md links), `references\clip-qa-template.md`
(anomaly ids reused here), `seedance\director\assets\review-record.md` (read-only; pass / fail / unknown per
requirement — never turn an unknown into a pass; inspect the full render, not stills only). When the render came
from a CapCut export by the owner, also confirm with `capcut_read_timeline` (MCP) or `capcut export-timeline`
that the draft and the render agree on order and duration (±0.2 s).

## Purpose
Verify the render against the edit plan and the platform spec before the owner sees it: segment order,
trims, overlay timing, loudness, safe zones, duration/format, no leftover original-brand marks, no speech
captions/subtitles rendered, music licence, editable project present. Decide `done` or `re-edit`.

## Inputs
`90-postgen\render\final-*.mp4`, `90-postgen\edit-plan.json`, `overlays.ass`, `qa.json`, `trend-brief.json`,
`30-decisions\swap-map.md` (original brand marks to look for), `answers.json` (Q6, P2), `90-postgen\project\`.

## Outputs
`90-postgen\final-check.md` (one table per render, rows exactly as playbook §7 + the caption row below),
`90-postgen\final-check.json` (`{"renders":[{"file":"…","pass":true,"rows":{"frames_vs_plan":"pass","audio_sync":"pass","loudness":"-14.2 LUFS / -1.0 dBTP","safe_zones":"pass","format":"pass","brand_marks":"pass","captions_absent":"pass","music_licence":"pass","editable_project":"pass"},"issues":[]}],"verdict":"done|re-edit"}`),
`state.json` (`stage=done` + `next_step=publish`, or `stage=re-edit` + `next_step=editor` with the issues).

## Method
1. `python C:\Users\Glaresquare1\.claude\analyze-stack\tools\clip_frames.py "<render>" --out "<run>\90-postgen\qa\final-A" --fps 1`
   → `sheet.jpg`, `f-*.jpg`; LOOK (Read tool) at the sheet and at the hook, mid and CTA frames.
2. Frames vs plan: clip order and trims match `edit-plan.json.clips[]` (schema v2, `tools\edit\EDIT-PLAN.md`);
   every `text_overlays[]` item appears at its start/end; no S2+ window from `qa.json` survived.
3. Captions absent: no speech captions/subtitles anywhere (frames at 1 fps; `overlays.ass` events are only the
   hook/callout/end-card texts listed in the plan; no `captions` block in the plan) — a violation is `re-edit`.
4. Audio sync: SFX land on cut frames (±2 frames); if a VO exists, re-transcribe the render (faster-whisper
   `small.en`) and compare word timing with the plan's VO cue (±80 ms).
5. Loudness: `& $ff -i "<render>" -af ebur128=peak=true -f null -` → I −14 ±1 LUFS, TP ≤ −1.0 dBTP.
6. Safe zones: `drawbox` overlay check on 3 frames (playbook §7 line); all text/product/logo inside the recorded box.
7. Format: ffprobe 1080x1920, 30 fps, h264 High, yuv420p, aac 48 kHz, faststart (`moov` first), duration ≤
   `max_duration_s` and ≤ platform ceiling.
8. Brand marks: OCR + eyes on hook/CTA/product frames and reflections for the original brand, creator handle,
   watermark, competitor product (A15); the audio tail for the original's sound.
9. Music licence: `audio.bed.license` vs deliverable type (paid → never `organic-only`).
10. Editable project: paths in `edit-plan.json.meta.projects` exist and open (CapCut draft listed in
    `root_meta_info.json` when registered; `.otio` parses with `python -c "import opentimelineio as otio; otio.adapters.read_from_file(r'<path>')"`).
11. Optional (only if Notes allow paid calls): Higgsfield `virality_predictor` on the render — record numbers.
12. Write the files; on `done` add the render, plan, project paths and trend brief to `70-deliverables\DELIVERABLES.md`
    (append a "## Post-generation" section); set state.

## Quality bar
- Every row has a measured value or a frame reference; "pass" without evidence is not allowed.
- The verdict is `re-edit` if any row fails; the issues list tells the editor exactly what to change.

## When evidence is missing
If a check cannot run (e.g. OTIO import fails on this machine), mark the row "not verified — <reason>"
and do not count it as a pass; the verdict still requires all verifiable rows to pass.
