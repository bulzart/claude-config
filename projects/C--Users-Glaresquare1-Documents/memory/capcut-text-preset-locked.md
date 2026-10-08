---
name: capcut-text-preset-locked
description: "/analyze-then-pick must always use the user's chosen CapCut text preset (learned from 03_Oct_2026_v09, locked); never re-learn or replace it unasked"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 543cfaf1-143c-45a0-83fb-1977a634706d
  modified: 2026-10-03T16:55:57.118Z
---

Every CapCut text layer in every /analyze-then-pick video uses the text preset the user picked in CapCut project
`03_Oct_2026_v09` (learned 2026-10-03; white text, black outline 0.06, font System, size 10). It lives in
`~/.claude/analyze-then-pick/config.json → capcut.text_style.learned` with `"locked": true`.

**Why:** the user styled one caption in CapCut and said the pipeline "should always use this font preset for all its videos".

**How to apply:** let `atp.py capcut-repair` / `capcut-text-style` apply it; never run `capcut-text-style --learn --replace`
or change the style unless the user explicitly asks for a different preset. If a CapCut project shows another text
style, re-apply the locked preset rather than re-learning.

**Position (user, 2026-10-09):** every text layer is horizontally centred (posX 0); only its height follows the
reference ("whether up, down or in the middle but in the center of the screen"). If centred text would cover the
product, a face or an insert, move it up or down, never sideways. Logged as caught error CE-010 and written into
capcut-assembly.md / text-and-format.md. Related: [[atp-caught-errors]].
