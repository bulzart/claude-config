## 3. How the model reads a prompt

### 3.1 Structure
a short, operational brief. "Optional, short description" when presets aren't
used [HF]. Say what changes and what stays, not the whole scene.

### 3.2 Identity
Object Swap identifies the target in the source by a unique plain-language anchor
("the white mug in the man's right hand", "the woman in the green jacket"), then binds the
replacement to `@ImageN`.

### 3.3 Action / physics
do not re-direct the action; the source's action is inherited.
- State that the replacement follows the original's position, trajectory, orientation, occlusion
    and contact points.
- If the client asset's size or shape differs, state the real size and grip adaptation.
- Large differences are a documented failure → regenerate instead.

### 3.4 Environment / light
say "matches the scene's lighting direction and colour, casts
consistent shadows and reflections". The source light is inherited.

### 3.5 Chronology
the source timeline governs. For a partial-time swap, name the window ("from
the moment she picks it up").

### 3.6 Camera
inherited. Never ask for new camera moves.

### 3.7 References
several views of the same asset jointly define it; say so ("@Image1 and
@Image2 are the front and side of the same bottle").
- Motion Transfer: `@Image1` = subject identity, optional `@Image2` = scene. Exclude the driving
    video's identity, clothing and background explicitly.

### 3.8 Frames
N/A.

### 3.9 Audio
inherited or none; verify it and restore it locally.

### 3.10 Negatives
there is no field. Use scoped exclusion sentences ("the original object must not
appear in any frame").

### 3.11 Visible text
- (a) Genjutsu preserves untargeted content, so the source's captions, usernames and watermarks
    survive by default [INFERRED from "preserving the rest"].
- (b) **Edit Mode policy removes them.**
    - Remove small static overlays locally first (`atp.py clean --delogo …`).
    - For large captions, add an explicit removal clause to the brief ("Remove all on-screen caption
      text and usernames and reconstruct the background behind them"). Its effectiveness is
      **unverified**: QC with OCR afterwards.
    - If text survives, run the whole edit with Seedance 2.5 `video_edit`, where removal is a
      documented operation.
- (c) N/A.
- (d) See (b).

### 3.12 Identity
a replaced person gets their complete look (face, hair, outfit) from the
reference image. State it, and state that the original person must not appear in any frame
(Higgsfield's exclusion pattern, see `first-party/ad-multiplier-prompt-writer.md`).

### 3.13 Product fidelity
the canonical template image is authoritative for shape, proportions,
silhouette, cap/closure and label.
- "Keep the product's exact shape and proportions from @Image1; do not adopt the original object's
    shape."
- Scale: "the same real-world size as in @Image1: a palm-sized bottle about the length of the hand".

### 3.14 Integration and continuity
say "tracks perspective and shadows across the shot" [SECONDARY
phrasing, see §4.0] and "occluded by fingers exactly where the original was".
- State the persistent states (label faces the camera when the original's front did, the lid state
    matches).

