---
description: Read a command's caught_errors.md ledger, find the patterns behind its failures, reverse-engineer their causes, and fold the lessons into that pipeline's first-try prompting, use cases, examples, instructions and QC.
argument-hint: "<command-name> [dry-run] [only CE-nnn,CE-nnn…]   e.g. analyze-then-pick"
disable-model-invocation: true
disallowed-tools:
  - Workflow
---

# /update-from-errors

Arguments: `$ARGUMENTS`

You are running **/update-from-errors**. When a pipeline command was first built, it had little
real context: few generation examples, an untested idea of what counts as an error and of what a
good prompt looks like. Its `caught_errors.md` ledger now holds what really went wrong, both what
QC agents caught and what the user saw after delivery. This command turns that record into better
first attempts: it reads the ledger and finds the patterns. It works out why each one happened.
Then it rewrites the pipeline's prompting logic, use cases, examples, instructions and QC so that
the next run gets it right the first time and QC finds nothing.

## 0. Contract

1. **The argument is required.** The first word names the command whose ledger is read
   (`analyze-then-pick`). Without it, list the ledgers that exist (Glob
   `~/.claude/**/caught_errors.md`, plus the matching `~/.claude/commands/<name>.md` for each),
   say "Run `/update-from-errors <command-name>`", and stop. Do not guess.
   - **`dry-run`**: do everything up to §4 and show the change set, but write nothing.
   - **`only CE-012,CE-013`**: restrict the pass to those entries. The rest of the ledger is still
     read as context.
2. **Normal command, never a workflow.** It uses ordinary tools in this conversation. At most two
   read-only Explore agents are allowed, and only to sweep a large library. It makes no paid
   calls and no generations; it learns from what is already on disk.
3. **Evidence decides the strength of what is written** (§3.3).
   - A **proven** lesson is backed by a verified prompt and a passing QC verdict, or by the user
     approving the fix. It is written as an instruction and an example.
   - A **repeated** lesson (two or more entries of one pattern) is written as a rule plus a QC
     check.
   - A **single, unproven** entry is written only as what to avoid, plus a QC check. Never present
     a guessed fix as if it had worked.
4. **A user entry outranks an agent entry** on the same point, because the user saw what QC
   passed. Where the user's feedback contradicts a rule the pipeline holds, the rule changes.
5. **Rewrite, don't stack.**
   - Each lesson goes into the section that owns it, in that file's voice and format.
   - A rule that already exists and failed again is **replaced**: a promoted rule that recurred did
     not work, so repeating it louder is not a fix.
   - Superseded wording is removed, and no "lessons learned" dump is appended anywhere.
   - Text stays compact: one line per rule, one short good/bad pair per example.
6. **QC only gets stricter or more precise.** It is loosened only when an entry shows a false
   positive (QC rejected what the user accepted).
7. **Never touch:**
   - the ledger's entries other than through its own tool, and never delete one: the ledger is
     the record;
   - `runs/` or other run data;
   - locked user preferences (memory files, locked config such as a CapCut text preset);
   - the hard rules a command marks as fixed, unless an entry is the user explicitly overriding one.
8. **Preserve each file's line endings.** Read and write bytes; if the file is CRLF, write CRLF.
   Back up the build prompt before changing it, as `.bak-YYYYMMDD-HHMMSS` beside it.
9. **Honest reporting.** Every change names the entries behind it. Anything left unresolved is
   reported as open, together with the test that would settle it.

## 1. Resolve the pipeline

| name | value |
|---|---|
| `CMD` | `~/.claude/commands/<name>.md` |
| `LIB` | `~/.claude/<name>/` (else the folder that holds the ledger) |
| `LEDGER` | `LIB/caught_errors.md` |
| `LOG` | `LIB/learning-log.md`: one section per pass of this command (§6) |
| `BUILD` | the build prompt, if the user keeps one. Find it through the memory index (an entry naming "<name> build prompt") or `~/Documents/prompts/<name>.txt`; otherwise none |

If `LEDGER` is missing or has no entries, say so and stop.

Read:
- the ledger's header, which defines its fields, sources, statuses and tool;
- **all** of its entries;
- `LOG`, if it exists, for the passes already made: which entries were consumed, what changed, and
  which hypotheses were left to test;
- the memory index, for locked preferences and constraints that must not be edited away.

**Map the pipeline before judging anything.** Read `CMD` and record which file and section owns
each of the following. This map is `<target map>`, used in §4.

| owner | what it holds |
|---|---|
| first-try prompting | the prompt structure, the translation into the model's language, the prompting stack |
| model guides | per-model phrasing, parameter gotchas, failure table, checklist, examples |
| use cases | when a reference, form, technique or operation is chosen or dismissed (selection, ranking, integration choices) |
| examples | official prompt examples, worked examples, good/bad pairs |
| instructions | the plan and brief rules, the step lists in `CMD`, the agent contract |
| error definitions | what counts as an error: anomaly classes, must-not-survive lists, thresholds |
| QC | the post-generation QC, the QC stack, the verdict format, the agents' QC duties, measurable checks |
| toolkit | scripts whose checks or defaults encode a rule |

