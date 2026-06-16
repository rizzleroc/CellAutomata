// DEEP SEARCH reel generator — the motion-weighted swarm's new champions, headlined by the SPIRAL
// and TARGET-WAVE regimes (k~0.052) the first pass missed. Waves need SPARSE seeding to form clean
// expanding fronts/spirals; textures use dense fill. High res (512²). -> /tmp/ds_field.bin
import fs from 'fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
globalThis.window = globalThis; globalThis.CA = { RULES: {} };
const ev = (0, eval);
const R = 512, M = 170, STEPF = 2;     // 2 steps/frame (20 substeps) -> visibly alive, still smooth
let gs = fs.readFileSync(`${ROOT}/docs/web8/experiment/rules/grayscott.js`, 'utf8');
gs = gs.replace('const W = 220;', `const W = ${R};`).replace('const H = 220;', `const H = ${R};`); ev(gs);
// [F, k, name, caption, seedMode] — the swarm's REAL dynamic finds (the k~0.052 "spiral/wave"
// picks were per-tile-normalisation artifacts that saturate at honest resolution, so they're out).
// What survives is a rich seam of DEFECT / HOLE / COEXISTENCE regimes (k ~0.054-0.066).
const PAT = [
  [0.0220, 0.0544, "Coral–Spot Lace",   "worms and spots coexisting — the highest sustained motion the search found", "dense"],
  [0.0250, 0.0574, "Holed Lattice",     "a crystalline spot lattice punched through by a dark hole", "dense"],
  [0.0250, 0.0580, "Invasion Front",    "a sharp front sweeping into a dense field of spots", "dense"],
  [0.0265, 0.0592, "Defect Lattice",    "roving lattice defects splitting and re-knitting the array", "dense"],
  [0.0370, 0.0640, "Mitotic Lattice",   "a lattice of spots caught dividing into dumbbells", "dense"],
  [0.0400, 0.0640, "Worm–Spot Coral",   "rods and dots reorganising along an active front", "dense"],
  [0.0535, 0.0628, "Ringed Hole Maze",  "a maze threaded with closed loops around dark holes", "dense"],
  [0.0630, 0.0628, "Dendritic Web",     "a fine, endlessly branching network", "dense"],
  [0.0650, 0.0622, "Dividing Negatons", "ring-blobs splitting inside a cellular network", "dense"],
  [0.0670, 0.0616, "Bold Ring Cells",   "high-contrast loops and holes — the richest structure at high feed", "dense"],
];
const u16 = new Uint16Array(R * R), h = new Float32Array(R * R);
const fd = fs.openSync('/tmp/ds_field.bin', 'w'); const t0 = Date.now();
PAT.forEach(([F, k, name, cap, mode], idx) => {
  const g = CA.RULES.grayscott(); g.params.F.value = F; g.params.k.value = k; g.reset();
  let s_ = (1234567 ^ ((F * 1e4) | 0) ^ (((k * 1e4) | 0) << 8)) >>> 0; const rnd = () => { s_ = (s_ * 1664525 + 1013904223) >>> 0; return s_ / 4294967296; };
  const nseed = mode === 'wave' ? 42 : 200, rad = mode === 'wave' ? 4 : 5, warm = mode === 'wave' ? 3600 : 3000;  // less mature -> more ongoing motion
  for (let n = 0; n < nseed; n++) g.paint((rnd() * R) | 0, (rnd() * R) | 0, rad, 'paint');
  for (let s = 0; s < (warm / 10) | 0; s++) g.step();
  for (let f = 0; f < M; f++) {
    for (let s = 0; s < STEPF; s++) g.step();
    g.renderHeight(h);
    for (let i = 0; i < h.length; i++) { let v = h[i]; v = v < 0 ? 0 : v > 1 ? 1 : v; u16[i] = (v * 65535) | 0; }
    fs.writeSync(fd, Buffer.from(u16.buffer, u16.byteOffset, u16.byteLength));
  }
  console.log(`#${idx} ${name} F${F} k${k} [${mode}] ${(Date.now() - t0) / 1000 | 0}s`);
});
fs.closeSync(fd);
fs.writeFileSync('/tmp/ds_meta.json', JSON.stringify({ R, M, patterns: PAT.map(([F, k, name, cap]) => ({ F, k, name, cap })) }));
console.log('DEEP SEARCH GEN DONE', PAT.length, 'patterns', (Date.now() - t0) / 1000 | 0, 's');
