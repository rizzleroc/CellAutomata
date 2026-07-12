// RAF — Reflexively-Autocatalytic Food-generated set.
// A SIMULATED reaction graph (not a per-pixel field): the integrated
// state lives on a small FIXED graph of N=16 molecular species; the
// width×height grid is only a canvas the render()/renderHeight() rasterise
// onto, so cost is O(species+reactions) and resolution-independent.
//
// Building block = autocatalysis as SELF-CONTROL: a hand-wired, formally
// auditable RAF (Kauffman 1971; Hordijk & Steel 2004). Every core reaction
// is catalysed by a molecule the core itself makes (reflexive closure), and
// feeder reactions trace the core's reactants back to clamped food
// (food-generated). The set IGNITES into a self-sustaining mint glow or
// COLLAPSES to dark depending purely on three knobs:
//
//   flux = k01·[reactant], k01 = rate/(1+rate), rate = base + gain·catalysis·[catalyst]
//
// The catalyst-independent floor `base` is kept DELIBERATELY tiny (0.02), so
// with catalysis = 0 even the feeders can't out-pump decay and the whole set
// goes dark — i.e. removing catalysis breaks the set, the defining property of
// a RAF. The autocatalytic gain term `gain·catalysis·[catalyst]` is what
// actually carries ignition.
//
// The saturating squash k01 ∈ [0,1) makes the dynamics provably bounded;
// a NaN-hardened clamp01 floors everything to [0,1].
(function () {
  "use strict";
  window.CA = window.CA || { RULES: {} };

  const W = 200;
  const H = 200;

  const N = 16;
  // BASE: tiny catalyst-INDEPENDENT floor — small enough that at catalysis=0
  //       the loop (and its feeders) cannot beat decay, so the set collapses.
  // GAIN: weight on the autocatalytic term — this is what carries ignition.
  const BASE = 0.02;
  const GAIN = 0.16;

  // Species classes (fixed at construction, all indices 0 ≤ idx < N).
  const FOOD  = [0, 1, 2, 3];
  const CORE  = [4, 5, 6, 7, 8, 9, 10, 11];
  const DECOY = [12, 13, 14, 15];

  // Render colour constants.
  const BG    = [8, 11, 18];     // near-black ink (also paletteBg)
  const FG    = [120, 245, 180]; // luminous mint (also paletteFg — the living loop)
  const AMBER = [212, 170, 90];  // food fuel (visually distinct from the SET)
  const GREY  = [70, 80, 95];    // subordinate feeder/decoy edges
  const DCOL  = [90, 92, 100];   // desaturated decoy disc

  function clamp01(x) {
    // NaN-hardening: `NaN > 0` is false, so NaN maps deterministically to 0.
    return x > 0 ? (x < 1 ? x : 1) : 0;
  }

  function make() {
    const conc = new Float32Array(N);   // concentration per species — THE state
    const cN   = new Float32Array(N);   // double-buffer for synchronous update
    const flux = new Float32Array(N);   // per-species net-delta accumulator
    const px   = new Float32Array(N);   // fixed pixel x positions
    const py   = new Float32Array(N);   // fixed pixel y positions

    const isFood  = new Uint8Array(N);
    const isCore  = new Uint8Array(N);
    const isDecoy = new Uint8Array(N);

    // Reaction table (parallel arrays). M = 8 core + 4 feeder + 4 decoy = 16.
    const M = 16;
    const rR    = new Int16Array(M); // reactant
    const rP    = new Int16Array(M); // product
    const rC    = new Int16Array(M); // catalyst
    const rCore = new Uint8Array(M); // 1 if this is a core reaction

    let generation = 0;
    let built = false;

    function buildTopology() {
      // Class masks.
      for (let i = 0; i < N; i++) { isFood[i] = 0; isCore[i] = 0; isDecoy[i] = 0; }
      for (const i of FOOD)  isFood[i]  = 1;
      for (const i of CORE)  isCore[i]  = 1;
      for (const i of DECOY) isDecoy[i] = 1;

      // Pixel layout (center cx=cy=100), three concentric rings.
      const cx = 100, cy = 100;
      // FOOD: inner anchor ring r ≈ 36px.
      for (let k = 0; k < 4; k++) {
        const a = k * (Math.PI * 2 / 4) - Math.PI / 2;
        px[FOOD[k]] = cx + 0.18 * W * Math.cos(a);
        py[FOOD[k]] = cy + 0.18 * W * Math.sin(a);
      }
      // CORE: middle ring r ≈ 68px (top, clockwise).
      for (let k = 0; k < 8; k++) {
        const a = k * (Math.PI * 2 / 8) - Math.PI / 2;
        px[CORE[k]] = cx + 0.34 * W * Math.cos(a);
        py[CORE[k]] = cy + 0.34 * W * Math.sin(a);
      }
      // DECOY: outer ring r ≈ 88px (< 100 ⇒ always on-canvas), interleaved.
      for (let k = 0; k < 4; k++) {
        const a = k * (Math.PI * 2 / 4) - Math.PI / 2 + Math.PI / 4;
        px[DECOY[k]] = cx + 0.44 * W * Math.cos(a);
        py[DECOY[k]] = cy + 0.44 * W * Math.sin(a);
      }

      let m = 0;
      // CORE 8-cycle on {4..11}: reaction j takes (4+j) → (4+((j+1)%8)),
      // catalysed by core species 4+((j+3)%8) — catalysts = exactly CORE,
      // so the cycle is reflexively autocatalytic.
      for (let j = 0; j < 8; j++) {
        rR[m]    = 4 + j;
        rP[m]    = 4 + ((j + 1) % 8);
        rC[m]    = 4 + ((j + 3) % 8);
        rCore[m] = 1;
        m++;
      }
      // FEEDER (food-generation): food f → core (4+2f), catalysed by that
      // same entered core node — reactants trace back to clamped food ⇒
      // the set is Food-generated, hence a genuine RAF.
      const feeders = [[0, 4], [1, 6], [2, 8], [3, 10]];
      for (let f = 0; f < 4; f++) {
        rR[m]    = feeders[f][0];
        rP[m]    = feeders[f][1];
        rC[m]    = feeders[f][1];
        rCore[m] = 0;
        m++;
      }
      // DECOY (deliberately NON-closed): 12→13 cat13, 13→14 cat14,
      // 14→15 cat15, 15→12 cat(a decoy species). Its catalysts are only
      // ever produced WITHIN the decoy ring — no food-traceable ignition
      // source — so it can only flicker on borrowed concentration. The
      // built-in dark control: only the true RAF lights up.
      const decoyRx = [[12, 13, 13], [13, 14, 14], [14, 15, 15], [15, 12, 14]];
      for (let d = 0; d < 4; d++) {
        rR[m]    = decoyRx[d][0];
        rP[m]    = decoyRx[d][1];
        rC[m]    = decoyRx[d][2];
        rCore[m] = 0;
        m++;
      }
      built = true;
    }

    function seed() {
      if (!built) buildTopology();
      const food = this && this.params ? this.params.foodLevel.value : 0.85;
      conc.fill(0);
      for (const i of FOOD) conc[i] = food;
      // A small core spark so an ignitable regime catches fast — with
      // exactly-zero reactants every xfer is 0 and the loop could never
      // start; whether the spark grows or dies is decided by the knobs.
      for (const i of CORE) conc[i] = 0.10;
      generation = 0;
    }

    return {
      id: "raf",
      label: "RAF · autocatalytic set",
      formula: "flux = k01·[reactant], k01 = rate/(1+rate), rate = base + gain·catalysis·[catalyst]; " +
               "base→0 ⇒ no catalyst, no set; food clamped; v·=(1−decay)   (RAF: Kauffman 1971; Hordijk & Steel 2004).",
      shortCaption: "STAGE 4 · RAF",
      whatThisIs: "Autocatalysis as self-control, on a fixed 16-species reaction graph. A hand-wired, " +
                  "auditable RAF — every core reaction is catalysed by a molecule the core itself makes, " +
                  "and feeder reactions trace its reactants back to clamped food. The closed loop either " +
                  "ignites into a self-sustaining glow or collapses to dark. Plausibly how chemistry first " +
                  "held itself together before genes.",
      aboutStage: "The building block here is autocatalysis as self-control. A reflexively-autocatalytic, " +
                  "food-generated set (Kauffman 1971; Hordijk & Steel 2004) is a closed loop of reactions " +
                  "that each catalyse the next, fed only by simple food. With no genes it sustains its own " +
                  "chemistry — plausibly how metabolism first held together. Raise catalysis to ignite it; " +
                  "starve food or raise decay and it dies.",
      paletteBg: [8, 11, 18],
      paletteFg: [120, 245, 180],
      width: W,
      height: H,

      params: {
        catalysis: { label: "catalysis strength", min: 0,   max: 6,    step: 0.1,   value: 3    },
        foodLevel: { label: "food influx",        min: 0,   max: 1,    step: 0.02,  value: 0.85 },
        decay:     { label: "decay rate",         min: 0,   max: 0.3,  step: 0.005, value: 0.05 },
        substeps:  { label: "reactions / frame",  min: 1,   max: 6,    step: 1,     value: 2    },
      },

      controlConsequence: {
        catalysis: "How strongly a present catalyst speeds the reaction it governs. Because every loop reaction is " +
                   "catalysed by a molecule the loop itself makes, this is the self-amplification dial — and the " +
                   "near-zero base rate means it is genuinely load-bearing: at catalysis 0 even the food feeders can't " +
                   "out-pump decay and the set stays dark. Raise it past the ignition threshold and the autocatalytic " +
                   "ring's gain beats decay, so the set catches and locks into a steady glow; drop it back below " +
                   "threshold (at the same food and decay) and the loop can't pay its own losses and fades to dark.",
        foodLevel: "The level the four food molecules are held at each step — the set's only outside supply, feeding " +
                   "the loop's entry reactions. Keep it high and the core stays fuelled and lit; starve it and even a " +
                   "strong catalyst suffocates for lack of raw material and the loop collapses, showing a RAF set is " +
                   "food-generated, not free.",
        decay:     "How fast every non-food molecule degrades away each step — the loss the autocatalytic loop must " +
                   "out-produce to survive. Low decay lets a marginal loop persist on a faint spark; raise it and you " +
                   "lift the ignition bar until the core can no longer outrun its own losses and the whole set goes dark.",
        substeps:  "How many chemistry iterations run per visible frame. A pure speed knob — more substeps reach the " +
                   "ignited or collapsed steady state sooner, with no change to which one ultimately wins.",
      },

      // Three presets bracket the RAF transition (gain · fuel > loss).
      presets: [
        { label: "ignited set", reseed: true,
          hint: "Strong catalysis and plentiful food with gentle decay — the closed loop's round-the-ring gain beats " +
                "the loss, so the core ring catches from the food anchors and locks into a steady mint glow while the " +
                "decoy ring stays dark. A living autocatalytic set.",
          values: { catalysis: 4.5, foodLevel: 0.9, decay: 0.04, substeps: 2 } },
        { label: "starved collapse", reseed: true,
          hint: "Catalysis is strong but the food supply is choked off — the loop has the catalytic machinery but no " +
                "raw material, so it suffocates and fades to dark. Autocatalysis alone cannot run without fuel.",
          values: { catalysis: 4.5, foodLevel: 0.12, decay: 0.05, substeps: 2 } },
        { label: "subcritical (weak catalysis)", reseed: true,
          hint: "Plenty of food and only gentle decay, but catalysis is below the ignition threshold — with so little " +
                "self-amplification each pass round the ring deposits less than the loop loses, so the spark fades to " +
                "dark. Raise catalysis at this very same food and decay and the set re-ignites: this is the " +
                "sub-threshold side of the RAF transition, and catalysis is the knob that crosses it.",
          values: { catalysis: 0.2, foodLevel: 0.9, decay: 0.05, substeps: 2 } },
      ],

      randomize() {
        seed.call(this);
        // Bounded ±0.05 jitter on each core spark so some near-threshold
        // runs catch and some don't (shows the stochastic edge). Never
        // required for the defining behaviour.
        for (const i of CORE) conc[i] = clamp01(conc[i] + (Math.random() - 0.5) * 0.1);
      },

      clear() {
        // Fully dark; food re-pins only next step if foodLevel>0, so clear
        // genuinely darkens and the loop must re-seed to relight.
        conc.fill(0);
        generation = 0;
      },

      reset() { seed.call(this); },

      step() {
        if (!built) buildTopology();
        // Defensive `this` guard (mirrors seed()): fall back to defaults if
        // step() is ever invoked unbound, so the kernel never throws.
        const P    = this && this.params ? this.params : null;
        const cat  = P ? P.catalysis.value : 3;
        const food = P ? P.foodLevel.value : 0.85;
        const dec  = P ? P.decay.value     : 0.05;
        const subs = (P ? P.substeps.value : 2) | 0;

        for (let s = 0; s < subs; s++) {
          flux.fill(0);
          // 1) FOOD CLAMP first, so reactions read fresh food this step.
          for (let fi = 0; fi < FOOD.length; fi++) conc[FOOD[fi]] = food;
          // 2) REACTIONS — move mass reactant→product, accelerated by catalyst.
          for (let k = 0; k < M; k++) {
            const Ri = rR[k], Pi = rP[k], Ci = rC[k];
            // rate = tiny floor + autocatalytic gain. conc[Ci]∈[0,1], cat∈[0,6]
            // ⇒ rate∈[0.02, 0.98], always finite and > 0.
            const rate = BASE + GAIN * cat * conc[Ci];
            const k01  = rate / (1 + rate);          // squash ⇒ strictly in [0,1)
            const xfer = k01 * conc[Ri];             // ≤ conc[Ri] ≤ 1
            flux[Ri] -= xfer;
            flux[Pi] += xfer;
          }
          // 3) APPLY flux + DECAY, then HARD CLAMP (NaN-hardened).
          for (let i = 0; i < N; i++) {
            if (isFood[i]) continue;                 // food governed by clamp
            let v = conc[i] + flux[i];
            v -= dec * v;                            // v*(1−dec); dec∈[0,0.30]
            cN[i] = clamp01(v);
          }
          for (let fi = 0; fi < FOOD.length; fi++) cN[FOOD[fi]] = food; // re-pin
          conc.set(cN);
        }
        generation += subs;
      },

      render(pixels) {
        // 1) FILL the whole buffer with bg AND alpha=255 first, so any
        //    untouched pixel is already valid/finite/opaque.
        for (let p = 0; p < pixels.length; p += 4) {
          pixels[p] = BG[0]; pixels[p + 1] = BG[1]; pixels[p + 2] = BG[2]; pixels[p + 3] = 255;
        }

        // 2) EDGES (under discs). Bright only when reactant present AND
        //    catalyst active. Skip near-dark edges.
        for (let k = 0; k < M; k++) {
          const activity = clamp01(conc[rR[k]] * (0.3 + 0.7 * conc[rC[k]]));
          if (activity < 0.02) continue;
          const x0 = px[rR[k]], y0 = py[rR[k]];
          const x1 = px[rP[k]], y1 = py[rP[k]];
          let tr, tg, tb, scale;
          if (rCore[k]) { tr = FG[0]; tg = FG[1]; tb = FG[2]; scale = activity * 0.6; }
          else          { tr = GREY[0]; tg = GREY[1]; tb = GREY[2]; scale = activity * 0.30; }
          const STEPS = 48;
          for (let s = 0; s <= STEPS; s++) {
            const t = s / STEPS;
            const xi = (x0 + (x1 - x0) * t) | 0;
            const yi = (y0 + (y1 - y0) * t) | 0;
            if (xi < 0 || xi >= W || yi < 0 || yi >= H) continue;
            const p = (yi * W + xi) * 4;
            pixels[p]     = Math.min(255, pixels[p]     + tr * scale) | 0;
            pixels[p + 1] = Math.min(255, pixels[p + 1] + tg * scale) | 0;
            pixels[p + 2] = Math.min(255, pixels[p + 2] + tb * scale) | 0;
            pixels[p + 3] = 255;
          }
        }

        // 3) DISCS (over edges).
        for (let i = 0; i < N; i++) {
          const t = conc[i];               // brightness, clamped [0,1]
          const rad = 4 + 6 * t;           // ≥4 so positions read even when dark
          let cr, cg, cb;
          if (isCore[i])       { cr = BG[0] + (FG[0]    - BG[0]) * t; cg = BG[1] + (FG[1]    - BG[1]) * t; cb = BG[2] + (FG[2]    - BG[2]) * t; }
          else if (isFood[i])  { cr = BG[0] + (AMBER[0] - BG[0]) * t; cg = BG[1] + (AMBER[1] - BG[1]) * t; cb = BG[2] + (AMBER[2] - BG[2]) * t; }
          else                 { cr = BG[0] + (DCOL[0]  - BG[0]) * t; cg = BG[1] + (DCOL[1]  - BG[1]) * t; cb = BG[2] + (DCOL[2]  - BG[2]) * t; }

          const cxp = px[i], cyp = py[i];

          // Soft low-intensity glow halo for an ignited core (literally blooms).
          if (isCore[i] && t > 0.5) {
            const gr = rad * 1.6;
            const gi = 0.4 * t;
            const x0 = Math.max(0, (cxp - gr) | 0), x1 = Math.min(W - 1, (cxp + gr) | 0);
            const y0 = Math.max(0, (cyp - gr) | 0), y1 = Math.min(H - 1, (cyp + gr) | 0);
            for (let yy = y0; yy <= y1; yy++) {
              for (let xx = x0; xx <= x1; xx++) {
                const dx = xx - cxp, dy = yy - cyp;
                const d2 = dx * dx + dy * dy;
                if (d2 > gr * gr) continue;
                const fall = 1 - Math.sqrt(d2) / gr; // ∈ [0,1]
                const p = (yy * W + xx) * 4;
                pixels[p]     = Math.min(255, pixels[p]     + FG[0] * gi * fall) | 0;
                pixels[p + 1] = Math.min(255, pixels[p + 1] + FG[1] * gi * fall) | 0;
                pixels[p + 2] = Math.min(255, pixels[p + 2] + FG[2] * gi * fall) | 0;
                pixels[p + 3] = 255;
              }
            }
          }

          // Filled disc with a soft rim falloff for a lit-orb look.
          const x0 = Math.max(0, (cxp - rad) | 0), x1 = Math.min(W - 1, (cxp + rad) | 0);
          const y0 = Math.max(0, (cyp - rad) | 0), y1 = Math.min(H - 1, (cyp + rad) | 0);
          for (let yy = y0; yy <= y1; yy++) {
            for (let xx = x0; xx <= x1; xx++) {
              const dx = xx - cxp, dy = yy - cyp;
              const d2 = dx * dx + dy * dy;
              if (d2 > rad * rad) continue;
              const fall = 1 - 0.4 * (Math.sqrt(d2) / rad); // ∈ [0.6,1]
              const p = (yy * W + xx) * 4;
              pixels[p]     = Math.min(255, Math.max(pixels[p],     cr * fall)) | 0;
              pixels[p + 1] = Math.min(255, Math.max(pixels[p + 1], cg * fall)) | 0;
              pixels[p + 2] = Math.min(255, Math.max(pixels[p + 2], cb * fall)) | 0;
              pixels[p + 3] = 255;
            }
          }

          // FOOD: constant thin amber outline ring (always) — sources read
          // as "externally supplied" even when the loop is dark.
          if (isFood[i]) {
            const orad = rad + 2;
            const STEPS = 64;
            for (let s = 0; s < STEPS; s++) {
              const a = s / STEPS * Math.PI * 2;
              const xi = (cxp + orad * Math.cos(a)) | 0;
              const yi = (cyp + orad * Math.sin(a)) | 0;
              if (xi < 0 || xi >= W || yi < 0 || yi >= H) continue;
              const p = (yi * W + xi) * 4;
              pixels[p]     = Math.min(255, Math.max(pixels[p],     AMBER[0] * 0.7)) | 0;
              pixels[p + 1] = Math.min(255, Math.max(pixels[p + 1], AMBER[1] * 0.7)) | 0;
              pixels[p + 2] = Math.min(255, Math.max(pixels[p + 2], AMBER[2] * 0.7)) | 0;
              pixels[p + 3] = 255;
            }
          }
        }
      },

      renderHeight(out) {
        // 1) Flat dark substrate.
        out.fill(0);
        // 2) Min-capped Gaussian dome per lit species.
        for (let i = 0; i < N; i++) {
          const amp = conc[i];
          if (amp <= 0.01) continue;
          const sigma = 6 + 5 * amp;       // ≥6 ⇒ 2·sigma² ≥ 72 > 0
          const denom = 2 * sigma * sigma;
          const win = Math.ceil(3 * sigma);
          const cxp = px[i], cyp = py[i];
          const x0 = Math.max(0, (cxp - win) | 0), x1 = Math.min(W - 1, (cxp + win) | 0);
          const y0 = Math.max(0, (cyp - win) | 0), y1 = Math.min(H - 1, (cyp + win) | 0);
          for (let yy = y0; yy <= y1; yy++) {
            for (let xx = x0; xx <= x1; xx++) {
              const dx = xx - cxp, dy = yy - cyp;
              const d2 = dx * dx + dy * dy;
              const g = amp * Math.exp(-d2 / denom); // exp(-x), x≥0 ∈ (0,1]
              const idx = yy * W + xx;
              const v = out[idx] + g;
              out[idx] = v < 1 ? v : 1;              // min-cap at 1
            }
          }
        }
      },

      paint(gx, gy, radius, mode) {
        if (!built) buildTopology();
        // Find the nearest species disc to (gx,gy) — no toroidal wrap; the
        // network is bounded, not a grid.
        let best = -1, bestD = Infinity;
        for (let i = 0; i < N; i++) {
          const dx = gx - px[i], dy = gy - py[i];
          const d2 = dx * dx + dy * dy;
          if (d2 < bestD) { bestD = d2; best = i; }
        }
        if (best < 0) return;
        if (mode === "erase") {
          // Knock out a node — if it's load-bearing in the closed loop,
          // the whole RAF dies; the decoy never sustains regardless.
          conc[best] = 0;
        } else {
          // Hand-inject to ignite a near-threshold loop.
          conc[best] = clamp01(conc[best] + 0.5);
        }
      },

      population() {
        let sum = 0;
        for (const i of CORE) sum += conc[i];
        const mean = sum / CORE.length;
        const regime = mean > 0.35 ? "IGNITED" : "dark";
        return `core ${mean.toFixed(2)} · ${regime}`;
      },

      generation() { return generation; },
    };
  }

  CA.RULES.raf = make;
})();
