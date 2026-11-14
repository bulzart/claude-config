---
name: static-mode-no-loupe-checks
description: "user 2026-11-14: Static mode (/create-static) does not use Loupe, so never run or chase Loupe-related tests, hooks or checks when working on it"
metadata:
  node_type: memory
  type: feedback
  originSessionId: efec77d7-2d15-4e76-856d-85333ee657d3
  modified: 2026-11-14T20:06:16.470Z
---

User 2026-11-14, when the AWL test suite showed failures in its Loupe, hook-capture, TTS stand-in and doc checks: "no need to check anything related to loupe, because we don't use it anyways in static mode".

**Why:** Static mode (the /create-static command and AWL's Static sub-mode) has no QC keeper, no flag record and no sample library; Loupe checks cost minutes and prove nothing about a Static change.

**How to apply:** when testing or syncing /create-static (or Static docs), skip `loupe` commands, `t03_loupe`, the Loupe-dependent hook checks and `loupe ensure`; its own suite is `python ~/.claude/create-static/scripts/check_all.py`. Do not report Loupe failures as findings unless the user asks. This does not change [[loupe-reload-before-generating]] or [[loupe-web-app]] for the generation pipelines that do use Loupe.

Related: [[create-static-command]], [[whisper-strictly-medium]].
