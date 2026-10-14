## 5. This session, as agents report
1. Read `result.json`, then `T state --run RUN append videos='<its json>'`.
2. Print one line: video, status, CapCut project, credits.
3. **Check that nothing was left undone** (the as-agents-report checklist; command A9b), and fix what is
   missing here or relaunch the agent; nothing waits for the wrap-up:
   0. **The flags** (command item 23). `T caught-flag reconcile --run <RUN>`: every `flagged_unrecorded` row gets
      `T caught-flag add` now (from the agent's `result.json` notes, the ledger history and the request file); each
      `failed_to_judge` row is read and marked or left as the validation or credit error it was; a flag still
      `open` or `persistent` is named in the wrap-up.
   1. **The attempts.** If `qc` says RESIDUAL FAILURE or regenerated and the video's brief has no attempt
      block with the verdict and what changed, add it now from `result.json`.
   2. **`state.json` → `videos[]`** holds this video (step 1).
   3. **The README table:** the agent's `readme-row.md` is appended to `<RUN>/deliverables/README.md`.
   4. **`<RUN>/deliverables/`** holds `video-NN-clean.mp4` and `video-NN-preview.mp4`.
   5. **`result.json`** is complete: every check of §3 item 13 has an evidence path or "not checked: <why>";
      a size verdict without its method, or resting on one assumed number, is re-measured here on the frame
      before it is repeated anywhere.
   6. **The plan and brief files** carry the attempts and the final prompt.
4. Launch the next queued video.
5. Handle blockers:
   - `permission` → ask (command A7b), store the answer, launch that video again;
   - `credits` → launch nothing more, report;
   - `capcut_running` → leave the project pending;
   - `failed_twice` / `other` → report in the wrap-up.
6. **At the end:** if projects are pending, ask the user once to close CapCut. Then assemble them,
   by relaunching their agents with "CapCut assembly only", or in this session.
