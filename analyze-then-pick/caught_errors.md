# Caught errors: the feedback ledger

One entry per video the user was not satisfied with, in the user's own words plus the diagnosis,
the cause, the fix and the rule the pipeline learns from it.

**Only the user's feedback after delivery fills this file.** The videos are generated, edited in
CapCut and delivered; the user watches them; whatever they then say is wrong, disliked, illogical
or unsatisfying becomes an entry, with the video's details. The agents never write here: an error
an agent catches during the run (QC, the pre-generation check, the sync check) is fixed in place,
as it always was, and stays in the run's own verdicts and logs. In Edit Mode the per-attempt
review before a video is approved is part of making it, not delivery; an entry is written only
when the user reports a problem with a video already approved or delivered. The file is **read at the start of
every run** (command A1 / E1): the entries that apply to the run (same mode, model, product family
or anomaly class) go into `<RUN>/20-analysis/caught-errors.md`, every plan names the entries it
applies, every prompt carries their rules in the model's phrasing, and QC checks each applied
entry by id. An entry whose rule is general, or that recurs, is **promoted** into the reference it
belongs to (an anomaly-catalog class, creative-direction, brand-guardrails, text-and-format, the
model guide's failure table) and marked `promoted` with the pointer; the entry stays here as the
record. The build prompt is updated after a promotion.

Write entries with the toolkit, never by hand, so the ids and the format stay parseable:

```
T caught-error add --title "<short title>" --video "<video or CapCut project>" --run "<run id>" --mode <analyze-recreate|analyze-create|edit> --model <model id> --product "<client product>" --user "<the user's words, verbatim>" --wrong "<what was wrong, diagnosed>" --class "<reference and section>" --cause <prompt|reference|parameter|plan|qc-miss|model-limit|unknown> --fix "<what was done>" --rule "<the general rule, as a kind not an instance>" [--brief <text|file>] [--prompt <text|request.json>] [--qc <text|file>] [--plan <file>]
T caught-error list [--mode …] [--model …] [--class …] [--status open|fixed|promoted] [--grep …] [--rules]
T caught-error set --id CE-003 --status promoted --promoted-to "anomaly-catalog.md §2.14"
```

Fields: **video** (number or CapCut project name), **run**, **delivered** (the CapCut project,
the final file, the credits and the run's QC verdict, read from the video's `result.json`),
**mode**, **model**, **product**,
**user said** (verbatim; the user's words are the evidence), **what was wrong** (the diagnosis
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
- **Recording:** whenever the user, having watched the delivered videos, says one is wrong, at the
  end of the run or in a later session, the entry is written first, with their words verbatim and
  the video's details (CapCut project, final file, brief, prompt, the run's QC verdict), before
  any fix is offered. One entry per distinct problem; a message about three videos writes three.
  Nothing the user reports goes unrecorded, and nothing the agents caught themselves goes in.

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
- **promoted to:** anomaly-catalog.md §2.7; scripts/atp.py scale; generation-system.md §4b.2, §5, §8, §9, §10; command A2b/X1/X2/X4/X9

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
- **status:** fixed
- **promoted to:** —

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
- **status:** fixed
- **promoted to:** —

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
- **status:** fixed
- **promoted to:** —

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
- **status:** fixed
- **promoted to:** —

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
