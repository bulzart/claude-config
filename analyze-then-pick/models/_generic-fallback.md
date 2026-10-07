---
guide: _generic-fallback
title: Fallback guide for a model without a dedicated guide
higgsfield_model_ids: []
guide_version: 1.0
last_verified: 2026-09-30
documentation_depth: none
---

# Fallback — a live Higgsfield model with no dedicated guide yet

Use this only when the user selects a video model that appears in the live `models_explore` catalog
but has no entry in `models/index.json`. Tell the user once that no researched guide exists and that
prompting follows conservative general rules. They can add a guide later (see `README.md` → "Adding
a model").

## 1. Build the parameter surface from the live catalog
Call `models_explore {action:"get", model_id}` and record:
- every parameter (name, values, default);
- the media roles;
- the durations and aspect ratios;
- `supports_unlim`.

Map the fixed output format:
- `aspect_ratio:"9:16"` if listed;
- the parameter whose options include 720p (or the closest tier);
- if no 9:16 is listed, a 9:16 start frame or source, plus `atp.py conform`.

Preflight with `get_cost` and read `adjustments`: they reveal ignored or unsupported parameters.

## 2. Look for official guidance before writing the prompt
Do a quick search for the provider's official prompt guide or example prompts (WebSearch/WebFetch)
and write a short pattern card (information order, temporal notation, camera vocabulary, reference
syntax, length) to `<run>/50-requests/<model>-pattern.md`. Label anything uncertain.

## 3. Conservative prompt defaults (when no official guidance is found)
- One scene, one main action with a visible cause and an explicit end state, and one camera behaviour.
- Order: subject (bound to its reference) → action over time (first… then… ends with…) → setting →
  light (direction, quality, colour) → camera → audio (if supported) → exclusions.
- Keep the prompt under ~120 words for ≤ 8 s. Chronological sentences, no keyword soup.
- References: state the role of each attached input ("the first image defines the character's face
  and outfit; the second defines the product's exact shape and label").
- Exclusions in one short sentence ("No on-screen text, captions or watermarks.").
- Physical and continuity anchors from `reference/generation-system.md` §3–§4 (states, contact,
  scale, light inheritance).
- Counts, openings and permanence from `reference/anomaly-catalog.md` §3: every multiple with its
  number per stage, every use as initial state → operation on the named part → result with the
  contact point, counts and states restated after exits and cuts, one exclusion per product for its
  own wrong use.

## 4. Extra QC
- Treat the first output as a probe: use a short duration first when cost matters.
- View the full storyboard (`atp.py qc`, with `--dense` on the plan's checkpoints,
  `reference/anomaly-catalog.md` §4) before continuing the set.
