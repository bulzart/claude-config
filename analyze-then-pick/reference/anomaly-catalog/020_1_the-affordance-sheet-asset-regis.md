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

