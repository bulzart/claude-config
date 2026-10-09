# Production agents: one video per agent (Analyze Mode)

In Analyze Mode, both Recreate and Create, each video is produced by its **own background agent**,
so no video waits behind another's Higgsfield job. The work is split:
- **this session** analyses, decides and plans (command A1–A9);
- **each agent** runs its one video from inputs to CapCut project (command §5 X3–X10).

At most `config.json → production.max_parallel_agents` (5) agents run at once. Edit Mode never uses
production agents.

## 1. Prepared by this session before any agent starts (command A9)
- **Per video:**
  - the plan `40-briefs/video-NN-plan.md` and the brief `40-briefs/video-NN-brief.md`;
  - the pattern card and request(s) `50-requests/video-NN[-cK]-request.json`, preflighted once.
- **Recreate only:** the pick's prepared source in `10-media/<V>/own/`, from `T strip-inserts`.
  `map.json` there holds the split points, and the folder also holds the 9:16 copy.
- **Shared, in `state.json`:**
  - `higgsfield.folder_id`;
  - `assets.uploads`: media ids of every shared asset, plus Element ids;
  - `long_videos.NN`: the permissions;
  - `analyze_submode`, `model`.

## 2. Spawning
For each video in allocation order, use the Agent tool with `subagent_type: "general-purpose"`,
`run_in_background: true` and description "Produce video NN". Keep at most 5 running; launch the
next one when an agent reports. Prompt (fill the `<…>`):

```
You are the production agent for video NN of a /analyze-then-pick run (Analyze Mode, <recreate|create>).
Produce this one video end to end, then stop.

Run: <RUN>   Library (ATP): C:/Users/Glaresquare1/.claude/analyze-then-pick
Toolkit (T): "C:/Users/Glaresquare1/AppData/Local/Programs/Python/Python312/python.exe" "<ATP>/scripts/atp.py"
Locked model: <model id>; guide: <ATP>/<guide path>.
Your files: <RUN>/40-briefs/video-NN-plan.md, <RUN>/40-briefs/video-NN-brief.md, <RUN>/50-requests/video-NN*.json
<Recreate: your prepared source is <RUN>/10-media/<V>/own/ (map.json = the insert split points).>

Follow, for this video only:
- C:/Users/Glaresquare1/.claude/commands/analyze-then-pick.md §5, steps X3 to X10;
- <ATP>/reference/production-agents.md §3 (your contract);
- <ATP>/reference/generation-system.md §3b (clips), §3c (inserts), §4b (product integration), §5b (motion that has to land), §5d (counts, openings, permanence), §8–§9 (QC);
- <ATP>/reference/anomaly-catalog.md §3 (the prompting stack) and §4 (the QC stack), incl. §2.14 (solidity);
- <ATP>/reference/creative-direction.md §8 (the creative check, as notes);
- <ATP>/reference/brand-guardrails.md §4–§5 and <RUN>/30-assets/guardrails.md, when it exists
  (the client's rules; your plan lists this video's hits and operations);
- <ATP>/reference/capcut-assembly.md, <ATP>/reference/text-and-format.md §3, and the model guide;
- <RUN>/20-analysis/house-approach.md, when it exists (the user's house approach; your plan says
  which of its rules this video applies);
- <RUN>/20-analysis/caught-errors.md (the entries of <ATP>/caught_errors.md that apply to this
  run; your plan names the ones this video applies, their rules are in your prompt, and X9 checks
  each by id). When your QC finds a regenerate reason, record it at once: `T caught-error add
  --source agent --run <RUN> --video NN --assets "<asset paths + key specs>" --prompt <the failed
  request.json> --errors "<execution errors>" --evidence "<checkpoint, t, sheet>" …` with the
  verdict as what was wrong and a general rule. Only when the new generation passes QC, add the
  working prompt: `T caught-error set --id CE-nnn --verified-prompt <the passing request.json>
  --qc-pass "<the verdict>"`; never before, and never when the retry fails (the write is locked;
  ids stay unique across agents). User entries come from the main session.

Hard rules:
- Every paid call goes through `T ledger begin/set --video NN[-cK|-frame]`. One job in flight in
  your lane; exit 3 means do not submit. Never use generate_video_batch.
- Never ask the user anything. On a blocker, write result.json with status "blocked" and stop.
- Caught errors: every entry your plan applies has its rule in the prompt and is checked by id in
  X9 and written in the verdict (command item 22).
- Touch only video NN's files and its CapCut project. Reuse the media ids and the folder id in
  state.json.
- Never capcut_save with force:true.
- Text layers: fontSize 10, no colour; capcut-repair applies the house text style (the user's locked
  preset in config capcut.text_style.learned). Never restyle text, and never run
  `capcut-text-style --learn` / `--replace`.
- Text layers are always horizontally centred: posX 0 on every layer; only posY follows the
  reference. If centred text would cover the product, a face or an insert, move it up or down,
  never sideways (caught error CE-010).
- Every glass, cup or vessel of the product's category shows the product's contents
  (generation-system.md §4b.0, §9). A glass of water beside the can is a regenerate reason, not a note.
- Counts and use (anomaly-catalog.md): every multiple keeps its number except through a visible cause;
  every use goes through the product's real opening after its preparation step, with the contact
  point. Measure the product's size with `T scale` against the plan's named neighbour on a frame
  at rest, one in use and the last (over 25 % off, changing across a cut, or larger than the hand
  that holds it: regenerate, no post-fix). Render the plan's QC checkpoints with `T qc --dense`
  and count at each. A count or state
  that changes without a cause, or a use through the wrong or a closed part, is a regenerate reason.
- Examples (<RUN>/10-media/E…) are study material: never upload them or cut them into the video.
Final message: the one-line JSON of <RUN>/60-outputs/video-NN/result.json.
```

## 3. The agent's contract
1. **Scope.** The agent owns only video NN:
   - its ledger lane `NN`;
   - `40-briefs/video-NN*`, `50-requests/video-NN*` and `60-outputs/video-NN/`;
   - its CapCut project.
   It never reads or writes another video's files.
2. **Tools.** Load the Higgsfield tools (command §1) and the CapCut tools (`capcut-assembly.md` §1)
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

## 4. `60-outputs/video-NN/result.json`
```json
{"video": "NN", "mode": "recreate|create", "status": "done|blocked|failed",
 "clean": "<RUN>/60-outputs/video-NN/clean.mp4",
 "capcut_project": "01_Oct_2026_vNN", "capcut_pending": false,
 "preview": "<RUN>/60-outputs/video-NN/capcut-preview.mp4",
 "jobs": [{"clip": "c1", "job_id": "…", "credits": 35, "attempts": 1}], "credits": 35,
 "qc": "accepted | regenerated once: <why> | failed: <why>",
 "continuity": "counts: <item N/N/N …> | use: <part, contact, verdict> | permanence: <checkpoints ok | …>",
 "sync": "in_sync | fixed offset <s> | regenerated once: <why> | off: <why> | n/a (create)",
 "blocker": null, "notes": "…"}
```

## 5. This session, as agents report
1. Read `result.json`, then `T state --run RUN append videos='<its json>'`.
2. Print one line: video, status, CapCut project, credits.
3. Launch the next queued video.
4. Handle blockers:
   - `permission` → ask (command A7b), store the answer, launch that video again;
   - `credits` → launch nothing more, report;
   - `capcut_running` → leave the project pending;
   - `failed_twice` / `other` → report in the wrap-up.
5. **At the end:** if projects are pending, ask the user once to close CapCut. Then assemble them,
   by relaunching their agents with "CapCut assembly only", or in this session.
