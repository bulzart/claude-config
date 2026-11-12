# Game clipping: rounds, fights and what to keep

For broadcasts of a match. The streamer logic (a personality and a chat) does not apply; the logic here is **the match**: its units, what each unit meant, how much of it to show, and what to leave out.
The game's own profile (`reference/games/<game>.md`) says what a unit is in that game and what its highlights look like.

## 1. The units
- **Round-based games (CS2 and CS:GO, Valorant, Rainbow Six Siege):** the unit is the **round**. Everything in a match is a round, a break between rounds, or something that is not play (timeouts, tactical and technical pauses, side switch, map change, desk, ads).
- **Objective and fight games (Dota 2, League of Legends):** there are no rounds; the units are **fights** (from initiation to disengage), **objective events** (a tower or barracks, Roshan, Baron, a dragon), **phases** (laning, mid game, late game) and **swings** (a comeback, a throw, a base race).
- **Anything else:** the profile says it (a goal in Rocket League, a set in a fighting game); an unknown game gets its own profile first (`reference/games/generic.md`).

## 2. The match map (written before any unit is judged): `RUN/20-analysis/match-map.md`
Every stretch of the broadcast classified by **what it is**, with rec times: pre-show and desk, the match start, each map or game, each half, play (the rounds), breaks between rounds (buy phase), timeouts, tactical pauses, technical pauses,
the side switch, overtime, the post-match, ads or station breaks, replays. Replays are listed with the rec span they cover and, when you can tell, the moment they repeat (the **live** version is the canonical one).
Sources: the score and timer series from `hud-scan` (`reference/game-clipping.md` §3), the sheets (the scoreboard overlay is on screen almost all the time), the casters' words, the loudness and chat numbers.

## 3. Read the screen with the HUD tools
The scoreboard, the round timer or game clock, the kill feed and the replay badge are on screen in known places. Find them once and let the tools read them over the whole match:
- `cc.py grid-frame --run RUN --at T` and `cc.py hud-read --run RUN --at T --region x,y,w,h` to find and test a region (x,y,w,h as fractions of the frame; the 10% grid is drawn on the frame);
- `cc.py hud-scan --run RUN --region ... --from T --to T --step 1 --name score|timer|clock|killscore --kind digits [--numeric --regex ...]`: the text of a region over time (OCR, skipped while the pixels do not change);
- `cc.py region-series --run RUN --region ... --step 0.5 --name feed|replay|banner`: how much a region changes over time (a kill-feed burst, a replay wipe, a banner).
They return facts (values and the times they changed). **You** read them: a score that went 7 to 8 at rec 4172.0 means a round ended there; a timer that reset to 1:55 means the next round went live; two kills in the feed within 4 s are a multi-kill.
Write the regions you found in `RUN/20-analysis/hud/regions.json` so everyone uses the same ones.

## 4. The unit card (one per round or fight): `RUN/20-analysis/blocks/block-NN.json -> units[]`
```json
{"id": "R14", "kind": "round", "rec_from": 4012.5, "rec_to": 4090.0, "live_from": 4031.0, "score_before": "7-6", "score_after": "8-6", "winner": "team name", "side": "CT", "how_it_ended": "bomb defused",
 "economy": "full buy vs force", "events": [{"rec": 4058.2, "what": "opening kill by X (AWP, B long)"}, {"rec": 4066.0, "what": "1v3 clutch begins"}, {"rec": 4087.4, "what": "defuse with 0.9 s left"}],
 "players": ["X", "Y"], "caster_peak": {"rec": 4087.6, "what": "caster shouts"}, "chat_peak": null, "replays": [[4094.0, 4104.5]],
 "impact": 9, "impact_why": "match point for the team on the other side, 1v3 clutch, last-second defuse",
 "highlight_types": ["clutch", "last-second-defuse"], "story": "saves the map", "keep": "full", "keep_spans": [[4058.0, 4092.0]], "keep_why": "the clutch needs its setup (1v3 at 40 s left) and the defuse",
 "detail_value": "none", "confidence": "high", "evidence": ["hud score change 4090.0", "transcript 4086-4090", "sheet C0023 s5"]}
```
For a fight in Dota 2 or League: `kind: "fight"`, `game_clock`, the participants, the result (kills each side, towers, Aegis, who won the fight), the net worth swing as you read it, the events, impact, keep.

