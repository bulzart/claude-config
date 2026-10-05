---
guide: happy-horse
title: HappyHorse (Alibaba) video model
provider: Alibaba — Alibaba Token Hub (ATH); served via Alibaba Cloud Model Studio and happyhorse.com
higgsfield_model_ids: [happy_horse_video]
guide_version: 1.1
last_verified: 2026-09-30
catalog_snapshot: higgsfield/catalog-snapshot-2026-09-30.json
documentation_depth: low
---

# HappyHorse — model engineering guide

> Scope: Higgsfield id `happy_horse_video` ("Text-to-video and single start-frame animation", provider label "Happy
> Horse") [HF]. First-party documentation consists of API references and a few example prompts; there is no
> first-party prompt guide. This guide is therefore short and conservative, and much of the prompting advice is
> labelled [SECONDARY] (official API partner fal) or [INFERRED]. Output format is fixed at 9:16, 720p (§2.6); the
> upstream default watermark is the main QC risk (§3.11e). The live `models_explore` catalog always wins over this file.
>
> Evidence tags: **[OFFICIAL]** provider docs, paper, model card, API reference, first-party prompt
> guide or first-party examples · **[HF]** Higgsfield catalog, MCP tool contract or first-party
> Higgsfield docs · **[SECONDARY]** reputable third-party testing or articles · **[INFERRED]**
> engineering inference that must be verified in use.

## 1. At a glance

**Who makes it (evidence).**
- Alibaba Cloud Model Studio publishes official HappyHorse API references (text-to-video, first-frame image-to-video,
  reference-to-video, video editing) and model pages for `happyhorse-1.0-*` and `happyhorse-1.1-*` [OFFICIAL]. An
  Alibaba Cloud blog post (2026-06-23, originally on Alizila) states "Alibaba has released HappyHorse 1.1…
  accessible… via its official website happyhorse.com and through an API on… Model Studio" [OFFICIAL].
- Caixin Global (2026-04-10): "developed by the AI Innovation Division under Alibaba's newly established Alibaba Token
  Hub (ATH) business group" after topping the Artificial Analysis leaderboard under an alias [SECONDARY]. Artificial
  Analysis lists the creator as "Alibaba-ATH" [SECONDARY]; API partner fal attributes it to "the Future Life Lab team
  at Taotian Group (Alibaba), led by Zhang Di" [SECONDARY].
- Open weights: some outlets reported an open-source release; fal says it is "closed source" and "the weights aren't
  publicly downloadable" [SECONDARY, conflicting]. No first-party open-weight release found — treat as closed.

**Positioning.** "Generate physically realistic, motion-smooth video from text prompts"; image-to-video with "highly
realistic dynamic rendering… fluid, natural, and rich in detail" [OFFICIAL]. All HappyHorse models list audio as a
feature; output 24 fps MP4, 3–15 s [OFFICIAL]. Version 1.1 (June 2026) improved reference consistency, "motion
expressiveness", instruction following, visual quality and audio-visual sync [OFFICIAL].

**Which version is on Higgsfield?** Higgsfield exposes 720p/1080p, 3–15 s, a single start frame, and ratios 16:9,
9:16, 1:1, 4:3, 3:4 [HF] — the HappyHorse 1.0 surface (1.1 adds 480P) [OFFICIAL] → most likely 1.0 [INFERRED].

- **Best for:** realistic human-centred single shots, smooth motion, cinematic camera moves; animating an approved
  9:16 still with native sound. Artificial Analysis (2026-09-30): text-to-video — 1.1 #10 (Elo 1046), 1.0 #13 (1024);
  image-to-video with audio — 1.1 #6 (1104), 1.0 #9 (1083); #1 in both categories without audio in April 2026
  [SECONDARY].
- **Weaker at / unknown:** no references, no end frame, no negative prompt, no silent switch, no Edit Mode; no
  official prompting guidance; on-screen text unreliable per partner guidance [SECONDARY]; possible corner watermark.
- **Choose it when** a short, realistic single shot or start-frame animation with sound is enough. **Choose another
  model when** you need references, first+last frames, documented multi-shot syntax, Edit Mode (`wan3_0`,
  `minimax_h3`) or a silent render.

| operation | how to invoke on Higgsfield | notes |
|---|---|---|
| Text-to-video | `prompt` only | ratio from `aspect_ratio` [HF] |
| Start frame → video | one `start_image` (9:16) | output keeps the image's aspect ratio [OFFICIAL] |
| End frame, references, edit, extension | — | N/A on Higgsfield (upstream r2v and video-edit exist, not exposed) [OFFICIAL/HF] |

## 2. Higgsfield parameter surface

### 2.1 Parameters per model id
| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `happy_horse_video` | `resolution` | `720p`, `1080p` | `720p` | "Output resolution." [HF]; always `720p` (§2.6); upstream default 1080P [OFFICIAL] |
| `happy_horse_video` | `duration` | number, min 3, max 15 | 5 | "Duration in seconds (3-15)." [HF]; upstream integer 3–15 [OFFICIAL] |
| `happy_horse_video` | `aspect_ratio` | `16:9`, `9:16`, `1:1`, `4:3`, `3:4` | — | always `9:16`; upstream image-to-video has no ratio parameter (follows image) [OFFICIAL] |
| `happy_horse_video` | seed, watermark, audio switch, negative prompt | — | — | not exposed on Higgsfield [HF]; negative prompt and prompt rewriting do not exist upstream [OFFICIAL, by absence] |

### 2.2 Media roles
| role | what it controls | limits / count | notes |
|---|---|---|---|
| `start_image` | first frame (upstream `first_frame`) | exactly 1; JPEG/JPG/PNG/WEBP, each side ≥300 px, aspect 1:2.5–2.5:1, ≤20 MB [OFFICIAL] | "Output pixel count approximates the selected tier while preserving the input image's aspect ratio" [OFFICIAL]; must be 9:16 |

`medias[].value` is a Higgsfield media UUID or completed job ID, never a URL [HF].

### 2.3 Duration, resolution, aspect ratio, audio
- 3–15 s, 24 fps [OFFICIAL]; unsupported values are snapped/clamped [HF contract].
- Fixed 720p, 9:16 (§2.6); with a start frame the frame's aspect ratio wins [OFFICIAL].
- **Audio:** a listed feature with no on/off parameter upstream [OFFICIAL] → expect speech, ambience or effects; strip
  locally for silent deliverables [INFERRED].
- **Watermark:** upstream default `true`, "HappyHorse"/"Happy Horse" text bottom-right [OFFICIAL]; see §3.11e.

### 2.4 Call recipes
Text-to-video:
```json
{"model":"happy_horse_video","prompt":"<PROMPT>","duration":5,"aspect_ratio":"9:16","resolution":"720p"}
```
Start frame → video (9:16 frame):
```json
{"model":"happy_horse_video","prompt":"<MOTION + CAMERA PROMPT>","medias":[{"value":"<IMAGE_MEDIA_ID or JOB_ID>","role":"start_image"}],"duration":6,"aspect_ratio":"9:16","resolution":"720p"}
```
Preflight with `get_cost: true` [HF].

### 2.5 Parameter gotchas
1. `aspect_ratio` is probably ignored when `start_image` is present (upstream image-to-video has no ratio control)
   [OFFICIAL/INFERRED] — the frame must already be 9:16.
2. Only one media role; no end frame [HF].
3. Prompt limit upstream: 5,000 non-Chinese or 2,500 Chinese characters; "Supports any language" [OFFICIAL].
4. Possible provider watermark — check the first output of every session before batch runs (§3.11e) [INFERRED].

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-pick)
| path | params | expected output | action |
|---|---|---|---|
| Text-to-video | `"aspect_ratio":"9:16","resolution":"720p"` | 9:16 at the 720P tier, 24 fps; no official pixel table (third-party docs list 720P as 1280×720 for 16:9) [SECONDARY] → 720×1280 expected [INFERRED] | verify |
| Start frame | same params + a 9:16 `start_image` | pixel count ≈ 720P tier, image ratio kept [OFFICIAL] → ≈720×1280 | verify |

