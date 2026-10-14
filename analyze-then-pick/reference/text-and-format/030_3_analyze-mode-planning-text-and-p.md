## 3. Analyze Mode: planning text and placing it in CapCut

1. **Read the reference's text** from the analysis card ("Overlay text"):
   - its wording and role (hook, "POV:" line, running caption, label, payoff line, context-bearing
     overlay: §1);
   - position: `y_rel` / `x_rel` of its centre, from `ocr.json` and the sheets;
   - timing: in and out, in seconds;
   - style: colour, size relative to the frame, outline or box, case, line breaks.
   No text role in the reference or its family → no text.
2. **Write the text** per §1 "Wording". Keep it short, in the family's tone and density:
   - hooks ≤ 8 words;
   - running captions 1–4 words per event, and ≤ 2 lines;
   - labels ≤ 5 words;
   - a meme caption keeps its natural length.
3. **Time it on the final timeline**, after inserts are placed (`generation-system.md` §3c):
   - ≥ 0.4 s plus ~0.25 s per word on screen;
   - never overlapping itself;
   - captions follow the generated speech when there is speech: take the times from the clean
     video's transcript (`atp.py prep-video`);
   - the hook appears in the first 0–0.3 s when the family's hook is textual;
   - a caption that spans the whole reference spans the whole video;
   - text that plays on the product (a logo pun, a reveal) is timed to the moment the product
     really shows it in the clean video, measured at 30 fps, never to the plan
     (`generation-system.md` §5b).
4. **Place it at the reference's height, always horizontally centred**, inside the 9:16 safe area
   (the user, 2026-10-09: "make the text be in the center, whether up, down or in the middle";
   CE-010):
   - every text layer is centred left to right: CapCut `posX = 0`, centre alignment; the
     reference's horizontal offset is never copied;
   - the height follows the reference: `posY = 1 − 2·y_rel`;
   - top margin ≥ 10 %; keep the bottom ~22–26 % clear of platform UI;
   - never over the key action, the face or the product: when the centred text would cover one,
     move it up or down to the nearest clear band (top, middle or bottom), never sideways.
5. **Style: the house text style, always** (`capcut-assembly.md` §3): font System, size 10, and the
   user's chosen preset, locked in `config.json → capcut.text_style.learned` (white text, black
   outline), on every text of every video.
   - The reference decides only the wording, its case convention and its height, never the font,
     size, colour or preset.
   - Supplied brand fonts and colours are not used for overlay text unless the user asks for them
     in the run.
6. **Place it in CapCut** as text layers (`capcut-assembly.md` §3, step 2), one `capcut_add_text`
   per event. A context-bearing source overlay goes in as the original picture overlay instead
   (`capcut-assembly.md` §3, step 2b).
   - **Fallback only**, when the CapCut MCP is unavailable: burn the same events with
     `atp.py captions --spec <captions.json>`, and say so.
7. **QC:**
   - The **generated plate** must be text-free:
     `atp.py qc --mode analyze --allowed-text "<printed words of every client asset visible>"`.
     Anything else detected is pseudo-text or a copied artifact: fix the plate or regenerate. A garbled
     ghost of the source caption at its old position is one (CE-045): restore the clean-plate lines and strip
     the caption from the reference.
   - The **text** is checked on the CapCut preview (`capcut-assembly.md` §5): wording, timing,
     position, no emoji, and every overlay on exactly its visible frames.

