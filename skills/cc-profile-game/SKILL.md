---
name: cc-profile-game
description: /create-clips game mode, phase 2: understand the broadcast (the game, the event, the teams, the casters, where the score and the clock are on screen, what is live and what is replay) and what the internet says about the game and the match (the ONE research agent's note, started in cc-start); write the context brief every later agent reads. Internal to that command.
user-invocable: false
---

# cc-profile-game: get in touch with the match (social research, not scientific)

> `CC`, `PY`, `T`, `RUN` as in cc-start.

## Read now
- `CC/reference/game-research-playbook.md` (recon, what the note's four sections hold, the brief's shape) and `CC/reference/research-agent.md` (the one agent: its budget, what to do while it works, how to collect it). Read each once.
- After the recon says which game it is, the game's profile if the library has one: `CC/reference/games/<slug>.md` (`cs2`, `dota2`, `valorant`, `lol`); any other game: `CC/reference/games/generic.md` (how to write its profile).

## Steps
1. **Recon** (this session, small; the research agent has been working since `cc-start`, so this overlaps it): from `RUN/00-inventory/stream.md`, `stream-meta.json` (the title and category over the broadcast), the chunk reports of the first chunk, the last chunk and three chunks in between (`RUN/10-media/Cnnnn/report.md`: what a reporter saw and heard, text on screen quoted as printed, nothing decided),
   their transcripts (`RUN/10-media/Cnnnn/transcript.txt`) and, where a report is thin, the overview sheets of those chunks (read them in ONE message, several Read calls together), find out
   the game and its edition, the tournament and the stage, the teams and players (the names on the scoreboard, the names the casters say), the map or the draft, the format (BO1, BO3, BO5), the score now, the casters, and how the broadcast is built (a desk, replays, ads, a pre-show).
   **A recording can hold more than one match** (the user, 2026-11-14: two, three or more different matches played through the stream): the title and category changes, a desk or a pre-show between games and the casters naming new teams are the hints; write each match you find with its teams, stage, format and rec range.
   **Live or replay is not said from a report or one frame**: write "looks like a replay (unverified)" until the replay-badge series of step 3 has been read (the first game run called two live rounds replays from one frame and a report; the mining agents corrected it).
   Write `RUN/20-analysis/recon.md` (15 to 25 lines, each with its rec time or its source) and fold in the user's `notes` from `state.json`.
   Record `T state --run RUN set game="Counter-Strike 2" game_slug=cs2 event="<tournament and stage>"`.
2. **Find the HUD** (the numbers on screen are what the scan reads rounds and fights from): pick two or three live moments from the recon, `T grid-frame --run RUN --at T` for each (the frames in ONE call), and measure the boxes (x,y,w,h as fractions of the frame) of
   the two team scores (Dota 2 and League: the two kill counts), the clock, the kill feed and the replay badge. Test every number box with `T hud-read --run RUN --at T --region x,y,w,h --kind digits --numeric` (look at the `image` it saves: it is what the reader saw;
   adjust `--scale`, `--threshold`, `--invert` until the text is right at three different times). Write `RUN/20-analysis/hud/regions.json`, which `hud-scan --spec` reads as it is (the `readers` list) and the agents read as the map of the screen:
   `{"frame": [1920,1080], "tested_at": [4031.0, 4410.5], "readers": [{"name": "score_a", "region": [0.43,0.03,0.04,0.05], "kind": "digits", "regex": "^\\d{1,2}$", "numeric": true, "note": "the left team's rounds"}, {"name": "score_b", ...}, {"name": "clock", "regex": "\\d{1,2}:\\d{2}", "numeric": true, ...}],
   "series": {"feed": [x,y,w,h], "replay": [x,y,w,h]}}` (`series` are the boxes for `region-series`: the kill feed and the replay badge, which are measured, not read).
   A broadcast with no readable scoreboard: write `"readers": []` and say so in `recon.md`; the scan then works from the casters' words and the sheets, and `state.json` gets `hud=none` (skip step 3's scan).
