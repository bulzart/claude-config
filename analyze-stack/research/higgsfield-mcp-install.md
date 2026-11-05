# Higgsfield as a persistent MCP server in Claude Code (research agent R5, 2026-09-16)

Scope: how to make Higgsfield available to `/analyze-stack` and `/analyze-stack-workflow` without
depending on the claude.ai connector, on this machine (Windows 11, Claude Code **2.1.273**, verified
with `claude --version`). Nothing was installed; the main session runs the commands below.

## 1. What is connected today (verified)

`claude mcp list` on 2026-09-16:

```
claude.ai Higssfield: https://mcp.higgsfield.ai/mcp - √ Connected
```

`claude mcp get "claude.ai Higssfield"` → `Scope: claude.ai config`. So the connector already in
this session **is** Higgsfield's official hosted MCP server (`https://mcp.higgsfield.ai/mcp`),
mirrored from the owner's claude.ai account. Its tools are exposed to agents as
`mcp__claude_ai_Higssfield__<tool>` (note the connector name is misspelled "Higssfield" in the
owner's claude.ai settings; the server itself is the official one).

`~/.claude.json` currently contains no user-scope `mcpServers` entry for Higgsfield (only an empty
project-level `"mcpServers": {}`), i.e. there is no standalone registration yet.

## 2. Official documentation found

| Source | What it says | URL |
|---|---|---|
| Higgsfield MCP page (official) | Server URL `https://mcp.higgsfield.ai/mcp`; "Add the Higgsfield MCP server URL in your agent's settings and authenticate through your Higgsfield account. No API keys to manage or configure."; for Claude (web) a one-click connector link `https://claude.ai/customize/connectors?modal=add-custom-connector&connectorName=Higgsfield&connectorUrl=https%3A%2F%2Fmcp.higgsfield.ai%2Fmcp`; "If you are using Claude Code or Codex, it's better to use the CLI" (link to `higgsfield-ai/cli`) | https://higgsfield.ai/mcp |
| Higgsfield blog "Generate AI Videos from Claude with Higgsfield MCP" (May 8 2026, updated Aug 29 2026) | Settings → Connectors → Add custom connector → name Higgsfield → URL `https://mcp.higgsfield.ai` → Connect → sign in with the Higgsfield account; "works across Claude on web, desktop, mobile, and Claude Code" | https://higgsfield.ai/blog/Generate-AI-Videos-From-Claude-with-Higgsfield-MCP |
| Higgsfield CLI page + GitHub README | `npm i -g @higgsfield/cli`, `higgsfield auth login` (browser sign-in), companion skills `npx skills add higgsfield-ai/skills`; commands `higgsfield upload`, `higgsfield generate create <model> [--wait]`, `generate get/wait/list`, `voices list`, `workflow`; no API-key / token env var documented; no stdio MCP server in the CLI | https://higgsfield.ai/cli , https://github.com/higgsfield-ai/cli |
| Higgsfield changelog | Aug 25 2026: Ad Multiplier "Runs through the Higgsfield MCP connector"; Jul 7 2026: models "available through Supercomputer, MCP, and CLI" | https://higgsfield.ai/creator-hub/changelog |
| Higgsfield Cloud API docs (separate product) | Base `https://api.higgsfield.ai`, header `Authorization: Key ${HF_API_KEY_ID}:${HF_API_KEY_SECRET}`, keys from `https://cloud.higgsfield.ai/api-keys` (docs also mention console.higgsfield.ai); upload via `POST /files/generate-upload-url` → PUT to `upload_url` (1 h expiry) → pass `public_url`; Python/TypeScript SDKs (`higgsfield-client`); **no MCP server and no Seedance-2.5/Genjutsu endpoints listed** on the index | https://docs.higgsfield.ai/docs , https://docs.higgsfield.ai/docs/concepts/file-uploads |
| Claude Code MCP docs | `claude mcp add --transport http <name> <url>`; `--scope user` writes to `~/.claude.json` top-level `mcpServers`; OAuth for remote servers via `/mcp` inside Claude Code or `claude mcp login <name>`; tool names `mcp__<server>__<tool>` (characters outside `A-Za-z0-9_-` become `_`) | https://code.claude.com/docs/en/mcp |
| Community setup guides (agree with the above) | `claude mcp add --transport http --scope user higgsfield https://mcp.higgsfield.ai/mcp`; OAuth in the browser on first use | https://techsy.io/en/blog/higgsfield-mcp-claude-code , https://claudefa.st/blog/tools/mcp-extensions/higgsfield-mcp , https://www.higgsfieldmcp.com/guides/setup-claude |

Third-party wrappers exist (`QalaLabs/claude-higgsfield-mcp` — Python stdio, `HF_API_KEY`/`HF_SECRET`
from cloud.higgsfield.ai, wraps the Cloud API; `geopopos/higgsfield_ai_mcp`; `jfikrat/higgsfield-mcp`).
They wrap the **Cloud API**, not the hosted MCP: different tool names (`generate_image`,
`generate_video`, `create_character`, …), no `models_explore`/`media_upload`/`jobs_wait`, no
Seedance 2.5 `video_edit`, no Genjutsu. Do not use them for this stack.

## 3. Auth: OAuth, no API key

The hosted server authenticates with the Higgsfield **account** (browser OAuth). There is no API
key for the MCP connector ("no API key is documented for the MCP connector"). API keys exist only
for the separate Cloud API (`cloud.higgsfield.ai/api-keys`) and are not accepted by
`mcp.higgsfield.ai`. Credits are the account's normal credits (balance today: 1051.56, plan `ultra`).

## 4. Exact install (main session runs this; do not run from an agent)

Windows PowerShell 5.1, Claude Code 2.1.273 (`claude mcp add --help` confirms `-t/--transport
{stdio,sse,http}`, `-s/--scope {local,user,project}`, `-H/--header`, `--callback-port`,
`--client-id`, `--client-secret`):

```powershell
# 1. register the official hosted server for every project of this user
claude mcp add --transport http --scope user higgsfield https://mcp.higgsfield.ai/mcp

# 2. authenticate (either; `claude mcp --help` on 2.1.273 lists `login [options] <name>` and `logout <name>`)
claude mcp login higgsfield            # browser OAuth sign-in with the Higgsfield account, or:
claude                                  # start a session, type /mcp, pick "higgsfield", "Authenticate" -> browser sign-in

# 3. verify
claude mcp list                         # expect: higgsfield: https://mcp.higgsfield.ai/mcp - Connected
claude mcp get higgsfield               # expect: Scope: User config (~/.claude.json)
```

Notes:
- Transport is **http** (streamable HTTP). Not sse, not stdio, no `npx` package.
- `--scope user` stores the entry under top-level `mcpServers` in `%USERPROFILE%\.claude.json`
  (`C:\Users\Bulzart\.claude.json`). Use `--scope project` only if the stack should ship a
  `.mcp.json` (it should not — the run folders are not a git project).
- OAuth callback: Claude Code opens the default browser and listens on a local port; if the
  corporate firewall blocks the random port, re-add with `--callback-port 8080` (documented flag).
  Tokens are stored by Claude Code and refreshed automatically.
- If the connector and the standalone server are both present, every tool exists twice
  (`mcp__claude_ai_Higssfield__*` and `mcp__higgsfield__*`). Both are deferred tools (schemas load
  through ToolSearch), so the context cost is small; either copy can be used. To avoid double
  listings, the owner can disconnect the claude.ai connector after the standalone server is
  authenticated — optional.
- Remove: `claude mcp remove higgsfield --scope user`.

## 5. Same tool names? Yes

`claude mcp list` shows the claude.ai connector pointing at the very same URL the standalone
registration uses (`https://mcp.higgsfield.ai/mcp`), so the tool roster is identical: the live list
is supplied by the server on connect ("tools are discovered when your MCP client connects").
Verified names in this session (connector): `models_explore, generate_video, generate_video_batch,
generate_image(_batch), generate_audio(_batch), media_upload, media_upload_widget, media_import_url,
media_confirm, show_medias, job_status, jobs_wait, job_display, show_generations,
show_generation_by_ids, balance, transactions, apps_search, apps_describe, apps_invoke,
motion_control, get_workflow_instructions, get_workflow_bundle_file, sandbox_exec, upscale_video,
video_analysis_create/status/jobs, virality_predictor, …` (full list in the deferred-tools banner
of any session).

Only the prefix changes: `mcp__claude_ai_Higssfield__generate_video` (connector) vs
`mcp__higgsfield__generate_video` (standalone, name chosen at `claude mcp add`). The skill should
discover tools with ToolSearch and accept either prefix, e.g.
`ToolSearch "select:mcp__higgsfield__generate_video,mcp__claude_ai_Higssfield__generate_video"`
(a `select:` with an unknown name simply returns the ones that exist), or a keyword query
`"higgsfield generate_video"` — keyword search matches tool descriptions, and the connector's
misspelled server name ("Higssfield") is why the `select:` form is the safer of the two.

## 6. Fallbacks if the hosted MCP is unavailable

1. **Higgsfield CLI** (`npm i -g @higgsfield/cli`; `higgsfield auth login` once, interactive
   browser sign-in; afterwards `higgsfield upload <file>`, `higgsfield generate create seedance_2_5
   … --wait`, `higgsfield generate get <job_id>` work from scripts). Same account, same credits.
   Not installed; no token env var is documented, so the one-time login must be done by a human.
2. **Higgsfield Cloud API** (API key): a different product surface; Seedance 2.5 `video_edit` and
   Genjutsu are not listed in its docs index. Only for image/video models it exposes.
3. **fal.ai / Replicate / WaveSpeed / BytePlus ModelArk** for Seedance 2.5 directly (parameter
   sheets in `seedance\SEEDANCE-SPEC.md` §11) — needs their own API keys and a Python `requests`
   client; the `@Image N/@Video N` prompt syntax is the same.

## 7. Open points for the main session

- `claude mcp login <name>` is present on 2.1.273 (verified with `claude mcp --help`; also
  `logout`, `add-json`, `get`, `list`, `remove`). `add-from-claude-desktop` is Mac/WSL only.
- After install, run one read-only call (`balance` or `models_explore get seedance_2_5`) through the
  new prefix to confirm auth, then re-run `ToolSearch "select:mcp__higgsfield__generate_video"`.
