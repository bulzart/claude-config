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
niche. A technique from an unrelated niche can be exactly what this story needs; its pacing usually is not.

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
you write: `[O]` observed at a timestamp (a measurement included), `[I]` your inference about why it works, `[U]`
unknown. View counts and popularity prove nothing about any single technique.

Write what you learn into the cards (`audiovisual_moments`, `narration_delivery`, `delight`: 01) and the cluster's
creative profile (02): what makes these videos *enjoyable*, not only what they contain, and what remains unexplored.

## 2. From the story approach to an audiovisual treatment

02 chooses the *story*: the subject, the angle, the five approaches and why one wins. The **treatment** decides how
that story sounds and looks, as one idea. Write two or three treatments of the chosen approach that genuinely
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
  something the references don't, and why.
- **risks**: how this treatment could get boring, cute, theatrical or monotonous over twenty minutes.

Then write its **samples**: the opening, a quiet middle and the turning point, each as the narration (50+ words) and
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
   template, and whether voice and picture feel like one idea. `review-record` seals its findings. Answer each one.
2. **Your decision, with reasons.** Which treatment sustains the whole runtime (not the best first 30 seconds),
   fits the subject's truth and the audience's purpose, and is most distinct from the references; and what you take
   from the others. Write it in `decision`.

Then `direction-lock`. The script and the beat directions are written from the locked treatment. Changing course
later is allowed and sometimes right: re-lock with `--revise "what changed and why"`. The lock compares the direction
field by field and says what the change touched (`affects`, and `outdated_now` for what exists):

- The evidence, the alternatives, the reasons and the samples touch nothing: same revision, nothing to redo.
- In the chosen treatment, the narrator touches the beat map, the script and the recorded narration; the writing voice
  the script; structure and pace the beat map, script, shot plan and edit; the visual language the shot plan, style
  bible, stills and edit; the sound the beat map, music and edit; the audiovisual relationship the beat map, shot plan
  and edit; the emotional course the beat map and script. In the strategy, the viewer's experience and facts as
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

Let the treatment evolve with the story: more distance in one beat, more intimacy in the next, a lighter touch after a
heavy one. Consistency means one world, one narrator and one visual logic, not one intensity. Never schedule
humour, suspense or "a reset" at fixed intervals: place them where the material earns them.

## 5. Narration people enjoy listening to

These are craft principles. Each one says when it applies.

- **Write for the ear.** Spoken rhythm, contractions where the narrator would use them, concrete nouns and verbs. Vary
  sentence length because the thought changes, not to a pattern. One idea per sentence when the idea is hard.
- **Give the narrator a point of view and a relationship.** Curious, amused, moved, sceptical, fond: sincerely, where
  the material earns it. A narrator who reacts to what they are telling ("which is a strange thing to do in a
  blizzard") sounds like a person; one who only reports sounds like a reader.
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
  is allowed. Sincerity beats intensity.
- **End when it's over.** Answer the promise, then stop soon. A long tail of statistics after the emotional payoff
  empties the room.
- **Delivery comes from the writing.** In TTS the voice and its settings set the character; the text sets the
  performance: punctuation, sentence length, line breaks, a question, direct address, and now and then a delivery
  tag where the register changes (05's catalogue). After the calibration part, `narration-measure` writes
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

## 7. Refine before spending, then once more at the end

1. **Your own pass.** Read the script aloud in your head with `writing_signals` beside you. Cut for length as a
   boredom pass: what a listener would drift through goes first; the vivid detail stays.
2. **The cold read.** `review-packet --kind script`, then one fresh agent with only that file, then `review-record`.
   Answer every finding: `revised` (with the lines), `kept` (minor only, with why) or `disputed` (with why). A major
   finding gets a fresh round-2 read of the revised script, by a new agent. After round 2 you decide, and the reasons
   stay on record for the release sheet.
3. **The calibration part.** Pace for the length (05), and `delivery.json` for the performance.
4. **The final watch review.** `av-profile --video NN --file export.mp4` makes the export's watch sheets;
   `review-packet --kind final --file` gives a fresh reviewer the sheets and what each part was meant to feel like.
   Fix, re-export, and the new file gets its own read. `release-check` confirms every gate for that exact file.

What the code enforces is the order, the versions and the answers. A passed `release-check` means the process was
followed. Whether the film is a pleasure to watch is the director's and the reviewers' judgement, and the user's.
