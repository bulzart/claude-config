## 9 The Static PC (setup, once per PC)

Static runs where ACE-Step 1.5 (the bed under every video) is installed, FLUX 3 Klein when the images are made on the PC, and with the
ElevenLabs key set (the narration is ElevenLabs', in the model the user picks: nothing of it runs on this PC). `T static check` reports each part; a part
a run needs and does not have is a blocker, reported at the start (never asked); music alone is not: without it the user is told at the
start and the videos go without a bed.
- **The pipeline**: `git pull` of the `~/.claude` repository, as on any PC.
- **Memory guard** (a Windows PC where loading a model can exhaust memory):
  `AWL_MUSIC_PYTHON` and `AWL_IMAGE_PYTHON` may name a small `.cmd` that starts the environment's `python.exe` inside a memory guard (a
  hard cap and a watchdog that stops the job before Windows runs out). Keep such a `.cmd`: pointing the variable at `python.exe`
  instead removes the guard, and everything still seems to work.
- **What a job needs** (the user, 2026-11-09: "this used to work though and i dont know why ace step has to always get 16gb of free
  memory while we did generate before with even lower memory, find the solution, verify it and then mark it on the pipeline";
  measured that day with the guard's `--log`, RTX 3060 12 GB, 16 GB RAM): with Windows' WDDM driver the GPU's memory counts as commit
  memory, so a model on the GPU is charged as commit once; a weights file opened the safetensors way (a copy-on-write map) is charged
  at its full size before a byte is read, so a model loaded that way is charged twice while it moves to the GPU. ACE-Step's own loading
  held its 4.46 GB music model twice (the job at 9.8 GB still loading, 13-15.4 GB at its peak); `music_worker.py` therefore loads the
  low-commit way (each tensor read from its file when asked, straight onto the GPU at the working precision; every weight checked
  identical to the file, 1,352 of 1,352; `T music make`'s answer and the bed's sidecar say `loading`): about 8 GB once loaded and
  about 10.7 GB at most while it makes a 283 s piece, so a bed needs about 13.6 GB free commit with the guard's 3 GB floor (FLUX 3
  Klein about 14.4 GB with one reference, §5).
