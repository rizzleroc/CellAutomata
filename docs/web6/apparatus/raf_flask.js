// Stage 2 — Autocatalytic sets (RAF) · reaction flask + magnetic stir plate.
//
// A round-bottom flask of faintly opalescent solution on a Bakelite magnetic
// stir plate; a PTFE stir bar spins up a vortex while a thermometer reads the
// neck. When running, a handful of glowing catalyst "nodes" hang suspended in
// the liquid, linked by thin edges and slowly rotating — the closure of a
// Kauffman / Hordijk-Steel reflexively-autocatalytic set. Every part is named.

import * as THREE from 'three';
import { glassMat, steelMat, brassMat, bakeliteMat, liquidMat, emissiveMat, flask, part, V } from './lib.js';

export function build() {
  const group = new THREE.Group();
  group.name = 'raf-flask';

  const plateTop = 0.62;      // top surface of the stir plate
  const flaskC = V(0, plateTop + 0.95, 0);
  const R = 0.95;

  // ── Magnetic stir plate: boxy Bakelite base + steel top plate ─────────────
  const baseBox = part(new THREE.BoxGeometry(2.2, 0.55, 1.8), bakeliteMat(0x201813),
    'stir-plate', V(0, 0.3, 0));
  group.add(baseBox);
  const topPlate = part(new THREE.CylinderGeometry(0.95, 0.95, 0.08, 48), steelMat(),
    'stir-plate-top', V(0, plateTop, 0));
  topPlate.name = 'stir-plate';
  group.add(topPlate);
  // brass speed knob + engraved dial
  const knob = part(new THREE.CylinderGeometry(0.16, 0.18, 0.16, 24), brassMat(),
    'speed-knob', V(0.78, 0.42, 0.92));
  knob.rotation.x = Math.PI / 2;
  group.add(knob);
  const dial = part(new THREE.CylinderGeometry(0.24, 0.24, 0.02, 24),
    new THREE.MeshStandardMaterial({ color: 0xe8e2d2, roughness: 0.5 }), 'speed-dial', V(0.42, 0.42, 0.901));
  dial.rotation.x = Math.PI / 2;
  group.add(dial);

  // ── Flask + opalescent solution ───────────────────────────────────────────
  const fl = flask(R, 'flask', 0.6);
  fl.position.copy(flaskC);
  group.add(fl);
  const sol = part(new THREE.SphereGeometry(R * 0.9, 40, 28),
    liquidMat(0xcfe0d8, { transmission: 0.7, roughness: 0.12, opacity: 0.85 }), 'solution', flaskC.clone());
  sol.scale.y = 0.62; sol.position.y = flaskC.y - 0.34;
  group.add(sol);

  // ── Stir bar (PTFE) at the flask floor ────────────────────────────────────
  const barPivot = new THREE.Group();
  barPivot.position.set(flaskC.x, flaskC.y - R * 0.78, flaskC.z);
  const bar = part(new THREE.CapsuleGeometry(0.07, 0.5, 6, 12),
    new THREE.MeshStandardMaterial({ color: 0xeeeeee, roughness: 0.4 }), 'stir-bar');
  bar.rotation.z = Math.PI / 2;
  barPivot.add(bar);
  group.add(barPivot);

  // ── Thermometer in the neck ───────────────────────────────────────────────
  const thermo = part(new THREE.CylinderGeometry(0.035, 0.035, 1.4, 16), glassMat(),
    'thermometer', V(flaskC.x + 0.12, flaskC.y + R * 0.9, 0));
  thermo.rotation.z = -0.18;
  group.add(thermo);
  const merc = part(new THREE.CylinderGeometry(0.018, 0.018, 0.9, 12), emissiveMat(0xcc3322),
    'thermometer-fluid', V(flaskC.x + 0.1, flaskC.y + R * 0.82, 0.001));
  merc.name = 'thermometer'; merc.rotation.z = -0.18;
  group.add(merc);

  // ── Catalyst nodes + links suspended in the liquid ────────────────────────
  const nodePivot = new THREE.Group();
  nodePivot.position.copy(flaskC);
  group.add(nodePivot);
  const nodeColors = [0xffd24a, 0x7df0c0, 0xc77dff, 0x5ab8ff, 0xff8a5a];
  const nodePos = [];
  const nodes = [];
  for (let i = 0; i < 5; i++) {
    const a = i / 5 * Math.PI * 2;
    const p = V(Math.cos(a) * R * 0.5, (i % 2 ? 0.25 : -0.2), Math.sin(a) * R * 0.5);
    nodePos.push(p);
    const n = part(new THREE.SphereGeometry(0.1, 16, 12), emissiveMat(nodeColors[i]), `node-${i}`, p.clone());
    nodePivot.add(n);
    nodes.push(n);
  }
  // directed links closing the set
  const linkMat = new THREE.LineBasicMaterial({ color: 0x9fffe0, transparent: true, opacity: 0.7 });
  const linkPairs = [[0, 2], [2, 4], [4, 1], [1, 3], [3, 0]];
  const links = [];
  for (let i = 0; i < linkPairs.length; i++) {
    const [a, b] = linkPairs[i];
    const geo = new THREE.BufferGeometry().setFromPoints([nodePos[a], nodePos[b]]);
    const ln = new THREE.Line(geo, linkMat);
    ln.name = `link-${i}`;
    nodePivot.add(ln);
    links.push(ln);
  }

  group.position.y = 0;

  // ── Animation ──────────────────────────────────────────────────────────────
  let running = true, progress = 0;
  group.userData.anim = {
    setRunning(on) {
      running = on;
      const v = on;
      for (const n of nodes) n.visible = v;
      for (const l of links) l.visible = v;
    },
    getProgress() { return progress; },
    reset() { progress = 0; barPivot.rotation.y = 0; nodePivot.rotation.y = 0; },
    update(dt, t) {
      if (!running) return;
      progress = Math.min(1, progress + dt / 25);
      barPivot.rotation.y += dt * 14;          // fast stir bar
      nodePivot.rotation.y += dt * 0.5;        // slow node rotation
      // vortex dimple: dip the solution centre and rock it slightly
      sol.scale.y = 0.62 - 0.05 * Math.abs(Math.sin(t * 7));
      // node glow pulse as the set "closes"
      const pulse = 0.85 + 0.15 * Math.sin(t * 3);
      for (const n of nodes) n.scale.setScalar(pulse);
      linkMat.opacity = 0.4 + 0.4 * progress;
    },
  };

  return group;
}

export const meta = {
  id: 'stage2-raf',
  label: 'Stage 2 — Autocatalytic sets',
  title: 'Reaction flask + magnetic stir plate',
  blurb: 'A well-stirred flask of mutually-catalysing species — a Kauffman/Hordijk-Steel RAF. '
       + 'Catalyst nodes glow and link as the autocatalytic set closes.',
  build,
};
