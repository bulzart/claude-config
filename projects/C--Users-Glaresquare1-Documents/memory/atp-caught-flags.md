---
name: atp-caught-flags
description: "Higgsfield generation flags are recorded in Loupe (web app) with `atp.py caught-flag add`, not in the retired caught_flags.html; write-only during a run, nothing reads it (user 2026-10-13 rule, moved to Loupe 2026-10-14)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 018f5736-eb42-45a5-8337-7d44d473e9a2
  modified: 2026-10-14T19:01:41.394Z
---

Every prompt and video Higgsfield flagged, refused, withheld or rerouted during `/analyze-then-pick` (a moderation block, a job failing in seconds with no reason, an `nsfw` / `ip_checking` upload, a withheld output, a `preset_recommendation` notice instead of a job) is recorded in **Loupe** ([[loupe-web-app]], `http://127.0.0.1:8787/#/flags`). The old `analyze-then-pick/caught_flags.html` page and its template were retired on 2026-10-14 (still in git history); its 6 entries (CF-001..CF-006) were imported with `loupe.py import-flags`, ids kept. The user asked on 2026-10-14 that the record no longer be an HTML file and that it gather smarter data about what may have caused the flag.

**Rule (user, 2026-10-13, unchanged): nobody reads the record during a run.** Never instruct an agent, a plan, a pre-generation check or a run start to read, list, search or digest it (growing records read at every run start rot the agents' context; same reason the caught-errors ledger was retired, [[atp-caught-errors]]). What a flag teaches goes into the references as a general rule (`generation-system.md` §5c.2, the model guides' failure tables, `higgsfield/higgsfield-mcp.md` §9) when the user asks (the flags are read with `T caught-flag list --full`). The only thing a run reads from Loupe is the QC sample library, in the QC phase, through `T qc-consult`.

**How to apply:**
- On any generation flag, in a run or in a chat: `T ledger set … --flagged`, then `T caught-flag add --run RUN --video NN --attempt aK --kind … --tool … --stage … --response "<verbatim|none given>" --trigger "[E|I] …" --cause … --tags <1–4 labels> [--asset …] [--prompt-span …] [--part-of … --part-from S --part-to S]` BEFORE changing the request. The script gathers the request, prompt, params, every input (file, V/A id, thumbnail, file facts: sha1, size, dimensions, printed words), the reference, plan, brief, the flagged ledger row and the raw answer the Higgsfield hook saved (by job id or `--capture ID`); Loupe adds evidence (timing, history of the same input across runs, similar flags, distinguishing prompt terms, diff to the cleared prompt). I supply the judgement and the tags ([[scripts-gather-agents-decide]]). `cleared` only once a changed request was accepted; else `persistent`.
- Loupe down is not a blocker: the entry waits in `loupe/data/outbox/` and gets a provisional `CF-Q…` id.
- Still in the command: item 23, X7 step 6 (`atp-submit`), the production-agents contract item 15, and the main session's `T caught-flag reconcile --run RUN` at each agent's report and in the wrap-up (it lists flagged calls with no entry and now also unclaimed hook captures). No digest at A1/E1, no per-run copy, no X4 check against the record. Related: [[atp-build-prompt-sync]].
