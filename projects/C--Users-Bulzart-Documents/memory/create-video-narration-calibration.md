---
name: create-video-narration-calibration
description: "2026-11-20 paid narration trial chosin-trial-01 (17 takes, 2,051 of the user's 5,000-credit cap): eleven_v4 bills ~0.40 credits/char (character-cost header), context unbilled, balance lags; results wait for the user's ears"
metadata:
  node_type: memory
  type: project
  originSessionId: 043c101b-0b28-4a7f-82ee-6dd10286c87b
  modified: 2026-11-20T15:20:33.916Z
---

User 2026-11-20 authorised up to 5,000 ElevenLabs credits for narration calibration ("a hard maximum, not a spending target"; not for Voice Design or the video's narration). Trial `chosin-trial-01` on run `20261119-045532-youtube` video-01, folder `C:\Users\Bulzart\.claude\static-studio\runs\20261119-045532-youtube\60-voice\video-01\trials\chosin-trial-01\` (plan.json, plan-approved-2026-11-20.json, plan-stage1.json, report.json, `listening\` blind set Q1-Q10 + listening-guide.md, answer-key.md/.json). Budget id `narration-calibration-2026-11-20` registered in `RUN/60-voice/trial-budgets.json`; 2,051 spent, live balance 3,438 after (reset 2026-12-19).

**Measured facts (use them):** eleven_v4 is billed ~0.40 credits per character on this account although GET /v1/models says multiplier 1.0; the `character-cost` reply header IS the credits billed and the balance falls by exactly it ~20-30 s later (an immediate balance read shows 0). `previous_text`/`next_text` were NOT billed (P2-C with 1,141 context chars cost 149 = P2-A). Context slowed delivery 3-5 % in all three passages and left a 0.56 s breath at a part's end (0.12 s without). Stability 0.6 vs 1.0 on this voice: no systematic change at the opening, larger take-to-take variation (repeat pitch range 9.65 vs 10.78 st at 0.6, 9.71 vs 9.82 at 1.0). [softly] made the ending ~1.1 dB quieter and narrower in pitch. The "restrained" ending came out the fastest passage (241 active WPM). Paragraph breaks barely changed it. Chosin: IPA /ˈtʃoʊzɪn/ (CHOH-zin), from the Congressional Record 2012 "play on words between 'chosen' and 'Chosin'" and the nicknames; Whisper heard the IPA take as "Chosen".

**How to apply:** no production setting changes until the user has listened (listening-guide.md first, answer key after). video-01 production is NOT resumed (user's rule); its 4 legacy holds (L051, L147, L289, L320) get a real purpose or are removed when it resumes, never an invented reason. Related: [[create-video-narration-direction]], [[awl-elevenlabs-v4-no-edit]].
