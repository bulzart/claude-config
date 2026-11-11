---
name: awl-static-drawn-annotations
description: "user 2026-11-11 (Static): the agents that edit a video can draw and animate over a still (dashed leader lines drawn on, highlights, hand-lettered words) as transparent clips CapCut plays; a drawing explains the picture, never a sticker"
metadata:
  type: feedback
---

User 2026-11-11: "the agents editing the video should also to be able to draw in capcut, and animate too, like combining flux klein image + drawing or animation along with other edit capabilities, like this example too: there is a static image but also a drawing animation (those width,height... lines are drawn and animated frame by frame) elaborating the results of the training a specific way" (a pen sketch of an arm, three dashed white curved lines drawn on from the words Width, Height, Depth to the muscle regions, each ending in a short bar, the regions filled red, blue, green).

**Why:** the references' videos explain a point by drawing on the picture; the Static pipeline only had still moves, joins, captions, labels and the effects folder.

**How to apply:** the video's own agent writes `drawings` into an image's plan entry once the still is viewed (static §5 "Drawings"): `T draw grid` (+ `--crop`, `--step`) for coordinates, `T draw words` for the spoken words' times, `T draw render` for the transparent clip (QuickTime Animation / PNG-in-MOV / ProRes 4444, whichever the CapCut effects check showed playing) and three previews to look at; `T slideshow plan` adds the clip as an overlay on a `draw` track, `T capcut-effects` writes it. The image holds still under a drawing (motion none); nothing has a stock look (the references' annotation pattern, §2, or the agent's own inside the style lock, with a written reason); never a sticker, emoji, icon, badge or decorative arrow (router item 6 says a drawn annotation is not one); words in the video's language, scripts that need shaping go as CapCut labels. CapCut has no freehand drawing tool and its masks are unverified on this PC, which is why the drawing is a clip inside the project, one track each. Related: [[awl-niche-family-and-approach]], [[analyze-with-loupe-command]].

**Extra fonts (same day):** the user also gave the agents permission to download extra fonts when the listed ones are not a good match for the video (T fetch-font: Fontsource, OFL 1.1 / Apache 2.0 only, into onts/ with a README row; CapCut's own cloud fonts cannot be fetched by a tool, only by its app).
