# Game edit craft: what changes when the footage is a match

The base is `edit-craft.md` (the EDL, cuts, layouts, zoom, transitions, captions, sound effects): read it first. This file only says what differs for a broadcast of a match.
The four tools are the same: cuts, captions (always), VFX (a zoom, a short transition, a blur where `safety.md` says) and sound effects. Still no music, no stickers, no emoji, no text but captions, no filters, no drawings, no speed changes.

## 1. The spans come from the plan
The brief lists units, each with a keep level and `keep_spans`. You decide the exact cut points inside each span (a breath between the casters' words: `T words`), and you may tighten a span;
you do not widen it past the unit's bounds without a reason you write in the report, and a `flash` stays a flash. Inside a video the order is chronological unless the brief names another one
(a short may open on the payoff and then play the round from its setup).

## 2. Layout: the HUD is part of the picture
Look at a real frame of the span first (`T grid-frame --run RUN --at T`; the broadcast's regions are in `RUN/20-analysis/hud/regions.json`).
- **Shorts (9:16):**
  - `fit-blur` is the default for a play where the score, the clock, the alive count or the kill feed are part of the story (a clutch, a round story, an ace: the viewer reads "1v3, 0:12 left" off the HUD).
    The whole 16:9 frame sits in the middle on a blurred copy of itself and the captions go in the empty band below. The background blur is not verified on this PC's CapCut 9.7: look at it in the first project, say so in the report, fall back to `fill` if it does not show.
  - `fill` around a measured focus when one thing carries the moment and the HUD does not matter to it: a single spectacular kill with the crosshair in the middle, a player cam or a caster cam reaction.
    From a 1080p source a 9:16 crop is 608x1080 enlarged to 1080x1920: acceptable; from 720p it is soft, say so in the report.
  - Switch layouts on a beat, never mid-sentence; at most once in a short.
- **Long-form (the condensed match, 16:9):** `native`. Nothing is cropped; the HUD is the story.
- Never crop away the scoreboard in a unit whose point is the stakes (map point, match point, a comeback).

## 3. The score and the clock (no text overlays)
You cannot add a score card: the only text is captions. The scoreboard is already in the picture: start a short on a frame where it is readable and the situation is clear (the alive count, the clock, the bomb).
A caption cue from the casters' words carries the stakes ("match point", "one versus three"). The title goes in `posting.md` as `<player> <what happened> vs <team> | <event>`; the first caption cue of a short does not spoil the result.

## 4. Cut points
- **Start** where the keep span says, pulled back to the previous breath between the casters' words, about 0.1 to 0.2 s before the first word of the call, or on a beat of the game's own sound.
- **End** on the result plus the scoreboard update, or the end of the casters' sentence, plus 1 to 2 s of crowd. A caster who is still screaming: let the scream land (up to 2 s) and never cut inside it.
- **Replays:** the live action is canonical. Remove a replay of what was just shown. Keep one only when the plan says it adds what the live view hid, and it follows the live action with its own cut.
- **Dead air:** the buy phase and the walk to the site are cut; the unit's `live_from` is where the action starts. The buy phase stays only for an economy beat the brief names.
- `edl-check` still reports a cut inside a word (`cut_in_inside_word`, `cut_out_inside_word`): both must be null.

## 5. The casters are the narration
- Never lower or mute them. Never put a sound effect over a call (a shout, a name, "he's got three").
- The captions follow the casters, who speak fast and shout. `T captions` makes the cues from the Whisper words; the **names** are the risk: apply the brief's lexicon (`replace`) and re-read every cue that holds a player or team name before you build.
- Crowd and game sound stay. Commercial music that is audible between rounds is a claim risk (`safety.md`): cut around it or note it.

## 6. Zoom, transitions and sound effects in a match
- **Zoom:** at most one punch-in per play, on the kill or the clutch beat (`to` 1.10 to 1.20) toward the focus (the crosshair, the kill). None in a round story's setup.
- **Transitions:** plain cuts. A `flash` or `white-flash` (0.15 to 0.25 s) only between two different plays in a compilation, or between maps in a long video.
- **Sound effects:** a serious play is not seasoned: none on an ace, a clutch, a decisive win. A meme sound belongs only to a funny cut (a throw, a funny death, a whiff), only when the casters or the crowd laugh, and never over speech.
  A condensed match has a handful at most, usually none.

## 7. The condensed match (long-form)
- One segment per straight run: adjacent kept units are one segment (the chunk joins inside it are seamless). A `flash` unit is its own short segment (3 to 8 s: the result and the scoreboard change).
  A skipped unit leaves nothing; the next kept unit makes the score clear (it is on the HUD); when two or more rounds were skipped in a row, a `flash` of the scoreboard between the clusters keeps the score line honest.
- A `flash` transition at each map change, plain cuts elsewhere. Never start or end in the middle of a round or a fight: a map's first segment starts at the map start or the first kept unit's live start, its last one ends on the map result.
- Chapters in `posting.md`: each map, each half, overtime and every unit that is a headline (an ace, a clutch), with output timestamps (`resolved.json -> pieces[].at`).
- The length is the sum of the kept spans. Do not pad; do not trim a unit below what makes it understood.

## 8. Safety in a match
Same rules as everywhere (`safety.md`): religion and superstition are avoided (a player's prayer or gesture, a blessing from a caster: not a pick; an incidental one is cut around or listed); distress and gore are blurred where seen
(game violence in its normal look is not gore; a real injury or a real breakdown on camera is); personal data on screen is blurred (a phone number, an email, a real address in a lower third); slurs from casters, players or chat are masked in the captions.
Betting and gambling sponsor overlays are common at tournaments: note them in the report (platforms may limit them), never blur them unless the brief says so.