## 5. Impact and significance (your judgement, written with its reason; the numbers are guides)
A unit matters for four kinds of reason; one is enough, two or more make it a keep:
- **Stakes:** it changed the score in a way that matters (map point, match point, the half-time score, a comeback round, the round that ended a streak, overtime, a pistol round that sets the economy, the last round of the map, a decider).
- **Highlight content:** kills and plays worth sharing on their own: an ace or 4k, a 1vN clutch, a multi-kill with an AWP or a rifle, a spectacular single kill (a flick, a noscope, a wallbang, a throwing-knife), a last-second defuse or plant, a fake that fooled everyone, a team execute that was perfect, a Black Hole that caught five, a Baron steal.
- **Story:** an upset (an eco round that beat a full buy), a comeback, a choke or throw by the favourite, a player's redemption, the moment a rivalry flared, a caster or crowd explosion.
- **Information value (the detail a viewer would lose):** a round that looks quiet but changes what follows: the economy reset after a save, a new strategy shown for the first time, a timeout and the round after it, a player swap or a technical pause that cost a team,
  a first kill of the match, the first time a map pick is played, a half-time score line.
A unit with none of these is **noise**: a clean execute with one or two kills that does not move the stakes, a routine eco, a dull farming stretch. Noise is dropped.

## 6. Keep levels (every unit gets one, with the reason)
- **full:** the whole play from where it becomes interesting to the result (a clutch, an ace, a decisive fight).
- **trim:** the part that carries the unit: from the first contact (or the setup a viewer needs) to the result and one beat after it. The usual level for a good round.
- **flash:** a few seconds that keep the fact and cost almost nothing: the result moment and the scoreboard change (3 to 8 s). For a unit that is not a highlight but a viewer should not lose: a pistol round won cleanly, a half-time score, an economy-changing save, a timeout, a score card that explains the next round.
- **skip:** noise. Skipped units leave no hole as long as the score flow is clear from the units kept (a flash of the scoreboard between clusters is enough).
Never skip: the round or fight the story turns on, the last round of a map, an overtime round, a pistol round that changed who has the economy (it can be a flash), the unit just before a big clutch if the situation needs it (the setup belongs to the clutch).

## 7. How much of a unit to take
- **Start** at the first contact, or a few seconds before the first kill when the positioning is the point; not at the freeze time and not at the long walk to the site. For a clutch start when it becomes 1vN and the viewer can see the situation (the alive count, the time, the bomb).
  Keep a caster's tactical remark if it explains the play; skip the buy phase unless the economy is the story (then the economy overlay for 3 to 5 s).
- **End** at the result (bomb exploded or defused, the last kill, time) plus 1 to 3 s for the reaction or the scoreboard update; a big play earns 2 to 3 s of the player cam or the crowd.
- **Replays:** the live action is canonical. Keep a replay only when it adds what the live view hid (the first-person view of a clutch, a different angle of a spectacular kill) and say why; a replay of what was just shown is cut (`replays` spans on the card).
- **Caster audio:** the casters are the narration and the hype: cut in a pause between sentences, let the scream land, keep the line that names the play. Captions follow them.
- **Context a viewer needs:** a short must make the score and the stakes clear in its first seconds (the scoreboard in view is enough; a unit from the HUD's side of the frame is cropped out only when the vertical crop loses it, then use the fit layout: `game-edit-craft.md`).

## 8. From units to videos
- **Shorts (up to 3 minutes):** the best plays one by one (an ace, a clutch, a spectacular kill, a throw, a caster explosion) at 15 to 60 s; a **round story** when a whole round is the clip (the 1v3 on match point: setup, play, result, reaction); a **best plays of the map** compilation of 3 to 6 plays at 60 to 150 s when each play is short;
  a **funny and fails** cut when the scene has it. As many as are good; the same play is never two shorts unless the hooks differ.
- **Long-form (the condensed match):** a map or a whole match as the viewer who missed it would want it: the rounds that matter at full or trim, the ones that explain at flash, the rest gone, in order, with the score always clear. About an hour is a guide, a CS2 map is usually 10 to 20 minutes condensed and a Dota 2 game 15 to 30;
  never end in the middle of a round or a fight. One video per map or per game is the natural unit; a theme video ("every clutch of the day") is fine when the day earned it. Chapters at each map, half, overtime and big round.
- **Titles:** the play and the people first (`<player> <what happened> vs <team> | <event>`), the stakes where they help, no spoiler of the result in the first caption of a short.

## 9. What to write
`match-map.md`, `hud/regions.json`, the unit cards (in the block files), then the planner's `rounds.json` (every unit with its keep level, merged and checked), `portfolio.md` (the videos), and one brief per video (`40-briefs/<id>-brief.md`) with the units it uses, each unit's keep level and `keep_spans`,
the replays to cut, the context to show, the touchy spans. The production agent decides the exact cuts inside those spans.
