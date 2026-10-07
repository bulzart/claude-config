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

A ledger that tracks only where the product is ("bottle: on the table → in hand → on the table")
lets both through: it carries neither the **count** of the capsules nor the bottle's **openings and
use**, and a QC pass that looks for the product's presence and spot never counts the capsules or
checks where the mouth met the bottle. The rules below close that gap for every product. The
examples illustrate the rules; they never limit them.

## 0. Three questions behind every anomaly

1. **How many?** Every multiple is counted at t=0, and the count changes only through a visible
   cause, by exactly the amount the cause explains (§2.1).
2. **Through what?** Every use of an object goes through the part built for it (the spout, the
   opened top, the nozzle, the torn notch, the handle, the screen) after the step that readies it,
   and the contact point is named (§2.2, §2.3).
3. **Still there, still so?** Whatever leaves the frame, passes behind a hand or sits across a cut
   comes back with the same count, spot, state and size (§2.4, §2.5).

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
| real size | from the spec, or by comparison | ~24 cm tall, ~7 cm wide, 1 l; an adult's hand spans the body, a child needs two hands | 355 ml slim can, 15.5 cm tall, 5.8 cm wide; one hand's width |
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

### 2.7 Scale and proportion

**Rule.** The product keeps its real size relative to hands, faces, furniture and the other
products, at every depth and in every shot.

**Breaks.** A gum pack at 23 % of the frame height (2026-10). A sachet two to three times its real
size. A can taller than a forearm. A child's bottle adult-sized in his hands and tiny on the table.
A phone that grows when lifted. A car shorter than the person beside it. A product that changes size
across cuts. A glass larger than the can that filled it.

**Ledger.** The registry's real size and a comparison ("a hand's length").

**Prompt.** Give the size by comparison ("about the length of an adult hand", "a child needs both
hands around it") and say it keeps that size; for a start-frame model, build the frame at the right
ratio; keep tight product crops padded small in the references (a tight crop pulls the product into
the foreground).

**QC.** Measure the product's height in pixels against a face or hand in the same depth plane on
two or three sheets, including the first and last frames; compare across shots.
- **Regenerate** when the ratio is off by more than roughly a quarter or changes between shots. A
  small, constant oversize that keeps the label readable may be **accepted with a note** (the sachet
  case).

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

**Ledger.** The time budget's beat durations from the family profile and the process's real
duration.

**Prompt.** "Real-time speed"; one process per stage with its natural duration; never a timestamp
on free motion (`generation-system.md` §5b).

**QC.** The dense sheet of the process: continuous progress at a natural duration; `T qc` freezes.
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

## 3. The prompting stack (in order, per video)

1. **Affordance sheet** (§1) for every product and object in the registry, before any plan.
2. **Ledger** (`generation-system.md` §3) with the columns count, opening/lid state, level, holder
   and hand, contact point, in-frame?; one row per event, each with its visible cause.
3. **Use beats** written as initial state → operation on the named part → observable result, with
   the contact point (§2.2, §2.3), the product's real size by comparison (§2.7) and the body
   mechanics of that use (§2.8), in the locked model's phrasing (its guide §3.14).
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
   beside the 5 fps storyboard. View every sheet.
2. **Count** every multiple at every checkpoint and write the numbers in the QC note
   ("capsules 3 / 3 / 3 / 1, two taken at 7.5 s").
3. **Part and contact** on every use beat: the preparation step, the part used, the lips or hand on
   it, the orientation, the head angle, the other parts (strap, cap, tab).
4. **States** across the ledger: no reversal, no effect before its cause, levels monotonic between
   causes, contents right.
5. **Permanence** before and after every exit, occlusion, cut and seam: count, spot, state, size,
   label orientation; reflections and shadows.
6. **Scale**: the product against a hand or face on two or three sheets.
7. **Ownership** after every hand-off; who uses what.
8. **Verdict** (`generation-system.md` §9): **regenerate** on any break in §2.1–§2.5, §2.8–§2.10 and
   on physics breaks in §2.6, §2.11, §2.12; **post-fix** only in the cases each class names (an
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
```

## 5. Quick reference

| anomaly | ledger | prompt line | QC checkpoint | verdict |
|---|---|---|---|---|
| fewer or more items after a walk-past, cut or occlusion | count; in-frame? | "exactly N … stay there, all N, while … and when he comes back"; "no N appears or disappears" | exit, re-entry, occlusion, cut at 15 fps; count | regenerate (a pixel hold only for an untouched static anchor) |
| used through a part with no opening, or a closed one | opening state; contact | "flips the cap open … lips on the spout … head level"; "only through the spout; no other opening" | use beat at 30 fps; lips on the part | regenerate |
| used before being made ready | event with cause | "lifts the tab; it stays up; then drinks from the opening" | state-change beat at 30 fps; cause before effect | regenerate; drop the leaking reference |
| opened, torn or poured state reverses | states copied forward | "continuing with the pouch torn open …" | every cut and re-entry; last frame | regenerate (trim a one-frame flicker) |
| level rises or falls without cause; wrong contents | level; sample binding | "half full … the can then nearly empty"; contents = the liquid of @ImageN | pours and sips at 30 fps; levels at checkpoints | regenerate |
| product too big, or its size changes | real size by comparison | "about the length of a hand; it keeps this size" | ratio vs face or hand on 3 sheets | regenerate (> ~25 % or changing); a note if small and constant |
| head tilted on a straw; fingers through; a second copy in the other hand | holder and hand; mouth | "drinks through the straw with his head level"; "both hands around the bottle" | use beat at 30 fps | regenerate |
| label mirrored, rotated or migrated; flavour changes; a part moves | mark orientation | "label upright, faces the camera, tilts with the bottle; same flavour throughout; strap on the lid" | first and last frame; rests; a full-resolution frame | regenerate (soft label while gripped: a note or a punch-in) |
| giver still holds it after the hand-off; two items | holder per row | "after that, only the boy holds it; her hands are empty" | hand-off at 30 fps; count after | regenerate |
| floats, sinks, wrong shadow, decor moves, wrong user | environment row; roles | contact shadow; "stays on the table"; who uses what | every sheet; cuts | regenerate (constant colour drift: post-fix) |
| process impossibly fast, frozen or repeated | time budget | "real-time speed"; one process per stage | dense sheet of the process; `T qc` freezes | regenerate (dead tail: trim) |
