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
- **The run's agent contract:** `50-requests/agent-contract.md`, generated from the §2 prompt at A9
  (never copied from an earlier run).
- **Shared, in `state.json`:**
  - `higgsfield.folder_id`;
  - `assets.uploads`: media ids of every shared asset, plus Element ids;
  - `long_videos.NN`: the permissions;
  - `analyze_submode`, `model`.

## 2. Spawning
For each video in allocation order, use the Agent tool with `subagent_type: "general-purpose"`,
`run_in_background: true` and description "Produce video NN". Keep at most 5 running; launch the
next one when an agent reports. **This prompt is the canonical agent contract.** At A9 the main session
fills it in and writes it to `<RUN>/50-requests/agent-contract.md`, and each agent's spawn message points to
that file. It is generated fresh for every run and never copied from an earlier run's file (a copied contract
once carried a rule that contradicted this section, and five agents obeyed the stale one). Run-specific notes
go in a "Run-specific notes" block at the end of the generated file, never in the rules above it. Prompt (fill
the `<…>`):

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
- When your QC finds a regenerate reason, write it at once in the video's brief as an attempt block (the
  failed request.json, the verdict with its numbers and frame paths, and what the retry changes) and in
  result.json (`qc`, `continuity`, `notes`); a flagged delivery (RESIDUAL FAILURE) is written the same way.
  There is no other error file; the only thing you write to the library is a Higgsfield flag record (below),
  and you read none: the rules live in the references you read above.
- Flags (command item 23). <ATP>/caught_flags.md is written, never read: do not open it. When Higgsfield
  flags, refuses, withholds or reroutes anything in your lane
  (a moderation or policy message; a job failed within seconds with no reason; an upload, video or
  Element marked nsfw / ip_checking / failed; an output withheld; a preset_recommendation notice instead
  of a job), record it BEFORE you change the request: `T ledger set --run <RUN> --job J --status failed
  --flagged --note "<what came back>"`, then `T caught-flag add --run <RUN> --video NN --attempt aK --kind
  … --tool … --stage … --response "<verbatim | none given>" --job J --credits "<refunded n>"
  --flagged-video "<the reference V id + file that rode as the video reference, and/or the clip + path>"
  --trigger "[E|I] <suspected trigger>" --cause … --mode … --model … --product …` (the prompt, params,
  media ids and plan attach themselves). Then make the one diagnosed change, say it with `T caught-flag
  set --id CF-nnn --changed "…"`, and once the changed request is accepted `T caught-flag set --id CF-nnn
  --status cleared --cleared-prompt <request.json> --cleared-job J`; a flag that stays is `--status
  persistent --note "<what was tried>"`. Never a third identical request after two refunded flagged
  failures: plan without the trigger (for example without the video reference) and say fidelity and sync
  are at risk. Never re-upload a flagged asset or video unchanged. A validation error (prompt over 5000
  characters, out of credits) is not a flag.

Hard rules:
- Every paid call goes through `T ledger begin/set --video NN[-cK|-frame]`. One job in flight in
  your lane; exit 3 means do not submit. Never use generate_video_batch.
- Never ask the user anything. On a blocker, write result.json with status "blocked" and stop.
- Spot and guide: the plan's spot passed `generation-system.md` §4b.1c (visible at the source's frame 0 and
  along the whole path, outside every hand's lane, bare and wider than the product, not the nearest plane
  unless the user marked it); where the model guide lists size or place as a limit and no passing-list anchor
  fits, and always for a near-plane spot the user marked, the request carries the size-and-place guide of
  §4b.6, built from the source's bare surface scrubbed of performer, clothing and lettering (Create: neutral
  texture only).
- Label: read the wordmark and the variant tag (flavour, size or model) word by word on a full-resolution
  frame at rest; a wrong letter is a regenerate reason (`anomaly-catalog.md` §2.9, §4 step 5h).
- Touch only video NN's files and its CapCut project. Reuse the media ids and the folder id in
  state.json.
- Never capcut_save with force:true.
- Text layers: fontSize 10, no colour; capcut-repair applies the house text style (the user's locked
  preset in config capcut.text_style.learned). Never restyle text, and never run
  `capcut-text-style --learn` / `--replace`.
- Text layers are always horizontally centred: posX 0 on every layer; only posY follows the
  reference. If centred text would cover the product, a face or an insert, move it up or down,
  never sideways (CE-010). No text layer contains an emoji.
- Every glass, cup or vessel of the product's category shows the product's contents
  (generation-system.md §4b.0, §9). A glass of water beside the can is a regenerate reason, not a note.
