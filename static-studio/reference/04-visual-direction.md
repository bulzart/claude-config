# 04 — Direct the image-led film, not a wallpaper slideshow

## Visual manifesto

The core format is **voice + still images and meaningful graphics edited into a YouTube long-form film**. It is neither silent reference-video recreation nor a sequence of generic prompts. Art and explanation are equal storytelling instruments. A good shot **answers, complicates, compares, humanizes, locates, foreshadows, contrasts or lets the viewer think**. Repeating the narrator's nouns with a random illustration is not enough.

Create `60-visuals/video-NN/style-bible.md` with: medium (documentary illustration, map/diagram, stylized paintings, clean product/tech renders as appropriate), palette, lighting, texture, character/prop/world identities, typography overlay rules, image composition grammar, historical or physical restrictions, and rule for factual photo vs invented illustration. Maintain visual continuity across an event: geography, facing direction, sunlight, military insignia, scale, tools, injury/damage state, attire, who holds which prop. Scenes cannot teleport silently. Change shot scale to earn perspective, not to fake energy.

For every beat, make a **visual argument sheet** `shot-plan.json`, each segment with ID, beat ID, approximate audio-linked start/end, frame prompt, composition, what NEW thing the viewer learns/feels from the picture, continuity anchors, whether diagram/map/callout/overlay is appropriate, how a visual idea evolves across adjacent shots, and whether it requires verified imagery. Look for these meaningful shot families:

- **Establish / orient:** clean geography, timeline, workspace, spatial relationship, scale or environment.
- **Decision / human:** the expression, hand movement, choice, consequence, ordinary object or lived limitation that makes an abstraction concrete.
- **Explain / compare:** diagram, overlay arrows added in CapCut, contrasting models, labelled relationship, map movement, before/after or cause/effect state.
- **Reveal / reframe:** deliberate change in perspective that creates an earned “oh, that's why” moment.
- **Breathe / reflect:** an evocative image held long enough for thought, rather than continuous informational strain.
- **Callback:** return to an earlier object/detail and visibly resolve or deepen it.

No requirement that every category appear every minute. A slow map animation is valuable when tracking route/constraints; decorative sparkle is not. Select the rhythm from comparable references in the same cluster, then adapt. A 14-minute thoughtful history film needn't cut at the rate of a TikTok Short.

## Static plus subtle motion (image-led, no forced video generation)

Allowed editing tools: modest Ken Burns movement, pans, reframing, layer masks, depth planes/parallax when achievable, wipe-on annotations and hand-drawn highlight, light temperature changes, overlays, comparison split screens, maps with moving pins, animated simple shapes and purposeful captions. Use CapCut for overlays and transitions where possible; don't bake normal subtitle text, motion arrows, social stickers or heavy VFX into generated base images merely because the model can. However **visible text is allowed when it is intrinsically part of the factual scene**, such as a label on an important document, signage, diagram or needed interface. Historic or scientific data graphics should be legible, accurately laid out and checked rather than trusting model-rendered gibberish.

Music/SFX create dimension but shouldn't erase room for a quiet moment. A sound cue should have a narrative job (recognition, scale, spatial setting, surprise, transition, or an emotional punctuation). Avoid constant sound effects, templates, forced whip pans and musical crescendos every chapter. Treat narration, illustration and music as one composition.

## Image prompt contract

Before creating an image, specify (a) exact beat/visual job, (b) scene and continuity anchors, (c) primary readable subject and visual hierarchy, (d) viewpoint/framing and reserved caption space, (e) texture, look and light, (f) physical and factual restrictions, (g) what must **not** appear, especially copied source overlays. Images should look like the **same film** even when topics/scenes vary; justified stylistic contrasts may be marked as such in the style bible. Verify every result with visual inspection: hands, objects, text, map boundaries, chronology, scale, logos, number of people, weapons/equipment accuracy where relevant, and whether the picture communicates the intended new idea.

For a niche with real historical artifacts/places/equipment, start by researching visual references and source provenance; either use licensed originals with attribution, or create a clearly illustrated interpretation based on grounded descriptions. Never turn model imagination into documentary evidence. For quantitative diagrams, prefer deterministic chart/map rendering over hallucinated numbers/labels.

## Engines (pick for each run; no other generation modes)

- **OpenAI Images API** (if the user's API credentials and endpoint permissions are configured): use `STUDIO/scripts/openai_images_worker.py --job <job.json>` with a list of `{id,prompt,file}` stills, model/quality/size, initially **without** `--execute` to inspect count and access, then **with** `--execute` only after approving cost. Current selectable model IDs include `gpt-image-2.5-flare` and `gpt-image-2.5-sunburst` (verify access and current API pricing). The worker saves image PNGs and resumable manifests, not the API key; this API generation path does not handle image edits/references and must not be falsely claimed to do so. For image-to-image, use a properly supported current provider API or local worker. Verify real outputs and continuity before the edit.
- **Local FLUX 3 Image Klein** (optional; existing ComfyUI setup): use `STUDIO/scripts/image_worker.py <job.json>` in the correct ComfyUI portable Python environment (`AWL_IMAGE_ROOT` and `AWL_IMAGE_PYTHON` may already be configured). It accepts `{"op":"generate", "images":[{"prompt":"...","out":"...png","width":1920,"height":1088,"seed":123,"steps":16,"upsample":true,"refs":[]}]}` as a starting structure; use dimensions divisible by 16 and use correct aspect/crop in CapCut. `{"op":"check"}` verifies local dependencies. This worker was preserved from the user's Static tooling, not an unrelated video generator.
- **User-supplied art:** write a complete prompt sheet, accept the new files, verify orientation/quality, then edit. A pre-existing reference video's frames are **never** silently repurposed as newly generated assets.

Optional music bed: `STUDIO/scripts/music_worker.py <job.json>` with user's existing ACE-Step 1.5 environment. It can create instrumental tracks; check first. Do not run locally if the engine/environment is absent. Other licensed music sources are acceptable with documented rights, but the command should not fabricate licenses.

## Long-form visual inventory and pacing

Prepare images/graphics for the **whole narration**, not just the opening. The number of stills depends on how much a shot changes, not an arbitrary seconds-per-image average. Some 20-second explanatory diagrams work; a static single face for 75 seconds may be dead air. Use beat map and actual speech timing to decide. For every quarter of the film, confirm there are visual discoveries, explanatory imagery or a consciously justified sustained hold. Plan especially around chapter transitions, complications and the ending. Don't spend the entire image budget in the first three minutes.

The edit should support 16:9 at least 1080p, keep important subjects in safe margins, use licensed local fonts only (do **not** bundle font binaries), respect low-volume playback readability, and retain enough negative space for chapter labels when those genuinely help comprehension. For publication thumbnail, develop separate 16:9 image concepts optimized for a small display, not a random frame crop.
