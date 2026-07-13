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
  const nodeColors = [0xffd24a, 0x7df0c0, 0xc77dff, 0x3fe0d0, 0xffb866];
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

  // ── Dynamic phenomena (all UNNAMED so the parts panel ignores them) ─────────
  const solTopY = flaskC.y - 0.34 + R * 0.9 * 0.62;   // approx solution surface height
  const solSurfR = R * 0.78;                            // radius of the surface disc

  // Stir VORTEX: an inverted cone dimpling the solution centre + a faint swirl
  // ring riding the surface. Spins with the bar; depth tracks stir speed.
  const vortexPivot = new THREE.Group();
  vortexPivot.position.set(flaskC.x, solTopY, flaskC.z);
  group.add(vortexPivot);
  const vortexMat = liquidMat(0xcfe0d8, { transmission: 0.7, roughness: 0.1, opacity: 0.9 });
  const vortexBase = solTopY + 0.02;
  const vortex = new THREE.Mesh(new THREE.ConeGeometry(solSurfR * 0.46, 0.5, 28, 1, true), vortexMat);
  vortex.position.y = -0.23;            // tip points down into the liquid
  vortexPivot.add(vortex);
  // surface swirl ring (teal-tinted) tracing the rotating dimple lip
  const swirlMat = new THREE.MeshBasicMaterial({ color: 0x3fe0d0, transparent: true, opacity: 0.0 });
  const swirl = new THREE.Mesh(new THREE.TorusGeometry(solSurfR * 0.5, 0.022, 10, 36), swirlMat);
  swirl.rotation.x = Math.PI / 2;
  vortexPivot.add(swirl);

  // Rising reaction BUBBLES, born at the stir bar, lofting to the surface.
  const bubbleMat = new THREE.MeshBasicMaterial({ color: 0xffb866, transparent: true, opacity: 0.0 });
  const bubbleFloorY = flaskC.y - R * 0.7;
  const bubbles = [];
  for (let i = 0; i < 22; i++) {
    const b = new THREE.Mesh(new THREE.SphereGeometry(0.026 + Math.random() * 0.022, 8, 6), bubbleMat.clone());
    b.userData.reset = () => {
      const a = Math.random() * Math.PI * 2;
      const rr = Math.random() * solSurfR * 0.7;
      b.userData.x = flaskC.x + Math.cos(a) * rr;
      b.userData.z = flaskC.z + Math.sin(a) * rr;
      b.userData.swirlA = a;
      b.userData.rad = rr;
      b.position.set(b.userData.x, bubbleFloorY, b.userData.z);
      b.userData.v = 0.35 + Math.random() * 0.5;
      b.userData.wob = Math.random() * Math.PI * 2;
    };
    b.userData.reset();
    b.position.y = bubbleFloorY + Math.random() * (solTopY - bubbleFloorY);  // pre-fill column
    group.add(b);
    bubbles.push(b);
  }

  group.position.y = 0;

  // ── Animation ──────────────────────────────────────────────────────────────
  let running = true, progress = 0;
  // base emissive colour per node, so we can pulse brightness without losing hue
  const nodeBase = nodes.map((n) => n.material.color.clone());
  group.userData.anim = {
    setRunning(on) {
      running = on;
      const v = on;
      for (const n of nodes) n.visible = v;
      for (const l of links) l.visible = v;
      vortexPivot.visible = v;
      for (const b of bubbles) b.visible = v;
      if (!on) {
        // settle the surface flat and rest the nodes at their base glow
        sol.scale.y = 0.62;
        for (let i = 0; i < nodes.length; i++) {
          nodes[i].scale.setScalar(1);
          nodes[i].material.color.copy(nodeBase[i]);
        }
      }
    },
    getProgress() { return progress; },
    reset() {
      progress = 0;
      barPivot.rotation.y = 0;
      nodePivot.rotation.y = 0;
      vortexPivot.rotation.y = 0;
      sol.scale.y = 0.62;
      for (const b of bubbles) b.userData.reset();
    },
    update(dt, t) {
      if (!running) return;
      progress = Math.min(1, progress + dt / 25);
      barPivot.rotation.y += dt * 7;           // calm stir bar (visibly turns)
      nodePivot.rotation.y += dt * 0.5;        // slow node rotation
      vortexPivot.rotation.y += dt * 4.5;      // swirl tracks the stir bar

      // vortex dimple: deepen as stir spins up, with a small surface wobble
      const dip = 0.04 + 0.03 * Math.abs(Math.sin(t * 3.5));
      sol.scale.y = 0.62 - dip;
      vortexPivot.position.y = solTopY - dip * R * 0.9 * 0.55;
      vortex.scale.y = 1 + dip * 4;            // dimple grows with the dip
      swirlMat.opacity = 0.25 + 0.2 * Math.abs(Math.sin(t * 3.5));

      // rising reaction bubbles, spiralling up the vortex toward the surface
      for (const b of bubbles) {
        b.userData.wob += dt * 3;
        b.userData.swirlA += dt * 1.75;         // curl with the swirl
        b.position.y += b.userData.v * dt;
        const climb = (b.position.y - bubbleFloorY) / Math.max(0.001, solTopY - bubbleFloorY);
        const rad = b.userData.rad * (0.4 + 0.6 * climb);
        b.position.x = flaskC.x + Math.cos(b.userData.swirlA) * rad + Math.sin(b.userData.wob) * 0.012;
        b.position.z = flaskC.z + Math.sin(b.userData.swirlA) * rad + Math.cos(b.userData.wob) * 0.012;
        const mat = b.material;
        mat.opacity = 0.55 * Math.min(1, climb * 2) * (1 - Math.max(0, climb - 0.85) / 0.15);
        if (b.position.y > solTopY) b.userData.reset();
      }

      // node glow pulses, staggered, brightening toward catalytic closure
      const closeGlow = 0.4 + 0.6 * progress;   // whole set brightens as it closes
      for (let i = 0; i < nodes.length; i++) {
        const ph = i / nodes.length * Math.PI * 2;
        const beat = 0.5 + 0.5 * Math.sin(t * 3 + ph);
        nodes[i].scale.setScalar(0.85 + 0.25 * beat * closeGlow);
        const g = (0.55 + 0.45 * beat) * closeGlow;
        nodes[i].material.color.copy(nodeBase[i]).multiplyScalar(0.6 + g);
      }
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
