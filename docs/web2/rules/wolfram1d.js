// Elementary 1D Wolfram automaton (rule 0–255), rendered as a scrolling
// 2D grid. Direct port of cellauto/rules/wolfram1d.py.
//
// The bottom row is the current generation; each step computes the new row
// and scrolls history upward.
(function () {
  "use strict";
  window.CA = window.CA || { RULES: {} };

  const W = 256;
  const H = 256;

  function make() {
    const cells = new Uint8Array(W * H);
    let generation = 0;

    return {
      id: "wolfram1d",
      label: "Wolfram · 1D elementary",
      formula: "next[x] = (rule >> (4·L + 2·C + R)) & 1   —   3-cell neighborhood.",
      shortCaption: "STAGE ∞ · WOLFRAM 1D",
      paletteBg: [245, 241, 230],
      paletteFg: [17, 17, 17],
      width: W,
      height: H,

      params: {
        ruleNumber: { label: "rule",  min: 0, max: 255, step: 1, value: 30 },
        seedRandom: { label: "seed?", type: "bool",            value: false },
      },

      _seed() {
        cells.fill(0);
        if (this.params.seedRandom.value) {
          const row = H - 1;
          for (let x = 0; x < W; x++) {
            if (Math.random() < 0.5) cells[row * W + x] = 1;
          }
        } else {
          cells[(H - 1) * W + (W >> 1)] = 1;
        }
        generation = 0;
      },

      randomize() {
        this.params.seedRandom.value = true;
        this._seed();
      },

      clear() {
        cells.fill(0);
        generation = 0;
      },

      reset() {
        this.params.seedRandom.value = false;
        this._seed();
      },

      step() {
        const r = this.params.ruleNumber.value | 0;
        // Read current bottom row.
        const cur = new Uint8Array(W);
        const baseRead = (H - 1) * W;
        for (let x = 0; x < W; x++) cur[x] = cells[baseRead + x];

        // Compute next row.
        const nxt = new Uint8Array(W);
        for (let x = 0; x < W; x++) {
          const L = cur[(x - 1 + W) % W];
          const C = cur[x];
          const R = cur[(x + 1) % W];
          const pat = (L << 2) | (C << 1) | R;
          nxt[x] = (r >> pat) & 1;
        }

        // Scroll up by one row: copy rows 1..H-1 into 0..H-2.
        cells.copyWithin(0, W, H * W);
        // Write new row at the bottom.
        const baseWrite = (H - 1) * W;
        for (let x = 0; x < W; x++) cells[baseWrite + x] = nxt[x];
        generation++;
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
        // Painting on Wolfram 1D writes to the current (bottom) row only —
        // history is read-only.
        const val = mode === "erase" ? 0 : 1;
        const y = H - 1;
        for (let dx = -radius; dx <= radius; dx++) {
          const x = ((gx + dx) % W + W) % W;
          cells[y * W + x] = val;
        }
      },

      population() {
        let liveNow = 0;
        const base = (H - 1) * W;
        for (let x = 0; x < W; x++) if (cells[base + x]) liveNow++;
        return `${liveNow} live · rule ${this.params.ruleNumber.value}`;
      },

      generation() { return generation; },
    };
  }

  CA.RULES.wolfram1d = make;
})();
