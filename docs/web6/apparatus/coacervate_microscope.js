// Stage 9 — Oparin coacervates under the microscope.
//
// A heavy brass-and-steel research microscope: cast foot, curved arm, body
// tube, objective turret, mechanical stage with a glass slide + coverslip,
// coarse/fine focus knobs and a sub-stage illuminator. A separate "eyepiece
// view" disc shows a lib.makeDynamicTexture field of coacervate droplets that
// COALESCE and COARSEN over time (small circles merging into larger ones) —
// liquid–liquid phase separation, à la Cahn–Hilliard. Brassier and warmer than
// the phase-contrast vesicle scope, and the droplets merge rather than drift.

import * as THREE from 'three';
import { glassMat, steelMat, brassMat, bakeliteMat, part, makeDynamicTexture, V } from './lib.js';

export function build() {
  const group = new THREE.Group();
  group.name = 'coacervate-microscope';

  // ── Foot: heavy cast horseshoe base ───────────────────────────────────────
  const foot = part(new THREE.CylinderGeometry(1.1, 1.25, 0.32, 48), steelMat(),
    'microscope-foot', V(0, 0.16, 0));
  foot.scale.z = 0.7; group.add(foot);
  group.add(part(new THREE.CylinderGeometry(0.28, 0.34, 0.5, 32), bakeliteMat(0x2a221a),
    'microscope-pillar', V(0, 0.55, 0.15)));

  // ── Arm: curved brass limb carrying the body tube ─────────────────────────
  const arm = part(new THREE.BoxGeometry(0.42, 2.4, 0.5), brassMat(), 'arm', V(0, 1.9, 0.05));
  arm.rotation.z = 0.12; group.add(arm);
  group.add(part(new THREE.CylinderGeometry(0.26, 0.26, 0.6, 24), brassMat(),
    'arm-elbow', V(-0.18, 3.05, 0.05)));

  // ── Body tube + objective turret ──────────────────────────────────────────
  const tube = part(new THREE.CylinderGeometry(0.21, 0.21, 1.5, 28), brassMat(),
    'body-tube', V(0.05, 3.55, 0.42));
  tube.rotation.x = -0.04; group.add(tube);
  const turret = part(new THREE.CylinderGeometry(0.34, 0.34, 0.26, 24), steelMat(),
    'objective-turret', V(0.05, 2.74, 0.45));
  group.add(turret);
  for (let i = 0; i < 3; i++) {
    const a = -0.6 + i * 0.6;
    const obj = part(new THREE.CylinderGeometry(0.06, 0.1, 0.36, 16), brassMat(),
      `objective-${i}`, V(0.05 + Math.sin(a) * 0.24, 2.5, 0.45 + Math.cos(a) * 0.24));
    obj.name = 'objective-turret'; group.add(obj);
  }

  // ── Mechanical stage with slide + coverslip ───────────────────────────────
  const stage = part(new THREE.BoxGeometry(1.5, 0.12, 1.2), steelMat(), 'stage', V(0.05, 2.05, 0.55));
  group.add(stage);
  const slide = part(new THREE.BoxGeometry(0.9, 0.04, 0.5), glassMat(), 'slide', V(0.05, 2.13, 0.55));
  group.add(slide);
  const coverslip = part(new THREE.BoxGeometry(0.34, 0.015, 0.34), glassMat(),
    'coverslip', V(0.05, 2.16, 0.55));
  group.add(coverslip);

  // ── Focus knobs (coarse big, fine small) on the pillar ────────────────────
  const focusCoarse = part(new THREE.CylinderGeometry(0.3, 0.3, 0.18, 28), bakeliteMat(0x1c1712),
    'focus-coarse', V(0.42, 1.0, 0.15));
  focusCoarse.rotation.z = Math.PI / 2; group.add(focusCoarse);
  const focusFine = part(new THREE.CylinderGeometry(0.17, 0.17, 0.16, 24), brassMat(),
    'focus-fine', V(0.42, 1.0, 0.42));
  focusFine.rotation.z = Math.PI / 2; group.add(focusFine);

  // ── Sub-stage illuminator (mirror/lamp under the stage) ───────────────────
  const illuminator = part(new THREE.CylinderGeometry(0.26, 0.3, 0.3, 24), steelMat(),
    'illuminator', V(0.05, 1.45, 0.55));
  group.add(illuminator);
  const lamp = part(new THREE.SphereGeometry(0.15, 20, 16),
    new THREE.MeshBasicMaterial({ color: 0xfff2cf }), 'illuminator-lamp', V(0.05, 1.62, 0.55));
  lamp.name = 'illuminator'; group.add(lamp);
  const illLight = new THREE.PointLight(0xfff0d0, 1.4, 4, 2);
  illLight.position.set(0.05, 1.9, 0.55); group.add(illLight);

  // ── Eyepiece (angled tube top) ────────────────────────────────────────────
  const eyepiece = part(new THREE.CylinderGeometry(0.16, 0.2, 0.5, 20), bakeliteMat(0x15110d),
    'eyepiece', V(0.05, 4.42, 0.3));
  eyepiece.rotation.x = -0.4; group.add(eyepiece);

  // ── Eyepiece view: a disc with the live coacervate field ──────────────────
  const dyn = makeDynamicTexture(256);
  const viewMat = new THREE.MeshBasicMaterial({ map: dyn.tex });
  const view = part(new THREE.CircleGeometry(1.3, 64), viewMat,
    'eyepiece-view', V(2.9, 3.4, 0.4));
  group.add(view);
  group.add(part(new THREE.TorusGeometry(1.32, 0.08, 16, 64), brassMat(),
    'eyepiece-view-bezel', V(2.9, 3.4, 0.4)));

  group.position.y = 0;

  // ── Coacervate field: droplets that coalesce + coarsen over time ──────────
  const { ctx, size } = dyn;
  let drops = [];
  function seed() {
    drops = [];
    for (let i = 0; i < 90; i++) {
      drops.push({ x: Math.random() * size, y: Math.random() * size,
        r: 3 + Math.random() * 4, vx: (Math.random() - 0.5) * 6, vy: (Math.random() - 0.5) * 6, alive: true });
    }
  }
  seed();
  function coarsen() {
    // merge nearest overlapping pairs: volume-conserving coalescence
    for (let i = 0; i < drops.length; i++) {
      const a = drops[i]; if (!a.alive) continue;
      for (let j = i + 1; j < drops.length; j++) {
        const b = drops[j]; if (!b.alive) continue;
        const dx = a.x - b.x, dy = a.y - b.y;
        if (Math.hypot(dx, dy) < a.r + b.r) {
          const nr = Math.sqrt(a.r * a.r + b.r * b.r);
          a.x = (a.x * a.r + b.x * b.r) / (a.r + b.r);
          a.y = (a.y * a.r + b.y * b.r) / (a.r + b.r);
          a.r = nr; b.alive = false;
        }
      }
    }
  }
  function paint() {
    ctx.fillStyle = '#0d1410'; ctx.fillRect(0, 0, size, size);
    for (const d of drops) {
      if (!d.alive) continue;
      const g = ctx.createRadialGradient(d.x - d.r * 0.3, d.y - d.r * 0.3, 1, d.x, d.y, d.r);
      g.addColorStop(0, 'rgba(190,210,180,0.95)');
      g.addColorStop(0.7, 'rgba(120,150,110,0.7)');
      g.addColorStop(1, 'rgba(60,90,60,0.15)');
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2); ctx.fill();
    }
    dyn.tex.needsUpdate = true;
  }
  paint();

  let running = true, progress = 0;
  let mergeTimer = 0;
  group.userData.anim = {
    setRunning(on) { running = on; illLight.intensity = on ? 1.4 : 0.3; lamp.material.color.setHex(on ? 0xfff2cf : 0x4a4636); },
    getProgress() { return progress; },
    reset() { progress = 0; seed(); paint(); focusCoarse.rotation.x = 0; },
    update(dt, t) {
      if (!running) return;
      for (const d of drops) {
        if (!d.alive) continue;
        d.x += d.vx * dt; d.y += d.vy * dt;
        if (d.x < d.r || d.x > size - d.r) d.vx *= -1;
        if (d.y < d.r || d.y > size - d.r) d.vy *= -1;
      }
      mergeTimer += dt;
      if (mergeTimer > 0.12) { coarsen(); mergeTimer = 0; }
      const alive = drops.filter((d) => d.alive).length;
      progress = Math.min(1, 1 - (alive - 1) / 89);     // coarsening fraction
      focusCoarse.rotation.x = Math.sin(t * 0.4) * 0.25; // focus knob drifts
      paint();
    },
  };

  return group;
}

export const meta = {
  id: 'stage9-coacervate',
  label: 'Stage 9 — Coacervates',
  title: 'Oparin droplets under the microscope',
  blurb: 'Oparin coacervates form by liquid–liquid phase separation (Cahn–Hilliard). '
       + 'Membraneless droplets coalesce and coarsen over time.',
  build,
};
