# Caught errors: the feedback ledger

One entry per video the user was not satisfied with, in the user's own words plus the diagnosis,
the cause, the fix and the rule the pipeline learns from it. The file is **read at the start of
every run** (command A1 / E1): the entries that apply to the run (same mode, model, product family
or anomaly class) go into `<RUN>/20-analysis/caught-errors.md`, every plan names the entries it
applies, every prompt carries their rules in the model's phrasing, and QC checks each applied
entry by id. An entry whose rule is general, or that recurs, is **promoted** into the reference it
belongs to (an anomaly-catalog class, creative-direction, brand-guardrails, text-and-format, the
model guide's failure table) and marked `promoted` with the pointer; the entry stays here as the
record. The build prompt is updated after a promotion.

Write entries with the toolkit, never by hand, so the ids and the format stay parseable:

```
T caught-error add --title "<short title>" --video "<video or CapCut project>" --run "<run id>" --mode <analyze-recreate|analyze-create|edit> --model <model id> --product "<client product>" --user "<the user's words, verbatim>" --wrong "<what was wrong, diagnosed>" --class "<reference and section>" --cause <prompt|reference|parameter|plan|qc-miss|model-limit|unknown> --fix "<what was done>" --rule "<the general rule, as a kind not an instance>"
T caught-error list [--mode …] [--model …] [--class …] [--status open|fixed|promoted] [--grep …] [--rules]
T caught-error set --id CE-003 --status promoted --promoted-to "anomaly-catalog.md §2.14"
```

Fields: **video** (number or CapCut project name), **run**, **mode**, **model**, **product**,
**user said** (verbatim; the user's words are the evidence), **what was wrong** (the diagnosis
in pipeline terms: which checkpoint, frame or beat, what the ledger or the plan said), **class**
(the reference and section it belongs to, or `new`), **cause** (prompt, reference, parameter,
plan, qc-miss, model-limit, unknown), **fix** (regenerate with what change, post-fix, none),
**rule** (one line, general, the kind of error and the check that catches it), **status**
(open, fixed, promoted), **promoted to**.

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
- **Recording:** whenever the user says a delivered video is wrong, in the run or in a later
  session, the entry is written first, with their words verbatim, before any fix is offered.
  Edit Mode's "Needs changes" always writes one. Nothing the user reports goes unrecorded.

## CE-001 · 2026-10-08 · Three capsules became one after a walk-past
- **video:** anime Create video (earlier run)
- **run:** reported from an earlier run
- **mode:** analyze-create
- **model:** unknown
- **product:** energy capsules
- **user said:** "in the beginning there were 3 capsules in the desk, the kid in the video continues walking past them and then when it gets back there are only one capsule left (things should be persistent throughout the vide, except in logical reasons such as the guy eats 2 of them energy capsules"
- **what was wrong:** the count of a multiple changed with no visible cause across an occlusion and a return; the ledger tracked only where the product was, not how many
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
- **class:** anomaly-catalog.md §2.7 (scale and proportion)
- **cause:** plan
- **fix:** real dimensions in the registry; a size reckoning per product per shot (depth, lens, expected fraction of the frame, ratio to a named neighbour, size ladder, constancy) in the plan and the prompt; `T scale` on a frame at rest, one in use and the last; over 25 % regenerates with no post-fix
- **rule:** a product's size in the frame is reckoned from its real dimensions, its distance, the lens and a named neighbour, never guessed, and measured after generation
- **status:** promoted
- **promoted to:** anomaly-catalog.md §2.7; scripts/atp.py scale; generation-system.md §4b.2, §5, §8, §9, §10; command A2b/X1/X2/X4/X9
