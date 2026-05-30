// Natural-selection rule — 16-species soup with amoeba formation.
// Direct port of cellauto/rules/natural_selection.py (also re-exported as
// AbiogenesisStage0Soup in the Python build).
//
// Phase 1: each cell adopts a random Moore-neighbour's species; if its
//          colour genuinely shifts, isNew = true. Amoebas age + die.
// Phase 2: same-species adjacent "new" pairs combine into an amoeba
//          (distinct palette colour, isNew = false, isAmeba = true).
(function () {
  "use strict";
  window.CA = window.CA || { RULES: {} };

  const W = 80;
  const H = 80;
  const N = W * H;
  const N_SPECIES = 16;
  const AMOEBA_LIFESPAN = 60;

  // 16-colour palette (matches PALETTE in natural_selection.py).
  const PALETTE = [
    [230, 25, 75],  [60, 180, 75],  [255, 225, 25], [67, 99, 216],
    [245, 130, 49], [145, 30, 180], [70, 240, 240], [240, 50, 230],
    [188, 246, 12], [250, 190, 190],[0, 128, 128],  [230, 190, 255],
    [154, 99, 36], [255, 250, 200], [128, 0, 0],    [170, 255, 195],
  ];

  function make() {
    // Three parallel Uint arrays keep the per-cell tuple light.
    const color  = new Uint8Array(N);   // species index 0..15
    const flags  = new Uint8Array(N);   // bit 0: isNew, bit 1: isAmeba
    const age    = new Uint16Array(N);
    let generation = 0;

    function seed() {
      for (let i = 0; i < N; i++) {
        color[i] = (Math.random() * N_SPECIES) | 0;
        flags[i] = 0;
        age[i]   = 0;
      }
      generation = 0;
    }

    return {
      id: "natural-selection",
      label: "Natural selection · 16-species soup",
      formula: "16-species lattice + neighbour mixing → same-species pairs become amoebas.",
      shortCaption: "STAGE 0 · NATURAL SELECTION",
      whatThisIs: "The first hint of compartmentalisation. In a soup of 16 chemical species, " +
                  "same-species pairs combine into longer-lived 'amoebas' — local pockets of identity. " +
                  "It matters because compartments are the precondition for everything else: " +
                  "without a boundary, there's no individual to be selected.",
      paletteBg: [10, 14, 22],
      paletteFg: [230, 224, 208],
      width: W,
      height: H,

      params: {
        amoebaLifespan: { label: "amoeba lifespan", min: 10, max: 200, step: 5, value: AMOEBA_LIFESPAN },
      },

      controlConsequence: {
        amoebaLifespan: "How many steps an amoeba survives before dying. Shorter: fast turnover, sparse population. Longer: amoebas accumulate into dense 'cities' that crowd out the unbound soup.",
      },

      randomize() { seed(); },
      clear()     { color.fill(0); flags.fill(0); age.fill(0); generation = 0; },
      reset()     { seed(); },

      step() {
        const lifespan = this.params.amoebaLifespan.value | 0;
        // Snapshot colours so neighbour reads don't see in-step writes.
        const old = new Uint8Array(color);

        // Phase 1: neighbour mixing + amoeba lifecycle.
        for (let y = 0; y < H; y++) {
          for (let x = 0; x < W; x++) {
            const i = y * W + x;
            // Reset isNew every step (bit 0 → 0, preserve bit 1).
            flags[i] = flags[i] & 0b10;

            if (flags[i] & 0b10) {
              // Amoeba ages, dies at lifespan.
              age[i]++;
              if (age[i] >= lifespan) {
                color[i] = (Math.random() * N_SPECIES) | 0;
                flags[i] = 0b01;   // new cell from amoeba death
                age[i]   = 0;
              }
              continue;
            }

            // Pick random Moore neighbour (8 options).
            let pick;
            do {
              const dx = ((Math.random() * 3) | 0) - 1;
              const dy = ((Math.random() * 3) | 0) - 1;
              if (dx === 0 && dy === 0) continue;
              const nx = x + dx, ny = y + dy;
              if (nx < 0 || nx >= W || ny < 0 || ny >= H) continue;
              pick = old[ny * W + nx];
              break;
            } while (true);
            if (pick !== undefined && pick !== color[i]) {
              color[i] = pick;
              flags[i] |= 0b01;
            }
          }
        }

        // Phase 2: combine same-species new pairs.
        for (let y = 0; y < H; y++) {
          for (let x = 0; x < W; x++) {
            const i = y * W + x;
            if (flags[i] !== 0b01) continue;  // not new, or already amoeba
            const myColor = color[i];
            const neighbours = [[1, 0], [0, 1], [1, 1], [-1, 1]];
            for (const [dx, dy] of neighbours) {
              const nx = x + dx, ny = y + dy;
              if (nx < 0 || nx >= W || ny < 0 || ny >= H) continue;
              const j = ny * W + nx;
              if (flags[j] !== 0b01) continue;
              if (color[j] !== myColor) continue;
              // Combine: both cells become amoebas with a new distinct colour.
              let newC;
              do { newC = (Math.random() * N_SPECIES) | 0; } while (newC === myColor);
              color[i] = color[j] = newC;
              flags[i] = flags[j] = 0b10;
              age[i] = age[j] = 0;
              break;
            }
          }
        }
        generation++;
      },

      render(pixels) {
        for (let i = 0; i < N; i++) {
          const [r, g, b] = PALETTE[color[i]];
          const p = i * 4;
          pixels[p] = r; pixels[p+1] = g; pixels[p+2] = b; pixels[p+3] = 255;
          // Amoebas get a brighter ring; rough but reads as "raised".
          if (flags[i] & 0b10) {
            pixels[p]   = Math.min(255, r + 60);
            pixels[p+1] = Math.min(255, g + 60);
            pixels[p+2] = Math.min(255, b + 60);
          }
        }
      },

      // SEM height: amoebas pop as raised domes, new cells as ridges,
      // settled cells as flat substrate.
      renderHeight(out) {
        for (let i = 0; i < N; i++) {
          if (flags[i] & 0b10)      out[i] = 1.0;
          else if (flags[i] & 0b01) out[i] = 0.55;
          else                       out[i] = 0.18;
        }
      },

      paint(gx, gy, radius, mode) {
        const newColor = (Math.random() * N_SPECIES) | 0;
        for (let dy = -radius; dy <= radius; dy++) {
          for (let dx = -radius; dx <= radius; dx++) {
            if (dx*dx + dy*dy > radius*radius) continue;
            const x = gx + dx, y = gy + dy;
            if (x < 0 || x >= W || y < 0 || y >= H) continue;
            const i = y * W + x;
            if (mode === "erase") {
              color[i] = 0; flags[i] = 0; age[i] = 0;
            } else {
              color[i] = newColor; flags[i] = 0b01;
            }
          }
        }
      },

      population() {
        let amoebas = 0, news = 0;
        for (let i = 0; i < N; i++) {
          if (flags[i] & 0b10) amoebas++;
          else if (flags[i] & 0b01) news++;
        }
        return `${amoebas} amoebas · ${news} new`;
      },

      generation() { return generation; },
    };
  }

  CA.RULES["natural-selection"] = make;
})();
