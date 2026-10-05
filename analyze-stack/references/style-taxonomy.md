# Style taxonomy — labels, sub-styles, reproduction parameters, Seedance phrasing

Used by the visual analyst (`20-analysis\style-profile.md`), the style-bible author (`40-plan\style-bible.md`)
and every prompt writer (the STYLE line of each prompt). Owner brief: identify "real organic footage,
cartoon (which style), animation (which style: 2D, 3D, anime, stop motion, claymation, pixel art, and
so on), sketch or drawing, or any other style, plus the sub-style details needed to reproduce it
(color palette, line work, rendering, camera language, era)".

## 1. Reproduction parameters (fill ALL for the source style; measured where possible)

| Parameter | What to record | Source |
|---|---|---|
| Colour palette | 5 dominant hex + shares (k-means from keyframes), overall temperature, saturation level (HSV mean), contrast | `10-measure\visual-stats.json` (`global.palette`, `frames[].brightness/saturation/contrast/colourfulness`, `global.style_hints`) + eye |
| Line work | none (photo) · clean vector · rough ink · pencil · variable brush · pixel edges; line weight; outline colour | keyframes at full res |
| Shading / rendering | photoreal · cel (flat, 2-tone) · soft gradient · painterly · toon-shaded 3D · PBR 3D · claymation matte · watercolour bleed · halftone | keyframes |
| Animation cadence | live 24/30 fps · on-2s (12 fps feel) · on-3s · stop-motion jitter · smear frames · limited animation (held bodies, moving mouths) | frame-diff pattern in `shots.json`/motion output |
| Camera language | handheld phone · gimbal · tripod locked · dolly/slider · drone · POV chest/head cam · screen recording · virtual camera (3D) · multiplane 2D | motion classification per second |
| Era / look | 2020s phone UGC · 2010s DSLR vlog · 90s VHS · 80s anime · 60s hand-drawn · modern flat design · retro pixel | grain, aspect, colour science, fonts |
| Texture | grain, noise, compression artefacts, paper texture, film scratches, halation, bloom, chromatic aberration | keyframes |
| Lighting | key direction, quality (hard/soft), colour temperature, practicals, time of day | keyframes + shot table |
| Lens / DoF | wide/normal/tele feel, DoF depth, focus breathing, phone ultra-wide distortion | keyframes |
| Typography (on-screen text) | font class, weight, colour, stroke, position, animation | `ocr.json` + frames |
| Audio character (for the style bible) | room tone, mic quality, music genre | `audio.md` |

## 2. Style labels and sub-styles

### 2.1 Real organic footage (photoreal, live action)
| Sub-style | Cues | Seedance phrasing (build on these; official style words in `SEEDANCE-SPEC.md` §6.7) |
|---|---|---|
| UGC handheld phone | vertical, slight shake, auto-exposure pumping, window light, face-to-camera, phone-camera texture | "authentic UGC texture, handheld phone video with slight natural shake, natural window light, real skin texture, no beautification, natural colors, HD" |
| Phone POV (chest/head/hand) | first-person hands, wide lens distortion, walking bob | "first-person perspective, phone ultra-wide look, hands visible in the lower frame, slight walking bob, natural daylight" |
| Studio product | seamless background, controlled softbox light, tripod, macro inserts | "clean studio product shot, seamless backdrop, soft diffused key light from the upper left, locked-off camera, macro detail, realistic metal/glass/liquid texture" |
| Cinematic | shallow DoF, graded (teal/amber…), gimbal moves, 24 fps motion blur, film grain | "cinematic live-action, 35mm film look, shallow depth of field, fine film grain, <grade> color grading, smooth gimbal movement" |
| Vlog / DSLR | eye-level, mirrorless bokeh, natural grade, jump cuts | "DSLR vlog look, natural colors, medium shot, soft background bokeh, natural indoor light" |
| Screen recording / UI | flat UI, cursor, app chrome | NOT generated: real UI must come from supplied screen footage (miko rule 7); prompt describes only what surrounds it |
| Security / dashcam / drone | fisheye, timestamp burn-in, high angle | "surveillance view / drone aerial perspective, wide angle, <time of day>" |
| Documentary / news | interview framing, lower thirds (not generated), natural light | "documentary style, natural lighting and shadows, handheld observational camera" |

