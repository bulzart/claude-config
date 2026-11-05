---
name: neurogum-package-forms
description: "Neurogum videos: use the updated official samples (grouped folders), gum pouch + small carton only, never the big box; rotate all five gum flavours"
metadata:
  node_type: memory
  type: feedback
  originSessionId: fa5bf234-ecf9-446e-a53f-9818d56c6f19
  modified: 2026-10-29T17:14:06.215Z
---

For Neuro / Neurogum videos, the product must match the **updated official samples** in
`Documents/neurogum/assets/product_samples_and_designs`. On 2026-10-07 they were grouped into folders by line, form and flavour:
- Gum - Extra Strength: Pouch 90 pieces and Carton 9 pieces, in Peppermint and Spearmint.
- Gum - Energy & Focus: Carton 9/6 pieces in Peppermint, Spearmint, Wintergreen, Watermelon and Cinnamon, plus single sachets.
- Gum pieces (renders).
- Mints - Energy & Focus: tins and pouches. (The mint single-sachet folder was removed by the user on 2026-10-13, on purpose; gum sachets remain.)

The older product sheet design (light-blue pouch, dark-blue caffeine band on every form) is outdated. Videos built from it were rejected by the user ("the neurogum aren't correct").

**Why:** the user said so on 2026-10-06/07:
- "try to not use the big package … rather the pouch and the small package";
- "we did update the official samples";
- for flavours, "Rotate all five" (superseded on 2026-10-13: Peppermint and Spearmint only, see below).
- The user also said "pick whats best", so the forms below were the agent's own pick.

**How to apply:**
- Use the gum pouch (the Extra Strength 90-piece) or a small 9-piece carton only, never a big multi-pack box.
- Use gum, not mints, unless mints are asked for.
- Don't use the opened carton with the blister card sticking out of the top as a placement.
  - On 2026-10-07 the user rejected the two videos that used it ("the package is not the one should be used, use different packages").
  - Use closed cartons (9-piece or 6-piece) instead.
  - Opening a carton as an on-screen action, where the source has the person open something, was not objected to.
- Vary the package form across a batch: pouch, 9-piece carton, 6-piece carton, line-up. Don't use the pouch every time.
- **Flavours (updated 2026-10-13, run 20261013-230824-13): Peppermint and Spearmint only**, rotated across the batch. The user chose this over "rotate all five" when the client guardrail document was put next to the old rule ("Feature peppermint or spearmint. Don't build a spot around cinnamon or wintergreen."). The pouch exists only in these two flavours. This replaces the 2026-10-06/07 "rotate all five".
- Re-check that folder for new designs before each Neurogum batch; the user adds designs there.
- **Dimensions authority (added by the user 2026-10-08, restructured 2026-10-13):** the `product_properties.txt` inside each leaf folder (one per form + flavour, e.g. `Gum - Extra Strength/Carton 9 pieces - Peppermint/product_properties.txt`; the two Gum group folders and `Gum pieces (renders)` also have one). Read the matching leaf file before writing any Neurogum prompt. The master `product_samples_and_designs/product_properties.txt` and the `Mints - Energy & Focus/product_properties.txt` group file were deleted by the user on 2026-10-13 deliberately ("nothing was on accident at all"): never recreate them, and never re-add removed samples to the txt files. Key values: 9- and 6-piece cartons share one die, ~7.5 × 7.5 × 1.6 cm matte paperboard (nearly square, slightly taller than wide, ~25 g); Extra Strength pouch 17.9 × 10.2 × 4.6 cm with a zipper below the top seal, tear notches, gusseted bottom; gum piece ~15–16 mm round tablet, 7–8 mm thick, white with coloured flecks (green Spearmint/Wintergreen, blue Peppermint, red Cinnamon), embossed wave N. Wan 3.0 Prime once rendered a 6-piece carton at half-torso size: always state the real size against a scene object (e.g. "a third of the water bottle's height, smaller than his hand"), and treat an oversized carton as a regenerate reason.
- **Size recipe that the client approved (2026-10-29):**
  - The user called three flat-lying carton videos "just perfect": 02 beside a phone, 04 beside a laptop, 10 on a counter by a forearm.
  - At the user's request, the recipe and the misses are written in the "Generation notes" section of `Documents/neurogum/assets/product_samples_and_designs/README.md`. Read it before any Neurogum generation.
  - Core of the recipe:
    - the carton is a slim flat card box: as wide as a phone, half its length, as thin as a phone;
    - a cut-out of the real photo `product_comparison_and_reference/IMG_6917.jpg` (carton alone, on grey) goes in as the second product image;
    - each neighbour gets its own sentence, with a bare band between it and the carton;
    - one constant size in every clip.
  - Never send a whole real photo: a gaming mouse pad with its logo bled into the scene.

Related: [[capcut-text-preset-locked]], [[celsius-no-orange-flavor]].
