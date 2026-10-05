---
guide: wan-2-6
title: Alibaba Wan 2.6
provider: Alibaba Cloud (Wan / Tongyi Wanxiang team; API via Alibaba Cloud Model Studio, DashScope)
higgsfield_model_ids: [wan2_6]
guide_version: 1.1
last_verified: 2026-09-30
catalog_snapshot: higgsfield/catalog-snapshot-2026-09-30.json
documentation_depth: medium
---

# Alibaba Wan 2.6 — model engineering guide

> Scope: Wan 2.6 (Dec 2025) upstream is a family: `wan2.6-t2v`, `wan2.6-i2v` (+flash) and `wan2.6-r2v` (+flash),
> the first Wan reference-to-video model [OFFICIAL]. Higgsfield id `wan2_6` exposes only reference roles
> (`image_references`, `video_references`, `audio_references`), no start-frame role, and names its resolution
> parameter `quality` [HF]. Which upstream endpoint each media combination reaches is not documented (§2.5, §9).
> Output format is fixed at 9:16, 720p (§2.6). The live `models_explore` catalog always wins over this file.
>
> Evidence tags: **[OFFICIAL]** provider docs, paper, model card, API reference, first-party prompt
> guide or first-party examples · **[HF]** Higgsfield catalog, MCP tool contract or first-party
> Higgsfield docs · **[SECONDARY]** reputable third-party testing or articles · **[INFERRED]**
> engineering inference that must be verified in use.

## 1. At a glance

- **Positioning.** "Wan2.6-R2V enables users to upload a character reference video with both appearance and
  voice, utilizing text prompts to generate vivid new scenes starring that same character… a person, animal or
  object, or even multiple subjects together" [OFFICIAL]. The series added "intelligent multi-shot storytelling",
  better audio-visual sync and "video outputs of up to 15 seconds" [OFFICIAL]. Higgsfield describes `wan2_6` as
  "Open-weight, stylized, experimental creative" [HF] — no Wan 2.6 open-weight release was found; Alibaba's
  Wan-Video GitHub publishes Wan2.1 and Wan2.2 base models (plus Wan-Animate-2, Wan-Dancer), nothing from 2.5 onward
  [OFFICIAL] (§9).
- **Best for:** putting one to three referenced characters/objects (appearance + voice from a reference video) into a
  new short scene; stylized looks; 5–10 s clips with auto-generated sound [OFFICIAL/HF].
