# /analyze-with-loupe — library

The `/analyze-with-loupe` slash command lives at `~/.claude/commands/analyze-with-loupe.md`. It is a normal Claude Code command:
`disable-model-invocation: true`, the `Workflow` tool is disallowed, and it uses at most 2 analysis agents plus, in Analyze Mode, one
production agent per video (at most 5 at once). Everything it loads at run time lives here or in the skills below.

## How it is organised: a router, 20 phase skills, section files

The context of a run is its scarcest resource, so nothing is loaded before its step:

- **The command is a router** (about 13 KB): arguments, resume, the loading rules, one line per contract item, the phase map, the labels table and the global Never rules.
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
│   ├── generation-system           dependency chain, work-backward plan, state ledger, multi-generation videos (§3b), reference inserts (§3c), integration analysis, swap / contents / natural placement (§4b, with the spot-feasibility checks §4b.1c and the size-and-place guide §4b.6), anti-slop gate, physics (§5b), source fidelity and audio-locked timing (§5c, with preparing the source §5c.2b), counts / openings / permanence (§5d), model translation, pre/post QC, brief
│   ├── anomaly-catalog             logical and physical anomaly classes (counts, openings and use, preparation, persistent states, object permanence, liquids, scale with the size reckoning and standard-size table, label legibility (a pixel budget), identity reference hygiene, body mechanics, labels, hand-offs, environment, timing, stylised rendering, solidity and collision, blend with the eleven-sign paste test): the affordance sheet per product, ledger entries, prompt lines, QC checkpoints and verdicts
│   ├── creative-direction          the creative team the pipeline plays (growth creative, mass-cognition engineer, trend analyst, creative director, performance editor): goal model, audience model, trend read, the craft sheet and the copy test (Create takes a reference's craft, never its subject), scored concept seeds, the sharpness gate, hook/payoff craft, creative QC notes
│   ├── brand-guardrails            the client's rules from the assets folder (no gore, count limits, no competitor brands, no ambassador likeness, claims, disclaimers): extraction, rule kinds, the per-reference guardrail audit (core → dismiss; peripheral → pick and edit: count reduced, competitor marks removed never blurred, faces swapped, captions rewritten), Create invariants, Edit Mode hits, QC
│   ├── text-and-format             mode-dependent text policy (Analyze: clean plate + CapCut text layers), text removal, fixed 9:16 / 720p rules
│   ├── capcut-assembly             Analyze Mode's editable master: one CapCut project per video (DD_Mon_YYYY_vNN) with the inserts and text layers (house text style: System, size 10, the user's locked preset); save, repair, preview
│   ├── production-agents           Analyze Mode (Recreate / Create): one background agent per video (max 5 at once), its prompt (which invokes the per-video skills), contract and result.json
│   └── assets-and-substitution     user-supplied assets only (analyze: dropped once; edit: per operation), contents samples, understanding + registry, substitution map, reference strategy per model
├── pipeline/preprocessing.md       the recorded local pipeline (FFmpeg-first) and sampling policy (~5 fps adaptive)
├── scripts/awl.py                  deterministic local toolkit (inventory, prep, frames, last-frame, strip-inserts, audio-profile, fetch-audio, conform, concat seams, qc with 30 fps --dense checkpoint sheets, scale (size reckoning: expected vs observed product size), sync-check, locked ledger/state, CapCut name/prep/repair, model-menu / model-entry, transfers; doc-text extracts PDFs with pypdf and flags an image-only one; seams (the per-frame luma and frame difference around a cut point, also printed by strip-inserts); status, doctor, lint-run and cost-report (gather-only inspection of a run and of this machine; status and doctor read the keeper's state); uploads (one schema per video, a loud merge into state.json); contract (the agent contract from the canonical prompt and state.json); frames --grid (gridded copies in source pixel coordinates); hf-put --capture (upload from the hook's capture); every `--run` takes a full path, a bare run name or a stamp prefix)
├── scripts/check_all.py            every check in one table (`check-all.cmd` / `.ps1` / `.sh`): the suites below, `docs_tool.py check`, Loupe's own tests; exit 1 on a failure
├── tests/                          the suites (`python tests/run_all.py`, `--real` adds the real-data suite): t01 the structure (docs check, skills, hand-offs, `T` commands, the Loupe and audio wiring, the forbidden names), t02 the toolkit on scratch fixtures, t03 the Loupe coupling against a Loupe server in the test process with a fake keeper, t04 real data read-only, t05 the three hooks and the upload capture; tests/rehearsal.py drives the whole golden path in a temp copy
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
localhost only, admin passphrase for the person, API keys for agents). It is started explicitly when a run is created (and again on resume and before the production agents are spawned): `awl.py loupe ensure` starts it detached when it is down, prints `library_size` (the number of QC samples the keeper is fed from), boots the keeper or brings it up to date (`keeper.state`: `in_sync`, `booted`, `synced`, `syncing` (the sync took longer than the 25 s `awl.py` waits, `AWL_KEEPER_SYNC_WAIT`, and goes on inside Loupe: the first consult waits for it), `empty` or `failed`; Loupe's own watcher keeps it current after later edits) and the run records `state.json → loupe` (`up` or `down`; none = up). If it cannot start, the run goes on: QC without samples (the verdict says so), flags wait in Loupe's outbox. The production agents' contract carries the same "Loupe" line. The keeper may ask Loupe for what it cannot judge instead of guessing (the video's plan, a frame of the video under QC, the product registry row, where a sample came from): Loupe fetches it read-only from the run into a folder of its own, in at most two rounds of three requests, and the keeper answers again; nothing fetched ever enters the library, and the library stays its only memory of past misses. A question only the QC agent can answer comes back as `needs_unmet` and is answered once with `--note`.
It holds two things:
- **The flag record:** every prompt and video Higgsfield flagged, refused, withheld or rerouted. `awl.py caught-flag add` gathers the video, the
  request, every input with its file, thumbnail and file facts (sha1, size, dimensions, printed words), whether the same file went through earlier
  runs, and the raw answer the Higgsfield hook saved, and takes the agent's trigger, tags, asset, prompt words and video part. Loupe searches with
  `field:value` operators, groups by trigger, asset, video, kind, run, model, cause, status or month, and shows the evidence next to each flag.
  No step of a run and no agent reads it; what a flag teaches is written into the references as a rule when the user asks for it.
