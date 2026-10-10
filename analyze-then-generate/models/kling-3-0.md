---
guide: kling-3-0
title: Kuaishou Kling 3.0 (incl. Kling 3.0 Turbo and 3.0 Motion Control)
provider: Kuaishou — Kling AI, served by Higgsfield
higgsfield_model_ids: [kling3_0, kling3_0_turbo]
guide_version: 1.0
last_verified: 2026-09-30
catalog_snapshot: higgsfield/catalog-snapshot-2026-09-30.json
documentation_depth: medium
---

# Kuaishou Kling 3.0 — model engineering guide

> Scope: Kling VIDEO 3.0 as served by Higgsfield under `kling3_0` ("Kling v3.0 — Multi-shot, audio sync,
> motion transfer") and the speed-optimised `kling3_0_turbo` ("Fast text-to-video and single start-frame
> animation"). Covers text-to-video, start-frame and start+end-frame generation with native audio, and
> Higgsfield Elements for identity/product consistency (Kling 3.0 only). Also documents the separate legacy
> MCP tool `motion_control` ("Kling 3.0 Motion Control"). Kling 3.0 Omni Edit and Kling 2.6 have their own
> guides. Project output format is fixed: vertical 9:16 at 720p (§2.6).
> The live `models_explore` catalog always wins over the parameter tables in this file.
>
> Evidence tags: **[OFFICIAL]** provider docs, paper, model card, API reference, first-party prompt
> guide or first-party examples · **[HF]** Higgsfield catalog, MCP tool contract or first-party
> Higgsfield docs · **[SECONDARY]** reputable third-party testing or articles · **[INFERRED]**
> engineering inference that must be verified in use. Source keys (S1…) point to §8.

## 1. At a glance

- **Positioning.** Kling 3.0 launched on 2026-02-06 with Video 3.0 Omni and Image 3.0 [OFFICIAL S5]. The Kling 3.0 Model Series "utilize a deeply integrated unified model training framework, achieving more native multimodal input and output", with native audio and element consistency control; "up to 15 seconds of continuous video, with a flexible duration ranging from 3 to 15 seconds"; multi-shot narratives; start frame + element reference; "Compared to Video 2.6, Video 3.0 excels at managing referencing three or more characters"; dialogue in Chinese, English, Japanese, Korean and Spanish with dialects and accents; "native-level text output" [OFFICIAL S1]. Turbo (2026-06-17) is a speed- and cost-optimised variant with audio included and improved lip sync [SECONDARY S12].
- **Best for:** cinematic 3–15 s shots with strong motion and physical detail (Higgsfield: "Cloth dynamics, hair movement, fluid behavior, and contact collisions") [HF S17]; native dialogue with lip sync; identity/product locking through Elements; start/end-frame bridging; preserving text already present in an approved start frame [OFFICIAL S1]; fast drafts with Turbo.
- **Weaker at:** no multi-shot switch, reference roles, negative prompt, cfg or camera-control parameter on the Higgsfield MCP [HF S8]; tests report occasional character mix-ups or left-right swaps between shots, a line reassigned to the wrong speaker and an unwanted extra character [SECONDARY S13]; multi-voice dialogue beyond two speakers degraded in 2.6 [OFFICIAL S4] (3.0 claims improvement [OFFICIAL S1]).
- **Choose this model when** you want a polished 3–15 s single shot or start-frame animation with native audio, Element-locked identity/product, or faithful carry-over of text in an approved frame.
- **Choose another model when** you need attached image/video/audio references (Seedance 2.0/2.5), guaranteed multi-shot structure through the MCP (one clip per shot, or a model with exposed multi-shot parameters), editing of footage (`kling_video_edit`, Seedance 2.5) or clips longer than 15 s.

| operation | how to invoke on Higgsfield | notes |
|---|---|---|
| Text-to-video | `model:"kling3_0"` or `"kling3_0_turbo"`, no `medias` | ratios 16:9 / 9:16 / 1:1 |
| Start frame to video | role `start_image` | both ids |
| Start + end frame | `start_image` + `end_image` | `kling3_0` only |
| Element-locked identity/product | `<<<element_id>>>` in the prompt | `kling3_0` only [HF S8] |
| Multi-shot | prompt-level only (unverified) | switch not exposed in the MCP (§3.5) |
| Motion transfer | legacy tool `motion_control` (no prompt) | Genjutsu `hf_mult_motion_control` is Higgsfield's default route [HF S8] |
| Video edit | N/A — see `kling-3-0-omni-edit.md` | |

## 2. Higgsfield parameter surface

### 2.1 Parameters per model id

| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `kling3_0` | `duration` | number, 3–15 s | 5 | "Duration in seconds (3-15)." Unsupported values snap or clamp [HF S8]. |
| `kling3_0` | `mode` | `std`, `pro`, `4k` | `std` | "'std' (standard), 'pro' (higher quality), or '4k' (4K resolution)." Tiers ≈ 720p / 1080p / 4K [HF S9; SECONDARY S20]. Project: `std` (§2.6). |
| `kling3_0` | `sound` | `"on"`, `"off"` (string) | `"on"` | "Generate audio. Use 'off' for silent video and lower credits." |
| `kling3_0` | `aspect_ratio` (call-level) | `16:9`, `9:16`, `1:1` | not stated | no `auto`; project: `9:16` |
| `kling3_0` | flags | `supports_unlim: true` | — | `use_unlim:true` only on explicit user request [HF S8, S14] |
| `kling3_0_turbo` | `resolution` | `720p`, `1080p` | `720p` | "Output resolution." Project: `720p`. |
| `kling3_0_turbo` | `duration` | number, 3–15 s | 5 | "Duration in seconds (3-15)." |
| `kling3_0_turbo` | `aspect_ratio` (call-level) | `16:9`, `9:16`, `1:1` | not stated | project: `9:16` |
| `kling3_0_turbo` | audio toggle | none | — | No `sound` parameter; Kling describes Turbo as audio-included [SECONDARY S12]; ffprobe the result and strip audio locally if silence is needed. |
| both | `negative_prompt`, `cfg_scale`, `camera_control`, `multi_shot` / `shot_type` / `multi_prompt`, `element_list` / `voice_list`, watermark, seed | — | — | **Not exposed on Higgsfield** [HF S8]. Kling's API has `negative_prompt`, `cfg_scale` (0–1, default 0.5), multi-shot (up to 6 shots with per-shot durations), elements and first/end-frame `image_list` [SECONDARY S10, S11]. Approximations: exclusions in prose (§3.10), explicit wording instead of cfg, camera moves in words (§3.6), one clip per shot (§3.5), Elements tokens (§3.7). |

Call-level keys: `model`, `prompt`, `medias`, `duration`, `aspect_ratio`, `get_cost` (preflight, submits nothing), `use_unlim` [HF S8].

### 2.2 Media roles

| role | what it controls | limits / count | notes |
|---|---|---|---|
| `start_image` (both ids) | first frame: composition, identity, product, scene, and any text in it | 1; jpg/jpeg/png, ≥300 px, ≤10 MB [OFFICIAL S3]; aspect 1:2.5–2.5:1 [SECONDARY S10] | text in the frame is preserved (§3.11) |
| `end_image` (`kling3_0`) | last frame | 1, with `start_image` | "Generation with only an end frame is not supported" (O1) [OFFICIAL S3]; Higgsfield copy suggests end-frame-only use [HF S17] — don't rely on it |
| Elements `<<<element_id>>>` (prompt token, `kling3_0`) | reusable identity or product reference | Kling builds elements from 2–4 reference images or a short video [OFFICIAL S1] | "the backend injects the image and rewrites it to @element_name" [HF S8] |

`medias[].value` is a media UUID or completed job id, never a URL; local files arrive via `media_upload` → HTTP PUT → `media_confirm`; results via `jobs_wait` [HF S8].

### 2.3 Duration, resolution, aspect ratio, audio

- **Duration** 3–15 s on both ids [HF S8; OFFICIAL S1].
- **Resolution** `kling3_0`: std / pro / 4k ≈ 720p / 1080p / 4K [HF S9]; Kling's 3.0 guide prices 720p and 1080p tiers and its blog a separate 4K mode [OFFICIAL S1, S6]. Turbo: 720p or 1080p [HF S8].
- **Aspect ratio** 16:9, 9:16, 1:1 [HF S8].
- **Audio** `kling3_0`: `sound:"on"` gives dialogue, SFX and ambience in the same pass — "micro-sounds, environmental textures, and timing cues that match physical interaction on screen" [HF S9]. Dialogue languages: Chinese, English, Japanese, Korean, Spanish; other languages are translated into English [OFFICIAL S1].

### 2.4 Call recipes

All recipes use the fixed 9:16 / 720p format (§2.6). Add `"get_cost": true` to preflight.

**Text-to-video (silent)**
```json
{"model":"kling3_0","prompt":"<PROMPT>","duration":5,"aspect_ratio":"9:16","mode":"std","sound":"off"}
```
**Text-to-video with native audio**
```json
{"model":"kling3_0","prompt":"<PROMPT>","duration":10,"aspect_ratio":"9:16","mode":"std","sound":"on"}
```
**Start frame** (exactly-9:16 image)
```json
{"model":"kling3_0","prompt":"<PROMPT describing change from the frame>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"}],"duration":8,"aspect_ratio":"9:16","mode":"std","sound":"on"}
```
**Start + end frame**
```json
{"model":"kling3_0","prompt":"<PROMPT describing the transition>","medias":[{"value":"<IMAGE_MEDIA_ID_FIRST>","role":"start_image"},{"value":"<IMAGE_MEDIA_ID_LAST>","role":"end_image"}],"duration":6,"aspect_ratio":"9:16","mode":"std","sound":"off"}
```
**Elements (identity + product), optionally with a start frame** — Kling supports "Start Frame + Element Reference" [OFFICIAL S1]; the combination through Higgsfield is unverified [INFERRED].
```json
{"model":"kling3_0","prompt":"<<<ELEMENT_ID_PERSON>>> picks up <<<ELEMENT_ID_PRODUCT>>> from the counter ...","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"}],"duration":8,"aspect_ratio":"9:16","mode":"std","sound":"on"}
```
**Turbo (text or start frame)**
```json
{"model":"kling3_0_turbo","prompt":"<PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"}],"duration":5,"aspect_ratio":"9:16","resolution":"720p"}
```
**Legacy Kling 3.0 Motion Control** — separate MCP tool, not `generate_video`; no prompt; 9:16 character image and 9:16 motion clip. Confirm argument names against the live schema (`ToolSearch select:mcp__higgsfield__motion_control`) [HF S8].
```json
{"image_id":"<IMAGE_MEDIA_ID>","motion_video_id":"<VIDEO_MEDIA_ID>","resolution":"720p","scene_control":"video"}
```

### 2.5 Parameter gotchas

- `sound` is a **string** on `kling3_0`, a boolean on `kling2_6`, `generate_audio` on Seedance; Turbo has no audio toggle [HF S8].
- `mode` is a quality/resolution tier, not a task selector; drafting in `4k` is listed as a common mistake [HF S9].
- No `auto` ratio [HF S8]; supply start/end frames at exactly 9:16.
- Multi-shot keys are not in the MCP catalog, and Kling states "When 'Multi-Shot' is disabled, the model will default to generating a single-shot video" [OFFICIAL S1]. Don't send undocumented multi-shot keys unless `models_explore` lists them.
- Elements are documented for `kling3_0`, not Turbo [HF S8].
- Motion transfer: Higgsfield routes Genjutsu motion transfer to `hf_mult_motion_control` and says never to use legacy `motion_control` for a Genjutsu edit [HF S8]; use `motion_control` only when the user picks Kling 3.0 Motion Control.
- Prompt length: Kling's API caps prompts at 2,500 characters [SECONDARY S10, S11].

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-generate)

