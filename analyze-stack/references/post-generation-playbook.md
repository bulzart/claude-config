# Post-generation playbook (`/analyze-stack`, stages 8–9d)

> **OWNER RULE (2026-09-16, overrides every caption passage below): speech captions / subtitles are
> NEVER added in the edit — not burned in, not as a caption track in the editable project, not via
> Descript/CapCut auto-captions. The owner adds them afterwards with a separate caption tool. Only
> non-speech text is allowed: hook text overlays, callouts, end cards, stickers. Wherever this file
> says "captions"/"captions.ass"/"word-pop captions", read it as "not applicable"; `overlays.ass`
> carries hook/callout/end-card text only. The measurement transcript (`10-measure\transcript.srt`)
> may be handed to the owner as a sidecar for that external tool, never rendered.
> Also: editing runs only after the owner answers P0 = "Edit now"; clips may arrive from the
> optional Higgsfield MCP generation stage (7g) or be dropped back manually (Stage 8).

Applies once the owner drops Seedance 2.5 (or other generator) clips back into a run. Governs stages
`80-generated\` and `90-postgen\` of `runs\<run-id>\` (see `LAYOUT.md`). Principle from the contract:
**realism beats length — a clean 30 s output is worth more than 2 min with anomalies.**

Tool paths (PATH may be stale in a fresh shell; scripts fall back to these):
`FFMPEG = C:\Users\Bulzart\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe`,
`FFPROBE` = same folder. ffmpeg 9.0.1 here has libx264, libass, libfreetype, libharfbuzz, libvidstab and
all filters used below (`xfade loudnorm drawtext subtitles ass zoompan noise deshake vidstab* setpts
atempo ebur128 eq curves unsharp hqdn3d tpad fade afade acrossfade sidechaincompress dynaudnorm
minterpolate overlay freezedetect blackdetect ssim signalstats scdet select crop scale aresample
volume alimiter highpass compand concat gblur vignette colorbalance lut3d tmix rgbashift chromashift`
— verified 2026-09-16). Every PowerShell call starts with the PATH refresh one-liner from `LAYOUT.md`;
chain with `;` only.

Stage order: **1 recognise → 2 clip QA (loop fixes) → 3 assembly → 4 trend boosts → 5 export →
6 editable project + edit-plan.json → 7 final check.** Steps 3–6 are executed by scripts in
`tools\edit\` (built by the editing-tooling agent); this file fixes the rules those scripts and the
agents follow.

---

## 1. Recognising generated clips

**Where they arrive.** The owner either (a) pastes absolute paths / drags files into chat, (b) copies
files into `runs\<run-id>\80-generated\`, or (c) names a Higgsfield/Seedance generation (then fetch it
with the Higgsfield MCP `show_generation_by_ids` → download URL → save into `80-generated\`). Anything
dropped in chat is **copied** into `80-generated\` first; nothing is edited in place outside the run.

**Matching clips to prompt numbers**, in this order of precedence:
1. An explicit mapping from the owner ("this is clip 3") or an existing `80-generated\manifest.json`.
2. A number in the file name: first standalone 1–2 digit group (regex `(?<!\d)(\d{1,2})(?!\d)`) in
   names like `clip-03.mp4`, `clip_03_seed1234.mp4`, `03-kitchen.mp4`. Generator default names
   (`higgsfield_<uuid>.mp4`, `seedance-<id>.mp4`, `download (2).mp4`) carry **no** usable number.
3. Otherwise file-modification-time order = prompt order, **and the agent lists the assumed mapping
   and asks the owner to confirm before QA** (one question, all clips at once).
4. Duration sanity: a clip whose duration differs from its prompt's planned seconds-per-prompt by more
   than ±20 % is flagged `duration_mismatch` and the mapping is re-checked.

**Probe every clip** (command verified on the samples in `samples\generated-clips\`):

```powershell
& $FFPROBE -v error -show_entries format=filename,duration,size,bit_rate:stream=index,codec_type,codec_name,profile,width,height,r_frame_rate,pix_fmt,sample_rate,channels -of json "<clip>"
```

Observed sample shapes: `clip-01-higgsfield-15s.mp4` = h264 High, **480x854 @ 24 fps**, AAC 32 kHz,
15.04 s; `clip-02-seg-0-15.mp4` = h264 High, **720x1280 @ 30 fps**, AAC 44.1 kHz, 15.0 s. Generated
clips are frequently below 1080x1920 and not 30 fps, so normalisation (§3) is mandatory and a
1080-upscale step (Higgsfield `upscale_video`, or ffmpeg `scale=…:flags=lanczos`) is part of assembly.

**Write `80-generated\manifest.json`** (rewritten on every drop; source of truth for later stages):

```json
{
  "run_id": "20260916-101500-snowscents",
  "generator": "seedance-2.5",
  "generated_at": "2026-09-16T12:40:00-05:00",
  "clips": [
    {"prompt_no": 1, "prompt_file": "50-prompts/clip-01.md", "file": "80-generated/clip-01.mp4",
     "original_name": "seedance-8f3a.mp4", "duration_s": 15.04, "width": 480, "height": 854, "fps": 24,
     "audio": true, "seed": null, "generation_id": null, "mapping_source": "filename|manifest|owner|mtime",
     "notes": ""}
  ]
}
```

Missing clips (prompt numbers with no file) are listed in `90-postgen\clip-qa.md` as `MISSING` and the
assembly runs without them (never wait silently).

---

## 2. Clip QA (compare every clip against its prompt)

**2.1 Extract evidence** into `90-postgen\qa\clip-NN\` (one folder per clip):

```powershell
# 1 frame per second, downscaled for the Read tool
& $FFMPEG -v error -i "<clip>" -vf "fps=1,scale=540:-2" "90-postgen\qa\clip-01\f_%03d.png"
# first frame and last frame (continuity endpoints)
& $FFMPEG -v error -i "<clip>" -frames:v 1 "90-postgen\qa\clip-01\first.png"
& $FFMPEG -v error -sseof -0.1 -i "<clip>" -update 1 -frames:v 1 "90-postgen\qa\clip-01\last.png"
# contact sheet (5x4 thumbnails)
& $FFMPEG -v error -i "<clip>" -vf "fps=1,scale=270:-2,tile=5x4" "90-postgen\qa\clip-01\sheet.png"
# automatic detectors: unexpected hard cuts, freezes, black
& $FFMPEG -v error -i "<clip>" -vf "select='gt(scene,0.35)',showinfo" -an -f null - 2>&1 | Select-String "pts_time"
& $FFMPEG -v error -i "<clip>" -vf "freezedetect=n=-60dB:d=0.5,blackdetect=d=0.2:pic_th=0.98" -an -f null -
```

Optional automated helpers when available: `rapidocr-onnxruntime` on the label crops for
`product-label` text (install status not verified here); Higgsfield `video_analysis_create` for a
second opinion; ElevenLabs `creative_transcribe_audio` if the clip carries speech.

**2.2 Compare** (the QA agent reads the frames with the Read tool and the prompt file side by side).
Check, in this order and write one line per item in `90-postgen\clip-qa.md`:

| Check | Pass condition |
|---|---|
| Subjects | Same count, same identity (face/body/clothing) across all frames; matches prompt + continuity sheet |
| Product identity | Shape, colour, size, cap/lid, **label text and logo** match `product-spec.md` images; no extra variants |
| Action order | Beats occur in the prompt's order; nothing skipped or repeated |
| Camera | Framing, movement (push-in / handheld / static) and lens feel as prompted; no unmotivated cut |
| Lighting | Direction, colour temperature and time of day as prompted; no flicker |
| On-screen text | Only if prompted; legible, correctly spelled; nothing hallucinated |
| Audio | Present/absent as prompted; no speech if not prompted; no music bed |
| Duration / aspect | Within ±10 % of planned seconds; aspect as planned (9:16) |
| Continuity | `last.png` of clip N vs `first.png` of clip N+1: same location, props, wardrobe, product state |

**2.3 Anomaly taxonomy** (use these ids in `clip-qa.md` and `qa.json`):

`A01 extra object` · `A02 missing object` · `A03 morphing object/shape drift` · `A04 hand/finger error`
· `A05 label/logo drift (text changes, mirrored, wrong colours)` · `A06 gibberish text` ·
`A07 physics violation (floating, clipping, liquid/cloth wrong)` · `A08 teleport / jump in position` ·
`A09 continuity break vs. adjacent clip` · `A10 audio mismatch (unwanted speech/music/noise)` ·
`A11 duration or aspect mismatch` · `A12 face/identity drift` · `A13 camera error (unprompted cut,
wrong move)` · `A14 lighting/colour shift mid-clip` · `A15 residual original-brand mark`.

**2.4 Severity scale** and default action:

| Sev | Meaning | Default action |
|---|---|---|
| S0 | Clean | Use whole clip |
| S1 | Cosmetic, only visible on frame-by-frame inspection | Use; trim if it sits on a cut point |
| S2 | Noticeable at 1x speed but confined to a window ≤ 25 % of the clip | **Trim** to the clean window (min 1.5 s left) |
| S3 | Breaks realism or product fidelity in most of the clip (A03/A05/A07/A12) | **Regenerate** with a fix prompt; if it is not a hero clip and the cut still reads without it, **drop** |
| S4 | Unusable / brand-safety / wrong product | **Drop** now, regenerate only if the story needs it |

**Decision rule (contract): shorter and clean beats longer with anomalies.** A 22 s edit made of S0/S1
material ships before a 45 s edit that contains one S3. The assembly never keeps an S3/S4 segment to
"reach the planned duration". Planned duration is a ceiling, not a target.

**2.5 Fix-prompt format** — append to `90-postgen\fix-prompts.md`, one block per clip, ready to paste:

```
### Fix — clip 03 (round 1)   anomalies: A05, A04   severity: S3
Reuse: seed <seed or "unknown">; reference frame: 50-prompts\references\clip-03-ref.png (or "first.png of clip 02 for continuity")
Keep: camera (slow push-in), lighting (warm window light, late afternoon), action beats 1–3.
CHANGE: the product label must read exactly "SNOW SCENTS — Vanilla Pine", white sans text on matte black,
        label faces camera throughout; the right hand holds the jar by the base with five visible fingers.
