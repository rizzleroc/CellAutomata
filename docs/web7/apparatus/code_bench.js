// Stage 8 — Genetic code · In-vitro translation bench.
//
// Vetsigian–Woese–Goldenfeld code coevolution: the codon→amino-acid table
// converges under selection toward the canonical code. A tidy bench vignette —
// a brass/steel tube rack of small clear reaction tubes (some tinted), an
// upright "codon table" card showing a grid of codon cells that flicker then
// progressively lock into stable colours as the code converges, and a small
// readout box with a convergence meter. progress = fraction of cells settled;
// setRunning(false) freezes the grid.

import * as THREE from 'three';
import { part, steelMat, brassMat, glassMat, bakeliteMat, liquidMat, makeDynamicTexture, V } from './lib.js';

const GRID = 4;                 // 4x4 codon-cell table
const N = GRID * GRID;
// canonical (settled) colours each cell converges to — amino-acid classes
const SETTLED = [
  0xd95f5f, 0xd98a4f, 0xd9c24f, 0x9fd94f, 0x4fd96b, 0x4fd9b0, 0x4fb6d9, 0x4f78d9,
  0x6b4fd9, 0xa84fd9, 0xd94fc2, 0xd94f86, 0xb0b0b0, 0x8fa86b, 0x6ba88f, 0xa88f6b,
];

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

  group.position.y = 0;

  // ── Animation ──────────────────────────────────────────────────────────────
  // deterministic lock times: cells settle one by one over the run
  const lockT = [];
  for (let i = 0; i < N; i++) lockT[i] = 2 + ((i * 2.7) % N) * 1.6; // 2..~28s
  const lastLock = Math.max(...lockT);

  let running = true, progress = 0, clock = 0;
  const settledFrac = (tc) => lockT.filter(l => tc >= l).length / N;

  group.userData.anim = {
    setRunning(on) { running = on; },
    getProgress() { return progress; },
    reset() {
      clock = 0; progress = 0;
      drawGrid(gridTex.ctx, gridTex.size, lockT, 0, true); gridTex.tex.needsUpdate = true;
      drawReadout(roTex.ctx, roTex.size, 0); roTex.tex.needsUpdate = true;
    },
    update(dt, t) {
      if (running) clock += dt;
      drawGrid(gridTex.ctx, gridTex.size, lockT, clock, running);
      gridTex.tex.needsUpdate = true;
      progress = settledFrac(clock);
      drawReadout(roTex.ctx, roTex.size, progress);
      roTex.tex.needsUpdate = true;
    },
  };
  return group;
}

export const meta = {
  id: 'stage8-code',
  label: 'Stage 8 — Genetic code',
  title: 'In-vitro translation bench',
  blurb: 'Vetsigian–Woese–Goldenfeld code coevolution: the codon→amino-acid table converges under selection toward the canonical code.',
  build,
};
