## 1. Inputs per video (produced by `awl.py prep-all`)

| file | what it gives |
|---|---|
| `10-media/<V>/video.md` | Specs, sampling summary, shot table, transcript (a run that ingests audio; otherwise the line `audio not ingested`), OCR spans, sheet list |
| `10-media/<V>/timeline.md` | One row per second: shot, cuts, motion peaks, static stretches, words spoken, loudness, on-screen text |
| `10-media/<V>/sheets/storyboard-NN.jpg` | The video at the run's effort level (2 to 5 frames per second, `T effort --run RUN`), every second covered, in order. White labels are the baseline; cyan `+` labels are densified frames (cut boundaries, motion peaks, first second); a red bar marks the first frame after a cut; grey cells mark thinned static stretches (≥ 1 fps kept) |
| `frames.json`, `cuts.json`, `activity.json`, `audio.json`, `transcript.json` (only when the run ingests audio, `state.json → audio_ingest` = `whisper`), `ocr.json` | Machine data for exact look-ups |

**Densify on demand** where the default rate is not enough: fast actions, object interactions, hand
contact, gestures, product appearances, swaps, text appearances, transitions. At most the run's `densify_ranges` per video (no cap at
Max); a field that cannot be judged without one more still gets it and says so, and a source picked for production is densified again
in X1 at every level (`effort.md` §2).
```
python awl.py frames "<video>" --out "<run>/10-media/<V>/detail" --range 3.2-4.4 --fps 15 --sheet --label grip
```
Read a single full-resolution frame (`--at 3.6 --max-side 1280`) for small details (labels, UI, hands).

