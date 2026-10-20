## 1. At a glance

- **Positioning.** "An All-in-One reference-based video generation model that supports Text-to-Video,
  Image-to-Video (first frame/first-last frame), and Reference-based Video Generation. It can generate videos up
  to 30 seconds long at 30fps." [OFFICIAL] Up to 20 reference materials per request upstream, native
  dialogue/BGM/SFX, editing and extension [OFFICIAL]. `wan3.0-video-prime` is the "high-speed version with
  capabilities aligned to the standard version" [OFFICIAL]. GA announced Aug 24, 2026; the API page still says
  "preview" [OFFICIAL].
- **Best for:** 10–30 s single-pass stories; timed multi-shot sequences; locking several people/props/scenes from
  references; voice timbre from audio; motion/camera transfer; regenerating a supplied clip (edit, ≤15 s source);
  "lifelike, diverse human faces" [OFFICIAL]. Artificial Analysis (2026-09-30): #1 text-to-video (Elo 1157), #5
  image-to-video with audio (Elo 1164) [SECONDARY].
- **Weaker at:** on-screen text and audio texture ("improving but not yet where we want them") [OFFICIAL]; exact
  lip sync; long choreography; orbits >45° [OFFICIAL]. Frame modes cannot take references or audio [OFFICIAL].
- **Choose Wan 3.0 when** you need >15 s, multi-reference casting, reference audio, a silent switch, motion
  transfer or a clean re-render of a supplied clip. **Choose another model when** exact in-frame text is required
  (add it in post), or a strict first frame *and* reference images are needed in one call (impossible here).

| operation | how to invoke on Higgsfield | notes |
|---|---|---|
| Text-to-video | `prompt` only | 2–30 s or smart duration; multi-shot by prompt [OFFICIAL] |
| First frame → video | one `start_image` | "pixel-level reproduction" of the frame [OFFICIAL] |
| First + last frame → video | `start_image` + `end_image` | `end_image` alone is not a documented combination [OFFICIAL] |
| Reference-to-video | `image_references` (≤10), `video_references` (≤5, ≤15 s total), `audio_references` (≤5, ≤15 s total) | cite as Image N / Video N / Audio N [OFFICIAL] |
| Audio-driven (lip/beat) | `image_references` + `audio_references` | not with `start_image` [OFFICIAL] |
| Motion / camera / VFX transfer | `video_references` (+ `image_references`) | upstream-documented; Higgsfield routing [INFERRED] |
| Video edit / extension (Edit Mode) | one `video_references` + edit/extend-intent prompt | upstream-documented; not advertised in the Higgsfield catalog description → verify [INFERRED] |
| Document / web-page input | — | N/A on Higgsfield (no `file`/`link` role) [HF] |

