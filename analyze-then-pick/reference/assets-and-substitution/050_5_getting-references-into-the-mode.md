## 5. Getting references into the model (by capability)

| model capability (see `models/index.json`) | strategy |
|---|---|
| Multi-reference (`image_references`, optionally `video_references` / `audio_references`) — Seedance 2.0/2.5, Wan 3.0 / 2.6, MiniMax H3, FLUX 3 Video, Gemini Omni, Grok 1.5 | Attach the canonical views and character references directly. Declare **one role per reference** in the prompt, using the model's syntax (multiple views of one item jointly define one entity). Attach a source video as a motion or camera reference only in **Recreate** (or Edit Mode), with explicit exclusions (its people, products, text and branding are not inherited). **Create never attaches a reference video** |
| Elements (`<<<id>>>`) — Kling 3.0, Seedance 2.0, Cinema Studio Video 2 / 3.0 | Create Elements once per project asset and cite them in the prompt |
| Start-frame-only — Veo 3 / 3.1, Kling 2.6 / 3.0 Turbo, Happy Horse, Grok, Hailuo, Wan 2.7, Seedance 1.5, Cinema Studio v1 (and anything where exact geometry matters most) | **Build a 9:16 start frame first** with an image model that takes several references (`nano_banana_pro`, `gpt_image_2_5`, `seedream_v5_pro`): the approved character, the client asset at correct scale, grip and lighting, and the environment. A natural placement is already at its anchor in this frame, with a contact shadow and the scene's light (`generation-system.md` §4b). Use `aspect_ratio:"9:16"` and at least 720×1280 output. **Check the frame against the canonical template before animating**: it becomes the geometry authority for that clip. Its `job_id` can be passed directly as `medias[].value` |
| Edit (source video + references) — Seedance 2.5 `video_edit` / `ad_multiplier`, Kling 3.0 Omni Edit, Genjutsu, Gemini Omni 1.1 edit, FLUX 3 Video Edit | The source video comes first (already 9:16), then the asset images in `@ImageN` order. Replacements are bound to their images, and each replaced source entity gets an exclusion sentence |

Useful image utilities for references (all cost credits; preflight when possible):
- `image_background_remover` / `remove_background`: a clean product cut-out;
- `nano_banana_2` or `seedream_v5_pro` with `is_inpaint`: cleaning text from a start frame;
- `flux_2_pro_outpaint` / `outpaint`: extending a frame to 9:16 without stretching.

