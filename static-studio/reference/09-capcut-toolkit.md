# 09 — Writing the CapCut project on this PC (toolkit)

This manual is about **tools**, not about what the film should contain: what goes on the timeline stays decided by manuals 04 and 05. `STUDIO/scripts/capcut_tools.py` holds the CapCut-writing code this PC's CapCut 9.7 needs, so that a project opens with its clips linked, plays the moves and joins it was given, and can be exported. It works next to the CapCut MCP and capcut-cli, which still add the images, the narration, the music and the texts.

Call it as `python "$HOME/.claude/static-studio/scripts/capcut_tools.py" <command> ...` (`-h` on a command lists its options). Every call prints one JSON object on its last line. Exit 0 = done, 1 = a step failed (read `action`), 2 = refused (nothing was changed), 3 = CapCut is running.

## What this PC's CapCut needs (why these commands exist)

- **CapCut must be closed** for any write. If it is open when the project is due, finish everything else, tell the user once to close it, and do not close it yourself. The commands refuse and change nothing.
- **Media links.** CapCut 9.7 opens a local clip through the `local_material_id` of its entry in the project's media list; without it every clip shows as missing. `capcut-repair` writes the entries and the links.
- **Moves.** CapCut 9.7 ignores the MCP's scale keyframes (a project keyed that way played every still static). `capcut-motion` writes the scale and position keyframes it does play, so use it for moves instead of `capcut_add_keyframe`.
- **Transitions and text entrances** come only from the measured catalogue `STUDIO/data/capcut-catalogue.md`, which lists what this PC's CapCut really draws. This PC has no CapCut Pro and a project that holds a Pro option will not export, so a Pro option is refused too (`STUDIO/config.json` → `capcut.pro` is false). Use `capcut-transitions` for joins instead of `capcut_add_transition`.
- **Fonts.** A project shows a font only while the file stays where the project points. `capcut-font --list` gives each file's `kept_by`: CapCut's own folders are replaced when it updates and its cache may be cleared.
- Never `capcut lint --fix` (it copies every media file into the draft, shortens texts over 7 s, trims captions and closes gaps), and never `capcut_save` with `force`.

## The order

1. `capcut-name --video NN` answers with a free project `name` (`DD_Mon_YYYY_vNN`, `-2`, `-3` when the folder exists) and its full `path`. That path is the `--draft` of every command below.
2. MCP `capcut_clone_draft {base: "_analyze-stack-template", newName: "<name>", empty: true}`: the empty template. Never edit or delete the template.
3. `capcut-prep --draft "<path>" --canvas 1920x1080` **immediately**, before any other call on the draft. It sets the template's identity files aside so the project can be registered, and sets the canvas (even edges).
4. MCP: `capcut_read_timeline` (the track indexes), `capcut_add_image` (`atSec`, `durSec`), `capcut_add_audio` (the narration at 0; a music bed needs `capcut_add_track` type audio first and its `trackIndex`, else it lands on the narration's track and `capcut_validate` refuses the overlap), `capcut_add_text` as needed, `capcut_validate`, `capcut_save`. **This is the last MCP save**: the commands below write the project's files, and a later MCP save writes its own copy over them (then run them again).
5. Moves and joins: write the images file (below), then `capcut-motion --draft "<path>" --timeline FILE` and `capcut-transitions --draft "<path>" --timeline FILE`.
6. Texts: `capcut-font --list [--family NAME]`, then `capcut-font --draft "<path>" --font-file FILE [--track NAME]`. It sets the font on every text (or one track's) and writes the outline and box where CapCut 9.x draws them; read `font_missing_glyphs` (characters the font lacks; when it is not empty pick another font). Then `capcut-text-anim --draft "<path>" [--track NAME] --intro SLUG [--intro-duration S] [--outro SLUG]`: CapCut's own entrance on every text of the track, slugs from `capcut enums --text-intros`, capped at each text's length.
7. `capcut-repair --draft "<path>"`: register (identity, media list, store index), the media links, `sync-timelines --nested` and `lint`, under the machine-wide store lock (it waits up to 15 minutes for another toolkit that holds it). Every text stays as it is. `ok: false` with an `action` means CapCut is running or lint found errors: fix through the MCP, `capcut_save`, then repeat steps 5–7. `--preview OUT.mp4` also renders capcut-cli's low-resolution proxy of the order, timing and text: a proxy, **never an export**.
8. Read the project back (`capcut_read_timeline` and the lint result) and write `70-edit/video-NN/timeline.json` from it, as manual 05 says.

## The images file (for `capcut-motion` and `capcut-transitions`)

Write it from the shot plan, for example as `RUN/70-edit/video-NN/capcut-images.json`:

```json
{"fps": 30, "images": [
  {"image": 1, "start": 0.0,  "motion": "zoom-in",   "amount": 0.06},
  {"image": 2, "start": 6.0,  "motion": "pan-right", "amount": 0.05, "transition": "mix", "trans_s": 0.5},
  {"image": 3, "start": 12.0, "scale": [1.0, 1.08], "x": [0.0, 0.03], "y": [0.0, 0.0]}
]}
```

- `image` is the clip's number in order. `start` is its start on the main track in seconds: a clip is found by its start (within half a frame), so these must be the starts the clips really have. `images_without_a_clip` in the answer must be empty.
- `motion` is `none`, `zoom-in`, `zoom-out`, `pan-left`, `pan-right`, `pan-up` or `pan-down`. `amount` is the zoom's change (0.06 = 6 %), or for a pan the scale it travels at. There is no default amount: without one nothing moves. `scale`, `x` and `y` as `[at the start, at the end]` pairs replace the named motion: scale 1 = the picture covers the canvas, `x` and `y` = the picture's centre in half-canvas units (x to the right, y up). Keep a pan or a zoom inside the margin its scale gives, or the picture's edge shows.
- `transition` is a slug from `capcut enums --transitions` and plays into this image, on the clip before it, for `trans_s` seconds (default 0.5). `cut` or none = no transition. A refused slug is listed in `failed` with its reason.
- Both commands can run again: `capcut-motion` replaces its own keyframes, `capcut-transitions` keeps a clip that already has one.

## Not covered

Overlay clips, effects and caption building are not part of this toolkit: use the MCP and capcut-cli as manual 05 says, then run `capcut-repair`. No tool exports a CapCut project; the export is the user's.
