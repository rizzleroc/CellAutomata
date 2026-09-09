// grid.js — the lattice every automaton in the lab runs on.
//
// A Grid is a w×h lattice of small-integer states (Uint8Array, so up to 256
// states) with a second buffer for synchronous update and a boundary policy:
//   'torus' — edges wrap (the default: the lattice is a closed surface, so
//             gliders and waves never fall off the world);
//   'dead'  — everything outside the lattice is permanently state 0;
//   'mirror'— the lattice is reflected at its edges.
// Rules never index the raw arrays for neighbours; they go through `idx`
// (boundary-aware) or, for the hot Moore/von-Neumann paths, `neighbourhood`
// tables built once per grid. Every random draw in the lab comes from the
// seeded mulberry32 generator, so a (seed, rule, size) triple is reproducible
// and a run URL re-creates the identical experiment.

export function mulberry32(seed) {
  let a = (seed >>> 0) || 0x9e3779b9;
  return function rng() {
    a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export const BOUNDARIES = ['torus', 'dead', 'mirror'];

export class Grid {
  constructor(width, height, { boundary = 'torus' } = {}) {
    if (!Number.isInteger(width) || !Number.isInteger(height) || width < 1 || height < 1) {
      throw new RangeError(`Grid: bad size ${width}×${height}`);
    }
    if (!BOUNDARIES.includes(boundary)) throw new RangeError(`Grid: unknown boundary "${boundary}"`);
    this.width = width; this.height = height; this.boundary = boundary;
    this.cells = new Uint8Array(width * height);
    this.next = new Uint8Array(width * height);
    this.generation = 0;
  }

  get size() { return this.width * this.height; }

  // Boundary-aware index. Returns -1 when the cell lies outside a 'dead' world.
  idx(x, y) {
    const w = this.width, h = this.height;
    if (x >= 0 && x < w && y >= 0 && y < h) return y * w + x;
    switch (this.boundary) {
      case 'torus':
        x = ((x % w) + w) % w; y = ((y % h) + h) % h;
        return y * w + x;
      case 'mirror':
        x = reflect(x, w); y = reflect(y, h);
        return y * w + x;
      default:
        return -1;
    }
  }
  get(x, y) { const i = this.idx(x, y); return i < 0 ? 0 : this.cells[i]; }
  set(x, y, v) { const i = this.idx(x, y); if (i >= 0) this.cells[i] = v; }

  clear() { this.cells.fill(0); this.next.fill(0); this.generation = 0; }

  // Fill with a random "soup": each cell is non-zero with probability
  // `density`; non-zero cells draw uniformly from 1..states-1.
  randomize(rng, density = 0.35, states = 2) {
    const c = this.cells, n = c.length, k = Math.max(1, states - 1);
    for (let i = 0; i < n; i++) c[i] = rng() < density ? 1 + Math.floor(rng() * k) : 0;
    this.generation = 0;
  }

  // Stamp a pattern ({width,height,cells}) with its top-left at (ox, oy).
  // Non-zero pattern cells overwrite; zero cells are transparent unless
  // `opaque` is set (used by the eraser and by "clear + place").
  stamp(pattern, ox, oy, { opaque = false } = {}) {
    for (let py = 0; py < pattern.height; py++) {
      for (let px = 0; px < pattern.width; px++) {
        const v = pattern.cells[py * pattern.width + px];
        if (v || opaque) this.set(ox + px, oy + py, v);
      }
    }
  }
  // Stamp centred on the lattice.
  stampCentered(pattern, opts) {
    this.stamp(pattern, (this.width - pattern.width) >> 1, (this.height - pattern.height) >> 1, opts);
  }

  swap() { const t = this.cells; this.cells = this.next; this.next = t; this.generation++; }

  clone() {
    const g = new Grid(this.width, this.height, { boundary: this.boundary });
    g.cells.set(this.cells); g.generation = this.generation;
    return g;
  }

  population(state) {
    const c = this.cells; let n = 0;
    if (state === undefined) { for (let i = 0; i < c.length; i++) if (c[i]) n++; }
    else { for (let i = 0; i < c.length; i++) if (c[i] === state) n++; }
    return n;
  }

  // Bounding box of non-zero cells, or null when empty.
  bounds() {
    let x0 = this.width, y0 = this.height, x1 = -1, y1 = -1;
    const c = this.cells, w = this.width;
    for (let i = 0; i < c.length; i++) {
      if (!c[i]) continue;
      const x = i % w, y = (i / w) | 0;
      if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
    }
    return x1 < 0 ? null : { x0, y0, x1, y1, width: x1 - x0 + 1, height: y1 - y0 + 1 };
  }

  // Neighbour-offset tables for the two classical neighbourhoods, resolved
  // per cell under the boundary policy. Built lazily and cached per (grid,
  // neighbourhood); rules call `grid.neighbourhood('moore')` and then read
  // `tbl[i*K + k]` (an index, or -1 when outside a dead world).
  neighbourhood(kind = 'moore') {
    this._nb = this._nb || {};
    const key = kind + ':' + this.boundary;
    if (this._nb[key]) return this._nb[key];
    const offs = kind === 'vn'
      ? [[0, -1], [-1, 0], [1, 0], [0, 1]]
      : [[-1, -1], [0, -1], [1, -1], [-1, 0], [1, 0], [-1, 1], [0, 1], [1, 1]];
    const K = offs.length, w = this.width, h = this.height;
    const tbl = new Int32Array(w * h * K);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const base = (y * w + x) * K;
      for (let k = 0; k < K; k++) tbl[base + k] = this.idx(x + offs[k][0], y + offs[k][1]);
    }
    const out = { K, tbl };
    this._nb[key] = out;
    return out;
  }
  invalidateTables() { this._nb = null; }
}

function reflect(v, n) {
  if (n === 1) return 0;
  const period = 2 * n;
  v = ((v % period) + period) % period;
  return v < n ? v : period - 1 - v;
}
