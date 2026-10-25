---
name: elevenlabs-setup
description: "ElevenLabs MCP (local, API key) installed in Claude Code user scope; free plan; Albanian not officially supported; outputs must go under Desktop"
metadata:
  node_type: memory
  type: reference
  originSessionId: c1639feb-dd77-47ca-950d-178277c7920f
  modified: 2026-10-25T23:21:02.847Z
---

On 2026-10-26 the local ElevenLabs MCP (`elevenlabs-mcp` 0.12.2, run via uvx at `C:\Users\Glaresquare1\AppData\Local\Programs\Python\Python312\Scripts\uvx.exe`) was added with `claude mcp add elevenlabs -s user`, with the user's API key in the env. ElevenLabs has deprecated and archived this local server in favour of the hosted OAuth server, which is also connected separately as the claude.ai ElevenLabs connector.

- The account is on the **free tier**: 10k credits a month, no commercial license, and mp3 192 / pcm 44.1k output is not available. As of 2026-10-26, 3,335 credits were left.
- Models include `eleven_v4`, `eleven_v4_turbo` and `eleven_v3`. **Albanian (sq) is not in any model's official language list**, and the voice library has no Albanian voices. Albanian text still generates when `language="sq"` is passed.
- MCP text_to_speech can only write under `ELEVENLABS_MCP_BASE_PATH` (default `C:\Users\Glaresquare1\Desktop`), so other folders fail with "not writeable".
- The first job was a 15 s Albanian skincare ad VO in `Desktop\skincare-ad-albanian\` (voice Jessica, eleven_v4), related to [[digital-products-business]].
