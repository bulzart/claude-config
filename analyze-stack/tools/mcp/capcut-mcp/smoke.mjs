// smoke.mjs — end-to-end check of the capcut MCP server over stdio against a SCRATCH drafts folder.
// Usage (PowerShell, CapCut may be open — the scratch folder is not the live store):
//   $S = "$env:TEMP\capcut-smoke"; New-Item -ItemType Directory -Force "$S\drafts" | Out-Null
//   Copy-Item "$env:LOCALAPPDATA\CapCut\User Data\Projects\com.lveditor.draft\_analyze-stack-template" "$S\drafts\_analyze-stack-template" -Recurse -Force
//   node "C:\Users\Glaresquare1\.claude\analyze-stack\tools\mcp\capcut-mcp\smoke.mjs" "C:\Users\Glaresquare1\.claude\analyze-stack\tools\mcp\capcut-mcp\src\server.js" "$S\drafts"
// Expected: initialize → 34 tools → list/read → clone → add_text / transition / keyframes / fade / trim(ripple) → validate ok
// → save refused while CapCut.exe runs (safety check) → save with force:true succeeds in the scratch folder only.
import { spawn } from 'child_process';
const server = process.argv[2], draftsDir = process.argv[3];
if (!server || !draftsDir) { console.error('usage: node smoke.mjs <server.js> <scratch drafts dir>'); process.exit(2); }
if (/com\.lveditor\.draft/i.test(draftsDir)) { console.error('refusing to run against the live CapCut store'); process.exit(2); }
const env = { ...process.env, CAPCUT_DRAFTS_DIR: draftsDir, CAPCUT_TEMPLATE_DRAFT: '_analyze-stack-template' };
const p = spawn('node', [server], { env, stdio: ['pipe', 'pipe', 'pipe'] });
let buf = ''; const pending = new Map(); let id = 0;
p.stdout.on('data', d => { buf += d; let i; while ((i = buf.indexOf('\n')) >= 0) { const line = buf.slice(0, i); buf = buf.slice(i + 1); if (!line.trim()) continue; try { const m = JSON.parse(line); if (m.id != null && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } } catch { console.log('non-json:', line.slice(0, 200)); } } });
p.stderr.on('data', d => process.stderr.write('[server] ' + d));
const send = (method, params) => new Promise(res => { const mid = ++id; pending.set(mid, res); p.stdin.write(JSON.stringify({ jsonrpc: '2.0', id: mid, method, params }) + '\n'); });
const call = async (name, args) => { const r = await send('tools/call', { name, arguments: args }); const t = r.result?.content?.[0]?.text ?? JSON.stringify(r.error); const short = t.length > 600 ? t.slice(0, 600) + ' …' : t; console.log(`\n>>> ${name} ${JSON.stringify(args).slice(0, 160)}\n${short}`); try { return JSON.parse(t); } catch { return t; } };
const init = await send('initialize', { protocolVersion: '2024-11-05', capabilities: {}, clientInfo: { name: 'smoke', version: '0' } });
console.log('initialize:', JSON.stringify(init.result?.serverInfo));
p.stdin.write(JSON.stringify({ jsonrpc: '2.0', method: 'notifications/initialized' }) + '\n');
const tl = await send('tools/list', {}); console.log('tools:', tl.result.tools.length, tl.result.tools.map(t => t.name).join(', '));
await call('capcut_list_drafts', {});
await call('capcut_read_timeline', { draft: '_analyze-stack-template' });
await call('capcut_clone_draft', { base: '_analyze-stack-template', newName: 'smoke-edit' });
const tl2 = await call('capcut_read_timeline', { draft: 'smoke-edit' });
const vseg = tl2.tracks.find(t => t.type === 'video').segments; const first = vseg[0], second = vseg[1] || vseg[0];
const hookTrack = await call('capcut_add_track', { draft: 'smoke-edit', type: 'text', name: 'Hook' });
await call('capcut_add_text', { draft: 'smoke-edit', text: 'HOOK TEST', atSec: 0.2, durSec: 2.5, fontSize: 22, color: '#ffd400', posY: 0.55, trackIndex: hookTrack.trackIndex });
const tr = await call('capcut_list_transitions', { query: 'zoom' });
await call('capcut_add_transition', { draft: 'smoke-edit', segmentId: first.id, name: tr.matches[0], durationSec: 0.3 });
await call('capcut_add_keyframe', { draft: 'smoke-edit', segmentId: second.id, property: 'UNIFORM_SCALE', atSec: second.atSec, value: 1.0 });
await call('capcut_add_keyframe', { draft: 'smoke-edit', segmentId: second.id, property: 'UNIFORM_SCALE', atSec: second.atSec + second.durSec, value: 1.12 });
const atr = tl2.tracks.find(t => t.type === 'audio'); if (atr && atr.segments[0]) await call('capcut_add_audio_fade', { draft: 'smoke-edit', segmentId: atr.segments[0].id, fadeInSec: 0.05, fadeOutSec: 0.15 });
await call('capcut_trim_segment', { draft: 'smoke-edit', segmentId: first.id, durSec: Math.max(1, first.durSec - 0.5), ripple: true });
await call('capcut_validate', { draft: 'smoke-edit' });
console.log('\n=== save WITHOUT force (refused while CapCut.exe runs = correct) ===');
await call('capcut_save', { draft: 'smoke-edit' });
console.log('\n=== save WITH force (scratch folder only) ===');
await call('capcut_save', { draft: 'smoke-edit', force: true });
await call('capcut_read_timeline', { draft: 'smoke-edit' });
console.log('\nThen: capcut register "<scratch>\\smoke-edit" --materials -H ; capcut sync-timelines "<scratch>\\smoke-edit" --nested ; capcut lint "<scratch>\\smoke-edit" -H');
p.stdin.end(); setTimeout(() => process.exit(0), 300);
