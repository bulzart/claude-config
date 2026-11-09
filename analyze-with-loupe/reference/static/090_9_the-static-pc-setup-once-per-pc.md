## 9 The Static PC (setup, once per PC)

Static runs where ACE-Step 1.5 (the bed under every video) is installed, FLUX 3 Klein when the images are made on the PC, and with the
ElevenLabs key set (the narration is ElevenLabs' Eleven v4: nothing of it runs on this PC). `T static check` reports each part; a part
a run needs and does not have is a blocker, reported at the start (never asked); music alone is not: without it the user is told at the
start and the videos go without a bed.
- **The pipeline**: `git pull` of the `~/.claude` repository, as on any PC.
- **Memory guard** (a Windows PC where loading a model can exhaust memory: each load commits about 13 GB of RAM plus page file):
  `AWL_MUSIC_PYTHON` and `AWL_IMAGE_PYTHON` may name a small `.cmd` that starts the environment's `python.exe` inside a memory guard (a
  hard cap and a watchdog that stops the job before Windows runs out). Keep such a `.cmd`: pointing the variable at `python.exe`
  instead removes the guard, and everything still seems to work.
- **ACE-Step 1.5** (the bed under every video): `git clone https://github.com/ace-step/ACE-Step-1.5`, `uv sync` in it (or the Windows portable
  package); never `pip install ace-step` (that is version 1). Then `AWL_MUSIC_PYTHON` = its `.venv\Scripts\python.exe` and `AWL_MUSIC_ROOT`
  = the clone's folder. Its models (about 10 GB) download on first use.
- **OpenAI** (only for images by the API): the user environment variable `OPENAI_API_KEY`; the organisation may need verifying for image
  models. The key is never typed into the chat, printed or written to a run.
