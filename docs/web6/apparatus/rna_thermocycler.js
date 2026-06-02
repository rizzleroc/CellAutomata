// Stage 7 — RNA world · Ribozyme replication assay.
//
// A vintage PCR thermocycler: a boxy bakelite/steel instrument with a hinged
// heated lid over a heat block holding an 8-tube strip, a front control panel
// with a small glowing display cycling the thermal program (95→55→72 °C). A
// gel-doc beside it shows migrating bands drifting downward. When run, the
// display cycles, the lid heat glow pulses, and the gel bands migrate. progress
// tracks cycle count — RNA replicating below the error threshold ε_c.

import * as THREE from 'three';
import { part, steelMat, bakeliteMat, glassMat, darkMetalMat, brassMat, makeDynamicTexture, V } from './lib.js';

const PROGRAM = [95, 55, 72]; // denature / anneal / extend (°C)
const STEP_T = 1.6;           // seconds per thermal step

function drawDisplay(ctx, size, temp, cycle, phase) {
  ctx.fillStyle = '#04130c'; ctx.fillRect(0, 0, size, size);
  ctx.fillStyle = '#0d3a22'; ctx.fillRect(6, 6, size - 12, size - 12);
  ctx.fillStyle = '#39ff9a'; ctx.textAlign = 'center';
  ctx.font = `bold ${size * 0.34}px "Courier New", monospace`;
  ctx.fillText(`${Math.round(temp)}°C`, size / 2, size * 0.46);
  ctx.font = `${size * 0.13}px "Courier New", monospace`;
  ctx.fillText(phase, size / 2, size * 0.66);
  ctx.fillText(`CYC ${cycle}`, size / 2, size * 0.86);
}

function drawGel(ctx, size, offset) {
  ctx.fillStyle = '#07110d'; ctx.fillRect(0, 0, size, size);
  const lanes = 6;
  for (let l = 0; l < lanes; l++) {
    const x = (l + 0.5) * (size / lanes);
    // well at top
    ctx.fillStyle = '#1c2a22'; ctx.fillRect(x - size * 0.05, 4, size * 0.1, 8);
    // migrating bands per lane, drifting down with offset
    for (let b = 0; b < 4; b++) {
      const base = size * (0.18 + b * 0.18) + (offset * size * 0.5) % (size * 0.7);
      const y = 14 + (base % (size - 28));
      const w = size * 0.07 * (1 - b * 0.12);
      const a = 0.85 - b * 0.15;
      ctx.fillStyle = `rgba(140,255,180,${a})`;
      ctx.fillRect(x - w, y, w * 2, size * 0.022);
    }
  }
}

