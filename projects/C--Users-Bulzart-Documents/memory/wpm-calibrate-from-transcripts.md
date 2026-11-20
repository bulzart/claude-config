---
name: wpm-calibrate-from-transcripts
description: "Before setting pace_wpm in a script, always measure actual WPM from the reference transcripts in that niche cluster — never use a default estimate"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 043c101b-0b28-4a7f-82ee-6dd10286c87b
  modified: 2026-11-19T11:48:56.692Z
---

Before setting `pace_wpm` in `script.json`, let the pipeline compute it from reference transcripts. The `length` command (`static_core.py length`) now does this automatically: it reads each ref's `10-media/V###/transcript.txt`, strips `[0.0-2.4]` timestamp prefixes, counts spoken words, divides by duration, averages across refs, and writes `pace_wpm` + `per_ref_wpm` + `target_words` into `length-lock.json`.

Do **not** pass `--pace-wpm` manually or use a default estimate.

**Why:** A session used `--pace-wpm 143` (the §03 example, since deleted) for a pov-military-narrative video. The actual measured pace is 178 WPM. Using 143 produces a script ~700 words short of target. A second mistake: an earlier manual calculation using `wc -w` over Whisper `[start-end] text` transcripts gave 198 WPM — inflated because `wc -w` treats each timestamp as a word. After stripping timestamps the correct value is 178 WPM.

**How to apply:** Run `length` without `--pace-wpm` and read `target_words` from the lock output. Write the script to that word count. The pipeline's `plan-check` enforces the ±8% tolerance; fix story substance, not filler.

**Niche WPM reference (measured with timestamp-stripped transcripts):**
- pov-military-narrative: 178 (V017=178, V018=179)
- Other niches will auto-compute when their `length` command runs.

Index line before the 2026-11-20 compaction of MEMORY.md (kept here so nothing is lost): before pace_wpm in script.json, compute word_count/duration for each niche cluster's refs; default estimates are dangerously low (143 vs actual 198 for pov-military-narrative)
