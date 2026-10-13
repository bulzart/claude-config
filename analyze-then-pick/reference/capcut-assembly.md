# CapCut assembly: Analyze Mode's editable master

Every Analyze Mode video ends as **its own CapCut project**, named `DD_Mon_YYYY_vNN`
(e.g. `01_Oct_2026_v03`). The project holds:
- the clean generated video, which has no overlay text;
- the reference inserts (memes, `generation-system.md` §3c), each in its gap;
- every overlay text as an editable CapCut text layer (`text-and-format.md` §3).

The CapCut project is the master, and the final export happens in CapCut. Load this file at the
first assembly of a run.

## 1. Tools and rules
- **CapCut MCP** (`capcut`, user scope). Load the tools before first use:
  `ToolSearch "select:mcp__capcut__capcut_clone_draft,mcp__capcut__capcut_read_timeline,mcp__capcut__capcut_add_video,mcp__capcut__capcut_add_image,mcp__capcut__capcut_add_audio,mcp__capcut__capcut_add_text,mcp__capcut__capcut_split_segment,mcp__capcut__capcut_move_segment,mcp__capcut__capcut_trim_segment,mcp__capcut__capcut_add_track,mcp__capcut__capcut_set_props,mcp__capcut__capcut_set_track_mute,mcp__capcut__capcut_add_audio_fade,mcp__capcut__capcut_add_transition,mcp__capcut__capcut_validate,mcp__capcut__capcut_save,mcp__capcut__capcut_discard,mcp__capcut__capcut_undo"`.
  - Drafts store: `config.json → capcut.drafts_dir`, the same as the server's `CAPCUT_DRAFTS_DIR`.
  - Template: `capcut.template_draft` = `_analyze-stack-template` (9:16, 1080×1920, 30 fps, with
    video, audio and text layers). Its text layer is only the structure `capcut_add_text` copies;
    the look is always the house text style (§3, step 2).
  - Never call `capcut_transcribe`, `capcut_add_captions` or `capcut_clear_captions`: overlay text
    is placed event by event.
- **capcut-cli** (`capcut` 0.25, on PATH) provides the repair lines and the proxy preview (§4).
- **CapCut must be closed to save.** `capcut_save` and the repair lines refuse while CapCut runs, or
  when the draft changed on disk.
  - Never pass `force:true` into the live store, and never `--force-write`.
  - If CapCut is running when an assembly is due:
    - keep generating;
    - assemble every pending project at the wrap-up;
    - tell the user once to close CapCut. That is a blocker notice, not a permission question.