- **Weaker at:** two generations behind (Artificial Analysis image-to-video with audio, 2026-09-30: #33, Elo 889, vs
  Wan 2.7 #11 and Wan 3.0 #5) [SECONDARY]; readable text [OFFICIAL]; no strict first frame; 1,500-character prompts
  [OFFICIAL]; multi-shot may be locked off (§2.5); cannot regenerate a supplied clip (§3.11).
- **Choose `wan2_6` when** you want its look, a cheap reference-driven draft, or a reference video to supply both
  appearance and voice. **Choose another model when** you need an exact first/last frame (`wan2_7`, `wan3_0`),
  multi-reference precision, Edit Mode or >10 s with references (`wan3_0`).

| operation | how to invoke on Higgsfield | notes |
|---|---|---|
| Text-to-video | `prompt` only | upstream `wan2.6-t2v`, 2–15 s [OFFICIAL/INFERRED mapping] |
| Text + audio | `prompt` + `audio_references` | upstream `audio_url` drives the video [OFFICIAL/INFERRED mapping] |
| Reference-to-video | `video_references` and/or `image_references` | upstream `wan2.6-r2v`: character1…N, ≤5 refs, 2–10 s [OFFICIAL/INFERRED mapping] |
| Image as first frame | — | no `start_image` role [HF]; an `image_references` item *might* reach `wan2.6-i2v` as first frame — unverified |
| First/last frame, edit, extension | — | N/A on Higgsfield |

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

## 3. How the model reads a prompt

### 3.1 Recommended prompt structure
Official Wan formulas that list Wan 2.6 [OFFICIAL]:
- **Reference-to-video (Wan 2.6):** `Prompt = Character + Action + Lines + Scene` — "Reference the main character
  using an identifier such as 'character1'… Each character can be referenced multiple times in the prompt to control
  their behavior."
- **Sound (Wan 3.0/2.7/2.6/2.5):** Entity + Scene + Motion + Sound description.
- **Multi-shot (Wan 3.0/2.7/2.6):** Overall description + Shot number + Timestamp + Shot content (subject to the
  `shot_type` caveat).
- **Text-to-video:** Entity + Scene + Motion + Aesthetic control + Stylization.

Official 2.6 t2v examples are single dense paragraphs that open with camera/light tags, then subject, action and
the spoken line with voice description [OFFICIAL]. Keep 120–220 words to stay under 1,500 characters [INFERRED].
English or Chinese [OFFICIAL]. Worked patterns: §4.0.

### 3.2 Subject and identity
In r2v the tag *is* the identity: "The model identifies characters in the references only through these
identifiers" [OFFICIAL]. Write `character1` (as in the official examples), plus a two- to five-word visual reminder
the first time ("character1, the man in the grey coat,") [INFERRED]. In text-to-video, describe appearance with
adjectives and short phrases [OFFICIAL].

### 3.3 Action, motion and physical interaction
Amplitude, speed and effect ("swaying violently", "moving slowly") [OFFICIAL]. One clear action chain per character;
"very long or complex action sequences" fail [OFFICIAL]. Objects can be their own reference character ("character2
is an alarm clock") [OFFICIAL]; contact and grip phrasing: §3.14.

### 3.4 Environment, lighting and style
Scene = background + foreground [OFFICIAL]. Official dictionary for light (daylight, firelight, overcast;
soft/hard/side/rim), shot size, composition, lens and tone; styles (claymation, felt, pixel, puppet, 3D cartoon)
[OFFICIAL]. Official 2.6 examples name light sources in parentheses ("mixed lighting (the practical light from the
desk lamp blends with the overcast light from the window)") [OFFICIAL].

### 3.5 Chronology, timing and multi-shot structure
Order events as they happen and link beats with connectors ("then", "immediately") [OFFICIAL multi-speaker
guidance]. Because `shot_type` is not exposed, write one continuous shot with a clear beginning, middle and end
state [INFERRED]; if a test proves multi-shot works, use "Shot 1 [0–3 s] …" [OFFICIAL formula].

### 3.6 Camera language and dedicated camera / motion controls
No camera parameters [HF]. Phrases: "camera pushes in", "camera moves left", "fixed camera", "camera pulls out",
orbit under 45° [OFFICIAL]. One camera move per shot is safest for this generation [INFERRED].

### 3.7 References (image / video / audio)
- Tags `character1`, `character2`, … in reference order; "Reference up to three characters at the same time"
  (prompt guide) vs ≤5 references in the API [OFFICIAL, inconsistent] → ≤3 characters.
- One subject per reference file: "character1 is a girl, and character2 is an alarm clock" [OFFICIAL].
- Reference videos carry voice (their audio is used if present) [OFFICIAL]; use clean-speech clips without music
  [INFERRED].
- `audio_references` (upstream `audio_url`) "generates the video using this audio" [OFFICIAL]; say who speaks or
  moves to it.
- In Analyze Mode, reference clips must not carry captions, usernames or watermarks into the output (§3.11).

### 3.8 Start and end frames
N/A on Higgsfield — no `start_image`/`end_image` roles [HF]. Use `wan2_7` or `wan3_0` for strict frames.

### 3.9 Audio, dialogue and sound
Voice = lines + emotion + tone + speed + timbre + accent [OFFICIAL]; official 2.6 wording: "its mouth clearly moving
as it speaks in a smooth, cynical voice: '…'" [OFFICIAL]. Monologue and multi-character dialogue are supported in r2v
[OFFICIAL]; multi-speaker rules: unique labels, action before speech, distinct voices, linking words [OFFICIAL].
Exact-word lip sync is unreliable [OFFICIAL]. Without an audio input the model adds BGM/SFX [OFFICIAL]; describe the
soundscape and say "no background music" if needed [INFERRED].

### 3.10 Negative constraints
No `negative_prompt` field on Higgsfield [HF] (upstream ≤500 characters [OFFICIAL]). One short exclusion sentence
inside the first 1,500 characters; prefer positive wording — the upstream rewriter may reword negatives [INFERRED].

### 3.11 Visible text
**(a) Reliability.** "Text renders approximately — specific words will not be precise" [OFFICIAL]; nothing suggests
Wan 2.6 does better. Treat in-frame text as unreliable.

**(b) Clean plate — default in Analyze Mode.** Generate without text; add hooks and captions in post
(`atp.py captions`, libass). Use Alibaba's phrasing "Do not add text." (Wan 2.7 example) or "Do not show any text, subtitles,
numbers, interface elements, or watermarks on screen." (Wan 3.0 example) [OFFICIAL for those versions / INFERRED
transfer], plus positive text-free surfaces. Never describe signage or screens with words or quote non-dialogue
strings [INFERRED].

**(c) Intentional in-frame text.** Not recommended on this model; put exact text in post [INFERRED].

**(d) Edit operations — removing source text.** N/A on Higgsfield: `wan2_6` video references define characters
(appearance + voice), not a clip to regenerate [OFFICIAL/HF], so it cannot produce a clean version of a supplied clip.
Use `wan3_0` (or local `atp.py clean --delogo` for small static overlays). Captions, usernames and platform marks inside
reference clips can leak into outputs [INFERRED] — clean or crop references before upload.

**(e) Watermark risk.** Upstream default is no watermark ("AI-generated", bottom-right, when enabled) and the switch is
not exposed [OFFICIAL/HF]. `atp.py qc` OCR flags invented or leaked marks — regenerate with cleaner references.

### 3.12 Character / identity consistency
Upstream r2v preserves "the distinctive look and sound of the original reference" [OFFICIAL]. One person per
reference, clear face, neutral background, even light; a short clip (one person, frontal and three-quarter views,
clean voice) gives identity and timbre [OFFICIAL constraints + INFERRED]. Higgsfield advertises "strong identity
retention" without "morphing" [HF]. Tie every mention to the same tag; no pronouns when two people are present
[OFFICIAL principle].

### 3.13 Product and object fidelity
Treat the product as its own reference character (clean single-object image) [OFFICIAL]. Lock geometry:
"character2 keeps its exact shape, proportions, color and parts; it does not bend, change size or duplicate"
[INFERRED]. Slow, simple handling. For strict product fidelity prefer `wan3_0` or a start frame on `wan2_7`
[INFERRED].

### 3.14 Integration and continuity
**Across clips.** Reuse the same references, in the same order, with identical tag descriptions [INFERRED].
Without frame roles, shot-to-shot matching relies on identical environment and lighting wording; expect more drift
than frame-chained models [INFERRED].

**Inserted assets.** An inserted object is a reference character: "character1 picks up character2 with her right
hand, fingers around its handle, holding it at chest height, its front face toward the camera" — state size relative
to the hand, orientation, grip, occlusion and where it ends up [INFERRED structure on the OFFICIAL tag syntax].

**Scene light on the asset.** Name the sources and direction once, the way official 2.6 examples do ("mixed lighting
(the practical light from the desk lamp blends with the overcast light from the window), side lighting")
[OFFICIAL], then add "character2 catches the same warm side light and casts a soft shadow on the counter"
[INFERRED].

**Persistent states.** End each beat with a state: "character2 stays on the table, lid closed", "the glass remains
half full" [INFERRED]; with references, restate the object tag rather than "it" when two objects exist [OFFICIAL
naming principle].

**Known failures.** Older generation fidelity [SECONDARY]; long/complex action, rapid scene changes within a clip,
exact-word lip sync, text [OFFICIAL]; multi-reference swaps when tags are unclear [OFFICIAL single-subject rule].
Slop prevention: §5.

## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach
Verbatim first-party examples (trimmed with […]):

1. Reference-to-video (Wan 2.6 formula) — prompt guide, https://www.alibabacloud.com/help/en/model-studio/text-to-video-prompt
   > "This is a whimsical fairytale scene. character1 jumps and plays on the grass. character2 plays piano under a
   > nearby apple tree. An apple falls on character2's head. character1 points at character2 and says happily,
   > "You're going to become a scientist!"."
2. Two-character dialogue — reference-to-video (2.6) API, https://www.alibabacloud.com/help/en/model-studio/legacy-wan-reference-to-video-api-reference
   > "character1 says to character2: “I'll rely on you tomorrow morning!” character2 replies: “You can count on me!”"
3. Single character — same page
   > "character1 sips milk tea while dancing freestyle to the music."
4. Characters, props and scene as references — same page
   > "Character2 sits in a chair by the window, holding character3, playing a soothing American country folk song
   > next to character4. Character1 says to Character2: “that sounds great”"
5. Text-to-video with dialogue — text-to-video API reference (wan2.6), https://www.alibabacloud.com/help/en/model-studio/text-to-video-api-reference
   > "Shot from a low angle, in a medium close-up, with warm tones, mixed lighting (the practical light from the
   > desk lamp blends with the overcast light from the window), side lighting, and a central composition. […] A fox,
   > wearing a dark brown trench coat and a light gray fedora, sits in a leather chair, […] its mouth clearly moving
   > as it speaks in a smooth, cynical voice: "The case was cold, colder than a fish in winter. […]""
