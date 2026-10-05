# Mode rules — Mode 1 slicing, Mode 2 selection, Mode 3 compression, anchors hybrid, edit approach (Stage 4)

Inputs: `20-analysis\beat-map.md/.json`, `10-measure\cuts.json`, `shots.json`, `probe.json`,
`30-decisions\answers.json` (Q2, Q2m, Q3a/b/c, Q4a–c), `swap-map.md`, `seedance\SEEDANCE-SPEC.md` §2.1
(4–30 s per clip) and `SEEDANCE-EDIT.md` §2 (edit source 4–30 s, ≤ 20 s recommended). Limits are read
at run time, never assumed. Output: `40-plan\plan.json` + the mode's markdown file.

## 1. Mode 1 — full replication (`40-plan\slicing.md`, slicer agent, `tools\slicer.py`)

- Total = original duration D; clip length L = Q3b; N = ceil(D / L).
- **Equal lengths (Q3c default)**: slices `[0, L), [L, 2L), …`; the last slice may be shorter only if
  unavoidable and must stay ≥ min_clip_s (spec); if the remainder < min_clip_s, redistribute: use
  N = ceil(D / L) equal slices of D / N seconds each, rounded to integer seconds (Seedance takes integer
  durations); write the exact slice table with source in/out (`00m00.00s`) and clip durations; the sum
  equals D within ±1 s (the last clip absorbs rounding).
  Example (62.4 s, L = 15; `tools\slicer.py` output verified 2026-09-16): the remainder 2.40 s would be below the
  4 s minimum → rebalanced to 5 equal source slices of 12.48 s that tile the original exactly; each clip's
  generation duration is `gen_duration_s = ceil(slice)` = 13 s (Seedance takes integer seconds), and the writer
  describes the extra 0.52 s as a held end frame (the join trims every clip back to its slice length).
- **Uneven allowed**: boundaries snap to the nearest confirmed cut (`cuts.json`, confidence ≥ 2
  detectors) within ±3 s of the equal boundary, or to a beat boundary from the beat map; every slice
  must be within [min_clip_s, max_clip_s]; prefer boundaries where the audio has no speech mid-word
  (`transcript.json` word timestamps).
- Each slice lists the beats it covers, the shots inside it, the cuts inside it (a clip may contain
  hard cuts: the prompt then uses "Hard cut." between shots, spec §5 transitions), dialogue lines
  verbatim with their local timestamps, and the reference frames to extract (start frame; one frame per
  internal shot).
- `plan.json` clips: `{no, kind:"clip", source_start_s, source_end_s, duration_s, beats[], shots[], cuts_inside[], dialogue[], references[]}`.

## 2. Mode 2 — best-segment replication (`40-plan\segments.md`, segment-selector agent, then A1)

- Target T = Q3a. Candidate windows = contiguous beat runs with total duration ≤ T (from
  `viral-analysis.md` §4); rank by `sum(importance × dur)`; a window that does not start with a hook-
  quality beat (V ≥ 4 within its first 3 s) is demoted below any that does.
