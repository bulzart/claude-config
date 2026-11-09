## 4 The script (A6s)

`40-briefs/video-NN-script.md` (readable: the beats, the devices used, the sources) and `40-briefs/video-NN-narration.json`, the lines the
voice speaks: `{"video": "NN", "language": "english", "pace": {"refs": ["<the references the point rests on: the niche's within the
family, else the family's>"], "wpm_articulation": [<low>,
<high>], "wpm_overall": [<low>, <high>], "target": {"wpm_articulation": <the point>, "wpm_overall": <the point>}, "tolerance": 0.015,
"pauses": {<the family's pauses a minute, median, p90, long ones per 10 minutes: the pattern the plan follows>}, "why": "<the numbers>"},
"delivery": "<audio tags leading every passage, e.g. [quick, measured pace]; or none: the voice's own way>", "voice_settings":
{"stability": <0 to 1>, "similarity_boost": <0 to 1>}, "tts": {"passage_chars": <optional>, "seed": <optional>}, "lines": [{"n": 1,
"text": "…", "emotion": "neutral", "delivery": "<a line's own only: [tags]>", "tags_after": "<only where the family holds a long pause:
[long pause]>", "passage_break": <only where a passage must end>}, …]}`. The pace, the point and the pauses are the measured numbers
of the niche's references within the family, the family's beside them (§1 "The run's niche within the set", §2, §6 "The pace": the
fair measure), chosen and checked by the judge before a passage is made (§13, J1); the levers that reach
the point are the voice, the delivery tags, the settings and the words, measured on a probe first, and `T tts say` measures the
narration as delivered. Eleven v4 has no speed: a `pace.speed` is refused, and nothing is sped, cut, trimmed or gained afterwards (the
user, 2026-11-09). A `pause_after` (plans written before 2026-11-09) and `pause_default_s` are only hints of where a passage may end: no
silence is placed (§6 "Passages").

- **The length** is the agent's, per video, from the spec's length pattern (§2), never asked of the user: where this subject sits among
  the references (a subject with as much to tell as their longest runs as long; one beat-light subject as short as their shortest), the
  beats the template needs and how long the references let each run. It is written into `video-NN-narration.json` as
  `"target_length_s"` with `"length_why"` (the references' numbers it rests on), and the script is sized to it.
- **The template of the spec**: the hook in the first line (spoken within the first second), every beat in its share, the payoff, the
  closing line or loop; the length: the target, as the words at the plan's overall point (`pace.target.wpm_overall`: words =
  seconds × words a minute / 60; 530 s at 165 words a minute is about 1,460 words), the voice, its tags and the words chosen and
  measured so the narration speaks at that point (§6: nothing is sped or slowed afterwards). A spelled-out year or number counts as the words it is spoken as ("eighteen twelve" is two). (Before the
  pace was set, 2026-11-06 to 11-08, scripts were sized at the voice's own speed, which ran about 12 % under its sample's: video 02 of
  the run of 2026-11-06 said 1,154 words in 530 s: by the references' yardstick 125 words a minute overall and 152 while speaking, its
  median pause 0.83 s, against the set's 160–174, 178–196 and 0.42–0.5 s; its own lines paced by `T tts say` measured 164 and 190,
  pauses 0.5 s.)
- **Lines**: one sentence or one breath each, as the references break them; a reveal gets its own line. **Long pauses are counted, not
  sprinkled**: the niche's references hold `long_pauses_per_10min` pauses of 0.8 s or more (`T static profile --refs <them>`, the
  family's beside it; F3 of the run of 2026-11-06: median 6.3, its survival references, the run's niche, 8.8), so a video of M minutes
  gets about that rate times M/10 long pauses, at its
  strongest turns (a reveal, a chapter's start), each asked of the model in the request (the line's `tags_after`: "[long pause]", or
  "[pause]" for a shorter one; or its punctuation: an ellipsis, a dash) and measured on the probe against the family's long pauses
  (their 90th percentile and longest), since no tag has a documented length; every other rest is the voice's own at the punctuation,
  and no silence is placed afterwards (§6). (2026-11-08: video 03 planned 56 pauses of 0.5-1.2 s and
  measured 33 long ones per 10 minutes, five times the family's median: the overall point then forced the voice faster.) The judge's
  forecast (§13, J1) shows the pattern the plan will give against the family's before a line is made.
- **Emotion**: most lines `neutral`, the voice's own delivery, the wording carrying the feeling; a line tagged with an emotion the run's
  voice holds tags for (§6: `T tts voice --emotion NAME="[tags]"`) takes those tags. A **strong** line (`"strong": true, "delivery":
  "[<the feeling as audio tags, e.g. quiet disbelief, slower>]"`: Eleven v4's audio tags, §6) is for the peaks only (the user,
  2026-11-05: "not make big strong emotion changes unexpectedly, but yeah make room for it"): where the references' narrator peaks (the
  hook's turn, the reveal, the payoff), at most one line in five and never two in a row unless the references do; its delivery in the
  references' register (no shouting a reference never does); the line before leads into it (its wording, a pause tag) and the line
  after comes back down, so the feeling never jumps unannounced. Its tag holds until the next one, so its passage ends after it (§6
  "Passages"). The narration's own `delivery` (the tags that lead every passage) and a section's own deliveries (a slow, quiet stretch
  asked "[slowly]") are chosen the same way and measured on the probe (§6, §13).
- **Spoken text only**: numbers written as they are said ("nineteen fifty-nine" when the voice must say it so), no stage directions, no
  emoji, no markup; the delivery and the pauses go in `delivery` and `tags_after` as audio tags, never in `text` (words outside the
  brackets are spoken).
- **No religion and no superstition** (§11): no line names or alludes to either; a fact that needs one to be told is cut or told without
  it. The subject is the run's niche (§10), told in the references' craft.
- **Nothing indecent, gory or distressing** (§11b): a hard fact is told plainly and briefly, never by its graphic side (how many people
  died may be said; how a body was found, an injury or someone's suffering is not); no swearing.
- **Fact sheet** (factual niches): `40-briefs/video-NN-facts.md`, every claim of the script with its source URLs.
- The copy test (`creative-direction.md` §5.0) and the sharpness gate pass before the script is final.

