## 9. Post-generation QC (after download)

1. `atp.py qc --video <final> --out <dir> --mode <analyze|edit> --allowed-text "<planned text>"
   --dense "<label>:<a>-<b>" …` with every QC checkpoint of the plan (`anomaly-catalog.md` §3
   step 8), then **view the 5 fps storyboard** sheets in order and every dense sheet under
   `<dir>/dense/`.
2. Check against the plan: identity, asset geometry (compare with the canonical template), the ledger
   states, interactions (densify contact moments with `atp.py frames --range a-b --fps 15 --sheet`),
   lighting, text (unexpected text or pseudo-text = fail), pacing (dead head/tail → `atp.py trim`),
   and format (720×1280).
   - **Placement (§4b):** compare the item's spot and state across the sheets, and densify around
     cuts, pickups, set-downs and any move (a car driven in or away).
   - These count as a **regenerate** reason: the item missing, unrecognisable, duplicated, changing
     spot without a visible action, featured like an ad, or looking pasted in. "Pasted in" is
     measured, not felt: the eleven-sign paste test on one full-resolution frame at rest and one in
     use, against the nearest neighbour at the same depth (`anomaly-catalog.md` §2.15), with the
     result written in the verdict.
   - **Contents (§4b.0):** every vessel of the product's category in the subject's scene shows the
     product's contents (colour, clarity, bubbles, garnish), whether it was planned or came from an
     asset photo. A glass of water beside the can, or any other consumable of the category that is
     not the product, is a **regenerate** reason, never a note. The corrected attempt states the
     vessel's contents from the sample, or excludes the vessel when contents would be illogical.
   - **Motion beats at the full frame rate.** Every motion beat gets
     `atp.py frames --range a-b --fps 30 --sheet` across the whole beat: spins, tosses, catches,
     pours and landings; a vehicle driving, turning, braking or parking; a door or lid opening. The
     5 fps sheets hide single-frame cheats. The motion must stay continuous and follow its own
     physics (§5b): a spin keeps its direction and slows, a toss keeps its arc, a vehicle speeds up
     and slows gradually with its wheels turning at its speed. A snap, a pause-and-resume without a
     cause, a reversal, a slide without a cause, or a morphing label, badge or body is a
     **regenerate** reason (§5b).
   - **Action sync (§5c),** whenever the original audio comes back: `atp.py sync-check` and its
     sheet, plus the sync anchors densified. Drift or a moved action is a **regenerate** reason;
     a steady offset is a post-fix.
   - **Leftovers:** check against §9b. Only its **must-not-survive** list counts as a finding.
     Everything on its **fine** list is ignored: not reported, not asked about, not regenerated.
   - **Size** (`anomaly-catalog.md` §2.7): on a full-resolution frame at rest, one in use and the
     last, `atp.py scale --product-cm <H> --product-px <y0-y1> --ref-cm <h> --ref-px <y0-y1>`
     against the named neighbour at the product's own depth (`--depth-ratio` from the frame when the product
     stands in front of or behind it) and `--distance --distance-basis --lens` for the shot (the distance
     derived from the frame); the two estimates must agree before an oversize verdict, a verdict from one
     assumed number is provisional and viewed on the frame first, and the observed multiple of the
     expected size and the method go in the verdict. Over 25 %, a size that changes between shots, or a
     product larger than the hand that holds it is a **regenerate** reason with no post-fix;
     15–25 % is a note only for a static product with a readable label. On a model whose guide lists
     size as a model limit, the retry changes the lever (the size-and-place guide, §4b.6, the integration
     form of §4b.0 or the anchor class from the guide's passing list), never the sizing words; a second miss
     ships the best take flagged, and both attempts are written as blocks in the brief.
   - **Posture, support and place** (`anomaly-catalog.md` §2.16): at 30 fps on every rest and every pass
     of a hand or sheet. A lean against nothing, a posture the shape cannot take, a pack touching a
     working hand or arm, a doubled or warped sheet, or a source beat taken over is a **regenerate**
     reason with no post-fix; the story reason is its own line of the verdict.
   - **Anchor from frame 0** (`anomaly-catalog.md` §4 step 5f): the placed or contents product is in the
     first-second dense sheet and is read against a fixed neighbour at least every 0.25 s across the clip;
     absent in the opening seconds, or moving with no action and no motivating cut, is a **regenerate**
     reason (CE-018, CE-019).
   - **Assembled timeline** (`anomaly-catalog.md` §4 step 5g): dense sheets at every transition, insert
     edge and overlay start and end; no replaced performer, frozen frame, stray rectangle or brightness
     step, the original audio whole, no emoji in a text layer (CE-016, CE-024, CE-025, CE-026). Fixed in
     the CapCut project.
   - **Source surfaces** (§8): each printed surface that a guardrail or §9b names, at full resolution and
     by `atp.py qc` OCR. A reproduced poster, livery, board or screen is a **regenerate** reason, and the
     retry replaces it with a named concrete thing instead of describing blankness.
   - **Label legibility** (`anomaly-catalog.md` §2.9, §4 step 5h): the wordmark and the variant tag
     (flavour, size or model) read exactly on a full-resolution frame at rest, word by word against the
     asset; a wrong letter is a **regenerate** reason, never "OCR noise".
   - **Hand lanes and camera path:** no hand covers, wraps or passes through the placed product in any beat;
     the camera and the performer's pose in the last third match the source (§5c.5); a placed product that
     leaves the frame while its anchor should still be in frame is a **regenerate** reason, like one missing
     at 0 s.
   - **Shot structure** (`anomaly-catalog.md` §4 step 5i; Recreate and Edit Mode with hard cuts): the output's
     cuts match the source's shot list in count and time, a person-free cutaway is not a face shot or a ghost
     dissolve, the placed product is in every shot where its anchor is in frame, and the closing emotion beat
     survives; a merged, dropped or dissolved shot is a **regenerate** reason, and the retry follows §3b.1
     item 7.
   - **Counts, openings and permanence** (`anomaly-catalog.md` §4): count every multiple at every
     checkpoint and write the numbers in the verdict; on every use beat check the preparation step,
     the part used and the contact point on the 30 fps sheet; before and after every exit,
     occlusion, cut and seam compare count, spot, state, size and label orientation. A count or
     state that changes without a cause, a use through a part with no opening or a closed one, and
     an effect before its cause are **regenerate** reasons. The catalog names the only post-fixes:
     a pixel hold on an untouched static anchor in a locked shot, a one-frame trim, a recolour or a
     punch-in in a locked shot.
3. **Verdict** (record it in the run log with the reason):
   - **accept**;
   - **post-fix**: trim, conform, restore-audio or a sync offset (text and inserts are fixed in the
     CapCut project);
   - **regenerate**: once, with a corrected request, after diagnosing whether the prompt, a
     reference or a parameter caused the problem. The model stays locked. Report the failure
     honestly if the retry also fails.
   These rules apply autonomously in Analyze Mode.
4. **Edit Mode review:** the user decides. After every attempt the finished video is opened for them
   (`atp.py open`) and they choose:
   - **Looks good** → next video;
   - **Needs changes** → re-edit, always from the **original source video**, with their feedback
     folded into a new request (new attempt, new ledger fingerprint);
   - **Stop**.
   Repeat until approved. Automated QC findings are shown with the video, not acted on silently.

