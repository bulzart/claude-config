# Analyze Mode — analysis protocol

This file covers how to turn a folder of references into:
- a project profile;
- per-video cards;
- dynamic content families;
- the content directions offered to the user;
- when the user supplies examples of their own videos, their house approach (§9).

The command, and any analysis agent, follows it exactly.

In **Viral-Browser** (no client, no assets, nothing generated) §0–§2, §4 and §7 apply as written; the card, the
synthesis and the analysis-agent prompt are `viral-browser.md` §3, §4 and §13.1.

## 0. Provenance labels (use everywhere)
- **[E]** direct evidence (a frame, a transcript line, OCR, a measured number, document text)
- **[I]** analytical inference
- **[U]** user instruction
- **[A]** client asset
- **[M]** model knowledge
- **[G]** generation instruction

Never present an inference as evidence. Measurements come from the tool output (cuts, timings,
loudness); opinions come from viewing.

## 1. Inputs per video (produced by `atg.py prep-all`)

| file | what it gives |
|---|---|
| `10-media/<V>/video.md` | Specs, sampling summary, shot table, transcript, OCR spans, sheet list |
| `10-media/<V>/timeline.md` | One row per second: shot, cuts, motion peaks, static stretches, words spoken, loudness, on-screen text |
| `10-media/<V>/sheets/storyboard-NN.jpg` | The video at **~5 frames per second**, in order. White labels are the baseline; cyan `+` labels are densified frames (cut boundaries, motion peaks, first second); a red bar marks the first frame after a cut; grey cells mark thinned static stretches (≥ 1 fps kept) |
| `frames.json`, `cuts.json`, `activity.json`, `audio.json`, `transcript.json`, `ocr.json` | Machine data for exact look-ups |
| `20-analysis/audio-context.md` (and `.json`, from `T audio-context --profile`) | The audio of every reference in one file: each transcript with its times, the language and its confidence, the speech and sound facts, repeated phrases that may be lyrics, and flags for a video whose transcript is missing, failed or doubtful. Read it before writing any card |

**Densify on demand** where the default rate is not enough: fast actions, object interactions, hand
contact, gestures, product appearances, swaps, text appearances, transitions.
```
python atg.py frames "<video>" --out "<run>/10-media/<V>/detail" --range 3.2-4.4 --fps 15 --sheet --label grip
```
Read a single full-resolution frame (`--at 3.6 --max-side 1280`) for small details (labels, UI, hands).

## 2. Reading a video as one continuous sequence

Read the storyboard sheets **in order with `timeline.md` open beside them**: every row of the timeline
is one second of the sheets. Do not describe isolated frames. Answer:

1. **Sequence:** what happens from the first frame to the last, and how earlier actions set up later
   ones (cause → effect).
2. **Subject:** who or what the video is about; which entities matter and what each represents
   (person, character, product, service, interface, topic, brand, place, prop).
3. **Message:** what is communicated and how the viewer is addressed (direct to camera, voice-over,
   POV, silent demonstration, text-led, dialogue between characters).
