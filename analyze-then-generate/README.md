# /analyze-then-generate — library

The `/analyze-then-generate` slash command lives at `~/.claude/commands/analyze-then-generate.md`. It is a
normal Claude Code command: `disable-model-invocation: true`, the `Workflow` tool is disallowed, and
it uses at most 2 analysis agents plus, in Analyze Mode's Recreate and Create, one production agent per
video (at most 5 at once). It is a fork of `/analyze-then-pick` (made 2026-10-11) with a third Analyze
sub-mode, **Viral-Browser**: the references become a source of ideas, nothing is generated, and the run
researches the market and returns the next three products to sell (`reference/viral-browser.md`; it uses up
to 3 research agents, one niche-audit agent, one blind scoring agent and a red-team agent, no production agents). Everything it loads at run time lives here.

```
analyze-then-generate/
├── caught_errors.md                the feedback ledger: one entry per video the user was not satisfied with (their words verbatim, the diagnosis, class, cause, fix, rule, status); read at every run start, applied in plans, prompts and QC, promoted into the references when general (`atg.py caught-error add | list | set`); `/update-from-errors analyze-then-generate` generalises its patterns into the references in one pass (what to achieve, what to avoid, the miss and its cause, the prompt correction, what worked)
├── learning-log.md                 one section per `/update-from-errors` pass: patterns, root causes, changes, promoted and open entries, hypotheses to test
├── config.json                     paths (python, runs), fixed output (9:16, 720p), analysis defaults, Edit Mode cost gate, CapCut store + template
├── models/
│   ├── index.json                  model id → guide, capabilities, 9:16/720p parameter mapping, continuation (max per generation + how clips join); the only file read to build the menu
│   ├── _TEMPLATE.md                structure every model guide follows
│   ├── _generic-fallback.md        used for a live model that has no guide yet
│   └── <guide>.md                  one researched guide per model (family); only the selected one is loaded
├── higgsfield/
│   ├── higgsfield-mcp.md           MCP operations: tools, uploads, roles, Elements, jobs, costs, errors, 9:16/720p
│   ├── catalog-snapshot-<date>.json  models_explore snapshot used when the guides were written
│   └── first-party/                verbatim Higgsfield recipes (ad-multiplier edit contract, media pipeline, Genjutsu)
├── reference/
│   ├── analysis-protocol.md        Analyze Mode: reading 5 fps storyboards + timelines, cards, lenses, families, directions, delegation; the user's examples → house approach (§9)
│   ├── generation-system.md        dependency chain, work-backward plan, state ledger, multi-generation videos (§3b), reference inserts (§3c), integration analysis, swap / contents / natural placement (§4b), anti-slop gate, physics (§5b), source fidelity and audio-locked timing (§5c), counts / openings / permanence (§5d), model translation, pre/post QC, brief
│   ├── anomaly-catalog.md          logical and physical anomaly classes (counts, openings and use, preparation, persistent states, object permanence, liquids, scale with the size reckoning and standard-size table, body mechanics, labels, hand-offs, environment, timing, stylised rendering, solidity and collision, blend with the eleven-sign paste test): the affordance sheet per product, ledger entries, prompt lines, QC checkpoints and verdicts
│   ├── creative-direction.md       the creative team the pipeline plays (growth creative, mass-cognition engineer, trend analyst, creative director, performance editor): goal model, audience model, trend read, the craft sheet and the copy test (Create takes a reference's craft, never its subject), scored concept seeds, the sharpness gate, hook/payoff craft, creative QC notes
│   ├── brand-guardrails.md         the client's rules from the assets folder (no gore, count limits, no competitor brands, no ambassador likeness, claims, disclaimers): extraction, rule kinds, the per-reference guardrail audit (core → dismiss; peripheral → pick and edit: count reduced, competitor marks removed never blurred, faces swapped, captions rewritten), Create invariants, Edit Mode hits, QC
│   ├── text-and-format.md          mode-dependent text policy (Analyze: clean plate + CapCut text layers), text removal, fixed 9:16 / 720p rules
│   ├── capcut-assembly.md          Analyze Mode's editable master: one CapCut project per video (DD_Mon_YYYY_vNN) with the inserts and text layers (house text style: System, size 10, the user's locked preset); save, repair, preview
│   ├── production-agents.md        Analyze Mode (Recreate / Create): one background agent per video (max 5 at once), its prompt, contract and result.json
│   ├── viral-browser.md            Analyze Mode, Viral-Browser: the team (growth strategist, direct-response seller, mass-cognition engineer, trend analyst, researcher, compliance screener, statistician, red team), the brief (market, price range, selling model, exclusions), the viral card (product layer apart from mechanism layer), the synthesis (mechanism map, essence, fit profile, audience and mentality, trend read, niche concentration), the niche-bias controls, candidate generation, the research lanes and evidence grades, the rubric, the six gates and the selection of three picks, the viral blueprint, the deliverables, report QC, feedback and the continuation to Create, the pitfalls, the agent prompts
│   └── assets-and-substitution.md  user-supplied assets only (analyze: dropped once; edit: per operation), contents samples, understanding + registry, substitution map, reference strategy per model
├── pipeline/preprocessing.md       the recorded local pipeline (FFmpeg-first) and sampling policy (~5 fps adaptive)
├── scripts/atg.py                  deterministic local toolkit (Viral-Browser: viral-stats = measured corpus profile + niche concentration; niches = the run's niche vocabulary, which the AGENTS build from the data (add, map, merge, distinct, audit; no niche or product name is built into any script, and a split niche is made visible by the audit, the look-alike note and the shared-word flag); candidates = candidate ledger with scoring, gates, independent-evidence cap and niche cap; evidence = research evidence ledger; econ = unit economics (per market: the lowest contribution counts); new-run --submode, inventory / prep-all --as/--set baseline; the rest: inventory, prep, frames, last-frame, strip-inserts, audio-profile, fetch-audio, conform, concat seams, qc with 30 fps --dense checkpoint sheets, scale (size reckoning: expected vs observed product size), caught-error (the feedback ledger), sync-check, locked ledger/state, CapCut name/prep/repair, transfers)
└── runs/<stamp>-<slug>/            one folder per run (state.json makes runs resumable: /analyze-then-generate resume <run-dir>); Viral-Browser runs add 30-research/ (candidates.json, evidence.json, dossiers, red team, ranking, bias log) and deliverables/ (report, three product files, evidence, Create hand-off)
```

