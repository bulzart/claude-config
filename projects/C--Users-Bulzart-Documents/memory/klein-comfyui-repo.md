---
name: klein-comfyui-repo
description: "bulzart/klein-comfyui (private) - standalone FLUX Klein worker = static-studio image_worker.py + 4 adaptations; re-sync after worker changes, on the user's say"
metadata:
  node_type: memory
  type: project
  originSessionId: 24e34d07-fc5a-4377-8a48-dcbcee1ff513
  modified: 2026-11-24T15:02:38.984Z
---

Local repo C:\Users\Bulzart\Documents\klein-comfyui, branch main, origin https://bulzart@github.com/bulzart/klein-comfyui.git
(private: 404 without a login). Commit identity: Bulzart + the GitHub no-reply address. core.autocrlf true; its files are CRLF.

Its image_worker.py is Static Studio's worker (C:\Users\Bulzart\.claude\static-studio\scripts\image_worker.py) with four
adaptations kept on every sync: (1) the repo's title line, (2) its opening lines (standalone by default; AWL_IMAGE_ROOT or
"root" in the job), (3) the studio gate only for a job that names its run (`if job.get("op") == "generate" and
job.get("run"):`), (4) gpu_take returns None when gpu_lease.py is not next to it. tools/flux3_python.cmd is a generalised
launcher (COMFYUI_PORTABLE), NOT the PC's own C:\Users\Bulzart\Documents\AI\tools\flux3_python.cmd (personal paths): never
copy that over it. memguard.py and flux3_upsampler_prompts.json are byte copies.

Synced 2026-11-24 (commit 9b0f305, the user: "push ... into comfyui repo if there was any changes too"). Standalone `check`
(with the ComfyUI probe) passed; three standalone generate runs were stopped by memguard while FLUX loaded (10.25 GB, free
commit ~12 GB against FLUX's ~11.5 GB plus the 3 GB floor), so a standalone image from the repo copy is still owed when the
PC has the memory. Adaptations 3 and 4 were checked directly in ComfyUI's embedded Python.

**Why:** the user keeps this repo as the FLUX Klein integration on its own; Static Studio's worker keeps changing.

**How to apply:** when the user asks to push it after a worker change: re-apply the four adaptations to the current worker
(never put adaptation 3 into Static Studio: there a job without a run must still be gated), diff to confirm only those
differ, test standalone (COMFYUI_PORTABLE set, then tools\flux3_python.cmd -X utf8 image_worker.py job.json), scan the
outgoing diff, commit with the no-reply identity and push. See [[github-accounts]], [[create-video-flux-klein-primary]].
