## 1. The state and the files

`state.json → voiceover` holds the choice. A run without the key has no own voiceover (a run made before item 31, Recreate, Edit Mode), and a
resume never asks it again.

| key | value |
|---|---|
| `enabled` | `true` or `false`: the user's answer (Free: `true` only when the requirement asked for it) |
| `method` | `native`, `lipsync` or `overlay` (§2): how the take meets the picture |
| `source` | `elevenlabs` (the pipeline voices each video's lines with the chosen voice) or `file` (the user's own finished voiceover files, one per video, client assets) |
| `model_id` | the ElevenLabs model: `eleven_v4` when `list_models` has it (it takes the emotion tags), else `eleven_v3` |
| `voice_id`, `voice_name` | the run's voice; `voices` maps a character to its own voice, `{"<character>": {"voice_id": "…", "voice_name": "…"}}`, when the user gave pairs |
| `language`, `language_name`, `language_official` | the ISO 639-1 code, its name, and whether it is in the model's official language list (`list_models`) |
| `preference` | the user's words for accent, dialect or delivery (`Scottish accent`, `Kosovar Albanian (Gheg dialect)`, …), or null |
| `settings`, `output_format` | `{"stability": 0.5, "similarity_boost": 0.75, "style": 0, "speed": 1.0, "use_speaker_boost": true}`; `mp3_44100_128` (192 kbps needs the Creator tier, PCM 44.1 kHz the Pro tier) |
| `tier`, `characters_left_at_start` | from `check_subscription` at the start |
| `videos` | Free only: the video numbers the requirement gives a voiceover (absent: every video) |
| `files` | written by `T voiceover record`: one entry per video or clip (`01`, `02-c1`) with the current take's file, sidecar, length, speech span, form and attempt |

Every take is kept in the run as `30-assets/voiceover/video-NN[-cK]-aK.<ext>` beside its sidecar `….json` (the script as sent, the spoken
words, the voice, the settings, the measured phrases and pauses). The ElevenLabs MCP writes only under its own base path
(`ELEVENLABS_MCP_BASE_PATH`, by default the Desktop): `T voiceover outdir` makes the run's folder there, and `T voiceover record` copies each
take into the run.

