# 05 — Narration, sound and CapCut: build the actual long-form watch

## Voice is an actor, not an audiobook metronome

The narrator should sound like a person who understands and *cares* about the subject. Delivery must track what the viewer is discovering: animated when an insight is surprising, restrained when a human consequence lands, clear in explanations, conversational around ordinary examples. Vary phrasing and pauses naturally. Do not insert monotonous sentence-ending rises, repetitive emphases, forced inspirational intonation or a dramatic growl for every fact. The script is written natively for the target language, not word-for-word translation from an English draft. Dates, names, foreign places and uncommon terms are previewed and pronunciation-corrected.

A channel/run uses a consistent narrator persona and visual identity; different **videos** may have distinct emotional routes and spoken languages. One narrator may need more dynamic delivery for an inventive science topic than for reflective history. Pick voice/model only once when stable; if the voice cannot handle the language/topic, explain a necessary change.

## ElevenLabs process; hard stop on partial narration

1. **Calibrate.** Use a brief paid sample of the intended voice/model only after confirming credit availability. Listen for natural pacing, pronunciation, emotional range and suitability. Record actual WPM/pauses in the video script. Long-form TTS quality is judged after listening, not by “the API returned bytes.” Use supported model/voice/language settings and current provider documentation.
2. **Preflight.** `plan-check` must pass. Run `static_core.py tts --run "RUN" --video NN --voice-id ID --model-id eleven_v4` **without** `--execute`: displays all text chunks and total planned characters; make sure your account has sufficient credits. The script does not request or report your API key. Check the model's actual capability, cost and subscription balance with ElevenLabs before initiating billed calls. The command uses current-known model text limits but must not assume subscription entitlements. When `--execute` is chosen, it first requests subscription allowance (`GET /v1/user/subscription`) and checks the **entire ungenerated remainder plus 15% character reserve** before making the first billable call. This is only a floor based on reported character allowance, **not a guarantee about credit conversion or model-specific cost**. Independently verify sufficient actual credits, API-key limits, voice/model access and any overage settings. An unavailable/insufficient balance stops before charges; you may deliberately adjust `--credit-safety-factor` between 1.0 and 3.0, but never bypass actual-balance verification.
3. **Produce.** After the user has accepted the billed production, set `ELEVENLABS_API_KEY` securely in the terminal environment and repeat with `--execute`. The tool generates contiguous, line-indexed parts with previous/next text continuity hints; it maintains `50-audio/video-NN/manifest.json`, preserves successful chunks for resuming, and concatenates them to `narration.wav` only after all parts are done. Never put the key in JSON, the ZIP, logs, scripts or `CLAUDE.md`.
4. **Check.** Run `audio-check --run "RUN" --video NN`; it verifies all script lines represented, each audio part exists, a complete manifest, joined WAV and duration against locked target. An error, partial voice, credit cutoff, missing chunk, two-minute result for a ten-minute lock, or incomplete source line is **blocking**. Do not rush into images/CapCut using what exists. Fix the script pacing/voice if its generated duration genuinely differs; rewrite for additional *meaning* if too short and regenerate affected parts after reconciling the manifest. A failed recording is *in progress*, not a shorter completed deliverable.
5. **Quality listen.** The duration and file checks cannot hear incorrect words, breaths, fake enthusiasm, unnatural joins, strange emphasis or repetitive prosody. Listen to all joins, the first minute, turning points, foreign names and conclusion. Acknowledge that ElevenLabs does not guarantee deterministic output or exact duration from a character count. Re-record only necessary passages with approvals/credit accounting.

Supported backend: ElevenLabs `POST /v1/text-to-speech/:voice_id`, text/model ID, optional `previous_text` and `next_text`. Model limits vary; never make up a valid voice ID or assume a specific chosen model is accessible. The package intentionally leaves TTS `--execute` off by default so agents do not spend unexpectedly. Each output has an auditable status; a credit-exhausted partial result never becomes “final.”

## Music and layered sound

Use an instrumental bed when it suits the niche/story and adds value. For historical reflection, it may be almost subliminal; for an exciting reconstruction, use a gradual texture change around meaningful turns; for tutorials, clarity often beats score. Never drown speech. Distinguish neutral atmosphere, story-world sound, illustrative SFX, and musical punctuation. Silence can be an intentional dramatic tool. If using ACE-Step 1.5, ensure its environment exists and output is instrumental; validate duration, clipping, license and whether loops sound repetitive. Never fabricate unavailable sound layers. Keep an audible narration bed with consistent loudness across chapters and on small speakers.

## Editing into CapCut

The picture is generated as *clean stills*. Add editable captions, arrows, highlights, chapter cards, lower thirds, diagrams, labels, controlled zoom/crop, simple wipes and optional licensed overlays in CapCut **only when helpful**. Social media captions/badges/emoji are not defaults. No static rule requires constant movement; an image can hold when it carries thought. Resist transitions that create discontinuities; vary macro shot family because a narrative turns, not just because a timer expired.

Use the real connected CapCut MCP and CLI after discovering their actual available tool names and schema. Typical actions in the user's existing setup may include listing drafts, adding image/audio/text, creating tracks, setting segment properties, adding keyframes and transitions, reading timeline, validating and saving. Do **not** fabricate tool calls or assume there is a CapCut render/export API. When no CapCut export tool is accessible, produce a **valid editable CapCut project** and explicitly explain the manual export needed. If local CapCut CLI fails, use an available supported route or stop with a clear blocker; never call a JSON manifest an exported edit.

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