Finish with `atp.py conform --video "<in>" --out "<out>"` (scale-to-cover + focus crop to exactly 720×1280, never
stretched; a no-op when already exact). If `conform` refuses (>12% loss), the frame ratio was wrong — fix the frame
and regenerate [INFERRED]. Never crop to hide a watermark (§3.11e).

## 3. How the model reads a prompt

### 3.1 Recommended prompt structure
No first-party formula exists [OFFICIAL silence]; first-party examples are plain prose of one to five sentences (§4.0)
[OFFICIAL]. The official API partner recommends "[Subject] [does action] in [setting], [time of day], [one atmosphere
or camera cue]" and "Most shots only need about twenty words", because "every extra detail eats into the same budget —
faces drift toward a generic average, hands lose geometry, gait flattens" [SECONDARY]. Working rule: 20–60 words, one
subject, one action chain, one setting, background activity, one camera cue at the end [SECONDARY/INFERRED].

### 3.2 Subject and identity
Two to four concrete visual traits; no praise words ("beautiful, stunning, masterpiece") [SECONDARY]. In image-to-video
do not re-describe the subject; refer to it ("the woman", "the dog") and describe what changes [INFERRED]. The official
i2v example ends with a preservation clause: "maintaining its soft, fuzzy texture and the realistic cinematic lighting
from the original image" [OFFICIAL].

