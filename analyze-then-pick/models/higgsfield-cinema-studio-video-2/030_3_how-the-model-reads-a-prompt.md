## 3. How the model reads a prompt

### 3.1 Structure
use the Higgsfield order (see §4.0): subject → setting → style → action →
atmosphere. Compact prose. A third-party skill reports a 512-character web limit [SECONDARY]; keep
prompts ≤ 500 characters.

### 3.2 Subject
bind the subject to the hero frame or an Element.

### 3.3 Action
one clear action per beat, with cause → contact → result.

### 3.4 Style
`genre` carries the look; describe the light direction in words.

### 3.5 Chronology
order the beats explicitly. With `multi_shots` in auto mode, write the beats as
"Shot one…, then…" in prose; the model decides the cuts [INFERRED].

### 3.6 Camera
describe one move per shot, or none for locked-off shots. The web Director Panel
stack is not exposed.

### 3.7 References
use Elements or start/end frames. There is no `image_references` role.

### 3.8 Frames
the Hero Frame First approach is the recommended way to control composition, asset
geometry and lighting.

### 3.9 Audio
with `sound:"on"`, state the ambience and action sounds and whether anyone speaks.

### 3.10 Negatives
there is no field. Use short positive phrasing plus one exclusion sentence.

### 3.11 Visible text
- (a) Reliability is unknown, so treat it as unreliable.
- (b) For a clean plate, end with "No on-screen text, captions or logos."
- (c) Add planned text in post with `atp.py captions`.
- (d) Edits: N/A.

### 3.12 Identity
keep the same Element id and wardrobe wording across clips.

### 3.13 Product
put the canonical product into the hero frame at the correct scale; state its size
relative to the hands and that its shape and label stay unchanged.

### 3.14 Integration
state the light direction and shadows on the inserted asset, the contact
points, and persistent states.

