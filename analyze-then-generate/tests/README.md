# Regression suites of the toolkit (`scripts/atg.py`)

`python tests/run_all.py` runs six suites (about 320 checks, a few minutes). They call the toolkit through its command line, on private copies of a small synthetic run (`tests/fixture/run`: four reference videos and two baseline videos with their cards, without images or audio), and a local web server for the photo and PDF commands. Set `ATG_UNDER_TEST=<path to a working copy of atg.py>` to test a copy before swapping it in (the `model-menu` check of `t11_shared` needs the copy to sit in `scripts/`).

| suite | covers |
|---|---|
| `t11_ledgers` | the candidate, niche and evidence ledgers: they record and tabulate and never rank, gate or label; form checks only |
| `t11_pack` | the specification and photo-link ledgers of the reference pack, the guards of the page and link probes (public addresses only, no download) |
| `t11_shared` | the shared tools: sync-check, conform, the submission ledger, the model menu, the inventory: numbers and records, no verdicts |
| `t11_audio` | the audio profile and context: measured numbers of real tones and noise, no labels |
| `t12_evidence` | the evidence ledger: the opened flag, batch add, copies, the blind and product-only views, `econ` (extra cost, price ladder, shipping charge, fixed yearly cost) |
| `t13_pack_fixes` | the pack fixes: folder names, `photo find --match/--offset/--md`, the looked basis, `spec gaps`, `pdf-text` |

The rule behind them (user, 2026-10-12): a script gathers, extracts, records, tabulates or calculates and never evaluates; the agent that runs the pipeline decides. A new command comes with a check that it returns numbers, tables or records and no verdict.
