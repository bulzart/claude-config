---
name: awl-static-whole-set-and-pace
description: "user 2026-11-08: Static reads the references as ONE set (no single reference as the template; data drives, no prefixed values) and every narration must provably hit the set's measured pace (model's own speed setting first, a post tempo only for the rest)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 6df6fb40-e7ad-4b91-b765-6c6c020da849
  modified: 2026-11-08T09:19:46.429Z
---

User 2026-11-08: "the narration speed and style should mirror the reference's data patterns, if the data tells that the best speed is 160 words with pauses and 178-191 while speaking per minute then thats what we should use too, no matter if we cant set the speaking speed of the generating voice we can still speed it up after generation ... we have to be very sure that the workflow really achieves a 178-191 words a minute. Also the reference datas should be studied as a whole not just pick one of them to "copy" ... what worked, hooks, emotions, patterns, length, voice speed, visuals, editing, engagement, mental attachment, social strategy, why it got the viewer hooked, content style, and everything ... the data is what should drive the video generation not fixated or constrained terms or prefixed values". Then: "if qwen 3.1 plus for example has the speed feature or word per minute then set it up in the model, only do manual tweaks if the model does not provied with what we want to achieve".

**Why:** video 02 (Airbnb) came out at 125 words a minute overall / 152 while speaking (pauses 0.83 s median) by the references' own yardstick, against the set's 160-174 / 178-196 (0.42-0.5 s); its own lines paced by the new step measured 164 / 190 (pauses 0.5 s): nothing set or checked the speed, and its plan cited "V02's template" and "V01's moves".

**How to apply:** `T static profile` before the spec; the spec is the whole set's (counts, medians, families read apart; the user's A5 style pick sets the look only); every narration JSON has `pace` (wpm_speech, wpm_overall bands from the set) and `pause_default_s`; `T tts say` paces it (Alibaba `rate` first, rubberband tempo only for the remainder or for local Qwen3-TTS) and measures with faster-whisper like A1; `pace.within` must be true before a narration ships. Static §1, §2, §4, §6. Related: [[analyze-with-loupe-command]], [[scripts-gather-agents-decide]].
