# /analyze-then-generate — library

The `/analyze-then-generate` slash command lives at `~/.claude/commands/analyze-then-generate.md`. It is a normal Claude Code command:
`disable-model-invocation: true`, the `Workflow` tool is disallowed, and it uses at most 2 analysis agents plus, in Analyze Mode's Recreate and Create,
one production agent per video (at most 5 at once). It has three Analyze sub-modes: **Recreate**, **Create** and **Viral-Browser**. In Viral-Browser the references become a source of ideas,
nothing is generated, and the run researches the market and returns the next three products to sell (`reference/viral-browser/`; up to 3 research agents, one niche-audit agent, one blind scoring agent,
a red-team agent and up to 3 reference-pack agents, no production agents). Create is virality-backed: the references are mined like Viral-Browser's, and every video blends a mined mechanism with a truth of
the client's own product. Everything it loads at run time lives here or in the skills below.

## How it is organised: a router, 25 phase skills, section files

The context of a run is its scarcest resource, so nothing is loaded before its step:

- **The command is a router** (about 20 KB): arguments, resume, the loading rules, one line per contract item (1–26), the phase map, the labels table and the global Never rules.
- **Phase skills** `~/.claude/skills/atg-*/SKILL.md` (25, `user-invocable: false`, descriptions marked internal) hold the steps, the contract items and the Never rules of one phase
  each, plus a "Read now" list of the exact section files the phase needs and a hand-off that names the next skill. The chains:
  - Recreate / Create: `atg-start` → `atg-analyze-prepare` → `atg-analyze-study` → `atg-create-plan` | `atg-recreate-plan` → `atg-asset-plan` → `atg-analyze-produce` → `atg-wrapup`;
  - Viral-Browser: `atg-start` → `atg-vb-cards` (inputs, brief, run, V1–V2) → `atg-vb-synthesis` (V3–V4b) → `atg-vb-research` (V5) → `atg-vb-select` (V6) → `atg-vb-deliver` (V7) → `atg-vb-wrapup` (V8–V9; continue to Create only on the user's yes);
  - Edit: `atg-start` → `atg-edit` → `atg-wrapup`;
  - the per-video loop (Edit, Recreate, Create): `atg-plan-video` → `atg-write-request` → `atg-inputs` → `atg-precheck` → `atg-submit` → `atg-postprocess` → `atg-qc` → `atg-record`;
  - `atg-feedback` (a video or a pick reported as wrong) and `atg-model-guide` are called when needed. `state.json → next_skill` makes every phase boundary resumable.
- **Section files.** Every long document (the references, the Higgsfield guide, every model guide) is an index file plus a folder of section files; the section numbers (`§4b.1c`,
  `§2.14`, `viral-browser §7.4`, `guide §3.14`) are unchanged. A skill reads the sections it names, never a whole document.
- **Production agents** get a contract that invokes the per-video skills (`atg-inputs`, `atg-submit`, `atg-postprocess`, `atg-qc`, `atg-record`); they never read the command file.
  Viral-Browser's agents are briefed by the prompts of `reference/viral-browser/` §13.

```
analyze-then-generate/
├── learning-log.md                 one section per change of substance (never read by a run)
├── config.json                     paths (python, runs), fixed output (9:16, 720p), analysis defaults, Edit Mode cost gate, CapCut store + template, the Viral-Browser rules of thumb (guidance for the agents; no script reads them)
├── (flag record)                   lives in Loupe (`~/.claude/loupe`, `http://127.0.0.1:8787`), not in this folder: written only by `atg.py caught-flag`, never read by a run
├── models/                         index.json (model id → guide, capabilities, 9:16/720p mapping, continuation; 40 KB: never Read whole, `atg.py model-menu` / `model-entry --id`), _TEMPLATE.md, _generic-fallback.md, <guide>.md (index) + <guide>/NNN_<id>_<slug>.md (sections)
├── higgsfield/                     higgsfield-mcp.md (index) + higgsfield-mcp/ (tools, uploads, roles, Elements, jobs, costs, errors, 9:16/720p), catalog-snapshot-<date>.json, first-party/ (verbatim Higgsfield recipes)
├── reference/                      each <name>.md is an index; the sections are in <name>/
│   ├── analysis-protocol           Analyze Mode: reading 5 fps storyboards + timelines, cards (with the audio context), lenses, families, directions, delegation; the user's examples → house approach (§9)
│   ├── generation-system           dependency chain, work-backward plan, state ledger, multi-generation videos (§3b), reference inserts (§3c), integration analysis, swap / contents / natural placement (§4b, spot feasibility §4b.1c, size-and-place guide §4b.6), anti-slop gate, physics (§5b), source fidelity and audio-locked timing (§5c), counts / openings / permanence (§5d), model translation, pre/post QC, brief
│   ├── anomaly-catalog             logical and physical anomaly classes (counts, openings and use, preparation, persistent states, object permanence, liquids, scale with the size reckoning, label legibility, identity reference hygiene, body mechanics, hand-offs, environment, timing, stylised rendering, solidity and collision, blend with the paste test): the affordance sheet per product, ledger entries, prompt lines, QC checkpoints and verdicts
│   ├── creative-direction          the creative team the pipeline plays: goal model, audience model, trend read, the craft sheet and the copy test (§5.0), blend not mimic (§5.0b), virality-backed blends (§5.0c), scored concept seeds, the sharpness gate, hook/payoff craft, creative QC notes
│   ├── brand-guardrails            the client's rules from the assets folder: extraction, rule kinds, the per-reference guardrail audit (core → dismiss; peripheral → pick and edit), Create invariants, Edit Mode hits, QC
│   ├── text-and-format             mode-dependent text policy (Analyze: clean plate + CapCut text layers), text removal, fixed 9:16 / 720p rules
│   ├── capcut-assembly             Analyze Mode's editable master: one CapCut project per video (DD_Mon_YYYY_vNN) with the inserts and text layers (house text style: System, size 10, the user's locked preset); save, repair, preview
│   ├── production-agents           Analyze Mode (Recreate / Create): one background agent per video (max 5 at once), its prompt (which invokes the per-video skills), contract and result.json
│   ├── assets-and-substitution     user-supplied assets only (analyze: dropped once; edit: per operation), contents samples, understanding + registry + product insight sheet, substitution map, reference strategy per model
│   └── viral-browser               Viral-Browser: the team (§1), the brief (§2), the viral card (§3), the synthesis (§4), niche-bias control (§5), candidates (§6), the research lanes and rules of evidence (§7), the rubric, gates and selection (§8), the blueprint and the reference pack (§9), deliverables and report QC (§10), wrap-up and continuation to Create (§11), traps (§12), the agent prompts (§13), and the same mining in Create (§14)
├── pipeline/preprocessing.md       the recorded local pipeline (FFmpeg-first) and sampling policy (~5 fps adaptive)
├── scripts/atg.py                  deterministic local toolkit (see below)
├── scripts/docs_tool.py            the section tool: `split` / `join` / `index` for the documents, `check` (indexes, section files, skills, paths, § citations) and `budget` (what each skill and the command load)
├── tests/                          regression suites (`python tests/run_all.py`: seven suites, about 330 checks): the toolkit on a slim synthetic run (the rule that a script never decides is tested, not only written) and the structure of the library (`t14_library`: indexes, skills, hand-offs and `T` commands agree)
└── runs/<stamp>-<slug>/            one folder per run (state.json makes runs resumable: /analyze-then-generate resume <run-dir>; `next_skill` names the phase to continue); Viral-Browser runs add 30-research/ (candidates.json, evidence.json, dossiers, red team, ranking, bias log) and deliverables/ (report, three product files, evidence, reference packs, Create hand-off)

