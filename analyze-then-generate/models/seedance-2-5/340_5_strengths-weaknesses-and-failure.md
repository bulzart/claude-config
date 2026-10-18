## 5. Strengths, weaknesses and failure modes

| failure mode | typical trigger | mitigation |
|---|---|---|
| Subtitles / captions appear | repeated dialogue words with tone notes; captions in a reference video; portrait frame | "Character's line (emotion): content"; clean references; explicit subtitle line; QA; removal pass [OFFICIAL S2, S6] |
| Misspelled or pseudo-text | any in-frame words | clean plate + post text; if required, text as image reference or letters one by one [OFFICIAL S2] |
| Source text survives an edit | text element not named | name every element with the remove sentence; removal-only pass first [OFFICIAL S2, S6; HF S13] |
| Music despite "No BGM" | SFX rendered as score | enumerate music terms, repeat policy start and end, or strip in post [OFFICIAL S2] |
| Edit routed as reference/extension | no trigger word; "reference Video 1" | trigger first; name `@Video1` directly [OFFICIAL S2, S6] |
| Edit output ~0.3–0.4 s short | model frame processing | 8n+1-frame source or reference mode; conform + QA [OFFICIAL S2; HF S13] |
| Complex multi-requirement edit unstable | several references + edits in one call | split into passes [OFFICIAL S2] |
| Wrong character ↔ reference mapping | upload order ≠ order of first appearance | reorder; one line per subject [OFFICIAL S2] |
| **Dead space / filler** | too little plot per time range; long take without timeline | one real change per range; shorter duration; hold only at the end [OFFICIAL S2; SECONDARY S19] |
| **Arbitrary slow motion** | long ranges, "cinematic" wording | "real-time speed; no slow motion" unless wanted [INFERRED; SECONDARY S19] |
| **Sudden speed changes** | overloaded ranges, speed-ramp words | even event density; "constant natural speed" [OFFICIAL S2; INFERRED] |
| **Unmotivated cuts / transitions** | packed ranges; vague multi-shot wording | "continuous one-shot, with no jump cuts" or explicit `Shot N` + "Hard cut." [OFFICIAL S2] |
| **Morphing** (objects bend, parts change) | fast orbit, weak references | 2–4 single-view images as one rigid entity; slow moves [OFFICIAL S7, S9; INFERRED] |
| **Identity drift** | mixed reference sheets, small face area | headshot + full body; "without drifting or changing identity" [OFFICIAL S2, S6] |
| **Duplicated objects / twins** | multi-view sheets, unlabeled subjects, >4 people | single-person images, counts, no-twin sentence [OFFICIAL S2, S6] |
| **Clothing / age changes** | unanchored wardrobe | clothing named as an invariant; official exclusion "Exclude face swaps, changes in age or clothing, sudden height shifts, added or missing characters, spatial jumps" [OFFICIAL S2] |
| Objects teleport or reset after cuts | no restated state | end state per stage, restated at next use [OFFICIAL S7; INFERRED S17] |
| Count of multiples changes after an exit, occlusion or cut (three capsules become one after a walk-past) | items not counted per stage; a walk-past or cut with no restatement | counts with numbers in every end state and after re-entry; "exactly N …; none appears or disappears" (`reference/anomaly-catalog.md` §2.1, §2.5) [INFERRED; observed 2026-10] |
| Product used through the wrong part (a straw bottle drunk from the side without the spout; a sealed can sipped) | the use written as a result only ("drinks"), without the part or the preparation step | initial state → operation on the named part → result, with the contact point; the preparation step first; one [Exclusions] item naming the wrong use (`reference/anomaly-catalog.md` §2.2, §2.3) [INFERRED; observed 2026-10] |
| A later state leaks into frame 0 (a raised tab on a can cracked later) | a reference image that shows the later state | attach only the t=0 state; write it in [Start state] (`reference/anomaly-catalog.md` §2.3) [observed 2026-10] |
| A thrown or passing thing goes through the product; the product sinks into a surface or shows through an arm | the path written without the product ("he tosses the paper"); complex multi-subject interaction is a stated weakness [OFFICIAL S1] | write the path relative to the product with the side and the landing spot, or the hit and its consequence; "[Exclusions] nothing passes through the bottle; it is solid and opaque"; move the anchor out of the path when the story does not need the contact (`reference/anomaly-catalog.md` §2.14) [observed 2026-10] |
| Object snaps, or pauses on a pose then resumes | free physical motion (a spin, toss or roll, or a vehicle's move) given exact times or a required end state ("never timestamp high-frequency actions" [OFFICIAL S2]) | describe the physics only; give the end state a visible cause; time product-pun text to the real moment (`generation-system.md` §5b) [INFERRED] |
| Inserted asset looks pasted on (a can on a dresser at 2–3× real size, squared to the lens, flat cool light in a warm dim room, no contact shadow, straight-on in a low-angle room) | product-photo lighting, exposure, background and camera angle inherited; a tight product crop; an anchor alone on an empty edge | "@ImageN defines only shape, proportions, colours and label; do not use its lighting, exposure, background, shadow or camera angle"; the room's light on the product, its size against a named neighbour, its mark angle, its contact shadow like the neighbour's, the scene's camera angle; an anchor touching or partly behind something; padded crops; the eleven-sign paste test in QC (`reference/anomaly-catalog.md` §2.15) [INFERRED; observed 2026-10] |
| A small flat pack named "lying flat on its largest face" is added standing upright facing the lens, or onto the keyboard end or the mouse (run 12 V08 V09) | a thin flat pack on open wood is read as a standing box; "in front of <neighbour>" puts it on the neighbour | §3.14 "Placing a small flat pack in an edit"; no passing take (CE-091, CE-092, CE-094) |
| The edit copies a guide image literally: pose, size, spot, soft label and thick bevelled rim | a guide with a soft label or a thick edge | a guide sharp at the video's pixel scale with a thin edge (CE-093) |
| Glowing eyes / fingerprint textures / bubbling audio | intense emotion words; oversized AI references; water wording | neutral emotion + "normal human eyes"; resize references; drop water/echo words [OFFICIAL S2] |
| Person swap leaves original in reflections | partial scope | DETAILED exclusion sentence [HF S13] |

