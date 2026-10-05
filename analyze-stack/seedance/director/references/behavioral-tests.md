# Behavioral Acceptance Tests

Apply the core instructions in [SKILL.md](../SKILL.md).

<a id="tests"></a>
## 13. Behavioral acceptance tests for an agent loading this file

These are regression scenarios, not measured Seedance benchmarks. They have not been executed against a downstream agent or used to certify rendered video. Test them when installing or revising the skill; assess the actual resulting prompt, not a claim of compliance.

| Scenario | Required behavior |
|---|---|
| User says only "generate the Seedance prompt" after an approved discussion | Recover the approved details and return one finished prompt, not generic questions or references to unseen conversation. |
| A recent correction conflicts with an older draft | Apply the correction and update all dependent beats and the ending; do not restore the discarded version. |
| Memory is unavailable | Use current accessible context; do not fabricate remembered details or claim account-wide access. |
| Two similar stations exist | Anchor them distinctly and retrieve each object from its last causally established location. |
| An object is explicitly moved between stations | Update the location; do not freeze its initial position under a generic preservation rule. |
| A required action repeats | Preserve acquisition, transport, release, return, and accumulation for the required repetitions. |
| The actor's hands are occupied | Add a feasible approved support transfer or change optional blocking before another hand-dependent action. |
| A later action needs an unavailable object | Establish its source and acquisition earlier, or flag the genuinely missing requirement. |
| A prop is off-screen for several beats | Preserve its state unless plausible declared activity changes it; do not silently reset it. |
| A camera move reverses screen-left/right | Preserve world location and character handedness rather than swapping object identities. |
| A cut joins an open object to a closed one | Show the required closure or label an authorized time jump; do not conceal a method-critical step. |
| Material enters a container with existing contents | Specify context-appropriate interaction and accumulation; do not replace earlier contents or apply a universal floating rule. |
| Contents are behind an opaque surface | Distinguish hidden from absent; do not force physically impossible visibility. |
| A mechanism has a documented hinge or latch | Respect the real axis, sequence, support, and clearance; do not invent an easier mechanism. |
| The user requests intentional magic | Preserve the authorized exception and its scope while maintaining unrelated continuity. |
| Required actions do not fit the requested duration | Protect essential method; flag the incompatibility and propose the least disruptive supported plan. |
| A decorative camera move hides a required contact | Redesign framing/movement so the key mechanism remains readable. |
| An image contradicts the requested first-frame state | Identify the conflict and resolve it; do not pretend both states can occupy the opening. |
| The request contains no reference media | Do not invent asset tags; write text-only direction or request truly essential missing media. |
| The user requests a nonphysical color edit with dependent reflections | Account for dependent appearance; do not guarantee contradictory pixel preservation. |
| A source clip is extended | Continue its inspected boundary state without replay or unexplained changes in holdings, contents, velocity, or sound. |
| Only screenshots are available for video QA | Report visible defects only; mark motion/synchronization unassessed. |
| The provider lacks a requested control | Do not invent its existence or a substitute API parameter; separate creative intent from execution. |
| The user requests only a prompt | Do not generate media, spend credits, emit the whole guide, or expose private planning. |
| The user asks for perfection or a measured improvement without results | Apply the audit, but do not guarantee flawless footage or fabricate benchmark numbers. |
| A new task is unrelated to all examples | Derive objects, materials, methods, style, and checks from the new task; import none of the example subject matter. |

