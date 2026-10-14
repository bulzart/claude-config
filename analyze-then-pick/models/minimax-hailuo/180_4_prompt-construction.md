## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach
Verbatim first-party examples:

1. Text-to-video with camera commands — MiniMax API, Create Text-to-Video Generation Task, https://platform.minimax.io/docs/api-reference/video-generation-t2v
   > "A man picks up a book [Pedestal up], then reads [Static shot]."
2. Image-to-video — MiniMax API, Image-to-Video Task, https://platform.minimax.io/docs/api-reference/video-generation-i2v
   > "A mouse runs toward the camera, smiling and blinking."
3. First + last frame — MiniMax API, Create First & Last Frame Video Generation Task, https://platform.minimax.io/docs/api-reference/video-generation-fl2v
   > "A little girl grow up."
4. Camera-command rules — same API pages
   > "Multiple commands inside one `[]` take effect simultaneously (e.g., `[Pan left,Pedestal up]`). Recommended max: 3."
   > · "Commands appear in order, e.g., "...[Push in], then...[Push out]"." · "Free-form descriptions also work, but
   > explicit commands yield more accurate results."
5. Higgsfield first-party examples [HF] — Minimax Hailuo 2.3: A Creative Guide, https://higgsfield.ai/blog/Minimax-Hailuo-2.3-A-Creative-Guide
   > "Human transforming into werewolf under moonlight" · "Perfume bottle melting into gold" · "Keep prompts short and
   > physical ('melt,' 'ignite,' 'morph')"

Patterns they teach:
- **Length:** 4–12 words; one subject, one or two actions (1–3).
- **Camera placement:** the bracket follows the clause it applies to; sequences joined with ", then" (1, 4).
- **Subject vs camera:** subject motion is plain prose, camera motion is only the bracket (1).
- **Image-to-video:** motion and expression only — no re-description of the frame (2).
- **First+last frame:** one phrase naming the change between the frames (3).
- **Exclusions:** none in any official example; transformation verbs are Higgsfield's stylistic lever (5) and a
  morphing risk for products.

### 4.1 Text-to-video
Follows patterns: short physical clause + bracket after it. Landscape output — not for 9:16 deliverables (§2.6).
```text
<Subject with 2–4 visual traits> <physical action 1> [<camera command>], then <action 2> [<camera command>]. <Setting>, <light>. No text, captions, logos or watermarks.
```
Worked example (variant `minimax-2.3`, 6 s, preview only): "A young gymnast in a plain navy leotard sprints down the
mat and launches into a round-off back handspring [Tracking shot], then lands cleanly and raises both arms [Static
shot]. Empty training hall, soft morning light. No text, captions, logos or watermarks."

### 4.2 Start frame (and end frame) to video
Follows patterns: motion only, bracket after each clause, ", then", end state.
```text
<What moves first, from the frame's exact state> [<camera command>], then <next movement> [<camera command>], <end state>. <Subject> keeps the same appearance, clothing and proportions; light and shadows stay as in the first frame. No text, captions or watermarks.
(FLF, variant minimax) <Change connecting the first frame to the last frame>, ending exactly on the last frame.
```
Worked example (variant `minimax-2.3-fast`, 10 s, 9:16 `start_image` = a hand holding a closed glass jar of honey on a
table): "The hand unscrews the lid slowly and sets it on the table, then a spoon dips in and lifts a thick ribbon of
honey that folds back into the jar [Push in], then the spoon rests on the rim [Static shot]. The jar keeps its exact
shape and size; light and shadows stay as in the first frame. No text, labels, captions or watermarks."

### 4.3 Reference-to-video
N/A on Higgsfield — `minimax_hailuo` accepts only `start_image` and `end_image` [HF]. Use `minimax_h3`.

### 4.4 Video edit / extension / motion transfer
N/A on Higgsfield. Approximate an extension by using a clean last frame as the next `start_image` [INFERRED].

