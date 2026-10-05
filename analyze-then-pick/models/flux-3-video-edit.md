---
guide: flux-3-video-edit
title: Black Forest Labs FLUX 3 Video Edit (FLUX Video Edit [fast])
provider: Black Forest Labs (BFL)
higgsfield_model_ids: [flux_3_video_edit]
guide_version: 1.1
last_verified: 2026-09-30
catalog_snapshot: higgsfield/catalog-snapshot-2026-09-30.json
documentation_depth: medium
---

# FLUX 3 Video Edit — model engineering guide

> Scope: a prompt-only video-to-video editor for **Edit Mode**. You send one source clip and describe what
> should be different; everything the prompt does not mention "stays as shot". This file covers
> `flux_3_video_edit`, which matches BFL's **FLUX Video Edit [fast]** (`POST /v1/flux-tools/video-edit-v1`,
> FLUX 3 family) [INFERRED from identical behaviour: prompt-only edit, 15 s limit, per-second billing].
> The only operation is editing a supplied clip. There is no text-to-video, no frames, no reference images
> and no extension. /analyze-then-pick renders **9:16 at 720p** (§2.6). In Edit Mode, **no source text may
> survive unless the user keeps it** (§3.11). The live `models_explore` catalog always wins over the
> parameter tables in this file.
>
> Evidence tags: **[OFFICIAL]** provider docs, paper, model card, API reference, first-party prompt
> guide or first-party examples · **[HF]** Higgsfield catalog, MCP tool contract or first-party
> Higgsfield docs · **[SECONDARY]** reputable third-party testing or articles · **[INFERRED]**
> engineering inference that must be verified in use.

## 1. At a glance

- **Positioning.** "Send FLUX Video Edit [fast] a clip and say what should be different. Everything the prompt doesn't mention stays as shot: length, framing, camera, timing and audio all come from the source" [OFFICIAL]. It edits by "remove, add or replace objects, change the setting, restyle, change text or dialogue" [OFFICIAL]. Higgsfield: "Edit a video with a text prompt. Uses the first 15 seconds at most; costs 1 credit per second of the processed clip" [HF].
- **Best for:** Edit Mode clean-up and changes that keep the source's motion, camera and timing:
  - removals, including (by inference) captions and overlays;
  - placed additions;
  - recolours and weather/VFX layers;
  - re-sets with contact surfaces;
  - restyles through materials;
  - blockout → finished scene;
  - length-matched dialogue changes and translation [OFFICIAL].
- **Weaker at / cannot do:**
  - no image input, so an approved person or product cannot be swapped in by reference [OFFICIAL];
  - no masks, no extension [OFFICIAL];
  - output ≤720p at 24 fps [OFFICIAL];
  - dialogue cannot outgrow the original speech [OFFICIAL].
- **Choose this model when** the source's motion and framing are right and the change can be described in words, especially removing overlays. **Choose another model when** a replacement must match approved references (use `gemini_omni_flash_1_1` `mode:"edit"` with `image_references`, or Higgsfield's object-replacement model), or when new footage is needed.

| Operation | How to invoke on Higgsfield | Notes |
|---|---|---|
| Text-to-video / frames / references | N/A on Higgsfield | Use `flux_3_video` |
| Video edit (Edit Mode) | `medias:[{role:"video_references"}]` + prompt | Source ≤15 s; output ≤720p, 24 fps [HF][OFFICIAL] |

## 2. Higgsfield parameter surface

### 2.1 Parameters per model id

| id | parameter | values | default | effect / notes |
|---|---|---|---|---|
| `flux_3_video_edit` | `prompt` | 1–4,096 characters | — | Whitespace is trimmed [OFFICIAL] |
| `flux_3_video_edit` | `folder_id` | string (nullable) | — | "Optional folder to place the generated output in" [HF] |
| `flux_3_video_edit` | `aspect_ratio` | none listed | — | Output follows the source [OFFICIAL][HF] |
| `flux_3_video_edit` | duration, resolution, seed, audio flag, mode | not exposed | — | BFL returns HTTP 422 for "`mode`, `version`, `seed`, `duration`, `resolution`, `aspect_ratio` and `generate_audio`" [OFFICIAL]. Do not send them |

### 2.2 Media roles