<full corrected prompt text, following seedance\SEEDANCE-SPEC.md formatting, with the changed lines marked ✱>
Expected duration: 10 s. Aspect 9:16.
```

Rules: state the change as what **should** be seen (Seedance responds to positive descriptions; use the
spec's negative-prompt field only if the spec provides one), keep everything that passed, re-use the
seed when the generator exposes it so only the changed element moves, and for continuity faults pass
the neighbouring clip's boundary frame as the reference image. Fix rounds are numbered
(`fixes-round-N`) and the loop ends when every kept clip is ≤ S1 or the owner accepts an S2 trim.

**2.6 `90-postgen\qa.json`** mirrors the markdown:

```json
{"clips":[{"prompt_no":3,"file":"80-generated/clip-03.mp4","severity":"S3","anomalies":["A05","A04"],
  "windows":[{"t_in":0.0,"t_out":4.2,"verdict":"clean"},{"t_in":4.2,"t_out":10.0,"verdict":"A05"}],
  "action":"regenerate","fix_prompt":"90-postgen/fix-prompts.md#clip-03-round-1"}]}
```

---

## 3. Assembly

1. **Normalise** every kept clip to the delivery format before cutting (keeps xfade/concat simple):
   `-vf "scale=1080:1920:force_original_aspect_ratio=decrease:flags=lanczos,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p" -c:v libx264 -preset slow -crf 16 -c:a aac -ar 48000 -b:a 192k`
   into `90-postgen\project\media\clip-NN.mp4`. Upscaled sources get a light `unsharp=5:5:0.3` only.
2. **Order** = `40-plan\plan.json` order (Mode 1 slicing / Mode 2 segments / Mode 3 compression), minus
   dropped clips; a dropped clip's beat is covered by lengthening the neighbour only if that neighbour
   is S0.
3. **Trim to the good part** using the `windows` from `qa.json`; always leave ≥ 6 frames of handle so a
   transition never exposes a bad frame. Trims are re-encoded (`-ss` before `-i`, then `-t`).
4. **Cut cadence** comes from the original: read `10-measure\cuts.json` → median shot length (MSL) and
   the hook's first-cut time. Rules: first cut ≤ original first-cut time (typically 1.0–2.5 s); keep
   the edit's MSL within ±25 % of the original MSL; never let a generated shot run > 2× MSL unless the
   prompt is a deliberate hold (ASMR, reveal).
5. **Hard cuts vs. transitions**: default is a hard cut. Use a transition only if `style-profile.md`
   recorded it in the original or the trend brief calls for it: whip/slide (`xfade=transition=slideleft:duration=0.2`),
   zoom punch (`xfade=transition=zoomin:duration=0.25`), crossfade only for mood/time-lapse beats
   (`xfade=transition=fade:duration=0.4`). Example for two normalised clips (offset = first clip
   length − duration):
   `-filter_complex "[0:v][1:v]xfade=transition=slideleft:duration=0.2:offset=4.8[v];[0:a][1:a]acrossfade=d=0.2[a]"`.
   Niche defaults: product/UGC/skincare → hard cuts + 1–2 punch-ins; POV trades (roofing, cleaning)
   → hard cuts + whip on location changes; fashion/lifestyle montage → beat-synced hard cuts, one
   zoom transition at the reveal.
6. **J/L cuts** for anything with speech or VO: audio of the next shot starts 6–12 frames before the
   picture (J), or the previous shot's audio tails 6–12 frames under the new picture (L). In ffmpeg
   this is done by building the audio track separately (`adelay`/`atrim` + `amix`); in CapCut/Descript
   by unlinking and sliding the audio segment. Generated clips' own audio is usually replaced or ducked
   to −18 dB under VO/music unless it is the point (ASMR).
7. **Loop-friendly ending**: end on a frame that matches the hook's framing (same shot size and
   location) or hold the last frame 8 frames and let the platform loop; no fade-to-black on TikTok/Reels
   (a black tail kills the loop and the re-watch).
8. Write the assembly as `edit-plan.json` (§6) **before** rendering; the render script reads the plan.

---

## 4. Trend boosts (driven by `90-postgen\trend-brief.md`)

**4.1 Hook text overlay, 0–2 s.** One line, 3–7 words from the brief's "hooks" section, centred, placed
inside the universal safe box (below). Style: bold sans (Poppins ExtraBold / Anton / Impact), 72–96 px
at 1080 wide, white fill, 6 px black outline, soft shadow; optional single-word colour pop
(#FFE600). It leaves at the first cut or at 2.0 s, whichever is first.

**4.2 Captions.** Word-by-word or 2–4-word phrase captions, highlighted current word, bold sans, white
with 4–6 px black stroke and a 2–4 px shadow, 64–80 px, lower-middle third (baseline at ~62–68 % of
height, i.e. y ≈ 1190–1300 px), max 2 lines. Generate from word timestamps
(`10-measure\transcript.json` from faster-whisper, or a new transcript of the VO) into an `.ass` file
and burn with `-vf "ass=90-postgen/project/captions.ass:fontsdir=<fonts dir>"` (libass is present).
Fonts on this machine: only system Impact / Arial Bold / Segoe UI Bold / Tahoma Bold / Verdana Bold /
Calibri Bold. Recommended downloads (Google Fonts, OFL, static TTFs verified on GitHub 2026-09-16):
`https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-ExtraBold.ttf`,
`…/ofl/poppins/Poppins-Black.ttf`, `…/ofl/anton/Anton-Regular.ttf`,
`…/ofl/bebasneue/BebasNeue-Regular.ttf` (Montserrat and Inter ship only as variable `[wght].ttf`
files in that repo — ffmpeg/libass cannot pick a weight axis, so prefer the static Poppins/Anton).
Store fonts in `C:\Users\Bulzart\.claude\analyze-stack\tools\edit\fonts\` and reference them via
`fontsdir` (no system install needed).

**4.3 Safe zones at 1080x1920** (keep text, product hero and CTA inside; sources: Meta's unified 9:16
safe zone effective March 2026, TikTok/Reels/Shorts guides from Kreatli, Creamate, quso, Koro —
platform UIs shift, re-check quarterly):

| Platform | Top | Bottom | Right | Left |
|---|---|---|---|---|
| TikTok organic | 130–140 px (7 %) | 250–324 px (13–17 %) | 140–164 px (13–15 %) | 60 px (6 %) |
| TikTok ads (CTA button + Sponsored label) | 140 px | **370 px (19 %)** | 164 px | 60 px |
| Instagram Reels (Meta unified, organic + ads) | **270 px (14 %)** | **672 px (35 %)** | 65 px (6 %) | 65 px (6 %) |
| YouTube Shorts | ~240 px (12 %) | ~384 px (20 %) | ~160 px (15 %) | 60 px |
| **Universal safe box used by the pipeline** | **y ≥ 270** | **y ≤ 1248** | **x ≤ 915** | **x ≥ 65** |

Hook text sits at y ≈ 300–450; captions at y ≈ 1150–1300 (inside the Reels 35 % bottom cut: Reels'
own caption/UI overlays start below ~1248, so anything lower is hidden on Reels); product hero and
logo never in the right 165 px column. If the deliverable is TikTok-only, the box may extend
downward: organic TikTok y ≤ 1596 (1920 − 324), TikTok ads y ≤ 1550 (1920 − 370), right edge
x ≤ 916 (1080 − 164) in both cases. Simplest rule: use the universal box unless the owner asks for a
single-platform cut, and record the box actually used in `edit-plan.json → safe_box`.

**4.4 Sound.** Options in priority order, decided by deliverable type (see the licensing table in
`research\trend-sources.md` §3): (1) paid ad → licensed bed baked in (company library / Splice stack /
ElevenLabs) or a CML / Meta Sound Collection track attached at publish time in-platform; (2) organic
post → trending sound from the brief attached **in-app at posting** (never baked in — platforms
detect and credit the sound only when attached natively) with the file exported with original/VO
audio only; (3) original audio when the format is ASMR/POV/voice-led. Music bed level −18 to −22 LUFS
under VO; sidechain-duck under speech (`sidechaincompress=threshold=0.05:ratio=6:attack=20:release=300`).

**4.5 SFX at cuts.** Whoosh on whips, soft pop/click on text pops, riser into the reveal, low thud on
the product land. Source: Splice `describe_a_sound` (query e.g. "short whoosh transition swipe", type
oneshot; returns duration/tags/asset UUID → `download_asset`) or ElevenLabs sound generation. Level
−12 to −16 dB below dialogue peak; never more than one SFX per cut; none in the first 0.5 s.

**4.6 VFX.** Punch-in zoom 1.00→1.08 over 8–10 frames at the hook and at the CTA (`zoompan` with
`z='min(zoom+0.01,1.08)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30`, or CapCut
scale keyframes); speed ramp 1.0→1.6× on montage B-roll (`setpts=PTS/1.6` on the segment; audio
`atempo=1.6`); subtle handheld shake only if the original was handheld:
`crop=w=iw*0.96:h=ih*0.96:x='(iw-ow)/2+8*sin(2*PI*t*1.7)':y='(ih-oh)/2+6*sin(2*PI*t*2.3)',scale=1080:1920`.
Never stack more than two effects on one shot.

