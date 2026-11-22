---
name: create-video-cold-reader-blind
description: "/create-video cold reader (user 2026-11-22): blind by orchestration (review-read / static-cold-reader), script-only limits, no priming, no anchoring numbers or caps; the director decides with full context"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 24e34d07-fc5a-4377-8a48-dcbcee1ff513
  modified: 2026-11-22T19:48:55.310Z
---

User 2026-11-22 (brief #4 Part 12.1, then focused corrections): blind-reader independence must be ENFORCED in the
reusable workflow, not only asked for in a prompt. The script cold reader gets only the title, the narration and each
line's intended whole silence; never earlier findings, the director's rationale, reference conclusions, visual plans,
house rules or exclusion records, and it must not reach them through tools or shared files. Corrections the user listed:
(1) enforce in the orchestration where feasible; (2) a script-only reader may judge the personality and delivery the
writing implies but never claims to have heard the voice or that a tag worked (that is the recording's and the audio/
audiovisual review's job); (3) no priming: no count or sum of the silences, no natural-pause baseline, no "the picture
stays" (keep each silence's own total); (4) valid line ids in the examples, no prefilled scores, never cap the
findings so a serious problem is dropped; (5) a pause cue next to a planned silence is part of that wait, never free:
the reader judges the intended wait, the recording and the edit measure and reconcile it. Keep the focus on what a
first-time viewer finds interesting, confusing, boring, repetitive, moving or satisfying, with causes and impact.

**Why:** a reader who can see the plan or is told the numbers confirms the plan instead of reporting the experience;
the context-aware editorial review and the Creative Director then weigh the findings against the full evidence.

**How to apply:** `review-packet --kind script` writes the packet (and the final review's sheets) into a fresh folder
outside the run; `review-read --kind K` runs the reader as its own `claude -p --restricted --tools Read,Write` process
in that folder (a read of a run file is refused: measured 2026-11-22); the `static-cold-reader` agent type
(~/.claude/agents/, Read and Write only) is the in-session alternative but can still read a guessed absolute path, and
loads only after a Claude Code restart. No new permanent judges; review architecture unchanged. Related:
[[create-video-narration-direction]], [[create-video-command]], [[no-cross-session-messages]].
