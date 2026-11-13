# Safety rules for every pick and every edit

Two rules from the user (2026-11-12), and what comes with them.

## 1. Religion and superstition: avoided (the AWL Static rule, adapted to clips)
No clip is about, names, shows or leans on a religion or a supernatural belief:
- God or gods, prophets, saints, angels and demons; clergy of any faith; scripture, prayer, worship, rituals; places of worship and what is in them;
  religious symbols as the subject of a shot (a cross, a crescent, prayer beads, a halo, idols); pagan and mythological gods; every other faith;
- superstition: astrology and horoscopes, omens, charms and amulets, curses, fortune telling, spirits and ghosts presented as real, "bad luck" rituals.
How it applies:
- **A moment whose point is one of these is not picked.** It is not cut down to the rest of it: another moment is chosen. This includes a streamer reacting to a religious
  video, a debate about faith, a prayer, a "my horoscope says" bit.
- **A moment where one is incidental** (a church in the background of an IRL walk, a necklace, an old joke with a saint's name in a place name) is edited so it does not show or
  sound: cut a few seconds earlier or later, choose another angle of the span, or leave the moment. A place's own name that carries a religious word (San Francisco) is geography and stays.
- **An exclamation** ("oh my God", "swear to God") is a figure of speech, not a topic: it does not make a moment religious. Still, if the moment can be cut so the exclamation is not in it
  at no cost to the joke, cut it out; when it cannot, keep the moment and list the exclamation in the video's report so the user can decide. It is never highlighted in a caption.
- **Fiction is not a belief**: ghosts in a horror game, a magic spell in a fantasy game, a fortune-teller NPC are fiction and stay. A streamer who says a ghost is really in the room, or reads a tarot card for a viewer, is superstition and is avoided.
- Captions, titles, hashtags, sound effects and music follow the same rule (no church bells, choir, chants, "amen" sound; no horoscope hashtag).
- Check the transcript words of every picked span for these before building, and the frames of the span for a place of worship or a symbol that stands out.

## 2. Distressing, gory, indecent: kept, never avoided, but blurred, only where it is seen
The moment stays in the clip. The section of the video where the content appears is blurred, and only that section: the time span it is visible, and the part of the frame it occupies when it
does not fill the frame. The rest of the clip is never blurred.
What gets blurred:
- **Gore and injury**: blood, a wound, a burn on skin, a broken bone, a body or a body part, a corpse, an animal hurt, violence or a death shown as it happens (a real one: a video the
  streamer is watching, a news clip, a game with realistic gore).
- **Real distress**: a real person in agony, terror or a breakdown seen in a video, a real accident's aftermath. Ordinary strong feeling (laughing, crying, rage, screaming at a game) is normal and is not blurred.
- **Nudity and sexual content**, implied or explicit, in a video, an ad, a photo or a screen.
- **Personal data**: a phone number, an address, an email, a payment card, a licence plate, a password or stream key, a private message with a private person's name, a live location, a child's face when it is not the streamer's own channel content. Blur the region while it is on screen.
Procedure (an agent does it for its own video):
1. Find the span: in the scan it is a `sensitive` entry on the moment (rec from, rec to, what, where in the frame). In the build, look again at full resolution: `cc.py grid-frame --run RUN --at <rec> [--region x,y,w,h]` (a frame with a 10% grid; measure the region on it) at the first moment it shows, at the last, and in between.
2. Decide the region: a part of the frame (a video playing in a window, a screen share, a corner) gets `region` = x,y,w,h as fractions of the frame; when it fills the frame, no region (the whole frame for that span).
   If the only thing on screen in that span is the streamer's own face and the blur would hide the whole point, the moment is not picked and the brief says why.
3. Set the span with a margin of 0.2 to 0.4 s before it first shows and after it is gone (frames are 0.75 s apart in a sheet: look at `cc.py frame` for the exact beat).
4. Put it in the EDL segment as a `censor` entry (`rec_from`, `rec_to`, `region`, `style` blur or pixel, `why`). `cc.py edl-check --make-censor` makes the blurred file for exactly that span and replaces the span in the edit with it. Check it with `cc.py censor ... --preview-only`
   (a blurred frame to look at) and look at the frames just before, inside and just after the span in the finished plan.
5. Audio is not changed by the blur. A scream of real pain or an explicit audio line is a call for the agent: choose a cut that avoids it, or note it in the report.
6. Every span blurred is listed in the video's report (rec range, what, region, style).

## 3. Other things an agent keeps in mind
- **Slurs, hate and threats**: a moment whose point is hate is not picked. A slur that is incidental is masked in the caption (`captions.mask_terms`) and, when the cut can avoid it, cut out; the report lists it. **With captions OFF** (the user's choice at the start) nothing masks it and no audio is edited: the plan marks every span where one is heard and cuts around it (or leaves the span out), and the report lists every one that is still audible. Ordinary swearing is the streamer's voice: it stays; mask only the hardest words in captions when the platform would limit the video (the report says which).
- **Meaning**: a cut never makes a person say or mean something they did not (no cutting "I would never" down to "I would"). When a clip needs context to be fair, the context is in it.
- **Minors, health, tragedies**: no jokes on a real tragedy, a real death or a real victim; not picked.
- **Commercial music**: a song that plays on stream can get a clip muted or claimed on YouTube, TikTok and Instagram; cut around it or leave the moment out; the report notes it.
- **Credit**: the posting notes credit the streamer and the channel.
