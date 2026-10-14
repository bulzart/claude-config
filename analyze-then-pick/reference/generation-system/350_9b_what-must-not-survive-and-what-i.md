## 9b. What must not survive, and what is fine (all modes)

UGC is full of everyday branded stuff. A Kirby poster, a Hello Kitty ornament or an AYBL hoodie in
a reference's room is normal, and so is a sign across the street. By default only two things have
to go: what makes the video **someone else's** or a **platform repost** (the copyright and
ownership floor, rows 1–6), and what the generation service **refuses to render** (row 7, a
block, not a rule). The pipeline has **no content rules of its own**: alcohol, weapons, gore,
profanity, meme faces and everything else a brand might dislike stay exactly as the reference
shows them unless the client's guardrails name them (`brand-guardrails.md`), and nothing is ever
blurred, pixelated, softened or removed on the pipeline's initiative.

| Must not survive: fix it | Fine: leave it, never flag it |
|---|---|
| The **original person or character** being replaced, in any shot, reflection or mirror | **Background decor:** posters, plushies, figurines, ornaments, wall art, toys, even of famous characters (Kirby, Hello Kitty) |
| The **original product** being swapped, and any **competitor product of the client's category** anywhere in frame (another energy drink for a drink client, another gum brand for a gum client, a rival car that is featured or has a readable badge for a car client; anonymous passing traffic is fine) | **Clothing and footwear** logos, stripes and prints on anyone (AYBL, three stripes, a swoosh) |
| **Overlay text:** captions, subtitles, hook text, stickers, usernames and handles, timestamps. The planned text comes back as CapCut layers | **Environmental text:** shop and street signs ("PHARMACY", "SALON"), generic labels, everyday packaging in the background |
| **Platform logos and watermarks:** TikTok, Instagram / Reels, YouTube Shorts, CapCut, Snapchat, creator watermarks | **Brands seen in passing:** furniture, appliances, cars, phones, laptops, unless they compete with the client's product (left) |
| **Featured third-party branding:** a readable brand name or logo that is held, used, centred or in close-up (a branded coffee cup in hand, a sneaker box shown to camera) | Anything the reference shows that is not featured, not an overlay, not a watermark, not refused by the service and not named by a guardrail |
| **A copyrighted character as the subject** (a costume, a toy presented to camera) and studio / film / character names in prompts. Higgsfield blocks those as "ip_detected" | **Meme inserts and the faces in them,** cut from the reference as they are (`generation-system.md` §3c): never blurred, never cropped, never replaced unless a guardrail names the person |
| **Service blocks (a block, not a rule):** what the generation service refuses or moderates (`Request Moderated`, `ip_detected`, a model's own real-face refusal where its guide says so): sexual content and nudity, graphic self-harm, hate symbols. The job fails, so the plan avoids them and a reference built on them is dismissed; a brand rule cannot enable them | **Brand-dependent content, nothing by default:** weapons, alcohol, tobacco and vapes, gambling, drugs, gore and fake blood, dangerous stunts, profanity, political or religious content, celebrity cameos in memes, and anything else a brand may dislike. It stays as the reference shows it unless a guardrail in the client's documents names it (`brand-guardrails.md` §2); then it is a hit, handled by the audit |

**The client's guardrails are the only content rules** (`brand-guardrails.md`): the content bans,
the competitor list they name or imply, the people whose likeness is excluded, the count limits,
the context rules, the banned wording and the required disclaimers. A competitor's mark is
**de-branded**, never blurred: the name, the logo and the identifying trade dress are removed and
the object stays as a plain one of the same shape, size, spot and light. Without a guardrail
document, only the floor (rows 1–6) and the service blocks apply, and the right column is left
alone in full.

**Fixes are autonomous and cost-aware:**
- **Small static leftovers** (a watermark, a corner logo, a sticker remnant): fix them locally and
  for free with `atp.py clean --delogo` on the clean video before CapCut. An Edit Mode source is cleaned
  before upload (`text-and-format.md` §2.2); a Recreate source never is: the clean-plate lines and the
  character-swap script carry its captions.
- **Everything else on the left:** one corrected regeneration that names the item explicitly
  ("Replace only…", "Remove only…").
- **Still failing:** report it in the wrap-up. In Analyze Mode, never ask about it mid-run.
- **The right column never costs a retry.**

