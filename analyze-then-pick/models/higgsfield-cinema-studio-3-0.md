---
guide: higgsfield-cinema-studio-3-0
title: Higgsfield Cinema Studio Video 3.0
provider: Higgsfield (in-house; underlying model not disclosed)
higgsfield_model_ids: [cinematic_studio_3_0]
guide_version: 1.0
last_verified: 2026-09-30
catalog_snapshot: higgsfield/catalog-snapshot-2026-09-30.json
documentation_depth: low
---

# Higgsfield Cinema Studio Video 3.0 — model engineering guide

> Scope: `cinematic_studio_3_0`, Higgsfield's "most advanced cinema-grade model" in the MCP catalog.
> It does text-to-video, image-conditioned and start/end-frame video, with optional native audio. The
> live `models_explore` catalog wins over the tables here.
>
> Evidence tags: **[HF]** catalog, MCP tool contract or Higgsfield page · **[VERIFIED]** observed in a
> real preflight response on 2026-09-30 · **[SECONDARY]** third-party · **[INFERRED]** verify in use.
> Higgsfield publishes marketing pages and a help-center workflow for this model, but no prompt
> specification. Treat the prompting advice here as conservative defaults.

## 1. At a glance

- **Positioning [HF]:** "Most advanced cinema-grade model" (catalog). Higgsfield's pages describe:
  - a "physics-aware generation engine" ("collisions carry a real sense of weight", fabric and
    environment detail);
  - a "cinematic reasoning system that understands story intent from reference images alone";
  - native audio (sound effects, speech, background music);
  - identity "locked across every frame": "the same face, body proportions, clothing, and features
    throughout the entire video".
- **Underlying model:** not disclosed for 3.0. The web app's Cinema Studio 4.0 "runs on Seedance 2.5"
  [HF]. The 3.0 MCP parameter surface (genre list, resolution tiers up to 4k) matches Seedance 2.0's
  [INFERRED]; do not rely on that.
- **Best for:** cinematic narrative shots with weighty physical action, a strong genre look, and
  consistent characters.
- **Weaker at:** exact choreography from a reference video (no video input), exact text, and fine
  multi-reference control (no `image_references` role; use Elements).
- **Choose it** for premium single-shot or short cinematic beats from a strong first frame or Elements.
  **Choose another model** when you must drive motion from a reference video (Seedance 2.x, Wan 3.0,
  MiniMax H3, Genjutsu), need more than 15 s, or need an edit of existing footage.

| Operation | How to invoke | Notes |
|---|---|---|
| Text-to-video | prompt only | `aspect_ratio:"9:16"`, `resolution:"720p"` |
| Image-conditioned | `medias:[{role:"image"}]` | Generic image input; Higgsfield does not document how strongly it is followed |
| First / last frame | `start_image` (+ `end_image`) | Exact compositions |
| Reusable characters / props / places | `<<<element_id>>>` in the prompt | Elements support Cinema Studio Video 3.0 [HF] |
| Edit / extension | — | Not available on this id |

## 2. Higgsfield parameter surface

### 2.1 Parameters
| id | parameter | values | default | notes |
|---|---|---|---|---|
| cinematic_studio_3_0 | `resolution` | 480p, 720p, 1080p, 4k | 720p | Higher costs more [HF] |
| | `genre` | auto, action, horror, comedy, noir, drama, epic | auto | Cinematic genre hint that shapes camera and colour language |
| | `generate_audio` | bool | **false** | Audio is **off** by default [VERIFIED adjustments]. Set `true` when the concept needs sound; the price did not change in preflight (8 s 720p = 40 credits both ways) |
| | `duration` | 4–15 s | — | Unsupported values are clamped |
| | `aspect_ratio` | auto, 21:9, 16:9, 4:3, 1:1, 3:4, 9:16 | — | |
| | `speedramp` | — | — | **Not supported over MCP**: the preflight reported "Cinema Studio Video 3.0 does not support this parameter" [VERIFIED], although the web UI has 8 speed-ramp presets |

Camera body, lens, focal length, aperture, speed ramp and the Director Panel movement stack are
web-app controls; the MCP does not expose them. Describe camera behaviour in the prompt instead.

### 2.2 Media roles
| role | controls | notes |
|---|---|---|
| `image` | Generic image conditioning | One or more? Not documented; start with one |
| `start_image` | First frame composition | The output follows its framing |
| `end_image` | Last frame composition | Use with `start_image` |

