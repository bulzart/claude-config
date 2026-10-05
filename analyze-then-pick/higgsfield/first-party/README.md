# First-party Higgsfield documentation (local copies)

Retrieved read-only on 2026-09-30 from the connected Higgsfield MCP server (`https://mcp.higgsfield.ai/mcp`)
with `get_workflow_instructions`, `get_workflow_bundle_file` and `get_preset_instructions`. No job was
submitted and no credits were spent to obtain them.

| File | Source call | Why it matters to /analyze-then-pick |
|---|---|---|
| `ad-multiplier-recipe.md` | `get_workflow_instructions {workflow:"ad-multiplier"}` (v1.4) | Higgsfield's own contract for Seedance-2.5-powered edits of a supplied 4–30 s video (`ad_multiplier` / `seedance_2_5` `mode:"video_edit"`): media order, silent render + source-audio restore, retry rules, `use_unlim` rules |
| `ad-multiplier-prompt-writer.md` | `get_workflow_bundle_file {workflow:"ad-multiplier", path:"references/prompt-writer.md"}` | Exact edit-prompt contract: COMPACT / DETAILED templates, person-replacement exclusion sentence, temporal scoping, 3,900-character limit, validation list |
| `ad-multiplier-media-pipeline.md` | `get_workflow_bundle_file {workflow:"ad-multiplier", path:"references/media-pipeline.md"}` | ffprobe normalisation and the audio-restoration remux gates (run locally with FFmpeg by /analyze-then-pick) |
| `genjutsu.md` | `get_preset_instructions {preset:"/genjutsu"}` | Routing for `hf_mult_motion_control` (motion transfer) and `hf_mult_replace_object` (object/character replacement in a source video) |

## Important differences from /analyze-then-pick policy

1. **Terminology.** Higgsfield calls these server-side instruction bundles "workflows". They are
   documentation recipes. They are unrelated to Claude Code's Workflow tool, which
   `/analyze-then-pick` never creates, triggers or calls.
2. **Visible text.** The ad-multiplier contract *preserves* source captions and on-screen text by default.
   `/analyze-then-pick` overrides that in **Edit Mode**: no text from the source video survives unless the
   user explicitly asks to keep that specific text (captions, subtitles, usernames, watermarks, title
   cards, meme text, stickers, social overlays, UI elements, timestamps, overlay logos, random lettering).
   Do not paste the first-party "Preserve every caption…" block into our edit prompts; use its remove
   operation instead ("Remove only [target] from @Video1 and reconstruct the revealed area consistently
   with its immediate surroundings"), plus local clean-up or regeneration when the model cannot remove
   it cleanly. In **Analyze Mode** new, intentional text may be created (by default in deterministic
   post-production), but reference wording is never copied. Full policy: `../../reference/text-and-format.md`.
3. **Local processing.** The recipe runs ffprobe/ffmpeg inside Higgsfield's remote `sandbox_exec`.
   `/analyze-then-pick` runs the same probe and remux steps locally with FFmpeg (see
   `pipeline/preprocessing.md`), which is deterministic and keeps files on the user's machine.
4. **Replacement people.** The recipe can auto-generate adult replacement people with Soul 2.0 when
   references are missing. `/analyze-then-pick` uses the approved character references the user
   supplied; generating new people happens only when the user asks for it.
5. **Batching.** The recipe submits one position at a time; `/analyze-then-pick` also runs videos
   sequentially, one at a time.
