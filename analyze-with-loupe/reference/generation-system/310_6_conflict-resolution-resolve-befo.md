## 6. Conflict resolution (resolve before sending)

| conflict | resolution |
|---|---|
| A camera move would hide the key interaction | Change the camera: a slower move, a different angle, or locked-off |
| The reference grip or placement does not fit the client asset | Adapt the interaction to the asset's real geometry |
| The replacement would produce wrong reflections or shadows | Restage it (angle, distance, surface) or specify the lighting explicitly |
| The sequence is too complex for the model's reliability | Simplify or split it into clips and keep the core mechanism. Fewer simultaneous movers, one camera move, real-time processes |
| The duration exceeds the model's range | Split per §3b (on the reference's cuts first, continuations only where the take is continuous). The model stays locked. Analyze Mode: a video over 30 s needs the user's permission first (command A7b) |
| Overlay text is needed | Always a clean plate plus CapCut text layers (Analyze Mode; `capcut-assembly.md`). Never model-rendered |
| The reference is wrong or weak for the need | Replace or improve the reference (new start frame, better asset view). Do not compensate with prompt text |
| A dedicated parameter exists (duration, aspect, audio, genre, mode, frames) | Use the parameter. Do not describe it only in prose |
| The house approach (the user's examples) differs from a default here | Follow the house approach (`20-analysis/house-approach.md`) and note it in the brief. It never overrides physics and logic, §9b, the permission rule or the house text style |


### Reasoning first: rules are conditions, examples show a mechanism

Every content rule in these references holds **when its trigger is in this video**. A line that came from one case is a default for that situation, not a law for every product, and a quoted example sentence shows a mechanism for another case: write this video's own nouns, never copy an example. Decide by reasoning, then check against the rules, never the other way round:

1. **Need:** what does the plan or the source need this product to do in this beat (be seen, be held, be set down, stay put)?
2. **Product details:** what do its own details allow (shape, size, weight, opening, label, the posture it can hold; from the registry, the affordance sheet and `product_properties.txt`)?
3. **Scene:** what does the scene offer (the surfaces, hands and neighbours the source frame shows)?
4. Choose what all three allow. If nothing does, change the plan (the anchor, the integration form), not the wording.

**Authority when two things pull apart** (the higher wins for that beat; write the reason in one line in the pattern card and the brief, and drop the lower line from the prompt instead of writing both): the hard floors (service blocks, the copyright and ownership floor, the user's explicit instruction), then the client's own document, then the source and the plan's intent for the beat, then the product's real details and physics, then the locked model's limits, then defaults learned from cases, then taste.

**In the prompt:** the intended state once, in positive words, at the beat where it matters; at most one targeted exclusion per product, naming the one wrong thing that product's own details make possible; no "never", "always" or "only" of the writer's own except the fidelity lock's scoped "only"; and no two sentences that ask opposite things of the same beat. The lines a section mandates by name are not the writer's own emphasis words and are not counted against that one exclusion: the fidelity lock and its keep-list (§5c.3), the solidity exclusion for a passing thing (`anomaly-catalog.md` §2.14), the duplicate exclusion for a placed product (§4b.5), the camera-lock and prepared-source sentences, and the guardrail operations' lines (`brand-guardrails.md` §4); each is written once, in the model's phrasing, where its section says.

**In QC:** a finding is a deviation from the plan's intent for that beat, from the product's real details, or from physics, written as its reasoning in a line or two (what was expected, why, what was seen). A deviation from a default alone (the pack is not label-up, the can is not on a desk) is a note when the source, the plan or the product's details make it plausible, and never a regenerate reason by itself.

