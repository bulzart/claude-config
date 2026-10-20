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

