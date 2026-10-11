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
| **Creative director** | Generates many ideas, scores them, picks the sharpest, kills the bland, keeps every video distinct, and chooses the best approach for the goal. Takes from a reference *how* it was made, never *what* it shows: a Create video is a new subject and a new idea built with the collected craft | the craft sheet and the copy test (§5.0), ideation and selection (§5.1), the best approach (§5.2) |
| **Performance editor** | Lands the hook in the first second, the payoff on the planned beat, the loop at the end, the text as a hook, the sound as a lift | the time budget (`generation-system.md` §2.2), the text and sound plans, the creative QC (§8) |

In **Viral-Browser** the team widens to a growth strategist, a direct-response seller, a statistician and a
red-team sceptic (`viral-browser.md` §1); §3 (the audience model) and §4 (the trend read) apply to it unchanged, and
§5.0 (craft versus subject) is what separates a mechanism from a product there.

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
  freeze, a reaction, an insert) resets attention. Use the interrupts of the mechanisms the video borrows (Recreate: the source's family), at their
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
  share a situation or a joke. What may be taken from a reference and what may not is fixed by the
  craft sheet and the copy test (§5.0).
- **Optional trend check (bounded):** when a decision depends on whether a specific format, meme,
  sound or caption convention is still current, or on its exact conventions, run at most two
  WebSearch queries per run to confirm, record the finding with its date in the trend read, and
  move on. The references stay the primary source; a search never replaces them, never adds a
  reference, and never slows the run beyond that.

## 5. Ideation and selection (Create), and the best approach

### 5.0 Transfer, not repetition: the craft sheet and the copy test (Create)

The analysis tells how the references work. Create uses that knowledge to make **another video**:
a new subject, a new situation, a new idea, built with the style, the properties, the approach,
the craft and the hook logic that the references proved. It never restages what a reference
shows. Restaging a reference's scene with the client's product is Recreate's job and is a
different sub-mode; in Create it is a failure, even when every frame is new.

**Two layers in every reference.** The analysis card separates them (protocol §3, "Transferable
craft" vs "Subject & entities"), and the synthesis writes them into `20-analysis/craft-sheet.md`,
one block per family and per reference that matters:

| layer | what it holds | Create |
|---|---|---|
| **Craft (how)** | **style:** look, palette and grade, lens and framing habits, light, era, performance register (deadpan, over-acted, silent), stylised or real; **properties:** length, pacing curve, cut rhythm, first-cut and speech-onset timing, caption grammar and text role, sound role, camera behaviour, aspect and shot sizes; **approach:** format name, hook *type* (not the hook), structure shape, escalation and reveal logic, payoff timing, interaction pattern, laugh mechanism, emotion arc, loop logic, how the viewer is addressed; **crafting:** one take or cuts, POV or observed, where text sits and when, when and how the product reads (swap, contents, placement; in hand, on a surface, the mark's moments), how the ending is built; **why it works:** the cognitive trigger behind the hook, the turn and the share | collected as **ingredients**: one mechanism at a time, re-expressed for the product; never lifted as one whole template (§5.0b rules 1 and 4) |
| **Subject (what)** | the premise and the situation, the setting and the location, the characters and their look, the specific action sequence, the joke's content and the punchline, the lines, the caption wording (except a generic meme line, `text-and-format.md` §1), the prop set and its arrangement, the first-frame composition, the ending image, the source product's own beat, the sound or track (a meme insert is the only exception, `generation-system.md` §3c) | left behind; the concept brings its own |

**The transfer rule.** A concept seed takes its **mechanism, style and properties from the craft
sheet** and its **subject from the audience model** (§3: the places, moments and situations the
audience lives in) and from the product's own natural use (`generation-system.md` §4b.0). It never
takes a subject line from a card. Minimum distance from every reference: a different premise,
a different setting, different characters in different roles, a turn with different content, a
different product beat and a different ending image. What may coincide: a borrowed mechanism,
the length and pacing the references show, caption grammar, camera behaviour and look, and a generic meme line; never the
whole structure, beat order and tone of one reference (§5.0b rule 4).

**The copy test** (at ideation on every seed, in the sharpness gate, and in the creative QC).
Someone who has seen the reference watches the new clip. Would they say any of these?
1. Same premise or situation ("the night-shift car scene again").
2. Same setting or the same kind of location dressed the same way.
3. The same character type doing the same action in the same order.
4. The same turn: the joke's content, the reveal, the punchline.
5. The same line, caption wording or sound (beyond a generic meme line or a cut insert).
6. The same first-frame composition or prop arrangement.
7. The same ending image.
8. The product doing exactly what the source product did at the same beat.
9. The same structure, beat order and tone as one reference or one family, with only the product swapped (the template-lock test, §5.0b rule 4).
One yes makes the seed a remake: it is rewritten with a new subject or dropped, and scores 0 on
trend fit and freshness (§5.1). The test is run against every reference the seed borrows from (and every family it draws on), not only
the nearest one, and across the run's own videos (§5.1 step 4).

**What "collect details" means.** Details are taken as *kinds*, not as *instances*: "the hook is a
face reacting before the viewer knows to what" is collected; "a man in a grey hoodie reacts to a
dog in a kitchen" is not. "The caption is a two-word POV line in the upper third" is collected;
its wording is not. "The product reads in the hand during the turn, label toward the lens" is
collected; the source's desk, mug and window are not. When a reference's strength is its subject
alone (a situation nobody else has used), the collected detail is the *kind* of situation
(a lived micro-moment with an unexpected consequence), and the seed invents another of that kind.

**Honest exceptions.** A format whose identity *is* its fixed frame (a running meme template, a
duet grid, a "caption over a still" format) keeps that frame as a property; its content still
changes. A trend check (§4) may confirm that a format's fixed frame is still current; it never
licenses the content.

### 5.0b Blend, not mimic: reference craft × product truth (Create)

Create is not "the references again with the product swapped in", and it is not bound to the
references' formats. It designs the most engaging video for *this* product from two inputs of equal
weight: the **references, understood** (why they work: hook logic, structure, proof, emotion, the
audience's situations, what is current; the craft sheet and the trend read) and the **product,
understood** (what it is, who wants it, what it can honestly show, what reads on camera, its
product truths; the insight sheet `30-assets/product-insights.md`, written from the supplied assets,
`assets-and-substitution.md` §2 step 3b). The references supply proven ingredients; the product
supplies the truth that makes the idea its own.

1. **Families are evidence and ingredients, never a menu or a template.** Style groups (command A6)
   are suggestions. The agents may also propose **hybrid groups** that mix mechanisms from several
   families, or a format the references never showed, when the mechanisms and the product's strengths
   support it (a skit's reveal driven by a sound the product makes; a tutorial's demonstration played
   as a deadpan one-take). A seed need not belong to any reference group.
2. **Every seed names its blend** in one line: the reference mechanism it borrows (craft-sheet id),
   the product truth it uses (insight-sheet line), the audience situation, and how the mechanism is
   re-expressed through what the product uniquely can do or show.
3. **The blend test** (with the copy test, on every seed): remove the product and the idea turns
   generic; remove the mechanism and it is only an ad. Both removals must break it. A seed made only
   of the references (the product pasted in) or only of the product (a packshot with a caption) is
   rewritten.
4. **The template-lock test** (the ninth question of the copy test): is it one reference's or one
   family's structure, beat order and tone with the product swapped in? Then it is a remake in
   disguise: rewrite it with another structure or another mix of mechanisms.
5. **Choose for engagement, not conformity.** The seed with the highest engagement potential for the
   goal and the audience wins, even if it looks unlike any reference, provided the hard rules and the
   sharpness gate hold; the trend read decides what is still current.
6. **The product is a source of ideas, not only an object to place.** Its sensory and functional
   strengths (a sound, a colour change, a texture, a satisfying motion, a one-hand use, a reveal) are
   the first place to look for a hook, a turn or a payoff, inside its affordance sheet and size
   reckoning; a concept that needs the product to do what it cannot is rejected.
7. **Precedence stays:** the blend never overrides the hard rules (command items 6, 14, 15, 18, 19),
   the anomaly catalog, the guardrails, the house approach or the user's instructions.

### 5.1 Concept seeds, scored (Create, A6)

For every video slot in a chosen style group (or a hybrid group, §5.0b):

1. **Diverge.** Write at least **five concept seeds**, one line each: `situation + turn + where the
   product lives`, plus its blend line (§5.0b: the borrowed mechanism, the product truth, the audience
   situation). Example: "night shift ends, parked car, slumps, lifts the sealed can from the cup
   holder, cracks it, first sip, melts — the can is the only light in the car." Draw situations from
   the audience model (places and moments they live in), hooks and turns from the **mechanisms of the
   craft sheet, from any family and in any mix**, the idea itself from the **product truths of the
   insight sheet**, and the product's spot from its most natural use (`generation-system.md` §4b.0).
   Never draw a situation, a setting, a joke or a line from a reference's card: the craft sheet gives
   the how, the insight sheet gives what the product brings, the seed invents the rest (§5.0). Run
   the copy test and the blend test on every seed before scoring it.
2. **Score** each seed 1–5 on:
   - **stop power** — what the first second shows, and whether it stops a thumb;
   - **relatability** — the "that's me" test, with a specific audience in mind;
   - **sharpness** — one clear idea, a real turn, sayable in one sentence; which laugh mechanism
     or emotion arc it uses (§3);
   - **product nativeness** — the product's presence is explainable in one clause and uses the
     product the way it is really used (or simply sits where it would), and a real strength from
     the insight sheet is part of the idea;
   - **blend** — the idea needs both a reference mechanism and a product truth (§5.0b rule 3); a
     seed that fails the blend test or the template-lock test scores 0 here and is rewritten;
   - **trend fit and freshness** — uses the mechanism, not a copy; no dated surface element; a
     seed that fails the copy test (§5.0) scores 0 here and is rewritten or dropped;
   - **feasibility** — few movers, one camera behaviour per shot, physics-safe for the locked
     model, within one generation or the permitted clips (`generation-system.md` §6);
   - **brand safety** — nothing on the copyright and ownership floor, nothing the generation
     service refuses, and nothing the client's guardrails ban (`brand-guardrails.md` §4: a content
     or context hit scores 0 here and the seed is dropped; limits, competitor and wording rules
     are invariants the plan obeys). With no guardrails, no content is avoided for taste: a bar,
     a gag with fake blood or a swear word in a caption is as eligible as anything else.
3. **Select** the highest total, with sharpness and stop power as tie-breakers; keep the runner-up
   in the plan as the fallback if the first cannot be rendered. Write the winner's **share line**
   (what a viewer types when sending it) and its **job** (§2).
4. **Distinctness.** Across the run, no two winners share a situation, a turn or a product beat;
   rotate settings, times of day, characters and the product's form of use. The copy test (§5.0)
   is also run between the run's own winners, so the run itself does not repeat.
5. **Show** one line per video: the winning seed, its score and the one reason it won. The user
   can swap it by replying; nothing is asked.

Seeds and scores go to `20-analysis/concepts.md`; the winner goes into the plan's intent (§2.1).

### 5.2 The best approach (both sub-modes)

Choose, and say in one line in the brief why this is the best approach for the goal:
- **Recreate vs Create** is the user's choice; within it, the pick (Recreate) or the style group
  and concept (Create) is chosen for the goal and the audience, not for convenience. A Create
  concept is a **blend** of the references' mechanisms and the product's own truths (§5.0b), chosen
  for engagement, not for resemblance to a reference.
- **Recreate ranking** (`analysis-protocol.md` §5) adds the creative potential of each reference:
  mechanism strength, fit to the goal and the audience, how natural the product's integration can
  be (swap > contents > placement in hand > placement on a surface), the freshness of its surface
  elements, and the risk that the result reads as a copy rather than a native post.
- **Swap, contents or placement** follows `generation-system.md` §4b.0; creativity decides the
  anchor and the one interaction so that the product sits at a moment of high attention without
  becoming the subject.
- **Length and structure** follow the measured ranges of the mechanisms the concept borrows and what the product's
  demonstration needs (Recreate: the source's family profile); a concept is never stretched to fill a
  duration (`generation-system.md` §2.2).

## 6. The sharpness gate (before a concept enters a plan)

A concept passes only if every answer is yes:
- Can the idea be said in one sentence, and would a stranger get it from the clip alone?
- Does the first second show something (a face, a motion, an oddity, a familiar place, a caption's
  first words), not a setup?
- Is there a real turn, and does the payoff land on the beat the plan sets (the timing of the mechanism it borrows)?
- Would a specific viewer send it, and is the share line obvious?
- Is the product's presence explainable in one clause, and is it used (or placed) the way it
  really is?
- Does the clip loop or end on its strongest frame?
- Is anything in it generic (a "person enjoys product" beat, an explained joke, a staged product
  moment, a stock situation nobody lives in)? If yes, rewrite or drop.
- Does it pass the blend test and the template-lock test (§5.0b): the idea needs both a reference
  mechanism and a product truth, and it is not one family's template with the product swapped in?
  If not, rewrite or drop.
- Does it pass the copy test (§5.0): a new premise, setting, characters, turn, lines, first frame,
  ending and product beat, with only the craft carried over? If not, it is a remake: rewrite with
  a new subject or drop.

## 7. Hook, payoff, loop, text and sound (the craft)

- **Hook (0–1 s):** motion onset or a face or an oddity in frame 1; the caption's first words carry
  the premise ("POV:", "when…", "me after…"); no logo, no establishing shot, no silence before
  something happens. The hook type the video borrows is kept, its surface is new.
- **Middle:** escalation or demonstration, one visible change every two to three seconds, no
  dead space (`generation-system.md` §2.2); the product's interaction, if any, at a natural pause.
- **Payoff:** on the borrowed mechanism's measured timing; the reaction after the cause (`anomaly-catalog.md`
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
- the clip loops or ends strong;
- (Create) the copy test (§5.0) against the references the blend borrowed from and the run's other videos: the
  clip shares craft with them, not subject;
- (Create) the blend (§5.0b): the product truth named in the plan is visible on screen, and the clip
  reads as its own idea, not a reference template with the product swapped in.
A missing hook or payoff that the plan required is a **narrative** failure
(`generation-system.md` §5 gate) and a regenerate reason like any other gate failure; everything
else here is a **note** in the verdict ("hook lands at 0.4 s; payoff reads; share line holds"),
never a question to the user and never a retry on its own.

## 9. Edit Mode

The source's appeal is the user's; the creative layer only keeps it: the replacement's anchor and
state sit where the original's attention was, the caption stays clear of the product, and the
brief says in one line what the edit does to the video's appeal and what it must not break.
