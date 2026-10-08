---
name: atp-anomaly-catalog
description: "/analyze-then-pick has reference/anomaly-catalog.md (counts, openings/use, permanence…) wired into the ledger, prompts and QC; new anomaly cases the user reports go there"
metadata:
  node_type: memory
  type: project
  originSessionId: 2adb81e3-0d33-4268-9b11-ed9262381e95
  modified: 2026-10-07T23:04:52.568Z
---

On 2026-10-08 the user reported two logical anomalies in anime Create videos made with
`/analyze-then-pick`: three capsules on a desk became one after the character walked past them and
came back, and a boy drank from the side of a flip-top straw bottle (spout on the left of the lid)
where it has no opening, after his mother filled it with milk. They asked for a general catalog of
such logical and physical anomalies across products, with the prompting and QC steps stacked to
avoid them.

The result is `~/.claude/analyze-then-pick/reference/anomaly-catalog.md` (affordance sheet per
product, 13 anomaly classes, prompting stack §3, QC stack §4, quick reference §5). It is wired into
`generation-system.md` (§3 ledger columns count / opening / level / holder / contact / in-frame,
§5 gate rows, §5d, §8, §9, brief line), the command (contract 14, A2b, A3, A8, E3, E4, X1 "QC
checkpoints", X2, X4, X9, Never), `production-agents.md` (reading list, hard rule, contract item 8,
`continuity` field in result.json), `analysis-protocol.md`, `assets-and-substitution.md`, the
Seedance 2.5 and Wan 3.0 guides, the template and fallback guides, and `atp.py qc --dense
"label:a-b"` (30 fps sheets per checkpoint under `<out>/dense/`). Backup of the pre-change files:
`analyze-then-pick/_backups/20261008-anomaly-catalog/`.

**Why:** the ledger only tracked where the product was, so count changes and wrong-opening use
passed planning and QC; the user wants every generated video to behave like real life.

**How to apply:** when the user reports a new illogical or physically wrong moment, add it as a
case to the matching class in `anomaly-catalog.md` (or a new class) with its ledger entry, prompt
line, QC checkpoint and verdict, and keep the pointers in `generation-system.md` and the command
intact. Plans must list QC checkpoints and X9 must run `T qc --dense` on them. Related:
[[analyze-then-pick-system]], [[claude-folder-git-versioning]].

**2026-10-08, size reckoning (§2.7 rewritten):** after a can on a dresser rendered 2–3× its real
size, §2.7 now reckons every product's size per shot from the registry's real dimensions (cm and
volume, from specs or the §2.7 standard-size table marked [I], never off the product photo), its
distance from the camera (shot size + blocking), the lens, the expected fraction of the frame
(`H·f/(36·d)` for 9:16), the ratio to a named neighbour at the same depth, the size ladder across
products and constancy. `atp.py scale` computes expected size (plan) and observed vs expected on a
frame (QC): ≤15 % ok, 15–25 % note, >25 % or changing or bigger than the holding hand →
regenerate, no post-fix. Wired into the affordance sheet, assets registry step 3, generation-system
§4b.2/§5 "size" gate/§8/§9/§10 "Size:" line, command A2b/X1/X2/X4/X9/Never, Seedance and Wan
§3.14 + checklists, production-agents, preprocessing usage, README, build prompt.

