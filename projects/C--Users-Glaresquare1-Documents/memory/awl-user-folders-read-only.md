---
name: awl-user-folders-read-only
description: /analyze-with-loupe never moves, renames or deletes the user's reference, example or edit-source files, it copies them; hooks/awl_input_guard.py refuses it for open runs (item 34)
metadata:
  type: feedback
---

The user, 2026-10-27/28: "make it so that when the agents do not remove or move the files from the reference folder, but if they need them in
the new directory i,e their run folder or others just copy them and not move". Contract item 34: nothing in the references, assets, examples
or edit-source folders is moved, renamed, deleted or overwritten; a file needed elsewhere is copied. Only the toolkit's own derived folders
are added there (`files_audio/`, `videos_without_audio/`, Edit Mode's `final/`).

**Why:** at 23:30:59 on 2026-10-27 all 15 videos of `Documents.10` went to the Recycle Bin in one batch while loupe run
`20261027-224009-27` (and an /analyze-then-pick run abandoned 18 s earlier) used the folder; a loupe run started at 23:33 inventoried an empty
folder; the videos were copied back from Downloads at 23:39. Who deleted them is not on record (session transcripts are not read).

**How to apply:** copy (`cp`, `Copy-Item`, `shutil.copy2`) into the run folder; never `mv`/`rm` in a user folder. The PreToolUse hook
`hooks/awl_input_guard.py` (Bash, PowerShell, Write, Edit, MultiEdit, NotebookEdit) refuses moves, deletes and writes inside the references,
edit-source and examples folders of loupe runs that are not done or abandoned and changed in the last 7 days (it also refuses copies, redirections and encoder outputs landing there, and a delete of a folder that holds one); the toolkit's writes retry an atomic replace a reader held, because the hook reads state.json on every call. The assets folders stay open, because the user curates them
([[neurogum-package-forms]]). If the user asks for such a change while a run is open, say it is refused and that they can make it themselves.
Related: [[analyze-with-loupe-command]], [[awl-effort-level]].
