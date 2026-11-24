# 10 — Creative direction: one vision for the story, the voice and the picture

The director's job is to decide how *this* story is told, heard and seen, so that a viewer enjoys every minute of it.
Not "what does this niche usually do", but "what would make this subject, for this audience, at this length, a
pleasure to watch". Evidence informs that decision; nothing here is a formula. Every example below is an example,
from one kind of video, not a rule for any niche.

The code around this stage checks only that the process happened: the evidence was measured, real alternatives were
written, an independent reader saw them, the decision was locked before the script, every reviewer finding got an
answer. It cannot tell a good treatment from a dull one. That is your work.

## 1. Read the references as films, not as data

`av-profile --run "RUN" --refs V###,...` measures each reference the same way our own narration and export are
measured later, and writes a **watch sheet** per minute: a frame every 5 seconds with the words spoken under it, and
the minute's numbers on top. Open the sheets in order. Read them the way an editor scrubs a timeline: what is the
viewer seeing *while* they hear this sentence?

Profile the comparable references (the length lock's) and any reference whose craft you want to learn from, in any
niche. A technique from an unrelated niche can be exactly what this story needs; its pacing usually is not. Evidence
that cites a reference outside the locked niche declares it in `evidence.borrowed` (`[{ref, technique, not_taken}]`):
the technique borrowed, and the subject assumptions not taken.

Every reference the direction cites has its content review (01), and no observation sits inside material it
excluded (`direction_cites_excluded_material`), unless the observation is about a useful element inside that
moment and says exactly which (`borrows_only`, a few words: "the cigarette-case exchange, not the prayer"); a
restricted segment lends how it is told, never what it shows. A
reference whose story depends on excluded material (`too_dependent`) still teaches its craft; never its story. When
leaving material out takes away something the story needed, invent the bridge: a different, original way to do that
narrative work, never the same device renamed and never filler.

For each reference, answer with timestamps:

- **The viewer's state, minute by minute.** Curious, amused, tense, moved, oriented, lost, bored? Where does the
  reference itself sag? (It will; popular videos sag too.)
- **What the narration does there.** Tells, teases, jokes, confides, lists, explains, reacts, goes quiet. Who is the
  narrator to the viewer: a guide, a friend, a witness, a storyteller at a fire, a sceptic?
- **What the picture does.** Shows what is said, shows what is *not* said, contradicts it, waits, explains with a
  drawing, lets a face carry it.
- **How picture and voice relate over time.** When does the cut speed up or hold? Does a new picture land on a new
  idea, or every few seconds regardless?
- **Sound.** Where music carries mood, where it drops out, where silence does the work.

The measurements give you the parts you can't perceive directly:

| Measured | What it shows | What it can't tell you |
|---|---|---|
| speaking rate per window, and how it varies | where the narrator speeds up and slows down | whether the speed feels right |
| pitch range and word-to-word pitch movement (semitones) | how much the voice moves; a flat stretch reads low | whether the movement is warm, irritating or forced |
| loudness contrast between words | emphasis | which words should be stressed; a music bed flattens it, so compare a dry voice with a dry voice |
| level in the gaps between words | a music/ambience bed under the voice (high) or silence (very low) | what the music is or does |
| cuts per minute, shot lengths, moving share, same picture again | rhythm, stillness, motion, reuse | whether a shot earns its length |

These are proxies, not taste. A narrator who moves a lot can still be tiring; a narrow one can be intimate. Label what
you write: `[O]` observed at a timestamp (a measurement included), `[I]` your inference about why it works, `[H]` a
hypothesis this film tests (what it should do for the viewer, and how the final watch will show whether it did), `[U]`
unknown. View counts and popularity prove nothing about any single technique. A pattern several references share is
evidence of a convention and of what it can do, not proof that it caused anyone to keep watching: read it in its scene,
for the experience it serves. An idea of ours that no reference uses is welcome: say it is ours, what it should give
the viewer, and judge it in context. The aim is informed originality, not evidence-shaped imitation: the references
show what audiences are used to and what a device can do; this film's choices come from its own story.

Write what you learn into the cards (`audiovisual_moments`, `narration_delivery`, `delight`: 01) and the cluster's
creative profile (02): what makes these videos *enjoyable*, not only what they contain, and what remains unexplored.

## 2. From the story approach to an audiovisual treatment

02 finds the *subject* (topic discovery: `subject`, what it offers this audience, its payoff and the value the film must carry) and chooses the *story*: the angle, the approaches (as many genuinely different ones as the subject allows, at least two, with the range explored in `chosen_approach.exploration`) and why one wins. The strategy's `progression` is how the subject's researched progression is told across the locked length, and each treatment shows in its samples how it makes the researched values land. The **treatment** decides how
that story sounds and looks, as one idea. Write two to four treatments of the chosen approach that genuinely
differ: different narrators, different relationships between picture and word, different emotional temperatures.
Not one treatment at three intensities.

To make the range concrete, three ways one subject could be treated (an illustration, not a menu): a dry, amused
narrator who treats the history as a series of human bad decisions, over bold flat illustrations and quick cuts; a
hushed, close narrator who stays inside one person's evening, over painterly stills that hold long; a curious
explainer who keeps stopping to show how something works, over diagrams that build up on screen.

Each treatment decides:

- **narrator**: who is talking, their relationship to the viewer, their energy range, how much licence they have
  for humour, warmth or emotion, and what they never do.
- **writing_voice**: sentence music, diction, devices it uses sparingly, and devices it avoids.
- **structure_and_pace**: where it accelerates, where it holds, where the long breath comes.
- **visual_language**: the medium, palette logic, composition and motion grammar, recurring motifs, when drawn
  annotations appear.
- **sound**: what music is for in this film, and where silence is.
- **audiovisual_relationship**: when the picture carries what the words leave unsaid, and when the two meet.
- **emotional_course**: how the feeling moves across the whole runtime.
- **evidence_used** and **departures**: which reference observations support it, and where it deliberately does
  something the references don't, and why. Consequential choices (the approach, the treatment, the narrator, the
  picture device, how music and silence are used) name their evidence and reasoning briefly, here or in the review
  files, keeping observation, interpretation and our own idea apart; small choices need no citation. The same reasoning
  carries through every later stage (delivery and tags, pauses, stills, drawings and moves, music, captions, cuts),
  so all of them serve one viewing experience: polish that keeps personality, clarity and surprise, with humour,
  intensity or drama where the material calls for them.
