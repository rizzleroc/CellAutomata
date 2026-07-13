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
// Emissive / light palette (only these three are allowed for glow + light):
const TEAL = 0x3fe0d0;                 // (−) laevo domain
const MAGENTA = 0xd77bff;              // (+) dextro domain — the winner here
const WARM = 0xffb866;                 // sodium-lamp warm
const WIN = SIGN > 0 ? MAGENTA : TEAL; // colour the sample resolves to
const TINT = new THREE.Color(WIN);     // physical sample tint toward the winner

function drawDial(ctx, size, deg, needleHex = '#d77bff') {
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
  ctx.strokeStyle = needleHex; ctx.lineWidth = 4; ctx.beginPath();
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
  const lightSource = part(new THREE.CircleGeometry(0.26, 28), emissiveMat(WARM), 'light-source', V(-0.95, TUBE_Y, 0));
  lightSource.rotation.y = -Math.PI / 2;
  group.add(lightSource);
  const naLamp = new THREE.PointLight(WARM, 2.5, 4, 2);
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
  const needleMat = new THREE.MeshStandardMaterial({ color: 0xe8e2d2, roughness: 0.4, metalness: 0.3, emissive: WIN, emissiveIntensity: 0.0 });
  const needle = part(new THREE.BoxGeometry(0.5, 0.03, 0.02), needleMat,
    'needle', V(2.15, TUBE_Y + 0.7, 0.06));
  // pivot the needle from its base: shift geometry so it rotates about one end
  needle.geometry.translate(0.25, 0, 0);
  group.add(needle);

  // ── DYNAMIC (unnamed) elements — the visible physical process ──────────────
  // The light travels along −x→+x down the tube; the rotating ANALYZER prism
  // sits just before the eyepiece. As enantiomeric excess grows the analyzer
  // must be turned to extinguish the beam, so it spins, the beam dims, the
  // needle swings, and the racemic teal/magenta domains resolve to one colour.
  const beamAxisX = 0.5;                          // tube centre x

  // Spinning analyzer prism (a graduated disc across the tube, just inside the
  // eyepiece). It rotates continuously while running — the headline motion.
  const analyzer = new THREE.Mesh(
    new THREE.CylinderGeometry(0.3, 0.3, 0.08, 6),
    new THREE.MeshStandardMaterial({ color: 0xcfd3d8, metalness: 0.6, roughness: 0.3,
      transparent: true, opacity: 0.55 }),
  );
  analyzer.position.set(2.0, TUBE_Y, 0);
  analyzer.rotation.z = Math.PI / 2;              // face down the tube
  group.add(analyzer);
  // index mark on the analyzer rim so its spin is unmistakable
  const analyzerMark = new THREE.Mesh(
    new THREE.BoxGeometry(0.05, 0.1, 0.26),
    new THREE.MeshStandardMaterial({ color: 0x1a1712, metalness: 0.3, roughness: 0.6 }),
  );
  analyzerMark.position.set(0, 0.24, 0);          // offset on the disc face
  analyzer.add(analyzerMark);                      // rides with the disc

  // Polarized light beam: a thin emissive cylinder along the tube whose opacity
  // pulses; plus a travelling photon bead and a point light that pulse-travels.
  const beamMat = new THREE.MeshBasicMaterial({ color: WARM, transparent: true, opacity: 0.0 });
  const beam = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 2.6, 16), beamMat);
  beam.position.set(beamAxisX, TUBE_Y, 0);
  beam.rotation.z = Math.PI / 2;
  group.add(beam);

  const photonMat = new THREE.MeshBasicMaterial({ color: WARM, transparent: true, opacity: 0.0 });
  const photon = new THREE.Mesh(new THREE.SphereGeometry(0.08, 12, 12), photonMat);
  photon.position.set(beamAxisX, TUBE_Y, 0);
  group.add(photon);

  const beamLight = new THREE.PointLight(WARM, 0, 3, 2);
  beamLight.position.set(beamAxisX, TUBE_Y, 0);
  group.add(beamLight);

  // Racemic domains inside the flask: small emissive blobs, half teal / half
  // magenta, that pulse and then converge (colour + emissive) on the winner.
  const domains = [];
  const DOM_N = 12;
  for (let i = 0; i < DOM_N; i++) {
    const startHex = (i % 2 === 0) ? TEAL : MAGENTA;
    const m = new THREE.MeshStandardMaterial({
      color: 0x2a2a30, emissive: startHex, emissiveIntensity: 0.0,
      roughness: 0.4, metalness: 0.0, transparent: true, opacity: 0.9,
    });
    const blob = new THREE.Mesh(new THREE.SphereGeometry(0.07, 12, 10), m);
    const a = (i / DOM_N) * Math.PI * 2, rr = 0.18 + (i % 3) * 0.12;
    blob.userData.base = V(-2.4 + Math.cos(a) * rr, 0.55 + Math.sin(a * 1.7) * 0.18, Math.sin(a) * rr);
    blob.userData.start = new THREE.Color(startHex);
    blob.userData.phase = i * 0.7;
    blob.position.copy(blob.userData.base);
    group.add(blob);
    domains.push(blob);
  }
  const winColor = new THREE.Color(WIN);

  group.position.y = 0;

  // ── Animation ─────────────────────────────────────────────────────────────
  // progress == enantiomeric excess (ee), 0 (racemic) → 1 (homochiral).
  const needleHex = '#' + new THREE.Color(WIN).getHexString();
  const baseLiq = new THREE.Color(0xdedad0);
  let running = true, progress = 0, curDeg = 0, beamPulse = 0;
  const maxAbs = Math.abs(FINAL_DEG);

  // Static (running-independent) part of the readout: dial drawing, needle
  // angle and sample tint — always reflects the current ee/rotation so a Stop
  // leaves a coherent frozen state.
  const apply = () => {
    drawDial(dialTex.ctx, dialTex.size, curDeg, needleHex);
    dialTex.tex.needsUpdate = true;
    // needle points up (−z rotation) at 0; swing by deg toward + side
    needle.rotation.z = Math.PI / 2 - (curDeg / 30) * (Math.PI * 0.75);
    needleMat.emissiveIntensity = 0.15 + (Math.abs(curDeg) / maxAbs) * 0.5;
    const f = Math.min(1, Math.abs(curDeg) / maxAbs);
    liqMat.color.copy(baseLiq.clone().lerp(TINT, f));
  };
  apply();

  const anim = {
    setRunning(on) {
      running = on;
      if (!on) {
        // calm everything that is purely a "process is live" indicator
        beam.material.opacity = 0;
        photon.material.opacity = 0;
        beamLight.intensity = 0;
      }
    },
    getProgress() { return progress; },
    reset() {
      progress = 0; curDeg = 0; beamPulse = 0;
      analyzer.rotation.x = 0;
      photon.position.x = beamAxisX;
      for (const b of domains) {
        b.position.copy(b.userData.base);
        b.material.emissive.copy(b.userData.start);
        b.material.emissiveIntensity = 0;
      }
      beam.material.opacity = 0; photon.material.opacity = 0; beamLight.intensity = 0;
      apply();
    },
    update(dt, t) {
      if (running) {
        // sigmoidal symmetry breaking: slow start, sharp autocatalytic commit
        progress = Math.min(1, progress + dt / 12);
        const s = 1 / (1 + Math.exp(-(progress - 0.4) * 11));
        // racemic jitter early, decaying as one handedness locks in
        const wobble = Math.sin(t * 6) * (1 - progress) * 2.0;
        curDeg = FINAL_DEG * s + wobble;

        // Analyzer prism spins to hunt the extinction angle; spin is brisk while
        // racemic, easing (but never zero) as the rotation locks in.
        const spin = 5.2 * (0.35 + 0.65 * (1 - s));
        analyzer.rotation.x += spin * dt;

        // Polarized beam: pulsing brightness + a photon bead travelling −x→+x.
        beamPulse += dt;
        const flick = 0.6 + 0.4 * Math.sin(t * 9);
        beam.material.opacity = (0.22 + 0.18 * flick) * (0.5 + 0.5 * s);
        photon.material.opacity = 0.85;
        const travel = (beamPulse % 0.7) / 0.7;          // 0..1 loop
        photon.position.x = beamAxisX - 1.25 + travel * 2.5;
        beamLight.intensity = 1.6 + 1.2 * flick;

        // Domains drift and resolve: colour lerps to the winner, emissive
        // brightens as ee rises, with a per-blob pulse so the field shimmers.
        for (const b of domains) {
          b.material.emissive.copy(b.userData.start).lerp(winColor, s);
          const pulse = 0.5 + 0.5 * Math.sin(t * 4 + b.userData.phase);
          b.material.emissiveIntensity = (0.2 + 0.8 * s) * pulse;
          const sway = (1 - s) * 0.06;
          b.position.x = b.userData.base.x + Math.sin(t * 2.3 + b.userData.phase) * sway;
          b.position.y = b.userData.base.y + Math.cos(t * 1.9 + b.userData.phase) * sway;
        }
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
