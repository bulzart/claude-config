## 3b. Sound layer (Create)
Generated clips usually carry only voices, action sounds and ambience. Viral reels add a soundtrack
(dramatic, comic, suspense, hype), sound effects, or both. Create videos get that layer here, in
CapCut, shaped by the references' sound profiles (`10-media/<V>/audio-profile.json`).

1. **Plan it from the profiles** (in X1):
   - the role, which the agent infers from the numbers plus the visuals;
   - the tempo and the energy arc;
   - whether there is a music bed at all;
   - where the hits land: on cuts, reveals or punchlines, mapped onto the new video's beats.
   Never add a bed where the references' family has none.
2. **Choose the source, in this order:**
   1. **A soundtrack the client supplied** (registry, audio entity).
   2. **The reference's own sound,** when its profile says `reusable_whole` (no speech over it, a
      music bed present). Use the extracted `files_audio` track, at the in-point and length the new
      video needs.
      - It may be a commercial or trending song whose rights belong to its owner. Mark it in the
        brief and the README so the user decides before posting; brand accounts may only post
        commercially licensed sounds.
      - A reference with speech over its music can't be reused cleanly, because no vocal separation
        is installed. It only guides the search.
   3. **A matching track, found and downloaded:**
      - Search royalty-free libraries by the profile's mood, genre and tempo tags: Pixabay Music,
        Mixkit, or CC0 / CC BY on Wikimedia Commons or the Free Music Archive. Use WebSearch /
        WebFetch to reach the **direct audio-file URL**.
      - Download with
        `T fetch-audio --url <file url> --page <source page> --license "<license as stated>" --role soundtrack --out <RUN>/30-assets/audio/<name>.mp3`.
        It writes `<file>.source.json` beside the file.
      - Prefer licenses that allow commercial use without credit. CC BY needs a credit line in the
        README.
      - When the `heygen` CLI is installed and signed in, the HeyGen catalog is an alternative:
        `npx hyperframes media-use resolve --type bgm --intent "<role, mood, tempo, energy arc>"`.
   4. **Sound effects:**
      - first the bundled library, `C:/Users/Glaresquare1/.claude/skills/media-use/audio/assets/sfx/`.
        It holds whoosh, whoosh-cinematic, impact-bass, riser, glitch, pop, chime, click, ping,
        sparkle and more, under the Pixabay license (commercial use, no credit);
      - for a named meme sound the references use, a downloaded royalty-free equivalent
        (`--role sfx:<name>`).
   - Never use audio whose license is unknown.
3. **Place it on its own audio tracks** (`capcut_add_track type:"audio"` when needed):
   - **Soundtrack:** `capcut_add_audio {file, atSec:0, durSec:<video length>, srcStartSec:<in-point>,
     trackIndex:<music track>, volume:<v>}`.
     - Volume: ~0.25 when speech runs through it, ~0.6–0.8 when there is no speech.
     - Fade in 0.3 s and out 0.8 s (`capcut_add_audio_fade`).
     - Over a meme insert, quiet the bed so the meme's own sound wins: `capcut_split_segment` at the
       insert's in and out, then `capcut_set_props {volume:0.1}` on the middle piece.
   - **Sound effects:** one `capcut_add_audio {file, atSec:<hit>, trackIndex:<sfx track>,
     volume:~0.8}` per hit, on the new video's cuts, reveals or punchlines, only where the plan
     puts them.
   - The generated video's own audio (dialogue, actions) stays on its clips at full volume.
4. **Check:**
   - `T audio-profile --audio <capcut-preview.mp4> --out <…/preview-audio.json>` confirms the bed
     is present and the hits land where planned (±0.15 s);
   - integrated loudness near −14 LUFS is the social norm; the user fine-tunes levels in CapCut;
   - record the source, license and in-point of every audio file in the README row.

