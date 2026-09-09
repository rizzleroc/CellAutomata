// ltl.js — Larger than Life (Evans 1996/2001): outer-totalistic rules on a
// (2r+1)² box neighbourhood with birth/survival INTERVALS instead of digit
// sets. Golly notation "R5,C0,M1,S34..58,B34..45" — R range, C states (0 = 2),
// M 1 to include the centre cell in its own count, S survival interval,
// B birth interval. At r=1 with M=0 this reduces to a Life-like rule; at
// larger r the discrete lattice starts to behave like a continuous medium
// ("bugs" that glide, breathe and collide).
//
// Counting uses a summed-area table, so a step is O(w·h) regardless of r.

export function parseLtl(text) {
  const s = String(text).replace(/\s+/g, '').toUpperCase();
  const m = s.match(/^R(\d+),C(\d+),M([01]),S(\d+)\.\.(\d+),B(\d+)\.\.(\d+)$/);
  if (!m) throw new SyntaxError(`bad Larger-than-Life rule "${text}" — expected R5,C0,M1,S34..58,B34..45`);
  const spec = { range: +m[1], states: Math.max(2, +m[2] || 2), middle: +m[3] === 1,
    sMin: +m[4], sMax: +m[5], bMin: +m[6], bMax: +m[7] };
  if (spec.range < 1 || spec.range > 10) throw new RangeError('range must be 1–10');
  const cap = (2 * spec.range + 1) ** 2;
  for (const k of ['sMin', 'sMax', 'bMin', 'bMax']) {
    if (spec[k] > cap) throw new RangeError(`${k}=${spec[k]} exceeds the ${cap}-cell neighbourhood`);
  }
  if (spec.sMin > spec.sMax || spec.bMin > spec.bMax) throw new RangeError('interval lower bound exceeds upper bound');
  return spec;
}
export function formatLtl(p) {
  return `R${p.range},C${p.states > 2 ? p.states : 0},M${p.middle ? 1 : 0},S${p.sMin}..${p.sMax},B${p.bMin}..${p.bMax}`;
}

export const CATALOG = [
  { name: "Bosco's Rule", rule: 'R5,C0,M1,S33..57,B34..45', note: 'Evans’ original bugs: gliding, breathing blobs that collide and split.' },
  { name: 'Bugs',         rule: 'R5,C0,M1,S34..58,B34..45', note: 'The classic Larger-than-Life bug rule.' },
  { name: 'Waffle',       rule: 'R7,C0,M1,S100..200,B75..170', note: 'Coarse waffle textures that hold still at the edges.' },
  { name: 'Globe',        rule: 'R8,C0,M0,S163..223,B74..252', note: 'Large rotating globes that drift and merge.' },
  { name: 'Majority r=4', rule: 'R4,C0,M1,S41..81,B41..81', note: 'A majority vote over 81 cells: coarsening domains.' },
  { name: 'Life (r=1)',   rule: 'R1,C0,M0,S2..3,B3..3',  note: 'Conway’s Life expressed as an interval rule — the sanity check.' },
];

export function make(spec) {
  if (typeof spec === 'string') spec = parseLtl(spec);
  const r = spec.range, C = spec.states;
  return {
    family: 'ltl',
    spec,
    states: C,
    describe: () => formatLtl(spec),
    step(grid) {
      const w = grid.width, h = grid.height, c = grid.cells, n = grid.next;
      const torus = grid.boundary === 'torus';
      // Summed-area table over an r-padded copy so the box sum is 4 lookups.
      // Under a torus the padding wraps; under dead/mirror it follows idx().
      const W = w + 2 * r, H = h + 2 * r;
      const sat = satBuf(W, H);
      for (let y = 0; y < H; y++) {
        let rowSum = 0;
        for (let x = 0; x < W; x++) {
          let v;
          const gx = x - r, gy = y - r;
          if (gx >= 0 && gx < w && gy >= 0 && gy < h) v = c[gy * w + gx] === 1 ? 1 : 0;
          else if (torus) v = c[(((gy % h) + h) % h) * w + (((gx % w) + w) % w)] === 1 ? 1 : 0;
          else { const j = grid.idx(gx, gy); v = j >= 0 && c[j] === 1 ? 1 : 0; }
          rowSum += v;
          sat[(y + 1) * (W + 1) + (x + 1)] = sat[y * (W + 1) + (x + 1)] + rowSum;
        }
      }
      const S1 = W + 1;
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
        // box [x-r, x+r] × [y-r, y+r] in grid coords → [x, x+2r] in padded coords
        const x0 = x, y0 = y, x1 = x + 2 * r + 1, y1 = y + 2 * r + 1;
        let cnt = sat[y1 * S1 + x1] - sat[y0 * S1 + x1] - sat[y1 * S1 + x0] + sat[y0 * S1 + x0];
        const i = y * w + x, s = c[i];
        if (!spec.middle && s === 1) cnt -= 1;
        if (s === 0) n[i] = (cnt >= spec.bMin && cnt <= spec.bMax) ? 1 : 0;
        else if (s === 1) n[i] = (cnt >= spec.sMin && cnt <= spec.sMax) ? 1 : (C > 2 ? 2 : 0);
        else n[i] = s + 1 < C ? s + 1 : 0;
      }
      grid.swap();
    },
  };
}
let _sat = null;
function satBuf(W, H) {
  const need = (W + 1) * (H + 1);
  if (!_sat || _sat.length < need) _sat = new Int32Array(need);
  else _sat.fill(0, 0, W + 1);   // only the first row must be zero; the rest is overwritten
  for (let y = 0; y <= H; y++) _sat[y * (W + 1)] = 0;
  return _sat;
}
