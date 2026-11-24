# 02 — Editorial invention engine: long-form YouTube with intelligence and personality

## What exceptional content means here

Do not write a ten-minute Wikipedia paraphrase, fake-suspense documentary, or robotic succession of image prompts. Aim for a piece that rewards the viewer's *time*, not only their click: a satisfying question, a surprising but earned path to understanding, emotional and human texture, a credible worldview, visual thought, and an ending that recontextualizes the beginning. Genuine interest and clarity are not enemies of entertainment. Different niches warrant different densities, levels of humor, and narrator distance. Be inviting without sounding like a school assignment, and expressive without manufacturing drama.

The user chooses a **niche**, not a forced title or story form. The writer has creative discretion over a *new* subject and angle inside it ("Finding the subject" below). For the chosen subject, brainstorm **five substantively different** ways of telling it before choosing: contrast perspective (insider vs bystander), scale (one decision vs whole system), structure (event chronology vs consequence-first), voice (practical guide vs intimate inquiry), and visualization (diagram-led vs artifact-led). At least one candidate should challenge the most obvious reference formula. Reject near-identical variants where only a person/date/location changed: five battles told the same way are one approach, not five. Record the five in `40-plans/video-NN/direction.json` → `approaches` (10, 07): what each `changes` (perspective, scale, structure, voice, visualization; at least three of these across the five), its `pitch`, its `strongest_case`, its `long_form_risk`, and whether it `challenges_reference_formula` (at least one does). Then `chosen_approach` with its `runner_up` and why it lost: the comparison is the reasoning, not a score. Rank **not by mathematical virality scores** but by: genuine open question, richness of evidence, ability to sustain locked duration, human consequence, visual potential, unique viewpoint, feasibility and earned conclusion.

No title, hook or narrator performance can save a premise with only three minutes of substance. If research finds no depth, return to topic exploration *before recording*. Never add invented “facts,” pointless facts, filler, machine-gun rhetorical questions or theatrical fake stakes to reach the duration.

**Comprehension without simplification.** A first-time viewer should always know who matters, what is happening and why it matters, while the film keeps its complexity, wit and surprises. Confusion is a cause to find (a name never set up, too much at once, a payoff too far from its set-up, a picture that shows something else), not a reason to explain everything; a mystery the viewer wants solved is a promise, and stays (03 "What the viewer knows at each turn").

## Finding the subject (topic discovery)

Before any approach or treatment, find the strongest subject the user's scope allows, and write the reasoning in
`direction.json` → `subject` (07). A weak subject is rarely rescued by production; an ordinary-looking one may hold an
exceptional explanation. The material decides this, not polish, fame or drama.

- **Scope first.** The user gave a niche, a subject inside it, an exact topic, or an exact story or concept
  (`scope.kind`; their own words in `user_words`; the locked niche in `niche`). Inside a niche the subject is ours to
  find; inside a broad subject, a narrower topic or an original angle within its bounds; an exact topic keeps its topic
  and researches its strongest angles (the candidates are those angles); an exact story or concept is developed, never
  replaced. For a subject, a topic or a story, write what the user asked for in your own words (`understood_as`) and
  where it would stop being that (`boundary`), then how the choice stays inside it (`selection.how_scope_kept`; for an
  exact topic or story also `keeps_user_scope: true`). Shared words prove nothing either way: "how a white rock paid
  Roman soldiers" is still "the history of salt", and "salt in the kitchen" is not, whatever words they share. For an
  exact topic or story the blind treatment reader is also asked whether each treatment is still a video about what was
  asked (06); a "partly" or "no" is a finding you answer.
- **What this audience values.** Read it from the references and the niche, never from one niche's idea of interesting:
  a history video may reward consequential decisions, a geography video an extraordinary phenomenon understood, a
  biology video a surprising mechanism, a tutorial a problem solved, a "what if" its logically developed consequences,
  a comedy its premise and timing (examples, not categories). Write it in `audience_value`.
- **References as evidence.** Each card's `moments_that_matter` (01) records, with times, what a reference does to make a
  development matter (observed) and why that may work (interpretation, kept apart). `from_references` names those that
  shaped the search. They show where value may lie; they never confine us to their subjects, and a technique seen in a
  successful video is not why it succeeded unless evidence says so.
