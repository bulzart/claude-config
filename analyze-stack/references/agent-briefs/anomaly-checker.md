# anomaly-checker — agent brief (Stage 6; one agent per lens, six in parallel, over ALL prompts together; mode `check` | `pre-check`)

Load first: `LAYOUT.md`, `references\anomaly-checklist.md` (your lens's checks, severities, output format,
fix routing, clean criteria, escalation, edit-prompt additions), and the rule file your lens names:
L1 `physics-rules.md` · L2 `physics-rules.md` §6 + the continuity sheet §A · L3 `prompt-template.md` §2 /
`edit-prompt-template.md` §2 + `SEEDANCE-SPEC.md` §6.4 · L4 `continuity-rules.md` · L5 `blending-rules.md` +
`swap-map.md` + `product-spec.md` · L6 `SEEDANCE-SPEC.md` §3.5, §4, §5, §6, §8 + `SEEDANCE-EDIT.md` §3–§4 +
`sd25-pe\SKILL.md` "Final Checklist". EVERY lens also loads the **Seedance 2.5 Director** bundle (read-only):
`seedance\director\references\continuity-and-causality.md` §5 (the anomaly table: check → repair) and "Cross-cutting
safeguards", `seedance\director\references\prompt-playbook.md` §8 (release gate; blocker / major / polish), and runs
the director categories mapped to its lens in `anomaly-checklist.md` §2b with the severity mapping blocker → S3,
major → S2, polish → S1. The director's "authorized surreal rules" clause applies only when Q5 chose a
non-realistic style; otherwise realism rules (SEEDANCE-SPEC.md §14 precedence).

## Purpose
Review every prompt of the set as one interconnected system through ONE lens (physics, space/layout,
timing, continuity, product consistency, spec compliance) and list every contradiction with a concrete
fix instruction routed to the writer of the affected clip(s). You never rewrite prompts.

## Inputs
All `50-prompts\clip-NN.md` or `edit-NN.md`, `50-prompts\prompts.json`, `40-plan\continuity-sheet.md`,
`40-plan\plan.json`, `30-decisions\swap-map.md` + `product-spec.md` (L5), `30-decisions\edit-intent.md`
(edit approach), `20-analysis\visual.md` (L2/L5: what the original shows), `seedance\SEEDANCE-SPEC.md`,
`seedance\SEEDANCE-EDIT.md`, previous rounds' `60-qa\anomaly-check.md` (to verify fixes landed).
Notes: lens id, round number, approach. `pre-check` mode: `plan.json` + continuity sheet rows instead of prompts.

## Outputs
`60-qa\anomaly-L<n>-round-<N>.md`:
```markdown
# Anomaly check — L5 product consistency — round 1 — result: 2 S3, 1 S2, 3 S1
| id | lens | sev | clip(s) | check | finding (quote the offending line) | fix instruction (for the writer, imperative) |
| F5-001 | L5 | S3 | 03 | PR03 | "…the strawberry one…" | replace with "the orange cream one" (swap-map dialogue rule, Q4a paraphrase allowed) |
| F5-002 | L5 | S3 | 02, 04 | PR01 | 02 says "orange cap", 04 says "white cap" | both copy the identity string from continuity sheet §C verbatim |
Verified fixed from round N−1: F5-0xx, … · Still open: none
```
(`pre-check`: `60-qa\feasibility-precheck.md` — clips with ≥ 2 risky items and a recommendation each, for A3.)
The main session merges the six files into `60-qa\anomaly-check.md`, routes `fixes-round-N.md`, updates `qa.json`.

## Method
1. Read every prompt file completely, in order; build a table of START/END states, counts, positions,
   camera/light lines, product identity strings, timestamps, attachments (whatever your lens needs).
2. Run every check of your lens over every clip AND across clips (a fix in clip 2 can break clip 3);
   quote the offending line; assign the severity from the checklist; write the fix as an instruction the
   writer can apply without interpretation (which block, which sentence, what to write instead).
3. Edit prompts (approach = edit): also run the edit additions — stays-as-filmed completeness (every
   visible subject category in the segment's shots is either in WHAT CHANGES or covered by the preservation
   block) and no contradictory change (nothing both replaced/removed and "kept exactly as filmed"; no two
   operations on the same target with different outcomes); identical wording across segments (L4/L6).
4. L5 mechanical pass: grep every prompt for the original brand name, product name, slogan, hashtag,
   handle, flavour words and colourway-as-brand words from `swap-map.md` REMOVE lines and `entities.json`
   brand_marks; any hit is S3 (PR03).
5. Round ≥ 2: first verify that each finding routed to writers in the previous round is fixed; re-open
   with a new id if not.
6. Director pass (all lenses, on the SET): read each prompt as a stranger with no sheet access — does every
   later use have a compatible earlier state inside the prompt text itself? Is the required METHOD visible
   (acquire → transport → deposit → return, repetitions, hand occupancy) or hidden behind a bridge verb, a cut,
   blur or an occluder? Do passive processes continue (settling, drips, foam)? Is "hidden" confused with "absent"?
   Report each as the mapped lens check id with the director category name in the `check` column
   (e.g. `L4 · custody/support`).

## Quality bar
- Zero false positives on quotes: every finding quotes text that exists in the file it names.
- Fix instructions are complete sentences the writer pastes or applies; no "consider" / "maybe".
- Cross-clip checks are explicit (`02→03`).

## When evidence is missing
If a check needs the continuity sheet row and the row is empty, report that as S3 against the sheet
(clip "sheet"), not against the writer. If you cannot decide a physics claim (e.g. the viscosity of the
owner's product is unknown), report S1 "unverifiable" with what evidence would settle it.
