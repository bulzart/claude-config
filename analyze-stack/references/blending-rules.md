# Blending rules — dynamic product-swap logic for ANY category (Stage 3s → `30-decisions\swap-map.md`)

Owner brief: "The swap has to blend into the video, and the logic must be dynamic so it works for any
category (beverages, gum, tools, toys, cosmetics, food, anything) … every visual consequence of the
change must be worked out across the whole video … Every downstream prompt must carry the swapped
product consistently in every clip, and no logos, labels, watermarks or brand mentions of the original
product may remain." These rules apply identically to replication prompts (Stage 5) and to Seedance
edit prompts (Stage 5e).

## 1. Method (swap-planner agents, one per ≤ 60 s segment where the product appears, + one reconciler)

1. List every **moment** the original product (Q1 entity) is visible, audible, named, or implied
   (reflection, shadow, hand shape, a cup it was poured into, a wrapper on the table): time range, shot,
   beat id, keyframe path. LOOK at the frames (Read tool), do not rely on `entities.json` alone.
2. For each moment run the §2 checklist against `product-spec.md` (ours) vs the original's observed
   properties (visual.md entity row). Record only the consequences that actually differ.
3. Write one swap-map entry per moment (§4 format). Then the reconciler merges segment maps, resolves
   contradictions (same moment described twice), and writes the global rules (§4.2).
4. If a behaviour of the original has no analogue for our product (a pour when ours is solid; a crunch
   when ours is liquid) the entry proposes the closest **same-function beat** and flags it
   `needs-owner-decision`; the main session shows these flags before planning (they surface in the Q2e
   answer for the edit approach or as A3 feasibility items for replication).

## 2. Checklist — applied to EVERY moment the product appears

