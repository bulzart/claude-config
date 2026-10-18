## 2. Work backward from the finished video

Write this plan to `<run>/40-briefs/video-NN-plan.md` **before** any prompt. Keep it compact
(tables and short lines). Label provenance on each line where it matters:

- **[E]** direct evidence from source material
- **[I]** analytical inference
- **[U]** user instruction
- **[A]** approved client asset
- **[M]** model engineering knowledge
- **[G]** generation instruction

### 2.1 Intent (answer first)
- **Communicates:** what the viewer must understand or feel by the last frame.
- **Why keep watching:** the curiosity / payoff contract set up in the first second.
- **Mechanism kept from the references [E/I]:** hook type, reveal logic, rhythm, interaction pattern
  and payoff timing, from the selected content family (Recreate) or from the mechanisms the blend borrows, from any family (Create).
- **Subject of its own (Create) [I]:** the premise, setting, characters, action sequence, turn,
  lines, first frame, ending image and product beat are the concept's, none of them a reference's;
  the plan names the craft it carries (the borrowed mechanisms) and states that the copy test passed
  (`creative-direction.md` §5.0).
- **The blend (Create) [I]:** the idea is a blend of a reference mechanism and a **product truth**
  from `30-assets/product-insights.md`, not a reference format with the product swapped in: the plan
  names the borrowed mechanism (its id M# in `mechanism-map.md`, with the craft-sheet block it comes from), the product truth it uses and how the mechanism is
  re-expressed through it, and states that the blend and template-lock tests passed
  (`creative-direction.md` §5.0b).
- **Virality rationale (Create) [I]:** why the video should spread, in the lines of `viral-browser.md` §14.4: the mechanism (M#, k of n, driver, grade)
  and the product truth (PT#) that expresses it, the audience trigger, the hook and its timing inside the measured range, the trend element
  (dated) or none, the share line, and what could make it fail. An argument from the references' evidence, never a prediction of reach.
- **Goal and job [I/U]:** the run's goal (`creative-direction.md` §2) and what this video makes the
  viewer do at the end, and what they keep of the product.
- **Audience and the one sharp idea [I]:** who it is for, the situation they have lived, the one
  idea in one sentence, the emotion arc or laugh mechanism, and the share line
  (`creative-direction.md` §3, §6).
- **Adapted:** which identity-specific elements become the client's [A/U]; what is dropped (source
  branding, usernames, watermarks, source wording).

### 2.2 Time budget (every second has a job)

| t (s) | beat | purpose (hook / context / demonstrate / build / payoff / rhythm) | action | camera | audio | text (mode-dependent) |
|---|---|---|---|---|---|---|

Rules:
- Rows must tile the whole duration with no unexplained gaps.
- **Stillness** is allowed only when the content family (Create: a borrowed mechanism) uses it deliberately (a held reaction, a
  reveal pause). Mark those rows "intentional hold".
- The **duration** comes from the content family's typical length (Create: the range the borrowed mechanisms show) and the concept, and must be one
  the selected model supports. Too long for one generation → plan clips per §3b, with explicit
  hand-off states (§3), assembled with `atg.py concat`. Hard cuts only where the family's editing
  style (Create: the blend's) cuts.
- **Hook density, information density and payoff timing** follow the profile from the
  analysis (Recreate: the source's family; Create: the measured ranges of the mechanisms the blend borrows), not generic AI editing habits.
- **Reference inserts** (memes, §3c) are not in the generated time budget. Their split points are
  marked as beat boundaries.
- **Overlay text** is never generated: the plate stays clean, and the text is placed as CapCut text
  layers (`capcut-assembly.md`, `text-and-format.md`).

### 2.3 Roles and assets

| entity | role in the video | source-of-truth asset [A] | must stay fixed | may adapt | replaced from source entity |
|---|---|---|---|---|---|

- The canonical template or source-of-truth reference is authoritative for identity and geometry.
- Variants may change appearance (colour, label, flavour, skin) but never the fundamental geometry,
  unless the user says so.

### 2.4 Scene
- **Environment:** layout, surfaces, depth planes, what is in the foreground and background.
- **Lighting:** key-light direction, quality (hard/soft), colour temperature, exposure level, practical
  lights, environmental colour spill.
- **Camera:** shot size, angle, lens feel, height, movement per beat. Every move needs a reason (§5).
- **Audio:** dialogue (who, exact words), ambience, action sounds, music (or none), native vs. post.
  **Create:** the generation carries dialogue, action sounds and ambience only, with no generated
  music. The soundtrack and sound effects come from the sound plan and are placed in CapCut
  (`capcut-assembly.md` §3b).
- **Text:** per `text-and-format.md`. Edit Mode removes source text; Analyze Mode may add planned text,
  by default in post.

