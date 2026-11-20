# 05 — Narration, sound and CapCut: build the actual long-form watch

## Voice is an actor, not an audiobook metronome

The narrator should sound like a person who understands and *cares* about the subject. Delivery must track what the viewer is discovering: animated when an insight is surprising, restrained when a human consequence lands, clear in explanations, conversational around ordinary examples. Vary phrasing and pauses naturally. Do not insert monotonous sentence-ending rises, repetitive emphases, forced inspirational intonation or a dramatic growl for every fact. The script is written natively for the target language, not word-for-word translation from an English draft. Dates, names, foreign places and uncommon terms are previewed and pronunciation-corrected.

The narrator's persona comes from the locked treatment (`direction.json`, 10): who is talking, their relationship to the viewer, their energy range and licence for humour or emotion. A channel/run uses one voice (the first video's treatment chooses it; later videos direct their delivery within it, or change it deliberately with `voice-pick --replace`); different **videos** may have distinct emotional routes and spoken languages. One narrator may need more dynamic delivery for an inventive science topic than for reflective history. Pick voice/model only once when stable; if the voice cannot handle the language/topic, explain a necessary change.

## Inline audio tags: chosen by the story, from the whole catalogue

`STUDIO/data/elevenlabs-audio-tags.json` holds every tag ElevenLabs documents for Eleven v4 / v4 Turbo (131, from its three official pages; the file names them and says when to re-read them). Each entry gives what the tag does, an example, a pipeline status, and for pauses and reactions an approximate time cost. The file also says how tags behave and what this setup has measured. Statuses: `usable` and `use_with_care` are the agents' call; `not_for_narration` is excluded by a standing rule (distress, crude, sound effects, national accents, dialogue; the reasons are in the file), and plan-check refuses it. A tag the file does not list is allowed: the vocabulary is open (`[amused, conspiratorial]`, `[hushed, as if not to wake someone]`: whatever the treatment's narrator needs), and it is judged on the calibration part: `narration-measure` lists any tag that made no measurable pause and `delivery.json` shows whether the voice moved where the tag asked; the user may also listen (optional).

The catalogue is information, not a recipe. No tag is ever required, and there is no quota. Who decides, and from what:

