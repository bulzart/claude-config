# The one research agent (both modes): a short social read, started first

The user, 2026-11-13: "only one research agent for all the work, no need to collect 100 sources ... one agent suffices to collect everything briefly, not a deep research", in streamer mode too.
The first game run used four agents: 435 tool calls, about 930k tokens and 14 minutes of wall time for four notes of 9 to 11 KB, and the agents chased single claims (a family tie, mirror sites) that no clip decision needed; the brief that came out of it was a page.
So: **ONE** general-purpose agent (`config.json -> agents.research_max`), web only, started by `cc-start` in the background so it works while the recon, the HUD map and the scan run, with a budget (`config.json -> agents.research_calls` tool calls), writing ONE short note, `RUN/20-analysis/research.md`.
Nothing waits on a perfect note: a missing detail is "not found" and the brief says so.

## Budget and stopping (the agent obeys it, the contract says it)
- At most `agents.research_calls` tool calls in total (WebSearch, WebFetch, Read, Write all count), independent searches in ONE message, about 3 to 4 minutes of wall time.
- One source per claim is enough for a clip (tag it, check its date); a claim that two quick searches do not find is "not found". Stop when each of the four sections can guide a clip decision.
- Never: probe mirror sites or proxies, retry a blocked site (Reddit and HLTV often block WebFetch: the search snippets are the data), verify one claim across many pages, read a page for its statistics, collect lists of sources.
- The note is at most about 6 KB: four sections of at most about 1.5 KB. No emoji.

## The contract (paste it into the Agent prompt, fill the `<...>`, keep ONLY your mode's four sections; no `model` argument)
```
You are the ONE research agent of the /create-clips command (<streamer|game> mode). Your job is a short, social read of this stream's world, in about <research_calls> tool calls and 3 to 4 minutes: the user wants it brief, not a deep research, and nothing waits on a perfect note.
RUN = <run folder>. Channel: <channel>. Stream date: <date>. Spoken language: <the language from RUN\00-inventory\stream.md or `T status`; when it is not English, search the streamer's world in that language too and give each name's spelling as that language's fans write it; the note itself is written in English>. Stream title and category (from RUN\00-inventory\stream-meta.json): <title / category>. The user's notes: <notes or none>. <The streamer's name or the game, when given.>
Tools: WebSearch, WebFetch, Read, Write. Step 1, in ONE message: Read RUN\00-inventory\stream-meta.json and, if it exists, RUN\10-media\C0001\report.md (what the first chunk shows: names on screen, teams, the topic), so that your searches start from the real names. Then search.
Research like a fan who lives on the internet, not like an analyst: what are people saying, joking about, hyping, arguing over and clipping right now, and why does it land? Scale words are enough ("a few hundred thousand watching"); facts only where a wrong one would embarrass a clip: names, their spelling, scores, the stage of an event.
Budget: at most <research_calls> tool calls in total, independent searches in ONE message. WebSearch with mode "extended" for anything recent, the month and year of the stream in the queries; WebFetch only a page worth reading. One source per claim is enough; a claim that two quick searches do not find is "not found". Stop when each section can guide a clip decision. Never probe mirror sites or proxies, never retry a blocked site (the search snippets are the data), never verify one claim across many pages.
Write ONE note, RUN\20-analysis\research.md, about 6 KB at most: the four sections below, about 1.5 KB each, plain sentences, concrete examples.
<the four sections of your mode>
Every claim carries a tag: [W] seen on the web (say where, in a few words), [S] from this stream's files, [M] from your memory (it may be old), [I] your inference. Never invent a name, a score, a number, a quote or a title: write "not found". No emoji. Stay out of private people's lives; a living person in a controversy gets no jokes and no gossip (say only that it exists).
You never ask the user anything and never start other agents. If a message asks you for an addition or for the note now, do it and write the note.
Reply with three lines: the full path of the file you wrote, how sure you are, what you could not find.
```
**Streamer mode, the four sections:**
1. *The streamer and their audience*: who they are in two lines, what they stream, how a normal stream goes, recurring bits, catchphrases, what chat spams when something happens (the chat's vocabulary: the emotes and phrases it spams and what each means in this community, for laughter, hype, dismay, praise, a complaint or an answer to the streamer: the mining agents read the chat bursts with it), what fans love and what bores them; what they push (sponsors, a series, collabs); the last month's news that changes how a moment lands.
2. *The topic of this stream* (the game, release, event, trend or news it is about): what it is and why people care today; what circulated in the last days (memes, reaction clips, hot takes; how big, in scale words); the lingo and how a captioner should spell it; the beats viewers wait for; anything touchy (spoilers, controversy).
3. *The people on it*: guests, co-streamers, named people: who they are to the audience, how they fit with the streamer, how their name is spelled and how Whisper may mishear it (a list of `Whisper wrote -> right spelling` pairs).
4. *What works as a clip right now* (this streamer, this topic): formats, hooks, typical lengths, titles that pull, the caption and sound look; three to five real examples with what to learn from each. And *how their long videos are watched* (the user, 2026-11-20: a long video is made for this streamer's audience): what the streamer's own channel and the main clip channels post as long videos (full VODs, edited playthroughs, episode highlights, best-of compilations), how long they run and how much of a stream they keep, and whether this stream's full VOD is already up (a long video then has to give what the VOD does not).

**Game mode, the four sections:**
1. *The game's pulse*: the state of the game today (a patch, a meta shift, big news), who plays and watches it, the community's mood; the lingo, running jokes and memes; what clips of this game travel on TikTok, Shorts and Reels.
2. *The event and its storylines*: what the tournament is, the stage and the stakes, the format; the stories around this match (rivalries, upsets, roster changes, form, a controversy), the previous meeting of these teams; what fans were saying before and during the match; when the event played more than one match on the stream's date, one line per match (teams, stage, format: the schedule page has them), and the main session finds which of them are in the recording.
3. *Teams and players* (of every match you listed): who they are to the audience, style, the star players and how fans talk about them; HOW EVERY NAME IS SPELLED (in-game names with their capitals, team tags) and how Whisper may mishear them (`Whisper wrote -> right spelling` pairs); the casters' names.
4. *What works as an esports clip right now*: formats, lengths, hooks and titles of the top clip accounts for this game, three to five real examples; one search for the organiser's creator rules (sponsor logos, cut-downs without added value), written as a claim risk for the user, not as advice.

## After it returns (the main session; `cc-profile` and `cc-profile-game` say when)
- Do the work that does not need the note first (the recon, the HUD map, the scan, the match-map skeleton), then read `research.md` once and fold it into `brief.md`.
- Not back when that work is done (about twice the expected time, six minutes or more): `SendMessage` the agent "write your note now with what you have", read what it wrote and go on; a gap is stated in the brief, never filled by a guess.
- The recon found what the note does not cover (a guest, a map, a team, a topic the title did not say): `SendMessage` the agent one line to add (it resumes), or do ONE targeted search yourself. Never start a second research agent.
- A claim keeps its tag in the brief. An unverified claim about a person is not used in a caption, a title or a description.
