// Stage 10 — Microfluidic protocell-selection chip.
//
// A flat clear acrylic/glass chip on a small steel stage, an etched serpentine
// channel running across it, brass inlet/outlet ports with fine tubing, and a
// grid array of small droplet wells. Each well is a disc whose colour encodes
// fitness on a red→green map. A wave of "selection" sweeps the array as fitter
// protocell lineages outcompete and take over wells (Eigen error threshold +
// hypercycle selection). progress = mean fitness across the array.
//
// RUNNING the experiment makes the biology visible: a translucent SELECTION
// FRONT sweeps left→right; inside each well a protocell GROWS (scale pulse) and
// periodically DIVIDES (a daughter buds off, then merges back); fluid FLOWS
// through the serpentine channel as a travelling teal highlight. Wells brighten
// with fitness. Pressing Stop freezes every protocell, the front and the flow.

import * as THREE from 'three';
import { glassMat, steelMat, brassMat, rubberMat, part, V } from './lib.js';

// Emissive/light palette (teal / magenta / warm only).
const TEAL = 0x3fe0d0, MAGENTA = 0xd77bff, WARM = 0xffb866;

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
  const wellY = cy + 0.18;
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const fitness = 0.05 + Math.random() * 0.15;        // start low (red)
      const mat = new THREE.MeshStandardMaterial({
        color: 0x000000, emissive: 0x000000, roughness: 0.3, metalness: 0.0,
      });
      const wx = cx - 1.9 + c * 0.54;
      const wz = -1.1 + r * 0.55;
      const w = part(new THREE.CylinderGeometry(0.2, 0.2, 0.08, 20), mat,
        `well-${r}-${c}`, V(wx, wellY, wz));
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

  // ── Protocells: one growing/dividing membrane sphere per well (UNNAMED) ────
  // Each rides above its well; scale tracks a growth phase, and on each division
  // a daughter cell buds out sideways then merges back (visible mitosis).
  const cellMat = () => new THREE.MeshStandardMaterial({
    color: 0xdfeef0, emissive: TEAL, emissiveIntensity: 0.0,
    roughness: 0.35, metalness: 0.0, transparent: true, opacity: 0.85,
  });
  const protocells = [];
  for (const w of wells) {
    const cellGroup = new THREE.Group();
    cellGroup.position.set(w.position.x, wellY + 0.12, w.position.z);
    const body = new THREE.Mesh(new THREE.SphereGeometry(0.12, 16, 12), cellMat());
    const daughter = new THREE.Mesh(new THREE.SphereGeometry(0.12, 16, 12), cellMat());
    daughter.visible = false;
    cellGroup.add(body); cellGroup.add(daughter);
    group.add(cellGroup);
    protocells.push({
      group: cellGroup, body, daughter, well: w,
      grow: Math.random(),                       // growth-cycle phase 0..1
      rate: 0.5 + Math.random() * 0.5,           // growth speed
      divPhase: -1,                              // ≥0 while a division is animating
      phase: Math.random() * Math.PI * 2,        // wobble offset
    });
  }

  // ── Selection front: translucent magenta sweep plane crossing the array ───
  const frontMat = new THREE.MeshBasicMaterial({
    color: MAGENTA, transparent: true, opacity: 0.0, side: THREE.DoubleSide,
    depthWrite: false,
  });
  const frontMesh = new THREE.Mesh(new THREE.PlaneGeometry(0.18, 3.0), frontMat);
  frontMesh.rotation.x = Math.PI / 2;            // lie flat, span across z
  frontMesh.position.set(cx - 2.1, wellY + 0.16, 0);
  group.add(frontMesh);
  // a soft light riding the front so the sweep reads as "energy"
  const frontLight = new THREE.PointLight(MAGENTA, 0, 2.2, 2);
  frontLight.position.set(cx - 2.1, wellY + 0.5, 0);
  group.add(frontLight);

  // ── Fluid flow: a travelling teal highlight bead in the serpentine channel ─
  const flowMat = new THREE.MeshBasicMaterial({ color: TEAL, transparent: true, opacity: 0.0 });
  const flowBead = new THREE.Mesh(new THREE.SphereGeometry(0.07, 12, 10), flowMat);
  flowBead.position.copy(curve.getPointAt(0));
  group.add(flowBead);
  const flowGlow = new THREE.PointLight(TEAL, 0, 1.4, 2);
  flowGlow.position.copy(flowBead.position);
  group.add(flowGlow);

  group.position.y = 0;

  // ── Animation: selection front sweeps; protocells grow/divide; fluid flows ─
  const X0 = cx - 2.1, X1 = cx + 2.1;            // front travel range (chip width)
  let running = true, progress = 0, front = 0, flow = 0;

  function meanFitness() { return wells.reduce((s, w) => s + w.userData.fitness, 0) / wells.length; }

  function resetCells() {
    for (const pc of protocells) {
      pc.grow = Math.random();
      pc.divPhase = -1;
      pc.daughter.visible = false;
      pc.group.scale.setScalar(1);
      pc.body.position.set(0, 0, 0);
      pc.daughter.position.set(0, 0, 0);
      pc.body.material.emissiveIntensity = 0;
      pc.daughter.material.emissiveIntensity = 0;
    }
  }

  function resetWells() {
    front = 0; flow = 0;
    for (const w of wells) { w.userData.fitness = 0.05 + Math.random() * 0.15; colorWell(w); }
    resetCells();
    frontMat.opacity = 0; frontLight.intensity = 0;
    flowMat.opacity = 0; flowGlow.intensity = 0;
    frontMesh.position.x = X0; frontLight.position.x = X0;
  }

  group.userData.anim = {
    setRunning(on) { running = on; },
    getProgress() { return progress; },
    reset() { progress = 0; resetWells(); },
    update(dt, t) {
      // Idle ⇒ everything calm and frozen (no transforms, lights off).
      if (!running) {
        frontMat.opacity = 0; frontLight.intensity = 0;
        flowMat.opacity = 0; flowGlow.intensity = 0;
        return;
      }

      // ── Selection front advances left→right across the array ──────────────
      front = Math.min(1.15, front + dt * 0.07);
      const fx = X0 + (X1 - X0) * Math.min(1, front);
      frontMesh.position.x = fx;
      frontLight.position.x = fx;
      const frontPulse = 0.55 + 0.45 * Math.sin(t * 6);
      frontMat.opacity = front < 1 ? 0.5 * frontPulse : 0.0;
      frontLight.intensity = front < 1 ? 1.6 * frontPulse : 0.0;

      // ── Fluid flows through the serpentine channel (looping highlight) ─────
      flow = (flow + dt * 0.22) % 1;
      const fp = curve.getPointAt(flow);
      flowBead.position.copy(fp);
      flowGlow.position.copy(fp);
      const flowPulse = 0.6 + 0.4 * Math.sin(t * 9);
      flowMat.opacity = 0.85 * flowPulse;
      flowGlow.intensity = 1.3 * flowPulse;
      flowBead.scale.setScalar(0.8 + 0.3 * flowPulse);

      // ── Per-well selection + protocell growth / division ──────────────────
      for (const pc of protocells) {
        const w = pc.well;
        const reached = w.userData.x <= front;
        if (reached) {
          // fitter lineages climb toward green; small jitter for "competition"
          const target = 0.85 + 0.12 * Math.sin(w.userData.x * 9 + 2);
          w.userData.fitness += (target - w.userData.fitness) * Math.min(1, dt * 1.4);
        }
        colorWell(w);

        const f = w.userData.fitness;

        // Growth cycle: fitter cells grow faster; completing a cycle triggers a
        // division. While running, the membrane visibly breathes.
        if (pc.divPhase < 0) {
          pc.grow += dt * pc.rate * (0.35 + f);          // fitness accelerates growth
          if (pc.grow >= 1) { pc.grow = 0; pc.divPhase = 0; }   // begin mitosis
        }

        // Size scales with fitness + growth phase + a gentle breathing wobble.
        const breathe = 0.04 * Math.sin(t * 3 + pc.phase);
        const base = 0.5 + 0.7 * f;                      // fitter ⇒ bigger colony
        const gscale = base * (0.85 + 0.25 * pc.grow) + breathe;
        pc.group.scale.setScalar(Math.max(0.2, gscale));

        // Membrane glow rises with fitness (teal life-signal).
        const glow = 0.15 + 0.85 * f;
        pc.body.material.emissiveIntensity = glow;

        // Division animation: daughter buds out along +x, then merges back.
        if (pc.divPhase >= 0) {
          pc.divPhase = Math.min(1, pc.divPhase + dt * 1.6);
          pc.daughter.visible = true;
          pc.daughter.material.emissiveIntensity = glow;
          // bud out (0→0.5) then snap back together (0.5→1)
          const sep = Math.sin(pc.divPhase * Math.PI) * 0.16;
          pc.body.position.set(-sep, 0, 0);
          pc.daughter.position.set(sep, 0, 0);
          const d = 0.7 + 0.3 * Math.sin(pc.divPhase * Math.PI);
          pc.daughter.scale.setScalar(d);
          if (pc.divPhase >= 1) {                        // division complete
            pc.divPhase = -1;
            pc.daughter.visible = false;
            pc.body.position.set(0, 0, 0);
            pc.daughter.position.set(0, 0, 0);
          }
        }
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