- **ElevenLabs** (the narration of every Static video; the user, 2026-11-09: "we will only use elevenlabs v4"): an API key of the user's
  ElevenLabs account, set once by the user as the user environment variable `ELEVEN_API_KEY` (the toolkit also reads `ELEVENLABS_API_KEY`;
  Windows: Settings, "Edit environment variables for your account", or in their own PowerShell window
  `[Environment]::SetEnvironmentVariable('ELEVEN_API_KEY', '<key>', 'User')`). The toolkit reads a variable set after Claude Code started
  from the stored environment, so no restart is needed; the key is never typed into the chat, printed or written to a run. `T tts check`
  gives the facts: which variable holds the key, the plan, its characters used and left, whether it may clone, and what Eleven v4 honours
  (`config.json → static.tts.elevenlabs`). The plan sets what is possible (ElevenLabs' docs and pricing, read 2026-11-09): Eleven v4 bills
  one credit a character; the Free plan has 10,000 a month, no voice cloning, no 44.1 kHz PCM (it gets MP3 at 128 kbps) and no commercial
  licence ("commercial usage rights are only available with paid plans"); 192 kbps MP3 needs Creator, 44.1 kHz PCM needs Pro. The
  Qwen3-TTS environments and models were removed from this PC on 2026-11-09; no local voice model is used.
- **FLUX 3 Klein** (only for images made on the PC; an NVIDIA GPU with 8 GB or more): the ComfyUI Windows portable (0.41.0 or later), and
  in its `ComfyUI\models\` the int8 files of `black-forest-labs/flux-3-image-klein-comfy` on Hugging Face (gated: the user accepts the
  FLUX Kommunity License there and logs this PC in with `hf auth login`; the token never goes into the chat):
  `diffusion_models/flux3-image-klein-int8-convrot.safetensors`, `text_encoders/qwen3vl_4b_int8_convrot.safetensors`,
  `text_encoders/qwen3.5_9b_flux3_prompt_upsampler_w4a8.safetensors` and `vae/flux2-vae.safetensors` (about 18 GB). Then
  `AWL_IMAGE_PYTHON` = its `python_embeded\python.exe` (or a guarded `.cmd`) and `AWL_IMAGE_ROOT` = the portable folder. int8 is the
  build for GPUs without FP8 (the RTX 30 series); the licence allows commercial outputs only for a business under US$5M a year.
- faster-whisper's cached models and ffmpeg (with xfade, loudnorm, sidechaincompress, subtitles) as for every run; OpenCV in the
  toolkit's Python (`T edit-profile`); capcut-cli on the PATH.
- **The CapCut check** (once per PC and again after every CapCut update; the user, 2026-11-06: "make sure ... what is left to the
  incoming agent is already verified that will work"): a file can look right and play nothing (CapCut 9.7 ignores UNIFORM_SCALE
  keyframes), so what CapCut draws is measured on CapCut's own export. `capcut_clone_draft` of the template into `AWL_capcut_check`,
  `T capcut-prep --canvas 1080x1920`, the four move stills (`runs/_capcut-check/media/check-A.png` and `check-B.png` at 0, 2, 4 and 6 s,
  2 s each) and the grey still (8 s to 53.6 s) with `capcut_add_image`, `capcut_save`; then `T capcut-check fill --draft <it>` (every
  move, every text intro and every transition of capcut-cli's catalogue, each at a known time); the user opens it in CapCut, lets the
  effects load and exports it; `T capcut-check measure --export <the mp4>` writes `AWL/data/capcut-catalogue.md` (and `.json`): each
  move played or not, each intro's and each transition's measured shape and whether CapCut drew it. The plans use only what it shows
  drawn, and match a reference's measured entrance and joins to its shapes.
  **Without CapCut Pro** (`config.json → capcut.pro` false) CapCut refuses to export a project that uses a Pro option, and writes which
  ones in `User Data/Cache/FeedbackOtherInfo.json`: the user tries the export once (that list becomes the catalogue's `free plan`
  column), then records CapCut's player full screen from before pressing play to the end, the time bar steady (2026-11-06: a first
  recording with the window moving could not be lined up), with the desktop sound; measure it with `--export <the recording> --crop
  W:H:X:Y` (the player's area; on a 1920x1080 screen with a 9:16 project `608:1080:656:0`) and `--start <second where the project's
  0.0 s plays>`. Each Static run asks for the CapCut plan the user exports with (`state.json → capcut_plan`, free | pro; the user,
  2026-11-06: "make him pick"): free, the agents use only options marked free; pro, the Pro ones too; a run without the key follows
  `config.json → capcut.pro`.
- **The CapCut effects check** (once per PC, after a CapCut update, and before the first run with an effects folder; the user, 2026-11-06:
  "a folder of effects (optional) that can have: sound effects, and green screen transitions"): the same steps into `AWL_effects_check`
  with ten stills of 3 s (`check-A.png` and `check-B.png` by turns, 0 to 30 s), then `T capcut-check effects-fill --draft <it>`: it makes
  test media with known shapes and times (a green-screen wipe with a tone, a glow on black, a red disc on transparent in four video
  formats, a ring sticker, a click and a noise burst; `runs/_capcut-check/effects/media/`) and writes them the way `T capcut-effects`
  does: CapCut's chroma key at two strengths, a cover scale, an overlay's sound and a muted one, the screen blend, each alpha format,
  scale and position keys on an overlay, sound effects on time, at a lower volume and with a fade, and a caption over all of it. The user
  exports it (or, blocked by Pro, records it as above, with the desktop sound: the sounds are measured from it); `T capcut-check
  effects-measure --export <file> [--crop W:H:X:Y]` (a recording is lined up from its first click and the stills' switches) writes the
  `effects` part of the catalogue: which ways play, the chroma strength that left no green, the alpha format CapCut reads.
  `T capcut-effects` writes an effect only by a way marked as playing (and free while the run's CapCut plan is free); with no CapCut
  chroma key or screen blend it makes an alpha file of the overlay instead (`30-assets/effects/video-NN/`), when an alpha format plays.
  Measured on this PC 2026-11-06 (CapCut 9.7, its own export; nothing in it Pro): capcut-cli's chroma key and screen blend do not play,
  so green screens and black backgrounds go in as ProRes 4444 alpha files made by ffmpeg (ProRes 4444, QuickTime Animation and PNG-in-MOV
  keep their transparency; VP9 does not); an overlay's sound at volume 0 still played, so overlays go in silent and their sound on an
  audio track; the cover scale, captions above the overlays, scale and position keys on an overlay, sound effects on time (5 ms), their
  volume (-11.9 dB for 0.25) and fades all play.
