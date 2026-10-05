---
name: genjutsu
title: Higgsfield Genjutsu
description: Generate a video with Higgsfield Genjutsu by transferring motion or replacing a subject or object in a source video.
source: get_preset_instructions {preset:"/genjutsu"} — retrieved 2026-09-30 (verbatim)
---

# Higgsfield Genjutsu

`/genjutsu` selects a generation model family. Use `generate_video` with the concrete model selected by the user's intent:

- Copy, repeat, reproduce, mimic, or transfer motion, actions, gestures, dance, or camera motion from a driving video to reference-image subjects: `hf_mult_motion_control`.
- Replace, change, or swap an object, product, garment, or character in a source video using reference images: `hf_mult_replace_object`.

Read `models_explore` with `action:"get"` with the selected `model_id` for current supported parameters. Put arguments inside `params`: `model` is the selected ID, `prompt` is the user's brief, and `medias` contains reference images with role `image` and exactly one source/driving video with role `video`. Use supplied media and context. If the intent or required media is missing, ask for those inputs; a bare `/genjutsu` still selects this workflow. Do not submit until required inputs are available.

Call `generate_video` once the inputs are ready, then wait with `jobs_wait` using `timeout_seconds:15`. Its generation widget updates automatically; use `job_display` only if the user requests a separate re-display. Do not claim success on a failed submission. Free Genjutsu attempts (`use_free_gens`) are not available on this connector. If explicitly requested, explain that limitation and do not submit a paid replacement. Preserve explicit `use_unlim` requests according to the full generation tool contract; do not silently remove that flag on rejection.

Do not treat this command as a missing preset, a Naruto effect request, or an instruction to open a gallery. Do not pass `genjutsu` as the model ID. Multiple independent edited variants of one clip belong to the ad-multiplier workflow only when the user requests those variants.

Reuse confirmed media IDs. For unconfirmed attached inputs call `media_upload_widget` with type `auto`, multiple true as the only tool in that turn; resume this Genjutsu command once uploaded. For media URLs use `media_import_url`.

---
Local note (not part of the Higgsfield text): in Claude Code the upload widget is unavailable; use
`media_upload` → HTTP PUT → `media_confirm` (see `../higgsfield-mcp.md` §4).
