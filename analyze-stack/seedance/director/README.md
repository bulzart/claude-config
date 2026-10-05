# Seedance 2.5 Director

Version 2.1.0. A conversation-aware prompt-writing skill with whole-video continuity, causal planning, and scene-specific anomaly checks.

## What to install

Install the **entire `seedance-2-5-director` folder**, not only its entrypoint. Keep `SKILL.md`, `agents`, `references`, `assets`, `evals`, `scripts`, and `docs` together. The archive contains one skill; it is not a collection of separate skills.

Use your agent's documented skill importer with `skill.zip`, or extract the folder into its configured skill directory. No universal install path is assumed. Configure the host to discover the `SKILL.md` name and description, load its instructions when relevant, and follow relative references on demand. Loading the ZIP as an ordinary attachment does not by itself establish automatic invocation.

For an agent with only one-document support, load [the standalone guide](docs/seedance-2-5-agent-guide.md) as project instructions or a retrievable knowledge file. Configure the host to read it for Seedance prompt requests. The standalone edition includes the operating guidance, templates, and behavioral cases; optional package utilities remain in the ZIP.

## Host instruction example

Adapt the file location to the actual host; this is an instruction snippet, not a universal installation command.

```text
For Seedance prompt requests, read seedance-2-5-director/SKILL.md and the
relevant supporting files before answering. Use the current conversation,
latest approved corrections, accessible project memory, and actual assets.
Apply the whole-video continuity and release checks. By default return one
finished, self-contained prompt. Do not assume memory or tool permissions
that the host has not granted, and do not render merely to write a prompt.
```

If the host does not support relative-file loading, use the standalone guide rather than loading only the compact entrypoint.

## Expected behavior

After discussing a video, say: **"Generate the Seedance 2.5 prompt."** The agent should recover the approved intent, establish the initial scene, plan prerequisites and consequences, track important entities across the whole timeline, check the actual final wording, and deliver one prompt. It should not repeat answered questions or leave essential scene facts as "as discussed."

The checks are subject-independent. They address identity, world location, custody, support, repetition, changing contents, material behavior, mechanism, causality, timing, camera, audio, and the final state. They must not import the example props, counts, materials, or styles into unrelated work. Authorized magic and stylistic exceptions remain allowed within the approved world rules.

## Package map

| Item | Purpose |
|---|---|
| [SKILL.md](SKILL.md) | Discovery metadata, core workflow, output contract, and resource routing |
| [agents/openai.yaml](agents/openai.yaml) | Display metadata for compatible skill interfaces |
| [Prompt playbook](references/prompt-playbook.md) | Conversation recovery, asset ownership, camera, timing, and compilation |
| [Continuity reference](references/continuity-and-causality.md) | World-state ledger, causal dependencies, and anomaly checks |
| [Worked examples](references/examples.md) | Ten original examples/patterns and acceptance checks |
| [Model logic](references/model-logic.md) and [source registry](references/sources.md) | Engineering background with explicit evidence/version boundaries |
| [Provider checks](references/provider-checks.md) | Real execution contracts, edit/extension distinctions, permissions |
| [Quality and iteration](references/quality-and-iteration.md) | Review evidence, diagnose defects, revise connected instructions |
| [Production worksheet](assets/job-template.md), [context handoff](assets/context-handoff.md), [continuity ledger](assets/continuity-ledger.md) | Optional reusable planning records |
| [Prompt template](assets/prompt-template.md) and [review record](assets/review-record.md) | Submission structure and explicit pass/fail/unknown criteria |
| [Evaluation guide](evals/README.md) and [cases](evals/evals.json) | 46 downstream-agent behavioral cases, including six multi-turn fixtures |
| [Validator](scripts/validate_bundle.py) and [unit tests](evals/test_validate_bundle.py) | Optional local package-integrity checks; not a physics or video validator |
| [Standalone guide](docs/seedance-2-5-agent-guide.md) | One-file reading edition for single-document hosts |
| [Validation record](VALIDATION.md) and [manifest](manifest.json) | What was checked, what was not, and file hashes |
| [Changelog](CHANGELOG.md) | Revision history |

## Requirements and permissions

Normal prompt writing requires a language-model agent that can read Markdown and the relevant supplied context. It requires no Python, API key, additional package, or video connector. Memory retrieval, browsing, media inspection, generation, and persistent storage work only when the host actually supports and authorizes them.

The optional package validator and its unit tests use Python 3.10 or newer and the standard library only. Run them from the skill folder:

```bash
python scripts/validate_bundle.py . --integrity
python -B -m unittest discover -s evals -p 'test_validate_bundle.py' -v
```

The validator is local and read-only. It does not make network requests, submit prompts, spend credits, or inspect generated video. Its pass means the packaged files satisfy its structural checks, not that an agent or model will obey every instruction.

## Context handoff and privacy

Use the context-handoff template when work spans sessions. Record approved facts, corrections, provenance, unknowns, and actual continuation states. Do not store private reasoning, secrets, unrelated personal details, or private signed URLs. Save only to an authorized project location. The host must explicitly provide the record on a later run; this skill does not create account-wide memory access.

## Evidence and limitations

The sources and engineering notes are carried forward from the supplied prior guide's September 17, 2026 research snapshot. This packaging revision did not newly verify external source pages. Recheck changing capabilities and provider contracts before execution. Model claims, provider behavior, predecessor research, authored heuristics, and observed output remain distinct.

No Seedance rendering or downstream-agent execution was performed to validate these prompts. A correct specification can still produce an incorrect take. Inspect actual output for temporal continuity, contact, material behavior, sound, and the requested ending. Do not mistake still-frame checks for full video evaluation or a visual demonstration for engineering proof.

## Updating the package

Edit canonical instructions in `SKILL.md` and `references`, and revise relevant templates and regression cases. Keep one authoritative instruction per decision; update connected examples when the rule changes. Regenerate the standalone reading edition after content edits. Re-run structural and behavioral checks separately. Regenerate `manifest.json` hashes after the final changes and package the complete single-skill folder as `skill.zip`.

Keep final archives below 25 MB. Do not bundle credentials, model weights, private media, downloaded papers, or unrelated assets. Review evidence from actual failures, generalize the failure class, and avoid hardcoding one scene into every future prompt.
