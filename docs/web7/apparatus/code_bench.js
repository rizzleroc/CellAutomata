// Stage 8 — Genetic code · In-vitro translation bench.
//
// Vetsigian–Woese–Goldenfeld code coevolution: the codon→amino-acid table
// converges under selection toward the canonical code. A tidy bench vignette —
// a brass/steel tube rack of small clear reaction tubes (some tinted), an
// upright "codon table" card showing a grid of codon cells that flicker then
// progressively lock into stable colours as the code converges, and a small
// readout box with a convergence meter. progress = fraction of cells settled;
// setRunning(false) freezes the grid.
//
// The experiment is ALSO shown as its real physical process: a ribosome rides
// along an mRNA strand reading a scrolling codon strip, and one amino-acid
// sphere is appended to a growing peptide chain per codon incorporated, with a
// teal indicator bead/light that blinks on every incorporation. All of that
// motion is gated on `running` (stop ⇒ the bench goes calm). progress folds in
// peptide length alongside code-consensus.

import * as THREE from 'three';
import { part, steelMat, brassMat, glassMat, bakeliteMat, liquidMat, makeDynamicTexture, V } from './lib.js';

const GRID = 4;                 // 4x4 codon-cell table
const N = GRID * GRID;
// canonical (settled) colours each cell converges to — amino-acid classes
const SETTLED = [
  0xd95f5f, 0xd98a4f, 0xd9c24f, 0x9fd94f, 0x4fd96b, 0x4fd9b0, 0x4fb6d9, 0x4f78d9,
  0x6b4fd9, 0xa84fd9, 0xd94fc2, 0xd94f86, 0xb0b0b0, 0x8fa86b, 0x6ba88f, 0xa88f6b,
];

// emissive/light palette (teal / magenta / warm only)
const TEAL = 0x3fe0d0, MAGENTA = 0xd77bff, WARM = 0xffb866;
// per-residue amino-acid sphere colours (cycled as the chain grows)
const AA_COLORS = [TEAL, WARM, MAGENTA, 0x9fd9c4, 0xffd0a0, 0xc8a8ff];

function drawGrid(ctx, size, lockT, t, running) {
  ctx.fillStyle = '#100d0a'; ctx.fillRect(0, 0, size, size);
  const pad = size * 0.06, cell = (size - pad * 2) / GRID;
  for (let i = 0; i < N; i++) {
    const r = Math.floor(i / GRID), c = i % GRID;
    const x = pad + c * cell, y = pad + r * cell;
    const settled = t >= lockT[i];
    let col;
    if (settled || !running) {
      const base = SETTLED[i];
      col = `#${base.toString(16).padStart(6, '0')}`;
    } else {
      // flicker through random codon assignments before locking
      const flick = Math.floor((t * 9 + i * 3) % SETTLED.length);
      const base = SETTLED[flick];
      col = `rgba(${((base >> 16) & 255)},${((base >> 8) & 255)},${base & 255},0.55)`;
    }
    ctx.fillStyle = col;
    ctx.fillRect(x + 2, y + 2, cell - 4, cell - 4);
    ctx.strokeStyle = settled ? '#caa86a' : '#3a342a';
    ctx.lineWidth = settled ? 3 : 1.5;
    ctx.strokeRect(x + 2, y + 2, cell - 4, cell - 4);
  }
}

function drawReadout(ctx, size, frac) {
  ctx.fillStyle = '#04130c'; ctx.fillRect(0, 0, size, size);
  ctx.fillStyle = '#39ff9a'; ctx.textAlign = 'left';
  ctx.font = `bold ${size * 0.16}px "Courier New", monospace`;
  ctx.fillText('CONVERGENCE', size * 0.08, size * 0.26);
  ctx.font = `bold ${size * 0.28}px "Courier New", monospace`;
  ctx.fillText(`${Math.round(frac * 100)}%`, size * 0.08, size * 0.62);
  // bar
  ctx.strokeStyle = '#1d6b40'; ctx.lineWidth = 4;
  ctx.strokeRect(size * 0.08, size * 0.72, size * 0.84, size * 0.16);
  ctx.fillStyle = '#39ff9a';
  ctx.fillRect(size * 0.08 + 3, size * 0.72 + 3, (size * 0.84 - 6) * frac, size * 0.16 - 6);
}

