## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach

1. Formula example, Google Cloud Blog (https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-veo-3-1):
   > Medium shot, a tired corporate worker, rubbing his temples in exhaustion, in front of a bulky 1980s computer in a cluttered office late at night. The scene is lit by the harsh fluorescent overhead lights and the green glow of the monochrome monitor. Retro aesthetic, shot as if on 1980s color film, slightly grainy.
2. Timestamp prompting, same source:
   > [00:00-00:02] Medium shot from behind a young female explorer with a leather satchel and messy brown hair in a ponytail, as she pushes aside a large jungle vine to reveal a hidden path. [00:02-00:04] Reverse shot of the explorer's freckled face, her expression filled with awe as she gazes upon ancient, moss-covered ruins in the background. SFX: The rustle of dense leaves, distant exotic bird calls. […] [00:06-00:08] Wide, high-angle crane shot, revealing the lone explorer standing small in the center of the vast, forgotten temple complex, half-swallowed by the jungle. SFX: A swelling, gentle orchestral score begins to play.
3. Dialogue and SFX, Gemini API (https://ai.google.dev/gemini-api/docs/veo):
   > A close up of two people staring at a cryptic drawing on a wall, torchlight flickering. A man murmurs, 'This must be it. That's the secret code.' The woman looks at him and whispering excitedly, 'What did you find?'
4. Text-safe dialogue, Agent Platform best practices (https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/video/best-practice):
   > A woman says: My name is Clara.
5. Image-to-video motion only, same source:
   > "Slow dolly in on the subject." / "The character's hair and clothes flutter gently in the wind." / "Fog rolls in slowly across the landscape."
6. Image-to-video prompt, Gemini API:
   > A surreal, cinematic macro video. Tiny surfers ride perpetual, rolling waves inside a stone bathroom sink. A running vintage brass faucet generates the endless surf. The camera slowly pans across the whimsical, sunlit scene as the miniature figures expertly carve the turquoise water.
7. First and last frame, Google Cloud Blog:
   > The camera performs a smooth 180-degree arc shot, starting with the front-facing view of the singer and circling around her to seamlessly end on the POV shot from behind her on stage. […]

Patterns these teach:
- **Order:** shot size or camera first, then subject, action, place/time, light, and style last (1, 6).
- **Sentence style:** declarative prose. Light and style may be terse fragments ("Retro aesthetic, … slightly grainy.").
- **Time:** `[mm:ss-mm:ss]` blocks, each holding one shot, one action and its own `SFX:` (2).
- **Subject vs camera motion:** Google separates camera motion, subject animation and environmental animation into distinct sentences (5). Transitions are described as a camera path (7).
- **Camera vocabulary:** standard film terms ("Reverse shot", "Tracking shot", "crane shot", "arc shot").
- **Audio:** separate sentences with `SFX:` or `Ambient noise:` labels. Dialogue in quotes is Google's generic syntax (3); the colon form (4) is Google's text-safe variant and this library's default.
- **Detail and length:** 30–110 words; concrete nouns and adjectives rather than adjective stacks.
- **Exclusions:** written as descriptions of what is there, not "no …" lists.

### 4.1 Text-to-video

Follows patterns 1–4: camera → subject → action → place → light/style → audio sentences → continuity/clean plate.
```text
<Shot size>, <angle>, <camera move>, <lens>. <Subject: age range, appearance, wardrobe>. <One action, cause →
effect>. <Place, time, weather>. <Light direction and temperature>, <style/format>. <Speaker> says: <short line,
no quotation marks>. SFX: <sound tied to the action>. Ambient noise: <place sound>. One continuous shot, no cuts,
real-time pace. Clean picture with plain unmarked surfaces and no captions, subtitles, logos or written words.
```
Example (`veo3_1`, 8 s, 9:16):
```text
Medium close-up, eye level, slow push-in, shallow depth of field. A man in his forties with close-cropped grey hair,
deep brown skin and a navy work jacket sits at a pale wooden workbench. He lifts a small matte-black handheld device
with his right hand, turns it once toward the window light, and sets it down beside a coil of cable, where it stays.
Quiet workshop at dusk, rain on the window. Warm lamp light from the left against cool blue window light, natural
film grain. He says: That should hold. SFX: a soft click as the device touches the bench. Ambient noise: steady
rain. One continuous shot, no cuts, real-time pace. Clean picture with plain unmarked surfaces and no captions,
subtitles, logos or written words.
```
Timestamped variant (pattern 2): at most four `[00:00-00:02]` blocks, each with one shot, one action and one SFX.

### 4.2 Start frame (and end frame) to video

Follows patterns 5–7: separate camera, subject and environment sentences; motion only.
```text
<Camera motion sentence>. <Subject animation sentence, general terms, in order>. <Environmental animation sentence>.
<Persistence: what stays fixed>. <Audio sentences>. One continuous shot. <Clean-plate sentence>.
```
Example (`veo3_1`, start_image = approved 9:16 product-in-scene still):
```text
Very slow dolly in toward the table. The woman slides the bottle two centimetres toward the camera with her right
hand and releases it. Steam drifts from the cup behind it. The bottle stays upright where she left it, keeping its
exact shape, proportions, label and soft shadow to the right. SFX: glass gliding on wood. One continuous shot. Clean
picture with no added captions or written words.
```
First + last (`veo3_1_lite`), pattern 7: `The camera arcs slowly a quarter-turn left around the desk as the small robot lamp raises its head and switches on, ending on the side view of the lit lamp. One continuous shot, no cuts. No captions or written words.`

### 4.3 Reference-to-video

N/A on Higgsfield. Use §4.2 with a start frame composited from the approved references.

### 4.4 Video edit / extension / motion transfer (only if supported)

N/A on Higgsfield. Edit Mode jobs go to `gemini_omni_flash_1_1` (edit) or `flux_3_video_edit`. Chain clips via last frame → `start_image`.

