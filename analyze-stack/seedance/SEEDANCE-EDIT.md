# SEEDANCE-EDIT.md — editing an existing video with Seedance 2.5 (and Higgsfield-native alternatives)

## 0. Header

- **VERSION BASIS: Seedance 2.5** — ByteDance Seed, official launch 2026-07-31; developer API on BytePlus
  ModelArk as `dreamina-seedance-2-5-260628` (Volcano Engine: `doubao-seedance-2-5-260628`, community
  single-source). Where 2.5 docs are silent the Seedance 2.0-series editing guide is used and marked.
  Higgsfield exposes the same model as `seedance_2_5` (`mode: "video_edit"`) and `ad_multiplier`.
- **Compiled: 2026-09-16** by research agent R5. Companion to `SEEDANCE-SPEC.md` (generation) and
  `sources.md` (S1–S21, P1–P21, C1–C15 numbering reused below; new sources are listed in §11).
- **READ-ONLY NOTICE: do not refresh or edit this file during `/analyze-stack` runs; only on explicit
  owner request.** (There is one command only; it never runs as a Workflow.)
- Tags: `[official]` ByteDance/Seed/BytePlus/Dreamina/CapCut · `[platform:<name>]` · `[community]` ·
  `[observed]` = measured in this session through the Higgsfield MCP · `[gap]` = not documented anywhere.
- Official ModelArk pages are JS-rendered; their bodies were fetched raw with a crawler UA and read from
  the embedded `MDContent` JSON, so the quotes are literal doc text as of 2026-09-16.

---

## 1. What the edit mode is called, and which model ids run it

| Surface | Name of the mode | Model / endpoint | How the mode is selected |
|---|---|---|---|
| BytePlus ModelArk / Volcano Ark `[official S2, S3]` | "Omni reference-to-video → **video editing** subtask" ("Edit the visuals or audio of an original video, such as replacing the video subject, adding or removing objects in the video, or redrawing or repairing part of the frame.") | `dreamina-seedance-2-5-260628` | `omni_reference_task_type: "edit"` (or `auto` + editing intent words); `content[]` holds one `{type:"video_url", role:"reference_video"}` plus optional `reference_image`/`reference_audio`; `ratio:"adaptive"`, `duration:-1` |
| Seed blog `[official S11]` | "timestamp-level editing", "green-screen editing", "camera-perspective editing" (marketing names for the same subtask) | — | — |
| Dreamina / CapCut consumer app `[official S16; Dreamina "localized editing" page]` | "Smart Edit" / "localized editing" ("precise region-level fixes, object removal, and video cleanup") | Seedance 2.5 in the app | upload source video + references, prompt with `@Video1/@Image1` |
| **Higgsfield MCP** `[platform:Higgsfield, models_explore 2026-09-16]` | `mode: "video_edit"` — "edit one reference video (billed by that video's duration; 'duration' and 'aspect_ratio' are ignored)" | `seedance_2_5`; identical parameter sheet on `ad_multiplier` ("Ad Multiplier video generation powered by Seedance 2.5") | `generate_video {model:"seedance_2_5", mode:"video_edit", medias:[{role:"video"…},{role:"image"…}]}` |
| Higgsfield web UI `[platform:Higgsfield P4, changelog Aug 6 2026]` | "Region-level edits. An object or a face can be fixed in one spot without re-rendering the whole clip." | Seedance 2.5 in the web editor | region brush in the UI — **no mask/region parameter exists in the MCP schema** `[gap]` |
| Higgsfield Genjutsu `[platform:Higgsfield, models_explore + changelog Sep 1 2026]` | "Object Swap" and "Motion Transfer" | `hf_mult_replace_object`, `hf_mult_motion_control` | `generate_video` with role `video` (one source) + role `image` (references); see §9 |
| fal.ai `[platform:fal P6, P9, learn workflows]` | editing runs through **reference-to-video**: "give it a reference video and describe what to change" | `bytedance/seedance-2.5/reference-to-video` | `video_urls[]` + prompt citing `[Video1]`/`@Video1`; `duration:"auto"`, `aspect_ratio:"auto"` |
| Replicate `[platform:Replicate P11]` | "Editing mode" | `bytedance/seedance-2.5` | `reference_videos[]`, `duration:-1`, `aspect_ratio:"adaptive"` ("Editing mode requires -1"; "editing, and extension modes require 'adaptive'") |
| WaveSpeedAI `[platform:WaveSpeed P16]` | "Video Edit" | `bytedance/seedance-2.5/video-edit` (+ turbo) | `video` (auto-trim to 30 s, pad to 4 s), `reference_images`, `reference_audios`, `resolution` 480p/720p/1080p/"4k", `generate_audio` |

