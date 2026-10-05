# Descript bridge — editable project through the Descript MCP (P2 = "CapCut + Descript project" or "CapCut + all exports"; CapCut is always the primary project)

The Python scripts cannot call MCP tools; this procedure is executed by the main session or the editor
agent. Everything it produces is recorded in `runs\<run-id>\90-postgen\project\descript\project.json`
and in `edit-plan.json → meta.projects.descript`. The ffmpeg render (`render_ffmpeg.py`) stays the
delivery file; Descript's published MP4 is a review link / alternative export.

> **Owner rule, repeated in every prompt sent to Descript: no captions.** Descript transcribes every
> import automatically (that is how it edits by text) — the transcript stays inside Descript and is never
> turned into on-screen captions, a caption track, or "Add captions" automation. Agent Underlord is told
> so explicitly (template below). The owner captions the final file afterwards with a separate tool.

Constraints found in `research\editing-tooling.md` §D (verified 2026-09-16): direct upload works
(`content_type` + `file_size`, PUT to the presigned `upload_url` with `Content-Type: application/octet-stream`,
size must match); Agent Underlord is non-deterministic and costs credits (model override available);
`export_timeline` never bundles media (relink to the local clips); `wait_for_job` waits at most 840 s per
call (call again); `download_url` expires (`download_url_expires_at`); compositions default to 1920x1080
so 1080x1920 @ 30 fps must be passed; drive verified: `75fa3661-691b-410c-9e41-a4fc5500f465`
("dropship ai's Drive"). Every clip is uploaded to Descript's cloud — do not use this path for material the
owner has not cleared for cloud storage.

## 0. Tools (discover, never hard-code beyond the `mcp__claude_ai_Descript__` connector)

`ToolSearch "select:mcp__claude_ai_Descript__get_drive_info,mcp__claude_ai_Descript__import_media,mcp__claude_ai_Descript__wait_for_job,mcp__claude_ai_Descript__get_project,mcp__claude_ai_Descript__prompt_project_agent,mcp__claude_ai_Descript__export_timeline,mcp__claude_ai_Descript__publish_project,mcp__claude_ai_Descript__report_upload_status"`

`get_drive_info {}` → confirm `drive_id` / `drive_name` before uploading anything.

## 1. Import the plan's media and create the composition (`import_media`)

Inputs: `edit-plan.json` (`clips[]` in `order`, `audio.music.path`, `audio.sfx[].path`). Use the clip
files the plan references (generated clips; or `90-postgen\project\media\clip-NN.mp4` if a normalised
copy exists). File sizes from `(Get-Item <path>).Length`.

```json
{
  "project_name": "<run-id> edit",
  "team_access": "edit",
  "add_media": {
    "clip-01.mp4": {"content_type": "video/mp4", "file_size": 10182723, "language": "en"},
    "clip-02.mp4": {"content_type": "video/mp4", "file_size": 5017820, "language": "en"},
    "clip-04.mp4": {"content_type": "video/mp4", "file_size": 5470324, "language": "en"},
    "music/bed.wav": {"content_type": "audio/wav", "file_size": 3456789}
  },
  "add_compositions": [
    {"name": "<run-id> 9x16", "width": 1080, "height": 1920, "fps": 30,
     "clips": [{"media": "clip-01.mp4"}, {"media": "clip-02.mp4"}, {"media": "clip-04.mp4"}]}
  ]
}
```

Rules: one `add_media` key per kept clip, **in plan order**, keys = the local file names (the reimport
matches by basename); dropped clips (QA S3/S4) are not uploaded; music only when
`audio.music.path` is a licensed file (a trending sound with `attach_in_app: true` is never uploaded);
SFX files may be added as media but are placed by Underlord (step 3) or left to the ffmpeg render.
Response: `job_id`, `project_id`, `project_url` (show it to the owner), `upload_urls{key → {upload_url, asset_id, artifact_id}}`.

## 2. Upload the bytes (PowerShell, PATH refresh first)

```powershell
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
Invoke-WebRequest -Uri '<upload_url for clip-01.mp4>' -Method Put -InFile 'C:\...\80-generated\clip-01.mp4' -ContentType 'application/octet-stream' -UseBasicParsing -TimeoutSec 900
```

One PUT per key; HTTP 200 expected. A failed PUT → `report_upload_status {job_id, media_id: "<key>", status: "failed", detail: "<http error>"}`
so the import job stops waiting on that file (others continue). Then `wait_for_job {job_id}` until
`job_state = "stopped"` and `result.status = "success"` (re-call on `wait_status = "still_running"`).
Descript transcribes on import — expected, internal, never rendered.

## 3. Apply the edit plan with Agent Underlord (`prompt_project_agent`)

`get_project {project_id}` → `compositions[0].id` (the 9:16 composition). Then:

```json
{"project_id": "<project_id>", "composition_id": "<composition_id>", "model": "claude-sonnet",
 "prompt": "<filled template>"}
```

Prompt template (fill from `edit-plan.json`; keep every sentence of the NO-CAPTIONS block verbatim):