~/.claude/skills/atg-*/SKILL.md     the 25 phase skills (see above)
~/.claude/commands/analyze-then-generate.md   the router
```

## The toolkit (`scripts/atg.py`) and its rule
Commands: **media and runs** — new-run (`--submode viral-browser`), state, inventory (`--as references | sources | assets | examples | baseline`), prep-assets, prep-video / prep-all (probe, cuts, 5 fps adaptive frames, storyboards, audio, transcript, OCR text with its numbers, per-second timeline), frames, prep-image, doc-text, split-audio, strip-inserts, trim, concat, last-frame, clean, captions, conform (reports the share of the picture a crop loses). **Sound** — audio-profile (the sound design as numbers), audio-context (every reference's transcript and sound numbers in one digest that every analysis agent reads, checked before the cards; Recreate: context only), fetch-audio, restore-audio (reports the facts of the result). **Measurements, no verdict** — qc (storyboard and measurements beside the expected values and the planned text, with 30 fps `--dense` checkpoint sheets), sync-check (offsets per window, drift, duration difference, side-by-side sheet), scale (size reckoning as arithmetic). **Production support** — model-menu (every available model, pinned first; it picks nothing), model-entry (one index entry), ledger (every paid generation; `begin` records and reports conflicts, the agent decides), hf-put, hf-get, finalize, open, capcut-name / capcut-prep / capcut-repair / capcut-text-style. **Loupe** — caught-flag (add | set | list | reconcile | open), loupe (ensure | status | open), qc-consult, qc-brief, plan-hints. **Viral-Browser** — viral-stats (the measured profile of the references and tables of what the cards' Facts lines say; Create uses `--no-niche`), niches (the niche vocabulary, a record of the agents' decisions: add | map | merge | audit | list | propose; no niche or product name is built into any script and nothing compares names), candidates (add | list | show | set | rate | summary | table: records the agents' decisions with who, when and why and sets the recorded values side by side), evidence (add | copy | retract | list), spec (add | list | table | judge | gaps | render | reject), photo (find | add | set | list | check: photo LINKS only, nothing is downloaded), pdf-text, econ (unit economics per market, arithmetic only), landed (landed cost, arithmetic only). Locked ledger and state files.

**The rule (the user, 2026-10-12).** The scripts gather, extract, record, tabulate and calculate; they never evaluate or decide, in every mode. No command hands out a verdict, status, flag or label derived from content,
applies a threshold that refuses, caps or changes an answer, ranks, picks a winner or breaks a tie, compares texts for sameness or counts words to decide anything. A command refuses only a bad argument, a missing file or tool,
a damaged ledger, an unsafe web address or a failed ffmpeg run, and it keeps the user's own locks (CapCut closed while a project is written, the locked house text preset). The AI agent that runs the pipeline reads the numbers
and tables, decides from the mode's specification, and records the decision with the reason (`--by`, `--reason`, the ranking and bias log, the QC verdict); independent checks stay with fresh agents (niche audit, blind
scoring, red team, reference packs), never with script gates. The numbers that used to be enforced (the 0.10 s sync tolerance, the 15 / 25 % size bands, the 12 % crop loss, pool shares, rating floors, evidence caps …)
are rules of thumb in these documents (for Viral-Browser also in `config.json → viral_browser.rules_of_thumb`): the agent applies them with judgement, may depart from them when the evidence says so, and writes down what
it applied or set aside and why.

## Case labels (`CE-nnn`)
`CE-nnn` in the references, the model guides and the skills are case labels. Each marks a lesson learned from a video that went wrong (a user report or an agent's regenerate reason, 2026-10-03 to 2026-10-13); the
lesson is written out where the label stands, as a kind (what to achieve, what to avoid) with its miss, cause, corrected wording and what worked, so a label is never looked up. The lessons of the first live
Viral-Browser research wave (cost basis, price and cost at one variant, stored scenario prices, derived figures in evidence rows) live in `reference/viral-browser/` §7.0, §7.3, §7.4 and §7.5 without labels. There is no error ledger: `caught_errors.md` and `atg.py caught-error` were retired on 2026-10-18 so that a run reads rules, not a growing pile of
past errors. The last version of that file is in git history (`git log --follow -- analyze-then-generate/caught_errors.md`). A new lesson goes, generalised, straight into the section that owns it.

## The flag record and the QC samples (Loupe)
Loupe is the pipeline's web app (`~/.claude/loupe`, run by `python loupe.py serve`, or started by `atg.py loupe ensure` when a command needs it; localhost only, admin passphrase for the person, API keys for agents).
Its run browser lists the runs of every pipeline library under `~/.claude`. It holds two things:
- **The flag record:** every prompt and video Higgsfield flagged, refused, withheld or rerouted. `atg.py caught-flag add` gathers the video, the request, every input with its file, thumbnail and file facts (sha1, size,
  dimensions, printed words), whether the same file went through earlier runs, and the raw answer the Higgsfield hook saved, and takes the agent's trigger, tags, asset, prompt words and video part. Loupe searches with
  `field:value` operators, groups by trigger, asset, video, kind, run, model, cause, status or month, and shows the evidence next to each flag. No step of a run and no agent reads it; what a flag teaches is written into
  the references as a rule when the user asks for it.
- **Generation misses (samples):** the admin picks a run and a video in Loupe, marks the second of the miss, and optionally the right version; Loupe saves one image per sample. Only the QC phase reads them:
  `atg.py qc-consult` asks the QC keeper (one separate read-only Claude session that holds the whole sample library and never sees a run) which samples apply to the video under QC; `qc-brief` returns the matching
  samples with no model call; `atg.py plan-hints` asks, once per video at its first request, for a few text-only hints (usually none). Viral-Browser runs have no QC and no requests, so they use none of this.

Three hooks in `~/.claude/settings.json` support both pipelines without adding to any agent's context: `hooks/atp_flag_watch.py` (PostToolUse of the Higgsfield generation tools: saves a flag-like answer to Loupe as a
capture and reminds the agent to record the flag first, naming the script of the run in progress), `hooks/atp_resume_note.py` (SessionStart after a compaction or resume: names the run in progress, whichever library it
belongs to, and its `next_skill`) and `hooks/atp_read_guard.py` (PreToolUse of Read: refuses a whole-file read of the toolkit scripts, `models/index.json`, the catalog snapshots and the backups; a read with an offset/limit passes).
Build prompt for the app: `Documents/prompts/loupe.txt`; build prompt for this library: `Documents/prompts/analyze-then-generate.txt`.

## Viral-Browser (the third Analyze sub-mode)
1. `/analyze-then-generate viral-browser <references-folder> [baseline <folder>] [market us|eu|global] [price <min>-<max> <currency>] [depth quick|standard|deep]`, or pick Analyze Mode → Viral-Browser.
2. It asks the **market** and the **price range** (and the selling model, how the user sells, and whether it may use their Chrome for live pages), reads the references only as ideas, and generates nothing: no model, no credits, no CapCut, no assets.
3. Per reference it writes a viral card (hook, style, approach, subject, how the product is used, engagement, audience and its mentality, length, commerce signals, drivers of spread, the product-agnostic mechanism, the audio context), then a mechanism map, the essence and the fit profile.
4. It builds a long list of specific candidate products across the whole market (the references' niche is one source of five), has a fresh agent audit the niche vocabulary, researches the shortlist in parallel (demand, commercial proof, competition, economics, compliance, logistics, customer voice, content fit, timing), has a fresh blind agent rate the candidates origin-blind on a rubric, applies six selection gates of thumb itself by reading the side-by-side candidate table (no script gates or ranks anything), attacks the would-be picks (plus the next two) with a red team, runs one backfill wave when fewer than three clear the gates, and delivers **three picks** with a blueprint each and a **reference pack** each (a sourced specification and links to photos from several angles, nothing downloaded; `deliverables/reference-C##-<name>/`).
5. The references' product niche cannot decide the answer, and no script does either: an agent-built and audited niche vocabulary, a balanced long list, the evidence rule of thumb the blind scoring agent applies, at most two picks per niche as a rule of thumb, written defences and the what-if tests; every merge, waiver, audit and override is written with its reason in `ranking.md` (the bias log). A data-backed product from that niche can still win.
6. At the end it can continue to Create for a pick, on the user's yes, once they supply that product's assets.
7. The same mining runs inside Create (`reference/viral-browser/` §14): the references are mined for why they spread, and the videos are virality-backed blends of a mined mechanism with a truth of the client's own product (a blend matrix, a virality rationale per video, `deliverables/blends.md`).

