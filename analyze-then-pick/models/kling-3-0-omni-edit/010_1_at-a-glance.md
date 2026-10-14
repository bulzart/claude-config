## 1. At a glance

- **Positioning.** Kling VIDEO 3.0 Omni (launched 2026-02-06 [OFFICIAL S15]): "the Kling VIDEO O1 model has been upgraded to VIDEO 3.0 Omni", and "The video editing, prompt transformation, and other features in 3.0 Omni function the same as in O1." [OFFICIAL S1]. For post-production Kling says users can "Input natural language like 'remove the bystanders in the background', or 'make the sky blue', and the model will use deep semantic understanding to automatically complete pixel-level adjustments" [OFFICIAL S2]. A June 2026 upgrade reportedly extended Omni editing to 3–15 s and 4K input/output with better source consistency [SECONDARY S9].
- **Best for:** one or two clear operations on a short clip that must keep its motion and camera: product/object swap from a reference image, background replacement, removal of distractions or burned-in text, recolouring, style transfer, weather/time changes, a new angle of the same action, green-screen extraction [OFFICIAL S2].
- **Weaker at / unknown:** no duration, audio or ratio controls on Higgsfield [HF S3]; short sources ("between 3s and 10s") [OFFICIAL S1]; ≤4 reference images with a video [OFFICIAL S1]; native audio "Not Supported Yet" with video input [OFFICIAL S1]; tag binding on Higgsfield undocumented (§2.5); no timestamp scoping documented.
- **Choose this model when** the edit is simple, the source is ≤10 s, and you want Kling's look.
- **Choose another model when** the source is 10–30 s or needs timestamp-scoped operations, more than four images, audio edits or dubbing (Seedance 2.5 `video_edit` under Higgsfield's edit contract), or a pure one-object swap that must pass source audio and untouched pixels through (Genjutsu `hf_mult_replace_object`) [HF S6].

| operation | how to invoke on Higgsfield | notes |
|---|---|---|
| Instruction edit (add / remove / modify / background / style / weather / angle / green screen) | `model:"kling_video_edit"`, one `video_references` item | output follows the source's ratio and length [HF S3, S4] |
| Reference-guided edit | same + up to 4 `image_references` | "When a video is provided, a total of up to 4 images/elements can be uploaded." [OFFICIAL S1] |
| Generation, multi-shot, next/previous shot, motion reference | N/A on this id | Omni generation modes are not exposed as `kling_video_edit` |

