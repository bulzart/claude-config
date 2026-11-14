# Game clipping: rounds, fights and what to keep

For broadcasts of a match. The streamer logic (a personality and a chat) does not apply; the logic here is **the match**: its units, what each unit meant, how much of it to show, and what to leave out.
The game's own profile (`reference/games/<game>.md`) says what a unit is in that game and what its highlights look like.

## 1. The units
- **Round-based games (CS2 and CS:GO, Valorant, Rainbow Six Siege):** the unit is the **round**. Everything in a match is a round, a break between rounds, or something that is not play (timeouts, tactical and technical pauses, side switch, map change, desk, ads).
- **Objective and fight games (Dota 2, League of Legends):** there are no rounds; the units are **fights** (from initiation to disengage), **objective events** (a tower or barracks, Roshan, Baron, a dragon), **phases** (laning, mid game, late game) and **swings** (a comeback, a throw, a base race).
- **Anything else:** the profile says it (a goal in Rocket League, a set in a fighting game); an unknown game gets its own profile first (`reference/games/generic.md`).

## 2. The match map (written before any unit is judged): `RUN/20-analysis/match-map.md`
Every stretch of the broadcast classified by **what it is**, with rec times: pre-show and desk, the match start, each map or game, each half, play (the rounds), breaks between rounds (buy phase), timeouts, tactical pauses, technical pauses,
the side switch, overtime, the post-match, ads or station breaks, **sponsorship and the like** (sponsor stings and bumpers, "presented by" cards, betting-odds or promo segments, sponsor reads, giveaways), replays. Replays are listed with the rec span they cover and, when you can tell, the moment they repeat (the **live** version is the canonical one).
**Sponsorship and the like is skipped totally** (the user, 2026-11-13): it is `non_play` and is cut from every video; it is not noted, not blurred and not kept as context. A small sponsor logo sitting on live play is not a stretch: it stays, because cutting it would cut the play.
Sources: the score and clock series from `hud-scan` (§3 below), the sheets (the scoreboard overlay is on screen almost all the time), the casters' words, the loudness and chat numbers.
The scan phase writes a skeleton from text only (the score resets, the long stretches with no score change, what the chunk reports say about them); the mining agents refine it in their `non_play`; the planner writes the final one.
**More than one match in the recording** (the user, 2026-11-14: "if the stream has 2, 3 different matches or more being played throughout the whole stream, do the video for each of the game in a separate capcut project"): a broadcast can play two, three or more different matches one after the other
(a **match** here is one contest between two teams, a BO1, BO3 or BO5; its maps or games are the **games** inside it). The match map then has one more level: each match (its two teams, the stage and the format, its rec range) with its games inside it.
What makes a stretch a new match is **the teams changing on the scoreboard**: a score reset alone is only the next map or game of the same match. The desk, the analysts, the pre-show of the next two teams, the breaks and the ads between two matches are `non_play`.
Before a stretch is called a new match, the team names are read in a frame just before and just after the change, and in the casters' words around it (`T window`).

## 3. Read the screen with the HUD tools
The scoreboard, the round timer or game clock, the kill feed and the replay badge are on screen in known places. Find them once and let the tools read them over the whole match:
- `cc.py grid-frame --run RUN --at T` and `cc.py hud-read --run RUN --at T --region x,y,w,h --numeric` to find and test a region (x,y,w,h as fractions of the frame; the 10% grid is drawn on the frame; `hud-read` keeps the picture the reader saw);
- `cc.py hud-scan --run RUN --spec RUN/20-analysis/hud/regions.json --step 1`: the text of every reader (the two scores, the clock) over the whole recording in one pass (OCR, skipped while the pixels do not change); one reader alone: `--region x,y,w,h --name score_a --regex ... --numeric`;
- `cc.py hud-states --run RUN --series score_a,score_b`: the score's changes as one time-ordered table with the state after each; `cc.py hud-slice --run RUN --name clock --from T --to T`: one reader's readings inside a range;
- `cc.py region-series --run RUN --region ... --step 0.5 --name feed`: how much a region changes over time (a kill-feed burst, a replay wipe, a banner).
They return facts (values and the times they changed). **You** read them: a score that went 7 to 8 at rec 4172.0 means a round ended there; a clock that restarted from 1:55 means the next round went live; two kills in the feed within 4 s are a multi-kill.
The regions found go in `RUN/20-analysis/hud/regions.json` (the profile phase writes it) so everyone uses the same ones.

