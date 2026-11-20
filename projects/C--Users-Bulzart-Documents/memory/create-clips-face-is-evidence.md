---
name: create-clips-face-is-evidence
description: "/create-clips: a laugh is almost never in the transcript; \"no reaction from him\" must be checked on the face cam (3 of 3 checked hid a laugh), T sheet --crop"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 046004a5-1b5b-492c-a227-505bb55d8234
  modified: 2026-11-20T17:18:48.926Z
---

Before an agent writes "no reaction" (a heat_review line, a dropped game-line moment), it looks at the streamer's face over the beat with a face-cam strip: `T sheet --run RUN --from <onset-6> --to <peak+10> --step 0.5 --crop x,y,w,h` (face cam region as fractions; caseoh 0,0.1,0.21,0.3, xqc 0,0.435,0.21,0.3). heat_review carries `face` (laughs|reacts|still|off-camera|no face cam). The game's line + his laugh is a moment (setup + payoff), same bar.

**Why:** 2026-11-20 evaluation: caseoh H013 (booty buffet) and H054 (Boobie's walkthrough) and xqc H003 (talk-radio vaccines) were set aside as "no reaction from him" while the face cam shows him doubling over laughing; Whisper transcribes laughter almost never (11 "ha" in 5 h). Reports describe 240x135 cells: too small for a face.

**How to apply:** mining, the second look and the planner's checks read the face for reactions; never infer "no reaction" from words. Related: [[create-clips-second-look]], [[verify-cited-examples-before-rules]]