export function build() {
  const group = new THREE.Group();
  group.name = 'rna-thermocycler-1953';

  // ── Cycler body (boxy bakelite + steel) ────────────────────────────────────
  const body = part(new THREE.BoxGeometry(3.4, 1.6, 2.4), bakeliteMat(0x2a221a), 'cycler-body', V(-0.6, 0.8, 0));
  group.add(body);
  // steel front fascia
  group.add(part(new THREE.BoxGeometry(3.42, 0.9, 0.06), steelMat(), 'cycler-fascia', V(-0.6, 0.55, 1.21)));

  // ── Heat block on top, recessed ────────────────────────────────────────────
  const block = part(new THREE.BoxGeometry(2.6, 0.4, 1.2), steelMat(), 'heat-block', V(-0.6, 1.6, 0));
  group.add(block);

  // ── 8-tube strip seated in the block ──────────────────────────────────────
  const tubeMat = glassMat();
  for (let i = 0; i < 8; i++) {
    const tx = -0.6 - 1.0 + i * (2.0 / 7);
    const t = part(new THREE.CylinderGeometry(0.1, 0.05, 0.42, 16), tubeMat, `tube-${i}`, V(tx, 1.78, 0));
    group.add(t);
    // cap
    group.add(part(new THREE.CylinderGeometry(0.12, 0.1, 0.08, 16), darkMetalMat(), `tube-cap-${i}`, V(tx, 2.0, 0)));
  }
  // named "tube-strip" connector spine
  group.add(part(new THREE.BoxGeometry(2.1, 0.06, 0.16), plasticSpine(), 'tube-strip', V(-0.6, 2.02, 0.0)));

  // ── Hinged heated lid (angled open) ────────────────────────────────────────
  const lid = new THREE.Group();
  lid.name = 'lid';
  const lidPlate = part(new THREE.BoxGeometry(2.8, 0.18, 1.4), steelMat(), 'lid-plate', V(0, 0, 0));
  lid.add(lidPlate);
  lid.add(part(new THREE.BoxGeometry(2.6, 0.1, 1.2), darkMetalMat(), 'lid-heater-face', V(0, -0.12, 0)));
  // hinge at back edge, lid raised at an angle
  lid.position.set(-0.6, 1.95, -0.6);
  lid.rotation.x = -0.9;
  // shift so it rotates about the back hinge
  lidPlate.position.y = 0.0; lid.children.forEach(c => { c.position.z += 0.6; c.position.y += 0.1; });
  group.add(lid);
  // heat-glow plane under the lid heater
  const glow = part(new THREE.PlaneGeometry(2.5, 1.1),
    new THREE.MeshBasicMaterial({ color: 0xff6a2a, transparent: true, opacity: 0.0 }), 'lid-glow', V(-0.6, 1.84, 0));
  glow.rotation.x = -Math.PI / 2;
  group.add(glow);
  const heatLight = new THREE.PointLight(0xff7a30, 0, 3, 2);
  heatLight.position.set(-0.6, 2.0, 0);
  group.add(heatLight);

  // ── Front control panel + glowing display ─────────────────────────────────
  group.add(part(new THREE.BoxGeometry(1.4, 0.7, 0.05), darkMetalMat(), 'control-panel', V(-1.2, 0.55, 1.24)));
  const dispTex = makeDynamicTexture(256);
  drawDisplay(dispTex.ctx, dispTex.size, PROGRAM[0], 1, 'DENATURE');
  dispTex.tex.needsUpdate = true;
  group.add(part(new THREE.PlaneGeometry(0.85, 0.5),
    new THREE.MeshBasicMaterial({ map: dispTex.tex }), 'display', V(-1.2, 0.62, 1.27)));
  // a couple of brass knobs on the panel
  for (const kx of [-0.35, 0.0]) {
    group.add(part(new THREE.CylinderGeometry(0.1, 0.1, 0.1, 18), brassMat(), `panel-knob-${kx}`, V(-0.6 + kx + 0.55, 0.4, 1.27)));
  }

  // ── Gel-doc beside the cycler (right) ──────────────────────────────────────
  group.add(part(new THREE.BoxGeometry(1.7, 2.2, 1.2), bakeliteMat(0x1d1712), 'gel-doc', V(2.2, 1.1, 0)));
  const gelTex = makeDynamicTexture(256);
  drawGel(gelTex.ctx, gelTex.size, 0);
  gelTex.tex.needsUpdate = true;
  group.add(part(new THREE.PlaneGeometry(1.3, 1.3),
    new THREE.MeshBasicMaterial({ map: gelTex.tex }), 'gel-screen', V(2.2, 1.4, 0.61)));
  group.add(part(new THREE.TorusGeometry(0.68, 0.04, 10, 40), steelMat(), 'gel-bezel', V(2.2, 1.4, 0.62)));

  group.position.y = 0;

  // ── Animation ──────────────────────────────────────────────────────────────
  let running = true, progress = 0, clock = 0, cycle = 1, gelOffset = 0;
  const TOTAL_CYCLES = 30;
  const phaseNames = ['DENATURE', 'ANNEAL', 'EXTEND'];

  group.userData.anim = {
    setRunning(on) { running = on; },
    getProgress() { return progress; },
    reset() {
      progress = 0; clock = 0; cycle = 1; gelOffset = 0;
      drawDisplay(dispTex.ctx, dispTex.size, PROGRAM[0], 1, phaseNames[0]); dispTex.tex.needsUpdate = true;
      drawGel(gelTex.ctx, gelTex.size, 0); gelTex.tex.needsUpdate = true;
      glow.material.opacity = 0; heatLight.intensity = 0;
    },
    update(dt, t) {
      if (!running) { glow.material.opacity *= 0.9; heatLight.intensity *= 0.9; return; }
      clock += dt;
      const stepIdx = Math.floor(clock / STEP_T) % PROGRAM.length;
      // advance cycle each full program
      const totalSteps = Math.floor(clock / STEP_T);
      cycle = 1 + Math.floor(totalSteps / PROGRAM.length);
      const temp = PROGRAM[stepIdx];
      drawDisplay(dispTex.ctx, dispTex.size, temp, Math.min(cycle, TOTAL_CYCLES), phaseNames[stepIdx]);
      dispTex.tex.needsUpdate = true;
      // lid heat glow pulses, hottest at denature (95)
      const heat = (temp - 55) / 40;            // 0..1
      const pulse = 0.5 + 0.5 * Math.sin(t * 4);
      glow.material.opacity = 0.15 + heat * 0.5 * pulse;
      heatLight.intensity = 0.5 + heat * 2.5 * pulse;
      // gel bands migrate downward
      gelOffset += dt * 0.04;
      drawGel(gelTex.ctx, gelTex.size, gelOffset); gelTex.tex.needsUpdate = true;
      // progress over cycles
      progress = Math.min(1, (clock / STEP_T / PROGRAM.length) / TOTAL_CYCLES);
    },
  };
  return group;
}

// thin plastic spine for the tube strip
function plasticSpine() {
  return new THREE.MeshStandardMaterial({ color: 0xcfd6da, roughness: 0.5, metalness: 0.0, transparent: true, opacity: 0.7 });
}

export const meta = {
  id: 'stage7-rna',
  label: 'Stage 7 — RNA world',
  title: 'Ribozyme replication assay',
  blurb: 'RNA is dual-role — it stores information AND catalyses (ribozymes). Below the error threshold ε_c it replicates; above it the quasispecies melts down.',
  build,
};
