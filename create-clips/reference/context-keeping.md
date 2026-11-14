# Context in the parts you cut (streamer mode, long videos)

The user, 2026-11-14: a part of the stream that has nothing to show is left out of a long video. Sometimes such a part holds something a viewer would be lost without, and something the video keeps leans on it. Then the agents may keep that bit, or only the part of it that carries the context, when they find it useful.
This is guidance for the agents' own judgement, based on what the stream shows. There are no limits, quotas or fixed lengths here, and it is never a reason to keep something by default.

## How to judge (from the data)
- Read what the stream actually says and shows (the words, the frames, the reports), not the numbers alone.
- Ask whether a viewer would be lost in something that is kept if this bit were gone, and be able to say what they would be missing and where it matters. If the data does not show that, there is nothing to keep.
- Keep what the context needs, as much or as little as that is: sometimes the one line that says it, sometimes a longer piece, sometimes nothing.
- The same judgement applies to how a kept span opens: if it starts in the middle of something, the words just before it may be the context it needs.

## What it can look like (illustrations in any stream's terms, not a list to match)
The line that says who just joined or what the stream switched to; the rules or the stakes of something that is kept later; a promise made earlier whose result is kept; why the picture looks as it does (a screen gone black, a restart); the premise of the stream when the video would otherwise open in the middle of it.

## Guards (what keeps it honest)
- Only what is already on tape: no text card, no narration, no line nobody said (`edit-craft.md`). If the context could only be given that way, leave it out and judge the moment without it.
- Never across a hole in the recording (a chunk with `gap_before_s`), never over an ad batch or an avoid span, and never in a way that changes what something means (`safety.md`).
- Context goes with what needs it: if what leaned on it is dropped, the bit is dropped too.

## Who does what (the flow stays read, plan, deliver)
- **The mining agents** work exactly as before: they read their block and hand over what they found. Nothing here is asked of them.
- **The planner (`cc-plan`):** a moment's `needs_context`, the block notes and the words around the spans it keeps are its leads. It checks the words and a frame before keeping a bit, marks each one in the long video's brief as a **context span** with what it gives and what needs it, and leaves out what the data does not support.
- **The builder (`cc-build-long`):** keeps a context span to what the context needs, may apply the same judgement when it decides what to drop inside a run, and lists every context span in its report with what it gives.
- **Shorts:** a short carries its own setup (`setup_from`, `needs_context`); nothing else changes for them.
