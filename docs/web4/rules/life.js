// Digital life — Stage XIII of the abiogenesis pipeline.  JS port of
// cellauto/rules/abiogenesis/life_vm.py + stage_life.py — the v5.0 "life
// itself" engine.
//
// After Stage XII distils LUCA (the *recipe* for life), Stage XIII populates
// the grid with discrete organisms whose behaviour is not a probability table
// but an *executing program*.  Every organism carries a genome: a tape of
// opcodes for a tiny virtual CPU.  The CPU steps instruction-by-instruction,
// and each instruction is the organism doing something — ingesting substrate,
// excreting waste, moving, comparing, copying, dividing.  The genome IS the
// phenotype.
//
// Tierra/Avida-derived (Ray 1991; Ofria & Wilke 2004): instruction-tape
// genomes competing for a shared substrate, with private per-organism memory
// and an energy economy (every instruction costs energy; INGEST replenishes
// it).  Mutation at copy time (Eigen 1971 per-digit error model) supplies the
// heritable variation, so distinct lineages diverge from the founder ancestor.
//
// JS sizing (PRD §F6): a smaller world than the Python build — ~200 founders
// on a 60×60 grid — so the per-organism virtual-CPU loop stays inside one
// animation frame in the browser.
(function () {
  "use strict";
  window.CA = window.CA || { RULES: {} };

  const W = 60;
  const H = 60;
  const N = W * H;

  // ── Instruction set — 20 opcodes, SAME order as life_vm.py OPCODES ───────
  const OPCODES = [
    "NOP",    // 0  — no-op / template marker
    "INC",    // 1  — reg[head] += 1
    "DEC",    // 2  — reg[head] -= 1
    "ADD",    // 3  — reg[0] = reg[1] + reg[2]
    "SUB",    // 4  — reg[0] = reg[1] - reg[2]
    "LOAD",   // 5  — reg[head] = next genome byte (immediate literal)
    "SWAP",   // 6  — swap reg[0] and reg[head]
    "HEAD",   // 7  — advance the register head
    "JUMP",   // 8  — ip = reg[head] mod genome length
    "JZ",     // 9  — if flag == 0: same jump as JUMP
    "CMP",    // 10 — flag = sign(reg[0] - reg[1])
    "SENSE",  // 11 — reg[head] = local substrate level (0..255)
    "INGEST", // 12 — consume substrate at this cell → energy
    "EXCRETE",// 13 — release waste into this cell
    "MOVE",   // 14 — step to the faced neighbour if empty (extra energy)
    "TURN",   // 15 — facing = (facing + 1 + reg[head]) mod 8
    "DIVIDE", // 16 — reproduce if energy ≥ e_div
    "COPY",   // 17 — advance the self-read copy head
    "RAND",   // 18 — reg[head] = rng byte 0..255
    "LOOP",   // 19 — reset ip to 0
  ];
  const OP = {};
  for (let i = 0; i < OPCODES.length; i++) OP[OPCODES[i]] = i;
  const N_OPCODES = OPCODES.length;   // 20
  const N_REGISTERS = 4;
  const GENOME_CAP = 512;

  // The canonical viable ancestor (Tierra's "ancestor 0080" analogue) — a
  // hand-written genome that actually lives: senses, eats, periodically
  // excretes, turns + moves to find fresh food, and divides when rich.
  const ANCESTOR_GENOME = [
    OP["SENSE"], OP["INGEST"], OP["INGEST"], OP["CMP"], OP["NOP"],
    OP["EXCRETE"], OP["INGEST"], OP["DIVIDE"], OP["TURN"], OP["MOVE"],
    OP["INGEST"], OP["DIVIDE"], OP["LOOP"],
  ];

  // Moore-neighbourhood unit directions, indexed by facing (0..7), clockwise
  // from east — matches stage_life._DIRS.
  const DIRS = [
    [1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0], [-1, -1], [0, -1], [1, -1],
  ];

  // Eigen quasispecies error threshold ε_c = ln(σ)/L (σ = e ⇒ ≈ 1/L).
  function errorThreshold(genomeLen) {
    const L = Math.max(1, genomeLen | 0);
    return 1 / L;   // ln(e) / L
  }

  function genomeDistance(a, b) {
    const n = Math.min(a.length, b.length);
    let mism = 0;
    for (let i = 0; i < n; i++) if (a[i] !== b[i]) mism++;
    return mism + Math.abs(a.length - b.length);
  }

  // --- Photoreal sprite atlas (baked offline, same PNGs the Python renderer
  //     uses).  Loaded async; the hi-res canvas path blits these instead of
  //     drawing pixel discs, so the browser matches the desktop look. ---
  const ATLAS = { ready: false, sheet: null, div: null, variants: 6, frames: 10, tile: 384 };
  (function loadAtlas() {
    try {
      fetch("assets/life/atlas.json")
        .then((r) => r.json())
        .then((m) => { ATLAS.variants = m.variants; ATLAS.frames = m.frames; ATLAS.tile = m.tile; })
        .catch(() => {});
      const s = new Image();
      s.onload = () => { ATLAS.sheet = s; if (ATLAS.div) ATLAS.ready = true; };
      s.src = "assets/life/cells.png";
      const d = new Image();
      d.onload = () => { ATLAS.div = d; if (ATLAS.sheet) ATLAS.ready = true; };
      d.src = "assets/life/cell_div.png";
    } catch (e) { /* no DOM (e.g. node smoke) — hi-res path simply stays inactive */ }
  })();

  function make() {
    // Three coupled grids + the live population.
    const substrate = new Float32Array(N);   // [0,1] — food
    const waste     = new Float32Array(N);    // [0,1] — toxic excretion
    const occupant  = new Int32Array(N);      // organism oid per cell, -1 empty
    let organisms   = new Map();              // oid → org
    let corpses     = [];                     // [x, y, stepsLeft]
    let nextOid     = 0;
    let generation  = 0;
    const founderGenome = ANCESTOR_GENOME.slice();
    const divRequests = [];
    // hi-res sprite render state (lazy)
    let hrFrame = 0;
    let floorCanvas = null;
    let floorImg = null;

    function seed() {
      // Substrate starts plentiful and uniform; waste empty.
      substrate.fill(0.7);
      waste.fill(0);
      occupant.fill(-1);
      organisms = new Map();
      corpses = [];
      nextOid = 0;
      generation = 0;

      const want = Math.min((this.params.population.value | 0), N);
      // Random scatter of founders into distinct empty cells.
      let placed = 0;
      let guard = want * 20;
      while (placed < want && guard-- > 0) {
        const c = (Math.random() * N) | 0;
        if (occupant[c] !== -1) continue;
        const x = c % W, y = (c / W) | 0;
        const oid = nextOid++;
        organisms.set(oid, {
          oid,
          genome: founderGenome.slice(),
          x, y,
          energy: this.params.initialEnergy.value,
          ip: 0,
          regs: [0, 0, 0, 0],
          head: 0,
          flag: 0,
          facing: (Math.random() * 8) | 0,
          copyHead: 0,
          age: 0,
          parent: null,
          lineage: oid,        // founders each start their own lineage
          nDivisions: 0,
          lastOp: 0,
        });
        occupant[c] = oid;
        placed++;
      }
    }

    // ── World protocol — what an executing organism does to the grid ──────
    function senseSubstrate(org) {
      return (substrate[org.y * W + org.x] * 255) & 0xFF;
    }
    function ingest(org, bite) {
      const i = org.y * W + org.x;
      const avail = substrate[i];
      const b = Math.min(bite, avail);
      substrate[i] = avail - b;
      return b;
    }
    function excrete(org, amount) {
      const i = org.y * W + org.x;
      waste[i] = Math.min(1, waste[i] + amount);
    }
    function move(org) {
      const d = DIRS[org.facing % 8];
      const nx = org.x + d[0], ny = org.y + d[1];
      if (nx < 0 || nx >= W || ny < 0 || ny >= H) return false;
      const ni = ny * W + nx;
      if (occupant[ni] !== -1) return false;
      occupant[org.y * W + org.x] = -1;
      occupant[ni] = org.oid;
      org.x = nx; org.y = ny;
      return true;
    }

    // ── Virtual CPU — run exactly ONE instruction of org's genome ─────────
    function executeOne(org, cfg) {
      org.age++;
      const g = org.genome;
      const n = g.length;
      if (n === 0) {
        org.energy -= cfg.instructionCost;
        return;
      }
      const op = g[org.ip % n];
      org.lastOp = op;
      // Advance ip first; JUMP/LOOP overwrite below.
      org.ip = (org.ip + 1) % n;
      // Base metabolic cost.
      org.energy -= cfg.instructionCost;
      const r = org.regs;

      switch (op) {
        case 0: break;                                          // NOP
        case 1: r[org.head] = (r[org.head] + 1) & 0xFF; break;  // INC
        case 2: r[org.head] = (r[org.head] - 1) & 0xFF; break;  // DEC
        case 3: r[0] = (r[1] + r[2]) & 0xFF; break;             // ADD
        case 4: r[0] = (r[1] - r[2]) & 0xFF; break;             // SUB
        case 5: {                                               // LOAD
          const literal = g[org.ip % n];
          r[org.head] = literal & 0xFF;
          org.ip = (org.ip + 1) % n;
          break;
        }
        case 6: { const t = r[0]; r[0] = r[org.head]; r[org.head] = t; break; } // SWAP
        case 7: org.head = (org.head + 1) % N_REGISTERS; break; // HEAD
        case 8: org.ip = r[org.head] % n; break;                // JUMP
        case 9: if (org.flag === 0) org.ip = r[org.head] % n; break; // JZ
        case 10: {                                              // CMP
          const diff = r[0] - r[1];
          org.flag = (diff > 0 ? 1 : 0) - (diff < 0 ? 1 : 0);
          break;
        }
        case 11: r[org.head] = senseSubstrate(org); break;      // SENSE
        case 12: org.energy += ingest(org, cfg.ingestBite) * cfg.ingestGain; break; // INGEST
        case 13: excrete(org, cfg.wasteExcretion); org.energy -= cfg.excreteCost; break; // EXCRETE
        case 14: if (move(org)) org.energy -= cfg.moveCost; break; // MOVE
        case 15: org.facing = (org.facing + 1 + r[org.head]) % 8; break; // TURN
        case 16: if (org.energy >= cfg.eDiv) divRequests.push(org.oid); break; // DIVIDE
        case 17: org.copyHead = (org.copyHead + 1) % n; break;  // COPY
        case 18: r[org.head] = (Math.random() * 256) | 0; break; // RAND
        case 19: org.ip = 0; break;                             // LOOP
      }
    }

    function mutateGenome(genome, epsilon) {
      const out = new Array(genome.length);
      for (let i = 0; i < genome.length; i++) {
        out[i] = (Math.random() < epsilon) ? ((Math.random() * N_OPCODES) | 0) : genome[i];
      }
      return out;
    }

    function divisionSite(parent) {
      const empties = [];
      for (const d of DIRS) {
        const nx = parent.x + d[0], ny = parent.y + d[1];
        if (nx >= 0 && nx < W && ny >= 0 && ny < H && occupant[ny * W + nx] === -1) {
          empties.push([nx, ny]);
        }
      }
      if (!empties.length) return null;
      return empties[(Math.random() * empties.length) | 0];
    }

    function divide(parent, cfg) {
      const site = divisionSite(parent);
      if (!site) return;
      const [nx, ny] = site;
      let daughterGenome = mutateGenome(parent.genome, cfg.mutationRate);
      if (daughterGenome.length > GENOME_CAP) daughterGenome = daughterGenome.slice(0, GENOME_CAP);
      const oid = nextOid++;
      parent.energy *= 0.5;
      parent.nDivisions++;
      const daughter = {
        oid,
        genome: daughterGenome,
        x: nx, y: ny,
        energy: parent.energy,    // 50/50 split (parent already halved)
        ip: 0,
        regs: [0, 0, 0, 0],
        head: 0,
        flag: 0,
        facing: (Math.random() * 8) | 0,
        copyHead: 0,
        age: 0,
        parent: parent.oid,
        lineage: parent.lineage,
        nDivisions: 0,
        lastOp: 0,
      };
      organisms.set(oid, daughter);
      occupant[ny * W + nx] = oid;
    }

    function cull(cfg) {
      const dead = [];
      for (const org of organisms.values()) {
        if (org.energy <= 0) { dead.push(org); continue; }
        const w = waste[org.y * W + org.x];
        if (w > 0 && Math.random() < cfg.wasteToxicity * w) dead.push(org);
      }
      for (const org of dead) {
        organisms.delete(org.oid);
        occupant[org.y * W + org.x] = -1;
        corpses.push([org.x, org.y, cfg.decaySteps]);
      }
    }

    function relaxEnvironment(cfg) {
      // Linear substrate regen toward S_max.
      const regen = cfg.substrateRegen, smax = cfg.substrateMax;
      for (let i = 0; i < N; i++) {
        const s = substrate[i] + regen * (smax - substrate[i]);
        substrate[i] = s < 0 ? 0 : (s > smax ? smax : s);
      }
      // Waste relaxes toward zero.
      const decay = cfg.wasteDecay;
      for (let i = 0; i < N; i++) waste[i] *= decay;
      // Corpses dribble body mass back into the substrate.
      if (corpses.length) {
        const give = smax / Math.max(1, cfg.decaySteps) * 0.5;
        const still = [];
        for (const c of corpses) {
          const i = c[1] * W + c[0];
          substrate[i] = Math.min(smax, substrate[i] + give);
          c[2] -= 1;
          if (c[2] > 0) still.push(c);
        }
        corpses = still;
      }
    }

    function cfgFromParams(self) {
      return {
        instructionCost: 1.0,
        ingestGain:      28.0,
        moveCost:        2.0,
        excreteCost:     0.5,
        eDiv:            120.0,
        ingestBite:      0.35,
        wasteExcretion:  0.05,
        wasteDecay:      0.96,
        wasteToxicity:   0.015,
        decaySteps:      10,
        substrateMax:    1.0,
        substrateRegen:  self.params.substrateRegen.value,
        mutationRate:    self.params.mutationRate.value,
        maxPopulation:   self.params.maxPopulation.value | 0,
      };
    }

    function energyFrac(org) {
      const f = org.energy / 120.0;   // e_div
      return f < 0 ? 0 : (f > 1 ? 1 : f);
    }

    return {
      id: "life",
      label: "Digital life · Tierra/Avida organisms",
      formula: "Each organism = a 20-opcode genome run by a virtual CPU; metabolism + ε-mutation + selection.",
      shortCaption: "STAGE XIII · DIGITAL LIFE",
      whatThisIs: "Life itself, as executing code. Each organism carries a genome — a tape of CPU " +
                  "instructions — and the genome IS the phenotype: it senses, eats substrate, " +
                  "excretes waste, moves, and divides with copying errors. Selection is implicit; " +
                  "efficient lineages out-reproduce the rest and diverge from the founder ancestor.",
      aboutStage: "The building block here is the open-ended evolving lineage. Following Tierra " +
                  "(Ray, 1991) and Avida (Ofria & Wilke, 2004), every organism is a tiny program on " +
                  "an instruction tape competing for shared substrate; each executed instruction costs " +
                  "energy, INGEST repays it, and DIVIDE copies the genome with per-instruction error ε " +
                  "(Eigen's 1971 quasispecies model). Raise ε past the error threshold ≈ 1/L and the " +
                  "master sequence melts — the error catastrophe. This is where the engine stops " +
                  "modelling the precursors of life and starts running life as an algorithm " +
                  "(Channon, 2003).",
      paletteBg: [10, 14, 22],
      paletteFg: [230, 224, 208],
      width: W,
      height: H,
      hiResScale: 12, // main.js sizes the canvas to grid×scale and calls renderHiRes

      params: {
        population:     { label: "founder population", min: 20,  max: 600, step: 10,   value: 200  },
        mutationRate:   { label: "ε — mutation rate",  min: 0.0, max: 0.20, step: 0.005, value: 0.02 },
        substrateRegen: { label: "substrate regen",    min: 0.0, max: 0.20, step: 0.005, value: 0.05 },
        maxPopulation:  { label: "population cap",     min: 200, max: 2000, step: 50,   value: 1400 },
        initialEnergy:  { label: "founder energy",     min: 20,  max: 120, step: 5,     value: 60   },
      },

      controlConsequence: {
        population:     "How many founder organisms seed the grid. Sparse: lineages may starve out before they catch. Dense: instant competition for substrate.",
        mutationRate:   "Eigen's ε, the per-instruction copy error. Low: lineages stay near the ancestor and persist. Past ≈ 1/L (the error threshold) the genome melts into noise — the error catastrophe.",
        substrateRegen: "How fast food regrows toward saturation. Raise it: a rich world that sustains a big population. Lower it: famine, boom-bust crashes, sharper selection.",
        maxPopulation:  "Hard ceiling on living organisms — divisions stop once it's hit. Keeps the per-frame CPU cost bounded in the browser.",
        initialEnergy:  "Energy each founder starts with. Higher: founders survive long enough to find food and divide. Lower: a harsher start, many founders die before their first meal.",
      },

      randomize() { seed.call(this); },
      clear() {
        substrate.fill(0); waste.fill(0); occupant.fill(-1);
        organisms = new Map(); corpses = []; nextOid = 0; generation = 0;
      },
      reset() { seed.call(this); },

      step() {
        const cfg = cfgFromParams(this);
        divRequests.length = 0;

        // 1. Execute one instruction per organism, in random order.
        const order = Array.from(organisms.keys());
        for (let i = order.length - 1; i > 0; i--) {
          const j = (Math.random() * (i + 1)) | 0;
          const t = order[i]; order[i] = order[j]; order[j] = t;
        }
        const eCap = cfg.eDiv * 5.0;   // bound energy (and disc radius)
        for (const oid of order) {
          const org = organisms.get(oid);
          if (!org) continue;
          executeOne(org, cfg);
          if (org.energy > eCap) org.energy = eCap;
        }

        // 2. Resolve divisions.
        for (const oid of divRequests) {
          if (organisms.size >= cfg.maxPopulation) break;
          const parent = organisms.get(oid);
          if (!parent || parent.energy < cfg.eDiv) continue;
          divide(parent, cfg);
        }

        // 3. Deaths: starvation + waste toxicity.
        cull(cfg);

        // 4. Environment relaxation.
        relaxEnvironment(cfg);

        generation++;
      },

      render(pixels) {
        const haveLut = (typeof VIRIDIS_LUT !== "undefined");
        const lutLen = haveLut ? (VIRIDIS_LUT.length / 3) : 0;
        // Background: substrate under viridis, darkened where waste pools.
        for (let i = 0; i < N; i++) {
          const s = substrate[i];
          let r, g, b;
          if (haveLut) {
            let idx = (s * (lutLen - 1)) | 0;
            if (idx < 0) idx = 0; else if (idx >= lutLen) idx = lutLen - 1;
            idx *= 3;
            r = VIRIDIS_LUT[idx]; g = VIRIDIS_LUT[idx+1]; b = VIRIDIS_LUT[idx+2];
          } else {
            // Fallback teal ramp if the LUT script wasn't loaded.
            r = (10 + 40 * s) | 0; g = (40 + 160 * s) | 0; b = (60 + 90 * s) | 0;
          }
          const dark = 1 - 0.55 * (waste[i] < 1 ? waste[i] : 1);
          const p = i * 4;
          pixels[p]   = (r * dark) | 0;
          pixels[p+1] = (g * dark) | 0;
          pixels[p+2] = (b * dark) | 0;
          pixels[p+3] = 255;
        }
        // Organisms as energy-coloured discs with a white membrane ring.
        for (const org of organisms.values()) {
          const frac = energyFrac(org);
          const rad = Math.round(1 + 2 * frac);   // bounded radius for a 60×60 grid
          const cr = (40 + 150 * frac) | 0;
          const cg = (120 + 110 * frac) | 0;
          const cb = (120 + 60 * (1 - frac)) | 0;
          const r2 = rad * rad;
          const rin2 = (rad - 1) * (rad - 1);
          for (let dy = -rad; dy <= rad; dy++) {
            const y = org.y + dy;
            if (y < 0 || y >= H) continue;
            for (let dx = -rad; dx <= rad; dx++) {
              const x = org.x + dx;
              if (x < 0 || x >= W) continue;
              const d2 = dx*dx + dy*dy;
              if (d2 > r2) continue;
              const p = (y * W + x) * 4;
              if (rad >= 2 && d2 >= rin2) {
                pixels[p] = 235; pixels[p+1] = 235; pixels[p+2] = 235;   // membrane ring
              } else {
                pixels[p] = cr; pixels[p+1] = cg; pixels[p+2] = cb;
              }
              pixels[p+3] = 255;
            }
          }
        }
      },

      // Hi-res photoreal path: draw a smooth sepia FOOD floor, then blit the
      // baked translucent-cell sprites (the same atlas the Python renderer
      // uses) at each organism's position — depth-sorted, energy-scaled,
      // flipbook-cycled, with the one teal dividing cell. This is what makes
      // the browser match the desktop look instead of pixel discs.
      renderHiRes(ctx, CW, CH) {
        hrFrame++;
        // --- sepia food floor (60×60 sepia buffer scaled up smoothly) ---
        if (!floorCanvas) {
          floorCanvas = document.createElement("canvas");
          floorCanvas.width = W;
          floorCanvas.height = H;
          floorImg = floorCanvas.getContext("2d").createImageData(W, H);
        }
        const d = floorImg.data;
        for (let i = 0; i < N; i++) {
          const s = substrate[i];
          const w = waste[i] < 1 ? waste[i] : 1;
          const lit = 0.32 + 0.68 * s; // dark where food has been eaten
          const p = i * 4;
          d[p] = (150 * lit) | 0;
          d[p + 1] = (120 * lit) | 0;
          d[p + 2] = (84 * lit * (1 - 0.3 * w)) | 0;
          d[p + 3] = 255;
        }
        floorCanvas.getContext("2d").putImageData(floorImg, 0, 0);
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = "high";
        ctx.drawImage(floorCanvas, 0, 0, CW, CH);

        const denom = (v) => (v > 1 ? v : 1);
        if (ATLAS.ready) {
          const tile = ATLAS.tile, V = ATLAS.variants, F = ATLAS.frames;
          let divOid = -1, best = -Infinity;
          for (const o of organisms.values()) {
            const sc = o.nDivisions * 1e6 + o.energy;
            if (sc > best) { best = sc; divOid = o.oid; }
          }
          const list = Array.from(organisms.values()).sort((a, b) => a.y - b.y);
          for (const org of list) {
            const frac = energyFrac(org);
            const depth = org.y / denom(H - 1);
            const cx = (0.05 + 0.90 * (org.x / denom(W - 1))) * CW;
            const cy = (0.06 + 0.88 * depth) * CH;
            const dw = CH * 0.072 * (0.7 + 0.5 * depth) * (0.82 + 0.4 * frac);
            const fidx = (((hrFrame * 0.3 + org.oid * 3) | 0) % F + F) % F;
            const isdiv = org.oid === divOid && frac > 0.5;
            const img = isdiv ? ATLAS.div : ATLAS.sheet;
            const sy = isdiv ? 0 : (org.oid % V) * tile;
            const sx = fidx * tile;
            const ang = ((org.facing * 45) + 4 * Math.sin(hrFrame * 0.05 + org.oid)) * Math.PI / 180;
            ctx.save();
            ctx.translate(cx, cy);
            ctx.rotate(ang);
            ctx.drawImage(img, sx, sy, tile, tile, -dw / 2, -dw / 2, dw, dw);
            ctx.restore();
          }
        } else {
          // fallback discs while the atlas PNGs load
          for (const org of organisms.values()) {
            const frac = energyFrac(org);
            const cx = (org.x / denom(W - 1)) * CW;
            const cy = (org.y / denom(H - 1)) * CH;
            ctx.fillStyle = "rgba(222,210,178,0.92)";
            ctx.beginPath();
            ctx.arc(cx, cy, CH * 0.018 * (0.7 + frac), 0, 6.2832);
            ctx.fill();
          }
        }
        // instrument chrome: badge + scale bar
        ctx.fillStyle = "rgba(20,15,10,0.5)";
        ctx.fillRect(CW - 372, 14, 358, 30);
        ctx.fillStyle = "rgba(228,212,172,0.96)";
        ctx.font = ((CH * 0.022) | 0) + "px monospace";
        ctx.fillText("LIVE SEM FEED · STAGE XIII · DIGITAL LIFE", CW - 360, 35);
        ctx.strokeStyle = "rgba(228,212,172,0.9)";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(CW / 2 - 75, CH - 28);
        ctx.lineTo(CW / 2 + 75, CH - 28);
        ctx.stroke();
      },

      // SEM height: organisms stand up as energy-scaled mounds on a low
      // substrate plain; waste digs the substrate down a touch.
      renderHeight(out) {
        for (let i = 0; i < N; i++) {
          out[i] = 0.15 * substrate[i] - 0.05 * waste[i];
        }
        for (const org of organisms.values()) {
          const frac = energyFrac(org);
          const rad = Math.round(1 + 2 * frac);
          const r2 = rad * rad;
          for (let dy = -rad; dy <= rad; dy++) {
            const y = org.y + dy;
            if (y < 0 || y >= H) continue;
            for (let dx = -rad; dx <= rad; dx++) {
              const x = org.x + dx;
              if (x < 0 || x >= W) continue;
              if (dx*dx + dy*dy > r2) continue;
              const v = 0.5 + 0.5 * frac;
              const i = y * W + x;
              if (v > out[i]) out[i] = v;
            }
          }
        }
      },

      // v4.1 sprite layer — each organism emits a "digital-organism" sprite.
      // With sprite mode ON they pick up a translucent body wall + gut + a
      // genome strip (the Brachionus internal-anatomy look, PRD §F6 / V10).
      // The painters are registered once on window.SPRITES.PAINTERS below.
      sprites() {
        const out = [];
        for (const org of organisms.values()) {
          const frac = energyFrac(org);
          out.push({
            kind: "digital-organism",
            x: org.x + 0.5,
            y: org.y + 0.5,
            scale: 1.6 + 1.6 * frac,
            energy: frac,
            ip: org.ip,
            lastOp: org.lastOp,
            head: org.head,
            facing: org.facing,
            nDivisions: org.nDivisions,
            // a short slice of the genome for the instruction strip
            strip: org.genome.slice(org.ip % org.genome.length).concat(org.genome).slice(0, 12),
            genomeLen: org.genome.length,
          });
        }
        return out;
      },

      paint(gx, gy, radius, mode) {
        for (let dy = -radius; dy <= radius; dy++) {
          for (let dx = -radius; dx <= radius; dx++) {
            if (dx*dx + dy*dy > radius*radius) continue;
            const x = gx + dx, y = gy + dy;
            if (x < 0 || x >= W || y < 0 || y >= H) continue;
            const i = y * W + x;
            if (mode === "erase") {
              // Remove any organism here and clear the cell back to bare substrate.
              const oid = occupant[i];
              if (oid !== -1) { organisms.delete(oid); occupant[i] = -1; }
              waste[i] = 0;
            } else {
              // Drop a fresh founder if the cell is empty.
              if (occupant[i] === -1) {
                const oid = nextOid++;
                organisms.set(oid, {
                  oid, genome: founderGenome.slice(), x, y,
                  energy: this.params.initialEnergy.value,
                  ip: 0, regs: [0, 0, 0, 0], head: 0, flag: 0,
                  facing: (Math.random() * 8) | 0, copyHead: 0, age: 0,
                  parent: null, lineage: oid, nDivisions: 0, lastOp: 0,
                });
                occupant[i] = oid;
              }
            }
          }
        }
      },

      population() {
        const orgs = Array.from(organisms.values());
        const n = orgs.length;
        if (!n) return "0 organisms · extinct";
        let eSum = 0, lenSum = 0, divSum = 0;
        const lineages = new Set();
        for (const o of orgs) {
          eSum += o.energy;
          lenSum += o.genome.length;
          divSum += genomeDistance(o.genome, founderGenome);
          lineages.add(o.lineage);
        }
        const avgE = Math.round(eSum / n);
        const divergence = (divSum / n).toFixed(1);
        const eps = this.params.mutationRate.value;
        const epsC = errorThreshold(founderGenome.length);
        return `${n} organisms · ${lineages.size} lineages · ⌀E ${avgE} · ` +
               `divergence ${divergence} · ε ${eps.toFixed(3)}/ε_c ${epsC.toFixed(3)}`;
      },

      generation() { return generation; },
    };
  }

  CA.RULES.life = make;

  // ── v4.1 sprite painter — Brachionus-style internal anatomy ─────────────
  // Registered only if the sprite library is present and doesn't already
  // claim the "digital-organism" kind.  Outline-and-translucent style, in
  // keeping with the v4.1.1 calm-overlay convention (the SEM substrate stays
  // visible through the body wall).  Skipping this leaves the disc render
  // intact; it never touches the other rules' painters.
  if (window.SPRITES && window.SPRITES.PAINTERS &&
      !window.SPRITES.PAINTERS["digital-organism"]) {
    function tint(pal, t) {
      if (!pal || !pal.length) return "rgb(230,224,208)";
      const n = pal.length / 3;
      const i = Math.min(n - 1, Math.max(0, (t * n) | 0)) * 3;
      return "rgb(" + pal[i] + "," + pal[i+1] + "," + pal[i+2] + ")";
    }
    window.SPRITES.PAINTERS["digital-organism"] = function (ctx, s, pal) {
      const r = s.scale * 1.0;
      // Translucent body wall — faint interior tint, hairline ring (V9/V10).
      ctx.fillStyle = tint(pal, 0.35 + 0.35 * (s.energy || 0));
      const prev = ctx.globalAlpha;
      ctx.globalAlpha = prev * 0.35;
      ctx.beginPath();
      ctx.ellipse(s.x, s.y, r, r * 0.82, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalAlpha = prev;
      // Hairline wall.
      ctx.strokeStyle = tint(pal, 0.92);
      ctx.lineWidth = Math.max(0.3, r * 0.07);
      ctx.beginPath();
      ctx.ellipse(s.x, s.y, r, r * 0.82, 0, 0, Math.PI * 2);
      ctx.stroke();
      // Gut compartment — small lower-right lobe.
      ctx.fillStyle = tint(pal, 0.20);
      ctx.globalAlpha = prev * 0.6;
      ctx.beginPath();
      ctx.arc(s.x + r * 0.30, s.y + r * 0.25, Math.max(0.4, r * 0.30), 0, Math.PI * 2);
      ctx.fill();
      ctx.globalAlpha = prev;
      // Genome instruction strip across the top; current instruction teal.
      const strip = s.strip || [];
      const nShow = Math.min(strip.length, 8);
      if (nShow > 0) {
        const dot = Math.max(0.3, r * 0.10);
        const spacing = (2 * r * 0.7) / Math.max(1, nShow);
        const startx = s.x - (nShow * spacing) / 2;
        const sy = s.y - r * 0.6;
        for (let i = 0; i < nShow; i++) {
          if (i === 0) {
            ctx.fillStyle = "rgb(60,220,200)";   // the instruction executing now
          } else {
            const g = (120 + 110 * (strip[i] / 19)) | 0;
            ctx.fillStyle = "rgb(" + g + "," + (g - 20) + ",90)";
          }
          ctx.beginPath();
          ctx.arc(startx + i * spacing, sy, dot, 0, Math.PI * 2);
          ctx.fill();
        }
      }
      // Division glow — a recently-divided, energy-rich organism flashes teal.
      if (s.nDivisions > 0 && (s.energy || 0) >= 0.75) {
        ctx.strokeStyle = "rgb(33,201,180)";
        ctx.lineWidth = Math.max(0.3, r * 0.06);
        ctx.beginPath();
        ctx.arc(s.x, s.y, r * 0.55, 0, Math.PI * 2);
        ctx.stroke();
      }
    };
  }
})();