3. **Start the screen scan now, in the background, all together in ONE message** (the moment `regions.json` exists nothing else is needed, and it runs while the research note is still being written and the recon is checked; the cost is decoding the video, so the passes run side by side):
   - `T hud-scan --run RUN --spec RUN/20-analysis/hud/regions.json --step 1` (`run_in_background`: every reader, the scores and the clock, over the whole recording in one pass; about one minute per ten minutes of video on this PC, so about 12 minutes for a two-hour match);
   - `T region-series --run RUN --region <series.replay> --step 1 --name replay` and the same for `--region <series.feed> --step 1 --name feed` (`run_in_background`; they write `20-analysis/hud/replay-series.txt` and `feed-series.txt`).
   Then, when they have finished, `T hud-states --run RUN --series score_a,score_b --stable 3` (seconds). Read the replay-badge series now and correct the recon: which stretches are live and which are replays, in numbers.
   Every reset of the score is the next map or game of the same match, or a new match: look at one frame just after each reset (all the frames in ONE call) and read the team names on the scoreboard; where they changed, it is a new match. Write the matches (teams, stage, format, rec range) into `recon.md` and the `match-map.md` skeleton.
   `cc-scan-game` checks that these files exist and only runs what is missing.
4. **Collect the research note**: `RUN/20-analysis/research.md` is written by the ONE research agent that `cc-start` started in the background (never a wave of agents; `config.json -> agents.research_max` is 1).
   While it finishes, write the `match-map.md` skeleton (the next phase's step 2) from the scan files. Read the note once when it is there. Not back yet after about twice the expected time (six minutes or more): `SendMessage` it "write your note now with what you have", then read what it wrote.
   The recon found what the note does not cover (a team, a map, a player the title did not say, the teams of a second or third match): one line to the agent by `SendMessage` (it resumes), or one targeted search of your own. `T state --run RUN set research.status=done`.
5. **Synthesis** (this session): read the note, then write
   - `RUN/20-analysis/brief.md` (at most about 4 KB, the eight parts of the playbook; it names the game's profile file; with several matches in the recording its first part lists each match with its teams and rec range);
   - `RUN/20-analysis/clip-criteria.md`: for THIS game and THIS match, which plays and units are worth cutting (the kinds that travel, with what to look and listen for in the casters' words, the HUD and the frames), whose plays travel (the crowd's favourites, the storyline), what the stage's stakes add,
     what to skip, and the five questions that decide a keep;
   - `RUN/20-analysis/lexicon.json`: `{"replace": [["Whisper wrote", "right spelling"], ...]}` for every player, team and caster name and the game's terms, checked against what Whisper really wrote in the transcripts. Only when captions are on (`T state --run RUN get captions` is not `off`); with captions off nothing is typed on the picture, so the pairs have no use (names in the brief and in `posting.md` keep the right spelling);
   - `RUN/20-analysis/game-profile.md` **only** when the library has no page for this game: written from `games/generic.md`'s questions and the research. The library's pages are never edited from a run.
   Where the note found nothing, the brief says it plainly and leans on the broadcast; a wrong name or score in the brief is worse than a gap.
6. `T state --run RUN set stage=profiled next_skill=cc-scan-game`, then tick the profile items in `RUN/todo.md` and set its `Next:` line (rule 16).

## Never
- Never write a research claim without its tag. Never copy a long text from a page: say it in a line and say where.
- Never turn the brief into a report with statistics: it is a briefing between friends who edit clips.
- Never guess a player's or a team's spelling: it comes from the scoreboard, the casters or a page, and it goes into the lexicon.
- Never call a stretch a replay or live on a report or one frame: the replay-badge series and a few frames say it.
- Never start a second research agent or a research wave.

## Hand-off
Invoke Skill `cc-scan-game`.
