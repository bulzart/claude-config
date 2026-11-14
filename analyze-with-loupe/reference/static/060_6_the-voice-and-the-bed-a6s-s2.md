## 6 The voice and the bed (A6s, S2)

**The voice** (ElevenLabs, on the user's key; the user, 2026-11-09: "we will no longer use a locl model for audio generation, we will use
elevenlabs" (the local Qwen3-TTS and the Alibaba engine were removed that day), and 2026-11-11: "user also has to be able to pick which
elevenlabs model he wants to use too, not always v4, he might use v4 turbo or other": the run's **narration model** is the user's pick
at the start from ElevenLabs' live list ("The models", below), Eleven v4 `eleven_v4` unless they pick another; the 2026-11-09 words "we
will only use elevenlabs v4" gave way to that pick): one voice per run, the same in every video and in every language, locked once picked
(§10): more videos of the run and a clone that keeps it make no new samples; the toolkit refuses a new design or pick without
`--replace`. The sample line names nothing religious or superstitious (§11). Nothing of the narration runs on this PC (no GPU, no
memory guard); the key is the user environment variable `ELEVEN_API_KEY` (§9), and `T tts check` gives the account's plan, its
characters left and what the run's model honours.
- **Five samples at the stop of A6s** (the user, 2026-11-06: "the agent should suggest 5 versions and also the file path for each of them
  so the user can hear them and pick the one they like to be the voice of the videos"): five candidates written from the spec's voice
  profile (gender, age, tone, pace, accent; the references' register, five different takes on it). Each is a voice the account has
  (`T tts voices --run RUN --measure`, filtered by `--gender`, `--accent`, `--age`, `--use-case`: ElevenLabs' list of the account's
  voices, each voice's own preview recording read with the references' yardstick: its words a minute overall and while articulating,
  its pauses, its pitch; free) or a Voice Design sample (`T tts design --run RUN --text "<a line of 100 to 1,000 characters>"
  --instruct "<voice 1>" …`, the pace in the description's words, e.g. "a quick, measured pace"; billed per character of the line, once
  per design; a designed voice may read less expressively on Eleven v4 than in its sample, ElevenLabs' docs). The stop lists each with
  the full path of its file and its measured pace; the user listens and picks. A preview is made by an older model on its own text, so
  its pace is a first reading only: the voice's pace on the run's model with the video's own words is the probe's (below). The samples
  are heard in the language of the run's first video (the user, 2026-11-11: "we need the voices to be in that language too"): a Voice
  Design sample line is written natively in it (`T tts design --language <it>`), a listed voice carries the languages ElevenLabs gives
  for it (`verified_languages`, where the API has them) beside its preview, and a preview that is in another language than the video's
  is said so at the stop.
- **The pick** becomes the run's voice: `T tts voice --run RUN --voice-id ID` (an account voice; its preview kept as the voice's
  reference recording), `--sample K` (a design, saved to the account) or `--clone FILE …` (an Instant Voice Clone, when the plan allows
  it: not on the Free plan); `--settings '{"stability": S, "similarity_boost": M}'` the voice's own settings, and at most two
  `--emotion NAME="[tags]"` when the spec's delivery swings: the audio tags sent where a line of that emotion begins.
- **The models** (the user, 2026-11-11: "the user has to be asked on which elevenlabs model they want to use too (based on elevenlabs
  mcp live pull)"): the run's narration model is picked at the start (`awl-start`, the question "Narration model") from ElevenLabs'
  live list of the models that can do text to speech. The list is pulled live, never written from memory: the ElevenLabs MCP's
  `list_models` first (the `elevenlabs` server's tool `mcp__elevenlabs__list_models`: each row's `model_id`, name, languages, request
  limit and `can_do_text_to_speech`), and when the MCP does not
  answer (on this PC: the web shield's certificate error) `T tts models`, the same `GET /v1/models` through the toolkit's own key (a
  free read; it keeps the list in `<runs_root>/.elevenlabs-models.json` for the language checks and prints each model with its
  language count, its request limit and whether it is set up). The pick is stored with `T tts model --run RUN --model-id ID --source
  elevenlabs-mcp|toolkit-api` (`state.json → static.tts_model`); the model is the run's, like the narrator, and another one for a
  single video is the user's word only: a narration JSON's own `model_id` then overrides it (the order: the narration's, the run's, the
  voice's, the config's). A model changes what a request can carry, so every model's facts are
  recorded in `config.json → static.tts.elevenlabs.models.<id>`: its voice settings and their ranges, whether it takes `speed`, `style`,
  SSML breaks, speaker boost or audio tags, its request stitching (and how many ids), a seed, `language_code`, its `max_chars`, its
  credits per character, its pace levers and the docs the record was read from with the date. The toolkit refuses what the record says
  the model does not take (a setting, a tag or a pace key it lacks is refused, never dropped silently), and the agent's levers (§13) are
  the record's. **A model with no record is "not set up"** (`T tts models` shows `set_up: false`; `T tts model` refuses it): before it is
  used its facts are read from ElevenLabs' docs (the model's overview and capability pages, the text-to-speech and with-timestamps API
  pages, the request-stitching guide), never from memory, written into the config with their `source` and date, and `T tts check --run
  RUN` then shows what the run's model honours; only then is the pick stored. A voice's measured points (`state.json →
  static.voice.fit`) are per voice, model and language: a new model or a new language has no measured point yet, so its first passage
  is a probe (below, "The pace").
- **What Eleven v4 takes** (the model recorded first; ElevenLabs' docs, read 2026-11-09; `config.json →
  static.tts.elevenlabs.models.eleven_v4`): two voice settings only, `stability` (0 to 1, default 0.5: higher holds the delivery steadier from passage to passage, lower is more expressive)
  and `similarity_boost` (0 to 1, default 0.75: how close the read stays to the voice); **no speed, no style, no SSML pause**: any other
  setting is refused, never dropped silently. Delivery and pace are **audio tags**, natural-language words in brackets before the clause
  they colour, holding until the next tag: "[Building tension, measured pace]", "[Quick, light, playful pace]", "[slowly]", "[tense,
  cautious]", "[softly]"; pauses "[short pause]", "[pause]", "[long pause]", and the punctuation (ellipses slow a line down; full stops
  and dashes give rests). A tag must describe something heard ("[pacing]" or "[standing]" are not performed), its adherence is not
  perfect, it can be taken for a sound effect, and no tag has a documented length: every lever is measured on the voice before a
  narration leans on it (the probe, below). Words outside the brackets are spoken ("he said quietly" is said). Tags are billed as text.
- **The rule** (the user, 2026-11-09: "no edits should be done from our side on the elevenlabs generation, whether speeding up the audio generation, nor making cuts in it, we should only try to speed it up by instructing the elevenlabs tts model, or use different parameters to achieve our goal by leveraging the elevenlabs official guide we attained during the research phase, or for example do 2 or more different generations that differ in speed and use them for a certain need such as the video having some parts for slow pace narrations too, but do not edit the delivered generation without any exception"): the delivered audio is used exactly as it came. No
  stretch, no trim or cut, no compressor or voice chain, no loudness pass, no fade, no silence added between passages. Pace, pauses and
  length are set in the request: the voice, the settings, the words and their punctuation, and the tags; a part told at another pace (a
  slow, quiet stretch) is asked at that pace (its lines' own `delivery`), never slowed afterwards. Two exceptions, both the user's
  (2026-11-09), each a single constant change of the whole narration and nothing else:
  - **the level**: "allow only volume changing if it is too low or too high in comparison with the references data mined and analysed":
    `T tts say` reads the narration's loudness against the references named in its `pace.refs` (their `integrated_lufs` from A1); inside
    their range it stays as delivered; outside, one constant gain toward their median, never past a true peak of
    `config static.narration.true_peak_db` (-1 dBTP: no limiter, no compressor), and none when the voice's own peaks leave under
    `level_min_step_db` (0.5 dB) of room (the sidecar's `level`; the delivered file kept as `video-NN.delivered.wav`). 2026-11-09, video
    03: -23.5 LUFS against the family's -21.5 to -14.0 (median -18.9), +4.6 dB wanted, its true peak -1.1 dBTP left 0.1 dB: as delivered;
  - **the last resort for the pace, only on the user's yes**: "also add the speed tweak to the audio if we cannot achieve what we aim
    for by the model directly, but just speeding allowed up until a certain point ... just the speed, no compresion or something else
    that might change the voice quality or lose its color and pitch, and also no cuts,trims or similar, just carefull speed up"; then,
    the same day: "from now on the speech speedup from now on should only happen on user's permission, we do deliver all the work and
    then tell the user we're on these stats and for example target was 200wpm but we achieved 180 and we need a bit of speedup, it goes
    to the capcut looks at the project and only speedup on their permission never else, even though speedup is the last option we
    should try to achieve it directly on the generation". The pace is reached in the generation (the request levers, the checks before and after the narration, §13);
    a miss the levers could not close is delivered as it is, and the wrap-up gives the user the numbers (the measured pace, speaking
    and overall, against the point) and the speed-up that would close it. Only after the user has looked at the project and said yes:
    `T tts tempo --run RUN --video NN --tempo X --why "<the request levers tried and what they measured>" --user-ok "<the user's
    words>"` speeds the whole narration up by X (above 1, at most `config static.narration.tempo_max`, 1.05), its pitch and formants
    kept (rubberband; refused without it, and refused without `--user-ok`); the narration before it stays as `video-NN.pre-tempo.wav`,
    a later tempo starts from it, the lines', passages' and words' times follow, and the project is built again. The level rule then
    reads the sped narration again, since a time-stretch changes the loudness (video 03, 2026-11-09: -23.6 LUFS as delivered, -25.5
    after 1.05 with its true peak from -1.1 to -2.5 dBTP, then one +1.5 dB gain to -24.0; the sped file before the gain kept as
    `video-NN.pre-level.wav`). That speed-up was the user's own call; they then had it taken back ("in our video case just return it
    to normal, no speedup"): `T tts say --rejoin` puts the passages back end to end exactly as delivered.
  The CapCut project plays the narration at its own level (§7).
- **Passages** (`T tts say`): Eleven v4 "works best when used for paragraphs or passages of text" (ElevenLabs), so the lines are sent in
  passages of up to `config.json → static.tts.elevenlabs.passage_chars` (850; the plan's `tts.passage_chars` overrides) characters,
  never over the run's model's own `max_chars` a request (a model with a smaller limit stops a passage that passes it before anything
  is sent). A
  passage ends after a line marked `passage_break`, and after a line whose own delivery is not the narration's unless the next line
  shares it (a tag holds until the next one, so a line's own delivery ends with its passage); when the next line would pass the size, it
  ends at the largest planned `pause_after` in its second half (a `pause_after` is only that hint now: no silence is ever placed). Each
  passage starts with the delivery in force (the narration's `delivery`, a line's own, or its emotion's), a line's `tags_after` (e.g.
  "[long pause]") follows its words, and each passage is stitched to its neighbours as the model's record says (ElevenLabs' request
  stitching; Eleven v4, `stitching: ids`: the request ids of up to its `stitch_max_ids`, three, passages just before it made in the last
  110 minutes, else the previous passage's text; the next passage's text; a model recorded `text` sends the neighbours' text only, one
  recorded `none` sends each passage alone); its seed is the voice's (or the plan's `tts.seed`) times 1,000 plus its number, for a model
  that takes a seed. The timestamps endpoint gives each line's start and end
  (speech-to-text for a line its timing misses, flagged); the passages are placed end to end exactly as delivered (`video-NN.wav`; each
  passage kept as `video-NN/passage-PP.wav`, an MP3 also as delivered beside its decoded WAV, its request in `passage-PP.json`).
- **A video's narration**: `T tts say --run RUN --video NN` makes the passages not yet made with their present text (nothing is billed
  twice: `--only N,M` makes again the passages holding those lines, `--again` all of them, `--rejoin` none: it places the made ones end
  to end again and reads them); a passage-1 probe made exactly as `say` would make passage 1 is that passage. `T narration-words --run
  RUN --video NN` gives the timed words, the cues, the SRT, and per line what was heard against the script. A line that came out wrong (a
  missing or repeated word, another speaker, a tag spoken aloud) is made again with its passage (`--only <the line>`, billed), at most
  twice, then noted; a passage whose timbre sits far from the others (`voice_match.passages_below`, against the voice's reference
  recording) the same. The cues keep every word inside its own line's audio (`words_kept_in_their_line`; `T slideshow plan` does the
  same for the edit's captions): speech-to-text can pull the first word after a long pause into the silence before it (2026-11-08,
  video 03: "Inside." 0.76 s and "Day four." 0.44 s before their voice).
- **Characters** (credits): Eleven v4 bills one credit per character of the text sent, tags included (the account's `GET /v1/models`,
  2026-11-09: `character_cost_multiplier` 1.0); each passage's cost is recorded (`characters`, from ElevenLabs' cost header when it sends
  one). `T static forecast --part narration` gives the characters the plan sends against the characters left. `say` reads the characters
  left before it starts and makes a passage only when it fits (`--budget N` caps the call); when they run out it stops before the
  passage that does not fit (`--fill`: that passage made from its whole lines that still fit) and the narration is the passages made: a
  **partial narration**, flagged in the sidecar (`partial`: the lines made, the passage it stopped at and why). The timeline then leaves
  out the images and effects after the last narrated line (`T slideshow plan`: `images_after_narration`), and the wrap-up names it.
- The narration starts `lead_s` after the first frame and the video ends `tail_s` after it (config `static.narration`).

**The language of a video** (the user, 2026-11-11: "it has to ask user which language has the video's content to be ... even though all
references might be in english or mixed, we still analyse them and understand, but make the content in a specific language the user
wants"; "the languages have to be called from Elevenlabs mcp since we need the voices to be in that language too, and the video builds
the content around that language"). The references are read in whatever language they are in (A1 detects each one's speech language
itself) and what is carried over is their craft (§4); the video is made in the language the user picks:
- **The choice**: asked at A5 after the count, again with More videos and for a clone (`awl-analyze-study`, §10), once per video or
  once for the batch ("1 English, 2 Spanish"). The options are the languages of the run's narration model, from the live list (the
  ElevenLabs MCP's `list_models` rows, or `T tts models --run RUN --language L`, which marks the models that list a language). A language
  given by name or by ISO code is resolved by `T static language --run RUN --language L` against that list, never by guessing a code from
  a name's first letters: its code and name, whether the model lists it (`in_model`; one it does not list is `official: false`:
  ElevenLabs may still speak it, so the first passage is made as a probe and what speech-to-text hears of it is read against its script
  before the rest is made, and the wrap-up names its pronunciation as not checked, for the user to listen to; a language that no
  ElevenLabs model lists cannot be resolved and is refused, so "Other" is a language of the live list), whether it is written with spaces,
  its direction and its **unit**. `T static language --run RUN --plan "English,Spanish"` records the batch's languages (`static.language_plan`:
  each video added after it takes the next one) and `T static subjects --add … --language L` states one video's; a video's language is
  fixed once its narration exists (`T static subjects --set` refuses a change): another language is a new video.
