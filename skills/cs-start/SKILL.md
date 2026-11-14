---
name: cs-start
description: /create-static phase 1: the references and assets, the images source, CapCut plan, narration model and QC-fixes choices, the setup check, the run. Internal to that command.
user-invocable: false
---

# cs-start — Start: the inputs, the choices, the run

> `CS` = `C:/Users/Bulzart/.claude/create-static` · `PY` = `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` · `T` = `"$PY" "$CS/scripts/cs.py"` (every call prints one JSON object on its last line; run through PowerShell: Git Bash forks fail on this PC) · `RUN` = the run folder `CS/runs/<stamp>-<slug>/`.
> A citation `file.md §id` is a section of `CS/reference/<file>/`; `file.md` itself is only the index. An id that is not a row of the index lives in its nearest parent row.

Phase 1 of `/create-static`. The router (the command) sent you here and passes the command's arguments (`$ARGUMENTS` below) as this skill's args. Nothing else needs to be loaded for this phase.

## Read now

Only these section files for this phase, nothing else unless a step below says so. A section already read in this session is not read again.

- static §0: `CS/reference/static/005_0_the-team-who-works-a-static-run.md` (5.8 KB)
- *when `T static check` reports a part the run needs as not ready:*
  - static §9: `CS/reference/static/090_9_the-static-pc-setup-once-per-pc.md` (12 KB)
- *when the narration model the user picks is not set up (`set_up: false`):*
  - static §6: `CS/reference/static/060_6_the-voice-and-the-bed-a6s-s2.md` (30.5 KB) (its bullet "The models": the set-up procedure)

## 1. Paths and tools

| name | value |
|---|---|
| `CS` | `C:/Users/Bulzart/.claude/create-static` (library root) |
| `PY` | `C:/Users/Bulzart/AppData/Local/Programs/Python/Python312/python.exe` (see `CS/config.json`) |
| `T` | `"$PY" "$CS/scripts/cs.py"`. Every call prints one JSON object on its last line; run through PowerShell |
| References | `CS/reference/<name>/` section files (index: `CS/reference/<name>.md`): `static`, `analysis-protocol`, `creative-direction`, `brand-guardrails`, `assets-and-substitution`, `anomaly-catalog`, `production-agents`, and `capcut-build.md` (one file). Each phase skill lists the sections it needs under "Read now" |
| CapCut | capcut-cli `capcut` on the PATH (the build calls it) and CapCut's drafts store and the empty template in `CS/config.json → capcut` and `CS/data/compose-template`. The project of every video is built by ONE command, `T capcut-build` (item 39, `cs-edit`); no CapCut MCP tool is used in this command |
| Run folder | created by `T new-run` under `CS/runs/<stamp>-<slug>/` (00-inventory, 10-media, 20-analysis, 30-assets, 40-briefs, 50-requests, 60-outputs, logs, state.json) |

## 2. Start (the router already handled `resume`, `more`, `clone` and reported-video feedback)

2. **This command makes Static runs only** (item 36): narrated still-image videos in the references' style on a new subject: the images by the OpenAI Images API
   with the user's key, by FLUX 3 Klein on this PC, or by the user from my prompts; the voice by ElevenLabs on the user's key, in the model they pick, in the language they pick
   per video; CapCut, one composition per video. There is no mode question. First read static §0 and, from here to the run's wrap-up, work as that team (the user,
   2026-11-06: "you're youtube long and short content specialist, sociology thinking and human behaviour expert ... in order to boost and
   hype him but also to be in accordance with what we're trying to achieve"): a YouTube short- and long-form strategist, storyteller,
   sociologist and human-behaviour expert, attention psychologist, fact-checker, art director and editor, ambitious for the best video and
   disciplined by the references' data and the hard rules. The images come from the OpenAI model in `config.json → static.images`, from FLUX 3 Klein on this PC
   (`config.json → static.klein`), or from the user; the audio question is not asked (`audio_ingest=whisper`) and there is no effort level: every reference is
   sampled at 2 fps (the user, 2026-11-07: "remove the effort idea completely (on static mode), just do 2fps when on static mode"). The
   run is one channel (static §10): its niche and its visual style are the user's picks at A5, after the analysis, and its narrator at
   A6s; nothing religious or superstitious ever (static §11). The references' real YouTube titles come from their file names
   (`<channel>_<title>_<YouTube id>`), or from a `context.txt` with a `thumbnails` folder when the references folder holds one: they are
   studied (A1, static §12), and every video gets its own YouTube title and thumbnail.
