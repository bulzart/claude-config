## 7. Model-specific pre-generation checklist

- [ ] `aspect_ratio: "9:16"`, `resolution: "720p"`; plan `atp.py conform` 704×1280 → 720×1280.
- [ ] Role semantics probed, or `image_references`/`video_references` avoided; one input type per request.
- [ ] Start/end frames and continuation sources conformed to 9:16; the source is text-free before continuation.
- [ ] One continuous take **or** SHOT/HARD CUT; one action plus one camera move per beat; the remaining seconds have a purpose.
- [ ] Grounding named (contact shadow, reflection); locks for subject, environment and color; persistent states stated.
- [ ] Quoted lines have speakers or a voiceover cue; tail "No on-screen text, no subtitles, no logos"; Analyze-Mode text in post.
- [ ] Line length fits duration (about 2.1–2.5 words/s); silent clips use `generate_audio: false`.
- [ ] `get_cost` done; interior frames QC'd for geometry, text and identity.

