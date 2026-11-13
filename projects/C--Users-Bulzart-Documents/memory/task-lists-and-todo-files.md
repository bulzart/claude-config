---
name: task-lists-and-todo-files
description: "user 2026-11-13: every pipeline run keeps a task list and a to-do file (RUN/todo.md, agents' own video todo.md) so what is done and what is next survives compaction and resume; router item 38"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 0ff74cb4-bc5e-4c0e-82b7-c94ab48b8c77
  modified: 2026-11-13T14:42:49.602Z
---

User 2026-11-13: "add to the pipeline so that we use tasklist and todo lists in order to keep context of whats done and whats about to be done".

Built as /analyze-with-loupe contract item 38 (router `commands/analyze-with-loupe.md`, `awl-start` writes `RUN/todo.md`, `awl-static-plan`, `awl-analyze-produce`, `awl-static-sound`, `awl-static-images`, `awl-static-edit`, `awl-record`, `awl-wrapup`, production-agents §2s and §3, the README, and the SessionStart note `hooks/atp_resume_note.py`, which now prints the to-do's path and its `Next:` line). Docs and a hook line only: no toolkit code, no script reads the file.

**Why:** a long run is compacted and resumed several times; `state.json` says which skill is next but not where inside a phase the work stood or what is open (a redraw, a re-record, a blocker), so that lived only in the conversation.

**How to apply:** `RUN/todo.md` (main session) and `RUN/60-outputs/video-NN/todo.md` (each production agent; one file, one writer): markdown checklist `[ ]` `[~]` `[x]` `[-]` (dropped with its reason), a `Next:` line on top, full paths, results in a few words; updated at every step boundary and before any long wait; mirrored in the session's task tools (TaskCreate, TaskUpdate) when the session has them (this session's did not); read first on resume; never given to a fresh reviewer; a record, never a gate. Related: [[awl-static-engagement-by-design]], [[awl-judge-decides-before-generation]], [[awl-never-ask-decide-autonomously]].