1. **The creative direction** (`direction.json`: the strategy's `sound_and_breath`, the locked treatment's `narrator` and `writing_voice`, and each beat's `narration_direction` in the beat map) says how *this* narration should sound and breathe: its register, where it slows, which moments must land. That is decided for this story, not for the niche in general.
2. **The references' measured delivery.** `pace-profile --run "RUN" --video NN` gives their WPM and how they pause (how often, the typical and the longest pause). It uses the same yardstick `narration-measure` later applies to our voice. If the comparable narrators never pause longer than about 2 s, a `[long pause]` (about 7 s measured here) is a foreign body however dramatic the line. A choice that departs from them on purpose is a creative decision, and the review says why.
3. **The script writer** (03) writes each chosen tag inline in the line's `text`, where it acts: before the words it colours, or at a line start or end for a pause. It is sent exactly as written. One line per tag goes under **"Delivery and tags"** in `editorial-review.md`: the line, the tag, why this moment, and what the references do at comparable moments.
4. **The audio stage executes** what the script carries. It never adds, moves or drops a tag. A tag that misfires on the calibration part goes back to the script stage as a finding.

How tags work (the catalogue's `how_tags_behave`, plus what was measured here):

- A tag carries through its line. Place a new one only where the delivery changes, and use one per clause. Put several qualities in one bracket (`[tense, cautious]`), never contrasting tags on the same words.
- Tags depend on the voice. A delivery outside a voice's training data may be ignored, rendered oddly or read aloud, and a serious register may refuse playful tags. `voice-probe` (a short passage) and the calibration part are where this is heard.
- **Pace tags do not set the video's pace.** Measured: a pace tag had no lasting effect over a real part. The pace belongs to the voice, so length is managed with words and holds.
- **Pause tags cost real time inside the narration**: about 2 s for `[pause]`, 1–2 s for `[slightly pause]` and 6–8 s for `[long pause]` here. They are also fixed once recorded. plan-check adds every tag's time to the forecast: the voice's measured cost once `narration-measure` has one, the catalogue's approximate cost before that.
- Punctuation already does much of the work with no tag at all: a comma, an ellipsis, a dash, a line break, a capitalised word.

**Pauses: one decision, two ways to realise it.** A pause the story wants that is longer than the voice's own gap after a line (about 0.4 s) is written in the script as `pause_after_s` with `pause_via` (03):

- `tag`: a pause tag in the sent text, so the voice performs the pause. It costs credits and is fixed once recorded.
- `edit`: a hold. `retime-shots` inserts silence there and holds the picture. It is exact, free, and adjustable after recording.

plan-check refuses a pause over 1 s that names neither.

## Pick the voice: five candidates, chosen for this story's narrator

1. `static_core.py voice-candidates --run "RUN" --video NN --count 5 [--search TEXT] [--design N] [--design-description "..."] [--design-text "..."]`: up to 5 candidates, free from the account's voices (`--design 0`) and/or billed Voice Design (`--design N`). The description states the narrator the locked treatment needs: character, register, age, accent and delivery. Each preview is transcribed and its `preview_wpm` recorded, but **a preview does not predict the real pace**. Measured here: a preview at 195 WPM read 180 on a real part; a 209-WPM human sample read 178; pace wording in the description had no steady effect. No agent here can listen. Each candidate also gets `measured_delivery` (pitch range and movement, loudness contrast: a short sample, indicative only), on the same yardstick as the references' `av-profile`. Choose for the treatment's narrator from the description and labels, what the preview said, and that measured delivery; list the files for the user, who may listen and overrule (optional, never a gate). Earlier rounds are kept as `candidates-<time>.json`.
2. `static_core.py voice-pick --run "RUN" --video NN --voice-id ID --name "..." --settings '{...}'`: locks one voice for the whole run, every video and language (`--replace` deliberately changes it). A Voice Design pick is first saved to the library; a voice that is already saved is used as it is. `preview_wpm` is kept only as information, and the script is never sized on it.
3. `static_core.py voice-probe ... --text "a real passage with its [tags]" --settings '{...}'` (optional, short, billed): for the user to hear the voice, and for the agents to measure it (`measured_delivery`) and see which tags came back as words (read aloud). It lists tags it may have read aloud. Its WPM is not the real pace.
4. **Settings.** Only `eleven_v4` and `eleven_v4_turbo` are used (the user's standing rule; the tool refuses any other model). Both take only `stability` and `similarity_boost` (their own capability flags: no style, no speaker boost), and speed is not used. Never leave `--settings` empty: the bare default `stability=0.5` widens variability between generations. Match it to the register: a grave, restrained narrator wants more stability.
5. **What this setup measured (2026-11-19).** Every voice, register and setting tried on v4 and v4 Turbo converged to about 175–188 WPM on real parts, while that run's human reference narrators measured 195–206. The voice's measured pace is a fact of production: the script is sized to it. Re-measure on each new run, since it may change.

## ElevenLabs process; hard stop on partial narration

1. **Preflight.** `plan-check` must pass (tags valid, pauses realised, content flags answered, forecast in range). Run `static_core.py tts --run "RUN" --video NN --voice-id ID --model-id eleven_v4 --settings '{"stability":S,"similarity_boost":M}'` **without** `--execute`: displays all text chunks and total planned characters; make sure your account has sufficient credits. The script does not request or report your API key. Check the model's actual capability, cost and subscription balance with ElevenLabs before initiating billed calls. When `--execute` is chosen, it first requests subscription allowance (`GET /v1/user/subscription`) and checks the **entire ungenerated remainder plus 15% character reserve** before making the first billable call — a floor based on reported character allowance, **not a guarantee about credit conversion or model-specific cost**: this session, real billed usage ran consistently at ~40% of raw characters sent across four independent measurements, despite the model's documented `character_cost_multiplier` being 1.0 (unexplained — possibly a time-limited promotional rate; re-verify, never assume it still holds). Verify a ratio yourself from a call's own subscription before/after delta before using `--assume-cost-ratio` (0.1-1.0, default 1.0) to adjust the preflight's required balance — always auditable in the manifest, never guessed. An unavailable/insufficient balance stops before charges.
2. **Calibrate on the first real part, never a throwaway sample.** Run `static_core.py tts ... --max-parts 1 --execute`, which records only part 1 (a real ~8,000-character part) and stops. The tool refuses to record several parts before this voice, model and settings has a real measured pace (`--skip-calibration` overrides). Then:
   - `static_core.py narration-measure --run "RUN" --video NN` uses the same Whisper call and formula as the references. It reports the real WPM, the natural gap after each line, what each tag really cost, the pause profile next to the references', and how well the words matched the script. From 300+ words it writes `60-voice/voice-lock.json` → `measured`. It also writes `delivery.json`: how the voice moves beat by beat (pitch range and movement, loudness contrast, rate), next to what each beat asked for and to the references' numbers. A beat asked to lift that measures flat is rewritten in the parts not yet recorded (10 §5).
   - `plan-check`: its `real_forecast_s` (narration plus edit holds) must land inside `export_window_s`. If it doesn't, change the *words* of the parts not yet recorded, or the holds. Never change the delivery, and never the recorded audio. Listen to part 1 too: voice, tags, names.
3. **Produce the rest.** Run the same command without `--max-parts`. Finished parts are kept and never re-billed. Parts carry previous/next text hints for continuity, and `narration.wav` is joined only when every part exists. Never put the key in JSON, the ZIP, logs, scripts or `CLAUDE.md`.
4. **Changing lines after recording.** Recorded parts keep their line boundaries, so editing a line changes only the part that holds it. The dry run lists `changed_recorded_parts` and their characters, and `tts ... --rerecord-changed --execute` re-records just those (old takes move to `superseded/`, never deleted). Adding or removing lines breaks the boundaries and forces a full re-record (`--rechunk --archive-existing`), so once audio exists, rewrite lines rather than add or delete them. Another voice, model or language: `--archive-existing`.
5. **Check.** `audio-check` covers:
   - every line recorded, the hashes and a complete join;
   - the duration against the audio tolerance;
   - **narration plus the planned edit holds inside the export window.** The picture can't be shorter than the narration, and `export-check` holds the export to a tighter window. A narration that fits only the audio tolerance fails here, now, rather than at export.

   An error, a partial voice, a credit cutoff or a missing part is **blocking**: a failed recording is in progress, not a shorter deliverable. Then run `narration-measure` on the complete narration: its line times feed `retime-shots`.
6. **Quality listen.** No agent here can hear audio. What stands in for listening: the word alignment (missing or extra words), tags that made no measurable pause, and `delivery.json` (flat or rushed stretches per beat, next to what each beat asked for). What only ears catch (a mispronounced name, a breath, fake enthusiasm, a bad join, strange emphasis, noise) is offered to the user as an optional listening list with exact times, never a gate. The checks cannot hear wrong words, breaths, fake enthusiasm, joins, strange emphasis or noise. Listen to all joins, the first minute, the turning points, foreign names, **every tag** (did it land as delivery, not read aloud?) and the ending. ElevenLabs output is not deterministic. Re-record only the parts that need it, with approval and credit accounting.

Supported backend: ElevenLabs `POST /v1/text-to-speech/:voice_id`, text/model ID, optional `previous_text` and `next_text`. Model limits vary; never make up a valid voice ID or assume a specific chosen model is accessible. The package intentionally leaves TTS `--execute` off by default so agents do not spend unexpectedly. Each output has an auditable status; a credit-exhausted partial result never becomes “final.”

## Music and layered sound

Music and sound carry out the locked treatment's `sound` and each beat's `sound_direction` (beat map): whether there is a bed at all, where it changes, where it drops to silence, what a single sound is for. They are decided there, with the story, not here. Use an instrumental bed when it suits this story and adds value. For instance, a reflective passage may want it almost subliminal, an exciting reconstruction a gradual texture change around meaningful turns, a demonstration clarity over score; the references' measured level under the voice (`av-profile`) shows what their audiences are used to, not what this film must do. Never drown speech. Distinguish neutral atmosphere, story-world sound, illustrative SFX, and musical punctuation. Silence can be an intentional dramatic tool. If using ACE-Step 1.5, ensure its environment exists and output is instrumental; validate duration, clipping, license and whether loops sound repetitive. Never fabricate unavailable sound layers. Keep an audible narration bed with consistent loudness across chapters and on small speakers.

## Editing into CapCut

The picture is generated as *clean stills*. Add editable captions, arrows, highlights, chapter cards, lower thirds, diagrams, labels, controlled zoom/crop, simple wipes and optional licensed overlays in CapCut **only when helpful**. Social media captions/badges/emoji are not defaults. No static rule requires constant movement; an image can hold when it carries thought. Resist transitions that create discontinuities; vary macro shot family because a narrative turns, not just because a timer expired.

Use the real connected CapCut MCP and CLI after discovering their actual available tool names and schema. Typical actions in the user's existing setup may include listing drafts, adding image/audio/text, creating tracks, setting segment properties, adding keyframes and transitions, reading timeline, validating and saving. Do **not** fabricate tool calls or assume there is a CapCut render/export API. When no CapCut export tool is accessible, produce a **valid editable CapCut project** and explicitly explain the manual export needed. If local CapCut CLI fails, use an available supported route or stop with a clear blocker; never call a JSON manifest an exported edit.

On this PC the project is written with `STUDIO/scripts/capcut_tools.py` next to the MCP and capcut-cli; its commands, their order and the files they read are in `STUDIO/reference/09-capcut-toolkit.md`.

**Time the pictures to the real narration before placing them.** The shot plan was written against the planned timings, and the real narration never matches them. `static_core.py retime-shots --run "RUN" --video NN --render-narration` does three things:
- It puts every cut in the silence between the last line of one shot and the first line of the next, from `narration-measure`'s line times.
- It inserts each edit hold (`pause_via: "edit"`) at its line and keeps it on the shot before.
- It rewrites `shot-plan.json`'s `start_s`/`end_s` (the planned values are kept once as `planned_*`) and writes `70-edit/video-NN/edit-plan.json` and `50-audio/video-NN/narration-edit.wav` (the narration with its holds).

The project then places `narration-edit.wav` at 0 (or `narration.wav` when there are no holds) and each still at its shot's times. `timeline-check` flags a project whose end drifted from the edit plan. Shots the retiming made very short or very long are listed in the edit plan's `notes`, for the director to split, merge or keep.

Write `70-edit/video-NN/timeline.json` **derived from the actual CapCut timeline**, not a fictional plan, with `canvas` (e.g. `1920x1080`), `visual_segments` in chronological order, each `{ "start_s": ..., "end_s": ..., "asset_path": "...", "beat_id": "B01", "purpose": "..." }`, and an optional `audio_tracks` array, transitions, labels, note on project path and export status. No section should vanish because only enough pictures/audio were rendered for the opening. The actual last narrated beat and the final held frame must reach the locked story destination. Run:

```bash
python "$HOME/.claude/static-studio/scripts/static_core.py" timeline-check --run "RUN" --video 1
```

It checks contiguous visual range, beat links, story purposes, 16:9 canvas and successful audio gate; it does not substitute for playing through the project. Avoid black tails after the main edit and accidental CapCut “extra two seconds” tracks. A picture can intentionally lead/lag narration; the project duration should still respect the length contract.

## Export is a separate deliverable, with separate proof

Default YouTube landscape 1920×1080 or higher 16:9, 30 fps unless the project actually requires a deliberate alternative. For an accessible `output.mp4`:

```bash
python "$HOME/.claude/static-studio/scripts/static_core.py" export-check \
  --run "RUN" --video 1 --file "C:/path/to/output.mp4" --deep
```

The checker uses `ffprobe` for true exported duration, picture/audio stream presence, size and aspect, plus optional FFmpeg black/silence diagnostics. A diagnostic is a **clue**, not proof of an error (intentional silence/black may be right). Visually inspect opening, cuts, maps and chapter boundaries, listen to audio throughout, sample a few intervals in every chapter and watch the final minute. Verify exact titles/captions/names. Don't declare export verification complete when the file isn't accessible. Record export size, duration, settings and any unresolved issues in `80-deliverables/video-NN-release.md`.

## Publishing package

Provide a small set of title/thumbnail **concepts that truthfully promise the story**, not bait; a polished video description, source credits/licensing, optional chapter timestamps based on actual export, and a practical first-comment idea only if it contributes to discussion. Do not replicate the viral references' titles or thumbnails. YouTube Analytics may inform the next video later, but do not invent CTR, AVD or retention results for this one.
