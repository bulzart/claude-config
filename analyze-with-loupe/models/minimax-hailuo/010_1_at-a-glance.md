## 1. At a glance

**Which public versions are these?** MiniMax's API lists `MiniMax-Hailuo-02`, `MiniMax-Hailuo-2.3` and
`MiniMax-Hailuo-2.3-Fast` [OFFICIAL]. Evidence for the mapping:

| Higgsfield variant | most likely public model | evidence | confidence |
|---|---|---|---|
| `minimax` | MiniMax Hailuo 02 (2025-06-18) | Higgsfield says 512 is unsupported by the 2.3 variants and incompatible with `end_image` [HF]; upstream, 512P exists only for `MiniMax-Hailuo-02`, and first+last-frame exists only for `MiniMax-Hailuo-02` and "does not support 512P" [OFFICIAL] | high [INFERRED] |
| `minimax-2.3` (default) | MiniMax Hailuo 2.3 (2025-10-28) | name match; 768/1080 only [OFFICIAL/HF] | high [INFERRED] |
| `minimax-2.3-fast` | MiniMax Hailuo 2.3 Fast | name match; image-to-video only upstream [OFFICIAL] | high [INFERRED] |
| `minimax-fast` | a speed tier of Hailuo 02 ("Hailuo 02 Fast", 512p image-to-video, 6/10 s, sold by third-party hosts) | no such model in MiniMax's own API [OFFICIAL]; third-party listings [SECONDARY] | low [INFERRED] |

- **Positioning.** Hailuo 02: "Native 1080p, SOTA Instruction Following, Extreme Physics Mastery" — "currently the
  only model globally capable" of intricate scenarios such as gymnastics; offered as 768p-6s, 768p-10s, 1080p-6s
  [OFFICIAL]. Hailuo 2.3: "Building upon the Hailuo 02 model, it further enhances dynamic expression… physical
  actions, stylization, and character micro-expressions, while further optimizing its response to motion commands";
  better anime/illustration/ink-wash/game-CG styles; "enhanced response to motion commands for objects" [OFFICIAL].
  2.3 Fast "generates videos faster at a lower price, reducing costs for batch creation by up to 50%" [OFFICIAL].
  Higgsfield: "Natural physics, facial emotion, multiple variants" [HF].
- **Best for:** short (6/10 s) physical-motion shots from a 9:16 still — bodies, sports, falls, fluids; facial
  emotion; stylized looks (2.3); cheap iterations (2.3 Fast).
- **Weaker at:** no audio; no references; no aspect-ratio control (text-to-video is landscape → unusable for 9:16);
  ≤10 s; 1080p only at 6 s; no Edit Mode; no first-party prose prompt guide. Not in the current Artificial Analysis
  top-25 image-to-video board [SECONDARY] — a 2025 generation.
- **Choose `minimax_hailuo` when** you need a silent, physics-heavy or emotive 6–10 s shot animated from an approved
  9:16 frame. **Choose another model when** you need text-to-video, audio, references, >10 s, multi-shot or Edit Mode
  (`minimax_h3`, `wan3_0`).

| operation | how to invoke on Higgsfield | notes |
|---|---|---|
| Start frame → video | `start_image` (9:16) | any variant; output ratio follows the image [OFFICIAL/HF] |
| First + last frame → video | `start_image` + `end_image`, variant `minimax` | upstream only on Hailuo 02, 768/1080 [OFFICIAL] |
| Text-to-video | `prompt` only; variant `minimax` or `minimax-2.3` | landscape output — not for 9:16 deliverables (§2.6) |
| Camera control | `[command]` brackets in the prompt | 15 official commands [OFFICIAL] |
| References, audio, edit, extension | — | N/A on Higgsfield |

