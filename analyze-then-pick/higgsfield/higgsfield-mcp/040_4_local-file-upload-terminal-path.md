## 4. Local file upload (terminal path)

```text
1. mcp__higgsfield__media_upload {files:[{filename:"<name>.png", content_type:"image/png"}, …]}   (≤ 20 per call)
   → uploads[i] = {upload_url (S3 presigned PUT, ~24 h), media_id (UUID), url (public CDN URL), content_type}
2. python atp.py hf-put --file "<local path>" --url "<upload_url>" --content-type "<exact content_type from step 1>"
   → {"ok": true, "status": 200}
3. mcp__higgsfield__media_confirm {type:"image", media_ids:[…]}   (one media type per call; only after HTTP 200)
```

- `Content-Type` is part of the signature and must equal the returned `content_type`. A mismatch returns
  S3 403 `SignatureDoesNotMatch`; request a fresh slot [VERIFIED in the 2026-09-16 research].
- Types: jpg/jpeg → `image/jpeg`, png → `image/png`, webp → `image/webp`, mp4 → `video/mp4`,
  mov → `video/quicktime`, mp3 → `audio/mpeg`, wav → `audio/wav`.
- Keep the returned `url`: Elements need both the `id` and the `url` (§6).
- Completed job ids (e.g. a generated start frame) can be passed directly as `medias[].value` without
  re-uploading [HF-DOC].
- Uploaded videos may be normalised server-side (stored params showed a `_trim.mp4` suffix) [VERIFIED].
- **Videos are uploaded without audio** (Edit Mode and Analyze Recreate; Analyze Create uploads no
  reference video at all). `atp.py split-audio` writes a silent copy of every original
  into `<given path>/videos_without_audio/` and its audio into `<given path>/files_audio/`. Only the
  silent copies (or their prepared derivatives) go to Higgsfield, which lowers the chance of
  moderation flags. Edit Mode finals get the original audio back with `atp.py restore-audio --audio`.
- Before uploading, prepare the input:
  - convert HEIC/AVIF to PNG/JPEG;
  - keep reference images ≤ 4K and < 30 MB;
  - put product cut-outs on a neutral background unless transparency is needed;
  - crop or trim source videos to the segment being edited (4–30 s for Seedance 2.5 / Genjutsu edits).

