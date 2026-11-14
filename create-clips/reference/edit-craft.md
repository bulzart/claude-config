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
 "captions": {"highlight_color": "#22AAFF", "y_rel": 0.66, "why": "the stream's blue overlay colour on a dark game scene", "replace": [["Kai Sinat", "Kai Cenat"]], "mask_terms": []}}
```
The captions block is short because the look has defaults (Loupe video 04's look: Luckiest Guy, upper case, the word-box, `size` auto, about 3 words a caption in a short, which the agent may change): only what this video needs is written, never a font (the section "Captions" below).
- A segment is a span of the stream; the output is the segments in order. The same span may appear twice (a cold open, a callback). `zoom.at` and `sfx.at.t` are seconds from the segment's start in the output.
- `edl-check` writes `resolved.json` (the pieces, per chunk), `mcp-plan.json` (the sound-effect lanes and the clips' places), `finish.json` (zoom keys, transitions, captions options) and returns facts: every cut with whether it lands inside a word and the gap to the nearest word,
  warnings (a hole in the recording, a missing blurred file, a refused transition), the duration. `T capcut-build` turns these files into the CapCut project in one composition (capcut-build.md): nothing is added to the project by hand or clip by clip.

## Cuts
- Find exact points with `cc.py words --run RUN --from T --to T` (every word with its start time). Cut in the breath between words: start about 0.1 to 0.2 s before the first word, end about 0.2 to 0.3 s after the last (let a laugh land).
  `edl-check` says `cut_in_inside_word` / `cut_out_inside_word`: both must be null.
- Open on the hook (clip-economy.md); remove dead air, "um", reading chat nobody needs. Keep a reaction that is the joke even if it is silent.
- A cut never changes what someone means. A short ends 0.3 to 1 s after the payoff.
- A cut across two chunks is fine (the two chunk files meet on the same frame); across a hole in the recording (`gap_before_s` in the chunk table) it is a jump: avoid it inside one beat.
- `speed` stays 1.0 unless the brief asks (no speed ramps in v1).

## Layout (shorts are 9:16, long videos are 16:9)
**A short is always 9:16 (1080x1920), whatever the source** (the user, 2026-11-14): its EDL needs no `canvas` (the default is 1080x1920) and never another; `edl-check` warns when a short's canvas is not 9:16 (the check is then not ok) and `capcut-build` lists it as a problem.
When the whole 16:9 frame is the point, `fit-blur` puts it in the middle of the 9:16 canvas on a blurred copy of itself: the canvas stays 9:16 either way. `native` is for long videos.
The source is 16:9 (1280x720 or 1920x1080). A short needs a decision about the frame:
- **fill** (the default): the crop around `focus` (fractions of the source: x, y of the middle of what you want) fills the 9:16 canvas. Use `cc.py layout-calc` or let `edl-check` compute it; it tells which part of the source is visible (`visible_x`).
  Look at the real frame first: `cc.py grid-frame --run RUN --at T`. For a facecam streamer the focus is the face; for a game with a facecam in a corner, cut between the gameplay focus and the facecam focus on the beats; for just-chatting the face.
  A 9:16 crop is a third of the width: from a 720p source it is a 405x720 picture enlarged to 1080x1920: soft. Say so in the report when the source is 720p; do not zoom further than needed.
- **fit-blur**: the whole 16:9 frame in the middle of the canvas on a blurred copy of itself (`"layout": {"mode": "fit-blur", "y_offset": 0.1}`; the background blur is capcut-cli's `bg-blur`, NOT verified on this PC's CapCut 9.7: look at it in the first project and fall back to fill if it does not show).
  Use it when the whole frame is the content (a screen with chat, two people at two ends) and the crop would lose the point.
- Long videos: `native` (the 16:9 frame as it is); a zoom is the only change.

## Zoom and transitions (the only VFX; use sparingly, every one must be motivated)
- **Zoom** (a punch-in on the line or face that carries the joke): `to` 1.10 to 1.25, `in` 0.15 to 0.25 s, `hold` as long as the beat, `out` 0.2 to 0.3 s. How many and how often is the agent's call, with no count and no spacing: in a short, use one wherever there is a beat and something worth pushing in on, and leave it out where there is nothing to push in on or it would feel off (a push-in on a person or an object that is not the point); none in most long videos (one on a big beat is enough). `focus` makes it push in toward a point (the face), not the middle.
- **Transitions**: only slugs the CapCut check drew on this PC and that are not Pro. Good for fast clip cuts: `flash`, `white-flash`, `white-flash-1`, `radial-blur`, `horizontal-blur`, `vertical-blur-ii`, `shake-3`, `twinkle-zoom`, `glitch`, `color-glitch`, `shutter`, `mix`, `black-fade` (0.15 to 0.35 s). A plain cut is the default and usually best;
  a transition belongs where the topic or the energy changes between two segments, and goes in the EDL as `transition_in` of the second segment. `edl-check` refuses a slug the catalogue does not show (`AWL data/capcut-catalogue.md`).
- Not used: scene effects, filters, masks, stickers, text overlays other than captions, speed changes, overlays. If the brief truly needs one, say it is unverified on this PC and flag it in the report.

## Sound effects (the library: `RUN/30-assets/sfx.md`, run `cc.py sfx-scan --run RUN` once)
They match the situation, never decoration, and how many to use is the agent's call: use them where there is room and they fit, leave them out where there is not. The names are the file names (meme sounds mostly: vine-boom, bruh, among-us, and some neutral ones: whoosh, riser, ding, clock).
| Situation | What fits | Rule |
|---|---|---|
| A reveal or an explosion of a reaction | an impact (boom, hit), a record scratch on a wrong answer | put it on the beat, not before; volume 0.6 to 0.9 |
| A zoom or a transition | a whoosh | shorter than the move |
| A fail, a wrong move | a comedic meme sound that matches the energy | only when the streamer is also laughing about it |
| A build-up | a riser or ticking | ends at the payoff |
| A tragic or heavy moment | none | never a meme sound on real pain, loss or a serious subject |
- Never over a word that carries the joke; leave the speech clean. No count and no spacing is set for a short: put them in the gaps and on the beats where one fits, and leave them out where there is no room or it would feel off; far fewer in long videos. Never a sound with a religious feel (bells, choir, chant, amen). Volume relative to the speech: the voice must stay on top.

## Captions (when the run's captions setting is on, which is the default: on every second of speech)
The user picks captions or no captions at the start of the command; it is `state.json -> captions` (`on` or `off`; a run without the key is `on`; `T state --run RUN get captions`). **With captions OFF** the EDL has no `captions` block, `cc.py captions` answers "skipped" and writes nothing,
`capcut-finish` adds no caption track, font or entrance (`finish.json` carries `captions.enabled: false`), the lexicon and every cue check are not needed, and a slur that is spoken stays audible (nothing masks it, no audio is edited): the plan cuts around it. Everything below is for captions ON.
The captions come from the Whisper words of the pieces (`cc.py captions`).

### The look: Loupe video 04's captions (the default, `captions.style: "word-box"`)
The user, 2026-11-13, comparing our frame with that video's (the Loupe run `20261106-063422-static-klein`, video 04): "the highlight is way too off and big in comparison with the fonts, and always use the same font family as they used in that video". So the look is COPIED from that video, not approximated:
**Luckiest Guy, always** (the file `LuckiestGuy-Regular.ttf` in the Loupe fonts folder), **upper case**, white words with a thick black outline (0.18) and a shadow, and the word being spoken on a rounded colour box that moves from word to word (radius 0.3, padding 0.08, sitting 0.15 lower, words 0.55 em apart).
Those box numbers were tuned with the user for that font: CapCut draws a box around the WHOLE LINE of a text (ascent plus descent), so how big the box looks and where it sits depend on the font's metrics. Luckiest Guy has a line of 1.0 em and capitals as tall as its lowercase; Barlow Black (line 1.2 em, small x-height) with the same numbers made a box more than twice the height of the word, sitting off it (the user's screenshot). Hence the font is fixed.
CapCut draws a box behind a whole text only, so the captions are built as ONE CAPCUT TEXT PER WORD AND STATE (`scripts/cc_wordbox.py`): about 2.5 texts per spoken word (a 4-minute video: about 1,900 texts on 15 tracks named `wordcap-<n>-<box|word>[-in]`), the line centred, the box on the spoken word, the others plain.
`style: "plain"` is the older look (one text per caption, key words in `highlight_color` through `highlight_words`) in the same font, outline and shadow; it is also used by itself, with the reason in `resolved.json -> captions.style_reason`, when the captions' language is written without spaces or right to left and when the video has more spoken words than `captions.word_box_max_words` (3000, about 23 minutes of continuous speech: a text per word and state would be tens of thousands of texts; raise the limit in the EDL to force the look).
The EDL's captions block, every key optional (the preset is the default; **no font key**):
`{"highlight_color": "#E02B3A", "y_rel": 0.76, "replace": [["Kerrigan", "karrigan"]], "mask_terms": [], "why": "BLAST red from the broadcast's banners stands out from the sand behind the band"}`
- **The font is never picked per video.** `captions.font_family`, `font_style` and `font_file` exist for ONE reason: a character of the captions that Luckiest Guy cannot draw (it has English, Albanian ë ç, French, Spanish and German letters, digits and punctuation; it has no Slavic or Turkish letters such as š ž č ć đ ğ ş, no Cyrillic, no Greek).
  `cc.py captions` lists `font_missing_glyphs` and says `house_font`; only when that list is not empty name another family (`T fonts --family <part>` lists the families on this PC) and look at the box in the first frame, since its line height differs from the house font's and the box numbers were tuned for Luckiest Guy. Otherwise never.
- **The box colour is the one free choice**: pick it to match the video's appearance, from a frame of the band where the captions will sit and the video's palette (a broadcast's accent, a streamer's brand, the game's UI), so that the white word, its black outline and the box all stay legible; a box close to the picture's own colour vanishes.
  The user's own pick for the run (`captions_color` in `state.json`, given at the start) fills it when the EDL leaves it open. Write the colour read and the reason in `captions.why` and in the report. The orange `#FF7A1A` (Loupe video 04's) is only the fallback.
