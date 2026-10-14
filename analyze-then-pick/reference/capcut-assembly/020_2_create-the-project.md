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

