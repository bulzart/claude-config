## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach

xAI publishes API examples but no prompting guide, so official material is thin. Items 1–6 are xAI's own examples (https://docs.x.ai/developers/model-capabilities/video/generation, …/reference-to-video, …/extension); items 7–8 are the closest first-party Higgsfield material.

1. Image-to-video [OFFICIAL]:
   > Make the water crash down and slowly pan out the camera
2. Text-to-video [OFFICIAL]:
   > A glowing crystal-powered rocket launching from the red dunes of Mars, ancient alien ruins lighting up in the background as it soars into a sky full of unfamiliar constellations
3. Reference-to-video [OFFICIAL]:
   > slow zoom in on the white fashion runway stage. then, the model from <IMAGE_0> walks in from the back of the shot from the white opening, and gracefully walk out onto the front of the white stage platform. they wear the shirt from <IMAGE_1> and black flared jeans. they look dramatically at the camera. high quality slow motion shot. fun, playful. skin pores. highly detailed faces. perfect shot. […]
4. References with voices [OFFICIAL]:
   > The person from <IMAGE_0> presents the product from <IMAGE_1> on the set from <IMAGE_2>, speaking with the voice from <AUDIO_0>. A second speaker with the voice from <AUDIO_1> replies.
5. First and last frame (not exposed on Higgsfield) [OFFICIAL]:
   > The camera dollies from the sunlit doorway to the window, settling on the closing frame.
6. Extension (not exposed on Higgsfield) [OFFICIAL]:
   > The shot pans to an over the shoulder perspective. Calm controlled scene.
7. Higgsfield Grok 1.5 page [HF] (https://higgsfield.ai/grok-imagine-1.5):
   > Slow cinematic push-in as embers drift across the scene and the fabric stirs in the wind.
8. Higgsfield REST docs example [HF] (https://docs.higgsfield.ai/docs/models/grok-video-1-5/reference-to-video):
   > A cinematic wide shot of ocean waves at sunset, with gentle camera movement.

Patterns these teach:
- **Length:** short, often one sentence (1, 2, 5, 7, 8). Longer only for reference staging (3).
- **Image-to-video:** motion verbs plus camera verb in one imperative line (1, 7), with no re-description of the frame.
- **Order in reference prompts:** camera first ("slow zoom in…"), then "then, <subject from <IMAGE_n>> <action>", then wardrobe/objects "from <IMAGE_n>", then look (3). Voices are bound with "with the voice from <AUDIO_n>" (4).
- **Sentence style:** plain, even lowercase fragments. Quality keywords sit at the end (3).
- **Pacing:** slow motion appears **only when requested** (3). Otherwise imply real time.
- **Tone words:** "Calm controlled scene." sets pacing (6).
- **Exclusions and dialogue:** none shown in official examples. This library adds them per §3.10/§3.11.

### 4.1 Text-to-video

Classic only in the fixed format; follows patterns 2, 7 and 8 (one descriptive sentence plus a camera phrase).
```text
<Camera move> of <subject with appearance> <one directed action with end state> in <setting, time, light>.
<What stays still>. <Audio sentence>. One continuous shot, real-time pace. <Blank-surface clause>. No on-screen
text, no subtitles, no captions, no logos.
```
Example (`grok_video`, 8 s, 9:16):
```text
Low tracking shot moving alongside a grey-muzzled black dog as it runs across a wet beach at sunrise, splashes
through a shallow wave, and slows to a trot with a stick in its mouth. Low golden backlight, spray catching the light.
Audio: waves breaking, paws slapping wet sand, distant gulls. One continuous shot, real-time pace. The beach is empty
of signs and buildings. No on-screen text, no subtitles, no captions, no logos.
```

### 4.2 Start frame (and end frame) to video

Follows patterns 1 and 7 (imperative motion plus camera; no re-description).
```text
<Camera move> as <what moves, general terms, with direction>. <What stays still and unchanged>. <Audio sentence>.
One continuous shot, real-time pace. No on-screen text, no subtitles.
```
Example (either id; start_image = approved 9:16 still of a car parked on a road):
```text
Slow push-in toward the front of the car as its headlights switch on and light mist drifts across the road. The car
stays parked and unchanged in shape and color. Audio: a soft click, a low idle hum, light wind. One continuous shot,
real-time pace. No on-screen text, no subtitles.
```
End frame: N/A on Higgsfield.

### 4.3 Reference-to-video

Follows patterns 3 and 4 (camera first, then "then", subjects "from <IMAGE_n>", voice "with the voice from <AUDIO_0>"). Probe first (§2.6).
```text
<Camera move> in <setting>. then, the <person description> from <IMAGE_0> <action> with the <object description>
from <IMAGE_1>. The <object> keeps its exact shape, proportions and color. <Speaker> speaks with the voice from
<AUDIO_0>: "<short line>". <Audio bed>. One continuous shot, real-time pace. No on-screen text, no subtitles.
```
Example (`grok_video_v15`, references only, 720p):
```text
Slow push-in in a bright minimalist studio. then, the woman with shoulder-length braids from <IMAGE_0> lifts the small
white ceramic speaker from <IMAGE_1> off a wooden table and holds it at chest height. The speaker keeps its exact
rounded shape, proportions and matte finish. She speaks with the voice from <AUDIO_0>: "This one goes everywhere
with me." Soft room tone. One continuous shot, real-time pace. No on-screen text, no subtitles.
```

### 4.4 Video edit / extension / motion transfer (only if supported)

N/A on Higgsfield. xAI's `/v1/videos/edits` and `/v1/videos/extensions` are not exposed [OFFICIAL][HF]. Edit-Mode jobs route to `gemini_omni_flash_1_1` or `flux_3_video_edit`.

