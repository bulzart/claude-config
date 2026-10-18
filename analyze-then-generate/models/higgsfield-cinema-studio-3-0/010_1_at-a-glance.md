## 1. At a glance

- **Positioning [HF]:** "Most advanced cinema-grade model" (catalog). Higgsfield's pages describe:
  - a "physics-aware generation engine" ("collisions carry a real sense of weight", fabric and
    environment detail);
  - a "cinematic reasoning system that understands story intent from reference images alone";
  - native audio (sound effects, speech, background music);
  - identity "locked across every frame": "the same face, body proportions, clothing, and features
    throughout the entire video".
- **Underlying model:** not disclosed for 3.0. The web app's Cinema Studio 4.0 "runs on Seedance 2.5"
  [HF]. The 3.0 MCP parameter surface (genre list, resolution tiers up to 4k) matches Seedance 2.0's
  [INFERRED]; do not rely on that.
- **Best for:** cinematic narrative shots with weighty physical action, a strong genre look, and
  consistent characters.
- **Weaker at:** exact choreography from a reference video (no video input), exact text, and fine
  multi-reference control (no `image_references` role; use Elements).
- **Choose it** for premium single-shot or short cinematic beats from a strong first frame or Elements.
  **Choose another model** when you must drive motion from a reference video (Seedance 2.x, Wan 3.0,
  MiniMax H3, Genjutsu), need more than 15 s, or need an edit of existing footage.

| Operation | How to invoke | Notes |
|---|---|---|
| Text-to-video | prompt only | `aspect_ratio:"9:16"`, `resolution:"720p"` |
| Image-conditioned | `medias:[{role:"image"}]` | Generic image input; Higgsfield does not document how strongly it is followed |
| First / last frame | `start_image` (+ `end_image`) | Exact compositions |
| Reusable characters / props / places | `<<<element_id>>>` in the prompt | Elements support Cinema Studio Video 3.0 [HF] |
| Edit / extension | — | Not available on this id |

