---
name: atg-vb-synthesis
description: /analyze-then-generate Viral-Browser phase: corpus profile, mechanism map, niche vocabulary and bias plan, candidates, cost basis (V3–V4b). Internal to that command.
user-invocable: false
---

# atg-vb-synthesis — Viral-Browser: synthesis, niche bias control, candidates, cost basis (V3–V4b)

> `ATG` = `C:/Users/Glaresquare1/.claude/analyze-then-generate` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$ATG/scripts/atg.py"` (every call prints one JSON object on its last line: numbers, tables and records, never a verdict; run through Bash) · `RUN` = the run folder `ATG/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `ATG/reference/<file>/` (for the Viral-Browser playbook `<file>` is `viral-browser`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

Phase of `/analyze-then-generate` (Viral-Browser). Nothing is generated. At the end of each step print one short status line and store `T state --run RUN set stage=<…> next_step=<…>`.

Scripts gather, you decide: the `T` commands measure, extract, record, tabulate and calculate. Every reading of their numbers, every choice and every exception is yours, written down with its reason (`--by` / `--reason`, the bias log in `30-research/ranking.md`). The numbers in this phase (the 40 % niche share, the six gates, the evidence caps, the pack minimums) are rules of thumb: apply them with judgement, depart from them when the evidence says so, and write what you applied, what you set aside and why.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- viral-browser §1: `ATG/reference/viral-browser/020_1_the-team.md` (2.7 KB) (the persona block for the agent prompts)
- viral-browser §4.1: `ATG/reference/viral-browser/120_4.1_measure-first.md` (2.5 KB)
- viral-browser §4.2: `ATG/reference/viral-browser/130_4.2_mechanism-map-20-analysis-mechan.md` (1.1 KB)
- viral-browser §4.3: `ATG/reference/viral-browser/140_4.3_hooks-length-and-pacing.md` (1.0 KB)
- viral-browser §4.4: `ATG/reference/viral-browser/150_4.4_engagement-style-the-approach.md` (0.6 KB)
- viral-browser §4.5: `ATG/reference/viral-browser/160_4.5_audience-and-mentality.md` (1.3 KB)
- viral-browser §4.6: `ATG/reference/viral-browser/170_4.6_what-hooked-them-the-essence-20.md` (1.1 KB)
- viral-browser §4.7: `ATG/reference/viral-browser/180_4.7_confounds-survivorship-and-small.md` (0.6 KB)
- viral-browser §4.8: `ATG/reference/viral-browser/190_4.8_trend-read.md` (0.7 KB)
- viral-browser §4.9: `ATG/reference/viral-browser/200_4.9_niche-concentration-and-the-bias.md` (0.9 KB)
- viral-browser §4.10: `ATG/reference/viral-browser/210_4.10_files-for-a-later-create.md` (0.4 KB)
- viral-browser §4.11: `ATG/reference/viral-browser/220_4.11_what-the-user-sees.md` (0.3 KB)
- viral-browser §5: `ATG/reference/viral-browser/230_5_niche-bias-control-the-reference.md` (13.6 KB) (niche-bias control)
- viral-browser §6: `ATG/reference/viral-browser/240_6_candidate-generation-v4.md` (4.5 KB) (candidate generation)
- viral-browser §7.0: `ATG/reference/viral-browser/260_7.0_before-the-wave-the-common-cost.md` (3.4 KB) (the common cost basis)
- viral-browser §13.5: `ATG/reference/viral-browser/510_13.5_niche-audit-agent-fresh-context.md` (3.5 KB) (the niche-audit agent's prompt)
- creative-direction §4: `ATG/reference/creative-direction/040_4_the-trend-read-written-into-20-a.md` (2.0 KB) (the trend read, for §4.8)
- analysis-protocol §5: `ATG/reference/analysis-protocol/060_5_cross-video-synthesis.md` (6.5 KB) (the cross-video synthesis, for §4.10)
- viral-browser §7.3: `ATG/reference/viral-browser/290_7.3_the-lanes.md` (9.3 KB) (the economics paragraph: the arguments of `T econ` and `T landed`, for V4b)

## Steps

### V3. Corpus profile and synthesis
- `T viral-stats --run RUN` (`--set both` with a baseline): tables only. Per set it prints the
  distributions (length, median shot, cuts per 10 s, first cut, when speech starts (any word, and the
  first word of probability 0.5 or more), words per second, loudness, loop similarity, text spans,
  tempo, beat strength, harmonic share, spectral flatness, audible non-speech share), the shares (a cut in the first 3 s, no cut at all, words found, a word or
  a text in the first second, vertical 9:16, attention-only) and one `labels` table per Facts key
  (label, count, share, videos). The `category` table is read through the niche vocabulary you
  recorded, with the raw labels written on the cards folded in, and marks each label
  `recorded_in_vocabulary` true or false: place every label that is not in the vocabulary
  (`T niches add` / `map`, with `--by main --reason "…"`), then run it again. It also lists
  `cards_without_facts` and `cards_with_unreadable_facts`: fix those cards (every reference card needs a
  `category`, `non-product` when no product category shows). Nothing is flagged, labelled or ranked: no
  script says which niche dominates or whether two names are one niche.
  **You read the category table** and apply the rule of thumb (`viral_browser.rules_of_thumb`): a niche
  that is 40 % or more of the references' cards is a **dominant niche**; with fewer than 10 videos read
  every share as an indication, not a rate. Write your reading, with any exception and its reason, in
  the bias log.
- Write, as `viral-browser.md` §4: `mechanism-map.md` (mechanisms `M1…`, k of n, niche
  independence, confounds), the hook, length and pacing profile, the engagement style (one template
  per family plus the composite), the audience and mentality model, `viral-essence.md` (the essence,
  the fit profile, what is not inferred), the trend read (at most `trend_checks[depth]` bounded
  searches; if a TikTok account is connected in Higgsfield, `tiktok_music_trending` for the market's
  country code, loaded with ToolSearch, else skipped silently), your niche-dominance reading with its
  bias plan, and the standard `families.md`, `craft-sheet.md` and `project-profile.md` for a later
  Create. Start the bias log, the "Bias log" section of `30-research/ranking.md` (written by the main
  session, not by a script).
- Show the short summary (§4.11): the essence in 5 lines, the fit profile, the niche shares (your
  dominance reading) and the controls it triggers, the mechanisms, the typical length and hook profile.
  `next_step=candidates`.

### V4. Candidates
- Build the long list of 12–20 specific candidates from the five sources (`viral-browser.md` §6),
  with `T candidates add` (or `--from-json`). A candidate is a product a supplier search returns, not a
  category; its name, definition, **niche** (as `--category`: a label from the vocabulary, or a new
  niche you decide and record with `T niches add`), type and origin are all required, and the name and
  definition never mention the references. `add` stores the niche under the one the agents recorded for
  that label (as written otherwise) and reports `niche_not_recorded_in_the_vocabulary`: record those.
  Screen with stated reasons.
- Read the balance of the long list yourself: `T candidates summary --run RUN` counts the candidates by
  niche, type, origin and status (`--exclude-eliminated` leaves the eliminated out). The rules of thumb
  (`viral_browser.rules_of_thumb`): at least 6 niches, none above 40 % of the list, at most half from
  the references' own products. Repair the list where the numbers show it departs from them, or keep
  it and write the exception and its reason in the bias log; no script flags or refuses anything. Then
  spawn the **niche-audit agent** (`viral-browser.md` §13.5; fresh context, it changes nothing and
  writes `30-research/niche-audit.md`): it reads the vocabulary for one niche under several names,
  synonyms that share no word included. Apply its merges (`T niches merge --from … --to … --reason "…"
  --by main`, which folds the members and renames the niche on the candidates), run `T viral-stats` again
  when a merge touched a card label, and record the audit (`T niches audit --by main --result "<what it
  found and what was applied>" --report 30-research/niche-audit.md`). Then choose the shortlist (6 / 9 /
  12 by depth), read `T candidates summary --run RUN --ids C01,C02,…` for exactly that set against the
  same rules of thumb, and start research with
  `T candidates set --run RUN --ids C01,C02,… --status researching --by main --reason "<the balance reading and any exception>"`.
  Statuses are a vocabulary you use and record (long, shortlisted, researching, researched, eliminated,
  picked, runner-up, watch): `set` changes any field and any status from any status, logs `--by` and
  `--reason` in the candidate's history, and the toolkit sets none on its own. Change a researched
  candidate's name, type, definition or niche only with a stated reason.
- Show one table: candidate, niche, origin, why it is in the pool. `next_step=cost-basis`.

### V4b. Cost basis and shared inputs (before the wave)
- Decide, once, the inputs that do not depend on the product and write them with their sources in
  `30-research/cost-basis.md` (`viral-browser.md` §7.0): the postage per order by weight class from a
  carrier's own price list (US and the lead country) plus pick, pack and materials = the fulfilment per
  order, and the store's shipping policy (`T econ --shipping-charge`, the same for every candidate; `T econ --prices` prints a price ladder); the return rate and the cost of a returned order
  per market; the card and platform fees of the channel's real fee schedule; the exchange rate with its
  source and date; the tariff regime for the origin with the guess it rests on; the freight tables and the
  calendar. Register the sourced ones once as evidence rows (`T evidence add --from-json`), under one
  candidate, so that the research agents copy them (`T evidence copy`) instead of searching again. Use the
  cost basis for the economics screen of V4: `T econ … --target-pct 25` per market on a rough landed cost
  (`T landed`) says which retail price a candidate needs; a price above the band's top, or far above what
  the market shows, removes the candidate with that reason. `next_step=research`.

## Rules this phase owns (contract item 25)

25. **Niche-bias control: the references' product niche must not decide the answer**
    (`viral-browser.md` §5). Candidates come from the mechanism, not from "more of what the videos
    show"; the references' own products are one source among five; niches are compared through a
    **vocabulary the agents build from the data** (`T niches`, a record with its history; no script
    lists, knows or compares any niche), never as free text, and a fresh **niche-audit agent** reads
    it for one niche under several names, synonyms that share no word included (no script flags
    look-alike names: the main session applies the agent's merges with a reason and records the
    audit); the long list should span at least six niches with none above 40 %, and the main session
    reads the **shortlist against the same rules of thumb before research starts**
    (`T candidates summary`, then `T candidates set --status researching --by main --reason "…"`;
    the numbers are guidance, and every exception is written in the bias log with its reason);
    research and rating are **origin-blind** (a fresh scoring agent rates, never this session); evidence rows carry a direction
    and an independence flag, and the scoring agent applies the rule of thumb that a criterion without
    a positive independent grade A/B row is rated 2 at most; the key criteria need a 3 when the main
    session selects; at most two picks should share a niche and none a product type; every pick has a
    red-team reading, and every pick from the dominant niche (a niche that is 40 % or more of the
    references' cards, read from `T viral-stats` by the main session) a written defence against the
    best outside-niche alternative, **before** the picks are recorded; the run reports whether the
    picks change when reference-derived evidence or the fit criterion is removed (the main session's
    own what-if: `T candidates table --exclude-criteria fit`). A data-backed product from the
    references' own niche stays eligible and may win: the evidence rules demand independent proof, not
    a quota. No script ranks, caps, gates or picks: the main session reads the tables, decides, and
    writes the decisions and their reasons in `30-research/ranking.md` (the picks, the runner-ups, why
    each other candidate is not a pick, the what-if and the bias log).

## Never (this phase)

- Viral-Browser: never let the references' product niche decide the answer (item 25, `viral-browser.md`
  §5). Never build the pool from "more of what the videos show"; never start research on a pool you have
  not read for balance (fewer than 6 niches, one niche above 40 %, or more than half the candidates from
  the references' own products is a departure to repair, or an exception to write down with its reason in
  the bias log); never put a candidate's origin in a research dossier, a research prompt or
  a scoring pass; never count reference-derived evidence as independent; never skip the defence note
  of a dominant-niche pick; and never exclude the dominant niche for being dominant.
- Viral-Browser: never type a niche, category, product or brand name into a script or a config (the
  agents decide them from the data and record them with `T niches`); never start research on a niche
  vocabulary that no fresh agent has audited (`T niches audit` records it; no script flags look-alike
  names); never leave a possibly split niche without a merge (`T niches merge --reason`) or a written
  reason in the bias log for keeping it apart; never record an audit that no fresh agent made; never
  rate in this session (the fresh scoring agent rates); never change a candidate's status, ratings or
  pick order without `--by` and `--reason` (the toolkit sets none by itself), never type an economics
  figure by hand (`T econ --cand` records it), and never change a researched candidate's name, type,
  definition or niche without a stated reason; never record the picks before the red-team readings and the
  defence notes exist, or from `T viral-stats` tables older than the niche vocabulary (run it again after
  a merge or a new mapping).
- Never start research on a pool you have not read for balance, and never exclude the dominant niche for being dominant (item 25).

## Hand-off

`T state --run RUN set stage=candidates-done next_step=research next_skill=atg-vb-research`, then invoke Skill `atg-vb-research`.

After a compaction, or on `resume`, re-invoke the skill named in `RUN/state.json → next_skill`: its text may have been summarised away.
