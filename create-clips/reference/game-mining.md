# Game mining: how a mining agent reads a block of a match

You get a block (about 8 chunks, 24 minutes), the context brief, the game's profile, the HUD files and the criteria. You bring back, for every unit of the block (a round, or a fight in Dota 2 and League),
what happened, how much it mattered and what kind of play it holds; what is not play (timeouts, pauses, desk, ads, sponsor stretches); the extra moments that travel (a caster who loses it, a crowd roar, a reaction on camera); and what needs blurring.
You do not decide the videos and you do not decide what is kept: the planner does, with your cards in front of it. Everything is in rec time (`H:MM:SS.cc` or seconds).

## Which units are yours
You write the card of every unit that **ends inside your block** (the score change, or the last kill of a fight, falls in your rec range). A unit that is still running when your block ends belongs to the next agent.
The start of your first unit may lie in the chunk before your block: read that chunk's transcript and its last sheets (read only) to find where the unit began.
Whatever the broadcast shows that is not a unit goes in `non_play`.

## Read in this order (cheap first, expensive only where it pays)
1. `RUN/20-analysis/brief.md` (the match, the teams and players with their spelling, what travels from this scene, how to judge a round or a play here) and `clip-criteria.md`.
   Then the game's profile the brief names (`CC/reference/games/<game>.md`, or `RUN/20-analysis/game-profile.md` for a game the library does not have).
2. `RUN/20-analysis/hud/regions.json` (where the score, the clock, the kill feed and the replay badge are on screen) and the rows of `RUN/20-analysis/hud/states.txt` inside your rec range
   (every change of the score with its time: a round ended there, or kills happened there). A change is a place to look, not yet a verdict.
   `cc.py hud-slice --run RUN --name clock --from T --to T` gives the clock's readings near a unit (the moment it restarts from its full value is where the round went live).
3. `RUN/20-analysis/match-map.md`: the rows that overlap your block (what each stretch is: play, break, timeout, desk, ad, replay).
4. **The chunk reports**: `RUN/10-media/Cnnnn/report.md` for every chunk of the block, in order. A separate reporter session wrote them while the match was downloaded: what the sheets show per 22.5 s (the kind of picture, who and what is visible, every piece of text on screen quoted as printed: team names, scores, clocks, banners),
   what the audio numbers do, what is said, and a few neutral sentences about what visibly or audibly happens, with evidence. **A report decides nothing**: it names no round, no ace, no clutch, no keep; the names are as printed or transcribed (unverified); a list at the edge of the picture is just a list of lines until you have looked at it.
   Use it to find the stretches (play, desk, replay, break, an advertisement-looking picture) and where to look. A chunk with no report (or a stale or failed one, see `T status`) is read from the raw data below.
5. The block's rows of `RUN/00-inventory/stream.md`, then the transcript of each chunk (`RUN/10-media/Cnnnn/transcript.txt`) in order. In a match the casters carry the story:
   what they shout, which names they say, "ace", "clutch", "he's got three", "no way".
6. `RUN/10-media/Cnnnn/sheets/overview.jpg` of each chunk where its report is thin, then the dense sheets (`sheets/sheet-NN.jpg`, a frame every 0.75 s, each timestamped) around the end of each unit and around every candidate play.
   `cc.py window`, `cc.py frame`, `cc.py sheet --step 0.25` only where the sheets leave a doubt.
7. `cc.py region-series` over a unit for the kill feed or the replay badge when you need to count kills or to tell live from replay (a burst of changes in the feed within a few seconds is kills: you look at the frames and count the names).
   `cc.py hud-read` for one value at one time (the clock at a play).
The numbers are facts a script read off the screen, the reports are what a reporter saw; the transcript and the frames are the evidence you check them against. When the HUD series, a report and the picture disagree, the picture wins, and the card says so.

