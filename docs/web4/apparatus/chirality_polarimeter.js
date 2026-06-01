// Stage 6 — Homochirality · Soai reaction + polarimeter.
//
// Frank/Soai autocatalysis breaks chiral symmetry: a tiny enantiomeric excess
// amplifies until one handedness dominates. A small reaction flask sits beside
// a brass polarimeter — a horizontal tube with a light source at one end and a
// graduated dial + eyepiece at the other. As one enantiomer wins, the flask
// liquid tints and the polarimeter needle swings off zero.

import * as THREE from 'three';
import { part, flask, glassMat, liquidMat, brassMat, steelMat, emissiveMat, makeDynamicTexture, V } from './lib.js';

// Deterministic choice of winning handedness: (+) magenta in this build.
const SIGN = +1;
const FINAL_DEG = 18 * SIGN;          // final optical rotation
const TINT = new THREE.Color(0xc850b0); // magenta (dextro); teal would be 0x2fb3a6

function drawDial(ctx, size, deg) {
  const c = size / 2;
  ctx.clearRect(0, 0, size, size);
  ctx.fillStyle = '#1a1712'; ctx.beginPath(); ctx.arc(c, c, c - 4, 0, Math.PI * 2); ctx.fill();
  ctx.strokeStyle = '#caa86a'; ctx.lineWidth = 5; ctx.stroke();
  // degree ticks (-30..+30 across the top semicircle)
  ctx.strokeStyle = '#e8e2d2';
  for (let d = -30; d <= 30; d += 5) {
    const a = -Math.PI / 2 + (d / 30) * (Math.PI * 0.75);
    const r0 = c - 12, r1 = (d % 10 === 0) ? c - 30 : c - 22;
    ctx.lineWidth = (d % 10 === 0) ? 3 : 1.5;
    ctx.beginPath();
    ctx.moveTo(c + Math.cos(a) * r0, c + Math.sin(a) * r0);
    ctx.lineTo(c + Math.cos(a) * r1, c + Math.sin(a) * r1);
    ctx.stroke();
  }
  ctx.fillStyle = '#9a9382'; ctx.font = `${size * 0.07}px Georgia, serif`; ctx.textAlign = 'center';
  ctx.fillText('-', c - c * 0.5, c - c * 0.32);
  ctx.fillText('+', c + c * 0.5, c - c * 0.32);
  // needle
  const na = -Math.PI / 2 + (deg / 30) * (Math.PI * 0.75);
  ctx.strokeStyle = '#ff5a8a'; ctx.lineWidth = 4; ctx.beginPath();
  ctx.moveTo(c, c); ctx.lineTo(c + Math.cos(na) * (c - 36), c + Math.sin(na) * (c - 36)); ctx.stroke();
  ctx.fillStyle = '#caa86a'; ctx.beginPath(); ctx.arc(c, c, 7, 0, Math.PI * 2); ctx.fill();
}

