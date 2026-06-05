// Stage 1 — Belousov–Zhabotinsky Petri dish (1958).
//
// A shallow borosilicate Petri dish on the bench under a ring light, holding a
// thin reagent film that self-organises into travelling target/spiral waves —
// the lab embodiment of Gray-Scott reaction-diffusion. The film's top surface
// is a CanvasTexture repainted every frame with expanding concentric rings; a
// glass pipette rests alongside. Every part is named for the parts panel.

import * as THREE from 'three';
import { glassMat, steelMat, brassMat, liquidMat, part, makeDynamicTexture, V } from './lib.js';

export function build() {
  const group = new THREE.Group();
  group.name = 'bz-petri-1958';

  const cx = 0, cy = 0.95, R = 1.7; // dish centre + radius

  // ── Petri base: shallow glass cylinder ────────────────────────────────────
  const base = part(new THREE.CylinderGeometry(R, R, 0.28, 64, 1, true), glassMat(),
    'petri-base', V(cx, cy, 0));
  group.add(base);
  const floor = part(new THREE.CylinderGeometry(R, R, 0.04, 64), glassMat(),
    'petri-base-floor', V(cx, cy - 0.14, 0));
  floor.name = 'petri-base'; // grouped under same logical part
  group.add(floor);

  // ── Reagent film: thin disc with a dynamic BZ texture on top ──────────────
  const dyn = makeDynamicTexture(256);
  const filmMat = new THREE.MeshPhysicalMaterial({
    map: dyn.tex, roughness: 0.25, transmission: 0.35, thickness: 0.2,
    ior: 1.34, transparent: true, clearcoat: 0.4, clearcoatRoughness: 0.15,
  });
  const film = part(new THREE.CylinderGeometry(R * 0.96, R * 0.96, 0.07, 64), filmMat,
    'reagent-film', V(cx, cy - 0.06, 0));
  group.add(film);

  // ── Petri lid: set slightly ajar, resting half on the rim ─────────────────
  const lid = part(new THREE.CylinderGeometry(R * 1.04, R * 1.04, 0.24, 64, 1, true), glassMat(),
    'petri-lid', V(cx + 0.55, cy + 0.55, -0.1));
  lid.rotation.z = -0.32;
  group.add(lid);
  const lidTop = part(new THREE.CylinderGeometry(R * 1.04, R * 1.04, 0.03, 64), glassMat(),
    'petri-lid-top', V(cx + 0.55, cy + 0.67, -0.1));
  lidTop.name = 'petri-lid'; lidTop.rotation.z = -0.32;
  group.add(lidTop);

  // ── Pipette: a slim glass tube with a rubber bulb, resting beside the dish ─
  const pip = new THREE.Group(); pip.name = 'pipette';
  const stem = part(new THREE.CylinderGeometry(0.05, 0.025, 2.0, 16), glassMat(), 'pipette-stem');
  pip.add(stem);
  const bulb = part(new THREE.SphereGeometry(0.16, 24, 18),
    new THREE.MeshStandardMaterial({ color: 0x33312e, roughness: 0.85 }), 'pipette-bulb', V(0, 1.1, 0));
  pip.add(bulb);
  pip.position.set(cx + 2.6, cy + 0.18, 0.7);
  pip.rotation.z = Math.PI / 2.3;
  pip.name = 'pipette';
  group.add(pip);

  // ── Ring light overhead ────────────────────────────────────────────────────
  const ring = part(new THREE.TorusGeometry(2.1, 0.12, 16, 64),
    new THREE.MeshStandardMaterial({ color: 0xe8e2d2, metalness: 0.3, roughness: 0.4, emissive: 0x2a2620 }),
    'ring-light', V(cx, cy + 2.6, 0));
  ring.rotation.x = Math.PI / 2;
  group.add(ring);
  const ringInner = part(new THREE.TorusGeometry(2.1, 0.06, 12, 64),
    new THREE.MeshBasicMaterial({ color: 0xfff4d8 }), 'ring-light-tube', V(cx, cy + 2.55, 0));
  ringInner.name = 'ring-light'; ringInner.rotation.x = Math.PI / 2;
  group.add(ringInner);
  const ringLight = new THREE.PointLight(0xfff0d0, 2.2, 8, 2);
  ringLight.position.set(cx, cy + 2.5, 0);
  group.add(ringLight);
  // three steel support arms
  for (let i = 0; i < 3; i++) {
    const a = i / 3 * Math.PI * 2;
    const arm = part(new THREE.CylinderGeometry(0.03, 0.03, 2.6, 8), steelMat(),
      `ring-arm-${i}`, V(cx + Math.cos(a) * 2.1, cy + 1.3, Math.sin(a) * 2.1));
    group.add(arm);
  }

  group.position.y = 0;

  // ── Dynamic chemistry elements (UNNAMED so they stay out of the parts panel)─
  // Reaction-glow light: a soft tint that pulses with the BZ phase. Colour is
  // drawn only from the sanctioned palette (teal ↔ warm), the liquid below
  // stays a physical reagent colour.
  const glow = new THREE.PointLight(0x3fe0d0, 0, 4.5, 2);
  glow.position.set(cx, cy + 0.25, 0);
  group.add(glow);

  // A handful of CO₂ bubbles that nucleate near the dish floor and rise through
  // the thin film, then re-seed — small, translucent, physical (no emissive).
  const filmTop = cy - 0.06 + 0.035;      // top surface of the reagent film
  const filmBottom = cy - 0.06 - 0.035;
  const bubbleMat = new THREE.MeshPhysicalMaterial({
    color: 0xffffff, roughness: 0.15, transmission: 0.85,
    thickness: 0.1, ior: 1.2, transparent: true, opacity: 0.6,
  });
  const bubbles = [];
  for (let i = 0; i < 7; i++) {
    const b = new THREE.Mesh(new THREE.SphereGeometry(0.03, 10, 8), bubbleMat);
    b.userData.reset = () => {
      const a = Math.random() * Math.PI * 2;
      const rad = Math.random() * R * 0.9;
      b.userData.bx = cx + Math.cos(a) * rad;
      b.userData.bz = Math.sin(a) * rad;
      b.position.set(b.userData.bx, filmBottom, b.userData.bz);
      b.userData.v = 0.10 + Math.random() * 0.14;     // rise speed
      b.userData.s = 0.7 + Math.random() * 0.8;        // size
      b.scale.setScalar(b.userData.s);
      b.userData.wob = Math.random() * Math.PI * 2;    // shimmer phase
    };
    b.userData.reset();
    // stagger the initial heights so they don't all pop at once
    b.position.y = filmBottom + Math.random() * (filmTop - filmBottom);
    group.add(b);
    bubbles.push(b);
  }

  // ── Animation: paint expanding BZ rings into the film texture ─────────────
  const { ctx, size } = dyn;
  const sources = [
    { x: 0.5, y: 0.5, ph: 0 }, { x: 0.32, y: 0.62, ph: 1.7 },
    { x: 0.68, y: 0.38, ph: 3.1 }, { x: 0.6, y: 0.7, ph: 4.5 },
  ];
  let running = true, progress = 0;

  // BZ phase colours: amber (oxidised, ferriin) ↔ teal (reduced, ferroin-ish).
  const amber = new THREE.Color(0xc8731e);
  const teal = new THREE.Color(0x1f8f86);
  const filmBaseY = film.position.y;
  filmMat.color.copy(amber);

  function paint(t) {
    ctx.fillStyle = '#1a3320';
    ctx.fillRect(0, 0, size, size);
    for (const s of sources) {
      const px = s.x * size, py = s.y * size;
      // concentric travelling waves: bright bands whose phase advances with t
      for (let r = 4; r < size; r += 3) {
        const phase = r * 0.18 - t * 2.4 + s.ph;
        const w = 0.5 + 0.5 * Math.sin(phase);
        if (w < 0.55) continue;
        const fade = 1 - r / (size * 0.95);
        if (fade <= 0) continue;
        const g = Math.floor(120 + 120 * w * fade);
        ctx.strokeStyle = `rgba(${Math.floor(60 * w)},${g},${Math.floor(80 + 60 * w)},${0.55 * fade})`;
        ctx.lineWidth = 1.6;
        ctx.beginPath();
        ctx.arc(px, py, r, 0, Math.PI * 2);
        ctx.stroke();
      }
    }
    dyn.tex.needsUpdate = true;
  }
  paint(0);

  // Settle the dynamic phenomenon back to a calm, stopped state.
  function calm() {
    glow.intensity = 0;
    filmMat.color.copy(amber);
    film.position.y = filmBaseY;
    film.scale.set(1, 1, 1);
    for (const b of bubbles) b.visible = false;
  }

  group.userData.anim = {
    setRunning(on) {
      running = on;
      ringLight.intensity = on ? 2.2 : 0.6;
      ringInner.material.color.setHex(on ? 0xfff4d8 : 0x44403a);
      if (!on) calm();
    },
    getProgress() { return progress; },
    reset() { progress = 0; calm(); paint(0); },
    update(dt, t) {
      if (!running) return;
      // Reaction maturity drives the readout.
      progress = Math.min(1, progress + dt / 30);
      paint(t);

      // BZ colour oscillation: the whole film breathes amber ↔ teal as the
      // ferroin/ferriin couple flips. Oscillation quickens as the run matures.
      const osc = 0.5 + 0.5 * Math.sin(t * (1.3 + progress * 0.9));
      filmMat.color.copy(amber).lerp(teal, osc);

      // Reaction glow pulses in step (teal at the reduced peak, warm otherwise).
      glow.color.copy(teal).lerp(new THREE.Color(0xffb866), 1 - osc);
      glow.intensity = 0.4 + 1.3 * osc;

      // Gentle surface ripple/shimmer: the film breathes vertically and in
      // plane — a subtle, finite oscillation of the liquid surface.
      film.position.y = filmBaseY + Math.sin(t * 2.2) * 0.012;
      const sh = 1 + Math.sin(t * 1.7) * 0.012;
      film.scale.set(sh, 1, sh);

      // CO₂ bubbles nucleate at the floor and rise; wobble laterally a touch.
      for (const b of bubbles) {
        b.visible = true;
        b.position.y += b.userData.v * dt;
        b.position.x = b.userData.bx + Math.sin(t * 2.4 + b.userData.wob) * 0.02;
        b.position.z = b.userData.bz + Math.cos(t * 2.1 + b.userData.wob) * 0.02;
        if (b.position.y > filmTop) b.userData.reset();
      }
    },
  };

  return group;
}

export const meta = {
  id: 'stage1-grayscott',
  label: 'Stage 1 — Reaction–diffusion',
  title: 'Belousov–Zhabotinsky Petri dish · 1958',
  blurb: 'A thin reagent film in a Petri dish self-organises into travelling spiral waves — '
       + 'the lab embodiment of Gray-Scott reaction-diffusion.',
  build,
};
