# `tools\edit\` — post-generation edit module (stage 9c of `/analyze-stack`)

Turns the generated clips of a run into an **editable project + a deterministic render**, driven by one
machine-readable plan (`90-postgen\edit-plan.json`, contract in `EDIT-PLAN.md`). Python 3.12, argparse,
absolute paths, JSON output, non-interactive, exit codes (0 ok · 1 plan/usage error · 2 build/render/
validation failure · 3 refused because the input is caption-shaped · 4 CapCut running on the live store).
Every PowerShell call starts with the PATH refresh one-liner from `LAYOUT.md`; scripts fall back to the
absolute tool paths in `LAYOUT.md` on their own (`common_edit.py` → `tools\common.py` → PATH → fallback).

| File | Role |
|---|---|
| `EDIT-PLAN.md`, `edit-plan.example.json` | the plan contract (schema `analyze-stack.edit-plan/2`) and a full example |
| `common_edit.py` | shared helpers: tool resolution, plan loading + caption refusal, timeline maths, safe-zone overlay layout (Pillow glyph measurement), CapCut/ffmpeg path helpers |
| `plan_from_clips.py` | first plan from clips + `qa.json` verdicts + `trend-brief.json` |
| `text_overlays.py` | plan `text_overlays` → `overlays.ass` (hook text / callouts / end cards; never captions) |
| `render_ffmpeg.py` | ffmpeg 9 render (normalise, trims, speed ramps, xfade, overlays, audio mix + ducking, two-pass loudnorm, H.264 High + AAC + faststart) |
| `build_capcut_draft.py` | CapCut 9.4 draft folder seeded from `research\capcut-draft-sample\`, registered in `root_meta_info.json`, linted with capcut-cli |
| `build_otio.py` | `.otio` + FCP7 `.xml` + `.fcpxml` + CMX `.edl` (OpenTimelineIO 0.18.1 + adapters) |
| `reimport_otio.py` | edited `.otio` / `.xml` / `.fcpxml` / `.edl` → plan trims/order/speed/transitions (NLE and Descript re-edit loop) |
| `descript_bridge.md` | exact Descript MCP procedure (import → Underlord with an explicit no-captions instruction → export_timeline → publish) |
| `fonts\` | Montserrat ExtraBold/Black/Bold, Anton, Bebas Neue (OFL) for libass `fontsdir`; fallbacks Arial Black → Impact |

## 1. No speech captions — owner rule (2026-09-16)

Speech captions / subtitles are **never** added in the edit: not burned in, not as a caption track in the
CapCut draft, the OTIO/XML timelines or the Descript project, not via CapCut/Descript auto-captions. The
owner captions the rendered file afterwards with a separate tool. This module enforces it, it does not
merely recommend it:

- `edit-plan.json` has **no captions block**. `common_edit.load_plan()` refuses (exit 3) a plan with
  `captions` / `subtitles` / `transcript` / `caption_track` / `subtitle_track` keys, an overlay typed
  caption / subtitle / speech / karaoke / lyrics, an overlay carrying `words[]` / `word_timestamps` /
  `transcript` / `srt` / `segments` / `speaker`, or an overlay whose `source` cites a transcript.
- `text_overlays.py` has **no transcript input**; `--transcript --srt --words --from-transcript --whisper
  --subtitles --captions` are recognised only to refuse them (exit 3). More than 12 overlays or six
  back-to-back short ones are refused as caption density.
- `plan_from_clips.py` ignores every trend-brief recommendation that targets captions and logs it.
- `build_capcut_draft.py` writes one `text` track with the plan's hook/callout/end-card/sticker text only,
  never a `subtitle` track; `build_otio.py` writes overlays as markers only; `reimport_otio.py` never
  turns markers into new text (a marker stream could be a caption track).
- `descript_bridge.md` puts a mandatory NO-CAPTIONS block in every Underlord prompt and checks the reply.
- Allowed non-speech text: hook text overlays, callouts, end cards, stickers — inside the safe zones.
  `10-measure\transcript.srt` may be handed to the owner as a sidecar for the external tool, never rendered.

## 2. Full post-generation flow (after Stage 7g generation or Stage 8 drop-back)

```
80-generated\clip-NN.mp4 + manifest.json
  │
  ├─ 9a  clip QA (one agent per clip; references\clip-qa-template.md)  → 90-postgen\clip-qa.md, qa.json, fix-prompts.md
  │
  ├─ 8q  P0 gate (main session, questions.md): Edit now | Regenerate flagged | Stop     ← nothing below runs unless "Edit now"
  │
  ├─ 9b  trend research (references\trend-brief-template.md)            → 90-postgen\trend-brief.md + trend-brief.json ; P2 (edit target) ; P3 (boosts)
  │
  ├─ 9c  python tools\edit\plan_from_clips.py --run-dir <run> [--platform …] [--cta …] [--music …]
  │        → 90-postgen\edit-plan.json (first version: QA trims/drops, brief hook/CTA/sound/effects, decisions[])
  │      editor agent refines the plan (cut cadence, J/L cuts, speed ramps, callouts, SFX, colour) — edits the JSON only
  │      python tools\edit\text_overlays.py <run>\90-postgen\edit-plan.json                → overlays.ass (+ .layout.json)
  │      builders, per P2:  build_capcut_draft.py  |  build_otio.py  |  descript_bridge.md  (or all)
  │      python tools\edit\render_ffmpeg.py <run>\90-postgen\edit-plan.json --out <run>\90-postgen\render\final-A-<platform>.mp4 --verify
  │
  └─ 9d  final check (references\post-generation-playbook.md §7) on render\final-*.mp4 → final-check.md ; state.json stage=done | re-edit
