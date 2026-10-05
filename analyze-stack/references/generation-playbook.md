# Generation playbook — G1 gate, cost estimate, Higgsfield MCP procedure, hand-off document (Stage 7g)

OWNER RULE: Higgsfield generation is OPTIONAL per run. Nothing is generated or spent before the owner
answers G1 with the cost estimate in front of them. "I will generate myself" ends the run with the
prompts (+ reference bundle + sliced source segments for the edit approach) until clips are dropped
back. Every attachment the prompts cite is uploaded and attached; never more clips than confirmed.
Sources: `research\higgsfield-mcp.md` (verified call sequence, parameters, polling, download, errors),
`seedance\SEEDANCE-EDIT.md` §5, §8, §10, `SEEDANCE-SPEC.md` §11.2.

## 1. Discovering the MCP tools (never hard-code the prefix)

`ToolSearch "select:mcp__higgsfield__balance,mcp__claude_ai_Higssfield__balance"` — whichever exists
is the prefix `P` for this run (`mcp__higgsfield__` = user-scope server; `mcp__claude_ai_Higssfield__`
= claude.ai connector). Then load with one `select:` per tool needed: `balance`, `transactions`,
`models_explore`, `media_upload`, `media_confirm`, `show_medias`, `generate_video`,
`generate_video_batch`, `jobs_wait`, `job_status`, `show_generations`. If neither prefix exists: tell
the owner Higgsfield is not connected (install steps in `research\higgsfield-mcp-install.md` §4) and
offer "I will generate myself" only.

## 2. Cost estimate for G1 (main session, read-only calls only)

1. `P balance {}` → `{credits, subscription_plan_type}`.
2. Rates (credits per second, `seedance_2_5`, any mode — from `SEEDANCE-EDIT.md` §8 / `higgsfield-mcp.md` §A,
   observed 2026-09-16): 480p 3 · 720p 6.5 · 1080p 9. $0.05 per credit.
3. Per item: replication clip → `rate(resolution) × duration_s`; edit segment → `rate × ceil(source_duration_s)`
   (billed by the source video's duration); passthrough segments cost 0.
4. Total = Σ items; show also the two other resolutions in DELIVERABLES.md's cost table.
5. **Authoritative preflight**: `P generate_video {params:{…exact params of one representative item…, get_cost:true}}`
   returns the credits without submitting (not allowed inside `generate_video_batch`) — run it for one
   item per distinct (mode, duration, resolution) and scale; if it disagrees with the table, the
   preflight wins and the table note is updated in `75-generation\generation-log.md`.
6. Budget rule: `total × 1.5 (retry allowance) ≤ balance`, else G1 still asks but the question's
   `{credits}` text is followed by "— exceeds 2/3 of the balance; a lower resolution or fewer clips is
   recommended" inside the placeholder value (wording of the question itself unchanged).
7. Default resolution for the estimate: the platform's native delivery (9:16 → 1080p; the clip is
   1080×1920, H.264 on Higgsfield). The owner may answer G1 via "Other" with a different resolution;
   then re-estimate and re-ask G1.

G1 placeholders: `{n}` items (non-passthrough), `{clips | edit segments}`, `{total}` s, the
approach-specific sentence, `{credits}`, `{balance}`, `{model id}` = `seedance_2_5` (Higgsfield id for
Seedance 2.5 per the spec notes §11.2), `{resolution}`, `{aspect}` (9:16 or "source ratio (auto)" for edits).

## 3. Attachment bundle (already on disk after Stage 7)

`70-deliverables\references\`: product images (`product-*.jpg/png`), cited frames
(`clip-NN-start-<t>.jpg`, `clip-NN-shot-K-<t>.jpg`), cited motion slices (`clip-NN-move-<t1>-<t2>.mp4`),
style refs, voice refs, and for the edit approach the source segments `seg-NN.mp4` (+ `seg-NN-audio.mka`
for the mux). The enhanced prompt text is the `prompt` field of `prompts.json` (= the `## Prompt`
block of each clip/edit file). The generator attaches exactly the files listed in each item's
`references[]`, in that order.

## 4. Generator procedure (generator agent; one agent per wave of ≤ 12 items, or one per item for chained runs)

