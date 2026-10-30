# /analyze-with-loupe — library

The `/analyze-with-loupe` slash command lives at `~/.claude/commands/analyze-with-loupe.md`. It is a normal Claude Code command:
`disable-model-invocation: true`, the `Workflow` tool is disallowed, and it uses at most 2 analysis agents plus, in Analyze Mode, one
production agent per video (at most 5 at once). Everything it loads at run time lives here or in the skills below.

## How it is organised: a router, 20 phase skills, section files

The context of a run is its scarcest resource, so nothing is loaded before its step:

- **The command is a router** (about 20 KB): arguments, resume, the loading rules, one line per contract item, the phase map, the labels table and the global Never rules.
- **Phase skills** `~/.claude/skills/awl-*/SKILL.md` (20, `user-invocable: false`, descriptions marked internal) hold the steps, the contract items and the Never rules of one phase
  each, moved verbatim from the old monolithic command, plus a "Read now" list of the exact section files the phase needs and a hand-off that names the next skill.
  Their order is the chain `awl-start` → (Analyze) `awl-analyze-prepare` → `awl-analyze-study` → `awl-create-plan` | `awl-recreate-plan` | `awl-free-plan` (Free; without references straight from `awl-analyze-prepare`) → `awl-asset-plan` → `awl-analyze-produce`
  → `awl-wrapup`, or (Edit) `awl-start` → `awl-edit` → `awl-wrapup`; the per-video loop is `awl-plan-video` → `awl-write-request` → `awl-inputs` → `awl-precheck` → `awl-submit` →
  `awl-postprocess` → `awl-qc` → `awl-record`; `awl-feedback` and `awl-model-guide` are called when needed. `state.json → next_skill` makes every phase boundary resumable.
- **Born from the library at `C:/Users/Glaresquare1/.claude/analyze-then-pick` on 2026-10-20** (a copy under new names, then changed; its log entries before that date are
  inherited). What this command changes: the toolkit only gathers (contract item 25: `sync-check`, `scale`, `qc`, `conform`, `audio-profile`, the OCR spans, the ledger and the model
  menu return numbers and facts, never a verdict, a label or a refusal; the rules of thumb sit in the references); the QC-fixes choice (item 27, `ask` or `auto`); pilot first (item
  26); a stalled-agent recovery, a request freeze and a planner contract (produce items 28–30); one uploads schema (`T uploads`), the generated agent contract (`T contract`), gridded
  frames (`T frames --grid`), `T hf-put --capture`; Loupe's answers carry the sample's title and origin, hint fields cut at a sentence, a busy fallback, the keeper's state readable by
  `status` and `doctor`; the preview is the 720×1280 burn, and no product clause teaches a faded product.
- **Section files.** Every long document (the references, the Higgsfield guide, every model guide) is an index file plus a folder of section files; the section numbers (`§4b.1c`,
  `§2.14`, `guide §3.14`) are unchanged. A skill reads the sections it names, never a whole document.
- **Production agents** get a contract that invokes the per-video skills (`awl-inputs`, `awl-submit`, `awl-postprocess`, `awl-qc`, `awl-record`); they never read the command file.

