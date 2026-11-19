# 06 — Quality: aim for “10/10” by design, not by a fake scalar score

## Editorial standard

The target is a **long-form YouTube film that is enjoyable, creative, coherent, informative and worth finishing**. There is no honest process that guarantees an objective 10/10 rating, viral performance or high retention for every video. Quality comes from repeated diagnosis and revisions against specific audience experiences, while protecting agency and originality. Use this checklist as an adversarial lens, not a rigid scoring algorithm. A genuine intentional quiet moment is not a defect just because it has no new cut.

**Evaluate against the intended experience.** A tutorial should not be measured by how much dramatic tension it generates. A reflective essay should not be faulted for lacking a formal carrying question. A playful explainer should not be penalised for lacking gravitas. The question is always: does the chosen creative approach actually succeed at what it set out to do?

| Dimension | The passing experience | Red flags demanding rework |
|---|---|---|
| Topic and premise | A real, distinctive reason to care about this story at this length | Generic subject, no organizing question, same reference script with different nouns |
| Originality | A fresh perspective/device/evidence contribution | Template sameness, lifted hook/ending/lines, gimmick rather than insight |
| Narrative architecture | Clear promise, growing understanding, consequential middle, earned payoff | Flat list of facts, weak middle, disconnected anecdotes, abrupt conclusion |
| Voice and human reality | Narrator has personality suited to the subject; human or emotional elements appear where natural for the format | Robotic trivia delivery, forced drama, manipulative tragedy, canned inspiration; also a subject calling for warmth executed with clinical detachment |
| Engagement with dignity | Questions worth considering, moments to infer and reflect, genuine surprise | Clickbait, “and then” chains, cliffhangers on a clock, overexplaining every image |
| Factual and logical integrity | Verified claims, labeled hypotheticals, timeline and object continuity | False quotes, confusing probability and fact, anachronistic visuals, logical teleporting |
| Cinematic language | Pictures contribute understanding, consistent visual world, intentional motion/space/sound | Wallpaper montage, repeated generic frames, pointless zooms, unreadable text |
| Craft and reliability | Natural full narration, balanced music, 16:9 edit, correct locked length, actual export checked | Partial ElevenLabs, short Standard, black tail, unplayable clips, wrong format |

## Red-team at four natural production decisions

1. **After reference synthesis** ask: Did we accidentally treat multiple niches/length classes as one? Are conclusions observed or guessed? Do metrics really exist? Are we imitating a viral video's subject instead of understanding its audience experience? Would someone watching only the stills get a very different sense than someone hearing the narration? Fix by revisiting timestamps and audio.
2. **Before any billable generation** ask: Can this *subject*, not a generic concept, sustain the locked minutes with non-repetitive value? What if the first minute is removed—is there still a story? What would a curious informed viewer learn in each third? Does a source support every consequential claim? Are we honoring thoughtful silence without padding? Check `blueprint.json`, `script.json`, `beat-map.json`, claim ledger and `plan-check`.
3. **During picture/audio assembly** ask: Does each visual do explanatory/emotional work? Are locations, objects and time consistent? Do sound and narration suit the beat? Did the script actually become natural, complete, intelligible speech? Check `audio-check`, all TTS seams, the image argument and frame context rather than relying on a contact sheet alone.
4. **Before publication** ask: Does the final video fulfill its title/thumbnail promise? Is the middle as alive as the opening? Is the final minute satisfying and untruncated? Is it enjoyable even without a running “dramatic” score? Check actual CapCut readback, `timeline-check`, exported MP4 `export-check`, facts, titles, audio, visual continuity, chapter rhythm and technical end frame.

A cold reader may be used once before paid generation: give the full script and title, not your self-praise or rationale; ask where the reader lost interest, what they believe the promise was, whether key scenes are credible and what feels formulaic. The writer then chooses what to revise. Repeat a review only to resolve a substantial problem. No army of reviewers or high-cost agents whose job is to add a number.

## Concrete anti-slop safeguards

- No later frame can depict an object/character in a different place/state without a shown or implied logically valid transition. No unmotivated jumps in distance, time, weather, lighting or scale. When two scenes must be separated, include a readable cut/ellipsis or bridge.
- A how-to cannot reference tools/steps not yet introduced; it must solve a useful real problem, not merely define terms.
- A military narrative's map orientation, movement, ranks, equipment and chronology are grounded; uncertain details are labeled as reconstructions.
- No script contains a holiday/religious feast scene (Thanksgiving, Christmas dinners, etc.), a dramatized religious ceremony/practice, or a superstition/supernatural claim (omens, luck, ghosts, astrology, curses) as a narrative or illustrative detail. Reject it on sight during red-team review and replace it with a different detail, even if accurate and sourced. Plain, unavoidable factual statements (e.g., a culture's religion shaped the event) are fine; dramatizing them as a scene is not.
- Every still, the thumbnail and every line are checked against 02's "Nothing indecent, gory or distressing" rule: skin where clothes belong, a bathroom/bed/shower scene, blood or a wound, a corpse, a face in agony, a person lying limp, a survival pose that doesn't read clearly alive, a child-looking face, graphic medical/injury detail, swearing, or an intimate body part named. A hit is a rework reason — rewrite the line/prompt to tell the fact (a number, an outcome) without its graphic form, never add a "no blood"-style negative prompt instead of actually changing the scene.
- A counterfactual's first changed assumption must remain in force; second-order branches may be uncertain but internally consistent.
- Narration and visuals are complementary. A still image isn't compelled to include a logo/label, and a visual-only inference need not be narrated twice.
- A chapter is not complete because the words stop. The promised consequence/answer and a sensible closing beat must be present.
- Paid generation errors are explicit. A partial or financially exhausted TTS recording does **not** earn a shortened completion status.

## Revisions are actionable

Instead of “quality: 7/10”, record `problem → evidence timestamp/line → audience impact → fix → recheck`. For example: “B3 repeats B2's explanation and shows the same three generic paintings → audience learns nothing new for 84 seconds → replace B3 with a sourced decision dilemma and map comparison → validate new script words and image count.” This preserves freedom and provides a measurable improvement. Use precise findings rather than decorative confidence badges.

## Release sheet (plain language)

Write `80-deliverables/video-NN-release.md` with: locked target and comparable reference IDs; actual script words and calibrated pace; actual audio duration and completeness result; CapCut project and measured timeline duration; actual export path and probed duration or `NOT EXPORTED/NOT VERIFIED`; manual opening/middle/ending checks; outstanding factual/visual/audio issues and resolutions; publishing assets/title/thumbnail; honest release status (`ready`, `blocked`, or `project-only`). Do not assert a creator can guarantee engagement or that a provider API returned results it did not.
