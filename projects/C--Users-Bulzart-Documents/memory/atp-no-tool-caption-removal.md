---
name: atp-no-tool-caption-removal
description: /analyze-then-pick agents never remove captions/names/patches from a source with tools (inpaint, delogo, crop); the original method is top-priority clean-plate prompt lines + pushed character-swap script (user 2026-10-13)
metadata:
  type: feedback
---

User, 2026-10-13: "the agents should not try to remove captions by any tools, rather just use high priority script no exception prompt pushing character swap and no text in the video generation, just like the old version used to do ... the idea was only use cases and problems catched to be generalized in the pipeline, not change it."

**Why:** the CE-001..094 pass had added caption inpainting and name removal in source preparation; that changed the method instead of generalising lessons. Old builds are in `Documents/prompts/*.bak-*`.

**How to apply:** Analyze Mode: clean-plate lines (no subtitles, no on-screen text, do not inherit text/captions/usernames/watermarks) are the highest-priority prompt lines, never trimmed; character swap is pushed in the script; a name or patch is one named replace sentence. No inpaint/delogo/crop on Recreate sources. Edit Mode removal methods are unchanged. New lessons add use cases and checks, never replace the pipeline's method.

Index line before the 2026-11-14 compaction of MEMORY.md (kept here so nothing is lost): Analyze Mode never removes captions/names with tools; top-priority clean-plate lines + pushed character-swap script (user 2026-10-13); lessons add cases, never change the method

Index line before the 2026-11-20 compaction of MEMORY.md (kept here so nothing is lost): Analyze Mode never removes captions/names with tools; clean-plate lines + character-swap script (user 2026-10-13)
