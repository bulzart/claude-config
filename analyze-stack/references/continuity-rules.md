# Continuity rules — continuity sheet, handoff, reference attachments (Stage 4 → `40-plan\continuity-sheet.md`)

Owner brief: "continuity between consecutive prompts (the end state of one clip is the start state of
the next: same characters, wardrobe, product, setting, lighting and camera language) … Each clip prompt
also carries a continuity handoff to the next clip and cites the reference attachments it needs
(product images for identity, extracted frames from the original as composition and motion references
where the model allows it), using the exact reference syntax from the saved Seedance spec notes."

## 1. Continuity sheet format (`40-plan\continuity-sheet.md`, written by the continuity author)

```markdown
# Continuity sheet — <run-id> · approach: replicate | edit · mode: 1|2|3|edit · clips: N

## A. Master layout (fixed for the whole video; restated in every prompt)
Setting S1 "kitchen": white counter along the back wall; window on the left wall (soft daylight, 5200 K,
from screen-left, slightly above eye level); sink at the right end; a wooden board at the counter centre;
camera at counter height +20 cm, 60 cm from the counter, eye-level, 5 cm right of centre; 9:16.
Setting S2 "…": (only if the original has more than one setup)

## B. Characters (2–3 stable visible features each; never a real name unless the owner gave one)
C1 "woman in grey hoodie": mid-20s, dark hair in a low bun, grey hoodie, small gold hoop earrings; right-handed.
C2 "…"

## C. Product (from product-spec.md + swap-map global rules)
P1 "SUNNY OAT Orange Cream 16 oz": glossy white bottle, orange cap, label text "SUNNY OAT / Orange Cream / 16 FL OZ"; @Image 1 front, @Image 2 label; grip rule; table rule; content rule; sound rule; removal rule.

## D. Props and counts
one tall clear glass (12 oz), three ice cubes, one carton of milk (white, no brand text), a straw (paper, white).

## E. Wardrobe, hair, makeup, accessories — locked per character; note any change in the original (shot, time).

## F. Lighting and camera language
Key: window left, soft; fill: none; practical: none. Camera: handheld phone, slight natural shake, eye-level,
MCU for talking, MS for actions; one move per shot; cuts on beats.

## G. Audio bed
Room tone: quiet kitchen; music: (none | "upbeat lo-fi ~99 BPM" from clip 1 to the end); speech: C1 only, US English, casual.

## H. Style line (verbatim in every prompt) — from style-profile.md or style-bible.md.

## I. Per-clip start/end states (the handoff table)
| clip | source slice | start state (t=0) | end state (t=dur) | references (spec syntax) | notes |
|---|---|---|---|---|---|
| 01 | 00m00.00s–00m15.00s | C1 at counter centre facing camera, P1 in right hand label to camera, glass empty at centre | glass 2/3 full, P1 standing right of glass, C1 smiling to camera | @Image 1 P1 front · @Image 2 label · @Image 3 frame 00m00.00s composition | |
| 02 | 00m15.00s–00m30.00s | = end state of 01 (verbatim) | … | @Image 1 · @Image 2 · @Image 3 frame 00m15.00s | |

## J. Long-range dependencies (Seedance 2.5 Director ledger; `seedance\director\assets\continuity-ledger.md`)
| later action or ending (clip, t) | required prior state | enabling earlier event (clip, t) | missing or contradictory element | repair |
|---|---|---|---|---|
| 03 t=4 C1 drinks from the glass | glass 2/3 full, in C1's right hand | 02 t=9–12 pour; 02 t=14 pick-up | — | — |

## K. Cut / occlusion / hard-cut boundaries
| boundary | before state | after state | explained change or declared time jump | essential action still visible? |
|---|---|---|---|---|
| 01→02 (continuous) | … | identical | none | yes |
| 02→03 hard cut: new setup S2 | … | S2 layout; identity/wardrobe carried | declared in plan.json | yes |
```

## 2. Handoff rule

