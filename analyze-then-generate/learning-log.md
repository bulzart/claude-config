# Learning log: /analyze-then-generate

One section per change of substance, newest last. A pattern that
recurs after a logged change means that change failed: revise it, do not repeat it.

## 2026-10-11 · fork · /analyze-then-generate created
- **Origin:** a copy of an earlier pipeline library as of 2026-10-10 14:04 (all references, the model guides, the
  toolkit renamed `atg.py`, the ledger CE-001..CE-029). The history of every inherited rule predates this log.
- **Added:** the Viral-Browser sub-mode (`reference/viral-browser.md`; command steps V1-V9 and contract items 23-25;
  toolkit `viral-stats`, `candidates`, `evidence`, `econ`, `new-run --submode`, the `baseline` set of `inventory` and
  `prep-all`; config `viral_browser`; the ledger causes research, scoring, bias, evidence).
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
- **Added (Create only; Recreate unchanged):** `viral-browser.md` section 14 (what Create takes and skips from the
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

## 2026-10-12 · the product reference pack (Viral-Browser)
- **User request:** for each of the 3 winning products, official or verified product information (size, width, height, weight, texture, usage and
  other useful data) and photo references from several angles, which may later be used as the product reference in Higgsfield video generation.
- **User correction (the same day, on seeing the first version, which downloaded the images):** "no don't download them just bring the image url
  links". The pack now holds LINKS only: no image is downloaded, resized, hashed or stored, and the PNG contact sheet, the EXIF and resolution
  handling, the duplicate detection by image content and the viewed / usable flow were removed. Lesson, as a kind: when the user asks for references
  to web material, deliver the pointers (links with their provenance and status), not copies; build the lightest thing that answers the request and
  offer the heavier one.
- **Added:** `viral-browser.md` section 9.1 (the reference unit; the sourced specification with grades and the verified / official / reported /
  conflict statuses; the photo links and their coverage; rights and honesty; use in Create; the files in `deliverables/reference-C##-<name>/`, named
  after the candidate so that a re-ranking cannot send two products into one folder), section 13.7 (the reference-pack agent prompt, one per pick
  after `rank --apply`, up to 3 at once), QC items in 10.4, pitfalls, the continuation to Create; toolkit `spec` (add, list, render, check, reject) and
  `photo` (find, add, set, list, check) with `config.json -> viral_browser` keys (`reference_pack_budget`, `photo_*`, `spec_tolerance_pct`).
- **Decisions:** a size or weight is never read off a photo; grade A is only the maker's, brand's or a regulator's own document (a listing is B); two
  sources count as independent only on different domains; a block (401, 403, 429) is final and is never bypassed; the angle of a link is as the source
  labels it (a background agent cannot see images and nobody has looked), so the visual flags stay unset until someone opens the image and `photo set`
  refuses them without `--looked-at yes`; the coverage verdict is covered / partial / thin / none, never "ready"; HEAD only (a server that does not
  answer HEAD leaves the link unchecked, there is no GET instead); only public http(s) addresses are probed, redirects by hand with each hop checked;
  `photo find` reads product PAGES (read-only) to list the image addresses they declare, because WebFetch's text rarely carries them; Higgsfield's
  `media_import_url` (HTTPS only) is the route from a link to a generation reference without saving the image; rights are unknown unless the source
  says otherwise; the reference unit is one real identifiable product (brand and model, or the supplier's listing), not the category.
- **Hypotheses to test on the first run:** (1) the maker's page declares three or more angles for most picks, otherwise galleries are built by script
  and `photo find` returns few addresses (count the "few images" notes); (2) the first image of a gallery really is the front (ask the user to open
  `photos.html` and say how many labels were wrong); (3) most image hosts answer HEAD (count the unchecked and blocked rows); (4) one reference unit
  per pick is enough when the pick is a generic white-label product (watch whether the specification differs between listings); (5) 24 web calls per
  pick at standard depth are enough for a complete sheet and a covered link set.
- **Hardening in the same pass:** (a) the pack folder is named after the candidate and recorded in `photos.json`, because a pick number changes when
  the ranking is applied again; (b) only public http(s) addresses are fetched and each redirect hop is checked, so a page cannot steer the toolkit to
  the user's own machine or network (the test suite reaches its local server with a hidden `--allow-private-host` switch that no prompt uses);
  (c) `photo_max_attempts` (30) caps the links tried per pick.
- **Second independent review (same day):** it verified real problems in the first links-only version, all fixed and tested: (a) text facts: wording
  that merely contained another's words was called verified, negations ("not dishwasher safe") merged with their opposite, the result depended on the
  order of registration, and a retailer's word-for-word copy of the maker's paragraph counted as a second source - now equal words verify, containment
  is only compatible, a negation or different words is a conflict, and a long text repeated by another site counts once; (b) a sheet could be "complete"
  with words in place of numbers ("wide", "light") - numeric fields now refuse text; (c) `photo check` said "covered" for five http links that all
  answered 403 - the verdict now needs confirmed links (`unconfirmed` otherwise); (d) the probe sent the maker's page as Referer, so a hotlink-protected image
  looked fine while Higgsfield's importer and the gallery would be refused - the probe now sends none; (e) a fact for another variant, or a generic fact
  beside a variant-specific one, could silently decide the sheet - the variant of the reference unit decides, a variant-specific fact outranks a
  generic one, and what was left out is listed; (f) a slow server or a hostile page could hold the command for a minute or more - every page read, probe and
  parse has a deadline, scripts are scanned in bounded time; (g) with only an https proxy configured the connect-time check stood aside for http
  addresses - the decision is now per address, and the check is installed once and switched on per thread; (h) a date such as 2026-02-30 broke the
  whole sheet later - dates are validated; (i) `derived` could be grade B and "measured" could be a size eyeballed from a thumbnail - both closed;
  (j) concurrent writers of one pack could collide on a fixed temporary name - names are unique, and the lock waits out a Windows deletion;
  (k) smaller: the https twin replaces an http link, angle spellings fold (rear, top-down, close-up), field names fold (Product Weight, Colors),
  compact srcset, <base href>, preload links and image addresses inside scripts are read, packaged lists reach the sheet, usage steps keep order and
  full text. Lesson, as a kind: a status that can be reached without evidence (verified by wording, complete by words, covered by unconfirmed links) is
  a defect of the same class as a missing check; test every status with the cheapest input that should NOT earn it.

## 2026-10-12 · audio context in every analysis mode
- **User request:** the agents that mine and analyse the video references should also transcribe the references' audio and understand it, to gather more
  context about each video, in Create and Viral-Browser, and in Recreate too (context only: the reference sent to Higgsfield stays silent); and verify the
  method really works on mp3 audio, extracted from the reference videos or from another sample, before relying on it.
- **Verified first:** the transcription already in the toolkit (faster-whisper, the open-source Whisper model, `small` cached locally, CPU, offline) was
  run on mp3 files: a text-to-speech sample of known text came back with a 2.9 % word error rate (only "ten" written as "10"), and the audio of all 15
  references in `Documents/test` was transcribed without an error: 6 had speech in English, 3 were songs (English lyrics, Spanish lyrics, a rap), 6 had no
  speech. The same audio through the pipeline's own 16 kHz route and through an mp3 gave different words for one music-led video, so the digest flags a
  doubtful language and low-confidence words instead of trusting the text.
- **Added:** `atg.py audio-context` (the digest `20-analysis/audio-context.md` and `.json`: every transcript with its times, the language, the speech and sound
  facts, repeated phrases, flags; `--profile` measures the sound design of the videos that lack it; `--check` fails while a transcript is missing, failed or
  skipped and, with `--cards`, while a card lacks its `Audio context:` and `Said:` lines), `--no-vad` on `prep-video` and `prep-all` for a second pass
  without the voice filter, `audio-profile` refactored into a function; the three card lines in the protocol card and the viral card; the spoken layer in
  the synthesis (`viral-browser.md` 4.3, 4.5); the pitfall "a transcript is a machine's hearing"; the agent prompts 13.1 and 13.6; the command's A1, A3, V1 and
  V2 steps; the build prompt.
- **Decisions:** the transcript is evidence of the words as heard, never of what the speaker meant; a spoken claim is a claim, not proof; in Recreate the audio
  is analysed and never uploaded (only the silent copy goes to Higgsfield, the original audio is restored afterwards); in Create the craft of the speech may
  be borrowed, never its lines, claims or subject; a larger model is optional and only for the videos the digest flags.
- **Hypotheses to test on the first run:** (1) the `small` model is enough for the speech references and the flagged ones are few; (2) the "Said:" lines
  change the mechanism map (hook lines, promises, calls to action) beyond what the pictures gave; (3) the music-led videos with no speech are a real
  silent-friendly mechanism and not a transcription miss (check one with `--no-vad`).

## 2026-10-12 · scripts gather, agents decide (every mode)
- **User rule, verbatim:** "make sure that the python scripts do not carry the heavy comparison and the final word because thats not correct, we do not
  want 'script that counts x word or niche that was gathered by the agents and then decides who wins because the script gathered x word to be more used than
  x word' because thats not normal, scripts can be used to gather and excract but never evaluate, scripts do not have decisive logic nor can understand data,
  decisions and evaluating the data should be carried by the ai agent that will run the pipeline", and then: "this logic should be true for all the modes ...
  on each mode the agents are those who decide what to do based on the mode specs, scripts just help with gathering and collecting".
- **Audit result (what decided in the scripts):** (a) shared tools, all modes: `qc` (problems list, pass flag, substring comparison of planned and seen text),
  `sync-check` (in_sync / constant_offset / drift / out_of_sync and a fix), `scale` (ok / note / regenerate / provisional / inconclusive), `conform` (refused a
  large crop), `finalize` (refused a file that failed its checks), `restore-audio` (gates), the submission ledger (refused four ways), `model-menu` (a ranked
  quick-pick list), `inventory` (guessed what a file is from its name), the OCR (caption track, persistent overlay, likely noise), the audio profile
  (music bed likely/unlikely, energy arc, reusable whole) and the audio digest (kind, language-uncertain flags); (b) Viral-Browser: `viral-stats` (dominant
  niche, concentration index, small-sample flag), `niches` (shared-word and look-alike warnings, a 25-character reason rule, an audit the script validated),
  `candidates` (pool balance, shortlist refusal, status guards, the independent-evidence cap, floors, six gates, the niche cap, tie-breaks, the ranking, two
  ablations), `spec` (clusters, verified / official / reported / conflict, a completeness verdict, text-agreement and negation heuristics), `photo` (scores,
  a junk flag, view guesses, a coverage verdict, a suggested reference set, caps) and `econ` (judging warnings, "the lowest market counts").
- **What replaced them:** numbers, records and side-by-side tables, with the decision recorded by the agent (`--by`, `--reason`, histories, `spec judge`,
  `niches audit`, the bias log in `ranking.md`). New or changed: `candidates rate | table | summary` (no `rank`, `pool`, `shortlist`), `spec judge | table | gaps`
  (no `check`), `niches` as a record (no `distinct`), `evidence retract | list --counts`, `ledger begin` reports `conflicts` and refuses nothing, `conform --dry-run`,
  `sync-check` windows with their correlation and motion, audio numbers (spectral flatness, steady-tone share, harmonic share, first confident word).
  The numbers the scripts enforced are rules of thumb in `config.json -> viral_browser.rules_of_thumb` and in the references, for the agent to apply, to
  depart from when the evidence says so, and to write down.
- **Kept, on purpose:** file locks, the exact-fingerprint bookkeeping, the safe-address guard of the page reader and the link probe, the form checks (a URL behind a
  sourced row, an integer 1-5, a unit for a size), the CapCut "close CapCut" and locked-preset checks. None of them reads meaning.
- **Found by the first live run (15 references, 2 card agents):** sung and rapped words counted as speech, a ghost first word, a beep read as words, the
  music-bed label wrong on noise and on a tone; the c< frame showed the new shot; the index printed prep time as if it were the length; a card agent could not tell
  who sets price_tier and creator_group. The first four are exactly what a label hides and a number shows.
- **Lesson, as a kind:** a label computed by a script (likely, covered, dominant, verified) lets the reader skip the data, and a heuristic behind it hides its inputs;
  a threshold in code is a decision nobody wrote down. Return the inputs, tabulate them, and let the agent that reads them decide and say why.
- **Hypotheses to test on the first full run:** (1) the main session's bias log names the dominant-niche reading and every departure from a rule of thumb, with
  its reason; (2) the blind scorer's notes say which evidence rule it applied; (3) `ranking.md` and the recorded `pick-rank`s agree; (4) no agent treats
  a table order as a ranking.

## 2026-10-18 · rebuild · router, 25 phase skills, section files; no error ledger; Loupe
- **What changed:** the monolithic command (about 190 KB) became a router (about 20 KB) plus 25 phase skills (`atg-*`), and every long document (the
  references including `viral-browser`, the Higgsfield guide, the model guides) an index plus section files (`scripts/docs_tool.py`). A phase loads only the
  sections its "Read now" list names, and `state.json -> next_skill` makes every phase boundary resumable. Viral-Browser's steps V1-V9 became six skills
  (`atg-vb-*`); the Create virality mining stays in `atg-analyze-study` and `atg-create-plan`. Contract items were renumbered: 22 no error ledger, 23 caught
  flags, 24-26 Viral-Browser (they were 23-25).
- **Error ledger retired:** `caught_errors.md` and `atg.py caught-error` are gone. The lessons of the first Viral-Browser research wave (the common cost basis,
  price and cost read at one variant, stored scenario prices, derived figures inside evidence rows) are written, as kinds, in `viral-browser` section 7.0 and
  sections 7.3 to 7.5. A video or a pick the user reports as wrong is diagnosed in its brief (Viral-Browser: `deliverables/feedback.md`); a lesson the references do not hold is
  written, generalised, into the section that owns it.
- **Loupe:** `atg.py caught-flag`, `qc-consult`, `qc-brief`, `plan-hints` and `loupe` are linked. The flag record is written and never read during a run; only QC
  reads the sample library, and the first request of a video asks it once for a few text-only hints.
- **Cleaned while moving (reasoning over rule lists):** niche, product and brand examples removed from rules and agent prompts (an example biases a run toward
  itself), live-run anecdotes and figures reduced to the kind of miss, the pitfalls list cut to the cross-cutting traps with the owning section named,
  the reference-pack and card prompts now cite section files.
- **Hypotheses to test:** (1) a Viral-Browser run resumed in a new session continues from `next_skill` without rereading earlier skills; (2) card labels and candidate
  pools no longer echo words from the removed examples; (3) Create's A3-A4 phase (about 110 KB of sections) still writes complete cards, otherwise split A3 from A4.

## 2026-10-18 · QC fixes option; consistency pass after the rebuild
- **What changed (the user's request):** new contract item 27, QC fixes, for Recreate and Create. At the start the user chooses `ask` or `auto` for the fix generation after a QC
  finding. `ask`: from the first video on, a production agent that finds issues or anomalies only a new generation can fix writes its attempt block, prepares the corrected request and
  its cost preflight, submits nothing and stops with a `fix_proposal` (`blocker: qc_fix_permission`); the main session asks the user (one question per waiting video: fix it / keep this
  take / fix it and stop asking), continues the stopped agent with `approved`, `declined` or `auto`, and a declined fix ships the take as generated, flagged. `auto`: the QC agents
  correct on their own, as before. Stored in `state.json -> qc_fixes` (a run without it is `auto`), argument `qc-fixes ask|auto`. Edit Mode is unchanged: it never regenerates
  automatically and the user reviews every attempt. Written in the router (item 27), `atg-start` (the choice), `atg-qc` (the proposal), `atg-submit` (X7 waits), `atg-analyze-produce`
  (the question), `atg-wrapup` (the report) and `production-agents` sections 1 to 5.
- **Found by comparing every step of the rebuilt skills with the previous command, and fixed:** (1) the submission ledger was described in three places as enforcing a cap and
  refusing (exit 3); it records and reports `conflicts` and never refuses; (2) six model guides and the Higgsfield guide said `conform` refuses a crop over 12 %; it reports
  `lost_fraction` and never refuses, and the crop rule is now where Create and the production agents read it; (3) rules whose only copy sat in a section read at the end of a phase
  moved into the sections that own them (a product already in every feed, region details, processor and ad-account limits, brand dependence, the PDF reader, the heartbeat and
  "the toolkit does not change during a wave"); (4) sections that no phase loaded are on Read-now lists (anomaly catalog 2.10 to 2.13 and 4.1, assets 1 and 6, the persona block for
  agent prompts, the card template's pointers); (5) old section numbers (`§5 X7`, `§2.4`, `§2.5`) replaced by labels that resolve; (6) the paste test and "a deviation from a default is
  a note" got a tie-break (a pose or light the plan asks for is not a sign), the prompt's "never / always / only" rule got one list of the lines a section mandates by name, and the
  one targeted exclusion has one wording; (7) the market-gap flag and the confidence rule agree (a gap alone caps confidence at medium); (8) the Viral-Browser state loops (V4 to V4b,
  V6 to V5 backfill) store a next step that resumes correctly; (9) index preambles no longer tell an agent to load a whole document; (10) the QC stack's step labels are in order.
- **Lesson, as a kind:** when a document is split into sections, every rule that two phases act on, every pointer to a section and every sentence that describes what a script does has to be
  checked against the new loading plan: a rule can survive in a section that is read too late, a pointer can name a section nobody loads, and a script described as refusing something it
  does not refuse sends an agent to wait for a signal that never comes.
- **Hypotheses to test:** (1) with `ask`, a run whose agents stop at the same time asks their questions in one call, and a continued agent resumes at X7 without rereading its plan;
  (2) a run resumed while an agent waits shows the `qc_fix_permission` row in `videos[]` and asks again; (3) with `auto`, nothing changes from before.
