# Trend-data sources for the run-time trend agent (US audience; TikTok / Reels / Shorts)

Researched 2026-09-16 from Claude Code on this machine (WebFetch / WebSearch / MCP read calls / local
smoke tests). Every "readable via WebFetch" claim below was tested on that date; everything marked
**unverified** is community-reported and was NOT confirmed here. Re-verify URL patterns quarterly —
these sites change often.

Conventions used in this file:

- **WebFetch** = the Claude Code WebFetch tool (no cookies, no JS execution, follows only same-host
  redirects, 15-minute cache). A "JS shell" means the fetched HTML contained navigation only.
- **Browser** = the `claude-in-chrome` skill listed in this environment (drives the owner's logged-in
  Chrome) — the only way from Claude Code to read JS-rendered or login-gated dashboards. Playwright is
  NOT installed (`python -m pip list` shows no playwright).
- **MCP** = a connected MCP server tool reached through `ToolSearch "select:<tool>"`.
- **Manual export** = the owner opens the page, screenshots/exports, and drops the file into
  `runs\<run-id>\90-postgen\trend-inputs\`.

Local tooling verified 2026-09-16: `yt-dlp 2026.8.19`, `requests 2.34.2`, Python 3.12.10,
ffmpeg 9.0.1 (libass/libfreetype/libharfbuzz/libx264/libvidstab enabled). `pytrends`, `trendspy`,
`playwright`, `google-api-python-client` are NOT installed.

---

## 1. Source-by-source evaluation

### 1.1 TikTok Creative Center — Trend Discovery (hashtags, songs, creators, videos)

| | |
|---|---|
| What it gives | First-party TikTok trend rankings: **Hashtags** (rank, post count, views, 7-day popularity curve, "new to top 100", industry tag, top creators), **Songs** (rank, title, artist, popularity curve, "Approved for business use" flag — flag existence recalled from prior use, **unverified** this session), **Creators** (follower/like growth), **Videos** (trending videos last 30 days). Filters: region (US), period, industry (e.g. Beauty & Personal Care, Apparel & Accessories, Food & Beverage, Household Products, Home Improvement…). Period options reported as 7 / 30 / 120 days by TikTok-guide sites and 7 / 30 / 180 by an Apify actor — **sources disagree; verify in browser**. |
| URLs | Hashtags: `https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pc/en` · Songs: `https://ads.tiktok.com/business/creativecenter/inspiration/popular/music/pc/en` · Creators: `https://ads.tiktok.com/business/creativecenter/inspiration/popular/creator/pc/en` · Videos: `https://ads.tiktok.com/business/creativecenter/inspiration/popular/pc/en` (creators/videos paths recalled, **unverified**). Region/period/industry are UI state, not query params, so deep links do not pre-filter. |
| WebFetch | **JS shell only** (tested hashtag + music pages: no data in HTML). The internal XHR `https://ads.tiktok.com/creative_radar_api/v1/popular_trend/hashtag/list?page=1&limit=20&period=7&country_code=US&sort_by=popular` returns `{"code":40101,"msg":"no permission"}` without the browser's signed headers (`user-sign`, `timestamp`, `anonymous-user-id` per community write-ups — **unverified**). Other internal paths reported by scrapers (unverified): `/creative_radar_api/v1/popular_trend/sound/rank_list`, `/popular_trend/creator/list`, `/popular_trend/list`. |
| Access from Claude Code | (a) **Browser** via `claude-in-chrome`: open the page, set Region = United States, Period = 7 days, Industry = niche, read the table, screenshot the popularity curves. (b) **Apify** actor `datapeak/tiktok-creative-center` (tested page read): modes `topAds`/`hashtags`/`songs`; inputs `region`, `period` (7/30/180), `industry`, `objective`, `keyword`, `orderBy` (`for_you`/`ctr`/`like`), `maxItems`; pay-per-event **$0.001 per hashtag/song record, $0.0015 per top-ad record**; requires an Apify token + Apify residential proxy. Call: `POST https://api.apify.com/v2/acts/datapeak~tiktok-creative-center/runs?token=<APIFY_TOKEN>` with the JSON input, then `GET https://api.apify.com/v2/datasets/<defaultDatasetId>/items?token=…`. Alternatives on Apify: `automation-lab/tiktok-creative-center-scraper`, `dami_studio/tiktok-creative-center-trends`, `webdata_labs/tiktok-hashtag-trends-scraper`. (c) Manual export. |
| Cost / login | Free, no login for Trend Discovery (login needed for some Top Ads details and for the Commercial Music Library). Apify: paid per record. |
| Refresh | Daily (first-party). |
| Reliability | High as data; **ToS note**: a 2026 guide states scraping Creative Center is a Terms violation where the Creative Center licence applies — the browser path (a human-driven session) or the official APIs are the safe options; Apify use is at the owner's risk. |
| Per niche / platform | TikTok only. Filter Industry + Region=US + Period=7d; for products cross-check the hashtag list against the niche keywords in `20-analysis\entities.json`. |

