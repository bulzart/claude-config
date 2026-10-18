## 9. Open questions / unverified behaviour

- Which `mode` Higgsfield expects for `start_image`/`end_image`; whether `start_image` may be combined with `*_references`.
- Whether `draft_job_id` finalize calls must resend prompt/medias; whether draft works with edit/extension.
- Confirm on Higgsfield that `video_extension` returns only the new segment, as ByteDance's own example does (ffprobe the first result: length ≈ `duration`), and which direction each `extension_mode` value maps to.
- Actual output dimensions for 9:16 first-frame and edit tasks on Higgsfield (720×1280 expected); behaviour when a start frame or source is not exactly 9:16.
- Whether Higgsfield's `_trim.mp4` re-encode changes frame counts (defeating the 8n+1 fix); what `duration_policy:"strict"` does.
- Whether audio-only reference calls are accepted on Higgsfield.
- Real-face moderation outside the Ad Multiplier recipe.
- Whether an edit can be made to lay a thin closed carton flat on open wood: guides and wording did not (CE-091, CE-093, CE-094).
- Prompt ceiling for non-edit calls (only the 3,900-character edit contract is documented).
- Removal quality for large or moving overlays (full-screen title cards, animated stickers) and spurious-subtitle rates at 9:16 on 2.5.
