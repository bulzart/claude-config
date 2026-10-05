# Trend brief — fixed format (filled by the run-time trend agent)

> **OWNER RULE (2026-09-16): the "Caption style" section is informational only, for the owner's
> separate caption tool. The edit step NEVER applies speech captions/subtitles; recommendations in
> the "apply to this video" list must not include captions — only hook text overlays, callouts,
> end cards, sounds/SFX, transitions, VFX, colour/grain and CTA.

Output path: `runs\<run-id>\90-postgen\trend-brief.md` (this format, verbatim headings) and
`runs\<run-id>\90-postgen\trend-brief.json` (same ids/fields). The editing step reads the JSON; the
owner reads the Markdown. Procedure and source notes: `research\trend-sources.md` §2–3.
Rules: every item has `source`, `url` (or "manual: <file>"), `fetched_at`; every sound has a
`license` value from {`organic-only`, `tiktok-cml`, `meta-sound-collection`, `owned`, `unknown`};
never invent numbers — write "n/a" when a source gives none; keep to one page of Markdown plus the JSON.

---

```markdown
# Trend brief — <run-id>

| Field | Value |
|---|---|
| Niche | <e.g. home fragrance / candles> |
| Sub-niche keywords | <3–8 keywords from entities.json> |
| Platform(s) | tiktok / reels / shorts (primary first) |
| Deliverable type | organic | paid ad  (drives the music rule) |
| Audience | US, <age band>, <gender skew if known>, <intent: discovery / purchase> |
| Date / window | <YYYY-MM-DD>, sources covering the last 7 days unless noted |
| Coverage | tier0-only | tier0+browser | tier0+browser+paid  (which tiers of the procedure ran) |
| Sources not reached | <list or "none"> |

## 1. Top 5 sounds

| # | id | Sound (title — artist / "original audio by @x") | Platform | Momentum (rank / uses / arrow) | Source + url | fetched_at | License | Fit for this video |
|---|---|---|---|---|---|---|---|---|
| 1 | tb-s1 | | | | | | organic-only / tiktok-cml / meta-sound-collection / owned / unknown | high / med / low + one reason |
| 2 | tb-s2 | | | | | | | |
| 3 | tb-s3 | | | | | | | |
| 4 | tb-s4 | | | | | | | |
| 5 | tb-s5 | | | | | | | |

Licensed alternative for paid use: <CML / Meta Sound Collection track, or "build bed with Splice prompt_to_stack at <BPM> <mood>", or ElevenLabs> — id tb-alt1, license, url.

## 2. Top formats and hooks

| # | id | Format (one line) | Hook (first 2 s, verbatim or paraphrase) | Example (url) | Views / date | Source | fetched_at |
|---|---|---|---|---|---|---|---|
| 1 | tb-f1 | | | | | | |
| 2 | tb-f2 | | | | | | |
| 3 | tb-f3 | | | | | | |
| 4 | tb-f4 | | | | | | |
| 5 | tb-f5 | | | | | | |

Hook-text candidates (3–7 words each, from Top Ads keyword insights / rising Google Trends terms / example titles): 1. … 2. … 3. …

## 3. Caption style

- Dominant style in the niche this week: <word-by-word | 2–4-word phrases | static line | none>, <font family class>, <colours: fill / stroke / highlight>, <position>.
- Emoji / punctuation habits: <…>
- On-screen text density: <low / medium / high> — evidence: <example urls>
- Recommendation for this video: style id `wordpop-v1` | `phrase-v1` | `hook-only`, font <Poppins ExtraBold / Anton / …>, size <px>, baseline y <px>.

## 4. Effects and transitions

| id | Effect / transition | Where it appears in the niche (example url) | Frequency this week | Use here? (yes/no + where in the timeline) |
|---|---|---|---|---|
| tb-e1 | e.g. punch-in zoom on hook | | common / occasional / rare | |
| tb-e2 | e.g. whip slide on location change | | | |
| tb-e3 | e.g. speed ramp montage | | | |
| tb-e4 | e.g. CapCut template "<name>" pattern | | | |

## 5. Hashtags

| Tier | Hashtags (with post count / rank when available) | Source | fetched_at |
|---|---|---|---|
| Niche (3–5) | | | |
| Trending-general (1–2, only if relevant) | | | |
| Product / brand (1–2) | | | |

## 6. Posting notes

- Duration sweet spot seen in top examples: <e.g. 9–18 s>; original video length: <s>; planned edit length: <s>.
- Best-performing publish windows (US, from source or "n/a"): <…>
- Platform-specific: TikTok <…>; Reels <…>; Shorts <…> (e.g. attach sound in-app, captions on/off, 3-minute Shorts cap).
- Ads only: CTA button copy to mirror, safe-zone variant (TikTok ads bottom 370 px), CML/Sound Collection track attached at publish.

## 7. Apply to this video — recommendations (ranked)

| # | Recommendation | Rationale (evidence id) | Cost / risk | Maps to edit-plan field |
|---|---|---|---|---|
| 1 | e.g. Open with hook text "<…>" over clip 1 punch-in | tb-f2 hooks + Top Ads CTR keyword "<…>" | low | text.hook |
| 2 | e.g. Attach sound tb-s2 in-app (organic) / use tb-alt1 (paid) | momentum + license | low | audio.bed |
| 3 | e.g. Word-pop captions, Poppins ExtraBold | §3 | low | text.captions |
| 4 | e.g. Whip transition into the reveal only | tb-e2 | low | timeline[].transition_in |
| 5 | e.g. Keep total ≤ 24 s, drop clip 4 | duration sweet spot + clip-qa S3 | none | deliverable.max_duration_s |

Do-not-do list (things trending in the niche that conflict with the plan, product or brand safety): <…>

## 8. Risks

- Licensing: <e.g. tb-s1 is organic-only; paid variant must use tb-alt1>.
- Trend age: <e.g. tb-f1 peaked >14 days ago; expect declining reach>.
- Platform policy / brand safety: <e.g. sound contains explicit lyrics; AI-generated content label required on TikTok/YouTube when realistic>.
- Data quality: <e.g. TikTok Creative Center not reached — sounds list from Later/Buffer only; Tokchart chart is global, not US>.
- Product fit: <e.g. format tb-f3 needs a hand model; generated clips have hand anomalies>.
```

