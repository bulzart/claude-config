## 3. The agent's contract
1. **Scope.** The agent owns only video NN:
   - its image calls' ledger entries (lane `NN`);
   - `40-briefs/video-NN*` and `60-outputs/video-NN/`;
   - its CapCut project (one per format).
   When its spawn message names a stretch of images (`images K1-K2`) or a format (`format <tag>`), it owns only that part of the video's work.
   It never reads or writes another video's files.
2. **Tools.** Everything is the toolkit `T`, run through PowerShell, and the run's files: images by `T image generate`, drawings by `T draw`,
   the timeline by `T slideshow plan`, the CapCut project by `T capcut-build` (command item 39). No CapCut MCP tool is loaded or called, and
   no ElevenLabs call is made: the narration and the bed are the main session's (`cs-sound`).
3. **Generation discipline** (command item 12, S3):
   - every image and thumbnail through `T image generate` (it keeps the ledger itself: `T ledger show --run RUN --video NN` lists the calls);
   - one image at a time (with FLUX 3 Klein, in the foreground);
   - never resend after an unknown outcome until it is resolved, and never an identical request that already made an image unless on a new
     draw (`--again`);
   - re-draws by the run's QC fixes: `auto` at most two diagnosed re-draws per image, then the best one, flagged; `ask` the proposal first
     (the agent prepares it and stops; the main session continues it with `approved` = draw the proposed images again, then go on;
     `declined` = no new draw, keep the images as they are, flagged, and go on to the edit with `qc` = "declined fix: <findings>"; `auto` =
     as approved, and no later fix asks); `off` none;
   - a request that failed twice → stop and report (`failed_twice`).
4. **Inputs.** The run's shared files: the anchors in `30-assets/characters/`, the narration and the bed, the plan files. Nothing is
   uploaded anywhere. With images by the user the images are `T image intake`'s copies in the video's images folder; the user's folders are
   read-only (command item 34).
5. **State.** The agent writes only through `T` and into its own files, and puts the result in `60-outputs/video-NN/result.json` (§4). It does
   not touch `state.json → videos[]`: the main session appends it as the agent reports (§5).
6. **CapCut** (S4, command item 39; `CS/reference/capcut-build.md`).
   - The timeline: `T slideshow plan` (its `undecided` empty, every drawing rendered and current).
   - The project: `T capcut-build --run RUN --video NN [--format <tag>]`: one composition, then the repair and a read-back whose `problems`
     list is empty or each entry fixed (in the plan or the stills, `T slideshow plan` again, a build under a new `--name`) or named in the
     brief with its reason. Never the CapCut MCP tools, never `capcut lint --fix`, never a save with force.
   - If CapCut is running the build stops (exit 3) and changes nothing: do everything else, set `"capcut_pending": true` and the blocker
     `capcut_running` in `result.json`, and stop.
7. **Deliverables.** The CapCut project is the final and the only edit: the user exports it from CapCut at the format's export size, 30 fps
   (the user, 2026-11-07: "no need to generate a ffmpeg video simulation version, just do it in capcut directly"), so no video file is
   rendered or put in `deliverables/`. The agent writes its README row to `60-outputs/video-NN/readme-row.md` (one row per format; the main
   session appends it to `<RUN>/deliverables/README.md`), the title `deliverables/video-NN-title.txt`, the thumbnail
   `deliverables/video-NN-thumbnail.png` and whatever the plan's `publish` block carries (static §12).
8. **The run's locks and content rules** (static §10, §11, §11b): the run's niche, style lock, text look and narrator; the video's own
   approach and language; nothing religious or superstitious, nothing indecent, gory or distressing, no subtitle-like text in an image, no
   sticker or emoji in a picture or a text layer (command item 6), real things look like themselves (static §5).
9. **Formats** (static §2b). One agent makes every format of its video (its stills, its project, its record entry), the same video at each
   format's size; a spawn message that names a format means that format only.
10. **No questions.** On any blocker, write `result.json` with `"status":"blocked"` and `"blocker"` set to one of `capcut_running` |
    `credits` | `failed_twice` | `qc_fix_permission` | `other`, plus one line of detail (`qc_fix_permission` also carries `fix_proposal`,
    §4). Then stop.
11. **Final message:** the content of `result.json`, as one JSON line, after the video's `RUN/60-outputs/video-NN/todo.md` (command item 38) is current and closed: each item `[x]`, or `[-]` with its reason,
    or named in the report as open. The agent writes that file when it starts and keeps it as it works (a file has one writer, so parallel agents never share one). An image agent of a split
    video ends with its stretch's one JSON line instead (`cs-images`).
12. **Record.** Every regenerate reason and every flagged delivery (RESIDUAL FAILURE: a still kept as the best after its re-draws, a build
    `problems` entry that stays) is written at once in the video's brief as an attempt block (the prompt that made the failed image or the
    plan that gave the failed build, the verdict with the words that show it and the file paths, what the redraw or the change does) and in
    `result.json`; nothing else is written to the library. The main session checks the briefs against the `result.json` files (§5).
13. **Checks that are never skipped** (with QC fixes `off` the checks still run and the re-draws do not). The agent views the images itself;
    an assumption, "the contract forbids" and an unviewed image are not evidence. Each check's evidence path (image file, `T image text`
    answer, preview sheet, the build's `read_back`) goes in `result.json` → `checks`; a check you could not run is written "not checked:
    <why>", never left out.
    1. **Every still** viewed (Read the file) and checked as static §8 says: the style lock, the people against their anchors, the clean
       picture, no made-up subtitle; after the stills `T image text --run RUN --video NN` read (a long line across the bottom third that no
       sign, page or screen carries is a failure); for a video in another language the bottom third of every still viewed.
    2. **The thumbnail** viewed at full size and at its small feed size (static §8, §12).
    3. **Logos, labels and drawings:** a placed logo (`T image brand`) viewed on its picture; a map's labels read off the picture beside their
       pins; each drawing's three previews viewed and the facts of `T draw render` read (static §5 "Drawings").
    4. **The content rules** (static §11, §11b): nothing religious or superstitious, nothing indecent, gory or distressing in any still, the
       thumbnail, the title, a caption or a label.
    5. **The edit** (static §8 "The edit"): the build's `problems` empty or each entry settled; `read_back` against the timeline (every image
       at its start and span, the narration and the bed on their tracks, every move keyed, every join, each effect and drawing on its track,
       the captions' count and look, `caption_font.font_missing_glyphs` empty); no emoji or sticker in any picture or text layer.
    6. **The cost:** the sum of the answers' `cost_usd_estimate` (0 with FLUX 3 Klein), written in `result.json` and the brief.
14. **Docs, before the final message:** the brief carries its S3 and S4 blocks (every regenerate reason and flagged delivery included);
    `result.json` complete; `readme-row.md` and the deliverables files written.
