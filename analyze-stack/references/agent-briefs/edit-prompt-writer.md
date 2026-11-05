# edit-prompt-writer — agent brief (Stage 5e, Seedance 2.5 edit approach; one agent per source segment; mode `write` | `fix`)

Load first (every time): `LAYOUT.md`, `references\edit-prompt-template.md` (file format, block rules, prompts.json
entry, self-check), `seedance\SEEDANCE-EDIT.md` §3 (how the source and references are cited: `@Video1`, `@ImageN`,
trigger words), §4 (A→B phrasing, official examples, the Higgsfield preservation contract, §4.1 skeleton),
§5 (audio: generate_audio false + mux), §6 (identical wording across segments), §7 (failure modes),
`C:\Users\Bulzart\.claude\skills\sd25-pe\SKILL.md` "Video Editing Template" (sole master, inventory
every visible subject, scope-closure sentence, motion-slot replacement, timeline inheritance, never
re-narrate the source from memory), `references\blending-rules.md`, `references\physics-rules.md`,
`references\continuity-rules.md` §4, and the **Seedance 2.5 Director** bundle (read-only): `seedance\director\references\provider-checks.md`
§10 rows "Edit" and "Multi-reference" (identify source, exact target, interval, requested change, protected
properties, boundary behaviour; a physically consequential edit may require dependent shadows / reflections /
contact / occlusion to change too — flag a preservation demand that contradicts them instead of promising
pixel-exact preservation), `seedance\director\references\continuity-and-causality.md` "Cross-cutting safeguards"
(dependency closure of edits) and `seedance\director\references\prompt-playbook.md` §8 (release gate: re-read the
finished edit prompt as a stranger; blocker / major / polish). SPEC/EDITSPEC numbers and the stack's owner rules win
over the bundle (SEEDANCE-SPEC.md §14).

## Purpose
Write ONE edit prompt for one source segment: what changes (every consequence from the swap map /
edit intent, timed to the segment's own seconds) and what stays exactly as filmed (people, motion,
camera, lighting, audio, timing, other objects and their count, on-screen text), with the product
references cited, the original brand marks removed, identical wording to the sibling segments.

## Inputs
`40-plan\plan.json` (your item: source_file, exact duration, moments, edit_intent_items, references),
`30-decisions\edit-intent.md`, `30-decisions\swap-map.md` (global rules + your moments' entries),
`40-plan\continuity-sheet.md` (your row: product state at start/end; identical image order),
`20-analysis\visual.md` (your shots), `entities.json`, the segment itself `00-input\segments\seg-NN.mp4`
(LOOK at frames: `50-prompts\references\seg-NN-start-<t>.jpg` plus 1 fps frames you extract with
`& $ff -hide_banner -loglevel error -y -i "<seg>" -vf "fps=1,scale=540:-2" "<run>\50-prompts\references\seg-NN-f_%03d.jpg"`),
`30-decisions\answers.json` (Q2e, Q6). `fix`: `60-qa\fixes-round-N.md` (your section) and your current file.

## Outputs
`50-prompts\edit-NN.md` in the template format (header, Attachments with the video first, Platform
parameters, `## Prompt`, `## Continuity`, `## Writer notes`). Passthrough segments are not written by you.

## Method (`write`)
1. LOOK (Read tool) at the segment's frames (start frame + 1 fps) and inventory every visible subject category:
   people, the target product, other products/props, background objects, text carriers; decide per
   category: replace / remove / keep (sd25-pe editing rule). Note where the target is occluded, in
   reflections, or off-screen.
2. Describe the target "as seen" (what, where, held how, when) in the segment's own seconds (0-based).
3. Prompt in this order: `Video edit.` + `Replace only <target as seen> in @Video1 with the product from
   @Image1 (…) and @Image2 (…). Do not copy the background, lighting or surface of @Image1 or @Image2.`
   + single-object sentence; timed lines `0-4s:` … with the swap-map consequences (real-world size, same grip
   and motion path, liquid colour and mixing result, foam/fizz, condensation, reflections, count) and
   `keep everything exactly the same` lines for untouched windows; one operation sentence per additional
   edit-intent item (`Modify only … so that …`, `Remove only …`, `Add only … at …`); `Remove only the <brand
   marks> wherever they appear (…) and reconstruct the revealed surfaces consistently with their immediate
   surroundings.`; the preservation block + the sd25-pe scope-closure sentence verbatim once; the short
   negatives; `The original <product> must no longer appear anywhere in the final video.`
4. Audio: default `generate_audio false`, no audio sentence (the source audio is muxed back); only when
   `edit-intent.md` asks for an audio change → `generate_audio true` + the sd25-pe audio-edit sentences and
   a Writer note on timbre drift. Sounds that should change with the product but cannot (fizz → still
   pour) go to Writer notes as "post-edit SFX".
5. Platform parameters line: `mode video_edit · duration <ceil(source)> · aspect_ratio auto · resolution 1080p ·
   generate_audio false · bitrate_mode high · count 1` + the conform/mux instruction — never in the prompt.
6. Continuity: product state at segment start/end from the sheet; confirm identical wording and image
   order with the sibling segments (the sheet's image order is the law); optional anchor still `@Image3`
   only if the plan says so.
7. Self-check (template §4): trigger first; exactly one `@Video1`; no "reference Video 1"; no extension
   words; ≤ 5 images; ≤ 3,900 characters; no ids/URLs/parameters; every moment's consequences present.

## Method (`fix`)
Apply the routed findings only; keep the preservation block and scope closure verbatim; keep wording
identical to siblings except where the finding requires a change (then say so in Writer notes so the
checker can propagate it); bump `qa rounds`.

## Quality bar
- Every visible subject category is accounted for (changed or explicitly kept); no contradictory change
  (nothing both "replaced" and "kept exactly as filmed").
- Timestamps are the segment's own seconds; nothing is re-narrated from memory.
- The removal covers every brand mark listed in the swap map for these moments, reflections included.

## When evidence is missing
If the target is not clearly visible in your frames, extract more frames (2 fps around the moment)
before writing; if still ambiguous, describe the target by the swap-map moment and note "target partly
occluded at 6-8s" in Writer notes. Never add a change the owner did not ask for.
