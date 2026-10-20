---
name: engineering-pass-edits-atp-only
description: "the coupling and execution-design engineering pass (Fable prompt) edits only /analyze-then-pick; /analyze-then-generate, Loupe, hooks and settings.json are read-only references (proposals only); user 2026-10-20"
metadata:
  node_type: memory
  type: project
  originSessionId: 550ea8f9-fa48-4983-be86-ce42635bab6a
  modified: 2026-10-20T01:49:37.575Z
---

User, 2026-10-20: "remove editing analyze-then-generate at all from the fable prompt, we will be only editing analyze-then-pick". The prompt `Documents/prompts/pipeline-coupling-fable.txt` now says so in its SCOPE paragraph and hard rules.

**Why:** the user is focusing the work on /analyze-then-pick; the sibling is the more mature reference and must not drift under an engineering pass.

**How to apply:** an agent following that prompt reads /analyze-then-generate only to compare; defects that can only be fixed in Loupe, the hooks or settings.json become proposals with the exact diff and risk. The same prompt also asks it to understand how agents process data formats, hand data over and judge it (section 0C, item 11), and to add the optional Whisper question to /analyze-then-pick ([[atp-audio-ingest-question]]). Do not re-add edits of the sibling unless the user says so. Related: [[no-cross-pipeline-mentions]], [[atp-skills-architecture]].
