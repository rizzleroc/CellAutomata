// Stage 0 — Miller–Urey spark-discharge synthesis (1953), live.
//
// This is the *authentic* experiment, not a generic Brownian field: a reducing
// atmosphere (CH₄, NH₃, H₂, H₂O) drifts in the spark flask over a boiling water
// pool. A tungsten spark fires across the gap; molecules caught in the plasma
// corridor dissociate and recombine into the real intermediates — hydrogen
// cyanide (HCN) and formaldehyde/aldehydes (CH₂O) — which then undergo Strecker
// synthesis into amino acids. The amino acids are heavier, rain down, and are
// absorbed into the pool, which darkens from clear water into tea-coloured
// "primordial soup". The whole water cycle runs: the pool boils → vapour rises
// → it condenses at the cool top → droplets fall back. Everything you see is the
// mechanism Miller & Urey actually reported (Miller 1953; Strecker 1850; the
// 2008 re-analysis of the volcanic-spark variant, Johnson et al.).
//
// Rendering: hiRes + renderPhotoreal paints this cross-section directly (the SEM
// shader can't show water boiling or a spark arc). renderHeight is retained so
// the SEM depth path + the headless smoke test still have a valid height field.
(function () {
  "use strict";
  window.CA = window.CA || { RULES: {} };

  const W = 180, H = 180;             // SEM height-field resolution
  const POOL_Y = 0.80;               // water surface (normalised sim y; 0 top, 1 bottom)
  const WALL_L = 0.06, WALL_R = 0.94, ROOF = 0.05;

  // Molecule species. Reactants are the reducing atmosphere; HCN/CHO are the
  // spark-made intermediates; AMINO is the product; INERT is the non-reducing
  // ballast (CO₂/N₂) that lowers yield in a weakly-reducing atmosphere.
  const CH4 = 0, NH3 = 1, H2 = 2, H2O = 3, INERT = 4, HCN = 5, CHO = 6, AMINO = 7;
  const COLOR = {
    [CH4]:   [120, 214, 198],   // teal
    [NH3]:   [120, 156, 232],   // periwinkle
    [H2]:    [206, 220, 232],   // pale H₂
    [H2O]:   [ 96, 200, 222],   // water cyan
    [INERT]: [122, 120, 132],   // grey ballast
    [HCN]:   [205, 132, 232],   // magenta intermediate
    [CHO]:   [232, 178, 96],    // amber aldehyde
    [AMINO]: [253, 214, 92],    // gold — the prize
  };
  const LABEL = { [CH4]:"CH₄", [NH3]:"NH₃", [H2]:"H₂", [H2O]:"H₂O",
                  [INERT]:"CO₂", [HCN]:"HCN", [CHO]:"CH₂O", [AMINO]:"amino acid" };
  // Vertical buoyancy bias (negative rises). Light gases rise; products fall.
  const BUOY = { [CH4]:-0.9, [NH3]:-0.8, [H2]:-1.6, [H2O]:-0.7, [INERT]:-0.2, [HCN]:-0.1, [CHO]:0.1, [AMINO]:1.3 };
  const isReactant = (t) => t === CH4 || t === NH3 || t === H2 || t === H2O;

  const ORG_TARGET = 220;            // amino acids absorbed → fully dark soup

  function make() {
    let mols = [];                   // {x,y,vx,vy,t}
    const drops = [];                // condensate droplets falling back to the pool
    const splashes = [];             // brief ring where an amino acid hits the pool
    const flashes = [];              // brief reaction sparks at conversion sites
    const bubbles = [];              // boiling bubbles in the pool
    let bolt = null;                 // cached jagged spark path (sim coords)
    let sparkFlash = 0;              // 0..1 decaying glow after a strike
    let sparkCounter = 0;            // steps since last strike
    let strikes = 0, synth = 0;      // cumulative strikes, amino acids synthesised
    let organics = 0;                // amino acids absorbed into the pool
    let progress = 0;                // organics / ORG_TARGET, clamped → pool darkening
    let generation = 0;
    let rt = 0;                      // cosmetic render time (shimmer), advanced in render

    const rnd = Math.random;
    const clampX = (x) => x < WALL_L ? WALL_L : x > WALL_R ? WALL_R : x;

    function newMol(t, x, y) {
      return { t, x: x ?? (WALL_L + rnd() * (WALL_R - WALL_L)),
                  y: y ?? (ROOF + rnd() * (POOL_Y - ROOF - 0.02)),
                  vx: (rnd() - 0.5) * 0.004, vy: (rnd() - 0.5) * 0.004 };
    }
    // Pick a reactant species honouring the reducing fraction (else inert ballast).
    function reactantType() {
      const red = params.reducing.value;
      if (rnd() > red) return INERT;
      const r = rnd();
      return r < 0.34 ? CH4 : r < 0.62 ? NH3 : r < 0.82 ? H2 : H2O;
    }
    function spawnFromPool(t) {       // rises off the boiling surface
      mols.push(newMol(t ?? reactantType(), WALL_L + rnd() * (WALL_R - WALL_L), POOL_Y - 0.015));
    }

    function fill(n) {
      mols.length = 0;
      for (let i = 0; i < n; i++) mols.push(newMol(reactantType()));
    }
    function ensureBubbles(n) {
      while (bubbles.length < n) bubbles.push({ x: WALL_L + rnd() * (WALL_R - WALL_L), y: 1, r: 0, v: 0 });
      bubbles.length = n;
    }

    function buildBolt() {
      const ax = 0.435, ay = 0.155, bx = 0.565, by = 0.155;   // electrode tips
      const pts = [[ax, ay]];
      const SEG = 7;
      for (let i = 1; i < SEG; i++) {
        const t = i / SEG;
        const jx = (rnd() - 0.5) * 0.05 * Math.sin(t * Math.PI);
        const jy = (rnd() - 0.5) * 0.06 * Math.sin(t * Math.PI);
        pts.push([ax + (bx - ax) * t + jx, ay + (by - ay) * t + 0.04 * Math.sin(t * Math.PI) + jy]);
      }
      pts.push([bx, by]);
      bolt = pts;
    }

    function strike() {
      strikes++; sparkFlash = 1; buildBolt();
      const yield_ = 0.18 + params.reducing.value * 0.5;     // reducing atmosphere → higher yield
      // Plasma corridor: the gap and the plume reaching down from it.
      for (const m of mols) {
        if (m.y > 0.52 || m.x < 0.34 || m.x > 0.66) continue;
        if (!isReactant(m.t) || rnd() > yield_) continue;
        const r = rnd();
        if (r < 0.46 && (m.t === CH4 || m.t === NH3 || m.t === H2)) m.t = HCN;     // → hydrogen cyanide
        else if (r < 0.84 && (m.t === CH4 || m.t === H2O)) m.t = CHO;             // → aldehyde
        else if (params.reducing.value > 0.7) { m.t = AMINO; synth++; }           // rare direct hit
        else m.t = HCN;
        m.vy += 0.01;                                          // kicked downward out of the plume
        flashes.push({ x: m.x, y: m.y, life: 1 });
      }
      sparkCounter = 0;
    }

    // Strecker synthesis: an HCN and an aldehyde meeting → an amino acid.
    function strecker() {
      const hcn = [], cho = [];
      for (let i = 0; i < mols.length; i++) {
        if (mols[i].t === HCN) hcn.push(i); else if (mols[i].t === CHO) cho.push(i);
      }
      let tries = Math.min(8, hcn.length);
      while (tries-- > 0 && cho.length) {
        const a = mols[hcn[(rnd() * hcn.length) | 0]];
        let best = -1, bd = 0.05 * 0.05;
        for (let k = 0; k < cho.length; k++) {
          const b = mols[cho[k]];
          const dx = a.x - b.x, dy = a.y - b.y, d = dx * dx + dy * dy;
          if (d < bd) { bd = d; best = k; }
        }
        if (best >= 0) {
          const b = mols[cho[best]];
          a.t = AMINO; a.x = (a.x + b.x) / 2; a.y = (a.y + b.y) / 2; a.vy = 0.006;
          b.t = reactantType();                                // the spare carbon returns to the gas
          synth++; flashes.push({ x: a.x, y: a.y, life: 1 });
          cho.splice(best, 1);
        }
      }
    }

    const rule = {
      id: "soup",
      label: "Miller–Urey · spark synthesis",
      formula: "CH₄ + NH₃ + H₂O —spark→ HCN + CH₂O → amino acids (Strecker)",
      shortCaption: "STAGE 0 · MILLER–UREY",
      whatThisIs: "The 1953 experiment, live. A reducing atmosphere is sparked over boiling water; " +
                  "the discharge makes hydrogen cyanide and aldehydes, which combine into amino acids " +
                  "that collect in the water — Oparin & Haldane's \"primordial soup\", synthesised before your eyes.",
      aboutStage: "This is abiogenesis' first datum: simple gases + an energy source make the building " +
                  "blocks of life with no biology involved. Watch the spark fire, the magenta HCN and amber " +
                  "aldehydes appear, gold amino acids form and rain into the pool, and the water darken as " +
                  "organics accumulate. Raise the spark rate or the reducing strength to speed synthesis; a " +
                  "weakly-reducing (CO₂/N₂) atmosphere starves it — exactly the debate the experiment opened.",
      paletteBg: [8, 11, 17],
      paletteFg: [253, 214, 92],
      width: W, height: H,
      hiRes: true,
      stepsPerSec: 30,

      params: {
        count:    { label: "gas density",         min: 120, max: 900, step: 30, value: 420 },
        spark:    { label: "spark rate (s⁻¹)",     min: 0.2, max: 4.0, step: 0.1, value: 1.2 },
        reducing: { label: "reducing atmosphere",  min: 0.2, max: 1.0, step: 0.05, value: 0.85 },
        boil:     { label: "boil / heat",          min: 0.1, max: 1.0, step: 0.05, value: 0.6 },
      },
      controlConsequence: {
        count:    "How many gas molecules fill the flask. Denser gas → more reactant in the spark corridor → more product per strike.",
        spark:    "Discharges per second across the electrode gap. Each strike is the energy that breaks bonds; more strikes → faster synthesis.",
        reducing: "Fraction of the atmosphere that is reducing (CH₄/NH₃/H₂/H₂O vs. inert CO₂/N₂). High → rich Miller-1953 yield; low → the weakly-reducing atmosphere that barely produces amino acids.",
        boil:     "How hard the pool boils. Heat sets thermal speed, vapour rising off the surface, and the water cycle that returns condensate to the pool.",
      },
      presets: [
        { label: "Miller 1953",
          hint: "The classic strongly-reducing flask: CH₄, NH₃, H₂, H₂O, a steady spark. Amino acids accumulate within minutes.",
          values: { count: 420, spark: 1.2, reducing: 0.85, boil: 0.6 } },
        { label: "weakly reducing (CO₂/N₂)",
          hint: "A near-neutral early atmosphere. The spark still fires, but yield collapses — the central objection to a Miller-type origin.",
          values: { count: 420, spark: 1.2, reducing: 0.30, boil: 0.55 } },
        { label: "volcanic spark-storm",
          hint: "The volcanic apparatus variant (Bada/Johnson 2008): vigorous boiling and frequent lightning. Synthesis runs hot.",
          values: { count: 640, spark: 3.0, reducing: 0.9, boil: 0.95 } },
      ],

      onParamChange(name) {
        if (name === "count") {
          const n = this.params.count.value;
          if (mols.length > n) mols.length = n;
          else while (mols.length < n) spawnFromPool();
        }
      },
      reset() {
        fill(this.params.count.value);
        drops.length = splashes.length = flashes.length = 0;
        ensureBubbles(0); bolt = null; sparkFlash = 0; sparkCounter = 0;
        strikes = synth = organics = 0; progress = 0; generation = 0;
      },
      randomize() { this.reset(); },
      clear() { mols.length = 0; organics = 0; progress = 0; generation = 0; },

      step() {
        const heat = this.params.boil.value;
        const target = this.params.count.value;
        const therm = 0.0016 + heat * 0.0040;
        const grav = 0.0016 + heat * 0.0022;

        // 1) advance molecules
        for (let i = mols.length - 1; i >= 0; i--) {
          const m = mols[i];
          m.vx += (rnd() - 0.5) * therm;
          m.vy += (rnd() - 0.5) * therm + BUOY[m.t] * grav;
          m.vx *= 0.9; m.vy *= 0.9;
          m.x += m.vx; m.y += m.vy;
          if (m.x < WALL_L) { m.x = WALL_L; m.vx = Math.abs(m.vx); }
          else if (m.x > WALL_R) { m.x = WALL_R; m.vx = -Math.abs(m.vx); }
          if (m.y < ROOF) {                                   // hit the cool roof
            m.y = ROOF; m.vy = Math.abs(m.vy);
            if (m.t === H2O && rnd() < 0.06) {                // vapour condenses
              drops.push({ x: m.x, y: m.y, v: 0 }); mols.splice(i, 1); continue;
            }
          }
          if (m.y > POOL_Y) {                                 // reached the water
            if (m.t === AMINO) {                              // absorbed → soup darkens
              organics++; progress = Math.min(1, organics / ORG_TARGET);
              splashes.push({ x: m.x, y: POOL_Y, r: 0 });
              m.t = reactantType(); m.y = POOL_Y - 0.02; m.vy = -0.01; // recycle as vapour
            } else { m.y = POOL_Y; m.vy = -Math.abs(m.vy) - 0.002; }   // gas can't sink
          }
        }

        // 2) boiling: vapour off the surface + keep the population near target
        const evap = Math.round(heat * 3);
        for (let i = 0; i < evap && mols.length < target * 1.15; i++) spawnFromPool(rnd() < 0.5 ? H2O : reactantType());
        while (mols.length < target) spawnFromPool();
        ensureBubbles(Math.round(4 + heat * 16));
        for (const b of bubbles) {
          if (b.r <= 0) { b.x = WALL_L + rnd() * (WALL_R - WALL_L); b.y = 0.985; b.r = 0.004 + rnd() * 0.006; b.v = (0.004 + rnd() * 0.006) * (0.4 + heat); }
          b.y -= b.v; b.r += 0.0002;
          if (b.y < POOL_Y + 0.01) b.r = 0;                  // pops at the surface
        }

        // 3) condensate droplets fall back to the pool
        for (let i = drops.length - 1; i >= 0; i--) {
          const d = drops[i]; d.v += 0.0016; d.y += d.v;
          if (d.y > POOL_Y) { splashes.push({ x: d.x, y: POOL_Y, r: 0 }); drops.splice(i, 1); }
        }

        // 4) spark timing
        sparkCounter++;
        const interval = Math.max(2, Math.round(this.stepsPerSec / this.params.spark.value));
        if (sparkCounter >= interval) strike();
        sparkFlash *= 0.80;

        // 5) Strecker recombination
        strecker();

        // 6) age transient effects
        for (let i = splashes.length - 1; i >= 0; i--) { const s = splashes[i]; s.r += 0.006; if (s.r > 0.06) splashes.splice(i, 1); }
        for (let i = flashes.length - 1; i >= 0; i--) { flashes[i].life -= 0.12; if (flashes[i].life <= 0) flashes.splice(i, 1); }

        generation++;
      },

      // ── Authentic cross-section render (hiRes path) ─────────────────────────
      renderPhotoreal(ctx, CW, CH, newCanvas) {
        rt += 1;
        const X = (x) => x * CW, Y = (y) => y * CH;
        if (!this._spr) this._spr = {};
        const sprite = (t) => {
          if (this._spr[t]) return this._spr[t];
          const s = 24, c = newCanvas(s, s), g = c.getContext("2d");
          const [r, gr, b] = COLOR[t];
          const rad = g.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2);
          rad.addColorStop(0, `rgba(${r},${gr},${b},1)`);
          rad.addColorStop(0.4, `rgba(${r},${gr},${b},0.6)`);
          rad.addColorStop(1, `rgba(${r},${gr},${b},0)`);
          g.fillStyle = rad; g.fillRect(0, 0, s, s);
          return (this._spr[t] = c);
        };

        // flask interior
        const bg = ctx.createRadialGradient(CW * 0.5, CH * 0.42, CH * 0.1, CW * 0.5, CH * 0.5, CH * 0.7);
        bg.addColorStop(0, "#0c1018"); bg.addColorStop(1, "#06080d");
        ctx.fillStyle = bg; ctx.fillRect(0, 0, CW, CH);
        // faint flask wall arc (the 5-litre sphere)
        ctx.strokeStyle = "rgba(63,224,208,0.10)"; ctx.lineWidth = Math.max(1, CW * 0.004);
        ctx.beginPath(); ctx.arc(CW * 0.5, CH * 0.52, CW * 0.46, Math.PI * 0.04, Math.PI * 0.96); ctx.stroke();

        // ── water pool (clear → tea-dark with progress) ────────────────────
        const top = COLOR[H2O], soup = [58, 33, 12];
        const mix = (a, b, k) => Math.round(a + (b - a) * k);
        const pr = progress;
        const surfShim = Math.sin(rt * 0.08) * CH * 0.004;
        const py = Y(POOL_Y) + surfShim;
        const pool = ctx.createLinearGradient(0, py, 0, CH);
        pool.addColorStop(0, `rgba(${mix(top[0],soup[0],pr)},${mix(top[1],soup[1],pr)},${mix(top[2],soup[2],pr)},0.92)`);
        pool.addColorStop(1, `rgba(${mix(20,28,pr)},${mix(54,16,pr)},${mix(66,8,pr)},0.98)`);
        ctx.fillStyle = pool; ctx.fillRect(0, py, CW, CH - py);
        // meniscus highlight
        ctx.strokeStyle = `rgba(${mix(150,90,pr)},${mix(220,60,pr)},${mix(232,40,pr)},0.55)`;
        ctx.lineWidth = Math.max(1, CH * 0.004);
        ctx.beginPath(); ctx.moveTo(0, py); ctx.lineTo(CW, py); ctx.stroke();
        // boiling bubbles
        ctx.fillStyle = "rgba(220,240,245,0.20)";
        for (const b of bubbles) { if (b.r <= 0) continue; ctx.beginPath(); ctx.arc(X(b.x), Y(b.y), b.r * CW, 0, 6.283); ctx.fill(); }
        // splash rings where amino acids / droplets land
        for (const s of splashes) {
          ctx.strokeStyle = `rgba(253,214,92,${Math.max(0, 0.5 - s.r * 7)})`;
          ctx.lineWidth = Math.max(1, CH * 0.003);
          ctx.beginPath(); ctx.arc(X(s.x), py, s.r * CW, Math.PI, 2 * Math.PI); ctx.stroke();
        }

        // ── molecules (additive glow + crisp core) ─────────────────────────
        ctx.globalCompositeOperation = "lighter";
        for (const m of mols) {
          const big = m.t === AMINO ? 1.7 : (m.t === HCN || m.t === CHO) ? 1.2 : 1;
          const sz = CW * 0.020 * big, c = sprite(m.t);
          ctx.drawImage(c, X(m.x) - sz, Y(m.y) - sz, sz * 2, sz * 2);
        }
        // reaction flashes
        for (const f of flashes) {
          ctx.fillStyle = `rgba(255,236,180,${f.life * 0.7})`;
          ctx.beginPath(); ctx.arc(X(f.x), Y(f.y), CW * 0.012 * (1 + (1 - f.life)), 0, 6.283); ctx.fill();
        }
        // condensate droplets
        for (const d of drops) {
          const c = sprite(H2O), sz = CW * 0.013;
          ctx.drawImage(c, X(d.x) - sz, Y(d.y) - sz, sz * 2, sz * 2);
        }
        ctx.globalCompositeOperation = "source-over";

        // ── electrodes + spark ─────────────────────────────────────────────
        ctx.strokeStyle = "#3b3b42"; ctx.lineWidth = CW * 0.018; ctx.lineCap = "round";
        ctx.beginPath(); ctx.moveTo(X(0.32), Y(0.07)); ctx.lineTo(X(0.435), Y(0.155));
        ctx.moveTo(X(0.68), Y(0.07)); ctx.lineTo(X(0.565), Y(0.155)); ctx.stroke();
        ctx.fillStyle = "#26262b";
        for (const ex of [0.32, 0.68]) { ctx.beginPath(); ctx.arc(X(ex), Y(0.07), CW * 0.018, 0, 6.283); ctx.fill(); }
        if (sparkFlash > 0.04 && bolt) {
          ctx.globalCompositeOperation = "lighter";
          const fl = sparkFlash;
          const halo = ctx.createRadialGradient(X(0.5), Y(0.18), 0, X(0.5), Y(0.18), CW * 0.3 * fl);
          halo.addColorStop(0, `rgba(215,150,255,${0.30 * fl})`); halo.addColorStop(1, "rgba(215,150,255,0)");
          ctx.fillStyle = halo; ctx.fillRect(0, 0, CW, CH * 0.6);
          ctx.strokeStyle = `rgba(245,225,255,${0.7 + 0.3 * fl})`;
          ctx.lineWidth = CW * 0.006 * (0.6 + fl);
          ctx.beginPath(); ctx.moveTo(X(bolt[0][0]), Y(bolt[0][1]));
          for (let i = 1; i < bolt.length; i++) ctx.lineTo(X(bolt[i][0]), Y(bolt[i][1]));
          ctx.stroke();
          ctx.globalCompositeOperation = "source-over";
        }

        // ── HUD (Catalytic-Silence) ────────────────────────────────────────
        const fs = Math.max(9, CH * 0.021);
        ctx.font = `${fs}px "IBM Plex Mono", monospace`;
        ctx.textBaseline = "top"; ctx.textAlign = "left";
        ctx.fillStyle = "rgba(63,224,208,0.85)";
        ctx.fillText("MILLER–UREY · SPARK-DISCHARGE SYNTHESIS", CW * 0.04, CH * 0.035);
        ctx.fillStyle = "rgba(206,200,184,0.85)";
        ctx.fillText(`strikes ${strikes}   amino acids ${synth}   organics ${(progress * 100) | 0}%`, CW * 0.04, CH * 0.035 + fs * 1.4);
        // legend
        const leg = [CH4, NH3, H2O, HCN, CHO, AMINO];
        let lx = CW * 0.04; const ly = CH * 0.92;
        ctx.textBaseline = "middle";
        for (const t of leg) {
          const [r, g, b] = COLOR[t];
          ctx.fillStyle = `rgb(${r},${g},${b})`;
          ctx.beginPath(); ctx.arc(lx + fs * 0.4, ly, fs * 0.34, 0, 6.283); ctx.fill();
          ctx.fillStyle = "rgba(206,200,184,0.8)";
          const tx = LABEL[t]; ctx.fillText(tx, lx + fs * 0.95, ly);
          lx += fs * 0.95 + ctx.measureText(tx).width + fs * 0.8;
        }
      },

      // ── SEM height field (retained for the SEM path + smoke test) ──────────
      // The organic deposit/soup reads as a raised aqueous floor; gas molecules
      // and products stipple the field above it.
      renderHeight(out) {
        const poolRow = (POOL_Y * H) | 0;
        for (let y = 0; y < H; y++) {
          const inPool = y >= poolRow;
          const base = inPool ? 0.45 + progress * 0.4 : 0.06;
          for (let x = 0; x < W; x++) {
            out[y * W + x] = base + (inPool ? 0.04 * Math.sin((x + y) * 0.3) : 0.02 * Math.random());
          }
        }
        for (const m of mols) {
          const xi = (m.x * W) | 0, yi = (m.y * H) | 0;
          if (xi < 0 || xi >= W || yi < 0 || yi >= H) continue;
          out[yi * W + xi] = Math.min(1, out[yi * W + xi] + (m.t === AMINO ? 0.6 : 0.3));
        }
      },

      // RGBA fallback (only if the hiRes path is unavailable).
      render(pixels) {
        const poolRow = (POOL_Y * H) | 0;
        for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
          const i = (y * W + x) * 4, inPool = y >= poolRow;
          pixels[i]   = inPool ? 40 + progress * 30 : 8;
          pixels[i+1] = inPool ? 70 - progress * 40 : 11;
          pixels[i+2] = inPool ? 90 - progress * 60 : 17;
          pixels[i+3] = 255;
        }
        for (const m of mols) {
          const xi = (m.x * W) | 0, yi = (m.y * H) | 0;
          if (xi < 0 || xi >= W || yi < 0 || yi >= H) continue;
          const i = (yi * W + xi) * 4, [r, g, b] = COLOR[m.t];
          pixels[i] = r; pixels[i+1] = g; pixels[i+2] = b;
        }
      },

      paint(gx, gy, radius) {            // inject reactant gas where painted
        const n = Math.max(1, (radius * radius / 6) | 0);
        for (let i = 0; i < n; i++) mols.push(newMol(reactantType(), clampX(gx / W), Math.min(POOL_Y - 0.02, gy / H)));
      },
      population() { return `${mols.length} molecules · ${strikes} strikes · ${synth} amino acids`; },
      generation() { return generation; },
    };

    // expose params to the closure helpers
    var params = rule.params;
    rule.reset();
    return rule;
  }

  CA.RULES.soup = make;
})();
