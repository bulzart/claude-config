## 5. Strengths, weaknesses and failure modes

Kling 4.0 has no failure record in this library yet; the rows below come from Kling's own warnings and the general model risks this command checks, and each is to be confirmed or struck by QC of the first takes.

| failure mode | typical trigger | mitigation |
|---|---|---|
| Burned-in subtitles appear | default behaviour; dialogue in the prompt | "no subtitles" line in every prompt (§3.11 b) [OFFICIAL S1] |
| Background music added | default behaviour | "No background music." / "SFX only, no music, no score, no song, no soundtrack." [OFFICIAL S1] |
| **Unmotivated cuts** in a take meant to be continuous | multi-shot on by default | FORMAT MODE continuous-take sentence (§3.5) [OFFICIAL S1 wording; effect unverified] |
| Invented beats, extra characters or story | short prompt + prompt expansion | complete prompt with counts and every beat [OFFICIAL S1] |
| A reference used for the wrong job | bare `@Image1` without a role | one role and a preserve-list per asset [OFFICIAL S1] |
| Characters, composition or text carried over from a style or video reference | no scope stated | "reference only its …; never inherit …" [OFFICIAL S1] |
| An edit regenerates instead of editing | "Reference @Video1" wording; wrong `mode` | "Edit @Video1" + `mode:"video-edit"` [OFFICIAL S1; INFERRED] |
| Unrequested changes in an edit | no keep-list | "Keep everything else unchanged, including […]" plus the keep-list [OFFICIAL S1] |
| Photoreal and animated looks mixed | animation style without exclusion | exclude photorealism [OFFICIAL S1] |
| Vague look | abstract adjectives ("premium", "cinematic feel") | concrete light, material and composition [OFFICIAL S1] |
| **Duplicated objects / extra people / miscounts** | counts left implicit | "EXACTLY <n> — NO DUPLICATES" first, "Exactly <n> … throughout" last [OFFICIAL S1 pattern] |
| **Identity drift, clothing changes, left-right swaps** | long multi-beat takes, cuts | references per person, LOCATION MAP, "Maintain consistent character positions, eyelines, and clothing", "No cuts, fades, dissolves, speed ramps, wardrobe transformations" [OFFICIAL S1] |
| Overlapping or misassigned dialogue; wrong accent | several speakers | one speaker at a time, line while on screen, "without English-accented pronunciation" [OFFICIAL S1] |
| **Arbitrary slow motion / sudden speed changes** | mood words, no pacing | "Real time", "no slow motion, no speed changes" [OFFICIAL S1] |
| **Dead space** at the start or end | nothing happens at 0.0 s; long holds | the first frame written mid-action ("Every shot begins mid-gesture […] No empty establishing beat."); a beat per row to the end [OFFICIAL S1] |
| **Morphing** between object states | transformation without a physical path | "No fades, dissolves, or object-morph transitions"; the state change shown as a hand action [OFFICIAL S1] |
| Hands through objects; weightless props | no physics stated | PHYSICS line: weight, inertia, "never passes through" [OFFICIAL S1] |
| A count changes after an exit, occlusion or cut; a product used through a part with no opening; a later state leaking from a reference (`reference/anomaly-catalog.md` §3) | counts and parts written once | counts restated in the first words after each exit or cut; part, preparation step and contact point per use; references show t=0 states only [INFERRED] |
| Placed product too large or too small (`reference/anomaly-catalog.md` §2.7) | untested on this model | size relation written as a check; first output measured with `awl.py scale`; risk in the brief [INFERRED] |
| Landscape or cropped result | `auto` ratio; a start frame not 9:16 | `aspect_ratio:"9:16"`; 9:16 frames and sources (§2.6) [OFFICIAL S1] |
| 1080p output and a higher bill | `resolution` omitted | send `720p` [HF S2] |
| Lip movement or music-timed motion under an own voiceover or restored audio | audio cannot be switched off | "No dialogue, no voice-over, and no background music."; track replaced in post [INFERRED] |
| Garbled or extra in-frame text | described signs or screens; quoted strings | plain, unmarked surfaces; quotes only for dialogue and intended text (§3.11) [INFERRED] |

