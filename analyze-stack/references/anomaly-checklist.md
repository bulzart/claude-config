# Anomaly checklist — six lenses over ALL prompts together (Stage 6 → `60-qa\anomaly-check.md`, `fixes-round-N.md`, `qa.json`)

Owner brief: "Before delivery, run an anomaly-check pass that reviews all prompts together for physical,
spatial, timing and continuity contradictions and fixes them." Pipeline: one checker agent per lens,
each reads EVERY prompt file (`50-prompts\clip-NN.md` or `edit-NN.md`), the continuity sheet, the
swap-map, the plan, the spec notes; writes its section; the main session merges, routes fixes to the
affected writers, loops until clean; max 3 rounds, then escalates to the owner (A3-style message
listing what could not be fixed and the recommendation).

## 1. Severities
| Sev | Meaning | Effect |
|---|---|---|
| S3 blocker | would produce a visible anomaly or a rejected/misclassified job | must be fixed; the set is not clean |
| S2 major | likely visible drift (count, layout, grip, colour result, continuity mismatch) | must be fixed |
| S1 minor | wording risk, unclear range, missing SFX, weak DoF statement | fixed if the writer is touched anyway; otherwise noted |
| S0 note | style/consistency suggestion | optional |

Clean = zero S3 and zero S2 across all lenses after a round.

## 2. Lenses and concrete checks

### L1 Physics (`physics-rules.md`)
- P01 every range has cause → effect; no state appears without a described cause (S3)
- P02 conservation: counts stated and constant; nothing appears/disappears/morphs; occlusion re-emergence stated (S3)
- P03 accumulation step-by-step (ice one by one, level rising, foam forming then settling, condensation over time) (S2)
- P04 gravity/liquids: no uphill flow, pour only when tilted, splash proportional, spills declared or excluded (S2)
- P05 hands: which hand, fingers, grip matched to the object size from product-spec; no two actions per hand per range (S3)
- P06 timing realistic (pour 4–6 s per 350 ml, cap 1–2 s, melt pool not in seconds) (S2)
- P07 one main action per range; ≤ 1 secondary motion; ≤ 2 actors; no high-burst actions (S2)
- P08 sound matches action: every contact/pour/click has its `<sfx>` in the same range (S1)
- P09 no tiny/gibberish text asked for; no text overlays; label text only from references (S3)

### L2 Space / layout (`physics-rules.md` §6, continuity sheet §A)
- SP01 START STATE positions relative to stable anchors, camera position/height/distance, light direction — all present (S2)
- SP02 layout identical to the continuity sheet master layout in EVERY prompt (same room, same object positions unless moved by a described action) (S3)
- SP03 objects moved in clip N are where clip N left them in clip N+1 (S3)
- SP04 line of action not crossed; camera side consistent (S2)
- SP05 the set does not contain objects that other prompts say are absent (S2)
- SP06 scale plausibility (16 oz bottle vs glass height, hand vs product) (S2)

### L3 Timing
- T01 timeline continuous integer-second ranges, no gaps/overlaps, sum = clip duration (S3)
- T02 dialogue fits its range at ≤ 3 words/s; speech ends before the final hold (S2)
- T03 per-beat budget 2–5 s ads / 6–8 s cinematic; no range packs > 1 main event (S2)
- T04 clip durations within the spec limits read at run time (4–30 s); edit segments 4–30 s (≤ 20 recommended) (S3)
- T05 handoff timing: clip N's last range ends on a held frame; N+1's first range starts from it (S2)
- T06 edit prompts: timestamps use the segment's own seconds (0-based), not the source's (S3)

### L4 Continuity (`continuity-rules.md`)
- C01 START STATE == continuity sheet row (textual match on characters, wardrobe, product state, props, camera, light, audio bed) (S3)
- C02 END STATE(N) == START STATE(N+1) unless "hard cut: new setup" declared (S3)
- C03 character descriptions identical strings across prompts; no new features (S2)
- C04 style line identical across prompts (S2)
- C05 music/ambience continuity (music starts/stops where the audio.md says) (S1)
- C06 references: the same product images with the same tags in every product clip; composition frame matches the clip's slice start (S2)
- C07 edit approach: identical wording and image order across segments; product state continuous across joins (S3)

