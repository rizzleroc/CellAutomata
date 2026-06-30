// Mineral-surface catalysis — Stage 5. The first polymers form on clay, not in
// water. Faithful port of cellauto/rules/abiogenesis/stage_minerals.py
// (Ferris 1996; Cairns-Smith 1982). Two coupled fields over a static
// montmorillonite clay mask: free activated monomer M (ImpA) and accumulated
// RNA polymer P.
//
//   ∂M/∂t = D_M ∇²M + feed·(1−M) − k(x)·M        k(x) = k_clay on clay, k_bulk off
//   ∂P/∂t = D_P ∇²P + k(x)·M     − hydro·P
//
// Condensation polymerisation is thermodynamically uphill in open water, so
// dilute monomers don't spontaneously become long chains. A mineral surface
// concentrates monomers and templates the bond, so long polymer accumulates ON
// the clay while the bulk stays monomeric. Set k_bulk = k_clay (no catalysis)
// and the localisation vanishes — the whole point of the stage.
//
// Replaces the previous Gray-Scott stand-in (ROADMAP REV-18).
(function () {
  "use strict";
  window.CA = window.CA || { RULES: {} };

  const W = 160;
  const H = 160;
  const DT = 0.5;
  const DM = 0.18;   // monomer diffusion
  const DP = 0.04;   // polymer diffuses slowly (large, surface-bound)

  function make() {
    let M  = new Float32Array(W * H);   // free activated monomer (ImpA)
    let P  = new Float32Array(W * H);   // accumulated RNA oligomer
    let Mn = new Float32Array(W * H);
    let Pn = new Float32Array(W * H);
    const clay = new Float32Array(W * H);   // static catalytic-surface mask (0 or 1)
    let generation = 0;

    // Scatter N round montmorillonite patches across the grid.
    function seedClay(patches) {
      clay.fill(0);
      const radius = Math.max(2, (Math.min(W, H) / 9) | 0);
      const n = Math.max(1, patches | 0);
      for (let kp = 0; kp < n; kp++) {
        const cx = (Math.random() * W) | 0;
        const cy = (Math.random() * H) | 0;
        const r = radius + ((Math.random() * 3) | 0) - 1;
        const r2 = r * r;
        for (let y = cy - r; y <= cy + r; y++) {
          if (y < 0 || y >= H) continue;
          for (let x = cx - r; x <= cx + r; x++) {
            if (x < 0 || x >= W) continue;
            const dx = x - cx, dy = y - cy;
            if (dx * dx + dy * dy <= r2) clay[y * W + x] = 1;
          }
        }
      }
    }

    return {
      id: "minerals",
      label: "Mineral catalysis · clay-surface polymerisation",
      formula: "∂M/∂t = D_M∇²M + feed(1−M) − k(x)M;   ∂P/∂t = D_P∇²P + k(x)M − hydro·P   (k = k_clay on clay)",
      shortCaption: "STAGE 5 · MINERAL CATALYSIS",
      whatThisIs: "The first polymers form on clay, not in water. Joining monomers into chains is " +
                  "thermodynamically uphill in open water, so dilute monomers don't spontaneously make " +
                  "long polymers. Montmorillonite clay solves this — it concentrates activated monomers " +
                  "on its charged surface and templates bond formation (Ferris 1996). Watch long RNA " +
                  "oligomers accumulate ON the clay patches while the bulk water stays monomeric.",
      aboutStage: "The building block here is a surface. Bulk condensation is unfavourable, but a mineral " +
                  "surface concentrates and templates monomers so chains grow where water alone cannot " +
                  "(Ferris 1996; Cairns-Smith 1982). Free monomer M is fed and diffuses; on the clay mask " +
                  "it condenses into polymer P at rate k_clay, off it at near-zero k_bulk; polymer slowly " +
                  "hydrolyses everywhere. Set k_bulk = k_clay (the 'no catalysis' regime) and the " +
                  "localisation disappears — proof that the surface, not the soup, makes the polymers.",
      paletteBg: [10, 14, 22],
      paletteFg: [230, 224, 208],
      width: W,
      height: H,

      params: {
        kClay:       { label: "clay catalysis k_clay",  min: 0.00, max: 0.60, step: 0.01,  value: 0.25 },
        kBulk:       { label: "bulk condensation k_bulk", min: 0.00, max: 0.30, step: 0.002, value: 0.002 },
        feed:        { label: "monomer feed",           min: 0.00, max: 0.30, step: 0.005, value: 0.08 },
        hydrolysis:  { label: "polymer hydrolysis",     min: 0.00, max: 0.05, step: 0.001, value: 0.01 },
        clayPatches: { label: "clay patches",           min: 1,    max: 24,   step: 1,     value: 9 },
        substeps:    { label: "steps / frame",          min: 1,    max: 6,    step: 1,     value: 2 },
      },

      controlConsequence: {
        kClay: "How fast monomers condense into polymer ON the clay surface — this is the catalysis. Raise it: long RNA oligomers pile up on the clay patches.",
        kBulk: "Condensation rate in open water, off the clay — near zero in reality (bulk polymerisation is uphill). Raise it toward k_clay and the clay's advantage disappears: polymer forms everywhere and the localisation is lost.",
        feed:  "How fast fresh activated monomer (ImpA) is replenished. Raise it: more raw material, faster polymer growth.",
        hydrolysis: "How fast polymer breaks back down everywhere. Raise it: only the fastest-growing clay sites outrun decay; bulk polymer never survives.",
        clayPatches: "How many montmorillonite patches seed the surface (re-seeds the field). More patches: more catalytic real estate.",
        substeps: "Reaction-diffusion iterations per frame — a speed knob, not a chemical parameter.",
      },

      // Named regimes — the canonical surface-catalysis demo and its control.
      presets: [
        { label: "surface catalysis", reseed: true,
          hint: "Strong clay catalysis with near-zero bulk condensation — long RNA oligomers accumulate ON the clay while the open water stays monomeric. Ferris (1996).",
          values: { kClay: 0.25, kBulk: 0.002, feed: 0.08, hydrolysis: 0.01, clayPatches: 9 } },
        { label: "no catalysis (control)", reseed: true,
          hint: "Set k_bulk = k_clay: the clay has no advantage, so polymer forms everywhere at the same low rate and the localisation vanishes — the negative control that proves the surface matters.",
          values: { kClay: 0.05, kBulk: 0.05, feed: 0.08, hydrolysis: 0.01, clayPatches: 9 } },
        { label: "washed out", reseed: true,
          hint: "High hydrolysis on a thin feed — polymer breaks down faster than even the clay can build it, and nothing lasting accumulates. A barren surface.",
          values: { kClay: 0.25, kBulk: 0.002, feed: 0.03, hydrolysis: 0.04, clayPatches: 9 } },
      ],

      randomize() { this.reset(); },
      clear() { M.fill(1.0); P.fill(0.0); generation = 0; },   // empties the chemistry, keeps the clay
      reset() {
        seedClay(this.params.clayPatches.value | 0);
        M.fill(1.0); P.fill(0.0); generation = 0;
      },
      onParamChange(name) {
        if (name === "clayPatches") seedClay(this.params.clayPatches.value | 0);
      },

      step() {
        const kc = this.params.kClay.value;
        const kb = this.params.kBulk.value;
        const feed = this.params.feed.value;
        const hyd = this.params.hydrolysis.value;
        const sub = this.params.substeps.value | 0;
        for (let s = 0; s < sub; s++) {
          for (let y = 0; y < H; y++) {
            const ym = (y - 1 + H) % H, yp = (y + 1) % H;
            for (let x = 0; x < W; x++) {
              const xm = (x - 1 + W) % W, xp = (x + 1) % W;
              const ic = y * W + x;
              const lapM = M[y*W+xm] + M[y*W+xp] + M[ym*W+x] + M[yp*W+x] - 4 * M[ic];
              const lapP = P[y*W+xm] + P[y*W+xp] + P[ym*W+x] + P[yp*W+x] - 4 * P[ic];
              const k = clay[ic] ? kc : kb;
              const poly = k * M[ic];                       // monomer condenses at the local rate
              let m = M[ic] + DT * (DM * lapM + feed * (1.0 - M[ic]) - poly);
              let p = P[ic] + DT * (DP * lapP + poly - hyd * P[ic]);
              if (m < 0) m = 0; else if (m > 1) m = 1;
              if (p < 0) p = 0;                             // P accumulates; may exceed 1 (clamped at render)
              Mn[ic] = m; Pn[ic] = p;
            }
          }
          const tm = M; M = Mn; Mn = tm;
          const tp = P; P = Pn; Pn = tp;
        }
        generation += sub;
      },

      // SEM height: clay is a low ridge; accumulated polymer raises bone-coloured
      // domes on top of the patches.
      renderHeight(out) {
        for (let i = 0; i < W * H; i++) {
          let p = P[i]; if (p > 1) p = 1;
          out[i] = Math.min(1, clay[i] * 0.30 + p * 0.90);
        }
      },

      // Direct RGBA (viridis-free): clay tan over near-black water, polymer glows
      // teal-green where it accumulates — matching the Python render_rgb.
      render(pixels) {
        for (let i = 0; i < W * H; i++) {
          const c = clay[i];
          let p = P[i]; if (p > 1) p = 1;
          const px = i * 4;
          let r = c ? 50 : 8, g = c ? 40 : 10, b = c ? 25 : 16;
          r = (r * (1 - p) + 0   * p) | 0;
          g = (g * (1 - p) + 235 * p) | 0;
          b = (b * (1 - p) + 150 * p) | 0;
          pixels[px] = r; pixels[px+1] = g; pixels[px+2] = b; pixels[px+3] = 255;
        }
      },

      paint(gx, gy, radius, mode) {
        for (let dy = -radius; dy <= radius; dy++) {
          for (let dx = -radius; dx <= radius; dx++) {
            if (dx*dx + dy*dy > radius*radius) continue;
            const x = gx + dx, y = gy + dy;
            if (x < 0 || x >= W || y < 0 || y >= H) continue;
            const i = y * W + x;
            if (mode === "erase") { P[i] = 0; M[i] = 1; }
            else                    P[i] = Math.min(1.5, P[i] + 0.4);
          }
        }
      },

      population() {
        let on = 0, onN = 0, off = 0, offN = 0, cells = 0;
        for (let i = 0; i < W * H; i++) {
          const p = P[i];
          if (p > 0.15) cells++;
          if (clay[i]) { on += p; onN++; } else { off += p; offN++; }
        }
        const onMean = onN ? on / onN : 0, offMean = offN ? off / offN : 0;
        return `${cells} oligomer cells · on-clay ${(onMean * 100) | 0} / bulk ${(offMean * 100) | 0}`;
      },

      generation() { return generation; },
    };
  }

  CA.RULES.minerals = make;
})();
