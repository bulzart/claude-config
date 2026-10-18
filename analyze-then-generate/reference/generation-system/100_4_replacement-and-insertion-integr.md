## 4. Replacement and insertion integration analysis

For every product placement, product swap, character swap, object insertion, interface replacement or
other entity substitution, fill this block (only the rows that matter for the shot, but consider all
of them):

| factor | source entity (what it was) [E] | client entity (what it is) [A] | resolved staging [G] |
|---|---|---|---|
| real size and scale | | | |
| proportions, silhouette, curves, geometry | | | **never inherited from the source entity** |
| orientation, perspective, depth, camera distance and angle | | | |
| location in frame; relation to character and surrounding objects | | | |
| supporting surface; contact points | | | |
| hand placement, grip, finger wrap, occlusion | | | adapt the grip to the client's real geometry |
| motion path, apparent weight, gravity, inertia | | | |
| materials (gloss, matte, transparent, metal, fabric) | | | |
| reflections, highlights, shadows (softness, direction) | | | |
| light direction, intensity, colour temperature, exposure, colour spill | | | inherit the scene's light |
| why it is here; how it arrived; where it was before; where it goes next | | | |
| what the character does with it; its state at each ledger checkpoint | | | |

Resolution rules:
- **Geometry follows the client's real asset.** If the source's grip, placement or container does
  not fit it (a different size, shape or opening), change the staging (grip, surface, framing,
  camera distance), never the asset.
- **Lighting is continuous.** The asset takes the scene's key direction, colour temperature and
  shadow softness in every shot and follows the light as the subject or camera moves. Reflective
  materials reflect the actual environment.
- **Context is logical.** The entity's presence, entrance and use must make sense in that
  environment. If the analogy is weak (e.g. the client's service replacing a physical prop), choose
  the most natural analogous staging (a screen, a document, a gesture) instead of forcing a literal
  swap.
- **One frame is never optimised at the expense of the timeline.** Check the whole ledger.
- **A swap is written as a replacement, anchored by its neighbours.** "Replace only <the source object> with
  <the product> at that exact spot, on the same footprint; the <source object> does not remain anywhere", with
  "exactly one <category> container in each shot". Written as the product "standing at the old spot" plus a
  negative, the old object stayed and a second, oversize product appeared (CE-048: an iced cup stayed beside
  the new can). The spot is named by the neighbours that occlude or border the source object in the source
  frame (behind the glasses case, against the wall), because "the cup's spot" alone is snapped to the nearest
  open desk (CE-071). A source object that a guardrail names is removed in the same grammar with a named
  replacement ("replace only the red can between the third bottle and the glass jar with a small pot; it does
  not remain"); "the shelf holds X" plus a negative did not remove it (CE-071: the removal worked on the retry,
  but that take shipped with the can at the wrong spot, so the sentence is observed, not verified).

For a natural placement (§4b), the "source entity" column holds the **anchor** instead: the hand
or surface it sits on [E], the light on that spot [E], and what surrounds it [E].

