# Ranking (2026-10-12T11:24:27+02:00)

Weights: demand 15, commercial 15, fit 20, economics 15, competition 10, compliance 10, logistics 5, timing 5, producibility 5
Independent-evidence cap: a criterion in ['commercial', 'competition', 'compliance', 'demand', 'economics'] without a positive independent grade A/B row (C for economics) is capped at 2; negative rows that match or outnumber the positive ones cap a 4 or 5 at 3.

## Picks

| # | id | product | niche | score | raw | no-fit | capped criteria | contribution % | conf | red team | dominant niche |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | C13 | Pet nail grinder | pets | 94.0 | 94.0 | 92.5 | - | 50.4 | high | survives | yes |
| 2 | C12 | Quiet pet water fountain | pets | 94.0 | 94.0 | 92.5 | - | 50.4 | high | survives | yes |
| 3 | C20 | Heatless curl ribbon | hair | 88.0 | 94.0 | 85.0 | demand | 50.4 | high | - | no |

## Runner-ups

| id | product | niche | score | why not a pick |
|---|---|---|---|---|
| C14 | Orthopedic pet bed | pets | 87.0 | lower independent score than the picks |
| C17 | Collapsible silicone lunch box | kitchen | 77.0 | lower independent score than the picks |
| C16 | Magnetic cable clips | desk | 77.0 | lower independent score than the picks |

## Not eligible

| id | product | score | gate failures |
|---|---|---|---|
| C26 | Compliance-D-only bag | 82.0 | G1 economics: no sourced input behind the calculation (a grade A or B economics row: the supplier price, the fee schedule, the freight or duty source); G2 compliance: no positive independent grade A/B compliance row behind the status; G5 floor: economics 2 < 3 (after the evidence cap); G5 floor: compliance 2 < 3 (after the evidence cap) |
| C18 | Mini portable blender | 77.0 | G2 compliance: open |
| C24 | Thin evidence gadget | 75.0 | G1 economics: no sourced input behind the calculation (a grade A or B economics row: the supplier price, the fee schedule, the freight or duty source); G4 independent evidence: 1 distinct source(s) with positive grade A/B rows in demand, commercial and competition (need 2, one of them commercial); G5 floor: commercial 2 < 3 (after the evidence cap); G5 floor: economics 2 < 3 (after the evidence cap) |
| C25 | Negative-signals tool | 66.0 | G1 economics: no sourced input behind the calculation (a grade A or B economics row: the supplier price, the fee schedule, the freight or duty source); G4 independent evidence: 0 distinct source(s) with positive grade A/B rows in demand, commercial and competition (need 2, one of them commercial); G5 floor: demand 2 < 3 (after the evidence cap); G5 floor: commercial 2 < 3 (after the evidence cap); G5 floor: economics 2 < 3 (after the evidence cap) |
| C15 | Pet hair glove | 60.0 | G1 economics: no sourced input behind the calculation (a grade A or B economics row: the supplier price, the fee schedule, the freight or duty source); G2 compliance: no positive independent grade A/B compliance row behind the status; G4 independent evidence: 0 distinct source(s) with positive grade A/B rows in demand, commercial and competition (need 2, one of them commercial); G5 floor: demand 2 < 3 (after the evidence cap); G5 floor: commercial 2 < 3 (after the evidence cap); G5 floor: economics 2 < 3 (after the evidence cap); G5 floor: compliance 2 < 3 (after the evidence cap) |
| C23 | Stain remover stick | 60.0 | G6 confidence: low < medium |
| C21 | Travel compression cubes | 57.0 | G1 economics: no sourced input behind the calculation (a grade A or B economics row: the supplier price, the fee schedule, the freight or duty source); G5 floor: economics 2 < 3 (after the evidence cap) |
| C22 | Posture corrector band | 53.0 | G1 economics: no sourced input behind the calculation (a grade A or B economics row: the supplier price, the fee schedule, the freight or duty source); G2 compliance: no positive independent grade A/B compliance row behind the status; G3 excluded by the brief; G4 independent evidence: 0 distinct source(s) with positive grade A/B rows in demand, commercial and competition (need 2, one of them commercial); G5 floor: demand 2 < 3 (after the evidence cap); G5 floor: commercial 2 < 3 (after the evidence cap); G5 floor: economics 2 < 3 (after the evidence cap); G5 floor: compliance 2 < 3 (after the evidence cap) |

