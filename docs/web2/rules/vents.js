// Alkaline hydrothermal vents — Stage 2 of the abiogenesis pipeline.
// Simplified port of cellauto/rules/abiogenesis/stage_vents.py (Russell,
// Martin, Lane).  A vertical mineral-honeycomb chimney slice carries an
// acetate plume upward by diffusion + drift, with a porous mineral mask
// modulating where the acetate can settle.
//
//   ∂A/∂t = D ∇²A + drift·∂A/∂y + S(mask) − decay·A
//
// The visualisation isn't a full Eigen-Schuster chimney — that lives in
// the Python build — but a faithful 2-D snapshot of the steady-state
// acetate gradient against the chimney wall.
(function () {
  "use strict";
  window.CA = window.CA || { RULES: {} };

  const W = 160;
  const H = 160;

  function make() {
    const mineral = new Float32Array(W * H);   // chimney wall mask (static once built)
    let A    = new Float32Array(W * H);
    let An   = new Float32Array(W * H);
    let generation = 0;

    function buildChimney() {
      mineral.fill(0);
      // Two vertical honeycomb walls flanking a central duct.
      const cx = W >> 1;
      for (let y = 0; y < H; y++) {
        const taper = 1 - (y / H) * 0.2;          // walls narrow upward
        const halfDuct = (8 * taper) | 0;
        const wallHi = halfDuct + 18;
        for (let x = 0; x < W; x++) {
          const dx = Math.abs(x - cx);
          if (dx >= halfDuct && dx <= wallHi) {
            // Honeycomb pores: stripe pattern.
            const cell = ((y + (x % 4 < 2 ? 0 : 3)) % 7);
            mineral[y * W + x] = cell < 5 ? 1 : 0.4;
          }
        }
      }
    }

    function seed() {
      buildChimney();
      A.fill(0);
      // Source: acetate enters at the bottom of the duct.
      const cx = W >> 1;
      for (let y = H - 8; y < H; y++) {
        for (let x = cx - 4; x < cx + 4; x++) {
          A[y * W + x] = 1.0;
        }
      }
      generation = 0;
    }

    return {
      id: "vents",
      label: "Alkaline vents · acetate plume",
      formula: "∂A/∂t = D ∇²A + drift·∂A/∂y + S(mask) − decay·A",
      shortCaption: "STAGE 2 · ALKALINE VENTS",
      paletteBg: [10, 14, 22],
      paletteFg: [230, 224, 208],
      width: W,
      height: H,

      params: {
        diffusion: { label: "diff D",   min: 0.05, max: 0.40, step: 0.01,  value: 0.20 },
        drift:     { label: "updraft",  min: 0.00, max: 0.50, step: 0.01,  value: 0.18 },
        decay:     { label: "decay",    min: 0.000, max: 0.020, step: 0.001, value: 0.004 },
        source:    { label: "source",   min: 0.00, max: 0.20, step: 0.005, value: 0.05 },
      },

      randomize() { seed(); },
      clear()    { A.fill(0); generation = 0; },
      reset()    { seed(); },

      step() {
        const D = this.params.diffusion.value;
        const drift = this.params.drift.value;
        const decay = this.params.decay.value;
        const src = this.params.source.value;
        const cx = W >> 1;
        for (let y = 0; y < H; y++) {
          const ym = (y - 1 + H) % H, yp = (y + 1) % H;
          for (let x = 0; x < W; x++) {
            const xm = (x - 1 + W) % W, xp = (x + 1) % W;
            const ic = y * W + x;
            const lap = A[y*W+xm] + A[y*W+xp] + A[ym*W+x] + A[yp*W+x] - 4 * A[ic];
            const gradY = (A[yp*W+x] - A[ym*W+x]) * 0.5;
            // Drift is upward (negative y), so subtract drift * gradY.
            let v = A[ic] + D * lap - drift * gradY - decay * A[ic];
            // Source at the base of the duct.
            if (y > H - 12 && Math.abs(x - cx) < 5) v += src;
            // Mineral mask: porous walls leak some acetate; solid walls block.
            if (mineral[ic] >= 1) v *= 0.3;
            else if (mineral[ic] > 0) v *= 0.85;
            if (v < 0) v = 0; else if (v > 1) v = 1;
            An[ic] = v;
          }
        }
        const t = A; A = An; An = t;
        generation++;
      },

      render(pixels) {
        // Chimney walls in warm brown; acetate plume in viridis-ish teal.
        for (let i = 0; i < W * H; i++) {
          const m = mineral[i];
          const a = A[i];
          const p = i * 4;
          // Base substrate.
          let r = 10, g = 14, b = 22;
          if (m > 0) {
            r = (60 + 110 * m) | 0;
            g = (45 + 70 * m) | 0;
            b = (30 + 30 * m) | 0;
          }
          // Acetate cloud composited additively.
          r = Math.min(255, r + (a * 80) | 0);
          g = Math.min(255, g + (a * 220) | 0);
          b = Math.min(255, b + (a * 210) | 0);
          pixels[p] = r; pixels[p+1] = g; pixels[p+2] = b; pixels[p+3] = 255;
        }
      },

      // SEM height: mineral walls are tall ridges; acetate is a softer
      // raised plume on top.
      renderHeight(out) {
        for (let i = 0; i < W * H; i++) {
          out[i] = Math.min(1, mineral[i] * 0.55 + A[i] * 0.85);
        }
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
        return `ΣA ${acetate.toFixed(0)} · ${walls} wall cells`;
      },

      generation() { return generation; },
    };
  }

  CA.RULES.vents = make;
})();