**4.7 Colour and grain for realism** (counter the over-polished AI look; apply to the whole timeline
as the last video filter): `eq=saturation=0.92:contrast=1.03:gamma=0.98,unsharp=3:3:0.35,noise=alls=7:allf=t+u,vignette=PI/5.5`
plus optional `chromashift=cbh=1:crv=-1` for a lens feel; match the original's LUT if
`style-profile.md` names one (`lut3d=<file>.cube`). Encode with `-tune film`. Skip the grain if the
trend brief says the niche is "clean beauty studio".

**4.8 End card / CTA.** 1.5–2.5 s, inside the safe box, product + one line + handle; on TikTok/Reels
prefer the CTA as the last spoken line + text pop rather than a static card (static cards drop
completion rate); on Shorts a card is fine. Ads: CTA text must match the platform button copy.

**4.9 A/B variants.** Produce `final-A.mp4` (as planned) and at least one variant that changes exactly
one thing: hook text, first clip order, sound, or CTA line. Name: `final-<variant>-<hook-slug>.mp4`;
record the difference in `edit-plan.json → variants[]`.

---

## 5. Export spec

Target file (all platforms): **MP4, 1080x1920, 30 fps** (or the source fps when all clips share one),
H.264 **High** profile level 4.1, yuv420p, closed GOP 2 s (`-g 60 -keyint_min 60`), 2 B-frames,
**VBR target 10 Mbps / max 16 Mbps** (YouTube's own recommendation is 8 Mbps at 1080p30, 12 Mbps at
60 fps; the extra headroom keeps grain from smearing), AAC-LC **48 kHz stereo 192–256 kbps**,
loudness **−14 LUFS integrated, −1.0 dBTP** (YouTube normalises to about −14; TikTok/Instagram publish
no number — informal tests put them at −14 to −15; −14/−1 is the safe universal target),
`-movflags +faststart`.

