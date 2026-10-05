# Conversation-Aware Prompt Playbook

Apply the core instructions in [SKILL.md](../SKILL.md).

## Contents

- [Conversation](#conversation)
- [Inputs](#inputs)
- [Direction](#direction)
- [Output](#output)
- [Release](#release)

<a id="conversation"></a>
## 2. Recover the intended result from conversation and memory

Treat "generate the prompt" as a request to synthesize the relevant preceding interaction, not as a context-free new brief.

1. Review the current request, earlier approved decisions, corrections, actual media, and relevant accessible project memory. Use authorized retrieval tools when needed context is missing; never assume access to other chats, hidden files, or an account's entire history.
2. Resolve references such as "that version," "same setup," "the first one," "continue," and "as discussed." Keep rejected branches and failed generated footage separate from the approved design. An assistant suggestion is not automatically a user decision.
3. Follow higher-priority instructions. Within the creative brief, use the latest explicit user correction over an older conflicting preference. Bind approved assets to their assigned properties. Use retrieved memory as relevant context, not authority over the current user.
4. Separate **required content**, **required method**, **fixed traits**, **allowed changes**, **optional style**, **known failure symptoms**, and **unknowns**. An example of a failure teaches a class of checks; it does not become mandatory subject matter in future prompts.
5. Form a compact intent contract: purpose/audience; what the viewer must understand; actual subjects and setting; initial state; ordered essential actions; emotional or practical payoff; final state; duration/frame shape/audio; allowed cuts; exactness requirements; references; forbidden substitutions.
6. Fill low-risk creative gaps conservatively without changing the story. Ask one focused question only when an unresolved issue materially changes the result and cannot be recovered. Do not ask again for known details. Provider, pricing, or render-budget gaps do not block a provider-neutral prompt draft.
7. Carry every necessary scene fact into the final prompt. Never write "as discussed," "same as before," or depend on the video service having access to this conversation. Use previous footage as a reference only when it is actually supplied through a supported control.

Preserve the user's intended **means**, not only the endpoint. A hand-operated action must not become automatic; several transfers must not become one unexplained appearance; an instructional sequence must not become an aesthetic montage that omits the operation.

Do not import unrelated remembered preferences. For example, a special character-design constraint belongs only to the project that established it, not every person or creature in later videos.


<a id="inputs"></a>
## 3. Choose the operation and inspect the actual inputs

Choose text-to-video, first-frame animation, multi-reference generation, keyframes, editing, or extension deliberately. These are planning categories, not universal API field names. Check the active provider before execution. Use conventional footage, graphics, simulation, or compositing when exact geometry or guaranteed preservation is the deliverable.

Inspect available images; inspect video action and boundaries when playback is possible; inspect audio when sound matters. Mark anything not inspected as unknown. Never invent an uploaded asset, model identifier, person, mechanical feature, or source-video event.

Maintain an internal manifest: `asset | actual provider label | role | authoritative properties | properties not to inherit | inspected status`.

Assign reference ownership by property: subject identity, product geometry, room layout, motion, camera path, material/lighting, or audio. Resolve conflicting references rather than asking the model to average incompatible versions. Several views of one subject are not several subjects. Preserve deliberate asymmetry. Treat unseen surfaces as unknown unless creative invention is allowed.

Use only actual supported attachment tags or IDs in a submitted prompt. Placeholder notation in this guide is illustrative, not Seedance syntax. A reference does not automatically lock the first frame, isolate a region, impose a motion path, or provide pixel-exact preservation. State the desired inheritance and plan to inspect it.


<a id="direction"></a>
## 6. Design flow, timing, camera, and sound together

Preserve the causal plan first; design the viewing experience around it. Establish enough geography to understand the action, foreground the important interaction, let consequences register, and end on the intended result. Keep emotion, focus, visual hierarchy, lighting, material response, and sound aligned with that progression.

Budget time for preparation, contact, repeated operations, movement, and settling. Check whether the required action can plausibly fit at the requested speed. Treat timecodes as staging targets, not guaranteed frame-accurate controls. Use contiguous shot intervals totaling the duration; nested simultaneous action/sound cues are allowed when intentional and compatible.

Choose a continuous shot or deliberate cuts. Do not force every scene into one take or an arbitrary four-shot template. Protect method-critical events from cuts, whip pans, extreme blur, obscuring hands, and shallow focus that makes them unverifiable. Keep natural pacing; do not atomize ordinary motion into dozens of stiff microcommands.

Give each movement an actor and frame of reference. Separate object rotation from camera orbit, zoom from physical approach, and character-right from screen-right. Give each shot one dominant camera behavior, or sequence its phases explicitly. Maintain plausible camera paths and readable screen direction; a change of viewpoint must not rewrite the set.

Maintain light-source direction and environmental conditions unless a motivated change occurs. Use lighting and depth of field that reveal the operation rather than hide it. Keep moving contact points and the target in a readable plane when that is central to acceptance.

Bind sound to its actual cause: impact at contact, motor during actuation, speech from the named speaker, ambience from the established space. Respect the requested line, speaker, language, and delivery; allow breath and reaction time. Separate narration from on-screen speech. Do not invent dialogue, music, commercial claims, or extra characters to fill time.

If the scene is overloaded, simplify optional scenery, simultaneous actions, or camera complexity before sacrificing required meaning or method. Use supported references or a different production plan for difficult essential actions. Do not silently shorten the story, alter a non-negotiable duration, substitute a tool, or hide the hard part. Briefly flag a genuine incompatible requirement and give the least disruptive viable alternative.


<a id="output"></a>
## 7. Compile one final prompt

Treat the prompt as a compact directing specification, not a dump of the internal ledger. Dreamina's official guidance favors concrete visible direction, reference ownership, purposeful timing, focused constraints, and isolated revisions. Use these published principles without treating them as guaranteed model laws. [S3](../references/sources.md#s3)

For a simple shot, write a concise natural paragraph. For a complex scene, use the following organization only where helpful:

```text
FORMAT AND INTENT
Duration, frame shape, shot structure, and the intended visible outcome.

REFERENCE OWNERSHIP
Actual attached references and the properties each controls, when present.

INITIAL WORLD STATE
Relevant subjects, distinct locations, object placement, holdings, contents,
and only the fixed traits needed for this scene.

CONNECTED ACTION AND CAMERA
Chronological beats with the actor, visible mechanism, important movement,
state consequence, camera behavior, and motivated transition.
Carry earlier consequences into later actions explicitly where ambiguity matters.

ENDING
The required final positions, holdings, contents/condition, and emotional payoff.

LOOK AND SOUND
Specific coherent treatment and event-linked audio or requested silence.

CONTINUITY CONSTRAINTS
Only the scene's high-risk invariants and necessary exclusions.
```

Reinforce a critical state at its later use, not in every sentence. For example, establish where a prop was left and identify that same location when it is retrieved. For changing contents, name the accumulated state at the next interaction. Prefer this to "no teleporting" without an actual trajectory.

Replace vague goals with visible direction. "Natural hand motion" is insufficient when the required act is a specific acquisition, transfer, and release. Likewise, "physically accurate" is insufficient when material movement and its resulting state are unspecified.

Use precise detail where it resolves identity, method, causality, state, timing, or composition. Remove redundant adjectives, irrelevant backstory, unrequested technical jargon, competing styles, and decorative actions. Do not hardcode a word count, shot count, subject, material, or beat duration. Check a real provider prompt-length limit before submission; when shortening, preserve causal bridges before decorative language.

Make the final prompt self-contained and ready to paste. Resolve pronouns, reference labels, placeholders, discarded alternatives, and incompatible directions. Do not include research citations, internal audit scores, API payloads, uncertain architecture claims, or commands asking Seedance to "think step by step" inside it.

**Response contract:** for "generate the Seedance prompt," return the completed prompt by default, even when the user did not explicitly say "prompt only." Do not prepend an essay or routinely append follow-up offers. Add a brief note outside the prompt only for a material unresolved assumption, incompatibility, or actual provider setup requirement. Supply multiple versions or explanatory planning only when requested. For model-logic questions, answer the technical question instead of forcing a video prompt.


<a id="release"></a>
## 8. Mandatory release gate: validate the written prompt, not only the plan

Read the compiled prompt as a fresh specification with no conversation memory. Check it in both directions and across every transition:

- **Intent:** the approved outcome, required method, corrections, and non-negotiables survived compilation; rejected ideas did not return.
- **State and causality:** every important later use has a compatible earlier state; every material change has an actor/mechanism or an explicitly authorized exception; required repetitions and transfers remain visible.
- **Physical and structural feasibility:** topology, support, mechanics, capacities, material response, available hands, motion, and optical visibility do not knowingly contradict each other.
- **Temporal and cinematic flow:** events fit the duration; camera and sound support the same action; cuts/occlusions do not reset state; the ending follows from what happened.
- **Input and contract integrity:** references are real and correctly bound; instructions are mutually compatible; no invented controls, unseen assets, unresolved template text, or false inspection claims remain.
- **Craft and economy:** the essential interaction is readable; pacing, lighting, framing, and payoff serve the brief; additional detail earns its place.

Classify defects internally as **blocker** (impossible/conflicting required states), **major** (missing mechanism, location, dependency, or essential visibility), or **polish** (nonessential clarity/style). Repair blockers and major issues first. Recheck any affected earlier/later beats after repairs. Stop when the prompt meets these conditions; do not claim an objective "100/100" score or iterate indefinitely chasing an undefined perfect prompt.

Prompt readiness and render quality are separate. Use `pass / fail / unknown` for a real review, and never turn an unknown into a pass. No phrasing can certify ungenerated footage.

