---
name: awl-static-drawn-annotations
description: "user 2026-11-11 (Static): the agents that edit a video can draw and animate over a still (dashed leader lines drawn on, highlights, hand-lettered words) as transparent clips CapCut plays; a drawing explains the picture, never a sticker"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 0ff74cb4-bc5e-4c0e-82b7-c94ab48b8c77
  modified: 2026-11-11T11:45:43.154Z
---

User 2026-11-11: "the agents editing the video should also to be able to draw in capcut, and animate too, like combining flux klein image + drawing or animation along with other edit capabilities, like this example too: there is a static image but also a drawing animation (those width,height... lines are drawn and animated frame by frame) elaborating the results of the training a specific way" (a pen sketch of an arm, three dashed white curved lines drawn on from the words Width, Height, Depth to the muscle regions, each ending in a short bar, the regions filled red, blue, green).

**Why:** the references' videos explain a point by drawing on the picture; the Static pipeline only had still moves, joins, captions, labels and the effects folder.

**How to apply:** the video's own agent writes `drawings` into an image's plan entry once the still is viewed (static §5 "Drawings"): `T draw grid` (+ `--crop`, `--step`) for coordinates, `T draw words` for the spoken words' times, `T draw render` for the transparent clip (QuickTime Animation / PNG-in-MOV / ProRes 4444, whichever the CapCut effects check showed playing) and three previews to look at; `T slideshow plan` adds the clip as an overlay on a `draw` track, `T capcut-effects` writes it. The image holds still under a drawing (motion none); nothing has a stock look (the references' annotation pattern, §2, or the agent's own inside the style lock, with a written reason); never a sticker, emoji, icon, badge or decorative arrow (router item 6 says a drawn annotation is not one); words in the video's language, scripts that need shaping go as CapCut labels. CapCut has no freehand drawing tool and its masks are unverified on this PC, which is why the drawing is a clip inside the project, one track each. Related: [[awl-niche-family-and-approach]], [[analyze-with-loupe-command]].

**Extra fonts (same day):** the user also gave the agents permission to download extra fonts when the listed ones are not a good match for the video (T fetch-font: Fontsource, OFL 1.1 / Apache 2.0 only, into fonts/ with a README row; CapCut's own cloud fonts cannot be fetched by a tool, only by its app).

**Built 2026-11-11:** `T draw` (grid|words|render|list, standalone `--spec`) and `T fetch-font` exist in awl.py, the tests pass (t01, t02 501 PASS). Demo for the user to check in CapCut: project `11_Nov_2026_DEMO-drawings` (image 31 of run 20261106 with the narration of lines 60-61 and a drawing timed to the heard words; made through `T draw render`, `T slideshow plan`, `T capcut-effects`, `T capcut-repair --keep-text`), its media in `C:\Users\Bulzart\Documents\awl-drawing-demo\` (delete the project first, then the folder). User 2026-11-11: "i'll go and open capcut and validate after finish": how CapCut plays the qtrle clip over the still is theirs to see; nothing here plays it. If it shows wrong, see alpha_video in `data/capcut-catalogue.md`.
