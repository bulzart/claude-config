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
patterns and their causes, checks which ones the pipeline already covers, rewrites the owning
prompting, use-case, dismissal, craft, example and QC sections for the gaps, promotes the entries
it folded in, and logs the pass in `learning-log.md`. When nothing is missing it changes nothing
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
- **status:** fixed
- **promoted to:** general part (a placed product never takes the source's beat): generation-system.md §4b.1b, anomaly-catalog.md §2.16; the Neuro form default (small closed carton or sachet in casual scenes) stays readable here

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
- **promoted to:** wan-3-0.md §5 (small placed product row; untested levers in §9); stays open as a model limit

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
- **promoted to:** wan-3-0.md §5 (small placed product row; untested levers in §9); stays open as a model limit

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
- **promoted to:** wan-3-0.md §5 (small placed product row; untested levers in §9); stays open as a model limit

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
- **status:** open
- **promoted to:** —

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
- **status:** open
- **promoted to:** —

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
- **promoted to:** —

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
- **status:** open
- **promoted to:** —

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
- **status:** open
- **promoted to:** —

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
- **status:** open
- **promoted to:** —

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
- **status:** open
- **promoted to:** —

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
- **status:** open
- **promoted to:** —

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
- **status:** open
- **promoted to:** —
