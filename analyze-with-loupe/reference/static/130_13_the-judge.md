## 13 The judge (A6s, S2, S3, S4)

The user, 2026-11-08: "make a smart judge system who can do things on its own who decides what to do when this happens or similar cases,
who is given enough brief and information and it evaluates the situation and decides way before generation happens and the generation
is done whether image, speech or music is done so we just make the most quality outputs and not unexpected things turn out after the
work is done ... before we execute we also judge the potential outcomes before we continue to generate, all without drifting from the
mined and collected data patterns and analysis from the references"; "the problem was with this word 'We didn't aim for 209.', because
every step should be taken carefully and thoroghfully, and nothing should turn out as unexpected"; and "no need to ask me for my call".

What it fixes (2026-11-08, video 03 of the run of 2026-11-06): the narration's speaking pace landed at the top of its band (208.5)
because the pace step stopped anywhere inside the band, and the script carried 33 long pauses per 10 minutes against the family's 6.3:
nobody had chosen either number, and nobody had forecast them.

**The rule.** Every value an output will carry is chosen on purpose, from the references' measured numbers, before it is generated; each
choice is written down with the numbers it rests on and the result it should give; after the generation the measured result is read
against that forecast, and a miss is explained and corrected (or recorded with its reason). Nothing lands somewhere by accident.

**Who.** An Opus agent with the brief below (`subagent_type: general-purpose`, `model: "opus"`), spawned by the main session at each
checkpoint of each video; in a session without agents, the main session takes the role itself with the same brief. It decides on its
own and never asks the user (the user, 2026-10-28 and 2026-11-08); it never generates an image, a line or a bed, never changes the
run's locks (the niche, the style lock, the narrator), the user's start choices (formats, images' source, QC fixes, CapCut plan) or
the memory guard, and never leaves the references' data: a target is a measured number of the set or of the video's family (the
family's median unless the data gives a reason for another of its numbers, written with that reason), never a stock value or a taste.

**Its information.** `20-analysis/static-spec.md` and the cards (the craft), `T static profile --run RUN --refs <the family>` (the
family's numbers: the pace by the fair measure, the pauses, the seconds a still), the video's plan files (`40-briefs/video-NN-*`), `T
static forecast --run RUN --video NN` (what the plan will give: below), the run's history (`60-outputs/video-*/images*.json` notes, the
briefs), and the PC's model-memory record.

**The forecast** (`T static forecast --run RUN --video NN [--part narration|images|music] [--from K --to K]`, facts only, written to
`40-briefs/video-NN-forecast.json`):
- *Narration*: the plan's words, lines and planned pauses (how many, how long, how many of `LONG_PAUSE_S` 0.8 s or more), the strong lines
  (their share and any two in a row), the target point and bands, the family's numbers, the voice's fit (learned from its last narration:
  its words a minute while articulating at tempo 1, the silence it adds at a join, its own pauses inside lines; `T tts fit` learns it
  again from a made narration), and from them the speed factor the point needs (inside the clean range or not), the pause between lines
  the overall point needs (reachable or not, and by how many seconds not), and the predicted pace and pause pattern against the family's
  (pauses a minute, median, 90th percentile, long ones per 10 minutes, their share), and the length against the target.
- *Images*: per image the facts that tend to spoil a still on this PC: things that carry writing in the scene (a sign, a screen, a chart,
  a report, a map, a thermometer …) with no exact words planned, digits in the scene, words of §11, words that ask for panels or a split,
  a missing style lock, clean-picture or one-scene sentence, overlay words, a label on a moving image, missing anchors, three or more
  references, the span against the family's seconds a still; the references' memory against the free memory now; FLUX 3 Klein's seconds
  an image on this run and the hours for the stretch; and this run's image history (what the upsampler added, what was flagged).
- *Bed*: the duration, the sections against what they must add up to, words in the captions that ask for vocals or §11 (a word only
  negated, "no vocals", is not counted), and the music model's memory record (the highest peak, the guard's stops) against the free
  commit memory now and the guard's floor.

**The fair measure of pace** (§6 "The pace"): words a minute overall (first to last word) and while articulating (the same words over the
span with every pause of 0.25 s or more taken out, `wpm_articulation`), from the words' times. The older reading (words over the
speech-to-text segments, `wpm_speech`) counts pauses differently in a natural recording (its segments run long and hold most of its
pauses) and in a joined narration (its segments end at the lines): 2026-11-08, video 03 read 208.5 by segments and 213.8 by the fair
measure against a family median of 211.9 by the same fair measure. The judge sets and judges the speaking pace by `wpm_articulation`.
Two cautions from the same video's re-join: the pace is measured on the narration as delivered (the voice chain and the loudness passes
applied; the raw join read 212.7 where the delivered file read 207.4), so the loop and `T narration-words` read the same file; and a
join heard near the 0.25 s mark (a default of 0.215 s plus the voice's breath) is counted as a pause in one reading and as speech in the
next, so the judge keeps every default join clearly on one side: `pace.pause_floor_s` (§4, §6) high enough that a default join is
heard as a pause, and a short `pause_after` of its own on a line that runs on into the next.

**The checkpoints** (each writes its decisions into `40-briefs/video-NN-judge.md`: the decision, the numbers it rests on, the
predicted result; and afterwards the measured result against it):
1. **J1, before any generation** (A6s step 9, after the scripts, image plans and bed are written; `awl-static-plan`): reads the
   forecast of every part and decides:
   - the narration's `pace` (§4): `refs` (the family), the bands by the fair measure, the `target` point (the family's median of
     `wpm_articulation` and of `wpm_overall`, unless a reason in the data), the `tolerance`;
   - the pauses: the long pauses the family holds (its `long_pauses_per_10min` times the video's minutes, at the strongest turns:
     the reveals, the chapter starts) as `pause_after`, a short `pause_after` where a line runs on into the next, every other join the
     default the pace loop sets, kept over `pace.pause_floor_s` so each is heard clearly as a pause; the forecast must then show the
     point reachable and the predicted pause pattern near the family's (a planned pause the family does not hold is cut);
   - the strong lines (at most one in five, never two in a row, §4), the length against the family's (§4);
   - every image prompt the forecast marks: a thing that would carry writing gets its exact words when the story needs them (a label
     is CapCut text, §5) or is described as plain and blank ("a blank white screen", "a chart of plain coloured bars with no writing");
     digits leave the scene words; a split word becomes one scene; a §11 word becomes a secular description; a missing sentence is put
     back; a still whose references the memory cannot hold rides with a cast sheet (§5);
   - the bed: its caption and sections fixed where the forecast marks them; when it can run (the memory forecast: a negative headroom
     means the guard would stop it, so it is run when the images are done and nothing else holds memory, read again right before).
   It then runs the forecast again and writes the predicted numbers it expects.
