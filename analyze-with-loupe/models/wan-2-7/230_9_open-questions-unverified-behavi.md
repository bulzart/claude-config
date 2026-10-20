## 9. Open questions / unverified behaviour
- Exact image-to-video output size for a 9:16 frame at 720P (720×1280 expected from the pixel-count rule).
- Exact upstream mapping of `audio_references` (t2v `audio_url` vs i2v `driving_audio`) and handling of a second
  audio item.
- Which dated `wan2.7-t2v` / `wan2.7-i2v` snapshots Higgsfield calls; whether `prompt_extend` stays on and
  `watermark` off.
- Whether `aspect_ratio` is ignored or rejected when `start_image` is present.
- Whether "No dialogue." / "No background music." are honoured in t2v/i2v as documented for reference mode.
- `supports_unlim` eligibility on the user's plan.
