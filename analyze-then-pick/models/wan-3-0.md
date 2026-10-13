---
guide: wan-3-0
title: Alibaba Wan 3.0 / Wan 3.0 Prime
provider: Alibaba Cloud (Wan / Tongyi Wanxiang team; API via Alibaba Cloud Model Studio, DashScope)
higgsfield_model_ids: [wan3_0, wan3_0_prime]
guide_version: 1.3
last_verified: 2026-10-13
catalog_snapshot: higgsfield/catalog-snapshot-2026-09-30.json
documentation_depth: high
---

# Alibaba Wan 3.0 / Wan 3.0 Prime — model engineering guide

> Scope: Wan 3.0 is Alibaba's "All-in-One" video model: one model id covers text-to-video, first-frame and
> first+last-frame image-to-video, multimodal reference-to-video (image/video/audio), and — upstream — video
> editing and extension, routed automatically from the attached media and the prompt's intent. This file
> covers Higgsfield ids `wan3_0` (standard) and `wan3_0_prime` (speed-optimized). Output format is fixed at 9:16,
> 720p (§2.6). The live `models_explore` catalog always wins over the parameter tables in this file.
>
> Evidence tags: **[OFFICIAL]** provider docs, paper, model card, API reference, first-party prompt
> guide or first-party examples · **[HF]** Higgsfield catalog, MCP tool contract or first-party
> Higgsfield docs · **[SECONDARY]** reputable third-party testing or articles · **[INFERRED]**
> engineering inference that must be verified in use.

## 1. At a glance

- **Positioning.** "An All-in-One reference-based video generation model that supports Text-to-Video,
  Image-to-Video (first frame/first-last frame), and Reference-based Video Generation. It can generate videos up
  to 30 seconds long at 30fps." [OFFICIAL] Up to 20 reference materials per request upstream, native
  dialogue/BGM/SFX, editing and extension [OFFICIAL]. `wan3.0-video-prime` is the "high-speed version with
  capabilities aligned to the standard version" [OFFICIAL]. GA announced Aug 24, 2026; the API page still says
  "preview" [OFFICIAL].
- **Best for:** 10–30 s single-pass stories; timed multi-shot sequences; locking several people/props/scenes from
  references; voice timbre from audio; motion/camera transfer; regenerating a supplied clip (edit, ≤15 s source);
  "lifelike, diverse human faces" [OFFICIAL]. Artificial Analysis (2026-09-30): #1 text-to-video (Elo 1157), #5
  image-to-video with audio (Elo 1164) [SECONDARY].
- **Weaker at:** on-screen text and audio texture ("improving but not yet where we want them") [OFFICIAL]; exact
  lip sync; long choreography; orbits >45° [OFFICIAL]. Frame modes cannot take references or audio [OFFICIAL].
- **Choose Wan 3.0 when** you need >15 s, multi-reference casting, reference audio, a silent switch, motion
  transfer or a clean re-render of a supplied clip. **Choose another model when** exact in-frame text is required
  (add it in post), or a strict first frame *and* reference images are needed in one call (impossible here).

| operation | how to invoke on Higgsfield | notes |
|---|---|---|
| Text-to-video | `prompt` only | 2–30 s or smart duration; multi-shot by prompt [OFFICIAL] |
| First frame → video | one `start_image` | "pixel-level reproduction" of the frame [OFFICIAL] |
| First + last frame → video | `start_image` + `end_image` | `end_image` alone is not a documented combination [OFFICIAL] |
| Reference-to-video | `image_references` (≤10), `video_references` (≤5, ≤15 s total), `audio_references` (≤5, ≤15 s total) | cite as Image N / Video N / Audio N [OFFICIAL] |
| Audio-driven (lip/beat) | `image_references` + `audio_references` | not with `start_image` [OFFICIAL] |
| Motion / camera / VFX transfer | `video_references` (+ `image_references`) | upstream-documented; Higgsfield routing [INFERRED] |
| Video edit / extension (Edit Mode) | one `video_references` + edit/extend-intent prompt | upstream-documented; not advertised in the Higgsfield catalog description → verify [INFERRED] |
| Document / web-page input | — | N/A on Higgsfield (no `file`/`link` role) [HF] |

## 2. Higgsfield parameter surface

### 2.1 Parameters per model id
Both ids expose an identical surface [HF].

| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `wan3_0`, `wan3_0_prime` | `duration` | number, min -1, max 30 | 5 | "Duration in seconds (2-30), or -1 to let the model choose the length from the prompt and media. Smart duration is billed as 10 seconds." [HF] |
| both | `resolution` | `480p`, `720p`, `1080p` | `720p` | always `720p` under the fixed format (§2.6); upstream default 1080P [OFFICIAL] |
| both | `generate_audio` | bool | `true` | "Generate a native audio track" [HF]; maps to upstream `audio` [INFERRED]; toggling "does not affect pricing" upstream [OFFICIAL] |
| both | `enable_thinking` | bool | `false` | "Let the model reason about the prompt before generating (slower, better prompt adherence)" [HF] |
| both | `aspect_ratio` | `auto`, `16:9`, `9:16`, `1:1`, `4:3`, `3:4` | — | always `9:16` (§2.6); `auto` ≈ upstream `adaptive` [INFERRED] |
| both | negative_prompt, seed, prompt_extend, watermark | — | — | not exposed on Higgsfield [HF]; see §2.5, §3.10, §3.11 |

### 2.2 Media roles
| role | what it controls | limits / count | notes |
|---|---|---|---|
| `start_image` | exact first frame (upstream `first_frame`) | 1 | exclusive with all `*_references` [OFFICIAL] |
| `end_image` | exact last frame (upstream `last_frame`) | 1, only with `start_image` | [OFFICIAL] |
| `image_references` | people, props, scenes, style, storyboard/keyframes | ≤10; JPEG/PNG/BMP/WEBP, 240–8000 px, ≤20 MB, aspect ≤8:1 [OFFICIAL] | "Image N" = N-th image reference [OFFICIAL] |
| `video_references` | motion, camera, VFX, identity+voice, or the source clip for edit/extension | ≤5 clips, 1–15 s each, ≤15 s total, ≥16 fps, ≤100 MB, mp4/mov [OFFICIAL] | "Video N"; input + output ≤30 s [OFFICIAL] |
| `audio_references` | voice timbre, music, beat, dialogue source | ≤5 clips, 1–15 s each, ≤15 s total, wav/mp3, ≤15 MB [OFFICIAL] | "Audio N" |

`medias[].value` is always a Higgsfield media UUID or a completed job ID, never a URL [HF].

