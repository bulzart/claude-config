## 7. Model-specific pre-generation checklist

- [ ] One primary task; `mode` matches; edit prompts start with a trigger and name `@Video1`; extensions say "Extend @Video1 forward/backward" and set `extension_mode`.
- [ ] Fixed format: `aspect_ratio:"9:16"` + `resolution:"720p"` (or `auto` with a 9:16 start frame / 9:16-reframed source); no draft unless a 480p preview is wanted.
- [ ] No duration, ratio, resolution, fps or sound toggle in the prompt text.
- [ ] One role line per asset ("use only / do not use"); `medias` order = `@ImageN/@VideoN/@AudioN`; subjects in order of first appearance; references resized to ≤ output resolution; standard JPGs.
- [ ] Limits: ≤30 images, ≤10 videos (≤30 s), ≤10 audio (≤30 s), ≤50 total; edit source 4–30 s (ideally ≤20 s), 1–5 images.
- [ ] Timestamps contiguous, one change per range, end states stated and carried forward; "real-time speed" unless slow motion is intended.
- [ ] One camera behaviour per shot; lock phrase if static.
- [ ] Dialogue: speaker + language + delivery + `{exact words}`; listeners silent; music policy stated.
- [ ] Visible text: Analyze Mode → clean-plate line, blank carriers, no `【】`, text-free references; Edit Mode → every source text element named in a remove sentence; no Higgsfield preservation block.
- [ ] Integration line for inserted assets: size, hand/grip, orientation, scene light direction/colour temperature, shadow, reflection.
- [ ] A small flat pack added in an edit: the guide sharp at the video's pixel scale with a thin edge; the bare support named below the neighbour, with the keyboard and its keys entirely clear; the posture the model keeps or a source-object swap; a flagged delivery expected (§3.14).
- [ ] Size from the reckoning: ratio to a named neighbour, depth, "small object in the background" where it is one, constancy; the reference padded; a start frame measured with `atp.py scale` (`reference/anomaly-catalog.md` §2.7).
- [ ] Counts with numbers in every stage; every use beat names the part, the preparation step and the contact point; one [Exclusions] item per product for its own wrong use and count; no reference shows a later state than t=0 (`reference/anomaly-catalog.md` §3).
- [ ] Identity: headshot + full body; no-twin sentence; DETAILED exclusion for person swaps.
- [ ] Edits: `generate_audio:false`, `duration: ceil(source)`, `aspect_ratio:"auto"`, `bitrate_mode:"high"`; audio restored and duration conformed locally.
- [ ] Prompt ≤3,900 characters; no ids or URLs in the prompt; `get_cost:true` preflight done.