`end state of clip N` is copied **verbatim** into `start state of clip N+1` in the prompt text (the
writer of N+1 receives the sheet row, not the neighbour's prompt, so both writers work from one source).
It covers: character positions/poses/gaze, wardrobe, hand contents, product state (position,
orientation, fill level, open/closed), props and counts, setting, lighting, camera position and shot
size, audio bed (music continuing or not). If the original cuts to a new setup at the boundary, the
sheet says "hard cut: new setup S2" and the start state describes S2 (no handoff of positions, but
character/product/wardrobe identity still carries).

Mode 3 / anchors: the handoff is between the compressed clips in their new order; a merged beat's end
state is the end of its last kept source beat.

Director persistence rule (continuity-and-causality §4.3): an established state remains until an event
explains its change — items never multiply, vanish, swap holders or relocate because the camera looked away;
a cut or occlusion is not a reset; passive processes (settling, dripping, foam collapse, condensation, cooling)
continue across the boundary; a declared time jump is labelled in the sheet and never skips a required action.

## 3. Reference attachments per clip (exact syntax from `SEEDANCE-SPEC.md` §3.5 and §12)

| Purpose | Attachment | Where it comes from | How it is cited in the prompt |
|---|---|---|---|
| Product identity | 2–4 single-view product photos (front, label close-up, 3/4, optional in-hand for scale) | `50-prompts\references\product-front.jpg` … (copied from product-library) | `@Image 1 = our product, front view. Use only: proportions, colours, cap, label layout and text. Do not use: background, lighting, surface.` |
| Composition / framing of the clip's first moment | one extracted original frame at the slice start (`clip_frames.py` or ffmpeg `-ss <t> -frames:v 1`) | `50-prompts\references\clip-01-start-00m00.00s.jpg` | `@Image 3 = composition reference for the first frame. Use only: camera position, shot size, layout of the room. Do not use: the person, the product, any text.` |
| Motion / camera move (where the spec allows video refs: omni_reference mode) | a 2–10 s original slice with the move, muted | `50-prompts\references\clip-03-move-00m31.00s-00m36.00s.mp4` | `@Video 1 = camera-movement reference. Use only: the camera path and rhythm. Do not use: people, clothing, location, audio.` |
| Chaining (serial generation only) | previous clip's last frame (post-generation: `python …\tools\clip_frames.py "<clip>" --out "<run>\90-postgen\qa\clip-01"` writes `last-<t>.jpg`) | `90-postgen\qa\clip-01\last-00m15.00s.jpg` | first-frame mode: `Use @Image 1 as the first frame.` (sd25-pe exact sentence) with `ratio=adaptive`; or in omni mode `@Image 1 is the exact first frame; continue forward from that moment; do not replay what happened before it.` |
| Style (style swap) | 1 style reference in the target style, no people | `50-prompts\references\style-ref.jpg` | `@Image 4 = rendering-style reference. Use only: line work, shading, palette. Do not use: subjects, layout.` |
| Voice timbre (rare) | ≤ 10 s clean voice sample | `50-prompts\references\voice-c1.wav` | `@Audio 1 = C1's voice timbre. Use only: timbre and pace.` |

Numbering = upload order within each type (three independent 1-based sequences); the prompt file's
ATTACHMENTS table lists the files in exactly that order and the generator uploads/attaches them in that
order (`generation-playbook.md`). Tag form for replication prompts: `@Image 1` (official 2.5 wording).
Tag form for edit prompts: `@Video1`, `@Image1` (Higgsfield video_edit contract, `SEEDANCE-EDIT.md` §3).

`return_last_frame`: available on ModelArk, NOT on Higgsfield (`research\higgsfield-mcp.md` §C). On
Higgsfield the last frame is extracted locally with ffmpeg after the clip is downloaded. Chaining is
therefore optional and serial: default is parallel generation with the text handoff + shared references;
the owner can request "chained" generation (each clip waits for the previous one's last frame).

Real faces: ModelArk rejects reference images/videos with real human faces (spec §3.2); Higgsfield does
not (`SEEDANCE-EDIT.md` §2). Frames with people are allowed as composition references on Higgsfield;
`GENERATE-YOURSELF.md` warns about the ModelArk rule for other platforms.

Limits per prompt: ≤ 5 images recommended (1–8 subjects), video refs 5–10 s each, ≤ 30 s combined;
never the full 50 (spec §8, §9.17).

## 4. Edit approach (Seedance 2.5 video_edit) continuity

- Every segment prompt attaches the SAME product images in the SAME order (`@Image1` front, `@Image2`
  label, …) and uses IDENTICAL wording for the change and the stays-as-filmed block; only the segment's
  own timestamps and the "as seen" description of the target differ (`SEEDANCE-EDIT.md` §6).
- After segment 1 passes QA, a clean frame of the edited product may be attached to later segments as
  an anchor still (`@Image3 = a frame of the already-edited footage; the product must look exactly like this`).
- Duration: each edited segment is conformed to its source length and the source audio muxed back before
  joining (`join_clips.py`), so joins land on the original hard cuts.
- The continuity sheet for the edit approach has sections A–H from the ORIGINAL (nothing changes) plus
  section I with per-segment "product state at segment start/end" so the swap reads continuous across joins.

## 5. Quality bar

- Every clip row has a non-empty start and end state; end(N) == start(N+1) textually unless "hard cut" is declared.
- Every reference in the sheet exists on disk under `50-prompts\references\` (the continuity author copies/extracts them).
- Character and product descriptions are identical strings across rows (copy, don't paraphrase).
- The continuity lens of the anomaly check (`anomaly-checklist.md`) fails any prompt whose START STATE differs from the sheet.
