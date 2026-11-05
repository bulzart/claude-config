# Clip QA template — `90-postgen\clip-qa.md` + `qa\clip-NN\` evidence + `qa.json` (Stage 9a, one agent per clip)

Consistent with `references\post-generation-playbook.md` §2 (evidence commands, check order, anomaly
taxonomy A01–A15, severity S0–S4, decision rule "shorter and clean beats longer with anomalies").
No captions anywhere: the QA never proposes captions/subtitles; on-screen text is checked only against
what the prompt asked for (normally nothing) and against residual brand marks.

## 1. Evidence per clip (`90-postgen\qa\clip-NN\`)
`python C:\Users\Bulzart\.claude\analyze-stack\tools\clip_frames.py "<run>\80-generated\clip-NN.mp4" --out "<run>\90-postgen\qa\clip-NN" --fps 1`
→ `first-00m00.00s.jpg`, `last-<t>.jpg`, `f-<MMmSS.ffs>.jpg` (1 fps, long side ≤ 1280), `sheet.jpg` (4 columns),
`frames.json` (index + probe); plus `detect.txt` (scene cuts > 0.35, freezes, black) from the playbook §2.1
ffmpeg detector lines. The QA agent LOOKS at `sheet.jpg`, `first-*.jpg`, `last-*.jpg` and every `f-*.jpg` where something
changes (Read tool), and reads the prompt file side by side. Optional helpers: RapidOCR on label crops,
Higgsfield `video_analysis_create` (paid; only if the main session allowed it), ElevenLabs transcription for speech.

## 2. `clip-qa.md` — one section per clip, fixed rows

```markdown
# Clip QA — <run-id> · generator: seedance-2.5 via Higgsfield | owner-dropped · date
Summary: 5 clips · clean 3 · flagged 2 (clip 03 S3 A05 label drift; clip 05 S2 A04 hand at 8–10 s) · missing 0

## Clip 03 — 80-generated\clip-03.mp4 — prompt 50-prompts\clip-03.md — 15.04 s 1080x1920 24 fps audio yes
| Check | Result | Evidence | Anomaly | Sev |
|---|---|---|---|---|
| Subjects | same woman, grey hoodie, bun; count 1 throughout | f-00m01.00s…f-00m15.00s | — | S0 |
| Product identity | shape/colour ok; label reads "SUNNY OAT" at f-00m04.00s, but "SUNNY OAK" at f-00m09.00s–f-00m12.00s | crops at 4.0 s and 9.0 s; OCR 0.93 | A05 | S3 |
| Action order | lift → cap off → pour → set down → sip → smile: as prompted | sheet.jpg | — | S0 |
| Camera | locked-off as prompted; no cut | detect.txt: 0 scene cuts | — | S0 |
| Lighting | window-left, stable | f-00m01.00s vs f-00m15.00s | — | S0 |
| On-screen text | none (as prompted) | all frames | — | S0 |
| Audio | pour + clink present; no speech; no music | ffprobe + transcription (0 words) | — | S0 |
| Duration / aspect | 15.04 s (planned 15) 9:16 | frames.json probe | — | S0 |
| Continuity | last-00m15.00s.jpg vs clip 04 first-00m00.00s.jpg: bottle position matches; cap missing in 04 first frame | last-*.jpg, ..\clip-04\first-*.jpg | A09 | S2 |
Windows: 0.0–4.2 clean · 4.2–12.0 A05 · 12.0–15.0 clean
Verdict: S3 → REGENERATE (fix prompt below) — fallback: trim to 0.0–4.2 + 12.0–15.0 only if the story reads without the pour (it does not: the pour is the signature beat).
```

Rows and ids are those of the playbook (§2.2, §2.3, §2.4). A missing clip gets a section with
`MISSING` and no rows. Edit-approach segments are checked the same way plus: `Stays-as-filmed` row
(person, motion, camera, other props unchanged vs the source segment's frames — compare
`00-input\segments\seg-NN.mp4` frames) and `Original brand marks` row (A15; OCR + eyes on every product frame and reflections).

## 3. `qa.json` (playbook §2.6) — rewritten by the main session from the sections
`{"clips":[{"prompt_no":3,"file":"80-generated/clip-03.mp4","severity":"S3","anomalies":["A05","A09"],"windows":[…],"action":"regenerate|trim|use|drop","fix_prompt":"90-postgen/fix-prompts.md#clip-03-round-1"}],"summary":{"clean":3,"flagged":2,"missing":0}}`

## 4. P0 placeholders
`{n_ok}` = clips with S0/S1, `{n_flag}` = S2+ or missing, `{one-line summary}` = the Summary line's
parenthesis. P0 is asked by the main session right after all QA sections are merged.
