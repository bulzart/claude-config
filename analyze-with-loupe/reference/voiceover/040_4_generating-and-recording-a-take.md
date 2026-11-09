## 4. Generating and recording a take (X1)

1. `T voiceover outdir --run RUN` makes and prints the folder the ElevenLabs MCP may write to (under the server's own
   `ELEVENLABS_MCP_BASE_PATH`, read from `~/.claude.json`, else the Desktop); any other folder answers "not writeable".
2. **One** `mcp__elevenlabs__text_to_speech` call per script version: `text` (the script file's text), `voice_id` (§5), `model_id`
   (`voiceover.model_id`), `language` (`voiceover.language`), `stability` and `similarity_boost` from `voiceover.settings` (Eleven v4 has no speed, style or
   speaker boost: the delivery and the pace are the script's audio tags), `output_format` (`voiceover.output_format`), `output_directory` (the outdir). It spends ElevenLabs credits: never a
   test call, never the same script twice.
3. `T voiceover record --run RUN --video NN --attempt K --file "<the saved file>" --script RUN/40-briefs/video-NN-voiceover.txt --voice-id <id> --voice-name "<name>" --model <id> --language <iso> --preference "<words>" --mode on-camera`
   (or `--mode off-screen`; add `--settings '<the JSON sent>'`). The saved file is the path the MCP's answer names: it ends at the file's
   extension, and its name may hold brackets, so quote it. The command copies the take into the run, measures it and writes its sidecar and
   `state.json → voiceover.files`: `duration_s`, `speech_start_s`, `speech_end_s`, `phrases` (the spans of speech between pauses), `pauses`,
   `integrated_lufs`, `spoken_text` (the words without tags), `spoken_words`, `words_per_speech_s`. Numbers and facts: the fit is yours.
4. **The fit.** The take's speech ends at least 0.3 s before the planned end and keeps to the method's limits (native: 15 s per generation;
   §6). A take that is over is taken again (attempt 2) with fewer words or a quicker delivery tag ("[quickly]", "[brisk pace]"): the take
   is an ElevenLabs generation and is never edited (the user, 2026-11-09: "do not edit the delivered generation without any exception":
   no tempo, cut, trim, gain or fade; `T voiceover mix` refuses a gain, a negative offset and speech past the picture's end, §8); native
   and lipsync take the take as it is, so it must fit as voiced. At most two takes per script; a third is the user's call (report it). The
   planned length grows only as far as the beats need, and never past 30 s without the permission of A7b.
5. **Re-time the plan to the take.** Beats sit on the measured phrases (a phrase start is a beat start; a pause is where a cut, an insert's
   split point or a product beat can land). The generation's duration, in the model's whole seconds: **native** the take's whole length rounded up (a driving audio is
   cut at the duration, and a shorter one leaves the rest silent); **lipsync** at least the take's whole length (the sync pass pads the voice,
   never the picture); **overlay** the speech end plus 0.3 to 0.6 s. The QC checkpoints add dense ranges at three phrase starts and one pause.
6. **Multi-clip:** one take per clip, cut at a pause of the script, each recorded with `--video NN-cK` (its sync pass, lipsync: `NN-cK-sync`).
7. **Source `file`:** no ElevenLabs call. `T voiceover record --source file --file "<the user's file>" --script <their text>` (or
   `--transcribe --language <iso>` without a script) per video, then steps 4–6. A file is never re-voiced: one that does not fit is reported
   and the plan adapts its length. A file over several clips: record it whole once (`--video NN`, for its pauses), then each clip's part
   with `--video NN-cK --span <start>-<end>`, cut in a pause (a lossless WAV take, measured from the cut).
8. A failed call (the quota, a voice not found, the MCP down) is a blocker: report the real error. Never fall back to the model's own voice
   silently.

