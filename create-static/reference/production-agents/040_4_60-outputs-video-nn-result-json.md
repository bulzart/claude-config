## 4. `60-outputs/video-NN/result.json`
```json
{"video": "NN", "status": "done|blocked|failed",
 "capcut_project": "13_Nov_2026_vNN", "capcut_project_path": "<the project's full path>", "capcut_pending": false,
 "qc": "accepted | regenerated: <the images drawn again and why> | RESIDUAL FAILURE: <what stays wrong> | declined fix: <why> | failed: <why> | off: not checked (the user reviews at the end)",
 "checks": "images: <viewed, the style lock, the people, the clean picture> | text: <T image text answer path> | thumbnail: <full and small size viewed> | content: <§11 and §11b read> | edit: <the build's read_back and problems> | evidence: <image, sheet and read-back paths>",
 "fix_proposal": null,
 "blocker": null, "notes": "…",
 "static": {"…": "the edit's record, written by cs-record"}}
```
`static` holds the Static video's record (`cs-record`: the format, the images with their source and re-draws, `cost_usd_estimate`, the
drawings, the narration's and the bed's facts, the language and approach, the title and thumbnail, the captions' look and `capcut_build`: the
build's `ok`, `seconds`, `problems` with how each was settled, and its `read_back`). A video made in more than one format has
`static.formats`: one entry per format, each with its own CapCut project (static §2b). There is no job, credit or flag field: a video's cost
is `static.cost_usd_estimate`.
`checks` names, for each check of §3 item 13, the file or answer that shows it; one that could not run says "not checked: <why>".
`fix_proposal` is set only with `blocker: qc_fix_permission` (QC fixes `ask`): `{"findings": ["<expected, why, seen, file paths>", …], "cause": "<the diagnosis>", "retry_changes": "<what the corrected prompts change>", "images": ["iKK", …], "prompts": ["<path of each corrected prompt file>", …], "cost_usd_estimate": <n>}` (0 with FLUX 3 Klein).
An image agent of a split video (`images K1-K2: S3 only`, cs-produce A9b) writes `60-outputs/video-NN/images-K1-K2.json` (each image's
attempts, re-draws, cost and flags) and ends with the one line `{"video", "images": "K1-K2", "status", "cost_usd_estimate", "flagged"}`; the
edit agent (`S4 and X10`) sums those files into its `result.json`.
