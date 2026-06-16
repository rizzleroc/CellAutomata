// Curate the swarm's champion (F,k) picks: render each at full quality (SEM warm-sepia, matured)
// into one labelled contact sheet so the finalist patterns can be chosen by eye.
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
const RES = 200, SUB = 4200;
let gs = fs.readFileSync(`${ROOT}/docs/web8/experiment/rules/grayscott.js`, 'utf8');
gs = gs.replace('const W = 220;', `const W = ${RES};`).replace('const H = 220;', `const H = ${RES};`); ev(gs);
const W = RES, H = RES;
// the swarm's champions (F,k) — diverse shortlist across the discovered themes
const CAND = [
  [0.0214, 0.052], [0.0271, 0.059], [0.0329, 0.059], [0.0300, 0.058],
  [0.0357, 0.045], [0.0443, 0.045], [0.0500, 0.045], [0.0586, 0.045],
  [0.0243, 0.059], [0.0443, 0.066], [0.0529, 0.066], [0.0500, 0.063],
  [0.0557, 0.064], [0.0557, 0.063], [0.0614, 0.063], [0.0700, 0.052],
];
function field(F, k) {
  const g = CA.RULES.grayscott(); g.params.F.value = F; g.params.k.value = k; g.reset();
  let s_ = (98765 ^ ((F * 1e4) | 0) ^ (((k * 1e4) | 0) << 8)) >>> 0; const rnd = () => { s_ = (s_ * 1664525 + 1013904223) >>> 0; return s_ / 4294967296; };
  for (let n = 0; n < 46; n++) g.paint((rnd() * W) | 0, (rnd() * H) | 0, 4, 'paint');
  for (let s = 0; s < (SUB / 10) | 0; s++) g.step();
  const h = new Float32Array(W * H); g.renderHeight(h); return h;
}
const SC = 1, T = RES * SC;            // SEM scale 1 -> tile = RES
const COLS = 4, ROWS = Math.ceil(CAND.length / COLS), MW = T * COLS, MH = T * ROWS;
const img = Buffer.alloc(MW * MH * 4); img.fill(0); for (let i = 3; i < img.length; i += 4) img[i] = 255;
const ps = new Uint8ClampedArray(T * T * 4);
CAND.forEach(([F, k], idx) => {
  const h = field(F, k);
  window.SEM.render(h, W, H, ps, { palette: 'warm-sepia', scale: SC, relief: 9 });
  const cx = (idx % COLS) * T, cy = ((idx / COLS) | 0) * T;
  for (let y = 0; y < T; y++) for (let x = 0; x < T; x++) {
    const sp = (y * T + x) * 4, dp = ((cy + y) * MW + (cx + x)) * 4;
    img[dp] = ps[sp]; img[dp + 1] = ps[sp + 1]; img[dp + 2] = ps[sp + 2]; img[dp + 3] = 255;
  }
  console.log(`#${idx} F${F} k${k}`);
});
const CT = (() => { const t = []; for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++)c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
const crc = (b) => { let c = 0xffffffff; for (let i = 0; i < b.length; i++)c = CT[(c ^ b[i]) & 0xff] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; };
function chunk(ty, d) { const L = Buffer.alloc(4); L.writeUInt32BE(d.length, 0); const T2 = Buffer.from(ty, 'ascii'); const C = Buffer.alloc(4); C.writeUInt32BE(crc(Buffer.concat([T2, d])), 0); return Buffer.concat([L, T2, d, C]); }
const sig = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]); const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(MW, 0); ihdr.writeUInt32BE(MH, 4); ihdr[8] = 8; ihdr[9] = 6;
const raw = Buffer.alloc((MW * 4 + 1) * MH); for (let y = 0; y < MH; y++) { raw[y * (MW * 4 + 1)] = 0; img.copy(raw, y * (MW * 4 + 1) + 1, y * MW * 4, y * MW * 4 + MW * 4); }
fs.writeFileSync('/tmp/gs_curate.png', Buffer.concat([sig, chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]));
console.log(`contact sheet -> /tmp/gs_curate.png  (${COLS}x${ROWS}, row-major #0..${CAND.length - 1})`);
