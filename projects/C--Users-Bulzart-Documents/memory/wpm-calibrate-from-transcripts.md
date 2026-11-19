---
name: wpm-calibrate-from-transcripts
description: "Before setting pace_wpm in a script, always measure actual WPM from the reference transcripts in that niche cluster — never use a default estimate"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 043c101b-0b28-4a7f-82ee-6dd10286c87b
  modified: 2026-11-19T11:43:03.098Z
---

Before setting `pace_wpm` in `script.json`, compute actual WPM from the run's transcripts:

```powershell
$words = (wc -w < "10-media/V###/transcript.txt")
$wpm = $words / ($duration_s / 60)
```

Do this for all references in the chosen niche cluster, then average them.

**Why:** 143 WPM was used as a default for a pov-military-narrative video; the actual reference narrators (V017, V018) both speak at exactly 198 WPM. Using 143 WPM would have produced a script ~1,100 words short of the target.

**How to apply:** At the `pace_wpm` planning step in script.json, run the transcript word count / duration calculation for the niche's reference cluster before writing the script. Set `pace_wpm` to the cluster average or slightly below (to allow for ElevenLabs being slightly slower than the original narrators). Write the script to the corrected word budget.

Measurement is cheap (one PowerShell loop); skipping it causes a large structural error in the script.