| id / operation | params to send | expected output | post-processing |
|---|---|---|---|
| `kling3_0` t2v / Elements | `aspect_ratio:"9:16"`, `mode:"std"` | 720p tier [HF S9; SECONDARY S20] → 720×1280 expected [INFERRED] | ffprobe; if not 720×1280, `atg.py conform` (downscale, or scale-to-fill + minimal crop); never stretch |
| `kling3_0` start / end frame | same + exactly-9:16 frame(s) | 720×1280 expected [INFERRED] | conform frames to 9:16 before upload; verify output |
| `kling3_0_turbo` | `aspect_ratio:"9:16"`, `resolution:"720p"` | 720×1280 expected [INFERRED] | ffprobe; conform if needed |
| `motion_control` | `resolution:"720p"`, 9:16 image and 9:16 motion clip | aspect follows the image or the motion clip depending on `scene_control`/orientation [HF S15; OFFICIAL S18] | reframe both inputs to 9:16 first; verify output |

`pro` (≈1080p) followed by a deterministic downscale is possible but is not the project default [INFERRED].

## 3. How the model reads a prompt

### 3.1 Recommended prompt structure (ordered elements, formula, length, language, prose vs. lists)

- **Kling's formula (official blog):** Subject → Action → Scene → Camera → Lighting & Mood ("A woman in a striped shirt" / "Walks toward camera" / "Outdoor terrace" / "Close-up, push-in" / "Golden hour, soft haze") [OFFICIAL S6]. O1 phrasing: "Subject (subject description) + Movement + Scene (scene description) + (Cinematic Language + Lighting + Atmosphere)" [OFFICIAL S3]; 2.6 adds audio: "Scene + Element + Movement + Audio + Other" [OFFICIAL S4].
- **Official 3.0 long-shot style:** camera setup and tone first, protagonist with wardrobe and hand-specific props, then time markers ("At the 4th second… In the final 3 seconds…"), ending on overall atmosphere (§4.0 E3) [OFFICIAL S1].
- "Name visible details such as haze, rim light, long shadows, soft golden sunlight, cold blue night tones, or reflections on wet pavement when those details matter" [OFFICIAL S6].
- **Length:** ≤2,500 characters [SECONDARY S10]; official 15 s example ~250 words; start simple, vary systematically [OFFICIAL S1, S6]. English prompts are fine; one prompt language except intentional multilingual dialogue [OFFICIAL S1].

