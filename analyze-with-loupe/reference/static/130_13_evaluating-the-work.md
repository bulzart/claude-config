## 13 Evaluating the work (A6s, S2, S3, S4)

The user, 2026-11-13: "every judge in this static mode should be removed, the pipeline should be intelligent to evaluate and be skeptical in
itself and judge while it works, but spawn different judges who have no context on the main agent". This replaces the judge agent and its
checkpoints (2026-11-08: "make a smart judge system ... nothing should turn out as unexpected"); what that system learned is kept below as
the pipeline's own habits and facts. (A run planned before 2026-11-13 may hold `video-NN-judge.md` files: they are history.)

**Judge your own work while you do it, and be skeptical of it.** Whoever makes a plan, a line, a still, a bed or an edit judges it as it
is made and assumes it may be wrong: the first plan, the first take, the first still. Every value an output will carry is chosen on
purpose, from the references' measured numbers (the run's niche's own within the video's family, the family's and the set's beside them,
§1 "The run's niche within the set"; their median unless the data gives a reason for another of theirs, written with that reason; when the
niche's references are too few to carry a number alone, weigh it with the family's and say how), before it is generated; the choice is
written down with the numbers it rests on and the result it should give; after the generation the measured result is read against it, and a
miss is explained and corrected, or recorded with its reason. Nothing lands somewhere by accident (2026-11-08, video 03: the narration's
pace landed at the top of its band and the script carried 33 long pauses per 10 minutes against the family's 6.3, because nobody had chosen
either number or forecast them). Ask of everything: what would make a stranger leave, what is unclear, what is not true, what did I not
measure, what did I assume without looking? A decision and its reason go into the video's brief (`40-briefs/video-NN-brief.md`). The user
is never asked for a call (the user, 2026-10-28 and 2026-11-08), and nothing here leaves the run's locks (the niche, the style lock, the
narrator), the user's start choices (formats, images' source, QC fixes, CapCut plan, the narration model), the video's language and approach
as the user picked them, §11 and §11b, or the memory guard.

