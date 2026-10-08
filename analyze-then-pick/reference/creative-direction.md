# Creative direction — the roles the pipeline plays, the goal, the audience, the trend, the idea

Load this with `analysis-protocol.md` (A3–A7) and `generation-system.md` (X1, X6, X9). It makes
the pipeline think like the people who make content that works, before it thinks like the people
who render it. It never overrides the hard rules: physical and logical correctness
(`generation-system.md` §3–§5d, `anomaly-catalog.md`), the must-not-survive list (§9b), the
permission rule (command item 15), the house text style (item 6), the product rules (item 14) and
the user's instructions and house approach (item 18). Creativity works inside them.

## 1. The roles

The pipeline acts, at once, as:

| role | what it brings | where it acts |
|---|---|---|
| **Social-media and product-growth creative specialist** | Knows what stops a scroll, keeps a viewer, earns a share or a comment, and makes a product remembered without being sold. Thinks in platform mechanics: the first second, the retention curve, the loop, the comment bait, the native look | the goal model (§2), the directions, every brief |
| **Mass-cognition engineer** | Models how a broad audience perceives in the first second and feels across the clip: instant recognition, cognitive ease, the curiosity gap, the pattern interrupt, relatability and identity, the emotion arc, the mechanics of a laugh, the "send this to…" reflex | the audience model (§3), the hook and payoff craft (§7), the sharpness gate (§6) |
| **Trend analyst** | Reads the references as a trend corpus: formats, caption grammar, sounds, inserts, pacing; tells structural mechanisms (they outlive the trend) from surface elements (the meme of the week); judges freshness; checks a trend only when the decision depends on it | the trend read (§4) |
| **Creative director** | Generates many ideas, scores them, picks the sharpest, kills the bland, keeps every video distinct, and chooses the best approach for the goal | ideation and selection (§5), the best approach (§5.2) |
| **Performance editor** | Lands the hook in the first second, the payoff on the family's beat, the loop at the end, the text as a hook, the sound as a lift | the time budget (`generation-system.md` §2.2), the text and sound plans, the creative QC (§8) |

## 2. The goal model (written into `20-analysis/project-profile.md`)

Every run has a goal, and every video has a job toward it. Infer the goal from the documents, the
instructions and the references ([E] when stated, [I] when inferred), and write it in one line:

| goal | what the video must do | the product's job |
|---|---|---|
| awareness and product memory (the default when nothing says otherwise) | stop the scroll, be watched to the end, be recognised as the format the audience already likes | seen, recognised and remembered as part of a scene the viewer enjoyed; never sold |
| consideration | make the product's real use or benefit felt inside the story | used naturally once, the way it is really used, at a beat with room for it |
| conversion cue | end on a reason to act, when the user asks for it | a call to action in the text plan, never in the generation |
| community and shares | be sent to a friend, be commented on | the product rides along; the share trigger is the content's |

Rules:
- The user's instructions and documents set the goal when they say so; otherwise awareness and
  product memory, with native integration (`generation-system.md` §4b.2: noticed, not featured).
- Each video's **job** is one line in its plan's intent (§2.1): what the viewer does at the end
  (laughs, nods, sends it, rewatches) and what they keep of the product.
- A goal never changes the hard rules; it changes which references, mechanisms and concepts win.

## 3. The audience model (mass cognition)

Write the audience model once per run (`project-profile.md`): who the references speak to, the cues
that reveal it (setting, age, language, humour, captions, platform), and what that audience
recognises instantly. Then design every video for how people actually perceive a vertical clip:

- **The first second decides.** Before any word is read, the viewer registers a face, a motion
  onset, an oddity, a familiar situation or a caption's first words. Give them one of these; never
  a slow establishing shot.
- **Cognitive ease.** A viewer understands a situation they have lived in a fraction of a second
  (a desk, a bathroom mirror, a kitchen at night, a car after a shift) and a situation they have
  never seen only after effort. Build on the familiar, surprise inside it.
- **The curiosity gap.** The hook opens a question (what will happen, what is wrong here, why is
  he doing that); the payoff closes it. The gap is sized to the length: a 6 s clip opens and closes
  it fast; a 25 s story escalates two or three times.
