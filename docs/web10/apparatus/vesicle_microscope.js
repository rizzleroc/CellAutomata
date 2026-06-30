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
  const illumMat = new THREE.MeshStandardMaterial({ color: 0xded6c6, metalness: 0.6, roughness: 0.2, emissive: 0xffb866, emissiveIntensity: 0.5 });
  const illuminator = part(new THREE.CylinderGeometry(0.3, 0.3, 0.1, 24), illumMat,
    'illuminator', V(0.15, 0.95, 0.15));
  illuminator.rotation.x = 0.4;
  group.add(illuminator);
  const illumLight = new THREE.PointLight(0xffb866, 1.0, 3, 2);
  illumLight.position.set(0.15, 1.1, 0.15);
  group.add(illumLight);

  // ── Eyepiece-view disc: lit circle showing drifting vesicles ──────────────
  const dyn = makeDynamicTexture(256);
  const view = part(new THREE.CircleGeometry(0.7, 48),
    new THREE.MeshBasicMaterial({ map: dyn.tex, transparent: true }), 'eyepiece-view', V(1.7, 3.9, 0.6));
  group.add(view);

  // ── Physical lipid vesicles ON the slide (unnamed dynamic meshes) ──────────
  // Translucent teal blobs sitting on the glass under the coverslip. Above the
  // CMC they NUCLEATE (fade in from a tiny nucleus), GROW (radius creeps up with
  // a gentle scale pulse), drift, and DIVIDE (a grown vesicle pinches in two,
  // spawning a daughter from the dormant pool) — bilayer self-assembly, mirrored
  // by the eyepiece-view field. Shared geometry; per-vesicle material so each can
  // fade its own opacity. Sphere slightly flattened onto the slide surface.
  const SLIDE_Y = 1.71;                                   // just above the slide, under coverslip
  const FIELD = { cx: 0.15, cz: 0.15, half: 0.16 };       // coverslip footprint
  const vesGeo = new THREE.SphereGeometry(1, 18, 14);
  const blobs = [];
  const NB = 9;
  const placeVesicle = (b, x, z, r) => {
    b.bx = x; b.bz = z;
    b.r = r; b.target = r * (2.4 + Math.random() * 1.6); // grows ~2.5–4×
    b.vx = (Math.random() - 0.5) * 0.05;
    b.vz = (Math.random() - 0.5) * 0.05;
    b.grow = 0.02 + Math.random() * 0.03;                 // growth rate
    b.phase = Math.random() * Math.PI * 2;                // scale-pulse phase
    b.born = 0;                                           // nucleation fade-in 0..1
    b.alive = true;
  };
  for (let i = 0; i < NB; i++) {
    const mat = new THREE.MeshPhysicalMaterial({
      color: 0x123830, emissive: 0x3fe0d0, emissiveIntensity: 0.4,
      roughness: 0.12, transmission: 0.75, thickness: 0.35, ior: 1.36,
      transparent: true, opacity: 0,
    });
    const m = new THREE.Mesh(vesGeo, mat);                // intentionally UNNAMED
    const b = { mesh: m, mat, alive: false, r: 0.02 };
    m.position.set(FIELD.cx, SLIDE_Y, FIELD.cz);
    m.scale.setScalar(0.001);
    blobs.push(b);
    group.add(m);
  }
  // seed two nucleated vesicles so the slide is alive the moment it runs
  placeVesicle(blobs[0], FIELD.cx - 0.05, FIELD.cz + 0.03, 0.02);
  placeVesicle(blobs[1], FIELD.cx + 0.06, FIELD.cz - 0.04, 0.018);

  group.position.y = 0;

  // base positions for faint stage micro-vibration (jitter applied each frame)
  const shakers = [stage, slide, coverslip].map((m) => ({ m, base: m.position.clone() }));

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

  // ── Vesicle bookkeeping helpers ───────────────────────────────────────────
  const clampField = (x) => Math.max(FIELD.cx - FIELD.half, Math.min(FIELD.cx + FIELD.half, x));
  const clampFieldZ = (z) => Math.max(FIELD.cz - FIELD.half, Math.min(FIELD.cz + FIELD.half, z));
  function aliveCount() { let n = 0; for (const b of blobs) if (b.alive) n++; return n; }
  function freeSlot() { for (const b of blobs) if (!b.alive) return b; return null; }
  function applyVesicle(b) {                                // push state → mesh each frame
    const s = b.r * (0.96 + 0.12 * Math.sin(b.phase));      // gentle scale pulse
    b.mesh.scale.set(s, s * 0.6, s);
    b.mesh.position.set(b.bx, SLIDE_Y, b.bz);
    b.mat.opacity = 0.85 * b.born;
    b.mat.emissiveIntensity = 0.3 + 0.35 * b.born;
  }
  function restVesicles() {                                 // calm idle pose (no motion)
    for (const b of blobs) {
      if (b.alive) applyVesicle(b);
      else { b.mesh.scale.setScalar(0.001); b.mat.opacity = 0; }
    }
  }
  restVesicles();

  let nucleTimer = 0, divTimer = 0;

  group.userData.anim = {
    setRunning(on) {
      running = on;
      illumLight.intensity = on ? 1.0 : 0.2;
      illumMat.emissiveIntensity = on ? 0.5 : 0.12;
      if (!on) {                                            // settle to a quiet pose
        for (const s of shakers) s.m.position.copy(s.base);
        restVesicles();
      }
    },
    getProgress() { return progress; },
    reset() {
      progress = 0; nucleTimer = 0; divTimer = 0;
      for (const v of ves) { v.x = Math.random(); v.y = Math.random(); }
      for (const b of blobs) { b.alive = false; b.mesh.scale.setScalar(0.001); b.mat.opacity = 0; }
      placeVesicle(blobs[0], FIELD.cx - 0.05, FIELD.cz + 0.03, 0.02);
      placeVesicle(blobs[1], FIELD.cx + 0.06, FIELD.cz - 0.04, 0.018);
      for (const s of shakers) s.m.position.copy(s.base);
      restVesicles();
      paint();
    },
    update(dt, t) {
      if (!running) return;

      // ── instrument: lamp flicker, focus drift, faint stage micro-vibration ──
      const flick = 0.82 + 0.18 * Math.sin(t * 11) + 0.06 * Math.sin(t * 37);
      illumLight.intensity = flick;
      illumMat.emissiveIntensity = 0.4 + 0.18 * Math.sin(t * 11);
      focusCoarse.rotation.x += dt * 0.5;                  // coarse knob racks slowly
      focusFine.rotation.x = Math.sin(t * 0.7) * 0.4;      // fine knob drifts back and forth
      for (const s of shakers) {                           // sub-pixel stage tremor
        s.m.position.set(
          s.base.x + Math.sin(t * 31 + s.base.z * 9) * 0.004,
          s.base.y + Math.sin(t * 27 + s.base.x * 7) * 0.003,
          s.base.z + Math.cos(t * 29) * 0.004,
        );
      }

      // ── eyepiece field (texture) keeps drifting ─────────────────────────────
      for (const v of ves) {
        v.x += v.vx * dt * 6; v.y += v.vy * dt * 6;
        if (v.x < 0) v.x += 1; if (v.x > 1) v.x -= 1;
        if (v.y < 0) v.y += 1; if (v.y > 1) v.y -= 1;
      }
      paint();

      // ── physical vesicles: nucleate, grow, drift, divide ────────────────────
      for (const b of blobs) {
        if (!b.alive) continue;
        b.born = Math.min(1, b.born + dt * 1.6);
        b.r += (b.target - b.r) * Math.min(1, b.grow * dt * 8);
        b.phase += dt * (2.2 + b.r * 6);                   // pulse a touch faster as it grows
        b.bx = clampField(b.bx + b.vx * dt);
        b.bz = clampFieldZ(b.bz + b.vz * dt);
        applyVesicle(b);
      }

      // periodically nucleate a fresh vesicle from the dormant pool
      nucleTimer += dt;
      if (nucleTimer > 1.6) {
        nucleTimer = 0;
        const slot = freeSlot();
        if (slot) placeVesicle(slot,
          clampField(FIELD.cx + (Math.random() - 0.5) * FIELD.half * 1.6),
          clampFieldZ(FIELD.cz + (Math.random() - 0.5) * FIELD.half * 1.6),
          0.015 + Math.random() * 0.008);
      }

      // a grown vesicle pinches in two: parent halves, daughter buds beside it
      divTimer += dt;
      if (divTimer > 0.9) {
        divTimer = 0;
        for (const b of blobs) {
          if (!b.alive || b.born < 1 || b.r < b.target * 0.85) continue;
          const child = freeSlot();
          if (!child) break;
          b.r *= 0.62; b.target *= 0.78;                   // parent shrinks
          placeVesicle(child,
            clampField(b.bx + (Math.random() - 0.5) * 0.06),
            clampFieldZ(b.bz + (Math.random() - 0.5) * 0.06),
            b.r * 0.8);
          child.born = 0.25;                               // visibly buds off
          break;                                           // one division per tick
        }
      }

      // progress tracks how full the field of vesicles is
      progress = Math.min(1, aliveCount() / NB);
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