## What to write: `RUN/20-analysis/blocks/block-NN.json`
```json
{"block": 3, "chunks": ["C0021","C0022","C0023"], "rec_from": 3780.0, "rec_to": 4320.0,
 "summary": "what happens in this block, 5 to 10 lines in time order, each with its rec time (the match and the map or game, the score, the turns, the breaks)",
 "units": [ {unit card}, ... ],
 "non_play": [ {"kind": "timeout|tactical-pause|technical-pause|desk|ad|sponsor|replay-block|side-switch|map-change|match-change|pre-show|post-match|interview|other", "rec_from": 4101.0, "rec_to": 4160.0, "note": "..."} ],
 "extras": [ {"id": "B03-X01", "rec_from": 4300.0, "rec_to": 4312.0, "type": "caster-meltdown|crowd|reaction|desk-joke|player-moment|fail|other", "what_happens": "...", "hook": "...",
              "why_it_travels": "...", "standalone": 7, "shareability": 8, "evidence": ["transcript 4300-4312"], "confidence": "medium"} ],
 "people": [{"name": "...", "role": "player|caster|analyst|coach|guest", "team": "...", "notes": "spelling, how Whisper wrote it"}],
 "lexicon_fixes": [["Whisper wrote", "right spelling"]],
 "sensitive": [ {"rec_from": 3901.0, "rec_to": 3908.5, "kind": "gore|distress|nudity", "what": "...", "region": [0.1,0.1,0.4,0.4], "unit": "R14"} ],
 "avoid": [ {"rec_from": 4001.0, "rec_to": 4064.0, "kind": "religion|superstition|hate|tragedy|music", "what": "..."} ],
 "notes": "anything the planner should know (a pause that cost a team, an ad, a gap, a HUD read that failed, a unit you could not card)"}
```
The unit card is the one in `game-clipping.md` §4 (every field; `null` where unknown). `impact` (1 to 10) and `keep_hint` (`full`, `trim`, `flash`, `skip`) are your first read with the reason in `impact_why` and `keep_hint_why`; `game-clipping.md` §5 to §7 say what they mean.
An empty `sensitive` and `avoid` is a statement that the block was checked: say so in `notes`.

## The quality bar
- **Every unit of the block gets a card**, the dull ones too, with a short reason (`skip`, impact 1 to 3): the planner needs the whole list to decide, and a silent gap looks like a missed round.
- **Bounds:** `rec_from` is where the round goes live (the clock leaves the freeze time) or where the fight starts (first contact); `rec_to` is the result plus the scoreboard update. Refine with the words and the frames, not with the HUD change alone (the score can update seconds after the bomb result).
- **Count only what you saw:** "4 kills: feed burst 4058 to 4063, frames C0023 s2 show four names". Write "ace" only for five kills by one player (or the game's equivalent) that you counted; if only the caster said it, write "caster says ace".
- **Live or replay:** say which one the decisive moment is on screen. A replay is not a unit: its span goes in the unit's `replays` (the play it repeats), or in `non_play` as `replay-block` when it covers several.
- **A new match is a border** (the user, 2026-11-14: a recording can hold two, three or more different matches): when the teams on the scoreboard change inside your block (a score reset alone is only the next map or game), record the stretch between the two matches as `non_play` kind `match-change`
  (the desk, the pre-show or the break inside it, and a note naming the teams on each side), card the next units with the new match's names, and never card the units of two matches as one.
- **Say what the viewer would lose:** `detail_value` is what a quiet unit changes later (an economy reset, a new tactic, a timeout and the round after it, a first kill, a score line): one line, or `none`.
- **Sponsorship and the like is `non_play`, kind `sponsor`:** sponsor stings and bumpers, "presented by" cards, betting-odds or promo segments, sponsor reads by the casters or the desk, giveaways and "use code" promotions, ad breaks. Give its exact span so it can be cut cleanly. A small sponsor logo that sits on live play is not a stretch: it is not recorded.
- **Ad-marked chunks (Twitch's own ads, recorded like everything else):** the recorder skips nothing, ad or not ad (the user, 2026-11-14), and passes Twitch's marker on (`(ad-marked)` after the chunk id in `stream.md`, `ad_chunks` per block in `T blocks`, `kind: "ad"` in the chunk's `chunk.json`). It is Twitch's word, not a verdict: look at each marked chunk of your block (report, overview sheet, a few words). What really is an advertisement goes in `non_play` as kind `ad` with its exact span (rec times, the chunks in the note) and is left out of your analysis: no unit, no extra, no round count in it. If the broadcast itself is on screen the marker was wrong: analyse it like any other stretch and say so in the unit's note. An advertisement the marker missed is `non_play` kind `ad` the same way.
- **Extras are rare and real:** a caster who loses it, a crowd roar, a reaction on camera, a funny moment off the play. Not every sentence is one.
- **Names as the brief spells them.** Where Whisper wrote a player or team wrong, add the pair to `lexicon_fixes`.
- **Say how sure you are:** a card read from the transcript only (no frames seen) is `medium` at best; one whose words you could not understand (crosstalk, music) is `low`, and the card says what would settle it.
- **Speed (the user wants it fast, without losing a check):** batch independent tool calls (several frames, contact sheets or Read calls in ONE message, every sheet you need from ONE PowerShell call, the images read together), aim for about 8 minutes and about 40 tool calls; one image per turn is the slowest way to read a block.
  Start from the units that matter (the story, the big plays), count the kills of those on frames, and give the dull ones a short reason from the clock, the score and the words.
- **Do not decide the videos or the keep levels.** Hand over the best map of the block you can.

Keep the file compact (the planner reads every block's file): at most about 24 KB, plain short sentences, evidence as pointers (a rec time, a sheet), no pasted transcript.
