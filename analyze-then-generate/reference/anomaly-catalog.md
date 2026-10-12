# Logical and physical anomalies — catalog, prompting stack and QC stack

Load this with `generation-system.md`: when the asset registry is built (command A2b; Edit Mode E3),
at X1 (plan), X2 (prompt), X4 (pre-generation QC) and X9 (QC). It is model-agnostic; the locked
model's guide (§3.14, §5, §7) says how to phrase the lines below in that model's structure.

It generalises two failures seen in anime Create videos (2026-10):

- **Counts.** Three capsules lay on the desk. The boy walked past them and came back; one capsule was
  left. Nothing had taken the other two.
- **Openings.** The mother filled the boy's bottle with milk. The bottle has a flip-top straw spout
  on one side of its lid; the boy drank from the other side of the lid, where the bottle has no
  opening.
- **Solidity.** A character tossed a crumpled paper and it travelled straight through the client's
  product, a plastic object, as if it were not there.
- **Blend.** A can stood on a bedroom dresser two to three times its real size, squared to the lens
  like a packshot, lit flat and cool while the room was warm and dim, sharper than the plate, with
  no contact shadow, and drawn straight-on while the camera looked up at the dresser: a paste, not
  a render.

A ledger that tracks only where the product is ("bottle: on the table → in hand → on the table")
lets both through: it carries neither the **count** of the capsules nor the bottle's **openings and
use**, and a QC pass that looks for the product's presence and spot never counts the capsules or
checks where the mouth met the bottle. The rules below close that gap for every product. The
examples illustrate the rules; they never limit them.

## 0. Four questions behind every anomaly

1. **How many?** Every multiple is counted at t=0, and the count changes only through a visible
   cause, by exactly the amount the cause explains (§2.1).
2. **Through what?** Every use of an object goes through the part built for it (the spout, the
   opened top, the nozzle, the torn notch, the handle, the screen) after the step that readies it,
   and the contact point is named (§2.2, §2.3).
3. **Still there, still so?** Whatever leaves the frame, passes behind a hand or sits across a cut
   comes back with the same count, spot, state and size (§2.4, §2.5).
4. **Still solid?** Nothing passes through the product or through anything else that is solid; a
   moving thing stops, deflects, bounces or lands at a solid, and whatever it hits reacts (§2.14).
5. **Rendered or pasted?** The product is lit, exposed, focused, grained, scaled, angled and
   shadowed exactly like the objects beside it, from the same camera (§2.15).
6. **How big, from here?** The product's size in the frame follows from its real dimensions, its
   distance from the camera, the lens and the known size of its neighbours; it keeps that size as
   things move and across cuts (§2.7).
7. **Where would a person leave it, and how?** The product lies or stands the way its shape allows, on
   something that is visibly there, out of the way of the hands at work; it never takes a beat of the
   source that belongs to another object (§2.16).

## 1. The affordance sheet (asset registry, one per product or object)

Written in `30-assets/registry.md` (and `state.json → assets`) for every product or object entity
that a video may show (A2b; Edit Mode E3 when the replacement is handled on screen), from the
supplied images and specs. It is the authority for how the product may be handled: the plan quotes
it in the ledger, the prompt quotes it in the use beats, and QC checks against it. Where an image
does not show a part (the spout side of a lid), say so and keep the use to what is known.

| field | record | flip-top straw bottle (example) | slim drink can (example) |
|---|---|---|---|
| parts | every visible part and where it sits | frosted semi-transparent body with printed time markers; screw lid; flip-top cap with the drinking spout on one side; lock clip; straw inside; wrist strap on the lid's loop | aluminium body; top end; ring pull (tab); the opening beside the tab |
| openings | where the contents come out, and where they go in | out: the spout on the lid; in: the whole lid unscrews | out: the opening under the tab; nothing else |
| opening sequence | the visible steps before any use | drink: flip the cap up → the spout stands up → drink; fill: unscrew the lid → pour → screw it back | lift the tab → it stays up → drink from the opening |
| use | how it is really used, and by whom | drunk through the spout with the head level (it is a straw), the bottle tilted little, held by the body; a child holds it with both hands | tilted to the mouth, the head tilted back a little, the opening at the lips; one hand |
| contact point | which part touches what | lips on the spout; hand(s) around the body; the strap hangs from the lid loop | lips on the rim at the opening; the thumb under the tab when opening |
| contents, amount, visibility | what it holds and whether that shows | a liquid: level and colour visible through the frosted body; the straw shows inside | opaque: the level never shows; a sip shows only on the face and throat |
| states | every state it can be in; which are irreversible | lid on / off; cap closed / open; level full → empty; strap on the wrist / hanging | sealed → opened (irreversible); full → empty (invisible) |
| real size | height × width or diameter × depth in cm and the volume, from the spec; else the category's standard size marked [I] (§2.7 table); plus one comparison | ~24 cm tall, ~7 cm wide, 1 l; an adult's hand spans the body, a child needs two hands | 355 ml slim can, 15.7 cm tall, 5.8 cm wide; shorter than a hand is long |
| mark orientation | where the label or wordmark is and how it reads when the object stands | markers run down the front, "REFILL" at the bottom; upright when standing | wordmark vertical on the front; upright when standing; tilts with the can |
| impossible | what this object cannot do (the exclusion is picked from here) | drinking from the lid's closed side or through the body; the strap on the base; two spouts; a level that rises without a pour | drinking from the side or the bottom; a sip through a sealed top; the tab sealing itself; a visible level |

Fill the same fields for every other object: a gum carton (the flap at one end; pieces in a blister
or loose; one piece slides out of the opened end), a pouch (tear notch, zip; pieces shaken into the
palm), a blister (a piece pressed through the foil from the back), a capsule or tablet bottle (cap
off, shaken into the palm, swallowed with a drink), a tube or pump (the nozzle; a pump pressed with
one hand into the other palm), a spray (nozzle away from the face), a carton (its spout), a straw
cup (the straw in the lid's hole), earbuds (out of the case, into the ears), a phone (screen toward
the user, the thumb on the screen), a laptop (lid up, screen toward the user), a car (the driver's
door on the driver's side, the steering wheel on that side, wheels on the ground), a fridge (one
hinge side; the door stays open until it is closed), a bag (zip or flap), a chair (sat on from the
front).

### 1.1 Product families: the breaks to expect

| product | breaks seen or expected | the sheet facts that prevent them |
|---|---|---|
| canned drink | a sip through a sealed top, the side or the bottom; the tab raised at frame 0 for a can cracked later; a visible level; a second can after a cut; the label turning on its own; condensation that vanishes | tab flat → lifted; the opening beside the tab; opaque; one can; the label moves with the can |
| bottle with a cap | drunk with the cap on; the cap vanishes or doubles; the level tilts with the bottle; a pour through the closed cap | cap off → drink → cap on; the level stays horizontal; one cap, in a hand or on the table |
| flip-top / straw bottle | drunk from the side without the spout; the cap closed while drinking; the head tilted back on a straw; the strap moving to the base; milk that looks like water | the spout side; cap open; head level; the strap on the lid loop; opaque milk with a visible level |
| glass, cup, mug (contents form) | the wrong contents (water beside the can); refills itself; the handle changes side; a cold drink steams | contents from the sample; the level drops only on a sip; handle side; condensation or steam by temperature |
| carton (milk, juice) | poured from a closed corner; the spout cap on while pouring; the receiving vessel never fills | spout side; cap off → pour → cap on; the receiving vessel fills as the carton pours |
| gum carton, pouch, blister | a piece pulled through the carton wall; the pack still full after a piece; the blister pressed from the front; the chewed piece visible in a closed mouth; the wrapper missing | the flap end; a count per event; pressed through the foil from the back; chew with the mouth closed; the wrapper exists after unwrapping |
| capsules, tablets | three become one after a walk-past; swallowed without a drink; taken from a closed bottle; pills that roll off and reappear | a count per event; cap off → shake into the palm → swallow with a sip; dropped pills stay dropped |
| snack bar, cookie, fruit | no bite mark after a bite; crumbs before the bite; the wrapper torn before being touched; a peeled fruit whole again | bite → mark; the wrapper's state; irreversible |
| cream, tube, pump, spray | squeezed from the cap; the pump pressed on the body; a dollop that never absorbs; the spray toward the face | nozzle; a pump with one hand into the other palm; absorbed over seconds; nozzle away |
| phone, laptop, earbuds | the screen faces away; the UI re-randomises; earbuds held to the ears; the lid closed while typing | screen toward the user; the UI persists; earbuds in the ears, the case open; lid up |
| car, bike | parked indoors; entered through the wrong door; moves without a driver; wheels off the ground; doors that swing on the wrong edge | where it stands; the driver's door; wheels on the ground; driven only by a driver (`generation-system.md` §5b) |
| worn items (bag, watch, cap) | the strap changes shoulder; the watch changes wrist; a cap on, off, on | worn where worn; stays worn until taken off |
| appliance, furniture | the fridge door on the wrong hinge; a chair sat on backwards; an open door closed by nobody | hinge side; used from the front; a door keeps its state |
| any product near a moving thing | a tossed paper, a ball, keys, a hand, a sleeve, hair, a bag strap, a door or a passing person goes through it; a thing that hits it leaves it untouched; it sinks into the table or a hand | it is solid and opaque; every path near it is written as past it or onto it, with the consequence; it occludes and is occluded by depth order (§2.14) |

