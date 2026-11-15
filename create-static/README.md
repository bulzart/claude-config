# /create-static — library

The `/create-static` slash command lives at `~/.claude/commands/create-static.md`. It makes narrated still-image videos ("Static"): it analyses a folder of reference videos, locks a niche family, a visual style and a
narrator, then makes new videos on new subjects: the stills (OpenAI Images, FLUX 3 Klein on this PC, or the user's own from its prompts), the ElevenLabs narration, an ACE-Step bed, drawn annotations, word-box captions, and
**one CapCut project per video built by ONE composition** (`T capcut-build`). It is a normal command (`disable-model-invocation: true`, the `Workflow` tool disallowed): at most 2 analysis agents and one production agent
per video (at most 5 at once).

## How it is organised: a router, 11 phase skills, section files

- **The command is a router** (about 29 KB): arguments, resume / more / clone, the loading rules, the contract items that apply (their numbers are stable labels the skills and references cite), the phase map and the global Never rules.
- **Phase skills** `~/.claude/skills/cs-*/SKILL.md` (11, `user-invocable: false`): `cs-start` → `cs-prepare` → `cs-study` → `cs-plan` → `cs-produce` (which runs `cs-sound` for every video and spawns one agent per video that runs
  `cs-images` → `cs-edit` → `cs-record`) → `cs-wrapup`; `cs-feedback` when a delivered video is reported as wrong. `state.json → next_skill` makes every phase boundary resumable; `RUN/todo.md` (item 38) says where inside a phase the work stood.
- **Section files** (`reference/<name>/`, index `reference/<name>.md`, rebuilt by `scripts/docs_tool.py index`): `static` (the whole mode), `analysis-protocol`, `creative-direction`, `brand-guardrails`, `assets-and-substitution`,
  `anomaly-catalog`, `production-agents` (the contract of the production agents), and the single file `capcut-build.md` (the build's recipe).
- **What differs from the Static mode of `/analyze-with-loupe`, which this was made from (2026-11-13):** only S4. There the project was made tool by tool (the CapCut MCP for the stills and audio, then one command per feature:
  moves, joins, effects, word-box captions, a font and an entrance per track, labels, repair). Here `T capcut-build` makes it in one process: one `capcut compile`, one write pass over the project's three timeline copies, the
  repair, and a read-back with a `problems` list. Everything else is the same; the mode's rules, quotes and questions were carried over word for word. There is no Higgsfield, Loupe, model menu, effort level, voiceover or memes here.

## The composition (`scripts/cs_compose.py`)

1. The timeline `T slideshow plan` wrote (`40-briefs/video-NN-timeline[-tag].json`) becomes a `capcut compile` spec: the stills on the main track (kept in place behind a 350 KB placeholder), the narration and the bed, each effect
   overlay, drawing clip and sound on its track, the caption texts (one per word and state in the word-box look, with their styles as operations), the labels, the joins as transition operations.
2. After compile, in ONE pass over each copy of the timeline: the real media behind the placeholders, the moves (KFTypeScaleX with the uniform scale on, KFTypePositionX/Y), the overlays' keys, the font on every text, the
   box field, the caption entrance. Then `register`, the media links, `sync-timelines`, `lint` under the machine-wide lock (`config.json → capcut.store_lock`, shared with the other toolkits that write CapCut's index).
3. A read-back against the timeline. Exit 3 when CapCut is running (nothing changed); exit 2 with a sentence for anything the plan must fix first (a refused join, entrance or effect, a missing still, a language the word box
   cannot place: then `--captions plain`).
4. Measured on a real 12.7-minute video (128 stills, 4,413 caption texts, 17 labels, 6 joins): 23 to 27 s, against about 3 minutes for the single commands; the two projects were compared segment by segment (4,560
   segments): equal but for the caption times, exact to the microsecond here and rounded to the millisecond by the SRT route.

## Layout

```
create-static/
├── README.md, config.json          paths (python, runs), CapCut store + template, the Static settings (images, Klein, TTS, music, captions)
├── data/                           capcut-catalogue.{json,md} (what this PC's CapCut draws, measured), compose-template/ (the empty CapCut 9.7 draft the build starts from)
├── fonts/                          the fonts the captions and labels use (kept here so a project keeps finding them)
├── pipeline/preprocessing.md       the media tools and the commands a Static run uses
├── reference/                      section files (above)
├── scripts/                        cs.py (the entry point) + cs_core.py (the toolkit, can be encrypted at rest), cs_compose.py (the composition, can be encrypted at rest),
│                                   cs_crypto_loader.py + cs_source.py (never encrypted: decrypt-on-import, lock/unlock/status), docs_tool.py, check_all.py, image_worker.py, music_worker.py
├── tests/                          t01_compose.py (the build on a synthetic video), t02_library.py (the command, skills, references and toolkit agree), run_all.py
└── runs/                           one folder per run (git-ignored)
```

`python scripts/check_all.py` runs the tests and `docs_tool.py check`. Machine settings are the environment variables of this PC (OPENAI_API_KEY, ELEVEN_API_KEY, AWL_IMAGE_PYTHON, AWL_IMAGE_ROOT, AWL_MUSIC_PYTHON,
AWL_MUSIC_ROOT, AWL_TTS_PYTHON): their names are unchanged. The input guard hook (`~/.claude/hooks/awl_input_guard.py`) protects the references, examples and effects folders of the open runs of this library too (item 34). The SessionStart resume note (`~/.claude/hooks/atp_resume_note.py`) names a run of this library that is in progress after a compaction or a resume, with its next skill and the first `Next:` line of its `todo.md` (item 38; `tests/t03_resume_hook.py`).
Whisper is `medium`, always (item 24: the user, 2026-11-14): no smaller model as a default, a fallback or a speed-up.

**Source encryption** (the user, 2026-11-15: "use encryption at run ... requires a key for files to be read ... not a .exe file"): `cs_core.py` (everything the toolkit does) and
`cs_compose.py` (the CapCut composition) can be stored on disk encrypted at rest (`cs_core.py.enc` instead of `cs_core.py`); the moment anything imports one, `cs_crypto_loader.py`
(a Python import hook installed the instant `cs.py` starts) decrypts it in memory with the key in the `CS_SOURCE_KEY` environment variable and runs it - no decrypted copy ever
touches disk, and without the right key nothing that needs it can run at all. A module whose plain `.py` is sitting there (the normal state while editing it) needs no key at all
and is loaded exactly as Python always loads a file; `~/.claude/.gitignore` lists both protected filenames by name, so an unlocked copy can never be committed by accident.
```
& $PY scripts\cs.py source generate-key     # prints a brand-new key ONCE; save it (a password manager, or setx CS_SOURCE_KEY "<key>") - nothing here writes it anywhere
& $PY scripts\cs.py source lock             # encrypts cs_core.py/cs_compose.py with CS_SOURCE_KEY, deletes the plain copies: this is the state to commit
& $PY scripts\cs.py source unlock [--force] # decrypts them with CS_SOURCE_KEY back into plain, editable .py files
& $PY scripts\cs.py source status           # plain, locked, both (edited since the last lock: re-lock it), or missing
```
Real protection, not security by obscurity: the plain source stays readable while someone is actively maintaining it, but once it is locked, the repository alone - the `.py.enc`
files and this very explanation included - cannot produce a working copy; only the key can. Lock before anything leaves this machine; a leak while still unlocked protects nothing.
`source generate-key|lock|unlock|status` always work with no key at all when nothing is locked, and `source status`/`unlock` always work even when both modules ARE locked and the
key is missing or wrong (that is the one case they exist for) - neither ever needs `cs_core.py` to import successfully first. Any other command needs the real key once `cs_core.py`
is locked: `tests/run_all.py`, `t01_compose.py` and `t02_library.py` exercise the real toolkit directly, so once it is actually locked, running them needs `CS_SOURCE_KEY` set to the
real key first - that is expected, not a failure of the suite. `tests/t04_source_crypto.py` is the one test that never needs the real key: it proves the mechanism itself (and
drives the real `cs.py` entry point) against disposable dummy modules in an isolated copy, never the real source.