## 4. Two writers: the scan gives facts and a first read, the planner gives the verdict
The mining agents read every unit of their block (starting from the chunk reports) and write a **card** (`RUN/20-analysis/blocks/block-NN.json -> units[]`): the facts and a first read. The planner checks the units it will use and writes the **verdict** into `RUN/20-analysis/rounds.json`.
Nobody else decides what is kept; a mining agent's `keep_hint` is advice. (The reports themselves decide nothing: they only say what a chunk shows.)
```json
{"id": "R14", "kind": "round", "rec_from": 4012.5, "rec_to": 4090.0, "live_from": 4031.0, "score_before": "7-6", "score_after": "8-6", "winner": "team name", "side": "CT", "how_it_ended": "bomb defused",
 "economy": "full buy vs force", "events": [{"rec": 4058.2, "what": "opening kill by X (AWP, B long)"}, {"rec": 4066.0, "what": "1v3 clutch begins"}, {"rec": 4087.4, "what": "defuse with 0.9 s left"}],
 "players": ["X", "Y"], "caster_peak": {"rec": 4087.6, "what": "caster shouts"}, "chat_peak": null, "replays": [[4094.0, 4104.5]],
 "impact": 9, "impact_why": "match point for the team on the other side, 1v3 clutch, last-second defuse",
 "highlight_types": ["clutch", "last-second-defuse"], "story": "saves the map", "keep_hint": "full", "keep_hint_why": "the clutch needs its setup (1v3 at 40 s left) and the defuse",
 "detail_value": "none", "confidence": "high", "evidence": ["hud score change 4090.0", "transcript 4086-4090", "sheet C0023 s5"]}
```
The planner's verdict for the same unit (`rounds.json -> units[]`: the card plus these fields):
```json
{"keep": "full", "keep_spans": [[4058.0, 4092.0]], "keep_why": "the clutch needs its setup (1v3 at 40 s left) and the defuse", "verified": "frames C0023 s4-s5, hud score 4090.0", "used_in": ["S03", "L01"]}
```
For a fight in Dota 2 or League: `kind: "fight"`, `game_clock`, the participants, the result (kills each side, towers, Aegis, who won the fight), the net worth swing as the scan reads it, the events, impact.

## 5. Impact and significance (a judgement written with its reason; the numbers are guides)
A unit matters for four kinds of reason; one is enough, two or more make it a keep:
- **Stakes:** it changed the score in a way that matters (map point, match point, the half-time score, a comeback round, the round that ended a streak, overtime, a pistol round that sets the economy, the last round of the map, a decider).
- **Highlight content:** kills and plays worth sharing on their own: an ace or 4k, a 1vN clutch, a multi-kill with an AWP or a rifle, a spectacular single kill (a flick, a noscope, a wallbang, a throwing-knife), a last-second defuse or plant, a fake that fooled everyone, a team execute that was perfect, a Black Hole that caught five, a Baron steal.
- **Story:** an upset (an eco round that beat a full buy), a comeback, a choke or throw by the favourite, a player's redemption, the moment a rivalry flared, a caster or crowd explosion.
- **Information value (the detail a viewer would lose):** a round that looks quiet but changes what follows: the economy reset after a save, a new strategy shown for the first time, a timeout and the round after it, a player swap or a technical pause that cost a team,
  a first kill of the match, the first time a map pick is played, a half-time score line.
A unit with none of these is **noise**: a clean execute with one or two kills that does not move the stakes, a routine eco, a dull farming stretch. Noise is dropped.

## 6. Keep levels (the planner gives every unit one, with the reason; the scan's `keep_hint` uses the same four words)
- **full:** the whole play from where it becomes interesting to the result (a clutch, an ace, a decisive fight).
- **trim:** the part that carries the unit: from the first contact (or the setup a viewer needs) to the result and one beat after it. The usual level for a good round.
- **flash:** a few seconds that keep the fact and cost almost nothing: the result moment and the scoreboard change (3 to 8 s). For a unit that is not a highlight but a viewer should not lose: a pistol round won cleanly, a half-time score, an economy-changing save, a timeout, a score card that explains the next round.
- **skip:** noise. Skipped units leave no hole as long as the score flow is clear from the units kept (a flash of the scoreboard between clusters is enough).
Never skip: the round or fight the story turns on, the last round of a map, an overtime round, a pistol round that changed who has the economy (it can be a flash), the unit just before a big clutch if the situation needs it (the setup belongs to the clutch).