## 2. Anomaly classes

Each class gives the real-life rule, how it breaks across products, the ledger entry, the prompt
lines, how QC catches it, and the corrected retry. "Regenerate" and "post-fix" are the X9 verdicts
(`generation-system.md` §9).

### 2.1 Counts and conservation

**Rule.** Every multiple is counted at t=0. The count changes only through a visible cause, by the
amount the cause explains, and whatever was taken exists somewhere (a hand, a mouth, a glass, a bin).

**Breaks.** Three capsules become one after a walk-past. A pack of ten still holds ten after a piece
is chewed. Two cans on the table are three after a cut. A six-pack never loses the can that was
taken. A glass fills itself; a can pours a full glass and stays full. A bite leaves no bite mark. Two
wrappers for one piece. A plate of cookies refills. A second strap. A twin bottle once the arm has
passed. Two earbuds in the case and two in the ears.

**Ledger.** A **count** column for every multiple and a **level** column for every vessel:
`capsules | 3 | on the desk, right of the lamp | 4.0 s he walks past behind the desk, untouched: 3 | 7.5 s back at the desk; right hand takes two, mouth, swallow: 1 on the desk, 2 swallowed | end: 1`.

**Prompt.** Positive, with the number, the spot and the persistence; then the event with its amount:
- "Exactly three capsules lie on the desk to the right of the lamp. They stay there, all three,
  while he walks past and when he comes back."
- With consumption: "… He picks up two of the three with his right hand, puts them in his mouth and
  swallows them. One capsule stays on the desk for the rest of the video."
- A pack: "The opened pack holds nine pieces after she takes one."
- Liquids: "She pours from the can into the glass until the glass is half full; the can is then
  nearly empty and stays open beside the glass."
- Restate the count after every exit, occlusion, cut, hand-off and seam (§3 step 4).
- One exclusion in the model's syntax: "no capsule appears or disappears"; "only one pack"; "only
  one glass".

**QC.** At every checkpoint where the anchor is visible, **count** and write the numbers in the QC
note: the first frame, before the exit, after the re-entry, after each occlusion, after each cut,
the last frame. Densify the exit and re-entry at 15 fps (the capsule case) and every pass of a hand
or body in front of the items. In transparent vessels compare the level before and after each sip or
pour; a level that rises without a pour or falls without a sip is a break.
- **Regenerate** when a count or level changes without a cause or by the wrong amount.
- **Post-fix** only for an untouched static anchor in a locked shot: hold the anchor's pixels from a
  good frame over the bad stretch (as done for a pouch in 2026-10). Never when a hand interacts.
- **Retry:** state the count with its number at t=0, at the event and at the end; say what happens
  to what was taken; add the exclusion. If a reference image shows a different number (a pack
  photographed with twelve pieces), say which count holds ("the pack holds nine pieces here").

### 2.2 Openings and use (affordances)

**Rule.** An object is used through the part built for it, after the steps that make it ready, with
the contact point real life uses.

**Breaks.** The straw bottle drunk from the side that has no spout (the case). A can sipped through
its side or bottom, or through a sealed top. A bottle drunk through its closed cap. A carton poured
from a closed corner. A gum piece pulled through the carton's wall. A blister piece taken from the
front. A tube squeezed from its cap. A spray held nozzle-toward-the-face. A pump pressed on its body.
Earbuds held against the ears. A phone used with its back to the user. The driver entering by the
passenger door. A fridge opened from its hinge side. A strap worn on the wrist while it hangs from
the base.

**Ledger.** An **opening/lid state** column and a **contact** column on every use row:
`bottle | 1 | on the table, lid on, cap closed, full of milk | 3.0 s left thumb flips the cap up: cap open, spout up | 3.5–5.5 s lips on the spout, head level, both hands on the body: level ¾ → ½ | 6.0 s cap flipped closed`.

**Prompt.** The affordance sheet in action, as initial state → operation on the named part →
observable result, with the contact point:
- "The bottle's lid has a flip-top cap with the drinking spout on one side. He flips the cap open
  with his thumb, puts his lips on the spout and drinks through it with his head level, both hands
  around the frosted body; the milk level sinks a little. The strap hangs from the lid."
- Can: "He lifts the ring pull with his thumb; it stays up. He tilts the can to his mouth and
  drinks from the opening beside the tab, his head tilted back a little."
- Gum carton: "She opens the flap at the end of the carton, slides one piece out of the opened end
  and closes the flap."
- The one exclusion that names this product's wrong use: "He drinks only through the spout; the
  bottle has no other opening." / "The can is drunk only from its opened top."
- When the model rebuilds the action from a reference (≈, ✗), write the source's own use the same
  way. A swapped product with a different opening gets a **planned grip and contact** that keeps the
  source hand path (`generation-system.md` §5c.4).

**QC.** Densify every use beat at 30 fps, from the reach to the release, and check frame by frame:
the opening step happened and the part stayed in that state; the lips, hand or finger are on the
right part; the object's orientation fits the use (a straw bottle nearly upright, a can tilted);
the other parts are where they belong (the strap on the lid, the cap flipped, the tab up).
- **Regenerate** when the use goes through the wrong part or a closed one, or when the preparation
  step is missing and the use still happens.
- **Retry:** add the sheet's opening sequence and contact point in the model's wording; add the
  exclusion; bind an asset view that shows the part ready (a photo with the cap flipped open, the
  tab up); for a start-frame model, build the start frame with the part in its ready state.

### 2.3 Preparation and causality (cause before effect)

**Rule.** The preparing action comes first and is visible; the effect follows it by the right
amount; nothing reacts before its cause.

**Breaks.** The glass is full before the pour. The can is open at frame 0 although it is cracked at
3 s (seen 2026-10: an open-tab reference image leaked the state). The boy drinks milk before the
mother pours it. The jaw chews before the piece goes in. The face reacts to the taste before the
sip. The lid flips by itself. A product turns label-forward on its own. The hand closes on a product
that is still on the table. The wrapper is torn before being touched. A laptop screen lights before
the lid lifts. The car moves before the driver is in.

**Ledger.** Every state change has an **event** cell naming its cause and the hand. A row whose
cause is missing is an error in the plan.

**Prompt.** Write each change as cause → effect in one sentence, in order; never the effect alone:
"The mother unscrews the lid, pours milk from the carton into the bottle until it is three-quarters
full and screws the lid back on. Then she hands it to the boy." Restate the ready state right
before the use ("the bottle, now three-quarters full of milk, …"). State the initial state
explicitly at t=0 ("sealed, tab flat").

**QC.** On the dense sheet of every state change, find the cause frames before the effect frames. A
state present at the first frame that the plan opens later (the raised tab) is a break even when
the rest is right.
- **Regenerate** when an effect has no cause or precedes it.
- **Retry:** write the t=0 state, remove any reference image that shows the later state, write the
  cause.

### 2.4 Irreversible and persistent states

