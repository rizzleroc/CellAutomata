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

  // ── Dynamic phenomenon layer (all UNNAMED so the parts panel is unchanged) ──
  // The real Ferris-style surface catalysis: monomers localise on the clay and
  // polymerise there ~12× the bulk rate, so small polymer aggregates ACCUMULATE
  // and GROW clinging to the clay surface as the run proceeds. Plus gentle
  // bubbling/precipitation through the supernatant and a slow convective stir.

  // Polymer aggregates nucleating on the clay surface (spawn + grow with run).
  const polyMat = new THREE.MeshStandardMaterial({
    color: 0xc98a44, roughness: 0.5, metalness: 0.08,
    emissive: 0xffb866, emissiveIntensity: 0.0,        // warm glow, ramps with growth
  });
  const NCLUMP = 30;
  const clumps = [];
  for (let i = 0; i < NCLUMP; i++) {
    const m = new THREE.Mesh(new THREE.IcosahedronGeometry(0.06, 0), polyMat);
    m.castShadow = true;
    // each clump nucleates at a fixed spot on the clay bed
    const ang = i * 2.39996;                            // golden-angle spread
    const rad = R * (0.18 + 0.74 * ((i * 13 % 17) / 17));
    const px = Math.cos(ang) * rad, pz = Math.sin(ang) * rad;
    m.position.set(px, CLAY_Y + 0.05, pz);
    m.scale.setScalar(0.0001);
    m.visible = false;
    group.add(m);
    clumps.push({
      mesh: m, x: px, z: pz,
      thr: 0.04 + (i / NCLUMP) * 0.9,                   // progress at which it nucleates
      grow: 0.7 + (i * 7 % 11) / 11 * 0.8,              // mature size multiplier
      phase: i * 0.91,
    });
  }

  // Bubbles / precipitation rising through the supernatant.
  const bubbleMat = new THREE.MeshStandardMaterial({
    color: 0xeaf4ec, roughness: 0.15, metalness: 0.0, transparent: true, opacity: 0.5,
  });
  const NBUB = 22;
  const bubbles = [];
  const bubbleGeo = new THREE.SphereGeometry(0.045, 8, 8);
  for (let i = 0; i < NBUB; i++) {
    const b = new THREE.Mesh(bubbleGeo, bubbleMat);
    const reset = () => {
      const ang = Math.random() * Math.PI * 2, rad = Math.random() * R * 0.85;
      b.userData.x = Math.cos(ang) * rad;
      b.userData.z = Math.sin(ang) * rad;
      b.position.set(b.userData.x, CLAY_Y + Math.random() * 0.25, b.userData.z);
      b.userData.v = 0.3 + Math.random() * 0.5;
      b.userData.s = 0.5 + Math.random() * 0.9;
      b.scale.setScalar(b.userData.s);
    };
    b.userData.reset = reset;
    reset();
    b.position.y = CLAY_Y + Math.random() * (SOLN_TOP - CLAY_Y - 0.1);  // pre-spread
    b.visible = false;
    group.add(b);
    bubbles.push(b);
  }

  // A faint warm catalytic glow seated on the clay surface (grows with run).
  const clayGlow = new THREE.PointLight(0xffb866, 0, 3.2, 2);
  clayGlow.position.set(0, CLAY_Y + 0.12, 0);
  group.add(clayGlow);

  // ── Animation ─────────────────────────────────────────────────────────────
  const stirRodBaseX = rod.position.x, stirRodBaseZ = rod.position.z;
  const supBaseY = supernatant.position.y;
  let running = true, progress = 0;

  const applyChains = () => {
    for (const ch of chains) {
      const grown = progress * MAXBEADS;
      for (let b = 0; b < MAXBEADS; b++) ch.beads[b].visible = b < grown;
    }
  };
  const applyClumps = () => {
    for (const cl of clumps) {
      const on = progress > cl.thr;
      cl.mesh.visible = on;
      if (on) {
        const local = Math.min(1, (progress - cl.thr) / 0.22);   // 0→1 growth ramp
        cl.mesh.scale.setScalar(0.0001 + local * cl.grow);
      } else {
        cl.mesh.scale.setScalar(0.0001);
      }
    }
  };
  applyChains();
  applyClumps();

  const anim = {
    setRunning(on) { running = on; },
    getProgress() { return progress; },
    reset() {
      progress = 0;
      applyChains();
      applyClumps();
      polyMat.emissiveIntensity = 0;
      clayGlow.intensity = 0;
      rod.position.x = stirRodBaseX; rod.position.z = stirRodBaseZ;
      supernatant.position.y = supBaseY;
    },
    update(dt, t) {
      if (running) progress = Math.min(1, progress + dt / 40);

      // Catalytic warmth ramps as polymer mass accumulates (gated on running).
      const heat = running ? progress : 0;
      polyMat.emissiveIntensity = heat * 0.6;
      clayGlow.intensity = heat * (1.3 + Math.sin(t * 3.0) * 0.18);

      // Growing RNA-like chains rising from the clay, with convective sway.
      for (const ch of chains) {
        const grown = progress * MAXBEADS;
        for (let b = 0; b < MAXBEADS; b++) {
          const bead = ch.beads[b];
          bead.visible = b < grown;
          if (bead.visible) {
            const sway = running ? Math.sin(t * 1.4 + ch.phase + b * 0.55) * 0.05 * (b + 1) : 0;
            bead.position.x = ch.x + sway;
            bead.position.z = ch.z + Math.cos(t * 1.1 + ch.phase + b * 0.5) * 0.04 * (b + 1) * (running ? 1 : 0);
            bead.position.y = CLAY_Y + 0.05 + b * 0.14 + (running ? Math.sin(t * 2.0 + b) * 0.012 : 0);
          }
        }
      }

      // Polymer aggregates clinging to the clay: nucleate, grow, and breathe.
      for (const cl of clumps) {
        const on = progress > cl.thr;
        cl.mesh.visible = on;
        if (!on) { cl.mesh.scale.setScalar(0.0001); continue; }
        const local = Math.min(1, (progress - cl.thr) / 0.22);
        const breathe = running ? 1 + Math.sin(t * 2.4 + cl.phase) * 0.12 : 1;
        cl.mesh.scale.setScalar((0.0001 + local * cl.grow) * breathe);
        cl.mesh.rotation.y = running ? t * 0.6 + cl.phase : cl.mesh.rotation.y;
        cl.mesh.rotation.x = running ? Math.sin(t * 0.8 + cl.phase) * 0.3 : cl.mesh.rotation.x;
        // tiny convective jitter clinging to the surface
        cl.mesh.position.x = cl.x + (running ? Math.sin(t * 1.7 + cl.phase) * 0.02 : 0);
        cl.mesh.position.z = cl.z + (running ? Math.cos(t * 1.5 + cl.phase) * 0.02 : 0);
      }

      // Bubbles / precipitation rising through the supernatant (calm when stopped).
      for (const b of bubbles) {
        if (!running) { b.visible = false; continue; }
        b.visible = true;
        b.position.y += b.userData.v * dt;
        // gentle helical drift on the way up
        b.position.x = b.userData.x + Math.sin(t * 2.2 + b.userData.s * 6) * 0.05;
        b.position.z = b.userData.z + Math.cos(t * 1.9 + b.userData.s * 6) * 0.05;
        if (b.position.y > SOLN_TOP - 0.05) b.userData.reset();
      }

      // Slow convective stir: the glass rod sweeps a small circle while running;
      // the supernatant surface bobs faintly with the convection.
      if (running) {
        rod.position.x = stirRodBaseX + Math.cos(t * 0.9) * 0.1;
        rod.position.z = stirRodBaseZ + Math.sin(t * 0.9) * 0.1;
        supernatant.position.y = supBaseY + Math.sin(t * 1.3) * 0.015;
      } else {
        rod.position.x = stirRodBaseX;
        rod.position.z = stirRodBaseZ;
        supernatant.position.y = supBaseY;
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
