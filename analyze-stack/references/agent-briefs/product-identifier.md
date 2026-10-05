# product-identifier — agent brief (Stage 3p; one agent; modes `identify` | `correct` | `relookup`)

Load first: `LAYOUT.md`, `references\product-library.md` (layout, lookup order, save/refresh rules),
`references\product-spec-template.md` (the spec sheet format and evidence tags), `references\blending-rules.md`
§2 (which physical properties the swap will need).

## Purpose
From the owner's samples, identify the EXACT product (brand, product name, variant, size, IDs, label
text, logo placement) and its physical properties and behaviours; when samples are not enough, use the
local product library, then the web by exact label/ID; write the run's product spec and stage a
product-library entry for reuse across runs. The main session asks Q1b from your summary.

## Inputs
`<run>\00-input\product-images\*` (everything the owner dropped; may include links listed in
`00-input\product-links.txt`), the owner's typed details (Notes / Answers: Q1a free text), `product-library\index.json`
and any matching `product-library\<slug>\`, `20-analysis\entities.json` (the original product's row = Q1 entity),
`30-decisions\answers.json`. Mode `correct`: the owner's corrections (Notes). Mode `relookup`: the owner's new details.

## Outputs
- `30-decisions\product-spec.md` (template format) and `30-decisions\product-spec.json` (identity, physical, behaviours, images[], evidence).
- `30-decisions\product-id-summary.json` — the Q1b sentence fields:
  `{"brand":"…","product_name":"…","variant":"…","size":"…","label_text":"…","id":"… | none found","properties":["matte black glass jar","cream soy wax","8 oz","gold foil wordmark","opaque","~350 g"],"source":"samples | product library | web lookup (<url>)","gaps":["dimensions unknown"],"slug":"snow-scents-vanilla-pine-8oz"}`
- Staged library entry: `product-library\<slug>\spec.md`, `spec.json`, `images\` (cropped single views),
  `sources.md`, `history.md` (append one line), and `index.json` updated with `"confirmed": false`
  (the main session sets `true` after Q1b = "Yes, exact product"; on "Almost"/"No" you are re-run and overwrite the staged entry).
- Copies for the writers: `50-prompts\references\product-front.<ext>`, `product-label.<ext>`, `product-three-quarter.<ext>` (only the views that exist).

## Method
1. Inventory every sample: LOOK at each image with the Read tool at full resolution; read the label
   line by line; note logo placement, colours (name + approximate hex), cap/lid, transparency, fill
   level, any ID (UPC/EAN/ASIN/SKU/model), size marks. Optional OCR helper:
   `python -c "from rapidocr_onnxruntime import RapidOCR; import sys; r,_=RapidOCR()(sys.argv[1]); print(r)" "<image>"` — eyes are the judge.
2. Merge with the owner's typed facts (`stated`). Build the identity block; mark each field
   `observed | stated | library | web | unknown` with its evidence.
3. Library: match by ID, then brand+name (case/punctuation-insensitive), then label-text overlap ≥ 60 %.
   A hit chosen by the owner at Q1a ("Use my product library") is used as is unless the new samples contradict it.
4. Web lookup only for fields still `unknown` that the swap needs (dimensions, volume, content colour,
   material, carbonation, viscosity): WebSearch the exact label wording and IDs; WebFetch only pages that
   show the same label/ID; record URL + fetch date in `sources.md`; never take facts from a look-alike.
5. Physical properties and behaviours: fill every applicable row of the template §2–§3 in prompt-ready
   words with sounds; §5 "Differences vs the original" from `entities.json` observed properties
   (size/grip, content colour, transparency, carbonation, material, behaviour).
6. Images: crop samples to the product (PIL) for the library `images\`; keep originals in `00-input`;
   order the reference list front → label close-up → 3/4 → in-hand; note "contains a hand/face" where true.
7. Write all outputs; append `history.md`: `<date> · run <run-id> · identified from <source> · confirmed: pending`.
8. Modes `correct`/`relookup`: apply the owner's corrections as `stated` facts (they override
   observations only when the observation was marked estimate/unknown; a contradiction with a clear
   observation is reported in `gaps`), rerun steps 3–7, overwrite the staged files.

## Quality bar
- Minimum confident identification = brand + product name + one legible label image; otherwise say so in `gaps`.
- No field is guessed; the Q1b sentence contains only `observed/stated/library/web` facts.
- `properties` in the summary are the 3–6 that matter most for the swap (size/grip, content, transparency, finish, carbonation/texture, weight class).

## When evidence is missing
List it in `gaps` (the main session tells the owner what is missing through the Q1b options). Never
fill a field from a similar product, a stock image, or a brand's other variant.
