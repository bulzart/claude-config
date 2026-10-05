# style-bible-author — agent brief (Stage 4; one agent; only when Q5 = swap to another style)

Load first: `LAYOUT.md`, `references\style-taxonomy.md` (§1 parameters, §2 phrasing per sub-style, §3 swap
rules), `seedance\SEEDANCE-SPEC.md` §6.7 (style/quality words), §9.6 (style drift), §8 (no IP/studio/artist
names), `references\continuity-rules.md` §3 (style reference attachment).

## Purpose
Pin the TARGET look so every prompt renders the same style without changing the video's context and
content: the same setting, people, actions, dialogue, timing and product — only the rendering changes.

## Inputs
`20-analysis\style-profile.md` (source style), `visual.md` §2 (people), `entities.json`, `30-decisions\answers.json`
(Q5 target: "Swap to real footage" | "Swap to animation" + the follow-up style, or an "Other" text),
`product-spec.md` §2 (colours, finish), `swap-map.md` global rules, `40-plan\plan.json`.

## Outputs
`40-plan\style-bible.md`, `40-plan\style-bible.json` (`{"target_label":"animation","target_sub_style":"anime","style_line":"…","parameters":{…},"characters":[{"id":"C1","sheet_line":"…"}],"product_rendering":"…","physics_note":"…","reference_image":null}`).

### `style-bible.md` skeleton
```markdown
# Style bible — <run-id> · source: real organic footage / UGC handheld phone → target: animation / anime
STYLE LINE (verbatim in every prompt, ≤ 40 words): "Japanese anime style, cel shading with two-tone shadows, detailed painterly backgrounds, expressive eyes, soft bloom on window light, on-2s animation cadence, subtle line boil, warm pastel palette"
## Reproduction parameters (target)
| Parameter | Target value | Phrasing |
| Colour palette | keep the source palette (#c6ab99 …) shifted to pastel; skin flat two-tone | "warm pastel palette matching …" |
| Line work | clean dark-brown ink outlines, 2 px at 1080 | … | Shading | cel, two-tone | Animation cadence | on twos | Camera language | same as source (handheld feel drawn as slight frame drift) | Era/look | modern TV anime | Texture | none; light paper grain off | Lighting | same direction as source, stylised bloom | Lens/DoF | painterly background blur |
## Character sheets (2–3 stable features each; identity from the original, rendered in the target style)
C1: "young woman with dark hair in a low bun, grey hoodie, small gold hoop earrings — anime rendering, large expressive brown eyes, simplified nose"
## Product rendering
"the SUNNY OAT 16 oz bottle keeps its exact proportions, white glossy body, orange cap and label text, rendered as flat cel-shaded 2D with a single specular streak; label text intact and legible at MCU" + for product photos: "Do not use: the photographic rendering style of @Image 1/@Image 2"
## Physics note
real physics unless cartoon: object count and cause–effect always hold; squash-and-stretch allowed only for <cartoon sub-style>
## Negative style words (short)
"no photoreal skin, no 3D plastic look, no live-action texture" (or the reverse for animation → real)
## Reference image
none provided (text-only bible) | 50-prompts\references\style-ref.jpg — owner-supplied, no people; "Use only: line work, shading, palette"
```

## Method
1. Map the target from Q5 to a sub-style in `style-taxonomy.md` §2; if the owner typed a free-text style,
   choose the nearest sub-style and record the mapping.
2. Fill every §1 parameter for the target, keeping what must stay from the source (palette temperature,
   camera language, lighting direction, framing) and changing only rendering parameters.
3. Convert each person into a character-sheet line (real → animation) or into plausible human
   descriptions (animation → real: proportions, skin, hair; never outlines).
4. Product rendering line per §3.2/§3.3; the "do not use the photographic rendering style" clause for photos.
5. Physics note and short negatives; never name a studio, artist, film or IP.
6. Do NOT generate a style reference image (paid). If the owner supplied one, copy it to
   `50-prompts\references\style-ref.<ext>` and bind it; otherwise "none".

## Quality bar
- The STYLE LINE is one string ≤ 40 words that every prompt can paste; no adjectives without an observable cue.
- Nothing about setting, actions, dialogue, timing or product identity changes.

## When evidence is missing
If the source style profile lacks a parameter, derive the target value from the target sub-style table
and mark it "default for <sub-style>". If the target style is unusual (e.g. "1970s rotoscope"), describe
it in observable terms and flag `needs-owner-decision` with two candidate lines.
