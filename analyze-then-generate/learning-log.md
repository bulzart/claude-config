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

## 2026-10-11 · review of the Viral-Browser build, and the Create blend
- **Independent review** (a fresh agent, files only, toolkit run on a scratch copy) found, and this pass fixed: niche controls that
  compared free-text labels (a first fix hardcoded a department list into the scripts; the user rejected that: no niche or category name may live in a script, so the fix is now a niche vocabulary the agents build from the data, `T niches`, which the scripts only enforce; `candidates add` refuses a label no agent has placed, the shortlist is checked by
  the command that starts research); gates that tested that evidence rows exist but not what they say (evidence now has a signal and an
  independence flag, an independent grade A/B row needs a URL, distinct sources are counted, key criteria have floors after the cap, G1
  needs an economics row written by `econ --cand`, G2 needs a positive compliance row, refs are validated); a red team that missed the
  final picks (it now attacks the gated, capped selection plus two, and `rank --apply` refuses a pick with no verdict or a dominant-niche
  pick with no defence); a scorer that could not be blind (a fresh scoring agent scores); `caught-error add` examples without `--title`;
  a "Continue to Create" that skipped the asset inventory (it now enters the Create flow at its start for the new inputs); `econ` fees on
  net revenue and one ROAS basis (fees on the amount paid, ROAS on both bases, a stress case, a capital check); AskUserQuestion headers over
  12 characters; one shared browser queue written by three agents (one file per candidate); a config merge that crashed on a partial gates block.
- **Gaps closed:** a backfill wave when fewer than three pass; the brief asks how the user sells (channel, ad platform, importer country,
  capital limit); the references' post pages are read when links and Chrome are available; a trend pass per pick; an engagement-style
  template per family; the EU withdrawal right and a per-market convention for Global.
- **User request, same day:** Create must not be hardened into re-making the reference samples. It is now a **blend**: the references
  understood (the craft sheet, the audience and trend read) and the product understood (a product insight sheet written from the supplied
  assets) are combined to design the most engaging video; families are evidence and ingredients, never a menu; hybrid groups are allowed;
  every seed names its blend and passes a blend test and a template-lock test (`creative-direction.md` section 5.0b).
- **Hypotheses to test next:** (1) the agents' niche vocabulary stays consistent on real reference folders (watch the look-alike-niche warnings and the unresolved labels `viral-stats` reports);
  (2) the scorer's blind scores differ from what the main session would have given (compare on the first run); (3) the blend test rejects
  re-skinned reference templates without rejecting good ideas; (4) one backfill wave is enough to reach three picks at standard depth.