- Counts and use (anomaly-catalog.md): every multiple keeps its number except through a visible cause;
  every use goes through the product's real opening after its preparation step, with the contact
  point. Measure the product's size with `T scale` on a full-resolution frame at rest, one in use and the last:
  against the plan's named neighbour at the product's own depth (A: when the product stands in front of or
  behind it, `--depth-ratio` comes from the frame, never 1 by default) AND against a distance you derive from
  the frame, never from the
  shot size (B: `--distance` with `--distance-basis`). An oversize verdict needs A and B to agree; a verdict
  from one assumed number is PROVISIONAL: view the frame yourself before you flag or report it, and never
  write RESIDUAL FAILURE for it (CE-028). With agreeing estimates (over 25 % off, changing across a cut, or larger than the hand
  that holds it: regenerate once, no post-fix; where the model guide lists size as a model limit the
  retry changes the lever (the size-and-place guide of generation-system.md §4b.6, the integration form or the
  anchor class from its passing list), never the sizing words, and a second miss ships the best take flagged). Render the plan's QC checkpoints with `T qc --dense`
  and count at each. A count or state
  that changes without a cause, or a use through the wrong or a closed part, is a regenerate reason.
- Posture, support and place (anomaly-catalog.md §2.16): flat on a bare surface by default, upright only for
  a reason the plan states, on a visible surface, out
  of a working hand's way, no lean on an invented prop, nothing on a thin sheet, the object that is
  picked up named; checked at 30 fps and written as its own line of the verdict.
- Printed surfaces of the source that the card or a guardrail names are replaced by a named concrete
  thing in the model's edit grammar, with the original in the exclusion line; check them at full
  resolution (brand-guardrails.md §4).
- Checks you never skip (details in §3 item 13; write each one's evidence path in result.json
  `continuity`): the product present from frame 0 and read against a fixed neighbour at least every 0.25 s;
  the first second; dense sheets at every transition, insert and overlay start and end; the context-bearing
  source overlays present as the original element; the original audio whole and identical; no emoji in any
  text layer. A check you could not run is written "not checked: <why>", never left out.
- Higgsfield and CapCut notes: a prompt over 5000 characters is rejected before any job exists (set the
  ledger entry failed with the note "rejected before creation"); decline a preset-recommendation notice with
  `declined_preset_id`, never ask the user; if `capcut render` crashes (a fontconfig drawtext segfault), burn
  the preview proxy with ffmpeg and an explicit fontfile (CapCut's en.ttf) and say so in `notes`.
- Deliverables: write your README row to <RUN>/60-outputs/video-NN/readme-row.md (the main session appends
  it to <RUN>/deliverables/README.md), and put `video-NN-clean.mp4` and `video-NN-preview.mp4` in
  <RUN>/deliverables/. With inserts, the clean is the edit built from the pieces, the inserts and the
  original audio, and the generated-only clip never replaces it.
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
15. **Flags** (command item 23; `ATP/caught_flags.md`). Every call Higgsfield flagged, refused, withheld or
    rerouted in the agent's lane is marked with `T ledger set --flagged` and recorded with `T caught-flag add`
    before the request changes, with the verbatim response, the flagged video and prompt, the media the
    request carried and the agent's suspected trigger ([E] or [I]); it is `cleared` only once a changed request
    was accepted (with the accepted request.json and job), else `persistent`. `result.json` → `notes` lists the
    CF ids, and `qc` names a video whose flag stayed. The main session reconciles them with `T caught-flag
    reconcile` (§5).

## 4. `60-outputs/video-NN/result.json`
```json
{"video": "NN", "mode": "recreate|create", "status": "done|blocked|failed",
 "clean": "<RUN>/60-outputs/video-NN/clean.mp4",
 "capcut_project": "01_Oct_2026_vNN", "capcut_pending": false,
 "preview": "<RUN>/60-outputs/video-NN/capcut-preview.mp4",
 "jobs": [{"clip": "c1", "job_id": "…", "credits": 35, "attempts": 1}], "credits": 35,
 "qc": "accepted | regenerated once: <why> | failed: <why>",
 "continuity": "counts: <item N/N/N …> | use: <part, contact, verdict> | permanence: <checkpoints ok | …> | anchor: <in frame from 0.0 s; max drift vs <neighbour> <px> | …> | timeline: <transitions, inserts, overlays, fades ok | …> | audio: <original, whole, hash match | …> | size: <A ×, B ×, agree | provisional> | evidence: <sheet and hash paths>",
 "sync": "in_sync | fixed offset <s> | regenerated once: <why> | off: <why> | n/a (create)",
 "blocker": null, "notes": "…"}
```

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
