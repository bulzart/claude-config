# Prompt template — per-clip prompt file `50-prompts\clip-NN.md` and `prompts.json` (Stage 5, replication)

Sources folded in: `seedance\SEEDANCE-SPEC.md` §12 skeleton (official 2.5 layout: asset binding →
one-sentence summary → timeline → additional notes; bracket rules; ≤ 1,000 words, 250–600 target),
ByteDance's official prompt-optimisation skill `C:\Users\Bulzart\.claude\skills\sd25-pe\SKILL.md`
(intent first; template first; account for every asset with "use only / do not use"; one line per
subject/asset — no range mappings; unused assets listed; separate parameters — never write ratio,
resolution, duration, fps or the audio toggle into the prompt text; no unrequested generic negatives
beyond subtitles/audio/brand; observable performance, not adjectives; stages with one state change
each; dialogue ledger — never turn speech into silence or invent lines; keyframe sentences verbatim
"Use @ImageN as the first frame."), `physics-rules.md`, `blending-rules.md`, `continuity-rules.md`,
`style-taxonomy.md`. Writers may also read the sd25-pe file directly at run time.

## 1. File format — `50-prompts\clip-NN.md`

```markdown
# Clip 03 / 05 — 15 s — source 00m26.00s–00m41.00s — beats b06, b07 — mode omni_reference
Run: <run-id> · approach: replicate · Mode 1 · platform: TikTok 9:16 · style: keep (UGC handheld phone)
Writer: prompt-writer (clip 03) · status: draft | checked | final · qa rounds: 0

## Attachments (upload order = @ numbering; three independent sequences)
| tag | file | role (Higgsfield) | use only | do not use |
|---|---|---|---|---|
| @Image 1 | 50-prompts\references\product-front.jpg | image_references | proportions, colours, cap, label layout and text | background, lighting, surface |
| @Image 2 | 50-prompts\references\product-label.jpg | image_references | logo and wording | anything else |
| @Image 3 | 50-prompts\references\clip-03-start-00m26.00s.jpg | image_references | camera position, shot size, room layout | the person, the product, any text |

## Platform parameters (NOT in the prompt text)
model seedance_2_5 · mode omni_reference · duration 15 · aspect_ratio 9:16 · resolution 1080p · generate_audio true · bitrate_mode high · count 1

## Prompt (submit verbatim; ≤ 900 words; no ids, no URLs, no parameters)
ASSET BINDINGS
@Image 1 = our product, SUNNY OAT Orange Cream 16 oz, front view. Use only: proportions, colours, orange cap, label layout and text. Do not use: its white studio background, lighting or surface.
@Image 2 = the same product's label close-up. Use only: the logo and wording "SUNNY OAT / Orange Cream / 16 FL OZ". Do not use: anything else.
@Image 3 = composition reference for the first frame. Use only: camera position, shot size and the kitchen layout. Do not use: the person, the product or any text in it.
The product in @Image 1 and @Image 2 is one single object throughout.

ONE-SENTENCE SUMMARY
A woman in her mid-20s with dark hair in a low bun, a grey hoodie and small gold hoop earrings pours the orange drink from the bottle over ice in a tall glass on a white kitchen counter, authentic UGC phone video, locked-off eye-level medium shot, quiet kitchen room tone with pour and glass sounds.

START STATE (0 s)
Composition as in @Image 3. The white counter runs along the back wall; the window is on the left wall and throws soft daylight from screen-left. The tall clear glass stands at the counter centre with three ice cubes in it, empty of liquid. The bottle stands 10 cm to the right of the glass, label toward the camera, cap on. Her right hand rests on the counter beside the bottle; her left hand is out of frame. Camera at counter height plus 20 cm, 60 cm away, eye-level medium shot. Quiet kitchen room tone.

TIMELINE
0-3s: Her right hand lifts the bottle by the lower body, four fingers around it and the thumb on the label edge; the label stays toward the camera. Her left hand enters from frame left and twists the cap off <short plastic click>; the cap stays in her left hand. Ends with the bottle 10 cm above the glass rim, tilted 20 degrees.
3-9s: She pours in one continuous motion. The opaque orange liquid falls straight into the glass; the level rises evenly from empty to two-thirds over these 6 seconds; where it meets the ice the surface swirls pale orange, no foam, no fizz, no spill. <smooth pour into a glass with ice>. Camera locked-off.
9-13s: She rights the bottle, sets it down on the same spot to the right of the glass, label toward the camera, <soft plastic set-down>, and lifts the glass with her right hand for one sip; her lips touch the rim once. <ice clink>
13-15s: She lowers the glass to the counter centre, looks into the lens and smiles; the corners of her mouth rise; the frame holds for the last second.

CAMERA
Locked-off camera, fixed camera position, eye-level medium shot; the camera never moves; no push, no pan, no zoom, no handheld shake. Natural phone depth of field: the counter and glass sharp, the background kitchen slightly soft.

LIGHT & LOOK
Soft daylight from the left window, 5200 K, no fill; authentic UGC texture, handheld-phone look at rest, real skin texture, natural colors, HD, rich details, stable motion, no flicker.

AUDIO
No dialogue. Quiet kitchen room tone throughout; <plastic click> at 1 s; <smooth pour> from 3 to 9 s; <set-down> at 10 s; <ice clink> at 11 s. No BGM; generate only environmental sounds and action sounds. No subtitles.

PRODUCT INVARIANTS
Preserve exactly: the bottle's proportions, glossy white body, orange cap, and the label text and layout of @Image 2, label facing the camera whenever visible. Exactly one bottle, one glass, three ice cubes, one cap; the same single bottle throughout.

END STATE (15 s) — handoff to clip 04
Glass two-thirds full of opaque orange liquid at the counter centre; bottle standing to its right, cap off in her left hand out of frame, label toward the camera; she stands centred facing the camera, smiling; same framing, same light; room tone. Hold for the last second.

CONSTRAINTS
No cuts, no slow motion, no duplicated people or products, no extra hands or fingers, no object teleportation, no identity or wardrobe change, no text overlays, no subtitles, no logos or watermarks other than the product label, no camera shake, liquid never flows uphill. Throughout the video, characters with completely identical appearance, clothing, and accessories are prohibited.

## Continuity
From clip 02 (start state source): 40-plan\continuity-sheet.md row 03 — matches verbatim: yes.
To clip 04: END STATE above is row 04's start state — matches verbatim: yes.

## Writer notes (not submitted)
- Swap-map moments covered: M03 (pour, peach result not applicable: over ice, no milk), M04 (set-down).
- Dialogue in the source (00m28.10s "so good") is an overlay-era line spoken off camera in the original → not reproduced (Q4a n/a in Mode 1: line was a caption, not speech). 
- Risk: glass reflection of the window; stated as "slightly soft background" to reduce specular drift.
- Word count: 412.
```

