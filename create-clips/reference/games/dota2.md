# Dota 2 match broadcasts

Written from model memory [M]: the broadcast wins over this page. Where the page and the picture disagree, trust the picture and note it.

## The match
- Two teams of five (Radiant and Dire) play one **game** at a time on one map; a series is BO1, BO3 or BO5. There are no rounds: a game runs 25 to 60 minutes and ends when a team's **Ancient** falls (or a team writes "gg" and leaves).
  A draft (bans and picks) comes before every game: the casters and the desk talk it through; it is not play.
- Phases: laning (to about 10 minutes), the mid game (objective fights), the late game (one fight can end it). Gold and experience decide how strong each side is; a **net worth** or **advantage** graph shows who leads.
- Objectives: towers (tiers one to four), barracks (destroying them gives the other team **mega creeps**), **Roshan** (the Aegis that gives a second life, and later items), outposts, the Ancient.

## What the broadcast shows
- The **game clock** and each team's **kill count** at the top centre, with tower and objective icons; hero panels and the kill feed around the edges; the observer camera jumps between fights and lanes; instant replays are marked; the draft screen opens each game.
  Measure the places on a real frame (`T grid-frame`); they differ between broadcasters and patches.
- Structure: pre-show and desk, the draft, the game (with replays after big fights), pauses (the clock freezes), the "gg", the desk between games, the post-match.

## What a highlight is (the words you will hear)
A **team wipe** (all five of the other team dead), a **rampage** (five kills in a row by one hero) and the game's own announcer lines (first blood, double kill, triple kill, ultra kill, killing spree);
a game-turning ultimate (Black Hole, Ravage, Chronosphere, Reverse Polarity, Echo Slam and the like: "he caught five"); an **Aegis snatch** or a **Roshan steal**; a **buyback** gamble in the late game; a **comeback** from a large net worth deficit;
a high-ground defence or a siege that breaks it; **mega creeps** rolling a base; a **throw** (a lead wasted by one bad move); a **gank** or a smoke ambush that picks a hero off; a lone hero killing five on a tower dive; the **"gg"**.
Lexicon: gank, roam, rotate, ult, BKB, blink, buyback, Aegis, Rosh, mega creeps, high ground, push, split-push, throw, comeback, farm, carry, support, tilted, draft diff.

## The unit: the fight
- There is no round score. The unit is a **fight** (a cluster of kills and abilities within about 20 seconds; its start is the initiation, its end is the disengage or the last kill plus a few seconds), an **objective event** (a tower, the barracks, Roshan, the Ancient),
  a **phase** or a **swing**. Read the units from the kill count changing in bursts (`hud-scan` of the two kill counts, then `hud-states`), the clock, the casters' voices and the frames.
- **Quiet but not noise:** first blood (it starts a story), a Roshan fight even without kills, the fight just before a comeback or a throw, a draft pick the casters build a story on, the "gg".
- **Usually noise:** laning and farming stretches, long positioning, shopping, a skirmish that moves nothing.
- **Never skip:** the fight the game turns on, the last fight and the Ancient, a throw and the comeback it allowed, the game's first and last kill.
- **Traps:** replays shown while the clock keeps running or freezes; pauses; the clock in the replay is the replay's, not the live one; kill counts that jump by several in one fight; the broadcast cutting away to a desk while the fight is still going on.
