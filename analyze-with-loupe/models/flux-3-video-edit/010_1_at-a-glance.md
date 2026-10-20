## 1. At a glance

- **Positioning.** "Send FLUX Video Edit [fast] a clip and say what should be different. Everything the prompt doesn't mention stays as shot: length, framing, camera, timing and audio all come from the source" [OFFICIAL]. It edits by "remove, add or replace objects, change the setting, restyle, change text or dialogue" [OFFICIAL]. Higgsfield: "Edit a video with a text prompt. Uses the first 15 seconds at most; costs 1 credit per second of the processed clip" [HF].
- **Best for:** Edit Mode clean-up and changes that keep the source's motion, camera and timing:
  - removals, including (by inference) captions and overlays;
  - placed additions;
  - recolours and weather/VFX layers;
  - re-sets with contact surfaces;
  - restyles through materials;
  - blockout → finished scene;
  - length-matched dialogue changes and translation [OFFICIAL].
- **Weaker at / cannot do:**
  - no image input, so an approved person or product cannot be swapped in by reference [OFFICIAL];
  - no masks, no extension [OFFICIAL];
  - output ≤720p at 24 fps [OFFICIAL];
  - dialogue cannot outgrow the original speech [OFFICIAL].
- **Choose this model when** the source's motion and framing are right and the change can be described in words, especially removing overlays. **Choose another model when** a replacement must match approved references (use `gemini_omni_flash_1_1` `mode:"edit"` with `image_references`, or Higgsfield's object-replacement model), or when new footage is needed.

| Operation | How to invoke on Higgsfield | Notes |
|---|---|---|
| Text-to-video / frames / references | N/A on Higgsfield | Use `flux_3_video` |
| Video edit (Edit Mode) | `medias:[{role:"video_references"}]` + prompt | Source ≤15 s; output ≤720p, 24 fps [HF][OFFICIAL] |