```

Re-edit loops (section 5) go back to `render_ffmpeg.py`; every render appends to `90-postgen\render\history.md`.

## 3. Script usage

### `plan_from_clips.py`
```
python C:\Users\Glaresquare1\.claude\analyze-stack\tools\edit\plan_from_clips.py --run-dir <run>
       [--clip-qa <qa.json>] [--trend-brief <trend-brief.json>] [--manifest <manifest.json>] [--clips-dir <dir>]
       [--out <edit-plan.json>] [--name <project>] [--platform universal|tiktok|tiktok-ads|reels|shorts]
       [--max-duration S] [--cta "text"] [--music <file> --music-gain-db -18] [--sfx-dir <dir>] [--handle-frames 6] [--json]
```
Defaults: `80-generated\manifest.json` (else `clip-*.mp4` numbered by the first 1–2-digit group),
`90-postgen\qa.json`, `90-postgen\trend-brief.json`, `10-measure\cuts.json`, `30-decisions\answers.json`
(platform from Q6), `40-plan\plan.json`; output `90-postgen\edit-plan.json`. **Markdown fallback (V2 fix,
2026-09-16):** when `qa.json` / `trend-brief.json` are missing, `clip-qa.md` / `trend-brief.md` (the
`references\*-template.md` formats: `## Clip NN` sections with `Windows:` + `Verdict:` lines; the brief's fields
table, §1 sounds, hook-text candidates, §4 effects, §6 sweet spot, §7 recommendations, do-not list) are parsed
instead and the fallback is logged in `meta.notes[]`; `--clip-qa <clip-qa.md>` / `--trend-brief <trend-brief.md>`
select the Markdown explicitly. Before the fix a missing `qa.json` silently kept every clip whole, flagged windows
included. The JSON companions stay the primary contract. Rules: S0/S1 → whole clip;
S2/trim → longest clean window ≥ 1.5 s with 6-frame handles; S3/S4/regenerate/drop/MISSING → excluded
("shorter and clean beats longer"); hook = `hook_candidates[0]` for 0–min(2 s, first clip); end card from a
`text.cta` recommendation or `--cta`; sound: organic → attached in-app (never baked in), paid → licensed
alternative or `--music`; effects → punch-in / whip / xfade / speed-ramp note; captions recommendations ignored.
Every decision is in `meta.decisions[]`; the output is re-validated with `load_plan`.