| # | Aspect | Question | Prompt-ready consequence (examples) |
|---|---|---|---|
| 1 | Colour of contents & mixing | what colour is our content; what does it mix with; what is the result | see §3 |
| 2 | Transparency / opacity | clear, translucent, opaque; does the container show the level | "the level is visible through the clear bottle" vs "opaque can: no level visible; weight cue via hand" |
| 3 | Reflections & specular | matte / gloss / metallic / clear surfaces; what reflects (window, ring light, hand) | "the glossy label shows a soft vertical window reflection sliding as she rotates it" |
| 4 | Foam / fizz / bubbles | carbonated? foaming? head height, settle time | "still liquid: smooth pour, no fizz, no head" · "carbonated: 1 cm foam that settles in 3 s" |
| 5 | Condensation / frost / steam | cold, hot, room temperature | "fine condensation beads form on the can over the clip; none on the room-temp jar" |
| 6 | Shadows & light on packaging | finish changes how light lands; shape changes the shadow footprint | "the matte black jar takes a soft gradient, no hot spot; contact shadow is round, ⌀ 8 cm" |
| 7 | Label legibility by distance | at wide shots the label is a colour block; at MCU it is readable; macro = exact text | "wide: black jar with a white label; MCU: wordmark 'SNOW SCENTS' readable; macro: full label text as in @Image 2" |
| 8 | Container size & grip | dimensions, weight → which fingers, one or two hands, how it sits in the palm; on a table: footprint | "held by the jar's lower half with the whole hand; the thumb rests on the label edge; the label stays toward the camera" |
| 9 | Weight & motion | heavier/lighter → slower lift, wrist angle, set-down sound | "set down with a dull glass thud; no wobble" |
| 10 | Sounds | pour, fizz, crunch, click, snap, spray, rattle, crinkle | "<dull thud>", "<smooth pour, no fizz>", "<crisp snap>" |
| 11 | On-screen text | overlays that name/describe the original (price, flavour, brand hashtag) | overlay → removed from generation entirely (overlays are the edit's job); text in the world (shelf tag, menu) → replaced/removed |
| 12 | Brand mentions in dialogue | lines that say the name, flavour, slogan, or a property that no longer holds ("so fizzy") | replace with our name/property if verbatim dialogue allowed to change (Q4a), else cut the line; never keep the original brand name |
| 13 | Brand mentions in captions/subtitles of the source | burned-in captions in the original | not reproduced (captions never generated; edit approach: "Remove only the burned-in caption text …" if it names the brand) |
| 14 | Behaviour differences | pouring vs solid, chewing vs drinking, tool action vs toy action, spray vs pump | same-function beat mapping; flag `needs-owner-decision` when no analogue |
| 15 | Quantity / count | multipack vs single; several flavours lined up | "exactly one jar throughout" / "three jars, identical, labels to camera" |
| 16 | Secondary props tied to the product | straw, glass, ice, opener, charger, applicator, spoon | keep if still plausible; remove or replace otherwise ("no straw: the jar is not drunk from") |
| 17 | Residue / traces | drips, crumbs, stains, lipstick marks, dust from the original product | must match ours ("a thin cream ring on the rim" / "no drips: solid product") |
| 18 | Environment fit | a fridge scene for a shelf-stable product, a bathroom for food… | keep the setting (context never changes) unless physically absurd → flag |
| 19 | Reflections of brand marks | the original logo reflected in a mirror/screen/sunglasses | removed ("no logo in the mirror reflection") |
| 20 | No original brand marks anywhere | logos, labels, watermarks, wordmarks, colourways that ARE the brand (the exact red + white swoosh), handles, hashtags, jingles | every entry ends with the removal line; the product-consistency anomaly lens re-checks |

## 3. Colour mixing — worked examples (state the RESULT nuance, never "mixes")

Method: name both colours, their opacity, the ratio (roughly), then the resulting nuance; describe the
transition (swirl → uniform) and the time it takes.

| Our content | Mixed with | Original result in the video | Our result to write |
|---|---|---|---|
| red liquid | white milk | pink | (reference case from the brief) "pale pink, uniform after 2 s of stirring" |
| **orange** liquid (opaque) | white milk | pink (original) | "peach / creamy orange; first orange streaks swirl through the white, then a uniform pale peach" |
| **green** liquid (translucent) | white milk | pink | "mint green, milky and opaque; streaks of darker green fade within 2 s" |
| **clear** liquid | white milk | pink | "stays white, slightly thinner; the level rises; no colour change" |
| dark brown (cola) | white milk | — | "light tan, opaque, small foam ring at the edge" |
| blue sports drink (translucent) | water + ice | — | "pale sky blue, transparent; ice cubes visible through it" |
| yellow oil | water | — | "does NOT mix: yellow beads float on top, then form a thin film" |
| red powder | water | — | "sinks, then clouds pink from the bottom up, uniform after stirring" |
| **Non-liquid analogues** | | | |
| chewing gum (pink) | mouth | (original: blue gum) | "pink gum; a small pink bubble, matte; no blue anywhere" |
| cream (white) | skin | (original: tinted cream) | "white cream spreads translucent and disappears in 3 s; no tint left on the skin" |
| peanut butter (tan, opaque) | bread | (original: jam) | "spreads thick, matte, holds knife marks; no red" |
| clay (grey) | hands | (original: green slime) | "grey clay: holds its shape, matte, leaves no residue" |
| chocolate (brown) | hot milk | — | "dark brown swirls, then uniform milk-chocolate brown; steam rises" |
| tool (steel) | wood | (original: red plastic tool) | "steel head, brushed finish; sawdust colour unchanged; no red plastic" |

Rules: opaque + opaque → average with bias to the darker/more saturated; translucent + white → pastel of
the translucent colour; clear + anything → no hue change; immiscible pairs never "blend"; carbonated +
liquid → foam ring first; powder → sinks/clouds; the transition is described in seconds (physics-rules §3).

## 4. Output format — `30-decisions\swap-map.md`

### 4.1 Per-moment entries

```markdown
### M03 — 00m06.20s–00m09.50s · shot 3 · beat b04 · keyframe 10-measure\keyframes\shots\shot-03-mid-00m07.50s.jpg
Original: the red 12 oz can (BRAND X) is tilted and poured into a tall glass of milk; the mix turns pink; the can logo faces the camera; overlay "so good 😍"; she says "the strawberry one is elite".
Ours (product-spec §1–3): orange 16 oz bottle, opaque white liquid, still, plastic gloss, label "SUNNY OAT — Orange Cream".
Visual: bottle held by the neck with three fingers, label toward the camera (grip: 8); the pour is a smooth opaque orange stream (1, 4); the milk turns peach — orange streaks then uniform pale peach over ~2 s (1); no fizz, no foam (4); no condensation (5); glossy plastic shows a soft window highlight (3, 6); at this MCU the wordmark "SUNNY OAT" is readable, sub-line not (7).
Audio: <smooth pour, no fizz>; line changes to "the orange cream one is elite" (12) [Q4a: paraphrase allowed] or the line is cut [verbatim].
Text: overlay "so good 😍" is not generated (11); no hashtag.
Behaviour: same beat (pour) — no change of function (14).
Props: glass, milk, ice kept (16); straw kept.
REMOVE: BRAND X logo/wordmark on the can, the red-and-white colourway, the overlay hashtag "#brandx" — nothing of the original brand remains in the frame, in the reflection on the fridge door, or in the dialogue (20).
Needs-owner-decision: no.
```

### 4.2 Global rules (top of the file, before the entries)

```markdown
# Swap map — <run-id> · original: <entity> → ours: <slug>
Global invariants (repeat in every prompt's PRODUCT block):
- Product identity: <brand> <name> <variant> <size>; label text "<verbatim>"; logo <placement>; colours <hex>.
- Grip rule: <how it is held, which hand, finger positions>; table rule: <footprint, orientation, label to camera>.
- Content rule: <colour, opacity, viscosity, carbonation>; mixing results: <list from §3>.
- Sound rule: <pour/fizz/crunch/click … in <> notation>.
- Dialogue rule: original brand words → <ours or cut>, per Q4a.
- Text rule: no overlays generated; world text with the original brand replaced/removed.
- Removal rule: no logos, labels, watermarks, wordmarks, colourways, handles, hashtags, jingles of <original brand> anywhere (frame, reflections, audio, text).
Moments where the product appears: M01 … M12 (12 moments, 31.4 s of screen time).
Needs-owner-decision items: <list or none>.
```

### 4.3 Machine-readable mirror — `30-decisions\swap-map.json`
`{"original_entity":"e1","product_slug":"…","moments":[{"id":"M03","start_s":6.2,"end_s":9.5,"shot":3,"beat":"b04","keyframe":"…","changes":{"visual":[…],"audio":[…],"text":[…],"dialogue":[…],"remove":[…]},"needs_owner_decision":false}]}`

## 5. Quality bar

- Every moment has an entry; entries cite a keyframe; nothing is described that the planner did not see.
- Colour results are named nuances (peach, mint, tan), not "mixes nicely".
- Grip/size statements match the spec's dimensions (a 16 oz bottle is not "held between two fingers").
- The removal line exists in every entry; the product-consistency lens fails any prompt missing it.
- For the edit approach the same entries become the WHAT CHANGES lines of each segment's prompt
  (`edit-prompt-template.md`), timed to the segment's own seconds.
