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
the memory guard, and never leaves the references' data: a target is a measured number of the references, mostly of the run's
niche's references within the video's family, the family's and the set's numbers beside it (§1 "The run's niche within the set"; their
median unless the data gives a reason for another of their numbers, written with that reason; when the niche's references are too few
to carry a number alone, the judge weighs it with the family's and writes how), never a stock value or a taste.

**Its information.** `20-analysis/static-spec.md` and the cards (the craft), `T static profile --run RUN --refs <the family>` and
`--refs <the niche's references in it>` (their numbers: the pace by the fair measure, the pauses, the seconds a still), the video's plan files (`40-briefs/video-NN-*`), `T
static forecast --run RUN --video NN` (what the plan will give: below), the run's history (`60-outputs/video-*/images*.json` notes, the
briefs), and the PC's model-memory record.

**The forecast** (`T static forecast --run RUN --video NN [--part narration|images|music] [--from K --to K]`, facts only, written to
`40-briefs/video-NN-forecast.json`):
- *Narration*: the plan's words, lines and characters, the lines with their own delivery and with pause tags, the lines that name an
  intimate part of the body (`intimate_body_words`, §11b), the passages and the
  characters they send (their tags included) against the account's characters left (read when the key is set: which line whole passages
  reach), the target point and bands, the family's numbers, the levers (the voice, the narration's delivery, the settings) and the
  voice's point measured for them (`same`, or the voice's latest as `nearest`: a probe's or a made narration's; `T tts fit` learns it
  again): its words a minute while articulating and overall, over the delivered audio (`wpm_delivered`: the length a narration of these
  words will have), its pauses; and from them the predicted pace, length and pause pattern against the point, the target length and the
  family's numbers. No speed and no pause between lines is calculated: Eleven v4 has no speed, and nothing is placed after it (§6).
- *Images*: per image the facts that tend to spoil a still on this PC: things that carry writing in the scene (a sign, a screen, a chart,
  a report, a map, a thermometer …) with no exact words planned, digits in the scene, words of §11 and of §11b (a shower, a bath,
  blood, a wound, a scream: `nudity_gore_or_distress_words`), words that ask for panels or a split,
  a missing style lock, clean-picture or one-scene sentence, overlay words, a label on a moving image, missing anchors, three or more
  references, the span against the family's seconds a still; the references' memory against the free memory now; FLUX 3 Klein's seconds
  an image on this run and the hours for the stretch; and this run's image history (what the upsampler added, what was flagged).
- *Bed*: the duration, the sections against what they must add up to, words in the captions that ask for vocals, §11 or §11b (a word only
  negated, "no vocals", is not counted), and the music model's memory record (the highest peak, the guard's stops) against the free
  commit memory now and the guard's floor.

**Memory is a fact, never a gate** (the user, 2026-11-07, after a lighter voice model was used because the free memory looked short:
"we've already generated prior voices such as the first one used in the video02 with the same memory we have now"): a forecast's
headroom (the free commit against a job's measured peak plus the guard's floor) says when a job is likeliest to fit (in a gap, with
nothing else running), never whether it is tried, and never turns a job into another engine (the two levers at the end of this
paragraph are the only lighter settings, and the user's). Every still and bed is tried (the narration runs at ElevenLabs, not on this PC);
only a real guard stop (its "STOPPED the app to protect Windows" line) shows it does not fit. Then the job waits until the free
commit is at least 1 GB above where the stopped attempt started (the user is told the guard's line; nothing of theirs is closed and
the guard is never changed), or, for a bed, goes on without, named. 2026-11-08, video 03: the bed tried at 15.4 GB free was stopped
at 2.3 GB with ACE-Step at 13.07 GB; a still tried at 13.53 GB was stopped, and stills passed from 15.3 GB. 2026-11-09 (§9 "What a
job needs"): ACE-Step's own loading held its model twice; the low-commit loading needs about 10.7 GB, so that bed fits from about
13.6 GB free; and the free commit at rest falls after a restart (the page file shrinks back), which is when a job that ran before is
stopped: the forecast's headroom is read against the free commit now, never against a past day's. Two levers lower a job's need
without another engine: FLUX 3 Klein's `--reserve-vram` (the same pixels, slower, §5; the agent's call from the free commit now) and
ACE-Step's own int8 quantization of the music model (`T music make --quantization int8_weight_only`, §6), only after the guard
stopped a full-precision try of that bed (the user, 2026-11-09, yes to "always try full precision first, and use int8 only after the
guard stops it"), never from the forecast alone.

**The fair measure of pace** (§6 "The pace"): words a minute overall (first to last word) and while articulating (the same words over the
span with every pause of 0.25 s or more taken out, `wpm_articulation`), from the words' times. The older reading (words over the
speech-to-text segments, `wpm_speech`) counts pauses differently in a natural recording (its segments run long and hold most of its
pauses) and in a joined narration (its segments end at the lines): 2026-11-08, video 03 read 208.5 by segments and 213.8 by the fair
measure against a family median of 211.9 by the same fair measure. The judge sets and judges the speaking pace by `wpm_articulation`.
The pace is read on the narration as delivered, the file that plays (2026-11-08, the same video: its raw join read 212.7 where the
processed file read 207.4; since 2026-11-09 nothing is done to the delivered audio, so the two are one file).

**The checkpoints** (each writes its decisions into `40-briefs/video-NN-judge.md`: the decision, the numbers it rests on, the
predicted result; and afterwards the measured result against it):
1. **J1, before any generation** (A6s step 9, after the scripts, image plans and bed are written; `awl-static-plan`): reads the
   forecast of every part and decides:
   - the narration's `pace` (§4): `refs` (the niche's references within the family, else the family), the family's bands by the fair
     measure, the `target` point (the niche's references' median of `wpm_articulation` and of `wpm_overall`, the family's beside it,
     unless a reason in the data), the `tolerance`;
   - the levers that reach the point (§6 "The pace"): the narration's `delivery` (pace and register tags), the `voice_settings`, the
     words (sentence length and punctuation), each measured first on a probe (passage 1 exactly as `say` will send it; another lever set
     is another probe): the judge names the lever sets, the main session runs `T tts probe` for each (billed; the judge never generates)
     and continues the judge with the measures; as few probes as the characters left allow (the forecast's `credits`), the narrator never
     changed (a lock);
   - the pauses: the long pauses the niche's references hold, the family's beside them (their `long_pauses_per_10min` times the
     video's minutes, at the strongest turns:
     the reveals, the chapter starts) asked as `tags_after` ("[pause]": 0.76 s with George, 2026-11-09; "[long pause]" ran 1.6-2.6 s,
     over the family's 0.92 s, §6 "what the levers did") or punctuation, every other rest the voice's own, the
     probe's pause pattern read against the family's (a pause the family does not hold is not asked);
   - the strong lines (their own `delivery` tags; at most one in five, never two in a row, §4), the length against the family's (§4);
   - every line the forecast marks with `intimate_body_words` (§11b): told by its other places ("her head, her neck and under her
     arms");
   - every image prompt the forecast marks: a thing that would carry writing gets its exact words when the story needs them (a label
     is CapCut text, §5) or is described as plain and blank ("a blank white screen", "a chart of plain coloured bars with no writing");
     digits leave the scene words; a split word becomes one scene; a §11 word becomes a secular description; a §11b word becomes the
     dressed or calm moment (every person's clothes named top to bottom; the care, never the harm; a lying-down pose that is the
     survival fact stays, the person clearly alive in it: head up or turned, eyes open, moving); a missing sentence is put
     back; a still whose references the memory cannot hold rides with a cast sheet (§5);
   - the bed: its caption and sections fixed where the forecast marks them; when it runs (when the images are done, or in a gap
     between image stretches once the narration is final, with nothing else holding memory; the memory forecast read again right
     before, a fact and never a gate: J4).
   It then runs the forecast again and writes the predicted numbers it expects.
2. **J2, after the narration** (S2, before the images; `awl-static-sound`): the measured pace and pauses (`T tts say`'s `pace`, then `T
   narration-words`) against J1's forecast and point: on the point within the tolerance, the pause pattern near the family's, the
   length, and a partial narration (the characters ran out) named; the image spans against the seconds a still. A miss is explained from
   the numbers (the point measured, the levers) and changed through the request first: another delivery tag, setting or wording and the
   passages made again (billed, by the run's QC fixes). What those cannot reach (the voice is locked; the tags and pause tags tried
   and measured) is kept as delivered and recorded with its reason, and J2 writes the speed-up that would close it (the tempo that
   brings the speaking measure to the point, at most `config static.narration.tempo_max`, 1.05) for the wrap-up to offer: it is made
   only on the user's yes after they have looked at the delivered project (§6; the user, 2026-11-09: "only speedup on their
   permission never else"), then `T narration-words`, `T slideshow plan` and the project again. Nothing else is ever done to the delivered audio but the level rule (§6: one gain only when the
   narration sits outside the references' loudness). Spans are moved by `from_line` (free). The point learned by the narration is the
   next video's forecast.
3. **J3, between image stretches** (S3; the main session spawns the judge when an image agent reports, before the next is spawned):
   the stretch's report and flags and the stills it names, viewed; what went wrong is traced to its prompt words (the caption the
   upsampler wrote is in each attempt) and the next stretches' prompts are changed so it does not happen again (prevention costs no
   generation); a re-draw of a made still follows the run's QC fixes.
4. **J4, right before the bed** (S2's bed step, when the images are done or in a gap between image stretches): the memory forecast
   again, recorded as a fact and never a gate ("Memory is a fact" above), so the bed is tried. Only a real guard stop shows it does
   not fit: the user is told the guard's line (a closed program frees the memory; the guard is never changed and nothing of the
   user's is closed), the bed is tried once in ACE-Step's int8 (`--quantization int8_weight_only`, §6: only after that stop), once
   more before the edit when that is stopped too, and still stopped the video goes on without a bed, named (never a
   blocker); after it: `T music measure` against the bed's plan.
5. **J5, before the edit** (S4; the edit agent's first step reads `video-NN-judge.md`): the labels, moves and joins the plan carries
   against the spec's numbers (the push-ins as many as the family's moving shots allow, the dips at the chapters), decided before the
   project is built.

**Judge prompt** (the main session fills the `<…>`):

```
You are the judge of a /analyze-with-loupe Static run (narrated still-picture videos), checkpoint <J1|J2|J3|J4|J5> for video <NN>.
Read first: C:/Users/Bulzart/.claude/analyze-with-loupe/reference/static/130_13_the-judge.md (your brief: follow it exactly), then
<RUN>/20-analysis/static-spec.md and only the sections of static §4, §5 or §6 your checkpoint touches.
Run: <RUN>. Toolkit T: "C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe" "C:/Users/Bulzart/.claude/analyze-with-loupe/scripts/awl.py"
(through PowerShell). The video's family: <family name> (<refs>); the run's niche and its references in the family: <niche> (<refs>,
or none: then the family's numbers lead); the run's QC fixes: <ask|auto|off>.
<what happened since the last checkpoint: the agent's report, the measured numbers, or "nothing generated yet">
Do: `T static profile --run <RUN> --refs <refs>` and `T static forecast --run <RUN> --video <NN> [--part … --from … --to …]`; read them
with the plan files; decide every change yourself (never ask anyone), edit only the plan files your checkpoint owns (J1: the narration
JSON's pace, delivery, settings and pause tags, the image plan's prompts and characters, music.json's track; J2: the narration
JSON's levers for passages made again; J3: the
image prompts of the stretches not made yet; J4: music.json's track; J5: the image plan's motion, labels and joins), run the forecast
again, and append your decisions to <RUN>/40-briefs/video-<NN>-judge.md (each: what, why with the numbers, the predicted result).
Never generate anything, never change a lock, a start choice or the memory guard, never leave the references' numbers. Heavy work (a
model, a test suite) never runs while FLUX 3 Klein makes images.
Final message: one line per decision and the forecast numbers you expect.
```
