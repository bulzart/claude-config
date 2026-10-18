## 3b. Videos longer than one generation

A video longer than the locked model's maximum per generation (`models/index.json →
continuation.max_s`) is made of clips. **Analyze Mode:** a video over 30 s needs the user's
permission before any of its clips is generated (command A7b). Only the generated content counts:
reference inserts such as memes are cut from the reference (§3c), never generated.

**Fill one generation first.** Seedance 2.5 is built for "coherent videos up to 30 seconds long…
without multi-segment stitching" [OFFICIAL]. Every provider's guidance agrees: split at cuts and
scene turns, and continue only a single continuous take. Higgsfield's own advice is: "To build a
longer sequence, use the last frame of one clip as the starting image for the next, then join them
in an editor" [HF].

