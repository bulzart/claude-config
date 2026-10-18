## 10. Deliverables (V7–V8)

### 10.1 Files, all in `<RUN>/deliverables/`

| file | content |
|---|---|
| `viral-browser-report.md` | the whole result (§10.2) |
| `product-01.md`, `product-02.md`, `product-03.md` | the pick's full dossier (the economics table, the lane findings, the red-team findings) and its blueprint (§9) |
| `evidence.md` | the evidence ledger rendered with `T evidence list --run RUN --out <RUN>/deliverables/evidence.md`: claim, value, grade, signal, independence, market, date, source |
| `reference-C##-<name>/` (one per pick) | the pick's reference pack (§9.1; `product-NN.md` links to it): `spec.md` and `spec.json` (the sourced specification, each field with the pack agent's judgement), `photos.md` (the image links, their status and flags, and the coverage table), `photo-links.json` (the same links as data) and `photos.html` (a gallery of them), and `NOTES.md` (including the reference set the pack agent recommends) |
| `create-handoff.md` | for each pick: the definition, audience model, goal line, trend read, the fit profile, the assets Create needs (samples, a contents shot, real dimensions; the reference pack stands in until the user's own sample photos exist) and the anomaly-catalog risks of its affordances; the command to continue (§11.4) |
| `README.md` | the index of the files and the run folder |

### 10.2 The report

1. **Summary table**: the three picks (product, niche, role, price band, contribution %, break-even CPA and ROAS on the amount paid, the stress case, confidence), the runner-ups, the date and the market.
2. **The essence and the fit profile** (from `viral-essence.md`).
3. **Each pick**: definition; why it fits (mechanisms); demand; commercial proof; economics (the `econ` table and the price ladder: the contribution at the no-name tier's price and at the brand tier's price); competition and angle; compliance and logistics; the reference unit, the specification table (each field with the pack agent's judged value, its status and reason, and the sources) and the photo links by angle with their status and flags (§9.1); red-team result; confidence and what would change it; the blueprint's headlines; next steps.
4. **Runner-ups** and why they are not picks.
5. **Eliminated** candidates with the gate or reason, including dominant-niche candidates that did not survive.
6. **Method and bias-control log** (the bias log of `ranking.md`): the niche-concentration line with the figures read, the niche vocabulary with its merges and audit, the pool and shortlist checks and repairs, each rule of thumb applied and each set aside with its reason, the limits applied, any tie at the pick boundary and how it was broken, both what-if results, the defence notes, the red-team readings.
7. **Unknowns and unreachable sources**, and what each would change.
8. **Sources**: the evidence table.

### 10.3 Chat summary

One table of the three picks (with the reference unit, size, weight, material and the pack's photo-link coverage) and three lines on the method; the decisions needed from the user (§11); the path to the deliverables. The full report is the file. Do not create a shared document unless the user asks.

### 10.4 Report QC (V8)

Before the summary is shown:
1. Every number in the report is a row in the evidence ledger (source, date) or is reproduced by `T econ`; recompute each pick's economics.
2. Each pick meets the six gates (§8.3) by the main session's reading of `T candidates table` and the evidence, and the report quotes that reading per pick (the figure read, and any number set aside with its reason).
3. The dossiers contain no reference to the reference videos or to a candidate's origin.
4. Every dominant-niche pick has its defence note.
5. One currency and one tax convention throughout; EU or global claims rest on market-region evidence, or carry the "market gap" flag.
6. Spot-check up to `verification_budget` (12) key claims of the picks (a price, a sold count, a fee, a compliance statement) by fetching the source again; correct what differs.
7. No hook or claim in the blueprint is unsupported, and no deceptive tactic is recommended (§0 rule 7).
8. Each error a research agent made that reached this step (a wrong figure, a dead link, an invented source) is corrected and noted in the bias log with its cause.
9. Each pick has its reference pack: the report quotes the `T spec gaps` counts (facts and judgements per core field) and the `T photo check` coverage table, with the main session's own reading of whether the pack is enough; every size, weight and material in the report is a fact of `T spec` (source, grade, date) shown with the pack agent's judgement (status and reason) and none was read off a photo; the pack names its reference unit and its variant; each photo link has its source page, its angle with the basis for it, its link status and its rights status; the report says that no image was downloaded and that none was looked at unless a row says so, and a blocked or unconfirmed link is listed as such; `NOTES.md` exists and `photo-links.json` is current (`T photo check` was the last command run). Up to three facts per pick are fetched again against their source (part of the item 6 budget).
10. A conflict between sources is shown with both values and the choice made (the pack agent's judgement says which value it stands behind and why); nothing is called verified that rests on two pages that copy each other, and the main session corrects such a label when it reads the judgements.

