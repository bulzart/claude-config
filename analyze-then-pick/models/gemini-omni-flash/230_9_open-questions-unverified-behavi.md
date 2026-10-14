## 9. Open questions / unverified behaviour

- Whether `gemini_omni` still routes to `gemini-omni-flash-preview` after its Gemini API deprecation (2026-09-30), is served by 1.1, or fails.
- Exact output dimensions at 720p 9:16 (720×1280 expected), and whether edit output follows the source ratio or the sent `aspect_ratio`.
- Whether `gemini_omni` honours image inputs as a first frame. The Agent Platform lists image-to-video and references as unsupported for the 1.0 preview; the Gemini API changelog says it can "animate still images".
- How Higgsfield maps `medias` to `<IMAGE_REF_N>`/`<VIDEO_REF_N>`, and whether Google tag syntax passes through.
- Edit-source limit: Higgsfield says 30 s, Google 10 s. Does Higgsfield segment longer clips?
- Removal quality for burned-in and animated captions, stickers and UI overlays. There is no official text-removal example.
- Real reference ceiling (7 vs 10), and whether `image_references` are accepted with `start_image` in `image-to-video` mode.
