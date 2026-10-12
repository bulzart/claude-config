---
name: scripts-gather-agents-decide
description: "In the user's pipelines Python scripts only gather, extract, record and calculate; they never evaluate, compare for a verdict, rank or decide (user, 2026-10-12). The AI agent running the pipeline carries every judgement."
metadata:
  node_type: memory
  type: feedback
  originSessionId: ff6a4b04-16a6-4927-889e-830c4c6779e4
  modified: 2026-10-12T10:19:19.038Z
---

The user, 2026-10-12, mid-run of the Viral-Browser test: "make sure that the python scripts do not carry the heavy comparison and the final word ... we do not want a script that counts x word or niche that was gathered by the agents and then decides who wins because the script gathered x word to be more used than x word ... scripts can be used to gather and extract but never evaluate, scripts do not have decisive logic nor can understand data; decisions and evaluating the data should be carried by the ai agent that will run the pipeline."

**Why:** a script cannot understand data. Counting words or niches and letting the count decide (dominant niche, shared-word flags, text similarity, gates, caps, ranking, tie-breaks, coverage verdicts) is not a judgement; the agent that reads the evidence must make it and write down why.

**How to apply (every pipeline script, existing and new):**
- Allowed: measure (durations, cuts, loudness), extract (frames, transcripts, OCR, page links), fetch and probe, record the agents' facts and decisions in ledgers (with who, when, reason), tabulate and sort on request (counts, side-by-side values, spreads, sums as plain arithmetic), pure formulas (unit conversion, unit economics), form checks (required fields, formats, a URL for a sourced row).
- Forbidden: a verdict, status or flag derived from the content (verified, conflict, dominant, covered, likely), a threshold gate, floor, cap or quota that refuses or changes an answer, ranking or choosing a winner, tie-breaks, similarity or same-meaning heuristics (shared words, token overlap), refusing to go on because of what the data says.
- The numbers a script used to enforce become guidance for the agent in the playbook and config (rules of thumb the agent applies and records), and the independent checks stay as fresh AI agents (niche audit, blind scorer, red team), never as script gates.
- Related: [[no-hardcoded-names-in-scripts]], [[atg-pipeline]].
