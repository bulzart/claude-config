---
name: create-clips-chat-heat
description: "user 2026-11-15: the live chat counted every 4 s (T heat) is a clue, never a verdict: each burst gets one look, heat adds at most a point to a moment the rest already rates, never picks or drops one; game mode much less"
metadata:
  node_type: memory
  type: project
  originSessionId: efec77d7-2d15-4e76-856d-85333ee657d3
  modified: 2026-11-15T08:51:16.553Z
---

User 2026-11-15: "we should use live comments count too ... count comments every 4 seconds ... peak charts of comments ... should be prioritized by the agents ... but still not get picked blindly ... a fuzzy and smart deciding system ... peak comments just adds a bit of score"; then, mid-build: "on game mode this thing should be taken into account way less since the game should be extracted based on the match content. but it still has to be considered". They also said I may use the Chrome MCP (not needed: WebSearch/WebFetch were enough) and to autocomplete/add addons.

**Built (2026-11-15):** `create-clips/scripts/cc_heat.py` (module 7 of cc.py): `T heat --run RUN` writes `20-analysis/heat.json` + `heat.md` (4 s bins of rec time from the chunks' `chat.json`, each against the median of the bins within +-37 bins, `z` = (n-base)/sqrt(base+1), `ratio`, `pct`; bursts = z >= 4 and n >= 5, merged <= 2 bins apart, widened while z >= 1.5; per burst the top tokens, `!` commands, top-token share, words per sampled message, samples, "after an ad"); `--from/--to [--rows]` for one span; `--coverage BLOCK.json` lists bursts nobody mentioned; `T blocks` lists each block's burst ids. No data (never "quiet"): before the first message, a 30 s+ zero stretch in a busy chat (capture gap), chunks with no chat file (ad-marked). Settings `config.json -> chat`. `reference/chat-heat.md` is the method: heat corroborates and never creates (up to ONE point on `shareability`, only when >= 2 other evidence kinds already rate the moment; pct under 90 or n under 8 = none, 90-97 half a point, 97+ a point), never subtracts, tie-break, helps `setup_from`/`rec_to`; every burst of a block gets one look = a moment (`heat` object), covered, or a `heat_review` line; the main session sends a file back once for bursts nobody looked at. Router rule 17, cc-start/cc-scan/cc-scan-game/cc-plan/cc-plan-game/cc-build-* lines, moment-mining/game-mining/game-clipping/portfolio/clip-economy/research docs, README, docs/processing.md; tests `tests/test_heat.py` + `test_docs.py`.

**Game mode, light:** one look per unit to fill the card's `chat_peak`, half a point at most on `impact` to settle a tie, never a keep level by itself, `heat_review` only for a burst outside every unit/extra/non-play span, no file sent back for it.

**Measured on the four recordings of 2026-11-14 [S]** (ishowspeed 28 min, xqc 15, hasanabi 4 + 6): chats ran 1.8-9.7 msgs/s; z >= 4 bursts about 10-40 an hour; 4-14 s wide (up to ~50 s); real causes seen: "F"/"KEKW" after a joke, "HUH", "Banger" while a song played, chat answering a question with a name, "lag" complaint. The recorder shifts chat 8 s back; the cause sat from ~14 s before the onset to the burst's first seconds (sometimes after: the streamer reacting to chat), so the read window is onset-14 s to peak+4 s. Outside [W]: LIGHTOR (arXiv 1910.12201): raw count fails (bots, delay ~20-27 s before any shift), short and similar messages mark highlights; stream-chat-summary tool: baseline-relative SD score, merges busy bins, flags break chat.

**Why:** chat is the best live "this travels" sign but easy to fool (commands, raids, spam on request, lag complaints, ad return, break talk); the user wants priority without blindness, scripts only gather (see [[scripts-gather-agents-decide]]).

**How to apply:** change the method in `reference/chat-heat.md` and the numbers in the tool/config, run `tests/test_heat.py` + `test_docs.py`; never let a script label or rank bursts; only 4 short recordings calibrate it (no long stream yet): watch the first real run's burst counts. Related: [[create-clips-pipeline]], [[create-clips-long-videos-whole-watches]], [[create-clips-shorts-level]].

Index line before the 2026-11-15 compaction of MEMORY.md (kept here so nothing is lost): user 2026-11-15: chat counted every 4 s (`T heat`, rule 17) is a clue, never a verdict: each burst gets one look, heat adds at most a point to a moment the rest already rates, never picks or drops one; game mode much less (`chat_peak`, half a point)

Index line before the 2026-11-20 compaction of MEMORY.md (kept here so nothing is lost): user 2026-11-15: chat counted every 4 s (T heat, rule 17) = a clue: one look per burst, <= 1 point on a moment the rest rates; game mode much less
