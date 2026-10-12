# Caught flags: prompts and videos Higgsfield flagged

One entry per flag. A **flag** is any time Higgsfield refuses, blocks, withholds or reroutes something
during `/analyze-then-pick` (and the sibling pipelines): a moderation or policy block, a job that fails
within seconds with no reason (and is refunded), an uploaded image, video or element marked `nsfw`,
`ip_checking` or `failed`, an output that was withheld or flagged, or a notice that comes back instead of
a job (`preset_recommendation`). Validation errors (a prompt over 5000 characters, out of credits) are
not flags; they stay in the submission ledger.

Each entry holds what is needed to find the trigger and not repeat it:
- the **verbatim response** from Higgsfield (or "none given"), the tool, the stage, the job id and credits;
- the **full flagged prompt**, the params and the **media the request carried** (roles and media ids);
- the **flagged video**: the reference video (V id, file) that rode as the video reference and/or the
  generated clip that was withheld, plus its output path;
- the agent's **suspected trigger** (labelled [E] evidence or [I] inference), the cause class, what was
  changed in the next request, and the outcome;
- when a changed request was accepted: the **cleared prompt** (with a sentence diff against the flagged one)
  and the cleared job. A flag is only `cleared` once a request went through; `persistent` means the flag
  stayed and the video was planned another way or reported.

