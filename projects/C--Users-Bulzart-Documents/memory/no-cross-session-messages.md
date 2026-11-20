---
name: no-cross-session-messages
description: Never message other Claude sessions on this PC to check what they are doing; their work is usually unrelated and the message interrupts it
metadata:
  node_type: memory
  type: feedback
  originSessionId: 046004a5-1b5b-492c-a227-505bb55d8234
  modified: 2026-11-20T12:42:35.791Z
---

Do not send SendMessage (cross-session) messages to other Claude sessions to ask whether they are running a pipeline, building CapCut projects or touching a run.

**Why:** the user, 2026-11-20, after I messaged a peer session ("Are you running /create-clips production...") that was busy on something completely different (Static Studio): "dont sent [that message] because you're sending message to another session agent working completely on something else". The message lands in the other session's conversation and interrupts its work.

**How to apply:** find out from files and processes instead: the run's `state.json` (`videos.<id>.status`), the newest file times in `RUN/60-outputs/`, the CapCut drafts folder, `Get-Process CapCut`. `ListAgents` may be used only to see that a session exists, never followed by a message. If it is still unclear whether another session is working on the same run, ask the user, not the session. Related: [[create-clips-pipeline]].