### 2.3 Duration, resolution, aspect ratio, audio
- **Duration:** integers 2–30, or `-1` smart duration ("the model automatically recommends a suitable duration
  based on the input prompt, content, and rich media" [OFFICIAL]; billed as 10 s on Higgsfield [HF]). Values 0/1
  are outside the upstream range; the server snaps/clamps unsupported values [HF contract].
- **Frame rate** 30 fps [OFFICIAL]. **Resolution/aspect:** fixed 720p, 9:16 — see §2.6. Upstream price scales with
  resolution per second [OFFICIAL]; use `get_cost: true` for Higgsfield credits.
- **Audio:** on by default; dialogue, SFX and BGM are generated jointly [OFFICIAL]. `generate_audio:false` yields no
  audio track [OFFICIAL/HF].

### 2.4 Call recipes
Text-to-video:
```json
{"model":"wan3_0","prompt":"<PROMPT>","duration":10,"aspect_ratio":"9:16","resolution":"720p","generate_audio":true,"enable_thinking":false}
```
First frame → video (start image already 9:16):
```json
{"model":"wan3_0","prompt":"<MOTION_PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID>","role":"start_image"}],"duration":8,"aspect_ratio":"9:16","resolution":"720p","generate_audio":true}
```
First + last frame → video (both frames 9:16, identical size):
```json
{"model":"wan3_0","prompt":"<PATH_PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID_FIRST>","role":"start_image"},{"value":"<IMAGE_MEDIA_ID_LAST>","role":"end_image"}],"duration":6,"aspect_ratio":"9:16","resolution":"720p","generate_audio":true}
```
Reference-to-video (order inside each role = its number):
```json
{"model":"wan3_0","prompt":"<PROMPT citing Image 1, Image 2, Video 1, Audio 1>","medias":[{"value":"<IMAGE_MEDIA_ID_1>","role":"image_references"},{"value":"<IMAGE_MEDIA_ID_2>","role":"image_references"},{"value":"<VIDEO_MEDIA_ID>","role":"video_references"},{"value":"<AUDIO_MEDIA_ID>","role":"audio_references"}],"duration":12,"aspect_ratio":"9:16","resolution":"720p","generate_audio":true,"enable_thinking":true}
```
Edit Mode — regenerate a supplied clip (source 9:16, ≤15 s; verify routing first) — a `<JOB_ID>` also works as value [HF]:
```json
{"model":"wan3_0","prompt":"Edit the video: <ONE CHANGE>; the rest of the frame stays unchanged.","medias":[{"value":"<VIDEO_MEDIA_ID or JOB_ID>","role":"video_references"}],"duration":-1,"aspect_ratio":"9:16","resolution":"720p","generate_audio":true}
```
Speed variant: replace `"wan3_0"` with `"wan3_0_prime"` [HF]. Preflight any call with `get_cost: true` [HF].

### 2.5 Parameter gotchas
1. **Mode exclusivity.** `start_image`/`end_image` cannot be combined with any `*_references` ("The two modes are
   mutually exclusive") [OFFICIAL]. For a strict first frame *and* a character, pre-compose a start frame that
   already contains the approved character, or use references and describe the opening [INFERRED].
2. **No audio in frame modes:** "Wan3.0's first frame/first-last frame mode does not [accept driving audio]… use
   the all-modal reference mode (reference_image + reference_audio)" [OFFICIAL].
3. **Smart duration is billed as 10 s** [HF], presumably whatever length the model picks [INFERRED].
4. **Video input counts:** input + output ≤30 s; upstream bills input + output seconds [OFFICIAL]; Higgsfield basis
   undocumented → `get_cost`.
5. **Hidden upstream defaults.** `prompt_extend` (LLM rewriting) defaults to `true` upstream and is not exposed
   [OFFICIAL/HF] — write complete prompts so the rewriter has nothing important to invent [INFERRED].
6. **`enable_thinking`** is absent from Alibaba's API reference (checked 2026-09-30) [OFFICIAL silence]; third-party
   schemas call it "deep thinking mode… required to process file/link inputs and to parse complex image content"
   [SECONDARY]. Slower; credit impact unknown.
7. **Numbering follows `medias` order within each role** [INFERRED from the upstream rule "the 1st reference_image
   in the array corresponds to Image 1" [OFFICIAL]].
8. **Never send `auto`** under the fixed format: text-only lets the model choose; references may pull it landscape
   [INFERRED from OFFICIAL "adaptive" behaviour].
9. **No pre-built start frame in Recreate.** The source video rides as `video_references`, and frame
   roles exclude every `*_references` (gotcha 1), so a product cannot be pinned at its reckoned pixel
   height by a start frame while the source carries the action. A frames-only build (the source's own
   first frame with the product composited at the reckoned height as `start_image`; ✗ in the command's
   fidelity ladder) pins the size and gives up the video reference's motion and timing; untested (§9).
10. **A size-and-place guide rides as one more `image_references` entry** beside the source
   `video_references` (reference modes combine; only the frame roles are exclusive, gotcha 1). It pins spot,
   size and look without giving up the source's motion and timing (§3.14, `reference/generation-system.md`
   §4b.6) [VERIFIED, 8 takes, 2026-10-12..13].

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-pick)
| mode | params | expected output | action |
|---|---|---|---|
| T2V, references | `"aspect_ratio":"9:16","resolution":"720p"` (same for `wan3_0_prime`) | 720×1280 at 30 fps expected: Wan 3.0 publishes no pixel table, Wan 2.7/2.6 720P 9:16 is 720×1280 [OFFICIAL] → [INFERRED] | verify |
| First / first+last frame | same params + 9:16 frames of identical size | frame mode "auto-matches first frame aspect ratio" [OFFICIAL] | verify |
| Edit / extension | same params; the source must already be 9:16 | adaptive keeps the source ratio [OFFICIAL]; 9:16 on a non-9:16 source is untested | reframe the source to 9:16 before upload |

Always finish with `atp.py conform --video "<in>" --out "<out>"` (scale-to-cover + focus crop to exactly 720×1280,
never stretched; a no-op copy when already exact). Expected loss here is ~0%; `conform` refuses losses above 12% —
treat that as a wrong-ratio generation and regenerate from 9:16 inputs rather than forcing the crop [INFERRED].
Never use 480p for deliverables (it would need upscaling).

## 3. How the model reads a prompt

### 3.1 Recommended prompt structure
Official full-modality formula [OFFICIAL]:

`Prompt = [Overall description] + [Reference citation: Image N / Video N / Audio N] + [Shot N (start–end s): Subject + Scene + Motion + Aesthetic control] + [Dialogue: xx says: "…"] + [Sound effect / BGM] + [Style / Mood] + [Negative prompt list]`

"Write down whatever you want to control, and simply skip any section you do not need." [OFFICIAL] Weak prompts
"cover entity and motion but skip aesthetic control and stylization — producing a static camera in an undefined
void" [OFFICIAL]. Alibaba's prompt-organizing skill (wan3-pe) uses five sections — [Core Task], [Plot Summary],
[Audio Style], [Camera & Core Constraints], [Negative Prompts] — and keeps ratio, duration and resolution out of the
prompt ("set via the page or API") [OFFICIAL]. Length: "A single sentence is enough… but the more complete and
precise the description, the closer the result" [OFFICIAL]; limit 20,000 characters [OFFICIAL]; practical 60–150
words per 5–8 s shot, 200–500 words for 15–30 s [INFERRED]. Chinese or English prompts; dialogue in other
languages appears in first-party examples [OFFICIAL]. Worked patterns: §4.0.

### 3.2 Subject and identity
Describe the subject with adjectives and short phrases (age, hair, clothing, distinguishing features) [OFFICIAL].
When a subject comes from a reference, bind it once and describe only what the reference cannot show (action,
emotion, position). "When the user only says 'character' or 'subject', keep that neutral term" [OFFICIAL wan3-pe].

### 3.3 Action, motion and physical interaction
State amplitude, speed and effect ("swaying violently", "moving slowly") [OFFICIAL]. A "30-second choreographed
sequence" and "high-frequency actions the model cannot control" are on the what-not-to-prompt lists [OFFICIAL].
First-party examples spell out visible physics ("hems swaying with motion… wall plaster flaking") [OFFICIAL].
Contact, grip and state phrasing: §3.14.

### 3.4 Environment, lighting and style
Scene = background + foreground [OFFICIAL]. Official lighting terms: daylight, firelight, overcast, clear-sky
light; soft, hard, side, rim, backlight; contrast, warm/cool tones, saturation [OFFICIAL]. Style block = art style +
color tone + mood, at the start or end [OFFICIAL]. Light matching for inserted assets: §3.14.

### 3.5 Chronology, timing and multi-shot structure
- `Overall description + Shot number + Timestamp + Shot content` [OFFICIAL]; shots "connect end-to-end with no gaps
  or overlaps, 2–5 seconds per segment" (prompt guide) vs "4~6 seconds per shot" (user guide) [OFFICIAL,
  inconsistent] → use contiguous 3–5 s shots.
- `Shot 1 [0-3s]`, `Shot 1 (00:00-00:03):` and `[00:00-00:03]` are interchangeable; pick one [OFFICIAL].
- Transitions: "hard cut" or "dissolve" at the end of a segment, or "seamlessly continue from the last frame of the
  previous segment" [OFFICIAL].
- Single take: "Generate single shot." / "One continuous shot" on the first line [OFFICIAL]; without it a four-word
  prompt came back as five shots in five seconds in one test [SECONDARY].
- Timestamps structure shots; they don't steer free physical motion. Never schedule when a moving object must face
  the camera or reach a mark. Wan fakes it with single-frame snaps or a pause-and-resume: seen on a spinning can,
  2026-10-01 (`generation-system.md` §5b) [INFERRED].

### 3.6 Camera language and dedicated camera / motion controls
Camera is prompt-only on Higgsfield [HF]. Official vocabulary: push in, pull out, orbit, handheld follow, "Fixed
shot, camera static, position unchanged"; "85mm telephoto, shallow depth of field / 24mm wide-angle, deep focus";
"High-speed photography (1000fps slow motion)" [OFFICIAL]. Intent: push-in = intimacy/tension, pull-out =
scale/isolation, tracking = alongside, orbit = importance, fixed = stillness; keep orbits under 45° [OFFICIAL].
Line-guided paths drawn in red on a reference image are official; their prompt opens "The final footage completely
removes all red lines, numeric markers, arrows, and auxiliary marks; no text or watermarks appear in the frame."
[OFFICIAL]

### 3.7 References (image / video / audio)
- **Syntax:** "Image 1", "Video 1", "Audio 1" — capital letter, space before the number; numbered per modality by
  upload order; one reference may be called "reference image" [OFFICIAL].
- **Bind by purpose, one subject per binding:** "Character A corresponds to Image 1, adopting facial features,
  hairstyle, and clothing. Prop A corresponds to Image 3, adopting structure, material, and color. Scene A
  references Image 4, adopting spatial layout, architecture, and lighting; the person in the image is ignored."
  [OFFICIAL wan3-pe]; "Clearly separate the purpose of each material… to prevent features from bleeding across
  subjects" [OFFICIAL].
- **Several images of one subject:** state what each adds "and declare that they jointly define the same entity and
  generate only one instance" [OFFICIAL].
