---
name: atg-pipeline
description: "/analyze-then-generate (2026-10-11): fork of /analyze-then-pick plus a third Analyze sub-mode, Viral-Browser (references as ideas, research, 3 winning products with blueprints, asks market + price range, generates nothing); library ~/.claude/analyze-then-generate, build prompt Documents/prompts/analyze-then-generate.txt"
metadata:
  node_type: memory
  type: project
  originSessionId: f2e65d75-f760-412f-aaeb-1f90311ace7e
  modified: 2026-10-10T23:03:08.136Z
---

On 2026-10-11 the user asked for a new pipeline `/analyze-then-generate` with a new Analyze sub-mode `viral-browser` (next to Recreate and Create) and a build prompt file like `analyze-then-pick.txt`. They named `analyze-stack-build-prompt.txt` as the base, but that file is the old `/analyze-stack` spec (Modes 1-3); the Recreate/Create structure they described is `analyze-then-pick.txt`, so the fork was made from the ATP library (snapshot 2026-10-10 14:04) and from that build prompt. `/analyze-then-pick` itself was not changed.

**What exists**
- Command `~/.claude/commands/analyze-then-generate.md` (contract items 23-25, steps V1-V9 after A10), library `~/.claude/analyze-then-generate/` (own toolkit `scripts/atg.py`, the ledger copied with CE-001..CE-029, a fresh `learning-log.md`, all references and model guides), the playbook `reference/viral-browser.md`, config `viral_browser` in `config.json`, build prompt `Documents/prompts/analyze-then-generate.txt` (generated from `analyze-then-pick.txt` plus a Viral-Browser block; same CRLF prose style).
- Viral-Browser: asks market (US/EU/global) and price range (plus selling model, Chrome yes/no, exclusions from the user's message only); per-reference viral cards (product layer apart from mechanism layer, a one-line `Facts:` JSON); `viral-stats` corpus profile and niche concentration; mechanism map, essence, fit profile; 12-20 specific candidates from five sources (the references' own products are one); up to 3 research agents (WebSearch/WebFetch, origin-blind dossiers, evidence rows graded A-D), a red-team agent, rubric scoring, six gates, independent-evidence cap, category cap 2, dominant-niche defence notes; three picks + blueprints in `RUN/deliverables/`; optional continue-to-Create on the user's yes. Nothing is generated (no model, no credits, no CapCut).
- Toolkit additions: `viral-stats`, `candidates` (add/list/set/pool/score/rank/show), `evidence`, `econ`, `new-run --submode`, `inventory --as baseline`, `prep-all --set baseline`.
- Ledger modes/causes for picks: `--mode analyze-viral-browser`, causes research / scoring / bias / evidence.

**Why:** the user is building an owned-inventory store (see [[user-kosovo-ecommerce-founder]]) and wants the next products to sell found from what made viral videos spread, without the references' dominant niche (e.g. pet tools) deciding the answer.

**How to apply**
- After any change to the ATG command or library, also update `analyze-then-generate.txt` (dated `.bak-*` beside it), as for [[atp-build-prompt-sync]]. The two pipelines are independent copies: a fix to Create/Recreate/Edit in one does not reach the other unless it is ported.
- `/update-from-errors analyze-then-generate` was not edited into that command's ATP target map; it resolves the target generically. Add a known map for ATG (including `reference/viral-browser.md` and the `candidates`/`evidence` tools) if the user wants it.
- Not yet run end to end on real references or live web research (the toolkit was tested on synthetic data); the hypotheses to check on the first runs are listed in `analyze-then-generate/learning-log.md`.
