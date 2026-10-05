# SEEDANCE-SPEC.md — Seedance 2.5 specification notes for the analyze-stack pipeline

## 0. Header

- **VERSION BASIS: Seedance 2.5** (ByteDance Seed; official launch 2026-07-31 on Jimeng/Doubao; public developer API on Volcano Engine / BytePlus ModelArk as model `dreamina-seedance-2-5-260628` / `doubao-seedance-2-5-260628`). Where 2.5 documentation is silent, Seedance 2.0-series documentation is used and marked as such; 1.5-pro / 1.0-pro documentation is used only for camera/voice vocabulary that the 2.x guides explicitly link to.
- **Compiled: 2026-09-16** by research agent R2. Sources are numbered (S = official ByteDance/Seed/BytePlus/Dreamina/CapCut, P = serving platform, C = community) and listed in `sources.md`.
- **READ-ONLY NOTICE: do not refresh or edit this file during `/analyze-stack` runs; only on explicit owner request.** The command (there is one; it never runs as a Workflow) loads it read-only; every generated prompt is derived from it. The prompt-engineering METHOD lives next door in `director\` (§14): this file owns the numbers, the director bundle owns the way prompts are planned, written and audited.
- Tags: `[official]` = ByteDance/Seed/BytePlus/Dreamina/CapCut; `[platform:<name>]` = a third-party or first-party serving platform's own parameter surface; `[community]` = unofficial; `[single-source]` = only one source states it; `[inferred]` = my inference, not stated anywhere.
- How the official docs were obtained: the BytePlus ModelArk doc pages are JavaScript-rendered; the article bodies were retrieved with a crawler user-agent and extracted from the embedded page JSON (the `MDContent` field), so the quotes below are the literal doc text as of the fetch date.

---

## 1. Model overview

| Version | Release | What it is | Key facts |
|---|---|---|---|
| Seedance 1.0 (pro / pro fast / lite) | June 2025 [official S15, S20] | Text/image-to-video, 1080p, native multi-shot, 24 fps | Camera-movement vocabulary responds reliably; `--camerafixed` text command existed; durations 2–12 s on API [official S3, S6]. Base generation 480p upscaled by a diffusion refiner [official S15]. |
| Seedance 1.5 pro | Dec 2025 (model id `seedance-1-5-pro-251215`) [official S6; date inferred from model id] | Adds joint audio-video generation (dialogue, multilingual, dialects), draft mode | 4–12 s, 480p/720p/1080p, `camera_fixed`, `seed` params [official S3, S9]. |
| Seedance 2.0 (std / fast / mini) | Released in China 2026-02-10/12 (Seed blog page says Feb 12; arXiv says "early February 2026") [official S12, S14] | "Unified multimodal audio-video joint generation architecture"; four input modalities (text, image, audio, video) | Up to 9 images + 3 videos + 3 audio references (15 assets), 4–15 s, 480p/720p native (std also outputs 1080p and 4K on API), video editing + extension, multi-shot, dual-channel audio, dialects/opera/singing [official S12, S14, S3, S6]. |
| **Seedance 2.5** | Announced 2026-06-23 at Volcano Engine FORCE (Beijing) [community C13]; **official launch 2026-07-31** on Jimeng and Doubao [official S11]; API on ModelArk documented by Sep 2026 [official S2] | "Builds on the unified multimodal audio-video joint-generation architecture of Seedance 2.0 … centers on foundational generation and reference-based generation, delivering major breakthroughs in long-form storytelling, multimodal reference, and editing" [official S11] | **30 s single-pass**, **50 reference assets (30 images + 10 videos + 10 audio)**, integer-second timestamp control, multi-view subject references, audio-only reference input, 11 native languages, MOV output, locked-parameter editing/extension tasks, 3D clay-model (white-box) references, storyboard and keyframe references, seamless transition between two videos, one-click video from stills [official S1, S2, S11]. |

What changed 2.0 → 2.5 (official wording, S1 "Differences from Seedance 2.0" + S2 "Latest capabilities"):
1. "Timestamp support: Seedance 2.0 does not respond to timestamps and only responds to shot numbers, while Seedance 2.5 supports integer-second timestamps."
2. "Multi-view image support: Seedance 2.0 does not recommend using multi-view images as subject references, while Seedance 2.5 supports them."
3. "Flexible aspect ratios: Seedance 2.0 only supports six fixed output aspect ratios, while Seedance 2.5 can support any output aspect ratio between [0.4, 2.5] by controlling the input assets."
4. "Improved V2V quality: Seedance 2.5 supports MOV output, which better preserves color consistency, brightness consistency, and audio-visual consistency in extension and editing tasks."
5. Duration 15 s → 30 s; reference images 9 → 30; reference audio/video 3 → 10 each; total reference A/V duration 15 s → 30 s; "Native multilingual support: Supports 11 languages" [official S2].
6. Seed's own framing: "Seedance 2.5 is not a cross-generational leap in the same way that 2.0 was compared with 1.5 … systematic enhancements for real production scenarios" [official S1].

Acknowledged limitations at launch: "room for improvement, particularly regarding the physical plausibility of complex motions and the stability of scenes involving interactions among multiple subjects" [official S11]. For 2.0: "detail stability, hyper-realism, and dynamic vitality … occasional audio distortion … multi-subject consistency, text rendering accuracy, and complex editing effects" [official S12]; "minor deformation artifacts, motion plausibility in edge cases, high-frequency visual noise, audio distortion and noise, and lip-sync errors in multi-speaker scenes" [official S14].

Marketing-only claims to treat with care: "native 4K", "10-bit", "20% better prompt adherence", "180 s beta long-video mode" appear on consumer/marketing pages (Dreamina S16, Krea P17, Higgsfield P4, TheNextWeb C13) but **not** in the ModelArk API docs, which cap 2.5 at 1080p and 30 s (see Discrepancies, section 13).

---

## 2. Output specs

### 2.1 Duration
- **Seedance 2.5: 4–30 s (integer seconds) or `-1` = model picks the length.** "Default `-1`; supports `[4, 30]` or `-1`" [official S3]; "Duration: 4–30 s" [official S6]; agreed by fal ("auto" or "4"–"30") [platform:fal P6, P7], Higgsfield MCP (4–30, default 5) [platform:Higgsfield P1], Replicate (-1..30, default 5) [platform:Replicate P11], Krea (4–30, default 5) [platform:Krea P18], WaveSpeed (4–30, default 5) [platform:WaveSpeed P13].
- No sub-second step on 2.5: the `frames` parameter (25+4n frames, 24 fps) exists only for Seedance 1.0 pro [official S3]. Returned `duration` = floor(total frames / 24) [official S3].
- **Video-editing tasks: duration is locked** — "`duration` must be `-1`"; output ≈ input length, "may be about 0.4 seconds shorter" (API) / "up to about 0.3 seconds" (prompt guide); zero drift if the edited video was itself generated by 2.5 [official S1, S2, S3]. Editing input must be 4–30 s.
- Extension and first/last-frame tasks: duration user-defined [official S1, S2].
- Seedance 2.0 series: 4–15 s (default 5) [official S3, S6]; Higgsfield seedance_2_0 4–15 [P1]; Seedance 1.5 pro 4–12; 1.0 pro 2–12 [official S3].
- Longer than 30 s: officially via "multi-round extension" ("can append subsequent shots for several minutes") [official S11] or the platform's own stitching; Dreamina/Krea/Wikipedia mention a "beta long-video mode up to 180 s" [platform:Dreamina S16; P17; C12] — not in the API docs.

### 2.2 Resolution
- **Seedance 2.5 on ModelArk: `480p` (8-bit), `720p` (8-bit, default), `1080p` (10-bit colour, H.265/HEVC)** [official S2, S3, S6]. "No 4k" for 2.5 (4K is a Seedance 2.0-std-only option, 10-bit) [official S3, S6; community C4 agrees].
- Pixel dimensions for 2.5 (width × height) [official S2, S3]:

| Ratio | 480p | 720p | 1080p |
|---|---|---|---|
| 16:9 | 854×480 | 1280×720 | 1920×1080 |
| 4:3 | 752×560 | 1112×834 | 1664×1248 |
| 1:1 | 640×640 | 960×960 | 1440×1440 |
| 3:4 | 560×752 | 834×1112 | 1248×1664 |
| 9:16 | 480×854 | 720×1280 | 1080×1920 |
| 21:9 | 992×432 | 1470×630 | 2206×946 |

  (fal lists 480p 16:9 as 864×496 and 9:16 as 496×864, i.e. the Seedance 2.0 grid [platform:fal P8]; the 2.5 grid above is the ModelArk one.)
- Per platform: fal 480p/720p only (default 720p) [P6, P7, P8]; Replicate 480p/720p [P11]; Higgsfield MCP `seedance_2_5` 480p/720p/1080p (default 720p) [P1]; Krea 480p/720p/1080p ("stops at 1080p and has no upscale flag") [P18]; WaveSpeed 480p/720p/1080p/**4k** (its own price tier; contradicts ModelArk) [P13, P14]; Higgsfield web "up to 4K upscaling" [P4]; Dreamina "4K output" [S16] (consumer app; presumably an upscale step — [inferred]).
- 1080p on 2.5 is 10-bit HEVC: "may not be compatible with some playback environments" (VLC/mpv/QuickTime recommended) [official S2, S3]. For our editing stack, prefer 720p 8-bit H.264 for QA passes and 1080p only for the final render, or transcode with ffmpeg [inferred].

### 2.3 Aspect ratio
- **Values: `16:9`, `4:3`, `1:1`, `3:4`, `9:16`, `21:9`, `adaptive`; default `adaptive` on 2.5** [official S2, S3]. `adaptive` for text/reference tasks = "Select the most suitable aspect ratio from the optional aspect ratios … based on the prompt" [official S2].
- **Locked tasks — `ratio` must be `adaptive`:** first-frame / first-last-frame (output takes the first-frame image's ratio), video editing and video extension (output takes the source video's ratio) [official S1, S2, S3]. This is how 2.5 reaches "any output aspect ratio between [0.4, 2.5]" [official S1].
- Platform names: fal `aspect_ratio` ∈ {auto, 21:9, 16:9, 4:3, 1:1, 3:4, 9:16} default "auto" [P6–P8]; Higgsfield `aspect_ratio` ∈ {auto, 21:9, 16:9, 4:3, 1:1, 3:4, 9:16} [P1]; Replicate `aspect_ratio` ∈ {16:9, 4:3, 1:1, 3:4, 9:16, 21:9, adaptive} default 16:9 [P11]; Krea default 16:9 [P18]; WaveSpeed t2v default 16:9 [P14]. fal's learn page says only "16:9, 9:16, or auto" for some endpoints [P9] — the schema pages list all six.
- Portrait note: "the probability of generating subtitles in landscape is significantly lower than in portrait" — official workaround is to generate landscape and crop [official S4] (2.0 FAQ). For a 9:16 TikTok deliverable this is a trade-off; see section 9.

### 2.4 Frame rate
- **24 fps, fixed** for every Seedance model on ModelArk [official S6]; the API's duration math uses 24 [official S3]. Reference *input* videos may be 24–60 fps [official S2, S3]. Dreamina's "60 FPS premium tier" [S16] is a consumer-app post-process ([inferred], not in API docs). [community C4 agrees: "fixed 24 fps, `frames` not supported"].

### 2.5 Watermark
- `watermark` boolean, **default `false`**; `true` = "An `AI Generated` watermark will be displayed in the lower right corner" [official S2, S3]. Replicate `watermark` default false [P11]. Returned last frame (`return_last_frame`) is always watermark-free PNG [official S3].
- Prompt-level: "do not generate a watermark" / "do not generate a logo" are recommended constraint words because references can leak platform logos [official S4].

### 2.6 Seeds / reproducibility
- ModelArk `seed` integer `[-1, 2147483647]`, default -1; "same seed value → similar results, but complete consistency is not guaranteed". **Listed supported models: Seedance 1.5 pro, 1.0 pro, 1.0 pro fast — the 2.x models are not listed** [official S3]. Platforms do expose a seed for 2.5: fal `seed` (returned in output) [P6, P7], Replicate `seed` ("Reproducibility is not guaranteed") [P11], Krea `seed` [P18]. Treat seed reuse as a weak tool on 2.5 (see Discrepancies).

### 2.7 Output container / audio format
- `output_format`: `mp4` (default, H.264) or `mov` (H.264 + yuv444p + PCM; 2.5 only) — "recommended to use the mov format as input and output in video editing and video extension scenarios" [official S2, S3]. 1080p mp4 is HEVC 10-bit [official S2].
- **Audio track is mono**: "All generated videos with audio are mono, regardless of the number of channels of the input audio" [official S3]. (Seed blog / arXiv describe 2.0's audio module as "dual-channel"/"binaural" [S12, S14] — model capability vs API delivery; see Discrepancies.)
- Video URL retention 24 h, max 100 downloads; task records 7 days [official S2].

### 2.8 Throughput and generation time
- ModelArk rate limits for 2.5: enterprise 600 RPM / 10 concurrent; individual 180 RPM / 3 concurrent [official S2, S6]. Offline (`flex`) tier not supported for 2.x [official S3].
- Generation time is **not documented officially**. Platform/community observations: a 30 s 1080p clip "averaged 10+ minutes" on Krea [platform:Krea P18]; "~60 seconds to 10 minutes" [community C-Renderforest P20]; 2–5 min for 2.0 on Dreamina [community C7]. [single-source each]
- Indicative prices: fal 720p ≈ $0.473/s, 480p ≈ $0.2205/s, tokens = (h×w×duration×24)/1024 at $0.0214/1k tokens; video references bill input seconds ×0.6 [platform:fal P6, P7]. WaveSpeed t2v 480p $0.18/s, 720p $0.36/s, 1080p $0.90/s, "4k" $1.80/s; edit/extend $0.11–$1.10/s on input+output [P14–P16]. Higgsfield 10 s clip: 480p 30 credits ($1.50), 720p 65 ($3.25), 1080p 90 ($4.50) [P4]. Atlas "from $0.134/s" [P19]. APIYI relay ≈ $1.37 per 720p/5 s [C4].

---

## 3. Inputs

### 3.1 Allowed input combinations (ModelArk `content[]`) [official S3]
"Text · Text (optional) + image · Text (optional) + video · Text (optional) + audio (Dreamina Seedance 2.5 supports audio-only input) · Text (optional) + image + audio · Text (optional) + image + video · Text (optional) + video + audio · Text (optional) + image + video + audio · Sample task ID (1.5 pro only)."

Task types 2.5 recognises (from assets + prompt intent) [official S2]:
| Task | Trigger | Constraints |
|---|---|---|
| Text-to-video | text only | none on `ratio`/`duration` |
| First-frame / first-last-frame | `content.role` = `first_frame` (+ `last_frame`) | `ratio` must be `adaptive` |
| Omni reference → reference-to-video | ≥1 asset with role `reference_image` / `reference_video` / `reference_audio` | none |
| Omni reference → **video editing** | ≥1 `reference_video` + editing intent words ("edit video, add, insert, remove, delete, modify, replace, change to") | `ratio`=`adaptive`, `duration`=`-1`, source video 4–30 s |
| Omni reference → **video extension** | ≥1 `reference_video` + extension words ("extend forward/backward, continue, continue from, extend the story") | `ratio`=`adaptive` |

`omni_reference_task_type` ∈ {`auto` (default), `reference`, `edit`, `extend`} validates the constraints at submit time; a mismatch between declared and detected intent still fails asynchronously (`InvalidParameter.TaskTypeMismatch`) [official S2, S3]. Recommended generic config: `omni_reference_task_type=auto`, `ratio=adaptive`, `duration=-1` [official S2].

**First/last-frame mode and omni-reference mode are mutually exclusive** — "cannot be mixed" [official S3]; Replicate echoes ("Cannot be combined with reference images, videos, or audios") [P11]. Workaround: put everything in as `reference_image` and say in the prompt "Image 1 is the first frame" / "Image 3 is the first frame, and Image 5 is the last frame" — "does not lock the output video's aspect ratio … may not match them exactly" [official S1, S3]. Higgsfield's MCP exposes `start_image`, `end_image`, `image_references`, `video_references`, `audio_references` roles on the same model [platform:Higgsfield P1]; whether it allows mixing is not documented [gap].

### 3.2 Images [official S2, S3]
- Roles: `first_frame`, `last_frame`, `reference_image`.
- Formats: jpeg, png, webp, bmp, tiff, gif, heic, heif. Input as URL, Base64 (`data:image/png;base64,…`), or `asset://` ID.
- Aspect ratio (w/h) 0.4–2.5; width and height 300–6000 px; each < 30 MB; request body ≤ 64 MB.
- Counts: first frame 1; first+last 2; **omni reference 1–30 (2.5)** / 1–9 (2.0 series). Total assets of all kinds ≤ 50 [official S1, S2, S11].
- First and last frame "can be identical"; if ratios differ "the first frame image takes precedence, and the last frame image will be automatically cropped" (API) / "will be stretched" (prompt guide) — use same-ratio pairs [official S3, S1].
- Reference-image roles the model understands: subject appearance/identity, scene/location, style, prop/product, storyboard grid, keyframes, first/last frame [official S1 capability table].
- Recommended counts: **1–8 image subjects** ("You may try 9–12 subjects, but stability may decrease") ; > 5 subjects → single-view images, split viewpoints into separate images rather than one multi-view sheet [official S1]. 2.0 guide: use a headshot + full-body photo per character, put the headshot first, avoid multi-view sheets on 2.0 [official S4].
- Storyboard images: ≤ 15 panels, stick-figure/line-art, no text on the storyboard, cannot be strictly aligned (use keyframes for strict alignment) [official S1].
- Faces: "Seedance 2.5 does not support directly uploading reference images or videos containing real human faces" [official S2, S3, S8]. Allowed: face-containing outputs generated by Seedance 2.5/2.0 under the same ModelArk account within 30 days (and their returned last frames, and Seedream 5.0 lite images), preset digital characters (`asset://`), or verified/authorized real-person assets [official S8]. Dreamina's consumer app also restricts photorealistic faces [community P20]. Higgsfield/fal/Replicate/WaveSpeed do not document a face block [gap].

