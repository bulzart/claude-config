## 7. Translating the plan into the selected model's language

1. Open the selected model guide at **§4.0 (official examples and patterns)** and write a
   **pattern card** into `<run>/50-requests/video-NN-pattern.md`:
   - information order;
   - sentence style and length;
   - temporal notation (chronological sentences, stages, timecodes, shots);
   - subject motion vs. camera motion;
   - camera vocabulary;
   - reference syntax (`@Image1`, `<<<element>>>`, "image one");
   - frame-anchor wording;
   - audio and dialogue syntax;
   - how exclusions are phrased;
   - prompt length limits.
   These patterns are engineering principles to adapt, not text to copy.
2. **Decide the channel for each element of the plan:**
   - **parameters**: duration, aspect, resolution, audio, genre, mode, extension direction;
   - **references**: identity, product geometry, scene plate, motion or camera driver, first/last
     frame. By sub-mode:
     - **Create:** only client assets and generated frames, never a reference video, frame or clip;
     - **Recreate:** the reference's prepared own-content source is the edit master, and the
       client's assets replace and add;
   - **prompt**: action, chronology, relationships, light, camera behaviour, states, exclusions;
   - **post-production, local** (`atp.py`): conform to 720×1280, source-audio restoration, trims,
     multi-clip joins, cutting the reference inserts;
   - **post-production, CapCut** (Analyze Mode, `capcut-assembly.md`): every overlay text as a text
     layer, the inserts in their gaps, the final edit.
   Nothing is expressed twice in conflicting ways.
3. Write the prompt in the model's pattern:
   - chronological if the official examples are chronological;
   - concise if they are concise;
   - subject motion separated from camera motion if the examples separate them;
   - the documented syntax for references and frames.
   Include the ledger's state anchors (start state, key state changes, end state) and the
   integration facts from §4 in the model's own phrasing. Express a natural placement as §4b.5
   says. Write every use beat as initial state → operation on the named part → observable result
   with its contact point, carry every count with its number and restate it after exits,
   occlusions, cuts and hand-offs, and add one targeted exclusion per product for its own wrong use
   (`anomaly-catalog.md` §3). Do not dump the analysis into the prompt.
4. Check the prompt against the pattern card and the model guide's §7 checklist, then save it to
   `<run>/50-requests/video-NN-request.json`: model, params, medias with their role and meaning, the
   prompt, the post-processing plan, and the preflight cost.

