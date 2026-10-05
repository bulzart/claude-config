---
guide: kling-3-0-omni-edit
title: Kuaishou Kling 3.0 Omni Edit
provider: Kuaishou — Kling AI, served by Higgsfield
higgsfield_model_ids: [kling_video_edit]
guide_version: 1.0
last_verified: 2026-09-30
catalog_snapshot: higgsfield/catalog-snapshot-2026-09-30.json
documentation_depth: medium
---

# Kuaishou Kling 3.0 Omni Edit — model engineering guide

> Scope: the editing side of Kling VIDEO 3.0 Omni as served by Higgsfield under `kling_video_edit`
> ("Kling 3.0 Omni Edit — Edit a source video with text instructions and optional reference images").
> One source video plus up to four reference images and a text instruction produce an edited clip that
> keeps the source's framing and timing: add, remove (including burned-in text), replace subjects, change
> background, local modifications, restyle, recolour, weather/time changes, camera-angle variants,
> green-screen keying. Generation features (text-to-video, multi-shot, native audio) are out of scope.
> Project output format is fixed: vertical 9:16 at 720p (§2.6).
> The live `models_explore` catalog always wins over the parameter tables in this file.
>
> Evidence tags: **[OFFICIAL]** provider docs, paper, model card, API reference, first-party prompt
> guide or first-party examples · **[HF]** Higgsfield catalog, MCP tool contract or first-party
> Higgsfield docs · **[SECONDARY]** reputable third-party testing or articles · **[INFERRED]**
> engineering inference that must be verified in use. Source keys (S1…) point to §8.

## 1. At a glance

