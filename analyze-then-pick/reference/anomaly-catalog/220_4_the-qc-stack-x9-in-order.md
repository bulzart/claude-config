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
5b. **Solidity** at 30 fps wherever anything passes near, in front of or behind the product, lands
   on it or hits it: no pass-through, no sinking, no see-through, the right occlusion order, and a
   consequence for every contact (§2.14).
5d. **Size** with `atp.py scale` on a full-resolution frame at rest, one in use and the last:
   the product's pixel height against the named neighbour's at the product's own depth (A; `--depth-ratio` is
   read from the frame when the product stands in front of or behind that neighbour, a can on the near table
   strip against the person seated behind it, and is never left at 1; CE-014, CE-015) and against a distance derived from the
   frame (B, `--distance-basis`), the two multiples agreeing before an oversize verdict, the observed
   multiple of the expected size and the method written in the verdict, constancy across cuts; a
   verdict from one assumed number is provisional and is viewed on the frame first (§2.7).
5e. **Identity match** on a full-resolution frame with the face and a hand or forearm: same skin tone, age
   and build as the kept body, the garment and every printed line of the kept clothing as planned (no costume
   change, no reversed or invented print), with the frame path in the verdict (§2.17; CE-029, CE-035,
   CE-039).
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
5h. **Label legibility** on a full-resolution frame at rest: the wordmark and the variant tag read exactly,
   word by word against the asset (fine print may blur but never become wrong letters), the frame path in
   the verdict; a wrong letter is a regenerate reason (§2.9; CE-032, CE-036, CE-042, CE-090, CE-093). **Hand
   lanes:** no hand covers, wraps or passes through the product in any beat (§2.16; CE-072, CE-076).
5i. **Shot structure** (Recreate and Edit Mode, wherever the source has hard cuts; CE-079, CE-083, CE-086): the
   output's cuts (30 fps sheets, or `T prep-video` on the output) beside the source's shot list from the card:
   the same count at the same times (within 0.2 s); a person-free cutaway still shows only the screen or the
   object, not a face shot and not a ghost dissolve into one; the placed product is in every shot where its
   anchor is in frame; the closing emotion beat (a laugh, a reaction) is there. A merged, dropped or dissolved
   shot is a **regenerate** reason; the retry follows `generation-system.md` §3b.1 item 7 (separate clips on
   the reference's own cuts). The shot list and the evidence path go in the verdict and in `result.json`.
6. **Scale**: the product against a hand or face on two or three sheets.
7. **Ownership** after every hand-off; who uses what.
8. **Verdict** (`generation-system.md` §9): **regenerate** on any break in §2.1–§2.5, §2.8–§2.10,
   §2.14, §2.15, §2.16, §2.17, on a failed step 5f (an anchor missing in the opening seconds or moving without a
   cause; a step 5g break is fixed in the CapCut project, not by regeneration) and on physics breaks in
   §2.6, §2.11, §2.12; **post-fix** only in the cases each class names (an
   untouched static anchor's pixel hold, a one-frame trim, a recolour in a locked shot, a punch-in);
   **accept with a note** only for the cases named as tolerable (a small constant oversize, a soft
   label while gripped).
9. **The corrected retry** names the cause (a missing sentence, a leaking reference, a parameter),
   adds the exact line from the class, and removes the leak. It never adds timing constraints to
   free motion (`generation-system.md` §5b).

