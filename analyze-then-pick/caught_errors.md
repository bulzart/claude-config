# Caught errors: the feedback ledger

One entry per error, with the diagnosis, the cause, the fix and the rule the pipeline learns from
it. **Two sources feed it:**
- **agent** (`--source agent`): an error an agent catches during the run, in QC, the
  pre-generation check or the sync check, that cost a regeneration or survived the retry. The
  agent fixes it in place as always, then records it with the verdict as what was wrong, the
  retry's change as the fix and a general rule.
- **user** (`--source user`): once every video is delivered (generated and edited in CapCut), the
  user is asked for feedback. Whatever they say is wrong, disliked, illogical or unsatisfying is
  recorded with their words verbatim and the video's details, one entry per problem; the same
  holds for feedback in a later session and for Edit Mode's "Needs changes".

A user entry outranks an agent entry on the same point: the user saw what QC passed. The file is **read at the start of
every run** (command A1 / E1): the entries that apply to the run (same mode, model, product family
or anomaly class) go into `<RUN>/20-analysis/caught-errors.md`, every plan names the entries it
applies, every prompt carries their rules in the model's phrasing, and QC checks each applied
entry by id. An entry whose rule is general, or that recurs, is **promoted** into the reference it
belongs to (an anomaly-catalog class, creative-direction, brand-guardrails, text-and-format, the
model guide's failure table) and marked `promoted` with the pointer; the entry stays here as the
record. The build prompt is updated after a promotion. `/update-from-errors analyze-then-pick`
does this for the whole ledger at once: it reads the full pipeline, then every entry, finds the
patterns and their causes, generalises each into a kind (what to achieve, what to avoid, the miss
and its cause, the prompt correction, what worked), checks which ones the pipeline already holds in
that form, rewrites the owning prompting, use-case, dismissal, craft, example and QC sections for
the gaps, promotes the entries it folded in, and logs the pass in `learning-log.md`. When nothing is missing it changes nothing
and says so, with any optional suggestion left for the user to accept.

Write entries with the toolkit, never by hand, so the ids and the format stay parseable:

```
T caught-error add --source <user|agent> --title "<short title>" --video "<video or CapCut project>" --run "<run id>" --mode <analyze-recreate|analyze-create|edit> --model <model id> --product "<client product>" --user "<the user's words, verbatim; user entries only>" --wrong "<what was wrong, diagnosed>" --class "<reference and section>" --cause <prompt|reference|parameter|plan|qc-miss|model-limit|unknown> --fix "<what was done>" --rule "<the general rule, as a kind not an instance>" [--brief <text|file>] [--prompt <text|request.json>] [--qc <text|file>] [--plan <file>] [--delivered <text>]
T caught-error list [--mode …] [--model …] [--class …] [--status open|fixed|promoted] [--grep …] [--rules]
T caught-error set --id CE-003 --status promoted --promoted-to "anomaly-catalog.md §2.14"
```

Fields: **source** (user or agent), **assets** (product and asset paths with key specs),
**params** (model, mode, duration, format, media roles of the failed request), **errors**
(execution errors), **evidence** (checkpoint, time range, sheet path), **verified prompt**,
**prompt change** and **verified** (filled only after a passing regeneration),
**video** (number or CapCut project name), **run**, **delivered** (the CapCut project,
the final file, the credits and the run's QC verdict, read from the video's `result.json`),
**mode**, **model**, **product**,
**user said** (verbatim; the user's words are the evidence; "—" on an agent entry), **what was wrong** (the diagnosis
in pipeline terms: which checkpoint, frame or beat, what the ledger or the plan said), **class**
(the reference and section it belongs to, or `new`), **cause** (prompt, reference, parameter,
plan, qc-miss, model-limit, unknown), **fix** (regenerate with what change, post-fix, none),
**rule** (one line, general, the kind of error and the check that catches it), **status**
(open, fixed, promoted), **promoted to**.

**The video's brief travels with the error.** Every entry carries the context that explains the
cause: the **brief** of that video (the X6 brief, saved as `<run>/40-briefs/video-NN-brief.md`:
concept, why it works, reference pattern, assets, substitutions and placement, main action and
states, counts and use, size, style and camera, text, inserts, sound, model and operation,
adaptation logic, guardrails, caught errors applied), the final **prompt** sent (from the newest
`<run>/50-requests/video-NN*-request.json`), the **qc** verdict with its reasons, and the **plan**
path. With `--run` and `--video` the command finds the brief, the prompt and the plan itself;
`--brief`, `--prompt` and `--qc` take a text or a file when the run is not at hand (a video
delivered in an earlier session, a brief the user pastes). An entry without its brief says "not
recorded" and the command names what is missing. Reading an entry, the diagnosis is checked
against the brief and the prompt: what the plan intended, what the prompt said, what came out.

How agents use it:
- **Analysis and planning:** an entry about a product family, a model or a mode applies to every
  video of that kind in the run; its rule goes into the plan's intent, ledger, prompt and QC
  checkpoints. An entry about creative quality (bland, no hook, a copied scene) goes into the
  ideation and the sharpness gate of the run.
- **Prompting:** the rule is written in the locked model's phrasing, as a positive line plus the
  model's exclusion syntax, like any anomaly-catalog prompt line.
- **QC:** each applied entry is checked by id and written in the verdict ("CE-004: paste test
  passed, 0 signs"; "CE-005: can at 1.05× expected size vs the bottle"). A failed check is a
  regenerate reason when the entry's class says so.
- **Recording, agent:** when QC catches an error that costs a regeneration, the agent records it at
  once with `--source agent` and the data the next run needs, compact rather than long: the
  product and asset paths with their key specs (`--assets`), the failed attempt's request
  (`--prompt <request.json>`, from which the params are read), the execution errors
  (`--errors`: Higgsfield errors, preflight adjustments, moderation, failed jobs), where it shows
  (`--evidence`: checkpoint, time range, sheet path), the verdict as what was wrong, the class,
  the cause and a general rule. Production agents write it themselves; the write is locked and the
  ids stay unique. A check that passed first time is not an entry.
- **The fix is inserted only when it is proven.** The entry's verified prompt stays "pending"
  until the new generation comes back and passes QC; only then does the agent run
  `T caught-error set --id CE-nnn --verified-prompt <the passing request.json> --qc-pass "<the
  passing verdict>"`, which stores the working prompt, the sentence-level change from the failed
  one and the params, and marks the entry fixed. If the retry fails too, the entry stays open with
  no fix, and the second failure is noted in its errors. `--status fixed` is refused without a
  passing verdict.
- **Feeding the next run:** `T caught-error list --digest` gives the incoming agents a compact
  view (product, assets, model and params, class, evidence, what was wrong, errors, rule, and for
  verified entries the prompt change that worked). Plans reuse a verified prompt change in the
  locked model's phrasing; an unverified entry tells only what to avoid.
- **Recording, user:** after everything is delivered, the wrap-up asks the user for feedback.
  Whatever they say is wrong, then or in a later session, is recorded first, with their words
  verbatim and the video's details (CapCut project, final file, brief, prompt, the run's QC
  verdict), before any fix is offered. One entry per distinct problem; a message about three
  videos writes three. Nothing the user reports goes unrecorded.

## CE-001 · 2026-10-08 · Three capsules became one after a walk-past
- **video:** anime Create video (earlier run)
- **run:** reported from an earlier run
- **mode:** analyze-create
- **model:** unknown
- **product:** energy capsules
- **user said:** "in the beginning there were 3 capsules in the desk, the kid in the video continues walking past them and then when it gets back there are only one capsule left (things should be persistent throughout the vide, except in logical reasons such as the guy eats 2 of them energy capsules"
- **what was wrong:** the count of a multiple changed with no visible cause across an occlusion and a return; the ledger tracked only where the product was, not how many
- **brief:** not recorded (reported from an earlier run; briefs were not saved then)
- **prompt:** not recorded
- **qc:** not recorded
- **plan:** not recorded
- **class:** anomaly-catalog.md §2.1 (counts and conservation), §2.5 (object permanence)
- **cause:** plan
- **fix:** the ledger carries counts per event; the prompt restates the number at t=0, each event and the end with a targeted exclusion; QC counts at every checkpoint on 30 fps sheets
- **rule:** every multiple keeps its number except through a visible cause, by the amount it explains; count it at every checkpoint, before and after every exit, occlusion and cut
- **status:** promoted
- **promoted to:** anomaly-catalog.md §2.1, §2.5; generation-system.md §3 invariants; command X1/X2/X4/X9

## CE-002 · 2026-10-08 · Drank from the side of the lid with no spout
- **video:** anime Create video (earlier run)
- **run:** reported from an earlier run
- **mode:** analyze-create
- **model:** unknown
- **product:** flip-top straw bottle
- **user said:** "the mom fills his kid bottle with the milk and the kid in the video starts drinking from it … instead of drinking from its outing pipe it start drinking from the other way where the pipe is not present at all (the pipe stands on the left and it drinks from the right where there is not hole at all)"
- **what was wrong:** a use beat went through a part with no opening; the product had no affordance sheet, so the prompt never named the spout, the flip-open step or the contact point
- **brief:** not recorded (reported from an earlier run; briefs were not saved then)
- **prompt:** not recorded
- **qc:** not recorded
- **plan:** not recorded
- **class:** anomaly-catalog.md §2.2 (openings and use), §2.3 (preparation)
- **cause:** plan
- **fix:** affordance sheet per product in the registry; use beats written as initial state → operation on the named part → result with the contact point and one targeted exclusion; QC densifies every use beat
- **rule:** every use goes through the object's real opening after its preparation step, with a named contact point; the affordance sheet is the authority
- **status:** promoted
- **promoted to:** anomaly-catalog.md §1, §2.2, §2.3; assets-and-substitution.md §2; command A2b/X2/X9

## CE-003 · 2026-10-08 · Tossed paper flew through the plastic bottle
- **video:** Create video (previous day)
- **run:** reported from an earlier run
- **mode:** analyze-create
- **model:** unknown
- **product:** plastic bottle
- **user said:** "the character tosses a paper and it goes just through our product, even though the product is a plastic object and the paper should not be able to travel through it"
- **what was wrong:** a moving thing passed through the product; the plan had no path row for the toss relative to the product and the prompt no solidity exclusion
- **brief:** not recorded (reported from an earlier run; briefs were not saved then)
- **prompt:** not recorded
- **qc:** not recorded
- **plan:** not recorded
- **class:** anomaly-catalog.md §2.14 (solidity, collision, occlusion)
- **cause:** prompt
- **fix:** path rows and occlusion notes in the ledger; every path written relative to the product (past it on a named side, or onto it with the consequence) plus the solidity exclusion; 30 fps QC at every pass-near, landing and hit; no post-fix
- **rule:** solid things exclude each other; every thrown, dropped or passing thing gets its path relative to the product and its consequence, and QC checks silhouettes, depth order and consequence at full frame rate
- **status:** promoted
- **promoted to:** anomaly-catalog.md §2.14; generation-system.md §3 invariants; command X1/X2/X4/X9

## CE-004 · 2026-10-08 · Can on the dresser looked pasted in
- **video:** Create video, bedroom POV scene
- **run:** reported from an earlier run
- **mode:** analyze-create
- **model:** unknown
- **product:** Celsius Peach Vibe can
- **user said:** "the can doesnt blend with the room environment, lights and props and even looks like a edit placement in photoshop and not a real product render"
- **what was wrong:** the can carried its reference photo's lighting, exposure, sharpness, pose and camera angle into a warm dim room: brighter and cooler than the nearest white object, flat front light, no contact shadow, packshot pose squared to the lens, drawn straight-on while the camera looked up, crisper than the plate, alone on the dresser's edge
- **brief:** not recorded (reported from a screenshot of an earlier run; the frame showed a POV caption, a boy in the foreground and the can on a dresser about 2.5 m back beside a water bottle)
- **prompt:** not recorded
- **qc:** not recorded
- **plan:** not recorded
- **class:** anomaly-catalog.md §2.15 (blend)
- **cause:** reference
- **fix:** the reference scoped to shape, proportions, colours and label with "do not use its lighting, exposure, background, shadow or camera angle"; the prompt states the room's light on the product, its contact shadow like the neighbour's and the scene's camera angle; the anchor touches or is partly occluded by something; the eleven-sign paste test in QC
- **rule:** a placed product is rendered in the room's light from the scene's camera, never with its photo's; QC measures the eleven signs of a paste on one frame at rest and one in use
- **status:** promoted
- **promoted to:** anomaly-catalog.md §2.15; generation-system.md §4b.4, §9; command X2/X9

## CE-005 · 2026-10-08 · Can rendered two to three times its real size
- **video:** Create video, bedroom POV scene (same as CE-004)
- **run:** reported from an earlier run
- **mode:** analyze-create
- **model:** unknown
- **product:** Celsius Peach Vibe can
- **user said:** "the can's size proportions are way off (it is so big) if they get calculated in comparison with the distance and the size,width and other details of the can"
- **what was wrong:** a 15.7 cm can about 2.5 m from the camera filled over an eighth of the frame height and stood taller than the 22 cm bottle beside it, about 2.75× its expected size; the plan had no size reckoning (dimensions, depth, lens, neighbour)
- **brief:** not recorded (same frame as CE-004)
- **prompt:** not recorded
- **qc:** not recorded
- **plan:** not recorded
- **class:** anomaly-catalog.md §2.7 (scale and proportion)
- **cause:** plan
- **fix:** real dimensions in the registry; a size reckoning per product per shot (depth, lens, expected fraction of the frame, ratio to a named neighbour, size ladder, constancy) in the plan and the prompt; `T scale` on a frame at rest, one in use and the last; over 25 % regenerates with no post-fix
- **rule:** a product's size in the frame is reckoned from its real dimensions, its distance, the lens and a named neighbour, never guessed, and measured after generation
- **status:** promoted
- **promoted to:** anomaly-catalog.md §2.7 (retry rewritten 2026-10-10: on a listed model limit wording is not a lever); scripts/atp.py scale; generation-system.md §4b.1b, §4b.2, §5, §8, §9, §10; wan-3-0.md §3.14, §5; command A2b/X1/X2/X4/X9

## CE-006 · 2026-10-08 · Exam paper glitched at the top left under the carton
- **video:** 14
- **run:** 20261006-002423-05
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Neurogum 9-piece carton, Wintergreen
- **user said:** "video video-14-preview (2) is bad because the paper glitches at the top left from the 6th second"
- **what was wrong:** in the top-down writing shot the carton was placed on the sheet's top-left corner; from about 6 s, while the hand wrote, the sheet corner under the carton doubled and warped: two surfaces fighting for the same space (a solid pack resting on a deformable sheet the hands move). QC sampled the shot at 5 fps and missed it
- **brief:**
  ```text
  Video 14 of Neurogum — "How did you do on your math test?" → "where is the x" → "here"  (Neurogum, Recreate of V12 `Video-39568.mp4`)
  Concept: the reference recreated with the Neurogum product in the scene; the same joke, timing and original audio.
  Reference pattern: V12 (3 clip(s); inserts: 0).
  Characters/assets: C11; product: 9-piece pack.
  House approach: none (no examples).
  Model & operation: wan3_0_prime reference-to-video recreate (≈); c1 3s, c2 15s, c3 4s; 9:16 720p; audio off (original restored) · est. 66 credits.
  Fidelity: Video 1 = the silent own-content segment padded to the integer duration; the action script is written out in order; sync-check after the merge.
  CapCut project: 06_Oct_2026_v14 (via T capcut-name --video 14).
  Details: 40-briefs/video-14-plan.md · text: 40-briefs/video-14-text.json
  ```
- **prompt:**
  ```text
  [Core Task] Recreate Video 1, a handheld top-down view of a test sheet on the same desk, with only these changes: the person's hand, the name on the sheet, a plain marker, and one gum carton lying on the desk. The person is the man in Image 3 (fair, lightly freckled skin, a dark olive-green zip-up jacket); use only him, not the field, sky or backpack. Only his hand and forearm (and at the start his knee) are visible, in the olive-green sleeve; his hand performs exactly the movements of the hand in Video 1, on the same frames. Image 1 is the front view and Image 2 an angled view of the same product: Neuro Energy & Focus Gum, Wintergreen, the 9-piece carton. It must match Images 1 and 2 exactly: same shape, proportions, colours, layout, logo and printed text; never mirrored, flipped or redesigned. It is a small matte paperboard carton, about 7.5 cm wide, 7.5 cm tall and 1.6 cm deep (nearly square, palm-sized, a finger thick), turquoise, with lighter aqua wave shapes, the navy Neuro logo at the upper left, a teal GUM panel at the upper right, a teal Wintergreen tag, the large navy Energy & Focus title and 9 Pieces | Dietary Supplement along the bottom; no band along its bottom edge. There is only one such carton in the whole scene. In this shot the carton lies flat, face-up, on the black desk mat at the upper LEFT of the image frame, to the LEFT of the test sheet's top-left corner and near the left frame edge, with a clear strip of black mat between the carton and the paper: it never touches, overlaps or covers the sheet. It is turned a little, its artwork readable from above, with a soft contact shadow in the warm daylight. It belongs to this desk although Video 1 has no gum; it stays exactly there the whole time and nobody touches it: the hand and the marker stay to the right of it, and the marker is set down on the sheet, never on the carton. Keep everything else from Video 1 unchanged: the camera position, framing, lens and camera movement; the desk, light and background; every hand movement, in the same order, at the same moments and at the same real-time speed. Video 1 is used only for the camera, framing, timing, every movement, the desk and the sheet; do not inherit any overlay text, graphics, smudges or blurred patches from it. Any blurred band or grey blotch near the top of Video 1 is an erased caption: shelf, mat and clean white paper continue there, sharp, with no text. The handwriting on the sheet belongs to the scene and stays as in Video 1, except the name on its first line. The test sheet is one single flat white sheet with four straight edges and a clean, sharp top-left corner; it stays rigid and flat in every frame, its edges never double, stack, bend, curl or warp, and nothing lies on top of it. [Plot Summary] The white sheet carries the handwritten lines 'Name: Sam' (a neutral first name in the same handwriting, never the name written in Video 1) and 'Date: Friday', the question '1- Where is the x?' and a right triangle with sides labelled 4cm, 2cm and x; a black desk mat and wooden desk edges surround it. A plain black marker with no brand name or lettering lies on the mat to the RIGHT of the sheet. 1. His hand comes in from the bottom-RIGHT of the image frame and picks up the marker, and the camera moves in close over the sheet. 2. A long, hesitant hover: the marker tip hangs just above the question with only tiny thinking movements, not touching the paper, for a long while. 3. Only then he slowly draws a circle around the x in the question and an arrow from it down to the x of the triangle. 4. He circles the x on the triangle and slowly writes the word 'here' beside it; every mark stays on the paper. 5. He sets the marker down on the sheet, his hand leaves the frame to the RIGHT, and the camera rises back to the wider view of the desk, the carton still lying at the upper LEFT. [Audio Style] No dialogue. No background music. No sound effects. [Camera & Core Constraints] Handheld top-down view exactly as in Video 1; real-time speed; warm daylight. One continuous top-down shot to the very end: the last split second of Video 1, a cut to a front view, is not part of this clip. [Negative Prompts] no double or stacked paper edges, no second sheet, no bent, curled or warping paper, no overlap between the carton and the sheet, no subtitles, no captions, no overlay text, no blurred or smeared patches, no second gum carton, no pouch or bag, no mints, no mirrored or reversed lettering on the carton, the only lettering is the handwriting on the sheet and the carton's own printed artwork exactly as in Images 1 and 2, no other name on the sheet, no extra brand names, no new writing besides the circles, the arrow and 'here', no extra fingers, no scale drift, no slow motion, no added camera movement, no added, skipped, repeated or reordered actions.
  ```
- **qc:** not recorded
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261006-002423-05\40-briefs\video-14-plan.md
- **class:** anomaly-catalog.md §2.14 (solidity, collision, occlusion)
- **cause:** prompt
- **fix:** c2 regenerated with the carton on the bare desk clear of the sheet and the sheet locked flat and still under the hand; delivered as 08_Oct_2026_v14-2
- **rule:** never place a product on, or overlapping, paper, cloth or any thin sheet that hands move or write on; put it on the bare surface beside it, say the sheet stays flat, and densify QC on that contact region for the whole shot
- **status:** promoted
- **promoted to:** anomaly-catalog.md §2.14, §2.16; generation-system.md §4b.1b; command X1/X4/X9

## CE-007 · 2026-10-08 · Big pouch used where the small package fits
- **video:** 15
- **run:** 20261006-002423-05
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Neurogum Extra Strength pouch, then 6-piece carton
- **user said:** "for video-15-preview (2) use the small package"
- **what was wrong:** the placement used the large 90-piece Extra Strength stand-up pouch in a casual phone-and-couch scene where the small carton reads more naturally. In the redo, Wan 3.0 Prime rendered the closed 6-piece carton about 1.5x its real size and twice put it into the source's pick-up beat in place of the bottle; the user accepted attempt 2 as is
- **brief:**
  ```text
  Video 15 of Neurogum — "…then you hear this sound:" desk reaction  (Neurogum, Recreate of V21 `Video-95282.mp4`)
  Concept: the reference recreated with the Neurogum product in the scene; the same joke, timing and original audio.
  Reference pattern: V21 (1 clip(s); inserts: 1).
  Characters/assets: C03; product: pouch.
  House approach: none (no examples).
  Model & operation: wan3_0_prime reference-to-video recreate (≈); c1 7s; 9:16 720p; audio off (original restored) · est. 21 credits.
  Fidelity: Video 1 = the silent own-content segment padded to the integer duration; the action script is written out in order; sync-check after the merge.
  CapCut project: 06_Oct_2026_v15 (via T capcut-name --video 15).
  Details: 40-briefs/video-15-plan.md · text: 40-briefs/video-15-text.json
  ```
- **prompt:**
  ```text
  [Core Task] Recreate Video 1 as the same one-take vertical phone video, with only these changes: the man, and one TINY closed gum carton, coaster-sized (7.5 cm), standing at the back of the table next to his phone, never touched. The man is the person in Image 3, adopting facial features, hairstyle, skin tone, build and clothing from Image 3 (short dark hair, light beard, navy jacket over a black tee); use only the person from that photo, not its background or objects. He performs exactly the movements, gestures, expressions and mouth movements of the person in Video 1, on the same frames; do not inherit that person's appearance. Image 1 is the front and Image 2 an angled view of the same product: Neuro Energy & Focus Gum, Spearmint, the small 6-piece carton, closed. It matches Images 1 and 2 exactly, never mirrored or redesigned: a thin, almost square matte turquoise carton, closed, with the Neuro logo, green GUM panel, green Spearmint tag, the navy Energy & Focus title and 6 Pieces | Dietary Supplement. Exactly one such carton stands upright on the white table at the LEFT of the image frame, at the back of the table as far from the camera as the water bottle, its printed front toward the camera, fully inside the frame; it belongs to this scene although Video 1 has no gum. His black smartphone lies flat and dark on the table right beside the carton as a size reference: the carton is only about half as long as the phone, and the phone never moves or lights up. It is a background prop only: untouched from the first frame to the last; nobody touches, holds, turns or looks at it; his hands touch only the water bottle. It takes the same soft room light, with a soft contact shadow. It is TINY at its real size, 7.5 cm wide, 7.5 cm tall and 1.6 cm deep: half the length of the phone, far smaller than his head, its top only a third of the way up the water bottle; it occupies only a small corner of the frame. The clear plastic water bottle he drinks from stays, with no label at all, just a blue cap. Keep everything else from Video 1 unchanged: camera position, framing and lens; room, furniture, light and background; every movement, gesture, head turn, gaze, expression and mouth movement, in the same order, at the same moments and at real-time speed. Inherit no text, graphics or smudges from Video 1; his jacket and tee are plain. [Plot Summary] 1. He sits at a white table facing the fixed phone camera and tilts the clear water bottle up to his mouth with the hand on the RIGHT side of the image frame, taking a quick drink with his eyes on the lens. 2. Right after the drink he lowers the bottle and stands it upright on the table at the bottom-RIGHT of the image frame, partly cut off by the frame edge. 3. He lets go of it for only a brief moment, his hand still resting beside the bottle, glancing around. 4. While his hand is still beside it, he takes the same WATER BOTTLE again (never the carton), holds it at chest height and turns it slightly in his fingers, glancing down at the bottle, for a little over a second; the carton stays standing in its corner, untouched. 5. He sets the bottle back down on the table at the bottom-RIGHT of the image frame. 6. Only now comes the long calm stretch, the longest part: he sits completely still with a faint, blissful smile, eyes half-closed, both hands resting motionless on the table away from the bottle, the carton and the phone; the bottle is not lifted or touched again until the very end. 7. Suddenly his smile drops, his eyes widen, he whips his head toward the RIGHT side of the image frame and his hand grips the bottle on the table. 8. The image then fades quickly to pure white, exactly as Video 1 ends, and stays white. [Audio Style] No dialogue. No background music. No sound effects. [Camera & Core Constraints] Fixed phone camera as in Video 1, eye level, framing him from mid-chest up; one continuous take; real-time speed; every action starts and ends on the same frames as in Video 1. Exactly one gum carton, one phone and one bottle in the scene; the carton keeps its place, tiny size and artwork in every frame; the bottle is lifted exactly twice, never a third time. [Negative Prompts] no hand on the carton, no picking up, holding, turning or presenting the carton, no looking at the carton, no oversized carton, no carton taller than a third of the bottle, no subtitles, captions or on-screen text, no blurred or smeared patches, the only lettering is the carton's own printed artwork, no second package, no open carton, no mirrored lettering, no third lift of the bottle, no hand on the phone, no label on the water bottle, no identity drift, no face distortion, no extra fingers, no scale drift, no slow motion, no added camera movement, no added, skipped, repeated, delayed or reordered actions.
  ```
- **qc:** not recorded
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261006-002423-05\40-briefs\video-15-plan.md
- **class:** anomaly-catalog.md §2.7 (scale); generation-system.md §4b (natural placement)
- **cause:** plan
- **fix:** r4: closed Spearmint 6-piece carton at real size wording, padded reference; 3 attempts; attempt 2 accepted by the user, delivered as 08_Oct_2026_v15-3
- **rule:** for Neurogum, default to the small closed carton (or the sachet) in casual hand-held scenes; use the pouch only where a large pack fits the scene. A placed product must never take over the source's pick-up or use beat of another object: name the object that is picked up and say the product stays where it was
- **status:** promoted
- **promoted to:** general part (a placed product never takes the source's beat): generation-system.md §4b.1b, anomaly-catalog.md §2.16; the form fits the scene's scale and register: command A7 (then the form)

## CE-008 · 2026-10-08 · Caption with 'mom' made the character read underage
- **video:** 15
- **run:** 20261007-232745-07
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Celsius Peach Vibe can
- **user said:** "for video-15-preview use a different caption instead of "mom" because it makes it seem underage and use a different character too"
- **what was wrong:** the reference's caption ('Mom ... school') was kept almost as written and the youngest-looking character (A04) was cast, so a Celsius energy drink was shown with someone who reads as a minor. The brand targets 18-25 adults
- **brief:**
  ```text
  Video 15 of 22 — CELSIUS — Recreate V15
  Concept: V15 recreated beat for beat with character A04 and the CELSIUS Peach Vibe can.
  Reference pattern: V15 card (timing, beats, inserts at 1.87-3.20, 3.20-4.43).
  Characters/assets: A04 (Image 1); A39.jpg, A38.jpg.
  House approach: none (no examples).
  Substitutions: creator → A04 | Placement: stands upright on the bed at frame-right near his knee, label toward the lens, in the same spot in both shots.
  Main action & states: source beats unchanged; product untouched and persistent.
  Style & camera: as V15, static phone camera, the source's light.
  Text: CapCut layers in the house style, reference wording/positions (see plan).
  Inserts: V15 1.87-3.20, V15 3.20-4.43.
  Sound: original audio restored; inserts with their own sound.
  Model & operation: wan3_0_prime reference-to-video (≈ recreate from Video 1), 5 s → trim 4.767 s, 9:16 720p, audio off, thinking on · est. 15 credits
  Fidelity: Video 1 = silent own content (motion/camera/timing), action script written out in order, keep-list + exclusions, same duration; sync-check after the merge. Risk: low.
  Adaptation logic: product placed at the analysed anchor; source branding dropped.
  
  
  ## Attempt 2 (2026-10-08, user change) [U]
  - Character: A20 (man, late twenties) instead of A04.
  - Caption rewritten (the reference's "Mom ... school" line reads underage): "When your professor says / attendance is optional today, / so you gotta pretend / it's a hard choice" at the same spot (x 0.50, y 0.27) and timing (0-7.3 s), house style.
  - Inputs re-uploaded to the top-up account; request 50-requests/video-15-a2-request.json; new CapCut project via T capcut-name.
  ```
- **prompt:**
  ```text
  [Core Task] Recreate Video 1 as a real phone-shot vertical clip with only these changes: the person and the product. Video 1 is the motion, camera, framing, cut and timing reference: keep every movement, gesture, head turn, gaze, expression and mouth movement of the person in Video 1 in the same order, at the same moments and at the same real-time speed, and keep the camera, framing, cuts, light, room and background of Video 1. Do not inherit the appearance, clothing, text, captions, stickers, usernames, watermarks or branded items of Video 1. The young man corresponds to Image 1, adopting facial features, hairstyle, skin tone, build and clothing (short dark hair, light stubble, black t-shirt), a man in his late twenties; Image 1 is only this person's identity: not its pose, its cafe table, the glass of water or anything else in it; no glass appears in this video. The young man replaces the person of Video 1 and performs exactly that person's movements. The CELSIUS Peach Vibe can corresponds to Image 2 (front) and Image 3 (second view); both images jointly define one single can, adopting its exact structure, material and colour: a tall slim 12 fl oz aluminium can, 155-159 mm tall and about 55 mm wide (its height almost three times its width, a little shorter than an adult hand from wrist to fingertips), slim straight walls, black tab on the top rim; white body, red-and-silver C-swoosh logo, black CELSIUS wordmark with LIVE FIT, large red PEACH VIBE lettering, teal palm-tree art, silver lower band with a 0 SUGAR badge. Keep its exact silhouette, slim proportions and printed label without deformation and without scale drift. Video 1 has no such item, but the CELSIUS Peach Vibe can is part of this scene from the first frame: it stands upright on the bed at frame-right near his knee, label toward the lens, in the same spot in both shots, at its real size, lit by the scene's own light with a soft contact shadow, untouched and in the same place for the whole clip. Only one exists in the scene. The large framed poster on the wall behind him at frame-right keeps its frame, size and place, but its picture is a generic muted mountain-lake landscape print with no person, no face, no guitar and no lettering; nothing of the poster picture in Video 1 is inherited.
  [Plot Summary] Shot 1 [0-1.87s]: Static low mirrored selfie framing, medium-wide, in a dorm room; projector lights drift slowly across the ceiling from warm to blue-purple. The young man sits cross-legged on the bed, torso slightly hunched forward, the right fist resting under the chin against the lips, elbow on the knee, eyes off to frame-left, brows slightly knit, deadpan.
  Shot 2 [1.87-4.77s]: Hard cut, same framing, same pose; the eyes shift slightly with tiny head movements. The right hand leaves the chin and rises beside the face with the fingers pinched and rolling as if weighing a decision, the head tilts back, the eyes roll up to the ceiling, the lips purse silently; then the hand returns under the chin, eyes back down to frame-left, deadpan, ending on the opening pose.
  [Audio Style] No dialogue. No background music. No sound effects.
  [Camera & Core Constraints] Camera: static throughout. Real-time speed, nothing added, skipped, repeated or reordered, no new gesture, no extra camera move, no re-staging, no new people or background action. No subtitles, captions or other on-screen text; do not reproduce any text, captions, usernames or watermarks from Video 1; the only lettering is the printed label on the can, exactly as in Image 2.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no extra fingers, no duplicate cans, no product deformation, no scale drift, no slow motion, no speed ramps, no other drink or snack brands, no logo stickers, no person or face on the wall poster, no mirrored text
  ```
- **qc:** not recorded
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261007-232745-07\40-briefs\video-15-plan.md
- **class:** brand-guardrails.md (audience and presentation); text-and-format.md §1 (caption rewriting)
- **cause:** plan
- **fix:** attempt 2: character A20 and the caption 'When your professor says attendance is optional today, so you gotta pretend it's a hard choice'; delivered as 08_Oct_2026_v15-2
- **rule:** for any adult-only or energy product, every caption and casting choice must read as an adult (college, work, own place): rewrite wording that implies a parent's authority, K-12 school, curfew or a minor, and cast characters who look 20 or older
- **status:** promoted
- **promoted to:** brand-guardrails.md §2 (Context and audience), §3 (adults only), §5 (Audience)

## CE-009 · 2026-10-08 · Neurogum carton rendered about 1.5x its real size
- **video:** 16
- **run:** 20261006-002423-05
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Neurogum 6-piece carton, then Cinnamon single sachet
- **user said:** "the package is a bit too big because we didn't had the product proportions ... redo the video once again; the product in the generated video doesn't really look as 7-7.5 x 7.5 x 1.6 cm; use the sachet instead"
- **what was wrong:** the first version had no real dimensions for the pack. After product_properties.txt gave 7.5 x 7.5 x 1.6 cm, Wan 3.0 Prime still rendered the carton about 0.9 of the phone's length (about 1.5x real) despite size-anchor wording and a padded reference; the sachet also renders about 1.5x real
- **brief:**
  ```text
  Video 16 of Neurogum — 8 hours of grinding → a TikTok yells → straight back to work  (Neurogum, Recreate of V17 `Video-71316.mp4`)
  Concept: the reference recreated with the Neurogum product in the scene; the same joke, timing and original audio.
  Reference pattern: V17 (2 clip(s); inserts: 1).
  Characters/assets: C05; product: 9-piece pack.
  House approach: none (no examples).
  Model & operation: wan3_0_prime reference-to-video recreate (≈); c1 6s, c2 4s; 9:16 720p; audio off (original restored) · est. 30 credits.
  Fidelity: Video 1 = the silent own-content segment padded to the integer duration; the action script is written out in order; sync-check after the merge.
  CapCut project: 06_Oct_2026_v16 (via T capcut-name --video 16).
  Details: 40-briefs/video-16-plan.md · text: 40-briefs/video-16-text.json
  ```
- **prompt:**
  ```text
  [Core Task] Recreate Video 1 with only two changes: the man, and one small sealed single-piece gum sachet (a flat foil packet smaller than a credit card) lying flat on the table beside his phone, never touched. The man is the person in Image 2, adopting facial features, hairstyle, skin tone, build and clothing from Image 2 (short brown hair, full beard, grey tee); use only the person from that photo, not its background or objects. He is bare-headed, with no cap and no headphones. He performs exactly the movements, gestures, expressions and mouth movements of the person in Video 1, on the same frames. Do not inherit the appearance of the person in Video 1. Image 1 is the front view of the product, a tiny single-piece gum sachet, shown very small in the middle of a white canvas; use Image 1 only for its shape, proportions, colours and the layout of its artwork, not for its size in the frame or its background. It must match Image 1 exactly: same shape, colours and artwork layout; never mirrored, flipped or redesigned. It is a small flat sealed foil flow-wrap sachet, portrait, paper-thin, with crimped seals along its top and bottom edges, light-blue with lighter wave shapes, a navy Neuro logo at the upper left, an orange-red panel at the upper right, a small orange-red tag and a navy Energy & Focus title; at this distance its print is far too small to read, so only its colour layout shows, with no enlarged or legible lettering. Exactly one such sachet lies flat, face-up, on the round polished wood table just to the right of the phone, at the bottom-RIGHT of the image frame, its top edge pointing away from the camera so the front artwork faces up and reads the right way round. It belongs to this scene although Video 1 has no gum; it stays exactly there the whole time and nobody touches it. It takes the warm room light and the cool glow of the monitor, with a soft contact shadow on the wood. Its real size is tiny, like a single tea-bag envelope or a sugar packet: about 5 cm wide and 7 cm tall and paper-thin, smaller than a credit card. It is the smallest object on the table: shorter than the phone is wide, so lying flat it is only about a third of the phone's length and narrower than the phone, much smaller than the computer mouse, and two fingers could cover it; in this wide shot it is just a small patch of light blue beside the phone. It is a soft flat sachet, not a box. Video 1 is the source clip: use it for the camera, framing, timing and every movement. Keep everything else from Video 1 unchanged: the camera position, framing, lens and any camera movement; the room, furniture, light and background; every movement, gesture, head turn, gaze, facial expression and mouth movement, in the same order, at the same moments and at the same real-time speed. Video 1 sets all timing: still moments stay as long as in Video 1, and no action starts earlier or later than in Video 1. Video 1 is used only for the camera, framing, timing, every movement and the room; do not inherit any text, graphics, smudges or blurred patches from Video 1: the smeared areas in Video 1 are where an on-screen caption was removed and are not part of the scene, so show the real scene there, sharp and clean, with no text. [Plot Summary] Seen from behind and to the side, he sits at a round polished wood dining table with a curved ultrawide monitor and a laptop, in an ornate room with a gilded mirror, black twisted columns, a crystal chandelier and red LED cove lighting. 1. He types at the laptop, eyes on the monitor, otherwise completely still. 2. He sits back in the chair with a small stretch. 3. The hand on the RIGHT side of the image frame takes his phone off the table and he holds it in both hands at chest height, looking down at it. [Audio Style] No dialogue. No background music. No sound effects. [Camera & Core Constraints] Fixed camera behind and to the left of him, high-ish wide shot, exactly as in Video 1; real-time speed. The monitor shows only soft, unreadable abstract shapes. [Negative Prompts] no subtitles, no captions, no on-screen text, no text over the picture, no blurred or smeared patches, no usernames or watermarks, the only lettering is the sachet's own printed artwork exactly as in Image 1, no second package, no carton, no box, no pouch, no oversized sachet, no sachet longer than a third of the phone, no sachet as long as the phone, no enlarged or legible print on the sachet, no mints, no mirrored lettering, no readable code or text on the screens, no identity drift, no face distortion, no extra fingers, no scale drift, no slow motion, no added camera movement, no added, skipped, repeated or reordered actions.
  ```
- **qc:** not recorded
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261006-002423-05\40-briefs\video-16-plan.md
- **class:** anomaly-catalog.md §2.7 (scale and proportion)
- **cause:** model-limit
- **fix:** r3 carton with size anchors (still oversized), then r4 with the Cinnamon single sachet NG_EF_CN1PC; delivered as 08_Oct_2026_v16-3, sachet still about 1.5x real, accepted by the user
- **rule:** read the client's dimension file before any prompt; with Wan 3.0 Prime, expect small flat packs under 8 cm to inflate about 1.5x, so name a neighbour of known size in the same plane (phone, hand), measure with T scale on the first output, and when over 25 percent, switch to the smallest real form or a wider shot rather than retrying the same wording
- **status:** promoted
- **promoted to:** wan-3-0.md §5 (small placed product row), §3.14; anomaly-catalog.md §2.7 retry; generation-system.md §4b.1b

## CE-010 · 2026-10-09 · Text layers placed off-centre horizontally
- **video:** 03, 04, 10, 14, 17 and old-run 14
- **run:** 20261007-232745-07
- **mode:** analyze-recreate
- **model:** any
- **product:** all
- **user said:** "edit all videos and make the text be in the center, whether up,down or in the middle but in the center of the screen"
- **what was wrong:** agents copied the reference's horizontal text offset (CapCut posX from -0.32 to +0.40) or slid captions sideways to clear the product, so 6 of the 23 delivered videos had text left or right of centre
- **brief:**
  ```text
  Video 03 of 22 — CELSIUS — Recreate V03
  Concept: V03 recreated beat for beat with character A12 and the CELSIUS Sparkling Watermelon can.
  Reference pattern: V03 card (timing, beats, inserts at none).
  Characters/assets: A12 (Image 1); A42.jpg, A41.jpg.
  House approach: none (no examples).
  Substitutions: creator → A12 | Placement: stands upright on the desk to the right of the laptop, label toward the camera, in the same spot in every shot that shows the desk.
  Main action & states: source beats unchanged; product untouched and persistent.
  Style & camera: as V03, static phone camera, the source's light.
  Text: CapCut layers in the house style, reference wording/positions (see plan).
  Inserts: none.
  Sound: original audio restored; inserts with their own sound.
  Model & operation: wan3_0_prime reference-to-video (≈ recreate from Video 1), 14 s → trim 13.800 s, 9:16 720p, audio off, thinking on · est. 42 credits
  Fidelity: Video 1 = silent own content (motion/camera/timing), action script written out in order, keep-list + exclusions, same duration; sync-check after the merge. Risk: multi-shot cuts and screen content.
  Adaptation logic: product placed at the analysed anchor; source branding dropped.
  ```
- **prompt:**
  ```text
  [Core Task] Recreate Video 1 as a real phone-shot vertical clip with only these changes: the person, the box and the product. Video 1 is the motion, camera, framing, cut and timing reference: keep every movement, gesture, head turn, gaze, expression and mouth movement of the person in Video 1 in the same order, at the same moments and at the same real-time speed, and keep the camera, framing, cuts, light, room and background of Video 1. Do not inherit the appearance, clothing, text, printed packaging or branded items of Video 1. The young man corresponds to Image 1, adopting facial features, hairstyle, skin tone, build and clothing (curly dark hair, round glasses, grey hoodie); Image 1 is only his identity, not its pose, background or objects. He replaces the person of Video 1 and performs exactly that person's movements. The box he carries is a plain matte green cardboard box with no logo, no picture, no printing and no text on any side, unlike the printed box in Video 1. The CELSIUS Sparkling Watermelon can corresponds to Image 2 (front) and Image 3 (second view); both images jointly define one single can, adopting its exact structure, material and colour: a slim 12 fl oz aluminium can, 155-159 mm tall and about 55 mm wide, black tab on top; white body, red-and-silver C-swoosh logo, black CELSIUS wordmark, a watermelon-slice illustration, SPARKLING WATERMELON in red, a dark band with three benefit lines, silver lower band with a 0 SUGAR badge. Keep its exact silhouette, proportions and printed label without deformation or scale drift. Video 1 has no such item, but the can is part of this scene from the first frame: it stands upright on the desk just right of the laptop, near his right hand, label toward the camera, at its real small size, lit by the scene's light with a soft contact shadow, untouched and in that same spot for the whole clip. Only one can exists in the scene.
  [Plot Summary] Shot 1 [0-1.3s]: Static waist-height shot of a bedroom with a wooden armoire and red wall decor, warm light. The young man enters from frame-right walking briskly toward frame-left past the lens, holding the plain green box in both hands at chest height, head turned to frame-left in profile, lips moving as he speaks, and leaves frame-left with motion blur.
  Shot 2 [1.3-2.7s]: Hard cut. Low angle from the desk beside the laptop lid (lid edge at frame-left). He arrives, swings the plain green box down onto the desk at the bottom of the frame, drops into the chair, then sits upright looking down-left at the laptop screen with a calm neutral face, lips finishing the line. Just right of the lid edge, beside his right arm, the can stands on the desk, small and clearly visible, farther from the lens than the box.
  Shot 3 [2.7-6.8s]: Hard cut. Over-the-shoulder shot from behind his right shoulder: the back of his head at frame-left, the green box at lower-left, the open laptop at centre, a window with trees behind in daylight; the can stands just right of the laptop. On the laptop screen the same young man appears as a reviewer, first holding the plain green box up, then holding a black microphone and talking; the screen shows only his video picture, and no words, letters or titles appear on it at any time, unlike Video 1. Near the end his hand slowly rises toward his mouth at the frame-left edge.
  Shot 4 [6.8-9.5s]: Hard cut. Same front angle as shot 2, the box and the can in the same places as in shot 2: his hand clamped over his mouth, eyes wide, staring at the laptop; then the hand slides up to rest on the cheek, the mouth drops open, brows up in distress, tiny head shakes.
  Shot 5 [9.5-11.2s]: Hard cut. The reviewer, the same young man, in a living room (white door, a framed poster top-right) facing the lens, a black microphone held vertically in the right hand near the chin, eyes wide, mouth open, talking and reacting. Static.
  Shot 6 [11.2-13.8s]: Hard cut. Over-the-shoulder again: the laptop shows the reviewer close-up with the microphone, with no words on the screen; his hand is raised to his face at frame-left; the can still stands just right of the laptop; nobody moves.
  [Audio Style] No dialogue. No background music. No sound effects.
  [Camera & Core Constraints] Camera: static in every shot; cuts exactly where Video 1 cuts. Real-time speed, nothing added, skipped, repeated or reordered, no new gesture, no extra camera move, no re-staging, no new people or background action. No subtitles, captions or other on-screen text; do not reproduce any text, captions, screen titles or watermarks from Video 1; the only lettering is the printed label on the can, exactly as in Image 2.
  [Negative Prompts] no subtitles, no on-screen text, no words on the laptop screen, no logo or printing on the box, no watermark, no face distortion, no identity drift, no costume changes, no duplicate cans, no can in the foreground, no product deformation, no scale drift, no slow motion, no other drink brands
  ```
- **qc:** not recorded
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261007-232745-07\40-briefs\video-03-plan.md
- **class:** capcut-assembly.md §3 item 2 (text position); text-and-format.md §3
- **cause:** plan
- **fix:** posX set to 0 on every text layer of the six projects; captions that would then cover the can (videos 04 and 14) moved to the top centre; previews re-burned from the projects
- **rule:** every CapCut text layer is horizontally centred (posX 0, centre alignment); only its height follows the reference (top, middle or bottom); when centred text would cover the product, a face or an insert, move it up or down, never sideways
- **status:** promoted
- **promoted to:** capcut-assembly.md §3 step 2; text-and-format.md §1, §3 step 4; production-agents.md hard rule; command item 6 + Never; build prompt (house text style)

## CE-011 · 2026-10-09 · Neuro carton 1.7x too big next to the bottle even with p40 padding and one-fifth wording
- **source:** agent
- **video:** 17
- **run:** C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261008-235833-08
- **delivered:** not recorded
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Neuro XE Spearmint 9pc carton
- **user said:** — (caught by the agent during the run)
- **what was wrong:** Attempt 1 (p40 refs, size recipe, 'quarter of the bottle') carton 163 px vs expected ~95 px = 1.71x vs the 27 cm bottle it stands against; attempt 2 (tighter: 'one fifth of the bottle, one eighteenth of the frame, pack of gum') came out 1.78x, i.e. no better. Placed against a large neighbour the carton also stood in front of the bottle base, nearly frontal, with a cyan glow on the table.
- **brief:**
  ```text
  Video 17 of 18 - Recreate of V08: Neuro XE Spearmint carton, placement leaning on the bottle
  Concept: the reference recreated as itself (same scenario, action, camera and timing), faces swapped to the supplied character(s), the product integrated (placement leaning on the bottle).
  Why it works: Communicates: "you try and take a break as an entrepreneur" - the phone he escapes to lectures him; deadpan loop. Why Neuro: focus at work, calm and wry (G24), product just there (G23); the small closed Neuro carton by the bottle is the 'work fuel' that stays (CE-007: small carton in a phone beat; it never takes the phone's pick-up beat). Kept [E]: one locked take around an insert; two impacts. Adapted: man -> K18; the black bottle is kept as unbranded decor (it is not a competitor: G12 not hit; no drink is replaced); the Bible/App Library part of the insert dropped (G3 does not bind N, G8 foreign UI; dropped for both versions for consistency); TikTok UI cleaned.
  Reference pattern: V08 (see 20-analysis/cards/V08.md and families.md)
  Characters/assets: see the plan sec 2.3; Higgsfield media ids in 30-assets/uploads.json and the request file.
  Substitutions: Placement; the bottle stays as in the source (unbranded, never replaced).
  Counts & use: | entity | count | state |
  |---|---|---|
  | carton | 1 | upright on its long edge, leaning against the black bottle's side, table left foreground, ~0.7 m, closed, label 30 deg; unchanged across the cut |
  | bottle | 1 | left foreground, untouched, no readable brand |
  Paths: phone and lid hand paths on the right side, away from the pouch; the left hand steadies the laptop base at ~6.0 without reaching the carton; the carton is never picked up (the phone is).
  Size: Carton 7.5 cm at ~0.7 m, 26 mm eq -> ~7.7% (~99 px); neighbour at the same depth: the black bottle (~27 cm) it leans on -> ~0.28 of its height ('about a quarter'). Wan 3.0 Prime tends to inflate small packs about 1.5x (CE-009): T scale on the first output. Constant.
  Guardrails: G16 (the client's real renders are the only product references; no AI-invented packaging: QC compares the label geometry and any morphed text is a regenerate reason), G17/G18 (Extra Strength, Peppermint or Spearmint, 9-piece carton, closed (small package, CE-007); the 6-pack box never appears), G19/G27 (closed package, nobody takes a piece, no blister shown), G23/G24 (the product just happens to be there; calm, wry register), G25 [U] (no sleeping/drained scene), G11/G21 (no numbers or claims in any text layer; the carton's own 100MG band is the only number), G12 (no competitor shown or replaced), G13/G14 (an adult supplied character, no ambassador likeness), G22 (phone-shot, everything in focus). The TikTok UI/username on the kept insert is removed (platform UI, 9b).
  Caught errors applied: CE-006 (a product is never placed on or overlapping paper: bare surface or a solid prop; sheets stay flat; QC densifies the contact region for the whole shot), CE-007 (small closed carton by default in casual scenes; the pouch only where a large pack fits; a placed product never takes over the source's pick-up beat: the object picked up is named and the product stays), CE-008 (adult framing in captions and casting), CE-010 (text centred), CE-001 (the package count stays 1; nothing taken), CE-002
  Text: As in the scene.
  Inserts: TikTok clip 5.50-14.03 of Video-64073.mp4; clean the UI band; split point 4.8.
  Sound: Own audio restored per segment; the insert keeps its speech.
  Fidelity approach: the silent own-content source as video_references (the most preserving input Wan 3.0 Prime offers: recreate-from-video-reference), exact duration rounded up, fidelity lock + the action script written out in the prompt; risks to fidelity or sync: lip-sync and exact timing are not guaranteed by this model; sync-check after the merge.
  Model & operation: video-17-request.json: wan3_0_prime reference-to-video, 9 s, 9:16 720p, generate_audio false, 4 media - est. 27 credits (3 credits/s, preflight read: no adjustments)
  Adaptation logic: One generation of 9 s (own 8.1 s; hard cut at 4.8). Insert: the TikTok advice clip 5.50-14.03 (with speech; its advice line 'do so much work it would be unreasonable for you not to be successful' is a hustle opinion, not a product claim: G11 not hit). Credits 27.
  ```
- **prompt:**
  ```text
  [Core Task] Generate single shot. The man corresponds to Image 1, adopting only his facial features and hairstyle; man replaces only the person in Video 1 and keeps the beige t-shirt; do not use the background, props or clothing of Image 1.  Use Video 1 for his movements, expressions, gaze, the camera framing, the room, the laptop, the phone, the large black insulated bottle and the timing; do not reproduce any text, captions, usernames or watermarks from Video 1. The carton corresponds to Image 2 and Image 3, which jointly define the same carton and generate only one instance, adopting only its structure, material, colours and printed label (a small flat closed sky-blue matte paperboard carton 7.2 cm wide, 7.5 cm tall and 1.6 cm thick, the dark-blue Neuro wordmark top-left, an EXTRA STRENGTH GUM badge top-right, a Spearmint pill tag, 'Energy & Focus' in blue type and a navy band reading 100MG OF NATURAL CAFFEINE); in Image 2 and Image 3 the carton is deliberately small in the frame and keeps that small scale; do not use the framing of Image 2 or Image 3, nor their lighting, exposure, background, shadow or camera angle.
  [Plot Summary] Locked phone camera at chest height about one and a half metres away, slightly high, three quarters from the left, a dark wooden dining table, white walls, a ceiling fan, grey chairs and a plant, bright even daylight from the right. Video 1 has one hard cut at about 4.8 s of its length; keep it at the same moment with the same framing. He sits with his right hand on the keys of an open silver laptop and his left forearm on the table, eyes on the screen; his right arm extends to the top edge of the lid and pulls it down in one motion, the lid meeting its base with a click; he sits back, his shoulders drop and both hands come to rest on the table edge and his lap, head tilted down; his right hand slides right and lifts a white phone from the table, brings it to chest height and his left hand joins; head down, his thumb scrolls. Cut. He still holds the phone in his right hand at chest height, head down; his right hand flicks the phone up and to the left of the screen, past the bottle and above the carton without touching either, and out of frame; his right hand returns, fingers hooking under the laptop lid with a thud, lifts it open while his left hand steadies the base; both hands type, eyes on the screen, a neutral resigned face. The large black insulated bottle, plain with no lettering or logo, stands untouched at the left foreground. A small closed Neuro Energy & Focus Extra Strength Spearmint carton stands upright on the table at the left foreground, leaning back against the side of the black bottle, about seventy centimetres from the lens. The carton is tiny, like a pack of gum: only about one fifth as tall as the black bottle it leans on, so its top reaches just the lowest part of the bottle's body, far below the bottle's handle; it is about as wide as three fingers, much shorter than his palm is long, about one eighteenth of the frame height and much smaller than his head, and it keeps that small size in every frame. Its label is turned about thirty degrees away from the lens, lit by the daylight from the right, soft shade on its left and a soft contact shadow on the wood; it stays on that spot for the whole clip; it is never the object he picks up: the white phone is the only thing he lifts and flicks away, and the carton stays where it was; his left hand never touches the carton. Phone-shot look, everything in focus. Real-time speed. No dialogue.
  [Camera & Core Constraints] Keep every movement, gesture, expression, gaze and mouth movement of the person in Video 1 on the same frames, the props and how they are handled, the camera framing and handheld feel, the light, the room and the timing of Video 1 unchanged; no added, skipped, repeated or reordered action, no new gesture, no extra camera move, no re-staging, no new people, no change of pace. There is exactly one carton, one bottle, one phone and one laptop, not duplicated, not vanished, not deformed, small and constant in size with no scale drift; the carton stays closed; nothing passes through it. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen; the only lettering is the printed label on the Neuro package, exactly as in Image 2.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no scale drift, no slow motion, no self-inserted cut points, no added or skipped action, no six-pack box, no blister card, no opened carton, no loose gum pieces, no gum in anyone's mouth, no second package, no studio lighting on the package, no shallow depth of field, no glow, no can, no drink brand or lettering on the bottle, no earphones, no oversized carton, no carton taller than his hand is long, no carton larger than his head, no carton in his hand
  ```
- **qc:** not recorded
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261008-235833-08\40-briefs\video-17-plan.md
- **class:** anomaly-catalog.md §2.7
- **cause:** model-limit
- **fix:** none: one diagnosed regeneration with tighter size wording did not shrink it; best picture (attempt 1) delivered flagged RESIDUAL FAILURE
- **rule:** For a small flat pack (carton) wan3_0_prime ignores size wording and p40 padding when the pack sits next to a larger neighbour (1.7x); words cannot fix it. Use a smaller-pad reference (p25 or lower), a pre-built start/last frame at the reckoned pixel size, or the single sachet form, instead of another wording retry.
- **status:** open
- **promoted to:** wan-3-0.md §5 (small placed product row), §4.0 item 10 (failed size wording, not verified), §9 (untested levers); stays open as a model limit

## CE-012 · 2026-10-09 · Sachet stands upright against the writer's forearm; forced placement
- **source:** user
- **video:** 14
- **run:** C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261008-235833-08
- **delivered:** CapCut project 09_Oct_2026_v14 · clean C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261008-235833-08/60-outputs/video-14/clean.mp4 · credits 117 · run QC: RESIDUAL FAILURE: size. a1 carton 1.50x, a2 carton 1.50x (tighter wording + refs padded to 18%), a3 sachet fallback ~1.3-1.5x vs distance reckoning (width about palm-wide); delivered a3 flagged, no more spend. CE-006/003/001/002/004/008/010 pass.
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Neuro Energy & Focus Peppermint single sachet (fallback for the XE carton)
- **assets:** not recorded
- **user said:** "it seems like forced, no one leaves a gum sachet standing at his harm while he writes though"
- **what was wrong:** The delivered product (fallback a3, a flat foil sachet) is rendered standing upright on its edge against the writer's forearm on the exam table. A flat sachet cannot stand by itself, and nobody sets a pack right against the arm of someone writing an exam. The plan anchored the product at the writer's elbow/forearm zone of a close, locked shot and QC checked only size, count, closed state and paper overlap, never the physical posture of the object or whether a person would really leave it there. The sachet fallback kept the carton's 'stands upright' anchor wording.
- **brief:**
  ```text
  Video 14 of 18 - Recreate of V05: Neuro XE Peppermint carton, placement on the marble table
  Concept: the reference recreated as itself (same scenario, action, camera and timing), faces swapped to the supplied character(s), the product integrated (placement on the marble table).
  Why it works: Communicates: "what teachers think would happen if they let us listen to music in an exam" - the VO reads answers like a track; deadpan. Why Neuro: students under sustained mental load (A456 sec 4), calm and wry (G24), the product 'just happens to be there' (G23). Kept [E]: the take, the VO, writing, the page flip. Goal/job [I]: awareness; the carton on the marble, noticed; share line "this is why we can't have music". Adapted: man -> K3; the caption box and shirt print removed from the plate; the package is Extra Strength Peppermint, closed (hero per G18, form per G27).
  Reference pattern: V05 (see 20-analysis/cards/V05.md and families.md)
  Characters/assets: see the plan sec 2.3; Higgsfield media ids in 30-assets/uploads.json and the request file.
  Substitutions: Placement; the closed hardcover notebook (a solid, not a sheet hands move: CE-006) is the smallest native element that lets a 1.6 cm-thick carton stand readable; hands busy: no use beat (G19/G27 satisfied: no piece is taken).
  Counts & use: | entity | count | state |
  |---|---|---|
  | carton | 1 | upright on its long edge, propped against a closed hardcover notebook on the bare marble, lower right, ~0.6 m, closed, label 30 deg; never moved |
  | sheets | 1-2 | flipped at 9.2-10.4 over the left edge, away from the carton |
  Size: Carton 7.5 cm at ~0.6 m, 26 mm eq -> ~9.0% (~116 px) (T scale --product-cm 7.5 --distance 0.6 --lens 26); neighbour: the exam sheet (29.7 cm) -> ~0.25 of its length; his palm is ~8.5 cm wide, the carton 7.2 cm wide -> slightly narrower than his palm. Oversize check: a carton taller than ~0.4 of the sheet is a regenerate reason.
  Guardrails: G16 (the client's real renders are the only product references; no AI-invented packaging: QC compares the label geometry and any morphed text is a regenerate reason), G17/G18 (Extra Strength, Peppermint or Spearmint, 9-piece carton, closed; the 6-pack box never appears), G19/G27 (closed package, nobody takes a piece, no blister shown), G23/G24 (the product just happens to be there; calm, wry register), G25 [U] (no sleeping/drained scene), G11/G21 (no numbers or claims in any text layer; the carton's own 100MG band is the only number), G12 (no competitor shown or replaced), G13/G14 (an adult supplied character, no ambassador likeness), G22 (phone-shot, everything in focus).
  Caught errors applied: CE-006 (a product is never placed on or overlapping paper: bare surface or a solid prop; sheets stay flat; QC densifies the contact region for the whole shot), CE-007 (small closed carton by default in casual scenes; the pouch only where a large pack fits; a placed product never takes over the source's pick-up beat: the object picked up is named and the product stays), CE-008 (adult framing in captions and casting), CE-010 (text centred), CE-001 (the package count stays 1; nothing taken), CE-002
  Text: CapCut layer as in the scene.
  Inserts: none.
  Sound: Original VO audio restored.
  Fidelity approach: the silent own-content source as video_references (the most preserving input Wan 3.0 Prime offers: recreate-from-video-reference), exact duration rounded up, fidelity lock + the action script written out in the prompt; risks to fidelity or sync: lip-sync and exact timing are not guaranteed by this model; sync-check after the merge.
  Model & operation: video-14-request.json: wan3_0_prime reference-to-video, 13 s, 9:16 720p, generate_audio false, 4 media - est. 39 credits (3 credits/s, preflight read: no adjustments)
  Adaptation logic: One generation of 13 s (own 12.07 s). Credits 39. No inserts.
  ```
- **prompt:**
  ```text
  [Core Task] Generate single shot. The man corresponds to Image 1, adopting only his facial features and hairstyle and light stubble; man replaces only the person in Video 1 and keeps the plain white t-shirt without lettering and the white over-ear headphones; do not use the background, props or clothing of Image 1.  Use Video 1 for his movements, expressions, gaze, the camera framing, the room, the exam sheets and the timing; do not reproduce any text, captions, white caption boxes, usernames or watermarks from Video 1. The sachet corresponds to Image 2 and generates only one instance, adopting only its structure, material, colours and printed label (a small flat closed sky-blue foil flow-wrap sachet about 5 cm wide, 7 cm tall and 1 cm thick with crimped seals at the top and bottom, the dark-blue Neuro wordmark top-left, a mint GUM badge top-right, a Peppermint pill tag, 'Energy & Focus' in large blue type and '1 Piece | Dietary Supplement' below it); do not use the lighting, exposure, background, shadow or camera angle of Image 2.
  [Plot Summary] Locked phone camera at eye level, medium shot, a white marble table filling the lower third, a bright room corner with a white door and warm lamp light from the upper left. He sits turned about forty degrees toward the left of the frame with his head tilted left, listening to his headphones, a blue pen in his right hand resting on an exam sheet and his left hand flat on the table; he turns his head down to the sheet and squares his torso; he writes with small right-hand strokes, glancing up and to the left once, and keeps writing; then both hands lift the right edge of the sheet and flip it over to the left, his left hand smoothing it down, and it lands on the same spot; he writes again with a glance to the right of the frame. A single closed sealed Neuro Energy & Focus Peppermint sachet stands upright with its bottom edge on the bare marble at the lower right of the frame, leaning back against the side of a closed black hardcover notebook that lies flat beside it (the sachet never sits on top of the notebook), to the right of his writing forearm and the exam sheets, clear of every sheet, about sixty centimetres from the lens in the same plane as the exam sheet, the blue pen and his left palm, a tiny object only about one fifth as tall as the exam sheet is long, clearly shorter than the blue pen, narrower than his open palm and no taller than his palm is wide, filling only about one thirteenth of the frame height, its label turned about thirty degrees away from the lens, lit by the same warm lamp light with a soft highlight on its upper left and a soft contact shadow on the marble falling to the right like the sheets' shadows; it stays on that spot for the whole clip, he never touches it, the exam sheets lie flat and keep their shape except when he flips the top one, and the flipped sheet stays on the left and never reaches the sachet. Phone-shot look with everything in focus and no shallow depth of field. Real-time speed. No dialogue. No background music.
  [Camera & Core Constraints] Keep every movement, gesture, expression, gaze and mouth movement of the person in Video 1 on the same frames, the props and how they are handled, the camera framing and handheld feel, the light, the room and the timing of Video 1 unchanged; no added, skipped, repeated or reordered action, no new gesture, no extra camera move, no re-staging, no new people, no change of pace. There is exactly one sachet, tiny, smaller than his hand and never growing, sealed and never opened, not duplicated, not vanished, not deformed, no scale drift; nothing passes through it. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen; the only lettering is the printed label on the Neuro sachet, exactly as in Image 2; do not reproduce any text, captions, usernames or watermarks from Video 1.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no scale drift, no cut-out edges, no slow motion, no speed ramps, no self-inserted cut points, no added or skipped action, no oversized or giant package, no six-pack box, no blister card, no opened sachet, no torn foil, no loose gum pieces, no gum in anyone's mouth, no chewing, no second package, no studio lighting on the package, no glow, no shallow depth of field, no white caption box, no text on the shirt, no phone
  ```
- **params:** model=wan3_0_prime · duration=13 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=video_references, image_references×2 · request=video-14-a3-request.json
- **errors:** none
- **evidence:** deliverables/previews/video-14.mp4 at about 5 s (sachet upright against the right forearm, beside the notebook)
- **qc:**
  ```text
  RESIDUAL FAILURE: size. a1 carton 1.50x, a2 carton 1.50x (tighter wording + refs padded to 18%), a3 sachet fallback ~1.3-1.5x vs distance reckoning (width about palm-wide); delivered a3 flagged, no more spend. CE-006/003/001/002/004/008/010 pass.
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261008-235833-08\40-briefs\video-14-plan.md
- **class:** generation-system.md §4b.1 (anchor logic), anomaly-catalog.md §2.14 (solidity) and §2.15 (placed, not pasted)
- **cause:** plan
- **fix:** regenerated with the verified prompt; see prompt change
- **verified prompt:**
  ```text
  [Core Task] Generate single shot. The man corresponds to Image 1, adopting only his facial features and hairstyle and light stubble; man replaces only the person in Video 1 and keeps the plain white t-shirt without lettering and the white over-ear headphones; do not use the background, props or clothing of Image 1.  Use Video 1 for his movements, expressions, gaze, the camera framing, the room, the exam sheets and the timing; do not reproduce any text, captions, white caption boxes, usernames or watermarks from Video 1. The sachet corresponds to Image 2 and generates only one instance, adopting only its structure, material, colours and printed label (a small flat closed sky-blue foil flow-wrap sachet about 5 cm wide, 7 cm tall and 1 cm thick with crimped seals at the top and bottom, the dark-blue Neuro wordmark top-left, a mint GUM badge top-right, a Peppermint pill tag, 'Energy & Focus' in large blue type and '1 Piece | Dietary Supplement' below it); in Image 2 the sachet is deliberately small in the frame and keeps that small scale; do not use the framing, lighting, exposure, background, shadow or camera angle of Image 2.
  [Plot Summary] Locked phone camera at eye level, medium shot, a white marble table filling the lower third, a bright room corner with a white door and warm lamp light from the upper left. He sits turned about forty degrees toward the left of the frame with his head tilted left, listening to his headphones, a blue pen in his right hand resting on an exam sheet and his left hand flat on the table; he turns his head down to the sheet and squares his torso; he writes with small right-hand strokes, glancing up and to the left once, and keeps writing; then both hands lift the right edge of the sheet and flip it over to the left, his left hand smoothing it down, and it lands on the same spot; he writes again with a glance to the right of the frame. A single closed sealed Neuro Energy & Focus Peppermint sachet lies flat on its wide face with its printed label facing up, resting entirely on the bare white marble in the bottom right of the frame, on the near side of the table, nearer the lens than his hands and forearm, where someone sets a sachet of gum down out of the way of their writing. It is fully inside the frame, with a band of bare marble at least as wide as the sachet itself between it and his forearm, hands and the exam sheets; nothing touches it and nobody picks it up. It is about fifty centimetres from the lens, a tiny object about as long as his index finger, narrower than his open palm and much shorter than his palm is long, filling only about one tenth of the frame width, seen from above at a slight angle as a thin flat rectangle, lit by the same warm lamp light with a soft contact shadow on the marble falling to the right like the sheets' shadows; it stays flat on that spot for the whole clip and never slides, tilts, stands up or leans, the exam sheets lie flat and keep their shape except when he flips the top one, and the flipped sheet stays on the left and never reaches the sachet. Phone-shot look with everything in focus and no shallow depth of field. Real-time speed. No dialogue. No background music.
  [Camera & Core Constraints] Keep every movement, gesture, expression, gaze and mouth movement of the person in Video 1 on the same frames, the props and how they are handled, the camera framing and handheld feel, the light, the room and the timing of Video 1 unchanged; no added, skipped, repeated or reordered action, no new gesture, no extra camera move, no re-staging, no new people, no change of pace. There is exactly one sachet, tiny, small and constant in size, never larger than his hand, lying flat, sealed and never opened, not duplicated, not vanished, not deformed, no scale drift; nothing passes through it. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen; the only lettering is the printed label on the Neuro sachet, exactly as in Image 2; do not reproduce any text, captions, usernames or watermarks from Video 1.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no scale drift, no cut-out edges, no slow motion, no speed ramps, no self-inserted cut points, no added or skipped action, no oversized or giant package, no sachet longer than his hand is wide, no sachet larger than his head, no standing, leaning, propped or tilted sachet, no sachet on its edge, no sachet on a sheet, no sachet touching his arm, no notebook, no six-pack box, no blister card, no opened sachet, no torn foil, no loose gum pieces, no gum in anyone's mouth, no chewing, no second package, no studio lighting on the package, no glow, no shallow depth of field, no white caption box, no text on the shirt, no phone
  ```
- **prompt change:**
  ```text
  - do not use the lighting, exposure, background, shadow or camera angle of Image 2.
  + in Image 2 the sachet is deliberately small in the frame and keeps that small scale;
  + do not use the framing, lighting, exposure, background, shadow or camera angle of Image 2.
  - A single closed sealed Neuro Energy & Focus Peppermint sachet stands upright with its bottom edge on the bare marble at the lower right of the frame, leaning back against the side of a closed black hardcover notebook that lies flat beside it (the sachet never sits on top of the notebook), to the rig
  - it stays on that spot for the whole clip, he never touches it, the exam sheets lie flat and keep their shape except when he flips the top one, and the flipped sheet stays on the left and never reaches the sachet.
  + A single closed sealed Neuro Energy & Focus Peppermint sachet lies flat on its wide face with its printed label facing up, resting entirely on the bare white marble in the bottom right of the frame, on the near side of the table, nearer the lens than his hands and forearm, where someone sets a sache
  + It is fully inside the frame, with a band of bare marble at least as wide as the sachet itself between it and his forearm, hands and the exam sheets;
  + nothing touches it and nobody picks it up.
  + It is about fifty centimetres from the lens, a tiny object about as long as his index finger, narrower than his open palm and much shorter than his palm is long, filling only about one tenth of the frame width, seen from above at a slight angle as a thin flat rectangle, lit by the same warm lamp lig
  + it stays flat on that spot for the whole clip and never slides, tilts, stands up or leans, the exam sheets lie flat and keep their shape except when he flips the top one, and the flipped sheet stays on the left and never reaches the sachet.
  - There is exactly one sachet, tiny, smaller than his hand and never growing, sealed and never opened, not duplicated, not vanished, not deformed, no scale drift;
  + There is exactly one sachet, tiny, small and constant in size, never larger than his hand, lying flat, sealed and never opened, not duplicated, not vanished, not deformed, no scale drift;
  - [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no scale drift, no cut-out edges, no slow motion, no speed ramps, no self-inserted cut points, no added or skipped action, no oversized or giant package, no six-pack box, no b
  + [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no scale drift, no cut-out edges, no slow motion, no speed ramps, no self-inserted cut points, no added or skipped action, no oversized or giant package, no sachet longer than
  ```
- **verified params:** model=wan3_0_prime · duration=13 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=video_references, image_references×2 · request=video-14-r2-request.json
- **rule:** A placed product takes a posture its own shape allows (a flat sachet or pouch lies flat; a carton stands on its base or leans on a solid object that is visible in the shot) and sits where a person would really leave it, away from a working hand or arm, on bare surface at the table's far side or edge, never touching the person; QC checks posture, support and the story reason for the spot as its own line, not only size and count.
- **status:** promoted
- **promoted to:** anomaly-catalog.md §2.16; generation-system.md §4b.1b; wan-3-0.md §3.14, §4.0 item 8, §5; command X1/X4/X9
- **verified:** r2 flat-lying single Energy & Focus Peppermint sachet on bare near-side marble: posture/support pass at 30 fps (flat, label up, whole underside on marble, contact shadow, no tilt/float), story pass (set down at the near table edge out of the writing hand's way), size 1.05x, count 1, sealed, never touches arm (2-D marble gap 18-37 px, about 0.2 hand-width, flagged), CE-001/002/003/004/006/007/008/010 pass, sync in_sync (2026-10-09)

## CE-013 · 2026-10-09 · Carton leans on nothing; the planned support never rendered
- **source:** user
- **video:** 15
- **run:** C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261008-235833-08
- **delivered:** CapCut project 09_Oct_2026_v15 · clean C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261008-235833-08/60-outputs/video-15/clean.mp4 · credits 45 · run QC: RESIDUAL FAILURE: carton renders 1.99x its expected size vs her head (a1 2.24x; a2 1.99x with tightened wording and 16% padded refs; a3 sachet fallback 1.83x, no better and non-hero form); constant across cuts; all other checks passed (count 1, closed, never touched, sheet flat, no blister/open/6-pack, OCR clean, small label line garbled)
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Neuro XE Spearmint 9pc carton
- **assets:** not recorded
- **user said:** "it is not correct too because the gum pack seems like it is leaning into something meanwhile there's nothing behind the package that it might've use to be leaning to"
- **what was wrong:** The plan propped the carton at about 60 degrees against a closed hardcover notebook behind and left of the sheet. The model rendered the carton tilted back on the bare desk with only a sliver of a notebook at the far left edge of the frame, so it appears to lean on thin air. QC counted one carton and measured its size, but did not check that every leaning or standing object has a visible, solid support in the same frame, and the contract's 'deliver flagged' path shipped it anyway.
- **brief:**
  ```text
  Video 15 of 18 - Recreate of V06: Neuro XE Spearmint carton, placement on the desk
  Concept: the reference recreated as itself (same scenario, action, camera and timing), faces swapped to the supplied character(s), the product integrated (placement on the desk).
  Why it works: Communicates: "pov: how it feels when your brain gives you a quick peek of the notes with the answer" - recall flash, a streamer meme voices the blank. Why Neuro: exam focus, deadpan (G24), product just there (G23). Kept [E]: POV caption + silent acting + a still flash + a speaking meme insert. Adapted: man -> K22 (woman; G28 balance for Neuro); caption rewritten minimally for G11: "0.1 second" (a number on screen) -> "a quick" (same role, position, timing); shirt lettering removed.
  Reference pattern: V06 (see 20-analysis/cards/V06.md and families.md)
  Characters/assets: see the plan sec 2.3; Higgsfield media ids in 30-assets/uploads.json and the request file.
  Substitutions: Placement; hands busy: no use beat.
  Counts & use: | entity | count | state |
  |---|---|---|
  | carton | 1 | upright on its long edge propped against a closed hardcover notebook, desk left behind-left of the sheet, on bare desk, ~0.7 m, closed, label 30 deg; unchanged across both cuts |
  Path: the raised left hand passes behind and above the carton.
  Size: Carton 7.5 cm at ~0.7 m, 26 mm eq -> ~7.7% (~99 px); neighbour: the sheet (29.7 cm) -> ~0.25 of its length; palm 8.5 cm vs carton 7.2 cm wide. Constant across cuts.
  Guardrails: G16 (the client's real renders are the only product references; no AI-invented packaging: QC compares the label geometry and any morphed text is a regenerate reason), G17/G18 (Extra Strength, Peppermint or Spearmint, 9-piece carton, closed; the 6-pack box never appears), G19/G27 (closed package, nobody takes a piece, no blister shown), G23/G24 (the product just happens to be there; calm, wry register), G25 [U] (no sleeping/drained scene), G11/G21 (no numbers or claims in any text layer; the carton's own 100MG band is the only number), G12 (no competitor shown or replaced), G13/G14 (an adult supplied character, no ambassador likeness), G22 (phone-shot, everything in focus).
  Caught errors applied: CE-006 (a product is never placed on or overlapping paper: bare surface or a solid prop; sheets stay flat; QC densifies the contact region for the whole shot), CE-007 (small closed carton by default in casual scenes; the pouch only where a large pack fits; a placed product never takes over the source's pick-up beat: the object picked up is named and the product stays), CE-008 (adult framing in captions and casting), CE-010 (text centred), CE-001 (the package count stays 1; nothing taken), CE-002
  Text: CapCut layer: the rewritten caption (no number), y_rel 0.66.
  Inserts: Still insert 0.87-1.03 (notes page) and video insert 2.67-7.03 (streamer, with speech) cut from Video-58078.mp4; split points 0.87 and 2.51.
  Sound: Own audio restored per segment; inserts keep their sound.
  Fidelity approach: the silent own-content source as video_references (the most preserving input Wan 3.0 Prime offers: recreate-from-video-reference), exact duration rounded up, fidelity lock + the action script written out in the prompt; risks to fidelity or sync: lip-sync and exact timing are not guaranteed by this model; sync-check after the merge.
  Model & operation: video-15-request.json: wan3_0_prime reference-to-video, 6 s, 9:16 720p, generate_audio false, 4 media - est. 18 credits (3 credits/s, preflight read: no adjustments)
  Adaptation logic: One generation of 6 s (own 5.17 s; hard cuts in own.mp4 at 0.87 and 2.51). Inserts: still 0.87-1.03 and the streamer clip 2.67-7.03 (cut from the reference, with sound). Credits 18.
  
  ## Attempts (production agent)
  - Source re-cut reused from video 07 (media c2e0856f, 5 s, 4.47 s kept); inserts V06-i1-final plus an insert 2 built from V06-i2-final with this videos generated frames fading to/from white.
  - a1 (job e4d19b65, 15 cr): carton refs padded 22
  ## Attempts (production agent)
  - Source re-cut reused from video 07 (media c2e0856f, 5 s, 4.47 s kept); inserts V06-i1-final plus an insert 2 built from V06-i2-final with this video's generated frames fading to/from white.
  - a1 (job e4d19b65, 15 cr): carton refs padded to 22%, 2.24x vs head, rejected. a2 (job 63c67af9, 15 cr): refs padded to 16%, deck-of-cards / one third of her head / under a tenth of the frame wording, 1.99x, still over. a3 (job d870c652, 15 cr): single Energy and Focus Spearmint sachet (A546) fallback, 1.83x, no better and not the hero Extra Strength form (G18). Delivered a2 flagged RESIDUAL FAILURE; a3 kept as alternate.
  - Caption posY -0.24 (y_rel 0.62) so the 3-line block stays above the carton (top at y 0.70).
  ```
- **prompt:**
  ```text
  [Core Task] Generate single shot. The woman corresponds to Image 1, adopting only her facial features and hairstyle; woman replaces only the person in Video 1 and keeps the backwards cream baseball cap and a plain black t-shirt without any lettering; do not use the background, props or clothing of Image 1.  Use Video 1 for her movements, expressions, gaze, the camera framing, the room and the timing; do not reproduce any text, captions, usernames or watermarks from Video 1; the picture is a front-camera mirror image and stays as seen. The carton corresponds to Image 2 and Image 3, which jointly define the same carton and generate only one instance at the small real size it has in those images (it occupies only about a sixth of each picture's width), adopting only its structure, material, colours and printed label (a small flat closed sky-blue paperboard carton 7.2 cm wide, 7.5 cm tall and 1.6 cm thick, the dark-blue Neuro wordmark top-left, an EXTRA STRENGTH GUM badge top-right, a Spearmint pill tag, 'Energy & Focus' in large blue type and a navy band at the bottom reading 100MG OF NATURAL CAFFEINE); do not use the lighting, exposure, background, shadow or camera angle of Image 2 or Image 3.
  [Plot Summary] Locked phone camera at desk height about a metre away, a dark wood desk, a beige wall and a door behind her, warm room light from the upper right. Video 1 has two hard cuts, at about 0.9 s and 2.2 s of its length, each with the same framing; keep them at the same moments, hard cuts with no fade, flash or dissolve. She sits at the desk writing on a white sheet with a yellow highlighter in her right hand, head down. Cut. She lifts her head, her eyes go up and to the left and the highlighter stops. Then both hands rise to shoulder height, palms out, fingers spread, the highlighter still in her right hand, her mouth opens slightly and she shakes her head a little. Cut. Her left hand is already at the side of her head scratching it, her right hand up with the highlighter, her eyes up; both hands then gesture outward in a shrug, her head tilting; then her hands return to the sheet and she writes again. A small closed Neuro Energy & Focus Extra Strength Spearmint carton stands upright on its long edge on the bare dark wood desk at the left, propped at about sixty degrees against a closed hardcover notebook, behind and to the left of the white sheet, clear of the sheet and never on paper, in the same plane and at the same distance as the sheet. It is very small, like a deck of playing cards stood on its edge: its height is only about one third of the height of her head with the cap, slightly less than the width of her open palm, clearly shorter than the yellow highlighter and about a quarter of the long edge of the white sheet, all in the same plane; in the picture it is less than one tenth of the frame height and her hand is bigger than the carton. Its label is turned about thirty degrees away from the lens, lit by the same warm light with a highlight on its upper right and a soft contact shadow on the wood; it stays on that spot for the whole clip; her raised left hand passes well behind and above it and never touches it. Phone-shot look with everything in focus and no shallow depth of field. Real-time speed. No dialogue. No background music.
  [Camera & Core Constraints] Keep every movement, gesture, expression, gaze and mouth movement of the person in Video 1 on the same frames, the props and how they are handled, the camera framing and handheld feel, the light, the room and the timing of Video 1 unchanged; no added, skipped, repeated or reordered action, no new gesture, no extra camera move, no re-staging, no new people, no change of pace. There is exactly one carton, closed and never opened, not duplicated, not vanished, not deformed, no scale drift; nothing passes through it. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen; the only lettering is the printed label on the Neuro package, exactly as in Image 2; do not reproduce any text, captions, usernames or watermarks from Video 1.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no scale drift, no cut-out edges, no slow motion, no speed ramps, no self-inserted cut points, no added or skipped action, no six-pack box, no blister card, no opened carton, no loose gum pieces, no gum in anyone's mouth, no chewing, no second package, no oversized carton, no giant or enlarged package, no large box, no studio lighting on the package, no glow, no shallow depth of field, no text on the shirt, no laptop
  ```
- **params:** model=wan3_0_prime · duration=5 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=video_references, image_references×3 · request=video-15-request.json
- **errors:** none
- **evidence:** deliverables/previews/video-15.mp4 at 0.5 s (carton tilted, no support behind it)
- **qc:**
  ```text
  RESIDUAL FAILURE: carton renders 1.99x its expected size vs her head (a1 2.24x; a2 1.99x with tightened wording and 16% padded refs; a3 sachet fallback 1.83x, no better and non-hero form); constant across cuts; all other checks passed (count 1, closed, never touched, sheet flat, no blister/open/6-pack, OCR clean, small label line garbled)
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261008-235833-08\40-briefs\video-15-plan.md
- **class:** anomaly-catalog.md §2.14 (solidity, support) and §2.15; generation-system.md §4b.1
- **cause:** qc-miss
- **fix:** none yet (not regenerated)
- **verified prompt:** pending (inserted only after a new generation passes QC)
- **rule:** Never plan a lean against a prop the model must also invent; a placed pack either stands flat on its base or lies flat on bare surface, or leans on a large solid object that is already in the source frame. QC adds a support check: every tilted or standing object must show its contact with a visible solid support at 30 fps, or it is a regenerate reason.
- **status:** promoted
- **promoted to:** anomaly-catalog.md §2.16 (support check); generation-system.md §4b.1b; wan-3-0.md §3.14, §5 (size: small placed product row); command X4/X9

## CE-014 · 2026-10-10 · Celsius can 1.6-1.7x too large in V08 placement, wan3_0_prime
- **source:** agent
- **video:** 01
- **run:** C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261010-020703-09
- **delivered:** not recorded
- **mode:** recreate
- **model:** wan3_0_prime
- **product:** Celsius Cherry Cola can
- **assets:** celsius-cherry-front-p40.png, celsius-cherry-angled-p40.png (155-159 mm, d53-58 mm); char-A04.jpg; V08 own-silent
- **user said:** — (caught by the agent during the run)
- **what was wrong:** Size failure: can 1.6-1.7x expected vs head, larger than her hand; wording one seventh of frame height and closer to the lens than she is did not shrink it
- **brief:**
  ```text
  # Video 01 brief: V08 POV explain math (placement, Cherry Cola can on the marbled table)
  Concept: recreate V08 with Celsius Cherry Cola (placement); char-A04.jpg. Why it works: the reference's own mechanism, product native to the scene, noticed not featured.
  Model/operation: wan3_0_prime, video_references + image_references, 4 s, 9:16 720p, generate_audio false. Cost: preflight in request file (3 credits per second expected).
  Fidelity: source silent video as video reference, same duration, action script written out, fidelity lock; risk: Wan rebuilds the action (approx. recreate); sync-check after the merge.
  Text: "POV: You're trying to explain math to bro but he just looks at you like this" y_rel 0.45 (posY 0.1, posX 0) 0-9.5 (final timeline)
  Guardrails: none (adult 20s woman replaces the young man; no competitor, no count issue). Verdict pick-clean.
  ```
- **prompt:**
  ```text
  [Core Task] Generate a real phone-shot clip, chest-up, of a person explaining something from a sheet of paper. The woman corresponds to Image 1, adopting only her facial features and hairstyle; she replaces only the young man with the brown fringe haircut in the black sweatshirt with a red print in Video 1 and keeps the clothing, body and pose of Video 1; do not use the background, props, clothing or lighting of Image 1. Use Video 1 for every movement, expression, gaze, the framing and camera, the room and the timing; do not reproduce any text, captions, usernames or watermarks from Video 1. The can corresponds to Image 2 and Image 3, which jointly define the same can and generate only one instance, adopting only its structure, material, colours and printed label (a white slim 355 ml aluminium can, a red-and-grey C-swoosh above the black CELSIUS wordmark with LIVE FIT, a cherries-and-cola illustration, SPARKLING CHERRY COLA in a magenta tag, a black band with three bullets and a silver-grey lower band); in Image 2 and Image 3 the can is deliberately small in the frame and keeps that small scale; do not use the framing, lighting, exposure, background, shadow or camera angle of Image 2 or Image 3.
  [Plot Summary] Shot: locked handheld chest-up framing, a plain grey wall behind, a marbled black-and-white table strip along the bottom of the frame. Video 1 has one jump cut at about 2.4 s of its length; keep that cut at the same moment. Before the cut: the woman looks down and to the left at a sheet of paper she holds up in her left hand at the left of the frame, her mouth moving as she explains, her right hand gesturing near the sheet; in the last fraction of a second before the cut she swings the sheet out to the left with a quick arm movement. After the cut: she holds the sheet up at the right of the frame, looks toward the lens and speaks, and in the last moment swings the sheet toward her head. A closed Celsius Cherry Cola can stands upright on the marbled table at the bottom of the frame, left of the centre, its base resting on the table with a small contact shadow, closer to the lens than she is, its label turned about thirty degrees toward the lens; it is part of this scene although Video 1 has none, it stays on this exact spot for the whole clip, nobody touches it and the sheet stays well above it. The can is a small object, 15.7 cm tall and 5.5 cm across: shorter than the sheet of paper is tall, about three quarters the height of her head, only as thick as three fingers side by side; it fills about one seventh of the frame height and keeps exactly this size before and after the cut. Soft cool light from the front left falls on it with a faint highlight on its left edge and a contact shadow like the table's reflections, same grain and focus as the rest. Real-time speed. No dialogue. No background music.
  [Camera & Core Constraints] Keep every movement, gesture, expression, gaze and mouth movement of the woman in Video 1 on the same frames, the props and how they are handled, the camera framing and handheld feel, the light, the room and the timing of Video 1 unchanged; no added, skipped, repeated or reordered action, no new gesture, no extra camera move, no re-staging, no new people, no change of pace. There is exactly one can, closed, standing on the table left of the centre before and after the cut, small and constant in size, not duplicated, not vanished, not deformed, no scale drift; the can stays where it is and fingers or objects never pass through it. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen; the only lettering is the printed label on the Celsius Cherry Cola can, exactly as in Image 2; do not reproduce any text, captions, usernames or watermarks from Video 1.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no scale drift, no cut-out edges, no slow motion, no speed ramps, no self-inserted cut points, no added or skipped action, no second can, no oversized can, no can taller than the sheet of paper is tall, no can larger than a head, no open tab, no drinking from the can, no studio lighting on the can, no glow, no clipping
  ```
- **params:** model=wan3_0_prime · duration=4 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=video_references, image_references×3 · request=video-01-request.json
- **errors:**
  ```text
  none; no adjustments
  ```
- **evidence:** a1 frames 0.0 and 3.0 s: can 375-380 px of 1280 (29.6 %), 1.61-1.69x vs head neighbour; larger than her hand; C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261010-020703-09/60-outputs/video-01/a1/qc
- **qc:** not recorded
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261010-020703-09\40-briefs\video-01-plan.md
- **class:** anomaly-catalog 2.7 / CE-005
- **cause:** model-limit
- **fix:** none yet
- **verified prompt:** pending (inserted only after a new generation passes QC)
- **rule:** Do not place the can closer to the lens than the person; name same-depth hand and head neighbours and a smaller frame fraction (one tenth); measure first output
- **status:** open
- **promoted to:** wan-3-0.md §5 (small placed product row, caveat), §9 (re-measured 2026-10-10: unproven for cans, depth lever (e) untested); anomaly-catalog.md §2.7 (derived distance, two estimates), §4 step 5d and §4.1 (neighbour at the product's own depth); stays open as a model limit

## CE-015 · 2026-10-10 · Placed can 1.28x oversize, cropped base, on the notebook (V10 placement)
- **source:** agent
- **video:** 03
- **run:** 20261010-020703-09
- **delivered:** not recorded
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Celsius Watermelon can (155-159 mm)
- **assets:** char-A23, celsius p40 refs, V10 own-silent
- **user said:** — (caught by the agent during the run)
- **what was wrong:** Can at 1.28x expected vs head (regenerate), base cut off by frame bottom, overlapping the notebook (CE-006) despite 'about one metre' and 1/10 frame wording; action/sync fine
- **brief:**
  ```text
  # Video 03 brief: V10 dividend notification reaction (placement, Watermelon can on the desk)
  Concept: recreate V10 with Celsius Watermelon (placement); char-A23.jpg. Why it works: the reference's own mechanism, product native to the scene, noticed not featured.
  Model/operation: wan3_0_prime, video_references + image_references, 3 s, 9:16 720p, generate_audio false. Cost: preflight in request file (3 credits per second expected).
  Fidelity: source silent video as video reference, same duration, action script written out, fidelity lock; risk: Wan rebuilds the action (approx. recreate); sync-check after the merge.
  Text: "Me receiving my $0.01 dividend in class releasing I don't need to be here" y_rel 0.1 (posY 0.8, posX 0) 0-5.4 (final timeline)
  Guardrails: N1/C2: the student reads as a minor -> complete face swap to an adult woman (done). Third-party banner (Trading 212) removed, GBP sign rewritten to $ in the CapCut text. Verdict pick-and-edit.
  ```
- **prompt:**
  ```text
  [Core Task] Generate a real phone-shot clip of a bored student at a window desk who picks up her phone. The woman corresponds to Image 1, adopting only her facial features and hairstyle; she replaces only the student in the grey-green T-shirt with curly brown hair in Video 1 and keeps the clothing, body and pose of Video 1; do not use the background, props, clothing or lighting of Image 1. Use Video 1 for every movement, expression, gaze, the framing and camera, the room and the timing; do not reproduce any text, captions, usernames or watermarks from Video 1. The can corresponds to Image 2 and Image 3, which jointly define the same can and generate only one instance, adopting only its structure, material, colours and printed label (a white slim 355 ml aluminium can, a red-and-grey C-swoosh above the black CELSIUS wordmark with LIVE FIT, a watermelon-slice illustration, SPARKLING WATERMELON in red, a black band with three bullets and a silver-grey lower band); in Image 2 and Image 3 the can is deliberately small in the frame and keeps that small scale; do not use the framing, lighting, exposure, background, shadow or camera angle of Image 2 or Image 3.
  [Plot Summary] Shot: fixed phone shot, chest-up, a bright overcast window at the left with grey curtains, a dark wooden chest of drawers behind, a notebook with a pen at the bottom of the frame, a black pencil pouch at the lower left. Video 1 is one continuous take of about three seconds. The woman leans her head on her right hand, the elbow on the desk at the right edge of the frame, a pen in her left hand, looking bored and slightly down; she puts the pen down on the notebook, leans forward and reaches with her left hand to the left, picks up a phone from the desk, lifts it to eye level and looks at it, then breaks into a small smile while still leaning on her hand; the notification banner and every caption of Video 1 are absent. A closed Celsius Watermelon can stands upright on the bare desk behind the notebook's right corner, about one metre from the lens, at least a hand-width clear of her arm and not touching the notebook or her; its base is visible with a contact shadow, its label turned about thirty degrees toward the lens; it is part of this scene although Video 1 has none, it stays there for the whole clip, nobody touches or picks it up and her phone hand never passes near it. The can is a small object, 15.7 cm tall and 5.5 cm across: shorter than the notebook is wide, about two thirds the height of her head; it fills about one tenth of the frame height and keeps exactly this size. Bright cool daylight from the window at the left puts a highlight on the can's left edge and a soft contact shadow on the desk. Real-time speed. No dialogue. No background music.
  [Camera & Core Constraints] Keep every movement, gesture, expression, gaze and mouth movement of the woman in Video 1 on the same frames, the props and how they are handled, the camera framing and handheld feel, the light, the room and the timing of Video 1 unchanged; no added, skipped, repeated or reordered action, no new gesture, no extra camera move, no re-staging, no new people, no change of pace. There is exactly one can on the desk, one phone, one pen, small and constant in size, not duplicated, not vanished, not deformed, no scale drift; the can stays where it is and fingers or objects never pass through it. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen; the only lettering is the printed label on the Celsius Watermelon can, exactly as in Image 2; do not reproduce any text, captions, usernames or watermarks from Video 1.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no scale drift, no cut-out edges, no slow motion, no speed ramps, no self-inserted cut points, no added or skipped action, no second can, no oversized can, no can taller than the notebook is wide, no can larger than a head, no open tab, no drinking from the can, no studio lighting on the can, no glow, no clipping
  ```
- **params:** model=wan3_0_prime · duration=3 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=video_references, image_references×3 · request=video-03-request.json
- **errors:**
  ```text
  none; completed
  ```
- **evidence:** a1 frame 0.0 s: can 338 px vs head 370 px, T scale 1.28x (27.9%), base cropped at bottom, stands against/over notebook right edge; C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261010-020703-09/60-outputs/video-03/a1/f0.png
- **qc:** not recorded
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261010-020703-09\40-briefs\video-03-plan.md
- **class:** anomaly-catalog.md §2.7
- **cause:** model-limit
- **fix:** none yet
- **verified prompt:** pending (inserted only after a new generation passes QC)
- **rule:** Placement in the foreground of a tight handheld shot: name the depth as farther than the nearest prop, keep base visible above the frame edge, give pixel height; fractions alone are ignored
- **status:** open
- **promoted to:** wan-3-0.md §5 (small placed product row, caveat), §9 (re-measured 2026-10-10: unproven for cans, depth lever (e) untested); anomaly-catalog.md §2.7 (derived distance, two estimates), §4 step 5d and §4.1 (neighbour at the product's own depth); stays open as a model limit

## CE-016 · 2026-10-10 · Original person still visible in parts of the video
- **source:** user
- **video:** 01
- **run:** 20261010-020703-09
- **delivered:** CapCut project 10_Oct_2026_v01 · clean C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261010-020703-09/60-outputs/video-01/clean.mp4 · credits 24 · run QC: RESIDUAL FAILURE size: can 1.55-1.60x expected vs head (a1 1.61-1.69x); constant across cut; counts 1/1, solidity, paste, sync pass
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Celsius Cherry Cola can (V08 recreate with inserts)
- **assets:** not recorded
- **user said:** "video-01-preview is not correct the original character still remains in some parts of the video"
- **what was wrong:** The two reference inserts (A 2.44-5.80 and B 7.28-9.50) were cut from the original with their dissolve-through-white edges and the reference's own overlay; the edges show the original performer, so the replaced person survives in the final timeline (floor, generation-system.md 9b). QC checked the generated pieces, not every frame of the assembled timeline incl. inserts.
- **brief:**
  ```text
  # Video 01 brief: V08 POV explain math (placement, Cherry Cola can on the marbled table)
  Concept: recreate V08 with Celsius Cherry Cola (placement); char-A04.jpg. Why it works: the reference's own mechanism, product native to the scene, noticed not featured.
  Model/operation: wan3_0_prime, video_references + image_references, 4 s, 9:16 720p, generate_audio false. Cost: preflight in request file (3 credits per second expected).
  Fidelity: source silent video as video reference, same duration, action script written out, fidelity lock; risk: Wan rebuilds the action (approx. recreate); sync-check after the merge.
  Text: "POV: You're trying to explain math to bro but he just looks at you like this" y_rel 0.45 (posY 0.1, posX 0) 0-9.5 (final timeline)
  Guardrails: none (adult 20s woman replaces the young man; no competitor, no count issue). Verdict pick-clean.
  
  ## Attempt 2 (size regeneration)
  a1 can 1.6-1.7x too large (CE-014). a2: can pushed to her depth, hand/head neighbours, one tenth of frame height, negatives against can closer than the woman. Result still 1.55-1.6x (residual failure, flagged). Cost 12 credits each (24 total).
  ```
- **prompt:**
  ```text
  [Core Task] Generate a real phone-shot clip, chest-up, of a person explaining something from a sheet of paper. The woman corresponds to Image 1, adopting only her facial features and hairstyle; she replaces only the young man with the brown fringe haircut in the black sweatshirt with a red print in Video 1 and keeps the clothing, body and pose of Video 1; do not use the background, props, clothing or lighting of Image 1. Use Video 1 for every movement, expression, gaze, the framing and camera, the room and the timing; do not reproduce any text, captions, usernames or watermarks from Video 1. The can corresponds to Image 2 and Image 3, which jointly define the same can and generate only one instance, adopting only its structure, material, colours and printed label (a white slim 355 ml aluminium can, a red-and-grey C-swoosh above the black CELSIUS wordmark with LIVE FIT, a cherries-and-cola illustration, SPARKLING CHERRY COLA in a magenta tag, a black band with three bullets and a silver-grey lower band); in Image 2 and Image 3 the can is deliberately small in the frame and keeps that small scale; do not use the framing, lighting, exposure, background, shadow or camera angle of Image 2 or Image 3.
  [Plot Summary] Shot: locked handheld chest-up framing, a plain grey wall behind, a marbled black-and-white table strip along the bottom of the frame. Video 1 has one jump cut at about 2.4 s of its length; keep that cut at the same moment. Before the cut: the woman looks down and to the left at a sheet of paper she holds up in her left hand at the left of the frame, her mouth moving as she explains, her right hand gesturing near the sheet; in the last fraction of a second before the cut she swings the sheet out to the left with a quick arm movement. After the cut: she holds the sheet up at the right of the frame, looks toward the lens and speaks, and in the last moment swings the sheet toward her head. A closed Celsius Cherry Cola can stands upright on the marbled table strip at the bottom of the frame, far to the left, at the same depth as the woman's body and her sheet (not closer to the lens than she is), its base resting on the table with a small contact shadow, its label turned about thirty degrees toward the lens; it is part of this scene although Video 1 has none, it stays on this exact spot for the whole clip, nobody touches it and the sheet stays well above it. The can is a small, slim object, 15.7 cm tall and 5.5 cm across: clearly shorter than her hand is long from wrist to fingertip, only about two thirds the height of her head from chin to crown, much shorter than the sheet of paper is tall, and as thin as three fingers side by side; it fills only about one tenth of the frame height (a small can in a wide room, roughly the height of her eye-to-chin distance doubled) and its top stays below the lower edge of the sheet; it keeps exactly this size before and after the cut. Soft cool light from the front left falls on it with a faint highlight on its left edge and a contact shadow like the table's reflections, same grain and focus as the rest. Real-time speed. No dialogue. No background music.
  [Camera & Core Constraints] Keep every movement, gesture, expression, gaze and mouth movement of the woman in Video 1 on the same frames, the props and how they are handled, the camera framing and handheld feel, the light, the room and the timing of Video 1 unchanged; no added, skipped, repeated or reordered action, no new gesture, no extra camera move, no re-staging, no new people, no change of pace. There is exactly one can, closed, standing on the table left of the centre before and after the cut, small and constant in size, not duplicated, not vanished, not deformed, no scale drift; the can stays where it is and fingers or objects never pass through it. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen; the only lettering is the printed label on the Celsius Cherry Cola can, exactly as in Image 2; do not reproduce any text, captions, usernames or watermarks from Video 1.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no scale drift, no cut-out edges, no slow motion, no speed ramps, no self-inserted cut points, no added or skipped action, no second can, no oversized can, no giant can, no can taller than her hand, no can taller than a head, no can closer to the lens than the woman, no open tab, no drinking from the can, no studio lighting on the can, no glow, no clipping
  ```
- **params:** model=wan3_0_prime · duration=4 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=video_references, image_references×3 · request=video-01-a2-request.json
- **errors:** none
- **evidence:** not recorded
- **qc:**
  ```text
  RESIDUAL FAILURE size: can 1.55-1.60x expected vs head (a1 1.61-1.69x); constant across cut; counts 1/1, solidity, paste, sync pass
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261010-020703-09\40-briefs\video-01-plan.md
- **class:** generation-system.md 3c (inserts) and 9b (must-not-survive); capcut-assembly.md 3
- **cause:** qc-miss
- **fix:** none yet
- **verified prompt:** pending (inserted only after a new generation passes QC)
- **rule:** An insert is cut on frames that contain only the insert's own content: trim its edges past any dissolve or any frame of the replaced performer, rebuild the dissolve in CapCut, and run the identity/leftover check on every frame of the assembled timeline, inserts and their edges included.
- **status:** promoted
- **promoted to:** generation-system.md §3c; capcut-assembly.md §3 step 1, §5; anomaly-catalog.md §4 step 5g; production-agents.md §3 item 13; command A6r, X9

## CE-017 · 2026-10-10 · The notification that carries the joke's context was dropped
- **source:** user
- **video:** 03
- **run:** 20261010-020703-09
- **delivered:** CapCut project 10_Oct_2026_v03 · clean C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261010-020703-09/deliverables/video-03-clean.mp4 · credits 18 · run QC: RESIDUAL FAILURE: can 1.28x expected vs head (a1 delivered; a2 larger ~1.4x and changed her top, rejected); base cropped at frame bottom; action/identity/count/sync OK
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Celsius Watermelon can (V10 recreate, dividend notification)
- **assets:** not recorded
- **user said:** "video-03-preview the notification from the original video didn't appear (and thats one of the things that is tied to the context of the video i.e 1cent divident notification that pushes the person to remember them they should not be in the class(the joke's context))"
- **what was wrong:** The plan removed the source's notification banner as third-party branding (Trading 212) and never rebuilt its function. The banner is the setup of the joke (a one-cent dividend notification pushes the student to think she should not be in class), so the edited video lost its context.
- **brief:**
  ```text
  # Video 03 brief: V10 dividend notification reaction (placement, Watermelon can on the desk)
  Concept: recreate V10 with Celsius Watermelon (placement); char-A23.jpg. Why it works: the reference's own mechanism, product native to the scene, noticed not featured.
  Model/operation: wan3_0_prime, video_references + image_references, 3 s, 9:16 720p, generate_audio false. Cost: preflight in request file (3 credits per second expected).
  Fidelity: source silent video as video reference, same duration, action script written out, fidelity lock; risk: Wan rebuilds the action (approx. recreate); sync-check after the merge.
  Text: "Me receiving my $0.01 dividend in class releasing I don't need to be here" y_rel 0.1 (posY 0.8, posX 0) 0-5.4 (final timeline)
  Guardrails: N1/C2: the student reads as a minor -> complete face swap to an adult woman (done). Third-party banner (Trading 212) removed, GBP sign rewritten to $ in the CapCut text. Verdict pick-and-edit.
  ```
- **prompt:**
  ```text
  [Core Task] Generate a real phone-shot clip of a bored student at a window desk who picks up her phone. The woman corresponds to Image 1, adopting only her facial features and hairstyle; she replaces only the student in the grey-green T-shirt with curly brown hair in Video 1 and keeps the clothing, body and pose of Video 1; do not use the background, props, clothing or lighting of Image 1. Use Video 1 for every movement, expression, gaze, the framing and camera, the room and the timing; do not reproduce any text, captions, usernames or watermarks from Video 1. The can corresponds to Image 2 and Image 3, which jointly define the same can and generate only one instance, adopting only its structure, material, colours and printed label (a white slim 355 ml aluminium can, a red-and-grey C-swoosh above the black CELSIUS wordmark with LIVE FIT, a watermelon-slice illustration, SPARKLING WATERMELON in red, a black band with three bullets and a silver-grey lower band); in Image 2 and Image 3 the can is deliberately small in the frame and keeps that small scale; do not use the framing, lighting, exposure, background, shadow or camera angle of Image 2 or Image 3.
  [Plot Summary] Shot: fixed phone shot, chest-up, a bright overcast window at the left with grey curtains, a dark wooden chest of drawers behind, a notebook with a pen at the bottom of the frame, a black pencil pouch at the lower left. Video 1 is one continuous take of about three seconds. The woman leans her head on her right hand, the elbow on the desk at the right edge of the frame, a pen in her left hand, looking bored and slightly down; she puts the pen down on the notebook, leans forward and reaches with her left hand to the left, picks up a phone from the desk, lifts it to eye level and looks at it, then breaks into a small smile while still leaning on her hand; the notification banner and every caption of Video 1 are absent. A closed Celsius Watermelon can stands upright on the bare desk surface behind and to the right of the notebook, clearly beyond the notebook's far edge and farther from the lens than the notebook, about 1.5 metres from the lens and as far from the lens as her face, at least a hand-width clear of her arm and not overlapping the notebook or her; its whole base is visible with a contact shadow well above the bottom edge of the frame, its label turned about thirty degrees toward the lens; it is part of this scene although Video 1 has none, it stays there for the whole clip, nobody touches or picks it up and her phone hand never passes near it. The can is a small object, 15.7 cm tall and 5.5 cm across: much smaller than her head, only about two thirds of her head's height and clearly shorter than the notebook is wide, about as tall as the black pencil pouch is wide; it fills only about one eighth of the frame height (about 160 pixels of 1280) and keeps exactly this size. Bright cool daylight from the window at the left puts a highlight on the can's left edge and a soft contact shadow on the desk. Real-time speed. No dialogue. No background music.
  [Camera & Core Constraints] Keep every movement, gesture, expression, gaze and mouth movement of the woman in Video 1 on the same frames, the props and how they are handled, the camera framing and handheld feel, the light, the room and the timing of Video 1 unchanged; no added, skipped, repeated or reordered action, no new gesture, no extra camera move, no re-staging, no new people, no change of pace. There is exactly one can on the desk, one phone, one pen, small and constant in size, not duplicated, not vanished, not deformed, no scale drift; the can stays where it is and fingers or objects never pass through it. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen; the only lettering is the printed label on the Celsius Watermelon can, exactly as in Image 2; do not reproduce any text, captions, usernames or watermarks from Video 1.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no scale drift, no cut-out edges, no slow motion, no speed ramps, no self-inserted cut points, no added or skipped action, no second can, no oversized can, no can taller than the notebook is wide, no can as tall as a head, no can overlapping the notebook, no can cut off by the frame edge, no open tab, no drinking from the can, no studio lighting on the can, no glow, no clipping
  ```
- **params:** model=wan3_0_prime · duration=3 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=video_references, image_references×3 · request=video-03-a2-request.json
- **errors:** none
- **evidence:** not recorded
- **qc:**
  ```text
  RESIDUAL FAILURE: can 1.28x expected vs head (a1 delivered; a2 larger ~1.4x and changed her top, rejected); base cropped at frame bottom; action/identity/count/sync OK
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261010-020703-09\40-briefs\video-03-plan.md
- **class:** text-and-format.md 2 and 3 (source overlays); creative-direction.md 6 (sharpness: the turn)
- **cause:** plan
- **fix:** none yet
- **verified prompt:** pending (inserted only after a new generation passes QC)
- **rule:** Removing a brand mark never removes the information role of an overlay: when a source overlay (notification, message, receipt, UI banner) carries the joke's setup, rebuild it as a neutral CapCut element with the same wording role, timing and position, without the third-party brand or foreign currency; the plan lists such context-bearing overlays and QC checks they are present.
- **status:** promoted
- **promoted to:** text-and-format.md §1 (context-bearing overlays), §3; capcut-assembly.md §3 step 2b; command item 6, §7 (superseded in form by CE-023: the original element, not a re-typed layer)

## CE-018 · 2026-10-10 · Can appears out of nowhere after the third second
- **source:** user
- **video:** 04
- **run:** 20261010-020703-09
- **delivered:** CapCut project 10_Oct_2026_v04 · clean C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261010-020703-09/60-outputs/video-04/clean.mp4 · credits 66 · run QC: RESIDUAL FAILURE: a2 headline removed, glass/sip ok, but the can is absent 0-4.2 s then appears at left foreground ~1.5-1.8x planned size (visual estimate); count 1; see qc-verdict.md
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Celsius Cherry Cola can + glass (V05 recreate, contents)
- **assets:** not recorded
- **user said:** "video-04-preview the can just comes/appears out of nowhere in the table after the 3rd seconds meanwhile thats not logical and the celsius can is supposed to be there from the start"
- **what was wrong:** The delivered attempt had no can in frame from 0 to about 4.2 s and then a can appeared on the table at 1.5-1.8x size; the agent delivered it as a flagged residual failure instead of treating the absence as a blocker. A placed product must exist from frame 0 (generation-system.md 4b.3); an appearance without a visible cause is a regenerate reason.
- **brief:**
  ```text
  # Video 04 brief: V05 finance desk panic (contents: the glass holds Cherry Cola, open can beside it)
  Concept: recreate V05 with Celsius Cherry Cola (contents); char-A19.jpg. Why it works: the reference's own mechanism, product native to the scene, noticed not featured.
  Model/operation: wan3_0_prime, video_references + image_references, 11 s, 9:16 720p, generate_audio false. Cost: preflight in request file (3 credits per second expected).
  Fidelity: source silent video as video reference, same duration, action script written out, fidelity lock; risk: Wan rebuilds the action (approx. recreate); sync-check after the merge.
  Text: "Me during earnings week" y_rel 0.13 (posY 0.74, posX 0) 0-10.2
  Guardrails: C6 politics: the right monitor's news headline (UK politics) replaced by a plain market chart (peripheral). Handle 'Financeaholic' removed. C3: one drink. C4: no coffee. Verdict pick-and-edit.
  ```
- **prompt:**
  ```text
  [Core Task] Generate a real phone-shot clip of a stressed trader at a three-monitor desk who takes a sip from a glass. The woman corresponds to Image 1, adopting only her facial features and hairstyle; she replaces only the man with glasses in the olive sweater in Video 1 and keeps the clothing, body and pose of Video 1; do not use the background, props, clothing or lighting of Image 1. Use Video 1 for every movement, expression, gaze, the framing and camera, the room and the timing; do not reproduce any text, captions, usernames or watermarks from Video 1. The can corresponds to Image 2 and Image 3, which jointly define the same can and generate only one instance, adopting only its structure, material, colours and printed label (a white slim 355 ml aluminium can, a red-and-grey C-swoosh above the black CELSIUS wordmark with LIVE FIT, a cherries-and-cola illustration, SPARKLING CHERRY COLA in a magenta tag, a black band with three bullets and a silver-grey lower band); in Image 2 and Image 3 the can is deliberately small in the frame and keeps that small scale; do not use the framing, lighting, exposure, background, shadow or camera angle of Image 2 or Image 3. The right monitor in Video 1 shows a news web page with a red header, a politician's photo and a large headline: replace its whole screen with a plain dark candlestick chart (green and red candles on a dark background, no text, no headline, no photo, no red banner). Image 4 is only the colour, clarity and bubbles of the drink; nothing else in it is used.
  [Plot Summary] Shot: locked phone framing from the right side of a white desk, medium shot, the camera unchanged from Video 1; a dim home office with a warm desk lamp from the lower left and cool monitor glow, three monitors (left a chart, centre a dashboard, right a dark candlestick chart with no text at all and no news page), a keyboard and blue and red sticky notes on the desk. The woman sits at the right of the frame in profile facing the monitors, keeping the glasses of Video 1. She leans toward the right monitor and reads; puts both hands on her head and slumps; drops her right hand to the keyboard; picks up the glass from the desk at the right of the keyboard with her right hand, tips it to her lips, takes one sip with her head tilted back slightly and sets it down off the right edge; types and writes; points at the left monitor; leans in and types; points again; leans in and types. The small clear glass by the right monitor's base holds Celsius Cherry Cola poured from the can beside it: dark brown cola with fine fizz bubbles, as in Image 4 (only Image 4's drink colour, clarity and bubbles; ignore everything else in it). She sips from the glass through its rim, not from the can. A Celsius Cherry Cola can, already open with its black tab lifted, stands upright on the desk right beside the glass, label turned about thirty degrees toward the lens; always exactly one can and one glass, not duplicated, the can is never picked up. The can is a small object, 15.7 cm tall and 5.5 cm across: a little taller than the glass beside it, shorter than her hand is long, about one eleventh of the frame height; it keeps exactly this size. After the sip the glass stands off-frame and is no longer seen; the can keeps its spot. The warm lamp from the lower left and the cool blue monitor glow fall on the can; a faint reflection on the white desk. Real-time speed. No dialogue. No background music.
  [Camera & Core Constraints] Keep every movement, gesture, expression, gaze and mouth movement of the woman in Video 1 on the same frames, the props and how they are handled, the camera framing and handheld feel, the light, the room and the timing of Video 1 unchanged; no added, skipped, repeated or reordered action, no new gesture, no extra camera move, no re-staging, no new people, no change of pace. There is exactly one can (open, standing beside the glass) and one glass of Cherry Cola; glass level drops slightly after the sip, small and constant in size, not duplicated, not vanished, not deformed, no scale drift; the can stays where it is and fingers or objects never pass through it. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen; the only lettering is the printed label on the Celsius Cherry Cola can, exactly as in Image 2; do not reproduce any text, captions, usernames or watermarks from Video 1.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no scale drift, no cut-out edges, no slow motion, no speed ramps, no self-inserted cut points, no added or skipped action, no second can, no oversized can, no can taller than her hand is long, no can larger than a head, no drinking from the can, no studio lighting on the can, no glow, no clipping, no news web page, no red header banner, no politician photo, no headline text on any monitor
  ```
- **params:** model=wan3_0_prime · duration=11 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=video_references, image_references×4 · request=video-04-a2-request.json
- **errors:** none
- **evidence:** not recorded
- **qc:**
  ```text
  RESIDUAL FAILURE: a2 headline removed, glass/sip ok, but the can is absent 0-4.2 s then appears at left foreground ~1.5-1.8x planned size (visual estimate); count 1; see qc-verdict.md
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261010-020703-09\40-briefs\video-04-plan.md
- **class:** generation-system.md 4b.3 (one persistent anchor); anomaly-catalog.md 2.5 (object permanence)
- **cause:** model-limit
- **fix:** none yet
- **verified prompt:** pending (inserted only after a new generation passes QC)
- **rule:** A placed or contents product must be in frame from the first frame to the last wherever its anchor is in frame; a product that appears, or is absent in the opening seconds, is never delivered as a note: regenerate with the product in a start frame or a reference that already shows it at its anchor, or pick another anchor.
- **status:** open
- **promoted to:** generation-system.md §4b.3; anomaly-catalog.md §4 step 5f; wan-3-0.md §5 (opening-seconds row), §4.0 item 11 (observed wording, not verified); command X9, §7; stays open as a model limit (start-frame lever untested, wan-3-0.md §9)

## CE-019 · 2026-10-10 · Can moves by itself along the table between seconds 1 and 2
- **source:** user
- **video:** 07
- **run:** 20261010-020703-09
- **delivered:** CapCut project 10_Oct_2026_v07 · clean C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261010-020703-09/60-outputs/video-07/clean.mp4 · credits 18 · run QC: Attempt 1 accepted. Counts: can 1 at s1 (0-1.0), shot 3 (4.5), cut3/end (5.0-5.97, shot 4); 3 people in wide shots; shot 2 no can. Size (T scale): shot 4 can 205 px = 0.16 of frame = ~1.0x lens expectation at 0.7 m (about 1.2x vs banknotes, perspective); wide shots 59 px = 0.046 = ~1.0x expected at 2.5 m (0.8-1.2x vs laptop). Within 25%, consistent across shots. Blend: warm light and contact shadow match table, label ~30 deg, not packshot, same grain; paste test 0 signs. CE-001 pass (one can); CE-002 pass (closed, never opened or drunk); CE-003 pass (hands pass beside/in front of can at 4.2-5.2, no pass-through, can unmoved); CE-004 0 signs; CE-005 ~1.0x; CE-006 n/a; CE-010 text posX 0, posY 0.81 top band; CE-012/013 n/a. Cuts at 3.03/3.97/5.27 vs source 3.07/3.97/5.33. OCR: only CELSIUS label. Notes: friend wears a grey hoodie in all shots (source had salmon then lilac shirts), minor costume deviation; no guardrail hits.
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Celsius Cherry Cola can (V07 recreate, kitchen table)
- **assets:** not recorded
- **user said:** "video-07-preview the can moves from the left side of the table to a more far place (the could've been good if in the video the person moves the can or does an action that could've impled that our product has moved along with its action such as the can/tin stays in the left of the table but when the cut happens the guy has placed the laptop at the place where the can was standind that could've been true, but in the video case the can moves by itself forcingly without any need between seconds 01: and :02)"
- **what was wrong:** Between about 1 s and 2 s the can changes its spot on the table with no visible cause. The QC compared size and count at checkpoints and judged the product as consistent, but did not track its position against a fixed neighbour second by second; the source's own shot change was not used to motivate any move.
- **brief:**
  ```text
  # Video 07 brief: V07 friend returns the money (placement, Cherry Cola can on the kitchen table)
  Concept: recreate V07 with Celsius Cherry Cola (placement); char-A11.jpg, char-A06.jpg. Why it works: the reference's own mechanism, product native to the scene, noticed not featured.
  Model/operation: wan3_0_prime, video_references + image_references, 6 s, 9:16 720p, generate_audio false. Cost: preflight in request file (3 credits per second expected).
  Fidelity: source silent video as video reference, same duration, action script written out, fidelity lock; risk: Wan rebuilds the action (approx. recreate); sync-check after the merge.
  Text: "When your friend returns the money you lent them early so you increase their credit limit 💰" y_rel 0.095 (posY 0.81, posX 0) 0-5.8
  Guardrails: none. Verdict pick-clean (high edit load: 2 faces, 4 shots).
  ```
- **prompt:**
  ```text
  [Core Task] Generate a real phone-shot skit of four quick shots in a small apartment.  Use Video 1 for every movement, expression, gaze, the framing and camera, the room and the timing; do not reproduce any text, captions, usernames or watermarks from Video 1. The can corresponds to Image 3 and Image 4, which jointly define the same can and generate only one instance, adopting only its structure, material, colours and printed label (a white slim 355 ml aluminium can, a red-and-grey C-swoosh above the black CELSIUS wordmark with LIVE FIT, a cherries-and-cola illustration, SPARKLING CHERRY COLA in a magenta tag, a black band with three bullets and a silver-grey lower band); in Image 3 and Image 4 the can is deliberately small in the frame and keeps that small scale; do not use the framing, lighting, exposure, background, shadow or camera angle of Image 3 or Image 4.
  [Plot Summary] Video 1 has three cuts, at about 3.1 s, 4.0 s and 5.3 s; keep each at the same moment. The standing friend corresponds to Image 1 (replacing the friend in the salmon and then lilac shirt) and the seated roommate in the black shirt with an embroidered print corresponds to Image 2, each adopting only the facial features and hairstyle of their image and keeping the clothing, body and pose of Video 1; do not use the background, props, clothing or lighting of Image 1 or Image 2. Shot 1, wide handheld from a corner of the kitchen: the friend, in a salmon shirt, walks from the stove toward a dark table where the roommate sits turned to the left; the friend pauses, shifts, then walks to the table end. Shot 2, close: the friend, now in a lilac button shirt, leans over an open laptop on the table. Shot 3, wide again: he stands at the open laptop on the table while the roommate gestures from his chair. Shot 4, close on a handshake across a dark table with a small stack of banknotes at the left, a grey sofa and a window behind. A closed Celsius Cherry Cola can stands upright on the kitchen table in the centre of its length, between the roommate and the laptop, in shots 1 and 3, base on the table with a contact shadow, label turned about thirty degrees toward the lens; in shot 4 it stands on the dark table at the right of the banknotes, softly out of focus beyond the handshake; it is part of this scene although Video 1 has none, one can only, nobody touches it. The can is a small object, 15.7 cm tall and 5.5 cm across: in the wide shots about two metres away it is a tiny red-and-white detail, one seventeenth of the frame height, about as tall as the laptop screen is wide; it keeps this size in each shot. Warm kitchen light from the ceiling lamp and window light from the right; the can takes the same light. Real-time speed. No dialogue. No background music.
  [Camera & Core Constraints] Keep every movement, gesture, expression, gaze and mouth movement of the people in Video 1 on the same frames, the props and how they are handled, the camera framing and handheld feel, the light, the room and the timing of Video 1 unchanged; no added, skipped, repeated or reordered action, no new gesture, no extra camera move, no re-staging, no new people, no change of pace. There is exactly one can in shots 1, 3 and 4 (not seen in shot 2), exactly three people in the wide shots, small and constant in size, not duplicated, not vanished, not deformed, no scale drift; the can stays where it is and fingers or objects never pass through it. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen; the only lettering is the printed label on the Celsius Cherry Cola can, exactly as in Image 3; do not reproduce any text, captions, usernames or watermarks from Video 1.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no scale drift, no cut-out edges, no slow motion, no speed ramps, no self-inserted cut points, no added or skipped action, no second can, no oversized can, no can taller than the laptop screen is wide, no can larger than a head, no open tab, no drinking from the can, no studio lighting on the can, no glow, no clipping
  ```
- **params:** model=wan3_0_prime · duration=6 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=video_references, image_references×4 · request=video-07-request.json
- **errors:** none
- **evidence:** not recorded
- **qc:**
  ```text
  Attempt 1 accepted. Counts: can 1 at s1 (0-1.0), shot 3 (4.5), cut3/end (5.0-5.97, shot 4); 3 people in wide shots; shot 2 no can. Size (T scale): shot 4 can 205 px = 0.16 of frame = ~1.0x lens expectation at 0.7 m (about 1.2x vs banknotes, perspective); wide shots 59 px = 0.046 = ~1.0x expected at 2.5 m (0.8-1.2x vs laptop). Within 25%, consistent across shots. Blend: warm light and contact shadow match table, label ~30 deg, not packshot, same grain; paste test 0 signs. CE-001 pass (one can); CE-002 pass (closed, never opened or drunk); CE-003 pass (hands pass beside/in front of can at 4.2-5.2, no pass-through, can unmoved); CE-004 0 signs; CE-005 ~1.0x; CE-006 n/a; CE-010 text posX 0, posY 0.81 top band; CE-012/013 n/a. Cuts at 3.03/3.97/5.27 vs source 3.07/3.97/5.33. OCR: only CELSIUS label. Notes: friend wears a grey hoodie in all shots (source had salmon then lilac shirts), minor costume deviation; no guardrail hits.
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261010-020703-09\40-briefs\video-07-plan.md
- **class:** generation-system.md 4b.3 (a placed product moves only through a visible, motivated action); anomaly-catalog.md 2.5
- **cause:** qc-miss
- **fix:** none yet
- **verified prompt:** pending (inserted only after a new generation passes QC)
- **rule:** QC tracks a placed product's position against a fixed neighbour (table edge, laptop, chair) on a dense sheet across the whole clip, not only at checkpoints; any move without a visible cause is a regenerate reason. A move is allowed only when an action or a cut motivates it (the person puts something else where it stood, the product stays put and the cut shows a new angle).
- **status:** promoted
- **promoted to:** generation-system.md §4b.3, §4b.5 (pin its spot to a fixed neighbour); anomaly-catalog.md §4 step 5f; wan-3-0.md §4.0 item 12 (observed, not verified); production-agents.md §3 item 13; command X1, X9, §7

## CE-020 · 2026-10-10 · Wrong brand for the scene: a barbecue is Celsius's scene, not Neuro's
- **source:** user
- **video:** 11
- **run:** 20261010-020703-09
- **delivered:** CapCut project 10_Oct_2026_v11 · clean 60-outputs/video-11/clean.mp4 · credits 48 · run QC: RESIDUAL FAILURE: sachet ~1.5x expected size (CE-005/008/011) and reads slightly propped/tilted against the grill front (CE-012/013); attempt 1 had it on the board and carried away (fixed in attempt 2); count 1 at all checkpoints, no contact with the board, identity ok, text clear of face
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Neuro Peppermint sachet (V02 grill recreate)
- **assets:** not recorded
- **user said:** "video-11-preview was wrongly picked for Neurogum it could've been a better fit for Celsius then Neurogum, first of all the neurogum doesn't go by the bbq scene it has no ties to it, meanwhile Celsius can be used as a drink that goes with the meat"
- **what was wrong:** The asset plan gave the grilling reference to Neuro because the table had a free surface; the brand fit was never judged. Neuro (focus, study, work, commute, coffee swap) has no tie to a barbecue, while a Celsius drink naturally goes with grilled food.
- **brief:**
  ```text
  # Video 11 brief: V02 grilling when you realize (placement, Neuro sachet on the porch table)
  Concept: recreate V02 with Neuro (placement); char-A27.jpg. Why it works: the reference's own mechanism, product native to the scene, noticed not featured.
  Model/operation: wan3_0_prime, video_references + image_references, 8 s, 9:16 720p, generate_audio false. Cost: preflight in request file (3 credits per second expected).
  Fidelity: source silent video as video reference, same duration, action script written out, fidelity lock; risk: Wan rebuilds the action (approx. recreate); sync-check after the merge.
  Text: "When you realize you're the only one who knows how to work the grill" y_rel 0.52 (posY -0.04, posX 0) 0-7.6
  Guardrails: C-N3: statistic ('70%') and the bank-account claim removed; caption rewritten without any number. Neuro: personal framing only. Verdict pick-and-edit.
  ```
- **prompt:**
  ```text
  [Core Task] Generate a real phone-shot clip of a young man grilling a steak on a covered porch. The man corresponds to Image 1, adopting only his facial features and hairstyle; he replaces only the young man with dark curly hair in the black long-sleeve shirt in Video 1 and keeps the clothing, body and pose of Video 1; do not use the background, props, clothing or lighting of Image 1. Use Video 1 for every movement, expression, gaze, the framing and camera, the room and the timing; do not reproduce any text, captions, usernames or watermarks from Video 1. The sachet corresponds to Image 2, generating only one instance, adopting only its structure, material, colours and printed label (a light-blue flat foil sachet with a Neuro wordmark, a GUM badge, a Peppermint tag and the title Energy & Focus).
  [Plot Summary] Shot: handheld phone, medium, one continuous take; a covered porch with string lights, a gas grill, a wooden cutting board on a table at the lower left. The man flips and moves a pink steak with tongs, then closes the large translucent grill hood with his left hand, then picks up the wooden board from the table with both hands and walks away to the right, as in Video 1. A single closed Neuro Energy & Focus Peppermint sachet lies flat on its wide face with its printed label up directly on the bare black metal side shelf of the grill, to the left of the wooden cutting board, with a clear gap of a full hand width between the sachet and the board; the sachet is never on the wooden board and never touches it; it is part of this scene although Video 1 has none; it stays exactly there on the shelf from the first frame to the last, nobody touches it, and when the man lifts the board and walks away to the right the board leaves without the sachet, which remains alone on the shelf. In Image 2 the sachet is deliberately small in the frame and keeps that small scale; do not use its framing, lighting, exposure, background, shadow or camera angle. The sachet is a small flat foil pack, about 5 cm by 7 cm and flat: smaller than the palm of his hand, about as long as his index finger, much smaller than the cutting board beside it; it is only about one third as wide as the cutting board blade and fills only about one fiftieth of the frame width and keeps exactly this size, lit by the same warm porch light with a thin contact shadow on the table. Real-time speed. No dialogue. No background music.
  [Camera & Core Constraints] Keep every movement, gesture, expression, gaze and mouth movement of the man in Video 1 on the same frames, the props and how they are handled, the camera framing and handheld feel, the light, the room and the timing of Video 1 unchanged; no added, skipped, repeated or reordered action, no new gesture, no extra camera move, no re-staging, no new people, no change of pace. There is exactly one sachet, sealed, lying flat, never opened, small and constant in size, not duplicated, not vanished, not deformed, no scale drift; the sachet stays where it is and fingers or objects never pass through it. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen; the only lettering is the printed label on the Neuro sachet, exactly as in Image 2; do not reproduce any text, captions, usernames or watermarks from Video 1.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no scale drift, no cut-out edges, no slow motion, no speed ramps, no self-inserted cut points, no added or skipped action, no second sachet, no oversized sachet, no sachet longer than his index finger is long, no sachet opened, no sachet on the cutting board, no sachet carried or moved with the board, no sachet touching the board, no sachet standing on its edge or leaning, no studio lighting on the sachet, no glow, no clipping
  ```
- **params:** model=wan3_0_prime · duration=8 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=video_references, image_references×2 · request=video-11-a2-request.json
- **errors:** none
- **evidence:** not recorded
- **qc:**
  ```text
  RESIDUAL FAILURE: sachet ~1.5x expected size (CE-005/008/011) and reads slightly propped/tilted against the grill front (CE-012/013); attempt 1 had it on the board and carried away (fixed in attempt 2); count 1 at all checkpoints, no contact with the board, identity ok, text clear of face
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261010-020703-09\40-briefs\video-11-plan.md
- **class:** analysis-protocol.md 5 (recreate ranking: product nativeness); generation-system.md 4b.0
- **cause:** plan
- **fix:** none yet
- **verified prompt:** pending (inserted only after a new generation passes QC)
- **rule:** Choose the brand per reference by scene fit before the surface fit: a food, grill, party or sport scene suits a drink; a desk, class, meeting, work or commute scene suits a focus product; the plan states the tie in one line and a scene with no tie for one brand goes to the other.
- **status:** promoted
- **promoted to:** analysis-protocol.md §5 (recreate ranking); command A7, §7

## CE-021 · 2026-10-10 · Sachet forced against the grill lid instead of a natural surface
- **source:** user
- **video:** 11
- **run:** 20261010-020703-09
- **delivered:** CapCut project 10_Oct_2026_v11 · clean 60-outputs/video-11/clean.mp4 · credits 48 · run QC: RESIDUAL FAILURE: sachet ~1.5x expected size (CE-005/008/011) and reads slightly propped/tilted against the grill front (CE-012/013); attempt 1 had it on the board and carried away (fixed in attempt 2); count 1 at all checkpoints, no contact with the board, identity ok, text clear of face
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Neuro Peppermint sachet (V02 grill recreate)
- **assets:** not recorded
- **user said:** "the one piece sachet thats used is so forcedly placed leaning on the bbq grill lid meanwhile it could've just been placed somewhere on the grills side shelf instead, it makes more sense"
- **what was wrong:** The product was placed leaning against the grill front/lid: a lean with a support that is not a natural resting place (CE-012/CE-013 repeated). The plan said 'bare table beside the board' and the model put it on the moving board; the retry moved it against the grill, while the grill's side shelf was a natural surface that exists in the source.
- **brief:**
  ```text
  # Video 11 brief: V02 grilling when you realize (placement, Neuro sachet on the porch table)
  Concept: recreate V02 with Neuro (placement); char-A27.jpg. Why it works: the reference's own mechanism, product native to the scene, noticed not featured.
  Model/operation: wan3_0_prime, video_references + image_references, 8 s, 9:16 720p, generate_audio false. Cost: preflight in request file (3 credits per second expected).
  Fidelity: source silent video as video reference, same duration, action script written out, fidelity lock; risk: Wan rebuilds the action (approx. recreate); sync-check after the merge.
  Text: "When you realize you're the only one who knows how to work the grill" y_rel 0.52 (posY -0.04, posX 0) 0-7.6
  Guardrails: C-N3: statistic ('70%') and the bank-account claim removed; caption rewritten without any number. Neuro: personal framing only. Verdict pick-and-edit.
  ```
- **prompt:**
  ```text
  [Core Task] Generate a real phone-shot clip of a young man grilling a steak on a covered porch. The man corresponds to Image 1, adopting only his facial features and hairstyle; he replaces only the young man with dark curly hair in the black long-sleeve shirt in Video 1 and keeps the clothing, body and pose of Video 1; do not use the background, props, clothing or lighting of Image 1. Use Video 1 for every movement, expression, gaze, the framing and camera, the room and the timing; do not reproduce any text, captions, usernames or watermarks from Video 1. The sachet corresponds to Image 2, generating only one instance, adopting only its structure, material, colours and printed label (a light-blue flat foil sachet with a Neuro wordmark, a GUM badge, a Peppermint tag and the title Energy & Focus).
  [Plot Summary] Shot: handheld phone, medium, one continuous take; a covered porch with string lights, a gas grill, a wooden cutting board on a table at the lower left. The man flips and moves a pink steak with tongs, then closes the large translucent grill hood with his left hand, then picks up the wooden board from the table with both hands and walks away to the right, as in Video 1. A single closed Neuro Energy & Focus Peppermint sachet lies flat on its wide face with its printed label up directly on the bare black metal side shelf of the grill, to the left of the wooden cutting board, with a clear gap of a full hand width between the sachet and the board; the sachet is never on the wooden board and never touches it; it is part of this scene although Video 1 has none; it stays exactly there on the shelf from the first frame to the last, nobody touches it, and when the man lifts the board and walks away to the right the board leaves without the sachet, which remains alone on the shelf. In Image 2 the sachet is deliberately small in the frame and keeps that small scale; do not use its framing, lighting, exposure, background, shadow or camera angle. The sachet is a small flat foil pack, about 5 cm by 7 cm and flat: smaller than the palm of his hand, about as long as his index finger, much smaller than the cutting board beside it; it is only about one third as wide as the cutting board blade and fills only about one fiftieth of the frame width and keeps exactly this size, lit by the same warm porch light with a thin contact shadow on the table. Real-time speed. No dialogue. No background music.
  [Camera & Core Constraints] Keep every movement, gesture, expression, gaze and mouth movement of the man in Video 1 on the same frames, the props and how they are handled, the camera framing and handheld feel, the light, the room and the timing of Video 1 unchanged; no added, skipped, repeated or reordered action, no new gesture, no extra camera move, no re-staging, no new people, no change of pace. There is exactly one sachet, sealed, lying flat, never opened, small and constant in size, not duplicated, not vanished, not deformed, no scale drift; the sachet stays where it is and fingers or objects never pass through it. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen; the only lettering is the printed label on the Neuro sachet, exactly as in Image 2; do not reproduce any text, captions, usernames or watermarks from Video 1.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no scale drift, no cut-out edges, no slow motion, no speed ramps, no self-inserted cut points, no added or skipped action, no second sachet, no oversized sachet, no sachet longer than his index finger is long, no sachet opened, no sachet on the cutting board, no sachet carried or moved with the board, no sachet touching the board, no sachet standing on its edge or leaning, no studio lighting on the sachet, no glow, no clipping
  ```
- **params:** model=wan3_0_prime · duration=8 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=video_references, image_references×2 · request=video-11-a2-request.json
- **errors:** none
- **evidence:** not recorded
- **qc:**
  ```text
  RESIDUAL FAILURE: sachet ~1.5x expected size (CE-005/008/011) and reads slightly propped/tilted against the grill front (CE-012/013); attempt 1 had it on the board and carried away (fixed in attempt 2); count 1 at all checkpoints, no contact with the board, identity ok, text clear of face
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261010-020703-09\40-briefs\video-11-plan.md
- **class:** generation-system.md 4b.1 (anchor logic), 4b.4 (lived-in pose); anomaly-catalog.md 2.14 and 2.15
- **cause:** plan
- **fix:** none yet
- **verified prompt:** pending (inserted only after a new generation passes QC)
- **rule:** Name a fixed, natural surface that exists in the source frame for the anchor (the grill's side shelf, a counter, a desk), never a moving prop (a board that is carried away) or a leaning support; the pack lies or stands on that surface where a person would really leave it.
- **status:** promoted
- **promoted to:** generation-system.md §4b.1, §4b.1b; anomaly-catalog.md §2.16; wan-3-0.md §4.0 item 8 (a standing can on the fixed shelf passed posture in V11 a4, not verified)

## CE-022 · 2026-10-10 · Caption rewritten into another subject; it must keep the same meaning
- **source:** user
- **video:** 11
- **run:** 20261010-020703-09
- **delivered:** CapCut project 10_Oct_2026_v11 · clean 60-outputs/video-11/clean.mp4 · credits 48 · run QC: RESIDUAL FAILURE: sachet ~1.5x expected size (CE-005/008/011) and reads slightly propped/tilted against the grill front (CE-012/013); attempt 1 had it on the board and carried away (fixed in attempt 2); count 1 at all checkpoints, no contact with the board, identity ok, text clear of face
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Neuro Peppermint sachet (V02 grill recreate)
- **assets:** not recorded
- **user said:** "also the video captions are way to different and we should not try to change the subject whom it was for savings and finance, instead just tweak the captions similarly but that has to exactly imply the same thing"
- **what was wrong:** To clear a guardrail (the percentage and the bank-account claim) the caption was replaced by an unrelated line ('the only one who knows how to work the grill'); the same happened to video 09. The subject of the reference's joke (savings and finance) was lost.
- **brief:**
  ```text
  # Video 11 brief: V02 grilling when you realize (placement, Neuro sachet on the porch table)
  Concept: recreate V02 with Neuro (placement); char-A27.jpg. Why it works: the reference's own mechanism, product native to the scene, noticed not featured.
  Model/operation: wan3_0_prime, video_references + image_references, 8 s, 9:16 720p, generate_audio false. Cost: preflight in request file (3 credits per second expected).
  Fidelity: source silent video as video reference, same duration, action script written out, fidelity lock; risk: Wan rebuilds the action (approx. recreate); sync-check after the merge.
  Text: "When you realize you're the only one who knows how to work the grill" y_rel 0.52 (posY -0.04, posX 0) 0-7.6
  Guardrails: C-N3: statistic ('70%') and the bank-account claim removed; caption rewritten without any number. Neuro: personal framing only. Verdict pick-and-edit.
  ```
- **prompt:**
  ```text
  [Core Task] Generate a real phone-shot clip of a young man grilling a steak on a covered porch. The man corresponds to Image 1, adopting only his facial features and hairstyle; he replaces only the young man with dark curly hair in the black long-sleeve shirt in Video 1 and keeps the clothing, body and pose of Video 1; do not use the background, props, clothing or lighting of Image 1. Use Video 1 for every movement, expression, gaze, the framing and camera, the room and the timing; do not reproduce any text, captions, usernames or watermarks from Video 1. The sachet corresponds to Image 2, generating only one instance, adopting only its structure, material, colours and printed label (a light-blue flat foil sachet with a Neuro wordmark, a GUM badge, a Peppermint tag and the title Energy & Focus).
  [Plot Summary] Shot: handheld phone, medium, one continuous take; a covered porch with string lights, a gas grill, a wooden cutting board on a table at the lower left. The man flips and moves a pink steak with tongs, then closes the large translucent grill hood with his left hand, then picks up the wooden board from the table with both hands and walks away to the right, as in Video 1. A single closed Neuro Energy & Focus Peppermint sachet lies flat on its wide face with its printed label up directly on the bare black metal side shelf of the grill, to the left of the wooden cutting board, with a clear gap of a full hand width between the sachet and the board; the sachet is never on the wooden board and never touches it; it is part of this scene although Video 1 has none; it stays exactly there on the shelf from the first frame to the last, nobody touches it, and when the man lifts the board and walks away to the right the board leaves without the sachet, which remains alone on the shelf. In Image 2 the sachet is deliberately small in the frame and keeps that small scale; do not use its framing, lighting, exposure, background, shadow or camera angle. The sachet is a small flat foil pack, about 5 cm by 7 cm and flat: smaller than the palm of his hand, about as long as his index finger, much smaller than the cutting board beside it; it is only about one third as wide as the cutting board blade and fills only about one fiftieth of the frame width and keeps exactly this size, lit by the same warm porch light with a thin contact shadow on the table. Real-time speed. No dialogue. No background music.
  [Camera & Core Constraints] Keep every movement, gesture, expression, gaze and mouth movement of the man in Video 1 on the same frames, the props and how they are handled, the camera framing and handheld feel, the light, the room and the timing of Video 1 unchanged; no added, skipped, repeated or reordered action, no new gesture, no extra camera move, no re-staging, no new people, no change of pace. There is exactly one sachet, sealed, lying flat, never opened, small and constant in size, not duplicated, not vanished, not deformed, no scale drift; the sachet stays where it is and fingers or objects never pass through it. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen; the only lettering is the printed label on the Neuro sachet, exactly as in Image 2; do not reproduce any text, captions, usernames or watermarks from Video 1.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no scale drift, no cut-out edges, no slow motion, no speed ramps, no self-inserted cut points, no added or skipped action, no second sachet, no oversized sachet, no sachet longer than his index finger is long, no sachet opened, no sachet on the cutting board, no sachet carried or moved with the board, no sachet touching the board, no sachet standing on its edge or leaning, no studio lighting on the sachet, no glow, no clipping
  ```
- **params:** model=wan3_0_prime · duration=8 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=video_references, image_references×2 · request=video-11-a2-request.json
- **errors:** none
- **evidence:** not recorded
- **qc:**
  ```text
  RESIDUAL FAILURE: sachet ~1.5x expected size (CE-005/008/011) and reads slightly propped/tilted against the grill front (CE-012/013); attempt 1 had it on the board and carried away (fixed in attempt 2); count 1 at all checkpoints, no contact with the board, identity ok, text clear of face
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261010-020703-09\40-briefs\video-11-plan.md
- **class:** text-and-format.md 1 and 3 (caption wording); brand-guardrails.md 4 (rewrite minimally)
- **cause:** plan
- **fix:** none yet
- **verified prompt:** pending (inserted only after a new generation passes QC)
- **rule:** A guardrail caption rewrite is minimal and keeps the reference's subject and meaning: remove only the banned element (a number, a statistic, a name) and say the same thing in the same grammar; never swap the topic for an unrelated joke.
- **status:** promoted
- **promoted to:** text-and-format.md §1; brand-guardrails.md §2; command item 6, §7

## CE-023 · 2026-10-10 · Notification was re-typed as plain text instead of using the original notification
- **source:** user
- **video:** 03
- **run:** 20261010-020703-09
- **delivered:** CapCut project 10_Oct_2026_v03 · clean C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261010-020703-09/deliverables/video-03-clean.mp4 · credits 18 · run QC: RESIDUAL FAILURE: can 1.28x expected vs head (a1 delivered; a2 larger ~1.4x and changed her top, rejected); base cropped at frame bottom; action/identity/count/sync OK
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Celsius Watermelon can (V10 recreate, dividend notification)
- **assets:** not recorded
- **user said:** "the video 03 notification is wrong, you should've used the same notification from the original video not just place text over it"
- **what was wrong:** After CE-017 the notification was rebuilt as a house-style text layer. A context-bearing source overlay (a phone notification banner) must be the SAME element as in the reference, cut from the original frames with its own look, position and timing and placed over the clean video, not re-typed in the house text style.
- **brief:**
  ```text
  # Video 03 brief: V10 dividend notification reaction (placement, Watermelon can on the desk)
  Concept: recreate V10 with Celsius Watermelon (placement); char-A23.jpg. Why it works: the reference's own mechanism, product native to the scene, noticed not featured.
  Model/operation: wan3_0_prime, video_references + image_references, 3 s, 9:16 720p, generate_audio false. Cost: preflight in request file (3 credits per second expected).
  Fidelity: source silent video as video reference, same duration, action script written out, fidelity lock; risk: Wan rebuilds the action (approx. recreate); sync-check after the merge.
  Text: "Me receiving my $0.01 dividend in class releasing I don't need to be here" y_rel 0.1 (posY 0.8, posX 0) 0-5.4 (final timeline)
  Guardrails: N1/C2: the student reads as a minor -> complete face swap to an adult woman (done). Third-party banner (Trading 212) removed, GBP sign rewritten to $ in the CapCut text. Verdict pick-and-edit.
  ```
- **prompt:**
  ```text
  [Core Task] Generate a real phone-shot clip of a bored student at a window desk who picks up her phone. The woman corresponds to Image 1, adopting only her facial features and hairstyle; she replaces only the student in the grey-green T-shirt with curly brown hair in Video 1 and keeps the clothing, body and pose of Video 1; do not use the background, props, clothing or lighting of Image 1. Use Video 1 for every movement, expression, gaze, the framing and camera, the room and the timing; do not reproduce any text, captions, usernames or watermarks from Video 1. The can corresponds to Image 2 and Image 3, which jointly define the same can and generate only one instance, adopting only its structure, material, colours and printed label (a white slim 355 ml aluminium can, a red-and-grey C-swoosh above the black CELSIUS wordmark with LIVE FIT, a watermelon-slice illustration, SPARKLING WATERMELON in red, a black band with three bullets and a silver-grey lower band); in Image 2 and Image 3 the can is deliberately small in the frame and keeps that small scale; do not use the framing, lighting, exposure, background, shadow or camera angle of Image 2 or Image 3.
  [Plot Summary] Shot: fixed phone shot, chest-up, a bright overcast window at the left with grey curtains, a dark wooden chest of drawers behind, a notebook with a pen at the bottom of the frame, a black pencil pouch at the lower left. Video 1 is one continuous take of about three seconds. The woman leans her head on her right hand, the elbow on the desk at the right edge of the frame, a pen in her left hand, looking bored and slightly down; she puts the pen down on the notebook, leans forward and reaches with her left hand to the left, picks up a phone from the desk, lifts it to eye level and looks at it, then breaks into a small smile while still leaning on her hand; the notification banner and every caption of Video 1 are absent. A closed Celsius Watermelon can stands upright on the bare desk surface behind and to the right of the notebook, clearly beyond the notebook's far edge and farther from the lens than the notebook, about 1.5 metres from the lens and as far from the lens as her face, at least a hand-width clear of her arm and not overlapping the notebook or her; its whole base is visible with a contact shadow well above the bottom edge of the frame, its label turned about thirty degrees toward the lens; it is part of this scene although Video 1 has none, it stays there for the whole clip, nobody touches or picks it up and her phone hand never passes near it. The can is a small object, 15.7 cm tall and 5.5 cm across: much smaller than her head, only about two thirds of her head's height and clearly shorter than the notebook is wide, about as tall as the black pencil pouch is wide; it fills only about one eighth of the frame height (about 160 pixels of 1280) and keeps exactly this size. Bright cool daylight from the window at the left puts a highlight on the can's left edge and a soft contact shadow on the desk. Real-time speed. No dialogue. No background music.
  [Camera & Core Constraints] Keep every movement, gesture, expression, gaze and mouth movement of the woman in Video 1 on the same frames, the props and how they are handled, the camera framing and handheld feel, the light, the room and the timing of Video 1 unchanged; no added, skipped, repeated or reordered action, no new gesture, no extra camera move, no re-staging, no new people, no change of pace. There is exactly one can on the desk, one phone, one pen, small and constant in size, not duplicated, not vanished, not deformed, no scale drift; the can stays where it is and fingers or objects never pass through it. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen; the only lettering is the printed label on the Celsius Watermelon can, exactly as in Image 2; do not reproduce any text, captions, usernames or watermarks from Video 1.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no scale drift, no cut-out edges, no slow motion, no speed ramps, no self-inserted cut points, no added or skipped action, no second can, no oversized can, no can taller than the notebook is wide, no can as tall as a head, no can overlapping the notebook, no can cut off by the frame edge, no open tab, no drinking from the can, no studio lighting on the can, no glow, no clipping
  ```
- **params:** model=wan3_0_prime · duration=3 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=video_references, image_references×3 · request=video-03-a2-request.json
- **errors:** none
- **evidence:** not recorded
- **qc:**
  ```text
  RESIDUAL FAILURE: can 1.28x expected vs head (a1 delivered; a2 larger ~1.4x and changed her top, rejected); base cropped at frame bottom; action/identity/count/sync OK
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261010-020703-09\40-briefs\video-03-plan.md
- **class:** text-and-format.md 2 and 3 (source overlays); generation-system.md 3c (insert-style cut from the reference)
- **cause:** plan
- **fix:** none yet
- **verified prompt:** pending (inserted only after a new generation passes QC)
- **rule:** When a source overlay carries the joke's context (notification, message, UI banner), reuse the original element itself: crop it from the reference's frames with its alpha-like region, place it as a picture overlay at the same position, size and timing; text layers are only for captions. Content the user names as part of the context outranks the third-party-brand removal.
- **status:** promoted
- **promoted to:** text-and-format.md §1, §3; capcut-assembly.md §3 step 2b; command item 6, §7

## CE-024 · 2026-10-10 · Audio of the re-cut video 01 drops and is not the original audio
- **source:** user
- **video:** 01
- **run:** 20261010-020703-09
- **delivered:** CapCut project 10_Oct_2026_v01 · clean C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261010-020703-09/60-outputs/video-01/clean.mp4 · credits 24 · run QC: RESIDUAL FAILURE size: can 1.55-1.60x expected vs head (a1 1.61-1.69x); constant across cut; counts 1/1, solidity, paste, sync pass
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Celsius Cherry Cola can (V08 recreate with inserts)
- **assets:** not recorded
- **user said:** "there is some problems with the audio of the deliverables/video-01-preview.mp4 because it seems like there were cuts to fit the video and it sounds like it just drops and is not the exact same audio with the original one"
- **what was wrong:** To remove the original performer from the insert edges (CE-016) the inserts were trimmed and the timeline shortened from 9.53 s to 8.15 s; the audio was then assembled from separate pieces (own audio at source times plus each insert's own sound), so the original track is cut and drops at the joins and no longer matches the reference.
- **brief:**
  ```text
  # Video 01 brief: V08 POV explain math (placement, Cherry Cola can on the marbled table)
  Concept: recreate V08 with Celsius Cherry Cola (placement); char-A04.jpg. Why it works: the reference's own mechanism, product native to the scene, noticed not featured.
  Model/operation: wan3_0_prime, video_references + image_references, 4 s, 9:16 720p, generate_audio false. Cost: preflight in request file (3 credits per second expected).
  Fidelity: source silent video as video reference, same duration, action script written out, fidelity lock; risk: Wan rebuilds the action (approx. recreate); sync-check after the merge.
  Text: "POV: You're trying to explain math to bro but he just looks at you like this" y_rel 0.45 (posY 0.1, posX 0) 0-9.5 (final timeline)
  Guardrails: none (adult 20s woman replaces the young man; no competitor, no count issue). Verdict pick-clean.
  
  ## Attempt 2 (size regeneration)
  a1 can 1.6-1.7x too large (CE-014). a2: can pushed to her depth, hand/head neighbours, one tenth of frame height, negatives against can closer than the woman. Result still 1.55-1.6x (residual failure, flagged). Cost 12 credits each (24 total).
  ```
- **prompt:**
  ```text
  [Core Task] Generate a real phone-shot clip, chest-up, of a person explaining something from a sheet of paper. The woman corresponds to Image 1, adopting only her facial features and hairstyle; she replaces only the young man with the brown fringe haircut in the black sweatshirt with a red print in Video 1 and keeps the clothing, body and pose of Video 1; do not use the background, props, clothing or lighting of Image 1. Use Video 1 for every movement, expression, gaze, the framing and camera, the room and the timing; do not reproduce any text, captions, usernames or watermarks from Video 1. The can corresponds to Image 2 and Image 3, which jointly define the same can and generate only one instance, adopting only its structure, material, colours and printed label (a white slim 355 ml aluminium can, a red-and-grey C-swoosh above the black CELSIUS wordmark with LIVE FIT, a cherries-and-cola illustration, SPARKLING CHERRY COLA in a magenta tag, a black band with three bullets and a silver-grey lower band); in Image 2 and Image 3 the can is deliberately small in the frame and keeps that small scale; do not use the framing, lighting, exposure, background, shadow or camera angle of Image 2 or Image 3.
  [Plot Summary] Shot: locked handheld chest-up framing, a plain grey wall behind, a marbled black-and-white table strip along the bottom of the frame. Video 1 has one jump cut at about 2.4 s of its length; keep that cut at the same moment. Before the cut: the woman looks down and to the left at a sheet of paper she holds up in her left hand at the left of the frame, her mouth moving as she explains, her right hand gesturing near the sheet; in the last fraction of a second before the cut she swings the sheet out to the left with a quick arm movement. After the cut: she holds the sheet up at the right of the frame, looks toward the lens and speaks, and in the last moment swings the sheet toward her head. A closed Celsius Cherry Cola can stands upright on the marbled table strip at the bottom of the frame, far to the left, at the same depth as the woman's body and her sheet (not closer to the lens than she is), its base resting on the table with a small contact shadow, its label turned about thirty degrees toward the lens; it is part of this scene although Video 1 has none, it stays on this exact spot for the whole clip, nobody touches it and the sheet stays well above it. The can is a small, slim object, 15.7 cm tall and 5.5 cm across: clearly shorter than her hand is long from wrist to fingertip, only about two thirds the height of her head from chin to crown, much shorter than the sheet of paper is tall, and as thin as three fingers side by side; it fills only about one tenth of the frame height (a small can in a wide room, roughly the height of her eye-to-chin distance doubled) and its top stays below the lower edge of the sheet; it keeps exactly this size before and after the cut. Soft cool light from the front left falls on it with a faint highlight on its left edge and a contact shadow like the table's reflections, same grain and focus as the rest. Real-time speed. No dialogue. No background music.
  [Camera & Core Constraints] Keep every movement, gesture, expression, gaze and mouth movement of the woman in Video 1 on the same frames, the props and how they are handled, the camera framing and handheld feel, the light, the room and the timing of Video 1 unchanged; no added, skipped, repeated or reordered action, no new gesture, no extra camera move, no re-staging, no new people, no change of pace. There is exactly one can, closed, standing on the table left of the centre before and after the cut, small and constant in size, not duplicated, not vanished, not deformed, no scale drift; the can stays where it is and fingers or objects never pass through it. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen; the only lettering is the printed label on the Celsius Cherry Cola can, exactly as in Image 2; do not reproduce any text, captions, usernames or watermarks from Video 1.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no scale drift, no cut-out edges, no slow motion, no speed ramps, no self-inserted cut points, no added or skipped action, no second can, no oversized can, no giant can, no can taller than her hand, no can taller than a head, no can closer to the lens than the woman, no open tab, no drinking from the can, no studio lighting on the can, no glow, no clipping
  ```
- **params:** model=wan3_0_prime · duration=4 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=video_references, image_references×3 · request=video-01-a2-request.json
- **errors:** none
- **evidence:** not recorded
- **qc:**
  ```text
  RESIDUAL FAILURE size: can 1.55-1.60x expected vs head (a1 1.61-1.69x); constant across cut; counts 1/1, solidity, paste, sync pass
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261010-020703-09\40-briefs\video-01-plan.md
- **class:** capcut-assembly.md 3 (audio); generation-system.md 3c (inserts keep the reference's timeline)
- **cause:** plan
- **fix:** none yet
- **verified prompt:** pending (inserted only after a new generation passes QC)
- **rule:** A Recreate keeps the reference's timeline and the reference's ORIGINAL audio track whole and untouched under it: never shorten the timeline or splice audio pieces. To hide a performer in an insert's edge frames, cover only those frames (hold a generated frame fading to the dissolve colour) and keep every duration, so the original audio stays continuous and in sync.
- **status:** promoted
- **promoted to:** generation-system.md §3c; capcut-assembly.md §3 step 1, §5, §6; anomaly-catalog.md §4 step 5g; production-agents.md §3 item 13; command X9, X10, §6, §7

## CE-025 · 2026-10-10 · Frozen character frames around the white flash
- **source:** user
- **video:** 01
- **run:** 20261010-020703-09
- **delivered:** CapCut project 10_Oct_2026_v01 · clean C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261010-020703-09/60-outputs/video-01/clean.mp4 · credits 24 · run QC: RESIDUAL FAILURE size: can 1.55-1.60x expected vs head (a1 1.61-1.69x); constant across cut; counts 1/1, solidity, paste, sync pass
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Celsius Cherry Cola can (V08 recreate with inserts)
- **assets:** not recorded
- **user said:** "okay it looks better but the moment the white flash comes the character and the just stucks until the flash takes the full view, and then when it starts to fade again the character starts as frozen then it unfreezes, and thats should not be the case"
- **what was wrong:** To cover the gaps where the original performer showed, a held (frozen) generated frame was faded to white and a frozen first frame was faded in from white; the character visibly freezes during the flash and unfreezes after it. A hold under a transition reads as a glitch.
- **brief:**
  ```text
  # Video 01 brief: V08 POV explain math (placement, Cherry Cola can on the marbled table)
  Concept: recreate V08 with Celsius Cherry Cola (placement); char-A04.jpg. Why it works: the reference's own mechanism, product native to the scene, noticed not featured.
  Model/operation: wan3_0_prime, video_references + image_references, 4 s, 9:16 720p, generate_audio false. Cost: preflight in request file (3 credits per second expected).
  Fidelity: source silent video as video reference, same duration, action script written out, fidelity lock; risk: Wan rebuilds the action (approx. recreate); sync-check after the merge.
  Text: "POV: You're trying to explain math to bro but he just looks at you like this" y_rel 0.45 (posY 0.1, posX 0) 0-9.5 (final timeline)
  Guardrails: none (adult 20s woman replaces the young man; no competitor, no count issue). Verdict pick-clean.
  
  ## Attempt 2 (size regeneration)
  a1 can 1.6-1.7x too large (CE-014). a2: can pushed to her depth, hand/head neighbours, one tenth of frame height, negatives against can closer than the woman. Result still 1.55-1.6x (residual failure, flagged). Cost 12 credits each (24 total).
  ```
- **prompt:**
  ```text
  [Core Task] Generate a real phone-shot clip, chest-up, of a person explaining something from a sheet of paper. The woman corresponds to Image 1, adopting only her facial features and hairstyle; she replaces only the young man with the brown fringe haircut in the black sweatshirt with a red print in Video 1 and keeps the clothing, body and pose of Video 1; do not use the background, props, clothing or lighting of Image 1. Use Video 1 for every movement, expression, gaze, the framing and camera, the room and the timing; do not reproduce any text, captions, usernames or watermarks from Video 1. The can corresponds to Image 2 and Image 3, which jointly define the same can and generate only one instance, adopting only its structure, material, colours and printed label (a white slim 355 ml aluminium can, a red-and-grey C-swoosh above the black CELSIUS wordmark with LIVE FIT, a cherries-and-cola illustration, SPARKLING CHERRY COLA in a magenta tag, a black band with three bullets and a silver-grey lower band); in Image 2 and Image 3 the can is deliberately small in the frame and keeps that small scale; do not use the framing, lighting, exposure, background, shadow or camera angle of Image 2 or Image 3.
  [Plot Summary] Shot: locked handheld chest-up framing, a plain grey wall behind, a marbled black-and-white table strip along the bottom of the frame. Video 1 has one jump cut at about 2.4 s of its length; keep that cut at the same moment. Before the cut: the woman looks down and to the left at a sheet of paper she holds up in her left hand at the left of the frame, her mouth moving as she explains, her right hand gesturing near the sheet; in the last fraction of a second before the cut she swings the sheet out to the left with a quick arm movement. After the cut: she holds the sheet up at the right of the frame, looks toward the lens and speaks, and in the last moment swings the sheet toward her head. A closed Celsius Cherry Cola can stands upright on the marbled table strip at the bottom of the frame, far to the left, at the same depth as the woman's body and her sheet (not closer to the lens than she is), its base resting on the table with a small contact shadow, its label turned about thirty degrees toward the lens; it is part of this scene although Video 1 has none, it stays on this exact spot for the whole clip, nobody touches it and the sheet stays well above it. The can is a small, slim object, 15.7 cm tall and 5.5 cm across: clearly shorter than her hand is long from wrist to fingertip, only about two thirds the height of her head from chin to crown, much shorter than the sheet of paper is tall, and as thin as three fingers side by side; it fills only about one tenth of the frame height (a small can in a wide room, roughly the height of her eye-to-chin distance doubled) and its top stays below the lower edge of the sheet; it keeps exactly this size before and after the cut. Soft cool light from the front left falls on it with a faint highlight on its left edge and a contact shadow like the table's reflections, same grain and focus as the rest. Real-time speed. No dialogue. No background music.
  [Camera & Core Constraints] Keep every movement, gesture, expression, gaze and mouth movement of the woman in Video 1 on the same frames, the props and how they are handled, the camera framing and handheld feel, the light, the room and the timing of Video 1 unchanged; no added, skipped, repeated or reordered action, no new gesture, no extra camera move, no re-staging, no new people, no change of pace. There is exactly one can, closed, standing on the table left of the centre before and after the cut, small and constant in size, not duplicated, not vanished, not deformed, no scale drift; the can stays where it is and fingers or objects never pass through it. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen; the only lettering is the printed label on the Celsius Cherry Cola can, exactly as in Image 2; do not reproduce any text, captions, usernames or watermarks from Video 1.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no scale drift, no cut-out edges, no slow motion, no speed ramps, no self-inserted cut points, no added or skipped action, no second can, no oversized can, no giant can, no can taller than her hand, no can taller than a head, no can closer to the lens than the woman, no open tab, no drinking from the can, no studio lighting on the can, no glow, no clipping
  ```
- **params:** model=wan3_0_prime · duration=4 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=video_references, image_references×3 · request=video-01-a2-request.json
- **errors:** none
- **evidence:** not recorded
- **qc:**
  ```text
  RESIDUAL FAILURE size: can 1.55-1.60x expected vs head (a1 1.61-1.69x); constant across cut; counts 1/1, solidity, paste, sync pass
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261010-020703-09\40-briefs\video-01-plan.md
- **class:** capcut-assembly.md 3 (transitions); generation-system.md 3c
- **cause:** plan
- **fix:** none yet
- **verified prompt:** pending (inserted only after a new generation passes QC)
- **rule:** Never cover a gap with a frozen frame: a dissolve or flash must run over real moving footage (fade the last/first frames of the moving piece itself) and the gap itself is pure transition colour; durations stay unchanged so the original audio stays continuous.
- **status:** promoted
- **promoted to:** generation-system.md §3c; capcut-assembly.md §3 step 1, §5; anomaly-catalog.md §4 step 5g; command X9, §7

## CE-026 · 2026-10-10 · Leftover bright rectangle where the notification was, visible during the fade to black
- **source:** user
- **video:** 03
- **run:** 20261010-020703-09
- **delivered:** CapCut project 10_Oct_2026_v03 · clean C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261010-020703-09/deliverables/video-03-clean.mp4 · credits 18 · run QC: RESIDUAL FAILURE: can 1.28x expected vs head (a1 delivered; a2 larger ~1.4x and changed her top, rejected); base cropped at frame bottom; action/identity/count/sync OK
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Celsius Watermelon can (V10 recreate, original notification overlay)
- **assets:** not recorded
- **user said:** "video03 when the transition happens there is a part of the video where the notification use to be that just catches your eye badly, things like this should try to be avoided too"
- **what was wrong:** The original-notification overlay clip (crop of the reference with its original window backdrop baked in) stays on screen after the banner has popped out and is not faded with the picture, so during the fade to black a bright window-coloured rectangle remains at the banner's position and catches the eye.
- **brief:**
  ```text
  # Video 03 brief: V10 dividend notification reaction (placement, Watermelon can on the desk)
  Concept: recreate V10 with Celsius Watermelon (placement); char-A23.jpg. Why it works: the reference's own mechanism, product native to the scene, noticed not featured.
  Model/operation: wan3_0_prime, video_references + image_references, 3 s, 9:16 720p, generate_audio false. Cost: preflight in request file (3 credits per second expected).
  Fidelity: source silent video as video reference, same duration, action script written out, fidelity lock; risk: Wan rebuilds the action (approx. recreate); sync-check after the merge.
  Text: "Me receiving my $0.01 dividend in class releasing I don't need to be here" y_rel 0.1 (posY 0.8, posX 0) 0-5.4 (final timeline)
  Guardrails: N1/C2: the student reads as a minor -> complete face swap to an adult woman (done). Third-party banner (Trading 212) removed, GBP sign rewritten to $ in the CapCut text. Verdict pick-and-edit.
  ```
- **prompt:**
  ```text
  [Core Task] Generate a real phone-shot clip of a bored student at a window desk who picks up her phone. The woman corresponds to Image 1, adopting only her facial features and hairstyle; she replaces only the student in the grey-green T-shirt with curly brown hair in Video 1 and keeps the clothing, body and pose of Video 1; do not use the background, props, clothing or lighting of Image 1. Use Video 1 for every movement, expression, gaze, the framing and camera, the room and the timing; do not reproduce any text, captions, usernames or watermarks from Video 1. The can corresponds to Image 2 and Image 3, which jointly define the same can and generate only one instance, adopting only its structure, material, colours and printed label (a white slim 355 ml aluminium can, a red-and-grey C-swoosh above the black CELSIUS wordmark with LIVE FIT, a watermelon-slice illustration, SPARKLING WATERMELON in red, a black band with three bullets and a silver-grey lower band); in Image 2 and Image 3 the can is deliberately small in the frame and keeps that small scale; do not use the framing, lighting, exposure, background, shadow or camera angle of Image 2 or Image 3.
  [Plot Summary] Shot: fixed phone shot, chest-up, a bright overcast window at the left with grey curtains, a dark wooden chest of drawers behind, a notebook with a pen at the bottom of the frame, a black pencil pouch at the lower left. Video 1 is one continuous take of about three seconds. The woman leans her head on her right hand, the elbow on the desk at the right edge of the frame, a pen in her left hand, looking bored and slightly down; she puts the pen down on the notebook, leans forward and reaches with her left hand to the left, picks up a phone from the desk, lifts it to eye level and looks at it, then breaks into a small smile while still leaning on her hand; the notification banner and every caption of Video 1 are absent. A closed Celsius Watermelon can stands upright on the bare desk surface behind and to the right of the notebook, clearly beyond the notebook's far edge and farther from the lens than the notebook, about 1.5 metres from the lens and as far from the lens as her face, at least a hand-width clear of her arm and not overlapping the notebook or her; its whole base is visible with a contact shadow well above the bottom edge of the frame, its label turned about thirty degrees toward the lens; it is part of this scene although Video 1 has none, it stays there for the whole clip, nobody touches or picks it up and her phone hand never passes near it. The can is a small object, 15.7 cm tall and 5.5 cm across: much smaller than her head, only about two thirds of her head's height and clearly shorter than the notebook is wide, about as tall as the black pencil pouch is wide; it fills only about one eighth of the frame height (about 160 pixels of 1280) and keeps exactly this size. Bright cool daylight from the window at the left puts a highlight on the can's left edge and a soft contact shadow on the desk. Real-time speed. No dialogue. No background music.
  [Camera & Core Constraints] Keep every movement, gesture, expression, gaze and mouth movement of the woman in Video 1 on the same frames, the props and how they are handled, the camera framing and handheld feel, the light, the room and the timing of Video 1 unchanged; no added, skipped, repeated or reordered action, no new gesture, no extra camera move, no re-staging, no new people, no change of pace. There is exactly one can on the desk, one phone, one pen, small and constant in size, not duplicated, not vanished, not deformed, no scale drift; the can stays where it is and fingers or objects never pass through it. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen; the only lettering is the printed label on the Celsius Watermelon can, exactly as in Image 2; do not reproduce any text, captions, usernames or watermarks from Video 1.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no scale drift, no cut-out edges, no slow motion, no speed ramps, no self-inserted cut points, no added or skipped action, no second can, no oversized can, no can taller than the notebook is wide, no can as tall as a head, no can overlapping the notebook, no can cut off by the frame edge, no open tab, no drinking from the can, no studio lighting on the can, no glow, no clipping
  ```
- **params:** model=wan3_0_prime · duration=3 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=video_references, image_references×3 · request=video-03-a2-request.json
- **errors:** none
- **evidence:** not recorded
- **qc:**
  ```text
  RESIDUAL FAILURE: can 1.28x expected vs head (a1 delivered; a2 larger ~1.4x and changed her top, rejected); base cropped at frame bottom; action/identity/count/sync OK
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261010-020703-09\40-briefs\video-03-plan.md
- **class:** capcut-assembly.md 3 (overlays, transitions); generation-system.md 9b (leftovers)
- **cause:** qc-miss
- **fix:** none yet
- **verified prompt:** pending (inserted only after a new generation passes QC)
- **rule:** An overlay cut from a reference must exist only on the frames where its element is really visible and must follow every fade, dissolve or flash of the picture beneath it; QC views dense sheets at every overlay start/end and every transition for stray rectangles, halos or brightness steps, not only the content frames.
- **status:** promoted
- **promoted to:** capcut-assembly.md §3 step 2b, §5; anomaly-catalog.md §4 step 5g; production-agents.md §3 item 13; command X9, §7

## CE-027 · 2026-10-10 · Caption must keep the reference's specific keyword text
- **source:** user
- **video:** 04
- **run:** 20261010-020703-09
- **delivered:** CapCut project 10_Oct_2026_v04-2 · clean C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261010-020703-09/60-outputs/video-04/clean.mp4 · credits 132 · run QC: RESIDUAL FAILURE (size only): a3 has the open can in frame from frame 0 to the end on one fixed spot (dense 0-1 s and 0-4.5 s checked, count 1, never touched); glass sipped once through the rim; headline gone. Can ~0.15 of frame height = ~1.65x planned (1/11) and in the left foreground, not beside the glass. a4 fixed size but vanished can / two glasses / drank from can, rejected. caught-error CE-018 NOT set to verified (QC not fully passed).
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Celsius Cherry Cola can + glass (V05 recreate, contents)
- **assets:** not recorded
- **user said:** "also the video-04-preview text let it be "Financeaholic" as in the original, due to the very specific keyword use"
- **what was wrong:** The source's only on-screen text ('Financeaholic') was treated as a handle/watermark and dropped, and replaced by an invented caption ('Me during earnings week'). The user wants the reference's own keyword kept because the keyword is the specific hook of the video.
- **brief:**
  ```text
  # Video 04 brief: V05 finance desk panic (contents: the glass holds Cherry Cola, open can beside it)
  Concept: recreate V05 with Celsius Cherry Cola (contents); char-A19.jpg. Why it works: the reference's own mechanism, product native to the scene, noticed not featured.
  Model/operation: wan3_0_prime, video_references + image_references, 11 s, 9:16 720p, generate_audio false. Cost: preflight in request file (3 credits per second expected).
  Fidelity: source silent video as video reference, same duration, action script written out, fidelity lock; risk: Wan rebuilds the action (approx. recreate); sync-check after the merge.
  Text: "Me during earnings week" y_rel 0.13 (posY 0.74, posX 0) 0-10.2
  Guardrails: C6 politics: the right monitor's news headline (UK politics) replaced by a plain market chart (peripheral). Handle 'Financeaholic' removed. C3: one drink. C4: no coffee. Verdict pick-and-edit.
  ```
- **prompt:**
  ```text
  [Core Task] Generate a real phone-shot clip of a stressed trader at a three-monitor desk who takes a sip from a glass. The woman corresponds to Image 1, adopting only her facial features and hairstyle; she replaces only the man with glasses in the olive sweater in Video 1 and keeps the clothing, body and pose of Video 1; do not use the background, props, clothing or lighting of Image 1. Use Video 1 for every movement, expression, gaze, the framing and camera, the room and the timing; do not reproduce any text, captions, usernames or watermarks from Video 1. The can corresponds to Image 2 and Image 3, which jointly define the same can and generate only one instance, adopting only its structure, material, colours and printed label (a white slim aluminium can, a red-and-grey C-swoosh above the black CELSIUS wordmark with LIVE FIT, a cherries-and-cola illustration, SPARKLING CHERRY COLA in a magenta tag, a black band with three bullets and a silver-grey lower band); in Image 2 and Image 3 the can is deliberately small in the frame and keeps that small scale; do not use the framing, lighting, background or camera angle of Image 2 or Image 3. The right monitor in Video 1 shows a news web page with a red header, a politician's photo and a large headline: replace its whole screen with a plain dark candlestick chart (green and red candles on a dark background, no text, no headline, no photo, no red banner). Image 4 is only the colour, clarity and bubbles of the drink; nothing else in it is used.
  [Plot Summary] Shot: locked phone framing from the right side of a white desk, medium shot, the camera unchanged from Video 1; a dim home office, three monitors (left a chart, centre a dashboard, right a dark candlestick chart with no text at all and no news page), a keyboard and blue and red sticky notes on the desk. The woman sits at the right of the frame in profile facing the monitors, keeping the glasses of Video 1. She leans toward the right monitor and reads; puts both hands on her head and slumps; drops her right hand to the keyboard; picks up the glass from the desk at the right of the keyboard with her right hand, tips it to her lips, takes one sip with her head tilted back slightly and sets it down off the right edge; types and writes; points at the left monitor; leans in and types; points again; leans in and types. The small clear glass by the right monitor's base holds Celsius Cherry Cola poured from the can beside it: dark brown cola with fine fizz bubbles, as in Image 4. She sips from the glass through its rim, not from the can. An open Celsius Cherry Cola can with its black tab up stands upright on the desk right beside the glass, touching distance, at the same depth from the lens as the glass, behind the keyboard near the right monitor's base, label turned about thirty degrees toward the lens. The can and the glass are both on the desk from the very first frame to the last frame; the glass is lifted only at about three seconds, while the can never moves and is never touched, never picked up, and does not appear or disappear; always exactly one can and one glass, not duplicated. The can is small and far from the lens: 15.7 cm tall, only about 1.3 times as tall as the glass beside it, shorter than her hand is long, about one twelfth of the frame height, exactly this size throughout. After the sip the glass stands off-frame and is no longer seen; the can stays in its spot in view until the last frame. Real-time speed. No dialogue. No background music.
  [Camera & Core Constraints] Keep every movement, gesture, expression, gaze and mouth movement of the woman in Video 1 on the same frames, the props and how they are handled, the camera framing and handheld feel, the light, the room and the timing of Video 1 unchanged; no added, skipped, repeated or reordered action, no new gesture, no extra camera move, no re-staging, no new people, no change of pace. There is exactly one can (open, standing beside the glass, visible from the first frame to the last) and one glass of Cherry Cola; glass level drops slightly after the sip, small and constant in size, not duplicated, not deformed; the can stays where it is and fingers or objects never pass through it. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen; the only lettering is the printed label on the Celsius Cherry Cola can, exactly as in Image 2.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no scale drift, no slow motion, no speed ramps, no self-inserted cut points, no added or skipped action, no second can, no oversized can, no can taller than her hand is long, no can larger than a head, no can in the foreground, no can closer to the camera than the glass, no drinking from the can, no studio lighting on the can, no glow, no clipping, no news web page, no red header banner, no politician photo, no headline text on any monitor
  ```
- **params:** model=wan3_0_prime · duration=11 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=video_references, image_references×4 · request=video-04-a4-request.json
- **errors:** none
- **evidence:** not recorded
- **qc:**
  ```text
  RESIDUAL FAILURE (size only): a3 has the open can in frame from frame 0 to the end on one fixed spot (dense 0-1 s and 0-4.5 s checked, count 1, never touched); glass sipped once through the rim; headline gone. Can ~0.15 of frame height = ~1.65x planned (1/11) and in the left foreground, not beside the glass. a4 fixed size but vanished can / two glasses / drank from can, rejected. caught-error CE-018 NOT set to verified (QC not fully passed).
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261010-020703-09\40-briefs\video-04-plan.md
- **class:** text-and-format.md 1 and 3 (what source text is re-placed)
- **cause:** plan
- **fix:** none yet
- **verified prompt:** pending (inserted only after a new generation passes QC)
- **rule:** When a reference's only text is a short keyword or tag that defines its niche, ask whether it is the hook before dropping it as a handle: if the user keeps it, re-place it word for word as a CapCut text layer at the same height; the user's instruction outranks the 'never copy handles' default.
- **status:** promoted
- **promoted to:** text-and-format.md §1; command item 6, §7

## CE-028 · 2026-10-10 · False oversize flag: size computed from a wrong assumed distance
- **source:** user
- **video:** 06
- **run:** 20261010-020703-09
- **delivered:** CapCut project 10_Oct_2026_v06 · clean 60-outputs/video-06/clean.mp4 · credits 60 · run QC: RESIDUAL FAILURE size: can 2.79x expected at rest, 3.51x at last frame (a1 2.98x); count 1 ok, cut/fidelity ok, no stray text, CE-001..013 checked
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Celsius Watermelon can (V09 recreate, lecture hall)
- **assets:** not recorded
- **user said:** "it looks accurate though, more of a 1.07x and not 2.8x"
- **what was wrong:** The QC measured the can against an expected 7.6% of frame height, computed from an ASSUMED distance of about 1.5 m. In the shot the can stands on the near fold-out desk well under a metre from the lens (expected about 16%, observed 21%, about 1.3x by that reckoning, 1.07x by the user's eye). The agent delivered it flagged as a 2.8x residual failure, the main session repeated the number, and a size summary built on it was wrong. Other flags (04, 08, 11, 01) used different neighbours and distances and may be overstated too.
- **brief:**
  ```text
  # Video 06 brief: V09 alone in finance investment class (placement, Watermelon can on the tablet-arm desk)
  Concept: recreate V09 with Celsius Watermelon (placement); no person swap. Why it works: the reference's own mechanism, product native to the scene, noticed not featured.
  Model/operation: wan3_0_prime, video_references + image_references, 10 s, 9:16 720p, generate_audio false. Cost: preflight in request file (3 credits per second expected).
  Fidelity: source silent video as video reference, same duration, action script written out, fidelity lock; risk: Wan rebuilds the action (approx. recreate); sync-check after the merge.
  Text: "Alone girl in my Finance investment class" y_rel 0.81 (posY -0.62, posX 0) 0-9.2
  Guardrails: none (crowd is background; no swap). Verdict pick-clean.
  
  ## Attempt 2 (size regeneration)
  a1 (job ee3c477c, 30 cr) passed fidelity (one can, cut at about 6.1, original action kept) but the can measured 288 px of 1280 = 22.5% of frame height vs 7.5% expected (about 3x, also wider than the desk reads). Diagnosed regeneration: p20 padded refs (can one fifth of the image), desk-width neighbour (60 cm desk top), "tiny, 90 px" wording, extra no-giant exclusions. Request: 50-requests/video-06-a2-request.json (same params, 30 credits).
  ```
- **prompt:**
  ```text
  [Core Task] Recreate Video 1 as it is: a handheld phone video across a university lecture hall.  Use Video 1 for every movement, expression, gaze, the framing and camera, the room and the timing; do not reproduce any text, captions, usernames or watermarks from Video 1. The can corresponds to Image 1 and Image 2, which jointly define the same can and generate only one instance, adopting only its structure, material, colours and printed label (a white slim 355 ml aluminium can, a red-and-grey C-swoosh above the black CELSIUS wordmark with LIVE FIT, a watermelon-slice illustration, SPARKLING WATERMELON in red, a black band with three bullets and a silver-grey lower band); in Image 1 and Image 2 the can is deliberately tiny in the frame, one fifth of the image height, and keeps that tiny scale; do not use the framing, lighting, exposure, background, shadow or camera angle of Image 1 or Image 2.
  [Plot Summary] Shot: handheld phone video, portrait, one hard cut at about 6.1 s of Video 1; keep the camera path, every person, every movement, the room and the timing exactly as in Video 1, including the students seated in the middle and the laptop screen that drifts into the lower right of the frame at the camera's drift (the screen shows only a soft, out-of-focus spreadsheet with no readable text). The only change: a closed Celsius Watermelon can stands upright on the white fold-out tablet-arm desk of the empty swivel seat in the foreground at the lower left of the frame (the desk seen at the lower left in the first and last parts), its base on the desk with a contact shadow, label turned about thirty degrees toward the lens; it is part of this scene although Video 1 has none, it stays on that desk the whole clip, nobody touches it; when the camera drifts away to the laptop it is out of frame and it is back on the same desk after the cut. The can is a very small object, 15.7 cm tall and 5.5 cm across, standing on a desk top that is about 60 cm wide and 40 cm deep, about 1.5 metres from the lens: the can is only one tenth of the desk top's width across and well under half of its depth tall, about the length of the seat's armrest post, a third of the seat's backrest height, and clearly smaller than the head of a seated student; it fills only about one fourteenth of the frame height (about 90 pixels of 1280), a tiny can far from the lens, not a close-up product, with its watermelon label just readable. Cool window light from the left and ceiling light from above; the can takes the same light with a soft contact shadow. Real-time speed. No dialogue. No background music.
  [Camera & Core Constraints] Keep every movement, gesture, expression, gaze and mouth movement of the people in Video 1 on the same frames, the props and how they are handled, the camera framing and handheld feel, the light, the room and the timing of Video 1 unchanged; no added, skipped, repeated or reordered action, no new gesture, no extra camera move, no re-staging, no new people, no change of pace. There is exactly one can on the tablet-arm desk when that desk is in frame; every other element of Video 1 unchanged, small and constant in size, not duplicated, not vanished, not deformed, no scale drift; the can stays where it is and fingers or objects never pass through it. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen; the only lettering is the printed label on the Celsius Watermelon can, exactly as in Image 1; do not reproduce any text, captions, usernames or watermarks from Video 1.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no scale drift, no cut-out edges, no slow motion, no speed ramps, no self-inserted cut points, no added or skipped action, no second can, no oversized can, no can taller than the seat's backrest is tall, no can larger than a head, no giant can, no can wider than a tenth of the desk top, no close-up of the can, no hero shot, no open tab, no drinking from the can, no studio lighting on the can, no glow, no clipping
  ```
- **params:** model=wan3_0_prime · duration=10 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=video_references, image_references×2 · request=video-06-a2-request.json
- **errors:** none
- **evidence:** not recorded
- **qc:**
  ```text
  RESIDUAL FAILURE size: can 2.79x expected at rest, 3.51x at last frame (a1 2.98x); count 1 ok, cut/fidelity ok, no stray text, CE-001..013 checked
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261010-020703-09\40-briefs\video-06-plan.md
- **class:** anomaly-catalog.md 2.7 (size reckoning) and 4 (QC); production-agents.md 3 (contract)
- **cause:** qc-miss
- **fix:** none yet
- **verified prompt:** pending (inserted only after a new generation passes QC)
- **rule:** Never take the distance from an assumption: derive it from a same-plane neighbour of known size or from the surface the product stands on in the frame, with two independent estimates (neighbour ratio and frame fraction) that must agree before an oversize verdict; a verdict from one assumed number is provisional and must be viewed on a frame before it is reported or repeated; when the user's eye disagrees the verdict is re-measured, not defended.
- **status:** promoted
- **promoted to:** anomaly-catalog.md §2.7, §4 step 5d, §4.1; generation-system.md §8, §9; production-agents.md §2, §3 items 13-14, §5; command X1, X4, X9, A9b, §6, §7; scripts/atp.py scale (--distance-basis, provisional guard); wan-3-0.md §5 caveat, §9

## CE-029 · 2026-10-10 · Swapped face lighter-skinned than the kept body
- **source:** user
- **video:** 13
- **run:** 20261010-020703-09
- **delivered:** CapCut project 10_Oct_2026_v13 · clean C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261010-020703-09/60-outputs/video-13/clean.mp4 · credits 60 · run QC: RESIDUAL FAILURE (size): a2 carton 1.33x expected vs laptop (a1 1.43x); carton flat, present from frame 0, same spot in all 3 shots, counts 1/1/1, no contact, action/identity/cuts ok
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Neuro Peppermint carton (V01 recreate, hooded man at laptop)
- **assets:** not recorded
- **user said:** "regenerate it again because the face of the character is white meanwhile the body is of a black person"
- **what was wrong:** The identity image (char-A09) has a lighter-skinned face while the source performer's body, hands and forearms (kept through the video reference) are dark-skinned, so the output shows a white face on a black body. result.json had already noted 'Hands look darker than the face (source hands kept)' and the run delivered anyway; QC compared counts, size and sync but not face vs neck vs hands tone.
- **brief:**
  ```text
  # Video 13 brief: V01 first 10k online (placement, Neuro Peppermint carton flat on the white table)
  Concept: recreate V01 with the Neuro Energy & Focus Extra Strength Peppermint 9-piece carton (placement, lying flat on the white table); char-A09.png. Replaces video 11 (barbecue, CE-020): a work/focus scene fits Neuro. Product noticed, not featured.
  Model/operation: wan3_0_prime, video_references + image_references, 10 s, 9:16 720p, generate_audio false. Cost: preflight in request file (3 credits per second expected).
  Fidelity: source silent video as video reference, same duration, action script written out, fidelity lock; risk: Wan rebuilds the action (approx. recreate); sync-check after the merge.
  Text: "18yr olds as soon as they make their first 10k online:" y_rel 0.13 (posY 0.74, posX 0) 0-9.7
  Guardrails: N1-N15 checked, no hit (adult swap, no claim in caption, original audio). Verdict pick-clean (+ person swap; hood/durag kept). Caught errors: CE-001..013, 019, 020, 021, 022.
  ```
- **prompt:**
  ```text
  [Core Task] Generate a real phone-shot clip of three shots: a man at a laptop panics then calms, then stands at windows. The man corresponds to Image 1, adopting only his facial features, beard and hairstyle; he replaces only the man in the black hood and durag in Video 1 and keeps the hood, durag, clothing, body and pose of Video 1; do not use the background, props, clothing or lighting of Image 1. Use Video 1 for every movement, expression, gaze, the framing and camera, the room and the timing; do not reproduce any text, captions, usernames or watermarks from Video 1. The carton corresponds to Image 2 and Image 3, which jointly define the same carton and generate only one instance, adopting only its structure, material, colours and printed label (a small flat light-blue paperboard carton with a Neuro wordmark top-left, a purple-and-mint GUM badge with an EXTRA STRENGTH tab top-right, a Peppermint tag, the title Energy & Focus, the line 9 Pieces | Dietary Supplement and a dark-blue band reading 100MG OF NATURAL CAFFEINE); in Image 2 and Image 3 the carton is deliberately small in the frame and keeps that small scale; do not use the framing, lighting, exposure, background, shadow or camera angle of Image 2 or Image 3.
  [Plot Summary] Video 1 has two changes of shot, one hard cut at about 3.3 s and one dissolve through white at about 4.9 s; keep both at the same moments. Shot 1, locked mid shot from table height: the man in a black hooded zip hoodie and a dark durag sits at a white table in front of an open dark laptop, a cream vertical-blind wall behind; he types looking down, bites his fist and shakes, drags a hand down over his hooded face, throws both hands up and shakes his head, then closes the laptop with both hands and rests his palms flat on the lid, talking. Shot 2: from behind, he stands at the vertical blinds with one hand on them, the closed black laptop on the white table at the bottom of the frame. Shot 3, after the dissolve: he stands with his back to a floor-to-ceiling night-time city window, hands behind his back, the closed laptop on the table at the bottom, almost no movement. A closed Neuro Energy & Focus Extra Strength Peppermint 9-piece carton lies completely flat on the bare white table to the right of the laptop, from the very first frame to the last, its large printed face up and parallel to the table top, never standing, never leaning, never propped, on the bare table and not on any paper, a full hand-width clear of his hands and of the laptop, with a thin contact shadow; it is part of this scene although Video 1 has none, it never moves, nobody touches it. It stays on this exact spot in all three shots: in shot 2 and in shot 3 it is still lying on the white table at the right of the closed laptop, visible as a small blue square in the lower part of the frame. The carton is a very small flat pack, 7.5 cm by 7.5 cm and 1.6 cm thick: slightly narrower than his flat hand is wide, only a quarter of the width of the laptop lid, much smaller than the laptop; in shot 1 (a wide framing, about 1.1 m away) it fills only about one thirtieth of the frame width, a tiny blue square on the white table, and it keeps this small size in shots 2 and 3. Soft cool daylight from the left in shot 1, dim city light in shot 3, the carton takes the same light. Real-time speed. No dialogue. No background music.
  [Camera & Core Constraints] Keep every movement, gesture, expression, gaze and mouth movement of the man in Video 1 on the same frames, the props and how they are handled, the camera framing and handheld feel, the light, the room and the timing of Video 1 unchanged; no added, skipped, repeated or reordered action, no new gesture, no extra camera move, no re-staging, no new people, no change of pace. There is exactly one carton, closed, flat, never opened, right of the laptop, visible in all three shots; one laptop (open then closed), small and constant in size, not duplicated, not vanished, not deformed, no scale drift; the carton stays where it is and fingers or objects never pass through it. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen; the only lettering is the printed label on the Neuro carton, exactly as in Image 2; do not reproduce any text, captions, usernames or watermarks from Video 1.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no scale drift, no cut-out edges, no slow motion, no speed ramps, no self-inserted cut points, no added or skipped action, no second carton, no oversized carton, no carton larger than a hand, no carton wider than a quarter of the laptop lid, no carton vanishing, no carton moving, no carton opened, no carton standing on its edge or leaning, no carton propped on anything, no carton on paper, no studio lighting on the carton, no glow, no clipping
  ```
- **params:** model=wan3_0_prime · duration=10 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=video_references, image_references×3 · request=video-13-a2-request.json
- **errors:** none
- **evidence:** not recorded
- **qc:**
  ```text
  RESIDUAL FAILURE (size): a2 carton 1.33x expected vs laptop (a1 1.43x); carton flat, present from frame 0, same spot in all 3 shots, counts 1/1/1, no contact, action/identity/cuts ok
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261010-020703-09\40-briefs\video-13-plan.md
- **class:** generation-system.md 9b / anomaly-catalog.md identity (swapped person); analysis-protocol.md character pick
- **cause:** plan
- **fix:** regenerated with a dark-skinned character (A28) matched to the source performer, skin-tone sentence and exclusion in the prompt; a4 accepted: face and hands one tone, carton from frame 0
- **verified prompt:** pending (inserted only after a new generation passes QC)
- **rule:** A swapped identity must match the source performer's skin tone and ethnicity on the whole body (face, neck, hands, forearms) because the video reference keeps the body; pick the character by skin tone and build before style, state the tone match in the prompt with an exclusion against a lighter or darker face, and QC compares face vs neck vs hands tone on a full-resolution frame with an evidence path; a noted tone mismatch is a regenerate reason, never a delivered note.
- **status:** promoted
- **promoted to:** anomaly-catalog.md 2.17, 4 (5e); build prompt

## CE-030 · 2026-10-12 · Mirrored source: shirt text and guitar read reversed while the placed pouch does not
- **source:** user
- **video:** 20
- **run:** 20261007-232745-07
- **delivered:** CapCut project 08_Oct_2026_v20 · clean C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07/60-outputs/video-20/clean.mp4 · credits 15 · run QC: accepted
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Neuro Energy & Focus Extra Strength Spearmint pouch (V06 recreate, study desk, placement)
- **assets:** A01 (character); A767.jpg, A768.jpg (Neuro Extra Strength Spearmint pouch, registry P3 about 17.9 x 10.2 x 4.6 cm); source Video-33468.mp4 (V06, mirrored)
- **user said:** "this one works better, but everything in the frame is reversed except the bag. Text on his shirt, guitar on the wall. Maybe flip video, then add bag. Also, maybe bag here is open, it's still sealed. I think he'd have it open if he's in class."
- **what was wrong:** (Client point 1.) The reference V06 (Video-33468) is itself a mirrored selfie: its card says 'image mirrored', so the creator's T-shirt print and the left-handed guitar on the wall are reversed in the source. Recreate used the source unchanged as the video reference, so the generation kept the mirror for everything the source holds (shirt print reads GEN/GFA reversed, guitar left-handed, room), while the pouch is drawn from its own un-mirrored label: the frame contradicts itself and the product is the only thing that reads correctly. The QC verdict even lists 'the mirrored T-shirt print' among the OCR extras and accepted; no plan step handled a mirrored source. The client's fix: flip the source first, then add the product.
- **brief:**
  ```text
  Video 20 of 22 — NEUROGUM — Recreate V06
  Concept: V06 recreated beat for beat with character A01 and the Neuro Extra Strength Energy & Focus gum pouch (Spearmint).
  Reference pattern: V06 card (timing, beats, inserts at 3.07-5.00).
  Characters/assets: A01 (Image 1); A767.jpg, A768.jpg.
  House approach: none (no examples).
  Substitutions: creator → A01 | Placement: stands on the desk at the lower-left, left of the notebook, label toward the camera, in the same spot before and after the cut.
  Main action & states: source beats unchanged; product untouched and persistent.
  Style & camera: as V06, static phone camera, the source's light.
  Text: CapCut layers in the house style, reference wording/positions (see plan).
  Inserts: V06 3.07-5.00.
  Sound: original audio restored; inserts with their own sound.
  Model & operation: wan3_0_prime reference-to-video (≈ recreate from Video 1), 5 s → trim 5.000 s, 9:16 720p, audio off, thinking on · est. 15 credits
  Fidelity: Video 1 = silent own content (motion/camera/timing), action script written out in order, keep-list + exclusions, same duration; sync-check after the merge. Risk: low.
  Adaptation logic: product placed at the analysed anchor; source branding dropped.
  ```
- **prompt:**
  ```text
  [Core Task] Recreate Video 1 as a real phone-shot vertical clip with only these changes: the person and the product. Video 1 is the motion, camera, framing, cut and timing reference: keep every movement, gesture, head turn, gaze, expression and mouth movement of the person in Video 1 in the same order, at the same moments and at the same real-time speed, and keep the camera, framing, cuts, light, room and background of Video 1. Do not inherit the appearance, clothing, text, captions, stickers, usernames, watermarks or branded items of Video 1. The young man corresponds to Image 1, adopting facial features, hairstyle, skin tone, build and clothing (short brown hair, trimmed beard); Image 1 is only this person's identity, not its pose, its background or any object in it. The young man replaces the person of Video 1 and performs exactly that person's movements. The Neuro Extra Strength Energy & Focus gum pouch (Spearmint) corresponds to Image 2 (front) and Image 3 (angled view); both images jointly define one single package, adopting its exact structure, material and colour: a sealed stand-up pouch about 13 cm wide and 18 cm tall, light turquoise with large brighter-cyan wave shapes and a zip seal near the top, a dark-blue Neuro wordmark, a small dark-blue EXTRA STRENGTH badge over a green GUM badge, a green Spearmint tag, the dark-blue title Energy & Focus and a dark-blue base band with white lettering. Keep its exact shape, proportions and printed artwork without deformation and without scale drift; it stays closed. Video 1 has no such item, but the Neuro Extra Strength Energy & Focus gum pouch (Spearmint) is part of this scene from the first frame: it stands on the desk at the lower-left, left of the notebook, label toward the camera, in the same spot before and after the cut, at its real size, lit by the scene's own light with a soft contact shadow, untouched and in the same place for the whole clip. Only one exists in the scene.
  [Plot Summary] Shot 1 [0-3.1s]: Static selfie framing, medium close-up, slightly low; guitars on the wall at frame-right. The young man sits leaning slightly forward over a blue notebook on the desk, head bowed, eyes half-closed, the frame-right hand writing short strokes with a silver pen, the frame-left hand resting by the chest, lips moving as if explaining. He releases the pen onto the notebook and both hands rise to chest height with palms open and fingers spread, making alternating explanatory gestures, head tilting side to side, lips moving, earnest. Then the frame-left index finger goes to the lips and chin, eyes rolled up thinking, mouth closed, as the image brightens toward white.
  Shot 2 [3.1-5.0s]: Hard cut, same framing: smiling, he points a finger toward the lens, then sweeps the hand down toward the desk; the frame-right hand picks the pen up from the notebook and writes, head slightly down, eyes up to the lens, a smug half-smile; while still writing, the frame-left index finger taps the temple, eyebrows up.
  [Audio Style] No dialogue. No background music. No sound effects.
  [Camera & Core Constraints] Camera: static throughout. Real-time speed, nothing added, skipped, repeated or reordered, no new gesture, no extra camera move, no re-staging, no new people or background action. No subtitles, captions or other on-screen text; do not reproduce any text, captions, usernames or watermarks from Video 1; the only lettering is the printed label on the package, exactly as in Image 2.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no extra fingers, no duplicate packages, no product deformation, no scale drift, no slow motion, no speed ramps, no other drink or snack brands, no logo stickers
  ```
- **params:** model=wan3_0_prime · duration=5 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=image_references×3, video_references · request=video-20-request.json
- **errors:** none
- **evidence:** deliverables/video-20-preview.mp4 at about 1.0 s (shirt print, guitar); source card 20-analysis/cards/V06.md ('image mirrored'); QC note in 60-outputs/video-20/result.json
- **qc:**
  ```text
  {"video": "20", "mode": "recreate", "status": "done", "clean": "C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07/60-outputs/video-20/clean.mp4", "capcut_project": "08_Oct_2026_v20", "capcut_pending": false, "preview": "C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07/60-outputs/video-20/capcut-preview.mp4", "jobs": [{"clip": "c1", "job_id": "49559639-fd57-4c68-b165-bad799ce957f", "credits": 15, "attempts": 1}], "credits": 15, "qc": "accepted", "continuity": "counts: pouch 1/1/1/1 at 0.0, 2.9 (pre-insert), 3.2 (post-insert), 4.9 | use: none (placement, untouched, sealed) | permanence: same spot, size, label orientation across the white dissolve/insert cut; pen pickup ~3.75 s and temple tap ~4.67 s land as in source", "sync": "in_sync", "blocker": null, "notes": "A01 + one sealed Neuro Extra Strength Energy & Focus Spearmint pouch upright at desk lower-left, left of the notebook, label matching A767/A768, same spot both sides of the insert. Generation kept the source's dissolve to white (no fade rebuild needed). Insert i1 V06 3.07-5.00 at 3.067 s, reusing the cleaned shared V06-i1 (caption covered with the frame's black letterbox bar). POV text moved from reference y_rel 0.656 to 0.10 (that spot covered the pouch label). Pouch colour wording in the prompt corrected before preflight. lint 0 errors, text style check 0 off. Preview rendered with ffmpeg/libass (capcut render fontconfig error). QC OCR extras are pouch label text and the mirrored T-shirt print."}
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261007-232745-07\40-briefs\video-20-plan.md
- **class:** generation-system.md §5c.2 (source preparation before it rides as the video reference); anomaly-catalog.md §2.9 (orientation, label and parts); analysis-protocol.md (card must flag a mirrored source)
- **cause:** plan
- **fix:** Video 1 = own-silent hflipped (own-silent-flipped.mp4); ALSO Image 1 flipped (A01-flipped.jpg) because the A01 selfie photo was itself mirrored (its chest print read reversed), so flipping only the video would have left the shirt text reversed; action script written with the sides swapped, pouch moved to the right of the notebook; prompt states 'nothing is mirrored, all lettering reads left to right' plus mirror negatives; QC checks every readable thing and handed object (guitar, notebook side, pen hand, label)
- **verified prompt:**
  ```text
  [Core Task] Recreate Video 1 as a real phone-shot vertical clip with only these changes: the person and the product. Video 1 is already in true orientation and is the motion, camera, framing, cut and timing reference: keep every movement, gesture, head turn, gaze, expression and mouth movement of the person in Video 1 in the same order, at the same moments and at the same real-time speed, and keep the camera, framing, light, room and background exactly as in Video 1, with the same left and right (guitars on the wall at the frame-left, the blue notebook at the lower frame-left, the pen in the frame-left hand); nothing is mirrored or flipped and all lettering reads correctly from left to right. Do not inherit the appearance, clothing, text, captions, usernames, watermarks or branded items of Video 1. The young man corresponds to Image 1, adopting facial features, hairstyle, skin tone, build and clothing (short brown hair, trimmed beard, a plain black crew-neck t-shirt with no print, no lettering and no logo); Image 1 is only his identity and clothing, not its pose, background or objects. He replaces the person of Video 1 and performs exactly that person's movements. The Neuro Extra Strength Energy & Focus gum pouch (Spearmint) corresponds to Image 2 (front) and Image 3 (angled view); both jointly define one single pouch, only its shape, proportions, colours and printed label, not their lighting, background, shadow or camera angle: a stand-up pouch about 18 cm tall, 10 cm wide and 5 cm deep, light turquoise with large brighter-cyan wave shapes, the dark-blue Neuro wordmark top-left, a small dark-blue EXTRA STRENGTH badge over a green GUM badge top-right, a green Spearmint tag, the large dark-blue title Energy & Focus, 90 Pieces Dietary Supplement, and a dark-blue base band reading 100MG OF NATURAL CAFFEINE; the label reads exactly as in Image 2, upright and never mirrored, without deformation and without scale drift.
  [Plot Summary] From the first frame to the last, an open Neuro Extra Strength Energy & Focus gum pouch (Spearmint) stands upright on its flat gusseted base on the bare black desk to the right of the blue notebook, its top strip torn off at the tear notches and its zipper mouth open, a few round white tablets with green flecks just visible inside the dark mouth, its label turned about twenty degrees toward the lens; it is part of this scene although Video 1 has none. It is about as tall as his hand is long and a little shorter than the notebook is wide, at the notebook's depth about half a metre from the lens, its left side two finger-widths from the notebook's right edge, lit by the room's soft light with a soft contact shadow like the notebook's. Nobody touches it, nothing is poured or taken, the pen is the only object he picks up, and the pouch stays exactly there in every frame, also after the white flash.
  Shot 1 [0-3.1s]: Static selfie framing, medium close-up, slightly low. The young man sits leaning slightly forward over the notebook, head bowed, eyes half-closed, his frame-left hand writing short strokes with a silver pen, his frame-right hand resting by his chest, lips moving as if explaining. He releases the pen onto the notebook and both hands rise to chest height, palms open, fingers spread, alternating explanatory gestures, head tilting side to side, earnest. Then his frame-right index finger goes to his lips and chin, eyes rolled up thinking, mouth closed, as the image brightens to white.
  Shot 2 [3.1-5.0s]: Out of the white, same framing: smiling, his frame-right hand points a finger toward the lens and sweeps down in front of him; his frame-left hand picks the pen up from the notebook and writes, head slightly down, eyes up to the lens, a smug half-smile; while still writing, his frame-right index finger taps his temple, eyebrows up. The open pouch is still there, one pouch, the same spot.
  [Audio Style] No dialogue. No background music. No sound effects.
  [Camera & Core Constraints] Camera static, phone-shot look, everything in focus. Real-time speed, nothing added, skipped, repeated or reordered, no new gesture, no camera move, no re-staging, no new people. Always exactly one pouch, open, upright, never poured, not duplicated, not vanished, not deformed. No subtitles or on-screen text; the only lettering is the pouch label exactly as in Image 2; the t-shirt carries no lettering.
  [Negative Prompts] no subtitles, no watermark, no text or print on the t-shirt, no mirrored image, no reversed lettering, no mirrored label, no face distortion, no identity drift, no costume changes, no extra fingers, no second pouch, no sealed pouch, no loose gum pieces on the desk, no spilled gum, no hand taking a piece, no chewing, no hand touching the pouch, no moving pouch, no oversized pouch, no pouch closer to the camera than the notebook, no pouch taller than his hand is long, no scale drift, no slow motion, no speed ramps, no other brands, no logo stickers
  ```
- **prompt change:**
  ```text
  - Video 1 is the motion, camera, framing, cut and timing reference: keep every movement, gesture, head turn, gaze, expression and mouth movement of the person in Video 1 in the same order, at the same moments and at the same real-time speed, and keep the camera, framing, cuts, light, room and backgrou
  - Do not inherit the appearance, clothing, text, captions, stickers, usernames, watermarks or branded items of Video 1.
  - The young man corresponds to Image 1, adopting facial features, hairstyle, skin tone, build and clothing (short brown hair, trimmed beard);
  - Image 1 is only this person's identity, not its pose, its background or any object in it.
  - The young man replaces the person of Video 1 and performs exactly that person's movements.
  + Video 1 is already in true orientation and is the motion, camera, framing, cut and timing reference: keep every movement, gesture, head turn, gaze, expression and mouth movement of the person in Video 1 in the same order, at the same moments and at the same real-time speed, and keep the camera, fram
  + nothing is mirrored or flipped and all lettering reads correctly from left to right.
  + Do not inherit the appearance, clothing, text, captions, usernames, watermarks or branded items of Video 1.
  + The young man corresponds to Image 1, adopting facial features, hairstyle, skin tone, build and clothing (short brown hair, trimmed beard, a plain black crew-neck t-shirt with no print, no lettering and no logo);
  + Image 1 is only his identity and clothing, not its pose, background or objects.
  + He replaces the person of Video 1 and performs exactly that person's movements.
  - both images jointly define one single package, adopting its exact structure, material and colour: a sealed stand-up pouch about 13 cm wide and 18 cm tall, light turquoise with large brighter-cyan wave shapes and a zip seal near the top, a dark-blue Neuro wordmark, a small dark-blue EXTRA STRENGTH ba
  - Keep its exact shape, proportions and printed artwork without deformation and without scale drift;
  - it stays closed.
  … 37 more changed sentences
  ```
- **verified params:** model=wan3_0_prime · duration=5 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=image_references×3, video_references · request=video-20-fix-a2-request.json
- **rule:** A source whose picture is mirrored (a front-camera selfie shown un-flipped: reversed shirt text, left-handed guitar, reversed signs) is un-mirrored in the preparation step, before it is uploaded as the video reference, so that everything readable or handed in the generated frame is correct and agrees with the placed product's own label; the analysis card flags 'mirrored' with the evidence frame, and QC treats reversed text or handed objects in the generated frame as a fail, never as OCR noise.
- **status:** fixed
- **promoted to:** —
- **verified:** a2 accepted (job 0edb3b0c-748c-475c-a68f-638579a7813a, ledger lane 20-fix attempt 3): un-mirrored room (guitars frame-left right-handed, notebook lower-left, pen in the frame-left hand), plain black tee with no readable text (OCR none), pouch label unmirrored and legible at full resolution (Neuro, EXTRA STRENGTH, GUM, Spearmint, Energy & Focus, 90 Pieces, 100MG OF NATURAL CAFFEINE), pouch OPEN (torn top, tablets in the mouth only) count 1 in every dense checkpoint and in 143 of 150 mask frames (rest are the white flash), same spot across the flash (x0 388-389 before, 386 after, drift <=3 px), nothing passes through it; size 1.15-1.23x by two methods (A and B agree, 15-25 pct note band, static, label readable); sync-check in_sync (offset -0.1 s, corr 0.83); original audio whole (decoded md5 identical); white flash rebuilt on own moving frames, no frozen frame; text layer posX 0, no emoji; evidence 60-outputs/video-20/fix-20261012/ (a2/qc/dense, assembly/qc/dense, a2/sync/sync-sheet.jpg, size/*.json, a2/f/label4.0.png, anchor-track.txt) (2026-10-12)

## CE-031 · 2026-10-12 · Pouch stays sealed although the person is in a class scene and would have it open
- **source:** user
- **video:** 20
- **run:** 20261007-232745-07
- **delivered:** CapCut project 08_Oct_2026_v20 · clean C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07/60-outputs/video-20/clean.mp4 · credits 15 · run QC: accepted
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Neuro Energy & Focus Extra Strength Spearmint pouch (V06 recreate, study desk, placement)
- **assets:** A767.jpg, A768.jpg (Neuro Extra Strength Spearmint pouch)
- **user said:** "this one works better, but everything in the frame is reversed except the bag. Text on his shirt, guitar on the wall. Maybe flip video, then add bag. Also, maybe bag here is open, it's still sealed. I think he'd have it open if he's in class."
- **what was wrong:** (Client point 2.) The plan fixed the pouch as 'sealed, untouched, upright' for every placement (the closed-pack default from the openings rule, CE-002, and the placement rule that the story never changes for the product). In this story the creator sits at a study desk explaining something in class; the client reads a sealed bag as unnatural there and expects it open. The default ignored the scene's own logic of use. No guardrail file existed in this run, so nothing forbade an open pouch; the default came from the pipeline's own habit, not from a client rule. Note for the plan: the pouch has a zipper under the top seal (registry), so 'open' means the top torn and the zipper mouth showing, standing upright, still one pouch, never poured; the Neuro memory rules (no opened carton with blister sticking out, no 6-pack box) do not cover an open pouch, so confirm before applying it elsewhere.
- **brief:**
  ```text
  Video 20 of 22 — NEUROGUM — Recreate V06
  Concept: V06 recreated beat for beat with character A01 and the Neuro Extra Strength Energy & Focus gum pouch (Spearmint).
  Reference pattern: V06 card (timing, beats, inserts at 3.07-5.00).
  Characters/assets: A01 (Image 1); A767.jpg, A768.jpg.
  House approach: none (no examples).
  Substitutions: creator → A01 | Placement: stands on the desk at the lower-left, left of the notebook, label toward the camera, in the same spot before and after the cut.
  Main action & states: source beats unchanged; product untouched and persistent.
  Style & camera: as V06, static phone camera, the source's light.
  Text: CapCut layers in the house style, reference wording/positions (see plan).
  Inserts: V06 3.07-5.00.
  Sound: original audio restored; inserts with their own sound.
  Model & operation: wan3_0_prime reference-to-video (≈ recreate from Video 1), 5 s → trim 5.000 s, 9:16 720p, audio off, thinking on · est. 15 credits
  Fidelity: Video 1 = silent own content (motion/camera/timing), action script written out in order, keep-list + exclusions, same duration; sync-check after the merge. Risk: low.
  Adaptation logic: product placed at the analysed anchor; source branding dropped.
  ```
- **prompt:**
  ```text
  [Core Task] Recreate Video 1 as a real phone-shot vertical clip with only these changes: the person and the product. Video 1 is the motion, camera, framing, cut and timing reference: keep every movement, gesture, head turn, gaze, expression and mouth movement of the person in Video 1 in the same order, at the same moments and at the same real-time speed, and keep the camera, framing, cuts, light, room and background of Video 1. Do not inherit the appearance, clothing, text, captions, stickers, usernames, watermarks or branded items of Video 1. The young man corresponds to Image 1, adopting facial features, hairstyle, skin tone, build and clothing (short brown hair, trimmed beard); Image 1 is only this person's identity, not its pose, its background or any object in it. The young man replaces the person of Video 1 and performs exactly that person's movements. The Neuro Extra Strength Energy & Focus gum pouch (Spearmint) corresponds to Image 2 (front) and Image 3 (angled view); both images jointly define one single package, adopting its exact structure, material and colour: a sealed stand-up pouch about 13 cm wide and 18 cm tall, light turquoise with large brighter-cyan wave shapes and a zip seal near the top, a dark-blue Neuro wordmark, a small dark-blue EXTRA STRENGTH badge over a green GUM badge, a green Spearmint tag, the dark-blue title Energy & Focus and a dark-blue base band with white lettering. Keep its exact shape, proportions and printed artwork without deformation and without scale drift; it stays closed. Video 1 has no such item, but the Neuro Extra Strength Energy & Focus gum pouch (Spearmint) is part of this scene from the first frame: it stands on the desk at the lower-left, left of the notebook, label toward the camera, in the same spot before and after the cut, at its real size, lit by the scene's own light with a soft contact shadow, untouched and in the same place for the whole clip. Only one exists in the scene.
  [Plot Summary] Shot 1 [0-3.1s]: Static selfie framing, medium close-up, slightly low; guitars on the wall at frame-right. The young man sits leaning slightly forward over a blue notebook on the desk, head bowed, eyes half-closed, the frame-right hand writing short strokes with a silver pen, the frame-left hand resting by the chest, lips moving as if explaining. He releases the pen onto the notebook and both hands rise to chest height with palms open and fingers spread, making alternating explanatory gestures, head tilting side to side, lips moving, earnest. Then the frame-left index finger goes to the lips and chin, eyes rolled up thinking, mouth closed, as the image brightens toward white.
  Shot 2 [3.1-5.0s]: Hard cut, same framing: smiling, he points a finger toward the lens, then sweeps the hand down toward the desk; the frame-right hand picks the pen up from the notebook and writes, head slightly down, eyes up to the lens, a smug half-smile; while still writing, the frame-left index finger taps the temple, eyebrows up.
  [Audio Style] No dialogue. No background music. No sound effects.
  [Camera & Core Constraints] Camera: static throughout. Real-time speed, nothing added, skipped, repeated or reordered, no new gesture, no extra camera move, no re-staging, no new people or background action. No subtitles, captions or other on-screen text; do not reproduce any text, captions, usernames or watermarks from Video 1; the only lettering is the printed label on the package, exactly as in Image 2.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no extra fingers, no duplicate packages, no product deformation, no scale drift, no slow motion, no speed ramps, no other drink or snack brands, no logo stickers
  ```
- **params:** model=wan3_0_prime · duration=5 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=image_references×3, video_references · request=video-20-request.json
- **errors:** none
- **evidence:** deliverables/video-20-preview.mp4 whole clip (pouch upright and sealed, desk lower-left)
- **qc:**
  ```text
  {"video": "20", "mode": "recreate", "status": "done", "clean": "C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07/60-outputs/video-20/clean.mp4", "capcut_project": "08_Oct_2026_v20", "capcut_pending": false, "preview": "C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07/60-outputs/video-20/capcut-preview.mp4", "jobs": [{"clip": "c1", "job_id": "49559639-fd57-4c68-b165-bad799ce957f", "credits": 15, "attempts": 1}], "credits": 15, "qc": "accepted", "continuity": "counts: pouch 1/1/1/1 at 0.0, 2.9 (pre-insert), 3.2 (post-insert), 4.9 | use: none (placement, untouched, sealed) | permanence: same spot, size, label orientation across the white dissolve/insert cut; pen pickup ~3.75 s and temple tap ~4.67 s land as in source", "sync": "in_sync", "blocker": null, "notes": "A01 + one sealed Neuro Extra Strength Energy & Focus Spearmint pouch upright at desk lower-left, left of the notebook, label matching A767/A768, same spot both sides of the insert. Generation kept the source's dissolve to white (no fade rebuild needed). Insert i1 V06 3.07-5.00 at 3.067 s, reusing the cleaned shared V06-i1 (caption covered with the frame's black letterbox bar). POV text moved from reference y_rel 0.656 to 0.10 (that spot covered the pouch label). Pouch colour wording in the prompt corrected before preflight. lint 0 errors, text style check 0 off. Preview rendered with ffmpeg/libass (capcut render fontconfig error). QC OCR extras are pouch label text and the mirrored T-shirt print."}
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261007-232745-07\40-briefs\video-20-plan.md
- **class:** generation-system.md §4b.4 (lived-in pose and state of a placed product); anomaly-catalog.md §2.2 (openings and use) and §2.4 (persistent states)
- **cause:** plan
- **fix:** Open pouch written as ONE positive sentence in the first clause of the Plot Summary (top torn at the tear notches, zipper mouth open, a few tablets with green flecks visible in the mouth only, upright on its gusset, label ~20 degrees toward the lens, left side two finger-widths from the notebook's right edge), exclusions in the negatives (sealed, second pouch, loose or spilled gum, a hand taking a piece, chewing, hand touching the pouch); story reason: he chews gum at his class desk; nobody touches it
- **verified prompt:**
  ```text
  [Core Task] Recreate Video 1 as a real phone-shot vertical clip with only these changes: the person and the product. Video 1 is already in true orientation and is the motion, camera, framing, cut and timing reference: keep every movement, gesture, head turn, gaze, expression and mouth movement of the person in Video 1 in the same order, at the same moments and at the same real-time speed, and keep the camera, framing, light, room and background exactly as in Video 1, with the same left and right (guitars on the wall at the frame-left, the blue notebook at the lower frame-left, the pen in the frame-left hand); nothing is mirrored or flipped and all lettering reads correctly from left to right. Do not inherit the appearance, clothing, text, captions, usernames, watermarks or branded items of Video 1. The young man corresponds to Image 1, adopting facial features, hairstyle, skin tone, build and clothing (short brown hair, trimmed beard, a plain black crew-neck t-shirt with no print, no lettering and no logo); Image 1 is only his identity and clothing, not its pose, background or objects. He replaces the person of Video 1 and performs exactly that person's movements. The Neuro Extra Strength Energy & Focus gum pouch (Spearmint) corresponds to Image 2 (front) and Image 3 (angled view); both jointly define one single pouch, only its shape, proportions, colours and printed label, not their lighting, background, shadow or camera angle: a stand-up pouch about 18 cm tall, 10 cm wide and 5 cm deep, light turquoise with large brighter-cyan wave shapes, the dark-blue Neuro wordmark top-left, a small dark-blue EXTRA STRENGTH badge over a green GUM badge top-right, a green Spearmint tag, the large dark-blue title Energy & Focus, 90 Pieces Dietary Supplement, and a dark-blue base band reading 100MG OF NATURAL CAFFEINE; the label reads exactly as in Image 2, upright and never mirrored, without deformation and without scale drift.
  [Plot Summary] From the first frame to the last, an open Neuro Extra Strength Energy & Focus gum pouch (Spearmint) stands upright on its flat gusseted base on the bare black desk to the right of the blue notebook, its top strip torn off at the tear notches and its zipper mouth open, a few round white tablets with green flecks just visible inside the dark mouth, its label turned about twenty degrees toward the lens; it is part of this scene although Video 1 has none. It is about as tall as his hand is long and a little shorter than the notebook is wide, at the notebook's depth about half a metre from the lens, its left side two finger-widths from the notebook's right edge, lit by the room's soft light with a soft contact shadow like the notebook's. Nobody touches it, nothing is poured or taken, the pen is the only object he picks up, and the pouch stays exactly there in every frame, also after the white flash.
  Shot 1 [0-3.1s]: Static selfie framing, medium close-up, slightly low. The young man sits leaning slightly forward over the notebook, head bowed, eyes half-closed, his frame-left hand writing short strokes with a silver pen, his frame-right hand resting by his chest, lips moving as if explaining. He releases the pen onto the notebook and both hands rise to chest height, palms open, fingers spread, alternating explanatory gestures, head tilting side to side, earnest. Then his frame-right index finger goes to his lips and chin, eyes rolled up thinking, mouth closed, as the image brightens to white.
  Shot 2 [3.1-5.0s]: Out of the white, same framing: smiling, his frame-right hand points a finger toward the lens and sweeps down in front of him; his frame-left hand picks the pen up from the notebook and writes, head slightly down, eyes up to the lens, a smug half-smile; while still writing, his frame-right index finger taps his temple, eyebrows up. The open pouch is still there, one pouch, the same spot.
  [Audio Style] No dialogue. No background music. No sound effects.
  [Camera & Core Constraints] Camera static, phone-shot look, everything in focus. Real-time speed, nothing added, skipped, repeated or reordered, no new gesture, no camera move, no re-staging, no new people. Always exactly one pouch, open, upright, never poured, not duplicated, not vanished, not deformed. No subtitles or on-screen text; the only lettering is the pouch label exactly as in Image 2; the t-shirt carries no lettering.
  [Negative Prompts] no subtitles, no watermark, no text or print on the t-shirt, no mirrored image, no reversed lettering, no mirrored label, no face distortion, no identity drift, no costume changes, no extra fingers, no second pouch, no sealed pouch, no loose gum pieces on the desk, no spilled gum, no hand taking a piece, no chewing, no hand touching the pouch, no moving pouch, no oversized pouch, no pouch closer to the camera than the notebook, no pouch taller than his hand is long, no scale drift, no slow motion, no speed ramps, no other brands, no logo stickers
  ```
- **prompt change:**
  ```text
  - Video 1 is the motion, camera, framing, cut and timing reference: keep every movement, gesture, head turn, gaze, expression and mouth movement of the person in Video 1 in the same order, at the same moments and at the same real-time speed, and keep the camera, framing, cuts, light, room and backgrou
  - Do not inherit the appearance, clothing, text, captions, stickers, usernames, watermarks or branded items of Video 1.
  - The young man corresponds to Image 1, adopting facial features, hairstyle, skin tone, build and clothing (short brown hair, trimmed beard);
  - Image 1 is only this person's identity, not its pose, its background or any object in it.
  - The young man replaces the person of Video 1 and performs exactly that person's movements.
  + Video 1 is already in true orientation and is the motion, camera, framing, cut and timing reference: keep every movement, gesture, head turn, gaze, expression and mouth movement of the person in Video 1 in the same order, at the same moments and at the same real-time speed, and keep the camera, fram
  + nothing is mirrored or flipped and all lettering reads correctly from left to right.
  + Do not inherit the appearance, clothing, text, captions, usernames, watermarks or branded items of Video 1.
  + The young man corresponds to Image 1, adopting facial features, hairstyle, skin tone, build and clothing (short brown hair, trimmed beard, a plain black crew-neck t-shirt with no print, no lettering and no logo);
  + Image 1 is only his identity and clothing, not its pose, background or objects.
  + He replaces the person of Video 1 and performs exactly that person's movements.
  - both images jointly define one single package, adopting its exact structure, material and colour: a sealed stand-up pouch about 13 cm wide and 18 cm tall, light turquoise with large brighter-cyan wave shapes and a zip seal near the top, a dark-blue Neuro wordmark, a small dark-blue EXTRA STRENGTH ba
  - Keep its exact shape, proportions and printed artwork without deformation and without scale drift;
  - it stays closed.
  … 37 more changed sentences
  ```
- **verified params:** model=wan3_0_prime · duration=5 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=image_references×3, video_references · request=video-20-fix-a2-request.json
- **rule:** A placed product takes the state its scene implies when the scene has a natural use for it (a snack or gum pack at a class or desk scene is open, a drink at a table is cracked or has been sipped from), decided in the plan from the story and the room and written as one positive sentence with its exclusions; the sealed, untouched state is the default only where nothing in the scene suggests use, and the plan says which case applies and why.
- **status:** fixed
- **promoted to:** —
- **verified:** a2 accepted (job 0edb3b0c-748c-475c-a68f-638579a7813a, ledger lane 20-fix attempt 3): un-mirrored room (guitars frame-left right-handed, notebook lower-left, pen in the frame-left hand), plain black tee with no readable text (OCR none), pouch label unmirrored and legible at full resolution (Neuro, EXTRA STRENGTH, GUM, Spearmint, Energy & Focus, 90 Pieces, 100MG OF NATURAL CAFFEINE), pouch OPEN (torn top, tablets in the mouth only) count 1 in every dense checkpoint and in 143 of 150 mask frames (rest are the white flash), same spot across the flash (x0 388-389 before, 386 after, drift <=3 px), nothing passes through it; size 1.15-1.23x by two methods (A and B agree, 15-25 pct note band, static, label readable); sync-check in_sync (offset -0.1 s, corr 0.83); original audio whole (decoded md5 identical); white flash rebuilt on own moving frames, no frozen frame; text layer posX 0, no emoji; evidence 60-outputs/video-20/fix-20261012/ (a2/qc/dense, assembly/qc/dense, a2/sync/sync-sheet.jpg, size/*.json, a2/f/label4.0.png, anchor-track.txt) (2026-10-12)

## CE-032 · 2026-10-12 · Text on the carton label is jumbled
- **source:** user
- **video:** 12
- **run:** 20261010-020703-09
- **delivered:** CapCut project 10_Oct_2026_v12 · clean C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261010-020703-09/60-outputs/video-12/clean.mp4 · credits 48 · run QC: RESIDUAL FAILURE: a1 carton ~1.5x expected vs laptop and standing upright instead of flat (CE-005/012); a2 sachet ~1.9x, upright, shirt changed, rejected; counts 1/1, no contact, action/identity/sync ok
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Neuro Extra Strength Spearmint 9-piece carton (V04 recreate, meeting table, placement)
- **assets:** Neuro Spearmint 9-piece carton front/angled references padded to p25 (celsius/neurogum assets); source V04
- **user said:** "the text on the box is very jumbled, maybe do at higher quality."
- **what was wrong:** The label on the placed carton renders as garbled letters. The carton is small in the frame (about 69 px wide in the 720p generation, label words only a few pixels high) and its padded reference (p25) gives the model even fewer label pixels to copy, so the model re-draws the label text as letter-like shapes; the mirrored reflection on the glossy table repeats it. The delivered file is the 1.5x Topaz upscale of the 540x960 preview, which cannot restore text that was never drawn. The QC verdict checked count, size, posture and 'OCR: no stray text' but had no check that the label itself reads (brand wordmark, flavour tag); garbled label text passed because OCR only looked for extra text.
- **brief:**
  ```text
  # Video 12 brief: V04 serious meeting (Neuro XE Spearmint 9-piece carton lying flat on the glossy table)
  Concept: recreate V04 with Neuro (placement); char-A10.jpg. Why it works: the reference's own mechanism, product native to the scene, noticed not featured.
  Model/operation: wan3_0_prime, video_references + image_references, 8 s, 9:16 720p, generate_audio false. Cost: preflight in request file (3 credits per second expected).
  Fidelity: source silent video as video reference, same duration, action script written out, fidelity lock; risk: Wan rebuilds the action (approx. recreate); sync-check after the merge.
  Text: "Me in a serious meeting wondering how they got this massive table through the door" y_rel 0.095 (posY 0.81, posX 0) 0-6.6
  Guardrails: none; Neuro: no claims, one product, spearmint (peppermint/spearmint rule), real packaging render only. Verdict pick-clean.
  ```
- **prompt:**
  ```text
  [Core Task] Generate a real phone-shot clip of a deadpan moment in a meeting room. The man corresponds to Image 1, adopting only his facial features and hairstyle; he replaces only the young man in the light-blue polo at the left of the table in Video 1 and keeps the clothing, body and pose of Video 1; do not use the background, props, clothing or lighting of Image 1. Use Video 1 for every movement, expression, gaze, the framing and camera, the room and the timing; do not reproduce any text, captions, usernames or watermarks from Video 1. The carton corresponds to Image 2 and Image 3, which jointly define the same carton and generate only one instance, adopting only its structure, material, colours and printed label (a small flat light-blue paperboard carton with a Neuro wordmark top-left, a mint-green GUM badge with an EXTRA STRENGTH tab top-right, a Spearmint tag, the title Energy & Focus and a dark-blue band reading 100MG OF NATURAL CAFFEINE).
  [Plot Summary] Shot: fixed phone shot, wide medium, the camera static and the framing unchanged from Video 1: a very large glossy red-brown conference table fills the bottom half of the frame, a glass wall and white ceiling panels behind, an older man in a dark shirt at the right edge of the frame with only his torso and clasped hands visible, unchanged and unreplaced. The man sits at the left of the table in the light-blue polo with an open silver laptop and a yellow highlighter in front of him. He looks up and to the left across the room with a deadpan wondering expression, glances down and to the left, turns back and listens toward the older man with a neutral face, then glances left again and gives one small nod; his hands rest near the keyboard and the older man's hands stay clasped. A closed Neuro Energy & Focus Extra Strength Spearmint 9-piece carton lies flat on the bare glossy table to the left of the laptop, its large printed face up, a hand-width clear of the laptop and of his hands, about 1.2 metres from the lens, with a contact shadow and a faint reflection in the glossy top like the highlighter's; it is part of this scene although Video 1 has none, it stays there and nobody touches it. In Image 2 and Image 3 the carton is deliberately small in the frame and keeps that small scale; do not use their framing, lighting, exposure, background, shadow or camera angle. The carton is a small flat pack, 7.5 cm by 7.5 cm and 1.6 cm thick: about as wide as three fingers, much smaller than the open laptop, shorter than the yellow highlighter is long; it fills only about one fiftieth of the frame width and keeps exactly this size. Cool overhead light with a warm glow from the wooden wall; the carton takes the same light. Real-time speed. No dialogue. No background music.
  [Camera & Core Constraints] Keep every movement, gesture, expression, gaze and mouth movement of the man in Video 1 on the same frames, the props and how they are handled, the camera framing and handheld feel, the light, the room and the timing of Video 1 unchanged; no added, skipped, repeated or reordered action, no new gesture, no extra camera move, no re-staging, no new people, no change of pace. There is exactly one carton, closed, flat, never opened; exactly two people, small and constant in size, not duplicated, not vanished, not deformed, no scale drift; the carton stays where it is and fingers or objects never pass through it. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen; the only lettering is the printed label on the Neuro carton, exactly as in Image 2; do not reproduce any text, captions, usernames or watermarks from Video 1.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no scale drift, no cut-out edges, no slow motion, no speed ramps, no self-inserted cut points, no added or skipped action, no second carton, no oversized carton, no carton longer than the yellow highlighter is long, no carton opened, no carton standing on its edge or leaning, no studio lighting on the carton, no glow, no clipping
  ```
- **params:** model=wan3_0_prime · duration=8 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=video_references, image_references×3 · request=final-prompt.json
- **errors:** none
- **evidence:** deliverables/video-12-preview_1.5x.mp4 at about 3 s (carton at the table, label and its reflection); 60-outputs/video-12/prev.png
- **qc:**
  ```text
  # Video 12 QC verdict (a1 delivered, flagged)
  RESIDUAL FAILURE size/posture. a1 (job 5c23930d, carton): carton ~69 px wide vs laptop lid 180 px (30 cm) = ~1.5x expected (T scale), constant at 0.5/4.0/7.5 s; carton stands upright on its base in front of the laptop instead of lying flat (CE-012/013 plan wanted flat). a2 (job 9c834a69, sachet fallback): sachet ~58 px wide (~1.9x), also upright, and the polo turned into a lilac shirt (costume change) -> worse, rejected; a1 kept.
  Counts at start/glance/nod/end: carton 1, laptop 1, yellow pad 1, people 2. CE-001 ok. CE-002 closed, never touched. CE-003 nothing passes the carton (hands rest, dense sheets glance/nod). CE-004 paste: contact reflection and room light ok, label slightly packshot-frontal (1 sign). CE-005 FAIL ~1.5x. CE-006 n/a. CE-010 text posX 0, posY 0.81 top band, clear of face. CE-007/008/011 inflation reproduced. CE-012/013 FAIL upright. OCR: no stray text. Guardrails none.
  Action/identity: head glances and nod land on source beats; identity, polo, older man kept.
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261010-020703-09\40-briefs\video-12-plan.md
- **class:** anomaly-catalog.md §2.15 (blend, render not paste: label legibility) and §4 (QC stack: add a label-legibility step); models/wan-3-0.md §5 (small product label garbles); generation-system.md §4b (reference padding vs label pixels)
- **cause:** model-limit
- **fix:** PARTIAL, status stays open (video 12 fix pass 2026-10-12, 3 generations, 144 credits; FLAGGED delivery of a2, job 4903885c-db85-4f4b-9365-ccfb8f1c152b, CapCut project 12_Oct_2026_v12, files client-fixes-20261012/run09-video-12-fixed-FLAGGED-*). What changed: resolution 1080p (a true 1080x1920 generation, no upscale), references padded less (p60 front and angled, native label pixels), the exact label wording in the prompt, an extra label-forward closeup artwork reference (Image 4), the identity photo cropped to the head (CE-035), the carton standing on its base (a flat label is foreshortened to 0.39 in this shot), the anchor asked nearer the lens. What improved: the Neuro wordmark and the Energy & Focus title read exactly. What remains: the Spearmint tag, the badge (EXTRA STRENGTH / GUM and fine print), the 9 Pieces | Dietary Supplement line and the navy band line are still letter-like shapes (letters 5-6 px high); a1 and a3 also rendered the badge as CUM; the carton renders 1.62x its real size (A 1.62x vs the laptop lid, B 1.57x by distance, agree), the model keeping it at the laptop depth whatever the placement words. Needs the user: a tracked composite of the client's real label render over the carton in post, or a shot where the carton is held or honestly large in frame.
- **verified prompt:** pending (inserted only after a new generation passes QC)
- **rule:** A product label that must read (brand wordmark, flavour, variant tag) is accepted only when it is legible at the delivered resolution: the plan estimates the label's pixel height from the size reckoning and, when the wordmark would be only a few pixels, chooses an anchor that gives it more pixels (held, nearer, larger in frame within the size rule) or records the limit; QC reads the label on a full-resolution frame at rest, word by word against the asset (wordmark and flavour tag exact, fine print may blur but never become wrong letters), and a garbled label is a regenerate reason, never 'OCR noise' and never fixed by upscaling.
- **status:** open
- **promoted to:** —

## CE-033 · 2026-10-12 · The bag renders carton-sized: the client's bag should be bigger than the boxes
- **source:** user
- **video:** 14
- **run:** 20261008-235833-08
- **delivered:** CapCut project 09_Oct_2026_v14-2 · clean C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261008-235833-08/60-outputs/video-14/clean.mp4 · credits 78 · run QC: r2 accepted (flat sachet). POSTURE/SUPPORT: lies flat on its wide face, label up, whole underside on bare marble with contact shadow, no tilt/edge/float at 30 fps (write, glance, flip, last). STORY: set down on the near table edge to the right of the writing hand, out of the way; a real person leaves a gum pack like that. Size 1.05x (5 cm width: 92-105 px vs 93 expected at 0.5 m). Count 1/1/1, sealed. Never touches the arm: 2-D marble gap 18-37 px (~0.2 hand-width; flagged, frame leaves only ~150 px under the forearm). r1 carton rejected: flat and ~1.1x but its corner sat against the forearm (gap 3-4 px) 0.5-8 s. CE-001/002/003/004/006/007/008/010/012 pass; CE-012 set fixed with the r2 prompt.
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Neuro Energy & Focus Peppermint single sachet (V05 recreate, redo of CE-012, exam table)
- **assets:** Neuro Energy & Focus Peppermint sachet A544 (single sachet, 5 x 7 cm per the QC verdict); registry P3 pouch 17.9 x 10.2 x 4.6 cm
- **user said:** "Idea is great, the bag is too small here. This would be the size of the box packaging. The bag is bigger than the boxes."
- **what was wrong:** The redo (video-14 r2) replaced the 9-piece carton with the single flat Energy & Focus Peppermint sachet after the carton touched the forearm. The registry lists sachets as 'present, registered, not planned' (G17/G18/G27: hero is the Extra Strength carton, secondary the 90-piece pouch at about 17.9 x 10.2 x 4.6 cm, bigger than the 7.5 cm carton). The sachet passed QC at 1.05x of its own 5 x 7 cm size, so QC found nothing wrong, but the client sees 'the bag' at about the size of the box packaging and says the bag is bigger than the boxes in reality. Two misses: a fallback form outside the planned list was chosen, and the size ladder between the client's own forms (bag larger than carton) was never checked against what the viewer expects; size was only checked against a neighbour and a distance. I read 'the bag' as the flat pack on the table; confirm with the client whether they mean the 90-piece pouch.
- **brief:**
  ```text
  Video 14 of 18 - Recreate of V05: Neuro XE Peppermint carton, placement on the marble table
  Concept: the reference recreated as itself (same scenario, action, camera and timing), faces swapped to the supplied character(s), the product integrated (placement on the marble table).
  Why it works: Communicates: "what teachers think would happen if they let us listen to music in an exam" - the VO reads answers like a track; deadpan. Why Neuro: students under sustained mental load (A456 sec 4), calm and wry (G24), the product 'just happens to be there' (G23). Kept [E]: the take, the VO, writing, the page flip. Goal/job [I]: awareness; the carton on the marble, noticed; share line "this is why we can't have music". Adapted: man -> K3; the caption box and shirt print removed from the plate; the package is Extra Strength Peppermint, closed (hero per G18, form per G27).
  Reference pattern: V05 (see 20-analysis/cards/V05.md and families.md)
  Characters/assets: see the plan sec 2.3; Higgsfield media ids in 30-assets/uploads.json and the request file.
  Substitutions: Placement; the closed hardcover notebook (a solid, not a sheet hands move: CE-006) is the smallest native element that lets a 1.6 cm-thick carton stand readable; hands busy: no use beat (G19/G27 satisfied: no piece is taken).
  Counts & use: | entity | count | state |
  |---|---|---|
  | carton | 1 | upright on its long edge, propped against a closed hardcover notebook on the bare marble, lower right, ~0.6 m, closed, label 30 deg; never moved |
  | sheets | 1-2 | flipped at 9.2-10.4 over the left edge, away from the carton |
  Size: Carton 7.5 cm at ~0.6 m, 26 mm eq -> ~9.0% (~116 px) (T scale --product-cm 7.5 --distance 0.6 --lens 26); neighbour: the exam sheet (29.7 cm) -> ~0.25 of its length; his palm is ~8.5 cm wide, the carton 7.2 cm wide -> slightly narrower than his palm. Oversize check: a carton taller than ~0.4 of the sheet is a regenerate reason.
  Guardrails: G16 (the client's real renders are the only product references; no AI-invented packaging: QC compares the label geometry and any morphed text is a regenerate reason), G17/G18 (Extra Strength, Peppermint or Spearmint, 9-piece carton, closed; the 6-pack box never appears), G19/G27 (closed package, nobody takes a piece, no blister shown), G23/G24 (the product just happens to be there; calm, wry register), G25 [U] (no sleeping/drained scene), G11/G21 (no numbers or claims in any text layer; the carton's own 100MG band is the only number), G12 (no competitor shown or replaced), G13/G14 (an adult supplied character, no ambassador likeness), G22 (phone-shot, everything in focus).
  Caught errors applied: CE-006 (a product is never placed on or overlapping paper: bare surface or a solid prop; sheets stay flat; QC densifies the contact region for the whole shot), CE-007 (small closed carton by default in casual scenes; the pouch only where a large pack fits; a placed product never takes over the source's pick-up beat: the object picked up is named and the product stays), CE-008 (adult framing in captions and casting), CE-010 (text centred), CE-001 (the package count stays 1; nothing taken), CE-002
  Text: CapCut layer as in the scene.
  Inserts: none.
  Sound: Original VO audio restored.
  Fidelity approach: the silent own-content source as video_references (the most preserving input Wan 3.0 Prime offers: recreate-from-video-reference), exact duration rounded up, fidelity lock + the action script written out in the prompt; risks to fidelity or sync: lip-sync and exact timing are not guaranteed by this model; sync-check after the merge.
  Model & operation: video-14-request.json: wan3_0_prime reference-to-video, 13 s, 9:16 720p, generate_audio false, 4 media - est. 39 credits (3 credits/s, preflight read: no adjustments)
  Adaptation logic: One generation of 13 s (own 12.07 s). Credits 39. No inserts.
  
  ## Redo (CE-012, 2026-10-09)
  r1: closed XE Peppermint carton lying flat label up on the bare near-camera marble, lower right (50-requests/video-14-r1-request.json, p40 refs 36960471/2bc3de47) - flat and ~1.1x but against the forearm; r2: flat-lying single Energy & Focus Peppermint sachet on the same strip, band of marble to the forearm (50-requests/video-14-r2-request.json) - delivered. Action script and fidelity lock unchanged. CapCut project 09_Oct_2026_v14-2.
  ```
- **prompt:**
  ```text
  [Core Task] Generate single shot. The man corresponds to Image 1, adopting only his facial features and hairstyle and light stubble; man replaces only the person in Video 1 and keeps the plain white t-shirt without lettering and the white over-ear headphones; do not use the background, props or clothing of Image 1.  Use Video 1 for his movements, expressions, gaze, the camera framing, the room, the exam sheets and the timing; do not reproduce any text, captions, white caption boxes, usernames or watermarks from Video 1. The sachet corresponds to Image 2 and generates only one instance, adopting only its structure, material, colours and printed label (a small flat closed sky-blue foil flow-wrap sachet about 5 cm wide, 7 cm tall and 1 cm thick with crimped seals at the top and bottom, the dark-blue Neuro wordmark top-left, a mint GUM badge top-right, a Peppermint pill tag, 'Energy & Focus' in large blue type and '1 Piece | Dietary Supplement' below it); in Image 2 the sachet is deliberately small in the frame and keeps that small scale; do not use the framing, lighting, exposure, background, shadow or camera angle of Image 2.
  [Plot Summary] Locked phone camera at eye level, medium shot, a white marble table filling the lower third, a bright room corner with a white door and warm lamp light from the upper left. He sits turned about forty degrees toward the left of the frame with his head tilted left, listening to his headphones, a blue pen in his right hand resting on an exam sheet and his left hand flat on the table; he turns his head down to the sheet and squares his torso; he writes with small right-hand strokes, glancing up and to the left once, and keeps writing; then both hands lift the right edge of the sheet and flip it over to the left, his left hand smoothing it down, and it lands on the same spot; he writes again with a glance to the right of the frame. A single closed sealed Neuro Energy & Focus Peppermint sachet lies flat on its wide face with its printed label facing up, resting entirely on the bare white marble in the bottom right of the frame, on the near side of the table, nearer the lens than his hands and forearm, where someone sets a sachet of gum down out of the way of their writing. It is fully inside the frame, with a band of bare marble at least as wide as the sachet itself between it and his forearm, hands and the exam sheets; nothing touches it and nobody picks it up. It is about fifty centimetres from the lens, a tiny object about as long as his index finger, narrower than his open palm and much shorter than his palm is long, filling only about one tenth of the frame width, seen from above at a slight angle as a thin flat rectangle, lit by the same warm lamp light with a soft contact shadow on the marble falling to the right like the sheets' shadows; it stays flat on that spot for the whole clip and never slides, tilts, stands up or leans, the exam sheets lie flat and keep their shape except when he flips the top one, and the flipped sheet stays on the left and never reaches the sachet. Phone-shot look with everything in focus and no shallow depth of field. Real-time speed. No dialogue. No background music.
  [Camera & Core Constraints] Keep every movement, gesture, expression, gaze and mouth movement of the person in Video 1 on the same frames, the props and how they are handled, the camera framing and handheld feel, the light, the room and the timing of Video 1 unchanged; no added, skipped, repeated or reordered action, no new gesture, no extra camera move, no re-staging, no new people, no change of pace. There is exactly one sachet, tiny, small and constant in size, never larger than his hand, lying flat, sealed and never opened, not duplicated, not vanished, not deformed, no scale drift; nothing passes through it. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen; the only lettering is the printed label on the Neuro sachet, exactly as in Image 2; do not reproduce any text, captions, usernames or watermarks from Video 1.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no scale drift, no cut-out edges, no slow motion, no speed ramps, no self-inserted cut points, no added or skipped action, no oversized or giant package, no sachet longer than his hand is wide, no sachet larger than his head, no standing, leaning, propped or tilted sachet, no sachet on its edge, no sachet on a sheet, no sachet touching his arm, no notebook, no six-pack box, no blister card, no opened sachet, no torn foil, no loose gum pieces, no gum in anyone's mouth, no chewing, no second package, no studio lighting on the package, no glow, no shallow depth of field, no white caption box, no text on the shirt, no phone
  ```
- **params:** model=wan3_0_prime · duration=13 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=video_references, image_references×2 · request=video-14-r2-request.json
- **errors:** none
- **evidence:** deliverables/previews/video-14-redo_1.5x.mp4 at about 6 s (flat pack at the near table edge, lower right); 60-outputs/video-14/qc-verdict.md
- **qc:**
  ```text
  # Video 14 REDO QC verdict (CE-012). Delivered: r2 (flat-lying single Energy & Focus Peppermint sachet). Two generations, 78 credits.
  Place decision (source frames at 0.5/5/10 s, r1/src*.png): the source has no notebook and the table's far side is hidden behind his torso; the only bare marble is the near-camera strip at the lower right (x 0.55-0.85, y 0.88-1.0). Chosen: that strip, in front of (nearer the lens than) his hands and forearm.
  
  r1 (carton, job 83c5f154, 39 cr): REJECTED. Posture/support pass (lies flat, label up, whole underside on the marble, contact shadow, never moved, stable at 30 fps). Size ~1.1x (area 15.7-19.5k px2 vs ~14.4k expected at 0.5 m, 26 mm eq; T-scale-equivalent on the 7.2 cm edge: 117-145 px vs 134 expected). FAIL: its rear corner sits against his right forearm in the picture (2-D gap 3-4 px from 0.5 to 8 s, measured with a colour mask, confirmed on a 4x crop), i.e. "against an arm".
  
  r2 (sachet, job 0652f637, 39 cr): ACCEPTED.
  POSTURE/SUPPORT (30 fps, write 2.4-4.8, glance 4.2-5.0, flip 9.0-10.6, last 11.0-12.07, all sheets viewed): lies flat on its wide face, label up, crimped seals visible, whole underside on the bare marble, soft contact shadow, no tilt, no edge balancing, no floating or sinking; it touches only the marble. Never slides, never lifted; only drifts with the handheld camera (bbox 146x107 px at 6 s, 150x93 at 10-11 s).
  STORY: he set the sachet down on the near edge of the table, to the right of where he writes, out of the way of the pen hand and the sheets; a real person leaves a pack of gum exactly like that and does not touch it.
  Place: bare marble, never touches the arm or hand: 2-D gap to the forearm 18-24 px at 0.5-8 s and 31-37 px at 9-12 s (a visible marble band; the sachet is also nearer the lens than the arm, so the real gap is larger). Honest flag: the 2-D gap is about 0.15-0.25 of a hand-width, not a full hand-width, because the frame leaves only about 150 px of marble below the forearm.
  Size: sachet 5 x 7 cm; far edge 92 px, near edge 105 px at 6 s (4x crop) vs 93 px expected for 5 cm at 0.5 m (26 mm eq) = 1.05x; area 9.3k px2 at 6 s vs ~9k expected. Narrower than his palm (about 165 px), well under his head. Constant (drift only with the camera). CE-005/CE-009: pass (<25%).
  Counts: sachet 1 at 0/6/12 s and every dense frame; nothing taken; sealed, never opened (CE-001, CE-002).
  CE-003/CE-006: sheets flat, flipped sheet lands on the left, never near the sachet; hands never touch it; sachet never on paper. CE-004/paste test: warm room light, same grain and focus as the marble, contact shadow present (it falls slightly down-left like the hand's shadow, minor), label geometry matches the A544 render, perspective consistent; 0 signs beyond that note. CE-007: small closed pack, source beats unchanged. CE-008: adult man, caption says professors. CE-010: text posX 0, posY 0.66 (y_rel 0.17). CE-012: pass (posture, support, place, story). CE-013 not this video.
  Guardrails: no blister, no opened pack, no 6-pack box; no number/claim in the text layer; OCR: only label words ("Focis" at 2.4 s = label OCR noise). Note: the sachet is the plain Energy & Focus format, not the Extra Strength carton (G17/G18 hero); the carton attempt was clean in posture and size but put against the forearm.
  Identity: same K3-like man as v1 (white tee, white headphones, no print, no caption box). Source beats kept: listen/head tilt left, writing from ~2.8 s, glance up-left ~4.5, page flip ~9.6-10.4 (source 9.2-10.4), writing again, glance right ~10.8.
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261008-235833-08\40-briefs\video-14-plan.md
- **class:** generation-system.md §4b.0 and §4b.1 (form choice and size ladder between the run's products); anomaly-catalog.md §2.7 (size ladder); brand-guardrails.md (fallback forms stay inside the planned list)
- **cause:** plan
- **fix:** Partial fix 2026-10-12: switched the product from the 5 x 7 cm sachet to the 90-piece Peppermint pouch, flat on the bare marble strip, size 1.06-1.12x real (A and B agree), clear of arm and hand; best take of 3, job aca0b58c-352d-4415-ac75-fc64211e32fd, delivered flagged in client-fixes-20261012 (run08-video-14-fixed-FLAGGED-*). Still failing: Neuro wordmark reads Nero, the label is turned a quarter turn, and the pouch looks like a flat envelope (CE-042). Status stays open.
- **verified prompt:** pending (inserted only after a new generation passes QC)
- **rule:** When a client's products come in several forms, the plan carries the size ladder between them (a pouch or bag is larger than a carton, a carton than a sachet) and QC checks that the rendered form keeps that ladder, in addition to the neighbour ratio; a fallback form is taken only from the planned list, and when the planned form fails a posture check the retry changes anchor or posture for that same form, never substitutes a smaller form the client reads as a different product.
- **status:** open
- **promoted to:** —

## CE-034 · 2026-10-12 · Carton looks very large next to the notebook
- **source:** user
- **video:** 22
- **run:** 20261007-232745-07
- **delivered:** CapCut project 08_Oct_2026_v22 · clean C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07/60-outputs/video-22/clean.mp4 · credits 21 · run QC: accepted
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Neuro Energy & Focus Cinnamon 9-piece carton (V16 recreate, table corner, placement)
- **assets:** Neuro Energy & Focus Cinnamon 9-piece carton (Images 2-3, orange-red GUM badge); A09 character; V16 inserts
- **user said:** "please check sizing of the box, I know it's close to the camera here, but it's next to the notebook and seems really big in relation to the notebook."
- **what was wrong:** The carton stands upright at the front-right table corner and, on the frame at about 0.8 s, is about as wide as the notebook page beside it, while a 9-piece carton is 7.5 cm wide against a page of about 21 cm: several times the true ratio (by eye on the frame, not measured). The delivered QC accepted it with the explanation 'large in frame because it sits at the table edge next to the lens', an assertion that was not measured against the same-table neighbour: nothing computed the depth ratio between the carton and the notebook, so the closeness to the lens was used as a reason instead of a number. The client had already allowed for the camera distance and still finds it too big.
- **brief:**
  ```text
  Video 22 of 22 — NEUROGUM — Recreate V16
  Concept: V16 recreated beat for beat with character A09 and the Neuro Energy & Focus gum carton (Cinnamon, 9 pieces).
  Reference pattern: V16 card (timing, beats, inserts at 1.80-4.40, 6.70-9.30).
  Characters/assets: A09 (Image 1); A709.jpg, A708.jpg.
  House approach: none (no examples).
  Substitutions: creator → A09 | Placement: stands upright at the front-right corner of the table, outside the sweep of the hands, label toward the lens, in the same spot in every shot.
  Main action & states: source beats unchanged; product untouched and persistent.
  Style & camera: as V16, static phone camera, the source's light.
  Text: CapCut layers in the house style, reference wording/positions (see plan).
  Inserts: V16 1.80-4.40, V16 6.70-9.30.
  Sound: original audio restored; inserts with their own sound.
  Model & operation: wan3_0_prime reference-to-video (≈ recreate from Video 1), 7 s → trim 6.300 s, 9:16 720p, audio off, thinking on · est. 21 credits
  Fidelity: Video 1 = silent own content (motion/camera/timing), action script written out in order, keep-list + exclusions, same duration; sync-check after the merge. Risk: low.
  Adaptation logic: product placed at the analysed anchor; source branding dropped.
  ```
- **prompt:**
  ```text
  [Core Task] Recreate Video 1 as a real phone-shot vertical clip with only these changes: the person and the product. Video 1 is the motion, camera, framing, cut and timing reference: keep every movement, gesture, head turn, gaze, expression and mouth movement of the person in Video 1 in the same order, at the same moments and at the same real-time speed, and keep the camera, framing, cuts, light, room and background of Video 1. Do not inherit the appearance, clothing, text, captions, stickers, usernames, watermarks or branded items of Video 1. The man corresponds to Image 1, adopting facial features, hairstyle, skin tone, build and clothing (short hair, stubble); Image 1 is only this person's identity, not its pose, its background or any object in it. The man replaces the person of Video 1 and performs exactly that person's movements. The Neuro Energy & Focus gum carton (Cinnamon, 9 pieces) corresponds to Image 2 (front) and Image 3 (angled view); both images jointly define one single package, adopting its exact structure, material and colour: a small closed flat cardboard carton, about 7 cm wide, 8.5 cm tall and 1.5 cm thick (palm-sized), light blue with wavy lighter-blue shapes, a blue N logo and Neuro wordmark top-left, an orange-red GUM badge top-right, a Cinnamon tag, the large blue title Energy & Focus. Keep its exact shape, proportions and printed artwork without deformation and without scale drift; it stays closed. Video 1 has no such item, but the Neuro Energy & Focus gum carton (Cinnamon, 9 pieces) is part of this scene from the first frame: it stands upright at the front-right corner of the table, outside the sweep of the hands, label toward the lens, in the same spot in every shot, at its real size, lit by the scene's own light with a soft contact shadow, untouched and in the same place for the whole clip. Only one exists in the scene.
  [Plot Summary] Shot 1 [0-1.8s]: Static eye-level mirrored selfie framing from the table edge, an open notebook at the bottom centre, a door frame behind. The man sits square to the camera, leaning forward, both palms flat on the notebook with fingers tapping, head bobbing, the mouth moving rapidly as if arguing, brows raised, intense eyes to the lens; the frame-right hand lifts the top page, flips it and slaps it back down; then wide sweeping open-hand gestures across the table, leaning in, mouth still "talking", as the image brightens toward white.
  Shot 2 [1.8-4.1s]: Hard cut, same framing: he leans back then forward, hands chopping and waving, palms-up shrugs, mouth arguing; the hands come down to the notebook; the right index finger taps the temple; the arm flings out wide toward frame-right and comes back down to the notebook.
  Shot 3 [4.1-6.3s]: Hard cut, same framing: hands out palms up in a shrug, a quick temple tap, an arm swing wide to frame-right; then both hands on the notebook tapping and sliding across the page as proof; a hand wipes across the mouth and nose, then a final open gesture, still mouthing.
  [Audio Style] No dialogue. No background music. No sound effects.
  [Camera & Core Constraints] Camera: static throughout. Real-time speed, nothing added, skipped, repeated or reordered, no new gesture, no extra camera move, no re-staging, no new people or background action. No subtitles, captions or other on-screen text; do not reproduce any text, captions, usernames or watermarks from Video 1; the only lettering is the printed label on the package, exactly as in Image 2.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no extra fingers, no duplicate packages, no product deformation, no scale drift, no slow motion, no speed ramps, no other drink or snack brands, no logo stickers
  ```
- **params:** model=wan3_0_prime · duration=7 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=image_references×3, video_references · request=video-22-request.json
- **errors:** none
- **evidence:** deliverables/upscale/leftout/video-22-preview_1.5x.mp4 at about 0.8 s (carton lower right beside the notebook); 60-outputs/video-22/result.json (QC note)
- **qc:**
  ```text
  {"video": "22", "mode": "recreate", "status": "done", "clean": "C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07/60-outputs/video-22/clean.mp4", "capcut_project": "08_Oct_2026_v22", "capcut_pending": false, "preview": "C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07/60-outputs/video-22/capcut-preview.mp4", "jobs": [{"clip": "c1", "job_id": "dcc6fe4d-af52-4dde-b7da-5d76f3820df4", "credits": 21, "attempts": 1}], "credits": 21, "qc": "accepted", "continuity": "counts: carton 1/1/1/1 (0, 1.8 split, 4.1 split, end) | use: none (closed carton, untouched; frame-right hand passes beside/behind it on the arm flings 3.6-4.1 and 5.0-5.2 without contact) | permanence: same spot front-right table corner, same size and label angle on both sides of each insert", "sync": "in_sync (offset 0.0 s, corr 0.33 raw / 0.62 after fade rebuild; temple taps 3.47 and 4.87, mouth wipe 5.75-5.85, notebook taps on the source frames)", "blocker": null, "notes": "A09 identity held (short hair, stubble, grey tee); source person, hoodie crest/swoosh and overlay text gone; one closed Neuro Energy & Focus Cinnamon 9-piece carton (Images 2-3 design, orange-red GUM badge, Cinnamon tag, no blister) upright at the front-right table corner, label to lens, same spot every frame; large in frame because it sits at the table edge next to the lens; OCR hits = carton label only (SUM = GUM misread); no Celsius/other product; page flip: hand pats/sweeps the page on the source frames but the page does not turn (accepted, as video 16); model dropped the white dissolves, rebuilt on clean.mp4 from own-silent's per-frame white level (peaks 1.73 s and 4.1 s); inserts = the shared cleaned V16 cuts (caption already covered with letterbox strip), copied to 60-outputs/video-22/inserts; insert 1's last 2 frames showed the original creator ghosting through the white dissolve, replaced with flat white (0xE8E8E8, 0xF4F4F4); text re-placed word for word (4 lines, x 0.50 y 0.31, 0-11.5 s, fontSize 10, house style 0 off), above the head, clear of face and carton; capcut lint 0 errors (cue-too-long warning intended; media info left); capcut render failed on fontconfig, proxy preview rendered with ffmpeg drawtext; final timeline 11.5 s"}
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261007-232745-07\40-briefs\video-22-plan.md
- **class:** anomaly-catalog.md §2.7 (size reckoning: neighbour ratio with the depth ratio read from the frame) and §4 step 5d; CE-005 and CE-014 (a near-lens anchor inflates the apparent size)
- **cause:** qc-miss
- **fix:** Measured the delivered clip first (table plane calibrated on the source notebook, T scale A/B): the carton was 1.27x (A) / 1.29x (B) its reckoned size, 1.36-1.38x by height, confirming the client. Regenerated (3 generations; a1 flat carton right of the notebook 1.7-2.1x = CE-038, a2 upright right of the notebook stood on the page 1.23-1.31x = CE-040) with the carton on the free front-left corner of the table, on the bare grey metal front edge left of the notebook, plus a scale-reference composite as Image 4 (carton at 0.85x true size beside the V16 notebook at that spot). Result 0.91-0.93x (A) / 0.90-0.91x (B), 0.98-1.00x by height, constant at 0.0 s, 3.0 s, 6.2 s. Shared V16 inserts and original audio (one whole stream copy) rebuilt in CapCut project 12_Oct_2026_v22.
- **verified prompt:**
  ```text
  [Core Task] Recreate Video 1 as a real phone-shot vertical clip with only these changes: the person and the product. Video 1 is the motion, camera, framing, cut and timing reference: keep every movement, gesture, head turn, gaze, expression and mouth movement of the person in Video 1 in the same order, at the same moments and at the same real-time speed, and keep the camera, framing, cuts, light, room, background and the notebook's place. Do not inherit the appearance, clothing, text, captions, usernames, watermarks or branded items of Video 1. The man corresponds to Image 1, adopting facial features, hairstyle, skin tone, build and clothing (short hair, stubble); Image 1 is only his identity, not its pose, background or objects. The man replaces the person of Video 1 and performs exactly that person's movements. The Neuro Energy & Focus gum carton (Cinnamon, 9 pieces) corresponds to Image 2 and Image 3, which jointly define one single package, adopting only its structure, material, colours and printed label: a small closed flat paperboard carton, 7.5 cm wide, 8.5 cm tall and 1.6 cm thick, light blue with wavy lighter-blue shapes, a blue N logo and Neuro wordmark top-left, an orange-red GUM badge top-right, a Cinnamon tag, the title Energy & Focus. Image 4 is a size and spot reference only: it shows this carton standing on the grey front edge of the table at the front-left corner beside the notebook of Video 1, only about one third as wide as the notebook page; use that size relation and that spot, not its framing, wall, lighting or perspective. Keep its exact shape, proportions and artwork without deformation and without scale drift; it stays closed. Video 1 has no such item, but the carton is part of this scene from the first frame: it stands upright on its base on the bare grey front edge of the table at the front-left corner, to the left of the open spiral notebook, its base level with the notebook's front edge, no nearer to the lens than the notebook, not touching or overlapping the notebook, a band of bare table between them and bare table to its left, fully inside the frame; lit by the scene's own light with a soft contact shadow, untouched and in the same place for the whole clip.
  [Plot Summary] The open spiral notebook lies at the bottom centre exactly as in Video 1, its whole page in view, about 21 cm wide; the carton at the front-left corner is small beside it: about one third as wide as the notebook page, a little narrower than the man's open palm and about one fifth of the frame width; it keeps exactly this size before and after every cut.
  Shot 1 [0-1.8s]: Static selfie framing from the table edge, a door frame behind. The carton stands at the front-left corner left of the notebook. The man sits square to the camera, leaning forward, both palms flat on the notebook with fingers tapping, head bobbing, mouth moving rapidly as if arguing, brows raised, intense eyes to the lens; the frame-right hand lifts the top page, flips it and slaps it back down; then wide sweeping open-hand gestures across the table, leaning in, mouth still talking, as the image brightens toward white; his hands and arms stay farther from the lens than the carton and never touch it.
  Shot 2 [1.8-4.1s]: Hard cut, same framing, the one carton still stands at the front-left corner: he leans back then forward, hands chopping and waving, palms-up shrugs, mouth arguing; hands come down to the notebook; the right index finger taps the temple; the arm flings out wide toward frame-right and comes back down to the notebook.
  Shot 3 [4.1-6.3s]: Hard cut, same framing, the one carton still stands at the front-left corner: hands out palms up in a shrug, a quick temple tap, an arm swing wide to frame-right; then both hands on the notebook tapping and sliding across the page as proof; a hand wipes across the mouth and nose, then a final open gesture, still mouthing.
  [Audio Style] No dialogue. No background music.
  [Camera & Core Constraints] Camera: static throughout. Real-time speed, nothing added, skipped, repeated or reordered, no new gesture, no extra camera move, no re-staging, no new people. Exactly one carton, closed, upright, not duplicated, not vanished, not deformed, constant in size; nothing passes through it. No subtitles, captions or other on-screen text; the only lettering is the printed label on the package.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no extra fingers, no duplicate packages, no scale drift, no slow motion, no speed ramps, no other brands, no oversized or giant carton, no carton as wide as the notebook, no carton wider than his palm, no carton closer to the camera than the notebook, no carton on the notebook or on any paper, no carton right of the notebook, no lying or tilted carton, no carton touching his hand or arm, no studio lighting on the carton, no glow, no blister, no opened carton, no loose gum pieces
  ```
- **prompt change:**
  ```text
  - Video 1 is the motion, camera, framing, cut and timing reference: keep every movement, gesture, head turn, gaze, expression and mouth movement of the person in Video 1 in the same order, at the same moments and at the same real-time speed, and keep the camera, framing, cuts, light, room and backgrou
  - Do not inherit the appearance, clothing, text, captions, stickers, usernames, watermarks or branded items of Video 1.
  + Video 1 is the motion, camera, framing, cut and timing reference: keep every movement, gesture, head turn, gaze, expression and mouth movement of the person in Video 1 in the same order, at the same moments and at the same real-time speed, and keep the camera, framing, cuts, light, room, background 
  + Do not inherit the appearance, clothing, text, captions, usernames, watermarks or branded items of Video 1.
  - Image 1 is only this person's identity, not its pose, its background or any object in it.
  + Image 1 is only his identity, not its pose, background or objects.
  - The Neuro Energy & Focus gum carton (Cinnamon, 9 pieces) corresponds to Image 2 (front) and Image 3 (angled view);
  - both images jointly define one single package, adopting its exact structure, material and colour: a small closed flat cardboard carton, about 7 cm wide, 8.5 cm tall and 1.5 cm thick (palm-sized), light blue with wavy lighter-blue shapes, a blue N logo and Neuro wordmark top-left, an orange-red GUM b
  - Keep its exact shape, proportions and printed artwork without deformation and without scale drift;
  + The Neuro Energy & Focus gum carton (Cinnamon, 9 pieces) corresponds to Image 2 and Image 3, which jointly define one single package, adopting only its structure, material, colours and printed label: a small closed flat paperboard carton, 7.5 cm wide, 8.5 cm tall and 1.6 cm thick, light blue with wa
  + Image 4 is a size and spot reference only: it shows this carton standing on the grey front edge of the table at the front-left corner beside the notebook of Video 1, only about one third as wide as the notebook page;
  + use that size relation and that spot, not its framing, wall, lighting or perspective.
  + Keep its exact shape, proportions and artwork without deformation and without scale drift;
  - Video 1 has no such item, but the Neuro Energy & Focus gum carton (Cinnamon, 9 pieces) is part of this scene from the first frame: it stands upright at the front-right corner of the table, outside the sweep of the hands, label toward the lens, in the same spot in every shot, at its real size, lit by
  … 30 more changed sentences
  ```
- **verified params:** model=wan3_0_prime · duration=7 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=image_references×4, video_references · request=video-22-fix-a3-request.json
- **rule:** 'It is close to the camera' is a number to compute, not a reason to accept: a placed product near the lens is accepted at its apparent size only when the neighbour ratio with the depth ratio read from the frame, and a distance derived from the frame, both agree it is within the allowed multiple of the reckoned size; a same-table neighbour (notebook, laptop) that the product looks as big as or bigger than is a regenerate reason, and the retry moves the product to the neighbour's depth instead of the lens-side corner.
- **status:** fixed
- **promoted to:** —
- **verified:** a3 job 4451b1c8-6e71-4eba-a843-75b1cce7441c passed QC: carton A 0.91-0.93x and B 0.90-0.91x of its reckoned size vs the notebook (agree, within 25 percent, same at rest, in use and last frame), count 1 closed upright in the same spot (x 52-206) on both sides of each insert, label orientation constant and legible, stands on its base on the bare front edge with contact shadow, no pass-through (left hand passes in front at 1.37-1.50 s and behind at 5.9-6.3 s, carton unmoved), sync in_sync offset 0.0 s corr 0.631, original audio whole (md5 of the stream equals the source), text present no emoji; carton abuts the notebook's near-left corner (no hand-width gap) (2026-10-12)

## CE-035 · 2026-10-12 · Swapped man re-dressed in the identity photo's overshirt (costume change) although the prompt keeps the polo
- **source:** agent
- **video:** 12
- **run:** C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261010-020703-09
- **delivered:** CapCut project 10_Oct_2026_v12 · clean C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261010-020703-09/60-outputs/video-12/clean.mp4 · credits 48 · run QC: RESIDUAL FAILURE: a1 carton ~1.5x expected vs laptop and standing upright instead of flat (CE-005/012); a2 sachet ~1.9x, upright, shirt changed, rejected; counts 1/1, no contact, action/identity/sync ok
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Neuro Extra Strength Spearmint 9-piece carton (V04 recreate, meeting table, client fix CE-032)
- **assets:** 30-assets/stage/char-A10.jpg (736x920, wears a pale lilac overshirt with chest pockets); 30-assets/stage-fix-12/neuro-xe-spearmint-front-p60.png + angled-p60.png (1890x1890, carton 60 %/57.5 % of width); 10-media/V04/own/own-silent.mp4; uploads in 30-assets/uploads-fix-12.json
- **user said:** — (caught by the agent during the run)
- **what was wrong:** V12 fix a1: the light-blue striped polo of Video 1 became the lilac button-up overshirt with chest pockets worn in char-A10.jpg, for the whole clip; the prompt said 'adopting only his facial features and hairstyle' and 'keeps the clothing, body and pose of Video 1'. The earlier delivered a1 kept the polo, the earlier a2 changed it to a lilac shirt too: the identity photo's garment leaks in some rolls.
- **brief:**
  ```text
  # Video 12 brief: V04 serious meeting (Neuro XE Spearmint 9-piece carton lying flat on the glossy table)
  Concept: recreate V04 with Neuro (placement); char-A10.jpg. Why it works: the reference's own mechanism, product native to the scene, noticed not featured.
  Model/operation: wan3_0_prime, video_references + image_references, 8 s, 9:16 720p, generate_audio false. Cost: preflight in request file (3 credits per second expected).
  Fidelity: source silent video as video reference, same duration, action script written out, fidelity lock; risk: Wan rebuilds the action (approx. recreate); sync-check after the merge.
  Text: "Me in a serious meeting wondering how they got this massive table through the door" y_rel 0.095 (posY 0.81, posX 0) 0-6.6
  Guardrails: none; Neuro: no claims, one product, spearmint (peppermint/spearmint rule), real packaging render only. Verdict pick-clean.
  ```
- **prompt:**
  ```text
  [Core Task] Generate a real phone-shot clip of a deadpan moment in a meeting room. The man corresponds to Image 1, adopting only his facial features and hairstyle; he replaces only the young man in the light-blue polo at the left of the table in Video 1 and keeps the clothing, body and pose of Video 1; do not use the background, props, clothing or lighting of Image 1. Use Video 1 for every movement, expression, gaze, the framing and camera, the room and the timing; do not reproduce any text, captions, usernames or watermarks from Video 1. The carton corresponds to Image 2 and Image 3, which jointly define the same carton and generate only one instance, adopting only its structure, material, colours and printed label, letter for letter. The printed label reads exactly: at the top left the wordmark "Neuro" with its small wavy N mark; at the top right a tall rounded badge with a navy top reading "EXTRA STRENGTH" over a green body reading "GUM", "L-theanine +B Vitamins" and "Zero Sugar"; a small green pill tag reading "Spearmint"; the large title "Energy & Focus" on two lines; a small line "9 Pieces | Dietary Supplement"; and across the bottom a dark-blue band reading "100MG OF NATURAL CAFFEINE". The letters are crisp, upright and spelled exactly as in Image 2, never melted, doubled, mirrored or invented, and the carton carries no other words.
  [Plot Summary] Shot: fixed phone shot, wide medium, the camera static and the framing unchanged from Video 1: a very large glossy red-brown conference table fills the bottom half of the frame, a glass wall and white ceiling panels behind, an older man in a dark shirt at the right edge of the frame with only his torso and clasped hands visible, unchanged and unreplaced. The man sits at the left of the table in the light-blue polo with his forearms resting on the table beside an open silver laptop, a phone lying on the table at his left and a yellow notepad lying on the table at the right of the laptop. He looks up and to the left across the room with a deadpan wondering expression, glances down and to the left, turns back and listens toward the older man with a neutral face, then glances left again and gives one small nod; his hands stay where they are and the older man's hands stay clasped. A closed Neuro Energy & Focus Extra Strength Spearmint 9-piece carton is on the bare glossy table from the first frame to the last, directly in front of the left half of the open laptop, a hand-width in front of the laptop's front edge, a palm-width clear of his resting forearm and watch, his phone and the yellow notepad; it stands upright by itself on its narrow bottom edge, square to the table, its large printed face turned toward the camera about twenty degrees, resting entirely on the bare table and leaning against nothing, the way someone sets a gum carton down on a table, with a contact shadow and a faint reflection in the glossy top like the laptop's; it is part of this scene although Video 1 has none, it never slides, tilts, falls, leans or lies down, and nobody touches it. Image 2 and Image 3 are for the label only, not their framing, lighting, background, shadow or camera angle. The carton is a small flat pack, 7.5 cm by 7.5 cm and 1.6 cm thick: about as wide as three fingers, a quarter of the open laptop's width, much narrower than the yellow notepad; it fills only about one sixteenth of the frame width and keeps exactly this size. Cool overhead light with a warm glow from the wooden wall; the carton takes the same light. Real-time speed. No dialogue. No background music.
  [Camera & Core Constraints] Keep every movement, gesture, expression, gaze and mouth movement of the man in Video 1 on the same frames, the props and how they are handled, the camera framing and handheld feel, the light, the room and the timing of Video 1 unchanged; no added, skipped or reordered action, no new gesture, no extra camera move, no re-staging, no new people, no change of pace. There is exactly one carton, closed, standing on the table, never opened; exactly two people, small and constant in size, not duplicated, not vanished, not deformed, no scale drift; the carton stays where it is and nothing passes through it. Do not show any text, subtitles, numbers, interface elements or watermarks on screen; the only lettering is the printed label on the Neuro carton, exactly as in Image 2.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no scale drift, no cut-out edges, no slow motion, no speed ramps, no self-inserted cut points, no added or skipped action, no second carton, no oversized carton, no carton wider than a third of the laptop, no carton opened, no carton lying on its back, no carton leaning, tilted or propped, no carton touching his arm, hand, phone or the notepad, no garbled, misspelled, melted or invented letters on the carton, no studio lighting on the carton, no glow, no clipping
  ```
- **params:** model=wan3_0_prime · duration=8 · aspect_ratio=9:16 · resolution=1080p · generate_audio=False · enable_thinking=True · medias=video_references, image_references×3 · request=a1-request.json
- **errors:**
  ```text
  none (no adjustments; preset recommendation IN THE DARK declined with declined_preset_id)
  ```
- **evidence:** job b2a4e866-7158-439f-ab0c-bb8f4dc9a464 raw 1080x1920; frames 0.0-7.5 s: 60-outputs/video-12/fix-20261012/a1/f/raw-t4.0.png, qc/qc-storyboard-01.jpg
- **qc:**
  ```text
  # Video 12 fix pass, attempt 1 (job b2a4e866, 1080p, p60 refs, exact label text, carton standing in front of the laptop's left half): REJECTED
  - costume: the polo of V04 became a pale lilac button-up overshirt with chest pockets (the clothing of Image 1 = char-A10.jpg) over the whole clip (frames/raw-t4.0.png). FAIL (identity/costume).
  - label at rest (a1/f/label-crop-t4.0.png, full resolution 1080x1920): "Neuro" exact, "Energy & Focus" exact (OCR reads "Energy" and "&Focus" 0-7.4 s); "Spearmint" tag letter-like shapes ("Spoamenn"); the badge word GUM reads CUM, EXTRA STRENGTH and the fine print mush; 9 Pieces line mush; navy band line wrong letters. FAIL (a).
  - count 1 / 1 / 1 / 1 at 0.0-0.8, 2.4-3.2, 5.4-6.2, 7.0-7.63 (dense sheets), closed, same spot (no slide), laptop 1, notepad 1, phone 1, people 2.
  - size: carton 127 px wide (7.1 cm visible width) vs laptop lid 267 px (30.4 cm), depth ratio 0.96 (carton base row 833/1280 -> 1.48 m, laptop 1.54 m): A 1.96x, B (distance 1.48 m from the table plane, f 26) 1.91x, spread 2.4 %, agree -> oversize, regenerate (a1/scale-t4.0.json).
  - posture: stands on its narrow base on the bare table, leans on nothing (OK) but its left edge sits against the man's resting forearm/watch (gap 0 px): FAIL clearance.
  - text/OCR: only the label words; no stray text, no source caption reproduced.
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261010-020703-09\40-briefs\video-12-plan.md
- **class:** anomaly-catalog.md §2.17 (identity image chosen and scoped to fit the kept body) and models/wan-3-0.md §3.12; generation-system.md §4b.5 (asset photos bring their props)
- **cause:** reference
- **fix:** Observed, not verified: the identity reference cropped to head and neck on a neutral grey (30-assets/stage-fix-12/char-A10-face.jpg) + the kept polo named in positive words + 'no button-up overshirt, no chest pockets, no lilac or white shirt' kept the light-blue polo in 2 of 2 rolls (video 12 fix a2 job 4903885c, a3 job d07e9d1a); those takes were rejected for the label, so the prompt is not stored as verified.
- **verified prompt:** pending (inserted only after a new generation passes QC)
- **rule:** An identity reference that shows clothing re-dresses the swapped person even when the prompt scopes it to face and hair. Crop the identity image above the collar (head and neck only), name the kept garment from the source in positive words (colour, collar, sleeves, pattern), and put the identity photo's garment in the exclusion line by name; QC compares the garment on a full-resolution frame at rest, a costume change is a regenerate reason.
- **status:** open
- **promoted to:** —

## CE-036 · 2026-10-12 · 1080p and p60 references: label big type legible but the carton renders 1.9x real size and small print is still wrong letters
- **source:** agent
- **video:** 12
- **run:** C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261010-020703-09
- **delivered:** CapCut project 10_Oct_2026_v12 · clean C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261010-020703-09/60-outputs/video-12/clean.mp4 · credits 48 · run QC: RESIDUAL FAILURE: a1 carton ~1.5x expected vs laptop and standing upright instead of flat (CE-005/012); a2 sachet ~1.9x, upright, shirt changed, rejected; counts 1/1, no contact, action/identity/sync ok
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Neuro Extra Strength Spearmint 9-piece carton (V04 recreate, meeting table, client fix CE-032)
- **assets:** 30-assets/stage-fix-12/neuro-xe-spearmint-front-p60.png + angled-p60.png; char-A10.jpg; own-silent.mp4; resolution 1080p
- **user said:** — (caught by the agent during the run)
- **what was wrong:** V12 fix a1 (1080p, p60 references, exact label text, carton standing in front of the laptop's left half at about 1.5 m): the carton is 127 px wide against 66 px expected (A vs the laptop lid 1.96x, B from the table plane 1.91x, agree): larger than the delivered 720p take (1.5x). Neuro wordmark and Energy & Focus read exactly, but the Spearmint tag, the badge (GUM read as CUM) and the navy band line are wrong letters, because their letters are 5 to 6 px high at this size. Its left edge touches the man's forearm. Geometry: the camera is about 0.65 m above the table (horizon row 431/1280), so a flat-lying label would be foreshortened to sin(22.7 deg) = 0.39 of its height: lying flat cannot be legible in this shot; standing on its base is the only posture that shows the label.
- **brief:**
  ```text
  # Video 12 brief: V04 serious meeting (Neuro XE Spearmint 9-piece carton lying flat on the glossy table)
  Concept: recreate V04 with Neuro (placement); char-A10.jpg. Why it works: the reference's own mechanism, product native to the scene, noticed not featured.
  Model/operation: wan3_0_prime, video_references + image_references, 8 s, 9:16 720p, generate_audio false. Cost: preflight in request file (3 credits per second expected).
  Fidelity: source silent video as video reference, same duration, action script written out, fidelity lock; risk: Wan rebuilds the action (approx. recreate); sync-check after the merge.
  Text: "Me in a serious meeting wondering how they got this massive table through the door" y_rel 0.095 (posY 0.81, posX 0) 0-6.6
  Guardrails: none; Neuro: no claims, one product, spearmint (peppermint/spearmint rule), real packaging render only. Verdict pick-clean.
  ```
- **prompt:**
  ```text
  [Core Task] Generate a real phone-shot clip of a deadpan moment in a meeting room. The man corresponds to Image 1, adopting only his facial features and hairstyle; he replaces only the young man in the light-blue polo at the left of the table in Video 1 and keeps the clothing, body and pose of Video 1; do not use the background, props, clothing or lighting of Image 1. Use Video 1 for every movement, expression, gaze, the framing and camera, the room and the timing; do not reproduce any text, captions, usernames or watermarks from Video 1. The carton corresponds to Image 2 and Image 3, which jointly define the same carton and generate only one instance, adopting only its structure, material, colours and printed label, letter for letter. The printed label reads exactly: at the top left the wordmark "Neuro" with its small wavy N mark; at the top right a tall rounded badge with a navy top reading "EXTRA STRENGTH" over a green body reading "GUM", "L-theanine +B Vitamins" and "Zero Sugar"; a small green pill tag reading "Spearmint"; the large title "Energy & Focus" on two lines; a small line "9 Pieces | Dietary Supplement"; and across the bottom a dark-blue band reading "100MG OF NATURAL CAFFEINE". The letters are crisp, upright and spelled exactly as in Image 2, never melted, doubled, mirrored or invented, and the carton carries no other words.
  [Plot Summary] Shot: fixed phone shot, wide medium, the camera static and the framing unchanged from Video 1: a very large glossy red-brown conference table fills the bottom half of the frame, a glass wall and white ceiling panels behind, an older man in a dark shirt at the right edge of the frame with only his torso and clasped hands visible, unchanged and unreplaced. The man sits at the left of the table in the light-blue polo with his forearms resting on the table beside an open silver laptop, a phone lying on the table at his left and a yellow notepad lying on the table at the right of the laptop. He looks up and to the left across the room with a deadpan wondering expression, glances down and to the left, turns back and listens toward the older man with a neutral face, then glances left again and gives one small nod; his hands stay where they are and the older man's hands stay clasped. A closed Neuro Energy & Focus Extra Strength Spearmint 9-piece carton is on the bare glossy table from the first frame to the last, directly in front of the left half of the open laptop, a hand-width in front of the laptop's front edge, a palm-width clear of his resting forearm and watch, his phone and the yellow notepad; it stands upright by itself on its narrow bottom edge, square to the table, its large printed face turned toward the camera about twenty degrees, resting entirely on the bare table and leaning against nothing, the way someone sets a gum carton down on a table, with a contact shadow and a faint reflection in the glossy top like the laptop's; it is part of this scene although Video 1 has none, it never slides, tilts, falls, leans or lies down, and nobody touches it. Image 2 and Image 3 are for the label only, not their framing, lighting, background, shadow or camera angle. The carton is a small flat pack, 7.5 cm by 7.5 cm and 1.6 cm thick: about as wide as three fingers, a quarter of the open laptop's width, much narrower than the yellow notepad; it fills only about one sixteenth of the frame width and keeps exactly this size. Cool overhead light with a warm glow from the wooden wall; the carton takes the same light. Real-time speed. No dialogue. No background music.
  [Camera & Core Constraints] Keep every movement, gesture, expression, gaze and mouth movement of the man in Video 1 on the same frames, the props and how they are handled, the camera framing and handheld feel, the light, the room and the timing of Video 1 unchanged; no added, skipped or reordered action, no new gesture, no extra camera move, no re-staging, no new people, no change of pace. There is exactly one carton, closed, standing on the table, never opened; exactly two people, small and constant in size, not duplicated, not vanished, not deformed, no scale drift; the carton stays where it is and nothing passes through it. Do not show any text, subtitles, numbers, interface elements or watermarks on screen; the only lettering is the printed label on the Neuro carton, exactly as in Image 2.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no scale drift, no cut-out edges, no slow motion, no speed ramps, no self-inserted cut points, no added or skipped action, no second carton, no oversized carton, no carton wider than a third of the laptop, no carton opened, no carton lying on its back, no carton leaning, tilted or propped, no carton touching his arm, hand, phone or the notepad, no garbled, misspelled, melted or invented letters on the carton, no studio lighting on the carton, no glow, no clipping
  ```
- **params:** model=wan3_0_prime · duration=8 · aspect_ratio=9:16 · resolution=1080p · generate_audio=False · enable_thinking=True · medias=video_references, image_references×3 · request=a1-request.json
- **errors:**
  ```text
  none
  ```
- **evidence:** a1/scale-t4.0.json (A 1.96x, B 1.91x); a1/f/label-crop-t4.0.png; a1/qc/dense/sheet-01-start-01.jpg
- **qc:**
  ```text
  # Video 12 fix pass, attempt 1 (job b2a4e866, 1080p, p60 refs, exact label text, carton standing in front of the laptop's left half): REJECTED
  - costume: the polo of V04 became a pale lilac button-up overshirt with chest pockets (the clothing of Image 1 = char-A10.jpg) over the whole clip (frames/raw-t4.0.png). FAIL (identity/costume).
  - label at rest (a1/f/label-crop-t4.0.png, full resolution 1080x1920): "Neuro" exact, "Energy & Focus" exact (OCR reads "Energy" and "&Focus" 0-7.4 s); "Spearmint" tag letter-like shapes ("Spoamenn"); the badge word GUM reads CUM, EXTRA STRENGTH and the fine print mush; 9 Pieces line mush; navy band line wrong letters. FAIL (a).
  - count 1 / 1 / 1 / 1 at 0.0-0.8, 2.4-3.2, 5.4-6.2, 7.0-7.63 (dense sheets), closed, same spot (no slide), laptop 1, notepad 1, phone 1, people 2.
  - size: carton 127 px wide (7.1 cm visible width) vs laptop lid 267 px (30.4 cm), depth ratio 0.96 (carton base row 833/1280 -> 1.48 m, laptop 1.54 m): A 1.96x, B (distance 1.48 m from the table plane, f 26) 1.91x, spread 2.4 %, agree -> oversize, regenerate (a1/scale-t4.0.json).
  - posture: stands on its narrow base on the bare table, leans on nothing (OK) but its left edge sits against the man's resting forearm/watch (gap 0 px): FAIL clearance.
  - text/OCR: only the label words; no stray text, no source caption reproduced.
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261010-020703-09\40-briefs\video-12-plan.md
- **class:** anomaly-catalog.md §2.7 / §2.15 / §2.16; models/wan-3-0.md §5 (size model limit) and §3.11 (text approximate); generation-system.md §4b.1b
- **cause:** model-limit
- **fix:** Tried (video 12 fix pass, 3 generations, 144 credits, none passed): a1 1080p p60 refs; a2 head-crop identity (fixes CE-035) + label-forward closeup artwork reference + near anchor asked in metres; a3 near anchor asked by frame position + label demand narrowed to Neuro / Spearmint / Energy & Focus. Result in all three: wordmark and Energy & Focus exact, Spearmint tag, badge (GUM read as CUM in a1 and a3), 9 Pieces line and band line wrong letters; the carton stays at the laptop depth at 1.62-1.96x (A and B agree) whatever the placement words. Not fixed; options left for the user: a tracked composite of the client's real label render in post, or a shot where the carton is honestly large in frame (held in hand).
- **verified prompt:** pending (inserted only after a new generation passes QC)
- **rule:** Label legibility is a pixel budget: a carton at its honest size 1.5 m away has about 65 px (1080p) of width, so only the wordmark and the largest title can read; tag, badge and band lines need about 3x that. Resolution and tighter references raise sharpness but not the size inflation (1.5x at 720p p25, 1.96x at 1080p p60). A label that must read needs an anchor honestly nearer the lens (derive the distance from the table plane, both size estimates at that depth) and a posture facing the camera (a flat label at a 20 degree camera elevation shows a third of its height); QC reads the label word by word on a full-resolution frame, and a wrong letter (GUM as CUM) is a regenerate reason.
- **status:** open
- **promoted to:** —

## CE-037 · 2026-10-12 · Stand-up pouch renders standing at the writer's forearm although the prompt says it lies flat
- **source:** agent
- **video:** 14
- **run:** C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261008-235833-08
- **delivered:** CapCut project 09_Oct_2026_v14-2 · clean C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261008-235833-08/60-outputs/video-14/clean.mp4 · credits 78 · run QC: r2 accepted (flat sachet). POSTURE/SUPPORT: lies flat on its wide face, label up, whole underside on bare marble with contact shadow, no tilt/edge/float at 30 fps (write, glance, flip, last). STORY: set down on the near table edge to the right of the writing hand, out of the way; a real person leaves a gum pack like that. Size 1.05x (5 cm width: 92-105 px vs 93 expected at 0.5 m). Count 1/1/1, sealed. Never touches the arm: 2-D marble gap 18-37 px (~0.2 hand-width; flagged, frame leaves only ~150 px under the forearm). r1 carton rejected: flat and ~1.1x but its corner sat against the forearm (gap 3-4 px) 0.5-8 s. CE-001/002/003/004/006/007/008/010/012 pass; CE-012 set fixed with the r2 prompt.
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Neuro Energy & Focus Extra Strength Peppermint 90-piece pouch (V05 recreate, CE-033 fix pass 1)
- **assets:** pouch front A567 p40 + left A568 p40 (upright renders), char-K3, V05 own-silent; pouch 17.9 x 10.2 x 4.6 cm; new-account media 0f92492b/a14ee394/9e7ce7cb/84637256
- **user said:** — (caught by the agent during the run)
- **what was wrong:** Fix pass 1 asked for the 90-piece pouch lying flat on its front face, label up, long side left-right on the near bare marble strip (flat wording incl. 'never stands up or leans' and 'no standing pouch'), with Image 2/3 the client's upright front and 3/4 renders. The model rendered it STANDING on its gusset in front of his left hand and forearm from frame 0 to the end, left edge about 5 px from the hand, overlapping the forearm: the CE-012 failure again (a pack standing at the arm of someone writing). Size was right (302 px tall; A vs his hand back at depth ratio 0.93: 1.11x; B table-plane distance 0.607 m: 1.11x; agree, within 15 %), count 1, sealed, label Neuro / Energy & Focus / Peppermint legible, but the 100MG caffeine band came back as wrong letters (10%LBS OF NATURAL CAFFENT).
- **brief:**
  ```text
  Video 14 of 18 - Recreate of V05: Neuro XE Peppermint carton, placement on the marble table
  Concept: the reference recreated as itself (same scenario, action, camera and timing), faces swapped to the supplied character(s), the product integrated (placement on the marble table).
  Why it works: Communicates: "what teachers think would happen if they let us listen to music in an exam" - the VO reads answers like a track; deadpan. Why Neuro: students under sustained mental load (A456 sec 4), calm and wry (G24), the product 'just happens to be there' (G23). Kept [E]: the take, the VO, writing, the page flip. Goal/job [I]: awareness; the carton on the marble, noticed; share line "this is why we can't have music". Adapted: man -> K3; the caption box and shirt print removed from the plate; the package is Extra Strength Peppermint, closed (hero per G18, form per G27).
  Reference pattern: V05 (see 20-analysis/cards/V05.md and families.md)
  Characters/assets: see the plan sec 2.3; Higgsfield media ids in 30-assets/uploads.json and the request file.
  Substitutions: Placement; the closed hardcover notebook (a solid, not a sheet hands move: CE-006) is the smallest native element that lets a 1.6 cm-thick carton stand readable; hands busy: no use beat (G19/G27 satisfied: no piece is taken).
  Counts & use: | entity | count | state |
  |---|---|---|
  | carton | 1 | upright on its long edge, propped against a closed hardcover notebook on the bare marble, lower right, ~0.6 m, closed, label 30 deg; never moved |
  | sheets | 1-2 | flipped at 9.2-10.4 over the left edge, away from the carton |
  Size: Carton 7.5 cm at ~0.6 m, 26 mm eq -> ~9.0% (~116 px) (T scale --product-cm 7.5 --distance 0.6 --lens 26); neighbour: the exam sheet (29.7 cm) -> ~0.25 of its length; his palm is ~8.5 cm wide, the carton 7.2 cm wide -> slightly narrower than his palm. Oversize check: a carton taller than ~0.4 of the sheet is a regenerate reason.
  Guardrails: G16 (the client's real renders are the only product references; no AI-invented packaging: QC compares the label geometry and any morphed text is a regenerate reason), G17/G18 (Extra Strength, Peppermint or Spearmint, 9-piece carton, closed; the 6-pack box never appears), G19/G27 (closed package, nobody takes a piece, no blister shown), G23/G24 (the product just happens to be there; calm, wry register), G25 [U] (no sleeping/drained scene), G11/G21 (no numbers or claims in any text layer; the carton's own 100MG band is the only number), G12 (no competitor shown or replaced), G13/G14 (an adult supplied character, no ambassador likeness), G22 (phone-shot, everything in focus).
  Caught errors applied: CE-006 (a product is never placed on or overlapping paper: bare surface or a solid prop; sheets stay flat; QC densifies the contact region for the whole shot), CE-007 (small closed carton by default in casual scenes; the pouch only where a large pack fits; a placed product never takes over the source's pick-up beat: the object picked up is named and the product stays), CE-008 (adult framing in captions and casting), CE-010 (text centred), CE-001 (the package count stays 1; nothing taken), CE-002
  Text: CapCut layer as in the scene.
  Inserts: none.
  Sound: Original VO audio restored.
  Fidelity approach: the silent own-content source as video_references (the most preserving input Wan 3.0 Prime offers: recreate-from-video-reference), exact duration rounded up, fidelity lock + the action script written out in the prompt; risks to fidelity or sync: lip-sync and exact timing are not guaranteed by this model; sync-check after the merge.
  Model & operation: video-14-request.json: wan3_0_prime reference-to-video, 13 s, 9:16 720p, generate_audio false, 4 media - est. 39 credits (3 credits/s, preflight read: no adjustments)
  Adaptation logic: One generation of 13 s (own 12.07 s). Credits 39. No inserts.
  
  ## Redo (CE-012, 2026-10-09)
  r1: closed XE Peppermint carton lying flat label up on the bare near-camera marble, lower right (50-requests/video-14-r1-request.json, p40 refs 36960471/2bc3de47) - flat and ~1.1x but against the forearm; r2: flat-lying single Energy & Focus Peppermint sachet on the same strip, band of marble to the forearm (50-requests/video-14-r2-request.json) - delivered. Action script and fidelity lock unchanged. CapCut project 09_Oct_2026_v14-2.
  
  ## Client fix 2026-10-12 (CE-033), attempt fix1 (ledger 14-fix attempt 4)
  Concept unchanged (V05 exam scene, same man K3, caption, original audio, sync anchors). Change: the product is the Neuro Energy & Focus Extra Strength Peppermint 90-piece POUCH (17.9 x 10.2 x 4.6 cm), sealed, lying flat on its front face, label up, long side left-right on the near-camera bare marble strip below the forearm, top seal to the right, count 1; plan: 40-briefs/video-14-fix-plan-20261012.md.
  Why: the client read the delivered sachet as box-sized ("the bag is bigger than the boxes"); the delivered 1.05x had rested on an assumed 0.5 m, the frame puts the strip at about 0.6 m (sachet 1.2-1.35x). Size ladder: pouch 17.9 : carton 7.5 : sachet 7 cm (2.4 : 1 : 0.93).
  Reference pattern: V05; fidelity lock and action script as delivered (r2 request structure); request 50-requests/video-14-fix1-request.json: wan3_0_prime reference-to-video, 13 s 9:16 720p, generate_audio false, enable_thinking true, 4 media (Video 1 own-silent, Image 1 K3, Image 2 pouch front A567 p40, Image 3 pouch left A568 p40), new-account media ids (30-assets/uploads-fix-14.json), no folder_id; 4920 chars; preflight 39 credits, no adjustments (preset recommendation declined).
  Size: pouch at 0.6 m (distance from the frame: hand back 160 px = 10.5 cm, A4 sheet 21 cm = 285 px -> hands 0.65-0.68 m; table plane: strip 0.56-0.62 m), f 26 mm eq: long side 276 px (38 % of the frame width), short side about 83 px of frame height (157 x 0.53 foreshortening); hand 18 cm = 245 px at 0.68 m. Accept within 25 % by A (hand, depth ratio from the frame) and B (derived distance); check both too small (client's miss) and too big.
  Posture/support/place/story: lies flat, label up, bare marble only, band of marble to the forearm and below it, not touching the arm or sheets; he set it down on the near edge out of the pen hand's way. Object picked up: the exam sheet (flip 9.2-10.4); the pouch stays.
  Risks: the model may stand the pouch up (reference shows it upright), inflate it, or cross the forearm; levers for attempt 2 are in the plan (pose reference / anchor depth), not sizing words. Text layer: caption posX 0, posY 0.66 in CapCut, house style, no emoji. Credits cap 3 x 39.
  ```
- **prompt:**
  ```text
  [Core Task] Generate single shot. The man corresponds to Image 1, adopting only his facial features and hairstyle and light stubble; man replaces only the person in Video 1 and keeps the plain white t-shirt without lettering and the white over-ear headphones; do not use the background, props or clothing of Image 1. His face, neck, hands and forearms share one consistent skin tone as in Image 1. Use Video 1 for his movements, expressions, gaze, the camera framing, the room, the exam sheets and the timing. The pouch corresponds to Images 2 and 3, which jointly define the same entity, and generates only one instance, adopting only its structure, material, colours and printed label (a closed, sealed stand-up gum pouch about 18 cm tall and 10 cm wide, plump when full, of sky-blue matte foil with a zipper strip under a flat top seal, the dark-blue Neuro wordmark top-left, a mint and navy EXTRA STRENGTH GUM badge top-right, a Peppermint tag, 'Energy & Focus' in large navy type, '90 Pieces Dietary Supplement' and a navy band along the bottom); the pouch keeps its real size; do not use the framing, lighting, exposure, background, shadow or camera angle of Images 2 and 3.
  [Plot Summary] Locked phone camera at eye level, medium shot, a white marble table filling the lower third, a bright room corner with a white door and warm lamp light from the upper left. He sits turned about forty degrees toward the left of the frame with his head tilted left, listening to his headphones, a blue pen in his right hand resting on an exam sheet and his left hand flat on the table; he turns his head down to the sheet and squares his torso; he writes with small right-hand strokes, glancing up and to the left once, and keeps writing; then both hands lift the right edge of the sheet and flip it over to the left, his left hand smoothing it down, and it lands on the same spot; he writes again with a glance to the right of the frame. A single closed sealed Neuro Energy & Focus Extra Strength Peppermint pouch lies flat on its front face with its printed label facing up, its top seal pointing to the right of the frame so that the label reads sideways, resting entirely on the bare white marble in the lower middle of the frame, on the near side of the table, nearer the lens than his hands and forearm, where someone sets a pouch of gum down out of the way of their writing. It is fully inside the frame, with a visible band of bare marble between it and his forearm and hands and another below it, away from the exam sheets; nothing touches it and nobody picks it up. It is about sixty centimetres from the lens and true to its real size, about as long as his hand from wrist to fingertip and a little wider than his open palm, its long side spanning about two fifths of the frame width and its short side about one fifteenth of the frame height as it lies, seen from above at a slight angle as a flat plump rectangle, lit by the same warm lamp light with a soft contact shadow on the marble falling to the right like the sheets' shadows; it stays flat on that spot for the whole clip and never slides, tilts, stands up or leans, the exam sheets lie flat except when he flips the top one, and the flipped sheet stays on the left and never reaches the pouch. Phone-shot look, everything in focus. Real-time speed. No dialogue. No background music.
  [Camera & Core Constraints] Keep every movement, gesture, expression, gaze and mouth movement of the person in Video 1 on the same frames, the props and how they are handled, the camera framing, the light, the room and the timing of Video 1 unchanged; no added, skipped, repeated or reordered action, no new gesture, no extra camera move, no re-staging, no new people, no change of pace. There is exactly one pouch, constant and true to its real size, lying flat, sealed with its zipper closed and never opened, not duplicated, not vanished, not deformed, no scale drift; nothing passes through it. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen; the only lettering is the printed label on the Neuro pouch, exactly as in Image 2; do not reproduce any text, captions, usernames or watermarks from Video 1.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no slow motion, no self-inserted cut points, no added or skipped action, no face lighter or darker than the hands, no oversized or giant package, no pouch much longer than his hand, no standing, upright, leaning, propped, folded or tilted pouch, no pouch on its base or on its edge, no pouch on a sheet, no pouch touching his arm or hand, no notebook, no carton, no sachet, no six-pack box, no blister card, no opened pouch, no torn top, no loose gum pieces, no gum in anyone's mouth, no chewing, no second package, no studio lighting on the package, no glow, no white caption box, no text on the shirt
  ```
- **params:** model=wan3_0_prime · duration=13 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=video_references, image_references×3 · request=video-14-fix1-request.json
- **errors:**
  ```text
  none: job d19013be completed, 39 credits, no adjustments, preset recommendation declined
  ```
- **evidence:** fix-20261012/a4/qc/dense/sheet-03-flip-01.jpg (30 fps, pouch upright from 9.0 to 10.6 s), a4/f0.5.png, a4/f6.0.png, a4/crop6.png: upright from frame 0 to the last frame, left edge against his hand/forearm (about 5 px)
- **qc:**
  ```text
  r2 accepted (flat sachet). POSTURE/SUPPORT: lies flat on its wide face, label up, whole underside on bare marble with contact shadow, no tilt/edge/float at 30 fps (write, glance, flip, last). STORY: set down on the near table edge to the right of the writing hand, out of the way; a real person leaves a gum pack like that. Size 1.05x (5 cm width: 92-105 px vs 93 expected at 0.5 m). Count 1/1/1, sealed. Never touches the arm: 2-D marble gap 18-37 px (~0.2 hand-width; flagged, frame leaves only ~150 px under the forearm). r1 carton rejected: flat and ~1.1x but its corner sat against the forearm (gap 3-4 px) 0.5-8 s. CE-001/002/003/004/006/007/008/010/012 pass; CE-012 set fixed with the r2 prompt.
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261008-235833-08\40-briefs\video-14-plan.md
- **class:** anomaly-catalog.md §2.16 (posture, support and place); wan-3-0.md §3.14 and §5 (a pack renders upright although the prompt says lies flat)
- **cause:** reference
- **fix:** none yet
- **verified prompt:** pending (inserted only after a new generation passes QC)
- **rule:** For a pack whose natural posture is standing (a stand-up pouch) that the plan lays flat, the references must show it lying flat (a pose reference built from the client's own render by a geometric transform: rotated, foreshortened) and the prompt must not call it a stand-up pouch; upright references plus 'lies flat' wording renders it standing, whatever the exclusions say. The retry changes the reference lever, not the flat wording or the sizing words.
- **status:** open
- **promoted to:** —

## CE-038 · 2026-10-12 · Flat-lying carton beside the notebook renders 1.7-2.1x its size, thick and rotated, and the right hand lands on it
- **source:** agent
- **video:** 22
- **run:** C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07
- **delivered:** CapCut project 08_Oct_2026_v22 · clean C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07/60-outputs/video-22/clean.mp4 · credits 21 · run QC: accepted
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Neuro Energy & Focus Cinnamon 9-piece carton (V16 recreate, fix pass for CE-034, attempt 1: flat-lying carton right of the notebook)
- **assets:** A09.jpg (Image 1); A709-p40.png and A708-p25.png (carton padded to 40 and 25 percent of the canvas width); V16 own-silent.mp4 6.3 s; carton 7.5 x 8 x 1.6 cm
- **user said:** — (caught by the agent during the run)
- **what was wrong:** a1 asked for the carton lying flat, label up, on the bare wood right of the notebook at the notebook's depth, with palm-width, one-third-of-the-notebook and one-fifth-of-the-frame words. The model drew a thick box 282-299 px wide (0.61-0.75 of the notebook's visible page width against 0.357 true: A 1.7-2.1x; B from the table plane 1.74x; A and B agree), tilted about 10 degrees, not flat-looking, and moved the notebook to the left edge where the page is cropped by the frame. The source's right hand rests on the notebook's right half and the carton stood there: the hand lands on the carton at 3.77-3.97 s and 6.2 s (contact, regenerate reason). Size words and the p40/p25 references did not move it, as the guide predicts
- **brief:**
  ```text
  Video 22 of 22 — NEUROGUM — Recreate V16
  Concept: V16 recreated beat for beat with character A09 and the Neuro Energy & Focus gum carton (Cinnamon, 9 pieces).
  Reference pattern: V16 card (timing, beats, inserts at 1.80-4.40, 6.70-9.30).
  Characters/assets: A09 (Image 1); A709.jpg, A708.jpg.
  House approach: none (no examples).
  Substitutions: creator → A09 | Placement: stands upright at the front-right corner of the table, outside the sweep of the hands, label toward the lens, in the same spot in every shot.
  Main action & states: source beats unchanged; product untouched and persistent.
  Style & camera: as V16, static phone camera, the source's light.
  Text: CapCut layers in the house style, reference wording/positions (see plan).
  Inserts: V16 1.80-4.40, V16 6.70-9.30.
  Sound: original audio restored; inserts with their own sound.
  Model & operation: wan3_0_prime reference-to-video (≈ recreate from Video 1), 7 s → trim 6.300 s, 9:16 720p, audio off, thinking on · est. 21 credits
  Fidelity: Video 1 = silent own content (motion/camera/timing), action script written out in order, keep-list + exclusions, same duration; sync-check after the merge. Risk: low.
  Adaptation logic: product placed at the analysed anchor; source branding dropped.
  ```
- **prompt:**
  ```text
  [Core Task] Recreate Video 1 as a real phone-shot vertical clip with only these changes: the person and the product. Video 1 is the motion, camera, framing, cut and timing reference: keep every movement, gesture, head turn, gaze, expression and mouth movement of the person in Video 1 in the same order, at the same moments and at the same real-time speed, and keep the camera, framing, cuts, light, room and background. Do not inherit the appearance, clothing, text, captions, usernames, watermarks or branded items of Video 1. The man corresponds to Image 1, adopting facial features, hairstyle, skin tone, build and clothing (short hair, stubble); Image 1 is only his identity, not its pose, background or objects. The man replaces the person of Video 1 and performs exactly that person's movements. The Neuro Energy & Focus gum carton (Cinnamon, 9 pieces) corresponds to Image 2 and Image 3, which jointly define one single package, adopting only its structure, material, colours and printed label: a small closed flat paperboard carton, 7.5 cm wide, 8 cm long and 1.6 cm thick, light blue with wavy lighter-blue shapes, a blue N logo and Neuro wordmark top-left, an orange-red GUM badge top-right, a Cinnamon tag, the title Energy & Focus. In Image 2 and Image 3 the carton is deliberately small in the frame and keeps that small scale; do not use their framing, lighting, background, shadow or camera angle. Keep its exact shape, proportions and artwork without deformation and without scale drift; it stays closed. Video 1 has no such item, but the carton is part of this scene from the first frame: it lies flat on its wide face with its printed label facing up and its top edge pointing away from the camera, resting entirely on the bare wooden tabletop directly to the right of the open spiral notebook, in the same plane and at the same distance from the lens as the notebook, a narrow band of bare wood between the notebook's right edge and the carton and bare wood to its right, fully inside the frame, where someone sets a pack of gum down out of the way of their hands; lit by the scene's own light with a soft contact shadow, untouched and in the same place for the whole clip.
  [Plot Summary] The open spiral notebook lies at the bottom of the frame a little left of centre, its whole page in view, about 21 cm wide. The carton beside it is small: about as wide as three fingers, a little narrower than the man's open palm, about one third as wide as the notebook page and about one fifth of the frame width, a thin flat slab with its label foreshortened; it keeps exactly this size before and after every cut.
  Shot 1 [0-1.8s]: Static selfie framing from the table edge, a door frame behind. The carton lies flat on the bare wood right of the notebook. The man sits square to the camera, leaning forward, both palms flat on the notebook with fingers tapping, head bobbing, mouth moving rapidly as if arguing, brows raised, intense eyes to the lens; the frame-right hand lifts the top page, flips it and slaps it back down; then wide sweeping open-hand gestures across the table, leaning in, mouth still talking, as the image brightens toward white; his hands and arms pass above the carton and never touch it.
  Shot 2 [1.8-4.1s]: Hard cut, same framing, the one carton still lies flat in the same spot: he leans back then forward, hands chopping and waving, palms-up shrugs, mouth arguing; hands come down to the notebook; the right index finger taps the temple; the arm flings out wide toward frame-right above the carton and comes back down to the notebook.
  Shot 3 [4.1-6.3s]: Hard cut, same framing, the one carton still lies flat in the same spot: hands out palms up in a shrug, a quick temple tap, an arm swing wide to frame-right above the carton; then both hands on the notebook tapping and sliding across the page as proof; a hand wipes across the mouth and nose, then a final open gesture, still mouthing.
  [Audio Style] No dialogue. No background music.
  [Camera & Core Constraints] Camera: static throughout. Real-time speed, nothing added, skipped, repeated or reordered, no new gesture, no extra camera move, no re-staging, no new people. Exactly one carton, closed, flat, not duplicated, not vanished, not deformed, constant in size; nothing passes through it. No subtitles, captions or other on-screen text; the only lettering is the printed label on the package.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no extra fingers, no duplicate packages, no scale drift, no slow motion, no speed ramps, no other brands, no oversized or giant carton, no carton as wide as the notebook, no carton wider than his palm, no standing, leaning, propped or tilted carton, no carton on its edge, no carton on the notebook or on any paper, no carton touching his hand or arm, no studio lighting on the carton, no glow, no blister, no opened carton, no loose gum pieces
  ```
- **params:** model=wan3_0_prime · duration=7 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=image_references×3, video_references · request=video-22-fix-a1-request.json
- **errors:**
  ```text
  none; job 64fe0c90-8040-41db-b2e8-2bb82daf7631 completed, 21 credits; preset notice IN THE DARK declined
  ```
- **evidence:** a1 frames 0.0, 3.0, 4.0, 6.2 s and dense sheet C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07/60-outputs/video-22/fix-20261012/a1/qc/dense/sheet-02-hand-right-01.jpg; T scale JSON C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07/60-outputs/video-22/fix-20261012/a1/scale_rest.json and scale_rest_470.json
- **qc:**
  ```text
  accepted
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261007-232745-07\40-briefs\video-22-plan.md
- **class:** anomaly-catalog.md 2.7 (size reckoning) and 2.16 (posture, support and place); wan-3-0.md 5 size row
- **cause:** model-limit
- **fix:** Fixed by a3: a scale-reference composite as Image 4 (carton at 0.85x true size beside the V16 notebook) AND a spot that exists in the source frame outside the hands' reach (free front-left corner, bare grey front edge, upright) brought the carton from 1.7-2.1x to 0.91-0.93x (A) / 0.90-0.91x (B) on wan3_0_prime.
- **verified prompt:**
  ```text
  [Core Task] Recreate Video 1 as a real phone-shot vertical clip with only these changes: the person and the product. Video 1 is the motion, camera, framing, cut and timing reference: keep every movement, gesture, head turn, gaze, expression and mouth movement of the person in Video 1 in the same order, at the same moments and at the same real-time speed, and keep the camera, framing, cuts, light, room, background and the notebook's place. Do not inherit the appearance, clothing, text, captions, usernames, watermarks or branded items of Video 1. The man corresponds to Image 1, adopting facial features, hairstyle, skin tone, build and clothing (short hair, stubble); Image 1 is only his identity, not its pose, background or objects. The man replaces the person of Video 1 and performs exactly that person's movements. The Neuro Energy & Focus gum carton (Cinnamon, 9 pieces) corresponds to Image 2 and Image 3, which jointly define one single package, adopting only its structure, material, colours and printed label: a small closed flat paperboard carton, 7.5 cm wide, 8.5 cm tall and 1.6 cm thick, light blue with wavy lighter-blue shapes, a blue N logo and Neuro wordmark top-left, an orange-red GUM badge top-right, a Cinnamon tag, the title Energy & Focus. Image 4 is a size and spot reference only: it shows this carton standing on the grey front edge of the table at the front-left corner beside the notebook of Video 1, only about one third as wide as the notebook page; use that size relation and that spot, not its framing, wall, lighting or perspective. Keep its exact shape, proportions and artwork without deformation and without scale drift; it stays closed. Video 1 has no such item, but the carton is part of this scene from the first frame: it stands upright on its base on the bare grey front edge of the table at the front-left corner, to the left of the open spiral notebook, its base level with the notebook's front edge, no nearer to the lens than the notebook, not touching or overlapping the notebook, a band of bare table between them and bare table to its left, fully inside the frame; lit by the scene's own light with a soft contact shadow, untouched and in the same place for the whole clip.
  [Plot Summary] The open spiral notebook lies at the bottom centre exactly as in Video 1, its whole page in view, about 21 cm wide; the carton at the front-left corner is small beside it: about one third as wide as the notebook page, a little narrower than the man's open palm and about one fifth of the frame width; it keeps exactly this size before and after every cut.
  Shot 1 [0-1.8s]: Static selfie framing from the table edge, a door frame behind. The carton stands at the front-left corner left of the notebook. The man sits square to the camera, leaning forward, both palms flat on the notebook with fingers tapping, head bobbing, mouth moving rapidly as if arguing, brows raised, intense eyes to the lens; the frame-right hand lifts the top page, flips it and slaps it back down; then wide sweeping open-hand gestures across the table, leaning in, mouth still talking, as the image brightens toward white; his hands and arms stay farther from the lens than the carton and never touch it.
  Shot 2 [1.8-4.1s]: Hard cut, same framing, the one carton still stands at the front-left corner: he leans back then forward, hands chopping and waving, palms-up shrugs, mouth arguing; hands come down to the notebook; the right index finger taps the temple; the arm flings out wide toward frame-right and comes back down to the notebook.
  Shot 3 [4.1-6.3s]: Hard cut, same framing, the one carton still stands at the front-left corner: hands out palms up in a shrug, a quick temple tap, an arm swing wide to frame-right; then both hands on the notebook tapping and sliding across the page as proof; a hand wipes across the mouth and nose, then a final open gesture, still mouthing.
  [Audio Style] No dialogue. No background music.
  [Camera & Core Constraints] Camera: static throughout. Real-time speed, nothing added, skipped, repeated or reordered, no new gesture, no extra camera move, no re-staging, no new people. Exactly one carton, closed, upright, not duplicated, not vanished, not deformed, constant in size; nothing passes through it. No subtitles, captions or other on-screen text; the only lettering is the printed label on the package.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no extra fingers, no duplicate packages, no scale drift, no slow motion, no speed ramps, no other brands, no oversized or giant carton, no carton as wide as the notebook, no carton wider than his palm, no carton closer to the camera than the notebook, no carton on the notebook or on any paper, no carton right of the notebook, no lying or tilted carton, no carton touching his hand or arm, no studio lighting on the carton, no glow, no blister, no opened carton, no loose gum pieces
  ```
- **prompt change:**
  ```text
  - Video 1 is the motion, camera, framing, cut and timing reference: keep every movement, gesture, head turn, gaze, expression and mouth movement of the person in Video 1 in the same order, at the same moments and at the same real-time speed, and keep the camera, framing, cuts, light, room and backgrou
  + Video 1 is the motion, camera, framing, cut and timing reference: keep every movement, gesture, head turn, gaze, expression and mouth movement of the person in Video 1 in the same order, at the same moments and at the same real-time speed, and keep the camera, framing, cuts, light, room, background 
  - The Neuro Energy & Focus gum carton (Cinnamon, 9 pieces) corresponds to Image 2 and Image 3, which jointly define one single package, adopting only its structure, material, colours and printed label: a small closed flat paperboard carton, 7.5 cm wide, 8 cm long and 1.6 cm thick, light blue with wavy
  - In Image 2 and Image 3 the carton is deliberately small in the frame and keeps that small scale;
  - do not use their framing, lighting, background, shadow or camera angle.
  + The Neuro Energy & Focus gum carton (Cinnamon, 9 pieces) corresponds to Image 2 and Image 3, which jointly define one single package, adopting only its structure, material, colours and printed label: a small closed flat paperboard carton, 7.5 cm wide, 8.5 cm tall and 1.6 cm thick, light blue with wa
  + Image 4 is a size and spot reference only: it shows this carton standing on the grey front edge of the table at the front-left corner beside the notebook of Video 1, only about one third as wide as the notebook page;
  + use that size relation and that spot, not its framing, wall, lighting or perspective.
  - Video 1 has no such item, but the carton is part of this scene from the first frame: it lies flat on its wide face with its printed label facing up and its top edge pointing away from the camera, resting entirely on the bare wooden tabletop directly to the right of the open spiral notebook, in the s
  + Video 1 has no such item, but the carton is part of this scene from the first frame: it stands upright on its base on the bare grey front edge of the table at the front-left corner, to the left of the open spiral notebook, its base level with the notebook's front edge, no nearer to the lens than the
  - [Plot Summary] The open spiral notebook lies at the bottom of the frame a little left of centre, its whole page in view, about 21 cm wide.
  - The carton beside it is small: about as wide as three fingers, a little narrower than the man's open palm, about one third as wide as the notebook page and about one fifth of the frame width, a thin flat slab with its label foreshortened;
  + [Plot Summary] The open spiral notebook lies at the bottom centre exactly as in Video 1, its whole page in view, about 21 cm wide;
  + the carton at the front-left corner is small beside it: about one third as wide as the notebook page, a little narrower than the man's open palm and about one fifth of the frame width;
  … 14 more changed sentences
  ```
- **verified params:** model=wan3_0_prime · duration=7 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=image_references×4, video_references · request=video-22-fix-a3-request.json
- **rule:** Where a source's working hands cover every bare spot at the product's depth, a carton asked to lie at the neighbour's depth is rendered 1.7-2x large and in the hands' zone: size words, a flat posture and padded references do not change it; the lever is a size cue the model copies (a scale-reference image that shows the carton beside the neighbour at the true ratio) or a spot outside the hands' reach
- **status:** fixed
- **promoted to:** —
- **verified:** the regeneration a3 (job 4451b1c8-6e71-4eba-a843-75b1cce7441c) passed QC: carton 0.91-0.93x (A) / 0.90-0.91x (B) of its reckoned size beside the notebook, count 1 closed upright, same spot on both sides of each insert, on the bare front edge of the table; sync in_sync, original audio whole, text present (2026-10-12)

## CE-039 · 2026-10-12 · Cropped chest print of the identity photo: the model invents the cut-off second line, upside down
- **source:** agent
- **video:** 20
- **run:** C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07
- **delivered:** CapCut project 08_Oct_2026_v20 · clean C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07/60-outputs/video-20/clean.mp4 · credits 15 · run QC: accepted
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Neuro Extra Strength Spearmint 90-piece pouch (V06 recreate, study desk, placement; fix pass 2026-10-12)
- **assets:** A01-flipped.jpg (736x1000, chest print cut off at the bottom edge: line 1 GEN- complete, line 2 only the tops of ATIO), A767.jpg/A768.jpg real renders, own-silent-flipped.mp4 5.000 s 720x1280
- **user said:** — (caught by the agent during the run)
- **what was wrong:** Video 20 fix a1: Image 1 (A01 flipped, true orientation) shows the cyan chest print only partly (GEN- complete, the second line cut by the photo's bottom edge). The generated shirt prints line 1 GEN- correctly but invents line 2 as upside-down mirrored letters (reads like a flipped CAT) in every frame: the client's complaint (reversed text on his shirt) would survive in a new form. The rest of a1 passed (un-mirrored room, guitar and notebook sides, open pouch count 1, same spot across the flash, label legible, sync in_sync).
- **brief:**
  ```text
  Video 20 of 22 — NEUROGUM — Recreate V06
  Concept: V06 recreated beat for beat with character A01 and the Neuro Extra Strength Energy & Focus gum pouch (Spearmint).
  Reference pattern: V06 card (timing, beats, inserts at 3.07-5.00).
  Characters/assets: A01 (Image 1); A767.jpg, A768.jpg.
  House approach: none (no examples).
  Substitutions: creator → A01 | Placement: stands on the desk at the lower-left, left of the notebook, label toward the camera, in the same spot before and after the cut.
  Main action & states: source beats unchanged; product untouched and persistent.
  Style & camera: as V06, static phone camera, the source's light.
  Text: CapCut layers in the house style, reference wording/positions (see plan).
  Inserts: V06 3.07-5.00.
  Sound: original audio restored; inserts with their own sound.
  Model & operation: wan3_0_prime reference-to-video (≈ recreate from Video 1), 5 s → trim 5.000 s, 9:16 720p, audio off, thinking on · est. 15 credits
  Fidelity: Video 1 = silent own content (motion/camera/timing), action script written out in order, keep-list + exclusions, same duration; sync-check after the merge. Risk: low.
  Adaptation logic: product placed at the analysed anchor; source branding dropped.
  
  ## Fix pass 2026-10-12, attempt a1 (CE-030 mirrored source, CE-031 sealed pouch)
  Video 20 fix - NEUROGUM - Recreate V06 (un-mirrored, open pouch)
  Concept: V06 recreated beat for beat with A01 and the open Neuro Extra Strength Energy & Focus Spearmint 90-piece pouch; the source and Image 1 are horizontally flipped to true orientation (both were mirrored selfies), the pouch stands open on the desk to the right of the notebook.
  Why it works: the study-desk "that one kid" joke and the white-flash insert are unchanged; the pouch just happens to be there, open because he chews gum in class (CE-031).
  Reference pattern: V06 card (timing, beats, insert 3.07-5.00), sides swapped.
  Characters/assets: Image 1 = A01 flipped; Images 2-3 = A767/A768 real renders; Video 1 = own-silent flipped.
  Substitutions: creator -> A01 | Placement: open pouch upright on its gusset, bare black desk right of the notebook, same spot from frame 0 and after the flash.
  Counts & use: pouch 1 (open, never poured, nothing loose, nobody touches it); the pen is the only picked-up object. QC checkpoints in the fix plan.
  Size: 17.9 cm at ~0.57 m, 26 mm -> ~22.7 % of frame height (~290 px); neighbours: notebook and his hand; size ladder pouch ~2.4x carton; baseline of the delivered take ~1.45x.
  Guardrails: Content Guardrails.pdf (neurogum): real renders only, one piece at a time, adult talent, no caffeine number except the pouch band.
  Caught errors applied: CE-030, CE-031, CE-032, CE-005/014/028/033/034, CE-007/012/013, CE-010, CE-016/024/025/026, CE-018/019, CE-029.
  Style & camera: as V06, static phone camera, the source's light.
  Text: one CapCut layer, house style, posX 0, posY 0.80 (as delivered).
  Inserts: V06 3.07-5.00 (streamer, not flipped: no readable text), placed at 3.067 s; original audio whole.
  Model & operation: wan3_0_prime reference-to-video, 5 s, 9:16 720p, audio off, thinking on - 15 credits (preflight 15, no adjustments).
  Adaptation logic: the flipped source and flipped A01 (CE-030), the open pouch (CE-031), sides of the action script swapped, pouch moved from left of the notebook to its right (the notebook is at the lower-left now).
  Request: 50-requests/video-20-fix-a1-request.json
  ```
- **prompt:**
  ```text
  [Core Task] Recreate Video 1 as a real phone-shot vertical clip with only these changes: the person and the product. Video 1 is already in true orientation and is the motion, camera, framing, cut and timing reference: keep every movement, gesture, head turn, gaze, expression and mouth movement of the person in Video 1 in the same order, at the same moments and at the same real-time speed, and keep the camera, framing, light, room and background exactly as in Video 1, with the same left and right (guitars on the wall at the frame-left, the blue notebook at the lower frame-left, the pen in the frame-left hand); nothing is mirrored or flipped and all lettering reads correctly from left to right. Do not inherit the appearance, clothing, text, captions, usernames, watermarks or branded items of Video 1. The young man corresponds to Image 1, adopting facial features, hairstyle, skin tone, build and clothing (short brown hair, trimmed beard, a black crew-neck t-shirt with the cyan outlined chest print exactly as in Image 1, reading left to right); Image 1 is only his identity and clothing, not its pose, background or objects. He replaces the person of Video 1 and performs exactly that person's movements. The Neuro Extra Strength Energy & Focus gum pouch (Spearmint) corresponds to Image 2 (front) and Image 3 (angled view); both jointly define one single pouch, only its shape, proportions, colours and printed label, not their lighting, background, shadow or camera angle: a stand-up pouch about 18 cm tall, 10 cm wide and 5 cm deep, light turquoise with large brighter-cyan wave shapes, the dark-blue Neuro wordmark top-left, a small dark-blue EXTRA STRENGTH badge over a green GUM badge top-right, a green Spearmint tag, the large dark-blue title Energy & Focus, 90 Pieces Dietary Supplement, and a dark-blue base band reading 100MG OF NATURAL CAFFEINE; the label reads exactly as in Image 2, upright and never mirrored, without deformation and without scale drift.
  [Plot Summary] From the first frame to the last, an open Neuro Extra Strength Energy & Focus gum pouch (Spearmint) stands upright on its flat gusseted base on the bare black desk to the right of the blue notebook, its top strip torn off at the tear notches and its zipper mouth open, a few round white tablets with green flecks just visible inside the dark mouth, its label turned about twenty degrees toward the lens; it is part of this scene although Video 1 has none. It is about as tall as his hand is long and a little shorter than the notebook is wide, at the notebook's depth about half a metre from the lens, its left side two finger-widths from the notebook's right edge, lit by the room's soft light with a soft contact shadow like the notebook's. Nobody touches it, nothing is poured or taken, the pen is the only object he picks up, and the pouch stays exactly there in every frame, also after the white flash.
  Shot 1 [0-3.1s]: Static selfie framing, medium close-up, slightly low. The young man sits leaning slightly forward over the notebook, head bowed, eyes half-closed, his frame-left hand writing short strokes with a silver pen, his frame-right hand resting by his chest, lips moving as if explaining. He releases the pen onto the notebook and both hands rise to chest height, palms open, fingers spread, alternating explanatory gestures, head tilting side to side, earnest. Then his frame-right index finger goes to his lips and chin, eyes rolled up thinking, mouth closed, as the image brightens to white.
  Shot 2 [3.1-5.0s]: Out of the white, same framing: smiling, his frame-right hand points a finger toward the lens and sweeps down in front of him; his frame-left hand picks the pen up from the notebook and writes, head slightly down, eyes up to the lens, a smug half-smile; while still writing, his frame-right index finger taps his temple, eyebrows up. The open pouch is still there, one pouch, the same spot.
  [Audio Style] No dialogue. No background music. No sound effects.
  [Camera & Core Constraints] Camera static, phone-shot look, everything in focus. Real-time speed, nothing added, skipped, repeated or reordered, no new gesture, no camera move, no re-staging, no new people. Always exactly one pouch, open, upright, never poured, not duplicated, not vanished, not deformed. No subtitles or on-screen text; the only lettering is the pouch label exactly as in Image 2 and the t-shirt print exactly as in Image 1.
  [Negative Prompts] no subtitles, no watermark, no mirrored image, no reversed lettering, no mirrored label, no face distortion, no identity drift, no costume changes, no extra fingers, no second pouch, no sealed pouch, no loose gum pieces on the desk, no spilled gum, no hand taking a piece, no chewing, no hand touching the pouch, no moving pouch, no oversized pouch, no pouch closer to the camera than the notebook, no pouch taller than his hand is long, no scale drift, no slow motion, no speed ramps, no other brands, no logo stickers
  ```
- **params:** model=wan3_0_prime · duration=5 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=image_references×3, video_references · request=video-20-fix-a1-request.json
- **errors:**
  ```text
  none (job c9978e8c-f54f-426e-8418-e3cbaa33fc51, 15 credits, no adjustments)
  ```
- **evidence:** 60-outputs/video-20/fix-20261012/a1/f/print4.0.png (full-res crop at 4.0 s), a1/qc/dense/sheet-06-pen-01.jpg and sheet-07-temple-01.jpg: second line of the chest print renders upside-down/mirrored ('OAT'/'CAT' flipped) from 0.6 s to the end
- **qc:**
  ```text
  accepted
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261007-232745-07\40-briefs\video-20-plan.md
- **class:** generation-system.md §4b.5 (asset photos bring their props) and anomaly-catalog.md §2.9 (orientation, label and parts); models/wan-3-0.md §3.11 (text renders approximately)
- **cause:** reference
- **fix:** A01-flipped.jpg cropped above the cut-off print row (A01-flipped-plain.jpg, 736x823, plain black tee) used as Image 1; prompt states 'plain black crew-neck t-shirt with no print, no lettering and no logo' and the negative 'no text or print on the t-shirt'; a2 shirt is plain with no text (OCR none), everything else of a1 kept
- **verified prompt:**
  ```text
  [Core Task] Recreate Video 1 as a real phone-shot vertical clip with only these changes: the person and the product. Video 1 is already in true orientation and is the motion, camera, framing, cut and timing reference: keep every movement, gesture, head turn, gaze, expression and mouth movement of the person in Video 1 in the same order, at the same moments and at the same real-time speed, and keep the camera, framing, light, room and background exactly as in Video 1, with the same left and right (guitars on the wall at the frame-left, the blue notebook at the lower frame-left, the pen in the frame-left hand); nothing is mirrored or flipped and all lettering reads correctly from left to right. Do not inherit the appearance, clothing, text, captions, usernames, watermarks or branded items of Video 1. The young man corresponds to Image 1, adopting facial features, hairstyle, skin tone, build and clothing (short brown hair, trimmed beard, a plain black crew-neck t-shirt with no print, no lettering and no logo); Image 1 is only his identity and clothing, not its pose, background or objects. He replaces the person of Video 1 and performs exactly that person's movements. The Neuro Extra Strength Energy & Focus gum pouch (Spearmint) corresponds to Image 2 (front) and Image 3 (angled view); both jointly define one single pouch, only its shape, proportions, colours and printed label, not their lighting, background, shadow or camera angle: a stand-up pouch about 18 cm tall, 10 cm wide and 5 cm deep, light turquoise with large brighter-cyan wave shapes, the dark-blue Neuro wordmark top-left, a small dark-blue EXTRA STRENGTH badge over a green GUM badge top-right, a green Spearmint tag, the large dark-blue title Energy & Focus, 90 Pieces Dietary Supplement, and a dark-blue base band reading 100MG OF NATURAL CAFFEINE; the label reads exactly as in Image 2, upright and never mirrored, without deformation and without scale drift.
  [Plot Summary] From the first frame to the last, an open Neuro Extra Strength Energy & Focus gum pouch (Spearmint) stands upright on its flat gusseted base on the bare black desk to the right of the blue notebook, its top strip torn off at the tear notches and its zipper mouth open, a few round white tablets with green flecks just visible inside the dark mouth, its label turned about twenty degrees toward the lens; it is part of this scene although Video 1 has none. It is about as tall as his hand is long and a little shorter than the notebook is wide, at the notebook's depth about half a metre from the lens, its left side two finger-widths from the notebook's right edge, lit by the room's soft light with a soft contact shadow like the notebook's. Nobody touches it, nothing is poured or taken, the pen is the only object he picks up, and the pouch stays exactly there in every frame, also after the white flash.
  Shot 1 [0-3.1s]: Static selfie framing, medium close-up, slightly low. The young man sits leaning slightly forward over the notebook, head bowed, eyes half-closed, his frame-left hand writing short strokes with a silver pen, his frame-right hand resting by his chest, lips moving as if explaining. He releases the pen onto the notebook and both hands rise to chest height, palms open, fingers spread, alternating explanatory gestures, head tilting side to side, earnest. Then his frame-right index finger goes to his lips and chin, eyes rolled up thinking, mouth closed, as the image brightens to white.
  Shot 2 [3.1-5.0s]: Out of the white, same framing: smiling, his frame-right hand points a finger toward the lens and sweeps down in front of him; his frame-left hand picks the pen up from the notebook and writes, head slightly down, eyes up to the lens, a smug half-smile; while still writing, his frame-right index finger taps his temple, eyebrows up. The open pouch is still there, one pouch, the same spot.
  [Audio Style] No dialogue. No background music. No sound effects.
  [Camera & Core Constraints] Camera static, phone-shot look, everything in focus. Real-time speed, nothing added, skipped, repeated or reordered, no new gesture, no camera move, no re-staging, no new people. Always exactly one pouch, open, upright, never poured, not duplicated, not vanished, not deformed. No subtitles or on-screen text; the only lettering is the pouch label exactly as in Image 2; the t-shirt carries no lettering.
  [Negative Prompts] no subtitles, no watermark, no text or print on the t-shirt, no mirrored image, no reversed lettering, no mirrored label, no face distortion, no identity drift, no costume changes, no extra fingers, no second pouch, no sealed pouch, no loose gum pieces on the desk, no spilled gum, no hand taking a piece, no chewing, no hand touching the pouch, no moving pouch, no oversized pouch, no pouch closer to the camera than the notebook, no pouch taller than his hand is long, no scale drift, no slow motion, no speed ramps, no other brands, no logo stickers
  ```
- **prompt change:**
  ```text
  - The young man corresponds to Image 1, adopting facial features, hairstyle, skin tone, build and clothing (short brown hair, trimmed beard, a black crew-neck t-shirt with the cyan outlined chest print exactly as in Image 1, reading left to right);
  + The young man corresponds to Image 1, adopting facial features, hairstyle, skin tone, build and clothing (short brown hair, trimmed beard, a plain black crew-neck t-shirt with no print, no lettering and no logo);
  - the only lettering is the pouch label exactly as in Image 2 and the t-shirt print exactly as in Image 1.
  - [Negative Prompts] no subtitles, no watermark, no mirrored image, no reversed lettering, no mirrored label, no face distortion, no identity drift, no costume changes, no extra fingers, no second pouch, no sealed pouch, no loose gum pieces on the desk, no spilled gum, no hand taking a piece, no chewi
  + the only lettering is the pouch label exactly as in Image 2;
  + the t-shirt carries no lettering.
  + [Negative Prompts] no subtitles, no watermark, no text or print on the t-shirt, no mirrored image, no reversed lettering, no mirrored label, no face distortion, no identity drift, no costume changes, no extra fingers, no second pouch, no sealed pouch, no loose gum pieces on the desk, no spilled gum,
  ```
- **verified params:** model=wan3_0_prime · duration=5 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=image_references×3, video_references · request=video-20-fix-a2-request.json
- **rule:** An identity photo whose clothing carries lettering is used only when that lettering is fully visible and un-mirrored in the image (a selfie photo is itself mirrored: read its text first and flip it); a print the photo cuts off is never left for the model to finish: the image is cropped above the print and the prompt states a plain garment with no print, no lettering and no logo, and QC reads every printed line at full resolution as part of the text check.
- **status:** fixed
- **promoted to:** —
- **verified:** a2 accepted (job 0edb3b0c-748c-475c-a68f-638579a7813a, ledger lane 20-fix attempt 3): un-mirrored room (guitars frame-left right-handed, notebook lower-left, pen in the frame-left hand), plain black tee with no readable text (OCR none), pouch label unmirrored and legible at full resolution (Neuro, EXTRA STRENGTH, GUM, Spearmint, Energy & Focus, 90 Pieces, 100MG OF NATURAL CAFFEINE), pouch OPEN (torn top, tablets in the mouth only) count 1 in every dense checkpoint and in 143 of 150 mask frames (rest are the white flash), same spot across the flash (x0 388-389 before, 386 after, drift <=3 px), nothing passes through it; size 1.15-1.23x by two methods (A and B agree, 15-25 pct note band, static, label readable); sync-check in_sync (offset -0.1 s, corr 0.83); original audio whole (decoded md5 identical); white flash rebuilt on own moving frames, no frozen frame; text layer posX 0, no emoji; evidence 60-outputs/video-20/fix-20261012/ (a2/qc/dense, assembly/qc/dense, a2/sync/sync-sheet.jpg, size/*.json, a2/f/label4.0.png, anchor-track.txt) (2026-10-12)

## CE-040 · 2026-10-12 · Upright carton right of the notebook stands on the notebook page at 1.28x its size (size-reference image halved the error)
- **source:** agent
- **video:** 22
- **run:** C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07
- **delivered:** CapCut project 08_Oct_2026_v22 · clean C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07/60-outputs/video-22/clean.mp4 · credits 21 · run QC: accepted
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Neuro Energy & Focus Cinnamon 9-piece carton (V16 recreate, fix pass for CE-034, attempt 2: upright right of the notebook with a size-reference image)
- **assets:** A09.jpg; A709-p40.png; A708-p25.png; scale-ref-carton-notebook.png (composite of the source frame at 2.0 s and the A709 packshot: carton 7.5 cm at true ratio 0.33 beside the notebook); V16 own-silent.mp4
- **user said:** — (caught by the agent during the run)
- **what was wrong:** a2 (upright, same plane as the notebook, plus a composite size-reference image of the carton beside the notebook at the true 0.33 ratio): the carton came out 183-189 px wide, A 1.23-1.27x vs the notebook (near-edge width 500 px, depth ratio 1.2 from its base row) and B 1.27-1.31x from the table plane calibrated on the source notebook: A and B agree, just over 25 percent, against 1.7-2.1x for the flat a1. But the model kept the notebook centred (the source layout) and, with no room right of it (40 px between the notebook corner and the frame edge), stood the carton on the notebook's upper-right page, base overlapping the sheet (CE-006 class: nothing on a thin sheet), and the right hand rests beside its right edge at 4.0 s
- **brief:**
  ```text
  Video 22 of 22 — NEUROGUM — Recreate V16
  Concept: V16 recreated beat for beat with character A09 and the Neuro Energy & Focus gum carton (Cinnamon, 9 pieces).
  Reference pattern: V16 card (timing, beats, inserts at 1.80-4.40, 6.70-9.30).
  Characters/assets: A09 (Image 1); A709.jpg, A708.jpg.
  House approach: none (no examples).
  Substitutions: creator → A09 | Placement: stands upright at the front-right corner of the table, outside the sweep of the hands, label toward the lens, in the same spot in every shot.
  Main action & states: source beats unchanged; product untouched and persistent.
  Style & camera: as V16, static phone camera, the source's light.
  Text: CapCut layers in the house style, reference wording/positions (see plan).
  Inserts: V16 1.80-4.40, V16 6.70-9.30.
  Sound: original audio restored; inserts with their own sound.
  Model & operation: wan3_0_prime reference-to-video (≈ recreate from Video 1), 7 s → trim 6.300 s, 9:16 720p, audio off, thinking on · est. 21 credits
  Fidelity: Video 1 = silent own content (motion/camera/timing), action script written out in order, keep-list + exclusions, same duration; sync-check after the merge. Risk: low.
  Adaptation logic: product placed at the analysed anchor; source branding dropped.
  ```
- **prompt:**
  ```text
  [Core Task] Recreate Video 1 as a real phone-shot vertical clip with only these changes: the person and the product. Video 1 is the motion, camera, framing, cut and timing reference: keep every movement, gesture, head turn, gaze, expression and mouth movement of the person in Video 1 in the same order, at the same moments and at the same real-time speed, and keep the camera, framing, cuts, light, room and background. Do not inherit the appearance, clothing, text, captions, usernames, watermarks or branded items of Video 1. The man corresponds to Image 1, adopting facial features, hairstyle, skin tone, build and clothing (short hair, stubble); Image 1 is only his identity, not its pose, background or objects. The man replaces the person of Video 1 and performs exactly that person's movements. The Neuro Energy & Focus gum carton (Cinnamon, 9 pieces) corresponds to Image 2 and Image 3, which jointly define one single package, adopting only its structure, material, colours and printed label: a small closed flat paperboard carton, 7.5 cm wide, 8.5 cm tall and 1.6 cm thick, light blue with wavy lighter-blue shapes, a blue N logo and Neuro wordmark top-left, an orange-red GUM badge top-right, a Cinnamon tag, the title Energy & Focus. Image 4 is a size reference only: it shows this carton standing on the table beside the notebook of Video 1, the carton about one third as wide as the notebook page; use only that size relation, not its framing, background, lighting or perspective. In Image 2 and Image 3 the carton is deliberately small in the frame and keeps that small scale. Keep its exact shape, proportions and artwork without deformation and without scale drift; it stays closed. Video 1 has no such item, but the carton is part of this scene from the first frame: it stands upright on its base on the bare table at the front edge, to the right of the open spiral notebook, its base level with the notebook's front edge, in the same plane as the notebook and no nearer to the lens than the notebook, its label turned about twenty degrees away from the lens, a band of bare table between the notebook and the carton; lit by the scene's own light with a soft contact shadow, untouched and in the same place for the whole clip.
  [Plot Summary] The open spiral notebook lies at the bottom left of the frame, its whole page in view, about 21 cm wide; the carton stands to its right and is small beside it: about one third as wide as the notebook page, a little narrower than the man's open palm and about one fifth of the frame width; it keeps exactly this size before and after every cut.
  Shot 1 [0-1.8s]: Static selfie framing from the table edge, a door frame behind. The carton stands on the table right of the notebook. The man sits square to the camera, leaning forward, both palms flat on the notebook with fingers tapping, head bobbing, mouth moving rapidly as if arguing, brows raised, intense eyes to the lens; the frame-right hand lifts the top page, flips it and slaps it back down; then wide sweeping open-hand gestures across the table, leaning in, mouth still talking, as the image brightens toward white; his hands and arms stay farther from the lens than the carton and never touch it.
  Shot 2 [1.8-4.1s]: Hard cut, same framing, the one carton still stands in the same spot: he leans back then forward, hands chopping and waving, palms-up shrugs, mouth arguing; hands come down to the notebook; the right index finger taps the temple; the arm flings out wide toward frame-right behind the carton and comes back down to the notebook.
  Shot 3 [4.1-6.3s]: Hard cut, same framing, the one carton still stands in the same spot: hands out palms up in a shrug, a quick temple tap, an arm swing wide to frame-right behind the carton; then both hands on the notebook tapping and sliding across the page as proof; a hand wipes across the mouth and nose, then a final open gesture, still mouthing.
  [Audio Style] No dialogue. No background music.
  [Camera & Core Constraints] Camera: static throughout. Real-time speed, nothing added, skipped, repeated or reordered, no new gesture, no extra camera move, no re-staging, no new people. Exactly one carton, closed, upright, not duplicated, not vanished, not deformed, constant in size; nothing passes through it. No subtitles, captions or other on-screen text; the only lettering is the printed label on the package.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no extra fingers, no duplicate packages, no scale drift, no slow motion, no speed ramps, no other brands, no oversized or giant carton, no carton as wide as the notebook, no carton wider than his palm, no carton closer to the camera than the notebook, no carton in the foreground, no lying or tilted carton, no carton on the notebook or on any paper, no carton touching his hand or arm, no studio lighting on the carton, no glow, no blister, no opened carton, no loose gum pieces
  ```
- **params:** model=wan3_0_prime · duration=7 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=image_references×4, video_references · request=video-22-fix-a2-request.json
- **errors:**
  ```text
  none; job 57cda53c-eb77-4f3c-a7cf-46046104735e completed, 21 credits
  ```
- **evidence:** a2 frames 0.0, 3.0, 4.0, 6.2 s in C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07/60-outputs/video-22/fix-20261012/a2/ and T scale JSON a2/scale_rest.json, scale_last.json, scale_use.json
- **qc:**
  ```text
  accepted
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261007-232745-07\40-briefs\video-22-plan.md
- **class:** anomaly-catalog.md 2.16 (support), 2.7 (size); wan-3-0.md 5 size row
- **cause:** model-limit
- **fix:** Fixed by a3: the same size-reference idea with the composite showing the carton at 0.85x true size on the free front-left corner of the table (a spot that exists in the source frame, left of the notebook) instead of beside the notebook's right edge; the carton stands on the bare grey front edge, not on the page, at 0.91-0.93x (A) / 0.90-0.91x (B).
- **verified prompt:**
  ```text
  [Core Task] Recreate Video 1 as a real phone-shot vertical clip with only these changes: the person and the product. Video 1 is the motion, camera, framing, cut and timing reference: keep every movement, gesture, head turn, gaze, expression and mouth movement of the person in Video 1 in the same order, at the same moments and at the same real-time speed, and keep the camera, framing, cuts, light, room, background and the notebook's place. Do not inherit the appearance, clothing, text, captions, usernames, watermarks or branded items of Video 1. The man corresponds to Image 1, adopting facial features, hairstyle, skin tone, build and clothing (short hair, stubble); Image 1 is only his identity, not its pose, background or objects. The man replaces the person of Video 1 and performs exactly that person's movements. The Neuro Energy & Focus gum carton (Cinnamon, 9 pieces) corresponds to Image 2 and Image 3, which jointly define one single package, adopting only its structure, material, colours and printed label: a small closed flat paperboard carton, 7.5 cm wide, 8.5 cm tall and 1.6 cm thick, light blue with wavy lighter-blue shapes, a blue N logo and Neuro wordmark top-left, an orange-red GUM badge top-right, a Cinnamon tag, the title Energy & Focus. Image 4 is a size and spot reference only: it shows this carton standing on the grey front edge of the table at the front-left corner beside the notebook of Video 1, only about one third as wide as the notebook page; use that size relation and that spot, not its framing, wall, lighting or perspective. Keep its exact shape, proportions and artwork without deformation and without scale drift; it stays closed. Video 1 has no such item, but the carton is part of this scene from the first frame: it stands upright on its base on the bare grey front edge of the table at the front-left corner, to the left of the open spiral notebook, its base level with the notebook's front edge, no nearer to the lens than the notebook, not touching or overlapping the notebook, a band of bare table between them and bare table to its left, fully inside the frame; lit by the scene's own light with a soft contact shadow, untouched and in the same place for the whole clip.
  [Plot Summary] The open spiral notebook lies at the bottom centre exactly as in Video 1, its whole page in view, about 21 cm wide; the carton at the front-left corner is small beside it: about one third as wide as the notebook page, a little narrower than the man's open palm and about one fifth of the frame width; it keeps exactly this size before and after every cut.
  Shot 1 [0-1.8s]: Static selfie framing from the table edge, a door frame behind. The carton stands at the front-left corner left of the notebook. The man sits square to the camera, leaning forward, both palms flat on the notebook with fingers tapping, head bobbing, mouth moving rapidly as if arguing, brows raised, intense eyes to the lens; the frame-right hand lifts the top page, flips it and slaps it back down; then wide sweeping open-hand gestures across the table, leaning in, mouth still talking, as the image brightens toward white; his hands and arms stay farther from the lens than the carton and never touch it.
  Shot 2 [1.8-4.1s]: Hard cut, same framing, the one carton still stands at the front-left corner: he leans back then forward, hands chopping and waving, palms-up shrugs, mouth arguing; hands come down to the notebook; the right index finger taps the temple; the arm flings out wide toward frame-right and comes back down to the notebook.
  Shot 3 [4.1-6.3s]: Hard cut, same framing, the one carton still stands at the front-left corner: hands out palms up in a shrug, a quick temple tap, an arm swing wide to frame-right; then both hands on the notebook tapping and sliding across the page as proof; a hand wipes across the mouth and nose, then a final open gesture, still mouthing.
  [Audio Style] No dialogue. No background music.
  [Camera & Core Constraints] Camera: static throughout. Real-time speed, nothing added, skipped, repeated or reordered, no new gesture, no extra camera move, no re-staging, no new people. Exactly one carton, closed, upright, not duplicated, not vanished, not deformed, constant in size; nothing passes through it. No subtitles, captions or other on-screen text; the only lettering is the printed label on the package.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no extra fingers, no duplicate packages, no scale drift, no slow motion, no speed ramps, no other brands, no oversized or giant carton, no carton as wide as the notebook, no carton wider than his palm, no carton closer to the camera than the notebook, no carton on the notebook or on any paper, no carton right of the notebook, no lying or tilted carton, no carton touching his hand or arm, no studio lighting on the carton, no glow, no blister, no opened carton, no loose gum pieces
  ```
- **prompt change:**
  ```text
  - Video 1 is the motion, camera, framing, cut and timing reference: keep every movement, gesture, head turn, gaze, expression and mouth movement of the person in Video 1 in the same order, at the same moments and at the same real-time speed, and keep the camera, framing, cuts, light, room and backgrou
  + Video 1 is the motion, camera, framing, cut and timing reference: keep every movement, gesture, head turn, gaze, expression and mouth movement of the person in Video 1 in the same order, at the same moments and at the same real-time speed, and keep the camera, framing, cuts, light, room, background 
  - Image 4 is a size reference only: it shows this carton standing on the table beside the notebook of Video 1, the carton about one third as wide as the notebook page;
  - use only that size relation, not its framing, background, lighting or perspective.
  - In Image 2 and Image 3 the carton is deliberately small in the frame and keeps that small scale.
  + Image 4 is a size and spot reference only: it shows this carton standing on the grey front edge of the table at the front-left corner beside the notebook of Video 1, only about one third as wide as the notebook page;
  + use that size relation and that spot, not its framing, wall, lighting or perspective.
  - Video 1 has no such item, but the carton is part of this scene from the first frame: it stands upright on its base on the bare table at the front edge, to the right of the open spiral notebook, its base level with the notebook's front edge, in the same plane as the notebook and no nearer to the lens
  + Video 1 has no such item, but the carton is part of this scene from the first frame: it stands upright on its base on the bare grey front edge of the table at the front-left corner, to the left of the open spiral notebook, its base level with the notebook's front edge, no nearer to the lens than the
  - [Plot Summary] The open spiral notebook lies at the bottom left of the frame, its whole page in view, about 21 cm wide;
  - the carton stands to its right and is small beside it: about one third as wide as the notebook page, a little narrower than the man's open palm and about one fifth of the frame width;
  + [Plot Summary] The open spiral notebook lies at the bottom centre exactly as in Video 1, its whole page in view, about 21 cm wide;
  + the carton at the front-left corner is small beside it: about one third as wide as the notebook page, a little narrower than the man's open palm and about one fifth of the frame width;
  - The carton stands on the table right of the notebook.
  … 9 more changed sentences
  ```
- **verified params:** model=wan3_0_prime · duration=7 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=image_references×4, video_references · request=video-22-fix-a3-request.json
- **rule:** A size-reference image that shows the product at the true ratio beside the neighbour cut the oversize from 1.7-2x to about 1.3x on wan3_0_prime, but a layout the frame cannot hold (a 9:16 frame where the neighbour already spans 70 percent of the width) is resolved by the model by putting the product on the neighbour; the reference must show the product on a spot that exists in the source frame (the free table corner), not beside a neighbour that leaves no room
- **status:** fixed
- **promoted to:** —
- **verified:** the regeneration a3 (job 4451b1c8-6e71-4eba-a843-75b1cce7441c) passed QC: carton 0.91-0.93x (A) / 0.90-0.91x (B) of its reckoned size beside the notebook, count 1 closed upright, same spot on both sides of each insert, on the bare front edge of the table; sync in_sync, original audio whole, text present (2026-10-12)

## CE-041 · 2026-10-12 · Flat pouch jammed against the writer's forearm and hand; label word Focus renders as Fccus
- **source:** agent
- **video:** 14
- **run:** C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261008-235833-08
- **delivered:** CapCut project 09_Oct_2026_v14-2 · clean C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261008-235833-08/60-outputs/video-14/clean.mp4 · credits 78 · run QC: r2 accepted (flat sachet). POSTURE/SUPPORT: lies flat on its wide face, label up, whole underside on bare marble with contact shadow, no tilt/edge/float at 30 fps (write, glance, flip, last). STORY: set down on the near table edge to the right of the writing hand, out of the way; a real person leaves a gum pack like that. Size 1.05x (5 cm width: 92-105 px vs 93 expected at 0.5 m). Count 1/1/1, sealed. Never touches the arm: 2-D marble gap 18-37 px (~0.2 hand-width; flagged, frame leaves only ~150 px under the forearm). r1 carton rejected: flat and ~1.1x but its corner sat against the forearm (gap 3-4 px) 0.5-8 s. CE-001/002/003/004/006/007/008/010/012 pass; CE-012 set fixed with the r2 prompt.
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Neuro Energy & Focus Extra Strength Peppermint 90-piece pouch (V05 recreate, CE-033 fix pass 2)
- **assets:** lying-flat pose reference (A567 front render rotated 90 deg cw, foreshortened 0.55, p40, media e677b4c0) + flat top view (A567 rotated 90 deg cw, p40, media 1a5631a9), char-K3, V05 own-silent; pouch 17.9 x 10.2 x 4.6 cm
- **user said:** — (caught by the agent during the run)
- **what was wrong:** Fix pass 2 (lying-flat references) fixed the posture: the 90-piece pouch lies flat on its front face, label up, long side left-right, top seal right (30 fps, write/glance/flip/last), size 1.08x (A vs hand back, depth ratio 0.92; B table-plane distance; agree), count 1, sealed. But (1) it was drawn about as tall as its true top view (165 px, 280 x 165) instead of foreshortened (about 90 px) and placed with its far long edge on his forearm and its left end against his hand: 0 px gap from 0.5 s to the end (the request asked for a band of marble and said so twice); (2) the label word Focus renders as Fccus for the whole clip (OCR '&Fccus' 0.00-12.00 s), a wrong-letters label (CE-032) caused by small rotated label text; fine print also garbled.
- **brief:**
  ```text
  Video 14 of 18 - Recreate of V05: Neuro XE Peppermint carton, placement on the marble table
  Concept: the reference recreated as itself (same scenario, action, camera and timing), faces swapped to the supplied character(s), the product integrated (placement on the marble table).
  Why it works: Communicates: "what teachers think would happen if they let us listen to music in an exam" - the VO reads answers like a track; deadpan. Why Neuro: students under sustained mental load (A456 sec 4), calm and wry (G24), the product 'just happens to be there' (G23). Kept [E]: the take, the VO, writing, the page flip. Goal/job [I]: awareness; the carton on the marble, noticed; share line "this is why we can't have music". Adapted: man -> K3; the caption box and shirt print removed from the plate; the package is Extra Strength Peppermint, closed (hero per G18, form per G27).
  Reference pattern: V05 (see 20-analysis/cards/V05.md and families.md)
  Characters/assets: see the plan sec 2.3; Higgsfield media ids in 30-assets/uploads.json and the request file.
  Substitutions: Placement; the closed hardcover notebook (a solid, not a sheet hands move: CE-006) is the smallest native element that lets a 1.6 cm-thick carton stand readable; hands busy: no use beat (G19/G27 satisfied: no piece is taken).
  Counts & use: | entity | count | state |
  |---|---|---|
  | carton | 1 | upright on its long edge, propped against a closed hardcover notebook on the bare marble, lower right, ~0.6 m, closed, label 30 deg; never moved |
  | sheets | 1-2 | flipped at 9.2-10.4 over the left edge, away from the carton |
  Size: Carton 7.5 cm at ~0.6 m, 26 mm eq -> ~9.0% (~116 px) (T scale --product-cm 7.5 --distance 0.6 --lens 26); neighbour: the exam sheet (29.7 cm) -> ~0.25 of its length; his palm is ~8.5 cm wide, the carton 7.2 cm wide -> slightly narrower than his palm. Oversize check: a carton taller than ~0.4 of the sheet is a regenerate reason.
  Guardrails: G16 (the client's real renders are the only product references; no AI-invented packaging: QC compares the label geometry and any morphed text is a regenerate reason), G17/G18 (Extra Strength, Peppermint or Spearmint, 9-piece carton, closed; the 6-pack box never appears), G19/G27 (closed package, nobody takes a piece, no blister shown), G23/G24 (the product just happens to be there; calm, wry register), G25 [U] (no sleeping/drained scene), G11/G21 (no numbers or claims in any text layer; the carton's own 100MG band is the only number), G12 (no competitor shown or replaced), G13/G14 (an adult supplied character, no ambassador likeness), G22 (phone-shot, everything in focus).
  Caught errors applied: CE-006 (a product is never placed on or overlapping paper: bare surface or a solid prop; sheets stay flat; QC densifies the contact region for the whole shot), CE-007 (small closed carton by default in casual scenes; the pouch only where a large pack fits; a placed product never takes over the source's pick-up beat: the object picked up is named and the product stays), CE-008 (adult framing in captions and casting), CE-010 (text centred), CE-001 (the package count stays 1; nothing taken), CE-002
  Text: CapCut layer as in the scene.
  Inserts: none.
  Sound: Original VO audio restored.
  Fidelity approach: the silent own-content source as video_references (the most preserving input Wan 3.0 Prime offers: recreate-from-video-reference), exact duration rounded up, fidelity lock + the action script written out in the prompt; risks to fidelity or sync: lip-sync and exact timing are not guaranteed by this model; sync-check after the merge.
  Model & operation: video-14-request.json: wan3_0_prime reference-to-video, 13 s, 9:16 720p, generate_audio false, 4 media - est. 39 credits (3 credits/s, preflight read: no adjustments)
  Adaptation logic: One generation of 13 s (own 12.07 s). Credits 39. No inserts.
  
  ## Redo (CE-012, 2026-10-09)
  r1: closed XE Peppermint carton lying flat label up on the bare near-camera marble, lower right (50-requests/video-14-r1-request.json, p40 refs 36960471/2bc3de47) - flat and ~1.1x but against the forearm; r2: flat-lying single Energy & Focus Peppermint sachet on the same strip, band of marble to the forearm (50-requests/video-14-r2-request.json) - delivered. Action script and fidelity lock unchanged. CapCut project 09_Oct_2026_v14-2.
  
  ## Client fix 2026-10-12 (CE-033), attempt fix1 (ledger 14-fix attempt 4)
  Concept unchanged (V05 exam scene, same man K3, caption, original audio, sync anchors). Change: the product is the Neuro Energy & Focus Extra Strength Peppermint 90-piece POUCH (17.9 x 10.2 x 4.6 cm), sealed, lying flat on its front face, label up, long side left-right on the near-camera bare marble strip below the forearm, top seal to the right, count 1; plan: 40-briefs/video-14-fix-plan-20261012.md.
  Why: the client read the delivered sachet as box-sized ("the bag is bigger than the boxes"); the delivered 1.05x had rested on an assumed 0.5 m, the frame puts the strip at about 0.6 m (sachet 1.2-1.35x). Size ladder: pouch 17.9 : carton 7.5 : sachet 7 cm (2.4 : 1 : 0.93).
  Reference pattern: V05; fidelity lock and action script as delivered (r2 request structure); request 50-requests/video-14-fix1-request.json: wan3_0_prime reference-to-video, 13 s 9:16 720p, generate_audio false, enable_thinking true, 4 media (Video 1 own-silent, Image 1 K3, Image 2 pouch front A567 p40, Image 3 pouch left A568 p40), new-account media ids (30-assets/uploads-fix-14.json), no folder_id; 4920 chars; preflight 39 credits, no adjustments (preset recommendation declined).
  Size: pouch at 0.6 m (distance from the frame: hand back 160 px = 10.5 cm, A4 sheet 21 cm = 285 px -> hands 0.65-0.68 m; table plane: strip 0.56-0.62 m), f 26 mm eq: long side 276 px (38 % of the frame width), short side about 83 px of frame height (157 x 0.53 foreshortening); hand 18 cm = 245 px at 0.68 m. Accept within 25 % by A (hand, depth ratio from the frame) and B (derived distance); check both too small (client's miss) and too big.
  Posture/support/place/story: lies flat, label up, bare marble only, band of marble to the forearm and below it, not touching the arm or sheets; he set it down on the near edge out of the pen hand's way. Object picked up: the exam sheet (flip 9.2-10.4); the pouch stays.
  Risks: the model may stand the pouch up (reference shows it upright), inflate it, or cross the forearm; levers for attempt 2 are in the plan (pose reference / anchor depth), not sizing words. Text layer: caption posX 0, posY 0.66 in CapCut, house style, no emoji. Credits cap 3 x 39.
  
  ## Client fix 2026-10-12 (CE-033), attempt fix2 (ledger 14-fix attempt 5) - lever: references
  fix1 (job d19013be, 39 credits) REJECTED, recorded as CE-037: the pouch rendered STANDING on its gusset in front of his hand and forearm from frame 0 to the end (left edge about 5 px from the hand); size 1.11x by A (his hand back, depth ratio 0.93) and B (table-plane distance 0.607 m), count 1, sealed, "Neuro" and "Energy & Focus" legible, the 100MG band garbled. Cause: upright client renders as references plus "lies flat" wording.
  fix2 changes only the reference lever (never the sizing words): Image 2 = a lying-flat pose reference (the client's A567 front render, rotated 90 degrees clockwise so the top seal points right, foreshortened 0.55, soft shadow, p40, by pure geometric transform in 60-outputs/video-14/fix-20261012/make_request... refs/make_pose_refs.py), Image 3 = the same render rotated 90 degrees clockwise, top view (label at full resolution), p40; no upright reference; the prompt calls it "a gum pouch ... flat like an envelope" (not stand-up) and binds how it lies to Image 2. Request 50-requests/video-14-fix2-request.json, 4916 chars, preflight 39 credits, no adjustments. Everything else as fix1.
  ```
- **prompt:**
  ```text
  [Core Task] Generate single shot. The man corresponds to Image 1, adopting only his facial features and hairstyle and light stubble; man replaces only the person in Video 1 and keeps the plain white t-shirt without lettering and the white over-ear headphones; do not use the background, props or clothing of Image 1. His face, neck, hands and forearms share one consistent skin tone as in Image 1. Use Video 1 for his movements, expressions, gaze, the camera framing, the room, the exam sheets and the timing. The pouch corresponds to Images 2 and 3, which jointly define the same entity, and generates only one instance, adopting only its structure, material, colours, printed label and how it lies: Image 2 shows it lying flat on its front face with the label up and the top seal to the right, Image 3 shows its label from directly above (a closed, sealed gum pouch about 18 cm long and 10 cm wide, flat like an envelope, of sky-blue matte foil with a zipper strip under a flat top seal, the dark-blue Neuro wordmark, a mint and navy EXTRA STRENGTH GUM badge, a Peppermint tag, 'Energy & Focus' in large navy type, '90 Pieces Dietary Supplement' and a navy band along the bottom); the pouch keeps its real size; do not use the lighting, exposure, background, shadow or camera angle of Images 2 and 3.
  [Plot Summary] Locked phone camera at eye level, medium shot, a white marble table filling the lower third, a bright room corner with a white door and warm lamp light from the upper left. He sits turned about forty degrees toward the left of the frame with his head tilted left, listening to his headphones, a blue pen in his right hand resting on an exam sheet and his left hand flat on the table; he turns his head down to the sheet and squares his torso; he writes with small right-hand strokes, glancing up and to the left once, and keeps writing; then both hands lift the right edge of the sheet and flip it over to the left, his left hand smoothing it down, and it lands on the same spot; he writes again with a glance to the right of the frame. A single closed sealed Neuro Energy & Focus Extra Strength Peppermint pouch lies flat on its front face with its printed label facing up, its top seal pointing to the right of the frame so that the label reads sideways, resting entirely on the bare white marble in the lower middle of the frame, on the near side of the table, nearer the lens than his hands and forearm, where someone sets a pouch of gum down out of the way of their writing. It is fully inside the frame, with a visible band of bare marble between it and his forearm and hands and another below it; nothing touches it and nobody picks it up. It is about sixty centimetres from the lens and true to its real size, about as long as his hand from wrist to fingertip and a little wider than his open palm, its long side spanning about two fifths of the frame width and its short side about one fifteenth of the frame height as it lies, seen from above at a slight angle as a flat plump rectangle, lit by the same warm lamp light with a soft contact shadow on the marble falling to the right like the sheets' shadows; it stays flat on that spot for the whole clip and never slides, tilts, stands up or leans, the exam sheets lie flat except when he flips the top one, and the flipped sheet stays on the left and never reaches the pouch. Phone-shot look, everything in focus. Real-time speed. No dialogue. No background music.
  [Camera & Core Constraints] Keep every movement, gesture, expression, gaze and mouth movement of the person in Video 1 on the same frames, the props and how they are handled, the camera framing, the light, the room and the timing of Video 1 unchanged; no added, skipped, repeated or reordered action, no new gesture, no extra camera move, no re-staging, no new people, no change of pace. There is exactly one pouch, constant and true to its real size, lying flat, sealed with its zipper closed and never opened, not duplicated, not vanished, not deformed, no scale drift; nothing passes through it. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen; the only lettering is the printed label on the Neuro pouch, exactly as in Images 2 and 3; do not reproduce any text, captions, usernames or watermarks from Video 1.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no slow motion, no self-inserted cut points, no added or skipped action, no face lighter or darker than the hands, no pouch much longer than his hand, no standing, upright, leaning, propped, folded or tilted pouch, no pouch on its base or on its edge, no pouch on a sheet, no pouch touching his arm or hand, no notebook, no carton, no sachet, no six-pack box, no blister card, no opened pouch, no torn top, no gum in anyone's mouth, no chewing, no glow, no white caption box, no text on the shirt
  ```
- **params:** model=wan3_0_prime · duration=13 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=video_references, image_references×3 · request=video-14-fix2-request.json
- **errors:**
  ```text
  none: job fe6a0281 completed, 39 credits, no adjustments
  ```
- **evidence:** fix-20261012/a5/crop6.png and a5/crop98.png (full-resolution crops at 6.0 s and 9.8 s), a5/qc/dense/sheet-03-flip-01.jpg (30 fps), a5/qc/qc.json (OCR: &Fccus 0.00-12.00 s), a5/scale-6.0.json
- **qc:**
  ```text
  r2 accepted (flat sachet). POSTURE/SUPPORT: lies flat on its wide face, label up, whole underside on bare marble with contact shadow, no tilt/edge/float at 30 fps (write, glance, flip, last). STORY: set down on the near table edge to the right of the writing hand, out of the way; a real person leaves a gum pack like that. Size 1.05x (5 cm width: 92-105 px vs 93 expected at 0.5 m). Count 1/1/1, sealed. Never touches the arm: 2-D marble gap 18-37 px (~0.2 hand-width; flagged, frame leaves only ~150 px under the forearm). r1 carton rejected: flat and ~1.1x but its corner sat against the forearm (gap 3-4 px) 0.5-8 s. CE-001/002/003/004/006/007/008/010/012 pass; CE-012 set fixed with the r2 prompt.
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261008-235833-08\40-briefs\video-14-plan.md
- **class:** anomaly-catalog.md §2.16 (clearance to a working hand or arm) and §2.7 (perspective of a flat pack); CE-032 (label must read)
- **cause:** reference
- **fix:** none yet
- **verified prompt:** pending (inserted only after a new generation passes QC)
- **rule:** A flat-lying pack needs a pose reference that carries the camera's foreshortening and only that (a top-view reference teaches a top-down footprint far taller than the table strip allows and the pack ends up against the arm); positions in words (a band to the arm) are not honoured, the reference and the placed spot are the levers. A label rotated a quarter turn and foreshortened gets fewer legible pixels: tight-cropped label detail in the reference and fewer label words in the prompt, and QC reads the wordmark and the main line word by word.
- **status:** open
- **promoted to:** —

## CE-042 · 2026-10-12 · Neuro wordmark renders as Nero on a pouch lying a quarter turn and foreshortened, although the layout reference carries it exactly
- **source:** agent
- **video:** 14
- **run:** C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261008-235833-08
- **delivered:** CapCut project 09_Oct_2026_v14-2 · clean C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261008-235833-08/60-outputs/video-14/clean.mp4 · credits 78 · run QC: r2 accepted (flat sachet). POSTURE/SUPPORT: lies flat on its wide face, label up, whole underside on bare marble with contact shadow, no tilt/edge/float at 30 fps (write, glance, flip, last). STORY: set down on the near table edge to the right of the writing hand, out of the way; a real person leaves a gum pack like that. Size 1.05x (5 cm width: 92-105 px vs 93 expected at 0.5 m). Count 1/1/1, sealed. Never touches the arm: 2-D marble gap 18-37 px (~0.2 hand-width; flagged, frame leaves only ~150 px under the forearm). r1 carton rejected: flat and ~1.1x but its corner sat against the forearm (gap 3-4 px) 0.5-8 s. CE-001/002/003/004/006/007/008/010/012 pass; CE-012 set fixed with the r2 prompt.
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Neuro Energy & Focus Extra Strength Peppermint 90-piece pouch (V05 recreate, CE-033 fix pass 3, last allowed generation)
- **assets:** layout reference 720x1280 (delivered r2 frame, sachet inpainted, A567 front render composited flat: rotated 90 deg cw, table-plane perspective at 0.57-0.67 m, soft contact shadow; media e1468cc1), char-K3 (media 9e7ce7cb), V05 own-silent (media 84637256); pouch 17.9 x 10.2 x 4.6 cm
- **user said:** — (caught by the agent during the run)
- **what was wrong:** Fix pass 3 (layout reference) fixed posture, place and size: the 90-piece pouch lies flat, label up, long side left-right, top seal right, low in the lower middle, in frame from 0.0 s, min 2-D distance to his hand or forearm 25 px (median about 31 px, never touching), size A 1.10x / B 1.05x at rest (1.12x by the tool with the 0.63 m table-plane distance), 0.94x in the flip, 1.07x at the end, 2.6x a carton's width at that depth, sheets never reach it, in sync, original audio stream-copied. It fails the label check: the Energy & Focus line is exact but the Neuro wordmark reads Nero / Nerro (the u is lost) in every sampled frame, the Peppermint tag and GUM badge are smudged (GLM) and the fine print is wrong letters, although the reference carried the label crisply at the target pixel size (wordmark about 14 px tall, 36 px long, rotated 90 degrees and foreshortened by 0.53). Extra notes: the pouch is a flat zero-thickness envelope with hard clean edges and a hard dark contact edge (paste signs 5/8), brighter and more saturated than the marble.
- **brief:**
  ```text
  Video 14 of 18 - Recreate of V05: Neuro XE Peppermint carton, placement on the marble table
  Concept: the reference recreated as itself (same scenario, action, camera and timing), faces swapped to the supplied character(s), the product integrated (placement on the marble table).
  Why it works: Communicates: "what teachers think would happen if they let us listen to music in an exam" - the VO reads answers like a track; deadpan. Why Neuro: students under sustained mental load (A456 sec 4), calm and wry (G24), the product 'just happens to be there' (G23). Kept [E]: the take, the VO, writing, the page flip. Goal/job [I]: awareness; the carton on the marble, noticed; share line "this is why we can't have music". Adapted: man -> K3; the caption box and shirt print removed from the plate; the package is Extra Strength Peppermint, closed (hero per G18, form per G27).
  Reference pattern: V05 (see 20-analysis/cards/V05.md and families.md)
  Characters/assets: see the plan sec 2.3; Higgsfield media ids in 30-assets/uploads.json and the request file.
  Substitutions: Placement; the closed hardcover notebook (a solid, not a sheet hands move: CE-006) is the smallest native element that lets a 1.6 cm-thick carton stand readable; hands busy: no use beat (G19/G27 satisfied: no piece is taken).
  Counts & use: | entity | count | state |
  |---|---|---|
  | carton | 1 | upright on its long edge, propped against a closed hardcover notebook on the bare marble, lower right, ~0.6 m, closed, label 30 deg; never moved |
  | sheets | 1-2 | flipped at 9.2-10.4 over the left edge, away from the carton |
  Size: Carton 7.5 cm at ~0.6 m, 26 mm eq -> ~9.0% (~116 px) (T scale --product-cm 7.5 --distance 0.6 --lens 26); neighbour: the exam sheet (29.7 cm) -> ~0.25 of its length; his palm is ~8.5 cm wide, the carton 7.2 cm wide -> slightly narrower than his palm. Oversize check: a carton taller than ~0.4 of the sheet is a regenerate reason.
  Guardrails: G16 (the client's real renders are the only product references; no AI-invented packaging: QC compares the label geometry and any morphed text is a regenerate reason), G17/G18 (Extra Strength, Peppermint or Spearmint, 9-piece carton, closed; the 6-pack box never appears), G19/G27 (closed package, nobody takes a piece, no blister shown), G23/G24 (the product just happens to be there; calm, wry register), G25 [U] (no sleeping/drained scene), G11/G21 (no numbers or claims in any text layer; the carton's own 100MG band is the only number), G12 (no competitor shown or replaced), G13/G14 (an adult supplied character, no ambassador likeness), G22 (phone-shot, everything in focus).
  Caught errors applied: CE-006 (a product is never placed on or overlapping paper: bare surface or a solid prop; sheets stay flat; QC densifies the contact region for the whole shot), CE-007 (small closed carton by default in casual scenes; the pouch only where a large pack fits; a placed product never takes over the source's pick-up beat: the object picked up is named and the product stays), CE-008 (adult framing in captions and casting), CE-010 (text centred), CE-001 (the package count stays 1; nothing taken), CE-002
  Text: CapCut layer as in the scene.
  Inserts: none.
  Sound: Original VO audio restored.
  Fidelity approach: the silent own-content source as video_references (the most preserving input Wan 3.0 Prime offers: recreate-from-video-reference), exact duration rounded up, fidelity lock + the action script written out in the prompt; risks to fidelity or sync: lip-sync and exact timing are not guaranteed by this model; sync-check after the merge.
  Model & operation: video-14-request.json: wan3_0_prime reference-to-video, 13 s, 9:16 720p, generate_audio false, 4 media - est. 39 credits (3 credits/s, preflight read: no adjustments)
  Adaptation logic: One generation of 13 s (own 12.07 s). Credits 39. No inserts.
  
  ## Redo (CE-012, 2026-10-09)
  r1: closed XE Peppermint carton lying flat label up on the bare near-camera marble, lower right (50-requests/video-14-r1-request.json, p40 refs 36960471/2bc3de47) - flat and ~1.1x but against the forearm; r2: flat-lying single Energy & Focus Peppermint sachet on the same strip, band of marble to the forearm (50-requests/video-14-r2-request.json) - delivered. Action script and fidelity lock unchanged. CapCut project 09_Oct_2026_v14-2.
  
  ## Client fix 2026-10-12 (CE-033), attempt fix1 (ledger 14-fix attempt 4)
  Concept unchanged (V05 exam scene, same man K3, caption, original audio, sync anchors). Change: the product is the Neuro Energy & Focus Extra Strength Peppermint 90-piece POUCH (17.9 x 10.2 x 4.6 cm), sealed, lying flat on its front face, label up, long side left-right on the near-camera bare marble strip below the forearm, top seal to the right, count 1; plan: 40-briefs/video-14-fix-plan-20261012.md.
  Why: the client read the delivered sachet as box-sized ("the bag is bigger than the boxes"); the delivered 1.05x had rested on an assumed 0.5 m, the frame puts the strip at about 0.6 m (sachet 1.2-1.35x). Size ladder: pouch 17.9 : carton 7.5 : sachet 7 cm (2.4 : 1 : 0.93).
  Reference pattern: V05; fidelity lock and action script as delivered (r2 request structure); request 50-requests/video-14-fix1-request.json: wan3_0_prime reference-to-video, 13 s 9:16 720p, generate_audio false, enable_thinking true, 4 media (Video 1 own-silent, Image 1 K3, Image 2 pouch front A567 p40, Image 3 pouch left A568 p40), new-account media ids (30-assets/uploads-fix-14.json), no folder_id; 4920 chars; preflight 39 credits, no adjustments (preset recommendation declined).
  Size: pouch at 0.6 m (distance from the frame: hand back 160 px = 10.5 cm, A4 sheet 21 cm = 285 px -> hands 0.65-0.68 m; table plane: strip 0.56-0.62 m), f 26 mm eq: long side 276 px (38 % of the frame width), short side about 83 px of frame height (157 x 0.53 foreshortening); hand 18 cm = 245 px at 0.68 m. Accept within 25 % by A (hand, depth ratio from the frame) and B (derived distance); check both too small (client's miss) and too big.
  Posture/support/place/story: lies flat, label up, bare marble only, band of marble to the forearm and below it, not touching the arm or sheets; he set it down on the near edge out of the pen hand's way. Object picked up: the exam sheet (flip 9.2-10.4); the pouch stays.
  Risks: the model may stand the pouch up (reference shows it upright), inflate it, or cross the forearm; levers for attempt 2 are in the plan (pose reference / anchor depth), not sizing words. Text layer: caption posX 0, posY 0.66 in CapCut, house style, no emoji. Credits cap 3 x 39.
  
  ## Client fix 2026-10-12 (CE-033), attempt fix2 (ledger 14-fix attempt 5) - lever: references
  fix1 (job d19013be, 39 credits) REJECTED, recorded as CE-037: the pouch rendered STANDING on its gusset in front of his hand and forearm from frame 0 to the end (left edge about 5 px from the hand); size 1.11x by A (his hand back, depth ratio 0.93) and B (table-plane distance 0.607 m), count 1, sealed, "Neuro" and "Energy & Focus" legible, the 100MG band garbled. Cause: upright client renders as references plus "lies flat" wording.
  fix2 changes only the reference lever (never the sizing words): Image 2 = a lying-flat pose reference (the client's A567 front render, rotated 90 degrees clockwise so the top seal points right, foreshortened 0.55, soft shadow, p40, by pure geometric transform in 60-outputs/video-14/fix-20261012/make_request... refs/make_pose_refs.py), Image 3 = the same render rotated 90 degrees clockwise, top view (label at full resolution), p40; no upright reference; the prompt calls it "a gum pouch ... flat like an envelope" (not stand-up) and binds how it lies to Image 2. Request 50-requests/video-14-fix2-request.json, 4916 chars, preflight 39 credits, no adjustments. Everything else as fix1.
  
  ## Client fix 2026-10-12 (CE-033), attempt fix3 (ledger 14-fix attempt 6) - lever: a layout reference (last of the 3 allowed)
  fix2 (job fe6a0281, 39 credits) REJECTED, recorded as CE-041: posture fixed (lies flat, label up, long side left-right, top seal right, size 1.08x by A and B) but it was drawn as tall as its top view (280 x 165 px) and sat with its far long edge on his forearm and its left end against his hand (0 px gap, 0.5 s to the end), and the label word Focus rendered as Fccus for the whole clip (OCR '&Fccus' 0.00-12.00 s). Words about a band of marble were not honoured twice.
  fix3 changes the reference lever again: Image 2 is a 720x1280 layout reference built from the delivered r2 frame at 6 s (sachet inpainted away) with the client's A567 pouch render (cut out, rotated 90 degrees clockwise, perspective of the table plane at 0.57-0.67 m, soft contact shadow, slightly warm grade) lying flat low in the lower middle: near edge y 1248, far edge y 1156, x 320-610 near / 342-588 far; band of bare marble to the forearm, clear of his left hand, 25 px margin to the bottom edge (60-90 px of marble to the forearm at x > 400). The label is therefore present at its target pixel size. No upright reference, no top view. Prompt: "Image 2 is a layout reference of this same table scene: the pouch is copied from the pouch in Image 2" (position, posture, size, spacing, label), "use nothing else from Image 2"; 4781 chars; preflight 39 credits, no adjustments. Spend after this attempt: 117 of 117 credits (cap reached).
  ```
- **prompt:**
  ```text
  [Core Task] Generate single shot. The man corresponds to Image 1, adopting only his facial features and hairstyle and light stubble; man replaces only the person in Video 1 and keeps the plain white t-shirt without lettering and the white over-ear headphones; do not use the background, props or clothing of Image 1. His face, neck, hands and forearms share one consistent skin tone as in Image 1. Use Video 1 for his movements, expressions, gaze, the camera framing, the room, the exam sheets and the timing. Image 2 is a layout reference of this same table scene: the pouch is copied from the pouch in Image 2, adopting its position on the table, its posture, its size, its spacing from his forearm and left hand, its structure, material, colours and printed label (a closed, sealed gum pouch about 18 cm long and 10 cm wide, flat like an envelope, of sky-blue matte foil with a zipper strip under a flat top seal, the dark-blue Neuro wordmark, a mint and navy EXTRA STRENGTH GUM badge, a Peppermint tag, 'Energy & Focus' in large navy type and a navy band along the bottom); it generates only one instance and keeps its real size; use nothing else from Image 2.
  [Plot Summary] Locked phone camera at eye level, medium shot, a white marble table filling the lower third, a bright room corner with a white door and warm lamp light from the upper left. He sits turned about forty degrees toward the left of the frame with his head tilted left, listening to his headphones, a blue pen in his right hand resting on an exam sheet and his left hand flat on the table; he turns his head down to the sheet and squares his torso; he writes with small right-hand strokes, glancing up and to the left once, and keeps writing; then both hands lift the right edge of the sheet and flip it over to the left, his left hand smoothing it down, and it lands on the same spot; he writes again with a glance to the right of the frame. A single closed sealed Neuro Energy & Focus Extra Strength Peppermint pouch lies flat on its front face with its printed label facing up, its top seal pointing to the right of the frame so that the label reads sideways, exactly as in Image 2, resting entirely on the bare white marble low in the lower middle of the frame, on the near side of the table, nearer the lens than his hands and forearm, with a narrow strip of marble below it and a clear band of bare marble between it and his forearm, well clear of his left hand, where someone sets a pouch of gum down out of the way of their writing; nothing touches it and nobody picks it up. It is about sixty centimetres from the lens and true to its real size, about as long as his hand from wrist to fingertip, its long side spanning two fifths of the frame width and its short side, foreshortened by the shallow viewing angle, about one fifteenth of the frame height; it is lit by the same warm lamp light with a soft contact shadow on the marble falling to the right like the sheets' shadows; it stays flat on that exact spot of the table for the whole clip and never slides, tilts, stands up or leans, the exam sheets lie flat except when he flips the top one, and the flipped sheet stays on the left and never reaches the pouch. Phone-shot look, everything in focus. Real-time speed. No dialogue. No background music.
  [Camera & Core Constraints] Keep every movement, gesture, expression, gaze and mouth movement of the person in Video 1 on the same frames, the props and how they are handled, the camera framing, the light, the room and the timing of Video 1 unchanged; no added, skipped, repeated or reordered action, no new gesture, no extra camera move, no re-staging, no new people, no change of pace. There is exactly one pouch, constant and true to its real size, lying flat, sealed with its zipper closed and never opened, not duplicated, not vanished, not deformed, no scale drift; nothing passes through it. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen; the only lettering is the printed label on the Neuro pouch, exactly as in Image 2; do not reproduce any text, captions, usernames or watermarks from Video 1.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no slow motion, no self-inserted cut points, no added or skipped action, no face lighter or darker than the hands, no pouch much longer than his hand, no standing, upright, leaning, propped, folded or tilted pouch, no pouch on its base or on its edge, no pouch on a sheet, no pouch touching, tucked under or against his arm or hand, no notebook, no carton, no sachet, no six-pack box, no blister card, no opened pouch, no torn top, no gum in anyone's mouth, no chewing, no glow, no white caption box, no text on the shirt
  ```
- **params:** model=wan3_0_prime · duration=13 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=video_references, image_references×2 · request=video-14-fix3-request.json
- **errors:**
  ```text
  none: job aca0b58c completed, 39 credits, no adjustments
  ```
- **evidence:** fix-20261012/a6/measure/wordmark_strip.png (rotated label crops at 0, 3, 9, 12 s), a6/crop6.png, a6/label6.png, a6/measure/measure.json (OCR: Energy and Focus 17 of 18 samples, wordmark read as WNero/WNemo/WNaro, never Neuro), a6/qc/dense sheets, a6/gap.json
- **qc:**
  ```text
  r2 accepted (flat sachet). POSTURE/SUPPORT: lies flat on its wide face, label up, whole underside on bare marble with contact shadow, no tilt/edge/float at 30 fps (write, glance, flip, last). STORY: set down on the near table edge to the right of the writing hand, out of the way; a real person leaves a gum pack like that. Size 1.05x (5 cm width: 92-105 px vs 93 expected at 0.5 m). Count 1/1/1, sealed. Never touches the arm: 2-D marble gap 18-37 px (~0.2 hand-width; flagged, frame leaves only ~150 px under the forearm). r1 carton rejected: flat and ~1.1x but its corner sat against the forearm (gap 3-4 px) 0.5-8 s. CE-001/002/003/004/006/007/008/010/012 pass; CE-012 set fixed with the r2 prompt.
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261008-235833-08\40-briefs\video-14-plan.md
- **class:** CE-032 (label must read); wan-3-0.md §3.11 (text reliability); anomaly-catalog.md §2.15 (blend)
- **cause:** model-limit
- **fix:** none yet
- **verified prompt:** pending (inserted only after a new generation passes QC)
- **rule:** A label word that must read, rendered at about 14 px, rotated a quarter turn and foreshortened, falls below what wan3_0_prime redraws exactly even when a layout reference carries it correctly; large type survives (Energy & Focus), small wordmarks and badges do not. The plan must choose the posture and place that gives the wordmark at least about 25 px of upright height (held, standing frontal, or nearer) or record the limit before generation; a layout reference (the client's render composited at the target place, scale and perspective into a frame of this same scene) is the lever that fixes place, posture, size and spacing in one generation and should be tried first for any placed pack. Do not accept a take on 'the main line reads' when the wordmark does not.
- **status:** open
- **promoted to:** —

## CE-043 · 2026-10-12 · Placed carton looks fake underneath: floats on the table edge and its lighting does not match the scene
- **source:** user
- **video:** 22
- **run:** 20261007-232745-07
- **delivered:** CapCut project 12_Oct_2026_v22 · clean client-fixes-20261012/run07-video-22-fixed-clean.mp4 · credits 63 (3 generations) · run QC: accepted
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Neuro Energy & Focus Cinnamon 9-piece carton (V16 recreate, client-fix pass, front-left table corner)
- **assets:** Neuro Energy & Focus Cinnamon 9-piece carton (Images 2-3, orange-red GUM badge); A09 character; V16 own source; fix-pass layout composite in 60-outputs/video-22/fix-20261012/refs
- **user said:** "run07-video-22-fixed-preview.mp4 is not correct because the neurogum package looks a bit fake underneath (like it is floating and lightning doest match too [screenshot with a red arrow at the carton's base on the dark grey strip below the wooden tabletop])"
- **what was wrong:** The fix pass for CE-034 solved the size (0.9x) by compositing a scale-reference render of the carton onto the layout reference and placing it on the dark grey steel front band beside the notebook. On the delivered frame (crop of the base at 3x, t 1.0 s) the carton's bottom edge is a clean hard line with only a hairline of dark under it: no cast shadow on the steel in the direction of the room light, no reflection or darkening where a box meets a polished metal surface, and the box is evenly bright, saturated cyan with no warm cast, no ambient colour from the grey table and none of the footage's phone-video softness, while the scene (man, wall, notebook) is warm, dim and low-contrast. It sits exactly on the seam between the wood top and the steel band, which reads as hovering in front of the table. The QC of the fix pass checked size, count, posture, label and sync and wrote 'contact shadow' as a pass without a close crop at 3x or a colour/lighting comparison with the neighbour (notebook paper, skin). The agent's own lever note says the layout composite fixed place and size; it carried the pasted look into the generation, the same pattern the agent flagged on the video-14 candidate (flat envelope, hard edges).
- **brief:**
  ```text
  Video 22 of 22 — NEUROGUM — Recreate V16
  Concept: V16 recreated beat for beat with character A09 and the Neuro Energy & Focus gum carton (Cinnamon, 9 pieces).
  Reference pattern: V16 card (timing, beats, inserts at 1.80-4.40, 6.70-9.30).
  Characters/assets: A09 (Image 1); A709.jpg, A708.jpg.
  House approach: none (no examples).
  Substitutions: creator → A09 | Placement: stands upright at the front-right corner of the table, outside the sweep of the hands, label toward the lens, in the same spot in every shot.
  Main action & states: source beats unchanged; product untouched and persistent.
  Style & camera: as V16, static phone camera, the source's light.
  Text: CapCut layers in the house style, reference wording/positions (see plan).
  Inserts: V16 1.80-4.40, V16 6.70-9.30.
  Sound: original audio restored; inserts with their own sound.
  Model & operation: wan3_0_prime reference-to-video (≈ recreate from Video 1), 7 s → trim 6.300 s, 9:16 720p, audio off, thinking on · est. 21 credits
  Fidelity: Video 1 = silent own content (motion/camera/timing), action script written out in order, keep-list + exclusions, same duration; sync-check after the merge. Risk: low.
  Adaptation logic: product placed at the analysed anchor; source branding dropped.
  ```
- **prompt:**
  ```text
  [Core Task] Recreate Video 1 as a real phone-shot vertical clip with only these changes: the person and the product. Video 1 is the motion, camera, framing, cut and timing reference: keep every movement, gesture, head turn, gaze, expression and mouth movement of the person in Video 1 in the same order, at the same moments and at the same real-time speed, and keep the camera, framing, cuts, light, room, background and the notebook's place. Do not inherit the appearance, clothing, text, captions, usernames, watermarks or branded items of Video 1. The man corresponds to Image 1, adopting facial features, hairstyle, skin tone, build and clothing (short hair, stubble); Image 1 is only his identity, not its pose, background or objects. The man replaces the person of Video 1 and performs exactly that person's movements. The Neuro Energy & Focus gum carton (Cinnamon, 9 pieces) corresponds to Image 2 and Image 3, which jointly define one single package, adopting only its structure, material, colours and printed label: a small closed flat paperboard carton, 7.5 cm wide, 8.5 cm tall and 1.6 cm thick, light blue with wavy lighter-blue shapes, a blue N logo and Neuro wordmark top-left, an orange-red GUM badge top-right, a Cinnamon tag, the title Energy & Focus. Image 4 is a size and spot reference only: it shows this carton standing on the grey front edge of the table at the front-left corner beside the notebook of Video 1, only about one third as wide as the notebook page; use that size relation and that spot, not its framing, wall, lighting or perspective. Keep its exact shape, proportions and artwork without deformation and without scale drift; it stays closed. Video 1 has no such item, but the carton is part of this scene from the first frame: it stands upright on its base on the bare grey front edge of the table at the front-left corner, to the left of the open spiral notebook, its base level with the notebook's front edge, no nearer to the lens than the notebook, not touching or overlapping the notebook, a band of bare table between them and bare table to its left, fully inside the frame; lit by the scene's own light with a soft contact shadow, untouched and in the same place for the whole clip.
  [Plot Summary] The open spiral notebook lies at the bottom centre exactly as in Video 1, its whole page in view, about 21 cm wide; the carton at the front-left corner is small beside it: about one third as wide as the notebook page, a little narrower than the man's open palm and about one fifth of the frame width; it keeps exactly this size before and after every cut.
  Shot 1 [0-1.8s]: Static selfie framing from the table edge, a door frame behind. The carton stands at the front-left corner left of the notebook. The man sits square to the camera, leaning forward, both palms flat on the notebook with fingers tapping, head bobbing, mouth moving rapidly as if arguing, brows raised, intense eyes to the lens; the frame-right hand lifts the top page, flips it and slaps it back down; then wide sweeping open-hand gestures across the table, leaning in, mouth still talking, as the image brightens toward white; his hands and arms stay farther from the lens than the carton and never touch it.
  Shot 2 [1.8-4.1s]: Hard cut, same framing, the one carton still stands at the front-left corner: he leans back then forward, hands chopping and waving, palms-up shrugs, mouth arguing; hands come down to the notebook; the right index finger taps the temple; the arm flings out wide toward frame-right and comes back down to the notebook.
  Shot 3 [4.1-6.3s]: Hard cut, same framing, the one carton still stands at the front-left corner: hands out palms up in a shrug, a quick temple tap, an arm swing wide to frame-right; then both hands on the notebook tapping and sliding across the page as proof; a hand wipes across the mouth and nose, then a final open gesture, still mouthing.
  [Audio Style] No dialogue. No background music.
  [Camera & Core Constraints] Camera: static throughout. Real-time speed, nothing added, skipped, repeated or reordered, no new gesture, no extra camera move, no re-staging, no new people. Exactly one carton, closed, upright, not duplicated, not vanished, not deformed, constant in size; nothing passes through it. No subtitles, captions or other on-screen text; the only lettering is the printed label on the package.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no extra fingers, no duplicate packages, no scale drift, no slow motion, no speed ramps, no other brands, no oversized or giant carton, no carton as wide as the notebook, no carton wider than his palm, no carton closer to the camera than the notebook, no carton on the notebook or on any paper, no carton right of the notebook, no lying or tilted carton, no carton touching his hand or arm, no studio lighting on the carton, no glow, no blister, no opened carton, no loose gum pieces
  ```
- **params:** model=wan3_0_prime · duration=7 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=image_references×4, video_references · request=video-22-fix-a3-request.json
- **errors:** none
- **evidence:** client-fixes-20261012/run07-video-22-fixed-preview.mp4 at about 1.0 s (carton base on the dark grey strip, red arrow in the client screenshot); 60-outputs/video-22/fix-20261012/ (a3, refs, meas, result.json)
- **qc:**
  ```text
  {"video": "22", "mode": "recreate", "status": "done", "fix": "CE-034", "clean": "C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/client-fixes-20261012/run07-video-22-fixed-clean.mp4", "preview": "C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/client-fixes-20261012/run07-video-22-fixed-preview.mp4", "capcut_project": "12_Oct_2026_v22", "capcut_pending": false, "jobs": [{"clip": "c1", "job_id": "4451b1c8-6e71-4eba-a843-75b1cce7441c", "credits": 21, "attempts": 3, "failed_attempts": [{"attempt": "a1", "job_id": "64fe0c90-8040-41db-b2e8-2bb82daf7631", "credits": 21, "caught_error": "CE-038"}, {"attempt": "a2", "job_id": "57cda53c-eb77-4f3c-a7cf-46046104735e", "credits": 21, "caught_error": "CE-040"}]}], "credits": 63, "passing_job_id": "4451b1c8-6e71-4eba-a843-75b1cce7441c", "qc": "regenerated twice (a1 CE-038, a2 CE-040), a3 accepted", "closed_caught_errors": ["CE-034", "CE-038", "CE-040"], "measurement_of_delivered": "T scale with the table plane calibrated on the source V16 notebook (21 cm page, f 26 mm, camera ~11 cm above table): delivered carton A 1.27x, B 1.29x (width), 1.36-1.38x by height; over 25 percent and A/B agree, so the client's eye was right. A first pass that fitted the plane including the carton's own width was circular (~1.0x) and was discarded. Evidence: meas/scale_calibrated_rest.json, scale_calibrated_use.json, scale_calibrated_last.json", "continuity": "counts: carton 1/1/1/1 at 0.0, 1.8 split, 4.1 split, end (and at every dense checkpoint) | use: none, closed carton untouched; left hand sweeps in front of it at 1.37-1.50 s and passes behind it at 5.9-6.3 s with correct occlusion order, carton unmoved and unchanged, no visible contact | permanence: same spot x 52-206 on the bare grey front edge left of the notebook on both sides of each insert, same size and label orientation | anchor: in frame from 0.0 s, drift vs notebook/table edge <= ~3 px | size: carton A 0.91-0.93x and B 0.90-0.91x of reckoned size (height 0.98-1.00x) at rest 0.0 s, in use 3.0 s and last frame 6.2 s, agree, constant (a3/scale_rest.json, scale_use.json, scale_last.json, scale_rest_height.json) | posture/support/place: stands upright on its base, whole base on the bare grey metal front edge with a contact shadow, no lean, float or tilt, in the least-visited zone of the source table; abuts the notebook's near-left corner (about 0 px gap, not on the page) | label: wordmark Neuro, GUM badge, Cinnamon tag, Energy & Focus legible, fine print blurry but no wrong letters | audio: original, whole, one stream copy (md5 of the final stream ee143a81d55ad5dd306e3af6c3820170 equals the source segment) | text: 1 layer, 4 lines word for word, fontSize 10, posX 0, posY 0.38, no emoji, capcut-text-style --check 0 off | joins: dense sheets in assembly/qc/dense (open, join1-4, end) all viewed, only A09 in the dissolves, no ghost of the original creator", "sync": "in_sync (offset 0.0 s, corr 0.631, 5/5 windows reliable after the white-dissolve rebuild; raw clip constant_offset -0.133 s before the rebuild; evidence a3/sync-final)", "acceptance": {"a_size": "pass: A 0.91-0.93x, B 0.90-0.91x, within 25 percent of reckoned size, both methods agree (a3/scale_*.json)", "b_count_closed_spot_label": "pass: count 1, closed, same spot (x 52-206) before and after each insert, label orientation constant (assembly/qc/dense)", "c_posture_support_place": "pass: upright on its base, on the bare grey front edge, contact shadow, front-left free corner; abuts the notebook corner, no hand-width gap (asked-for gap not achieved)", "d_person_beats_sync": "pass: A09 identity and the source beats; sync in_sync offset 0.0 s corr 0.631", "e_no_ghost": "pass: dense checks at joins 1-4 show only A09, no original creator in the dissolves", "f_text": "pass: 4-line layer present 0-11.5 s, no emoji, style check 0 off", "g_audio": "pass: original audio whole, one stream copy, md5 equals the source segment"}, "evidence": {"fix_folder": "C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07/60-outputs/video-22/fix-20261012/", "a3_raw": "C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07/60-outputs/video-22/fix-20261012/a3/raw.mp4", "a3_request": "C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07/50-requests/video-22-fix-a3-request.json", "a1_request": "C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07/50-requests/video-22-fix-a1-request.json", "a2_request": "C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07/50-requests/video-22-fix-a2-request.json", "timeline_clean": "C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07/60-outputs/video-22/fix-20261012/assembly/clean-orig-audio.mp4", "preview_qc": "C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07/60-outputs/video-22/fix-20261012/preview-qc/qc.json", "timeline_qc": "C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07/60-outputs/video-22/fix-20261012/assembly/qc/qc.json", "sync": "C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07/60-outputs/video-22/fix-20261012/a3/sync-final", "uploads": "C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07/30-assets/uploads-fix-22.json"}, "blocker": null, "notes": "Failure causes: a1 (flat carton right of the notebook) came out 1.7-2.1x thick and tilted with the right hand landing on it (CE-038: where the hands cover every bare spot, size words and padded references do not shrink it); a2 (upright right of the notebook plus a composite size-reference image as Image 4) came out 1.23-1.31x and stood on the notebook page because the 9:16 frame leaves no room right of the notebook (CE-040). Lever that worked (a3): the size-reference composite at 0.85x true size standing on a spot that exists in the source frame (free front-left corner, bare grey front edge, left of the notebook) plus an upright, same-depth instruction. Rebuild: pieces of the a3 clip with the white dissolves rebuilt from the original per-frame alpha, shared cleaned V16 inserts at 1.80-4.40 and 6.70-9.30, original audio as one whole stream copy (the old deliverable re-encoded pieces), same 4-line text layer, new CapCut project 12_Oct_2026_v22 (capcut lint 0 errors, 1 intended cue-too-long warning, media info left as in the delivered project). The CapCut render step did not produce a preview (fontconfig drawtext crash), so the preview was burned with ffmpeg drawtext and CapCut's en.ttf (size matched to the delivered preview, 540x960, original audio stream copy); preview QC: text on every sample, only label words and the insert's own text flagged. Calibration assumptions for the table plane: 21 cm page, f 26 mm equivalent, camera ~11 cm above the table; the model drifts the notebook by about 25 px, so A and B were measured per frame. Remaining flags: the carton touches the notebook's near-left corner instead of standing a hand-width away; the left hand overlaps the carton in image space at 1.37-1.50 s (in front) and 5.9-6.3 s (behind) with correct occlusion and no visible contact; the delivered carton re-measured at ~1.3x, confirming the client; this fix used all 3 generations (63 credits)."}
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261007-232745-07\40-briefs\video-22-plan.md
- **class:** anomaly-catalog.md §2.15 (blend, render not paste) and §4 QC (blend/paste test); generation-system.md §4b (grounding: contact shadow, reflection, light and colour match); production-agents.md (layout composite = placement guide only)
- **cause:** qc-miss
- **fix:** none yet. Proposed: regenerate with the carton standing fully ON the table surface (not on the seam or an edge band), the layout composite used only for position and scale, never the look; prompt a rendered look (soft contact shadow falling away from the window light, faint reflection of the base on the steel, the room's warm dim colour temperature, phone-footage softness and grain), a 3x base crop and a colour comparison with the notebook paper as QC; max 3 generations.
- **verified prompt:** pending (inserted only after a new generation passes QC)
- **rule:** A placed product is accepted only when it is grounded in the scene: a visible contact shadow in the direction of the scene's light, a reflection or surface darkening where it meets a glossy or metal surface, its base well inside a surface (never on a seam or an edge), and its brightness, saturation and softness within the scene's range as read against a neighbouring object; QC crops the base at 3x on a full-resolution frame at rest and in use and compares colour and contrast with a same-scene neighbour, and a hard clean edge with no shadow or reflection is a regenerate reason, never a pass on 'contact shadow present'. A layout composite is a placement and scale guide only; the generation prompt asks for the rendered look explicitly.
- **status:** open
- **promoted to:** —

## CE-044 · 2026-10-12 · Grounded layout reference and grounding wording did not ground the carton: hard clean base, no cast shadow, no reflection, squared to the lens
- **source:** agent
- **video:** 22
- **run:** C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07
- **delivered:** CapCut project 08_Oct_2026_v22 · clean C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07/60-outputs/video-22/clean.mp4 · credits 21 · run QC: accepted
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Neuro Energy & Focus Cinnamon 9-piece carton (V16 recreate, CE-043 fix pass, attempt 1: grounded layout reference + grounding wording)
- **assets:** A09.jpg; A709-p40.png; A708-p25.png; v2/refs/scale-ref-grounded-left.png (Image 4: 3D carton 0.92x, yaw 12, shadow + reflection); V16 own-silent.mp4
- **user said:** — (caught by the agent during the run)
- **what was wrong:** CE-043 attempt 1 (job 49927b98-ec5a-4554-9455-dc1b192406d6, v2/a1): Image 4 (layout reference) now carried the grounding (3D-projected carton at 0.92x true size, tone-matched muted warm, directional contact shadow, faint blurred reflection on the steel) and the prompt asked for the rendered look in plain words (soft darker contact shadow toward the lens and to the right, faint blurred reflection on the steel, muted warm colour, notebook's phone softness, label turned about 15 degrees) and said to use Image 4's grounding. The take has the right size (0.98x vs the notebook at the same depth), count 1, same spot, and still reads as pasted: on a 3x crop at 1.0 s the base is a hard clean line with only a hairline of dark, no cast shadow on the steel, no reflection, the carton is squared to the lens (the turn was not rendered) and it is the brightest saturated cyan block of a warm dim scene (lum 116, sat 0.54, R/B 0.46 against steel lum 83 and wood lum 98 with R/B 1.4-2.5). The model does draw cast shadows on the steel for his hand (visible at 1.25 s), so the capability exists. The grounding in a small full-scene layout image (carton about 10 percent of its area) and in the prompt text did not transfer: the carton was drawn from the two studio packshots (Images 2 and 3), which the prompt scoped to structure, material, colours and label but which are the only large views of the carton.
- **brief:**
  ```text
  Video 22 of 22 — NEUROGUM — Recreate V16
  Concept: V16 recreated beat for beat with character A09 and the Neuro Energy & Focus gum carton (Cinnamon, 9 pieces).
  Reference pattern: V16 card (timing, beats, inserts at 1.80-4.40, 6.70-9.30).
  Characters/assets: A09 (Image 1); A709.jpg, A708.jpg.
  House approach: none (no examples).
  Substitutions: creator → A09 | Placement: stands upright at the front-right corner of the table, outside the sweep of the hands, label toward the lens, in the same spot in every shot.
  Main action & states: source beats unchanged; product untouched and persistent.
  Style & camera: as V16, static phone camera, the source's light.
  Text: CapCut layers in the house style, reference wording/positions (see plan).
  Inserts: V16 1.80-4.40, V16 6.70-9.30.
  Sound: original audio restored; inserts with their own sound.
  Model & operation: wan3_0_prime reference-to-video (≈ recreate from Video 1), 7 s → trim 6.300 s, 9:16 720p, audio off, thinking on · est. 21 credits
  Fidelity: Video 1 = silent own content (motion/camera/timing), action script written out in order, keep-list + exclusions, same duration; sync-check after the merge. Risk: low.
  Adaptation logic: product placed at the analysed anchor; source branding dropped.
  ```
- **prompt:**
  ```text
  [Core Task] Recreate Video 1 as a real phone-shot vertical clip with only these changes: the person and the product. Video 1 is the motion, camera, framing, cut and timing reference: keep every movement, gesture, head turn, gaze, expression and mouth movement of the person in Video 1 in the same order, at the same moments and at the same real-time speed, and keep the camera, framing, cuts, light, room, background and the notebook's place. Do not inherit the appearance, clothing, text, watermarks or branded items of Video 1. The man corresponds to Image 1, adopting facial features, hairstyle, skin tone, build and clothing (short hair, stubble); Image 1 is only his identity. The Neuro Energy & Focus gum carton (Cinnamon, 9 pieces) corresponds to Image 2 and Image 3, which jointly define one single package, adopting only its structure, material, colours and printed label, not their studio lighting, shadow, background or camera angle: a small closed flat paperboard carton, 7.5 cm wide, 8.5 cm tall and 1.6 cm thick, light blue with wavy lighter-blue shapes, a blue N logo and Neuro wordmark top-left, an orange-red GUM badge top-right, a Cinnamon tag, the title Energy & Focus. Image 4 is a size, spot and grounding reference: it shows this carton at the front-left corner beside the notebook, one third as wide as the page, in the room's warm dim light with its soft contact shadow and faint reflection on the steel; use that size, spot, angle and grounding, not its framing or wall. Keep its exact shape, proportions and artwork; it stays closed. Video 1 has no such item, but the carton is part of this scene from the first frame: it stands upright on its base, its whole base on the bare brushed steel front band at the front-left corner, clearly in front of the wood strip and not on the seam, left of the open spiral notebook, its base level with the notebook's front edge, a narrow band of bare steel between them, inside the frame, its label turned about fifteen degrees away from the lens. The room's warm light slants from the upper left and behind and lights it like the notebook and the man: a soft highlight on its upper left, its right side and lower part in shade, its blue slightly muted and warmed, no brighter or more saturated than the wood or his skin, with the notebook's soft phone focus and grain. A soft darker contact shadow lies under its base and falls toward the lens and to the right, as his hands' shadows fall on the page, with a faint blurred reflection of its lower edge on the steel; its bottom edge meets the steel with no gap or hard cutout outline. It stays untouched in the same place for the whole clip.
  [Plot Summary] The open spiral notebook lies at the bottom centre as in Video 1; the small carton at the front-left corner, one third as wide as the page, keeps exactly this size, light and shadow before and after every cut.
  Shot 1 [0-1.8s]: Static selfie framing from the table edge, a door frame behind; the carton stands at the front-left corner. The man sits square to the camera, leaning forward, both palms flat on the notebook with fingers tapping, head bobbing, mouth moving rapidly as if arguing, brows raised; the frame-right hand lifts the top page, flips it and slaps it back down; then wide sweeping open-hand gestures, leaning in, mouth still talking, as the image brightens toward white; his hands and arms never touch the carton.
  Shot 2 [1.8-4.1s]: Hard cut, same framing, the one carton still stands in the same spot: he leans back then forward, hands chopping and waving, palms-up shrugs, mouth arguing; hands come down to the notebook; the right index finger taps the temple; the arm flings out wide toward frame-right and comes back down to the notebook.
  Shot 3 [4.1-6.3s]: Hard cut, same framing, the one carton still stands in the same spot: hands out palms up in a shrug, a quick temple tap, an arm swing wide to frame-right; then both hands tapping and sliding across the notebook; a hand wipes across the mouth and nose, then a final open gesture, still mouthing.
  [Audio Style] No dialogue. No background music.
  [Camera & Core Constraints] Camera: static throughout. Real-time speed, nothing added, skipped, repeated or reordered, no new gesture, no re-staging, no new people. Exactly one carton, closed, upright, not duplicated, not vanished, not deformed, constant in size; nothing passes through it. No subtitles, captions or other on-screen text; the only lettering is the printed label on the package.
  [Negative Prompts] no subtitles, no watermark, no face distortion, no identity drift, no extra fingers, no duplicate packages, no scale drift, no other brands, no oversized carton, no carton on the notebook or any paper, no carton right of the notebook, no tilted or leaning carton, no carton touching his hand, no floating carton, no shadowless carton, no hard cutout edge, no pasted look, no studio lighting on the carton, no carton brighter or more saturated than the room, no glow
  ```
- **params:** model=wan3_0_prime · duration=7 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=image_references×4, video_references · request=video-22-fix-v2-a1-request.json
- **errors:**
  ```text
  none; job 49927b98-ec5a-4554-9455-dc1b192406d6 completed, 21 credits
  ```
- **evidence:** C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261007-232745-07/60-outputs/video-22/fix-20261012/v2/a1/base3x_1.0.png (3x base crop), v2/a1/crops_montage.png, v2/meas/colour_v2a1_1.0.json, v2/a1/raw.mp4
- **qc:**
  ```text
  attempt 1 of the CE-043 pass: size ok, count/spot ok, but no cast shadow, no reflection, hard clean base, squared to the lens, brightest saturated cyan block: paste signs 3, 5, 8; regenerate with a different lever
  ```
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261007-232745-07\40-briefs\video-22-plan.md
- **class:** anomaly-catalog.md §2.15 (signs 3, 5, 8 and 9: no contact shadow, packshot pose, hard outline without reflection, footprint) and §2.16; wan-3-0.md §5 paste row; CE-043
- **cause:** reference
- **fix:** none yet
- **verified prompt:** pending (inserted only after a new generation passes QC)
- **rule:** A look the model must copy has to be in the reference it draws the object from: when the object's only large references are studio packshots, a grounded layout image (object about 10 percent of its area) plus grounding words does not ground it. Put the grounding into a close-up reference of the object itself (standing on the real surface of the scene, with its cast shadow, its reflection, the room's warm muted colour and the footage's softness, at about 40 percent of the canvas), bind it in the prompt as the look and grounding reference, and keep one packshot for the printed label only [OBSERVED once; attempt 2 of the same pass tests the close-up].
- **status:** open
- **promoted to:** —
