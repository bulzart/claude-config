# Fix prompt template — `90-postgen\fix-prompts.md` (post-generation; consistent with `post-generation-playbook.md` §2.5)

One block per flagged clip (S2 with a regenerate decision, S3, S4), ready to paste into the generator or
to hand to the generator agent when P0 = "Regenerate flagged clips first". The fix prompt is the full
corrected prompt (same template as `prompt-template.md` / `edit-prompt-template.md`), with the changed
lines marked `✱`, never a diff alone. Positive phrasing (what SHOULD be seen); keep everything that
passed; reuse the seed only when the generator exposes one (Higgsfield seedance_2_5: none → "unknown");
for continuity faults attach the neighbouring clip's boundary frame as a reference. No captions anywhere.

```markdown
### Fix — clip 03 (round 1)   anomalies: A05, A09   severity: S3
Reuse: seed unknown (Higgsfield exposes no seed); reference frames: 50-prompts\references\product-label.jpg (label, unchanged),
      90-postgen\qa\clip-02\last-00m15.00s.jpg (from clip_frames.py) as @Image 3 = exact first frame (continuity with clip 02) [omni: "@Image 3 is the exact first frame; continue forward…"]
Keep: camera (locked-off MCU), lighting (window left), action beats 1–5, audio design.
CHANGE (✱ lines): the label must read exactly "SUNNY OAT / Orange Cream / 16 FL OZ" as in @Image 2, label facing the camera whenever visible,
      the wordmark stays sharp and unchanged during the pour; the cap remains in her left hand and is visible on the counter by the end state (so clip 04's first frame matches).
Platform: mode omni_reference · duration 15 · aspect 9:16 · resolution 1080p · generate_audio true · attachments: product-front.jpg → @Image 1, product-label.jpg → @Image 2, qa\clip-02\last-00m15.00s.jpg → @Image 3

Prompt (full, corrected):
ASSET BINDINGS
@Image 1 = …
@Image 2 = … Use only: the logo and the exact wording "SUNNY OAT / Orange Cream / 16 FL OZ". ✱
@Image 3 is the exact first frame; continue forward from that moment; do not replay what happened before it. ✱
…
PRODUCT INVARIANTS
Preserve exactly the label text and layout of @Image 2 in every frame where the label is visible; the wordmark never changes spelling. ✱
END STATE (15 s)
… the orange cap lies on the counter to the left of the glass. ✱
CONSTRAINTS
…
Expected: 15 s, 9:16. After regeneration: re-run clip QA on clip 03 and the continuity check 02→03→04.
```

Edit-approach fix (segment): same block; the CHANGE lines tighten the `Replace only …` scope (add the
"as seen" description that was missed, a timestamp window "from 4-6 seconds in @Video1", or an anchor
still `@Image3` of an approved segment); the source segment and audio mux stay the same.

Rounds: `fixes-round-N` numbering continues from the anomaly check (post-generation rounds start at 1
again but are labelled `postgen round N`). The loop ends when every kept clip is ≤ S1 or the owner
accepts an S2 trim (P0 answered "Edit now" with trims recorded in `qa.json.windows`).
