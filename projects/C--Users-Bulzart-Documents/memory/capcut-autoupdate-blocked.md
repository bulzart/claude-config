---
name: capcut-autoupdate-blocked
description: "CapCut's automatic updates BLOCKED 2026-11-19 at the user's request (it had moved itself 9.7 -> 9.8.0.4213 on 2026-11-16, beta channel); how it is blocked, how to undo it, and that the measured catalogue was made on 9.7.0.4153"
metadata:
  node_type: memory
  type: project
  originSessionId: 549f8e45-9a41-4703-936a-cc5f7f1a833a
  modified: 2026-11-19T03:25:38.906Z
---

User 2026-11-19, after the /create-video CapCut toolkit was verified: "okay and if everything works correctly then block capcut from autoupdating". Done the same day.

**What I found (read-only first):** CapCut updated itself on 2026-11-16 10:39-10:41 from 9.7.x to **9.8.0.4213** (`%LOCALAPPDATA%\CapCut\Apps` holds 9.7.0.4153, 9.7.1.4203 and 9.8.0.4213; the launcher `CapCut.exe`, `ProductInfo.xml` (full_appver 9.8.0.4213) and `uninst.exe` were replaced). There is no scheduled task, service or startup entry for it: the updater is inside the app. `User Data\Config\updateInfo` has `joinBeta=true` (the install is on CapCut's beta channel, which is why it moves fast). The switches are in `User Data\Config\globalSetting` ([General]): `enableAutoUpdate`, `totalSilentUpgradeSwitch` (both were true), `upgradeIntervalMin=30`, `upgradeEnv=formal`; `getCfg` (the server's config) has no update keys. Normal launches never create anything directly in `Apps` (its own timestamp stayed 11/16 10:41:12 across the launches of 11/18-19); only an update installing a new `Apps\<version>` does.

**What the block is (`static-studio/maintenance/capcut_autoupdate.py status | block | unblock`, CapCut must be closed):** (1) `enableAutoUpdate=false` and `totalSilentUpgradeSwitch=false` in globalSetting, only those two lines (UTF-8, CRLF kept; the original is kept beside it as `globalSetting.before-autoupdate-block`); (2) a deny entry `(WD,AD)` for the current user on `Apps`, this folder only (no new files or folders directly in it; existing versions and running CapCut are unaffected). Verified: a new folder and a new file in `Apps` are refused, the toolkit's font scan still reads `Apps`, `unblock` restores the original file byte for byte, `block` is idempotent. Final state: blocked. NOT verified: that CapCut keeps the two switches false after its next launch (nobody launched it; `getCfg` does not carry them), or how it reacts to a server-forced update.

**Consequences, told to the user:** no more updates at all (security fixes too); a forced-update gate could stop CapCut until `unblock`; updating by hand needs `unblock` first (then `block` again); `joinBeta` was left true. The version stays 9.8.0.4213: the measured catalogue (`analyze-with-loupe/data/capcut-catalogue.*`, copied into static-studio/data) was made on **9.7.0.4153** (2026-11-06) and has not been re-measured on 9.8 (a measurement needs an export from CapCut itself). The 9.7 folders are still installed (the launcher runs the newest); a rollback was not asked for and not done.

**9.8 against the pipelines' output (checked 2026-11-19):** the create-clips builds of 2026-11-18 (made from a 9.7-marked template) carry 9.8's own save markers (`new_version` 193.0.0, `last_modified_platform` 9.8.0) and were saved within seconds of the app starting, and CapCut's export service ran afterwards, so 9.8 opens and saves that output; a 9.8-saved draft has the same keys as the 9.7 template. What is still not re-measured on 9.8: the transition/entrance catalogue (needs an export from CapCut itself, `capcut-check measure`), the keyframe behaviour, which options are Pro.

**How to apply:** never run `unblock` unless the user asks; when CapCut-related behaviour looks off, check `capcut_autoupdate.py status` and remember the version is 9.8, the facts in older notes are 9.7. Related: [[pc-pipeline-tooling]], [[create-video-command]].

Index line before the 2026-11-20 compaction of MEMORY.md (kept here so nothing is lost): user 2026-11-19: CapCut self-updated to 9.8.0.4213 (11-16); blocked via static-studio/maintenance/capcut_autoupdate.py; `unblock` only on the user's say
