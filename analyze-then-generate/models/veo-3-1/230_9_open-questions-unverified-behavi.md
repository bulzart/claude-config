## 9. Open questions / unverified behaviour

- **Output dimensions.** What `veo3_1` `quality` `basic`/`high`/`ultra` deliver (720p/1080p/4k expected, unconfirmed), and whether `variant` changes resolution. Whether `basic` + 9:16 yields exactly 720×1280, and what Lite delivers (720×1280 expected). No Higgsfield source states these.
- **Backend.** Which backend Higgsfield calls: Gemini API preview ids (shutdown 2026-10-22) or Agent Platform GA ids.
- **4k on Fast.** Whether `ultra` works with `veo-3-1-fast`; Google's two doc sets conflict.
- **Lite audio switch.** How `generate_audio: false` is implemented on Lite, and whether lips still move when dialogue is written with audio off.
- **Blocked jobs.** Whether Higgsfield bills Google-side safety or audio blocks.
- **Colon dialogue.** How much it reduces subtitle artifacts on Veo 3.1; no rates are published.
- **Timestamps.** Reliability beyond four segments or with segments under 2 s.