**Fresh reviewers, with none of your context.** **One fresh read of the plan is a standing step** (the user, 2026-11-13: "make one fresh
read of the plan before the first generation a standing step, still with no judge"): before the first generation of each video (A6s step
9), spawn a new agent that reads the finished plan cold, as a stranger on the feed would (the narration's text, the pictures' plan, the
title, thumbnail and whatever else is published with the video), and reports where it would stop watching and what is unclear, flat,
repetitive, unearned or untrue; you decide and fix, while a change still costs a line. It is a read, not a judge: no checklist, no verdict,
no schedule of checkpoints. Beyond that one, when a second opinion is worth having, spawn one or more new agents (`subagent_type:
general-purpose`, `model: "opus"`) that know nothing of the working agent's context: give each the thing to look at and the standard to
look at it by (the references' numbers where they apply, the hard rules), and never your reasoning, expectations or conclusions (a
reviewer told what to find finds it). Several reviewers may look at the same thing in different ways: where they agree it is evidence,
where they differ it is a question to settle with the data. A reviewer reports; it never changes a plan or a file and never generates, and
you decide and fix (a re-draw follows the run's QC fixes). Beyond the standing read you choose when and how many, never on a schedule, and
not at all when there is nothing worth asking; typical moments are a stretch of made stills looked at cold against their lines and the
finished edit. Heavy work (a model, a test suite) never runs beside FLUX 3 Klein, a reviewer included. In a session without agents the
working agent does the cold read itself, from the artifact alone.

**Informed helpers, with all of your context** (the user, 2026-11-14: agents that "use their free will, suggestions, curiosity build up,
engagement engine, strategy and other aspects"): the other kind of fresh agent, for the design (A6s 6a) and any time the planner wants more
minds on the work. It is given everything the planner has (the spec's page "What the references teach" and the niche's cards, the design
note, the script, the pictures' plan, the facts), the user's aim in the user's words, the hard rules and what a change costs at this stage;
it reads the references first, then thinks freely and brings back suggestions, each with its reason (the pattern, or the viewer) and its cost
(free; a line recorded again; a still drawn again). It scores and passes nothing and changes no file but its own report; the planner decides,
applies what is free and brings the costly to the user. Whether to use any, how many and with what focus is the planner's call for the
subject (§4b); a cold reader, who is given nothing, is a different check.

**The facts you read.** `20-analysis/static-spec.md` and the cards (the craft); `T static profile --run RUN --refs <the family>` and
`--refs <the niche's references in it>` (their numbers: the pace by the fair measure, the pauses, the seconds a still); the video's plan
files (`40-briefs/video-NN-*`); `T static forecast` (below); the run's history (`60-outputs/video-*/images*.json` notes, the briefs); and
the PC's model-memory record.

**The forecast** (`T static forecast --run RUN --video NN [--part narration|images|music] [--from K --to K]`, facts only, written to
`40-briefs/video-NN-forecast.json`):
- *Narration*: the plan's words, lines and characters, the lines with their own delivery and with pause tags, the lines that name an
  intimate part of the body (`intimate_body_words`, §11b), the passages and the
  characters they send (their tags included) against the account's characters left (read when the key is set: which line whole passages
  reach), the target point and bands, the family's numbers, the levers (the voice, the narration's delivery, the settings) and the
  voice's point measured for them (`same`, or the voice's latest as `nearest`: a probe's or a made narration's; `T tts fit` learns it
  again): its words a minute while articulating and overall, over the delivered audio (`wpm_delivered`: the length a narration of these
  words will have), its pauses; and from them the predicted pace, length and pause pattern against the point, the target length and the
  family's numbers. No speed-up and no pause between lines is calculated: a model's own `speed` setting is a lever of the request (§6),
  never a change of the delivered audio, and nothing is placed after it (§6).
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
measure against a family median of 211.9 by the same fair measure. The speaking pace is set and judged by `wpm_articulation`. The pace is
read on the narration as delivered, the file that plays (2026-11-08, the same video: its raw join read 212.7 where the processed file
read 207.4; since 2026-11-09 nothing is done to the delivered audio, so the two are one file).

**Your own checks, in order** (each step's skill holds its steps; these are what each check settles, from the old checkpoints' lessons):
1. *Before any generation* (A6s step 9, once the scripts, image plans and bed are written; `awl-static-plan`): read the forecast of every
   part and settle:
   - the video's **approach and language** as recorded (`T static subjects --run RUN`, `state.json → static.video_info`): the family the
     video takes, its variety against the last video's approach (§10), the language of the narration, title and captions and its model (§6);
   - the narration's `pace` (§4): `refs` (the niche's references within the family, else the family), the family's bands by the fair
     measure, the `target` point (the niche's references' median of `wpm_articulation` and of `wpm_overall`, the family's beside it, unless
     a reason in the data), the `tolerance`; for another language the references' English points converted by the measured ratio of the
     script's units to its English glosses' words (`T static units --run RUN --video NN`), written with the ratio and `"unit"` (§4); the
     model's own levers (§6 "The models");
   - the levers that reach the point (§6 "The pace"): the narration's `delivery` (pace and register tags), the `voice_settings`, the
     words (sentence length and punctuation), each measured first on a probe (passage 1 exactly as `say` will send it; another lever set is
     another probe): name the lever sets, run `T tts probe` for each (billed), as few probes as the characters left allow (the forecast's
     `credits`), the narrator never changed (a lock);
   - the pauses: the long pauses the niche's references hold, the family's beside them (their `long_pauses_per_10min` times the video's
     minutes, at the strongest turns), asked as `tags_after` ("[pause]": 0.76 s with George, 2026-11-09; "[long pause]" ran 1.6-2.6 s, over
     the family's 0.92 s, §6) or punctuation, every other rest the voice's own, the probe's pause pattern read against the family's (a pause
     the family does not hold is not asked);
   - the strong lines (their own `delivery` tags; at most one in five, never two in a row, §4), the length against the user's pick
     (`static.length_plan`; the standard's against the family's, §4) and the forecast's predicted length against it;
   - every line the forecast marks with `intimate_body_words` (§11b): told by its other places; for another language the forecast runs the
     §11, §11b and intimate-word lists on each line's English gloss (`lines_without_gloss` names the lines that have none: read those in
     their language yourself);
   - every image prompt the forecast marks: a thing that would carry writing gets its exact words when the story needs them (a label is
     CapCut text, §5) or is described as plain and blank; digits leave the scene words; a split word becomes one scene; a §11 word becomes
     a secular description; a §11b word becomes the dressed or calm moment (every person's clothes named top to bottom; the care, never
     the harm; a lying-down pose that is the survival fact stays, the person clearly alive in it); a missing sentence is put back; a still
     whose references the memory cannot hold rides with a cast sheet (§5);
   - the bed: its caption and sections fixed where the forecast marks them; when it runs (when the images are done, or in a gap between
     image stretches once the narration is final, with nothing else holding memory).
   Then run the forecast again and write down the numbers you expect.
