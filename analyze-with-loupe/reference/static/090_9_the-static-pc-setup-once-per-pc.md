## 9 The Static PC (setup, once per PC)

Static runs where Qwen3-TTS (and ACE-Step 1.5 when beds are wanted, FLUX 3 Klein when the images are made on the PC) are installed.
`T static check` reports each part; a part a run needs and does not have is a blocker, reported at the start (never asked).
- **The pipeline**: `git pull` of the `~/.claude` repository, as on any PC.
- **Qwen3-TTS**: its own environment (Python 3.11 or 3.12; a CUDA build of torch and torchaudio from download.pytorch.org; `pip install -U
  qwen-tts`; flash-attn is optional and not used: `sdpa`), then the user environment variable `AWL_TTS_PYTHON` = that environment's
  `python.exe` (and `AWL_TTS_DEVICE` when not `cuda:0`). The models (VoiceDesign and Base, 1.7B) download on first use. Optional, about
  8x faster: `faster-qwen3-tts` in that environment (it brings `qwen-tts-hf` in place of `qwen-tts`; pin `transformers==5.15.1`, the
  version its README tests); the worker then makes the audio with it on CUDA in bf16 and names the engine in every answer. A seed gives
  the same take again only on the engine that made it; `AWL_TTS_ENGINE=qwen-tts` forces qwen-tts.
- **Memory guard** (a Windows PC where loading a model can exhaust memory: each load commits about 13 GB of RAM plus page file):
  `AWL_TTS_PYTHON`, `AWL_MUSIC_PYTHON` and `AWL_IMAGE_PYTHON` may name a small `.cmd` that starts the environment's `python.exe` inside a memory guard (a
  hard cap and a watchdog that stops the job before Windows runs out). Keep such a `.cmd`: pointing the variable at `python.exe`
  instead removes the guard, and everything still seems to work.
- **ACE-Step 1.5** (only for beds): `git clone https://github.com/ace-step/ACE-Step-1.5`, `uv sync` in it (or the Windows portable
  package); never `pip install ace-step` (that is version 1). Then `AWL_MUSIC_PYTHON` = its `.venv\Scripts\python.exe` and `AWL_MUSIC_ROOT`
  = the clone's folder. Its models (about 10 GB) download on first use.
- **OpenAI** (only for images by the API): the user environment variable `OPENAI_API_KEY`; the organisation may need verifying for image
  models. The key is never typed into the chat, printed or written to a run.
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
