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

## 2026-10-11 · second independent review (D1-D9) and the rest of the Create blend
- **Second review** (the same reviewer; files, and a scratch run of the toolkit) found, and this pass fixed: **D1** the dominant-niche check
  compared strings by case and trusted statistics computed before a vocabulary change (it now compares normalised keys; `viral-stats` records
  how every label resolved and `rank` blocks on stale statistics or unplaced labels); **D2** a careless niche split slipped past the pool
  balance and the caps (new: `niches merge`, `niches distinct` for pairs and for words that are not niche markers, a shared-word check that
  works from the data alone, no word list, in the pool, the shortlist, `rank` and `viral-stats`, and a fresh **niche-audit agent** whose
  recorded audit the shortlist requires: `viral-browser.md` §13.5); **D3** statuses and the contribution could be typed in
  (`candidates set --status researching` skipped the shortlist, `--contribution-pct` skipped `econ`): both are closed, and `score` and
  `econ --cand` refuse a candidate that is not in research; **D4** a Global market kept only the last `econ` run (now one result and one
  evidence row per market, the lowest contribution counts); **D5** label keys were ASCII-only (now case-folded Unicode); **D6** a grade C
  calculation could stand alone for economics (the criterion and G1 now need a grade A or B sourced input row too); **D7** ties went to the
  order the candidates were added (now independent rows, contribution, then name, with a warning at the pick boundary); **D8** `rank --force`
  needed no reason, a defence could be one word, a returns assumption of 0 passed silently and an unreadable ledger was read as empty and then
  overwritten (now: a reason, 30 characters, a warning, and a hard stop); **D9** the documentation lagged the toolkit.