## 7. How much of a unit to take
- **Start** at the first contact, or a few seconds before the first kill when the positioning is the point; not at the freeze time and not at the long walk to the site. For a clutch start when it becomes 1vN and the viewer can see the situation (the alive count, the time, the bomb).
  Keep a caster's tactical remark if it explains the play; skip the buy phase unless the economy is the story (then keep the broadcast's own economy graphic on screen for 3 to 5 s).
- **End** at the result (bomb exploded or defused, the last kill, time) plus 1 to 3 s for the reaction or the scoreboard update; a big play earns 2 to 3 s of the player cam or the crowd.
- **Replays:** the live action is canonical. Keep a replay only when it adds what the live view hid (the first-person view of a clutch, a different angle of a spectacular kill) and say why; a replay of what was just shown is cut (`replays` spans on the card).
- **Caster audio:** the casters are the narration and the hype: cut in a pause between sentences, let the scream land, keep the line that names the play. Captions follow them.
- **Context a viewer needs:** the scoreboard is always in the picture (the video is 16:9 and nothing is cropped), and the casters' words say the rest. A condensed match keeps the score line honest: when units were skipped in a row, the next kept unit still shows the score (a `flash` of the scoreboard between clusters if it does not).

## 8. From units to videos: long-form only (the user, 2026-11-13: no shorts at all in game mode)
Game mode makes **condensed matches** and nothing else: a map or a whole match as the viewer who missed it would want it. The rounds that matter at full or trim, the ones that explain at flash, the rest gone, in order, with the score always clear.
- **One video per map or per game** is the unit (`L01`, `L02` ...): a BO3 that went three maps gives three videos; a one-sided map or a quick best-of-one gives a brief video; a map or game that was dull gets a brief video, or none. A whole series is one video only when it is one match and its maps together add up to a brief one.
- **Different matches are never mixed** (the user, 2026-11-14): when the recording holds 2, 3 or more different matches, the games of each match are videos of their own, each in its own CapCut project (one production agent per video), numbered in the order they were played.
  Never two matches in one video or one project, however short each is, and never one game split between two videos: a border falls between games, at a map's result and the scoreboard update, never in the middle of a round or a fight.
  A match the recording holds only in part (it starts or stops in the middle of one) is a video of what is there when that is worth watching, otherwise none; its brief and the README say where it begins or ends. Each video's title, brief and spellings are its own match's teams.
- **Length** follows what the kept units add up to: a CS2 map is usually 10 to 20 minutes condensed, a Dota 2 game 15 to 30. About an hour is only a ceiling; never pad; never end in the middle of a round or a fight.
- **Chapters** at each half, overtime and every unit that is a headline (an ace, a clutch, a comeback), with output timestamps in `posting.md`.
- **Titles:** the teams, the map or game and the event (`<team> vs <team> | Map 2 Mirage | <event>`), the stage where it helps; no spoiler of the result in the title when the stage is an elimination or a final.
- Never: a short, a vertical (9:16) version, a highlight reel under 3 minutes, a sound effect, a text overlay.

## 9. What to write (the chunk reports the mining agents start from were made while the match was downloaded: observations only, `reporter.md`)
The profile phase: `hud/regions.json`, `recon.md`, `brief.md`, `clip-criteria.md`, `lexicon.json` (and `game-profile.md` for a game the library lacks). The scan phase: `hud/*.json` and `hud/states.txt`, the `match-map.md` skeleton, one block file per block with its unit cards.
The plan phase: `rounds.json` (every unit with its keep level, merged and checked), the final `match-map.md`, `portfolio.md` (the videos), and one brief per video (`40-briefs/<id>-brief.md`) with the units it uses, each unit's keep level and `keep_spans`,
the replays to cut, the context to show, the touchy spans. The wrap-up writes `deliverables/rounds.md` (`cc.py units-table`). The production agent decides the exact cuts inside the spans.
