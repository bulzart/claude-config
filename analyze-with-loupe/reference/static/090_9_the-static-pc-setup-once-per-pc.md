## 9 The Static PC (setup, once per PC)

Static runs where Qwen3-TTS (and ACE-Step 1.5 when beds are wanted) are installed. `T static check` reports each part; a part a run needs
and does not have is a blocker, reported at the start (never asked).
- **The pipeline**: `git pull` of the `~/.claude` repository, as on any PC.
- **Qwen3-TTS**: its own environment (Python 3.12; a CUDA build of torch and torchaudio from download.pytorch.org; `pip install -U
  qwen-tts`; flash-attn is optional and not used: `sdpa`), then the user environment variable `AWL_TTS_PYTHON` = that environment's
  `python.exe` (and `AWL_TTS_DEVICE` when not `cuda:0`). The models (VoiceDesign and Base, 1.7B) download on first use.
- **ACE-Step 1.5** (only for beds): `git clone https://github.com/ace-step/ACE-Step-1.5`, `uv sync` in it (or the Windows portable
  package); never `pip install ace-step` (that is version 1). Then `AWL_MUSIC_PYTHON` = its `.venv\Scripts\python.exe` and `AWL_MUSIC_ROOT`
  = the clone's folder. Its models (about 10 GB) download on first use.
- **OpenAI** (only for images by the API): the user environment variable `OPENAI_API_KEY`; the organisation may need verifying for image
  models. The key is never typed into the chat, printed or written to a run.
- faster-whisper's cached models and ffmpeg (with zoompan, xfade, loudnorm, sidechaincompress, subtitles) as for every run; capcut-cli on
  the PATH.
