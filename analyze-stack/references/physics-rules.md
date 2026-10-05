# Physics rules — the prompt physics contract (every clip prompt and every edit prompt)

Owner brief: "Prompt generation must be extremely careful about physics, movement, mixing, space,
surroundings and every other entity in the scene. Everything must be processed as one interconnected
system so there are no anomalies when the clips are generated." Seedance's own acknowledged limits
(`SEEDANCE-SPEC.md` §1, §9): physical plausibility of complex motions, multi-subject interaction,
text rendering, hands. These rules exist to keep every shot inside what the model does well.

## 1. Structure of every prompt: START STATE → TIMELINE → END STATE

- **Start state (t = 0 s)**: who is where, facing which way; what each hand holds; every product/prop
  position and orientation (label direction); container fill levels; camera position, shot size, angle;
  light source and direction; the ambient sound bed. Nothing may exist later that is not here or
  brought in by a described action.
- **Timeline**: continuous integer-second ranges with no gaps (`0-3s`, `3-9s`, `9-15s`); one main event
  per range; cause before effect; each range ends with the observable state it produced.
- **End state (t = duration)**: final positions, poses, hand contents, product orientation, fill levels,
  camera, light, sound state; the frame holds for the last 0.5–1 s. This block is copied verbatim as
  the next clip's start state (continuity handoff).

DO: `0-3s: she lifts the bottle with her right hand from the right of the glass; label stays toward the camera. Ends with the bottle 10 cm above the glass rim, tilted 20°.`
DON'T: `She pours the drink and enjoys it.` (no start, no cause, no end, two events)

## 2. Cause and effect

Every visible change has a visible cause in the same or the previous range: a pour raises the level;
a hand releases before an object falls; a light switch precedes a light change; a mouth moves before a
line is heard. Reactions come after triggers, and the trigger is on screen (sd25-pe causal-reveal rule).

DO: `3-6s: the cap is twisted off by her left hand; <short hiss> as it opens; the cap stays in her left hand.`
DON'T: `The bottle is suddenly open.`

## 3. Conservation of objects — nothing appears, disappears, teleports or morphs

- State the count of every key object and keep it: "exactly one glass, one bottle, one hand in frame".
- Objects that leave the frame are described leaving ("the cap exits frame right in her hand"); objects
  that return are the same object ("the same bottle, same label orientation").
- Occlusion: after a hand covers the product, it re-emerges unchanged (spec §9: repeat identity after occlusion).
- Morphing: a product never changes size, colour, label, cap, or shape; ice never changes count; food
  does not regrow; a bite stays taken.
