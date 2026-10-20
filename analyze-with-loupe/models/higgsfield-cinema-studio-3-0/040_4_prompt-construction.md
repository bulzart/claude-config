## 4. Prompt construction

### 4.0 First-party examples and the patterns they teach
Higgsfield publishes no official prompt set for 3.0. The closest first-party material:

1. Higgsfield blog (cinematic tools; snippet captured by search on 2026-09-30; the page now returns
   404): "Cinematic style. A woman from image one walking through a neon-lit Tokyo street from image
   three, holding the umbrella from image two, slow rain, reflections on asphalt, shallow depth of
   field." [HF]
2. Cinema Studio 3.0 announcement: "Write a prompt that describes what you want to happen… Focus on
   the narrative: what the characters do, what the scene communicates, how the action unfolds." [HF]

Patterns:
- The style tag comes first.
- The subject is bound to a reference ("from image one").
- One continuous action, then the environment detail.
- Then the physical and optical cues (rain, reflections, depth of field).
- Comma-separated compact prose, and no camera jargon beyond one optical cue.
- Narrative intent over technical micromanagement.

### 4.1 Text-to-video
```text
<Style/genre cue>. <Subject (Element tag)> <one continuous action with end state> in <setting>, <key physical detail: contact, weight, material>. <Light direction and quality>. <One camera behaviour>. <Sound line if audio on>. No on-screen text.
```
Example: "Cinematic realism. A courier in a rain-darkened jacket sets a heavy wooden crate onto a
loading dock; it lands with a dull thud and settles. Cold overhead sodium light from above, wet
concrete reflecting it. Slow push-in at chest height. Rain hiss and the crate's thud, no dialogue. No
on-screen text."

### 4.2 Start (and end) frame
```text
<What moves first>, then <what follows>, ending <end state that matches the last frame>. <Camera behaviour>. <Light stays consistent with the frame>. <Sound>. No on-screen text.
```

### 4.3 Reference-to-video (Elements)
```text
<<<CHAR>>> <action> with <<<OBJECT>>> <scale/grip>, in <setting>. <light>. <camera>. <sound>. No on-screen text.
```

### 4.4 Edit / extension
N/A on this id.

