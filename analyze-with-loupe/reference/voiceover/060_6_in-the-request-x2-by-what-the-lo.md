## 6. In the request (X2), by what the locked model takes

Read the locked model's guide §2.2 (its audio role and limits), §3.7 and §3.9 (its reference and dialogue syntax). The model is never
switched for the voiceover: the method was chosen with it.

| method | the request |
|---|---|
| **native**, Wan 3.0 / Wan 3.0 Prime (reference mode; never with `start_image`, the guide's §2.5) | `image_references`: the character (Image 1) and the product views, each bound by purpose; `audio_references`: the take (Audio 1, the first audio entry, ≤15 s); the prompt says the take is the whole soundtrack ("The audio of the video consists entirely of Audio 1, <the speaker>'s voice, with no other dialogue or music"); on-camera: "<Label A> speaks Audio 1 to the camera, lip-synced to it", the mouth, the gestures and the delivery per phrase on the take's phrase times, the words carried by the audio, not re-written as dialogue [INFERRED from the guides of Wan 2.7 §3.7, §3.9 and Wan 3.0 §1, §2.5]; off-screen: "Audio 1 is an off-screen voice; nobody in the frame speaks; the actions follow its rhythm"; native audio on (`generate_audio: true`) |
| **native**, Wan 2.7 (`start_image` + one audio) | the start frame shows the speaker with the product at t=0 (built in X3, a paid image call); the take as the one `audio_references` entry; the prompt as above: who voices the audio and what else may be heard (the guide's §3.7) |
| **lipsync**, the first generation | the speaking scene in the model's own structure: the speaker performs the take's `spoken_text` word for word in the guide's dialogue syntax (Seedance: language + accent + delivery + speaker + {words}, listeners' mouths closed; Wan: `Image 1 says: "…"`), so the mouth moves on those words; with an `audio_references` role the take rides too, as the voice reference (timbre, pace, emotion); native audio on; the duration at least the take's length |
| **lipsync**, the sync pass | `{"model":"sync_so","medias":[{"role":"input_video","value":"<the accepted clip's job id>"},{"role":"input_audio","value":"<the take's media id>"}],"sync_mode":"silence"}` in `50-requests/video-NN-sync-request.json` (`silence` pads the voice to the clip's length; the other modes loop, bounce, cut or retime the picture) |
| **overlay** | no dialogue: the guide's no-dialogue line ("no dialogue, mouths naturally closed, no narration; only the specified ambience and action sounds"); no audio reference; native audio on for the ambience, or off where the guide's mute is cleaner |

- **The duration** (§4 step 5), in the model's whole seconds: native the take's whole length rounded up (at most 15 s per generation);
  lipsync at least the take's length; overlay the speech end plus 0.3 to 0.6 s.
- Written dialogue wins over an audio reference in Seedance and Wan, so in **lipsync** it is the take's `spoken_text` exactly, in the take's
  language, never a translation or a paraphrase.
- Unverified on Higgsfield as of 2026-10-26: how faithfully a driving audio is kept as the soundtrack and followed by the lips (both Wan guides
  list exact lip sync as a weakness), and whether `sync_so` keeps 720×1280 and the take as its soundtrack. The pilot video (item 26) shows it,
  and X8 measures it for every video (§8).
- Music stays out of the generation as always (`capcut-assembly.md` §3b): the soundtrack is placed in CapCut.

