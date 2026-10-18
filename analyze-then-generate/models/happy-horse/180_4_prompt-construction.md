## 4. Prompt construction

### 4.0 Official prompt examples and the patterns they teach
First-party examples exist (API references and Alibaba's campaign page), but no first-party prompt guide:

1. Text-to-video — HappyHorse text-to-video API reference, https://www.alibabacloud.com/help/en/model-studio/happyhorse-text-to-video-api-reference
   > "A miniature city built from cardboard and bottle caps comes to life at night. A cardboard train slowly passes
   > through, with small lights dotting the scene and illuminating the way ahead."
2. Image-to-video — HappyHorse image-to-video API reference, https://www.alibabacloud.com/help/en/model-studio/happyhorse-image-to-video-api-reference
   > "A cat running on the grass"
3. Image-to-video with dialogue — Alibaba Cloud Happy Horse-1.1 campaign page, https://www.alibabacloud.com/en/campaign/happyhorse-video
   > "The cute teddy bear as it briskly walks forward across the train station platform, pulling its brown suitcase
   > behind it with a sense of urgency. The bear's mouth moves in perfect lip-sync as it hurriedly says: 'There's no
   > time left, I'm going to be late!' Its expression should appear anxious and determined. In the background, other
   > passengers and the trains should have subtle, natural movements to reflect a busy station atmosphere. The camera
   > follows the bear with a smooth forward tracking shot, maintaining its soft, fuzzy texture and the realistic
   > cinematic lighting from the original image."
4. Text-to-video with a style change — same page
   > "A girl is dancing gracefully. As she spins around in a full turn, the entire scene seamlessly transforms from a
   > cartoon style into a realistic live-action setting."
5. Sequencing (reference mode, not exposed on Higgsfield) — HappyHorse reference-to-video API reference, https://www.alibabacloud.com/help/en/model-studio/happyhorse-reference-to-video-api-reference
   > "A woman in a red qipao from [Image 1] is first shown in a profile medium shot, highlighting the tailored cut and
   > S-curve of the dress. The camera then switches to a low-angle shot, […]"

Closest supporting guidance (API partner, [SECONDARY]): "[Subject] [does action] in [setting], [time of day], [one
atmosphere or camera cue]."

Patterns they teach:
- **Order:** subject + action with manner → dialogue with lip-sync and expression → background activity → camera move
  → preservation of texture and lighting (3).
- **Sentence style:** plain declarative prose, one idea per sentence; pace words ("slowly", "briskly") (1, 3).
- **Subject vs camera:** the camera gets its own final sentence (3); partner guidance agrees the last position carries
  the most weight [SECONDARY].
- **Temporal markers:** "As she…", "first… then" rather than timecodes (4, 5).
- **Dialogue:** "<subject>'s mouth moves in perfect lip-sync as it says: '…'" plus an expression sentence (3).
- **Length:** 5–95 words; image-to-video can be minimal (2). **Exclusions:** none in any official example.

### 4.1 Text-to-video
Follows patterns: subject + paced action → setting/light → background activity → sound → clean-plate clause → camera last.
```text
<Subject with 2–4 traits> <one action with manner/pace> in <setting>, <time of day / light>. In the background, <subtle natural movement>. <Sound: what is audible | no music>. No text, captions, logos or watermarks. <One camera move>.
```
Worked example (5 s, 9:16, 720p): "An elderly man in a grey wool coat feeds pigeons on a park bench, scattering seeds with
slow, steady tosses, late-afternoon golden light. In the background, a few people walk slowly along the path. Sound:
soft wing flaps and distant traffic, no music. No text, captions, logos or watermarks. Slow dolly-in from a medium
shot."

### 4.2 Start frame (and end frame) to video
Follows patterns: action with pace → dialogue/expression → background → camera → preservation clause.
```text
The <subject> <action from the frame's exact state, with pace>, <expression/secondary motion>. In the background, <subtle natural movement>. <Sound / dialogue: mouth moves in lip-sync as it says: "…" | no dialogue, no music>. The camera <one move>, maintaining the look and the lighting from the original image. No text, captions or watermarks.
```
Worked example (6 s, 9:16 `start_image` = a cyclist stopped at a crossing): "The cyclist pushes off and pedals steadily
across the street, glancing left once, jacket rippling in the wind. In the background, cars idle at the light. Sound:
bicycle chain and city ambience, no dialogue, no music. The camera follows with a smooth side tracking shot,
maintaining the look and the lighting from the original image. No text, captions or watermarks."

### 4.3 Reference-to-video
N/A on Higgsfield — `happy_horse_video` exposes only `start_image` [HF].

### 4.4 Video edit / extension / motion transfer
N/A on Higgsfield. Upstream `happyhorse-1.0-video-edit` exists but is not exposed [OFFICIAL/HF].

