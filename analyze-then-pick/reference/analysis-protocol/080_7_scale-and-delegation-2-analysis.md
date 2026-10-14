## 7. Scale and delegation (≤ 2 analysis agents, no Workflow)

- **≤ 6 videos** (or ≤ ~3 min total): the main session analyses everything itself.
- **More:** spawn **1** analysis agent, or **2** when there are over ~15 videos, each with a
  **disjoint** list of video ids. Two analysis agents is the ceiling; production agents (one per
  video, `production-agents.md`) come later and are separate.
- Agents only read this protocol plus their videos' prepared files, write the cards, and never ask
  questions.
- The main session always writes the synthesis (§5–§6) itself.

Agent prompt (fill in the placeholders; use the Agent tool with `subagent_type: general-purpose`):

```
You analyse reference videos for a /analyze-then-pick run. Follow the section files of
C:/Users/Glaresquare1/.claude/analyze-then-pick/reference/analysis-protocol/ (the index is analysis-protocol.md) §0–§4 exactly, and read
only those. The card fields that §3 names also use: brand-guardrails/ §3 (the guardrail audit, only when <RUN>/30-assets/guardrails.md exists),
creative-direction/ §3, §4 and, for Create, §5.0 (trend elements, transferable craft), generation-system/ §4b.1c, §5c.1 and §5c.2b (placement
opportunities, source preparation flags), anomaly-catalog/ §2.1, §2.2, §2.5 and §2.14 (object use, counts, paths) and, for Create,
`python <ATP>/scripts/atp.py audio-profile` (sound design). Never read a whole reference or models/index.json.
Run dir: <RUN>. Your videos: <V01, V04, …> (prepared under <RUN>/10-media/<V>/).
For each video: read video.md and timeline.md, view every storyboard sheet in order, densify with
`python <ATP>/scripts/atp.py frames …` where §1 says so, then write <RUN>/20-analysis/cards/<V>.md
using the §3 template with provenance labels. Project context so far: <2–4 lines>.
Client's placeable entities (for the "Client-entity fit" line only): <type, category, real size —
e.g. "slim 355 ml aluminium drink can", "palm-sized pack of 10 gum pellets", "compact five-door
hatchback, about 4 m long">.
Your examples (if any): <E01, …> (prepared under <RUN>/10-media/<E>/): the user's own finished
videos. For each, write <RUN>/20-analysis/examples/<E>.md with the §9.2 template (§9.1 says what to read).
Rules: do not call Higgsfield tools, do not spawn agents, do not use the Workflow tool, do not ask
questions, write only your card files. Every product, person or brand you see in these videos
belongs to the references; client assets come only from the user's supplied asset registry, which you
do not need. Final message: one line per video (format label, hook, mechanism,
swap/contents/placement, inserts, overlay text yes/no, confidence).
```

