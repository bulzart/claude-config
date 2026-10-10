# Learning log: /update-from-errors passes on /analyze-then-generate

One section per pass, newest last. The next pass reads this file before the ledger (§1.2). A pattern that
recurs after a logged change means that change failed: revise it, do not repeat it.

## 2026-10-11 · fork · /analyze-then-generate created from /analyze-then-pick
- **Origin:** a copy of the `/analyze-then-pick` library as of 2026-10-10 14:04 (all references, the model guides, the
  toolkit renamed `atg.py`, the ledger CE-001..CE-029). The history of every inherited rule is that pipeline's own
  learning log: `~/.claude/analyze-then-pick/learning-log.md`.
- **Added:** the Viral-Browser sub-mode (`reference/viral-browser.md`; command steps V1-V9 and contract items 23-25;
  toolkit `viral-stats`, `candidates`, `evidence`, `econ`, `new-run --submode`, the `baseline` set of `inventory` and
  `prep-all`; config `viral_browser`; the ledger causes research, scoring, bias, evidence).
- **No `/update-from-errors` pass has run on this pipeline yet.**
- **Hypotheses to test on the first Viral-Browser runs:**
  1. The independent-evidence cap and the category cap keep a dominant niche from filling the picks without
     excluding it (check `ablation_changed` and the defence notes).
  2. Research agents reach enough primary sources with `WebSearch` and `WebFetch` alone; if most lanes end
     "unreachable", the browser route becomes the default.
  3. The default rubric weights, the 25 % contribution gate and the 3x markup ceiling fit the user's real margins.
  4. Origin-blind scoring survives the main session having read the cards (the scorer sees `candidates show --blind`).
  5. Twelve to twenty candidates and 9 researched at standard depth is the right funnel for the cost.