```powershell
& $FFMPEG -y -i "90-postgen\project\timeline-video.mp4" -i "90-postgen\project\timeline-audio.wav" `
  -vf "ass=90-postgen/project/captions.ass:fontsdir=tools/edit/fonts,eq=saturation=0.92:contrast=1.03,noise=alls=7:allf=t+u,format=yuv420p" `
  -af "loudnorm=I=-14:TP=-1.0:LRA=9:print_format=summary" `
  -c:v libx264 -profile:v high -level 4.1 -preset slow -tune film -b:v 10M -maxrate 16M -bufsize 20M -g 60 -keyint_min 60 -bf 2 -r 30 `
  -c:a aac -ar 48000 -ac 2 -b:a 256k -movflags +faststart "90-postgen\render\final-A.mp4"
```

(Use two-pass `loudnorm` — measure first with `-af loudnorm=print_format=json -f null -`, then feed
`measured_*` values — when the first pass reports LRA > 12.)

Duration ceilings (2026): **YouTube Shorts ≤ 3 min** (must be vertical or square); **Instagram Reels
≤ 3 min recorded in-app / ~20 min uploaded, but Reels > 3 min are not recommended to new audiences —
keep ≤ 90 s**; **TikTok ≤ 10 min in-app / ≤ 60 min upload on eligible accounts** — irrelevant here:
the pipeline's target is the original's length or shorter, and never over 60 s unless the plan says so.
Ads: TikTok in-feed 5–60 s (9–15 s recommended); Meta Reels ads ≤ 60 s recommended.