- **Size: small to normal, for phones and tablets** (the user, 2026-11-13: "neither too small nor too large ... most viewers may be watching from the phone or tablets ... preferably don't use large fonts"). `size: "auto"` puts the font's em at `size_em_pct` = 4.6 percent of the picture's SMALLER side: the same on a 16:9 video (its height) and on a vertical one (its width) and in any font (CapCut sets a text's LINE, ascent plus descent, from the size, so a font with a taller line needs a smaller number).
  In Luckiest Guy that is CapCut size 4.5 on a 1920x1080 video and 8.0 on 1080x1920. The Loupe videos themselves use 5.5 and 10 (an em of about 5.6 percent, some 20 percent larger); that is not the default here. `cc.py captions` reports `size.em_pct_of_smaller_side` and `size.vs_guide` against the guide of 4.0 to 5.0 percent (a fact, not a stop): stay inside it, never above. Change `size_em_pct` when the picture calls for it, a bare number in `size` only for a deliberate choice.
- **Lines:** in a short about 3 words a caption by default (`max_words` 3, `max_chars` 18, upper case; the agent sets another count in the EDL's `captions` block when the speech or the picture calls for it: a fast run of short words, one word that must land alone), in a long video up to 5 words and 32 characters; a caption whose line would fill more than about 90 percent of the frame is split by `cc.py captions` (`split_for_width`). In this look the lexicon (`replace`) works on word SEQUENCES: a phrase Whisper split across a caption's edge still matches, a replaced phrase keeps its place in time.
- **Position:** `y_rel` is the baseline's place as a fraction of the height (0.66 in a short, 0.88 in a long video); on a broadcast put it above the HUD's bottom row (game-edit-craft.md). The box sits a little low (`v_offset`).
- **Checks:** `capcut texts` equals `captions.json -> word_box.texts`; `capcut lint` reports many `caption-too-fast` warnings (one-word texts of 0.1 to 0.5 s): expected, 0 errors is the bar. After a good finish the build removes capcut-cli's undo snapshots and the `*.bak` copies of the draft (they were 100 MB for one 4-minute video).
- **The plain look** (`style: "plain"`): 1 to 4 words per cue in a short, a line of up to 7 words in a long video, white with the same thick outline and shadow in Luckiest Guy, the key words in `highlight_color` (`highlight_words`), a 0.1 s fade-in in shorts; `size: "auto"` applies to it too.
- Names and terms: `replace` pairs from `lexicon.json` fix Whisper's spelling. Profanity and slurs are ALWAYS typed with one asterisk in place of the first vowel after the first letter (f*ck, sh*t, f*ggot, p*do, g*y; the user, 2026-11-14): `cc.py captions` masks the user's own list (`data/caption-masks.json`) by itself, and the EDL's `mask_terms` adds the exact lower-case forms of any other such word the agent hears (read the cues once after `cc.py captions`, add, run it again; `masked` in its answer and in `captions.json` says what was masked). The house font draws the asterisk. The audio is never changed (safety.md §3).
- A stretch of more than 4 s with no speech and no caption is reported by `cc.py captions` (`silent_stretches_over_4s`): decide whether it is fine (a visual beat) or needs a short text line (add it by hand in the report, not with a new tool).
- No emoji in any text. The captions never cover the face or the key action (move `y_rel` for the whole video if they do).

## Check before you build
`edl-check` returns: no warnings, no missing blurred files, no refused transitions, every cut clean, the duration inside the brief (a short at most 180 s), the captions' silent stretches understood (captions on), the SFX not on speech, nothing religious or superstitious in the transcript words of the spans (`safety.md`).