## 2. Block rules (from the spec §12, sd25-pe and the Seedance 2.5 Director bundle `seedance\director\`)

Director overlay on every block (prompt-playbook §7): the prompt is a compact directing specification, not a
ledger dump — the director's compile organisation (FORMAT AND INTENT / REFERENCE OWNERSHIP / INITIAL WORLD STATE /
CONNECTED ACTION AND CAMERA / ENDING / LOOK AND SOUND / CONTINUITY CONSTRAINTS) maps 1:1 onto the blocks below
(summary+platform line / ASSET BINDINGS / START STATE / TIMELINE+CAMERA / END STATE / LIGHT & LOOK+AUDIO /
PRODUCT INVARIANTS+CONSTRAINTS). Reinforce a high-risk state at its later use ("the same glass, now two-thirds
full", "the cap she set down at the left edge"), not in every sentence; never use a bridge verb ("handles",
"does the process", "then it is ready", "seamlessly transitions") or a quality adjective ("physically accurate",
"natural hand motion") in place of the specific acquisition, transfer, release or material interaction; the text
must be self-contained (no "as discussed", "same as before", pronouns without a referent, unresolved tags,
research notes, or instructions asking the model to reason).

| Block | Rule |
|---|---|
| ASSET BINDINGS | one line per asset in upload order; "Use only / Do not use" on every line; a product with several views is declared "one single object"; never rely on labels inside images; ≤ 5 images; if chaining: the exact sentence `Use @Image 1 as the first frame.` (first-frame mode) or `@Image 1 is the exact first frame; continue forward from that moment; do not replay what happened before it.` (omni mode) |
| ONE-SENTENCE SUMMARY | subject (2–3 stable visible features) + action + location/time + genre/style + camera clause + sound clause |
| START STATE | physics-rules §1/§6: positions relative to stable anchors, hands, product orientation, fill levels, camera, light, sound bed; = the continuity sheet's start state verbatim |
| TIMELINE | continuous integer-second ranges (2.5 timestamps), ~15–25 words per second, one main event per range, cause before reaction, each range ends with its observable state; SFX in `<>`, music in `()`, dialogue as `Speaker (language, delivery): "line"` (≤ 10 words, speaker attributes, non-speakers' mouths closed, speech finishes before the final hold); no high-frequency actions timestamped |
| CAMERA | one move per shot with start/end composition and trigger, or the locked-off sentence; DoF |
| LIGHT & LOOK | key direction/quality/colour; the STYLE LINE from style-profile.md or style-bible.md verbatim; quality words |
| AUDIO | dialogue or "No dialogue"; ambience; SFX tied to events; "(music…)" or "No BGM; generate only environmental sounds and action sounds"; "No subtitles." always on 9:16 |
| PRODUCT INVARIANTS | only when a product is in the clip; from swap-map global rules (or the original product's observed identity when no swap); counts |
| END STATE | handoff (continuity-rules §2); hold 0.5–1 s |
| CONSTRAINTS | short, grouped, last; subtitles/audio/brand negatives + the scenario-specific physics line; the official duplicate-character sentence |

Style swap: LIGHT & LOOK carries the style bible's STYLE LINE and character sheet lines; product
photos get "Do not use: the photographic rendering style" when the target is animated.

Hard cuts inside a clip (Mode 1 slices spanning several shots): write each shot as its own timeline
range starting with `Hard cut.` and a new shot-size/camera line; at most one camera move per shot.

## 3. `50-prompts\prompts.json` schema (shared by replication and edit prompts)

```json
{
  "schema": "analyze-stack.prompts/1",
  "run_id": "20260916-101500-snowscents",
  "approach": "replicate",
  "mode": 1,
  "model": "seedance_2_5",
  "platform": {"name": "tiktok", "aspect_ratio": "9:16", "resolution": "1080p", "fps": 24},
  "style": {"label": "real organic footage", "sub_style": "UGC handheld phone", "swapped": false},
  "product_swap": {"original_entity": "e1", "product_slug": "sunny-oat-orange-cream-16oz"},
  "items": [
    {"no": 3, "kind": "clip", "file": "50-prompts/clip-03.md", "duration_s": 15,
     "source_start_s": 26.0, "source_end_s": 41.0, "beats": ["b06", "b07"],
     "mode": "omni_reference", "aspect_ratio": "9:16", "resolution": "1080p", "generate_audio": true, "bitrate_mode": "high",
     "prompt": "<the ## Prompt block verbatim>",
     "references": [
       {"tag": "@Image 1", "file": "50-prompts/references/product-front.jpg", "role": "image_references", "use_only": "…", "do_not_use": "…"},
       {"tag": "@Image 2", "file": "50-prompts/references/product-label.jpg", "role": "image_references", "use_only": "…", "do_not_use": "…"},
       {"tag": "@Image 3", "file": "50-prompts/references/clip-03-start-00m26.00s.jpg", "role": "image_references", "use_only": "…", "do_not_use": "…"}
     ],
     "continuity": {"from": "clip 02 end state (sheet row 03)", "to": "clip 04 start state (sheet row 04)"},
     "word_count": 412, "status": "final", "qa_rounds": 1}
  ],
  "updated": "2026-09-16T16:02:00-05:00"
}
```
Edit segments use `"kind": "edit-segment"`, `"mode": "video_edit"`, `"aspect_ratio": "auto"`,
`"generate_audio": false`, `"source_file"`, `"passthrough"` and `@Video1`/`@ImageN` tags
(`edit-prompt-template.md`). `prompts.json` is rewritten by the main session after every fix round from
the clip files (the clip files are the source of truth).

## 4. Writer self-check before returning (all must be true)
- All `{{…}}` placeholders replaced; no parameters, ids, URLs, analysis notes in the Prompt block.
- Every asset bound with use-only/do-not-use; unused attachments removed from the table (not listed as unused).
- Timeline continuous, integer seconds, sums to the clip duration; one event per range.
- START STATE == continuity sheet row (verbatim); END STATE == next row's start.
- Product block matches swap-map global rules; the removal rule is honoured (no original brand words anywhere).
- Word count 250–600 (≤ 900 hard); dialogue lines ≤ 10 words; language named for non-English.
- Physics DO/DON'T table respected (physics-rules §12).
- Director release gate passed on the `## Prompt` block alone (prompt-playbook §8): intent + method preserved;
  every later use has a compatible earlier state in the text; no known contradiction in paths, support, capacities,
  hands, materials, visibility; events fit the seconds; cuts/occlusions reset nothing; the ending follows; only real
  attachments cited; no bridge verbs, placeholders, "as discussed", or reasoning commands; every detail earns its place.
