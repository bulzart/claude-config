## 4. `60-outputs/video-NN/result.json`
```json
{"video": "NN", "mode": "recreate|create", "status": "done|blocked|failed",
 "clean": "<RUN>/60-outputs/video-NN/clean.mp4",
 "capcut_project": "01_Oct_2026_vNN", "capcut_pending": false,
 "preview": "<RUN>/60-outputs/video-NN/capcut-preview.mp4",
 "jobs": [{"clip": "c1", "job_id": "…", "credits": 35, "attempts": 1}], "credits": 35,
 "qc": "accepted | regenerated once: <why> | declined fix: <why> | failed: <why>",
 "continuity": "counts: <item N/N/N …> | use: <part, contact, verdict> | permanence: <checkpoints ok | …> | anchor: <in frame from 0.0 s; max drift vs <neighbour> <px> | …> | timeline: <transitions, inserts, overlays, fades ok | …> | audio: <original, whole, hash match | …> | size: <A ×, B ×, agree | provisional> | evidence: <sheet and hash paths>",
 "sync": "within 0.10 s | fixed offset <s> | regenerated once: <why> | off: <why> | n/a (create)",
 "voiceover": "off | <method>: <voice>, <language>, <form>, take a<K>, <kept | laid back at <s> | sync pass <job id> | mixed at <s>, tempo <t>>, lips: <ok | …>, pronunciation: not checked (listen)",
 "fix_proposal": null,
 "keeper_gaps": [],
 "blocker": null, "notes": "…"}
```
`keeper_gaps` lists, one line each, what the Loupe keeper said the library does not cover for this video (`not_covered`) and every question of
its still unmet after the `--note` re-ask (`qc-consult`, and `plan-hints` when the pattern card's "Sample hints" block names one): what was asked
and why it could not be answered. Empty when the keeper had everything it needed. The main session reports them in the wrap-up for the admin.
`fix_proposal` is set only with `blocker: qc_fix_permission` (QC fixes `ask`): `{"findings": ["<expected, why, seen, frame paths>", …], "cause": "<the diagnosis>", "retry_changes": "<what the corrected request changes>", "request": "<path of the corrected request.json>", "credits_now": <n>, "preflight_credits": <n>}`.

