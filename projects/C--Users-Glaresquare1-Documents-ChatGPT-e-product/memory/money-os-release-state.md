---
name: money-os-release-state
description: "Freelancer Money OS status as of 2026-10-09 — v1.2.1 (state planning-rate table D-82) rebuilt local + cloud; setup video re-recorded on v1.2.1 (D-83, 3 min 51 s) awaiting owner approval; Google builder number-format fix (D-84) with in-place cloud rebuild 2026-10-09; gates still open; nothing live"
metadata:
  node_type: memory
  type: project
  originSessionId: a7551dd1-9530-4a94-a346-55ba54629a27
  modified: 2026-10-05T02:51:36.937Z
---

Everything for 01A lives in `Documents/prompts/digital-products-specs/01A-Freelancer-Money-OS/` (README.md = status;
INVENTORY.md = every file; scripts use source/paths.py). Google items owned by bulzarti@gmail.com (`/u/4/`); ids in
product/google-sheets/cloud-manifest.md + drive-ledger.md. v1.0.0 files archived in release/archive/v1.0.0/.

History: v1.1.0 (2026-10-04 morning) fixed an audit's 10 findings (D-56…D-69). The same day an **independent release
audit** (second calculator `tests/audit/2026-10-04_release-audit/indep/calc.py`, 53 cases from IRS sources) found six
calculation defects in v1.1.0 on every platform — partial / client-less reimbursements, stray FX rate on USD rows,
refunds of sales-tax invoices booked gross, 2027 Q4 due date ignoring MLK Day — plus two claim problems (car method
"Both" relies on the buyer's statement; non-US "ready" wording). Fixed as **v1.1.1** (D-70…D-76, VERSION 1.1.1).
Retest of the actual deliverables (2026-10-04 11:09–15:53): Excel files baked 11:09 (Pro sha256 3cd36584…, Base
f0b1b448…; ZIPs a7886cb6… / 598f614d…); Excel Windows 53/53 + 52/52 audit cases and 110/110 fixtures per edition
(31,388 / 30,948 values); Google Sheets masters/release/demo/QA rebuilt in place by Dev Tools opDrive2 (QA 110/110
each, demos 945/941); fresh `/copy` of each release file passed 53/53 (Pro) and 52/52 (Base) audit cases with 0 refused
(Audit.gs); Excel web Pro + Base by hand (XW-111). Reports: docs/2026-10-04_independent-release-audit-v1.1.1.md (+pdf),
owner report docs/2026-10-04_owner-report-v1.1.md (updated), test log §F. Disposable Drive copies trashed 2026-10-05
04:46 (Ops3.gs). OneDrive still holds the `_r2` test uploads.

Owner's video brief for the re-record (videos are still v1.0.0): at most 4 min 30 s, with voice-over; do NOT include any
"unlock the sheet" content (the owner withdrew that request). Also still open: add video-generation instructions to the
other build prompts (01B…03C) using the same pipeline.

Still open (owner/outside gates): CPA review (never claim it), sharing approval + second-account /copy test,
store/checkout/support inbox, licence/refund wording, video re-record + ElevenLabs plan, Excel 2019/Mac/mobile untested.
Nothing published or sold.

**Why:** later sessions must not redo finished work or overclaim; gates must stay honest; v1.1.1 is the current build.

**How to apply:** start from README.md and docs/release-checklist.md; evidence in tests/test-log.md §F and
tests/audit/2026-10-04_release-audit/. Fixture rule: every fixture needs explicit `rate_calc` nulls (see
[[sheets-audit-runner-technique]]). Related: [[excel-com-testing-technique]], [[excel-web-chrome-testing-technique]],
[[browser-tooling-preference]], [[apps-script-editor-paste-technique]]

**2026-10-05 (05:35–10:56) independent CPA/EA-standard review of v1.1.1 → v1.2.0.** Reviewer's own calculator
`tests/audit/2026-10-05_cpa-standard-review/indep/cpa_calc.py` (62 cases): v1.1.1 arithmetic/federal rules correct on every
platform (0 differences). Findings: F-1 missing input for other household taxable income (built as `set_OtherIncome` +
engine row OTHER → AGI, D-77), F-2 stale demo figures in tutorial/description ($7,238 / $2,068 are right, D-78), F-3 version
strings/counts (D-79), F-4 Excel-web list-cell autocomplete (documented), F-5 oracle names not emitted (fixed), F-6 per-client
reimbursement matching (accepted, D-81). VERSION 1.2.0; 113 fixtures; decisions D-77…D-81. Retest: oracle PASS; Excel Windows
62/62 + 61/61 reviewer cases (19,800 / 19,503 values) and 113/113 fixtures (32,679 / 32,227); Google Sheets fresh /copy
62/62 + 61/61 (same counts, 0 refused), QA copies 113/113 each, demos 1,412 / 1,407 = calculator; Excel web Pro CPA-51 and
Base worked example by hand. Google files rebuilt in place 06:53–07:11 (same ids), release/demo renamed "v1.2" (06:53),
masters renamed "v1.2_" (10:24); six "BACKUP 2026-10-05 v1.1.1 — …" copies in My Drive root (+ their 6 form copies, keep).
Excel: blanks e31f89fd… (Base) / 3a8f1c25… (Pro), ZIPs 8eede99b… / bb61b0ad…; SHA256SUMS regenerated. Report:
docs/2026-10-05_independent-cpa-standard-review-and-update.md (+ 9-page PDF); test log §G. Review disposables (4 copies +
4 forms) trashed 10:52–10:56; OneDrive `CPAreview_*` uploads left. Gates still open: signed CPA review (unsigned
CPA/EA-standard review only), sharing + second-account /copy test, store/checkout/support, licence/refund wording,
videos (v1.0.0), screenshots (v1.1).

**2026-10-08 v1.2.1 (D-82, owner request after the review):** `source/tools/state_rates_2026.py` → JSON + Markdown table of
suggested state planning rates (flat rate / 0 / effective rate at $60k single taxable income rounded up; 2nd column $120k;
Tax Foundation 2026 table + SC DOR + TF errata for GA; research note `source/notes/research/state-planning-rates-2026.md`,
yearly refresh with the January constants). Lives in tutorial Appendix A (PDF 23 pages) and Access Guide page 3 (3 pages);
Settings note + FAQ entry point to it; VERSION 1.2.1, MOS_VERSION 1.2.1. Rebuilt: Excel (bake OK), ZIPs, bundles; Google six
files in place 03:26–03:43 via `tests/audit/2026-10-08_v121/Ops5.gs` after "BACKUP 2026-10-08 v1.2.0 — …" copies (ids in the
ledger); bound Pro scripts (master 143DFGDF…, release 10n7Qgo0…, demo 1-doxjfVC…) pasted 1.2.1 — dismiss the "signed in as"
notice first; QA copies 113/113 (Pro 32,679 / Base 32,227 values). Headless **Edge stopped writing PDFs/screenshots** (hands off
to its startup-boost process even with --user-data-dir) → both PDF builders use headless Chrome now. Video v1.2.1 (D-83, done 2026-10-09): narration 14 clips (ElevenLabs flow 1IQg75FE5WkEWHQdubaH, Alex), recorded 05:48–06:44
on the disposable copy 1CuSr_JilmORa7R0I7NU1v0iAHUi-NA-fv_187mrrUOk (+2 form copies; Trash after the owner approves), edit
`assets/video/setup-tutorial-v1.2/tools/edit_spec.py` + render.py → `assets/video/Setup_tutorial_Pro.mp4` 3 min 51 s, −16.6 LUFS,
stereo; v1.0.0 video archived in `assets/video/archive/v1.0.0/`; permission screens reused from the 2026-10-03 capture (account
already authorised); phone-form taps placed by hand; docs/checksums/inventory updated by `source/tools/finalize_video_v121.py`.
Tour_60s / Setup_walkthrough_Base are still v1.0.0. Owner gates for the video: approve it, ElevenLabs commercial plan.

**2026-10-09 number-format defect (D-84):** the v1.2.0 in-place rebuild left old number formats on Settings cells whose row
moved (B67 showed "1400.00%"; B57/B73) — `Sheet.clear()` keeps number formats. Fix in `source/build/emit_gs.py`
(`resetSheet_`: clearFormat + setNumberFormat('General'); `buildFormatting` starts from 'General'); bundles rebuilt, SHA256SUMS
via `source/tools/write_sums.py`; cloud: Dev Tools Code.gs = new Dev.gs, `tests/audit/2026-10-09_v121-formats/Ops6.gs` over
Audit.gs (runner `ops5Run`, keys rebuildOps_v121f / rebuildDrive_v121f; backups "BACKUP 2026-10-09 v1.2.1 — …" ids in the
ledger; a page-resident setInterval autoclicker presses Run until OPS6 ALL DONE; `opFormats6` scans every block cell's number
format against the spec). Results in `tests/audit/2026-10-09_v121-formats/notes.md` and test-log §G4.
