// EXPORT HEIGHT — dump a rule's real height field (Float32 [0,1]) as a 16-bit grayscale PNG heightmap
// for Unreal import (displacement / WPO). This is the science bridge: the UE protocell surface is driven
// by the actual simulation, not noise. Mirrors sem_probe.mjs's load + warmup.
//   node export_height.mjs <ruleId> <warmup> [OUT] [tag]   env: GEN_PARAMS (JSON), FF, KK
//   -> /tmp/<tag>_height.png  (OUT x OUT, 16-bit grayscale)
import fs from 'fs';
import zlib from 'node:zlib';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
globalThis.window = globalThis; globalThis.CA = { RULES: {} };
const ev = (0, eval); const load = p => ev(fs.readFileSync(p, 'utf8'));
load(ROOT + '/docs/web8/experiment/viridis.js'); load(ROOT + '/docs/web8/experiment/sprites.js'); load(ROOT + '/docs/web8/experiment/sem.js');
const A = process.argv, ID = A[2] || 'grayscott', warmup = +A[3] || 200, OUT = +A[4] || 1024, tag = A[5] || ('ue_' + ID);
load(`${ROOT}/docs/web8/experiment/rules/${ID}.js`);
const g = CA.RULES[ID.replace('natural_selection', 'natural-selection')]();
if (process.env.FF && g.params && g.params.F) g.params.F.value = +process.env.FF;
if (process.env.KK && g.params && g.params.k) g.params.k.value = +process.env.KK;
if (process.env.GEN_PARAMS) { const o = JSON.parse(process.env.GEN_PARAMS); for (const k in o) if (g.params && g.params[k]) { g.params[k].value = o[k]; if (g.onParamChange) try { g.onParamChange(k); } catch (e) {} } }
const W = g.width, H = g.height; g.reset();
for (let i = 0; i < warmup; i++) g.step();
const h = new Float32Array(W * H); g.renderHeight(h);
let mn = 1e9, mx = -1e9; for (let i = 0; i < h.length; i++) { if (h[i] < mn) mn = h[i]; if (h[i] > mx) mx = h[i]; }
const span = (mx - mn) || 1;
// bilinear upsample W x H -> OUT x OUT, normalize to full 16-bit range
const samp = new Uint16Array(OUT * OUT);
for (let y = 0; y < OUT; y++) {
  const fy = (y + 0.5) * H / OUT - 0.5; let y0 = Math.floor(fy); const ty = fy - y0; let y1 = y0 + 1;
  y0 = Math.max(0, Math.min(H - 1, y0)); y1 = Math.max(0, Math.min(H - 1, y1));
  for (let x = 0; x < OUT; x++) {
    const fx = (x + 0.5) * W / OUT - 0.5; let x0 = Math.floor(fx); const tx = fx - x0; let x1 = x0 + 1;
    x0 = Math.max(0, Math.min(W - 1, x0)); x1 = Math.max(0, Math.min(W - 1, x1));
    const a = h[y0 * W + x0], b = h[y0 * W + x1], c = h[y1 * W + x0], d = h[y1 * W + x1];
    const v = (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty;
    samp[y * OUT + x] = Math.max(0, Math.min(65535, Math.round((v - mn) / span * 65535)));
  }
}
// 16-bit grayscale PNG (bit depth 16, color type 0)
const CT = (() => { const t = []; for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
const crc = b => { let c = 0xffffffff; for (let i = 0; i < b.length; i++) c = CT[(c ^ b[i]) & 0xff] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; };
const chunk = (ty, d) => { const L = Buffer.alloc(4); L.writeUInt32BE(d.length, 0); const T = Buffer.from(ty, 'ascii'); const C = Buffer.alloc(4); C.writeUInt32BE(crc(Buffer.concat([T, d])), 0); return Buffer.concat([L, T, d, C]); };
const ih = Buffer.alloc(13); ih.writeUInt32BE(OUT, 0); ih.writeUInt32BE(OUT, 4); ih[8] = 16; ih[9] = 0;
const raw = Buffer.alloc((OUT * 2 + 1) * OUT);
for (let y = 0; y < OUT; y++) { let o = y * (OUT * 2 + 1); raw[o++] = 0; for (let x = 0; x < OUT; x++) { const v = samp[y * OUT + x]; raw[o++] = v >>> 8; raw[o++] = v & 255; } }
const png = Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ih), chunk('IDAT', zlib.deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]);
const outp = `/tmp/${tag}_height.png`; fs.writeFileSync(outp, png);
console.log(`height ${ID} ${W}x${H} -> ${OUT}x${OUT} 16-bit [${mn.toFixed(3)}..${mx.toFixed(3)}] -> ${outp} (${(png.length/1024)|0} KB)`);