2. **J2, after the narration** (S2, before the images; `awl-static-sound`): the measured pace and pauses (`T tts say`'s `pace`, then `T
   narration-words`) against J1's forecast and point: on the point within the tolerance, the pause pattern near the family's, the
   length; the image spans against the seconds a still. A miss is explained from the numbers (the fit, the planned pauses) and corrected
   with what costs nothing (`T tts say --rejoin` after a change of the plan's pauses or point: no line is made again; spans by moving
   `from_line`); a line made again follows the run's QC fixes. The fit learned by the narration is the next video's forecast.
3. **J3, between image stretches** (S3; the main session spawns the judge when an image agent reports, before the next is spawned):
   the stretch's report and flags and the stills it names, viewed; what went wrong is traced to its prompt words (the caption the
   upsampler wrote is in each attempt) and the next stretches' prompts are changed so it does not happen again (prevention costs no
   generation); a re-draw of a made still follows the run's QC fixes.
4. **J4, right before the bed** (S2's bed step, when the images are done): the memory forecast again; run, or wait for the headroom
   (the guard is never changed and no program of the user's is closed), or go on without a bed when it cannot fit (never a blocker);
   after it: `T music measure` against the bed's plan.
5. **J5, before the edit** (S4; the edit agent's first step reads `video-NN-judge.md`): the labels, moves and joins the plan carries
   against the spec's numbers (the push-ins as many as the family's moving shots allow, the dips at the chapters), decided before the
   project is built.

**Judge prompt** (the main session fills the `<…>`):

```
You are the judge of a /analyze-with-loupe Static run (narrated still-picture videos), checkpoint <J1|J2|J3|J4|J5> for video <NN>.
Read first: C:/Users/Bulzart/.claude/analyze-with-loupe/reference/static/130_13_the-judge.md (your brief: follow it exactly), then
<RUN>/20-analysis/static-spec.md and only the sections of static §4, §5 or §6 your checkpoint touches.
Run: <RUN>. Toolkit T: "C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe" "C:/Users/Bulzart/.claude/analyze-with-loupe/scripts/awl.py"
(through PowerShell). The video's family: <family name> (<refs>); the run's QC fixes: <ask|auto|off>.
<what happened since the last checkpoint: the agent's report, the measured numbers, or "nothing generated yet">
Do: `T static profile --run <RUN> --refs <refs>` and `T static forecast --run <RUN> --video <NN> [--part … --from … --to …]`; read them
with the plan files; decide every change yourself (never ask anyone), edit only the plan files your checkpoint owns (J1: the narration
JSON's pace and pauses, the image plan's prompts and characters, music.json's track; J2: the narration JSON's pauses and point; J3: the
image prompts of the stretches not made yet; J4: music.json's track; J5: the image plan's motion, labels and joins), run the forecast
again, and append your decisions to <RUN>/40-briefs/video-<NN>-judge.md (each: what, why with the numbers, the predicted result).
Never generate anything, never change a lock, a start choice or the memory guard, never leave the references' numbers. Heavy work (a
model, a test suite) never runs while FLUX 3 Klein makes images.
Final message: one line per decision and the forecast numbers you expect.
```
