---
name: cc-profile-game
description: /create-clips game mode, phase 2: understand the broadcast (the game, the event, the teams, the casters, where the score and the clock are on screen) and what the internet says about the game and the match; write the context brief every later agent reads. Internal to that command.
user-invocable: false
---

# cc-profile-game: get in touch with the match (social research, not scientific)

> `CC`, `PY`, `T`, `RUN` as in cc-start.

## Read now
- `CC/reference/game-research-playbook.md` (recon, the research wave, the brief's shape). Read it whole once.
- After the recon says which game it is, the game's profile if the library has one: `CC/reference/games/<slug>.md` (`cs2`, `dota2`, `valorant`, `lol`); any other game: `CC/reference/games/generic.md` (how to write its profile).

## Steps
1. **Recon** (this session, small): from `RUN/00-inventory/stream.md`, `stream-meta.json` (the title and category over the broadcast), the chunk reports of the first chunk, the last chunk and three chunks in between (`RUN/10-media/Cnnnn/report.md`: what a reporter saw and heard, text on screen quoted as printed, nothing decided),
   their transcripts (`RUN/10-media/Cnnnn/transcript.txt`) and, where a report is thin, the overview sheets of those chunks, find out
   the game and its edition, the tournament and the stage, the teams and players (the names on the scoreboard, the names the casters say), the map or the draft, the format (BO1, BO3, BO5), the score now, the casters, and how the broadcast is built (a desk, replays, ads, a pre-show).
   Write `RUN/20-analysis/recon.md` (15 to 25 lines, each with its rec time or its source) and fold in the user's `notes` from `state.json`.
   Record `T state --run RUN set game="Counter-Strike 2" game_slug=cs2 event="<tournament and stage>"`.
2. **Find the HUD** (the numbers on screen are what the scan reads rounds and fights from): pick two or three live moments from the recon, `T grid-frame --run RUN --at T` for each, and measure the boxes (x,y,w,h as fractions of the frame) of
   the two team scores (Dota 2 and League: the two kill counts), the clock, the kill feed and the replay badge. Test every number box with `T hud-read --run RUN --at T --region x,y,w,h --kind digits --numeric` (look at the `image` it saves: it is what the reader saw;
   adjust `--scale`, `--threshold`, `--invert` until the text is right at three different times). Write `RUN/20-analysis/hud/regions.json`, which `hud-scan --spec` reads as it is (the `readers` list) and the agents read as the map of the screen:
   `{"frame": [1920,1080], "tested_at": [4031.0, 4410.5], "readers": [{"name": "score_a", "region": [0.43,0.03,0.04,0.05], "kind": "digits", "regex": "^\\d{1,2}$", "numeric": true, "note": "the left team's rounds"}, {"name": "score_b", ...}, {"name": "clock", "regex": "\\d{1,2}:\\d{2}", "numeric": true, ...}],
   "series": {"feed": [x,y,w,h], "replay": [x,y,w,h]}}` (`series` are the boxes for `region-series`: the kill feed and the replay badge, which are measured, not read).
   A broadcast with no readable scoreboard: write `"readers": []` and say so in `recon.md`; the scan then works from the casters' words and the sheets, and `state.json` gets `hud=none`.
3. **Research wave**: spawn the research agents **in one message** (up to `config.json -> agents.research_max`, 4: the game's social pulse, the event and its storylines, the teams and players, what is working as an esports clip), no `model` argument (they use the model the user picked).
   Each is a general-purpose agent, web only (WebSearch, WebFetch, Read, Write), briefed with: the stream's date, `recon.md`, the playbook's section for its job, its output file (`20-analysis/game.md`, `event.md`, `teams.md`, `clip-trends.md`), and these rules:
   research socially (what fans are saying, joking about, hyping, arguing over and clipping; concrete examples, plain sentences, scale in words), tag every claim [W] with where it was seen, [S], [M] or [I], never invent a name, a score, a number, a quote or a title (write "not found"),
   `WebSearch` with `mode: "extended"` for anything recent, the month and year of the match in the queries, several searches per turn, stop when the note can guide a clip decision, at most about 2 KB per section, no emoji. The agent never asks and never spawns agents.
   It returns three lines: the file it wrote, how sure it is, what it could not find.
4. **Synthesis** (this session): read the four notes, then write
   - `RUN/20-analysis/brief.md` (at most about 4 KB, the eight parts of the playbook; it names the game's profile file);
   - `RUN/20-analysis/clip-criteria.md`: for THIS game and THIS match, which plays and units are worth cutting (the kinds that travel, with what to look and listen for in the casters' words, the HUD and the frames), whose plays travel (the crowd's favourites, the storyline), what the stage's stakes add,
     what to skip, and the five questions that decide a keep;
   - `RUN/20-analysis/lexicon.json`: `{"replace": [["Whisper wrote", "right spelling"], ...]}` for every player, team and caster name and the game's terms;
   - `RUN/20-analysis/game-profile.md` **only** when the library has no page for this game: written from `games/generic.md`'s questions and the research. The library's pages are never edited from a run.
   Where a research agent found nothing, the brief says it plainly and leans on the broadcast; a wrong name or score in the brief is worse than a gap.
5. `T state --run RUN set stage=profiled next_skill=cc-scan-game`.

## Never
- Never write a research claim without its tag. Never copy a long text from a page: say it in a line and say where.
- Never turn the brief into a report with statistics: it is a briefing between friends who edit clips.
- Never guess a player's or a team's spelling: it comes from the scoreboard, the casters or a page, and it goes into the lexicon.

## Hand-off
Invoke Skill `cc-scan-game`.
