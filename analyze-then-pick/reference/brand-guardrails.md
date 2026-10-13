# Brand guardrails: picking and editing references under the client's rules

Clients ship rules with their assets: a brand book, a "dos and don'ts" sheet, a legal or compliance
note, a claims policy, a list of people whose likeness may not be used. Those rules decide which
references may be picked and what has to change in them. The principle, in one line:

> **If a reference's core is what a rule bans, do not pick it. If the rule hits something that an
> edit can change without changing what the video is about, pick it and edit it.**

Seed cases (an energy-drink client):
- "No blood or gore." A reference whose joke is a gory prank is about the gore: **dismiss**. A
  reference with a horror poster on the wall: the poster is set dressing, **pick and remove** it.
- "No excessive-caffeine messaging; two cans per day max." A reference that shows three cans on a
  desk: **pick and reduce** the count to two. A reference whose joke is drinking twelve cans:
  **dismiss**, the excess is the video.
- "No competitor brands on screen." A Red Bull or Monster in the frame: **pick and de-brand** it
  (its name and logo removed, the object kept, never blurred); the one analogous product is
  swapped for the client's anyway. A bag of Doritos is not a competitor and stays. A "Red Bull vs
  Monster taste test" is about the competitors: **dismiss**.
- "No ambassador likeness (Rogan, Aoki, Ohno, Tsunoda, Hooper, Schulz)." A reference with one of
  them in it: **pick**, and the face is swapped without exception, as every person is in Recreate.
  A reference whose hook text is "Joe Rogan reacts to…" is about him: **dismiss**.

The guardrails are the client's **authoritative requirements** (`analysis-protocol.md` §6): the
user's instructions for the run outrank them, they outrank the house approach and the pipeline's
defaults, and they never relax a hard rule (physics and continuity, the must-not-survive list, the
permission rule, the house text style, the model lock). Nothing is dismissed without a quoted rule,
and no rule is invented. **The pipeline has no content rules of its own.** Without a guardrail
document, only the copyright and ownership floor of `generation-system.md` §9b (the replaced
person, the swapped or competitor product, overlay text and handles, platform logos and
watermarks, featured third-party branding, a copyrighted character as the subject) and the
generation service's own blocks apply; alcohol, weapons, gore, profanity, meme faces, cameos and
everything else stay exactly as the reference shows them, and nothing is blurred, pixelated,
softened or removed for taste. A brand rule can add a content rule; it can never remove the floor
or enable what the service refuses.

## 1. Finding and reading the guardrails (A2)

- **Where:** any document among the supplied assets (`30-assets/project/docs/`), and any document
  in the references folder (`10-media/docs/`): PDF, docx, md, txt, spreadsheets, slides. Typical
  names: guidelines, guardrails, brand book, brand rules, dos and don'ts, legal, compliance,
  claims, restrictions, usage, safety, ambassadors. Read every document anyway (`T doc-text`,
  PDFs with Read); a rule can sit in a spec sheet's footer.
- **Write `30-assets/guardrails.md`** (and `state.json → guardrails`): one rule per line,
  `G<n> · <quote> [E] · <source file> · <kind, §2> · <what it hits> · <default operation>`. Then
  the derived lists the rules imply, each marked [E] when named or [I] when inferred:
  - **competitors:** the brands the document names, plus every brand in the client's product
    category (another energy drink for an energy drink, another gum or nootropic for a gum; a
    snack, a phone or a car is not a competitor of a drink);
  - **people:** ambassadors, celebrities, athletes, anyone whose likeness is excluded, with the
    cues to recognise them (the names only; faces are matched from the references' own context:
    a podcast set, a name on screen, a known show);
  - **limits:** counts and servings ("two cans per day", "one serving per video"), times of day,
    contexts ("never while driving", "never with alcohol");
  - **wording:** banned words and claims, required disclaimers with their wording;
  - **presentation:** how the product may be shown (upright, label clear, not in the mouth,
    never distorted, clear space around the logo, colours).
- **Conflicts** between documents, or between a document and the user's instructions, go to the
  user once, with both quotes (protocol §6). Everything else is applied without a question.

## 2. Rule kinds, and what each does to a reference

