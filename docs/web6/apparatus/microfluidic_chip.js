// Stage 10 — Microfluidic protocell-selection chip.
//
// A flat clear acrylic/glass chip on a small steel stage, an etched serpentine
// channel running across it, brass inlet/outlet ports with fine tubing, and a
// grid array of small droplet wells. Each well is a disc whose colour encodes
// fitness on a red→green map. A wave of "selection" sweeps the array as fitter
// protocell lineages outcompete and take over wells (Eigen error threshold +
// hypercycle selection). progress = mean fitness across the array.

import * as THREE from 'three';
import { glassMat, steelMat, brassMat, rubberMat, part, V } from './lib.js';

export function build() {
  const group = new THREE.Group();
  group.name = 'microfluidic-chip';

  const cx = 0, cy = 1.0;

  // ── Stage: a low steel platform the chip rests on ─────────────────────────
  group.add(part(new THREE.BoxGeometry(5.2, 0.4, 3.4), steelMat(), 'stage', V(cx, 0.2, 0)));
  group.add(part(new THREE.BoxGeometry(5.0, 0.06, 3.2), steelMat(), 'stage-top', V(cx, 0.42, 0)));

  // ── Chip body: thin clear glass/acrylic slab ──────────────────────────────
  const chipMat = new THREE.MeshPhysicalMaterial({
    color: 0xeaf2f4, metalness: 0, roughness: 0.08, transmission: 0.85,
    thickness: 0.4, ior: 1.49, transparent: true, clearcoat: 0.6, clearcoatRoughness: 0.08,
  });
  const chip = part(new THREE.BoxGeometry(4.4, 0.3, 2.8), chipMat, 'chip-body', V(cx, cy, 0));
  group.add(chip);

  // ── Etched serpentine channel (thin dark glass tubes on the chip face) ────
  const channelGroup = new THREE.Group(); channelGroup.name = 'channel';
  const chanMat = new THREE.MeshPhysicalMaterial({
    color: 0x6fb6c8, roughness: 0.2, transmission: 0.5, thickness: 0.1, ior: 1.34, transparent: true,
  });
  const pts = [];
  const rows = 5, span = 3.4, top = cy + 0.17;
  for (let r = 0; r < rows; r++) {
    const x0 = -span / 2, x1 = span / 2;
    const z = -1.0 + r * 0.5;
    if (r % 2 === 0) { pts.push(V(x0, top, z), V(x1, top, z)); }
    else { pts.push(V(x1, top, z), V(x0, top, z)); }
  }
  const curve = new THREE.CatmullRomCurve3(pts);
  const channel = new THREE.Mesh(new THREE.TubeGeometry(curve, 200, 0.05, 12, false), chanMat);
  channel.name = 'channel'; channelGroup.add(channel);
  group.add(channelGroup);

  // ── Inlet / outlet ports (brass) + fine tubing ────────────────────────────
  const inlet = part(new THREE.CylinderGeometry(0.13, 0.16, 0.36, 20), brassMat(),
    'inlet', V(-span / 2, cy + 0.28, -1.0));
  group.add(inlet);
  const outlet = part(new THREE.CylinderGeometry(0.13, 0.16, 0.36, 20), brassMat(),
    'outlet', V(span / 2, cy + 0.28, 1.0));
  group.add(outlet);
  const tubeMat = rubberMat(0x33312e);
  for (const [px, pz, sgn] of [[-span / 2, -1.0, -1], [span / 2, 1.0, 1]]) {
    const tcurve = new THREE.CatmullRomCurve3([
      V(px, cy + 0.46, pz), V(px + sgn * 0.4, cy + 0.9, pz + sgn * 0.3),
      V(px + sgn * 1.3, cy + 1.1, pz + sgn * 0.6),
    ]);
    const t = new THREE.Mesh(new THREE.TubeGeometry(tcurve, 40, 0.06, 10, false), tubeMat);
    t.name = 'tubing'; group.add(t);
  }

  // ── Droplet-well array: grid of fitness-coloured discs ────────────────────
  const COLS = 8, ROWS = 5;
  const wells = [];
  const wellArray = new THREE.Group(); wellArray.name = 'well-array';
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const fitness = 0.05 + Math.random() * 0.15;        // start low (red)
      const mat = new THREE.MeshStandardMaterial({
        color: 0x000000, emissive: 0x000000, roughness: 0.3, metalness: 0.0,
      });
      const wx = cx - 1.9 + c * 0.54;
      const wz = -1.1 + r * 0.55;
      const w = part(new THREE.CylinderGeometry(0.2, 0.2, 0.08, 20), mat,
        `well-${r}-${c}`, V(wx, cy + 0.18, wz));
      w.userData = { fitness, x: c / (COLS - 1) };
      wellArray.add(w);
      wells.push(w);
    }
  }
  group.add(wellArray);

  function colorWell(w) {
    const f = w.userData.fitness;                          // red(0)→green(1)
    const rr = Math.min(1, 2 * (1 - f)), gg = Math.min(1, 2 * f);
    w.material.color.setRGB(rr, gg, 0.1);
    w.material.emissive.setRGB(rr * 0.25 * f, gg * 0.35 * f, 0.0);
  }
  wells.forEach(colorWell);

  group.position.y = 0;

  // ── Animation: a selection wave sweeps left→right; fitter lineages win ─────
  let running = true, progress = 0, front = 0;
  function meanFitness() { return wells.reduce((s, w) => s + w.userData.fitness, 0) / wells.length; }
  function resetWells() {
    front = 0;
    for (const w of wells) { w.userData.fitness = 0.05 + Math.random() * 0.15; colorWell(w); }
  }

  group.userData.anim = {
    setRunning(on) { running = on; },
    getProgress() { return progress; },
    reset() { progress = 0; resetWells(); },
    update(dt, t) {
      if (!running) return;
      front = Math.min(1.15, front + dt * 0.07);            // selection front advances
      for (const w of wells) {
        const reached = w.userData.x <= front;
        if (reached) {
          // fitter lineages climb toward green; small jitter for "competition"
          const target = 0.85 + 0.12 * Math.sin(w.userData.x * 9 + 2);
          w.userData.fitness += (target - w.userData.fitness) * Math.min(1, dt * 1.4);
        }
        colorWell(w);
      }
      progress = Math.min(1, meanFitness());
    },
  };

  return group;
}

export const meta = {
  id: 'stage10-selection',
  label: 'Stage 10 — Protocell selection',
  title: 'Microfluidic culture chip',
  blurb: 'Eigen error threshold + hypercycle selection across a droplet array. '
       + 'Fitter protocell lineages outcompete and take over wells.',
  build,
};
