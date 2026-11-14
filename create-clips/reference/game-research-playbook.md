# Game mode research: get in touch with the match and its scene (social, like a fan, not like an analyst)

Game mode is for broadcasts of a game being played as a competition (a tournament stream such as BLAST Premier CS2, a Dota 2 match with casters, Valorant or League esports,
a ranked showmatch). The same spirit as the streamer playbook (`research-playbook.md`, which you do not need here): read the **social pulse** the way an internet fan does: what people say,
joke about, hype, argue over and clip. Numbers are only scale words ("one of the biggest events of the year", "a few hundred thousand watching"); facts matter where a mistake would embarrass the clip:
team names, player names, scores, the stage of the event.

Tags on every claim: **[W]** seen on the web (say where: a Reddit match thread, an X post, a YouTube comment section, HLTV or Liquipedia, a news line), **[S]** said or shown in this broadcast (rec time),
**[M]** model memory (flag it: it may be old), **[I]** inference. Never invent a name, a score, a quote or a clip title: write "not found".

## Step 1: recon of the broadcast (this session, from the run's data)
From `stream-meta.json` (title and game per chunk), the transcripts of the first chunk and a few windows, and the sheets:
which game (and which edition: CS2 vs CS:GO, Dota 2 patch), which tournament and stage (group, playoffs, grand final), which teams and players (tags on the scoreboard, names the casters say),
which map or draft is on, the format (BO1, BO3, BO5), the score now, the casters, and how this broadcast is built (a desk between matches, replays, ads, a pre-show), and whether it plays more than one match (the title changing, the casters naming new teams): each match with its teams and stage. Write `20-analysis/recon.md` (15 to 25 lines, with rec times).

## Step 2: the research note (ONE agent, started in `cc-start`, web only, one note `research.md` of four short sections; the contract and the budget are in `research-agent.md`)
- **R1 The game's social pulse** (section 1): the state of the game today (a new patch, a meta shift, big news, how big it is in scale words), who plays and watches it, the community's mood;
  the lingo and running jokes everybody uses; the memes; what clips of this game travel on TikTok, YouTube Shorts and Reels (aces, clutches, throws, caster meltdowns, crowd, rage, funny deaths ...) and how clippers title and caption them.
- **R2 The event and its storylines** (section 2): what this tournament is and why it matters, the stage and the stakes (qualification, a final, prize), the format; the stories around this match:
  rivalries, upsets, roster changes, a player's form, a streak, a controversy; the previous meeting of these teams; what fans were saying before the match and during it (match threads, X, comments).
- **R3 The teams and the players** (section 3): who they are to the audience, their style, the star players and how fans talk about them (nicknames, memes), their form; **how every name is spelled** (in-game names with their capitals,
  team tags) and how Whisper may mishear them (a lexicon of `Whisper wrote -> right spelling` pairs); the casters' names.
- **R4 What is working as an esports clip right now** (section 4): formats, lengths, hooks, caption styles and titles of the top clip accounts for this game; 5 to 8 real examples and what to learn from each.
Search the way fans do ("<tournament> <team> vs <team> reddit", "<player> ace clutch", "<game> highlights shorts", "<event> upset"), month and year in the query, `WebSearch` with `mode: "extended"` for anything recent.
Liquipedia and news pages often fetch; HLTV and Reddit often block `WebFetch`: then the search snippets are the data (never retry a blocked site, never probe mirrors).
One source per claim is enough for a clip; stop inside the budget (`config.json -> agents.research_calls` tool calls, about 3 to 4 minutes): the first game run's four agents spent 435 tool calls and 14 minutes and chased claims no clip decision needed.

## Step 3: the context brief (`RUN/20-analysis/brief.md`, at most about 4 KB; every later agent reads it first)
1. **The match** (each match of the recording with its rec range, when there are several): game, event, stage, format, teams, map or draft, score at each point you know, casters, the broadcast's structure.
2. **The game's pulse:** what everyone is saying and joking about, the lingo, what clips travel.
3. **The event and the storylines:** stakes, rivalries, what the audience hopes to see in this match.
4. **Teams and players:** each with the spelling to use and a line on how fans see them.
5. **What travels from this scene:** the 6 to 10 kinds of moment that get shared, each with a real example in a few words.
6. **Touchy:** religion and superstition (avoided; "god" as praise ("he is a god", "godlike") is a figure of speech: not highlighted, kept), real gore or distress (blurred where seen; game violence in the game's normal look is not gore),
   personal data on screen is left as it is (never blurred), slurs from players or chat (masked in captions; with captions off the plan cuts around them), commercial music in the broadcast (a claim risk), a living person in a controversy (no jokes).
7. **Lexicon fixes:** `Whisper wrote -> right spelling` pairs, checked against what Whisper really wrote in the transcripts (they go into the captions' `replace`; with captions off they are not needed).
8. **How to judge a round or a play here:** the five questions that decide a keep for this game and this stage.
The longer note stays beside it (`research.md`).
