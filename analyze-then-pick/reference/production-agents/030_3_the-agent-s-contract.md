## 3. The agent's contract
1. **Scope.** The agent owns only video NN:
   - its ledger lane `NN`;
   - `40-briefs/video-NN*`, `50-requests/video-NN*` and `60-outputs/video-NN/`;
   - its CapCut project.
   It never reads or writes another video's files.
2. **Tools.** Load the Higgsfield tools (the ToolSearch line in `atp-inputs`) and the CapCut tools (`capcut-assembly.md` §1)
   with ToolSearch before first use.
3. **Generation discipline** (command item 12, X7):
   - `T ledger begin` before and `T ledger set` after every `generate_video` / `generate_image`;
   - one job in flight in its lane;
   - never resubmit after an unknown outcome until it is resolved;
   - at most one autonomous, diagnosed regeneration per clip;
   - a request that failed twice → stop and report.
   The ledger also caps the whole run at 5 jobs in flight. On "parallel cap", wait with `jobs_wait`
   on its own job, or simply retry `begin` after a short pause; never work around it.
4. **Inputs.** Reuse the shared media ids and folder id from `state.json`. Upload only this video's
   own inputs: the Recreate source, hand-off frames, start frames.
5. **State.** Write only through `T state` / `T ledger`; both are locked against the other agents.
   Put the result in `60-outputs/video-NN/result.json` (§4).
6. **CapCut.**
   - Name with `T capcut-name --video NN`, then `capcut_clone_draft` → `T capcut-prep` → build →
     `capcut_validate` → `capcut_save`.
   - Then `T capcut-repair --draft <dir> --preview <…>`. It applies the house text style to every
     text layer and serializes the store-index writes across agents.
   - If CapCut is running, finish the clean video, set `"capcut_pending": true` and stop.
   - **Create:** build the sound layer (`capcut-assembly.md` §3b). Find tracks with WebSearch /
     WebFetch, download them with `T fetch-audio` (license recorded), and never use audio with
     an unknown license.
7. **Leftovers per `generation-system.md` §9b.** Only the must-not-survive list counts.
   Posters, toys, ornaments, signs, and clothing or footwear logos are never reported and never
   cost a retry. The client's guardrails extend the list (`brand-guardrails.md` §5): the plan's
   guardrail operations are carried out and verified (the count at the limit at every checkpoint,
   competitor marks removed and never blurred, the excluded face absent from every shot,
   reflection and placed-back insert, the text lines rewritten and the disclaimers placed).
8. **Counts, openings and permanence** (`anomaly-catalog.md` §4). X9 renders every checkpoint of the
   plan with `T qc --dense`; the agent views every dense sheet, writes the counts and the use
   verdicts into `result.json` (`continuity`), and regenerates once on a break. The only post-fixes
   are the catalog's.
9. **Recreate: source fidelity** (command item 19). The first request already carries the fidelity
   lock: the source action script, the most preserving input and mode, the scoped change, the
   keep-list and the exclusions (`generation-system.md` §5c), checked at X4. The reference's own
   audio comes back, so run `T sync-check` after the merge. Fix a steady offset in post; spend the
   one diagnosed regeneration on drift or a moved action. Record the verdict in `result.json`
   (`sync`).
10. **No questions.** On any blocker, write `result.json` with `"status":"blocked"` and `"blocker"`
   set to one of `permission` | `capcut_running` | `credits` | `failed_twice` | `other`, plus one
   line of detail. Then stop.
11. **Final message:** the content of `result.json`, as one JSON line.
12. **Record.** Every regenerate reason and every flagged delivery (RESIDUAL FAILURE) is written at once in
   the video's brief as an attempt block (the failed request, the verdict with its numbers and frame paths,
   what the retry changes) and in `result.json`; nothing else is written to the library but the flag record
   of item 15. The main session checks
   the briefs against the `result.json` files (§5).
13. **Checks that are never skipped** (CE-016, CE-017, CE-018, CE-019, CE-023, CE-024, CE-025, CE-026, CE-027,
    CE-028, CE-079, CE-083, CE-086). The agent views the sheets itself; an assumption, "the contract forbids" and an unviewed sheet are
    not evidence. Each check's evidence path (sheet, hash, measurement) goes in `result.json` → `continuity`.
    1. **Anchor from frame 0:** the placed or contents product is in the dense sheet of 0 to 1 s and in every
       second after it wherever its anchor is in frame, and its position is read against a fixed neighbour
       at least every 0.25 s across the clip and every cut. Absent in the opening seconds, or moving with no
       action and no motivating cut: regenerate once; never a flagged note.
    2. **The first second, and every transition, insert start and end and overlay start and end** of the
       assembled timeline, on 15 to 30 fps sheets: no frame of the replaced performer in an insert's edges, no
       frozen or held frame, no stray rectangle, halo or brightness step.
    3. **Overlay lifetime and fades:** an overlay cut from the reference exists only on the frames where its
       element is visible and fades with the picture under it.
    4. **Context-bearing source overlays** (a notification, a message, a banner that sets up the joke), the
       hook keyword and any text the plan keeps are present as the original element, not re-typed. The plan lists
       them and the agent ticks each.
    5. **Audio continuity and sameness:** a Recreate's final carries the reference's ORIGINAL audio as one
       whole segment (a stream copy; compare the hash or run a null test), the reference's duration, no cut,
       drop or splice at any join.
    6. **Size:** two estimates (the neighbour at the product's own depth, and a derived distance; `anomaly-catalog.md`
       §2.7), the frame viewed, before any
       size verdict is written.
    7. **Text:** no emoji in any text layer; every layer posX 0.
    8. **Label and lanes:** the wordmark and the variant tag read exactly on a full-resolution frame at rest,
       word by word (a wrong letter regenerates once); no hand covers, wraps or passes through the placed
       product in any beat; the camera and the performer's pose in the last third match the source.
    9. **Shot structure** (a source with hard cuts): the output's cuts against the source's shot list, the same
       count at the same times, person-free cutaways not face shots or ghost dissolves, the placed product in
       every shot where its anchor is in frame, the closing emotion beat present (`anomaly-catalog.md` §4 step
       5i); a merged, dropped or dissolved shot regenerates once as separate clips on the source's own cuts
       (`generation-system.md` §3b.1 item 7).
14. **Docs, before the final message:** the brief carries a block per attempt (every regenerate reason and
    flagged delivery included) and the final prompt; `result.json` complete; `readme-row.md` and the
    deliverables files written; the CF ids of any flag (item 15) listed in `result.json` → `notes`.
15. **Flags** (command item 23; `ATP/caught_flags.html`). Every call Higgsfield flagged, refused, withheld or
    rerouted in the agent's lane is marked with `T ledger set --flagged` and recorded with `T caught-flag add`
    before the request changes, with the verbatim response, the agent's suspected trigger ([E] or [I]) and
    its grouping tags, and the asset, the prompt words and the video part when it can tell (the prompt, the
    inputs with their files and the reference attach themselves); it is `cleared` only once a changed request
    was accepted (with the accepted request.json and job), else `persistent`. `result.json` → `notes` lists the
    CF ids, and `qc` names a video whose flag stayed. The main session reconciles them with `T caught-flag
    reconcile` (§5).

