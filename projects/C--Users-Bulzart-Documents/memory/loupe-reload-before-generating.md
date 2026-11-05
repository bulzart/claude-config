---
name: loupe-reload-before-generating
description: "When the user says they changed the Loupe platform, restart the Loupe server and re-sync the keeper/readings before any generation"
metadata:
  node_type: memory
  type: feedback
  originSessionId: d2814013-7f9e-45ba-a173-7873857b1ab5
  modified: 2026-10-27T23:26:52.433Z
---

When the user says they changed Loupe ("reload loupe generation misses agents because i did some changes in the platform", 2026-10-28, AWL run 20261027-233328-27), reload it before the next generation, and again right before the first generation of the run:
1. stop the process listening on 127.0.0.1:8787 (Python code changes need a restart; `web/*.js` and CSS are live),
2. `awl.py loupe ensure` (restarts it detached, syncs the keeper),
3. `python ~/.claude/loupe/loupe.py keeper understand` (reads only new or changed samples), then `keeper status` (run it with PYTHONIOENCODING=utf-8: a BOM in a sample title crashes the cp1252 console).

**Why:** the keeper and the readers answer plan-hints and qc-consult from the library; a stale server or keeper misses the user's new samples and code.
**How to apply:** record it in the run's state.json so the produce phase does it before spawning. Related: [[loupe-web-app]], [[analyze-with-loupe-command]].