### 2.2 Cartoon (stylised 2D, non-anime)
| Sub-style | Cues | Phrasing |
|---|---|---|
| Classic Western cartoon (rubber-hose / 90s TV) | thick outlines, flat fills, squash-and-stretch, limited palette | "2D cartoon animation, bold black outlines, flat cel colors, squash-and-stretch motion, <era> Saturday-morning cartoon look" |
| Modern flat / vector (explainer) | no outlines or thin, geometric shapes, pastel palette, smooth tween motion | "flat vector 2D animation, minimal outlines, geometric shapes, pastel palette, smooth eased motion" |
| Adult-animation sitcom | thin uniform lines, flat colours, held bodies + moving mouths | "2D animated sitcom style, thin uniform outlines, flat colors, limited animation with held poses" |
| Comic / graphic novel | halftone, panels, speech bubbles, ink | "comic-book style, ink linework, halftone shading, high-contrast colors" |

### 2.3 Animation
| Sub-style | Cues | Phrasing |
|---|---|---|
| 2D hand-drawn | visible line boil, on-2s cadence, painted backgrounds | "hand-drawn 2D animation, animated on twos, soft painted backgrounds, subtle line boil" |
| 3D (CG) | PBR materials, GI lighting, subsurface skin, virtual camera | "3D animated film look, soft global illumination, subsurface skin, physically based materials, smooth virtual camera" |
| 3D toon-shaded | cel shading on 3D models, outline pass | "3D cel-shaded animation, flat two-tone shading with outline pass" |
| Anime | large eyes, hair highlights, painterly backgrounds, speed lines, dramatic lighting | "Japanese anime style, cel shading, detailed painterly backgrounds, expressive eyes, <studio-era feel described in words — never a studio or artist name>" |
| Stop motion (puppet) | fabric/felt textures, replacement mouths, slight jitter | "stop-motion puppet animation, felt and fabric textures, slight frame-to-frame jitter, tabletop miniature set with real shadows" |
| Claymation | matte clay, fingerprints, morphing forms | "claymation, matte clay surfaces with subtle fingerprints, stop-motion cadence, miniature set lighting" |
| Pixel art | hard pixel edges, limited palette, no anti-aliasing, 8/16-bit motion | "pixel-art animation, 16-bit look, hard pixel edges, limited palette, no anti-aliasing" (official example E6 in the spec) |
| Sketch / drawing | pencil or ink on paper, visible strokes, paper texture, sometimes drawn-on-live | "pencil sketch animation on textured paper, visible graphite strokes, line boil, monochrome with <accent>" |
| Watercolour | bleeding edges, paper grain, soft washes | "watercolor animation, soft bleeding edges, visible paper grain, translucent washes" |
| Comic (animated) | panel motion, halftone, ink | as 2.2 comic + "animated panels, hard cuts between panels" |
| Mixed media | live action + drawn elements / collage | describe each layer: "live-action footage with hand-drawn overlay animation" |
| Motion graphics / kinetic type | text-driven, shapes | text rendering is unreliable → keep on-screen text out of generation; overlays are added in the edit |

## 3. Style swap rules (Q5 = swap)

1. Context and content never change: same setting, people, actions, dialogue, timing, product; only the
   rendering changes. The style bible (`40-plan\style-bible.md`) pins the target look with all §1
   parameters, written in Seedance words, and every prompt carries the same STYLE line verbatim.
2. Real → animation: convert people to characters with 2–3 stable visible features each (hair, wardrobe,
   accessory); products keep exact colours/label but in the target rendering ("the same can rendered as
   flat cel-shaded 2D with the label text intact"); physics stay real unless the style is cartoon
   (then squash-and-stretch is allowed but object count and cause-effect still hold).
3. Animation → real: replace stylised proportions with plausible humans/objects; keep palette and
   composition; add camera realism (handheld or locked) and real lighting; never keep outlines.
4. Reference images in a different style pull the output toward that style (spec §9.6) — for a swap,
   prefer product photos (identity) plus a style reference converted to the target style, and state
   "do not use the rendering style of @Image N" for photos when the target is animated.
5. Never name a studio, artist, film or IP (spec §8 limits); describe the look in observable terms.
6. `style-profile.md` records the SOURCE style with §1 parameters; `style-bible.md` records the TARGET
   style and, per entity, the conversion (person → character sheet lines; product → rendering note).

## 4. `style-profile.md` skeleton

```markdown
# Style profile — <run-id>
Label: <real organic footage> · Sub-style: <UGC handheld phone> · Confidence: high/medium/low
| Parameter | Value | Evidence |
|---|---|---|
| Colour palette | #c6ab99 35 %, #302122 22 %, … ; warm; saturation 0.41 mean | palette from measure output |
| Line work | none (photo) | — |
| … (all §1 rows) | | |
STYLE LINE for prompts (verbatim, ≤ 40 words): "authentic UGC texture, handheld phone video with slight natural shake, warm window light from the left, real skin texture, natural colors, HD, rich details"
On-screen text style (for the edit, not for generation): <font class, colour, position>
```
