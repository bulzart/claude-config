# 02 — Editorial invention engine: long-form YouTube with intelligence and personality

## What exceptional content means here

Do not write a ten-minute Wikipedia paraphrase, fake-suspense documentary, or robotic succession of image prompts. Aim for a piece that rewards the viewer's *time*, not only their click: a satisfying question, a surprising but earned path to understanding, emotional and human texture, a credible worldview, visual thought, and an ending that recontextualizes the beginning. Genuine interest and clarity are not enemies of entertainment. Different niches warrant different densities, levels of humor, and narrator distance. Be inviting without sounding like a school assignment, and expressive without manufacturing drama.

The user chooses a **niche**, not a forced title or story form. The writer has creative discretion over a *new* angle inside it. For every video brainstorm **five substantively different** options before choosing: contrast perspective (insider vs bystander), scale (one decision vs whole system), structure (event chronology vs consequence-first), voice (practical guide vs intimate inquiry), and visualization (diagram-led vs artifact-led). At least one candidate should challenge the most obvious reference formula. Reject near-identical variants where only a person/date/location changed. Rank **not by mathematical virality scores** but by: genuine open question, richness of evidence, ability to sustain locked duration, human consequence, visual potential, unique viewpoint, feasibility and earned conclusion.

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

## Three example niches — different dramaturgy, never a fixed formula

### How-to and scenario/problem-solving

Give useful progress early. Hook with a clearly recognizable failure or desired result; demonstrate the mechanism, show a common wrong approach and its consequence, walk through a realistic repair or technique, then test edge cases. Use real-world constraints and on-screen comparative diagrams; don't withhold all steps as a retention trick. An 8–15-minute lesson needs multiple practical examples, failure modes and a meaningful outcome, not repetitive motivational narration. Where an instruction has a safety or expertise boundary, state it promptly.

Possible route: concrete frustrated moment → diagnosis → smallest successful fix → why it works → tricky case → what to do next. Other routes, such as a live experiment or suspenseful troubleshooting, are equally valid when better for the topic.

### History, including military history

The most engaging question may be: what did the people involved actually know, what decision was available, what did that decision cost, and what changed because of it? Let maps, terrain, distance, material conditions, chronology, logistics, political context and imperfect information create tension. Use identifiable human stakes but don't invent diary lines, dialogue, motives, casualty counts or impossible eyewitness perspectives. Separate documented actions, disputed interpretations and creative reconstructed illustration. Protect against anachronistic clothing, wrong insignia, misdated equipment and impossible travel.

The format can be an object-led investigation, battle/decision reconstruction, a misunderstood logistical problem, the path of one ordinary witness, an unexpected turning point, or a comparison of rival interpretations. History should feel alive without becoming fiction sold as fact. Avoid glamorizing harm; choose appropriate sensitivity for a general audience.

### What-if and counterfactual explainers

State the **single changed assumption** clearly. Set real-world baseline and known constraints. Trace first-order effects, then second-order consequences, feedback loops and at least one plausible competing branch. Give the viewer a framework to think with, not confident pronouncements about imaginary timelines. Show a branching timeline and visually mark the point where historical fact ends and the hypothetical begins. Use humor, thought experiments and everyday analogies if they illuminate. Land on the real lesson learned by exploring the counterfactual.

An alternative may be to begin with a startling predicted consequence and work backwards through assumptions, or to stage an argument between competing models with explicit uncertainties. The key is testable logic, not loud speculations.

### Other niches

Infer their storytelling grammar from *relevant* references rather than forcing the above three outlines on them. A personal story, science explainer, reflective essay or invented fable may succeed through voice, structure and insight more than dense graphics. Choose what fits audience, promise, level of evidence and duration.

## Research that supports creativity without turning into a hard documentary

For factual work, obtain primary and credible secondary sources independent of reference videos. `30-research/video-NN/sources.md` records URL/title, author/issuer, publication or revision date, precise claims supported, counterevidence and verification status. `claims.json` lists consequential dates, numbers, quotes, geographic claims, causal assertions, dangerous instructions and contested conclusions with source IDs and confidence. Cite internally in planning; final narration can flow naturally without reading footnotes aloud. If evidence is disputed, narrate the dispute honestly, with distinct perspectives when relevant. For nonfactual/fictional stories, label the genre and keep scene logic consistent; do not falsely imply documentation.

**Voice and humanism:** Narration is written for *listening*, not silently reading. Use varied sentence length and light, well-placed conversational language. A single vivid detail can do the work of several abstract paragraphs. Use “we” sparingly and “you” only when it genuinely engages the viewer. Personal warmth may be inquisitive, dry, playful or reflective; never one relentless hyped-up sales pitch. Let characters have constraints and decisions, not just pronouncements. Pause to let a consequence land. Nothing about “being engaging” requires fabricated conflict, machine-gun cliffhangers or editing every 1.5 seconds.

## Originality and copyright integrity

Mined references may contribute functional techniques (e.g., start with the outcome, explain with a scale comparison, slow down on a decision), but never copy their unique shot sequences, artistic identities, voice recordings, specific scripts, distinct jokes or watermarked materials. No attempt to disguise replicated footage. For a borrowed functional device write `source timestamp → audience function → genuinely different new application → adaptation trade-off`. Generate original assets or use sources with clear licenses.

**Internal conversation:** Creative lead may critique concepts internally while drafting. A separate cold-read reviewer is useful once before paid production, not mandatory at every small edit. Do not outsource artistic judgment to a rigid number: the producer owns the final direction.
