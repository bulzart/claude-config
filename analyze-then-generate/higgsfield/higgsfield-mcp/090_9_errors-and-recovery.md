## 9. Errors and recovery

| Situation | Response |
|---|---|
| Transport timeout on submit | The outcome is unknown. Do not resubmit. Check `show_generations {type:"video", size:5}` / `transactions` for a matching job, then continue polling or resubmit once it is known that nothing was created |
| `adjustments` in a response | The server applied defaults or clamped values. Check each one against the plan |
| `recovery_tool` | Call it immediately (credits / plan flows), then wait for the user |
| `unlim_choice` | Nothing was submitted. Ask, then resubmit with `use_unlim` |
| Validation error naming a field | Fix that field only (role name, parameter name, value out of range) and resubmit. The creative intent stays unchanged. Log the correction |
| Unsupported feature for the model | Do not fake it in prose. Switch the operation (e.g. start frame instead of references), or tell the user the model cannot do it and suggest a model from `index.json` that can |
| PUT not 200 | Do not confirm. Request a new `media_upload` slot (URLs are single-use, signed per content type) |
| Job `failed` | A refund appears in `transactions`. Read `fail_reason` if present, adjust (content filter → rephrase; input → fix), and retry once. A failure within seconds, with no reason or a filter text, is a **flag**: record it first (`T ledger set --flagged`, `T caught-flag add`, command item 23), then change the request |
| Content protection block ("May contain protected content") | Remove real-person likeness claims or protected IP from the prompt and references, then ask the user if the asset itself is the cause [HF-DOC]. It is a flag: `T caught-flag add` with the verbatim text before the change |
| An uploaded image, video or Element comes back `nsfw`, `ip_checking` or `failed`; an output is withheld; a `preset_recommendation` notice comes back instead of a job | Flags: record with `T caught-flag add` (`--stage upload` / `result` / `submit`; name a flagged input with `--asset`, a file path for an upload), then replace the input with another supplied asset; for a `preset_recommendation` notice (a reroute, not a content block: one preset matched about 20 first submissions of runs 01 and 02 and the matching words were never identified) retry the one literal request with `declined_preset_id` set to the notice's preset id and the wording unchanged, and pass that `declined_preset_id` on every later `generate_video` call of the run from the start; never re-upload a flagged file unchanged |
| Result shorter than planned | Report it. Never loop or freeze frames to pad a result |