| kind | examples | how it shows in a reference | editable when | operation when editable |
|---|---|---|---|---|
| **Content ban** (exists only when a client rule names it; the pipeline bans nothing by itself) | blood, gore, drugs, alcohol, tobacco, vapes, weapons, dangerous stunts, profanity, political or religious content, minors consuming, meme faces or cameos | the scene, a prop, a poster, a word in the caption, a word in the speech, an insert | the element is set dressing or one caption word, and nothing in the action touches it | remove the prop or poster ("Remove only …, reconstruct the wall"); rewrite the caption word; cut the insert; a spoken word cannot be edited (the original audio returns) |
| **Quantity and consumption limit** | "two cans per day max", "one serving per video", no chugging, no mixing with alcohol, not as a pre-workout before X | the number of units in frame, how many are opened or drunk, what sits beside the product | the extra units are not handled and the count is not the joke | set the ledger count to the limit; "Remove only the third can …" with the surface reconstructed; the two that remain keep their spots and states |
| **Competitor exclusion** | "no competitor brands on screen", no rival logos, no comparison | a rival can, bottle, pack, shell, bag, app or sign; a comparison; a brand name in speech or text | the rival object is not the subject and the video is not a comparison | **de-brand:** remove the name, the logo and any mark that identifies the brand from the object; keep the object, its shape, size, spot and light; when the trade dress alone names the brand (a green claw, a blue-and-silver livery), neutralise it to a plain colour. Never blur, pixelate or paint a block over it. The one analogous product is swapped for the client's product (`generation-system.md` §4); other rival units are de-branded or, when nothing touches them, removed. Non-competing brands stay unless §9b or another rule hits them |
| **Likeness exclusion** | no ambassador likeness, no celebrities, no real people without a release, no minors | the person on screen; a reflection; an insert or meme that shows them; their name in text or speech; their voice | the person is a performer who is swapped (Recreate swaps every person) and the video is not about who they are | mandatory, complete face swap to a supplied character (face, hair, distinctive marks, reflections and mirrors); an insert that shows them is cut and not placed back; their name in text is dropped; the voice stays in the original audio and is named in the brief, unless the rule names the voice too, in which case a speaking appearance dismisses the reference |
| **Wording and claims** | no health or medical claims, no "best", no caffeine figures, no pricing, no guarantees, required disclaimers | caption lines, labels, spoken lines | the line is a caption (CapCut rewrites it) or a required disclaimer (a text layer is added); a spoken claim only when its segment can be trimmed at a cut without losing a beat or the sync | rewrite the text layer minimally (the role, position, timing, subject and meaning stay: remove only the banned element, a number, a statistic or a name, and say the same thing in the same grammar, never an unrelated line; CE-022; `text-and-format.md` §1); add the disclaimer as a CapCut layer in the house style; trim or dismiss for speech |
| **Presentation** | product upright, label toward the camera, not distorted, clear space, never in the mouth, never on the floor, colour rules | the plan's anchor, grip and use beats | always (these are plan rules, not pick rules) | the affordance sheet and the anchor obey them; a use beat the rule forbids is replaced by the nearest allowed use |
| **Context and audience** | never while driving, never in a gym with alcohol, never at a party, not for under-18s | the setting of the scene, who consumes, and who the casting and the caption make a character read as (a parent's authority, a school, a curfew) | the context is a backdrop that an adapted environment can change (`generation-system.md` §2) and the characters are supplied adults | adapt the environment or the character; for an adult-only audience (a client rule, or an energy drink or supplement) cast people who read 20 or older and rewrite wording that implies a minor into an adult register (college, work) with the joke kept (CE-008: a caption with "mom" and the youngest-looking cast made an energy drink read underage); when the setting is the premise, dismiss |
| **Platform and sound** | no duets, no lyrics, no sound X, no stitching | the format, the soundtrack, the inserts | always in Create (the sound plan obeys); in Recreate when the sound is not the video's point | the sound plan drops the item; an insert is cut |

## 3. The guardrail audit, per reference (A3 card, E2 card)

For every reference, against every rule in `30-assets/guardrails.md`:

1. **Locate every hit:** the time range, the element, how prominent it is (the subject, featured,
   or peripheral), and where it lives (picture, caption, speech, insert, reflection).
2. **Classify the hit:**
   - **core** when the hook, the turn or the payoff depends on the element; when the element is
     the subject or the premise; when it is spoken in audio that returns under the edit; when
     removing it leaves a hole in the action or breaks a sync anchor; when a hand or the action
     touches it (fidelity, command item 19); or when the edit would change what the video is
     about or where it goes;
   - **peripheral** when it is set dressing, a unit beyond the limit that nobody touches, a brand
     mark on an object that stays, a person who is swapped anyway, a caption line, or a short
     segment that a cut can drop without losing a beat.
3. **The meaning test** for every peripheral hit: after the edit, would a viewer who never saw the
   source describe the video the same way (the same premise, turn and payoff), and does the sync
   still hold? If yes, it is editable. If not, it is core.
4. **Verdict:** **pick-clean** (no hits), **pick-and-edit** (every hit peripheral and editable;
   list the operations with their times), or **dismiss** (any core hit; name the rule and why it
   is core). Write it on the card as "Guardrail audit".

More cases, by kind:

| rule | pick and edit | dismiss |
|---|---|---|
| no alcohol | a beer bottle on the counter at the back, untouched: remove it | a drinking game; a toast; a bar scene where the drink is the premise |
| no gore | a horror poster, a fake-blood prop in a corner: remove it | a prank where the fake blood is the payoff |
| two cans max | three cans on the desk, one is drunk: remove an untouched one | a fridge full of cans as the joke; "day 5 of 10 cans a day" |
| no competitors | a Monster in the background while the subject's Red Bull is swapped for the client's can: de-brand the Monster | a taste test; "which is better"; a competitor's logo as the hook |
| no ambassador likeness | the ambassador is the performer: swap the face; the voice stays and is named in the brief | "<name> reacts" in the hook text; a podcast clip whose point is who is speaking; the rule covers the voice and they speak |
| no profanity | a swear word in a caption: rewrite the caption | the joke is the swear; the swear is spoken and the line is a beat |
| no minors consuming | a child in the background; an adult drinks: fine | the kid drinking is the premise |
| adults only | a caption with "mom" or "school", a character who reads underage: rewrite the wording into a college or work register, cast a character who reads 20 or older | the premise is a minor's life (a parent's permission, a school-run, a curfew) |
| never while driving | a parked car scene: fine; a can in a cup holder with the engine off: fine | the sip at the wheel is the beat |
| no health claims | "cured my 3 pm slump" caption: rewrite to a non-claim in the same role | a spoken testimonial about health |
| required disclaimer | add the layer in the house style where the rule says | never a reason to dismiss |

