---
name: create-video-older-directions-advisory
description: user 2026-11-24 - /create-video planning rules added later are advisory for directions approved before them (direction-lock planning_rules stamp); safety/money/assets/release stay strict
metadata:
  node_type: memory
  type: project
  originSessionId: 24e34d07-fc5a-4377-8a48-dcbcee1ff513
  modified: 2026-11-24T11:58:00.333Z
---

A direction approved before a set of new planning rules keeps the plan it was approved with: the new creative-planning
requirements are shown to it as advisories, never forcing unrelated re-planning. New productions follow every rule.
Implemented 2026-11-24: direction-lock stamps `planning_rules: 2`; a lock without the stamp (e.g. the Garbo run
20261121-160057-youtube) gets the rules of 2026-11-24 as "advisory (...)" warnings (static_core NEW_PLANNING_RULES).
Never advisory, for every run: safety/content, money (paid ledger), asset integrity, export/release validation.

**Why:** the user, 2026-11-24: "Do not force older completed or partially completed productions to undergo unrelated
creative re-planning merely because new fields were introduced."

**How to apply:** when a later change adds planning requirements, bump PLANNING_RULES, add the new checks to the advisory
list, and keep the safety/integrity checks out of it.
