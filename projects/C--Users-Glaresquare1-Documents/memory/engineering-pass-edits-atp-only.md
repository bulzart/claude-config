---
name: engineering-pass-edits-atp-only
description: "the Fable-prompt engineering pass is free to change anything in /analyze-then-pick and its shared infrastructure (Loupe, hooks, settings.json) to improve it, but must not deform the intended functionality; /analyze-then-generate is never edited; user 2026-10-20"
metadata:
  node_type: memory
  type: project
  originSessionId: 550ea8f9-fa48-4983-be86-ce42635bab6a
  modified: 2026-10-20T13:06:15.445Z
---

User, 2026-10-20, in three steps: (1) "remove editing analyze-then-generate at all from the fable prompt, we will be only editing analyze-then-pick"; (2) "edit the fable prompt so that the agent is free to do anything he wants: edit, change, alter, implement or add anything in the pipeline and do not strip it to only inspecting because the idea is that it improves and not just inspects"; (3) "but just not deform the supposed functionality". `Documents/prompts/pipeline-coupling-fable.txt` now carries SCOPE, AUTHORITY, a FUNCTIONALITY CONTRACT, plan item 0d (an executable functionality baseline: command surface snapshot, golden-path rehearsal, docs checks) and a SAFETY NET in place of the old propose-only gate; `pipeline-coupling-fable-addendum-authority.txt` is the same policy as a paste for a session that is already running.

**Why:** the user wants the pipeline improved, not only audited, with the intended behaviour kept intact.

**How to apply:** an agent following that prompt may change /analyze-then-pick and the shared infrastructure it depends on (Loupe, hooks, settings.json, build prompts, memory notes) on evidence, without stopping to ask; /analyze-then-generate is never edited and its tests stay green after shared changes. Still the user's: credits and Higgsfield calls, live run folders, credentials, pushing, the product and brand rules in memory, the start-at-logon refusal. It also covers how agents process data formats, hand data over and judge it (section 0C, item 11) and the optional Whisper question ([[atp-audio-ingest-question]]). Related: [[no-cross-pipeline-mentions]], [[atp-skills-architecture]].
