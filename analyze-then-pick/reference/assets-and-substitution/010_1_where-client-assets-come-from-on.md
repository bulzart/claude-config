## 1. Where client assets come from: only the user

The optional **examples folder** (the user's own finished videos) is not an asset source: it is
studied for the house approach (`analysis-protocol.md` §9) and never used as an input.

| mode | when | what the user drops | what the command does |
|---|---|---|---|
| **Analyze** | **once, at the start**, with the references folder | Everything the new videos may use: product samples, characters, logos, interface screenshots, environments, specs. Any mix of files and folders | Inventories them (`inventory --as assets`, scope `project`) and understands them (§2). Then it **picks from them autonomously** for every video (the asset plan, command A7). It does not ask again |
| **Edit** | **per edit, per operation**, after the user picks the operations (Replace, Swap, Remove, Insert, …) | The files for each chosen operation, e.g. the replacement product's views for *Replace* and the character for *Swap* | Registers them for that edit only (`--as assets --scope video-NN`) and binds each file to its operation and target |

Hard rules:
- **Never search, detect or infer client assets inside the references folder or the edit-source
  folder.** They can contain other products, several samples or entirely different executions; every
  file there is reference material.
- Never reuse another edit's files unless the user says "same files as video K".
- Never invent a client identity silently. If a concept needs something that was not supplied:
  1. **adapt the concept** to what was supplied (e.g. hands-only POV when no character was given);
  2. otherwise ask once: drop the element, the user adds files, or a candidate reference is generated
     for their approval (`generate_image`, e.g. `nano_banana_pro` / `gpt_image_2_5` / `soul_2` for
     people), used only after they approve it.

What a well-prepared asset set looks like (share this only if the user asks):

| asset type | ideal files |
|---|---|
| Physical product or object | A **canonical template** (clean views: front, back, side, top; real dimensions if known) plus **variants** (colours, flavours, label designs), ideally one folder per product. When the product is handled on screen, also a view of it **ready for use** (the cap flipped open, the tab up, the pack opened), used only for a scene that starts in that state: a view that shows a later state than the scene's t=0 leaks it into the first frame (`anomaly-catalog.md` §2.3). A real shaded render of the product in a room (a photo or an earlier take) is the best source of a size-and-place guide, and its label close-up is sharp at the video's pixel scale (`generation-system.md` §4b.6) |
| Contents samples | For products that are poured, eaten or applied (a drink, a gum, a food, a cream): one photo per variant of the **contents themselves** (the drink in a clear glass, a gum piece, the cream on a finger: colour, clarity, bubbles, texture, shape), named or placed with its variant. Used by the "contents" form (`generation-system.md` §4b.0). They are often among the supplied files without a label: look for them (a pour, a glass of the drink, a texture swatch, a lifestyle shot that shows the contents) |
| Person / character / mascot | Face close-up + full body + outfit(s), one folder per character. Note any props in the photos (a glass, a cup, a snack): the plan turns each into the product's contents or excludes it (`generation-system.md` §4b.5). An identity image carries the face and nothing else: clothing with lettering the frame would cut, or a garment unlike the source's kept one, is cropped away (head and neck on a neutral grey), and a selfie photo's lettering is read first and the photo flipped when it is mirrored (`anomaly-catalog.md` §2.17, `generation-system.md` §5c.2b) |
| Software / app / website | Real screenshots or screen recordings of the exact screens |
| Brand | Logo files, palette. Brand fonts are listed but not used: CapCut text always uses the house text style (`capcut-assembly.md` §3) |
| Place / style | Environment photos, style references |