### `text_overlays.py`
```
python …\text_overlays.py <edit-plan.json> [--out overlays.ass] [--fonts-dir DIR] [--max-overlays 12] [--total-duration S] [--json]
```
Default output: `overlays.ass` next to `edit-plan.json` (`<stem>.overlays.ass` for any other plan name).
Presets `hook-v1` (Montserrat ExtraBold 88 px, white, 6 px outline, shadow, top band), `callout-v1` (Anton 72,
#FFE600, bottom band), `endcard-v1` (Bebas Neue 120 + Montserrat Bold 60 sub-line, middle), `sticker-text-v1`.
Blocks are measured with the real TTF (Pillow), wrapped to the safe width and positioned with `\an5\pos(x,y)`
inside `project.safe_zones` (universal box x 65–915 / y 270–1248; playbook §4.3); `overlays.layout.json`
records geometry, `in_safe_box` and warnings. Poison flags / caption-shaped plans → exit 3.

### `render_ffmpeg.py`
```
python …\render_ffmpeg.py <edit-plan.json> --out <final.mp4> [--overlays overlays.ass] [--no-overlays]
       [--single-pass-loudnorm] [--no-loudnorm] [--preset medium] [--verify] [--dry-run]
```
Graph per clip: `trim` + `setpts/(speed)` per piece (+ `atempo` chain), `concat`, cover-fit
`scale…:force_original_aspect_ratio=increase,crop` (or contain + pad), light `unsharp` on upscaled sources,
`fps=30,setsar=1,format=yuv420p,settb=1/30`, optional `zoompan` punch-in; assembly by `concat` or
`xfade=transition=<fade|slideleft|zoomin|any>:duration=d:offset=(accumulated − d)` (+ `acrossfade`), each
output re-pinned with `settb` (xfade refuses mixed timebases); colour preset (`eq/unsharp/noise/vignette`,
optional `lut3d`) before the text; `ass=filename='C\:/…/overlays.ass':fontsdir='C\:/…/fonts'`; PNG stickers by
`overlay=enable=between(t,a,b)`; audio = clip audio (silence for mute clips) + music (`volume`, `adelay`,
`sidechaincompress` keyed by the clip mix) + SFX (`adelay` + `amix`) → `loudnorm` two-pass (pass 1 runs an
audio-only graph and feeds `measured_*`) → `-c:v libx264 -profile:v high -level 4.1 -crf 18 -g 60 -bf 2
-c:a aac -b:a 192k -ar 48000 -movflags +faststart`. The graph is written to `<out>.filter.txt` and passed with
**`-/filter_complex <file>`** (ffmpeg ≥ 7 option-from-file; `-filter_complex_script` no longer exists in
ffmpeg 9), the argv to `<out>.cmd.txt`, stderr to `<out>.log`, verification to `<out>.report.json`.
`--verify` ffprobes the output (1080x1920, 30 fps, planned duration ±0.15 s, 48 kHz audio, `moov` before `mdat`).

### `build_capcut_draft.py`
```
python …\build_capcut_draft.py <edit-plan.json> --name <draft> [--drafts-dir DIR] [--template DIR] [--project-copy DIR]
       [--no-register] [--timelines-mirror] [--force] [--no-lint] [--json]
```
Writes `<drafts-dir>\<name>\` (default drafts dir = the live store
`C:\Users\Glaresquare1\AppData\Local\CapCut\User Data\Projects\com.lveditor.draft`; refuses while CapCut.exe
runs unless `--force`): `draft_content.json` (all markers verbatim from the 9.4 template: `version 360000`,
`new_version "185.0.0"`, `platform.app_version "9.4.0"`; canvas 1080x1920 "9:16" 30 fps; main video track = one
segment per clip piece with trims/order/speed (`source_timerange.duration = target × speed`), transitions
Dissolve / Slide / Pull in (capcut-cli enum ids) attached to the first segment, audio tracks (music, sfx — one
track per non-overlapping set), a `text` track with hook/callout/end-card text materials (UTF-16 style ranges,
highlight words as extra ranges, font TTF path, outline/shadow), PNG stickers as `photo` materials on an
overlay video track), `draft_meta_info.json` (`draft_materials[type 0]` = one entry per media file; every
video material's `local_material_id` links to it — the CapCut 9.x "file inaccessible" fix), `draft_virtual_store.json`,
`draft_settings`, `timeline_layout.json`, verbatim sidecars, `draft_cover.jpg`, empty resource dirs. Registers
the draft in `root_meta_info.json` after backing it up to `root_meta_info.json.bak-<stamp>` (replaces only a
previous entry of the same name; other drafts untouched). Validates (JSON re-parse, every `material_id` /
`extra_material_refs` exists, `duration` == last segment end, media paths exist, text ranges inside the text)
and runs `capcut lint` + `capcut version` (capcut-cli 0.23) → `lint.json`, `build-report.json`. A copy of the
folder is kept in `<plan dir>\project\capcut\<name>\` so CapCut re-saves never destroy the generated original.

### `build_otio.py`
```
python …\build_otio.py <edit-plan.json> --out-dir <dir> [--name timeline] [--no-audio] [--json]
```
`.otio` (Resolve 18.5+, Kdenlive 25.04+, Premiere 25.6+), `.xml` FCP7 (Premiere "Final Cut Pro XML" import,
Resolve, Avid via conversion), `.fcpxml` (Final Cut Pro 10.x), `.edl` CMX 3600 (any NLE; video track only).
V1 = one clip per piece (`source_range` = trim-in + timeline duration; speed as `LinearTimeWarp` + metadata),
`Transition` objects (SMPTE dissolve, centred on the cut so the timeline length equals the render's), markers
for every overlay on V1 and on the sequence (FCP7 XML carries sequence markers), A1 clip audio, A2 music, A3
SFX. Every file is re-parsed with OTIO (the `.edl` at the plan fps — V2 fix: an EDL carries no frame rate and the
cmx_3600 reader defaults to 24 fps, which rejected a 30 fps cut at frame 24 with "Frame rate mismatch"; import the
EDL at 30 fps in the NLE); `<name>.otio-export.json` + `README-otio.md` list results and caveats.

### `reimport_otio.py`
```
python …\reimport_otio.py <edited.otio|.xml|.fcpxml|.edl> --plan <edit-plan.json> [--out <edit-plan.json>] [--track V1] [--dry-run] [--json]
```
Reads the first video track, rebuilds `clips[]` (order, `in`/`out`, speed, merged pieces → `speed_ramps`,
new media → new clips, dropped clips removed) and `transitions[]` (neighbouring trims widened by d/2 to
reproduce the NLE's centred cut in ffmpeg's overlap model), re-times existing overlays from matching markers,
re-anchors `end_card` overlays to the new timeline end when the cut got shorter/longer and no marker re-timed
them (V2 fix; other overlays left beyond the new end are listed in `overlays_beyond_end` — the renderer skips
them), reads `.edl` at the plan fps (V2 fix: the cmx_3600 reader defaults to 24 fps and rejects frame numbers
≥ 24), backs up the previous plan (`edit-plan.<stamp>.json`), appends `meta.history`, re-validates.

## 4. Editable-project options (P2)

| P2 answer | Artefact | Built by | Editable in | Carries | Does not carry (re-apply in-app or rely on the ffmpeg render) |
|---|---|---|---|---|---|
| CapCut only (default; always built) | `<drafts>\<run-id>\` + copy in `90-postgen\project\capcut\` | `build_capcut_draft.py`, then the **`capcut` MCP** (`tools\mcp\capcut-mcp\`: trims with ripple, split/move/delete, transitions from a 116-entry catalog, keyframe animation, audio fades, 474 filters, masks, stickers by resource id, text overlays, mute, undo, validate, save) + capcut-cli repair after every save (`register --apply --materials`, `sync-timelines --nested --apply`, `lint`) | CapCut 9.4.0.4015 (draft listed by name after a restart) | trims, order, speed pieces, transitions (any catalog entry via the MCP; Dissolve/Slide/Pull in via the builder), keyframe punch-ins, audio fades, filters, music + SFX tracks with gains, hook/callout/end-card text with font, colour, outline, shadow, position | grain, sidechain ducking (ffmpeg render only), PNG sticker scale convention (UNCERTAIN), speech captions (never; the MCP's caption tools are forbidden) |
| CapCut + timeline export | `90-postgen\project\otio\*.otio/.xml/.fcpxml/.edl` (in addition to the CapCut draft) | `build_otio.py` | DaVinci Resolve, Premiere Pro, Final Cut Pro, Kdenlive, Avid | clips, trims, order, dissolves (otio/xml/edl), speed (otio only), markers = overlay text + geometry (otio/xml), music + SFX tracks | titles (markers only), whip/zoom look (dissolve stand-in), speed in XML/FCPXML, colour |
| CapCut + Descript project | Descript project + `90-postgen\project\descript\project.json` (in addition to the CapCut draft) | `descript_bridge.md` procedure (MCP) | Descript web app | order, trims, transitions, text overlays as instructed to Underlord, music | determinism (Underlord is an agent), local media (cloud copies), captions (explicitly forbidden) |
| CapCut + all exports | CapCut draft + OTIO package + Descript project | all three | — | — | — |
| always | `90-postgen\edit-plan.json` | `plan_from_clips.py` + editor | any text editor / agent | everything the render uses | — |

**Every render is produced from the plan, never from an ad-hoc ffmpeg line** (playbook §6).

## 5. Re-edit loops

| Loop | Owner edits in | Comes back as | Command | Then |
|---|---|---|---|---|
| plan | `edit-plan.json` (hand or agent) | the plan itself | — | `render_ffmpeg.py` + rebuild the projects (`build_capcut_draft.py` regenerates the draft; it is never patched) |
| CapCut (a) | CapCut draft | CapCut's own MP4 export | — | final check on that file; the plan stays the record of intent |
| CapCut (b) | CapCut draft | `capcut_read_timeline` (MCP) to inspect what changed, then OTIO from the re-saved draft: `capcut export-timeline "<draft dir>" --out edited.otio --captions skip` (capcut-cli 0.25; CapCut closed) | `reimport_otio.py edited.otio --plan …` | `render_ffmpeg.py` (text/effects/keyframes are not carried by the export — read them with `capcut_read_timeline` and update `text_overlays[]` by hand when the owner changed them) |
| NLE | Resolve / Premiere / Final Cut / Kdenlive | export `.otio` (Resolve 18.5+, Kdenlive 25.04+, Premiere 25.6+), FCP7 `.xml`, `.fcpxml` or `.edl` | `reimport_otio.py <file> --plan …` | `render_ffmpeg.py`; `.xml/.fcpxml` lose speed → re-add `speed_ramps` by hand if used |
| Descript | Descript web app / Underlord | `export_timeline` (`premiere` / `davinci_resolve` → `.xml`, `fcp` → `.fcpxml`, `edl`) → download | `reimport_otio.py <file> --plan …` | `render_ffmpeg.py`, or take `publish_project`'s MP4 through the final check |

Every re-render gets a new variant suffix (`final-B-….mp4`), the previous render is kept, and
`render\history.md` gains a line (playbook §6).

## 6. Smoke test — `runs\b4test\` (2026-09-16, this machine)

Inputs: the four stand-in clips in `samples\generated-clips\` (clip-01 480x854 @ 24 fps AAC 32 kHz 15.04 s;
clips 02–04 720x1280 @ 30 fps AAC 44.1 kHz 15.0 s). Plan `runs\b4test\90-postgen\edit-plan.json`: c01 0–4 s
with a punch-in, c02 2–7 s, c03 0–5 s with a 1.5× ramp from 2 s (timeline 4 s), c04 3–8 s; one `xfade` 0.4 s
(c02→c03), hook text "Wait for the pour" 0–1.8 s (highlight "pour"), end card "SNOW SCENTS / Link in bio"
15.6–17.6 s, a silent 0.3 s SFX placeholder at 8.6 s, no music (attach in-app), colour `realism-v1`.
Planned duration 4 + 5 + 4 + 5 − 0.4 = **17.6 s**.

| Step | Command (from `tools\edit\`) | Result |
|---|---|---|
| overlays | `python text_overlays.py …\edit-plan.json --out …\overlays.ass --json` | exit 0; 2 events; fonts Montserrat ExtraBold + Bebas Neue from `fonts\`; `outside_safe_box: []`; hook at `\pos(490,406)` (block width 826 px measured with the TTF, shifted left of centre to stay ≤ x 915), end card `\pos(540,759)` |
| refusals | `--transcript x.json` / plan with `captions` block / overlay with `words[]` / overlay type `subtitle` / 8 back-to-back 0.45 s callouts / `render_ffmpeg.py` on the captions plan | all exit 3 with the owner-rule message |
| render | `python render_ffmpeg.py …\edit-plan.json --out …\render\final-A-all.mp4 --verify` | exit 0 in ~47 s wall; ffprobe: h264 High 1080x1920 yuv420p 30/1, aac LC 48 kHz stereo, **17.70 s** (planned 17.6; the tail is the SFX/loudnorm padding, within ±0.15), 30.8 MB, 13.9 Mb/s, faststart ok; two-pass loudnorm pass 1 measured `input_i −16.28, input_tp +1.98, input_lra 7.40, input_thresh −26.86, target_offset −1.14` → output `ebur128` **I −13.7 LUFS, LRA 4.3, peak −0.7 dBFS** (target −14 / −1 dBTP; short programme, within ±1 LU) |
| frames (Read tool) | `frames\hook-00m00.90s.png`, `mid-xfade-00m08.80s.png`, `endcard-00m16.60s.png` (safe box drawn with `drawbox=x=65:y=270:w=850:h=978`) | hook text inside the box in the top band with "pour" in yellow; xfade visible mid-transition; end card centred inside the box in Bebas Neue + Montserrat Bold sub-line. **No captions.** The only other text ("OBVIOUSLY 🥲", "@LeaFelicitas") is burned into the stand-in clips themselves (they are excerpts of the original viral sample) — a real run's final check would flag that as A15 on the generated material, not on the edit |
| CapCut draft | `python build_capcut_draft.py …\edit-plan.json --name b4test --drafts-dir …\runs\b4test\capcut-drafts` (live store untouched) | exit 0; 5 video segments (c03 as two pieces, second at speed 1.5), 1 sfx audio segment (volume 0.1995 = −14 dB), 2 text segments; `duration` 18 000 000 µs (= Σ pieces; render 17.6 s because ffmpeg overlaps the xfade); 0 validation errors; `capcut lint` **0 errors / 0 warnings / 5 info** (`media-outside-draft`: media referenced outside the draft folder — intended, `material_save_mode 0`); `capcut version` → CapCut 9.4.0 windows, schema 360000, `write_guard ok`; `capcut texts` lists both overlays; `root_meta_info.json` created with one entry; second run with the same name → `root_meta_info.json.bak-20260916-231729`, entry replaced, no other entry touched; auto plan (`--name b4test-auto`) → Slide transition material + punch-in, lint 0/0/3 |
| OTIO | `python build_otio.py …\edit-plan.json --out-dir …\project\otio --name b4test` | exit 0; re-parse: `.otio` 11 clips / 3 tracks / 2 transitions / 4 markers / **17.6 s**; `.xml` 11 / 3 / 2 / 2 markers / 17.6 s; `.fcpxml` 11 / 3 / 0 transitions / 0 markers / 17.6 s (adapter limitation); `.edl` 5 clips / 1 track / 1 dissolve / 17.75 s |
| reimport (round trip) | `python reimport_otio.py …\project\otio\b4test.xml --plan …\edit-plan.json --out …\edit-plan.roundtrip.json` | clips and the 0.4 s xfade reproduced exactly; c03 came back as 0–4 s at 1× (FCP7 XML drops `LinearTimeWarp`) |
| reimport (edited) | scratch script swapped c02/c04 and retrimmed c01 to 0.5–3.5 in `edited.otio` → `reimport_otio.py edited.otio --plan … --out edit-plan.reedit.json` | order c01, c04, c03, c02; c01 0.5–3.5; xfade now c04→c03 with trims widened by 0.2 s; c03 ramp `{2.0→5.0 @1.5}` preserved; c02 2.0–6.8 (its handle stayed in the NLE) |
| re-render | `python render_ffmpeg.py …\edit-plan.reedit.json --out …\render\final-B-reedit.mp4 --verify` | exit 0; 16.70 s (planned 16.6); all checks true; end card clamped to the new end (warning recorded). Wall time was ~10 min on a loaded machine vs 47 s for the first render — same graph, so treat it as machine load, but watch it |
| plan_from_clips | fixture `80-generated\manifest.json` (4 clips), `qa.json` (01 S0, 02 S2 A04 trim, 03 S3 regenerate, 04 S1), `trend-brief.json` → `python plan_from_clips.py --run-dir …\b4test --platform tiktok --out …\edit-plan.auto.json` | kept c01, c02 (1.40–15.00 s with handle), c04; c03 excluded (S3); hook from `hook_candidates[0]`; end card "Link in bio"; sound tb-s1 attached in-app (organic-only, not baked in); punch-in on hook + CTA; whip into c04; speed-ramp left to the editor; the captions recommendation ignored and logged; total 43.4 s flagged against the 18 s sweet spot; dry-run render ok |

Artefacts: `runs\b4test\90-postgen\{edit-plan.json, edit-plan.auto.json, edit-plan.roundtrip.json,
edit-plan.reedit.json, overlays.ass, overlays.layout.json, qa.json, trend-brief.json, history.md,
render\final-A-all.mp4 (+ .filter.txt .cmd.txt .log .report.json), render\final-B-reedit.mp4,
render\frames\*.png, project\otio\*, project\capcut\b4test*, project\sfx\silent-placeholder.wav}`,
`runs\b4test\capcut-drafts\{b4test, b4test-auto, root_meta_info.json, root_meta_info.json.bak-*}`,
`runs\b4test\80-generated\{clip-01..04.mp4, manifest.json}`.

## 6b. V2 verification — `runs\verify-v2\` (2026-09-16)

Full re-run of this module on the four stand-in clips from hand-written `clip-qa.md` (clip 03 "trim to 0–8 s")
and `trend-brief.md`: plan → overlays → render (35.0 s, −13.8 LUFS) → CapCut draft (test store + ONE real
registration `analyze-stack-verify` in the live store, CapCut closed, index backed up to
`runs\verify-v2\root_meta_info.backup.json`) → OTIO/XML/FCPXML/EDL → manual-edit loop (`edit-plan.v2.json`,
c02 +2 s + new hook → `final-v2.mp4`) → NLE loop (`edited.otio` c04 shortened → `edit-plan.nle.json`).
Report with every number and the three fixes (Markdown fallback, EDL rate, end-card re-anchor):
`runs\verify-v2\VERIFY-REPORT.md`.

## 7. Known limits / to verify in-app (not verifiable without launching CapCut on the live store)

- CapCut MCP (`tools\mcp\capcut-mcp\`, installed 2026-09-19): media added with `capcut_add_video/_audio/_image` gets
  `local_material_id = ""` and no `draft_meta_info.json` entry → run `capcut register … --apply --materials` after
  every `capcut_save` or CapCut may show "file inaccessible"; the MCP writes root `draft_content.json` only → run
  `capcut sync-timelines … --nested --apply` (CapCut 9.x treats the nested `Timelines\` copy as authoritative);
  `capcut_add_text` needs `_analyze-stack-template` in the store; `capcut_save` refuses while CapCut.exe runs
  (intended); effects/transitions still need CapCut's online resource cache to render in-app. VERIFIED 2026-09-19:
  `smoke.mjs` end-to-end in a scratch folder (34 tools; clone, add_track+add_text, catalog transition, keyframe pair,
  audio fade, ripple trim, validate ok:true, save refused while CapCut.exe ran, forced save in scratch only) and the
  registered user-scope server read the live store from inside Claude Code (`capcut_list_drafts`, `capcut_read_timeline`,
  locked flag on the draft open in CapCut). capcut-cli on the saved scratch draft: `register --materials` reports every
  referenced file registered, `sync-timelines --nested` in sync, `lint` 0 errors. Local patch: the upstream validator
  flagged audio-vs-video segments sharing render_index 0 as an ambiguous layer order (every builder draft with an SFX
  under a clip) — audio tracks are now excluded from that check (`PROVENANCE.md`).

- CapCut draft opened in CapCut 9.4: font by TTF path (`content.styles[].font.path` + `font_path`),
  `font_size` heuristic (px ÷ 4.6; 88 px → 19 like capcut-cli's hook template), `border_width` = outline/size,
  transition resources (CapCut downloads the effect by `effect_id`/`resource_id` when online; otherwise
  re-apply in-app), PNG sticker scale convention, the `Timelines\` mirror (off by default; `--timelines-mirror`
  or `capcut sync-timelines <draft> --nested --apply` if CapCut opens an empty timeline). First open re-saves
  the folder (expected). CapCut 10.x reportedly rejects tool-written drafts — keep 9.4.
- OTIO: XML/FCPXML adapters (1.0.0) drop speed effects (and FCPXML drops transitions/markers); titles are markers.
- Music ducking, colour/grain and punch-in exist only in the ffmpeg render (CapCut: owner re-applies
  Auto-ducking / filters; OTIO: metadata only).
- `render_ffmpeg.py` normalises to cover-fit; a 480x854 source is upscaled 2.25× (`lanczos` + light `unsharp`) —
  Higgsfield `upscale_video` before the edit gives better texture (paid; playbook §3.1).
- Loudness: two-pass `loudnorm` lands within ±0.5 LU on 17 s programmes; very short renders (< 10 s) may drift more.

## 8. Dependencies (all present on this machine 2026-09-16)

ffmpeg/ffprobe 9.0.1 (Gyan full: libx264, libass, libfreetype, fontconfig), Python 3.12 with Pillow 11.3 and
opentimelineio 0.18.1 + `otio-fcp-adapter`, `otio-fcpx-xml-adapter`, `otio-cmx3600-adapter` (MSVC 2022
runtime installed), capcut-cli 0.23.0 (`%APPDATA%\npm\node_modules\capcut-cli\dist\index.js`, run through
node to avoid the `.ps1` shim), CapCut 9.4.0.4015, fonts in `tools\edit\fonts\`. Nothing to install.
