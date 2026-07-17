// LUCA — lineage convergence toward the last universal common ancestor.
//
// A population of 16-bit GENOMES on a 120×120 toroidal lattice evolves under
// three biology-first descent controls: DIVERGENCE (per-locus mutation),
// SELECTION (local tournament biased toward a fixed environmental optimum),
// and HORIZONTAL TRANSFER (uniform-crossover allele pooling between cells).
// A per-locus majority consensus above a tunable threshold builds coreMask —
// the live universal-ancestor genome — and coreField[i] measures each cell's
// membership in it. Slide divergence up against transfer/selection to cross
// the error-threshold-like LUCA ↔ no-LUCA transition.
// (Woese 1998, PNAS; Weiss et al. 2016, Nat. Microbiol.)
(function () {
  "use strict";
  window.CA = window.CA || { RULES: {} };

  const W = 120;
  const H = 120;
  const N = W * H;
  const G = 16;                       // genes per genome (one Uint16)

  // Precomputed 16-bit popcount table — O(1) Hamming / fitness / membership.
  const POP16 = new Uint8Array(65536);
  for (let v = 0; v < 65536; v++) {
    let c = 0, t = v;
    while (t) { c += t & 1; t >>= 1; }
    POP16[v] = c;
  }

  function make() {
    let genome     = new Uint16Array(N);   // each cell's 16-gene bit vector
    let genomeNext = new Uint16Array(N);    // double buffer (snapshot reads)
    const bitCount = new Int32Array(G);     // scratch: per-locus allele-1 tally
    const coreField = new Float32Array(N);  // membership in emergent core [0,1]

    let coreMask = 0;        // which loci are conserved enough to be core
    let coreValue = 0;       // per-locus CONSENSUS bit value (the live LUCA genome)
    let coreCount = 0;       // POP16[coreMask], 0..16
    let envOptimum = 0;      // fixed fitness target = the adapted niche
    let generation = 0;

    // Bits agreeing with the optimum, 0..16.
    function fit(g) { return POP16[(~(g ^ envOptimum)) & 0xFFFF]; }

    // Rebuild the consensus core from the CURRENT genome buffer.
    // A locus joins the core when its MAJORITY allele (0 or 1) is carried by
    // at least coreFrac·N cells — agreement, not allele-1 frequency, so a
    // locus conserved at 0 counts exactly like one conserved at 1. coreValue
    // records the winning bit per core locus = the reconstructed LUCA genome.
    function rebuildCore(coreFrac) {
      bitCount.fill(0);
      for (let i = 0; i < N; i++) {
        const g = genome[i];
        for (let b = 0; b < G; b++) bitCount[b] += (g >> b) & 1;
      }
      const thr = coreFrac * N;
      let mask = 0, value = 0;
      for (let b = 0; b < G; b++) {
        const ones = bitCount[b];
        const zeros = N - ones;
        const consensusBit = ones >= zeros ? 1 : 0;   // majority allele
        const agree = consensusBit ? ones : zeros;    // cells holding it
        if (agree >= thr) {
          mask |= (1 << b);
          if (consensusBit) value |= (1 << b);
        }
      }
      coreMask = mask;
      coreValue = value & mask;
      coreCount = POP16[coreMask];
    }

    // Per-cell core membership = fraction of core loci whose bit MATCHES the
    // consensus value, [0,1]. XOR against coreValue (masked to core loci)
    // gives the mismatches; subtract from coreCount so a cell faithfully
    // carrying a conserved-0 locus is credited exactly like a conserved-1 one.
    function recomputeField() {
      if (coreCount === 0) { coreField.fill(0); return; }
      for (let i = 0; i < N; i++) {
        const miss = POP16[(genome[i] ^ coreValue) & coreMask];
        coreField[i] = (coreCount - miss) / coreCount;
      }
    }

    // Random in-bounds von-Neumann/Moore neighbour (toroidal, never both 0).
    function neighbour(x, y) {
      let dx = 0, dy = 0;
      do {
        dx = ((Math.random() * 3) | 0) - 1;
        dy = ((Math.random() * 3) | 0) - 1;
      } while (dx === 0 && dy === 0);
      const nx = ((x + dx) % W + W) % W;
      const ny = ((y + dy) % H + H) % H;
      return ny * W + nx;
    }

    function seed(freshOptimum) {
      if (freshOptimum) envOptimum = (Math.random() * 65536) | 0;
      // Maximally diverse primordial soup — no ancestor yet.
      for (let i = 0; i < N; i++) genome[i] = (Math.random() * 65536) | 0;
      generation = 0;
      // Compute consensus + field once so the first render is valid.
      rebuildCore(0.85);
      recomputeField();
    }

    return {
      id: "luca",
      label: "LUCA · lineage convergence",
      formula: "core = { gene b : max(n₀,n₁) ≥ coreFrac·N }, consensus bit = argmax;  fit(g)=popcount(¬(g⊕env))  (Woese 1998; Weiss et al. 2016).",
      shortCaption: "STAGE 13 · LUCA",
      whatThisIs: "Descent control as a building block — the last universal common ancestor. " +
                  "A population of bit-vector genomes diverges by mutation, converges under selection " +
                  "toward a fixed environmental optimum, and pools winning alleles by horizontal transfer. " +
                  "A per-locus majority consensus IS the reconstructed universal ancestor: a genome no " +
                  "single cell ever held, distilled from the whole population.",
      aboutStage: "The building block here is descent control — the last universal common ancestor. " +
                  "Bit-vector genomes mutate, are selected toward a fixed environmental optimum, and " +
                  "swap alleles by horizontal transfer; a per-locus majority consensus is the reconstructed " +
                  "LUCA — a genome no single cell holds. It matters because, as Woese (1998) and Weiss et al. " +
                  "(2016) argue, pervasive gene transfer makes LUCA a shareable consensus, not one cell.",
      paletteBg: [10, 14, 22],
      paletteFg: [230, 224, 208],
      width: W,
      height: H,

      params: {
        divergence:    { label: "μ — divergence (mutation rate)", min: 0,   max: 0.05, step: 0.001, value: 0.004 },
        selection:     { label: "selection pressure",             min: 0,   max: 1,    step: 0.02,  value: 0.5   },
        transfer:      { label: "horizontal transfer (genome pooling)", min: 0, max: 1, step: 0.02, value: 0.4   },
        coreThreshold: { label: "core consensus threshold",       min: 0.5, max: 0.99, step: 0.01,  value: 0.85  },
        substeps:      { label: "generations / frame",            min: 1,   max: 6,    step: 1,     value: 2     },
      },

      controlConsequence: {
        divergence:    "Per-gene mutation rate each generation — the engine of lineage divergence. Low: descendants stay near their parent and a shared ancestral core can accumulate and persist as LUCA. High: every copy scrambles its genome, no gene keeps a majority, and no universal ancestor can be distilled — the conserved core shatters into many disjoint lineages.",
        selection:     "How strongly a fitter neighbour out-competes a cell for the environment-optimal genome. Zero: neutral drift — the 'core' is just whatever bits happen to fix by chance. High: the population is pulled crisply onto the same adaptive feature set, so selection decides WHICH genes become LUCA's conserved core and gives convergence a direction.",
        transfer:      "Probability a cell imports alleles from a neighbour (horizontal gene transfer / recombination). This is the LUCA-maker: it pools winning genes laterally across lineage boundaries so the conserved core spreads fast and a sharp universal ancestor emerges. Set it to zero and lineages inherit only vertically, so convergence is slow and clade-by-clade.",
        coreThreshold: "What fraction of the whole population must carry a gene before it counts as part of the universal core. Lower: a looser, larger reconstructed LUCA core that lights up easily. Higher: only near-universal genes qualify, giving a stricter, smaller conserved core — the intersection of nearly all lineages.",
        substeps:      "How many descent generations are simulated per visible frame. Pure speed knob — more generations per frame fast-forwards toward the LUCA-or-shatter outcome without changing which steady state is reached.",
      },

      presets: [
        { label: "sharp LUCA", reseed: true,
          hint: "High transfer and strong selection with low mutation — winning genes pool laterally across the whole field and the population converges onto one environment-optimal genome. A near-universal conserved core lights up as a bright bone-cream plateau: a single, sharp last universal common ancestor.",
          values: { divergence: 0.002, selection: 0.85, transfer: 0.8, coreThreshold: 0.85, substeps: 2 } },
        { label: "balanced descent", reseed: true,
          hint: "Moderate mutation, selection and transfer — a real conserved core forms and most cells share it, but ongoing mutation keeps a few divergent descendant clades alive around the edges. LUCA exists as a consensus, with daughter lineages branching off it.",
          values: { divergence: 0.006, selection: 0.5, transfer: 0.4, coreThreshold: 0.85, substeps: 2 } },
        { label: "tree of life", reseed: true,
          hint: "Strong selection but no horizontal transfer and low mutation — lineages can only pass genes vertically, so convergence is slow and clade-by-clade: coloured domains compete until one slowly becomes the ancestor of all.",
          values: { divergence: 0.004, selection: 0.8, transfer: 0, coreThreshold: 0.85, substeps: 2 } },
        { label: "no universal ancestor", reseed: true,
          hint: "High divergence overwhelms weak selection and little transfer — mutation outruns convergence, so no gene ever becomes universal. The core collapses to nothing and the field fragments into many disjoint, saturated lineages with no common ancestor to reconstruct.",
          values: { divergence: 0.04, selection: 0.1, transfer: 0.05, coreThreshold: 0.85, substeps: 2 } },
      ],

      randomize() { seed(true); },                       // fresh envOptimum
      reset()     { seed(false); },                      // keep envOptimum (reproducible presets)
      clear() {
        genome.fill(0); coreField.fill(0);
        coreMask = 0; coreValue = 0; coreCount = 0; generation = 0;
      },

      step() {
        const mu       = this.params.divergence.value;
        const sel      = this.params.selection.value;
        const hgt      = this.params.transfer.value;
        const coreFrac = this.params.coreThreshold.value;
        let subs       = this.params.substeps.value | 0;
        if (subs < 1) subs = 1;

        for (let s = 0; s < subs; s++) {
          // STAGE A — rebuild consensus core from current genome buffer.
          rebuildCore(coreFrac);

          // STAGE B — per-cell update: read genome[], write genomeNext[].
          for (let y = 0; y < H; y++) {
            for (let x = 0; x < W; x++) {
              const i = y * W + x;
              let g = genome[i];

              // (1) SELECTION — local tournament vs one random neighbour.
              const j = neighbour(x, y);
              const fi = fit(g) / G;
              const fj = fit(genome[j]) / G;
              let pReplace = 0.5 + sel * (fj - fi);
              if (pReplace < 0) pReplace = 0; else if (pReplace > 1) pReplace = 1;
              if (Math.random() < pReplace) g = genome[j];

              // (2) HORIZONTAL TRANSFER — uniform crossover from a neighbour.
              if (Math.random() < hgt) {
                const h = genome[neighbour(x, y)];
                let tmask = 0;
                for (let b = 0; b < G; b++) if (Math.random() < 0.5) tmask |= (1 << b);
                g = (g & ~tmask) | (h & tmask);
              }

              // (3) DIVERGENCE — per-locus point mutation.
              if (mu > 0) {
                for (let b = 0; b < G; b++) if (Math.random() < mu) g ^= (1 << b);
              }

              genomeNext[i] = g & 0xFFFF;
            }
          }
          const t = genome; genome = genomeNext; genomeNext = t;
        }

        // Recompute consensus + field once from the final buffer.
        rebuildCore(coreFrac);
        recomputeField();
        generation += subs;
      },

      render(pixels) {
        const fg0 = 230, fg1 = 224, fg2 = 208;   // bone-cream paletteFg
        for (let i = 0; i < N; i++) {
          const g = genome[i];
          // (1) Genome hue — integer hash → even spread; identical genomes
          //     share an exact colour (clades = colour patches).
          const hue8 = (Math.imul(g, 2654435761) >>> 24) & 0xFF;  // 0..255
          // 6-segment HSV→RGB ramp at S≈0.7, V≈0.82 (no trig).
          const region = (hue8 * 6) / 256;       // 0 .. 5.976 (hue8 ≤ 255)
          const seg = region | 0;                // 0..5 (max reachable seg is 5)
          const f = region - seg;                // 0..1
          const vMax = 209;                      // 0.82 * 255
          const vMin = 63;                       // vMax * (1 - 0.7)
          const span = vMax - vMin;              // 146
          const up = vMin + span * f;
          const down = vMax - span * f;
          let baseR, baseG, baseB;
          switch (seg) {
            case 0:  baseR = vMax; baseG = up;   baseB = vMin; break;
            case 1:  baseR = down; baseG = vMax; baseB = vMin; break;
            case 2:  baseR = vMin; baseG = vMax; baseB = up;   break;
            case 3:  baseR = vMin; baseG = down; baseB = vMax; break;
            case 4:  baseR = up;   baseG = vMin; baseB = vMax; break;
            default: baseR = vMax; baseG = vMin; baseB = down; break;  // seg 5 (max)
          }
          // (2) LUCA-core glow toward bone-cream by w = coreField²; only
          //     genuine core members light up.
          let w = coreField[i]; w = w * w;
          const r  = (baseR + (fg0 - baseR) * w) | 0;
          const gg = (baseG + (fg1 - baseG) * w) | 0;
          const b  = (baseB + (fg2 - baseB) * w) | 0;
          const p = i * 4;
          pixels[p] = r; pixels[p + 1] = gg; pixels[p + 2] = b; pixels[p + 3] = 255;
        }
      },

      // SEM height = coreField — LUCA rises as a plateau, clades as pits,
      // a dissolved core as a flat floor.
      renderHeight(out) {
        for (let i = 0; i < N; i++) out[i] = coreField[i];
      },

      sprites() { return []; },

      paint(gx, gy, radius, mode) {
        // draw: nucleate a LUCA patch (stamp the consensus genome, or the
        //   environmental optimum if no core has formed yet).
        // erase: inject a divergent invading clade (fresh random genomes).
        const stamp = coreMask !== 0 ? coreValue : envOptimum;
        for (let dy = -radius; dy <= radius; dy++) {
          for (let dx = -radius; dx <= radius; dx++) {
            if (dx * dx + dy * dy > radius * radius) continue;
            const x = ((gx + dx) % W + W) % W;
            const y = ((gy + dy) % H + H) % H;
            const i = y * W + x;
            if (mode === "erase") genome[i] = (Math.random() * 65536) | 0;
            else                  genome[i] = stamp & 0xFFFF;
          }
        }
      },

      population() {
        // Cheap distinct-genome estimate on a stride sample.
        const seen = new Set();
        for (let i = 0; i < N; i += 7) seen.add(genome[i]);
        return `core ${coreCount}/16 · ${seen.size} lineages`;
      },

      generation() { return generation; },
    };
  }

  CA.RULES.luca = make;
})();
