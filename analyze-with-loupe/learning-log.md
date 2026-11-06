# Learning log: /analyze-with-loupe

One section per change of substance, newest last (the first four sections are the passes of a learning command that has since been retired). Since 2026-10-13 there is no ledger (see the 2026-10-13 section, which also maps every `CE-nnn` case label of the references to the section that holds its lesson). A pattern that
recurs after a logged change means that change failed: revise it, do not repeat it.

_Entries before 2026-10-20 are inherited from the library at `C:/Users/Bulzart/.claude/analyze-then-pick`, from which this command was copied on 2026-10-20 (its history up to the copy; names rewritten to this command's)._

## 2026-10-10 · CE-014..CE-028 (only CE-014..CE-028 in scope) · 8 patterns · commit 8385158
- **Scan:** record set = `caught_errors.md` (28 entries, CE-001..CE-013 read as context) + run `20261010-020703-09` (plans, requests, `result.json`, `qc-verdict.md`, `capcut-edit-note.md` of videos 01, 03, 06, 09, 10, the run's `50-requests/agent-contract.md`). Run-level records with no ledger entry, gathered with ids of their own: `R-20261010-020703-09-all-1` (the run's agent contract said "Never write to AWL/caught_errors.md yourself" while `production-agents.md` §2/§3 said to record; five agents reported "contract forbids" and recorded nothing; the main session wrote entries by hand later), `R-20261010-020703-09-10-1` (video 10: `wan3_0_prime` failed twice in ~15 s with no error text, both refunded; the video reference still showed a real celebrity's face; attempt 3 without the video reference passed QC). Offered, not written: adding them through the ledger tool needs the user's words.
- **Patterns:**
  - P1 A size verdict from an assumed distance (CE-028 user; CE-005, CE-009, CE-011, CE-014, CE-015; repeated, plus a false positive; model limit on `wan3_0_prime` for the real oversize cases).
  - P2 A placed or contents product absent in the opening seconds, or drifting along its surface with no cause (CE-018, CE-019; two single user entries, one class; qc-miss and model limit).
  - P3 The assembled CapCut timeline breaks what the generation got right: the replaced performer in insert edges, a spliced and shortened audio track, frozen frames under a flash, a leftover overlay rectangle (CE-016, CE-024, CE-025, CE-026; repeated; qc-miss and plan).
  - P4 Source text and overlays handled by rule instead of by meaning: a context-bearing notification dropped then re-typed, a caption swapped to another subject, a specific keyword dropped, an emoji in a text layer (CE-017, CE-023, CE-022, CE-027 and the user's emoji rule; repeated; plan).
  - P5 A brand given a scene it has no tie to (CE-020; single; plan).
  - P6 A placed pack leaned on a lid instead of resting on a fixed natural surface of the source (CE-021; repeats CE-012/013 after their rule; plan).
  - P7 Agents and the main session not double-checking or not updating the docs and the ledger (run-level record `R-20261010-020703-09-all-1`; the unchecked claims in the run's agent reports: CE-016, CE-018, CE-019, CE-025, CE-026, CE-028).
  - P8 A real celebrity's face in the video reference fails moderation (run-level record `R-20261010-020703-09-10-1`; single, unproven).
- **Root causes:**
  - P1 wording and QC miss. `anomaly-catalog.md` §2.7 told the planner to take the distance "from the shot size and the blocking" with a table of default distances (1.5 m for a medium shot); the false assumption was that the shot size gives the distance. One number was enough for an agent to write RESIDUAL FAILURE and for the main session to repeat it; nobody viewed the frame. The `scale` tool printed a bare verdict from `--distance/--lens` alone.
  - P2 QC miss. §4b.3 had "one location, persistent" but QC compared size and count at checkpoints, not the position against a fixed neighbour second by second, and a product absent for the first 4 s was delivered as a flagged note.
  - P3 QC miss and plan. QC checked the generated pieces, not every frame of the assembled timeline (insert edges, transitions, overlays, audio); each fix (CE-016 trim, CE-024 splice, CE-025 hold) introduced the next error because no rule said "cover only the edge span, keep every duration, fade real motion, never hold a frame".
  - P4 plan. The third-party-brand removal and the never-copy-handles defaults were applied without asking what the element is for in the joke; the user's instruction outranks both.
  - P5 plan. The asset plan picked the brand by free surface; brand fit was never judged.
  - P6 wording. The §4b.1b support rule ("bare surface or a large solid object") did not say fixed and natural, so a moving cutting board and a grill lid both passed.
  - P7 structure of the documents. The agent contract was a copied file from an earlier run, not the canonical text; the "as each agent reports" step reconciled only the ledger.
  - P8 model limit (hypothesis). The input shows a real face; moderation fails the job without text.
- **Coverage:** P1 gap (rule existed and recurred) · P2 gap · P3 gap · P4 gap · P5 gap · P6 gap (rule existed and recurred) · P7 gap · P8 gap, unproven.
- **Changes:**
  - `reference/anomaly-catalog.md`: §2.7 breaks, depth derived from the frame, two independent estimates, provisional verdicts, method in the verdict, re-measure when the eye disagrees; §2.16 fixed natural surface (P1, P6; CE-028, CE-005, CE-014, CE-015, CE-021); §4 step 5d rewritten, new steps 5f (anchor from frame 0, position every 0.25 s) and 5g (assembled timeline, audio hash, emoji), step 8 verdict, §4.1 verdict lines, §5 rows (P1, P2, P3; CE-018, CE-019, CE-016, CE-024, CE-025, CE-026).
  - `reference/generation-system.md`: §3c step 4 (edges past dissolves, timeline and original audio whole, real-motion fades, no frozen frames), §4b.1 and §4b.1b (fixed natural surface), §4b.3 (there from frame 0; a cut is not a motive), §5c.2 (moderation fallback), §8 and §9 (derived distance, two estimates, anchor and timeline bullets) (P1, P2, P3, P6, P8; CE-016, CE-018, CE-019, CE-021, CE-024, CE-025, CE-028).
  - `reference/production-agents.md`: §2 is the canonical contract generated at A9 (never copied), recording stated as mandatory, the size method, the never-skipped checks, the Higgsfield and CapCut notes of the old run contract, the deliverables rule; §3 items 12 to 14 (the double-check duties with evidence paths, docs and ledger before the final message); §4 `continuity` fields; §5 item 3 the as-agents-report checklist (P1, P2, P3, P7; CE-016..CE-028).
  - `reference/capcut-assembly.md`: §3 step 1 (Recreate keeps the timeline and the original audio whole), step 2 (no emoji), new step 2b (overlays cut from the reference: visible frames only, fade with the picture), §5 (dense sheets, audio hash), §6 (clean built from pieces, all videos in one folder) (P3, P4; CE-016, CE-023..CE-026).
  - `reference/text-and-format.md`: §1 (minimal guardrail rewrite, specific keyword, context-bearing overlays, no emoji), §3 steps 1, 6, 7 (P4; CE-017, CE-022, CE-023, CE-027).
  - `reference/brand-guardrails.md` §2 wording row (P4; CE-022). `reference/analysis-protocol.md` §5 ranking (P5; CE-020). `models/wan-3-0.md` §5 (caveat on the size row, opening-seconds row, celebrity-reference row), §9 (re-measure the run-09 flags) (P1, P2, P8; CE-018, CE-028).
  - `commands/analyze-with-loupe.md`: item 6 and item 14, A6r, A7, A9 step 5 (agent contract generated), A9b (as-each-agent-reports checklist), X1, X4, X9 (size method, anchor, assembled timeline, CapCut project), X10, §6 (deliverables, emoji and size verification), §7 Never (P1 to P7).
  - `scripts/awl.py` `scale`: new `--distance-basis`; a verdict from `--distance/--lens` alone prints `provisional`, `verdict_base`, `provisional_reason` and a "PROVISIONAL (distance assumed)" human line (stderr and `reading`); two estimates that disagree by more than `--note-pct` give `inconclusive`; flags and the existing fields are unchanged (P1; CE-028).
  - Build prompt `Documents/prompts/analyze-with-loupe.txt` brought in line (size reckoning, persistence, posture support, text rules, inserts, deliverables, quality control, the agent contract, the Never list).
- **Promoted:** CE-016, CE-017, CE-019, CE-020, CE-021, CE-022, CE-023, CE-024, CE-025, CE-026, CE-027, CE-028 with their pointers (the entries stay as the record, none marked fixed: no passing verdict exists). **Left open:** CE-014, CE-015 and CE-018 (model limit on `wan3_0_prime`; their pointers now also name the new rules; the start-frame lever of `wan-3-0.md` §9 is untested).
- **Suggested, not applied:**
  - Re-measure the run-09 size flags (V01, V04, V08, V11) on their full-resolution frames with two derived estimates (`wan-3-0.md` §9); if most land within 1.25x the model-limit row of §5 is overstated.
  - Add the two run-level records as proper ledger entries (needs the user's words).
- **Design suggestions (structural, for the user):**
  - A `T agent-contract --run RUN` command that renders `production-agents.md` §2 into `50-requests/agent-contract.md`, so the contract cannot be hand-copied from an earlier run (a new toolkit command; P7).
  - A `T deliverables-check --run RUN` command that compares `state.json` `videos[]` with `deliverables/`, the README rows and the CapCut drafts' text layers (emoji scan) (a new command; P7, P4).
  - A `T qc --track "<neighbour box>"` option or command that follows the placed product against a fixed neighbour automatically at 0.25 s steps (a new QC method; P2).
  - A ledger source `run` for run-level records, so records like `R-20261010-020703-09-all-1` need no user quote (a format change; P7).
- **To test:**
  - P1: on the next run with placements, record the method (A, B, basis) of every size verdict → measure how often the user's eye agrees within 15 % and how often `scale` prints `inconclusive`; proven when 5 of 5 reported sizes survive the user's eye.
  - P2: first-second dense sheet plus 0.25 s tracking on every placement → measure how many deliveries still show an absent or drifting product; proven when 0 of the next 5 do.
  - P3: dense sheets at every transition, insert and overlay edge, audio hash on every Recreate with inserts → proven when the next with-inserts videos get no user note about frozen frames, stray rectangles, replaced performers or audio.
  - P4/P5/P6: the next Recreate batch → proven when no user note about a re-typed overlay, a changed caption subject, a dropped keyword, an emoji, a brand without a scene tie or a leaning pack.
  - P7: the next run → proven when every agent `result.json` has evidence paths, no agent reports "contract forbids", and the wrap-up finds nothing missing in `deliverables/`.
  - P8: the next celebrity swap on `wan3_0_prime` → measure whether the video-referenced request fails again; proven when it fails twice and the no-reference attempt passes.

## 2026-10-10 · CE-001..CE-028 (whole ledger in scope) · 1 pattern changed · commits cded26f (edits) and 7dce424 (log)
- **Scan:** record set = `caught_errors.md` (28 entries; none newer than the previous pass: the file was last written at 05:56 and that pass committed at 05:57) + the files its entries point to (briefs, prompts and plans of runs 05, 07, 08, 09; run 09 `result.json`, `qc-verdict.md`, requests, and the frames `video-01/a1/f0.png`, `video-03/a1/f0.png`) + the files that cite CE ids (the references, `wan-3-0.md`, `awl.py`, the command, `update-from-errors.md`) + run-level records: all 104 `result.json` (9 of the 11 run folders have them). By text match 52 say a generation was regenerated, flagged or failed; 40 of them have no ledger entry (37 after dropping three that only match the phrase "no regeneration"). Run-level ids `R-<run>-<video>-1`, not written to the ledger: runs 01-07 (24 records, before the ledger existed: source printed text, logos, decor or the replaced performer leaking into the plate, burned-in caption ghosts, a tab raised from frame 0, a spin stopped early, a seam or cut that broke, a contents sample leaking into a vessel, sync misses; every class has a rule in force: `generation-system.md` §3b/§5b/§5c/§9b, `anomaly-catalog.md` §2.3/§2.6/§2.9, `text-and-format.md` §2.2); run 08 (9; delivered flagged: V02 V06 V09 V10 V12 V18, size and a count); run 09 (4, all delivered flagged: V08 gate-board text, an extra can on a seat, a glass not set back, size; V09 tumbler badge, size; V12 carton upright and oversize; V13 carton oversize). All were produced before the pass-1 rules.
- **Log:** this file was deleted by the auto-commit `c37cec3` (06:09, 12 minutes after pass 1) and is restored from `29b4964`; the pass-1 section below is unchanged. README and the ledger header still list it.
- **Patterns** (reclustered over the whole ledger and the run-level records; P1-P8 as in pass 1, P9 added):
  - P1 Size of a placed product on `wan3_0_prime` (CE-005, 007, 009, 011, 013, 014, 015, 028 and the run-level size flags). Two mechanisms sat under one label: (a) small flat packs rendered about 1.5-1.8x against a same-plane neighbour (CE-007, CE-009, CE-011; user-confirmed in CE-009; wording did not move it in CE-009 r3 to r4 and CE-011 a1 to a2); (b) a Celsius can found nearer the lens than planned and measured against her head at an assumed same depth (CE-014, CE-015, V04 a3, V11): unproven.
  - P2 anchor absent or drifting (CE-018, CE-019). P3 assembled timeline (CE-016, 024, 025, 026). P4 source text and overlays (CE-017, 022, 023, 027, emoji). P5 brand fit (CE-020). P6 posture, support and place (CE-006, 007, 012, 013, 021). P7 agents and main session not double-checking, docs and ledger not updated (run-level). P8 a real celebrity's face fails moderation (run-level, single).
  - P9 the early classes, promoted before pass 1: counts (CE-001), openings (CE-002), solidity (CE-003), blend (CE-004), adult framing (CE-008), centred text (CE-010). They recurred only in the form QC catches: run 08 V10 "2 pairs of glasses" (CE-001) and run 09 V08 "extra can on a seat" were found by X9 and shipped flagged after the one regeneration; the check works, the model's behaviour is the limit.
- **Diagnosis check (§2):**
  - CE-014 corrected. Frame `video-01/a1/f0.png`: can 375 px (29 % of the frame height) on the near table strip in front of her; its width (130 px for 5.8 cm at f26) puts it at 0.41 m, her head (340 px for 23 cm) at 0.62 m. Against her head at depth ratio 1 `T scale` prints 1.61x (invalid: the can is in front of her); at ratio 0.66 it prints 1.07x; a ground-plane reading (camera about 30 cm above a level table) gives about 1.4x. Unsettled between about 1x and 1.4x until a known-size object at the can's depth is in the frame. The a1 prompt itself asked for the can "closer to the lens than she is".
  - CE-015 corrected. Frame `video-03/a1/f0.png`: can width 125 px for 5.5 cm gives 0.41 m, her head 0.58 m; 0.94x at that read, base cropped by the frame bottom (a depth and support miss, §2.16). Unsettled between about 1x and 1.3x.
  - CE-018 supplemented. V04 a2 to a3 added "the can and the glass are both on the desk from the very first frame to the last frame … does not appear or disappear" and the can was in frame from 0 s on one spot (a3 failed size only); a3 to a4 pinned the depth ("at the same depth from the lens as the glass, behind the keyboard", "about 1.3 times as tall as the glass", "no can in the foreground, no can closer to the camera than the glass") and the can came out at about 0.086 against 0.083 planned, but vanished at 2.8-3.4 s and was drunk from. The a3 verdict itself says the can stood in the left foreground, "T scale vs the hand is not like-for-like". Neither is a verified prompt (no passing verdict), so neither is an example.
  - CE-011 confirmed (the carton leans on the bottle: a valid same-plane neighbour). CE-006..CE-013 and CE-016..CE-028 confirmed against the attached brief, prompt and verdict text (frames not re-viewed). CE-001..CE-005 unverifiable (brief and prompt not recorded, earlier runs).
- **Root causes:**
  - P1(b) QC miss and wording. Pass 1 fixed the assumed distance (estimate B) but left estimate A as "the plan's named neighbour" in the texts agents follow (contract `production-agents.md` §2 and §3 item 13.6, `anomaly-catalog.md` §4 step 5d, `generation-system.md` §9, command X9); the same-plane qualifier and `--depth-ratio` lived only in §2.7 and the tool, which the agent reading list does not name. The false assumption: that a person's head is at the product's depth. Also the user, who gave detailed notes on V01, V03 and V04, never named a size problem on them (CE-016..CE-018, CE-023, CE-026, CE-027 are about other things), and said V06 "looks accurate" (CE-028).
  - P2-P8 unchanged from pass 1; no run has happened since, so no rule has been tested.
- **Coverage:** P1(a) covered, unproven (wan-3-0.md §5 passing list; anomaly-catalog §2.7, §4 5d; awl.py scale) · P1(b) gap (QC text where agents read it) · P2 covered, unproven (generation-system §4b.3; anomaly-catalog §4 5f; wan-3-0 §5) · P3 covered, unproven (generation-system §3c; capcut-assembly §3, §5; anomaly-catalog §4 5g) · P4 covered, unproven (text-and-format §1, §3; capcut-assembly §3 2b) · P5 covered, unproven (analysis-protocol §5; command A7) · P6 covered, unproven (generation-system §4b.1b; anomaly-catalog §2.16) · P7 covered, unproven (production-agents §2, §3, §5; command A9, A9b, §6) · P8 covered, unproven (generation-system §5c.2) · P9 covered (CE-008 travels through the A1 ledger read and the guardrail audit: CE-008 passed in the run 08 verdicts, and the run 09 V03 brief applies the client guardrail "N1/C2": reads as a minor, so a complete face swap).
- **Changes** (one clause each, the existing method kept):
  - `reference/anomaly-catalog.md`: §4 step 5d (estimate A is read against a neighbour at the product's own depth, `--depth-ratio` from the frame, never left at 1) and one §4.1 verdict line "size (neighbour in another plane)" (P1b; CE-014, CE-015).
  - `reference/production-agents.md` §2 hard rule and §3 item 13.6, `reference/generation-system.md` §9 size bullet, `commands/analyze-with-loupe.md` X9 size bullet: the same clause (P1b).
  - `models/wan-3-0.md` §5 size row (CE-014/CE-015 out of the "agree" list; the caveat now says what was re-measured and that the limit holds for flat packs against a same-plane neighbour and is unproven for cans), §9 (the re-measure bullet replaced by its result; untested lever (e), pin the depth with a landmark, a same-depth neighbour and foreground negatives) (P1; CE-014, CE-015, CE-018).
  - Build prompt `Documents/prompts/analyze-with-loupe.txt` (backup `.bak-20261010-084135`): the QC sentence on the neighbour's depth.
  - No new part: the lesson fitted the existing sections.
- **Promoted:** none; the pointers of CE-014 and CE-015 were extended through the tool (status unchanged). **Left open:** CE-011, CE-014, CE-015 (model limit; CE-014/015 now graded unproven for cans), CE-018 (a3 passed the presence check but not size, so no verified prompt).
- **Suggested, not applied:**
  - `brand-guardrails.md` §2 "Context and audience": promote the general part of CE-008 (an adult-only product's captions and casting read as adult: no parent, K-12 school or curfew wording, characters who look 20 or older). Today it travels through the ledger read at A1 and the client's guardrail audit.
  - Add the delivered-flagged run-level records (run 08 V02 V06 V09 V10 V12 V18; run 09 V08 V09 V12 V13) as `--source agent` ledger entries, one per class and anchor with the videos listed; the size ones become evidence for P1 with their frames re-measured.
  - If the next run's depth-pinned placements land within 1.25x, relax the `wan-3-0.md` §5 passing-list rule for cans and keep it for flat packs.
  - A "depth miss" QC line (a placed product found nearer the lens than its planned anchor, with a threshold) once more than agent flags show it matters; the user has not reported it.
- **Design suggestions (structural, for the user):** the four held back by pass 1 (a `T agent-contract` command, a `T deliverables-check` command, a `T qc --track` option, a ledger source `run`) were re-read under item 7b of `update-from-errors.md` (new coupled parts are now allowed when the errors show them needed). They are not demanded yet: no run has happened since the pass-1 text rules (the canonical contract, the A9b and §6 checklists, steps 5f and 5g), so nothing shows those rules failing. They become needed if P2, P3 or P7 recur after a run under the new text.
- **To test:**
  - P1: on the next Recreate with placements on `wan3_0_prime`, write for every placed product the planned depth and the depth found on the frame, estimate A with its depth ratio and basis, estimate B, and whether they agree → proven when 5 of 5 reported sizes survive the user's eye. Lever (e): put a depth landmark, a same-depth neighbour and the foreground negatives into the first request → measure the frame fraction against the planned fraction; proven when 3 of 4 placements land within 1.25x with the depth read from the frame.
  - P2-P8: unchanged from pass 1 (no run since).

## 2026-10-10 · CE-001..CE-028 (whole ledger in scope; first pass under the generalisation contract, items 6b and §3.3b) · 7 gaps of form · commits 934c43e (edits) and 8c8de19 (log)
- **Scan:** unchanged from the pass above: no ledger entry and no run is newer, so the record set is the same (28 entries, the files they point to, the files that cite them, the 104 `result.json` of runs 01-09). Two more attempt diffs were read for the cards: run 09 V07 (request to a2) and V11 (a2 to a3 to a4).
- **Why this pass:** `update-from-errors.md` now asks for each lesson as a kind (achieve, avoid) with its miss, cause, prompt correction and what worked, and a fourth coverage element: the lesson held in that general form. The rules written by the two earlier passes were checked against it. Most were already in kind form (the catalog classes carry Rule, Breaks, Prompt, QC, Retry); seven were not.
- **Generalised (one line per lesson card):**
  - L1 counts: achieve every multiple keeps its number except through a visible cause / avoid a count that changes across an exit, occlusion or cut ← capsules 3 to 1 after a walk-past (CE-001); cause: the ledger tracked where, not how many; prompt: the catalog's "Exactly three … all three, while he walks past" (designed, no stored verified take); worked: delivered takes of runs 08 and 09 list CE-001 pass, and it caught two glasses (run 08 V10) and an extra can (run 09 V08); transfer: a pack of ten, a six-pack, wrappers.
  - L2 openings: achieve every use through the real opening after its preparation step / avoid use through a part with no opening ← a bottle drunk from the side without the spout (CE-002); cause: no affordance sheet; prompt: start state, action on the named part, result, one exclusion (designed); worked: CE-002 pass in the run 08 verdicts; transfer: a gum carton's flap, a tube's nozzle, a car's driver door.
  - L3 solidity: achieve every thrown or passing thing has a path relative to the product and a consequence / avoid pass-through, sinking, a hit with no consequence ← tossed paper through a plastic bottle (CE-003); cause: no path row, no solidity exclusion; worked: CE-003 pass with a hand passing in front of a can (run 09 V07); transfer: keys on a pack, a sleeve past a can.
  - L4 blend: achieve a placed product is lit, exposed, focused and angled like its neighbours / avoid its reference photo's light, pose and camera ← a can brighter and cooler than the room, squared to the lens (CE-004); cause: the reference's studio look inherited; prompt: scope the reference to shape, colour and label, state the room's light on it; worked: paste test 0 signs in later verdicts; transfer: a phone screen in daylight, a car on a cloudy street.
  - L5 size (gap of form, fixed): achieve an anchor from the guide's passing list and a size verdict from derived numbers at the product's own depth / avoid sizing words as the control on a flat pack, an assumed distance, a head at a different depth ← a carton 1.7x then 1.78x against the bottle it leans on (CE-011), a pack 1.5x against a phone (CE-009), a can "1.6x" that stood in front of the person (CE-014, CE-015), a false 2.8x (CE-028); cause: model limit for flat packs against a same-plane neighbour; QC that assumed the distance and the neighbour's depth; prompt: bad "about one fifth as tall as the bottle … one eighteenth of the frame height" (`wan-3-0.md` §4.0 item 10), good none verified; worked: nothing verified for packs; for cans unproven; transfer: a gum pack beside a phone, a bottle beside a laptop.
  - L6 posture, support, place: achieve a posture its shape allows, on a fixed natural surface the source frame shows, where a person would leave it / avoid a lean, a prop that moves, a thin sheet, a source beat taken over ← a sachet upright against the writer's forearm (CE-012), a carton leaning on nothing (CE-013), a sachet on the grill lid (CE-021), a pack on an exam sheet (CE-006), a pouch taking the bottle's pick-up (CE-007); cause: the support rule allowed a moving board and a lid; prompt: bad "stands upright … leaning back against … a notebook", good "lies flat on its wide face, label up, entirely on the bare marble … a band of bare marble wider than itself to his forearm" (verified, CE-012); worked: CE-012 (posture and support at 30 fps, 1.05x, in sync); a can standing on the grill's fixed shelf passed posture in V11 a4, not verified; the flat wording failed on a shelf and a glossy table; transfer: a can on a counter, not a tray; a phone on a desk, not a book.
  - L7 anchor persistence (gap of form, fixed): achieve the product in frame from frame 0, its spot named against a fixed neighbour and restated across cuts / avoid a loose spot, an appearance with no cause, a slide with no action ← a can absent until 4.2 s (CE-018), a can sliding between 1 s and 2 s (CE-019); cause: the can named late, a loose spot, QC at checkpoints only; prompt: bad "stands upright … in the centre of its length, between the roommate and the laptop", observed "at the left end of the table … a hand's width in from its left edge … does NOT move, slide … the cut hides no move" and "The can and the glass are both on the desk from the very first frame to the last"; worked: both observed to remove the symptom inside a shot (slide gone; can in frame from 0 s), neither take passed QC (the can relocated across a cut; size), so not verified (`wan-3-0.md` §4.0 items 11 and 12; `generation-system.md` §4b.5); transfer: a phone on a desk, a car parked at a curb.
  - L8 inserts, timeline, audio: achieve an insert cut on frames of its own content, every duration kept so the original audio stays one segment, fades over real motion / avoid the replaced performer in the edges, a shortened timeline, spliced audio, a frozen frame, a leftover rectangle ← CE-016, 024, 025, 026 (each fix caused the next error); cause: QC read the generated pieces, not the assembled timeline; worked: not verified (no run since); transfer: any insert or transition in any video.
  - L9 context-bearing overlays (gap of form, fixed): achieve the original element reused, on its visible frames, faded with the picture / avoid re-typing it, dropping it with its brand ← the dividend notification (CE-017, CE-023, CE-026); cause: a brand rule removed the information role; worked: not verified; transfer: a message, a receipt, an app banner.
  - L10 caption rewrites and keywords (gap of form, fixed): achieve a minimal rewrite that keeps subject and meaning, and a hook keyword placed word for word / avoid an unrelated line, a keyword dropped as a handle ← a finance caption turned into a grill joke (CE-022), "Financeaholic" dropped (CE-027); cause: the guardrail and handle defaults applied without asking what the text is for; worked: not verified; transfer: a health claim, a competitor's name, an ambassador's name.
  - L11 text placement and emoji: achieve every text layer centred, only the height following the reference, no emoji / avoid a sideways move, an emoji ← CE-010 and the user's emoji rule; worked: posX 0 in the run 09 verdicts; transfer: any caption in any video.
  - L12 brand and form fit (gap of form, fixed): achieve the brand chosen by scene fit before surface fit, and the product form that fits the scene's scale / avoid a brand with no tie to the scene, a large pack in a casual handheld scene ← a grill reference given to the focus brand (CE-020), a stand-up pouch in a phone-and-couch scene (CE-007); worked: not verified (the redo with the drink brand was delivered flagged for size only); transfer: a gym scene for a sports drink, a desk scene for a focus gum.
  - L13 audience reads adult (gap, fixed): achieve captions and casting that read adult when the audience is adult-only / avoid wording that implies a parent, a school or a curfew, a youngest-looking cast ← a caption with "mom" on an energy drink (CE-008); cause: the rule lived only in the ledger; worked: CE-008 pass in the run 08 verdicts, and the run 09 V03 brief swapped a student who read as a minor; transfer: a supplement, any adult-only product.
  - L14 agent contract and reconciliation: achieve a contract generated fresh each run, every flagged delivery recorded / avoid a copied contract that forbids recording ← run 09 (five agents recorded nothing); worked: not verified (no run since).
  - L15 moderation on a real face (gap of form, fixed): achieve a request the service accepts / avoid a third identical request ← run 09 V03 failed twice in ~15 s with no error text; prompt: plan without the video reference; worked: the attempt without it passed QC (once, unproven).
  - L16 source printed surfaces: achieve each printed surface replaced by a named concrete thing, the original in the exclusion line / avoid a description of blankness ← run 08 V01 V04, run 09 V04 V08; prompt: bad "a plain market chart with no readable text", good "replace its whole screen with a plain dark candlestick chart … no text, no headline" (verified, `wan-3-0.md` §4.0 item 9); worked: V04 retry; the gate boards stayed printed in 3 attempts.
  - L17 measurement discipline: achieve every size verdict from inputs derived on the frame (a distance, a neighbour at the product's own depth), two estimates that agree / avoid an assumed number reported as a flag ← CE-028, CE-014, CE-015; worked: the tool prints "provisional" and "inconclusive"; re-measured V01 and V03 (1x to 1.4x, unsettled).
- **Coverage:** L1-L4, L6, L8, L11, L14, L16, L17 covered (L8, L11, L14 unproven: no run since) · L5, L7, L9, L10, L12, L13, L15 gap of form, repaired.
- **Changes** (wording replaced or sentences added inside existing sections; no new part):
  - `anomaly-catalog.md` §2.7 Retry: the model-specific numbers ("12 of 12", the CE ids) replaced by the kind and a pointer to the guide, now consistent with the guide's caveat (L5).
  - `generation-system.md` §4b.1b (the guide's passing list no longer duplicated here: achieve and avoid, pointer), §4b.5 (new bullet: pin the spot to a fixed neighbour, with its miss and cause), §5c.2 (the moderation fallback rewritten as achieve, avoid, miss and cause) (L5, L7, L15).
  - `brand-guardrails.md` §2 (Context and audience row), §3 (adults only row), §5 (Audience check) (L13). `text-and-format.md` §1: the miss and cause of CE-022, CE-027, CE-017, CE-023, CE-026 beside their rules (L9, L10). `analysis-protocol.md` §5: the miss of CE-020 (L12).
  - `commands/analyze-with-loupe.md` A7 (new bullet "Then the form"), §6 wording (L12). `README.md` and the ledger header: the description of the command (generalisation).
  - `models/wan-3-0.md` §4.0: item 8 gets the shelf note, new items 10, 11, 12 (failed or observed, each with its miss and cause, none claimed verified); §5 opening-seconds row points to item 11 (L5, L6, L7).
  - Build prompt `Documents/prompts/analyze-with-loupe.txt` (backup `.bak-20261010-093234`): the update-from-errors paragraph (generalise, gap of form, samples with miss and cause, no generalising across models), the form-fit and audience cases, the spot pin.
- **Promoted:** CE-007 and CE-008 (fixed to promoted, with pointers). Pointers extended for CE-011, CE-018, CE-019, CE-021. **Left open:** CE-011, CE-014, CE-015, CE-018. Nothing marked verified (no new take passed QC).
- **Suggested, not applied:** the earlier suggestions stand (ledger entries for the delivered-flagged run-level records; relax the `wan-3-0.md` §5 passing-list rule for cans only if depth-pinned placements land within 1.25x; a "depth miss" QC line once more than agent flags show it matters). New: the CE-008 default ("an energy drink or supplement is adult-only") is the user's own entry made general; if it should apply only when a client document says so, say so and the row is narrowed.
- **Design suggestions (structural, for the user):** unchanged: `T agent-contract`, `T deliverables-check`, `T qc --track`, a ledger source `run`; not demanded, no run since.
- **To test:** L7: write the pinned-spot sentence (fixed neighbour, restated across cuts, "no sliding product") into the first request of every placement → measure the product's position against the neighbour every 0.25 s; proven when 4 of 5 placements hold across every cut. L5: as in the pass above. L13: the next adult-product run → proven when no user note about a caption or a character reading underage. L12: the next Recreate batch with two brands → proven when no user note about a brand with no tie to its scene.

## 2026-10-13 · CE-001..CE-094 (whole ledger; first pass over CE-029..CE-094) · 16 patterns · ledger retired · commit f878524 and its follow-up commits (wording fixes from the independent review; `git log -- analyze-with-loupe/` lists them)
- **The user's instruction:** "execute /update-from-errors for "analyze-with-loupe" command, then remove caught_errors files inserting each error entry completely, errors should no longer be inserted and saved in a different file because its causing ai agent context memory rot, and because we're firm we've had enough cases covered to be generalized for a final pipeline". Read as: (A) a normal pass over every entry; (B) every lesson written completely into its owning section (kind plus sample, not a copy of the 1.3 MB file); (C) the ledger mechanism retired. This overrides the update command's "never delete a ledger entry / never remove a command" for this one pipeline; the old file stays in git history (last commit `aba83d3`).
- **Scan:** record set = `caught_errors.md` (94 entries: 49 open, 25 promoted, 20 fixed; 84 on `wan3_0_prime`, 4 on `seedance_2_5`, 6 unknown/any; runs 05–12) read through a digest (fields without the attached briefs and prompts), plus the files the entries point to on disk: runs `20261007-232745-07`, `20261010-020703-09`, `20261012-230535-12`, `client-fixes-20261012` (briefs, plans, requests, `result.json`). Spot checks (§2): the retry requests `video-08-a2`, `video-09-a2` and `video-14-b2` of run 12 carry the "Image 4" guide as the entries record. CE-001..CE-028 were consumed by the three passes above; CE-029 was promoted by hand on 2026-10-10; CE-030..CE-094 (66 entries, 47 of them from run 12 on 2026-10-12/13) had never been consumed by a pass. `caught_flags.md` read as context, untouched. No run-level record lacked a ledger entry (every regenerated or flagged video of run 12 already had one), so no `R-` ids.
- **Consumed (so the next pass does not re-gather it):** every run folder up to and including `20261012-230535-12` and `client-fixes-20261012` (their briefs, requests, verdicts and `result.json`, including every RESIDUAL FAILURE or regenerated video, whether or not it had a ledger entry). With the ledger gone, the next pass must start from run folders created after 2026-10-13 and from the user's words given as the argument; it must not read older run-level records as new errors.
- **Diagnosis check (§2):** CE-084's size line corrected by its own text (the carton read 1.9× against the planned wood spot but ≈1.2× at its own depth); CE-085/CE-089 against CE-054: a sentence naming a forearm beside the hand drew a second fist twice and held once, so the rule says "name only the one hand and the bare empty area". All other diagnoses confirmed against the attached verdicts; frames not re-viewed except through the entries' own measurements.
- **Patterns** (P1–P9 are the earlier passes'; ids continue):
  - P10 Placed pack or can size and plane on `wan3_0_prime` (CE-034, 038, 040, 049, 050, 054, 057, 062, 064, 066, 070, 073–075, 077, 078, 081, 085, 088, 089 and CE-009/011/014/015; repeated; model limit). Words never moved it; a reference-image lever did.
  - P11 Guide design: what the guide copies (CE-052, 067, 069, 090, 093; repeated).
  - P12 Spot feasibility: frame 0, camera path, hand lanes, cluttered strips, nearest plane, neighbours the model snaps onto, frame edge (CE-053, 055, 056, 061, 072, 073, 076, 077, 082, 084, 087, 092; repeated).
  - P13 Posture: lying flat as the user's rule, and the model's standing renders (CE-037, 041, 059, 060, 063, 091, 094).
  - P14 Look and grounding (CE-043, 044, 058, 064; two users, verified).
  - P15 Label legibility, a pixel budget (CE-032, 036, 042, 090, 093; repeated, no fix has passed).
  - P16 Swap and removal grammar (CE-048, 064, 071, 084).
  - P17 Source preparation: a mirrored selfie, burned-in caption, identifying names and marks, a baked face effect (CE-030, 045, 051, 065, 080).
  - P18 Identity reference hygiene (CE-035, 039, 047, 053, 055, 062, 090; with CE-029).
  - P19 Scene state and the client's form ladder (CE-031, 033; users).
  - P20 Camera lock and pose lock (CE-056, 061, 068, 078).
  - P21 Cut-heavy references and emotion beats (CE-075, 079, 083, 086).
  - P22 Empty surfaces, per-shot state, invented limbs and objects (CE-046, 054, 074, 078, 085, 088).
  - P23 QC discipline: "close to the camera" as a reason, paste signs written as notes, "contact shadow present" without a crop (CE-034, 043, 058; users).
  - P24 Seedance 2.5 `video_edit` placement (CE-091..CE-094).
  - P25 The ledger itself: 1.3 MB read at every run start (the user's context-rot point).
- **Root causes:**
  - P10 model limit plus a wrong lever: the rule said "change the form or the anchor class", but every comparable retry in run 12 changed only the words or the anchor and failed; the lever that worked was an image the model copies (spot, size and look at once), eight times. The earlier rule assumed the only free lever was the anchor class.
  - P11 plan: guides were built ad hoc by each agent; the failures are what a guide carries by accident (the source frame, a flat paste, a soft label).
  - P12 plan: the planner named a surface from the card without checking frame 0, the camera path or the hands; the card did not record hand lanes, path coverage or strip widths.
  - P13 plan and model limit: the planner chose "upright for the label" (CE-036 geometry) against how people leave a pack; the model renders thin packs standing on open wood whatever the wording, and a stand-up pouch with upright references renders standing.
  - P14 reference: the look must be in the reference the object is drawn from; QC accepted "contact shadow present" without a 3× crop and a paste look as a note.
  - P15 model limit: small print under about 25 px is redrawn as letter-like shapes; resolution and padding raise sharpness, not legibility.
  - P16 wording: a swap written as an addition plus a negative; a source object removed by a negative only.
  - P17 plan: nothing in the preparation step handled a mirrored source, a burned-in caption on a wall, a name or a patch; the prompt cannot undo what the video reference carries.
  - P18 reference: the identity image brings everything in it.
  - P19 plan: a default ("sealed, untouched"; the next form down) ignored the scene's use and the client's form ladder.
  - P20, P21, P22 model limits found by exclusion; the camera-lock and empty-desk sentences were verified, the cut-heavy remedy is planned only.
  - P23 QC text: the checks were permissive in the wording agents follow.
  - P24 model limit (posture and support in an edit) plus guide copying.
  - P25 structure: lessons were piled in a file instead of the sections that own them.
- **Generalised (one line per lesson card; every Achieve/Avoid is a kind, the instances sit in the samples):**
  - L18 size lever: achieve a size-and-place guide as the control where size is a model limit / avoid sizing words ← CE-009, 011, 034, 054 (miss: 1.3–2.8× whatever the words); cause wrong lever; prompt bad "it fills about one twelfth of the frame height and keeps this size" → good "Image 4 is a size and placement guide only … exactly where Image 4 shows it … keeps the size it has in Image 4"; worked CE-054 a2 (A 1.20× / B 1.02×) and 7 more; transfer: a bottle beside a monitor, a phone on a counter.
  - L19 guide design: achieve the source's bare surface scrubbed of performer, clothing and lettering (Create: neutral texture), shaded product in perspective, sharp label, thin edge / avoid an unscrubbed source frame, a flat paste, a soft label ← CE-067, 069, 052, 093; worked CE-064 a4, CE-074 a2; transfer: any inserted object.
  - L20 spot feasibility: achieve a spot bare at frame 0, in frame along the path, outside every hand's lane, wider than the product, not the nearest plane unless the user marked it (then with a guide) / avoid the first free-looking surface ← CE-053..CE-092; worked CE-076 b2, CE-074 a2, CE-078 a2; transfer: a phone on a desk, a bottle on a counter.
  - L21 posture: achieve lies flat, left casually / avoid standing, fully displayed, a top-view reference for a pack laid flat ← CE-059, 060 (users), 037, 041; worked posture in CE-088 a4 / CE-041 a5 by reference; not verified for Seedance edits.
  - L22 look: achieve material sentence plus grounding in the reference the object is drawn from / avoid a pasted look written as a note ← CE-043 (user), 058 (user), 044, 064; worked CE-043 a3, CE-058/064 a4.
  - L23 label: achieve a label that reads at the delivered resolution (plan the pixel budget, record the limit) / avoid enlarging the pack, upscaling, "the main line reads" ← CE-032 (user), 036, 042, 090, 093; not verified (no fix passed).
  - L24 swap grammar: achieve a replacement anchored by neighbours, a named replacement for a removed object / avoid product-at-old-spot plus a negative ← CE-048, 071, 064; worked CE-048 a2 and CE-064 a4 (verified); CE-071 a2 removed the named can but shipped with another flaw (observed).
  - L25 source preparation: achieve the prepared copy carries what the output needs (flipped, inpainted, names removed) / avoid fixing in the prompt what the video reference carries ← CE-030 (user), 045, 065, 080, 051; worked CE-030 a2, CE-045 a3; not verified for names, patches by sentence (CE-075 shows the edit grammar works for patches) or a baked face effect.
  - L26 identity hygiene: achieve the face and nothing else of the person / avoid clothing, cut-off prints, negated glasses, open eyes over a hidden face ← CE-035, 039, 090, 053, 055, 062, 047; worked CE-039 a2 (plain tee), CE-047 a2; CE-035 observed 2 of 2.
  - L27 scene state and forms: achieve the state the scene implies, decided and stated in the plan; the client's forms keep their ladder / avoid sealed-by-default and a smaller fallback form ← CE-031 (user), 033 (user); worked CE-031 a2; CE-033 partial.
  - L28 camera lock and pose lock: achieve a camera-lock sentence for edge or orbit shots, compare the last third with the source / avoid a pack at the frame edge ← CE-056, 061, 068, 078; worked CE-078 a2.
  - L29 cut-heavy references: achieve separate clips on the reference's own cuts / avoid one clip with a person identity reference ← CE-079, 083, 086, 075; planned, not verified.
  - L30 empty surfaces and limbs: achieve surfaces written empty per shot, one hand named with the bare area / avoid "out of frame in shot 1", a named second limb ← CE-046, 078, 054, 085, 088; worked CE-046 a2, CE-078 a2; CE-054 a2 held while naming a forearm and CE-085/089 did not.
  - L31 QC wording: achieve "close to the camera" as a number, paste signs as regenerate reasons, a 3× base crop, the label read word by word, hand lanes ← CE-034, 043, 058, 032, 072, 076; tested by the next run.
  - L32 Seedance edit placement: achieve a guide sharp at the video's pixel scale, the support named below the neighbour, the posture the model keeps / avoid "lies flat" words alone ← CE-091..094; not verified.
- **Coverage:** L18–L32 gap (grep-confirmed absent before the pass: no mirrored-source rule, no guide, no hand lanes, no camera lock, no label legibility, no empty-surface rule, no identity hygiene); the earlier lessons (CE-001..CE-029) covered, unproven or promoted, unchanged except the size row, §2.7 Retry and the passing list, which the new evidence contradicted and which were replaced.
- **Changes** (additions inside existing sections; three new subsections, coupled; nothing removed from the pipeline's shape except the ledger):
  - `reference/generation-system.md`: new §4b.1c (spot feasibility), §4b.6 (size-and-place guide), §5c.2b (prepare the source), §3b.1 item 7 (cut-heavy references); §4 swap-as-replacement; §4b.1b posture and anchor class; §4b.2 casual; §4b.3 source frame 0; §4b.4 state follows use; §4b.5 empty surfaces; §5c.3 camera lock, left/right, emotion beats; §5c.5 pose lock; §8 checklist and §9 QC bullets (replacing the ledger lines); §10 template (guide line replaces "Caught errors applied").
  - `reference/anomaly-catalog.md`: §2.1 invented limb or object; §2.7 QC ("close to the camera") and Retry; §2.9 label legibility; §2.15 material, grounding, 3× crop, notes not allowed; §2.16 stand-up laid flat, hand lanes; §2.17 identity reference hygiene; §3 item 7; §4 step 5h and step 8; §4.1 five verdict lines; §5 three rows.
  - `reference/analysis-protocol.md` (card: Source preparation flags, lanes and path in Placement opportunities; §5 ranking: feasibility, cut structure; §6 ledger bullet removed), `text-and-format.md` (clean-plate lines never cut, ghost caption), `brand-guardrails.md` §4 (garment marks, names, named replacement), `assets-and-substitution.md` (identity photo, guide material), `production-agents.md` (contract: no ledger, attempts in the brief, new hard rules, §3 items 12–14, §5 item 3.1).
  - `models/wan-3-0.md` 1.3: §2.5 gotcha 10, §3.11b, §3.12, §3.14, §4.0 items 13–19 (verified samples), §5 rows (size row rewritten around the guide and a downgraded laptop-side class, eight new rows), §7, §9. `models/seedance-2-5.md` 1.1: §3.14, §5, §7, §9.
  - `commands/analyze-with-loupe.md`: item 22 rewritten (no ledger), §1 paths row removed, §2.2 Feedback first, A1/E1 ledger reads removed, A3/A6r/E5 flags and feasibility, A7 form ladder, A9b and §6 (attempt blocks instead of ledger reconcile), X1 spot and guide, X2, X4, X6, X9 (ledger bullet replaced by label, lanes/camera/orientation, attempt blocks), X9-R, §7 Never (ledger bullets replaced, two new).
  - `scripts/awl.py`: `caught-error` removed (command, parser, constants, `_ce_parse`); the `_ce_*` helpers stay because `caught-flag` uses them. `pipeline/preprocessing.md`, `README.md` (tree, case labels). Build prompt `Documents/prompts/analyze-with-loupe.txt` (backup `.bak-20261013-pre-ledger-retire`), `update-from-errors.txt` and `commands/update-from-errors.md` (AWL has no ledger now; the skill also takes the user's own words and runs on a pipeline with no ledger: frontmatter, §0 items 2 and 8, §1.1 step 5 and the no-record rule, the Never list).
  - Memory: `awl-caught-errors` rewritten as the retirement note, `awl-anomaly-catalog`, `update-from-errors-command`, `MEMORY.md`.
  - Independent review (a read-only subagent; each finding was checked against the files before any fix). The guide lever now reads the same everywhere: the passing list is in the hand, swapped for the source's own handheld object, or one flat sachet when the planned package is the sachet; a spot beside a large same-plane object, or in the near plane, needs a guide, and "form" in a retry is the integration form, never a smaller package (command A7). A near-plane spot the user marked stays, with a guide. The guide is built from the source's bare surface scrubbed of performer, clothing and lettering (Create: neutral texture only); the verified prompts state the relation to the named neighbour once, so "no sizing words" became "no fractions, padded-reference phrases or oversize exclusions relied on". The lying-flat default is the same in the agent contract and the Wan checklist, and Wan items 13 and 14 are marked as predating it. A mirrored source is flipped in Recreate and, in Edit Mode, only when the user asks. "Recorded" wording with no destination now points at the brief; "flavour tag" became "variant tag (flavour, size or model)"; `generation-system.md` has the `## 10. The short brief` heading that command X6 cites. Figures corrected: the size row reads 1.3–2.8× (3.51× was CE-028's invalid flag), a flat label seen from 23° above the table shows 0.39 of its height (CE-036), the label-legibility limit is stated for a small pack at its honest size (a 13×18 cm pouch read every line in CE-030 a2), and CE-045's verification covered two changes made together. Declined: the unescaped `|` in a code span of the command's §1 "Caught flags" row (older text, not this pass's).
- **Correction (user, same day): no tool removes captions in Analyze Mode.** The pass had added inpainting of burned-in captions and removal of names from the prepared source (§5c.2b, E5, card flags, checklists, Wan item 19, build prompt). Withdrawn: the method stays the original one, the clean-plate lines at top priority, never trimmed, plus the pushed character-swap script; names and patches are one named replace sentence. CE-045's lesson is now only "never trim the lines". Mirror flip stays. Edit Mode's own removal methods (text-and-format §2.2) are unchanged.
- **New parts and why they had to be new:** §4b.1c, §4b.6 and §5c.2b are new subsections because no existing section held a spot checklist, a reference-image lever or source preparation (CE-053..092 and CE-030/045/051/065/080); each is called from X1/X2/X4/X9, the §8 checklist, the production-agent contract, the Wan checklist and the build prompt. No new file, step or toolkit command. Follow-up the same day: `anomaly-catalog.md` §4 step 5i (shot structure) is new because L29 (cut-heavy references) had a prompting rule and no QC check (CE-079, CE-083, CE-086); it is called from X9, `generation-system.md` §9, production-agents contract item 13.9, the Wan failure row and the build prompt.
- **Retired:** `analyze-with-loupe/caught_errors.md` (94 entries, 1.3 MB; last version in git history, commit `aba83d3`), the `caught-error` toolkit command, the per-run `20-analysis/caught-errors.md` digest, the A1/E1 reads, the by-id checks in X1/X2/X9, the agents' recording duty and the wrap-up reconcile. Kept, as the user decided the same day: `caught_flags` and `awl.py caught-flag` (the flag record, 3 entries; later the same day it became the self-contained page `caught_flags.html`, with its viewer template `scripts/caught_flags_template.html`, which gathers the video, the request, every input with its file and thumbnail, the reference and the source segment and takes the agent's trigger, tags, asset, prompt words and video part; CF-001..003 were moved into it with nothing dropped), written whenever Higgsfield flags something and never read. Follow-up the same day: the A1/E1 digest read, the per-run `20-analysis/caught-flags.md`, the X4 check against it, the agents' reading-list entry, the "never start a run without reading it" rule, the flags file's "Who reads it" paragraph and the build prompt's matching sentences were removed; X4 now tests the plan against the references' service-block rules (`generation-system.md` §5c.2, `higgsfield/higgsfield-mcp.md` §9, the model guides' failure tables), and the preset-notice lesson of CF-002/CF-003 (a reroute, not a block; pass `declined_preset_id` from the start) moved into `higgsfield/higgsfield-mcp.md` §9. The writing, `T ledger set --flagged` and the main session's reconcile (it only lists flagged calls with no entry) stay. Out of scope: `analyze-then-generate/` (its own pipeline), the `runs/` folders (their old digests are inert run data).
- **Promoted / left open:** nothing marked (no ledger). Open lessons carried by their section: model-limit rows in `wan-3-0.md` §5/§9 (labels, laptop-side anchors, baked face effects, names), Seedance edit placement (`seedance-2-5.md` §3.14/§9), cut-heavy references (`generation-system.md` §3b.1 item 7, planned).
- **Suggested, not applied:**
  - The old `20-analysis/caught-errors.md` digests inside `runs/` are inert; delete them with the runs when no longer needed.
- **Design suggestions (structural, for the user):**
  - `T guide`: a toolkit command that builds the size-and-place guide (bare-surface crop, product render turned and shaded, soft shadow, scaled to the reckoned height) so agents stop writing ad hoc scripts; eight guided takes were built by hand, and the failures were construction errors. Needs a visual check by the agent, so held back.
  - `T prep-source`: one command for the preparation flags (hflip, caption inpaint, name removal) with a before/after sheet.
- **To test (next run):**
  - L18: a Recreate with placements on `wan3_0_prime`, the guide in the first request → proven when 4 of 5 first takes land within 1.25× (A and B agree) with the spot kept.
  - L20: the hand-lane map and path coverage on every placement → proven when no take shows a hand over the pack, a laptop-deck landing, or a product leaving the frame early.
  - L25: a mirrored selfie source → proven when the first take reads correctly (no user note about reversed text).
  - L23: the pixel budget → measure how many takes still show wrong letters when the wordmark is under 25 px; proven when the plan writes the limit in the brief before generating in every such case.
  - L29: the first cut-heavy reference generated as separate clips → proven when its cuts, cutaways and final emotion beat survive.
  - L31: the verdicts → proven when no paste sign appears as a note and every size line carries A, B and the depth basis.
- **Case-label map (each label → the section that holds its lesson; the entry text lives only in git history):**
  - CE-001 anomaly-catalog §2.1, §2.5 · CE-002 §1, §2.2, §2.3 · CE-003 §2.14 · CE-004 §2.15 · CE-005 §2.7 · CE-006 §2.14, §2.16 · CE-007 generation-system §4b.1b, command A7 · CE-008 brand-guardrails §2, §3, §5 · CE-009 wan-3-0 §5, catalog §2.7 · CE-010 capcut-assembly §3, text-and-format §3 · CE-011 wan-3-0 §5, §4.0 item 10, §9 · CE-012 catalog §2.16, wan §4.0 item 8 · CE-013 §2.16 · CE-014, CE-015 wan §5, §9, catalog §2.7 · CE-016 generation-system §3c, capcut-assembly §3, §5 · CE-017, CE-023 text-and-format §1 · CE-018, CE-019 generation-system §4b.3, §4b.5, wan §4.0 items 11–12 · CE-020 analysis-protocol §5, command A7 · CE-021 generation-system §4b.1, §4b.1b · CE-022, CE-027 text-and-format §1 · CE-024, CE-025, CE-026 generation-system §3c, capcut-assembly §3 · CE-028 catalog §2.7, §4 step 5d, production-agents · CE-029 catalog §2.17, §4 step 5e.
  - CE-030 generation-system §5c.2b, wan §4.0 item 17 · CE-031 §4b.4, wan item 17 · CE-032, CE-036, CE-042, CE-090 catalog §2.9 (legibility), §4 step 5h, wan §5 · CE-033 command A7 · CE-034 catalog §2.7 QC, §4b.6, wan item 14 · CE-035 catalog §2.17, wan §3.12 · CE-037, CE-041 generation-system §4b.1b, wan §5 · CE-038, CE-040 §4b.6, wan item 14 · CE-039 catalog §2.17, wan item 17 · CE-043, CE-044 catalog §2.15, wan item 15 · CE-045 text-and-format §1, §3, generation-system §5c.2b, wan item 19 · CE-046 generation-system §4b.5, wan item 18 · CE-047 §5c.3 · CE-048, CE-064 §4, §4b.6, wan item 16 · CE-049 wan §5 (passing list 1) · CE-050, CE-070 §4b.6, wan §5 · CE-051 §5c.2b, analysis-protocol §5 · CE-052, CE-067, CE-069 §4b.6, catalog §2.15 · CE-053 §4b.1c, §4b.3 · CE-054 §4b.6, catalog §2.1, wan item 13 · CE-055, CE-061 §4b.1c, wan §5 · CE-056 §4b.1c, §5c.3 · CE-057 §4b.1c · CE-058 catalog §2.15 · CE-059 §4b.1b · CE-060, CE-063 §4b.2 · CE-062 catalog §2.17 · CE-065 §5c.2b, brand-guardrails §4 · CE-066, CE-073, CE-081 §4b.1c, §4b.6 · CE-068 §4b.2, §5c.5 · CE-071 §4, brand-guardrails §4 · CE-072, CE-076 §4b.1c, catalog §2.16 · CE-074 §4b.1c, catalog §2.1 · CE-075 brand-guardrails §4, §4b.6 · CE-077, CE-082 §4b.1c, §4b.3 · CE-078 §4b.5, §5c.3, wan item 18 · CE-079, CE-083, CE-086 §3b.1 item 7 · CE-080 §5c.2b · CE-084, CE-087, CE-092 §4b.1c · CE-085, CE-088, CE-089 catalog §2.1 · CE-091, CE-093, CE-094 seedance §3.14, §5.

## 2026-10-18 · the learning command retired
- **What changed:** at the user's request the learning command that made the passes above is retired. The command, the skills, the README and the build prompt of this pipeline no longer refer to it. A lesson from a
  reported miss is written, generalised (what to achieve, what to avoid, the miss and its cause, the corrected wording, what worked), into the section that owns it, and only on the user's yes (`awl-feedback`,
  `awl-wrapup`); a flag whose rule is general or recurs is written the same way when the user asks. The dated sections above stay as the record of the four passes and of the retirement of the ledger.
- **Not touched:** the run folders (their briefs and results keep the words they were written with), and the retired command's own file and build prompt, which stay on disk unused.

## 2026-10-19 · Loupe is started and recorded at the start of every run
- **What changed:** run creation (`awl-start`) runs `T loupe ensure` and stores `state.json → loupe` (`up` or `down`); resume runs it again; the analyze-produce phase runs it before spawning the production agents and fills a "Loupe" line of the agent contract; the QC phase retries it once when `qc-consult` answers `mode: unavailable` on an `up` run and says in the verdict when no sample was consulted. `loupe ensure` prints `library_size` and boots the keeper or brings it up to date (`keeper.state`); Loupe's watcher keeps it current after the admin's later edits.
- **Why:** Loupe started only as a side effect of the first flag, consult or hint call, so five agents could race to start it and a run never recorded whether samples were available.
- **Checked:** the keeper was fed from the library through both toolkits (`library_size` 12, same samples returned by `qc-consult` of both), `keeper_sync.py` 39 offline and 13 live checks.
- **Hypotheses to test:** (1) a run started with Loupe stopped shows `library_size` in the start line and `loupe=up`; (2) with Loupe unable to start, the run records `down`, QC verdicts say "no sample consulted: Loupe unavailable" and the flags appear in Loupe after it is started.

## 2026-10-20 · the keeper asks instead of guessing
- **What changed:** the keeper's library digest now says where each sample came from (run, video, time, mode) and drops empty fields; the keeper may put a `needs` list in its answer (video plan, a frame of the video under QC, the request prompt, the product registry row, a sample's origin, a question for the QC agent) and Loupe fetches what it can, read-only and capped, into a folder of its own (two rounds of three at most, each round one keeper turn); what only the QC agent can answer returns as `needs_unmet`, answered once with `qc-consult --note`.
- **Why:** the keeper judged from the admin's words and the question alone, so a vague question got a generic answer and a gap was written in `not_covered`; it now asks, and the library stays the only thing it remembers (fetched data is evidence for one answer, never a sample).
- **Hypotheses to test:** (1) a vague question makes the keeper ask once or twice and the answer names what it looked at; (2) a specific question with checkpoints asks nothing; (3) the session's turn count stays within the rotation (a round counts as a turn).

## 2026-10-20 · coupling pass: run names, PDFs, the seam profile, inspection commands, the audio choice, a test suite
- **What changed:** every `--run` takes a full path, a bare run name or a unique stamp prefix (`resolve_run`; an ambiguous prefix is refused with the candidates; `AWL_HOME` points tests at a temp library copy). `doc-text`, `prep-assets` and `prep-all` extract PDFs with pypdf (layout text per page, `pages`, `chars`, `image_only`; the page images of an image-only PDF go to `docs/<D>-pages/`), and the skills no longer say to read PDFs with Read. `strip-inserts` prints a seam profile per cut point (luma and frame difference 0.5 s either side, numbers only; `T seams` does it for any video), and the Recreate plan reads it before a source is uploaded. `loupe ensure` waits at most 25 s for the keeper sync and reports `syncing` (Loupe finishes the sync and a consult waits on the same lock). `inventory` no longer guesses an asset's role from its file name. New gather-only commands: `status`, `doctor`, `lint-run`, `cost-report`. `awl-qc` asks the keeper once per video. Contract item 24: the user chooses at the start between Whisper speech-to-text and frames only (`state.json → audio_ingest`, the only source; no default anywhere); frames only writes no transcript and every speech field says `audio not ingested`. A test suite (`tests/`, `scripts/check_all.py`) covers the structure, the toolkit on scratch fixtures and the Loupe coupling with a fake keeper; a real-data suite is opt-in.
- **Why:** reproduced in the live Recreate run of 2026-10-19/20 and in this pass: `T state --run <bare name>` failed although the skills write `--run RUN`; `T doc-text` returned a stub for PDFs and Read renders at most 10 pages here; the insert out-point of one pick (7.52 s) sat inside a white flash the original's luma shows ending at 7.93 s, found by a planner reading frames by hand; `loupe ensure` could block up to 170 s while a consult of the same run waited 63 minutes behind the keeper lock; prompts of 4434-4975 characters stood against a 5000-character cap that nothing measured; a transcript file said "No speech detected." when no speech engine had run; file-name hints are the heuristic the user's rule forbids.
- **Not changed, for the user to decide:** the toolkit's remaining verdicts (`ledger begin` exit 3, `sync-check`, `scale`, `conform`, `qc`, `audio-profile`, `restore-audio`, `finalize`, `model-menu` quick picks, OCR noise), because skills, the contract and CE-028 wording depend on them; the 43 CRLF section files; Loupe, the hooks and settings.json (proposals in `Documents/prompts/coupling-report-2026-10-20.md`).
- **Checked:** `tests/run_all.py` t01 42, t02 42, t03 17 checks; `docs_tool.py check` 0 errors, 0 warnings; the measured Whisper cost (small, int8, CPU): a 15 s clip in 10 s, a 9 s clip in 18 s with the model load.
- **Hypotheses to test:** (1) with the seam profile read at A6r, no prepared source of a later run keeps a flash tail; (2) `lint-run` before spawning catches a prompt over the cap and an unknown media id before credits are spent; (3) a frames-only run's cards never say "no speech".

## 2026-10-20 · /analyze-with-loupe is born: a copy of the stable pipeline under new names, then every improvement the coupling pass found

- **Why a new command.** The user's decision of 2026-10-20: the stable pipeline and its live run stay untouched; the improvements go into a new command so that nothing is deformed and the user decides later which one stays. The functionality contract: the same golden-path rehearsal (`tests/rehearsal.py`, 118 steps for Analyze Recreate, Analyze Create and Edit on a temp copy with fake references, a stubbed speech-to-text, a Loupe server in the process and a fake keeper) runs on both; after the copy the two were identical step for step; after the changes the only differences are the ones listed here.
- **Scripts gather, agents decide (item 25).** The deciding functions the pipeline still had were replaced by the gather-only ones the user had accepted elsewhere: `sync-check` (numbers, exits 0, no verdict and no fix), `ledger begin` (records a pending entry every time and reports `conflicts`), `conform` (`lost_fraction`, `--dry-run`, never refuses), `scale` (`size_factor` per estimate, no provisional label), `qc` (measurements beside the expected values, `planned_text` beside `visible_text`), `audio-profile` (numbers and the spectral facts; the speech share stays null when the audio was not ingested), the OCR spans (numbers and spelling facts, no `kind_hint`), `restore-audio` and `finalize` (`facts`), `model-menu` (no picks). The rules of thumb moved into the references and the skills (sync 0.10 s, size 15 / 25 %, crop 12 %).
- **Loupe first-class.** The consult answer now carries the sample's title and origin (on the real library the admin wrote every miss in the title, and the agents had received it only inside the image); every keeper field is cut at a sentence end instead of mid-word (three real hints had their caveat cut mid-sentence); a run outside Loupe's folders is named as such; `needs_unmet` lists only what is unmet; `held_back_why`; the keeper runs in its own process group and is ended whole on a timeout, and the lock is acquired with a timeout (one real consult had waited 63 minutes behind a dead subprocess); `GET /api/qc/keeper/state` for `status` and `doctor`; the composite says that the RIGHT frame comes from another video and skips a zoom that would repeat the panel; kinds are suggested from the admin's words and confirmed by the admin; every `media_upload` answer is kept as a capture and `hf-put --capture` uploads from it.
- **The user's rules the library contradicted.** The preview was documented as the capcut-cli proxy (the rule: a 720×1280 burn); two prompt examples taught a faded product ("as muted as the room's", "slightly muted warm colour" in a verified case): the example clause is rewritten, the verified case keeps its words and carries the rule as a note after it.
- **From the live run of 2026-10-19/20.** QC fixes `ask` / `auto` (item 27, the question at the start, the fix proposal in `result.json`, the main session's question); pilot first (26); the stalled-agent recovery (28); the request freeze with `lint-run` reporting a request edited after its ledger entry (29); the planner contract (30); one uploads schema (`T uploads set|show|merge`, three hand-written shapes had polluted state.json); `T contract` (the canonical prompt filled from state.json, the placeholders it cannot fill listed); `T frames --grid`.
- **Tests.** t01 (structure: every `T <command> --flag` the texts cite exists; the old names are refused; the wiring of items 24–30), t02 (the converted commands fail on the toolkit as copied and pass after), t03, t05 (the hooks against a Loupe server in the process, a PUT server for `hf-put --capture`), `tests/rehearsal.py`; Loupe's keeper_sync 62 → 75 and selftest 89 → 93.

## 2026-10-20 · the Free sub-mode, and the QC-fixes choice for every Analyze sub-mode

- **Why.** The user (2026-10-20): the Analyze sub-modes decide the shape of the videos for the user; a third one must let the user say in their own words what the videos achieve and how, with references analysed first or from the requirement alone, still with the model's official prompting, the pipeline's features where they help, and Loupe's samples and misses throughout; and at the start the user chooses whether the QC agents fix a generation miss on their own or ask first, in every Analyze sub-mode.
- **What.** `awl-start` asks "Free", then with references or requirement only, then the requirement (typed or a file), kept verbatim in `00-inventory/requirement.md`; `state.json → analyze_submode=free`, `free_references`, later `videos_kind` and `free_plan_confirmed`. `awl-analyze-prepare` skips the references when there are none and hands off to the new `awl-free-plan` (A6f); with references, `awl-analyze-study` runs as always (the count from the requirement) and hands off to it. The free plan labels its lines [U]/[E]/[I], lists the past misses that touch the requirement (`T qc-brief` per product), is confirmed once, and gives each video a kind that selects the Recreate or the Create branch of every per-video step (the contract's "Video kind" line, `awl-plan-video`, `awl-write-request`, `awl-qc`, `awl-asset-plan`). The QC-fixes question (item 27) covers Recreate, Create and Free. Tests: t01 (20 skills, the Free wiring), the rehearsal (two Free paths: with references and requirement only, 208 steps in all).

## 2026-10-20 · the prompts of the two takes of a sample

- **Why.** The user (2026-10-20): when a miss has a correction, keep both prompt versions of the generation (the wrong take's and the corrected take's) in Loupe's database, never in the image, so the keeper and the agents that craft the prompts take them into account for future generations; without context rot; and nothing diffed or judged by code (the agents observe and judge).
- **What.** Loupe's report keeps `wrong_prompt`, `fixed_prompt` and the admin's one-line `prompt_note` (filled from the run's request file of the version picked, or pasted). Every list, brief, consult answer and hint carries only `prompts` (`pair`, `wrong`, `fixed`) and the note; the keeper's digest says PROMPTS OF BOTH TAKES SAVED and its role tells it to ask `sample_origin` for them (they come whole, as evidence) and judge itself what the corrected prompt did differently, never to assume. In this library `T sample-prompts --id S12 --run RUN` writes both whole to `RUN/40-briefs/samples/S12-prompts.md`; `plan-hints` and `qc-consult` print a `prompts_rule` when a hint or a relevant sample carries the marker. `awl-write-request`: read the pair only for a hint you apply (at most two per video), take the mechanism in the model's own structure and your words, never a sentence of either prompt; `awl-qc`: a lead for the diagnosed cause and the corrected request of a sample judged relevant, never a verdict. Tests: t03 (the marker and rule in both answers, the file with both prompts, an unknown id), Loupe selftest 96 → 106 and keeper_sync 75 → 81.

## 2026-10-22 · the labelled placement marker replaces the size-and-place guide image

- **Why.** The user (2026-10-22, the Celsius run's V09 pilot, on the prepared source with the can composited into it): a composited asset sample can be read by the model as the product's final look; next to the product the reference must say it is only a placement and size reference from the client's asset sample, and the generated video must show a real product rendered in the scene, not the pasted sample. Its size must be calculated (proportions, dimensions, distance) against the original video's objects of known size, with the real dimensions from the client assets. The blurred source-crop guide image: "never upload or use it ever again". Extended the same day: the rule covers every reference that places the product (a video reference, a layout or guide image, Create's neutral-texture guide, any placement image), each paired in the request with the placement-only sentence and the removal of the label and marks; a start or end frame is the literal first or last frame, so it carries no label and its product is photoreal and paste-tested.
- **What.** `T placeholder` (new, gather-only): a product render composited into a silent 9:16 source video (one or more `--window`s for cuts, punch-ins and set-ups) or into a placement image (`--image`), drawn at the real cm proportions, tone-matched to a sample, with a contact shadow, blur and grain, optional luma-follow (`--luma-ref`, `--luma-spans`) and occlusion (`--occlusion-mask`, `--skin`), a thin red outline and a short label beside it (Wan's convention for auxiliary marks); the sidecar records the boxes, the drawn size and the `--basis` lines with their arithmetic, and nothing is chosen by the tool. `generation-system.md` §4b.6 rewritten (the placement marker, the request sentences, the removal line, Create's marked texture, the start/end-frame exception, the old guide's evidence kept as history) and §4b.7 added (real dimensions from the assets, the distance from at least two neighbours of known size with their depth ratios, two estimates that agree within about 25 % before the marker is built, perspective, posture, occlusion, windows, the label). Pointed to it: generation-system §4b.1b, §4b.1c, §4b.2, §4b.3, §4b.5, §5c.2b, §6, §8, §9 (marker residue), §9b (a must-not-survive row), §10 (the brief's Marker line); anomaly-catalog §2.7, §2.9, §2.15, §2.16, §3, §4 (step 5j), §4.1, §5; analysis-protocol §5; assets-and-substitution §5; production-agents §2 ("Spot and marker"); the wan-3-0 guide (§2.5 gotcha 10, §3.6, §3.14, §4.0 items 10, 13, 14, §5, §7, §9), seedance-2-5 (§3.14, §5) and the start-frame notes of grok-video, minimax-hailuo, veo-3 and veo-3-1; the skills `awl-recreate-plan`, `awl-edit`, `awl-plan-video`, `awl-write-request`, `awl-inputs`, `awl-precheck`, `awl-qc`, `awl-analyze-produce`. Unverified: whether the locked model removes the outline and the label cleanly; X9 reads every take for residue. Tests: t01 +6 checks, t02 +8 checks, the rehearsal +3 steps.

## 2026-10-26 · the own voiceover (contract item 31): native driving audio, a lip-sync pass, or the voice over the video

- **Why.** The user (2026-10-26), after voicing a Kosovar-Albanian skincare ad with ElevenLabs: Analyze → Create must be able to use the user's own ElevenLabs
  voiceover in the generations (Free too, but only on the user's own decision: the pipeline must know where to find it and what to do, never suggest it); the
  user picks the voice (from the list, or by name or id) and the language, with an extra preference such as a Scottish accent or Kosovar Albanian. Then: the
  voiceover must be in the generated video natively, the generation using the audio and syncing the movements and lips to it, not placed in CapCut, where that
  is possible, and else the most accurate syncing approach. Then: native driving with Wan 3.0 as one option, and also the voice only placed over the video in
  CapCut (narration, a product review), selectable with every model.
- **What the guides say.** Seedance 2.5's `audio_references` carry timbre, accent and emotion only, and written dialogue wins over them: not a driving audio.
  A driving audio exists only in Wan 3.0 and Wan 3.0 Prime (reference mode: `image_references` + `audio_references`, never with `start_image`; ≤5 clips, ≤15 s)
  and Wan 2.7 (`start_image` + one audio as `driving_audio`, 2–30 s, cut at the duration; a shorter audio leaves silence). Higgsfield's `sync_so` (Sync Lipsync 3:
  `input_video` + `input_audio`, `sync_mode`) re-syncs any clip's mouth to an audio; it sits in `index.json → not_selectable.utility`, so it never enters the menu.
- **What changed.** Three methods the user picks at the start, before the model menu (`state.json → voiceover.method`): **native** (the take is the driving
  audio; the driving models lead the menu), **lipsync** (any model speaks the take's words verbatim, then a `sync_so` pass with the exact take, through the ledger
  as `--video NN-sync`), **overlay** (no dialogue; `T voiceover mix` lays the take over the picture and the CapCut project carries it on its own track).
  `reference/voiceover.md` (11 sections); the router's item 31, its labels row and the read-only ElevenLabs tools in allowed-tools (a paid take still asks);
  `awl-start` steps 2b (the method), 4 (the facts line, native options first), 5c (the voice list printed whole, then Voice, Language and Voice style in one call)
  and 6 (the keys); `awl-free-plan` step 2b (only from the requirement; open items inside the one confirmation, at most four questions); `awl-create-plan`,
  `awl-asset-plan` (lines and form under the method; native ≤15 s per generation); `awl-plan-video` (the X1 Voiceover block: the take, the fit, the durations by
  method); `awl-write-request`, `awl-inputs`, `awl-precheck`; `awl-postprocess` step 5b (once the picture passed: align, keep or lay back, the sync pass, the mix,
  the fallback) and step 6 (the voice by method); `awl-submit` (the sync pass's ledger lane); `awl-qc` (soundtrack, lips at three phrase starts and one pause,
  the face after a sync pass; the hand-off back to step 5b); `awl-record`, `awl-wrapup`, `awl-analyze-produce` (the contract line, the `voiceover` blocker, the
  pilot); production-agents §1–§4 (the "Voiceover: <voiceover>" line, the blocker, `result.json → voiceover`); capcut-assembly §3, §3b; higgsfield-mcp §5; the
  guides wan-3-0, wan-2-7 and seedance-2-5 §3.9. `T voiceover outdir | record | align | mix` (gather-only: it measures, records and mixes, never judges) and
  `T contract` fills the Voiceover line (`off` for a run without the key, so the run in progress is untouched); `T status` reports the choice and the takes.
- **Measured.** `eleven_v4`: 242 credits for a 240-character script (tags count). Albanian (`sq`) is in no official language list and still voiced well on
  2026-10-26. The MCP's `text_to_speech` writes only under its base path (another folder answers "not writeable"), and its file names hold brackets.
- **Inspection of the whole chain** (the user asked for anything missed, skipped or disconnected). Fixed: `awl-qc` had no route back to
  `awl-postprocess` step 5b once the picture passed (it went straight to the CapCut step) and a declined fix now applies the voice first;
  a planner fork (produce item 30) calls no generation tool, so the main session writes the lines and records the take before the fork
  plans the rest; `awl-feedback` handles a report about the voice (a new take, then by method) or the lips; the CapCut clip per method is
  named (overlay: the clean picture plus the voice track, never `with-voiceover.mp4`, whose voice would double; inserts split the voice
  track); a clip's sync pass is `NN-cK-sync`; a synced file whose sound is not the take gets it laid back; `result.json → clean` names the
  voiced file; `awl-model-guide` names the guide's §2.2 and §3.9 for a voiceover request; QC reads the `result.json` schema it writes into.
  Toolkit: `voiceover outdir` reads the server's own `ELEVENLABS_MCP_BASE_PATH` from `~/.claude.json` (the toolkit's shell never sees the
  server's env, so a custom base path would have been refused as "not writeable"); `voiceover record --span` takes one clip's part of a
  user's longer file; `lint-run` counts the ledger's job ids as known (a sync request names its clip's job) and reports the Voiceover line;
  `doctor` reports the ElevenLabs MCP and its base path, never the key. Also refreshed: 40-odd Read-now sizes that had drifted since
  2026-10-22 (generation-system §4b.6: 8.1 → 14.2 KB). The 26 citations `docs_tool.py coverage` still lists were read one by one: pointers
  inside rule texts and misattributions (`higgsfield-mcp.md` §9 counted as generation-system §9), none a read a step needs.
- **Tests.** t01 +8 checks (the reference, the router item, the start questions and their order, the Free rule, the wiring of 19 steps,
  the contract, the command); t02 +29 checks on synthetic tone bursts (record: phrases, pauses, spoken words, the kept earlier take, the
  state key, a transcribed own file, a clip's span; align: the built-in 0.25 s found at r=1.0; mix: the muted and the kept bed, the voice
  track, cut speech reported; outdir from the server's config without printing its key; the sync pass's ledger lane and its ids in
  lint-run; the contract's Voiceover line on and off). All suites: t01 78, t02 101, t03 30, t05 11; the rehearsal 211/211.
- **Hypotheses to test** (the pilot video of the first voiced run measures them):
  1. native on Wan 3.0 / Prime: the generated file's sound is the take (`T voiceover align` near 1 at near 0) and the on-camera speaker's mouth opens within
     0.1 s of each phrase start; proven when 3 of 3 voiced videos need no lay-back and no sync pass.
  2. `sync_so` keeps 720×1280 and the take as its soundtrack, and leaves the face unharmed (no blur, smear or doubled teeth around the mouth); its cost is read
     with `get_cost` on the first pass.
  3. lipsync's first generation on Seedance speaks the verbatim words in an unofficial language closely enough for the sync pass to land; else write the
     dialogue in the take's language and report how close the mouths came.
  4. a language outside the official list (Albanian) keeps its pronunciation over a whole run: the user's ear is the only check (no agent listens).

## 2026-10-26 · memes in Create (contract item 32), and the always-loaded text kept lean

- **Why.** The user (2026-10-26): Create must offer "include meme" and "don't include meme". Without memes "there is not meme screen record,
  video or any other type of meme or slip clip in the video, totally pure video generation content"; with memes, memes or other original
  clips go in between the generated parts, as the pipeline did for every Create run (it cut a reference's meme into the final whenever the
  style called for one, with no way for the user to say no). And: "make sure to avoid causing any memory context rot in pipeline agents".
- **What.** `awl-start` step 2c asks it in the same call as the voiceover method (header "Memes", "Include memes" / "No memes: pure
  generation", none recommended; `$ARGUMENTS` `memes` / `no-memes`); `state.json → memes` = `include` | `none`, a Create run without the key
  includes them (the run in progress is untouched). With `none`: no insert or meme sound of any kind, a reference's meme beat played by the
  generated scene, never by a generated copy; the choice wins over the house approach. Wired into `awl-create-plan` (the seeds),
  `awl-asset-plan` (the whole length is generated and counts), `awl-plan-video` (the insert plan, the sound plan), `awl-precheck` (X4),
  `awl-postprocess` (the CapCut project), `awl-qc` (an insert found is removed), `awl-free-plan` step 2c (the requirement decides; silent, an
  insert only as a visible [I] line of the confirmation), `awl-analyze-produce` and the contract (`T contract` fills "Memes: n/a | none |
  include | as your plan says"; `lint-run` reports the line; `status` prints `memes`); generation-system §3c, capcut-assembly §3, §3b, §5,
  creative-direction §4, analysis-protocol §2 state the condition. Router item 32.
- **Context budget.** Measured against the commit before items 31–32 (`e5ccec5`): the voiceover work had added about 11 KB to every
  production agent's always-loaded text (the per-video skills, the contract and its rules), even in runs without a voiceover. The method
  details now live only in `reference/voiceover/` sections that load when a run has one (the sync request and the durations moved into §8
  and §6, the store line into §1); each step keeps a one- or two-line pointer; the contract's duty paragraph is said once (§2), not again in
  §3; the contract lines are short; `T voiceover align` prints its summary and leaves every window in `vo-align.json`. Result: a production
  agent +4.7 KB of 112 KB (+4 %), the main session for a Create run +13.8 KB (+8 %), both including the inspection fixes and item 32.
- **Tests.** t01 +4 checks (item 32 in the router, the start question before the model menu, the wiring of eight skills, the contract line
  and §3c), t02 +2 (the Memes line for none and for a Create run without the key; status) and the lint-run and align checks extended (the
  Memes line; align's stdout without the window list). All suites: t01 82, t02 103, t03 30, t05 11.
- **Hypotheses to test:** (1) a `none` Create run delivers videos whose read-back timelines hold generated pieces only, and no reference's
  meme beat is replaced by a generated imitation; (2) a `none` run's longer generated length changes the 30 s permission count as planned;
  (3) the production agents of a voiced run read the voiceover sections once each and stay within their context with five agents running.

## 2026-10-27 · the effort level (contract item 33), no approval stops, and the original perspective

- **Why.** The user (2026-10-26 and 27): the pipeline takes too many resources and frames, which drains tokens; ask at the start how much
  to analyse, as an effort level of five steps (low, medium, high, xhigh, max = the earlier settings), without lowering anything the
  accuracy needs ("making it skip one second of the video ... losing data that needs to be processed from the source") and without context
  rot; "no change should be made on the loupe or its agents whether on qc agents or others because the judge agents should always be
  stable"; "no more questions like these" (an upload approval, a "go for uploading and generating?"); and "video should be in the original
  perspective not reverted/mirrored".
- **Where the frames went** (run `20261021-224049-21`): reference storyboards and close-ups at analysis (766 baseline frames, 291 motion-peak
  frames, 33 close-up sheets for 16 references), and above all QC (30 fps checkpoint sheets and 30 to 49 single frames per pass). QC was
  then kept out of the level at the user's word, so the level saves at analysis and spreads the spending.
- **What.** `awl-start` step 5d asks the level in the same call as the QC-fixes and audio questions (`effort.md` §1, read once: the five
  levels as a table, four buttons, XHigh and custom numbers through Other). `T effort` stores it in `state.json → effort` (custom values
  held to the floors); `T prep-all` reads the reference sampling (fps, the dense rate, the motion peaks, their ±0.5 s window kept at every
  level), the analysts keep the close-up budget (analysis-protocol §1 and the §7 prompt), and the produce phase takes the agents at once and
  the pilot threshold. QC, its Loupe consult, the `qc` command and the agent contract are exactly as at the last push (`c96a742`; the `qc`
  code is restored byte for byte; t01 guards that no effort setting reaches them). No pixel size changes at any level.
- **No approval stops.** The upload-approval stops came from a standing note of 2026-10-22, already revoked in the user's memory and in
  the live runs' contracts on 2026-10-27; the router (item 15), the produce phase and X3 now say it themselves: no reference review and no
  "Go" before an upload or a generation. The long-video permission (A7b) and the QC-fix question (only with `ask`) stay as designed.
- **Orientation.** `generation-system.md` §5c.2b flipped a front-camera selfie source before upload (CE-030, on the client's "maybe flip
  video, then add bag"), so those outputs came out mirrored against the original. Now a source is never flipped in any mode: a selfie keeps
  its reversed print as the original shows it, the product label reads correctly, and only a mirrored identity photo is turned true. The
  same rule in §5c.3, §8, analysis-protocol §3 and §5, anomaly-catalog §4.1 and §5, and the wan-3-0 guide (§4.0 note, §5, §7). Live runs
  prepared from flipped sources before this (the Celsius run's videos 01 and 08, run `20261026-222435-26` video 04) are left to their
  session.
- **Tests.** t01 87 (the effort reference and wiring, the no-approval lines, the guard that no effort setting reaches QC or the contract),
  t02 113 (the five levels, the bounds, prep-all reading the level, every second sampled at the lowest level, the ±0.5 s peak window on a
  moving source, qc unchanged, no Effort line in the contract), t03 30, t05 11; the rehearsal 211/211.
- **Hypotheses to test:** (1) a Medium run reads about 40 % fewer reference storyboard cells than a Max run with the same cards; (2) two
  agents at once keep a long run under the usage limit without changing any verdict; (3) a selfie source kept in its own orientation is
  accepted by the user with its reversed print beside the correctly read label.

## 2026-10-27 · Loupe: a zoom only under a marked frame; either side of a miss can be the original or another generation

- **Why.** The user (2026-10-27): "when there is no circel,arrow or square in a frame no need for the bottom zoom frame example at all"; Video A
  ("the version as generated") "can also pick the original video too or even from other generations on both sides wrong and right/correct"; and
  this command stays in step with the change.
- **What (Loupe).** A frame gets a zoom only when the admin marked it with a circle, an arrow or a box, cut around its own marks (none for an
  unmarked frame or a text label alone, none when its own marks cover most of it). Either side of a report can be the video's original, read
  from the run's own records only (the source clip the requests or `state.json` name, as the inventory holds it, and the source as each
  generation sent it: `source_prepared`, the first video input, the video's uploads record), a take of another video of the run, or a take of
  another run's video. Each frame's tag names its source (`as generated`, `correct version`, `original video`, plus `· video NN` or
  `· run R video NN`), the image's legend says the same, the words are kept with each frame of the moment, and the keeper's role and the brief
  carry them. The prompt fill and the product sample of a take of another video read that video's own request; the original fills no prompt.
- **What (here).** `awl-qc` (Samples first) describes the source tags and the zoom rule, so a QC agent never takes a frame tagged
  `original video` for a generated one; README (Generation misses), the `qc-consult` docstring and the build prompt say the same, and t01
  guards the skill's wording. The QC procedure is unchanged (the judges stay stable): `qc-consult`, `qc-brief`, `plan-hints`,
  `sample-prompts`, the agent contract and every step of a run are as before, and the consult's `frames` already carried each frame's source.
- **Tests.** t01 89, t02 113, t03 30, t05 11; Loupe: selftest 147, keeper_sync 91, page_smoke, transport_check and flags_smoke pass.
- **The product sample (same day).** On a report of this command's runs Loupe found no product sample ("i cannot see the product can nor include
  it in the miss sample frame"): this command writes each input's meaning on the input itself in `params.medias` and keeps its registry in
  `state.json → assets.product` with variants, and Loupe read only a `medias_meaning` table and `assets.products`. Loupe now reads both forms,
  names the product in the request's own words and fills a new report's product field with it; nothing in this command changed.

## 2026-10-28 · all five effort levels, never skipped; the user's folders read-only (item 34); the Loupe coupling in step
- **Reported:** the effort question offered four levels (Low, Medium, High, Max; XHigh only by typing it into Other), and a parallel run of
  another command never asked (that command has no effort level; the user: only this command matters). The user wants all five, every run,
  and each one adjusting what it should. Separately, all 15 videos of `Documents.10` went to the Recycle Bin at 23:30:59 in one batch while
  run `20261027-224009-27` was reading the folder (copied back from Downloads at 23:39:04; run `20261027-233328-27`, started at 23:33,
  inventoried an empty folder). The user: agents never remove or move reference files; what they need elsewhere they copy.
- **Causes:** AskUserQuestion holds at most four options, and its dialog hides the table printed above it. A level that was never stored
  ran silently at Max. Static thinning counted a still stretch only from 3 duplicate frames, which a still second never reaches at 2 or 3 fps,
  so Low and Medium kept every frame of a still shot and Medium could cost more than High. Nothing kept a session or an agent from deleting
  or moving a reference; who sent the 15 videos to the Recycle Bin is not on record (no session transcript was read). The Loupe audit found
  the consult timeout (190 s) shorter than Loupe's own limits (a 209 s consult lost its paid answer), reconcile reading only the newest 30
  captures (29 were upload answers), `--capture` seeing only the newest 200, and a queued flag's `CF-Q…` id lost once Loupe recorded it.
- **Changes:** effort §1 and awl-start 5d, step 6, rule 33 and never-line: asked in plain chat, the five levels numbered, never a question
  dialog; `T new-run` writes `effort: null` and `T prep-all` and `T effort` stop until the answer is stored (no key = a run made before item
  33, kept at Max); the router's item 33 and resume line. Still-stretch thinning: 3 duplicates at 4 fps and up, as before; below 4 fps a
  whole still second counts (QC never uses it). Item 34 in the router, a line in the production agents' contract and in the analysis
  agents' prompt, and `hooks/awl_input_guard.py` registered for Bash, PowerShell, Write, Edit, MultiEdit and NotebookEdit. awl.py:
  `CONSULT_TIMEOUT` (600 s, `AWL_CONSULT_TIMEOUT`), reconcile lists the flag captures and counts the upload answers, `_capture_full`, the
  queued flag's log note and its resolution (`caught-flag set --id CF-Q…` after Loupe recorded it). Wording kept in step with Loupe in
  awl-start, awl-write-request, awl-inputs and the README. Unchanged: Loupe, the QC skill, the `qc` command, the judges' rules.
- **Verified:** t01 90, t02 123, t03 35, t05 43 checks and the rehearsal's 216 steps pass. t02 runs every level on a 40 s clip of eight motion
  bursts: the stored column equals effort §1's table and prep-all samples it (2/3/4/5/5 fps, 6/8/10/10/10 around motion, at most 4/5/6/8/8
  peaks, every second covered; storyboard cells 112 < 135 < 152 < 197 = 197). The real runs agree: `20261027-224009-27` (Medium) sampled at
  3 fps, 8 around motion, at most 5 peaks; `20261027-233328-27` (High) at 4 fps, 10 around motion, at most 6. The guard hook refuses
  `Remove-Item` in `Documents.10` and an `rm` in `Documents.10` and lets a copy into a run through (about 0.1 s per shell call).
- **Independent review (same day), and what it changed:** the guard hook read every open run's `state.json` on every shell call, and on
  Windows a reader makes the toolkit's `os.replace` fail (measured 145 of 300 with three readers; the hook's own shared read still 61):
  `write_json`/`write_text` now retry a blocked replace (0 of 300) and the uploads merge writes atomically too. The guard was rewritten:
  verbs at command position only (a note saying "move" passes), variables, loops, nested shells, line continuations, `..`, a parent
  folder's delete, overwrites (copy, redirection, Set-Content, ffmpeg output), heredoc data never read as commands, a verb on an unset
  variable let through, Python checked call by call with the names that hold a reference path (str.replace is no file replace), and a run
  idle for 7 days releases its folders. Still stretches at 2 fps are left unthinned again (thinning saved no cell there); 3 fps thins from
  2 duplicates. The consult waits 780 s (Loupe's worst case 720 s). `T state set effort.x=…` works on the empty level. Wording: "5 for a
  run made before item 33" (an empty level stops), the close-up budget's no cap, the examples folder read-only in the analysts' prompt,
  Edit Mode and the prepare step name the effort stop. A known edge left as it is: a `caught-flag set` that lands while Loupe is in the
  middle of ingesting that queued flag can be lost (Loupe saves the copy it read).
- **Verified after the review:** t01 90, t02 123, t03 35, t05 73 checks and the rehearsal's 216 steps pass; the guard, dry-run on the real
  open runs, lets the pipeline's own commands through (split-audio, inventory, strip-inserts, frames, copies into 55-references, ffmpeg
  reads, python heredocs that read the references, cleanups in the run folder) and refuses `rm` and `Get-ChildItem | Remove-Item` in
  `Documents\27.10`.

## 2026-10-28 · the judge writes the prompt template; the judge on Opus, a collector with no verdict; QC fixes off
- **Reported:** a sample's collection (`S32.json`) showed the session that read its picture concluding about the two prompts itself, while the
  judge never saw both prompts whole. The user: the judge is an Opus 5.5 agent, the Haiku agent on Loupe only collects data and gives no verdict,
  and the QC, keeper and judge agents on Opus decide, pass flags or ask for more. Then: the judge must not only inspect a prompt the pipeline
  wrote; the agent working on a video briefs the judge (what it works on, what the video is about, what it wants to achieve), the judge gives a
  prompt template from what worked and what failed before, the agent crafts its prompt from it and generates, and the judge is consulted again
  only after the generation, when QC has caught errors, with enough details to answer accurately; the generation video model goes to the judge
  too. And a third QC-fixes choice: no QC agent after the first generation at all; the user instructs fixes once everything is delivered.
- **Causes:** the reader was given the prompts and asked for a mechanism, so it judged; the keeper defaulted to Haiku and fetched the prompts
  only on request (cut at 4000 characters); X2 only asked for at most three text hints; the QC consult went in before QC had looked and carried
  no prompt, template or brief.
- **Changed:** Loupe: the keeper (the judge) runs on Opus 5.5, the collector on Haiku with no verdict and no prompts (marked, right_version,
  product_and_scene, admin_words, unclear); every cited sample's prompts reach the judge whole before an answer is final (`prompts_judged`); a
  template purpose (step 1 the samples it needs, step 2 both prompts whole, then the template, basis, notes, changes); a QC question carries the
  request prompt, its params, the video model, the template and the brief, and the answer adds `cause` and `template_fix`. Here: `T
  prompt-template` at X2 (the brief file, the pattern card as the structure, the video model's index entry; busy retried three times; saved as
  `40-briefs/video-NN-template.json` and `.md`), the "Judge's template" block that X4 checks and X6 copies, QC's consult after its first pass
  with `--attempt` and `evidence_sent`, `result.json → judge`, `prompts_files` written by every consult, the consult timeout 1080 s, the
  production agents spawned on Opus, and QC fixes `off` (the start question, the contract's line and its skip of awl-qc, X8's hand-off to X10,
  the pilot's technical outcome, the wrap-up's feedback question as the review). Loupe's miss screens: a report and its samples edited where
  they stand, the product sample ticked from every image the generation used, and frames that survive a take the browser cannot play.
- **Verified:** t01, t02, t03 and t05 pass and the rehearsal runs 220 steps (`prompt-template` included); Loupe's selftest 168, keeper_sync 91,
  transport, page and flags smoke tests pass.

## 2026-10-28 · X4b: the judge writes the final prompt after X1–X4, and nothing deforms it
- **Reported:** the pre-generation check (X4) ran after the request was crafted from the judge's template and could change it. The user: X4 must
  know the prompt is the judge's and not deform it, at most mix in something carefully and only if needed, best not tweak it at all; better, run
  X1 to X4 first, then pass the full brief to the judge, and run on the judge's template.
- **Changed:** X2 writes the pipeline's own request as the checked draft, with a "Must carry" block and `40-briefs/video-NN-musts.md` (the
  sentences the prompt must carry word for word); X4 checks the draft and those lines; X4b (`awl-precheck`) sends the judge the whole checked brief
  (`T prompt-template`: the judge brief, the draft's prompt, parameters and inputs, the must-carry lines, the pattern card, the video model) and
  `T template-apply` puts the judge's final prompt in the request word for word (the draft kept as `video-NN-request.draft.json`; facts reported:
  must-carry lines missing, slots left, length against 5000). Nothing rewrites it: a missing line or a length over the limit is asked of the judge
  once more, only then `--add-must` (word for word, at the end) or `--use-draft`. A regeneration takes the judge's `template_fix`. Loupe's role
  says the template is the final prompt, built on the checked draft, every must-carry line word for word. The QC consult says when the prompt used
  is the judge's, its slots filled.
- **Verified:** t01, t02 (template-apply), t03 (the whole brief reaches the judge; the prompt applied; QC knows it), t05 pass; the rehearsal runs
  224 steps; Loupe's selftest 171, keeper_sync 91 and the page test pass.

## 2026-10-28 · A take made of several generations: one prompt field per side, each generation's prompt under its seconds
- **Reported:** some clips have more than one generation (video-02 of the Neuro run is c1 0–6.1 s and c2 6.1–12.433 s). When a miss's frames
  come from different generations, the prompt of each must be saved, with the seconds it is responsible for, so the judge knows which frames
  each prompt made. The user then gave the form: one field per side. The Wrong frames' prompts go in "Prompt of Video A (as generated)"; two
  Wrong frames from different generations put both prompts in that one field, each under "This is the prompt responsible for frames generated
  from second 0 to x" and the like. The same goes for the Right frames. No multiple prompt boxes.
- **Changed (Loupe b05bcf2):** Loupe reads a joined take as one generation per clip, with its request, prompt and seconds. The form writes
  the prompts of the generations the frames come from into the side's one field, each under that line, and the field follows the frames until
  the admin types in it. The take's generations are saved beside the field, so the judge gets, sample by sample, the prompt of each generation
  that sample's frames come from. `awl.py sample-prompts` writes the same into `40-briefs/samples/<id>-prompts.md`, under one heading per
  generation (`Generation k of n · clip · request`). Each heading carries the line with its seconds and the sample's frames from it.
- **Verified:** t03 (the generation of the sample's WRONG frame alone; the second generation alone when the frame falls in it) passes;
  Loupe's selftest 183, keeper_sync 91, page_smoke and transport_check pass.

## 2026-10-28 · The placement marker removed: the original video is the only reference
- **Reported:** video-02 of the Neuro run was generated in two parts because of Wan 3.0 Prime's 15 s limit on reference video per request.
  Each request sent the original span plus the placement preview (the same span with the pack's spot and size marked), so a pair for the full
  12.4 s would have been about 25 s, and the source was split on its own cut at 6.10 s. The user: "remove the reference placement from the
  analyze-with-loupe totally ... just let the original video as a reference, i believe prompts,images and instructions suffice".
- **Changed:** the `placeholder` command is gone from `awl.py`, with its tests. `generation-system.md` §4b.6 (the placement marker) and
  §4b.7 (reckoning the marker) are deleted; their general rules moved to §4b.5. These are: the original reference as the only video reference
  (the silent footage of the plan's span, in the model's most preserving input, within the model's own limit, a longer source split on its own
  cuts); no placement image of any kind, in any mode, and never a guide image cut from a source frame; padded product views; the one hand named
  with the bare empty area; start and end frames photoreal and paste-tested. The skills, the X4 and X9 checks, the agent contract, the brief and
  the model guides lost the marker. The guides' halved limits ("up to 7.5 s" for the pair) went back to each model's own limit. Size: the prompt
  carries the spot (pinned to a fixed neighbour) and the size (against a named neighbour). Where a guide lists size as a model limit, the
  anchor class or the integration form is the lever, and otherwise the size risk is written in the brief; QC measures it with `T scale`. The
  retry levers are the integration form, the spot or the anchor class. §9b's marker-residue row went too, which puts its row numbers back.
- **Verified:** `docs_tool.py check` 0 errors; t01 now guards that no step, section, guide or the README speaks of a placement marker or
  preview and that no `placeholder` command exists; t01, t02, t03, t05 and the rehearsal pass.

## 2026-10-28 · A frame ties back to the prompt that made it
- **Reported:** the prompt line named Video A, but nothing in the sample's image tied a frame to it ("no Video A placeholder or something else that would
  tie the frame back to the prompt"); the line should also say which frames it is responsible for ("frame 1,3,4 or similar").
- **Changed (Loupe):** each frame's tag in the image has two lines: `FRAME n · WRONG · m:ss.ss`, and under it `VIDEO A · as generated · generation k of n ·
  clip cK (from–to s)`. meta.json, the keeper's digest and the brief name each frame the same way. The prompt line leads with the frames: "This is the prompt
  responsible for Frame 1 (WRONG, 0:03.00) and Frame 3 (WRONG, 0:05.20) of this sample: it generated second 0 to second 6.1 of Video A (generation 1 of 2 ·
  clip c1 · request)". `awl.py sample-prompts` writes the same line under each `Generation k of n` heading.
- **Verified:** t03 passes; Loupe's selftest 186, keeper_sync 91, page_smoke, transport_check and flags_smoke pass.

## 2026-10-28 · Example prompts: prompts behind Example frames are never wrong or corrected
- **Reported:** a report may have only Example frames; its filled prompts must be marked Example, not wrong and not right or corrected, "so that it
  doesnt cause any ambiguity on the qc judge or keeper".
- **Changed (Loupe):** a side's prompt is an Example prompt when its field speaks only for Example frames, or when every frame of the sample is an
  Example (`prompt_roles`). The judge's text, the digest, the brief, the form's labels, the samples page and the reports list name it the example take
  of Video A or B. `awl.py sample-prompts` heads it `## Prompt of the example take of Video A` and returns `prompt_roles`; a sample of Examples only
  gets a closing note that neither prompt is a wrong or a corrected one.
- **Verified:** t03 (a sample of Example frames only) passes; Loupe's selftest 191, keeper_sync 91, page_smoke pass.

## 2026-10-28 · What each sample prompt is: the flawed version's, the correct take's, or just an example
- **Reported:** it must be known in the database and by every agent fed with the prompts that an Example's prompt is just an example (neither bad
  nor right). Otherwise Video A's prompt is the one that generated the flawed version, and Video B's is the correct take's.
- **Changed (Loupe):** the report keeps `wrong_prompt_role` (flawed | example) and `fixed_prompt_role` (correct | example), written on every save.
  The judge's text, the digest, the brief, the keeper's roles, the template request and the form name the prompts so. In this library,
  `qc-consult` and `plan-hints` say it in their prompts rules, `sample-prompts` heads them `## Prompt of the flawed take (Video A: its prompt
  generated the flawed version)` and `## Prompt of the correct take (Video B)`, and the QC and pre-check skills and the README use the same words.
- **Verified:** t01, t02, t03, t05 pass; Loupe's selftest 195, keeper_sync 91, page_smoke pass.

## 2026-10-29 · What an Example is: a suggestion, never mixed with a miss in one sample
- **Reported (2026-10-28):** an Example is not a bad generation nor a correct one; it is what could have changed, how one thing could have been done another
  way, a suggestion. A sample with Wrong or Right frames has no Examples, and a sample with Examples has only Examples.
- **Changed:** Loupe refuses a sample that mixes them, and its form warns and does not save one. Images with Example frames carry a legend line that says what
  an Example is, and every description (Loupe's roles, judge text, digest, brief, form; this library's prompts file, consult and hint rules, the QC and
  pre-check skills, the README) says a suggestion of what could have changed or how one thing could have been done another way, neither a bad generation nor a correct one.
- **Verified:** t01, t02, t03, t05 pass; Loupe's selftest 197, keeper_sync 91, page_smoke pass.

## 2026-10-29 · An Examples sample has one prompt box, its one video's
- **Reported:** "examples -> one fill from prompt box since we will only use one video for examples (but there could by many generations in one video all generations prompts should be filled there in that box with information which prompt is from which second until which, as we already do), and then there's right or wrong who have two input boxes for prompt fillings".
- **Changed:** Loupe's form gives an Examples sample one box, the video its frames come from, filled with the prompt of every generation of that video
  under the seconds it made; the other box is never filled. Example frames from two videos are warned about and refused. The judge's text, the
  `?prompts=1` answer (`prompt_sides`), the digest marker and the brief give only the boxes a sample speaks through. `sample-prompts` writes the one box
  alone, headed as the prompt of the example video, and returns `prompt_sides`; the consult and hint rules, the command's help and the QC skill say an
  Examples sample keeps one prompt.
- **Verified:** t01, t02, t03 (50), t05 pass; Loupe's selftest 201, keeper_sync 91, page_smoke, transport_check, flags_smoke pass.

## 2026-10-29 · One record per sample, the judge's flags, a lean digest
- **Reported:** "when the loupe qc keeper, judge or any other ai agent processes the generation misses it need them to be tied and fed in accordance ... for sample 1 these are the prompts,frames, user feedback and other stuff, and then so on for the other samples ... even if all the samples are tossed to the agents in one go then separate them clearly so that they can easily be differentiated what caused what, everything needs to be connected and known in which "generation miss" it corresponds to"; then "the agents are to be able to see all samples, but just be able to differentiate between them and be able to know which prompt,video,frame,feedback and verdict corresponds to which sample ... but also be able to pass flags, or ask for something if something's missing or causing ambiguity, also make sure to avoid memory context rot, also make sure everything is coupled and in sync".
- **Changed:** Loupe hands every sample as one record between `=== SAMPLE S12 · generation miss R7 ... ===` and `=== END OF SAMPLE S12 ===`: the
  admin's words tied to the frames, every frame with its video, generation, marks and the label of the prompt that made it (`made by S12-P1`), every
  prompt under its label. The keeper's digest keeps its records lean (each part explained once); the judge can pass `flags` beside `needs`.
  `sample-prompts` writes the sample's whole record; qc-consult, plan-hints and prompt-template pass the flags on with a `flags_rule`.
- **Verified:** t01, t02, t03, t05 pass; Loupe's selftest 208, keeper_sync 92, page_smoke pass.

## 2026-10-29 · Video generation prompts whole; every part of a sample's record names its sample
- **Reported:** "make sure to not trim the video generation prompts at all without any exception because we need them fully,and also make sure to give enough separation context for each sample or its elements even if it makes each sample a bit more bigger in bytes".
- **Changed:** nothing cuts a video generation prompt any more: `prompt-template` sends the brief and the structure whole (no `BRIEF_CHARS`,
  `STRUCTURE_CHARS`, `brief_cut`, `structure_cut`, `template_cut`), the caught-flag listing keeps the prompts whole; Loupe keeps every prompt,
  template, template_fix and request prompt whole. A sample's record names its sample on every line (`S12 · ...`, `S12-P1`, headings with the id).
- **Verified:** t01, t02, t03, t05 pass; Loupe's selftest and keeper_sync pass.

## 2026-10-29 · Text size 11 when a video has only a little text
- **Reported:** "when there's little text to place over the video in capcut edits and our standard text size is 10 but whent there's only few text to be placed then use font size 11"; then "but standard size yet 10 right?" (yes).
- **Changed:** the house text size is one per video: 10, or 11 when at no moment more than 5 words are on screen (every text shown at that
  moment counted, so a caption split into two layers counts whole) and, at 11, every line stays within 82% of the frame width
  (`config.json → capcut.text_style.short_text`; null turns it off). `capcut-text-style`, run by `capcut-repair`, counts the words on the
  timeline, measures each line with CapCut's System font and reports both as `sizing`. CapCut draws size s with a font of about 0.00575·s of the
  frame width, measured on the covers CapCut itself rendered of `03_Oct_2026_v09` (size 10) and `06_Oct_2026_v14` (size 9). Agents still pass
  `fontSize:10`. In step: capcut-assembly §3, §4, §5; text-and-format §3 step 5; production-agents §2 (the contract); awl-plan-video;
  awl-postprocess; preprocessing; README; the build prompt.
- **On the store (read only):** 13 of the 229 projects would get 11 ("Hero vs villain", "Who decided that?", the day labels under "life as
  student", "first day as an assassin"); `20_Oct_2026_v03` (two layers shown together, 10 words) and `28_Oct_2026_v10` ("POV: YOU WORK IN
  SALES", 84% of the width at 11) stay at 10. No project was rewritten: a project takes the rule at its next repair.
- **Verified:** t02 adds 8 checks (sizes, the split caption, the too-wide line, the pair, the write, the off switch, the contract); t01, t02,
  t03, t05 pass; `docs_tool.py check` 0 errors.

## 2026-10-29 · A Loupe prompt box holds only the generations its frames come from; every join is recorded
- **Reported:** Fill on a report of run `20261028-202809-recreate-neurogum-celsius` video 02 warned "They differ (inserts between the clips, or another
  cut)": its clean video is c1 0-1.9 s, c2 1.9-3.4 s, c1 again to 5.867 s, read as c1 0-5 s and c2 5-7 s. Then: "if two or more samples are from one video
  generation only make sure to only include that generation prompts in the prompt filler not more, but if the frames used as wrong,right or examples are
  from more than a single generation ... then in the prompt fill of flawed versions include the video prompts of the generations whom's frames turned out
  wrong ..., and in the right/correct prompt filler box put the prompts that generated the correct version ..., but if there's only 3 right frames or 3
  wrong frames, or 3 examples then only fill in one prompt ... make sure that thats how they get read from judges and keepers ... nothing should be left out
  of sync or unchecked and in accordance with both analyze-with-loupe command and loupe app too! and then in the end update cases in loupe generation misses
  that all frames have the same type of sample"; "make sure that video generation prompts from the samples are not trimmed in any way"; "also make sure to
  avoid memory contex rot to agents whatever function they do but video prompts should not be trimmed no matter what".
- **Root cause:** joins were not recorded (`concat` deleted its list; hand-made ffmpeg lists were the only trace), so Loupe assumed clip order and each
  clip's full length, and took a clip's attempt from the number of attempts made (a clip that shipped its first attempt after a failed second got the
  second's prompt); a box held every generation of a take, or the whole take when no frame of its kind existed.
- **Changed:** `concat` writes `<out>.join.json` (each piece's clip, attempt and seconds; the output's sha1; a piece that is a join keeps its generations,
  an insert is a piece of no clip); `restore-audio`, `conform`, `clean`, `captions` and `trim` carry it (trim shifted). Loupe reads the join (that record,
  the CapCut project of a render, the list of the attempt folder a copy came from, a render of the clean video, the clips' pieces, their trimmed files;
  never assumed) and gives each box only the generations its frames come from, every sample of the report counted, a box no frame feeds empty, each prompt
  under the line that says what it is. The qc-consult and plan-hints rules share `LOUPE_PROMPTS_WORDS`; `sample-prompts` heads a sample by its boxes and
  each generation by every span. Docs: awl-postprocess (every join through `T concat`), seam discipline, deliverables, preprocessing, README, awl-qc,
  awl-precheck, the tests README, the build prompt.
- **Verified:** t02 adds 4 join-record checks, t03 checks the prompts file by role; t01, t02, t03, t05 pass; Loupe's selftest 225, keeper_sync 92,
  page_smoke, transport_check, flags_smoke pass.

## 2026-10-30 · One set of names for a sample's prompts, in Loupe and here; a keeper told a new header starts fresh
- **Reported:** after the box rule of 2026-10-29 the judge's ASK rule in Loupe still asked for "the prompts of its two takes". The user: "but did we
  not get told to not tell you to not let nothing out of sync ... yes do it right now, and also check for other outdated and similar in sync issues
  between the two".
- **Root cause:** the box rule named the boxes by what they hold (the flawed version's prompt, the correct version's, an example prompt), but the words
  of before (the two takes, both prompts, the correct take, Video A's prompt for the frames called Wrong and Video B's for those called Right) stayed in
  Loupe's role and record kinds, the collector's role, the form's placeholders and labels, the chips, comments and docstrings, both READMEs, both build
  prompts and three of this toolkit's texts, and no test looked for them. Loupe's library header reaches a keeper session only when it boots, so a
  change to it never reached a running session.
- **Changed:** here, `prompt-template`'s docstring and `prompts_rule`, the prompts files' writer, the README, the command's rule 23 and awl-free-plan
  name the prompts as Loupe does; the qc-consult and plan-hints rules also say how to read a sample with one box (what that prompt secured, or let
  happen, at the frames it made) and an example prompt (what it suggests). In Loupe every such text, comment and docstring was renamed (A MISS WITH ITS
  CORRECT VERSION; `box_words`, `EXAMPLE_PROMPT`; `_with_frames` lost its unused `every`), the keeper's state keeps the header it was told
  (`HEADER_SIG`) and a session told another one is booted fresh, and its selftest and page_smoke fail on any old word. "Flawed take" stays in
  awl-inputs and awl-write-request, where it means a clip QC rejected. The entries of 2026-10-20 and 2026-10-28 keep the words of their day.
- **Audit (read-only, the same day), each finding checked against the code:** the judge read the prompts of only three cited samples while
  every text said every one (now up to six, `prompts_judged` complete, `prompts_unread` named, the rules say which); `qc-brief` overwrote the
  video's `qc-consult.json` and claimed a keeper had read its prompts (now `qc-brief.json`, no prompts files, honest wording, also for a busy or
  fallback consult); the collector's reading was described as a verdict; the README and the start and free-plan skills still put the judge at X2
  hints; `prompt_sides` and the brief's fields were missing from the answers; a caught flag's diff was cut at 300 characters and 14 lines; the
  README described the prompts file's old headings; Loupe's key table did not name this toolkit; a build-prompt paragraph was split by an
  inserted passage.
- **Limits raised (the admin, the same day):** "make it up to 10 instead of 6, and raise 150second judge call timeout to 240, and raise the 150k
  characters to 250k". Loupe: the judge reads the saved prompts of up to ten samples (a template request's read and an answer's final prompts
  round), a keeper call may run 240 s, a keeper session is replaced after 250 000 characters (Loupe's own point for a fresh session, not a limit
  of Claude Code). Here: `AWL_CONSULT_TIMEOUT` 1620 s (120 s of lock wait, six keeper calls of 240 s, 60 s of margin); t03 checks the wait
  against Loupe's `KEEPER_CALL_TIMEOUT`.
- **Verified:** t01 (91), t02 (134), t03 (53), t05 (73) pass; `docs_tool.py check` 0 errors; Loupe's selftest 230, keeper_sync 94, page_smoke,
  transport_check, flags_smoke pass; after the restart Loupe's live check passes.

## 2026-10-30 · The judge decides the product images; every input names the client's original file

- **Reported:** the admin, on a sample whose product band showed prepared names (`Image 2 · = image2-product-…-front-padded`) and no count:
  "actually the names are far better to be told as they were in their original files ... so the upcoming runs know which assets samples to use or
  how much of them, also the judge should be able to tell and decide to how many asset sample references should be used in the generation based on
  what it thinks the best use is ... (i am talking only for the product ...)"; then "no need to say the exact folder ..., just the exact file/image
  name", and "use as many resources and test as much as we need, just don't let anything out of sync".
- **Root cause:** a request recorded where an input came from only as free text, in forms the agents made up (a `build` note, `from`, `source_file`
  or a plain `source` path with `prepare`, words in `meaning`; the live run alone used five), and the product images sat anywhere among the image
  inputs, so neither Loupe nor the judge could tell which client file an image was, and nothing let the judge choose them. At QC the judge saw only a
  count of the inputs (`image_references×3`).
- **Changed:** X2 records `params.medias[].source` {`original`, `asset_id`, `prepared`, `kind`} for every input prepared from a client file and puts
  the product images last (awl-write-request); `prompt-template` hands the judge each input with its asset id and original file name and the client's
  images of that product (registry row and inventory); the judge answers `product_images`; `template-apply` applies them at X4b (`musts_renumbered`,
  `musts_superseded`, `product_images_problems`, `prompt_names_images_beyond_the_inputs`); `product-images --apply` takes a QC answer's for a
  regeneration (only added after the last image or the last ones left out, never both; a request the ledger holds is refused; the request kept once as
  `.pre-product-images.json`); `qc-consult` sends the request's inputs (`request_inputs`); X3 prepares and uploads an image the judge added (its
  placeholder `value`, `<X3: prepare <file> for Image N>`); `lint-run` lists inputs without a recorded source and requests whose product images are
  not last; `result.json → judge.product_images`; the production agent's spawn text and contract item 23 say it. Older requests are read exactly as
  Loupe reads them (`_pi_source` = `runs._source_of`; two ids named is no record, never a guess). In Loupe: the band says how many product images
  and shows each whole name, `Image 2 · A82 · <original file name>`; the records' PRODUCT IMAGES section; the role's PRODUCT IMAGES paragraph (a
  regeneration: never both at once, never another file in an image's place); `request_inputs` in the QC question; the ten existing samples with
  product images rebuilt (backup `~/.claude/backups/loupe-20261030-063326-before-product-names`).
- **Found on the way:** comments that quoted the client's folder and file names (Loupe allows no product names in code: neutral stand-ins now); the
  judge's product list was cut to six before malformed entries were dropped; the automatic pick lost its input number; the sample meta cache was keyed
  by time alone; old prompt words in Loupe's own test headers and one fixture.
- **Verified:** t01 (92), t02 (145), t03 (61), t05 (73) pass; `docs_tool.py check` 0 errors; Loupe's selftest 243, keeper_sync 98, page_smoke,
  transport_check, flags_smoke pass; on the real runs (read-only) Loupe and the toolkit read every image input alike (0 disagreements; the live run
  resolves 49 of its 58 product images, the rest name no file or two).
- **The same day, later (the admin):** "make it so that the product samples that alredy been used in that generation will automatically be included, but only the verified assets that were directly used to higgsfield for that specific generation ... even if they characters or other attachment check them by default, just don't show client's original or as the upload records ... if it isnt directly used as a reference in that video generation ... then don't show it, and then if i want to exclude some or add more i'll do it myself". Loupe's picker now offers only the images sent with the take's generation, verified from the run's records, every one ticked (Loupe's change). Here the registry's product rows are read in either form runs write (an id starting with P-, or a type cell that says product: run 20261028-202809 wrote `| NG-EF6-SPE | product | … |`), as Loupe reads them (`_pi_registry_rows` = `runs._registry_product_rows`, a t03 parity check), and an input whose label or file name carries a product row's id counts as a product view (`_pi_names_product`, also in the judge's inputs text).
- **The same day, later still (the admin):** "also update the generation miss samples on Loupe, let them all have their verified used video generation
  assets/resources to be in saved moments", then "i only meant for moments we already saved" and "make sure everything is in sync between command
  pipeline and loupe, we're not in rush". Loupe now reads every form older runs recorded what a generation was sent in (uploads in `state.json` under
  `file`, `local` or `path`; a plain asset-id map giving the run's one copy of that asset, never a look preview; a request's `media_files` and
  `media_map`; a guide only the request's own words name), reads a take from its file (letter clips, `delivered_attempt`; an attempt it cannot tell
  gives nothing) and shows one tile per picture, named with every clip that sent it; every saved sample was rebuilt with what its generation was
  sent (Loupe 31129bc and the library rebuild). The toolkit: `PI_PRODUCT_NAME` takes Loupe's widened `runs.PRODUCT_FILE` pattern (the word also
  before a folder separator, a colon or a number, never inside another word), a t03 parity check beside the registry-row and source checks.
- **Read alike on the real runs:** of 573 image inputs both read (every submitted request of every run), Loupe and the toolkit name the same
  source for all; Loupe had called 4 inputs in pass folders (`a3/p1/`) product images by the folder's name, fixed so a code is read only in an
  input's own names, as the toolkit reads it. The 36 left differ only where Loupe reads an older run's `state.json` product registry or uploads
  record, forms the current pipeline no longer writes and the toolkit never reads again (its runs are finished).
- **Verified:** t01 (92), t02 (146), t03 (63), t05 (73) pass; `docs_tool.py check` 0 errors; Loupe's selftest 255, keeper_sync 100, page_smoke,
  transport_check, flags_smoke pass; every image of the 19 saved samples is the file Higgsfield stored under its media id (size and MD5 from a
  header request, 63 of 63), and each of the 23 jobs lists exactly those media ids as its image inputs (its job record, 23 of 23).

## 2026-11-02 · A Loupe sample's marks on its zoom only; every saved sample rebuilt; the two kept in step

- **Reported (the admin):** "in our loupe app when we mark generation misses samples, can we make the up frames to not have the circle,box,arrow
  just the bottom ones", then "also update the already generated samples moments and frames in the loupe app to mirror the changes,do a backup too,
  and then push both repos claude-config and loupe, make sure we have both analyze-with-loupe and loupe app in sync, no rush we can take all the time
  and resources".
- **Changed in Loupe (5712e1b, b33b280 and the sync commit after them):** in a sample's image a frame that has a zoom (under its row, or its close
  range beside it when it sits alone in its row) is shown clean and its marks are drawn on the zoom only; a frame without a zoom (a text label alone,
  marks over most of it, the zoom switched off) keeps its marks; `frame-N-marked.png` keeps each frame whole with its marks in place. The library
  header, the record's IMAGE line and the data collector's role say so: the judge started a fresh session and every picture was collected again (21
  of 21, `COLLECTOR_VERSION` collector-2026-11-02). Every saved sample was rebuilt: 21 samples, 44 frames, 27 now clean above their zoom, 2 without a
  zoom keeping their marks (S10), 15 never marked; outside the cleaned panels every image is pixel-identical to before, and no meta.json, frame file
  or zoom file changed. Backups: `~/.claude/backups/loupe-20261102-220339-before-marks-on-zoom-only` and
  `~/.claude/backups/loupe-20261102-221522-library-after-rebuild-before-awl-sync`. The unregistered MCP server's `qc_get_sample` description still
  said the first two-panel layout (the miss with marks on the left, the correct frame on the right); it now says the frames and the zoom.
- **Changed here:** awl-qc's "Samples first" paragraph says the zoom alone carries a frame's marks with the frame above it left clean, a frame
  without a zoom keeps its marks, and `frame-N-marked.png` beside `composite_path` is each frame whole with its marks in place (for where a zoom sits
  in its frame); the README's Generation misses paragraph says the same; t01 guards the wording. `qc-consult`, `qc-brief`, `prompt-template` and
  `sample-prompts` are unchanged: they carry `composite_path` as before. The run folders keep what their agents were given (their
  `S<id>-prompts.md` are text and point at Loupe's live images).
- **Found on the way:** Loupe's live keeper checks (`selftest.py --keeper`) had failed since 2026-10-22, the code from before this change alike: the
  fake-keeper sections above them booted sessions only the fake knew, and the real session then resumed one ("No conversation found with session
  ID"); the live section now starts from a reset keeper.
- **Verified:** t01 (93), t02 (146), t03 (63), t05 (73) pass, and t04 (10) with the live keeper (one real qc-consult, one real plan-hints); the
  rehearsal 221/221 steps, no contract failure; `docs_tool.py check` 0 errors; Loupe's selftest 256 (261 with `--keeper`, the real session's checks
  passing again), keeper_sync 105 and `--live` 13 (the keeper IN SYNC with the 21 samples), page_smoke, transport_check, flags_smoke pass.

## 2026-11-02 · A keeper whose saved conversation is gone starts a fresh session by itself

- **Reported (the admin):** "yes fix the gap", to: if the keeper's saved conversation is ever lost, Loupe keeps failing until the keeper is reset
  on the Keeper page.
- **Root cause:** Loupe keeps the keeper's session id and resumes it (`claude --resume`). When the CLI no longer has that conversation (its
  transcript removed or cleaned up) it answers "No conversation found with session ID", the call failed and the stored id stayed, so every later
  consult answered from the brief (`mode: fallback`; `unavailable` for plan-hints and prompt-template) until the admin pressed Reset. The same
  failure kept Loupe's live keeper tests red from 2026-10-22 until earlier today.
- **Changed in Loupe:** that answer on a resume is `SessionLost`; a consult then boots a fresh session told the whole library and asks the same
  question there (without the delta), a sync boots in place of the delta it could not send; the answer carries `keeper_restarted` (words naming
  the lost session) and the audit log `keeper.session_lost`; a session the call has just started is never booted again (no loop).
- **Changed here:** `plan-hints` and `prompt-template` pass `keeper_restarted` on (`qc-consult` and `loupe ensure` print Loupe's whole answer);
  the README says so; t03 checks the three through the toolkit.
- **Verified:** t01 (93), t02 (146), t03 (64), t05 (73) pass, and t03 against the toolkit of before fails for plan-hints and prompt-template
  only; the rehearsal 221/221 steps, no contract failure; `docs_tool.py check` 0 errors; Loupe's keeper_sync 112, selftest 256 and 262 with
  `--keeper` (a real claude session given an id it never saved is replaced and answers the same question), page_smoke, transport_check,
  flags_smoke pass; the live Loupe restarted on the new code, the keeper in sync with the 21 samples.
- **Every sample of the library in each template, the judgement kept per video (the admin, 2026-11-03):** asked whether the judge reads its ten
  prompts in a separate session, then: "along with the full 10 prompts that agent has to have context of what were previous missings even though it may not read the full prompts of them but it should be able to avoid them by the understanding it has for them", "fix gaps" and "don't make it say them in the chat window though because it will pollute it ... let it do a .md file that will be saved for each video". It
  was already the same session (step 2 of a template request resumes the session that holds every sample's record). Now the role asks for it
  outright: in step 2 the judge goes through every sample, read or not and whatever the product, designs out every miss that could happen in this
  video through the same mechanism, and answers `avoided` and `set_aside` beside `basis` (Loupe keeps `basis` up to ten now; it had stayed at eight).
  `prompt-template` writes the whole judgement to `40-briefs/video-NN[-cK]-judgement.md` and prints only `judged` and the file; `awl-precheck` X4b
  tells the agent never to paste it into the chat. Caught on the way: a fix script that saved through Python's text mode wrote awl.py and
  t03_loupe.py with CRLF endings (as the 3c33e1b auto-commit had); put back to LF before any commit.
- **Verified:** t01 (93), t02 (146), t03 (66), t05 (73) pass; `docs_tool.py check` 0 errors; Loupe's selftest 260, keeper_sync 112, page_smoke,
  transport_check, flags_smoke pass.
- **The live check (2026-11-03):** given the real brief of run 20261102-233733-02 video 15 c1 under the test name sync-check-20261103, the real
  judge judged all 19 samples in 164 s (7 read and used, 4 designed out from their records, 8 set aside, none unjudged) with a 4927-character
  prompt; the misses it designed out came from other products by mechanism (a pasted look, a distant product looking fake, the product's size
  changing, something passing through the carton). It wrote each designed-out entry as one note (the miss, then 'Designed out by: ...'), so an
  avoided entry is now `mechanism` (the miss and what this video shares with it) and `where` (the part of the prompt that designs it out), an
  older answer's `why` read as its mechanism; and the judgement file names the draft's product images when the judge keeps them.

## 2026-11-03 · One file, one fingerprint, in every run

- **Reported (the admin):** "we have to add a little bit more context or whatever it may be for the qc keeper judge to have more accurate and less ambigous verdicts", after the live check's judge flagged one photo, IMG_6917.jpg, as A274 in one run and A273 in another,
  and S44's product field "Celsius products" beside a Neuro carton.
- **Root cause:** an asset id is the run's own number; the judge saw only ids and file names, so a sample's id from another run could name another
  file of this run, and `_product_plan` took the id's file without a word. S44's product field was Loupe's pre-fill (the first heading of the
  run's registry), never typed by the admin.
- **Changed in Loupe:** `runs.file_fingerprint` (sha1[:8] of the content); each sample's `meta.json` keeps the original's and the file sent's;
  the records, the fetches and the answers name each image `<name> #3f9a1c2b` (the file sent's where the original's cannot be had, never in its
  place); `LIB_HEADER` and the role say an asset id is the run's own number and ask for the `fingerprint` of each product image (the header
  changed, so the keeper starts fresh). A new report's product field is no longer pre-filled from a registry heading.
- **Changed here:** `_pi_fingerprint` (the same as Loupe's); the inputs, the product images and the client's images in what the judge reads carry
  it; `_product_plan` applies the file a fingerprint names (noted in `product_images_notes`) and makes an id and a file name that name two files
  of this run a problem when there is no fingerprint; the judgement file shows it. The field is `fingerprint`, never `mark`, which the judge
  already uses for the admin's drawings.
- **Verified:** t01 (93), t02 (146), t03 (69), t05 (73) pass; `docs_tool.py check` 0 errors; Loupe's selftest 264, keeper_sync 112,
  page_smoke, transport_check, flags_smoke pass.
- **The live check (2026-11-03):** the morning's real brief again (run 20261102-233733-02 video 15 c1, under the test name sync-check-20261103):
  the judge judged all 19 samples in 118 s (7 read and used, 6 designed out, 6 set aside, none unjudged; a 4940-character prompt), tied S44's
  and S46's photo to this run's by its fingerprint ('IMG_6917 #846e6464': A273 in their run, A274 here, where A273 is IMG_6916.jpg) and kept
  the draft's product images; the morning's flags on the two ids and on S44's product field are gone. `_product_plan` on that draft turns
  'A273 IMG_6917.jpg #846e6464' into A274 (noted); the same without a fingerprint is a problem, nothing applied.

## 2026-11-03 · Create: clean source takes, the whole edit in CapCut; no sticker or emoji, ever

- **Reported (the user):** their rules for Create ("Generate clean source shots first, then assemble and finish the video through CapCut MCP"; clean means free of baked-in editorial additions, never a limit on the
  genre, the art style or the imagination), "without losing anything that's in our current pipeline"; then, asked about one
  generation per shot: "we can do only 2 of 15seconds video generations and then split them across, insert, do cuts or whatever it takes to achieve similar video styles and edits like the references had, and do the editing with the capcut, no need to do 5 video generations of 6 seconds" (and later: "i just took two generations per 30seconds video as an example because for example wan 3.0 prime only allows max 15s per generation not that i want to split the video into multiple generations, if 30s could've been done in one shot then why not, we could've just edited it after the generation and do splits,cuts,vfx,insertions or whatever it takes"); then "capcut may be updated and commands change so they should also try to figure out themself too"; then "never use or apply stickers, ever, neither in the video generation nor in the edit", and "when i said stickers i meant stickers and emojis both, never use them ever, neither in video generation nor edits".
- **What was there:** the clean plate held for text only (text-and-format §1: overlay text as CapCut layers); a generation could
  hold several shots joined by hard cuts; the CapCut project was one joined clean video plus inserts, text and the reference's own
  transitions; the CapCut tools were a fixed list.
- **Changed:** contract item 35 (Create and Free `create`; Recreate and Edit Mode unchanged), owned by `awl-create-plan` and
  `awl-plan-video`, carried by `awl-analyze-study` (the cards' edit layer apart from the scene layer), `awl-free-plan`,
  `awl-write-request` (one continuous shot in the model's single-take phrasing, a must-carry line, never a word of the edit),
  `awl-precheck`, `awl-postprocess` (the whole edit from the takes, capcut-assembly §3c, new), `awl-qc` (`capcut detect-scenes`;
  the project against the edit plan), `awl-record` (the takes as the clean originals) and the production agents' contract. The
  takes are as few as the locked model's longest duration allows (one when the length fits it; the
  user's two 15 s takes were an example of a 15 s maximum), never one per shot. The
  agents find the CapCut tools live (`ToolSearch +capcut`, the catalog tools, `capcut --help`); the named tools are suggestions;
  the router allows keyframes, masks, filters, transitions and their catalogs and segment delete, never the caption, transcript
  or raw-patch tools. No sticker or emoji, ever: item 6, every mode, in a generation and in the edit (a graphic or a text layer);
  the sticker tool neither allowed nor named. Text and symbols that belong to
  the depicted world may appear, of whatever kind fits it; the clean-plate line forbids overlay text only. The skills' Read-now sizes follow the refreshed index tables.
- **Then (the user):** "do not make this too constrained ... everything that fits and is part of the video generation let it be without forcing or only allowing books": the in-world text had read as a closed list (signs, books, shirt prints, only when planned, "no other
  lettering is"); it is open now: any text or symbol that belongs to the depicted world and fits it, the plan naming only what the
  story depends on, QC accepting the rest when it reads as part of the world.
- **Verified:** t01 (98, five new: item 35 in the router, its owners and the agents' contract; the whole item in its two owners; the CapCut section, the cards' edit layer, the take check and the clean originals; the live tool discovery and the router's tools; no sticker or emoji), t02 (146), t03 (69), t05 (73) pass; `docs_tool.py check` 0 errors.

## 2026-11-03 · Item 35 refined with the user: the agents decide within the limits; less to load

- **Reported (the user):** answers to a list of wordings tighter than meant: cut times set after the generation; what a take shows is the
  agents' decision; as few generations as the video needs ("make it smart and dynamic"; a new place is a reason for another); real camera
  work filmed when it serves the realism ("make it smartly decide"); only effects pasted on top flagged; the take keeps its light and
  colours; only buttons, frames and labels added on top banned ("smartly decided"); no change to when a flaw is regenerated; text space only
  where text goes; "only no added ones" for stickers and emojis (a chat's emojis on a phone are natural); the edit layer as "a middle
  ground"; then "we should aim to avoid memory context rot in our ai agents and pipeline as a whole and keep the current structure, only
  call and what access to what needed".
- **Changed:** item 35's whole text in `awl-plan-video`; `awl-create-plan` carries what A6 acts on and points there (16.1 → 11.2 KB); the
  router's item 35 back to one short line (1926 → 831 characters); `awl-write-request`, `awl-precheck`, `awl-qc` (the take and project
  checks), `awl-postprocess` (cuts timed on the takes), `awl-analyze-study` and the card (a pattern with its key moments); capcut-assembly
  §1 (the usual tools by name, a narrow search only for an operation they lack, the catalogs only when needed), §3c, §5; text-and-format §1
  (item 6: no sticker or emoji added); generation-system §3b.1.
- **Verified:** t01 98 pass (the whole item 35 in awl-plan-video and the A6 part in awl-create-plan; the narrow CapCut tool search; no sticker or emoji added); t02 146, t03 69, t05 73 unchanged since the code did not change; `docs_tool.py check` 0 errors.

## 2026-11-03 · Request files named with the attempt last are read like the usual form

- **Reported (the user):** report 36 (run 20261102-233733-02, video 06): "it is the a2 generation that doesnt have any in its assets slot"; then
  "yes fix it".
- **Cause:** the run wrote the take's request as `video-06-request-a2.json`; Loupe and the toolkit only knew `video-06-a2-request.json`, so
  the take had no request (no sent images, no prompt). Nine such files across two runs.
- **Changed:** Loupe `runs.request_canon` and `request_files_named`, used by every request-name parser; `awl.py` `_cf_req_canon` and
  `_cf_requests_named` in the caught-flag and QC prompt lookups, `status` and `lint-run`; the files keep their names. Loupe selftest and t03
  check both forms.
- **Verified:** Tests: Loupe selftest 265 (both name forms, a kept copy left out), transport_check and page_smoke all passed; /analyze-with-loupe t01 98, t02 146, t03 70 (the toolkit reads both forms as Loupe does), t05 73.

## 2026-11-03 · The audit with Loupe: a clip's first take, uploads recorded in full, a regeneration's request name

- **Asked (the user):** "take our time we are not in rush make sure everything works correctly or we didnt let anything aside,also make sure to
  not let anything out of sync between loupe and analyze with loupe command".
- **Found:** the caught-flag and QC lookups handed a clip's first take (`--attempt c2-a1`) the video's newest request, where Loupe reads
  `video-NN-c2-request.json`; 54 uploads entries in four runs named their file relative to the pipeline's home (`runs/<run>/...`), which Loupe
  read inside the run and missed (those takes offered no image); awl-write-request named no regeneration's request, so runs wrote
  `video-NN-request-aK.json`.
- **Changed:** `_cf_req_tag` (the same rule as Loupe's `runs._request_tag`) in `_cf_request_file` and `_video_request_prompt`; `uploads set`
  records the file in full; awl-write-request names `video-NN-aK-request.json` and `video-NN-cK-aK-request.json`. In Loupe: `runs.run_file` for
  every recorded file it reads; `sample_origin` hands the judge the sample's own product images (each video's); a new report's product field takes
  Video A's product words.
- **Verified:** t01 98, t02 147 (uploads set records a file in full), t03 71 (a clip's first take reads its own request; the toolkit reads every request name's generation as Loupe does), t05 73, docs_tool check 0 errors; Loupe: selftest 272 (a file an uploads record names from the pipeline's home found in the run; sample_origin hands the judge both videos' product images), keeper_sync 112, page_smoke 72 (a new report's product field takes Video A's product words), transport_check.

## 2026-11-05 · Static: a fourth Analyze sub-mode, narrated still images instead of video generations (item 36)

- **Asked (the user):** "lets add another option on analyze -> static, ideally it will have everything that recreate have but instead of
  doing video generations it will do image generations"; "no higgsfield at all called in this mode strictly, i will give my api keys for the
  direct api image generations, and as for the qwen voice model it is in a different pc"; "also try to avoid memory context rot and keep the
  pipeline already established structure and calls logic"; "btw for the background music (if needed) the agent will use ace-step 1.5".
- **Decided with the user:** Loupe is left out of Static (its code unchanged); three voice samples, the user picks one, and it is reused for
  every video of the run; the OpenAI key lives only in the environment variable `OPENAI_API_KEY`, never printed and never written to a run.
- **Changed:** the router's item 36 (with its owners), items 14, 15, 17, 24 and 27, the phase rows, the labels A6s and S2–S4, and no Loupe
  at resume. Four skills: `awl-static-plan` (A6s: the characters, a pool of subjects with sources for facts, three voice samples, one stop,
  the scripts and image plans), `awl-static-sound` (S2: the narration, its words and cues, a music bed only when the spec calls for one),
  `awl-static-images` (S3: the API, or the prompts file and the folder intake) and `awl-static-edit` (S4: the timeline, the local render, the
  CapCut project). Static lines in awl-start, awl-analyze-prepare, awl-analyze-study, awl-analyze-produce (A9s), awl-record and
  awl-wrapup; `reference/static.md` (nine sections) and production-agents §2s, the Static contract `T contract` writes when
  `analyze_submode=static`. The toolkit: `prep-video` and `prep-all --no-extras` (exactly 1 fps), `audio-profile --voice`, `static check`,
  `image generate|prompts|intake|use` (the OpenAI Images API by urllib, a ledger row of kind image per call, a refusal never resent
  unchanged, 429 and 5xx sent again twice at most, a timeout recorded as unknown), `tts check|design|voice|say` (`scripts/tts_worker.py`
  in the Qwen3-TTS interpreter, `AWL_TTS_PYTHON`), `music check|make` (`scripts/music_worker.py`, ACE-Step 1.5, `AWL_MUSIC_PYTHON`,
  `AWL_MUSIC_ROOT`), `narration-words`, `slideshow plan|render` (ffmpeg: zoompan, xfade, ducking, −14 LUFS); one GPU lock for the two
  workers; `config.json → static`. While there: the production notes and item 27 name Recreate, Create, Free and Static.
- **Verified:** docs_tool check 0 errors (36 docs, 24 skills); t01 108, t02 169 (exactly 1 fps; the image API against a local mock: an image,
  a refusal, the key never printed or written, the ledger rows; prompts and intake copy, never move; tts and music with stubs;
  narration-words with the transcribe stub; slideshow plan and render; static check with and without the key; the Static contract and its
  lint), t03 71, t05 73; a scratch run end to end with the stubs (a 12 s video at 720×1280, −13.9 LUFS, captions burned). Not run on this
  PC: Qwen3-TTS and ACE-Step themselves (they live on the Static PC, where `T static check` reports them).

## 2026-11-05 · Recreate: the whole source in one generation when it fits the model's live maximum

- **Asked (the user):** "if the model's max video generation is 15s ... and then one of our videos we're processing is 14s or 15s then no
  need to do two seperate generations for a single video, rather send the whole video at once, only do it if necessary, such as changing
  ambient and sorroundings or other specific cases, and if the videos length is > than the generation model's max length then do 2,3... or
  more generations based on the data"; then "no do it after we call the higgsfield's mcp and it returns the models and their input and
  output lengths, do not do it hardcoded, because models change often"; then "if the video generating model maximum output is 15seconds and our video reference is 15s no need to split it into two 7.5 + 7.5s (or similar) rather send one 15second video generation sample and expect a 16s output, or if the generation model max video output length is 30seconds and the video is 27seconds we send it all at once, but for example if that 27seconds has a different scene or sorroundings change and we decide that it would've been better to split it into 15+12 seconds then we can do it but otherwise send it 27seconds at once".
- **Changed:** generation-system §3b.1 item 7: in Recreate (and a Free `recreate` video) a source within the maximum goes whole, in one
  generation with its cuts; at most 0.4 s over the maximum, only its first <maximum> seconds are sent (one generation, the audio cut
  with a short fade-out; `T trim --end`, `restore-audio --duration`); it is split under the maximum only for a new place or ambience or
  a case one generation already failed; a longer source takes its length divided by the maximum, rounded up, split on its own cuts;
  Edit Mode keeps the earlier rule. The user's examples are in item 7: 15 s on a 15 s maximum is never 7.5 + 7.5 s, a take back at
  16 s is trimmed to the source, 27 s on a 30 s maximum goes at once, 15 + 12 s only for a change of scene or surroundings, and a
  "works best" note (Seedance 2.5's "≤20 s best") never lowers the maximum. The maximum
  is the live one: E4 (at A6r, before the source is prepared) and A8 record the `models_explore get` answer as `state.json → model_limits`
  (the `duration` range and any video-reference limit; a limit the live answer lacks comes from the guide §2.2 and says so);
  awl-plan-video and awl-recreate-plan read it; a run made before it and resumed (run 20261104-225639-04 among them) records it at
  A9's start, before any video is planned. No number is kept in the models' index.
- **Found:** the user's strict rule of the same morning, kept as a memory of run 20261104-225639-04 and not yet in the library ("videos
  15s and under never do two generations but rather direct one, even if its 15.2s or 15.4s just send the 15s, but if its over that than
  we can do a smart 2+ generations"; there video-30, one unbroken 15.0 s take, was split in two and the can jumped at the seam): the
  first wording of item 7 would have split a 15.2 s source in two, so the 0.4 s margin was added. The live answer gives the output's range (Seedance 2.5 4–30 s, Wan 3.0 Prime 2–30 s on 2026-11-05) but not the longest video
  reference, so that one number still comes from the model's guide, labelled `guide §2.2`.
- **Verified:** t01 (the rule's words in §3b.1 and both skills; the limits recorded at E4 and refreshed at A8; the 0.4 s margin in
  item 7, A6r, E5 and X1; the record at A9's start for a resumed run), docs_tool check 0 errors.

## 2026-11-05 · Static: the format the user picks (the CapCut export is the final) and strong lines by the voice-design model

- **Asked (the user):** "export it as the final, but the images used quality depends on the users pick, make sure to suggest the most
  correct size first along with options"; "let me ask about the quality but make sure to recommend whats the most optimal for our video
  reference such as 16:9 720p or 1080p or whatever is the right version and also other options i could choose too"; "make strong lines with
  the voice-design model instead, though the voice may shift slightly from line to line, but make sure to use it optimally and not make big
  strong emotion changes unexpectedly, but yeah make room for it".
- **Changed:** A5 asks the format with the count (header Format, static §2). `T static formats` gives the facts: the references' sizes and
  aspects, and per aspect and resolution the export, the image size with the move margin, the one without, the check size, and whether the
  image API takes each (OpenAI's documented size rules, `config.json → static.images.limits`). The best fit comes first, marked
  Recommended (the references' main aspect at 1080, quality high); `T static format` stores `state.json → static.format` and refuses a size
  the API does not take. `image generate` and `image prompts` take the run's size and quality; `image intake` measures each image against
  the run's aspect (`off_aspect`); the check render takes the format's check size; `capcut-prep --canvas` sets the project's canvas;
  awl-static-edit, awl-record and awl-wrapup say the CapCut export at the format's size is the final (no tool exports a CapCut project, so
  the user does). Strong lines: a narration line with `strong` and `delivery` is made by the VoiceDesign model from the run's voice
  description plus that delivery, with the picked sample's seed (`tts design` gives each sample a seed, `tts voice` keeps it, the worker
  seeds every random source). The sidecar measures every line's pitch (semitones from the run's voice) and timbre similarity (MFCC
  cosine), and `voice_match` gives the cloned lines' spread. Static §4 keeps strong lines to the references' peaks (at most one in five,
  never two in a row, led in and out); one apart from the cloned lines is made again with another seed, at most twice, then cloned.
- **Found:** at 1080 on the short side, a 1088×1920 image is upscaled about 11 % at the end of a 12 % zoom, so the recommended 9:16 size
  is 1216×2160 (each edge times 1.12, up to a multiple of 16; inside the API's standard range, not "experimental"). A 720×720 square is
  under the API's minimum pixels (refused; its margin size 816×816 is fine).
- **Verified:** docs_tool check 0 errors; t01 113; t02 177 (the formats facts from an inventory, a refused size, the stored pick, the
  image calls sending its size and quality, the prompts file's "vertical 9:16, 1216x2160", intake's `off_aspect`, the timeline's check
  and export sizes, a 16:9 check render at 1280×720, `capcut-prep --canvas 1920x1080` labelled 16:9, a strong line made by the design
  model with seed 1107 and every line's pitch and timbre); t03 71, t05 73; rehearsal 221/221.

## 2026-11-05 · Static: the text look is the references' own (no house size or preset)

- **Asked (the user):** "the agents are free to chose any font preset,size,color and family or whatever they like while editing the video and are not constrained like we do with recreate for example where the font size is 10,11 and the preset is set also, the thing is that everything is data driven (from the references) and nothing is predefined".
- **Changed:** static §1 reads every text's look on the frames; §2's **Text look** replaces the caption pattern (the font family seen, or
  the closest from `T capcut-font --list`, CapCut's own first; the weight; the size in CapCut's units; the fill; the outline; the
  shadow; the box; the case; the words; the lines; the position; the highlight; the animation); §5's plan carries it per video in
  `captions`; §7 applies it in CapCut with `capcut import-srt`'s flags, `T capcut-font` for the family, `capcut text-anim` and
  `capcut add-text`, then `T capcut-repair --keep-text`; §8 checks it by reading the timeline back. awl-static-edit and awl-static-plan
  follow; the router's item 6 notes the Static exception and item 36 the look. Toolkit: `capcut-font --list` (the fonts on this PC as
  facts: CapCut's bundled ones, its downloads, Windows', the user's) and `capcut-font --draft --font-file [--track]` (the font on every
  text or one track's, their size, colours, outline and ranges kept); `capcut-repair --keep-text`; `slideshow plan` carries the whole
  captions block and writes the captions in upper case when the look says so; the check render burns the look (font file, the size
  from CapCut's units, fill, outline, box, bold, shadow, animation). The video modes keep the house style.
- **Verified:** docs_tool check 0 errors; t01 114; t02 180 (the fonts listed, a font set on the subtitle track only with its sizes and
  colours kept, the check copy's look in its subtitle file: the colour, the fade, the upper case); t03 71, t05 73; rehearsal 221/221.

## 2026-11-06 · Static: FLUX 3 Image Klein on this PC, a third images choice

- **Asked (the user):** "setup flux.3 image klein int8 and if it works, set it up to be the generating model along with openai image in analyze with loupe -> analyze -> static (user picks if it wants klien image,openai image,or just prompts) but this one running locally instead (kleint image int8)".
- **Changed:** awl-start's "Images" question has a third option, "FLUX 3 Klein on this PC" (`static_images=api|klein|prompts`;
  `images api|klein|prompts` in the arguments). `T image generate` takes the source from `static_images` (`--engine` overrides): with
  klein it runs `scripts/image_worker.py` in a ComfyUI portable's Python (`AWL_IMAGE_PYTHON`, a guarded .cmd; `AWL_IMAGE_ROOT`) under
  the GPU lock, ledgered with provider klein and no cost; the seed comes from the request and the attempt (recorded; `--seed`,
  `--again`), the caption the model got is in the answer and the record, at most 10 references, edges a multiple of 16 from 64 to
  4096 (`config.json → static.klein`). `T static check` reports `images_klein`; `static formats` gives Klein's size facts and `static
  format` checks them (no quality in Klein mode); the contract's Images line takes klein. Static §2, §5, §8 and §9, awl-static-images,
  production-agents §2s, awl-wrapup, the router's item 36 and the README follow.
- **Found:** the int8 build exists only for ComfyUI (the reference code has none). Black Forest Labs' own ComfyUI workflows use the w4a8
  prompt upsampler (6.7 GB), ModelSamplingFlux at alpha 16 (the reference code's shift since 2026-10-17; ComfyUI's built-in default is
  the launch value 6.93) and the upsampler's decoding (greedy, presence penalty 1.5 for text-to-image and 0 for edits, no repetition
  penalty). ComfyUI's dynamic VRAM keeps all three models staged at once (15.8 GB of commit on this 16 GB PC), so the worker writes the
  caption, unloads everything (POST /free), then draws (14.1 GB at 1 MP, 15.3 GB at 1216×2160 with a reference; RAM stays mostly free);
  the classic loader filled real RAM and the memory guard stopped it. The same seed gives identical pixels in another process.
- **Verified:** docs_tool check 0 errors; t01 115; t02 192 (a Klein run's format and its refused size, static check's part, an image
  made with no key and no API call, the record's seed and caption, the same request reused, `--again` with a new seed, `--again --seed`,
  the 10-reference limit, the ledger's provider, the contract's Images line); t03 71, t05 73; rehearsal 221/221. On the real model,
  through `T image generate`: a 1216×2160 character sheet in 69 s and a story image with it as the reference in 93 s.

## 2026-11-06 · Static: what the first full test run found, fixed in the toolkit and the steps

- **Asked (the user):** "test the workflow and also do any tweaks in order to deliver the final runable and verified coupled pipeline";
  during the fixes: "feel free to do any updgrades in mcp version if needed too, just fix all isues".
- **The run:** `20261106-063422-static-klein` (one reference of 40 s; one video, Napoleon Bonaparte in 46 s; nine FLUX 3 Klein stills with
  one anchor; one word at a time in the references' look; QC fixes off).
- **Found and changed:**
  - **The check render lost pictures and said nothing.** Hard cuts are one-frame xfades; with cuts off the frame grid ffmpeg rounds each
    offset to a frame, the chain came up one frame short of a join, and xfade dropped every later frame: 973 of 1394 frames (images 8 and
    9 gone) while the file still reported 46.48 s, its sound's length. `T slideshow render` now works in whole frames (each image's first
    frame, each join's frames, `trim=end_frame`) and counts the frames each file holds (`video_frames` against `expected_frames`; short of
    them it answers `ok` false and exits 1); `T slideshow plan` puts every cut on the frame at or just before its line's start, so the
    render and CapCut cut on the same frame. The old code on that timeline gives 973 frames, the new one 1394.
  - **CapCut 9.3 and later open a local clip by its `local_material_id`** (the id of its entry in `draft_meta_info.json`); capcut-cli's
    `register --materials` writes the entries but never the links, so every project the toolkit built would open with its clips missing
    in this PC's CapCut 9.7 (the agent repaired its project with `capcut lint --fix`, which also copied every media file into the draft).
    `T capcut-repair` has a link step after `register` in every mode: on the delivered project its links equal capcut-cli's, and a second
    run changes nothing. `capcut lint --fix` is never used: it also shortens any text over 7 s, trims captions, closes main-track gaps and
    copies all media.
  - **CapCut would not draw the captions' outline.** `capcut import-srt` writes the outline on the material only (check_flag 7); a text
    CapCut styled itself carries it in each style's `strokes` with check_flag 15. `T capcut-font` now writes the outline into the styles
    and the check_flag bits (8 outline, 16 box, 32 shadow) from the material's own values. Every toolkit fix of a draft also updates the
    `draft_info.json` mirror capcut-cli keeps.
  - **The narration was 1.9 LU under the target** (-15.9 LUFS: one loudnorm pass on speech whose peaks sit 19.6 dB over its loudness; two
    passes alone gave -15.5). `T tts say` runs a voice chain (a gentle compressor, `config.json → static.narration.voice_chain`) and two
    loudnorm passes: -14.1 LUFS, true peak -1.5 dBTP, the duration to the sample. The CapCut project plays that file at 1.0, so the final
    carries the target; the render mixes its sound apart and brings it to the target the same way. `--rejoin` joins the existing lines
    again without making any (before, a call without `--only` made every line again).
  - **One word at a time:** 29 of 103 cues overlapped the next (fixed during the run) and 18 were on screen under 0.2 s, one for a single
    frame. A word that would be on screen for less than `captions.min_cue_s` (0.2 s) takes the next word with it, up to twice the words
    at once, never across a sentence end: 85 cues.
  - **The word check listed correct lines.** Speech-to-text writes spoken years as digits ("1769"), "Saint" as "St", and "about a hundred
    thousand" as "about 100,000": numbers, an "a" that belongs to one, and abbreviations are compared as spoken; `narration-words` takes
    the plan's `captions.words`. On this video: 5 lines listed before, none after.
  - **The script came out 13 % long** (45.4 s against the spec's 30–40 s): it was sized at the reference narrator's pace, and the picked
    voice's sample runs about 12 % faster than its cloned narration (2.9 against 2.5 words per second). `tts design` and `tts voice` record
    each sample's `words_per_s`; static §4 sizes the script by it plus every pause.
  - **Image lessons (static §5, §8):** the one image with no reference came back as two stacked pictures with a seam (Klein's upsampler):
    every Klein prompt says one continuous scene from a single viewpoint. A character's reference makes the models draw that character
    larger than the rest (an emperor three times the pope's size, a giant horse): the prompt states sizes and depth. An anchor's ornament
    that reads as a letter came back in every image: the anchor check looks for it.
  - **Smaller:** `T contract --notes` fills `<RUN>` and `<AWL>`; the Static contract no longer says captions are "styled by
    capcut-repair" (in Static it keeps the text as set) and runs T through PowerShell when Git Bash cannot start under memory load;
    awl-record lists the klein source.
- **Not changed:** capcut-cli stays 0.25.0: 0.32.0 writes neither the links nor the strokes, and its new `loudness --target` is not
  needed once the narration carries the target. The images of the run were not drawn again (QC fixes off: the user reviews at the end).

## 2026-11-06 · Static: the edit layer measured, decided by the agent, played by CapCut as verified on this PC

- **Asked (the user, on the first test video):** "in the reference video there were zoom in and zoom outs and other sort of edits but the
  video i exported from capcut seems to have no type of edits beside the font (even though the video-01-preview have a zoom in and zoom out
  but it shaky and not stable), even the font transition had no popup style ... please make sure to check these things that make the video
  enjoyable and engagaging"; then: "dont set fixed numbers let the agent decide how much to zoom in or out, how fast, decide the font popup
  style and do other edits based on ... what the analyzed data tells and what pattern it understands from it, but make sure we chose the
  right approach and what is left to the incoming agent is already verified that will work".
- **Found (measured, not seen at 1 fps):**
  - CapCut 9.7 plays no UNIFORM_SCALE keyframe: the user's export of the rebuilt project measured a zoom of exactly 1.000 on all nine
    stills although each clip was keyed 1.0 to 1.12.
  - The check copy shook: ffmpeg's zoompan crops on whole pixels; frame to frame it wobbled 0.065-0.070 % of the width sideways, where the
    reference wobbles 0.001-0.002.
  - The 1 fps study misread the reference: "a slight push-in on most stills, no caption animation" was in fact a zoom of about 20 % on
    every still, in and out by turns (6 %/s on the first), a pan of 12.6 %, two 0.1 s slides at cuts, and every word popping in (it enters
    about 20 px low at 86 % size, overshoots about 8 px and 4 %, and settles in about five frames).
  - Frame-to-frame feature matching under-reads a slow zoom (a twelfth of a pixel per frame: 1.058 for 1.12), and feature points sit on
    whole pixels (a smooth pan read as shaky).
- **Changed:**
  - `T edit-profile`: a video's edit layer as numbers at its full frame rate (shots split at every picture switch; each shot's zoom and pan
    against its first frame, re-anchored on a long move; pace in the first and last quarter; jitter from sub-pixel optical flow; short
    shots; each cut's signature: the frames that change, shift, scale step, brightness peak and dip, sharpness low; each caption entrance:
    height, width, sideways shift, rise and fill over ten frames against where it settles). A1 runs it for every Static reference; the
    card, the spec and the plan take the moves, joins and entrance from it.
  - No stock style: the timeline has no default move, amount or transition (config `render.motions`, `render.transition` gone); the plan
    decides each image's move and amount (or its own scale and position pairs) and each join; `T slideshow plan` lists what is undecided
    and an edge that would show. The image margin of `T static formats` comes from the references' largest measured move.
  - The check copy draws each still with an exact affine resample per frame (`_render_still`), the values CapCut keys; joins stay
    frame-exact xfades (a CapCut transition's nearest).
  - CapCut: `T capcut-motion` (KFTypeScaleX with uniform scale on, KFTypePositionX/Y; replaces capcut_add_keyframe for moves),
    `T capcut-transitions` (capcut-cli `transition`; replaces capcut_add_transition), `T capcut-text-anim` (one CapCut intro on every
    caption, capped at each caption's length).
  - The CapCut check: `T capcut-check fill` builds one project with every move, all 76 text intros and all 116 transitions of capcut-cli's
    catalogue at known times; the user exports it once; `T capcut-check measure` reads CapCut's own export into `data/capcut-catalogue.md`:
    what CapCut drew, and each option's measured shape, so a reference's entrance and joins are matched by numbers.
- **Verified on this PC's CapCut** (9.7.0.4153; no CapCut Pro, so its export of the check project was blocked and the user recorded
  CapCut's player full screen instead; the recording lined up at 5.45 s, the player's 608x1080 column): the moves play (zoom-in 9.42 %/s
  against 9.54 keyed, zoom-out -8.69 against -8.71, pan-right -9.64 against -9.8, pan-up 9.8 against 9.8); 76 text intros drawn, 59 of
  them free (17 Pro, among them Pop Up, Spring and Bounce In, read from CapCut's own FeedbackOtherInfo.json); 96 of capcut-cli's 116
  transitions drawn, all free, 20 draw nothing. `data/capcut-catalogue.md` holds each one's measured shape and a free-plan column;
  `config.json -> capcut.pro` false keeps the agents to the free ones.
- **The reference read again, frame by frame:** its two "slides" (7.4 % of the width per frame, one with a flash of +0.13, one with a
  dip of -0.15) were inserts: another picture flashed for 3 frames at the turn into the rise and at the turn into the fall; the optical
  flow read the change of picture as a shift. Static §1 now says to view every join that is not a one-frame cut before naming it, and
  §5 plans an insert as an image of its own with `offset_s` (`T slideshow plan` orders the timeline by start). Its joins sit in silent
  pauses (50-90 dB under the voice): no sound effects.

## 2026-11-06 · Static: the optional effects folder (sound effects, green-screen transitions, overlays), verified in CapCut

- **Asked (the user):** "the static mode will also to ask user to provide with a folder of effects(optional) that can have: sound
  effects, and green screen transitions(such as some transitions found in C:\Users\Bulzart\Documents\fx\100 Green screen transitions\100
  Green screen transitions) make sure to cover these too".
- **Changed:**
  - `awl-start` asks for the folder (optional, in the same message as the other paths; `effects <folder>` / `no-effects` in the
    arguments); `state.json → static.effects_folder`; the input guard protects it like the references (read-only: copied, never moved).
  - `T effects scan` (A1): every file measured once and cached (`runs/_effects-cache`, by path, size, time and settings): a sound's
    length, loudness, peak, where it starts, its loudest 10 ms, how fast it falls, its colour (centroid, flatness, strongest frequency);
    an overlay's key green, its shares of green, black, white and transparent pixels in the box a cover on the run's canvas shows, the
    seconds that box holds no green (a green-screen transition hides the picture there: its cut goes inside), all black (nothing shows
    in screen blend) or all white, its brightest and busiest moment; contact sheets with the box outlined and the cover's middle,
    brightest and busiest frames; archives listed, not unpacked. Facts only.
  - The plan's `effects` (static §5): an overlay or a sound from the scan, its moment (`join` K, `line` N or `at_s`) and the second of
    the file that lands on it (`anchor_s`), how an overlay meets the picture (`blend`: chroma, screen, normal), its `fit` (cover,
    contain), `volume`, optional scale and position keys and opacity; a sound's volume and fades; the reason. Nothing has a stock value:
    `T slideshow plan` lists what is left out, places each effect, and puts overlapping ones on separate tracks. Only where an effect plays
    the part of a device the references show; never a sticker, emoji or badge (item 6), even when the folder holds one.
  - `T slideshow render` draws them (ffmpeg's chromakey, the screen blend on black, alpha overlays, keys as expressions; the sounds in the
    mix before its loudness pass).
  - `T capcut-effects` (S4) writes each overlay on its own video track above the stills and each sound on an audio track with capcut-cli
    (`add-video`, `chroma`, `mix-mode`, `add-audio`, `audio-fade`), then the in point, the file's real length, the cover scale (3.16 for
    16:9 on 9:16), the scale and position keys, opacity and volume into the draft; only by ways the CapCut effects check verified, and an
    alpha file made by ffmpeg when CapCut's own chroma key or screen blend does not play but an alpha format does; it refuses the rest.
  - The CapCut effects check (`T capcut-check effects-fill | effects-measure`, static §9): test media with known shapes and times (a green
    wipe with a tone, a glow on black, a red disc in four alpha formats, a ring sticker, a click and a noise burst) written the way
    capcut-effects writes them, measured on CapCut's export or a screen recording with the desktop sound (lined up from its first click
    and the stills' switches); `data/capcut-catalogue.json → effects` and the catalogue's Effects table.
  - `config.json → capcut.pro` false: the agents use only options marked free.
- **Found in the user's folder (219 files):** 5 green-screen transitions (silent sound tracks; 01 and 02 never hide a whole 9:16 box,
  03-05 hide it for 0.13-0.27 s), 25 "Flash" files that are fire and sparks on black, electricity, HUD, light leaks, 26 paint-brush mattes
  (black to white), motion graphics, two sound effects (the mouse click starts 0.53 s into its file), two PNG stickers (never used:
  item 6), two archives (not read).
- **Verified:** CapCut's own export of the effects check (9.7, nothing in it Pro: it exported on the free plan): capcut-cli's chroma
  key and screen blend are ignored (the wipe stayed green, the glow kept its black box), so green screens and black backgrounds go in as
  ProRes 4444 alpha files made by ffmpeg (ProRes 4444, QuickTime Animation and PNG-in-MOV keep their transparency, VP9 does not), and the
  check render draws the same file; an overlay's sound at volume 0 still played, so overlays go in silent and their sound, when wanted,
  on an audio track of its own; the cover scale, the captions above the overlays, scale and position keys on an overlay, sound effects on
  time (5 ms early), at their volume (-11.9 dB for 0.25) and with their fades all play. The measuring side was first proven on synthetic
  exports and a synthetic screen recording (`tests/t06_effects_check.py`: every way read as playing, a recording lined up at 1.7 s from
  its first click, an unkeyed green screen read as chroma not playing).
- **The CapCut plan** (the user, the same day: "the user might also pay for pro subscription too so make him pick, if he picks pro then
  be free to pick any edit feature that pro has if we need them, if not then just the free ones"): `awl-start` asks Free or Pro for every
  Static run (`state.json → capcut_plan`, the contract's CapCut plan line); `T capcut-text-anim`, `capcut-transitions` and
  `capcut-effects` refuse a Pro option on a free run and an option the catalogue shows CapCut not drawing; `config.json → capcut.pro` is
  the default for a run without the key.
- **The third build of the test video** (`06_Nov_2026_v01-3`, the plan decided from the measured reference: the moves, hard cuts, two
  3-frame inserts at the story's turns, CapCut's free Mini Zoom on every word, no effects since the reference has none), measured on the
  user's own CapCut export: zooms 1.198-1.203 for 1.2, 0.832 for 0.833, 0.847 for 0.847, pans 12.55 and 12.52 % of the height (the
  reference: 12.56), inserts 0.10 s, jitter 0.000-0.001, every word entering at 76-96 % of its size and settling in 2-4 frames; it
  exported without a Pro block. The production agent's notes became fixes: `capcut-motion` judges the clips on draft_content.json (a
  template's stale draft_info.json mirror had made it answer ok false), the timeline keeps cut times to 6 places and edit-profile splits a
  given cut by its frame (4 places put a cut 33 µs after its frame and read as a phantom 1-frame shot), the catalogue says pan-left and
  pan-down are the measured pans' keys with the opposite sign; the caption font path inside CapCut's version folder is listed as a risk.

## 2026-11-06 · Static: the team every agent works as

- **Asked (the user):** "on the beginning of the static mode you should give an instruction to the agent such as you're youtube long and
  short content specialist, sociology thinking and human behaviour expert and similar instructions in order to boost and hype him but also
  to be in accordance with what we're trying to achieve".
- **Changed:** static §0 (new): from the first Static step to the wrap-up, the session and every production agent work as one team (a
  YouTube short- and long-form strategist, storyteller, sociologist and human-behaviour expert, attention psychologist, fact-checker, art
  director and editor), ambitious for the video a stranger watches to the end and sends on, and disciplined by the references' data, tone
  and register, sourced facts, a new subject, the verified CapCut options and the hard rules. awl-start reads it when the sub-mode is
  Static; awl-analyze-study and awl-static-plan list it (read again only after a compaction); the Static production prompt (§2s) opens
  with it; the router's item 36 and the README name it. creative-direction §1-§4 stay the A3 lens, read as this team's story-and-attention
  lens.
