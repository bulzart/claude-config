---
name: create-clips-speaker-facts
description: "/create-clips \"who speaks\" facts (2026-11-20): [sub] marks = transcript words matching the on-screen subtitle (OCR), voices.json per chunk, T voices; voice/music/laughter classifiers tested and NOT shipped"
metadata:
  node_type: memory
  type: project
  originSessionId: 046004a5-1b5b-492c-a227-505bb55d8234
  modified: 2026-11-20T15:43:00.793Z
---

User 2026-11-20 spec "Audio Understanding and Entertainment Intelligence": give agents trustworthy evidence of who speaks / music / vocal events, validated, never deciding.

**Shipped (cc_voices.py, encrypted like the others; .gitignore lists cc_voices.py):** one ffmpeg pass decodes the bottom band (y 0.70-0.98, x 0.10-0.90, scaled to 1536 wide) at 2 fps; centred text lines found from bright strokes beside a dark outline; RapidOCR RECOGNITION only on those strips (~0.1 s a line; the full detector was 0.9 s/frame = too slow); identical strips not re-read; each subtitle line matched ONCE to the nearest transcript words (>=2 tokens, >=50 %), inner substitutions join, EDGE substitutions join only if they look alike (ratio >= 0.5); a strip is split at gaps > 3 line heights and only centred parts are read (a button prompt like INTERRUPT on the subtitle's rows dropped Charles's line at 10678); OCR words run together ('okaygotta') are split into two known transcript words — the caseoh case "He's scamming you!" spoken over mom's "Mira, I sold..." must stay unattributed. Labels per word: S on-screen subtitle, o other text on screen (says nothing about who), . none. transcript.txt marks S runs `[sub]` with a header (unmarked file byte-identical); `T words` shows [sub]...[/sub]; `T window` too; reporter gets voices.json (quote subtitles from it, never from the transcript); report signature ignores the marks (voices.json keeps `unmarked_transcript_txt_size`). Processor runs it after the transcript (config voices.enabled; not a STAGE, never fails a chunk); `T voices --run RUN` backfills (FileLock per chunk, parallel 2). EDL `captions.skip` rec spans (lyrics/background voices only, never the streamer). Docs: moment-mining "Who speaks", cc-start/cc-scan/cc-plan/builds, edit-craft (y_rel ~0.76 when game subtitles at ~0.87-0.90: long-video captions at 0.88 sat ON GTA subtitles in CapCut).

**Validated on caseoh:** blind frame check of 45 lines: S 15/15 correct, '.' 14-15/15 no text; ~14-24 s/chunk CPU (8 h ~ 40-60 min). Agents' moments: facts agreed with every checked attribution (they inferred from context); no selection would have changed on caseoh. "Jack, why..." (C0014) not subtitled while neighbours are -> consistent with "Chat, why"; "Jack of Hearts" was a subtitled game line (lexicon guard BUILT 2026-11-20: scope "streamer" entries skip words printed in the game's subtitle, [[create-clips-lexicon-scope]]).

**Not shipped, why:** voice-only (MFCC+pitch logistic) AUC 0.87-0.95 but uncalibrated (7/45 or 29/39 wrong at 0.5); music cues (HPSS, chroma stability, beat, stereo side) separate only loosely, Silero calls singing speech; laughter invisible in transcripts (11 "ha" in 5 h). Listening pack for the user's labels: C:\Users\Bulzart\Documents\stream-clips\validation\audio-20261120 (16 clips + labels.csv). Next step proposed: small ONNX audio tagger + speaker embedding, scored on those labels.

Too-short ad fragments (< 1/fps s) are skipped, not failed (`too_short` in the answer). Pre-existing (not ours): test_proc fails 'A: cells carry loudness and chat numbers' and 'A: audio.json windows' (63/65) on the unchanged live code too.

Related: [[create-clips-caption-look]], [[scripts-gather-agents-decide]], [[create-clips-chat-heat]], [[pipeline-source-encryption]]
