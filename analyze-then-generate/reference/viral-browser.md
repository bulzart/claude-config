# Viral-Browser — read what made the references spread, then find the next three products to sell with the same approach

Analyze Mode's third sub-mode (command V1–V9). **The references folder is a source of ideas**, not material to edit (Recreate) or to imitate (Create). The run learns *why* the videos spread, then looks across the whole market, not only inside the references' niche, for the products that could spread the same way, researches them, and hands back **three data-backed picks**, each with a viral blueprint (the engagement style combined with what is trending now).

**Nothing is generated:** no model is picked, no Higgsfield generation tool is called, no credits are spent, no CapCut project is written, no client assets are asked for. The run reads, measures, searches and reasons, and writes files.

Load this with `analysis-protocol.md` (§0 provenance, §1–§2 how to read a video, §4 lenses, §7 scale and delegation), `creative-direction.md` (§1 roles, §3 audience model, §4 trend read, §5.0 craft versus subject) and, only at the continuation to Create (§11), `anomaly-catalog.md`.

Two things this mode must never do: **let the references' product niche decide the answer** (§5), and **state a number it did not get from a source or a method** (§0).

## 0. Precedence and hard rules

1. **The user's brief outranks every default here** (§2): market, price band, selling model, exclusions. Documents in the references folder (notes, product lists, "we already sell X") are authoritative requirements and are quoted.
2. **Provenance** as in the protocol: [E] evidence, [I] inference, [U] user instruction, [M] model knowledge. Research adds an **evidence grade** on every fact that reaches a score:

   | grade | what it is | counts toward a score and the gates |
   |---|---|---|
   | **A** | a primary or official source retrieved in this run (a regulator page, a platform policy page, a marketplace listing, a price page), or a measurement from the reference files | yes |
   | **B** | a reputable secondary source retrieved in this run (an industry article, an analytics page, a seller community's data) with its date | yes |
   | **C** | an estimate derived with its method and inputs written out (a margin from quoted prices, a slope from two readings) | yes, for `economics` only as a lone source; elsewhere it supports a grade A or B row |
   | **D** | unverified: a forum claim, an undated post, a single anonymous source, or model knowledge [M] | never; shown, never scored |
3. **No number without a source or a method.** A price, a sold count, a margin, a growth rate, a search-interest reading, a duty rate, a fee: each carries its source and retrieval date, or its method. A source that cannot be reached is written "unreachable"; a gap is written "unknown". Neither is filled by a guess, and "unknown" never scores 3 (§8).
4. **Retrieval dates.** Today's date comes from the environment. Everything fetched is stamped with it (`T evidence add --retrieved`).
5. **Viability screens, not taste.** The compliance, platform-policy and IP screens (§7) exist so the user does not buy a product that cannot legally be sold, shipped or advertised in their market. They are not preferences. The pipeline has no content rules of its own: a product is never dropped for being something a brand might dislike. **Exclusions come only from the user**; none is ever invented.
6. **The run is read-only on the world.** No purchase, no sign-up, no login, no message to a seller, no form submission, no scraping behind a login, no bypassing a paywall or a site's terms. Comments and reviews are read in aggregate (themes, counts); no personal data is collected and no handle appears in a deliverable except as a cited source.
7. **Honest persuasion.** The blueprint never recommends fake scarcity, fake countdowns, fake or incentivised-undisclosed reviews, unprovable claims or health and income promises. A claim in a hook must be one the evidence and the law allow in the market.
8. **Honest confidence.** Every pick carries a confidence grade and the evidence that would change the call. **"No product passes" is a valid result:** say which gate removed the candidates and what the user could relax (price band, market, exclusions), and never lower the bar silently.
9. **The creative layer and the research layer do not override each other.** Virality fit never overrides a compliance blocker or a margin gate; a margin never overrides a missing mechanism fit.
10. **Precedence of rules:** the user's brief > the user's documents > this reference > the config defaults. The config numbers are rules of thumb, editable in `config.json → viral_browser`.

## 1. The team

The pipeline acts, at once, as everything below, and says so to every agent it briefs. The persona block (copy it into each agent prompt):

> You are an expert short-form social media growth strategist (organic and paid), a direct-response product-selling specialist (offers, price psychology, unit economics, conversion, returns), a mass-cognition engineer (how a broad audience perceives, feels and decides in seconds), a trend analyst, a market and competitor researcher, a sourcing, logistics and compliance screener, a statistician who knows what a handful of videos can and cannot prove, and the red-team sceptic who tries to kill every idea before the user's money does. The user is about to put real money into a product. Work for that outcome: find products that will sell, not products that sound exciting; say "unknown" or "no" when that is the honest answer; never let how often something appears in the references stand in for evidence that people buy it.

| role | what it brings | where it acts |
|---|---|---|
| **Social-media growth strategist** | what stops a thumb, holds a viewer, earns a share, a save, a comment and a click; the first second, retention, the loop, the native look, platform mechanics | the viral cards (§3), the engagement style (§4.4), the blueprint (§9) |
| **Direct-response product seller** | what makes a stranger buy a product from a 20-second clip: problem awareness, proof, price anchoring, perceived value against price, objections, offer, returns | commerce signals (§3), economics (§7), the blueprint's offer and proof plan |
| **Mass-cognition engineer** | cognitive ease, the curiosity gap, pattern interrupt, identity and "that is me", social proof, loss aversion, effort minimisation, impulse thresholds, the share reflex | audience and mentality (§4.5), what hooked them (§4.6) |
| **Trend analyst** | formats, sounds and caption grammar; structural mechanisms that outlive a trend versus surface elements that date; freshness | the trend read (§4.8), the blueprint's trend layer |
| **Market and competitor researcher** | demand slope, sale signals, saturation, price spread, customer voice | research (§7) |
| **Sourcing, logistics and compliance screener** | landed cost, MOQ, lead time, duties and VAT, size and hazmat limits, product-safety regimes, platform policies, IP | research (§7), the gates (§8) |
| **Statistician** | sample size, survivorship, confounds, base rates, independence of evidence | the synthesis (§4.7), bias control (§5), scoring (§8) |
| **Red-team sceptic** | the strongest case against each top candidate | the red-team pass (§7.6) |
| **Creative director** | turns a mechanism into hooks, structure and tests for a specific product | the blueprint (§9) |

## 2. The brief (inputs)

| input | how it is obtained | default | used for |
|---|---|---|---|
| references folder | `$ARGUMENTS`, else plain chat | required | the idea source |
| **market location** | `AskUserQuestion` (US / EU / Global; "Other" for a country list) | always asked unless in `$ARGUMENTS` | where demand is measured, the price and VAT convention, the compliance regime, the language |
| **price range** | `AskUserQuestion` (the retail price band and its currency) | always asked unless in `$ARGUMENTS` | gate G1, economics, the perceived-value test |
| selling model | `AskUserQuestion`: owned inventory (bulk order, own warehouse) / dropshipping / print-on-demand / digital | asked | MOQ and capital at risk, lead time, returns, differentiation options |
| research tools | `AskUserQuestion`: web search and fetch only / web plus the user's Chrome (read-only pages) | web only | whether dynamic pages (trend charts, marketplace pages, ad libraries) can be read live |
| exclusions and constraints | plain chat, optional | none | gate G3 (categories to avoid, regulated goods, size or weight limits, battery-free, and so on) |
| how you sell | plain chat, optional: sales channel(s) (own store, TikTok Shop, Amazon, …), ad platform(s), the country of the selling company (the importer of record), the capital you can put into a first order | own store with paid social; importer = the seller's company; capital unknown | the platform fees and the restricted lists to screen against, the VAT and duty regime, the EU authorised-representative duty when the seller is outside the EU, and the MOQ sized against the capital limit (`T econ --capital-limit`) |
| baseline folder | optional | none | the contrast set (§3.4) |
| metrics or links file | optional, in or beside the references | none | engagement ratios, the platform, the date; with links and Chrome allowed, the reference-page pass (§3.6) |
| depth | `$ARGUMENTS` `quick` / `standard` / `deep` | `standard` | how many candidates and how many web calls (§7.2) |

Derived and written to `20-analysis/brief.md` at V1:
- **Currency and tax convention.** US prices exclude sales tax; EU consumer prices include VAT. `T econ --vat-pct` removes it, so a margin computed on a VAT-inclusive price is never overstated. Card and platform fees are charged on the amount paid (`--fees-on gross`, the default), and an ad platform reports return on ad spend on the amount paid unless its pixel is set otherwise, so read the break-even ROAS on that basis (`break_even_roas_gross`).
- **Returns.** The returns assumption is stated, never zero. In the EU a statutory withdrawal right applies to distance sales: check the rules of the lead countries and set the assumption from them and from the category's return-reason themes; run `T econ --stress` (retail -20 %, returns x2, landed +15 %) on every candidate that reaches the gates.
- **A Global market** has no single VAT or duty: run `T econ` once per market the user names (US with `--vat-pct 0`, each EU lead country with its rate) and let gate G1 use the **lowest** contribution of them.
- **Countries and language.** US: one regime, English. EU: 27 national markets with different languages and VAT rates; choose one to three lead countries by evidence (demand, language reach, logistics) and say why; "pan-EU" is a rollout order, not a market. Global: the **strictest** compliance of the markets named (at least US and EU) applies, the weakest-evidenced region sets the confidence, and each pick says which parts hold where.
- **Landed-cost ceiling** = net price ÷ markup (default 3, a rule of thumb for paid-social selling, not a law), from the band's lower and upper price.
- **Calendar.** Today's date, the next 120 days of selling windows that matter in the market (gifting seasons, sales events, holidays, religious and cultural calendars, weather), and the production plus shipping plus customs plus receiving lead time of the selling model. A product whose lead time misses its window is flagged in `timing`.
- **Tool reality.** `WebSearch` is US-only: **evidence for the EU or a global market must come from market-region sources** (trend tools with a region filter, country marketplace pages, region-filtered ad libraries). A pick for the EU backed only by US evidence carries a "market gap" flag and confidence no higher than medium.
- **Production route** (for `producibility`): the user's own filming with real samples, or AI video through Create; it decides how hard a demonstration is to make (§9).

## 3. The viral card (per reference, `20-analysis/cards/<V>.md`)

### 3.1 How to read

Follow `analysis-protocol.md` §1–§2: view every storyboard sheet in order beside `timeline.md`, densify the hook (0–3 s), the demonstration and the payoff (`T frames … --fps 15`), read the transcript against the lips. Then keep **two layers apart**, in every field:
- **Product layer**: what is sold or shown (category, form, size, material, price signal, branded or not).
- **Mechanism layer**: why people watched, felt, shared and wanted it (the hook, the visible change, the proof, the emotion, the identity, the price perception). This is what transfers to another product.

A card that mixes the two cannot support §5. "Pet gloves go viral" is a product statement; "an instant, silent, visible clean-up in the first three seconds at an impulse price" is a mechanism.

### 3.2 The card

```
# <V> — <file name> (<duration> s, <aspect>, <fps>) [E]
Facts: {"category":"<niche label>","product_form":"…","price_tier":"…","format":"…","creator_style":"…","creator_group":"g1","hook_type":"…","demo_type":"…","cta":"none|soft|hard","commerce_signal":"none|weak|strong","attention_only":true,"dependence_on_product":"low|medium|high","driver_primary":"craft|product|creator|trend|paid|bait|timing|unknown","claims_risk":"none|low|high","awareness_stage":"unaware|problem|solution|product|most","platform":"…"}
Format & style: <dynamic label from the material> · <organic UGC | produced | animation | screen recording | …> · <hands-only | talking head | voice-over | POV | observed | text-led> · language <…> [E/I]
Subject: <what the video is about, one sentence> [E]
Product layer: <what is sold or shown: category, form, size, material, price shown or implied, branded or unbranded, where it appears and for how long> [E/I]
Hook (0–1 s, 0–3 s): <what is seen, heard, read> · type <kind, not the instance> · curiosity gap <the question it opens> · first cut <t> · speech onset <t> [E/I]
Beat map: | t | beat | what happens | product on screen | text | audio | [E]
Time to wow: <seconds until the benefit is visible>; payoff <what, t>; loop <yes/no>; length <s>; pacing <median shot, cuts/10 s from video.md> [E]
Product use / demonstration: <how it is used or shown: transformation, before/after, hack, unboxing, comparison, tutorial, satisfying process, reaction, story, review…>; what proves it works; how legible the proof is [E/I]
Claims & proof: <explicit and implied claims; proof devices (numbers, counters, results, reviews, authority); any health, income or guarantee claim> [E/I]
Engagement mechanics: <retention devices; comment bait; share line; save or utility trigger; rewatch reason; questions asked; the call to action, as a kind> [E/I]
Audience: <who it speaks to: age band, gender cues, situation, interests, region and language cues> · awareness stage <unaware | problem-aware | solution-aware | product-aware | most aware> · the pain or desire it taps [I]
Mentality: <the mental shortcuts it uses (see §4.5); emotions at hook → middle → payoff; what got them hooked, in one line> [I]
Commerce signals: <shown or provided: price, shop tag or cart, "link in bio", "where to buy" or "need this" comments, view / like / comment / share / save counts, creator size, date, platform; "not provided"> · ratios where numbers exist [E]
Sound: <voice, music, effects; a trending sound? ; its role> (T audio-profile) [E/I]
Text: <roles, wording as kinds, position and timing> [E]
Trend & freshness: <format name; structural mechanism; surface elements: current / fading / dated> [I]
Drivers of spread (ranked): 1. … 2. … ; attention-only or commerce-proven; confidence [I]
Mechanism (one sentence, product-agnostic): <"This spread because …"> [I]
Product dependence: low | medium | high — <could a different kind of product carry the same mechanism? why> [I]
Transplant needs: <what any product needs for this mechanism to work: time to wow ≤ s, a visible change, silent-friendly, a price tier, a size, a single-location demo…> [I]
Producibility: <how hard a similar video is with a different product: real filming or AI generation; the physics, counts and openings involved (anomaly-catalog.md)> [I]
Create fields: <inserts (in-out, video or still); overlay text events; per handled object the part used, preparation step, contact point, hand; counts of multiples over time> [E]
Craft (kinds): <style | properties | approach | crafting | why it works> (creative-direction.md §5.0) [I]
Flags: <health or income claims, brands or IP visible, safety issues, minors, a regulated category> [E]
Confidence: <high | medium | low> — <what was hard to see or hear>
```

- **The `Facts:` line is JSON on one line, starting at the beginning of the line** (`T viral-stats` reads it). **`category` is the niche of the product's main use, written as a short label taken from the material** ("pet grooming", "kitchen storage": whatever the video shows; **no script lists, expects or knows any niche**, and a video that shows no product category says `non-product`). The niche-bias controls (§5) count niches, so one niche must not hide behind several spellings, and **the agents, not the scripts, decide which labels are the same niche**: after the first pass the main session reads the labels in use (`T niches propose --run RUN`), decides which belong together, and records the **niche vocabulary** as run data with `T niches add --name "<niche>" --members "<label>,<label>"` and `T niches map --label … --to …` (file `20-analysis/niche-vocabulary.json`). From then on `T viral-stats` and `T candidates` resolve every label through that vocabulary; a label no agent has placed is reported (and refused for a candidate) and goes back to an agent to decide. Every other label (`format`, `hook_type`, `demo_type`, the mechanisms) stays free text invented from the material, and **one meaning gets one label**: the main session merges synonyms in `20-analysis/labels.md` and rewrites the Facts lines. `product_form` is the physical or digital form; `creator_group` an anonymous id (`g1`, `g2`…) shared by videos of one creator, taken from file names or the metrics file, so creator concentration shows without handles. Leave a key out when the video does not show it.
- **Drivers of spread**, ranked, from this set (add others when the material shows them): the **craft** (hook and format), the **product** (novelty, need, wow), the **creator or account** (an existing audience), the **trend or sound** it rides, **paid amplification**, **controversy or engagement bait** ("is this real?"), **timing** (a season, an event) and luck. A driver that is not the product cannot be credited to a product later.
- **Attention versus commerce.** Entertainment can spread without anyone buying. `commerce_signal` is `strong` only with evidence of buying intent (a shop tag, a cart, "where do I buy" comments, a price and a link, a sold counter); `attention_only: true` marks a video that spread without such evidence. Attention-only videos still teach mechanisms; they never count as proof that a product sells.
- **Numbers.** When a metrics file exists, its figures go into `20-analysis/metrics.md` (one row per video: views, likes, comments, shares, saves, followers, post date, link, source) and the card cites them; ratios (shares per view, saves per view, comments per view) are computed, not eyeballed. A counter visible on screen is [E] with its frame time. Without numbers, write "not provided"; never estimate views from the look of the video.

### 3.3 Reading the product's price

A price seen, said or implied is recorded as a signal with its currency, not a fact about the market: "the video says it costs less than a coffee" is [E] about the video; the market price is researched (§7). Implied price tier (`impulse`, `mid`, `considered`) is an [I] label the synthesis defines from what the corpus shows.

### 3.4 Baseline cards (when a baseline folder exists)

A baseline video is a comparable video that did **not** spread (same niche, same platform, lower reach). It gets a **light card** in `cards/B<nn>.md`: the `Facts:` line plus format, hook (type and first cut), time to wow, product use, sound, text and engagement mechanics. The point is contrast: what the spreaders share that the non-spreaders do not (§4.7). A baseline never supplies ideas and never supplies candidates.

### 3.5 Scale and delegation

As the protocol's §7: up to six videos (or about three minutes) the main session reads everything; more, one analysis agent, two when there are over about fifteen, each with a disjoint list of ids (baseline cards included in the lists). The main session always writes the synthesis (§4). The agent prompt is §13.1.

### 3.6 Reference pages (optional, read-only)

A video file carries none of what happened around it. **When the user supplied a links file and chose "web plus my Chrome"**, the main session (never an agent) opens each reference's post page in the browser, up to `reference_pages_max[depth]` pages (quick 0, standard 10, deep 30), only to read: the visible counters (views, likes, comments, shares, saves), the caption and hashtags, the creator's follower count, the date, and the **top comments in aggregate** (counts of "where do I buy / link / price", "need this", objections, doubts, the words viewers use; no handles, no quotes beyond a few short anonymous phrases). The findings go into `20-analysis/metrics.md` and the cards' Commerce signals, Audience and Mentality lines, and mark a video `commerce_signal: strong` only on evidence of buying intent. This is the best evidence the run can get for engagement, the audience's mentality and "where do I buy"; without links or without Chrome it is skipped and the cards say "not provided".

## 4. Cross-video synthesis (V3)

### 4.1 Measure first

1. Merge the card labels (`labels.md`), fix the Facts lines, and record the **niche vocabulary** (`T niches propose`, then `add` / `map`; §3.2).
2. `T viral-stats --run RUN` (with a baseline, `--set both`) writes `20-analysis/corpus-stats.json` and `.md`: the length, pacing, first-cut, speech-onset, text-in-the-first-second, music, loop and loudness distributions, the shares, and the **concentration** of niche (the cards' `category`, resolved through the niche vocabulary), product form, creator group, format and hook type (top-1 share, top-2 share, HHI, the effective number of niches, and a **dominant** flag when one label reaches `niche_dominance_threshold`); a `category` label no agent has placed in the vocabulary is listed in the notes and counted as `unresolved:<label>`, which understates the concentration until an agent places it. Below ten videos it prints a small-sample note: read every share as an indication, not a rate.

### 4.2 Mechanism map — `20-analysis/mechanism-map.md`

Cluster the cards' mechanism sentences into **mechanisms** `M1, M2, …`, named from the material (never from a fixed list). For each:

| field | content |
|---|---|
| id and name | `M2 — instant visible change in under three seconds` |
| videos | which cards, k of n |
| strength | how many of those videos were commerce-proven, and, with metrics, their engagement ratios |
| what carries it | the hook type, the demonstration, the proof, the emotion, the identity trigger |
| **niche independence** | high / medium / low: could another kind of product carry it? The test: restate the mechanism for two unrelated product categories; if it still reads as a mechanism, it is independent |
| transplant needs | what a product must have (from the cards) |
| confounds | creator reach, a riding trend or sound, paid reach, bait, a season |

### 4.3 Hooks, length and pacing

From `corpus-stats` and the cards: the hook types that occur, the first-cut and speech-onset timing, the share with text in the first second, the length distribution and where the payoff lands, the median shot and cut rate, the sound role. State the **typical** profile and the **range**, not one video.

### 4.4 Engagement style — the approach

One template **per content family** (the families of `families.md`, §4.10) plus the composite across them, as kinds: the format, the structure shape (hook → proof → payoff → loop), the camera and edit behaviour, the text grammar, the sound role, the call-to-action kind, the way the viewer is addressed. A corpus is rarely one form, so the approach is not one template: each blueprint (§9) **chooses** the family template that fits its product's demonstration and says why, or a blend of two. Templates are written without any product, so they apply to any product that fits.

### 4.5 Audience and mentality

- **Who.** Segments, the situation they are in, the language and region cues, from the cards.
- **Awareness mix.** Share of videos aimed at unaware, problem-aware, solution-aware, product-aware, most-aware viewers. A corpus of unaware-stage videos sells novelty and demonstration; a most-aware one sells price and trust.
- **Triggers.** The emotions used at the hook, the middle and the payoff, and the **mass-thinking patterns** the material actually uses, inferred, never assumed: cognitive ease (understood in a fraction of a second), the curiosity gap, pattern interrupt, social proof, identity and "that is me", loss aversion and fear of missing out, effort minimisation ("a hack"), authority, price anchoring and perceived value above price, instant gratification and the satisfaction of a completed process, nostalgia, cuteness, status. Mark each [E] where a visible device shows it, otherwise [I].
- **Buying psychology.** The impulse threshold the corpus suggests (the price tiers of the commerce-proven videos), how the video makes the product feel worth more than it costs, what removes risk (a demonstration, a guarantee, a return promise, reviews), and which objections the comments raise.

### 4.6 What hooked them — the essence — `20-analysis/viral-essence.md`

At most twelve lines, product-free:
- **The essence**: three to five sentences on why this set spread ("an instant, silent, visible change that a stranger understands in two seconds, at a price that needs no deliberation, for a problem everyone has had").
- **The fit profile**: the **hard requirements** (a product that fails one is out), the **soft preferences** (each adds fit), and the **anti-patterns** (what does not fit this approach), each tied to the mechanism it comes from.
- **What we do not infer**: the claims the corpus cannot support (a size effect, a price effect, a causal claim from winners alone).

### 4.7 Confounds, survivorship and small samples

State plainly, in the synthesis: the references are winners only (survivorship), so shared features may be shared by all videos; the creator or the account may have carried the reach; entertainment is not demand; ten videos is a sample for ideas, not a statistic. With a baseline, list the **contrasts** from `corpus-stats` and name which shared features survive them. Each hypothesis in the mechanism map is graded: **supported** (a baseline contrast or several independent creators), **plausible** (consistent, untested) or **speculative** (one video).

### 4.8 Trend read

As `creative-direction.md` §4 (format names, structural mechanisms, surface elements marked current / fading / dated), with the research mode's allowance: **up to `viral_browser.trend_checks[depth]` bounded WebSearch queries** to confirm that the formats, sounds and caption conventions the references use are still current in the market, each finding dated. If the user connected a TikTok account in Higgsfield (`tiktok_accounts`), `tiktok_music_trending` (read-only, the market's country code) gives the commercially licensed trending tracks for the blueprint's sound plan; skip silently when no account is connected. A trend informs the blueprint; it never makes a product a candidate by itself.

### 4.9 Niche concentration and the bias plan

From `corpus-stats`: the category table, the dominant niche (or "none"), the creator concentration, and the **bias plan**: which of the controls in §5 apply (they always apply; the plan states how strongly, for example "dominant niche: pet, 7 of 10, so the defence note is mandatory for any pet pick and the pool must hold at least six other categories").

### 4.10 Files for a later Create

Write the standard `20-analysis/families.md`, `craft-sheet.md` (protocol §5 step 3b) and `project-profile.md` (domain, goal, audience model, trend read) from the same cards, so that the continuation to Create (§11) needs no re-analysis. The goal line for the profile is "product discovery, then awareness and product memory".

### 4.11 What the user sees

A short summary in chat: the essence in five lines; the fit profile; the niche-concentration line and the controls that follow; the mechanism list with k of n; the typical length and hook profile. Then `T state --run RUN set stage=analyzed next_step=candidates`.

## 5. Niche-bias control (the references' product niche must not decide the answer)

References usually come from one corner of the market. Left alone, three biases push the answer back into that corner: the **pool** (candidates are brainstormed from what the videos show), the **scoring** (a familiar category feels safer and more proven), and the **selection** (a bigger pool of one category fills the top three by sheer count). The controls, all mandatory:

1. **Layer separation (§3).** The mechanism is collected; the product is not. Candidates come from the mechanism's *transplant needs*, never from "more of what the videos show".
2. **Mechanism-first generation (§6).** The long list is built from mechanisms, problem scans and market feeds across many categories. The references' own products enter as **one source among five**, tagged `origin: reference`.
3. **Niches are data, decided by agents and enforced by the toolkit.** The controls count niches, so one niche must not hide behind several names ("pet tools", "pets", "dog care"). **No script knows or lists any niche**: the agents decide which labels in the data are one niche and record that **niche vocabulary** in `20-analysis/niche-vocabulary.json` (`T niches add` / `map`, starting from `T niches propose`). Every label on a card or a candidate must resolve through it (`T candidates add` refuses an unplaced label and sends it back to an agent), `T niches add` warns when a new niche shares many words with an existing one, and `pool` flags look-alike niches in use, so a split is a visible, recorded decision and never an accident.
4. **Pool balance, enforced.** The long list is checked with `T candidates pool` (at least `min_categories_in_pool`, 6, niches; none above `max_pool_share_per_category`, 40 %, of the pool; at most half from the references' own products), and **the shortlist that is actually researched is checked again, by the only command that can start research**: `T candidates shortlist --ids …` refuses a shortlist that fails the balance (a shortlist of 6 needs at least 3 niches, of 9 at least 5, of 12 at least 6), and `T evidence add` refuses evidence for a candidate that is not shortlisted. A failing set is repaired by adding candidates from other niches, never by dropping the dominant one; passing `--force` needs a stated `--reason`, which goes in the bias log.
5. **Origin-blind evidence and scoring, by a fresh agent.** The ledger knows each candidate's origin; **dossiers and scoring never mention it**. Research agents are not told where a candidate came from. The main session built the pool and read the cards, so **it does not score**: a **fresh scoring agent** (§13.4) receives only `T candidates show --blind`, the evidence, the dossiers, the brief and the essence and fit profile (for `fit` only), and writes the scores. Reference-derived rows appear to it as "not independent: not counted".
6. **Independent, directional evidence.** The references prove nothing about the market. Evidence rows carry a **signal** (positive, negative, mixed: which way the fact points for selling the product in that lane) and an independence flag; an independent grade A or B row needs a URL. A criterion in `independent_criteria` (demand, commercial, competition, economics, compliance) with **no positive independent** grade A or B row (grade C for economics) is **capped at 2**; one whose negative rows match or outnumber the positive ones is capped at 3 when scored 4 or 5. `T candidates rank` applies both and prints raw against capped scores.
7. **Gates and floors (§8).** To be a pick a candidate needs positive independent grade A or B evidence from at least two distinct sources across the demand, commercial and competition lanes (one of them commercial), a supported compliance status, an economics row, and a floor of 3 on demand, commercial, economics, compliance and fit **after the cap**. A product whose rows say demand fell, nothing sells and the price war has begun cannot be carried by high scores elsewhere.
8. **Per-niche and per-type caps.** At most `max_picks_per_category` (2) picks share one niche, and no two picks share a product type (the `type` an agent assigned; an exact match blocks, and `rank` warns when two picks' types share many words so that an agent confirms they differ or gives them one type). A third pick from the same niche goes to the next-best candidate of another and appears among the runner-ups as "category cap". These caps are a deliberate diversification safeguard on the three-place table, not an exclusion of any niche (see below); the user can relax them in the config.
9. **The defence note and the red team come before the verdict.** Every pick from the dominant niche carries a written defence, its independent evidence side by side with the best outside-niche alternative (independent score, evidence rows, contribution margin, saturation) and why it still wins (`T candidates set --defence`); every pick carries a red-team verdict (`--redteam`). **`T candidates rank --apply` refuses until both exist** (`--force --reason` overrides, and the reason is printed in the bias log), so a defence can still demote a pick.
10. **Reference-gravity tests (ablations).** `rank` reports whether the picks change (a) when reference-derived evidence is allowed to count (`ablation_reference_evidence_changed`: the independence rules, not the references, decided) and (b) when the `fit` criterion, which is derived from the references, is removed (`ablation_no_fit_changed`). If either changes the picks, say so in the bias log and the report.
11. **Transparency.** `30-research/bias-log.md` records, as the run goes: the niche-concentration line, the pool and shortlist checks and repairs (and any forced override with its reason), the caps applied, the ablation results and the defence notes. The report prints it.

**What bias control does not do:** it does not exclude the dominant niche. A pet, kitchen or any other product from the references' own niche that the market data backs stays eligible, may win, and may take two of the three places. The evidence rules demand *independent proof*, not a quota. The pool and pick limits (40 % of a pool, two picks per niche) are the only quota-like parts: they keep the long list broad and the three-place answer diversified, they never stop a data-backed product from competing, and the user can relax them (`max_pool_share_per_category`, `max_picks_per_category`) if they want the data alone to decide.

**Worked example (illustrative only; the labels come from the material, never from this file).** Seven of ten references show pet tools: a hair-removal glove, a bowl insert, a nail grinder. Read at the product layer, the corpus says "pet tools sell". Read at the mechanism layer it says: **M1** "a mess disappears on camera in under three seconds, hands only, no voice" (6 of 10 videos, niche independence high) and **M2** "a hated chore becomes satisfying" (4 of 10, high); transplant needs: a visible before and after within three seconds, silent-friendly, an impulse price, a one-location demonstration. Candidates are then drawn by those needs across the market: a lint remover, a stain-lifting stick, a window-track cleaner, a drain-hair catcher, a grout pen, and, from the references, the hair-removal glove and the nail grinder. The glove now competes with the others on *independent* demand, commercial, competition and economics evidence. It wins only if that evidence, not its presence in the references, beats theirs; if it wins it is a data-backed pet product and stays, with its defence note. If the lint remover wins instead, the answer was found by the mechanism, in a niche the videos never showed.

## 6. Candidate generation (V4)

**Goal:** twelve to twenty specific candidates (`viral_browser.long_list`), then a researched shortlist (`researched_candidates[depth]`: 6 / 9 / 12).

**A candidate is a product, not a category.** It is specific enough that a supplier search or a marketplace search returns it: a name, the defining features, size or material, the use, the variants, and two or three example listings. "Pet products" is a category; "quiet ceramic-filter pet water fountain, 2 L" is a candidate. `T candidates add` requires a name, a definition, a **category** (the product's niche: a label that resolves through the niche vocabulary, §5 item 3; an unplaced label is refused and goes back to an agent to map or add), a **type** (the product type, for the one-per-type rule) and an **origin**; nothing defaults. `--from-json <file>` takes a list of objects with those fields plus `origin_note`, `mechanisms` (a list of ids such as `["M1","M3"]`) and `note`; it validates every entry first and adds them all in one locked write or none. **The name and the definition never mention the references or a video id** (they are read by the research agents and by the scorer; the origin lives only in `origin` and `origin_note`, which `--blind` hides).

**Five sources, all used** (`origin`):

| source | how |
|---|---|
| `mechanism` | take each high-independence mechanism's transplant needs and ask which products, in at least six unrelated categories, meet them. This is the main source |
| `problem-scan` | list universal frictions the audience model names (cleaning, organising, cooking, travelling, sleeping, commuting, grooming, repairing, gifting, working from a desk) and find the products that remove each with a visible demonstration |
| `trend-feed` | what market feeds show rising now in the user's market (trend tools, marketplace movers, shop charts, ad libraries, community threads): bounded `WebSearch` and the user's browser when allowed. Candidates found here are screened by the same mechanism test, so a trending product that cannot be demonstrated does not enter |
| `variant` | an improved, differentiated, safer or better-targeted version of a product the references or the feeds show (a bundle, a size, a material, a use-case angle) |
| `reference` | the references' own products, tagged so the pool balance can see them. They enter once each, at the same footing as the others |

**Screens before research** (a cheap pass with `candidates set --status eliminated --by "<gate>"` for each removal): the price band is feasible (a plausible retail price inside the band, a plausible landed cost under the ceiling, a variant or bundle that fits counts); no obvious market blocker (a regulated category the user cannot sell in that market, a shipping prohibition); not in the user's exclusions; the mechanism test (it can be demonstrated, honestly, in the time the corpus shows). A screen removes a candidate only with a stated reason.

Then `T candidates pool` on the long list (§5 item 4) and repair it, choose the shortlist, and start research with **`T candidates shortlist --run RUN --ids C01,C02,…`**, which re-checks the balance on exactly those candidates, refuses a failing set (`--force --reason "<why>"` overrides and is logged) and marks them `researching`. Show the user one table: candidate, niche, origin, and the one-line reason it is in the pool; the origin is shown to the user and hidden from the research (§5 item 5).

## 7. Research protocol (V5)

### 7.1 Who does what

- **Research agents** (up to `max_research_agents`, 3; `subagent_type: general-purpose`, `run_in_background: true`): each takes a **disjoint** list of shortlisted candidates (`researching`) and researches every lane (§7.3) for each, within the budget (§7.2). They use `WebSearch` and `WebFetch` only, register evidence rows with `T evidence add`, run `T econ … --cand C## --run RUN` for the economics, write one **origin-blind dossier** per candidate (§7.7), and queue the pages they could not read in their own file (§7.5). They **do not score, rank, eliminate or recommend** (a lane that settles a gate is reported in their final line; the main session eliminates), are not told where a candidate came from, and never cite the references.
- **The main session** processes the browser queue when the user allowed their Chrome (§7.5). It does not edit the dossiers and **does not score** (§8.2).
- **One scoring agent** scores the researched candidates blind (§8.2, prompt §13.4), and a fresh one revisits the criteria the red team names.
- **One red-team agent** attacks the red-team targets (§7.6).
- **Fallback when an agent lacks a tool.** If a background agent reports that it was denied `WebSearch`, `WebFetch` or `Bash`, do not retry it: research that candidate in the main session within the same budget, or report the lane "unreachable".
- **Backfill wave.** If fewer than `picks` candidates pass the gates, run **one** more research wave before reporting a shortfall: shortlist the next best `backfill_researched[depth]` candidates from the long list (the pool check applies), research them the same way, score them blind and re-rank. Only then report fewer than three (§8.6).
- No agent calls Higgsfield or CapCut, spawns agents, uses the Workflow tool, asks a question, logs in anywhere, buys anything or contacts anyone. They report blockers (a tool failure, rate limits) and stop.

### 7.2 Depth

| | quick | standard | deep |
|---|---|---|---|
| candidates researched | 6 | 9 | 12 |
| web calls per candidate (a `WebSearch` or a `WebFetch` each) | 8 | 16 | 30 |
| trend checks on the references' formats (§4.8) | 3 | 6 | 12 |
| browser pages per candidate (§7.5, only when allowed; EU and global evidence mostly needs them) | 2 | 3 | 5 |
| reference pages (§3.6, only with a links file and Chrome) | 0 | 10 | 30 |
| backfill candidates (§7.1, one wave) | 3 | 5 | 6 |
| red-team calls per candidate (red-team targets) | 8 | 8 | 8 |
| trend checks per pick, for the blueprint (§9 item 7) | 2 | 4 | 8 |
| verification re-fetches (§10.4) | 12 | 12 | 12 |

A lane that settles a gate early (a prohibited product, a margin that cannot work) ends the candidate's research: the agent reports it, the main session marks the candidate `eliminated --by <gate>`, and the rest of the budget is spent nowhere. `WebSearch` modes: `standard` for lookups; `extended` only when a standard result is thin or stale, or for fresh prices and availability and for niche facts.

### 7.3 The lanes

Every lane yields three to eight evidence rows, a verdict (green / amber / red / unknown) and the unknowns. The sources are **where to look, not a checklist**: availability changes, no source is mandatory, and an unreachable one is recorded as such.

| lane (criterion) | the question | where to look | record | red flags |
|---|---|---|---|---|
| **demand** (`demand`) | is interest rising, and is it early or late? | trend tools with a region and a time filter (12 months and 5 years), the platform's own trend and top-products pages, marketplace movers and new-release lists, community threads, video search counts | the slope, the stage (emerging / rising / peak / plateau / declining), seasonality, the region | a spike already falling; a seasonal product read as evergreen; interest only in a region outside the market |
| **commercial** (`commercial`) | is anyone paying? | marketplace listings (sold-in-the-last-month badges, ranks, review counts and their growth), shop pages (sold counts), supplier-site order counts, ad libraries (how many advertisers, how long each ad has run), price pages | the signals, with the market they are from | views without any buying signal; sold counts from a different market; one advertiser only |
| **competition** (`competition`) | how crowded, and is there room? | marketplace and search-result pages, price spreads, seller and listing counts, brand presence, review quality, ad libraries | seller count, price spread and trend, dominant brands, the **differentiation angles** open (variant, bundle, material, size, brand, use-case, quality) | many identical listings with collapsing prices; a dominant brand; no credible angle |
| **economics** (`economics`) | does it make money at the band's price? | supplier listings and price tiers at a realistic quantity, freight and customs sources, official VAT and duty tables, the platform's fee schedule, payment fees, fulfilment quotes, return-rate sources for the category | the inputs (each with its source), then `T econ` (grade C) | landed cost over the ceiling; contribution under the gate; MOQ capital out of proportion; duty or VAT forgotten |
| **compliance** (`compliance`) | can it be legally sold, shipped and advertised in the market? | the market's official product-safety regime (EU: the general product safety regulation, CE and the product's directive or standard, labelling and the EU responsible-person duty, batteries, waste, packaging, cosmetics, food contact, toys; US: CPSC and its child-product rules, FDA for food, cosmetics and devices, FCC for radio and electronics, state labelling), the shop and ad platforms' restricted and prohibited lists, trademark and design-patent databases (a name, a shape, a look-alike), advertising-claims rules | what applies, the certification or labelling route and its cost, the platform status, an IP check, the claims you may not make; **official sources first** | a regulated category without a route; a platform prohibition; an IP conflict; a claim the product depends on that the law forbids |
| **logistics** (`logistics`) | what does moving it cost and risk? | the listing's size and weight, carrier restrictions, return-reason themes in 1–3 star reviews | size, weight, fragility, battery / liquid / magnet / aerosol / hazmat, shelf life, size or fit variants | bulky; fragile; batteries or liquids in air freight; fit-dependent (high returns) |
| **voice** (feeds `fit`, `competition`, `logistics`) | what do buyers say? | review pages (the 1–3 star ones especially), community threads, comment sections | themes with counts: praise, failure modes, unmet needs, the words buyers use; no handles | the same defect in many reviews; durability complaints; "not as shown" |
| **content** (`fit`, `producibility`) | can the benefit be shown honestly, in seconds, in one place? | comparable demonstrations (what they show, how long, how they hook), the fit profile (§4.6) | demonstration time, the visible change, silent-friendliness, filming set-up, comparable videos and their reach | the benefit cannot be seen; needs a long explanation; physics-heavy (liquids, counts, many hands) |
| **timing** (`timing`) | does the window fit the lead time? | the calendar in `brief.md`, supplier lead times, shipping and customs time, factory-holiday dates, seasonal sales curves | the window, the lead time, the gap | the window closes before arrival; a supply shutdown in the lead time; a product that peaks and falls within weeks |

Unit economics inputs (the `economics` lane): the retail price inside the band (what comparable products actually charge in the market, with VAT as the market shows it), the landed cost per unit at the quantity the selling model implies (product price tier + freight + duty + any non-recoverable import tax), fulfilment per order, the platform and payment fees from the schedules of the user's sales channel and processor (`brief.md`), the return rate as a **stated assumption** with its source or "assumption" (never zero; the EU withdrawal right, §2), and the MOQ against the user's capital limit. Then `T econ --retail … --vat-pct … --landed … --fulfil … --platform-fee-pct … --payment-fee-pct … --payment-fixed … --returns-pct … --return-cost … --moq … --capital-limit … --stress --currency … --market … --cand C## --run RUN`: with `--cand` it writes the contribution into the candidate **and registers the grade C economics row itself**, so the typed number can never stand without its evidence. For a Global market run it once per market named and keep the lowest contribution. The scoring agent sets `--price-fit yes|variant|no`.

### 7.4 Rules of evidence

- One claim per row; the number itself in `--value` with its `--unit`; `--source` is the URL (or the method for a grade C row); `--retrieved` today; `--market` the market the figure is from.
- **`--signal positive|negative|mixed` is required**: which way the fact points for selling *this product* in that lane (rising demand, a buying signal, room to differentiate, a margin that works, a clean compliance route = positive; falling interest, no sales, a price war, a blocker = negative). Negative rows are as valuable as positive ones: they are what the scorer and the red team need, and `rank` counts both.
- **`--independent yes|no` is required, and research agents always pass `yes`**: they never see or cite the references. A row derived from the reference videos is registered only by the main session, with `no` (it is shown, never counted). **An independent grade A or B row needs a URL** as its source; a figure you cannot link is grade C with its method, or grade D.
- **Distinct sources.** Gate G4 counts distinct source domains: two rows from one page are one source.
- A figure that conflicts with another source is registered twice and flagged in the dossier; the lower-quality one is not silently dropped.
- Grade D rows are kept to show what was heard and not verified.
- Stale evidence: a readable date older than twelve months on a fast-moving measure (interest, ads, prices, fees) is graded one step down.
- Quote sparingly; never copy paragraphs of a page; never fabricate a URL, a quote or a number.

### 7.5 The browser queue

Dynamic pages (trend charts, marketplace pages, ad libraries, shop pages) often cannot be read by `WebFetch`. Each agent lists what it could not read in **its own file per candidate**, `30-research/queue-<C>.md` (several agents write at once, so one shared file would lose lines), one line each: `- <lane> | <URL> | <what to read>`. **Only when the user chose "web plus my Chrome"**, the main session loads the browser tools (`ToolSearch`), calls `tabs_context_mcp` first, opens a new tab per page, reads it (`get_page_text` or `read_page`; filters and a region selector may be set; nothing is submitted, no login, no purchase, no dialog-triggering control), registers the evidence rows (`--independent yes`), and stops at `browser_pages_per_candidate[depth]` pages per candidate (EU and global evidence depends on these pages, since `WebSearch` is US-only). Pages beyond the cap, or with Chrome off, stay "unreachable" in the dossier and cap that lane's confidence.

### 7.6 The red-team pass

After the scoring (§8.4) `T candidates rank --provisional` prints the **red-team targets**: the gated, capped selection (the candidates that would be picks) **plus the next two**, so the final picks are the ones attacked, not a pre-gate top five. One red-team agent takes them. For each: "assume this product fails within ninety days; what is the most likely cause?" It looks for the strongest evidence of: saturation or price collapse, margin collapse (a cost it missed, a fee, a return rate), a compliance or platform block, a fad already peaking, a defect pattern in reviews, an IP conflict. Findings are registered as evidence rows (`--signal negative`, `--independent yes`) and summarised in `30-research/redteam.md`: per candidate, the attacks tried, the strongest counter-evidence, the residual risk, and a verdict (**survives**, **weakened**, **fails**) naming the criteria whose scores to revisit. The main session records the verdict (`T candidates set --redteam …`), and a candidate that **fails** is eliminated with the red team's evidence ids as the reason. After the rescoring and the elimination, run `--provisional` again: **any new entrant to the targets is red-teamed too** (repeat until no target lacks a verdict; at most two rounds). `rank --apply` refuses a pick without a verdict.

### 7.7 The dossier — `30-research/<C>.md` (origin-blind)

```
# <C> — <product name>
Definition: <specific product: features, size or material, variants>; example listings: <URL>, <URL>
Market checked: <market, lead countries> · retail price band check: typical retail <range> <currency> (<EV ids>)
Lane verdicts: demand <green|amber|red|unknown> — <one line>; commercial …; competition …; economics …; compliance …; logistics …; voice …; content …; timing …
Demand & trend: <slope, stage, seasonality; EV ids>
Commercial proof: <sale signals, ad longevity and advertiser count, review velocity; EV ids>
Competition & angle: <sellers, price spread, brands, open differentiation angles, saturation; EV ids>
Economics: <inputs with sources> → T econ: contribution <…> (<…> % of net), break-even CPA <…>, break-even ROAS <…>, MOQ capital <…>; EV ids
Compliance & policy: <regime and what applies, certification or labelling route, platform status, IP check, claims limits; official sources; EV ids>
Logistics & returns: <size, weight, fragility, battery / liquid / magnet / hazmat, shelf life, variants; EV ids>
Customer voice: <themes with counts: praise, failure modes, unmet needs; EV ids>
Content fit: <can the benefit be shown in one place in seconds; comparable demonstrations; EV ids>
Timing: <window, lead time, gap, supply risks; EV ids>
Unknowns and unreachable: <list>
Browser queue: <entries added>
```

It never states or hints where the candidate came from, and never mentions the reference videos.

## 8. Scoring, gates and selection (V6)

### 8.1 The rubric (weights in `config.json → viral_browser.rubric`, summing to 100)

Each criterion is scored 1–5 (2 and 4 sit between the anchors). **Unknown is not 3:** a criterion without evidence scores 1 or 2.

| criterion (weight) | 5 | 3 | 1 |
|---|---|---|---|
| **demand** (15) | interest has risen for three months or more and is not at a peak, two independent sources agree, in the target market | flat or mixed; or one source | falling, peaked, or no data |
| **commercial** (15) | two or more independent sale signals in the market (sold counts or ranks, review growth, ads running 30+ days from several advertisers) | one signal, or an indirect one | none: attention without buying evidence |
| **fit** (20) | meets every hard requirement of the fit profile and at least 70 % of the soft ones | meets the hard ones and a few soft ones | fails a hard requirement (also gate G5) |
| **economics** (15) | contribution of 45 % of net revenue or more at the band's price after landed cost, fulfilment, fees and returns; modest MOQ capital | 25–35 % | under 15 %, or unknown |
| **competition** (10) | few established sellers, no price war, a credible differentiation angle | crowded, but an angle exists | commoditised: identical listings, collapsing prices, no angle |
| **compliance** (10) | no regime beyond general product safety; not restricted by the shop or ad platforms; no IP conflict | a certification or labelling route is needed and its cost and route are known | restricted or prohibited, or unclear and high-risk |
| **logistics** (5) | small, light, robust, no battery / liquid / magnet / aerosol, one variant, low expected returns | some breakage or size variance | fragile, bulky, hazmat or size-variant |
| **timing** (5) | evergreen, or rising with a window ahead that the lead time reaches | seasonal with a tight fit | the spike has peaked, or the window closes before arrival |
| **producibility** (5) | the benefit shows in one location with hands and one object; no complex physics | feasible with care (liquids, two hands, counts) | hard to film or generate believably (anomaly-catalog-heavy) |

The anchors are guides, not formulas; the evidence decides. The economics percentages are heuristics for paid-social selling.

### 8.2 Scoring procedure

1. **A fresh scoring agent scores, not the main session** (§5 item 5; prompt §13.4). The main session built the pool, saw the origins and wrote the mechanism map, so it is the one reader that cannot be blind. The scoring agent receives `T candidates show --run RUN --id C## --blind`, the candidate's evidence (`T evidence list`), its dossier, `20-analysis/brief.md` (market, price band, exclusions) and `viral-essence.md` (for `fit` only). It never opens the cards, the mechanism map or the origin.
2. `T candidates score --run RUN --id C## --scores demand=4,commercial=3,fit=5,… --refs "demand=EV004+EV005 commercial=EV009" --confidence high|medium|low --note "<one line>"`. Every score names the evidence rows behind it (ids that do not exist for the candidate are rejected); the command prints the criteria that still have no positive independent row, which `rank` will cap.
3. Set the gate fields from the evidence: `T candidates set --id C## --price-fit yes|variant|no --compliance clear|resolved|open|unknown --excluded yes|no`. The contribution is not typed: it comes from `T econ … --cand C##` (§7.3). **`clear` or `resolved` needs a positive independent grade A or B compliance row behind it**, and a `clear` status that sits beside negative compliance rows is rejected by the gate: use `resolved` with the route, or `open`.
4. **Confidence:** high = two or more independent grade A rows in each of demand and commercial and a region match; medium = grade A or B rows in most lanes, a gap noted; low = thin or conflicting evidence, unreachable key sources, or a market gap.

### 8.3 The gates

A candidate is **eligible to be a pick** only if it passes all six; a failed gate is printed with its reason by `T candidates rank`. The red team's `fails` verdict also removes a candidate.

| gate | rule |
|---|---|
| **G1** price and economics | a retail price (or a variant or bundle) inside the user's band, a contribution at or above `min_contribution_pct` (25 % of net revenue) that **came from `T econ --cand`**, and an independent economics evidence row behind it |
| **G2** compliance | status `clear` or `resolved` (`open` and `unknown` fail), **and** at least one positive independent grade A or B compliance row; `clear` beside negative compliance rows fails |
| **G3** exclusions | not in the user's exclusions |
| **G4** independent evidence | positive independent grade A or B rows across the demand, commercial and competition lanes from at least `min_independent_evidence` (2) **distinct sources**, one of them in the commercial lane |
| **G5** floors | after the evidence cap, `demand`, `commercial`, `economics`, `compliance` and `fit` each at least 3 (`gates.min_scores`): high scores elsewhere never carry a candidate whose evidence says the opposite |
| **G6** confidence | at least `min_confidence_for_pick` (medium) |

### 8.4 Procedure

1. The scoring agent scores every researched candidate (§8.2).
2. `T candidates rank --run RUN --provisional`: the **red-team targets**, the gated, capped, niche-limited selection plus the next two, with the gate failures of the rest.
3. The red team (§7.6) attacks the targets; record each verdict (`T candidates set --id C## --redteam survives|weakened|fails`), eliminate the ones that fail, and have a fresh scoring agent revisit only the criteria the red team names. Run `--provisional` again until every target has a verdict (at most two rounds).
4. `T candidates rank --run RUN`: read the picks, the blockers and the two ablation results; write the **defence note** for every pick in the dominant niche (`T candidates set --id C## --defence "…"`; if no honest defence exists, demote the pick by eliminating it with the reason, and rank again); complete `bias-log.md` (§5 item 11).
5. `T candidates rank --run RUN --apply`: it **refuses** while a pick lacks a red-team verdict or a dominant-niche pick lacks its defence (`--force --reason` overrides and is printed); on success it writes `30-research/ranking.md` and `.json` and marks `picked` / `runner-up`.
6. Show the user the ranking table.

### 8.5 Selection rules

- Order by the **capped** score; ties go to more independent rows, then higher contribution.
- At most `max_picks_per_category` (2) per niche and one per product type (an exact `type` match blocks; look-alike types are warned about); runner-ups (three) show their reason (`category cap`, or a lower independent score).
- After the picks are fixed, give each a **role** from the data, never forced: *safest* (highest confidence and margin), *highest upside* (strongest demand slope with a manageable gap) or *fastest to test* (lowest capital at risk and shortest lead time).
- A role never changes a pick.

### 8.6 Fewer than three

If fewer than three pass, first run the **backfill wave** (§7.1: one more wave from the long list, with the pool check). If it still falls short, deliver those that pass and say which gate removed each of the others and what the user could relax (the price band, the market, the exclusions, the capital limit). A near miss may be listed as **watch** with the one thing that would qualify it. Never lower a gate to fill the table. For a Global market the gates use the weakest market named: G1 the lowest contribution, G2 the strictest compliance, G4 evidence from each region that is claimed.

## 9. The viral blueprint (V7), per pick

The blueprint is **the approach**: the corpus's engagement style, fitted to this product, combined with what is trending now. It is a plan to produce and test content, not a script to shoot. Every pick gets all of:

1. **Source mechanisms and why they transfer.** Which mechanisms (M#) and which clauses of the essence this product satisfies, which family template of §4.4 it follows (or which two it blends, and why), and what changes for it (the demonstration, the proof, the price perception).
2. **Audience and promise.** Who, in which situation, at which awareness stage; the one-sentence promise; the objections and the honest answer to each.
3. **Five hooks.** One line each: the first-second visual, the on-screen line (a kind of line, not final copy), the sound idea, the hook type (from the corpus). No claim the evidence or the law does not allow.
4. **Structure and timing.** Length target and range, hook within `<s>`, time to wow `<s>`, payoff at `<s>`, the loop, from the corpus's measured profile; the beat template.
5. **Demonstration and proof.** What to show, from how many set-ups, what to prove (a visible change, a measurement, a comparison), what the samples and props are.
6. **Engagement plan.** The share line a viewer would type, the save or utility trigger, an honest comment prompt, the call-to-action kind and where it sits for the chosen platform.
7. **Trend layer, researched per pick.** The references' trend read (§4.8) says what was current in the corpus; it does not say what is current in *this product's* niche and market today. For each pick run a bounded **trend pass** (up to `pick_trend_checks[depth]` searches or browser pages, dated): the formats, hooks, caption grammar and sounds now used in videos for products of this kind in the market, which are rising and which are worn out; plus, once, `tiktok_music_trending` for the market's country code when a TikTok account is connected. The blueprint then names the current formats and hooks to use, the licensed-sound options for a business account in the market, and the dated elements to avoid.
8. **Offer and price framing** inside the user's band: price anchoring, a bundle, a guarantee, shipping message, the perceived-value argument, and the claims wording the market allows.
9. **Test plan** (suggestions, not benchmarks): a matrix of angles and hooks; what to watch (three-second view rate, hold, shares and saves per view, click-through, cost per order against the break-even CPA from `econ`); a decision rule with honest sample sizes; what would make you stop.
10. **Production route and producibility.** Real filming with the samples, or AI video through Create (then the anomaly catalog applies: counts, openings, size reckoning, liquids, solidity) and the assets to obtain before Create can run.
11. **Validation before bulk inventory** (owned-inventory model): order samples first; make content from them; a small test or pre-sale where the platforms allow; a small first batch sized to the capital at risk; the go / no-go rule.
12. **What would change the call.** The two or three facts that, if found, would demote the pick.

## 10. Deliverables (V7–V8)

### 10.1 Files, all in `<RUN>/deliverables/`

| file | content |
|---|---|
| `viral-browser-report.md` | the whole result (§10.2) |
| `product-01.md`, `product-02.md`, `product-03.md` | the pick's full dossier (the economics table, the lane findings, the red-team findings) and its blueprint (§9) |
| `evidence.md` | the evidence ledger rendered with `T evidence list --run RUN --out <RUN>/deliverables/evidence.md`: claim, value, grade, signal, independence, market, date, source |
| `create-handoff.md` | for each pick: the definition, audience model, goal line, trend read, the fit profile, the assets Create needs (samples, a contents shot, real dimensions) and the anomaly-catalog risks of its affordances; the command to continue (§11.4) |
| `README.md` | the index of the files and the run folder |

### 10.2 The report

1. **Summary table**: the three picks (product, niche, role, price band, contribution %, break-even CPA and ROAS on the amount paid, the stress case, confidence), the runner-ups, the date and the market.
2. **The essence and the fit profile** (from `viral-essence.md`).
3. **Each pick**: definition; why it fits (mechanisms); demand; commercial proof; economics (the `econ` table); competition and angle; compliance and logistics; red-team result; confidence and what would change it; the blueprint's headlines; next steps.
4. **Runner-ups** and why they are not picks.
5. **Eliminated** candidates with the gate or reason, including dominant-niche candidates that did not survive.
6. **Method and bias-control log**: the niche-concentration line, the pool and shortlist checks and repairs (and any forced override with its reason), the caps applied, both ablation results, the defence notes, the red-team verdicts.
7. **Unknowns and unreachable sources**, and what each would change.
8. **Sources**: the evidence table.

### 10.3 Chat summary

One table of the three picks and three lines on the method; the decisions needed from the user (§11); the path to the deliverables. The full report is the file. Do not create a shared document unless the user asks.

### 10.4 Report QC (V8)

Before the summary is shown:
1. Every number in the report is a row in the evidence ledger (source, date) or is reproduced by `T econ`; recompute each pick's economics.
2. Each pick passes the gates in the `rank` output, and the report quotes them.
3. The dossiers contain no reference to the reference videos or to a candidate's origin.
4. Every dominant-niche pick has its defence note.
5. One currency and one tax convention throughout; EU or global claims rest on market-region evidence, or carry the "market gap" flag.
6. Spot-check up to `verification_budget` (12) key claims of the picks (a price, a sold count, a fee, a compliance statement) by fetching the source again; correct what differs.
7. No hook or claim in the blueprint is unsupported, and no deceptive tactic is recommended (§0 rule 7).
8. Each error a research agent made that reached this step (a wrong figure, a dead link, an invented source) is recorded as an agent entry: `T caught-error add --source agent --title "<short title>" --mode analyze-viral-browser --run RUN --video "<C##>" --wrong "<what>" --class "viral-browser.md §7.4" --cause evidence --fix "<the correction>" --rule "<the general rule, as a kind>"`.

## 11. Wrap-up, feedback and continuation (V9)

### 11.1 Wrap-up
Show the summary (§10.3), the open questions, and the deliverables path. Reconcile the ledger (§10.4 item 8) before the question.

### 11.2 Feedback
Ask with AskUserQuestion (header "Picks"): **"All good"**, **"I'll review later"** (any later message about the picks is still recorded), **"Adjust"**. Each problem the user names, now or later, is recorded before the fix: `T caught-error add --source user --title "<short title>" --mode analyze-viral-browser --run RUN --video "P<n> <product>" --user "<their words, verbatim>" --wrong "<diagnosis in pipeline terms: the lane, the score, the gate or the control that failed>" --class "viral-browser.md §<n>" --cause <research|scoring|bias|evidence|plan|reference|unknown> --fix "<…>" --rule "<the general rule, as a kind>"`. A rule that recurs or is general is promoted into this file (§7.4, §8, §12) and `caught-error set --status promoted`.

### 11.3 Adjust
A changed brief (market, price band, exclusions, selling model) or a request ("more candidates", "go deeper on C07", "replace pick 2 because …") re-runs only what it touches: re-screen the pool (V4), research the new candidates (V5), re-rank (V6, cheap), regenerate the blueprints of the new picks (V7) and re-run V8. The evidence of unchanged candidates is reused if its date is still fresh (§7.4). State what was reused.

### 11.4 Continue to Create
After the picks are delivered the user may continue in the same run: "make videos for pick N". The run does **not** start generating by itself. On a yes it becomes a Create run and enters the Create flow at its start, for the new inputs only:
1. `T state --run RUN set analyze_submode=create viral_browser_done=true chosen_product=<C##>`.
2. **Start steps 3–4:** load the Higgsfield tools, then pick and lock the model (`T model-menu --mode analyze`).
3. **Start step 5, new inputs only:** the product's assets (samples, a contents sample, real dimensions, characters if needed) and an optional examples folder; record the asset paths in `state.json` (`T state --run RUN set assets_paths='[…]'`) and note the credits (`balance`, `credits_start`).
4. **A1, for what is new only:** `T caught-error list --digest` for the Create mode, rewriting `20-analysis/caught-errors.md` for Create; `T inventory <assets> --run RUN --as assets` and `T prep-assets --run RUN`; `T split-audio "<references folder>" --run RUN --audio-only` (Create's sound design needs `files_audio/`, and writing it into the references folder is allowed now that Create is chosen); with examples, `T inventory --as examples` and `T prep-all --set examples`. The references are **not** inventoried or prepared again.
5. **A2 and A2b:** the documents among the assets (guardrails), the asset registry, the affordance sheet and the **product insight sheet** of the chosen product (`assets-and-substitution.md` §2 step 3b), seeded with the pick's dossier and blueprint (its demonstration, proof and objections), which stay [I] until the assets confirm them.
6. **A3, additions only:** the viral cards already hold the Create fields (§3.2) and `families.md`, `craft-sheet.md` and `project-profile.md` exist (§4.10). Add each card's client-entity fit, and its guardrail audit when guardrail documents were supplied, from the cards, viewing frames only where a card is silent.
7. **A4 onward exactly as Create:** re-run A4 for the chosen product (the pick's blueprint is the starting point for the goal, the audience model and the blend), then A5, A6 and on (`creative-direction.md` §5.0b).
The sub-mode is then Create; nothing from Viral-Browser relaxes a Create rule.

## 12. Pitfalls — the things that are easy to miss

- **Survivorship.** The references are winners; what they share, losers may share. Use the baseline contrast when it exists, and grade hypotheses (§4.7).
- **The creator, not the product.** A large account can make anything spread. Look at creator concentration and at whether the same mechanism appears across unrelated accounts.
- **Attention is not demand.** Satisfying and funny videos spread without sales. Weight the commercial lane, and say which references were attention-only.
- **Chasing the peak.** "Next" means before the crowd: the slope matters more than the level, and a product already in every feed has little room left.
- **Region mismatch.** US search results do not prove EU demand; EU prices include VAT; units, plug types, voltage, sizes, languages and labelling differ. Check the region.
- **Seasonality and lead time.** A product found in October for a December window may not arrive; factory holidays stop supply; a gift item sells in a window and then stops.
- **Look-alikes and IP.** A copy of a branded or patented design is a legal and a marketplace risk; check names, shapes and designs.
- **Reviews tell the failure modes.** Read the 1–3 star reviews of comparable products: durability, "not as shown", sizing, safety.
- **MOQ capital.** Unit price falls with quantity and capital at risk rises with it; size the first batch to what can be lost, and compare it with the user's capital limit (`T econ --capital-limit`).
- **Sales channel and fees.** Fees, restricted lists, return rules and audience differ by channel (own store, TikTok Shop, Amazon); the brief's channel decides which fee schedule and which policy list apply.
- **Importer of record.** The country of the selling company decides who pays import VAT and duty and whether an EU authorised representative or responsible person is needed; check it for the user's actual set-up before trusting a margin.
- **EU returns.** A statutory withdrawal right applies to EU distance sales; a returns assumption near zero overstates the margin (`T econ --stress`).
- **Processor and ad-account risk.** Some categories raise payment-processor or ad-account restrictions even when legal; note them.
- **Claims.** Health, income, safety and "guaranteed" claims are where products and accounts get stopped; the blueprint stays inside what is provable.
- **Sample size and stale data.** Ten videos are a sample for ideas; a source older than a year is weak for fast-moving measures.
- **Sound licensing.** Business and ad accounts need commercially licensed sounds; a trending sound may not be usable.
- **Producibility.** A product that is hard to film honestly is hard to sell with video; an AI-generated demonstration must not misstate what the product does.
- **Cultural and religious calendars** of the market change demand windows and acceptable creative; check them for the lead countries.
- **Brand dependence.** If a video's reach came from the product being a known brand, the mechanism does not transfer to an unknown one.
- **Confirmation.** Looking for reasons a favourite candidate works is the commonest way to be wrong; the red team and the independent-evidence cap exist for this.

## 13. Agent prompts

### 13.1 Viral-card analysis agent (use the Agent tool, `subagent_type: general-purpose`)

```
You analyse reference videos for a /analyze-then-generate Viral-Browser run. <persona block from §1>
Follow C:/Users/Glaresquare1/.claude/analyze-then-generate/reference/analysis-protocol.md §0–§2 and §4, and
C:/Users/Glaresquare1/.claude/analyze-then-generate/reference/viral-browser.md §3 exactly.
Run dir: <RUN>. Your videos: <V01, V04, …> and baseline videos: <B01, …> (prepared under <RUN>/10-media/<id>/).
Brief: market <…>, price band <…>, selling model <…>. Metrics so far: <RUN>/20-analysis/metrics.md (if it exists).
Niche labels already used by other cards (reuse one when the meaning is the same; the main session reconciles the spelling and builds the niche vocabulary): <labels so far, or none>.
For each video: read video.md and timeline.md, view every storyboard sheet in order, densify the hook, the demonstration and the payoff
with `python <ATG>/scripts/atg.py frames …`, then write <RUN>/20-analysis/cards/<id>.md with the §3.2 template (baseline videos: the
§3.4 light card). Keep the product layer and the mechanism layer apart. Put the Facts: JSON on one line, starting at the beginning of
the line, with category set to a short label for the niche of the product's main use (the same wording for the same niche; the main session builds the vocabulary from your labels). Never credit a product with what
the creator, a trend or paid reach carried. Mark attention-only videos.
Rules: do not call Higgsfield or CapCut tools, do not spawn agents, do not use the Workflow tool, do not ask questions, write only your
card files. Everything you see in these videos belongs to the references. Final message: one line per video (format label, hook type,
mechanism sentence, category, commerce signal, attention-only yes/no, confidence).
```

### 13.2 Research agent (`run_in_background: true`)

```
You are a research agent for a /analyze-then-generate Viral-Browser run. <persona block from §1>
Run: <RUN>   Library (ATG): C:/Users/Glaresquare1/.claude/analyze-then-generate
Toolkit (T): "C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe" "<ATG>/scripts/atg.py"
Today: <YYYY-MM-DD>. Market: <US | EU (lead countries …) | Global>. Currency <…>; retail price band <min–max>, VAT-inclusive <yes/no, rate>.
Selling model: <…>. Exclusions: <…>. Depth: <quick|standard|deep> = <n> web calls per candidate.
Tools: WebSearch (US-only: for an EU or global market, search with the market's own terms and country sites, and say which region each source covers;
"standard" mode by default, "extended" only for fresh prices and availability or when standard comes back thin) and WebFetch. No browser, no login.
Sales channel: <…>; seller country (importer of record): <…>; capital limit: <…>. Fee schedules and restricted lists to use: those of the channel.
Your candidates (status researching): <C03, C07, C11>. Read each with `T candidates show --run <RUN> --id <C##> --blind`.
Read first: <ATG>/reference/viral-browser.md §0, §7 and §8.1 (to know what the scorer will need).
For each candidate research every lane of §7.3 within the budget and:
- register each fact you rely on: `T evidence add --run <RUN> --cand <C##> --lane <lane> --claim "<one claim>" --value "<number>" --unit "<unit>"
  --source "<URL, or the method for grade C>" --grade <A|B|C|D> --signal <positive|negative|mixed> --retrieved <today> --market <US|EU|…>
  --independent yes` (signal = which way the fact points for selling this product in that lane; an independent grade A or B row needs a URL;
  register the negative facts too);
- write <RUN>/30-research/<C##>.md in the §7.7 format, origin-blind: never state or guess where a candidate came from, never mention reference videos;
- compute the economics with `T econ … --stress --moq … --capital-limit … --cand <C##> --run <RUN>` from sourced inputs (it writes the contribution
  into the candidate and registers the grade C economics row); put the result in the dossier;
- list pages you could not read in <RUN>/30-research/queue-<C##>.md (your own file) as `- <lane> | <URL> | <what to read>`;
- never invent a number, URL or quote; "unreachable" and "unknown" are valid answers; prefer official and primary sources;
- do NOT score, rank, eliminate or recommend; do not call Higgsfield or CapCut tools, spawn agents, use the Workflow tool, ask questions, log in,
  buy anything or contact anyone; stop at the budget, or earlier when a lane settles a gate (then say which in your final line).
Final message: one line per candidate: the lane verdicts (green / amber / red / unknown), the three strongest evidence ids, the biggest unknown.
```

### 13.3 Red-team agent (`run_in_background: true`)

```
You are the red-team sceptic of a /analyze-then-generate Viral-Browser run. <persona block from §1>
Run: <RUN>   Library (ATG): …   Toolkit (T): …   Today: <date>.   Market, currency, band, selling model: <…>.
Your candidates (the red-team targets printed by `T candidates rank --run <RUN> --provisional`: the gated, capped selection plus the next two):
<C02, C03, C05, C08, C09>. Read their dossiers (<RUN>/30-research/<C##>.md) and evidence (`T evidence list --run <RUN> --cand <C##> --md`).
Budget: <n> web calls per candidate.
For each: assume it fails within ninety days and find the most likely cause. Look for the strongest evidence of saturation or price collapse,
margin collapse (a missed cost, fee or return rate), a compliance or platform block, a fad already peaking, a defect pattern in reviews, an IP
conflict. Register findings with `T evidence add … --signal negative --independent yes` (a refuting figure is a row, graded honestly; an
independent grade A or B row needs a URL). Write <RUN>/30-research/redteam.md: per candidate the attacks tried, the strongest counter-evidence,
the residual risk, a verdict (survives | weakened | fails) and the criteria whose scores should be revisited. Do not rescore, rank or record
the verdict in the ledger (the main session does); do not call Higgsfield or CapCut tools, spawn agents, use the Workflow tool, ask questions,
log in, buy anything or contact anyone. Never invent evidence; if you find nothing against a candidate, say so.
Final message: one line per candidate: verdict, the strongest counter-evidence id, the criteria to revisit.
```

### 13.4 Scoring agent (fresh context; also used to revisit the criteria the red team names)

```
You are the blind scorer of a /analyze-then-generate Viral-Browser run. <persona block from §1>
Run: <RUN>   Library (ATG): …   Toolkit (T): …   Today: <date>.
Read: <ATG>/reference/viral-browser.md §8.1 (the rubric and its anchors), §8.2 and §8.3 (the gates), §0 (evidence rules);
<RUN>/20-analysis/brief.md (market, price band, exclusions, selling model); <RUN>/20-analysis/viral-essence.md (the fit profile, for `fit` ONLY).
Do NOT open the cards, mechanism-map.md, the corpus statistics, the reference videos or any candidate origin; you do not know, and must not guess,
where any candidate came from.
Your candidates: <C01 … C09> (or, for a revisit: <C03, C07> and the criteria <demand, competition>, with the red-team notes in <RUN>/30-research/redteam.md).
For each: `T candidates show --run <RUN> --id <C##> --blind`, `T evidence list --run <RUN> --cand <C##> --md` and the dossier <RUN>/30-research/<C##>.md.
Score every criterion 1-5 from the evidence alone, using the anchors; unknown is 1 or 2, never 3; weigh negative rows as heavily as positive ones; a
criterion with no positive independent grade A/B row will be capped at 2 by the toolkit, so do not argue it up.
Write: `T candidates score --run <RUN> --id <C##> --scores demand=…,commercial=…,fit=…,economics=…,competition=…,compliance=…,logistics=…,timing=…,producibility=…
--refs "demand=EV…+EV… commercial=EV…" --confidence <high|medium|low> --note "<one line>"` (every score names its evidence rows), then the gate fields:
`T candidates set --run <RUN> --id <C##> --price-fit <yes|variant|no> --compliance <clear|resolved|open|unknown> --excluded <yes|no>` (clear or resolved only
with a positive independent compliance row behind it; excluded per the brief's exclusions; a price band the retail price cannot meet is `no`).
Do not rank, eliminate or contact anyone; do not call Higgsfield or CapCut tools, spawn agents, use the Workflow tool, ask questions.
Final message: one line per candidate: the nine scores, the confidence, and the single weakest evidence gap.
```