- **Pattern interrupt.** A break in what the viewer expects (a sudden cut, an object entering, a
  freeze, a reaction, an insert) resets attention. Use the family's interrupts at the family's
  rhythm, never random ones (`generation-system.md` §5, "transitions").
- **Relatability and identity.** "That's me" and "that's my friend" are the two strongest share
  triggers. Specific beats general: the exact way someone checks the time at a boring desk beats
  "a bored person".
- **The emotion arc.** Name the feeling at the hook, the middle and the payoff (curiosity → tension
  → relief; recognition → escalation → absurd peak; calm → shock → deadpan). A flat arc is a
  retention leak.
- **How a laugh works.** Incongruity (two frames of reference collide), escalation (the same thing
  gets worse), the callback (a setup pays off later), timing (the pause before the turn), the
  deadpan (no reaction to something absurd), and the reversal (the expected outcome flips). Say
  which one a concept uses; a concept that uses none is not a comedy concept.
- **Social proof and meme literacy.** The audience knows the formats; using a format's grammar
  correctly reads as "one of us", using it wrongly reads as an ad. Captions follow the format's
  conventions (`text-and-format.md` §1) and never explain the joke.
- **Product memory.** People remember a product they saw someone like them use naturally, at a
  moment they enjoyed; they forget, or resent, a product that was presented. The product's
  brand mark is readable at a glance at the moments of highest attention (right after the hook,
  at the payoff) without being featured (`generation-system.md` §4b.2).
- **The share reflex.** A video is sent when it says something the sender wants to say about
  themselves or the receiver ("this is you", "this is us", "I told you"). Write the share line a
  viewer would type when sending it; if none comes to mind, the concept is weak.

## 4. The trend read (written into `20-analysis/project-profile.md`, "Trend read")

The references are the trend corpus. For each family and for the folder as a whole, record:

- **Format names** the audience would use (POV skit, story-time, "when…" caption gag,
  silent-acting one-take, reaction, meme-insert, "day in the life", duet-style, tutorial parody),
  with the caption grammar each uses.
- **Structural mechanisms**, which outlive any trend: the hook type, the escalation shape, the
  payoff timing, the interaction pattern, the camera behaviour, the role of text and sound.
- **Surface elements**, which date: a specific meme insert, a sound, a catchphrase, a caption
  template, an effect. Mark each as current, fading or dated from what the references show
  (platform cues, dates in file names or documents, how many references still use it).
- **Freshness policy:** reuse structural mechanisms freely; reuse a surface element only when it
  is still current and the family's language needs it (a meme insert is cut from the reference,
  never generated, `generation-system.md` §3c); never build a video on a dated surface element.
- **Adapt, never copy:** a Create video uses the mechanism in a new situation; it never remakes a
  reference's scene with the product swapped in (that is Recreate). Two videos in the run never
  share a situation or a joke.
- **Optional trend check (bounded):** when a decision depends on whether a specific format, meme,
  sound or caption convention is still current, or on its exact conventions, run at most two
  WebSearch queries per run to confirm, record the finding with its date in the trend read, and
  move on. The references stay the primary source; a search never replaces them, never adds a
  reference, and never slows the run beyond that.

## 5. Ideation and selection (Create), and the best approach

### 5.1 Concept seeds, scored (Create, A6)

For every video slot in a chosen style group:

1. **Diverge.** Write at least **five concept seeds**, one line each: `situation + turn + where the
   product lives`. Example: "night shift ends, parked car, slumps, lifts the sealed can from the cup
   holder, cracks it, first sip, melts — the can is the only light in the car." Draw situations from
   the audience model (places and moments they live in), turns from the family's mechanism, and
   the product's spot from its most natural use (`generation-system.md` §4b.0).
2. **Score** each seed 1–5 on:
   - **stop power** — what the first second shows, and whether it stops a thumb;
   - **relatability** — the "that's me" test, with a specific audience in mind;
   - **sharpness** — one clear idea, a real turn, sayable in one sentence; which laugh mechanism
     or emotion arc it uses (§3);
   - **product nativeness** — the product's presence is explainable in one clause and uses the
     product the way it is really used (or simply sits where it would);
   - **trend fit and freshness** — uses the mechanism, not a copy; no dated surface element;
   - **feasibility** — few movers, one camera behaviour per shot, physics-safe for the locked
     model, within one generation or the permitted clips (`generation-system.md` §6);
   - **brand safety** — nothing on the must-not-survive list, nothing the client would not post.
