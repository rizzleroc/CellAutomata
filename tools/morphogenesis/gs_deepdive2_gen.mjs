// DEEP DIVE II — the 8 best champions at high resolution (512²) for smooth, crisp detail, each
// matured then captured with gentle motion (1 step/frame) so a slow dive INTO the texture stays fluid.
import fs from 'fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
globalThis.window = globalThis; globalThis.CA = { RULES: {} };
const ev = (0, eval);
const R = 512, M = 170, WARM = 4200, STEPF = 1;     // hi-res, long mature, gentle 10-substep frames
let gs = fs.readFileSync(`${ROOT}/docs/web8/experiment/rules/grayscott.js`, 'utf8');
gs = gs.replace('const W = 220;', `const W = ${R};`).replace('const H = 220;', `const H = ${R};`); ev(gs);
const PAT = [
  [0.0214, 0.0520, "Fingerprint Maze",  "tight interlocking ridges — no two whorls alike"],
  [0.0329, 0.0590, "Brain Coral",       "bold sweeping meanders, the classic Turing labyrinth"],
  [0.0243, 0.0590, "Mitotic Spots",     "a whole field of spots caught mid-division"],
  [0.0367, 0.0649, "Dividing Cells",    "Pearson's mitosis — every spot splits, then splits again"],
  [0.0529, 0.0660, "Gliding Solitons",  "mobile worm-solitons weaving through the lattice"],
  [0.0620, 0.0609, "U-skate Crawlers",  "self-replicating spots that crawl and collide"],
  [0.0614, 0.0630, "Deep Labyrinth",    "the densest, most intricate maze the search found"],
  [0.0700, 0.0520, "Negaton Holes",     "inverse spots — dark voids drifting in a bright sea"],
];
const u16 = new Uint16Array(R * R), h = new Float32Array(R * R);
const fd = fs.openSync('/tmp/dd2_field.bin', 'w'); const t0 = Date.now();
PAT.forEach(([F, k, name], idx) => {
  const g = CA.RULES.grayscott(); g.params.F.value = F; g.params.k.value = k; g.reset();
  let s_ = (424242 ^ ((F * 1e4) | 0) ^ (((k * 1e4) | 0) << 8)) >>> 0; const rnd = () => { s_ = (s_ * 1664525 + 1013904223) >>> 0; return s_ / 4294967296; };
  for (let n = 0; n < 200; n++) g.paint((rnd() * R) | 0, (rnd() * R) | 0, 5, 'paint');   // denser scatter fills the bigger plane
  for (let s = 0; s < (WARM / 10) | 0; s++) g.step();
  for (let f = 0; f < M; f++) {
    for (let s = 0; s < STEPF; s++) g.step();
    g.renderHeight(h);
    for (let i = 0; i < h.length; i++) { let v = h[i]; v = v < 0 ? 0 : v > 1 ? 1 : v; u16[i] = (v * 65535) | 0; }
    fs.writeSync(fd, Buffer.from(u16.buffer, u16.byteOffset, u16.byteLength));
  }
  console.log(`#${idx} ${name} F${F} k${k} ${(Date.now() - t0) / 1000 | 0}s`);
});
fs.closeSync(fd);
fs.writeFileSync('/tmp/dd2_meta.json', JSON.stringify({ R, M, patterns: PAT.map(([F, k, name, cap]) => ({ F, k, name, cap })) }));
console.log('DEEPDIVE2 GEN DONE', PAT.length, 'patterns', (Date.now() - t0) / 1000 | 0, 's');
