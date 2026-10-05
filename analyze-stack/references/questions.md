# Question script (verbatim, fixed order) — used by /analyze-stack

The main session asks these questions itself with the AskUserQuestion tool (never a subagent).
Wording, order and option order are fixed. Fill the `{…}` placeholders from
the run files. Record every answer in `30-decisions\answers.json` (key, question, answer,
timestamp) before moving on. Skip a question only when its condition is not met.

Timing rule: the analysis report (`20-analysis\report.md`) is shown FIRST. Then Q1 is asked
before any other question.

Order: Q1 → (Q1a → Q1b) → Q2 approach → (Q2e edit intent | Q2m mode) → Q3a → Q3b → Q3c →
(Q4a–c, Mode 3) → (Q5, replicate only) → Q6 → [planning approvals A1/A2/A3] → G1 generation →
[after generation] P0 → (P1 when clips were dropped manually) → P2 → P3.

---

## Q1 — product (ALWAYS FIRST after the report)

header: `Product`
question: `What do you want to do with this video? I detected these products and entities: {numbered list: "1. {entity} — {what it is, where it appears, screen time}" … }. Do you want to replace one of them with your product, or keep the video as it is with no product change?`
options (single select):
- if 1–3 swappable entities were detected: one option per entity, label `Replace {entity}`, description `Swap {entity} for our product; every visual, audio and text consequence is worked out across the whole video.`
- if more than 3: the three with the most screen time as options; the rest stay in the numbered list and can be chosen via "Other" by number.
- last option always: label `Keep the video as it is`, description `No product change. Reproduce the video with its original products and entities.`

### Q1a — product samples (only if a swap was chosen)

header: `Samples`
question: `Drop the images and samples of your product in the chat now (file paths or links). If you know them, add the brand, exact product name, label text, variant, size and any product ID. Type "done" when everything is attached.`
options (single select):
- `Attached — identify it` — `I have dropped the images/samples above; identify the exact product from them.`
- `Use my product library` — `Pick the product from the local product library instead of new samples ({list of library entries or "library is empty"}).`

### Q1b — product confirmation (only if a swap was chosen; asked after identification)

header: `Confirm product`
question: `I identified the product as: {brand} {product name} {variant} {size} — label: "{label text}", ID: {id or "none found"}. Key physical properties: {3–6 properties}. Source: {samples / product library / web lookup}. Is this the exact product?`
options (single select):
- `Yes, exact product` — `Save/refresh the product spec sheet in the library and plan the swap.`
- `Almost — I will correct details` — `Tell me what is wrong (brand, variant, size, colour, label…) and I will re-identify.`
- `No — look it up again` — `Search the product library and the web again with the details I give you.`

## Q2 — approach (replicate or Seedance 2.5 edit)

header: `Approach`
question: `How do you want to produce the result? Replicate the video by generating new clips from Seedance 2.5 prompts (full, best-segment or condensed), or edit the original video directly with Seedance 2.5 video editing on Higgsfield: the source video is uploaded through the Higgsfield MCP and edited in place ({"swapping " + entity + " for your product" | "with the edits you describe"}) while everything else stays exactly as filmed.`
options (single select):
- `Replicate with generated clips (default)` — `New clips are generated from prompts that reproduce the video (Modes 1–3), product swapped in if chosen.`
- `Seedance 2.5 edit of the original video` — `The original footage is kept and edited by Seedance 2.5; segments longer than the spec's video-input limit are split, edited with one consistent prompt each and re-joined.`

### Q2e — edit intention (only if Seedance 2.5 edit was chosen)

header: `Edit intent`
question: `What exactly should the Seedance 2.5 edit change in the original video? Product from Q1: {"{entity} → your product" | "no product swap chosen"}. Add anything else to change (remove logos or text, change a colour, swap the setting, restyle, replace another entity) and anything that must stay exactly as filmed. The edit prompt is built with the same blending, physics and continuity logic as a replication.`
options (single select):
- `Only the product swap from Q1` — `Replace {entity} with your product everywhere it appears; nothing else changes.`
- `Product swap plus other edits` — `Describe the extra edits after choosing this.`
- `Other edits only` — `No product swap; describe what to change.`
(If the intent names a product and Q1 was "Keep the video as it is", re-ask Q1 for that entity, then Q1a/Q1b.)

### Q2m — output mode (only if replication was chosen)

