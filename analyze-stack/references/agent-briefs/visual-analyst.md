# visual-analyst — agent brief (Stage 2a; one agent per ≤ 60 s segment; plus one `reconcile` pass on long videos)

Load first: `LAYOUT.md`, `references\report-template.md` (§2, §7, §8, §10 — what the report needs from
you), `references\style-taxonomy.md` (§1 parameters, §2 labels, §4 skeleton), `references\physics-rules.md`
§6 (how spatial layout must be described), `research\miko-analysis.md` §2.6–§2.8 (evidence hierarchy,
shot-table columns, overlay vs physical text).

## Purpose
See the video. Produce the shot table, people and setups, the fixed spatial layout, the entity and
product inventory with screen time (this feeds Q1), camera and lighting per setup, and the measured
style profile. You LOOK at every contact sheet and every shot keyframe with the Read tool; JSON is
only the index to what you look at.

## Inputs
`10-measure\contact-sheets\sheet-NN.jpg` + `contact-sheets\index.json` (sheet/cell → t/shot/frame — use it to cite cells),
`10-measure\keyframes\shots\shot-NN-first|mid|last-<t>.jpg` (full resolution) + `keyframes\sampled\t-<t>.jpg` + `keyframes.json`,
`shots.json`, `cuts.json`, `ocr.json` (`spans[]` with `kind_hint` overlay/unknown, `brand_candidates[]`, `handles[]`, `hashtags[]`),
`probe.json`, `visual-stats.json` (`shots[].camera_motion.label`, `frames[].palette/brightness/saturation/edge_density`,
`global.palette`, `global.style_hints`, `global.motion.dominant/handheld_fraction`), `measure-summary.md` §1–§11 and
`analysis-segments.json` (your segment row). Notes tell you your segment range and whether other segments exist.

## Outputs
- Single-segment video: `20-analysis\visual.md`, `20-analysis\entities.json`, `20-analysis\style-profile.md`.
- Multi-segment: `20-analysis\visual-segNN.md`, `entities-segNN.json`, `style-profile-segNN.md`; then the
  `reconcile` agent merges them into the three final files (global entity ids, screen time summed,
  boundary shots not double-counted, one style profile, disagreements listed).

### `visual.md` skeleton (fixed headings)
```markdown
# Visual analysis — <run-id> · segment 01 (00m00.00s–00m31.40s) | full video
## 1. Shot table
| # | Source time | Dur | Framing | Camera move | On screen / props | Action and delivery | Evidence |
|---|---|---|---|---|---|---|---|
| 1 | 00m00.00s–00m01.40s | 1.40 | MCU eye-level | handheld static | overlay "POV: …" (0.0–1.4 s); red can in right hand | she raises the can to the lens, label out, mouth opens on "okay" | sheet-01 c1–c4, shots\shot-01-first-00m00.00s.jpg |
## 2. People and setups
Setup S1 (shots 1–3, 9): C1 — woman, mid-20s, dark hair low bun, grey hoodie, gold hoop earrings, right-handed; …
## 3. Spatial layout per setup (relative to stable anchors; camera position; light direction)
S1 "kitchen": counter along the back wall; window left wall (soft daylight from screen-left, slightly above eye level); sink right end; glass at counter centre 20 cm from the front edge; camera at counter height +20 cm, ~60 cm away, eye-level; …
## 4. Entity & product inventory (sorted by screen time)
| id | entity | kind | category | where (times, shots) | screen time | swappable? | brand marks seen | observed properties |
| e1 | red 12 oz slim can | product | beverage | 00m00.00s–00m09.50s (1–3), 00m40.00s–00m45.00s (9) | 14.5 s | yes | "BRAND X" wordmark on the can (shot 2, kf shots\shot-02-mid-00m02.20s.jpg); hashtag overlay "#brandx" 00m28.10s | aluminium, red body, white wordmark, red carbonated liquid (foam visible shot 3) |
## 5. Camera and lighting per setup
## 6. On-screen text: overlays (excluded from generation) vs physical text (preserved/replaced)
| time | text (verbatim or "unreadable") | kind | position | evidence |
## 7. Style (summary; full profile in style-profile.md)
## 8. Uncertainties and disagreements with measurement
```

