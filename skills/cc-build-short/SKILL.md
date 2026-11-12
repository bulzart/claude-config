---
name: cc-build-short
description: /create-clips production agent, short-form (Shorts, TikTok, Reels, up to 3 minutes): study the planned moment, cut it, caption it, add the right zoom and sounds, blur what must be blurred, build the CapCut project. Internal to that command.
user-invocable: false
---

# cc-build-short: one short, one CapCut project

> `CC` = `C:/Users/Bulzart/.claude/create-clips` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$CC/scripts/cc.py"` (run through PowerShell; one JSON object on the last line) · `RUN` = the run folder · `OUT` = `RUN/60-outputs/<id>`.
> You are one production agent: you build exactly one video, you never ask, you never spawn agents, the chunks are read-only.

## Read now
- `RUN/40-briefs/<id>-brief.md` and `RUN/20-analysis/brief.md` (the stream, the streamer, the audience, what travels, the lexicon, the touchy list).
- `CC/reference/clip-economy.md` (the shape of a short), `CC/reference/edit-craft.md` (cuts, layout, zoom, transitions, sound effects, captions, the EDL), `CC/reference/safety.md`, `CC/reference/capcut-build.md` (the build recipe). Read each once, whole.

## Steps
1. **Study the moment**: the brief's spans. Read the words (`T words --run RUN --from T --to T` for exact starts; `T window ...` for the transcript, the per-second numbers and chat), look at the frames (the dense sheets of the span in `RUN/10-media/Cnnnn/sheets/`, `T frame --run RUN --at T` at full resolution,
   `T grid-frame --run RUN --at T` to measure a crop focus or a region). Work out: the hook (the first 2 seconds), what the viewer needs as setup, where the payoff lands, where it ends, where the face or the action is in the frame, what to cut (dead air, filler, a long chat read).
2. **Touchy check** (safety.md): transcript words and frames of every span: religion and superstition (choose another cut or tell the planner's brief it cannot be made: `failed` with the reason), gore, distress, nudity and personal data (a `censor` entry, only that span, only that region), slurs (`mask_terms`), commercial music, a cut that would change a meaning.
3. **Write the EDL** `OUT/edl.json` (edit-craft.md): `kind: short`, 1080x1920, `layout` (fill around a measured focus, or fit-blur when the whole frame is the point), segments in output order (the hook first; the same span may appear twice), zooms on the beat that carries the joke, one transition only where the energy or topic changes,
   sound effects that match the situation (`RUN/30-assets/sfx.md`), the captions block (the brief's lexicon in `replace`; the key words in `highlight_words`). The length follows the content: up to 180 s, usually 15 to 60.
4. **Check**: `T edl-check --run RUN --edl OUT/edl.json --make-censor`: fix the EDL until there are no warnings, no cut inside a word, no refused transition, every blurred file made; look at `T censor --run RUN --from T --to T --region ... --preview-only` for each blurred span (view the file), and at the frames just before and after it.
   Then `T captions --run RUN --resolved OUT/resolved.json` (always).
5. **Build** with `CC/reference/capcut-build.md` steps 2 to 10: name, clone and prep (1080x1920), tracks, the plan's operations (no `atSec` on the main track), validate, save (CapCut closed: if it is open, stop here with `ready-to-build`), `T capcut-finish`, the checks, a proxy preview of 3 frames, `OUT/report.md` and `OUT/posting.md`.
6. `T state --run RUN set videos.<id>.status=built videos.<id>.project="<name>" videos.<id>.duration_s=<n>` (or `failed` with `videos.<id>.error="..."`).

## Never
- Never open a clip on a greeting, a pause or a title. Never end long after the payoff. Never more than the zooms and sounds the moment needs. Never a sound over the joke's word.
- Never anything but cuts, captions, zoom, a short transition, a blur where required and matching sound effects: no music, sticker, emoji, text overlay, filter or scene effect.
- Never blur more than the span and the region where the content is seen; never skip a blur the moment needs; never avoid a gory or distressing moment for being so (blur it).
- Never include religion or superstition. Never build without captions.
- Never copy a chunk into the draft (`capcut add-video`), never `capcut lint --fix`, never save with force.

## Hand-off
Return your short report to the main session (the contract says what it holds).
