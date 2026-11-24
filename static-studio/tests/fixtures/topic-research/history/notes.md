# Research notes: history, topic discovery

Budget used: 7 web searches and 5 page reads. A sixth fetch, Britannica on Richard Lander, was refused (HTTP 403) and
returned nothing, so it is not counted as a read. Nothing was paid for, signed into or contacted.

## Before searching
I listed history subjects that drawn maps, diagrams and painted scenes could carry for ten minutes. Two were rejected on
the content rules before any search: the Great Stink and the Broad Street pump (both told through sewage and illness),
and the Halifax explosion (told through injuries). Five others were set aside unresearched for budget, and any of them
could be a later alternative: measuring Everest, the Zimmermann telegram, the Erie Canal, California drawn as an island,
and the Panama Canal locks decision. I researched three that offer genuinely different value: a belief traced on maps
(Kong), a fraud explained by its mechanism (Blanc), and an engineering failure explained (Vasa).

## Trail
1. Search, Kong. Found the 1991 peer-reviewed study (S1), a 2023 Library of Congress post (S2), popular pages (S4-S6) and
   a dealer listing (S7). Leads: forty maps from 1798 to 1892, Binger in the late 1880s, a last appearance in 1905.
2. Search, Blanc. Found only popular retellings, which disagree on the start year (1834 or 1836), a brother's name
   (Joseph or Louis) and the verdict. No source for the "1837 law". One university lecture page (S9).
3. Search, Vasa. Found the museum page (S14) and many popular retellings. The stability test and the inquest appear only
   in summaries; the death toll is given as 30 and as 53.
4. Read S1. Abstract, footnotes and references only (the body was behind an access wall, and the tool paraphrased the
   abstract). It gave the core: the range begins with Rennell and supported his Niger argument; forty maps; lengths of
   525-3,950 km and a southward drift; the authority-of-maps argument; Binger's 1889 report and 1890 article; the editor's
   note on hills to the north-north-west; governor in 1893; Park's possible rock hills; Buache as a possible model.
5. Read S2. Rennell's 1798 map; Park's route and turning back; the Niger sent east into "Lybia Palus"; the Guinea
   Highlands; "there are no Mountains of Kong". It is independent of S1, so C01 and C03 are confirmed.
6. Search, Kong and the Landers. Leads only: Binger at Kong on 20 February 1888; "mosques instead of mountains"; a 1908
   eclipse report over the mountains; "several hundred maps".
7. Search, Holzmann and Pehrson. Their 1994 book exists, but nothing came up on the Blanc episode; 556 stations over
   4,800 km.
8. Read S9. A 1997 lecture outline. It confirms the Blanc mechanism and that operators mid-line could not read the
   messages; it names nobody and says nothing of a trial or a law.
9. Read S14. The date, "minutes", 30 dead, the design cause, the suspicion before sailing. Nothing on the test, the
   inquest or the salvage.
10. Search, the Landers' 1830 voyage. Pointed to the Princeton Library page (S3).
11. Read S3. The 1830 float from Bussa through the delta to the sea, and the 1831 announcement. With S2, C12 (the Niger
    reaches the sea through a delta) is confirmed.
12. Search, Fisher's claim (S8). A 2017 explorer's book says the mountains exist; only popular coverage, no independent
    support. Recorded as counterevidence (C21), not used.

## Why Kong, in one line
Its strange central fact rests on two independent sources I read, its causes form a chain in which each step opens the
next, and maps are both its evidence and its pictures. The Vasa was close on evidence but leads to the answer most
viewers expect.

## Dropped, and why
- "Binger found mosques instead of mountains": a vivid line from popular pages. Dropped because it makes a religious
  building the punchline of a beat, which the content rules forbid. It was only a snippet anyway.
- Binger's arrival date, the 1905 atlas, the 1908 eclipse report and "several hundred maps": unverified. They are kept in
  claims.json as legend and left out of the plan; the plan says "the late 1880s".
- Park's death on his second journey and the Landers' capture in the delta: true by the sources but incidental, so they
  are left out rather than staged.
- Buache: kept as contested material that no value carries, because the content of his theory was not read.
- "Rennell in London": the read source says only "English cartographer", so the wording says English.

## Where I was unsure
- S1 was read only as its abstract and footnotes. Check the 525, 3,950 and 1,874 km figures and the latitudes against
  the article before a script states them.
- C09 (forty maps, 1798-1892) is marked confirmed because S1 is the study that made the count (primary research on the
  maps). A stricter reading would call S1 secondary scholarship and C09 likely. In that case M3 needs a second source
  (a library record of a later map that names the range would do) before it stays decisive.
- M9 (the range as a wall that keeps the river inland) is my reasoning from the map's description and S1. Rennell's own
  argument was not read, so the plan presents it as reasoning.
- The Blanc story may be stronger than it looks here. The French court reports or Holzmann and Pehrson's chapter could
  settle the names, the discovery and the verdict.
- For the Vasa, the stability test, the inquest and the idea that its builders measured in two different units are
  strong leads, but none was read. The judgement against it is about the expected answer, not the evidence.

## Format choices
- `depends_on` sits at beat level, as in 07's beat-map example and in the checker, which reads beat `depends_on` and
  `significance.self_contained`. The brief listed it inside `significance`.
- Hedge sentences are given for the reasoned values too (R4, R6, R10), because the brief asks for one wherever a value
  is not established. The manual requires them only for contested values (R3, R7). For a reasoned value the sentence
  shows the inference rather than casting doubt on it.
- Material ids run on across candidates (T1: M1-M18, T2: M19-M23, T3: M24-M28), so no id means two things.
- The frame prompts ask for no lettering; any labels belong to the edit's drawn annotations.
