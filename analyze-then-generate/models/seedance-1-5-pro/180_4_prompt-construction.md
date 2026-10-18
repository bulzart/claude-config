## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach

All from the BytePlus Seedance 1.5 pro prompt guide (S1):

**E1 — motion with degree adverbs:** "The doll first rotates slowly, then she stops rotating and shows her cuteness in front of the camera."

**E2 — voice control:** "In a gentle emotional state, with a soft tone and a slow speaking pace, say: "You can take your time. I'm not rushing you.""

**E3 — two-person dialogue:** "In a warm, softly lit independent bookstore, two Americans—a man and a woman—stand shoulder to shoulder, flipping through the same book. The light falls across the pages and their faces. The camera makes an extremely subtle dolly-in, creating a quiet and intimate atmosphere. English dialogue: Man: "Did you ever read this one before?" Woman: "No, but… I think I want to, with you.""

**E4 — voice-over:** "Generate a video with voiceover: A deep, calm male voice says, "In the vast silence of the universe, our world is but a fleeting moment. Yet, within it, life thrives against all odds." The scene should slowly transition from night to dawn, with the stars gradually disappearing and the sun rising from behind the mountains."

**E5 — product keyframe:** "Generate a video based on the input lipstick product keyframe image, keeping the appearance, proportions, and materials of both the lipstick and the model accurate and consistent, with no unnecessary elements added. The overall style is a high-end e-commerce beauty commercial, clean, refined, and premium in tone. The video consists of three continuous shots: in the first shot, the camera performs an extremely slow and smooth push-in […]"

**E6 — shot timing:** "Shot 1: Medium shot. The character raises her hand and looks at her palm. Shot 2: Cut to a close-up of the hand. Faint glowing particles begin to appear around the palm, slowly drifting in the air. Shot 3: Cut to a close-up of the character's neck. The glowing particles spread upward. […] Shot 5: Cut to a close-up of her face. […] she smiles with satisfaction and says, "Merry Christmas.""

Patterns these teach [derived from E1–E6]:
- **Order:** scene and light → subjects with attributes → action → camera → dialogue block last (E3); image tasks open with the fidelity sentence (E5).
- **Sentence style:** plain declarative sentences; degree adverbs ("slowly", "extremely subtle") set speed and amplitude (E1, E3).
- **Time:** no timestamps — "first … then", "Shot N: … Cut to …", "slowly transition from … to …" (E1, E4, E6).
- **Subject vs camera:** separate sentences ("The camera makes an extremely subtle dolly-in…") (E3).
- **Dialogue syntax:** language header ("English dialogue:"), `Speaker: "line"`; delivery as "In a <emotion> state, with a <tone> and a <pace>, say:" (E2, E3).
- **Length:** 15–100 words; 12 s allows up to five short shots (E6).
- **Exclusions:** expressed positively ("with no unnecessary elements added") (E5).

### 4.1 Text-to-video

```text
<Scene: place, time, light direction>. <Subject with concrete features> <movement with degree adverbs: first …, then …>. <Camera: shot size + movement formula, or "static shot, fixed camera position">. <Aesthetic: palette, texture>. <Sound: ambience, action sounds, music or "no background music">. <Dialogue: In a <emotion> state, with a <tone> and a <pace>, <speaker> says: "<line>"> <Constraint sentence>.
```
Worked example (8 s):
```text
At dusk, at a quiet bus stop, cool blue street light reflects on the wet pavement. A young woman with short silver hair and a navy windbreaker checks the empty road, then slowly lowers her hood as light rain begins. The camera starts in a medium shot and performs a slow dolly-in to a close-up of her face. Realistic texture, soft reflections. Soft rain on the shelter roof, distant traffic, no background music. In a calm emotional state, with a low tone and a slow speaking pace, she says: "It's always late on Fridays." Keep it subtitle-free; avoid generating any text or subtitles; the shelter and signs are blank; do not generate a logo or watermark.
```

### 4.2 Start frame (and end frame) to video

```text
Based on the first frame, <what changes: subject action with degree adverbs, object state, camera move>. Keep <identity details>, <product appearance, proportions and materials> accurate and consistent, with no unnecessary elements added. <Camera>. <Light: direction and shadows stay as in the frame>. <Sound>. <Constraint sentence>.
[With an end frame:] The shot moves continuously from the first frame to the last frame: <connecting action>.
```
Worked example (4 s):
```text
Based on the first frame, a hand enters from the right, picks up the small round alarm clock by its base, turns it slowly so the face points at the camera, then sets it back in the same spot. Keep the clock's shape, proportions and colours accurate and consistent, with no unnecessary elements added. Static shot, fixed camera position. The desk lamp keeps lighting the clock from the left; its shadow stays on the right. Soft desk ambience, a light tap as the clock is set down, no background music. Keep it subtitle-free; the clock face shows plain hands without numbers or text; do not generate a logo or watermark.
```

### 4.3 Reference-to-video

N/A on Higgsfield — no reference inputs [HF S5]. Use `seedance_2_0` or `seedance_2_5`.

### 4.4 Video edit / extension / motion transfer (only if supported)

N/A on Higgsfield [HF S5; OFFICIAL S3]. "Extension" = chaining the last frame into a new first-frame clip (§3.14). Multi-shot dialogue inside one 12 s clip follows E3/E6:
```text
<Scene with light; each character's gender, age, clothing>. The shot begins with a <shot size> of <both>. <Character A>, <emotion/tone>, says: "<line>". The shot cuts to a close-up of <Character B>, who <reaction> and replies <tone>: "<line>". Finally, the shot cuts back to <shot size>; <final action>; the frame holds. <Sound>. <Constraint sentence>.
```
Worked example:
```text
In a small workshop under warm lamp light from above, a bearded man in a denim apron and a young woman in a grey hoodie stand at a workbench over a half-built wooden stool. The shot begins with a medium shot of both. The man, calm and encouraging, says: "Sand it once more, then we glue." The shot cuts to a close-up of the woman, who nods and replies with a small smile: "Once more. Got it." Finally, the shot cuts back to the medium shot; she picks up a sanding block with her right hand and starts on the seat edge; the frame holds. Soft workshop hum, sanding sound, no background music. Keep it subtitle-free; avoid generating any text or subtitles; do not generate a logo or watermark.
```