6. Timed shot line — prompt guide
   > "Shot 2 [4–6 s] Hard cut transition, fixed camera position, focusing on the boy's eyes, which are glistening
   > with tears, showing loss and helplessness."

Patterns they teach:
- **Tags as sentence subjects:** `characterN` starts each action sentence; props and even scenes can be characters
  (1, 4).
- **Order (r2v):** scene sentence → one action per character → consequence → dialogue (1).
- **Dialogue:** "character1 says to character2: "…" character2 replies: "…"" — speaker, addressee, colon, quote (2).
- **Order (t2v):** camera/light/composition tags first, light sources in parentheses, then subject, action, mouth
  movement and the spoken line with a voice description (5).
- **Timed shots:** "Shot N [a–b s]" + transition + camera state + content (6).
- **Brevity:** reference prompts are one to four short sentences (1–4); t2v prompts stay under the 1,500-character
  cap (5). No official 2.6 example contains an exclusion list.

### 4.1 Text-to-video
Follows patterns: tags first, light sources in parentheses, mouth + voice description, one closing sentence.
```text
<shot size>, <angle>, <tone>, <lighting with sources in parentheses>, <composition>. <Subject with 3–6 descriptors> <action at real-time speed> in <scene>, <end state>.
The camera <single move | stays fixed>. <Sound: voice line + delivery | SFX | BGM | no background music>.
Do not add text.
```
Worked example (10 s, 9:16, 720p): "Eye-level medium shot, warm tones, soft light (morning sun through a side window),
center composition. A small brown dog in a red knitted sweater trots along a wet cobblestone lane at real-time
speed, stops at a puddle, sniffs its reflection, then shakes water from its paws and sits. The camera tracks slowly
beside it. Sound: light rain, paw splashes, a distant bicycle bell, gentle acoustic guitar. Do not add text."

