---
name: create-video-captions
description: "/create-video captions (user 2026-11-20): picked once at the start (Luckiest Guy word box | Montserrat Bold yellow active word | none), timed by the narration's own Whisper words; captions.py + captions-* commands; CapCut's own drawing not verified"
metadata:
  node_type: memory
  type: project
  originSessionId: 043c101b-0b28-4a7f-82ee-6dd10286c87b
  modified: 2026-11-20T15:20:24.632Z
---

User 2026-11-20 (master brief Part B, carried into /create-video at the user's say: "we're doing the same captions feature in create-videos too"; see [[one-pipeline-per-session]]). Built in `~/.claude/static-studio`:
- **Choice** asked once in the start dialog, no default: `captions-choice --captions on --style luckiest-guy|montserrat-highlight` or `--captions off`; `state.json` `captions`, `caption_style`, `captions_history` (a change needs `--change "why"`). Older runs are asked once when their edit begins.
- **Looks** (`scripts/captions.py` LOOKS, fonts in `static-studio/fonts/`, checked by PIL name): Luckiest Guy = capitals, white, black outline 0.18, shadow, 3 words a caption, the spoken word on a rounded box (radius 0.3, pad 0.05, v_offset 0.15, gap 0.55 em), box colour per video from its palette (`captions-plan --box-color --box-color-why`); its 7 helper functions are byte-copies of awl.py's word box (a test proves it). Montserrat = Montserrat-Bold.otf, white #FFFFFF, black outline 0.18, no box, NO shadow (the brief said no unrequested effects), one CapCut text per moment holding the whole line, the active word a yellow #FFFF00 range via capcut-cli `import-ass` (`{\c&H00FFFF&}`), bridge 0.12 s, a real pause = all white, every word lit >= 2 frames, line <= 6 words / 80 % width, never across a sentence end or a 0.6 s pause, tail 0.5 s. Size: em 4.6 % of the smaller side (4.5 / 5.49 on 1920x1080), y_rel 0.85 landscape, 0.75 portrait.
- **Timing**: narration-measure now keeps `word_times` per line in line-times.json; `captions-plan` maps the script's display words to them (a number over two words shares its token, a word with no time sits between neighbours, counted as `between`) and adds every retime-shots hold -> `70-edit/video-NN/captions.json`. `captions-build --draft` (CapCut closed) writes tracks `caption-hl` or `caption-box-N-box|word` and reads back; `timeline-check` reads them back from `capcut_draft`; `captions-preview` = PIL PNGs.
- Verified 2026-11-20: 13 caption tests (real capcut-cli builds in a scratch template copy, both looks, portrait, off) and a read-only real-data check on video-01 part 1 (first 90 s, 230 words: highlight 230/230 lit; word box 224 boxed, 6 sub-frame words passed on by the copied rule).
- NOT verified: CapCut's own drawing of either look (no export made), the outline thickness in the PIL preview, a whole run through the command.
