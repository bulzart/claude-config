## 9. Open questions / unverified behaviour

- Which model serves `veo3` after the 2026-06-30 upstream shutdown, and whether the two variants still differ.
- Actual output for `aspect_ratio: "9:16"`: 720×1280 expected, unconfirmed. Also actual duration (8 s expected).
- Whether a `duration` field sent to `veo3` is ignored, snapped or rejected.
- Current subtitle-artifact rate after Google's 2025 fixes; there is no official figure.
- Whether `[00:00-00:02]` timestamps work on Veo 3 (documented for 3.1 only).
