## 9. Examples: the user's own videos → the house approach

The optional examples folder holds the user's own finished, AI-edited videos: how **they** place, use,
continue and blend their products. Study them to learn that approach, never to copy their content.
They are prepared like references (`10-media/<E>/`, command A1) and are never generation inputs.

### 9.1 What to read in each example
- **Product integration:**
  - the form (swap / contents / placement) and the anchor (hand, surface, environment, where a
    large product stands, a screen), and which hand;
  - the size in frame, the label or badge angle, and how long it is visible;
  - how often it is used, and on which beat (hook, middle, payoff, ending);
  - whether it ever gets a hero moment.
- **Continuation:** how multi-clip videos are joined (hard cuts on beats, continuous seams), the clip
  lengths, and how the product's state and position carry across the joins.
- **Blend:** light and grade match, realism level, camera style and movement, and how the product
  sits in the scene's light.
- **Characters:** who appears, how many people, and how faces and outfits stay consistent.
- **Text:** roles, wording style, positions, timing and density. Font, size and preset are fixed by
  the house text style (command item 6) and are not learned.
- **Structure and pacing:** length, hook type and timing, beats, inserts or memes, endings or calls to
  action.
- **Sound:** speech, music bed, sound effects and their levels.
- **What they avoid:** anything the examples consistently leave out.
- **Flaws:** physics cheats, leftovers or glitches. Note them so they are never copied.

### 9.2 Example card — `20-analysis/examples/<E>.md`
```
# <E> — <file name> (<duration> s) [E]
Product(s) shown: <which, as seen> [E]
Integration: <form; anchor; hand; size in frame; label/badge angle; visible ~<x> % of the runtime; used: <how, when>; hero moment: <no | when>> [E/I]
Continuation: <single take | clips joined at <t>, seam type; state carried: …> [E/I]
Blend: <light and grade match; realism; camera> [E/I]
Characters: <…> [E]
Text: <roles, positions, timing, density> [E]
Structure: <length; hook at t=…; beats; inserts; ending / call to action> [E/I]
Sound: <speech / bed / SFX, levels> [E/I]
Avoids: <…> [I]
Flaws not to copy: <… | none seen> [E]
```

### 9.3 The house approach — `20-analysis/house-approach.md`
The main session writes it from all the example cards:
- **One rule per line,** each with its evidence and the default it replaces. Example: "The product is
  held in the right hand at chest height, label toward the camera, visible ~70 % of the runtime (5 of
  6 examples) → replaces the 'noticed, not featured' prominence (`generation-system.md` §4b.2)."
- **Consistent** rules (most examples agree) are followed. Rules that vary are listed as options only,
  and a single example is a weak signal.
- It never holds a rule that breaks the hard rules (command item 18): physical and logical
  correctness, the §9b list, the permission rule and the house text style.
- No examples, or an empty folder → no file; the defaults apply.
