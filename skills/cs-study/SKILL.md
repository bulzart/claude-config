---
name: cs-study
description: /create-static Analyze Mode / Static phase: video analysis, synthesis, house approach, the niche, style, length, language and video count (A3–A5). Internal to that command.
user-invocable: false
---

# cs-study — Static: analysis, synthesis, the locks, count (A3–A5)

> `CS` = `C:/Users/Bulzart/.claude/create-static` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$CS/scripts/cs.py"` (every call prints one JSON object on its last line; run through PowerShell: Git Bash forks fail on this PC) · `RUN` = the run folder `CS/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `CS/reference/<file>/`; `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again. Static's card is static §1–§2: the protocol's §3 card and its product, placement and video-physics sections are not read.

- analysis-protocol §0: `CS/reference/analysis-protocol/010_0_provenance-labels-use-everywhere.md` (0.6 KB)
- analysis-protocol §1: `CS/reference/analysis-protocol/020_1_inputs-per-video-produced-by-awl.md` (1.6 KB)
- analysis-protocol §2: `CS/reference/analysis-protocol/030_2_reading-a-video-as-one-continuou.md` (5.8 KB)
- analysis-protocol §4: `CS/reference/analysis-protocol/050_4_effectiveness-lenses-apply-those.md` (2.1 KB)
- analysis-protocol §5: `CS/reference/analysis-protocol/060_5_cross-video-synthesis.md` (5.4 KB)
- analysis-protocol §6: `CS/reference/analysis-protocol/070_6_project-inference-20-analysis-pr.md` (2.4 KB)
- analysis-protocol §7: `CS/reference/analysis-protocol/080_7_scale-and-delegation-2-analysis.md` (3.4 KB)
- analysis-protocol §8: `CS/reference/analysis-protocol/090_8_presenting-results-to-the-user.md` (0.2 KB)
- analysis-protocol §9: `CS/reference/analysis-protocol/100_9_examples-the-user-s-own-videos-t.md` (3.1 KB)
- creative-direction §1: `CS/reference/creative-direction/010_1_the-roles.md` (1.8 KB)
- creative-direction §2: `CS/reference/creative-direction/020_2_the-goal-model-written-into-20-a.md` (1.4 KB)
- creative-direction §3: `CS/reference/creative-direction/030_3_the-audience-model-mass-cognitio.md` (3.0 KB)
- creative-direction §4: `CS/reference/creative-direction/040_4_the-trend-read-written-into-20-a.md` (2.1 KB)
- *the client's documents hold rules (`RUN/30-assets/guardrails.md` exists):*
  - brand-guardrails §3: `CS/reference/brand-guardrails/030_3_the-guardrail-audit-per-referenc.md` (3.2 KB)
- static §0: `CS/reference/static/005_0_the-team-who-works-a-static-run.md` (5.8 KB) (who works the run: read at the start, again only
  after a compaction)
- static §1: `CS/reference/static/010_1_what-static-mines-from-the-refer.md` (12.7 KB)
- static §2: `CS/reference/static/020_2_the-static-card-and-the-spec-a3.md` (13.5 KB)
- static §10: `CS/reference/static/100_10_one-channel-per-run.md` (11.5 KB) (the niche, the visual style and the narrator, A5)

