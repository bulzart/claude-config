## 1. Prepared by this session before any agent starts (command A9s)
- **Per video** (A6s, S2):
  - the plan: `40-briefs/video-NN-script.md`, `video-NN-narration.json` and `video-NN-images.json` (the images' prompts, moves, joins,
    labels, drawings places, effects, captions look and bed), the video's brief `40-briefs/video-NN-brief.md` and its forecast
    `video-NN-forecast.json`;
  - the narration `30-assets/narration/video-NN.wav` with its words, cues and `.srt`, the image spans, and the bed
    `30-assets/music/video-NN.wav` (`cs-sound`), when the plan has one;
  - with images by the user, their images taken in by `T image intake`.
- **The run's anchors:** `30-assets/characters/` (the characters' anchors), made once before any agent.
- **The run's agent contract:** `50-requests/agent-contract.md`, generated from the §2s prompt at A9s
  (never copied from an earlier run).
- **Shared, in `state.json`:**
  - `static_images` (`api`, `klein` or `prompts`; the contract's "Images" line), `qc_fixes` (`ask`, `auto` or `off`; the contract's "QC fixes"
    line), `capcut_plan` (`free` or `pro`; the "CapCut plan" line), `static.format` and `static.extra_formats` (the "Formats" line),
    `audio_ingest` (`whisper`);
  - `static.video_info` (each video's own approach and language), `static.voice`, `static.tts_model`, `static.length_plan`, `static.waiting`
    (`images` while the run waits for the user's folder);
  - `videos[]`, appended as each agent reports (§5).
