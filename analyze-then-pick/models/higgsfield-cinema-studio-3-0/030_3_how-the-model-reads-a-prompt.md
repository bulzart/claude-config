## 3. How the model reads a prompt

### 3.1 Structure
Higgsfield's guidance for 3.0: "Write a prompt that describes what you want to happen. The cinematic
reasoning engine will interpret your intent… Focus on the narrative: what the characters do, what the
scene communicates, how the action unfolds." [HF]. Higgsfield's general structure advice for its
cinematic tools puts the elements in this order:
1. main subject first,
2. setting,
3. style early,
4. the exact action,
5. atmosphere (lighting, emotion, pacing) last [HF, see §4.0].

Use compact prose, one scene, one main action with an explicit end state, ≤ 500 characters.

### 3.2 Subject and identity
- Name each subject once and bind it to its Element or frame.
- Put the hero subject first. With several `<<<element>>>` tags, the first-mentioned character tends
  to become the protagonist; in action scenes two tagged characters can swap roles [SECONDARY].
  Tag only the characters that must be exact.

### 3.3 Action, motion, physical interaction
- The physics engine is the selling point. State the cause, the contact and the consequence:
  "the door slams against the wall and shudders", "the box lands with a heavy thud and slides a few
  centimetres".
- Keep to one primary action per shot and give an end state.

### 3.4 Environment, lighting, style
- Use `genre` for the global look and describe the light direction and quality in the prompt.
- Avoid stacking contradictory style words; the genre parameter already carries much of the style.

### 3.5 Chronology
- Use short sequential clauses ("first… then… finally…") for 4–15 s.
- Multi-shot planning is not exposed for 3.0 over MCP. For several shots, generate separate clips
  and assemble them.

### 3.6 Camera
- Describe it in words: shot size, angle, one movement, speed, and what it reveals. The web app's
  camera rig is not reachable.
- One camera move per clip.

### 3.7 References
- There is no `image_references` role. Use Elements (`<<<id>>>`) for characters, props and locations.
- Use `start_image` when composition and geometry must be exact.
- `image` is a generic input whose weighting is undocumented.

### 3.8 Start and end frames
- Build them at 9:16 with the client asset already correct in scale, lighting and placement; the
  model animates from them.
- When both are given, write the prompt as the motion that connects them.

### 3.9 Audio
- With `generate_audio:true`, describe the sound in plain sentences (ambience, action sounds,
  whether anyone speaks). If nobody should speak, say "no dialogue".
- Put any spoken line in quotes and attribute it to a visible speaker [INFERRED; general practice].

### 3.10 Negative constraints
- There is no negative-prompt field.
- Phrase exclusions positively ("clean, unbranded surfaces") and keep at most one short exclusion
  sentence.

### 3.11 Visible text
- **(a) Reliability:** exact in-frame text is undocumented and unverified. Assume unreliable.
- **(b) Clean plate:** end the prompt with "No on-screen text, captions or logos." Rely on post
  captions (`atp.py captions`) for planned text in Analyze Mode.
- **(c) Intentional in-frame text:** avoid it. If the scene needs a sign or screen, keep the text
  illegibly distant or render the text-bearing object in the start frame.
- **(d) Edits:** N/A (no source video).

### 3.12 Character consistency
- Use an Element for each recurring character; use the same Element id across all videos of a run.
- Higgsfield claims per-video identity lock [HF]. Cross-video consistency comes from the same Element
  plus a consistent wardrobe description.

### 3.13 Product and object fidelity
- Supply the canonical product as an Element, or place it in a 9:16 start frame at the correct
  scale.
- State its real size relative to the hand or body ("a palm-sized bottle"), its orientation, and
  that its shape and label stay unchanged.

### 3.14 Integration and continuity
- Tie the inserted asset to the scene light: "lit by the same warm window light from the left, soft
  shadow on the table".
- State support and contact: "resting on the counter", "held in the right hand, fingers wrapped
  around the lower half".
- State the persistent states: "the lid stays open", "the glass remains half full".

