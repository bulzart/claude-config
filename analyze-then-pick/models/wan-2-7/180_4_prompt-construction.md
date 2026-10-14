## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach
Verbatim first-party examples (trimmed with […]):

1. Timed multi-shot — Wan2.7 text-to-video API reference, https://www.alibabacloud.com/help/en/model-studio/text-to-video-api-reference
   > "A tense detective story with cinematic storytelling. Shot 1 [0–3 seconds] wide shot: Rainy New York street at
   > night, neon lights flicker, a detective in a black trench coat walks briskly. Shot 2 [3–6 seconds] medium shot:
   > The detective enters an old building, rain wets his coat, the door closes slowly behind him. Shot 3 [6–9
   > seconds] close-up: The detective's focused eyes, distant sirens sound, he frowns slightly. […]"
2. First frame + driving audio — Wan 2.7 image-to-video API reference, https://www.alibabacloud.com/help/en/model-studio/image-to-video-general-api-reference
   > "A scene of urban fantasy art. A dynamic graffiti art character. A boy made of spray paint comes to life on a
   > concrete wall. He sings an English rap song at high speed while striking a classic, energetic rapper pose. […]
   > The light comes from a single street lamp, creating a cinematic atmosphere full of high energy and amazing
   > detail. The audio of the video consists entirely of the rap, with no other dialogue or noise."
3. First + last frame — same page
   > "Realistic style, a small black cat looks up at the sky curiously. The camera angle gradually rises from eye
   > level, finally capturing its curious gaze from a top-down view."
4. Clip + last frame — Image-to-video 2.7 guide, https://www.alibabacloud.com/help/en/model-studio/wan-image-to-video-guide
   > "The man looks down at the wooden box on the ground. He bends over, carefully opens the lid, and stares at the
   > contents. His lips tremble and part slightly, his brow furrows, and his eyes widen with a horrified expression."
5. Sound and voice formulas — prompt guide, https://www.alibabacloud.com/help/en/model-studio/text-to-video-prompt
   > "A small glass ball falls from a table onto a wooden floor, making a "thud" sound in a quiet indoor
   > environment." · "A man is doing a stand-up comedy routine. He says, "Study hard and make progress every day," in
   > a relaxed tone, at a moderate speed, with a clear voice, in American English."
6. Exclusion — wan2.7 reference-to-video example, https://www.alibabacloud.com/help/en/model-studio/wan-video-to-video-api-reference
   > "Keep the characters and the forest scene consistent. Do not add text."

Patterns they teach:
- **Order:** one-line overall description → shots or scene → sound → one short exclusion (1, 2, 6).
- **Timed shots:** `Shot N [a–b seconds] <shot size>:` then content; contiguous 3-second shots (1).
- **Image-to-video = motion + camera:** the camera gets its own sentence with a start and end state (3); the subject
  is not re-described (3, 4).
- **Sentence style:** short sequential sentences, visible micro-expressions and physical consequences (4, 5).
- **Audio:** sound = source + action + ambience (5); voice = line + tone + speed + timbre + accent (5); with a driving
  track, state what the audio consists of (2).
- **Exclusions:** a short imperative sentence, not a list (6). **Length:** 20–90 words.

### 4.1 Text-to-video
Follows patterns: overall line, timed shots with shot size first, audio formula, one exclusion sentence.
```text
<One-line overall description>. Generate a single-shot video. <shot size>, <angle>, <light source + direction>, <tone>.
<Subject with 3–6 visual descriptors> <action with speed/amplitude, at real-time speed> in <scene: background + foreground>, <end state>.
The camera <move, from … to …>. <Sound: source + action + ambience | voice line + delivery | No dialogue. No background music.>
Do not show any text, subtitles, numbers, interface elements, or watermarks on screen.
```
Multi-shot variant: replace "Generate a single-shot video." with "Shot 1 [0–3 seconds] <shot size>: … Shot 2 [3–6
seconds] <shot size>: …".

Worked example (8 s, 9:16, 720p): "A quiet street moment. Generate a single-shot video. Eye-level medium shot, overcast
daylight, soft light, cool tones. A red vintage bicycle leans against a pale stone wall; a grey cat walks along the
top of the wall at real-time speed, pauses beside the handlebar, then hops down and trots out of frame to the right.
The camera holds a fixed position. Sound: soft paw steps, a distant bird, light wind. No dialogue. No background
music. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen."

### 4.2 Start frame (and end frame) to video
Follows patterns: motion + camera only, camera sentence with start and end, driving-audio statement.
```text
Generate a single-shot video. <What moves first, speed>, <then>, <end state>. The camera <from … to …>.
(FLF) The motion ends on the composition of the final frame: <pose/position>.
(Audio) <Who speaks/sings to the uploaded audio>; the audio consists only of <voice/music>, with no other dialogue.
Lighting, clothing and the scene stay as in the first frame. Do not add text.
```
Worked example (6 s, 9:16 `start_image` = a person at a desk holding a phone; `audio_references` = a 6 s spoken line):
"Generate a single-shot video. The person looks up from the phone toward the camera and speaks the line in the audio
with natural lip movement and a small nod, then sets the phone face-down on the right side of the desk, where it
stays. The camera pushes in slowly from a medium shot to a medium close-up. The audio consists only of their voice,
with no music. Lighting, clothing and the room stay as in the first frame. Do not add text."

### 4.3 Reference-to-video
N/A on Higgsfield — `wan2_7` exposes no image or video reference roles [HF]. Use `wan3_0` or `minimax_h3`.

### 4.4 Video edit / extension / motion transfer
N/A on Higgsfield — upstream `wan2.7-videoedit` and continuation are not exposed [HF]. Approximate an extension by
using a clean last frame as `start_image` [INFERRED].

