// capcut_build.mjs - the whole CapCut project of one Static Studio video in one Node process (capcut_tools.py capcut-build).
//
// It loads the CapCut MCP's own library (core.js: the CapCutDraft code that the MCP's capcut_read_timeline, capcut_add_track,
// capcut_add_image, capcut_add_video, capcut_add_audio, capcut_add_audio_fade, capcut_validate and capcut_save tools call) and
// applies a build plan that capcut_tools.py wrote and checked: every picture, overlay and sound, at the times, on the tracks and
// at the levels the plan gives. It decides nothing: no time, file, level, fade or track is chosen here. The draft is saved once,
// at the end; anything that fails before that leaves the draft as it was.
//
// Two things are written on top of what core.js writes, as the build this replaces did (2026-11-23):
//   * a still's material gets CapCut's own still duration (3 hours) when core.js could not read one (ffprobe has none for a PNG);
//   * every audio clip is in CapCut's own form for a local file (type "extract_music", named after its file): core.js writes
//     type "audio", which CapCut 9.x drops when it opens the project (2026-11-22: every audio track showed empty).
//
// Usage: node capcut_build.mjs <build-plan.json>
// Environment: CAPCUT_MCP_CORE (core.js), CAPCUT_DRAFTS_DIR (the folder that holds the draft and the template) and
// CAPCUT_TEMPLATE_DRAFT (the template's folder name), as the MCP server has them. CapCut must be closed: the save refuses otherwise.
// Prints one JSON object on its last line; exit 0 saved, 1 failed (nothing saved).
import fs from 'fs';
import path from 'path';
import { pathToFileURL } from 'url';

const PHOTO_US = 10800000000;   // what CapCut writes on a still it imports itself (3 hours)

function emit(obj, code) {
  process.stdout.write(JSON.stringify(obj) + '\n');
  process.exitCode = code;
}

const baseName = f => String(f).split(/[\\/]/).pop();
const samePath = (a, b) => path.resolve(a).toLowerCase() === path.resolve(b).toLowerCase();

async function main() {
  const planPath = process.argv[2];
  if (!planPath) throw new Error('usage: node capcut_build.mjs <build-plan.json>');
  const plan = JSON.parse(fs.readFileSync(planPath, 'utf8'));
  const corePath = process.env.CAPCUT_MCP_CORE;
  if (!corePath || !fs.existsSync(corePath)) throw new Error(`the CapCut MCP library is not at ${corePath} (config.json -> capcut.mcp_core)`);
  const { CapCutDraft, DRAFTS_DIR } = await import(pathToFileURL(corePath).href);
  const name = plan.draft_name;
  if (!name || !plan.draft) throw new Error('the build plan names no draft');
  if (name === process.env.CAPCUT_TEMPLATE_DRAFT) throw new Error(`${name} is the template draft: it is never edited`);
  if (!samePath(path.join(DRAFTS_DIR, name), plan.draft)) throw new Error(`core.js works in ${DRAFTS_DIR}, the plan's draft is ${plan.draft}`);

  const d = new CapCutDraft(name);
  const held = d.content.tracks.reduce((k, t) => k + (t.segments || []).length, 0);
  if (held) throw new Error(`the draft already holds ${held} clip(s): only a fresh clone is built`);
  const log = [];
  const matOf = (segId, key) => {
    for (const tr of d.content.tracks) for (const s of (tr.segments || [])) if (s.id === segId)
      return (d.content.materials[key] || []).find(m => m.id === s.material_id);
    return null;
  };
  const asCapCutAudio = (segId, file) => {
    const m = matOf(segId, 'audios');
    if (!m) throw new Error(`no audio material for ${file}`);
    Object.assign(m, { type: 'extract_music', name: baseName(file), category_name: 'local', check_flag: 1 });
  };
  const lanes = {};
  const lane = (type, trackName) => {
    if (lanes[trackName] == null) lanes[trackName] = d.addTrack(type, trackName);
    return lanes[trackName];
  };

  // the pictures: every shot's still on the first video track (the one timeline-write and capcut-motion read), in shot order
  let main = d.content.tracks.findIndex(t => t.type === 'video');
  if (main < 0) main = d.addTrack('video', 'video');
  for (const im of plan.images) {
    const r = d.addImage(im.file, { atUs: im.at_us, durUs: im.dur_us, trackIndex: main });
    const m = matOf(r.segmentId, 'videos');
    if (m && !Number.isFinite(m.duration)) m.duration = PHOTO_US;
    log.push({ kind: 'picture', image: im.image, shot_id: im.shot_id, segmentId: r.segmentId, at: im.at });
  }
  // the drawn overlays, each on its own draw track above the stills
  for (const ov of plan.overlays) {
    const r = d.addVideo(ov.file, { atUs: ov.at_us, durUs: ov.dur_us, trackIndex: lane('video', ov.track), volume: 0 });
    log.push({ kind: 'overlay', id: ov.id, shot_id: ov.shot_id, track: ov.track, segmentId: r.segmentId, at: ov.at });
  }
  // the narration: the edit plan's file at 0 s, at speed 1, untrimmed and whole, on the first audio track
  let voice = d.content.tracks.findIndex(t => t.type === 'audio');
  if (voice < 0) voice = d.addTrack('audio', 'narration');
  {
    const n = plan.narration;
    const r = d.addAudio(n.file, { atUs: 0, durUs: n.dur_us, srcStartUs: 0, trackIndex: voice, volume: 1, speed: 1 });
    asCapCutAudio(r.segmentId, n.file);
    log.push({ kind: 'narration', segmentId: r.segmentId, at: 0 });
  }
  // the beds, then the sound effects, each on its own audio track
  for (const [kind, rows] of [['bed', plan.beds], ['sfx', plan.sfx]]) {
    for (const s of rows) {
      const r = d.addAudio(s.file, { atUs: s.at_us, durUs: s.dur_us, srcStartUs: s.src_start_us || 0,
                                     trackIndex: lane('audio', s.track), volume: s.volume });
      asCapCutAudio(r.segmentId, s.file);
      if (s.fade_in_us || s.fade_out_us) d.addAudioFade(r.segmentId, { fadeInUs: s.fade_in_us || 0, fadeOutUs: s.fade_out_us || 0 });
      log.push({ kind, id: s.id, track: s.track, segmentId: r.segmentId, at: s.at, volume: s.volume,
                 fade_in: (s.fade_in_us || 0) / 1e6, fade_out: (s.fade_out_us || 0) / 1e6 });
    }
  }
  const v = d.validate();
  if (!v.ok) throw new Error('capcut_validate refused the project: ' + v.issues.slice(0, 5).join('; '));
  const saved = d.save({ force: false });
  const tracks = d.content.tracks.map((t, i) => ({ index: i, type: t.type, name: t.name, segments: (t.segments || []).length }));
  emit({ ok: true, draft: plan.draft, name, drafts_dir: DRAFTS_DIR, validate: v, saved, tracks, segments: log }, 0);
}

main().catch(e => emit({ ok: false, error: String((e && e.message) || e) }, 1));
