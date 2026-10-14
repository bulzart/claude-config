## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach

Sources: BFL Text-to-Video guide (https://docs.bfl.ai/guides/prompting_video_text_to_video), Audio and speech guide (https://docs.bfl.ai/guides/prompting_video_audio), cookbooks (https://docs.bfl.ai/cookbook/video_start_from_images, https://docs.bfl.ai/cookbook/video_edit_recast_continue).

1. Short:
   > A red fox leaping through fresh snow, telephoto.
2. Long natural language:
   > A red fox stalks across a wide snowfield at dawn, low winter light, a dark treeline fading into mist behind it. It slows, crouches, then leaps high and pounces into the fresh snow. Telephoto lens, shallow depth of field, locked-off camera panning gently to follow. Muffled paw steps and a soft breeze.
3. Multi-shot:
   > SHOT ONE: wide aerial of a desert highway at dawn, a single red car speeding through. HARD CUT. SHOT TWO: interior close-up, the driver's hands drumming the wheel. HARD CUT. SHOT THREE: from the roadside, the car shrinks into the heat haze. One music bed across all three shots.
4. Timesteps:
   > 0.0–1.5s — locked wide of a still harbor at dawn, boats motionless on glassy water / 1.5–3.0s — a slow push-in begins as gulls lift off the water / 3.0–5.0s — the sun breaks the horizon, warm light spreads and the camera settles
5. Dialogue:
   > A weather presenter on camera in front of a stylized storm map, speaking to the lens: "Storm season is here — and this time, we're ready." Confident delivery, clean studio lighting. No on-screen text, no subtitles.
6. Start frame (cookbook):
   > The video begins exactly on the provided image, the fully set dinner table holding still for a beat. Then the entire room begins to rotate slowly clockwise, ninety degrees over the length of the clip, so the right-hand wall becomes the new floor. […] The camera is locked rigidly to the room so the world itself appears to tip. Audio: […] No on-screen text.
7. Reference images (cookbook):
   > The stop-motion claymation badger from the reference images, same striped face, same brass spectacles, same mustard tweed waistcoat and clay fingerprints, stands in a wind-bent meadow at dusk holding a tiny clay clipboard. […] Handheld camera eases in to a chest-up framing. Audio: wind through dry grass, the creak of stiff clay as he turns, a single distant crow. No on-screen text, no subtitles.
8. Continuation (cookbook):
   > Continue this video from its final frames: the brass wind-up robot reaches the very edge of the workbench, its front foot steps out over nothing, and it keeps marching forward on the empty air, […] Audio: the clockwork ticking continues unbroken, […] One continuous shot. No on-screen text.

Patterns these teach:
- **Order:** subject + action + environment, then lens/camera, then audio, then the exclusion tail (2, 5, 7). One-liners compress to subject, action, lens (1).
- **Sentence style:** directorial prose. Mode-specific openers: "The video begins exactly on the provided image" (6); "Continue this video from its final frames: <what they show>" (8); "The <subject> from the reference images, same <anchor>, same <anchor>" (7).
- **Time:** `SHOT ONE … HARD CUT` (3); `0.0–1.5s —` timesteps (4); beats ordered with "then" (2, 6).
- **Subject vs camera:** the camera gets its own clause ("locked-off camera panning gently to follow"; "The camera is locked rigidly to the room") (2, 6).
- **References:** re-list identity anchors with "same …" (7).
- **Detail:** 7–110 words; one event per shot.
- **Exclusions:** explicit tails "No on-screen text, no subtitles." in nearly every official video example (5–8).
- **Audio:** an `Audio:` label with concrete sources. Speech is quoted with a named on-camera speaker (5). "One music bed across all three shots" (3).

### 4.1 Text-to-video

Follows patterns 2, 3 and 5.
```text
One continuous unbroken real-time shot. <Subject, fixed description> <one action: cause → response → payoff> in
<environment, time>. <Camera clause: framing, angle, one movement>. <Light source/direction, depth of field, look>.
<Speaker> says: "<short line>" | Audio: <ambience>, <effects tied to actions>. The set and every object keep the same
geometry throughout. Clean, unmarked surfaces. No on-screen text, no subtitles, no logos.
```
Example (10 s, 9:16, audio on):
```text
One continuous unbroken real-time shot. A small brass wind-up toy robot marches in a straight line across a
cluttered wooden workbench at night, stiff even steps with a faint mechanical tremor, and stops at the edge of the
bench. Low tracking shot level with the bench, moving slowly right. A single desk lamp rakes light from the left,
shallow depth of field, warm amber palette. Audio: low lamp hum, clockwork ticking locked to each step. The bench and
every object keep the same geometry throughout. Clean, unmarked surfaces. No on-screen text, no subtitles, no logos.
```
Multi-shot variant (pattern 3): `SHOT ONE: <wide>. HARD CUT. SHOT TWO: <contrasting close-up>. HARD CUT. SHOT THREE: <payoff>. One music bed across all shots. No on-screen text, no subtitles.`

### 4.2 Start frame (and end frame) to video

Follows pattern 6.
```text
The video begins exactly on the provided image. <What moves, in order, with direction>. <What stays fixed: shape,
set, light, contact shadow>. <Camera clause>. <Audio layers or none>. No on-screen text.
```
Example (start_image = approved 9:16 still of a product on a table; audio off):
```text
The video begins exactly on the provided image. Morning light slides slowly across the table from left to right,
passing over the ceramic bottle and its shadow; a thin curl of steam rises from the cup behind it. The bottle stays
perfectly still, with the same shape, proportions and contact shadow. Locked-off camera. No on-screen text.
```
Start + end: `The video begins exactly on the first provided image and ends exactly on the second: <stages of the change in order>. The camera stays locked off; the light and set never change. <Audio>. No on-screen text.`

### 4.3 Reference-to-video

Follows pattern 7 (use only after the §2.5 probe confirms reference behaviour).
```text
The <subject> from the reference images, same <anchor 1>, same <anchor 2>, same <anchor 3>, <action> in <new
setting>. <Camera clause>. <Light> with <grounding: contact shadow, reflection>. Audio: <…>. No on-screen text, no
subtitles.
```
Example (image_references = a two-view sheet of a handheld device):
```text
The handheld device from the reference images, same rounded-rectangle body, same matte sage-green shell, same single
circular button on the front, rests in the open palm of a person's hand on a sunlit balcony, then the hand tilts it
slowly toward the camera. Handheld close shot. Warm afternoon sun from the left, the device casting a soft shadow
across the palm. Audio: distant city hum, leaves rustling. No on-screen text, no subtitles.
```

### 4.4 Video edit / extension / motion transfer (only if supported)

Continuation via `video_references` (if the probe confirms continuation), following pattern 8:
```text
Continue this video from its final frames: <what the last frames show>. <One next action>. <Camera continues its
current move>. <Established sounds continue unbroken>, then <new sound tied to the new action>. One continuous
shot. No on-screen text.
```
Example: `Continue this video from its final frames: the cyclist reaches the crest of the hill. She freewheels down the far side as the road curves left, the camera keeping the same low trailing angle. Wind and tyre hiss continue unbroken; a bell rings once as she passes a gate. One continuous shot. No on-screen text.`

Editing a supplied clip: `flux_3_video_edit`. Motion transfer: N/A.

