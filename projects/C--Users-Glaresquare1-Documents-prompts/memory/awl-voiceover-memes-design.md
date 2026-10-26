---
name: awl-voiceover-memes-design
description: "/analyze-with-loupe items 31 (own ElevenLabs voiceover: native/lipsync/overlay) and 32 (memes include/none in Create): the user's decisions and what is still unverified"
metadata:
  node_type: memory
  type: project
  originSessionId: c1639feb-dd77-47ca-950d-178277c7920f
  modified: 2026-10-26T01:52:06.786Z
---

On 2026-10-26 the user had two features added to /analyze-with-loupe (library `~/.claude/analyze-with-loupe`, router `~/.claude/commands/analyze-with-loupe.md`):

- **Item 31, own voiceover (ElevenLabs).** Create asks it before the model menu; Free uses it only when the user's requirement asks (never suggested); never in Recreate or Edit Mode. The user picks the voice (from the printed list, by name or id), the language and an accent or dialect (their examples: a Scottish accent, Kosovar Albanian). There are three methods. **native**: the take is the generation's driving audio, on Wan 3.0, Wan 3.0 Prime or Wan 2.7. **lipsync**: any model, then a Higgsfield `sync_so` pass with the take. **overlay**: no dialogue, the take placed over the video in CapCut, for narration or a product review.
- **Item 32, memes in Create.** `include` keeps memes and other cut-in clips as before. `none` means pure generation: no insert or meme sound of any kind.

**Why:** the user called the voiceover living inside the generation itself, with lips and movement synced and no CapCut edit, "the most preferred high priority need". Overlay was added for narration on any model. Memes had been cut in whenever the references had them, with no way to opt out.

**How to apply:** treat native as the first choice wherever the model allows it. Do not re-propose a design that drops any of the three methods. As of 2026-10-26, native driving fidelity and `sync_so` quality on Higgsfield are untested; the pilot video of the first voiced run measures them. Reports must never claim pronunciation was checked, because no agent listens. Related: [[elevenlabs-setup]], [[pipeline-context-budget]].
