// Gray-Scott reaction-diffusion. Direct port from docs/web/sim.js (v1)
// with the Pearson preset library exposed as a per-rule control.
//
// PDE:
//   ∂u/∂t = Du ∇²u  -  u v²  +  F (1 - u)
//   ∂v/∂t = Dv ∇²v  +  u v²  -  (F + k) v
//
// Toroidal 5-point Laplacian. Ping-pong Float32 buffers. No allocations
// in the hot loop.
(function () {
  "use strict";
  window.CA = window.CA || { RULES: {} };

  const W = 220;
  const H = 220;
  const Du = 0.16;
  const Dv = 0.08;
  const DT = 1.0;
  // PDE substeps per render frame: GS needs many small Euler steps per
  // visible update or the pattern dynamics look glacial.
  const SUBSTEPS = 10;

  // Pearson (1993) presets — same numbers as the v1 demo and the Python
  // build's GRAY_SCOTT_PRESETS table.
  const PRESETS = {
    spots:     { F: 0.035,  k: 0.065  },
    stripes:   { F: 0.040,  k: 0.060  },
    mitosis:   { F: 0.0367, k: 0.0649 },
    waves:     { F: 0.014,  k: 0.045  },
    labyrinth: { F: 0.039,  k: 0.058  },
  };

  function make() {
    let u  = new Float32Array(W * H);
    let v  = new Float32Array(W * H);
    let un = new Float32Array(W * H);
    let vn = new Float32Array(W * H);
    let generation = 0;

    function seed() {
      u.fill(1.0);
      v.fill(0.0);
      const r = 7;
      const cx = (W / 2) | 0;
      const cy = (H / 2) | 0;
      for (let y = cy - r; y < cy + r; y++) {
        for (let x = cx - r; x < cx + r; x++) {
          const i = y * W + x;
          u[i] = 0.5;
          v[i] = 0.25;
        }
      }
      for (let i = 0; i < v.length; i++) {
        v[i] += (Math.random() - 0.5) * 0.02;
        if (v[i] < 0) v[i] = 0;
        if (v[i] > 1) v[i] = 1;
      }
      generation = 0;
    }

    function substep(F, k) {
      for (let y = 0; y < H; y++) {
        const ym = (y - 1 + H) % H;
        const yp = (y + 1) % H;
        for (let x = 0; x < W; x++) {
          const xm = (x - 1 + W) % W;
          const xp = (x + 1) % W;
          const ic = y * W + x;
          const il = y * W + xm;
          const ir = y * W + xp;
          const iuu = ym * W + x;
          const id = yp * W + x;
          const lapU = u[il] + u[ir] + u[iuu] + u[id] - 4 * u[ic];
          const lapV = v[il] + v[ir] + v[iuu] + v[id] - 4 * v[ic];
          const uc = u[ic];
          const vc = v[ic];
          const uvv = uc * vc * vc;
          let uNew = uc + DT * (Du * lapU - uvv + F * (1.0 - uc));
          let vNew = vc + DT * (Dv * lapV + uvv - (F + k) * vc);
          if (uNew < 0) uNew = 0; else if (uNew > 1) uNew = 1;
          if (vNew < 0) vNew = 0; else if (vNew > 1) vNew = 1;
          un[ic] = uNew;
          vn[ic] = vNew;
        }
      }
      const tu = u; u = un; un = tu;
      const tv = v; v = vn; vn = tv;
    }

    return {
      id: "grayscott",
      label: "Gray–Scott · reaction–diffusion",
      formula: "∂u/∂t = Du ∇²u − uv² + F(1−u);   ∂v/∂t = Dv ∇²v + uv² − (F+k)v",
      shortCaption: "STAGE 1 · REACTION–DIFFUSION",
      paletteBg: [10, 14, 22],
      paletteFg: [230, 224, 208],
      width: W,
      height: H,

      params: {
        preset: { label: "preset", type: "enum", options: Object.keys(PRESETS), value: "spots" },
        F:      { label: "feed F", min: 0.000, max: 0.090, step: 0.001, value: 0.035 },
        k:      { label: "kill k", min: 0.030, max: 0.075, step: 0.001, value: 0.065 },
      },

      onParamChange(name) {
        if (name === "preset") {
          const p = PRESETS[this.params.preset.value];
          if (p) {
            this.params.F.value = p.F;
            this.params.k.value = p.k;
          }
        } else if (name === "F" || name === "k") {
          // Manual edit → drop out of named preset.
          this.params.preset.value = "";
        }
      },

      randomize() {
        u.fill(1.0);
        v.fill(0.0);
        // Sprinkle 8 random patches.
        for (let n = 0; n < 8; n++) {
          const cx = (Math.random() * W) | 0;
          const cy = (Math.random() * H) | 0;
          const r = 4 + ((Math.random() * 8) | 0);
          for (let y = cy - r; y < cy + r; y++) {
            for (let x = cx - r; x < cx + r; x++) {
              const xi = ((x % W) + W) % W;
              const yi = ((y % H) + H) % H;
              const i = yi * W + xi;
              u[i] = 0.5;
              v[i] = 0.25 + (Math.random() - 0.5) * 0.05;
              if (v[i] < 0) v[i] = 0;
              if (v[i] > 1) v[i] = 1;
            }
          }
        }
        generation = 0;
      },

      clear() {
        u.fill(1.0);
        v.fill(0.0);
        generation = 0;
      },

      reset() { seed(); },

      step() {
        const F = this.params.F.value;
        const k = this.params.k.value;
        for (let s = 0; s < SUBSTEPS; s++) substep(F, k);
        generation += SUBSTEPS;
      },

      render(pixels) {
        const lutLen = (typeof VIRIDIS_LUT !== "undefined") ? (VIRIDIS_LUT.length / 3) : 0;
        if (lutLen > 0) {
          for (let i = 0; i < W * H; i++) {
            let t = v[i];
            if (t < 0) t = 0; else if (t > 1) t = 1;
            const idx = Math.min(lutLen - 1, (t * lutLen) | 0) * 3;
            const p = i * 4;
            pixels[p]   = VIRIDIS_LUT[idx];
            pixels[p+1] = VIRIDIS_LUT[idx+1];
            pixels[p+2] = VIRIDIS_LUT[idx+2];
            pixels[p+3] = 255;
          }
        } else {
          // Grayscale fallback.
          for (let i = 0; i < W * H; i++) {
            const t = Math.max(0, Math.min(1, v[i])) * 255 | 0;
            const p = i * 4;
            pixels[p] = pixels[p+1] = pixels[p+2] = t;
            pixels[p+3] = 255;
          }
        }
      },

      paint(gx, gy, radius, mode) {
        // Painting drops a v-perturbation patch (matter into the
        // substrate) or, with shift/erase, restores the u substrate.
        for (let dy = -radius; dy <= radius; dy++) {
          for (let dx = -radius; dx <= radius; dx++) {
            if (dx*dx + dy*dy > radius*radius) continue;
            const x = ((gx + dx) % W + W) % W;
            const y = ((gy + dy) % H + H) % H;
            const i = y * W + x;
            if (mode === "erase") {
              u[i] = 1.0;
              v[i] = 0.0;
            } else {
              u[i] = 0.5;
              v[i] = 0.25;
            }
          }
        }
      },

      population() {
        let total = 0;
        for (let i = 0; i < v.length; i++) total += v[i];
        return `Σv ${total.toFixed(0)}`;
      },

      generation() { return generation; },
    };
  }

  CA.RULES.grayscott = make;
})();