### 1.2 TikTok Creative Center — Top Ads and Keyword Insights

| | |
|---|---|
| What it gives | **Top Ads**: best-performing TikTok ads by region/industry/objective/period sorted by reach, CTR, likes; per-ad video, CTR tier, spend tier, landing page, "creative keywords". **Keyword Insights**: ad-copy keywords ranked by popularity/CTR per industry and region (script hooks). |
| URLs | Top Ads: `https://ads.tiktok.com/business/creativecenter/inspiration/topads/pc/en` (the shorter `/creativecenter/topads/pc/en` returned **404** on 2026-09-16). Keyword Insights: `https://ads.tiktok.com/business/creativecenter/keyword-insights/pc/en` (WebFetch returned a marketing page, i.e. it redirected; the real tool is JS-rendered). |
| WebFetch | JS shell / redirect. |
| Access | Browser (best), Apify `datapeak/tiktok-creative-center` mode `topAds` with `keyword`/`industry`/`orderBy=ctr`, or manual export. Some ad details require a TikTok for Business login. |
| Cost | Free in browser; Apify $0.0015/ad. |
| Refresh | Daily. |
| Reliability | High (first-party). |
| Per niche | Industry filter + keyword search (product name, category); read the top 10 hooks (first 2 s) and captions — feed into the trend brief "hooks" section. |

### 1.3 TikTok Commercial Music Library (CML)

| | |
|---|---|
| What it gives | ~1M pre-cleared tracks + SFX usable by Business accounts for organic AND paid TikTok content; filters: region, usable placements, themes, genre, mood, duration, "Usable for Business". |
| URLs | `https://ads.tiktok.com/business/creativecenter/music/pc/en` (WebFetch on 2026-09-16 redirected to a Symphony Creative Studio marketing page — the library itself renders only in a logged-in browser). Help: `https://ads.tiktok.com/help/article/commercial-music-library?lang=en`, `https://ads.tiktok.com/help/article/how-to-use-the-commercial-music-library`. In-app: Business account → Add sound → Commercial sounds. |
| Access | Browser (TikTok for Business login) or **Higgsfield MCP `tiktok_music_trending`** (see 1.10) once a TikTok account is connected. |
| Cost | Free with a TikTok Business account. Some tracks are labelled Premium and may carry a fee when attached to ad inventory (reported by licensing blogs, **unverified**). |
| Licence scope | **TikTok only.** The CML licence does not cover re-posting the same video with that track to Instagram/YouTube/broadcast. |
| Per niche | Filter by mood/genre matching the style profile; there is no keyword search in the MCP version (genre/country/date-range only). |

### 1.4 Instagram Reels — trending audio / formats

