## 1. Connection and conventions

| Item | Value |
|---|---|
| MCP server | `higgsfield` (user scope, `~/.claude.json`), `https://mcp.higgsfield.ai/mcp`, OAuth through the Higgsfield account [VERIFIED] |
| Tool names | `mcp__higgsfield__<tool>`. All are **deferred**: load their schemas first with `ToolSearch "select:mcp__higgsfield__generate_video,…"`. If the account uses the claude.ai connector instead, the prefix differs (e.g. `mcp__claude_ai_Higgsfield__`); discover it with `ToolSearch "+higgsfield generate_video"` and never hard-code it |
| Auth problems | The tools are missing, or the only ones are `authenticate` / `complete_authentication` → ask the user to run `/mcp`, pick **higgsfield**, then **Authenticate** (or run `! claude mcp login higgsfield`). Then reload the tool schemas |
| Client type | Claude Code has **no Apps UI**. Never call widget-only tools: `media_upload_widget`, `show_marketing_studio_v2`, the `get_presets` widget flow. `generate_video` still returns job ids; the widget part is simply not shown [HF-TOOL] |
| "Workflows" | Higgsfield calls its server-side instruction bundles "workflows" (`get_workflow_instructions`). They are documentation recipes, not Claude Code Workflows. The knowledge /analyze-then-pick needs is already copied in `first-party/`. The command never calls the Claude Code Workflow tool |
| Remote sandbox | `sandbox_exec` is a remote Linux sandbox with ffmpeg. /analyze-then-pick does not use it: every media operation runs locally with FFmpeg (`scripts/atp.py`) |

