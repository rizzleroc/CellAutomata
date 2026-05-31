// Vesicle — area-preserving, curvature-penalized phase-field membrane flow.
// A stable caricature of Helfrich (1973) lipid-bilayer bending dynamics:
// a true membrane compartment (a closed bilayer enclosing a lumen), as
// distinct from the membrane-less coacervate droplet.
//
// ∂φ/∂t = −M( W'(φ) − κ_b ∇²φ − ⟨·⟩ )
//
// φ ∈ [0, 1].  φ = 1 → vesicle lumen (inside); φ = 0 → exterior.  The
// membrane is the interface where φ ≈ 0.5.  W'(φ) = 2φ(1−φ)(1−2φ) is the
// double-well derivative (minima at 0 and 1); −κ_b ∇²φ is the bending /
// interface-width term; subtracting the field mean ⟨·⟩ is a Lagrange
// projection that conserves total lumen area so vesicles round up and
// coarsen instead of evaporating.
(function () {
  "use strict";
  window.CA = window.CA || { RULES: {} };

  const W = 160;
  const H = 160;

  function make() {
    let phi  = new Float32Array(W * H);
    let lap  = new Float32Array(W * H);
    let g    = new Float32Array(W * H);
    let phiN = new Float32Array(W * H);
    let generation = 0;

    function clamp01(v) { return v < 0 ? 0 : (v > 1 ? 1 : v); }

    function seed() {
      // Start from exterior (0) with several filled disks (vesicles).
      // Small ±0.02 noise everywhere keeps interfaces from being razor-flat.
      for (let i = 0; i < phi.length; i++) phi[i] = (Math.random() - 0.5) * 0.04;
      const disks = 6 + (Math.random() * 5 | 0);   // 6–10 vesicles
      for (let d = 0; d < disks; d++) {
        const cx = Math.random() * W | 0;
        const cy = Math.random() * H | 0;
        const r  = 8 + (Math.random() * 11 | 0);   // radius 8–18
        const r2 = r * r;
        for (let dy = -r; dy <= r; dy++) {
          for (let dx = -r; dx <= r; dx++) {
            if (dx*dx + dy*dy > r2) continue;
            const x = ((cx + dx) % W + W) % W;
            const y = ((cy + dy) % H + H) % H;
            phi[y * W + x] = 1;
          }
        }
      }
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
      id: "vesicles",
      label: "Vesicle · lipid membrane",
      formula: "∂φ/∂t = −M( W'(φ) − κ_b ∇²φ − ⟨·⟩ )  — area-preserving Helfrich-type membrane flow (Helfrich 1973).",
      shortCaption: "STAGE 11 · VESICLE",
      whatThisIs: "A lipid bilayer enclosing an interior — a true membrane compartment, " +
                  "unlike the membrane-less coacervate droplet. The closed membrane defines a " +
                  "persistent inside vs outside, the precursor to the protocell. Curvature-penalized " +
                  "area-preserving flow, a caricature of Helfrich (1973) bilayer bending energy.",
      paletteBg: [10, 14, 22],
      paletteFg: [230, 224, 208],
      width: W,
      height: H,

      params: {
        bending:  { label: "κ_b — membrane bending",  min: 0.5,  max: 6.0, step: 0.1,  value: 2.0  },
        mobility: { label: "M — relaxation rate",     min: 0.05, max: 0.6, step: 0.01, value: 0.25 },
        substeps: { label: "PDE iterations / frame",  min: 1,    max: 8,   step: 1,    value: 3    },
      },

      controlConsequence: {
        bending:  "Membrane bending modulus κ_b — raise it and the bilayer stiffens, giving fewer, bigger, rounder vesicles that resist tight curves; lower it for floppier, smaller, more numerous vesicles.",
        mobility: "How fast the membrane relaxes toward equilibrium. Time-scaling only — the final vesicle pattern is unchanged.",
        substeps: "How many PDE substeps per visible frame. Pure speed knob — coarser steps coarsen faster but with less smooth dynamics.",
      },

      // P1-D2: bending regimes that reseed so coarsening reads from scratch.
      presets: [
        { label: "many small vesicles", reseed: true,
          hint: "Floppy, low-bending bilayer — the field settles into many small vesicles.",
          values: { bending: 0.8, mobility: 0.25, substeps: 3 } },
        { label: "balanced", reseed: true,
          hint: "The default — a spread of vesicle sizes rounding up and slowly coarsening.",
          values: { bending: 2.0, mobility: 0.25, substeps: 3 } },
        { label: "few large vesicles", reseed: true,
          hint: "Stiff, high-bending bilayer — it resists tight curves, so a few big round vesicles dominate.",
          values: { bending: 5.0, mobility: 0.35, substeps: 4 } },
      ],

      randomize() { seed(); },
      clear()    { phi.fill(0); generation = 0; },
      reset()    { seed(); },

      step() {
        const M = this.params.mobility.value;
        const eps2 = this.params.bending.value;       // κ_b → interface width² / bending modulus
        const subs = this.params.substeps.value | 0;
        // The update's diffusion contribution is +dt·M·κ_b·∇²φ; explicit 2-D
        // diffusion needs dt·(M·κ_b) ≤ 0.25 or the field checkerboards.  Cap
        // dt adaptively so the whole bending/mobility range stays stable —
        // dt stays 0.20 in the common low-stiffness case and only shrinks
        // for stiff, fast membranes (high κ_b · M).
        const D = M * eps2;
        const dt = Math.min(0.20, 0.24 / Math.max(D, 1e-6));
        const N = phi.length;
        for (let s = 0; s < subs; s++) {
          // g = W'(φ) − κ_b ∇²φ, accumulating its mean for the Lagrange projection.
          laplacian(phi, lap);
          let gSum = 0;
          for (let i = 0; i < N; i++) {
            const p = phi[i];
            const Wp = 2 * p * (1 - p) * (1 - 2 * p);   // double-well derivative
            const gi = Wp - eps2 * lap[i];
            g[i] = gi;
            gSum += gi;
          }
          const gMean = gSum / N;                       // ⟨·⟩ — conserves lumen area
          for (let i = 0; i < N; i++) {
            phiN[i] = clamp01(phi[i] - dt * M * (g[i] - gMean));
          }
          const t = phi; phi = phiN; phiN = t;
        }
        generation += subs;
      },

      render(pixels) {
        // Bright bilayer ring keyed off the φ = 0.5 LEVEL SET, not the raw
        // gradient: 4φ(1−φ) peaks at φ = 0.5 and is bright at the interface
        // whatever its thickness, so the membrane stays visible across the
        // whole bending range (stiff membranes have thick, gentle interfaces
        // whose per-cell gradient would otherwise be too weak to light up).
        // exterior (φ→0) → dark bg; lumen interior (φ→1) → dim fill; membrane
        // (φ≈0.5) → bright bone-cream paletteFg.  Defining visual: rings.
        const bg = this.paletteBg, fg = this.paletteFg;
        for (let i = 0; i < phi.length; i++) {
          const p = phi[i];
          // Level-set ring: 1 at φ=0.5, 0 at φ=0/1; ^1.2 tightens it slightly.
          const ring = Math.pow(4 * p * (1 - p), 1.2);
          // Interior fill: dim lift above bg inside the lumen.
          const fill = p > 0.5 ? 0.15 : 0.0;
          // Compose: bg → fill toward fg, then the membrane ring on top.
          const t = fill + (1 - fill) * ring;          // 0..1, in [0,1]
          const r = (bg[0] + (fg[0] - bg[0]) * t) | 0;
          const gg = (bg[1] + (fg[1] - bg[1]) * t) | 0;
          const b = (bg[2] + (fg[2] - bg[2]) * t) | 0;
          const o = i * 4;
          pixels[o] = r; pixels[o+1] = gg; pixels[o+2] = b; pixels[o+3] = 255;
        }
      },

      // SEM height = φ — the lumen rises as rounded vesicle domes.
      renderHeight(out) {
        for (let i = 0; i < phi.length; i++) {
          out[i] = phi[i];
        }
      },

      paint(gx, gy, radius, mode) {
        const target = mode === "erase" ? 0 : 1;       // inject or remove a vesicle
        for (let dy = -radius; dy <= radius; dy++) {
          for (let dx = -radius; dx <= radius; dx++) {
            if (dx*dx + dy*dy > radius*radius) continue;
            const x = ((gx + dx) % W + W) % W;
            const y = ((gy + dy) % H + H) % H;
            phi[y * W + x] = target;
          }
        }
      },

      population() {
        // Level-set counts so the readout is stable across the bending range:
        // lumen = clearly-inside cells; membrane = the φ≈0.5 transition band.
        let inside = 0, membrane = 0;
        for (let i = 0; i < phi.length; i++) {
          const p = phi[i];
          if (p > 0.6) inside++;
          else if (p > 0.35) membrane++;   // 0.35 < φ ≤ 0.6 → interface band
        }
        return `${inside} lumen · ${membrane} membrane`;
      },

      generation() { return generation; },
    };
  }

  CA.RULES.vesicles = make;
})();
