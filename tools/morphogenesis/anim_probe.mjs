// ANIMATION PROBE — run ANY lab rule and emit a time-filmstrip (K snapshots across the run) + a
// motion score, so a swarm agent can SEE the dynamics and judge how unique the animation is.
//   node tools/morphogenesis/anim_probe.mjs <tag> <ruleId> <warmup> <totalSteps> [K]
//   env: GEN_PARAMS='{"k":v,...}'  FF=<F> KK=<k>  SCAT=<n>   (optional)
import fs from 'fs';
import zlib from 'node:zlib';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
globalThis.window = globalThis; globalThis.CA = { RULES: {} };
const ev = (0, eval);
ev(fs.readFileSync(`${ROOT}/docs/web8/experiment/viridis.js`, 'utf8'));
ev(fs.readFileSync(`${ROOT}/docs/web8/experiment/sprites.js`, 'utf8'));
ev(fs.readFileSync(`${ROOT}/docs/web8/experiment/sem.js`, 'utf8'));
const A = process.argv, tag = A[2], ID = A[3], warmup = +A[4] || 0, total = +A[5] || 360, K = +A[6] || 6;
ev(fs.readFileSync(`${ROOT}/docs/web8/experiment/rules/${ID}.js`, 'utf8'));
const key = ID.replace('natural_selection', 'natural-selection');
const g = CA.RULES[key]();
if (process.env.GEN_PARAMS) { const o = JSON.parse(process.env.GEN_PARAMS); for (const k in o) if (g.params && g.params[k]) { g.params[k].value = o[k]; if (g.onParamChange) { try { g.onParamChange(k); } catch (e) {} } } }
if (process.env.FF && g.params && g.params.F) g.params.F.value = +process.env.FF;
if (process.env.KK && g.params && g.params.k) g.params.k.value = +process.env.KK;
const W = g.width, H = g.height;
g.reset();
if (process.env.SCAT && g.paint) { function mul(a){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};} const rng=mul(987); for (let i=0;i<+process.env.SCAT;i++) g.paint((rng()*W)|0,(rng()*H)|0,4,'paint'); }
const pop0 = g.population ? g.population() : '';
for (let i = 0; i < warmup; i++) g.step();
const px = new Uint8ClampedArray(W * H * 4), snaps = [], per = Math.max(1, (total / K) | 0);
for (let s = 0; s < K; s++) { for (let i = 0; i < per; i++) g.step(); g.render(px); snaps.push(Uint8Array.from(px)); }
const popN = g.population ? g.population() : '';
let motion = 0;
for (let s = 1; s < K; s++) { let d = 0; const a = snaps[s - 1], b = snaps[s]; for (let i = 0; i < a.length; i += 4) d += Math.abs(a[i] - b[i]) + Math.abs(a[i + 1] - b[i + 1]) + Math.abs(a[i + 2] - b[i + 2]); motion += d / (a.length / 4 * 3); }
motion = +(motion / (K - 1)).toFixed(2);
// filmstrip: K snapshots left->right
const T = 220, MW = T * K, MH = T, img = Buffer.alloc(MW * MH * 4);
for (let s = 0; s < K; s++) {
  const sn = snaps[s], cx = s * T;
  let mx = 1; for (let i = 0; i < sn.length; i += 4) { if (sn[i] > mx) mx = sn[i]; if (sn[i + 1] > mx) mx = sn[i + 1]; if (sn[i + 2] > mx) mx = sn[i + 2]; }
  const sc = Math.min(4, 238 / mx);   // per-snapshot brightness stretch so dim rules (GS) stay legible
  for (let y = 0; y < T; y++) for (let x = 0; x < T; x++) { const sp = (((y * H / T) | 0) * W + ((x * W / T) | 0)) * 4, dp = (y * MW + cx + x) * 4; img[dp] = Math.min(255, sn[sp] * sc); img[dp + 1] = Math.min(255, sn[sp + 1] * sc); img[dp + 2] = Math.min(255, sn[sp + 2] * sc); img[dp + 3] = 255; }
}
const CT = (() => { const t = []; for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++)c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
const crc = (b) => { let c = 0xffffffff; for (let i = 0; i < b.length; i++)c = CT[(c ^ b[i]) & 0xff] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; };
function chunk(ty, d) { const L = Buffer.alloc(4); L.writeUInt32BE(d.length, 0); const T2 = Buffer.from(ty, 'ascii'); const C = Buffer.alloc(4); C.writeUInt32BE(crc(Buffer.concat([T2, d])), 0); return Buffer.concat([L, T2, d, C]); }
const sig = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(MW, 0); ihdr.writeUInt32BE(MH, 4); ihdr[8] = 8; ihdr[9] = 6;
const raw = Buffer.alloc((MW * 4 + 1) * MH); for (let y = 0; y < MH; y++) { raw[y * (MW * 4 + 1)] = 0; img.copy(raw, y * (MW * 4 + 1) + 1, y * MW * 4, y * MW * 4 + MW * 4); }
fs.writeFileSync(`/tmp/anim_${tag}.png`, Buffer.concat([sig, chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]));
fs.writeFileSync(`/tmp/anim_${tag}.json`, JSON.stringify({ tag, id: ID, W, H, K, motion, pop0, popN, filmstrip: `/tmp/anim_${tag}.png (${K} snapshots L->R over time)` }));
console.log(`${tag} [${ID}] motion=${motion} pop:${pop0} -> ${popN} -> /tmp/anim_${tag}.png`);
