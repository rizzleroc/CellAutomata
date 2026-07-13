// cellauto · web9 — the Instrument's measurement layer.
//
// web9 forks web8 (the guided lab, amoeba "slime" guide included) and adds what
// REAL_LAB_ROADMAP.md calls for: turn the micrograph from a picture into a
// MEASUREMENT. Every real step we sample the running stage's live height field
// and record a small time-series of honest observables — mean level ⟨h⟩,
// roughness σ² (field variance, a proxy for pattern amplitude), and peak — plus
// the rule's own population line. That series drives a live sparkline, a CSV
// export, and (with the run link) a shareable specimen.
//
// Zero-dependency and self-contained; nothing here mutates the simulation, so
// the science is unchanged — it only observes.

const MAX_POINTS = 4000; // rolling cap so a long run stays memory-bounded
const SPARK_POINTS = 240; // how many recent points the sparkline draws

export const Observables = {
  spark: null,
  sparkCtx: null,
  readEl: null,
  series: [], // [{ step, mean, rough, peak, pop }]
  label: '',
  _raf: 0,

  init(sparkCanvas, readEl) {
    this.spark = sparkCanvas || null;
    this.sparkCtx = this.spark && this.spark.getContext ? this.spark.getContext('2d') : null;
    this.readEl = readEl || null;
    this._draw();
    return this;
  },

  // Start a fresh time-series (called on every specimen load).
  reset(label) {
    this.label = label || '';
    this.series = [];
    this._render('—');
    this._draw();
  },

  // Take one measurement from the running rule + its height field.
  record(rule, heightBuf) {
    let mean = 0;
    let rough = 0;
    let peak = 0;
    if (heightBuf && heightBuf.length) {
      const n = heightBuf.length;
      let s = 0;
      let mx = 0;
      for (let i = 0; i < n; i++) {
        const v = heightBuf[i];
        s += v;
        if (v > mx) mx = v;
      }
      mean = s / n;
      let s2 = 0;
      for (let i = 0; i < n; i++) {
        const d = heightBuf[i] - mean;
        s2 += d * d;
      }
      rough = s2 / n; // variance
      peak = mx;
    }
    const step =
      rule && typeof rule.generation === 'function' ? rule.generation() | 0 : this.series.length;
    const pop = rule && typeof rule.population === 'function' ? String(rule.population()) : '';
    this.series.push({ step, mean, rough, peak, pop });
    if (this.series.length > MAX_POINTS) this.series.shift();
    this._render(this._fmt(mean, rough, peak, pop));
    this._scheduleDraw();
  },

  _fmt(mean, rough, peak, pop) {
    // roughness is a dimensionless field variance; ×10³ for a legible readout.
    const r = rough * 1000;
    const rs = r >= 100 ? r.toFixed(0) : r.toFixed(1);
    return `σ² ${rs}·10⁻³ · ⟨h⟩ ${mean.toFixed(3)}` + (pop ? ` · ${pop}` : '');
  },

  _render(text) {
    if (this.readEl) this.readEl.textContent = text;
  },

  _scheduleDraw() {
    if (this._raf || !this.sparkCtx || typeof requestAnimationFrame !== 'function') return;
    this._raf = requestAnimationFrame(() => {
      this._raf = 0;
      this._draw();
    });
  },

  _draw() {
    const ctx = this.sparkCtx;
    const cv = this.spark;
    if (!ctx || !cv) return;
    const W = cv.width;
    const H = cv.height;
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = 'rgba(9,12,17,0.55)';
    ctx.fillRect(0, 0, W, H);
    const s = this.series;
    if (s.length < 2) return;
    const vals = s.slice(-SPARK_POINTS).map((p) => p.rough);
    let mn = Infinity;
    let mx = -Infinity;
    for (const v of vals) {
      if (v < mn) mn = v;
      if (v > mx) mx = v;
    }
    const span = mx - mn || 1e-9;
    const pad = 3;
    const plotW = W - pad * 2;
    const plotH = H - pad * 2;
    const xAt = (i) => pad + (vals.length === 1 ? 0 : (i / (vals.length - 1)) * plotW);
    const yAt = (v) => pad + plotH - ((v - mn) / span) * plotH;
    ctx.beginPath();
    for (let i = 0; i < vals.length; i++) {
      const x = xAt(i);
      const y = yAt(vals[i]);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.strokeStyle = '#3fe0d0';
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.fillStyle = '#3fe0d0';
    ctx.beginPath();
    ctx.arc(xAt(vals.length - 1), yAt(vals[vals.length - 1]), 2, 0, 6.2832);
    ctx.fill();
  },

  // The measured time-series as CSV (for File-style download).
  toCSV() {
    const rows = [['step', 'mean_height', 'roughness_var', 'peak_height', 'population']];
    for (const p of this.series) {
      rows.push([
        p.step,
        p.mean.toFixed(6),
        p.rough.toFixed(8),
        p.peak.toFixed(6),
        '"' + String(p.pop).replace(/"/g, '""') + '"',
      ]);
    }
    return rows.map((r) => r.join(',')).join('\n');
  },

  count() {
    return this.series.length;
  },
};
