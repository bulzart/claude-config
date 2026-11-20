# 01 — Reference forensics: learn why the story works

## Intent

A reference folder may contain formats you recognise and ones you don't. Treat **every video as its own narrative system**—analyse it fully before imposing any category on it. Categories emerge from the evidence; they are not assigned from a predefined list. Study genuinely comparable cohorts once categories have been discovered. The objective is transferable knowledge about *audience experience*, not a copyable outline. A user-found viral video is a strong creative reference, not proof that a specific zoom or hook caused its views.

## Intake, audio and visual coverage

Use `static_core.py init`, `scan`, `prepare --dry-run`, then `prepare`. Never skip Whisper merely because speech is present in auto-captions. Faster-Whisper with word timestamps, VAD, and original source audio creates `10-media/V###/transcript.json` plus `.txt` (when available). Listen to the video yourself; repair/annotate uncertain names, numerals, quotes, jokes, irony, tonal delivery and sound-only context. Whisper is **an imperfect observation aid**, not an authority on dialogue. For silent clips, mark no audio; for a failed transcribe mark *unknown/unprocessed*, not “no speech.”

Visual pass: 5 sampled frames/sec is broad semantic coverage; read it as temporal sequence, not random isolated thumbnails. To understand a cut, reveal, text animation, camera move or split-second joke, seek into the original video and use full-native-FPS extraction for the specific reference (`prepare --ids V### --full-fps`) or a narrow decoded segment. `--full-fps` can create enormous files for long videos: plan space and inspect in digestible ranges. Important for 30/60 fps reference edits: measure actual frame-to-frame changes; a contact sheet is only a coarse map. Retain timestamps and original frame order. Never assert that examining a subset equals reviewing every native frame.

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

## Cross-video synthesis without niche pollution

Each reference can have multiple niche tags but must have a primary `story_form`. Distinguish topical niche (“military history”) from story form (“decision-under-pressure reconstruction”) from art style (“charcoal maps”). Runtime is measured by ffprobe, not estimated from cards. Use `cohorts`: it reports median/mean/min/max and warns on high spread. **A combined average over five 40-second explainers and five 15-minute history videos is invalid as the Standard length of either.** Even 8-minute and 35-minute history videos may form separate runtime families. Provide comparable IDs in the length lock.

When niche or story_form labels vary across cards for what are clearly comparable videos (e.g. one agent wrote `"military history narrative"`, another `"military history"`), assign an explicit `cohort_id` (a stable lowercase slug you choose, e.g. `long-military-history`) to the relevant cards. Any cards sharing a `cohort_id` form their own group in the `cohorts` output and can be used directly in `length --cohort-id` without matching niche/story_form strings.

After all cards, create `20-analysis/niche-synthesis.md`: one chapter per niche with (a) primary references and durations, (b) observed audience experiences, (c) confidence and disagreement across references, (d) specific *story engine* candidates, (e) medium/style choices and limits, (f) pacing ranges for that audience, (g) ways to adapt structural techniques borrowed from another niche, with an explanation of the trade-off. An animated graphic from a short how-to may help a 20-minute strategic history explanation; its aggressive pacing probably should not be copied.

**Outcome:** The user sees distinct creative directions rather than a generic count of references. After picking a direction, derive a **creative profile** (`20-analysis/creative-profiles/[cluster-slug].md`) from the synthesis—what appears to work for that audience, what weaknesses exist, and what creative territory remains unexplored. See §02 for the profile structure. The writer gains *permission to be original*; source titles, names, jokes, voice clones or watermark/overlay text do not get repeated in the new video's final creative work.


Sampled frame filenames have a `frame-index.json` with **nominal** time slots (0.2 s apart at 5 fps). Those are approximate, not original source PTS. For exact transitions or frame-accurate claims, open the original and inspect a native-frame window; never assert precise source timings from a nominal index.
