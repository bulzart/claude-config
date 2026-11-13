## 5. This session, as agents report
1. Read `result.json`, then `T state --run RUN append videos='<its json>'`.
2. Print one line: video, status, CapCut project, cost (`static.cost_usd_estimate`).
3. **Check that nothing was left undone** (the as-agents-report checklist; command A10), and fix what is
   missing here or relaunch the agent; nothing waits for the wrap-up:
   1. **The attempts.** If `qc` says RESIDUAL FAILURE or regenerated and the video's brief has no attempt
      block with the verdict and what changed, add it now from `result.json`.
   2. **`state.json` → `videos[]`** holds this video (step 1).
   3. **The README table:** the agent's `readme-row.md` (one row per format) is appended to `<RUN>/deliverables/README.md`.
   4. **`<RUN>/deliverables/`** holds `video-NN-title.txt` and `video-NN-thumbnail.png` (and the files the plan's `publish` block names), and
      no video file: the CapCut project each README row names, by its full path, is the final (static §7).
   5. **`result.json`** is complete: every check of §3 item 13 has an evidence path or "not checked: <why>"; `static` is filled
      (`cs-record`), with a `capcut_build` per format whose `problems` are settled or named.
   6. **The plan and brief files** carry the attempts and the S3 and S4 blocks.
4. Launch the next queued video.
5. Handle blockers:
   - `qc_fix_permission` (only with QC fixes `ask`; never with `auto` or `off`) → ask the user the fix question of command item 27 (`cs-produce`), then continue the stopped agent with `approved`, `declined` or `auto`
     (SendMessage to that agent; if it cannot be continued, launch a fresh agent for that video: "resume at cs-images with the proposal in result.json, decision <…>");
   - `credits` → launch nothing more, report;
   - `capcut_running` → leave the project pending;
   - `failed_twice` / `other` → report in the wrap-up.
6. **At the end:** if projects are pending, ask the user once to close CapCut. Then build them,
   by relaunching their agents with `Video NN: S4 and X10`, or in this session with `T capcut-build` (command item 39).
