# Product library — `C:\Users\Bulzart\.claude\analyze-stack\product-library\`

The persistent dataset the owner brief asks for: "it looks the product up in our own dataset (a local
product library the skill maintains and reuses across runs) or on the internet … and saves a product
spec sheet for future runs". Non-negotiable rule 4: the library is updated whenever a product is
identified/confirmed.

## 1. Layout

```
product-library\
  index.json
  <slug>\
    spec.md            ← references\product-spec-template.md format
    spec.json          ← machine-readable mirror (identity, physical, behaviours, images[])
    images\            ← single-view reference images, cropped to the product (front.jpg, label-closeup.jpg, three-quarter.jpg, …)
    sources.md         ← where each fact came from (sample path, URL + fetch date, owner statement)
    history.md         ← one line per run that used or refreshed this entry
```

`slug` = lowercase brand-product-variant-size, ASCII, hyphens: `snow-scents-vanilla-pine-8oz`.

`index.json`:
```json
{
  "schema": "analyze-stack.product-library/1",
  "updated": "2026-09-16T14:02:00-05:00",
  "products": [
    {"slug": "snow-scents-vanilla-pine-8oz", "brand": "Snow Scents", "name": "Vanilla Pine Candle",
     "variant": "Vanilla Pine", "size": "8 oz", "ids": {"upc": "012345678905"}, "category": "home fragrance",
     "label_text": ["SNOW SCENTS", "Vanilla Pine", "hand-poured soy", "8 oz"],
     "images": ["images/front.jpg", "images/label-closeup.jpg"], "confirmed": true,
     "last_used_run": "20260916-101500-snowscents", "last_refreshed": "2026-09-16"}
  ]
}
```
If `index.json` does not exist, the identifier creates it with an empty `products` list.

## 2. Lookup order (product-identifier agent, Stage 3p)

1. **Samples first** — every file the owner dropped at Q1a (`00-input\product-images\`) is opened with
   the Read tool; label text is read at full resolution (RapidOCR as a helper, eyes as the judge).
   The owner's typed details (brand, name, label text, variant, size, ID) are `stated` facts.
2. **Product library** — match by any ID, then by brand + name (case-insensitive, punctuation-free),
   then by label text overlap ≥ 60 %. A library hit that the owner selected in Q1a ("Use my product
   library") is used as is unless the new samples contradict it (then refresh).
3. **Web lookup by exact label / ID** — only when 1–2 leave identity or physical fields `unknown`:
   search the exact label wording and any ID (UPC/ASIN/SKU); use WebSearch + WebFetch; accept a page
   only if it shows the same label text/ID; record URL + fetch date in `sources.md`; take only observable
   facts (dimensions, volume, colour names, material, ingredient/content type). Never fill a field from
   a look-alike product.
4. Anything still unknown stays `unknown` and is listed in the Q1b sentence's gaps so the owner can
   correct it ("Almost — I will correct details").

## 3. When to save / refresh

| Event | Action |
|---|---|
| Q1b = "Yes, exact product" | write/overwrite `<slug>\spec.md`, `spec.json`, copy cropped images, append `history.md`, update `index.json` (`confirmed: true`) |
| Q1b = "Almost — I will correct details" | apply the corrections, re-identify (steps 1–3), ask Q1b again; save only on "Yes" |
| Q1b = "No — look it up again" | rerun steps 2–3 with the owner's new details; ask Q1b again |
| Library entry older than 180 days or missing a field the swap needs | refresh from samples/web, keep the old file as `spec.<date>.md` |
| A run adds a better image (higher res, cleaner view) | add to `images\`, append to `spec.json.images`, never delete an image another run cited |

## 4. What the rest of the pipeline reads

- Swap planner: `30-decisions\product-spec.md` (the run copy) §1–3 and §4 image list.
- Prompt writers: image paths (copied into `50-prompts\references\` as `product-<view>.<ext>`) and the
  label text (verbatim) for the product invariants block.
- Generator: uploads each `50-prompts\references\product-*.{jpg,png}` once (uploads.json).
- Clip QA: label text + colours for the product-identity check (A05/A15).
