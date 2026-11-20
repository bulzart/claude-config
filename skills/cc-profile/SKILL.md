---
name: cc-profile
description: /create-clips phase 2: understand the stream, the streamer and their audience, the topic or game or event it is about and what the internet is saying about it, the people on it (the ONE research agent's note, started in cc-start); write the context brief every later agent reads. Internal to that command.
user-invocable: false
---

# cc-profile: get in touch with the stream (social research, not scientific)

> `CC`, `PY`, `T`, `RUN` as in cc-start.

## Read now
- `CC/reference/research-playbook.md` (what the note's four sections hold, how to search, the brief's shape) and `CC/reference/research-agent.md` (the one agent: its budget, what to do while it works, how to collect it). Read each once.

## Steps
1. **Recon** (this session, small; the research agent has been working since `cc-start`, so this overlaps it): from `RUN/00-inventory/stream.md`, `stream-meta.json` (titles and categories over the night), the chunk reports of the first chunk, the last chunk and three chunks in between (`RUN/10-media/Cnnnn/report.md`: what a reporter saw and heard, observations only)
   and their transcripts (`RUN/10-media/Cnnnn/transcript.txt`; or `T window --run RUN --from T --to T`), find out: who the streamer is (the channel name, how they are addressed), what the stream is about (the game, the event, the release, the trend), who is on with them (names heard), the mood.
   Read the reports and the transcripts in ONE message (several Read calls together).
   Write `RUN/20-analysis/recon.md` (10 to 20 lines, each with its rec time or its source). Fold in the user's `notes` from `state.json`.
2. **Collect the research note**: `RUN/20-analysis/research.md` is written by the ONE research agent that `cc-start` started in the background (never a wave of agents; `config.json -> agents.research_max` is 1).
   Read it once now. Not back yet: send it `SendMessage` "write your note now with what you have" only when it has run about twice the expected time (six minutes or more), then read what it wrote.
   The recon found what the note does not cover (a guest, a topic the title did not say): one line to the agent by `SendMessage` (it resumes), or one targeted search of your own. `T state --run RUN set research.status=done`.
3. **Synthesis** (this session): read the note and the recon, then write
   - `RUN/20-analysis/brief.md` (at most about 4 KB, the eight parts of the playbook: this stream, the streamer and their people, what travels for them, the topic's social pulse, people, touchy, lexicon fixes, how to judge a moment here);
   - `RUN/20-analysis/clip-criteria.md`: for THIS streamer and THIS topic, what makes a moment worth cutting (the kinds that travel, with what to look and listen for in the transcript, the frames and the chat), what is on brand, what to skip, and the five questions that decide a pick;
   - `RUN/20-analysis/lexicon.json`: `{"replace": [["Whisper wrote", "right spelling"], ...]}` from the people and the topic, checked against what Whisper really wrote in the transcripts. How an entry is applied (every caption look, `T captions`): whole words only, the longest entry first, ONE pass (a replacement is never replaced again), punctuation written in `from` must be there and is replaced by the punctuation of `to` (write `["Jack,", "Chat,"]`, never `["Jack,", "Chat,,"]`; unwritten punctuation is kept), a capitalised word in `from` matches only that spelling, a lower-case one any case. A common word that is sometimes a name, or a guess about a plural or a possessive (`boobies` -> `Boobie's`: in "Yo boobies II" it was "Yo Boobie, I-I"), is never a bare pair: write it as an object with a context guard (`{"from": "Jack", "to": "chat", "not_before": ["of hearts"], "why": "..."}`; also `not_after`, `only_before`, `only_after`) or `"review": true` (held, not applied: the build agent confirms it per video); two entries with the same `from` and different `to` are both refused. Only when captions are on (`T state --run RUN get captions` is not `off`): with captions off nothing is typed on the picture, so the spelling fixes have no use (names in the brief and in `posting.md` still use the right spelling).
   Where the note found nothing, the brief says it plainly and leans on the transcript; a wrong claim in the brief is worse than a gap.
4. `T state --run RUN set stage=profiled next_skill=cc-scan`, then tick the profile items in `RUN/todo.md` and set its `Next:` line (rule 16).

## Never
- Never write a research claim without its tag. Never copy a long text from a page: say it in a line and say where.
- Never turn the brief into a report with statistics: it is a briefing between friends who edit clips.
- Never skip the topic: a stream about a release, a tournament or a trend is judged against what everyone is saying about it.
- Never start a second research agent or a research wave.

## Hand-off
Invoke Skill `cc-scan`.
