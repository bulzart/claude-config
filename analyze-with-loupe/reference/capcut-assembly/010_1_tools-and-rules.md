## 1. Tools and rules
- **CapCut MCP** (`capcut`, user scope). **Its tools are checked live, loading only what the project needs** (the user, 2026-11-03:
  "capcut may be updated and commands change so they should also try to figure out themself too", and "only call and what access to
  what needed"): load the usual set below with one `select`; a name it no longer finds was renamed or removed, so search for that
  operation (`ToolSearch` with `+capcut` and the operation's words, a few results). When the plan needs an operation the set has no
  tool for (reverse playback, an effect, something new), search the same way before calling it unavailable. The tools these sections
  name are suggestions for the usual operations, a newer or better one the search finds included (a tool added since the command's
  allowed list may ask the user once for permission); the catalog tools (`capcut_list_transitions`, `capcut_list_filters`,
  `capcut_list_masks`) are called only for the operation that needs them. capcut-cli the same way: `capcut <command> --help` for the
  command in hand, `capcut --help` only to look for one. Whatever their names become, the caption, transcript and sticker tools stay
  unused (command items 6, 35) and nothing is saved with force (below). The usual set:
  `ToolSearch "select:mcp__capcut__capcut_clone_draft,mcp__capcut__capcut_read_timeline,mcp__capcut__capcut_add_video,mcp__capcut__capcut_add_image,mcp__capcut__capcut_add_audio,mcp__capcut__capcut_add_text,mcp__capcut__capcut_split_segment,mcp__capcut__capcut_move_segment,mcp__capcut__capcut_trim_segment,mcp__capcut__capcut_add_track,mcp__capcut__capcut_set_props,mcp__capcut__capcut_set_track_mute,mcp__capcut__capcut_add_audio_fade,mcp__capcut__capcut_add_transition,mcp__capcut__capcut_list_transitions,mcp__capcut__capcut_add_keyframe,mcp__capcut__capcut_add_mask,mcp__capcut__capcut_list_masks,mcp__capcut__capcut_add_filter,mcp__capcut__capcut_list_filters,mcp__capcut__capcut_delete_segment,mcp__capcut__capcut_validate,mcp__capcut__capcut_save,mcp__capcut__capcut_discard,mcp__capcut__capcut_undo"`.
  - Drafts store: `config.json → capcut.drafts_dir`, the same as the server's `CAPCUT_DRAFTS_DIR`.
  - Template: `capcut.template_draft` = `_analyze-stack-template` (9:16, 1080×1920, 30 fps, with
    video, audio and text layers). Its text layer is only the structure `capcut_add_text` copies;
    the look is always the house text style (§3, step 2).
  - Never call `capcut_transcribe`, `capcut_add_captions` or `capcut_clear_captions`: overlay text
    is placed event by event.
- **capcut-cli** (`capcut` 0.25, on PATH) provides the repair lines and the proxy preview (§4).
- **CapCut must be closed to save.** `capcut_save` and the repair lines refuse while CapCut runs, or
  when the draft changed on disk.
  - Never pass `force:true` into the live store, and never `--force-write`.
  - If CapCut is running when an assembly is due:
    - keep generating;
    - assemble every pending project at the wrap-up;
    - tell the user once to close CapCut. That is a blocker notice, not a permission question.
- **Fallback when the capcut MCP is missing or broken:** deliver the clean assembly (§6), burn the
  planned text with `awl.py captions` (same strings, times and positions; it imitates the house
  style: CapCut's System font, white fill, black outline), and say so.

