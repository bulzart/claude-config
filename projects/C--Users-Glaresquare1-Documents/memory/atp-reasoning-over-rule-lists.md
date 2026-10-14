---
name: atp-reasoning-over-rule-lists
description: "Prompt crafting and QC reason from the product's details and the scene, not from lists of never/always rules and example failures; rules are conditions with triggers; fewer examples (user 2026-10-15)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 550ea8f9-fa48-4983-be86-ce42635bab6a
  modified: 2026-10-15T00:30:00.000Z
---

On 2026-10-15 the user said the prompt-crafting and QC examples ("product should not do this, should do that, never laying on the floor, always avoiding the desk or other") are ambiguous and double-edged, fight each other, make generations obscure and stop logical reasoning from taking place; asked to reduce the volume of examples a bit and focus on logical reasoning, logical evaluation examples, and the web app's miss/right use done logically in accordance with the product's details.

**What was done:** generation-system §6 got a "Reasoning first" subsection (need → the product's own details → what the scene offers → choose what all three allow; an order of authority when things pull apart; prompt economy: one positive statement per beat, at most one targeted exclusion, no never/always, no opposite sentences; QC: a finding = deviation from plan intent, product details or physics, a deviation from a default alone is only a note). Read by plan-video, write-request, precheck (X4 check "rules that pull apart") and QC (three short worked evaluations). The catalog's long example-failure lists were compressed to mechanisms; §2.16 and §4b.1b are derived from the product's shape and the scene; brand-guardrails "never on the floor" etc. are examples of what a client document may say, not defaults; X2 lost many quoted example sentences; `/update-from-errors` lesson cards now need a Trigger and a Counter-case, lessons are defaults with triggers (never bare never/always unless physics or the service), at most one short example. The Loupe keeper matches samples by shared product details and scene mechanism (`--product-details` on `qc-consult`, `qc-brief`, `plan-hints`), answers in conditions, and Loupe holds back a hint worded as a universal command.

**How to apply:** when adding a rule or a lesson anywhere in the pipeline, give it a trigger and the product detail that makes it true, phrase it as a derivation, keep examples to one short mechanism (placeholders or a neutral noun), and let QC judge by intent, product details and physics. Related: [[atp-sample-hints-delicate]], [[atp-skills-architecture]], [[loupe-web-app]].
