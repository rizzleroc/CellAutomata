// Alkaline hydrothermal vents — Stage 4 (pipeline "Stage 2"). Russell, Martin &
// Lane. A vertical mineral-honeycomb chimney slice separates ALKALINE vent fluid
// from the ACIDIC ocean; that natural pH difference is a proton-motive force
// (PMF) across the mineral membrane, and it is the free-energy source that drives
// carbon fixation. Acetate is synthesised AT the membrane in proportion to the
// local proton gradient, then rises (drift) and diffuses up the chimney.
//
//   ∂A/∂t = D ∇²A − drift·∂A/∂y + PMF·|∇pH|·feed·[membrane] − decay·A
//
// Set the PMF to zero (the "no gradient" regime) and synthesis stops — no
// gradient, no chemistry. This is a simplified 2-D coupling, not full
// Wood-Ljungdahl kinetics (those live in the Python build), but the
// chemiosmotic gradient→fixation link is now genuinely simulated and tunable,
// not the old advection-diffusion-plume stand-in.
(function () {
  "use strict";
  window.CA = window.CA || { RULES: {} };

  const W = 160;
  const H = 160;

  function make() {
    const mineral = new Float32Array(W * H);   // chimney wall mask (static once built)
    const Hp      = new Float32Array(W * H);   // proton field: 0 alkaline (vent) → 1 acidic (ocean)
    let A    = new Float32Array(W * H);         // acetate
    let An   = new Float32Array(W * H);
    let generation = 0;

    function buildChimney() {
      mineral.fill(0); Hp.fill(0);
      const cx = W >> 1;
      for (let y = 0; y < H; y++) {
        const taper = 1 - (y / H) * 0.2;          // walls narrow upward
        const halfDuct = (8 * taper) | 0;
        const wallHi = halfDuct + 18;
        for (let x = 0; x < W; x++) {
          const dx = Math.abs(x - cx);
          // Proton gradient: alkaline vent fluid in the duct, acidic ocean
          // outside, with a STEEP ramp across the mineral wall band (the membrane).
          let h;
          if (dx <= halfDuct) h = 0.05;                                   // vent fluid — alkaline
          else if (dx >= wallHi) h = 0.95;                                // ocean — acidic
          else h = 0.05 + 0.90 * (dx - halfDuct) / (wallHi - halfDuct);   // membrane ramp
          Hp[y * W + x] = h;
          if (dx >= halfDuct && dx <= wallHi) {
            const cell = ((y + (x % 4 < 2 ? 0 : 3)) % 7);                 // honeycomb pores
            mineral[y * W + x] = cell < 5 ? 1 : 0.4;
          }
        }
      }
    }

    function seed() {
      buildChimney();
      A.fill(0);            // acetate starts empty — it is SYNTHESISED at the membrane, not injected
      generation = 0;
    }

    return {
      id: "vents",
      label: "Alkaline vents · proton-gradient carbon fixation",
      formula: "∂A/∂t = D∇²A − drift·∂A/∂y + PMF·|∇pH|·feed·[membrane] − decay·A   (chemiosmotic synthesis)",
      shortCaption: "STAGE 2 · ALKALINE VENTS",
      whatThisIs: "An alkaline hydrothermal vent: a porous mineral chimney separating alkaline vent fluid " +
                  "from the acidic ocean. That natural pH difference is a proton-motive force — a free-energy " +
                  "source — and here it DRIVES the chemistry: acetate is fixed at the membrane in proportion " +
                  "to the local proton gradient (Russell, Martin & Lane), then rises up the chimney. Turn the " +
                  "PMF to zero and synthesis stops: no gradient, no chemistry.",
      aboutStage: "The building block is a place plus a power source — porous mineral honeycomb plus a natural " +
                  "proton gradient across it (alkaline vent vs acidic ocean). This model simulates that gradient " +
                  "as a field and couples it to synthesis: acetate is fixed at the membrane proportional to the " +
                  "proton-motive force (a toy of Wood-Ljungdahl carbon fixation), then drifts and diffuses up " +
                  "the chimney. The PMF slider IS the free-energy source — at zero there is no gradient, no " +
                  "fixation, and the plume dies. (A simplified 2-D coupling; the full kinetic chemiosmotic " +
                  "chemistry lives in the Python build.)",
      paletteBg: [10, 14, 22],
      paletteFg: [230, 224, 208],
      width: W,
      height: H,

      params: {
        diffusion: { label: "diffusion D",                min: 0.05,  max: 0.40,  step: 0.01,  value: 0.20 },
        drift:     { label: "updraft velocity",           min: 0.00,  max: 0.50,  step: 0.01,  value: 0.18 },
        decay:     { label: "acetate decay",              min: 0.000, max: 0.020, step: 0.001, value: 0.004 },
        pmf:       { label: "proton-motive force (ΔpH)",  min: 0.00,  max: 1.00,  step: 0.02,  value: 0.50 },
        feedstock: { label: "H₂/CO₂ feedstock",           min: 0.00,  max: 0.20,  step: 0.005, value: 0.06 },
      },

      controlConsequence: {
        diffusion: "How fast acetate spreads sideways from the membrane. Raise it: a broader, fuzzier plume. Lower it: a tight column on the wall.",
        drift:     "Buoyant updraft carrying the warm plume up the chimney. Raise it: acetate reaches higher before it decays.",
        decay:     "How fast acetate is consumed or lost per step. Raise it: a short plume; lower it: long-lived build-up.",
        pmf:       "The proton-motive force — the steepness of the natural pH gradient across the mineral membrane (alkaline vent vs acidic ocean). This is the FREE-ENERGY SOURCE that drives carbon fixation to acetate. Set it to 0 and synthesis stops: no gradient, no chemistry (Russell, Martin & Lane).",
        feedstock: "H₂/CO₂ supply feeding Wood-Ljungdahl carbon fixation at the membrane. Raise it: more acetate fixed per unit of proton drive.",
      },

      // Named regimes — note the "no gradient" negative control that proves the
      // PMF, not the geometry, drives the chemistry.
      presets: [
        { label: "living vent",
          hint: "A steep proton gradient with steady feedstock — the membrane fixes carbon into a rising acetate plume. The Lane–Martin chemiosmotic origin scenario.",
          values: { diffusion: 0.20, drift: 0.18, decay: 0.004, pmf: 0.60, feedstock: 0.08 } },
        { label: "no gradient (control)",
          hint: "Proton-motive force = 0: with no pH gradient there is no free-energy source, carbon fixation stops, and the plume fades. Proof that the gradient — not the chimney's shape — drives the chemistry.",
          values: { diffusion: 0.20, drift: 0.18, decay: 0.006, pmf: 0.00, feedstock: 0.08 } },
        { label: "vigorous chimney",
          hint: "A strong gradient, rich feedstock and buoyant updraft — fixed acetate floods the whole chimney.",
          values: { diffusion: 0.30, drift: 0.40, decay: 0.002, pmf: 1.00, feedstock: 0.15 } },
      ],

      randomize() { seed(); },
      clear()    { A.fill(0); generation = 0; },
      reset()    { seed(); },

      step() {
        const D = this.params.diffusion.value;
        const drift = this.params.drift.value;
        const decay = this.params.decay.value;
        const pmf = this.params.pmf.value;
        const feed = this.params.feedstock.value;
        for (let y = 0; y < H; y++) {
          const ym = (y - 1 + H) % H, yp = (y + 1) % H;
          for (let x = 0; x < W; x++) {
            const xm = (x - 1 + W) % W, xp = (x + 1) % W;
            const ic = y * W + x;
            const lap = A[y*W+xm] + A[y*W+xp] + A[ym*W+x] + A[yp*W+x] - 4 * A[ic];
            const gradY = (A[yp*W+x] - A[ym*W+x]) * 0.5;
            // Drift is upward (negative y), so subtract drift * gradY.
            let v = A[ic] + D * lap - drift * gradY - decay * A[ic];
            // Chemiosmotic carbon fixation: acetate is synthesised at the mineral
            // membrane in proportion to the local proton gradient × the PMF knob.
            if (mineral[ic] > 0) {
              const gx = Math.abs(Hp[y*W+xp] - Hp[y*W+xm]) * 0.5;   // local |∇pH| across the wall
              v += pmf * gx * feed * 20.0 * mineral[ic];            // fix carbon at the membrane
            }
            if (mineral[ic] >= 1) v *= 0.82;   // dense wall core is semi-permeable (lets the plume show)
            if (v < 0) v = 0; else if (v > 1) v = 1;
            An[ic] = v;
          }
        }
        const t = A; A = An; An = t;
        generation++;
      },

      render(pixels) {
        for (let i = 0; i < W * H; i++) {
          const m = mineral[i];
          const a = A[i];
          const h = Hp[i];
          const p = i * 4;
          // Base substrate with a faint pH backdrop: alkaline (low h) reads cool,
          // acidic (high h) a touch warmer — the gradient made just visible.
          let r = 10 + ((h * 16) | 0), g = 14, b = 22 + (((1 - h) * 12) | 0);
          if (m > 0) {
            r = (60 + 110 * m) | 0;
            g = (45 + 70 * m) | 0;
            b = (30 + 30 * m) | 0;
          }
          // Fixed acetate composited additively in teal-green.
          r = Math.min(255, r + (a * 70) | 0);
          g = Math.min(255, g + (a * 220) | 0);
          b = Math.min(255, b + (a * 205) | 0);
          pixels[p] = r; pixels[p+1] = g; pixels[p+2] = b; pixels[p+3] = 255;
        }
      },

      // SEM height: mineral walls are tall ridges; fixed acetate is a softer
      // raised plume on top.
      renderHeight(out) {
        for (let i = 0; i < W * H; i++) {
          out[i] = Math.min(1, mineral[i] * 0.35 + A[i] * 1.10);   // acetate reads ABOVE the walls so the PMF effect shows in SEM
        }
      },

      // Honeycomb mineral-cell sprite layer (the acetate plume is the SEM
      // substrate's job, not sprited).
      sprites() {
        const out = [];
        const cellR = 7;
        const xStep = cellR * Math.sqrt(3);
        const yStep = cellR * 1.5;
        for (let row = 0, y = cellR; y < H - cellR; row++, y += yStep) {
          const xOffset = (row & 1) ? xStep / 2 : 0;
          for (let x = cellR + xOffset; x < W - cellR; x += xStep) {
            const xi = x | 0, yi = y | 0;
            if (mineral[yi * W + xi] < 0.5) continue;      // only the wall cells
            out.push({ kind: "mineral-cell", x: x, y: y, scale: cellR });
          }
        }
        return out;
      },

      paint(gx, gy, radius, mode) {
        for (let dy = -radius; dy <= radius; dy++) {
          for (let dx = -radius; dx <= radius; dx++) {
            if (dx*dx + dy*dy > radius*radius) continue;
            const x = gx + dx, y = gy + dy;
            if (x < 0 || x >= W || y < 0 || y >= H) continue;
            const i = y * W + x;
            if (mode === "erase") A[i] = 0;
            else                   A[i] = Math.min(1, A[i] + 0.4);
          }
        }
      },

      population() {
        let acetate = 0, walls = 0;
        for (let i = 0; i < W * H; i++) {
          acetate += A[i];
          if (mineral[i] > 0) walls++;
        }
        return `ΣA ${acetate.toFixed(0)} · PMF-fixed · ${walls} membrane cells`;
      },

      generation() { return generation; },
    };
  }

  CA.RULES.vents = make;
})();
