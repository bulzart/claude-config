# Edit craft: cuts, layouts, zoom, transitions, sound effects, captions

The edit has four tools and nothing else: **cuts**, **captions** (when the run's captions setting is on, which is the default), **VFX** (zoom, a short transition, a blur where `safety.md` says so) and **sound effects** that match the situation. No drawings, no stickers, no emoji, no music bed.
You write the edit as an EDL (`60-outputs/<id>/edl.json`); `cc.py edl-check` resolves it into the CapCut plan and tells you facts about every cut.

## The EDL (schema `cc-edl/1`; times are rec time)
```json
{"schema": "cc-edl/1", "video": "S03", "kind": "short",
 "canvas": {"width": 1080, "height": 1920, "fps": 30},
 "layout": {"mode": "fill", "focus": [0.5, 0.5]},
 "segments": [
  {"id": "s1", "rec_from": 3941.0, "rec_to": 3944.0, "note": "cold-open teaser of the payoff"},
  {"id": "s2", "rec_from": 3890.0, "rec_to": 3950.5, "speed": 1.0, "volume": 1.0,
   "layout": {"mode": "fill", "focus": [0.3, 0.45]},
   "zoom": [{"at": 51.2, "to": 1.18, "in": 0.2, "hold": 1.2, "out": 0.25, "focus": [0.3, 0.4]}],
   "transition_in": {"slug": "flash", "dur": 0.2},
   "censor": [{"rec_from": 3901.0, "rec_to": 3908.5, "region": [0.55, 0.1, 0.4, 0.45], "style": "blur", "why": "gore in the video he is watching"}]}
 ],
 "sfx": [{"name": "vine-boom", "at": {"seg": "s2", "t": 51.3}, "volume": 0.7, "why": "lands on the reveal"}],
 "captions": {"size": 15, "y_rel": 0.66, "max_words": 3, "case": "upper", "highlight_words": ["wild"], "replace": [["Kai Sinat", "Kai Cenat"]], "mask_terms": []}}
```
- A segment is a span of the stream; the output is the segments in order. The same span may appear twice (a cold open, a callback). `zoom.at` and `sfx.at.t` are seconds from the segment's start in the output.
- `edl-check` writes `resolved.json` (the pieces, per chunk), `mcp-plan.json` (the exact CapCut tool calls), `finish.json` (zoom keys, transitions, captions options) and returns facts: every cut with whether it lands inside a word and the gap to the nearest word,
  warnings (a hole in the recording, a missing blurred file, a refused transition), the duration.

## Cuts
- Find exact points with `cc.py words --run RUN --from T --to T` (every word with its start time). Cut in the breath between words: start about 0.1 to 0.2 s before the first word, end about 0.2 to 0.3 s after the last (let a laugh land).
  `edl-check` says `cut_in_inside_word` / `cut_out_inside_word`: both must be null.
- Open on the hook (clip-economy.md); remove dead air, "um", reading chat nobody needs. Keep a reaction that is the joke even if it is silent.
- A cut never changes what someone means. A short ends 0.3 to 1 s after the payoff.
- A cut across two chunks is fine (the two chunk files meet on the same frame); across a hole in the recording (`gap_before_s` in the chunk table) it is a jump: avoid it inside one beat.
- `speed` stays 1.0 unless the brief asks (no speed ramps in v1).

## Layout (shorts are 9:16, long videos are 16:9)
The source is 16:9 (1280x720 or 1920x1080). A short needs a decision about the frame:
- **fill** (the default): the crop around `focus` (fractions of the source: x, y of the middle of what you want) fills the 9:16 canvas. Use `cc.py layout-calc` or let `edl-check` compute it; it tells which part of the source is visible (`visible_x`).
  Look at the real frame first: `cc.py grid-frame --run RUN --at T`. For a facecam streamer the focus is the face; for a game with a facecam in a corner, cut between the gameplay focus and the facecam focus on the beats; for just-chatting the face.
  A 9:16 crop is a third of the width: from a 720p source it is a 405x720 picture enlarged to 1080x1920: soft. Say so in the report when the source is 720p; do not zoom further than needed.
- **fit-blur**: the whole 16:9 frame in the middle of the canvas on a blurred copy of itself (`"layout": {"mode": "fit-blur", "y_offset": 0.1}`; the background blur is capcut-cli's `bg-blur`, NOT verified on this PC's CapCut 9.7: look at it in the first project and fall back to fill if it does not show).
  Use it when the whole frame is the content (a screen with chat, two people at two ends) and the crop would lose the point.
- Long videos: `native` (the 16:9 frame as it is); a zoom is the only change.

## Zoom and transitions (the only VFX; use sparingly, every one must be motivated)
- **Zoom** (a punch-in on the line or face that carries the joke): `to` 1.10 to 1.25, `in` 0.15 to 0.25 s, `hold` as long as the beat, `out` 0.2 to 0.3 s. At most one every 6 to 8 s in a short; none in most long videos (one on a big beat is enough). `focus` makes it push in toward a point (the face), not the middle.
- **Transitions**: only slugs the CapCut check drew on this PC and that are not Pro. Good for fast clip cuts: `flash`, `white-flash`, `white-flash-1`, `radial-blur`, `horizontal-blur`, `vertical-blur-ii`, `shake-3`, `twinkle-zoom`, `glitch`, `color-glitch`, `shutter`, `mix`, `black-fade` (0.15 to 0.35 s). A plain cut is the default and usually best;
  a transition belongs where the topic or the energy changes between two segments, and goes in the EDL as `transition_in` of the second segment. `edl-check` refuses a slug the catalogue does not show (`AWL data/capcut-catalogue.md`).
- Not used: scene effects, filters, masks, stickers, text overlays other than captions, speed changes, overlays. If the brief truly needs one, say it is unverified on this PC and flag it in the report.

## Sound effects (the library: `RUN/30-assets/sfx.md`, run `cc.py sfx-scan --run RUN` once)
They are seasoning that matches the situation, never decoration. The names are the file names (meme sounds mostly: vine-boom, bruh, among-us, and some neutral ones: whoosh, riser, ding, clock).
| Situation | What fits | Rule |
|---|---|---|
| A reveal or an explosion of a reaction | an impact (boom, hit), a record scratch on a wrong answer | put it on the beat, not before; volume 0.6 to 0.9 |
| A zoom or a transition | a whoosh | shorter than the move |
| A fail, a wrong move | a comedic meme sound that matches the energy | only when the streamer is also laughing about it |
| A build-up | a riser or ticking | ends at the payoff |
| A tragic or heavy moment | none | never a meme sound on real pain, loss or a serious subject |
- Never over a word that carries the joke; leave the speech clean. About one per 8 to 10 s of a short at most, far fewer in long videos. Never a sound with a religious feel (bells, choir, chant, amen). Volume relative to the speech: the voice must stay on top.

## Captions (when the run's captions setting is on, which is the default: on every second of speech)
The user picks captions or no captions at the start of the command; it is `state.json -> captions` (`on` or `off`; a run without the key is `on`; `T state --run RUN get captions`). **With captions OFF** the EDL has no `captions` block, `cc.py captions` answers "skipped" and writes nothing,
`capcut-finish` adds no caption track, font or entrance (`finish.json` carries `captions.enabled: false`), the lexicon and every cue check are not needed, and a slur that is spoken stays audible (nothing masks it, no audio is edited): the plan cuts around it. Everything below is for captions ON.
The captions come from the Whisper words of the pieces (`cc.py captions`), 1 to 4 words per cue in a short, a line of up to 7 words in a long video.
- Shorts: Montserrat Bold, size 15 (about 93 px on 1080 wide; CapCut size = px / (0.00575 x canvas width)), white with a black outline, around 66% down (`y_rel` 0.66), upper case, the key word in gold (`highlight_words`), a 0.1 s fade-in.
- Long: Montserrat Bold, size 6, bottom (`y_rel` 0.88), normal case, no intro.
- Names and terms: `replace` pairs from `lexicon.json` fix Whisper's spelling. `mask_terms` masks the hardest words (first letter then stars).
- A stretch of more than 4 s with no speech and no caption is reported by `cc.py captions` (`silent_stretches_over_4s`): decide whether it is fine (a visual beat) or needs a short text line (add it by hand in the report, not with a new tool).
- No emoji in any text. The captions never cover the face or the key action (move `y_rel` for the whole video if they do).

## Check before you build
`edl-check` returns: no warnings, no missing blurred files, no refused transitions, every cut clean, the duration inside the brief (a short at most 180 s), the captions' silent stretches understood (captions on), the SFX not on speech, nothing religious or superstitious in the transcript words of the spans (`safety.md`).