- **Partial borrowing** (take X, leave Y) and **storyboards** ("Use the storyboard only as shot guidance; do not
  generate video from the storyboard as a single image") [OFFICIAL] — examples in §4.0.
- **Audio:** "Voice timbre references Audio 1" (applies to all of that character's lines) or beat-driving
  ("following the beat of the fixed audio") [OFFICIAL].
- In Analyze Mode never inherit a reference's wording, usernames or watermarks (§3.11).

### 3.8 Start and end frames
Frame mode reproduces the image at t=0 (and at the end) [OFFICIAL]. "The image already establishes the subject,
scene, and style, so the prompt should focus on describing the motion, plot, dialogue, and camera movement"
[OFFICIAL]. For first+last frames describe the path; keep lighting, framing and subject count compatible
[INFERRED]. Both frames 9:16, identical size (§2.6).

### 3.9 Audio, dialogue and sound
- Dialogue: "character + speaking verb + colon + quoted content"; multi-person: `Image 1 says: "…"; Image 2 replies:
  "…"` [OFFICIAL]. Voice formula: lines + emotion + tone + speed + timbre + accent; append "Lip sync" when needed
  [OFFICIAL]; exact-word lip sync is listed as unreliable in the general Wan guide [OFFICIAL].
- "No dialogue." — "otherwise the model decides on its own whether to include dialogue"; "No background music." or
  "No BGM, generate only ambient and action sounds" [OFFICIAL]. SFX auto-match described actions and may carry
  timestamps [OFFICIAL].
- Multi-character: unique labels, action before speech, distinct voice labels, linking words ("Immediately,")
  [OFFICIAL].

### 3.10 Negative constraints
No `negative_prompt` field on Higgsfield [HF] (upstream: ≤500 chars [OFFICIAL]). Wan 3.0's formula ends with an
in-prompt **Negative prompt list**: "Write only what you do not want to appear; leave it empty if there is none. Do
not pad the list or repeat content already stated in the positive prompt." [OFFICIAL] Official categories: faces
("No face distortion, No face swapping, No extra fingers"), text ("No subtitles, No watermark, No complex text, No
extra brand names"), camera ("No large camera movements, No frequent shot cuts"), space ("No axis errors") and
consistency ("No character position changes, No costume changes, No scale drift") [OFFICIAL]. One line, last,
5–12 items [INFERRED].

### 3.11 Visible text
**(a) Reliability.** Alibaba lists "on-screen text rendering accuracy" as still "improving but not yet where we want
them" [OFFICIAL]; the general guide says "Text renders approximately — specific words will not be precise"
[OFFICIAL]. First-party examples still request short titles, chart labels and packaging copy [OFFICIAL] — so the
model attempts text, but exact wording is not reliable.

**(b) Clean plate — default in Analyze Mode.** Generate without on-screen text and add hooks, captions and labels
in post (`atp.py captions`, libass). Use Alibaba's own phrasings as the closing line: "Do not show any text, subtitles, numbers,
interface elements, or watermarks on screen." or the negative-list form "No subtitles, No watermark, No complex
text, No extra brand names"; an official re-render example even excludes "text, Chinese characters, English
letters, numbers, labels, subtitles, watermarks, logos or platform corner bugs" [OFFICIAL]. Pair it with positive
text-free surfaces ("plain unmarked packaging", "the screen shows soft abstract color") [INFERRED]. Never describe
signs, captions or screens with words, and never quote non-dialogue strings — the official dictionary shows that
described subtitles ('White English subtitles "My little Max…" appear at the bottom of the screen') are requested
content [OFFICIAL example]. Keep the no-subtitles item whenever there is dialogue [INFERRED]. With reference media
add: "do not reproduce any text, captions, usernames or watermarks from Video 1" [INFERRED from the official "do not
inherit" pattern]. Never cut these lines to fit Higgsfield's 5000-character limit (cut descriptive wording):
with "captions, usernames" and "no on-screen text" trimmed, a garbled grey ghost of the source caption stood
on the wall at its old position for the whole clip; restoring them and giving the model a reference with the
caption inpainted removed it (§4.0 item 19) [VERIFIED CE-045 a3].

**(c) Intentional in-frame text.** Only when it belongs to the scene (a sign, packaging, a screen UI), is 1–3 short
words, large, frontal and mostly static; state it once, bound to its surface, and QC every frame [INFERRED]. Anything
longer, or any caption/subtitle/hook, goes to post. Approved real product text comes from the reference image:
"keep the printed label exactly as in Image 2; add no other text" [INFERRED]. The official packaging example asks for
text "sharp and legible… without deformation" [OFFICIAL]; verify with `atp.py qc --mode analyze --allowed-text
"<text>"`.

**(d) Edit operations — removing source text (Edit Mode).** Wan 3.0 can take the supplied clip as `video_references`
and regenerate it with an edit instruction [OFFICIAL capability]; text removal itself is not documented [INFERRED].
Small static overlays (handles, corner bugs, watermarks) can first be removed locally with `atp.py clean --delogo`;
captions over the subject belong to the model. Following the official edit pattern ("Edit the video: remove … in video
1…; the … rest of the frame stay unchanged") and "modifying one item at a time is the most stable" [OFFICIAL], run
text removal as its own first pass:
"Edit the video: remove every caption, subtitle, username, watermark, sticker, timestamp, meme text, UI overlay and
overlay logo from Video 1 and reconstruct the scene behind them; the people's movement, the camera, lighting, sound
and timing stay unchanged. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen."
Keep a specific source text only if the user asked, naming it ("keep only the lettering on the mug"). Limits: source
≤15 s (reference-video cap); `duration:-1` keeps the source length [OFFICIAL]. Verify with `atp.py qc --mode edit`
for residual or ghosted letters.

**(e) Watermark risk.** Upstream `watermark` defaults to `false` (when true: "AI Generated", lower-right) and is not
exposed [OFFICIAL/HF]. The practical risk is model-invented corner marks or "platform corner bugs" copied from
references [INFERRED]; `atp.py qc` OCR catches them — regenerate with the clean-plate line and cleaner references.

### 3.12 Character / identity consistency
Wan 3.0 claims fine-grained consistency of "facial features, hairstyle and hair color, body shape, clothing, and
accessories" in reference mode [OFFICIAL]. One person per reference image ("a single-person setting image
corresponds to exactly one character") [OFFICIAL]; clean, well-lit front or three-quarter views; bind with "adopting
facial features, hairstyle, and clothing". To replace a source performer: "Replace the <person> in Video 1 with the
<person> in Image 1, keeping only the motion, trajectory and camera of Video 1; do not inherit Video 1's
appearance" [composite of OFFICIAL patterns]. Labels "unique and consistent — no pronouns or synonyms" [OFFICIAL].
The identity image brings its clothing, lettering and props (`reference/anomaly-catalog.md` §2.17): crop it above
the collar when its clothing differs from the kept garment and name that garment in positive words (the photo's
overshirt re-dressed the man in some rolls, CE-035); a print the photo cuts off is finished by the model, in one
case as an upside-down second line on every frame: crop above it and state "a plain black crew-neck t-shirt with no
print, no lettering and no logo" [VERIFIED CE-039 a2]; describe the replacement's glasses positively; state a
hidden face or closed eyes of the source in words; flip a mirrored selfie photo (`reference/generation-system.md`
§5c.2b).

### 3.13 Product and object fidelity
Official claim: "multi-angle appearance, hardware structure, logos, and material details remain stable shot to
shot" [OFFICIAL]. Attach 1–3 clean single-object product images (no grids), bind "Prop A corresponds to Image 2,
adopting structure, material, and color" [OFFICIAL] and lock geometry: "keep the exact silhouette, proportions,
part count and construction of Image 2 without deformation; no scale drift" [OFFICIAL phrasing]. For a first frame
that must match an approved packshot, use frame mode ("pixel-level reproduction") [OFFICIAL].

### 3.14 Integration and continuity
**Across clips.** "Setting the last frame of one clip as the first frame of the next creates seamless transitions"
[OFFICIAL]; extract it with `atp.py last-frame` (exact, lossless), then `media_upload` → PUT → `media_confirm` [HF contract]. Frame mode takes no references or driving audio [OFFICIAL]; carry the voice in reference mode with an `audio_references` slice cut from clip A. Upstream extension exists (its output includes the source; input + output ≤ 30 s), but Higgsfield exposes no extension mode for this id [OFFICIAL; HF]. Extensions
restate "the character traits, clothing, and scene to avoid continuity glitches" [OFFICIAL]. Reuse identical
references and binding sentences across a project [INFERRED].

**Inserted or replaced assets.** Official phrasings to reuse: "have the woman in video 1 put on the hat from image
1, naturally fitting her head shape"; "The position, orientation, size ratio, quantity and mutual occlusion of every
object in the scene are copied exactly; no additions, no deletions, no moves"; "the character and scene edges blend
naturally with no cutout artifacts" [OFFICIAL]. Build the asset sentence as: size relative to a body part or known
object → orientation (which face toward camera) → contact and grip (which hand, which fingers, where) → occlusion
("her fingers overlap the front edge") → end position [INFERRED structure]. The size relation comes from the plan's
size reckoning (`reference/anomaly-catalog.md` §2.7): the ratio to the named neighbour at the same depth, the depth
in the shot line ("on the dresser behind him, about 2.5 m from the lens"), "a small object in the background" where
it is one, and "No scale drift" in the consistency line. On `wan3_0_prime` these words are a check, not a
control: tighter fractions, neighbour ratios, padded references (p40 down to p16) and "no oversized"
exclusions did not move a small placed product (12 of 12 same-form retries, -15 to +24 %; §5), and a start
frame at the reckoned height cannot be combined with the source video (§2.5 gotcha 9). The control is a
size-and-place guide image (§4.0 items 13–14; `reference/generation-system.md` §4b.6) or an anchor from the §5
passing list, and the first output is measured with `atp.py scale` [OBSERVED 2026-10-08..13]. Guardrail edits
(`reference/brand-guardrails.md` §4) use the same edit grammar: "remove only the brand name, logo and markings from
the green can on the shelf in video 1; keep its shape, size, position, lighting and shadow; it becomes a plain
unbranded can of the same colour" (never "blur" or "pixelate"), and "remove only the third can at the left end of
the desk in video 1 and reconstruct the desk and wall behind it; keep the two other cans exactly as they are",
with the consistency line listing what stays [INFERRED].

**Scene light on the asset.** Official examples name the source, angle, softness and color: "warm sunlight slants
from the upper-left-back at about forty-five degrees, shadow edges slightly soft, direction uniform"; "real contact
shadows"; "The figure's face naturally receives mixed lighting from warm indoor light and cool neon light outside
the window" [OFFICIAL]. Add reflections on glossy surfaces and a contact shadow under placed objects [INFERRED].

**Persistent states.** Official: "After the handover is complete, the bouquet is only in that character's hands";
"There is always only one orb, stable in size, not duplicated, not vanished, not deformed"; "Do not change the
positions of pine trees and rocks" [OFFICIAL]. Write end states for placed objects, open/closed containers, liquid
levels and which hand holds what ("the cup stays in her left hand, half full, lid on") [INFERRED].

**Posture, support and place** (`reference/anomaly-catalog.md` §2.16). Write the pack's posture, its
support and the reason for its spot as one chronological sentence, positive first, then the exclusions in
the "Negative prompt list:": "lies flat on its wide face with its printed label facing up, resting entirely
on the bare marble at the near edge of the table, a band of bare marble at least as wide as itself between
it and his forearm, where someone sets a sachet of gum down out of the way of their writing; it never
slides, tilts, stands up or leans" with "no standing, leaning, propped or tilted sachet, no sachet on its
edge, no sachet on a sheet, no sachet touching his arm" [VERIFIED 2026-10-09, CE-012]. A support is bare
surface or a large solid object the source frame shows; a prop the model has to invent renders as a sliver
and the pack leans on nothing (CE-013). Name the object that is picked up and say the pack stays (CE-007).

**Source surfaces.** Wan re-renders a printed surface of Video 1 (a poster, an airline livery, a gate board,
a monitor page) when the prompt only describes it as blank or plain, or does not name it. Replace it with a
named concrete thing in the edit grammar and put the original item in the exclusion line: "The right monitor
in Video 1 shows a news web page: replace its whole screen with a plain dark candlestick chart (green and
red candles, no text, no headline, no photo)" with "no news web page, no red header banner, no politician
photo, no headline text on any monitor"; "remove only the red, orange and yellow airline livery from the
winglet and reconstruct it as plain white metal" [VERIFIED on the retry: run 08 V01 V04, run 09 V04]. "Gate
boards behind him showing no text" and "a plain blank grey panel" came back printed in 3 attempts (run 09
V08).

**Counts and use** (`reference/anomaly-catalog.md`). Count multiples in the official "always only one orb" form
("There are always exactly three capsules on the desk right of the lamp, not duplicated, not vanished, also while
he walks past and after he comes back"); write each use as the part, the preparation step and the contact point
inside the shot's action clause ("he flips the spout cap open with his thumb, puts his lips on the spout and drinks
through it with his head level, both hands around the bottle"); restate counts and states in the opening words of
every shot after a cut or an exit; put one item per product in the "Negative prompt list:" for its own wrong use
and count ("no drinking from any side of the bottle other than the spout", "no capsule appears or disappears")
[INFERRED; observed 2026-10].

**Guide, camera lock, swap grammar, empty surfaces** (`reference/generation-system.md` §4b.6, §5c.3, §4,
§4b.5). Bind the guide as spot and size only and repeat it in the anchor sentence ("exactly where Image 4 shows it
… keeps exactly the size it has in Image 4"), with no sizing words beside it; the camera lock is its own sentence
("the camera keeps the same position and framing for the whole shot; no zoom, push-in, pan or tilt toward the
carton; the hand, the keys and the trackpad keep their place in the frame"); a swap is "Replace only <the source
object> with <the product> at that exact spot, on the same footprint; <the source object> does not remain
anywhere"; an empty surface is written empty, per shot ("shot 1: only the laptop and the planner; no can
anywhere"); name the one hand in frame and the bare empty area, and the object a hand picks up. Items 13–19 of
§4.0 carry the verified wording.

**Known failures.** Alibaba's own exclusion categories name them: face distortion/swapping, extra fingers, twisted
limbs, "clipping artifacts", "cutout traces", "characters running illogically", "No scale drift (common in editing
/ reference scenarios)" [OFFICIAL]; plus text, audio texture and wide orbits (above). Slop prevention: §5.

## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach
Verbatim first-party examples (trimmed with […]):

1. Full-modality prompt — wan3.0 Prompt Guide, https://www.alibabacloud.com/help/en/model-studio/wan3-video-generation-prompt-guide
   > "Eastern epic xianxia, majestic and imposing. A general in heavy armor holds a long spear, riding alone on a
   > golden qilin […] 15 seconds, pacing shifts from steady restraint to explosive release. The general's appearance
   > references Image 1, facial expression references Image 2, mount references Image 3, voice timbre references
   > Audio 1. Shot 1 (00:00-00:03): Extreme wide establishing shot, 24mm wide-angle, extreme low angle, camera
   > static. […] Shot 2 (00:03-00:06): Close-up, 85mm telephoto, shallow depth of field. […] The general speaks low:
   > "This pass, I have guarded for ten years." […] Negative prompt list: No modern elements, no subtitles or
   > watermarks, no extra characters, avoid facial distortion and continuity errors, avoid blur and low resolution."
2. Timed shots — same page
   > "This story is told from a third-person perspective, a short drama about letting go and rediscovering hope.
   > Shot 1 [0-3s] A boy sits alone in a corner of the playground, looking down at the letter in his hand, then sighs
   > softly, eyes lost. Shot 2 [4-6s] Hard cut, fixed camera, focused on the boy's eyes, tears glistening, filled
   > with loss and helplessness. […]"
3. Reference writing — same page
   > "The child in Image 1 stands in the entryway of the modern apartment in Image 2" · "Replace the skateboarding
   > man in Video 1 with the woman in Image 1, keeping the skateboarding action, trajectory, and scene unchanged" ·
   > "Style references Image 2; Only reference the color tone and lighting of Image 2, not the characters"
4. Motion-only reference — same page
   > "Reference the character from Image 1; use Video 1 only as a motion reference. Generate a one-take,
   > real-phone-shot-quality dance video in a pure-white shadowless studio: bright even soft light, clean
   > background, the camera essentially fixed, with no transitions and no cuts. […] The reference video is used only
   > for motion control; do not inherit its character appearance. […] with no subtitles and no watermarks."
5. Edit — same page
   > "Edit the video: remove the woman's sunglasses in video 1, revealing natural eye makeup and gaze; the woman's
   > movement and the rest of the frame stay unchanged."
6. Organized request with state persistence — wan3-pe skill, https://g-adoc.alcasset.com/media/maas_docs/sfm/common/files/6a4b3c2d1e0f9cef.zip
   > "2. The character in Image 1 receives the handed-over bouquet with both hands, brings it to his chest, smiles,
   > and nods in thanks to the other person, using Audio 3's timbre to say: "Thank you very much." 3. After the
   > handover is complete, the bouquet is only in that character's hands."
7. Clean-plate line — same prompt guide (creative example)
   > "Do not show any text, subtitles, numbers, interface elements, or watermarks on screen."
8. Verified in use (CE-012, 2026-10-09; the user's complaint: a sachet "standing at his arm while he writes")
   > bad: "A single closed sealed Neuro Energy & Focus Peppermint sachet stands upright with its bottom edge
   > on the bare marble at the lower right of the frame, leaning back against the side of a closed black
   > hardcover notebook that lies flat beside it […] to the right of his writing forearm"
   > good: "[…] sachet lies flat on its wide face with its printed label facing up, resting entirely on the
   > bare white marble in the bottom right of the frame, on the near side of the table, nearer the lens than
   > his hands and forearm, where someone sets a sachet of gum down out of the way of their writing. It is
   > fully inside the frame, with a band of bare marble at least as wide as the sachet itself between it and
   > his forearm, hands and the exam sheets; nothing touches it and nobody picks it up. […] it stays flat on
   > that spot for the whole clip and never slides, tilts, stands up or leans"
   > passed QC: posture and support at 30 fps, size 1.05×, in sync. The same flat wording failed on a shelf
   > and on a glossy table (run 09 V11 V12: propped, upright). A can standing on its base on the grill's fixed
   > front shelf, named in the scene and excluded from the board, the lid and the walls, passed posture and
   > support at 30 fps (run 09 V11 a4, CE-021); that take was flagged for size on an assumed 1 m distance, so
   > it is not verified.
9. Verified on the retry (a source surface, run 09 V04)
   > bad: "right a plain market chart with no readable text" (the news page came back with its headline)
   > good: "The right monitor in Video 1 shows a news web page with a red header, a politician's photo and a
   > large headline: replace its whole screen with a plain dark candlestick chart (green and red candles on a
   > dark background, no text, no headline, no photo, no red banner)." + "no news web page, no red header
   > banner, no politician photo, no headline text on any monitor"
10. Failed, not verified (CE-011, run 08 V17; the miss: a closed carton leaning on a bottle rendered 1.71×
    then 1.78× its expected size against that bottle; the cause: a model limit for a small flat pack
    against a same-plane neighbour, the size words did not move it)
   > bad: "The carton is tiny, like a pack of gum: only about one fifth as tall as the black bottle it
   > leans on […] about one eighteenth of the frame height and much smaller than his head, and it keeps
   > that small size in every frame" (a1, "a quarter of the bottle": 1.71×; a2, this wording: 1.78×)
   > good: none verified. The lever is the anchor class (§5 passing list), not the size words.
11. Observed, not verified (CE-018, run 09 V04; the miss: the placed can was absent from 0 to 4.2 s and then
    appeared; the likely cause: the can named late, and a video reference with no such object)
   > a2: "An open Celsius Cherry Cola can […] stands upright on the desk right beside the glass […] always
   > exactly one can and one glass, not duplicated, the can is never picked up."
   > a3 added: "The can and the glass are both on the desk from the very first frame to the last frame; the
   > glass is lifted only at about three seconds, while the can never moves and is never touched, never
   > picked up, and does not appear or disappear" and "visible from the first frame to the last".
   > Result: the can in frame from 0 s on one fixed spot (dense 0 to 1 s and 0 to 4.5 s), but the take
   > failed size, so it is not verified; a4 kept the sentence and the can vanished at 2.8 to 3.4 s.
12. Observed, not verified (CE-019, run 09 V07; the miss: the can slid along the table between 1 s and 2 s;
    the likely cause: a loosely named spot)
   > a1: "A closed Celsius Cherry Cola can stands upright on the kitchen table in the centre of its length,
   > between the roommate and the laptop […] the can stays where it is"
   > a2: "[…] at the left end of the kitchen table, the end nearest the stove, a hand's width in from the
   > table's left edge […] there from the first frame […] The can does NOT move, slide, rotate, shift or get
   > touched in any shot: the table's left edge and the can keep exactly the same relation, one hand's width
   > apart, in shot 1 and in shot 3, and the cut hides no move" + "no moving can, no sliding can, no can that
   > changes place on the table"
   > Result: the slide at 1 to 2 s was gone (x 182 at 1.0 s, 180 at 2.9 s), but the can relocated across the
   > shot-2 cut; not verified.
13. Verified, the size-and-place guide (CE-054, run 12 V08 a2; the miss: a carton on the near desk strip, 217 px =
    17 % of the frame height, A 1.32× / B 1.57× agreeing, plus an invented second fist; the cause: a model limit,
    sizing words did not move it)
   > bad (a1): "[…] stands upright on its base on the bare wooden desk to the right of the keyboard, a hand's
   > width from the keyboard's right edge, nearer the lens than the monitor stands […] a small flat object, 7.5
   > cm tall and 7.5 cm wide and 1.6 cm thick: about a sixth of the keyboard's length […] it fills about one
   > twelfth of the frame height and keeps this size"
   > good (a2): "Image 4 is a size and placement guide only: it shows the carton at its true small size standing on
   > the bare desk in front of the round base of the right monitor, beside the keyboard; use only that size and
   > that spot, never its crop, hand or keyboard as new content. […] stands upright on its base on the bare
   > wooden desk right of the keyboard, in front of the round black base of the right monitor, exactly where
   > Image 4 shows it […] only the hand resting on the keyboard's left edge and the man's left forearm are in
   > frame, no other hand is near the carton. […] about four keyboard keys wide, much smaller than the man's
   > hand, and keeps the size it has in Image 4"
   > passed [VERIFIED 2026-10-13]: 141 px = 11.1 % of the frame height, constant, A 1.20× (key pitch), B 1.02×
   > (distance), no second hand, label legible, in sync. Guide: the first take's carton cut out and pasted back at
   > 0.65× on the source desk crop, perspective and shadow kept. Seven more guided takes landed within 1.25×:
   > CE-034 a3 (0.91–0.93×), CE-057 a2 (A 1.21× / B 0.96×), CE-064 a4 (1.0–1.04×), CE-074 a2 (0.89×), CE-078 a2
   > (0.85×), CE-076/CE-081 b2 (A 1.21× / B 1.10×), CE-048 a2 (cup gone, B 1.06×). Guides that failed, failed on
   > place or copy: laptop deck (CE-055, CE-061, CE-084, CE-087), the source's scene or person copied (CE-067,
   > CE-069), a flat paste copied (CE-052). The sentence naming a forearm beside the hand held here and drew a
   > second fist in CE-085 and CE-089: name only the one hand and the bare empty area.
14. Verified, a spot that exists in the source plus a scale reference (CE-034, CE-038, CE-040, run 07 V16 a3; the
    miss, the client: "please check sizing of the box, I know it's close to the camera here, but it's next to the
    notebook and seems really big in relation to the notebook"; the cause: the working hands cover every bare spot at
    the neighbour's depth, and a layout the frame cannot hold is resolved by standing the pack on the neighbour)
   > bad (a1/a2): the carton lying or standing "directly to the right of the open spiral notebook" with "Image 4 is
   > a size reference only: it shows this carton standing on the table beside the notebook […] about one third as
   > wide as the notebook page" (1.7–2.1× flat; 1.23–1.31× upright, standing on the notebook page)
   > good (a3): "Image 4 is a size and spot reference only: it shows this carton standing on the grey front edge of
   > the table at the front-left corner beside the notebook of Video 1, only about one third as wide as the
   > notebook page; use that size relation and that spot, not its framing, wall, lighting or perspective. […] it
   > stands upright on its base on the bare grey front edge of the table at the front-left corner, to the left of
   > the open spiral notebook, its base level with the notebook's front edge, no nearer to the lens than the
   > notebook"
   > passed [VERIFIED 2026-10-12]: A 0.91–0.93×, B 0.90–0.91×, constant at 0.0, 3.0 and 6.2 s, count 1, the same
   > spot on both sides of each insert, in sync.
15. Verified, grounding (CE-043, CE-044, run 07 V16 a3; the miss, the client: "the neurogum package looks a bit
    fake underneath (like it is floating and lightning doest match too)"; the cause: the layout composite
    carried a pasted look, the base stood on the seam between wood and steel, and QC wrote "contact shadow" without
    a 3× crop; a grounded layout image plus grounding words (a1) still gave a hard clean base)
   > bad (a1): "Image 4 is a size, spot and grounding reference: it shows this carton at the front-left corner
   > beside the notebook […] in the room's warm dim light with its soft contact shadow and faint reflection on the
   > steel; use that size, spot, angle and grounding, not its framing or wall"
   > good (a3): "Image 2 gives only its exact printed label and artwork, not its studio lighting, shadow or
   > background; Image 3 shows this same carton as it sits in the room and gives its look and grounding: soft phone
   > focus, slightly muted warm colour, its right side and lower part in shade, a soft dark contact shadow under
   > and in front of its base on the brushed steel and a faint blurred reflection of its lower edge […]; adopt that
   > look and grounding, not Image 3's framing or wall"
   > passed [VERIFIED 2026-10-12]: steel under the base lum 68–70 against 136–139 clean, a bluish reflection tint,
   > base 43 px inside the steel band, carton lum 98–99 against steel 107–112 and wood 127–137.
16. Verified, a swap and the product's material (CE-048 → CE-058 → CE-064, run 12 V04 a4; the misses: a1 kept the
    iced cup and added a second can at 1.9–2.4×; a2 passed size but the can "looks like an animation or a photoshop
    placement", the user; the causes: the swap written as an addition plus a negative, and no material sentence)
   > bad (a1): "A single closed […] can stands upright on the desk at the back of the desk near the monitor stand
   > in both shots: in shot 1 at the exact spot where the iced Dunkin cup stood […]" with "no Dunkin cup" in the
   > negatives
   > good (a4): "Replace only the iced Dunkin coffee cup with the red straw that stands at the back of the desk
   > behind the customer's elbow in shot 1 with one closed […] can that stands upright at that exact spot, on the
   > same footprint, as in Image 4; the cup does not remain anywhere on the desk. […] The can reads as a real
   > aluminium can in the room: a curved metal body with a soft specular highlight and a faint reflection of the
   > room, the label wrapped around the curve, shading darker toward one side, a soft contact shadow, not a flat
   > cut-out" with layout references (Image 4, 5) built from a realistic can crop, for spot and scale only
   > passed [VERIFIED 2026-10-13]: paste test 0–1 signs, drink containers 1/1/1, the can at the cup's spot in both
   > shots, shot 2 1.04× / 1.04×, last frame 1.01×.
17. Verified, a mirrored source, an open pouch and a plain shirt (CE-030, CE-031, CE-039, run 07 V20 a2; the
    misses, the client: "everything in the frame is reversed except the bag. Text on his shirt, guitar on the wall.
    Maybe flip video, then add bag. Also, maybe bag here is open, it's still sealed. I think he'd have it open if
    he's in class"; the causes: the source and the identity photo were both mirrored selfies, the plan defaulted to
    "sealed, untouched", and the photo's cut-off chest print was finished upside down)
   > bad: "Video 1 is the motion, camera, framing, cut and timing reference: […]"; "[…] adopting facial features,
   > hairstyle, skin tone, build and clothing […]"; "a sealed stand-up pouch […]"; "it stays closed"
   > good: Video 1 and Image 1 flipped in preparation; "Video 1 is already in true orientation and is the motion,
   > camera, framing, cut and timing reference: […]; nothing is mirrored or flipped and all lettering reads
   > correctly from left to right"; "[…] clothing (short brown hair, trimmed beard, a plain black crew-neck t-shirt
   > with no print, no lettering and no logo)"; the pouch "top torn at the tear notches, zipper mouth open, a few
   > tablets with green flecks visible in the mouth only, upright on its gusset, label turned about twenty degrees
   > toward the lens, its left side two finger-widths from the notebook's right edge", with "no sealed pouch, no
   > second pouch, no loose or spilled gum, no hand taking a piece, no chewing, no hand touching the pouch" and
   > "no mirrored image, no reversed lettering, no mirrored label, no text or print on the t-shirt"
   > passed [VERIFIED 2026-10-12]: guitars frame-left and right-handed, the pen in the frame-left hand, the tee
   > plain (OCR none), the label legible at full resolution, count 1 in every dense checkpoint, the same spot across
   > the flash (drift ≤ 3 px), in sync.
18. Verified, empty surfaces (CE-046 run 12 V05 a2; CE-078 V20 a2; the misses: padded standing-can references pulled a
    standing can onto the desk from frame 0 (1.66×) for a source whose can only enters in a hand; "out of frame in
    shot 1" put a hero can in shot 1 and another on the keyboard in shot 2)
   > bad: the can "enters with the hand" described, the desk not mentioned; "in shot 1 its spot is out of frame at
   > the other side of the laptop"
   > good: "[…] and an empty black desk […]; nothing else stands on the desk at any moment"; the can "comes up from
   > below the frame holding […]" and leaves below the frame edge; "Shot 1: […] the desk holds only the laptop and
   > the planner; no can anywhere", negatives "no can in shot 1, no can on the laptop, no can on the keyboard", the
   > guide for shot 2, the camera lock sentence
   > passed [VERIFIED 2026-10-13]: V05 empty desk at 30 fps in 0–1 s and after 2.0 s, the can enters in the hand at
   > 0.8 s, exits below the frame by 1.97 s, 1.00×; V20 shot 1 count 0, shot 2 count 1 on bare wood in front of the
   > lunch box, 0.85× / 0.77×, no hand contact.
19. Verified, the clean-plate lines and a clean reference (CE-045, run 07 V16 a3; the miss: a faint garbled grey
    ghost of the source caption on the wall for the whole clip; the cause: the lines were trimmed to fit 5000
    characters while the video reference still carried the burned-in caption)
   > bad (a2): "Do not inherit the appearance, clothing, text, watermarks or branded items of Video 1"; "No
   > subtitles, captions or other on-screen text"; negatives without "no on-screen text"
   > good (a3): "Do not inherit the appearance, clothing, text, captions, usernames, watermarks or branded items of
   > Video 1"; "No subtitles, captions, letters or other on-screen text anywhere"; "[Negative Prompts] no subtitles,
   > no on-screen text, […]", other wording cut to fit; the video reference replaced by a copy with the caption
   > inpainted from the static wall
   > passed [VERIFIED 2026-10-12]: no source text on the wall in any sample.

Patterns they teach:
- **Order:** overall description (genre, length, pacing) → reference bindings → timed shots → dialogue → sound →
  style/mood → one exclusion line (1).
- **Camera first, then subject:** each shot opens with shot size + lens + angle + camera state, then the subject's
  action (1, 2) — camera motion and subject motion are separate clauses.
- **Temporal markers:** `Shot N (00:00-00:03):` or `Shot N [0-3s]`, one style per prompt; transitions named ("Hard
  cut, fixed camera") (1, 2).
- **Sentence style:** short declarative present tense; concrete physical detail instead of adjectives of quality
  (1, 2).
- **Reference syntax:** "<role> references Image N", "the <noun> in Image N"; partial borrowing says what to take
  and what to leave ("not the characters", "do not inherit its character appearance") (3, 4).
- **Exclusions:** a single "Negative prompt list:" line, or one closing "no …" sentence (1, 4, 7).
- **Dialogue/audio:** speaker + verb + colon + quoted line; timbre "using Audio N's timbre to say:" (1, 6).
- **Edits:** "Edit the video: <one change> in video 1; <everything else> stay unchanged." (5).
- **States:** end states are written explicitly (6). **Length:** ~60 words for a 10 s drama (2) to 200+ for 15 s
  multi-reference (1).

### 4.1 Text-to-video
Follows patterns: order, camera-first shots, timecodes, one exclusion line.
```text
<Generate single shot.>  (omit for multi-shot)
<Genre/format + one-sentence overall description, pacing, real-time speed>.
Shot 1 [0-4s] <shot size, lens, angle, camera move>. <Subject with 3–6 visual descriptors> <action with speed/amplitude> in <scene: foreground/background>, <light source, direction, color temperature>.
Shot 2 [4-8s] <hard cut | seamlessly continue…>, <camera>. <Subject action and end state>.
<Label> says: "<line>" <tone, pace>. | No dialogue.
Sound: <SFX>; <BGM style | No background music.>
Style and mood: <art style>, <color tone>, <mood>.
Negative prompt list: No subtitles, no on-screen text, no watermark, no slow motion, no costume changes, <task items>.
```
Worked example (8 s, 9:16, 720p): "Generate single shot. A calm demo moment in a small home workspace, steady real-time
pacing. Medium close-up, 50mm, eye level, the camera pushes in very slowly. A young woman with shoulder-length dark
hair and a grey knit sweater lifts a matte white handheld speaker from a wooden desk with her right hand, turns it
slowly to show its rounded side, then sets it back down exactly where it was; its soft shadow returns under it.
Soft window light from the left, warm tones. No dialogue. Sound: the soft tap of the speaker on wood, quiet room
tone. No background music. Style and mood: natural photographic realism, calm. Negative prompt list: No subtitles,
no on-screen text, no logos, no watermark, no extra objects on the desk, no slow motion."

### 4.2 Start frame (and end frame) to video
Follows patterns: motion + camera only (the frame defines subject and style), explicit end state, one exclusion line.
```text
<Generate single shot.>
Continue from the first frame: <what moves first, speed>, <then>, <end state>. <Camera: fixed | slow push in | …>.
(FLF) End exactly on the final frame: <pose/position/composition to land on>.
<Sound / dialogue | No dialogue. No background music.>
Keep <subject>'s appearance, clothing and the scene layout unchanged.
Negative prompt list: No subtitles, no on-screen text, no watermark, no extra people, no costume changes.
```
Worked example (6 s, 9:16 frames: a dog sitting on a porch → the same dog lying down): "Generate single shot. The dog
looks toward the street, ears lifting, then slowly lowers itself onto its front paws and settles into the lying
position of the final frame. Fixed camera at eye level. Soft afternoon light unchanged. Sound: a faint breeze and
one quiet sigh from the dog. No dialogue. No background music. Negative prompt list: No subtitles, no on-screen
text, no second dog, no change of fur color."

### 4.3 Reference-to-video
Follows patterns: wan3-pe sections, "<role> corresponds to Image N, adopting …", timed beats, explicit end states.
```text
[Core Task] Generate a <format> of <overview>. <Label A> corresponds to Image 1, adopting facial features, hairstyle, and clothing. <Prop B> corresponds to Image 2, adopting structure, material, and color; keep its exact silhouette and proportions without deformation. <Scene C> references Image 3, adopting spatial layout and lighting; the person in the image is ignored. <Voice of Label A references Audio 1.> The whole film adopts <style>.
[Plot Summary]
1. Shot 1 [0-4s]: <camera>. <beat, grip, contact>.
2. Shot 2 [4-8s]: <camera>. <beat>; <Label A> says: "<line>". <End state of props>.
[Audio Style] <SFX, voice texture, BGM | No background music.>
[Camera & Core Constraints] <camera style>; real-time speed; <continuity constraints>.
[Negative Prompts] no subtitles, no on-screen text, no watermark, no identity drift, no scale drift, <items>
```
Worked example (10 s, 9:16): Image 1 = approved person, Image 2 = a handheld camera, Image 3 = a rooftop at dusk.
"[Core Task] Generate a short lifestyle clip. The man corresponds to Image 1, adopting facial features, hairstyle,
and clothing. The camera body corresponds to Image 2, adopting structure, material, and color; keep its exact
shape and proportions. The rooftop references Image 3, adopting layout and lighting. [Plot Summary] 1. Shot 1
[0-5s]: wide shot, slow tracking. The man walks to the rooftop edge holding the camera from Image 2 in both hands,
low warm sun from his left. 2. Shot 2 [5-10s]: hard cut, medium close-up, fixed camera. He raises the camera to eye
level and takes one photo; the camera stays in his hands throughout. [Audio Style] Wind, distant traffic, one
shutter click. No dialogue. No background music. [Negative Prompts] no subtitles, no on-screen text, no watermark,
no identity drift, no extra people."

### 4.4 Video edit / extension / motion transfer
Upstream-documented; Higgsfield routing unverified [INFERRED]. Follows patterns 3–5: one change per pass, explicit
"stay unchanged" list, take/leave statements.
```text
Clean regeneration (Edit Mode, pass 1): Edit the video: remove every caption, subtitle, username, watermark, sticker, timestamp, meme text, UI overlay and overlay logo from Video 1 and reconstruct the scene behind them; the people's movement, the camera, lighting, sound and timing stay unchanged. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen.
Edit (pass 2+):  Edit the video: change <target> in Video 1 to <result>; <asset size, grip, light>; the rest of the frame stays unchanged.
Extension:       Extend Video 1: continue after its last frame — <new action>. <Restate subject traits, clothing, scene.>
Transfer:        Reference only the <camera movement | motion | choreography> of Video 1. The performer is <label> in Image 1, adopting facial features, hairstyle and clothing; do not inherit the appearance, text or graphics of Video 1.
```
Extension needs "extend/continue" and restated traits; duration -1 or source + extension [OFFICIAL]; first-party
examples use "forward/backward" inconsistently [OFFICIAL], so write the direction literally [INFERRED].
Worked example (motion transfer, 8 s, 9:16): "Reference only the walking path and camera movement of Video 1. The
performer is the woman in Image 1, adopting facial features, hairstyle and clothing; do not inherit the
appearance, text or graphics of Video 1. She walks the same path along a quiet park lane at the same real-time
pace. Negative prompt list: No subtitles, no on-screen text, no watermark, no face swapping."

## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Gibberish text, subtitles, corner marks | described signage/screens; dialogue without a no-subtitles item; text in references | §3.11 |
| Features bleed between people/props | vague bindings | one subject per image, unique labels, adoption scope [OFFICIAL] |
| Product silhouette/proportion drift | grid references, heavy motion, editing | clean single-object refs, geometry sentence, "No scale drift" [OFFICIAL] |
| **Small placed product renders 1.3–3.5× its reckoned size, whatever the words** (MODEL LIMIT, `wan3_0_prime`: most first takes of runs 08–09 and 12; Celsius cans within 1.25× on the first attempt in 11 of 23 videos of runs 08–09, small Neuro packs in 0 of 7) | a pack, can or sachet set on a surface in a tight handheld or chest-up shot, any depth tried; the nearest plane of a table-level shot (hero-sized, 25–47 % of the frame height); a laptop-side strip; a pack that stands upright or leans; a neighbour that is paper, a notebook or a head; a base cropped by the frame edge | 12 of 12 comparable wording retries moved the multiple −15 to +24 % (median −5 %): spend none. **The lever is a size-and-place guide** (§4.0 items 13–14; `reference/generation-system.md` §4b.6): 8 takes within 1.25× (CE-034 a3 0.91–0.93×; CE-054 a2 A 1.20× / B 1.02×; CE-057 a2 A 1.21× / B 0.96×; CE-064 a4 1.0–1.04×; CE-074 a2 0.89×; CE-078 a2 0.85×; CE-076/CE-081 b2 A 1.21× / B 1.10×; CE-048 a2), put in the FIRST request when no passing anchor fits (CE-070). **Passing anchors without a guide** (delivered take within ~1.25×): (1) in the hand that holds it, or swapped for the source's own handheld object (4 of 4 in runs 08–09, 1.0–1.15×; a static source bottle swapped for a can landed at 1.25–1.27× on edit grammar, CE-049); (2) one sachet lying flat on bare near-side surface, sized by "as long as his index finger, narrower than his open palm, about one tenth of the frame width" (CE-012, 1.05×; the flat wording failed in 2 of 3: run 09 V11 V12); (3) on a bare surface beside a large rigid same-plane object, a laptop (5 of 7 in runs 08–09), which failed in run 12 on cluttered strips, orbit paths and the nearest plane (CE-050, CE-055, CE-061, CE-077, CE-084, CE-087): use it only where `reference/generation-system.md` §4b.1c holds, and with a guide. Caveat (CE-028; re-measured 2026-10-10, §9): several multiples of runs 08–09 were measured against a head or a distance taken from the shot size, with the product often nearer the lens than planned; the same-plane measurements are CE-009 and CE-011, so the limit holds for small flat packs against a same-plane neighbour and is unproven for cans without a guide [OBSERVED 2026-10-08..13] |
| A small pack renders upright, tilted or propped although the prompt says "lies flat" (run 09 V11 V12; CE-012, CE-013, CE-037, CE-041) | the pack planned to lean on a prop the model has to invent; a spot against a person's arm; "lies flat" without the support, the reason and the exclusions; upright references for a stand-up pouch; a top-view reference for a flat pack | the verified sentence of §3.14 (flat, label up, entirely on bare surface at the near edge, a band of bare surface wider than the pack to the arm, the story reason) plus "no standing, leaning, propped or tilted sachet, no sachet on its edge"; references that show the pack lying flat in the scene's perspective; never plan a lean on an invented prop; QC posture, support and place at 30 fps (`reference/anomaly-catalog.md` §2.16) [VERIFIED once; the wording alone failed in 2 of 3] |
| A placed or contents product is absent in the opening seconds and appears later at another spot (run 09 V04 a1: absent 0–4.2 s, then 1.5–1.8× at the left foreground; a4: vanished; CE-018) | the product named late or only in a later clause; a source video reference with no such object | name the product at its anchor in the first clause of the Plot Summary and in the shot's opening state ("from the first frame"); read the dense 0–1 s sheet first; on a miss the one retry changes the form or the anchor class from the passing list (a start frame is out of reach while the source rides as a video reference, §9 lever a), never a flagged note (`reference/generation-system.md` §4b.3) [OBSERVED over 4 attempts; wording alone unproven, §4.0 item 11] |
| The request fails twice within ~15 s with no error text while the video reference shows a real celebrity's face (run 09 V03, both refunded; cause unconfirmed; recorded as CF-001 in `caught_flags.md`) | the person who is swapped is still in the video reference | after the second identical failure plan without the video reference (image references and the written action script), say fidelity and sync are at risk, never send a third identical request (`reference/generation-system.md` §5c.2) [OBSERVED once; the attempt without the video reference passed QC] |
| The source's printed surface comes back (poster, airline livery, gate board, monitor page, shirt print) | the surface only described as blank, plain or "showing no text", or not named at all | replace it with a named concrete thing in the edit grammar and name the original item in the exclusion line (§3.14 "Source surfaces"); QC OCR and a full-resolution look at the surface [VERIFIED on 3 retries; 1 persistent: the gate boards, 3 attempts] |
| A placed pack sits in a hand's lane, on a laptop deck or keyboard end, in the nearest plane, off the camera path or at the frame edge (CE-053, CE-055, CE-056, CE-061, CE-066, CE-070, CE-072, CE-073, CE-077, CE-082, CE-084, CE-087) | a spot the source does not have, a cluttered strip narrower than the pack, an orbit or sweep that leaves the strip, a pack cut by the frame edge | the spot checks of `reference/generation-system.md` §4b.1c; the camera-lock sentence (it stopped a 3.3× push-in and held in CE-061, CE-078); per-shot desk state; name the object a hand picks up [VERIFIED CE-074, CE-078] |
| The source person, clothing, sponsor lettering or monitor text comes back, or the pack is copied as a flat sticker | the guide or layout reference cut from the source frame, or a flat packshot paste | build the guide from bare surface only (`reference/generation-system.md` §4b.6) (CE-052, CE-067, CE-069) |
| Everything the source holds is reversed while the product's label reads correctly | a mirrored front-camera selfie source and a mirrored identity photo | flip both in preparation; "nothing is mirrored" (`reference/generation-system.md` §5c.2b) [VERIFIED CE-030] |
| The swapped person is re-dressed, a cut-off print is invented, the source's glasses stay, or a hidden face shows open eyes | the identity image brings its clothing, lettering, props and open eyes | `reference/anomaly-catalog.md` §2.17; §3.12 [VERIFIED CE-039; CE-035 observed] |
| Small print on a placed pack comes back as wrong letters (Nero, CUM) while large type reads | a wordmark under about 25 px upright; a flat or rotated label; resolution and padding do not help | an anchor that gives the wordmark its pixels, or the limit recorded; QC word by word (`reference/anomaly-catalog.md` §2.9) [no fix has passed: CE-032, CE-036, CE-042, CE-090] |
| A many-cut reference loses its first cuts, ghost-dissolves person-free cutaways and drops an emotion beat; a face effect or mask in the video reference keeps the replaced face; a real person's name stays legible in some shots | one clip with a person identity reference; the video reference carries the effect and the name whatever the prompt says | separate clips on the reference's own cuts (`reference/generation-system.md` §3b.1 item 7); hide the effect or name in the prepared source, or ship flagged (§5c.2b) [not verified: CE-051, CE-079, CE-080, CE-083, CE-086] |
| Product looks pasted on (a can on a dresser at 2–3× real size, squared to the lens, flat cool light in a warm dim room, no contact shadow, straight-on in a low-angle room) | the reference's lighting, exposure, background and camera angle inherited; a tight product crop pulls it forward and up in size; an anchor alone on an empty edge | "the can in Image N: adopt only structure, material, colour and label, not its lighting, background or camera angle"; the room's light on it, "real contact shadows", "edges blend naturally with no cutout artifacts" [OFFICIAL phrasings], its size against a named neighbour, its mark angle, an anchor touching or partly behind something, padded crops; the eleven-sign paste test in QC (`reference/anomaly-catalog.md` §2.15) [INFERRED; observed 2026-10] |
| Spatial distortion | orbit >45° [OFFICIAL] | smaller arcs, slower moves |
| Object snaps, or pauses on a pose then resumes | free physical motion (a spin, toss or roll, or a vehicle's move) given exact times or a required end state | describe the physics only; give the end state a visible cause (a hand stops it, a driver brakes); time product-pun text to the real moment (`generation-system.md` §5b) [INFERRED] |
| Actions compressed or skipped | too many beats per shot | ≤2 actions per 3–5 s shot [INFERRED] |
| Count of multiples changes after an exit, occlusion or cut (three capsules become one after a walk-past) | items not counted per shot; no restatement after the exit or cut | "always exactly N …, not duplicated, not vanished" per shot and after re-entry (`reference/anomaly-catalog.md` §2.1, §2.5) [INFERRED; observed 2026-10] |
| Product used through the wrong part (a straw bottle drunk from the side without the spout; a sealed can sipped) | the use written as a result only ("drinks"), without the part or the preparation step | the part, the preparation step and the contact point in the action clause; one "Negative prompt list:" item naming the wrong use (`reference/anomaly-catalog.md` §2.2, §2.3) [INFERRED; observed 2026-10] |
| A later state leaks into frame 0 (a raised tab on a can cracked later) | a reference image that shows the later state | attach only the t=0 state and state it in the shot's opening clause (`reference/anomaly-catalog.md` §2.3) [observed 2026-10] |
| A thrown or passing thing goes through the product; the product sinks into a surface or shows through an arm | the path written without the product ("he tosses the paper"); "clipping artifacts" are an official exclusion category [OFFICIAL] | write the path relative to the product with the side and the landing spot, or the hit and its consequence; "Negative prompt list: … no clipping, nothing passes through the bottle"; move the anchor out of the path when the story does not need the contact (`reference/anomaly-catalog.md` §2.14) [observed 2026-10] |
| Lip sync off | exact-word expectations [OFFICIAL] | short lines, "Lip sync", audio timbre reference |
| Request rejected | frames + references, or frames + audio [OFFICIAL] | one mode per call (§2.5) |
| Storyboard grid rendered as a frame | undeclared multi-grid reference | "use the storyboard only as shot guidance" [OFFICIAL] |
| Unwanted music/voices | nothing said about sound [OFFICIAL] | "No dialogue." "No background music." |

**AI-slop tendencies and prevention.** `atp.py qc` flags black and frozen spans; `atp.py trim` removes dead head/tail frames deterministically.

| slop tendency | prevention (prompt / params) |
|---|---|
| Dead space, padded length | size `duration` to the beats, or use smart duration, built so "a simple product beat doesn't get padded to 30 seconds" [OFFICIAL]; a visible change every 2–3 s [INFERRED] |
| Arbitrary slow motion | "No slow motion", "no heroic slow-motion posing entrance" [OFFICIAL]; say "real-time speed" [INFERRED] |
| Sudden speed changes | state pacing in the overall description [OFFICIAL]; "no speed ramps" [INFERRED] |
| Unmotivated cuts / transitions | "Generate single shot."; "no flickering, shaking, frame-skipping or self-inserted cut points"; "No frequent shot cuts" [OFFICIAL] |
| Morphing | "no transformation collapsing into a blurry light blob" [OFFICIAL]; "objects keep their shape" [INFERRED] |
| Identity drift | "no distorted or drifting faces", "No face swapping" [OFFICIAL]; restate traits per shot |
| Duplicated / vanishing objects | "not duplicated, not vanished, not deformed" [OFFICIAL] |
| Clothing changes | "No costume changes" [OFFICIAL] |

## 6. Model-specific features and controls
- **Smart duration** (`-1`, billed as 10 s), **thinking mode** (use for dense multi-reference/multi-shot prompts or
  after an adherence miss [INFERRED]) and **Prime** (same capabilities, faster [OFFICIAL]).
- **All-in-one routing** by media type and intent words ("edit video", "remove", "replace", "extend", "continue")
  [OFFICIAL] — avoid those verbs in normal generation prompts [INFERRED]. Official prompt skill `wan3-pe` [OFFICIAL].

## 7. Model-specific pre-generation checklist
- [ ] Mode chosen (never frames + references; never frames + audio); Analyze vs Edit Mode known.
- [ ] `aspect_ratio:"9:16"`, `resolution:"720p"`; frames/sources already 9:16; `atp.py conform` afterwards (§2.6).
- [ ] Reference limits (≤10 images, ≤5 videos ≤15 s, ≤5 audio ≤15 s); input + output ≤30 s.
- [ ] References cited as "Image N / Video N / Audio N" in attach order, each with an adoption scope.
- [ ] "Generate single shot." or contiguous 3–5 s timed shots; camera clause before subject clause.
- [ ] Dialogue quoted with speaker or "No dialogue."; BGM specified or "No background music."
- [ ] Clean-plate line (§3.11b); in-frame text only if short and scene-bound; Edit Mode: removal pass first.
- [ ] Asset size/grip/occlusion, light direction and end states written (§3.14); slop exclusions included (§5).
- [ ] Size: the anchor is from the §5 passing list, or a size-and-place guide (§4.0 items 13–14) carries spot and size; the reckoning (neighbour ratio, depth, fraction of the frame, "No scale drift") is written as a check, and no wording retry follows a miss (`reference/anomaly-catalog.md` §2.7).
- [ ] Spot and camera: the spot passes `reference/generation-system.md` §4b.1c; a camera-lock sentence when the product is near a frame edge or the shot is handheld or an orbit; per-shot desk state; the one hand in frame named with the bare empty area, and the object a hand picks up.
- [ ] Identity image: cropped to the face when its clothing differs from the kept garment, the kept garment in positive words, a mirrored selfie flipped (`reference/anomaly-catalog.md` §2.17); the prepared source flipped, inpainted and cleaned as its card flags (`reference/generation-system.md` §5c.2b).
- [ ] Label pixel budget (`reference/anomaly-catalog.md` §2.9): the wordmark at least about 25 px upright, or the limit recorded before generating.
- [ ] Posture, support and place (§3.14): flat or on its base, on a visible surface, out of a working hand's way, with the story reason; no lean on an invented prop; nothing on a thin sheet; the object that is picked up is named (`reference/anomaly-catalog.md` §2.16).
- [ ] Source surfaces: each printed surface of Video 1 that a guardrail or `generation-system.md` §9b names is replaced with a named concrete thing in the edit grammar, and the original is in the exclusion line (§3.14).
- [ ] Counts with numbers per shot; every use beat names the part, the preparation step and the contact point; one "Negative prompt list:" item per product for its own wrong use and count; no reference shows a later state than t=0 (`reference/anomaly-catalog.md` §3).
- [ ] `duration`, `generate_audio`, `enable_thinking` set deliberately; `get_cost: true`.
- [ ] QC with `atp.py qc --mode analyze|edit`: size, freezes, pseudo-text, corner marks, identity, product geometry; `--dense` on the plan's checkpoints: counts, the part and contact of every use, permanence across exits and cuts (`reference/anomaly-catalog.md` §4).

## 8. Sources
- [OFFICIAL] Wan3.0 – Video Generation API Reference — https://www.alibabacloud.com/help/en/model-studio/wan3-video-generation-api-reference (accessed 2026-09-30)
- [OFFICIAL] Wan3.0 Video Generation (user guide) — https://www.alibabacloud.com/help/en/model-studio/wan3-video-generation-guide (accessed 2026-09-30)
- [OFFICIAL] wan3.0 Video Generation Prompt Guide — https://www.alibabacloud.com/help/en/model-studio/wan3-video-generation-prompt-guide (accessed 2026-09-30)
- [OFFICIAL] wan3-pe prompt optimization Skill (SKILL.md v0.2.0), linked from the prompt guide — https://g-adoc.alcasset.com/media/maas_docs/sfm/common/files/6a4b3c2d1e0f9cef.zip (accessed 2026-09-30)
- [OFFICIAL] Video generation prompt guide (Wan formulas, dictionary, what not to prompt) — https://www.alibabacloud.com/help/en/model-studio/text-to-video-prompt (accessed 2026-09-30)
- [OFFICIAL] Video generation and editing (model list) — https://www.alibabacloud.com/help/en/model-studio/use-video-generation (accessed 2026-09-30)
- [OFFICIAL] Wan2.7 text-to-video API reference (720P 9:16 = 720×1280 table) — https://www.alibabacloud.com/help/en/model-studio/text-to-video-api-reference (accessed 2026-09-30)
- [OFFICIAL] Wan3.0: 30-Second AI Video Generation from Any Input (blog, 2026-08-13) — https://www.alibabacloud.com/blog/wan3-0-30-second-ai-video-generation-from-any-input_603452 (accessed 2026-09-30)
- [OFFICIAL] Wan3.0 at General Availability (blog, 2026-08-27) — https://www.alibabacloud.com/blog/wan3-0-at-general-availability-capabilities-benchmarks-pricing-and-the-workflows-it-changes_603505 (accessed 2026-09-30)
- [OFFICIAL] Wan2.7 vs. Wan3.0: What Actually Changed? (blog, 2026-08-27) — https://www.alibabacloud.com/blog/wan2-7-vs--wan3-0-what-actually-changed_603504 (accessed 2026-09-30)
- [HF] Higgsfield catalog snapshot — higgsfield/catalog-snapshot-2026-09-30.json (captured 2026-09-30); Higgsfield MCP tool contract facts supplied with this task
- [SECONDARY] Third-party API schemas describing `enable_thinking`: fal.ai — https://fal.ai/models/alibaba/wan-3.0/reference-to-video/llms.txt ; Picsart — https://picsart.com/api-platform/models/wan-3.0-video/advanced ; Oxen.ai — https://docs.oxen.ai/inference-api/reference/models/wan-v3-0-video.md (accessed 2026-09-30)
- [SECONDARY] Segmind, "Wan 3 Prompt Guide: Alibaba's Official Formulas, Tested" — https://blog.segmind.com/wan-3-prompt-guide-alibabas-official-formulas-tested/ (accessed 2026-09-30)
- [SECONDARY] Artificial Analysis text-to-video / image-to-video leaderboards — https://artificialanalysis.ai/video/leaderboard/text-to-video ; https://artificialanalysis.ai/video/leaderboard/image-to-video (accessed 2026-09-30)

## 9. Open questions / unverified behaviour
- Exact 720p 9:16 pixel dimensions for Wan 3.0 (no official table). Data point [VERIFIED 2026-09-30, account
  history]: a `wan3_0_prime` job at 9:16 / 480p delivered **480×854 at 30 fps**, although its stored params said
  768×1344. That supports 720×1280 at 720p; measure the first output anyway. The behaviour of `aspect_ratio:"9:16"`
  with a non-9:16 start frame or edit source is still unverified.
- Whether Higgsfield routes edit/extension intents, and whether a text-removal edit reconstructs the scene cleanly
  (not documented upstream either).
- What `enable_thinking` does server-side and whether it changes cost.
- Whether Higgsfield leaves upstream `prompt_extend` on and `watermark` off.
- Whether `medias` order is preserved into Image N / Video N / Audio N numbering.
- How Higgsfield bills video references (upstream bills input + output seconds).
- Per-shot length guidance conflicts (2–5 s vs 4–6 s); inconsistent "forward/backward" extension wording.
- Quality parity of Prime vs standard beyond "aligned capabilities"; API page "preview" vs GA blog.
- Size levers (§5 model limit): the size-and-place guide is proven (§4.0 items 13–14; 8 takes). Still untested: (a) a
  frames-only build, the source's first frame with the product composited at the reckoned height as `start_image`
  (§2.5 gotcha 9), which pins size and may cost motion and sync; (c) asking for 0.6× the reckoned size to cancel a
  ~1.5× bias; (e) pinning the depth with a scene landmark and a same-depth neighbour (V04 a4 reached about 0.086 of
  the frame height against 0.083 planned but lost the can at 2.8–3.4 s). Open: whether a guide's shrink is a stable
  ~20 % of the nearest-plane size (CE-081), and whether a guide on open wood can make a small closed carton lie flat
  on Seedance edits (CE-087, CE-094: no).
- Re-measured 2026-10-10 on the frames still on disk: the Celsius cans stood nearer the lens than planned and than
  the person and were measured against a head at the assumed same depth; the readings are unsettled between about
  1× and 1.4×. So the §5 row stands for small flat packs against a same-plane neighbour (CE-009, CE-011) and is
  unproven for cans without a guide; a product found nearer the lens than planned is a depth miss, a different
  failure from oversize (CE-014, CE-015).
