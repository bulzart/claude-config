---
name: atp-brand-guardrails
description: "/analyze-then-pick has reference/brand-guardrails.md: the client's rules from documents in the assets folder decide which references are picked (core hit → dismiss) and what is edited (peripheral hit → count reduced, competitor marks removed never blurred, ambassador faces swapped, captions rewritten)"
metadata:
  type: project
---

On 2026-10-08 the user asked that agents pick references under the brand's guardrails found in
the assets folder: dismiss a reference when its core is what a rule bans (a gory prank under "no
gore", a taste test under "no competitors", "Rogan reacts" under "no ambassador likeness"); pick
and edit when the hit is peripheral (three cans → two under "two cans per day max"; a Red Bull or
Monster in frame de-branded, names and logos removed, never blurred, while Doritos stays because
it is not a competitor; an ambassador's face swapped without exception). Result:
`~/.claude/analyze-then-pick/reference/brand-guardrails.md` (extraction to
`30-assets/guardrails.md` with competitor/people/limit/wording/presentation lists; rule kinds with
operations; the per-reference guardrail audit with the core-vs-peripheral meaning test; Recreate
first filter; Create invariants; Edit Mode hits shown, user decides; edit grammar; QC; wrap-up).
Wired: command item 21, §1 references, A2, A3, A4, A6, A6r, E2, X1, X2, X9, §6 wrap-up, Never;
protocol §2.13, card line, §5 ranking, §6; generation-system §5 gate, §9b, §10 brief line;
creative-direction brand safety; text-and-format Recreate wording exception; assets docs line;
production-agents; Seedance/Wan de-brand phrasing; README; build prompt.

**Why:** rules in the client's documents were only "authoritative requirements" with no pick or
edit logic; the user wants references kept whenever an edit fixes the hit without changing the
video's meaning, and dropped only when the rule hits the video's core.

**How to apply:** precedence is user instructions > guardrails > house approach > defaults;
guardrails never relax hard rules; never invent a rule; competitor = named or same category as
the client's product. New rule kinds or cases go into `brand-guardrails.md` §2–§3, then the build
prompt. Related: [[atp-anomaly-catalog]], [[atp-creative-direction]], [[atp-build-prompt-sync]].