- **The page file sets the headroom.** Windows' system-managed page file starts small (6.5 GB here) and grows only when the commit
  runs out, which the guard never lets happen; a growth (Windows' "Virtual Memory Minimum Too Low" event: 2026-11-05, 11-07, 11-08)
  lasts until the next restart. So after a restart the same jobs that ran the day before are stopped (2026-11-09, after the 03:37
  restart: 10.75 GB free at rest; the beds of 11-06 and 11-07 were made while the page file was grown). A fixed page file large enough
  for the jobs (the user's setting: System Properties, Advanced, Performance Settings, Advanced, Virtual memory, a custom size on C:,
  then a restart) keeps that headroom across restarts; the guard and its floor stay as they are. On this PC (the user, 2026-11-09:
  "set the bed alocation it need", then the admin prompt approved): C: is a fixed page file of 12,288 MB at least and 16,384 MB at most
  (C: had 17.7 GB free), from the next restart: Windows refused to grow the running page file at once (NtCreatePagingFile
  0xC00000F1), so the commit limit changes only after the restart.
- **ACE-Step 1.5** (the bed under every video): `git clone https://github.com/ace-step/ACE-Step-1.5`, `uv sync` in it (or the Windows portable
  package); never `pip install ace-step` (that is version 1). Then `AWL_MUSIC_PYTHON` = its `.venv\Scripts\python.exe` and `AWL_MUSIC_ROOT`
  = the clone's folder. Its models (about 10 GB) download on first use.
- **OpenAI** (only for images by the API): the user environment variable `OPENAI_API_KEY`; the organisation may need verifying for image
  models. The key is never typed into the chat, printed or written to a run.
- **ElevenLabs** (the narration of every Static video, in the run's narration model: Eleven v4 unless the user picks another, §6 "The
  models"; the user, 2026-11-11: "not always v4, he might use v4 turbo or other"): an API key of the user's
  ElevenLabs account, set once by the user as the user environment variable `ELEVEN_API_KEY` (the toolkit also reads `ELEVENLABS_API_KEY`;
  Windows: Settings, "Edit environment variables for your account", or in their own PowerShell window
  `[Environment]::SetEnvironmentVariable('ELEVEN_API_KEY', '<key>', 'User')`). The toolkit reads a variable set after Claude Code started
  from the stored environment, so no restart is needed; the key is never typed into the chat, printed or written to a run. `T tts check`
  gives the facts: which variable holds the key, the plan, its characters used and left, whether it may clone, and what the run's model
  honours (`config.json → static.tts.elevenlabs`). **The live model list** is the first source of the models and languages the user
  is offered (§6 "The models", "The language of a video"): the ElevenLabs MCP's `list_models` (the `mcp__elevenlabs__list_models` tool,
  loaded with ToolSearch like the voiceover's tools), and, when it does not answer, `T tts models` (the same `GET /v1/models` through the
  key above, free). On this PC the `elevenlabs` MCP server (the local one started with `uvx`, whose tools are `mcp__elevenlabs__…`; not
  the claude.ai ElevenLabs connector) failed `list_models` on 2026-11-11 with "[SSL: CERTIFICATE_VERIFY_FAILED] … unable to get local
  issuer certificate" (the antivirus's web shield re-signs the traffic with its own root and that server's HTTP client trusts only
  certifi's public roots) and, behind that, with `401 invalid_api_key` for the old key its entry held. The user had it fixed that day: its
  entry in their `~/.claude.json` now has `ELEVENLABS_API_KEY` = `${ELEVEN_API_KEY}` (Claude Code fills it from its own environment: the
  key the toolkit uses) and `SSL_CERT_FILE` = `C:\Users\Bulzart\AppData\Local\elevenlabs-mcp\ca-bundle.pem` (certifi's roots plus the
  shield's root; `make-ca-bundle.ps1` beside it builds it again, e.g. after a reinstall of the antivirus); a server that was running
  before such a change is started again with `/mcp`, Reconnect. Whenever the MCP still does not answer, `T tts models` does (the
  toolkit's own call trusts the Windows store). The pipeline never edits that configuration. The plan sets what is
  possible (ElevenLabs' docs and pricing, read 2026-11-09): Eleven v4 bills
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
- faster-whisper's cached `medium` model (the only Whisper model used, item 24) and ffmpeg (with xfade, loudnorm, sidechaincompress, subtitles) as for every run; OpenCV in the
  toolkit's Python (`T edit-profile`); capcut-cli on the PATH.
- **The CapCut check** (maintenance of the catalogue `CS/data/capcut-catalogue.md`, already measured on this PC with CapCut 9.7.0.4153 and kept with this library: a run never does it; it is done once per PC and again after every CapCut update, with the CapCut MCP and the toolkit's own `capcut-check`, the only place those are used; the user, 2026-11-06: "make sure ... what is left to the
  incoming agent is already verified that will work"): a file can look right and play nothing (CapCut 9.7 ignores UNIFORM_SCALE
  keyframes), so what CapCut draws is measured on CapCut's own export. `capcut_clone_draft` of the template into `AWL_capcut_check`,
  `T capcut-prep --canvas 1080x1920`, the four move stills (`runs/_capcut-check/media/check-A.png` and `check-B.png` at 0, 2, 4 and 6 s,
  2 s each) and the grey still (8 s to 53.6 s) with `capcut_add_image`, `capcut_save`; then `T capcut-check fill --draft <it>` (every
  move, every text intro and every transition of capcut-cli's catalogue, each at a known time); the user opens it in CapCut, lets the
  effects load and exports it; `T capcut-check measure --export <the mp4>` writes `CS/data/capcut-catalogue.md` (and `.json`): each
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
  formats, a ring sticker, a click and a noise burst; `runs/_capcut-check/effects/media/`) and writes them the way `T capcut-build`
  does: CapCut's chroma key at two strengths, a cover scale, an overlay's sound and a muted one, the screen blend, each alpha format,
  scale and position keys on an overlay, sound effects on time, at a lower volume and with a fade, and a caption over all of it. The user
  exports it (or, blocked by Pro, records it as above, with the desktop sound: the sounds are measured from it); `T capcut-check
  effects-measure --export <file> [--crop W:H:X:Y]` (a recording is lined up from its first click and the stills' switches) writes the
  `effects` part of the catalogue: which ways play, the chroma strength that left no green, the alpha format CapCut reads.
  `T capcut-build` writes an effect only by a way marked as playing (and free while the run's CapCut plan is free); with no CapCut
  chroma key or screen blend it makes an alpha file of the overlay instead (`30-assets/effects/video-NN/`), when an alpha format plays.
  Measured on this PC 2026-11-06 (CapCut 9.7, its own export; nothing in it Pro): capcut-cli's chroma key and screen blend do not play,
  so green screens and black backgrounds go in as ProRes 4444 alpha files made by ffmpeg (ProRes 4444, QuickTime Animation and PNG-in-MOV
  keep their transparency; VP9 does not); an overlay's sound at volume 0 still played, so overlays go in silent and their sound on an
  audio track; the cover scale, captions above the overlays, scale and position keys on an overlay, sound effects on time (5 ms), their
  volume (-11.9 dB for 0.25) and fades all play.