- **Research the material, not titles.** For each promising candidate (an event, a mechanism, a phenomenon, a problem
  and its solution, a question, a relationship, a transformation, a concept), find what genuinely makes it worth a
  viewer's time: `what_happens` (what is discovered, explained, shown or experienced), `why_it_matters` (within this
  subject and experience), `reward`, and its `strongest_material`, each item with an `id` (M1, M2...) and how sure the
  film may be of it (`certainty`):
  - established: a fact, resting on `claims` (claims.json) whose sources were read;
  - reasoned: a consequence that follows from established items (`from`) by reasoning you state (`reasoning`);
  - contested: credible sources disagree, or the evidence leaves it open; said with its `hedge`;
  - speculative: a possibility beyond the evidence, said as one (`framed_as`);
  - assumed: an explicit premise of a hypothetical, said as an assumption (`framed_as`);
  - invented: only where the subject is not factual (a comedy's premise, a fiction).

  Inside a broad subject look for the strongest angle, not the most famous event or a whole chronology; read a timeline
  for turning points and dependencies when the subject has one.
- **A recorded source is not evidence; the reading of it is.** Weigh each source before anything rests on it and write
  what you found in its ledger entry: who made it and with what expertise; primary (the record, the study, the data),
  secondary (an account of them) or popular (press, encyclopedias, videos); its date, and whether newer work replaced
  it; whether it really says what you need (the claim itself, not a nearby one; the abstract's own hedges kept);
  whether independent sources agree or disagree; and how much of it you read (`- Access:` read, indirect or snippet). A
  search summary is a lead, never a source. Each consequential claim gets its confidence in claims.json: confirmed (a
  primary record, or two or more independent credible sources, read), likely (one credible source), disputed (credible
  sources disagree), legend (popular, unverified). Extraordinary claims need strong support: what the choice of subject
  rests on (`selection.decisive_material`), when it is said as established, must be confirmed. Don't dismiss the
  surprising either: a strange fact with strong evidence is exactly what this stage is looking for.
  - Science: keep the mechanism accurate and the uncertainty where the evidence leaves it (a result in cultured cells is
    not a result in people; a preprint is not a consensus; "may" in an abstract stays "may").
  - History: established facts, contested interpretations and counterfactuals stay apart; a famous quote or story with
    no contemporary source is legend until shown otherwise.
  - A "what if": the premise is assumed, what follows from known science is reasoned, what nobody can know is
    speculative; a possibility is never presented as a guaranteed consequence.
  - Fiction and comedy: invented material is fine, and is never dressed as fact.
- **Magnitude is not sensationalism.** Death, war, huge numbers or a shocking claim are not value by themselves; an
  ingenious mechanism or a useful solution can be the bigger reward. A candidate whose exciting version needs
  exaggeration is not the one. A long build-up must be worth its reward, unless the journey itself is the value; many
  videos reward continuously (discovery, cumulative understanding, progress, humour) rather than once.
- **Enough for the locked length, judged from the material.** No share of minutes decides this: six minutes of notes can
  hold ten when each development opens the next, and fifteen may not when they repeat. For each candidate write its
  `runtime.progression` (what the viewer newly gets, step by step, each step resting on its material ids), a `verdict`
  (sustains, short or uncertain) and `why`, from the density this audience wants, the treatment it could have and the
  pictures and sound it allows. Where it is thin, say what is missing (`shortfall`). A chosen candidate judged short or
  uncertain goes back to re-selection (another candidate, or a wider or narrower angle inside the scope) or to the
  user, whose decision is recorded in `runtime_decision` (`decided_by: "user"`, their words, the decision: another
  length through the lock, another angle). Never invented developments, repetition, slower speech, pauses or extra
  exposition to fill it. An estimate of minutes may be noted (`material_minutes`); it never decides.
- **Can we make it?** `feasibility`: whether stills, drawings, maps, voice and music can carry it.
- **How many.** No fixed number: research until a strong decision is supported, and stop there. An open scope (a niche,
  a subject, an exact topic's angles) needs at least one researched alternative, because a choice with nothing to choose
  from is the first idea that came up. Compare genuinely different alternatives, not five versions of one idea.
- **Choose in words, on the evidence.** `selection`: the candidate, `why` it is the strongest opportunity in scope, the
  material the choice rests on (`decisive_material`), and for each alternative why not (`over_alternatives`: one entry
  per candidate, each its own reason). Say when it was close. No scores, weights or thresholds. Put every reason through
  the swap test: if it would still be true with another candidate's name in it ("it changes how the viewer sees X"), it
  explains nothing, and the checks refuse reasons two candidates share. Signs of a shallow choice, to catch in yourself:
  the first plausible search result; fame doing the work; a reference's title repeated without further research; a
  sensational claim preferred over better-supported material; conflict or a climax assumed where the subject offers
  understanding; material that can't fill the length.
- **Carry the value forward.** `value_to_carry`: the findings the film must deliver (`what`, `why_it_matters`,
  `certainty`; `rests_on`: the material ids it stands on, never said more surely than they allow; `needs_first`: the
  values the viewer must hold before it). Each is carried by a beat (`carries` in the beat map), after what it needs
  first. Where the video turns or pays off, that beat is a key moment, and its shots say how the picture carries it
  (`carries_significance`); where value builds step by step (a tutorial, a tour of a mechanism, a run of jokes), no key
  moment is needed and none is invented: the blueprint says how the value builds (`reward_shape`). The script says each
  factual value in the beat that carries it (one of its claims tied to a line there) and as surely as it is known (a
  contested, speculative or assumed value names the line that says so: the beat's `hedges`), and the pictures are given
  what each beat carries and how sure it is (the media gate), so a possibility is never drawn as a documented fact. One
  the film no longer needs goes in `dropped` with the reason. Research identifies the opportunity; the director decides
  how to realise it, and may leave out what weakens the experience, never silently.
- **When it changes.** Another subject is another film: everything follows. A new angle on the chosen subject (its own
  description) is another story: the beat map, script and shot plan follow, and the media follow them where they
  changed. A researched value that changes reaches only the beats that carry it, their lines and their shots. A
  corrected source or claim is re-checked where it is used (plan-check names the claims, lines and values), then
  recorded with `direction-lock --research-rechecked`, never rebuilt. The other candidates, the reasons and the research
  notes feed nothing.

`direction-lock`, `plan-check`, `shot-check` and the media gate check that this reasoning exists, is specific, rests on
read sources, keeps the scope and reaches the beat map, the script and the pictures. Whether the subject is worth a
viewer's time, and whether a source deserves trust, is the director's judgement, not theirs.

## The story engine (author before script)

Write `40-plans/video-NN/blueprint.json` and a compelling 1–2-page `outline.md` that answer:

1. **Audience promise.** Why click? What exact valuable feeling, knowledge or resolution will be delivered? Promise a real answer; don't set a misleading or overbroad challenge.
2. **Carrying question.** What thoughtful uncertainty can sustain curiosity, and what are its real causal steps? Set it up early; it doesn't have to be shock or fear.
3. **Original angle.** What fresh viewpoint, organizing device, illustration method or surprising-but-well-supported contrast differentiates this video from its references?
4. **Human lens.** Who or what experiences consequences? A relatable constraint, dilemma, error, physical scale, sensory detail or plain-language analogy often gives the facts a human shape. Historical actors are not fictional narrators unless clearly framed as reconstruction.
5. **Movement.** Each section must earn its inclusion by altering the viewer's understanding: make a claim, show evidence, expose a constraint, deepen a dilemma, reveal an exception, demonstrate something or pay off an earlier detail. Do not line up five chapters that all restate the same point.
6. **Meaningful relief.** Place natural laughter, warmth, awe, surprise, self-questioning or reflection where the material invites them. Leave some ambiguity for the viewer to resolve. Slow scenes may be the strongest scenes when there is something to contemplate.
7. **Visual argument.** Sketch the picture that contributes information rather than echoes the narration. How do map movement, comparison, diagrams, artifacts, faces, scale, negative space or a quiet close-up change comprehension?
8. **Closing satisfaction.** Answer the original promise, then offer an earned broader implication or question. Avoid an abrupt cut or a generic sermon/CTA.

Treat the title/thumbnail as the **opening contract**. The first 30–60 seconds should demonstrate that the video can deliver, not waste time introducing the channel. The intro can begin with an outcome, an intimate detail, a specific problem, a source discovery or a visually legible contradiction. Avoid a single mandatory “what if I told you ...” gimmick.

## Adaptive methodology: creative profiles and episode strategy

There is no fixed formula for how-to, historical, counterfactual, or any other niche. The right creative approach depends on the specific subject, the evidence from the references, and what this particular video is trying to achieve. Discover it; don't assume it.

### Generate a creative profile per cluster

After grouping references into creative clusters (see §01), generate a **creative profile** for each meaningful cluster. Store it as `20-analysis/creative-profiles/[cluster-slug].md`. This is a diagnostic summary—not a template—covering what appears to work for that audience and format, what weaknesses the references show, and what creative territory remains unexplored.

Each profile should capture, with reference IDs and timestamps:

- **Audience expectations and viewing purpose:** what viewers likely arrive wanting, and whether references meet or deliberately subvert that.
- **Storytelling mechanisms** that appear to sustain interest—curiosity development, revelation timing, emotional movement, information density. Label each `[I]` (plausible inference) unless confirmed by actual analytics `[M]`.
- **Emotional and intellectual register:** how humor, tension, awe, curiosity, reflection, and warmth appear—and whether they feel earned or manufactured.
- **Narrator personality:** what voice characteristics appear to suit this audience and why.
- **Visual and cinematic language:** what the references accomplish visually, and where they fall short.
- **Pacing and breathing room:** where references slow down and speed up, and whether the rhythm appears intentional.
- **Originality gap:** what these references don't do that could be genuinely compelling to the same audience.
- **What to avoid copying:** distinctive aesthetic choices, structural devices, or voice identities that belong to those creators.
- **How picture, voice and sound work together** in these videos, from their watch sheets and measurements (`av-profile`, 01): the rhythm of cuts against sentences, where the voice lifts or settles, where music sits, what each does when the story turns. Label measured `[O]` and inferred `[I]`; note what makes them enjoyable, not only what they contain.

A technique found effective in one cluster may inspire a genuinely different application elsewhere. Cross-cluster experimentation is encouraged when it serves the specific subject and audience—but transferred techniques must be adapted to the destination context, not transplanted wholesale.

### Episode-specific creative strategy

Receiving a creative profile does not mean applying it. For every video, the agent must independently determine the best creative approach for this specific subject and intended experience.

Before writing complete narration, write the episode-specific creative strategy in `40-plans/video-NN/direction.json` → `strategy` (07 has the keys), covering:

- Why this particular idea is worth a viewer's time at this length.
- What experience the viewer should have—what they discover, feel, understand, or question.
- How the story progresses without padding or artificial urgency.
- Which tools from the story engine above fit this subject, and which would feel forced.
- How factual information becomes an enjoyable experience rather than an information delivery.
- What visual storytelling contributes beyond illustrating spoken words.
- How the narration should sound and breathe for this story: its register, where it slows or quickens, and the few moments (if any) that must land in silence. Read this against the references' measured delivery (`pace-profile`: their pace and how they pause), not copied from it. 03's pauses and 05's voice and tag choices carry out what this says; they never invent their own.
- What makes the execution distinct from the references.

Do not mechanically insert humor, tension, cliffhangers, emotional beats, or rhetorical questions to satisfy a format expectation. A quiet, reflective video can be exceptional. So can a playful, energetic one. The right choice depends on the subject and the intended experience.

The strategy then becomes two or three **audiovisual treatments**: narrator, writing voice, pacing, visual language, sound and how picture and voice relate, decided together and tried in sample moments. A blind read compares them, the director decides, and `direction-lock` fixes the choice before the script is written. How is in **10-creative-direction.md**; it is the creative director's manual, and the script stage (03) and the visual and voice stages (04, 05) work from what it locks.

## Research that supports creativity without turning into a hard documentary

For factual work, obtain primary and credible secondary sources independent of reference videos. `30-research/video-NN/sources.md` has one `### S1.` entry per source with URL/title, author/issuer, publication or revision date, primary or secondary, `- Access:` (read, indirect or snippet: how much of it was actually read), precise claims supported, counterevidence and verification status. `claims.json` lists consequential dates, numbers, quotes, geographic claims, causal assertions, dangerous instructions and contested conclusions with source IDs, confidence (confirmed, likely, disputed or legend: "Finding the subject") and the script lines that say them (`line_refs`). Cite internally in planning; final narration can flow naturally without reading footnotes aloud. `plan-check` lists `numbers_without_claim`: lines that state a date, count or distance and are tied to no claim. Each consequential one gets a claim, verified, before the part that holds it is recorded, because a wrong number found later costs a re-record. A trivial one (a count of sides, the narrator's premise) needs none. If evidence is disputed, narrate the dispute honestly, with distinct perspectives when relevant. For nonfactual/fictional stories, label the genre and keep scene logic consistent; do not falsely imply documentation.

**Voice and humanism:** Narration is written for *listening*, not silently reading. Use varied sentence length and light, well-placed conversational language. A single vivid detail can do the work of several abstract paragraphs. Use “we” sparingly and “you” only when it genuinely engages the viewer. Personal warmth may be inquisitive, dry, playful or reflective; never one relentless hyped-up sales pitch. Let characters have constraints and decisions, not just pronouncements. Pause to let a consequence land. Nothing about “being engaging” requires fabricated conflict, machine-gun cliffhangers or editing every 1.5 seconds.

**No holiday, religious or superstitious narrative devices.** Never pick a holiday/religious feast (Thanksgiving, Christmas dinners, etc.), a religious ceremony or practice, or a superstition/supernatural claim (omens, luck, ghosts, astrology, curses) as the vivid detail that carries a beat — not as period texture, irony, dramatic contrast, or scene-setting — no matter how well-documented or historically accurate it is. If research surfaces one, leave it out and find a different detail to do that narrative work. Plain factual context that's genuinely unavoidable to the story (e.g., stating that a culture's religion shaped a historical event) can still be stated, but never dramatized as a scene or used as the illustrative device.

**Nothing indecent, gory or distressing.** No subject, line, caption, picture, thumbnail or sound shows, describes or dwells on: nudity, implied included (a bare body or one in underwear/swimwear/a towel only; a bare chest; a moment whose ordinary form is undressed — a shower, bath, changing clothes, sauna, swim, beach in swimwear; anything sexual or suggestive); gore and injury (blood, a wound, a burn, a broken bone, a body or body part, a corpse, a death or violence shown as it happens, an accident's aftermath, a hurt animal or carcass); extreme distress (agony, terror, panic, sobbing, screaming, despair, a breakdown; suicide or self-harm, spoken or shown; cruelty); anyone shown as if dead, unconscious or gravely ill (nobody lies limp or flat with closed/half-closed eyes on a floor, stretcher or sickbed; someone being cared for is awake, eyes open, sitting up where the story allows; a survival pose low on the ground — crawling, bracing, a recovery position — always shows the person clearly alive: head up or turned so the open eyes show, mid-move, never limp or still); children or anyone who looks like one (every person is a clearly adult figure); and what a family audience isn't shown or told — vomit, excrement, a toilet in use, drugs, drunkenness, graphic medical detail (a needle in skin, an operation, a wound being treated), swearing, slurs, crude jokes, or a person humiliated. A subject whose story genuinely *needs* any of this to be told (a gruesome crime, a war's atrocities, an illness told by its symptoms, a disaster told through its victims' suffering) is not a viable subject at all; one where such a fact is incidental is told without it. A hard fact may still be stated plainly: how many people died is a fact and may be said; how a body was found, what an injury looked like, or how someone suffered is not. No line names an intimate part of the body, even as a clinical/first-aid fact — tell it by its other, non-intimate places.

**Sensitive subject, never graphic telling.** A war, a crime, an accident, a disaster, a death or historical violence can be a strong subject; it is never rejected for being one. What separates it from the rule above is presentation: the facts are told plainly and with their full weight (how many fell, that a man was wounded and carried on, what the decision cost), and nothing graphic is shown or described. The picture finds what carries the meaning without the gore: the place, the map, the objects left behind, the weather, the people before or after, a figure at a distance, a period illustration. These are possibilities, not a template; the story's seriousness and impact must survive, and a bland retelling is a failure too.

**Reference material left out stays out.** A reference's content review (01) may exclude a segment: a graphic one, or a religious, superstitious or holiday device. Nothing from it is cited, adapted or rebuilt in disguise (the same device under another name is the same device), and what depended on it goes with it. The rest of that reference keeps teaching: its pacing, hooks, structure and craft. When an exclusion removes something a story needed, build a different, original bridge that does the narrative work, never a mechanical splice or filler; when it cannot be done coherently, say so instead of leaving a gap.

## Originality and copyright integrity

Mined references may contribute functional techniques (e.g., start with the outcome, explain with a scale comparison, slow down on a decision), but never copy their unique shot sequences, artistic identities, voice recordings, specific scripts, distinct jokes or watermarked materials. No attempt to disguise replicated footage. For a borrowed functional device write `source timestamp → audience function → genuinely different new application → adaptation trade-off`. Generate original assets or use sources with clear licenses.

**Internal conversation:** Creative lead may critique concepts internally while drafting. Independent readers come in at three points only: the blind treatment comparison, the cold read of the script, and the final watch review (06, 10), never at every small edit. Do not outsource artistic judgment to a rigid number: the producer owns the final direction, and records why when it overrules a reader.
