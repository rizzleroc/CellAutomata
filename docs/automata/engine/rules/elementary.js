// elementary.js — Wolfram's elementary cellular automata (1983): one row of
// binary cells, each updated from itself and its two neighbours by one of the
// 256 possible lookup tables ("rule N": bit k of N is the output for the
// 3-cell input pattern with value k). The lattice here is the SPACE–TIME
// diagram: row `grid.row` is the present, rows above are the past, and a
// step writes the next row beneath (scrolling once the sheet is full).
//
// Also the k=2, r=2 TOTALISTIC extension ("code N", Wolfram's 5-neighbour
// sum rules) — enough to reach rule 20 (class 4-like) and the classic
// totalistic gallery.

export const CATALOG = [
  { name: 'Rule 30',  rule: 30,  cls: 3, note: 'Chaotic; its centre column is a pseudo-random bit stream (Wolfram 1983).' },
  { name: 'Rule 90',  rule: 90,  cls: 3, note: 'Additive (XOR of the two neighbours) — grows the Sierpiński gasket.' },
  { name: 'Rule 110', rule: 110, cls: 4, note: 'Universal (Cook 2004): gliders on a periodic background.' },
  { name: 'Rule 184', rule: 184, cls: 2, note: 'The traffic rule: particles are conserved and jam.' },
  { name: 'Rule 54',  rule: 54,  cls: 4, note: 'Class-4 glider dynamics on a stripe background.' },
  { name: 'Rule 22',  rule: 22,  cls: 3, note: 'Sierpiński-like from one cell, chaotic from a soup.' },
  { name: 'Rule 45',  rule: 45,  cls: 3, note: 'Chaotic, asymmetric.' },
  { name: 'Rule 60',  rule: 60,  cls: 3, note: 'Additive: left-neighbour XOR self — Pascal’s triangle mod 2.' },
  { name: 'Rule 73',  rule: 73,  cls: 2, note: 'Walls that separate periodic regions.' },
  { name: 'Rule 105', rule: 105, cls: 3, note: 'Additive, three-cell XOR complement.' },
  { name: 'Rule 126', rule: 126, cls: 3, note: 'Sierpiński-like nested triangles.' },
  { name: 'Rule 150', rule: 150, cls: 3, note: 'Additive XOR of all three cells.' },
  { name: 'Rule 250', rule: 250, cls: 1, note: 'Class 1: grows a solid checkerboard and stays there.' },
  { name: 'Rule 232', rule: 232, cls: 2, note: 'Majority of three: freezes into domains immediately.' },
];

export function make({ rule = 30, totalistic = false, init = 'single' } = {}) {
  rule = rule | 0;
  const maxRule = totalistic ? 63 : 255;
  if (rule < 0 || rule > maxRule) throw new RangeError(`rule must be 0–${maxRule}`);
  const bit = (k) => (rule >> k) & 1;
  return {
    family: 'elementary',
    spec: { rule, totalistic, init },
    states: 2,
    oneD: true,
    describe: () => (totalistic ? `code ${rule}` : `rule ${rule}`),
    // Seed row 0 (single centre cell or a soup) and mark it the present.
    init(grid, rng) {
      grid.clear(); grid.row = 0;
      if (init === 'single') grid.cells[grid.width >> 1] = 1;
      else for (let x = 0; x < grid.width; x++) grid.cells[x] = rng() < 0.5 ? 1 : 0;
    },
    step(grid) {
      const w = grid.width, h = grid.height, c = grid.cells;
      if (grid.row === undefined) grid.row = 0;
      let src = grid.row, dst = src + 1;
      if (dst >= h) {            // sheet full: scroll one row up, keep the present at the bottom
        c.copyWithin(0, w, w * h);
        src = h - 2; dst = h - 1;
        c.fill(0, dst * w, (dst + 1) * w);
      }
      const torus = grid.boundary !== 'dead';
      const at = (x) => {
        if (x >= 0 && x < w) return c[src * w + x];
        if (!torus) return 0;
        return c[src * w + (((x % w) + w) % w)];
      };
      for (let x = 0; x < w; x++) {
        let out;
        if (totalistic) {
          const sum = at(x - 2) + at(x - 1) + at(x) + at(x + 1) + at(x + 2);
          out = bit(sum);
        } else {
          out = bit((at(x - 1) << 2) | (at(x) << 1) | at(x + 1));
        }
        c[dst * w + x] = out;
      }
      grid.row = dst; grid.generation++;
    },
  };
}