### 3.2 Subject and identity

- Concrete visible features at first mention; "Character labels must be unique and consistent" [OFFICIAL S4]; avoid pronouns in multi-character scenes [SECONDARY S19].
- Kling says 3.0 "excels at managing referencing three or more characters" [OFFICIAL S1]; still anchor each character to set objects to prevent left-right swaps [SECONDARY S13; INFERRED].
- Locked identity: Element or start frame; describe only what the Element does, "since its look is already defined by the element itself" [HF S9].

### 3.3 Action, motion and physical interaction

- The 15 s window is pitched for continuity: "Say goodbye to fragmented assembly and embrace a story with real progression and flow." [OFFICIAL S1]. Order beats with explicit transitions.
- Avoid overloading one shot with several actions [HF S9]; give hands explicit jobs ("clutches a small white flower in her right hand and lifts the hem of her dress with her left") [OFFICIAL S1].
- Marketed physics: "Characters transfer weight, vehicles lean into turns, liquids obey gravity" [HF S17]; still state contact, direction and end state (§3.14).

### 3.4 Environment, lighting and style

- Name light direction, quality and palette ("cold blue night and silvery white starry sky") [OFFICIAL S1, S6]. No genre parameter on `kling3_0` [HF S8]. Anchor locations to durable objects [INFERRED].

### 3.5 Chronology, timing and multi-shot structure

- **Timestamps:** "At the 4th second…", "At the 8th second…", "In the final 3 seconds…" inside one continuous shot [OFFICIAL S1]; Higgsfield examples use "0-1.5s:" ranges [HF S9].
- **Multi-shot in Kling:** automatic ("the model will automatically plan shot transitions") or "Custom Multi-Shot" with shot count and durations; with the switch on "the model will generally follow the prompts" [OFFICIAL S1]. Custom syntax: "Shot 1, profile shot of …, cinematic handheld. Shot 2, …" [OFFICIAL S1]; Omni uses "Shot 1 (3s): …" [OFFICIAL S2]. API mirrors: up to 6 shots, ≥3 s each, 15 s total [SECONDARY S10].
- **On the Higgsfield MCP the switch is absent**, and with it off "the model will default to generating a single-shot video" [OFFICIAL S1]. Options: (1) one continuous shot with time markers (reliable) [OFFICIAL S1]; (2) prompt-level shot labels — test once at `std`, 5 s, `sound:"off"` [INFERRED]; (3) one generation per shot, "Use the final frame of one scene as the start frame of the next", same Elements in every shot [HF S9].

