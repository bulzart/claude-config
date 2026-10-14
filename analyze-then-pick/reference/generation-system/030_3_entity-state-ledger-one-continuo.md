## 3. Entity state ledger (one continuous evolving state)

Track every important character, product, object, container, liquid, interface, garment and prop from
the first frame to the last. Earlier states constrain later ones.

| entity | count | t=0 state (spot · opening/lid · level · holder + hand · mark · in frame?) | event (visible cause · hand · contact point) | new state | … | final state |
|---|---|---|---|---|---|---|
| e.g. bottle | 1 | on counter, right of glass, cap on, full, label to camera | 1.2 s right hand lifts it | in right hand, cap on | 2.0 s left hand unscrews the cap and sets it on the counter; 2.5–4.0 s lips on the bottle's mouth, head tilted back: ⅓ drunk | back on counter, cap off beside it, ⅔ full |
| e.g. can (placed, §4b) | 1 | on desk, right of laptop, open (tab up), label ~30° to camera | 6.0 s left hand lifts it; lips on the opening beside the tab, one sip, head tilted back a little | in left hand | 7.5 s set down on the same spot | on desk, right of laptop, open |
| e.g. capsules | 3 | on the desk, right of the lamp, in a row | 4.0–7.5 s he walks past behind the desk and out of frame: untouched | 3 on the desk | 7.5 s right hand takes two, into the mouth, swallows | 1 on the desk, 2 swallowed |
| e.g. car (placed, §4b) | 1 | parked at the curb behind the bench, lights off, wheels straight, badge ~30° to camera | 8.5 s owner walks to it, opens the driver's door, gets in | engine on, lights on | 9.5 s pulls away slowly, wheels turning | leaving frame left |

Invariants to check against the ledger:
- **Placement persists:** an object stays where it was put until a visible action moves it.
- **One holder, one hand:** an object held in the right hand stays in the right hand unless a
  visible hand-off happens.
- **Irreversible states persist:** opened stays open, poured stays poured, broken stays broken,
  consumed stays consumed.
- **Liquids are conserved:** the amount leaving a container equals the amount arriving; nothing
  appears from nowhere.
- **Camera changes preserve layout:** a cut or angle change keeps left/right, near/far and on/under
  relations (respect the 180° line unless the reference deliberately breaks it).
- **Screens and interfaces:** a UI state changes only through a visible interaction and never
  re-randomises.
- **Wardrobe, hair, makeup and accessories** are constant unless a visible change happens.
- **Multi-clip videos:** each clip's end state is the next clip's start state, word for word.
- **Counts persist:** every multiple is counted at t=0 and changes only through a visible cause, by
  the amount it explains; what was taken exists somewhere (`anomaly-catalog.md` §2.1).
- **Use goes through the opening:** an object is used through the part built for it (the spout, the
  opened top, the nozzle, the torn notch, the handle, the screen), after the step that readies it,
  with the contact point named; nothing reacts before its cause (§2.2, §2.3, §2.8).
- **Object permanence:** what leaves the frame, passes behind a hand or sits across a cut comes
  back with the same count, spot, state and size (§2.5).
- **Parts and marks belong to the body:** a cap, strap, straw or label moves with the object, never
  on its own, never mirrored, never duplicated; the variant stays the same (§2.9).
- **Rendered, not pasted:** the product shares the neighbours' light, exposure, focus, grain,
  camera angle, scale and shadow direction, and stands inside its surface among the things around
  it (`anomaly-catalog.md` §2.15, the eleven-sign paste test).
- **Solids exclude each other:** nothing passes through the product or any other solid thing;
  nothing sinks into a surface or a hand; opaque bodies hide what is behind them in depth order; a
  moving thing that meets a solid stops, deflects, bounces or lands, and what it hits reacts
  (§2.14).