### A3. Video analysis (as continuous sequences)
- **The card (Static):** each card is the Static card (static §1–§2) in place of the product and physics fields: read `video.md`, `timeline.md`
  and every storyboard sheet (2 fps), and run `T audio-profile --audio "<files_audio file>" --out 10-media/<V>/audio-profile.json
  --transcript 10-media/<V>/transcript.json --cuts 10-media/<V>/cuts.json --voice` (the bed and the voice as numbers). The moves, joins
  and caption entrances come from `10-media/<V>/edit-profile.json` (`T edit-profile`, A1), never from the 2 fps sheets; view one caption
  entrance and one cut densely (`T frames … --range a-b --fps 30 --sheet`) to see what its numbers describe. The spec's motion, joins and
  entrance are matched to `CS/data/capcut-catalogue.md` (static §2, §9: only what CapCut drew on this PC). Each card also records the
  reference's **drawn annotations** (static §1; the user, 2026-11-11: lines, arrows, circles, highlights and words drawn on over a still,
  each with its times, look and lead on the spoken word), read on the frames viewed densely, or "none". Every card has every field
  of static §1, the retention, emotion, language (the language the reference speaks included), engagement, attachment, social,
  content-style and approach fields included, so the set can be read as a whole (the references may be in one language or a mix: each
  is read in its own).
- Follow `CS/reference/analysis-protocol/` (the sections named in Read now) exactly. For each video:
  - read `video.md` and `timeline.md`;
  - view **every** storyboard sheet in order, reading the timeline beside it;
  - densify with `T frames … --range a-b --fps 15 --sheet` around fast actions, cuts and text appearances;
  - write `20-analysis/cards/<V>.md`, with the fields of static §2 and, from protocol §2:
    - its **trend elements and cognitive triggers** (protocol §2.12; `creative-direction.md` §3–§4):
      the format name and caption grammar, the structural mechanism, the surface elements with
      their freshness, the emotion arc, the laugh mechanism, the share line;
    - its **guardrail audit** (protocol §2.13; `brand-guardrails.md` §3), when `30-assets/guardrails.md` exists: every hit against
      it with its time, element, prominence and place (picture, caption,
      speech, insert, reflection), classified core or peripheral by the meaning test, and the
      verdict: pick-clean, pick-and-edit with the operations, or dismiss with the rule;
    - its **inserts**: memes or other clips that interrupt the reference, with their exact in and
      out on cut frames, video or still, and their sound;
    - its **overlay text**: wording, role, centre position, in and out times, and style. The OCR spans (`ocr.json`,
      `video.json`, `video.md`, `timeline.md`) carry numbers and spelling facts only: `text`, `first_t`, `last_t`,
      `hits`, `share_of_frames_scanned`, `y_rel`, `band`, `band_distinct_texts`, `band_frames`, `score_mean`, `chars`,
      `words`, `has_at_handle`, `has_hashtag`, `has_url_pattern`, and `bands[]` per row of the frame. No script says
      whether a text is a caption, a fixed overlay, a watermark, a handle, a label or noise: you decide that from the
      numbers and the storyboard.
- Analysis agents (contract item 2): delegate only per §7 of the protocol, with disjoint video lists: none by default (the
  main session analyses everything itself), 1 for many references, 2 for a large folder. The agents write the Static card (static §1–§2) in
  place of the protocol's §3 template. Give them the registry's one-line summary of what the user supplied and no cap on densified ranges
  (Static has no effort level, static §1).
- Images and other files in the references folder are also **reference material**: samples, thumbnails and executions. Analyse them as
  references and never treat them as client assets.
- **Examples** (contract item 18): one card per example, `20-analysis/examples/<E>.md` (protocol §9):
  product integration, continuation, blend, characters, text, structure, sound, what they avoid,
  and flaws not to copy. The same agents (at most 2) take them in their lists.

### A4. Synthesis
Write, following the protocol §5–§6:
- `20-analysis/families.md`: dynamic content families with measured profiles;
- `20-analysis/project-profile.md`: the domain and objective and the authoritative requirements (protocol §6), and the **goal**, the
  **audience model** and the **trend read** (`creative-direction.md` §2–§4; protocol §6);
