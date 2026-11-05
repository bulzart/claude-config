---
name: no-cross-pipeline-mentions
description: "User 2026-10-18 (twice): docs, skills, routers, READMEs and prompts of one pipeline must not describe, compare with or point to the other pipeline unless a file or folder path needs it"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 550ea8f9-fa48-4983-be86-ce42635bab6a
  modified: 2026-10-18T12:37:12.206Z
---

The user stopped me twice on 2026-10-18 while I wrote the /analyze-then-generate library: "do not add these type of
descriptions 'The library was rebuilt on 2026-10-18 the way `/analyze-then-pick` was' that might hype the agents to read
analyze-then-pick unnecessarily too, only include it if its necessary for file or folder paths".

**Why:** an agent that meets "rebuilt like /analyze-then-pick", "a fork of ...", "successor of ..." goes and reads the other
pipeline's files, which wastes context and mixes two libraries that are meant to be independent copies.

**How to apply:**
- In a pipeline's router, skills, references, README, learning log and build prompt, never mention the other pipeline (no
  fork/successor/"same as" wording, no pointers to its learning log or ledger). Describe what the pipeline itself does.
- Allowed only where a file or folder path or a real marker needs the name (the toolkit's inventory skips both pipelines'
  `final/` marker folders; shared infrastructure such as the hooks and Loupe must name both because they serve both).
- Shared infrastructure docs (Loupe README/build prompt, hooks) may say "either pipeline".
- This covers my own new text; old history in a log may stay only if it does not point at the other pipeline's files.

Related: [[atg-pipeline]], [[atg-skills-architecture]].
