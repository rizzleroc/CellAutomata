// Coacervate — Cahn-Hilliard liquid–liquid phase separation.
// Simplified port of cellauto/rules/abiogenesis/stage_coacervate.py
// (which implements Oparin's coacervate hypothesis via the
// Cahn-Hilliard equation, Banani et al. 2017).
//
// ∂φ/∂t = M ∇²( φ³ − φ − κ ∇²φ )
//
// φ ∈ [−1, +1].  Negative phase = dilute solvent; positive phase =
// coacervate droplet.  Random initial condition → spinodal decomposition
// → coarsening droplets.
(function () {
  "use strict";
  window.CA = window.CA || { RULES: {} };

  const W = 160;
  const H = 160;

  function make() {
    let phi   = new Float32Array(W * H);
    let mu    = new Float32Array(W * H);
    let lapPhi = new Float32Array(W * H);
    let phiN   = new Float32Array(W * H);
    let generation = 0;

    function seed() {
      // ±0.05 noise around zero — meta-stable, separates spontaneously.
      for (let i = 0; i < phi.length; i++) phi[i] = (Math.random() - 0.5) * 0.1;
      generation = 0;
    }

    function laplacian(src, dst) {
      for (let y = 0; y < H; y++) {
        const ym = (y - 1 + H) % H, yp = (y + 1) % H;
        for (let x = 0; x < W; x++) {
          const xm = (x - 1 + W) % W, xp = (x + 1) % W;
          const ic = y * W + x;
          dst[ic] = src[y*W+xm] + src[y*W+xp] + src[ym*W+x] + src[yp*W+x] - 4 * src[ic];
        }
      }
    }

    return {
      id: "coacervate",
      label: "Coacervate · Cahn-Hilliard",
      formula: "∂φ/∂t = M ∇²( φ³ − φ − κ ∇²φ )   (Oparin 1924; Banani et al. 2017).",
      shortCaption: "STAGE 9 · COACERVATE",
      whatThisIs: "Membrane-less compartments as a building block. Concentrated chemistry separates " +
                  "from a dilute background into droplets — no lipid membrane required. " +
                  "Modern cells still use this exact mechanism for organelles. Plausibly the first " +
                  "compartment in the origin-of-life arc.",
      paletteBg: [10, 14, 22],
      paletteFg: [230, 224, 208],
      width: W,
      height: H,

      params: {
        mobility:  { label: "M — mobility",            min: 0.05, max: 0.6,  step: 0.01, value: 0.30 },
        kappa:     { label: "κ — interface stiffness", min: 0.1,  max: 2.0,  step: 0.05, value: 1.00 },
        substeps:  { label: "PDE iterations / frame",  min: 1,    max: 8,    step: 1,    value: 3    },
      },

      controlConsequence: {
        mobility:  "How fast the field relaxes toward equilibrium. Time-scaling only — the final droplet pattern is unchanged.",
        kappa:     "Interface stiffness — how much the field 'dislikes' sharp boundaries. Raise it: fewer, larger, smoother droplets. Lower it: many small ragged ones.",
        substeps:  "How many PDE substeps per visible frame. Pure speed knob — coarser steps simulate faster but with less smooth dynamics.",
      },

      randomize() { seed(); },
      clear()    { phi.fill(0); generation = 0; },
      reset()    { seed(); },

      step() {
        const M = this.params.mobility.value;
        const kappa = this.params.kappa.value;
        const subs = this.params.substeps.value | 0;
        const dt = 0.4;
        for (let s = 0; s < subs; s++) {
          // μ = φ³ − φ − κ ∇²φ
          laplacian(phi, lapPhi);
          for (let i = 0; i < phi.length; i++) {
            const p = phi[i];
            mu[i] = p * p * p - p - kappa * lapPhi[i];
          }
          // ∂φ/∂t = M ∇²μ
          laplacian(mu, lapPhi);   // reuse lapPhi as scratch
          for (let i = 0; i < phi.length; i++) {
            let v = phi[i] + dt * M * lapPhi[i];
            if (v < -1) v = -1; else if (v > 1) v = 1;
            phiN[i] = v;
          }
          const t = phi; phi = phiN; phiN = t;
        }
        generation += subs;
      },

      render(pixels) {
        // φ < 0 → obsidian (dilute); φ > 0 → bone-cream (droplet).
        for (let i = 0; i < phi.length; i++) {
          const t = (phi[i] + 1) * 0.5;   // 0..1
          const r = (10  + (230 - 10)  * t) | 0;
          const g = (14  + (224 - 14)  * t) | 0;
          const b = (22  + (208 - 22)  * t) | 0;
          const p = i * 4;
          pixels[p] = r; pixels[p+1] = g; pixels[p+2] = b; pixels[p+3] = 255;
        }
      },

      // SEM height = (φ + 1) / 2 — droplets rise above dilute substrate.
      renderHeight(out) {
        for (let i = 0; i < phi.length; i++) {
          out[i] = (phi[i] + 1) * 0.5;
        }
      },

      paint(gx, gy, radius, mode) {
        const target = mode === "erase" ? -1 : 1;
        for (let dy = -radius; dy <= radius; dy++) {
          for (let dx = -radius; dx <= radius; dx++) {
            if (dx*dx + dy*dy > radius*radius) continue;
            const x = ((gx + dx) % W + W) % W;
            const y = ((gy + dy) % H + H) % H;
            const i = y * W + x;
            phi[i] = target * 0.95;
          }
        }
      },

      population() {
        let pos = 0, neg = 0;
        for (let i = 0; i < phi.length; i++) {
          if (phi[i] > 0) pos++; else if (phi[i] < 0) neg++;
        }
        return `${pos} droplet · ${neg} solvent`;
      },

      generation() { return generation; },
    };
  }

  CA.RULES.coacervate = make;
})();