- **Create blend, what was left:** the structure, length, payoff timing, pacing QC and copy test still pointed at "the family profile" or "the
  family's references", which pulled Create back toward one family's template. They now follow the mechanisms the blend borrows (Recreate keeps
  the source's family profile); the ninth copy-test question (the template swap) is in the list; the copy test runs against every reference the
  blend borrows from; the product truths are "up to six, as many as the supplied assets support" and a gap is "not supplied"; a mixed
  "Agent's choice plus named groups" answer without quantities gives the groups half of the videos (rounded up).
- **Hypotheses to test next:** (1) the audit agent finds real synonyms on real reference folders without over-merging (watch merges that
  push the pool below six niches); (2) the shared-word flag is not too noisy (count how often `niches distinct --word` is needed);
  (3) the per-market minimum matches the margins the user sees on a real first order.

## 2026-10-11 · third independent review (E1-E10)
- **Third review** (the same reviewer, a scratch copy of the toolkit and 13 repro scripts) found, and this pass fixed: **E1** `watch` was a status
  anyone could type and it counts as a research status, so evidence, economics and scoring accepted a candidate that never went through the
  shortlist (now `watch` only for a candidate already in research, and `rank --apply` refuses a pick with no recorded shortlist check);
  **E2** the dominant-niche control could be switched off without a blocker (`viral-stats --niche-threshold 1.0`, `viral-stats --set baseline`
  overwriting the references set, cards without a `category`, a missing or corrupt statistics file): the ranking now recomputes the dominant
  niche from the stored table with the configured threshold, `viral-stats` keeps the sets it did not recompute, and a missing or unreadable
  file, a references set without a category on every card, or stale resolution all block `rank --apply`; **E3** `set --category` after the audit
  and the shortlist could move a pet product into another niche unseen (now `--force --reason`, recorded and printed); **E4** waivers were free
  and invisible (`distinct --word pet --reason x`, an audit with no report, a merge with no reason): reasons need 25 characters, a word inside a
  niche name cannot be waived, the audit needs the audit agent's report `30-research/niche-audit.md` (200 bytes, newer than the newest niche),
  and `ranking.md` prints every merge, distinct decision, waived word, audit, forced shortlist, niche change and forced apply; **E5** three pet
  products spread over three niches ("pet feeding", "pet grooming", "dog care") passed because the word check counted pool share and never the
  picks (now niches whose names share a word, or share one with the dominant niche's labels, are flagged at the pool and shortlist and block the
  apply, and a pick that shares a word with the dominant niche's labels needs the same defence as a pick from it); **E6** the documented remedy
  for a shared word (`niches distinct --a --b`) did not clear it (the check now knows pairs judged distinct); **E7** `econ --cand` took an
  optional, case-sensitive market (now required, key without case); **E8** Unicode keys split on combining marks (two different Hindi words
  collided; now marks are kept); **E9** the docs claimed things the code did not do (reasons "printed in the bias log", "statistics older");
  **E10** four more "family" wordings in Create paths.
- **Not fixed, on purpose:** the toolkit cannot verify that a fresh agent performed the audit (it checks that the report exists and is newer than
  the newest niche); Turkish dotted I and vocalised Arabic still differ from their plain spellings (an agent maps them); `portable`, `silicone`
  and other modifiers can trip the shared-word flag on a set of nine (one `niches distinct --word` waives each, and it is printed).
- **Hypotheses to test next:** (1) the shared-word and name-overlap flags need at most a handful of decisions per run on a real folder; if they
  need dozens, the thresholds are wrong (`max_pool_share_per_category` is also the word threshold); (2) the audit agent's report is specific
  (names the entries that show a merge) and not boilerplate; (3) the "linked" defence for picks is not triggered by generic words.

## 2026-10-11 · fourth independent review (F1-F6)
- **Fourth review** (a narrow check of the round-3 code) found, and this pass fixed: **F1** edits after the shortlist were unrecorded, so a
  rename (`set --name Glove`) cleared the dominant-link defence rule, and a researched candidate could be sent back to `long`, edited and still
  picked (now the name, type, definition and niche of a candidate that went through research change only with `--force --reason`, recorded as
  an edit and printed in `ranking.md`; a candidate in research cannot go back to the long list; `rank` ranks only candidates in research);
  **F2** the dominant-link rule read the name, type and niche but not the `definition` or every member label of the dominant niche (now it
  reads the definition, the dominant niche's name, member labels and card labels); **F3** `viral-stats --niche-threshold 1.0` still silenced
  the card-label word flag (that flag now always uses the configured cap); **F4** the audit report check was satisfied by 200 bytes of "x", a
  report copied from another run, or a report dated tomorrow (now it must name every current niche, one verdict line each, and may not be dated
  in the future); **F5** only the biggest niche counted as dominant (every niche reaching the threshold now does); **F6** recording that a pick's
  niche differs from the dominant niche did not stop that niche's own name linking the pick (it does now).
- **Also:** a niche name or label with no letter or digit is refused (two of them collided as an empty key); an old statistics file of the wrong
  shape cannot crash `viral-stats`.
- **Not fixed, on purpose:** a stored baseline set survives after the baseline videos are removed (re-run `viral-stats --set baseline` to refresh
  it); the audit report is still a file the main session could write itself (it is the recorded trail, not a proof).

## 2026-10-12 · Create takes the Viral-Browser mining
- **User request:** the idea of Viral-Browser must also drive Analyze -> Create: understand the references' style, engagement and attention
  approach and the logic that made them viral (hooks, how the product is used, audience, mentality, mass-thinking patterns, length), then
  generate fitting scenario videos for the product in the assets folder, blending the mined data with the product information, as
  virality-backed videos; the agents must not be fixated on the references' product type.
- **Added (Create only; Recreate and `/analyze-then-pick` unchanged):** `viral-browser.md` section 14 (what Create takes and skips from the
  mining; only mechanisms whose driver is the craft are borrowed; the blend matrix `20-analysis/blend-matrix.md`; the virality rationale per
  video; the Create trend pass of up to `analysis.create_trend_checks` = 6 dated searches; what the mining never does); Create cards are viral
  cards (A3); the virality synthesis at A4 (`T viral-stats --run RUN --no-niche` writes `20-analysis/corpus-profile.*` and leaves
  `corpus-stats.*` alone, mechanism map, hook/length/pacing ranges, engagement style, audience and mentality, essence, trend read); ideation
  draws seeds from the available matrix cells (`creative-direction.md` section 5.0c); the plan's intent and the new `deliverables/blends.md`
  carry the rationale; the persona block opens every Create analysis and ideation prompt; the product truths are numbered PT1..PT6.
- **Not done on purpose:** no call to the Higgsfield virality predictor (it analyses an uploaded or generated video, its cost is unknown, and
  it cannot see the CapCut text and sound); the rationale is an argument from the references' evidence, never a prediction of reach.
- **Hypotheses to test on the first Create runs:** (1) the blend matrix drops mechanisms the product cannot honestly carry instead of
  forcing them, and the surviving cells give seeds that differ from each other; (2) viral cards for every reference do not make A3 too slow
  (watch the time per reference with two agents); (3) the attribution table in `blends.md` is enough to learn which mechanism, hook or
  truth won; (4) one pass of six dated searches finds usable current formats for the product's niche.
- **Review of this change** (a fresh agent, read only, one toolkit run) found and this pass fixed: Create's audience model was still the
  references' audience, so a pet-tools corpus with a non-pet product could still produce pet-audience scenes (the model now has a corpus half
  for the triggers and a **product half** for the situations and places; the blend matrix judges whether a trigger holds for the product's
  audience); `viral-stats --no-niche` still profiled the references' product form and price tier (dropped); the brief template had no slot for
  the rationale and still said "craft-sheet id" beside M# (both fixed); the agent prompt mixed protocol sections and a Viral-Browser run (a
  dedicated Create prompt, `viral-browser.md` 13.6); Create has no market (inferred from assets, documents and language, else region-free) and
  some transplant needs cannot be known (`unknown` cells stay available as a stated risk); a seed outside the matrix could not fill the blend
  line (`M#: none (new format), speculative`); the continuation to Create re-ran the synthesis (now only the product side of A4); the TikTok
  sound sentence was dropped; P# clashed with the pick labels and became PT#; "proven ingredients" became graded candidate ingredients.

