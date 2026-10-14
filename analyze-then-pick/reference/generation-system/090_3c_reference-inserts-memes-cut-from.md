## 3c. Reference inserts (memes): cut from the reference, never generated

An **insert** is footage that interrupts the reference's own scene: a meme clip, a film or TV
snippet, a reaction image, usually with its own sound (analysis card → "Inserts"). Example: a 27 s
reference has 13 s of its own footage, a 2 s meme with a meme sound, then 12 s more footage.

1. **Generate only the reference's own content.** In the example that is one 25 s generation; the
   time budget (§2.2) covers those 25 s.
2. **Split points.** Each insert k gets a split point in the generated timeline:
   `split_k = t_in_k − (sum of the earlier inserts' durations)`. In the example, 13.0 s.
   - Plan a natural beat boundary there. The line or action before the insert ends on it (the
     setup), and the content after it resumes as the reference does after the insert.
   - A sentence never runs across a split point.
3. **Measure the real split on the output.** After generation, put each split on the generated
   clip's actual boundary within ±0.5 s of the plan: the pause after the line, or a planned cut.
   Measure it with the transcript and cuts from `atp.py prep-video`, or a dense frame sheet.
4. **Cut each insert from the original reference video, with its sound:**
   `atp.py trim --video "<reference original>" --start <t_in> --end <t_out> --out <run>/30-assets/inserts/<V>-iK.mp4`,
   with `t_in` / `t_out` on the cut frames from `cuts.json`, moved inward past any dissolve, flash or
   frame of the replaced performer at the edge, so that every frame of the cut holds only the insert's own
   content (CE-016: an edge that kept the original performer left the replaced person in the final). Then
   `atp.py conform` to 720×1280.
   - **A video meme is always cut, never screenshotted.**
   - A still image held for the insert's duration is cut the same way, which keeps its sound. Or
     take a lossless screenshot (`atp.py last-frame` on the cut) and place it with the insert's
     sound under it.
   - Overlays the reference added on top of the insert (its caption, username or watermark) are
     removed with `atp.py clean`. The meme's own built-in text stays. If removal isn't clean, say
     so in the brief.
   - **The reference timeline and its ORIGINAL audio stay whole** (Recreate; CE-024, CE-025). The edge span
     removed from an insert stays on the timeline as pure transition colour (white or black), every
     duration unchanged, so the original audio stays one untouched segment under the whole video: never a
     shortened timeline, never audio assembled from pieces. The picture runs into and out of the gap on real
     moving footage (the last and first frames of the moving piece itself fade); a held or frozen frame under
     a flash or dissolve reads as a glitch and is never used. An insert that starts or ends on a brightness
     step is faded in or out from the gap colour.
5. **The 30 s permission counts only the generated content.** In the example, 25 s means one
   generation, so no question.
6. **Assembly happens in CapCut** (`capcut-assembly.md`): the generated video split at each point,
   with each insert in its gap.
7. **The product stays put across inserts.** The placed product keeps its anchor on both sides of
   an insert (§4b); inserts never show it.

