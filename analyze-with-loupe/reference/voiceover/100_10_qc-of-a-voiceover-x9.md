## 10. QC of a voiceover (X9)

- **The soundtrack** (native, lipsync): your reading of `T voiceover align`: the delivered sound is the take (near 1 at near 0), or it was
  laid back (§8). **overlay**: the mix facts (`vo_speech_cut_s` 0, the final has audio).
- **Lips** (native and lipsync, on-camera): `@full` dense ranges around three phrase starts and one pause of at least 0.4 s: the planned
  speaker's mouth opens within about 0.1 s of each phrase start and rests in the pause, and no listener mouths the words. Off: native → the
  sync pass or one regeneration (§8, under the QC-fixes choice); lipsync → one more sync pass, or the fallback.
- **The sync pass did not harm the face** (lipsync, or a native fix): dense frames around the mouth and the jaw at rest and in speech: no
  blur, no smear, no doubled teeth, no seam at the chin, identity unchanged.
- **overlay** and every off-screen form: nobody in the frame speaks.
- **What QC cannot check:** no agent listens, so pronunciation, accent and dialect are never judged: `result.json → voiceover` says
  "pronunciation: not checked (listen)", and a language outside the model's official list is named in the wrap-up.
- A take that cannot fit the picture, or a line that must change, is not re-voiced by the agent: blocker `voiceover` with one line of detail;
  the main session makes the new take (§4) and continues the agent.

