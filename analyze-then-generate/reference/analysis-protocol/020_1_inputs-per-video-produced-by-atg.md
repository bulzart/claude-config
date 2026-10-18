## 1. Inputs per video (produced by `atg.py prep-all`)

| file | what it gives |
|---|---|
| `10-media/<V>/video.md` | Specs, sampling summary, shot table, transcript, OCR spans, sheet list |
| `10-media/<V>/timeline.md` | One row per second: shot, cuts, motion peaks, static stretches, words spoken, loudness, on-screen text |
| `10-media/<V>/sheets/storyboard-NN.jpg` | The video at **~5 frames per second**, in order. White labels are the baseline; cyan `+` labels are densified frames (cut boundaries, motion peaks, first second); a red bar marks the first frame after a cut; grey cells mark thinned static stretches (≥ 1 fps kept) |
| `frames.json`, `cuts.json`, `activity.json`, `audio.json`, `transcript.json`, `ocr.json` | Machine data for exact look-ups |
| `20-analysis/audio-context.md` (and `.json`, from `T audio-context --profile`) | The audio of every reference in one file: each transcript with its times, the language and its confidence, the speech facts and the sound numbers (no label: no "music bed", "song" or "chant" is put on any video), three-word phrases said twice or more (an extraction: a chorus, a chant or a slogan repeats), and notes for a video whose transcript is missing, skipped or failed (facts about the run; whether a transcript is doubtful is your reading). For a video with no words found, `T audio-context --second-pass` adds the same audio transcribed once more without the voice filter (sung words are kept, but words can be invented over pure music or a tone: judge it against the picture and the sound numbers). Read it before writing any card |

**Densify on demand** where the default rate is not enough: fast actions, object interactions, hand
contact, gestures, product appearances, swaps, text appearances, transitions.
```
python atg.py frames "<video>" --out "<run>/10-media/<V>/detail" --range 3.2-4.4 --fps 15 --sheet --label grip
```
Read a single full-resolution frame (`--at 3.6 --max-side 1280`) for small details (labels, UI, hands).