5. **Inputs.** Take what `$ARGUMENTS` already gives (`<references-folder> assets <asset files/folders…> [examples <folder>] [effects <folder> | no-effects]
   [images api|klein|prompts] [capcut free|pro] [tts-model <id>] [qc-fixes ask|auto|off]`) and ask in plain chat, in **one** message, only for what is
   missing. Then stop and wait. Static needs the references folder and the assets (the characters as photos and/or descriptions: a text file each, or words in
   the message; usually no product), and offers the optional **examples folder** and **an effects folder (optional;** the user, 2026-11-06: "a
   folder of effects (optional) that can have: sound effects, and green screen transitions"**)**:
   *"An effects folder is optional: sound effects, green-screen transitions, overlays (light leaks, flashes, glows).
   I measure every file and use what fits the references' edit; 'none' skips it. Your folder is read only: files are copied, never moved."*
   An archive in it (.zip, .rar) is listed and not unpacked: say once that its files are used only once unpacked into a folder.
   Say in the message: *"Drop or paste the paths. I will use only these as your assets and pick from them for each video on my own. Examples are optional:
   I study them for how you make your videos and never use them as assets."* The user may answer "no assets" for a project that needs none (item 14: the product
   appears only when the assets hold one). Paths may arrive quoted, space-separated, dragged into the terminal, or one per line. If an image arrives only as a chat
   attachment without a file path, ask for its path or folder. Validate every path (Glob/ls) and report any that don't exist.
   **The four choices**, in ONE AskUserQuestion call once the paths are validated, each skipped when `$ARGUMENTS` answers it, none recommended:
   - header "QC fixes" (item 27), "After a video's first image, how should QC and its fixes run?": **"Ask me first"** ("From the first video on, I show you what QC found,
     what the fix would change and cost, and wait for your yes or no before spending credits on it.") · **"QC agents fix on their own"** ("The QC agents draw again with
     one diagnosed fix on their own, without asking, and ship the best take flagged if it still fails.") · **"No QC, I review at the end"** ("No QC agent runs after a
     video's first images: each image is made once, the video is assembled and delivered unchecked, with no new draw. Once everything is delivered you tell me what to fix.").
   - header "Images", none recommended: **"Generate with OpenAI"** ("I make every image with the OpenAI Images API on your key (OPENAI_API_KEY on
     this PC), check each one and draw again by your QC-fixes choice; it uses your OpenAI credits.") or **"FLUX 3 Klein on this PC"** ("I
     make every image locally with FLUX 3 Image Klein (int8) on this PC's GPU, check each one and draw again by your QC-fixes choice; no
     credits, about a minute or more per image, and its licence allows commercial use only for a business under US$5M a year.") or
     **"Prompts for me"** ("I write one prompt per image and the character sheets; you make the images, put them in one folder and send me
     its path; I check them."); `$ARGUMENTS` with `images api|klein|prompts` answers it.
   - header "CapCut plan" (the user, 2026-11-06: "make him pick, if he picks pro then be free to pick any edit feature that pro has if we need them, if not
     then just the free ones"): **"Free"** ("The edit uses only CapCut's free options, so every project exports without a subscription.") or **"Pro"** ("The edit may
     also use CapCut's Pro options the CapCut check showed working (such as the Pop Up and Spring text intros); you export with an active CapCut Pro subscription.");
     `$ARGUMENTS` with `capcut free|pro` answers it.
   - header "Narration model" (the user, 2026-11-11: "the user has to be asked on which elevenlabs model they want to use too
     (based on elevenlabs mcp live pull)" and "not always v4, he might use v4 turbo or other"). **Pull the live list
     first, never write it from memory** (static §6 "The models"): load `mcp__elevenlabs__list_models` with ToolSearch and call it; when it fails (on this PC: an SSL
     certificate error, static §9) run `T tts models` (the same live list through the toolkit's key, free; `--language L` marks the models that list a language). Print the
     models that can do text to speech in chat before the question, compactly: name, `model_id`, how many languages, the characters one request takes, and
     whether it is set up (`T tts models` gives `set_up`; with the MCP's rows a model is set up when `config.json → static.tts.elevenlabs.models` holds its id). The
     options are four of them **you choose** from that list (the models a creator is most likely to want: the latest flagship, its low-latency variant, and the other
     families the list shows), each described by what the list says (its description line, its language count, its request limit) and whether it is set up; any other
     listed model is picked by name or id in the Other box; `$ARGUMENTS` with `tts-model <model id>` answers it. A model that is not set up is set up before the run is
     created, from ElevenLabs' docs, as static §6 "The models" says (a stop only when the docs cannot be read: the user is told and picks another). The answer is
     stored in step 6.
   Then `T static check` (add `--offline` with prompts or klein): a part the run needs that is not ready (the key with OpenAI; `images_klein` with FLUX 3 Klein; `tts`,
   the ElevenLabs key and the run's model, for every run: the narration is ElevenLabs', static §6) is a blocker: report it with static §9's setup line and stop before any
   analysis. With no ElevenLabs key, tell the user how to set `ELEVEN_API_KEY` themselves (static §9: never typed into the chat), wait for their word, then `T static
   check` again (no restart needed); say once the account's characters left (`tts` gives them; the model bills at its `credits_per_character`, one a character on Eleven
   v4, static §6). Music (ACE-Step 1.5) makes the bed under every video (static §6): when it is not ready, tell the user here with static §9's setup line; the videos then
   go without a bed (never a blocker). CapCut must be closed when a video is built (the build stops otherwise, `cs-edit`): say so once.
6. **Create the run** (only at a new start: a session that already has a run continues it for every later request, new references included; the router's "One run per
   session"):
   - `T new-run --source "<refs folder>" [--assets "<path>" "<path>" …] [--examples "<folder>"]`;
   - keep `RUN` from the JSON;
   - write `RUN/todo.md` (contract item 38, the user, 2026-11-13: tasks and to-dos so that what is done and what comes next is never only in a conversation): a first line `# Run to-do: <run id> (kept by the main session; one writer)`, a
     `Next:` line, an `Updated:` line, the marks (`[ ]` not started, `[~]` in progress, `[x]` done, `[-]` dropped with its reason), then every phase still ahead as checklist items (the start answers, the references'
     analysis, A6s's steps with each video's standing fresh read, S2, S3's stretches, the bed, S4 and X10, the wrap-up); make the session's tasks from them when it has task tools (TaskCreate, TaskUpdate); each later
     phase adds its own items when it starts and the hand-off ticks the finished one;
   - store the run's choices: `T state --run RUN set analyze_submode=static static_images=api|klein|prompts audio_ingest=whisper qc_fixes=ask|auto|off` (no video model is stored; item 36),
     the effects folder: `T state --run RUN set static.effects_folder="<folder>"` or `static.effects_folder=none`, the CapCut plan:
     `T state --run RUN set capcut_plan=free|pro`, and the narration model: `T tts model --run RUN --model-id <id> --source
     elevenlabs-mcp|toolkit-api` (the source the live list came from; it refuses a model that is not set up, static §6).

## Rules this phase owns (contract items 24, 27)

24. **Audio ingest** is `whisper` in Static and is never asked: every reference's audio is transcribed locally (faster-whisper, the config's `whisper_model` = `medium`, always: the user, 2026-11-14, "we should strictly always use medium model for anything", so no smaller model as a default, a fallback or a speed-up; int8 on the CPU)
    and written once per reference as `10-media/<V>/transcript.json` and `transcript.txt` by `T prep-all`; `state.json → audio_ingest` is the only source.
27. **QC fixes** (the user chooses at the start; `state.json → qc_fixes`, a run without it is `auto`):
    - **`ask`**: when QC finds issues in a video's images that only a new draw can fix, from the first video on, the fix is not drawn until the user answers yes:
      the production agent prepares the corrected request and stops with a proposal, and the main session asks (`cs-produce`);
    - **`auto`**: the QC agents correct on their own, without asking: diagnosed re-draws (at most two per image), then the best take ships flagged;
    - **`off`**: no QC agent after a video's first images at all; each image is made once and delivered unchecked, and the user says what to fix after everything is delivered
      (the wrap-up's feedback question, item 22).
    Never asked: local post-fixes, drawings and edit fixes, the retry of a call that failed with no output.

## Never (this phase)

- Never pick the QC-fixes, images, CapCut-plan or narration-model choice for the user, and never mark one of their options as recommended.
- Never write the narration model from memory: the live list first (`T tts models` or the MCP's `list_models`).
- Never decide the audio choice (it is `whisper`) and never write `no speech` for a reference whose audio was transcribed.
- Never take client assets from the references folder: it is reference material, and may show other products or executions.
- Never load a CapCut MCP tool in this command (item 39).

## Hand-off

`T state --run RUN set stage=started next_skill=cs-prepare`, then invoke Skill `cs-prepare`.

After a compaction, or on `resume`, read `RUN/todo.md` first (item 38), then re-invoke the skill named in `RUN/state.json → next_skill`: its text may have been summarised away.
