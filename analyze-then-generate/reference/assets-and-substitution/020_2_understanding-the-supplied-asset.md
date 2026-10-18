## 2. Understanding the supplied assets (autonomous)

Inputs:
- `30-assets/<scope>/asset-inventory.md`: ids, paths, kinds, sizes, sub-folder groups and `duplicate_of` for
  identical files (facts only: the inventory guesses no role from a file name);
- `asset-previews.md`;
- `assets-sheet-*.jpg`: every supplied image, labelled with id and path;
- `docs/`: extracted text of supplied documents. Rules found in them (brand books, dos and don'ts,
  legal and claims notes, ambassador lists) are extracted into `30-assets/guardrails.md` and drive
  which references may be picked and what must be edited in them (`brand-guardrails.md`).

Steps:
1. **Look at the contact sheet** (and full previews where detail matters). The inventory lists paths and
   facts and guesses no role from a file name: you confirm every role (product, character, logo, contents
   sample, ...) by looking at the asset; the image decides.
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
   - **Product truths:** up to six one-sentence facts a concept can be built on (numbered PT1, PT2, … within each product, cited `<product>/PT2` when a run has several products, so that the blend matrix and the plans can name them), as many as the supplied
     material supports ("it opens with a loud crack", "it changes the colour of the water it dissolves
     in", "it fits one hand and one pocket"). A truth the assets do not show is "not supplied", never
     invented. They are the product's ingredients for ideation, the way the craft sheet holds the
     references' ingredients.
4. **For each character:** the best face and full-body views, plus the outfits present.
5. **Everything else:** logos, palettes, UI screenshots, environments, audio (voice, music). Fonts
   are listed only: overlay text always uses the house text style (`capcut-assembly.md` §3).
6. Write the registry (§3). Ask **one** consolidated question only when a consequential ambiguity
   cannot be resolved by looking. Otherwise continue without asking.

