## 1. Prepared by this session before any agent starts (command A9)
- **Per video:**
  - the plan `40-briefs/video-NN-plan.md` and the brief `40-briefs/video-NN-brief.md`;
  - the pattern card and request(s) `50-requests/video-NN[-cK]-request.json`, preflighted once.
- **Recreate only:** the pick's prepared source in `10-media/<V>/own/`, from `T strip-inserts`.
  `map.json` there holds the split points, and the folder also holds the 9:16 copy. Whatever the model, the original
  reference (the original's `videos_without_audio` copy, or the prepared copy when it was cut, flipped or padded;
  `generation-system.md` §4b.5) is uploaded silent and is the only video reference: nothing that places the
  product rides beside it.
- **The run's agent contract:** `50-requests/agent-contract.md`, generated from the §2 prompt at A9
  (never copied from an earlier run).
- **Shared, in `state.json`:**
  - `higgsfield.folder_id`;
  - `assets.uploads`: media ids of every shared asset, plus Element ids;
  - `long_videos.NN`: the permissions;
  - `analyze_submode` (`recreate`, `create` or `free`; a Free run also `free_references`, `videos_kind` per video and `free_plan_confirmed`), `model`, `qc_fixes` (`ask` or `auto`; the contract's "QC fixes" line), `loupe` (`up` or `down`; the contract's "Loupe" line),
    `audio_ingest` (`whisper` or `frames-only`; the contract's "Audio ingest" line), `voiceover` (the method, the voice, the language,
    the preference and every take in `voiceover.files`, `30-assets/voiceover/`; the contract's "Voiceover" line, item 31), `memes`
    (Create: `include` or `none`, none set = `include`; the contract's "Memes" line, item 32).

