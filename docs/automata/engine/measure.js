// measure.js — the instrument layer: what the lab MEASURES about a run.
//
//   population   — non-zero cells (and the density = population / cells)
//   activity     — fraction of cells that changed state in the last step
//   entropy      — Shannon entropy (bits) of the 2×2 block distribution of the
//                  live/dead field: 0 for a blank or uniform lattice, 4 for a
//                  maximally disordered one. Structure lowers it; noise raises it.
//   classify     — an ESTIMATE of the Wolfram class from the activity series:
//                  I fixed (activity reaches 0), II periodic (the activity
//                  series repeats with a short period), III chaotic (high,
//                  aperiodic activity), IV complex (low but aperiodic activity).
//                  A heuristic, labelled as one in the UI.

export function population(grid) { return grid.population(); }
export function density(grid) { return grid.population() / grid.size; }

export function activity(grid, prevCells) {
  const c = grid.cells; let d = 0;
  for (let i = 0; i < c.length; i++) if (c[i] !== prevCells[i]) d++;
  return d / c.length;
}

export function blockEntropy(grid) {
  const w = grid.width, h = grid.height, c = grid.cells;
  const hist = new Uint32Array(16);
  let total = 0;
  for (let y = 0; y + 1 < h; y++) for (let x = 0; x + 1 < w; x++) {
    const i = y * w + x;
    const code = (c[i] ? 1 : 0) | (c[i + 1] ? 2 : 0) | (c[i + w] ? 4 : 0) | (c[i + w + 1] ? 8 : 0);
    hist[code]++; total++;
  }
  let H = 0;
  for (let k = 0; k < 16; k++) if (hist[k]) { const p = hist[k] / total; H -= p * Math.log2(p); }
  return H;
}

// Period detection: smallest p ≤ maxP such that series repeats exactly over
// the trailing window. Returns 0 when no period is found.
export function periodOf(series, maxP = 32, tol = 0) {
  const n = series.length;
  for (let p = 1; p <= maxP; p++) {
    if (n < 3 * p) break;
    let okp = true;
    for (let i = n - 2 * p; i < n; i++) {
      if (Math.abs(series[i] - series[i - p]) > tol) { okp = false; break; }
    }
    if (okp) return p;
  }
  return 0;
}

export function classify(activitySeries, { window = 64 } = {}) {
  const s = activitySeries.slice(-window);
  if (s.length < 8) return { cls: 0, label: '—', why: 'not enough history yet' };
  const last = s[s.length - 1];
  if (last === 0 && s.slice(-4).every((v) => v === 0)) return { cls: 1, label: 'I · fixed', why: 'activity has fallen to zero' };
  const p = periodOf(s, 24, 1e-12);
  if (p > 0) return { cls: 2, label: 'II · periodic', why: `activity repeats with period ${p}` };
  const mean = s.reduce((a, b) => a + b, 0) / s.length;
  if (mean > 0.12) return { cls: 3, label: 'III · chaotic', why: `high aperiodic activity (mean ${(mean * 100).toFixed(1)}%)` };
  return { cls: 4, label: 'IV · complex', why: `low aperiodic activity (mean ${(mean * 100).toFixed(1)}%)` };
}

// A rolling log of per-generation observables (for the sparkline + CSV).
export class RunLog {
  constructor(cap = 2000) { this.cap = cap; this.rows = []; }
  push(row) { this.rows.push(row); if (this.rows.length > this.cap) this.rows.splice(0, this.rows.length - this.cap); }
  clear() { this.rows.length = 0; }
  series(key) { return this.rows.map((r) => r[key]); }
  toCSV() {
    const keys = ['generation', 'population', 'density', 'activity', 'entropy'];
    return [keys.join(','), ...this.rows.map((r) => keys.map((k) => (typeof r[k] === 'number' ? +r[k].toFixed(6) : r[k])).join(','))].join('\n');
  }
}