- **The voice** is the run's narrator in every language (a lock, §10). When ElevenLabs lists verified languages for it
  (`verified_languages`), the video's language is checked against them: one that is not there is a fact the stop reports (the voice may
  keep its own accent into it) where the language is asked and at the voice stop, and the wrap-up names the pronunciation as not checked
  (§8). The request sends `language_code` only when the run's model
  honours it and lists the code; the narration JSON's `language` names the language and the text is written natively (§4).
- **The unit of the pace**: another language has words of another size, and some (Japanese, Chinese, Thai, Lao, Khmer, Burmese) have
  no spaces between words. The pace's `unit` is `words` or `characters`; the keys keep their names (`wpm_articulation`, `wpm_overall`).
  `T static units --run RUN --video NN` gives the ratio of the script's units to its glosses' English words and the references' English
  points converted by it (§4, §13). The speech-to-text reading of the narration (the heard words, the pace, the cues, the timed words)
  is made with the language's own Whisper code (`T static language` gives it; a language Whisper does not list is read with its
  automatic detection, said in the answer) and with the model of the config's `whisper_model`, `medium` for every speech step (the
  user, 2026-11-11: "use medium for everything", and 2026-11-14: "strictly always use medium model for anything"; the multilingual 769M-parameter model, about 3 times slower than `small`; a medium that cannot be loaded is an error with its real error, never replaced by another model). A reference written without spaces counts characters, so the set's words-based medians leave
  it out (`T static profile` lists it with the reason).
