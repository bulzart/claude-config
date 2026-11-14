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
- Never across a hole in the recording (a chunk with `gap_before_s`), never over an ad batch or an avoid span, and never in a way that changes what something means (`safety.md`). A bit from an earlier part of the stream is a span of its own; it never straddles a hole.
- Context goes with what needs it and comes before it in the video: if what leaned on it is dropped, the bit is dropped too.

## Who does what (the flow stays read, plan, deliver; nobody new is involved)
- **The mining agents** already read every line of their block. When a moment they pick needs something a viewer would not know, its `needs_context` says what, and where the stream tells it when they saw it in their block (a rec span). When it lies outside their block, or they cannot see where, they say only what is needed: the planner sees every block and finds it. Anything not tied to a moment (the premise of the stream, a thread that runs through it) goes in `notes`. They do not go looking for it, and a moment's bounds are not stretched for context (that is what `setup_from` is for).
- **The planner (`cc-plan`)** is the one place that sees every block, so it connects what a single miner cannot (next section). It checks the words and a frame before keeping a bit, marks each one in the long video's brief as a **context span** with what it gives and what needs it, and leaves out what the data does not support.
- **The builder (`cc-build-long`):** keeps a context span to what the context needs, may apply the same judgement when it decides what to drop inside a run, and lists every context span in its report with what it gives.
- **Shorts:** a short carries its own setup (`setup_from`, `needs_context`); nothing else changes for them.

## Finding the context (the planner, across blocks too)
1. **Leads:** the `needs_context` of the moments it keeps (what, and where if the miner saw it), the blocks' `people` (`first_rec`, `notes`: where someone first shows up) and `summary` lines (they carry rec times: who is on, what they do, the topic, the turns), the block notes, a moment at the very start of a block (its beginning may lie in the block before), and the words just before a kept span that opens in the middle of something. A moment that needs nothing needs no search.
2. **Already told?** If the video already tells it earlier, there is nothing to add.
3. **Where does the stream say it?** If the miner gave no place, or the place lies in another block, use a plain text search over the transcripts of the whole recording (`RUN/10-media/Cnnnn/transcript.txt`; every line carries its rec time) for the name or the word, and read around the hits (`T window`). Search for the word as the transcript may have written it too (`lexicon.json` and the `people` notes list the spellings Whisper used). Leave out hits inside ad batches and avoid spans. A passing mention is not the telling; the place where the stream really says it is the one to use, which is often but not always the first hit. To tell the telling from a mention, read the lines around each candidate and ask what the moment that leans on it actually needs (its `needs_context`): the telling is where someone explains the thing, asks what it is, gives its rule, reason or stakes, or reacts to it being new; a line that only uses the word as if everyone knew it is a mention. When several places tell it, take the clearest one that a viewer can follow on its own, and check a frame. When none does, the stream does not tell it: judge the moment without it.
4. **Decide from what you read:** would a viewer be lost without it? If so, keep the bit that carries it as a context span, placed before what leans on it. If the stream never says it, or a viewer would not be lost, judge the moment without it.
