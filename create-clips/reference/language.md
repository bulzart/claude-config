# The spoken language (a stream may be in German, Spanish or any other language)

The user, 2026-11-14: "not always all of the streams we will process will be in english, some will be in german or spanish too". The Whisper model in use is `medium` (the multilingual one, not `medium.en`): it reads German, Spanish and many more.
Until this rule the config forced `language: "en"`, so every chunk was decoded as English whatever was spoken. Now the language is found per stream.

## How the processor finds it (facts, no decision by an agent)
- `config.json -> whisper.language` is `auto`: Whisper names the language of each chunk itself. `transcript.json` carries `language`, `language_probability` and `language_source` (`detected`, `fallback` or `forced`).
- A guess it is not sure of (below `whisper.detect_min_probability`, 0.85: music, one short word, noise) is not trusted: the chunk is decoded in `whisper.fallback_language` (en) and the guess is kept as a fact (`detected_language`, `detected_probability`).
- The first sure guess on real speech (at least `whisper.detect_min_words`, 40, words) of a STREAM chunk becomes the run's language: `state.json -> settings.whisper.language_locked` (`language_locked_from` says where from). The chunks after it are told that language, so they are not guessed one by one.
  An ad chunk never sets it and never uses it (an advertisement is in its own language, often not the stream's).
- The user's own language wins over all of it: `T new-run --language de`, or `T state --run RUN set settings.whisper_override.language=de` before the chunks are processed; a language written in the config does the same for every run.
- The task is always **transcribe** (the words in the language spoken) and never translate (Whisper's translate-to-English task): the captions must show what the streamer says in the viewers' language, and a translation would lose word timing and exactness.
- A wrong lock or a wrong early guess: set the override as above and redo the chunks (`T ingest --run RUN --chunk RUN\10-media\Cnnnn\chunk.mp4 --force`, `docs/processing.md`).
- Where the agents see it: the `Spoken language` line at the top of `stream.md`, `language` in `T status`, `language` in every chunk row.

## What changes for the agents when the stream is not English
- Read the transcripts as spoken. The reports and the cards quote lines in the language spoken; the notes, briefs and reports the user reads are written in English.
- The research agent searches the streamer's world in that language too (its contract carries the spoken language) and gives each name's spelling as that language's fans write it.
- The lexicon (`replace`) fixes how Whisper spelled names and terms in that language.
- Profanity and slurs: `data/caption-masks.json` is an English list. In another language the agent adds the profanity and slurs it hears to `captions.mask_terms` when it reads the cues (the same rule, the same one-asterisk typing: `safety.md` section 3).
  With captions off the plan cuts around a spoken slur as always.
- Posting text (title, description, hashtags) is written in the language the stream is spoken in, the viewers' language, unless the user's notes say otherwise; the streamer's name and the topic stay as they are known.
- Both caption fonts draw German and Spanish letters; `T captions` lists `font_missing_glyphs` for a language the look's font cannot: Luckiest Guy (the box look) has no Slavic or Turkish letters, Cyrillic or Greek; Montserrat Bold (the no-box look) has the Slavic and Turkish letters but no Cyrillic or Greek.
