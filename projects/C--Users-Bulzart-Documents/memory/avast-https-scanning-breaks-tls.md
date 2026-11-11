---
name: avast-https-scanning-breaks-tls
description: "Avast HTTPS scanning re-signs all TLS on the user's PC; uv, Python and Rust downloaders fail with UnknownIssuer unless pointed at the Windows cert store"
metadata:
  node_type: memory
  type: project
  originSessionId: 6df6fb40-e7ad-4b91-b765-6c6c020da849
  modified: 2026-11-11T09:55:25.427Z
---

Avast "Web/Mail Shield" HTTPS scanning is on (verified 2026-11-05): every HTTPS cert (github.com, pypi.org, download.pytorch.org, huggingface.co) is issued by "CN=Avast Web/Mail Shield Root". Tools with their own CA bundle fail with `invalid peer certificate: UnknownIssuer` / SSL verify errors. git, PowerShell Invoke-RestMethod, curl.exe and winget work (Windows store).

**Why:** uv (rustls + bundled Mozilla roots) and Python certifi don't read the Windows store, which is where Avast's root lives.

**How to apply:**
- uv 0.11+: `$env:UV_SYSTEM_CERTS='1'` (flag `--system-certs`; the old `--native-tls` name is gone). Set persistently as a User env var on 2026-11-05.
- Python: `import truststore; truststore.inject_into_ssl()` before any network call. Plain `ssl`/urllib on Windows already reads the Windows store; certifi-based clients (requests) do not. Python312 does this lazily (see [[pc-pipeline-tooling]]); never put pip-system-certs back into a Python the hooks run on (2.7 s per start).
- huggingface_hub: install `hf_xet` and keep xet ON — tested 2026-11-05, hf_xet reads the Windows store and saturates the link; plain HTTP single-connection downloads got throttled to ~1.3 MB/s.
- winget: the msstore source fails (cert pinning) — use `--source winget`.
- Node and Claude Code already trust Avast's root: Avast sets `NODE_EXTRA_CA_CERTS=C:\ProgramData\Avast Software\Avast\wscert.pem` itself.
- **Broken replies (found 2026-11-05):** for some Cloudflare-fronted servers Avast hands back `transfer-encoding: chunked` with a body that is not chunked. Claude Code (Bun) reports `InvalidHTTPResponse`, Node `HPE_INVALID_CHUNK_SIZE`. This breaks the Higgsfield MCP (`mcp.higgsfield.ai`, OAuth discovery) and the plugin HTTP MCP servers. The claude.ai connectors (through Anthropic's proxy) and api.anthropic.com (Content-Length replies) work. No client-side fix: the user must exclude these sites from HTTPS scanning or turn it off (their call). Test afterwards with `claude mcp get higgsfield`.
- **`SSLKEYLOGFILE`:** Avast injects `SSLKEYLOGFILE=\\.\aswMonFltProxy\<id>` into every process. uv's Python 3.14 (the one `uvx elevenlabs-mcp` gets) aborts with `OPENSSL_Uplink(...,08): no OPENSSL_Applink` as soon as it makes a TLS context. The 3.11 venvs and python.org 3.12 are fine. Fix per server: env `SSLKEYLOGFILE=""`. Note: `python -I` hides the crash (it ignores the variable).
- **elevenlabs MCP (fixed 2026-11-11 at the user's request):** the server (`uvx elevenlabs-mcp`, Python 3.14, httpx + certifi) trusts only certifi's roots, so the instance Claude Code started failed `list_models` with `[SSL: CERTIFICATE_VERIFY_FAILED] ... unable to get local issuer certificate` (Avast re-signs; a copy of the server I started from a script sometimes got a genuine chain: interception varies by process), and its old key (ending 6c5167) was rejected, `401 invalid_api_key`. Fix in `~/.claude.json`, `mcpServers.elevenlabs.env`: `SSL_CERT_FILE=C:\Users\Bulzart\AppData\Local\elevenlabs-mcp\ca-bundle.pem` (certifi's roots + Avast's `wscert.pem`; `make-ca-bundle.ps1` beside it rebuilds it; `wscert.pem` alone would fail whenever Avast does not re-sign) and `ELEVENLABS_API_KEY=${ELEVEN_API_KEY}` (Claude Code fills it from its environment: the pipeline's key). A running server keeps its old env: `/mcp`, Reconnect (or restart Claude Code). Test without Claude Code: spawn the server as the config says, send MCP `initialize`, then `tools/call list_models`; never print the key.
- Don't change the user's Avast settings yourself; disabling HTTPS scanning is their call.

Related: [[local-ai-installs]]

**2026-11-09: it also resets plain local HTTP (127.0.0.1):** 14 of 60 POSTs with ~800 KB answers were cut (WinError 10054, "forcibly closed") and the 60 took 268 s instead of about 1 s. The toolkit resends after a drop, so a test's stand-in sees the request twice: tests that count requests count an identical resend once (t02 `_once`). With ElevenLabs a resend after the audio was made bills it twice: `T tts say` records each passage's tries and lists `resent_after_a_drop` (video 03's real narration had none: 9,399 characters billed for 9,399 sent). Never change Avast's settings (the user's call).