## How a run uses the documentation
1. Right after the mode (Analyze / Edit; not in Viral-Browser, which generates nothing and asks for no model), the command prints the model menu with
   `atg.py model-menu`. The menu lists **every** available model: `models/index.json` merged with the
   live `models_explore` catalog. Pinned models come first (`menu.pinned`: Seedance 2.5, Wan 3.0
   Prime), then `menu.order`. Change the pins or the order there; the command needs no change.
2. The picked model is **locked for the whole run**. At the planning step the command reads **only**
   that model's `guide` plus `higgsfield/higgsfield-mcp.md`.
3. The guide's **§4.0 official examples** become a per-video *pattern card*. Prompts are written in
   the model's proven structure, and parameters come from the guide's §2 recipes plus
   `output_9x16_720p` in the index.

## Viral-Browser (the third Analyze sub-mode)
1. `/analyze-then-generate viral-browser <references-folder> [baseline <folder>] [market us|eu|global] [price <min>-<max> <currency>] [depth quick|standard|deep]`, or pick Analyze Mode → Viral-Browser.
2. It asks the **market** and the **price range** (and the selling model and whether it may use your Chrome for live pages), reads the references only as ideas, and generates nothing: no model, no credits, no CapCut, no assets.
3. Per reference it writes a viral card (hook, style, approach, subject, how the product is used, engagement, audience and its mentality, length, commerce signals, drivers of spread, the product-agnostic mechanism), then a mechanism map, the essence and the fit profile.
4. It builds a pool of specific candidate products across the whole market (the references' niche is one source of five), has a fresh agent audit the niche vocabulary, researches the shortlist in parallel (demand, commercial proof, competition, economics, compliance, logistics, customer voice, content fit, timing), has a fresh blind agent score the candidates origin-blind on a rubric, passes six gates, attacks the would-be picks (plus the next two) with a red team, runs one backfill wave when fewer than three pass, and delivers **three picks** with a blueprint each (`deliverables/`).
5. The references' product niche cannot decide the answer: an agent-built and audited niche vocabulary, pool balance, the independent-evidence cap (sourced economics inputs included), the two-per-niche cap, defence notes and the ablation tests; every merge, waiver, audit and override is printed in `ranking.md` under "Decisions on record". A data-backed product from that niche can still win.
6. At the end it can continue to Create for a pick, on your yes, once you supply that product's assets.
7. The same mining runs inside Create (`reference/viral-browser.md` §14): the references are mined for why they spread, and the videos are virality-backed blends of a mined mechanism with a truth of your own product (a blend matrix, a virality rationale per video, `deliverables/blends.md`).

## Adding a model
1. Confirm it exists: `models_explore {action:"get", model_id:"<id>"}`.
2. Copy `models/_TEMPLATE.md` to `models/<guide-slug>.md` and fill it from **official** sources
   first: provider docs, API reference, prompt guide, model card, paper, first-party examples. Tag
   every claim [OFFICIAL] / [HF] / [SECONDARY] / [INFERRED]. Quote 3–8 official example prompts in
   §4.0 with the patterns they teach. Fill §2.6 (9:16 / 720p mapping) and §3.11 (visible text).
3. Add an entry under `models` in `models/index.json` (copy an existing entry; the fields are
   explained in its `_schema` block), and add its id to `menu.order` where it should appear in the
   menu. Ids that are missing from the order are listed at the end.
4. Nothing in the command changes. A live model without an index entry still works through
   `_generic-fallback.md`, with a warning.

## Updating a model
- Run `models_explore list` and compare it with `higgsfield/catalog-snapshot-*.json`. On drift,
  update the guide's §2 tables and the index entry, bump `guide_version` and `last_verified`, and
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
