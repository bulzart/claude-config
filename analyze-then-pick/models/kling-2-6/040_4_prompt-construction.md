## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach

All from the KLING VIDEO 2.6 User Guide (S1):

- **E1 — single speaker:** "[Man speaking], "Sentence" + Deep + Fast"
- **E2 — two speakers:** "[Character A, angrily] says, "Sentence" [Character B, calmly] replies, "Sentence""
- **E3 — action first:** "The black-suited agent slams his hand on the table. [Black-suited Agent, angrily shouting]: "Where is the truth?""
- **E4 — sound effect:** "[Object: Wooden Door] suddenly [Action: Slams] + [Sound Effect: Bang]"
- **E5 — narration:** "Visual: In a tidy living room, a white robotic vacuum sits in the center, with no clutter around it. Dialog: [Narrator, soft female voice] accompanied by the gentle sound of vacuuming. […]"
- **E6 — ambience:** "In an afternoon room, sunlight filters through the blinds, creating striped light spots on the floor. A [ginger cat] lies on the windowsill. The [ginger cat] breathes slowly, with background sounds of distant birds and rustling leaves."

Patterns these teach [derived from E1–E6]:
- **Order:** scene and light → bracketed subject → action → audio (E5, E6).
- **Labels:** square-bracket tags for speakers and even subjects (`[ginger cat]`), reused verbatim; delivery inside the tag ("[Character A, angrily]") (E2, E6).
- **Blocks:** `Visual:` and `Dialog:` separate picture from sound (E5).
- **Speech:** double quotes around spoken words; voice qualities appended ("+ Deep + Fast") (E1, E2).
- **Causality:** the physical action sentence precedes the line or sound it motivates (E3, E4).
- **Detail level:** short concrete scene sentences; one subject, one action (E6).
- **Exclusions:** expressed positively ("with no clutter around it") (E5).
- **Time:** no timestamps or shots — single continuous moments.

### 4.1 Text-to-video

```text
Visual: <scene: place, time, light direction>. <[Subject label] with concrete features> <one continuous action: first …, then …>. <Camera: one move or static>. <Style/emotion>.
Dialog: [<Speaker>, <tone>] says, "<line>" / <SFX: [Object] <state> + [Sound Effect: …]> / <ambience: scene + sound elements + reverb>.
No captions, subtitles, signage text, logos or watermarks appear.
```
Worked example (10 s, `sound:true`):
```text
Visual: A quiet bakery kitchen before sunrise, warm light from a single pendant lamp above the counter. A [young baker] with a flour-dusted apron and rolled sleeves lifts a tray of bread rolls from the oven with both gloved hands, then sets it on the steel counter. Slow push in from a medium shot to a close-up of the rolls. Cosy documentary mood.
Dialog: The tray lands with a light metallic clatter. [young baker, cheerful and soft] says, "first batch, right on time." Oven hum with a faint echo off the tiled walls.
No captions, subtitles, signage text, logos or watermarks appear; the walls and tray are plain.
```

### 4.2 Start frame (and end frame) to video

```text
Visual: Starting from the first frame, <[subject] action: first …, then …>. <Camera: one move or static>. The <light> keeps falling <direction>; <shadow side>. Keep <identity, product shape and colours, layout> exactly as in the first frame.
Dialog: <audio as in 4.1>.
No captions, subtitles, logos or watermarks appear.
```
Worked example (5 s, `sound:true`):
```text
Visual: Starting from the first frame, the [brown dog] on the porch lifts its head, stands up, stretches its front legs, then trots down the two wooden steps toward the camera and sits on the lawn. Static camera at knee height. Morning sun from the left keeps its shadow on the right. Keep the dog's markings and size, the porch and the lawn exactly as in the first frame; one dog only.
Dialog: Morning birdsong, soft paws on wood, one short happy bark.
No captions, subtitles, logos or watermarks appear.
```
End frame: N/A on Higgsfield [HF S2].

### 4.3 Reference-to-video

N/A on Higgsfield — no reference roles or Elements [HF S2, S7]. Use `kling3_0` (Elements) or Seedance 2.0/2.5.

### 4.4 Video edit / extension / motion transfer (only if supported)

N/A on Higgsfield for `kling2_6` [HF S2]. Extension ≈ chaining the last frame into a new start-frame clip (§3.14); edits → `kling_video_edit` or `seedance_2_5`; motion transfer → legacy `motion_control` (Kling 3.0 Motion Control) or Genjutsu `hf_mult_motion_control` [HF S7]. Two-person dialogue within one 10 s clip (E2/E3 pattern):
```text
Visual: <scene with light>. [<Character A>: description] and [<Character B>: description] <positions relative to an object>.
Dialog: <Character A action>. [<Character A>, <tone>] says, "<line>". <Character B reaction action>. [<Character B>, <tone>] replies, "<line>".
<Camera>. No captions, subtitles, signage text, logos or watermarks appear.
```
Worked example:
```text
Visual: A small repair shop at noon, daylight through the front window on the left. A [grey-haired technician] in a navy work shirt stands behind the counter; a [young customer] in a yellow raincoat stands in front of it holding a folded umbrella.
Dialog: The technician slides a small repaired radio across the counter. [grey-haired technician, calm and friendly] says, "good as new." The customer picks up the radio with both hands and smiles. [young customer, relieved] replies, "thank you, really." Faint street traffic outside.
Static medium shot from the side of the counter. No captions, subtitles, signage text, logos or watermarks appear; the radio and shop walls are unmarked.
```

