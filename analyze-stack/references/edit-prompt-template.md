# Edit prompt template — per-segment `50-prompts\edit-NN.md` for `seedance_2_5` video_edit (Stage 5e)

Sources: `seedance\SEEDANCE-EDIT.md` §3–§6 (trigger words, `@Video1`/`@ImageN` contract, A→B phrasing,
preservation block, generate_audio false + mux, segment consistency), `SEEDANCE-SPEC.md` §3.1 (video
editing task constraints: ratio adaptive, duration -1, source 4–30 s), ByteDance's `sd25-pe` editing
template (sole master; inventory every visible subject and say replaced / removed / kept; scope-closure
sentence mandatory; motion-slot replacement; timeline inheritance; no re-writing the source into
invented timestamps), `blending-rules.md`, `physics-rules.md`, `continuity-rules.md` §4, and
`30-decisions\edit-intent.md` (Q2e). Same blending/physics/continuity logic as replication.

## 1. File format — `50-prompts\edit-NN.md`

```markdown
# Edit segment 02 / 04 — 15.000 s — source 00m15.00s–00m30.00s (00-input\segments\seg-02.mp4) — mode video_edit
Run: <run-id> · approach: Seedance 2.5 edit · intent: product swap only (Q2e) · swap-map moments in this segment: M03, M04
Writer: edit-prompt-writer (segment 02) · status: draft | checked | final · passthrough: false

## Attachments (video first, then images in @Image order — Higgsfield medias order)
| tag | file | role (Higgsfield) | use only | do not use |
|---|---|---|---|---|
| @Video1 | 00-input\segments\seg-02.mp4 | video_references | the source footage: every shot, cut, camera move, performance, lighting, timing | — |
| @Image1 | 50-prompts\references\product-front.jpg | image_references | proportions, colours, orange cap, label layout and text | background, lighting, surface |
| @Image2 | 50-prompts\references\product-label.jpg | image_references | logo and wording | anything else |

## Platform parameters (NOT in the prompt text)
model seedance_2_5 · mode video_edit · duration 15 (= ceil(source), ignored by the mode) · aspect_ratio auto · resolution 1080p · generate_audio false · bitrate_mode high · count 1
Post: conform to 15.000 s and mux 00-input\segments\seg-02-audio.mka back (SEEDANCE-EDIT §5), then QC gates.

## Prompt (submit verbatim; ≤ 3,900 characters and ≤ 1,000 words; trigger word first; no ids/URLs/parameters)
Video edit. Replace only the red 12 oz slim can with a white label held in the woman's right hand and standing on the counter in @Video1 with the product from @Image1 (front view: exact proportions, glossy white body, orange cap, label layout and text) and @Image2 (label close-up: logo and wording "SUNNY OAT / Orange Cream / 16 FL OZ"). Do not copy the background, lighting or surface of @Image1 or @Image2. The replacement is one single 16 oz bottle throughout.

0-4s: keep everything exactly the same except the target: the bottle stands to the right of the glass where the can stood, at real-world size (taller and wider than the can), label toward the camera.
4-10s: she lifts and pours from the bottle with the same grip timing and the same motion path and tilt as the can; four fingers wrap the lower body and the thumb rests on the label edge; the liquid that pours is opaque orange and still, so the stream is smooth with no fizz and no foam; the milk in the glass turns peach — orange streaks first, then a uniform pale peach by the end of the pour; the level rises exactly as it does in @Video1.
10-15s: the bottle is set down where the can was set down, label toward the camera; keep everything exactly the same.

Remove only the "BRAND X" wordmark and the red-and-white brand colourway wherever they appear in @Video1 (the can, the reflection on the fridge door at 12-14s) and reconstruct the revealed surfaces consistently with their immediate surroundings.

Keep everything else from @Video1 exactly the same: shots and cuts, camera moves, framing, the woman's face, hair, grey hoodie, hands and performance, the glass, the ice, the milk carton and their count, the kitchen, lighting, colour grading, pacing and timing. Preserve every caption, subtitle, and other untargeted on-screen text element from @Video1 exactly as it appears, including its wording, styling, placement, animation, and timing. Text physically attached to a replaced target follows that replacement. Except for the objects explicitly modified above, all other visible characters, props, and background elements in @Video1 remain unchanged and are not to be replaced or removed.

No subtitles. No watermark. No extra products, no duplicated hands, no floating objects. The original can must no longer appear anywhere in the final video.

## Continuity
Product state at segment start: bottle on the counter, cap on, label to camera (= end of segment 01). At segment end: bottle on the counter, cap off, level in the glass two-thirds (= start of segment 03). Identical wording and identical @Image order as segments 01, 03, 04: yes.

## Writer notes (not submitted)
- Overlay "so good 😍" at 00m28.10s names no brand → preserved by the preservation block (owner's caption tool handles captions later anyway).
- The fizz sound in the source audio (00m20.00s–00m24.00s) will not match a still pour: flagged for the post-generation edit (SFX replacement), since audio is muxed from the source.
- Characters: 1,912.
```

