---
name: awl-real-things-look-like-themselves
description: "/analyze-with-loupe Static: a company/brand the story is about shows its official logo (composited, never drawn) where it comes in and again later; a known person looks like them; known places/things too"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 6df6fb40-e7ad-4b91-b765-6c6c020da849
  modified: 2026-11-07T08:45:11.497Z
---

User 2026-11-07: "if there's a company, or a brand being talked about, their logo should appear somewhere, or if talking about famous
person whos appeareance is known it should really look like them, and so on"; the logo "somewhere in the beginning of the story where
they first found the company, and then somewhere latter, because we need to let the viewer ... have more context about who we're talking
about". Then asked whether the 2008 scene's logo was right for that time (it was not: the Bélo is from July 2014, the name Airbnb from
March 2009).

**Why:** viewers need to recognise who the video is about; a stand-in shape or an unlike face loses them.

**How to apply:** static §5 "Real things look like themselves": `T fetch-image --kind logo|photo` (official source or Wikimedia Commons,
licence recorded), the plan's `logo` field with a blank surface in the prompt, `T image brand --logo --box [--card] [--cover]` after the
image is made (a model redraws logos wrong); a known person's anchor rides with public photos. Mind the story's date: a dated scene
should not show a logo from years later (open question to the user 2026-11-07: period-accurate name vs present logo). Related:
[[analyze-with-loupe-command]].