### 4.1 Idempotent uploads → `75-generation\uploads.json`
```json
{"schema":"analyze-stack.uploads/1","prefix":"mcp__claude_ai_Higssfield__","items":[
 {"file":"70-deliverables/references/product-front.jpg","sha256":"…","type":"image","content_type":"image/jpeg","media_id":"aab7a7ad-…","status":"confirmed","uploaded_at":"…"}]}
```
For every distinct file cited by the confirmed items (by sha256): if `uploads.json` has it with
`status: confirmed` → reuse the `media_id`; else
1. `P media_upload {files:[{filename, content_type}], method:"upload_url"}` (≤ 20 per call) → `upload_url`, `media_id`, `content_type`;
2. PUT the bytes (PowerShell, PATH refresh first):
   `Invoke-WebRequest -Uri $uploadUrl -Method Put -InFile '<abs path>' -ContentType '<content_type returned>' -UseBasicParsing -TimeoutSec 600`
   (the Content-Type must equal the returned one — signed header; mismatch → 403);
3. only after HTTP 200: `P media_confirm {type:"image"|"video"|"audio", media_id}` → `status:"uploaded"`; write the row with `status:"confirmed"` immediately;
4. PUT ≠ 200 → request a fresh slot; never confirm an unuploaded id.
Segments/videos: mp4 ≤ 200 MB, 4–30 s (edit), 300–6000 px, ratio 0.4–2.5, 24–60 fps — verified with ffprobe before upload.

### 4.2 Submit → `75-generation\jobs.json` (persist BEFORE polling)
Per item, params from `prompts.json` (never retyped):
- replication clip: `{model:"seedance_2_5", mode:"omni_reference" (or "t2v" when no references), prompt, medias:[{value:<media_id>, role:"image_references"|"video_references"|"audio_references"|"start_image"|"end_image"} in the item's references order], duration:<int>, aspect_ratio:"9:16", resolution:"1080p", generate_audio:true, bitrate_mode:"high", count:1}`
- edit segment: `{model:"seedance_2_5", mode:"video_edit", prompt, medias:[{value:<segment media_id>, role:"video_references"}, {value:<image ids>, role:"image_references"}…], duration:<ceil(source_s)>, aspect_ratio:"auto", resolution:"1080p", generate_audio:false, bitrate_mode:"high", count:1}`
- ≤ 12 items → one `P generate_video_batch {requests:[{index, params}]}`; more → several batches, one global index; a single test clip → `P generate_video {params}`.
- `jobs.json` row: `{index, item_no, kind, job_id, params, status:"submitted", submitted_at, credits_estimated, credits_charged:null, result_url:null, file:null, attempts:1}` — written right after the response, before any poll.
- `unlim_choice` in the response = nothing submitted → stop and report to the main session (owner decides `use_unlim`); transport timeout → do NOT resubmit; check `P show_generations {type:"video", size:12}` and `P transactions {size:25}` for a matching job/spend first.
- HARD STOP: the number of submitted items never exceeds the count the owner confirmed at G1 ("all" = every non-passthrough item; "test" = item 1 only).

### 4.3 Poll
`P jobs_wait {jobs:[{index, job_id}…], timeout_seconds:15}` every 15 s until `all_terminal:true`
(`poll_after_seconds` honoured); `job_status {jobId}` for a single job. Statuses: completed / failed /
queued / in progress. Append every poll summary line to `75-generation\generation-log.md`.

### 4.4 Download + verify → `80-generated\`
`python C:\Users\Glaresquare1\.claude\analyze-stack\tools\download.py "<result_url>" --out "<run>\80-generated\clip-NN.mp4" --probe`
(streaming, retries with back-off, Content-Length check, `--probe` = ffprobe requires a video stream; then check
duration, fps 24, audio as requested). Edit segments land as `80-generated\seg-NN-edit.mp4`; then conform + mux
(`SEEDANCE-EDIT.md` §5 recipe: `-t <source_s>`, `apad`/`atrim`, source `seg-NN-audio.mka`) → `80-generated\seg-NN.mp4`;
QC gates: duration within max(1/fps, 0.10) s of the source, aspect within 1.5 %, short edge within 8 px of the
target, AAC audio present — a segment shorter than the source beyond the tolerance is `failed`, never
frame-frozen. Then `python …\tools\join_clips.py --clips <seg-01.mp4> <00-input\segments\seg-02.mp4 (passthrough)> … --out "<run>\80-generated\joined.mp4" --width <w> --height <h> --fps <fps>`
→ `joined.mp4` (edit approach; explicit order). Replication previews: `join_clips.py --run-dir "<run>" --out …` (manifest order).