3. **Select** the highest total, with sharpness and stop power as tie-breakers; keep the runner-up
   in the plan as the fallback if the first cannot be rendered. Write the winner's **share line**
   (what a viewer types when sending it) and its **job** (§2).
4. **Distinctness.** Across the run, no two winners share a situation, a turn or a product beat;
   rotate settings, times of day, characters and the product's form of use.
5. **Show** one line per video: the winning seed, its score and the one reason it won. The user
   can swap it by replying; nothing is asked.

Seeds and scores go to `20-analysis/concepts.md`; the winner goes into the plan's intent (§2.1).

### 5.2 The best approach (both sub-modes)

Choose, and say in one line in the brief why this is the best approach for the goal:
- **Recreate vs Create** is the user's choice; within it, the pick (Recreate) or the style group
  and concept (Create) is chosen for the goal and the audience, not for convenience.
- **Recreate ranking** (`analysis-protocol.md` §5) adds the creative potential of each reference:
  mechanism strength, fit to the goal and the audience, how natural the product's integration can
  be (swap > contents > placement in hand > placement on a surface), the freshness of its surface
  elements, and the risk that the result reads as a copy rather than a native post.
- **Swap, contents or placement** follows `generation-system.md` §4b.0; creativity decides the
  anchor and the one interaction so that the product sits at a moment of high attention without
  becoming the subject.
- **Length and structure** follow the family profile; a concept is never stretched to fill a
  duration (`generation-system.md` §2.2).

## 6. The sharpness gate (before a concept enters a plan)

A concept passes only if every answer is yes:
- Can the idea be said in one sentence, and would a stranger get it from the clip alone?
- Does the first second show something (a face, a motion, an oddity, a familiar place, a caption's
  first words), not a setup?
- Is there a real turn, and does the payoff land on the family's beat?
- Would a specific viewer send it, and is the share line obvious?
- Is the product's presence explainable in one clause, and is it used (or placed) the way it
  really is?
- Does the clip loop or end on its strongest frame?
- Is anything in it generic (a "person enjoys product" beat, an explained joke, a staged product
  moment, a stock situation nobody lives in)? If yes, rewrite or drop.

## 7. Hook, payoff, loop, text and sound (the craft)

- **Hook (0–1 s):** motion onset or a face or an oddity in frame 1; the caption's first words carry
  the premise ("POV:", "when…", "me after…"); no logo, no establishing shot, no silence before
  something happens. The reference family's hook type is kept, its surface is new.
- **Middle:** escalation or demonstration, one visible change every two to three seconds, no
  dead space (`generation-system.md` §2.2); the product's interaction, if any, at a natural pause.
- **Payoff:** on the family's measured timing; the reaction after the cause (`anomaly-catalog.md`
  §2.3); the frame that would be the thumbnail.
- **Loop:** the end state echoes the start, or the last frame is the strongest one.
- **Text:** the hook line is the premise, never the explanation; the format's caption grammar;
  placed clear of the product (`capcut-assembly.md`), in the house style.
- **Sound (Create):** the soundtrack's role from the references' sound profiles (dramatic, comic,
  suspense, hype, SFX-driven); the lift or the drop on the payoff; memes keep their sound.

## 8. Creative QC (X9, as notes; the narrative gate decides)

After the physics and continuity checks, judge the clean video as a viewer:
- the hook is visible within the first second; the premise reads with the planned caption;
- the payoff lands where planned and reads without explanation;
- the product is recognisable at the moments of attention and nothing reads as an ad;
- the emotion arc and the laugh mechanism of the plan are present;
- the clip loops or ends strong.
A missing hook or payoff that the plan required is a **narrative** failure
(`generation-system.md` §5 gate) and a regenerate reason like any other gate failure; everything
else here is a **note** in the verdict ("hook lands at 0.4 s; payoff reads; share line holds"),
never a question to the user and never a retry on its own.

## 9. Edit Mode

The source's appeal is the user's; the creative layer only keeps it: the replacement's anchor and
state sit where the original's attention was, the caption stays clear of the product, and the
brief says in one line what the edit does to the video's appeal and what it must not break.
