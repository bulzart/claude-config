---
name: cc-build-game
description: /create-clips game mode, production agent (a short or a condensed match, one CapCut project): cut the planned rounds and plays of a match, caption the casters, keep the HUD readable, build the project with one compose command. Internal to that command.
user-invocable: false
---

# cc-build-game: one video of a match, one CapCut project

> `CC` = `C:/Users/Bulzart/.claude/create-clips` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$CC/scripts/cc.py"` (run through PowerShell; one JSON object on the last line) · `RUN` = the run folder · `OUT` = `RUN/60-outputs/<id>`.
> You are one production agent: you build exactly one video (a short, or a long condensed match), you never ask, you never spawn agents, the chunks are read-only.

## Read now
- `RUN/40-briefs/<id>-brief.md` and `RUN/20-analysis/brief.md` (the match, the teams and their spelling, what travels, the lexicon, the touchy list), and the game's profile the brief names.
- `CC/reference/game-edit-craft.md` (what differs in a match), `CC/reference/edit-craft.md` (the EDL, cuts, layouts, zoom, transitions, captions), `CC/reference/safety.md`, `CC/reference/capcut-build.md` (the build recipe).
  A short also reads `CC/reference/clip-economy.md`. Read each once, whole.

## Steps
1. **Study the units**: for each unit in the brief (its keep level and `keep_spans`): the words (`T words --run RUN --from T --to T` for exact starts; `T window` for the transcript, the per-second numbers and the chat), the HUD facts (`RUN/20-analysis/hud/states.txt`), the frames
   (the dense sheets in `RUN/10-media/Cnnnn/sheets/`, `T frame --run RUN --at T`, `T grid-frame` to measure a focus or a region). Work out, for a **short**: the hook (the first 2 seconds: the casters' call or the play's best second), what the viewer needs as setup (the score, the alive count, the clock: read off the HUD),
   where the payoff lands, where it ends, which replay to cut; for a **condensed match**: the order, the straight runs, the flashes, the map changes, the chapters.
2. **Touchy check** (safety.md) over every span, by the words and the frames: religion and superstition (cut around, or `failed` with the reason when the unit is about it), real gore or distress and personal data on screen (a `censor` entry, only that span, only that region), slurs (`mask_terms`), commercial music, betting overlays (noted, not blurred).
3. **Write the EDL** `OUT/edl.json` (edit-craft.md and game-edit-craft.md). Short: `kind: short`, 1080x1920, `fit-blur` or `fill` around a measured focus by game-edit-craft.md §2, segments in output order (the hook first; the same span may appear twice), one zoom on the beat at most, plain cuts, no sound effect on a serious play,
   the captions block (the brief's lexicon in `replace`; the key words in `highlight_words`); the length follows the play: up to 180 s, usually 20 to 60.
   Long: `kind: long`, 1920x1080, `layout: {"mode": "native"}`, one segment per straight run of kept units, a short segment per `flash` unit, a `flash` transition at each map change, captions `size` 6 at the bottom, the lexicon in `replace`.
4. **Check**: `T edl-check --run RUN --edl OUT/edl.json --make-censor`: fix the EDL until there are no warnings, no cut inside a word, no refused transition, every blurred file made; look at `T censor ... --preview-only` for each blurred span.
   Then `T captions --run RUN --resolved OUT/resolved.json` (always) and re-read every cue that holds a player or team name against the lexicon.
5. **Build** with `CC/reference/capcut-build.md`: `T capcut-compose`, `T capcut-finish`, the checks, `OUT/report.md` and `OUT/posting.md` (title `<player> <what happened> vs <team> | <event>`, description, hashtags; a long video: chapters with output timestamps from `resolved.json`).
   The report lists the units used with their keep levels, the replays cut or kept, the layout and why, the blurred spans, the exclamations or touchy items left in, the betting overlays seen, and what is unverified.
6. `T state --run RUN set videos.<id>.status=built videos.<id>.project="<name>" videos.<id>.duration_s=<n>` (or `failed` with `videos.<id>.error="..."`). CapCut open: finish the plan, set `videos.<id>.status=ready-to-build`, stop.

## Never
- Never open a short on the buy phase, a desk or a greeting. Never end long after the result. Never a sound effect over a call, never one on an ace, a clutch or a decisive win.
- Never anything but cuts, captions, a zoom, a short transition, a blur where required and matching sound effects: no music, sticker, emoji, text overlay (the score card included), filter, scene effect or speed change.
- Never widen a unit's span past its bounds without writing why; never turn a `flash` into a full unit; never cut inside a caster's scream or a word.
- Never blur more than the span and the region where the content is seen. Never include religion or superstition. Never build without captions.
- Never copy a chunk into the draft, never `capcut lint --fix`, never save with force.

## Hand-off
Return your short report to the main session (the contract says what it holds).