- **What stays English**: the glosses, the briefs and decision records, the forecast and every instruction. **What is in the video's
  language**: the narration, the title, the thumbnail's words, the captions, the labels (§5, §7, §12).
- **The fit points** (`state.json → static.voice.fit`, and the forecast's point) are per voice, model and language: the first video in a
  new language or on a new model has no measured point, the forecast says so, and you ask for a probe before you commit the pace
  (§13, the check before any generation).
- **Characters** (credits): the forecast counts the characters of the native text against the characters left (`credits`:
  `characters_to_send`, `characters_left`), so a language that writes the same story in more or fewer characters than English costs more
  or less; a model whose record has `credits_per_character` under 1 (v4 Turbo: 0.5, ElevenLabs' live list) spends fewer credits than
  characters, and what a passage cost is the sidecar's `characters`, from ElevenLabs' own cost header.

**The pace** (the user, 2026-11-08: "the narration speed and style should mirror the reference's data patterns ... we have to be very
sure that the workflow really achieves" it; then "every step should be taken carefully and thoroghfully, and nothing should turn out as
unexpected": the pace is aimed at a point the agent chose on purpose, §13, never left wherever it lands inside a band; and 2026-11-09: "do it in
the generation directly by giving the detailed specs and parameters"). The narration JSON's `pace` (§4: the family, the bands, the
`target` point, the tolerance) is what the narration is aimed at and measured against:
- **the measure**: words a minute overall (first to last word) and while articulating (`wpm_articulation`: the same words over the span
  with every pause of 0.25 s or more taken out), both from the words' times, read the same way in the references and in a narration (§13
  "The fair measure"; the older segment reading `wpm_speech` is kept only as a fact), on the narration as delivered;
- **the levers, all before generation**: the voice (its own pace on Eleven v4 is the main one: a voice reads about as fast as the audio
  it was made from), the delivery and pace tags where the run's model reads them (the narration's `delivery` leads every passage, e.g.
  "[quick, measured pace]"), the settings (and a `speed` or `style` setting where the model's record has one: a request lever like any
  other, sent in the generation and never applied to the delivered audio; SSML break tags are not used, the text is spoken text only,
  §4), and the words (shorter sentences and fewer
  commas read quicker; ellipses, dashes and full stops add rests). The levers are the run's model's: the numbers below are Eleven v4's
  (a model whose record lacks the audio tags has no `delivery`, and a tag sent to it is refused before anything is billed). Each is measured
  first: `T tts voices --measure` (free, the voices' own previews: a first reading), then `T tts probe --run RUN --video NN [--voice-id
  <a candidate>] [--delivery "<tags>"] [--settings '<json>']`: passage 1 made exactly as `say` would send it and read with the
  references' yardstick (articulating, overall, and `wpm_delivered`: the words over the delivered audio, its own silences in, the length a
  narration of these words will have); billed, and used by `say` as passage 1 when the plan's levers are the probe's, so it is paid once.
  A probe of another voice or tag is a candidate in `30-assets/voice/probes.json`; the run voice's points fill `state.json →
  static.voice.fit`. Two probes that differ in pace may serve different parts (a slow section asked slow). The probes are run by the
  main session, and no fresh reviewer ever generates (§13);
- **the decision** is the agent's (§13, the check before any generation), from the forecast (`T static forecast --part narration`: the
  point measured for the plan's levers, the predicted pace and length against the plan's point, the family and the characters left);
  after the narration the measured pace is read against the point (§13, the check after the narration). A miss is changed through the request first (another tag, setting or wording, the passages
  made again, billed); what the request levers cannot reach is delivered as it is, recorded with its reason, and offered in the
  wrap-up as the capped speed-up that would close it (above), made only on the user's yes. `T tts fit` learns the voice's point again from a made
  narration and `T narration-words`' heard words (the next video's forecast).
- **what the levers did** (video 03, George on Eleven v4, 2026-11-09; two test passages, the opening and a dense middle, measured
  speaking / overall wpm, the family's point 211.9 / 174.0): no tag 213.7 / 161.4 and 187.2 / 144.8; "[quick, measured pace]" 213.4 /
  169.9 and 192.4 / 152.7; "[quickly, steady narration]" 214.7 / 174.9 (the opening on the point) and 196.4 / 153.8; "[quickly, steady
  narration with short pauses]" 225.8 / 171.2 and 194.4 / 153.0; on the middle "[fast, brisk narration]" 196.8 / 158.9 (pause median
  0.46 s, the family's 0.44) and stability 0.3 no change (197.6 / 154.6); Daniel no tag 199.8 / 154.6 and 175.4 / 140.1 (slower than
  George on v4, though his preview read faster). The dense passage (1.50 syllables a word against the opening's 1.32; the family's 1.43)
  is read at the same syllables a minute, so it stays slower in words: a firmer tag on dense passages, the lighter one elsewhere. Pause
  tags after "Day one." (ElevenLabs' timing): "[pause]" 0.76 s, "[short pause]" 0.76 s, an ellipsis 0.08 s (no rest); "[long pause]"
  gave 1.6-2.6 s in the narration (the family's long pause is 0.92 s heard), so a section turn is "[pause]".
A narration is never fitted to a length afterwards: the length comes from the words at the voice's measured pace (§4).

**The bed** (ACE-Step 1.5): an instrumental under every video, also when the references are voice only (the user, 2026-11-06: "make
sure we try to generate instrumentals that fit the video content type and narration based on the data collected from the references, no
need to analyze their instrumentals too"). It is written from what the run already knows, never from analysing the references' music:
- **the content type**: the kind and niche of the references and of this video's subject (a life story, quick facts, a kids' story, a
  true case, a myth …): the palette;
- **the narration**: the spec's register and delivery in words (calm, wry, warm, ominous …), its pace (words per minute, the pauses) and
  the voice's pitch: the music leaves the narrator's band clear (no lead melody or busy part where the voice sits) and has no vocals,
  and nothing sacred or ritual (no hymn, choir singing sacred words, chant or church organ: §11), and no screams, sobs or sounds of
  pain (§11b);
- **the story's arc over time**: this video's beats (its script) at the narration's line times (the hook, the rise, the turn, the fall
  or payoff, the close) and each line's emotion: where the bed holds, builds, drops or darkens;
- **the pictures' rhythm**: the seconds per still and the cuts (§2), which a pulse can sit under without fighting;
- **the references' own sound, as the numbers A3 already has** (`T audio-profile`: a bed or none; when one, its tempo, beat strength and
  energy arc): a reference bed's tempo and energy are followed; its instruments and genre are not analysed.
Reason from these to the caption, as these worked examples do, never as a lookup: a brisk, wry life story with a rise and a fall → a
light orchestral underscore with a march pulse that swells to the peak and darkens with low strings at the fall (the run of 2026-11-06:
100 bpm under a 175-words-a-minute narrator); a calm bedtime story → soft celesta, harp and warm strings, slow and even, no drums; a dark
true case → low drones and sparse piano on a slow pulse that tightens at the reveal; quick surprising facts → light plucked and mallet
sounds, curious and bouncy. `40-briefs/music.json` (A6s), one track per video:
`{"tracks": [{"video": "NN", "caption": "<genre, mood and its arc, instruments, tempo in words; no vocals>", "duration": <lead +
narration + tail, set in S2>, "bpm": <n>, "seed": <n>, "why": "<each choice and the data it rests on>"}]}`, then in S2 `T music make
--run RUN` (every track in one model load; instrumental). The file carries its own fades (the track's `fade_in`, `fade_out`) and is
saved as 16-bit PCM WAV, the format the CapCut effects check showed playing (ACE-Step writes 32-bit float; the toolkit converts it).
**When the memory cannot hold it at full precision** (§9 "What a job needs"; the forecast's memory, §13): full precision is always
tried first, and int8 only after the memory guard stopped that try (the user, 2026-11-09, yes to "always try full precision first,
and use int8 only after the guard stops it": never from the forecast alone). Then `T music make --run RUN --quantization
int8_weight_only` has ACE-Step quantize its music model to int8 (the user, the same day: "int8 quantization of the ace step 1.5 model
if possible"; about 2.2 GB less, the full-size weights released before the next model loads); its answer and the bed's sidecar name
it with the full-precision try it follows (`int8_after`: when, the guard's stop and the free commit then, from the PC's memory
record since Windows started; null when the record holds none). A stopped full-precision answer carries the guard's line
(`worker.guard_stopped`, `worker.guard_line`). Measured that day at 10.7 GB free: int8 loaded and began generating where full precision was stopped loading, and was then
stopped at 8.69 GB; at full precision the bed needs about 13.6 GB free, int8 a little over 11.5.
**A long bed** (the user, 2026-11-07: "if acestep 1.5 max is 10 minutes, then we could do 2x8minutes for a 16minutes video i guess, or
5x5 for a 25 minutes"): ACE-Step makes at most 600 s per piece on this PC (`config.json → static.music.max_s`), so a longer track is made
in sections and joined end to end with crossfades (`crossfade_s`, default 4 s) into the one file the edit uses: either the agent's own
`"sections": [{"caption": "<this part's mood, the same instruments and tempo>", "duration": <s>}, …]` (one per part of the story, following the story's feeling as the plan was thought through (§4b, the user, 2026-11-13: from the start),
each at its place in the narration, so the bed supports what the part does; the section lengths add up to the track's duration plus one
crossfade per join), or, without them, the fewest
equal sections of at most `max_section_s` (480 s) under the track's caption. The fade-in is on the first section, the fade-out on the
last; the pieces stay in `30-assets/music/parts/`. `T music measure`'s level per second shows each join: no drop or jump around it.

**The bed's check and level** (S2): `T music measure --run RUN --video NN` gives the facts: the words speech-to-text hears in the bed
alone (a voice where none was asked), its loudness, its level per second and over each narration line (does it build and drop where the
beats do), its energy by band, and, as the CapCut project plays it (one constant gain, no ducking), its distance under the narration and
the narration's words heard with it against without it. The level is the agent's: every narration word heard the same with the bed
under it, and the bed still heard in the pauses; another level is tried with `--gain G` and kept as the image plan's `music_gain` (with
`"music": true`; else `config.json → static.music.gain`). A voice in the bed, or an arc that fights the story, is a new take (another
seed or a reworded caption, `T music make --run RUN --video NN`), at most two, by the run's QC fixes (off: none, noted in the brief). The
CapCut project, the only edit (no local render, §7), plays the bed at that gain without ducking (no CapCut ducking was checked), which is
the level the measure judged.

