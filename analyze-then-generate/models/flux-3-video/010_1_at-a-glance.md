## 1. At a glance

- **Positioning.** FLUX 3 "jointly learns from images, videos, and audio within a unified architecture" [OFFICIAL: BFL blog, 2026-07-23]. The video API launched in preview on 2026-08-04 with "Up to 20 seconds at FHD… 24 fps", "multilingual speech with strong lipsync, plus effects and ambience", and "Multiple scenes and camera angles in one generation, with accurate in-scene text and typography" [OFFICIAL]. Higgsfield: "Text-to-video, multi-frame image-to-video, and video continuation with synchronized audio" [HF].
- **Best for:**
  - the longest single generations here (20 s);
  - hard-cut multi-shot sequences in one clip;
  - pixel-exact first frames;
  - multilingual lip-sync;
  - motivated physical inserts (light in fog, liquids, contact);
  - short in-scene typography [OFFICIAL].
- **Weaker at / risky (per BFL's field guide):**
  - "close human performance";
  - "identity-critical products without conditioning";
  - "exact audiovisual synchronization";
  - "graphic sans-serif overlays and late-shot text";
  - "long multi-step narratives with exact timing" [OFFICIAL].
  - End-frame pinning is "experimental" [OFFICIAL].
- **Choose this model when** you need 10–20 s, planned cuts, an exact opening frame, multilingual speech, or a short physical text element. **Choose another model when** you need editing (use `flux_3_video_edit`), identity or product fidelity from references alone, or exact captions (post).
- **Role-ambiguity warning:** `image_references` and `video_references` each map to two different documented BFL behaviours (§2.5 #1). Probe before production use.

| Operation | How to invoke on Higgsfield | Notes |
|---|---|---|
| Text-to-video | no `medias` | BFL `t2v` [OFFICIAL] |
| Start frame / start + end | `start_image` (+ `end_image`) | Pixel-exact frames [OFFICIAL] |
| Multi-frame storyboard | Tagged "storyboard" [HF]; role mapping undocumented | §2.5 #1 |
| Image references | `image_references` | Semantics unverified (§2.5 #1) |
| Video input | `video_references` | Higgsfield: "video continuation" [HF] |
| Edit a supplied clip | N/A here → `flux_3_video_edit` | [OFFICIAL][HF] |