File naming: `runs\<run-id>\90-postgen\render\final-<variant>-<platform>.mp4` (platform ∈ `all`,
`tiktok`, `reels`, `shorts`) plus `…-nocaptions.mp4` when the owner posts with platform captions.
Keep the render log as `render\final-<variant>.log` (contains the loudnorm summary).

---

## 6. Editable project rule

**Every render is produced from an editable project, never from an ad-hoc ffmpeg line.** Minimum:
`90-postgen\edit-plan.json` (machine-readable, below) **plus the CapCut draft** (owner rule 2026-09-19: the edit
lives in CapCut; the other formats are optional extras chosen in P2):

- **CapCut draft, edited through the `capcut` MCP** — the draft is built registered by `tools\edit\build_capcut_draft.py`,
  then refined in place with the MCP tools (`capcut_read_timeline`, `capcut_trim_segment` ripple, `capcut_add_transition`,
  `capcut_add_keyframe`, `capcut_add_audio_fade`, `capcut_add_filter`, `capcut_add_text`, `capcut_validate`, `capcut_save`;
  never the caption tools), repaired after every save with capcut-cli (`register --apply --materials`,
  `sync-timelines --nested --apply`, `lint`) and read back with `capcut_read_timeline` / `capcut export-timeline` on every
  re-edit. Server: `tools\mcp\capcut-mcp\` (LAYOUT.md tool table). The MCP refuses to save while CapCut.exe runs —
  that is the intended protection against CapCut's autosave; never force it.
- **CapCut draft (direct path)** written into `C:\Users\Bulzart\AppData\Local\CapCut\User Data\Projects\com.lveditor.draft\<run-id>\draft_content.json` (plaintext JSON, `version` 360000 / `new_version` "185.0.0", registered in `root_meta_info.json`; a real sample is in `research\capcut-draft-sample\`). Builder script: `tools\edit\build_capcut_draft.py` (uses `pyJianYingDraft` if installed, else the in-house writer — see `research\editing-tooling.md`). Media is referenced by absolute path from `90-postgen\project\media\`.
- **OTIO timeline** `90-postgen\project\timeline.otio` (+ FCPXML / Premiere XML via OTIO adapters) — note: on 2026-09-16 `import opentimelineio` failed on this machine (`DLL load failed while importing _opentime`); reinstall is in the install plan. Until fixed, the CapCut draft is the primary editable artefact.
- **Descript project** via MCP: `import_media` (clips + VO) → `prompt_project_agent` (Agent Underlord applies the edit-plan: order, trims, captions) → `export_timeline` (EDL / AAF / SESX / FCPXML / Premiere XML / Resolve XML; poll `wait_for_job`, keep `download_url`) and/or `publish_project` for a shareable review link. Record the project id in `edit-plan.json → projects.descript`.

**`edit-plan.json` schema** (v1; written by the assembly step, read by every render script):

```json
{
  "schema": "analyze-stack.edit-plan/1",
  "run_id": "20260916-101500-snowscents",
  "deliverable": {"type": "organic|paid", "platforms": ["tiktok","reels","shorts"], "w": 1080, "h": 1920, "fps": 30, "max_duration_s": 40},
  "source_reference": {"cuts": "10-measure/cuts.json", "median_shot_s": 1.9, "first_cut_s": 1.4},
  "timeline": [
    {"id": "s1", "clip": "80-generated/clip-01.mp4", "prompt_no": 1, "in": 0.0, "out": 4.8, "speed": 1.0,
     "transition_in": {"type": "cut"}, "effects": [{"type": "punch_in", "at": 0.0, "to": 1.08, "frames": 9}]},
    {"id": "s2", "clip": "80-generated/clip-02.mp4", "prompt_no": 2, "in": 1.2, "out": 6.0, "speed": 1.0,
     "transition_in": {"type": "slideleft", "duration": 0.2}, "effects": []}
  ],
  "audio": {
    "vo": {"file": "90-postgen/project/vo.wav", "lufs": -16, "j_cut_frames": 8},
    "bed": {"file": null, "trending_sound_id": "tb-s2", "attach_in_app": true, "license": "organic-only|tiktok-cml|meta-sound-collection|owned"},
    "sfx": [{"file": "project/sfx/whoosh-01.wav", "at": 4.8, "gain_db": -14}],
    "ducking": {"threshold": 0.05, "ratio": 6}
  },
  "text": {
    "hook": {"text": "This jar sold out twice", "from": 0.0, "to": 1.4, "style": "hook-v1", "y_px": 380},
    "captions": {"file": "90-postgen/project/captions.ass", "style": "wordpop-v1", "baseline_y_px": 1240},
    "cta": {"text": "Link in bio", "from": 34.0, "to": 36.0}
  },
  "look": {"filters": "eq=saturation=0.92:contrast=1.03,noise=alls=7:allf=t+u,vignette=PI/5.5", "lut": null},
  "safe_box": {"x_min": 65, "x_max": 915, "y_min": 270, "y_max": 1248},
  "export": {"profile": "h264-high-4.1", "v_bitrate": "10M", "v_maxrate": "16M", "a_bitrate": "256k", "lufs": -14, "tp": -1.0},
  "variants": [{"name": "B", "changes": {"text.hook.text": "POV: your kitchen smells like pine"}}],
  "projects": {"capcut_draft": "…\\com.lveditor.draft\\20260916-101500-snowscents", "otio": "90-postgen/project/timeline.otio", "descript": null},
  "trend_brief": "90-postgen/trend-brief.md",
  "updated": "2026-09-16T13:05:00-05:00"
}
```

**Re-edit loop** (both directions must work; the render script `tools\edit\render.py` takes
`--plan edit-plan.json` and optionally `--from-capcut <draft>`):

1. Owner edits in the app → CapCut: export from CapCut directly **or** read the re-saved draft back
   (`capcut_read_timeline` through the MCP for a look; `capcut export-timeline "<draft dir>" --out edited.otio --captions skip`
   then `python tools\edit\reimport_otio.py edited.otio --plan 90-postgen\edit-plan.json`) and render again; Descript: `export_timeline` → convert with OTIO → plan → render, or
   `publish_project` for the app-rendered file. The re-rendered file gets a new variant suffix; the
   previous render is kept.
2. Owner (or agent) edits `edit-plan.json` (e.g. swaps hook text, drops segment s3) →
   `python tools\edit\build_capcut_draft.py --plan …` regenerates the draft and `render.py` re-renders;
   the draft is regenerated, not patched, so the plan stays the single source of truth.
3. Every render bumps `updated` and appends a line to `90-postgen\render\history.md`
   (who/what/why/output file), and `state.json → next_step` becomes `final-check`.

---

## 7. Final check (`90-postgen\final-check.md`)

Run on every render; all rows must pass before `DELIVERABLES.md` links the file.

| Check | How | Pass |
|---|---|---|
| Frames vs plan | `fps=1` frames of the render (§2.1 command on `final-*.mp4`); confirm segment order, trims, hook/caption timing against `edit-plan.json`; no S2+ frame survived | Yes |
| Audio sync | VO word timestamps (re-transcribe the render with faster-whisper / ElevenLabs) within ±80 ms of `captions.ass`; SFX land on cut frames | Yes |
| Loudness | `& $FFMPEG -i final.mp4 -af ebur128=peak=true -f null -` → I = −14 ±1 LUFS, true peak ≤ −1.0 dBTP | Yes |
| Safe zones | Overlay check: `drawbox=x=65:y=270:w=850:h=978:color=green@0.4:t=3` on 3 sample frames (hook, mid, CTA) and inspect; all text/product/logo inside | Yes |
| Duration / format | ffprobe: 1080x1920, 30 fps, h264 High, yuv420p, aac 48 kHz, faststart (`moov` before `mdat`: `-v trace` shows `type:'moov'` first), duration ≤ `max_duration_s` and ≤ platform ceiling | Yes |
| No leftover original-brand marks | OCR + visual pass on hook/CTA/product frames for the original creator's handle, watermark, brand, competitor product (anomaly A15); check the audio tail for the original's sound | Yes |
| Music licence | `audio.bed.license` matches deliverable type (paid → never `organic-only`) | Yes |
| Editable project present | `projects.*` paths exist and open (CapCut draft listed in `root_meta_info.json`) | Yes |
| Optional | Higgsfield `virality_predictor` on the render (upload with `media_upload`, then `action:"create"`) — record hook-strength / retention-risk numbers in the report | n/a |

Then update `state.json` (`stage: "postgen-final"`, `files`, `next_step: "publish"`) and add the
render, the edit-plan, the project paths and the trend brief to `70-deliverables\DELIVERABLES.md`.

---

### Sources for the numbers in this file (checked 2026-09-16)

Safe zones: Meta unified 9:16 safe zone (14 % top / 35 % bottom / 6 % sides, March 2026) via
behaviour.digital, adnabu, 1clickreport; TikTok organic/ads margins via quso.ai, creamate.ai,
kreatli.com, getkoro.app; Shorts via kreatli.com. Loudness: forasoft, TrackGleam, Mr. Vocal, OpusClip
guides (YouTube ≈ −14 LUFS; TikTok/IG unpublished). Encoding: YouTube upload recommendations
(support.google.com/youtube/answer/1722171: MP4 faststart, H.264 High, closed GOP, 2 B-frames, AAC-LC
48 kHz, 8 Mbps @1080p30 / 12 Mbps @60). Duration limits: Headliner, Zeely, Flowshorts 2026 pages.
Caption style: Blitzcut / OpusClip 2026 caption studies (word-by-word, white + black outline, bold
sans, lower-middle third). Fonts: google/fonts GitHub API listings.
