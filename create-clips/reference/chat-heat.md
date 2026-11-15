# Chat heat: the audience's reaction as a clue, never a verdict

The user, 2026-11-15: count the live comments every 4 seconds, find where the chat peaks, give those parts priority and "a bit of score", but "not blindly only due to the score": a fuzzy, smart decision that weighs every aspect of the stream, where a chat peak is one more thing in the balance.
Game mode (the user, 2026-11-15): "taken into account way less, since the game should be extracted based on the match content, but it still has to be considered": see "Game mode" at the end.

## What it is for
When something lands, chat floods: a joke, a scare, a win, a fail, a donation, an outrage. A burst of messages is the audience saying where to look, and it is the best live sign of "this travels" that a recording keeps.
It is also easy to fool (bots and commands, a giveaway, "spam F" on request, a raid or a gifted-sub flood, a lag complaint, the surge when viewers come back from an ad, chat talking while the streamer is away),
and much of what makes a great clip never makes chat blast (a dry line, a quiet payoff, a slow chat, a chat in emote-only or slow mode). So heat does three small jobs and no big one:
1. **It tells you where to look**: every burst of your block gets one look (the second look below).
2. **It adds a bit** to a moment the rest of the evidence already likes, never more than a point.
3. **It helps place the cut**: where the cause starts (`setup_from`), where the payoff lands, how long the reaction lasts.
It never picks a moment alone, it never drops one, and no chat (or a quiet chat) says nothing about a moment.

