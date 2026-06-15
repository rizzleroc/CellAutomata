// GS PARAMETER-SPACE SWEEP + interestingness scorer + a 6-up montage for an agent to judge.
// Combs a rectangle of Gray-Scott (F,k) space, scores each cell for structure/complexity/motion,
// and writes the region's top-6 as one PNG (rank 1..6, row-major) + a ranked JSON.
//   node tools/morphogenesis/gs_sweep.mjs <tag> <F0> <F1> <k0> <k1> <nF> <nk> [res] [steps] [seed]
import fs from 'fs';
import zlib from 'node:zlib';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');   // repo root, cwd-independent
globalThis.window = globalThis; globalThis.CA = { RULES: {} };
const ev = (0, eval);
ev(fs.readFileSync(`${ROOT}/docs/web8/experiment/viridis.js`, 'utf8'));
const A = process.argv;
const tag = A[2], F0 = +A[3], F1 = +A[4], k0 = +A[5], k1 = +A[6], nF = +A[7], nk = +A[8];
const RES = +A[9] || 100, STEPS = +A[10] || 2800, SEEDV = +A[11] || 12345;
let gs = fs.readFileSync(`${ROOT}/docs/web8/experiment/rules/grayscott.js`, 'utf8');
gs = gs.replace('const W = 220;', `const W = ${RES};`).replace('const H = 220;', `const H = ${RES};`); ev(gs);
const W = RES, H = RES;
const VL = (typeof VIRIDIS_LUT !== 'undefined') ? VIRIDIS_LUT : null, VN = VL ? VL.length / 3 : 0;
function run(F, k) {
  const g = CA.RULES.grayscott(); g.params.F.value = F; g.params.k.value = k; g.reset();
  let s_ = (SEEDV ^ ((F * 1e4) | 0) ^ (((k * 1e4) | 0) << 8)) >>> 0; const rnd = () => { s_ = (s_ * 1664525 + 1013904223) >>> 0; return s_ / 4294967296; };
  for (let n = 0; n < 46; n++) g.paint((rnd() * W) | 0, (rnd() * H) | 0, 4, 'paint');   // scatter-seed so the regime fills the plane
  const calls = Math.max(1, (STEPS / 10) | 0);
  for (let s = 0; s < calls; s++) g.step();
  const v = new Float32Array(W * H); g.renderHeight(v);
  let mean = 0; for (const x of v) mean += x; mean /= v.length;
  let varr = 0; for (const x of v) varr += (x - mean) ** 2; varr /= v.length; const std = Math.sqrt(varr);
  if (std < 0.015) return { F: +F.toFixed(4), k: +k.toFixed(4), score: 0, mean: +mean.toFixed(3), std: +std.toFixed(3), edge: 0, live: 0, v };
  let edge = 0; for (let y = 1; y < H - 1; y++) for (let x = 1; x < W - 1; x++) { const i = y * W + x; const gx = v[i + 1] - v[i - 1], gy = v[i + W] - v[i - W]; edge += Math.hypot(gx, gy); } edge /= ((W - 2) * (H - 2));
  for (let s = 0; s < 6; s++) g.step(); const v2 = new Float32Array(W * H); g.renderHeight(v2);
  let live = 0; for (let i = 0; i < v.length; i++) live += Math.abs(v2[i] - v[i]); live /= v.length;
  let pen = 1; if (mean > 0.55) pen *= 0.4; if (mean < 0.02) pen *= 0.3;
  const score = edge * (0.3 + std) * (0.5 + Math.min(1, live * 40)) * pen;
  return { F: +F.toFixed(4), k: +k.toFixed(4), score: +score.toFixed(5), mean: +mean.toFixed(3), std: +std.toFixed(3), edge: +edge.toFixed(4), live: +live.toFixed(4), v };
}
// sweep
const out = [];
for (let j = 0; j < nk; j++) for (let i = 0; i < nF; i++) {
  const F = F0 + (F1 - F0) * (nF > 1 ? i / (nF - 1) : 0);
  const k = k0 + (k1 - k0) * (nk > 1 ? j / (nk - 1) : 0);
  out.push(run(F, k));
}
out.sort((a, b) => b.score - a.score);
const top = out.slice(0, 6);
// montage: 3 cols x 2 rows, tile T (viridis, nearest-upscaled)
const T = 240, COLS = 3, ROWS = 2, MW = T * COLS, MH = T * ROWS;
const img = Buffer.alloc(MW * MH * 4);
function blit(tile, ti) {
  const cx = (ti % COLS) * T, cy = ((ti / COLS) | 0) * T, v = tile.v;
  if (!v) return;
  let mn = 1e9, mx = -1e9; for (const x of v) { if (x < mn) mn = x; if (x > mx) mx = x; } const rng = (mx - mn) || 1;
  for (let y = 0; y < T; y++) for (let x = 0; x < T; x++) {
    const sv = v[((y * H / T) | 0) * W + ((x * W / T) | 0)]; let t = (sv - mn) / rng; t = t < 0 ? 0 : t > 1 ? 1 : t;
    let r, gg, b; if (VL) { const idx = Math.min(VN - 1, (t * VN) | 0) * 3; r = VL[idx]; gg = VL[idx + 1]; b = VL[idx + 2]; } else { r = gg = b = (t * 255) | 0; }
    const p = ((cy + y) * MW + (cx + x)) * 4; img[p] = r; img[p + 1] = gg; img[p + 2] = b; img[p + 3] = 255;
  }
}
top.forEach((t, i) => blit(t, i));
// PNG writer
const CT = (() => { const t = []; for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++)c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
const crc = (b) => { let c = 0xffffffff; for (let i = 0; i < b.length; i++)c = CT[(c ^ b[i]) & 0xff] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; };
function chunk(ty, d) { const L = Buffer.alloc(4); L.writeUInt32BE(d.length, 0); const T2 = Buffer.from(ty, 'ascii'); const C = Buffer.alloc(4); C.writeUInt32BE(crc(Buffer.concat([T2, d])), 0); return Buffer.concat([L, T2, d, C]); }
const sig = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]); const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(MW, 0); ihdr.writeUInt32BE(MH, 4); ihdr[8] = 8; ihdr[9] = 6;
const raw = Buffer.alloc((MW * 4 + 1) * MH); for (let y = 0; y < MH; y++) { raw[y * (MW * 4 + 1)] = 0; img.copy(raw, y * (MW * 4 + 1) + 1, y * MW * 4, y * MW * 4 + MW * 4); }
fs.writeFileSync(`/tmp/sweep_${tag}.png`, Buffer.concat([sig, chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]));
const ranked = out.slice(0, 12).map((t, i) => ({ rank: i + 1, F: t.F, k: t.k, score: t.score, mean: t.mean, std: t.std, edge: t.edge, live: t.live }));
fs.writeFileSync(`/tmp/sweep_${tag}.json`, JSON.stringify({ tag, region: { F0, F1, k0, k1, nF, nk }, points: out.length, top6_montage: `/tmp/sweep_${tag}.png (3x2, rank 1-6 row-major)`, ranked }, null, 1));
console.log(`${tag}: swept ${out.length} pts · top score ${out[0].score} @ F${out[0].F} k${out[0].k} · montage /tmp/sweep_${tag}.png`);
