# Product spec â€” celsius-live-fit-sparkling-12oz
Identified: 2026-09-21 19:58 Â· Source of identification: samples (owner lineup + owner spec sheet) + owner notes; web used only to confirm carbonation / zero sugar and the can-size class
Status: confirmed by owner (Q1b)
Mode: identify Â· Run: 20260921-192043-monsters-celsius Â· Replaces: entity e1â€“e6 (six Monster Energy cans, S1â€“S6, 00m00.00sâ€“00m03.77s)

This is a PRODUCT FAMILY: one can structure shared by six flavour variants (Â§1â€“Â§3 describe the shared can once; Â§1b is the per-flavour table). The owner wants the six Monster slides replaced by Celsius cans "chosen randomly" from the lineup.

## 1. Identity (shared by all six variants)
| Field | Value | Evidence |
|---|---|---|
| Brand | CELSIUS | observed: 00-input\product-images\celsius-6pack-lineup.png (wordmark on every can); stated (product-notes.txt) |
| Product name | CELSIUS Live Fit Sparkling (energy drink) | observed: "CELSIUS" + "LIVE FIT" + "SPARKLING" on every can; stated |
| Variant / flavour | six flavours, left â†’ right in the lineup: Orange Â· Kiwi Guava Â· Wild Berry Â· Watermelon Â· Grape Rush Â· Cola | observed (top band + flavour line, legible at 3Ã— zoom); stated |
| Size / volume | 12 FL.OZ (355 mL) slim can | observed: "12 FL.OZ (355mL)" on the grey band of all six cans; stated |
| IDs (UPC/EAN/SKU/ASIN) | none found | no barcode legible in the samples (back-panel barcode is a blur); owner gave none |
| Label text, front, top â†’ bottom (verbatim, identical on every can except the two flavour lines) | "<FLAVOUR>" (top band, flavour colour) / small ring icon left of the logo / gradient "C" logo / "CELSIUS" + small registered-mark dot / "LIVE FIT" (flavour colour) / fruit artwork with rising bubbles / "SPARKLING" (black) / "<FLAVOUR>" (flavour colour) / "NATURAL FLAVOR WITH OTHER NATURAL FLAVORS" (tiny grey) / black band: "â€º ESSENTIAL ENERGY" Â· "â€º ACCELERATES METABOLISMâ€ " Â· "â€º BURNS BODY FATâ€ " (the mark after METABOLISM and FAT is a tiny footnote symbol, exact glyph unreadable) / grey band: "0 SUGAR" roundel + three activity icons (runner Â· cyclist Â· seated yoga figure) / "12 FL.OZ (355mL)" | observed at 3â€“4Ã— zoom of the lineup and the spec-sheet close-ups |
| Label text, back | orange header "NUTRITION FACTS" in the top band; white "Nutrition Facts" panel with black border: "Nutrition Facts" / "Calories 0" legible; serving lines, ingredient block and barcode unreadable at 90 px tile width | observed: celsius-orange-can-spec-sheet.png BACK tile (low-res) |
| Logo placement | gradient "C" mark centred in the upper third (â‰ˆ y 14â€“33 % of can height), â‰ˆ 40 % of can width, opening to the right; small ring icon at its upper left; "CELSIUS" wordmark centred just below it (â‰ˆ y 37â€“41 %), â‰ˆ 70 % of can width; "LIVE FIT" right-aligned under the wordmark | observed (lineup) |
| Category | beverage â€” sparkling energy drink, zero sugar | observed (label); web (brand page) |
| Product page URL | https://www.celsius.com/products/celsius/sparkling-orange/ (Orange; fetched 2026-09-21) | web |

