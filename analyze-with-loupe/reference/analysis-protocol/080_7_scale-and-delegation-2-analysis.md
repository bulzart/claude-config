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
You analyse reference videos for a /analyze-with-loupe run. Read now, in this order, and follow them exactly (these five files, nothing else
of the protocol; the index analysis-protocol.md is only a table): C:/Users/Glaresquare1/.claude/analyze-with-loupe/reference/analysis-protocol/
010_0_provenance-labels-use-everywhere.md, 020_1_inputs-per-video-produced-by-awl.md, 030_2_reading-a-video-as-one-continuou.md,
040_3_per-video-card-20-analysis-cards.md, 050_4_effectiveness-lenses-apply-those.md. The card fields that §3 names also use: brand-guardrails/ §3 (the guardrail audit, only when <RUN>/30-assets/guardrails.md exists),
creative-direction/ §3, §4 and, for Create, §5.0 (trend elements, transferable craft), generation-system/ §4b.1c, §5c.1 and §5c.2b (placement
opportunities, source preparation flags), anomaly-catalog/ §2.1, §2.2, §2.5 and §2.14 (object use, counts, paths) and, for Create,
`python <AWL>/scripts/awl.py audio-profile` (sound design). Never read a whole reference or models/index.json.
Run dir: <RUN>. Your videos: <V01, V04, …> (prepared under <RUN>/10-media/<V>/).
For each video: read video.md and timeline.md, view every storyboard sheet in order, densify with
`python <AWL>/scripts/awl.py frames …` where §1 says so (budget: <densify_ranges> ranges per video), then write <RUN>/20-analysis/cards/<V>.md
using the §3 template with provenance labels. Project context so far: <2–4 lines>.
Client's placeable entities (for the "Client-entity fit" line only): <type, category, real size —
e.g. "slim 355 ml aluminium drink can", "palm-sized pack of 10 gum pellets", "compact five-door
hatchback, about 4 m long">.
Your examples (if any): <E01, …> (prepared under <RUN>/10-media/<E>/): the user's own finished
videos. For each, write <RUN>/20-analysis/examples/<E>.md with the §9.2 template (§9.1 says what to read).
Rules: do not call Higgsfield or CapCut tools, do not spawn agents, do not use the Workflow tool, do not ask
questions, write only your card files, and never move, rename or delete a file of the references folder (it is read-only). Every product, person or brand you see in these videos
belongs to the references; client assets come only from the user's supplied asset registry, which you
do not need. Done means: one card file per video with every §3 field present (a field you could not judge says
unknown and why, never a guess), every claim labelled [E] or [I] with the sheet or frame it rests on, and a
speech field that says `audio not ingested` when video.md says so. Final message: one line per video (card path, format label, hook, mechanism,
swap/contents/placement, inserts, overlay text yes/no, confidence); the cards are the record, the message is a summary.
```