- **Positioning.** Kling VIDEO 3.0 Omni (launched 2026-02-06 [OFFICIAL S15]): "the Kling VIDEO O1 model has been upgraded to VIDEO 3.0 Omni", and "The video editing, prompt transformation, and other features in 3.0 Omni function the same as in O1." [OFFICIAL S1]. For post-production Kling says users can "Input natural language like 'remove the bystanders in the background', or 'make the sky blue', and the model will use deep semantic understanding to automatically complete pixel-level adjustments" [OFFICIAL S2]. A June 2026 upgrade reportedly extended Omni editing to 3–15 s and 4K input/output with better source consistency [SECONDARY S9].
- **Best for:** one or two clear operations on a short clip that must keep its motion and camera: product/object swap from a reference image, background replacement, removal of distractions or burned-in text, recolouring, style transfer, weather/time changes, a new angle of the same action, green-screen extraction [OFFICIAL S2].
- **Weaker at / unknown:** no duration, audio or ratio controls on Higgsfield [HF S3]; short sources ("between 3s and 10s") [OFFICIAL S1]; ≤4 reference images with a video [OFFICIAL S1]; native audio "Not Supported Yet" with video input [OFFICIAL S1]; tag binding on Higgsfield undocumented (§2.5); no timestamp scoping documented.
- **Choose this model when** the edit is simple, the source is ≤10 s, and you want Kling's look.
- **Choose another model when** the source is 10–30 s or needs timestamp-scoped operations, more than four images, audio edits or dubbing (Seedance 2.5 `video_edit` under Higgsfield's edit contract), or a pure one-object swap that must pass source audio and untouched pixels through (Genjutsu `hf_mult_replace_object`) [HF S6].

| operation | how to invoke on Higgsfield | notes |
|---|---|---|
| Instruction edit (add / remove / modify / background / style / weather / angle / green screen) | `model:"kling_video_edit"`, one `video_references` item | output follows the source's ratio and length [HF S3, S4] |
| Reference-guided edit | same + up to 4 `image_references` | "When a video is provided, a total of up to 4 images/elements can be uploaded." [OFFICIAL S1] |
| Generation, multi-shot, next/previous shot, motion reference | N/A on this id | Omni generation modes are not exposed as `kling_video_edit` |

## 2. Higgsfield parameter surface

### 2.1 Parameters per model id

| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `kling_video_edit` | `mode` | `std`, `pro`, `4k` | `pro` | "Output quality: Standard, Pro, or 4K." [HF S3]. Project: `std` (§2.6). |
| `kling_video_edit` | `aspect_ratio` | none (empty list) | — | Output follows the source [HF S3; INFERRED]. |
| `kling_video_edit` | `duration` | none | — | Output follows the source length ("duration matches source range") [HF S4]; API mirrors: duration ignored in base editing [SECONDARY S10]. |
| `kling_video_edit` | audio | none | — | Native audio "Not Supported Yet" with video input [OFFICIAL S1]; Kling's API has a keep-original-sound option and a mirror defaults `keep_audio:true` [SECONDARY S10, S11]; restore the source audio locally (§2.5). |
| `kling_video_edit` | `negative_prompt`, `cfg_scale`, `keep_original_sound`, `refer_type` (base/feature), elements, seed | — | — | **Not exposed on Higgsfield** [HF S3]. Kling's API separates a "base" video to edit from a "feature" video used as style/camera reference [SECONDARY S10]; this id is edit-only. Write preservation and exclusions in the prompt (§3.10). |

Call-level keys: `model`, `prompt`, `medias`, `get_cost` (preflight, submits nothing) [HF S6].

### 2.2 Media roles

| role | what it controls | limits / count | notes |
|---|---|---|---|
| `video_references` | the source clip to edit (`@Video1`) | exactly 1: "You can upload one video with a duration between 3s and 10s, file size ≤ 200MB, and resolution ≤ 2k." [OFFICIAL S1]; June 2026 upgrade: 3–15 s, 4K input [SECONDARY S9] | send it first in `medias` [INFERRED] |
| `image_references` | replacement subject/product, background, style or colour source (`@Image1…4`) | ≤4 with a video; each ≥300 px, ≤10 MB, jpg/jpeg/png [OFFICIAL S1, S2] | in `@Image` order after the video |

`medias[].value` is a media UUID or completed job id, never a URL; local files arrive via `media_upload` → HTTP PUT → `media_confirm`, and finished clips return as public MP4 URLs via `jobs_wait` [HF S6]. Server-side role coercion applies when unambiguous [HF S6].

### 2.3 Duration, resolution, aspect ratio, audio

- **Duration:** follows the source [HF S4]; keep sources 3–10 s unless a test confirms the upgraded 3–15 s range on Higgsfield [OFFICIAL S1; HF S5; SECONDARY S9]. Split longer sources on hard cuts.
- **Resolution:** `std` / `pro` / `4k` output tiers [HF S3]; Higgsfield's help centre still lists Omni Edit at 1080p max while the catalog offers `4k` [HF S5, S3].
- **Aspect ratio:** follows the source [HF S3].
- **Audio:** treat returned audio as untrusted; strip it and restore the source's own track locally, conformed to the source duration (Higgsfield's own practice for Seedance edits) [OFFICIAL S1; HF S8; INFERRED].
- **Billing basis:** undocumented — preflight with `get_cost:true` [HF S6].

### 2.4 Call recipes

Source reframed to 9:16 before upload (§2.6). Add `"get_cost": true` to preflight.

