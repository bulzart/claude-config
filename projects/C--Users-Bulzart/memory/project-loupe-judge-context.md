---
name: project-loupe-judge-context
description: Loupe QC keeper judge context decisions — image fingerprints shipped 2026-11-03; Haiku collector reading reference images declined
metadata:
  node_type: memory
  type: project
  originSessionId: c1639feb-dd77-47ca-950d-178277c7920f
  modified: 2026-11-03T03:42:46.344Z
---

On 2026-11-03 the user asked for "a little bit more context ... for the qc keeper judge to have more accurate and less ambigous verdicts".
Shipped: every image the judge reads carries a content fingerprint (`<name> #xxxxxxxx`, sha1[:8]; Loupe `runs.file_fingerprint`, toolkit
`awl.py _pi_fingerprint`), because asset ids are per-run (one photo was A273 in one run, A274 in another, and A273 was a different photo there).

**Declined:** the user then proposed, and on being told it already exists for samples, chose "Fingerprints only" over extending Loupe's Haiku 5.5
collector to also read and describe the reference images (product/character images sent, the run's client photos).

**Why:** the user's choice; the collector already reads each sample's picture once, with no verdict.

**How to apply:** don't re-propose the reference-reading extension unless the user raises it again. The field is named `fingerprint`, never
`mark` (the judge's "marks" are the admin's circles/arrows/boxes). Related: [[project-analyze-stack]].