### 3.3 Video references [official S2, S3]
- Role: `reference_video` (fixed). Formats mp4 / mov; codecs H.264 or H.265; audio AAC/MP3 (PCM in mov).
- Input resolution: API page says 480p, 720p, 1080p, 4k; tutorial page says 480p, 720p (see Discrepancies). Dimensions 300–6000 px, ratio 0.4–2.5, total pixels 407,696–8,295,044; ≤ 200 MB; 24–60 fps.
- Duration: **each 2–30 s (non-editing) / 4–30 s (editing); up to 10 videos; combined ≤ 30 s** (2.5). 2.0: each 2–15 s, ≤ 3 videos, ≤ 15 s total.
- What a video reference can supply: "subject, camera movement, action performance, and overall style" [official S5]; "action/expression/camera movement/creativity/effects"; motion + subject; 3D clay-model motion; style; storyboard; source for editing/extension; two clips for a seamless transition [official S1].
- Recommended: 1–5 subjects per A/V reference (6–10 possible), **5–10 s per clip** ("Longer inputs may reduce stability"); editing source ≤ 20 s [official S1].
- fal: each video/audio reference 1.8–30.2 s, combined ≤ 30.2 s per list; video references "should carry camera movement OR performance, not both" [platform:fal P9, P10].

### 3.4 Audio references [official S2, S3]
- Role: `reference_audio`. Formats wav, mp3; each 2–30 s; **up to 10; combined ≤ 30 s**; ≤ 15 MB each. 2.5 accepts audio-only input; 2.0 requires an image or video alongside. fal: "Audio references require at least one accompanying image or video" [P9] and Replicate says the same [P11] — platform behaviour differs from ModelArk 2.5 here (see Discrepancies).
- What it supplies: "timbre, music melody, and dialogue content" [official S5]; "music/melody/dialogue/voice" [official S1]; rhythm/beat sync ("synchronize the background sound effects with @Audio 1") [official S4].

### 3.5 How references are cited inside the prompt
- **Official rule (2.5):** "Use `@Image 1`, `@Video 1`, and `@Audio 1` to refer to reference assets. Specify what each asset provides, such as appearance, action, or timbre, and what should not be referenced." [official S2]. The 2.5 prompt guide itself mixes `@Image 1`, `@Image1`, `Image 1`, `[Video 1]`, `@video1` — all are accepted forms of "asset type + number" [official S1].
- **Numbering = upload order within the same type**: "'Image n' refers to the nth reference image with `type="image_url"` in the `content` array (counting starts from 1 in array order). Note that referencing assets by Asset ID is not supported." [official S5, S8]. So images, videos and audio each have their own 1-based sequence.
- Never put the mapping only inside the image ("avoid writing 'John' on the protagonist's image") [official S1].
- Bind every asset explicitly, one line each; for many characters use a list [official S1]:
  - "The knight in Image 1"
  - "Images 1-2 are Character 1 and correspond to Audio 1; Images 3-4 are Character 2 and correspond to Audio 2."
  - "Image 1 depicts the protagonist John and uses the voice timbre from Audio 1."
  - "Refer to the action of casting the spell in Video 1 and the wrap-around camera movement in Video 2."
  - "Refer to Image 1 for lighting and filters."
