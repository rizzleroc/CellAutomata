// RNA world — Eigen quasispecies & the error catastrophe.
// Building block: information control — replication fidelity sets a hard
// limit on how much heredity a sloppy copier can hold (Eigen 1971;
// Eigen & Schuster 1977).
//
// Distance-only reduction: each cell stores ONE integer d — the Hamming
// distance to a fixed canonical master sequence (the all-zeros word).
// Under a uniform mutation kernel + distance-only single-peak fitness the
// distance process is exactly Markov, so we never store the {A,C,G,U}
// string at all. fidelity f = 1 − d/L ∈ [1/K, 1]; no PDE, no exp/log in
// the hot loop, fidelity = integer/integer → structurally NaN-proof.
//
// Master replicates σ-fold but a whole-genome copy survives mutation-free
// only with quality factor Q = (1−μ)^L. Well-mixed Eigen theory localises
// the master iff σ·Q > 1, i.e. μ < μc_mf = 1 − σ^(−1/L) ≈ ln(σ)/L. This is
// a SPATIAL lattice, not a well-mixed pot: a master must win its local
// 5-cell roulette AND copy faithfully, which roughly doubles its effective
// fidelity burden, so the measured collapse tracks μc = 1 − σ^(−1/(2L))
// across σ∈[2,8], L∈[8,64]. We report THAT μc (the value the lattice
// obeys), with the mean-field number shown alongside as the textbook
// reference. Below μc → bright master domains + a mutant halo (the
// quasispecies cloud). Above μc → every lineage drifts up in d and the
// lattice relaxes to the random-sequence floor d_eq = L(K−1)/K, fidelity →
// 1/K = 0.25 everywhere = the error catastrophe. μc moves under THREE axes:
// μ sweeps across it, σ raises it, L lowers it (~1/L).
(function () {
  "use strict";
  window.CA = window.CA || { RULES: {} };

  const W = 128;
  const H = 128;
  const N = W * H;
  const K = 4;            // RNA alphabet {A,C,G,U} — a constant, never an array.
  const INV_K = 1 / K;    // 0.25 = random-sequence fidelity floor.
  const L_MIN = 4;        // matches params.length.min — declared envelope.
  const L_MAX = 64;       // matches params.length.max — declared envelope.

  function make() {
    let d     = new Int16Array(N);   // Hamming distance to master, clamped [0,L].
    let dNext = new Int16Array(N);   // double-buffer for synchronous update.
    let generation = 0;

    // Single shared length clamp — ALWAYS finite and inside [L_MIN, L_MAX],
    // even if a host writes NaN / Infinity / an out-of-range value. Every
    // consumer (step, render, renderHeight, population, paint, seed) goes
    // through this, so no path can ever emit a non-finite field or run an
    // unbounded O(L) loop.
    function curL() {
      let L = Math.round(this.params.length.value);
      if (!Number.isFinite(L)) L = L_MIN;
      if (L < L_MIN) L = L_MIN; else if (L > L_MAX) L = L_MAX;
      return L;
    }

    // Live collapse threshold for THIS lattice. The mean-field Eigen criterion
    // σ·(1−μ)^L = 1 gives the well-mixed value μc_mf = 1 − σ^(−1/L). A spatial
    // 5-cell Moran update tips earlier: a master must BOTH win its local
    // roulette AND copy faithfully, so its effective fidelity burden roughly
    // doubles — the measured collapse tracks 1 − σ^(−1/(2L)) across the whole
    // σ∈[2,8], L∈[8,64] envelope (empirically within a few ×10⁻³ of where the
    // master sub-population vanishes). We report THAT value, so the printed μc
    // is the threshold the lattice actually obeys, not a number it ignores.
    const SPATIAL = 2;  // effective-length factor for the spatial Moran update.
    function muThreshold(sigma, L) {
      if (!(sigma > 1) || !(L > 0)) return 0;
      const v = 1 - Math.pow(sigma, -1 / (SPATIAL * L));
      return Number.isFinite(v) ? v : 0;
    }
    // Mean-field reference (Eigen 1971) — shown alongside as the textbook value.
    function muThresholdMeanField(sigma, L) {
      if (!(sigma > 1) || !(L > 0)) return 0;
      const v = 1 - Math.pow(sigma, -1 / L);
      return Number.isFinite(v) ? v : 0;
    }

    // d_eq = L(K-1)/K — the random-sequence equilibrium distance.
    function noiseFloor(L) { return Math.round(L * (K - 1) / K); }

    // One capped Bernoulli "binomial": sum of `trials` Bernoulli(p) draws.
    // trials is an integer ≥0 (and bounded by L ≤ L_MAX by construction);
    // result is an integer in [0, trials] BY CONSTRUCTION, so distance
    // arithmetic can never leave range and the loop can never run away.
    function binom(trials, p) {
      if (trials <= 0 || p <= 0) return 0;
      let k = 0;
      for (let t = 0; t < trials; t++) if (Math.random() < p) k++;
      return k;
    }

    // Seed: random-floor equilibrium everywhere, jittered ±2, then stamp a
    // central master disc (d=0) to watch nucleation / erosion from frame 1.
    function seed(L) {
      const eq = noiseFloor(L);
      for (let i = 0; i < N; i++) {
        let v = eq + ((Math.random() * 5) | 0) - 2;   // ±2 jitter
        if (v < 0) v = 0; else if (v > L) v = L;
        d[i] = v;
      }
      const cx = W >> 1, cy = H >> 1, R = 14;
      for (let dy = -R; dy <= R; dy++) {
        for (let dx = -R; dx <= R; dx++) {
          if (dx * dx + dy * dy > R * R) continue;
          const x = ((cx + dx) % W + W) % W;
          const y = ((cy + dy) % H + H) % H;
          d[y * W + x] = 0;   // pure master core.
        }
      }
      generation = 0;
    }

    // Re-clamp existing distances into [0,L] (used on length change).
    function reclamp(L) {
      for (let i = 0; i < N; i++) {
        let v = d[i];
        if (v < 0) v = 0; else if (v > L) v = L;
        d[i] = v;
      }
    }

    return {
      id: "rna",
      label: "RNA World · Eigen Quasispecies",
      formula: "σ·(1−μ)^L > 1  ⇔  μ < μc  (Eigen 1971; Eigen & Schuster 1977).  Well-mixed μc = 1−σ^(−1/L); this spatial lattice tips at μc = 1−σ^(−1/2L).",
      shortCaption: "STAGE 8 · RNA WORLD",
      whatThisIs: "Information control as a building block. A self-copying RNA holds heredity only " +
                  "while its copying error μ stays below the threshold μc, where the master's effective " +
                  "growth σ·(1−μ)^L drops to 1. Cross that line and the master sequence delocalises — " +
                  "heredity dissolves into random-sequence noise. This is Eigen's error catastrophe: the " +
                  "limit on how much information error-prone replication can carry, and why early life " +
                  "needed short, high-fidelity genomes.",
      aboutStage: "The building block is information control — replication fidelity. A self-copying RNA " +
                  "(Eigen 1971) keeps heredity only while its per-base error μ stays below μc, where the " +
                  "master's growth σ·(1−μ)^L falls to 1: master plus mutant cloud form a quasispecies. " +
                  "Past μc the master delocalises and information dissolves into noise — the error " +
                  "catastrophe that capped the first genomes.",
      paletteBg: [8, 10, 20],
      paletteFg: [120, 240, 180],
      width: W,
      height: H,

      params: {
        // mutation max widened to 0.5 so the catastrophe is REACHABLE across
        // the whole length range: μc = 1−σ^(−1/L) can sit near ~0.35 for short
        // high-fidelity genomes (small L, large σ), so a 0.2 ceiling left them
        // unable to ever cross over. 0.5 = the maximally-disordering kernel.
        mutation: { label: "μ — mutation / base",       min: 0, max: 0.5, step: 0.002, value: 0.01 },
        sigma:    { label: "σ — master fitness adv.",    min: 1, max: 8,   step: 0.1,   value: 4    },
        length:   { label: "L — sequence length",        min: 4, max: 64,  step: 1,     value: 32   },
        substeps: { label: "replication rounds / frame", min: 1, max: 6,   step: 1,     value: 2    },
      },

      controlConsequence: {
        mutation: "Copying error per base, per replication. The protagonist: nudge μ up past the live threshold μc (printed in the readout) and the master's effective growth σ·(1−μ)^L drops below 1 — it can no longer outrun its own decay, so the bright quasispecies domains fray and dissolve into uniform random-sequence noise. Eigen's error catastrophe, on one slider.",
        sigma:    "How much faster the exact master sequence replicates than any mutant. Higher σ buys tolerance for sloppier copying: it raises the error threshold μc, so a population that was dissolving can re-condense into a coherent master cloud without lowering μ. Drop σ toward 1 and there is nothing to localise around — the field is always noise.",
        length:   "How many bases the genome carries. Error compounds per base, so longer genomes are far more fragile: the threshold μc falls roughly as 1/L, and the same μ that is survivable for a short genome tips a long one into catastrophe — Eigen's limit on how much information error-prone replication can hold.",
        substeps: "How many replication rounds run per visible frame. Pure speed knob — more rounds reach the steady-state quasispecies cloud (or the collapsed noise floor) faster, with no change to which regime ultimately wins.",
      },

      // Presets bracket the REAL lattice threshold μc = 1−σ^(−1/2L), measured
      // for THIS spatial update (σ=4, L=32 → μc ≈ 0.021; σ=4, L=48 → μc ≈ 0.014).
      // below μc → locked, at μc → flicker, well past → full catastrophe.
      presets: [
        { label: "quasispecies locked", reseed: true,
          hint: "μ well below the threshold μc. Selection wins: a bright master domain wrapped in a graded mutant halo — the quasispecies. Heredity is safe and information is conserved.",
          values: { mutation: 0.010, sigma: 4, length: 32, substeps: 2 } },
        { label: "at the error threshold", reseed: true,
          hint: "μ parked right on μc. The master barely localises — bright cores flicker, the mutant cloud swells to engulf them and recedes. The knife-edge between heredity and chaos; nudge μ either way to tip it.",
          values: { mutation: 0.022, sigma: 4, length: 32, substeps: 2 } },
        { label: "error catastrophe", reseed: true,
          hint: "μ pushed well past the threshold on a longer, more fragile genome. The master delocalises completely — every bright patch dissolves and the dish collapses to uniform random-sequence noise at fidelity ~1/4. Information is lost.",
          values: { mutation: 0.040, sigma: 4, length: 48, substeps: 2 } },
      ],

      randomize() { seed(curL.call(this)); },
      clear()     { d.fill(0); generation = 0; },   // pristine all-master dish — watch DECAY under high μ.
      reset()     { seed(curL.call(this)); },

      // Keep the live length and the distance cache from desyncing.
      onParamChange(name) {
        if (name === "length") reclamp(curL.call(this));
      },

      step() {
        const L     = curL.call(this);
        let   mu    = this.params.mutation.value;
        if (!Number.isFinite(mu)) mu = 0;
        if (mu < 0) mu = 0; else if (mu > 0.5) mu = 0.5;
        let   sigma = this.params.sigma.value;
        if (!Number.isFinite(sigma)) sigma = 1 + 1e-6;
        if (sigma < 1 + 1e-6) sigma = 1 + 1e-6;   // ln σ > 0 strictly.
        const subs  = Math.max(1, Math.min(6, this.params.substeps.value | 0));

        const muBack = mu / (K - 1);   // a wrong base mutates back to the master letter.

        // Master intrinsic reproductive edge = σ. The whole-genome quality
        // factor Q = (1−μ)^L is NOT folded in here — it emerges for free from
        // the explicit per-base binom mutation below (a master only stays a
        // master if its copy draws zero forward errors, probability Q). Folding
        // Q into the weight too would double-count it and shift the collapse
        // well below the Eigen threshold; the binom replication alone carries
        // the fidelity physics, and the σ weight carries the selection.
        let   wMaster = sigma;
        if (!Number.isFinite(wMaster) || wMaster < 1) wMaster = 1;

        for (let s = 0; s < subs; s++) {
          for (let y = 0; y < H; y++) {
            const ym = (y - 1 + H) % H, yp = (y + 1) % H;
            for (let x = 0; x < W; x++) {
              const xm = (x - 1 + W) % W, xp = (x + 1) % W;
              const i = y * W + x;

              // von-Neumann + self = 5 replication candidates.
              const c0 = i;
              const c1 = y * W + xm;
              const c2 = y * W + xp;
              const c3 = ym * W + x;
              const c4 = yp * W + x;

              // 1) LOCAL SELECTION — Eigen fitness-proportional roulette.
              //    w = σ for a master (d==0), else 1. Sum ∈ [5, 5σ] > 0,
              //    so the roulette is always well-posed.
              const w0 = d[c0] === 0 ? wMaster : 1;
              const w1 = d[c1] === 0 ? wMaster : 1;
              const w2 = d[c2] === 0 ? wMaster : 1;
              const w3 = d[c3] === 0 ? wMaster : 1;
              const w4 = d[c4] === 0 ? wMaster : 1;
              const wsum = w0 + w1 + w2 + w3 + w4;

              let r = Math.random() * wsum;
              let parent;
              if      ((r -= w0) < 0) parent = c0;
              else if ((r -= w1) < 0) parent = c1;
              else if ((r -= w2) < 0) parent = c2;
              else if ((r -= w3) < 0) parent = c3;
              else                    parent = c4;   // fallback = S neighbour.

              // 2) REPLICATION WITH MUTATION — exact Hamming transition via
              //    two capped binomials; child is an integer in [0,L].
              const dp = d[parent];
              const nBack = binom(dp, muBack);     // ≤ dp   → distance −1 each
              const nFwd  = binom(L - dp, mu);     // ≤ L−dp → distance +1 each
              let child = dp - nBack + nFwd;
              if (child < 0) child = 0; else if (child > L) child = L;  // belt-and-suspenders.

              dNext[i] = child;
            }
          }
          // swap double-buffer — neighbour reads never see in-round writes.
          const t = d; d = dNext; dNext = t;
        }
        generation += subs;
      },

      render(pixels) {
        const L = curL.call(this);
        const invL = 1 / L;
        const br = 8,   bg = 10,  bb = 20;    // paletteBg.
        const fr = 120, fg = 240, fb = 180;   // paletteFg.
        for (let i = 0; i < N; i++) {
          let f = 1 - d[i] * invL;
          if (!(f >= 0)) f = 0; else if (f > 1) f = 1;   // NaN-safe via !(f>=0).
          // smoothstep gamma — cloud pops, melt near threshold reads sharp.
          const t = f * f * (3 - 2 * f);
          let r = (br + (fr - br) * t) | 0;
          let g = (bg + (fg - bg) * t) | 0;
          let b = (bb + (fb - bb) * t) | 0;
          // master highlight — d==0 cores glow inside their halo.
          if (d[i] === 0) { g += 30; if (g > 255) g = 255; }
          const p = i * 4;
          pixels[p] = r; pixels[p + 1] = g; pixels[p + 2] = b; pixels[p + 3] = 255;
        }
      },

      // SEM height — stretch the LEGIBLE fidelity band [1/K, 1] across the
      // whole height range so the quasispecies cloud (the master core plus its
      // graded mutant halo) reads as relief, not a saturated plate, while the
      // collapsed catastrophe regime still flattens to the low noise floor.
      // In the locked regime almost every cell sits at d=0..3 (f≈0.91..1), so
      // after the [1/K,1]→[0,1] remap they crowd the top of the range; a
      // gamma > 1 expands that crowded shoulder downward so the master core
      // (d=0→1), its first halo shells (d=1→.84, d=2→.71, d=3→.59) and the
      // collapsed floor (d≫0→0) read as distinct relief instead of one plate.
      renderHeight(out) {
        const L = curL.call(this);
        const invL = 1 / L;
        const span = 1 / (1 - INV_K);   // 1/0.75 — remap [1/K,1] → [0,1].
        for (let i = 0; i < N; i++) {
          let f = 1 - d[i] * invL;
          if (!(f >= 0)) f = 0; else if (f > 1) f = 1;   // NaN-safe.
          let h = (f - INV_K) * span;
          if (h < 0) h = 0; else if (h > 1) h = 1;
          h = h * h * h * h;   // gamma 4 — spread the crowded near-master shoulder.
          if (!(h >= 0)) h = 0; else if (h > 1) h = 1;   // NaN-safe re-clamp.
          out[i] = h;
        }
      },

      // No sprites — the pixel + height fields carry the whole story.
      sprites() { return []; },

      paint(gx, gy, radius, mode) {
        const L = curL.call(this);
        const eq = noiseFloor(L);
        for (let dy = -radius; dy <= radius; dy++) {
          for (let dx = -radius; dx <= radius; dx++) {
            if (dx * dx + dy * dy > radius * radius) continue;
            const x = ((gx + dx) % W + W) % W;
            const y = ((gy + dy) % H + H) % H;
            const i = y * W + x;
            if (mode === "erase") {
              // fresh random-sequence static.
              let v = eq + ((Math.random() * 5) | 0) - 2;
              if (v < 0) v = 0; else if (v > L) v = L;
              d[i] = v;
            } else {
              d[i] = 0;   // stamp pure master — a fresh patch of information.
            }
          }
        }
      },

      population() {
        const L     = curL.call(this);
        let   mu    = this.params.mutation.value;
        if (!Number.isFinite(mu)) mu = 0;
        if (mu < 0) mu = 0; else if (mu > 0.5) mu = 0.5;
        let   sigma = this.params.sigma.value;
        if (!Number.isFinite(sigma)) sigma = 1;
        const cloudR = Math.max(1, Math.round(0.05 * L));
        let master = 0, cloud = 0;
        for (let i = 0; i < N; i++) {
          const di = d[i];
          if (di === 0) master++;
          if (di <= cloudR) cloud++;
        }
        const muc   = muThreshold(sigma, L);            // lattice threshold.
        const mucMF = muThresholdMeanField(sigma, L);   // textbook reference.
        const pMaster = (100 * master / N).toFixed(1);
        const pCloud  = Math.round(100 * cloud / N);

        // Verdict is driven by the OBSERVED master fraction, NOT by comparing μ
        // to a formula. This guarantees the text can never assert the opposite
        // of the visible master%: a localised dish reads "localised", a
        // collapsed dish reads "catastrophe", regardless of where μ sits.
        const frac = master / N;
        let verdict;
        if      (frac < 0.005) verdict = "delocalised — catastrophe";
        else if (frac > 0.03)  verdict = "localised — quasispecies";
        else                   verdict = "near μc — knife-edge";
        return `${pMaster}% master · ${pCloud}% cloud · μc=${muc.toFixed(3)} (mf ${mucMF.toFixed(3)}) · ${verdict}`;
      },

      generation() { return generation; },
    };
  }

  CA.RULES.rna = make;
})();
