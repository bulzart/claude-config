# Product spec sheet template — `30-decisions\product-spec.md` (copied to `product-library\<slug>\spec.md`)

Written by the product-identifier agent from the owner's samples (Q1a), the product library or a web
lookup by exact label/ID. Rule: every field is `observed` (seen in a sample image, with the image path),
`stated` (owner text), `library` (from an earlier run), `web` (URL + date) or `unknown` — never guessed.
The Q1b confirmation sentence is built from the identity block + 3–6 key physical properties.

```markdown
# Product spec — <slug>
Identified: <YYYY-MM-DD HH:MM> · Source of identification: samples | product library | web lookup (<url>)
Status: confirmed by owner (Q1b) | pending

## 1. Identity
| Field | Value | Evidence |
|---|---|---|
| Brand | Snow Scents | observed: images\front.jpg |
| Product name | Vanilla Pine Candle | observed |
| Variant / flavour / scent | Vanilla Pine | observed (label) |
| Size / volume / weight | 8 oz (227 g) | observed (label bottom) |
| IDs (UPC/EAN/SKU/ASIN/model) | UPC 0 12345 67890 5 | stated by owner |
| Label text (verbatim, line by line) | "SNOW SCENTS" / "Vanilla Pine" / "hand-poured soy" / "8 oz" | observed at full res |
| Logo placement | wordmark centred on the front label, 30 % of label height; small icon on lid | observed |
| Category | home fragrance / candle | stated |
| Product page URL | https://… | web |

## 2. Physical properties
| Property | Value | Evidence |
|---|---|---|
| Packaging colours | matte black jar (#1a1a1a), white label, gold foil wordmark | observed |
| Content colours | cream wax (#f3ead9); when lit: pale amber melt pool | observed / web |
| Transparency | jar opaque; wax opaque; melt pool translucent | observed |
| Viscosity / state | solid wax; liquid pool ~3 mm after 30 min | web |
| Carbonation / foam | n/a | — |
| Texture / finish | matte jar, glossy label, smooth wax top | observed |
| Material | glass jar, tin lid, cotton wick | observed |
| Shape / dimensions | cylinder ⌀ 7.5 cm × 9 cm, lid adds 1 cm | web |
| Weight class | ~350 g full — held one-handed, palm grip | web + inferred (mark as estimate) |
| Reflectivity | label glossy → specular streak under window light; jar matte → soft shading | observed |

## 3. Behaviours (only the ones that apply to this product and to the moments in the video)
| Behaviour | Description in prompt-ready words | Sound |
|---|---|---|
| Opening | lid lifts straight up with slight friction; no hiss | <soft lid lift> |
| Pouring | n/a | — |
| Melting | wick lights in ~1 s; flame 1.5 cm; melt pool widens over minutes (not seconds) | <match strike, faint flame> |
| Mixing / dissolving | n/a | — |
| Chewing / crunch | n/a | — |
| Bouncing / dropping | glass: does not bounce; dull thud on wood | <dull thud> |
| Spraying / pumping | n/a | — |
| Foaming / fizzing | n/a | — |

## 4. Reference images (single-view, no text/people other than the product; ≥ 720 px; the order is the @Image order for prompts)
| # | File | View | Use in prompts | Notes |
|---|---|---|---|---|
| 1 | product-library\snow-scents-vanilla-pine\images\front.jpg | front, label centred | identity: proportions, colours, label layout | background is white studio — "do not copy the background" |
| 2 | …\label-closeup.jpg | label macro | logo + wording legibility | |
| 3 | …\three-quarter.jpg | 3/4 with lid | lid geometry | |
| 4 | …\in-hand.jpg (optional) | scale reference in a hand | grip and size | contains a real hand — allowed on Higgsfield; ModelArk rejects real faces only |

## 5. Differences vs the original product in the video (filled by the swap planner; feeds swap-map.md)
| Aspect | Original | Ours | Consequence |
|---|---|---|---|
| Size / grip | 12 oz slim can, 3-finger grip | 8 oz jar, full palm | hand pose changes in shots 1–3 |
| Content colour | red liquid | n/a (solid) | the pour beat is replaced by a lid-off + light beat (Q2e / swap-map) |
```

Rules:
- Sample images that contain people, other products or text are cropped to the product before they are
  saved to the library (`images\`), keeping the originals in `00-input\product-images\`.
- Minimum for a confident identification: brand + product name + one label image. Anything less →
  Q1b option "Almost — I will correct details" is expected; say what is missing.
- The spec sheet never contains a claim the identifier could not see, read or fetch.
