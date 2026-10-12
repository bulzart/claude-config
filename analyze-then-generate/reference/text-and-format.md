# Visible text and output format

Load this during planning (for the text and format rows of the plan) and again during post-processing.

## 1. Text policy depends on the mode

### Edit Mode: no source text survives
Remove every text element that comes from the source video unless the user explicitly asks to keep
**that specific** text:
- captions and subtitles, title cards, meme text, stickers;
- social-media overlays, usernames and handles, watermarks, timestamps;
- interface elements, overlay logos, random lettering;
- any other baked-in overlay text.

Environmental text that belongs to the scene stays: shop and street signs, posters, clothing
prints, everyday packaging in the background. It is not source text, unless it is featured
third-party branding (`generation-system.md` §9b).

Reconstruct the underlying scene instead of leaving holes or smears. Text that is part of the
**client's approved asset** (their real product label, their real interface) is not source text; keep
it for fidelity.

### Analyze Mode: generate clean, then place the text in CapCut
Text may be created when it improves the concept or matches the analyzed structure: opening hooks,
"POV: …" and "when …" lines, captions, labels, meme text, annotations and callouts.
- **Wording.**
  - Keep the reference text's **role, format, height and timing**. Its look is always the house
    text style (§3, step 5), never the reference's, and it is always **horizontally centred**
    (§3, step 4).
  - **Recreate** (the same video, edited): the reference's overlay text is removed in the edit and
    re-placed in CapCut **word for word**, except a line that breaks a client guardrail (a banned
    claim or word, an excluded person's name): that line is rewritten minimally (remove only the banned
    element, a number, a statistic or a name, and say the same thing in the same grammar: the reference's
    subject and meaning stay, never an unrelated line; CE-022: a finance caption was swapped for an unrelated joke to clear a number) in the same role, position and timing, and a required disclaimer is added as a layer in the house style
    (`brand-guardrails.md` §2). A caption that *is* the banned point makes the reference a
    dismiss, not a rewrite.
  - **Create** (new videos): a generic meme caption line that carries the joke and names no brand,
    person, handle or source-specific detail may keep its wording (e.g. "first day as an
    assassin"). Anything source-specific is rewritten for the client and concept.
  - In both, **never copy** usernames, handles, watermarks or the reference's brand names.
  - **A specific keyword.** When a reference's only text is a short tag or keyword that defines its niche
    (a channel keyword), ask whether it is the hook before dropping it as a handle; when the user keeps
    it, it is placed word for word as a CapCut text layer at the same height (CE-027: the only text, "Financeaholic", was dropped as a handle and replaced by an invented caption), and the user's
    instruction outranks "never copy handles".
  - **Context-bearing overlays** (a notification, message, receipt or banner that sets up the joke): the
    original element is reused. It is cut from the reference's own frames with its look, position, size and
    timing, placed over the clean video as a picture overlay on exactly the frames where it is visible, and
    faded with the picture under it (CE-017: the banner was dropped with its brand and the joke lost its setup; CE-023: a re-typed text layer is not the original; CE-026: the crop's backdrop stayed on screen after the banner left). Removing a third-party brand never removes
    such an overlay's information role, and content the user names as part of the context outranks the
    brand removal. Text layers are for captions only.
  - **No emoji** in any text layer (the user's rule, strict): an emoji in a source caption is dropped and
    the rest of the wording kept.
- Text must be intentional, readable, contextually correct and consistent across frames. No
  pseudo-text, malformed letters, words that change between frames, duplicate captions, unreadable
  typography or stray lettering.
- **Production method, always:**
  1. Generate a **clean plate**: the prompt asks for no on-screen text, and the model never
     renders overlay text.
  2. Place every overlay text as a **CapCut text layer** over the clean video
     (`capcut-assembly.md` §3).
  - Text never gets burned in with `atg.py captions`, except as the fallback when the CapCut MCP is
    unavailable.
  - Only text that physically belongs to the scene stays in the generation: the client product's
    own printed label, logo or badge (below).
- **The client asset's own label is not stray text.** A swapped or placed product keeps its real
  printed label, logo or badge exactly as in its reference image; that's what makes it
  recognisable.
  - The clean-plate wording carves it out, e.g. "No subtitles, captions or other text appear on
    screen; the only lettering is the printed label on the <product>, exactly as in @ImageN" (for
    a car: "the only lettering is the badge on the <car>").
    Never write a bare "no logos" that would blank the product.
  - Its words go into QC `--allowed-text` (§3, step 7).

## 2. Edit Mode: removing source text

### 2.1 Inventory (before planning the edit)
Sources: `10-media/<id>/ocr.json` (spans with the numbers that describe each text: `first_t`, `last_t`, `hits`
(frames it was seen in), `share_of_frames_scanned`, `y_rel` and `band`, `band_distinct_texts` and `band_frames`
(how many different texts, in how many frames, sat in that row of the frame), `score_mean`, and the spelling
facts `has_at_handle`, `has_hashtag`, `has_url_pattern`; plus `bands[]`, the rows of the frame with their counts),
`timeline.md` (the text column per second), and the storyboard sheets (read every overlay by eye; OCR
misses stylised text and stickers). The tool labels nothing: whether a text is a caption, a fixed overlay, a
handle, a watermark, a label or noise is your reading of these numbers and the picture. Rules of thumb: a row of
the frame that held many different texts over several frames reads like a caption track; a text seen in most of
the scanned frames reads like a fixed overlay; the spelling facts help to tell a handle or a URL from a caption.

For each element record:

| text | kind (overlay / in-scene) | position (y_rel, x) | time span | size vs. frame | over important content? | keep (user said so)? |
|---|---|---|---|---|---|---|

### 2.2 Choose the removal method (least destructive that fully removes it)

| situation | method |
|---|---|
| The edit model supports prompt-level removal (see the model guide §3.11d), e.g. `seedance_2_5` / `ad_multiplier` `video_edit`, `kling_video_edit`, `gemini_omni_flash_1_1` edit, `flux_3_video_edit` | One explicit **remove operation per text element** in the same edit request: "Remove only <the caption text band across the middle of the frame> from @Video1 and reconstruct the revealed area consistently with its immediate surroundings." Never include the first-party "Preserve every caption…" block |
| Small static overlay (handle, watermark, corner logo) on a simple background | Local `atg.py clean --delogo "x,y,w,h[@t0-t1]"` before upload. Inspect the result: `delogo` smears textured backgrounds, so if it does, use the model instead |
| The text sits in a removable band (meme bars, letterboxed title area) | `atg.py clean --crop "x,y,w,h"` keeping the picture, then `conform` / Higgsfield `reframe` back to 9:16 |
| Large or animated captions over the subject or the key action | **Clean-frame reconstruction:** regenerate the scene with a reference-to-video model, using the source as a video reference for motion, camera and timing only, with the edit's substitutions applied. Or run the edit model's removal first, then QC |
| A start-frame model is chosen | Pick a source moment without text, or clean the frame (image edit), and use it as the 9:16 start frame |
| The user asked to keep specific text | Preserve exactly that element; name it in the prompt as preserved, and remove everything else |

### 2.3 Verify
Run `atg.py qc --mode edit` and view the storyboard. `qc` lists the text its OCR saw (`visible_text`, with
times, frames seen and row) beside any text you planned to keep (`--allowed-text`) and says nothing about pass or
fail: you read the list against the storyboard. In Edit Mode no source text may remain unless the user kept it
explicitly, so any residual source text, ghosting or smear means the check fails (your verdict): pick the next
method in §2.2.

## 3. Analyze Mode: planning text and placing it in CapCut

1. **Read the reference's text** from the analysis card ("Overlay text"):
   - its wording and role (hook, "POV:" line, running caption, label, payoff line, context-bearing
     overlay: §1);
   - position: `y_rel` / `x_rel` of its centre, from `ocr.json` and the sheets;
   - timing: in and out, in seconds;
   - style: colour, size relative to the frame, outline or box, case, line breaks.
   No text role in the reference or its family → no text.
2. **Write the text** per §1 "Wording". Keep it short, in the tone and density of the family it follows (Create: of the mechanisms it borrows):
   - hooks ≤ 8 words;
   - running captions 1–4 words per event, and ≤ 2 lines;
   - labels ≤ 5 words;
   - a meme caption keeps its natural length.
3. **Time it on the final timeline**, after inserts are placed (`generation-system.md` §3c):
   - ≥ 0.4 s plus ~0.25 s per word on screen;
   - never overlapping itself;
   - captions follow the generated speech when there is speech: take the times from the clean
     video's transcript (`atg.py prep-video`);
   - the hook appears in the first 0–0.3 s when the hook it follows (the family's, or the borrowed mechanism's) is textual;
   - a caption that spans the whole reference spans the whole video;
   - text that plays on the product (a logo pun, a reveal) is timed to the moment the product
     really shows it in the clean video, measured at 30 fps, never to the plan
     (`generation-system.md` §5b).
4. **Place it at the reference's height, always horizontally centred**, inside the 9:16 safe area
   (the user, 2026-10-09: "make the text be in the center, whether up, down or in the middle";
   caught error CE-010):
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
     `atg.py captions --spec <captions.json>`, and say so.
7. **QC:**
   - The **generated plate** must be text-free:
     `atg.py qc --mode analyze --allowed-text "<printed words of every client asset visible>"`.
     `qc` returns `planned_text` (what you allowed) beside `visible_text` (what its OCR saw); you compare the two
     and read the storyboard. Anything visible that was not planned is pseudo-text or a copied artifact: fix the
     plate or regenerate.
   - The **text** is checked on the CapCut preview (`capcut-assembly.md` §5): wording, timing,
     position, no emoji, and every overlay on exactly its visible frames.

## 4. Fixed output format: 9:16 at 720p (720×1280)

Every Higgsfield generation in both modes is vertical 9:16 at 720p. It is never asked, and never
stretched.

### 4.1 Decision tree
1. **Native.** The model has `aspect_ratio` 9:16 and a 720p setting → send both through the model's
   own parameter names (`models/index.json → output_9x16_720p.params`) → confirm 720×1280 with `qc`.
2. **Near-native.** The output is 9:16 at a different size (768p, 1080p, 2K, or 704×1280) →
   `atg.py conform` (scale-to-cover plus a crop of a few pixels, lanczos).
3. **The aspect follows an input** (a start frame, or a source video for edits and motion transfer) →
   make the input 9:16 first:
   - build or crop the start frame at 720×1280;
   - reframe the source (below).
4. **A source video is not 9:16 in Edit Mode** → before the edit:
   - `atg.py conform --focus-x/--focus-y` when a crop keeps every important subject, prop and action
     (`--dry-run` reports `lost_fraction`, the share of the picture the crop removes, and writes nothing; the
     tool never refuses a crop, so you decide: a loss above about 12 % is a reason to use Higgsfield `reframe` or
     to regenerate from a 9:16 start frame; check the storyboard first);
   - otherwise Higgsfield `reframe` (`aspect_ratio:"9:16"`, `resolution:"720p"`, AI-expanded edges;
     preflight with `get_cost`);
   - otherwise regenerate with the source as a video reference in a 9:16 generation.
5. **The output is not 9:16 when it should have been** → treat it as a failure. Conform only when the
   crop is subject-safe; otherwise regenerate with corrected parameters.
6. **Padding** (`conform --mode pad`, blurred fill) only when the user asks for it.

### 4.2 Post-processing order
`hf-get` → `restore-audio` → `conform` → `trim` (dead head/tail) → `concat` (multi-clip videos) →
`qc` of the clean video.
- **Analyze Mode** then continues in the video's CapCut project (`capcut-assembly.md`): inserts,
  text layers, then the preview QC.
- Edit Mode `restore-audio` always uses the original audio from `<given path>/files_audio/`, created
  at intake by `split-audio`, with `--audio-offset`, and `--start` when a single segment was edited.
- Multi-segment edits: `concat` the edited pictures first, then restore the full original audio
  once.
- Only silent copies (`videos_without_audio`) are uploaded to Higgsfield.
- After the user approves an Edit Mode video, `finalize` copies it to `<given path>/final/<original
  name>.mp4`.
Text is rendered last, at the final resolution, so it is never scaled or cropped afterwards.
