# Worked Production Examples

Apply the core instructions in [SKILL.md](../SKILL.md).

## Contents

- [Examples](#examples)

<a id="examples"></a>
## 11. Worked examples: transfer the logic, not the subject

These are original, unrendered examples, not copied official prompts or validated success recipes. Durations are creative targets and must be supported by the active mode. Bracketed asset labels in examples must be replaced with actual inspected, provider-supported references. Use only the examples relevant to the user's project; never insert their props, materials, actions, or style into unrelated requests.

### A. Prop persistence while attention shifts

**Brief:** Move a tool to a work mat, operate a nearby switch, and retrieve that same tool. Two similar work areas exist. **Planning risk:** later retrieval from the wrong station; an occupied hand doing another task.

```text
One continuous 12-second shot, 16:9. A technician stands at a bench with a dark work mat beside the window and a pale work mat beside the door. One red-handled screwdriver initially lies on the dark mat; the pale mat is empty. Both mats and the adjacent wall switch remain visible in a steady waist-high three-quarter view.
0-4s: with their right hand, the technician lifts the screwdriver from the dark mat, carries it across the bench, sets it down fully on the pale mat, and releases it.
4-7s: the now-empty right hand presses the nearby wall switch, activating the task lamp; the screwdriver remains on the pale mat beside the door.
7-12s: the right hand returns to that same pale mat and picks up the same screwdriver. End holding it above that mat; the dark mat stays empty and the task lamp stays on. Quiet workshop ambience, a light tool contact, and a switch click. Keep the bench layout and tool design unchanged.
```

**Check:** the transfer is shown, the original station is emptied, the hand is available at the switch, and later retrieval matches the updated location. Do not make the earlier location permanent when the story explicitly moves the item.

### B. Repeated transfer with visible accumulation

**Brief:** Place three wooden tokens into a pouch individually, then lift it. **Planning risk:** skipping cycles, generating contents, or losing earlier deposits.

```text
One continuous 16-second close shot of a tabletop. An open fabric pouch stands at center, its mouth supported open. Exactly three wooden tokens lie separately on a shallow tray to its left. A person's right hand starts empty; the tray, hand, and pouch opening stay in view.
During 0-10s, the hand transfers the tokens one at a time: grasp one token from the tray, carry it above the pouch opening, release it through the opening, and return empty to the tray. Perform this complete cycle three times. Previously deposited tokens remain inside while the visible tray count decreases to zero.
During 10-14s, the right hand grasps the pouch by its upper fabric edge and lifts it gently from the table; its contents remain inside and the fabric responds to their weight. During 14-16s, hold the pouch above the now-empty tray. Fixed camera, soft side light, subtle wooden contacts and fabric movement, no speech or cuts.
```

**Check:** required count and method survive; contents move with the carrier. Do not insist that hidden tokens remain visible through opaque fabric. For another brief, derive the repetitions and material behavior from that brief rather than copying these numbers.

### C. Mechanism with visible prerequisites and no end-state reset

**Brief:** Inspect a hinged case, then finish with it closed. **Assets:** approved case views showing its real latch and hinge.

```text
Create a 15-second single-shot product demonstration of the case in [CASE_REFERENCE], retaining its actual hinge, latch, proportions, and finish. It starts closed on a stable workbench. Frame the latch, lid, and hands clearly in a fixed three-quarter view.
0-3s: the left hand steadies the base while the right hand releases the latch.
3-7s: the right hand lifts the lid along its existing hinge axis; the base stays on the bench and the hinge remains connected.
7-9s: hold the open position with the right hand supporting the lid, revealing the approved interior.
9-13s: lower that same lid along the reverse hinge path until seated, then close the latch. Release the lid only after it is supported by the base.
13-15s: withdraw both hands and hold on the same closed case in its original position. Soft fixed studio light, mechanism sounds at contact, no narration or camera movement.
```

**Check:** the final closed state follows an actual closure, not a cut that magically resets it. Do not use this sequence for a product with a different mechanism.

### D. Travel, obstruction, and physical support

**Brief:** Carry a parcel through a doorway and set it down. **Planning risk:** extra hands, passing through a closed door, or dropping support before placement.

```text
One continuous 14-second medium-wide shot. A courier holds one small parcel in both hands outside an already-open doorway. A low table is visible inside, one step beyond the threshold; the doorway is wide enough for the courier and parcel. Keep the open door, threshold, parcel, and tabletop in view.
0-7s: the courier walks through the open doorway without changing their two-handed grip, then stops directly in front of the table.
7-11s: the courier bends naturally and lowers the parcel until its base rests fully on the tabletop, then releases both hands.
11-14s: the courier straightens and steps back; the parcel remains where it was placed. A gentle camera follow stops before placement. Maintain parcel dimensions and room geography; synchronize footsteps and the soft placement sound. No dialogue.
```

**Check:** the established opening enables passage; the carrier supplies support until the table takes over. Do not introduce a new door-opening action without allocating a free hand or a prior set-down.

### E. Motivated dialogue and reaction

**Brief:** One character reports a signal, and another reacts after hearing it. **Assets:** actual approved character references.

```text
Create a 10-second stationary two-shot of [CHARACTER_A] and [CHARACTER_B] beside an unlit signal panel. Preserve their assigned designs. Character A stands nearest the panel; Character B faces A and can see the panel. Both begin silent.
0-2s: the panel indicator lights with a soft beep; A looks at it.
2-5s: A turns toward B and says in English, with quiet relief, "The signal is back." Only A speaks.
5-8s: after hearing the line, B looks toward the illuminated panel, visibly relaxes, and nods once.
8-10s: hold their shared relieved reaction; the indicator remains lit. Soft room ambience, no music, subtitles, additional lines, or camera move.
```

**Check:** the cue precedes the report and reaction; each character can perceive the trigger; speaker assignment is clear.

### F. Rigid-object inspection rather than accidental body motion

**Brief:** Show the approved display model from all sides. **Assets:** compatible views of one display model.

```text
A 12-second, square studio inspection video. The supplied front, side, and rear references depict the same rigid display model, not separate subjects. Place that model on one motorized turntable; the camera and studio lights remain fixed.
0-2s: hold the front view. 2-10s: the turntable carries the entire model through one complete smooth rotation, revealing the referenced profiles and back without independent movement of its parts. 10-12s: settle on the original front view. Keep the model centered at constant scale, preserve its asymmetric features, and maintain its contact with the rotating platform. No dialogue or cuts.
```

**Check:** rotation has an established driver, the correct actor moves, and the final view reconnects to the opening. Do not inherit a project-specific facial or clothing restriction unless the current brief requires it.

### G. Mechanical motion reference with separate appearance ownership

**Brief:** Restyle an approved assembly visualization. **Prompt pattern:** "Use [MOTION_CLIP] for component identities, positions, assembly order, trajectories, clearances, timing, and camera. Use [LOOK_REFERENCE] only for materials, color, and illumination. Keep each insertion along its demonstrated path and retain earlier assembled parts. Finish on the source's completed configuration." Check the actual clip before specifying it. Treat the result as visualization, not validation of manufacturability.

### H. Targeted edit with dependent effects

**Brief:** Change one prop's color in an existing shot. **Prompt pattern:** "Edit [SOURCE_CLIP]. Change only the identified prop's surface color to the approved color over the stated interval. Preserve its identity, geometry, location, handling, and the original action/camera/audio. Let reflections of that prop remain consistent with its changed appearance." Specify temporal transitions if the edit covers only part of the clip. Do not promise every other pixel unchanged when dependent reflections must change.

### I. Extension without replay or lost custody

**Brief:** Continue a character who ends the source walking while carrying an object. **Prompt pattern:** "Continue directly from [SOURCE_CLIP]'s inspected final state. Preserve the same object in the same hand, walking direction, pace, and camera motion. Complete the remaining approach to the already-established destination, place the object with visible support transfer, then stop and hold the resulting state." Use only boundary details actually observed; do not invent a destination from absent footage.

### J. Loop with attachment and velocity continuity

**Brief:** A hanging ornament completes one gentle oscillation. **Prompt pattern:** "One stationary view of the same ornament attached to its cord. Begin at the left turning point, swing through the right turning point, and return to the same left turning point over one cycle. Maintain the attachment, shape, light, and framing; match the turning behavior at the seam." Inspect repeated playback and audio. Matching endpoint images alone do not prove a smooth loop.

**Official demonstration patterns, paraphrased:** ByteDance's launch examples distinguish structural motion/camera references from appearance references, and carry subjects through connected locations rather than describing isolated tableaux. Borrow those organizational principles, then perform this guide's independent continuity audit. An official demo is not a guarantee that every prompt using its structure will succeed. [S1](../references/sources.md#s1)

