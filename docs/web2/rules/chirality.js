// Homochirality — Frank's autocatalytic enantiomer-amplification kinetics
// on a 2-D lattice.  Simplified port of cellauto/rules/abiogenesis/
// stage_chirality.py.
//
// PDE per cell (Frank 1953):
//   dL/dt = α L (1 − L − R) − β L R
//   dR/dt = α R (1 − L − R) − β L R
// plus a small diffusive coupling and additive Gaussian noise (the
// stochastic kick that breaks the mirror symmetry).
//
// The chiral excess at each pixel is |L − R|; renderHeight uses it
// directly so a winning enantiomer reads as a depth-shaded crystalline
// patch under SEM mode.
(function () {
  "use strict";
  window.CA = window.CA || { RULES: {} };

  const W = 160;
  const H = 160;

  function make() {
    let L = new Float32Array(W * H);
    let R = new Float32Array(W * H);
    let Ln = new Float32Array(W * H);
    let Rn = new Float32Array(W * H);
    let generation = 0;

    function seed() {
      // Tiny symmetric base + a hair of noise; the symmetry breaks itself.
      for (let i = 0; i < L.length; i++) {
        L[i] = 0.10 + (Math.random() - 0.5) * 0.01;
        R[i] = 0.10 + (Math.random() - 0.5) * 0.01;
      }
      generation = 0;
    }

    return {
      id: "chirality",
      label: "Homochirality · Frank kinetics",
      formula: "dL/dt = αL(1−L−R) − βLR;   dR/dt = αR(1−L−R) − βLR  (Frank 1953).",
      shortCaption: "STAGE 6 · HOMOCHIRALITY",
      whatThisIs: "Symmetry-breaking as a building block. A racemic 50/50 mix of left- and " +
                  "right-handed molecules spontaneously collapses to one handedness. Real biology " +
                  "uses only L-amino-acids and D-sugars — this is the mathematical answer to why.",
      paletteBg: [10, 14, 22],
      paletteFg: [230, 224, 208],
      width: W,
      height: H,

      params: {
        alpha:     { label: "α — autocatalytic growth", min: 0.01, max: 0.30, step: 0.005, value: 0.12 },
        beta:      { label: "β — mutual inhibition",    min: 0.05, max: 1.50, step: 0.01,  value: 0.50 },
        diffusion: { label: "diffusion D",              min: 0.00, max: 0.30, step: 0.01,  value: 0.10 },
        noise:     { label: "symmetry-breaking noise",  min: 0.00, max: 0.05, step: 0.001, value: 0.005 },
      },

      controlConsequence: {
        alpha:     "How fast each enantiomer reproduces itself. Raise it: symmetry breaks faster. Lower it: the racemic state lingers.",
        beta:      "How strongly L and R inhibit each other. This is the term that BREAKS the symmetry — set β=0 and the system stays racemic forever, no matter what.",
        diffusion: "Smooths out local imbalances. Raise it: one enantiomer eventually wins globally. Lower it: rival domains persist in stable patches.",
        noise:     "The random kick that lets the system fall off the racemic ridge. With zero noise it's metastable forever; a real noise floor is essential.",
      },

      randomize() { seed(); },
      clear() { L.fill(0); R.fill(0); generation = 0; },
      reset() { seed(); },

      step() {
        const a = this.params.alpha.value;
        const b = this.params.beta.value;
        const D = this.params.diffusion.value;
        const sigma = this.params.noise.value;
        const dt = 0.4;

        for (let y = 0; y < H; y++) {
          const ym = (y - 1 + H) % H, yp = (y + 1) % H;
          for (let x = 0; x < W; x++) {
            const xm = (x - 1 + W) % W, xp = (x + 1) % W;
            const ic = y * W + x;
            const lapL = L[y*W+xm]+L[y*W+xp]+L[ym*W+x]+L[yp*W+x] - 4*L[ic];
            const lapR = R[y*W+xm]+R[y*W+xp]+R[ym*W+x]+R[yp*W+x] - 4*R[ic];
            const Lc = L[ic], Rc = R[ic];
            const rxnL = a*Lc*(1 - Lc - Rc) - b*Lc*Rc;
            const rxnR = a*Rc*(1 - Lc - Rc) - b*Lc*Rc;
            const noise = sigma * (Math.random() - 0.5);
            let nl = Lc + dt * (D * lapL + rxnL) + noise;
            let nr = Rc + dt * (D * lapR + rxnR) - noise;
            if (nl < 0) nl = 0; else if (nl > 1) nl = 1;
            if (nr < 0) nr = 0; else if (nr > 1) nr = 1;
            Ln[ic] = nl; Rn[ic] = nr;
          }
        }
        const tL = L; L = Ln; Ln = tL;
        const tR = R; R = Rn; Rn = tR;
        generation++;
      },

      render(pixels) {
        // L wins → bone-white; R wins → magenta; racemic → grey.
        for (let i = 0; i < L.length; i++) {
          const l = L[i], r = R[i];
          const total = Math.max(0.001, l + r);
          const chiral = (l - r) / total;     // -1..+1
          const intensity = Math.min(1, total);
          const p = i * 4;
          if (chiral >= 0) {
            pixels[p]   = (230 * intensity) | 0;
            pixels[p+1] = (224 * intensity) | 0;
            pixels[p+2] = (208 * intensity) | 0;
          } else {
            pixels[p]   = (212 * intensity) | 0;
            pixels[p+1] = ( 57 * intensity) | 0;
            pixels[p+2] = (164 * intensity) | 0;
          }
          pixels[p+3] = 255;
        }
      },

      // SEM height = chiral excess magnitude.  Racemic = flat substrate;
      // pure handedness = raised crystalline mound.
      renderHeight(out) {
        for (let i = 0; i < L.length; i++) {
          out[i] = Math.abs(L[i] - R[i]);
        }
      },

      paint(gx, gy, radius, mode) {
        const which = mode === "erase" ? "erase" : (Math.random() < 0.5 ? "L" : "R");
        for (let dy = -radius; dy <= radius; dy++) {
          for (let dx = -radius; dx <= radius; dx++) {
            if (dx*dx + dy*dy > radius*radius) continue;
            const x = ((gx + dx) % W + W) % W;
            const y = ((gy + dy) % H + H) % H;
            const i = y * W + x;
            if (which === "erase") { L[i] = R[i] = 0; }
            else if (which === "L") { L[i] = Math.min(1, L[i] + 0.4); }
            else                    { R[i] = Math.min(1, R[i] + 0.4); }
          }
        }
      },

      population() {
        let sumL = 0, sumR = 0;
        for (let i = 0; i < L.length; i++) { sumL += L[i]; sumR += R[i]; }
        const total = Math.max(1, sumL + sumR);
        const ee = ((sumL - sumR) / total * 100);
        return `ee ${ee.toFixed(1)}%`;
      },

      generation() { return generation; },
    };
  }

  CA.RULES.chirality = make;
})();
