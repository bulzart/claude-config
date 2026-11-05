# Higgsfield MCP — exact call sequence for the analyze-stack generation pipeline

Research agent R5, 2026-09-16. Everything below comes from the tool schemas loaded in this session
(`ToolSearch select:mcp__claude_ai_Higssfield__…`), from `models_explore` output, from the bundled
`ad-multiplier` workflow files served by the MCP, and from **zero-cost calls actually run** (balance,
models_explore, media_upload + PUT + media_confirm with two probe files, show_medias, show_generations,
job_status, jobs_wait, transactions). No generation was submitted. Tool prefix in this session:
`mcp__claude_ai_Higssfield__`; a standalone registration would be `mcp__higgsfield__` (see
`higgsfield-mcp-install.md`). The connector name is misspelled "Higssfield" in the owner's claude.ai
settings — discover tools with `ToolSearch "select:<exact name>"`.

## A. Balance and cost estimation

- `balance {}` → `{"credits": 1051.56, "subscription_plan_type": "ultra"}` (2026-09-16 18:5x UTC).
- `transactions {size: 25}` → `{items:[{display_name:"Seedance 2.5", credits:-26, action:"spend"|"refund"|"grant"|"deduct", created_at}], next_cursor}` — the ledger to reconcile spend per clip (refund rows appear for failed jobs).
- Observed per-clip charges for `seedance_2_5` today: 4 s 480p = 12, 5 s 480p = 15, 6 s 480p = 18, 4 s 720p = 26 → **3 credits/s at 480p, 6.5 credits/s at 720p**; 1080p = 9 credits/s (Higgsfield blog: 10 s = 30/65/90 credits at 480/720/1080p; $0.05 per credit). Fractional credits are charged (6.5 exists).

| clip | 480p | 720p | 1080p |
|---|---|---|---|
| 5 s | 15 | 32.5 | 45 |
| 10 s | 30 | 65 | 90 |
| 15 s | 45 | 97.5 | 135 |
| 20 s | 60 | 130 | 180 |
| 30 s | 90 | 195 | 270 |

`video_edit` is "billed by that video's duration" (source length); `video_extension` by the new duration (assumed, `[gap]`). Genjutsu `hf_mult_*`: 15 s = 40 / 104 / 144 credits. `flux_3_video_edit`: 1 credit/s (first 15 s).
- **Authoritative preflight**: `generate_video {params:{…same params…, get_cost:true}}` → returns the credit cost **without submitting** ("If true, return the cost in credits for this generation without submitting any job"). Not allowed inside `generate_video_batch` (`get_cost` is rejected there), so preflight one representative clip per (duration, resolution, mode) and multiply.
- Budget rule for a run: `sum(cost) × (1 + retry allowance 0.5) ≤ balance`, else stop and report before submitting.
- `use_unlim`: omit it; if the account holds a free-trial allowance the server returns `unlim_choice` instead of submitting — put the question to the owner and resubmit with `use_unlim:true|false`. Today `models_explore` reports `unlim.available:false`, `seedance_2_5.supports_unlim` absent (only `seedance_2_0`, `kling3_0`, `gemini_omni`, `wan2_7` carry `supports_unlim:true`).

## B. Getting a `media_id` for local files (verified non-interactively from PowerShell)

Three intake tools; `medias[].value` must be a media_id or a job_id — "Do not pass https:// URLs here".

