---
name: sheets-audit-runner-technique
description: "Independent Google Sheets re-test of a release /copy from the owner's Dev Tools Apps Script project (Audit.gs runner, gen_audit_gs.py, state keys, pasting, Run cadence)"
metadata:
  type: reference
---

01A pattern (2026-10-04): `tests/audit/<date>/indep/gen_audit_gs.py` embeds the independent cases (calc.py expected
values + cell writes) gzip/base64 into `Audit.gs`; TARGETS = the ids of fresh `/copy` disposables of the release
files; AUDIT_KEY must be a NEW script-property key for every fresh run (state persists per key). Paste Audit.gs into
the Dev Tools project (clip.ps1 → open the file → click inside the code → ctrl+a, ctrl+v, ctrl+s; verify with the
Monaco model length/djb2 hash), open the file so the Run button targets its first function (`auditRun`), click Run
(JS: button[aria-label="Run the selected function"]) and re-click after each "Execution completed" until the log
prints the report. Read progress from `document.body.innerText` (replace `=&?` before returning). Typed-cell refusals
are counted ("refused") — a refusal means the sheet's validation blocked a value the case needs.
Dev Tools QA copies are rebuilt and checked by `opDrive2` (Ops2.gs: rebuild masters/release/demo/QA, qaClear,
qaRunNext ×3, qaSummary; `_pass2` property reruns a slice). Each qaRunNext batch ≈ 250 s for ~45 fixtures.
Fixture files must carry explicit `rate_calc` nulls, otherwise the Pro Rate Calculator keeps its defaults in the
fixture books while the oracle assumes blanks (found 2026-10-04, AUD2-*).
Related: [[apps-script-editor-paste-technique]], [[money-os-release-state]]