### 3.6 Camera language and dedicated camera / motion controls

- Official 3.0 camera phrases: "ultra-wide-angle medium-long shot tracking horizontally", "the stabilizer moves low to the ground", "camera accelerates forward with her", "orbits the protagonist in a smooth 360-degree pan", "pushes in over the protagonist's shoulder", "low-angle rear wide shot, tracking behind", "high-angle wide shot with gentle downward tilt", "first-person POV", "cinematic handheld", "profile shot", "frontal macro shot" [OFFICIAL S1]. Blog: close-up, medium close-up, full body, establishing wide, push-in (dolly-in), pan, tilt, tracking, with slow/steady/quick pacing [OFFICIAL S6]; understands "shot-reverse-shot dialogues" and "cross-cutting dialogue" [OFFICIAL S1].
- One move per shot, described explicitly [HF S9]. API `camera_control` presets are not exposed [SECONDARY S16]; write start framing, move and end framing; static: "locked-off tripod shot; the camera does not move" [INFERRED].

### 3.7 References (image / video / audio): syntax, roles, what is inherited and what must be excluded

- Only frames and Elements are available [HF S8]; describe voices in words.
- **Elements:** reusable reference images placed as `<<<element_id>>>`; Higgsfield injects the image and rewrites the token to `@element_name` [HF S8]; list them with `show_reference_elements` (read-only). "Tag the same element in every shot where it appears"; Elements keep "identity, proportions, and spatial relationships from shot to shot" [HF S9]. Kling elements come from "2-4 reference images" or a short video, optionally with a bound voice — "it's not recommended to set the tone again in the prompt" for voice-bound elements [OFFICIAL S1]; voice binding is not exposed through the MCP [HF S8].
- Text in frames and element images carries into the video (§3.11).

### 3.8 Start and end frames

- Describe how the scene evolves from the image; keep prompt and image consistent ("ensure image content matches the text description", 2.6 tip) [OFFICIAL S4].
- Start + end: frames "can differ in tone/style; the model bridges them"; describe the transition; misaligning the prompt with the end frame is a common mistake [HF S9]. End frame only with a start frame [OFFICIAL S3]; Turbo takes only a start frame [HF S8].

### 3.9 Audio, dialogue and sound (if supported)

- Dialogue format: "Mom (softly, in a surprised tone): Wow, I didn't expect this plot at all. Dad (in a low voice, agreeing, in a calm tone): Yeah, it's totally unexpected." — `Name (tone): line` [OFFICIAL S1]; the 2.6 bracket format `[Character A, angrily] says, "…"` also works [OFFICIAL S4].
- Dialects/accents: "Simply tag the desired dialect or accent for the speech content"; mixed-language scenes supported [OFFICIAL S1]. English speech: lowercase words, uppercase only acronyms and proper nouns [OFFICIAL S4; SECONDARY S10].
- Action before line — official example: "The black-suited agent slams his hand on the table. [Black-suited Agent, angrily shouting]: "Where is the truth?"" [OFFICIAL S4]. Prefer ≤2 speakers per beat [INFERRED from OFFICIAL S4 and SECONDARY S13].
- SFX: "Sound Source (Action/Object) + State + Professional Sound Effects"; ambience: "Scene + Sound Elements + Spatial Reverb" [OFFICIAL S4]. Silence: `sound:"off"` [HF S8].

### 3.10 Negative constraints (is there a negative-prompt field on Higgsfield? how to phrase exclusions)

- No negative-prompt field on Higgsfield [HF S8], although Kling's API/app have one and Kling reports stronger negative-prompt adherence in 3.0, including image-to-video [OFFICIAL S7; SECONDARY S10].
- Positive states first ("plain unmarked walls", "one cup on the table"), then one short scene-specific exclusion sentence [INFERRED].

### 3.11 Visible text

Policy: **Edit Mode** removes all source text unless the user keeps specific text; **Analyze Mode** may add intentional new text, by default in deterministic post (FFmpeg/libass); reference wording, usernames and watermarks are never copied.

- **(a) Reliability:** Kling claims "native-level text output, which accurately preserves textual details from original images" and that the model "can automatically identify text content in uploaded images (such as signs, captions, or logos) and maintain text consistency" [OFFICIAL S1]; its blog gives a recipe for requested text ("Write the exact words, placement, surface, and camera distance. Keep the text short when readability matters.") [OFFICIAL S6]. Independent verification of spelling accuracy for newly generated text was not found [INFERRED gap]. Verdict: strong for keeping approved text already in a start frame; new short scene text is plausible but must be QA'd; captions go to post.
- **(b) Clean plate:** Kling's documented text-avoidance lever is its negative-prompt field, which Higgsfield does not expose [OFFICIAL S7; HF S8]. Therefore: start frames and Element images must be text-free (Kling preserves detected captions and logos) [OFFICIAL S1]; avoid quoted strings except dialogue; describe signs, packaging and screens as blank or abstract; end with "No captions, subtitles, on-screen text, logos or watermarks appear." [INFERRED]; QA frames.
- **(c) Intentional in-frame text (scene text only):** either put the exact text in the approved start frame (preserved) [OFFICIAL S1] or write "the exact words, placement, surface, and camera distance" in quotes, short, on a steady surface ("a matte white shop sign above the door reads "OPEN" in black block letters, seen from medium distance") [OFFICIAL S6 pattern]. Verify spelling frame by frame.
- **(d) Source text in edits:** N/A for these ids — use `kling_video_edit` or Seedance 2.5 `video_edit`.

