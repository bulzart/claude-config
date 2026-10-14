## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach

Sources: FLUX Video Edit (https://docs.bfl.ai/flux_tools/flux_video_edit) and the Video Editing prompting guide (https://docs.bfl.ai/guides/prompting_video_editing).

1. > Remove the orange bucket.
2. > Add a tall white lighthouse with a red lantern room standing on the end of the harbor wall to the right of the boats.
3. > Change the stencil on the crate to read DAILY CATCH.
4. > Make him say "Fresh mackerel, four for ten."
5. > Replace the cliff with the reflective windows of a high-rise building. Add narrow metal window ledges at the climber's hand and foot contact points. Far below, traffic and illuminated buildings fill a dense city in blue-hour light.
6. > Render this previz chase as a desert convoy pursuit at golden hour: the pillars become ruined highway columns in open dust, the lead car an armored pickup, the chaser a spiked buggy, both trailing dust plumes, heat shimmer. Same weave lines, same speeds, same camera overtake. V8 roar and wind.
7. > Restyle this clip as live-action footage of a claw machine lifting a lavender octopus plush. Fine velour fibers and sewn seams replace the ink outlines. The plush compresses gently where the metal claw grips it. Soft arcade lights reflect in the glass.
8. Stacked independent edits:
   > Remove the orange bucket. Make the apron red. Change the stencil on the crate to read DAILY CATCH. Add a seagull standing on the corner of the crate. Make it snow, with flakes settling on the crate and the fish.

Patterns these teach:
- **Order:** imperative verb first (Remove / Add / Change / Make / Replace / Render / Restyle), then the target by a visible handle, then placement relative to a landmark, then appearance (2, 5).
- **Sentence style:** one short sentence per change. Stacks are separate sentences (8).
- **Locks:** inherited motion is locked explicitly ("Same weave lines, same speeds, same camera overtake") (6).
- **Physics:** contact points for re-sets (5); grip deformation and reflections for restyles (7).
- **Text and speech:** retext as `to read WORDS`, capitals without quotes (3). Speech as `Make him say "…"`, quoted and length-matched (4).
- **Audio:** a trailing sound fragment when sound changes ("V8 roar and wind.") (6).
- **Length:** 3–45 words; detail only where the edit needs it.
- **Exclusions:** none. Removal is written positively as "Remove …" (1).

### 4.1 Text-to-video

N/A on Higgsfield (edit-only; use `flux_3_video`).

### 4.2 Start frame (and end frame) to video

N/A on Higgsfield.

### 4.3 Reference-to-video

N/A on Higgsfield (no image or reference input).

### 4.4 Video edit / extension / motion transfer (only if supported)

Templates follow patterns 1–8.

Edit Mode text removal (always pass 1 when overlays exist):
```text
Remove the <text element 1 by position/look>, the <text element 2> and the <text element 3>, and restore the
<surfaces> behind them. [Keep the <approved product label/UI> exactly as it is.]
```
Example: `Remove the white subtitle text along the bottom of the frame and the username in the top-left corner, and restore the kitchen counter and tiled wall behind them. Keep the printed label on the jar exactly as it is.`

Content edit:
```text
<Imperative verb> <target by visible handle> [<placement relative to a landmark>] [<size, look>] [<contact/grip/
light/reflection detail>]. [<Second independent change>.] [Same <motion/timing lock>.]
```
Worked examples (generic):
- Add: `Add a small grey cat sitting on the windowsill to the left of the plant, watching the person at the desk; it casts a soft shadow on the sill.`
- Replace (text only): `Replace the paper cup in her hand with a plain white ceramic mug of the same size, her fingers around its handle.`
- Re-set: `Replace the parking lot behind the car with a coastal road at sunset; the tires stay on dry asphalt and the car keeps its exact shape and color.`
- Restyle: `Restyle this clip as stop-motion clay animation: visible fingerprints in the clay, slightly stepped motion, soft studio light reflecting on the clay surfaces. Same movements and timing.`
- VFX: `Make it rain lightly, with droplets beading on the car roof and the pavement turning glossy.`
- Dialogue: `Make her say "See you tomorrow, same time."`