### L5 Product consistency (`blending-rules.md`, `swap-map.md`, `product-spec.md`)
- PR01 identity block present and identical (brand, name, label text verbatim, colours, cap/lid) in every clip where the product appears (S3)
- PR02 every swap-map moment inside the clip/segment has its consequences in the prompt (colour result named, foam/fizz, condensation, reflections, grip, sound, text, dialogue) (S3)
- PR03 **no original brand marks remain**: grep every prompt for the original brand name, product name, slogan, hashtag, handle, colourway words; reflections and dialogue included; edit prompts contain the removal sentences (S3)
- PR04 behaviour analogue correct (no pour for a solid, no crunch for a liquid) (S3)
- PR05 count and single-object statements (S2)
- PR06 no swap chosen: the original product's observed identity is described consistently and its brand marks are NOT reproduced unless the owner kept the video as is (Q1 "Keep") — then the label is described only as observed, never invented (S2)

### L6 Spec compliance (`SEEDANCE-SPEC.md`, `SEEDANCE-EDIT.md`, sd25-pe)
- SC01 no parameters (ratio, resolution, duration, fps, audio toggle), ids, URLs, analysis notes in the prompt text (S3)
- SC02 every `@` asset bound with use-only/do-not-use; numbering = attachment order; ≤ 5 images; tag form correct (`@Image 1` replication, `@Video1`/`@Image1` edit) (S3)
- SC03 ≤ 1,000 words (target 250–600); edit ≤ 3,900 chars (S2)
- SC04 dialogue in quotes with speaker attributes; language named for non-English; ≤ 10 words/line; brackets not reused for names (S2)
- SC05 one camera move per shot; locked-off sentence when static; no stacked moves (S2)
- SC06 negatives short and last; subtitles negative present on 9:16; duplicate-character sentence present (S1)
- SC07 edit prompts: trigger word first; exactly one `@Video1`; no "reference Video 1"; no extension words; preservation block + scope-closure sentence once; generate_audio false unless an audio edit was requested (S3)
- SC08 chaining sentences verbatim (`Use @Image 1 as the first frame.`) when used (S2)
- SC09 platform parameter line matches prompts.json (mode, duration int, aspect, resolution, audio) (S2)
- SC10 no IP/brand/artist/studio names in style lines (S2)

### Edit-prompt additions (approach = Seedance 2.5 edit; L4 runs ED01–ED02, L6 runs ED03–ED04)
- ED01 **stays-as-filmed completeness**: every visible subject category in the segment's shots (people,
  the target product, other products/props, background objects, text carriers — from `visual.md` rows for
  those shots) is either named in WHAT CHANGES or covered by the preservation block + the scope-closure
  sentence; an unlisted category the swap could disturb (a second cup, a mirror, a shelf tag) is S2,
  S3 when it carries a brand mark
- ED02 **no contradictory change**: nothing is both replaced/removed/modified and "kept exactly as
  filmed"; no two operation sentences target the same object with different outcomes; a "keep everything
  exactly the same" window never overlaps a change window (S3)
- ED03 identical wording and identical `@Image` order across all segments — only the timestamps and the
  "as seen" description of the target may differ (S3)
- ED04 the removal sentences cover every brand mark in the swap-map REMOVE lines for the segment's
  moments, reflections included, plus the "must no longer appear anywhere in the final video" sentence (S3)

### 2b. Seedance 2.5 Director categories → lens mapping (`seedance\director\references\continuity-and-causality.md` §5; every checker runs its rows)