2. *After the narration* (S2, before the images; `awl-static-sound`): the measured pace and pauses (`T tts say`'s `pace`, then `T
   narration-words`) against the forecast and the point: on the point within the tolerance, the pause pattern near the family's, the
   length, a partial narration (the characters ran out) named; the image spans against the seconds a still. A miss is explained from the
   numbers and changed through the request first: another delivery tag, setting or wording and the passages made again (billed, by the
   run's QC fixes). What those cannot reach (the voice is locked; the tags and pause tags tried and measured) is kept as delivered and
   recorded with its reason, and the speed-up that would close it (the tempo that brings the speaking measure to the point, at most
   `config static.narration.tempo_max`, 1.05) is written for the wrap-up to offer: it is made only on the user's yes after they have
   looked at the delivered project (§6; the user, 2026-11-09: "only speedup on their permission never else"), then `T narration-words`,
   `T slideshow plan` and the project again. Nothing else is ever done to the delivered audio but the level rule (§6: one gain only when
   the narration sits outside the references' loudness). Spans are moved by `from_line` (free). The point learned by the narration is the
   next video's forecast.
3. *Between image stretches* (S3; the main session, when an image agent reports, before the next is spawned; `awl-analyze-produce` A9b):
   read the stretch's report and flags and view the stills it names; trace what went wrong to its prompt words (the caption the upsampler
   wrote is in each attempt) and change the prompts of the stills still to come so it does not happen again (prevention costs no
   generation); a re-draw of a made still follows the run's QC fixes. A fresh reviewer may look at the stretch cold, against its lines.
4. *Right before the bed* (S2's bed step, when the images are done or in a gap between image stretches): the memory forecast again,
   recorded as a fact and never a gate ("Memory is a fact" above), so the bed is tried. Only a real guard stop shows it does not fit: the
   user is told the guard's line (a closed program frees the memory; the guard is never changed and nothing of the user's is closed), the
   bed is tried once in ACE-Step's int8 (`--quantization int8_weight_only`, §6: only after that stop), once more before the edit when that
   is stopped too, and still stopped the video goes on without a bed, named (never a blocker); after it: `T music measure` against the
   bed's plan.
5. *Before the edit* (S4; the edit agent's first step): the labels, drawings, moves and joins the plan carries against the spec's numbers
   (the push-ins as many as the family's moving shots allow, the dips at the chapters; the drawings as many and as long as the references'
   annotation pattern shows, §2, or, where they draw nothing, only where the narration elaborates something a drawn layer shows better,
   each with its reason), read with `T draw list` and the `drawings_*` facts of `T slideshow plan` (a clip not rendered, a drawing on a
   moving image, past its image or in the caption band), decided before the project is built. Also the caption word box's colour
   (`captions.word_box.color`, §7: the video's own, from its finished stills' palette and standing out from them, never the last video's by
   default; write the colours you read and why in `word_box.why`).
