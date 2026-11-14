---
name: create-clips-game-one-project-per-match
description: "user 2026-11-14, GAME MODE: a recording with 2, 3 or more different matches gives every game of every match its own video in its own CapCut project; matches never mixed; a new match = the teams change on the scoreboard"
metadata:
  node_type: memory
  type: feedback
  originSessionId: efec77d7-2d15-4e76-856d-85333ee657d3
  modified: 2026-11-14T04:30:22.174Z
---

User 2026-11-14, right after the streamer-mode long-video rule ([[create-clips-long-videos-whole-watches]]): "also add this logic to game mode too "if the stream has 2,3 different matches or more being played throughout the whole stream, do the video for each of the game in a separate capcut project"".

**Why:** a broadcast can play several matches one after the other (a whole day of an event). The game-mode docs assumed one match per recording, so teams, titles, research and videos could be mixed.

**How to apply:** game mode only; no script change, no new agent, no new schema field (one new `non_play` kind).
- Words: a **match** = one contest between two teams (BO1, BO3, BO5); its maps or games are the **games** inside it. The standing unit stays ONE VIDEO PER MAP OR GAME (a BO3 of three maps = three videos); a whole series is one video only when it is one match and its maps add up to a brief one. Never two matches in one video or one CapCut project, however short each is; never a game split between two videos; videos numbered in the order played.
- A new match is told by the TEAMS CHANGING ON THE SCOREBOARD; a score reset alone is only the next map or game. The profile phase looks at one frame just after each score reset and writes the matches (teams, stage, format, rec range) into recon.md and the match-map skeleton; a second or third match's teams go to the one research agent by `SendMessage` (its schedule line per match is in the contract). The miners record the stretch between two matches as `non_play` kind `match-change`; the planner's final match-map has a match level, checks the team names in a frame before and after, and records `videos.L01.match` and `videos.L01.game`; each brief names its match, game and sibling videos.
- A match the recording holds only in part (it starts or stops mid-match) is a video of what is there when that is worth watching, otherwise none; the brief and the README say where it begins or ends. The wrap-up README groups game videos by match.
- Lengths are unchanged: NO 25-minute-to-an-hour range in game mode (a condensed CS2 map is 10 to 20 minutes, a Dota 2 game 15 to 30; `game-clipping.md` "about an hour is only a ceiling").
- Where: `reference/game-clipping.md` sections 2 and 8, `game-mining.md`, `game-research-playbook.md`, `research-agent.md`, skills cc-profile-game, cc-scan-game, cc-plan-game, cc-wrapup, cc-start (mode text), router rule 5, README; checks in `tests/test_docs.py`.

Related: [[create-clips-pipeline]], [[scripts-gather-agents-decide]], [[create-clips-ads-recorded-agents-judge]].
