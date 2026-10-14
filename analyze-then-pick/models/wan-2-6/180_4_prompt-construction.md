## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach
Verbatim first-party examples (trimmed with […]):

1. Reference-to-video (Wan 2.6 formula) — prompt guide, https://www.alibabacloud.com/help/en/model-studio/text-to-video-prompt
   > "This is a whimsical fairytale scene. character1 jumps and plays on the grass. character2 plays piano under a
   > nearby apple tree. An apple falls on character2's head. character1 points at character2 and says happily,
   > "You're going to become a scientist!"."
2. Two-character dialogue — reference-to-video (2.6) API, https://www.alibabacloud.com/help/en/model-studio/legacy-wan-reference-to-video-api-reference
   > "character1 says to character2: “I'll rely on you tomorrow morning!” character2 replies: “You can count on me!”"
3. Single character — same page
   > "character1 sips milk tea while dancing freestyle to the music."
4. Characters, props and scene as references — same page
   > "Character2 sits in a chair by the window, holding character3, playing a soothing American country folk song
   > next to character4. Character1 says to Character2: “that sounds great”"
5. Text-to-video with dialogue — text-to-video API reference (wan2.6), https://www.alibabacloud.com/help/en/model-studio/text-to-video-api-reference
   > "Shot from a low angle, in a medium close-up, with warm tones, mixed lighting (the practical light from the
   > desk lamp blends with the overcast light from the window), side lighting, and a central composition. […] A fox,
   > wearing a dark brown trench coat and a light gray fedora, sits in a leather chair, […] its mouth clearly moving
   > as it speaks in a smooth, cynical voice: "The case was cold, colder than a fish in winter. […]""
6. Timed shot line — prompt guide
   > "Shot 2 [4–6 s] Hard cut transition, fixed camera position, focusing on the boy's eyes, which are glistening
   > with tears, showing loss and helplessness."

Patterns they teach:
- **Tags as sentence subjects:** `characterN` starts each action sentence; props and even scenes can be characters
  (1, 4).
- **Order (r2v):** scene sentence → one action per character → consequence → dialogue (1).
- **Dialogue:** "character1 says to character2: "…" character2 replies: "…"" — speaker, addressee, colon, quote (2).
- **Order (t2v):** camera/light/composition tags first, light sources in parentheses, then subject, action, mouth
  movement and the spoken line with a voice description (5).
- **Timed shots:** "Shot N [a–b s]" + transition + camera state + content (6).
- **Brevity:** reference prompts are one to four short sentences (1–4); t2v prompts stay under the 1,500-character
  cap (5). No official 2.6 example contains an exclusion list.

### 4.1 Text-to-video
Follows patterns: tags first, light sources in parentheses, mouth + voice description, one closing sentence.
```text
<shot size>, <angle>, <tone>, <lighting with sources in parentheses>, <composition>. <Subject with 3–6 descriptors> <action at real-time speed> in <scene>, <end state>.
The camera <single move | stays fixed>. <Sound: voice line + delivery | SFX | BGM | no background music>.
Do not add text.
```
Worked example (10 s, 9:16, 720p): "Eye-level medium shot, warm tones, soft light (morning sun through a side window),
center composition. A small brown dog in a red knitted sweater trots along a wet cobblestone lane at real-time
speed, stops at a puddle, sniffs its reflection, then shakes water from its paws and sits. The camera tracks slowly
beside it. Sound: light rain, paw splashes, a distant bicycle bell, gentle acoustic guitar. Do not add text."

### 4.2 Start frame (and end frame) to video
N/A on Higgsfield — no frame roles for `wan2_6` [HF]. Use `wan2_7` or `wan3_0`.

### 4.3 Reference-to-video
Follows patterns: scene sentence, one action per tagged character, dialogue with addressee, short.
```text
<Scene/style sentence>. character1, <short visual reminder>, <action with grip/contact>. character2, <short visual reminder>, <state or action>.
character1 says to character2: "<line>". Immediately, character2 replies: "<line>".  (or: No dialogue.)
<Camera: one move or fixed>. <Sound>. Keep each character's appearance exactly as in its reference. Do not add text.
```
Worked example (10 s, 9:16; reference 1 = short video of an approved person, reference 2 = image of a plain ceramic
mug): "A calm kitchen at golden hour, natural realism. character1, the woman in the green cardigan, walks to the
counter and picks up character2, the white ceramic mug, with her right hand around the handle, then takes one slow
sip and sets it back on the counter, where it stays. character2 keeps its exact rounded shape and size. character1
says softly: 'Finally, a quiet morning.' The camera pushes in slowly to a medium close-up. Sound: birdsong outside,
the soft clink of the mug, no music. Keep each character's appearance exactly as in its reference. Do not add text."

### 4.4 Video edit / extension / motion transfer
N/A on Higgsfield — `wan2_6` video references define characters (appearance + voice), not a clip to edit, extend or
clean [OFFICIAL/HF]. Use `wan3_0`.

