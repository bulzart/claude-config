## 5. Logic, continuity and anti-slop gate

Evaluate before writing the prompt, and again in the pre-generation QC pass (§8):

| dimension | pass condition |
|---|---|
| physical | Plausible mass, gravity, contact, grip, liquids and material behaviour. No floating, unsupported or intersecting objects. No fingers through objects, no malformed hands |
| spatial | A stable layout, with consistent left/right, near/far and supporting surfaces |
| temporal | Cause precedes effect; every state change has a visible cause; no reversals |
| narrative | Every beat serves the intent (§2.1); the payoff pays off the hook |
| environmental | The background, props and weather stay consistent; no morphing |
| asset fidelity | Canonical geometry, identity, materials and label/interface fidelity (label text only when real and approved) |
| camera continuity | Moves are motivated; axis respected; framing keeps the important interaction readable |
| lighting continuity | Direction, colour and exposure are stable unless a visible cause changes them; reflections and shadows agree |
| motion continuity | Natural speed; no arbitrary slow motion, sudden speed-ups or jump-speed changes |
| interaction realism | Believable body mechanics, weight shifts and follow-through |
| composition | The subject and asset are readable in 9:16; key action kept out of platform UI zones |
| pacing | Matches the family profile; no dead space, filler or unexplained pauses; no repeated actions |
| transitions | Every cut, zoom, reframe, speed ramp or scene change has a reason (the action, the family's editing style, the narrative). None are added "for cinematic feel" |
| identity | No drift in face, hair, body or wardrobe; no duplicated people or objects |
| placement (§4b) | The placed client entity is present and recognisable, on one anchor that persists through every shot. It moves only by a visible action, matches the plate, and is noticed but not featured |
| counts | Every multiple keeps its number except through a visible cause; nothing appears, vanishes or doubles across exits, occlusions and cuts (`anomaly-catalog.md` §2.1, §2.5) |
| affordance | Every use goes through the object's real opening or control, after its preparation step, with a real contact point and the body mechanics of that use (§2.2, §2.3, §2.8) |
| solidity | Nothing passes through, sinks into or shows through a solid; occlusion follows depth; every contact has its consequence (§2.14) |
| sharpness | One clear idea, a hook in the first second, a real turn, a payoff on the family's beat, a share line, and the product native to the scene (`creative-direction.md` §6) |
| size | Every product's size in every shot is reckoned from its real dimensions, its distance, the lens and a named neighbour, written into the prompt and the start frame, and kept across motion and cuts (§2.7) |
| guardrails | Every hit of the client's rules is edited as planned (count at the limit, competitor marks removed, excluded faces swapped, captions rewritten, props removed) and nothing the rules ban is in the concept (`brand-guardrails.md`) |
| transfer (Create) | The video carries the references' craft (style, properties, approach, crafting) and none of their subject: the copy test passes against every reference of the family and the run's other videos (`creative-direction.md` §5.0) |

The AI-slop blacklist must never appear in a plan or a prompt:
- unexplained dead space, filler or pauses, and unnecessary static stretches;
- arbitrary slow motion, abrupt fast-forwarding and sudden speed changes;
- out-of-nowhere transitions, unjustified cuts and random scene changes;
- teleporting, disappearing or duplicated objects;
- a count that changes without a cause (three capsules that are one after a walk-past);
- a product used through a part that has no opening or through a closed one (a straw bottle drunk
  from the side without the spout, a sealed can sipped), or used before it was made ready;
- anything passing through the product or another solid (a tossed paper through a plastic bottle),
  sinking into a surface, showing through an opaque body, or hitting something without a
  consequence;
- a generic concept: a "person enjoys product" beat, an explained joke, a stock situation nobody
  lives in, a dated meme;
- a placed product that changes spot between shots, enters or leaves without a cause, or looks
  pasted in (its own light, a halo, mismatched sharpness, no contact shadow, a packshot pose);
- identity drift, clothing changes and asset deformation;
- inconsistent backgrounds, unexplained lighting changes and broken reflections;
- impossible physics, inconsistent scale and nonsensical motion;
- repeated actions and environmental morphing.