- Propose the top window (or up to 3 non-overlapping windows when T ≥ 2 × the best single window and the
  owner's Q3a phrasing allowed "segment(s)"), each snapped to hard cuts at both ends, with: time range,
  duration, beats, why (mechanics from the beat map), what is lost outside it. Also prepare the next-best
  set for the A1 option "Show alternatives".
- The main session asks **A1** with `{segments with timestamps, total {total}s}` and `{why each}`.
  "Change — I will give timestamps": accept owner timestamps, snap to cuts only if within ±0.5 s, else
  use them as given. "Show alternatives": show the next-best set and re-ask A1.
- After confirmation, slice each kept segment exactly like Mode 1 (equal / uneven per Q3c) and write
  `plan.json` (clips reference the kept segment's source times). If the windows are non-adjacent, the
  continuity sheet declares a "hard cut: new setup" at each join.

## 3. Mode 3 — condensed remake (`40-plan\compression-plan.md`, compression-planner agent, then A2)

Algorithm and gate in `compression-planning.md`. Summary: beat map → importance → time budget over kept
beats → keep/merge/drop table with reasons → compressed storyboard + script at target length → split
into clips (Q3b/Q3c) with continuity → success test → **A2 approval before any prompt is written**.
`plan.json` clips carry `beats[]` with `source_start_s/end_s` per beat and `compressed: true|false`.

## 4. Anchors hybrid (Q4c ≠ "No anchors")

- Anchors are source time ranges (from the suggested candidates or the owner's list `mm:ss–mm:ss`),
  snapped outward to cuts (never cut inside an anchor).
- Each anchor is replicated exactly: its clip(s) are Mode 1 slices of the anchor range (its own
  dialogue verbatim, its own shots), placed in the compressed timeline at the position the beat order
  dictates; the surrounding beats are compressed by the Mode 3 algorithm with the remaining budget
  (T − Σ anchor durations). If an anchor is longer than max_clip_s it is sliced like Mode 1.
- The compression plan marks anchor rows `ANCHOR` and the A2 question lists them.
- Feasibility: if Σ anchors > 0.8 × T, the plan recommends a longer target or fewer anchors (A2 option
  "Recommend a shorter target" is replaced by the recommendation text in the plan file; the wording of
  A2 stays as in questions.md).

## 5. Edit approach — Seedance 2.5 video_edit (`40-plan\edit-segments.md`, edit-segmenter agent, `slicer.py` + `segment_source.py`)

- Read the limits from `SEEDANCE-EDIT.md` §2 at run time: source segment 4–30 s hard, ≤ 20 s
  recommended, one video per call, native ratio kept, ≥ 720p, ≤ 200 MB, 24–60 fps in.
- Segment length L = Q3b (refused if outside the hard limit; if L > the recommended 20 s the plan notes
  the stability warning). Equal (Q3c default) or snapped to hard cuts (uneven) — **never split mid-shot
  when a cut is within ±2 s**; a segment must not end mid-word (word timestamps).
- Cut the source with ffmpeg into `00-input\segments\seg-NN.mp4` (`segment_source.py`): stream copy
  (`-c copy`) when the boundary is on a keyframe, else a frame-accurate re-encode
  (`-ss <start> -to <end> -c:v libx264 -preset veryfast -crf 16 -c:a aac -b:a 192k -movflags +faststart`),
  keep the native resolution/ratio/fps; write `seg-NN-audio.mka` (source audio for the mux) next to it — the
  segmenter agent extracts it with ffmpeg (`-map 0:a:0 -vn -c:a copy`), `segment_source.py` writes only the mp4 +
  `segments.json`; ffprobe every segment and record exact durations (the edit output is conformed to these).
- Segments that contain no product moment and no other requested edit (from `30-decisions\edit-intent.md`)
  are marked `passthrough: true` in `plan.json` — they are NOT sent to Seedance (no cost) and are joined
  as the original footage; the main session says so in the deliverables.
- `plan.json` items: `{no, kind:"edit-segment", source_file:"00-input/segments/seg-01.mp4", source_start_s, source_end_s, duration_s (exact, e.g. 15.000), passthrough:false, moments:["M03"], edit_intent_items:[…], references:[product images in @Image order]}`.
- Re-join after generation: the generator conforms each edited segment to its source duration and muxes
  the original audio back (`SEEDANCE-EDIT.md` §5 recipe) → `80-generated\seg-NN.mp4`; then
  `python …\tools\join_clips.py --clips <seg files in order, passthrough ones from 00-input\segments\> --out "<run>\80-generated\joined.mp4" --width <w> --height <h> --fps <fps>`
  normalises every file once and concatenates with the `concat` demuxer (stream copy) → `joined.mp4`.
- Slicing for the edit approach uses `tools\slicer.py` (`--duration --clip-seconds --min-clip --max-clip [--uneven --shots]`)
  → `40-plan\plan-slices.json`, which `tools\segment_source.py --run-dir <run> --plan <plan-slices.json>` cuts.

## 6. Recommendation rule (all modes): realism beats length

The planner computes a **feasibility score** per clip: number of simultaneously moving elements, people
in frame, camera moves, liquid/particle events, small-text needs, high-burst actions. Any clip with
≥ 2 risky items is listed for A3. When the recommended shorter target (or a simpler split) removes
every risky item, the plan says so and the main session offers it (Q3a recommendation text, A2 option
"Recommend a shorter target", or A3 "Apply recommendation").

## 7. `plan.json` (shared by all modes)

```json
{"schema":"analyze-stack.plan/1","run_id":"…","approach":"replicate|edit","mode":1,"target_s":62,"clip_s":15,"equal":true,
 "anchors":[{"start_s":6.2,"end_s":9.5}],
 "items":[{"no":1,"kind":"clip","source_start_s":0.0,"source_end_s":13.0,"duration_s":13,"beats":["b01","b02"],"shots":[1,2],"cuts_inside":[1.4],
           "dialogue":[{"t_local":0.3,"speaker":"C1","line":"okay this is the one"}],"references":["50-prompts/references/product-front.jpg","50-prompts/references/product-label.jpg","50-prompts/references/clip-01-start-00m00.00s.jpg"],
           "compressed":false,"passthrough":false}],
 "feasibility":[{"no":3,"risks":["two people + pour","handheld + whip pan"],"recommendation":"split clip 3 at the cut 00m34.10s"}],
 "updated":"2026-09-16T15:10:00-05:00"}
```
