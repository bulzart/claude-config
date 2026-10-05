# clip-qa — agent brief (Stage 9a; one agent per generated clip / edited segment, in parallel)

Load first: `LAYOUT.md`, `references\clip-qa-template.md` (evidence, section format, qa.json, P0 placeholders),
`references\post-generation-playbook.md` §2 (check order, anomaly taxonomy A01–A15, severity S0–S4, decision
rule), `references\fix-prompt-template.md`, `references\physics-rules.md` §12 (what a correct frame shows),
`references\blending-rules.md` §2 #20 (no original brand marks), and the **Seedance 2.5 Director** bundle (read-only):
`seedance\director\references\quality-and-iteration.md` §12 (inspect the FULL temporal sequence; the defect record
`timestamp | observed failure | violated requirement | possible cause | one proposed change | pass condition`;
change the smallest coherent set of dependent instructions; regenerate the full prompt, never a patch),
`seedance\director\assets\review-record.md` (pass / fail / unknown — an unknown is never a pass; stills cannot
certify motion or lip sync).

## Purpose
Compare ONE generated clip, frame by frame, against its prompt and its neighbours' boundary states;
flag every anomaly with an id, a severity and a time window; decide use / trim / regenerate / drop; and
write a ready-to-paste fix prompt when regeneration is needed. Shorter and clean beats longer with anomalies.

## Inputs
`80-generated\clip-NN.mp4` (or `seg-NN.mp4` + the source `00-input\segments\seg-NN.mp4` for the edit approach),
`80-generated\manifest.json`, `50-prompts\clip-NN.md` / `edit-NN.md`, `40-plan\continuity-sheet.md` (your row and
neighbours), `30-decisions\product-spec.md` + `swap-map.md` (identity, label text, removal rule),
`90-postgen\qa\clip-<NN±1>\first-*.jpg|last-*.jpg` when the neighbours' QA already ran (else extract them yourself with `clip_frames.py`).

## Outputs
`90-postgen\qa\clip-NN\` evidence (`first-00m00.00s.jpg`, `last-<t>.jpg`, `f-<MMmSS.ffs>.jpg` at 1 fps, `sheet.jpg`,
`frames.json` — written by `clip_frames.py`; plus `detect.txt` from the ffmpeg detectors),
`90-postgen\qa\clip-NN\qa.md` (the clip's section in the template format), `90-postgen\qa\clip-NN\qa.json`
(`{"prompt_no":3,"file":"80-generated/clip-03.mp4","severity":"S3","anomalies":["A05","A09"],"windows":[{"t_in":0.0,"t_out":4.2,"verdict":"clean"},…],"action":"regenerate|trim|use|drop","fix_prompt":"90-postgen/qa/clip-03/fix.md"}`),
`90-postgen\qa\clip-NN\fix.md` (fix-prompt-template block; only when action = regenerate or S3/S4).
The main session merges these into `90-postgen\clip-qa.md`, `qa.json`, `fix-prompts.md`.

## Method
1. Evidence: `python C:\Users\Glaresquare1\.claude\analyze-stack\tools\clip_frames.py "<clip>" --out "<run>\90-postgen\qa\clip-NN" --fps 1`
   (writes `first-*.jpg`, `last-*.jpg`, `f-*.jpg`, `sheet.jpg`, `frames.json`); then the detectors into `detect.txt`
   (playbook §2.1: `select='gt(scene,0.35)',showinfo`, `freezedetect=n=-60dB:d=0.5`, `blackdetect=d=0.2:pic_th=0.98`,
   captured with `Start-Process … -RedirectStandardError`). Fallback when the script is absent: the playbook's
   ffmpeg lines (`fps=1,scale=540:-2`, first/last frame, `tile=5x4` sheet) and ffprobe JSON.
2. LOOK at `sheet.jpg`, then `first-*.jpg`, `last-*.jpg`, then every `f-*.jpg` in order (Read tool); keep the
   prompt open side by side; for labels crop/zoom by extracting a full-res frame at that second
   (`-ss <t> -frames:v 1 -update 1`) and optionally OCR it.
3. Fill the fixed rows in order: Subjects, Product identity (label text vs `product-spec` verbatim; A05/A15),
   Action order, Camera, Lighting, On-screen text (only what was prompted; A06), Audio (ffprobe streams; if
   speech was not prompted and a voice is audible per a quick transcription, A10), Duration/aspect (A11),
   Continuity (your `last-*.jpg` vs the next clip's `first-*.jpg`; your `first-*.jpg` vs the previous `last-*.jpg`; A09).
   Edit approach adds: `Stays-as-filmed` (person, motion, camera, other props unchanged vs the source segment
   frames — extract the same 1 fps frames from `00-input\segments\seg-NN.mp4` and compare pairwise) and
   `Original brand marks` (A15, reflections included).
4. Windows: list clean and faulty time windows; severity per the scale; action per the default rules
   (S2 confined ≤ 25 % → trim with ≥ 1.5 s left; S3 → regenerate or drop if not a hero clip; S4 → drop).
5. Fix prompt (when needed): the full corrected prompt with changed lines marked `✱`, positive phrasing,
   keep what passed, seed "unknown" on Higgsfield, the neighbour's boundary frame as a reference for
   continuity faults, platform line and attachments; edit approach: tighten the `Replace only …` scope / add
   a timestamp window / an anchor still. No captions anywhere.
6. Director discipline: every anomaly row carries the six-field defect record (timestamp, observed failure,
   violated requirement = the prompt line, possible cause marked as hypothesis, one proposed change, pass
   condition); criteria you could not inspect at 1 fps (motion smoothness, lip sync, audio timing) are
   `unknown`, never `pass` — extract at 4–8 fps around the suspect window (`clip_frames.py --fps 6` on a trimmed
   copy) before calling a motion fault S3. Fix prompts change the smallest coherent set of dependent lines and
   are regenerated as a FULL prompt.
7. Write the three files; return the summary line (`clip 03: S3 A05 label drift 4.2–12.0 s → regenerate`).

## Quality bar
- Every anomaly names a frame file and a time window; no "looks off".
- Product identity is judged against the spec's label text and images, not memory.
- The verdict follows the decision rule; the fix prompt is complete and pasteable.

## When evidence is missing
Missing clip → `MISSING` section and `action:"missing"`. No neighbour frames yet → extract them from the
neighbour clip if it exists, else mark the continuity row "pending (neighbour missing)". Audio you cannot
verify → "not verified (no transcription run)"; never claim silence without ffprobe.