### 3.3 Action, motion and physical interaction
One clear action with manner and pace ("briskly walks forward… pulling its brown suitcase behind it with a sense of
urgency") [OFFICIAL example]. Partner testing: multi-step prose "tend[s] to compress into a single motion"; wardrobe
details "drift in fast action"; extreme slow-motion cues rarely produce the stated time dilation [SECONDARY]. Grip and
states: §3.14.

### 3.4 Environment, lighting and style
Concrete lighting terms ("overcast daylight, wet asphalt, neon reflections in puddles, warm amber backlight") rather than
praise [SECONDARY]. First-party examples mix realism with stylization, including a mid-shot style transformation
[OFFICIAL] — avoid such wording unless wanted.

### 3.5 Chronology, timing and multi-shot structure
No first-party syntax; first-party reference prompts sequence with "first… then" [OFFICIAL]. The partner reports that
multi-beat clips read best as a timecoded shot list ("0-4s: …") [SECONDARY]. Conservative default: one continuous shot;
timecodes only for 2–3 beats within 10–15 s [INFERRED].

### 3.6 Camera language and dedicated camera / motion controls
No camera parameters [HF]. Official example: "The camera follows the bear with a smooth forward tracking shot"
[OFFICIAL]. Partner: "unusually good at camera moves"; "Put the camera cue at the end of the prompt — that's where it
gets the most weight"; two or three concrete cues beat a paragraph [SECONDARY].

### 3.7 References (image / video / audio)
N/A on Higgsfield — no reference roles [HF]. (Upstream `happyhorse-*-r2v` cites "[Image 1]", "[Image 2]" [OFFICIAL].)

### 3.8 Start and end frames
Start frame only [HF]. The 9:16 image fixes composition, identity and aspect ratio [OFFICIAL]; describe motion,
expression, background activity, camera and sound, plus a preservation clause [OFFICIAL example]. End frames: N/A on
Higgsfield.

### 3.9 Audio, dialogue and sound
Audio is generated jointly [OFFICIAL]. Official i2v wording for dialogue: "The bear's mouth moves in perfect lip-sync as
it hurriedly says: 'There's no time left, I'm going to be late!'" [OFFICIAL]. Partner: quoted dialogue is voiced; list
audible sounds and write "no music" to avoid a score; lip-sync languages reported as English, Mandarin, Cantonese,
Japanese, Korean, German, French [SECONDARY]. For wordless clips: "no dialogue, no voices" [INFERRED].

### 3.10 Negative constraints
No negative-prompt field upstream or on Higgsfield [OFFICIAL/HF]; official examples contain no exclusions [OFFICIAL].
Partner: "Most negative cues are wasted words" [SECONDARY]. Use positive descriptions and at most one short exclusion
clause where policy requires it [INFERRED].

### 3.11 Visible text
**(a) Reliability.** No first-party statement [OFFICIAL silence]. The official API partner: "Video models can still
mangle on-screen type more often than they nail it" [SECONDARY]. Treat in-frame text as unreliable.

**(b) Clean plate — default in Analyze Mode.** The partner's advice matches the project default: "frame for a clean
plate and add graphics in post" [SECONDARY]. Describe surfaces as plain and unmarked, use text-free 9:16 start frames,
never quote non-dialogue strings, and add one clause "no text, captions, logos or watermarks" [INFERRED]. Captions,
hooks and labels go on in post (`atp.py captions`, libass).

**(c) Intentional in-frame text.** Not recommended. Only if already present in the start frame and scene-bound, with
"the lettering on the <object> stays unchanged", verified with `atp.py qc --mode analyze --allowed-text "<text>"`
[INFERRED].

**(d) Edit operations — removing source text.** N/A on Higgsfield: no video input on this id; upstream
`happyhorse-1.0-video-edit` is not exposed [OFFICIAL/HF]. Use `wan3_0` or `minimax_h3` to regenerate a supplied clip.

**(e) Watermark risk — highest of the models in this set.** Upstream `watermark` defaults to `true` and stamps
"HappyHorse" (text-to-video) / "Happy Horse" (image-to-video) in the bottom-right corner [OFFICIAL]; Higgsfield does
not expose the switch or document its setting [HF silent]. **Catch it:** run `atp.py qc --mode analyze` on the first
output of every session (and a sample of later ones) — its OCR reports unplanned text; also inspect the bottom-right
region (about the right 35% × bottom 12% of the frame) on first/middle/last frames. **If present:** reject the clip;
do not try to prompt it away and do not crop it out (the 9:16 frame cannot lose a corner); regenerate the shot on
another model (`wan2_7` for start-frame animation, `wan3_0` otherwise) and record the finding so later runs skip this
model until Higgsfield's behaviour changes. A local `atp.py clean --delogo` on that corner is a last resort only with
the user's approval, since it leaves a visible smudge [INFERRED].

### 3.12 Character / identity consistency
Identity comes from the start frame or text [HF]. Use a sharp, well-lit 9:16 frame with the approved face visible;
short prompts (long ones push faces "toward a generic average") [SECONDARY]; avoid fast action where wardrobe must stay
exact [SECONDARY]. 1.1's consistency gains concern reference-to-video, not exposed here [OFFICIAL/HF].

### 3.13 Product and object fidelity
Put the approved object in the start frame; keep motion gentle; add "the bottle keeps its exact shape, proportions and
color" [INFERRED]. Avoid spins that reveal unseen sides [INFERRED]. For strict product work prefer `wan3_0` or
`minimax_h3`.

### 3.14 Integration and continuity
**Across clips.** Extract the last frame (`atp.py last-frame --video <clip> --out <handoff.png>`), upload it as the next `start_image`
(`media_upload` → PUT → `media_confirm`) [HF contract]. Keep lighting and camera wording identical across a sequence
[INFERRED].

**Inserted assets.** Only via the start frame. Keep handling to one simple grip and one movement ("lifts the bottle
with her right hand around its neck, label toward camera, and sets it back at the table edge"); the partner reports
that "hands lose geometry" as prompts grow [SECONDARY], so short sentences beat detailed choreography [INFERRED].

**Scene light on the asset.** Reuse the official preservation wording: "maintaining … the realistic cinematic lighting
from the original image" [OFFICIAL]; name reflections or shadows only for the moving object [INFERRED].

**Background life.** The official i2v example keeps the scene alive without new subjects: "In the background, other
passengers and the trains should have subtle, natural movements" [OFFICIAL] — use this to avoid frozen or dead
backgrounds.

**Persistent states.** One end-state sentence ("the cup stays on the table, half full") [INFERRED].

**Known failures (partner observations).** Faces toward "a generic average", hands losing geometry, flattened gait with
long prompts; multi-step compression; wardrobe drift in fast action; ignored slow-motion cues [SECONDARY]. Slop
prevention: §5.

## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach
First-party examples exist (API references and Alibaba's campaign page), but no first-party prompt guide:

1. Text-to-video — HappyHorse text-to-video API reference, https://www.alibabacloud.com/help/en/model-studio/happyhorse-text-to-video-api-reference
   > "A miniature city built from cardboard and bottle caps comes to life at night. A cardboard train slowly passes
   > through, with small lights dotting the scene and illuminating the way ahead."
2. Image-to-video — HappyHorse image-to-video API reference, https://www.alibabacloud.com/help/en/model-studio/happyhorse-image-to-video-api-reference
   > "A cat running on the grass"
3. Image-to-video with dialogue — Alibaba Cloud Happy Horse-1.1 campaign page, https://www.alibabacloud.com/en/campaign/happyhorse-video
   > "The cute teddy bear as it briskly walks forward across the train station platform, pulling its brown suitcase
   > behind it with a sense of urgency. The bear's mouth moves in perfect lip-sync as it hurriedly says: 'There's no
   > time left, I'm going to be late!' Its expression should appear anxious and determined. In the background, other
   > passengers and the trains should have subtle, natural movements to reflect a busy station atmosphere. The camera
   > follows the bear with a smooth forward tracking shot, maintaining its soft, fuzzy texture and the realistic
   > cinematic lighting from the original image."
4. Text-to-video with a style change — same page
   > "A girl is dancing gracefully. As she spins around in a full turn, the entire scene seamlessly transforms from a
   > cartoon style into a realistic live-action setting."
5. Sequencing (reference mode, not exposed on Higgsfield) — HappyHorse reference-to-video API reference, https://www.alibabacloud.com/help/en/model-studio/happyhorse-reference-to-video-api-reference
   > "A woman in a red qipao from [Image 1] is first shown in a profile medium shot, highlighting the tailored cut and
   > S-curve of the dress. The camera then switches to a low-angle shot, […]"

Closest supporting guidance (API partner, [SECONDARY]): "[Subject] [does action] in [setting], [time of day], [one
atmosphere or camera cue]."

Patterns they teach:
- **Order:** subject + action with manner → dialogue with lip-sync and expression → background activity → camera move
  → preservation of texture and lighting (3).
- **Sentence style:** plain declarative prose, one idea per sentence; pace words ("slowly", "briskly") (1, 3).
- **Subject vs camera:** the camera gets its own final sentence (3); partner guidance agrees the last position carries
  the most weight [SECONDARY].
- **Temporal markers:** "As she…", "first… then" rather than timecodes (4, 5).
- **Dialogue:** "<subject>'s mouth moves in perfect lip-sync as it says: '…'" plus an expression sentence (3).
- **Length:** 5–95 words; image-to-video can be minimal (2). **Exclusions:** none in any official example.

### 4.1 Text-to-video
Follows patterns: subject + paced action → setting/light → background activity → sound → clean-plate clause → camera last.
```text
<Subject with 2–4 traits> <one action with manner/pace> in <setting>, <time of day / light>. In the background, <subtle natural movement>. <Sound: what is audible | no music>. No text, captions, logos or watermarks. <One camera move>.
```
Worked example (5 s, 9:16, 720p): "An elderly man in a grey wool coat feeds pigeons on a park bench, scattering seeds with
slow, steady tosses, late-afternoon golden light. In the background, a few people walk slowly along the path. Sound:
soft wing flaps and distant traffic, no music. No text, captions, logos or watermarks. Slow dolly-in from a medium
shot."

### 4.2 Start frame (and end frame) to video
Follows patterns: action with pace → dialogue/expression → background → camera → preservation clause.
```text
The <subject> <action from the frame's exact state, with pace>, <expression/secondary motion>. In the background, <subtle natural movement>. <Sound / dialogue: mouth moves in lip-sync as it says: "…" | no dialogue, no music>. The camera <one move>, maintaining the look and the lighting from the original image. No text, captions or watermarks.
```
Worked example (6 s, 9:16 `start_image` = a cyclist stopped at a crossing): "The cyclist pushes off and pedals steadily
across the street, glancing left once, jacket rippling in the wind. In the background, cars idle at the light. Sound:
bicycle chain and city ambience, no dialogue, no music. The camera follows with a smooth side tracking shot,
maintaining the look and the lighting from the original image. No text, captions or watermarks."

### 4.3 Reference-to-video
N/A on Higgsfield — `happy_horse_video` exposes only `start_image` [HF].

### 4.4 Video edit / extension / motion transfer
N/A on Higgsfield. Upstream `happyhorse-1.0-video-edit` exists but is not exposed [OFFICIAL/HF].

## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Corner watermark | upstream default `watermark:true` [OFFICIAL] | QC per §3.11e; reject and switch model |
| Generic faces, broken hands | long, over-detailed prompts [SECONDARY] | 20–60 words, one action |
| Steps merged into one motion | multi-step prose [SECONDARY] | one beat per clip or a short timecoded list |
| Wardrobe drift | fast action [SECONDARY] | slower action; shorter clips |
| Unwanted music or voices | audio always on [OFFICIAL] | describe audible sounds; "no music", "no dialogue" |
| Text or gibberish | text-bearing scenes or frames | §3.11 |
| Wrong format with start frame | frame not 9:16 [OFFICIAL] | 9:16 frames only (§2.6) |
| Weak camera adherence | camera cue buried mid-prompt [SECONDARY] | one camera cue last |

**AI-slop tendencies and prevention.** `atp.py qc` flags black and frozen spans; `atp.py trim` removes dead head/tail frames deterministically.

| slop tendency | prevention |
|---|---|
| Dead space / frozen background | 3–6 s for single actions; "subtle, natural movements" in the background [OFFICIAL example / INFERRED] |
| Arbitrary slow motion | don't request it (cues are unreliable) [SECONDARY]; "at real-time speed" [INFERRED] |
| Sudden speed changes | one action with one stated pace ("briskly", "slowly") [OFFICIAL style] |
| Unmotivated cuts / transitions | "one continuous shot"; timecodes only when cuts are wanted [INFERRED/SECONDARY] |
| Morphing | avoid "transforms/morphs" wording (official examples use it deliberately) [OFFICIAL/INFERRED] |
| Identity drift | short prompt, clear start frame [SECONDARY] |
| Duplicated objects | "only one <object>" [INFERRED] |
| Clothing changes | slower action; "clothing unchanged" [SECONDARY/INFERRED] |

## 6. Model-specific features and controls
- Joint audio-video generation; lip-sync dialogue from quoted lines [OFFICIAL example/SECONDARY].
- Single start-frame animation; 3–15 s; 720p/1080p [HF].
- Upstream-only (not exposed): 480P (1.1), extra ratios (4:5, 5:4, 9:21, 21:9 in the t2v reference), reference-to-video
  with "[Image N]" tags, video editing, seed, watermark switch [OFFICIAL].

## 7. Model-specific pre-generation checklist
- [ ] `aspect_ratio:"9:16"`, `resolution:"720p"`; start frame exactly 9:16 and text-free; `atp.py conform` (§2.6).
- [ ] Prompt 20–60 words: subject, one paced action, setting/light, background movement, sound, camera cue last.
- [ ] Dialogue with lip-sync wording or "no dialogue"; "no music" if needed.
- [ ] One clean-plate clause; captions/hooks planned for post (`atp.py captions`); no Edit Mode on this model.
- [ ] Grip, light and end states (§3.14); slop guards (§5); `get_cost: true`.
- [ ] First output of the session through `atp.py qc --mode analyze` for the provider watermark (§3.11e).

## 8. Sources
- [OFFICIAL] HappyHorse text-to-video API reference (watermark default, ratios, durations) — https://www.alibabacloud.com/help/en/model-studio/happyhorse-text-to-video-api-reference (accessed 2026-09-30)
- [OFFICIAL] HappyHorse image-to-video (first frame) API reference — https://www.alibabacloud.com/help/en/model-studio/happyhorse-image-to-video-api-reference (accessed 2026-09-30)
- [OFFICIAL] HappyHorse reference-to-video API reference (not exposed on Higgsfield) — https://www.alibabacloud.com/help/en/model-studio/happyhorse-reference-to-video-api-reference (accessed 2026-09-30)
- [OFFICIAL] happyhorse-1.0-i2v model page — https://www.alibabacloud.com/help/en/model-studio/happyhorse-1-0-i2v (accessed 2026-09-30)
- [OFFICIAL] Video generation and editing (HappyHorse 1.0/1.1 specs, recommendations) — https://www.alibabacloud.com/help/en/model-studio/use-video-generation (accessed 2026-09-30)
- [OFFICIAL] HappyHorse Gets Stronger Motion Expressiveness, Higher Generation Consistency, and Enhanced Visual Quality (2026-06-23) — https://www.alibabacloud.com/blog/happyhorse-gets-stronger-motion-expressiveness-higher-generation-consistency-and-enhanced-visual-quality_603293 (accessed 2026-09-30)
- [OFFICIAL] Happy Horse-1.1 campaign page (first-party example prompts) — https://www.alibabacloud.com/en/campaign/happyhorse-video (accessed 2026-09-30)
- [OFFICIAL] HappyHorse official site — https://happyhorse.com (accessed 2026-09-30)
- [HF] Higgsfield catalog snapshot — higgsfield/catalog-snapshot-2026-09-30.json; MCP tool contract facts supplied with this task
- [SECONDARY] Caixin Global, "Alibaba Unveils HappyHorse After AI Model Tops Video Rankings Under Alias" (2026-04-10) — https://www.caixinglobal.com/2026-04-10/alibaba-unveils-happyhorse-after-ai-model-tops-video-rankings-under-alias-102432775.html (accessed 2026-09-30)
- [SECONDARY] Artificial Analysis text-to-video / image-to-video leaderboards (creator "Alibaba-ATH") — https://artificialanalysis.ai/video/leaderboard/text-to-video ; https://artificialanalysis.ai/video/leaderboard/image-to-video (accessed 2026-09-30)
- [SECONDARY] fal (official API partner): HappyHorse model page — https://fal.ai/happyhorse ; "Happy Horse 1.0: what do we know so far" — https://fal.ai/learn/devs/happyhorse-1-0-what-do-we-know-so-far ; Prompting guide — https://fal.ai/learn/tools/prompting-happy-horse ; "How to use Happy Horse 1.1" — https://fal.ai/learn/tools/how-to-use-happy-horse-1-1 (accessed 2026-09-30)
- [SECONDARY] Magnific API docs, Happy Horse 1.0 (720P = 1280×720) — https://docs.magnific.com/api-reference/text-to-video/happy-horse-1/overview (accessed 2026-09-30)
- [SECONDARY] Atlas Cloud, "HappyHorse-1.0 Takes First Place, API Coming Soon" (open-source claims; conflicts with fal) — https://www.atlascloud.ai/blog/guides/happyHorse-hits-1-api-coming-soon (accessed 2026-09-30)

## 9. Open questions / unverified behaviour
- Whether Higgsfield disables the upstream default watermark (the key QC question).
- Whether Higgsfield serves HappyHorse 1.0 or 1.1; exact 9:16 pixel size at 720P.
- Whether `aspect_ratio` is ignored or rejected with `start_image`.
- Whether timecoded multi-beat prompts work reliably (partner claim only).
- Open-weight status (conflicting reports) and exact team attribution inside Alibaba.
