## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach

1. Single scene, Gemini API Omni guide (https://ai.google.dev/gemini-api/docs/omni):
   > Continuous, unbroken handheld shot of a fluffy tabby cat sitting on a sunny windowsill, looking out into a leafy garden. The cat's tail twitches slowly, and its ears rotate slightly toward ambient noises. Sunbeams illuminate dust motes in the air. Sound design: Gentle breeze, distant bird chirps. No dialogue.
2. Timecodes, same source:
   > [0-3s] A person is walking [3-6s] They stop and turn around [6-10s] They start running
3. Simplified edits, same source:
   > Add a cat that jumps onto his lap, he begins to pet it. Keep everything else the same. / Make the phone invisible. Keep everything else the same.
4. Declared sources and references, same source:
   > [# Sources <FIRST_FRAME>@Image1] [# References <IMAGE_REF_0>@Image2] a woman <IMAGE_REF_0> is walking. Use Image1 as the starting frame. Use Image2 as a reference for the video generation.
5. First and last frame, DeepMind Omni prompt guide (https://deepmind.google/models/gemini-omni/prompt-guide/):
   > A close-up low-angle shot of a stylish drummer in a beige suit playing a red drum kit in a grand hall transitions as the camera whip-pans to the side, revealing an older saxophonist playing alongside a ballet dancer spinning in a white outfit under soft purple stage lights. One continuous shot, no jump cuts.
6. Image as a motion guide, Gemini API:
   > turn this into realistic footage, using the drawing only as a guide for movement, do not show the drawing in the final video
7. Intended scene text, Gemini API:
   > There is a street sign that says: "This is an AI generation by Omni", there is a storefront that says: "All you need AI", there's a car with the number plate: "OMNI1.1"
8. First-party Higgsfield VFX edit [HF] (https://higgsfield.ai/blog/gemini-omni-flash-vfx-video-editing):
   > SOURCE LOCK: This is an ADD-ELEMENT VFX pass on video_1, NOT a new generation. Keep 1:1 everything already in the plate […] Only ADD the live bird and animate it. […] ANTI-SLOP: Real feather texture with high detail; lively eyes with a sharp catchlight; convincing flight physics with proper weight, acceleration, and air resistance. No robotic/CGI look, no floating, and no morphing shapes or extra limbs. […] No music. No on-screen text.

Patterns these teach:
- **Order:** continuity phrase first ("Continuous, unbroken … shot"), then subject, micro-actions, ambient detail, a `Sound design:` label, and short negatives last (1).
- **Sentence style:** short declarative sentences. Edits are one imperative sentence plus "Keep everything else the same." (3).
- **Time:** `[0-3s]` timecodes with one action per segment (2).
- **Subject vs camera:** camera path stated as the transition ("transitions as the camera whip-pans…") separate from subject action (5).
- **References:** declared blocks and inline tags, then guiding sentences at the end (4). Intent words for how an image is used ("only as a guide for movement, do not show the drawing") (6).
- **Detail:** 10–70 words; less prescriptive than Veo. Higgsfield's long, block-structured prompt (8) is its own style for complex VFX, and runs against Google's "simple prompts" edit advice.
- **Exclusions:** "No dialogue." / "Do not do X" (1, 8).
- **Scene text:** `says: "<exact words>"` (7).

### 4.1 Text-to-video

Follows patterns 1–2 and 7.
```text
In a single continuous shot, <camera framing and move>. <Subject with appearance> <micro-actions in order, or
[0-3s]/[3-6s]/[6-10s] beats>. <Location, time, light source>. <Style>. Sound design: <ambience/SFX/music>.
<Speaker> says: <line without quotation marks> | No dialogue. <Blank-surface clause>. No on-screen text. No subtitles.
No captions.
```
Example (`mode:"text-to-video"`, 8 s, 9:16):
```text
In a single continuous shot, a slow push-in at table height. An orange tabby cat stalks along a sunlit kitchen
counter, pauses beside a glass of water, taps it once with a paw so the water ripples, then sits beside it while the
glass stays upright. Late-morning light from a side window, soft shadows to the right, natural documentary look, real-
time pace. Sound design: quiet kitchen ambience, a light tap of paw on glass, distant birdsong. No dialogue. Cupboards
and appliances are plain and unlabeled. No on-screen text. No subtitles. No captions.
```

### 4.2 Start frame (and end frame) to video

Follows patterns 1 and 5 (initial frame → path → final reveal).
```text
<Camera movement>. <What moves, general terms, in order>. <What stays fixed>. Sound design: <…>. One continuous
shot, no jump cuts. No on-screen text.
```
Example (`mode:"image-to-video"`, start_image = approved 9:16 still of a person at a desk with a laptop):
```text
Slow push-in from medium to medium close-up. The woman looks up from the laptop, smiles, and closes the lid with both
hands; the laptop stays flat on the desk with its exact shape and proportions. Dust motes drift through the window
light. Sound design: soft room tone and the muted click of the lid. No dialogue. One continuous shot, no jump cuts.
No on-screen text.
```
First + last example: `The first frame shows a closed cardboard box on a workbench; the camera stays locked off while the lid flaps open and a small wind-up toy climbs out, ending exactly on the final frame of the toy standing beside the open box. One continuous shot, no jump cuts. No on-screen text.`

### 4.3 Reference-to-video

Follows pattern 4 (declared blocks, tags plus description, guiding sentences last).
```text
[# References <IMAGE_REF_0>@Image1 <IMAGE_REF_1>@Image2] In a single continuous shot, <scene and camera>. <Person
description> <IMAGE_REF_0> <action> with the <object description> <IMAGE_REF_1>. <Locks: exact shape, proportions,
color, material; identity>. <Light inheritance>. Sound design: <…>. No on-screen text. No subtitles. Use the given
images as references for video generation. The images should not be used as literal initial frames.
```
Example (two image references):
```text
[# References <IMAGE_REF_0>@Image1 <IMAGE_REF_1>@Image2] In a single continuous shot, a slow tracking shot along a
city sidewalk at golden hour. The young man with short curly hair <IMAGE_REF_0> walks toward camera carrying the
compact silver thermos <IMAGE_REF_1> in his left hand and unscrews its cap. The thermos keeps its exact cylindrical
shape, proportions and brushed-metal finish, lit by the same warm low sun as the street. Sound design: footsteps,
light traffic, a soft metallic twist. No dialogue. No on-screen text. No subtitles. Use the given images as references
for video generation. The images should not be used as literal initial frames.
```

### 4.4 Video edit / extension / motion transfer (only if supported)

Follows pattern 3: one operation, short, then "Keep everything else the same." Run text removal as pass 1 (§3.11d).
```text
<One operation, 1–2 sentences, with placement/scale/light details only if the edit needs them>. <Reference binding
if any>. Keep everything else the same.
```
Examples:
- `Remove the white caption text along the bottom of the frame and restore the table surface behind it. No on-screen text. Keep everything else the same.`
- `Replace the red mug in her hand with the ceramic mug from <IMAGE_REF_0>, same size and same motion, lit by the same window light. Keep everything else the same.`
- `Change the lighting to warm late-afternoon sun from the left. Keep everything else the same.`

Motion transfer (Google-documented intent) [OFFICIAL]: `Apply the pose and motion from <VIDEO_REF_0> to the character from <IMAGE_REF_0>. Use the given video as a reference. Do not use it as a source for video editing.` Extension: N/A on Higgsfield.

