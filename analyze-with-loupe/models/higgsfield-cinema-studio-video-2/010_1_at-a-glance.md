## 1. At a glance
- **Positioning [HF]:** the Cinema Studio 2.x video engine.
  - The web app pairs Cinema Studio 2.0 with a "Hero Frame First" workflow: build the perfect still,
    then animate it, with up to three stacked camera moves.
  - Cinema Studio 2.5 adds colour grading, Soul Cast characters, Single / Multi-Shot Auto /
    Multi-Shot Manual modes, and speed ramps.
- **Underlying model:** not disclosed. Its parameter style (`cfg_scale`, std/pro modes, multi-shot)
  resembles Kling's [INFERRED].
- **Best for:** fast, cheap cinematic clips from a strong hero frame, with genre look, speed ramps and
  automatic multi-shot planning. Preflight: 6 s std = 9 credits [VERIFIED].
- **Weaker at:** exact multi-shot scripting over MCP (see §2.5), references beyond Elements, and exact
  text.

| Operation | How | Notes |
|---|---|---|
| Text-to-video | prompt | |
| Hero frame → video | `start_image` (+ `end_image`) | Recommended use |
| Image conditioning | `image` | Weighting undocumented |
| Reusable assets | `<<<element_id>>>` | Elements support "Cinema Studio Video 2" [HF] |
| Multi-shot | `multi_shots:true`, `multi_shot_mode:"auto"` | The model plans the shots; custom per-shot prompts are not available (§2.5) |

