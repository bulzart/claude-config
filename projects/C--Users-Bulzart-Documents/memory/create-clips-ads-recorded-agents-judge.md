---
name: create-clips-ads-recorded-agents-judge
description: "user 2026-11-14: the recorder skips NOTHING, ad or not ad; Twitch's ad segments become their own chunks (kind ad), the create-clips agents judge and leave out the ad batches; plus the streamer-mode Videos question (long only | long + shorts)"
metadata:
  node_type: memory
  type: project
  originSessionId: efec77d7-2d15-4e76-856d-85333ee657d3
  modified: 2026-11-14T01:53:35.499Z
---

User 2026-11-14, after seeing `| ad` on the recording bar while their own player showed no ad: "just record while the ad is playing too and then the agents on createclips exclude it" and then "just do not skip anything, whether ad or not ad, and the agents then exclude batches of ads when they analyse". Also: "the pipeline workflow has to ask on streamer mode if the user wants only long content or long content + shorts, and they pick".

What was built (extension `C:\Users\Bulzart\Documents\twitch-chunk-recorder`, create-clips `~/.claude/create-clips`):
- **Recorder** (`src/engine.js`): every segment Twitch marks as an ad is downloaded and saved as chunks of its own (an ad has its own init map and clock, so it never shares a chunk with the stream), numbered in sequence between the live chunks; the sidecar adds `kind: "ad"` and `ad: {segments_by_range, segments_by_title, titles}`. No chat file for an ad chunk; an ad chunk is NEVER dropped (the live-scrap rule of 5 s stays for stream chunks); a lost ad segment is counted in `ads_skipped_s`. The pill says `| ad (recorded)`. No switch in the popup (engine option `recordAds` exists for the tests of the old skipping only). Tests: `test/ads.test.js` (25 checks), whole suite + real-Chrome e2e 62/62 pass.
- **Toolkit** is gather-only: the marker is copied into the chunk table (`kind`, `ad`), shown as `(ad-marked)` in stream.md, `AD-MARKED` in `T chunks`/`T status`, `ad_chunks` per block and `ad_batches` in `T blocks`, and in the reporter's prompt. **No script excludes anything** ([[scripts-gather-agents-decide]]): rec time runs through ad chunks, `split_across_chunks` still resolves them. The mining agents look at each marked batch and write `ad_batches` with a verdict `ad|stream|mixed` (moment-mining.md "Ad-marked chunks"; game mode: `non_play` kind `ad`); the planner merges them into `ad-batches.json` and puts the `ad` ones into `avoid.json` kind `ad`, so every brief carries them. Test `tests/test_ads.py`.
- **Videos question**: `cc-start` asks `Videos` in the same dialog as Mode and Captions (streamer mode only, no default, no "Recommended"): "Long videos only" or "Long videos + shorts"; stored as `state.json -> only` = `long` | `both` (`only=shorts` stays an argument; no value = both; game mode records `long` without asking). `cc-plan` and `cc-produce` read `only`. NOTE `state.videos` is the dict of planned videos: never reuse that key for the choice.

**Why:** the user feared the recorder was dropping real stream content behind the `ad` label. Recording everything and letting agents judge removes that worry and matches "scripts gather, agents decide".

**Facts found while investigating (jynxzi, ishowspeed, jasontheween, xqc recordings 2026-11-13/14, anonymous session, no Turbo):** a 30.2 s pre-roll at the start of every session (first chunk starts ~26 s after the session start); ishowspeed had a mid-roll break about every 8 min, each leaving `gap_before_s` 181.41 on the next chunk while only 49-71 s were flagged ad: 1684 s recorded of 2627 s (36% of the stream missing); jasontheween one break; xqc none. The recorder's session is not the user's player (their player may show no ad). An ad chunk holds the ad, NOT the stream that aired meanwhile: the unexplained ~110-130 s per break is not in that session's playlist (the README says the ad takes the place of the live content for that viewer); recording the ad chunks lets the user look at what those seconds really were. Ad-free options (Turbo, a channel sub, "Use my Twitch login") never tried live. Bypassing ads (adblock-style playerType tricks) was NOT proposed or built.

**How to apply:** after an extension change reload it in `chrome://extensions`; restart `CreateClipsWatcher` after toolkit changes. If an ad chunk looks like real stream content, the agent's verdict says `stream` and it is mined like any chunk; never make a script drop or skip ad chunks.

Related: [[create-clips-pipeline]], [[scripts-gather-agents-decide]]