- **Generation misses:** the admin picks a run and a video in Loupe, marks the second of the miss with an arrow, circle or box and a note, then picks
  the fixed version and the same moment of it. Loupe saves one image: the miss on the left, the correct frame on the right, a zoom of the marked
  place below. Only the QC phase reads them: `awl.py qc-consult` asks the QC keeper (one separate read-only Claude session that holds the whole
  sample library and never sees a run) which samples apply to the video under QC; `qc-brief` returns the matching samples with no model call. The answer's `relevant[]` carries
  the sample's words (`title`, `details`, `correct_note`, `idea`, `better`, `missed`), where it came from (`model`, `run`, `video`, `t_wrong`, `kinds`), the composite's path and the
  keeper's `why`, `check` and `wrong_pattern`, every field whole or cut at a sentence end; `needs_unmet` lists only what Loupe could not fetch; when another keeper call runs longer
  than the lock wait the answer comes from the brief with `mode: busy`. `plan-hints` fields are cut the same way and `held_back_why` says why a hint was set aside. `status`
  and `doctor` read the keeper's state (in sync, turns, library version) through the qc key.
  Agents can also reach the same library as MCP tools (`mcp_server.py`: `qc_search`, `qc_get_sample`, `qc_brief`, `qc_consult`).

Three hooks in `~/.claude/settings.json` support the pipeline without adding to any agent's context: `hooks/atp_flag_watch.py` (PostToolUse of the
Higgsfield generation tools and `media_upload`: saves a flag-like answer to Loupe as a capture the moment it returns and reminds the agent to record the flag first; every
upload answer is kept as a capture too, so `awl.py hf-put --capture <id>` uploads without the presigned URL ever passing through the agent),
`hooks/atp_resume_note.py` (SessionStart after a compaction or resume: names the run in progress and its `next_skill`) and `hooks/atp_read_guard.py`
(PreToolUse of Read: refuses a whole-file read of `awl.py`, `models/index.json`, the catalog snapshot and the backups; a read with an offset/limit
passes). Build prompt for the app: `Documents/prompts/loupe.txt`.

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
or `auto` (the agent submits its one diagnosed regeneration itself); `state.json → qc_fixes`, the contract's "QC fixes" line. Local post-fixes and CapCut fixes never ask; Edit
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
- The Higgsfield MCP server `higgsfield` (OAuth via `/mcp`).
- CapCut desktop (9.x), the `capcut` MCP server (installed with analyze-stack:
  `~/.claude/analyze-stack/tools/mcp/capcut-mcp`, template draft `_analyze-stack-template`), and
  capcut-cli 0.25 (`capcut` on PATH via npm) for registration, timeline sync, lint and proxy
  previews. CapCut must be closed while a project is written.

Details: `pipeline/preprocessing.md`.
