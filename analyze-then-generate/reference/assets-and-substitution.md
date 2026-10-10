# Client assets and substitutions

Load this when asking for assets (the Analyze Mode project stage, and each video in Edit Mode) and
when planning any substitution.

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
| Physical product or object | A **canonical template** (clean views: front, back, side, top; real dimensions if known) plus **variants** (colours, flavours, label designs), ideally one folder per product. When the product is handled on screen, also a view of it **ready for use** (the cap flipped open, the tab up, the pack opened), used only for a scene that starts in that state: a view that shows a later state than the scene's t=0 leaks it into the first frame (`anomaly-catalog.md` §2.3) |
| Contents samples | For products that are poured, eaten or applied (a drink, a gum, a food, a cream): one photo per variant of the **contents themselves** (the drink in a clear glass, a gum piece, the cream on a finger: colour, clarity, bubbles, texture, shape), named or placed with its variant. Used by the "contents" form (`generation-system.md` §4b.0). They are often among the supplied files without a label: look for them (a pour, a glass of the drink, a texture swatch, a lifestyle shot that shows the contents) |
| Person / character / mascot | Face close-up + full body + outfit(s), one folder per character. Note any props in the photos (a glass, a cup, a snack): the plan turns each into the product's contents or excludes it (`generation-system.md` §4b.5) |
| Software / app / website | Real screenshots or screen recordings of the exact screens |
| Brand | Logo files, palette. Brand fonts are listed but not used: CapCut text always uses the house text style (`capcut-assembly.md` §3) |
| Place / style | Environment photos, style references |

## 2. Understanding the supplied assets (autonomous)

Inputs:
- `30-assets/<scope>/asset-inventory.md`: ids, sub-folder groups, filename hints;
- `asset-previews.md`;
- `assets-sheet-*.jpg`: every supplied image, labelled with id and path;
- `docs/`: extracted text of supplied documents. Rules found in them (brand books, dos and don'ts,
  legal and claims notes, ambassador lists) are extracted into `30-assets/guardrails.md` and drive
  which references may be picked and what must be edited in them (`brand-guardrails.md`).

Steps:
1. **Look at the contact sheet** (and full previews where detail matters). Filename hints are only
   hints; the image decides.
2. **Group files into entities.** One entity per distinct product, object, character, interface,
   brand kit, environment or sound. Sub-folders usually separate entities, but verify visually:
   - two different products in one folder are two entities;
   - two photos of the same item in different folders are one entity.
3. **For each product or object:** choose the canonical template: the view that best shows the true
   geometry, or the file the user named template/canonical. List the other views; mark variants
   (appearance-only differences); take real dimensions and materials from supplied specs: height,
   width or diameter, depth, in cm, and the volume. When no spec gives them, use the category's
   standard size from `anomaly-catalog.md` §2.7 and mark it [I]; never read a size off the
   product's own photo. Every plan reckons the product's size in every shot from these numbers.
   - Link each **contents sample** (a liquid or texture photo) to the variant it belongs to, using
     the folder, the name and what the photo shows. It is the authority for that variant's contents
     (colour, clarity, bubbles, texture).
   - Never treat a contents sample as a separate product.
   - Write the product's **affordance sheet** (`anomaly-catalog.md` §1): parts, openings, the
     opening sequence, how it is used and held, the contact point, what it holds and how many, its
     states, real size, the orientation of its mark, and what it cannot do. Take it from the images
     and specs; where an image does not show a part (the spout side of a lid), say so and keep the
     use to what is known.
