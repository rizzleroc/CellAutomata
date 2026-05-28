// Conway's Game of Life. B3/S23. Direct port of cellauto/rules/conway.py.
//
// Grid is a Uint8Array (0 or 1), W×H, toroidal. Renders 1:1 to ImageData.
(function () {
  "use strict";
  window.CA = window.CA || { RULES: {} };

  const W = 128;
  const H = 128;

  function make() {
    const cells = new Uint8Array(W * H);
    const next = new Uint8Array(W * H);
    let generation = 0;

    return {
      id: "conway",
      label: "Conway · Life (B3/S23)",
      formula: "B3/S23 — born on 3 live neighbors, survives on 2 or 3.",
      shortCaption: "STAGE ∞ · CONWAY'S LIFE",
      paletteBg: [10, 14, 22],
      paletteFg: [230, 224, 208],
      width: W,
      height: H,

      params: {
        density: { label: "density", min: 0.05, max: 0.6, step: 0.01, value: 0.30 },
        wrap:    { label: "wrap",    type: "bool",                value: true  },
      },

      randomize() {
        const d = this.params.density.value;
        for (let i = 0; i < cells.length; i++) cells[i] = Math.random() < d ? 1 : 0;
        generation = 0;
      },

      clear() {
        cells.fill(0);
        generation = 0;
      },

      reset() { this.randomize(); },

      step() {
        const wrap = this.params.wrap.value;
        for (let y = 0; y < H; y++) {
          const ym = wrap ? (y - 1 + H) % H : (y - 1);
          const yp = wrap ? (y + 1) % H     : (y + 1);
          for (let x = 0; x < W; x++) {
            const xm = wrap ? (x - 1 + W) % W : (x - 1);
            const xp = wrap ? (x + 1) % W     : (x + 1);
            let live = 0;
            if (ym >= 0) {
              if (xm >= 0) live += cells[ym * W + xm];
              live += cells[ym * W + x];
              if (xp < W)  live += cells[ym * W + xp];
            }
            if (xm >= 0) live += cells[y * W + xm];
            if (xp < W)  live += cells[y * W + xp];
            if (yp < H) {
              if (xm >= 0) live += cells[yp * W + xm];
              live += cells[yp * W + x];
              if (xp < W)  live += cells[yp * W + xp];
            }
            const me = cells[y * W + x];
            next[y * W + x] = me ? (live === 2 || live === 3 ? 1 : 0)
                                  : (live === 3 ? 1 : 0);
          }
        }
        cells.set(next);
        generation++;
      },

      // SEM mode: write the cell grid as a scalar height field (0 dead,
      // 1 alive).  The renderer's Gaussian blur turns hard binary cells
      // into smooth shadeable mounds.
      renderHeight(out) {
        for (let i = 0; i < cells.length; i++) out[i] = cells[i];
      },

      render(pixels) {
        const [br, bg, bb] = this.paletteBg;
        const [fr, fg, fb] = this.paletteFg;
        for (let i = 0; i < cells.length; i++) {
          const p = i * 4;
          if (cells[i]) {
            pixels[p] = fr; pixels[p+1] = fg; pixels[p+2] = fb;
          } else {
            pixels[p] = br; pixels[p+1] = bg; pixels[p+2] = bb;
          }
          pixels[p+3] = 255;
        }
      },

      paint(gx, gy, radius, mode) {
        const val = mode === "erase" ? 0 : 1;
        for (let dy = -radius; dy <= radius; dy++) {
          for (let dx = -radius; dx <= radius; dx++) {
            if (dx*dx + dy*dy > radius*radius) continue;
            const x = ((gx + dx) % W + W) % W;
            const y = ((gy + dy) % H + H) % H;
            cells[y * W + x] = val;
          }
        }
      },

      population() {
        let alive = 0;
        for (let i = 0; i < cells.length; i++) if (cells[i]) alive++;
        return `${alive} / ${cells.length}`;
      },

      generation() { return generation; },
    };
  }

  CA.RULES.conway = make;
})();
