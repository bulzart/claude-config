# generator — agent brief (Stage 7g; runs ONLY after G1 = "Generate all now" or "Generate clip 1 first as a test"; modes `all` | `test` | `chained` | `regenerate`)

Load first: `LAYOUT.md`, `references\generation-playbook.md` (the procedure this brief follows), `research\higgsfield-mcp.md`
(verified call shapes, parameter tables, polling, download, error rules), `seedance\SEEDANCE-EDIT.md` §5 (mux
recipe and QC gates), §8 (credits), `seedance\SEEDANCE-SPEC.md` §11.2 (Higgsfield parameter sheet),
`references\post-generation-playbook.md` §1 (manifest format), `tools\README.md` if present.

## Purpose
Upload every attachment the prompts cite (once), submit each confirmed prompt with the right mode and
parameters, poll, download, verify, conform/mux edit segments, write the manifest and the cost log —
and never submit more clips than the owner confirmed.

## Inputs
`50-prompts\prompts.json` (the `prompt` text, `references[]` in order, per-item parameters), `70-deliverables\references\`
(files), `70-deliverables\prompts-final.md`, `75-generation\uploads.json` and `jobs.json` if they exist (resume),
Notes: MCP prefix (`mcp__higgsfield__` or `mcp__claude_ai_Higssfield__`), confirmed count ("all" | "test = item 1" |
a list of item numbers for `regenerate`), resolution, `chained: yes|no`. `regenerate` mode: `90-postgen\fix-prompts.md` blocks.

## Outputs
`75-generation\uploads.json`, `75-generation\jobs.json`, `75-generation\generation-log.md`, `80-generated\clip-NN.mp4`
(replication) or `80-generated\seg-NN-edit.mp4` → conformed `80-generated\seg-NN.mp4` (+ `joined.mp4` via `join_clips.py`),
`80-generated\manifest.json`, `state.json` (`stage=generating` → `generated`, `next_step=clip-qa`).

## Method — the exact MCP sequence
0. Discover tools: `ToolSearch "select:<P>balance,<P>media_upload,<P>media_confirm,<P>generate_video,<P>generate_video_batch,<P>jobs_wait,<P>job_status,<P>show_generations,<P>transactions,<P>show_medias"`
   with `<P>` = the prefix from Notes (try both prefixes if unknown; the one that returns schemas wins). Log the prefix.
1. Balance: `<P>balance {}` → log credits; compute the wave's estimate from `prompts.json` (rates 480p 3 · 720p 6.5 ·
   1080p 9 credits/s; edit segments by `ceil(source_s)`); if `estimate × 1.5 > balance` → stop and report (no submit).
2. Idempotent uploads (`uploads.json`, keyed by sha256 of the file):
   a. for each cited file not yet `confirmed`: `<P>media_upload {files:[{filename, content_type}], method:"upload_url"}` (≤ 20 per call);
   b. PUT (PowerShell, PATH refresh first): `Invoke-WebRequest -Uri $uploadUrl -Method Put -InFile '<abs file>' -ContentType '<content_type returned>' -UseBasicParsing -TimeoutSec 600`
      — the Content-Type must equal the returned value (signed header); videos: ffprobe first (mp4, ≤ 200 MB, 4–30 s for edits, 300–6000 px, ratio 0.4–2.5, 24–60 fps);
   c. only after HTTP 200: `<P>media_confirm {type:"image"|"video"|"audio", media_id}` → `status:"uploaded"`; write the row `{file, sha256, type, content_type, media_id, status:"confirmed", uploaded_at}` immediately;
   d. PUT ≠ 200 → new `media_upload` slot; never confirm an unuploaded id; never reuse a presigned URL.
3. Preflight one representative item per (mode, duration, resolution): `<P>generate_video {params:{…item params…, get_cost:true}}` → credits; log estimate vs table.
4. Submit (params copied from `prompts.json`, never retyped; `medias[]` = the item's references in order with `value:<media_id>`):
   - replication: `{model:"seedance_2_5", mode:"omni_reference"|"t2v", prompt, medias:[{value, role:"image_references"|"video_references"|"audio_references"|"start_image"|"end_image"}], duration:<int>, aspect_ratio:"9:16", resolution:"1080p", generate_audio:true, bitrate_mode:"high", count:1}`
   - edit: `{model:"seedance_2_5", mode:"video_edit", prompt, medias:[{value:<segment id>, role:"video_references"}, {value:<image ids>, role:"image_references"}…], duration:<ceil(source_s)>, aspect_ratio:"auto", resolution:"1080p", generate_audio:false, bitrate_mode:"high", count:1}`
   - `test` → one `<P>generate_video {params}`; `all` → `<P>generate_video_batch {requests:[{index, params}]}` in waves of ≤ 12 with one global index; `chained` → serial (playbook §4.8: previous clip's last frame uploaded as `start_image`, preflight the first chained call with `get_cost:true`);
   - write `jobs.json` rows `{index, item_no, kind, job_id, params, status:"submitted", submitted_at, credits_estimated, credits_charged:null, result_url:null, file:null, attempts:1}` BEFORE any poll;
   - HARD STOP: submitted items ≤ the confirmed count; `unlim_choice` → nothing submitted → stop and report; transport timeout → do NOT resubmit; check `<P>show_generations {type:"video", size:12}` + `<P>transactions {size:25}` first.
5. Poll: `<P>jobs_wait {jobs:[{index, job_id}…], timeout_seconds:15}` every 15 s (honour `poll_after_seconds`) until `all_terminal:true`; single job: `<P>job_status {jobId}`; append every poll summary to `generation-log.md`.
6. Download + verify: `python C:\Users\Glaresquare1\.claude\analyze-stack\tools\download.py "<result_url>" --out "<run>\80-generated\clip-NN.mp4" --probe`
   (fallback: `Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing` then ffprobe); verify video stream, duration ±0.5 s of the plan (edits: ≤ 0.4 s shorter), fps 24, audio present/absent as requested.
7. Edit segments: download as `80-generated\seg-NN-edit.mp4`, conform + mux (`SEEDANCE-EDIT.md` §5 recipe with `-t <source_s>`, `apad`/`atrim`, `seg-NN-audio.mka`) → `80-generated\seg-NN.mp4`; QC gates (duration within max(1/fps, 0.10) s, aspect within 1.5 %, short edge within 8 px, AAC present) — a too-short segment is `failed`, never frame-frozen; then
   `python C:\Users\Glaresquare1\.claude\analyze-stack\tools\join_clips.py --clips "<run>\80-generated\seg-01.mp4" "<run>\00-input\segments\seg-02.mp4" … --out "<run>\80-generated\joined.mp4" --width <src w> --height <src h> --fps <src fps>`
   (explicit order; passthrough segments come from `00-input\segments\`; replication clips: `--run-dir "<run>" --out …` uses the manifest order).
8. Failures: job `failed` → retry that index once with identical params (refund appears in `transactions`); failed twice → manifest `status:"failed"`, continue; `adjustments`/`recovery_tool` → apply and call it; insufficient credits → stop the wave and report the shortfall (never lower the resolution silently); wrong role/param → fix and resubmit (unpaid); an edit misclassified as reference/extension → report to the main session for the edit-prompt writer, not a retry.
9. Manifest + cost: `80-generated\manifest.json` (`generator:"seedance-2.5 via Higgsfield"`, per clip `prompt_no, prompt_file, file, duration_s, width, height, fps, audio, generation_id:<job_id>, mapping_source:"manifest"`); `<P>transactions {size:50}` → `credits_charged` per job, wave totals and refunds into `generation-log.md`.
10. `state.py "<run>" set stage=generated next_step=clip-qa` and `add-file 80-generated …`; `test` mode → `next_step=G1-remaining` and extract the test clip's QA frames (`python …\tools\clip_frames.py "<clip>" --out "<run>\90-postgen\qa\clip-01"` → `sheet.jpg`).
   `chained` mode: the previous clip's last frame is `90-postgen\qa\clip-NN\last-<t>.jpg` from the same script.

## Quality bar
- Every job id is on disk before it is polled; every upload is reusable on resume.
- No clip beyond the confirmed count; no paid call before the balance/preflight checks are logged.
- Every downloaded file is ffprobe-verified and named by its prompt number.

## When evidence is missing
Unknown tool prefix → try both; neither present → report "Higgsfield MCP not connected" (install steps in
`research\higgsfield-mcp-install.md` §4) and stop. Missing `download.py`/`join_clips.py` → use the
PowerShell/ffmpeg fallbacks named above and log it. Never guess a media_id or a job status.
