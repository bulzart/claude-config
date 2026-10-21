---
name: no-genjutsu-use-wan-prime
description: "User dropped Genjutsu Object Swap mid-run (2026-10-21) for Wan 3.0 Prime: \"all work has to be on wan 3.0 prime from now on, not use genjutsu anywhere\""
metadata:
  node_type: memory
  type: feedback
  originSessionId: fd23b3ce-bd75-4669-95d5-20d1bbdbcdef
  modified: 2026-10-21T21:54:14.653Z
---

On 2026-10-21, during the Celsius Recreate run `20261021-224049-21` of /analyze-with-loupe, the user switched the locked model from Genjutsu Object Swap (`hf_mult_replace_object`) to Wan 3.0 Prime (`wan3_0_prime`): "forget genjutsu lets use wan 3.0 prime", then "all work has to be on wan 3.0 prime from now on, not use genjutsu anywhere".

**Why:** the Genjutsu pilot (V09) needed one change per call, left the performer's face unswapped when the call also removed the caption, returned 24 fps output squeezed shorter than the source, and could only replace objects, never add the can (a composited placeholder workaround). The user ended it.

**How to apply:** in that run, every request, contract and agent uses `wan3_0_prime`; no Genjutsu call, pass or wording anywhere. For later runs, the model is still the user's pick from the menu; do not recommend Genjutsu for Recreate face or product swaps without saying what this pilot showed. Related: [[analyze-with-loupe-command]].
