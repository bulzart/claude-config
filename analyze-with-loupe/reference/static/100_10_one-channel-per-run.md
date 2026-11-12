## 10 One channel per run

The user, 2026-11-07: "on Static mode the idea behind it is that when we do analyzing the references we should lock: one narrator, and
one field/kind of videos that we will continue making, because we will use the content to publish on youtube, and we don't want to mix
styles and subjects in one channel"; "even though user picks philosophy we still have to take from patterns, hooks, engagement style,
visuality, narration, presenting and other data from the references, but just make the content into philosophy niche and subject".

A Static run is one channel. Its **locks** are set once and kept by every video the run ever makes; `T static lock --run RUN` shows them:
- **The niche** (A5, the user's pick: philosophy, math, history, storytelling, persuasion, survival …; `T static lock --run RUN --niche
  "<niche>"`). It is a **family of content**: the field the channel is about and the kind of stories that live in it, never a title
  wording, a story form, a point of view or a length (below: "The niche is a family, each video an approach"). Every subject of the run
  comes from it (§3). The references give the craft (the hook, the telling, the devices, the pacing, the edit, the sound, the text
  look), never the field: a run that studied history references may make philosophy videos in their way. When the set holds
  references of the run's niche, they give most of the craft and the whole set the rest (§1 "The run's niche within the set"; the
  user, 2026-11-09).
- **The visual style** (A5: the user names the one reference whose visuals they like; `T static lock --run RUN --style-ref <V>`). Its
  picture style is the run's style lock (§2, §5: every image of every video, by the API, FLUX 3 Klein or the user), and when it shows
  captions, its text look is the run's text look (font family, weight, size, colours, outline, case, position, highlight, entrance;
  §2, §7); without captions on it, the text look of the references that have them. The other references still give the rest of the
  craft.
- **The narrator** (A6s, the user's pick of five samples, §6): one voice for every video. `T tts design` and `T tts voice` refuse a new
  voice once one is picked; `--replace` only when the user picks again in a clone.
- The formats, the images' source, the CapCut plan, the narration model (the ElevenLabs model that speaks the run's videos, picked from
  the live list, §6), the effects folder and the QC fixes: the start's answers (a later request may name another format for its next
  videos, `T static format` again: one channel can hold Shorts and long videos; or the same videos in one more format, `T static
  format --also`, §2b).
- **Not a lock: each video's approach and language** (below and §6): they are asked or decided per video, and recorded with its
  subject, so one channel can hold videos in several languages and in several approaches inside the one niche.
- **Not a lock: the length** (the user, 2026-11-12): asked at A5 once the niche is locked and before anything is planned or generated
  (static §2 "Length", §4): standard (the niche's references' length) or the user's own, per batch or per video, kept in
  `static.length_plan`; every `more <run>` asks it again for its new videos.
The toolkit refuses another niche or style reference once one is set (`--replace` only before the run's first video): another niche
is another run, a clone.

**The niche is a family, each video an approach** (the user, 2026-11-11: "the idea is not to always product the exact same form of
content, but rather have an niche in a family of content such as 'how to survive when X' or 'N days of X' but not lock 'N days of X'
only, and then all the videos will be 'N days of X' but rather we lock the niche family and then it build taking from the whole set of
reference but pushing of what the niche references story was about but not always in the same direction and approach of story and
content but always inside that niche family that the reference videos were about, also leaving room to agents for free will and
creativity on their own too"). The lock names the **field** ("Survival scenarios and how-tos"), never "N days of X" or "how to
survive when X" alone: a run locked to a title form makes every video that form. What changes from video to video is its
**approach**, written with its subject (`T static subjects --run RUN --add "<title>" --story-form … --language …`; `state.json →
static.video_info`):
- `story_form`: the shape of the telling (counted days, hour by hour, a real case retold, a life path, "what happens if", myth
  against fact, a step-by-step guide …), or the story family of the spec (F1, F2, F3 …) it follows;
- `angle`: what the video shows or argues about its subject (the twist, the one decision that saved people, the mechanism);
- `point_of_view`: second person "you", the third person, "we", an expert; `time_frame`: the span it counts (minutes, hours, days,
  years); `scale`: one person, a family, a town, a country, a species;
- `title_form`: a pattern of the references' titles (§12: "How …", "Why …", "N days …", a "you" premise, a question, "The ENTIRE
  history of …");
- `pillar`: the sub-topic inside the niche (heat, water, fire …), so the same danger does not come twice in a row; `series`
  (optional): a named recurring form the user or the agent wants to keep; `why`: the references' numbers or the reason it rests on.
The references give the approaches (A3 reads each one's story form, point of view, time frame, scale, pillar and title form, §1; the
spec lists them with counts, §2), and the **whole set** may lend the niche its other story families: an approach is built taking from
the whole set, pushing off what the niche references' story was about (a survival run may tell a history, a myth against fact or a
how-to in the survival references' craft: the hook, the devices, the retention, the pace). The agents keep **room of their own**: an
approach no reference shows is allowed when it stays inside the niche, keeps the references' craft and passes the copy test
(`creative-direction.md` §5.0), and the agent writes why. **Variety across the run**: a video's approach differs from the one before
it in at least two of story form, time frame and title form, unless the data says one form is the niche's strength and the reason is
written. **The point of view is never varied for variety's sake** (the user, 2026-11-11: "don't push point of view changes ... that has
to be decided based on the references, the other changes suffice"): each video's point of view follows what the references do (their
second-person "you" or third-person telling, and where each is used, §1, §2), decided per video from that data; `T static subjects --run RUN` lists the approaches made (a fact: the agent decides), and the pool of A6s (§3)
shows each candidate with its approach beside the last video's. **Rewording a niche** (never to another field): `T static lock --run
RUN --reword "<wording>" --why "<reason>"`, allowed after videos exist and recorded in `static.niche.reworded`. (The run of
2026-11-06 locked its niche as "Survival scenarios: 'how to survive when X' and 'N days of X' stories told to 'you', with real survival
facts": two title forms and a point of view inside the field, so every candidate came back a "How to …"; it was reworded to "Survival
scenarios and how-tos".)

**More videos** (the user: "the next videos he decides to generate in that claude code run session he will only be suggested to pick
subjects of that niche he firstly picked"): `/analyze-with-loupe more <run> [N]`, or the user asking for more after a wrap-up. No start
question is asked again and nothing already analysed is analysed again (new references first: below): the count when it is not given
(AskUserQuestion, header "Videos"), then the length (header "Length": standard or the user's own, §2, §4; the niche is locked, so it
comes straight after the count and before any planning), then the language of each new video (header "Language", §6; the narration model stays the run's),
then A6s for the new videos only. Their pool holds subjects of the locked niche the run has not made (`T static subjects --run RUN`
lists the made ones with their approaches and languages; never one of them, never one so close it retells it), each with its approach
beside the last video's (above), the one stop shows the subjects alone (no voice samples: the narrator is locked), each pick is added
with `T static subjects --run RUN --add "<title>" --story-form … --language …` (it takes the next video number), and their scripts
and image plans keep the locked style and text look. Then A9s runs for the new videos only. A run made before the locks existed is asked
its niche once, with its subjects as context, before its pool is drawn; its style reference is the reference its style lock came from.

**New references in the same run** (the user, 2026-11-07: "if we did generate one video based on sadam husseins reference and then i
added two more references it doesnt mean we have to create a new run folder ... if there's new references analyze them and save their
data on the folders we specifically use, if there's not we just use what we already mined from the references, but all inside one run
folder"; "a new run session or a clone session is the only thing that creates a new run folder"): a session keeps its run. Files added
to the run's references folder are taken into it before its next videos: `T inventory "<references folder>" --run RUN --as references`
again (every file already listed keeps its id; the new ones take the next ids, its `new` lists them; a file that has gone keeps its id,
marked gone), then A1 for the new ones only (`awl-analyze-prepare`'s Static A1: `split-audio --audio-only`, `prep-all --ocr-frames
30`, which skips every prepared reference, `edit-profile --ref <V>` for each new one, `T static context`), their cards (A3 in
`awl-analyze-study`), and the spec revised with every reference (A4: the length, pace, hook, title and bed patterns now hold the new
ones; the locks stay: the niche, the style reference, the narrator; A5 is not asked again). No new reference: the videos use what the
run already mined. Then More videos as above.

**A clone for another niche** (the user: "we still need the references processed data to be used in another niche such as history then
we can do something like /analyze-with-loupe clone <run> and it will create a new run folder but will just clone all the references
data ... and then ask for the niche"): `T clone-run --from <run>` makes a new run with the analysis copied: the inventory, every
reference's media (frames, storyboards, transcripts, the audio and edit profiles), the cards and the spec, the characters and the
narrator, with the paths inside them pointed at the new run. The subjects, the niche, the old niche's subject pool, every video's files,
the ledger and the CapCut projects stay with the old run. The clone starts at A5 with one AskUserQuestion call: its niche (never the old
one; "Other" for any), the narrator (keep it, first; or five new samples) and the visual style (keep the reference, first; or name
another), and the count; then, in a second call, the narration model (keep the run's, first; or another from the live list, §6) and
the language of each video (§6). A style picked again rewrites the spec's style lock and text look from that reference's card. A narrator
picked again gets five new samples (account voices by `T tts voices --run RUN --measure`, designs by `T tts design --run RUN
--replace …`), then `T tts voice --run RUN --voice-id ID --replace` (or `--sample K --replace`). Nothing is
analysed twice.
