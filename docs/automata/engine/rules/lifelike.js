// lifelike.js — the outer-totalistic family: Life-like (B/S) and Generations
// (B/S/C) rules on the Moore or von Neumann neighbourhood.
//
// A rule is a pair of neighbour-count sets: a dead cell is BORN when its live
// neighbour count is in B, a live cell SURVIVES when its count is in S.
// Generations rules add C states: a cell that fails to survive does not die
// outright but ages through C−2 "dying" states (which count as dead for the
// neighbour tally) before clearing — Brian's Brain is B2/S/C3.
//
// Notation accepted by parseRule (all case-insensitive, whitespace ignored):
//   "B3/S23"  "b3s23"  "23/3" (S/B, the older convention)
//   "B2/S/C3" "/2/3" (S/B/C for Generations)   suffix "V" → von Neumann.
// formatRule emits the canonical "B…/S…[/C…][V]" form.

const MOORE_N = 8, VN_N = 4;

export function parseRule(text) {
  if (typeof text !== 'string') throw new TypeError('rule must be a string');
  let s = text.replace(/\s+/g, '').toUpperCase();
  if (!s) throw new SyntaxError('empty rule');
  let neighbourhood = 'moore';
  if (/V$/.test(s)) { neighbourhood = 'vn'; s = s.slice(0, -1); }
  const maxN = neighbourhood === 'vn' ? VN_N : MOORE_N;
  let birth, survive, states = 2;
  const digits = (str, what) => {
    const set = new Set();
    for (const ch of str) {
      if (!/[0-9]/.test(ch)) throw new SyntaxError(`bad ${what} digit "${ch}" in "${text}"`);
      const d = +ch;
      if (d > maxN) throw new SyntaxError(`${what} count ${d} exceeds the ${maxN}-cell neighbourhood in "${text}"`);
      set.add(d);
    }
    return set;
  };
  if (/^B[0-8]*\/?S[0-8]*(\/C?\d+)?$/.test(s)) {
    const m = s.match(/^B([0-8]*)\/?S([0-8]*)(?:\/C?(\d+))?$/);
    birth = digits(m[1], 'birth'); survive = digits(m[2], 'survival');
    if (m[3] !== undefined) states = +m[3];
  } else if (/^[0-8]*\/[0-8]*(\/\d+)?$/.test(s)) {
    const parts = s.split('/');
    survive = digits(parts[0], 'survival'); birth = digits(parts[1], 'birth');
    if (parts[2] !== undefined) states = +parts[2];
  } else {
    throw new SyntaxError(`unrecognised rule "${text}" — use B3/S23, 23/3, B2/S/C3 or /2/3`);
  }
  if (!Number.isInteger(states) || states < 2 || states > 255) {
    throw new RangeError(`Generations state count must be 2–255 (got ${states})`);
  }
  if (birth.has(0) && neighbourhood === 'moore' && states === 2 && survive.size === 9) {
    // B0/S012345678 saturates instantly — legal but degenerate; allowed.
  }
  return { birth, survive, states, neighbourhood };
}

export function formatRule(spec) {
  const d = (set) => [...set].sort((a, b) => a - b).join('');
  let s = `B${d(spec.birth)}/S${d(spec.survive)}`;
  if (spec.states > 2) s += `/C${spec.states}`;
  if (spec.neighbourhood === 'vn') s += 'V';
  return s;
}

// Langton's λ (1990): the fraction of all neighbourhood configurations that
// map to a live cell. For an outer-totalistic rule on N neighbours the
// configurations with k live neighbours number C(N,k), so λ is the binomially
// weighted measure of B ∪ S over the 2·2^N configurations. Life gives 140/512
// ≈ 0.273.
export function langtonLambda(spec) {
  const N = spec.neighbourhood === 'vn' ? VN_N : MOORE_N;
  let live = 0;
  for (let k = 0; k <= N; k++) {
    const c = binom(N, k);
    if (spec.birth.has(k)) live += c;      // centre dead → born
    if (spec.survive.has(k)) live += c;    // centre alive → survives
  }
  return live / (2 * (1 << N));
}
export function binom(n, k) {
  let r = 1;
  for (let i = 1; i <= k; i++) r = (r * (n - k + i)) / i;
  return Math.round(r);
}

