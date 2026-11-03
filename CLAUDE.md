# Compact Instructions

When compacting this conversation, write a long, detailed summary. Do not aim for brevity: prefer keeping
too much over losing something that is needed to continue. A summary of tens of thousands of tokens is fine
when the session has that much worth keeping.

Keep, in this order:
1. Every request the user made and every correction or preference they gave, in their own words where the
   wording matters. Never drop a rule the user stated, even if it was given early.
2. Decisions made and the reason for each, plus options that were rejected and why, so they are not re-proposed.
3. Exact file paths, commands, flags, config keys, IDs, URLs and error messages. Quote them; do not paraphrase.
4. Files created or edited, with what changed in each and the current state of the important ones
   (key code, function signatures, settings values). Include short code or config snippets when they are
   still being worked on.
5. Work in progress: what has just been done, what is half-finished, the exact next step, and open questions.
6. Results of runs, tests and tool output that later steps depend on (counts, scores, pass/fail, run folders).
7. Anything that failed and the cause that was found, so the same mistake is not repeated.

Drop only: greetings, repeated attempts that led nowhere, and raw tool output that is already summarised
by its result.

# Reporting a change

When you change something for the user (code, a prompt, a command or skill, a rule, a setting, a document), report it
this way, in plain everyday words and short sentences:

- What you did: a few sentences on what changed, what it does now and how you checked it. No file-by-file log.
- Then a numbered list of what the change might also do that the user may not want, and of the choices you made that
  they might want differently. Look for: wording stricter or wider than meant (a title says "never" where the aim is
  "as few as possible"); normal, wanted things it could now block, flag or reject (a real camera zoom read as an added
  effect, old files a new check refuses); things it could push an agent to avoid, cram or score lower; cost or time it
  adds (more generations or credits, a slower page); other places that use what changed and could now disagree with it
  (another command, a doc, a test).
- Each point: a short name, what could happen shown with one concrete example from the user's work, why it happens,
  and "Fix:" with the smallest change that keeps the aim. One idea per point, a few short sentences. When only the
  user can decide, end the point with a short question that names the options.
- One closing line: "Tell me which numbers to change", plus the questions to answer.

Limits: keep in view what the change is for; every fix keeps that aim, and a point that is not about it does not
belong. List only what is likely in the user's real work, never padding; when there is nothing, say so in one line and
ask nothing. Fix a plain mistake in your own work before you report instead of listing it. Apply no listed fix until
the user picks it, unless they already asked you to fix what you find. No file paths, code names or jargon in the list
unless the user needs them to find something. A pipeline run's videos and edits are reported by its own wrap-up and
feedback questions, not by this list. A subagent reporting to another agent keeps its own format.
