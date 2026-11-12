---
name: neuro-llm-longform-windows-port
description: Neuro LLM long-form lane ported to native Windows (no WSL) at ~/glare-work/Neuro/llm-longform-win; skill glare-neuro-llm-longform-win; how to run it and what the port changed
metadata:
  node_type: memory
  type: project
  originSessionId: 64219a15-3c0f-443d-871e-13c20d59e89e
  modified: 2026-11-12T19:36:57.144Z
---

The Neuro LLM long-form pack v02 (zip in Downloads, team handover: 3-minute 16:9 kinetic explainers rendered from HTML in headless Chrome, one ElevenLabs voiceover, zero Higgsfield credits) was ported to run natively on this PC without WSL/Ubuntu, 2026-11-12, at the user's request.

- Lane: `C:\Users\Glaresquare1\glare-work\Neuro\llm-longform-win` (keep the path short, Windows 260-char limit, LongPathsEnabled is off). Skill: `C:\Users\Glaresquare1\glare-work\.claude\skills\glare-neuro-llm-longform-win\SKILL.md` (scoped to glare-work, not global). The original pack in Downloads is untouched; its Mac/Ubuntu installers are copied in `_pack_original/`.
- Every Bash call for the lane starts with `source ~/glare-work/Neuro/llm-longform-win/_kit/win/env.sh` (PYTHONUTF8=1, CHROME_BIN). The Windows layer is `_kit/win/` (winkit.py, port_to_windows.py = idempotent re-port, setup.sh, doctor.sh). Details and the test record: `WINDOWS.md`, `WINDOWS-TEST-REPORT.md` in the lane root.
- Never run the doctor, `run_gates.sh` or `winkit.py kill-chrome` while a render runs: they kill the lane's Chrome workers (only profiles `/tmp/chrome-*`).
- Tested 2026-11-12 (record: `WINDOWS-TEST-REPORT.md`): every stage works and matches the Mac files EXCEPT a complete render: a 6-worker render of build 14 on this 15.7 GB PC was stopped at 97% by the low-memory guard and its frames were largely bad (missing photos, fallback fonts; the same frames render right alone in a fresh Chrome). Use `winkit.py workers` (about 2 here), never restart a reaped render without asking, and run `winkit.py verify-frames .` before encoding. A full-video render + encode is still unproven.
- Whisper is replaced by faster-whisper (`winkit.py whisper-json`); Phase 6 screen ENDS can differ up to ~0.9 s from the Mac run, starts agree to hundredths.
- Windows Explorer "Extract All" of the pack dropped 2 images (long paths) and garbled 1 filename; re-extract with 7-Zip/Python if a fresh pack is needed. Two ~150-char image names were shortened in the lane copy.

**Why:** the team PC has no WSL and the user does not want it installed.
**How to apply:** when the user asks for a Neuro LLM long-form video, use the Windows skill/lane, not the pack's WSL path; the ElevenLabs voice clone and key are the user's own to set (never ask for the key in chat); Phase 5 is the only paid step (state the character count, wait for a yes).
