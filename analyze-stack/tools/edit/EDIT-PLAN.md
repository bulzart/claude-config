# `edit-plan.json` — the machine-readable edit plan (schema `analyze-stack.edit-plan/2`)

One file drives everything in `tools\edit\`: `render_ffmpeg.py` (the render), `build_capcut_draft.py`
(CapCut 9.4 draft), `build_otio.py` (OTIO / FCP7 XML / FCPXML / EDL), `text_overlays.py`
(`overlays.ass`), `plan_from_clips.py` (writes the first version) and `reimport_otio.py` (updates it from
an edited timeline). It lives at `runs\<run-id>\90-postgen\edit-plan.json`. Times are **seconds** (float);
the CapCut builder multiplies by 1 000 000 (µs), the OTIO builder uses `RationalTime(frames, fps)`.
Relative paths resolve against `project.run_dir` (absolute paths are always accepted).

> **Owner rule — no captions block exists in this schema.** Speech captions / subtitles are never
> added in the edit: not burned in, not as a caption track in CapCut / OTIO / Descript, not via
> auto-captions. `common_edit.load_plan()` refuses a plan that carries `captions`, `subtitles`,
> `transcript`, `caption_track` or `subtitle_track` keys (top level or under `text`), an overlay whose
> `type` is caption/subtitle/speech/karaoke/lyrics, an overlay with `words[]` / `word_timestamps` /
> `transcript` / `srt` / `segments` / `speaker` keys, or an overlay whose `source` cites a transcript.
> `text_overlays.py` additionally refuses more than 12 overlays or six back-to-back short ones
> (caption density). The owner captions the rendered file afterwards with a separate tool; the
> measurement transcript (`10-measure\transcript.srt`) may be handed over as a sidecar, never rendered.

Full example: `tools\edit\edit-plan.example.json`. Minimal smoke plan: `runs\b4test\90-postgen\edit-plan.json`.

## Top level

| Key | Required | Meaning |
|---|---|---|
| `schema` | yes | must be `"analyze-stack.edit-plan/2"` |
| `project` | yes | canvas + run context (below) |
| `clips` | yes (≥1) | the timeline, one entry per source clip (or per trimmed window of a clip) |
| `transitions` | no | transitions between consecutive clips; default = hard cut |
| `text_overlays` | no | hook text / callouts / end cards / stickers — never speech captions |
| `audio` | no | original-audio gain, music bed + ducking, SFX, loudness target |
| `colour` | no | colour/grain preset applied to the whole timeline before the text |
| `export` | no | encoder settings |
| `meta` | no | free-form provenance: `run_id`, `source`, `decisions[]`, `trend_brief`, `clip_qa`, `updated`, `history[]`, `variants[]`, `projects{}` |

## `project`

```json
{"name": "20260916-101500-snowscents", "run_dir": "C:/…/runs/20260916-101500-snowscents",
 "fps": 30, "width": 1080, "height": 1920, "platform": "tiktok",
 "safe_zones": {"x_min": 65, "x_max": 915, "y_min": 270, "y_max": 1248}}
```

- `platform`: `universal` (default) | `tiktok` | `tiktok-ads` | `reels` | `shorts` | `all`. Selects the
  default safe box from `references\post-generation-playbook.md` §4.3 (universal box x 65–915, y 270–1248
  at 1080x1920; TikTok organic may extend to y ≤ 1596, TikTok ads y ≤ 1550, Shorts y ≤ 1536).
- `safe_zones`: explicit box (px) that overrides the platform default. Every text overlay is laid out
  inside it and the render/final check draw it for inspection.

## `clips[]`

```json
{"id": "c01", "path": "80-generated/clip-01.mp4", "prompt_no": 1, "in": 0.0, "out": 4.8, "order": 1,
 "speed": 1.0, "speed_ramps": [{"from": 2.0, "to": 4.8, "speed": 1.5}],
 "transform": {"fit": "cover", "scale": 1.0, "x": 0, "y": 0, "punch_in": {"to": 1.08, "frames": 9}},
 "volume": 1.0, "notes": "S0 clean; hook shot"}
