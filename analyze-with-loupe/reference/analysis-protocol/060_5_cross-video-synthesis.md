## 5. Cross-video synthesis

1. **Compare cards** and list the recurring mechanisms, with the videos that show each.
2. **Cluster dynamically** into content families by *execution style × what the video is doing or
   communicating*. Never use a fixed taxonomy; name each family from the material (e.g. "locked-off
   tabletop reveal with dry humour", "creator-to-camera myth-busting with cutaways").
3. **Profile each family** from measured data:

| family | members | typical length | median shot | first cut | speech onset | hook mechanism | payoff time | camera style | editing logic | text role | audio | structure template |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

3b. **Craft sheet** (Create): write `20-analysis/craft-sheet.md`, one block per family (and per
   reference whose craft stands out), with two columns from the cards: **collected** (the
   transferable craft: style, properties, approach, crafting, why it works) and **left behind**
   (the subject: premise, setting, characters, action sequence, joke content, lines, caption
   wording, props, first frame, ending image, the source product's beat, the sound). Create
   ideation reads only the first column for the how and invents the what
   (`creative-direction.md` §5.0).
4. **Directions** are meaningful combinations of subject × structure × execution style that fit the
   client.
   - **Create** presents them as numbered **style groups**, `<content type> × <style> × <subject>`
     grouped by content type (e.g. "G1 Organic × POV skit × gym", "G3 Anime × reaction ×
     school"). The user picks one or a mix. The `<subject>` of a group is a *field* for new
     situations (a gym, an office, a school), never a reference's own scene; the group carries the
     family's craft, and each video in it gets its own subject (`creative-direction.md` §5.0).
   - **Recreate** also ranks every analysed reference by **recreate fit**, after the **guardrail
     audit** has filtered it (`brand-guardrails.md` §4: a dismissed reference is listed under the
     ranking with its rule; a pick-and-edit reference carries its operations into the edit load):
     - the product's integration form (swap / contents / placement);
     - the scene fit of each supplied brand (CE-020: a grill reference went to the focus brand because the table had a free surface): a food, grill, party or sport scene suits a drink; a
       desk, class, meeting, work or commute scene suits a focus product; a reference with no tie for one
       brand ranks for the other (command A7);
     - for a placement, the anchor class the locked model renders at size: where its guide lists size as
       a model limit (`wan3_0_prime`, `wan-3-0.md` §5), an in-hand, swap or large same-plane-neighbour
       anchor (the last only where `generation-system.md` §4b.1c holds, and with a guide) ranks above a
       surface anchor that only paper, a notebook or a head can size;
     - placement feasibility (`generation-system.md` §4b.1c): a spot that is bare at frame 0, stays in frame
       along the whole path, lies outside every hand's lane and is wider than the product. A reference with none
       (both hands cover the lower half in turn; an orbit that leaves the only free strip; a cluttered strip
       narrower than the product) ranks low for a placed product, and its plan is the swap of a source object or
       an in-hand product (CE-055, CE-061, CE-073, CE-082);
     - cut structure and source flags: a reference with many hard cuts, one that alternates a person with
       person-free close-ups, or one with a face effect baked in ranks low (`generation-system.md` §3b.1 item
       7, §5c.2b; CE-051, CE-079, CE-083, CE-086); a mirrored source ranks normally and is flipped in the
       prepared copy (CE-030);
     - the number of people against the supplied characters;
     - the own-content length after inserts, against the locked model's edit range;
     - the text and overlay load;
     - the motion complexity for the model's edit kind;
     - the strength of its mechanism;
   - its creative potential (`creative-direction.md` §5.2).
     Write the ranking to `20-analysis/recreate-ranking.md`.

   Each direction names:
   - its source family;
   - its mechanism;
   - why it will work for the goal and the audience, and the concept seeds it suggests
     (`creative-direction.md` §5);
   - what the client's entities would do;
   - **how the client's product appears:**
     - a swap of a named source entity;
     - contents ("the cup holds the product; the open can stands beside it", "the gum piece comes
       from the open pack on the table");
     - or a natural placement with its likely anchor ("in hand while walking", "on the desk beside
       the laptop", "parked at the curb behind them").
     A family whose references have nothing analogous is still a valid direction;
   - the assets it would need;
   - a typical length. When that is over 30 s, or over the locked model's maximum per generation,
     mark it "needs ≥2 generations". Such a video asks the user's permission before it is
     generated (command A7b).
   Write them to `20-analysis/directions.md`; they are what the user chooses from.