### 4.2 Start frame (and end frame) to video
N/A on Higgsfield — no frame roles for `wan2_6` [HF]. Use `wan2_7` or `wan3_0`.

### 4.3 Reference-to-video
Follows patterns: scene sentence, one action per tagged character, dialogue with addressee, short.
```text
<Scene/style sentence>. character1, <short visual reminder>, <action with grip/contact>. character2, <short visual reminder>, <state or action>.
character1 says to character2: "<line>". Immediately, character2 replies: "<line>".  (or: No dialogue.)
<Camera: one move or fixed>. <Sound>. Keep each character's appearance exactly as in its reference. Do not add text.
```
Worked example (10 s, 9:16; reference 1 = short video of an approved person, reference 2 = image of a plain ceramic
mug): "A calm kitchen at golden hour, natural realism. character1, the woman in the green cardigan, walks to the
counter and picks up character2, the white ceramic mug, with her right hand around the handle, then takes one slow
sip and sets it back on the counter, where it stays. character2 keeps its exact rounded shape and size. character1
says softly: 'Finally, a quiet morning.' The camera pushes in slowly to a medium close-up. Sound: birdsong outside,
the soft clink of the mug, no music. Keep each character's appearance exactly as in its reference. Do not add text."

### 4.4 Video edit / extension / motion transfer
N/A on Higgsfield — `wan2_6` video references define characters (appearance + voice), not a clip to edit, extend or
clean [OFFICIAL/HF]. Use `wan3_0`.

## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Multi-shot request returns one shot | upstream `shot_type` default `single` [OFFICIAL] | single continuous shots; test before relying on cuts |
| Prompt tail ignored | >1,500 characters truncated [OFFICIAL] | ≤220 words; exclusions early |
| Wrong person gets a line/action | pronouns, unclear tags, mixed reference order | tags only, one subject per reference, visual reminder |
| Reference bleed | group photos, cluttered references [OFFICIAL single-subject rule] | crop to one subject per file |
| 15 s fails/clamps with references | r2v 2–10 s [OFFICIAL] | 5 or 10 s |
| Unwanted soundtrack | audio on by default [OFFICIAL] | describe sound; strip locally |
| Text/gibberish, leaked overlays | text in prompt or references | §3.11 |
| Unclear first-frame behaviour | `image_references` routing unknown [HF silent] | test; strict frames on `wan2_7`/`wan3_0` |
| Lower overall fidelity | older generation [SECONDARY] | draft here, finish on a newer model |

**AI-slop tendencies and prevention.** `atp.py qc` flags black and frozen spans; `atp.py trim` removes dead head/tail frames deterministically.

| slop tendency | prevention |
|---|---|
| Dead space | 5 s unless the beats need 10 s; a visible change every 2–3 s [INFERRED] |
| Arbitrary slow motion / speed jumps | "at real-time speed", "steady pace" [INFERRED] |
| Unmotivated cuts | one continuous shot; upstream default `single` helps [OFFICIAL] |
| Morphing | "character2 keeps its exact shape"; no transformations [INFERRED] |
| Identity drift / swaps | one subject per reference; tags, never pronouns [OFFICIAL] |
| Duplicated objects | "only one character2 in the scene" [INFERRED] |
| Clothing changes | "clothing exactly as in the reference" [INFERRED] |

## 6. Model-specific features and controls
- Reference-to-video with `character1…` tags; reference videos supply appearance **and voice** [OFFICIAL].
- Audio-conditioned t2v via `audio_references` (upstream `audio_url`, 3–30 s) [OFFICIAL/INFERRED mapping].
- Upstream-only (not exposed): `shot_type`, `prompt_extend`, `negative_prompt`, `seed`, flash variants with a silent
  switch, 4:3/3:4 sizes [OFFICIAL/HF].

