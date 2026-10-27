## 2. What never changes

- **The judges.** QC (X9) and its Loupe consult work exactly as they always have, at every level: the same storyboard and checkpoint
  rates, every frame they view, every sample image; Loupe itself and its keeper are never touched by the level.
- **Coverage.** At every level every second of every reference is sampled (at least 2 frames per second; a static stretch keeps at
  least 1), every cut keeps its last and first frame, and the first second and the motion peaks are densified. Nothing is skipped to
  save frames.
- **The floors** (`T effort` raises a lower custom value to them): references 2 fps, and 6 fps around motion; the 4 strongest motion
  peaks of a reference, each over ±0.5 s; 2 densified ranges per reference; the pilot runs first from 5 videos at the latest. The agents
  at once (1 to 5) change only how fast tokens are spent, never what is checked.
- **Pixels.** No level makes a frame, a sheet cell or a video smaller: only how many frames are taken changes.
- **Not scaled at all:** the plan of a produced video densifies its own source as its steps say (the source action script, the sync
  anchors, the spot, the size reckoning); every planning and generation step; OCR (it runs on the CPU and costs no tokens).
- **A budget never skips what a card needs.** A card field that cannot be judged within the close-up budget takes the range it needs and
  says so; "unknown, and why" is written only when even that cannot settle it.