| role | what it controls | limits / count | notes |
|---|---|---|---|
| `video_references` | The source clip to edit | Exactly 1 [OFFICIAL] | MP4, ≤15 s, ≤50 MiB, each side ≥160 px, ≥17 frames at 24 fps (about 0.7 s) [OFFICIAL]. Higgsfield uses "the first 15 seconds at most" [HF] |

Values are Higgsfield media UUIDs or completed job IDs (for example a previous pass), never URLs [HF].

### 2.3 Duration, resolution, aspect ratio, audio

- **Duration:** equal to the trimmed source. BFL rejects sources over 15 s ("rejected, not trimmed"); Higgsfield uses the first 15 s [OFFICIAL][HF]. Trim locally so you choose the window.
- **Resolution:** "Sources larger than 720p are downscaled to 720p: the 1920 × 1088 harbor clip came back at 1248 × 704" [OFFICIAL].
- **Frame rate:** 24 fps output [OFFICIAL]. 30/60 fps sources come back at 24 fps; account for this when remuxing [INFERRED].
- **Audio:** "Source audio is carried through unless the prompt asks for a dialogue or sound change. A silent source returns a silent result" [OFFICIAL].
- **Billing:** 1 credit per processed second [HF]. BFL: $0.03 per output second, "a ten second clip costs the same whatever the edit" [OFFICIAL]. Stacked edits in one prompt cost no more [INFERRED].

### 2.4 Call recipes

All in the fixed output format (§2.6): the source is conformed to 9:16 720×1280 and trimmed to ≤15 s before upload.

Single edit or text-removal pass:
```json
{"model":"flux_3_video_edit","prompt":"<EDIT_PROMPT>","medias":[{"value":"<VIDEO_MEDIA_ID>","role":"video_references"}]}
```
Second pass on the previous result (dependent edits):
```json
{"model":"flux_3_video_edit","prompt":"<NEXT_EDIT_PROMPT>","medias":[{"value":"<JOB_ID>","role":"video_references"}]}
```
With an output folder:
```json
{"model":"flux_3_video_edit","prompt":"<EDIT_PROMPT>","medias":[{"value":"<VIDEO_MEDIA_ID>","role":"video_references"}],"folder_id":"<FOLDER_ID>"}
```
Preflight with the same params plus `get_cost: true` [HF]. Upload flow: `media_upload` → HTTP PUT → `media_confirm`; collect via `jobs_wait` [HF].

### 2.5 Parameter gotchas

1. **Pre-trim and pre-reframe** the source (≤15 s, ≥0.7 s, ≥160 px, ≤50 MiB, 9:16) [OFFICIAL + policy].
2. **720p ceiling and 24 fps** [OFFICIAL]. Re-time source audio against the 24 fps output if the pipeline restores it [INFERRED].
3. **One video only.** "image input, audio-only input, masks and extending a clip are not supported" [OFFICIAL].
4. **Untargeted content persists, including text** [OFFICIAL behaviour]. Every overlay to remove must be named (§3.11).
5. **Speech cannot grow** [OFFICIAL].
6. **Moderation.** `Request Moderated` / `Content Moderated` are terminal; reword rather than resubmit verbatim [OFFICIAL].

### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-pick)