**Instruction-only edit**
```json
{"model":"kling_video_edit","prompt":"<EDIT INSTRUCTION citing @Video1>","medias":[{"value":"<VIDEO_MEDIA_ID>","role":"video_references"}],"mode":"std"}
```
**Reference-guided edit (source first, then up to four images)**
```json
{"model":"kling_video_edit","prompt":"<EDIT INSTRUCTION citing @Video1 and @Image1..@Image2>","medias":[{"value":"<VIDEO_MEDIA_ID>","role":"video_references"},{"value":"<IMAGE_MEDIA_ID_1>","role":"image_references"},{"value":"<IMAGE_MEDIA_ID_2>","role":"image_references"}],"mode":"std"}
```
**Two-pass clean-up: text removal first, content edit second** (the second call uses the first call's completed job id as its source) [INFERRED]
```json
{"model":"kling_video_edit","prompt":"<REMOVE-ONLY INSTRUCTION>","medias":[{"value":"<VIDEO_MEDIA_ID>","role":"video_references"}],"mode":"std"}
```
```json
{"model":"kling_video_edit","prompt":"<CONTENT EDIT citing @Video1 and @Image1>","medias":[{"value":"<JOB_ID>","role":"video_references"},{"value":"<IMAGE_MEDIA_ID_1>","role":"image_references"}],"mode":"std"}
```

### 2.5 Parameter gotchas

- **Tag binding is undocumented on Higgsfield.** Kling's guide writes `[@Video]`, `[@Image1]`, `[@Element]` [OFFICIAL S2]; API mirrors use `@Video1`/`@Image1`/`@Element1` [SECONDARY S11] or `<<<image_1>>>` [SECONDARY S12]; Higgsfield normalises `@Image` tags server-side for Seedance [HF S8]. Write `@Video1` and `@Image1…@Image4` in `medias` order **and** describe every target in words [INFERRED].
- No `duration` or `aspect_ratio` parameters — do not send them [HF S3]. Four images maximum [OFFICIAL S1].
- Elements are documented for `kling3_0`, not this id [HF S6]; use `image_references`.
- Source ≤200 MB and ≤2K (transcode 4K phone footage) unless 4K input is confirmed [OFFICIAL S1; SECONDARY S9].
- Using a completed job id as the next call's source is supported by the MCP contract [HF S6]; whether Higgsfield accepts a video job id for `video_references` on this id is untested.
- Kling's API caps prompts at 2,500 characters [SECONDARY S13]; keep edit prompts short.

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-pick)

