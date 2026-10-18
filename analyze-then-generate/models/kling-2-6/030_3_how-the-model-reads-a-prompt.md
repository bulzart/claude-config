## 3. How the model reads a prompt

### 3.1 Recommended prompt structure (ordered elements, formula, length, language, prose vs. lists)

- **Official general formula:** "Scene (Scene Description) + Element (Subject Description) + Movement (Movement Description) + Audio (Dialogue/Singing/Sound Effects/Pure Music) + Other (Style/Emotion/Camera)" [OFFICIAL S1].
- Official examples label blocks `Visual:` and `Dialog:` and put subjects in square brackets (`[Narrator, soft female voice]`, `[ginger cat]`) (§4.0) [OFFICIAL S1].
- "Use quotation marks to clarify sound content"; "Avoid stacking too many elements (e.g., multiple ambient sounds + complex speech)"; "ensure image content matches the text description" [OFFICIAL S1].
- Kling's cross-model blog formula (Subject, Action, Scene, Camera, Lighting & Mood) is compatible [OFFICIAL S5b].
- **Length:** 2–5 sentences for 5 s, up to ~120 words for 10 s dialogue/singing [INFERRED]; ≤2,500 characters [SECONDARY S8]. English or Chinese prompts [OFFICIAL S1].

### 3.2 Subject and identity

- Describe each subject concretely once and reuse the same bracketed label; "Character labels must be unique and consistent" [OFFICIAL S1].
- With a start frame, identity comes from the image; keep text consistent with it [OFFICIAL S1].
- Prefer two speaking characters per clip [OFFICIAL S1; SECONDARY S11].

### 3.3 Action, motion and physical interaction

- One main action with direction, speed and end state; one clip = one continuous shot [HF S3].
- Sounds tied to actions: "[Object: Wooden Door] suddenly [Action: Slams] + [Sound Effect: Bang]" [OFFICIAL S1].
- Hands, grip, final placement and liquids per §3.14 [INFERRED].

### 3.4 Environment, lighting and style

- Scene first, with light direction and time of day ("In an afternoon room, sunlight filters through the blinds, creating striped light spots on the floor") [OFFICIAL S1].
- Ambience: "Scene + Sound Elements + Spatial Reverb" (e.g. "Echo in an Open Hall (Reverb)") [OFFICIAL S1]. Style, emotion and camera go last ("Other") [OFFICIAL S1].

### 3.5 Chronology, timing and multi-shot structure

- One continuous shot, no shot planning [HF S3]; order beats with "first … then … finally"; "First describe the action, then follow with the dialogue" [OFFICIAL S1].
- Numeric timestamps are undocumented for 2.6 [OFFICIAL S1 silent]. 10 s for dialogue or singing; 5 s for one action [OFFICIAL S1]. Multi-shot sequences = one clip per shot, chained by frames [INFERRED].

### 3.6 Camera language and dedicated camera / motion controls

- Explicit directional terms (push in, pull back, pan left, tilt up, tracking shot, static shot), one move per clip [OFFICIAL S5b vocabulary; INFERRED one-move rule].
- API `camera_control` presets are not exposed [HF S2; SECONDARY S10]; describe start framing, move and end framing. Static: "static tripod shot; the camera does not move" [INFERRED].

### 3.7 References (image / video / audio): syntax, roles, what is inherited and what must be excluded

N/A beyond the start frame: no reference roles or Elements [HF S2, S7]. Kling's custom voices (`[Character Name] @VoiceName: 'Dialogue'`) are app-only [OFFICIAL S1].

### 3.8 Start and end frames

- Start frame only; describe what changes; keep text and image consistent; use high-resolution, clean frames [OFFICIAL S1; INFERRED].
- End frame: N/A on Higgsfield [HF S2]; describe the ending pose explicitly or use `kling3_0` with `end_image`.

### 3.9 Audio, dialogue and sound (if supported)