For `analyze-then-pick` the map is known. Confirm it exists before using it:
- first-try prompting: `reference/generation-system.md` §7–§8, `reference/anomaly-catalog.md` §3,
  and `models/<model>.md` §3–§4 (§4.0 holds the examples);
- use cases: `reference/analysis-protocol.md` (ranking), `generation-system.md` §4b (forms,
  anchors), `reference/assets-and-substitution.md`, `reference/creative-direction.md`;
- error definitions: `anomaly-catalog.md` §2 (classes and thresholds), `generation-system.md` §9b;
- QC: `generation-system.md` §9, `anomaly-catalog.md` §4 and §4.1 (verdict examples),
  `reference/production-agents.md` §3, and `CMD` X4 / X9;
- model failure modes: `models/<model>.md` §5 (failure table), §7 (checklist) and §9 (open
  questions);
- toolkit: `scripts/atp.py` (`scale`, `qc`, `sync-check`, `caught-error`).

## 2. Read every entry, then check it against its evidence

For each entry in scope, build a row: id, source, status, mode, model, product, class, cause, what
was wrong, rule, prompt (failed), verified prompt and prompt change (if any), params, errors,
evidence, and the brief's intent.

For the entries in scope, check the diagnosis against what is still on disk. Read selectively,
only what settles a question:
- the brief and plan paths: did the plan already intend the right thing, so the prompt or the
  model lost it, or was the plan itself wrong?
- the request JSON: what was actually sent (media roles, durations, flags), not what the entry
  says was sent;
- the evidence path (QC frames or sheets): look at the named frame when the diagnosis is in doubt,
  or when two entries disagree.

Mark each row's diagnosis **confirmed**, **corrected** (say how) or **unverifiable** (files gone).
A missing file is not an error; note it and move on.

## 3. Find the patterns and reverse-engineer them

### 3.1 Cluster

Group the rows by what really failed, not by the wording of their titles:
- the same class (the anomaly class, the text rule, the guardrail);
- the same product family;
- the same model;
- the same operation or media roles;
- the same cause;
- the same placement or technique.

One entry can sit in two clusters. Also note the **cross-cuts**: one model failing across several
classes, or one class failing across several models.

### 3.2 Reverse-engineer each cluster

Answer these, citing ids:

1. **What did the plan intend, what did the prompt say, and what came out?** Find the step where
   intent and output parted: the plan, the translation, the parameters, the model, or QC.
2. **Which lever caused it?** Pick one or more:
   - wording: an instruction missing, vague, buried or contradicted;
   - structure: placement in the prompt, or a positive line without its exclusion;
   - parameter or media role;
   - an asset-prep problem (padding, framing, a reference image that teaches the wrong scale);
   - plan choice (the anchor, the depth, the operation, the reference itself);
   - model limit, where no wording fixes it and only a different technique or a post step does;
   - QC miss, where the check was absent, unmeasured or below threshold;
   - use case, where a reference or form should have been dismissed or chosen differently.
3. **Why did the existing rule not prevent it?** Check whether the rule was missing, present but
   ignored by this model, or present but unmeasured.
   - A cluster that recurs after a promotion or a `LOG` change means **that change failed**. Say
     what it assumed that was false. For example: "a frame fraction in words controls size on Wan
     3.0 Prime: false, ignored in CE-011, CE-014 and CE-015".
4. **What works?**
   - Verified prompt changes and passing verdicts: the sentence-level diff is the strongest
     evidence in the ledger.
   - Then patterns that appear only in the passing attempts.
   - Then the model guide's official guidance.
5. **What should QC have measured, and at what threshold,** to catch it on the first output, or
   to reject it before a credit was spent (the pre-generation check)?

### 3.3 Grade each lesson

| grade | evidence | written as |
|---|---|---|
| **proven** | a verified prompt that passed QC, or a fix the user approved | an instruction + a good/bad example (failed vs verified wording) + a QC check |
| **repeated** | two or more entries, consistent cause | a rule in the owning section + a measurable QC check + the failed wording as a bad example |
| **single** | one unverified entry | an avoid line + a QC check; at most a "to test" hypothesis in `LOG` and the model guide's open questions |
| **model limit** | the same failure despite correct wording, two or more times | the model guide's failure table with the workaround technique (a different operation, start frame, post step or plan choice), plus a use-case change: when not to attempt it on this model |
| **false positive** | QC flagged what the user accepted | the QC threshold or check made more precise |

Lessons from a model apply to that model's guide only. They move into the model-agnostic
references only when two or more models show the same thing.

## 4. Build the change set

For every lesson, write one change row:
`file § section | change kind | the new text (or the replacement) | CE ids | grade`.
The change kinds are:
- **Prompting logic:** the first-try instruction in the owning section, written so a planner
  applies it before generating. Use the model's own phrasing and include its exclusion syntax.
