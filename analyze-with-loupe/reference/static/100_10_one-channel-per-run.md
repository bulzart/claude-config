## 10 One channel per run

The user, 2026-11-07: "on Static mode the idea behind it is that when we do analyzing the references we should lock: one narrator, and
one field/kind of videos that we will continue making, because we will use the content to publish on youtube, and we don't want to mix
styles and subjects in one channel"; "even though user picks philosophy we still have to take from patterns, hooks, engagement style,
visuality, narration, presenting and other data from the references, but just make the content into philosophy niche and subject".

A Static run is one channel. Its **locks** are set once and kept by every video the run ever makes; `T static lock --run RUN` shows them:
- **The niche** (A5, the user's pick: philosophy, math, history, storytelling, persuasion …; `T static lock --run RUN --niche
  "<niche>"`). Every subject of the run comes from it (§3). The references give the craft (the hook, the telling, the devices, the
  pacing, the edit, the sound, the text look), never the field: a run that studied history references may make philosophy videos in
  their way.
- **The visual style** (A5: the user names the one reference whose visuals they like; `T static lock --run RUN --style-ref <V>`). Its
  picture style is the run's style lock (§2, §5: every image of every video, by the API, FLUX 3 Klein or the user), and when it shows
  captions, its text look is the run's text look (font family, weight, size, colours, outline, case, position, highlight, entrance;
  §2, §7); without captions on it, the text look of the references that have them. The other references still give the rest of the
  craft.
- **The narrator** (A6s, the user's pick of five samples, §6): one voice for every video. `T tts design` and `T tts voice` refuse a new
  voice once one is picked; `--replace` only when the user picks again in a clone.
- The format, the images' source, the CapCut plan, the effects folder and the QC fixes: the start's answers.
The toolkit refuses another niche or style reference once one is set (`--replace` only before the run's first video): another niche
is another run, a clone.

**More videos** (the user: "the next videos he decides to generate in that claude code run session he will only be suggested to pick
subjects of that niche he firstly picked"): `/analyze-with-loupe more <run> [N]`, or the user asking for more after a wrap-up. No start
question is asked again and nothing is analysed again: the count when it is not given (AskUserQuestion, header "Videos"), then A6s for
the new videos only. Their pool holds subjects of the locked niche the run has not made (`T static subjects --run RUN` lists the made
ones; never one of them, never one so close it retells it), the one stop shows the subjects alone (no voice samples: the narrator is
locked), each pick is added with `T static subjects --run RUN --add "<title>"` (it takes the next video number), and their scripts and
image plans keep the locked style and text look. Then A9s runs for the new videos only. A run made before the locks existed is asked
its niche once, with its subjects as context, before its pool is drawn; its style reference is the reference its style lock came from.

**A clone for another niche** (the user: "we still need the references processed data to be used in another niche such as history then
we can do something like /analyze-with-loupe clone <run> and it will create a new run folder but will just clone all the references
data ... and then ask for the niche"): `T clone-run --from <run>` makes a new run with the analysis copied: the inventory, every
reference's media (frames, storyboards, transcripts, the audio and edit profiles), the cards and the spec, the characters and the
narrator, with the paths inside them pointed at the new run. The subjects, the niche, the old niche's subject pool, every video's files,
the ledger and the CapCut projects stay with the old run. The clone starts at A5 with one AskUserQuestion call: its niche (never the old
one; "Other" for any), the narrator (keep it, first; or five new samples) and the visual style (keep the reference, first; or name
another), and the count. A style picked again rewrites the spec's style lock and text look from that reference's card. A narrator
picked again makes five new samples (`T tts design --run RUN --replace …`, then `T tts voice --run RUN --sample K --replace`). Nothing is
analysed twice.
