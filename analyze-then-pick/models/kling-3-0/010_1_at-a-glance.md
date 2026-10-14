## 1. At a glance

- **Positioning.** Kling 3.0 launched on 2026-02-06 with Video 3.0 Omni and Image 3.0 [OFFICIAL S5]. The Kling 3.0 Model Series "utilize a deeply integrated unified model training framework, achieving more native multimodal input and output", with native audio and element consistency control; "up to 15 seconds of continuous video, with a flexible duration ranging from 3 to 15 seconds"; multi-shot narratives; start frame + element reference; "Compared to Video 2.6, Video 3.0 excels at managing referencing three or more characters"; dialogue in Chinese, English, Japanese, Korean and Spanish with dialects and accents; "native-level text output" [OFFICIAL S1]. Turbo (2026-06-17) is a speed- and cost-optimised variant with audio included and improved lip sync [SECONDARY S12].
- **Best for:** cinematic 3–15 s shots with strong motion and physical detail (Higgsfield: "Cloth dynamics, hair movement, fluid behavior, and contact collisions") [HF S17]; native dialogue with lip sync; identity/product locking through Elements; start/end-frame bridging; preserving text already present in an approved start frame [OFFICIAL S1]; fast drafts with Turbo.
- **Weaker at:** no multi-shot switch, reference roles, negative prompt, cfg or camera-control parameter on the Higgsfield MCP [HF S8]; tests report occasional character mix-ups or left-right swaps between shots, a line reassigned to the wrong speaker and an unwanted extra character [SECONDARY S13]; multi-voice dialogue beyond two speakers degraded in 2.6 [OFFICIAL S4] (3.0 claims improvement [OFFICIAL S1]).
- **Choose this model when** you want a polished 3–15 s single shot or start-frame animation with native audio, Element-locked identity/product, or faithful carry-over of text in an approved frame.
- **Choose another model when** you need attached image/video/audio references (Seedance 2.0/2.5), guaranteed multi-shot structure through the MCP (one clip per shot, or a model with exposed multi-shot parameters), editing of footage (`kling_video_edit`, Seedance 2.5) or clips longer than 15 s.

| operation | how to invoke on Higgsfield | notes |
|---|---|---|
| Text-to-video | `model:"kling3_0"` or `"kling3_0_turbo"`, no `medias` | ratios 16:9 / 9:16 / 1:1 |
| Start frame to video | role `start_image` | both ids |
| Start + end frame | `start_image` + `end_image` | `kling3_0` only |
| Element-locked identity/product | `<<<element_id>>>` in the prompt | `kling3_0` only [HF S8] |
| Multi-shot | prompt-level only (unverified) | switch not exposed in the MCP (§3.5) |
| Motion transfer | legacy tool `motion_control` (no prompt) | Genjutsu `hf_mult_motion_control` is Higgsfield's default route [HF S8] |
| Video edit | N/A — see `kling-3-0-omni-edit.md` | |

