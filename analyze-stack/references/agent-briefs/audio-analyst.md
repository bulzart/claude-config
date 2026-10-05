# audio-analyst — agent brief (Stage 2b; one agent, runs in parallel with the visual analysts)

Load first: `LAYOUT.md`, `references\report-template.md` (§1, §5, §9 — what the report needs from you),
`research\miko-analysis.md` §2.5–§2.6 (speech rules: verbatim vs summary, no invented speakers, WPM
denominator), `research\tool-audit.md` §F (transcription routes).

## Purpose
Turn the measured audio into a reconciled account of speech, music, sound effects, timing and dead
air that the narrative analyst, the swap planner (brand mentions) and the prompt writers (audio
blocks, dialogue ledger) can rely on.

## Inputs
`10-measure\audio.wav` (source rate) + `audio-16k.wav` (whisper input), `transcript.json` (`has_speech`, `language`,
`language_probability`, `segments[].words[]`) + `transcript.srt`, `audio-features.json` (`tempo_bpm`, `beat_times`,
`onset_times`, `rms[]`, `loudness`, `segmentation[]` speech / music-or-ambience / silence with confidence), `cuts.json`,
`shots.json`, `probe.json`, `measure-summary.md` §4 and §6.

## Outputs
`20-analysis\audio.md` and `20-analysis\audio.json` (same facts, machine-readable).

### `audio.md` skeleton
```markdown
# Audio analysis — <run-id>
Track: aac stereo 44.1 kHz · integrated −16.2 LUFS · true peak −1.1 dBTP · speech: yes (en, p 0.98) · music: yes · SFX: 6
## 1. Reconciled transcript (verbatim; uncertain words as [word?]; timestamps from word timings)
| # | start | end | speaker | delivery | line |
|---|---|---|---|---|---|
| 1 | 00m00.30s | 00m02.10s | C1 (on-screen, female) | upbeat, fast, US English | "okay this is the one everyone [keeps?] talking about" |
## 2. Speakers and delivery
C1: on-screen, casual US English, ~142 WPM (speech-only denominator: 118 words / 49.8 s of speech), pitch rises on questions …
## 3. Brand, product and property mentions in speech (for the swap map)
| time | line fragment | what it names | consequence if the product is swapped |
| 00m01.20s | "the strawberry one" | flavour of the original | line must change or be cut (blending-rules #12) |
## 4. Music
present 00m00.00s–01m02.40s · ~99 BPM (beat_track) · mood/genre in words (never a title unless on screen): "upbeat lo-fi hip-hop, muted drums" · starts under the first word · ducked −8 dB under speech from 00m02.00s · ends on the last frame (no tail)
## 5. Sound effects and diegetic sounds
| time | sound | source visible? | evidence |
| 00m07.40s–00m09.60s | pour with fizz | yes (shot 3) | onset cluster in audio-features 7.4–9.6; transcript gap |
## 6. Sync points
cuts on beats: cuts at 10.00 / 18.53 / 19.87 s fall within 60 ms of beat times → editing is beat-synced from 10 s; the first two cuts are speech-synced (on word ends).
## 7. Dead air and silences
| start | end | dur | what is on screen | keep/cut hint for Mode 3 |
## 8. Room, mic, quality
close phone mic, small reverberant kitchen, slight auto-gain pumping at 00m14.00s …
## 9. Uncertainties
```

### `audio.json` schema
```json
{"schema":"analyze-stack.audio/1","run_id":"…","speech":{"present":true,"language":"en","probability":0.98,"wpm":142,"wpm_denominator":"speech-only","lines":[{"n":1,"start_s":0.3,"end_s":2.1,"speaker":"C1","delivery":"upbeat, fast","text":"…","uncertain_words":["keeps"]}]},
 "brand_mentions":[{"t":1.2,"text":"the strawberry one","names":"flavour","consequence":"change or cut"}],
 "music":{"present":true,"start_s":0.0,"end_s":62.4,"bpm":99,"beats_s":[0.61,1.22],"mood":"upbeat lo-fi","ducking":"−8 dB under speech from 2.0 s"},
 "sfx":[{"start_s":7.4,"end_s":9.6,"sound":"pour with fizz","visible":true}],
 "sync":{"cuts_on_beats":[10.0,18.53,19.87],"cuts_on_words":[1.4,3.4]},
 "dead_air":[{"start_s":9.3,"end_s":14.0}],"room":"close phone mic, small reverberant kitchen"}
```

## Method
1. Read `transcript.json`; keep every word; mark words with probability < 0.6 as `[word?]`; split lines
   at sentence ends or pauses ≥ 0.5 s; attribute speakers by evidence (visible mouth movement per the
   shot table if `visual.md` already exists, voice change implied by pitch/tempo change in `audio-features`,
   on-screen vs off-screen). Never name a speaker you cannot justify — use `V1`, `V2` for unseen voices.
2. If the transcript quality is doubtful (many low-probability words, brand names garbled), re-run
   transcription on the doubtful range with a larger cached model and compare:
   `python -c "from faster_whisper import WhisperModel; m=WhisperModel('small.en',device='cpu',compute_type='int8'); segs,_=m.transcribe(r'<run>\10-measure\audio.wav',language='en',word_timestamps=True,vad_filter=True); [print(round(s.start,2),round(s.end,2),s.text) for s in segs]"`
   Record which words changed and which version you kept, and why.
3. Music: from `audio-features.json` (BPM, beat times, RMS envelope) and the silence/loudness data; state
   where it starts/stops, ducking under speech, mood in plain words. Never guess a track title or artist.
4. SFX: onsets not explained by speech or music beats, matched to visible actions in `shots.json`
   times (pour, click, thud, whoosh, fizz, crunch) — mark `visible: false` for off-screen sounds.
5. Sync points: compare cut times with beat times (±60 ms) and word ends (±80 ms).
6. Dead air: silences ≥ 0.5 s with what is on screen at the time (from shots.json) and a hint for Mode 3.
7. Brand/property mentions: every line that names the product, brand, flavour, slogan, or a property
   that depends on the product (fizzy, creamy, crunchy, cold).

## Quality bar
- Lines are verbatim; the transcript in `audio.md` supersedes `transcript.srt` for every later stage.
- WPM states its denominator; timing values come from word timestamps, not from estimates.
- Every SFX row cites the feature or transcript gap that supports it.

## When evidence is missing
No audio stream → `audio.md` says so in the header and all sections are "n/a". No speech → "no speech
detected" (language probability quoted). Unknown song → "unknown (not on screen)". Never invent lyrics,
speaker identities, or sound names you cannot support.