- Say which part to use and which not: 2.0 formula "Define `[Core_Subject_Features]` in `Image 1` as `Subject 1`" with 2–3 stable static features; "Define the woman wearing a red dress and a straw hat in Image 1 as Zhang Hong"; for simple cases "Zhang San@Image 1" each time the subject is mentioned [official S4].
- When the reference is already exact, don't re-describe it: "Strictly refer to the actions and camera movements in Video 1, and keep the sequence consistent with the video" [official S1].
- Editing/extension: name the video directly ("Edit Video 1 …", "Extend Video 1 backward …"); "Do not use 'reference Video 1'" or it may be classified as a reference task [official S4].
- Platform syntax: fal schema says "Address references as `[Image1]`, `[Video1]`, `[Audio1]`" and its examples use brackets [platform:fal P6]; fal's learn/prompting pages use `@Image1` [P9, P10]; Replicate `[Image1]` [P11]; WaveSpeed `@image1` [P14, P16]; Higgsfield `@Image 1` [P4; community C8]; Dreamina/CapCut `@Image1` [official S16, S17, S18]; Krea passes arrays and shows no in-prompt notation [P18]. All are positional aliases of the same "type + number" concept; use `@Image 1` (official 2.5 wording) unless a platform's schema says otherwise.
- Ordering priority: "The more an asset requires precise reference, the earlier it should be placed in the prompt" [official S4]; upload character identity refs first, then scene, then motion video, then audio [inferred from S4's recommended 4–5-asset configuration].

### 3.6 Text prompt [official S3]
- `content[].type = "text"`. Languages: English always; 2.5 additionally Spanish, Indonesian, Portuguese, Japanese, Malay, Thai, Arabic, Vietnamese, Korean (and Chinese).
- **Recommended length: "no more than 500 Chinese characters or 1,000 English words. Lengthy text will lead to scattered information, and the model may ignore details and only focus on key points."**
- Legacy inline commands (`--ratio/--rt`, `--resolution/--rs`, `--duration/--dur`, `--seed`, `--camerafixed/--cf`, `--watermark/--wm`) belong to 1.x; on 1.5 pro they are the "Legacy way" and the request-body fields are "Strongly recommended" [official S9, S10, S20]. **Not documented for 2.x; do not put resolution/ratio/duration in 2.5 prompt text** [community C3, C8 agree: "Don't include resolution, frame rate, aspect ratio in prompt text"].

---

## 4. Native audio

- Parameter `generate_audio` (default `true`): "The model will automatically generate matching human voice, sound effects and background music based on the text prompt and visual content. **It is recommended to put dialogue content in double quotes to optimize the audio generation effect.** For example: The man stopped the woman and said: "Remember, you can't point at the moon with your finger in the future."" `false` → silent video [official S3]. Output is mono [official S3]. fal: "Put spoken dialogue in double quotes for lip-synced audio" [P7, P8]; Replicate: "dialogue (use double quotes in prompt)" [P11].
- **Bracket convention (official 2.5 prompt rules):** "Use `()` for music, `<>` for sound effects, `{}` for dialogue, and `【】` for subtitles. For non-Chinese dialogue, it is recommended to specify the language before the dialogue." [official S2]. 2.0 guide table: Music `（）` "（fast-paced rock music is playing in the background）"; Dialogue `{}` "{Hello, world}. If the dialogue is in a less common language (neither Chinese nor English), the language must be marked, such as: says in Japanese {こんにちは}"; Subtitles `【】` "【Chapter One: Departure】" [official S4]. Official examples use both `{…}` and `"…"` for lines (e.g. 2.0 dorm drama uses `{How did the exam go? Did you pass?}`; the 2.5 rocket storyboard uses `Dialogue (elderly woman): "Fly safe, my child. Come back to me."`). Either works; braces are the disambiguating form when music/SFX/subtitle brackets are also present.
- **Speaker + language + delivery before the line** (1.5-pro guide, reused by 2.x): "In a gentle emotional state, with a soft tone and a slow speaking pace, say: "You can take your time. I'm not rushing you."" ; multi-speaker blocks as `Man: "…" / Woman: "…"` with "English dialogue:" header; "Accurately specify each character's personalized attributes (gender, age, clothing, actions)" so lips match the right person [official S9]. Voice-timbre reference: "'Character' says: 'lines', voice timbre references 'Audio n'" and add voice descriptors — "Use the low, thick, warm, and finely grainy middle-aged male voice of @Audio 1 to say" [official S4, S5].
- Languages: 11 native for 2.5 — Chinese, English, Spanish, Indonesian, Malay, Thai, Arabic, Portuguese, Vietnamese, Japanese, Korean [official S2, S3]; 2.0 also handles Chinese dialects (Sichuan, Northeastern, Cantonese), opera, singing, rap [official S12, S14]. Official rap example: eight "hello" lines in eight languages with "precise lip sync", hard cuts on the beat [official S2].
- Keep one dialogue language per video: "The language of dialogue must be consistent, and mixing Chinese and English should be avoided (except for proper nouns)" [official S4].
- Lip sync quality: strong for single speakers; "lip-sync errors in multi-speaker scenes" and "audio distortion and noise" listed as areas for improvement [official S14]; community: ≤10 words per line, ~20 spoken words per 15 s, lock the camera on a medium close-up while speaking, "no exaggerated mouth opening, no head turns while speaking" [community C7]; state who speaks and that other mouths stay closed [platform:fal P10].
- Timing of speech: 2.5 timestamps can place lines ("0-3 seconds: she looks into the phone camera and says, "…"") [platform:fal P10]; official 2.5 examples attach lines to shots ("Shot 3 (6-10s): … Dialogue (elderly woman): "…"") [official S1]. Community: keep dialogue in the first two-thirds and end on a silent held beat to avoid cut-off speech [community C7]; official FAQ: "abrupt clicking sounds and cut-off noise are likely to appear at the end of the video" when there is narration — regenerate or fade out in the NLE [official S4].
- Sound effects / ambience / music: write them as events in the timeline ("Sound effects: roaring heat waves and a slightly exaggerated dry cracking sound", "Sound effect: a 'ding' discovery sound … followed by half a second of silence") [official S2 grapefruit example]; "Natural environmental audio only, including wind, rustling grass, and the soft plop of the panda rolling" [official S1]. BGM is generated by default; style and pacing are controllable in text ("accompanied by a heart-stirring symphony", "clap hands in time with the drumbeats") [official S9]; audio references drive melody/beat ("synchronize the background sound effects with @Audio 1") [official S4].
- **Negative audio control (officially supported):** "No BGM; generate only environmental sounds and action sounds." · "No audio." · "No subtitles." / "Do not add subtitles." [official S1]. Community stack for UGC: "No music, no library audio, no voiceover narration, no on-screen text, no subtitles, no logo" plus a mix ranking sentence "Dialogue clean and prominent, ambient … subtle" [community C7].
- Volume/mute: no per-track volume parameter exists; extension outputs "may differ slightly" in loudness from the source (smaller if the source was 2.5-generated) [official S1]; the only hard mute is `generate_audio=false` [official S3]. Audio editing tasks can add/remove/modify vocals, music, SFX ("remove the background music from @Video 1"; "Translate the spoken dialogue in the video into Chinese, with no subtitles. Precisely adjust the lip movements to match the translated speech") [official S1, S2].
- Pronunciation: replace hard-to-read Chinese characters with common homophones [official S4]; use common words, avoid rare glyphs for on-screen text [official S4].

---

## 5. Camera control vocabulary

Official statement: "Basic camera and shot terms can be written directly … For overly niche or technical terms, convert them into [term + descriptive explanation]" [official S1]. "The model has a strong understanding of camera movement terms, so you can directly use standard camera movement terminology" [official S4]. Report: "Advanced camera movement is the hardest sub-category … no model exceeds 3.14 [/5] on any metric" [official S14] — keep camera work simple and singular.

| Intent | Official wording (quote where possible) | Source |
|---|---|---|
| Static / locked camera | "fixed camera position", "fixed shot" [S4]; "[Wide shot, locked-off camera, eye-level, rule-of-thirds composition]" [S1]; "Macro insert shot, locked-off camera" [S2]; "a static shot" [S9]; "The camera never moves. The column remains fixed." [P10] | official S1, S2, S4, S9; platform P10 |
| Push in | "push in" [S1]; "slow push-in" [S4]; "The camera quickly pushes into a close shot" [S10]; "dolly-in" [S9] | official |
| Pull out | "pull out" / "pull back" [S1]; "The camera quickly pulls out, revealing…" [S10]; "dolly-out"; "the camera gradually zooms back … dolly out steadily" [S9] | official |
| Pan | "pan" [S1]; "the camera pans right to shoot…" [S10]; "Pan Left/Right" [S10] | official |
| Tilt | "tilt up" [S1]; "handheld camera slowly tilting downward"; "handheld fast tilt-up" [S1, S2]; "Rise/Fall" [S9] | official |
| Tracking / follow | "track", "follow" [S1]; "smooth lateral tracking" [S4]; "Tracking Shot … Truck Left/Right"; "the camera follows the flying lion" [S10]; "The camera follows steadily in a medium shot" [S4] | official |
| Orbit / arc | "orbit" [S1]; "circles halfway around her, moving from the front to her back" [S4]; "Circle around … from the woman's back to her front" [S10]; "Surround"; "slow, close-range 360-degree pan around them" [S9, S10] | official |
| Dolly zoom | "Hitchcock zoom/dolly zoom" [S1]; "Hitchcock shot = dolly-in/out + zoom-out/in"; "Keep the girl's main composition unchanged, dolly out + increase the focal length of the lens" [S9] | official |
| Handheld | "handheld shake", "handheld shot" [S1]; "slight handheld feel"; "Handheld cinematography with breathing-like camera shake" [S1]; "aggressive handheld push-in" [S2]; "A handheld camera rapidly tracks forward, with slight realistic camera shake" [S4] | official |
| Crane / rise | "Rise" [S9, S10]: "The camera rises, and between the main branches…"; "the camera should quickly fly upward to the top, rapidly turn back, and then dive vertically downward" [S1] | official |
| Drone / aerial | "aerial perspective" [S1]; "From a drone perspective, it overlooks the entire cliff" [S4]; "Aerial shots from high above" [S10]; "bird View" [S9] | official |
| POV / FPV | "first-person perspective" [S1]; "FPV" [S1]; "first-person diving perspective" [S4]; "xx Subjective View" [S9] | official |
| Rack focus | "Rack focus: the focus shifts smoothly; the trees that were originally clear in the foreground become blurred, while the character in the background gradually becomes clear." [S1]; "rack focus from the brass latch to her eyes" [S17] | official |
| Zoom | "Zoom" [S9]; "Under a zoom lens, the camera pushes in on the defendant's nervous face as the courtroom … gradually pull away" [S10] | official |
| Whip pan | "entering with a handheld whip pan" [S2]; "At 5s camera whips left; when foreground bookcase fills frame it cuts to next scene" [C1] | official S2; community |
| Dive | "dive" [S1]; "dive vertically downward" [S1] | official |
| Speed ramp / bullet time / one-shot | "one-shot/long take, … bullet time, handheld shot, and speed ramp" can be written directly [S1]; "Bullet time shot = time slowdown + surround" [S9] | official |
| Shot sizes | "extreme wide shot/wide shot/medium shot/medium close-up/close-up" [S1]; "long shot, full shot, medium shot, close-up" [S10]; "headshot/bust/half-length portrait/full-length portrait"; grammar "Subject + Shot Size (e.g., Close-up of the man on the left)" [S9] | official |
| Angles | "low angle/overhead shot/first-person perspective" [S1]; "High Angle / Low Angle / bird View / Eye-level" [S9]; "Over-the-shoulder", "Telescope View", "Surveillance View", "fisheye" [S9, S10] | official |
| Transitions / cuts | "cut to …" [S4]; "Hard cut." after each shot; "Use HARD CUTS on the beat, with dual contrast on every cut (both shot size and camera type change at the same time)" [S2]; "At the 5-second mark, the camera quickly transitions leftward using a left wipe combined with a natural dissolve" [S1]; "no dissolve transitions … only hard cuts" [S2] | official |

Rules:
- **One camera instruction per shot**: "Try to specify only 1 type of camera movement in a single shot. Do not require push, pull, pan, and move at the same time, as this will increase image instability." [official S4]. Community agrees ("Stacked camera moves → jitter, drift") [C6].
- Movement formula: "Starting frame composition description + Shot movement + Shot movement amplitude + Ending frame composition description" [official S9]. Give the trigger: "camera begins push only after cup tips" [platform:fal P10].
- Locking a shot on 2.5 is done **in language only**. The API `camera_fixed` boolean ("ModelArk will append the fixed camera instruction to the user's prompt, but the actual result is not guaranteed"; "Reference-image scenarios are not supported") is listed for Seedance 1.5 pro / 1.0 pro / 1.0 pro fast only [official S3]; legacy text `--camerafixed true` / `--cf true` likewise 1.x [official S9, S10, S20]; "`frames` and `camera_fixed` (Seedance 1.x) are unsupported" on 2.x [community C4]. Replicate's README mentions `camera_fixed` but its live schema has no such field [P11]. Recommended lock phrase for our prompts (built from the official examples): "Locked-off camera, fixed camera position, eye-level [shot size]; the camera never moves; no push, no pan, no zoom, no handheld shake." [inferred composite].
- A camera-movement reference video is the most reliable way to reproduce a specific move: "Refer to the camera movement in Video 1 … keeping the scene consistent" [official S4, S5]; 3D clay-model video "as the only reference for the entire video's camera movement, shot rhythm, shot-size changes, subject motion trajectory, and camera blocking" [official S1].

---

## 6. Recommended prompt structure (official)

1. **Basic 2.5 formula:** "Organize the prompt in the order of 'subject + action/event + scene and environment + visual style + camera movement/shot cuts + sound'; unnecessary parts may be omitted." [official S2]. (Dreamina's public version: "format → subject → action → environment → camera → look → timing → audio/constraints" [official S17]; 1.5-pro: "Subject + Movement + Environment (optional) + Camera movement (optional) + Aesthetic description (optional) + Sound (optional)" [official S9].)
2. **Full 2.5 layout** [official S1 "Basic prompting techniques"]:
   - *Asset Referencing for R2V* — "Clearly identify each image, video, or audio asset by its upload order and intended purpose."
   - *One-Sentence Summary* — "Subject + Location + Event + Genre/Style + Camera movement…"
   - *Detailed Plot Description* — "Shot sequence or timeline: Either format is acceptable. Use timestamps or 'Shot N' to divide the video into segments, and describe each segment's specific visuals, camera movement, actions, dialogue, sound effects, and other details. Use positive descriptions whenever possible. Negative constraints are supported for subtitles and audio control, such as 'no subtitles' and 'no BGM.'"
   - *Additional Notes* — "Add any visual details that should remain consistent throughout, such as camera angle, camera movement, environment, scene setting, sound, atmosphere, and other recurring elements."
   - "Treat Seedance 2.5 as a visual content producer, and write structured prompts with a visual storytelling mindset."
3. **2.0 advanced formula (still valid on 2.5):** "precise subject + action details + scene/environment + lighting & color tone + camera movement + visual style + image quality + constraints"; per shot: (1) camera movement or transition, (2) subject actions and expressions, (3) position/spatial changes, (4) audio [official S4]. "Break the video into several shots … who + where + doing what + how the camera moves."
4. **Timestamps (2.5 only)** [official S1]: "Use 1-second intervals as the basic unit"; keep the timeline continuous ("avoid gaps such as '0-3s... 5-6s...'"); formats "0-3 seconds...3-7 seconds...7-15 seconds" or "[1s-4s]....[4s-8s]"; time-points ("Quick left sideways transition at the 5-second mark"); relative time ("After 3 seconds, everyone around him shakes their head"; "The frame freezes for 1 second after the main character presses the shutter"). "If too little plot is specified within a given time range, the model may improvise more freely. If too much content is packed into a given time range, the result may contain excessive cuts or omit parts of the plot." "It is not recommended to use timestamps to control high-frequency actions." Community adds: "Timestamps allocate pacing only — not frame-level cut points" [community C1, C8]. On **Seedance 2.0 timestamps are unstable**: "The model's support for precise timing (such as 0–3 seconds) is unstable" — use "Shot 1/2/3" and let pacing emerge [official S4].
5. **Time per beat**: official examples allocate 2–5 s per shot (rocket: 9 shots in 30 s; rap: 8 shots in 20 s; grapefruit: 9 beats in 29 s) [official S1, S2]; Dreamina: "Four connected shots works well; assign 6–8 seconds per beat" [official S17].
6. **Actions**: "Body-movement refinement + degree quantification" (hands/legs/head/shoulders + range, speed, force); "Prioritize slow, gentle, continuous small movements … try to avoid high-burst, large-dynamic actions such as sprinting, big jumps, and violent rolls"; "Supplement transitions between actions"; "Give priority to general descriptions … Only write specific details for a few memorable actions, and avoid repeating the same actions" [official S4, S1]. Emotions must be externalised (table in S4: Sadness = "lowering the head, shoulders trembling slightly, eyes reddening, fingers unconsciously clutching the corner of clothing"; Joy = "the corners of the mouth rising uncontrollably … steps becoming light"; Nervousness = "frequently checking the watch, fingers constantly tapping the tabletop, rapid breathing"; Anger = "both fists clenched, jawline tense, chest heaving"; Relief = "letting out a long breath, tense shoulders completely relaxing").
7. **Style / quality / constraint words**: "HD, rich details, cinematic texture, natural colors, soft lighting"; style words ("cyberpunk cool blue-purple tone, retro film"); constraints "keep it subtitle-free", "avoid generating any text or subtitles", "do not generate a logo", "do not generate a watermark"; character stability lines "The character's face remains stable without deformation; movements are natural and smooth, with no stutter or flicker" [official S4].
8. **Negative descriptions**: officially supported for subtitles and audio ("no subtitles", "no BGM", "no audio") [official S1]; official 2.5 examples also use "[Strictly exclude] Black-and-white, monochrome … storyboard frames, rough sketches; tilt-shift miniature look, toy-like appearance, plastic CG" and "No subtitles, no text overlays, no dissolve transitions, no duplicated people, only hard cuts" [official S1, S2]; "Throughout the video, characters with completely identical appearance, clothing, and accessories are prohibited. Do not generate duplicate avatars or a twin effect." [official S4]. Dreamina: "Keep negative constraints short and grouped at the end" [official S17]. Caveat: "Currently, it is not possible to directly avoid generating subtitles 100%" [official S4]. Prefer positive phrasing for everything else [official S1].
9. **Length**: API guidance ≤ 1,000 English words [official S3]; official 30 s examples are 300–600 words; Dreamina's 2.0 article suggests 30–100 words for simple clips [official S18]; community 60–100 words for 2.0 [C5, C6]. Rule of thumb: ~15–25 words per second of video for a timeline prompt, never past ~900 words [inferred from the examples].
10. **Language**: English prompts are fully supported; Chinese is the source language of the guides; keep the prompt in one language and match it to on-screen text and dialogue language [official S3, S4; community C6].
11. **Emphasis**: no weighting syntax exists. Ordering is the emphasis mechanism — "place important content at the front" [official S7]; "The more an asset requires precise reference, the earlier it should be placed" [official S4]; restate invariants in the "Additional Notes" block [official S1].
12. **Official prompt-optimisation skill**: ModelArk ships an agent skill `sd25-pe` ("`npx --yes skills@latest add "https://arkdocs-en.tos-ap-southeast-1.volces.com/skills/" --skill sd25-pe --yes`", usage "/sd25-pe + your prompt") [official S1, S2]. Not installed here (needs approval); see install_plan.

---

## 7. Official prompting examples (verbatim)

All quotes are literal doc text (only the doc's markdown escapes `\-` were normalised to `-`). Reference numbering inside each example is the doc's own.

**E1 — Text-to-video with timeline (2.5 prompt guide, basic template)** [official S1]
> Realistic nature documentary style, natural lighting and shadows. On a warm afternoon, on a grassy slope in the forest, a chubby panda cub rolls down the hill.
> The panda has fluffy, realistic black-and-white fur, a small round body, and clumsy, adorable movements. The scene is a green forest slope. The ground is covered with grass, moss, clover, soil, small stones, dry branches, and a few small yellow flowers. Tall tree trunks and dense woods are softly blurred in the background. The camera is a low-angle medium-wide shot with a slight handheld feel. The framing remains mostly stable, keeping the panda in frame at all times.
> 0s-3s: A panda cub lies on a green grassy slope, its body round and chubby. It begins to slowly roll sideways down the slope with clumsy movements, gently bending the grass beneath its body. A light breeze passes through, and sunlight filters through the trees from the upper left, creating dappled light and shadow.
> 3s-8s: The panda rolls toward the lower right of the frame and gradually comes to a stop, shifting from lying on its side to lying on its belly. Its round face turns toward the camera, and its front paws press into the grass. The panda lies in the foreground grass, adjusts into a comfortable position, slightly raises and lowers its head, and makes a soft little humming sound.
> Low camera position, slight handheld feel, subtly following the panda as it moves toward the lower right. Natural depth of field: the foreground grass is slightly blurred, the panda remains clear, and the background forest is softly out of focus. Natural environmental audio only, including wind, rustling grass, and the soft plop of the panda rolling. The overall mood is warm, realistic, and natural.

**E2 — 30 s product commercial, image reference + timeline + SFX + voiceover (2.5 tutorial; `ratio 16:9`, `duration 30`, `generate_audio true`, one `reference_image`)** [official S2]
> 3D animated advertising style, with bright and translucent colors. The pulp and juice should have a strong sense of freshness and impact. The overall feeling is like a high-quality commercial animated short, with a little exaggerated humor. The desert horned lizard character is cute, agile, and expressive, referring to @Image1. The visual texture should follow the reference image's soft natural light, delicate fur / skin surface texture, dreamy macro depth of field, and a feeling that is realistic with a touch of childlike playfulness. 0-3s: The scene is a desert scorched by the blazing sun. The air shimmers with heat, the sand is burning hot, and the distance looks as if it is smoking. A desert horned lizard lies on the hot sand, tongue slightly out, eyes unfocused, almost dried out by the sun. It takes two steps and wobbles, its whole body looking as if it is about to "evaporate." Sound effects: roaring heat waves and a slightly exaggerated dry cracking sound. 3-6s: The desert horned lizard suddenly stops and sniffs. It looks down and sees a cool, plump grapefruit with water droplets buried in the sand. The grapefruit gleams crystal-clear in the sunlight, with a delicate peel, like a miracle suddenly appearing in the desert. Performance: the lizard's eyes instantly widen as if it has seen a lifeline. Sound effect: a "ding" discovery sound. 6-8s: The desert horned lizard leaps forward, clutching the grapefruit tightly with both hands and pressing its whole face against the peel. It shows a blissful expression of "finally coming back to life." The image holds for 1 second, creating an exaggerated and funny advertising memory point. Sound effect: a thump, followed by half a second of silence. 8-11s: The desert horned lizard grabs the grapefruit. The peel cracks open, revealing full, glossy, translucent pulp. In the next instant, the juice does not simply flow out; it surges out like a tsunami. Sound effects: a "crack" bite-open sound, followed by an exaggerated juice-burst sound. 11-16s: Orange-pink, clear, shining grapefruit juice gushes wildly, pouring down the dunes and rapidly flooding the entire desert. The dry yellow sand instantly becomes a cool, sparkling summer ocean with a fruity feel. Cacti, rocks, and small dunes in the desert are swallowed by waves of juice, exaggerated and dreamlike. Performance: the desert horned lizard is excited at first, then realizes something is wrong, its expression changing from surprise to panic. 16-20s: The desert horned lizard is almost submerged by the "grapefruit sea" and frantically clings to half a grapefruit, floating on the surface like it is holding a life buoy. It pokes its wet head out, looking completely confused. The sea surface sparkles, colored like juice lit by sunlight. Sound effects: exaggerated splashing, waves, and a touch of comedy. 20-23s: The image suddenly cuts to a white screen. In the center appears the brand name and slogan: "Seedance Grapefruit: bite into the pulp, and summer pours out." Voiceover reads the full line: "Seedance Grapefruit: bite into the pulp, and summer pours out." Sound effect: a clean, refreshing brand sting. 23-29s: The white screen cuts back. The desert horned lizard is now leisurely sitting on a floating grapefruit, wearing small sunglasses, holding a straw cup, and drifting slowly across the "juice sea" on vacation. Orange pulp, small ice cubes, and refreshing splashes float around it. The sky turns deep blue, and the atmosphere instantly shifts from "survival" to "vacation." Finally the desert horned lizard leans back against the grapefruit in satisfaction. The camera pulls out and freezes on a refreshing, bright, playful summer image. Sound effects: relaxed summer music and gentle waves. Subtitles may keep only the brand name; no need for too much text.

**E3 — Multilingual lip-synced music video, shot list with timecodes and hard cuts (2.5 tutorial; `duration 20`, `ratio 16:9`, one `reference_image`)** [official S2]
> A cinematic hip-hop / rap music video with photorealistic texture, a premium tone, and a seaside setting. Build the image from @Image1: a band performs on a golden beach by the shore where waves break - a lead vocalist grips a microphone and sings passionately, with the mic stand planted in wet sand; one guitarist stands on the left side of the frame, another guitarist on the right side, and a drummer sits behind a drum kit in the back, playing. A vast coastline spreads behind them, rolling waves surge in layers, and a huge warm golden-hour sunset slants across the beach, sparkling on the water. Sea mist and salty humidity float in the air. The lead vocalist in a red tracksuit raps rhythmically toward the camera - lip shapes and jaw movement precisely match every word, and the head nods hard to the beat, driving the entire flow. The musicians sway and groove with the rhythm while waves crash behind them. This is a bright, energetic rap track - fast delivery, confident attitude, and a powerful beat. Use HARD CUTS on the beat, with dual contrast on every cut (both shot size and camera type change at the same time). Lyrics (the lead vocalist sings the following "hello" in each language in order, with precise lip sync): English: "Hello" Chinese: "你好" Japanese: "こんにちは" Korean: "안녕하세요" Portuguese: "Olá" Thai: "สวัสดี" Spanish: "Hola" Arabic: "مرحبا" Shot 1 [0:00-0:03] - Low-angle extreme wide establishing shot. A Steadicam slowly pushes in through golden sunset light and sea mist, with waves surging behind the band. Lyric line 1 (English "Hello"). Hard cut. Shot 2 [0:03-0:05] - Close-up of the red-tracksuit lead vocalist rapping into the camera, entering with a handheld whip pan, with the sparkling ocean blurred in the background. Lyric line 2 (Chinese "你好"). Hard cut. Shot 3 [0:05-0:08] - Macro insert shot, locked-off camera, a guitarist's fingers rapidly picking the strings as grains of sand and salty mist sweep past the foreground. Lyric line 3 (Japanese "こんにちは"). Hard cut. Shot 4 [0:08-0:10] - 3/4 side medium shot of one musician, slow prowling orbit, with instrument hardware and wet highlights reflecting the low slanting sunset over the sea. Lyric line 4 (Korean "안녕하세요"). Hard cut. Shot 5 [0:10-0:13] - A musician by the shore; a fast lateral dolly move sweeps past them, they turn toward the camera, and a wave breaks behind them. Lyric line 5 (Portuguese "Olá"). Hard cut. Shot 6 [0:13-0:15] - The drummer by the water, handheld fast tilt-up, sea wind and spray blowing through their hair as they groove and strike the drums on the beat. Lyric line 6 (Thai "สวัสดี"). Hard cut. Shot 7 [0:15-0:18] - Tight aggressive push-in on the red-tracksuit lead vocalist at the height of the flow, aggressive handheld, the dusk ocean behind them silhouetting the band. Lyric line 7 (Spanish "Hola"). Hard cut. Shot 8 [0:18-0:20] - Heroic extreme wide shot of the full band, aggressive handheld push-in. The vocalist and musicians step toward the camera on the beat, waves break, and golden sunset light blooms behind the whole band. Lyric line 8 (Arabic "مرحبا"). White balance 4000K, teal-and-amber color grade, 35mm, shallow depth of field, film grain, diffused sea mist, golden-hour glow. Solid, premium, high-end texture. Rhythmic rap performance, precise lip sync, head nodding to the beat. No subtitles, no text overlays, no dissolve transitions, no duplicated people, only hard cuts. Total duration 20 seconds.

**E4 — Multi-panel storyboard reference + character refs + dialogue, 9 shots / 30 s, explicit exclusions (2.5 prompt guide)** [official S1]
> Image 1: Nine-panel storyboard reference, used for the overall shot structure, shot sizes, and camera-movement rhythm.
> Image 2: Live-action reference of a rocket launch site on a dusk grassland, used as the benchmark for environmental composition, warm golden sunset light, cool twilight blue tones, and realistic color live-action texture.
> Image 3: Subject 1 (guardian robot) character appearance reference.
> Image 4: Subject 2 (elderly grandmother) character appearance reference.
> [Subject settings]
> Subject 1 (guardian robot): Refer to Image 3. A near-future weathered retro robot with an aged blue-green metal body, mottled rust, a domed head, two glowing red circular camera eyes, thin antennas, and slender articulated limbs. It is very tall, about twice the height of a human.
> Subject 2 (elderly grandmother): Refer to Image 4. A frail elderly woman with silver hair tied into a low bun, deep wrinkles, wearing a bright golden floor-length dress with gold-and-blue embroidered details on the chest. Her expression is full of reluctance and sorrow. Her height only reaches the robot's chest.
> Environment (dusk grassland launch site): Refer to Image 2. A near-future grassland at dusk, with the sky gradually shifting from warm gold to cool blue. On the distant horizon, a launch tower stands with a white rocket, steam rising around it. Knee-high wild grass sways in the wind across a vast, open landscape.
> [Overall style]
> Live-action color cinematic film, realistic photoreal texture, full-color visuals throughout. Color 35mm film look, fine realistic film grain, rich cinematic color grading, IMAX large-format feel. Handheld cinematography with breathing-like camera shake, shallow depth of field, wide aperture, continuous drifting foreground grass, sparks, and ash. Slight Dutch angle. Strong contrast between warm golden sunset light, cool twilight blue, and explosive warm orange. 16:9 horizontal frame. Near-future emotional disaster-film atmosphere: quiet, tragic, protective, and filled with reluctance.
> [Strictly exclude]
> Black-and-white, monochrome, grayscale, desaturated visuals; hand-drawn, sketch, line art, illustration, comics, animation; storyboard frames, rough sketches; tilt-shift miniature look, toy-like appearance, plastic CG, glossy overexposed CG.
> [Shot list] (9 shots, approximately 30 seconds)
> Shot 1 (0-3s): Extreme wide shot, ultra-low camera position close to the ground, looking upward, handheld camera slowly tilting downward. Refer to the grassland composition in Image 2. The dusk grassland feels vast and empty. Knee-high wild grass in the foreground sways out of focus, and warm golden lens flare sweeps across the frame.
> Shot 2 (3-6s): Medium front shot with a handheld camera. The robot supports the elderly woman.
> Shot 3 (6-10s): Facial close-up. The elderly woman looks reluctant to part. Dialogue (elderly woman): "Fly safe, my child. Come back to me."
> Shot 4 (10-14s): Extreme wide shot tilting upward. The rocket rises with a thick white smoke trail. Dialogue (elderly woman): "There he goes... there he goes."
> Shot 5 (14-18s): Extreme wide shot. The rocket explodes and breaks apart in midair. Dialogue (elderly woman): "No... no, no—"
> Shot 6 (18-22s): Extreme facial close-up. The elderly woman's pupils contract and tears fall. Dialogue (elderly woman): "...he was almost there."
> Shot 7 (22-25s): Close-up transitioning to a medium close-up. The elderly woman breaks down in tears. Dialogue (elderly woman): "Bring him back! Please—bring him back!"
> Shot 8 (25-28s): Ultra-low-angle, nearly vertical upward shot. The robot embraces the elderly woman, forming a protective dome around her. Dialogue (robot): "Don't look up. I've got you."
> Shot 9 (28-30s): Extreme wide rear shot. The two figures embrace tightly in silhouette. Dialogue (robot): "I'm still here. I'll stay... as long as you need."

**E5 — Line-art storyboard with asset bindings and bracketed camera notes (2.5 prompt guide)** [official S1]
> Visual Style: Domestic realistic short drama, shot on Arri Alexa Mini LF, 35 mm cinema lens, cinematic realistic lighting, indoor night scene with snow-falling night view outside the window, film grain, authentic skin texture, natural lifelike performance, subtle micro-expressions, real adult facial bone structure and facial features, no excessive beautification or skin smoothing.
> Asset Bindings: Storyboard @Image1, bedroom @Image2, Li Tian @Image3, Li Qian @Image4, book *Happy Times* @Image5.
> Shot 1: [Wide shot, locked-off camera, eye-level, rule-of-thirds composition] Room on a snowy winter night. In front of floor-to-ceiling windows, a man stands sideways with both hands in his pockets, gazing out at falling snow. A young girl stands beside him, watching the man quietly. Calm and restrained atmosphere. Snowflakes keep drifting against the glass window.
> Shot 2: [Medium shot, over-the-shoulder shot] The girl's back serves as foreground. The man turns his head and looks gently toward the girl. The girl bows her head slightly in silence. Snow keeps falling outside the window.
> Shot 3: [Medium close-up, diagonal composition] The man holds the book *Happy Times* and extends it slowly. The young girl raises her hands to receive the book.
> Shot 4: [Close-up on the girl's face, central composition] The girl clutches the book tight against her chest. Her eyes turn red, teardrops roll slowly down her cheeks with a sorrowful look.
> Shot 5: [Close-up on the man's face, oblique composition] The man wears a soft faint smile, gazing quietly at the tearful girl with melancholy in his eyes.
> Shot 6: [Wide shot, locked-off camera] The girl turns and walks slowly out of frame. Only the man remains standing alone by the window, hands in pockets, staring out into the blowing snow. The room feels empty and still.

**E6 — Keyframe reference, one-shot, six stills (2.5 prompt guide)** [official S1]
> Create a one-shot vertical pixel-art wuxia-themed video based on @Image 1 to @Image 6. Use Chinese-style 8-bit wuxia background music. The entire video should use a unified light-blue background, consistent pixel-art style, and a clean, bright, transparent visual look.
> Shot 1: Hold on the ink-wash-style "江湖风云" logo from @Image 1. The background is the unified light-blue color. Keep the frame still for about 1 second.
> Shot 2: After the text area from @Image 1 disappears, the pixel-art close-up face of the male wuxia character from @Image 2 slides in from the bottom of the frame. The character blinks and looks toward the camera, then quickly moves downward and exits the frame. After the character exits, the original logo area transforms into the blue pixel-art "武功秘籍" martial arts manual from @Image 3.
> Shot 3: Immediately transition to @Image 4. A small pixel-art wuxia character jumps forcefully upward from the bottom of the frame and hits the blue diamond-shaped question mark icon above. Bold dark-blue text "今日闯江湖!" pops out above the question mark icon. After landing, the character strikes the standing pose from @Image 4, then raises a hand to greet the viewer. Next, the character prepares to run, turns toward the right side of the frame, and runs to the right, with the running pose referencing @Image 5. The camera follows the character smoothly to the right, and the character jumps out of frame from the right side.
> Shot 4: The UI interface from @Image 6 slides into the frame from the right. The pixel-art wuxia character jumps in from the upper-right corner and lands at the lower-right side of the large "三月廿七日" text. The character opens both arms in an enthusiastic presentation pose and freezes. The final frame holds on this composition.
> Overall requirements: Pixel-art wuxia visual style throughout, with a unified light-blue background tone. The camera movement should be continuous and smooth, presenting a one-shot flow with seamless position shifts and follow movement. Element transitions should feel natural, and character actions should connect smoothly. No stuttering, no flickering. Text and UI must remain clear and stable.

Also: "Use Images 1 to 7 in order as keyframes. In a sea of clouds and mountains, blue-and-pink long-tailed spirit fish soar through the air. …" — the required first sentence for strict keyframe alignment [official S1].

**E7 — Video instruction editing (2.5 prompt guide)** [official S1]
> Preserve the composition, camera position, lighting, and performance rhythm of @Video 1. Only modify the female lead's appearance and expression: let her naturally age from her twenties to around sixty. The restraint in her eyes gradually softens, tears slide past the corners of her eyes, and the corners of her mouth slowly lift until she finally smiles through her tears. The entire video should be a continuous one-shot, with no jump cuts and no flickering. Her facial features should gradually age without drifting or changing identity.

**E8 — Video editing with reference images (subject + scene swap, keep motion) (2.5 prompt guide)** [official S1]
> Replace the two-person fight in @Video 1 with an empty-handed probing exchange before a cold-weapon duel.
> Replace the scene with a medieval stone castle platform, an ancient courtyard, an outer platform of a mountain fortress, or a simple stone-brick duel arena. The background should include castle walls, wind, fog, distant mountain ridges, and a flat stone ground. Refer to @Image 1 for the environment.
> Replace the man in dark clothing in the video with @Image 2, and replace the man in light-colored clothing with @Image 3. Keep the original actions and rhythm unchanged.
> AI effects should only enhance the environment and texture: wind-blown clothing, light fog, a small amount of dust at contact points, cool metallic reflections, subtle film grain, and an epic color palette. The overall style should be restrained, realistic, and evoke a classic hardcore duel atmosphere. Keep the background music synchronized with the action beats.

**E9 — Product swap edit (2.0 prompt guide, valid on 2.5)** [official S4]
> Replace the perfume featured in Video 1 with the face cream from Image 1, with all original motions and camera work preserved.

Related official editing templates [official S4]: "Adding: At [Timestamp/Timing] and [Spatial Location] of [Video N], add [Description of intended element]. Removing: Remove [Element to be deleted] from [Video N], keeping the rest of the video content unchanged. Modifying: Replace [Description of element to be changed] in [Video N] with [Description of intended element]." Examples: "Add snacks such as fried chicken and pizza to the countertop in Video 1."; "Remove everything that isn't office supplies from the table in Video 1, keeping the rest of the video content unchanged."; 2.5: "Change the man's action from drinking coffee to mopping the floor from 4-6 seconds in Video 1, and leave the rest of the content unchanged." [official S1].

**E10 — Audio editing / dubbing (2.5 prompt guide)** [official S1]
> Translate the spoken dialogue in the video into Chinese, with no subtitles. Precisely adjust the lip movements to match the translated speech, while keeping everything else unchanged.

**E11 — Video extension (2.5 prompt guide; output_format mov recommended)** [official S1]
> Extend @Video 1 by 5 seconds. A bee flies in and lands on the flower. Then, in a macro close-up, its legs and abdomen are covered with golden pollen particles. The bee flaps its wings and takes off, and the camera follows it as it flies toward another flower of the same species. In slow motion, pollen shakes loose from the bee's fine hairs and falls precisely into the flower's stamen, magnifying the moment of pollination.

2.0 extension examples [official S4]: "Generate the content after Video 1: the two men who are late run towards them, the five people finally meet and have a friendly chat."; "Extend the opening segment of Video 1: Set up an over-the-shoulder shot of the man in a hoodie, and the man says: "It's not that bad. You're just stressed. Everyone goes through this, you just need to keep going.""

**E12 — Seamless transition between two videos (2.5 prompt guide)** [official S1]
> Seamlessly connect [Video 1] and [Video 2]. At the end of [Video 1], the camera should quickly fly upward to the top, rapidly turn back, and then dive vertically downward, creating a natural seamless transition into [Video 2]. During the transition, the mahjong tiles gradually transform into high-rise buildings, and the entire scene changes accordingly. Do not alter the two uploaded videos themselves.

**E13 — Multi-reference dialogue drama with `{}` dialogue (2.0 prompt guide, Example 1)** [official S4]
> Asset preparation: @Image 1: Half-body photo of the female lead · @Image 2: Dormitory scene reference image · @Video 1: Camera movement reference for indoor dialogue (medium-shot dolly in/out or slight pan) · @Audio 1: Indoor ambient sound or light music
> Use the girl in @Image 1 as the main character, use @Image 2 as the dormitory scene style reference, and refer to the camera movement in @Video 1.
> Shot 1: At dusk, girl @Image 1 walks briskly to the dormitory entrance @Image 2. The camera follows steadily in a medium shot. Warm yellow sunlight spills into the hallway from the window. She pauses at the doorway, takes a deep breath, and looks slightly nervous.
> Shot 2: Girl @Image 1 pushes the door open and enters the dormitory. The camera cuts to an indoor medium shot. Her roommates look up at her while organizing their books. One of them smiles and asks {How did the exam go? Did you pass?}. The camera slowly cuts between half-body close-ups of several people.
> Shot 3: Girl @Image 1 first lowers her head with a dejected expression. The camera gives her a close-up. Then she raises her head, unable to hold back a smile, laughs out loud, and says {I was kidding}. Her roommates start chasing and play-fighting with her. The camera slowly pulls back and freezes on a wide shot of the dormitory filled with laughter.
> The entire video should have a high-definition cinematic documentary style, with warm tones and soft lighting. The character's face remains stable without deformation; movements are natural and smooth, with no stutter or flicker. The ambient sound blends naturally with @Audio 1.

**E14 — Multi-reference action scene with camera-movement video + audio sync (2.0 prompt guide, Example 2)** [official S4]
> Use the woman in red from @Image 1 as the female lead, use the woman in black from @Image 2 as the opponent, use the cliff and bamboo forest environment in @Image 3 as the scene reference, refer to the overall camera movement and action rhythm in @Video 1, and synchronize the background sound effects with @Audio 1.
> Shot 1: At dusk, the camera slowly pushes in from a side medium shot of woman in red @Image 1. She stands at the edge of the cliff and lifts a wine flask to drink. Her sleeves and robe hem sway gently in the mountain wind. The camera circles halfway around her, moving from the front to her back. In the distance, a figure in black is faintly visible in the bamboo forest.
> Shot 2: The camera zooms and fades into a long shot. From a drone perspective, it overlooks the entire cliff and bamboo forest. The two characters stand at opposite ends of the cliff. The mountain wind lifts their robe hems and dust, and the rhythm slightly accelerates with the drum beats.
> Shot 3: The camera cuts back to a ground-level close shot. The two slowly draw their swords and face off. Woman in red @Image 1 shifts from a careless expression to a cold gaze. Woman in black @Image 2 looks determined, and the sword tip trembles slightly. The camera steadily follows the two as they circle each other, finally freezing on a close-up of the instant before the two swords meet.
> The overall visual style should feel like a cinematic wuxia world in misty rain, with cool tones, low saturation, a film-grain texture, and rich light-and-shadow layers. The characters' faces and body proportions remain stable without deformation. Movements are continuous and natural, not stiff, with no clipping or stutter.

**E15 — Product shots (2.0 prompt guide, image reference)** [official S4]
> Use the cameras featured in Image 1, Image 2 and Image 3. Replace the original background with a white one, and place the cameras on a white table. The camera first focuses on the cameras in close-up, then slowly rotates 360° with the cameras as the main subject, clearly displaying the front, sides and back of each camera.

> In a warm-toned home setting, present the thermos shown in the reference image in a medium shot. Then smoothly push the camera into a close-up of the thermos. Next, a hand naturally enters the frame off-screen, gently grips the thermos body and picks it up. The camera follows the slight rotating motion of the hand to showcase the thermos.

> The scene is set in the restaurant from image 4 with people coming and going. The girl from image 1, wearing the clothes from image 2, is organizing the items on the counter. The boy, a customer, from image 3 approaches her to ask for her contact information. The logo from image 5 remains in the bottom right corner throughout.

**E16 — Dialogue with composition references and Korean lines (2.0 prompt guide)** [official S4]
> Refer to the composition in Image 3. A girl (her character design refers to Image 1) is waiting for her father to finish cooking, and she says: "아빠, 배고파요! 밥 다 됐어요?" Then the camera pans right and cuts to the frame and composition shown in Image 4. The father (his character design refers to Image 2) replies to her: "거의 다 됐어, 조금만 기다려!" Next, the camera cuts back to a close-up shot of the daughter's slightly disappointed facial expression, and she says: "아직 멀었어요? 맛있는 냄새 나는데..." Then the shot switches to a close-up of the father's face, and he says: "이제 진짜 금방이야. '빨리빨리' 하지 말고 손부터 씻고 와!"

**E17 — UGC-style product talking head with a preset digital character (portrait doc)** [official S8]
> Vertical HD close-up video of a beauty blogger (Image 1). She has bold, glamorous makeup with no facial shine or glare and a sweet smile. She holds a face cream jar (Image 2), presents it directly to the camera. The background is fresh and minimalist. Energetic and sweet style. Character speaks in real-time: 'I found my holy grail face cream! It has a cloud-like creamy texture that absorbs instantly. Perfect for post-all-nighter rescue, deep hydration and moisturization—my skin glows naturally even without makeup!'

**E18 — Camera-control one-liners (1.0 pro guide, "Lens language")** [official S10]
> i2v: The camera quickly pushes into a close shot of the little girl, who turns her back to the lens and slowly raises her head to look up at the building in front of her.
> i2v: The camera quickly pulls out, revealing the woman's upper body. She slightly turns her head and looks to the right of the frame, with a bustling street as the background.
> t2v: At a fashion show scene, the camera pans right to shoot a gorgeously dressed model walking the runway in profile.
> i2v: The camera circles around, moving from the woman's back to her front. She is extremely beautiful, raising her hand to cover her mouth and smiling shyly.
> t2v: In the courtroom, the judge is about to announce the verdict. Under a zoom lens, the camera pushes in on the defendant's nervous face as the courtroom and the crowd in the background gradually pull away, compressing the space to highlight the defendant's suffering while waiting for the judgment.

**E19 — Hitchcock zoom and dolly-in with start/end composition (1.5 pro guide)** [official S9]
> A close-up shot shows a girl with glasses and well-defined features, dyed short red hair, frowning, looking straight into the camera. The background is a dilapidated amusement park, with a stationary carousel and a water slide in the distance, the ground covered in dirt and overgrown with weeds, and the girl stubbornly biting her nails. Hitchcockian camera movement: Keep the girl's main composition unchanged, dolly out + increase the focal length of the lens.
> … The camera starts with a medium shot (above the chest), slowly zooms in at a steady sliding speed, approaching his face, and finally reaches an extreme close-up (showing only the area of his eyes and nose bridge).

**E20 — Three-shot beauty commercial with synchronized voice-over (1.5 pro guide)** [official S9]
> Generate a video based on the input lipstick product keyframe image, keeping the appearance, proportions, and materials of both the lipstick and the model accurate and consistent, with no unnecessary elements added. The overall style is a high-end e-commerce beauty commercial, clean, refined, and premium in tone. The video consists of three continuous shots: in the first shot, the camera performs an extremely slow and smooth push-in to showcase the lipstick's overall appearance and design details, with a rich, saturated lipstick bullet under soft, stable diffused warm lighting and a clean, blurred background; in the second shot, the view cuts to a close-up of the model's face, with the model holding the lipstick near her face in a portrait-style composition, featuring natural, luminous skin tone and a calm, confident expression, centered and stable to emphasize the connection between the product and the wearer; in the third shot, the camera cuts to a close-up of the lipstick placed on a woman's tabletop, resting on a clean surface with a minimal surrounding environment, soft and delicate lighting, and a stable frame, reinforcing product texture and final brand recall. A clear, confident female commercial voice-over with a refined tone and moderate speaking pace is synchronized with the visuals, delivering the following lines: "Rich color. Smooth texture. One swipe delivers radiant lips. Lightweight, comfortable, and effortlessly elegant."

**E21 — 3D clay-model (white-box) reference with character/scene mapping (2.5 prompt guide)** [official S1]
> Refer to [Video 1] for the lighting direction and lighting changes, camera movement, character positions, music, sound effects, and visual rhythm to generate an animated scene.
> Replace the pink model in [Video 1] with Hina Amano from [Image 3], and replace the gray model in [Video 1] with Hodaka Morishima from [Image 2]. Use the rooftop and sky from [Image 1] as the full background scene.
> First, Hina Amano clasps her hands together and closes her eyes in prayer. Sunlight gradually illuminates her face and the distant buildings from the upper left of the frame. As the shot changes, Hodaka Morishima says "あっ?" with slight surprise. He turns toward the right side of the frame, leans back in surprise, and looks at the sunlight shining from the upper right. The light spreads from the lower left of the ground toward the upper right, illuminating the boy's clothing. Then the shot switches to a wide view referencing [Image 1]. The two protagonists stand with their backs to the camera. The boy spreads his arms and says "Ah~" in surprise, while the girl maintains her praying pose.
> Japanese animation style inspired by Makoto Shinkai. The lighting should evoke sunlight breaking through clouds, and the overall atmosphere should feel hopeful and emotional. The character appearances must strictly reference [Image 2] and [Image 3], remain consistent throughout the video, and avoid face changes. Keep the original audio unchanged. High image quality, rich details, stable motion, and smooth visuals.

**E22 — Dreamina official 2.5 examples (product / performance ad; note the "Preserve … / Avoid …" tail)** [official S17]
> 20 seconds, 1:1 premium product commercial. Use @Image1 as the exact smartwatch reference; preserve its logo, bezel, button placement, proportions, and screen design. 00–05s: macro shot of rain beads landing on the watch face against black stone. 05–12s: slow clockwise orbit as the display activates and blue interface light reflects on the metal edge. 12–17s: athlete fastens the watch before a dawn run; match cut from the circular display to the rising sun. 17–20s: locked hero pack shot with the logo facing camera and clean negative space on the right. High-contrast studio lighting, realistic metal and glass, smooth controlled motion. Audio: subtle water impact, soft electronic activation, restrained bass rise. No warped logo, extra buttons, changing strap color, unreadable text, or camera shake.

> 15 seconds, 9:16 vertical direct-response ad, three fast but coherent beats. Keep the creator from @Image1 and the bottle from @Image2 consistent. 00–03s: handheld close-up, creator looks into camera and says, "My desk used to look like this by noon," while pointing to three empty cups. 03–10s: two match-cut demonstrations—pouring the drink over ice, then working calmly at the desk—with the bottle label always facing camera. 10–15s: clean pack shot beside the creator, gentle push-in, spoken CTA: "One bottle. No afternoon crash." Bright window light, authentic UGC texture, readable composition, beat-matched natural cuts. Preserve face, bottle shape, label colors, and hand anatomy. No extra fingers, label mutation, captions, background people, or floating props.

**E23 — fal's production-brief style (platform, not ByteDance): product demo with two image references and a continuation prompt** [platform:fal P10]
> 14-second continuous product demonstration in the Los Angeles kitchen from @Image2. @Image1 controls only the exact portable espresso maker: preserve its short cylindrical proportions, matte cobalt-blue shell, black rubber grip ring, circular copper button, and clear lower chamber. Do not copy @Image1's studio background. @Image2 controls only the kitchen layout, oak countertop, white cup, beige towel, plants, window light, and warm daylight. Do not add the studio surface from @Image1. Start on a wide frame matching @Image2 with the product standing to the left of the white cup. 0-4 seconds: the camera makes a slow, level push toward the product while it remains still. 4-7 seconds: one natural right hand enters from frame right and presses the copper button once. 7-11 seconds: dark espresso begins flowing into the clear lower chamber; the liquid level rises naturally while the product body stays rigid and unchanged. 11-14 seconds: the hand withdraws and the camera shifts slightly right to place the product and cup side by side in the final frame. Keep the cup, towel, plants, countertop, product geometry, button position, and lighting consistent. No logo, no text, no extra machine, no extra hands, no cuts, no slow motion. Audio: quiet apartment room tone, soft button click, gentle brewing sound, distant Los Angeles traffic, no music.

> Use @Image1 as the exact first frame and continue forward from that moment. Preserve the same stack of three buttermilk pancakes, softened square of butter, six blueberries, white ceramic plate, amber syrup pool, counter, warm diner light, 21:9 framing, macro lens, and camera position. Do not replay or recreate the syrup pour that happened before this frame. 0-4 seconds: hold the same composition while the syrup pool makes only small natural settling movements. 4-8 seconds: one clean stainless-steel fork enters from frame right with no hand visible, presses into the front edge of the top pancake, and separates one bite-sized piece. 8-10 seconds: the fork lifts the same piece upward; one thin syrup strand stretches from the piece to the stack. 10-12 seconds: the syrup strand narrows and breaks, and the fork exits toward frame right with the piece. The remaining stack stays on the plate with one small missing bite at the front. No new pour, no pitcher, no hand, no extra fork, no extra pancakes, no changing blueberry count, no cut, no slow motion, no text, no music. Audio is quiet diner room tone with a soft fork contact and sticky syrup separation.

---

## 8. Limits (consolidated)

| Limit | Value | Source |
|---|---|---|
| Prompt length | ≤ 500 Chinese chars / ≤ 1,000 English words recommended | official S3 |
| Output duration | 4–30 s or -1 (2.5); 4–15 s (2.0) | official S2, S3, S6; platforms P1, P6, P11, P18 |
| Editing output duration | locked to source (-1), ≤ 0.3–0.4 s drift | official S1, S2, S3 |
| Resolution | 480p / 720p / 1080p (2.5); 4K only on 2.0 std | official S2, S3, S6 |
| Aspect ratios | 16:9, 4:3, 1:1, 3:4, 9:16, 21:9, adaptive; locked tasks adaptive only | official S2, S3 |
| fps | 24 | official S6 |
| Reference images | ≤ 30 (2.5) / ≤ 9 (2.0); < 30 MB; 300–6000 px; ratio 0.4–2.5 | official S2, S3 |
| Reference videos | ≤ 10, each 2–30 s (edit source 4–30 s), total ≤ 30 s, ≤ 200 MB, 24–60 fps | official S2, S3 |
| Reference audio | ≤ 10, each 2–30 s, total ≤ 30 s, ≤ 15 MB, wav/mp3 | official S2, S3 |
| Total references | ≤ 50 | official S1, S2, S11 |
| Request body | ≤ 64 MB | official S3 |
| Recommended subjects | 1–8 image subjects; 1–5 A/V subjects; 5–10 s per reference clip; ≤ 4 people per generated frame for stability | official S1, S4 |
| Storyboard panels | ≤ 15 | official S1 |
| Editing source length | ≤ 20 s recommended; 1–5 ref images | official S1 |
| Resolution × duration | no documented restriction on 2.5 (any resolution at any 4–30 s); 4K on 2.0 has RPM 15 / concurrency 1 | official S6 [single-source for "no restriction": absence in docs] |
| Rate limits | 600/180 RPM, 10/3 concurrent (enterprise/individual) | official S2, S6 |
| Asset retention | video URL 24 h (100 downloads); task 7 days; trusted face outputs 30 days | official S2, S8 |
| Generation time | undocumented; 30 s 1080p ≈ 10+ min on Krea; 1–10 min elsewhere | platform P18 [single-source]; community P20 |
| Real faces | not accepted as direct reference input (2.0/2.5 on ModelArk); use trusted outputs / digital characters / authorized assets | official S2, S3, S8 |
| Named IP / brands | naming a specific film, studio or artist gets a generation rejected on Krea; Disney and Paramount cease-and-desist letters Feb 2026 led ByteDance to "strengthen intellectual property safeguards" | platform P18 [single-source]; community C12 |
| Logos | model can render a supplied logo from a reference image ("The logo from image 5 remains in the bottom right corner throughout") and can leak other platforms' logos/watermarks unless told "do not generate a logo/watermark" | official S4 |
| Minors | no specific statement found in the fetched docs; general "ModelArk security moderation policies" apply to outputs | official S8 [gap] |
| Text rendering | supported for "common text" (slogans, subtitles, speech bubbles) with prompt control of colour/style/timing/position; use common characters, avoid rare glyphs; "text restoration accuracy" still an improvement area | official S4, S14 |
| Watermark | off by default; `watermark=true` adds "AI Generated" | official S2, S3 |
| Audio channels | mono output | official S3 |

---

## 9. Known failure modes and what to avoid

Official (ModelArk FAQ and guides) — with the official fix:
1. **Character ID drift / "face swapping" mid-clip** — cause: mixed reference sheets, small face area. Fix: separate close-up headshot (face only, neutral expression) + full-body photo; "facial features reference image 1 (headshot), makeup and styling reference image 2 (full-body photo)"; put the precise-reference asset first; 2.0: avoid multi-view sheets [official S4]. 2.5 supports multi-view but recommends single-view above 5 subjects [official S1].
2. **Duplicated characters ("twins")** — cause: unlabelled subjects, multi-view sheets. Fix: "Zhang San (corresponding to image 1) throws … Li Si (corresponding to image 2)"; append the global no-duplicate constraint; single-person photos; don't paste the whole script [official S4]. Cannot be avoided 100%.
3. **Too many people** — > 4 reference people lowers stability (wrong head-count, duplicates). Fix: generate group stills of ≤ 4 first, then image-to-video from those [official S4].
4. **Unexpected subtitles / on-screen text** — add "keep it subtitle-free", "avoid generating any text or subtitles"; strip text from references first; generate landscape and crop [official S4]. Not 100% avoidable.
5. **Foreign logo / watermark appears** — "Do not generate watermarks", "Do not generate Logos" [official S4].
6. **Style drift** (realistic reference pulls an anime prompt to live-action) — state the style explicitly; pre-convert references to the target style [official S4].
7. **Jump cuts / rollback at extension joins** — trim 6 frames off the end of the earlier clip and 1 frame off the start of the next in the NLE; end clips on a cut and start the next in a new scene [official S4]. Use `mov` in and out on 2.5 [official S1, S2].
8. **Quality degradation over repeated extensions** (blotchy faces) — convert the source to a white 3D-model video first ("Convert the video into a white 3D model. All characters should be unified as pure white 3D models, with no color, no texture, and no shadows…"), use HD references, limit the number of continuations [official S4].
9. **Special effects don't match a textual description** (e.g. a countdown) — supply the effect as a reference video [official S4].
10. **End-of-clip audio click / cut-off** with narration — regenerate or fade in the NLE [official S4].
11. **Mispronounced Chinese** — substitute common homophones [official S4]. **Voice doesn't match the reference audio** — describe the timbre in words and keep the lines' tone close to the reference [official S4].
12. **Frame stretching/compression jumps in first/last-frame mode** — input image dimensions differ from the output grid; crop the image to the table values and use `ratio=adaptive` [official S5].
13. **Timestamp over/under-packing** — too much per interval → "excessive cuts or omit parts of the plot"; too little → improvisation; never timestamp high-frequency actions [official S1]. Contradictory camera/motion instructions in storyboard prompts → failure [official S1].
14. **Stacked camera moves** — more than one movement type per shot "will increase image instability" [official S4]. **High-burst actions** (sprinting, big jumps, violent rolls) are riskier than slow continuous movement [official S4].
15. **Multi-speaker lip sync, audio distortion/noise, high-frequency visual noise, minor deformation, motion plausibility in edge cases** — acknowledged model limits [official S14]; "physical plausibility of complex motions and the stability of scenes involving interactions among multiple subjects" [official S11]; "text rendering accuracy", "complex editing effects" [official S12].
16. **Storyboards > 15 panels** cause still frames or wrong order; cluttered/over-sharpened AI storyboards and text on panels confuse the model [official S1].
17. **Over-long prompts** → "scattered information … missing elements" [official S3]; over-full asset lists → "style conflicts, blurry subject identification" ("It is not recommended to use the full asset limit") [official S4].
18. **Editing vs reference misclassification** — writing "reference Video 1" in an edit prompt may turn it into a reference task; use "Edit Video 1 …" and include an edit/extend trigger word [official S1, S2, S4].
19. **First/last-frame + omni-reference mixing** is rejected [official S3]; last frame with a different ratio is cropped/stretched [official S1, S3].

Platform / community observations (not ByteDance statements) that map to our anomaly checklist:
- **Hands and fingers**: Dreamina's own example ends with "Preserve … hand anatomy. No extra fingers" [official S17]; fal examples add "no extra hands", "no duplicated limbs" [platform:fal P10]; APIYI's checklist "avoid bent limbs" [community C5]. Write one hand, which hand, and what it holds.
- **Liquids**: describe pooling/settling phases and gravity ("Syrup pools on the plate and does not flow uphill"; "Coffee follows the counter surface and never moves uphill") [platform:fal P10]. No official statement on liquids [gap].
- **Object count changes / teleportation**: "No object teleportation", "no changing blueberry count" [P10]; official: state the count of the target object across the whole clip in edits ("There is exactly one white folding lamp throughout") [community C1, claiming official manual].
- **Occlusion resets**: repeat identity/clothing/speed after an occlusion ("the same woman emerges from the opposite side of the column with the same face, hair, green coat…") [P10].
- **Camera + subject both moving**: allowed but tie the camera move to the subject ("camera moves parallel and keeps the red player in the left third") [P10]; official rule remains one camera move per shot [S4].
- **Small text** (menus, specs, formulas): "Subtitles, formulas, signage, specs, frame-precise timing needing exact match should use pre-composited assets + generation + post-production" [community C1]; official: prefer common characters, logo via reference image [S4].
- **Mirrors / reflections / crowds / long continuous takes**: no explicit official or platform statement found; crowds fall under "too many people" (official S4) and "multi-subject interaction" (official S11); 30 s single takes are supported but "A 30-second shot needs a timeline" or it drifts into waiting/repetition/slow motion [P10]. Mirrors/reflections: [no source — treat as unverified risk].
- **Reference bleed**: an un-scoped reference leaks its lighting/background/framing — always say what to take and what not to take [official S1 "which part"; community C1, C8; platform P10].
- **Generic adjectives** ("cinematic", "dynamic", "emotional") without observable cues do nothing [official S4 emotion table; platform P10; official S17].
- **Brand/IP names** in prompts can be rejected on some platforms (Krea) [P18]; describe the look instead.
- **Vertical 9:16** has a higher chance of spurious subtitles [official S4]; add the subtitle-free constraint on every vertical prompt.

---

## 10. Consistency across clips (officially recommended techniques)

1. **Last frame → first frame chaining**: set `return_last_frame=true` (watermark-free PNG at output size) and "Use the last frame of the previously generated video as the first frame of the next video task, and generate multiple consecutive videos in a loop. Afterward, you can use tools such as FFmpeg by yourself to stitch…" [official S3, S7]. On 2.5 the next clip must then run in first-frame mode (`role=first_frame`, `ratio=adaptive`) **without** omni references [official S3] — or pass the frame as `reference_image` and write "Image 1 is the first frame" to keep other references at the cost of exact match [official S1]. Trusted-output rule lets these face-containing frames pass moderation for 30 days [official S8].
2. **Extension instead of a new clip** when the scene continues: "Continuous long take (video extension): suitable for 'dialogue scenes' within a single scene … Scene / action turning points (segmented stitching): suitable for plot turns or complex, fast-paced 'action scenes'" [official S4]; extension keeps identity/environment ("Multi-round extension maintaining character/environment consistency") [official S11]; use `mov` in/out; expect small loudness differences; trim 6/1 frames at joins if needed [official S1, S4].
3. **Identity via reference images**: headshot + full-body per character, headshot first, bound by name every time it is mentioned; 2.5 allows multi-view but split views into separate files [official S1, S4]. Products: multi-angle photos as separate images ("Use the cameras featured in Image 1, Image 2 and Image 3") [official S4].
4. **Explicit invariants**: the "Additional Notes" block restating camera angle, environment, sound, atmosphere [official S1]; character-stability sentence ("face remains stable without deformation; movements are natural and smooth, with no stutter or flicker") [official S4]; in edits, "Parts not mentioned remain unchanged by default" but "emphasize [unchanged elements] in the prompt for better performance" [official S4].
5. **Fixed camera language** ("locked-off camera, fixed camera position", one move per shot) and a camera-movement reference video for repeatable moves [official S1, S4]; `camera_fixed` is not available on 2.x [official S3].
6. **Seed reuse**: "similar results, but complete consistency is not guaranteed" [official S3]; exposed on fal/Replicate/Krea for 2.5 but not listed for 2.x on ModelArk — do not rely on it [official S3; platforms P6, P11, P18].
7. **Explicit start and end states**: official 2.5 templates end each shot with a held/frozen frame ("The final frame holds on this composition", "The frame freezes", "the camera pulls out and freezes") [official S1, S2]; community/official-manual translation: each stage "Opens with / Main event / Ends with" and a "[KEEP CONSISTENT]" block [community C1]; fal: "Use @Image1 as the exact first frame and continue forward … Do not replay or recreate the [action] that happened before this frame" [platform:fal P10].
8. **Storyboard for strict layouts**: keyframes ("Use Images 1 to N in order as keyframes") when the shot composition must be reproduced exactly [official S1].
9. **Asset library / digital characters**: preset `asset://` characters give a stable, compliant face across all clips; authorized real-person assets for the owner's own talent [official S8].
10. **Anchor-shot workflow** (community): generate a hero shot, feed it back as `@Video 1` for style/camera in every later shot; change one variable per iteration [community C6, P10].

---

## 11. Platform parameter cheat-sheet

### 11.1 BytePlus ModelArk / Volcano Engine Ark (first-party API) [official S2, S3, S6]
- Endpoint: `POST https://ark.ap-southeast.bytepluses.com/api/v3/contents/generations/tasks` (BytePlus) / `https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks` (Volcano, per C11 [community]); `Authorization: Bearer $ARK_API_KEY`; async → poll "Retrieve a video generation task".
- `model`: `dreamina-seedance-2-5-260628` (BytePlus) / `doubao-seedance-2-5-260628` (Volcano [community C4, single-source]); 2.0: `dreamina-seedance-2-0-260128`, `-fast-260128`, `-mini-260615`; 1.5: `seedance-1-5-pro-251215`.
- `content[]`: `{type:"text", text}` · `{type:"image_url", image_url:{url}, role: first_frame|last_frame|reference_image}` · `{type:"video_url", video_url:{url}, role:"reference_video"}` · `{type:"audio_url", audio_url:{url}, role:"reference_audio"}`.
- `omni_reference_task_type`: auto | reference | edit | extend (2.5).
- `resolution`: 480p | 720p (default) | 1080p. `ratio`: 16:9 | 4:3 | 1:1 | 3:4 | 9:16 | 21:9 | adaptive (default). `duration`: -1 (default) or 4–30. `generate_audio`: true (default) | false. `watermark`: false (default) | true. `output_format`: mp4 (default) | mov. `return_last_frame`: false | true. `seed` and `camera_fixed`: 1.x only. `priority` 0–9, `callback_url`, `execution_expires_after`, `safety_identifier`.
- Example (2.5 reference-to-video): `{"model":"dreamina-seedance-2-5-260628","content":[{"type":"text","text":"…@Image1…"},{"type":"image_url","image_url":{"url":"https://…png"},"role":"reference_image"}],"generate_audio":true,"ratio":"16:9","duration":30}`.

### 11.2 Higgsfield (MCP connected to this stack) [platform:Higgsfield P1, P2]
- Model ids from `models_explore`: `seedance_2_5` — "Seedance 2.5 text-to-video, multimodal omni-reference generation, video edit, and video extension"; `ad_multiplier` — "Ad Multiplier video generation powered by Seedance 2.5" (same parameters); `seedance_2_0`; `seedance1_5`.
- `seedance_2_5` params: `mode` = `t2v` (default) | `omni_reference` | `video_edit` ("billed by that video's duration; 'duration' and 'aspect_ratio' are ignored") | `video_extension` ("'aspect_ratio' is ignored — the output follows the extended video"); `duration` 4–30 (default 5); `resolution` 480p | 720p (default) | 1080p; `generate_audio` true (default); `bitrate_mode` standard | high; `extension_mode` backward | forward (required for video_extension). `aspect_ratios`: auto, 21:9, 16:9, 4:3, 1:1, 3:4, 9:16. Media roles: `start_image`, `end_image`, `image_references`, `video_references`, `audio_references`.
- `seedance_2_0` params: `duration` 4–15 (default 5); `resolution` 480p | 720p | 1080p | 4k; `mode` std; `bitrate_mode`; `genre` auto|action|horror|comedy|noir|drama|epic; `generate_audio`; same roles and ratios; `supports_unlim: true`.
- `seedance1_5`: duration 4 | 8 | 12; 480p/720p/1080p; roles start_image, end_image; `generate_audio`.
- `generate_video` call shape: `params: { model, prompt, medias: [{value: <media_id|job_id>, role}], duration, aspect_ratio ("9:16" for TikTok/Reels; or width/height), count 1–4, get_cost, use_unlim }`. Uploads via `media_upload_widget` / `media_import_url` (URLs are never passed in `medias`).
- Higgsfield's web copy: "@Image 1" syntax, up to 50 references, "Up to high-resolution 4K upscaling", 10 s clip credits 30/65/90 at 480p/720p/1080p [P3, P4]. Reference-count breakdown and per-clip length limits are not published by Higgsfield (assume ModelArk limits) [gap].

### 11.3 fal.ai [platform:fal P6–P10]
- Endpoints: `bytedance/seedance-2.5/text-to-video`, `/image-to-video`, `/reference-to-video` (editing and extension both go through reference-to-video).
- Params: `prompt`; `image_url` (+ `end_image_url`) for i2v; `image_urls` (≤ 30), `video_urls` (≤ 10), `audio_urls` (≤ 10), ≤ 50 total, each video/audio 1.8–30.2 s, per-list total ≤ 30.2 s, audio needs an image or video; `resolution` "480p" | "720p" (default); `duration` "auto" (default) | "4"…"30" (strings); `aspect_ratio` "auto" (default) | 21:9 | 16:9 | 4:3 | 1:1 | 3:4 | 9:16; `generate_audio` true; `seed`; `end_user_id` (B2B). Output `{video:{url,content_type:"video/mp4",…}, seed}`.
- Reference wording: schema/README `[Image1] [Video1] [Audio1]`; learn pages `@Image1`. "Put spoken dialogue in double quotes for lip-synced audio."

### 11.4 Replicate [platform:Replicate P11]
- Model `bytedance/seedance-2.5`. Inputs: `prompt` (optional when media present; "works best with detailed, structured 'production brief' style prompts"); `image` (first frame; cannot be combined with references); `last_frame_image` (requires `image`); `reference_images` ≤ 30; `reference_videos` ≤ 10, combined ≤ 30 s; `reference_audios` ≤ 10, combined ≤ 30 s, "Requires at least one reference image or video"; `duration` -1…30 (default 5; "Editing mode requires -1"); `resolution` 480p | 720p (default); `aspect_ratio` 16:9 (default) | 4:3 | 1:1 | 3:4 | 9:16 | 21:9 | adaptive ("First/last-frame, editing, and extension modes require 'adaptive'"); `generate_audio` true; `watermark` false; `output_format` mp4 | mov; `seed` ("Reproducibility is not guaranteed"). References cited as `[Image1]`, `[Video1]`, `[Audio1]`.

### 11.5 WaveSpeedAI [platform:WaveSpeed P12–P16]
- Endpoints: `bytedance/seedance-2.5/text-to-video` (+ turbo), `/image-to-video` (+ turbo, "spicy"), `/video-edit` (+ turbo), `/video-extend`, talking avatar.
- t2v: `prompt`, `aspect_ratio` (16:9 default, 9:16, 4:3, 3:4, 1:1, 21:9), `resolution` 480p | 720p (default) | 1080p | **4k** (WaveSpeed-specific), `duration` 4–30 (default 5), `generate_audio` true, `reference_images` ≤ 30, `reference_videos` ≤ 10, `reference_audios` ≤ 10. i2v: `image`, `last_image`, `resolution`, `duration`, `generate_audio`. video-edit: `video` ("auto-trimmed to 30s max, padded to 4s min"), `reference_images`, `reference_audios`, duration/ratio follow input. video-extend: `video` ("uses up to last 30 seconds as context"), `duration` 4–30 of new segment. References written as `@image1`, `@video1`, `@audio1`.

### 11.6 Krea [platform:Krea P18]
- `POST https://api.krea.ai/generate/video/bytedance/seedance-2-5`: `prompt`, `duration` 4–30 (5), `resolution` 480p | 720p (default) | 1080p, `aspect_ratio` 16:9 (default) | 4:3 | 1:1 | 3:4 | 9:16 | 21:9, `generate_audio` (default **false** on Krea), `reference_images` ≤ 30, `reference_videos` ≤ 10, `reference_audios` ≤ 10, `start_image`, `end_image`, `enhance_prompt`, `seed`. No in-prompt tag syntax documented. Naming a film/studio/artist gets rejected.

### 11.7 Atlas Cloud [platform:Atlas P19]
- Same three endpoint names as fal; duration 4–30 or auto; 480p/720p ("native 4K forthcoming"); six ratios + adaptive; ≤ 30 images / 10 videos / 10 audio, total reference duration 30 s; audio-only referencing; MP4 or MOV; toggles for audio, watermark, last-frame return; documented params `model, prompt, duration, resolution, ratio, generate_audio` (mirrors ModelArk).

### 11.8 Dreamina / CapCut (consumer UI) [official S16, S17, S18]
- Reference tags `@Image1`, `@Video1`, `@Audio1`; up to 50 assets (30/10/10); durations up to 30 s ("beta long-video 180 s"); "4K" and "60 FPS" in premium tiers; region-level edit, upscale, interpolation, soundtrack; free daily credits; photorealistic faces gated behind verification [community P20].

### 11.9 Not verified
- Freepik/Magnific (`magnific.com/seedance-2`) returned HTTP 403; Freepik's own site lists Seedance 1.5 Pro only in search results. Volcano Engine Chinese doc pages (`docs.volcengine.com/docs/82379/…`) returned a JS shell; the BytePlus English mirror of the same docs was used instead.

---

## 12. Prompt skeleton for our pipeline (per clip)

Derived from sections 3–6: official 2.5 layout (asset binding → one-sentence summary → timeline → additional notes) [S1], the official 2.5 formula and bracket rules [S2], the 2.0 advanced formula and constraint words [S4], Dreamina's "Preserve … / Avoid …" tail [S17], and fal's start-state / timeline / end-state blocking [P10]. Writers fill every `{{…}}`; delete a block only if its rule says "omit if empty". Target 250–600 words for a 10–30 s clip, never > 900 words [S3]. Use integer-second timestamps only on Seedance 2.5; on 2.0 replace them with "Shot N:" labels [S1, S4].

```
[CLIP {{clip_no}} / {{clip_total}} — {{duration_s}} s, {{ratio}} — generation mode: {{t2v | first_frame | first_last_frame | omni_reference | video_extension}}]
(parameters go in the API call, not in the prose: resolution={{res}}, ratio={{ratio|adaptive}}, duration={{duration_s|-1}}, generate_audio={{true|false}}, output_format={{mp4|mov}}, return_last_frame=true)

ASSET BINDINGS (one line per uploaded asset, in upload order; omit if no assets)
@Image 1 = {{what it is}}. Use only: {{appearance / product geometry, colours, label, materials / scene layout & light / first frame}}. Do not use: {{background / pose / lighting / text / other people}}.
@Image 2 = {{…}}. Use only: {{…}}. Do not use: {{…}}.
@Video 1 = {{camera-movement | action | rhythm | effect}} reference. Use only: {{camera path, shot rhythm, cut points}}. Do not use: {{people, clothing, location, audio}}.
@Audio 1 = {{voice timbre | music | ambience}}. Use only: {{…}}.
{{If chaining:}} @Image 1 is the exact first frame; continue forward from that moment; do not replay or recreate what happened before it.

ONE-SENTENCE SUMMARY
{{Subject (name + 2–3 stable visible features)}} {{main action/event}} in {{location, time of day}}, {{genre/style}}, {{camera in one clause}}, {{sound in one clause}}.

START STATE (t = 0 s)
{{Who is where, facing which way; what each hand holds; product position and orientation; camera position, shot size, angle; light source and direction; ambient sound bed.}}

TIMELINE (continuous, integer seconds, no gaps; one main event and at most one camera move per interval; cause before reaction)
0-{{t1}}s: {{action with body part + range/speed/force}}; camera {{one movement or "locked-off"}}; {{SFX in <>}} {{music in ()}} {{dialogue: Speaker (language, delivery): "line"}}.
{{t1}}-{{t2}}s: {{…}}
{{t2}}-{{duration_s}}s: {{…}} Ends on {{held/frozen frame description}}.

CAMERA
{{Shot size}} {{angle}}; {{single primary move: "locked-off camera, fixed camera position" | "slow push in from … to …" | "parallel tracking at … height keeping subject in left third" | …}}; {{trigger: "the camera begins … only after …"}}; {{axis/side rule: "never cross the …"}}; {{lens/DoF}}.

LIGHT & LOOK
{{key light source + direction + quality}}; {{colour palette / grade}}; {{texture: film grain, phone-camera, studio}}; {{style words}}; HD, rich details, stable motion, no flicker.

AUDIO
{{"Dialogue: …" with speaker attributes, language named before any non-English line, mouths of non-speakers closed | "No dialogue"}}; {{ambience list}}; {{contact SFX tied to events}}; {{"(music: …)" | "No BGM; generate only environmental sounds and action sounds"}}; {{"No subtitles."}}

REFERENCE/PRODUCT INVARIANTS (product-swap clips)
Preserve exactly: {{product proportions, colours, label text/orientation, cap/button positions, logo placement}}; the product is one single object throughout; {{count of each key object stays N}}.

END STATE (t = {{duration_s}} s) — continuity handoff
{{Final positions, poses, hand contents, product orientation, camera position and shot size, light, sound state.}} The frame holds for the last {{0.5–1}} s. {{Next clip starts from this frame: yes/no.}}

CONSTRAINTS (short, grouped, last)
No {{cuts | slow motion}}, no duplicated {{people/products}}, no extra hands or fingers, no object teleportation, no identity or wardrobe change, no text overlays, no subtitles, no logos or watermarks other than the referenced product label, no camera shake {{unless handheld}}, {{scenario-specific: e.g. "liquid never flows uphill", "the column stays fixed"}}. Throughout the video, characters with completely identical appearance, clothing, and accessories are prohibited.
```

Filling rules for writers:
- Every `@` asset must have a "Use only / Do not use" line [S1, S2]; never rely on labels inside images [S1].
- Timestamps: continuous ranges; ~15–25 words per second; one main change per interval; no high-frequency actions; 2–5 s per beat for ads, 6–8 s for cinematic beats [S1, S17].
- One camera movement per shot; lock the camera with words, not a parameter [S3, S4].
- Dialogue: double quotes (or `{}` when using the bracket set), ≤ ~10 words per line, speaker attributes stated, language named for non-English, finish speech before the final held beat [S2, S3, S9; C7].
- Negative list stays short and at the end; only subtitles/audio negatives are guaranteed to be honoured, the rest lowers probability [S1, S4].
- For product swaps supply 2–4 single-view product photos as separate `@Image`s (front, 3/4, label close-up) and bind them as "the same single product" [S1, S4].
- Chaining: request `return_last_frame=true`; next clip = first-frame mode with `ratio=adaptive` (or `@Image 1` "is the exact first frame" in omni mode when other references are needed) [S3, S1, P10].
- Prefer `t2v`/`omni_reference` with `ratio` set explicitly to the platform aspect (9:16 for TikTok/Reels); locked modes inherit ratio from the asset, so the first frame must already be 9:16 [S2, S3].

---

## 13. Discrepancies between sources (self-check)

| Topic | Sources disagree | Resolution used in these notes |
|---|---|---|
| Max resolution of 2.5 | ModelArk API/tutorial/model-list: 1080p max (4K only Seedance 2.0 std) [S2, S3, S6]; Krea: 1080p max [P18]; fal/Replicate: 720p max [P6, P11]; WaveSpeed sells a "4k" tier [P13, P14]; Dreamina, Higgsfield web, TheNextWeb, Krea blog: "native 4K" [S16, P4, C13, P17] | Treat 1080p as the model's documented API maximum; "4K" is platform upscaling/marketing unless the owner verifies a platform's 4K output. |
| Max duration | 30 s everywhere official; "180 s beta" on Dreamina/Krea/Wikipedia [S16, P17, C12] | 30 s per generation; longer only via extension/stitching. |
| fps | 24 fps official [S6]; Dreamina "60 FPS premium" [S16] | 24 fps; 60 fps = interpolation. |
| Audio channels | ModelArk: mono output [S3]; Seed blog/arXiv: dual-channel/binaural [S12, S14] | Expect a mono file from the API; do not promise stereo. |
| Seed on 2.5 | ModelArk lists `seed` for 1.x only [S3]; fal/Replicate/Krea expose `seed` [P6, P11, P18] | Platform-only; weak reproducibility. |
| camera_fixed | ModelArk: 1.x only, not in reference scenarios [S3]; Replicate README mentions it, schema lacks it [P11]; APIYI: unsupported on 2.x [C4] | Not available on 2.5; lock via prompt language. |
| Reference tag syntax | `@Image 1` [S2], `@Image1` [S1, S16–S18, P9, P10, P4], `Image 1` [S1, S4, S5], `[Image1]` [S1, P6, P11], `@image1` [P14, P16] | All positional; use `@Image 1` unless a platform schema prescribes brackets. |
| Audio-only reference | ModelArk 2.5: allowed [S2, S3]; fal/Replicate: needs an image or video [P9, P11] | Follow the serving platform's rule. |
| Last frame with different ratio | "will be stretched" [S1] vs "automatically cropped to fit" [S3] | Always match ratios. |
| Editing duration drift | ≤ 0.3 s [S1] vs ≤ 0.4 s [S2, S3] | Budget 0.4 s. |
| Reference video input resolution | API page: 480p, 720p, 1080p, 4k [S3]; tutorial usage-limits: 480p, 720p [S2]; pixel-count bound 407,696–8,295,044 (≈ 3326×2494) [S2, S3] | Feed 720p–1080p reference clips; stay inside the pixel bound. |
| Prompt length | ≤ 1,000 English words [S3]; 30–100 words [S18]; 60–100 words [C5, C6] | Short guidance is for 2.0 single shots; 2.5 timeline prompts run 300–600 words in official examples. |
| Timestamps | 2.5 honours integer-second timestamps [S1]; 2.0 does not (shot labels only) [S1, S4] | Version-specific; the pipeline targets 2.5. |
| Seedance 2.0 release date | Feb 10 (search snippet), Feb 12 (Seed blog fetch) [S12], "early February" [S14] | Recorded as 10–12 Feb 2026. |
| Multi-view character sheets | 2.0: not recommended [S4]; 2.5: supported, but single-view above 5 subjects [S1] | Use separate single-view images. |
| Aspect ratio list on fal | learn page "16:9, 9:16, or auto" [P9] vs schema six ratios + auto [P6–P8] | Schema wins. |
| Community "official manual" (dev.to/apimodels/tryonr, C1–C3) | Claims to translate ByteDance's 2.5 manual; content matches the ModelArk 2.5 guide in substance (formula, brackets, limits, locked parameters) but adds templates not present in the English ModelArk doc | Used only for ideas tagged [community]; never for limits. |

Key limits with two or more agreeing sources: duration 4–30/-1; 480p/720p/1080p; six ratios + adaptive; 24 fps; 30/10/10 references and 50 total; ≤ 30 s combined A/V reference; 2–30 s per reference clip; 30 MB images; 15 MB audio; 200 MB video; 1,000-word prompt guidance (S3 only → [single-source] but official); locked ratio/duration rules (S1, S2, S3). Single-source items are marked inline.

---

## 14. Seedance 2.5 Director bundle (owner-supplied; `seedance\director\`; installed 2026-09-19)

- **What it is:** the complete `seedance-2-5-director` skill bundle, package revision **2.1.0** (2026-09-17), supplied by the owner as `C:\Users\Glaresquare1\Documents\prompts\seedance-2-5-agent-guide.zip` and installed whole (SKILL.md, references, assets, docs, evals, scripts, manifest) into `seedance\director\`. Integrity: `python seedance\director\scripts\validate_bundle.py seedance\director --integrity` → PASS on install (10 unit tests OK). **READ-ONLY at run time**, exactly like this file.
- **What it adds (method, not numbers):** the operating contract `recover intent → inspect inputs → establish world state → plan dependencies → stage the action → audit → compile → recheck the written prompt → deliver`; the intent contract (viewer takeaway, required content AND required method, initial state, essential events, ending, duration/frame, sound, cut policy, fixed traits, allowed changes, references, unknowns); the world-state ledger (`identity | location | orientation | holder/support | contents/count/condition | mechanism state | visibility | ongoing motion`); causal expansion of every essential action (`preconditions → actor/mechanism → reachable path and contact → transfer/change → observable consequence → updated state`); backward-then-forward dependency validation; the 15 anomaly categories with repairs (`references\continuity-and-causality.md` §5); the cross-cutting safeguards (passive processes keep running, hidden ≠ absent, a cut is not a reset, dependency closure of edits, unknowns stay unknown); the compile organisation (FORMAT AND INTENT / REFERENCE OWNERSHIP / INITIAL WORLD STATE / CONNECTED ACTION AND CAMERA / ENDING / LOOK AND SOUND / CONTINUITY CONSTRAINTS); the mandatory release gate (intent+method, state+causality, feasibility+visibility, temporal/cinematic flow, input/contract integrity, craft+economy; blocker / major / polish); the per-operation checks (text-to-video, first-frame, multi-reference, keyframes, motion/clay, edit, extend, loop); the defect record `timestamp | observed failure | violated requirement | possible cause | one proposed change | pass condition`; the pass/fail/unknown review discipline; ten worked example patterns; 46 behavioural cases.
- **Where the stack uses it:** continuity author (ledger, long-range dependency and boundary tables → continuity sheet §J/§K), prompt writers (compile + release gate on top of the stack's START STATE → TIMELINE → END STATE contract), anomaly checkers (category → lens mapping, `references\anomaly-checklist.md` §2b), clip QA (defect record + review record), compression planner (preserve the method, never an ellipsis that skips a required action). The launch template tells every agent that `seedance\` is read-only; the bundle is inside it.
- **Precedence (binding):** (1) numbers, limits, syntax and platform parameters come from THIS file and `SEEDANCE-EDIT.md` (they quote the official ModelArk docs); the bundle's sources are an inherited 2026-09-17 snapshot that its own `references\sources.md` says was not re-verified. (2) The bundle's METHOD governs how prompts are planned, written and audited; where the stack's own rule files (`physics-rules.md`, `blending-rules.md`, `continuity-rules.md`, `prompt-template.md`, `anomaly-checklist.md`) say the same thing in different words, both apply; where they conflict on method, the director's rule wins **except** the stack's owner rules (no speech captions, no original brand marks, realism beats length, START/END states string-identical to the continuity sheet, the Q4a dialogue rule, the swap-map product invariants), which always win. (3) The director's "authorized surreal rules" clause applies only when the owner chose a non-realistic style in Q5; a real-footage replication stays physical.
- **Cross-check of the bundle's numeric claims against this file (2026-09-19):** up to 30 s per generation — agrees with §2.1; reference mix up to 30 images / 10 videos / 10 audio — agrees with §3; "extensions" and "timestamp-directed editing" — agree with §1 and `SEEDANCE-EDIT.md`; the bundle states no fps, resolution, ratio, file-size or prompt-length numbers (it defers to provider contracts) — this file's §2, §3, §8 remain the only source for those; the bundle's S4 (Runway "Creating with Seedance 2.5") is a serving-platform page not in `sources.md` P-list — Runway parameters are NOT used by the stack (Higgsfield/ModelArk parameters in §11 stay authoritative). No contradiction found.
- **Do not import from the bundle:** its `agents\openai.yaml` (foreign host metadata), its "one finished prompt by default" response contract (the stack writes one file per clip in the template format, then the main session assembles `prompts.json` — the director's compile organisation is applied INSIDE the `## Prompt` block), its Deepgram/OpenAI mentions, and its example subjects (the bundle itself forbids importing example props into unrelated work).
