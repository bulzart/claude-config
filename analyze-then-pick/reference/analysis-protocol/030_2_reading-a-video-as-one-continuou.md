## 2. Reading a video as one continuous sequence

Read the storyboard sheets **in order with `timeline.md` open beside them**: every row of the timeline
is one second of the sheets. Do not describe isolated frames. Answer:

1. **Sequence:** what happens from the first frame to the last, and how earlier actions set up later
   ones (cause → effect).
2. **Subject:** who or what the video is about; which entities matter and what each represents
   (person, character, product, service, interface, topic, brand, place, prop).
3. **Message:** what is communicated and how the viewer is addressed (direct to camera, voice-over,
   POV, silent demonstration, text-led, dialogue between characters).
4. **Speech:** what is said (transcript, verified against the lips and timing), the delivery (pace,
   tone), and where the words land relative to the visual beats.
5. **Evolution:** scene changes, state changes of objects, reveals, transformations.
6. **Camera and edit:** shot sizes, movement, handheld or locked-off, cut rhythm (median shot length
   from `video.md`), why each cut happens, transitions and their motivation, speed changes.
7. **Payoff:** what it is and when it lands (seconds), and whether the ending loops back to the start
   (`loop_similarity`, plus the first and last frames).
8. **Continuity:** entity states over time (the start of an entity ledger); the count of every
   multiple over time; for every handled object, how it is used (the part: spout, opened top,
   nozzle, torn end; the preparation step; the contact point; the hand; the head angle), because a
   Recreate keeps it and a Create reuses the mechanism (`generation-system.md` §5d,
   `anomaly-catalog.md` §2); any source flaws (continuity errors, dead space, a count or
   affordance break of the source's own) that must **not** be copied.
9. **Client-entity fit:** what is the most suitable way for the client's placeable entity (the
   registry, command A2b) to be part of this video, given what it is, its size and how it is used
   (`generation-system.md` §4b.0)?
   - **Swap:** the video shows its analog in the same form (another can for a can, another gum
     pack for a gum, another car for a car), so it is replaced.
   - **Contents:** the video shows the product's category in another form or vessel, whatever its
     role in the story (a glass of water on the subject's café table, a drink in a cup that gets
     poisoned and drunk, gum pellets shaken into a palm).
     - What is inside becomes the client's product, and its opened package is placed nearby.
     - Note the vessel or form, the amount over time, where the package could stand, and anything
       that would make the switch illogical (the joke is about that exact drink, a hot drink for a
       cold product, a background stranger's glass).
   - **Placement:** nothing analogous. Examples: a funny story with nothing to drink or chew in
     it, a man crossing a street with free hands, a sidewalk interview with no car in shot. Record
     the placement opportunities:
     - when the hands are free or busy, per beat (handheld products);
     - the surfaces near the subject, and which shots show them;
     - where a large product would naturally stand (the curb, a driveway, a corner of the room);
     - the light falling on those spots.
   - A source object that is **not** analogous (a phone for a drink client, a bicycle for a car
     client) stays a reference element. It is never forced into a swap.
10. **Inserts:** footage that interrupts the reference's own scene, such as a meme clip, a film or
    TV snippet, or a reaction image, usually with its own sound. For each one record:
    - the exact in and out on the cut frames (`cuts.json`);
    - what it is;
    - whether it is video or a still;
    - its sound;
    - any overlays the reference added on top of it.
    Inserts are cut from the reference later, never generated (`generation-system.md` §3c).
11. **Overlay text:** every text event's wording, role, centre position (`x_rel`, `y_rel` from
    `ocr.json` and the sheets), in and out times, and style. The new video is generated clean, and
    the text is re-placed as CapCut layers (`text-and-format.md` §3).
12. **Trend elements and cognitive triggers** (`creative-direction.md` §3–§4): the format's name
    and caption grammar; the structural mechanism that would outlive the trend; the surface
    elements (a meme, a sound, a catchphrase, an effect) with their freshness; the emotion arc at
    the hook, the middle and the payoff; the laugh mechanism (incongruity, escalation, callback,
    timing, deadpan, reversal); the share line a viewer would type when sending it.
13. **Guardrail audit** (`brand-guardrails.md` §3), when `30-assets/guardrails.md` exists: every
    hit against the client's rules with its time, element, prominence and place (picture, caption,
    speech, insert, reflection); core or peripheral by the meaning test (would a viewer who never
    saw the source describe the edited video the same way, and does the sync hold?); the verdict
    (pick-clean, pick-and-edit with the operations, dismiss with the rule).