## 7. Model-specific pre-generation checklist
- [ ] `aspect_ratio:"9:16"`, `quality:"720p"` (not `resolution`); 9:16 reference images; `atp.py conform` (§2.6).
- [ ] Duration 5 or 10 s when references are attached.
- [ ] Prompt ≤1,500 characters, one continuous shot, events in order.
- [ ] Each reference = one subject, free of captions/usernames/watermarks; tags `character1…` in `medias` order; ≤3.
- [ ] Voice from a reference video wanted? Clean-speech clip; otherwise describe the voice.
- [ ] Clean-plate sentence; captions/hooks planned for post (`atp.py captions`); no Edit Mode on this model.
- [ ] Grip, light and end states written (§3.14); slop guards (§5).
- [ ] `get_cost: true`; QC with `atp.py qc --mode analyze` (size, freezes, pseudo-text, corner marks, identity).

## 8. Sources
- [OFFICIAL] Text-to-video API reference, section "HTTP (wan2.6 and earlier)" (size tables) — https://www.alibabacloud.com/help/en/model-studio/text-to-video-api-reference (accessed 2026-09-30)
- [OFFICIAL] Wan image-to-video first frame API reference (2.1–2.6) — https://www.alibabacloud.com/help/en/model-studio/legacy-image-to-video-api-reference (accessed 2026-09-30)
- [OFFICIAL] Wan – reference-to-video (2.6) API reference — https://www.alibabacloud.com/help/en/model-studio/legacy-wan-reference-to-video-api-reference (accessed 2026-09-30)
- [OFFICIAL] Video generation prompt guide (Wan 2.6 R2V formula, sound and multi-shot formulas) — https://www.alibabacloud.com/help/en/model-studio/text-to-video-prompt (accessed 2026-09-30)
- [OFFICIAL] Wan – reference-to-video API reference (wan2.7; "Do not add text." example) — https://www.alibabacloud.com/help/en/model-studio/wan-video-to-video-api-reference (accessed 2026-09-30)
- [OFFICIAL] wan3.0 Video Generation Prompt Guide (clean-plate phrasing) — https://www.alibabacloud.com/help/en/model-studio/wan3-video-generation-prompt-guide (accessed 2026-09-30)
- [OFFICIAL] Video generation and editing (model list, 2.6 specs) — https://www.alibabacloud.com/help/en/model-studio/use-video-generation (accessed 2026-09-30)
- [OFFICIAL] Alibaba Unveils Wan2.6 Series Enabling Everyone to Star in Videos (2025-12-16) — https://www.alibabacloud.com/blog/alibaba-unveils-wan2-6-series-enabling-everyone-to-star-in-videos_602742 (accessed 2026-09-30)
- [OFFICIAL] Wan-Video GitHub organization (open weights: Wan2.1, Wan2.2) — https://github.com/Wan-Video (accessed 2026-09-30)
- [HF] Higgsfield catalog snapshot — higgsfield/catalog-snapshot-2026-09-30.json; MCP tool contract facts supplied with this task
- [HF] Higgsfield Wan 2.6 page — https://higgsfield.ai/wan-2.6 (accessed 2026-09-30)
- [HF] WAN 2.6 by Alibaba User Guide on Higgsfield — https://higgsfield.ai/blog/WAN-2.6-by-Alibaba-User-Guide-on-Higgsfield (accessed 2026-09-30)
- [SECONDARY] Artificial Analysis image-to-video leaderboard — https://artificialanalysis.ai/video/leaderboard/image-to-video (accessed 2026-09-30)

## 9. Open questions / unverified behaviour
- Routing of each media combination to `wan2.6-t2v`, `-i2v`, `-r2v` or flash variants; whether `image_references`
  becomes a first frame (and then dictates aspect ratio).
- Whether Higgsfield sets `shot_type:"multi"` or leaves `single`; ordering of mixed image/video references into
  `character1…N`.
- Behaviour of 15 s requests with references, and of `audio_references` combined with references.
- The Higgsfield "open-weight" tag (no official Wan 2.6 weights found); whether `prompt_extend` stays on and
  `watermark` off.