## 4. The audit in the pipeline

- **Recreate (A4, A6r):** the audit is the **first filter** of the recreate ranking. Dismissed
  references are out of the ranking and listed under it with their rule. Pick-and-edit references
  rank normally; their guardrail operations count toward the pick's edit load and motion
  complexity, and go into its operations list, its source action script (as change marks) and
  its first request, under the fidelity lock. A count reduction updates the ledger (the limit is
  the count at every checkpoint, `anomaly-catalog.md` §2.1).
- **Create (A6, X1):** the rules are plan invariants, not pick rules: the count limit is a ledger
  invariant ("never more than two cans in any frame; one is opened"), competitor objects never
  appear, only supplied characters appear, the wording rules shape the text plan, the content bans
  and context rules zero a seed's brand-safety score (`creative-direction.md` §5.1), and the
  presentation rules shape the anchor and the use beats.
- **Edit Mode (E2, E3):** the card lists every hit with its classification and the operation the
  rule requires; the E2 understanding shows them to the user ("G4 requires a face swap for the
  man on the left; G3 requires de-branding the can on the shelf"). A core hit is stated as such
  ("this video's point is X, which G1 bans; editing it would change the video"). The user decides
  the operations, as always in Edit Mode.
- **Plan and brief (X1, X6):** the plan carries the hits and their operations; the brief gets a
  line: `Guardrails: G2 (two cans max) → third can removed, count 2 at every checkpoint; G3 (no
  competitors) → Monster can de-branded at the shelf; G4 (ambassador) → face swapped, voice
  remains in the original audio`. With no guardrail document: `Guardrails: none supplied`.
- **Prompts (X2):** each operation in the model's own edit syntax (its guide §3.14 and §4): "Remove
  only the third can at the left end of the desk and reconstruct the desk and wall behind it;
  keep the two other cans exactly as they are"; "Remove only the brand name and logo from the green
  can on the shelf; keep its shape, size, position and lighting; it becomes a plain unbranded can
  of the same colour"; the person-replacement contract for the swap. Never "blur", "pixelate" or
  "cover". A printed surface the audit names (a news page on a monitor, a poster, a livery, a gate board)
  is replaced by a named concrete thing in the same grammar ("replace its whole screen with a plain dark
  candlestick chart, no text") with the original item in the exclusion line; a description of blankness
  ("gate boards showing no text", "a plain market chart") or no mention at all came back printed in the
  first requests (run 08 V01 V04, run 09 V04 V08). A patch or logo on the kept garment is the same: named
  only in the negatives ("no patch, no logo") it came back from 0.4 s; "remove only the <named patch> at
  <named place> in Video 1 and reconstruct the plain <fabric> there; it does not remain anywhere on the
  garment", with the original in the exclusion line, removed patches and a flag emblem cleanly in a later take
  (CE-065; CE-075 a1, observed, that take failed on other points). An object a rule names (a rival can on a
  shelf) is removed with a named replacement ("replace only the red can between the third bottle and the glass
  jar with a small pot; it does not remain"), because "the shelf holds the pot" plus a negative left it
  standing (CE-071: the removal worked on the retry, whose take shipped with another flaw; observed, not
  verified). A real person's name on a screen is carried by
  the video reference in every shot where it is legible, and a one-sentence edit changed it in one shot only
  (CE-080): remove it from the prepared source (`generation-system.md` §5c.2b) or ship the take flagged.

## 5. QC (X9) and the wrap-up

- **Count:** the limit holds at every checkpoint (`T qc --dense`), including the first and last
  frame.
- **De-branding:** `T qc` OCR shows no competitor name anywhere, and a full-resolution look at every
  de-branded object shows no logo, claw, crest or livery that names the brand, no blur and no
  patch; the object stands as before.
- **Likeness:** the identity check covers every shot, reflection and mirror, and every insert
  placed back; the swapped character is the only face.
- **Text:** the rewritten lines and the disclaimers are on the CapCut preview, in the house style.
- **Audience:** when an adult-only rule applies, every caption line and every cast character reads
  adult; checked on the plan's casting and on the CapCut preview (CE-008).
- A leftover hit in the picture is a **regenerate** reason with the operation named; a leftover
  in a text layer is a CapCut fix. A dismiss-level element that turns out to be core only at QC
  (a removed can was handled after all) is reported, and the reference is replaced by the next
  runner-up when the run allows it.
- **Wrap-up:** the dismissed references with their rule, and the edits each pick needed.
