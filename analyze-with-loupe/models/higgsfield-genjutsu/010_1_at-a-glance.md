## 1. At a glance
- **Positioning [HF]:** "rebuilds part of a clip without a full reshoot". Object Swap "replaces the
  object or element you specify while preserving the rest of the original footage". Motion Transfer
  "uses the motion from an existing video as a reference, then applies that movement to a new
  character or rebuilt scene".
- **What stays [HF]:** original motion and timing, camera work and framing, shot structure and pacing.
- **Limits [HF]:**
  - one input video of **4–30 s**;
  - up to **30 reference images**;
  - output up to **1080p**;
  - works on AI-generated and filmed footage.
- **Needs full regeneration instead [HF]:**
  - different character actions or performance beats;
  - changes to duration, pacing or shot structure;
  - "object replacements with significantly different sizes/shapes";
  - "new interactions requiring physical contact or movement";
  - "multiple simultaneous changes across the frame".
- **Choose Object Swap** (Edit Mode) when one clearly defined entity must become the client's entity,
  and the replacement has similar size and handling to the original.
- **Choose Motion Transfer** (Analyze or Edit Mode) when the reference's choreography, gesture timing
  or camera move is the valuable mechanism and the subject or scene must be rebuilt with approved
  characters.
- **Choose Seedance 2.5 `video_edit`** instead (see `seedance-2-5.md`) for several simultaneous edits,
  text removal plus a swap in one pass, or a replacement whose geometry differs strongly.

| Operation | Model id | Media |
|---|---|---|
| Object / character / product / garment / location swap | `hf_mult_replace_object` | 1 source video + 1–30 reference images |
| Motion transfer to a new subject or scene | `hf_mult_motion_control` | 1 driving video + reference images (subject, optionally scene) |

