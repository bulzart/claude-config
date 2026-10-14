## 2. Higgsfield parameter surface

### 2.1 Parameters per model id
| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `wan2_6` | `quality` | `720p`, `1080p` | `720p` | "Output resolution / quality." [HF]; the resolution control — always `720p` (§2.6) |
| `wan2_6` | `duration` | `5`, `10`, `15` | 5 | discrete options [HF]; upstream r2v supports only 2–10 s [OFFICIAL] |
| `wan2_6` | `aspect_ratio` | `16:9`, `9:16`, `1:1` | — | always `9:16`; upstream also has 4:3 and 3:4 (not exposed) [OFFICIAL/HF] |
| `wan2_6` | negative_prompt, seed, prompt_extend, shot_type, audio switch, watermark | — | — | not exposed on Higgsfield [HF]; see §2.5 |

### 2.2 Media roles
| role | what it controls | limits / count | notes |
|---|---|---|---|
| `image_references` | appearance of a character/object (r2v) — or possibly the first frame (i2v) | upstream r2v: images 0–5, images + videos ≤5; JPEG/PNG (no alpha)/BMP/WEBP, 240–8000 px, ≤20 MB [OFFICIAL] | "Each reference file should contain only one subject character" [OFFICIAL] |
| `video_references` | appearance **and voice** of a character/object | upstream r2v: videos 0–3, 1–30 s, mp4/mov, ≤100 MB [OFFICIAL] | "Used to extract character appearance and voice (if available)" [OFFICIAL] — not an edit source |
| `audio_references` | soundtrack driving t2v/i2v (upstream `audio_url`) | wav/mp3, 3–30 s, ≤15 MB; truncated to `duration`, silence if shorter [OFFICIAL] | legacy r2v has no audio input [OFFICIAL]; combinations unverified |

`medias[].value` is a Higgsfield media UUID or completed job ID, never a URL [HF].

### 2.3 Duration, resolution, aspect ratio, audio
- **Duration:** 5, 10 or 15 s [HF]. Upstream t2v/i2v 2–15 s; r2v 2–10 s [OFFICIAL] → with references use 5 or 10 s;
  15 s will probably be clamped or rejected [INFERRED].
- **Resolution/aspect:** fixed `quality:"720p"`, 9:16 (§2.6); 30 fps [OFFICIAL].
- **Audio:** the 2.6 standard models "generate videos with audio by default"; only the flash variants can be silenced
  [OFFICIAL]. No switch on Higgsfield [HF] → expect a soundtrack; strip locally if needed [INFERRED].

### 2.4 Call recipes
Text-to-video:
```json
{"model":"wan2_6","prompt":"<PROMPT ≤1500 chars>","duration":10,"aspect_ratio":"9:16","quality":"720p"}
```
Text + audio (duration ≈ audio length):
```json
{"model":"wan2_6","prompt":"<PROMPT>","medias":[{"value":"<AUDIO_MEDIA_ID>","role":"audio_references"}],"duration":10,"aspect_ratio":"9:16","quality":"720p"}
```
Reference-to-video (order = character number: first → character1):
```json
{"model":"wan2_6","prompt":"<PROMPT using character1, character2>","medias":[{"value":"<VIDEO_MEDIA_ID>","role":"video_references"},{"value":"<IMAGE_MEDIA_ID>","role":"image_references"}],"duration":10,"aspect_ratio":"9:16","quality":"720p"}
```
Preflight with `get_cost: true` [HF]. A completed job ID may be used as a media `value` [HF].

### 2.5 Parameter gotchas
1. **Resolution is `quality`**, not `resolution` [HF].
2. **No start-frame role.** Whether an `image_references` item goes to i2v (first frame) or r2v (subject) is
   undocumented [HF silent]; run a 5 s/720p test and check frame 1 before relying on either [INFERRED].
3. **Multi-shot may be forced off.** Upstream `shot_type` defaults to `single` and "overrides the prompt. Setting
   shot_type to single produces a single-shot video even if the prompt requests multi-shot"; `multi` works only with
   `prompt_extend: true` [OFFICIAL]. Neither is exposed [HF] → design one continuous shot unless tested [INFERRED].
4. **Prompt budget 1,500 characters** (≈220–250 English words), auto-truncated [OFFICIAL]; put exclusions early.
5. **Character numbering spans images and videos together:** "The first URL maps to character1, the second to
   character2" [OFFICIAL]; how Higgsfield orders mixed-role `medias` is unknown [INFERRED risk].
6. **Hidden upstream defaults:** `prompt_extend` true, `watermark` false, random seed [OFFICIAL]; none exposed [HF].

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-pick)
| mode | params | expected output | action |
|---|---|---|---|
| Text-to-video (± audio) | `"aspect_ratio":"9:16","quality":"720p"` | 720×1280, 30 fps (upstream size table: 720*1280 = 9:16) [OFFICIAL] | verify |
| Reference-to-video | same params | 720×1280 (r2v size table lists 720*1280 as 9:16) [OFFICIAL] | verify |
| If an image reference is used as a first frame (unverified route) | same params | output follows the image's aspect [OFFICIAL i2v] | supply 9:16 reference images |

Finish with `atp.py conform --video "<in>" --out "<out>"` (scale-to-cover + focus crop to exactly 720×1280, never
stretched; a no-op when already exact). Expected loss ~0%; if `conform` refuses (>12% loss), the output was not 9:16 —
regenerate with 9:16 inputs [INFERRED].

