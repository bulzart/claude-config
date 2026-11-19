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

## Deriving the niche's storytelling grammar

Before choosing a premise, extract the narrative engine from the references themselves. Different niches create engagement through fundamentally different mechanisms. Never force one niche's formula onto another's material — and never default to a documentary-style structure simply because it is familiar.

For any niche, study the references and answer these seven questions, writing the results into `20-analysis/niche-synthesis.md` before any creative work begins:

1. **Source of curiosity** — what creates the carrying question? A decision under pressure, a skill gap, a revealed contradiction, a possibility space, an unsolved mystery?
2. **Viewer's most valuable gain** — what do they arrive not knowing, and what matters most about what they leave with? Understanding, capability, wonder, a changed perspective, closure?
3. **Forward motion** — what pulls each section into the next? Revelation, demonstration, escalation, complication, evidence, argument, discovery, or the earned payoff of an earlier planted detail?
4. **Participation moments** — when does the viewer get to infer, predict, feel, or think independently rather than just receive? Where can the story slow down and let them arrive at something themselves?
5. **Visual language** — what visuals are native to this niche and do useful explanatory or emotional work? Maps, diagrams, artifacts, faces, scale comparisons, process shots, before/after contrasts?
6. **Natural emotional arc** — what is the full emotional experience from opening to close? Suspense→resolution, confusion→clarity, problem→skill, speculation→insight, awe→understanding?
7. **Niche-specific failure modes** — what kills engagement specifically in this type of content, based on the weakest moments in the references studied?

The answers become a creative grammar earned from the actual material, not borrowed from a generic template. If the references show no clean grammar — because they mix incompatible niches, durations, or audiences — split them and treat each cohort independently before writing a niche brief.

### Three illustrated applications

The following are worked examples of this process, not prescriptions. If the reference folder contains none of these niches, derive the grammar the same way from what is actually there.

**How-to and problem-solving:** Curiosity comes from a recognizable gap between current state and desired result. Forward motion comes from demonstration, failure modes, and repair. The viewer is mentally applying each step to their own situation. Failure mode: withholding useful steps as a retention trick, or defining terms without solving a real problem.

**History, including military history:** Curiosity comes from imperfect information and consequential decisions. Forward motion comes from revealed constraints, costs of choices, and changing stakes. The viewer reconstructs what was knowable at a given moment. Failure mode: listing events without human stakes, inventing motives or dialogue, anachronistic details that break credibility.

**What-if and counterfactual:** Curiosity comes from a changed assumption and its logical consequences. Forward motion comes from tracing first-order then second-order effects, with uncertainty clearly marked. The viewer tests the logic against their own assumptions. Failure mode: confident pronouncements about imaginary timelines, or second-order effects that ignore known constraints.

## Research that supports creativity without turning into a hard documentary

For factual work, obtain primary and credible secondary sources independent of reference videos. `30-research/video-NN/sources.md` records URL/title, author/issuer, publication or revision date, precise claims supported, counterevidence and verification status. `claims.json` lists consequential dates, numbers, quotes, geographic claims, causal assertions, dangerous instructions and contested conclusions with source IDs and confidence. Cite internally in planning; final narration can flow naturally without reading footnotes aloud. If evidence is disputed, narrate the dispute honestly, with distinct perspectives when relevant. For nonfactual/fictional stories, label the genre and keep scene logic consistent; do not falsely imply documentation.

**Voice and humanism:** Narration is written for *listening*, not silently reading. Use varied sentence length and light, well-placed conversational language. A single vivid detail can do the work of several abstract paragraphs. Use “we” sparingly and “you” only when it genuinely engages the viewer. Personal warmth may be inquisitive, dry, playful or reflective; never one relentless hyped-up sales pitch. Let characters have constraints and decisions, not just pronouncements. Pause to let a consequence land. Nothing about “being engaging” requires fabricated conflict, machine-gun cliffhangers or editing every 1.5 seconds.

## Originality and copyright integrity

Mined references may contribute functional techniques (e.g., start with the outcome, explain with a scale comparison, slow down on a decision), but never copy their unique shot sequences, artistic identities, voice recordings, specific scripts, distinct jokes or watermarked materials. No attempt to disguise replicated footage. For a borrowed functional device write `source timestamp → audience function → genuinely different new application → adaptation trade-off`. Generate original assets or use sources with clear licenses.

**Internal conversation:** Creative lead may critique concepts internally while drafting. A separate cold-read reviewer is useful once before paid production, not mandatory at every small edit. Do not outsource artistic judgment to a rigid number: the producer owns the final direction.