- first `T static profile --run RUN` (every analysed reference's measured numbers and the set's median and range,
  `20-analysis/set-profile.md`; `--refs` for a family), then `20-analysis/static-spec.md` (static §2) from the **whole set** (the user,
  2026-11-08: "the reference datas should be studied as a whole not just pick one of them to copy"): the narration template, the pace
  (the set's bands while speaking and overall, the pauses), seconds per still, retention, emotion over time, language, engagement,
  attachment, the social side, content style, the approaches seen (static §2: counted across the set and the niche's references), the
  niche candidates (fields, never a title or story form), the visual styles (each reference's, grouped, with a storyboard sheet
  each), the caption pattern, motion and transitions, the drawn-annotation pattern (static §2: how often, which kinds, their look and
  speed as numbers, their lead on the spoken word; empty when no reference draws), the voice profile, the bed brief, the devices, what
  is left behind; each value
  with the counts and numbers of the set it rests on, families read apart when the set holds different kinds; the style lock and the
  text look are written after A5 from the reference the user picks (static §10: the look only); no directions, ranking or craft sheet;
- **With examples:** `20-analysis/house-approach.md` (protocol §9.3): the user's consistent approach,
  one rule per line with its evidence and the default it replaces. The picks and plans
  follow it (contract item 18).

Show a **short** chat summary:
- the project profile in about 5 lines;
- the families table;
- the house approach in 2–4 lines, or "no examples";
- then the Static spec in about six lines, followed by the visual styles, one line per family: the references in it, the look in words and the full path of its storyboard sheet,
  so the user can look before A5's question.
Then run `T state --run RUN set stage=analyzed next_step=count`.

### A5. How many videos
One AskUserQuestion call with four questions (static §10; the user, 2026-11-07: one niche, one visual style and one narrator
per run, "because we want to remain consistency on content and style"):
  - header "Videos": options "1", "3", "5" ("Other" allows any number);
  - header "Formats", multiSelect (static §2): `T static formats --run RUN` gives the facts; the aspects, the best fit first,
    marked (Recommended), each with its sizes and, from the second on, what one more format adds; the first picked (in the options'
    order) is the primary, stored with `T static format --run RUN --aspect A --res R [--quality Q] [--image-size WxH]`, each other one
    with the same command and `--also`;
  - header "Niche", "Which niche is this channel about? Every video of this run stays in it.", none recommended: up to four of the spec's
    niche candidates (the references' own field first), each with one line on the kind of stories in it and two or three approaches
    its videos could take (from the spec's "Approaches seen": counted days, "what happens if", a case retold …); a niche is a
    **field**, never a title wording or one story form (the user, 2026-11-11; static §10 "The niche is a family, each video an
    approach"), so a candidate never reads "N days of X" or "How to …" alone; "Other" takes any field;
  - header "Visual style", "Which reference's visuals should every video have?", none recommended: up to four references, one per visual
    style family, each named with its look in words; "Other" takes any reference by its id. A run with one reference skips this question
    and takes that one (said in one line).

Then `T static lock --run RUN --niche "<niche>" --style-ref <V>`, and write the spec's style lock and text look from that reference's
card (static §2, §10: its captions when it has them, else the most common look of the references that have them). Then the spec's
**niche's references** (the user, 2026-11-09; static §1 "The run's niche within the set", §2): the references whose field is the
picked niche, read from their cards with the reason (none when the niche is new to the set: the whole set's craft leads), each
field's pattern for them beside the set's and the family's, and their numbers (`T static profile --run RUN --refs <them>`); and the
spec's **approaches seen** (static §2): the story forms, points of view, time frames, scales, pillars and title forms the cards
record, counted across the set and across the niche's references.

**Then the length**, one more AskUserQuestion call, always after the niche is locked and before any subject, script or image plan
(the user, 2026-11-12: the length is asked way before generation and planning; when no niche is locked yet, the niche family is
locked first, as above, and then the length is asked; when the niche is already locked, `more <run>`, it is asked straight after
the count; static §2 "Length", §4, §10). The numbers first, printed in one short block from the run's data: the niche's
references' lengths (the references the spec names as the niche's: each, the shortest, the median, the longest, from `T static lock
--run RUN` → `reference_lengths.each` read for those ids; the whole set's beside them when the niche is new to the set) and what
their length follows (the spec's Length). Header "Length", "How long should each video be?", two options, **"Standard"** first
(the length the niche's references run: its median in minutes, "about N min, the niche's references run A to B min"; each video's
own length is then the agent's from that pattern, as before, static §4) and **"My own length"** (the user's number: the total ("15
minutes") or the change from standard ("2 minutes longer", "3 less"), the same for every video of the batch, or one per video
("1 12 min, 2 8 min") through "Other"); a "My own length" answered with no number is asked once in plain chat. A length the
format cannot carry (a Short under a minute in a long video's format, or the reverse) is said in one line with the nearest that
fits, and the user decides. Store it with `T state --run RUN set 'static.length_plan={"mode":"standard"|"own","minutes":<N or
null>,"offset_minutes":<±N or null>,"per_video":{"1":<minutes>,…},"standard":{"median_s":…,"shortest_s":…,"longest_s":…,"refs":[…]}}'`
(`mode` "standard" with no number; "own" with `minutes` or `offset_minutes` or `per_video`). The plan then follows it (static §4
"The length", `cs-plan` step 6): **standard** is the agent's per-video length from the niche's pattern, **own** is the
user's number as the video's `target_length_s` (an offset is added to the agent's standard for that video). Nothing in the run is
planned or generated before this is stored.

**Then the language**, one more AskUserQuestion call (the first holds four questions; static §6 "The language of a video"; the user,
2026-11-11: "it has to ask user which language has the video's content to be"): header "Language", "In which language should the
videos be made?": **"English"** (the references' language, or the one most of them speak: said), then up to three languages the
conversation, the assets, the documents or the references' mix point to; "Other": any language of the live list by name or ISO code (one no ElevenLabs model lists is refused), or one language
per video ("1 English, 2 Spanish"). Before the question, print in chat, compactly, the languages the run's narration model lists
(`state.json → static.tts_model`; the ElevenLabs MCP's `list_models` row for it, loaded with ToolSearch (`select:mcp__elevenlabs__list_models`), else `T
tts models --run RUN`). Store with `T static language --run RUN --plan "<L1>[,<L2>…]"` (one language: every video of the batch);
it resolves each language against the live list and gives its facts: `official` false (the model's list does not hold it) is said in
one line, as ElevenLabs still voices it without a pronunciation guarantee (its first passage is a probe read against its script,
and the wrap-up names the pronunciation as not checked, static §6, §8); `unit`
(words, or characters for a language written without spaces), `direction` and `spaced` say what the captions can do (static §7);
`narrator_verified` says whether the locked narrator's voice is verified for it (said in one line when it is not: the narrator is a
lock, a clone may pick another).

- **A clone** (`state.json → cloned_from`; `/create-static clone <run>`, static §10): nothing is analysed; one
  AskUserQuestion call: header "Niche" (as above; never the old niche, `cloned_from.niche`), header "Narrator": **"Keep the narrator"**
  (the voice in a few words and the full path of `30-assets/voice/ref-neutral.wav`) or **"Pick a new narrator"** (five new samples at
  A6s), header "Visual style": **"Keep <V>'s style"** or another reference (as above), and header "Videos". Store with
  `T static lock --run RUN --niche "<niche>" [--style-ref <V> --replace]`; a new style rewrites the spec's style lock and text look from
  that reference's card; a new narrator: `T state --run RUN set static.new_voice=true` (A6s makes the samples); the new niche's
  references are written into the spec as above (static §2). Then a second AskUserQuestion call: header "Narration model":
  **"Keep <model>"** (the run's, `static.tts_model`, kept by the clone) or another from the live list (the options as the start's
  question gives them, `cs-start`; stored with `T tts model --run RUN --model-id <id> --source …`), and header "Language" (as above).
  The length is asked between the two calls' answers and the plan, as above, with the new niche's references' lengths (header
  "Length", the same two options), before A6s.
- Store the answer in `requested_videos`.

## Rules this phase owns (contract items 18, 20, 21)

18. **Examples: the user's own finished videos (optional).** They are asked for with the
    other inputs at the start. The folder may be empty or absent; then nothing changes.
    - They show the user's **house approach**: how their products are placed, used, continued across
      clips and blended, plus anything else they consistently do (text placement, pacing, sound,
      characters, endings).
    - When present, they are prepared and analysed (A1, A3) into
      `20-analysis/house-approach.md`, and every plan follows it (A4–A6s).
    - **Precedence:** the user's instructions for the run > the house approach > the pipeline's
      defaults. The house approach never overrides the hard rules: physical and logical
      correctness, the content rules of Static (static §11, §11b), the permission rule
      (item 15) and the text rule (item 6).
    - Examples are **study material only**: never uploaded, remade, cut into a new video, or used
      as client assets. Their own flaws (a physics cheat, a leftover watermark) are never copied.
20. **The pipeline is also the creative team** (`reference/creative-direction/`): a social-media
    and product-growth creative specialist, a mass-cognition engineer, a trend analyst, a creative
    director and a performance editor at once (in Static their product-growth lens becomes the
    team's story-and-attention lens, static §0). Every run writes its goal, its audience model and
    its trend read, and every brief says why the video will work. The creative layer never overrides the hard
    rules (items 6, 14, 15, 18 and the anomaly catalog); it decides which references, mechanisms and
    concepts win inside them.
21. **Brand guardrails decide what may be picked and what must be edited**
    (`reference/brand-guardrails.md`). Documents among the supplied assets (and in the references
    folder) that state the client's rules (no gore, two cans per day max, no competitor brands on
    screen, no ambassador likeness, no health claims, required disclaimers, …) are extracted into
    `30-assets/guardrails.md`, one quoted rule per line with its kind and default operation, plus
    the competitor, people, limit, wording and presentation lists they imply. Every reference gets
    a **guardrail audit** on its card: each hit located and classified **core** (the hook, turn,
    payoff, subject or premise depends on it; it is spoken in audio that returns; a hand or the
    action touches it; the edit would change what the video is about) or **peripheral** (set
    dressing, an untouched unit beyond the limit, a brand mark on an object that stays, a person
    who is swapped anyway, a caption line). Verdict: pick-clean, pick-and-edit (count reduced to
    the limit, competitor marks **removed, never blurred**, ambassador faces swapped without
    exception, captions rewritten, props removed) or dismiss (any core hit, with the rule). In
    Static the rules are plan invariants for the subjects, scripts and image plans
    (`brand-guardrails.md` §4, read at A6s). The user's run instructions outrank the guardrails; the guardrails outrank the house
    approach and the defaults; they never relax a hard rule; none is invented. **The pipeline has
    no content rules of its own beyond Static's two:** nothing religious or superstitious (static §11) and nothing indecent,
    gory or distressing (static §11b); without a guardrail document only those two and the image and speech services' own blocks apply,
    and nothing is blurred, softened or removed for taste.

## Never (this phase)

- Never upload an example, remake it or cut it into a new video, never take client assets from the
  examples folder, and never copy an example's flaws. Never let the house approach override the
  hard rules (contract item 18).
- Never pick a reference whose core a guardrail bans, and never dismiss one for a peripheral hit
  that an edit removes without changing what the video is about; never invent a guardrail, and
  never let one relax a hard rule (`brand-guardrails.md`).

## Hand-off

After A5 is answered and stored (`requested_videos`): `T state --run RUN set stage=counted next_skill=cs-plan`, then invoke Skill `cs-plan`.

After a compaction, or on `resume`, read `RUN/todo.md` first (item 38), then re-invoke the skill named in `RUN/state.json → next_skill`: its text may have been summarised away.
