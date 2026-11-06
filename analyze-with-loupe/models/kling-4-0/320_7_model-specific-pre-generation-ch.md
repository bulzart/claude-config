## 7. Model-specific pre-generation checklist

- [ ] `mode` matches the `medias` (`text-to-video` | `image-to-video` | `reference-to-video` | `video-edit`); frames never ride with references.
- [ ] `aspect_ratio:"9:16"`, `resolution:"720p"` (the default is 1080p); frames exactly 9:16 at 720×1280; an edit source already 9:16; `awl.py conform` afterwards (§2.6).
- [ ] `duration` a whole number 3–30, matching the prompt's stated length; a source up to the live maximum is one generation.
- [ ] Video quota: video references + edit clips + video elements ≤5 clips and ≤30 s, each clip ≥3 s; ≤10 images; ≤15 assets in total.
- [ ] Every reference has a role and a preserve-list (`@Image1 defines …; preserve …`), and a "never inherit" scope where it carries more than its job; the same order in every clip.
- [ ] FORMAT MODE: the continuous-take sentence for a take, or the planned shots with their cut times.
- [ ] SCENE CONTEXT opens with "EXACTLY <n> … — NO DUPLICATES"; POSITIVE CONSTRAINTS restate the counts.
- [ ] ACTION TIMING in decimal-second rows: each hand's job, the part and contact point of every use, counts and states restated after exits, occlusions and cuts; one exclusion per product for its own wrong use and count (`reference/anomaly-catalog.md` §3).
- [ ] LOCATION MAP fixes sides; CAMERA gives distance, height, rig and one move; LIGHTING one key source with the product's highlight, reflection and contact shadow.
- [ ] Size relation from the reckoning written as a check; the size risk in the brief (§3.14).
- [ ] AUDIO: dialogue in quotes in its language with the voice described, or "No dialogue, no voice-over"; "No background music" unless music is wanted.
- [ ] Clean-plate line (§3.11 b); surfaces described plain; reference text excluded; edits: "Edit @Video1" + keep-list, text removal as its own first pass.
- [ ] Prompt length within the limit the first request shows (§2.5 item 10), with no clean-plate, count or continuity line cut.
- [ ] `get_cost: true` preflight done.

