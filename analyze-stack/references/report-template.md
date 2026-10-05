# Report template — `20-analysis\report.md` (what the owner sees before Q1)

Written by the MAIN SESSION (Stage 2d) by reconciling `20-analysis\visual.md`, `audio.md`,
`narrative.md`, `beat-map.md`, `style-profile.md`, `entities.json` and `10-measure\measure-summary.md`.
Rules: every number is measured or marked `estimate`; every claim about a frame cites a contact sheet
cell or keyframe path; nothing is invented (unreadable text = "unreadable", unknown song = "unknown");
disagreements between analysts are resolved here and the resolution is recorded in section 11.
Show the whole report in chat (not a summary) and then ask Q1. Keep to ~150–300 lines.

Headings are fixed (the questions script fills its placeholders from them):

```markdown
# Analysis report — <run-id>

Source: <file name or link> · analysed <YYYY-MM-DD HH:MM> · measurement: 10-measure\measure-summary.md

## 1. Specs
| Field | Value | Method |
|---|---|---|
| Duration | 62.40 s | ffprobe |
| Resolution / aspect | 1080x1920 (9:16) | ffprobe |
| fps | 30 | ffprobe |
| Audio | yes — speech + music, −16.2 LUFS | ffprobe + ebur128 |
| Cuts / shots | 14 confirmed cuts → 15 shots (union of 3 detectors, merged @3 frames) | cuts.json |
| Median shot length / first cut | 3.1 s / 1.4 s | shots.json |
| On-screen text | 3 overlays (see §2), 1 physical label | ocr.json + frames |
| Speech | 118 words, 1 speaker, 142 WPM (speech-only denominator) | transcript.json |
| Music | ~99 BPM, present 0–62 s, ducked under VO | audio-features.json |

## 2. Shot table + pacing
| # | Source time | Framing | Camera move | On screen / props | Action and delivery | Sheet ref |
|---|---|---|---|---|---|---|
| 1 | 00m00.00s–00m01.40s | MCU, eye level | handheld static | overlay "POV: …" (0.0–1.4 s) | she holds the can to camera, says "…" | sheet-01 c1–c4 |
…
Pacing: cut cadence (median, min, max), where the cadence accelerates, dead air windows (from audio.md).

## 3. Narrative structure
| Beat | Time | What happens | Function |
|---|---|---|---|
| Hook | 0.0–2.1 s | … | stops the scroll because … |
| Setup | … | … | … |
| Escalation | … | … | … |
| Climax | … | … | … |
| Payoff / ending / CTA | … | … | … |
One paragraph: what the video is about, what is being told, tone and humour.

## 4. Main frames and iconic moments
| # | Time | Frame ref | Why it matters |
|---|---|---|---|
| I1 | 00m07.50s | 10-measure\keyframes\shots\shot-03-mid-00m07.50s.jpg (sheet-02 c8) | the pour + colour change — the signature visual |
…

## 5. Key lines (verbatim from transcript; uncertain words in [brackets?])
| Time | Speaker | Line | Why it matters |
|---|---|---|---|

## 6. Why it went viral
- Hook (first 1–3 s): …
- Retention mechanics: … (open loop / pattern interrupt / show-while-telling / countdown / reveal …)
- Emotional triggers: … (curiosity, surprise, satisfaction, relatability, humour, aspiration …)
- Payoff / share reason: …
- Beat scores summary (from beat-map.md): top 5 beats by importance with scores S/V/X/Q.

## 7. Visual style + sub-style
Style label: <real organic footage | cartoon | animation | sketch/drawing | mixed> — sub-style: <UGC handheld phone | …>
Reproduction parameters: palette (hex + shares), line work, shading/rendering, animation cadence,
camera language, era, texture, lighting, lens/DoF, grade. (Full: 20-analysis\style-profile.md)

## 8. Setting, people and spatial layout
Setting(s) with fixed object positions; each person (appearance, wardrobe, role) per setup; camera
position and light direction per setup (this becomes the continuity sheet's base).

## 9. Audio
Speech (speakers, delivery, language), music (BPM, mood, where it starts/stops, ducking), SFX with
timestamps, sync points (cut-on-beat), dead air, mic/room character.

## 10. Entity & product inventory  ← feeds Q1
| # | Entity | What it is | Where it appears (times, shots) | Screen time | Swappable? | Brand marks seen |
|---|---|---|---|---|---|---|
| 1 | red 12 oz can | beverage, held/poured | 00m00.00s–00m09.50s, 00m40.00s–00m45.00s (shots 1–3, 9) | 14.5 s | yes | "BRAND X" logo on can, hashtag overlay |
| 2 | tall glass with ice | prop | … | … | yes | none |
| 3 | woman, grey hoodie | person | whole video | 62.4 s | no (person) | none |
Sorted by screen time. `entities.json` holds the same rows with ids `e1…eN`.

## 11. Measurements, disagreements, uncertainty
Analyst disagreements and how they were resolved; estimates vs measured; what could not be read/heard.
```

Q1's numbered list = §10 rows in order: `"{#}. {entity} — {what it is}, {where it appears}, {screen time}"`.
The Q2m placeholders `{duration}` and `{n_shots}` come from §1; Q4c anchor candidates from §4/§6;
Q5 `{style label}` and `{sub-style summary}` from §7.
