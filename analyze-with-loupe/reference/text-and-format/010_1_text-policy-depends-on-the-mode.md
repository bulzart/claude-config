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
  - **No sticker or emoji added, ever** (the user, 2026-11-03: "never use or apply stickers, ever, neither in the video generation nor in the edit",
    then "only no added ones if the video has emojis meanwhile someone is texting on phone thats natural, but not just place emojis or stickers as an adder"): in no mode is a sticker
    or an emoji added, to a generation as a decoration or in CapCut (as a graphic or in a text layer); one that belongs naturally to the
    scene (the emojis of a chat someone is typing on a phone) is scene content; a source's added sticker or emoji is removed (Edit Mode,
    with the text above) and a reference's is never re-made. One printed on the client's product is part of its label.
- Text must be intentional, readable, contextually correct and consistent across frames. No
  pseudo-text, malformed letters, words that change between frames, duplicate captions, unreadable
  typography or stray lettering.
- **Production method, always:**
  1. Generate a **clean plate**: the prompt asks for no on-screen text, and the model never
     renders overlay text.
  2. Place every overlay text as a **CapCut text layer** over the clean video
     (`capcut-assembly.md` §3).
  - Text never gets burned in with `awl.py captions`, except as the fallback when the CapCut MCP is
    unavailable.
  - The clean-plate lines are never the lines to cut when a prompt must fit the length limit (Higgsfield
    rejects a prompt over 5000 characters): cut descriptive wording instead. The lines are: do not inherit
    text, captions, usernames or watermarks from the video reference; no subtitles; no on-screen text
    anywhere. With them trimmed, a faint garbled ghost of the source caption stood on the wall at the
    caption's old position for the whole clip (CE-045; gone on the retry with the lines restored). A
    caption burned into the video reference is never removed by a tool in Analyze Mode: these lines carry
    it (`generation-system.md` §5c.2b).
  - Only text that physically belongs to the scene stays in the generation: the client product's
    own printed label, logo or badge (below).
  - **Create (command item 35) widens it: text and symbols that belong to the depicted world** are scene content too, of whatever
    kind fits the scene (a sign, a screen or interface in use, packaging, a poster, a book, a print on clothing, a menu, a map,
    graffiti: examples, not a list); only editorial text is kept out. The ones the story depends on are named in the plan, written
    exactly in the prompt and allowed in QC; the rest appear as naturally as that world has them. A Create take's clean-plate line
    forbids overlay text only: "No subtitles, captions, titles or other overlay text appear on screen; the only lettering is what
    belongs to the scene itself, the printed label on the <product> exactly as in @ImageN". Whatever appears meets the rule above
    (readable or naturally out of focus, the same across frames, no pseudo-text that draws the eye), the guardrails (no competitor or
    featured third-party brand, `generation-system.md` §9b) and item 6 (no sticker or emoji added).
- **The client asset's own label is not stray text.** A swapped or placed product keeps its real
  printed label, logo or badge exactly as in its reference image; that's what makes it
  recognisable.
  - The clean-plate wording carves it out, e.g. "No subtitles, captions or other text appear on
    screen; the only lettering is the printed label on the <product>, exactly as in @ImageN" (for
    a car: "the only lettering is the badge on the <car>").
    Never write a bare "no logos" that would blank the product.
  - Its words go into QC `--allowed-text` (§3, step 7).