---

## JSON companion (`trend-brief.json`)

```json
{
  "schema": "analyze-stack.trend-brief/1",
  "run_id": "", "niche": "", "keywords": [], "platforms": [], "deliverable_type": "organic|paid",
  "audience": {"geo": "US", "age": "", "intent": ""},
  "date": "", "coverage": "tier0-only|tier0+browser|tier0+browser+paid", "sources_not_reached": [],
  "sounds": [{"id": "tb-s1", "title": "", "artist": "", "platform": "", "momentum": "", "source": "", "url": "", "fetched_at": "", "license": "organic-only", "fit": "high", "fit_reason": ""}],
  "licensed_alternative": {"id": "tb-alt1", "title": "", "license": "", "url": ""},
  "formats": [{"id": "tb-f1", "format": "", "hook": "", "example_url": "", "views": null, "date": "", "source": "", "fetched_at": ""}],
  "hook_candidates": [],
  "captions": {"style": "wordpop-v1", "font": "Poppins ExtraBold", "size_px": 72, "baseline_y_px": 1240, "fill": "#FFFFFF", "stroke": "#000000", "highlight": "#FFE600", "evidence": []},
  "effects": [{"id": "tb-e1", "name": "", "frequency": "", "use": true, "where": ""}],
  "hashtags": {"niche": [], "general": [], "brand": []},
  "posting": {"duration_sweet_spot_s": [9, 18], "windows_us": "", "platform_notes": {}},
  "recommendations": [{"rank": 1, "text": "", "evidence": ["tb-f2"], "risk": "low", "edit_plan_field": "text.hook"}],
  "do_not": [],
  "risks": [{"type": "licensing|trend-age|policy|data-quality|product-fit", "text": ""}]
}
```