### 3.12 Character / identity consistency

- One Higgsfield Element per approved person, tagged at every mention, optionally with a clean start frame of the same person [HF S8, S9; OFFICIAL S1]. Kling: element locking keeps key subjects stable "Regardless of camera movements and scene development" [OFFICIAL S1].
- Reduce swaps: distinct wardrobe colours, positions anchored to set pieces, one speaker per beat, few characters per shot [SECONDARY S13; INFERRED]. Approved references replace source people; never describe a source person's face [INFERRED].

### 3.13 Product and object fidelity (geometry, proportions, labels, scale, handling)

- Save the product as its own Element (front, side, back, detail) and tag it wherever it appears [OFFICIAL S1; HF S8]. Approved label side toward camera in the start frame — Kling preserves image text [OFFICIAL S1].
- State count, rigidity, size relative to the hand, grip and orientation; slow moves; end on a steady hero framing [INFERRED].

### 3.14 Integration and continuity (scale, orientation, contact, grip, occlusion, scene-light inheritance, reflections, shadows, persistent object states across the timeline)

- **Scale / orientation / grip / occlusion:** "<<<ELEMENT_ID_PRODUCT>>> is palm-sized, held upright in the right hand with the thumb on the lid, logo side toward the camera; the left hand never touches it" [INFERRED]; name what passes in front ("a passer-by crosses in front of the counter at the 4th second").
- **Scene light:** Kling reads named light cues [OFFICIAL S6]; tie inserted items to them ("the product catches the warm rim light from the window behind; its reflection shows in the glossy counter; its shadow falls toward the camera") [INFERRED]. Elements keep "identity, proportions, and spatial relationships" but lighting must still be stated [HF S9; INFERRED].
- **Persistent states:** restate states at each time marker ("At the 6th second, the mug she set down is still on the left edge of the table, half full") [INFERRED]; keep the same hand until a described release.
- **Known failures:** character mix-ups and left-right swaps between shots, reassigned lines, unwanted extra characters, empty opening frames [SECONDARY S13].
- **Across clips:** Higgsfield's help centre: "Upload Start and End Frames. These anchor the motion at both ends and make transitions predictable. Use the final frame of one scene as the start frame of the next to chain shots seamlessly." [HF, https://higgsfield.ai/creator-hub/help-center/ai-models/how-do-i-use-kling, 2026-10-01]. Hand-off frame: `atg.py last-frame` (exact, lossless); `end_image` = an approved keyframe of the planned end state (keyframe ladder). Reuse the same Elements, mode, ratio and audio setting; restate positions, hand contents and light at the start of each prompt [INFERRED]. Kling's own Extend (4–5 s per round) is not on the MCP [OFFICIAL; HF]. No seed [HF S8].

## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach

**E1 — custom multi-shot** (Kling 3.0 guide, S1): "Shot 1, profile shot of black man driving a truck, cinematic handheld. Shot 2, frontal macro shot of black man driving a truck, cinematic handheld. Shot 3, macro shot of hands on the steering wheel, cinematic handheld. Shot 4, macro shot of a weathered picture of a young black child laying on the passenger side seat, cinematic handheld."

**E2 — multi-character dialogue** (S1): "Mom (softly, in a surprised tone): Wow, I didn't expect this plot at all. Dad (in a low voice, agreeing, in a calm tone): Yeah, it's totally unexpected."

**E3 — 15 s continuous shot with time markers** (S1): "Opening with an ultra-wide-angle medium-long shot tracking horizontally, the stabilizer moves low to the ground, with a highly contrasting romantic cinematic tone of cold blue night and silvery white starry sky […] The protagonist is a young woman in a dark green long dress, running with all her might on the garden lawn illuminated by moonlight; […] she clutches a small white flower in her right hand and lifts the hem of her dress with her left […] At the 4th second, the camera accelerates forward with her […] At the 8th second, the camera gradually zooms in to a medium shot […] In the final 3 seconds, the camera keeps moving forward […]"

**E4 — dialect tag** (S1): "In a high-rise office building, the man leaned back, wearing a tired, disdainful expression, and said in Cantonese: […]"

**E5 — Omni storyboard and element use** (Kling 3.0 Omni guide, S2): "Shot 1 (3s): Wide shot. A neon-lit street corner late at night, wet pavement reflecting lights. @Element1 leans against a red phone booth, smoking, with strong motion blur." · "Long take. On a windy day in an Icelandic mountain range, @Male Protagonist says with a barely contained smile, 'Do you think our wedding is too simple—like there's no one here to bless us?' […]"

**E6 — camera-first single shot** (Kling blog, S6): "A smooth and deliberate dolly-in tracking shot approaching a classical marble statue […] The camera starts from a medium-wide distance and slowly moves forward […] Highly cinematic, realistic lighting with soft natural daylight, subtle god rays."

