---
name: create-video-content-review
description: "user 2026-11-21: /create-video content review per reference (safety vs religion/superstition vs holiday, kept apart) with selective exclusion; checked downstream (direction, script flags, shot/job prompts, reviewer packets); every picture on the timeline looked at"
metadata:
  node_type: memory
  type: project
  originSessionId: 043c101b-0b28-4a7f-82ee-6dd10286c87b
  modified: 2026-11-20T23:05:04.637Z
---

User 2026-11-21 brief, Parts 3 and 4:
- Handle gore, distressing and harmful material by context, not keyword filters.
- War, crime and death stay possible as subjects, told non-graphically.
- Religious, superstitious and holiday material is the user's creative exclusion, NOT a safety matter ("Do not falsely classify harmless cultural, historical, or religious material as dangerous").
- Exclusion is selective: an affected segment plus what narratively depends on it, never a fixed window. The rest of the reference stays useful.
- Excluded themes must not come back, even disguised.

**Audit before the change (2026-11-21):**
- Functional: only `content_flags` (CONTENT_FLAGS regexes on script lines, answered under "Content flags" in editorial-review.md).
- Prompt-only: 02 "No holiday, religious or superstitious narrative devices" and "Nothing indecent, gory or distressing"; 04 and 06 checks (06 says every still is checked); HOUSE_RULES in the reviewer packets.
- Nothing at all for reference ingestion or analysis, frame prompts, generation jobs, generated stills or the timeline.
- Provider limits: OpenAI moderation only. FLUX Klein is local and has none.

**Built (static_core):**
- **`content-review --ref V### --file review.json`**, saved to `20-analysis/content/V###.json`:
  - `kind` is `safety` (with a category and a severity), `religion_superstition` or `holiday` (no severity).
  - `action` is exclude, restrict_visuals (safety only) or keep (with why).
  - Each segment: `depends` (by narrative dependency), `avoid` (what must not come back), `confidence`.
  - The review also has `story_without_exclusions` (coherent / bridged / too_dependent) and `usable`.
  - Code checks shape and process only:
    - religious material recorded as safety is refused;
    - minors is always excluded;
    - high severity is never kept;
    - an unsure segment that is still used needs a closer look on disk.
  - `--signals` gathers pointers; `--status` lists every reference.
- **Downstream:**
  - `direction_facts`: cited references need a review; an observation inside an excluded range (with its depends) is an issue; a restricted range or `too_dependent` is a warning.
  - `excluded_themes` → `theme_hits` (all of an avoid phrase's content words) feed script `content_flags`, `shot_facts` (prompt flags: 02's words + themes, answered by a shot `content_note` of 6+ words or a rewrite) and `media_gate` (thumbnail and treatment-preview prompts, plus style words added around a frame prompt).
  - `house_rules(rd, n)` adds the excluded themes to every reviewer packet. The house rules now say plainly that stating someone was hurt or died is fine.
- **Pictures:**
  - `content-review --video N --pictures --file looks.json` writes `60-visuals/video-NN/content-looks.json`, with each file's sha256.
  - `timeline_facts` refuses a picture without a clean look of its current bytes.
  - `release-check` reports `content` (pictures looked at; export seen only through watch sheets).
- Docs updated: 01 (Content review section), 02 (sensitive subject vs graphic telling; reference material left out stays out), 04, 06, 07 (schemas), 10, and the command file.

**Effect on the existing run:** video-01 (no direction, no timeline yet, 68 frame prompts with no flagged words) will need a picture look per still before its timeline passes, and reviews of any reference its future direction cites.

**Validated on real references 2026-11-21** (scratch run, V008 Rome, V017 WW2 soldier POV, V018 WW2 daily life, V026 psychology of discipline; one analysis agent per reference). What it showed, and what changed for every future run (user: "fix the underlying causes in the real workflow rather than patching the individual examples"):
- **The watch sheets (a frame every 5 s) never showed 12-43% of shots** (V026: 131 of 303). A 1.8 s noose-like rope drawing in V026 was seen only because the agent built its own per-shot montage. Fix: `content-review --shot-sheets` (one frame of every shot, 36 to a sheet) is required before a review saves. The export gets the same shot sheets inside `av-profile --video --file`, and the final review packet lists them.
- **Over-exclusion.** Agents excluded children in ordinary scenes as "minors", low-severity moments, and uncertain pictures. Fixes:
  - the category is renamed `sexual_content_minors`; `minors` is refused with an explanation;
  - low severity is never excluded;
  - every action needs `why` (an exclusion says why restricting is not enough, or why it is a device and not a fact);
  - every `unsure` segment needs a closer look, whatever the action;
  - `evidence` must cite mm:ss times;
  - manual 01 says to take out as little as keeps the video within 02, and that a cue (colour, word, shape) is a reason to look, not a verdict.
- **Time-range blocking also blocked useful elements inside an excluded moment.** Fix: a direction observation with `borrows_only` (6+ words naming what it takes) becomes a warning instead of an issue.
- **Deliberately not changed:** the CONTENT_FLAGS word list (no new keywords, per the user). Paraphrased themes ("a pale soldier who had died stood beside him") pass the word net by design; the fresh reviewers' house rules and the final reviewer's shot sheets carry the semantic check.
- **GPU Whisper on the full references:** 13.6-14.2x real time; 65 min of audio prepared in 436 s, profiled in 90 s.

Related: [[create-video-analysis-2fps]], [[awl-static-no-indecent-gory-distress]], [[scripts-gather-agents-decide]], [[reasoning-over-rule-lists]].
