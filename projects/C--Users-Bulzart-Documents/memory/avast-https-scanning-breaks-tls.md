---
name: avast-https-scanning-breaks-tls
description: "Avast HTTPS scanning re-signs all TLS on the user's PC; uv, Python and Rust downloaders fail with UnknownIssuer unless pointed at the Windows cert store"
metadata:
  node_type: memory
  type: project
  originSessionId: 6df6fb40-e7ad-4b91-b765-6c6c020da849
  modified: 2026-11-05T12:18:05.595Z
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
- Don't change the user's Avast settings yourself; disabling HTTPS scanning is their call.

Related: [[local-ai-installs]]