```

| Field | Meaning |
|---|---|
| `id` | unique string; used by `transitions[].between` and the project builders |
| `path` | absolute or run-relative path of the generated clip (any size/fps: 480x854 @ 24 fps is normalised) |
| `in`, `out` | trim in source seconds (`out` is clamped to the real media length) |
| `order` | placement order (ties broken by id); the same file may appear twice with different windows |
| `speed` | base speed (1.0); duration on the timeline = (out − in) / speed |
| `speed_ramps[]` | `{from, to, speed}` in **source** seconds; the clip is split into pieces (setpts/atempo in ffmpeg, one CapCut segment per piece, `LinearTimeWarp` in OTIO). Pieces may not overlap. |
| `transform.fit` | `cover` (scale up + centre crop, default) or `contain` (letterbox/pillarbox) |
| `transform.scale/x/y` | extra zoom (≥1.0) and pixel offset applied after the fit; CapCut receives the normalised equivalent |
| `transform.punch_in` | `{to, frames}` zoom 1.00→`to` over N frames at the clip start (playbook §4.6) |
| `volume` | gain on the clip's own audio (linear; 0 = mute) |
| `notes` | free text (QA verdict, beat name) |

## `transitions[]`

```json
{"between": ["c02", "c03"], "type": "xfade", "duration": 0.4, "xfade": "fade"}
```

`type` ∈ `cut` | `xfade` (ffmpeg `fade`, CapCut Dissolve, OTIO SMPTE_Dissolve) | `whip` (ffmpeg
`slideleft`, CapCut Slide) | `zoom` (ffmpeg `zoomin`, CapCut Pull in). `duration` in seconds (default
0.4 / 0.2 / 0.25); `xfade` optionally names any of ffmpeg's 58 xfade transitions for the render. In the
render the second clip starts `duration` seconds before the first one ends (offset = accumulated length
− duration), so every transition shortens the total by its duration; the CapCut draft keeps the segments
contiguous and attaches the transition material to the first segment (CapCut's own overlap model), so
its timeline is longer by Σ durations — documented in README §5.

## `text_overlays[]` — hook text, callouts, end cards, stickers only

```json
{"id": "hook", "type": "hook_text", "text": "This jar sold out twice", "t_start": 0.0, "t_end": 1.8,
 "position": {"anchor": "top"}, "style": "hook-v1", "font": "Montserrat ExtraBold", "size_px": 88,
 "highlight_words": ["twice"], "highlight_colour": "#FFE600"}
```

| Field | Meaning |
|---|---|
| `type` | `hook_text` \| `callout` \| `end_card` \| `sticker` (anything else, and any caption-like type, is refused) |
| `text` | the line(s); `\n` forces a break; wrapped to the safe width automatically. End cards: first line = headline, following lines use the preset's sub-font |
| `t_start`, `t_end` | timeline seconds (clamped to the timeline end) |
| `position` | `{anchor: top\|middle\|bottom}` inside the safe box, or explicit `{x_px, y_px}` (centre of the block); blocks that would leave the box are shifted back in and a warning is recorded in `overlays.layout.json` |
| `style` | preset: `hook-v1` (Montserrat ExtraBold 88, white, 6 px outline, shadow 2, top band y≈300–450), `callout-v1` (Anton 72, #FFE600, bottom band), `endcard-v1` (Bebas Neue 120 + Montserrat Bold 60 sub-line, middle), `sticker-text-v1` (Montserrat Black 96) |
| `style_overrides` | any preset key (`size`, `fill`, `outline`, `shadow`, `outline_colour`, `fade`, `line_h`) |
| `font`, `size_px` | override the preset font/size; fonts resolve from `tools\edit\fonts\` (Montserrat ExtraBold/Black/Bold, Anton, Bebas Neue) via libass `fontsdir`, fallback Arial Black → Impact (system) |
| `highlight_words`, `highlight_colour` | single-word colour pops (`#FFE600` default) |
| `image`, `width_px` | `sticker` only: a PNG composited by the renderer with `overlay=enable=between(t,…)`; no text needed |

