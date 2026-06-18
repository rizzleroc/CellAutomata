// SEM CINEMATIC PROBE — render a rule's depth-shaded micrograph (warm-sepia or cool-mono) as a
// time-filmstrip so a swarm agent can judge the *documentary* look and pick the best warmup /
// params / frame-window / crop for an award-grade reel. Mirrors gen.mjs's load + param handling.
//   node sem_probe.mjs <tag> <ruleId> <warmup> <total> [K] [palette] [relief]
//   env: GEN_PARAMS (JSON {param:value}), FF, KK, SCAT  (same as gen.mjs)
//   -> /tmp/sem_<tag>.png  (K snapshots left->right = early->late, depth-shaded micrograph)
//   -> /tmp/sem_<tag>.json (W,H,SC,steps[],relief[],label)
import fs from 'fs';
import zlib from 'node:zlib';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');   // repo root, cwd-independent
globalThis.window = globalThis; globalThis.CA = { RULES: {} };
const ev = (0, eval); const load = p => ev(fs.readFileSync(p, 'utf8'));
load(ROOT + '/docs/web8/experiment/viridis.js'); load(ROOT + '/docs/web8/experiment/sprites.js'); load(ROOT + '/docs/web8/experiment/sem.js');
const A = process.argv, tag = A[2], ID = A[3], warmup = +A[4] || 0, total = +A[5] || 600, K = +A[6] || 6;
const PAL = A[7] || 'warm-sepia', RELIEF = +A[8] || 14.0;
load(`${ROOT}/docs/web8/experiment/rules/${ID}.js`);
const key = ID.replace('natural_selection', 'natural-selection');
const g = CA.RULES[key]();
if (process.env.FF && g.params && g.params.F) g.params.F.value = +process.env.FF;
if (process.env.KK && g.params && g.params.k) g.params.k.value = +process.env.KK;
if (process.env.GEN_PARAMS) { const o = JSON.parse(process.env.GEN_PARAMS); for (const pk in o) { if (g.params && g.params[pk]) { g.params[pk].value = o[pk]; if (g.onParamChange) { try { g.onParamChange(pk); } catch (e) {} } } } }
const W = g.width, H = g.height; g.reset();
if (process.env.SCAT) { function mul(a){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};} const rng=mul(987654); for(let i=0;i<+process.env.SCAT;i++) g.paint((rng()*W)|0,(rng()*H)|0,5,'paint'); }
const SC = (W <= 120 ? 4 : (W <= 160 ? 3 : 2));
const pw = W * SC, ph = H * SC;
const ps = new Uint8ClampedArray(pw * ph * 4), h = new Float32Array(W * H);
for (let i = 0; i < warmup; i++) g.step();
// snapshot schedule: K frames spread across `total` further steps
const steps = []; for (let kk = 0; kk < K; kk++) steps.push(Math.round(total * (K > 1 ? kk / (K - 1) : 0)));
// PNG writer (from cymatics.mjs)
const CT=(()=>{const t=[];for(let n=0;n<256;n++){let c=n;for(let k=0;k<8;k++)c=c&1?0xedb88320^(c>>>1):c>>>1;t[n]=c>>>0;}return t;})();
const crc=(b)=>{let c=0xffffffff;for(let i=0;i<b.length;i++)c=CT[(c^b[i])&0xff]^(c>>>8);return(c^0xffffffff)>>>0;};
function chunk(ty,d){const L=Buffer.alloc(4);L.writeUInt32BE(d.length,0);const T2=Buffer.from(ty,'ascii');const C=Buffer.alloc(4);C.writeUInt32BE(crc(Buffer.concat([T2,d])),0);return Buffer.concat([L,T2,d,C]);}
function writePNG(p,w,hh,rgba){const sig=Buffer.from([137,80,78,71,13,10,26,10]),ih=Buffer.alloc(13);ih.writeUInt32BE(w,0);ih.writeUInt32BE(hh,4);ih[8]=8;ih[9]=6;const raw=Buffer.alloc((w*4+1)*hh);for(let y=0;y<hh;y++){raw[y*(w*4+1)]=0;rgba.copy(raw,y*(w*4+1)+1,y*w*4,y*w*4+w*4);}fs.writeFileSync(p,Buffer.concat([sig,chunk('IHDR',ih),chunk('IDAT',zlib.deflateSync(raw)),chunk('IEND',Buffer.alloc(0))]));}
// montage
const T2 = 248, COLS = Math.min(K, 6), ROWS = Math.ceil(K / COLS), MW = T2 * COLS, MH = T2 * ROWS;
const img = Buffer.alloc(MW * MH * 4); const relief = [];
let prev = 0;
for (let kk = 0; kk < K; kk++) {
  const adv = steps[kk] - prev; prev = steps[kk];
  for (let s = 0; s < adv; s++) g.step();
  g.renderHeight(h);
  // structure score: stddev of the height field (flat/dead field -> ~0)
  let m = 0; for (let i = 0; i < W * H; i++) m += h[i]; m /= (W * H);
  let v = 0; for (let i = 0; i < W * H; i++) { const d = h[i] - m; v += d * d; } v = Math.sqrt(v / (W * H));
  relief.push(+v.toFixed(4));
  window.SEM.render(h, W, H, ps, { palette: PAL, scale: SC, relief: RELIEF });
  const cx = (kk % COLS) * T2, cy = ((kk / COLS) | 0) * T2;
  for (let y = 0; y < T2; y++) for (let x = 0; x < T2; x++) {
    const sp = (((y * ph / T2) | 0) * pw + ((x * pw / T2) | 0)) * 4, dp = ((cy + y) * MW + cx + x) * 4;
    img[dp] = ps[sp]; img[dp + 1] = ps[sp + 1]; img[dp + 2] = ps[sp + 2]; img[dp + 3] = 255;
  }
}
writePNG(`/tmp/sem_${tag}.png`, MW, MH, img);
fs.writeFileSync(`/tmp/sem_${tag}.json`, JSON.stringify({ tag, id: ID, label: g.label, W, H, SC, palette: PAL, warmup, steps, relief, montage: `/tmp/sem_${tag}.png (${COLS}x${ROWS}, left->right = early->late)` }));
console.log(`sem probe ${tag}: ${g.label} ${W}x${H} SC${SC} pal:${PAL} relief[min..max]=${Math.min(...relief).toFixed(3)}..${Math.max(...relief).toFixed(3)} -> /tmp/sem_${tag}.png`);
