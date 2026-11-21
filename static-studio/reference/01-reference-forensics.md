# 01 — Reference forensics: learn why the story works

## Intent

A reference folder may contain formats you recognise and ones you don't. Treat **every video as its own narrative system**—analyse it fully before imposing any category on it. Categories emerge from the evidence; they are not assigned from a predefined list. Study genuinely comparable cohorts once categories have been discovered. The objective is transferable knowledge about *audience experience*, not a copyable outline. A user-found viral video is a strong creative reference, not proof that a specific zoom or hook caused its views.

## Intake, audio and visual coverage

Use `static_core.py init`, `scan`, `prepare --dry-run`, then `prepare`. Never skip Whisper merely because speech is present in auto-captions. Faster-Whisper with word timestamps, VAD, and original source audio creates `10-media/V###/transcript.json` plus `.txt` (when available). Listen to the video yourself; repair/annotate uncertain names, numerals, quotes, jokes, irony, tonal delivery and sound-only context. Whisper is **an imperfect observation aid**, not an authority on dialogue. For silent clips, mark no audio; for a failed transcribe mark *unknown/unprocessed*, not “no speech.”

Visual pass: two sampled frames per second is broad semantic coverage (the run's analysis rate, `state.json` `analysis_fps`: 2 for a new run, each frame picked by and kept with its own source timestamp; a run keeps the rate it was analysed at, and one made before keeps its 5 fps nominal slots); read it as temporal sequence, not random isolated thumbnails. At 2 fps a shot shorter than about a second can merge with its neighbours and a flash is rarely seen: the av-profile lists `inspect_candidates` (flashes, cut series, transitions, short shots), and `inspect-window --ref V### --from mm:ss --to mm:ss` looks closer at one brief stretch (10 fps by default, or `--native` for every frame; at most a few hundred frames, never a whole video). To understand a cut, reveal, text animation, camera move or split-second joke, seek into the original video and use full-native-FPS extraction for the specific reference (`prepare --ids V### --full-fps`) or a narrow decoded segment. `--full-fps` can create enormous files for long videos: plan space and inspect in digestible ranges. Important for 30/60 fps reference edits: measure actual frame-to-frame changes; a contact sheet is only a coarse map. Retain timestamps and original frame order. Never assert that examining a subset equals reviewing every native frame.

Extract, within the agent's analytical notes: edit boundaries, title-card transitions, types and durations of visual states (still / diagram / archival shot / photo collage / screen recording / artwork), timing of narration relative to image change, silence, sound cues, music intensity, on-screen language, and how graphics convey things the narrator intentionally leaves unsaid. When a visual is technically hard to interpret, mark it as unknown and re-open the relevant source segment. For a factual claim shown on-screen, verify it independently before recycling the *fact*.

## Evidence discipline

For every analytical assertion, distinguish:

- `[O]` observed at a specific video timestamp (spoken line, visible object, scene cut, sound, or duration).
- `[I]` inferred editing/story mechanism (why *this could* sustain curiosity or comprehension).
- `[U]` unknown (real retention drop, comments, click-through rate, authors' intent, audience emotions, view counts not actually supplied).
- `[M]` independently supplied metadata (platform, publish date, views, CTR, average percentage viewed, other analytics) with source/time window and denominator. Don't present `[I]` as `[M]`.

Where two videos differ in age, audience, topic, creator, upload era or format, don't infer performance by raw view count. YouTube Studio's retention charts and similar-length comparisons may be used when the user supplies them. Never fabricate analytics or conclude that a “hook worked” as a measured fact without valid evidence.

## Per-reference creative anatomy (whole-video, not keyword extraction)

Study the reference start to finish before segmenting. The creator's sequence can be modeled as a **viewer-experience timeline**, with 5–20 meaningful turns for a long video, not a requirement for a cliffhanger every 15 seconds. For each turn record time range, current viewer question, what is revealed or changed, emotional state and tension, whether the viewer can infer something themselves, visual/sonic mechanism, how this advances or delays an earned payoff, and whether a prior planted detail returns.

A detailed card in `20-analysis/cards/V###.json` should include these additional fields beyond the mandatory schema:

```json
{
  "reference_id": "V001",
  "niches": ["military history", "decision-making"],
  "story_form": "historical narrative",
  "cohort_id": "optional-stable-slug",
  "language": "en",
  "visual_medium": "illustrated stills with maps",
  "platform": "YouTube",
  "length_family": "longform-10-to-18-min",
  "title_promise": "Question or expectation set by the title",
  "editorial_summary": "What the video is really about beyond its nouns",
  "hook": {"start_s": 0, "end_s": 35, "promise": "...", "evidence": "[O] ..."},
  "viewer_experience": [
    {"start_s": 0, "end_s": 55, "question": "...", "new_value": "...",
     "emotional_turn": "...", "visual_function": "...", "breathing_room": "...",
     "evidence": "[O] V001 00:14–00:32; [I] ..."}
  ],
  "narrator_character": "Conversational/inquisitive/grounded, with examples",
  "narration_delivery": {"from_words": "[I] dry asides, direct address, short punchlines after long setups",
                         "measured": "[O] av-profile: pitch range ~12 st per window, rate 190-245 wpm, a music bed under the voice"},
  "audiovisual_moments": [
    {"start_s": 240, "end_s": 300, "narration": "confides; slows down",
     "picture": "holds one face for 14 s while the words move on", "edit_and_sound": "music drops out",
     "viewer_effect": "[I] the quiet makes the next cut land", "evidence": "[O] sheet-005, 04:00-05:00"}
  ],
  "delight": [{"what": "the specific, slightly absurd true detail before each turn", "evidence": "[O] 03:12, 07:40",
               "confidence": "[I] medium: seen twice, no retention data"}],
  "information_density": "Measured and interpreted within its format",
  "creative_strengths": ["..."],
  "weaknesses_or_tradeoffs": ["..."],
  "transferable_devices": [
    {"from_time_s": 185, "observed_technique": "...", "audience_function": "...",
     "possible_adaptation": "...", "constraint": "do not copy the original wording or unique scene"}
  ],
  "metrics": {"supplied": false},
  "unknowns": ["Actual audience retention has not been provided"]
}
```

**Watch the reference as a film: `av-profile --run "RUN" --refs V###,...`** (10 §1). It measures the narration (speaking rate per window and how it varies, pitch range and word-to-word movement, loudness contrast, the level under the voice in its gaps) and the picture (cuts, shot lengths, moving and still time, brightness and saturation, the same picture coming back), side by side in 15-second windows with the words spoken, and writes one **watch sheet** per minute to `20-analysis/av/V###/`: a frame every 5 seconds with its words underneath. Open the sheets in order: they are the closest thing to watching that an agent has, and they show what the viewer sees *while* each sentence is heard. The same functions measure this run's narration and export later, so the numbers compare directly; they are measurements, never verdicts. `pace-profile` remains the quick view of pace and pauses alone.

For `narrator_character` and `narration_delivery`, combine what the words show (diction, humour, asides, direct address, sentence music) with what was measured, and label which is which. Note where the narrator's longest silences fall and what the story is doing there. For `audiovisual_moments`, record the moments where narration, picture, edit and sound work together (or against each other), with what you infer it does for the viewer. For `delight`, what makes this video *enjoyable*, with its evidence and how sure you are. The command also expects a *human-readable* `20-analysis/V###-notes.md` summarizing the reference's 3–6 most useful mechanisms with timestamps and a critique of where it loses the viewer. If a creator succeeds despite apparent repetition or a sparse edit, record that: the voice, concrete tension, or source topic may be doing the work. Do not mistake high shot frequency for high value.

## Content review (every reference, before it lends anything)

Every reference gets a content review from the agent who watched it, written as `content-review --ref V### --file review.json` (fields in 07). It covers every picture: open every watch sheet and every **shot sheet** (`content-review --ref V### --shot-sheets`: one frame of every shot, 36 to a sheet), because a watch sheet's frame every 5 seconds can step over a shot of a second or two; the review is refused until the shot sheets exist. Start from `content-review --ref V### --signals`: the stretches whose words touch 02's subjects and the picture stretches the samples cannot settle. They are places to look, not verdicts: a word can be plain fact, and a picture can be graphic with nothing said. Judge the use in context, never a keyword.

Two things are recorded, and kept apart:

- **Content safety** (`kind: safety`): graphic injury or gore, distressing imagery, self-harm, dangerous instructions, sexual violence or exploitation, anything sexual involving minors, hate or violent extremism, nudity. Each has a severity and an action: `exclude` (nothing from it is used), `restrict_visuals` (the subject may be told, nothing graphic shown or described) or `keep` (looked at and fine in context, with why). A battle told with casualty counts, maps and the soldiers' choices is not a safety segment at all; a lingering wound close-up is.
- **The user's creative exclusions** (`kind: religion_superstition` or `holiday`): a ritual, a devotional theme, an omen, a curse, a holiday celebration or holiday framing used as a story device. Not harmful and never recorded as safety; simply never used here. `exclude`, or `keep` for a plain unavoidable fact never dramatised (02).

**Take out as little as keeps our videos within 02, and no less.** Exclude only when nothing of the moment can be borrowed without the excluded thing itself: the moment *is* the graphic image, the cruelty, the device. When the story beat can be told within 02 (a triage under fire with nobody described as if dead, a battle without its wounds), restrict what is shown and how it is described, and keep the beat. Severity is proportionate: what is low is restricted or kept, never excluded. The presence of a child, a young soldier, a wounded or motionless person, or an object or shape that resembles something harmful is not by itself a reason to exclude: judge what is shown, what is said, what is meant and how graphically. A child in an ordinary scene is not a safety segment at all (our own pictures show adults anyway, 02); `sexual_content_minors` is only for sexual content involving a minor, and is always excluded. Every action says why: an exclusion says why restricting is not enough, or why it is a story device rather than a plain fact.

**Evidence, not cues.** A colour (a red patch), a single word or an ambiguous shape is a reason to look closer, never a classification. A finding rests on what the frames show, what is said and what the moment does in the story, and its evidence cites the times you saw and heard it. When these don't settle it, mark it `unsure`, take a closer look (required for every unsure segment, whatever you decide) and decide on what is there; a judgement call stays marked unsure in the record. A creative exclusion counts however it is carried: said outright, paraphrased, implied, or only in the picture; a religious, superstitious or holiday word used as an idiom or a passing fact is not a device.

For each segment: its timestamps, what it is (neutrally, no graphic detail), its role in the story, the evidence, how sure you are, and the action. An excluded segment also names what depends on it (`depends`: a setup, a payoff, a line that only makes sense with it), each with why; the range follows the story, never a fixed number of seconds. It names what must not come back (`avoid`): the device itself, so that no rewrite smuggles it back in other words. What sits next to it stays usable, and so does a useful element inside the same picture or moment (an exchange, a gesture, the pacing): the direction may cite it with `borrows_only`, naming exactly what it takes (10). Say whether the reference's story still holds without it (`story_without_exclusions`: coherent, bridged, or too_dependent with why), and what stays useful (pacing, hooks, structure, composition, editing rhythm, reactions).

Sparse samples can miss a brief image. Where risk or doubt justifies it, look closer (`inspect-window`) before deciding; a segment you are unsure of and still want to use needs that closer look on record. After looking at disturbing material, remove the window's frames (`inspect-window ... --remove`): the record stays, no extra copy does.

## Cross-video synthesis without niche pollution

Each reference can have multiple niche tags but must have a primary `story_form`. Distinguish topical niche (“military history”) from story form (“decision-under-pressure reconstruction”) from art style (“charcoal maps”). Runtime is measured by ffprobe, not estimated from cards. Use `cohorts`: it reports median/mean/min/max and warns on high spread. **A combined average over five 40-second explainers and five 15-minute history videos is invalid as the Standard length of either.** Even 8-minute and 35-minute history videos may form separate runtime families. Provide comparable IDs in the length lock.

When niche or story_form labels vary across cards for what are clearly comparable videos (e.g. one agent wrote `"military history narrative"`, another `"military history"`), assign an explicit `cohort_id` (a stable lowercase slug you choose, e.g. `long-military-history`) to the relevant cards. Any cards sharing a `cohort_id` form their own group in the `cohorts` output and can be used directly in `length --cohort-id` without matching niche/story_form strings.

After all cards, create `20-analysis/niche-synthesis.md`: one chapter per niche with (a) primary references and durations, (b) observed audience experiences, (c) confidence and disagreement across references, (d) specific *story engine* candidates, (e) medium/style choices and limits, (f) pacing ranges for that audience, (g) ways to adapt structural techniques borrowed from another niche, with an explanation of the trade-off. An animated graphic from a short how-to may help a 20-minute strategic history explanation; its aggressive pacing probably should not be copied.

**Outcome:** The user sees distinct creative directions rather than a generic count of references. After picking a direction, derive a **creative profile** (`20-analysis/creative-profiles/[cluster-slug].md`) from the synthesis—what appears to work for that audience, what weaknesses exist, and what creative territory remains unexplored. See §02 for the profile structure. The writer gains *permission to be original*; source titles, names, jokes, voice clones or watermark/overlay text do not get repeated in the new video's final creative work.


Sampled frame filenames have a `frame-index.json`. In a run analysed at 2 fps each frame carries its own exact time (`t_s`, on the transcript's clock: its source timestamp minus the audio stream's start, so a variable frame rate or a start offset never shifts it; `pts_s` is the source's, `slot_s` the half-second it was picked for). What happens between two samples is unseen: a cut is known only to within one interval. File numbers are a sequence, not a clock: a source with uneven frames skips a slot now and then, so look a frame's time up in the index (`t_s`), never compute it from its number. A run made before keeps **nominal** slots (`mode: nominal_sample_time`, within half an interval of the slot). For exact transitions or frame-accurate claims, look at a native-frame window (`inspect-window --native`); never assert precise source timings from samples alone.
