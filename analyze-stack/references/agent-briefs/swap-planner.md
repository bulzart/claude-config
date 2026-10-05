# swap-planner — agent brief (Stage 3s; one agent per ≤ 60 s segment where the product appears, plus one `reconcile` agent)

Load first: `LAYOUT.md`, `references\blending-rules.md` (the 20-point checklist, colour-mixing table,
swap-map entry format, global rules), `references\physics-rules.md` §3–§5, §7, §10 (accumulation,
liquids, hands, timing, sound), `references\product-spec-template.md` §5, `seedance\SEEDANCE-EDIT.md` §4.1
and §5 (what an edit prompt can change; audio is muxed from the source in the edit approach).

## Purpose
Work out EVERY visual, audible and textual consequence of replacing the original product (Q1 entity)
with ours, at every moment it appears — so that both replication prompts and edit prompts carry the
swap consistently and nothing of the original brand remains.

## Inputs
`30-decisions\product-spec.md` (+ `.json`), `20-analysis\visual.md`, `entities.json` (the Q1 entity row:
appearances, held_by, observed properties, brand marks), `audio.md` §3 (brand mentions in speech),
`beat-map.json`, `10-measure\keyframes\shots\`, `keyframes\sampled\`, `ocr.json`, `30-decisions\answers.json`
(Q1 entity, Q2 approach, Q4a when Mode 3), `30-decisions\edit-intent.md` when the approach is edit.
Notes: your segment range (`segment 2 of 3: 00m60.00s–01m20.00s`) or `mode: reconcile`.

## Outputs
- Segment agents: `30-decisions\swap-map-segNN.md` (entries in the §4.1 format, one per moment `M##`).
- Reconcile agent: `30-decisions\swap-map.md` (global rules §4.2 on top, then all entries renumbered
  in time order) and `30-decisions\swap-map.json` (§4.3). A single-segment video: the one agent writes
  the final files directly.

## Method
1. List every moment the original product is visible, audible, named or implied within your range —
   from `entities.json` appearances, `audio.md` brand mentions, `ocr.json` text that names it, and your
   own LOOK (Read tool) at every shot keyframe and the 1 fps frames around each appearance (reflections, shadows,
   a cup it was poured into, a wrapper on the table, a hand shaped around it).
2. For each moment apply the 20-point checklist against `product-spec` (ours) vs the observed original;
   write only the consequences that differ, in prompt-ready words; name colour results as nuances
   (peach, mint, tan) using the mixing table; state grip/size from the spec's dimensions; sounds in `<>`.
3. Behaviour differences: when the original's action has no analogue for our product (pour vs solid,
   chew vs drink), propose the closest same-function beat and flag `Needs-owner-decision: yes` with
   the alternatives in one line each.
4. Every entry ends with the REMOVE line (logo, wordmark, colourway-as-brand, hashtag, handle, jingle,
   reflections) — nothing of the original brand may remain anywhere.
5. Edit approach: add to each entry the operation sentences the edit-prompt writer will use
   (`Replace only … in @Video1 with … from @Image1`, `Remove only …`) and note which sounds will NOT
   change because the source audio is muxed back (`SEEDANCE-EDIT.md` §5) → `post-edit SFX: <list>`.
6. Reconcile: merge segment files, keep one entry per moment (resolve duplicates by the more specific
   description), write the global rules (identity, grip, table, content, sound, dialogue, text, removal),
   count moments and total screen time, list needs-owner-decision items, write the JSON mirror.

## Quality bar
- Every moment has an entry citing a keyframe you looked at; every entry has all four blocks
  (Visual / Audio / Text / Behaviour) plus Props and REMOVE.
- Colour results are never "mixes nicely"; grips never contradict the spec's size/weight class.
- The dialogue rule follows Q4a (verbatim → cut the line; paraphrase → replace with our name/property).

## When evidence is missing
If a property of ours is `unknown` in the spec (e.g. viscosity), write the consequence conditionally
("if the liquid is still: smooth pour, no fizz") and add it to needs-owner-decision. If a moment's frame
is ambiguous (product occluded), say "occluded at 00m12.40s–00m13.10s; treated as present".
