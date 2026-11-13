---
name: awl-static-sound
description: /analyze-with-loupe Static step S2: each video's narration in the run's voice, its timed words and checks, the image spans, and the bed when planned. Internal to that command.
user-invocable: false
---

# awl-static-sound — Static step S2: narration and bed (main session)

> `AWL` = `C:/Users/Bulzart/.claude/analyze-with-loupe` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$AWL/scripts/awl.py"` (every call prints one JSON object on its last line; run through Bash) · `RUN` = the run folder `AWL/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `AWL/reference/<file>/` (models: `AWL/models/<guide>/`, Higgsfield: `AWL/higgsfield/higgsfield-mcp/`); `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- static §6: `AWL/reference/static/060_6_the-voice-and-the-bed-a6s-s2.md` (30.5 KB)
- static §8: `AWL/reference/static/080_8_static-qc-s2-s4.md` (9.7 KB)
- static §13: `AWL/reference/static/130_13_evaluating-the-work.md` (15.8 KB)

The main session runs S2 for every video, one at a time, before any production agent starts (`awl-analyze-produce` A9s). The narration
is ElevenLabs' in the run's voice (`state.json → static.voice`) and the run's narration model (`state.json → static.tts_model`: Eleven v4
unless the user picked another, static §6 "The models"), in each video's own language (`state.json → static.video_info`, static §6
"The language of a video"): nothing of it runs on this PC, every passage is billed at the model's credits a character (one on Eleven v4),
and the delivered audio is not edited (the user, 2026-11-09: "do not edit the delivered generation
without any exception") but for the two exceptions the user then allowed (static §6 "The rule"): one gain only when its loudness sits
outside the references', and a capped speed-up made only on the user's yes after they have seen the delivered project.

## Step S2 (per video)

1. `T tts say --run RUN --video NN` (add `--fill` when the characters may not cover the script: the last passage is then made from the
   whole lines that still fit; `--budget N` caps the call) → `RUN/30-assets/narration/video-NN.wav` (the passages end to end exactly as
   delivered), its sidecar (each line's start and end, each passage's request, the loudness as read) and the passages in
   `RUN/30-assets/narration/video-NN/`. It makes only the passages not yet made with their present text; a passage-1 probe made exactly
   as `say` would make it is used as passage 1 (nothing paid twice); `--only N` makes again the passages holding those lines, `--again`
   all of them, `--rejoin` none. The requests are the run's model's: `T tts say` refuses a tag, a setting or a pace key the model's
   record says it lacks before anything is billed. **A language the model does not list** (`official: false` in `T static language`,
   or a model or language with no measured point yet): the first passage is made as a probe (`T tts probe --run RUN --video NN`, billed
   for that passage only, which `say` then keeps as passage 1), read by `T narration-words` against its script, and the rest is made
   only when the heard words match; a text the model cannot speak is a blocker reported with the numbers (the user picks another
   language or model), never asked mid-run. **The pace** (static §6 "The pace", §13): the narration JSON's `pace` carries the point you chose (static §13, before any generation; in the
   language's own unit, `T static units`) and
   its levers (the voice, `delivery`, `voice_settings`, the words) were measured on the probe; the answer's `pace.on_target` and
   `pace.within` are the facts for your check in step 4b: a narration off its point is never shipped unexplained. The answer's `level` is the
   loudness rule's (static §6: as delivered inside the references' range, else one gain toward their median within -1 dBTP). A partial
   narration (`partial`: the characters ran out) is named in the brief and the wrap-up; the timeline leaves out the images after it.
   Run it in the foreground; it may run past ten minutes and continue in the background on its own, which is fine once started.
   **Passages** (static §6): read `voice_match`; a passage whose timbre sits far from the others (`passages_below`) is made again
   (`--only <one of its lines>`, billed), at most twice, by the run's QC fixes, noted.
2. `T narration-words --run RUN --video NN` (its `pace` is the second reading of the pace, against the same bands; it reads the speech in the
   video's language, with that language's own Whisper code) → the timed words, `video-NN.cues.json`, `video-NN.srt` (as many words at once as the image
   plan's `captions.words`, or `captions.chars` characters for a language written without spaces; a word that would be on screen under `captions.min_cue_s`, 0.2 s, takes the next word with it; no cue
   overlaps the next), and per line what was heard against the script; numbers are compared apart in English (speech-to-text writes a
   spoken "seventeen sixty-nine" as "1769"): each line's `numbers` gives the script's and the heard ones to compare by ear (in another
   language `numbers.compared` is false: its spoken numbers are read from the heard text itself). Judge every line it
   lists (`lines_to_check`) from its missing, extra and repeated words and its numbers: a wrong line (a missing or repeated word, a tag
   spoken aloud, another speaker) is made again with its passage: `T tts say --run RUN --video NN --only N` (billed: the passage's
   characters), then `narration-words` again; at most twice per line, then it stays and the brief notes it (with QC fixes `off` nothing
   is made again). A `tts say` that stopped part way (no answer, or the characters ran out) keeps what was made: `T tts say` again makes
   only the missing passages.
3. **Length and pace:** the duration against the video's own target (`target_length_s` in `video-NN-narration.json`: the user's pick at A5 or, for the standard, the agent's from the
   references' pattern, static §4); more than about a tenth off it: shorten or extend lines of the script and
   `video-NN-narration.json` (static §4), then make those passages again (billed; never an edit of the audio).