- Accumulation is step-by-step and monotonic (owner's examples):
  - "ice cubes are dropped in one at a time — one, two, three — and the level rises with each cube"
  - "the liquid level rises steadily while poured, from empty to two-thirds, never above the rim"
  - "foam forms as the stream hits the surface, peaks at 1 cm, then settles over 3 s to a thin ring"
  - "condensation beads appear gradually over the clip on the cold can, none on the warm jar"
  - "the tube is squeezed; a pea-sized amount emerges and stays on the fingertip until it is applied"

DON'T: "ice cubes fill the glass" (how many? when?), "the drink is now full" (no pour shown).

## 4. Gravity, momentum, liquids and materials

Director material reasoning (`seedance\director\references\continuity-and-causality.md` §5, binding): derive the
behaviour from the ACTUAL material and conditions in `product-spec.md` — density, viscosity, carbonation, binding,
transparency, temperature — never from a universal decree ("every solid floats", "every liquid mixes", "contents stay
visible through an opaque can"); distinguish a stream entering a vessel from a flat layer appearing above it, solid
contact from interpenetration, elastic deformation from a change of topology; unknown properties stay unknown
(mark "estimate") rather than inventing numbers.

- Liquids fall straight down, pool at the lowest point, never flow uphill, splash in proportion to
  height and speed; a tilted container pours only when tilted past the fill line; a stream narrows as
  the pour slows; drips stop within a second.
- Momentum: heavy objects move slower and stop with a settle; nothing halts instantly mid-air; a
  dropped object bounces only if its material bounces (rubber ball yes, glass no).
- Cloth, hair, powder, foam, steam, smoke: describe the direction and the settle time ("steam rises
  straight up and thins over 2 s").
- Spills/mess are either intended (then described with extent and where they land) or excluded ("no spill").
- Ripples spread outward from the impact point and fade in ~2 s; reflections move with the surface.

DO: `6-11s: espresso flows into the clear chamber; the level rises evenly; the machine body stays rigid; no spill on the counter.` (fal example E23 in the spec)
DON'T: `Coffee splashes everywhere dramatically.`

## 5. Hands, fingers, grips (the most frequent anomaly)

- One hand or two, which hand, what it holds, where the fingers are, matched to the object's size from
  `product-spec.md` ("a 12 oz slim can is held with four fingers around the body and the thumb on the
  label edge"; "an 8 oz jar sits in the palm with fingers wrapping the lower half").
- Hands enter and leave frame by a described path; the empty hand's position is stated.
- Never two actions with the same hand in one range; never a grip that the object's weight makes implausible.
- Constraints line: "no extra hands or fingers, no duplicated limbs" (Dreamina/fal wording, spec §9).

DO: `her right hand holds the bottle by the neck with three fingers; her left hand rests flat on the counter.`
DON'T: `she holds the bottle` / `hands appear`.

## 6. Fixed spatial layout — repeated in every clip

Where every object sits (relative to stable anchors: counter edge, window, sink, table centre — not
only screen-left/right, sd25-pe rule), where the camera is (distance, height, angle, side), where the
light comes from (direction, quality, colour). The continuity sheet holds the master layout; each
prompt restates it in START STATE and CAMERA/LIGHT so the same room is generated every time.

DO: `the glass stands at the centre of the white counter, 20 cm from the front edge; the bottle stands to its right; the window is behind and to the left; the camera is at counter height, 60 cm away, eye-level medium shot, slightly right of centre.`
DON'T: `kitchen setting` / `nice lighting`.

## 7. Realistic timing

A pour lasts as long as filling that glass takes (a 350 ml glass from a bottle: 4–6 s); a cap twists
off in 1–2 s; a sip is 1–2 s; a spread of cream 3–5 s; a lid lifts in 1 s; a candle lights in 1 s and
its melt pool needs minutes (do not show it "melting" in 5 s); a bite + chew 2–4 s; a spray 0.5 s.
Allocate 2–5 s per ad beat, 6–8 s per cinematic beat (spec §6.5); never compress a physical process
below its real duration — cut instead (a clip boundary or a hard cut inside the prompt).

## 8. One clear action per beat; limited simultaneous motion

- One main action per time range; at most one secondary motion (steam rising, a hand resting).
- At most 2 people acting at once; ≤ 4 people in frame (spec §9.3); one camera move per shot (spec §5).
- Prefer slow, gentle, continuous small movements; avoid sprints, jumps, throws, violent rolls (spec §6.6).
- High-frequency actions (shaking, stirring fast, tapping) are described without timestamps for each
  repetition ("she stirs for 3 s") (spec §6.4).

## 9. Text on screen and in the world

- No on-screen text is generated (overlays, captions, subtitles, handles) — they belong to the edit or
  the owner's caption tool. Constraint line on every prompt: "no text overlays, no subtitles".
- World text (labels, packaging) comes from reference images; keep it short and at MCU or closer for
  legibility; at wide shots describe it as a colour block; never ask for tiny text (menus, ingredient
  lists, phone screens) — replace with "unreadable small print" or keep the object out of focus.
- Never invent text the owner did not supply; gibberish risk is stated in the writer notes.

## 10. Sound matches action (native audio)

Each contact, pour, click, step, or mouth movement has its SFX in the same range, written as
`<sfx>`; music in `(…)`; dialogue in quotes with speaker attributes and language; ambience listed once
in START STATE; "No BGM; generate only environmental sounds and action sounds" when the original has
no music (spec §4). Speech finishes before the final held beat; ≤ 10 words per line; non-speakers'
mouths stay closed. Edit approach: `generate_audio:false` and the source audio is muxed back — sounds
that must change with the product are added in the post-generation edit (`SEEDANCE-EDIT.md` §5).

## 11. Camera physics

Locked-off by default ("locked-off camera, fixed camera position; the camera never moves; no push, no
pan, no zoom, no handheld shake"), one move per shot with start/end composition and a trigger ("the
camera begins the push only after the cap is off"), handheld only if the original is handheld ("slight
handheld feel"), never crossing the line of action; DoF stated (spec §5, §6).

## 12. The DO/DON'T table for writers (paste-ready wording)

| Rule | DO (Seedance wording) | DON'T |
|---|---|---|
| Count | "exactly one bottle throughout; exactly one glass" | "some bottles" |
| Accumulation | "one ice cube at a time — one, two, three — the level rises with each" | "ice fills the glass" |
| Pour | "the liquid level rises evenly from empty to two-thirds over 5 seconds; no spill" | "she pours a drink" |
| Foam | "1 cm of foam forms then settles to a thin ring in 3 seconds" | "foamy" |
| Hands | "right hand, three fingers on the neck, thumb on the label edge; left hand flat on the counter" | "holding it" |
| Layout | "the bottle stands to the right of the glass, 10 cm apart, labels to camera" | "on the table" |
| Camera | "locked-off camera, eye-level medium shot; the camera never moves" | "dynamic camera" |
| Timing | "3-8s: the pour" | "she quickly pours" (in 1 s) |
| Text | "no text overlays, no subtitles; the label reads only what @Image 2 shows" | "with a caption saying…" |
| Sound | "<glass set down on wood>", "No BGM" | "nice sounds" |
| End | "Ends with the glass two-thirds full at the centre, bottle at the right, label to camera; hold 1 second" | (nothing) |