- **Use case:** when to choose or dismiss a reference, form, anchor, technique or operation,
  including "on model X, do not attempt Y; do Z".
- **Example:** a short good/bad pair. The bad side is the failed wording, quoted from the entry.
  The good side is the verified wording if one exists; otherwise there is no good side, only "avoid
  this". Put it in the owning model guide's examples section (§4.0 in ATP guides) or the
  reference's examples, never in a new file.
- **Instruction:** a plan or brief rule, a step in `CMD`, an agent-contract line.
- **Error definition:** what now counts as an error: a new class, a widened class, or a threshold.
- **QC:** a measurable check at the right stage (pre-generation, first output, final). Give its
  threshold, its tool if one exists, the verdict line it writes, and whether a failure means
  regenerate or a note. Add a line to the verdict examples.
- **Toolkit:** a default or a check in a script, only if a rule is better enforced by a tool than
  by text. Keep it a small change, and test it.

Then review the set as a whole:
- no two rows contradict each other or an existing hard rule;
- nothing duplicates a rule that already exists. Merge or replace instead, removing the old text
  where it is superseded;
- every QC row has a threshold, and every prompting row has the model's phrasing;
- every change traces to entries, and no change rests only on an unverified guess.

**`dry-run`:** print the patterns (§3) and the change set as a table, then stop.

## 5. Apply

1. Edit each file in place. Keep its section structure, voice, numbering and line endings. Edit
   scripts handle CRLF, validate every anchor before writing anything, and write bytes.
2. Update `CMD` wherever a step, a check or a "Never" changes, and keep its numbered items
   consistent.
3. **Mark the entries in the ledger, using its tool only.** For ATP:
   - Promote an entry whose rule now lives in a reference:
     `"$PY" -X utf8 "$LIB/scripts/atp.py" caught-error set --id CE-nnn --status promoted
     --promoted-to "<file §, file §>"`.
   - A **proven** entry is promoted with its pointer.
   - A repeated or single entry is promoted with its pointer **and stays as the record**. Its
     fields are not touched, and its fix is never marked as verified.
   - An unresolved model-limit entry stays `open`; its pointer names the failure-table row.
   - Ledgers without a tool are edited in their own format, by the same rules.
4. **Build prompt:** if `BUILD` exists, back it up and then fold in the changes, in its own prose
   style, where it describes the owning parts. It specifies the pipeline, so it changes when the
   pipeline does.
5. **Verify:**
   - every anchor you changed reads correctly when read back;
   - the toolkit still runs (`atp.py --help`, plus the changed command on a small input);
   - `caught-error list --rules` still parses every entry;
   - no file changed its line endings unintentionally (`git diff --stat`, plus a CRLF check).
6. **Commit** in `~/.claude` (a git repo with auto-commit hooks): one commit,
   `<name>: update from caught errors CE-a..CE-b (<n> patterns)`, with the change list in the
   body.

## 6. Learning log (`LIB/learning-log.md`)

Append one section per pass, compactly:

```
## <date> · CE-001..CE-015 · <n> patterns · commit <hash>
- **Patterns:** P1 <one line> (CE-005, CE-011, CE-014, CE-015; repeated; model limit on wan3_0_prime) …
- **Root causes:** P1 <the lever, and what the earlier rule wrongly assumed> …
- **Changes:** <file §>: <one line> (P1) …
- **Promoted:** CE-… → <pointer>; **left open:** CE-… (<why>)
- **To test:** <hypothesis> → measure <what> on the next run of <model/class>; proven when <criterion>
```

The next pass reads this first. A pattern that recurs after a logged change means that change
failed, and it is revised, not repeated.

## 7. Report

In a short table, give: pattern → entries → root cause → grade → what changed (file §).
Then give:
- the entries promoted, and the ones left open, with the reason;
- the hypotheses to test, and what the next run should measure;
- any diagnosis corrected in §2;
- the files changed, the build-prompt backup and the commit hash.

In dry-run, end by offering to apply. Otherwise, end by offering, in one line, to run the pipeline
on a small batch that exercises the changed rules.

## 8. Never

- Never run without the command-name argument, and never guess it.
- Never generate, preflight or spend credits.
- Never use a Claude Code Workflow.
- Never delete or rewrite a ledger entry's content. Use its tool to set status and pointer only.
- Never present an unverified fix as working, or write a "good" example that never passed QC.
- Never re-promote a recurring rule unchanged. Find what it got wrong, and replace it.
- Never stack a new rule beside an old one it supersedes.
- Never append a lessons-learned dump instead of editing the owning section.
- Never generalise one model's failure to every model.
- Never loosen QC without a false-positive entry.
- Never edit locked user preferences, run data or a file's line endings.
- Never change a file you did not read first.
- Never skip the build-prompt backup and update, the learning log, or the commit.