// Named rules from the literature and from the Golly/LifeWiki catalogues.
// `cls` is the Wolfram class the rule is usually assigned in the literature —
// a label, not a measurement; the lab's measurement layer estimates its own.
export const CATALOG = [
  { name: "Conway's Life",       rule: 'B3/S23',          cls: 4, note: 'The original (Conway 1970). Gliders, guns, universal computation.' },
  { name: 'HighLife',            rule: 'B36/S23',         cls: 4, note: 'Life plus birth on 6 — has a small self-replicating pattern (Bell 1994).' },
  { name: 'Seeds',               rule: 'B2/S',            cls: 3, note: 'Nothing survives; everything is born. Explosive growth from any two cells.' },
  { name: 'Day & Night',         rule: 'B3678/S34678',    cls: 4, note: 'Symmetric under live↔dead swap — patterns run identically as holes.' },
  { name: 'Diamoeba',            rule: 'B35678/S5678',    cls: 4, note: 'Diamond-shaped amoebae with cellular interiors.' },
  { name: 'Anneal',              rule: 'B4678/S35678',    cls: 2, note: 'Majority-vote-like coarsening: domains smooth and merge over time.' },
  { name: 'Morley',              rule: 'B368/S245',       cls: 4, note: 'Small oscillators and puffers; named for Stephen Morley (Move).' },
  { name: '2×2',                 rule: 'B36/S125',        cls: 4, note: 'Block-invariant: 2×2 blocks evolve as a coarser automaton.' },
  { name: 'Life without Death',  rule: 'B3/S012345678',   cls: 2, note: 'Cells never die; growth throws slow, ladder-like "ladders".' },
  { name: 'Replicator',          rule: 'B1357/S1357',     cls: 3, note: 'Every pattern replicates itself (a linear XOR-like rule).' },
  { name: 'Coral',               rule: 'B3/S45678',       cls: 2, note: 'Slow-growing, branching coral textures.' },
  { name: 'Maze',                rule: 'B3/S12345',       cls: 2, note: 'Grows a maze of corridors from any seed.' },
  { name: 'Mazectric',           rule: 'B3/S1234',        cls: 2, note: 'Maze with longer, straighter corridors.' },
  { name: 'Coagulations',        rule: 'B378/S235678',    cls: 2, note: 'Expanding blobs that coagulate into stable clots.' },
  { name: 'Walled Cities',       rule: 'B45678/S2345',    cls: 2, note: 'Stable walled regions with chaotic interiors.' },
  { name: 'Vote',                rule: 'B5678/S45678',    cls: 2, note: 'Majority vote (Toffoli & Margolus): smooths a soup into domains.' },
  { name: 'Gnarl',               rule: 'B1/S1',           cls: 3, note: 'Grows gnarled crystalline fronts from a single cell.' },
  { name: 'Stains',              rule: 'B3678/S235678',   cls: 2, note: 'Ink-stain textures that stabilise.' },
  { name: 'Amoeba',              rule: 'B357/S1358',      cls: 4, note: 'Large amoeboid regions with chaotic interiors.' },
  { name: 'Pseudo Life',         rule: 'B357/S238',       cls: 4, note: 'Life-like dynamics with a different still-life set.' },
  { name: "Life (von Neumann)",  rule: 'B3/S23V',         cls: 1, note: 'Life on the 4-cell neighbourhood — dies out fast.' },
  // Generations
  { name: "Brian's Brain",       rule: 'B2/S/C3',         cls: 3, note: 'Three states: on, dying, off. A boiling sea of gliders (Silverman).' },
  { name: 'Star Wars',           rule: 'B2/S345/C4',      cls: 4, note: 'Ships, guns and spaceship-like structures with a 4-state decay.' },
  { name: 'Frogs',               rule: 'B34/S12/C3',      cls: 3, note: 'Hopping, frog-like oscillators.' },
  { name: 'Bloomerang',          rule: 'B34678/S234/C24', cls: 3, note: 'Long 24-state trails that bloom and return.' },
  { name: 'Faders',              rule: 'B2/S2/C25',       cls: 3, note: 'Slowly fading trails in 25 states.' },
  { name: 'Fireworks',           rule: 'B13/S2/C21',      cls: 3, note: 'Bursting rings that fade through 21 states.' },
  { name: 'Lava',                rule: 'B45678/S12345/C8',cls: 3, note: 'Flowing, molten textures.' },
  { name: 'Swirl',               rule: 'B34/S23/C8',      cls: 3, note: 'Turbulent swirls.' },
  { name: 'Transers',            rule: 'B26/S345/C5',     cls: 4, note: 'Ships that transfer along trails.' },
  { name: 'Worms',               rule: 'B25/S3467/C6',    cls: 3, note: 'Wriggling worm-like structures.' },
];

// ── The rule object ─────────────────────────────────────────────────────────
// make(spec) → { states, describe, step(grid), lambda, oneD:false }.
// step() writes grid.next synchronously and swaps. Generations semantics:
// only state 1 is "alive" for the neighbour count.
export function make(spec) {
  if (typeof spec === 'string') spec = parseRule(spec);
  const B = new Uint8Array(9), S = new Uint8Array(9);
  for (const k of spec.birth) B[k] = 1;
  for (const k of spec.survive) S[k] = 1;
  const C = spec.states;
  const kind = spec.neighbourhood;
  return {
    family: 'lifelike',
    spec,
    states: C,
    describe: () => formatRule(spec),
    lambda: langtonLambda(spec),
    step(grid) {
      const { K, tbl } = grid.neighbourhood(kind);
      const c = grid.cells, n = grid.next, N = c.length;
      for (let i = 0; i < N; i++) {
        let live = 0;
        const base = i * K;
        for (let k = 0; k < K; k++) { const j = tbl[base + k]; if (j >= 0 && c[j] === 1) live++; }
        const s = c[i];
        if (s === 0) n[i] = B[live] ? 1 : 0;
        else if (s === 1) n[i] = S[live] ? 1 : (C > 2 ? 2 : 0);
        else n[i] = s + 1 < C ? s + 1 : 0;
      }
      grid.swap();
    },
  };
}

// A random Life-like rule (used by the "random rule" button); optional λ
// target lets the lab sample the ordered/complex/chaotic bands of rule space.
export function randomRule(rng, { states = 2, neighbourhood = 'moore' } = {}) {
  const N = neighbourhood === 'vn' ? VN_N : MOORE_N;
  const birth = new Set(), survive = new Set();
  for (let k = 0; k <= N; k++) { if (rng() < 0.35) birth.add(k); if (rng() < 0.45) survive.add(k); }
  if (birth.size === 0) birth.add(1 + Math.floor(rng() * N));
  return { birth, survive, states, neighbourhood };
}
