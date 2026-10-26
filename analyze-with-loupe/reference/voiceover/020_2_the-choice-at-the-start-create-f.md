## 2. The choice at the start (Create; Free from the requirement)

1. **The method (Create), before the model menu** (`awl-start` step 2b), header "Voiceover", no option marked as recommended:
   - **"Native: drives the video"**: "Your ElevenLabs voiceover is the generation's driving audio: the model builds the video around it, the
     lips and the action timing follow it, and the generated file's sound is your voiceover. Needs Wan 3.0, Wan 3.0 Prime or Wan 2.7 (you pick
     the model next); up to 15 s of voice per generation."
   - **"Lip-synced pass"**: "Any model generates the speaking scene, then Higgsfield's Sync Lipsync 3 re-syncs the mouth to your exact
     voiceover, and the result carries your voice. One extra generation per voiced video."
   - **"Over the video"**: "For narration, a product review or any voice that is not spoken on camera: the video is generated without
     dialogue and your voiceover is placed over it in CapCut, on its own track. Works with every model."
   - **"No, the model's own audio"**: "As in every run: the generation carries its own dialogue, action sounds and ambience."
2. **The model menu after it** (`awl-start` step 4) shows every model as always, plus one line of facts under the table: which models take a
   driving audio (Wan 3.0, Wan 3.0 Prime, Wan 2.7) and that the lip-synced pass and the overlay work with every model. With **native**, the
   driving models are the menu's first options (each description says "driven by your voiceover"). A model without driving audio picked anyway:
   say so in one line and ask once which of the other two methods to use (a planning question, before the run exists). Never suggest a model
   after the pick.
3. **The voice, the language and the style** (after the paths, `awl-start` step 5c). Load the tools:
   `ToolSearch "select:mcp__elevenlabs__search_voices,mcp__elevenlabs__search_voice_library,mcp__elevenlabs__get_voice,mcp__elevenlabs__list_models,mcp__elevenlabs__check_subscription,mcp__elevenlabs__text_to_speech"`.
   None found: say the ElevenLabs MCP is not connected (`claude mcp list`; it is added with `claude mcp add elevenlabs -s user -e
   ELEVENLABS_API_KEY=<key> -- uvx elevenlabs-mcp`, then Claude Code is restarted) and ask once: continue without an own voiceover, or stop
   here to connect it. Then `check_subscription` (tier, characters used and left, the reset), `list_models` (the model and its languages) and
   `search_voices` (every voice in the user's library). **Print the whole voice list in chat, every row** (name, id, category): never a top-N.
4. Ask in **one** AskUserQuestion call:
   - header **"Voice"**, "Which voice speaks the videos?": three voices you choose from the list (a mix of registers, female and male) and
     **"My own voiceover files"** ("finished voiceover files you already made, one per video; you give their paths next"). Other: any name or
     voice id from the list, a voice id or name from the user's ElevenLabs account or Voice Library, or `character = voice` pairs for several
     speaking characters.
   - header **"Language"**, "In which language are the lines written and spoken?": English first, then up to three languages the
     conversation, the assets or the documents point to. Other: any language, by name or ISO code.
   - header **"Voice style"**, "Any extra preference for accent, dialect or delivery?": **"No extra preference"**, **"Scottish accent"**,
     **"Kosovar Albanian (Gheg dialect)"** (the user's own examples; swap them for two that fit when the conversation already names the
     language). Other: the user's words (an accent, a dialect, an age, a pace, an energy).
5. **Resolve and verify.** A voice name through `search_voices`, then `search_voice_library`; a voice id through `get_voice`. A Voice Library
   voice that is not among the user's own voices cannot be used by the MCP: say so and ask the user to add it in ElevenLabs (Voice Library →
   add to My Voices) or to pick another (one more question). Note each chosen voice's labels (gender, age, accent, description) for §5. The
   language becomes its ISO 639-1 code; one that is not in the model's list is `language_official=false`: say in one line that ElevenLabs
   still voices it but its pronunciation is not guaranteed (Albanian worked on 2026-10-26), so the user listens to the first take. "My own
   voiceover files": ask for their paths in plain chat (client assets, item 11), one file per video, and their scripts if the user has them.
   A `free` tier: one line, as information, that the free plan carries no commercial licence for the audio (posting the ads needs at least
   the Starter plan).
6. **Store** (`awl-start` step 6): the keys of §1. "No, the model's own audio": `voiceover.enabled=false`.

**Free.** The keys come from the requirement ([U]), the method included ("drive the video with my voice", "lip-synced", "over the video",
"narration", …). What it leaves open is asked inside the free plan's one confirmation call: the method (its options limited to what the
locked model allows: native only for a driving model), the voice and the language; when the method, the voice and the language are all
open, the language and the style share one question (header "Language": "English", "English, Scottish accent", "Albanian, Kosovar (Gheg)";
Other: any language with any accent, dialect or delivery), so the call keeps to four questions. The voice list is printed before it. A
requirement that does not ask for an own voiceover gets none, and nothing about one is offered, suggested, asked or written into the plan.