Playbook rules baked in: hook text 3–7 words, leaves at the first cut or 2.0 s; callouts in the bottom
band above y 1248; end card 1.5–2.5 s inside the box; nothing in the right 165 px column.

## `audio`

```json
{"original_gain": 1.0,
 "music": {"path": "90-postgen/project/music/bed.wav", "gain_db": -18, "start": 0.0,
           "ducking": {"enabled": true, "threshold": 0.05, "ratio": 6, "attack": 20, "release": 300},
           "license": "owned", "trending_sound_id": null, "attach_in_app": false},
 "sfx": [{"path": "90-postgen/project/sfx/whoosh-01.wav", "at": 4.8, "gain_db": -14, "label": "whip"}],
 "loudness_target": {"i": -14, "tp": -1.0, "lra": 11}}
```

- `original_gain`: linear gain on the clips' own audio (1.0 = as generated; 0 = drop it).
- `music.path` may be `null` with `trending_sound_id` + `attach_in_app: true` when the sound must be
  attached natively at posting (organic trending sounds are never baked in — `research\trend-sources.md` §3).
  `gain_db` (alias `gain`) in dB; `start` seconds; ducking = ffmpeg `sidechaincompress` keyed by the clip mix.
- `sfx[]`: `at` = timeline seconds; `gain_db` (alias `gain`); mixed with `adelay` + `amix`. Never more than
  one per cut, none in the first 0.5 s (playbook §4.5).
- `loudness_target`: two-pass `loudnorm` (measure, then apply with `measured_*`), default −14 LUFS / −1 dBTP.

## `colour`

`{"preset": "realism-v1", "grain": 7, "filters": null, "lut": null}` — presets `none`, `clean`,
`realism-v1` (`eq=saturation=0.92:contrast=1.03:gamma=0.98,unsharp=3:3:0.35,noise=alls=<grain>:allf=t+u,vignette=PI/5.5`),
`realism-soft`. `filters` = literal ffmpeg chain override; `lut` = `.cube` file (`lut3d`). Applied to the whole
timeline before the text, so overlays stay crisp. CapCut/OTIO do not carry it (the owner re-applies a filter in-app).

## `export`

`{"codec": "libx264", "profile": "high", "level": "4.1", "preset": "medium", "crf": 18, "tune": null,
"audio_bitrate": "192k", "faststart": true, "name": "final-A-all.mp4"}` — 1080x1920 30 fps H.264 High
CRF 18–20, closed GOP 2 s, 2 B-frames, AAC-LC 48 kHz stereo 192–256 kbps, `+faststart`. `name` is the
file name the pipeline uses under `90-postgen\render\`.

## `meta`

Provenance only (never read by the renderer): `run_id`, `source` (`plan_from_clips` | `editor` |
`reimport_otio`), `decisions[]` (why clips were dropped/trimmed), `trend_brief`, `clip_qa`, `manifest`,
`updated` (ISO), `history[]`, `variants[]` (A/B: one change each), `projects` (`capcut_draft`, `otio`,
`descript`). Builders add their output paths here.

## Validation performed by every script (`common_edit.load_plan`)

schema string · `project.fps/width/height` present · ≥1 clip with unique ids, `path`, `in < out` ·
transitions name two existing ids and a known type · no caption-shaped content (refusal, exit 3) ·
overlay types in the allowed set. `render_ffmpeg.py` also clamps `out` to the media length and verifies
the output with ffprobe (size, fps, duration, audio, faststart).