4. **The images meet the narration:** each image spans from its `from_line`'s start to the next image's (the first from 0, the last to the
   end with the tail). Keep every span within the spec's range of seconds per still and none under about 2 s: move `from_line`, merge or
   split images in `video-NN-images.json` (their prompts with them).
4b. **Check the narration yourself, skeptically** (static §13 "After the narration"): read the narration's measured pace, pauses, length
   and spans against your forecast and the point and settle: spans by `from_line` (free); a miss of the point changed through the request
   first (another delivery tag, pause tag, setting or wording, the passages made again, billed, by the run's QC fixes); what the
   request levers cannot reach is kept as delivered with its reason, and you write the speed-up that would close it (at most config
   `static.narration.tempo_max` 1.05) for the wrap-up to offer: never made here (the user, 2026-11-09: "only speedup on their
   permission never else"). On the user's later yes, after they have looked at the delivered project: `T tts tempo --run RUN --video NN
   --tempo X --why "<the levers tried and their measures>" --user-ok "<the user's words>"` (pitch and formants kept; the level rule read
   again on the sped file, its answer's `level`), then `T narration-words`, the spans, the bed's length and the project again.
   Then `T tts fit --run RUN --video NN` (after `narration-words`): the voice's point learned again
   (`state.json → static.voice.fit`), what the next video's forecast reads.
5. **The bed** (every video, static §6; `RUN/40-briefs/music.json` from A6s), after every narration is made, when every image is made
   or in a gap between image stretches (two local models never share the GPU and the commit memory; 2026-11-08 the guard stopped
   ACE-Step at 2.0 GB free commit; since 2026-11-09 it loads the low-commit way, the answer's `loading`, and needs about 13.6 GB free
   commit, static §9 "What a job needs"): first your check before the bed (static §13): `T static forecast --run RUN --video NN --part music` right before, its
   memory headroom a fact and never a gate (static §13 "Memory is a fact"): the bed is tried at full precision; after a real guard
   stop (the answer's `worker.guard_stopped` and `worker.guard_line`) the user is told its line and the bed is tried once in
   ACE-Step's int8 (below), once more before the edit when that is stopped too, and still stopped the video goes on without a bed,
   noted (nothing of the user's is closed, the guard is never changed). Each track's `duration` =
   lead + the narration's duration + tail (config `static.narration`), then `T music make --run RUN` (full precision first, always;
   `--quantization int8_weight_only`, ACE-Step's own int8, only after the guard stopped that try: the user, 2026-11-09, "always try
   full precision first, and use int8 only after the guard stops it", never from the forecast alone; its answer's `int8_after`
   names the stopped try; static §6; every track in one model load; a
   track over ACE-Step's 600 s is made in sections and joined with crossfades, static §6: the plan's own `sections` per part of the
   story, else equal ones).
   Then per video `T music measure --run RUN --video NN`, judged as static §6 and §8 say: a voice heard in the bed alone, or an arc that
   fights the story's beats → a new take (another `seed` or a reworded `caption` in music.json, `T music make --run RUN --video NN`, then
   measure again), at most two, by the run's QC fixes (off: none, noted); a narration word heard differently with the bed under it, or a
   bed lost in the pauses → another level with `--gain G`, kept as the image plan's `music_gain`. A bed that failed: that video goes on
   without one, noted; a bed is never a blocker.
6. The video's brief (`RUN/40-briefs/video-NN-brief.md`, block S2): the voice, the narration's length and characters, the passages made again and why, a partial narration, the
   bed (its caption and why, the take, the level and the facts the level rests on) or why there is none.

An ElevenLabs error is reported with its real text (the key never shown). Narration failing for every video is a blocker of the run
(`T tts check` gives the facts of the setup, static §9).

## Never (this phase)

- Never change the run's voice between videos or make a passage in another voice (a strong line is the run's voice with its own
  delivery tags, static §6).
- Never call ElevenLabs for a Static narration except through `T tts` (never the ElevenLabs MCP or connector for it: the MCP's
  `list_models` is only the read of the live model and language lists, static §6), never Higgsfield, and never print, echo or write
  `ELEVEN_API_KEY` or `ELEVENLABS_API_KEY`.
- Never change the run's narration model between videos of a run on the agent's own call: the model is the run's (the user's pick at the
  start, or at a clone), like the voice.
- Never edit the delivered narration (the user, 2026-11-09): no stretch, trim, cut, compressor, loudness pass, fade or added silence.
  Its pace, pauses and length come from the request (the voice, the settings, the words, the audio tags; static §6); a length that is
  off is a script rewritten and its passages made again. The only two changes allowed (the user, 2026-11-09) are the level rule's one
  gain (outside the references' loudness only) and a capped speed-up (`T tts tempo`, pitch kept) made only on the user's own yes
  after they have looked at the delivered project, never on the agent's or a reviewer's call (the user, 2026-11-09: "only speedup on
  their permission never else").
- Never analyse the references' music beyond the numbers A3 already has (the user, 2026-11-06: "no need to analyze their instrumentals
  too"); never keep a bed's level at which a narration word is heard differently (a level costs nothing to change, whatever the QC fixes).

## Hand-off

Return to A9s in `awl-analyze-produce`.
