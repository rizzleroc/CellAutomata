// wireworld.js — Silverman's Wireworld (1987): four states on the Moore
// neighbourhood. 0 empty · 1 conductor · 2 electron head · 3 electron tail.
//   head → tail; tail → conductor; conductor → head iff exactly 1 or 2 of its
//   eight neighbours are heads; empty stays empty.
// Electrons therefore travel along wires one cell per generation, and the
// "1 or 2 heads" rule makes diodes, OR gates, XOR gates and clocks possible —
// Wireworld is Turing-complete (a full computer has been built in it).

export const EMPTY = 0, WIRE = 1, HEAD = 2, TAIL = 3;

export function make() {
  return {
    family: 'wireworld',
    spec: {},
    states: 4,
    describe: () => 'Wireworld',
    step(grid) {
      const { K, tbl } = grid.neighbourhood('moore');
      const c = grid.cells, n = grid.next, N = c.length;
      for (let i = 0; i < N; i++) {
        const s = c[i];
        if (s === EMPTY) { n[i] = EMPTY; continue; }
        if (s === HEAD) { n[i] = TAIL; continue; }
        if (s === TAIL) { n[i] = WIRE; continue; }
        let heads = 0;
        const base = i * K;
        for (let k = 0; k < K; k++) { const j = tbl[base + k]; if (j >= 0 && c[j] === HEAD) heads++; }
        n[i] = (heads === 1 || heads === 2) ? HEAD : WIRE;
      }
      grid.swap();
    },
  };
}
