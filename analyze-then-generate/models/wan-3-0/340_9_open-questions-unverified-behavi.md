## 9. Open questions / unverified behaviour
- Exact 720p 9:16 pixel dimensions for Wan 3.0 (no official table). Data point [VERIFIED 2026-09-30, account
  history]: a `wan3_0_prime` job at 9:16 / 480p delivered **480×854 at 30 fps**, although its stored params said
  768×1344. That supports 720×1280 at 720p; measure the first output anyway. The behaviour of `aspect_ratio:"9:16"`
  with a non-9:16 start frame or edit source is still unverified.
- Whether Higgsfield routes edit/extension intents, and whether a text-removal edit reconstructs the scene cleanly
  (not documented upstream either).
- What `enable_thinking` does server-side and whether it changes cost.
- Whether Higgsfield leaves upstream `prompt_extend` on and `watermark` off.
- Whether `medias` order is preserved into Image N / Video N / Audio N numbering.
- How Higgsfield bills video references (upstream bills input + output seconds).
- Per-shot length guidance conflicts (2–5 s vs 4–6 s); inconsistent "forward/backward" extension wording.
- Quality parity of Prime vs standard beyond "aligned capabilities"; API page "preview" vs GA blog.
- Size levers (§5 model limit): the size-and-place guide is proven (§4.0 items 13–14; 8 takes). Still untested: (a) a
  frames-only build, the source's first frame with the product composited at the reckoned height as `start_image`
  (§2.5 gotcha 9), which pins size and may cost motion and sync; (c) asking for 0.6× the reckoned size to cancel a
  ~1.5× bias; (e) pinning the depth with a scene landmark and a same-depth neighbour (V04 a4 reached about 0.086 of
  the frame height against 0.083 planned but lost the can at 2.8–3.4 s). Open: whether a guide's shrink is a stable
  ~20 % of the nearest-plane size (CE-081), and whether a guide on open wood can make a small closed carton lie flat
  on Seedance edits (CE-087, CE-094: no).
- Re-measured 2026-10-10 on the frames still on disk: the Celsius cans stood nearer the lens than planned and than
  the person and were measured against a head at the assumed same depth; the readings are unsettled between about
  1× and 1.4×. So the §5 row stands for small flat packs against a same-plane neighbour (CE-009, CE-011) and is
  unproven for cans without a guide; a product found nearer the lens than planned is a depth miss, a different
  failure from oversize (CE-014, CE-015).
