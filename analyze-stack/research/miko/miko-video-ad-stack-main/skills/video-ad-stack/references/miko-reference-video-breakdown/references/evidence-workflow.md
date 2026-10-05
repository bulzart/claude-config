# Evidence workflow

Preserve source footage; write derivatives into a separate working folder. Check ffmpeg/ffprobe, frame inspection and connected Higgsfield visual/audio analyzer availability. Missing tools are a limitation to report, not evidence that an analysis ran. No separate speech-transcription dependency is required.

## Preparation and measurement

Probe video dimensions, frame rate, duration and audio stream. Trim the chosen segment accurately; record source start/end and segment-local timestamps. Split long coverage into indexed segments and reconcile their boundaries.

The source SOP uses ffmpeg scene scores over 0.30 for hard-cut candidates and over 0.08 for broader visual changes. These thresholds are starting heuristics: flashes overcount, similarly colored cuts can be missed, and small UI changes or slow camera moves may not register. Count confirmed cuts separately from candidate changes. Shot count is generally confirmed internal cuts plus one for a continuous segment; do not add duplicate segment-boundary shots.

Example filter fragments to use with the local ffmpeg invocation:

```text
select='gt(scene,0.30)',showinfo
select='gt(scene,0.08)',showinfo
fps=3,scale=270:480:force_original_aspect_ratio=decrease,pad=270:480:(ow-iw)/2:(oh-ih)/2,tile=4x4:padding=4
fps=4,tblend=all_mode=difference,signalstats,metadata=print:key=lavfi.signalstats.YAVG
```

Use 3 sampled frames/second for short fast-cut footage and 2 for longer footage as the SOP's starting settings; increase sampling around ambiguity. Preserve aspect ratio rather than stretching landscape footage. Label timestamps where possible. If using unlabeled tiles, map sheet/cell to the sampling schedule with `((sheet-1)*cells_per_sheet + cell-1)/sample_fps`, plus source offset; verify actual sampled PTS before claiming precise timing. A 3x4 sheet has 12 cells, not 16. Padding cells at the end are not source frames.

Motion difference metrics are optional. Report preprocessing/settings alongside values; low difference is not automatically a dead or ineffective shot. Confirm motion visually.

## Watching and speech

Use the current media-upload route for the local trimmed segment, confirm upload if required, then create the analysis and poll its ID. Keep upload credentials out of saved output. A direct YouTube route is useful when supported, but a full-link analysis must not be misrepresented as the same trimmed segment.

Use the Higgsfield analyzer's audio results for speech, delivery, music, ambience and effects. No audio stream means no speech transcript. If the analyzer returns only dialogue summaries or misses a word, label that limitation; do not convert paraphrases into purported verbatim quotations. Replay source audio where possible to resolve significant ambiguities. If exact speech remains unclear, mark it uncertain or request clarification. Do not invent speaker identity. This supersedes the original PDF's separate transcription step at the user's direction.

## Reconciliation

- Cut timing: detector candidate plus source-frame confirmation; inspect adjacent source frames for precision.
- Camera motion, wardrobe, room/setup and props: compare consecutive inspected frames.
- Spoken words: analyzer dialogue evidence, with source-audio checking when needed; distinguish exact words from summaries.
- Music, effects and acoustics: audio inspection/analyzer with uncertainty stated.
- Labels or screen text: full-resolution source frames first; never invent unreadable text.

Record material disagreements, evidence and resolution. Keep unresolved cases marked. Calculate speech rate only with a sufficiently complete dialogue record; otherwise mark unavailable. State the denominator (whole segment or speech-only duration). The SOP's 150/175 WPM examples are descriptive reference points, not compulsory targets.
