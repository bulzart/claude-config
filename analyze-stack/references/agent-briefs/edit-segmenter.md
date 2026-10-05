# edit-segmenter — agent brief (Stage 4e, Seedance 2.5 edit approach; one agent)

Load first: `LAYOUT.md`, `references\mode-rules.md` §5 (edit segmenting rules, passthrough, re-join),
`seedance\SEEDANCE-EDIT.md` §2 (input limits — read the numbers at run time), §5 (mux recipe), §6 (split
on hard cuts, 4–20 s), `references\continuity-rules.md` §4, `tools\README.md` if present.

## Purpose
Split the original video into source segments that Seedance 2.5 `video_edit` can take (each within
the spec's video-input limit, on hard cuts when uneven is allowed, never mid-word), cut them with ffmpeg
at native resolution/ratio/fps with the source audio saved for the mux, mark segments that need no edit
as passthrough, and write `plan.json`.

## Inputs
`10-measure\probe.json`, `cuts.json`, `shots.json`, `transcript.json`, `30-decisions\answers.json` (Q2 = edit,
Q3b segment length, Q3c), `30-decisions\edit-intent.md` (what changes, per entity and moment),
`30-decisions\swap-map.json` (moments) when a product is swapped, `20-analysis\entities.json`.

## Outputs
`40-plan\edit-segments.md`, `40-plan\plan.json` (`approach: "edit"`, items `kind: "edit-segment"`, schema in
mode-rules §5/§7), `00-input\segments\seg-NN.mp4` + `seg-NN-audio.mka` per segment, `00-input\segments\segments.json`
(`[{"no":1,"file":"…","start_s":0.0,"end_s":15.0,"duration_s":15.000,"width":1080,"height":1920,"fps":30,"stream_copy":false,"passthrough":false}]`),
`50-prompts\references\seg-NN-start-<t>.jpg` (first frame, for the writer to LOOK at), state files index.

### `edit-segments.md` skeleton
```markdown
# Edit segments — <run-id> · Seedance 2.5 video_edit · original 62.40 s 1080x1920 30 fps · Q3b 15 s · Q3c uneven
Limits read from SEEDANCE-EDIT.md §2: source 4–30 s hard, ≤ 20 s recommended, 1 video per call, ≤ 200 MB, 300–6000 px, ratio 0.4–2.5, 24–60 fps; output keeps the source ratio and duration (−0.4 s max)
| seg | source in | source out | dur (exact) | cut method | moments / intent items | passthrough | file | audio |
| 01 | 00m00.00s | 00m13.40s | 13.400 | re-encode (boundary not on a keyframe) | M01, M02 | no | 00-input\segments\seg-01.mp4 | seg-01-audio.mka |
| 03 | 00m31.40s | 00m45.00s | 13.600 | stream copy | — | yes (no product, no other edit) | seg-03.mp4 | — |
Join order after generation: 01 (edited) → 02 (edited) → 03 (passthrough) → 04 (edited); join_clips.py conforms each edited segment to its source duration and muxes the source audio.
## Feasibility (for A3)
| seg | risks | recommendation |
```

## Method
1. Read the limits from `SEEDANCE-EDIT.md` §2. Refuse Q3b outside the hard limit (write it and return);
   if Q3b exceeds the recommended length, plan with it but write the stability warning.
2. Boundaries: equal (Q3c default) → `N = ceil(D / L)`, boundaries at multiples of `D/N`, each then
   moved to the nearest hard cut within ±2 s when one exists (never split mid-shot when a cut is that
   close), never inside a spoken word; uneven → snap every boundary to hard cuts (confidence ≥ 2) so
   each segment stays within [min, max]; a remainder shorter than the minimum is merged into its neighbour.
3. Cut. Preferred route (scripts): first
   `python C:\Users\Glaresquare1\.claude\analyze-stack\tools\slicer.py --duration <D> --clip-seconds <Q3b> --min-clip <MIN> --max-clip <MAX> [--uneven --shots "<run>\10-measure\shots.json" --snap-window 2] --out "<run>\40-plan\plan-slices.json"`
   (adjust boundaries for the mid-word rule yourself), then
   `python C:\Users\Glaresquare1\.claude\analyze-stack\tools\segment_source.py --run-dir "<run>" --plan "<run>\40-plan\plan-slices.json" --reencode`
   (`--copy` only when every boundary is on a keyframe) → `00-input\segments\seg-NN.mp4` + `segments.json`
   (ffprobe-verified durations). `segment_source.py` reads `plan-slices.json` (`clips[]` with start/end), not
   the final `plan.json` `items[]`, and writes ONLY the mp4 files + `segments.json` — after it, run the two
   ffmpeg lines below for every segment yourself (`seg-NN-audio.mka` for the mux and the first frame for the
   writer). Manual route for the cut itself (PATH refresh first; `$ff` from LAYOUT):
   - boundary on a keyframe (check `ffprobe -select_streams v -show_frames -show_entries frame=pts_time,key_frame -read_intervals <t-0.05>%<t+0.05>`) → stream copy:
     `& $ff -hide_banner -loglevel error -y -ss <in> -to <out> -i "<src>" -c copy -movflags +faststart "<seg>"`
   - otherwise frame-accurate re-encode:
     `& $ff -hide_banner -loglevel error -y -ss <in> -to <out> -i "<src>" -c:v libx264 -preset veryfast -crf 16 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart "<seg>"`
   - audio for the mux: `& $ff -nostdin -y -i "<seg>" -map 0:a:0 -vn -c:a copy "<seg-NN-audio.mka>"`
   - first frame: `& $ff -hide_banner -loglevel error -y -i "<seg>" -frames:v 1 -update 1 -q:v 2 "<run>\50-prompts\references\seg-NN-start-<t>.jpg"`
4. ffprobe every segment (duration, w×h, fps, size); verify the limits; record exact durations (the
   edit output is conformed to them).
5. Passthrough: a segment with no swap-map moment and no edit-intent item inside → `passthrough: true`
   (no prompt, no cost, joined as the original).
6. `plan.json` items: `{no, kind:"edit-segment", source_file, source_start_s, source_end_s, duration_s, passthrough, moments[], edit_intent_items[], references:[product images in @Image order]}`;
   feasibility flags (two swapped products in one segment, person swap with speech, > 5 references,
   segment > 20 s). `state.py "<run>" set stage=planning next_step=continuity`.

## Quality bar
- Every segment file plays, is within the limits, and its exact duration is in `segments.json`.
- No boundary inside a spoken word; joins land on hard cuts wherever a cut exists within the tolerance.
- The join order and the passthrough list are explicit.

## When evidence is missing
No `cuts.json` → equal boundaries only, with a note that joins may fall mid-shot. No transcript → the
mid-word rule is skipped and noted. Never trim or clamp a source that is out of range silently — report it.