| step | what to do | expected output | post-processing |
|---|---|---|---|
| before upload | reframe the source to 9:16 at 720×1280 with `atp.py conform` (scale-to-fill + minimal crop; never stretch); keep 3–10 s | — | — |
| edit call | `mode:"std"` (Kling's standard tier ≈ 720p) [SECONDARY S16; INFERRED for the edit model] | follows the source ratio → 720×1280 expected [INFERRED] | ffprobe; if the short edge is not 720 or the ratio drifted, `atp.py conform`; conform duration to the source; restore source audio |

A non-9:16 source whose important content would be cropped away is better re-created in Analyze Mode with a generation model than edited [INFERRED].

## 3. How the model reads a prompt

### 3.1 Recommended prompt structure (ordered elements, formula, length, language, prose vs. lists)

- Kling edit prompts are **short imperative sentences** built on fixed structures (O1 guide, followed by 3.0 Omni) — see §4.0 [OFFICIAL S1, S2].
- Tasks can be combined in one prompt ("adding a subject while modifying the background") [OFFICIAL S2]; keep one or two operations per call and chain passes for more [INFERRED].
- Always state what stays: "Change [Target Subject] in [Video] to [New State], keep everything else unchanged" (Higgsfield's O1 formula) [HF S4].
- Order for this project: operation sentence(s) → attribute binding per `@Image` → integration line (size, grip, light) → preservation sentence → "No new text" line [INFERRED]. 1–5 sentences, ≤2,500 characters.

### 3.2 Subject and identity

- Name each source target by visible, unique cues: position, clothing colour, action ("the man in the blue jacket on the left who opens the door") [INFERRED].
- Person replacement: "Change [the person as seen] in @Video1 to the person from @Image1" [OFFICIAL S2 structure], plus a complete-look and exclusion sentence adapted from Higgsfield's Seedance contract: "The original person must not appear in any frame, including reflections and brief entrances or exits; the replacement takes face, hair, body, clothing and accessories from @Image1 and keeps only the original performance, pose, blocking and timing." [HF S8 pattern; INFERRED for Kling]. Map each person separately [HF S8 pattern].

### 3.3 Action, motion and physical interaction

- The edit inherits source motion; don't re-describe it unless it must change [INFERRED].
- For different-sized replacements, specify grip and size ("same grip and finger positions; real-world size fits in one hand") and consequences (a darker liquid, heavier object, new reflections) [INFERRED].

### 3.4 Environment, lighting and style

- Background replacement changes what is behind the subject; say whether the subject is relit ("relight the person to match warm sunset light") or keeps its light [INFERRED].
- Named style presets: American cartoon, Japanese anime, cyberpunk, pixel art, ink wash painting, watercolour, clay, figure style, Monet-inspired, wool felt; or "the style of [@Image1]" [OFFICIAL S2].
- Kling's guide does not state what an edit leaves unchanged; say it explicitly every time [OFFICIAL S2 silent; HF S4].

### 3.5 Chronology, timing and multi-shot structure

- No timestamp scoping is documented; instructions apply to the whole clip [OFFICIAL S2 silent; INFERRED]. For a partial change, trim the source locally to that part, edit, and re-assemble.
- Multi-shot sources: split on hard cuts into separate 3–10 s edits with identical references and wording [INFERRED].

### 3.6 Camera language and dedicated camera / motion controls

- Camera moves are inherited; no camera control [HF S3]. "Generate [another angle/composition] in [@Video]" regenerates a new viewpoint of the same action (close-up, wide shot) [OFFICIAL S2] — check continuity carefully.

### 3.7 References (image / video / audio): syntax, roles, what is inherited and what must be excluded

- `@Video1` = source master; `@Image1…4` = targets in `medias` order [INFERRED]. Say which attribute each image supplies and what to ignore ("the bottle's shape, colours and label from @Image1; ignore its background and the hand holding it") [INFERRED; mirrors Kling's "from [@Image]" structures S2].
- Kling's app builds multi-angle elements from "up to 4 images" [OFFICIAL S1, S2]; on Higgsfield, pass up to four views of the same object as images and state they show one object [INFERRED]. No audio references [HF S3].

### 3.8 Start and end frames

N/A on Higgsfield for this id (edit-only; no frame roles) [HF S3].

### 3.9 Audio, dialogue and sound (if supported)

N/A: no audio control, and native audio is "Not Supported Yet" with video input [HF S3; OFFICIAL S1]. Restore the source track locally; add new SFX in post [INFERRED].

### 3.10 Negative constraints (is there a negative-prompt field on Higgsfield? how to phrase exclusions)

- No negative-prompt field on Higgsfield [HF S3] (Kling's API/app have one [SECONDARY S13; OFFICIAL S14]).
- Use preservation sentences rather than long negative lists: "Keep everything else in @Video1 unchanged: people, objects, camera movement, lighting, timing." Add one short exclusion line for known risks ("no extra objects, no duplicated hands, no new text") [INFERRED].

### 3.11 Visible text

Policy: **Edit Mode** removes all source text unless the user keeps specific text; **Analyze Mode** may add intentional new text, by default in deterministic post (FFmpeg/libass); reference wording, usernames and watermarks are never copied.

- **(a) Reliability / tendency:** Kling 3.0 is built to *keep* text: it "can automatically identify text content in uploaded images (such as signs, captions, or logos) and maintain text consistency" [OFFICIAL S7]. Expect untargeted source text to survive an edit, and replaced objects to acquire plausible-looking text unless told otherwise [INFERRED].
- **(b) Clean result:** end every edit with "No new text, subtitles, logos or watermarks appear." [INFERRED]; approved product-label text is the only permitted text and is named explicitly ("the label printed on the bottle from @Image1 stays exactly as in the reference") [INFERRED].
- **(c) Intentional text:** not added through edits in this project; captions and callouts go to post. Kling's "Add [describe content] to [@Video]" structure is not documented for text [OFFICIAL S2 silent].
- **(d) Removing source text:** use Kling's official remove structure "Remove [describe content] from [@Video]" [OFFICIAL S2] phrased like Higgsfield's first-party remove template — "Remove only [target] from @Video1 and reconstruct the revealed area consistently with its immediate surroundings" [HF S8] — naming every element with position and time: captions, subtitles, usernames/handles, watermarks, title cards, meme text, stickers, social overlays, UI elements, timestamps, overlay logos, random lettering. Do **not** add Higgsfield's "Preserve every caption…" block (a Seedance-contract default this project overrides) [HF S8]. Prefer a removal-only pass first (§2.4 two-pass recipe). When text covers faces, hands or the product, spans most of the frame (title cards), or animates heavily, trim that segment locally or re-create the shot in Analyze Mode instead; local blur/inpaint is a last resort [INFERRED].

### 3.12 Character / identity consistency

- One clean, front-facing image per replacement person (a second angle if slots allow); keep the source person's face out of references [INFERRED].
- The replacement covers every appearance, including reflections and brief exits/entrances — say so [HF S8 pattern]. Avoid replacing a speaking person unless lip mismatch is acceptable (audio is not regenerated) [INFERRED].

### 3.13 Product and object fidelity (geometry, proportions, labels, scale, handling)

- "Change the [object as seen, with position and hand] in @Video1 to the [product] from @Image1 (front) and @Image2 (side view of the same object); it is one rigid object with exactly the shape, proportions, colours and label of the references, held with the same grip, following the same motion." [OFFICIAL S2 structure; INFERRED wording]
- Prefer replacements of similar size and form factor, or accept regenerated hands [INFERRED].

### 3.14 Integration and continuity (scale, orientation, contact, grip, occlusion, scene-light inheritance, reflections, shadows, persistent object states across the timeline)

- **Scale / orientation / grip / occlusion:** "at the size of the original can, upright, label toward the camera, held with the same four-finger grip; the thumb covers the lower label edge as the original did; the hand still passes in front of it at the same moments" [INFERRED].
- **Scene light:** "lit by the scene's warm window light from the left like the original object; soft shadow to the right on the table; the glossy surface reflects the window" — and exclude product-photo lighting ("ignore the studio lighting of @Image1") [INFERRED].
- **Persistent states:** state constants the edit must not disturb ("the cup stays on the right edge of the table; the drawer stays closed; the liquid level in the glass stays as in @Video1") [INFERRED].
- **Known failures:** undocumented officially; expect hand deformation with size mismatches, identity drift in fast motion, and re-rendered text on replaced objects [INFERRED].
- **Across segments:** identical images, order, wording and `mode`; after the first approved segment, add a frame of the edited product as an extra image (within the four-image cap); conform each output to its source duration and restore the original audio once over the joined timeline [INFERRED; HF S8 practice].

## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach

Kling publishes **edit structures**, not full edit example prompts; the closest first-party material is quoted below (all verbatim from the KLING VIDEO O1 User Guide, S2, which 3.0 Omni follows per S1, unless labelled).

- **E1 — add:** "Add [describe content] to [@Video]" · "Add [describe content] from [@Image] to [@Video]"
- **E2 — remove:** "Remove [describe content] from [@Video]"
- **E3 — modify subject:** "Change [specified subject] in [@Video] to [target subject] from [@Image]"
- **E4 — background:** "Change the background in [@Video] with [@Image]"
- **E5 — restyle / recolour / weather:** "Change [@Video] to the style of [@Image1]" · "Change the [item] in [@Video] to [color]" · "Change [@Video] to [describe weather, like 'a rainy day']"
- **E6 — camera angle / green screen:** "Generate [another angle/composition, e.g., close-up, wide shot] in [@Video]" · "Change the background in [@Video] to a green screen, and keep [describe content]"
- **E7 — natural-language post-production (S2):** "Input natural language like 'remove the bystanders in the background', or 'make the sky blue', and the model will use deep semantic understanding to automatically complete pixel-level adjustments."
- **E8 — [HF] Higgsfield formula (S4):** "Change [Target Subject] in [Video] to [New State], keep everything else unchanged" · **[SECONDARY] fal example (S11):** "Change environment to be fully snow as @Image1. Replace animal with @Element1"

Patterns these teach [derived from E1–E8]:
- **Sentence style:** one imperative verb per operation (Add / Remove / Change / Generate), target first, source asset last ("… from [@Image]").
- **Reference syntax:** the source video is always named (`[@Video]`); images are bound with "from [@Image]" or "the style of [@Image1]".
- **Detail level:** short, specific targets ("the bystanders in the background", "the sky"); no timing language.
- **Preservation:** stated explicitly ("keep everything else unchanged", "and keep [describe content]").
- **Length:** one sentence per operation; operations can be concatenated (E8).
- **Exclusions:** not used in official material; this project adds "No new text…" (§3.11).

### 4.1 Text-to-video

N/A on Higgsfield — `kling_video_edit` is edit-only [HF S3]. Use `kling3_0`.

### 4.2 Start frame (and end frame) to video

N/A on Higgsfield — no frame roles on this id [HF S3].

### 4.3 Reference-to-video

N/A as a generation mode; reference images are used only inside edits (§4.4) [HF S3].

### 4.4 Video edit / extension / motion transfer (only if supported)

**Replace (product or object)** — follows E3 + E8:
```text
Change the <object as seen: colour, position, which hand holds it> in @Video1 to the <product> from @Image1 (front) and @Image2 (side view of the same object). It is one rigid object with exactly the shape, proportions, colours and materials of the references, at <size relative to the hand>, held with the same grip and following the same motion; lit by the scene's <light direction and colour> with its shadow <direction>; ignore the backgrounds and lighting of @Image1 and @Image2. Keep everything else in @Video1 unchanged: <person, face, hands, clothing>, all other objects, camera movement, lighting and timing. No new text, subtitles, logos or watermarks appear; one <product> only.
```
Worked example:
```text
Change the green glass bottle in the woman's right hand in @Video1 to the matte white insulated bottle from @Image1 (front) and @Image2 (side view of the same bottle). It is one rigid bottle with exactly the shape, proportions and colours of the references, the same height as the original bottle, held with the same grip and following the same motion; lit by the warm window light from the left with its shadow on the right; ignore the backgrounds and lighting of @Image1 and @Image2. Keep everything else in @Video1 unchanged: the woman, her face, hands and clothing, the kitchen, the camera movement, lighting and timing. No new text, subtitles, logos or watermarks appear; one bottle only.
```

**Remove source text (Edit Mode default, first pass)** — follows E2 + Higgsfield's remove wording:
```text
Remove only <each text element with position and time> from @Video1 and reconstruct the revealed area consistently with its immediate surroundings. Keep everything else in @Video1 unchanged. No new text, subtitles, logos or watermarks appear.
```
Worked example:
```text
Remove only the burned-in subtitles along the bottom, the username in the lower-left corner, the sticker with lettering at the top right and the small watermark in the top-right corner from @Video1 and reconstruct the revealed areas consistently with their immediate surroundings. Keep everything else in @Video1 unchanged. No new text, subtitles, logos or watermarks appear.
```

**Replace (person)** — follows E3:
```text
Change the <person as seen> in @Video1 to the person from @Image1. The original person must not appear in any frame, including reflections and brief entrances or exits; the replacement takes face, hair, body, clothing and accessories from @Image1 and keeps only the original performance, pose, blocking and timing. Keep all other people, objects, the setting, camera movement, lighting and timing unchanged. No new text, subtitles, logos or watermarks appear.
```

**Background / environment** — follows E4:
```text
Change the background in @Video1 to <setting> (or: with @Image1). Keep the <subject> and all foreground objects, their motion, the camera movement and timing unchanged; relight the subject to match <light> (or: keep the original lighting). No text or signage appears in the new background.
```

**Restyle / recolour / weather / angle** (one per call) — E5, E6:
```text
Change @Video1 to <style> style. Keep the composition, motion and timing unchanged. No text appears.
Change the <item> in @Video1 to <color>. Keep everything else unchanged.
Change @Video1 to <weather or time of day>. Keep people, objects, camera and timing unchanged.
Generate a <close-up | wide shot> of the same action in @Video1. Keep identities, objects and timing consistent.
```

**Extension / motion transfer:** N/A on this id. Kling's "Based on [@Video], generate the next shot" and "Animate the character in [@Image 1] with the same motion as the character in [@Video]" are Omni generation features [OFFICIAL S2] not exposed via `kling_video_edit`; use `kling3_0` chaining, the legacy `motion_control` tool, Seedance 2.5 `video_extension`, or Genjutsu `hf_mult_motion_control` [HF S6].

## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Untargeted captions/watermarks survive | text not named; Kling preserves detected text | name every element in a remove sentence; removal-only pass first [OFFICIAL S2, S7; INFERRED] |
| Replaced object gains pseudo-text | text-free instruction missing | "No new text…"; name the only permitted label [INFERRED] |
| Reference background or lighting bleeds in | unscoped `@Image` | "ignore the background and lighting of @Image1"; crop references [INFERRED] |
| Wrong object replaced | ambiguous target | position + colour + hand + action [INFERRED] |
| Original person visible in a reflection or later | replacement scoped to one moment | "must not appear in any frame" sentence [HF S8 pattern] |
| **Morphing** of the replacement | size/form-factor mismatch, fast motion | similar-size replacement; "one rigid object"; grip and size stated [INFERRED] |
| **Identity drift** of a replaced person | single low-quality reference | clean front-facing image (+ second angle) [INFERRED] |
| **Duplicated objects** | "add" without count/position | exact count and placement [INFERRED] |
| **Clothing changes** on untouched people | broad style/background edits | preservation sentence naming untouched people and clothing [INFERRED] |
| **Flicker / unmotivated re-framing** | "Generate another angle" or restyle | one operation per call; QA; avoid angle regeneration for continuity-critical shots [OFFICIAL S2; INFERRED] |
| Output audio missing or altered | edits don't regenerate audio | restore source track locally [OFFICIAL S1; INFERRED] |
| Rejected or truncated source | >10 s, >200 MB, >2K | trim to 3–10 s on hard cuts; transcode ≤2K [OFFICIAL S1] |
| Tags not bound | Higgsfield tag handling unknown | describe targets in words as well [INFERRED] |

## 6. Model-specific features and controls

- Edit families (O1 lineage): add, remove, modify subject, background, local modification, restyle, recolour, weather/environment, camera angle/composition, green-screen keying, creative effects [OFFICIAL S2]; combined tasks in one instruction [OFFICIAL S2].
- `mode` std/pro/4k (project uses `std`); June 2026 upgrade: 4K input/output and 3–15 s editing [HF S3; SECONDARY S9].
- Not exposed: duration, ratio, audio, negative prompt, cfg, elements, base/feature reference type [HF S3].

## 7. Model-specific pre-generation checklist

- [ ] Source: one clip, 3–10 s, ≤200 MB, ≤2K, cut on hard cuts, reframed to 9:16 720×1280; text regions and times listed.
- [ ] `mode:"std"`; no `duration`/`aspect_ratio` sent.
- [ ] ≤4 reference images (≥300 px, ≤10 MB, jpg/png), cropped to the target, in citation order.
- [ ] Kling edit structures; `@Video1`/`@ImageN` plus plain-language targets; one or two operations per call.
- [ ] Every source text element named in a remove sentence (removal-only pass first if large); "No new text…" line; no Higgsfield preservation block.
- [ ] Integration line: size, grip, orientation, scene light, shadow; persistent states named.
- [ ] Person replacement has the exclusion sentence; product replacement states rigidity and size.
- [ ] `get_cost:true` preflight; post: ffprobe, conform ratio/duration, restore source audio, frame QA.

## 8. Sources

- S1 [OFFICIAL] Kling AI — Kling VIDEO 3.0 Omni Model User Guide ("the Kling VIDEO O1 model has been upgraded to VIDEO 3.0 Omni"; "The video editing, prompt transformation, and other features in 3.0 Omni function the same as in O1."; one video 3–10 s, ≤200MB, ≤2k; up to 4 images/elements with a video; native audio "Not Supported Yet" with video input) — https://kling.ai/quickstart/klingai-video-3-omni-model-user-guide (accessed 2026-09-30)
- S2 [OFFICIAL] Kling AI — KLING VIDEO O1 User Guide (edit structures E1–E6, post-production example E7, styles, combinations, next/previous shot, motion reference) — https://kling.ai/quickstart/klingai-video-o1-user-guide (accessed 2026-09-30)
- S3 [HF] Higgsfield live catalog snapshot — `higgsfield/catalog-snapshot-2026-09-30.json` (`kling_video_edit`)
- S4 [HF] Higgsfield blog — "Kling O1 is Here: A Complete Guide" (edit mode: 3–10 s source, up to 4 images, output duration matches source) — https://higgsfield.ai/blog/Kling-01-is-Here-A-Complete-Guide-to-Video-Model (accessed 2026-09-30); Higgsfield "Kling O1 prompt bank" formula (E8) — https://higgsfield.ai/blog/kling-O1-prompt-bank (search-index text 2026-09-30; direct fetch returned 404)
- S5 [HF] Higgsfield help centre — "How do I use Kling" (Omni Edit: 1080p, 3–10 s) — https://higgsfield.ai/creator-hub/help-center/ai-models/how-do-i-use-kling (accessed 2026-09-30)
- S6 [HF] Higgsfield MCP tool contract (call shape, `get_cost`, role coercion, job ids as media, `jobs_wait`, Elements scope, Genjutsu routing) as verified for /analyze-then-pick, 2026-09-30; `higgsfield/first-party/genjutsu.md`
- S7 [OFFICIAL] Kling AI — Kling VIDEO 3.0 Model User Guide (text preservation: "can automatically identify text content in uploaded images (such as signs, captions, or logos) and maintain text consistency") — https://kling.ai/quickstart/klingai-video-3-model-user-guide (accessed 2026-09-30)
- S8 [HF] Higgsfield Ad Multiplier prompt-writer and media-pipeline references (remove template, person-replacement exclusion, silent render + source-audio restore; the "Preserve every caption…" default this project overrides) — `higgsfield/first-party/ad-multiplier-prompt-writer.md`, `ad-multiplier-media-pipeline.md` (retrieved 2026-09-30); observed Seedance tag normalisation in `analyze-stack/research/higgsfield-mcp.md` (2026-09-16)
- S9 [SECONDARY] Atlas Cloud — "Kling 3.0 Omni Upgrade: 4K Editing, Longer Clips, More Consistency" (2026-06-17) — https://www.atlascloud.ai/blog/guides/kling-3-0-omni-upgrade (accessed 2026-09-30)
- S10 [SECONDARY] Kling API field descriptions via mirrors (reference type "base" vs "feature"; duration ignored in base editing; keep_original_sound) — https://skills.cat/skills/calesthio/openmontage/kling-official and search-index excerpts of Kling V3 Omni API docs (accessed 2026-09-30)
- S11 [SECONDARY] fal.ai — Kling O3 Edit Video (@Video1/@Image1/@Element1 syntax, 3–15 s, ≤4 images/elements, keep_audio default true, example E8) — https://fal.ai/models/fal-ai/kling-video/o3/pro/video-to-video/edit/llms.txt (accessed 2026-09-30)
- S12 [SECONDARY] CometAPI — Kling omni-video API mirror (`<<<image_1>>>` syntax) — https://apidoc.cometapi.com/api/video/kling/omni-video.md (accessed 2026-09-30)
- S13 [SECONDARY] Magnific — Kling V3 API overview (2,500-character prompt and negative-prompt limits) — https://docs.magnific.com/api-reference/video/kling-v3/overview (accessed 2026-09-30)
- S14 [OFFICIAL] Kling AI blog — "Kling AI Negative Prompts: Fix Video Distortion & Glitches" (2026-05-26) — https://kling.ai/blog/kling-ai-negative-prompts-fix-video-distortion (page body not retrievable; search-index content, 2026-09-30)
- S15 [OFFICIAL] Kling AI 3.0 launch press release (2026-02-06; "in-video editing"), via Bernama — https://www.bernama.com/en/news.php/?id=2520897 (accessed 2026-09-30)
- S16 [SECONDARY] muapi — "Kling 3.0 API Pricing — Standard, Pro, 4K & Omni Tiers" (Standard 720p, Pro 1080p) — https://muapi.ai/kling-3-pricing (search-index content, 2026-09-30)

## 9. Open questions / unverified behaviour

- How Higgsfield binds `@Video1` / `@ImageN` (or `[@Video]`) for this id and whether it rewrites them to Kling's `<<<…>>>` form.
- Accepted source length (3–10 s vs upgraded 3–15 s) and maximum input resolution on Higgsfield.
- Output dimensions for `std` with a 720×1280 source (720×1280 expected); billing basis.
- Whether the output carries source audio, silence or regenerated audio.
- Whether a video job id is accepted as the source of a second pass.
- Removal quality for large, moving or animated overlays, and whether timestamp phrases ("from 2-4 seconds") are honoured.
- Whether a fifth image is rejected or silently dropped.
