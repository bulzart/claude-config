---
name: create-video-adaptive-niche-guardrail
description: "/create-video must never drift from the user's 9-point adaptive-niche shift; how the creative director process is built (2026-11-20)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 043c101b-0b28-4a7f-82ee-6dd10286c87b
  modified: 2026-11-20T04:31:49.674Z
---

The user's 9 points (2026-11-19/20): no fixed niche guides, automatic niche discovery, dynamic creative strategies, more creative freedom, less boring narration, smarter reference learning (understand, not copy), adaptive quality evaluation, better grouping and duration matching, originality over imitation. Flow: analyse references → discover what engages → audience → explore original ideas → custom strategy → produce and critically refine. Their main concern: creativity, boringness, engagement, the right way to narrate. They want the agents to be a creative director, not more paperwork; human review is optional calibration, never mandatory.

**Why:** a session spent on pace/length mechanics let a run skip its creative strategy, explore "five approaches" that were five battles told the same way, and write one run's numbers into the general manuals as niche rules.

**How to apply (built 2026-11-20, static-studio):** reference/10-creative-direction.md is the director's manual. av-profile (scripts/av_tools.py) measures references, narration and export on one yardstick + watch sheets (frames every 5 s with words). direction.json (evidence, 5 approaches on 3+ axes, strategy, 2-3 treatments with sample moments, decision) → blind treatment read → direction-lock BEFORE the script (--late only recorded). Three fresh reads (treatment, script, final) via review-packet/review-record: findings sealed, every one answered, a major gets a round-2 read, edits after a read beyond a small trim need a new read. Code enforces process only, never quality; agents can't hear or watch, so measurements + sheets stand in and the user may listen. Keep per-run numbers out of the general rules; never add per-niche rules. Related: [[create-video-command]], [[feedback-elevenlabs-v4-only]], [[scripts-gather-agents-decide]].