export function build() {
  const group = new THREE.Group();
  group.name = 'genetic-code-bench';

  // ── Bench block (the working surface vignette) ─────────────────────────────
  group.add(part(new THREE.BoxGeometry(5.0, 0.25, 2.2), bakeliteMat(0x2b231a), 'bench-block', V(0, 0.125, 0)));

  // ── Tube rack (brass/steel) holding clear reaction tubes ───────────────────
  const rack = new THREE.Group(); rack.name = 'tube-rack';
  rack.position.set(-1.6, 0.25, 0);
  // two end plates + base
  for (const sz of [-0.55, 0.55]) {
    rack.add(part(new THREE.BoxGeometry(0.1, 0.8, 1.0), brassMat(), `rack-end-${sz < 0 ? 'L' : 'R'}`, V(sz, 0.4, 0)));
  }
  rack.add(part(new THREE.BoxGeometry(1.3, 0.1, 1.0), steelMat(), 'rack-base', V(0, 0.05, 0)));
  // top rail with holes (a steel bar)
  rack.add(part(new THREE.BoxGeometry(1.3, 0.08, 1.0), steelMat(), 'rack-rail', V(0, 0.72, 0)));
  group.add(rack);

  // ── Reaction tubes, some tinted ────────────────────────────────────────────
  const tints = [0xdedad0, 0x9fd9c4, 0xdedad0, 0xd9b0c8, 0xc8d0d9, 0xdedad0];
  for (let i = 0; i < 6; i++) {
    const tx = -1.6 - 0.45 + (i % 3) * 0.45;
    const tz = (i < 3 ? -0.22 : 0.22);
    const tube = part(new THREE.CylinderGeometry(0.11, 0.07, 0.7, 18), glassMat(), `tube-${i}`,
      V(tx, 0.62, tz));
    group.add(tube);
    // liquid fill
    group.add(part(new THREE.CylinderGeometry(0.09, 0.06, 0.34, 16),
      liquidMat(tints[i], { transmission: 0.65, opacity: 0.85 }), `tube-${i}-fill`, V(tx, 0.5, tz)));
  }

  // ── Codon-table card (upright panel) ───────────────────────────────────────
  const gridTex = makeDynamicTexture(256);
  drawGrid(gridTex.ctx, gridTex.size, new Array(N).fill(1e9), 0, true);
  gridTex.tex.needsUpdate = true;
  // card backing frame
  group.add(part(new THREE.BoxGeometry(1.9, 1.9, 0.08), bakeliteMat(0x1d1712), 'codon-card', V(0.7, 1.2, -0.2)));
  group.add(part(new THREE.PlaneGeometry(1.7, 1.7),
    new THREE.MeshStandardMaterial({ map: gridTex.tex, roughness: 0.6, metalness: 0.05 }),
    'codon-grid', V(0.7, 1.2, -0.155)));
  // little brass easel leg
  const leg = part(new THREE.CylinderGeometry(0.04, 0.04, 1.6, 12), brassMat(), 'card-easel', V(0.7, 0.95, -0.45));
  leg.rotation.x = 0.35;
  group.add(leg);

  // ── Readout box with convergence meter ─────────────────────────────────────
  group.add(part(new THREE.BoxGeometry(1.2, 0.8, 0.7), steelMat(), 'readout', V(2.2, 0.65, 0.2)));
  const roTex = makeDynamicTexture(256);
  drawReadout(roTex.ctx, roTex.size, 0);
  roTex.tex.needsUpdate = true;
  const roDisp = part(new THREE.PlaneGeometry(0.95, 0.55),
    new THREE.MeshBasicMaterial({ map: roTex.tex }), 'readout-display', V(2.2, 0.72, 0.56));
  group.add(roDisp);

  // ── Translation stage: mRNA strand + ribosome + growing peptide ────────────
  // A glass deck slung in front of the rack carries the working translation.
  // Everything below is UNNAMED dynamic apparatus added to this sub-group so it
  // reads as "the live experiment" sitting on the bench, gated on `running`.
  const tStage = new THREE.Group();
  tStage.position.set(-1.6, 1.18, 0.62);          // floats in front of the rack
  group.add(tStage);

  const TRACK_X0 = -1.05, TRACK_X1 = 1.05;        // mRNA extent (stage-local x)
  const TRACK_LEN = TRACK_X1 - TRACK_X0;
  const CODON_W = 0.30;                            // spacing of codon rungs
  const NCODON = Math.round(TRACK_LEN / CODON_W);  // codons visible on the strip

  // mRNA backbone — a slim teal-lit rail the codons scroll along.
  const mrna = part(new THREE.CylinderGeometry(0.035, 0.035, TRACK_LEN + 0.5, 12),
    new THREE.MeshStandardMaterial({ color: 0x14322e, emissive: TEAL, emissiveIntensity: 0.18, roughness: 0.5, metalness: 0.2 }),
    'mrna-strand', V(0, 0, 0));
  mrna.rotation.z = Math.PI / 2;
  tStage.add(mrna);

  // Codon strip: a row of little emissive rungs that SCROLLS along the mRNA
  // (translate in -x, wrap around) so the message is visibly being read.
  const codonMat = [TEAL, WARM, MAGENTA].map((c) =>
    new THREE.MeshStandardMaterial({ color: 0x0c0c10, emissive: c, emissiveIntensity: 0.5, roughness: 0.4 }));
  const codons = [];
  for (let i = 0; i <= NCODON + 1; i++) {
    const rung = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.12, 0.20), codonMat[i % 3]);
    rung.userData.baseX = TRACK_X0 + i * CODON_W;
    rung.position.set(rung.userData.baseX, 0.0, 0);
    tStage.add(rung);
    codons.push(rung);
  }

  // Ribosome: a two-subunit clamp (large lower + small upper sphere) that steps
  // codon by codon along the mRNA. Its own little group so both halves move.
  const ribo = new THREE.Group();
  ribo.position.set(TRACK_X0, 0, 0);
  const riboBig = new THREE.Mesh(new THREE.SphereGeometry(0.22, 24, 18),
    new THREE.MeshStandardMaterial({ color: 0x6b5a44, roughness: 0.6, metalness: 0.15 }));
  riboBig.position.y = -0.10;
  const riboSmall = new THREE.Mesh(new THREE.SphereGeometry(0.15, 20, 16),
    new THREE.MeshStandardMaterial({ color: 0x8a7860, roughness: 0.55, metalness: 0.15 }));
  riboSmall.position.y = 0.14;
  ribo.add(riboBig); ribo.add(riboSmall);
  tStage.add(ribo);

  // Indicator bead riding on the ribosome — blinks (emissive + light) on every
  // codon incorporated.
  const beadMat = new THREE.MeshStandardMaterial({ color: 0x07201d, emissive: TEAL, emissiveIntensity: 0.0, roughness: 0.3 });
  const bead = new THREE.Mesh(new THREE.SphereGeometry(0.06, 14, 12), beadMat);
  bead.position.y = 0.30;
  ribo.add(bead);
  const beadLight = new THREE.PointLight(TEAL, 0.0, 2.2, 2);
  beadLight.position.y = 0.30;
  ribo.add(beadLight);

  // Growing peptide chain: a pool of amino-acid spheres that get APPENDED one at
  // a time (made visible + positioned) as the ribosome incorporates each codon,
  // trailing back from the ribosome's exit tunnel.
  const MAXPEP = NCODON;                            // residues per full pass
  const pepGeo = new THREE.SphereGeometry(0.085, 16, 12);
  const peptide = [];
  for (let i = 0; i < MAXPEP; i++) {
    const aa = new THREE.Mesh(pepGeo, new THREE.MeshStandardMaterial({
      color: AA_COLORS[i % AA_COLORS.length], emissive: AA_COLORS[i % AA_COLORS.length],
      emissiveIntensity: 0.22, roughness: 0.45, metalness: 0.1,
    }));
    aa.visible = false;
    aa.userData.homeX = 0;                          // where in the chain it settled
    tStage.add(aa);
    peptide.push(aa);
  }

  group.position.y = 0;

  // ── Animation ──────────────────────────────────────────────────────────────
  // deterministic lock times: cells settle one by one over the run
  const lockT = [];
  for (let i = 0; i < N; i++) lockT[i] = 2 + ((i * 2.7) % N) * 1.6; // 2..~28s
  const settledFrac = (tc) => lockT.filter(l => tc >= l).length / N;

  // translation timing
  const STEP_T = 0.85;                              // seconds the ribosome takes per codon
  const SCROLL_V = CODON_W / STEP_T;                // strip scroll speed (codon/step)

  let running = true, progress = 0, clock = 0;
  let nIncorp = 0;          // residues incorporated this pass
  let stepClock = 0;        // time accumulator for the current codon step
  let blink = 0;            // 0..1 decaying flash on incorporation
  let scroll = 0;           // strip scroll offset

  function placePeptide() {
    // chain dangles back from the ribosome's exit (to its left / -x), curving
    // slightly down — append order so newest residue is nearest the ribosome.
    const exitX = ribo.position.x - 0.18;
    for (let i = 0; i < MAXPEP; i++) {
      const aa = peptide[i];
      if (i >= nIncorp) { aa.visible = false; continue; }
      aa.visible = true;
      const back = (nIncorp - 1 - i);               // 0 = newest (at exit)
      const x = exitX - back * 0.16;
      const y = -0.04 - Math.sin(back * 0.6) * 0.10 - back * 0.012;
      const z = 0.10 + Math.sin(back * 0.9) * 0.06;
      aa.position.set(x, y, z);
    }
  }

  function layoutTranslation() {
    // Keep the ribosome anchored near the strip's reading head (left third) and
    // scroll the codon strip beneath it — classic "tape reader" motion.
    ribo.position.x = TRACK_X0 + 0.15;

    // scroll the codon rungs leftwards, wrapping within the track extent.
    for (const rung of codons) {
      let x = rung.userData.baseX - scroll;
      // wrap into [TRACK_X0 - 0.5, TRACK_X1 + 0.5]
      const span = TRACK_LEN + 0.5;
      while (x < TRACK_X0 - 0.25) x += span;
      while (x > TRACK_X1 + 0.25) x -= span;
      rung.position.x = x;
      // codons brighten as they pass under the reading head (the ribosome)
      const d = Math.abs(x - ribo.position.x);
      rung.material.emissiveIntensity = 0.4 + (running ? Math.max(0, 0.7 - d * 1.6) : 0);
    }

    placePeptide();

    // indicator bead + light blink decays after each incorporation
    beadMat.emissiveIntensity = 0.05 + blink * 1.4;
    beadLight.intensity = running ? blink * 2.4 : 0;
    bead.scale.setScalar(1 + blink * 0.8);

    // gentle ribosome "ratchet" wobble while actively translating
    const wob = running ? Math.sin(stepClock / STEP_T * Math.PI) * 0.04 : 0;
    riboSmall.position.x = wob;
    ribo.position.y = wob * 0.5;
  }

  group.userData.anim = {
    setRunning(on) { running = on; },
    getProgress() { return progress; },
    reset() {
      clock = 0; progress = 0;
      nIncorp = 0; stepClock = 0; blink = 0; scroll = 0;
      drawGrid(gridTex.ctx, gridTex.size, lockT, 0, true); gridTex.tex.needsUpdate = true;
      drawReadout(roTex.ctx, roTex.size, 0); roTex.tex.needsUpdate = true;
      layoutTranslation();
    },
    update(dt, t) {
      if (running) {
        clock += dt;

        // advance the ribosome one codon at a time
        stepClock += dt;
        scroll += SCROLL_V * dt;
        if (stepClock >= STEP_T) {
          stepClock -= STEP_T;
          if (nIncorp < NCODON) {
            nIncorp++;                 // APPEND one amino acid to the peptide
            blink = 1;                 // flash the incorporation indicator
          } else {
            // full message read → recycle: ribosome releases, strip keeps going
            nIncorp = 0;
            blink = 1;
          }
        }
        // decay the incorporation flash
        blink = Math.max(0, blink - dt * 3.0);
      }
      // texture-driven displays (codon table + convergence meter)
      drawGrid(gridTex.ctx, gridTex.size, lockT, clock, running);
      gridTex.tex.needsUpdate = true;
      const consensus = settledFrac(clock);
      // progress folds peptide-chain length with code consensus
      const pepFrac = nIncorp / NCODON;
      progress = Math.max(0, Math.min(1, consensus * 0.7 + pepFrac * 0.3));
      drawReadout(roTex.ctx, roTex.size, progress);
      roTex.tex.needsUpdate = true;

      // the physical translation motion (gated on running inside)
      layoutTranslation();
    },
  };
  // lay everything out once so the idle/initial frame is sane + finite
  group.userData.anim.reset();
  return group;
}

export const meta = {
  id: 'stage8-code',
  label: 'Stage 8 — Genetic code',
  title: 'In-vitro translation bench',
  blurb: 'Vetsigian–Woese–Goldenfeld code coevolution: the codon→amino-acid table converges under selection toward the canonical code.',
  build,
};
