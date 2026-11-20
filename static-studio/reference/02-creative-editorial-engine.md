# 02 — Editorial invention engine: long-form YouTube with intelligence and personality

## What exceptional content means here

Do not write a ten-minute Wikipedia paraphrase, fake-suspense documentary, or robotic succession of image prompts. Aim for a piece that rewards the viewer's *time*, not only their click: a satisfying question, a surprising but earned path to understanding, emotional and human texture, a credible worldview, visual thought, and an ending that recontextualizes the beginning. Genuine interest and clarity are not enemies of entertainment. Different niches warrant different densities, levels of humor, and narrator distance. Be inviting without sounding like a school assignment, and expressive without manufacturing drama.

The user chooses a **niche**, not a forced title or story form. The writer has creative discretion over a *new* angle inside it. For every video brainstorm **five substantively different** options before choosing: contrast perspective (insider vs bystander), scale (one decision vs whole system), structure (event chronology vs consequence-first), voice (practical guide vs intimate inquiry), and visualization (diagram-led vs artifact-led). At least one candidate should challenge the most obvious reference formula. Reject near-identical variants where only a person/date/location changed: five battles told the same way are one approach, not five. Record the five in `40-plans/video-NN/direction.json` → `approaches` (10, 07): what each `changes` (perspective, scale, structure, voice, visualization; at least three of these across the five), its `pitch`, its `strongest_case`, its `long_form_risk`, and whether it `challenges_reference_formula` (at least one does). Then `chosen_approach` with its `runner_up` and why it lost: the comparison is the reasoning, not a score. Rank **not by mathematical virality scores** but by: genuine open question, richness of evidence, ability to sustain locked duration, human consequence, visual potential, unique viewpoint, feasibility and earned conclusion.

No title, hook or narrator performance can save a premise with only three minutes of substance. If research finds no depth, return to topic exploration *before recording*. Never add invented “facts,” pointless facts, filler, machine-gun rhetorical questions or theatrical fake stakes to reach the duration.

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

For factual work, obtain primary and credible secondary sources independent of reference videos. `30-research/video-NN/sources.md` records URL/title, author/issuer, publication or revision date, precise claims supported, counterevidence and verification status. `claims.json` lists consequential dates, numbers, quotes, geographic claims, causal assertions, dangerous instructions and contested conclusions with source IDs and confidence. Cite internally in planning; final narration can flow naturally without reading footnotes aloud. `plan-check` lists `numbers_without_claim`: lines that state a date, count or distance and are tied to no claim. Each consequential one gets a claim, verified, before the part that holds it is recorded, because a wrong number found later costs a re-record. A trivial one (a count of sides, the narrator's premise) needs none. If evidence is disputed, narrate the dispute honestly, with distinct perspectives when relevant. For nonfactual/fictional stories, label the genre and keep scene logic consistent; do not falsely imply documentation.

**Voice and humanism:** Narration is written for *listening*, not silently reading. Use varied sentence length and light, well-placed conversational language. A single vivid detail can do the work of several abstract paragraphs. Use “we” sparingly and “you” only when it genuinely engages the viewer. Personal warmth may be inquisitive, dry, playful or reflective; never one relentless hyped-up sales pitch. Let characters have constraints and decisions, not just pronouncements. Pause to let a consequence land. Nothing about “being engaging” requires fabricated conflict, machine-gun cliffhangers or editing every 1.5 seconds.

**No holiday, religious or superstitious narrative devices.** Never pick a holiday/religious feast (Thanksgiving, Christmas dinners, etc.), a religious ceremony or practice, or a superstition/supernatural claim (omens, luck, ghosts, astrology, curses) as the vivid detail that carries a beat — not as period texture, irony, dramatic contrast, or scene-setting — no matter how well-documented or historically accurate it is. If research surfaces one, leave it out and find a different detail to do that narrative work. Plain factual context that's genuinely unavoidable to the story (e.g., stating that a culture's religion shaped a historical event) can still be stated, but never dramatized as a scene or used as the illustrative device.

**Nothing indecent, gory or distressing.** No subject, line, caption, picture, thumbnail or sound shows, describes or dwells on: nudity, implied included (a bare body or one in underwear/swimwear/a towel only; a bare chest; a moment whose ordinary form is undressed — a shower, bath, changing clothes, sauna, swim, beach in swimwear; anything sexual or suggestive); gore and injury (blood, a wound, a burn, a broken bone, a body or body part, a corpse, a death or violence shown as it happens, an accident's aftermath, a hurt animal or carcass); extreme distress (agony, terror, panic, sobbing, screaming, despair, a breakdown; suicide or self-harm, spoken or shown; cruelty); anyone shown as if dead, unconscious or gravely ill (nobody lies limp or flat with closed/half-closed eyes on a floor, stretcher or sickbed; someone being cared for is awake, eyes open, sitting up where the story allows; a survival pose low on the ground — crawling, bracing, a recovery position — always shows the person clearly alive: head up or turned so the open eyes show, mid-move, never limp or still); children or anyone who looks like one (every person is a clearly adult figure); and what a family audience isn't shown or told — vomit, excrement, a toilet in use, drugs, drunkenness, graphic medical detail (a needle in skin, an operation, a wound being treated), swearing, slurs, crude jokes, or a person humiliated. A subject whose story genuinely *needs* any of this to be told (a gruesome crime, a war's atrocities, an illness told by its symptoms, a disaster told through its victims' suffering) is not a viable subject at all; one where such a fact is incidental is told without it. A hard fact may still be stated plainly: how many people died is a fact and may be said; how a body was found, what an injury looked like, or how someone suffered is not. No line names an intimate part of the body, even as a clinical/first-aid fact — tell it by its other, non-intimate places.

## Originality and copyright integrity

Mined references may contribute functional techniques (e.g., start with the outcome, explain with a scale comparison, slow down on a decision), but never copy their unique shot sequences, artistic identities, voice recordings, specific scripts, distinct jokes or watermarked materials. No attempt to disguise replicated footage. For a borrowed functional device write `source timestamp → audience function → genuinely different new application → adaptation trade-off`. Generate original assets or use sources with clear licenses.

**Internal conversation:** Creative lead may critique concepts internally while drafting. Independent readers come in at three points only: the blind treatment comparison, the cold read of the script, and the final watch review (06, 10), never at every small edit. Do not outsource artistic judgment to a rigid number: the producer owns the final direction, and records why when it overrules a reader.
