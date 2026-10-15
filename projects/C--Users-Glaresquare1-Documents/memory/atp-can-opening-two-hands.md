---
name: atp-can-opening-two-hands
description: ATP/ATG use beats need a visible physical cause; a ring-pull can is held by one hand while a fingertip of the other hand pulls the tab (user 2026-10-16)
metadata:
  node_type: memory
  type: feedback
  originSessionId: e5edfcc0-8eea-4941-8498-ba3ffcf09198
  modified: 2026-10-15T22:53:31.313Z
---

A can's opening in a generated video is a two-hand beat: one hand holds the can by its body, the other hand's index fingertip hooks under the ring and pulls the tab up over about a second, in contact until the lid cracks, and the pop comes after the contact. The camera sits a little above the chest so the lid shows, both hands stay in frame, and the targeted exclusion states the mechanism. Never "his thumb lifts the ring-pull tab" with no second hand, a tab that jumps in a split second, a tab that rises with no visible finger, or a can opened while it stands unheld on a surface.

**Why:** 2026-10-16 the user sent back videos 06, 07 and 08 of the Celsius run (20261015-215200-08): "it pops the can lid open without even touching it, illogical and incorrect, every action has to have a logical cause"; "opens it with one finger in a split of a second like it was nothing ... should've held the can with one hand and opened it with the other"; "it takes one hand to hold and the other to open". The prompts had written only "thumb lifts the ring-pull tab" (no holding hand, no contact point, no duration) and the camera showed the lid edge-on.

**How to apply:** write both hands' jobs in the use beat of every prompt that opens a can. QC checks, on 24-30 fps sheets: one hand grips the body, a fingertip is on the tab ring for at least about 0.5 s while the tab rises, the pop follows the contact, no opening on an unheld can. A take that fails is a regenerate reason (the same applies to any other use beat without a visible cause). Not yet folded into the references: `/update-from-errors` should add it as a general kind (use beats need a visible, physical cause) to the owning prompting and QC sections. Related: [[atp-anomaly-catalog]], [[update-from-errors-command]], [[atp-reasoning-over-rule-lists]].
