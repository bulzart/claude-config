## 3. Standard execution sequence for one video

Every video is a **lane** with one job in flight. Inside a lane, finish, download and QC each clip
before submitting the next.
- **Edit Mode** runs one video at a time.
- **Analyze Mode** runs one production agent per video, at most 5 at once
  (`reference/production-agents.md`).
- The ledger caps the run at `production.max_parallel_jobs` (5) jobs in flight.

1. **Model entry.** Read `models/index.json` for the selected `model_id`, then read its guide.
   Call `models_explore {action:"get", model_id}` once per run. If the live parameters, roles or ranges
   differ from the guide, the live catalog wins; note the drift in the run log.
2. **Project folder, once per run.** `list_workspaces` → the `is_selected` workspace. Then
   `create_project {name:"atp <run-id>", workspace_id, idempotency_key:"<run-id>"}` and store
   `project_id` and `default_folder_id` in `state.json`. Retry an uncertain create only with the same
   idempotency key.
3. **Inputs.** Upload each needed file once per run (§4) and store `{local path, sha1 → media_id, url}`
   in `state.json → assets.uploads`. Reuse media ids and completed job ids across videos.
4. **Params.** Assemble them from the model guide's call recipe:
   - `model`, `prompt`, `medias[{value: media_id | job_id, role}]`
   - `duration`, `aspect_ratio:"9:16"` and the model's own 720p setting (§7)
   - the model-specific parameters, and `folder_id`
   `medias[].value` is **never a URL** [HF-TOOL].
5. **Preflight.** `generate_video {params:{…, get_cost:true}}` → `{cost:{credits}, adjustments}`
   [VERIFIED]. Read `adjustments`: it names every parameter the server defaulted or changed. If it
   changed something that matters (e.g. audio default, duration clamp), fix the params and preflight
   again. Show the cost in the per-video brief.
6. **Submit (ledger-guarded).** Run `atp.py ledger begin --run <run> --video NN --attempt K
   --request <request.json>` first.
   - Exit 3 means **do not submit**: an open job must be resolved first, the request duplicates a
     finished job, or the request already failed twice.
   - Otherwise make exactly one `generate_video {params:{…}}` call, with `get_cost` removed and
     `count` 1.
   - Immediately record the job id with `atp.py ledger set --fingerprint F --job J --status
     submitted`, or `--status unknown` if no job id came back, **before** polling.
   - Nothing is ever submitted in parallel or "just in case".
   - `unlim_choice` in the response → nothing was submitted; ask the user its exact question, then
     resubmit with `use_unlim` set.
   - `recovery_tool` → call it immediately (e.g. `show_plans_and_credits` when credits are short).
   - A transport timeout → the outcome is unknown; **do not resubmit**. Check `show_generations`
     and `transactions` first [HF-TOOL].
7. **Poll.** `jobs_wait {jobs:[{index:0, job_id}], timeout_seconds:15}`; repeat while
   `all_terminal:false`, waiting `poll_after_seconds` when given. Typical jobs take 1–4 min; long 1080p
   jobs can take 10+ min.
8. **Download.** `atp.py hf-get --url <result_url> --out <run>/60-outputs/<nn>/raw.mp4`. It streams
   with retries and verifies with ffprobe. Result URLs are public CloudFront links
   (`https://d8j0ntlcm91z4.cloudfront.net/user_<id>/hf_<date>_<time>_<job_id>.mp4`) [VERIFIED];
   download immediately.
9. **Post-process locally.** In order, as the plan requires:
   - `restore-audio`: Edit Mode silent edits get the source audio back;
   - `conform`: exact 720×1280, no stretching;
   - Analyze Mode text and inserts: placed in the video's CapCut project
     (`reference/capcut-assembly.md`); `captions` is only the fallback;
   - `qc`.
   See `reference/text-and-format.md`.
10. **Failures.**
    - A failed job is refunded (it shows in `transactions`). Retry once with the same or corrected
      params, and never create a duplicate of a pending job.
    - A second failure → report it and continue with the next video.

