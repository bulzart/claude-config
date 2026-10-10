---
description: Learn a command's full pipeline, then read its caught_errors.md ledger, find the patterns behind its failures, reverse-engineer their causes, and fold the lessons into that pipeline's first-try prompting, use cases, examples, craft, dismissal rules, instructions and QC.
argument-hint: "<command-name> [dry-run] [only CE-nnn,CE-nnn…]   e.g. analyze-then-pick"
disable-model-invocation: true
disallowed-tools:
  - Workflow
---

# /update-from-errors

Arguments: `$ARGUMENTS`

You are running **/update-from-errors**. When a pipeline command was first built, its context was
thin. It had few generation examples. It had an untested idea of what counts as an error and of
what a good prompt is. It had no record of what makes a great video and what should be dismissed.

Its `caught_errors.md` ledger now holds what really went wrong: what the QC agents caught, and what
the user saw after delivery. This command turns that record into better first attempts:
1. It learns how the whole pipeline works.
2. It reads the ledger and finds the patterns.
3. It works out why each pattern happened.
4. It checks whether the pipeline already covers each pattern. Where it does not, it rewrites the
   pipeline's prompting logic, use cases, examples, craft guidance, dismissal rules, instructions
   and QC. Where it does, it says "looks good", and suggests any optional improvement without
   applying it.

The aim is that the next run gets the video right the first time, and QC finds nothing.

## 0. Contract

1. **Order: the pipeline first (§1), then the caught errors (§2), then the work (§3–§7).**
   - Never open the ledger's entries before the pipeline model (§1.3) is written.
   - An error can only be traced to the step that let it through, and an edit can only land in the
     part that owns it, once the pipeline is understood.
