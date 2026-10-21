---
name: always-full-paths
description: "User wants every file path given in full (absolute, from the drive letter), never relative to a run folder or a stated base"
metadata:
  node_type: memory
  type: feedback
  originSessionId: fd23b3ce-bd75-4669-95d5-20d1bbdbcdef
  modified: 2026-10-21T21:59:20.141Z
---

When naming files to the user, always write the complete absolute path (e.g. `C:\Users\Glaresquare1\.claude\analyze-with-loupe\runs\<run>\10-media\V09\prepared\source-placeholder-layer.png`), never a path relative to a base folder named once above (e.g. `10-media\V09\...`).

**Why:** user 2026-10-21: "give me always full paths not like this 10-media\V09\prepared\source-placeholder-layer.png".

**How to apply:** every chat message, summary, wrap-up and report that points to a file or folder, in every pipeline and task; one path per file, copy-pasteable as is.
