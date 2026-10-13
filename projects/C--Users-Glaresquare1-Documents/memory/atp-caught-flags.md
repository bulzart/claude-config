---
name: atp-caught-flags
description: "ATP/caught_flags.html — the flag record, one self-contained page (data + viewer: search, filters, grouping by trigger/asset/video). Whenever a Higgsfield generation flag occurs in /analyze-then-pick, SAVE it there with `atp.py caught-flag add`; write-only, no agent/step/plan reads it (user 2026-10-13, context rot)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 018f5736-eb42-45a5-8337-7d44d473e9a2
  modified: 2026-10-13T20:32:25.791Z
---

`~/.claude/analyze-then-pick/caught_flags.html` records every prompt and video Higgsfield flagged, refused, withheld or rerouted during `/analyze-then-pick` (a moderation block, a job failing in seconds with no reason, an `nsfw` / `ip_checking` upload, a withheld output, a `preset_recommendation` notice instead of a job). The user asked for the ledger on 2026-10-12, and on 2026-10-13 asked for it to be an HTML file / simple web app instead of markdown that gathers which video it was, which asset caused the flag, which part of the video and which prompt, as logical, searchable, groupable data.

**Rule (user, 2026-10-13): the page stays where it is, but nobody reads it.** Never instruct an agent, a plan, a pre-generation check or a run start to read it, digest it or copy it into a run (growing files read at every run start rot the agents' context; same reason the caught-errors ledger was retired, [[atp-caught-errors]]). The name lives here, in memory, so that whenever a generation flag occurs I save it. What a flag teaches goes into the references as a general rule (`generation-system.md` §5c.2, the model guides' failure tables, `higgsfield/higgsfield-mcp.md` §9) through `/update-from-errors`, which reads the page with `T caught-flag list --full`.

**How it works:** the data is a JSON block inside the page; the viewer (search with `kind:` `tag:` `asset:` `video:` `run:` `status:` `prompt:` operators, filters, group by trigger tag / suspected asset / video / kind / run / model / cause / status / month, detail view with input thumbnails, the prompt with the suspect words marked, a frame of the suspected video part) is `scripts/caught_flags_template.html`. Never edit the HTML by hand: edit the template and run `T caught-flag render`. `T caught-flag open` shows it to the user.

**How to apply:**
- On any generation flag, in a run or in a chat: `T ledger set … --flagged`, then `T caught-flag add --run RUN --video NN --attempt aK --kind … --tool … --stage … --response "<verbatim|none given>" --trigger "[E|I] …" --cause … --tags <1–4 labels> [--asset "Image 2"] [--prompt-span "<exact words>"] [--part-of "reference V10" --part-from S --part-to S]` BEFORE changing the request. The script gathers the request, prompt, params, every input with file/type/V-A id/thumbnail, the reference and source segment, plan, brief and the flagged ledger row; I (the agent) supply the judgement and the tags (scripts gather, agents decide, [[scripts-gather-agents-decide]]). `--tags` is required. `cleared` only once a changed request was accepted; else `persistent`.
- Still in the command: the writing (item 23, X7 step 6, production-agents contract item 15) and the main session's `T caught-flag reconcile --run RUN` at each agent's report and the wrap-up (it only lists flagged calls with no entry yet). No digest read at A1/E1, no per-run copy, no X4 check against the page; X4 tests the plan against the references' service-block rules.
- Three entries so far, migrated from the old markdown on 2026-10-13: CF-001 (celebrity face in the video reference, two refunded failures; rule in `generation-system.md` §5c.2), CF-002 and CF-003 (preset notice; rule in the Higgsfield guide §9). Related: [[atp-build-prompt-sync]].