```
You are finishing a 9:16 (1080x1920, 30 fps) short-form edit from the clips already on this composition. Apply EXACTLY the following and nothing else.

ORDER AND TRIMS (source seconds of each clip file):
1. clip-01.mp4  keep 0.00–4.00
2. clip-02.mp4  keep 2.00–7.00
3. clip-04.mp4  keep 3.00–8.00
Remove every other part of these clips from the timeline. Do not add, reorder or repeat clips beyond this list.

TRANSITIONS: hard cuts everywhere except: crossfade 0.4 s between clip-02.mp4 and clip-04.mp4.
SPEED: clip-03 piece 2.00–5.00 at 1.5x (only if listed in the plan's speed_ramps; otherwise say "no speed changes").
TEXT OVERLAYS (these are the ONLY text elements allowed):
- Hook text "Wait for the pour" from 0.0 s to 1.8 s, top third of the frame, centred, bold sans (Montserrat ExtraBold or similar), white with a thick black outline, inside the safe area (at least 270 px from the top, 65 px from the sides, nothing in the right 165 px column).
- End card "SNOW SCENTS / Link in bio" from 15.6 s to 17.6 s, centred vertically.
MUSIC: <"none — the sound is attached in the platform at posting" | "bed.wav at −18 dB under the clip audio, ducked under any speech">.
AUDIO: keep the clips' own audio at its level; do not remove filler words, do not apply Studio Sound, do not add voiceover.

NO CAPTIONS — MANDATORY: Do not add captions or subtitles of any kind. Do not run automatic captions, do not create a caption track, do not place transcript text, lower thirds or word-by-word text on the video. The only text on screen is the TEXT OVERLAYS listed above. Do not add stock media, effects, filters, or scene changes.

When done, reply with the final timeline: every clip with its in/out points, transitions, and the text elements present.
```

`wait_for_job {job_id}` (show `progress.label` to the owner while it runs). Underlord is
non-deterministic: after it stops, `get_project` and read its reply; if anything beyond the list was
added (captions, stock media), send one corrective `prompt_project_agent` ("Remove X; keep everything else")
— never more than two correction rounds, then fall back to the ffmpeg render and the CapCut/OTIO projects.

## 4. Export the timeline for the re-edit loop (`export_timeline`)

```json
{"project_id": "<project_id>", "composition_id": "<composition_id>", "format": "premiere",
 "include_markers": true, "snap_frame_rates": true}
```

| `format` | File | Import back with | Opens in |
|---|---|---|---|
| `premiere` | Premiere Pro XML (FCP7-style `.xml`) | `reimport_otio.py <file>.xml` (adapter `fcp_xml`) | Premiere Pro |
| `davinci_resolve` | Resolve XML (`.xml`, FCP7 flavour) | `reimport_otio.py <file>.xml` | DaVinci Resolve |
| `fcp` | `.fcpxml` | `reimport_otio.py <file>.fcpxml` (adapter `fcpx_xml`; `create_track_per_file` must stay false) | Final Cut Pro |
| `edl` | CMX 3600 `.edl` | `reimport_otio.py <file>.edl` (video track only) | any NLE, Reaper |
| `aaf` / `sesx` | binary AAF / Audition | not re-imported (audio tools) | Pro Tools, Logic, Audition |

`wait_for_job` → `result.download_url` (expires at `result.download_url_expires_at`) →
`Invoke-WebRequest -Uri '<download_url>' -OutFile 'C:\...\90-postgen\project\descript\timeline-premiere.xml' -UseBasicParsing`.
Media is never bundled: `reimport_otio.py` matches clips by file name to the plan's local paths, then
`render_ffmpeg.py` re-renders locally. Descript's own text layers do not survive the XML (titles are
NLE-specific); the plan's `text_overlays` stay the source of truth.

## 5. Optional review link / alternative export (`publish_project`)

```json
{"project_id": "<project_id>", "composition_id": "<composition_id>", "resolution": "1080p", "access_level": "unlisted", "media_type": "Video"}
```

`wait_for_job` → `result.share_url` + `result.download_url` — show both to the owner. Publishing the same
composition again reuses the share URL. This MP4 is not loudness-normalised or graded like the ffmpeg
render; if it is to be posted, run the final check on it too (`90-postgen\final-check.md`).

## 6. Record (`90-postgen\project\descript\project.json`)

```json
{"drive_id": "75fa3661-691b-410c-9e41-a4fc5500f465", "project_id": "…", "project_url": "https://web.descript.com/…",
 "composition_id": "…", "imports": {"clip-01.mp4": {"asset_id": "…", "bytes": 10182723, "status": "uploaded"}},
 "underlord": [{"job_id": "…", "model": "claude-sonnet", "prompt_sha1": "…", "result_summary": "…"}],
 "exports": [{"format": "premiere", "file": "90-postgen/project/descript/timeline-premiere.xml", "downloaded": "2026-09-16T22:10:00-05:00"}],
 "publish": {"share_url": "…", "download_url": "…", "resolution": "1080p", "access_level": "unlisted"},
 "no_captions": "Underlord was instructed not to add captions; verified in get_project + reply", "updated": "…"}
```

Then set `edit-plan.json → meta.projects.descript = "90-postgen/project/descript/project.json"` and add the
project URL to `70-deliverables\DELIVERABLES.md`.

## Failure handling

- `import_media` 4xx on `folder_name`/`workspace_name`: retry without them (they need shared team access).
- Upload size mismatch → 4xx from storage: recompute `file_size`, re-run step 1 for that key only (new `project_id` is NOT needed: pass `project_id` and omit `add_compositions`, then `update_compositions` with `append_clips`).
- `publish_project` 422 "no video content": the composition is empty — Underlord removed the clips; re-run step 3 from `get_project`'s state or rebuild from the plan with a fresh composition (`import_media` with `project_id` + `add_compositions`).
- Credits/quota errors from `prompt_project_agent`: stop, report, continue with the CapCut/OTIO projects (the ffmpeg render never depends on Descript).
