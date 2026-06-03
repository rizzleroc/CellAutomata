// Genetic code — the codon→amino-acid map self-organising into an
// error-minimising universal controller.  A caricature of Vetsigian,
// Woese & Goldenfeld (2006, PNAS 103:10696): the code is not a frozen
// accident but the product of selection for mutation-buffering plus
// horizontal gene transfer that drives it toward universality.
//
// An 8×8 toroidal lattice of 64 codons, each assigned one of K
// amino-acid CLASSES laid out on a 1-D physico-chemical axis
// (prop[k] = k/(K-1), the Woese polar-requirement stand-in).  The
// local energy of a codon is the squared property-distance to its 4
// single-mutation (von-Neumann, wrapped) neighbours; low energy ⇔ a
// point mutation lands on a chemically similar class ⇔ the code is
// mutation-buffered.  A synchronous double-buffered Glauber relaxation
// under selection β, plus 3×3 horizontal-transfer of fitter sub-codes,
// drives a scrambled map (rainbow confetti) into smooth chemically-graded
// blocks (a coherent colour gradient) — the genetic code coming into being.
(function () {
  "use strict";
  window.CA = window.CA || { RULES: {} };

  const NC = 8;            // codons per side
  const N = NC * NC;       // 64 codons
  const CELL = 20;         // display px per codon
  const W = NC * CELL;     // 160
  const H = NC * CELL;     // 160
  const KMAX = 12;         // palette/prop arrays sized so `classes` can range without realloc
  const EMAX = 4;          // max E_local = 4 neighbours × (Δprop ≤ 1)²

  function make() {
    let code   = new Int8Array(N);        // codon → amino-acid class (the genetic code)
    let codeN  = new Int8Array(N);        // double buffer for the synchronous selection sweep
    const prop = new Float32Array(KMAX);  // class → 1-D physico-chemical coordinate ∈ [0,1]
    const robust = new Float32Array(N);   // per-codon local robustness ∈ [0,1] (recomputed each step)
    const palette = new Uint8Array(KMAX * 3); // fixed hue-by-chemistry ramp, built once
    let generation = 0;
    let lastK = 0;

    // --- fixed HSV→RGB palette: adjacent classes get adjacent hues, so
    //     a chemically-smooth code reads as a coherent colour gradient. ---
    (function buildPalette() {
      const S = 0.62, V = 0.92;
      for (let k = 0; k < KMAX; k++) {
        const h = (k / KMAX) * 320;          // degrees, 0..320
        const c = V * S;
        const hp = h / 60;
        const xx = c * (1 - Math.abs((hp % 2) - 1));
        let r = 0, g = 0, b = 0;
        if (hp < 1)      { r = c; g = xx; b = 0; }
        else if (hp < 2) { r = xx; g = c; b = 0; }
        else if (hp < 3) { r = 0; g = c; b = xx; }
        else if (hp < 4) { r = 0; g = xx; b = c; }
        else if (hp < 5) { r = xx; g = 0; b = c; }
        else             { r = c; g = 0; b = xx; }
        const m = V - c;
        palette[k * 3]     = ((r + m) * 255) | 0;
        palette[k * 3 + 1] = ((g + m) * 255) | 0;
        palette[k * 3 + 2] = ((b + m) * 255) | 0;
      }
    })();

    function curK() {
      let K = this && this.params ? (this.params.classes.value | 0) : 8;
      if (K < 2) K = 2; else if (K > KMAX) K = KMAX;
      return K;
    }

    let baseE = 1;   // mean per-codon E_local of a fully-random K-code (∈ (0,EMAX]).

    function buildProp(K) {
      const denom = Math.max(1, K - 1);
      for (let k = 0; k < K; k++) prop[k] = k / denom;
      // leave higher slots as-is; they are never indexed while labels are < K.
      // Random-code baseline: the expected E_local of a uniformly-random code is
      //   4 · E[(prop_a − prop_b)²]  over independent uniform draws a,b ∈ 0..K-1.
      // Computed exactly over the K evenly-spaced levels so the displayed
      // robustness can be baseline-subtracted (a scrambled map reads near 0, a
      // perfectly-buffered one near 1) — widening the legible dynamic range
      // instead of compressing it into the top fifth of the scale.
      let s2 = 0;
      for (let i = 0; i < K; i++) {
        for (let j = 0; j < K; j++) { const d = prop[i] - prop[j]; s2 += d * d; }
      }
      const meanSq = s2 / (K * K);     // E[(Δprop)²]
      baseE = 4 * meanSq;              // mean E_local over 4 neighbours
      if (!(baseE > 1e-6)) baseE = 1e-6;
    }

    // E_local(g, a) = Σ over 4 wrapped von-Neumann neighbours of (prop[a] − prop[code[j]])²
    function eLocal(g, a, src) {
      const cx = g % NC, cy = (g / NC) | 0;
      const xm = (cx - 1 + NC) % NC, xp = (cx + 1) % NC;
      const ym = (cy - 1 + NC) % NC, yp = (cy + 1) % NC;
      const pa = prop[a];
      let e = 0, d;
      d = pa - prop[src[cy * NC + xm]]; e += d * d;
      d = pa - prop[src[cy * NC + xp]]; e += d * d;
      d = pa - prop[src[ym * NC + cx]]; e += d * d;
      d = pa - prop[src[yp * NC + cx]]; e += d * d;
      return e;
    }

    // mean E_local over a wrapped 3×3 block centred at (ccx,ccy) on `src`.
    function blockE(ccx, ccy, src) {
      let sum = 0;
      for (let dy = -1; dy <= 1; dy++) {
        const yy = ((ccy + dy) % NC + NC) % NC;
        for (let dx = -1; dx <= 1; dx++) {
          const xx = ((ccx + dx) % NC + NC) % NC;
          const g = yy * NC + xx;
          sum += eLocal(g, src[g], src);
        }
      }
      return sum / 9;
    }

    function recomputeRobust() {
      // Baseline-subtracted display robustness: r = 1 − E_local/baseE, clamped
      // to [0,1].  A codon no better than a random assignment (E_local ≈ baseE)
      // reads ~0; a fully mutation-buffered codon (E_local → 0) reads 1.  This
      // is a DISPLAY rescaling only — it never feeds back into the dynamics
      // (the Glauber sweep evaluates raw eLocal directly), so fidelity is intact.
      const inv = 1 / baseE;
      for (let g = 0; g < N; g++) {
        let r = 1 - eLocal(g, code[g], code) * inv;
        if (r < 0) r = 0; else if (r > 1) r = 1;
        robust[g] = r;
      }
    }

    function seed(K) {
      const top = K - 1;
      for (let g = 0; g < N; g++) {
        let a = (Math.random() * K) | 0;
        if (a > top) a = top;          // guard the rand()===1.0 edge
        code[g] = a;
      }
      buildProp(K);
      recomputeRobust();
      generation = 0;
      lastK = K;
    }

    return {
      id: "code",
      label: "Genetic code · self-organising",
      formula: "E_local(g,a) = Σ_j∈N(g) (prop[a] − prop[code[j]])²;  pAcc = 1/(1+exp(clamp(β·ΔE,−30,30)))  (Vetsigian, Woese & Goldenfeld 2006).",
      shortCaption: "STAGE 12 · GENETIC CODE",
      whatThisIs: "The controller as a building block. The codon→amino-acid map is not a frozen " +
                  "accident — it self-organises so single mutations land on chemically similar " +
                  "amino acids (mutation-buffering), and horizontal gene transfer drives it toward " +
                  "one shared universal code. A scrambled map crystallises into smooth, error-minimising blocks.",
      aboutStage: "The building block here is the controller itself — the genetic code coming into being. " +
                  "An assignment of codons to amino-acid classes self-organises so single mutations land " +
                  "on chemically similar amino acids, while horizontal gene transfer spreads the fittest " +
                  "sub-codes toward one universal code. As Vetsigian, Woese & Goldenfeld (2006) argued, the " +
                  "code is no frozen accident but an evolved, error-minimising community consensus.",
      paletteBg: [10, 14, 22],
      paletteFg: [230, 224, 208],
      width: W,
      height: H,

      params: {
        selection:    { label: "β — selection for error-minimisation", min: 0,   max: 12,  step: 0.25, value: 4    },
        transfer:     { label: "HGT — horizontal transfer strength",   min: 0,   max: 1,   step: 0.02, value: 0.4  },
        mutationRate: { label: "reassignment / mutation rate",         min: 0,   max: 0.5, step: 0.01, value: 0.08 },
        classes:      { label: "amino-acid classes (K)",               min: 2,   max: 12,  step: 1,    value: 8    },
        sweeps:       { label: "relaxation sweeps / frame",            min: 1,   max: 8,   step: 1,    value: 3    },
      },

      controlConsequence: {
        selection:    "How strongly evolution rewards a mutation-buffered code — the pressure to make neighbouring codons code chemically similar amino acids. Near zero the map stays a frozen accident; raise it and error-minimising blocks crystallise and robustness climbs toward the canonical code.",
        transfer:     "How readily a fit codon sub-assignment is copied sideways to another region (Vetsigian-Woese-Goldenfeld). At zero the code evolves vertically and freezes into several mismatched rival domains; raise it and superior sub-codes broadcast across the dish, merging domains into one shared universal code.",
        mutationRate: "Fraction of codons randomly reassigned each sweep regardless of selection — codon ambiguity and innovation that the Glauber gate cannot immediately veto. A little anneals out domain-wall seams for a cleaner global code; too much and reassignments outpace selection so no stable code can ever freeze in (error catastrophe).",
        classes:      "How many distinct amino-acid chemistry classes the 64 codons are assigned among. Fewer classes give a coarse code with a few big blocks; more classes force a finer mosaic of smaller domains. Either way the code still self-organises into smooth, mutation-buffered territories.",
        sweeps:       "How many selection-plus-transfer micro-sweeps run per visible frame. Pure speed knob — more sweeps reach the organised code in fewer frames; it changes neither the dynamics nor the final code that emerges.",
      },

      // P1-D2: named regimes along the frozen-accident → universal-code axis.
      presets: [
        { label: "frozen accident", reseed: true,
          hint: "Almost no selection — the Glauber gate still accepts code-degrading reassignments nearly half the time, so the map random-walks and stays a scrambled confetti patchwork pinned near the random robustness baseline. The pre-organisation null case Woese argued against.",
          values: { selection: 0.5, transfer: 0, mutationRate: 0.08, classes: 8, sweeps: 3 } },
        { label: "vertical only (no HGT)", reseed: true,
          hint: "Strong error-minimisation but zero horizontal transfer — blocks nucleate and the code organises, but freezes into several mismatched rival domains, a stuck local optimum. Vertical evolution alone.",
          values: { selection: 7, transfer: 0, mutationRate: 0.06, classes: 8, sweeps: 3 } },
        { label: "universal controller (HGT)", reseed: true,
          hint: "Strong selection plus vigorous horizontal transfer — good sub-codes broadcast across the community, rival domains merge, and one smooth high-robustness canonical-like code sweeps in fast. Vetsigian-Woese-Goldenfeld's universal code.",
          values: { selection: 8, transfer: 0.65, mutationRate: 0.07, classes: 8, sweeps: 4 } },
      ],

      randomize() { seed(curK.call(this)); },

      // Degenerate, trivially-smooth, information-free single-class code:
      // E_local = 0 everywhere → robust = 1.  Finite before any step.
      clear() {
        const K = curK.call(this);
        code.fill(0);
        buildProp(K);
        recomputeRobust();
        generation = 0;
        lastK = K;
      },

      reset() { seed(curK.call(this)); },

      // Keep labels/prop valid the instant the `classes` slider moves.
      onParamChange(name) {
        if (name === "classes") {
          const K = curK.call(this);
          buildProp(K);
          for (let g = 0; g < N; g++) code[g] %= K;   // labels stay in 0..K-1
          recomputeRobust();
          lastK = K;
        }
      },

      step() {
        // --- runtime-K guard: clamp + remap so prop/palette never go out of range. ---
        const K = curK.call(this);
        if (K !== lastK) {
          buildProp(K);
          for (let g = 0; g < N; g++) code[g] %= K;
          lastK = K;
        }
        const beta = this.params.selection.value;
        const mu   = this.params.mutationRate.value;
        const h    = this.params.transfer.value;
        let sweeps = this.params.sweeps.value | 0;
        if (sweeps < 0) sweeps = 0;            // never let generation() run backwards
        const top = K - 1;
        let nHGT = Math.round(h * 2 * NC);     // 0..16 transfer events per sweep
        if (nHGT < 0) nHGT = 0;                // guard out-of-range negative transfer

        for (let s = 0; s < sweeps; s++) {
          // (1) SELECTION — synchronous double-buffered Glauber single-site update.
          //     Each site proposes a UNIFORMLY-RANDOM candidate class and adopts
          //     it only if the candidate survives the β-weighted Glauber gate
          //     pAcc = 1/(1+exp(β·ΔE)).  This is the load-bearing fidelity fix:
          //     the candidate is an unbiased proposal (not a neighbour-copy that
          //     mechanically lowers ΔE), so SELECTION β is what drives order.
          //       • β=0  → pAcc=0.5 for every move, good or bad.  The proposal is
          //         unbiased, so the equilibrium is the uniform (maximally
          //         scrambled) distribution: the map stays a frozen accident and
          //         robustness sits at its random baseline — no organisation.
          //       • high β → energy-raising candidates are rejected (pAcc→0) while
          //         energy-lowering ones pass (pAcc→1), so mutation-buffered
          //         chemically-graded blocks crystallise and robustness climbs.
          //     Evaluated against the pre-sweep `code` snapshot, written into
          //     codeN, swapped at the end (order-independent / synchronous).
          codeN.set(code);
          for (let g = 0; g < N; g++) {
            const cur = code[g];
            let a = (Math.random() * K) | 0;   // unbiased uniform candidate class
            if (a > top) a = top;
            if (a === cur) { codeN[g] = cur; continue; }            // null move
            const dE = eLocal(g, a, code) - eLocal(g, cur, code);   // ∈ [−4,+4]
            let z = beta * dE;
            if (z < -30) z = -30; else if (z > 30) z = 30;          // clamp before exp
            const pAcc = 1 / (1 + Math.exp(z));                     // ∈ (≈1e-14, ≈1-1e-14)
            codeN[g] = (Math.random() < pAcc) ? a : cur;
          }
          const tmp = code; code = codeN; codeN = tmp;

          // (1b) MUTATION — UNCONDITIONAL random reassignment of a fraction `mu`
          //      of codons (codon ambiguity / innovation).  Crucially this
          //      BYPASSES the selection gate: selection cannot veto a mutation
          //      the instant it lands.  A little mutation anneals out domain-wall
          //      seams; too much (high `mu`) injects scramble faster than the
          //      Glauber sweep can repair it, so no stable code can freeze in —
          //      the documented error catastrophe.  Expected mutations per sweep
          //      = round(mu·N); applied in-place after the swap.
          let nMut = Math.round(mu * N);
          if (nMut < 0) nMut = 0; else if (nMut > N) nMut = N;   // guard out-of-range mu
          for (let m = 0; m < nMut; m++) {
            const g = (Math.random() * N) | 0;
            let a = (Math.random() * K) | 0;
            if (a > top) a = top;
            code[g] = a;
          }

          // (2) HORIZONTAL GENE TRANSFER — broadcast fitter 3×3 sub-codes across
          //     the grid so rival domains merge into one shared universal code.
          //     A donor block is copied over a recipient only when the donor is
          //     strictly the fitter (lower-energy) sub-code — i.e. transfer flows
          //     consensus outward, it does not inject noise.  This is what
          //     distinguishes the "universal controller" regime from "vertical
          //     only": vertical selection settles into several mismatched rival
          //     domains, and HGT is the only force that fuses them.
          for (let e = 0; e < nHGT; e++) {
            const sx = (Math.random() * NC) | 0, sy = (Math.random() * NC) | 0;
            const tx = (Math.random() * NC) | 0, ty = (Math.random() * NC) | 0;
            const eDon = blockE(sx, sy, code);
            const eAcc = blockE(tx, ty, code);
            if (eDon < eAcc) {
              for (let dy = -1; dy <= 1; dy++) {
                const syy = ((sy + dy) % NC + NC) % NC;
                const tyy = ((ty + dy) % NC + NC) % NC;
                for (let dx = -1; dx <= 1; dx++) {
                  const sxx = ((sx + dx) % NC + NC) % NC;
                  const txx = ((tx + dx) % NC + NC) % NC;
                  code[tyy * NC + txx] = code[syy * NC + sxx];   // pure integer copy
                }
              }
            }
          }
        }

        // (3) ROBUSTNESS recompute on the post-sweep code (for render/height/readout).
        recomputeRobust();
        generation += sweeps;
      },

      render(pixels) {
        // Codon grid coloured by class (adjacent classes → adjacent hues),
        // brightness scaled by robustness, with a faint grout between cells.
        const bg0 = 10, bg1 = 14, bg2 = 22;
        for (let py = 0; py < H; py++) {
          const cy = (py / CELL) | 0;
          const fy = py - cy * CELL;
          for (let px = 0; px < W; px++) {
            const cx = (px / CELL) | 0;
            const fx = px - cx * CELL;
            const g = cy * NC + cx;
            let kls = code[g]; if (kls < 0) kls = 0; else if (kls >= KMAX) kls = KMAX - 1;
            const b = 0.55 + 0.45 * robust[g];        // ∈ [0.55,1.0]
            let r = (palette[kls * 3]     * b) | 0;
            let gg = (palette[kls * 3 + 1] * b) | 0;
            let bb = (palette[kls * 3 + 2] * b) | 0;
            // faint grout: blend toward bg on the 1-px cell border.
            if (fx === 0 || fy === 0) {
              r  = (r  * 0.35 + bg0 * 0.65) | 0;
              gg = (gg * 0.35 + bg1 * 0.65) | 0;
              bb = (bb * 0.35 + bg2 * 0.65) | 0;
            }
            const p = (py * W + px) * 4;
            pixels[p] = r; pixels[p + 1] = gg; pixels[p + 2] = bb; pixels[p + 3] = 255;
          }
        }
      },

      // SEM height = per-codon robustness, block-expanded into smooth mesas.
      renderHeight(out) {
        for (let py = 0; py < H; py++) {
          const cy = (py / CELL) | 0;
          for (let px = 0; px < W; px++) {
            const cx = (px / CELL) | 0;
            let v = robust[cy * NC + cx];
            if (v < 0) v = 0; else if (v > 1) v = 1;
            out[py * W + px] = v;
          }
        }
      },

      paint(gx, gy, radius, mode) {
        const K = curK.call(this);
        const top = K - 1;
        let ccx = (gx / CELL) | 0, ccy = (gy / CELL) | 0;
        for (let dy = -radius; dy <= radius; dy++) {
          for (let dx = -radius; dx <= radius; dx++) {
            if (dx * dx + dy * dy > radius * radius) continue;
            const cx = ((ccx + dx) % NC + NC) % NC;
            const cy = ((ccy + dy) % NC + NC) % NC;
            const g = cy * NC + cx;
            if (mode === "erase") {
              let a = (Math.random() * K) | 0;     // re-scramble: fresh random class
              if (a > top) a = top;
              code[g] = a;
            } else {
              code[g] = 0;                          // hand-plant a coherent block (class 0)
            }
          }
        }
        recomputeRobust();
      },

      // Contiguous block-count (4-connected flood fill over equal classes) +
      // mean robustness %.
      population() {
        const seen = new Uint8Array(N);
        const stack = new Int16Array(N);
        let blocks = 0;
        for (let start = 0; start < N; start++) {
          if (seen[start]) continue;
          blocks++;
          const cls = code[start];
          let sp = 0;
          stack[sp++] = start;
          seen[start] = 1;
          while (sp > 0) {
            const g = stack[--sp];
            const cx = g % NC, cy = (g / NC) | 0;
            const nb = [
              cy * NC + ((cx - 1 + NC) % NC),
              cy * NC + ((cx + 1) % NC),
              ((cy - 1 + NC) % NC) * NC + cx,
              ((cy + 1) % NC) * NC + cx,
            ];
            for (let i = 0; i < 4; i++) {
              const j = nb[i];
              if (!seen[j] && code[j] === cls) { seen[j] = 1; stack[sp++] = j; }
            }
          }
        }
        let sum = 0;
        for (let g = 0; g < N; g++) sum += robust[g];
        const pct = (sum / N * 100) | 0;
        return `${blocks} blocks · ${pct}%`;
      },

      generation() { return generation; },
    };
  }

  CA.RULES.code = make;
})();