| Director category | Lens | What to check (director wording) | Repair the writer must apply | Severity |
|---|---|---|---|---|
| Identity and count | L5 (product) · L4 (people/props) | an entity duplicates, merges, changes variant or silently switches | stable descriptors + real reference ownership; track each instance | blocker → S3 |
| Location and topology | L2 | a later position does not follow from a real path; similar places confused | name persistent world anchors; describe any relocation | major → S2 (S3 if the product) |
| Custody and support | L1 · L4 | who holds/supports each item; a hand or tool double-booked; release before support | specify contact, lift, carry, placement, release at the decisive points | blocker → S3 |
| Causality and knowledge | L1 · L3 | effect without an available cause; a reaction without a perceivable trigger | establish mechanism, prerequisite, sightline or audible cue first | major → S2 |
| Time and order | L3 | concurrent when sequential is required; the allotted seconds are infeasible | sequence dependencies; drop optional activity; shorter target (A3) | major → S2 |
| Inventory and volume | L1 · L5 | contents fail to persist/accumulate; source not depleted; destination overfilled | describe material movement and resulting levels qualitatively | blocker → S3 |
| Solid geometry | L1 · L2 | interpenetration, stretching, scale change, passing through closed barriers | clearance, entry route, rigid parts, authorized articulation | blocker → S3 |
| Mechanical function | L1 | motion contradicts the real hinge / joint / latch / thread / cap | show unlocking / alignment / actuation before the result | major → S2 |
| Force and motion | L1 | implausible motion, stopping, falling, turning, support | driving action, continuous trajectory, settling response | major → S2 |
| Materials and phases | L1 · L5 | fluid / granular / rigid / elastic / cloth behaviour wrong for the material; universal rules ("every solid floats") | describe the actual interaction and aftermath for THIS material (product-spec.md) | major → S2 |
| Optics and visibility | L2 · L5 | "invisible" is really occlusion, opacity, reflection or framing; label legibility | preserve appearance; distinguish what exists from what can be seen | polish → S1 (S2 for the label) |
| Body and environment | L1 · L2 | reach, grip, balance, footing, gaze, scale incompatible | natural reachable blocking; room for handling | major → S2 |
| Camera and edit | L3 · L4 | cuts, screen direction, focus, crop or moves conceal or contradict essential events; a cut used as a reset | preserve action geography; make contact readable; sequence camera phases | major → S2 |
| Sound and emotion | L3 · L6 | a sound or reaction without the right source, timing or motivation | bind cues to events; give reactions a stimulus | polish → S1 (S2 for dialogue sync) |
| Production contract | L6 | reference inputs, settings, duration, mode and required precision disagree | verify supported controls (SPEC §3.5, §11); separate wishes from settings | blocker → S3 |

Cross-cutting safeguards (all lenses): passive processes keep running between actor commands; repeated locations
are anchored to durable room features; non-visual consequences persist (a device stays on, a consumed item is
gone); an edit's dependency closure (shadows, reflections, occlusion, contact, later reach) is checked; unknown
geometry / density / timing stays unknown — no invented precision; essential correctness is never hidden behind
cuts or blur. Method fidelity is a finding in its own right: a required operation replaced by a bridge verb, a
montage, an ellipsis or an off-screen moment is S3 under the lens that owns the operation.

## 3. Output — `60-qa\anomaly-check.md` (merged by the main session) and per-lens sections

```markdown
# Anomaly check — <run-id> — round 1 — result: NOT CLEAN (S3: 3, S2: 5, S1: 4)
| id | lens | sev | clip(s) | check | finding (quote the offending line) | fix instruction |
|---|---|---|---|---|---|---|
| F001 | L5 | S3 | 03 | PR03 | "…the strawberry one…" (original flavour word) | replace with the swap-map dialogue rule ("orange cream") or cut the line (Q4a) |
| F002 | L4 | S3 | 02→03 | C02 | 02 END: "cap on the counter"; 03 START: "cap in her left hand" | writer 03 copies row 03 of the sheet verbatim |
…
```

`60-qa\fixes-round-N.md` (routing):
```markdown
# Fixes — round 1
## clip-03 → prompt-writer (clip 03)
- F001 (S3, L5/PR03): …fix instruction…
- F007 (S2, L3/T02): …
## clip-02 → prompt-writer (clip 02)
- F002 (S3, L4/C02): …
```
Writers rewrite their file, bump `qa rounds`, and return; the main session regenerates `prompts.json`
and re-runs the six checkers on the whole set (a fix in clip 02 can break clip 03).

`60-qa\qa.json`: `{"rounds":[{"n":1,"findings":[{"id":"F001","lens":"L5","check":"PR03","sev":"S3","clips":[3],"status":"fixed|open"}],"clean":false}],"clean":true,"final_round":2}`

## 4. Feasibility pre-check (A3, run on the PLAN before writing prompts)
The same lenses L1/L2/L3 are applied to `plan.json` + continuity sheet rows (not prompts): clips with
≥ 2 risky items (simultaneous movers > 2, people > 2, liquid + camera move, small text, high-burst
action, > 1 camera move) are listed with a recommendation (split at a cut, shorter target, drop the
shot). The main session asks A3 only if the list is non-empty.

## 5. Escalation (after round 3 still not clean)
`anomaly-check.md` gets a `## Escalation` section: open findings, why they persist, the recommended
change (usually a simpler split or a shorter target). The main session shows it and asks A3 with
`{n}` = open S3+S2 count and the recommendation; "Apply recommendation" → back to Stage 4 for the
affected clips; "Proceed as planned" → deliverables are written with the open findings listed in
DELIVERABLES.md under "Known risks".
