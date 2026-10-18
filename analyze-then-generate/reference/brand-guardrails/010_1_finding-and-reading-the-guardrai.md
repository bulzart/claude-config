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

