---
guide: <guide-slug>                      # file name without .md, e.g. seedance-2-5
title: <Model family display name>
provider: <Provider / lab>
higgsfield_model_ids: [<id>, <id>]       # every Higgsfield model id this guide covers
guide_version: 1.0
last_verified: <YYYY-MM-DD>
catalog_snapshot: higgsfield/catalog-snapshot-<date>.json
documentation_depth: high | medium | low # how much first-party prompting documentation exists
---

# <Title> — model engineering guide

> Write the guide as ONE file on this template, then run `python scripts/docs_tool.py split models/<guide-slug>.md`: the file becomes
> an index (this front matter, the scope below and a table of sections) and the sections go to `models/<guide-slug>/`. Steps load
> only the sections they name (`atp-model-guide` has the step → section table), so keep the section numbers below. Delete this note.
>
> Scope: what the model is, which Higgsfield ids this file covers, which operations are available.
> The live `models_explore` catalog always wins over the parameter tables in this file.
>
> Evidence tags: **[OFFICIAL]** provider docs, paper, model card, API reference, first-party prompt
> guide or first-party examples · **[HF]** Higgsfield catalog, MCP tool contract or first-party
> Higgsfield docs · **[SECONDARY]** reputable third-party testing or articles · **[INFERRED]**
> engineering inference that must be verified in use.

## 1. At a glance
- Positioning and generation of the model (1–3 lines, official wording where possible).
- Best for / weaker at.
- Choose this model when … / choose another model when …
- Operations available through Higgsfield (table: operation → how to invoke → notes).

## 2. Higgsfield parameter surface
### 2.1 Parameters per model id
| id | parameter | values | default | effect / notes |
### 2.2 Media roles
| role | what it controls | limits / count | notes |
### 2.3 Duration, resolution, aspect ratio, audio
### 2.4 Call recipes
One JSON `generate_video` `params` object per supported operation, with placeholders
(`<IMAGE_MEDIA_ID>`, `<VIDEO_MEDIA_ID>`, `<JOB_ID>`), exactly as the command should send it — always
in the project's fixed output format (§2.6).
### 2.5 Parameter gotchas
(e.g. ratio locked by the start frame, audio flag naming, ignored parameters, billing basis.)
### 2.6 9:16 / 720p mapping (fixed output format of /analyze-then-pick)
Per model id: the exact params that produce vertical 9:16 at 720p (`aspect_ratio` + the model's own
resolution / quality / mode parameter), the expected output dimensions, and whether deterministic
post-processing is needed (downscale, or scale-to-fill + minimal crop via `atp.py conform`). For
outputs whose aspect follows a start frame or a source video, state how 9:16 is guaranteed (9:16 start
frame, source reframed to 9:16 first). Never stretch.

## 3. How the model reads a prompt
### 3.1 Recommended prompt structure (ordered elements, formula, length, language, prose vs. lists)
### 3.2 Subject and identity
### 3.3 Action, motion and physical interaction
### 3.4 Environment, lighting and style
### 3.5 Chronology, timing and multi-shot structure
### 3.6 Camera language and dedicated camera / motion controls
### 3.7 References (image / video / audio): syntax, roles, what is inherited and what must be excluded
### 3.8 Start and end frames
### 3.9 Audio, dialogue and sound (if supported)
### 3.10 Negative constraints (is there a negative-prompt field on Higgsfield? how to phrase exclusions)
### 3.11 Visible text
(a) how reliably the model renders exact text (official claims vs. evidence); (b) clean-plate
prompting — no captions, subtitles, pseudo-text or watermarks — in the provider's documented phrasing;
(c) intentional in-frame text when reliable (quoting conventions); (d) for edit operations, how to
remove source text and reconstruct the scene. Policy: Edit Mode removes all source text unless the
user keeps specific text; Analyze Mode may add intentional NEW text, by default in deterministic post.
### 3.12 Character / identity consistency
### 3.13 Product and object fidelity (geometry, proportions, labels, scale, handling)
### 3.14 Integration and continuity (scale, orientation, contact, grip, occlusion, scene-light
inheritance, reflections, shadows, persistent object states across the timeline; how this model
phrases counts of multiples, the part and contact point of every use, and restatements after
exits, occlusions and cuts — `reference/anomaly-catalog.md` §3)

## 4. Prompt construction
### 4.0 Official prompt examples and the patterns they teach
3–8 short official / first-party example prompts quoted verbatim with sources, then the engineering
patterns they demonstrate (information order, sentence style, temporal markers, subject vs. camera
motion, camera vocabulary, reference syntax, detail level, length, exclusions, audio/dialogue syntax).
The templates below must follow these patterns.
### 4.1 Text-to-video
### 4.2 Start frame (and end frame) to video
### 4.3 Reference-to-video
### 4.4 Video edit / extension / motion transfer (only if supported)
Each template uses `<placeholders>` and is followed by one short generic worked example
(no real brands, no industry assumptions).

## 5. Strengths, weaknesses and failure modes
| failure mode | typical trigger | mitigation |
Include the model's AI-slop tendencies (dead space, arbitrary slow motion, sudden speed changes,
unmotivated cuts/transitions, morphing, identity drift, duplicated objects, clothing changes) and how
the prompt or parameters prevent each. Also the count and affordance breaks of
`reference/anomaly-catalog.md` (a count that changes after an exit or cut, a product used through a
part with no opening, a later state leaking from a reference) and how this model's wording prevents
them.

## 6. Model-specific features and controls
(multi-shot, genre, speed ramp, draft/finalize, thinking mode, cfg scale, Elements support, variants …)

## 7. Model-specific pre-generation checklist
- [ ] …
- [ ] Counts with numbers, the part and contact point of every use, restatements after exits and
      cuts, one exclusion per product for its own wrong use (`reference/anomaly-catalog.md` §3).

## 8. Sources
- [OFFICIAL] <title> — <url> (accessed <date>)
- [HF] …
- [SECONDARY] …

## 9. Open questions / unverified behaviour
- …
