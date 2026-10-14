## 4. After every save (capcut-cli)
```
T capcut-repair --draft "<store>/<name>" --preview "<run>/60-outputs/video-NN/capcut-preview.mp4"
```
It first applies the **house text style** to every text layer (`T capcut-text-style`, root and
nested timeline copies), then runs these capcut-cli steps, the first three under one machine-wide
lock:
```
capcut register "<store>/<name>" --apply --materials
capcut sync-timelines "<store>/<name>" --nested --apply
capcut lint "<store>/<name>"
capcut render "<store>/<name>" --out "<preview>" --burn-captions
```
- The lock exists because `register` rewrites CapCut's **shared** project index, and production
  agents assemble projects in parallel.
- Exit 1 with an `action` line means CapCut is running, or lint found errors.
- `register` recreates the identity file from the new timeline and lists the media. Without the
  media list, CapCut shows the clips as "file inaccessible".
- `sync-timelines` writes the nested timeline copy that CapCut 9.x reads first.
- `lint` must report 0 errors.
- The preview is a low-resolution proxy, not CapCut's own render. It shows the order, the timing,
  the inserts and the text.
- **The exact preset: the user's choice, learned and locked.** CapCut keeps its preset tiles on its
  servers, not in a readable file, so the preset is copied from a text the user styled in CapCut.
  - **Current house preset:** chosen by the user in `03_Oct_2026_v09` and learned on 2026-10-03
    (white text, black outline 0.06). It is stored in `config.json → capcut.text_style.learned`
    with `"locked": true`, and every project of every run gets it. The font path is resolved to the
    newest installed CapCut version at apply time, so CapCut updates do not break it.
  - **Never replace it** unless the user explicitly asks for a different preset. `--learn` refuses
    while the preset is locked; only then use:
    1. in CapCut, add a text to any project, pick the new preset, and close CapCut;
    2. `T capcut-text-style --learn --replace --draft "<store>/<that project>"` (`--text N` when the
       project holds several texts).
  - A `warning` in the learn output means the preset also uses an extra material that is not copied
    yet.
  - Without a learned preset (only if config is lost), the fallback look is white fill, black
    outline (width 0.06), no shadow, no background.

