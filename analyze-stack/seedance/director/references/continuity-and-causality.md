# Whole-Video Continuity and Anomaly Checks

Apply the core instructions in [SKILL.md](../SKILL.md).

## Contents

[World state and event planning](#continuity) | [Anomaly categories](#anomalies) | [Cross-cutting safeguards](#cross-cutting-safeguards)

<a id="continuity"></a>
## 4. Mandatory whole-video continuity engine

Use the following planning representation in proportion to scene complexity. A simple shot needs a few internal checks; a multi-step interaction needs an explicit compact ledger. Do not expose a large ledger unless the user requests a plan.

### 4.1 Establish one persistent world

Give every important entity a stable identity and every relevant place an unambiguous anchor. Track repeated-looking objects separately. Prefer environment-relative locations such as "the tray beside the door" to "the first tray" unless numbering has been visibly established. Do not add visible labels just to express internal IDs.

Distinguish world coordinates, screen position, and a character's own left/right. A camera crossing the room can reverse screen position without moving an object in the world. Track adjacency, containment, support, reachable paths, doors, obstacles, and sightlines. Do not invent metric coordinates where the brief provides none.

For each important entity, track only relevant state:

`identity/design | world location | orientation/pose | holder or support | contents/count/level | open/closed or assembled state | condition | visibility/occlusion | current motion`

Separate **invariants** from **state that must change**. The same container can retain its identity while its contents increase. An unchanged room layout does not require every moving person to remain stationary. Overbroad preservation instructions must not freeze the requested action.

### 4.2 Expand actions into causal transitions

For every essential event, establish:

`preconditions -> actor and mechanism -> path/contact/transfer -> observable consequence -> resulting state`

For physical handling, identify who reaches, which hand/tool engages, where contact occurs, when support changes, and where the object is left. Complete release before assigning the same hand to an incompatible task. For a handoff, receiver support precedes giver release unless a deliberate throw is requested. Keep the carrier and carried object moving together until separation.

For repeated operations, preserve the repeat structure: return to the source, acquire the next portion/item, transport it, deposit it, and retain previous results. Use the user's specified count. When count is not essential, choose natural pacing rather than inventing a fragile exact inventory.

For a transfer, maintain a source, carrier or channel, destination, and state change on both sides. Contents cannot appear at the destination merely because it moved nearby. Track accumulation, depletion, remaining capacity, and any permitted loss or transformation. Do not require equal visible levels in differently shaped containers.

Never use vague bridge verbs such as "handles," "does the process," "then it is ready," or "seamlessly transitions" to conceal a required mechanism.

### 4.3 Propagate state across the entire timeline

Apply a persistence rule: an established state remains until an event explains its change. An object left at a location must later be retrieved there unless a transfer occurs. Items do not multiply, vanish, change identity, swap holders, or relocate because the camera looked away.

Allow normal occlusion and off-screen activity without confusing them with disappearance. Record where the object remains and what could plausibly happen while hidden. Do not hide the critical mechanism behind an occluder just to obtain the correct final image. If the method is part of the brief, keep enough of it visible to verify.

At a continuous cut, match previous end state to next start state: object locations, hand occupancy, pose, contents, damage/wetness, active lights, direction of travel, ongoing speech, and background relationships. A cut is not a reset button.

An intentional time jump, montage, dream, transformation, or separate pack shot may change state. Label it as such, make its relationship to the story understandable, and respect the user's continuity requirement. Never introduce an ellipsis merely to skip a required action.

### 4.4 Plan backward, then validate forward

Work backward from the required ending: identify what must already be true for each later event. Seed needed objects, available hands, open paths, preparation, knowledge, or motivation before they are used. A future reaction needs a prior perceptible trigger unless the story intentionally establishes anticipation.

Then walk forward through the complete sequence. Confirm every prerequisite is satisfied by the starting state or an earlier event. Reconcile every later use of an object with its last recorded state. Audit connections spanning several intervening beats, not only adjacent sentences.

When revising one action, propagate the change through all dependent beats, timings, references, and the ending. Do not patch one sentence while preserving an incompatible later state.

### 4.5 Use a compact planning ledger when needed

```text
INTENT: approved outcome and required method
WORLD: entities, distinct anchors, topology, baseline physical/style rules
INVARIANTS: traits that must remain fixed
BEAT: time/order | preconditions | actor/action/path | visible consequence
      | object locations/custody/contents afterward | camera/audio
DEPENDENCIES: later uses and their earlier enabling events
RISKS: failure opportunity | preventive staging | visible pass condition
ENDING: final states and the narrative/practical payoff
```

This is an agent-side planning aid, not a claimed model feature, executable physics simulation, or provider request schema.


<a id="anomalies"></a>
## 5. Audit structural, logical, engineering, and physical anomalies

Apply only relevant checks, but scan all categories. Diagnose what could go wrong in this particular scene instead of adding a universal negative-prompt blacklist.

| Category | Check before drafting | Repair in the scene specification |
|---|---|---|
| Identity and count | Does an entity duplicate, merge, change variant, or silently switch? | Use stable descriptors and actual reference ownership; track each important instance. |
| Location and topology | Does a later position follow from a real path? Are similar places confused? | Name persistent world anchors and describe any necessary relocation. |
| Custody and support | Who holds or supports each item? Is a hand/tool double-booked? | Specify contact, lift, carry, placement, and release at the decisive points. |
| Causality and knowledge | Can the effect happen from the available cause? Can a character perceive its trigger? | Establish the mechanism, prerequisite, sightline, or audible cue first. |
| Time and order | Are operations concurrent when they must be sequential? Is the allotted time feasible? | Sequence dependencies; remove optional activity or adjust the production plan. |
| Inventory and volume | Do contents persist and accumulate? Is the source depleted or the destination overfilled? | Describe material movement and resulting levels/counts qualitatively unless exact values matter. |
| Solid geometry | Do parts interpenetrate, stretch, change scale, or pass through closed barriers? | Define clearance, entry routes, rigid parts, and authorized articulations. |
| Mechanical function | Does the motion match the actual hinge, joint, latch, thread, or actuator? | Use verified references; show unlocking/alignment/actuation before the result. |
| Force and motion | Are motion, stopping, falling, turning, and support plausible for the world? | Establish the driving action, continuous trajectory, and settling response. |
| Materials and phases | Do fluid, granular, rigid, elastic, or cloth behaviors match the material? | Describe the relevant interaction and aftermath, not "perfect physics." |
| Optics and visibility | Is invisibility actually occlusion, opacity, reflection, or framing? | Preserve material appearance and distinguish what exists from what can be seen. |
| Body and environment | Are reach, grip, balance, footing, gaze, and scale compatible? | Use natural reachable blocking and leave room for handling. |
| Camera and edit | Do cuts, screen direction, focus, crop, or moves conceal or contradict essential events? | Preserve action geography; make contact readable; sequence camera phases. |
| Sound and emotion | Does each sound/reaction have the right source, timing, and motivation? | Bind cues to events and give reactions an established stimulus. |
| Production contract | Do reference inputs, settings, duration, mode, and required precision agree? | Verify supported controls; separate wishes from executable settings. |

**Material reasoning:** distinguish a stream entering a vessel from a flat layer appearing above it; distinguish solid contact from interpenetration; distinguish elastic deformation from changing topology. Apply gravity, displacement, buoyancy, friction, inertia, viscosity, and settling only as relevant to the actual materials and conditions. Do not decree that every solid floats, that every liquid mixes, or that contents remain visible through opaque surfaces. Treat density, binding, geometry, and transparency as context-dependent; verify specialist properties rather than guessing.

**Engineering boundary:** visual plausibility is not engineering validation. Do not invent a device's mechanism, power source, load rating, medical process, or safety procedure. Use supplied documentation and specialist sources for high-stakes accuracy, or classify the result as conceptual visualization rather than evidence.

**Intentional exceptions:** preserve authorized magic, animation conventions, impossible architecture, time reversal, or stylization. Define their onset and scope; do not let a deliberate exception excuse unrelated continuity failures. Do not automatically "correct" the user's creative premise into realism.


## Cross-cutting safeguards

Treat these as authored planning rules, not a formal physics solver.

- Preserve changes caused by ongoing established processes, including falling, momentum, cooling, drainage, and settling where relevant. An unchanged-state rule does not freeze the world between explicit actor commands.
- Anchor ambiguous repeated locations to durable room features, not merely current screen-left/right. Use visible distinctions already present; do not redesign an approved set to manufacture easier landmarks.
- Track what characters have perceived when motives or reactions depend on it. An object can be visible to the audience but hidden from a character.
- Preserve non-visual consequences: an activated device stays on until disabled; a completed transfer changes availability; a consumed item cannot be used again without replenishment.
- Audit related edits as a dependency closure. Moving an object may require changed shadows, reflections, occlusion, contact, and later reach. If strict pixel preservation conflicts with these effects, flag the actual tradeoff.
- Keep unknown geometry, density, timing, or device behavior unknown until a reliable input resolves it. Do not insert numerical precision merely to make a plan look engineered.
- Scale detail to risk. Describe a decisive grasp or material interaction clearly, but let ordinary compatible movement remain natural rather than prescribing every joint angle.
- Do not hide essential correctness behind cuts or blur. Use reference footage or a different production method when the requested mechanism is essential and repeatedly fails.

Use [the continuity ledger](../assets/continuity-ledger.md) for complex jobs. Re-read the final prompt independently from the ledger: a correct plan does not help when an essential transition was dropped during compilation.
