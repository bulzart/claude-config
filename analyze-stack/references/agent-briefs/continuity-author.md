# continuity-author — agent brief (Stage 4 / 4e; one agent, after the plan exists and A1/A2 are approved)

Load first: `LAYOUT.md`, `references\continuity-rules.md` (sheet format, handoff rule, reference attachments,
edit-approach continuity), `references\physics-rules.md` §1, §6 (start/end states, fixed layout),
`seedance\SEEDANCE-SPEC.md` §3.5 (reference syntax), §10 (consistency techniques), `research\higgsfield-mcp.md` §C
(media roles), `references\blending-rules.md` §4.2 (global product rules), and the **Seedance 2.5 Director** bundle
(read-only): `seedance\director\references\continuity-and-causality.md` §4.1 (one persistent world: stable identities,
world-relative anchors, world vs screen vs handedness, invariants vs state that must change), §4.3 (persistence rule;
a cut is not a reset; hidden ≠ absent), §4.4 (backward then forward), and `seedance\director\assets\continuity-ledger.md`
(the ledger tables you fold into sections J and K of the sheet).

## Purpose
Write the single source of truth every prompt writer copies from: the master spatial layout, the
characters, the product, props and counts, wardrobe, lighting and camera language, the audio bed, the
style line, and the per-clip start/end states with the reference attachments in the exact spec syntax.
End state of clip N = start state of clip N+1, verbatim.

## Inputs
`40-plan\plan.json` (+ `slicing.md` / `segments.md` / `compression-plan.md` / `edit-segments.md`),
`20-analysis\visual.md` (§2–§5 setups, people, layout, camera, light), `entities.json`, `audio.md` (§4 music,
§8 room), `style-profile.md` (STYLE LINE) or `40-plan\style-bible.md` when the style is swapped,
`30-decisions\swap-map.md` (global rules), `product-spec.md` §4 (image list), `answers.json` (Q5, Q6),
`10-measure\keyframes\`, `50-prompts\references\` (frames already extracted by the planner).

## Outputs
`40-plan\continuity-sheet.md` (format: continuity-rules §1, sections A–I), `40-plan\continuity-sheet.json`
(`{"layout":{…},"characters":[…],"product":{…},"props":[…],"style_line":"…","rows":[{"clip":1,"start_state":"…","end_state":"…","references":[{"tag":"@Image 1","file":"…","use_only":"…","do_not_use":"…"}],"hard_cut_new_setup":false}]}`),
and the reference files copied/extracted into `50-prompts\references\` (product images as
`product-front.<ext>`, `product-label.<ext>`, `product-three-quarter.<ext>`; frames as named in plan.json;
motion slices `clip-NN-move-<t1>-<t2>.mp4` muted, 2–10 s, only when a camera move must be copied).

## Method
1. Master layout (A) from `visual.md` §3, rewritten relative to stable anchors with camera position and
   light direction; one block per setup. LOOK (Read tool) at the start frame of each clip while writing its row.
2. Characters (B): 2–3 stable visible features each, identical strings reused everywhere; wardrobe (E)
   locked per setup with the shot where the original changes it.
3. Product (C): identity, `@Image` bindings, grip/table/content/sound/removal rules copied from the swap-map
   global rules (or the original product's observed identity when no swap; brand marks are never
   reproduced unless Q1 = "Keep the video as it is", then described only as observed).
4. Props and counts (D), lighting and camera language (F), audio bed (G), style line (H) verbatim.
4b. Director tables: (J) long-range dependencies — every later use or the ending → the required prior state →
   the enabling earlier event → missing/contradictory element → repair (work backward from the last clip's end
   state, then forward through every row; distant dependencies, not only neighbours); (K) cut / occlusion /
   hard-cut boundaries — before state, after state, explained changes or declared time jump, "essential action
   still visible?" (never hide a method-critical step behind a cut). Both tables go into the sheet
   (`continuity-rules.md` §1 J/K) and `continuity-sheet.json` (`dependencies[]`, `boundaries[]`).
5. Rows (I): for each plan item, start state (positions, poses, gaze, hand contents, product state,
   fill levels, camera, light, sound) and end state; `end(N)` pasted verbatim into `start(N+1)` unless the
   plan declares "hard cut: new setup". Mode 3: rows follow the compressed order; merged beats end at their
   last kept source beat. References per row in upload order (product images → composition frame →
   motion slice), each with use-only / do-not-use, tags `@Image 1` (replication) or `@Video1/@Image1` (edit).
6. Edit approach: sections A–H describe the ORIGINAL (nothing changes); rows carry "product state at
   segment start/end" and the identical image order for every segment; note the optional anchor still.
7. Verify every referenced file exists; extract missing frames with ffmpeg (`-ss <t> -frames:v 1 -update 1`);
   mute motion slices (`-an`). `state.py "<run>" set next_step=style-bible|feasibility|prompts`.

## Quality bar
- `end(N) == start(N+1)` textually for every consecutive pair without a declared hard cut.
- Descriptions of characters and the product are copy-identical across rows; the style line is one string.
- ≤ 5 image references per row; motion slices 2–10 s; all paths exist.

## When evidence is missing
If a start frame is occluded or dark, describe from the nearest visible frame and mark "inferred from
00m12.90s". If the original changes wardrobe or setting between clips, declare a hard cut rather than
inventing a transition. Never add a prop the original does not show.