- **Fallback when the capcut MCP is missing or broken:** deliver the clean assembly (§6), burn the
  planned text with `atp.py captions` (same strings, times and positions; it imitates the house
  style: CapCut's System font, white fill, black outline), and say so.

## 2. Create the project
1. `T capcut-name --video NN` gives the free name: today's date plus the run's video number, with
   `-2`, `-3` appended when the name exists.
2. `capcut_clone_draft {base:"_analyze-stack-template", newName:"<name>", empty:true}`.
3. `T capcut-prep --draft "<store>/<name>"` comes **immediately**, before any other CapCut call on
   the draft.
   - Why: the clone inherits the template's identity file (`draft_meta_info.json`, with the
     template's draft id, name and folder) and its timeline layout.
   - What it does: sets both aside (`*.atpbak`) and points the layout at the new timeline. That
     lets `capcut register` (§4) write a correct identity.
4. `capcut_read_timeline {draft}` gives the canvas (9:16, 1080×1920) and the track indexes (video,
   audio, text). The template's tracks are empty after the clone.

## 3. Build the timeline
Inputs:
- the accepted **clean video** `60-outputs/video-NN/clean.mp4`: the generation, joined if
  multi-clip, conformed and trimmed, without overlay text;
- the inserts `30-assets/inserts/<V>-iK.mp4`;
- the text plan.

1. **Main video track.**
   - No inserts: `capcut_add_video {draft, file:"<clean.mp4>", atSec:0, trackIndex:<video>}`.
   - With inserts: place the whole generation at 0, then handle each insert k in order. Keep
     `offset` = the sum of the earlier inserts' durations (0 for the first) and `d_k` = this
     insert's duration:
     1. `capcut_split_segment` the generated segment at `split_k + offset`;
     2. `capcut_move_segment` the right-hand piece to `split_k + offset + d_k`;
     3. `capcut_add_video {file:"<insert>", atSec:split_k + offset, trackIndex:<video>}` into the
        gap. For a screenshot of a still meme: `capcut_add_image` for `d_k` plus `capcut_add_audio`
        with the insert's sound.

     Example: a 25 s generation with a 2 s meme at 13 s →
     `[generated 0–13] [meme 13–15] [generated 15–27]`.
   - Sound: the generated audio stays on its pieces and each insert keeps its own sound. Check
     that no track is muted (`capcut_read_timeline` → `muted`; fix with `capcut_set_track_mute`).
   - **Recreate: the reference timeline and its ORIGINAL audio stay whole** (CE-024, CE-025). The
     timeline's length equals the reference's, and the original audio is ONE untouched segment under all
     of it (the pieces' and inserts' own audio muted, never assembled from parts); its hash, or a null
     test against the source audio, proves it. An insert's edge span that showed the replaced performer
     stays on the timeline as pure transition colour (white or black) of the same duration, and the
     neighbouring piece fades into and out of it on real moving footage (its own last and first frames
     fade). A held or frozen frame is never used under a flash or dissolve; an insert that starts or
     ends on a brightness step fades from the gap colour.
2. **Text layers.** One `capcut_add_text` per text event, all on the text track:
   - `text`, and `atSec` / `durSec` on the **final** timeline, after the inserts;
   - **position: always horizontally centred** (the user, 2026-10-09, CE-010):
     `posX = 0` with centre alignment on every text layer, whatever the reference's `x_rel`. Only
     the height comes from the reference: `posY = 1 − 2·y_rel` (`y_rel` = the text centre in the
     reference, 0 = top, 1 = bottom; CapCut's transform uses half-canvas units with +y up). When
     centred text would cover the product, a face or an insert's picture, move it **up or down**
     (top, middle or bottom band), never sideways;
   - text that plays on the product (a logo pun such as "All I C is u") goes on the frame where
     the logo really faces the camera in the clean video, measured at 30 fps
     (`generation-system.md` §5b);
   - **the house text style, always:** font **System**, size **10**, and **the user's chosen
     preset** (learned from `03_Oct_2026_v09` on 2026-10-03, locked in
     `config.json → capcut.text_style.learned`; white text, black outline). Pass `fontSize:10` and
     no `color`. `T capcut-repair` (§4) then rewrites every text layer to exactly that style (font,
     size, fill, outline and the preset's fields). Never another font, size, colour or preset unless
     the user asks for it in the run;
   - never over the face, the product or the key action; inside the platform-safe area
     (`text-and-format.md` §3);
   - no emoji in any text layer (the user's rule, strict).
2b. **Overlays cut from the reference** (a context-bearing notification, message or banner;
   `text-and-format.md` §1): crop the original element from the reference's own frames, keep its look,
   position, size and timing, and place it on a video track above the picture (`capcut_add_video`). It
   exists only on the frames where the element is really visible (find its first and last visible frames
   at 30 fps; the plain frames before and after are not part of it) and it follows every fade, dissolve or
   flash of the picture under it (the same fade baked into the clip, or the clip trimmed to end before the
   fade). A crop that carries its own backdrop (the window behind a banner) is never left on screen after
   the element is gone (CE-026).
3. **Only what the reference does:** a transition only where the reference has one
   (`capcut_add_transition`, from the catalog), and a short fade on an insert's sound when it
   clicks (`capcut_add_audio_fade`).
4. **Create:** the sound layer (§3b).
5. `capcut_validate` → `capcut_save`.

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

## 4. After every save (capcut-cli)
```
T capcut-repair --draft "<store>/<name>" --preview "<run>/60-outputs/video-NN/capcut-preview.mp4"
```
It first applies the **house text style** to every text layer (`T capcut-text-style`, root and
nested timeline copies), then runs these capcut-cli steps, the first three under one machine-wide
lock:
```
capcut register "<store>/<name>" --apply --materials
capcut sync-timelines "<store>/<name>" --nested --apply
capcut lint "<store>/<name>"
capcut render "<store>/<name>" --out "<preview>" --burn-captions
```
- The lock exists because `register` rewrites CapCut's **shared** project index, and production
  agents assemble projects in parallel.
- Exit 1 with an `action` line means CapCut is running, or lint found errors.
- `register` recreates the identity file from the new timeline and lists the media. Without the
  media list, CapCut shows the clips as "file inaccessible".
- `sync-timelines` writes the nested timeline copy that CapCut 9.x reads first.
- `lint` must report 0 errors.
- The preview is a low-resolution proxy, not CapCut's own render. It shows the order, the timing,
  the inserts and the text.
- **The exact preset: the user's choice, learned and locked.** CapCut keeps its preset tiles on its
  servers, not in a readable file, so the preset is copied from a text the user styled in CapCut.
  - **Current house preset:** chosen by the user in `03_Oct_2026_v09` and learned on 2026-10-03
    (white text, black outline 0.06). It is stored in `config.json → capcut.text_style.learned`
    with `"locked": true`, and every project of every run gets it. The font path is resolved to the
    newest installed CapCut version at apply time, so CapCut updates do not break it.
  - **Never replace it** unless the user explicitly asks for a different preset. `--learn` refuses
    while the preset is locked; only then use:
    1. in CapCut, add a text to any project, pick the new preset, and close CapCut;
    2. `T capcut-text-style --learn --replace --draft "<store>/<that project>"` (`--text N` when the
       project holds several texts).
  - A `warning` in the learn output means the preset also uses an extra material that is not copied
    yet.
  - Without a learned preset (only if config is lost), the fallback look is white fill, black
    outline (width 0.06), no shadow, no background.

## 5. QC of the project
- Read the project back with `capcut_read_timeline`:
  - the generated pieces are contiguous, and each insert sits exactly at its split;
  - the total = generated length + the inserts;
  - every text event is at its planned time and position;
  - `T capcut-text-style --draft "<store>/<name>" --check` reports 0 texts off the house style;
  - no text layer contains an emoji.
- On the preview (`atp.py qc --video <capcut-preview.mp4> --out <dir> --expect-size 540x960`, plus
  its storyboard), check:
  - the cut into and out of every insert, and the sound;
  - text presence and timing;
  - dense sheets (15 to 30 fps) of every transition, insert start and end, overlay start and end and the
    first second: no frame of the replaced performer, no held frame, no stray rectangle, halo or
    brightness step (CE-016, CE-025, CE-026);
  - audio (Recreate): the original track is one segment, the duration equals the reference's, and its
    hash or a null test against the source audio matches (CE-024).
- Fix through the MCP: read → edit → `capcut_validate` → `capcut_save` → §4 again. A save refused
  because the draft changed on disk → `capcut_discard`, then rebuild the edits.

## 6. Deliverables (Analyze Mode)
- **CapCut project `<name>`**: the editable master, with the text. Export the final from CapCut
  (Export → 1080×1920 or 720×1280).
- **`RUN/deliverables/video-NN-clean.mp4`**: the same edit without text, assembled locally.
  - Cut the clean video at the split points with `atp.py trim`.
  - Join the pieces and inserts with `atp.py concat --seams cut,…`.
  - A Recreate's clean carries the original audio whole (`restore-audio` over the joined result), and a
    with-inserts clean is never replaced by the generated-only `60-outputs/video-NN/clean.mp4`.
  - Every video of the run has both deliverable files in this one folder and a row in `README.md`.
- **`RUN/deliverables/video-NN-preview.mp4`**: the proxy with the text burned in, for review.
- The project uses files from the run folder: keep the run folder.