2. **The argument is required.** The first word names the command whose ledger is read
   (`analyze-then-pick`).
   - Without it, list the ledgers that exist (the §1.1 ledger search over `~/.claude/**`, plus
     the matching `~/.claude/commands/<name>.md` for each), say "Run `/update-from-errors
     <command-name>`", and stop. Do not guess.
   - **`dry-run`**: do §1–§4 and show the change set, but write nothing.
   - **`only CE-012,CE-013`**: restrict the pass to those entries. The rest of the ledger is still
     read as context.
3. **Normal command, never a workflow.**
   - It uses ordinary tools in this conversation.
   - At most two read-only Explore agents are allowed, and only to sweep a large library.
   - It makes no paid calls and no generations; it learns from what is already on disk.
4. **Evidence decides the strength of what is written** (§3.3).
   - A **proven** lesson is backed by a verified prompt and a passing QC verdict, or by the user
     approving the fix. It is written as an instruction and an example.
   - A **repeated** lesson (two or more entries of one pattern) is written as a rule plus a QC
     check.
   - A **single, unproven** entry is written only as what to avoid, plus a QC check.
   - Never present a guessed fix as if it had worked.
5. **A user entry outranks an agent entry** on the same point, because the user saw what QC
   passed. Where the user's feedback contradicts a rule the pipeline holds, the rule changes.
6. **Rewrite, don't stack.**
   - Each lesson goes into the section that owns it, in that file's voice and format.
   - A rule that already exists and failed again is **replaced**. A promoted rule that recurred did
     not work, so repeating it louder is no fix.
   - Superseded wording is removed. No "lessons learned" dump is appended anywhere.
   - Text stays compact: one line per rule, one short good/bad pair per example.
7. **QC only gets stricter or more precise.** It is loosened only when an entry shows a false
   positive, meaning QC rejected what the user accepted.
8. **Never touch:**
   - the ledger's entries, except through its own tool. Never delete one: the ledger is the record;
   - `runs/` or any other run data;
   - locked user preferences (memory files, locked config such as a CapCut text preset);
   - the hard rules the command marks as fixed, unless an entry is the user explicitly overriding
     one.
9. **Preserve each file's line endings.**
   - Read and write bytes; if a file is CRLF, write CRLF.
   - Back up the build prompt before changing it, as `.bak-YYYYMMDD-HHMMSS` beside it.
10. **Honest reporting.** Every change names the entries behind it. Anything left unresolved is
    reported as open, together with the test that would settle it.

## 1. Learn the full pipeline (before opening the ledger)

### 1.1 Resolve

| name | value |
|---|---|
| `CMD` | `~/.claude/commands/<name>.md` |
| `LIB` | `~/.claude/<name>/` (else the folder that holds the ledger) |
| `LEDGER` | the pipeline's **error record set**: `LIB/caught_errors.md` when it exists, plus every file chained to it, found by the scan below. The scan runs on every pass, whether or not `caught_errors.md` exists |
| `LOG` | `LIB/learning-log.md`: one section per pass of this command (§6) |
| `BUILD` | the build prompt, if the user keeps one. Look for a memory-index entry naming "<name> build prompt", or `~/Documents/prompts/<name>.txt`; otherwise none |

**The error-record scan (every pass).** `caught_errors.md` is the entry point, not the whole
record. A pipeline's errors are usually a chain of files: the ledger, the files its entries
point to, the files that point back at it, and sibling files that hold errors under another
name. So the scan always runs, even when `caught_errors.md` exists, and the result is the
**record set** that §2 reads. Do it in this order, and keep a list of what was found and why:

1. **The primary ledger.** `LIB/caught_errors.md` if it exists. Otherwise, a file in `LIB` (then
   `~/.claude/<name>*/` and the paths `CMD` names) whose name says it holds errors:
   `caught_errors`, `caught-errors`, `errors_caught`, `generation_errors`,
   `generation-errors-caught`, `listed_errors`, `error_log`, `errors.md`, `failures`,
   `known_issues`, `mistakes`, `feedback_ledger`, `lessons`, and similar spellings with dashes,
   underscores or spaces, in any case; in Markdown, text, JSON or CSV. Also grep `CMD` for
   "ledger", "errors" or "feedback" next to a file path; the command usually names its own.
2. **Follow the chain out from the ledger**, without reading the entries' content yet: grep the
   ledger for paths and pointers, and record each target as part of the set:
   - run folders and the files an entry names (brief, plan, request, `result.json`, evidence
     frames and sheets, the run's own `caught-errors.md` or verdicts);
   - `promoted to` pointers (the reference sections that already hold a rule from an entry);
   - the learning log and any "see also" file;
   - the tool that writes the ledger (its format and its fields are read from the script).
3. **Follow the chain in.** Grep `LIB` and `CMD` for files that mention the ledger or its ids
   (`CE-012`): per-run `caught-errors.md` digests, QC verdicts that check entries by id, model
   guide failure tables that cite them. These are where the rules are applied, and §3 needs them
   to tell whether a rule was in force.
4. **Siblings by name.** The same name search as step 1, over the whole of `LIB` and the run
   folders: a second ledger (per model, per class, per month, one entry per file), a QC log, a
   retry log, a `failures.json`, a feedback file. A split ledger is read as one, in date order.
   A file that is a different thing is listed and, if it holds error records, included.
5. **Run-level records with no ledger entry.** Where `CMD` says errors are recorded at run level
   (QC verdicts, `result.json`, "regenerated because" fields, per-run reports), gather from the
   last 30 days or the last ten runs, whichever is more, every record that says a generation, an
   edit or a check went wrong **and has no ledger entry** (match on run and video). These are
   errors the ledger never received. Give each an id of its own (`R-<run>-<video>-<n>`) and
   include it. Offer, as an optional suggestion, to add them to the ledger properly.

Rules for the set:
- Every record is read with the same fields in mind: an id, the video, the run, the model, what
  was wrong, the cause, the fix, the rule, the status, and the evidence. Missing fields are noted
  as "not recorded", never invented.
- One error, several files (the ledger entry, the run digest, the QC verdict): one row, with all
  of its sources named. The ledger entry's wording wins; the others add evidence.
- The scan's result goes in the report: files included, files seen and skipped, and records
  gathered from run level.
- No ledger and no record anywhere: stop, say the pipeline has no error record to learn from,
  and name where one should go (`LIB/caught_errors.md`).

Stop and say so if `CMD` is missing, or if the record set has no entries. To check for entries,
look only for entry headings or records; do not read their content yet.

### 1.2 Read the whole pipeline

1. **`CMD`, in full:**
   - its contract and its modes;
   - every step from input to delivery;
   - its agents and their contracts;
   - its wrap-up and its "Never" list.
2. **`LIB`'s README and file tree.** Then read every reference file `CMD` points to: planning,
   analysis and selection, creative direction, prompting, integration, error definitions,
   guardrails, assembly, QC, and the agent contracts.
3. **The model guides of the models the ledger involves.** Find those models by grepping the
   entries' `model` fields (or whatever field the ledger's own format uses), without reading the
   entries. Also read the guide template, if one
   exists, to learn the guides' fixed sections.
4. **The toolkit's surface:** `--help` of each script, plus the subcommands that encode checks
   (for example size, QC and sync checks).
5. **The memory index**, for locked preferences and constraints that must not be edited away.
6. **`LOG`**, if it exists:
   - the passes already made;
   - which entries they consumed;
   - what they changed;
   - which hypotheses they left to test.

### 1.3 Write the pipeline model (in working notes, before §2)

- **The flow.** List the stages from input to delivered output. For each stage, note:
  - where its instructions live (file §);
  - what it produces;
  - which check guards it.
- **The target map.** Note which file and section owns each item in the table below. It places each
  error in §2 and each edit in §4.

| owner | what it holds |
|---|---|
| first-try prompting | the prompt structure, the translation into the model's language, the prompting stack |
| model guides | per-model phrasing, parameter gotchas, failure table, checklist, examples |
| use cases | when a reference, form, anchor, technique or operation is chosen (selection, ranking, integration choices) |
| dismissal | what is dismissed or never attempted, and why (ranking filters, guardrail audit, model limits) |
| craft | what makes a great video: hook, payoff, concept seeds, sharpness gate, house approach |
| examples | official prompt examples, worked examples, good/bad pairs, verdict examples |
| instructions | the plan and brief rules, the step lists in `CMD`, the agent contract |
| error definitions | what counts as an error: anomaly classes, must-not-survive lists, thresholds |
| QC | the pre-generation check, the post-generation QC, the QC stack, the verdict format, the agents' QC duties, measurable checks |
| toolkit | scripts whose checks or defaults encode a rule |

- **The rules in force.** For prompting, craft, dismissal, error definitions and QC, note each rule
  that already exists and where it lives. §3 needs this to tell a missing rule from one that exists
  and failed.

For `analyze-then-pick`, the map is known. Confirm each location exists before relying on it:
- **the flow:** `CMD` §2–§6 (A-steps for analysis and planning, X-steps per video, X9 QC, the §6
  wrap-up), plus `reference/production-agents.md`;
- **first-try prompting:**
  - `reference/generation-system.md` §7–§8;
  - `reference/anomaly-catalog.md` §3;
  - `models/<model>.md` §3–§4 (§4.0 holds the examples);
- **use cases and dismissal:**
  - `reference/analysis-protocol.md` (the cards, the ranking and its filters);
  - `reference/brand-guardrails.md`;
  - `generation-system.md` §4b (forms, anchors);
  - `reference/assets-and-substitution.md`;
- **craft:** `reference/creative-direction.md` (seeds, sharpness gate, copy test, hook and
  payoff), plus the house approach rules;
- **error definitions:** `anomaly-catalog.md` §2 (classes and thresholds), plus
  `generation-system.md` §9b;
- **QC:**
  - `generation-system.md` §8–§9;
  - `anomaly-catalog.md` §4 and §4.1 (verdict examples);
  - `reference/production-agents.md` §3;
  - `CMD` X4 and X9;
- **model failure modes:** `models/<model>.md` §5 (failure table), §7 (checklist) and §9 (open
  questions);
- **toolkit:** `scripts/atp.py` (`scale`, `qc`, `sync-check`, `caught-error`).

## 2. Then read the caught errors and check them against their evidence

1. **Read the whole record set from the scan (§1.1):** the ledger's header (fields, sources,
   statuses, tool), if it has one, then **all** of its entries, then every chained and sibling
   record, then the run-level records gathered without a ledger entry.
2. **Build a row for each entry in scope**, with these fields:
   - id, source, status;
   - mode, model, product;
   - class, cause;
   - what was wrong, and the rule;
   - the failed prompt, plus the verified prompt and the prompt change, if any;
   - params, errors, evidence;
   - the brief's intent.
3. **Place each row on the pipeline model (§1.3).** Note:
   - the stage where the error was made;
   - the stage that should have caught it;
   - the rule in force there, if any.

Then check each diagnosis against what is still on disk. Read selectively, only what settles a
question:
- **The brief and plan paths.** Did the plan already intend the right thing, so the prompt or the
  model lost it? Or was the plan itself wrong?
- **The request JSON.** What was actually sent (media roles, durations, flags), not what the entry
  says was sent.
- **The evidence path (QC frames or sheets).** Look at the named frame when the diagnosis is in
  doubt, or when two entries disagree.

Mark each row's diagnosis **confirmed**, **corrected** (say how) or **unverifiable** (files gone).
A missing file is not an error; note it and move on.

## 3. Find the patterns and reverse-engineer them

### 3.1 Cluster

Group the rows by what really failed, not by the wording of their titles. Entries cluster when
they share any of these:
- the class (the anomaly class, the text rule, the guardrail, the creative check);
- the product family;
- the model;
- the operation or the media roles;
- the cause;
- the placement or the technique.

One entry can sit in two clusters. Also note the **cross-cuts**: one model failing across several
classes, or one class failing across several models.

### 3.2 Reverse-engineer each cluster

Answer these, citing ids:

1. **What did the plan intend, what did the prompt say, and what came out?** Name the stage where
   intent and output parted: the reference choice, the plan, the translation, the parameters, the
   model, or QC.
2. **Which lever caused it?** One or more of these:
   - **wording:** an instruction missing, vague, buried or contradicted;
   - **structure:** the placement in the prompt, or a positive line without its exclusion;
   - **parameter or media role;**
   - **asset prep:** padding, framing, or a reference image that teaches the wrong scale;
   - **plan choice:** the anchor, the depth, the operation, or the reference itself;
   - **model limit:** no wording fixes it; only a different technique or a post step does;
   - **QC miss:** the check was absent, unmeasured or below threshold;
   - **use case or dismissal:** the reference or form should have been dismissed or chosen
     differently;
   - **craft:** the video worked technically but was bland, copied or missed its hook or payoff.
3. **Why did the rule in force not prevent it?** Was the rule missing? Present but ignored by this
   model? Present but unmeasured?
   - A cluster that recurs after a promotion or a `LOG` change means **that change failed**.
   - Say what it assumed that was false. For example: "a frame fraction in words controls size on
     Wan 3.0 Prime: false, ignored in CE-011, CE-014 and CE-015".
4. **What works?** In order of strength:
   - verified prompt changes and passing verdicts (the sentence-level diff is the strongest evidence
     in the ledger);
   - patterns that appear only in the passing attempts;
   - the model guide's official guidance.
5. **What should QC have measured, and at what threshold?** Either to catch it on the first output,
   or to reject it in the pre-generation check, before a credit was spent.

### 3.3 Grade each lesson

| grade | evidence | written as |
|---|---|---|
| **proven** | a verified prompt that passed QC, or a fix the user approved | an instruction + a good/bad example (the failed wording vs the verified wording) + a QC check |
| **repeated** | two or more entries with a consistent cause | a rule in the owning section + a measurable QC check + the failed wording as a bad example |
| **single** | one unverified entry | an avoid line + a QC check; at most a "to test" hypothesis in `LOG` and in the model guide's open questions |
| **model limit** | the same failure twice or more despite correct wording | a row in the model guide's failure table with the workaround technique (a different operation, start frame, post step or plan choice), plus a dismissal or use-case line saying when not to attempt it on this model |
| **false positive** | QC flagged what the user accepted | a more precise QC threshold or check |

A lesson learned from one model applies to that model's guide only. It moves into the
model-agnostic references only when two or more models show the same thing.

### 3.4 Coverage check: is anything actually missing?

Before writing a single change, hold each lesson against the rules in force (§1.3). A lesson is
**covered** when the pipeline already has all three of these, in the owning section:
- a first-try rule that prevents it, in the model's phrasing where it is model-specific;
- an error definition with a threshold that names it;
- a QC check that measures it, at the stage that can catch it.

Grade the coverage of each lesson:
- **covered**: all three exist and the entries behind the lesson date from before the rule was
  written (the rule has not had a run to prove itself yet). Nothing to change.
- **covered but unproven**: all three exist, but no run has tested them since. Nothing to change;
  name the test the next run should make.
- **gap**: one of the three is missing, vague or unmeasured, or the lesson recurred after the
  rule was written. This is what §4 is for.
- **optional**: the pipeline handles it, but an example, a sharper threshold or a clearer line
  would help. Suggest it; do not apply it unless the user asks.

**If there are no gaps, the pass ends here.** Say "Looks good": the pipeline already covers every
case the ledger describes. List what is covered but unproven, and the optional suggestions, if
any. Do not edit a file to show work, do not re-promote entries that are already promoted, and
do not touch the build prompt. Still write the learning-log section (§6), since "checked, nothing
missing" is also a result the next pass needs.

## 4. Build the change set

For every lesson, write one change row:

`file § section | change kind | the new text (or the replacement) | CE ids | grade`

The change kinds:
- **Prompting logic:** the first-try instruction in the owning section, written so the planner
  applies it before generating. It uses the model's own phrasing and its exclusion syntax.
- **Use case:** when to choose a reference, form, anchor, technique or operation.
- **Dismissal:** when to dismiss a reference, or not attempt something on a model, and what to do
  instead.
- **Craft:** what makes the video great or flat. This covers the hook, the payoff, the concept
  rules, the sharpness gate and the copy test.
- **Example:** a short good/bad pair.
  - The bad side is the failed wording, quoted from the entry.
  - The good side is the verified wording, if one exists. Otherwise there is no good side, only
    "avoid this".
  - It goes in the owning model guide's examples section (§4.0 in ATP guides) or in the
    reference's own examples, never in a new file.
- **Instruction:** a plan or brief rule, a step in `CMD`, or a line in the agent contract.
- **Error definition:** what now counts as an error: a new class, a widened class, or a
  threshold.
- **QC:** a measurable check at the right stage (pre-generation, first output, final). Give:
  - its threshold;
  - its tool, if one exists;
  - the verdict line it writes;
  - whether a failure means regenerate or only a note.

  Also add a line to the verdict examples.
- **Toolkit:** a default or a check in a script. Use this only when a tool enforces the rule better
  than text. Keep the change small, and test it.

Then review the set as a whole:
- No two rows contradict each other or an existing hard rule.
- Nothing duplicates a rule that already exists; merge or replace instead, and remove the
  superseded text.
- Every QC row has a threshold, and every prompting row is in the model's phrasing.
- Every change traces to entries, and no change rests only on an unverified guess.

**`dry-run`:** print the pipeline model's key findings, the patterns (§3), the coverage check
(§3.4) and the change set as a table, then stop.

## 5. Apply

1. **Edit each file in place.** Keep its section structure, voice, numbering and line endings. Any
   edit script must handle CRLF, check every anchor before writing anything, and write bytes.
2. **Update `CMD`** wherever a step, a check or a "Never" rule changes, and keep its numbered items
   consistent.
3. **Mark the entries in the ledger, through its tool only.**
   - For ATP: `"$PY" -X utf8 "$LIB/scripts/atp.py" caught-error set --id CE-nnn --status promoted
     --promoted-to "<file §, file §>"`.
   - **Proven** entry: promote it with its pointer.
   - **Repeated or single** entry: promote it with its pointer, and **keep it as the record**. Its
     fields stay untouched, and its fix is never marked verified.
   - **Unresolved model-limit** entry: it stays `open`, and its pointer names the failure-table row.
   - Ledgers without a tool: edit them in their own format, by the same rules.
4. **The build prompt.** If `BUILD` exists, back it up, then fold in the changes where it describes
   the owning parts, in its own prose style. It specifies the pipeline, so it changes when the
   pipeline does.
5. **Verify:**
   - read back every anchor you changed;
   - check the toolkit still runs (`atp.py --help`, plus each changed subcommand on a small input);
   - check `caught-error list --rules` still parses every entry;
   - check no file's line endings changed unintentionally (`git diff --stat`, plus a CRLF check).
6. **Commit** in `~/.claude` (a git repo with auto-commit hooks), as one commit:
   - subject: `<name>: update from caught errors CE-a..CE-b (<n> patterns)`;
   - body: the change list.

## 6. Learning log (`LIB/learning-log.md`)

Append one compact section per pass:

```
## <date> · CE-001..CE-015 · <n> patterns · commit <hash>
- **Patterns:** P1 <one line> (CE-005, CE-011, CE-014, CE-015; repeated; model limit on wan3_0_prime) …
- **Root causes:** P1 <the lever, and what the earlier rule wrongly assumed> …
- **Coverage:** P1 gap · P2 covered (anomaly-catalog §2.7) · P3 covered, unproven · P4 optional
- **Changes:** <file §>: <one line> (P1) …   (or "none: looks good")
- **Promoted:** CE-… → <pointer>; **left open:** CE-… (<why>)
- **Suggested, not applied:** <the optional lines> …
- **To test:** <hypothesis> → measure <what> on the next run of <model/class>; proven when <criterion>
```

A "looks good" pass writes the same section with "Changes: none" and no commit hash. The next
pass reads this file in §1.2. A pattern that recurs after a logged change means that change
failed: revise it, do not repeat it.

## 7. Report

Give a short table: pattern → entries → root cause → coverage → what changed (file §).

Then list:
- the entries promoted, and the ones left open with the reason;
- the hypotheses to test, and what the next run should measure;
- any diagnosis corrected in §2;
- the files changed, the build-prompt backup and the commit hash.

End with one line:
- in a dry-run, offer to apply;
- otherwise, offer to run the pipeline on a small batch that exercises the changed rules.

**When there were no gaps (§3.4),** the report is short: "Looks good. The pipeline already covers
every case in CE-a..CE-b." Then, only if there are any:
- **Suggested updates** (optional grade): each as `file §: one line`, with the entries behind
  it. Offer to apply them in one line; do nothing until the user says so.
- **Covered but unproven:** the rules that still need a run to prove them, and what that run
  should measure.
No files are changed, nothing is committed, and the learning log gets its "none" section.

## 8. Never

**Order and scope**
- Never run without the command-name argument, and never guess it.
- Never read the ledger's entries before the pipeline is read and modelled.
- Never generate, preflight or spend credits.
- Never use a Claude Code Workflow.
- Never change a file when the coverage check found no gap. "Looks good" is a complete result;
  a pass is not measured by how much it edits.
- Never apply an optional suggestion without the user's yes.

**The ledger and evidence**
- Never delete or rewrite a ledger entry's content. Set its status and pointer through its tool
  only.
- Never present an unverified fix as working, or write a "good" example that never passed QC.

**How lessons are written**
- Never re-promote a recurring rule unchanged. Find what it got wrong, and replace it.
- Never stack a new rule beside an old one it supersedes.
- Never append a lessons-learned dump instead of editing the owning section.
- Never generalise one model's failure to every model.
- Never loosen QC without a false-positive entry.

**Files**
- Never edit locked user preferences, run data, or a file's line endings.
- Never change a file you did not read first.
- Never skip the build-prompt backup and update, the learning log, or the commit.
