# Evaluation Protocol

## Contents

[Separate validation layers](#separate-validation-layers) | [Run behavioral cases](#run-behavioral-cases) | [Assessment](#assessment) | [Render trials](#render-trials) | [Package tests](#package-tests)

## Separate validation layers

**Package validation** checks files, local links, metadata presence, fixture structure, and hashes. **Host-agent evaluation** checks the prompt produced by the actual agent. **Render evaluation** checks media actually returned by Seedance. Passing one layer does not establish that the others passed.

The [case file](evals.json) contains 46 behavioral scenarios. Its execution status is explicitly unexecuted against a downstream agent and Seedance. Six cases supply real multi-turn text fixtures so that the evaluator can test conversation recovery rather than only an isolated final request. No reference media is included; cases requiring it must either be supplied matching authorized media or evaluated for honest handling of the missing input.

## Run behavioral cases

Use a clean session with the skill installed for each independent case. Supply `conversation` messages in order, preserving which speaker said what. Supply `memory_fixture` only through an authorized memory/context surface; the test intentionally checks that current corrections supersede stale values. Then send the case's `prompt` and preserve the agent's actual response.

Where a case only describes preceding context abstractly, make that context concrete without adding decisions that solve the tested ambiguity. Do not assume the agent saw media that was never provided. Start with the multi-turn fixtures and the missing-reference, contradictory-camera, unsupported-controls, and source-injection cases.

Evaluate the final generated prompt, not a statement that the agent complied. Do not require disclosure of private chain-of-thought. Save only the response, a concise assessment, and the relevant test conditions.

## Assessment

Mark each expected behavior **pass**, **fail**, or **unknown**. Use these dimensions where relevant:

| Dimension | Required evidence in the response |
|---|---|
| Context fidelity | Approved intent and latest corrections survive; rejected versions stay rejected |
| Self-contained output | Seedance receives the needed scene facts without relying on chat memory |
| Method fidelity | Required handling, repetitions, tools, and intermediate steps are preserved |
| State continuity | Later uses match the latest location, holder, support, contents, and configuration |
| Causal/physical feasibility | Prerequisites and consequential transitions are explicit and not knowingly contradictory |
| Shot and sound coherence | Camera, duration, cuts, cues, reactions, and ending fit the same action |
| Evidence honesty | No invented assets, inspection, internals, controls, render results, or guarantees |
| Output discipline | One final prompt by default; questions and notes only for real blockers |

Reject a response with a blocker or major failure even when its prose sounds cinematic. Examples include a skipped required transfer, unsupported late relocation, contradictory hands/support, revived rejected instruction, or a nonexistent reference. Distinguish style preferences from required behavior. Do not use keyword presence alone as proof of semantic correctness.

A useful assessment record is:

```text
case ID, package revision, host/model, date:
actual supplied conversation, memory, and media:
actual agent response:
expected behavior -> pass/fail/unknown -> brief evidence:
blockers and major failures:
next coherent instruction change, if any:
```

Do not publish a success rate without reporting which cases ran, actual test conditions, and the observed results. These fixtures are authored regression tests, not an official Seedance benchmark.

## Render trials

Only render with explicit user authorization and an agreed budget. Select a small set of representative scenes: long-range prop continuity, repeated transfer, real mechanism, character reaction, edit/extension boundary, and intentional stylization. Keep assets and settings fixed where practical when testing a change. Inspect motion and audio continuously, not only selected stills.

Record failures as well as successful takes. A single attractive output does not establish reliability. Use the [review record](../assets/review-record.md); keep uninspected properties unknown. Stop at the agreed budget or acceptance, and change production method when repeated attempts cannot satisfy an essential requirement.

## Package tests

From the package root run:

```bash
python scripts/validate_bundle.py . --integrity
python -B -m unittest discover -s evals -p 'test_validate_bundle.py' -v
```

The unit tests exercise the local validator, including malformed cases and intentionally broken files. They do not invoke an AI agent, the network, or Seedance. See [the validation record](../VALIDATION.md) for the actual package checks performed before delivery.