| | |
|---|---|
| What it gives | Instagram exposes trends only inside the app: (1) **Professional Dashboard → Tips and resources → Trending audio** (US professional accounts only; curated list). (2) Music sticker → **Trending** tab (top ~50 sounds, refreshed every few days). (3) Upward-arrow icon next to a Reel's sound name = trending. (4) `@creators` account weekly trend posts. |
| API | Instagram Graph API has **no trending endpoint**. Useful per-niche proxy: hashtag search `GET https://graph.facebook.com/v20.0/ig_hashtag_search?user_id=<IG_USER_ID>&q=<niche>&access_token=…` then `GET /<hashtag-id>/top_media?user_id=…&fields=id,media_type,permalink,caption,like_count,comments_count,timestamp` (needs an IG Business/Creator account linked to a Facebook Page + app token; cap of 30 unique hashtags per 7 days — from Graph API docs as recalled, **unverified** this session). |
| WebFetch | instagram.com is not fetchable (login wall). |
| Access | Browser (owner's logged-in IG web session does NOT show Professional Dashboard trending audio — that is app-only → **manual screenshot** from the phone), Graph API with token, or third-party weekly roundups (1.13). |
| Cost | Free. |
| Refresh | Trending tab: every few days; roundups: weekly. |
| Reliability | Medium (curated, no numbers). |
| Music for business accounts | Business accounts are restricted to the **Meta Sound Collection** (`https://www.facebook.com/sound/collection`, also via Meta Business Suite → All tools → Sound Collection): royalty-free, cleared for commercial use on Facebook/Instagram/Messenger/Audience Network, downloadable. Trending mainstream songs are available to personal/creator accounts for organic posts only. |

### 1.5 YouTube — Trending, Charts, Data API, yt-dlp

| | |
|---|---|
| Trending page | **Discontinued 21 July 2025.** Replaced by category charts (music, podcasts, trailers, gaming) at `https://charts.youtube.com/charts/TrendingVideos/us` — WebFetch sees only a JS shell; browser needed. No general or Shorts trending list exists anymore. |
| Data API v3 | `GET https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics,contentDetails&chart=mostPopular&regionCode=US&videoCategoryId=<id>&maxResults=50&key=<YOUTUBE_API_KEY>` — **1 quota unit**, 10,000 units/day per key. Since 21 July 2025 `mostPopular` returns videos from the Trending Music/Movies/Gaming charts, not general trending (revision history quoted verbatim in this session). **No Shorts filter** exists; infer Shorts by `contentDetails.duration` ≤ PT3M and vertical thumbnails, or test whether `https://www.youtube.com/shorts/<id>` serves without redirect. Per-niche discovery: `GET https://www.googleapis.com/youtube/v3/search?part=snippet&q=<niche>&type=video&videoDuration=short&order=viewCount&publishedAfter=<ISO-8601 7 days ago>&regionCode=US&relevanceLanguage=en&maxResults=50&key=…` — **100 units per call** (`videoDuration=short` = under 4 min). Key setup: Google Cloud Console → enable "YouTube Data API v3" → Credentials → API key; store as env var `YOUTUBE_API_KEY`. |
| yt-dlp (free, verified) | Hashtag Shorts feed works: `yt-dlp --flat-playlist --playlist-end 50 --no-warnings --print "%(title)s | views=%(view_count)s | %(webpage_url)s" "https://www.youtube.com/hashtag/<tag>/shorts"` (tested with `skincare`: returned 5 Shorts with view counts 1.9M–51M). Keyword search works: `"ytsearch50:<niche> shorts"` (tested). `ytsearchdate50:` **failed** on yt-dlp 2026.8.19 (`Unsupported url scheme`) — reason unknown; use `ytsearch` + sort by `upload_date` from `-j` output instead. Gotcha: piping `-j` through PowerShell adds a UTF-8 BOM that breaks `json.loads` — run yt-dlp from Python `subprocess` with `encoding='utf-8-sig'`, or `--print-to-file`. TikTok tag pages via yt-dlp **fail** ("No working app info is available"). |
| Cost | Data API free within quota; yt-dlp free. |
| Refresh | Live. |
| Reliability | High (API), medium (yt-dlp — extractor breaks occasionally; keep it updated with `python -m pip install -U yt-dlp`, needs approval). |

### 1.6 Google Trends

| | |
|---|---|
| What it gives | Search-interest curves per keyword (web / YouTube / shopping property), related & rising queries, US "Trending Now" list with approximate volume — good for niche demand and for naming hooks with rising terms; not a video-format source. |
| Readable via WebFetch (verified) | Trending Now page: `https://trends.google.com/trending?geo=US&hours=24` (hours ∈ 4/24/48/168; the page listed terms + volumes; the `category=` query param is **ignored** by a plain fetch — the category dropdown is client-side). RSS: `https://trends.google.com/trending/rss?geo=US` (title, approx_traffic, pubDate, news items — verified). Category picker JSON: `https://trends.google.com/trends/api/explore/pickers/category?hl=en-US&tz=240` (verified; strip the `)]}'` prefix). |
| Category IDs (verified from the picker) | 44 Beauty & Fitness · 143 Face & Body Care · 146 Hair Care · 94 Fitness · 185 Fashion & Style · 71 Food & Drink · 45 Health · 11 Home & Garden · 158 Home Improvement · 1175 Roofing · 66 Pets & Animals · 18 Shopping · 12 Business & Industrial · 47 Autos & Vehicles · 65 Hobbies & Leisure · 3 Arts & Entertainment. |
| Internal endpoints (need a cookie session → Python, not WebFetch) | `GET /trends/api/explore?hl=en-US&tz=240&req={"comparisonItem":[{"keyword":"<kw>","geo":"US","time":"now 7-d"}],"category":<id>,"property":""}` → widget tokens → `GET /trends/api/widgetdata/multiline?token=…&req=…`, `/widgetdata/comparedgeo`, `/widgetdata/relatedsearches`. Trending Now: `POST /_/TrendsUi/data/batchexecute?rpcids=i0OFE&source-path=/trending` with `f.req=[[["i0OFE","[null,null,\"US\",0,\"en-US\",24]",null,"generic"]]]`. Needs the `NID` cookie from a prior `GET https://trends.google.com/`; ≥2 s between calls; 429 on bursts. All responses are prefixed with `)]}'\n`. |
| Libraries | **pytrends is dead** (repo archived April 2025, last PyPI 4.9.2 from 2023; fails with 429 on first call). Use **`trendspy`** (`pip install trendspy`; `from trendspy import Trends; tr=Trends(); tr.trending_now(geo='US')`, `tr.interest_over_time(['snail mucin'], geo='US', timeframe='now 7-d', cat=143)`, `tr.related_queries(...)`, `tr.categories()`, `tr.geo()`; README verified, release date not visible). Google's official Trends API is an application-gated alpha (announced 24 July 2025). Paid fallbacks: SerpApi `google_trends` / `google_trends_trending_now` engines. |
| Cost | Free (rate-limited). |
| Refresh | Trending Now: hourly-ish; interest data: daily. |
| Reliability | Medium (unofficial endpoints; expect occasional 429 — back off 5→10→20 s). |

### 1.7 Tokboard

DNS lookup for `tokboard.com` failed on 2026-09-16 (`ENOTFOUND`). Treat as **offline/defunct**; do not include in the procedure.

### 1.8 Tokchart

| | |
|---|---|
| What it gives | Daily TikTok trending-sound chart (score, artist, countries where trending), monthly charts, per-sound pages. |
| URLs | `https://tokchart.com/` (readable via WebFetch: top ~5 sounds free, remaining rows locked), `https://tokchart.com/dashboard/tiktok-trending-sounds`, `https://tokchart.com/dashboard/charts/monthly/<month-year>`, `https://tokchart.com/dashboard/tiktok-sound/<sound-id>`. |
| Cost | Free top-5 only; Pro $14.99/mo (weekly refresh), Business $59/mo (daily), Discovery $149/mo. |
| Refresh | Daily ("last updated September 16, 2026" on the day of testing). |
| Reliability | Medium; global chart with country flags — the free view is **not US-filtered**. |
| Per niche | None (sound chart only). Use to confirm a sound's momentum. |

### 1.9 Chartmetric

Music-industry analytics (Spotify/Apple/TikTok/YouTube/Instagram per artist/track). Free tier shows up to 5 TikTok tracks per artist page; TikTok trend curves (28-day) need Premium; daily refresh; API exists (`https://builder-api.chartmetric.com/apidoc/`) but pricing is not public. Login required; no WebFetch path. **Low priority** for niche video trends — use only to validate a specific sound's trajectory when the owner already has an account. Soundcharts has an equivalent TikTok API (`developers.soundcharts.com`).

### 1.10 Higgsfield MCP `tiktok_music_trending` (TikTok Commercial Music Library via API)

| | |
|---|---|
| Schema (loaded 2026-09-16) | Required `connector_id` (uuid from `tiktok_accounts`); optional `country_code` (default US), `date_range` ∈ `1DAY/7DAY/30DAY/90DAY` (default 7DAY), `genre` ∈ `ALL, POP, HIP_HOP/RAP, LO-FI, EDM, COUNTRY, K-POP, CHILL_BEATS, EPIC` (default ALL), `limit` 1–100 (default 10), `offset`. No keyword search. Read-only. Description: lists trending **commercially licensed** CML tracks with listen links; the chosen track id is passed as `music_sound_id` to `tiktok_publish` (DIRECT_POST only — drafts drop the music). |
| Real call results | `tiktok_accounts` → `{"accounts":[]}` (no TikTok account connected in this Higgsfield workspace). `tiktok_music_trending` with the nil uuid `00000000-0000-0000-0000-000000000000`, `country_code=US`, `date_range=7DAY`, `genre=ALL`, `limit=5` → **error** `Error listing TikTok music: not found` (request id 4387d032-c76b-4581-921d-fd90d85fa34f). The success output shape is therefore **unknown**; expected fields per the description: track id, title/artist, listen URL. |
| To enable | Owner runs `tiktok_connect` (Higgsfield) with the company's TikTok **Business** account, then `tiktok_accounts` returns a `connector_id` with status `active`. |
| Cost | Free with Higgsfield workspace; TikTok CML free. |
| Refresh | TikTok's chart windows (1/7/30/90 days). |
| Per niche | Genre only; niche fit must be judged from the style profile. |

Related Higgsfield read tools worth wiring into the post-generation stage: `virality_predictor` (`action:"create"`, `params.model:"virality_predictor"`, `params.medias:[{role:"video", id:<media_id>}]`) on the rendered final; `video_analysis_create/status` on the sample.

### 1.11 Splice MCP (`describe_a_sound`, `prompt_to_stack`) — sound sourcing, not a trend source

| | |
|---|---|
| `describe_a_sound` | Inputs: `query` (natural language), `type` ∈ `loop`/`oneshot`, `bpm_min`, `bpm_max`. Verified output (query "short whoosh transition swipe sound effect for video cut", type oneshot): "Showing 10 of 15672 total results", each with file name, BPM/key when present, duration, type, pack, tags, `https://splice.com/sounds/sample/<hash>/<slug>` link and an **Asset UUID** (used by `download_asset`). |
| `prompt_to_stack` | Inputs: `prompt` (include target BPM), `bpm_min` + `bpm_max` (together), `generate_public_url`. Returns a multi-track arrangement (drums/bass/keys…) of harmonically matched samples — use to build an original licence-safe music bed matching a trending sound's tempo/mood instead of using the trending sound in paid ads. Do not call both tools for the same request (per tool docs). One-shots cannot seed stacks. |
| Licence | Splice samples are royalty-free for use in productions including commercial ones under Splice's terms (general knowledge — confirm the current Splice licence text before an ad campaign). |

### 1.12 Ad-spy tools and ad libraries

| Source | What it gives | Access from Claude Code | Cost (2026, from vendor/comparison pages; may change) |
|---|---|---|---|
| **Meta Ad Library (web UI)** | Every active Meta ad by keyword/advertiser/country, media type filter, start date, platforms. URL pattern: `https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=US&q=<keyword>&search_type=keyword_unordered&media_type=video` | WebFetch → **HTTP 403** (bot block). Browser (`claude-in-chrome`) works without login for browsing. | Free |
| **Meta Ad Library API** | `GET https://graph.facebook.com/v20.0/ads_archive?search_terms=<kw>&ad_reached_countries=['US']&ad_type=ALL&fields=…&access_token=…` | Python/requests with a user token. **Scope limitation**: outside the EU only political/issue ads are returned; full commercial ads only for EU-targeted ads (DSA). Needs identity verification (gov-ID, 1–3 days), a developer app, 200 calls/hour. | Free |
| **TikTok Commercial Content API** | Paid-ads transparency data (advertiser, dates, targeting, reach) — **EU ads only** as of the page fetched. Apply at `https://developers.tiktok.com/products/commercial-content-api/` (approval ~2 working days). | Python/requests after approval. | Free |
| **Pipiads** | 50M+ TikTok ads, TikTok Shop product filters, run-duration, UGC tracking. | Login only; manual export. | ~$49/mo; trial 500 credits, 0 detail views |
| **Minea** | Facebook/TikTok/Pinterest ads + product/supplier tracing. | Login only. | from ~$49/mo; free trial 100–250 credits (sources vary) |
| **Foreplay** | Swipe-file / creative-team workflow, Discovery ad library. | Login only. | ~$49/mo (annual); free plan **unknown** |
| **Kalodata** | TikTok Shop analytics: product GMV, creators, videos, LIVE by market. Pricing page returns 403 to WebFetch. | Login only; manual export. | ~$45.90/mo (comparison sites); free tier unknown |
| **AdMapix / BigSpy / WinningHunter** | Cheaper spy tools mentioned in comparisons (AdMapix ~$9.9/mo). | Login only. | paid |

Free path that covers 80 % of ad-spy needs for this pipeline: TikTok Creative Center Top Ads (browser) + Meta Ad Library UI (browser) + yt-dlp Shorts listing.

### 1.13 Weekly trend roundups (WebFetch-readable) — Later, Buffer, HeyOrca, Hootsuite

| Source | URL | Verified readability (2026-09-16) | Cadence |
|---|---|---|---|
| **Later — Reels trends** | `https://later.com/blog/instagram-reels-trends/` | **Readable**: trend name, format, how-to-use, audio name (e.g. "Rapid-fire recap" / Milkshake – Kelis; "Leg swipe transition" / TiK ToK – Kesha). Last updated 11 Sep 2026. | Weekly (Thursdays) |
| **Buffer — trending Instagram sounds** | `https://buffer.com/resources/trending-audio-instagram/` | **Readable**: sound, artist, trend name, suggested content type. Updated 3 Sep 2026. No licensing notes. | ~Monthly |
| **HeyOrca — trending audio TikTok + Reels** | `https://www.heyorca.com/blog/trending-audio-for-reels-tiktok` | **Partly readable**: text present, but sound names live in embedded posts. Updated 11 Sep 2026. | Weekly (Fridays) |
| **Hootsuite — Instagram trends** | `https://blog.hootsuite.com/instagram-trends/` | Readable but **annual** (Aug 2025) — strategy-level only. | Yearly |
| **TikTok "What's Next 2026"** | `https://ads.tiktok.com/business/en-US/next-trends-report` | Not fetched; themes reported: "Irreplaceable Instinct" — Brand Fusion, Identity Osmosis, Creative Catalysts. Macro-level only. | Yearly |
| Others seen in search (unverified) | SocialPilot Reels trends, ScottSocial "50+ trending Reels audio this week", heytrendy.app | — | weekly |

### 1.14 CapCut trending templates (format / transition / effect trends)

| | |
|---|---|
| What it gives | Template names, usage/view counts, duration, category — a direct read on which cut patterns, transitions and text-animation styles are circulating (many TikTok/Reels formats start as CapCut templates). |
| URLs | Hub `https://www.capcut.com/templates` (**readable via WebFetch**: names, view counts, durations, categories). Category pages `https://www.capcut.com/template/<category>` (social, holiday, calendar, anniversary, record, effects, industry, business, insights, others). Detail `https://www.capcut.com/template-detail/<slug>/<template-id>`. Search URL pattern not verified. |
| Cost / login | Free, no login to browse. |
| Refresh | Continuous. |
| Reliability | Medium — counts are global, not US-only; template names are noisy. |
| Per niche | Read `/template/business` and `/template/effects`; grep names for niche words; note the durations (most trending templates are 6–20 s → informs pacing). |

### 1.15 In-app "manual export" sources (no API, high signal)

- TikTok app → Search → **Trending** tab, and TikTok Creative Center in-app "Trends" (Business accounts).
- Instagram app → Professional Dashboard → **Trending audio** (US professional accounts); Reels → music sticker → Trending.
- YouTube app → Shorts feed for the niche hashtag (`youtube.com/hashtag/<tag>/shorts` also works logged-out — see 1.5).
- Owner drops screenshots into `runs\<run-id>\90-postgen\trend-inputs\`; the trend agent reads them with the Read tool (images are supported).

---

## 2. Ranked default trend-research procedure (run-time trend agent)

Inputs from the run folder: niche keywords + product category (`20-analysis\entities.json`, `30-decisions\product-spec.md`), target platform(s) and aspect (`30-decisions\answers.json`), the original video's sound/caption/effect profile (`20-analysis\style-profile.md`, `audio.md`), and the deliverable type (organic vs. paid ad — decides the music rule).

Every item written to the brief carries `source`, `url`, `fetched_at` (ISO, local time) and `license` (see §3).

**Tier 0 — zero-cost, always run (parallel, ~2–4 min):**

1. **YouTube per-niche Shorts sample** (yt-dlp): for each of 3–5 niche tags run the `hashtag/<tag>/shorts` listing (top 50) and `ytsearch50:<niche> shorts`; keep the 10 highest `view_count` published in the last 30 days (`upload_date` from `-j`). Extract hooks from titles, hashtags from titles, and note durations. If `YOUTUBE_API_KEY` is set, add one `search.list` call (`videoDuration=short&order=viewCount&publishedAfter=<7d>`).
2. **Google Trends**: WebFetch the RSS (`/trending/rss?geo=US`) and Trending Now page (`hours=168`) for context terms; if `trendspy` is installed, `interest_over_time` + `related_queries` (rising) for the niche keywords with the matching category id (table in 1.6). Flag rising terms as hook-text candidates.
3. **Weekly roundups**: WebFetch Later, Buffer, HeyOrca (in that order); collect every sound/format whose description matches the niche or the original video's format; record artist + platform + trend name.
4. **CapCut templates**: WebFetch the hub + `/template/business` and `/template/effects`; collect the 10 most-viewed templates ≤ 20 s and their implied cut/transition patterns.
5. **Tokchart free top-5** (sound momentum check only).

**Tier 1 — first-party dashboards via browser (`claude-in-chrome`), run when the skill is available and the owner allows it (~5 min):**

6. **TikTok Creative Center Trend Discovery**: Region US, Period 7 d, Industry = niche → Hashtags (top 20 + "new to top 100"), Songs (top 20, note "approved for business use"), Videos (top 10: read format, hook, caption style, effects). Screenshot each table into `90-postgen\trend-inputs\`.
7. **TikTok Top Ads**: Industry = niche, Region US, sort by CTR, period 7–30 d → top 10 hooks, caption styles, CTA patterns.
8. **Meta Ad Library**: keyword = product category, country US, media_type video, active → 10 competitor ads; note formats and text overlays.
9. **CML** (if the deliverable is a paid TikTok ad): search by mood/genre with "Usable for Business" → 3 candidates.

If the browser is unavailable: ask the owner for screenshots (1.15) or skip Tier 1 and mark the brief `coverage: tier0-only`.

**Tier 2 — paid / connected APIs, only when credentials exist:**

10. Higgsfield `tiktok_music_trending` (after `tiktok_connect`), US, 7DAY, genre from the style profile → licensed sound candidates with listen links.
11. Apify `datapeak/tiktok-creative-center` when `APIFY_TOKEN` is set and the owner accepted the ToS risk — replaces steps 6–7 without a browser.
12. Kalodata / Pipiads / Minea exports (owner-provided) for TikTok Shop product niches.
13. Chartmetric / Tokchart Pro for sound trajectory confirmation.

**Fallback rules:** a source that errors twice is skipped and listed under "Sources not reached" in the brief; Tokboard is never called; if no commercially licensed trending sound is found for a paid deliverable, the brief recommends (a) a CML/Meta Sound Collection track of the same tempo/mood, or (b) an original bed built with Splice `prompt_to_stack` at the trending sound's BPM, or (c) ElevenLabs sound/music generation — and says so explicitly. Never present a personal-library trending sound as usable for an ad.

**Output:** `runs\<run-id>\90-postgen\trend-brief.md` in the fixed format `references\trend-brief-template.md`, plus `trend-brief.json` (same fields, machine-readable) so the edit-plan can reference sound/caption choices by id.

---

## 3. Music licensing note (ads vs. organic)

| Use case | TikTok | Instagram / Facebook | YouTube Shorts |
|---|---|---|---|
| Organic post from a **personal/creator** account | Full general sound library incl. trending mainstream songs | Full music library (trending songs) | In-app Shorts audio picker (song remixes allowed on Shorts only) |
| Organic post from a **business** account | **Commercial Music Library only** (enforcement tightened 25 July 2025 for any account with commercial purpose) | **Meta Sound Collection only** (royalty-free catalogue), or independently licensed music | YouTube Audio Library or licensed music |
| **Paid ad** (Spark Ads, in-feed, Reels ads, Shorts ads) | CML tracks (Premium ones may add a fee) or your own licence; trending personal-library sounds are **not** licensed for ads | Meta Sound Collection or your own licence | Licensed music only |
| Cross-posting the same file to several platforms | CML licence is **TikTok-only** | Sound Collection covers Meta apps only | — |

Practical rule for this pipeline: a "trending sound" in the brief is tagged `license: organic-only` unless it was found in the CML "usable for business" list (`license: tiktok-cml`) or the Meta Sound Collection (`license: meta-sound-collection`). For any paid deliverable, the edit uses either a `tiktok-cml` / `meta-sound-collection` track attached **in the platform at publish time** (not baked into the file), or a baked-in bed the company owns/licensed (Epidemic Sound / Artlist / Soundstripe subscription, Splice-built stack, ElevenLabs-generated music or SFX). Keep the licence id / receipt path in `edit-plan.json → audio.license`.

---

## 4. Quick reference — commands that were verified on this machine

```powershell
# PATH refresh first (every PowerShell call)
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')

# YouTube Shorts for a niche tag (works logged-out)
yt-dlp --flat-playlist --playlist-end 50 --no-warnings --print "%(title)s | views=%(view_count)s | %(webpage_url)s" "https://www.youtube.com/hashtag/skincare/shorts"

# Keyword search (ytsearchdate failed on 2026.8.19; sort by upload_date yourself)
yt-dlp --flat-playlist --no-warnings -j "ytsearch50:skincare routine shorts" --print-to-file "%(.{title,view_count,upload_date,duration,webpage_url})j" out.jsonl
```

WebFetch-readable URLs (verified): `https://trends.google.com/trending/rss?geo=US`, `https://trends.google.com/trending?geo=US&hours=168`, `https://trends.google.com/trends/api/explore/pickers/category?hl=en-US&tz=240`, `https://later.com/blog/instagram-reels-trends/`, `https://buffer.com/resources/trending-audio-instagram/`, `https://www.capcut.com/templates`, `https://tokchart.com/`.

Not WebFetch-readable (browser or API needed): all `ads.tiktok.com/business/creativecenter/*` pages, `charts.youtube.com`, `youtube.com/feed/trending` (gone), `facebook.com/ads/library` (403), `kalodata.com/pricing` (403), `instagram.com/*`.

---

## 5. Sources consulted (2026-09-16)

- TikTok Creative Center pages (fetched; JS shells) and `creative_radar_api` probe (40101 "no permission").
- Apify `datapeak/tiktok-creative-center` actor page (pricing, input/output fields).
- TikTok CML help centre articles (`ads.tiktok.com/help/article/commercial-music-library`), Soundstripe / Third Chair / Foxi licensing guides (business-account restrictions, 25 July 2025 enforcement, TikTok-only licence scope).
- Meta Business Help: Sound Collection (`facebook.com/business/help/880459498798521`, `/402084904469945`), `facebook.com/sound/collection`.
- YouTube Data API revision history (10 July 2025 entry on `mostPopular`; 26 March 2025 on Shorts views), `videos.list` reference, YouTube upload encoding recommendations (`support.google.com/youtube/answer/1722171`), TechCrunch/Variety on Trending-page removal.
- Google Trends: dev.to "pytrends is dead… how Google Trends actually loads data in 2026" (endpoints), trendspy GitHub README, Glimpse/Scrapfly alternative round-ups, live RSS/Trending fetches, category picker JSON.
- Tokchart homepage; Chartmetric help centre; comparison pages for Pipiads/Minea/Foreplay/Kalodata pricing (AdLibrary, AdMapix, tool-deals, Minea trial pages).
- Later / Buffer / HeyOrca / Hootsuite trend pages (fetched).
- CapCut templates hub (fetched).
- Safe-zone and LUFS sources are cited in `references\post-generation-playbook.md`.
