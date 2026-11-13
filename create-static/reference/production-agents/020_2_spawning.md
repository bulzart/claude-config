## 2. Spawning
For each video in allocation order, use the Agent tool with `subagent_type: "general-purpose"`, `model: "opus"`
(the production agents run QC and judge: Opus 5.5, the user, 2026-10-28), `run_in_background: true` and description "Produce video NN". Keep at most 5 running, none
overlapping (each agent owns video NN only); launch the next one when an agent reports.
- **The prompt is the canonical agent contract** of §2s. At A9s the main session generates it with `T contract --run RUN [--notes "…"]` (the
  toolkit fills the placeholders from state.json, keeps the previous file beside it when it differs, and lists any placeholder it could not
  fill: no agent is spawned while one remains), written to `<RUN>/50-requests/agent-contract.md`; each agent's spawn message points to
  that file. It is generated fresh for every run and never copied from an earlier run's file (a copied contract
  once carried a rule that contradicted this section, and five agents obeyed the stale one). Run-specific notes
  go in a "Run-specific notes" block at the end of the generated file, never in the rules above it.
- **The spawn message** names what the agent makes and, from `state.json → static.video_info` (`T static subjects --run RUN`), the video's own
  approach and language (the contract's "One channel" rule refers to them):
  - `Video NN`: its whole work, S3, S4 and X10;
  - `Video NN, images K1-K2: S3 only` (and `… and the thumbnail`): one stretch of a long video's stills (`cs-produce` A9b);
  - `Video NN: S4 and X10`: the edit and the record, every image already made;
  - `Video NN, format <tag>` (and `, images K1-K2: S3 only`): one more format of a video (static §2b);
  - the path of the agent's own to-do, `<RUN>/60-outputs/video-NN/todo.md` (command item 38).
- **What the agent finds:** the files of §1, and the contract of §3 in its prompt. It runs `cs-images`, then `cs-edit`, then `cs-record`.
- **What comes back:** one JSON line, the content of `result.json` (§4), handled as §5 says.
- **Without the Agent tool** the main session runs S3, S4 and X10 per video itself, one video at a time.
