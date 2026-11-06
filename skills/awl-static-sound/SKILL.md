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

- static §6: `AWL/reference/static/060_6_the-voice-and-the-bed-a6s-s2.md` (6.1 KB)
- static §8: `AWL/reference/static/080_8_static-qc-s2-s4.md` (2.7 KB)

The main session runs S2 for every video, one at a time (one model on the GPU; the toolkit's lock holds a second one back), before any
production agent starts (`awl-analyze-produce` A9s).

## Step S2 (per video)

1. `T tts say --run RUN --video NN` → `RUN/30-assets/narration/video-NN.wav`, its sidecar (each line's start and end) and the loudness
   (the voice chain and two loudnorm passes bring the file to the target: it is what the CapCut project plays). Without `--only` it
   makes every line; `--only N` makes those lines again; `--rejoin` makes none and only joins the line files again (the timing stays).
   **Strong lines** (static §4, §6): read `voice_match`; a strong line apart from the cloned lines' numbers is made again with another seed
   (the line's `seed` in `video-NN-narration.json`, then `--only N`), at most twice, then as a cloned line (`strong` false), noted.
2. `T narration-words --run RUN --video NN` → the timed words, `video-NN.cues.json`, `video-NN.srt` (as many words at once as the image
   plan's `captions.words`; a word that would be on screen under `captions.min_cue_s`, 0.2 s, takes the next word with it; no cue
   overlaps the next), and per line what was heard against the script; numbers are compared apart (speech-to-text writes a spoken
   "seventeen sixty-nine" as "1769"): each line's `numbers` gives the script's and the heard ones to compare by ear. Judge every line it
   lists (`lines_to_check`) from its missing, extra and repeated words and its numbers: a wrong line is made again
   with `T tts say --run RUN --video NN --only N`, then `narration-words` again; at most twice per line, then it stays and the brief notes it
   (local and free; with QC fixes `off` nothing is made again).
3. **Length and pace:** the duration against the spec's range; a quarter or more outside it: shorten or extend lines of the script and
   `video-NN-narration.json` (static §4), then make those lines again.
4. **The images meet the narration:** each image spans from its `from_line`'s start to the next image's (the first from 0, the last to the
   end with the tail). Keep every span within the spec's range of seconds per still and none under about 2 s: move `from_line`, merge or
   split images in `video-NN-images.json` (their prompts with them).
5. **The bed** (every video, static §6; `RUN/40-briefs/music.json` from A6s), after every narration is made: each track's `duration` =
   lead + the narration's duration + tail (config `static.narration`), then `T music make --run RUN` (every track in one model load).
   Then per video `T music measure --run RUN --video NN`, judged as static §6 and §8 say: a voice heard in the bed alone, or an arc that
   fights the story's beats → a new take (another `seed` or a reworded `caption` in music.json, `T music make --run RUN --video NN`, then
   measure again), at most two, by the run's QC fixes (off: none, noted); a narration word heard differently with the bed under it, or a
   bed lost in the pauses → another level with `--gain G`, kept as the image plan's `music_gain`. A bed that failed: that video goes on
   without one, noted; a bed is never a blocker.
6. The video's brief (`RUN/40-briefs/video-NN-brief.md`, block S2): the voice, the narration's length, the lines made again and why, the
   bed (its caption and why, the take, the level and the facts the level rests on) or why there is none.

A worker error is reported with its real text. Narration failing for every video is a blocker of the run (`T static check` gives the
facts of the setup, static §9).

## Never (this phase)

- Never change the run's voice between videos or make a line in another voice (a strong line is the run's voice description by the
  design model, static §6).
- Never call ElevenLabs or Higgsfield for a Static voice or bed.
- Never stretch or speed a narration to fit a length: rewrite the lines.
- Never analyse the references' music beyond the numbers A3 already has (the user, 2026-11-06: "no need to analyze their instrumentals
  too"); never keep a bed's level at which a narration word is heard differently (a level costs nothing to change, whatever the QC fixes).

## Hand-off

Return to A9s in `awl-analyze-produce`.
