---
name: scripts-gather-agents-decide
description: "In the user's pipelines, in EVERY mode, Python scripts only gather, extract, record, tabulate and calculate; they never evaluate, compare for a verdict, rank, gate or decide (user, 2026-10-12). The AI agent running the pipeline carries every judgement and records why."
metadata:
  node_type: memory
  type: feedback
  originSessionId: ff6a4b04-16a6-4927-889e-830c4c6779e4
  modified: 2026-10-12T11:15:33.389Z
---

The user, 2026-10-12, mid-run of the Viral-Browser test: "make sure that the python scripts do not carry the heavy comparison and the final word ... we do not want a script that counts x word or niche that was gathered by the agents and then decides who wins because the script gathered x word to be more used than x word ... scripts can be used to gather and extract but never evaluate, scripts do not have decisive logic nor can understand data; decisions and evaluating the data should be carried by the ai agent that will run the pipeline." Then, twice: "this logic should be true for all the modes ... on each mode the agents are those who decide what to do based on the mode specs, scripts just help with gathering and collecting" - not only Viral-Browser.

**Why:** a script cannot understand data. Counting words or niches and letting the count decide (dominant niche, shared-word flags, text similarity, gates, caps, ranking, tie-breaks, coverage or sync verdicts) is not a judgement; the agent that reads the evidence must make it and write down why. A label computed by a script (likely, covered, dominant, verified, in_sync) also lets the reader skip the data and hides the inputs; the live Viral-Browser run showed it (a beep read as words, sung lyrics counted as speech, a music-bed label wrong on noise).

**How to apply (every pipeline script, existing and new, in every mode):**
- Allowed: measure (durations, cuts, loudness, spectra), extract (frames, transcripts, OCR text with its numbers, page links), fetch and probe, record the agents' facts and decisions in ledgers (with who, when, reason), tabulate and sort on request (counts, side-by-side values, spreads, plain weighted sums of the agent's own ratings), pure formulas (unit conversion, unit economics, size geometry), form checks (required fields, formats, a URL for a sourced row, an integer 1-5).
- Forbidden: a verdict, status, flag or label derived from the content, a threshold gate, floor, cap or quota that refuses or changes an answer, ranking or choosing a winner, tie-breaks, similarity or same-meaning heuristics (shared words, token overlap, file-name guesses), refusing to go on because of what the data says.
- Before adding logic to a script ask: does this label, threshold or refusal depend on what the data says? If yes, return the inputs as numbers or a table and let the agent decide.
- Former thresholds become rules of thumb for the agent (ATG: `config.json -> viral_browser.rules_of_thumb`, the references' reading guides, e.g. the sync tolerance, the 15/25 % size bands, the crop-loss guide); the independent checks stay as fresh AI agents (niche audit, blind scorer, red team, reference-pack agents), never as script gates.
- Kept on purpose (they read no meaning): file locks, exact-fingerprint bookkeeping, the safe-address guard of page reads and link probes, form checks, the CapCut "close CapCut" and locked-preset checks.
- Done for /analyze-then-generate (atg.py, 2026-10-12): qc, sync-check, scale, conform, finalize, restore-audio, ledger begin (records and reports `conflicts`), model-menu, inventory, OCR, audio-profile, audio-context, viral-stats, niches, candidates (rate / table / summary; no rank, pool, shortlist), evidence, econ, spec (judge / table / gaps), photo. NOT yet converted: /analyze-then-pick (atp.py and its docs) and analyze-stack still carry the old verdict logic; offer to convert them when relevant.
- Related: [[no-hardcoded-names-in-scripts]], [[atg-pipeline]].
