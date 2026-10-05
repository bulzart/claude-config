# prompt-writer — agent brief (Stage 5, replication; one agent per clip, in parallel; mode `write` | `fix`)

Load first (all of them, every time): `LAYOUT.md`, `references\prompt-template.md` (file format, block rules,
prompts.json entry, self-check), `seedance\SEEDANCE-SPEC.md` §3.5 (reference syntax), §4 (native audio and
bracket rules), §5 (camera vocabulary), §6 (official structure, timestamps, actions), §9 (failure modes),
§12 (the skeleton), `C:\Users\Glaresquare1\.claude\skills\sd25-pe\SKILL.md` (ByteDance's official
optimisation rules: intent first, template first, every asset accounted for, separate parameters, no
unrequested negatives, observable performance, dialogue ledger, keyframe sentences verbatim),
`references\physics-rules.md`, `references\blending-rules.md` (§4.2 global rules), `references\continuity-rules.md`,
`references\style-taxonomy.md` §2 (phrasing), and the **Seedance 2.5 Director** bundle (read-only):
`seedance\director\SKILL.md` §1–§5 (intent contract, asset ownership, persistent world + causal action plan, staging
and audit, compile + recheck), `seedance\director\references\prompt-playbook.md` §7 (compile) and §8 (release gate),
`seedance\director\references\continuity-and-causality.md` §4.2–§4.4 (causal transitions, propagation, backward/forward
validation) and §5 (anomaly categories — run them on your own draft), `seedance\director\references\examples.md`
(patterns A–J: transfer the logic, never the subjects). Precedence: SPEC/EDITSPEC numbers and the stack's owner
rules win; the director governs how you plan and phrase (SEEDANCE-SPEC.md §14). Read only your clip's inputs listed below.

## Purpose
Write ONE Seedance 2.5 clip prompt that reproduces its exact time slice of the original (Mode 1/2) or
its storyboard rows (Mode 3) in full detail — subjects, actions, camera, lighting, setting, dialogue,
sound, on-screen text logic — as a start state, a second-by-second timeline and an end state, with the
swapped product carried consistently, the reference attachments cited in the spec syntax, and the
continuity handoff to the next clip.

## Inputs
`40-plan\plan.json` (your item: source slice, beats, shots, cuts inside, dialogue, references, swap moments),
`40-plan\continuity-sheet.md` (master sections A–H and YOUR row + the next row), `30-decisions\swap-map.md`
(global rules + the entries for your moments) when a swap exists, `40-plan\style-bible.md` (swap) or
`20-analysis\style-profile.md` (STYLE LINE), `40-plan\compression-plan.md` (Mode 3: your storyboard rows),
`20-analysis\visual.md` (your shots' rows), `audio.md` (your lines, SFX, music state), `beat-map.md` (your beats),
the frames in `50-prompts\references\` for your clip and `10-measure\keyframes\` for your shots (LOOK),
`30-decisions\answers.json` (Q4a, Q5, Q6). `fix` mode: `60-qa\fixes-round-N.md` (your section) and your current file.

## Outputs
`50-prompts\clip-NN.md` in the template format (header, Attachments table, Platform parameters, `## Prompt`,
`## Continuity`, `## Writer notes`). The main session builds `prompts.json` from the clip files.

## Method (`write`)
1. Read your plan item and your continuity row. LOOK at the clip's start frame and at each shot keyframe
   inside your slice (Read tool); note hand positions, product orientation, fill levels, camera side, light.
2. Story contract (sd25-pe): subjects and counts, actions in causal order, prop ownership and final states,
   dialogue ledger (every line verbatim from `audio.md` with speaker, delivery, language; never turn speech
   into silence; never invent lines; Mode 3 paraphrase only when Q4a allows), what must be preserved.
