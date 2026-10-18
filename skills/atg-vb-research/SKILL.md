---
name: atg-vb-research
description: /analyze-then-generate Viral-Browser phase: the research wave with up to three web-only agents (V5). Internal to that command.
user-invocable: false
---

# atg-vb-research — Viral-Browser: research (V5)

> `ATG` = `C:/Users/Glaresquare1/.claude/analyze-then-generate` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$ATG/scripts/atg.py"` (every call prints one JSON object on its last line: numbers, tables and records, never a verdict; run through Bash) · `RUN` = the run folder `ATG/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `ATG/reference/<file>/` (for the Viral-Browser playbook `<file>` is `viral-browser`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

Phase of `/analyze-then-generate` (Viral-Browser). Nothing is generated. At the end of each step print one short status line and store `T state --run RUN set stage=<…> next_step=<…>`.

Scripts gather, you decide: the `T` commands measure, extract, record, tabulate and calculate. Every reading of their numbers, every choice and every exception is yours, written down with its reason (`--by` / `--reason`, the bias log in `30-research/ranking.md`). The numbers in this phase (the 40 % niche share, the six gates, the evidence caps, the pack minimums) are rules of thumb: apply them with judgement, depart from them when the evidence says so, and write what you applied, what you set aside and why.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- viral-browser §1: `ATG/reference/viral-browser/020_1_the-team.md` (2.7 KB) (the persona block for the agent prompts)
- viral-browser §0: `ATG/reference/viral-browser/010_0_precedence-and-hard-rules.md` (4.4 KB) (precedence, hard rules, the evidence grades)
- viral-browser §7.1: `ATG/reference/viral-browser/270_7.1_who-does-what.md` (7.3 KB)
- viral-browser §7.2: `ATG/reference/viral-browser/280_7.2_depth.md` (1.4 KB)
- viral-browser §7.3: `ATG/reference/viral-browser/290_7.3_the-lanes.md` (9.3 KB)
- viral-browser §7.4: `ATG/reference/viral-browser/300_7.4_rules-of-evidence.md` (4.7 KB) (rules of evidence)
- viral-browser §7.7: `ATG/reference/viral-browser/330_7.7_the-dossier-30-research-c-md-ori.md` (1.5 KB) (the dossier)
- viral-browser §13.2: `ATG/reference/viral-browser/480_13.2_research-agent-run-in-background.md` (7.4 KB) (the research agent's prompt)
- *"web plus my Chrome":*
  - viral-browser §7.5: `ATG/reference/viral-browser/310_7.5_the-browser-queue.md` (3.1 KB) (the browser queue)

## Steps

### V5. Research (agents)
- Spawn up to 3 research agents (Agent tool, `subagent_type: general-purpose`,
  `run_in_background: true`) with disjoint candidate lists and the prompt of `viral-browser.md`
  §13.2 filled in (market, currency, band, VAT convention, selling model, sales channel, importer
  country, capital limit, exclusions, depth, today's date). They register evidence (`T evidence add`
  with `--signal positive|negative|mixed|neutral`, `--independent yes` and `--by`; the toolkit checks the
  form only: the required fields, and a URL on an independent grade A or B row; each sourced economics
  input is its own grade A or B row with a URL), run `T econ … --cand C## --run RUN --market <M>`
  (arithmetic only; once per market for a global or multi-country market: the results are kept per market
  in `economics_by_market`, side by side, each with its inputs, and an evidence row with signal
  `calculation` is written; the contribution per order, `break_even_cpa` (it can be negative),
  `break_even_roas_*` (null when the contribution is not positive) and `inputs_left_at_zero` are numbers
  for you to read, not judgements), write `30-research/<C>.md`, origin-blind, and queue unreadable pages
  in their own `queue-<C>.md`. The prompt carries the cost basis and the shared rows to copy; the agents
  use `T landed`, `T econ … --target-pct 25` (the retail price a 25 % contribution needs, set against the
  prices the market shows), `T evidence add --from-json` and `--opened yes|no`. A background wave stops when
  you interrupt the turn: the ledger keeps what was registered, so restart each agent with only its
  unfinished candidates and a STATE AT RESTART note (`viral-browser.md` §13.2).
- Before you read the results side by side, read the stored economics inputs of every candidate (each
  candidate's `economics_by_market` has them) for different assumptions on the same cost lines; reconcile them
  on the cost basis: re-run `T econ` for each candidate and market, withdraw the superseded calculation rows
  with `T evidence retract` and the reason, and note it in the bias log.
- When they have reported, check that every shortlisted candidate has a dossier, evidence rows, an
  economics row and a sourced input row behind it (`T evidence list --counts` tabulates the rows by lane,
  signal, grade, independence and distinct sites; it weighs nothing); a missing one is researched once by
  a new agent. A candidate an agent reports as settled by a gate is eliminated here by you
  (`T candidates set --id C## --status eliminated --by main --reason "<the gate and the evidence>"`; the
  reason stays on the candidate). A wrong evidence row is withdrawn with
  `T evidence retract --id EV### --reason "…"` (kept on record, left out of the counts).
  If an agent reports a denied tool (`WebSearch`, `WebFetch`, `Bash`), research that candidate in this
  session within the same budget instead of retrying the agent.
- With "web plus my Chrome": load the browser tools in one call (`ToolSearch "select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__tabs_create_mcp,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__get_page_text,mcp__claude-in-chrome__read_page,mcp__claude-in-chrome__find,mcp__claude-in-chrome__computer,mcp__claude-in-chrome__tabs_close_mcp"`),
  call `tabs_context_mcp` first and process the `30-research/queue-<C>.md` files in this session, up
  to `browser_pages_per_candidate[depth]` pages per candidate, read-only (`viral-browser.md` §7.5),
  registering the evidence. Without it, queued pages stay "unreachable". Read a marketplace search page
  with a short read-only script (title, price, rating count and sold badge of each result), a trend chart
  from a screenshot, an official rules page as text; then re-run `T econ --cand` at the retail price the
  pages support (the market's stored result is replaced; withdraw the superseded calculation row with the
  reason). A page that informs several candidates counts for each; call `tabs_context_mcp` with
  `createIfEmpty` again before each batch, and stop after two failed attempts to connect.
- Blockers (a tool failure, rate limits) are reported, not asked. If `WebSearch` and `WebFetch`
  are both unavailable, stop here: V1–V3 are delivered (the mechanism map and the fit profile are
  useful alone) and the summary says research could not run. `next_step=scoring`.
- **Backfill:** if your selection in V6 leaves fewer than 3 candidates that meet the gates of thumb, come
  back here **once**: shortlist the next `backfill_researched[depth]` candidates from the long list (read
  the balance rules of thumb on that set again and record `researching` with `--by main --reason`),
  research them the same way, then hand off as below: `atg-vb-select` rates the new candidates blind and selects again (`viral-browser.md` §7.1).

## Never (this phase)

- Viral-Browser: never state a number without its source and retrieval date or its method; never score
  "unknown" as 3; never count a grade D row; never invent a URL, a quote or a figure; never present an
  estimate as a measurement; never credit a product with what the creator, a trend or paid reach
  carried; never take attention for buying evidence (attention-only videos teach mechanisms and never prove a
  product sells, `viral-browser.md` §3.2); never claim EU or global demand from US-only evidence without the
  "market gap" flag (a pick for the EU or a global market backed only by US evidence carries it, with confidence
  no higher than medium, §2).
- Viral-Browser: never buy, sign up, log in, message a seller or submit a form; never collect personal
  data; never use a browser tool unless the user chose "web plus my Chrome", and then only to read
  pages (`viral-browser.md` §0 rule 6, §7.5).
- Never put a candidate's origin (which reference or card it came from) in a research dossier or a research prompt.

## Hand-off

`T state --run RUN set stage=researched next_step=scoring next_skill=atg-vb-select`, then invoke Skill `atg-vb-select`.

After a compaction, or on `resume`, re-invoke the skill named in `RUN/state.json → next_skill`: its text may have been summarised away.