## 2. Block rules

| Block | Rule |
|---|---|
| Trigger | the prompt starts with `Video edit.` and uses `Replace only … / Remove only … / Modify only … / Add only …`; never "reference Video 1", never "extend/continue" (`SEEDANCE-EDIT.md` §3, §7) |
| Source | exactly one video, always `@Video1`; product/reference images `@Image1…@ImageN` (case-sensitive, no space — Higgsfield contract); the video is listed first in Attachments |
| WHAT CHANGES | one operation sentence per change; A→B ("the red can … with the product from @Image1"); every consequence from the swap-map entries for this segment's moments (colour/mixing result, foam/fizz, condensation, reflections, shadows, grip/size, sound where generated, world text, count), timed to the SEGMENT'S OWN seconds (`0-4s`, not the source's `15-19s`); timestamps only where the change is partial in time; never re-narrate the whole source from memory (sd25-pe) |
| Removal | `Remove only the <brand mark> … wherever it appears … and reconstruct the revealed surface consistently with its immediate surroundings.` — every original brand mark from the swap-map removal rule, including reflections; the final sentence `The original <product> must no longer appear anywhere in the final video.` |
| WHAT STAYS EXACTLY AS FILMED | the fixed preservation block (people, motion, camera, lighting, audio, timing, other objects and their count, on-screen text) + the sd25-pe scope-closure sentence, verbatim, once |
| Negatives | short, last: No subtitles. No watermark. No extra products, no duplicated hands, no floating objects. |
| Audio | `generate_audio:false` by default; NO audio sentence in the prompt (the source audio is muxed back). Only when the owner's edit intent includes an audio change: `generate_audio:true` and the audio-edit sentences from sd25-pe ("Keep the original dialogue and music unchanged; change only …") with the writer note that timbre may drift |
| Continuity | product state at start/end; identical wording and image order across segments; optional anchor still from an approved earlier segment as `@Image3` |
| Length | ≤ 3,900 characters, ≤ 1,000 words; typically 150–350 words |

Edit intents beyond the product swap (Q2e "plus other edits" / "other edits only") get one operation
sentence each, in the same A→B form, and are listed in the WHAT CHANGES block after the product
sentences: colour change ("Modify only the wall behind the counter in @Video1 so that it is sage green;
keep its texture and lighting"), setting swap ("Replace the background outside the woman's outline with
the beach from @Image3; keep her lighting direction"), restyle ("Modify only the rendering of @Video1
so that it looks like <style bible line>; keep every motion, cut and timing"), entity replacement (a
person → bind to an `@ImageN`, never to `@Video1`; note the lip-sync consequence if the person speaks).

## 3. `prompts.json` entry (see `prompt-template.md` §3)

```json
{"no": 2, "kind": "edit-segment", "file": "50-prompts/edit-02.md", "source_file": "00-input/segments/seg-02.mp4",
 "source_audio": "00-input/segments/seg-02-audio.mka", "source_start_s": 15.0, "source_end_s": 30.0, "duration_s": 15.000,
 "passthrough": false, "moments": ["M03", "M04"], "edit_intent_items": ["product-swap"],
 "mode": "video_edit", "aspect_ratio": "auto", "resolution": "1080p", "generate_audio": false, "bitrate_mode": "high",
 "prompt": "<the ## Prompt block verbatim>",
 "references": [
   {"tag": "@Video1", "file": "00-input/segments/seg-02.mp4", "role": "video_references"},
   {"tag": "@Image1", "file": "50-prompts/references/product-front.jpg", "role": "image_references", "use_only": "…", "do_not_use": "…"},
   {"tag": "@Image2", "file": "50-prompts/references/product-label.jpg", "role": "image_references", "use_only": "…", "do_not_use": "…"}],
 "continuity": {"from": "segment 01 end product state", "to": "segment 03 start product state"},
 "char_count": 1912, "status": "final", "qa_rounds": 1}
```
Passthrough segments appear with `"passthrough": true`, `"prompt": null` and no references.

## 4. Writer self-check
- Trigger word first; one `@Video1`; ≤ 5 images; all bound with use-only/do-not-use.
- Every swap-map moment inside the segment has its consequences in WHAT CHANGES, timed to segment seconds.
- Removal sentence covers every brand mark listed for these moments (incl. reflections) + the "must no longer appear" sentence.
- Preservation block + scope-closure sentence present verbatim, once.
- No parameters, ids, URLs; ≤ 3,900 chars.
- Wording identical to the sibling segments except the timestamps and the "as seen" description.