## Warnings and blockers

- BLOCKER: pick(s) ['C20'] have no red-team verdict: red-team them (`candidates set --redteam survives|weakened|fails`)
- a niche was added or merged after the last audit, or the vocabulary was never audited: the niche limits rest on an unaudited vocabulary; have a fresh agent audit it again (viral-browser.md section 13.5) and record `niches audit`
- pick C20 was edited after research (definition: 'lifts pet fur from sofas' -> 'Heatless curl ribbon: test', a sentence that says why, long enough to count as an argument; category: 'hair' -> 'kitchen tools', a sentence that says why, long enough to count as an argument; category: 'kitchen tools' -> 'hair', a sentence that says why, long enough to count as an argument): check that this is not a way around the niche limits or the dominant-niche defence
- the picks differ when reference-derived evidence is allowed to count: the independence rules changed the outcome; say so in the bias log

## Decisions on record (niche vocabulary and overrides)

- Niches (22): bags, cleaning, desk, diy, fitness, gadgets, hair, health, home organization, kitchen, kitchen tools, outdoor, pet feeding, pet grooming, pet toys, pets, serving, tea, travel, wardrobe, पानी, पुनः
- Audit: by niche-auditor-test at 2026-10-12T11:23:24+02:00: no synonyms found; no merges needed (STALE: a niche was added or merged since)
- Merge: kitchen gear -> kitchen: the same shelf and the same buyer (2026-10-12T11:23:01+02:00)
- Merge: canine gear -> pets: the same buyers: dog owners (2026-10-12T11:23:02+02:00)
- Merge: fishing -> outdoor: test: the label now resolves to another niche (2026-10-12T11:24:20+02:00)
- Judged distinct: kitchen tools / kitchen: cookware is bought for another job than appliances (2026-10-12T11:23:00+02:00)
- Judged distinct: pet feeding / pet grooming: feeding bowls and grooming tools are different shelves (2026-10-12T11:23:16+02:00)
- Judged distinct: pet feeding / pets: feeding supplies are bought apart from general pet care (2026-10-12T11:23:16+02:00)
- Judged distinct: pet grooming / pets: grooming tools are bought apart from general pet care (2026-10-12T11:23:17+02:00)
- Judged distinct: pets / kitchen tools: pet supplies and kitchenware are bought in different places (2026-10-12T11:24:19+02:00)
- Judged distinct: kitchen / desk: kitchenware and desk accessories are bought in different places (2026-10-12T11:24:24+02:00)
- Judged distinct: kitchen / bags: kitchenware and bags are bought in different places (2026-10-12T11:24:24+02:00)
- Judged distinct: desk / bags: desk accessories and bags are bought in different places (2026-10-12T11:24:24+02:00)
- Word judged not a niche marker: bamboo: a material or modifier, not a niche marker at all (2026-10-12T11:23:09+02:00)
- Edited after research: C20 name: 'Heatless curl ribbon' -> 'Pet-safe heatless curl ribbon': a sentence that says why, long enough to count as an argument (2026-10-12T11:24:16+02:00)
- Edited after research: C20 name: 'Pet-safe heatless curl ribbon' -> 'Heatless curl ribbon': a sentence that says why, long enough to count as an argument (2026-10-12T11:24:18+02:00)
- Edited after research: C20 definition: 'Heatless curl ribbon: test' -> 'lifts pet fur from sofas': a sentence that says why, long enough to count as an argument (2026-10-12T11:24:18+02:00)
- Edited after research: C20 definition: 'lifts pet fur from sofas' -> 'Heatless curl ribbon: test': a sentence that says why, long enough to count as an argument (2026-10-12T11:24:18+02:00)
- Edited after research: C20 category: 'hair' -> 'kitchen tools': a sentence that says why, long enough to count as an argument (2026-10-12T11:24:19+02:00)
- Edited after research: C20 category: 'kitchen tools' -> 'hair': a sentence that says why, long enough to count as an argument (2026-10-12T11:24:20+02:00)
- Edited after research: C24 category: 'gadgets' -> 'diy': a sentence that says why, long enough to count as an argument (2026-10-12T11:24:04+02:00)
- Edited after research: C24 name: 'Thin-evidence gadget' -> 'Thin evidence gadget': a sentence that says why, long enough to count as an argument (2026-10-12T11:24:06+02:00)
