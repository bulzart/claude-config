# Counter-Strike 2 (and CS:GO) match broadcasts

Written from model memory [M]: the broadcast wins over this page. Where the page and the picture disagree, trust the picture and note it.

## The match
- Two teams of five on one map at a time; a series is BO1, BO3 or BO5 (the veto picks the maps). A map is rounds: the first team to **13** wins (12 rounds per half, the sides swap after round 12; CS:GO's older format was first to 16).
  At 12-12 overtime follows (in tournaments: 6 rounds, sides swap after 3, first to 4 OT rounds wins; it repeats if tied).
- A round: **freeze time** (the buy phase, players cannot leave their spawn), then **live** with 1:55 on the clock. The Terrorists plant the bomb at site A or B (the bomb then explodes after 40 s); the Counter-Terrorists defuse it.
  A round ends when: a whole team is eliminated; the bomb explodes (Terrorists win); the bomb is defused (Counter-Terrorists win); the clock runs out with no plant (Counter-Terrorists win).
- **Economy:** money comes from wins, losses (a bonus for a losing streak) and kills. **Pistol rounds** are round 1 and round 13 (both teams on pistols). Buy types: **eco** or **save** (buy little or nothing), **force** (a partial buy on low funds), **full buy**.
  An eco round that beats a full buy is an upset and a story; a saved weapon set decides the next round's economy.

## What the broadcast shows
- Observer HUD: the **scoreboard top centre** (team names or logos with each team's round score on either side of the round clock; the bomb icon and its countdown when planted), alive-player bars at both sides, the **kill feed top right**, the player card bottom centre
  (name, health, weapon), the radar top left. During an instant replay a **replay badge or wipe** appears. Places differ by broadcaster: always measure on a real frame (`T grid-frame`).
- The observer view follows one player's point of view or an overview; player cams and a caster desk appear in corners or between rounds.
- Structure of a broadcast: pre-show and desk, map intro, live rounds with instant replays after big kills, tactical timeouts (a team's short pause between rounds), half-time after round 12, technical pauses, the map result, the desk between maps, the post-match; ad breaks that the recorder skips show up as gaps in the chunk table.

## What a highlight is (the words you will hear)
**Ace** (five kills in one round by one player), 4k, 3k, a multi-kill with a rifle or an AWP; a **clutch** (the last player alive against X: 1v1 is common, 1v3 and up is rare and shared); an AWP **flick**, a **noscope**, a **wallbang**, a kill through smoke;
a **spray transfer**; a **ninja defuse** (defusing while enemies are close), a **last-second defuse or plant**; a **retake** (the defenders take the site back); a perfect team **execute**; a **fake** that fools the other team; a knife or taser kill;
the **opening duel** that decides a round; **trade** kills; the **throw** (a won round lost: 4v1 lost, a lead given away); a lost 1v5 that nearly worked; a caster who loses their voice; a crowd that explodes.
Lexicon: eco, force, save, rotate, retake, execute, default, lurk, entry, trade, peek, prefire, outplayed, cracked, diff, "he's him", match point, map point, decider, half-time, tech pause, timeout, anti-eco, mid control, molly, flash, smoke.

## The unit: the round
- A round's end is the score change on the scoreboard (it can update a few seconds after the bomb result: use the frames). Its start is where the clock leaves freeze time and runs from 1:55.
- **Quiet but not noise:** the pistol rounds (round 1, round 13) when the result sets the economy (a `flash` at least), the round after a big clutch or an upset (the economy swing), a save round that decides the next one, a timeout and the round after it, the first kill of a map, a half-time score line.
- **Usually noise:** a standard execute with one or two kills that does not move the stakes, an eco round the eco team simply loses, a default that ends in a clean trade-out.
- **Never skip:** the round the map turns on, map point and match point rounds, overtime rounds, the last round of a map, the round a story is built on.
- **Traps:** replays show kills twice (live is canonical); a scoreboard that updates late; an OCR that reads 1 as 7; the sides swapping at half-time (what "CT" means changes: use the team names); a paused clock; the desk replaying an earlier round while the live game waits.
