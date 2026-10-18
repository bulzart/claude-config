---
name: atg-vb-cards
description: /analyze-then-generate Viral-Browser phase: inputs and brief, the run, inventory, preprocessing and the viral cards (V1–V2). Internal to that command.
user-invocable: false
---

# atg-vb-cards — Viral-Browser: inputs, brief, run, viral cards (V1–V2)

> `ATG` = `C:/Users/Glaresquare1/.claude/analyze-then-generate` · `PY` = `C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$ATG/scripts/atg.py"` (every call prints one JSON object on its last line: numbers, tables and records, never a verdict; run through Bash) · `RUN` = the run folder `ATG/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `ATG/reference/<file>/` (for the Viral-Browser playbook `<file>` is `viral-browser`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

Viral-Browser is the third Analyze sub-mode. The references are a **source of ideas**; nothing is generated: no Higgsfield generation tool, no model, no credits, no CapCut, no client assets, no change to the references folder. The run ends with the **next three products to sell**, each with a blueprint and a reference pack. `atg-start` sent you here as soon as the sub-mode was known; `$ARGUMENTS` are the command's arguments. At the end of each step print one short status line and store `T state --run RUN set stage=<…> next_step=<…>` (the `next_step` values make the run resumable). The market, price range, selling model, sales channel, tools, depth and exclusions live in `state.json → brief.*`.

Scripts gather, you decide: the `T` commands measure, extract, record, tabulate and calculate. Every reading of their numbers, every choice and every exception is yours, written down with its reason (`--by` / `--reason`, the bias log in `30-research/ranking.md`). The numbers in this phase (the 40 % niche share, the six gates, the evidence caps, the pack minimums) are rules of thumb: apply them with judgement, depart from them when the evidence says so, and write what you applied, what you set aside and why.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- viral-browser §0: `ATG/reference/viral-browser/010_0_precedence-and-hard-rules.md` (4.4 KB) (precedence and hard rules)
- viral-browser §1: `ATG/reference/viral-browser/020_1_the-team.md` (2.7 KB) (the team: the persona block)
- viral-browser §2: `ATG/reference/viral-browser/030_2_the-brief-inputs.md` (6.3 KB) (the brief)
- viral-browser §3.1: `ATG/reference/viral-browser/050_3.1_how-to-read.md` (1.6 KB)
- viral-browser §3.2: `ATG/reference/viral-browser/060_3.2_the-card.md` (13.3 KB) (the card)
- viral-browser §3.3: `ATG/reference/viral-browser/070_3.3_reading-the-product-s-price.md` (0.5 KB)
- viral-browser §3.5: `ATG/reference/viral-browser/090_3.5_scale-and-delegation.md` (0.8 KB)
- viral-browser §4.5: `ATG/reference/viral-browser/160_4.5_audience-and-mentality.md` (1.3 KB) (the mental shortcuts of the card's Mentality line)
- creative-direction §5.0: `ATG/reference/creative-direction/060_5.0_transfer-not-repetition-the-craf.md` (5.1 KB) (the craft kinds of the card's Craft line)
- viral-browser §13.1: `ATG/reference/viral-browser/470_13.1_viral-card-analysis-agent-use-th.md` (3.8 KB) (the card agent's prompt)
- *a baseline folder was given:*
  - viral-browser §3.4: `ATG/reference/viral-browser/080_3.4_baseline-cards-when-a-baseline-f.md` (0.5 KB)
- *a links file and "web plus my Chrome" (reference pages):*
  - viral-browser §3.6: `ATG/reference/viral-browser/100_3.6_reference-pages-optional-read-on.md` (1.0 KB)
- analysis-protocol §0: `ATG/reference/analysis-protocol/010_0_provenance-labels-use-everywhere.md` (0.6 KB) (provenance labels)
- analysis-protocol §1: `ATG/reference/analysis-protocol/020_1_inputs-per-video-produced-by-atg.md` (1.9 KB) (the per-video inputs, `T frames` and the sheet legend)
- analysis-protocol §2: `ATG/reference/analysis-protocol/030_2_reading-a-video-as-one-continuou.md` (6.5 KB) (item 4: the audio context)
- analysis-protocol §4: `ATG/reference/analysis-protocol/050_4_effectiveness-lenses-apply-those.md` (2.1 KB) (the effectiveness lenses)
- analysis-protocol §7: `ATG/reference/analysis-protocol/080_7_scale-and-delegation-2-analysis.md` (2.7 KB) (scale and delegation)

## Inputs and the run (the Start steps for Viral-Browser)

- **Viral-Browser** needs the references folder, offers four optional extras, and then asks the
  brief. Take what `$ARGUMENTS` already gives (`viral-browser <references-folder> [baseline <folder>]
  [market …] [price …] [depth …]`) and ask, in **one** plain-chat message, only for what is missing;
  then stop and wait:
  1. The **references folder** (videos are the primary content; a notes, links or metrics file
     in it is read: views, likes, comments, shares, saves, dates, links).
  2. *(Optional)* a **baseline folder**: comparable videos that did **not** spread (same niche
     and platform). It lets the run separate what the viral videos share from what all videos
     share (`viral-browser.md` §3.4).
  3. *(Optional)* **anything to exclude or respect**: categories you will not sell, regulated
     goods, size or weight limits, no batteries or liquids, a supplier or shipping limit, a
     product you already sell. Taken from the user only; never inferred.
  4. *(Optional)* **how you sell**: the sales channel(s) (own store, TikTok Shop, Amazon, …), the ad
     platform(s), the country of your selling company (the importer of record), the capital you
     can put into a first order and the shipping policy of the store (free to the customer / the
     customer pays a flat amount / free above a threshold). They decide the fee schedules, the
     restricted lists, the VAT and duty regime, the fulfilment cost in the cost basis and the MOQ
     capital figure (`T econ --moq` prints the capital at risk; you compare it with the limit);
     without them the defaults are an own store with paid social, the seller's own company as
     importer, an unknown capital limit and shipping free to the customer (the conservative
     reading, said in the cost basis).
  5. *(Optional)* `depth quick|standard|deep` (default standard) and `price` / `market` if not
     already in `$ARGUMENTS`.
  Say in the message: *"I will use the references only as ideas and generate nothing. I will
  ask four quick questions next: market, price range, how you sell, and whether I may use your
  Chrome for live pages."* Stop and wait for the reply.
  Then, after the paths are validated, ask the **brief** with one AskUserQuestion call holding
  only the questions `$ARGUMENTS` did not answer (`viral-browser.md` §2):
  - header "Market": "Where will you sell?" **US** / **EU** (then ask which countries in the
    next chat message, or say "all, lead countries chosen by the data") / **Global** ("Other":
    UK or a country list).
  - header "Price": "What retail price range (in the market's currency: USD for the US, EUR
    for the EU; type another currency under Other)?" **Impulse: up to 25** / **Core: 25 to 60**
    / **Premium: 60 to 150** ("Other": any range and currency).
  - header "Sell model": **Owned inventory** (bulk order, your own warehouse) /
    **Dropshipping** / **Print-on-demand** / **Digital product**.
  - header "Tools": **Web search and fetch only** (Recommended) / **Web plus my Chrome**
    (read-only pages: trend charts, marketplace pages, ad libraries).
  Hold the answers, and store them right after the run is created (below): `T state --run RUN set
  brief.market=… brief.price_min=… brief.price_max=… brief.currency=… brief.model=…
  brief.tools=web|chrome brief.depth=… brief.exclusions='…' brief.channel='…' brief.importer_country='…'
  brief.capital_limit=… brief.shipping='…'`.

Paths may arrive quoted, space-separated, dragged into the terminal, or one per line; validate every path (Glob/ls) and report any that do not exist.

**Create the run:** `T new-run --mode analyze --submode viral-browser --source "<refs folder>" [--baseline "<folder>"]` (it adds `30-research/` and `deliverables/`); keep `RUN` from the JSON; no model is stored and no `balance` is called (Viral-Browser spends no credits). Then store the held answers: `T state --run RUN set brief.market=… …` (the keys above).

## Steps

### V1. Brief, inventory and preprocessing
- The held answers are stored (above).
- Write `20-analysis/brief.md` from the answers (`viral-browser.md` §2): market and lead
  countries, currency and tax convention (US prices exclude sales tax, EU prices include VAT; fees
  are charged on the amount paid), the price band and the landed-cost ceiling, the selling model,
  the sales channel, ad platform, importer-of-record country and capital limit when given,
  exclusions, depth and tools, today's date, the selling windows of the next 120 days with the lead
  time, the Global per-market convention, and the production route.
- `T inventory "<refs folder>" --run RUN --as references`; with a baseline folder
  `T inventory "<baseline>" --run RUN --as baseline`.
- `T prep-all --run RUN --jobs 2` (and `T prep-all --run RUN --set baseline --jobs 2`); with more
  than about 3 minutes of video run it in the background and read the documents meanwhile
  (documents are authoritative requirements and are quoted, "we already sell X" included).
  **No `split-audio`:** the references folder is not touched.
- `T audio-context --run RUN --profile --second-pass` (and `--set baseline` with a baseline): the digest of every transcript and the sound
  numbers of every video, with no labels (`--second-pass` runs for every video in which no
  words were found; `viral-browser.md` §3.1, `analysis-protocol.md` §2 item 4). A video whose status is
  failed, missing or skipped (`without_a_transcript` in the JSON) is prepared again before the cards
  (`T prep-all --run RUN --only <V> --redo --whisper-model medium`).
- A metrics or links file becomes `20-analysis/metrics.md`: one row per video (views, likes,
  comments, shares, saves, followers, date, link, source), matched to the video ids by file name or
  link, and "not provided" where there is nothing. Never estimate a metric. **Reference pages**
  (only with a links file and "web plus my Chrome"): read each post page, read-only, up to
  `reference_pages_max[depth]` pages, for the counters, the caption, the creator's size, the date
  and the top comments in aggregate, and add them to `metrics.md` (`viral-browser.md` §3.6).
- Show the counts in one line. `next_step=cards`.

### V2. Viral cards
- One card per reference in `20-analysis/cards/<V>.md` and a light card per baseline video, as
  `viral-browser.md` §3: the product layer and the mechanism layer kept apart, the one-line `Facts:`
  JSON with `category` set to a short label for the niche of the product's main use (taken from the
  material; no script lists niches), `voice_type` (on-camera / voice-over / sung / rap / chant / none /
  mixed …: the card agent's judgement, since the transcriber cannot tell speech from lyrics),
  `shots_seen` (the agent's own shot count from the storyboard, beside the measured one) and
  `price_tier` only when the video shows or says a price, commerce signal versus attention-only,
  the ranked drivers of spread, the one-sentence mechanism, the transplant needs. Every card states
  "sheets seen n of n", and a sheet that did not display is read again before the card is written.
- Sound: for each reference run `T audio-profile --audio "<the original video>" --out
  10-media/<V>/audio-profile.json --transcript 10-media/<V>/transcript.json --cuts
  10-media/<V>/cuts.json` (the original video is the input here; nothing is written to the references
  folder). `T viral-stats` tabulates the numbers (tempo, beat strength, harmonic share, spectral
  flatness, audible non-speech share) and labels nothing; what each sound is, is the card agent's call.
  Every card carries the `Audio context:`, `Said:` and
  `Words and sound together:` lines (`viral-browser.md` §3.2); when the cards are written, run
  `T audio-context --run RUN --check --cards` (and with `--set baseline`): a completeness check only, which
  writes nothing; add what it lists before V3.
- Scale and delegation as protocol §7: up to 6 videos in this session; more, 1 analysis agent (2 over
  about 15 videos) with disjoint lists and the prompt of `viral-browser.md` §13.1.
- Merge the labels into `20-analysis/labels.md` and rewrite the Facts lines so one meaning has one
  label; set `creator_group` in them yourself (the main session), from the creator handle each card
  carries, in the format `g01`. Then build the **niche vocabulary** yourself from the data:
  `T niches propose --run RUN` tabulates the category labels in use with their counts, the niche each
  is recorded under and the `unmapped_labels`; you decide which labels are the same niche (no script
  compares labels or words) and record each decision with its reason:
  `T niches add --name "<niche>" --members "<label>,<label>" --by main --reason "…"` and
  `T niches map --label … --to … --by main --reason "…"` (a label that another niche held moves, and
  the move is noted; `viral-browser.md` §3.2; the full procedure is §5 item 3, read in `atg-vb-synthesis`). `next_step=synthesis`.

## Rules this phase owns (contract item 24)

24. **Viral-Browser: the references are a source of ideas, and the run generates nothing**
    (`reference/viral-browser.md`).
    - **No generation, no model, no assets.** No model is picked, no Higgsfield generation tool is
      called, no credits are spent, no CapCut project is written, no client assets are asked for,
      and the references folder is never modified (no `split-audio`).
    - **The brief is asked, not assumed:** the **market location** (US, EU, global or a country
      list) and the **price range** (the retail band and its currency) are always asked unless
      `$ARGUMENTS` gives them; the selling model and the research tools are asked with them; exclusions,
      constraints and how they sell (sales channel, ad platform, importer-of-record country, capital
      limit) are taken from the user's chat message (the optional questions of "Inputs and the run" above). Nothing about the
      user is inferred into an exclusion.
    - **The product layer and the mechanism layer are kept apart** in every card. The run learns
      *why* the videos spread (the hook, the visible proof, the emotion, the identity trigger, the
      price perception, the length, the engagement style), then looks for products that the same
      mechanism could carry, across the whole market.
    - **Three products, each data-backed:** researched in parallel by research agents, attacked by
      a red-team agent, rated on a rubric by a fresh blind agent, read by the main session against
      six gates of thumb (the reasoning written down), and delivered with a blueprint (the corpus's
      engagement style combined with what is trending now), the economics
      at the user's price, the compliance and logistics findings, a **reference pack** (the
      product's sourced specification: size, weight, material, texture, usage; and links to photos
      from several angles, none downloaded), a validation plan and the evidence that would
      change the call. "No product passes" is a valid result.
    - **Evidence discipline:** no number without a source and a retrieval date or a method; grades
      A–D; "unknown" never scores 3; the run is read-only on the world (no purchase, no login, no
      contact); the compliance, platform and IP screens are viability checks, never taste. The
      pipeline adds no exclusion of its own.

## Never (this phase)

- Viral-Browser: never generate anything. No model pick, no Higgsfield generation tool, no credits, no
  CapCut project, no request for client assets, no `split-audio` or any other change to the
  references folder; never start Create without the user's yes (item 26).
- Viral-Browser: never invent an exclusion. The user's exclusions come from the user alone, and the
  compliance, platform and IP screens are viability checks, never taste (`viral-browser.md` §0 rule 5).
  Never recommend fake scarcity, fake or undisclosed incentivised reviews, unprovable claims or any
  deceptive tactic in a blueprint (§0 rule 7).
- Never type a niche, category, product or brand name into a script or a config: the agents decide them from the data and record them with `T niches`.
- Never put a card's product layer into the mechanism layer, never estimate a metric, and never skip the "sheets seen n of n" statement of a card.

## Hand-off

`T state --run RUN set stage=cards-done next_step=synthesis next_skill=atg-vb-synthesis`, then invoke Skill `atg-vb-synthesis`.

After a compaction, or on `resume`, re-invoke the skill named in `RUN/state.json → next_skill`: its text may have been summarised away.