header: `Mode`
question: `Which output mode do you want? The original is {duration}s ({n_shots} shots). Mode 1 reproduces it 1:1 as {n_prompts_at_max} prompts of {max_clip_s}s. Mode 2 replicates only the strongest segment(s) 1:1 — I would propose {proposed segments with timestamps and why}. Mode 3 re-cuts the whole story into a shorter version of your chosen length, keeping the same story, characters, style and payoff (anchors can be pinned to be replicated exactly).`
options (single select):
- `Mode 1 — full replication` — `Every second of the original, sliced into consecutive clips, product swapped in if chosen.`
- `Mode 2 — best-segment replication` — `Only the strongest continuous segment(s), replicated 1:1; you confirm or change my proposal.`
- `Mode 3 — condensed remake` — `Same video compressed to a target length via a scored beat map and an approved keep/merge/drop plan.`

## Q3 — duration and seconds per prompt

Spec limits come from `seedance\SEEDANCE-SPEC.md` (generation) and `seedance\SEEDANCE-EDIT.md`
(video editing input limits). Never assume; read them: `{min_clip_s}`–`{max_clip_s}` seconds per
clip, supported values `{supported_clip_lengths}`.

### Q3a — target duration (Mode 2 and Mode 3 only)

header: `Target length`
question: `What target duration do you want for the output, in seconds? (Mode 2: the total length of the kept segment(s). Mode 3: the length of the condensed version.) The original is {duration}s. My recommendation for a fully natural, physically feasible result is {recommended_s}s because {reason}.`
options (single select):
- `{recommended_s}s (recommended)` — `{reason in one line}`
- `{alt_1}s` — `{one-line consequence}`
- `{alt_2}s` — `{one-line consequence}`
(Any other number via "Other".)

### Q3b — seconds per prompt / per edited segment (all approaches)

header: `Clip length`
question: `How many seconds should each Seedance prompt cover? {"For the edit approach this is the length of each source segment uploaded and edited." | ""} Allowed by the saved spec: {supported_clip_lengths} (max {max_clip_s}s). Equal lengths by default. With {target_or_original_duration}s that gives {n} clips at {default_clip_s}s.`
options (single select):
- `{max_clip_s}s (default)` — `{n_at_max} clips; fewest joins, longest continuous takes.`
- `10s` — `{n_at_10} clips; shorter, simpler actions per clip generate more cleanly.`
- `5s` — `{n_at_5} clips; safest per clip, most joins.`
(Other values 5–30 via "Other"; values outside the spec are refused and re-asked.)

### Q3c — uneven lengths (all approaches)

header: `Uneven clips`
question: `May clip lengths be uneven when a beat or shot boundary makes it cleaner (for example 15s + 10s + 15s), or must all clips be equal?`
options (single select):
- `Equal lengths only (default)` — `Every clip has the same duration; the last one may be shorter only if unavoidable.`
- `Uneven allowed` — `Clip boundaries snap to shot/beat boundaries within the spec limits.`

## Q4 — Mode 3 extras (Mode 3 only, asked in this order)

### Q4a — dialogue
header: `Dialogue`
question: `Should dialogue be kept verbatim (only compressed by cutting lines), or may it be paraphrased to fit the time budget?`
options:
- `Verbatim, compressed (default)` — `Only original lines are used; quotable lines survive word for word.`
- `Paraphrase allowed` — `Lines may be shortened or merged while keeping the meaning and tone.`

### Q4b — ending / CTA
header: `Ending`
question: `Must the original ending or CTA be kept as is?`
options:
- `Keep the ending as is (default)` — `The final beat/CTA is replicated exactly.`
- `Ending may be adapted` — `The payoff is kept but may be shortened or reworded.`

### Q4c — anchors
header: `Anchors`
question: `Do you want to pin specific moments as anchors that are replicated exactly while everything around them is compressed? Candidates from the viral analysis: {list "t=mm:ss–mm:ss — what happens — why it matters"}.`
options:
- `No anchors` — `Everything is compressed by the plan.`
- `Use the suggested anchors` — `Pin all the listed candidates.`
- `I will list anchors` — `Give timestamps (mm:ss–mm:ss) and I will pin them.`

## Q5 — style (replication only; for the edit approach a restyle is part of Q2e)

header: `Style`
question: `The original is {style label} ({sub-style summary}). Keep that style, or swap to another style without changing the video's context and content?`
options:
- `Keep the original style (default)` — `{style label} stays {style label}.`
- `Swap to real footage` — `Photoreal live-action look; a style bible will pin the look.`
- `Swap to animation` — `Choose the animation style in the follow-up (anime, 2D cartoon, 3D, claymation, stop motion, pixel art, sketch…).`
(If "Swap to animation": follow-up question `Which animation style?` with options `Anime`, `2D cartoon`, `3D animation`, `Sketch / drawing`; others via "Other" — claymation, stop motion, pixel art, watercolour, comic.)

