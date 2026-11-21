---
name: create-video-held-silences
description: "/create-video held silences (user brief 2026-11-21): whole-silence proposals decided on the recorded voice and again with the picture; no quota, formula, reference-copy or padding; holds / hold-decide"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 48644031-73ae-4535-b1ee-b68bd3d3def6
  modified: 2026-11-21T21:12:50.048Z
---

User 2026-11-21 (long brief, Garbo run as the diagnostic): "Silence is a creative tool, not a default editing ingredient." Fix the reusable workflow, never one video; no quota, no universal maximum, no formula (not a pause per reveal/joke/ending, not lengths that grow through the film, not a reference's pause as a target), never silence to reach the length; some videos get no holds. Natural narration is the baseline: count the voice's own gap once, never on top.

**Built (static-studio, 2026-11-21):** script lines plan `pause_total_s` (the WHOLE silence, voice gap included) + `pause_via` (edit | tag, never both) + `pause_purpose`/`pause_picture`/`pause_sound` (plan-check requires all three). The older `pause_after_s` is still read as written (added on top) so old runs resume; warned. narration-measure reads each line's real gap from the audio (`gap_after_s`; quiet = 35 dB under the 90th-percentile frame, calibrated on a real part: Whisper's line ends are off by up to 0.2 s). `holds` (+ `--preview Lnnn --totals a,b`: local wav/mp4 previews for the user's ears) and `hold-decide --stage narration|picture --total S | --no-hold --reason` write 40-plans/video-NN/holds.json (history kept; a decision goes stale when its part is re-recorded or its still changes). retime-shots inserts ONLY decided holds, adds total minus the measured gap inside the real silence, verifies narration-edit.wav with the same measure (0.06 s), skips seam holds at held lines, refuses when silence reaches the export window. timeline-check needs every hold decided with its picture and the edit plan timed from the decisions in force. The script packet shows the whole silence with picture and sound and no reference pause length; the final packet lists the held silences (where, how long, the words around) without the director's reasons. Decisions never re-open the script read (a text reader can't judge 1.2 s against 2.5 s).

**Why:** the Garbo audit found the old `pause_after_s` defined as "the silence wanted" in manual 03 but inserted ON TOP of the voice's gap (2.5 s planned = 3.1 s heard); holds inserted mechanically from pre-voice guesses; reasons anchored to a reference narrator's pauses (the packet even showed "the comparable narrators' longest pause is about 8.6 s"); a 2.5/3.0/3.5/4.0 escalation no check noticed.

**How to apply:** keep this when editing static-studio; code gathers, checks process and measures; the length is the director's call, decided on evidence (the user's listening where offered). Related: [[create-video-narration-direction]], [[create-video-adaptive-niche-guardrail]], [[scripts-gather-agents-decide]], [[awl-elevenlabs-v4-no-edit]].
