---
name: atg-vb-select
description: /analyze-then-generate Viral-Browser phase: blind scoring, red team, the six gates of thumb and the three picks (V6). Internal to that command.
user-invocable: false
---

# atg-vb-select — Viral-Browser: scoring, red team, selection (V6)

> `ATG` = `C:/Users/Glaresquare1/.claude/analyze-then-generate` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$ATG/scripts/atg.py"` (every call prints one JSON object on its last line: numbers, tables and records, never a verdict; run through Bash) · `RUN` = the run folder `ATG/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `ATG/reference/<file>/` (for the Viral-Browser playbook `<file>` is `viral-browser`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

Phase of `/analyze-then-generate` (Viral-Browser). Nothing is generated. At the end of each step print one short status line and store `T state --run RUN set stage=<…> next_step=<…>`.

Scripts gather, you decide: the `T` commands measure, extract, record, tabulate and calculate. Every reading of their numbers, every choice and every exception is yours, written down with its reason (`--by` / `--reason`, the bias log in `30-research/ranking.md`). The numbers in this phase (the 40 % niche share, the six gates, the evidence caps, the pack minimums) are rules of thumb: apply them with judgement, depart from them when the evidence says so, and write what you applied, what you set aside and why.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- viral-browser §1: `ATG/reference/viral-browser/020_1_the-team.md` (2.7 KB) (the persona block for the agent prompts)
- viral-browser §0: `ATG/reference/viral-browser/010_0_precedence-and-hard-rules.md` (4.4 KB) (precedence, hard rules, the evidence grades)
- viral-browser §5: `ATG/reference/viral-browser/230_5_niche-bias-control-the-reference.md` (13.6 KB) (niche-bias control: the selection obligations)
- viral-browser §7.4: `ATG/reference/viral-browser/300_7.4_rules-of-evidence.md` (4.7 KB) (rules of evidence)
- viral-browser §7.6: `ATG/reference/viral-browser/320_7.6_the-red-team-pass.md` (2.1 KB) (the red-team pass)
- viral-browser §8.1: `ATG/reference/viral-browser/350_8.1_the-rubric-weights-in-config-jso.md` (2.6 KB)
- viral-browser §8.2: `ATG/reference/viral-browser/360_8.2_scoring-procedure.md` (4.1 KB)
- viral-browser §8.3: `ATG/reference/viral-browser/370_8.3_the-gates.md` (2.6 KB)
- viral-browser §8.4: `ATG/reference/viral-browser/380_8.4_procedure.md` (2.5 KB)
- viral-browser §8.5: `ATG/reference/viral-browser/390_8.5_selection-rules.md` (1.3 KB)
- viral-browser §8.6: `ATG/reference/viral-browser/400_8.6_fewer-than-three.md` (0.8 KB)
- viral-browser §13.3: `ATG/reference/viral-browser/490_13.3_red-team-agent-run-in-background.md` (4.9 KB) (the red-team agent's prompt)
- viral-browser §13.4: `ATG/reference/viral-browser/500_13.4_scoring-agent-fresh-context-also.md` (3.3 KB) (the scoring agent's prompt)

## Steps

### V6. Scoring, red team and selection
- Spawn the **scoring agent** (`viral-browser.md` §13.4): a fresh, blind context that never sees the
  cards, the mechanism map or any origin. It rates every researched candidate
  (`T candidates rate --id C## --ratings demand=4,commercial=3,… --refs "demand=EV001+EV002 …"
  --confidence low|medium|high --by …`; a form check only: an integer 1-5, a known criterion, evidence rows
  that exist for the candidate) and records its readings of price fit, compliance and exclusion with
  `T candidates set --price-fit yes|variant|no|unknown --compliance clear|resolved|open|unknown --excluded …`
  (the words are defined in `viral-browser.md` §8.2 item 3; the command echoes what it stored; a rating no
  row backs says `--refs "demand=none"`). It applies the rules of thumb for evidence
  and says so in its note: a rating on demand, commercial, competition, economics or compliance with no
  independent grade A or B row (of any direction) is 2 at most; a 4 or 5 needs a positive one, and so does a 3 on compliance (§7.4) (for economics the calculated estimate also needs a
  sourced input row); negative rows that match the positive ones hold a 4 or a 5 at 3. No script caps or
  changes a rating. **This session does not score**: it built the pool and has seen the origins. A
  compliance row is **positive** only when the obligation can be met by a known route at a stated cost
  (`viral-browser.md` §7.4), so `resolved` and G2 need the route and cost rows; the fit profile holds
  mechanism requirements only (the brief's price, cost and compliance constraints are read under economics,
  compliance and G1/G2). The stored `economics_by_market` is the authority, not the dossier's older numbers.
  The scorers read `T candidates show --blind` and `T evidence list --cand C## --md --no-copies`.
- Read the table yourself: `T candidates table --run RUN --sort weighted --desc` sets the candidates
  side by side (ratings per criterion, `weighted_sum_of_rated` = a plain weighted sum of the ratings where
  an unrated criterion adds nothing, confidence, red team, price fit, compliance, economics per market, an
  evidence cell "rows (grade A/B; distinct sites)", pick rank; `--blind` hides the origin). It marks no
  winner and applies no gate. Choose the **red-team targets** yourself: the candidates you would pick under
  the gates of thumb below, plus the next two (when fewer than three pass, the near misses nearest to
  passing, each with the gate it fails: the red team also closes the gaps that decide those gates, for
  example the compliance route and its cost per market). Spawn the red-team agent (§13.3) on them and record each
  reading (`T candidates set --id C## --redteam survives|weakened|fails --note "…" --by red-team`),
  eliminate the ones that fail (`--status eliminated --by main --reason "…"`), have a fresh scoring agent
  revisit only the criteria the red team names, and read the table again until every target has a reading
  (two rounds at most).
- **Select** (this session, by your own reading). Apply the six gates of thumb to each candidate: the price
  band; a contribution margin of at least 25 % of net revenue from `T econ` with a sourced input row
  (read per market in `economics_by_market`, side by side: you decide which market governs for this
  brief and write down why); compliance clear or resolved, backed by a positive independent official or
  reputable row; not excluded by
  the brief; positive independent evidence from at least two distinct sources across demand, commercial and
  competition, one of them commercial; ratings of at least 3 on demand, commercial, economics, compliance
  and fit, and confidence of at least medium. Choose the three picks and the runner-ups (at most two picks
  in a niche, none sharing a product type) and break any tie by your own reading, written down. Write the
  defence of every pick from the dominant niche against the best outside-niche alternative
  (`T candidates set --id C## --defence "…"`); a pick with no honest defence is eliminated and the selection
  redone. Run the what-if yourself: the same selection without the reference-derived evidence and without the
  fit criterion (`T candidates table --exclude-criteria fit`), and say whether the picks change. Write
  `30-research/ranking.md`: the picks, the runner-ups, every other candidate with the reason it is not a
  pick, the what-if and the bias log (your dominance reading, and every gate of thumb you applied or set
  aside, each with its reason). Then record the result for each pick: `T candidates set --id C##
  --status picked --pick-rank N --by main --reason "…"` (`--status runner-up` for the runner-ups;
  `--pick-rank` records your pick order).
- Show the ranking table in chat: the picks, the runner-ups, the gate each other candidate did not meet
  (your reading), any exception. If fewer than 3 meet the gates, run the backfill first (once: `T state --run RUN set stage=backfill next_step=research next_skill=atg-vb-research`,
  then invoke Skill `atg-vb-research`, whose Backfill step hands back here); if still
  fewer, report the shortfall and say which gate removed each and what could be relaxed (§8.6): a gate is
  never lowered silently to fill the table. `next_step=blueprints`.

## Rules this phase owns (contract item 25, selection part)

Item 25 is written out in `atg-vb-synthesis`; at selection it means: a fresh scoring agent rates (never this session); every pick has a red-team reading; every pick from the dominant niche has a written defence against the best outside-niche alternative before the picks are recorded; at most two picks share a niche and none a product type; the what-if is run; and every gate you apply or set aside is written in the bias log with its reason.

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
- Viral-Browser: never state a number without its source and retrieval date or its method; never score
  "unknown" as 3; never count a grade D row; never invent a URL, a quote or a figure; never present an
  estimate as a measurement; never credit a product with what the creator, a trend or paid reach
  carried; never take attention for buying evidence (attention-only videos teach mechanisms and never prove a
  product sells, `viral-browser.md` §3.2); never claim EU or global demand from US-only evidence without the
  "market gap" flag (a pick for the EU or a global market backed only by US evidence carries it, with confidence
  no higher than medium, §2).
- Viral-Browser: never lower a gate silently to fill the table (fewer than 3 candidates meeting the gates
  is a valid result; any gate you relax is named in the report with its reason), and never show a pick
  without its confidence and what would change the call.
- Never record the picks before the red-team readings and the defence notes exist.

## Hand-off

`T state --run RUN set stage=selected next_step=blueprints next_skill=atg-vb-deliver`, then invoke Skill `atg-vb-deliver`.

After a compaction, or on `resume`, re-invoke the skill named in `RUN/state.json → next_skill`: its text may have been summarised away.