**Rule.** Opened, torn, bitten, poured, spilled, wet, lit, broken, written, peeled, chewed and
swallowed stay so. A lid, cap, door, zip or switch keeps the state it was left in. Levels move in one
direction between causes.

**Breaks.** A can that reseals. A torn pouch whole in the next shot. A bite mark gone. A spill dry a
second later. A glass refilled. A straw back in its hole. A lid open in one shot and closed in the
next with no hand. A written note blank again. A half-peeled banana whole. A phone screen dark,
lit, dark. Condensation that vanishes; foam that regrows. A light switched off that is on after the
cut. A car door open, then closed by nobody.

**Ledger.** After an irreversible event the state cells stay identical to the end (copied forward).
Read each row left to right for any reversal.

**Prompt.** Carry the state forward in the next stage's opening words ("Continuing with the can
open and the tab up, …"); the end state names every irreversible state ("the pouch stays torn open
on the table"); every multi-clip hand-off state lists them.

**QC.** Compare the state at each cut, each re-entry and the last frame with the ledger; densify
any stretch where a state looks different for even one frame (a tab that flickers).
- **Regenerate** on any reversal. **Post-fix** a one-frame flicker only when a trim removes it
  without harming a beat.

### 2.5 Object permanence: exits, occlusions, pans and cuts

**Rule.** What the camera stops seeing is still there, unchanged, when it sees it again. The same
holds for what a body, hand, door or passing object hides for a moment.

**Breaks.** The capsule case. A pouch that dissolved while an arm passed (2026-10). A can gone when
the character leans over it. A glass missing after a pan. A product on the desk in shot 1 and on the
chair in shot 3. A bag strap that changes shoulder. A poster that changes. A mirror that shows an
empty table. A shadow that stays after the object moved.

**Ledger.** An **in-frame?** mark per row for the anchor ("out of frame 4.0–7.5 s, unchanged"), so
the restatement at re-entry is planned.

**Prompt.** Say the item stays while it is out of view, and name the re-entry state: "He walks out
of frame to the right; the three capsules stay on the desk. When he steps back into frame, the
same three capsules are on the desk where they were." Across cuts: "Shot 3 shows the same desk with
the same three capsules." Occlusion: "His arm passes in front of the pouch; the pouch stays where
it is, unchanged."

**QC.** For every exit and re-entry, pan-away and pan-back, occlusion and cut, compare the frame
before and the frame after at 15 fps: count, spot, state, size, label orientation; reflections and
shadows where present.
- **Regenerate** on a changed count, spot, state or size. **Post-fix** (a pixel hold) only for an
  untouched static anchor in a locked shot.

### 2.6 Liquids, powders and materials

**Rule.** Liquids keep a level surface, slosh with motion, pour in an arc from the opening, are
conserved, show through transparent vessels and not through opaque ones, foam and then settle, and
look like what they are: milk opaque white, a sparkling drink clear with rising bubbles, coffee dark.
Cold things sweat; hot things steam. Ice floats. Cream absorbs over seconds; powder dissolves when
stirred.

**Breaks.** Milk that looks like water. A level tilted with the bottle. A pour from a closed cap. A
stream that starts in mid-air. Foam that regrows. An opaque can showing its level. A level that
rises on a tilt. Ice that sinks. Steam from a cold drink, condensation on a hot one. A dollop still
on the skin after rubbing. Powder visible after stirring. Bubbles rising in a flat drink. A drink
that changes colour between shots. The contents sample leaking into the vessel's material (a blue
tumbler turned into a clear glass, 2026-10).

**Ledger.** The level column with the amount ("¾ full") and "visible? (transparent / opaque)".

**Prompt.** Bind the contents to the sample (`generation-system.md` §4b.5) with colour, opacity and
bubbles, and bind it to the liquid only ("only the liquid of @ImageN, not its glass"); state the
level and its change; for a pour name the source, the opening, the stream and the result; keep the
temperature cues consistent ("cold: fine condensation on the can; no steam").

**QC.** Read the level and colour in transparent vessels at each checkpoint; densify pours and sips
at 30 fps; check that the surface stays horizontal when the vessel tilts.
- **Regenerate** on wrong contents (§4b.0, §9: water beside the can), non-conserved amounts, or a
  physics break in a pour. A slight colour drift between shots can be a **post-fix** (a recolour in
  a locked shot) when nothing else is wrong.

### 2.7 Scale and proportion (the size reckoning)

**Rule.** The product keeps its real size relative to hands, faces, furniture and the other
products, at every depth and in every shot. Its size in the frame is **reckoned, not guessed**:
from its real dimensions in the registry, its distance from the camera, the lens, and the known
sizes of what stands beside it. A product that reads too big reads as a paste (§2.15), as an ad
(`generation-system.md` §4b.2) and as a wrong world, however well it is drawn.

**Breaks.** A gum pack at 23 % of the frame height (2026-10). A sachet two to three times its real
size. A can taller than a forearm. A child's bottle adult-sized in his hands and tiny on the table.
A phone that grows when lifted. A car shorter than the person beside it. A product that changes size
across cuts. A glass larger than the can that filled it. A false flag is a break of the check, not of the video: a can
standing under a metre from the lens was measured against an assumed 1.5 m and read as 2.8× its size
(1.07× by eye; CE-028), and the same assumption may sit under other flags of that run.

**Ledger: the size reckoning,** one line per product per shot, written in the plan from these
inputs:
1. **Real dimensions** from the registry's affordance sheet (height × width or diameter × depth,
   and volume as a check). The registry takes them from the supplied specs; when none are
   supplied, from the category's standard size, marked [I] (table below), never from how large the
   product looks in its own photo (a packshot fills its frame).
2. **Depth**: the product's distance from the camera in metres. **Never assumed; derived from the
   frame** (CE-028). Take it from, in this order: (a) the surface the product stands on, read off the
   frame (a fold-out desk at the lens is under a metre; a dresser behind the subject is farther than
   the subject); (b) a same-plane neighbour of known size, `d = neighbour_m · f / (36 · neighbour_fraction)`
   (a head 23 cm, a hand 18 cm, a laptop 33 cm wide, a bottle); (c) the depth order from the occlusions.
   Write the basis in the plan next to the number ("0.85 m: from her head, 23 cm = 250 px, f 26"). The
   shot-size distances (extreme close-up ≈ 0.4 m, close-up ≈ 0.7, medium close-up ≈ 1.0, medium ≈ 1.5,
   medium-wide ≈ 2.5, wide ≈ 4) are priors for sketching a plan before any frame exists, never for a
   verdict. Recreate: the source frame exists, so the plan derives the distance from it. Create: the plan
   states the blocking it asks for, and X9 re-derives the distance from the output.
3. **Lens**: the 35 mm-equivalent focal length the look implies (a phone's main lens ≈ 24–26 mm,
   a "cinematic" look 35–50 mm, a long portrait look 85 mm).
4. **Expected size in the frame**: in a 9:16 frame, the frame height covers about `36 · d / f`
   metres at distance `d` for focal length `f`, so a product `H` metres tall fills `H · f / (36 · d)`
   of the frame height. A 15.7 cm slim can at 1.5 m through a 26 mm lens fills ≈ 7.6 % of the
   frame height (≈ 97 px of 1280); at 2.5 m ≈ 4.5 % (≈ 58 px); only at 0.5 m does it reach 23 %.
   `atg.py scale --product-cm 15.7 --distance 1.5 --lens 26` computes it and prints the table over
   the usual shot distances.
5. **Neighbours**: for every object of known size that stands near the product, the expected
   ratio (`H_product / H_neighbour`), corrected by the depth ratio when they are not at the same
   depth (an object twice as far looks half as big). Name the one neighbour the prompt will use.
6. **The size ladder** when a run places several products: their real sizes relative to each
   other, in one line ("bottle 22 cm : can 15.7 cm : gum carton 7 cm ≈ 3 : 2 : 1"), kept in every
   shot that shows two of them.
7. **Constancy**: the size the product must keep while it, the camera or the subject moves, and
   the size it must have again after every exit, occlusion and cut (§2.5).

Standard sizes for the reckoning (use the registry's spec when it exists; these are [I] fallbacks
and comparators):

