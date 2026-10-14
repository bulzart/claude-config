## 4. Fixed output format: 9:16 at 720p (720×1280)

Every Higgsfield generation in both modes is vertical 9:16 at 720p. It is never asked, and never
stretched.

### 4.1 Decision tree
1. **Native.** The model has `aspect_ratio` 9:16 and a 720p setting → send both through the model's
   own parameter names (`models/index.json → output_9x16_720p.params`) → confirm 720×1280 with `qc`.
2. **Near-native.** The output is 9:16 at a different size (768p, 1080p, 2K, or 704×1280) →
   `atp.py conform` (scale-to-cover plus a crop of a few pixels, lanczos).
3. **The aspect follows an input** (a start frame, or a source video for edits and motion transfer) →
   make the input 9:16 first:
   - build or crop the start frame at 720×1280;
   - reframe the source (below).
4. **A source video is not 9:16 in Edit Mode** → before the edit:
   - `atp.py conform --focus-x/--focus-y` when a crop keeps every important subject, prop and action
     (the tool refuses more than 12 % loss unless `--allow-large-crop`; check the storyboard first);
   - otherwise Higgsfield `reframe` (`aspect_ratio:"9:16"`, `resolution:"720p"`, AI-expanded edges;
     preflight with `get_cost`);
   - otherwise regenerate with the source as a video reference in a 9:16 generation.
5. **The output is not 9:16 when it should have been** → treat it as a failure. Conform only when the
   crop is subject-safe; otherwise regenerate with corrected parameters.
6. **Padding** (`conform --mode pad`, blurred fill) only when the user asks for it.

### 4.2 Post-processing order
`hf-get` → `restore-audio` → `conform` → `trim` (dead head/tail) → `concat` (multi-clip videos) →
`qc` of the clean video.
- **Analyze Mode** then continues in the video's CapCut project (`capcut-assembly.md`): inserts,
  text layers, then the preview QC.
- Edit Mode `restore-audio` always uses the original audio from `<given path>/files_audio/`, created
  at intake by `split-audio`, with `--audio-offset`, and `--start` when a single segment was edited.
- Multi-segment edits: `concat` the edited pictures first, then restore the full original audio
  once.
- Only silent copies (`videos_without_audio`) are uploaded to Higgsfield.
- After the user approves an Edit Mode video, `finalize` copies it to `<given path>/final/<original
  name>.mp4`.
Text is rendered last, at the final resolution, so it is never scaled or cropped afterwards.
