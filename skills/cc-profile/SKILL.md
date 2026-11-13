---
name: cc-profile
description: /create-clips phase 2: understand the stream, the streamer and their audience, the topic or game or event it is about and what the internet is saying about it, the people on it; write the context brief every later agent reads. Internal to that command.
user-invocable: false
---

# cc-profile: get in touch with the stream (social research, not scientific)

> `CC`, `PY`, `T`, `RUN` as in cc-start.

## Read now
- `CC/reference/research-playbook.md` (the research wave, how to search, the brief's shape). Read it whole once.

## Steps
1. **Recon** (this session, small): from `RUN/00-inventory/stream.md`, `stream-meta.json` (titles and categories over the night), the chunk reports of the first chunk, the last chunk and three chunks in between (`RUN/10-media/Cnnnn/report.md`: what a reporter saw and heard, observations only)
   and their transcripts (`RUN/10-media/Cnnnn/transcript.txt`; or `T window --run RUN --from T --to T`), find out: who the streamer is (the channel name, how they are addressed), what the stream is about (the game, the event, the release, the trend), who is on with them (names heard), the mood.
   Write `RUN/20-analysis/recon.md` (10 to 20 lines, each with its rec time or its source). Fold in the user's `notes` from `state.json`.
2. **Research wave**: spawn the research agents **in one message** (up to `config.json -> agents.research_max`, 4: streamer and audience, the topic, the people, what is working as a clip). Each is a general-purpose agent, web only
   (WebSearch, WebFetch, Read, Write), briefed with: the channel, the stream's date, `recon.md`, the playbook's section for its job, its output file (`20-analysis/streamer.md`, `topic.md`, `people.md`, `clip-trends.md`), and these rules:
   research socially (what people are saying, joking about, hyping, arguing over and clipping; concrete examples, plain sentences, scale in words), tag every claim [W] with where it was seen, [S], [M] or [I], never invent a number, quote or title (write "not found"),
   `WebSearch` with `mode: "extended"` for anything recent, the month and year of the stream in the queries, several searches per turn, stop when the note can guide a clip decision, at most about 2 KB per section, no emoji. The agent never asks and never spawns agents.
   The agent returns three lines: the file it wrote, how sure it is, what it could not find.
3. **Synthesis** (this session): read the four notes, then write
   - `RUN/20-analysis/brief.md` (at most about 4 KB, the eight parts of the playbook: this stream, the streamer and their people, what travels for them, the topic's social pulse, people, touchy, lexicon fixes, how to judge a moment here);
   - `RUN/20-analysis/clip-criteria.md`: for THIS streamer and THIS topic, what makes a moment worth cutting (the kinds that travel, with what to look and listen for in the transcript, the frames and the chat), what is on brand, what to skip, and the five questions that decide a pick;
   - `RUN/20-analysis/lexicon.json`: `{"replace": [["Whisper wrote", "right spelling"], ...]}` from the people and the topic.
   Where a research agent found nothing, the brief says it plainly and leans on the transcript; a wrong claim in the brief is worse than a gap.
4. `T state --run RUN set stage=profiled next_skill=cc-scan`.

## Never
- Never write a research claim without its tag. Never copy a long text from a page: say it in a line and say where.
- Never turn the brief into a report with statistics: it is a briefing between friends who edit clips.
- Never skip the topic: a stream about a release, a tournament or a trend is judged against what everyone is saying about it.

## Hand-off
Invoke Skill `cc-scan`.