Official formats [OFFICIAL S1]:
- **Single speaker:** "[Man speaking], "Sentence" + Deep + Fast".
- **Multiple speakers:** "[Character A, angrily] says, "Sentence" [Character B, calmly] replies, "Sentence"" — labels unique and consistent; action first: "The black-suited agent slams his hand on the table. [Black-suited Agent, angrily shouting]: "Where is the truth?""
- **Narration:** `Visual: … Dialog: [Narrator, <voice>] …`.
- **SFX:** "Sound Source (Action/Object) + State + Professional Sound Effects". **Ambience:** "Scene + Sound Elements + Spatial Reverb".
- **Singing:** ""Lyrics" + Singing Style + Accompaniment + Emotion". **Rap:** ""Sentence (Rhyming)" + Rhythm Style + Emotion".
- **English casing:** "please use lowercase letters for English words whenever possible. When referring to acronyms or proper nouns, please use uppercase letters".
- **Silence:** `sound:false` [HF S2].

### 3.10 Negative constraints (is there a negative-prompt field on Higgsfield? how to phrase exclusions)

- No negative-prompt field on Higgsfield [HF S2] (Kling's API has one [SECONDARY S8]).
- Positive description first; one short exclusion sentence targeting this clip's risks; for audio say what the soundtrack contains ("only rain and footsteps; no music, no voice") [INFERRED].

### 3.11 Visible text

Policy: **Edit Mode** removes all source text unless the user keeps specific text; **Analyze Mode** may add intentional new text, by default in deterministic post (FFmpeg/libass); reference wording, usernames and watermarks are never copied.

- **(a) Reliability:** no official 2.6 text-rendering claim; Kling introduced "native-level text output" with 3.0 [OFFICIAL S5]. Treat any 2.6 in-frame text as pseudo-text [INFERRED].
- **(b) Clean plate:** clean start frames of captions, handles, watermarks and signage; describe carriers as blank (plain signs, unlabelled packaging, screens with abstract colour); frame text-bearing surfaces out or defocus them; quoted strings only for spoken or sung lines (Kling uses quotes to mark sound content) [OFFICIAL S1]; end with "No captions, subtitles, signage text, logos or watermarks appear." [INFERRED].
- **(c) Intentional text:** not on this model — add in post, or use Kling 3.0 / Seedance 2.5 for scene text [INFERRED]. An approved label already in the start frame may stay; keep motion slow and verify it [INFERRED].
- **(d) Source text in edits:** N/A — no edit mode [HF S2].

### 3.12 Character / identity consistency

- Within a clip: one bracketed label and description per character; prefer two speakers [OFFICIAL S1; SECONDARY S11].
- Across clips: same approved still or previous last frame as `start_image`, identical identity wording [INFERRED]. No Elements on this id [HF S7]. Approved references replace source people by becoming the start frame [INFERRED].

### 3.13 Product and object fidelity (geometry, proportions, labels, scale, handling)

- Put the product in the start frame; "the <product> keeps its exact shape, proportions and colours from the first frame; one <product> only" [INFERRED].
- Gentle motion; no rotations to unseen sides; hand, grip, orientation and final placement described [INFERRED].

### 3.14 Integration and continuity (scale, orientation, contact, grip, occlusion, scene-light inheritance, reflections, shadows, persistent object states across the timeline)

- **Scale / orientation / grip:** "[Barista] lifts the small glass jar with the right hand, fingers around its body, lid toward the camera; it is palm-sized" [INFERRED; bracket pattern OFFICIAL S1].
- **Scene light:** official examples describe light as scene elements ("sunlight filters through the blinds, creating striped light spots on the floor") [OFFICIAL S1]; make inserted objects receive it ("the stripes of light fall across the jar; its shadow lies to the right") [INFERRED].
- **Persistent states:** "the jar stays where it is set down; the lid stays on"; same hand until release [INFERRED].
- **Known failures:** voice attribution with 3+ speakers [OFFICIAL S1; SECONDARY S11]; otherwise undocumented.
- **Across clips:** last frame extracted locally → next `start_image`; "continuing from this exact moment" plus restated positions, hand contents and light; identical ratio, duration and `sound` [INFERRED]. No seed [HF S2].