Other edit-capable video models in the Higgsfield catalog (not Seedance; listed for routing): `kling_video_edit`
("Kling 3.0 Omni Edit — edit a source video with text instructions and optional reference images",
`mode` std|pro|4k), `flux_3_video_edit` ("Uses the first 15 seconds at most; costs 1 credit per second"),
`gemini_omni_flash_1_1` (`mode:"edit"`, "uses the source video duration capped at 30 seconds"). `[platform:Higgsfield]`

---

## 2. Input video limits (source clip to be edited)

Official ModelArk `[official S2 usage limits, S3 API]`:

| Item | Value |
|---|---|
| Duration of the video **to edit** | **4–30 s** ("The input video to be edited must be `[4, 30]` seconds long. Otherwise, an error is returned."); non-editing reference videos 2–30 s |
| Recommended length | "Videos within **20 seconds** generally produce better results. Longer videos may reduce stability, and multiple attempts may be needed." `[official S1]` |
| Number of videos | up to 10 per request, combined ≤ 30 s; in an edit "If multiple input videos are provided, the model determines which video to edit based on the prompt" → **send exactly one video per edit call** (Higgsfield's `video_edit` is defined as "edit one reference video") |
| Reference images alongside the video | "**1–5 reference images** generally produce better results. You may try 6–8 reference images, but stability may decrease" `[official S1]`; hard cap 30 images / 50 assets |
| Container / codecs | mp4 (`video/mp4`) or mov (`video/quicktime`); video H.264/AVC or H.265/HEVC; audio AAC, MP3 (mov also PCM) |
| Resolution | tutorial: "480p, 720p"; API page: "480p, 720p, 1080p, 4k" (see SPEC §13); hard bounds: width/height 300–6000 px, w/h ratio 0.4–2.5, total pixels **407,696–8,295,044** (≈ 614×664 … 3326×2494) → a 1080×1920 phone video (2,073,600 px) is inside the bound |
| Aspect | any ratio in [0.4, 2.5]; **output keeps the source ratio** ("Locks the output video's aspect ratio, strictly matching the aspect ratio of the video to be edited. The `ratio` parameter must be set to `adaptive`") |
| fps | 24–60 in; output 24 fps |
| File size | ≤ 200 MB per video; request body ≤ 64 MB (so pass a URL, not Base64) |
| Output duration | locked: "keeping it approximately aligned with the duration of the video to be edited. The `duration` parameter must be set to -1 … the output duration may differ slightly from the input, by up to about 0.3 seconds" (API page: "about 0.4 seconds shorter"; "The output duration may be a non-integer number of seconds"); "If a video generated by Seedance 2.5 is used as the editing input, the output duration will not differ from the input duration." |
| Output format | "It is recommended to set `output_format` to `mov`" for editing (yuv444p + PCM: "better preserves color consistency, brightness consistency, and audio-visual consistency in extension and editing tasks") |
| Real faces | ModelArk: "Seedance 2.5 does not support directly uploading reference images or videos containing real human faces" `[official S2, S3, S8]` — a viral UGC source **cannot be sent to ModelArk directly** unless it is a trusted output / authorized asset. Higgsfield's own Ad Multiplier workflow edits user-supplied footage with people in it, so Higgsfield does not apply this block `[platform:Higgsfield workflow]`; fal/Replicate/WaveSpeed document no block `[gap]`. |

Platform specifics:
- **Higgsfield** `[observed + platform]`: no published length/size caps for `video_edit`; the Ad Multiplier workflow (same model) enforces "exactly one measured source video of **4.0–30.0 seconds inclusive**. Do not trim, split, loop, freeze, or clamp an out-of-range source". Uploaded reference videos are stored re-encoded with a `_trim.mp4` suffix (seen in stored generation params) → Higgsfield trims/normalises inputs server-side; the trim length is undocumented `[gap]`. `media_import_url` accepts ≤ 50 MB; `media_upload` (presigned S3 PUT) has no documented cap — assume the ModelArk 200 MB bound.
- **WaveSpeed**: "Videos longer than 30 seconds are trimmed to 30 seconds; videos shorter than 4 seconds are padded to 4 seconds" `[P16]`.
- **fal**: each video reference 1.8–30.2 s, ≤ 30.2 s per list; "Every second of input video you send is a billed second" `[P6, P9]`.
- **Genjutsu**: source "4–30 seconds" (blog) vs "3 to 30 seconds" (product page); "up to 30" (blog) vs "up to 40" (page) reference images; output up to 1080p `[platform:Higgsfield; discrepancy]`.

Pipeline rule derived from the above: cut the source into edit segments of **≤ 20 s (ideal 10–15 s), never < 4 s, always on a hard cut** from `10-measure\cuts.json`; keep the segment at its native ratio and ≥ 720p; one segment per call.

---

## 3. Referencing the source video and the product images in the prompt

- Official 2.5 rule: "Use `@Image 1`, `@Video 1`, and `@Audio 1` to refer to reference assets. Specify what each asset provides, such as appearance, action, or timbre, and what should not be referenced." `[official S2]`. The locked-task table writes the same tags as `@video1` / `@image1` and the tutorial's edit example as `@Video 1` / `@Video1` — all are the same positional "type + number" alias `[official S1, S2]`.
- Numbering = upload order **within the same type** (images, videos, audio are three independent 1-based sequences; asset IDs are never referenced) `[official S5]`. In an edit call with one video, the source is always `@Video 1`; product photos are `@Image 1 … @Image N` in the order they are attached.
- The prompt **must contain an editing trigger** and must **not** contain an extension trigger: "Include at least one editing trigger in the prompt: **edit video, add, insert, remove, delete, modify, replace, change to**, or similar wording" `[official S1]`; "The prompt must include at least one keyword or phrase such as edit the video, add, delete/remove, or modify/replace/change" `[official S2]`. Extension triggers ("extend forward/backward, continue, continue from, extend the story") would reclassify the task. Do not write "reference Video 1" in an edit prompt ("may be classified as a reference task") `[official S4]`. Mismatch → `InvalidParameter.TaskTypeMismatch`; constraint violation → `InvalidParameter.TaskTypeConstraint` `[official S2, S3]`.
- Name the video directly and put the trigger first: official pattern "Video edit: remove everyone in @Video 1 except the protagonist." `[official S2]`, "Editing task: Replace the Asian woman on the right in Video 1 with the Latina woman from Image 1." `[official S1]`.
- Bind every image: "replace the character in @Video 1 with the character in @Image 1" `[official S2]`; "Replace the man in dark clothing in the video with @Image 2, and replace the man in light-colored clothing with @Image 3." `[official S1]`; "Refer to @Image 1 for the environment." `[official S1]`. Say what **not** to take from an image (background, lighting, pose) — the general "which part" rule `[official S1]`.
- Timestamps scope partial edits (2.5 only): "Change the man's action from drinking coffee to mopping the floor from 4-6 seconds in Video 1, and leave the rest of the content unchanged." `[official S1]`; Seed blog: "precise content editing via timestamps … for a specific time frame" `[official S11]`.
- **Higgsfield prompt contract** (from Higgsfield's bundled Ad Multiplier `prompt-writer.md`, which drives the same `video_edit` mode) `[platform:Higgsfield]`: tags are **case-sensitive `@Video1` and `@Image1..@ImageN`** ("never lowercase or mixed-case variants"); "`@Video1` identifies only the source footage and source targets. Every reference-backed replacement comes from its assigned `@ImageN`; bind the alias with `from @ImageN`"; the `medias` array must list the video first and the images in `@Image` order; prompt ≤ 3,900 characters; "Never emit a media UUID, upload id, generation job id, URL, or other transport identifier in the prompt." `[observed]`: stored prompts in generation history show `<<<image_1>>>` tokens where `@Image 1` was written, i.e. Higgsfield normalises the tags server-side (undocumented).
- Other platforms: fal/Replicate schema wording `[Video1]`, `[Image1]` (fal learn pages use `@Video1`); WaveSpeed `@video1`, `@image1` ("Replace the woman on the right with the person in @image1.") `[P6, P11, P16]`.

---

## 4. How to phrase the edit instruction (official examples verbatim)

Official guidance `[official S1 "Editing tasks"]`: "Clarify the scope and content to be modified. Timestamps can be used for partial edits. Whenever possible, describe how the content should change from **A to B**."

| # | Prompt (verbatim) | Source |
|---|---|---|
| EE1 | Video edit: remove everyone in @Video 1 except the protagonist. — *input 5:4 / 16 s → "The output retains the input video's 5:4 aspect ratio and is approximately 16 seconds long."* (API body: `"text": "Video edit: remove everyone in @Video1 except the protagonist."`, `role: "reference_video"`, `ratio: "adaptive"`, `duration: -1`, `omni_reference_task_type: "edit"`, `output_format: "mov"`) | official S2 |
| EE2 | Only edit the man's dialogue in Video 1: change it to 'Don't come over here,' and adjust the accent to an American English accent... | official S1 |
| EE3 | Change the man's action from drinking coffee to mopping the floor from 4-6 seconds in Video 1, and leave the rest of the content unchanged. | official S1 |
| EE4 | Editing task: Replace the Asian woman on the right in Video 1 with the Latina woman from Image 1. | official S1 |
| EE5 | Add small animals to @video1; replace the character in @video1 with @image1; remove the background music from @video1. | official S1 (locked-task table) |
| EE6 | Add some little animals to @Video 1; replace the character in @Video 1 with the character in @Image 1; remove the background music from @Video 1. | official S2 |
| EE7 (= SPEC E7) | Preserve the composition, camera position, lighting, and performance rhythm of @Video 1. Only modify the female lead's appearance and expression: let her naturally age from her twenties to around sixty. The restraint in her eyes gradually softens, tears slide past the corners of her eyes, and the corners of her mouth slowly lift until she finally smiles through her tears. The entire video should be a continuous one-shot, with no jump cuts and no flickering. Her facial features should gradually age without drifting or changing identity. | official S1 "Video instruction editing" |
| EE8 (= SPEC E8) | Replace the two-person fight in @Video 1 with an empty-handed probing exchange before a cold-weapon duel. / Replace the scene with a medieval stone castle platform, an ancient courtyard, an outer platform of a mountain fortress, or a simple stone-brick duel arena. The background should include castle walls, wind, fog, distant mountain ridges, and a flat stone ground. Refer to @Image 1 for the environment. / Replace the man in dark clothing in the video with @Image 2, and replace the man in light-colored clothing with @Image 3. Keep the original actions and rhythm unchanged. / AI effects should only enhance the environment and texture: wind-blown clothing, light fog, a small amount of dust at contact points, cool metallic reflections, subtle film grain, and an epic color palette. The overall style should be restrained, realistic, and evoke a classic hardcore duel atmosphere. Keep the background music synchronized with the action beats. | official S1 "Video editing with reference images" |
| EE9 (= SPEC E10) | Translate the spoken dialogue in the video into Chinese, with no subtitles. Precisely adjust the lip movements to match the translated speech, while keeping everything else unchanged. | official S1 "Video audio editing" |
| EE10 (2.0, product swap) | Replace the perfume featured in Video 1 with the face cream from Image 1, with all original motions and camera work preserved. | official S4 |
| EE11 (2.0 templates) | Adding: At [Timestamp/Timing] and [Spatial Location] of [Video N], add [Description of intended element]. · Removing: Remove [Element to be deleted] from [Video N], keeping the rest of the video content unchanged. · Modifying: Replace [Description of element to be changed] in [Video N] with [Description of intended element]. — examples "Add snacks such as fried chicken and pizza to the countertop in Video 1."; "Remove everything that isn't office supplies from the table in Video 1, keeping the rest of the video content unchanged." | official S4 |
| EE12 (2.0 FAQ) | "Parts not mentioned remain unchanged by default" but "emphasize [unchanged elements] in the prompt for better performance" | official S4 (see SPEC §10.4) |
| EE13 | Replace the perfume in [Video1] with the face cream from [Image1], keeping all original motion. | platform:fal P6 / Replicate P11 |
| EE14 | Take the monsoon night in @Video1 to a dry, dust-heavy late afternoon. The rain becomes airborne dust and heat shimmer... Hold every camera move, the courier's exact route over the parapet, the laundry line catching his shoulder, the bedsheet tearing loose and the hatch slam, all on the same frames as the original. | platform:fal (learn "seedance-2-5-workflows") |
| EE15 (Genjutsu) | "Replace the defender with this girl, keeping her watch on her wrist" · "Move the whole fight into this pastel valley by the turquoise stream" · "Recast both fighters and restage the fight in the pastel valley — every move and camera stays" | platform:Higgsfield genjutsu page |

Higgsfield's own edit-prompt templates (bundled `prompt-writer.md`, used for `mode:"video_edit"`) `[platform:Higgsfield]`:

```text
TASK - VIDEO EDIT:
Preserve every caption, subtitle, and other untargeted on-screen text element from @Video1 exactly as it appears, including its wording, styling, placement, animation, and timing. Text physically attached to a replaced target follows that replacement.
<start>-<end>s: keep everything exactly the same
<start>-<end>s: <one operation sentence>. Keep every unrequested element, camera motion, lighting treatment, and overall color grading from @Video1 exactly the same.
```
Sentence patterns: "Replace only [target] in @Video1 with [replacement] from [@ImageN]" · "Modify only [target] in @Video1 so that [change]" · "Remove only [target] from @Video1 and reconstruct the revealed area consistently with its immediate surroundings" · "Add only [element] at [caption-grounded placement] in @Video1". Segments "tile the full measured duration with no gaps or overlaps"; "A whole-clip edit has one change line and no keep line." The DETAILED template opens with one declaration line per image ("[@ImageN] — [ALIAS], the complete replacement look for [TARGET]: …"), then "Video edit. Keep this @Video1 clip exactly as it is — the same shots and cuts, camera moves, framing, composition, unmapped performers, setting, untargeted held and environmental props, lighting, pacing, and timing. Change only [complete scope] …", numbered operations, a "lock" line naming what must not change, a "Render …" line and "Everything else — … — stays exactly the same."

### 4.1 Product-swap edit skeleton for our pipeline (derived; fill every `{{}}`)

```text
Video edit. Replace only {{original product as seen: "the red 12 oz can with a white label held in the left hand"}} in @Video1 with {{our product}} from @Image1 (front view: exact proportions, colours, cap, label layout and text) and @Image2 (label close-up: logo and wording). Do not copy the background, lighting or surface of @Image1 or @Image2.
{{0}}-{{t_end}}s: the replacement is the same single object throughout, at real-world size, held with the same grip and finger positions, following the same motion path and orientation changes; {{physics consequences: "the liquid poured from it is {{colour}} and {{foam/fizz behaviour}}; the mix turns {{resulting nuance}}"}}. {{Timestamped partial edits if any: "From 4-6 seconds in @Video1, change the sound of the pour to a still, non-carbonated pour."}}
Remove only the {{original brand}} logo and text wherever it appears ({{cup, sleeve, shelf tag}}) and reconstruct the revealed surface consistently with its immediate surroundings.
Keep everything else from @Video1 exactly the same: shots and cuts, camera moves, framing, the person's face, hair, clothing, hands and performance, all other objects and their count, the setting, lighting, colour grading, pacing and timing. Preserve every caption, subtitle, and other untargeted on-screen text element from @Video1 exactly as it appears, including its wording, styling, placement, animation, and timing. Text physically attached to a replaced target follows that replacement.
{{Audio line: "Keep the original audio unchanged." (only when generate_audio=true; our default is generate_audio=false + mux, §5)}} No subtitles. No watermark. No extra products, no duplicated hands, no floating objects.
```
Rules: trigger word ("Video edit", "Replace", "Remove") first; one video; 1–5 images; ≤ 3,900 characters (Higgsfield) and ≤ 1,000 words (ModelArk); describe A→B, then the invariants explicitly (EE12); keep the exact preservation block once (Higgsfield contract); never restate the source person's identity as coming from `@Video1` for a person swap — bind it to an `@ImageN`.

---

## 5. Audio: preserved or regenerated? Do lip-sync and dialogue survive?

- The model **re-renders audio in the same pass** as the picture; there is no pass-through: audio editing is a documented edit sub-capability ("Adds, removes, or modifies audio in video … vocals, music, sound effects") `[official S1]`, `generate_audio` (default `true`) applies to edit tasks, output is mono `[official S3]`, and MOV in/out is recommended because it "better preserves … audio-visual consistency in extension and editing tasks" `[official S1, S2]`. fal states it outright: "audio comes out of the same pass, so an edit that takes the rain away will take the bedsheet snap with it unless you stop it"; "naming the sounds to drop matters as much as naming the picture" `[platform:fal]`.
- To keep the original track through the model, write it: "Keep the original audio unchanged." (official wording, E21 `[official S1]`), "Keep the background music synchronized with the action beats." (EE8). Expect timbre/loudness drift; extension outputs "may differ slightly" in volume `[official S1]`.
- **Higgsfield's own production rule** (Ad Multiplier, same `video_edit` mode): render **silent** — `mode:"video_edit"`, `generate_audio:false` — then restore the source's default audio with ffmpeg ("verified finals receive only the source's default audio"; "Discard accidental generated audio, retain only the generated video stream, trim to exact source duration, and restore only extracted source audio") `[platform:Higgsfield media-pipeline.md]`. This is the right default for our product swaps: dialogue, voice and music stay bit-identical; lip movements are inherited from the source footage (the edit preserves performance), so lip-sync survives by construction as long as the speaker is not the replaced target.
- If the **speaker's face is replaced** or dialogue is changed, the model re-synthesises lips ("Precisely adjust the lip movements to match the translated speech", EE9) and the voice becomes generated; multi-speaker lip-sync is an acknowledged weakness `[official S14]`. Avoid face replacement in Mode 1/2 swaps.
- Consequence for a product swap: sounds that must change with the product (fizz → still pour, crunch, click) are **not** produced when rendering silent. Add them in the post-generation edit (Splice/ElevenLabs SFX, `references\post-generation-playbook.md`) rather than trusting a regenerated mix. Alternative when the sound must come from the model: `generate_audio:true` + "Keep the original dialogue and music unchanged; change only the pour sound to …" and QA the result.
- Genjutsu: "Original audio kept on every non-translated variant" `[platform:Higgsfield changelog 2026-09-01]`; lip-sync "carries over" (press coverage of the launch) — audio is passed through, not regenerated.

Local mux recipe (Windows, ffmpeg 9.0.1; adapted from Higgsfield's pipeline, which forbids `-itsoffset`, `-shortest`, `-avoid_negative_ts make_zero`):
```powershell
# source segment: seg-03.mp4 (15.00 s); edited silent result: seg-03-edit.mp4 (~14.6–15.0 s)
$ff = 'C:\Users\Glaresquare1\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe'
& $ff -nostdin -y -i seg-03.mp4 -map 0:a:0 -vn -c:a copy seg-03-audio.mka
& $ff -nostdin -y -i seg-03-edit.mp4 -i seg-03-audio.mka -filter_complex "[1:a:0]asetpts=PTS-STARTPTS,apad=whole_dur=15.0,atrim=duration=15.0[a]" -map 0:v:0 -map "[a]" -t 15.0 -c:v copy -c:a aac -b:a 192k -movflags +faststart seg-03-final.mp4
```
QC gates (Higgsfield's): duration within max(1/fps, 0.10) s of the source, display aspect within 1.5 %, short edge within 8 px of 720/1080, AAC audio present. If the edited video is shorter than the source by more than the tolerance, fail it rather than freezing frames.

---

## 6. Consistency across split segments (source > 20–30 s, or 15 s pipeline slices)

1. **Split on hard cuts** (from `cuts.json`), 4–20 s per segment; never mid-shot. Because an edit preserves the source's motion, camera and timing, joins at cuts are inherited from the original.
2. **Identical instruction and identical references** for every segment: same prompt text (only the timestamp lines and the "as seen" description of the target change), same product images in the same order, same resolution, same `generate_audio` setting. Identity comes from the images, not from the previous segment.
3. **Seed**: not available — Higgsfield's `seedance_2_5` schema has no `seed`; ModelArk lists `seed` for 1.x only ("similar results, but complete consistency is not guaranteed") `[official S3]`; fal/Replicate expose a seed but "Reproducibility is not guaranteed" `[P6, P11]`. Do not build continuity on seeds.
4. **Anchor still**: after the first segment passes QA, extract a clean frame of the rendered product (ffmpeg) and attach it as an extra `@ImageN` to later segments ("the product must look exactly as in @Image3, which is a frame of the already-edited footage") — the 2.0/2.5 "trusted output" and community anchor-shot practice `[official S8; community C6]`; on ModelArk this also satisfies the face rule for frames containing people.
5. **Duration**: each edited segment may be up to 0.3–0.4 s shorter (0 s if the source segment was itself a Seedance 2.5 output) → conform every result to its source segment length before concatenation (§5 mux, `-t`), then concat with the original audio track as a single continuous file (`-c copy` after identical encoding parameters, or re-encode once).
6. **Colour**: expect small brightness/colour drift per segment (MOV recommended on ModelArk; Higgsfield returns mp4 only) → run a light colour match on the joins in the edit stage; keep `bitrate_mode:"high"` on Higgsfield for the final.
7. Genjutsu Object Swap follows the same segment rules (3–30 s per call) and keeps the source audio itself.

---

## 7. Known failure modes for edits (and the fix)

| Failure | Evidence | Fix |
|---|---|---|
| Task classified as reference or extension instead of edit | trigger-word rule; `InvalidParameter.TaskTypeMismatch` / `.TaskTypeConstraint` `[official S1, S2, S3]` | start with "Video edit:"/"Replace only …"; never "reference Video 1"; never "continue/extend"; on ModelArk set `omni_reference_task_type:"edit"` for synchronous validation |
| Source too long / too many images | "Videos within 20 seconds generally produce better results"; "1–5 reference images" `[official S1]` | ≤ 20 s segments, ≤ 5 images |
| Duration drift, non-integer output | ≤ 0.3–0.4 s shorter `[official S1, S3]` | conform with ffmpeg (§5) |
| Audio replaced / SFX dropped / voice re-synthesised | fal statement; Higgsfield renders silent and restores audio | `generate_audio:false` + mux original audio |
| Reference bleed (product photo's background/lighting leaks into the shot) | "which part to use and which not" `[official S1]`; fal "Do not copy @Image1's studio background" `[P10]` | "Do not copy the background, lighting or surface of @Image1" |
| Label text mutates, logo warps | "text rendering accuracy" improvement area `[official S12]`; Dreamina "No warped logo … unreadable text" `[S17]`; Genjutsu review: "Faces, small text, hands, occlusions, and fine background details can still drift" | supply a label close-up image; keep label text short; QA frames with OCR; fall back to Genjutsu Object Swap or a post-production label composite for legibility-critical shots |
| Original brand text survives on cups/shelf tags | Higgsfield contract preserves untargeted text by default | target each text element explicitly ("Remove only the … logo on the cup …"); "Text physically attached to a replaced target follows that replacement" |
| Captions/subtitles of the source removed or restyled | same contract | include the preservation block (§4) verbatim — our pipeline keeps speech captions out of the edit anyway (LAYOUT overlays rule) |
| Hands / grip mismatch when the new product has a different size | owner brief; fal "no extra hands" | describe the grip and real-world size; prefer a product of the same form factor; otherwise expect re-generation instead of edit |
| Person swap leaves the original person in reflections / cuts | Higgsfield contract exclusion sentence | use the DETAILED template's exclusion sentence; avoid person swaps unless required |
| "Complex editing effects" unstable, multi-subject interaction unstable | `[official S12, S11]` | one operation per call; split compound edits (product first, then environment) |
| 1080p edit outputs are 10-bit HEVC on ModelArk | `[official S2]` | QA at 720p, transcode finals |
| Real faces rejected | ModelArk face policy `[official S2, S3, S8]` | use Higgsfield (no block) or trusted outputs; never ModelArk for raw UGC |
| Region-only fix needed | Higgsfield/Dreamina region edit is UI-only | re-run the whole segment with a tighter "Replace only …" scope, or fix the region in the NLE |

---

## 8. Costs

Higgsfield (credits; $0.05 per credit from the published $1.50 / 30 credits) `[platform:Higgsfield P4 + observed ledger 2026-09-16]`:

| Resolution | credits / s (seedance_2_5, any mode) | 15 s edit (billed by source duration) | Observed charges |
|---|---|---|---|
| 480p | 3 | 45 cr ≈ $2.25 | 4 s = 12, 5 s = 15, 6 s = 18 |
| 720p | 6.5 | 97.5 cr ≈ $4.88 | 4 s = 26 |
| 1080p | 9 | 135 cr ≈ $6.75 | 10 s = 90 (blog) |

`video_edit` is "billed by that video's duration" (models_explore); Ad Multiplier passes `duration: ceil(SOURCE_DURATION)`. Preflight with `generate_video {…, get_cost:true}` (returns credits, submits nothing; not available inside `generate_video_batch`). Failed jobs are refunded (refund rows appear in `transactions`).
Genjutsu (`hf_mult_replace_object` / `hf_mult_motion_control`) `[platform:Higgsfield blog]`: 15 s → 480p 40 cr ($2.00), 720p 104 cr ($5.20), 1080p 144 cr ($7.20). `flux_3_video_edit`: 1 credit/s, first 15 s only.
Other platforms: fal reference-to-video with video input ≈ $0.2838/s at 720p, $0.1323/s at 480p (0.6× multiplier; input seconds billed) `[P9]`; WaveSpeed video-edit $0.11 / $0.22 / $0.55 / $1.10 per s at 480p/720p/1080p/"4k" on input + output duration `[P16]`; ModelArk list prices not fetched `[gap]`.

---

## 9. Higgsfield-native alternatives: Genjutsu (exact MCP parameters)

`models_explore get` (2026-09-16) — both models are plain `generate_video` models; `apps_search` returns **no** Genjutsu marketplace app (the only app is "Match Cut + Tracelab"), so `apps_describe`/`apps_invoke` do not apply.

| | `hf_mult_replace_object` — "Genjutsu: Replace objects in a source video using reference images" | `hf_mult_motion_control` — "Genjutsu: Transfer motion from a reference video to subjects in reference images" |
|---|---|---|
| parameters | `resolution` ∈ {480p, 720p, 1080p}, default 720p (only parameter) | same |
| medias roles | `image_references`, `video_references` | same |
| aspect ratios | `[]` → output follows the source video | `[]` |
| duration | none → follows the source (3/4–30 s) | none |
| tags | video-edit, object-replacement, reference | motion-control, image-to-video, video-reference |
| routing rule (generate_video description) | "Replace, change, or swap an object, product, garment, or character in one source video from reference images -> `hf_mult_replace_object`" | "Copy, repeat, reproduce, mimic, or transfer motion, movement, actions, gestures, dance, or camera motion from one driving video to reference-image subjects -> `hf_mult_motion_control`" |
| call shape | `generate_video {params:{model:"hf_mult_replace_object", prompt:"Replace only the red can held in the left hand with the product from @Image1 (front) and @Image2 (label). Keep every move, the grip, the camera and the audio.", resolution:"720p", medias:[{value:"<source video media_id>", role:"video"},{value:"<product img media_id>", role:"image"},{value:"<label img media_id>", role:"image"}]}}` — "Pass images with role `image` and exactly one source/driving video with role `video`" | same shape; the video is the *driving* clip and the images define the new subject/scene |
| never | "Never use legacy `motion_control` or `ad-multiplier` for a single Genjutsu edit" (MCP server instructions). `motion_control` is Kling 3.0 (`image_id`, `motion_video_id`, `resolution` 720p/1080p, `scene_control` image/video) — a different product | |

Web-UI facts `[platform:Higgsfield genjutsu page / blog / changelog]`: "Object Swap: change exactly what you describe; the rest of the frame stays untouched."; "Motion Transfer: take the motion from any video and build a new scene around it."; presets alone can drive a change, "a short description" refines it; preserved: "Motion and camera work, Timing and cuts, Audio, Original shot composition (in Object Swap mode)"; "Original audio kept on every non-translated variant."; limits: video 3/4–30 s, 30–40 reference images, up to 1080p; review-site caveat: "Faces, small text, hands, occlusions, and fine background details can still drift" and it "performs a generative reconstruction, not a deterministic layer edit".

**When to prefer which** (decision for the swap planner):
- **Genjutsu Object Swap** — the change is one object/product/garment/person in real footage and everything else, including the original audio track and on-screen text, must stay as filmed; no timestamped partial edits; no environment/style change; you want the shortest prompt. Best first try for Mode 1/2 product swaps in a UGC clip.
- **Seedance 2.5 `video_edit`** — the swap has visual consequences beyond the object (liquid colour, foam, reflections, condensation, lighting on new packaging), needs timestamp-scoped edits ("from 4-6 seconds"), needs removal + reconstruction of logos/text on several surfaces, a setting/style change, audio edits, or > 5 references bound with explicit "use only / do not use" scoping; also when the source is a Seedance-generated clip (zero duration drift).
- **Genjutsu Motion Transfer** — the owner wants the original's choreography and camera but a completely new person/product/scene (a "replicate the format" re-shoot rather than an edit); the output is a full re-render, so continuity rules from SEEDANCE-SPEC §10 apply.
- Both Genjutsu models are Higgsfield-only (no ModelArk/fal equivalent); Seedance edit is portable across platforms.

---

## 10. Checklist per edit call (both engines)

1. Segment 4–20 s, on hard cuts, native ratio, ≥ 720p, ≤ 200 MB; confirmed `media_id` (see `research\higgsfield-mcp.md` §B).
2. 1–5 product images, single-view, each bound in the prompt with "use only / do not use".
3. Prompt: trigger word first, one video (`@Video1`), A→B, invariants stated, preservation block, ≤ 3,900 chars; no ids/URLs.
4. Higgsfield call: `mode:"video_edit"`, `generate_audio:false`, `resolution` per QA/final tier, `bitrate_mode:"high"` for finals, `duration: ceil(source)`, `aspect_ratio:"auto"`; `get_cost:true` first.
5. Poll → download → conform duration → mux original audio → QC gates → frame QA (product identity, label OCR, hands, count of objects) → next segment with identical references (+ anchor still).

---

## 11. Sources added by R5 (beyond `sources.md`)

- BytePlus ModelArk 2607689 / 2607688 / 1520757 (S1–S3), re-fetched raw 2026-09-16; sections quoted: "Locked: Editing, first and last frames, and extension", "Reference asset input recommendations", "Editing tasks", "Edit videos", "Task types and constraints", "Video editing" configuration, "Error handling", "Example: Edit a video", usage limits, `omni_reference_task_type`.
- Seed blog S11 (editing paragraphs); Dreamina "Seedance 2.5 Localized Editing Guide" https://dreamina.capcut.com/seedance/seedance-2-5-localized-editing (conceptual only).
- Higgsfield MCP `models_explore` (seedance_2_5, ad_multiplier, hf_mult_replace_object, hf_mult_motion_control, kling_video_edit, flux_3_video_edit, gemini_omni_flash_1_1), `get_workflow_instructions ad-multiplier` + bundle files `references/prompt-writer.md`, `references/media-pipeline.md`, `transactions`, `show_generations` (2026-09-16).
- Higgsfield pages: https://higgsfield.ai/genjutsu , https://higgsfield.ai/blog/higgsfield-genjutsu , https://higgsfield.ai/creator-hub/changelog , https://higgsfield.ai/blog/seedance-2-5-on-higgsfield-2026 , https://higgsfield.ai/blog/seedance-2-5-pricing-2026 , https://higgsfield.ai/seedance/2.5 .
- fal: https://fal.ai/models/bytedance/seedance-2.5/reference-to-video , https://fal.ai/learn/tools/seedance-2-5-workflows ; Replicate https://replicate.com/bytedance/seedance-2.5 ; WaveSpeed https://wavespeed.ai/models/bytedance/seedance-2.5/video-edit .
- Community (Genjutsu limitations): https://www.stork.ai/en/higgsfield-genjutsu , https://www.bottlerocketcontent.com/higgsfield-genjutsu-motion-transfer/ .
