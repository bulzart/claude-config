## 7. Uploading the take (X3)

**native** and **lipsync** upload the take (an on-camera **lipsync** video needs its media id for the sync pass; a native one rides it as
Audio 1): `media_upload {files:[{filename:"<the take's file name>", content_type:"audio/mpeg"}]}` (a WAV: `audio/wav`) →
`T hf-put --capture <id> --file <the take>` → `media_confirm {type:"audio", media_ids:[…]}` (the media type of the file) →
`T uploads set --run RUN --video NN --label "Audio 1" --role audio_references --media-id <id> --file <the take> --content-type audio/mpeg`.
The silent-video rule of X3 is about videos: the take is the one audio input. A retake (§4) is a new upload; a regeneration reuses the media
id. **overlay** never uploads the take.

