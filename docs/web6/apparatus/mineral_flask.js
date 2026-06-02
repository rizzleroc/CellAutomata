// Stage 5 — Mineral catalysis · Montmorillonite clay reactor.
//
// Ferris-style surface catalysis: a tall borosilicate beaker holds a settled
// layered bed of Na-montmorillonite clay (stacked dark-ochre discs) under a
// pale supernatant of activated monomers. When running, short RNA-like polymer
// chains (connected beads) slowly grow upward from the clay surface — the
// mineral templating prebiotic polymerisation.

import * as THREE from 'three';
import { part, glassMat, liquidMat, brassMat, V } from './lib.js';

const CLAY_Y = 0.55;       // top of the clay bed
const SOLN_TOP = 3.4;      // supernatant surface
const R = 1.05;            // beaker inner radius

function build() {
  const group = new THREE.Group();
  group.name = 'mineral-flask-1953';

  // ── Tall glass beaker on the bench ────────────────────────────────────────
  const beaker = part(new THREE.CylinderGeometry(R + 0.06, R + 0.06, 4.0, 48, 1, true),
    glassMat(), 'beaker', V(0, 2.05, 0));
  group.add(beaker);
  group.add(part(new THREE.CylinderGeometry(R + 0.06, R + 0.06, 0.12, 48), glassMat(),
    'beaker-floor', V(0, 0.06, 0)));
  // pour lip ring
  const rim = part(new THREE.TorusGeometry(R + 0.06, 0.05, 12, 48), glassMat(), 'beaker-rim', V(0, 4.05, 0));
  rim.rotation.x = Math.PI / 2;
  group.add(rim);

  // ── Settled layered clay bed (montmorillonite) ────────────────────────────
  const clayCols = [0x6b4a1f, 0x7a5526, 0x5f4119, 0x836032, 0x6b4a1f];
  let cy = 0.16;
  for (let i = 0; i < clayCols.length; i++) {
    const h = 0.085 - i * 0.006;
    const disc = part(new THREE.CylinderGeometry(R * 0.98, R * 0.98, h, 40),
      new THREE.MeshStandardMaterial({ color: clayCols[i], roughness: 0.92, metalness: 0.04 }),
      `clay-layer-${i}`, V(0, cy + h / 2, 0));
    group.add(disc);
    cy += h;
  }

  // ── Translucent supernatant solution ──────────────────────────────────────
  const supH = SOLN_TOP - CLAY_Y;
  const supernatant = part(new THREE.CylinderGeometry(R, R, supH, 48),
    liquidMat(0xcfe2d4, { transmission: 0.78, opacity: 0.6 }),
    'supernatant', V(0, CLAY_Y + supH / 2, 0));
  group.add(supernatant);

  // ── Glass stopper on top ──────────────────────────────────────────────────
  group.add(part(new THREE.CylinderGeometry(R * 0.55, R * 0.62, 0.45, 32), glassMat(),
    'stopper', V(0, 4.25, 0)));
  group.add(part(new THREE.SphereGeometry(0.34, 24, 18), glassMat(),
    'stopper-knob', V(0, 4.6, 0)));

  // ── Glass stir rod, leaning in the beaker ─────────────────────────────────
  const rod = part(new THREE.CylinderGeometry(0.05, 0.05, 4.6, 16), glassMat(),
    'stir-rod', V(R * 0.55, 2.4, 0.2));
  rod.rotation.z = 0.16;
  group.add(rod);
  group.add(part(new THREE.SphereGeometry(0.08, 16, 12), glassMat(),
    'stir-rod-tip', V(R * 0.55 + 0.36, 0.7, 0.2)));

  // ── Growing polymer chains (connected beads rising from the clay) ─────────
  const beadMat = new THREE.MeshStandardMaterial({ color: 0xd98c3a, roughness: 0.4, metalness: 0.1, emissive: 0x2a1402 });
  const chains = [];
  const NCHAINS = 9, MAXBEADS = 7;
  for (let c = 0; c < NCHAINS; c++) {
    const ang = (c / NCHAINS) * Math.PI * 2 + 0.4;
    const rad = R * (0.25 + 0.55 * ((c * 7 % 5) / 5));
    const bx = Math.cos(ang) * rad, bz = Math.sin(ang) * rad;
    const beads = [];
    for (let b = 0; b < MAXBEADS; b++) {
      const m = part(new THREE.SphereGeometry(0.07, 12, 10), beadMat, `chain-${c}-bead-${b}`,
        V(bx, CLAY_Y + 0.05 + b * 0.14, bz));
      m.visible = false;
      group.add(m);
      beads.push(m);
    }
    chains.push({ beads, x: bx, z: bz, phase: c * 0.7 });
  }

  // ── Brass clamp boss (period fitting holding the beaker) ──────────────────
  const clampRing = part(new THREE.TorusGeometry(R + 0.18, 0.07, 12, 40), brassMat(), 'clamp-ring', V(0, 2.6, 0));
  clampRing.rotation.x = Math.PI / 2;
  group.add(clampRing);

  group.position.y = 0;

  // ── Animation ─────────────────────────────────────────────────────────────
  let running = true, progress = 0;
  const apply = () => {
    for (const ch of chains) {
      const grown = progress * MAXBEADS;
      for (let b = 0; b < MAXBEADS; b++) {
        ch.beads[b].visible = b < grown;
      }
    }
  };
  apply();

  const anim = {
    setRunning(on) { running = on; },
    getProgress() { return progress; },
    reset() { progress = 0; apply(); },
    update(dt, t) {
      if (running) { progress = Math.min(1, progress + dt / 40); }
      // chains visible per progress; gentle sway from convection
      for (const ch of chains) {
        const grown = progress * MAXBEADS;
        for (let b = 0; b < MAXBEADS; b++) {
          const bead = ch.beads[b];
          bead.visible = b < grown;
          if (bead.visible) {
            const sway = running ? Math.sin(t * 1.2 + ch.phase + b * 0.5) * 0.02 * b : 0;
            bead.position.x = ch.x + sway;
            bead.position.z = ch.z + sway * 0.6;
          }
        }
      }
    },
  };
  group.userData.anim = anim;
  return group;
}

export const meta = {
  id: 'stage5-minerals',
  label: 'Stage 5 — Mineral catalysis',
  title: 'Montmorillonite clay reactor',
  blurb: 'Ferris-style surface catalysis: activated monomers polymerise on a settled bed of Na-montmorillonite clay.',
  build,
};
