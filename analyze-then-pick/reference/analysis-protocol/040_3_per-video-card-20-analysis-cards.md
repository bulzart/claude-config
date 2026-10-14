## 3. Per-video card — `20-analysis/cards/<V>.md`

```
# <V> — <file name> (<duration> s, <aspect>, <fps>) [E]
Format (dynamic label): <e.g. "POV hands-only demo with text hook" — invent the label from the material>
Subject & entities: <entity — what it represents — screen time — role>              [E/I]
Beat map:
| t | beat | what happens | camera | audio/speech | text role |                        [E]
Hook (0–1 s, 0–3 s): <visual, audio, text role, curiosity gap>                          [E/I]
Payoff: <what, at t=…>; loop: <yes/no, why>; depends on its own object's geometry? <e.g. its logo lands between two caption words → the new video gives that landing a visible cause and the text follows the product (generation-system.md §5b)> [E/I]
Camera & editing: <shot sizes, moves, median shot …s, cut logic, transitions + motivation> [E/I]
Audio & address: <speech / VO / music / SFX; how the viewer is addressed>                 [E/I]
Overlay text: <per event: wording, role (hook / "POV:" line / running caption / label / meme line / none), centre x_rel,y_rel, in–out s, style (colour, size, outline/box, case, line breaks)> — re-placed in CapCut over the clean video; wording kept only for a generic meme line (text-and-format.md §1) [E/I]
Inserts: <per insert: t_in–t_out (cut frames), what it is (name the meme if recognisable), video or still, its sound, the reference's own overlays on it> — cut from this video, never generated (generation-system.md §3c) [E]
Sound design (Create; audio-profile.json): <music bed yes/no/unknown, ~BPM, beat strength, energy arc, hits (t, on cut?), speech share, reusable whole?> → role [I]: <dramatic / comic / suspense / hype / SFX-driven / voice-only>; lyrics in the transcript may identify the song [E/I]
Engagement mechanisms: <mechanism — evidence (t=…) — why it works>                         [I]
Trend & cognition: <format name + caption grammar; structural mechanism; surface elements (current / fading / dated); emotion arc hook→middle→payoff; laugh mechanism; share line> (creative-direction.md §3–§4) [E/I]
Transferable craft (how, as kinds not instances): <style: look, grade, lens, light, performance register | properties: length, pacing curve, cut rhythm, caption grammar, sound role, camera behaviour | approach: hook type, structure shape, reveal logic, payoff timing, laugh mechanism, loop | crafting: one take or cuts, POV or observed, where text sits, when and how the product reads | why it works> — what a Create video may take; everything under "Subject & entities" and the beat map is what it may not (creative-direction.md §5.0) [I]
Interactions & physics: <grips, pours, handling, weight; per handled object: the part used, the preparation step, the contact point, the hand, the head angle; counts of multiples over time — anything a generation must reproduce (anomaly-catalog.md §2)> [E]
Continuity & flaws: <source errors and dead space not to copy>                             [E/I]
Entities → preserve / replace / adapt / ignore: <per entity, with reason>                  [I/U]
Client-entity fit: <swap: <source entity> at t=… → client <entity> | contents: <vessel or form> holds the product, package nearby | placement: nothing analogous> [E/I]
Placement opportunities (contents / placement): <hands free/busy per beat and each hand's lane over the whole clip (resting, writing, page-turning, pick-up sweeps); surfaces near the subject + side + depth plane + shots that show them; the region that is bare and in frame at 0, 1, 2.5, 4 and 6 s (an orbit or a sweep especially); strip widths against the pack; where a large product would stand; light on each spot; the large rigid same-plane objects the source shows (a laptop, a monitor) as size neighbours; best anchor, checked against generation-system.md §4b.1c> [E/I]
Source preparation flags (generation-system.md §5c.2b): <mirrored: a front-camera selfie shown un-flipped (reversed print or signs, a left-handed instrument), with the evidence frame | burned-in text on a flat surface | a real person's name, or a patch or logo on the kept garment, with the shots where it is legible | a face effect baked in (mask, filter, clone) | cut structure: n hard cuts, alternation of person and person-free shots | camera path: locked, handheld, orbit | none> [E]
Must not survive (generation-system.md §9b): <the copyright and ownership floor only: the person being replaced, the product being swapped, competitor products, overlay text, usernames, platform logos and watermarks, featured third-party branding, a copyrighted character as the subject; plus anything the generation service refuses>; incidental decor, clothing logos, meme faces and all brand-dependent content (alcohol, weapons, gore, profanity, …) are fine and are not listed; brand-dependent content appears only in the guardrail audit when a client rule names it [E]
Guardrail audit (brand-guardrails.md §3): <none supplied | per hit: G<n> · t=… · element · subject/featured/peripheral · picture/caption/speech/insert/reflection · core/peripheral (why) · operation> → verdict: pick-clean | pick-and-edit: <operations> | dismiss: <rule, why core> [E/I]
Confidence: <high/medium/low> — <what was hard to see or hear>
```