### 4.5 Manifest + cost log
`80-generated\manifest.json` (format in `post-generation-playbook.md` §1; `generation_id` = job_id,
`mapping_source: "manifest"`, `seed: null`). Credits: `P transactions {size:50}` after the wave;
match rows by time/display_name; write `credits_charged` per job and the wave total into
`generation-log.md` (`estimated vs charged`, refunds for failed jobs).

### 4.6 Failures and retries
Job `failed` → retry that index ONCE with identical params (refund appears in `transactions`); failed
twice → `manifest.json` marks the clip `failed` and the run continues; `adjustments`/`recovery_tool` in a
response → apply and call the recovery tool; insufficient credits → stop the wave, report the shortfall
(never lower the resolution silently); wrong role/param error → fix and resubmit (unpaid); an edit
misclassified (no trigger word) → back to the edit-prompt writer, not a generator retry.

### 4.7 Test-clip flow (G1 = "Generate clip 1 first as a test")
Upload only clip 1's attachments, submit item 1, download, extract QA frames
(`python …\tools\clip_frames.py "<clip>" --out "<run>\90-postgen\qa\clip-01"` → `sheet.jpg`), and return. The main session shows the frames/contact sheet path and asks G1 again for the remaining
items with the updated estimate (`{n}` = remaining), after any fix the owner wants applied to the prompts.

### 4.8 Chained generation (only when the owner asked for chaining)
Serial: after item N completes, `clip_frames.py "<clip>" --out "<run>\90-postgen\qa\clip-NN"` → `last-<t>.jpg`, upload it,
and submit item N+1 with `{value:<id>, role:"start_image"}` (first-frame mode: aspect_ratio auto; drop
other image refs — ModelArk forbids mixing; Higgsfield behaviour undocumented, so the first chained
submission is preflighted with `get_cost:true` and, if refused, falls back to `image_references` + the
"exact first frame" sentence).

## 5. "I will generate myself" — `70-deliverables\GENERATE-YOURSELF.md`

```markdown
# Generate yourself — <run-id> · Seedance 2.5 · N items · approach: replicate | edit
Platform parameter sheets: seedance\SEEDANCE-SPEC.md §11 (ModelArk / fal / Replicate / WaveSpeed / Krea / Higgsfield UI).
Warning: ModelArk rejects reference images/videos with real human faces (spec §3.2); the cited frames/segments below contain people — use Higgsfield, Dreamina, fal, Replicate or WaveSpeed for those, or drop the frame reference.
Order: generate in item order; each item lists its handoff. Drop the results back in the chat as clip-NN.mp4 (or any name — I will ask you to confirm the mapping, question P1).

## Item 1 — clip 01 — 13 s — omni_reference — 9:16 — 1080p — audio on
Upload, in this order: 
  1. 70-deliverables\references\product-front.jpg  (→ @Image 1)
  2. 70-deliverables\references\product-label.jpg  (→ @Image 2)
  3. 70-deliverables\references\clip-01-start-00m00.00s.jpg  (→ @Image 3)
Parameters: duration 13 · ratio 9:16 · resolution 1080p · generate_audio true · (Higgsfield: mode omni_reference, bitrate_mode high)
Prompt (copy verbatim):
```
<prompt text>
```
Expect: 13 s, ends on <end state summary>. Next item starts from that state.

## Item 2 — edit segment 02 — source 00-input\segments\seg-02.mp4 (15.000 s) — video_edit — ratio auto — 1080p — audio OFF (mux the original back: SEEDANCE-EDIT.md §5)
…
```
The reference bundle is copied (not linked) into `70-deliverables\references\` so the folder can be
zipped as is. `state.json`: `stage: "awaiting-generation"`, `next_step: "drop generated clips in chat"`.
