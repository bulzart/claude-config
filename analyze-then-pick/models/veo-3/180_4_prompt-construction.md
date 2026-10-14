## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach

1. Character with dialogue, DeepMind Veo 3 prompt guide (https://deepmind.google/models/veo/prompt-guide/):
   > A medium shot frames an old sailor, his knitted blue sailor hat casting a shadow over his eyes, a thick grey beard obscuring his chin. He holds his pipe in one hand, gesturing with it towards the churning, grey sea beyond the ship's railing. "This ocean, it's a force, a wild, untamed might. And she commands your awe, with every breaking light"
2. Sound design, same source:
   > A keyboard whose keys are made of different types of candy. Typing makes sweet, crunchy sounds. Audio: Crunchy, sugary typing sounds, delighted giggles.
3. Style-first script, same source:
   > Camping (Stop Motion): Camper: "I'm one with nature now!" Bear: "Nature would prefer some personal space."
4. Text-safe dialogue with ambience, Agent Platform prompt guide (https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/video/video-gen-prompt-guide):
   > A medium shot in a dimly lit interrogation room. The seasoned detective says: Your story has holes. The nervous informant, sweating under a single bare bulb, replies: I'm telling you everything I know. The only other sounds are the slow, rhythmic ticking of a wall clock and the faint sound of rain against the window
5. Audio detail, Gemini API ("prompting Veo 3's audio generation") (https://ai.google.dev/gemini-api/docs/veo):
   > A wide shot of a misty Pacific Northwest forest. Two exhausted hikers, a man and a woman, push through ferns when the man stops abruptly, staring at a tree. Close-up: Fresh, deep claw marks are gouged into the tree's bark. Man: (Hand on his hunting knife) "That's no ordinary bear." […] A rough bark, snapping twigs, footsteps on the damp earth. A lone bird chirps.
6. Unbranded detail and play-by-play, DeepMind Veo 3 prompt guide:
   > […] Several heavily modified, entirely unidentifiable, and unbranded off-road vehicles are engaged in a frenetic, no-holds-barred race. […] a hulking, high-clearance beast with a heavily reinforced external roll cage and no discernible badging […]
7. Image-to-video motion, Agent Platform best practices (https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/video/best-practice):
   > "Slow dolly in on the subject." / "The character's hair and clothes flutter gently in the wind." / "Fog rolls in slowly across the landscape."

Patterns these teach:
- **Order:** shot framing first (1, 4, 5), or style first ("Camping (Stop Motion):"), then subject, action, setting, sound.
- **Sentence style:** vivid prose. A shot change can be written inline ("Close-up: …") (5).
- **Dialogue:** quoted after the description (1), a `Speaker:` script (3, 5), or colon without quotes (4, the text-safe form used here). Stage directions go in parentheses (5).
- **Audio:** `Audio:` label (2) or plain closing sound sentences (4, 5).
- **Exclusions:** stated as descriptive absence ("unidentifiable, and unbranded", "no discernible badging") (6).
- **Detail:** 20–120 words. Play-by-play only for complex action (6).
- **Image-to-video:** camera, subject and environment motion as separate short sentences (7).

### 4.1 Text-to-video

Follows patterns 1, 4 and 6: style → shot → subject → action → place/light → colon dialogue → sound sentences → continuity/clean plate.
```text
<Style/format>. <Shot size>, <angle>, <camera move>. <Subject with explicit appearance and wardrobe>. <One action,
cause → effect, with end state>. <Place and time>. <Light direction and temperature>. <Speaker> says: <short line>.
<Sound sentence(s)>. One continuous shot, no cuts, real-time pace. Clean picture with unbranded, unmarked surfaces
and no captions, subtitles, logos or written words.
```
Example (`veo3`, 9:16):
```text
Photorealistic, shot on 35mm film. Wide shot, low angle, slow tracking left. A brown-and-white dog with a plain red
collar trots along a shallow stream bed, splashing through the water, then stops on a flat stone and shakes itself
dry. Early morning in a pine forest, mist between the trunks. Soft warm backlight rims the wet fur. Water splashing,
the rattle of the dog shaking, birdsong in the distance. One continuous shot, no cuts, real-time pace. Clean picture
with no captions, subtitles, logos or written words.
```

### 4.2 Start frame (and end frame) to video

Follows pattern 7: separate camera, subject and environment sentences; general subject terms.
```text
<Camera motion>. <Subject animation, general terms, in order>. <Environmental motion>. <What stays fixed>.
<Sound sentence>. One continuous shot. <Clean-plate sentence>.
```
Example (start_image = approved 9:16 still of a person holding a handheld object):
```text
Slow push-in toward her hands. She raises the handheld object to chest height and holds it steady in her right
hand. Curtains stir in a light breeze behind her. The object keeps its exact shape and details from the first frame.
Fabric rustle and quiet room tone. One continuous shot. No captions or written words appear.
```
End frame: N/A on Higgsfield.

### 4.3 Reference-to-video

N/A on Higgsfield; use §4.2 with a composited start frame.

### 4.4 Video edit / extension / motion transfer (only if supported)

N/A on Higgsfield (extension is a Veo 3.1 feature upstream) [OFFICIAL][HF].

