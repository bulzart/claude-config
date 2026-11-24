---
name: create-video-flux-klein-primary
description: "user 2026-11-24 - FLUX 3 Image Klein int8 (local) is /create-video's primary, default and required image engine; never a silent fallback"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 24e34d07-fc5a-4377-8a48-dcbcee1ff513
  modified: 2026-11-24T05:31:57.485Z
---

The local FLUX 3 Image Klein int8 worker (static-studio/scripts/image_worker.py, launched through
Documents/AI/tools/flux3_python.cmd: ComfyUI's embedded Python inside the memory guard) is the default image engine for
every /create-video run. OpenAI Images is used only when the user explicitly chooses it (`static_core.py image-engine
--engine openai --why "<their words>"`). If FLUX fails: report the real error and stop; never switch provider, model,
size or precision on your own. Never modify, reinstall or re-quantize its weights or ComfyUI.

**Why:** the user said so twice on 2026-11-24 ("our primary, default, most frequently used, and required image-generation
backend"; "do not silently switch ... report the actual problem and stop").

**How to apply:** any change touching prompts, upsampling, style, provenance or still checks is verified on the real FLUX
path (a bounded smoke run on an isolated test run, never a production run), not only through mocks or OpenAI. See
[[create-video-verify-real-paths]].