## 1b. Per-flavour table (what changes between the six cans â€” everything else is identical)
Colours are sampled from the lineup at native resolution; small anti-aliased text lightens the sampled value, so hex values are approximate. Crops: `00-input\product-images\crops\front-<flavour>.png` (also in the library `images\`).

| # (lineup Lâ†’R) | Flavour (label text, top band AND under SPARKLING) | Flavour-text / LIVE FIT colour | Band colour (left strip of the claims band) | C-logo gradient (top-left arm â†’ top-right tip â†’ lower arm) | Fruit / art below the wordmark | Crop |
|---|---|---|---|---|---|---|
| 1 | ORANGE | orange (#d68647 â€“ #efb988) | orange (#e2a06e) | orange (#d98d15) â†’ orange (#da8321) â†’ silver-grey (#d7d7d7 â†’ #8f8f8f) | one orange wedge (half-slice), pith-white rim, three rising bubbles | front-orange.png |
| 2 | KIWI GUAVA | pink-red (#cf4251 â€“ #ea8691) | coral pink (#dd6e79) | pink-red (#bf7980) â†’ lime green (#71b03e) â†’ silver-grey | pink-fleshed guava half (left) + green kiwi half (right), bubbles | front-kiwi-guava.png |
| 3 | WILD BERRY | plum / berry magenta (#964365 â€“ #c4869f) | plum-magenta (#b07089) | crimson-magenta (#a91d47) â†’ berry (#9c2551) â†’ silver-grey | raspberry (red) with blueberries and blackberries clustered around it, bubbles | front-wild-berry.png |
| 4 | WATERMELON | red-pink (#cc4248 â€“ #e87a80) | watermelon red (#da696e) | red (#cd404d) â†’ red (#d0313b) â†’ silver-grey | one watermelon wedge, red flesh with black seeds, green rind, bubbles | front-watermelon.png |
| 5 | GRAPE RUSH | purple (#644269 â€“ #9b7c9f) | purple (#87688b) | wine-magenta (#8c2143) â†’ deep purple (#642052) â†’ silver-grey | bunch of red-purple grapes with a green leaf, bubbles | front-grape-rush.png |
| 6 | COLA | brown (#80463d â€“ #c4a199) | cola brown (#9c6b61) | caramel-orange-brown (#9b5413) â†’ dark brown (#823916) â†’ silver-grey | no fruit: a spray of small orange / red / brown dots (fizz burst), bubbles | front-cola.png |

Shared on every can: white body, black "SPARKLING", grey sub-line, black claims band, grey metallic band, "0 SUGAR" roundel, three activity icons, "12 FL.OZ (355mL)", black lid, silver rims.

## 2. Physical properties (shared)
| Property | Value | Evidence |
|---|---|---|
| Form factor | tall slim ("sleek") aluminium can, straight cylindrical body, slight neck taper to a narrower top rim; observed height:width â‰ˆ 2.97 : 1 in the lineup (body 184 px wide Ã— 546 px tall) | observed (lineup + spec sheet FRONT/SIDE tiles) |
| Dimensions | 355 mL sleek-can class; ~58 mm âŒ€ Ã— ~157 mm tall is the industry format for this volume (ESTIMATE â€” not from the label); third-party dimension sites list "6.25 in Ã— 2.6 in" (â‰ˆ 159 Ã— 66 mm) for Celsius cans â€” unverified, not a brand source | web + estimate (see sources.md) |
| Packaging colours (top â†’ bottom) | black lid (#2a2a2a) with a bright silver top rim (#e7e6e5); white body (#e2e2e2â€“#e6e6e6 as photographed, pure white in print) from the neck down to â‰ˆ 70 % of the height; black claims band (#1e1e1eâ€“#252525) â‰ˆ 70â€“79 %; flavour-coloured vertical strip on the LEFT edge of the black band only (â‰ˆ 8 % of can width); brushed grey metallic band (#5d5d5dâ€“#6b6a6a, lighter toward the edges) â‰ˆ 79â€“98 %; silver bottom rim (#979797) | observed (lineup, sampled) |
| Content colours | not visible (sealed can); liquid colour UNKNOWN for every flavour | unknown |
| Transparency | fully opaque metal can; no fill level visible | observed |
| Viscosity / state | thin carbonated liquid ("Sparkling"; brand page: carbonated) | observed (label) + web |
| Carbonation / foam | carbonated: opening gives a short hiss; a pour gives fine fizz and a thin short-lived foam ring (behaviour from product type, not seen in the samples) | label + web; behaviour = inference |
| Texture / finish | body: satin/semi-gloss printed aluminium (soft, wide vertical highlight, no mirror reflection); grey band: brushed-metal look with a horizontal highlight; lid: matte-black anodised look with a bright polished rim; pull tab dark | observed (lineup, spec-sheet TOP-DOWN and lying tiles) |
| Material | aluminium (printed sleeve/ink on can), standard stay-on-tab end | observed |
| Top / bottom finish | top: black lid ring, silver dome, standard stay-on pull tab (dark) with a score line; bottom: silver rim, recessed base (not visible) | observed (TOP-DOWN tile, lying tile) |
| Weight class | ~370â€“380 g full (355 mL liquid + can) â€” ESTIMATE; held one-handed, fingers wrap Â¾ of the circumference, thumb on the label side | estimate |
| Reflectivity | white body takes a soft vertical window/softbox highlight down one side and a soft shadow on the other; black band shows a faint glossy streak; grey band has a bright specular stripe; lid rim is the brightest specular point | observed (lineup shading) |
| Label wrap | the front artwork wraps the cylinder; the SIDE tile shows artwork edges at both silhouettes; the BACK tile shows the Nutrition Facts panel (the exact wrap layout between front art and nutrition panel is ambiguous in the sample â€” ESTIMATE) | observed (low-res) |

## 3. Behaviours (only the ones that could apply; the source video shows sealed, static packshots â€” none of these occur in the sample video)
| Behaviour | Description in prompt-ready words | Sound |
|---|---|---|
| Static packshot (the beat in this video) | can stands upright on its base, label centred to camera, no rotation; soft contact shadow under the base; no condensation (studio, room temperature) | none (music only) |
| Opening | thumb lifts the stay-on tab; short sharp pressure release, tab folds back into the recess | <sharp psst hiss, metal click> |
| Pouring | thin liquid, streams cleanly; fine fizz, thin foam ring that settles in ~2 s; liquid colour unknown (do not describe it) | <fizzing pour> |
| Condensation | only if shown cold: fine even beads on the white body and the grey band; none in the owner samples | â€” |
| Bouncing / dropping | light aluminium: hollow metallic clink, may dent, rolls if on its side | <hollow metal clink> |
| Mixing / melting / chewing / spraying / foaming | n/a | â€” |

## 4. Reference images (single-view; native resolution; order = @Image order for prompts)
All lineup crops are 200 Ã— 592 px; all spec-sheet tiles are â‰¤ 128 px wide (LOW resolution â€” see gaps). The backgrounds are white studio â€” "do not copy the background". No hands, faces or other products in any crop except `spec-front-pair-orange-kiwi.png` (two cans).

| # | File (library) | Also at (run) | View | Use in prompts | Notes |
|---|---|---|---|---|---|
| 1 | product-library\celsius-live-fit-sparkling-12oz\images\front-orange.png | 00-input\product-images\crops\front-orange.png | front | identity + colours for the ORANGE variant | soft floor shadow included |
| 2 | â€¦\images\front-kiwi-guava.png | â€¦\crops\front-kiwi-guava.png | front | KIWI GUAVA variant | |
| 3 | â€¦\images\front-wild-berry.png | â€¦\crops\front-wild-berry.png | front | WILD BERRY variant | |
| 4 | â€¦\images\front-watermelon.png | â€¦\crops\front-watermelon.png | front | WATERMELON variant | |
| 5 | â€¦\images\front-grape-rush.png | â€¦\crops\front-grape-rush.png | front | GRAPE RUSH variant | |
| 6 | â€¦\images\front-cola.png | â€¦\crops\front-cola.png | front | COLA variant | |
| 7 | â€¦\images\spec-three-quarter-orange.png | â€¦\crops\spec-three-quarter-orange.png | three-quarter | can geometry / neck taper | 91 Ã— 251 px, Orange only |
| 8 | â€¦\images\spec-side-orange.png | â€¦\crops\spec-side-orange.png | side | label wrap | 91 Ã— 251 px |
| 9 | â€¦\images\spec-back-orange.png | â€¦\crops\spec-back-orange.png | back | Nutrition Facts panel position | text unreadable |
| 10 | â€¦\images\spec-top-down-orange.png | â€¦\crops\spec-top-down-orange.png | top-down | lid + pull tab | 105 Ã— 112 px |
| 11 | â€¦\images\spec-closeup-upper-orange.png | â€¦\crops\â€¦ | label close-up (top band, C logo, wordmark) | logo legibility | grey background |
| 12 | â€¦\images\spec-closeup-middle-orange.png | â€¦\crops\â€¦ | label close-up (wordmark â†’ claims band) | label text | grey background |
| 13 | â€¦\images\spec-closeup-lower-orange.png | â€¦\crops\â€¦ | label close-up (fruit â†’ size line) | roundel row, size line | grey background |
| 14 | â€¦\images\spec-lying-side-orange.png | â€¦\crops\â€¦ | lying on its side | lid/rim geometry from the side | 172 Ã— 86 px |
| 15 | â€¦\images\spec-front-orange.png, spec-front-orange-b.png | â€¦\crops\â€¦ | front (spec-sheet duplicates) | fallback only | lower res than #1 |
| â€” | â€¦\images\spec-front-pair-orange-kiwi.png | â€¦\crops\â€¦ | TWO cans | not a single-can reference | keep for the library only |

Writer copies: `50-prompts\references\product-front-<flavour>.png` (six), `product-three-quarter.png`, `product-side.png`, `product-back.png`, `product-top-down.png`, `product-label.png` (= closeup-middle).

## 5. Differences vs the original product in the video (pre-filled from entities.json e1â€“e6; the swap planner completes it â†’ swap-map.md)
| Aspect | Original (Monster, e1â€“e6) | Ours (Celsius family) | Consequence |
|---|---|---|---|
| Size / format | tall slim 500 mL / 16 fl oz class can (estimate), ~2.7:1 h:w | 355 mL sleek can, ~2.97:1 h:w observed; shorter and slightly slimmer | in the packshot framing (can centred xâ‰ˆ240â€“480, yâ‰ˆ45â€“680 of 720) our can can fill the same box â€” same visual size on screen, proportions â‰ˆ 10 % slimmer; nobody holds it (no grip change) |
| Body colour per slide | six strongly different colourways (white, sky-blue, coral-pink, magenta, purple, green) â€” the colour-flicker mechanic | six WHITE-bodied cans; the difference is only the top-band/flavour text colour, the C-logo gradient, the fruit art and the band strip | the 0.57â€“0.73 s slide flicker reads as "the same white can" at 720 px; the variant signal must come from the fruit art + coloured strip (report Â§11 already flags this) â€” decision item for the swap planner |
| Brand marks | claw "M", "MONSTER", "ENERGY", "ULTRA"/"JUICE", flavour names, overlay "Who likes Monster?" | "CELSIUS", "LIVE FIT", "SPARKLING <flavour>", claims band | all Monster marks removed; the hook card must be re-authored in the edit (never generated) |
| Content / transparency | opaque, sealed, not visible | opaque, sealed, not visible; liquid colour unknown | no pour beat exists in the video â€” nothing to describe |
| Pose | upright cut-out packshot on white, no shadow | our lineup crops have a soft floor shadow | prompt/edit must state "on white, soft contact shadow or none" consistently across the six slides |
| Count | one can per slide, six slides | six variants available; owner: "chosen randomly" | random draw rule (with or without repeats, which six) = needs-owner-decision N1 (already open in report Â§11) |

## 6. Gaps / needs-owner-decision
- GAP-1 (resolution): every reference image is small â€” lineup crops 200 Ã— 592 px, spec-sheet tiles â‰¤ 128 px wide, below the template's â‰¥ 720 px guidance. Higher-resolution originals (one PNG per flavour â‰¥ 1000 px tall, and the spec sheet at its source size) would improve Seedance's label fidelity. needs-owner-decision: supply hi-res originals, or accept the current crops (upscaling is a paid Higgsfield tool and was not run).
- GAP-2: can dimensions/weight are estimates (355 mL sleek-can class); no brand source states them. Harmless for this video (no hands, no scale reference).
- GAP-3: liquid colour per flavour unknown (sealed cans) â€” irrelevant unless a pour beat is added.
- GAP-4: no UPC/SKU; back-panel text unreadable (Nutrition Facts, "Calories 0" only).
- GAP-5: the spec sheet's back/side tiles look like a rendered mock (blurred nutrition text, ambiguous label wrap); only the front artwork is treated as authoritative.
- Random-draw rule for the six slides (N1 in report Â§11): which flavours, in which order, repeats allowed or not â€” owner decision before the swap map.

