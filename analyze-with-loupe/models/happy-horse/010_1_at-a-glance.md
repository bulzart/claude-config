## 1. At a glance

**Who makes it (evidence).**
- Alibaba Cloud Model Studio publishes official HappyHorse API references (text-to-video, first-frame image-to-video,
  reference-to-video, video editing) and model pages for `happyhorse-1.0-*` and `happyhorse-1.1-*` [OFFICIAL]. An
  Alibaba Cloud blog post (2026-06-23, originally on Alizila) states "Alibaba has released HappyHorse 1.1…
  accessible… via its official website happyhorse.com and through an API on… Model Studio" [OFFICIAL].
- Caixin Global (2026-04-10): "developed by the AI Innovation Division under Alibaba's newly established Alibaba Token
  Hub (ATH) business group" after topping the Artificial Analysis leaderboard under an alias [SECONDARY]. Artificial
  Analysis lists the creator as "Alibaba-ATH" [SECONDARY]; API partner fal attributes it to "the Future Life Lab team
  at Taotian Group (Alibaba), led by Zhang Di" [SECONDARY].
- Open weights: some outlets reported an open-source release; fal says it is "closed source" and "the weights aren't
  publicly downloadable" [SECONDARY, conflicting]. No first-party open-weight release found — treat as closed.

**Positioning.** "Generate physically realistic, motion-smooth video from text prompts"; image-to-video with "highly
realistic dynamic rendering… fluid, natural, and rich in detail" [OFFICIAL]. All HappyHorse models list audio as a
feature; output 24 fps MP4, 3–15 s [OFFICIAL]. Version 1.1 (June 2026) improved reference consistency, "motion
expressiveness", instruction following, visual quality and audio-visual sync [OFFICIAL].

**Which version is on Higgsfield?** Higgsfield exposes 720p/1080p, 3–15 s, a single start frame, and ratios 16:9,
9:16, 1:1, 4:3, 3:4 [HF] — the HappyHorse 1.0 surface (1.1 adds 480P) [OFFICIAL] → most likely 1.0 [INFERRED].

- **Best for:** realistic human-centred single shots, smooth motion, cinematic camera moves; animating an approved
  9:16 still with native sound. Artificial Analysis (2026-09-30): text-to-video — 1.1 #10 (Elo 1046), 1.0 #13 (1024);
  image-to-video with audio — 1.1 #6 (1104), 1.0 #9 (1083); #1 in both categories without audio in April 2026
  [SECONDARY].
- **Weaker at / unknown:** no references, no end frame, no negative prompt, no silent switch, no Edit Mode; no
  official prompting guidance; on-screen text unreliable per partner guidance [SECONDARY]; possible corner watermark.
- **Choose it when** a short, realistic single shot or start-frame animation with sound is enough. **Choose another
  model when** you need references, first+last frames, documented multi-shot syntax, Edit Mode (`wan3_0`,
  `minimax_h3`) or a silent render.

| operation | how to invoke on Higgsfield | notes |
|---|---|---|
| Text-to-video | `prompt` only | ratio from `aspect_ratio` [HF] |
| Start frame → video | one `start_image` (9:16) | output keeps the image's aspect ratio [OFFICIAL] |
| End frame, references, edit, extension | — | N/A on Higgsfield (upstream r2v and video-edit exist, not exposed) [OFFICIAL/HF] |

