---
name: atg-pipeline
description: "/analyze-then-generate: Edit + Analyze (Recreate, Create = virality-backed blend, Viral-Browser = references as ideas, research, 3 winning products with blueprints and reference packs, generates nothing); scripts only gather, agents decide; library ~/.claude/analyze-then-generate, build prompt Documents/prompts/analyze-then-generate.txt"
metadata:
  node_type: memory
  type: project
  originSessionId: 550ea8f9-fa48-4983-be86-ce42635bab6a
  modified: 2026-10-18T12:37:26.805Z
---

`/analyze-then-generate` (created 2026-10-11, rebuilt into a router + 25 skills on 2026-10-18, see [[atg-skills-architecture]]) has Edit Mode and
Analyze Mode with three sub-modes: Recreate, Create and **Viral-Browser** (the third, added at the user's request: the references are a
source of ideas, the run asks the market and the price range and returns the next three products to sell). Library
`~/.claude/analyze-then-generate/`, own toolkit `scripts/atg.py`, playbook `reference/viral-browser/` (sectioned), config
`viral_browser` in `config.json` (former gate numbers are `viral_browser.rules_of_thumb`: guidance for the agent, read by no script),
build prompt `Documents/prompts/analyze-then-generate.txt` (CRLF prose, update after every change with a dated `.bak-*`, [[atp-build-prompt-sync]]).
The two pipelines are independent copies; do not mention one in the other's docs ([[no-cross-pipeline-mentions]]).

- **THE RULE (user, 2026-10-12, every mode): scripts gather, extract, record, tabulate and calculate; agents decide and record why**
  ([[scripts-gather-agents-decide]]). In atg.py nothing ranks, gates, caps, labels or refuses on content: `candidates` (ledger + side-by-side
  table), `niches` (the agents' vocabulary: add/map/merge/audit/list/propose), `evidence`, `spec` (facts side by side, `spec judge` records the
  agent's status/value/reason, `gaps`), `photo` (links only), `viral-stats`, `econ` (arithmetic per market), `audio-context`/`audio-profile`,
  `qc`, `sync-check`, `scale`, `conform --dry-run`, `finalize`, `restore-audio`, `ledger begin` (records, reports `conflicts`), `model-menu`
  (no quick picks), `inventory` (no name hints). **No niche, product or category name in any script or config** ([[no-hardcoded-names-in-scripts]]).
- **Viral-Browser flow** (skills `atg-vb-*`): asks market (US/EU/global), price range, selling model, Chrome yes/no (+ how the user sells;
  exclusions only from the user's message); viral cards (product layer apart from mechanism layer; one-line `Facts:` JSON, `category` = niche
  label reconciled into a run-level niche vocabulary; `voice_type`, `shots_seen`; `creator_group` assigned by the main session); mechanism map,
  essence, fit profile; 12-20 candidates from five sources; pool-balance and dominant-niche rules of thumb + bias log in
  `30-research/ranking.md`; fresh niche-audit agent; up to 3 research agents (origin-blind dossiers, evidence graded A-D with signal and
  independence; economics per market on a common cost basis written before the wave); fresh blind scoring agent (main session never scores);
  red team; the MAIN session applies the six gates by reading `candidates table` and records picks with `--pick-rank --by --reason`; one
  backfill wave; three picks + blueprints in `RUN/deliverables/`, each with a **reference pack** (sourced spec facts via `T spec`, **image URL
  links only, nothing downloaded**, [[atg-photo-links-only]]); optional continue-to-Create on the user's yes. Nothing is generated.
- **Create is a virality-backed blend (user, 2026-10-11/12):** understands the references (craft sheet, audience, trend, mechanism map,
  `viral-stats --no-niche`, blend matrix) AND the product (`30-assets/product-insights.md`, up to six truths PT#), seeds pass the blend test and
  the template-lock test, "Agent's choice (Recommended)" style option, virality rationale per video, `deliverables/blends.md`.
- **Audio context in every analysis mode (user, 2026-10-12):** `T audio-context --profile --second-pass` writes `20-analysis/audio-context.md`
  (transcripts + numbers, no labels); every card has `Audio context:`, `Said:`, `Words and sound together:`; `--check --cards` writes nothing.
- **No error ledger** (retired 2026-10-18, [[atp-caught-errors]] has the reasoning): a bad video or pick is diagnosed in its brief (picks:
  `deliverables/feedback.md`); Loupe holds the flag record and the QC samples ([[loupe-web-app]]); contract items 22 no ledger, 23 flags,
  24-26 Viral-Browser. `/update-from-errors` is obsolete ([[update-from-errors-command]]).

**Live test (2026-10-12):** Viral-Browser on `Documents\test` (15 downloads), run `ATG/runs/20261012-113001-test-hunt`: no candidate passed all six
gates, watch list only; it produced the common cost basis, the shipping-policy question, price and cost at one variant, one rater across
batches, `--opened` on A/B evidence, `pdf-text`, `photo find --match`. Open design question: gate G2 (a positive compliance row = route AND cost)
is hard to meet at standard depth. Regression suites: `analyze-then-generate/tests/run_all.py` (all suites pass).

**Why:** the user is building an owned-inventory store ([[user-kosovo-ecommerce-founder]]) and wants the next products found from what made videos
spread, without the references' dominant niche deciding the answer.
