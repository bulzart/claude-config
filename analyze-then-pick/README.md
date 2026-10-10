# /analyze-then-pick — library

The `/analyze-then-pick` slash command lives at `~/.claude/commands/analyze-then-pick.md`. It is a
normal Claude Code command: `disable-model-invocation: true`, the `Workflow` tool is disallowed, and
it uses at most 2 analysis agents plus, in Analyze Mode, one production agent per video (at most
5 at once). Everything it loads at run time lives here.

```
analyze-then-pick/
├── caught_errors.md                the feedback ledger: one entry per video the user was not satisfied with (their words verbatim, the diagnosis, class, cause, fix, rule, status); read at every run start, applied in plans, prompts and QC, promoted into the references when general (`atp.py caught-error add | list | set`); `/update-from-errors analyze-then-pick` folds its patterns into the references in one pass
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
│   └── assets-and-substitution.md  user-supplied assets only (analyze: dropped once; edit: per operation), contents samples, understanding + registry, substitution map, reference strategy per model
├── pipeline/preprocessing.md       the recorded local pipeline (FFmpeg-first) and sampling policy (~5 fps adaptive)
├── scripts/atp.py                  deterministic local toolkit (inventory, prep, frames, last-frame, strip-inserts, audio-profile, fetch-audio, conform, concat seams, qc with 30 fps --dense checkpoint sheets, scale (size reckoning: expected vs observed product size), caught-error (the feedback ledger), sync-check, locked ledger/state, CapCut name/prep/repair, transfers)
└── runs/<stamp>-<slug>/            one folder per run (state.json makes runs resumable: /analyze-then-pick resume <run-dir>)
```

## How a run uses the documentation
1. Right after the mode (Analyze / Edit), the command prints the model menu with
   `atp.py model-menu`. The menu lists **every** available model: `models/index.json` merged with the
   live `models_explore` catalog. Pinned models come first (`menu.pinned`: Seedance 2.5, Wan 3.0
   Prime), then `menu.order`. Change the pins or the order there; the command needs no change.
2. The picked model is **locked for the whole run**. At the planning step the command reads **only**
   that model's `guide` plus `higgsfield/higgsfield-mcp.md`.
3. The guide's **§4.0 official examples** become a per-video *pattern card*. Prompts are written in
   the model's proven structure, and parameters come from the guide's §2 recipes plus
   `output_9x16_720p` in the index.

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