| id | params to send | expected output | post-processing | how 9:16 is guaranteed |
|---|---|---|---|---|
| `flux_3_video_edit` | None. There is no aspect or resolution parameter, and sending one is a 422 upstream [OFFICIAL] | Follows the source ratio, length and 24 fps, at ≤720p [OFFICIAL]. For a 720×1280 source, expect 720×1280 or a 704-wide variant such as 704×1248 (BFL's 16:9 720p class is 1248×704) [INFERRED] | `atp.py conform` the output to exactly 720×1280 (scale-to-fill plus minimal crop; never stretch) | **Reframe the source to 9:16 (720×1280) with `atp.py conform` before upload.** The reframe may already crop away edge captions, which leaves less text to remove |

## 3. How the model reads a prompt

### 3.1 Recommended prompt structure (ordered elements, formula, length, language, prose vs. lists)

- **Describe the change.** "An edit prompt describes a change, not a shot. Everything it doesn't mention stays as filmed, so the shortest prompt that names the change is usually the right one, and detail goes where the edit needs it." "Start with the change, then add details that matter to the edit" [OFFICIAL].
- **Structure:** `<imperative verb> <target by visible handle> [placement] [appearance] [action/interaction]`.
- **Stacking.** Independent changes go in separate sentences; BFL stacks up to five: "Remove the orange bucket. Make the apron red. Change the stencil on the crate to read DAILY CATCH. Add a seagull… Make it snow…" [OFFICIAL]. Dependent changes go in separate passes [OFFICIAL].
- **Language and length:** English; 3–60 words [INFERRED from BFL examples].

### 3.2 Subject and identity

Target people by a visible handle ("the fishmonger", "the woman in the grey coat"). Replacement is by description only: "Replace the fishmonger with a woman in her thirties wearing the same yellow apron and grey cap" [OFFICIAL]. **It cannot enforce an approved character reference.** Use it for identity-neutral edits, and route approved-reference replacements to a reference-capable edit model [OFFICIAL + policy].

### 3.3 Action, motion and physical interaction

- **Motion and timing are inherited** [OFFICIAL].
- **Added actions** can interact with existing objects: "A gull swoops down and steals a fish from the crate" [OFFICIAL].
- **Blockouts:** name what each proxy becomes and lock the motion: "Same weave lines, same speeds, same camera overtake" [OFFICIAL].
- **Re-sets:** name "the surfaces the climber touches, so the hands and feet have something to hold" [OFFICIAL].

### 3.4 Environment, lighting and style

- **Setting:** "Replace the harbour behind him with a Mediterranean harbour at midday, bright sun and white buildings" [OFFICIAL].
- **Light:** "Change the desert chase to deep night. Turn on the headlights and add a huge low moon above the canyon" [OFFICIAL].
- **Restyle through materials,** not a style name alone: "Fine velour fibers and sewn seams replace the ink outlines…" [OFFICIAL]. Whole-clip restyles also work: "Make the whole clip a hand-drawn watercolour animation" [OFFICIAL].

### 3.5 Chronology, timing and multi-shot structure

Timing and cuts come from the source. There is no documented time-scoping syntax [OFFICIAL: absent]. Anchor partial edits to visible events ("when the door opens, …") and verify [INFERRED].

### 3.6 Camera language and dedicated camera / motion controls

N/A. "framing, camera, timing… come from the source" [OFFICIAL]. Do not request camera changes [INFERRED].

### 3.7 References (image / video / audio): syntax, roles, what is inherited and what must be excluded

No image, style-video or audio inputs [OFFICIAL]. The single video is the edit source. Everything is inherited except what the prompt changes. Overlays, usernames and watermarks are therefore inherited unless named (§3.11d).

### 3.8 Start and end frames

N/A on Higgsfield.

### 3.9 Audio, dialogue and sound (if supported)

- **Source audio survives by default** [OFFICIAL].
- **Dialogue swap:** `Make him say "Fresh mackerel, four for ten."`. Match the length of the original line; a longer line "kept the first part and cut the rest" [OFFICIAL].
- **Translation:** "Say the same sentence entirely in German, with no English words." [OFFICIAL]
- **Pipeline:** if /analyze-then-pick restores source audio after editing, request no sound changes [INFERRED].

### 3.10 Negative constraints (is there a negative-prompt field on Higgsfield? how to phrase exclusions)

There is no field. FLUX doctrine: replace negation with the positive ("no text" → "clean surfaces, unmarked, blank") [OFFICIAL]. In an editor, removal is itself positive: "Remove the orange bucket." [OFFICIAL]. Use "Remove X" and "Keep Y exactly as it is", not "no X" [INFERRED].

### 3.11 Visible text

Policy: **Edit Mode** means no source text survives unless the user keeps specific text: captions, subtitles, usernames, watermarks, title cards, meme text, stickers, social overlays, UI elements, timestamps, overlay logos, random lettering. Text that is part of an approved real product or interface may stay for fidelity. New text in an edit only when the user asks; otherwise add it in post.

**(a) Reliability.**
- **Rendering:** the FLUX 3 family renders "accurate in-scene text and typography" [OFFICIAL], and this tool retexts physical signage ("Change the stencil on the crate to read DAILY CATCH.") [OFFICIAL].
- **Removal:** BFL shows **no** text-removal example [OFFICIAL: absent]. Removal quality is unverified.

**(b) Clean plate.** In an edit, a clean plate needs explicit removal: "Everything the prompt doesn't mention stays as shot" [OFFICIAL]. Untargeted text is **kept, not dropped**.

**(c) Intentional in-frame text** (only on user request): retext a physical surface with BFL's form `Change the <surface> to read <WORDS>` [OFFICIAL]. New overlay captions go in post.

**(d) Removing source text: most reliable wording** [INFERRED; BFL's "Remove …" pattern plus Higgsfield's first-party removal contract]. Higgsfield's contract reads: "Remove only [target]… and reconstruct the revealed area consistently with its immediate surroundings" [HF].
1. **Reframe first.** Conform to 9:16, then list what text remains. Band captions outside the 9:16 window disappear with the crop.
2. **One removal sentence per group.** Name each element by position and look, and say what is revealed:
   `Remove the white subtitle text along the bottom of the frame, the username in the top-left corner and the semi-transparent watermark in the lower-right corner, and restore the wooden floor and wall behind them.`
3. **Stack only independent content edits in the same prompt.** A content edit in the same area as the text goes in a second pass on the cleaned result [OFFICIAL pass rule].
4. **QC every frame for residue.** Animated or stylized captions may leave ghosts. Re-run the removal on the result once [INFERRED].
5. **When local clean-up or regeneration is better** [INFERRED]:
   - **Local:** small static corner logos or watermarks on plain backgrounds (FFmpeg `delogo`, deterministic, zero credits), and band captions that the 9:16 reframe crops away.
   - **Regenerate:** when text sits over faces or products, or moves across most of the clip, and residue survives one retry. Regenerate the shot in Analyze Mode, or try `gemini_omni_flash_1_1` `mode:"edit"`.

### 3.12 Character / identity consistency

Unmentioned people stay as filmed [OFFICIAL], which is strong protection for identities you keep. Replacements are text-described only [OFFICIAL]. Approved-reference replacement must use another model [policy]. For several clips, reuse identical replacement descriptions and treat the result as approximate [INFERRED].

### 3.13 Product and object fidelity (geometry, proportions, labels, scale, handling)

- **Preserve:** unmentioned products keep their filmed geometry and real labels. Near an edit, add "Keep the <product> and its printed label exactly as they are" [OFFICIAL behaviour + INFERRED].
- **Replace:** by description only ("Replace the mackerel with lobsters") [OFFICIAL]. This cannot reproduce approved canonical geometry, so route to a reference-capable edit model [INFERRED].
- **Add:** give size, look and placement. "Add a lighthouse." landed small and far; the specific prompt landed as described and "stays for the whole clip" [OFFICIAL].

### 3.14 Integration and continuity (scale, orientation, contact, grip, occlusion, scene-light inheritance, reflections, shadows, persistent object states across the timeline)

First-party phrasing, all from BFL's examples [OFFICIAL]:
- **Placement and scale:** "a tall white lighthouse with a red lantern room standing on the end of the harbor wall to the right of the boats".
- **Contact:** "Add narrow metal window ledges at the climber's hand and foot contact points".
- **Grip deformation and reflections:** "The plush compresses gently where the metal claw grips it. Soft arcade lights reflect in the glass."
- **Environmental interaction:** "Make it snow, with flakes settling on the crate and the fish."
- **Kept attributes on a replacement:** "wearing the same yellow apron and grey cap".

Extending those patterns [INFERRED]:
- **Scale:** "the same size as the cup it replaces".
- **Orientation:** "label facing camera".
- **Occlusion:** "behind her hand where she holds it".
- **Light:** "lit by the same warm light from the left as the rest of the scene; its shadow falls right onto the table; a faint reflection in the tabletop".
- **Persistence:** "stays in place for the whole clip", "the lid stays closed", "the glass stays half full".

**Known failures:**
- vague adds land small or far [OFFICIAL];
- over-long dialogue is truncated [OFFICIAL];
- unrequested details can shift. BFL's showcase tells you to "Compare the fish and background details as well as the requested edit" [OFFICIAL];
- 720p softening [OFFICIAL].

**Across clips.** Apply identical wording to every clip of a sequence. Layer dependent changes by passes. Each pass re-encodes at ≤720p, so keep chains short [OFFICIAL + INFERRED].

## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach

Sources: FLUX Video Edit (https://docs.bfl.ai/flux_tools/flux_video_edit) and the Video Editing prompting guide (https://docs.bfl.ai/guides/prompting_video_editing).

1. > Remove the orange bucket.
2. > Add a tall white lighthouse with a red lantern room standing on the end of the harbor wall to the right of the boats.
3. > Change the stencil on the crate to read DAILY CATCH.
4. > Make him say "Fresh mackerel, four for ten."
5. > Replace the cliff with the reflective windows of a high-rise building. Add narrow metal window ledges at the climber's hand and foot contact points. Far below, traffic and illuminated buildings fill a dense city in blue-hour light.
6. > Render this previz chase as a desert convoy pursuit at golden hour: the pillars become ruined highway columns in open dust, the lead car an armored pickup, the chaser a spiked buggy, both trailing dust plumes, heat shimmer. Same weave lines, same speeds, same camera overtake. V8 roar and wind.
7. > Restyle this clip as live-action footage of a claw machine lifting a lavender octopus plush. Fine velour fibers and sewn seams replace the ink outlines. The plush compresses gently where the metal claw grips it. Soft arcade lights reflect in the glass.
8. Stacked independent edits:
   > Remove the orange bucket. Make the apron red. Change the stencil on the crate to read DAILY CATCH. Add a seagull standing on the corner of the crate. Make it snow, with flakes settling on the crate and the fish.

Patterns these teach:
- **Order:** imperative verb first (Remove / Add / Change / Make / Replace / Render / Restyle), then the target by a visible handle, then placement relative to a landmark, then appearance (2, 5).
- **Sentence style:** one short sentence per change. Stacks are separate sentences (8).
- **Locks:** inherited motion is locked explicitly ("Same weave lines, same speeds, same camera overtake") (6).
- **Physics:** contact points for re-sets (5); grip deformation and reflections for restyles (7).
- **Text and speech:** retext as `to read WORDS`, capitals without quotes (3). Speech as `Make him say "…"`, quoted and length-matched (4).
- **Audio:** a trailing sound fragment when sound changes ("V8 roar and wind.") (6).
- **Length:** 3–45 words; detail only where the edit needs it.
- **Exclusions:** none. Removal is written positively as "Remove …" (1).

### 4.1 Text-to-video

N/A on Higgsfield (edit-only; use `flux_3_video`).

### 4.2 Start frame (and end frame) to video

N/A on Higgsfield.

### 4.3 Reference-to-video

N/A on Higgsfield (no image or reference input).

### 4.4 Video edit / extension / motion transfer (only if supported)

Templates follow patterns 1–8.

Edit Mode text removal (always pass 1 when overlays exist):
```text
Remove the <text element 1 by position/look>, the <text element 2> and the <text element 3>, and restore the
<surfaces> behind them. [Keep the <approved product label/UI> exactly as it is.]
```
Example: `Remove the white subtitle text along the bottom of the frame and the username in the top-left corner, and restore the kitchen counter and tiled wall behind them. Keep the printed label on the jar exactly as it is.`

Content edit:
```text
<Imperative verb> <target by visible handle> [<placement relative to a landmark>] [<size, look>] [<contact/grip/
light/reflection detail>]. [<Second independent change>.] [Same <motion/timing lock>.]
```
Worked examples (generic):
- Add: `Add a small grey cat sitting on the windowsill to the left of the plant, watching the person at the desk; it casts a soft shadow on the sill.`
- Replace (text only): `Replace the paper cup in her hand with a plain white ceramic mug of the same size, her fingers around its handle.`
- Re-set: `Replace the parking lot behind the car with a coastal road at sunset; the tires stay on dry asphalt and the car keeps its exact shape and color.`
- Restyle: `Restyle this clip as stop-motion clay animation: visible fingerprints in the clay, slightly stepped motion, soft studio light reflecting on the clay surfaces. Same movements and timing.`
- VFX: `Make it rain lightly, with droplets beading on the car roof and the pavement turning glossy.`
- Dialogue: `Make her say "See you tomorrow, same time."`

## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Source captions, usernames, watermarks survive | Not named; untargeted text persists [OFFICIAL] | Removal pass naming each element (§3.11d); 9:16 reframe first |
| Text residue or ghosting after removal | Animated or stylized captions [INFERRED] | Second removal pass; local `delogo` for static marks; regenerate if it persists |
| Added element lands small or far | Unplaced add [OFFICIAL] | Size, look, landmark placement |
| Floating or sliding subject after a re-set | No contact surfaces [OFFICIAL] | Name the surfaces touched |
| Unrequested detail changes (morphing, slop) | Over-long or shot-describing prompt [OFFICIAL] | Shortest change-only prompt; "Keep <x> exactly as it is"; compare frames |
| Duplicated added objects | No count [INFERRED] | "a single …" |
| Replacement identity or clothing drift | Text-only replacement [OFFICIAL: no image input] | State kept wardrobe ("the same yellow apron…"); route approved identities elsewhere |
| Truncated dialogue | Line longer than the source speech [OFFICIAL] | Match word count and duration |
| Judder or timing mismatch | 30/60 fps source converted to 24 fps [OFFICIAL + INFERRED] | Conform and remux carefully; check duration |
| Rejected source | >15 s (BFL), <0.7 s, side <160 px, >50 MiB [OFFICIAL] | Trim and conform locally |
| Dependent edits conflict | Two dependent changes in one request [OFFICIAL] | Sequential passes |

Dead space, slow motion, speed changes and cuts are inherited from the source, not generated. Fix them in the source cut [INFERRED].

## 6. Model-specific features and controls

- **Everything-else-stays contract** (length, framing, camera, timing, audio) [OFFICIAL].
- **Stackable independent edits** at the same per-second cost [OFFICIAL][HF].
- **Retext signage; swap or translate speech within timing** [OFFICIAL].
- **Blockout → final render** [OFFICIAL].
- **Sequential passes** on the previous result [OFFICIAL].
- **`folder_id`** output folder [HF].

## 7. Model-specific pre-generation checklist

- [ ] Source conformed to 9:16 720×1280 and trimmed to the intended ≤15 s window.
- [ ] Inventory of all remaining source text; every element to remove is named; approved product/UI text protected.
- [ ] Removal is pass 1; dependent content edits come after; independent ones are stacked.
- [ ] Adds give size, look and landmark placement; re-sets name contact surfaces; light, shadow and reflection stated.
- [ ] No approved-reference identity or product swap (reroute if needed); dialogue length-matched; no sound change if source audio is restored.
- [ ] No duration, resolution, aspect or audio params sent; `get_cost` done.
- [ ] Output conformed to 720×1280; QC'd for text residue, unrequested changes, 24 fps timing.

## 8. Sources

- [OFFICIAL] FLUX Video Edit (twelve edits, request parameters, limits, pricing) — https://docs.bfl.ai/flux_tools/flux_video_edit — accessed 2026-09-30
- [OFFICIAL] Video Editing prompting guide — https://docs.bfl.ai/guides/prompting_video_editing — accessed 2026-09-30
- [OFFICIAL] API reference: Edit a video (`/v1/flux-tools/video-edit-v1`) — https://docs.bfl.ai/api-reference/tools/video-edit — accessed 2026-09-30
- [OFFICIAL] FLUX 3 — Video (video-editing section; typography claims) — https://docs.bfl.ai/flux_3/flux3_video — accessed 2026-09-30
- [OFFICIAL] Technical Parameters: working without negative prompts — https://docs.bfl.ai/guides/prompting_unified_technical — accessed 2026-09-30
- [OFFICIAL] BFL documentation index (FLUX Video Edit [fast] in the FLUX 3 family) — https://docs.bfl.ml/llms.txt — accessed 2026-09-30
- [OFFICIAL] BFL release notes — https://docs.bfl.ai/release-notes — accessed 2026-09-30
- [HF] Higgsfield catalog snapshot — higgsfield/catalog-snapshot-2026-09-30.json — accessed 2026-09-30
- [HF] Higgsfield MCP tool contract; first-party edit-prompt contract (removal and reconstruction wording) — higgsfield/first-party/ad-multiplier-prompt-writer.md — accessed 2026-09-30

## 9. Open questions / unverified behaviour

- That `flux_3_video_edit` is BFL's FLUX Video Edit [fast]. Inferred; Higgsfield does not say so.
- Output dimensions for a 720×1280 source: 720×1280 or a 704-wide variant.
- Whether Higgsfield trims to the first 15 s or forwards longer sources that BFL would reject.
- Removal quality for burned-in, animated or stylized captions, stickers, UI overlays and watermarks. No official example exists.
- Whether edits can be reliably time-scoped.
- Whether source audio is passed byte-identical or re-encoded, and whether moderated jobs are billed.
