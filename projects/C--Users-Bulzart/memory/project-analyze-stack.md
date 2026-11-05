---
name: project-analyze-stack
description: "The analyze-stack build — the single /analyze-stack slash command (Agent-tool engine) for viral-video → Seedance 2.5 prompt sets, optional Higgsfield generation, post-generation editing in CapCut; stack home, installed pieces and key decisions"
metadata: 
  node_type: memory
  type: project
  originSessionId: efb68ef5-1bca-4047-9efb-e863b99cf91c
  modified: 2026-09-18T23:31:01.942Z
---

Started 2026-09-16. Stack home: `C:\Users\Bulzart\.claude\analyze-stack\` (LAYOUT.md is the
architecture contract; `references\questions.md` is the verbatim question script; `seedance\`
holds the Seedance spec + edit notes AND, since 2026-09-19, `seedance\director\` = the owner-supplied
"Seedance 2.5 Director" bundle rev 2.1.0 (from `C:\Users\Bulzart\Documents\prompts\seedance-2-5-agent-guide.zip`)
— all READ-ONLY at run time, changed only on explicit request; SPEC §14 states the precedence: SPEC
numbers win, the director's method governs prompt planning/writing/auditing, owner rules win over both;
`product-library\` persists product spec sheets; `runs\<run-id>\` per analysis run).
The skill lives in `C:\Users\Bulzart\.claude\skills\analyze-stack\SKILL.md` and spawns agents
with the Agent tool. It is the ONLY command; it never runs as a Workflow (owner 2026-09-17, reaffirmed
2026-09-19 — all workflow-twin wording removed from the live files that day).

**Why:** one command keeps the process simple; the fixed process (stages, questions, files) with
an unbounded run-time agent count is what matters; installs needing approval go through the main
session.
**How to apply:** never rebuild or reference a workflow twin; keep the shared references as the
single source of truth; never edit `seedance\` during a run. Tools installed 2026-09-16 via
winget: FFmpeg 9.0.1, Python 3.12.10, Git 2.55, VC++ runtime (PATH may be stale in fresh shells;
scripts fall back to absolute paths listed in LAYOUT.md).

Editing = CapCut (2026-09-19): user-scope MCP server `capcut` = `analyze-stack\tools\mcp\capcut-mcp\`
(Gusmares/MCP-CapCut fork of JmsLdrn/capcut-mcp, commit bbe4c21, source-reviewed; env
`CAPCUT_DRAFTS_DIR` = live store, `CAPCUT_TEMPLATE_DRAFT` = `_analyze-stack-template`, a permanent
draft copied from the verify run; `claude mcp get capcut` → Connected). capcut-cli upgraded to 0.25.0;
after every MCP save run `capcut register --apply --materials`, `sync-timelines --nested --apply`, `lint`
(the MCP registers no media and writes no Timelines mirror). P2 now always keeps CapCut and only adds
exports. Verified 2026-09-19 (full access): `smoke.mjs` end to end in a scratch folder + the registered
server reading the live store from inside Claude Code; local validator patch (audio segments excluded
from the render_index clash check, see PROVENANCE.md). Lessons: overlays go on their own text track
(`capcut_add_track` first); transition/filter names only from `capcut_list_*`. Still pending: the
template draft is unregistered in `root_meta_info.json` because CapCut was open all day (harmless).
The archived build brief is `C:\Users\Bulzart\Documents\prompts\analyze-stack-build-prompt.txt`
(the Downloads copy no longer exists).
Higgsfield MCP: claude.ai connector "Higssfield" (sic) is connected; a persistent user-scope
server `higgsfield` (https://mcp.higgsfield.ai/mcp, HTTP) was added 2026-09-16 with
`claude mcp add` and still needs the owner to authenticate via `/mcp`. The skill discovers tools
with ToolSearch and never hard-codes the prefix.
Related: [[user-ai-video-marketing]], [[feedback-pipeline-rules]].
