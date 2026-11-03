## 3c. The Create edit from clean takes (command item 35)
Create and Free `create` videos: the timeline is built from the conformed takes by the plan's edit plan, never from one joined take,
and nothing of it was generated. Recreate keeps §3. The tools below are suggestions for the usual operations: find the live tool list
first (§1) and use what it offers for each operation, a newer or better tool included.
1. **Pieces.** Each piece is a span of a take, in the plan's order on the main track:
   `capcut_add_video {draft, file:"<take>", srcStartSec:<in>, durSec:<out - in>, atSec:<its time>, trackIndex:<video>}`.
   Pieces of different takes interleave freely, a span may come back (a replay), and `capcut_delete_segment` with `ripple:true`
   closes a gap.
2. **Speed.** `speed` on the piece (`capcut_add_video`, or `capcut_set_props`): under 1 for slow motion, over 1 for fast; a speed
   ramp is the same span cut into consecutive pieces at stepped speeds.
3. **Freeze frame.** A still of the take at that moment (`awl.py frames "<take>" --at <t> --out <dir>`) placed with
   `capcut_add_image` for the hold.
4. **Punch-in, pan, artificial shake, animated crop.** Keyframes on the piece (`capcut_add_keyframe`): `UNIFORM_SCALE` for a
   punch-in or a zoom, `KFTypePositionX` / `KFTypePositionY` for a pan, small alternating positions for a shake, scale and position
   together for an animated crop; a held punch-in is `scale` with `capcut_set_props`. The take plan framed the subject with the room
   the punch-in needs (X1), so it never enlarges past the detail the take holds.
5. **Multi-view layouts** (split screen, picture-in-picture, comparison panels, grid, collage): each panel is its own clean take on
   its own track (a higher `trackRenderIndex` on top), placed and sized (`posX`, `posY`, `scale`), cropped with a mask
   (`capcut_add_mask`, a shape from `capcut_list_masks`) and kept in sync on the timeline; a divider or a border is added here.
6. **Transitions** (`capcut_add_transition`, from `capcut_list_transitions`) where the edit plan has them, and the **finishing
   treatment** as a filter (`capcut_add_filter`, from `capcut_list_filters`).
7. **Graphics.** A supplied graphic (an arrow, a badge, a logo among the client's assets) as `capcut_add_image` on an upper track.
   Never a sticker or an emoji, as a graphic or in a text layer (the user, 2026-11-03; command item 6), whatever the live list offers.
8. **Reverse playback and CapCut's effect library** (glitches, glows, particles, motion-graphics templates) had no MCP tool when this
   was written: look for one in the live list first; with none, they stay in the edit plan and in the video's README row as "to apply
   in CapCut", and are never generated.
9. Then the inserts (§3 step 1, Create only with `memes=include`), the text layers (§3 step 2: the house style, centred, no emoji),
   the sound layer (§3b) and the voice (command item 31), as for every Create video; `capcut_validate` → `capcut_save` → §4.
- The preview (`capcut render`) flattens the main track only (its pieces, trims, speeds and text): the layouts, keyframes, masks,
  filters and graphics show only in CapCut, and §5 checks them on the timeline read back.
