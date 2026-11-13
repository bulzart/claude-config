# Research playbook: get in touch with the streamer, the niche and the moment (social, not scientific)

The user, 2026-11-12: the agents that pick and cut the moments must be "in touch" with the streamer, the topic of the stream and what is going on around it
(his example: a GTA VI release stream: what was circulating about GTA VI, how viral it went, its key points, how popular the game is, who plays it), and
"not in a scientific way, rather in a social way".

So: research like a fan who lives on the internet, not like an analyst writing a report. The question behind every search is "what are people saying,
joking about, hyping, arguing over and clipping right now, and why does it land with them?" Numbers are only there to give a sense of scale
("the trailer broke records in a day", "a few hundred thousand watching") and the facts (dates, names, titles) only where a wrong one would make a clip embarrassing.

## What the research agent brings back: four short sections of ONE note (`20-analysis/research.md`; the contract is `research-agent.md`)

The four parts below (R1 to R4) are the four SECTIONS of one note, about 1.5 KB each, written by the ONE research agent: take the points that can guide a clip decision, not the whole list.
Write the note the way you would explain it to a friend who is about to edit clips of this stream: plain sentences, real examples, no tables of statistics.
Every claim carries a tag: **[W]** seen on the web (say where: a Reddit thread, a post on X, a TikTok trend, a YouTube video and its comments, a news line),
**[S]** said in this stream (transcript, rec time), **[M]** from the model's memory (flag it: it may be old), **[I]** inference. Never invent a number, a quote or a clip
title: write "not found" instead.

### R1 The streamer and the people who watch them
- Who they are in two lines; what they stream (the categories they live in), how a normal stream goes, their recurring bits, catchphrases, running jokes, the
  names the community uses for things (emotes, nicknames, "the lore").
- Who watches: how the audience talks, what they spam in chat when something happens, what they love to see (the type of moment) and what bores them.
- What they promote or push on stream (sponsors, their own brand, merch, charity, a series, collabs): this is context, and it tells which moments are "on brand".
- What fans actually share: 5 to 8 real examples of moments of THIS streamer that travelled (title or description, roughly when, why it spread: the reaction, the line, the
  chaos, the guest). Which kinds of moments they are famous for.
- The last month: anything that changes how a moment will land (a feud, a ban, a big event, a new format, a milestone).
- How clip channels title and cut this streamer's moments (the hook lines, the caption look that is common).

### R2 The topic of the stream: the game, event, release, trend or news it is about
Start from the stream itself (the recon note says what it is: title, category, what the first minutes talk about), then go find how the internet is talking about that thing:
- What it is in a sentence, and why people care today (a release, a trailer, a tournament, a drama, a challenge, a holiday).
- What circulated in the last days and weeks: the memes, the reaction clips, the hot takes, the jokes everybody repeats, the arguments, the hype and the disappointment.
  How big it went (scale words are enough) and what the key points of the conversation are.
- Who is into it: the kind of people who play or follow it, what they want out of it, what they are afraid of, what the in-crowd says.
- The lingo: names, slang, abbreviations and running gags a clip must not get wrong, and how a captioner should spell them.
- What moments viewers of this topic are waiting for or will share (the beats: a first look, a bug, a funny death, a spoiler, a record).
- Other streamers' viral moments on the same topic (what already worked, so the clips here are fresh and not a copy).
- Anything touchy: a controversy, leaks or spoilers, a sensitive subject, a person or a brand not to joke about.

### R3 The people in this stream
Guests, co-streamers, mods, people the streamer talks about or reacts to. For each: who they are to the audience (one line), why they matter to this stream,
how they and the streamer fit together (friends, rivals, first meeting, running joke), what they are known for going viral with, how their name is spelled and how
Whisper may mishear it. If the recon cannot name the guest, search with what the transcript gives (a voice line, a handle, a game name) and say how sure it is.

### R4 What is working as a clip right now
For this streamer and this topic on TikTok, YouTube Shorts and Instagram Reels (and the long YouTube compilations): the formats and hooks that are travelling, typical lengths,
how the captions and sound look, what the top clip channels post, titles that pull. Five to eight real examples and what to learn from each.

## How to search (what works on this PC)
- `WebSearch` is the main tool; `mode: "extended"` for anything recent or niche (the stream is days old: the topic's news is fresh, a standard search returns last year's),
  "standard" for the basics. Add the month and year of the stream to the query. Run several searches in one turn.
- Phrase queries the way fans do: "<topic> reddit", "<topic> memes", "<streamer> reacts <topic>", "<streamer> best moments", "<topic> tiktok trend", "<streamer> clip went viral",
  "<topic> what everyone is saying", "<guest> <streamer> stream". Read the result titles and snippets as the social signal itself (a thread title, a post, a clip name, a comment
  quoted in an article is data).
- `WebFetch` a page worth reading (a news article, a Know Your Meme entry, a fan wiki, a thread that is not blocked). When a site blocks it, the search snippets are enough.
- One source per claim is enough for a clip: tag it and check its date (a thing from two years ago is background, not "what is circulating"); what two quick searches do not find is "not found". Never probe mirror sites or chase one claim across many pages.
- Stop when the note is rich enough to guide a clip decision, inside the budget (`config.json -> agents.research_calls` tool calls, about 3 to 4 minutes). Depth on the 10 things that matter beats a long list.

## The context brief (written once the notes are in; every later agent reads it first)
`RUN/20-analysis/brief.md`, at most about 4 KB, plain language:
1. **This stream:** channel, date, length, title and category changes, who is on, what it is about (3 to 5 lines).
2. **The streamer and their people:** who they are, who watches, what the audience loves and hates, what is on brand.
3. **What travels for them:** the 6 to 10 kinds of moment fans share (each with a real example in a few words).
4. **The topic's social pulse:** what everyone is saying and joking about, the key points, the scale in words, the lingo, what viewers wait for.
5. **People:** each guest or named person in a line, with the spelling to use.
6. **Touchy:** what must not be joked about or shown (religion and superstition always: avoided), what gets blurred (gore, distress, nudity, personal data), spoiler or controversy notes.
7. **Lexicon fixes:** `Whisper wrote -> right spelling` pairs for names, handles, game terms (they go into the captions' `replace`; with captions off the pairs are not needed).
8. **How to judge a moment here:** the five questions that decide a pick for this streamer and this topic.
The longer note stays beside it in `20-analysis/research.md` for an agent that needs the detail.