| thing | about |
|---|---|
| adult hand, wrist to fingertip · palm width | 18–19 cm · 8–9 cm |
| child's hand (6–8 y) | 13–14 cm |
| adult face, chin to hairline · whole head | 19–20 cm · 23 cm |
| forearm · shoulder width | 25–27 cm · 40–45 cm |
| standing adult · child (6 y) · seated adult (seat to crown) | 165–180 cm · 115 cm · 85–90 cm |
| slim 250 ml can · slim 355 ml can · standard 330 ml can · 500 ml can | 13.4 × 5.3 · 15.7 × 5.8 · 11.5 × 6.6 · 16.8 × 6.6 cm |
| 500 ml PET bottle · 1 l sports bottle · wine bottle · mug | 22 × 6.5 · 24–26 × 7–8 · 30 × 7.5 · 9.5 × 8 cm |
| phone · earbud case · laptop (13–15") · keyboard | 15 × 7 · 5 × 6 · 30–36 wide, under 2 thick · 44 cm |
| gum carton or stick pack · blister card · capsule bottle | 7–8 × 2–3 · 8 × 5 · 10 × 5 cm |
| desk or table top · chair seat · sofa seat · sofa arm | 72–76 · 45 · 42 · 60 cm high |
| bed top · dresser top · kitchen counter · window sill | 50–60 · 75–90 · 90 · 90 cm high |
| door · door handle height · fridge · dinner plate | 200 × 80 · 100 · 170–180 · 27 cm |
| compact car · bicycle wheel | 4.2–4.6 m long, 1.45 m high · 70 cm |

**Breaks, named by the reckoning.** The can on the dresser: a 15.7 cm can at ≈ 2.5 m should fill
about 4–5 % of the frame height and stand two thirds the height of the 22 cm bottle beside it; it
filled over 12 % and stood taller than the bottle, which puts it either at 0.9 m from the camera
(in front of the boy, where it is not) or at 40 cm tall. Either reading is a wrong world.

**Prompt.** Put the reckoning into the model's own structure (its guide §3.14):
- the size **against the named neighbour at the same depth** with the ratio in words ("two thirds
  the height of the water bottle beside it", "shorter than his hand is long");
- the **depth** ("on the dresser about two and a half metres from the camera, behind the boy");
- the **fraction of the frame** when the model takes it ("it fills about one twentieth of the
  frame height, a small object in the background");
- the size ladder when more than one product shows;
- **constancy** ("it keeps this size as he turns", the model's "no scale drift" line);
- the reference scoped to shape, proportions, colours and label only (§2.15), **padded** so the
  product does not fill its reference image (a tight crop pulls the product forward and up in
  size), and never a reference image that shows the product larger than a hand that holds it;
- for a start-frame model, **build the start frame at the reckoned pixel height** and check it
  with `atg.py scale --frame <start.png> --product-px <y0-y1> --ref-cm … --ref-px …` before
  animating; a wrong start frame is animated faithfully wrong.
- A stylised video keeps the same ratios: an anime can is still one hand tall; a stylised frame
  may simplify, never resize.

**QC.** On one full-resolution frame at rest, one in use and the last frame, measure the product's
pixel height and the pixel height of the named neighbour (or a hand or face) at the same depth, and
run `atg.py scale --product-cm <H> --product-px <y0-y1> --ref-cm <h> --ref-px <y0-y1>
[--depth-ratio r] [--distance d --distance-basis "<how d was derived>" --lens f]`. The tool does
arithmetic only: for each estimate it can make it returns `size_factor` (the observed size as a multiple of the
expected size) and `deviation_pct`, with two estimates also `estimates_spread_pct`, and it records the distance
basis as given; it prints no verdict. You read the numbers with the rules of thumb below (guidance, not enforced by
the tool: depart from them when the evidence says so, and write down what you applied or set aside and why), and
write the observed multiple of the expected size in the verdict ("renders at 2.6× its expected size vs the
bottle"). Compare across shots and after every cut for constancy. The same measurement is the "scale" sign of the
paste test (§2.15).
- **Two independent estimates should agree before you call a size oversize** (CE-028; CE-005, CE-014, CE-015):
  (A) the ratio to a named same-plane neighbour (`--ref-cm/--ref-px`), and (B) the expected fraction of the
  frame height from a distance derived from a different object or the surface (`--distance` with
  `--distance-basis`). Rule of thumb: they agree when the two multiples are within 25 % of each other
  (`estimates_spread_pct`); when they are further apart the reading is inconclusive, and nothing is flagged
  until the distance and the neighbour are re-derived on the full-resolution frame.
- **A size from one assumed number is provisional** (your word; the tool does not label it). A `scale` call with
  `--distance/--lens` and no neighbour gives one estimate from a distance that may be an assumption. A
  provisional reading is not a regenerate reason until a second estimate agrees, not a RESIDUAL FAILURE, and is
  never repeated or summarised. Whoever reports a size (the production agent
  and the main session alike) first views the full-resolution frame, checks that the rows measured are the
  product and the neighbour, and re-measures when the eye disagrees with the number.
- **The verdict line records the method:** the multiple vs the neighbour (A: product px / neighbour px ×
  cm), the multiple vs distance (B: d, its basis, f), and whether the two agree. When the user's eye
  disagrees with a flag, it is re-measured, not defended; the other flags that rest on the same
  assumption are re-measured too.
- **Accept** within 15 % (`deviation_pct`). **Note** between 15 and 25 % when the product is static, the label
  stays readable and nothing else fails (the sachet case).
- **Regenerate** over 25 %, or when the size changes between shots or across a cut, or when a
  product is larger than a hand that holds it when it should not be. There is **no post-fix**: a
  punch-in cannot shrink a product in its scene.
- **Retry:** the lever depends on the model. For a start-frame model, rebuild the start frame at the
  reckoned height. For a reference model whose guide lists size as a model limit (`wan3_0_prime`:
  `wan-3-0.md` §5), a wording retry on that product form is a re-roll: sizing words did not move a flat
  pack against a same-plane neighbour (CE-009, CE-011). The one retry changes the form or the anchor
  class from the guide's passing list, or none is spent and the best take ships flagged and recorded.
  The guide holds the numbers and the forms its evidence covers; cans measured against a person's head
  are unproven (CE-014, CE-015). For any other model: name the neighbour and the ratio, the depth and
  the fraction of the frame, pad the reference and add the constancy line.

### 2.8 Body mechanics at the product

**Rule.** People use things with the body a real person would. The head tilts back for a can or a
bottle without a straw and stays level with a straw. Lips close around the spout. The jaw chews after
the piece is in; nobody speaks clearly with a full mouth; a swallow follows. A child holds a large
bottle with both hands. Fingers wrap the real shape and never pass through it. The free hand does
what the story needs, not a second copy of the product.

**Breaks.** The head tilted back on a straw. Drinking with the mouth closed. Chewing with nothing
taken. A mouthful of dialogue. A piece that appears on the tongue. A child one-handing a litre
bottle. Fingers through the can. The product held while both hands gesture. A sip with the can
upright. The hand changes mid-shot. A swallow before the sip.

**Ledger.** The holder-and-hand column; the mouth state at each sync anchor.

**Prompt.** Name the hand and the mouth: "he drinks through the straw with his head level"; "she
tilts the can and her head back a little"; "mouth closed while chewing; he speaks only after
swallowing"; "both of the boy's hands around the bottle".

**QC.** On the 30 fps sheet of each use beat: the head angle for that vessel, the lips on the part,
the jaw, the number of hands and what each holds, the finger wrap.
- **Regenerate** for a wrong-part use, a missing mouth action, pass-through fingers, or a second
  product in the other hand.

### 2.9 Orientation, label and parts

**Rule.** A product's label, markings and parts belong to its body: they move with it, stay upright
when it stands, never mirror, never rotate on their own, never multiply. The flavour and variant stay
the same.

**Breaks.** Artwork rotated 180° toward the character (2026-10). A mirrored wordmark. A label that
turns around the can while the can stands still. Time markers out of order on the bottle. A strap
that jumps from the lid to the base. Two straws. Watermelon becoming Peach after a cut. The can's
wordmark printed on the tumbler (2026-10).

**Ledger.** "Mark orientation" in the anchor row ("label ~30° to camera, upright").

**Prompt.** State the orientation and that it moves with the body ("the label reads upright and
faces the camera; it tilts with the bottle when he drinks"); bind the artwork to its image; "the
same flavour throughout"; "the strap stays on the lid's loop".

**QC.** Read the label on the first and last frame and at every rest; check the text direction on a
full-resolution frame (`T frames <video> --out <dir> --at <t> --max-side 1280`); check the parts
count and attachment on every use beat.
- **Regenerate** for a mirrored, rotated, migrated or changed label or part. A brief soft label at
  small scale while gripped is a **note**, or a **post-fix** when a punch-in removes it.

### 2.10 Ownership and hand-offs (two or more people)

**Rule.** After a hand-off the giver's hands are empty and the receiver holds the item in the state
it was given. Each person's own item stays theirs. Counts match the number of people and the story.

**Breaks.** The mother still holds the bottle after giving it. Two bottles after the hand-off. The
bottle empty in his hands and full in hers. A shared can in both people's hands at once. The friend's
can becomes the subject's. A second identical product appears for the second person without a
source.

**Ledger.** The holder column names the person on every row.

**Prompt.** "She hands the bottle to the boy; after that, only the boy holds it and her hands are
empty." State the count per person.

**QC.** Densify the hand-off at 30 fps; count the items after it; check each person's hands.
- **Regenerate** for a duplicated item or a stale holder.

### 2.11 Environment, context and suitability

**Rule.** Objects live where they live and move as the world allows: a car on a road or driveway
with its wheels on the ground, entered by the driver's door; a fridge door on its hinge; the desk
lamp lights the desk; the window's light keeps its direction and colour; a clock and the weather
move only as time really would; dropped things fall; leaning things stay or fall, never float; a
kid stays a kid, with kid-sized things. A product goes to the person who would really use it: no
energy drink or supplement for a child, no baby bottle for an adult, a car driven by an adult
(`generation-system.md` §4b.0 "when not to").

**Breaks.** A car in a living room. A fridge door swinging from the wrong edge. A shadow against the
key light. Window light changing colour mid-scene. A clock that jumps. A floating bottle. A product
sinking into the table. A shadow without an object. A strap hanging sideways. Rain that stops at a
cut. The child drinking the energy drink that was placed for the parent.

**Ledger.** The scene's constants (light direction, surfaces, the set) in the plan §2.4 and an
environment row in the ledger; the user of each product in the roles table.

**Prompt.** The scene's constants stated once and carried into every stage; placed objects on their
surface with a contact shadow (`generation-system.md` §4b.4); who uses what.

**QC.** On each sheet: the light direction and contact shadows, the surfaces under objects, the
room's constants across cuts, who holds and uses each product.
- **Regenerate** for floating, sinking, moving decor, a light change, or the wrong user. A small
  constant colour drift can be a **post-fix**.

### 2.12 Timing of real processes

**Rule.** Real actions take real time: a sip 1–2 s, a long drink 3–5 s, pouring a glass 2–4 s,
unwrapping 1–2 s, a bite about a second plus chewing, a pump press or a lid flip under a second, a
cream absorbing over several seconds. Nothing freezes mid-action or completes within a frame.

**Breaks.** A glass filled in a third of a second. A single 6 s sip. A frozen pour. A lid both
closed and open across one frame. A chew that never ends. A spin that stops early (2026-10). The
same sip twice (a repeated cycle).

**Ledger.** The time budget's beat durations (Recreate: from the family profile; Create: from the blend's planned beats) and
the process's real duration.

**Prompt.** "Real-time speed"; one process per stage with its natural duration; never a timestamp
on free motion (`generation-system.md` §5b).

**QC.** The dense sheet of the process: continuous progress at a natural duration; the freeze starts `T qc` lists
are pointers to look at on the sheet.
- **Regenerate** on frozen, impossibly fast or repeated processes. **Post-fix** (trim) a dead tail.

### 2.13 Stylised and anime rendering

**Rule.** A style changes how things are drawn, not what they do. An anime bottle is still drunk
from its spout; three capsules are still three; milk is still opaque. The family's visual language
(sweat drops, speed lines, sparkles, a held frame, a chibi cut) is allowed where the references use
it, and is never a reason to accept a count or affordance break.

**Tendencies of stylised output.** Small items drop out or double between held frames. A label loses
its words. A mouth is drawn on the near side of whatever is held, spout or not. Held frames hide
snaps, so the dense sheet is read for the exact frame where a state changes. Limited animation
repeats a cycle (the same sip twice). Exaggeration grows the product. Simplified hands pass through
objects.

**Prompt.** The affordance sheet and the counts in full, as for live action, plus the style: "drawn
in the style of the references, with real proportions and the real use of the bottle". For a held
frame say what stays identical ("the three capsules stay drawn in the same spots").

**QC.** The same checkpoints, with extra attention to held frames (compare the first and last frame
of each hold), to the count of small items, and to the mouth's position on the object.

### 2.14 Solidity, collision and occlusion

**Rule.** Solid things exclude each other. A moving thing that meets a solid stops, deflects,
bounces, slides along it or lands on or against it, and the thing it meets reacts according to its
weight: a crumpled paper hitting a bottle leaves it standing or rocks it, a hand knocks a can over,
keys dropped on a pack push it a little. Opaque bodies hide what is behind them, and whatever is
nearer the camera hides what is farther, in that order and in that order only. Nothing sinks into a
surface, a hand or a body, and nothing is seen through something that is opaque.

**Breaks.** A tossed crumpled paper flies straight through the client's bottle (the case). A ball
passes through a can. Keys dropped on the pack land inside it. A hand or a finger goes through the
product or the product through the hand. A sleeve, a strap, hair or a scarf passes through the
bottle. A door closes through a person; a person walks through a chair or a table edge. The
product sinks into the table, the sofa arm or a palm. A sticker, a label or a shadow is seen
through the body. The product shows through the arm that should hide it, or stays fully visible
while a hand passes in front of it. A thrown thing hits the product and the product does not move,
or the product moves before the thing arrives. Two objects occupy the same spot after a cut. A
glass of drink sits half inside the can beside it. A phone slides into a laptop. Rain or a spill
goes through a closed lid. A car's wheel passes through the kerb; a bike leans through the wall.
A carton resting on the corner of an exam sheet doubles and warps the sheet's corner while the hand
writes (CE-006, 2026-10): two surfaces fight for one space, so the pack goes on the bare surface (§2.16).

**Ledger.** Every thrown, dropped, swung, rolled or carried thing that passes near the product (or
near any other tracked object) gets a **path row**: where it starts, the side it passes on or the
point where it lands, what it touches, and what reacts; and every tracked object gets an
**occlusion note** at the moments something passes in front of or behind it.

**Prompt.** Write every path relative to the solid things it passes (positive first, then the one
exclusion): "He tosses the crumpled paper; it arcs past the bottle on its far side and lands behind
it on the desk; the bottle is not touched and does not move." Or, with contact: "The paper hits the
can, bounces off it and drops to the desk; the can rocks once and settles upright on the same spot."
Occlusion: "His arm passes in front of the bottle and hides it for a moment; the bottle is seen
again behind the arm, unchanged." Contact with a surface: "the can stands on the desk with its
whole base on the wood". In the model's exclusion syntax: "nothing passes through the bottle; the
bottle is solid and opaque". For a stylised video, the same lines; a drawing is still solid.

**QC.** Densify at 30 fps every moment a thing passes near, in front of or behind the product, and
every landing or hit: check that the moving thing's silhouette and the product's never overlap in a
way that only a transparent body would allow, that the occlusion order matches the depth, that the
contact has its consequence (a rock, a knock, a bounce, a stop) and that nothing reacts before the
contact. Check the base of every placed object against its surface and every grip for
interpenetration on at least two sheets.
- **Regenerate** on any pass-through, sinking, see-through, wrong occlusion order, or a hit
  without a consequence. There is no post-fix: the motion is the error.
- **Retry:** write the path relative to the product with the side and the landing spot, name the
  contact and its consequence, add the solidity exclusion, and move the product's anchor out of
  the throw's or the hand's natural path when the story does not need the contact.

### 2.15 Blend: a render, not a paste

**Rule.** A placed or swapped product is part of the same photograph as everything around it: the
same key light and colour temperature, the same exposure, the same focus and grain, the same
camera height and lens, at its real size against its neighbours, standing a little inside the
surface with a contact shadow that falls the way the neighbours' shadows fall, turned a little like
a thing someone put down, and occluded by whatever stands in front of it
(`generation-system.md` §4b.2, §4b.4).

**The paste test (what a paste looks like).** Any one of these, and the product reads as an edit:
1. **Exposure and white balance:** its whites are brighter or cooler than the nearest white
   object (a door, a box, a wall), its colours more saturated than anything in the room.
2. **Light direction:** it is lit evenly from the front while the room's light comes from a lamp,
   a window or the ceiling and shades every other object.
3. **No contact shadow,** or a shadow that falls another way than the neighbours' shadows.
4. **Sharpness and grain:** it is crisper and cleaner than objects at the same depth.
5. **Packshot pose:** squared to the lens, perfectly upright, label centred, as in its reference
   image.
6. **Perspective:** its top and base ellipses do not match the camera height (a can drawn
   straight-on in a room seen from below or above); its verticals do not follow the room's.
7. **Scale:** larger or smaller than its real size against the objects beside it (the affordance
   sheet's size by comparison).
8. **Edges:** a hard, haloed or cut-out outline; no reflection or colour spill from the
   surroundings on glossy or metallic parts.
9. **Footprint:** it stands on the very edge of the surface, overlaps a neighbour's footprint, or
   floats a little above the surface.
10. **Depth of field:** sharp while its plane is soft, or soft while its plane is sharp.
11. **Prominence:** it is the brightest, most saturated or most centred thing in the frame.

**Breaks.** The dresser can (the case). A pouch brighter than the laptop it stands beside. A car
with studio reflections on a cloudy street. A phone whose screen glows in a sunlit room. A gum
carton crisp on a soft-focus table. A bottle whose label faces the lens while the character sees
its side. A can standing on the back edge of a shelf with half its base in the air. A product with
the reference photo's white background shadow under it. A can rendered at the reference's
exposure in a night scene, glowing on its own.

**Causes, by what leaked.** The product reference's **studio lighting, exposure and background**
inherited into the scene; the reference's **camera angle** inherited instead of the scene's; a
**tight product crop** pulling the product to the foreground and up in size; the **anchor** chosen
on an empty, unoccluded, edge-of-surface spot where nothing in the scene touches or shades it; the
prompt describing the product's look but not the room's light on it; a start frame checked for
geometry but not for blend.

**Ledger.** The anchor row carries the blend facts: the key light on that spot (direction, colour,
dimness), the neighbour it is scaled against, the neighbour whose shadow it copies, what partly
occludes it, and the angle of its mark.

**Prompt.** Scope the reference and describe the room's light on the product, never the product's
own light:
- "@Image2 defines only the can's shape, proportions, colours and printed label; do not use its
  lighting, exposure, background, shadow or camera angle."
- "The can stands on the dresser a little inside its front edge, to the left of the bottle and
  slightly behind it, about a third shorter than the bottle, its label turned about thirty degrees
  away from the camera. It is lit by the same warm, dim ceiling light as the dresser and the
  bottle: a soft highlight on its upper left, its right side in shadow, its colours as muted as the
  room's, a soft contact shadow under it falling to the right like the bottle's. It is seen from
  the same low angle as the dresser, with the same grain and focus as the bottle."
- For a model that composites easily, choose an anchor that forces integration: partly behind a
  neighbour, touching another object, inside the lamp's falloff, never alone on an empty edge.
- The exclusion in the model's syntax: "no studio lighting on the can, no cut-out edges, no glow;
  the can is not brighter than the room".
- Start-frame models: the frame is checked with the paste test before it is animated. Reference
  models: pad tight product crops; if a photo of the product in a real room with directional
  light exists, bind it for lighting only ("use the light of @Image3, not its room").

**QC.** On one full-resolution frame at rest and one during any interaction, compare the product
with its nearest neighbour at the same depth, point by point through the eleven signs above:
brightness and warmth of its whites against the nearest white object, shadow direction against
the neighbour's, sharpness and grain, label angle, ellipse geometry against the camera height,
height against the neighbour per the affordance sheet, edge quality, footprint. Write the result
in the verdict ("whites +1.5 stops over the door, no contact shadow, 2.4× the bottle: paste").
- **Regenerate** on any sign of a paste; it is the §4b "looks pasted in" reason. The retry fixes the
  named cause: scope the reference's lighting, write the room's light on the product, give the
  size against a neighbour, angle the mark, move the anchor into contact or partial occlusion,
  pad the crop, rebuild the start frame.
- **Post-fix** only for a static, untouched product in a locked shot whose only failing sign is
  exposure or warmth: a local regrade of the product's pixels to match the neighbour. Never a
  post-fix for size, angle, perspective, shadow or edges.

### 2.16 Posture, support and place

**Rule.** A placed or carried product takes the posture its shape allows, rests on something that is
visibly there and fixed (a counter, a desk, a grill's side shelf: a natural surface the source frame shows,
never a prop that moves or is carried away, never a lean; CE-021), and sits where a person would really
leave it. A flat sachet or pouch lies flat, label up;
a carton lies flat or stands on its base; a can stands on its base. Nothing leans on a prop the model has
to invent, nothing stands on its edge against a person, and nothing rests on or overlaps a thin sheet that
hands move or write on. A placed product never takes a beat of the source (the pick-up, the use) that
belongs to another object.

**Breaks.** A flat sachet stands upright against a writer's forearm (CE-012). A carton "leans" on a
notebook that renders as a sliver at the frame edge, so it tilts back against nothing (CE-013). A carton
lies on the corner of an exam sheet; from 6 s the sheet's corner doubles and warps while the hand writes
(CE-006). The placed pouch takes the bottle's pick-up beat (CE-007). A sachet planned to lie flat on a
grill shelf renders propped against the grill front, a carton planned flat renders upright (run 09, V11 and
V12). A sachet leans against the grill front while the grill's side shelf, a natural surface the source
shows, was free (CE-021); the retry that moved it onto the cutting board put it on a prop that is carried away.

**Ledger.** The anchor row carries the posture (flat / on its base / in hand), the support (bare surface or
a named solid object that is in frame), the clearance to the nearest working hand, arm or sheet, and the
story reason in one clause ("set down at the near edge, out of the writing hand's way").

**Prompt.** Posture, support and reason as one chronological sentence, positive first, with its exclusion
in the model's syntax: "lies flat on its wide face with its printed label facing up, resting entirely on
the bare marble at the near edge of the table, a band of bare marble at least as wide as itself between it
and his forearm, where someone sets a sachet of gum down out of the way of their writing; it never slides,
tilts, stands up or leans" with "no standing, leaning, propped or tilted sachet, no sachet on its edge, no
sachet on a sheet, no sachet touching his arm" (CE-012, verified). A support is bare surface or a large
solid object the source frame shows. Name the object that is picked up and say the product stays where it
was.

**QC.** At 30 fps across every rest and every pass of a hand or sheet: the posture (flat or on its base, no
tilt, no float), the support (the whole underside on a visible surface or solid, with its contact shadow),
the clearance to a working hand or arm (touching is a regenerate reason; a gap under about half a
hand-width is a note, CE-012's accepted take had about 0.2), the sheet region for the whole shot when paper
is near, and the story reason written as its own line of the verdict.
- **Regenerate** on a lean against nothing, a posture the shape cannot take, a pack touching a working hand
  or arm, a doubled or warped sheet, or a source beat taken over. No post-fix.
- **Retry:** re-plan the posture and the place (flat on bare near-side surface, on the fixed natural surface
  the source shows, or in hand) and drop any prop the model has to invent or that moves; the sizing words
  are not the lever (§2.7).

### 2.17 Identity: the swapped face matches the kept body (skin tone, build, age)

**Rule.** When the source video rides as the video reference, the model keeps the source performer's
body, hands, forearms, neck and posture and replaces only what the identity image names. The identity
image is therefore chosen to fit the kept body: the same skin tone and undertone, apparent age and
build. A lighter face on a darker body (or the reverse) is a regenerate reason (CE-029).

**Plan.** Pick the character from the supplied set by comparing it with the source performer's skin
tone, hair and build, and state the pick and the match in the plan; never take the next unused
character without that comparison.

**Prompt.** One sentence in the Core Task: his face, neck, hands and forearms share the same skin tone
as the hands and body of the man (woman) in Video 1, one consistent skin tone from face to fingertips,
plus an exclusion against a face lighter or darker than the hands.

**QC.** On a full-resolution frame with the face and a hand or forearm together, compare their tone and
write the observation and the frame path in the verdict (agents record "skin tone face vs hands: match,
frame <path>"); an unchecked item counts as failed. **Regenerate** on a visible mismatch; no post-fix.

## 3. The prompting stack (in order, per video)

1. **Affordance sheet** (§1) for every product and object in the registry, before any plan.
2. **Ledger** (`generation-system.md` §3) with the columns count, opening/lid state, level, holder
   and hand, contact point, in-frame?; one row per event, each with its visible cause.
3. **Use beats** written as initial state → operation on the named part → observable result, with
   the contact point (§2.2, §2.3), the product's size from its **size reckoning** (§2.7: against a
   named neighbour at the same depth, its depth, its fraction of the frame, the size ladder,
   constancy) and the body mechanics of that use (§2.8), in the locked model's phrasing (its
   guide §3.14). Every thrown,
   dropped, swung or passing thing gets its path relative to the product: past it on a named side,
   or onto it with the consequence, plus the solidity exclusion (§2.14).
4. **Restatements**: the count and state of every tracked item right after each exit, re-entry,
   occlusion, cut, hand-off and seam (§2.1, §2.4, §2.5), and in every multi-clip hand-off state.
5. **Contents** bound to the sample and to the liquid only, with levels and conservation (§2.6).
6. **One targeted exclusion per product**, naming its own wrong use and its count ("drunk only
   through the spout; no other opening", "exactly three capsules; none appears or disappears"), in
   the model's exclusion syntax. A generic list never replaces it.
7. **References**: when the model takes images, one view that shows the part in its ready state;
   never a view that shows a later state than t=0 (an open tab for a can cracked on screen); tight
   product crops padded small.
8. **QC checkpoints** listed in the plan: every use beat, exit and re-entry, occlusion, cut,
   hand-off, pour and seam, plus the first and last second, each with its time range and the counts
   and states expected there. They become the `--dense` arguments of X9.

## 4. The QC stack (X9, in order)

1. `T qc --video <final> --out <dir> --mode <mode> --allowed-text "…" --dense "<label>:<a>-<b>" …`
   with every checkpoint of the plan: it writes a 30 fps sheet per checkpoint under `<dir>/dense/`
   beside the 5 fps storyboard, and returns measurements beside the expected values (duration, aspect, size,
   audio, black spans, freeze starts, and `planned_text` beside the `visible_text` its OCR saw), with no pass or
   fail. View every sheet, read the numbers, and write the verdict yourself. Rules of thumb for the numbers: a
   duration off by more than max(0.25 s, 5 %) is a duration problem; any black span or freeze needs a look at the
   sheet; Edit Mode: no source text may remain unless the user kept it; Analyze Mode: only the planned text may
   appear, anything else is pseudo-text or a copied artifact.
2. **Count** every multiple at every checkpoint and write the numbers in the QC note
   ("capsules 3 / 3 / 3 / 1, two taken at 7.5 s").
3. **Part and contact** on every use beat: the preparation step, the part used, the lips or hand on
   it, the orientation, the head angle, the other parts (strap, cap, tab).
4. **States** across the ledger: no reversal, no effect before its cause, levels monotonic between
   causes, contents right.
5. **Permanence** before and after every exit, occlusion, cut and seam: count, spot, state, size,
   label orientation; reflections and shadows.
5b. **Solidity** at 30 fps wherever anything passes near, in front of or behind the product, lands
   on it or hits it: no pass-through, no sinking, no see-through, the right occlusion order, and a
   consequence for every contact (§2.14).
5d. **Size** with `atg.py scale` on a full-resolution frame at rest, one in use and the last:
   the product's pixel height against the named neighbour's at the product's own depth (A; `--depth-ratio` is
   read from the frame when the product stands in front of or behind that neighbour, a can on the near table
   strip against the person seated behind it, and is never left at 1; CE-014, CE-015) and against a distance derived from the
   frame (B, `--distance-basis`), the two multiples agreeing (within 25 % of each other) before you call a size
   oversize, the observed multiple of the expected size and the method written in the verdict, constancy across
   cuts; a size from one assumed number is read as provisional and is viewed on the frame first (§2.7; the tool
   returns numbers only).
5e. **Identity match** on a full-resolution frame with the face and a hand or forearm: same skin tone, age
   and build as the kept body, with the frame path in the verdict (§2.17; CE-029).
5c. **Blend** on one full-resolution frame at rest and one during any interaction: the eleven-sign
   paste test against the nearest neighbour at the same depth (§2.15).
5e. **Posture, support and place** at 30 fps across every rest and every pass of a hand or sheet: the
   posture, the whole underside on a visible support, the clearance to a working hand or arm, the sheet
   region when paper is near, and the story reason as its own line (§2.16).
5f. **Anchor tracking** (CE-018, CE-019): a placed or contents product is in frame from frame 0 wherever
   its anchor is in frame (the dense sheet of the first second shows it; one absent in the opening
   seconds is a regenerate reason, never a note), and its position is read against a fixed neighbour (table
   edge, laptop, chair, window frame) on a dense sheet at least every 0.25 s across the whole clip and
   every cut. A move needs a visible cause: an action, or a cut that shows a new angle of the same spot.
5g. **Assembled timeline** (CE-016, CE-024, CE-025, CE-026): after the CapCut project is built, dense
   sheets (15 to 30 fps) of every transition, every insert start and end, every overlay start and end and
   the first second of the final. No frame of the replaced performer in an insert's edges, no frozen or
   held frame under a transition, no stray rectangle, halo or brightness step (an overlay exists only on
   the frames its element is visible and fades with the picture under it), every context-bearing source
   overlay present as the original element (`text-and-format.md` §1), no emoji in any text layer. Audio
   (Recreate): the reference's ORIGINAL track is one whole segment under the whole timeline, a stream
   copy (identical hash or a null-test residual of silence), the duration equal to the reference's, no
   splice. The evidence path of each of these checks goes in `result.json` (`continuity`).
6. **Scale**: the product against a hand or face on two or three sheets.
7. **Ownership** after every hand-off; who uses what.
8. **Verdict** (`generation-system.md` §9): **regenerate** on any break in §2.1–§2.5, §2.8–§2.10,
   §2.14, §2.15, §2.16, on a failed step 5f (an anchor missing in the opening seconds or moving without a
   cause; a step 5g break is fixed in the CapCut project, not by regeneration) and on physics breaks in
   §2.6, §2.11, §2.12; **post-fix** only in the cases each class names (an
   untouched static anchor's pixel hold, a one-frame trim, a recolour in a locked shot, a punch-in);
   **accept with a note** only for the cases named as tolerable (a small constant oversize, a soft
   label while gripped).
9. **The corrected retry** names the cause (a missing sentence, a leaking reference, a parameter),
   adds the exact line from the class, and removes the leak. It never adds timing constraints to
   free motion (`generation-system.md` §5b).

### 4.1 How the verdict is written (examples)

```
counts: capsules 3 (0.0 s) / 3 (3.9 s, before exit) / 1 (7.6 s, re-entry) — no cause → regenerate.
  retry: "Exactly three capsules … stay there, all three, while he walks past and when he comes back"; exclusion "no capsule appears or disappears".
use: bottle 3.5–5.6 s @30 fps — cap closed; lips on the lid's right side, no spout there; head tilted back → regenerate.
  retry: the sheet's lines (flip-top spout on the left of the lid; thumb flips it open; lips on the spout; head level; both hands); exclusion "drinks only through the spout; no other opening"; @Image3 = the bottle with the cap flipped open.
state: can tab raised at 0.0 s, cracked at 3.0 s in the plan → regenerate; cause: the open-tab reference → removed; "[Start state] sealed, tab flat".
permanence: pouch missing 8.1–8.3 s while the arm passes; untouched static anchor, locked camera → post-fix (pixel hold from frame 236); checked at 30 fps, no edge artefacts.
scale: pack 155 px = 12 % of frame height vs ~10 % target, constant → accept with note.
size (method): can 270 px = 21 % of the frame; A: vs her head (23 cm, 250 px, at 1.0 m; the can at 0.55 m, `--depth-ratio 0.55`) = 0.87×; B: d = 0.55 m derived from the desk edge, f 26 → expected 264 px = 1.02×; A and B agree → accept (an assumed 1.5 m had said 2.79×).
size (provisional): `scale --distance 1.5 --lens 26` only → one estimate, 2.79× from an assumed distance, which the agent reads as provisional (the tool prints numbers, not that word): not flagged and not repeated; the frame shows the can on the near fold-out desk under a metre from the lens (CE-028) → re-measured against the head, then judged.
size (neighbour in another plane): can 375 px = 29 % of the frame; A against her head (23 cm, 340 px) at `--depth-ratio` 1 gives 1.61×, but the can stands on the near table strip in front of her, so that A is invalid; the depth ratio is read from the frame (the can nearer than her head) and B is derived from the table plane; if they disagree (`estimates_spread_pct` above about 25 %) the reading is inconclusive, nothing is flagged and the depth is re-derived (CE-014, CE-015, re-measured 2026-10-10: 1.07× to about 1.4×, unsettled).
size (wan3_0_prime): carton 163 px vs ~95 expected = 1.71× vs the bottle → regenerate; the guide lists size as a model limit, so no wording retry: the retry changes the form or the anchor class (in hand / beside a large same-plane object / one flat sachet on bare near-side surface), or none is spent and the best take ships flagged and recorded.
anchor: can absent 0.0–4.2 s, appears at the left foreground at 4.3 s → regenerate (never a note); the 0–1 s dense sheet shows an empty table. | can at 1.0 s left of the table end, at 2.0 s one laptop-width to the right, no action, no cut → regenerate; read against the table edge every 0.25 s.
timeline: overlay clip visible on 2.93–3.0 s as a bright rectangle on the fading picture → the overlay is cut to the frames its element is visible and faded with the picture; hold frames under the flash replaced by real-motion fades into pure white; original audio one segment, stream copy, hash identical.
posture: sachet upright against the forearm 4.8–6.0 s @30 fps, 0 px gap to the arm, no support under its edge → regenerate; retry: flat on bare near-side surface, a band of bare surface to the arm, the story reason; exclusion "no standing, leaning, propped or tilted sachet".
```

## 5. Quick reference

| anomaly | ledger | prompt line | QC checkpoint | verdict |
|---|---|---|---|---|
| fewer or more items after a walk-past, cut or occlusion | count; in-frame? | "exactly N … stay there, all N, while … and when he comes back"; "no N appears or disappears" | exit, re-entry, occlusion, cut at 15 fps; count | regenerate (a pixel hold only for an untouched static anchor) |
| used through a part with no opening, or a closed one | opening state; contact | "flips the cap open … lips on the spout … head level"; "only through the spout; no other opening" | use beat at 30 fps; lips on the part | regenerate |
| used before being made ready | event with cause | "lifts the tab; it stays up; then drinks from the opening" | state-change beat at 30 fps; cause before effect | regenerate; drop the leaking reference |
| opened, torn or poured state reverses | states copied forward | "continuing with the pouch torn open …" | every cut and re-entry; last frame | regenerate (trim a one-frame flicker) |
| level rises or falls without cause; wrong contents | level; sample binding | "half full … the can then nearly empty"; contents = the liquid of @ImageN | pours and sips at 30 fps; levels at checkpoints | regenerate |
| product too big, or its size changes | the size reckoning per shot: real dimensions, depth, lens, expected fraction of the frame, ratio to a named neighbour, the size ladder, constancy | "two thirds the height of the bottle beside it, on the dresser about 2.5 m from the camera, a small object in the background; it keeps this size" | `T scale` on a frame at rest, one in use and the last: observed vs expected by two estimates (neighbour ratio; a distance derived from the frame with `--distance-basis`) that agree; one assumed number is read as provisional and viewed first; constancy across cuts | regenerate (> 25 % on agreeing estimates, changing, or larger than the hand that holds it; no post-fix); a note at 15–25 % when static and readable |
| a placed or contents product absent in the opening seconds, or moving along the surface without an action or a motivating cut | the anchor row from t=0 with a fixed neighbour; a visible cause for every move | "stands on the table from the first frame, left of the laptop, and stays; nobody touches it" | dense sheets of 0–1 s and of the whole clip, the product read against the fixed neighbour at least every 0.25 s | regenerate (no post-fix) |
| a transition, insert edge or overlay leaves a frozen frame, the replaced performer, a stray rectangle or brightness step, a spliced or shortened audio track, or an emoji in a text layer | the timeline row of the CapCut plan: pieces, edges, overlay lifetimes, one audio segment | edges cut on frames of the insert only; real-motion fades into a pure-colour gap; overlays trimmed to their visible frames and faded with the picture | dense sheets at every transition, insert and overlay start and end; audio hash or null test; text-layer scan | fix in the CapCut project (no regeneration) |
| head tilted on a straw; fingers through; a second copy in the other hand | holder and hand; mouth | "drinks through the straw with his head level"; "both hands around the bottle" | use beat at 30 fps | regenerate |
| label mirrored, rotated or migrated; flavour changes; a part moves | mark orientation | "label upright, faces the camera, tilts with the bottle; same flavour throughout; strap on the lid" | first and last frame; rests; a full-resolution frame | regenerate (soft label while gripped: a note or a punch-in) |
| giver still holds it after the hand-off; two items | holder per row | "after that, only the boy holds it; her hands are empty" | hand-off at 30 fps; count after | regenerate |
| floats, sinks, wrong shadow, decor moves, wrong user | environment row; roles | contact shadow; "stays on the table"; who uses what | every sheet; cuts | regenerate (constant colour drift: post-fix) |
| process impossibly fast, frozen or repeated | time budget | "real-time speed"; one process per stage | dense sheet of the process; the freeze starts `T qc` lists | regenerate (dead tail: trim) |
| a thrown, dropped or passing thing goes through the product; the product sinks or shows through; a hit without a consequence; wrong occlusion order | path row; occlusion note | "it arcs past the bottle on its far side and lands behind it; the bottle is not touched"; "hits the can, bounces off; the can rocks and settles"; "nothing passes through the bottle" | every pass-near, landing and hit at 30 fps; silhouettes, depth order, consequence | regenerate (no post-fix) |
| the product reads as a paste: brighter or cooler than the room, flat front light, no contact shadow, crisper than the plate, packshot pose, wrong perspective, wrong size, hard edges, on an empty edge | anchor row with the light on the spot, the neighbour for scale and shadow, the occluder, the mark angle | "@ImageN defines only shape, proportions, colours and label; not its lighting, exposure, background or camera angle"; "lit by the same warm, dim ceiling light as the bottle beside it, a third shorter than it, label about 30° away, soft contact shadow to the right like the bottle's, seen from the same low angle" | one full-res frame at rest and one in use: the eleven-sign paste test against the nearest neighbour | regenerate (local regrade only for a static untouched product failing on exposure alone) |
| a placed pack stands on its edge or leans on nothing, rests on a thin sheet, touches a working hand or arm, or takes over a source beat | the anchor row: posture, support, clearance, story reason | "lies flat on its wide face, label up, entirely on the bare marble at the near edge, a band of bare marble wider than itself to his forearm, where someone sets a sachet down out of the way"; "no standing, leaning, propped or tilted sachet, no sachet on a sheet" | every rest and every pass of a hand or sheet at 30 fps: posture, support, clearance, the sheet region; the story reason as its own line | regenerate (no post-fix) |
