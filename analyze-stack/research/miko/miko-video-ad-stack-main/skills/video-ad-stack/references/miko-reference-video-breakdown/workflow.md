# Reference video breakdown

Adapted from Miko's Second-by-Second Video Breakdown SOP, supplied September 6, 2026. This skill observes the reference; brand adaptation belongs in the separate video-plan stage. Do not silently rewrite the source dialogue to fit a different product.

## Inputs and scope

Accept a video file/link and requested segment. Probe duration, dimensions, frame rate and audio presence. Analyze the requested coverage: use short segments, preferably up to 30 seconds, but cover every segment if the user requests the whole video. Preserve original-time offsets. Never silently replace a whole-video request with the first 30 seconds.

Create `breakdown/<reference-id>/` for evidence and the final `breakdown.md`. Read [evidence-workflow.md](references/evidence-workflow.md) before extracting or reconciling evidence.

## Two complementary evidence methods

1. **Measurement:** ffmpeg cut candidates, visual-change candidates and contact sheets. These are heuristics to verify, not infallible counts.
2. **Watching and listening:** Higgsfield video analyzer on the same segment for actions, scene details, dialogue, delivery and sound. Discover the current tool schema; persist the analysis ID and poll that job instead of submitting duplicates. Use its actual returned audio/dialogue evidence. If only a paraphrase is returned, label it as a summary rather than an exact transcript. Mark uncertain words or speakers; inspect the source audio when available to resolve important ambiguity. Do not install or require a separate speech-transcription tool for this workflow.

Open every contact sheet yourself. Use full-resolution frames and closer frame sampling around ambiguous cuts, text, gestures or setup changes. Sampled sheets are not enough to claim frame-accurate timing. Reconcile disagreements explicitly; confirmed source footage/audio is the authority. If a layer is unavailable, report its missing coverage and continue only with evidence actually available.

## Deliverable

For the four-stage stack, BOTH ffmpeg/frame inspection and Higgsfield visual/audio analysis must complete on matching coverage. If either method is unavailable, save partial evidence but mark the stage blocked; do not advance to adaptation/generation as though the full SOP completed.

Use [output-template.md](references/output-template.md). Preserve the SOP's detailed shot table, appearance and wardrobe per setup, spatial background detail, lighting, grade, overlay inventory, audio character, retention mechanisms and measured statistics. Distinguish measured values, estimates and creative interpretation. Do not claim attention or conversion performance was measured from the footage alone.

Transcribe user-supplied footage when requested. For third-party linked material, keep excerpts within applicable quotation limits and supply a timestamped summary instead of an unauthorized full transcript. Mark inaudible words and uncertain speakers; don't invent them.

Inventory captions, handles and graphics separately from physical product-label text. The default recreation brief excludes added overlays but preserves intended physical labels. User-requested final captions can be added in editing; they are not part of the source scene.

Finish with transferable mechanics and production constraints for the next skill. For a requested faithful recreation, also read [recreation-prompt.md](references/recreation-prompt.md) and produce the SOP's prompt deliverable. For a different brand/product, hand off the observed structure to the adaptation stage instead. Do not submit media generation jobs from this skill.
