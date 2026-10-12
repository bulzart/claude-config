---
name: atg-photo-links-only
description: "Product photo references in /analyze-then-generate Viral-Browser are image URL links only; never download or store the images (user, 2026-10-12)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: ff6a4b04-16a6-4927-889e-830c4c6779e4
  modified: 2026-10-12T07:51:27.491Z
---

When the user asks for photo references of a product (or any web material to point at) in the Viral-Browser, bring the **image URL links**, not downloaded copies. The user, on seeing the first version that downloaded, resized and contact-sheeted the images: "no don't download them just bring the image url links".

**Why:** they want pointers they can open and later hand to Higgsfield (`media_import_url` takes an HTTPS image URL and returns a media id), not files. The first version built much more machinery than was asked (download, EXIF, resize, hash dedupe, contact sheet, viewed/usable flow).

**How to apply:**
- The pack lives in `deliverables/reference-C##-<name>/`: `spec.md`/`spec.json`, `photos.md` (links table, coverage, suggested reference set), `photos.html` (a gallery that makes the user's browser load the linked images; nothing stored), `photo-links.json`, `NOTES.md`. No image file is ever written.
- `T photo add` only probes the address with HEAD (never GET, no fallback when HEAD is refused); `T photo find` reads product pages (not images) to list the addresses they declare. Angles are "as the source labels it": nobody looks at the images, so the visual flags (background, watermark, third-party brand marks, same variant) stay unset unless someone opened the image (`--looked-at yes`).
- More generally: when the user asks for references, deliver the lightest thing that answers (links with provenance and status) and offer the heavier one (copies) as a separate choice. Related: [[atg-pipeline]].