| Tool | Takes | Returns | Use |
|---|---|---|---|
| `media_upload` | `{filename, content_type?}` or `{files:[{filename, content_type?}] (1–20)}`, `method:"upload_url"` | `uploads[]: {upload_url (S3 presigned PUT, `expires_in_seconds: 86400`, signed headers `content-type;host`), media_id (UUID), url (public CloudFront URL of the future file), method:"PUT", content_type, instructions}` | **our path**: local mp4/jpg/png/wav; type is inferred from the extension |
| `media_confirm` | `{type:"image"|"video"|"audio"|"file", media_id}` or `{type, media_ids:[…] (1–20, same type)}` | `{results:[{media_id, status:"uploaded"}]}` | after every PUT returned 200 |
| `media_import_url` | `{url (HTTPS), type?:"auto"|"image"|"video"|"audio"}` | confirmed `media_id` | public URLs ≤ 50 MB (yt-dlp'd sample already hosted, CDN links) |
| `media_upload_widget` | `{type, multiple, min_files, max_files, label}` | opens a browser widget | **Apps-UI clients only (claude.ai); not usable from Claude Code / headless** — do not call it |
| `show_medias` | `{type:"image"|"video"|"audio", size, cursor}` | `{items:[{id, type, url, created_at}], media_type, next_cursor}` | find/reuse earlier uploads |

Verified sequence (2026-09-16, 205-byte PNG and a 714 KB 720×1280 24 fps H.264/AAC mp4):

1. `media_upload {files:[{filename:"analyze-stack-probe.png", content_type:"image/png"}, {filename:"analyze-stack-probe-2s.mp4", content_type:"video/mp4"}], method:"upload_url"}` → two `upload_url`s + `media_id`s (`aab7a7ad-…`, `9e6b75ec-…`).
2. PUT from Windows PowerShell 5.1 (no curl needed):
   ```powershell
   Invoke-WebRequest -Uri $uploadUrl -Method Put -InFile 'C:\…\runs\<run>\50-prompts\references\product-front.png' -ContentType 'image/png' -UseBasicParsing -TimeoutSec 300
   ```
   → `HTTP 200` with an `ETag`. `Content-Type` **must equal** the `content_type` returned by `media_upload` (it is a signed header; a mismatch gives S3 403 `SignatureDoesNotMatch`). Use `-TimeoutSec 600` for 100–200 MB videos. Python equivalent: `requests.put(upload_url, data=open(path,'rb'), headers={'Content-Type': ct}, timeout=600)`.
3. `media_confirm {type:"image", media_id:"aab7a7ad-…"}` → `{"results":[{"media_id":"aab7a7ad-…","status":"uploaded"}]}`; same for the video with `type:"video"`. Confirm **only** after HTTP 200; `media_ids[]` batches one type at a time.
4. `show_medias {type:"video", size:3}` listed the new file at `https://d2ol7oe51mr4n9.cloudfront.net/user_<id>/<media_id>.mp4` (HEAD → 200, public, no auth).

Limits: no size cap is documented for `media_upload`; the presigned URL is valid 24 h; reserve URLs right before uploading and never reuse one. Assume the Seedance input bounds (video ≤ 200 MB, 4–30 s for edits, 300–6000 px, w/h 0.4–2.5, 24–60 fps; images < 30 MB) — `SEEDANCE-EDIT.md` §2. Uploaded reference videos are stored re-encoded with a `_trim.mp4` suffix (observed in generation params) — Higgsfield normalises inputs; trim length undocumented.

Fallback (only if PUT is blocked by the network): host the file at a public HTTPS URL and call `media_import_url`. Google Drive via the Drive MCP: `create_file` takes `base64Content` (impractical for videos, fine for a product JPG ≤ ~5 MB), `share_file` only grants a named email (no "anyone with link" option) → the owner must set link-sharing manually; then `media_import_url {url:"https://drive.google.com/uc?export=download&id=<fileId>", type:"video"}` (≤ 50 MB; larger Drive files return a virus-scan interstitial and fail). Job ids of completed generations can be used directly as `medias[].value` (no re-upload) — the server resolves them ("image_job"/"video" media), used by Higgsfield's own workflow.

## C. `generate_video` parameters for Seedance 2.5

Schema: `generate_video {params: {model (required), prompt, medias:[{value, role}], duration (int), aspect_ratio, count 1–4, get_cost, use_unlim, preset_id (higgsfield_preset only), declined_preset_id, …model-specific keys}}` — `params` accepts additional properties, which is how the model parameters below are passed. Full `seedance_2_5` spec from `models_explore get`:

| key | values | notes |
|---|---|---|
| `mode` | `t2v` (default) · `omni_reference` · `video_edit` · `video_extension` | "`video_edit` to edit one reference video (billed by that video's duration; 'duration' and 'aspect_ratio' are ignored)"; "`video_extension` … ('aspect_ratio' is ignored — the output follows the extended video)" |
| `duration` | 4–30, default 5 | "Unsupported → nearest allowed value or clamped"; Ad Multiplier also passes `duration_policy:"strict"` (undocumented extra key) |
| `resolution` | `480p` · `720p` (default) · `1080p` | |
| `generate_audio` | bool, default `true` | `false` = silent |
| `bitrate_mode` | `standard` (default) · `high` | use `high` for finals |
| `extension_mode` | `backward` · `forward` | required for `video_extension`, forbidden otherwise |
| `aspect_ratio` | `auto`, `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16` | or `width`/`height` (e.g. 1080×1920) — the backend derives the ratio; stored params show `width:720,height:1280` for 9:16 720p |
| `medias[].role` | `start_image`, `end_image`, `image_references`, `video_references`, `audio_references` | "Server may auto-coerce when unambiguous": Higgsfield's own workflow passes `role:"video"` / `role:"image"` and stored params show `role:"image"` / `role:"video"` — both forms work; use the explicit role names for start/end frames |
| `count` | 1–4 | variants of the same request in one widget; batch tool forces 1 |
| observed stored keys (not in schema) | `genre:"auto"`, `multi_shots:false`, `multi_shot_mode`, `multi_prompt:[]`, `speedramp:"auto"`, `reference_elements:[]`, `prompt_language:"en"`, `model:"default"` | server defaults; do not set |

Not available on Higgsfield's Seedance 2.5: `seed`, `watermark`, `output_format` (mp4 only), `return_last_frame`, `omni_reference_task_type`, `camera_fixed`, a region mask.

Mode → media layout and how `@` tags map:

| mode | medias | prompt tags |
|---|---|---|
| text-to-video | none; `mode:"t2v"` | none |
| image-to-video | `[{role:"start_image"}]` (+ `[{role:"end_image"}]`); `mode:"omni_reference"` (Higgsfield has no separate i2v mode; whether start/end frames may be mixed with `*_references` is undocumented `[gap]` — ModelArk forbids mixing) | describe "the first frame" in prose; official "Image 1 is the first frame" wording when passed as a reference instead |
| multi-reference | `mode:"omni_reference"`; images with `image_references` (or `image`), videos `video_references`, audio `audio_references`; ≤ 30/10/10, ≤ 50 total (ModelArk bounds; Higgsfield publishes "up to 50 references") | `@Image N` = Nth image in `medias` order, `@Video N` = Nth video, `@Audio N` = Nth audio (three independent 1-based counters); Higgsfield contract: exact case `@Image1`/`@Video1` (space-less form also seen server-side as `<<<image_1>>>`) |
| video edit | `mode:"video_edit"`, **video first, then images in `@Image` order**, exactly one video; `duration: ceil(source_s)`, `aspect_ratio:"auto"`, `generate_audio:false` (Higgsfield's own rule, then mux source audio) | `@Video1` = the source; `@ImageN` = product/identity refs; editing trigger word required (`SEEDANCE-EDIT.md` §3–4) |
| video extension | `mode:"video_extension"`, `extension_mode:"forward"|"backward"`, one video (+ refs), `duration` = new length | "Extend @Video1 forward by … : …" |

`generate_video_batch {requests:[{index, params}] (1–12)}` — same `params` minus `count` (fixed 1) and minus `get_cost`; response keeps each `index` with its `job_id`; "A partial failure or timeout does not make the whole batch safe to retry: keep returned job IDs and resolve unknown submission outcomes before retrying affected items." For > 12 clips submit several batches and keep one global index. `use_unlim` handling is per request (an `unlim_choice` means nothing was submitted for that item).

## D. Polling and result shape (verified on completed jobs)

- `job_status {jobId}` → `{generation:{id, type:"video", status:"completed", model:"seedance_2_5", params:{prompt, aspect_ratio, duration, medias:[{role, data:{id, type:"media_input"|"video_input", url}}], width, height, resolution, generate_audio, bitrate_mode, extension_mode, …}, results:{rawUrl, thumbnailUrl}, createdAt (epoch s)}}` plus a `[Resource link]` line. Non-terminal responses carry `poll_after_seconds`; `sync:true` makes the server poll up to ~25 s. `raw_data:true` → `{raw_data:{id, status, job_set_type:"seedance_2_5", display_name, result_url, min_result_url, h264_url, thumbnail_url (cdn.higgsfield.ai …_thumbnail.webp), result_json, text, meta, created_at, params, debug}}`.
- `jobs_wait {jobs:[{index, job_id}] (1–12), timeout_seconds 0–15}` → `{jobs:[{index, job_id, status, type, model, result_url, thumbnail_url}], summary:{total, completed, failed, active, errors}, all_terminal}`; when `all_terminal:false` wait `poll_after_seconds` and call again. Typical video jobs "~60–180 s"; 30 s 1080p clips can take longer (platform reports of 10+ min elsewhere).
- `show_generation_by_ids {jobs:[{index, job_id}] (1–60)}` renders a gallery widget (claude.ai); from Claude Code it is optional — `jobs_wait` already returns `result_url`. `show_generations {type, size, cursor}` and `job_display {id}` are for history only.
- Status values seen/declared: `completed`; the tools describe `failed` and non-terminal states (queued/in progress) with `poll_after_seconds`.
- **Result URL**: `https://d8j0ntlcm91z4.cloudfront.net/user_<uid>/hf_<YYYYMMDD>_<HHMMSS>_<job_id>.mp4` — public (HEAD 200 without auth), `Cache-Control: public, max-age=31536000, immutable`, no documented expiry (contrast: ModelArk deletes after 24 h). Download promptly anyway and record the job id in `80-generated\manifest.json`.

Polling loop for a batch of N clips: submit ≤ 12 per `generate_video_batch` → every 15 s `jobs_wait` on each group with `timeout_seconds:15` → when `all_terminal`, download every `result_url` → if `failed`, resubmit that index once with identical params (Higgsfield's rule: "Retry each failed generation position at most once").

## E. Downloading the mp4 to disk (no MCP download tool)

```python
# tools\hf_download.py  <url> <out.mp4>   (Python 3.12; requests 2.34 installed)
import sys, time, requests, subprocess, json
FFPROBE = r"C:\Users\Bulzart\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffprobe.exe"
url, out = sys.argv[1], sys.argv[2]
for attempt in range(4):
    try:
        with requests.get(url, stream=True, timeout=(15, 120)) as r:
            r.raise_for_status()
            expected = int(r.headers.get("Content-Length", 0))
            n = 0
            with open(out, "wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk); n += len(chunk)
        if expected and n != expected:
            raise IOError(f"short read {n}/{expected}")
        meta = json.loads(subprocess.check_output([FFPROBE, "-v", "error", "-show_streams", "-show_format", "-of", "json", out]))
        assert any(s["codec_type"] == "video" for s in meta["streams"]), "no video stream"
        print(json.dumps({"file": out, "bytes": n, "duration": meta["format"]["duration"]}))
        break
    except Exception as e:
        if attempt == 3: raise
        time.sleep(2 ** attempt)
```
PowerShell one-liner alternative: `Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing`. Always ffprobe the file (duration, 24 fps, mono AAC) before QA; Higgsfield outputs are H.264 mp4 even at 1080p (ModelArk's 10-bit HEVC caveat does not apply here).

## F. Error handling and retries

| Situation | Rule (from tool descriptions / Higgsfield workflow) |
|---|---|
| Transport timeout on `generate_video`/`_batch` | "the submission outcome may be unknown: do not automatically resubmit. Reuse returned job IDs and retry only after the original outcome is known" → check `show_generations {type:"video", size:5}` (newest first) and `transactions` for a matching spend before resubmitting |
| `unlim_choice` returned | nothing was submitted; ask the owner, resubmit the identical params with `use_unlim` set |
| `adjustments` / `recovery_tool` in a response | apply the adjustment and "immediately call any recovery_tool" (e.g. `show_plans_and_credits` when credits are insufficient) |
| Insufficient credits | stop the run, report the shortfall (cost table §A); never downgrade resolution silently |
| PUT ≠ 200 | do not `media_confirm`; request a fresh `media_upload` slot (URLs expire in 24 h, signed for one content-type) |
| `media_confirm` before upload | rejected/unusable media — confirm only after 200 |
| Job `failed` | refund appears in `transactions`; retry that index once with identical params; if it fails twice, mark the clip failed in `manifest.json` and continue with the others |
| Batch partial failure | keep the successful job ids, resolve unknown ones, retry only the affected indices |
| Rate limits | undocumented on Higgsfield; keep ≤ 12 concurrent submissions (one batch) per wave |
| Wrong role / unsupported param | server "may auto-coerce"; otherwise the error names the field — fix and resubmit (not a paid failure) |
| Edit misclassified (no trigger word) | Seedance-side semantics (`SEEDANCE-EDIT.md` §7); rewrite the prompt with "Video edit:"/"Replace only …" |

Persist every submitted `job_id` with its clip index in `80-generated\manifest.json` **before** polling so a crashed session can resume with `job_status`/`jobs_wait` instead of paying twice (same rule as the Miko workflow's run-manifest).

## G. Every Seedance model `models_explore` returns (search "seedance", type video; 2026-09-16)

| id | name | parameters | media roles | aspect ratios | tags / notes |
|---|---|---|---|---|---|
| `seedance_2_5` | Seedance 2.5 — "text-to-video, multimodal omni-reference generation, video edit, and video extension" | `mode` t2v/omni_reference/video_edit/video_extension (default t2v); `duration` 4–30 (5); `resolution` 480p/720p/1080p (720p); `generate_audio` true; `bitrate_mode` standard/high; `extension_mode` backward/forward (nullable) | start_image, end_image, image_references, video_references, audio_references | auto, 21:9, 16:9, 4:3, 1:1, 3:4, 9:16 | text-to-video, reference, identity, audio-reference, video-reference, video-edit, video-extension, 480p, 720p, 1080p; no `supports_unlim` |
| `ad_multiplier` | Ad Multiplier — "video generation powered by Seedance 2.5" | identical to `seedance_2_5` | identical | identical | used by the bundled `ad-multiplier` workflow with `mode:"video_edit"`, `generate_audio:false`, `duration_policy:"strict"`; the MCP instructions reserve it for "explicitly requested independent variants" |
| `seedance_2_0` | Seedance 2.0 — reference-driven, multi-SKU | `duration` 4–15 (5); `resolution` 480p/720p/1080p/4k (720p); `mode` std; `bitrate_mode`; `genre` auto/action/horror/comedy/noir/drama/epic; `generate_audio` true | start_image, end_image, image_references, video_references, audio_references | auto, 16:9, 9:16, 4:3, 3:4, 1:1, 21:9 | `supports_unlim: true`; 4k only here |
| `seedance1_5` | Seedance 1.5 Pro | `duration` 4/8/12 (4); `resolution` 480p/720p/1080p; `generate_audio` true | start_image, end_image | auto, 16:9, 9:16, 4:3, 3:4, 1:1, 21:9 | reliable, motion |

Related Higgsfield video models for our pipeline: `hf_mult_replace_object` and `hf_mult_motion_control` (Genjutsu; `resolution` only; roles image_references + video_references; no aspect list), `kling_video_edit` (`mode` std/pro/4k; roles video_references + image_references), `flux_3_video_edit`, `gemini_omni_flash_1_1` (`mode` edit), `video_upscale`, `bytedance_video_upscale` (1080p/2k/4k, 24–60 fps, presets incl. `ugc`), `topaz_video`, `video_deflicker`, `sam_3_video` (background removal), `sync_so` (lipsync). Full list in the session log (`models_explore list type video` returned 40 models, `has_more:false`).

## H. Worked examples

### H1 — one 15 s 9:16 clip, two product images + one source-frame reference (Stage 5 clip prompt, Mode 1/2 with product swap)

Preconditions: `product-front.png` → media_id `P1`, `product-label.png` → `P2`, `frame-clip03-start.png` (extracted from the original at the clip's first frame, used for composition only) → `P3`, all confirmed (§B).

```json
{"params": {
  "model": "seedance_2_5",
  "mode": "omni_reference",
  "prompt": "@Image 1 = our product, front view: use only its proportions, colours, cap and label layout; do not copy its background or lighting. @Image 2 = the same product's label close-up: use only the logo and wording. @Image 3 = composition and framing reference for the first frame: use only the camera position, shot size and the kitchen layout; do not copy the person, the product or the text in it.\nOne-sentence summary: a woman in a grey hoodie pours the drink from the bottle in @Image 1 over ice in a tall glass on a white kitchen counter, handheld phone video, UGC realism, natural window light from the left, kitchen room tone.\nSTART STATE (0 s): composition as in @Image 3; the bottle stands at the right of the glass, label facing the camera; her right hand rests on the counter.\n0-3s: she picks up the bottle with her right hand, label stays toward the camera; camera locked-off, medium shot. <cap twist and hiss>\n3-9s: she pours in one continuous motion; the orange liquid rises in the glass and turns pale orange where it meets the ice; light foam forms and settles; no spill. <pour and fizz>\n9-13s: she sets the bottle down at the same spot, label facing the camera, lifts the glass and takes one sip. <glass set down>\n13-15s: she looks into the lens and smiles; the frame holds for the last second.\nCAMERA: locked-off camera, fixed camera position, eye-level medium shot; the camera never moves. LIGHT & LOOK: soft daylight from the left, phone-camera texture, natural colours, HD, stable motion, no flicker.\nAUDIO: no dialogue; kitchen room tone, cap hiss, pour, glass contact; No BGM; generate only environmental sounds and action sounds. No subtitles.\nINVARIANTS: the bottle is one single object throughout with the exact label of @Image 2; exactly one glass; no extra hands or fingers; no text overlays, no logos other than the product label, no watermark.\nEND STATE (15 s): glass half full in her left hand, bottle standing at the right with label to camera, same framing, same light.",
  "medias": [
    {"value": "P1", "role": "image_references"},
    {"value": "P2", "role": "image_references"},
    {"value": "P3", "role": "image_references"}
  ],
  "duration": 15,
  "aspect_ratio": "9:16",
  "resolution": "720p",
  "generate_audio": true,
  "bitrate_mode": "high",
  "count": 1,
  "get_cost": true
}}
```
Run once with `get_cost:true` (expect 97.5 credits at 720p, 45 at 480p, 135 at 1080p), then resubmit without it (or as one `generate_video_batch` item with `index: 3`). If the first frame must be matched exactly instead of referenced, replace `P3`'s role with `start_image` and drop `P1/P2` (ModelArk forbids mixing first-frame and reference modes; Higgsfield behaviour is undocumented — test once before relying on it).

### H2 — video edit of a 15 s source segment (product swap in the original footage)

Preconditions: `seg-03.mp4` (15.00 s, 1080×1920, 30 fps, cut on hard cuts) → media_id `V1` (§B); `P1`, `P2` as above.

```json
{"params": {
  "model": "seedance_2_5",
  "mode": "video_edit",
  "prompt": "Video edit. Replace only the red 12 oz can held in the woman's left hand in @Video1 with the product from @Image1 (front view: exact proportions, colours, cap and label layout) and @Image2 (label close-up: logo and wording). Do not copy the background, lighting or surface of @Image1 or @Image2.\n0-15s: the replacement is the same single object throughout, at real-world size, held with the same grip and finger positions, following the same motion path and orientation changes; the liquid poured from it is orange and non-carbonated, so the pour is smooth with no fizz and the mix in the glass turns pale orange.\nRemove only the red-brand logo on the paper cup at the right of the counter and reconstruct the revealed surface consistently with its immediate surroundings.\nKeep everything else from @Video1 exactly the same: shots and cuts, camera moves, framing, the woman's face, hair, clothing, hands and performance, all other objects and their count, the kitchen, lighting, colour grading, pacing and timing. Preserve every caption, subtitle, and other untargeted on-screen text element from @Video1 exactly as it appears, including its wording, styling, placement, animation, and timing. Text physically attached to a replaced target follows that replacement.\nNo subtitles. No watermark. No extra products, no duplicated hands, no floating objects.",
  "medias": [
    {"value": "V1", "role": "video_references"},
    {"value": "P1", "role": "image_references"},
    {"value": "P2", "role": "image_references"}
  ],
  "duration": 15,
  "aspect_ratio": "auto",
  "resolution": "720p",
  "generate_audio": false,
  "bitrate_mode": "high",
  "count": 1
}}
```
Then: `jobs_wait` → download `result_url` → conform to 15.00 s and mux the original `seg-03.mp4` audio back (`SEEDANCE-EDIT.md` §5) → QC gates → frame QA. Expected cost 97.5 credits at 720p (billed by the 15 s source). Genjutsu alternative for the same job: `{"model":"hf_mult_replace_object","resolution":"720p","prompt":"Replace only the red can in the woman's left hand with the product from @Image1 and @Image2; keep every move, the grip, the camera, the captions and the audio.","medias":[{"value":"V1","role":"video"},{"value":"P1","role":"image"},{"value":"P2","role":"image"}]}` (≈ 104 credits for 15 s at 720p; original audio kept by the model).

## I. Open gaps

- Higgsfield's `video_edit` input caps (max length/size, trim behaviour of `_trim.mp4`) and whether `start_image` can be combined with `*_references` — undocumented; verify with one paid test each.
- Exact behaviour of `show_generation_by_ids` in a CLI client (widget-only?) — irrelevant because `jobs_wait` carries `result_url`.
- `video_extension` billing basis and Genjutsu per-second rounding — unverified.
- Result URL retention on CloudFront — no documented expiry; download immediately regardless.
