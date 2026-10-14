### 5d. Counts, openings and object permanence
Two anomalies from anime Create videos (2026-10) define this rule set: three capsules on a desk
became one after the character walked past them and came back, and a boy drank from the side of a
flip-top straw bottle that has no opening there, after his mother had filled it with milk. A ledger
that tracks only "where the product is" lets both through. `anomaly-catalog.md` is the full
catalog; what every plan, prompt and QC pass must do:
- **The affordance sheet first** (`anomaly-catalog.md` §1): parts, openings, the opening sequence,
  how the product is used and held, the contact point, what it holds and how many, its states, its
  real size, the orientation of its mark, and what it cannot do, written into the registry before
  the plan.
- **The ledger counts and names the part** (§3 above): a count per multiple, the opening or lid
  state, the level, the holder and hand, the contact point, and whether the anchor is in frame.
- **The prompt** writes every use beat as initial state → operation on the named part → observable
  result with the contact point, carries every count with its number, restates counts and states
  after each exit, occlusion, cut, hand-off and seam, and adds one targeted exclusion per product
  for its own wrong use (`anomaly-catalog.md` §3).
- **QC** renders the plan's checkpoints dense (`atp.py qc --dense`), counts at each, checks the part
  and the contact on every use beat, and compares count, spot, state and size across every exit,
  occlusion, cut and seam (`anomaly-catalog.md` §4). A count or state that changes without a cause,
  a use through the wrong or a closed part, and an effect before its cause are regenerate reasons.