function build() {
  const group = new THREE.Group();
  group.name = 'chirality-polarimeter-1953';

  // ── Reaction flask on the bench (left) ────────────────────────────────────
  const fl = flask(0.7, 'flask', 0.5);
  fl.position.set(-2.4, 0.75, 0);
  group.add(fl);
  const liqMat = liquidMat(0xdedad0, { transmission: 0.7 });
  const liquid = part(new THREE.SphereGeometry(0.6, 40, 28), liqMat, 'liquid', V(-2.4, 0.6, 0));
  liquid.scale.y = 0.7;
  group.add(liquid);

  // ── Polarimeter stand ─────────────────────────────────────────────────────
  const TUBE_Y = 1.7;
  group.add(part(new THREE.BoxGeometry(4.4, 0.12, 0.9), steelMat(), 'stand', V(0.6, 0.06, 0)));
  for (const sx of [-1.3, 2.4]) {
    group.add(part(new THREE.CylinderGeometry(0.07, 0.09, TUBE_Y - 0.1, 20), brassMat(),
      `stand-post-${sx < 0 ? 'L' : 'R'}`, V(sx, (TUBE_Y - 0.1) / 2 + 0.06, 0)));
  }

  // ── Horizontal brass polarimeter tube ─────────────────────────────────────
  const ptube = part(new THREE.CylinderGeometry(0.32, 0.32, 3.0, 36), brassMat(),
    'polarimeter-tube', V(0.5, TUBE_Y, 0));
  ptube.rotation.z = Math.PI / 2;
  group.add(ptube);
  // sample cell window (glass) mid-tube
  const cell = part(new THREE.CylinderGeometry(0.22, 0.22, 1.1, 28), glassMat(),
    'sample-cell', V(0.5, TUBE_Y, 0));
  cell.rotation.z = Math.PI / 2;
  group.add(cell);

  // ── Light source at far (left) end ────────────────────────────────────────
  const lightHousing = part(new THREE.CylinderGeometry(0.4, 0.4, 0.5, 28), steelMat(),
    'light-housing', V(-1.15, TUBE_Y, 0));
  lightHousing.rotation.z = Math.PI / 2;
  group.add(lightHousing);
  const lightSource = part(new THREE.CircleGeometry(0.26, 28), emissiveMat(0xfff2c4), 'light-source', V(-0.95, TUBE_Y, 0));
  lightSource.rotation.y = -Math.PI / 2;
  group.add(lightSource);
  const naLamp = new THREE.PointLight(0xfff0bf, 2.5, 4, 2);
  naLamp.position.set(-0.95, TUBE_Y, 0);
  group.add(naLamp);

  // ── Eyepiece + graduated dial at near (right) end ─────────────────────────
  const eyepiece = part(new THREE.CylinderGeometry(0.18, 0.24, 0.6, 24), brassMat(),
    'eyepiece', V(2.45, TUBE_Y, 0));
  eyepiece.rotation.z = Math.PI / 2;
  group.add(eyepiece);

  const dialTex = makeDynamicTexture(256);
  drawDial(dialTex.ctx, dialTex.size, 0);
  dialTex.tex.needsUpdate = true;
  // mount the dial facing the viewer (in xy plane) just above the tube end
  const dial = part(new THREE.CircleGeometry(0.55, 48),
    new THREE.MeshStandardMaterial({ map: dialTex.tex, roughness: 0.5, metalness: 0.2 }),
    'dial', V(2.15, TUBE_Y + 0.7, 0));
  group.add(dial);
  // dial bezel
  const bezel = part(new THREE.TorusGeometry(0.55, 0.05, 12, 48), brassMat(), 'dial-bezel', V(2.15, TUBE_Y + 0.7, 0));
  group.add(bezel);

  // physical needle overlay (in addition to drawn needle, for depth)
  const needle = part(new THREE.BoxGeometry(0.5, 0.03, 0.02),
    new THREE.MeshStandardMaterial({ color: 0xff5a8a, roughness: 0.4, metalness: 0.3, emissive: 0x4a0a22 }),
    'needle', V(2.15, TUBE_Y + 0.7, 0.06));
  // pivot the needle from its base: shift geometry so it rotates about one end
  needle.geometry.translate(0.25, 0, 0);
  group.add(needle);

  group.position.y = 0;

  // ── Animation ─────────────────────────────────────────────────────────────
  let running = true, progress = 0, curDeg = 0;
  const maxAbs = Math.abs(FINAL_DEG);
  const apply = () => {
    drawDial(dialTex.ctx, dialTex.size, curDeg);
    dialTex.tex.needsUpdate = true;
    // needle points up (-y rotation) at 0; swing by deg toward + side
    needle.rotation.z = Math.PI / 2 - (curDeg / 30) * (Math.PI * 0.75);
    const f = Math.abs(curDeg) / maxAbs;
    liqMat.color.copy(new THREE.Color(0xdedad0).lerp(TINT, f));
  };
  apply();

  const anim = {
    setRunning(on) { running = on; },
    getProgress() { return progress; },
    reset() { progress = 0; curDeg = 0; apply(); },
    update(dt, t) {
      if (running) {
        // sigmoidal symmetry breaking: slow start, sharp commit
        progress = Math.min(1, progress + dt / 30);
        const s = 1 / (1 + Math.exp(-(progress - 0.45) * 12));
        const wobble = running ? Math.sin(t * 6) * (1 - progress) * 1.2 : 0;
        curDeg = FINAL_DEG * s + wobble;
      }
      apply();
    },
  };
  group.userData.anim = anim;
  return group;
}

export const meta = {
  id: 'stage6-chirality',
  label: 'Stage 6 — Homochirality',
  title: 'Soai reaction + polarimeter',
  blurb: 'Frank/Soai autocatalysis breaks chiral symmetry — one handedness wins. The polarimeter dial swings to + or −.',
  build,
};
