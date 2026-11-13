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
You analyse reference videos for a /create-static run (narrated still-image videos). Read now, in this order, and follow them exactly: C:/Users/Bulzart/.claude/create-static/reference/
static/005_0_the-team-who-works-a-static-run.md, static/010_1_what-static-mines-from-the-refer.md, static/020_2_the-static-card-and-the-spec-a3.md (the Static card you write and the
spec it feeds), and from analysis-protocol/ (the index analysis-protocol.md is only a table): 010_0_provenance-labels-use-everywhere.md, 020_1_inputs-per-video-produced-by-awl.md,
030_2_reading-a-video-as-one-continuou.md and 050_4_effectiveness-lenses-apply-those.md. When <RUN>/30-assets/guardrails.md exists also brand-guardrails/ §3 (the guardrail audit) and
creative-direction/ §3 and §4 (audience, trend read). Never read a whole reference.
Run dir: <RUN>. Your videos: <V01, V04, …> (prepared under <RUN>/10-media/<V>/).
For each video: read video.md and timeline.md, view every storyboard sheet in order, densify with `python <CS>/scripts/cs.py frames …` where the protocol says so (no cap on densified
ranges: a Static run has no effort level), run `python <CS>/scripts/cs.py edit-profile --run <RUN> --ref <V>` once its cuts exist, then write <RUN>/20-analysis/cards/<V>.md as the
Static card static §2 describes, with provenance labels. Project context so far: <2–4 lines>. The registry's one-line summary of what the user supplied: <characters, no product / …>.
Your examples (if any): <E01, …> (prepared under <RUN>/10-media/<E>/): the user's own finished videos. For each, write <RUN>/20-analysis/examples/<E>.md with the §9.2 template (§9.1 says
what to read).
Rules: do not call CapCut tools, do not spawn agents, do not use the Workflow tool, do not ask questions, write only your card files, and never move, rename or delete a file of the
references or examples folders (they are read-only). Every person or brand you see in these videos belongs to the references; assets come only from the user's supplied asset registry,
which you do not need. Done means: one card file per video with every field of the Static card present (a field you could not judge says unknown and why, never a guess), every claim
labelled [E] or [I] with the sheet or frame it rests on. Final message: one line per video (card path, format label, hook, story form, narration pace, cut and caption pattern, confidence);
the cards are the record, the message is a summary.
```