```
analyze-with-loupe/
├── learning-log.md                 one section per change of substance: patterns, root causes, changes, hypotheses to test; the section of 2026-10-13 records the retirement of the feedback ledger and holds the map from every `CE-nnn` case label to the section that now holds its lesson (never read by a run)
├── config.json                     paths (python, runs), fixed output (9:16, 720p), analysis defaults, Edit Mode cost gate, CapCut store + template
├── (flag record)                   lives in Loupe (`~/.claude/loupe`, `http://127.0.0.1:8787`), not in this folder: written only by `awl.py caught-flag`, never read by a run
├── models/
│   ├── index.json                  model id → guide, capabilities, 9:16/720p parameter mapping, continuation (max per generation + how clips join). 40 KB: never Read whole; `awl.py model-menu` builds the menu, `awl.py model-entry --id <id>` prints one entry
│   ├── _TEMPLATE.md                structure every model guide follows (write a new guide as one file on it, then `docs_tool.py split`)
│   ├── _generic-fallback.md        used for a live model that has no guide yet (small, read whole)
│   ├── <guide>.md                  the guide's INDEX: front matter, scope, and the table of its sections
│   └── <guide>/NNN_<id>_<slug>.md  the guide's section files; only the selected model's, and only the sections a step names, are loaded
├── higgsfield/
│   ├── higgsfield-mcp.md           index of the MCP guide; sections in higgsfield-mcp/ (tools, uploads, roles, Elements, jobs, costs, errors, 9:16/720p)
│   ├── catalog-snapshot-<date>.json  models_explore snapshot used when the guides were written
│   └── first-party/                verbatim Higgsfield recipes (ad-multiplier edit contract, media pipeline, Genjutsu); read on demand
├── reference/                      each <name>.md is an index; the sections are in <name>/
│   ├── analysis-protocol           Analyze Mode: reading 5 fps storyboards + timelines, cards, lenses, families, directions, delegation; the user's examples → house approach (§9)
│   ├── generation-system           dependency chain, work-backward plan, state ledger, multi-generation videos (§3b), reference inserts (§3c), integration analysis, swap / contents / natural placement (§4b, with the spot-feasibility checks §4b.1c, and §4b.5: the original video is the only video reference, spot and size in the prompt), anti-slop gate, physics (§5b), source fidelity and audio-locked timing (§5c, with preparing the source §5c.2b), counts / openings / permanence (§5d), model translation, pre/post QC, brief
│   ├── anomaly-catalog             logical and physical anomaly classes (counts, openings and use, preparation, persistent states, object permanence, liquids, scale with the size reckoning and standard-size table, label legibility (a pixel budget), identity reference hygiene, body mechanics, labels, hand-offs, environment, timing, stylised rendering, solidity and collision, blend with the eleven-sign paste test): the affordance sheet per product, ledger entries, prompt lines, QC checkpoints and verdicts
│   ├── creative-direction          the creative team the pipeline plays (growth creative, mass-cognition engineer, trend analyst, creative director, performance editor): goal model, audience model, trend read, the craft sheet and the copy test (Create takes a reference's craft, never its subject), scored concept seeds, the sharpness gate, hook/payoff craft, creative QC notes
│   ├── brand-guardrails            the client's rules from the assets folder (no gore, count limits, no competitor brands, no ambassador likeness, claims, disclaimers): extraction, rule kinds, the per-reference guardrail audit (core → dismiss; peripheral → pick and edit: count reduced, competitor marks removed never blurred, faces swapped, captions rewritten), Create invariants, Edit Mode hits, QC
│   ├── text-and-format             mode-dependent text policy (Analyze: clean plate + CapCut text layers), text removal, fixed 9:16 / 720p rules
│   ├── capcut-assembly             Analyze Mode's editable master: one CapCut project per video (DD_Mon_YYYY_vNN) with the inserts and text layers (house text style: System, size 10, or 11 when the video has only a little text, the user's locked preset); save, repair, preview
│   ├── production-agents           Analyze Mode (Recreate / Create / Free): one background agent per video (max 5 at once), its prompt (which invokes the per-video skills), contract and result.json
│   ├── assets-and-substitution     user-supplied assets only (analyze: dropped once; edit: per operation), contents samples, understanding + registry, substitution map, reference strategy per model
│   ├── effort                      the effort level (item 33): the start question with the five levels, and what never changes (the judges, coverage, the floors)
│   └── voiceover                   the own voiceover (item 31): the state and the take files, the choice at the start (method, voice, language, style), writing the lines, generating and recording a take, on-camera or off-screen, the request by method (native driving audio, the lipsync scene and its `sync_so` pass, overlay), the upload, after the generation (align, mix, sync pass, the fallback), the CapCut voice track, QC, credits and honesty
├── pipeline/preprocessing.md       the recorded local pipeline (FFmpeg-first) and sampling policy (~5 fps adaptive)
├── scripts/awl.py                  deterministic local toolkit (inventory, prep, frames, last-frame, strip-inserts, audio-profile, fetch-audio, conform, concat seams, qc with 30 fps --dense checkpoint sheets, scale (size reckoning: expected vs observed product size), sync-check, locked ledger/state, CapCut name/prep/repair, model-menu / model-entry, transfers; doc-text extracts PDFs with pypdf and flags an image-only one; seams (the per-frame luma and frame difference around a cut point, also printed by strip-inserts); status, doctor, lint-run and cost-report (gather-only inspection of a run and of this machine; status and doctor read the keeper's state); uploads (one schema per video, a loud merge into state.json); contract (the agent contract from the canonical prompt and state.json); frames --grid (gridded copies in source pixel coordinates); hf-put --capture (upload from the hook's capture); voiceover (outdir: the run's folder the ElevenLabs MCP may write to; record: a take into the run with its measured phrases, pauses and spoken words; align: where a take lies in a file's sound, with a plot; mix: the take laid over a picture, with the CapCut voice track); effort (the run's effort level: show it or set a level and custom values held to the floors; prep-all and the produce phase read it, never QC; a new run's level is empty until stored, and effort and prep-all stop on it); every `--run` takes a full path, a bare run name or a stamp prefix)
├── scripts/check_all.py            every check in one table (`check-all.cmd` / `.ps1` / `.sh`): the suites below, `docs_tool.py check`, Loupe's own tests; exit 1 on a failure
├── tests/                          the suites (`python tests/run_all.py`, `--real` adds the real-data suite): t01 the structure (docs check, skills, hand-offs, `T` commands, the Loupe and audio wiring, the forbidden names), t02 the toolkit on scratch fixtures, t03 the Loupe coupling against a Loupe server in the test process with a fake keeper, t04 real data read-only, t05 the four hooks (the input guard too) and the upload capture; tests/rehearsal.py drives the whole golden path in a temp copy
├── scripts/docs_tool.py            the section tool: `split` / `join` / `index` for the documents, `check` (indexes, section files, skills, paths, § citations) and `budget` (what each skill and the command load)
└── runs/<stamp>-<slug>/            one folder per run (state.json makes runs resumable: /analyze-with-loupe resume <run-dir>; `next_skill` names the phase to continue)

