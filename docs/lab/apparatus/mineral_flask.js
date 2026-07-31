// Stage 5 — Mineral catalysis · Montmorillonite clay reactor.
//
// Ferris-style surface catalysis: a tall borosilicate beaker holds a settled
// layered bed of Na-montmorillonite clay (stacked dark-ochre discs) under a
// pale supernatant of activated monomers. When running, short RNA-like polymer
// chains (connected beads) slowly grow upward from the clay surface — the
// mineral templating prebiotic polymerisation.

import * as THREE from 'three';
import { part, glassMat, liquidMat, brassMat, bubbleColumn, liquidVolume, V } from './lib.js';

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

  // ── Translucent supernatant — a REAL filled volume with a flat rippling
  //    meniscus (the cylinder helper ties fill height to 2·radius, so a
  //    non-uniform group scale.y stretches it up the beaker; radius stays true).
  const supH = SOLN_TOP - CLAY_Y;
  const supernatant = liquidVolume(R, 0.98,
    liquidMat(0xcfe2d4, { transmission: 0.78 }),
    { shape: 'cylinder', name: 'supernatant' });
  supernatant.group.scale.y = supH / (2 * R);
  supernatant.group.position.set(0, CLAY_Y + supH / 2, 0);
  group.add(supernatant.group);

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

  // Mineral effervescence rising through the supernatant — the shared
  // bubbleColumn (opaque Fresnel-rimmed beads the liquid refracts, fixed-count
  // pool so Run/Stop stays a real state for the anim gate).
  const boil = bubbleColumn({
    center: V(0, (CLAY_Y + SOLN_TOP) / 2, 0), radius: R * 0.7,
    floorY: CLAY_Y + 0.1, topY: SOLN_TOP - 0.1,
    count: 24, rMin: 0.03, rMax: 0.06, rise: 0.4, lateral: 0.05, grow: 0.3,
    color: 0xeaf4ec, name: 'mineral-bubbles',
  });
  group.add(boil.group);

  // A faint warm catalytic glow seated on the clay surface (grows with run).
  const clayGlow = new THREE.PointLight(0xffb866, 0, 3.2, 2);
  clayGlow.position.set(0, CLAY_Y + 0.12, 0);
  group.add(clayGlow);

  // ── Animation ─────────────────────────────────────────────────────────────
  const stirRodBaseX = rod.position.x, stirRodBaseZ = rod.position.z;
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
    setRunning(on) { running = on; boil.setRunning(on); },
    getProgress() { return progress; },
    reset() {
      progress = 0;
      applyChains();
      applyClumps();
      polyMat.emissiveIntensity = 0;
      clayGlow.intensity = 0;
      rod.position.x = stirRodBaseX; rod.position.z = stirRodBaseZ;
      supernatant.setLevel(0.98);
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

      // Mineral effervescence rising through the supernatant (calm when stopped).
      if (running) boil.update(dt, t);

      // Slow convective stir: the glass rod sweeps a small circle while running;
      // the supernatant surface ripples faintly with the convection.
      if (running) {
        rod.position.x = stirRodBaseX + Math.cos(t * 0.9) * 0.1;
        rod.position.z = stirRodBaseZ + Math.sin(t * 0.9) * 0.1;
        supernatant.shimmer(t);
      } else {
        rod.position.x = stirRodBaseX;
        rod.position.z = stirRodBaseZ;
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
