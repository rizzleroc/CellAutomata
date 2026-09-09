// turmite.js — Langton's ant (1986) and its multi-colour generalisations
// (Propp's "turmites" as popularised by Gale, Propp, Sutherland & Troubetzkoy
// 1995). The lattice holds colours 0..k−1; an ant standing on colour c turns
// according to the c-th letter of the rule string (L or R), flips the cell to
// colour c+1 mod k, then steps forward. "RL" is Langton's ant: after ~10 000
// chaotic steps it builds the famous 104-step "highway" forever.
//
// The rule object steps `movesPerGen` ant moves per generation so the lab
// clock stays comparable with the synchronous families.

export const CATALOG = [
  { name: "Langton's ant", rule: 'RL',            note: 'Chaos for ~10 000 steps, then the diagonal highway (period 104).' },
  { name: 'LLRR symmetric', rule: 'LLRR',         note: 'Grows a symmetric, cardioid-like pattern.' },
  { name: 'LRRRRRLLR',      rule: 'LRRRRRLLR',    note: 'Fills space in a square.' },
  { name: 'RRLLLRLLLRRR',   rule: 'RRLLLRLLLRRR', note: 'A growing triangle.' },
  { name: 'LLRRRLRLRLLR',   rule: 'LLRRRLRLRLLR', note: 'Convoluted highway.' },
  { name: 'RLR',            rule: 'RLR',          note: 'Chaotic growth.' },
  { name: 'LRRL',           rule: 'LRRL',         note: 'Square-spiral filling.' },
];

const DX = [0, 1, 0, -1], DY = [-1, 0, 1, 0];   // N, E, S, W

export function parseTurmite(text) {
  const s = String(text).replace(/\s+/g, '').toUpperCase();
  if (!/^[LRNU]{2,32}$/.test(s)) throw new SyntaxError(`turmite rule must be 2–32 letters of L/R/N/U (got "${text}")`);
  return s;
}

export function make({ rule = 'RL', ants = 1, movesPerGen = 8 } = {}) {
  rule = parseTurmite(rule);
  const k = rule.length;
  ants = Math.max(1, Math.min(64, ants | 0));
  movesPerGen = Math.max(1, Math.min(2000, movesPerGen | 0));
  const spec = { rule, ants, movesPerGen };
  return {
    family: 'turmite',
    spec,
    states: k,
    describe: () => `turmite ${rule}`,
    agents: [],
    init(grid, rng) {
      grid.clear();
      this.agents = [];
      for (let a = 0; a < ants; a++) {
        const x = ants === 1 ? grid.width >> 1 : Math.floor(rng() * grid.width);
        const y = ants === 1 ? grid.height >> 1 : Math.floor(rng() * grid.height);
        this.agents.push({ x, y, dir: ants === 1 ? 0 : Math.floor(rng() * 4), alive: true });
      }
    },
    step(grid) {
      const w = grid.width, h = grid.height, c = grid.cells;
      for (let m = 0; m < movesPerGen; m++) {
        for (const ant of this.agents) {
          if (!ant.alive) continue;
          const i = ant.y * w + ant.x, col = c[i];
          const t = rule[col];
          if (t === 'L') ant.dir = (ant.dir + 3) & 3;
          else if (t === 'R') ant.dir = (ant.dir + 1) & 3;
          else if (t === 'U') ant.dir = (ant.dir + 2) & 3;
          c[i] = (col + 1) % k;
          let nx = ant.x + DX[ant.dir], ny = ant.y + DY[ant.dir];
          if (nx < 0 || nx >= w || ny < 0 || ny >= h) {
            if (grid.boundary === 'torus') { nx = ((nx % w) + w) % w; ny = ((ny % h) + h) % h; }
            else if (grid.boundary === 'mirror') { ant.dir = (ant.dir + 2) & 3; nx = ant.x; ny = ant.y; }
            else { ant.alive = false; continue; }   // walked off a dead world
          }
          ant.x = nx; ant.y = ny;
        }
      }
      grid.generation++;
    },
  };
}
