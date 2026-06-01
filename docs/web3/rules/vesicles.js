// Lipid vesicles — Stage 3 of the abiogenesis pipeline.
//
// NOT a line-for-line port of cellauto/rules/abiogenesis/stage3_vesicles.py.
// The Python stage drives a two-species Gray-Scott reaction-diffusion lipid
// field and adds a small Helfrich biharmonic SMOOTHING pass once per frame.
// This browser version instead runs a single-field Allen-Cahn phase model
// with an explicit Helfrich (∇²)² bending term — a *different* PDE that
// reaches the same qualitative endpoint (smooth closed bilayer loops that
// read as vesicle cross-sections). It is "inspired by", not "a port of",
// the Python stage; both share the Helfrich-curvature idea, not the equation.
//
// Physics (Allen-Cahn phase field + Helfrich bending):
//   φ = lipid concentration field, [0, 1].
//   ∂φ/∂t = D ∇²φ − γ φ (1 − φ)(½ − φ) − κ (∇²)²φ + noise
//
// The (φ)(1−φ)(½−φ) reaction term is a double-well that wants φ to land
// at either 0 (water) or 1 (lipid).  The κ biharmonic penalises sharp
// curvature — the Helfrich term — so the interface relaxes into smooth
// closed loops (which read as vesicle cross-sections in 2-D).
//
// Sprites: anywhere a local maximum of φ exceeds VESICLE_THRESHOLD we
// draw a bilayer ring centred on it.
(function () {
  "use strict";
  window.CA = window.CA || { RULES: {} };

  const W = 160;
  const H = 160;
  // v4.1.1: raised from 0.62 → 0.78 so only well-formed vesicles get
  // a sprite (the lower threshold produced spammy maxima from
  // half-collapsed bilayers, frame-to-frame churn).
  const VESICLE_THRESHOLD = 0.78;

  function make() {
    let phi   = new Float32Array(W * H);
    let phiN  = new Float32Array(W * H);
    const lap1 = new Float32Array(W * H);
    const lap2 = new Float32Array(W * H);
    let generation = 0;
    let lastSpriteScan = -1;
    let cachedSprites = [];

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

    function seed() {
      // Start as random near-zero — vesicles nucleate from fluctuations.
      for (let i = 0; i < phi.length; i++) phi[i] = 0.08 + (Math.random() - 0.5) * 0.06;
      // Plus a handful of lipid-rich seed patches.
      for (let n = 0; n < 6; n++) {
        const cx = (Math.random() * W) | 0;
        const cy = (Math.random() * H) | 0;
        const r = 6 + ((Math.random() * 5) | 0);
        for (let y = cy - r; y < cy + r; y++) {
          for (let x = cx - r; x < cx + r; x++) {
            const xi = ((x % W) + W) % W;
            const yi = ((y % H) + H) % H;
            const dx = x - cx, dy = y - cy;
            if (dx*dx + dy*dy <= r*r) phi[yi * W + xi] = 0.85;
          }
        }
      }
      generation = 0;
      lastSpriteScan = -1;
    }

    return {
      id: "vesicles",
      label: "Vesicles · Helfrich lipid bilayer",
      formula: "∂φ/∂t = D ∇²φ − γ φ(1−φ)(½−φ) − κ (∇²)²φ + noise   (Helfrich curvature).",
      shortCaption: "STAGE 3 · VESICLES",
      whatThisIs: "True membrane compartments. Lipid molecules spontaneously assemble into " +
                  "closed bilayer spheres — the kind of compartment modern cells have. " +
                  "Distinct from coacervate's liquid-liquid droplets: a vesicle has an actual " +
                  "membrane, and the membrane is selectively permeable.",
      aboutStage: "The building block here is the protocell boundary itself. Unlike the membrane-less " +
                  "coacervate, this is a real closed lipid bilayer enclosing a lumen — a persistent " +
                  "inside versus outside. It matters as the true compartment a cell needs to hold its " +
                  "chemistry together and meter what crosses. The flow follows Helfrich (1973) bending " +
                  "energy; raise the bending modulus κ_b for fewer, larger, rounder vesicles.",
      paletteBg: [10, 14, 22],
      paletteFg: [230, 224, 208],
      width: W,
      height: H,

      params: {
        diffusion: { label: "D — lipid diffusion",       min: 0.05, max: 0.5,  step: 0.01,  value: 0.18 },
        gamma:     { label: "γ — double-well strength",  min: 0.5,  max: 4.0,  step: 0.05,  value: 1.60 },
        kappa:     { label: "κ — bending rigidity",      min: 0.01, max: 0.30, step: 0.01,  value: 0.10 },
        noise:     { label: "thermal fluctuation",       min: 0.000, max: 0.020, step: 0.001, value: 0.004 },
      },

      controlConsequence: {
        diffusion: "How fast lipids spread through the aqueous phase. Raise it: vesicles dissolve back into the substrate. Lower it: lipid stays clumped and never forms membranes.",
        gamma:     "How strongly lipid prefers water-OR-lipid (the φ(1−φ)(½−φ) double-well). Raise it: sharper, more defined vesicle walls. Lower it: blurry partitioning.",
        kappa:     "Bending rigidity (Helfrich's κ). Raise it: vesicles relax into smooth round spheres. Lower it: jagged, deformed membranes.",
        noise:     "Thermal kicks. Without noise the system gets stuck in any random initial state. A real membrane fluctuates — without κ pulling it back, it would tear.",
      },

      // P1-D2: named regimes along the membrane-bending axis. κ is Helfrich's
      // bending rigidity — the knob that decides how round the vesicles get.
      presets: [
        { label: "floppy membranes", reseed: true,
          hint: "Low bending rigidity with a soft double-well — limp, jagged bilayers that deform into many small, irregular vesicles.",
          values: { diffusion: 0.18, gamma: 1.00, kappa: 0.03, noise: 0.004 } },
        { label: "balanced", reseed: true,
          hint: "The default — moderate stiffness and well depth give a spread of rounded vesicles that slowly relax and coarsen.",
          values: { diffusion: 0.18, gamma: 1.60, kappa: 0.10, noise: 0.004 } },
        { label: "stiff spheres", reseed: true,
          hint: "High bending rigidity and a sharp double-well — the membrane resists curvature, so a few smooth, round spheres dominate.",
          values: { diffusion: 0.18, gamma: 3.00, kappa: 0.26, noise: 0.004 } },
      ],

      randomize() { seed(); },
      clear()    { phi.fill(0); generation = 0; lastSpriteScan = -1; },
      reset()    { seed(); },

      step() {
        const D = this.params.diffusion.value;
        const g = this.params.gamma.value;
        const k = this.params.kappa.value;
        const sigma = this.params.noise.value;
        const dt = 0.45;
        // ∇²φ
        laplacian(phi, lap1);
        // ∇²(∇²φ) = biharmonic = (∇²)²
        laplacian(lap1, lap2);
        for (let i = 0; i < phi.length; i++) {
          const p = phi[i];
          // Double-well reaction term: roots at 0, 0.5, 1; stable at 0 and 1.
          const reaction = g * p * (1 - p) * (0.5 - p);
          const noise = sigma * (Math.random() - 0.5);
          let v = p + dt * (D * lap1[i] - reaction - k * lap2[i]) + noise;
          if (v < 0) v = 0; else if (v > 1) v = 1;
          phiN[i] = v;
        }
        const t = phi; phi = phiN; phiN = t;
        generation++;
      },

      render(pixels) {
        // φ → bone-cream when high (lipid), obsidian when low (water).
        for (let i = 0; i < phi.length; i++) {
          const t = phi[i];
          const r = (10  + (230 - 10)  * t) | 0;
          const g = (14  + (224 - 14)  * t) | 0;
          const b = (22  + (208 - 22)  * t) | 0;
          const p = i * 4;
          pixels[p] = r; pixels[p+1] = g; pixels[p+2] = b; pixels[p+3] = 255;
        }
      },

      renderHeight(out) {
        // φ itself is the height: lipid stands up, water lies flat.
        for (let i = 0; i < phi.length; i++) out[i] = phi[i];
      },

      // v4.1 sprite layer — find local maxima of φ above the vesicle
      // threshold and emit a bilayer-ring sprite at each.
      sprites() {
        if (generation === lastSpriteScan) return cachedSprites;
        lastSpriteScan = generation;
        const out = [];
        // Coarse local-maximum scan; stride widened in v4.1.1 from 4 → 8
        // so neighbouring near-degenerate maxima within the same vesicle
        // don't both qualify (was producing 600+ overlapping rings).
        const stride = 8;
        for (let y = stride; y < H - stride; y += stride) {
          for (let x = stride; x < W - stride; x += stride) {
            const ic = y * W + x;
            const me = phi[ic];
            if (me < VESICLE_THRESHOLD) continue;
            // Reject unless it's a maximum in its 3-window.
            let isMax = true;
            for (let dy = -stride; dy <= stride && isMax; dy += stride) {
              for (let dx = -stride; dx <= stride && isMax; dx += stride) {
                if (dx === 0 && dy === 0) continue;
                if (phi[(y + dy) * W + (x + dx)] > me) isMax = false;
              }
            }
            if (!isMax) continue;
            // Scale grows with how far above threshold we are.
            const lift = Math.min(1, (me - VESICLE_THRESHOLD) / (1 - VESICLE_THRESHOLD));
            const scale = 3 + lift * 4;
            out.push({ kind: "vesicle-bilayer", x: x + 0.5, y: y + 0.5, scale });
          }
        }
        cachedSprites = out;
        return out;
      },

      paint(gx, gy, radius, mode) {
        const target = mode === "erase" ? 0 : 0.9;
        for (let dy = -radius; dy <= radius; dy++) {
          for (let dx = -radius; dx <= radius; dx++) {
            if (dx*dx + dy*dy > radius*radius) continue;
            const x = ((gx + dx) % W + W) % W;
            const y = ((gy + dy) % H + H) % H;
            phi[y * W + x] = target;
          }
        }
        lastSpriteScan = -1;
      },

      population() {
        let lipidArea = 0;
        for (let i = 0; i < phi.length; i++) if (phi[i] > 0.5) lipidArea++;
        const vesicles = this.sprites().length;
        return `${vesicles} vesicle · ${lipidArea} lipid-cells`;
      },

      generation() { return generation; },
    };
  }

  CA.RULES.vesicles = make;
})();