~/.claude/skills/awl-*/SKILL.md     the 20 phase skills (see above)
~/.claude/commands/analyze-with-loupe.md   the router
```

## Case labels (`CE-nnn`)
`CE-nnn` in the references, the model guides and the skills are case labels. Each marks a lesson learned from a
video that went wrong (a user report or an agent's regenerate reason, 2026-10-03 to 2026-10-13); the lesson is
written out where the label stands, as a kind (what to achieve, what to avoid) with its miss, cause, corrected
wording and what worked. There is no error ledger: `caught_errors.md` and `awl.py caught-error` were retired on
2026-10-13 so that a run reads rules, not a growing pile of past errors. The last version of that file is in
this folder's git history (`git log --follow -- analyze-with-loupe/caught_errors.md`, last commit `aba83d3`), and
`learning-log.md` maps every label to the section that holds its lesson. A new lesson goes, generalised, straight into the
section that owns it (on the user's yes).

## The flag record and the QC samples (Loupe)
Loupe is the pipeline's web app (`~/.claude/loupe`, run by `python loupe.py serve`, or started by `awl.py loupe ensure` when a command needs it;
localhost only, admin passphrase for the person, API keys for agents). It is started explicitly when a run is created (and again on resume and before the production agents are spawned): `awl.py loupe ensure` starts it detached when it is down, prints `library_size` (the number of QC samples the keeper is fed from), boots the keeper or brings it up to date (`keeper.state`: `in_sync`, `booted`, `synced`, `syncing` (the sync took longer than the 25 s `awl.py` waits, `AWL_KEEPER_SYNC_WAIT`, and goes on inside Loupe: the first consult waits for it), `busy` (another keeper call held Loupe's lock over 20 s: nothing was synced, the first consult brings the keeper up to date) or `failed`; an empty library has no keeper (`keeper: null`); Loupe's own watcher keeps it current after later edits) and the run records `state.json → loupe` (`up` or `down`; none = up). If it cannot start, the run goes on: QC without samples (the verdict says so), flags wait in Loupe's outbox. The production agents' contract carries the same "Loupe" line. The keeper may ask Loupe for what it cannot judge instead of guessing (the video's plan, a frame of the video under QC, the product registry row, where a sample came from): Loupe fetches it read-only from the run into a folder of its own, in at most two rounds of three requests, and the keeper answers again; nothing fetched ever enters the library, and the library stays its only memory of past misses. A question only the QC agent can answer comes back as `needs_unmet` and is answered once with `--note`.
It holds two things:
- **The flag record:** every prompt and video Higgsfield flagged, refused, withheld or rerouted. `awl.py caught-flag add` gathers the video, the
  request, every input with its file, thumbnail and file facts (sha1, size, dimensions, printed words), whether the same file went through earlier
  runs, and the raw answer the Higgsfield hook saved, and takes the agent's trigger, tags, asset, prompt words and video part. Loupe searches with
  `field:value` operators, groups by trigger, asset, video, kind, run, model, cause, status or month, and shows the evidence next to each flag.
  No step of a run and no agent reads it; what a flag teaches is written into the references as a rule when the user asks for it.
- **Generation misses:** the admin picks a run and a video in Loupe, marks the second of the miss with an arrow, circle or box and a note, then picks
  the fixed version (either side can also be the original video the generation was made from, or a take of another video or run) and the same
  moment of it. Loupe saves one image: the frames side by side, each tagged with its source, and a zoom below each frame marked with a circle,
  arrow or box. Only the QC phase reads them: `awl.py qc-consult` asks the QC keeper (one separate read-only Claude session that holds the whole
  sample library and never sees a run, with a short reading of every sample's picture that Loupe had a fresh session make once by opening it, the full reading kept as JSON in
  Loupe's data and redone only for a new or changed sample; its context is kept small: after a session starts only changed lines are sent, and a session
  is replaced after 30 turns or 150 000 characters) which samples apply to the video under QC; `qc-brief` returns the matching samples with no model call. The answer's `relevant[]` carries
  the sample's words (`title`, `details`, `correct_note`, `idea`, `better`, `missed`), where it came from (`model`, `run`, `video`, `t_wrong`, `kinds`), the composite's path and the
  keeper's `why`, `check` and `wrong_pattern`, every field whole or cut at a sentence or word end; `needs_unmet` lists what Loupe could not fetch and, as `kind: more`, requests left over after the two rounds; when another keeper call runs longer
  than the lock wait the answer comes from the brief with `mode: busy`. `plan-hints` fields are cut the same way and `held_back_why` says why a hint was set aside. A sample marked `prompts`
  (`pair`, `wrong` or `fixed`) keeps in Loupe, each named by what it is, the flawed version's prompt (the prompt of each generation its frames called WRONG come from) and the correct version's prompt (each generation its frames called RIGHT come from, from either video), only the boxes it has frames for (frames called RIGHT only: the correct version's alone), or an Examples sample's one example box (the generations of its one video its Example frames come from; a suggestion of what could have changed or how it could have been done another way, neither a bad generation nor a correct one: `prompt_roles`, `prompt_sides`); a box holds no other generation, and which generation made a frame is read from the join record `awl.py concat` writes (`<out>.join.json`); with the admin's `prompt_note`; lists, answers and hints carry only the marker
  and the note, and `awl.py sample-prompts --id S12 --run RUN` writes them whole to `RUN/40-briefs/samples/S12-prompts.md` for a sample the agent judged relevant (X2 for an applied hint, QC for a
  diagnosed cause; a take joined from several generations gives the prompt of each generation the sample's frames come from, each under
  `Generation k of n · clip · request` and the line naming the frames it is responsible for, as the sample's image tags them, and the seconds it generated): the agent reads and judges what changed, nothing is compared in code, nothing of them is pasted. `status`
  and `doctor` read the keeper's state (in sync, turns, library version, how many samples have a current reading) through the qc key.
  **Coupled with Loupe (since 2026-10-22):** `loupe ensure` reports `keeper.understanding` and a `reading_note` while new or changed samples are being read;
  `plan-hints` passes on `held_back_why`, `library_read`, each hint's `reading_path` (read only when the trigger match is unclear) and the keeper's
  `needs_unmet` with an `unmet_rule` (answer from the plan and ask once more with `--note`); `qc-consult` adds a `reading_rule` (each relevant sample's
  `reading` and `reading_path`: view the picture first), a `not_read_rule` and a `gaps_rule`: what the library does not cover and any need still unmet go
  to `result.json → keeper_gaps`, and the wrap-up reports them for the admin (Loupe's Keeper page lists them too). The judge's `flags` (what is missing, contradictory or ambiguous in a sample's record) come with a `flags_rule`: QC writes each into `keeper_gaps` (`flag S12: ...`), planning into the Sample hints block, the template step into the Judge's template block. A prompts file is the sample's whole record from Loupe: its generation miss, the admin's words tied to the frames, every frame with its video, generation, marks and the prompt label that made it, every prompt under its label. A declined preset notice is stored once
  in `state.json → higgsfield.declined_preset_id`, so every request carries it and `lint-run` knows it.
  Loupe also ships the same library as MCP tools (`mcp_server.py`: `qc_search`, `qc_get_sample`, `qc_brief`, `qc_consult`); that server is not registered in `~/.claude.json`, so the pipeline's agents reach the library only through `awl.py qc-consult`, `qc-brief` and `plan-hints`.

The judge writes the prompt template (the user, 2026-10-28). Loupe's keeper is the judge and runs on Opus 5.5; a Haiku data collector only
describes each sample's picture once and gives no verdict. X1–X4 come first: the plan, the pattern card, the pipeline's own request
(the checked draft, with its must-carry lines in `40-briefs/video-NN-musts.md`) and the pre-generation check. Then, at X4b, the whole checked brief
goes to the judge (`awl.py prompt-template --structure-file RUN/50-requests/video-NN-pattern.md`: the judge brief `40-briefs/video-NN-judge-brief.md`,
the draft's prompt, parameters and inputs, the must-carry lines and the video model's entry); the judge names the samples whose saved prompts it needs,
Loupe sends the saved prompts of each (every box its frames speak through) whole from its record, and the judge answers the final prompt with its basis (what worked, what failed, where it
carries it), notes and changes. `awl.py template-apply` puts that prompt in the request word for word (the draft kept as `video-NN-request.draft.json`)
and reports the must-carry lines missing, the slots left and the length; nothing rewrites the judge's prompt: a missing line or a length over the
limit is asked of the judge once more, and only then is a line added word for word or the checked draft kept. The judge is not asked again before
generation, and a regeneration takes the judge's `template_fix` in place of the part it names. A template asked while another keeper call runs is asked
again up to 3 times (`AWL_TEMPLATE_BUSY_RETRIES`). After generation QC consults the judge once its first pass has caught what it caught, and the
consult carries by itself the prompt the video was generated from (`--attempt` picks the request) with that request's video model and parameters,
the template and the brief (`evidence_sent`); both kinds of consult send the generation video model's entry of `models/index.json`, and the judge
weighs each sample by the model that generated it;
the answer adds `cause` and `template_fix`, kept in `result.json → judge` for the user's review. Before any QC or planning answer is final Loupe also
hands the judge the saved prompts of every sample it cites (`prompts_judged`), and `qc-consult` writes them for the agent (`prompts_files`).
`plan-hints` stays for older runs; X2 no longer calls it.

Kept in step with Loupe (2026-10-28): `qc-consult`, `prompt-template` and `plan-hints` wait up to 1080 s (`AWL_CONSULT_TIMEOUT`), since Loupe may
wait 120 s for a running keeper call and then make up to six keeper calls of up to 150 s each (a 209 s consult was cut at the old 190 s and its
answer lost; a Bash call that outlasts its own timeout goes on in the background);
`caught-flag reconcile` lists the unclaimed flag captures and only counts the `media_upload` answers the hook keeps for `hf-put`
(`unclaimed_upload_answers`: 29 of the newest 30 captures were uploads, which hid older flags); `--capture` finds a capture at any age (the
old lookup saw the newest 200); a flag queued while Loupe failed carries a log note with its provisional `CF-Q…` id, so `caught-flag set --id
CF-Q…` still finds it after Loupe records it under its own number.

Four hooks in `~/.claude/settings.json` support the pipeline without adding to any agent's context: `hooks/atp_flag_watch.py` (PostToolUse of the
Higgsfield generation tools and `media_upload`: saves a flag-like answer to Loupe as a capture the moment it returns and reminds the agent to record the flag first; every
upload answer is kept as a capture too, so `awl.py hf-put --capture <id>` uploads without the presigned URL ever passing through the agent),
`hooks/atp_resume_note.py` (SessionStart after a compaction or resume: names the run in progress and its `next_skill`) and `hooks/atp_read_guard.py`
(PreToolUse of Read: refuses a whole-file read of `awl.py`, `models/index.json`, the catalog snapshot and the backups; a read with an offset/limit
passes) and `hooks/awl_input_guard.py` (PreToolUse of Bash, PowerShell, Write and Edit: an open run's references, edit sources and examples
stay read-only, item 34). Build prompt for the app: `Documents/prompts/loupe.txt`.

## The Free sub-mode (contract item 17, A6f)
The third Analyze sub-mode: the user's own requirement, written at the start and kept verbatim in `RUN/00-inventory/requirement.md`, decides what the videos achieve and
how (how many, what happens, the product and its use, references edited or re-made or only studied, length, text, sound), with references analysed first (A1–A5, then
`awl-free-plan`) or from the requirement and the assets alone (`awl-analyze-prepare` hands off straight to `awl-free-plan`). The free plan (`20-analysis/free-plan.md`)
labels every line [U], [E] or [I], lists the past misses that touch the requirement (`T qc-brief` per product, no model call), is confirmed by the user once, and gives
every video its kind (`state.json → videos_kind`, `recreate` or `create`), which selects the branch of every per-video step. The pipeline keeps the hard rules, the locked
model's own prompting and official examples (X2), the plan discipline, the QC stack, Loupe's hints and consults, the CapCut assembly and the deliverables.

## QC fixes (contract item 27, every Analyze sub-mode), pilot first (26), the stalled agent, the request freeze and the planner contract (28–30)
At the start of a Recreate, Create or Free run the user chooses `ask` (from the first video on, a fix generation after a QC finding waits for the user's yes: the production agent
prepares the corrected request and stops with a `fix_proposal`, the main session asks with one question per waiting video, `Fix it` / `Keep this take` / `Fix it, and stop asking`)
or `auto` (the agent submits its one diagnosed regeneration itself) or `off` (the user, 2026-10-28: no QC agent after a video's first generation at all; each video is
generated once, assembled and delivered unchecked, the pilot shows only its technical outcome, and the user says what to fix after the wrap-up through its feedback
question); `state.json → qc_fixes`, the contract's "QC fixes" line. Local post-fixes and CapCut fixes never ask; Edit
Mode reviews every attempt anyway. With more than four videos the first one runs through its QC before the rest are planned (26). A production agent whose output folder has not
changed for 20 minutes while its lane holds a submitted job is continued by its id, never relaunched blindly (28); a request file is frozen once its agent is spawned and `T lint-run`
reports one edited after its ledger entry (29); a planner fork writes only its own video's files and a status note (30).

## Audio ingest (contract item 24)
At the start the user chooses, once per run, whether the videos' audio is processed as text: **Whisper speech-to-text** (faster-whisper `small`, int8 on the CPU, about real time per
video plus about 8 s of model load; the transcript is written once per video as `10-media/<V>/transcript.json` and `.txt` and feeds the cards, the sync anchors of spoken lines, the
caption timing and the sound profile's speech share) or **frames only** (no speech-to-text, no transcript file; every speech field of every card, plan and brief says `audio not
ingested`, never `no speech`: what was said is unknown, not absent). The answer is `state.json → audio_ingest` (`whisper` | `frames-only`) and the only source of the choice: no
script or skill picks a default, `T prep-all` stops without it, `T prep-video` takes `--audio-ingest`, `T captions --from-speech` refuses in a frames-only run. Whatever needs the
audio file itself (the original audio restored under the picture, loudness and silences, `T audio-profile`, `T sync-check`) runs in both modes.

## Own voiceover (contract item 31)
In **Create**, before the model menu, the user picks whether the videos speak with their own ElevenLabs voiceover and how the take meets the picture (the
**method**, `state.json → voiceover.method`):
- **native**: the take is the generation's driving audio. Wan 3.0 and Wan 3.0 Prime (reference mode: the character and product images plus the take as Audio 1)
  and Wan 2.7 (a start frame plus the take) build the video around it; the lips and the action timing follow it, and the generated file's sound is the take.
  Up to 15 s of voice per generation; one generation, nothing edited afterwards.
- **lipsync**: any model generates the speaking scene (the take's words verbatim as dialogue), then Higgsfield's Sync Lipsync 3 (`sync_so`, the clip plus the
  take, `sync_mode: silence`) re-syncs the mouth to the exact take: one extra generation per voiced video, through the ledger as `--video NN-sync`.
- **overlay**: any model generates the video without dialogue (narration, a product review, a story told over the pictures); `T voiceover mix` lays the take
  over the picture for the deliverable and the CapCut project carries it on its own track.
- or "No, the model's own audio", as in every run.

With native the driving models lead the model menu; the model is still locked for the run and never suggested after the pick. After the paths, the
ElevenLabs tools are loaded, the subscription and the models are read, the user's whole voice library is printed, and one question asks the **voice** (three
from the list, the user's own voiceover files, or any name, voice id or `character = voice` pairs), the **language** and an extra **preference** for accent,
dialect or delivery (the user's examples: a Scottish accent, Kosovar Albanian in the Gheg dialect). **Free** uses one only when the user's requirement asks for
it (the pipeline never offers it); what the requirement leaves open is asked inside the free plan's one confirmation. Never in Recreate or Edit Mode, whose
original audio returns (item 19).

Per video: X1 writes the lines (the dialect in the words, an accent tag, emotion tags, the length budget) and makes one take per script with the MCP's
`text_to_speech` into the folder `T voiceover outdir` prints (the MCP writes only under `ELEVENLABS_MCP_BASE_PATH`, by default the Desktop); `T voiceover record`
copies it into the run (`30-assets/voiceover/video-NN[-cK]-aK.mp3` with a sidecar: the script as sent, the spoken words, the phrases and pauses), and the beats
and the duration are re-timed to it. X2 builds the request by method (`voiceover.md` §6), X3 uploads the take (native, lipsync), X8 runs step 5b once the
picture passed (`T voiceover align`: near 1 at near 0 means the file's sound is the take; the sync pass; `T voiceover mix`), X9 checks the soundtrack, the lips
at three phrase starts and one pause, and the face after a sync pass, and the wrap-up reports the method, the voice, the takes, the sync passes and the credits.
No agent listens: pronunciation, accent and dialect are always "not checked (listen)", and a language outside the model's official list is named. Unverified
on Higgsfield as of 2026-10-26: how faithfully a driving audio is kept and followed by the lips (both Wan guides list exact lip sync as a weakness) and whether
`sync_so` keeps 720×1280 and the take as its soundtrack; the pilot video measures both, and X8 measures them for every video.

## Memes in Create (contract item 32)
At the start of a Create run, beside the voiceover method, the user picks **Include memes** (as the references do: a meme, a reaction clip, a
film or TV snippet or another original clip the style calls for is cut from the references with its sound, or taken from the user's files,
and placed between the generated parts in CapCut) or **No memes: pure generation** (every second of every video is generated: no meme clip,
meme still, reaction clip, screen recording, snippet or meme sound of any kind; where a reference uses a meme, the new video plays that beat in
its own generated scene, never with a generated copy of the meme). `state.json → memes` (`include` | `none`); a Create run without the key
includes them, as its plans were made. The choice wins over the house approach and reaches the concept seeds, the asset plan (with `none` the
whole length is generated and counts toward generations and the 30 s permission), the insert plan, X4, the CapCut project, QC (an insert found
in a `none` video is removed) and the agent contract's "Memes" line. Recreate keeps its references' own inserts; Free takes the choice from
its requirement (`awl-free-plan` step 2c).

## Effort level (contract item 33)
At the start of every run, in both modes, the user picks **Low**, **Medium**, **High**, **XHigh** or **Max** (or their own numbers). The level
sets how densely the references are sampled at analysis (2, 3, 4, 5, 5 frames per second; 6, 8, 10, 10, 10 around motion and in the first
second; 4, 5, 6, 8, 8 motion peaks of ±0.5 s each; 2, 4, 6, 8 or no cap close-ups per reference), how many production agents run at once
(2, 3, 4, 5, 5) and from how many videos the pilot runs first (2, 3, 5, 5, 5). Max is the pipeline's settings before the choice existed,
and a run without the key keeps them. The question is asked in plain chat with all five levels numbered (the user, 2026-10-27: "they need
to be 5"; a question dialog holds at most four options and hid XHigh behind Other). `T new-run` writes the level empty (`null`), and
`T effort` and `T prep-all` stop until the user's answer is stored, so a skipped question never runs at rates nobody picked; a run made
before item 33 has no key and keeps Max without being asked. `T effort` stores it in `state.json → effort` and holds custom values to the
floors; `T prep-all` and the produce phase read it. **QC and Loupe are never part of it** (the user, 2026-10-27: the judges stay stable): QC renders, views and consults
exactly as always, at every level. What never changes (`reference/effort.md` §2): every second of every reference is sampled, every cut keeps
its last and first frame, the first second and the motion peaks are dense, no frame or video is made smaller, and a produced video's own
source is densified in X1 as always.

## The user's folders are read-only (contract item 34)
Nothing in the references, assets, examples or edit-source folders is moved, renamed, deleted or overwritten, by the main session or any
agent (the user, 2026-10-27, after the 15 videos of a references folder went to the Recycle Bin in one batch while two runs were reading
it): a file needed in the run folder or anywhere else is copied. Only the toolkit adds its own derived folders there, as before
(`files_audio/` and `videos_without_audio/` from `T split-audio`, Edit Mode's `final/`). `hooks/awl_input_guard.py` (PreToolUse of Bash,
PowerShell, Write, Edit, MultiEdit and NotebookEdit) refuses a move, rename, delete or write (`rm`, `mv`, `Remove-Item`, `Move-Item`,
`Rename-Item`, `del`, `find -delete`, a .NET or Recycle Bin delete, `shutil.move`, `os.remove`; a copy, redirection, `Set-Content` or
encoder output landing there; a delete of a folder that holds one) inside the references, edit-source or examples folders of every run of
the library that is not done or abandoned and changed in the last 7 days. It reads verbs at command position only, through shell and
PowerShell variables, `for` loops, nested shells (`bash -c`, `cmd /c`, `powershell -Command`) and line continuations; in Python (a
heredoc or here-string fed to an interpreter, `-c`, a script it runs) a delete, move or write call aimed at a reference path or at a name
that holds one. A heredoc that is only data (a note written with `cat`) is never read as commands, and a verb whose target is an unset
variable passes. Copies, reads, the toolkit's own calls and the run folder pass; the assets folders stay open to the user's own curation.
It fails open, and the refusal tells the agent to copy instead. It reads the runs' `state.json` with FILE_SHARE_DELETE, and the toolkit's
writes retry an atomic replace a reader held (on Windows a reader can make `os.replace` fail: measured 145 of 300 without the retry, 0 with
it).

## Orientation
The output keeps the original's perspective (the user, 2026-10-27): a source is never flipped, in any mode. A front-camera selfie keeps its
own reversed print and signs as the original shows them, while the client's product label reads correctly; only an identity photo that is
itself a mirrored selfie is turned to the person's true face (`generation-system.md` §5c.2b; CE-030's flip of the source is retired).

## Context budget
What every run loads stays lean (the user, 2026-10-26: no context rot in the pipeline's agents). A feature that only some runs use keeps its
details in a section that a skill's Read-now list names under a condition (the own voiceover: `reference/voiceover/`, read only by a run that
has one); the always-loaded skills, the router and the agent contract carry a one- or two-line pointer. Toolkit answers print a summary and
leave long lists in their JSON files (`T voiceover align` → `vo-align.json`). Measured against the commit before items 31–32: a production
agent's always-loaded text grew by about 4 % (4.7 KB of 112 KB), the main session's for a Create run by about 8 % (13.8 KB).

## How a run uses the documentation
1. The command invokes `awl-start`: it prints the model menu with `awl.py model-menu`. The menu lists **every** available model: `models/index.json` merged with the
   live `models_explore` catalog. Pinned models come first (`menu.pinned`: Seedance 2.5, Wan 3.0 Prime), then `menu.order`. Change the pins or the order there; the command needs no change.
2. The picked model is **locked for the whole run**. `awl.py model-entry --id <model>` prints its index entry and its guide folder; each per-video skill then reads **only the
   sections of that guide it names** (`awl-model-guide` has the table: §2.4 recipes and §4.0 official examples for the request, §5 and §7 for the pre-generation check, …).
3. The guide's **§4.0 official examples** become a per-video *pattern card*. Prompts are written in the model's proven structure, and parameters come from the guide's §2 recipes plus
   `output_9x16_720p` in the index.
4. Each phase hands off to the next skill and records `next_skill` in `state.json`, so a run can be compacted, resumed or moved to a new session at any phase boundary.

## Editing the pipeline
- **A step or a rule of a phase:** edit that phase's `~/.claude/skills/awl-*/SKILL.md` (the router's labels table says which skill owns which step; a rule that two phases act on is written in both skills).
- **A reference or a guide section:** edit its section file; after adding, renaming or removing one run `python scripts/docs_tool.py index <doc>.md`. Never edit between the index markers by hand.
- After any edit: `python scripts/docs_tool.py check` (it must report 0 errors) and, for a pipeline change, update the build prompt `Documents/prompts/analyze-with-loupe.txt`.
- `python scripts/docs_tool.py budget` shows what each skill weighs; `join <doc>.md` prints a whole document (never in a run).

## Adding a model
1. Confirm it exists: `models_explore {action:"get", model_id:"<id>"}`.
2. Copy `models/_TEMPLATE.md` to `models/<guide-slug>.md` and fill it from **official** sources
   first: provider docs, API reference, prompt guide, model card, paper, first-party examples. Tag
   every claim [OFFICIAL] / [HF] / [SECONDARY] / [INFERRED]. Quote 3–8 official example prompts in
   §4.0 with the patterns they teach. Fill §2.6 (9:16 / 720p mapping) and §3.11 (visible text).
3. Run `python scripts/docs_tool.py split models/<guide-slug>.md` (lossless: it verifies the rejoin) so the guide becomes an index plus section files.
4. Add an entry under `models` in `models/index.json` (copy an existing entry; the fields are
   explained in its `_schema` block), and add its id to `menu.order` where it should appear in the
   menu. Ids that are missing from the order are listed at the end.
5. Nothing in the command or the skills changes. A live model without an index entry still works through
   `_generic-fallback.md`, with a warning.

## Updating a model
- Run `models_explore list` and compare it with `higgsfield/catalog-snapshot-*.json`. On drift,
  update the guide's §2 section files and the index entry, bump `guide_version` and `last_verified` (in the guide index's front matter), and
  save a new snapshot.
- A model that disappears from the live catalog stays in the index with `"status": "retired"` until
  it is removed; the command hides unavailable models.

## Tooling requirements (this machine)
- FFmpeg / ffprobe 9.x (winget Gyan.FFmpeg).
- Python 3.12 with Pillow, NumPy and requests; faster-whisper (models cached: small, base, tiny) and
  rapidocr-onnxruntime are optional but used.
- The Higgsfield MCP server `higgsfield` (OAuth via `/mcp`); the lipsync method uses its `sync_so` model (Sync Lipsync 3), which the model menu never lists.
- For an own voiceover (item 31): the ElevenLabs MCP server `elevenlabs` (the local `elevenlabs-mcp` through `uvx`, user scope, `ELEVENLABS_API_KEY` in its
  environment; `claude mcp add elevenlabs -s user -e ELEVENLABS_API_KEY=<key> -- uvx elevenlabs-mcp`, then a restart). It writes files only under
  `ELEVENLABS_MCP_BASE_PATH` (default: the Desktop). A free ElevenLabs plan carries no commercial licence for the audio.
- CapCut desktop (9.x), the `capcut` MCP server (installed with analyze-stack:
  `~/.claude/analyze-stack/tools/mcp/capcut-mcp`, template draft `_analyze-stack-template`), and
  capcut-cli 0.25 (`capcut` on PATH via npm) for registration, timeline sync, lint and proxy
  previews. CapCut must be closed while a project is written.

Details: `pipeline/preprocessing.md`.
