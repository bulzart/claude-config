---
name: avast-https-scanning-breaks-tls
description: "Avast HTTPS scanning re-signs all TLS on the user's PC; uv, Python and Rust downloaders fail with UnknownIssuer unless pointed at the Windows cert store"
metadata:
  node_type: memory
  type: project
  originSessionId: 6df6fb40-e7ad-4b91-b765-6c6c020da849
  modified: 2026-11-05T08:14:13.815Z
---

Avast "Web/Mail Shield" HTTPS scanning is on (verified 2026-11-05): every HTTPS cert (github.com, pypi.org, download.pytorch.org, huggingface.co) is issued by "CN=Avast Web/Mail Shield Root". Tools with their own CA bundle fail with `invalid peer certificate: UnknownIssuer` / SSL verify errors. git, PowerShell Invoke-RestMethod, curl.exe and winget work (Windows store).

**Why:** uv (rustls + bundled Mozilla roots) and Python certifi don't read the Windows store, which is where Avast's root lives.

**How to apply:**
- uv 0.11+: `$env:UV_SYSTEM_CERTS='1'` (flag `--system-certs`; the old `--native-tls` name is gone). Set persistently as a User env var on 2026-11-05.
- Python: `import truststore; truststore.inject_into_ssl()` before any network call.
- huggingface_hub: install `hf_xet` and keep xet ON — tested 2026-11-05, hf_xet reads the Windows store and saturates the link; plain HTTP single-connection downloads got throttled to ~1.3 MB/s.
- winget: the msstore source fails (cert pinning) — use `--source winget`.
- Don't change the user's Avast settings yourself; disabling HTTPS scanning is their call.

Related: [[local-ai-installs]]