**Who writes it.** The agent that made the call, at once (the contract in `reference/production-agents.md`
§3 item 15 and the command's item 23), always with `T caught-flag add`, never by hand. The script records
and tabulates only; the diagnosis is the agent's. `ledger set --flagged` marks the submission, and
`caught-flag reconcile --run RUN` lists marked rows with no entry and failed rows to judge; the main session
runs it as each agent reports and in the wrap-up.

**Who reads it.** Every run reads it at the start (command A1 / E1): `T caught-flag list --digest`. The entries
that apply (same model, tool, kind, or a trigger the plan could repeat: a person's face in a video reference,
a brand or celebrity in the prompt, an image kind) go into `<RUN>/20-analysis/caught-flags.md`; every plan
names the ones it avoids, and X4 checks the request against them before any credit is spent. A cleared prompt
shows what Higgsfield accepted. A general rule is promoted into the owning reference (the model guide's failure
table, `generation-system.md` §5c.2, brand-guardrails) and marked `promoted`; the entry stays as the record.

```
T caught-flag add --title "<short>" --kind <moderation-block|refused-no-reason|media-flagged|output-flagged|preset-notice|other> --run "<run id>" --video "<NN>" --attempt "<a1|c2-a1>" --mode <…> --model <id> --tool generate_video --stage <preflight|submit|job|upload|result> --response "<verbatim | none given>" --job "<job id(s)>" --credits "<refunded n>" --flagged-video "<V id + file, and/or the clip>" --trigger "[E|I] <suspected trigger>" --cause <prompt-wording|reference-video|image-reference|output|parameter|unknown> [--changed "<what the next request changes>"]
T caught-flag set --id CF-nnn --status cleared --cleared-prompt <the accepted request.json> --cleared-job <job id> [--rule "<general rule>"]
T caught-flag set --id CF-nnn --status persistent --note "<what was tried>"
T caught-flag list [--digest] [--model <id>] [--kind <k>] [--status open|cleared|persistent] [--run <id>] [--grep <text>]
T caught-flag reconcile --run <run id>
```

## CF-001 · 2026-10-12 · Two jobs refused within ~16 s, no reason, while the swapped celebrity's real face rode as the video reference
- **source:** agent
- **kind:** refused-no-reason
- **tool:** generate_video
- **stage:** job
- **run:** 20261010-020703-09
- **video:** 10
- **attempt:** a1
- **mode:** analyze-recreate
- **model:** wan3_0_prime
- **product:** Celsius Cherry Cola can (V03 recreate, celebrity replaced)
- **response:**
  ```text
  none given: job a78815fa failed after ~16 s, refunded 45 credits, no reason; the identical resubmit 36ed36b0 failed again after ~15 s, refunded, no reason
  ```
- **job:** a78815fa-9ad2-481d-8992-ba4f3ee5174b, 36ed36b0-bd54-4da2-bdde-5f7ae68890fe
- **ledger:** f0c7f366acbbb44642c5
- **credits:** 45 charged and refunded, twice
- **flagged prompt:**
  ```text
  [Core Task] Generate a real phone-shot clip: a short opener at a table and then a long held reaction in arena seats.  Use Video 1 for every movement, expression, gaze, the framing and camera, the room and the timing; do not reproduce any text, captions, usernames or watermarks from Video 1. The can corresponds to Image 3 and Image 4, which jointly define the same can and generate only one instance, adopting only its structure, material, colours and printed label (a white slim 355 ml aluminium can, a red-and-grey C-swoosh above the black CELSIUS wordmark with LIVE FIT, a cherries-and-cola illustration, SPARKLING CHERRY COLA in a magenta tag, a black band with three bullets and a silver-grey lower band); in Image 3 and Image 4 the can is deliberately small in the frame and keeps that small scale; do not use the framing, lighting, exposure, background, shadow or camera angle of Image 3 or Image 4.
  [Plot Summary] Video 1 opens on a man at a white table for about one second, then dissolves through white into a long shot of a man in arena seats; keep that dissolve at the same moment. The man at the table corresponds to Image 1 (replacing the man in the mustard jacket), and the man in the arena seats corresponds to Image 2 (replacing the man in the green coat over a cream hoodie), each adopting only the facial features and hairstyle of his image and keeping the clothing, body and pose of Video 1; do not use the background, props, clothing or lighting of Image 1 or Image 2. Shot 1: Image 1's man in the mustard jacket sits at a white table looking down at a phone in his hand. Shot 2, medium close, dim arena light with tan seats behind: Image 2's man in the green coat looks down at a phone in his right hand with a tired expression, then looks up and around, shifts his weight, and later sits still with his hands resting on his thighs, looking ahead and slightly down, as in Video 1. A closed Celsius Cherry Cola can stands upright on the white table at the right of the phone hand in shot 1, base on the table with a contact shadow, label turned about thirty degrees toward the lens; in shot 2, from the moment he lowers the phone, the can rests in his left hand on his left thigh at the lower edge of the frame, held upright around its body, label toward the lens, and stays in that hand until the end; it is part of this scene although Video 1 has none, exactly one can. The can is a small object, 15.7 cm tall and 5.5 cm across: it is shorter than his hand is long, spans from the heel of the palm to just above the fingertips, about two thirds the height of his head; it fills about one eleventh of the frame height in shot 2 and keeps this size. Dim arena light from above with a soft highlight on the can's upper left. Real-time speed. No dialogue. No background music.
  [Camera & Core Constraints] Keep every movement, gesture, expression, gaze and mouth movement of the people in Video 1 on the same frames, the props and how they are handled, the camera framing and handheld feel, the light, the room and the timing of Video 1 unchanged; no added, skipped, repeated or reordered action, no new gesture, no extra camera move, no re-staging, no new people, no change of pace. There is exactly one can: on the table in shot 1, in his left hand from the lowering of the phone onward in shot 2, small and constant in size, not duplicated, not vanished, not deformed, no scale drift; the can stays where it is and fingers or objects never pass through it. Do not show any text, subtitles, numbers, interface elements, or watermarks on screen; the only lettering is the printed label on the Celsius Cherry Cola can, exactly as in Image 3; do not reproduce any text, captions, usernames or watermarks from Video 1.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no scale drift, no cut-out edges, no slow motion, no speed ramps, no self-inserted cut points, no added or skipped action, no second can, no oversized can, no can taller than his hand is long, no can larger than a head, no open tab, no drinking from the can, no studio lighting on the can, no glow, no clipping
  ```
- **params:** model=wan3_0_prime · duration=15 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=video_references, image_references×4 · request=video-10-a1-failed-request.json
- **flagged inputs:**
  ```text
  video_references: 3a7335b2-8237-46c9-b063-d86fc1668797
  image_references: 6765ab6b-0e20-4bdf-b66e-f62ba55be255
  image_references: f4449894-2cfc-44fb-9a21-99c1be2f97dc
  image_references: f4b6de51-f7af-418e-af13-074b30f86bcb
  image_references: 9b93f5f2-b1ef-4562-be49-556443b461e5
  ```
- **flagged video:** run 09 V03 own-silent.mp4 (a real celebrity who is swapped but still visible in the video reference): C:/Users/Glaresquare1/.claude/analyze-then-pick/runs/20261010-020703-09/10-media/V03/own-silent.mp4
- **output:** none (the job produced no file)
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261010-020703-09\40-briefs\video-10-plan.md
- **suspected trigger:** [I] the swapped person's real face (a celebrity) in the video reference; both jobs died within seconds with no error text, and the third request without the video reference ran. Not confirmed by Higgsfield.
- **cause:** reference-video
- **what was changed:** after the second identical failure: planned without the video reference (image references + the action script written out, original audio restored), fidelity and sync judged on the sheet
- **outcome:** cleared: a changed request was accepted
- **cleared prompt:**
  ```text
  [Core Task] Generate a real phone-shot clip of 15 seconds: a one-second opener of a man at a white table that dissolves through white into a long held shot of a man in dim arena seats. The man in the opener corresponds to Image 1, adopting his facial features, hairstyle and build; he wears a mustard-yellow jacket over a black hoodie. The man in the arena corresponds to Image 2, adopting his facial features, hairstyle and build; he wears a long olive-green wool coat over a cream hoodie; do not use the background, props, clothing or lighting of Image 1 or Image 2. The can corresponds to Image 3 and Image 4, which jointly define the same can and generate only one instance, adopting only its structure, material, colours and printed label (a white slim 355 ml aluminium can, a red-and-grey C-swoosh above the black CELSIUS wordmark with LIVE FIT, a cherries-and-cola illustration, SPARKLING CHERRY COLA in a magenta tag, a black band with three bullets and a silver-grey lower band); in Image 3 and Image 4 the can is deliberately small in the frame and keeps that small scale; do not use the framing, lighting, exposure, background, shadow or camera angle of Image 3 or Image 4.
  [Plot Summary] Generate single shot per scene, handheld phone realism, real-time speed, no slow motion. Scene 1, about one second, fixed medium shot from table height: Image 1's man sits at a white table in a plain bright room looking down at a phone in his right hand, a closed Celsius Cherry Cola can standing upright on the table at the right of his phone hand, base on the table with a contact shadow, label turned about thirty degrees toward the lens. Then a white flash dissolve. Scene 2, about fourteen seconds, a fixed medium close shot in dim arena light with rows of tan seats behind: Image 2's man in the long olive-green coat over the cream hoodie sits in an arena seat looking down at a phone in his right hand with a tired, blank expression; after about three seconds he lowers the phone, looks up, glances slowly around, shifts his weight, and settles; from the moment the phone is lowered a closed Celsius Cherry Cola can rests in his left hand on his left thigh at the lower edge of the frame, held upright around its body, label toward the lens, and stays in that hand until the end; for the last ten seconds he sits almost still, his hands resting on his thighs, eyes ahead and slightly down, breathing slowly, tired. The can is a small object, 15.7 cm tall and 5.5 cm across: shorter than his hand is long, spanning from the heel of the palm to just above the fingertips, about two thirds the height of his head, only as thick as three fingers; it fills about one eleventh of the frame height in scene 2 and keeps exactly this size; always exactly one can, closed, never opened, never drunk from, never duplicated. Dim arena light from above with a soft highlight on the can's upper left. No dialogue. No background music.
  [Camera & Core Constraints] One person per scene, no other people in focus, no camera shake, no added gesture, no change of pace. Do not show any text, subtitles, numbers, interface elements, logos or watermarks on screen; the only lettering is the printed label on the Celsius can, exactly as in Image 3.
  [Negative Prompts] no subtitles, no on-screen text, no watermark, no face distortion, no identity drift, no costume changes, no scale drift, no cut-out edges, no slow motion, no speed ramps, no self-inserted cut points, no second can, no oversized can, no can taller than his hand is long, no can larger than his head, no open tab, no drinking from the can, no studio lighting on the can, no glow, no clipping, no celebrity likeness, no logos on the clothing
  ```
- **prompt change:**
  ```text
  - [Core Task] Generate a real phone-shot clip: a short opener at a table and then a long held reaction in arena seats.
  - Use Video 1 for every movement, expression, gaze, the framing and camera, the room and the timing;
  - do not reproduce any text, captions, usernames or watermarks from Video 1.
  + [Core Task] Generate a real phone-shot clip of 15 seconds: a one-second opener of a man at a white table that dissolves through white into a long held shot of a man in dim arena seats.
  + The man in the opener corresponds to Image 1, adopting his facial features, hairstyle and build;
  + he wears a mustard-yellow jacket over a black hoodie.
  + The man in the arena corresponds to Image 2, adopting his facial features, hairstyle and build;
  + he wears a long olive-green wool coat over a cream hoodie;
  + do not use the background, props, clothing or lighting of Image 1 or Image 2.
  - [Plot Summary] Video 1 opens on a man at a white table for about one second, then dissolves through white into a long shot of a man in arena seats;
  - keep that dissolve at the same moment.
  - The man at the table corresponds to Image 1 (replacing the man in the mustard jacket), and the man in the arena seats corresponds to Image 2 (replacing the man in the green coat over a cream hoodie), each adopting only the facial features and hairstyle of his image and keeping the clothing, body and
  - do not use the background, props, clothing or lighting of Image 1 or Image 2.
  - Shot 1: Image 1's man in the mustard jacket sits at a white table looking down at a phone in his hand.
  … 29 more changed sentences
  ```
- **cleared params:** model=wan3_0_prime · duration=15 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=image_references×4 · request=video-10-request.json
- **cleared job:** 67d930fc-1193-4f23-93bc-d3524937b9e9
- **rule:** When a source's swapped person is a recognisable real face, expect the service to refuse the video reference within seconds with no text; after two identical refunded failures plan without the video reference and say fidelity and sync are at risk; never send a third identical request.
- **status:** cleared
- **log:** 2026-10-12 backfilled from the run 09 ledger and notes on 2026-10-12
- **promoted to:** —

## CF-002 · 2026-10-12 · Server answered with a preset_recommendation notice (IN THE DARK) instead of creating the job
- **source:** agent
- **kind:** preset-notice
- **tool:** generate_video
- **stage:** submit
- **run:** 20261002-232019-02
- **video:** 02
- **attempt:** a1
- **mode:** analyze-recreate (runs 20261001-195409-01 and 20261002-232019-02) and analyze-create (20261002-000344-01)
- **model:** wan3_0_prime
- **product:** Celsius can (runs 20261001-195409-01, 20261002-000344-01, 20261002-232019-02: about 20 first submissions)
- **response:**
  ```text
  server returned a preset_recommendation notice (preset IN THE DARK, id 24bae836-2c4a-48e0-89b6-49fcc0b21612) instead of a job; no job created, nothing charged
  ```
- **job:** none (no job id returned)
- **ledger:** not recorded
- **credits:** not recorded
- **flagged prompt:**
  ```text
  [Core Task] Generate a realistic, phone-shot vertical comedy clip that recreates Video 1 beat for beat. Video 1 is used only as the reference for motion, timing, framing, camera and location: keep its actions, timing, camera position and setting exactly, but do not inherit the appearance of its person and do not reproduce any captions, subtitles, text, usernames or watermarks from Video 1. The man corresponds to Image 1, adopting his facial features, short hair, goatee and light-blue knit polo shirt; Image 1 is only his identity, not its car seat, seat belt or window. He also wears black nitrile gloves on both hands. The drink can corresponds to Image 2 and Image 3, which jointly define a single can (Image 2 shows the front label, Image 3 the opened lid with its tab up): one CELSIUS Sparkling Orange can: a slim, tall 355 ml aluminium can with a white body, an orange-to-silver "C" swoosh, an orange-slice graphic, a brushed silver lower band and a black lid, opened. Keep its exact silhouette and proportions without deformation, keep its printed label exactly as in Image 2, and keep it at real size. A commercial food-truck kitchen with a stainless-steel counter, squeeze bottles and a steel extractor hood; cool overhead fluorescent light. The camera sits low at counter level, locked off. In the foreground on the steel counter stands a tall clear plastic cup about two-thirds full. The drink in the cup is CELSIUS Sparkling Orange poured from that can: a bright yellow-orange, clear, lightly sparkling drink with fine rising bubbles, exactly the colour, clarity and bubbles of the liquid in Image 4 (only the liquid of Image 4; not its mug, can, counter or kitchen). The opened, nearly empty can stands upright on the counter just right of the cup, at the same depth, label toward the camera, with a soft contact shadow; it stays there untouched for the whole video. Only one can in the scene. The can is part of this scene from the first frame, although Video 1 has none.
  [Plot Summary]
  Generate single shot. [0-0.6s] He glances left, then right, checking that nobody is watching.
  [0.6-1.4s] He holds his left hand above the cup and sprinkles a fine pinch of white powder from his fingertips into the drink; the powder falls in a thin stream and dissolves, and the drink keeps its colour.
  [1.4-2.0s] He brushes his gloved hands together.
  [2.0-3.0s] He pinches more powder over the cup, then dips two gloved fingertips into the drink and stirs it.
  [3.1-3.8s] He raises the stirring fingertip to his lips as if tasting it, with a thoughtful expression.
  [3.8-5.0s] He rubs his hands together and looks up and away innocently.
  [5.0-6.6s] He glances left and walks out of frame to the left.
  [6.6-7.4s] The cup and the open can remain alone on the counter.
  [Audio Style] No background music; no sound is needed.
  [Camera & Core Constraints] Camera as in Video 1. Fixed camera, real-time speed; the cup and the can never move; the drink level stays the same.
  [Negative Prompts] no subtitles, no captions, no on-screen text other than the can's own printed label, no watermark, no identity drift, no face distortion, no extra fingers, no scale drift, no second can, no slow motion, no extra people
  ```
- **params:** model=wan3_0_prime · duration=8 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=image_references×4, video_references · request=video-02-request.json
- **flagged inputs:**
  ```text
  image_references: 958592bd-cc96-47be-b695-57f7af063efc
  image_references: f28a7580-a808-4b5a-b4de-2bce51e46d1d
  image_references: b067e029-09ae-4f65-8b6c-600171ab3f13
  image_references: 959d11f4-e91c-4610-b83b-9d97c4c7eae5
  video_references: 0aa3797d-9a4a-4baa-9628-713da6480505
  ```
- **flagged video:** none (a prompt-level reroute, no video was sent)
- **output:** none (the job produced no file)
- **plan:** C:\Users\Glaresquare1\.claude\analyze-then-pick\runs\20261002-232019-02\40-briefs\video-02-plan.md
- **suspected trigger:** [I] the server matched the prompt to its IN THE DARK preset and asked for a choice instead of creating the job; the exact prompt words that match are not identified
- **cause:** prompt-wording
- **what was changed:** resubmitted the same params literally with declined_preset_id set to the preset's id
- **outcome:** cleared: a changed request was accepted
- **cleared prompt:**
  ```text
  [Core Task] Generate a realistic, phone-shot vertical comedy clip that recreates Video 1 beat for beat. Video 1 is used only as the reference for motion, timing, framing, camera and location: keep its actions, timing, camera position and setting exactly, but do not inherit the appearance of its person and do not reproduce any captions, subtitles, text, usernames or watermarks from Video 1. The man corresponds to Image 1, adopting his facial features, short hair, goatee and light-blue knit polo shirt; Image 1 is only his identity, not its car seat, seat belt or window. He also wears black nitrile gloves on both hands. The drink can corresponds to Image 2 and Image 3, which jointly define a single can (Image 2 shows the front label, Image 3 the opened lid with its tab up): one CELSIUS Sparkling Orange can: a slim, tall 355 ml aluminium can with a white body, an orange-to-silver "C" swoosh, an orange-slice graphic, a brushed silver lower band and a black lid, opened. Keep its exact silhouette and proportions without deformation, keep its printed label exactly as in Image 2, and keep it at real size. A commercial food-truck kitchen with a stainless-steel counter, squeeze bottles and a steel extractor hood; cool overhead fluorescent light. The camera sits low at counter level, locked off. In the foreground on the steel counter stands a tall clear plastic cup about two-thirds full. The drink in the cup is CELSIUS Sparkling Orange poured from that can: a bright yellow-orange, clear, lightly sparkling drink with fine rising bubbles, exactly the colour, clarity and bubbles of the liquid in Image 4 (only the liquid of Image 4; not its mug, can, counter or kitchen). The opened, nearly empty can stands upright on the counter just right of the cup, at the same depth, label toward the camera, with a soft contact shadow; it stays there untouched for the whole video. Only one can in the scene. The can is part of this scene from the first frame, although Video 1 has none.
  [Plot Summary]
  Generate single shot. [0-0.6s] He glances left, then right, checking that nobody is watching.
  [0.6-1.4s] He holds his left hand above the cup and sprinkles a fine pinch of white powder from his fingertips into the drink; the powder falls in a thin stream and dissolves, and the drink keeps its colour.
  [1.4-2.0s] He brushes his gloved hands together.
  [2.0-3.0s] He pinches more powder over the cup, then dips two gloved fingertips into the drink and stirs it.
  [3.1-3.8s] He raises the stirring fingertip to his lips as if tasting it, with a thoughtful expression.
  [3.8-5.0s] He rubs his hands together and looks up and away innocently.
  [5.0-6.6s] He glances left and walks out of frame to the left.
  [6.6-7.4s] The cup and the open can remain alone on the counter.
  [Audio Style] No background music; no sound is needed.
  [Camera & Core Constraints] Camera as in Video 1. Fixed camera, real-time speed; the cup and the can never move; the drink level stays the same.
  [Negative Prompts] no subtitles, no captions, no on-screen text other than the can's own printed label, no watermark, no identity drift, no face distortion, no extra fingers, no scale drift, no second can, no slow motion, no extra people
  ```
- **prompt change:**
  ```text
  not computed (the entry has no flagged prompt)
  ```
- **cleared params:** model=wan3_0_prime · duration=8 · aspect_ratio=9:16 · resolution=720p · generate_audio=False · enable_thinking=True · medias=image_references×4, video_references · request=video-02-request.json
- **cleared job:** none yet
- **rule:** A generate_video call may come back as a preset_recommendation notice with no job; it is a reroute, not a content block: set declined_preset_id to the notice's preset id on the one literal retry, never change the wording, never ask the user.
- **status:** cleared
- **log:** 2026-10-12 backfilled from the ledgers of runs 20261001-195409-01, 20261002-000344-01 and 20261002-232019-02 (the model of those runs was read from the request file: check the model field)
- **promoted to:** —
