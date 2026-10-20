## 5. Failure modes
| Failure | Trigger | Mitigation |
|---|---|---|
| Original object still visible | Fast motion, small target, weak target description [SECONDARY test] | Unique anchor; exclusion sentence; 720p+; shorter clip; else Seedance 2.5 edit |
| Replacement ignores trajectory at contact | Hand interactions [SECONDARY] | Inspect contact frames in QC (`frames --range` at 15 fps); regenerate if broken |
| Geometry deformation | Replacement shape differs a lot from the original [HF] | Regenerate with a reference-to-video model instead of swapping |
| Captions survive | Untargeted text is preserved | Local `clean`, removal clause, or Seedance edit |
| Wrong aspect | Non-9:16 source | Reframe the source first |
| Identity bleed | Motion Transfer copies the driver's look | Explicit "do not use the person/clothing of @Video1" + a strong identity image |

