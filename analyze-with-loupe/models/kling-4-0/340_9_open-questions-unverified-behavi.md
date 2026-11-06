## 9. Open questions / unverified behaviour

- **Mode routing:** does Higgsfield infer `mode` from the `medias`, reject media that do not fit the mode, or drop them silently? Is `start_image` + `image_references` in one call rejected (Kling: the entry points cannot combine)?
- **Reference numbering:** does `@ImageN` / `@VideoN` follow the `medias` order within each role on Higgsfield, also when roles are interleaved?
- **Frame naming:** in `image-to-video`, are `start_image` / `end_image` addressable as `@Image1` / `@Image2`, or only as "the first frame" / "the last frame"? Is `end_image` alone accepted (Kling supports a last frame only)?
- **Middle keyframes:** the catalog says "ordered keyframes" and tags `keyframes`, but lists no role for frames between the first and the last. Can several ordered images reach Kling's keyframes (for example as `image_references` in `image-to-video`)?
- **Elements:** how does a prompt cite `kling_element_ids` (`@Element1` by array order, `<<<element_id>>>`, a name)? Do Higgsfield reference-element UUIDs work like Kling elements, and can a voice-bound element carry a voice?
- **Audio:** confirm on the first output that a stereo track is always present and cannot be suppressed; does a video reference's own sound leak into the output?
- **Output:** exact pixel size and frame rate at 9:16 / 720p (720×1280 expected); behaviour of `aspect_ratio:"9:16"` with a non-9:16 start frame or edit source.
- **Edit length and billing:** in `video-edit`, does the output follow the source length or `duration`? How is a 5-clip edit billed? Is the source's audio kept by default?
- **Prompt limit:** Higgsfield's character cap for this id (Kling: 8,000 tokens); truncation or rejection when exceeded.
- **Continuous takes:** does the FORMAT MODE continuous-take sentence reliably suppress the default multi-shot? Do written shot lists cut at the written times?
- **Text:** spelling accuracy of new in-frame text, and whether "no subtitles" fully suppresses default subtitles.
- **Size:** does a placed product follow written size relations on this model (§3.14)?
- **Cost:** which of Higgsfield's two credit tables holds, and how much each added reference costs (`get_cost` per request).
- **Prompt expansion:** does Higgsfield leave Kling's expansion on, and does it ever override a complete prompt?