### 2.3 Duration, resolution, aspect, audio
4–15 s; 480p–4k; audio optional and off by default.

### 2.4 Call recipes (fixed 9:16 / 720p)
```json
{"model":"cinematic_studio_3_0","prompt":"<prompt>","duration":8,"aspect_ratio":"9:16","resolution":"720p","genre":"auto","generate_audio":true,"folder_id":"<FOLDER_ID>"}
```
```json
{"model":"cinematic_studio_3_0","prompt":"<motion-and-story prompt that continues from the first frame>","duration":6,"aspect_ratio":"9:16","resolution":"720p","generate_audio":false,
 "medias":[{"value":"<START_FRAME_MEDIA_ID>","role":"start_image"},{"value":"<END_FRAME_MEDIA_ID>","role":"end_image"}],"folder_id":"<FOLDER_ID>"}
```
```json
{"model":"cinematic_studio_3_0","prompt":"<<<CHARACTER_ELEMENT_ID>>> <action> while holding <<<PRODUCT_ELEMENT_ID>>> …","duration":8,"aspect_ratio":"9:16","resolution":"720p","generate_audio":true,"folder_id":"<FOLDER_ID>"}
```

### 2.5 Gotchas
- `generate_audio` defaults to false, unlike most models.
- `speedramp` is silently dropped over MCP. Always read `adjustments` from the `get_cost` preflight.
- **Prompt length.** A third-party skill reports a hard **512-character** prompt limit in Cinema
  Studio's web UI, with ~350–400 visible characters recommended when references are attached
  [SECONDARY]. The MCP limit is unknown. Keep prompts **≤ 500 characters**, and shorter with Elements.

### 2.6 9:16 / 720p mapping
`aspect_ratio:"9:16"`, `resolution:"720p"` → expected 720×1280 [INFERRED from the resolution tier;
confirm with `atp.py qc`]. With `start_image` / `end_image`, supply frames that are already 9:16
(720×1280 or larger at the same ratio). Run `atp.py conform` if the output differs.

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

## 5. Strengths, weaknesses, failure modes

| Failure mode | Trigger | Mitigation |
|---|---|---|
| Prompt rejected or truncated | Long prompts (web limit 512 chars [SECONDARY]) | ≤ 500 chars; move style to `genre` |
| Character role swap | Two tagged characters in one action | Tag only characters that must be exact; hero first |
| Location drift across clips | No persistent location reference | Location Element or start frames from one location plate |
| Unwanted slow motion or dramatic ramping | Genre look plus no tempo cue | State "real-time speed, no slow motion"; `genre:"auto"` for everyday content |
| Dead air at the end | Too little action for the duration | Shorter duration, or an extra beat with an end state |
| Garbled signage | Legible text in the scene | Clean plate + post captions |

## 6. Model-specific features
- Genre presets.
- Physics-aware motion.
- Native audio (off by default).
- Elements support.
- 4k tier (not used; the deliverable is 720p).

## 7. Checklist
- [ ] `aspect_ratio:"9:16"`, `resolution:"720p"`, duration 4–15.
- [ ] `generate_audio` set deliberately.
- [ ] Prompt ≤ 500 characters, subject first, one action with an end state.
- [ ] Elements for recurring characters and products, and start frames at 9:16.
- [ ] Preflight `adjustments` read (speed ramp is dropped).
- [ ] "No on-screen text" unless in-frame text is deliberately planned.

## 8. Sources
- [HF] Higgsfield catalog `models_explore` (2026-09-30); `get_cost` preflights with `adjustments` (2026-09-30).
- [HF] Cinema Studio 3.0 — https://higgsfield.ai/blog/cinema-studio-3 (accessed 2026-09-30)
- [HF] How do I use Cinema Studio — https://higgsfield.ai/creator-hub/help-center/tools-and-workflows/how-do-i-use-cinema-studio (accessed 2026-09-30)
- [HF] show_reference_elements tool description (supported models) — MCP contract, 2026-09-30
- [SECONDARY] OSideMedia higgsfield-ai-prompt-skill, "higgsfield-cinema" — https://openskillindex.com/skills/osidemedia-higgsfield-ai-prompt-skill-higgsfield-cinema (accessed 2026-09-30)

## 9. Open questions
- Output pixel size at 720p 9:16; confirm on the first run with `atp.py qc`.
- How strongly the `image` role conditions the output, and whether several `image` inputs are
  honoured.
- The MCP prompt-length limit.