- **risks**: how this treatment could get boring, cute, theatrical or monotonous over twenty minutes.
- **carries_values**: for every payoff value (`value_to_carry` marked `"payoff": true`, 02), how this treatment
  delivers it, in its own terms (`[{value, how}]`). The research shapes the treatment here; its fields are not copied
  into it.

Then write its **samples**: the opening, a quiet middle and the moment where its value lands hardest (its turn
when the subject has one, `turning_point`; otherwise its best demonstration, clearest understanding or biggest
laugh, `strongest_moment`, never a turn invented to fill the slot), each as the narration (50+ words) and
what the viewer sees. The samples are where a treatment proves itself. A treatment that can't make a quiet middle
interesting will sag in the real film; a treatment that only works at full volume will exhaust.

Don't default. A serious subject isn't automatically grave, a light one isn't automatically jokey, and the
documentary voice is one option among many. Ask what the subject's own nature and the audience's purpose call for.
Playfulness can carry a hard subject (never at the expense of the people who suffered in it); calm can carry an
exciting one.

Optional, when it helps and the user allows: free local stills (FLUX) for the sample moments (an image job with
`"purpose": "treatment_preview"`, each item naming its treatment and moment, 04), and a short paid voice
probe (05) for the user to hear a narrator and the agents to measure it. Neither is required; both are evidence, not decisions.

## 3. Choosing without scores

No numbers decide this. Two things do:

1. **A blind comparison by one fresh reader.** `review-packet --kind treatment` writes the treatments' descriptions
   and samples under random labels, without your rationale. Spawn one new agent whose whole prompt is to read that
   file and follow it. It says which it would watch to the end, where each would wear thin, what feels like a
   template, and whether voice and picture feel like one idea. When the user gave an exact topic or story, or the
   niche scope has its `boundary` (02), it is also asked whether each treatment is still a video about what was asked
   (for a niche: still a video of that niche); a "partly" or "no" becomes a finding. `review-record` seals its findings. Answer each one.
2. **Your decision, with reasons.** Which treatment sustains the whole runtime (not the best first 30 seconds),
   fits the subject's truth and the audience's purpose, and is most distinct from the references; and what you take
   from the others. Write it in `decision`, with `carries_payoff`: how the chosen treatment makes the payoff land.

Then `direction-lock`. The script and the beat directions are written from the locked treatment. Changing course
later is allowed and sometimes right: re-lock with `--revise "what changed and why"`. The lock compares the direction
field by field and says what the change touched (`affects`, and `outdated_now` for what exists):

