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

