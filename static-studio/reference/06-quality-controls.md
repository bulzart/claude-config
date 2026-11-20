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
2. **Before any billable generation** ask: Can this *subject*, not a generic concept, sustain the locked minutes with non-repetitive value? What if the first minute is removed—is there still a story? What would a curious informed viewer learn in each third? Does a source support every consequential claim? Are we honoring thoughtful silence without padding? **Does the script's word count match the pace of the voice that will actually speak it, not just the reference narrators'?** (Once the calibration part is measured, `plan-check`'s `real_forecast_s` must sit inside the export window.) Does every pause and tag come from the story, and is the reason in the review ("Delivery and tags")? Is every content flag answered with a real decision, not a reflex "kept"? Was the treatment chosen and locked before the script, and does every beat carry its direction? Did the cold read happen, is every finding answered, and did a major finding get its second read? Check `direction.json`, `blueprint.json`, `script.json`, `beat-map.json`, the review records, claim ledger and `plan-check`.
3. **During picture/audio assembly** ask: Does each visual do explanatory/emotional work? Are locations, objects and time consistent? Do sound and narration suit the beat? Did the script actually become natural, complete, intelligible speech? Did every tag land as delivery (not read aloud, not a sound effect), and does `narration-measure`'s pause profile sit where the creative strategy meant it to next to the references'? After `retime-shots`, does each still still hold its moment at its real length (the edit plan's `notes`)? Does `delivery.json` show the voice doing what each beat asked (a beat meant to lift that measures flat is rewritten in the parts not yet recorded)? Does `shot-check` pass, and are its repetition warnings deliberate callbacks? Check `audio-check`, all TTS seams, the image argument and frame context rather than relying on a contact sheet alone.
4. **Before publication** ask: Does the final video fulfill its title/thumbnail promise? Is the middle as alive as the opening? Is the final minute satisfying and untruncated? Is it enjoyable even without a running “dramatic” score? Did the final watch review of this exact export find anything still unanswered? Check actual CapCut readback, `timeline-check`, exported MP4 `export-check`, the export's watch sheets (`av-profile --file`), the final review and `release-check`, facts, titles, audio, visual continuity, chapter rhythm and technical end frame.

## Independent reads: three of them, each on record

The writer cannot see their own boring stretches; a reader who knows nothing else can. Three reads, at the three moments where a fresh eye changes the outcome:

| Read | When | The reader gets | It must not get |
|---|---|---|---|
| `treatment` | before `direction-lock` | the treatments' descriptions and three sample moments each, under random labels | the evidence, the risks, your preference |
| `script` | before the first paid narration | the title and the bare script | the plan, the rationale, the writing signals |
| `final` | after export, before release | the export's watch sheets and what each part was meant to feel like | your hopes for it |

`review-packet --kind K` writes the packet with the reader's brief (a viewer's questions, the house rules, the findings format). Spawn ONE new agent whose whole prompt is: read only that file and follow it. Add nothing: no rationale, no plan, no hint of what you hope it finds. `review-record` seals the findings with a hash, so they can't be softened later, and starts the answers file. Answer every finding:

- `revised`: say what changed (for the script, the lines; plan-check checks those lines really changed);
- `kept`: minor findings only, with why;
- `disputed`: with why. A reader can be wrong; say so plainly, with the reason.

A **major** finding (a viewer would likely stop watching, lose the thread or stop trusting the video there) gets a second, fresh read of the revised version by a new agent: round 2 for the script and the final review. After round 2 the director decides, and the reasons stay on record for the release sheet. More reads are always allowed and never required, so nothing loops forever. An approval covers the version it read: a script changed beyond a small trim, a treatment never read or rewritten past 70% of the vocabulary its reader saw, or a different export needs a new read. Refining the chosen treatment does not; it is shown at every plan-check.

What the code enforces: the order, the version each read covers, sealed findings, every finding answered, a revision that really changed something, the second read after a major. What it cannot enforce: that the reader really was fresh, that the answers are honest, that the revision fixed the problem. Those are the director's integrity. Never write or edit a reviewer's findings yourself. No army of reviewers or high-cost agents whose job is to add a number.

## Concrete anti-slop safeguards

- No later frame can depict an object/character in a different place/state without a shown or implied logically valid transition. No unmotivated jumps in distance, time, weather, lighting or scale. When two scenes must be separated, include a readable cut/ellipsis or bridge.
- Whatever form the story takes, its own logic holds from start to finish. What that logic is comes from this video's approach, not from a niche rulebook. Some examples: a step can't rely on a tool or step not yet shown; a hypothetical's first changed assumption stays in force; a reconstructed event keeps its map, chronology and equipment grounded and labels uncertain details as reconstruction; an essay's argument doesn't quietly change its terms.
- No script contains a holiday/religious feast scene (Thanksgiving, Christmas dinners, etc.), a dramatized religious ceremony/practice, or a superstition/supernatural claim (omens, luck, ghosts, astrology, curses) as a narrative or illustrative detail. Reject it on sight during red-team review and replace it with a different detail, even if accurate and sourced. Plain, unavoidable factual statements (e.g., a culture's religion shaped the event) are fine; dramatizing them as a scene is not.
- Every still, the thumbnail and every line are checked against 02's "Nothing indecent, gory or distressing" rule: skin where clothes belong, a bathroom/bed/shower scene, blood or a wound, a corpse, a face in agony, a person lying limp, a survival pose that doesn't read clearly alive, a child-looking face, graphic medical/injury detail, swearing, or an intimate body part named. A hit is a rework reason — rewrite the line/prompt to tell the fact (a number, an outcome) without its graphic form, never add a "no blood"-style negative prompt instead of actually changing the scene.
- Read the finished beat map and shot plan for places a drawn/animated explanation (04) would teach or land something better than the still alone — a quantity, a process, a route, a timeline, something worth circling — and for any already planned, whether it's earning its place (would it be missed if cut?) rather than decorating. Neither a long stretch with nothing drawn nor a drawing on every still is automatically wrong; ask whether the specific moment calls for one and act on the answer, don't default either way.
- Narration and visuals are complementary. A still image isn't compelled to include a logo/label, and a visual-only inference need not be narrated twice.
- A chapter is not complete because the words stop. The promised consequence/answer and a sensible closing beat must be present.
- Paid generation errors are explicit. A partial or financially exhausted TTS recording does **not** earn a shortened completion status.

## Revisions are actionable

Instead of “quality: 7/10”, record `problem → evidence timestamp/line → audience impact → fix → recheck`. For example: “B3 repeats B2's explanation and shows the same three generic paintings → audience learns nothing new for 84 seconds → replace B3 with a sourced decision dilemma and map comparison → validate new script words and image count.” This preserves freedom and provides a measurable improvement. Use precise findings rather than decorative confidence badges.

## Release sheet (plain language)

Write `80-deliverables/video-NN-release.md` with: the locked treatment (and whether the direction was locked late), each later revision of the direction and what followed it (updated, or reapproved with its reason); each read's rounds, its major findings and how they were answered, with any closed by the director's decision named; the `release-check` result for the exported file; locked target and comparable reference IDs; actual script words and calibrated pace; actual audio duration and completeness result; CapCut project and measured timeline duration; actual export path and probed duration or `NOT EXPORTED/NOT VERIFIED`; manual opening/middle/ending checks; outstanding factual/visual/audio issues and resolutions; publishing assets/title/thumbnail; honest release status (`ready`, `blocked`, or `project-only`). Do not assert a creator can guarantee engagement or that a provider API returned results it did not.