- The evidence, the alternatives, the reasons and the samples touch nothing: same revision, nothing to redo.
- In the chosen treatment, the narrator touches the beat map, the script and the recorded narration; the writing voice
  the script; structure and pace the beat map, script, shot plan and edit; the visual language the shot plan, style
  bible, stills and edit; the sound the beat map, music and edit; the audiovisual relationship the beat map, shot plan
  and edit; the emotional course the beat map and script; how it carries the payoff values (`carries_values`) the beat
  map and script. In the strategy, the viewer's experience and facts as
  experience touch the beat map and script, the progression also the shot plan and edit, the picture's contribution
  the shot plan, style bible and stills, sound and breath the beat map, music and edit. Another approach touches the
  beat map, script, shot plan and edit; another treatment touches everything.
- Each touched piece is updated for real (its own checks then apply: a script edit beyond a trim gets a fresh read) or
  kept on record with `direction-reapprove --artifact NAME --reason "why it still serves the treatment"`, before the
  stage that uses it continues: `plan-check` and paid narration for the script and beat map, the image workers for the
  shot plan and style bible, `retime-shots` and `timeline-check` for the narration, stills, music and edit.
- Refining the chosen treatment needs no new blind read; it is shown at every plan-check. A treatment never read, or
  rewritten so far that under 70% of its vocabulary is what its reader saw, gets its own blind read first.

## 4. Beat direction: the treatment, moment by moment

The treatment is the film's identity; it is not one setting held for twenty minutes. In `beat-map.json`, each beat
says:

- `experience`: what the viewer should feel or understand by the end of it.
- `narration_direction`: register and energy here, and what the words do (explain, tease, confide, react, joke,
  list, land, go quiet).
- `visual_intent`: what the pictures show that the words don't; composition, motion, atmosphere.
- `sound_direction`: music, bed, silence, a single sound with a job.
- `pace`: brisk, unhurried, quickening, a held breath.

