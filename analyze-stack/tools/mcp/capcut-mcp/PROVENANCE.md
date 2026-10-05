# capcut-mcp (Gusmares/MCP-CapCut fork of JmsLdrn/capcut-mcp)

- Source: https://github.com/Gusmares/MCP-CapCut
- Commit: bbe4c21cde0eaa6de3a0537b2bb202634dfc048e (2026-09-14T23:10:37-03:00)
- Upstream: https://github.com/JmsLdrn/capcut-mcp (v0.1.0, 2026-08-07)
- License: MIT (see LICENSE)
- Installed: 2026-09-19 into the analyze-stack by the owner's request ("video editing should be in CapCut, accessed from an MCP")
- Reviewed before install: src/server.js + src/core.js. Only outbound network call = Deepgram in capcut_transcribe when DEEPGRAM_API_KEY is set (never used by analyze-stack; speech captions are forbidden in edits). Local process calls: tasklist (CapCut running?), ffprobe/ffmpeg. Writes only under CAPCUT_DRAFTS_DIR (path-traversal guarded) and .transcript-cache/.
- Known gaps on CapCut 9.4 (covered by capcut-cli after every capcut_save): media added through the MCP is NOT registered in draft_meta_info.json (local_material_id left empty) and only the root draft_content.json is written (no Timelines/ mirror). Run: capcut register <dir> --apply --materials ; capcut sync-timelines <dir> --nested --apply ; capcut lint <dir>.
- Registered in Claude Code (user scope) as server name "capcut" with env CAPCUT_DRAFTS_DIR and CAPCUT_TEMPLATE_DRAFT (see LAYOUT.md).
- Local patch 2026-09-19 (src/core.js validate()): audio-track segments are excluded from the shared-render_index clash check — CapCut writes render_index 0 on main-track video AND on audio segments, so the upstream check flagged every draft with an SFX under a clip as "ambiguous layer order" and blocked capcut_save without force. Same-track overlap and all other checks unchanged. Smoke test (smoke.mjs) passes with ok:true after the patch.
