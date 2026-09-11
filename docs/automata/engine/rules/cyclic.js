// cyclic.js — excitable media.
//
// CYCLIC (Fisch, Gravner & Griffeath 1991): n states arranged on a ring. A
// cell in state s advances to s+1 (mod n) when at least `threshold` cells in
// its range-r neighbourhood are already in state s+1. From a random soup the
// system self-organises: debris → droplets → spiral defects that eventually
// dominate the lattice (the "cyclic spiral" phase).
//
// GREENBERG–HASTINGS (1978): the discrete excitable medium. State 0 is
// resting, 1 excited, 2..n−1 refractory. Resting cells fire when at least
// `threshold` neighbours are excited; excited and refractory cells advance
// deterministically back to rest. Target waves and rotating spirals as in
// cardiac tissue and the Belousov–Zhabotinsky reaction.

export const CATALOG = [
  { name: 'Cyclic 14 / t1 / r1',     values: { model: 'cyclic', states: 14, threshold: 1, range: 1 }, note: 'The classic: debris → droplets → spirals.' },
  { name: 'Cyclic 313',              values: { model: 'cyclic', states: 3,  threshold: 3, range: 1 }, note: 'Griffeath’s 3-state, threshold-3 rule: turbulent spirals.' },
  { name: 'Cyclic spirals r3',       values: { model: 'cyclic', states: 8,  threshold: 3, range: 3 }, note: 'Wide neighbourhood, big rotating spirals.' },
  { name: 'Cutting edge',            values: { model: 'cyclic', states: 5,  threshold: 5, range: 2 }, note: 'High threshold: sharp fronts that only advance where the wave is thick.' },
  { name: 'Perfect spirals',         values: { model: 'cyclic', states: 8,  threshold: 5, range: 3 }, note: 'Clean, slow, perfectly circular spirals.' },
  { name: 'Greenberg–Hastings 3',    values: { model: 'gh', states: 3, threshold: 1, range: 1 }, note: 'Excited → refractory → rest. Rings and spirals from any excited seed.' },
  { name: 'Greenberg–Hastings 8',    values: { model: 'gh', states: 8, threshold: 1, range: 1 }, note: 'Long refractory tail: broad slow waves.' },
  { name: 'GH threshold 2, r2',      values: { model: 'gh', states: 6, threshold: 2, range: 2 }, note: 'Needs two excited neighbours: waves must be thick to propagate.' },
];

export function make({ model = 'cyclic', states = 14, threshold = 1, range = 1, neighbourhood = 'moore' } = {}) {
  states |= 0; threshold |= 0; range |= 0;
  if (states < 3 || states > 64) throw new RangeError('states must be 3–64');
  if (range < 1 || range > 4) throw new RangeError('range must be 1–4');
  const box = (2 * range + 1) ** 2 - 1;
  if (threshold < 1 || threshold > box) throw new RangeError(`threshold must be 1–${box}`);
  const offs = [];
  for (let dy = -range; dy <= range; dy++) for (let dx = -range; dx <= range; dx++) {
    if (dx === 0 && dy === 0) continue;
    if (neighbourhood === 'vn' && Math.abs(dx) + Math.abs(dy) > range) continue;
    offs.push([dx, dy]);
  }
  const spec = { model, states, threshold, range, neighbourhood };
  return {
    family: 'cyclic',
    spec,
    states,
    describe: () => (model === 'gh' ? `GH n${states} t${threshold} r${range}` : `cyclic n${states} t${threshold} r${range}`),
    init(grid, rng) {
      if (model === 'gh') {
        grid.clear();
        // a sparse sprinkling of excited cells plus a few refractory "cuts" to seed spirals
        const n = grid.size;
        for (let i = 0; i < n; i++) {
          const u = rng();
          if (u < 0.02) grid.cells[i] = 1; else if (u < 0.03) grid.cells[i] = 2;
        }
      } else {
        grid.randomize(rng, 1, states);
        for (let i = 0; i < grid.size; i++) grid.cells[i] = Math.floor(rng() * states);
      }
    },
    step(grid) {
      const w = grid.width, h = grid.height, c = grid.cells, nx = grid.next;
      const torus = grid.boundary === 'torus';
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
        const i = y * w + x, s = c[i];
        let target, next;
        if (model === 'gh') {
          if (s !== 0) { nx[i] = s + 1 < states ? s + 1 : 0; continue; }
          target = 1; next = 1;
        } else {
          target = (s + 1) % states; next = target;
        }
        let cnt = 0;
        for (let k = 0; k < offs.length; k++) {
          let ax = x + offs[k][0], ay = y + offs[k][1], j;
          if (ax >= 0 && ax < w && ay >= 0 && ay < h) j = ay * w + ax;
          else if (torus) j = (((ay % h) + h) % h) * w + (((ax % w) + w) % w);
          else { j = grid.idx(ax, ay); if (j < 0) continue; }
          if (c[j] === target) { cnt++; if (cnt >= threshold) break; }
        }
        nx[i] = cnt >= threshold ? next : s;
      }
      grid.swap();
    },
  };
}