## What the tool gives you (facts)
`T heat --run RUN` (`cc-start` runs it; it is cheap) writes `RUN/20-analysis/heat.md` (read this one) and `heat.json`: the chat's messages counted in **4-second bins of rec time**, each bin measured against **this stream's own normal**
(the median of the bins within about 150 s around it, so a 2 messages/s chat and a 10 messages/s chat read on one scale; never compare numbers of two streams). Per bin and per burst:
- `n` (messages in the bin) against `base` (its normal); `ratio` = (n + 1) / (base + 1); `z` = (n - base) / sqrt(base + 1), a size-adjusted excess (not a p-value: chat comes in clumps); `pct` = where the bin's z stands among all the run's bins (0 to 100). A small `n` is weak evidence: the list needs n of at least 5, and under about 10 you hold it loosely.
- A **burst** is a run of bins with z of at least 4 and n of at least 5 (about the top 3 to 4 percent of the stream's own bins), merged when 8 s apart or less and widened while z stays at 1.5 or more: its `onset`, `peak` and `end`, its messages, and what chat said:
  the top tokens (counted over ALL messages), the messages that are commands (they start with `!`), how much of the burst one token makes (`top token per message`), the words per sampled message (short = people reacting, long = people talking about something else), sample lines (at most 120 per chunk are sampled), and whether it came within 90 s after an ad-marked chunk.
- Per chunk: messages, the busiest bin, the highest z, the **hot share** (the share of its bins with z of at least 2: how long the chat stayed lively), the number of bursts. No-data stretches are named, never counted as quiet: before the first message (the chat was not connected yet), a capture dropout (no message at all for 30 s or more in a chat that is normally busy), and chunks with no chat file (ad-marked ones, or capture off).
- `T heat --run RUN --from T --to T` gives the same numbers, tokens and sample lines for any span (a candidate's bounds, the cause window); with `--rows` it also prints the heat.md rows of the chunks and bursts in the span, which is how a mining agent reads its own block without reading the whole file (a long stream's heat.md is long). `T blocks` lists each block's burst ids. `heat.json` says `has_chat: false` when no chat was recorded: then none of this applies.
- The settings are `config.json -> chat`; the burst list is a view with a threshold (`--min-z`, `--min-n` change it), not a ranking: it is in time order and nothing reads it by itself.

What it measured on your own recordings (2026-11-14: ishowspeed 28 min, xqc 15 min, hasanabi twice, 10 min in all) [S]: chats ran from 1.8 to 9.7 messages/s, so a stream's own baseline is the only fair yardstick; bursts at z of 4 came at about 10 to 40 an hour (5 to 20 per 30-minute block);
a burst is usually 1 to 3 bins (4 to 14 s) and up to about 50 s when the hype goes on, which is why 4 s is the right bin. Real bursts in them: "F" and "KEKW" after a joke, "HUH" after something odd, "Banger" while a song played, chat answering a question with a name, and "lag" when the stream stuttered.
Published, for comparison [W]: a Twitch study (LIGHTOR, Jiang et al., arXiv 1910.12201) found that raw message count alone fails, because bots post many messages at once and because viewers only chat after they have seen a highlight (the delay was about 20 s in its example and 23 to 27 s across its data, before any shift), and that short and similar messages, not long ones, mark a highlight; a chat-summary tool
(stream-chat-summary, "highlights") scores a bin by how many standard deviations it sits above the stream's own typical count, merges busy bins that touch, and warns that ordinary breaks in a marathon stream get flagged.

## How to look at a burst (one look, about 30 seconds)
1. Read its row: the size (z, pct, n against base), what chat says, the commands, the words per message, `after an ad`.
2. Read the tokens with this chat's own vocabulary (the research note: what this community spams and what each emote means). Common ones [M]: laughter (KEKW, LUL, OMEGALUL, LULW), respects or a fail (F), a win or a loss (W, L), confusion (HUH, ?), dismay or fear (D:, NOOO, monkaS), hype (POG and its cousins), praise (Banger, Cinema), a complaint (lag, mic, volume, audio), names or numbers (chat answering a question), `!` words (commands).
3. **Read the cause**: the words from 14 s before the burst's onset to 4 s after its peak (`T window --what transcript`, or `T words`), and a frame or a dense sheet when the words do not explain it. Chat reacts after the event; the recorder already moves the chat 8 s back, and what is left differs from stream to stream: in the recordings above the cause sat anywhere from about 14 s before the onset to the burst's first seconds,
   and sometimes after it, when the streamer is reacting to chat (reads a message, answers a poll). The cause is also often not the streamer's words: a clip or video being watched, a song, a game moment, a donation, a guest's line.
4. Name what it is. One of: a reaction to content (a joke, a turn, a fail, a reveal); chat answering the streamer (a question, a poll, "who should I play with"); a bit the streamer set up (spam F); a chat-made event (a raid, gifted subs, a hype train); commands or a giveaway; a technical complaint; the surge after an ad; talk during a break; a copypasta; nothing on screen explains it.
5. Only the first kind is a moment by itself, and only when the words and the picture agree; "answering" and "a bit set up" are moments only when the bit is good on its own; the rest are not moments (a technical complaint is a place to cut around).

## How heat enters the decision (the fuzzy part)
A moment is judged on several kinds of evidence, each as a degree (none, weak, clear, strong), never a yes or no: **the words** (setup, turn, payoff), **the picture and the sound** (a laugh, a shout, a fail, a reveal), **the streamer's own reaction**, **standalone and hook** (does it work for someone who was not there, do the first 2 seconds hold), **the topic and the audience** (what the research says they care about now), and **the audience's heat**. You combine them with judgement; there is no formula. Heat's place in it:
- **It corroborates, it never creates.** It can lift a moment that at least two of the other kinds already rate clear: up to **one point on `shareability`** (the 10-point scale), applied inside your own number and recorded in the moment's `heat.nudge` (0, 0.5 or 1). Where the other evidence is thin, it adds nothing, however big the burst.
- **By size:** `pct` under 90 or `n` under 8: no nudge. `pct` from 90 to 97: at most half a point, enough to settle a tie. `pct` 97 or more: up to a point. Take it down, to nothing if need be, for what you found when you looked: commands, one repeated token on request, a raid, the ad surge, a break, a complaint are not the audience reacting to content.
- **It never subtracts.** A moment in a quiet chat, a slow chat, a chat in emote-only or slow mode, or a run with no chat is judged on the rest alone. A quiet funny line can be the best clip of the night.
- **It orders, softly.** Among moments of about the same worth (the best three shorts, the first pick under `concentrated`), the hotter one goes first; it never goes ahead of a clearly better moment.
- **It helps the cut.** `setup_from` reaches back to where the cause starts; `rec_to` stays until the reaction has fallen (the burst's `end`) when the reaction is part of the joke; the peak, a few seconds after the onset, is a check on where the payoff is when the words and the picture leave you unsure.
- **It says a little about a whole stretch.** A chunk's hot share is a small clue to how watched the stretch was, one input to its `richness`; a dull stretch is still dull when its chat is busy, and a lively one is not dull because its chat is slow.

## The second look: priority without blindness
Every burst of your block (`T blocks` lists the ids) gets one look and ends in one of three places, so none is skipped and none is picked just for being loud:
- **a moment**, new or one you already have: put the burst's id and numbers in the moment's `heat`;
- **covered**: it lies inside a moment, a game unit, an extra or a non-play span you already wrote (nothing more to write);
- **`heat_review`**: one line in the block file, with the burst, what you named it (step 4 above) and why it is not a moment.
The main session runs `T heat --run RUN --coverage <your block file>` and sends a file back once, with the unmentioned bursts named, when one was never looked at (like an ad batch). A burst you looked at and rejected is fine; a burst never looked at is not.

## What to write
In a moment (null when no burst lies in it; say nothing about heat then):
```json
"heat": {"burst": "H012", "peak_rec": 3941.0, "z": 6.3, "pct": 99.2, "n": 73, "base": 35, "says": "F x191, NA x71, OMEGALUL x24", "kind": "reaction", "nudge": 1}
```
In the block file, next to `moments`:
```json
"heat_review": [ {"burst": "H013", "peak_rec": 4010.0, "kind": "commands", "why": "giveaway: !join x120, the streamer reads the rules; nothing to cut"} ]
```
`kind` is your word from step 4 above. Put `heat` in `evidence` too (`"chat H012: z 6.3, F x191"`), and say in `why_it_travels` how the audience reacted when that is part of why it travels.

## Game mode (taken into account way less, but taken into account)
A match is extracted from its own content: the score and the clock, the kill feed, the casters, the clutch, the replay. Chat is the least reliable witness there: the crowd cheers for a team, copypasta and promotions fly, the desk and the replays make bursts too.
So here heat is a light clue, and it is looked at, never skipped:
- **One look per unit.** For each unit you card, read the bursts that fall in it (or end within 8 s after it) and fill the card's `chat_peak` with the burst's numbers (`{"burst": "H014", "z": 5.2, "pct": 99, "says": "..."}`) or `null`. It is one more line in `impact_why` when it says something the match did not (the crowd saw a play the clock hides).
- **A half point at most**, on `impact`, only when the match evidence already rates the unit and only to settle a tie between units of the same impact. It never changes a `keep_hint` and it never makes a unit; a unit with no burst loses nothing.
- **No second look for every burst.** Bursts inside a unit, an extra or a non-play span are covered. Only a burst that lies outside all of them (a caster meltdown the units do not hold, a crowd roar, a reaction off the play) gets a line in `heat_review`, and the main session does not send a file back for it.
- **The planner** may use a unit's `chat_peak` as one small clue in a close call between two keep levels (`full` or `trim`), after the match content has spoken; it never decides alone.

## What heat is not
Not a measure of quality, not a trend signal (the research note says what the internet cares about), not comparable across streams, and not an order to include or cut. It is how the room reacted, which is one witness among several.