2b. Director pass (before writing a single block): (i) intent contract for THIS clip — viewer takeaway, required
   content and the required METHOD (a hand-poured drink stays hand-poured; three scoops stay three scoops), initial
   state, essential events in order, ending, fixed traits vs allowed changes, real references, unknowns; (ii) world
   ledger — every consequential entity with `identity | anchor | orientation | holder/support | contents/count |
   mechanism state | visibility | ongoing motion` at t=0 (from the sheet) and after each beat; (iii) expand every
   essential action as `preconditions → actor/mechanism → reachable path and contact → transfer/change → observable
   consequence → updated state` (acquisition, support, transport, placement, release for handling; source → carrier →
   destination with accumulation on both sides for material; no double-booked hand; receiver support before release);
   (iv) walk backward from the END STATE (what must already be true) then forward (every later use matches the last
   recorded state; distant dependencies, not only adjacent sentences); (v) passive processes keep running between
   actions (settling, drips, foam collapse, condensation); hidden ≠ absent; a camera move relocates nothing.
3. Fill the template blocks in order: ASSET BINDINGS (one line per attachment, use-only / do-not-use,
   "one single object" for multi-view product images; chaining sentence only when the plan says chained),
   ONE-SENTENCE SUMMARY, START STATE (= your sheet row verbatim + layout from section A), TIMELINE
   (continuous integer-second ranges summing to the duration; ~15–25 words/s; one main event per range;
   cause before reaction; SFX `<…>`, music `(…)`, dialogue `Speaker (language, delivery): "line"`; `Hard cut.`
   + new shot line at every internal cut; camera one move per shot), CAMERA, LIGHT & LOOK (STYLE LINE verbatim),
   AUDIO ("No BGM; generate only environmental sounds and action sounds" when the original has none;
   "No subtitles." always on 9:16), PRODUCT INVARIANTS (swap-map global rules; every moment's consequences:
   colour result, foam/fizz, condensation, reflections, grip, sound, count; no original brand words anywhere),
   END STATE (= next row's start state verbatim; hold 0.5–1 s), CONSTRAINTS (short, last, only the
   subtitles/audio/brand/duplicate-character lines plus one scenario-specific physics line).
4. Apply the physics DO/DON'T table (physics-rules §12) to every range; realistic timing (§7); ≤ 2 movers.
5. Platform parameters line (mode `omni_reference` when any reference is attached, else `t2v`; duration =
   plan item; aspect from Q6; resolution 1080p default; generate_audio true; bitrate_mode high) — NEVER
   inside the prompt text.
6. Release gate (director prompt-playbook §8): re-read ONLY the `## Prompt` block as a stranger with no access to the
   sheet — intent+method preserved; every later use has a compatible earlier state; no contradictions in paths,
   support, capacities, hands, visibility; events fit the seconds; cuts never reset state; the ending follows; only
   real attachments cited; no "as discussed" / "same as before" / placeholders / research notes / commands asking the
   model to reason; every detail earns its place. Classify what you find as blocker (fix now) / major (fix now) /
   polish (fix if cheap); reinforce a high-risk state at its later use ("the same glass, now two-thirds full") rather
   than repeating every invariant in every sentence — and never write "no teleporting" or "perfect physics" instead of
   the explicit feasible transition. Then the template self-check (§4); write the file with status `draft`, word
   count, swap moments covered, risks.

## Method (`fix`)
Apply every finding routed to you (F-ids) exactly as instructed; change nothing else; keep the START
STATE/END STATE contract with the sheet; bump `qa rounds`; list the F-ids you fixed in Writer notes; if a
fix contradicts the continuity sheet or another finding, do not guess — write `needs-owner-decision` with both options.

## Quality bar
- 250–600 words (≤ 900 hard); no parameters, ids, URLs or analysis in the prompt; every `@` asset bound.
- No vague bridge verbs ("handles", "does the process", "then it is ready", "seamlessly transitions") where a
  mechanism is required; no generic quality adjectives in place of the mechanism; the prompt is self-contained.
- START/END states are string-identical to the continuity sheet; the product block matches the swap map.
- Every dialogue line ≤ 10 words per spoken sentence, language named when not English, speech finished
  before the final hold; non-speakers' mouths closed.

## When evidence is missing
If a frame is unreadable or a hand is occluded, describe the most plausible state consistent with the
sheet and mark it in Writer notes as "inferred". Never add objects, lines or actions the original does not
show (Mode 3 merges are the planner's, not yours).
