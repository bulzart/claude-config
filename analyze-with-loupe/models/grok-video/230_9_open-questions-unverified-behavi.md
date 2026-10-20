## 9. Open questions / unverified behaviour

- Output resolution of `grok_video` on Higgsfield (xAI API default 480p) and its exact 9:16 dimensions.
- Whether `grok_video_v15` honours an `aspect_ratio` sent through MCP (it is absent from the catalog but present in Higgsfield's REST schema), and what `auto` yields in reference mode.
- Whether MCP also forbids `start_image` plus references (the REST docs forbid it), and how many `audio_references` MCP accepts (REST: one `audio_url`).
- Whether uploaded voice clips are accepted as `audio_references`; xAI gates custom voices.
- The mapping of `grok_video` to `grok-imagine-video` (inferred), and the tag order Higgsfield uses.
- Subtitle or pseudo-text behaviour with dialogue; there is no measurement.
