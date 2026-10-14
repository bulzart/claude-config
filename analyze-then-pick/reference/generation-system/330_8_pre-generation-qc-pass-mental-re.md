## 8. Pre-generation QC pass (mental render, first frame → last frame)

Walk through the planned video in 0.5–1 s steps and confirm each of these, or fix it before sending:

- [ ] Subject identity and wardrobe are stable; the approved character is used and the source
      person is excluded.
- [ ] Client asset fidelity: canonical geometry, materials, labels and interface; correct scale
      relative to hands and body.
- [ ] Size reckoning: for every product in every shot, the real dimensions, the depth (derived from the
      frame, its basis written, never assumed), the lens,
      the expected fraction of the frame and the ratio to a named neighbour are in the plan and in
      the prompt; a start frame was measured with `atp.py scale` before animating; the size ladder
      holds when several products show (`anomaly-catalog.md` §2.7).
- [ ] Anchor class (§4b.1b): the posture, the visible support, the place and its story reason are in the plan
      and the prompt; no lean on a prop the model has to invent; nothing on a thin sheet; no source beat
      taken over. Where the guide lists size as a model limit, the anchor is from its passing list or a guide
      image (§4b.6) carries spot and size, and no sizing words are relied on.
- [ ] Source surfaces: every printed surface of the source that a guardrail or §9b names (a poster, a
      livery, a gate board, a monitor page, a shirt print, a patch or logo on the kept garment) is an explicit
      "replace / remove only … and reconstruct it as <named concrete content>" sentence in the model's
      grammar, never a description of blankness, and the original item is in the exclusion line
      (`brand-guardrails.md` §4); a real person's name on a screen is removed from the prepared source (§5c.2b).
- [ ] Scene layout, perspective and camera logic are consistent across every beat and cut.
- [ ] Placement, contact, grip and occlusion are physically possible at every step.
- [ ] Surroundings are consistent (surfaces, props, background people) with nothing morphing.
- [ ] Lighting, reflections and shadows agree with the scene for the inserted asset in every beat.
- [ ] Natural placement (§4b), if used:
      - the anchor is logical, and the item is visible most of the runtime;
      - it is in frame from frame 0, the same spot holds in every shot, and every move has a visible action;
      - it is noticed, not featured, and it does not read as an edit.
- [ ] Contents (§4b.0): every glass, cup or other vessel of the product's category in the subject's
      scene holds the product (from its contents sample), with the package open beside it, unless
      the plan says why not. Every vessel's contents are stated in the prompt.
- [ ] Props in the asset photos (a glass, a cup, a snack) are planned as contents or excluded in the
      prompt.
- [ ] Counts: every multiple has its number at t=0, at every event and at the end, and nothing
      appears, vanishes or doubles without a cause (`anomaly-catalog.md` §2.1, §2.5).
- [ ] Openings and use: every use beat goes through the product's real opening or control after its
      preparation step, with the contact point, orientation and body mechanics of its affordance
      sheet; no effect precedes its cause; no reference image shows a later state than t=0
      (§2.2, §2.3, §2.8).
- [ ] Permanence and parts: the count and state of every tracked item are restated after each exit,
      occlusion, cut, hand-off and seam; caps, straps, straws and labels stay with their body
      (§2.4, §2.5, §2.9). The plan lists its QC checkpoints (`anomaly-catalog.md` §3 step 8).
- [ ] Blend: the product reference is scoped to shape, colours and label; the prompt states the
      room's light on the product, its size against a neighbour, its mark angle, its contact shadow
      and its camera angle; the anchor touches or is partly occluded by something; a start frame
      passed the paste test (`anomaly-catalog.md` §2.15).
- [ ] Solidity: every thrown, dropped, swung or passing thing has its path written relative to the
      product (past it on a named side, or onto it with the consequence), the solidity exclusion
      is in the prompt, and no placed object sinks into its surface or a hand (§2.14).
- [ ] Sharpness: the plan's intent names the goal, the job, the one idea, the emotion arc or laugh
      mechanism and the share line, and the concept passed the gate (`creative-direction.md` §6).
- [ ] Transfer (Create): the plan takes only craft from the references and the copy test passed;
      no premise, setting, character, turn, line, first frame, ending or product beat is a
      reference's (`creative-direction.md` §5.0).
- [ ] Motion is natural in speed and weight, with no unmotivated speed changes.
- [ ] Every object state matches the ledger at every checkpoint.
- [ ] Spot (§4b.1c): visible in the source's first frame and along the whole camera path, outside every
      hand's lane over every beat, bare and wider than the product, not the nearest plane (a near-plane spot
      the user marked stays, with a guide), not "in front of" a neighbour it would sit on, fully inside the
      frame; the user's marked spot is used.
- [ ] Guide (§4b.6), when the model lists size or place as a limit and no passing-list anchor fits (always for
      a near-plane spot the user marked): built from the source's bare surface scrubbed of performer, clothing
      and lettering (Create: neutral texture only), the product shaded in the scene's perspective at
      the reckoned size, its label sharp, the spot passing the line above, bound in the prompt as spot and size
      only, and measured with `atp.py scale --frame`.
- [ ] Source prepared (§5c.2b): orientation (a mirrored selfie flipped, the identity photo too); burned-in
      text, identifying names and marks covered by prompt sentences (clean-plate lines first, never trimmed;
      no tool removes them); a baked face effect planned for; left and right of every beat read on the
      prepared frames.
- [ ] Pacing matches the family profile: no dead space, every second has a job.
- [ ] Transitions are all motivated, and multi-clip hand-offs are identical.
- [ ] No free physical motion is pinned to exact timestamps; a required end state has a visible
      cause (§5b).
- [ ] The text plan follows the mode policy. The generated plate is clean (only the product's real
      label). Analyze Mode overlay text is planned as CapCut layers. No accidental text.
- [ ] Inserts (§3c): the generation covers only the reference's own content, and every split point
      is a planned beat boundary.
- [ ] House approach (when examples exist): the plan applies its consistent rules, and none of them
      breaks a hard rule.
- [ ] Beginning, intermediate and end states are all readable and correct.
- [ ] Params, references, prompt and post plan describe the same video (the dependency chain holds).
- [ ] Format: 9:16 and 720p through the model's own parameters (`models/index.json` →
      `output_9x16_720p`), with a conform step if needed.
- [ ] Preflight done: cost known, `adjustments` read and reconciled.

