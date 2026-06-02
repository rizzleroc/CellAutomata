// Stage 3 — Vesicles · vintage phase-contrast research microscope + slide.
//
// Fatty acids above their CMC self-assemble into lipid bilayer vesicles
// (Deamer; Hanczyc & Szostak), observed under the scope. A heavy brass/steel
// microscope carries a glass slide + coverslip on its stage; an angled eyepiece
// floats a lit "eyepiece view" disc whose CanvasTexture shows drifting circular
// vesicles. The coarse-focus knob turns slowly while running. Parts are named.

import * as THREE from 'three';
import { glassMat, steelMat, brassMat, darkMetalMat, makeDynamicTexture, part, V } from './lib.js';

export function build() {
  const group = new THREE.Group();
  group.name = 'vesicle-microscope';

  // ── Foot + arm (the heavy curved body) ────────────────────────────────────
  const foot = part(new THREE.CylinderGeometry(1.1, 1.3, 0.35, 8), darkMetalMat(),
    'microscope-foot', V(0, 0.18, 0));
  group.add(foot);
  const pillar = part(new THREE.BoxGeometry(0.45, 1.9, 0.5), darkMetalMat(),
    'pillar', V(-0.35, 1.2, -0.2));
  group.add(pillar);
  // curved arm (a thick torus segment leaning back)
  const arm = part(new THREE.TorusGeometry(1.0, 0.16, 16, 32, Math.PI * 0.9), darkMetalMat(),
    'arm', V(-0.35, 2.2, -0.2));
  arm.rotation.z = -0.9;
  group.add(arm);

  // ── Stage (flat platform) with slide, coverslip + clips ───────────────────
  const stage = part(new THREE.BoxGeometry(1.5, 0.12, 1.2), steelMat(), 'stage', V(0.15, 1.6, 0.15));
  group.add(stage);
  const slide = part(new THREE.BoxGeometry(0.9, 0.03, 0.5),
    new THREE.MeshPhysicalMaterial({ color: 0xeaf2f5, transmission: 0.6, roughness: 0.1, transparent: true, ior: 1.5 }),
    'slide', V(0.15, 1.68, 0.15));
  group.add(slide);
  const coverslip = part(new THREE.BoxGeometry(0.4, 0.01, 0.4), glassMat(), 'coverslip', V(0.15, 1.705, 0.15));
  group.add(coverslip);
  for (const sx of [-0.35, 0.35]) {
    const clip = part(new THREE.BoxGeometry(0.1, 0.04, 0.3), brassMat(),
      `stage-clip-${sx < 0 ? 'L' : 'R'}`, V(0.15 + sx, 1.69, 0.15));
    group.add(clip);
  }

  // ── Body tube + objective turret with three objectives ────────────────────
  const bodyTube = part(new THREE.CylinderGeometry(0.22, 0.22, 1.2, 24), darkMetalMat(),
    'body-tube', V(0.15, 2.95, -0.05));
  group.add(bodyTube);
  const turret = part(new THREE.CylinderGeometry(0.32, 0.32, 0.18, 24), brassMat(),
    'objective-turret', V(0.15, 2.25, 0.0));
  group.add(turret);
  for (let i = 0; i < 3; i++) {
    const a = i / 3 * Math.PI * 2 - Math.PI / 2;
    const ox = 0.15 + Math.cos(a) * 0.2, oz = Math.sin(a) * 0.2;
    const len = 0.22 + i * 0.06;
    const obj = part(new THREE.CylinderGeometry(0.06, 0.09, len, 16), steelMat(),
      `objective-${i}`, V(ox, 2.25 - 0.1 - len / 2, oz));
    group.add(obj);
  }

  // ── Focus knobs (coarse + fine) on the pillar ─────────────────────────────
  const focusCoarse = part(new THREE.CylinderGeometry(0.32, 0.32, 0.16, 32), brassMat(),
    'focus-coarse', V(-0.72, 1.2, -0.2));
  focusCoarse.rotation.z = Math.PI / 2;
  group.add(focusCoarse);
  const focusFine = part(new THREE.CylinderGeometry(0.2, 0.2, 0.14, 32), brassMat(),
    'focus-fine', V(-0.72, 1.2, 0.18));
  focusFine.rotation.z = Math.PI / 2;
  group.add(focusFine);

  // ── Eyepiece (angled at top of body tube) ─────────────────────────────────
  const eyepiece = part(new THREE.CylinderGeometry(0.13, 0.16, 0.55, 20), darkMetalMat(),
    'eyepiece', V(0.15, 3.7, 0.25));
  eyepiece.rotation.x = -0.5;
  group.add(eyepiece);

  // ── Illuminator / mirror below the stage ──────────────────────────────────
  const illuminator = part(new THREE.CylinderGeometry(0.3, 0.3, 0.1, 24),
    new THREE.MeshStandardMaterial({ color: 0xded6c6, metalness: 0.6, roughness: 0.2, emissive: 0x332f22 }),
    'illuminator', V(0.15, 0.95, 0.15));
  illuminator.rotation.x = 0.4;
  group.add(illuminator);
  const illumLight = new THREE.PointLight(0xfff0d0, 1.0, 3, 2);
  illumLight.position.set(0.15, 1.1, 0.15);
  group.add(illumLight);

  // ── Eyepiece-view disc: lit circle showing drifting vesicles ──────────────
  const dyn = makeDynamicTexture(256);
  const view = part(new THREE.CircleGeometry(0.7, 48),
    new THREE.MeshBasicMaterial({ map: dyn.tex, transparent: true }), 'eyepiece-view', V(1.7, 3.9, 0.6));
  group.add(view);

  group.position.y = 0;

  // ── Animation: drifting vesicles in the eyepiece field ────────────────────
  const { ctx, size } = dyn;
  const ves = [];
  for (let i = 0; i < 14; i++) {
    ves.push({
      x: Math.random(), y: Math.random(), r: 0.04 + Math.random() * 0.07,
      vx: (Math.random() - 0.5) * 0.02, vy: (Math.random() - 0.5) * 0.02,
    });
  }
  let running = true, progress = 0;

  function paint() {
    const c = size / 2;
    ctx.fillStyle = '#161b22';
    ctx.fillRect(0, 0, size, size);
    // circular field-of-view mask
    ctx.save();
    ctx.beginPath(); ctx.arc(c, c, c - 4, 0, Math.PI * 2); ctx.clip();
    ctx.fillStyle = '#243042'; ctx.fillRect(0, 0, size, size);
    for (const v of ves) {
      const px = v.x * size, py = v.y * size, rr = v.r * size;
      const grad = ctx.createRadialGradient(px, py, rr * 0.2, px, py, rr);
      grad.addColorStop(0, 'rgba(220,235,245,0.05)');
      grad.addColorStop(0.8, 'rgba(180,210,230,0.25)');
      grad.addColorStop(1, 'rgba(120,160,190,0.6)');
      ctx.fillStyle = grad;
      ctx.beginPath(); ctx.arc(px, py, rr, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = 'rgba(200,225,240,0.5)'; ctx.lineWidth = 1.4;
      ctx.beginPath(); ctx.arc(px, py, rr, 0, Math.PI * 2); ctx.stroke();
    }
    ctx.restore();
    dyn.tex.needsUpdate = true;
  }
  paint();

  group.userData.anim = {
    setRunning(on) { running = on; illumLight.intensity = on ? 1.0 : 0.2; },
    getProgress() { return progress; },
    reset() { progress = 0; for (const v of ves) { v.x = Math.random(); v.y = Math.random(); } paint(); },
    update(dt, t) {
      if (!running) return;
      progress = Math.min(1, progress + dt / 35);
      focusCoarse.rotation.x += dt * 0.6;       // coarse knob racks slowly
      for (const v of ves) {
        v.x += v.vx * dt * 6; v.y += v.vy * dt * 6;
        if (v.x < 0) v.x += 1; if (v.x > 1) v.x -= 1;
        if (v.y < 0) v.y += 1; if (v.y > 1) v.y -= 1;
      }
      paint();
    },
  };

  return group;
}

export const meta = {
  id: 'stage3-vesicles',
  label: 'Stage 3 — Vesicles',
  title: 'Phase-contrast microscope + slide',
  blurb: 'Fatty acids above their critical micelle concentration self-assemble into lipid '
       + 'bilayer vesicles (Deamer; Hanczyc & Szostak), observed under the microscope.',
  build,
};