4. **Speech and sound (the audio context, in every mode):** read `20-analysis/audio-context.md` and the
   video's transcript right through, not only its first line.
   - What is said, checked against the lips, the picture and the on-screen text (the machine mishears, so a
     doubtful line is marked), in the language it is said in and translated into the card.
   - Who says it: on camera, a voice-over, sung, a text-to-speech voice, nobody.
   - The hook line, the story or the steps, the claims, numbers, prices and names spoken aloud, and the calls to action.
   - The delivery (pace, tone, emotion) and where the words land relative to the visual beats.
   - What the sound adds that the picture does not: credibility, instruction, humour, identity, rhythm, a
     trending song named by its lyrics or tempo.
   - A video with no speech is a finding too (a silent-friendly demonstration, a song under a visual).
   - **In Recreate this is context only:** the reference that goes to Higgsfield is the silent copy, and the
     original audio is restored afterwards (the audio is analysed, never uploaded).
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
Audio context: language <code (confidence)> · voice <on-camera | voice-over | sung | text-to-speech | none> · transcript <ok | doubtful: why | unavailable: why> (T audio-context) [E]
Said: <what is said, in one to three sentences (translated into English when it is not); the hook line verbatim with its time and, beside it, its translation; the story or steps, the claims, numbers, prices, product and brand names and calls to action spoken aloud; or "no speech"> [E]
Words and sound together: <what the words and the sound add that the picture does not: credibility, instruction, humour, emotion, identity, rhythm; the song or the trending sound, named when the lyrics, the tempo or a known format identify it> [I]
Audio & address: <speech / VO / music / SFX; how the viewer is addressed>                 [E/I]
Overlay text: <per event: wording, role (hook / "POV:" line / running caption / label / meme line / none), centre x_rel,y_rel, in–out s, style (colour, size, outline/box, case, line breaks)> — re-placed in CapCut over the clean video; wording kept only for a generic meme line (text-and-format.md §1) [E/I]
Inserts: <per insert: t_in–t_out (cut frames), what it is (name the meme if recognisable), video or still, its sound, the reference's own overlays on it> — cut from this video, never generated (generation-system.md §3c) [E]
Sound design (every mode; audio-profile.json from `T audio-context --profile`; Create builds its sound layer from it): <music bed yes/no/unknown, ~BPM, beat strength, energy arc, hits (t, on cut?), speech share, reusable whole?> → role [I]: <dramatic / comic / suspense / hype / SFX-driven / voice-only>; lyrics in the transcript may identify the song [E/I]
Engagement mechanisms: <mechanism — evidence (t=…) — why it works>                         [I]
Trend & cognition: <format name + caption grammar; structural mechanism; surface elements (current / fading / dated); emotion arc hook→middle→payoff; laugh mechanism; share line> (creative-direction.md §3–§4) [E/I]
Transferable craft (how, as kinds not instances): <style: look, grade, lens, light, performance register | properties: length, pacing curve, cut rhythm, caption grammar, sound role, camera behaviour | approach: hook type, structure shape, reveal logic, payoff timing, laugh mechanism, loop | crafting: one take or cuts, POV or observed, where text sits, when and how the product reads | why it works> — what a Create video may take; everything under "Subject & entities" and the beat map is what it may not (creative-direction.md §5.0) [I]
Interactions & physics: <grips, pours, handling, weight; per handled object: the part used, the preparation step, the contact point, the hand, the head angle; counts of multiples over time — anything a generation must reproduce (anomaly-catalog.md §2)> [E]
Continuity & flaws: <source errors and dead space not to copy>                             [E/I]
Entities → preserve / replace / adapt / ignore: <per entity, with reason>                  [I/U]
Client-entity fit: <swap: <source entity> at t=… → client <entity> | contents: <vessel or form> holds the product, package nearby | placement: nothing analogous> [E/I]
Placement opportunities (contents / placement): <hands free/busy per beat; surfaces near the subject + side + depth plane + shots that show them; where a large product would stand; light on each spot; the large rigid same-plane objects the source shows (a laptop, a monitor) as size neighbours; best anchor> [E/I]
Must not survive (generation-system.md §9b): <the copyright and ownership floor only: the person being replaced, the product being swapped, competitor products, overlay text, usernames, platform logos and watermarks, featured third-party branding, a copyrighted character as the subject; plus anything the generation service refuses>; incidental decor, clothing logos, meme faces and all brand-dependent content (alcohol, weapons, gore, profanity, …) are fine and are not listed; brand-dependent content appears only in the guardrail audit when a client rule names it [E]
Guardrail audit (brand-guardrails.md §3): <none supplied | per hit: G<n> · t=… · element · subject/featured/peripheral · picture/caption/speech/insert/reflection · core/peripheral (why) · operation> → verdict: pick-clean | pick-and-edit: <operations> | dismiss: <rule, why core> [E/I]
Confidence: <high/medium/low> — <what was hard to see or hear>
```

**Create cards are also viral cards.** Besides the fields above, a Create card carries the viral layer of `viral-browser.md` §3.2, so that each reference is read once: the product layer kept apart from the mechanism layer; the ranked drivers of spread and whether it is attention-only or commerce-proven; the one-sentence product-agnostic mechanism, its dependence on its own product and its transplant needs; the audience (who, the awareness stage, the pain or desire) and the mentality (the mental shortcuts it uses, the emotion at the hook, the middle and the payoff, what got them hooked); the engagement mechanics; commerce signals when a metrics file is supplied; and the one-line `Facts:` JSON (its `category` is optional in Create). The product layer is recorded and then discarded for ideation (`viral-browser.md` §14.1).

**The audio context in each mode.** Every card, in Recreate, Create and Viral-Browser, carries the three lines `Audio context:`, `Said:` and `Words and sound together:` (a baseline's light card, the first one), written from `20-analysis/audio-context.md` and the transcript; `T audio-context --check --cards` refuses while one is missing or empty. **Recreate:** context only, so that the plan knows what is said and which beats the restored original audio must still fit; only the silent copy is ever uploaded. **Create:** the craft of the speech may be borrowed (the hook type, the delivery, the way the viewer is addressed), never the lines, the claims or the subject. **Viral-Browser:** the words are evidence of the hook, the promise, the audience and the mentality (`viral-browser.md` §4.3, §4.5).

## 4. Effectiveness lenses (apply those the material supports; add new ones when needed)

| lens | guiding question |
|---|---|
| Hook / first second | What stops the scroll at 0.0–1.0 s (motion onset, face, question, conflict, oddity, text line, sound)? |
| Curiosity | What question opens, and when does it close? |
| Relatability / POV | Does the viewer see themselves (POV, everyday problem, shared frustration)? |
| Humour / surprise | Where is the turn, and how is it timed? |
| Demonstration / proof | What is shown working, and how legibly? |
| Storytelling | Setup → escalation → payoff structure; stakes |
| Educational value | What is learned, and how fast? |
| Spectacle / satisfaction | Visual pleasure, ASMR-like processes, transformations |
| Transformation | A before/after state change, and its visibility |
| Visual interruption | Pattern breaks, sudden cuts, zooms, object entries — and whether they are motivated |
| Rhythm and pacing | Shot length distribution, beat alignment with speech or music, information density per second |
| Camera behaviour | Proximity, POV vs. observer, motion energy, stability |
| Composition | Subject placement in 9:16, readability, UI-safe areas |
| Viewer interaction | Direct address, questions, calls to comment or share, challenges |
| Emotional response | The intended feeling at the hook, the middle and the payoff |
| Loopability / retention | Seamless loop, end-state echo, payoff near the end, retention risks (dead space, slow middle) |
| Comment / share potential | Controversy, identity, utility, "send this to…" |
| Audience targeting | Who it speaks to, and the cues that reveal it |
| Cognitive ease | Is the situation one the audience has lived, understood in a fraction of a second? |
| Trend element | Which format, meme, sound or caption grammar it uses; structural or surface; current, fading or dated |
| Share trigger | What a viewer would say by sending it ("this is you", "this is us") |
| Product memory | At which moments of attention a product could be seen and remembered without being featured |
| Structure | The reusable template of beats |

## 5. Cross-video synthesis

1. **Compare cards** and list the recurring mechanisms, with the videos that show each.
2. **Cluster dynamically** into content families by *execution style × what the video is doing or
   communicating*. Never use a fixed taxonomy; name each family from the material (e.g. "locked-off
   tabletop reveal with dry humour", "creator-to-camera myth-busting with cutaways").
3. **Profile each family** from measured data:

| family | members | typical length | median shot | first cut | speech onset | hook mechanism | payoff time | camera style | editing logic | text role | audio (language, voice type, sound role) | structure template |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

3b. **Craft sheet** (Create): write `20-analysis/craft-sheet.md`, one block per family (and per
   reference whose craft stands out), with two columns from the cards: **collected** (the
   transferable craft: style, properties, approach, crafting, why it works) and **left behind**
   (the subject: premise, setting, characters, action sequence, joke content, lines, caption
   wording, props, first frame, ending image, the source product's beat, the sound). Create
   ideation reads only the first column for the how and invents the what
   (`creative-direction.md` §5.0). Tag each block with the mechanism ids M# it carries (step 3c).
3c. **Virality synthesis** (Create; `viral-browser.md` §14): `T viral-stats --run RUN --no-niche` (the measured profile in `20-analysis/corpus-profile.md`); `20-analysis/mechanism-map.md` (mechanisms M#, k of n, driver, strength, independence of the product, transplant needs, confounds, graded hypotheses); the hook, length and pacing ranges; the engagement style; the audience and mentality model with the mass-thinking patterns the material uses; `20-analysis/viral-essence.md`; and the trend read with the Create trend pass.
3d. **Blend matrix** (Create): `20-analysis/blend-matrix.md`, the mined mechanisms that pass the driver test, set against the product's truths and affordances (`viral-browser.md` §14.3). Ideation reads it with the craft sheet and the insight sheet.
4. **Directions** are meaningful combinations of subject × structure × execution style that fit the
   client.
   - **Create** presents them as numbered **style groups**, `<content type> × <style> × <subject>`
     grouped by content type (e.g. "G1 Organic × POV skit × gym", "G3 Anime × reaction ×
     school"). The user picks one or a mix. The `<subject>` of a group is a *field* for new
     situations (a gym, an office, a school), never a reference's own scene; the group carries the
     craft it borrows (from one family, or from several in a hybrid), and each video in it gets its own
     subject and its own blend with the product (`creative-direction.md` §5.0, §5.0b). The
     groups are **suggestions, not a menu**: the agents also propose **hybrid groups** that blend
     mechanisms from several families with the product's own strengths (the insight sheet,
     `assets-and-substitution.md` §2 step 3b), and a concept need not belong to any group of the
     references (`creative-direction.md` §5.0b).
   - **Recreate** also ranks every analysed reference by **recreate fit**, after the **guardrail
     audit** has filtered it (`brand-guardrails.md` §4: a dismissed reference is listed under the
     ranking with its rule; a pick-and-edit reference carries its operations into the edit load):
     - the product's integration form (swap / contents / placement);
     - the scene fit of each supplied brand (CE-020: a grill reference went to the focus brand because the table had a free surface): a food, grill, party or sport scene suits a drink; a
       desk, class, meeting, work or commute scene suits a focus product; a reference with no tie for one
       brand ranks for the other (command A7);
     - for a placement, the anchor class the locked model renders at size: where its guide lists size as
       a model limit (`wan3_0_prime`, `wan-3-0.md` §5), an in-hand, swap or large same-plane-neighbour
       anchor ranks above a surface anchor that only paper, a notebook or a head can size;
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

## 6. Project inference — `20-analysis/project-profile.md`

Everything is inferred from the folder, never assumed:
- **Domain and objective:** what kind of project this is (physical product, digital product, app,
  service, personality or character, education, finance, entertainment, memes, brand, other) and the
  likely content goal. Label [E] with the evidence files, or [I].
- **Brand guardrails [E]:** the client's rules from the supplied documents, extracted to
  `30-assets/guardrails.md` with the competitor, people, limit, wording and presentation lists they
  imply (`brand-guardrails.md` §1). They drive the guardrail audit of every reference (§2.13).
- **Authoritative requirements [E]:** quote every instruction found in documents, scripts, briefs,
  PDFs and spreadsheets, with the file id. These override inferences. Conflicts between documents go
  to the user.
- **Caught errors that apply [E]:** the ids from `20-analysis/caught-errors.md` (command A1,
  item 22) relevant to this project's product family, mode and model, with the step each one
  changes (ideation, plan, prompt, QC). An entry about creative quality shapes the directions and
  the concept seeds; an entry about a product family shapes its affordance sheet and ledger.
- **Entities:** the client entities (what to put in, taken **only** from the user-supplied asset
  registry), the source entities (what the references show, possibly many different products or
  executions), and the mapping options:
  - preserve (the mechanism, the action, the camera logic);
  - replace (people → approved characters; a source product → the client product; an interface →
    the client interface; a brand → the client brand; other analogous substitutions);
  - adapt (an environment matched to the client);
  - **contents / place** (no source entity of the same form: the vessel's contents become the
    product with its package beside it, or the product is placed naturally in the scene,
    `generation-system.md` §4b). List which references are swap, contents and placement;
  - ignore (irrelevant extras).
- **Asset fit:** map the entity roles each direction needs onto the **user-supplied** asset registry
  (`assets-and-substitution.md` §2–§3), and flag roles no supplied asset can fill. Never look for
  client assets in the references folder: products, people or brands seen there belong to the
  references.
- **Audience and platform cues** [I].
- **Goal** [E/I], **audience model** [I] and **trend read** [E/I] (`creative-direction.md` §2–§4):
  the goal in one line and each video's job; who the references speak to and what they recognise
  instantly; the format names, the structural mechanisms, the surface elements with their
  freshness, and any bounded trend check with its date. In Create the audience model also has a product half
  (who the client's product is for and where they live, from the insight sheet and the documents) beside this
  corpus half (`creative-direction.md` §3).

## 7. Scale and delegation (≤ 2 analysis agents, no Workflow)

- **≤ 6 videos** (or ≤ ~3 min total): the main session analyses everything itself.
- **More:** spawn **1** analysis agent, or **2** when there are over ~15 videos, each with a
  **disjoint** list of video ids. Two analysis agents is the ceiling; production agents (one per
  video, `production-agents.md`) come later and are separate.
- Agents only read this protocol plus their videos' prepared files, write the cards, and never ask
  questions.
- The main session always writes the synthesis (§5–§6) itself.

Agent prompt (fill in the placeholders; use the Agent tool with `subagent_type: general-purpose`):

```
You analyse reference videos for a /analyze-then-generate run. Follow
C:/Users/Glaresquare1/.claude/analyze-then-generate/reference/analysis-protocol.md §0–§4 exactly.
Run dir: <RUN>. Your videos: <V01, V04, …> (prepared under <RUN>/10-media/<V>/).
For each video: read video.md and timeline.md, view every storyboard sheet in order, densify with
`python <ATG>/scripts/atg.py frames …` where §1 says so, then write <RUN>/20-analysis/cards/<V>.md
using the §3 template with provenance labels. Project context so far: <2–4 lines>.
Client's placeable entities (for the "Client-entity fit" line only): <type, category, real size —
e.g. "slim 355 ml aluminium drink can", "palm-sized pack of 10 gum pellets", "compact five-door
hatchback, about 4 m long">.
Your examples (if any): <E01, …> (prepared under <RUN>/10-media/<E>/): the user's own finished
videos. For each, write <RUN>/20-analysis/examples/<E>.md with the §9.2 template (§9.1 says what to read).
Rules: do not call Higgsfield tools, do not spawn agents, do not use the Workflow tool, do not ask
questions, write only your card files. Every product, person or brand you see in these videos
belongs to the references; client assets come only from the user's supplied asset registry, which you
do not need. Final message: one line per video (format label, hook, mechanism,
swap/contents/placement, inserts, overlay text yes/no, confidence).
```

## 8. Presenting results to the user

Keep the chat summary short:
- project profile (5 lines);
- families table;
- numbered directions.

The full files stay in `20-analysis/`. Ask for the number of videos, then the directions (§ command
flow).

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
