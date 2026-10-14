## 3. How the model reads a prompt

### 3.1 Recommended structure
- The prompt is optional in the template path. When used: "write a prompt describing the shot, tone,
  and what the ad needs to show" [HF].
- Keep it to the creative intent; the preset supplies structure, pacing, voice-over and hook.

### 3.2 – 3.10
Not individually controllable: the format preset drives subject handling, action, camera, chronology,
audio and exclusions. Describe only the intent and the order of what must be shown.

### 3.11 Visible text
- (a) Formats may add their own captions or text, and "voiceover and pacing in UGC Videos can vary by
  generation" [HF].
- (b) Request "no on-screen text" in generic mode.
- (c) Add planned text in post (`atp.py captions`).
- (d) Edits: N/A. Run QC with OCR in any case.

### 3.12 Character / identity consistency
Avatars come from the preset or custom library, and supplied character references are not guaranteed
to be used. Approved project characters therefore need other models (Seedance, Kling with Elements).

### 3.13 Product and object fidelity
A product created from a URL or images is the product record. With image-only generic mode, supply
the canonical template image.

### 3.14 Integration and continuity
The engine handles them and they are not controllable. QC the product geometry, hands and object
states carefully on the storyboard.