## How a run uses the documentation
1. The command invokes `atg-start`: it prints the model menu with `atg.py model-menu` (not in Viral-Browser, which hands off to `atg-vb-cards` first). The menu lists **every** available model: `models/index.json` merged with the
   live `models_explore` catalog. Pinned models come first (`menu.pinned`: Seedance 2.5, Wan 3.0 Prime), then `menu.order`. Change the pins or the order there; the command needs no change.
2. The picked model is **locked for the whole run**. `atg.py model-entry --id <model>` prints its index entry and its guide folder; each per-video skill then reads **only the
   sections of that guide it names** (`atg-model-guide` has the table).
3. The guide's **§4.0 official examples** become a per-video *pattern card*. Prompts are written in the model's proven structure, and parameters come from the guide's §2 recipes plus
   `output_9x16_720p` in the index.
4. Each phase hands off to the next skill and records `next_skill` in `state.json`, so a run can be compacted, resumed or moved to a new session at any phase boundary.

## Editing the pipeline
- **A step or a rule of a phase:** edit that phase's `~/.claude/skills/atg-*/SKILL.md` (the router's labels table says which skill owns which step; a rule that two phases act on is written in both skills).
- **A reference or a guide section:** edit its section file; after adding, renaming or removing one run `python scripts/docs_tool.py index <doc>.md`. Never edit between the index markers by hand.
- After any edit: `python scripts/docs_tool.py check` (it must report 0 errors) and, for a pipeline change, update the build prompt `Documents/prompts/analyze-then-generate.txt`.
- `python scripts/docs_tool.py budget` shows what each skill weighs; `join <doc>.md` prints a whole document (for maintenance, never in a run).

