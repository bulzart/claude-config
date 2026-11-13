# Game edit craft: the condensed match

The base is `edit-craft.md` (the EDL, cuts, captions): read it first. This file says what differs for a broadcast of a match. Game mode makes **long-form condensed matches only** (the user, 2026-11-13): no shorts, no vertical versions, **no sound effects at all**.
The tools are cuts, captions (always), a short transition where a map changes, and a blur where `safety.md` says. No zoom, no music, no stickers, no emoji, no text but captions, no filters, no drawings, no speed changes.

## 1. The spans come from the plan
The brief lists units, each with a keep level and `keep_spans`. You decide the exact cut points inside each span (a breath between the casters' words: `T words`), and you may tighten a span;
you do not widen it past the unit's bounds without a reason you write in the report, and a `flash` stays a flash. Order: chronological, as the match went.

## 2. Layout: nothing is cropped
`kind: long`, canvas 1920x1080, `layout: {"mode": "native"}`: the 16:9 broadcast frame as it is, so the scoreboard, the clock, the alive count and the kill feed are always in the picture and the HUD tells the story. Nothing else changes the picture.

## 3. The score and the clock (no text overlays)
You cannot add a score card: the only text is captions. The scoreboard is already in the picture; the casters' words in the captions carry the stakes ("match point", "one versus three"). The title goes in `posting.md`: `<team> vs <team> | Map 2 Mirage | <event>`.

## 4. Cut points
- **Start** where the keep span says, pulled back to the previous breath between the casters' words, about 0.1 to 0.2 s before the first word of the call, or on a beat of the game's own sound.
- **End** on the result plus the scoreboard update, or the end of the casters' sentence, plus 1 to 2 s of crowd. A caster who is still shouting: let it land (up to 2 s) and never cut inside it.
- **Replays:** the live action is canonical. Remove a replay of what was just shown. Keep one only when the plan says it adds what the live view hid, and it follows the live action with its own cut.
- **Dead air:** the buy phase and the walk to the site are cut; the unit's `live_from` is where the action starts.
- **Sponsorship and the like is cut, totally:** a sponsor sting or bumper, a "presented by" card, a betting-odds or promo segment, a sponsor read, a giveaway, an ad break inside or between your spans is left out; cut on the boundary of the stretch (the brief and `non_play` give its span; look at the frames before and after the cut).
  It is not noted, not blurred and not kept as context. A small sponsor logo on live play stays: cutting it would cut the play.
- `edl-check` still reports a cut inside a word (`cut_in_inside_word`, `cut_out_inside_word`): both must be null.

## 5. The casters are the narration
- Never lower or mute them. There are no sound effects, so nothing competes with a call.
- The captions follow the casters, who speak fast and shout. `T captions` makes the cues from the Whisper words; the **names** are the risk: apply the brief's lexicon (`replace`) and re-read every cue that holds a player or team name before you build.
- Crowd and game sound stay. Music that is audible between rounds belongs to a cut stretch; commercial music over live play is a claim risk (`safety.md`): cut around it where the play allows.

## 6. The condensed match
- One segment per straight run: adjacent kept units are one segment (the chunk joins inside it are seamless). A `flash` unit is its own short segment (3 to 8 s: the result and the scoreboard change).
  A skipped unit leaves nothing; the next kept unit makes the score clear (it is on the HUD); when two or more rounds were skipped in a row, a `flash` of the scoreboard between the clusters keeps the score line honest.
- A `flash` transition (0.15 to 0.25 s) at each map change; plain cuts everywhere else. Never start or end in the middle of a round or a fight: a map's first segment starts at the map start or the first kept unit's live start, its last one ends on the map result.
- Captions: `size` 6, at the bottom, normal case, the lexicon in `replace`; every second of speech is captioned.
- Chapters in `posting.md`: each half, overtime and every unit that is a headline (an ace, a clutch, a comeback), with output timestamps (`resolved.json -> pieces[].at`).
- The length is the sum of the kept spans. Do not pad; do not trim a unit below what makes it understood.

## 7. Safety in a match
Same rules as everywhere (`safety.md`): religion and superstition are avoided (a player's prayer or gesture, a blessing from a caster: not a pick; an incidental one is cut around or listed); distress and gore are blurred where seen
(game violence in its normal look is not gore; a real injury or a real breakdown on camera is); personal data on screen is blurred (a phone number, an email, a real address in a lower third); slurs from casters, players or chat are masked in the captions.