**What happens, why it matters, what it pays.** A viewer can follow every event and still not feel why the important
ones matter; they can know why and still not get the reward. These fail separately, and an accurate, coherent script
can fail the second without anyone noticing, least of all a reader who already knows the subject. For the few beats
the film is built around (`key_moment`), decide all three before the script, in `significance`: `matters_because`
(why it matters inside this video, in the viewer's terms: what is at risk or gained, what question it answers, what
setup it pays, what the viewer can now do or see differently), `reward` (what the viewer gets there: an answer,
relief, a laugh, a skill, awe, a feeling), and what they must already know for it to land, its `depends_on` (given
earlier, or withheld on purpose) or `self_contained` (why it needs nothing earlier). Where the subject's payoff (02) `builds_to` one moment or comes
in `several`, the value it delivers (`"payoff": true`) lands at a key moment; a `progressive` payoff is carried by
more than one beat; it is never dropped. Significance is whatever this
viewer came for: a joke's lies in its setup, a tutorial step's in the problem it solves, a reveal's in what it
changes, a quiet scene's in what it lets the viewer feel. Never manufacture danger, conflict or a twist the material
does not have, nor a key moment the video doesn't have (one whose value builds step by step marks none and says how it builds
in the blueprint's `reward_shape`), and never claim more than the evidence: a contested consequence stays contested (`certainty:
"contested"` with `hedge`, the line that keeps it honest). Then plan where the viewer learns what they need: before
the moment, enough to recognise what it means when it comes, without explaining the payoff in advance; a mystery held
on purpose stays held. A verdict afterwards ("historians judged it decisive") confirms a meaning the viewer already felt; it cannot give the moment the weight it lacked when it happened. When a moment is understood but not felt, find the cause before the cure: context missing or
given too late, a consequence never shown, a relation the picture never makes, too much at once, a payoff that
answers no expectation, a weak idea. Fix that cause with the means that fits it (one clearer line, a picture or
drawing that shows the relation, another order, a stronger setup, a different idea); more narration, a louder
delivery, a diagram or a pause is never the default.

Let the treatment evolve with the story: more distance in one beat, more intimacy in the next, a lighter touch after a
heavy one. Consistency means one world, one narrator and one visual logic, not one intensity. Never schedule
humour, suspense or "a reset" at fixed intervals: place them where the material earns them.

A beat's `narration_direction` is where the performance is decided, and it decides it for the writer, not for a tag:
what the viewer should understand or discover here; the narrator's attitude to it (amused, wary, moved, matter-of-fact);
the rhythm of the talk (quick and conversational, slow and plain, one long sentence then a short one); whether the
words alone carry the feeling, which they usually should; whether one delivery tag would genuinely change something
the writing can't; and how the voice sits with the picture and the sound (stepping back while a map explains, carrying
a moment the picture only hints at). More expressive is not better: a calm, thoughtful beat can be the one people
remember, and a restrained line often lands harder than a dramatic one.

The narrator is chosen for the treatment, per video (05, `voice-pick`): the voice that can be this narrator for this
whole film, never one assumed for the subject or the niche. Its stability is chosen for the narrator too (steadier, or
freer in range), never to move the pace.

## 5. Narration people enjoy listening to

These are craft principles. Each one says when it applies.

- **Write for the ear.** Spoken rhythm, contractions where the narrator would use them, concrete nouns and verbs. Vary
  sentence length because the thought changes, not to a pattern. One idea per sentence when the idea is hard.
- **Give the narrator a point of view and a relationship.** Curious, amused, moved, sceptical, fond: sincerely, where
  the material earns it. A narrator who reacts to what they are telling ("which is a strange thing to do in a
  blizzard") sounds like a person; one who only reports sounds like a reader.
- **The voice performs, and the script plans it.** ElevenLabs v4's delivery and pause cues are part of every
  narration where a moment calls for them (05): a line that settles, a beat before a reveal, restrained humour, a
  hushed passage. Never a quota, never decoration, and never a cover for a sentence that is unclear: rewrite that.
- **Context just in time.** Give the viewer what they need for the next moment, when they need it. A recap before the
  story begins is usually the first exit. If the title promises an experience, start the experience.
- **Facts become experience.** Tie a number to a body, a decision, a comparison or a picture. Say each number once,
  in its most meaningful form. When three numbers pile up, keep the one that matters and put the rest on a drawn
  overlay (04).
- **Humour and warmth come from specifics:** understatement, contrast, the absurd true detail, the human reaction.
  Never at the expense of victims, never in grief. How much is the treatment's call, never a quota. A subject with no
  room for jokes still has room for warmth and wit.
- **Watch for tics.** A device used once is style; used eight times, the listener hears the template. `plan-check`'s
  `writing_signals` lists repeated phrases, sentence shapes used again and again, runs of fragments, very long
  sentences, number-dense lines and words echoing in neighbouring lines. A refrain can be deliberate; know which yours
  are.
- **No theatre.** No manufactured stakes, constant drama or rhetorical questions that aren't real questions. Quiet
  is allowed. Sincerity beats intensity. What a listener hears as a reading, not a storyteller: facts recited in an
  encyclopaedia's order, every sentence performed like a trailer, forced excitement, one intensity for twenty minutes,
  a dramatic pause after every reveal, questions in a row, the same sentence shape again, emphasis on details that
  don't matter, an artificial cliffhanger at every turn. `writing_signals` counts some of it (questions in a row,
  exclamations, words in capitals, how often the text directs the voice); the cold read hears the rest.
- **End when it's over.** Answer the promise, then stop soon. A long tail of statistics after the emotional payoff
  empties the room. The same goes for the last silence: it lasts as long as the final picture and the sound need to
  resolve, not a fixed number of seconds of nothing.
- **Silence is a tool, not an ingredient.** The narrator's own rhythm comes first: the breath and the short gap after
  each line already give most moments their time. Hold a silence only where the viewer needs time the voice does not
  give, and judge it in its scene, not by its sentence:
  - *the story*: does the viewer need a moment to take in a revelation, anticipate what comes, feel a consequence, or
    follow a turn? A line that sounds important is not, by itself, a reason.
  - *the picture*: what is on screen while it lasts, and does it keep giving (a reveal still building, a map line being
    drawn, a face, a resolved final composition)? A still frame can carry a pause; pointless motion added to disguise
    one cannot. The picture can also go on revealing under the next line, which often serves better than stopping.
  - *the sound*: the voice stopping does not have to stop everything; a bed that goes on, drops out, or gives way to one
    story-world sound (wind over an empty field) is a choice. Music or effects never cover dead air.
  - *the rhythm around it*: does it make the line before land and the next one more wanted, or does it delay
    information, break momentum, slow a deadpan joke into waiting for a laugh, or stall the opening hook?
  The same length can be right in one scene and dead air in another. No quota, no escalation, no length per kind of
  moment, never runtime. The voice's usual gaps are the baseline to judge from, not a ceiling. A reference's silences
  are evidence to read in their scenes (what the viewer was processing, what the picture and the sound did), never
  lengths to copy. A length written in the script is a proposal: it is decided
  on the recorded voice (its real gap there, a listening preview) and again with the picture (05, `holds`,
  `hold-decide`).
- **The way into a silence and out of it is part of the performance.** A silence reads as meant when the voice lands
  the line before it (it falls and settles, often into a soft or creaky end) and starts the next one fresh (a reset,
  a breath that leads in). After a line left hanging, a long silence sounds like the voice stopped or is waiting for a
  laugh. Choose what the moment needs, not a treatment: a deadpan joke usually wants the line said flat and a short,
  clean stop, never a softened tail; a hard reveal can cut straight to silence; a reflective beat can let the music
  hold the room while the voice rests; an ending can let the last image and the bed resolve together. Most transitions
  need nothing at all beyond the right length. When the voice does not land a line the silence needs landed: in parts
  not yet recorded, write the ending to land (a full stop, a short last clause, a tag only where the writing cannot do
  it); in recorded parts, a shorter silence, the picture or the bed usually serves before any paid re-recording. The
  edit never fades a syllable, a release or a breath, and never adds sound to hide an empty moment (05).
- **Delivery comes from the writing and its cues.** In TTS the voice and its settings set the character; the text
  sets the performance: punctuation, sentence length, line breaks, a question, direct address, and a delivery or
  pause cue wherever it gets a moment directly (05's catalogue; its scope stated, 05). Plan each important moment
  as a performance: how the line lands, the silence and what it holds, how the next line starts again. After the calibration part, `narration-measure` writes
  `delivery.json`: pitch range and movement, loudness contrast and rate per beat, next to what each beat asked for and
  to the references' numbers. A beat asked to lift that measures flat gets rewritten in the parts not yet recorded:
  shorter sentences, a turn of phrase, a question, a tag. The audio is never edited to fake it.

## 6. Picture and narration as one

- **The picture carries what the words don't:** place, scale, consequence, a face's reaction, the thing just out of
  frame. Echo the words only when they need anchoring.
- **Rhythm is a choice.** Hold a picture while it keeps giving; cut when it has given what it had. Read the references'
  shot lengths and moving share, then choose this film's rhythm for this story, beat by beat.
- **Repetition:** a returning image is a callback when intended and wallpaper when not. `shot-check` lists prompts
  that are nearly the same and long runs of one composition; the export's watch sheet shows the same picture coming
  back.
- **Simplicity before spectacle.** One clear image with a drawn annotation often teaches more than a spectacular
  one. A beautiful picture that adds nothing to the moment is decoration.
- **Every shot says its job** (`new_thing` in the shot plan): what the viewer learns or feels from the picture that
  the narration didn't give them.
- **Show the relationship.** When the words state a cause, a comparison, a route or a plan, the picture shows how the
  parts connect, revealed in the order the viewer needs it (04). Plan the drawing with the beat, not after the edit.
- **One thing to read at a time.** Captions, drawn labels and words inside the picture compete for the same eyes. Give
  a label the time and the size to be read, keep it out of the caption band, and let a dense moment be carried by
  the picture or the words, not both at once (timeline-check lists small, short or covered words).

## 7. Refine before spending, then once more at the end

1. **Your own pass.** Read the script aloud in your head with `writing_signals` beside you. Cut for length as a
   boredom pass: what a listener would drift through goes first; the vivid detail stays.
2. **The cold read.** `review-packet --kind script`, then one fresh agent with only that file, then `review-record`.
   Answer every finding: `revised` (with the lines), `kept` (minor only, with why) or `disputed` (with why). Then
   reconcile each key moment in the answers file (`reconcile`, 06): what it was planned to mean beside what the reader
   took from it, `same`, `different_but_valid` or `gap`; a gap counts as a major finding. A major
   finding gets a fresh round-2 read of the revised script, by a new agent. After round 2 you decide, and the reasons
   stay on record for the release sheet.
3. **The narrator, then the calibration part.** `voice-pick` for this treatment (05). When the voice, its stability, the
   tags or a name are in doubt, a short `narration-trial` (approved and priced first) compares them one change at a
   time and gives the user clips to hear. Then the calibration part: pace for the length (05), every line heard, and
   `delivery.json` for the performance.
4. **The final watch review.** `av-profile --video NN --file export.mp4` makes the export's watch sheets;
   `review-packet --kind final --file` gives a fresh reviewer the sheets, the parts by time only and the held
   silences; what each part is meant to do stays with you, to compare with its account when you answer. Its key
   moments are reconciled the same way. Fix, re-export, and the new file gets its own read. `release-check` confirms every gate for that exact file.

What the code enforces is the order, the versions and the answers. A passed `release-check` means the process was
followed. Whether the film is a pleasure to watch is the director's and the reviewers' judgement, and the user's.
