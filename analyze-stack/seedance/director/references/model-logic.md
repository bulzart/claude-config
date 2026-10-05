# Model Logic and Evidence Boundaries

Apply the core instructions in [SKILL.md](../SKILL.md).

<a id="model"></a>
## 9. Model logic and engineering boundaries

Keep five evidence categories separate: **developer-confirmed 2.5 fact**, **named-provider behavior**, **predecessor research**, **authored production heuristic**, and **observed output**. Do not promote one into another.

**Verified 2.5 scope:** ByteDance describes a unified multimodal audio-video architecture inherited from 2.0. Its launch material describes up to 30 seconds per generation, extensions, multimodal references, and timestamp-directed editing; the stated reference mix is up to 30 images, 10 videos, and 10 audio clips. These are developer-level descriptions, not universal endpoint guarantees. ByteDance also acknowledges remaining difficulty with complex-motion physics and highly crowded interactions. [S1](../references/sources.md#s1) [S2](../references/sources.md#s2)

**Published lineage, not a 2.5 block diagram:** the 1.0 report describes a video VAE, diffusion transformer, refinement, and flow-matching training. A VAE compresses and reconstructs video representations; a generative transformer models the transformation needed to produce conditioned samples. The 1.5 Pro report describes dual audio/video branches, cross-modal interaction, supervised fine-tuning, and reinforcement learning from human feedback. The 2.0 model card describes unified conditioning on text, image, audio, and video. Keep all these statements attached to their actual versions. [S8](../references/sources.md#s8) [S7](../references/sources.md#s7) [S6](../references/sources.md#s6)

Use this **conceptual abstraction**, not a disclosed 2.5 algorithm:

`approved brief + references + operation/settings -> conditioned audio-video realization -> provider processing -> inspected output`

`output ~ P(video, audio | text, references, operation, settings)`

Do not assume the service interprets prose as executable code, maintains the agent's object ledger, performs a certified physical simulation, or sees the current chat. A visually plausible frame does not certify a feasible action sequence. The ledger and dependency audit are external authoring tools that make the intended sequence explicit and reviewable.

Use engineering understanding conservatively: separate appearance from movement and camera; supply relevant actual references; specify causal events; inspect temporal behavior rather than assuming it. Do not diagnose a rendered defect as a particular hidden attention failure. A successful take is not evidence of the network's implementation.

No standalone official 2.5 engineering paper is established in this guide's evidence set. Exact parameter count, layer topology, latent dimensions, sampler, training mixture, native HDR/4K behavior, and local-inference hardware requirements remain unverified here. Do not import predecessor numbers to fill these gaps. Verify new model-specific disclosures before updating this statement.

Do not invent special syntax, token-priority laws, ideal word counts, CFG/step settings, LoRA support, or a guaranteed negative-prompt field. Do not imply that saying "physics engine" or "deterministic continuity" activates a hidden control.

