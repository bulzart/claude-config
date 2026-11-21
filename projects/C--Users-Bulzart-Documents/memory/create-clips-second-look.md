---
name: create-clips-second-look
description: "/create-clips recall safety net (2026-11-20): cc.py recall + ONE second-look agent after the scan, reaction leads checked on the face cam; evaluation numbers and cost"
metadata:
  node_type: memory
  type: project
  originSessionId: 046004a5-1b5b-492c-a227-505bb55d8234
  modified: 2026-11-20T17:18:43.517Z
---

User 2026-11-20 spec "Improve Highlight Discovery Recall": "Find broadly. Understand deeply. Recover overlooked opportunities. Select only what deserves to be watched." Fewer missed exceptional moments, never more average clips.

**Built (live):** `cc.py recall --run RUN` (cc_recall.py, encrypted; facts only) writes 20-analysis/recall.md/json: uncovered stretches (moments count setup..end), leads `maybe` (block field), `reaction` (heat_review bursts set aside as no reaction / the game's line, face not seen, or `face` not looked), `summary` lines and `thread` points no moment covers, `sample` windows every 600 s of uncovered time placed by the clock alone. cc-scan step 3b: ONE second-look agent (reference/second-look.md) writes second-look.json (SL- moments with found_by/why_missed, one `checked` line per lead); `recall --check` lists unmentioned leads. cc-plan merges SL moments, checks every one, same bar; counts unchanged (shorts level, long-video content). Switch: config `recall.second_look` (true). Mining now: `maybes`, structured `threads`, no "3 to 8 per 30 min" count, `face` in heat_review, payoff bounds (+20 s look). `T sheet --crop x,y,w,h` = face-cam strip.

**Evaluation (3 regions: caseoh blocks 03 and 10, an xqc 28 min with a baseline mining run; fresh reviewers blind to the picks):** reviewer strong 11/11 found by the single pass; good 16/18 (xqc: a laugh at a talk-radio line dismissed "no reaction"; a drawbridge stunt under a licensed song). No verified miss of a strong moment. Second look v1: caseoh b03 4 recovered (1 = big laugh payoff "These houses are abandoned", verified on the face cam; 3 rated minor by the reviewer), b10 1 (PEST CONTROL payoff cut off by B10-M08's end, reviewer good), xqc 0. v2 with reaction leads: xqc 1 (the laugh, verified). Lead yield: summary 3/20, sample 1/10, reaction 1/3 in xqc. Cost: ~250k tokens, 40-65 tool calls, 12-20 min per 30-min region. caseoh shorts would not change (planned shorts score 16-18 of 20, recovered 11-14).

**Long form:** caseoh long spans hold 310 of 314 live min (~77% after planned cuts); miners marked 8% dull/break, reviewers judged ~40% of the sampled blocks ordinary (transit, menus, chores, cutscenes with no reaction): recommended a separate editorial-selection change, not built.

Evidence: C:\Users\Bulzart\Documents\stream-clips\validation\recall-20261120 (10-clip review pack + evidence\). Related: [[create-clips-face-is-evidence]], [[create-clips-lexicon-scope]], [[scripts-gather-agents-decide]], [[create-clips-speaker-facts]]

**Made selective 2026-11-21 (the user: proportional, no whole-stream repeats):** the whole-stream second look on caseoh took 22 min and ~415k tokens for 2 weak finds and no plan change. Now `recall.md` lists leads in tiers: look first (a burst set aside without his face seen, a beat a miner set aside as unsure), sample windows, the rest as context; `recall --check` requires only the first two; thread leads off by default (`recall.thread_leads`, 0 moments from 15). The agent runs in the background while cc-plan merges; the portfolio waits for it. Budget ~8 min, ~30 calls. The "fresh reviewers" of the evaluation above were an experiment, never part of the command ([[create-clips-no-detached-judges]]).
