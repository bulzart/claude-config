---
name: atg-vb-deliver
description: /analyze-then-generate Viral-Browser phase: blueprints, reference packs (spec and photo links) and the deliverable files (V7). Internal to that command.
user-invocable: false
---

# atg-vb-deliver — Viral-Browser: blueprints, reference packs, deliverables (V7)

> `ATG` = `C:/Users/Glaresquare1/.claude/analyze-then-generate` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$ATG/scripts/atg.py"` (every call prints one JSON object on its last line: numbers, tables and records, never a verdict; run through Bash) · `RUN` = the run folder `ATG/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `ATG/reference/<file>/` (for the Viral-Browser playbook `<file>` is `viral-browser`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

Phase of `/analyze-then-generate` (Viral-Browser). Nothing is generated. At the end of each step print one short status line and store `T state --run RUN set stage=<…> next_step=<…>`.

Scripts gather, you decide: the `T` commands measure, extract, record, tabulate and calculate. Every reading of their numbers, every choice and every exception is yours, written down with its reason (`--by` / `--reason`, the bias log in `30-research/ranking.md`). The numbers in this phase (the 40 % niche share, the six gates, the evidence caps, the pack minimums) are rules of thumb: apply them with judgement, depart from them when the evidence says so, and write what you applied, what you set aside and why.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- viral-browser §1: `ATG/reference/viral-browser/020_1_the-team.md` (2.7 KB) (the persona block for the agent prompts)
- viral-browser §0: `ATG/reference/viral-browser/010_0_precedence-and-hard-rules.md` (4.4 KB) (precedence, hard rules, the evidence grades)
- viral-browser §9: `ATG/reference/viral-browser/410_9_the-viral-blueprint-v7-per-pick.md` (3.2 KB) (the viral blueprint)
- viral-browser §9.1: `ATG/reference/viral-browser/420_9.1_the-product-reference-pack-per-p.md` (16.1 KB) (the product reference pack)
- viral-browser §10: `ATG/reference/viral-browser/430_10_deliverables-v7-v8.md` (5.4 KB) (deliverables)
- viral-browser §13.7: `ATG/reference/viral-browser/530_13.7_reference-pack-agent-run-in-back.md` (9.8 KB) (the reference-pack agent's prompt)
- *"web plus my Chrome":*
  - viral-browser §7.5: `ATG/reference/viral-browser/310_7.5_the-browser-queue.md` (3.1 KB) (the browser queue)

## Steps

### V7. Blueprints, reference packs and deliverables
- Per pick, a **trend pass** (up to `pick_trend_checks[depth]` bounded searches or pages for the
  formats, hooks and sounds now used in that product's niche and market, dated; `tiktok_music_trending`
  once when an account is connected), then `deliverables/product-NN.md` (its dossier and its
  blueprint, `viral-browser.md` §9–§10).
- **Reference packs** (`viral-browser.md` §9.1): right after the picks are recorded, spawn up to 3
  reference-pack agents, one per pick, in the background with the prompt of §13.7 filled in (run,
  toolkit, date, market, the pick, the depth and its `reference_pack_budget`), and write the blueprints
  meanwhile.
  - Each agent records the facts it finds (`T spec add`, with source, kind, grade, scope and variant),
    the photo links (`T photo find` / `add`) and its judgement of each core field with
    `T spec judge --cand C## --field … --fact SP### --status "<its own label, for example verified, official, reported, unverified, conflict>" --reason "…" --by …`
    (the latest judgement wins and nothing is computed). A fact found to be wrong is withdrawn with
    `T spec reject --id SP### --reason "…"`, a link with `T photo set --id PH### --reject --reason "…"`
    (both stay on record, off the sheet; `--restore` brings a link back). A manual or datasheet that is
    a PDF is read with `T pdf-text --url <PDF> [--pages 1-5]` (WebFetch cannot open a PDF with compressed
    text); a page that lists related products before its gallery is narrowed with
    `T photo find --match <word> --offset N --md`. The agent reads the product with
    `T candidates show --id C## --product-only` (no status, ratings or economics).
  - When they report, read each pack yourself: `T spec gaps --run RUN --cand C##` counts the facts and
    judgements for the core fields, `T spec table --run RUN --cand C##` sets the facts side by side with
    the plain spread of the numbers, and `T photo list --run RUN --cand C##` / `T photo check` produce the
    photo coverage table (links, confirmed, https and looked-at per view label as the agents wrote it,
    and for the core views). Whether a pack is enough is your reading, guided by the pack rules of thumb
    in `viral_browser.rules_of_thumb` (photo links per pick, attempts, thumbnail size, minimum angles,
    spec tolerance): no script suggests a set or calls a pack covered. A pack you judge not enough gets
    one more reference-pack agent for that pick alone,
    told what is missing, with the same budget again (one extra round only), and what is still missing is
    reported, never invented.
  - **No image is downloaded: the packs hold links.** Process `30-research/queue-<C>-pack.md` with the
    user's Chrome only when they allowed it (read-only: the image links of a gallery, a specification
    table; register them with `T spec add` / `T photo add`; an image you open in the browser may get its
    flags with `T photo set --looked-at yes`, which the four visual flags require; the views no source
    names are recorded the same way, `T photo set --angle front --basis looked --looked-at yes`: the
    looking step belongs to the stage, a background agent cannot do it), then `T spec render`
    and `T photo check` for each pick (`spec.md`, `photos.md` and `photos.html` are written into the pack:
    the judged value with its status and reason, or "no judgement recorded" with the facts side by side).
    The packs go in `deliverables/reference-C##-<name>/` (named after the candidate; the first
    `T spec render` or `T photo add` creates the folder).
- Then `viral-browser-report.md` (with each pick's specification table and photo links with their link
  status and the flags recorded),
  `evidence.md` (`T evidence list --run RUN --out <RUN>/deliverables/evidence.md`),
  `create-handoff.md` and `README.md`. `next_step=report-qc`.

## Never (this phase)

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
- Viral-Browser: never buy, sign up, log in, message a seller or submit a form; never collect personal
  data; never use a browser tool unless the user chose "web plus my Chrome", and then only to read
  pages (`viral-browser.md` §0 rule 6, §7.5).
- Viral-Browser: never read a size or weight off a photo; never give a specification fact without its
  source, kind, grade and date, and never call a single listing verified; never download an image (the
  packs hold links); never read a page or probe a link behind a login or past a block (401, 403, 429),
  or by another route after one; never call an angle verified when nobody looked at the image; and
  never present a web image as rights-cleared or as the user's own asset (`viral-browser.md` §9.1).
- Viral-Browser: never invent an exclusion. The user's exclusions come from the user alone, and the
  compliance, platform and IP screens are viability checks, never taste (`viral-browser.md` §0 rule 5).
  Never recommend fake scarcity, fake or undisclosed incentivised reviews, unprovable claims or any
  deceptive tactic in a blueprint (§0 rule 7).

## Hand-off

`T state --run RUN set stage=delivered-files next_step=report-qc next_skill=atg-vb-wrapup`, then invoke Skill `atg-vb-wrapup`.

After a compaction, or on `resume`, re-invoke the skill named in `RUN/state.json → next_skill`: its text may have been summarised away.