## Q6 — platform and aspect ratio (all approaches)

header: `Platform`
question: `Which platform and aspect ratio? Default is 9:16 vertical for TikTok, Reels and Shorts, US audience.`
options:
- `TikTok 9:16 (default)` — `1080x1920, hook in the first second, overlays in the safe zone.`
- `Instagram Reels 9:16` — `1080x1920, Reels safe zones and cover frame.`
- `YouTube Shorts 9:16` — `1080x1920, Shorts UI safe zones.`
- `Other ratio` — `Say 16:9, 1:1 or 4:5 and the platform.`

---

## Stage-4 approvals (asked by the main session after planning, before any prompt is written)

### A1 — segment confirmation (Mode 2 only)
header: `Segments`
question: `I propose keeping {segments with timestamps, total {total}s}: {why each}. Confirm or change?`
options: `Confirm`, `Change — I will give timestamps`, `Show alternatives` (offers the next-best set).

### A2 — compression plan approval (Mode 3 only)
header: `Plan`
question: `Here is the keep / merge / drop plan for {target}s ({kept beats} kept, {merged} merged, {dropped} dropped; hook at 0–{hook_s}s, ending preserved: {yes/no}; anchors: {list}). Full plan: 40-plan\compression-plan.md. Approve, or tell me what to change?`
options: `Approve`, `Change — I will describe edits`, `Recommend a shorter target` (re-plans at the recommended length).

### A3 — feasibility warning (any approach, only if the anomaly pre-check flags infeasible shots)
header: `Feasibility`
question: `{n} planned shots are physically risky for generation ({examples}). I recommend {shorter target / simpler split / dropping shot X}. Proceed as planned, or apply the recommendation?`
options: `Apply recommendation`, `Proceed as planned`.

## G1 — generation on Higgsfield (after the anomaly check is clean and the deliverables are written; both approaches)

header: `Generate`
question: `Prompts are final: {n} {clips | edit segments}, {total}s. Generate them now on Higgsfield with Seedance 2.5 through the MCP? {"The source segments will be uploaded and edited in place." | "Reference images and frames will be uploaded and attached."} Estimated cost: {credits} credits (balance {balance}), model {model id from the spec notes}, {resolution}, {aspect}. Nothing is spent before you confirm.`
options (single select):
- `Generate all now` — `Run every clip; results land in 80-generated\ with a manifest, then clip QA.`
- `Generate clip 1 first as a test` — `One clip only; you review it before the rest.`
- `I will generate myself` — `Stop here; drop the generated clips back in the chat later.`

## Post-generation questions

### P0 — edit now? (right after clip QA, both approaches)
header: `Edit now?`
question: `Clip QA done: {n_ok} clean, {n_flag} flagged ({one-line summary}; fix prompts in 90-postgen\fix-prompts.md). Do you want to edit and render the video now (trend boosts, editable project), or stop here with the generated clips?`
options: `Edit now`, `Regenerate flagged clips first`, `Stop here — clips are in 80-generated`.

### P1 — clip mapping (only when the owner dropped clips manually)
header: `Clips`
question: `I found {n} clip(s): {list with durations}. I mapped them to prompts {mapping}. Is the mapping right?`
options: `Yes`, `No — I will give the order`.

### P2 — edit target
header: `Edit in`
question: `The edit is built in CapCut: a registered CapCut 9.4 draft refined through the CapCut MCP, kept fully editable in the app, with the final MP4 rendered by ffmpeg from the same plan. Do you also want another editable format?`
options (single select):
- label `CapCut only (default)`, description `The draft in your CapCut projects list is the project: open it, change anything, and I re-read it through the CapCut MCP for the next render.`
- label `CapCut + timeline export`, description `Also writes an OTIO / FCP7 XML / FCPXML / EDL package for Resolve, Premiere or Final Cut.`
- label `CapCut + Descript project`, description `Also uploads the clips to Descript through its MCP and builds a project there (cloud copies).`
- label `CapCut + all exports`, description `CapCut draft plus the timeline package plus the Descript project.`

### P3 — trend boosts
header: `Boosts`
question: `Trend brief for {niche} on {platform} ({date}): {3-line summary}. Apply which boosts? (Speech captions/subtitles are never added in the edit — you add them afterwards with your caption tool; only non-speech text such as hook overlays, callouts and end cards can be applied here.)`
options (multi select): `Hook text overlay + callouts`, `Trending sound / SFX`, `Transitions + VFX`, `All recommended`.