Patterns these teach [derived from E1–E6]:
- **Order:** camera setup and tone first, then subject (wardrobe, what each hand holds), then action beats, then atmosphere (E3, E6).
- **Sentence style:** multi-shot lines are terse comma lists ("Shot N, <shot type> of <subject/action>, <camera style>") with the same style tag repeated per shot (E1); single shots are flowing prose (E3).
- **Time:** "At the Nth second…", "In the final 3 seconds…" in continuous shots; "Shot 1 (3s):" durations in storyboards (E3, E5).
- **Subject vs camera motion:** the camera gets its own clause each beat ("the camera accelerates forward with her") (E3).
- **Camera vocabulary:** shot type + angle + rig ("stabilizer", "handheld", "tracking") (E1, E3, E6).
- **References:** `@Element` names used as the subject noun (E5); on Higgsfield the `<<<element_id>>>` token plays this role.
- **Dialogue:** `Name (tone, emotion): line`, or a speech verb with a quoted line; dialect/language tags before the line (E2, E4, E5).
- **Detail level:** concrete wardrobe, hand assignments, light colours; 150–250 words for 15 s, one line per shot for storyboards.
- **Exclusions:** none in the official examples — clarity comes from positive specification; add exclusions only for project policy (§3.10, §3.11).
- Slow motion appears only when explicitly written (E3's "drifting down in slow motion") — so state "real-time speed" when it matters [INFERRED].

### 4.1 Text-to-video

```text
<Camera setup: shot size, angle, rig/move>, <tone and palette>. <Subject: age, build, wardrobe, what each hand holds> <main action> in <scene with named light direction and colour>. At the <n>th second, <next beat>; the camera <move>. In the final <k> seconds, <ending action>; the camera settles on <final composition>. <Name (tone): "line"> <ambience and action sounds>. <Atmosphere>, real-time speed. No captions, subtitles, on-screen text, logos or watermarks appear.
```
Worked example (10 s, `sound:"on"`):
```text
Handheld medium shot, warm late-afternoon light through a shop window from the left, natural colours. A woman in her thirties in a rust-coloured cardigan walks into a small plant shop carrying a folded tote bag in her left hand. At the 3rd second, she stops at a wooden table and lifts a small potted fern with her right hand, turning it to look at the leaves; the camera pushes in to a close-up. At the 6th second, she smiles and says (softly, pleased): "this one." In the final 3 seconds, she places the pot into the open tote bag and the camera settles on the bag and her hands. Quiet shop ambience, leaves rustling, the soft thud of the pot in the bag. Calm, cosy atmosphere, real-time speed. No captions, subtitles, on-screen text, logos or watermarks appear; the shop walls and pots are plain.
```

### 4.2 Start frame (and end frame) to video

```text
Starting from the first frame, <camera behaviour>; <what moves and how, which hand>. At the <n>th second, <next beat>. [The shot ends on the last frame: <how the transition resolves into it>.] <Light stays: direction, colour, shadow side>. <Sound or silence>. Keep <identity, product shape and proportions, layout> exactly as in the frame. No captions, subtitles, on-screen text, logos or watermarks appear.
```
Worked example (start + end frame, 6 s, `sound:"off"`):
```text
Starting from the first frame, the camera tracks slowly from the rear wheel of the parked electric scooter along its deck toward the handlebar while the street lights switch off one by one at dawn. The shot ends on the last frame: a three-quarter front view of the same scooter with its headlight on. Cool dawn light from the right keeps the scooter's shadow on the left. Keep the scooter's frame shape, wheel size and colour exactly as in the frames; one scooter only. No captions, subtitles, on-screen text, logos or watermarks appear.
```

### 4.3 Reference-to-video

Elements are the only reference mechanism on `kling3_0` (not Turbo) [HF S8].
```text
<Camera setup and tone>. <<<ELEMENT_ID_A>>> <action> in <scene with light>. <<<ELEMENT_ID_B>>> (product) is <position and state>; <how A handles B: hand, grip, orientation, size relative to the hand>. At the <n>th second, <<<ELEMENT_ID_A>>> <next action>. <<<ELEMENT_ID_A>>> (tone): "<line>". <Light, reflection and shadow on the product>. <Sound>. The product keeps its exact shape and proportions; one of each; real-time speed. No captions, subtitles, on-screen text, logos or watermarks appear.
```
Worked example (8 s):
```text
Static medium shot at a sunlit kitchen counter, soft morning light from the window on the right. <<<ELEMENT_ID_PERSON>>> stands behind the counter; <<<ELEMENT_ID_BOTTLE>>> stands upright to their right. At the 2nd second, <<<ELEMENT_ID_PERSON>>> picks up <<<ELEMENT_ID_BOTTLE>>> with the right hand, fingers around its middle, and turns it so its front faces the camera. At the 5th second, <<<ELEMENT_ID_PERSON>>> (warm, relaxed): "i take it everywhere." In the final 2 seconds, the bottle is set back down in the same spot and the hand moves away. The window light gives the bottle a bright edge on its right side; its shadow falls left on the counter. Kitchen room tone, a soft tap as the bottle touches the counter. The bottle keeps its exact shape and proportions; one person, one bottle; real-time speed. No captions, subtitles, on-screen text, logos or watermarks appear.
```

### 4.4 Video edit / extension / motion transfer (only if supported)

- **Edit:** N/A for these ids — use `kling_video_edit` (see `kling-3-0-omni-edit.md`).
- **Extension:** N/A as a mode; chain the last frame into a new start-frame clip (§3.14).
- **Motion transfer (legacy `motion_control`):** no prompt; inputs are a character image and a motion video [HF S8]. Kling's guidance: head and body clearly visible and unobstructed, framing/proportions matching the motion video; the motion video a single continuous shot without cuts or camera movement, 3–30 s, one clear subject, steady moderate movements, real human action recommended [OFFICIAL S18]. Orientation "matches video" (default; movements, expressions, camera and orientation follow the reference; up to 30 s) vs "matches image" (up to 10 s) [OFFICIAL S18; HF S15]. `scene_control` chooses "whether the output video pulls the background from the motion reference video or from your character image" [HF S15]; its mapping to Kling's orientation option is unconfirmed [INFERRED]. 3.0 improves facial consistency [OFFICIAL S18]. Clean both inputs of text and watermarks and reframe them to 9:16 — no prompt can fix them later [INFERRED].

Experimental prompt-level multi-shot (see §3.5):
```text
Shot 1 (3s): <shot size, angle>, <subject action>, <camera move>.
Shot 2 (4s): <shot size>, <action or dialogue: Name (tone): "line">.
Shot 3 (3s): <shot size>, <resolving action>; hold.
<Global look and sound>, real-time speed. No captions, subtitles, on-screen text, logos or watermarks appear.
```

## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Expected cuts don't happen | shot labels without the multi-shot switch | continuous shot with time markers, or one clip per shot [OFFICIAL S1; HF S9] |
| **Unmotivated cuts** | ambiguous multi-beat prose (if server-side multi-shot engages) | "one continuous shot, no cuts" wording; one camera move per beat [INFERRED] |
| **Dead space / empty opening** | long duration with few beats; unpopulated scene description | one beat per 3–4 s; say who is visible at the start [SECONDARY S13; INFERRED] |
| **Arbitrary slow motion / speed changes** | "cinematic" moods; no pacing words | "real-time speed"; slow motion only where written [OFFICIAL S1 pattern; INFERRED] |
| **Identity drift / character swaps** | similar characters, pronouns, crowded frame | Elements per person, distinct wardrobe, anchored positions, unique labels [SECONDARY S13; OFFICIAL S4] |
| **Duplicated objects / extra characters** | vague headcount | exact counts ("one person, one bottle") [SECONDARY S13; INFERRED] |
| **Morphing** | fast orbits around products | product Element + slow moves + steady hero frame [OFFICIAL S1; INFERRED] |
| **Clothing changes** | wardrobe stated once in long prompts | Element or repeated wardrobe noun at each beat [INFERRED] |
| Line on the wrong speaker | dialogue not tied to action; 3+ speakers | action first, `Name (tone): "line"`, ≤2 speakers per beat [OFFICIAL S4; SECONDARY S13] |
| Caption/logo from the input frame persists | text in start frame or Element image | clean inputs; Kling preserves image text [OFFICIAL S1] |
| Unwanted words rendered | quoted strings; described signage | quotes only for dialogue; blank carriers [OFFICIAL S6; INFERRED] |
| English words mispronounced | capitals in English lines | lowercase English [OFFICIAL S4] |
| End frame ignored / unnatural morph | prompt contradicts end state | describe the transition toward the end frame [HF S9] |
| Turbo returns unwanted audio | no toggle | strip audio locally [INFERRED] |
| Motion Control output shorter than the clip | fast or complex motion | steady moderate motion, single continuous shot [OFFICIAL S18] |

## 6. Model-specific features and controls

- Native audio (dialogue with lip sync in five languages, dialects/accents, SFX, ambience) via `sound` [OFFICIAL S1; HF S8].
- Multi-shot (auto/custom) exists in Kling's app/API and Higgsfield's web UI — not in the MCP catalog [OFFICIAL S1; HF S8, S9].
- Element consistency via Higgsfield Elements (`kling3_0` only); voice binding not exposed [HF S8].
- Native-level text preservation [OFFICIAL S1]. Modes std / pro / 4k (project uses `std`); Turbo 720p/1080p (project uses 720p) [HF S8].
- Kling 3.0 Motion Control via legacy `motion_control` (image + motion video, `resolution` 720p/1080p, `scene_control` image|video) [HF S8]. Unlim-eligible (`kling3_0`) on explicit request [HF S8].

## 7. Model-specific pre-generation checklist

- [ ] Right id: `kling3_0` (frames, Elements, `sound`) vs `kling3_0_turbo` (start frame only, fast).
- [ ] `aspect_ratio:"9:16"`; `mode:"std"` (`kling3_0`) or `resolution:"720p"` (Turbo); frames exactly 9:16; output verified with ffprobe and conformed if needed.
- [ ] `sound` string set deliberately; Turbo audio handled in post if silence is needed.
- [ ] Prompt ≤2,500 characters; camera setup first; time markers; one action and one camera move per beat; "real-time speed".
- [ ] Multi-shot approach chosen (continuous / experimental labels / one clip per shot).
- [ ] Every person/product Element tagged at every mention; frames and Element images text-free.
- [ ] Dialogue `Name (tone): "line"`, lowercase English, ≤2 speakers per beat, action before each line.
- [ ] Integration: size, hand/grip, orientation, light direction, reflection and shadow; states restated at later beats.
- [ ] Clean-plate exclusion sentence; quoted strings only for dialogue; scene text only via start frame or exact-words recipe.
- [ ] End frame only with a start frame; `get_cost:true` preflight done.

## 8. Sources

- S1 [OFFICIAL] Kling AI — Kling VIDEO 3.0 Model User Guide (series description, 3–15 s, multi-shot switch, custom multi-shot example, dialogue format, dialects/accents, 3+ characters, element binding, text output, 15 s example) — https://kling.ai/quickstart/klingai-video-3-model-user-guide (accessed 2026-09-30)
- S2 [OFFICIAL] Kling AI — Kling VIDEO 3.0 Omni Model User Guide (`Shot N (Ns)` storyboards, @Element usage, examples) — https://kling.ai/quickstart/klingai-video-3-omni-model-user-guide (accessed 2026-09-30)
- S3 [OFFICIAL] Kling AI — KLING VIDEO O1 User Guide (T2V formula, start/end-frame rules, image limits) — https://kling.ai/quickstart/klingai-video-o1-user-guide (accessed 2026-09-30)
- S4 [OFFICIAL] Kling AI — KLING VIDEO 2.6 User Guide (audio formulas, speaker labels, action-first example, lowercase English rule, multi-voice two-character guidance) — https://kling.ai/quickstart/klingai-video-26-audio-user-guide (accessed 2026-09-30)
- S5 [OFFICIAL] Kling AI 3.0 launch press release (2026-02-06), via Bernama — https://www.bernama.com/en/news.php/?id=2520897 (accessed 2026-09-30)
- S6 [OFFICIAL] Kling AI blog — "Kling AI Prompt Guide: The Secret to Cinematic Video Prompts" (2026-08-07; formula, camera terms, text-rendering recipe, 4K mode) — https://kling.ai/blog/kling-ai-prompt-guide (accessed 2026-09-30)
- S7 [OFFICIAL] Kling AI blog — "Kling AI Negative Prompts: Fix Video Distortion & Glitches" (2026-05-26) — https://kling.ai/blog/kling-ai-negative-prompts-fix-video-distortion (page body not retrievable; search-index content, 2026-09-30)
- S8 [HF] Higgsfield catalog snapshot (`kling3_0`, `kling3_0_turbo`) and MCP tool contract (call shape, `get_cost`, Elements `<<<element_id>>>` for Kling 3.0, legacy `motion_control` params, Genjutsu routing) — `higgsfield/catalog-snapshot-2026-09-30.json`; /analyze-then-generate brief 2026-09-30
- S9 [HF] Higgsfield blog — "Kling 3.0 is on Higgsfield: User Guide" (tiers 720p/1080p/4K, multi-shot auto/custom, Elements usage, frames, audio, common mistakes) — https://higgsfield.ai/blog/Kling-3.0-is-on-Higgsfield-User-Guide-AI-Video-Generation (accessed 2026-09-30); Higgsfield help centre "How do I use Kling" — https://higgsfield.ai/creator-hub/help-center/ai-models/how-do-i-use-kling (accessed 2026-09-30)
- S10 [SECONDARY] fal.ai — Kling Video v3 Pro API reference — https://fal.ai/docs/model-api-reference/video-generation-api/kling-video-v3-pro.md; Magnific — Kling V3 API overview (2,500-character prompts, up to 6 shots, ≥3 s per shot, image specs) — https://docs.magnific.com/api-reference/video/kling-v3/overview (accessed 2026-09-30)
- S11 [SECONDARY] CometAPI — Kling omni-video API mirror (`<<<image_1>>>` syntax) — https://apidoc.cometapi.com/api/video/kling/omni-video.md (accessed 2026-09-30); Kling's own API reference (https://kling.ai/document-api/apiReference/model/textToVideo) returned "Access Denied" to automated fetches
- S12 [SECONDARY] Atlas Cloud — "Kling 3.0 Turbo and Omni: What Launched on June 17, 2026" — https://www.atlascloud.ai/blog/guides/kling-3.0-turbo-kling-omni (accessed 2026-09-30)
- S13 [SECONDARY] DataCamp — "Kling 3.0" hands-on tutorial (character mix-ups, left-right swaps, reassigned line, extra character, empty opening frames) — https://www.datacamp.com/tutorial/kling-3-0 (accessed 2026-09-30)
- S14 [HF] Higgsfield Ad Multiplier workflow v1.4, "Unlimited generations (use_unlim)" — `higgsfield/first-party/ad-multiplier-recipe.md` (retrieved 2026-09-30)
- S15 [HF] Higgsfield blog — "Why You Need Kling Motion Control 3.0 In Your Workflow" (2026-03-05; orientation, background source, 720p/1080p) — https://higgsfield.ai/blog/kling-motion-control-3 (accessed 2026-09-30)
- S16 [SECONDARY] Comfy docs — Kling Camera Controls node (API `camera_control` presets) — https://docs.comfy.org/built-in-nodes/partner-node/video/kwai_vgi/kling-camera-controls (accessed 2026-09-30)
- S17 [HF] Higgsfield — Kling 3.0 page (physics claims, up to 6 cuts, voice binding) — https://higgsfield.ai/kling-3.0 (accessed 2026-09-30)
- S18 [OFFICIAL] Kling AI — Motion Control User Guide (inputs, orientation options, 3.0 facial consistency, element binding) — https://kling.ai/quickstart/motion-control-user-guide (accessed 2026-09-30)
- S19 [SECONDARY] fal.ai blog — "Kling 3.0 Prompting Guide" (avoid pronouns, unique labels) — https://blog.fal.ai/kling-3-0-prompting-guide/ (accessed 2026-09-30)
- S20 [SECONDARY] muapi — "Kling 3.0 API Pricing — Standard, Pro, 4K & Omni Tiers" (Standard 720p, Pro 1080p, 4K 3840×2160) — https://muapi.ai/kling-3-pricing (search-index content, 2026-09-30)

## 9. Open questions / unverified behaviour

- Exact output dimensions of `kling3_0` `std` and Turbo `720p` at 9:16 (720×1280 expected) and whether `4k` is native.
- Whether prompt-level `Shot N` labels produce cuts without the multi-shot switch, and whether undocumented multi-shot keys are accepted.
- Whether `start_image` + Elements is accepted and how Elements count toward Kling's image limits.
- Whether Turbo returns an audio track on Higgsfield and whether it can be muted server-side.
- Whether `end_image` without `start_image` is accepted.
- Behaviour when the start frame's ratio differs from `aspect_ratio` (crop, pad or reject).
- Semantics of `motion_control` `scene_control` vs Kling's orientation option, its duration caps and output aspect.
- Spelling accuracy of newly generated text (no independent test found).
