## 2. What never changes

- **Coverage.** At every level every second of every video is sampled (at least 2 frames per second; a static stretch keeps at least
  1), every cut keeps its last and first frame, and the first second and each motion peak are densified. Nothing is skipped to save
  frames.
- **The floors** (`T effort` raises a lower custom value to them): references 2 fps, and 6 fps around motion; 2 densified ranges per
  reference; QC storyboards 4 fps (the product's anchor is read at least every 0.25 s); QC checkpoint sheets 15 fps (frames at most
  1/15 s apart, inside the 0.1 s sync and contact tolerances); 4 extra full-resolution frames per QC pass.
- **Every frame, at every level** (`T qc --dense "<label>:<a>-<b>@full"`): the first second, every insert, seam and cut edge, and each
  voiceover phrase start checked for lips, where a single frame (a replaced performer, a flash, a jump) is the failure.
- **Not scaled at all:** the plan of a produced video densifies its own source as its steps say (the source action script, the sync
  anchors, the spot, the size reckoning); every checkpoint the plan names; a full QC pass for every attempt; the label-legibility and
  size checks with their full-resolution frames; the sync check; the Loupe consult; OCR (it runs on the CPU and costs no tokens).
- **A budget never skips a check.** A card field or a check that cannot be judged within its budget takes the range or the frame it
  needs and says so; "unknown, and why" is written only when even that cannot settle it.
