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
4. **For each character:** the best face and full-body views, plus the outfits present.
5. **Everything else:** logos, palettes, UI screenshots, environments, audio (voice, music). Fonts
   are listed only: overlay text always uses the house text style (`capcut-assembly.md` §3).
6. Write the registry (§3). Ask **one** consolidated question only when a consequential ambiguity
   cannot be resolved by looking. Otherwise continue without asking.