### `entities.json` schema
```json
{"schema":"analyze-stack.entities/1","run_id":"…","segment":"01|all",
 "entities":[{"id":"e1","name":"red 12 oz slim can","kind":"product|person|animal|prop|vehicle|text|location|other","category":"beverage",
   "appearances":[{"start_s":0.0,"end_s":9.5,"shots":[1,2,3]},{"start_s":40.0,"end_s":45.0,"shots":[9]}],
   "screen_time_s":14.5,"swappable":true,"brand_marks":["BRAND X wordmark on can (shots 1–3)","#brandx overlay 28.1–30.0 s"],
   "observed_properties":{"colour":"red body, white wordmark","size":"12 oz slim can (estimate)","material":"aluminium","content":"red liquid, carbonated, foam 1 cm at 7.5 s","transparency":"opaque"},
   "held_by":"C1 right hand, three fingers on the body, thumb on the label edge (shots 1–3)",
   "keyframes":["10-measure/keyframes/shots/shot-02-mid-00m02.20s.jpg"]}],
 "setups":[{"id":"S1","name":"kitchen","shots":[1,2,3,9],"layout":"…","camera":"…","light":"…"}],
 "people":[{"id":"C1","features":["mid-20s woman","dark hair low bun","grey hoodie","gold hoop earrings"],"handedness":"right","speaks":true}]}
```

## Method
1. Read `shots.json` and `cuts.json` for the shot list of your segment (global shot numbers).
2. LOOK at every contact sheet covering your range in order (`index.json` tells you which sheets/cells cover
   your seconds; cite cells as `sheet-02 c5`); then LOOK at every `keyframes\shots\shot-NN-first|mid|last-*.jpg`
   of your shots (full resolution — read labels and hands here); use `keyframes\sampled\t-*.jpg` for moments
   between shot frames. Write the shot table row by row while looking, not afterwards. `visual-stats.json`
   camera labels are heuristic hints — your eyes decide the "Camera move" column.
3. Setups: group shots by location/wardrobe/light; describe each person with 2–3 stable visible
   features (no names unless on screen); note wardrobe/hair/makeup changes with the shot where they change.
4. Spatial layout per setup: positions relative to stable anchors (counter edge, window, door, table
   centre), camera distance/height/angle/side, light direction/quality/colour (physics-rules §6).
5. Inventory: every product, prop, person, animal, vehicle, visible text carrier. Screen time = sum of
   shot durations where the entity is visible (partial visibility counts; state "partly visible");
   `swappable` = a product/prop that could be replaced by another product of the same function (people,
   locations, animals are not swappable). Record brand marks precisely (what, where, when, evidence).
6. On-screen text: split overlays (captions, handles, watermarks, stickers, UI) from physical text
   (labels, signs, menus); verbatim only when legible at full resolution, else "unreadable".
7. Style profile per `style-taxonomy.md` §1 (all rows) and §4 skeleton, with the measured cues from
   `measure-summary.md` (palette, motion) and your observations (line work, grain, lens, grade). Produce
   the STYLE LINE (≤ 40 words, Seedance phrasing from §2).
8. `reconcile` mode: merge segment files; renumber entities globally (`e1…`), sum screen time, merge
   appearances, keep the longest-evidence description, pick one style profile (note per-segment
   differences), list boundary disagreements in §8, write the three final files.

## Quality bar
- Every row cites a sheet cell or keyframe path. No aesthetic adjectives without an observable cue.
- The inventory is complete enough for Q1: nothing a viewer would call "the X" is missing.
- Grips, sizes and positions are described as the prompt writers will need them (which hand, fingers, orientation, distance).

## When evidence is missing
"unreadable" for text, "estimate" for sizes, "not visible" for occluded properties; never infer a brand
from colours alone (write "brand mark present, illegible"). If a contact sheet is missing or corrupt,
say which and continue with the keyframes.
