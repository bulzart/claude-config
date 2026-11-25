---
name: create-video-pacing-from-narrators
description: "user 2026-11-25, every /create-video run: pace weighed from the reference narrators who match (decision.pacing, planning rules 4); narrator chosen on quality; length and voice never force each other"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 3cb802e3-203e-41d6-98ff-b19f9a9a5679
  modified: 2026-11-25T02:55:33.252Z
---

The user's brief "Correct Reference-Derived Narration Pacing" (2026-11-25), for every /create-video run in every niche:

- The intended pace comes from the reference narrators who genuinely match this film, each weighed with its reason:
  narrator personality and delivery, format, information density, how familiar and complex its terms are, sentence
  structure, emotional course, natural variation, pace while speaking against overall pace, pauses and what the
  audience must catch. Recorded in direction.json `decision.pacing` (`references[{ref, relevant, why}]`, `range`, and
  `uncertainty` when only one matches). Several where several match; never an arithmetic average or a numeric score.
  One alone is allowed with its uncertainty stated; never manufacture a second match.
- A measured voice from another production is technical history, never evidence for a new film's pace.
- The narrator is chosen on creative quality (personality, charisma, naturalness, emotional range, clarity, both the
  personal letters and the explanation), never rejected for a pace that differs from the forecast. Its pace never
  silently overrides an approved length either. Real pace is judged on real parts (variation, pauses, delivery,
  the whole script), not one short sample; a true mismatch is diagnosed (voice, script density, delivery or length)
  and any length change goes to the user. Nothing re-locks automatically.

**Why:** the Qin run's 16:30 re-lock took its pace from V007 alone and cited the earlier production's George
(164 wpm) as support; the user asked for that to be verified, then corrected workflow-wide.

**How to apply:** code is PLANNING_RULES 4 (`pacing_decision_issues`; locks stamped earlier see it as advisories);
plan-check reports `pacing` (each reference's measured profile, the script's own density, the relevant range, the
forecast across it, `voice_pace_that_fits_the_lock_wpm`) and warns, never blocks. Manuals 03 ("The narrators this
narration follows", "Narrator and length"), 05, 07, 10 §3. Related: [[create-video-storytelling]],
[[create-video-narration-direction]], [[wpm-calibrate-from-transcripts]], [[create-video-older-directions-advisory]].