3b. **Product insights (Create; useful in Recreate too).** Write, per product, the block that lets
   ideation start from what is genuinely engaging about *this* product instead of from the
   references' scenes: `30-assets/product-insights.md` (`creative-direction.md` §5.0b). Use the
   supplied images, specs and documents only, tagged [A] / [E] / [I]; a gap is written "not
   supplied" and is never filled from the references or invented:
   - **What it is and what it does for someone:** the need, desire or small pleasure it serves, in
     one line a user would say.
   - **Who and when:** the people it is for, the situations and moments it belongs to, the
     audience cues in the documents.
   - **What reads on camera:** its visual, sensory and audible strengths (colour, texture, shine,
     motion, the sound it makes, the reveal when it opens, pours, unfolds or lights up): what a
     stranger would stop for.
   - **What it can honestly show, and how fast:** the demonstrations that are true to the
     affordance sheet, with the seconds each needs.
   - **Proof and claims** the documents allow, and those they ban (with the guardrail id).
   - **Identity and emotion it carries** (energy, focus, calm, indulgence, belonging, status,
     humour), as the documents or the packaging suggest.
   - **Objections and limits:** what it cannot do, what viewers may doubt, what must not be
     implied.
   - **Occasions and pairings:** seasons, places, the other things it naturally sits beside.
   - **Product truths:** three to six one-sentence facts a concept can be built on ("it opens
     with a loud crack", "it changes the colour of the water it dissolves in", "it fits one hand
     and one pocket"). They are the product's ingredients for ideation, the way the craft sheet
     holds the references' ingredients.
4. **For each character:** the best face and full-body views, plus the outfits present.
5. **Everything else:** logos, palettes, UI screenshots, environments, audio (voice, music). Fonts
   are listed only: overlay text always uses the house text style (`capcut-assembly.md` §3).
6. Write the registry (§3). Ask **one** consolidated question only when a consequential ambiguity
   cannot be resolved by looking. Otherwise continue without asking.

## 3. Asset registry — `30-assets/registry.md` and `state.json → assets`

One row per asset:

| id | type | role | files (local) | canonical? | variant_of | views | real size / materials / notes | affordances (parts · openings · sequence · use + contact · contents/count · states · mark · impossible) | media_ids (+url) | element_id | uses |
|---|---|---|---|---|---|---|---|---|---|---|---|

- **Canonical templates** are authoritative for size, proportions, shape, curves, silhouette,
  construction and packaging structure.
- **Variants** may change surface appearance only. They inherit the canonical geometry unless the user
  says otherwise.
- **Characters:** when several approved characters exist and no assignment is given, rotate them
  across videos to balance usage and fit each direction. Record `uses`, and do not reuse the same
  character every time.
- **Upload once, reuse everywhere:** keep the `media_id` / `url` per file hash and reuse it across
  videos. Create Elements (`show_reference_elements create`) for characters, products and places when
  the selected model supports Elements (Kling 3.0, Seedance 2.0, Cinema Studio Video 2 / 3.0); store
  the `element_id`.

Scopes:
- `project`: Analyze Mode. The assets were dropped once at the start, and every video picks from them
  through the asset plan without asking again.
- `video-NN`: Edit Mode. The files for that edit, each bound to its operation and target (e.g.
  `replace → target 2`, `swap → person 1`).

Only the registry of the right scope feeds a generation.

## 4. Substitution map (per video)

Generalise beyond "product swap". Any analogous replacement is possible:
- person → approved character;
- product → client product;
- interface → client interface;
- brand → client brand;
- prop → prop;
- location → location;
- digital asset → digital asset;
- physical → representational (e.g. a service shown as its deliverable).

| source entity [E] | appears (t ranges) | action it performs | target entity [A] | substitution type | preserve from source | adapt | notes |
|---|---|---|---|---|---|---|---|

- Preserve the useful structure, behaviour, action, pacing, cinematic logic and engagement mechanism.
- Replace identity-specific elements.
- Do not keep source identities, competitor products, featured third-party branding, usernames,
  overlay text or watermarks (`generation-system.md` §9b). Incidental background decor and
  clothing logos are fine and stay.
- For each row, fill the integration analysis in `generation-system.md` §4 (scale, geometry, grip,
  light, context, states).

**Product as contents → contents row (Analyze Mode).** The reference's vessel or form and its action
stay; what is inside becomes the chosen variant's contents (from its contents sample); the package
stands nearby, opened:

`<cup of pink drink> | t ranges | poisoned, stirred, drunk | <product variant> + its contents sample | contents | the vessel, the action, the story | the liquid; the package placed beside | …`
`<gum pellets in his palm> | t ranges | shaken out, one tossed into the mouth, chewed | <product variant> + its contents sample | contents | the hand, the action, the story | the pellets; the opened pack on the table, one fewer | …`

**Nothing analogous in the reference → placement row (Analyze Mode).** When the reference contains
nothing the client's product or object can replace, its row reads:

`— (none analogous) | — | — | <client entity> | placement | the whole story | anchor | …`

- The client entity is placed naturally per `generation-system.md` §4b:
  - at an anchor that fits its size and use: in hand, on a surface or elsewhere in the
    environment for a handheld item; where such things stand for a large one (a car at the curb);
    on a device in use for software;
  - noticed, not featured;
  - on one persistent anchor;
  - matched to the plate.
- It is never dropped because nothing could be swapped.
- An unrelated source object is never bent into a swap.

## 5. Getting references into the model (by capability)

| model capability (see `models/index.json`) | strategy |
|---|---|
| Multi-reference (`image_references`, optionally `video_references` / `audio_references`) — Seedance 2.0/2.5, Wan 3.0 / 2.6, MiniMax H3, FLUX 3 Video, Gemini Omni, Grok 1.5 | Attach the canonical views and character references directly. Declare **one role per reference** in the prompt, using the model's syntax (multiple views of one item jointly define one entity). Attach a source video as a motion or camera reference only in **Recreate** (or Edit Mode), with explicit exclusions (its people, products, text and branding are not inherited). **Create never attaches a reference video** |
| Elements (`<<<id>>>`) — Kling 3.0, Seedance 2.0, Cinema Studio Video 2 / 3.0 | Create Elements once per project asset and cite them in the prompt |
| Start-frame-only — Veo 3 / 3.1, Kling 2.6 / 3.0 Turbo, Happy Horse, Grok, Hailuo, Wan 2.7, Seedance 1.5, Cinema Studio v1 (and anything where exact geometry matters most) | **Build a 9:16 start frame first** with an image model that takes several references (`nano_banana_pro`, `gpt_image_2_5`, `seedream_v5_pro`): the approved character, the client asset at correct scale, grip and lighting, and the environment. A natural placement is already at its anchor in this frame, with a contact shadow and the scene's light (`generation-system.md` §4b). Use `aspect_ratio:"9:16"` and at least 720×1280 output. **Check the frame against the canonical template before animating**: it becomes the geometry authority for that clip. Its `job_id` can be passed directly as `medias[].value` |
| Edit (source video + references) — Seedance 2.5 `video_edit` / `ad_multiplier`, Kling 3.0 Omni Edit, Genjutsu, Gemini Omni 1.1 edit, FLUX 3 Video Edit | The source video comes first (already 9:16), then the asset images in `@ImageN` order. Replacements are bound to their images, and each replaced source entity gets an exclusion sentence |

Useful image utilities for references (all cost credits; preflight when possible):
- `image_background_remover` / `remove_background`: a clean product cut-out;
- `nano_banana_2` or `seedream_v5_pro` with `is_inpaint`: cleaning text from a start frame;
- `flux_2_pro_outpaint` / `outpaint`: extending a frame to 9:16 without stretching.

## 6. Fidelity rules

- A client asset is **never deformed** to fit the source object's shape, size or packaging. Change
  the staging instead.
- Labels, logos and UI text on the client's **real** asset may appear because they belong to the
  asset. Source-brand text never appears.
- When fidelity matters more than motion complexity, prefer a start frame or reference with the exact
  asset and simpler motion (one grip, one move) over an ambitious action that risks deformation.
- Record in the brief which asset file is the authority for each entity.
- A product is used only through its real opening or control, after its preparation step, with the
  contact point of its affordance sheet; a swapped product with a different opening gets a planned
  grip that keeps the source hand path (`anomaly-catalog.md` §2.2, `generation-system.md` §5c.4).