## Adding a model
1. Confirm it exists: `models_explore {action:"get", model_id:"<id>"}`.
2. Copy `models/_TEMPLATE.md` to `models/<guide-slug>.md` and fill it from **official** sources
   first: provider docs, API reference, prompt guide, model card, paper, first-party examples. Tag
   every claim [OFFICIAL] / [HF] / [SECONDARY] / [INFERRED]. Quote 3–8 official example prompts in
   §4.0 with the patterns they teach. Fill §2.6 (9:16 / 720p mapping) and §3.11 (visible text).
3. Run `python scripts/docs_tool.py split models/<guide-slug>.md` (lossless: it verifies the rejoin) so the guide becomes an index plus section files.
4. Add an entry under `models` in `models/index.json` (copy an existing entry; the fields are
   explained in its `_schema` block), and add its id to `menu.order` where it should appear in the
   menu. Ids that are missing from the order are listed at the end.
5. Nothing in the command or the skills changes. A live model without an index entry still works through
   `_generic-fallback.md`, with a warning.

## Updating a model
- Run `models_explore list` and compare it with `higgsfield/catalog-snapshot-*.json`. On drift,
  update the guide's §2 section files and the index entry, bump `guide_version` and `last_verified` (in the guide index's front matter), and
  save a new snapshot.
- A model that disappears from the live catalog stays in the index with `"status": "retired"` until
  it is removed; the command hides unavailable models.

## Tooling requirements (this machine)
- FFmpeg / ffprobe 9.x (winget Gyan.FFmpeg).
- Python 3.12 with Pillow, NumPy and requests; faster-whisper (models cached: small, base, tiny) and
  rapidocr-onnxruntime are optional but used.
- The Higgsfield MCP server `higgsfield` (OAuth via `/mcp`).
- CapCut desktop (9.x), the `capcut` MCP server (installed with analyze-stack:
  `~/.claude/analyze-stack/tools/mcp/capcut-mcp`, template draft `_analyze-stack-template`), and
  capcut-cli 0.25 (`capcut` on PATH via npm) for registration, timeline sync, lint and proxy
  previews. CapCut must be closed while a project is written.

Details: `pipeline/preprocessing.md`.
