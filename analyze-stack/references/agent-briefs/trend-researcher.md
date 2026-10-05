# trend-researcher — agent brief (Stage 9b; one agent; runs after P0 = "Edit now")

Load first: `LAYOUT.md`, `references\trend-brief-template.md` (fixed format, JSON companion, the OWNER RULE at
its top: the caption section is informational only), `research\trend-sources.md` §2 (ranked procedure, tiers,
fallbacks), §3 (music licensing), §4 (verified commands), `references\post-generation-playbook.md` §4 (which
boosts the editor can apply).

## Purpose
Find what is trending right now in this video's niche on the target platform(s) — sounds, formats,
hooks, effects/transitions, hashtags, posting notes — with sources, dates and licences, and rank the
boosts the edit should apply (hook text overlays, callouts, end cards, sounds/SFX, transitions, VFX,
colour/grain, CTA). Speech captions are never a recommendation for the edit.

## Inputs
`20-analysis\entities.json` (niche keywords), `30-decisions\product-spec.md` (category), `answers.json` (Q6
platform; deliverable type organic/paid if the owner said so — else assume organic and say so),
`20-analysis\style-profile.md`, `audio.md` (the original's sound profile), `40-plan\plan.json` (planned length),
`90-postgen\trend-inputs\` (owner screenshots, if any — LOOK at them).

## Outputs
`90-postgen\trend-brief.md` (verbatim headings of the template) and `90-postgen\trend-brief.json`; raw
fetch notes in `90-postgen\trend-inputs\fetch-log.md` (url, fetched_at, what was readable).

## Method
1. Derive 3–8 niche keywords and the category; set platform order from Q6; date = today.
2. Tier 0 (always, in parallel, zero cost): yt-dlp Shorts listings per tag (`youtube.com/hashtag/<tag>/shorts`,
   `ytsearch50:<niche> shorts`, run via Python `subprocess` with `encoding='utf-8-sig'`), Google Trends RSS +
   Trending Now page (WebFetch), Later / Buffer / HeyOrca roundups (WebFetch), CapCut templates hub +
   `/template/business` + `/template/effects` (WebFetch), Tokchart free top-5. Each source that errors twice
   is skipped and listed under "Sources not reached".
3. Tier 1 (only if the `claude-in-chrome` skill is available in this session and Notes say the owner
   allows it): TikTok Creative Center Trend Discovery (US, 7 d, industry), Top Ads, Meta Ad Library UI;
   screenshots into `trend-inputs\`. Otherwise mark `coverage: tier0-only`.
4. Tier 2 (only with credentials in Notes): Higgsfield `tiktok_music_trending` after `tiktok_accounts` shows an
   active connector; Apify actor with `APIFY_TOKEN`. Never call paid tools otherwise.
5. Fill every table; every item carries `source`, `url` (or `manual: <file>`), `fetched_at`, and every sound a
   `license` from the fixed set; numbers only when a source gives them ("n/a" otherwise).
6. Recommendations (§7): ranked, each mapped to an edit-plan field (`text.hook`, `audio.bed`, `audio.sfx`,
   `timeline[].transition_in`, `look`, `text.cta`, `deliverable.max_duration_s`); never `text.captions`. Paid
   deliverable → licensed alternative required (CML / Meta Sound Collection / Splice stack / ElevenLabs).
7. Risks (§8): licensing, trend age, policy (AI-content label), data quality, product fit (e.g. hands).

## Quality bar
- One page of Markdown + the JSON; ids `tb-s1…`, `tb-f1…`, `tb-e1…` consistent between both files.
- Nothing invented: a sound without a verifiable source is not listed.
- The P3 placeholders are ready: `{niche}`, `{platform}`, `{date}`, `{3-line summary}` = the first three recommendations.

## When evidence is missing
Say which tiers ran and which sources failed; if no niche-specific sound was found, say so and give the
licensed-bed fallback; if the browser was unavailable, recommend the owner drop screenshots (trend-sources §1.15).
