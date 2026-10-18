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

