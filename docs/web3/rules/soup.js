// Primordial soup — Brownian particles drifting on a thermal field.
// A simplified ode-free visualisation of Stage 0 (cellauto/rules/abiogenesis/
// stage0_soup.py): N tracer particles wander with Gaussian displacement,
// each leaves a fading trail.  Particle "species" → palette index.
//
// This isn't the full Python Stage 0 chemistry — it's the JS-portable
// surface of it, designed to look like the rendered plate.
(function () {
  "use strict";
  window.CA = window.CA || { RULES: {} };

  const W = 200;
  const H = 200;
  const N_SPECIES = 6;

  // Distinct hue palette for 6 species, plus background.
  const PALETTE = [
    [253, 231, 37],   // viridis hi — primary
    [94, 201, 98],
    [33, 144, 141],
    [59, 82, 139],
    [212, 57, 164],   // magenta
    [230, 224, 208],  // bone
  ];

  function make() {
    let particles = [];       // {x, y, vx, vy, species}
    const field = new Uint8Array(W * H * 3);  // RGB persistent trail
    let generation = 0;

    function gauss() {
      // Box-Muller, one call → one sample.
      const u1 = Math.max(1e-9, Math.random());
      const u2 = Math.random();
      return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    }

    function spawnParticles(n) {
      particles.length = 0;
      for (let i = 0; i < n; i++) {
        particles.push({
          x: Math.random() * W,
          y: Math.random() * H,
          vx: 0,
          vy: 0,
          species: (Math.random() * N_SPECIES) | 0,
        });
      }
    }

    function clearField() {
      field.fill(0);
    }

    return {
      id: "soup",
      label: "Primordial soup · Brownian",
      formula: "dx = √(2D·dt)·N(0,1) — Brownian tracers, persistent trail.",
      shortCaption: "STAGE 0 · PRIMORDIAL SOUP",
      whatThisIs: "Chemistry, before any organisation. Particles random-walk through a substrate, " +
                  "laying down a fading occupancy trail. Oparin & Haldane's \"soup\" — the starting " +
                  "condition for everything downstream in the origin-of-life arc.",
      paletteBg: [10, 14, 22],
      paletteFg: [230, 224, 208],
      width: W,
      height: H,

      params: {
        count:       { label: "particle count",    min: 50, max: 1500, step: 50, value: 600 },
        diffusion:   { label: "diffusion D",       min: 0.05, max: 2.5, step: 0.05, value: 0.6 },
        evaporation: { label: "trail evaporation", min: 0.00, max: 0.20, step: 0.01, value: 0.04 },
        drift:       { label: "current drift",     min: -0.5, max: 0.5, step: 0.01, value: 0.0 },
      },

      controlConsequence: {
        count:       "How many tracer particles in the soup. More tracers → denser substrate, more collisions, faster mixing.",
        diffusion:   "How vigorously each particle random-walks. Raise it: trails blur into smoke. Lower it: tracks stay distinct.",
        evaporation: "How fast the trail field fades. Raise it: only the recent past shows. Lower it: long-lived history builds up — closer to a real geological record.",
        drift:       "Net current pushing every particle one way. Zero: pure diffusion. Non-zero: a flowing soup, like a real ocean current.",
      },

      onParamChange(name) {
        if (name === "count") {
          spawnParticles(this.params.count.value);
        }
      },

      randomize() {
        spawnParticles(this.params.count.value);
        clearField();
        generation = 0;
      },

      clear() {
        clearField();
        generation = 0;
      },

      reset() {
        spawnParticles(this.params.count.value);
        clearField();
        generation = 0;
      },

      step() {
        const D = this.params.diffusion.value;
        const sigma = Math.sqrt(2 * D);
        const drift = this.params.drift.value;
        const evap = this.params.evaporation.value;

        // 1) Evaporate the trail field.
        if (evap > 0) {
          const factor = 1 - evap;
          for (let i = 0; i < field.length; i++) {
            field[i] = (field[i] * factor) | 0;
          }
        }

        // 2) Advance particles + deposit.
        for (let i = 0; i < particles.length; i++) {
          const p = particles[i];
          p.x += sigma * gauss() + drift;
          p.y += sigma * gauss();
          // Torus wrap.
          p.x = ((p.x % W) + W) % W;
          p.y = ((p.y % H) + H) % H;
          const xi = p.x | 0;
          const yi = p.y | 0;
          const base = (yi * W + xi) * 3;
          const [r, g, b] = PALETTE[p.species];
          // Brighten the trail toward the species colour, clamped at 255.
          field[base]   = Math.min(255, field[base]   + ((r * 0.6) | 0));
          field[base+1] = Math.min(255, field[base+1] + ((g * 0.6) | 0));
          field[base+2] = Math.min(255, field[base+2] + ((b * 0.6) | 0));
        }

        generation++;
      },

      // v4.1.1 sprite layer (calmer revision) — every Nth tracer
      // renders as a coloured granule.  Default 600 tracers ÷ 3 = 200
      // sprites, which reads as a granular surface without overwhelming
      // the trail-field SEM substrate.
      sprites() {
        const out = [];
        const stride = 3;
        for (let i = 0; i < particles.length; i += stride) {
          const p = particles[i];
          const [r, g, b] = PALETTE[p.species];
          out.push({
            kind: "granule",
            x: p.x, y: p.y,
            scale: 1.1,
            color: "rgb(" + r + "," + g + "," + b + ")",
          });
        }
        return out;
      },

      // SEM mode: collapse the RGB trail field to luminance and normalise.
      // The Brownian trails read as granular substrate under depth shading.
      renderHeight(out) {
        let maxL = 0;
        for (let i = 0; i < W * H; i++) {
          const fi = i * 3;
          const L = 0.299 * field[fi] + 0.587 * field[fi+1] + 0.114 * field[fi+2];
          out[i] = L;
          if (L > maxL) maxL = L;
        }
        // Normalise to [0,1] so the SEM shader gets a usable dynamic range.
        const scale = maxL > 0 ? (1 / Math.max(8, maxL)) : 0;
        if (scale > 0) {
          for (let i = 0; i < W * H; i++) {
            out[i] = Math.min(1, out[i] * scale);
          }
        }
      },

      render(pixels) {
        const [br, bg, bb] = this.paletteBg;
        for (let i = 0; i < W * H; i++) {
          const fi = i * 3;
          const pi = i * 4;
          // Compose trail over the obsidian background.
          const tr = field[fi], tg = field[fi+1], tb = field[fi+2];
          pixels[pi]   = Math.min(255, br + tr);
          pixels[pi+1] = Math.min(255, bg + tg);
          pixels[pi+2] = Math.min(255, bb + tb);
          pixels[pi+3] = 255;
        }
      },

      paint(gx, gy, radius, mode) {
        // Painting injects fresh particles in a disk (or wipes the field).
        if (mode === "erase") {
          for (let dy = -radius; dy <= radius; dy++) {
            for (let dx = -radius; dx <= radius; dx++) {
              if (dx*dx + dy*dy > radius*radius) continue;
              const x = ((gx + dx) % W + W) % W;
              const y = ((gy + dy) % H + H) % H;
              const base = (y * W + x) * 3;
              field[base] = field[base+1] = field[base+2] = 0;
            }
          }
          return;
        }
        const n = Math.max(1, (radius * radius / 4) | 0);
        for (let i = 0; i < n; i++) {
          const a = Math.random() * Math.PI * 2;
          const r = Math.sqrt(Math.random()) * radius;
          particles.push({
            x: ((gx + Math.cos(a) * r) % W + W) % W,
            y: ((gy + Math.sin(a) * r) % H + H) % H,
            vx: 0,
            vy: 0,
            species: (Math.random() * N_SPECIES) | 0,
          });
        }
      },

      population() {
        return `${particles.length} particles · ${N_SPECIES} species`;
      },

      generation() { return generation; },
    };
  }

  CA.RULES.soup = make;
})();
