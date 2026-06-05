// Stage 7 — RNA world · Ribozyme replication assay.
//
// A vintage PCR thermocycler: a boxy bakelite/steel instrument with a hinged
// heated lid over a heat block holding an 8-tube strip, a front control panel
// with a small glowing display cycling the thermal program (95→55→72 °C). A
// gel-doc beside it shows migrating bands drifting downward. When run, the
// display cycles, the lid heat glow pulses, and the gel bands migrate. progress
// tracks cycle count — RNA replicating below the error threshold ε_c.

import * as THREE from 'three';
import { part, steelMat, bakeliteMat, glassMat, darkMetalMat, brassMat, makeDynamicTexture, V } from './lib.js';

const PROGRAM = [95, 55, 72]; // denature / anneal / extend (°C)
const STEP_T = 1.6;           // seconds per thermal step

function drawDisplay(ctx, size, temp, cycle, phase) {
  ctx.fillStyle = '#04130c'; ctx.fillRect(0, 0, size, size);
  ctx.fillStyle = '#0d3a22'; ctx.fillRect(6, 6, size - 12, size - 12);
  ctx.fillStyle = '#39ff9a'; ctx.textAlign = 'center';
  ctx.font = `bold ${size * 0.34}px "Courier New", monospace`;
  ctx.fillText(`${Math.round(temp)}°C`, size / 2, size * 0.46);
  ctx.font = `${size * 0.13}px "Courier New", monospace`;
  ctx.fillText(phase, size / 2, size * 0.66);
  ctx.fillText(`CYC ${cycle}`, size / 2, size * 0.86);
}

function drawGel(ctx, size, offset) {
  ctx.fillStyle = '#07110d'; ctx.fillRect(0, 0, size, size);
  const lanes = 6;
  for (let l = 0; l < lanes; l++) {
    const x = (l + 0.5) * (size / lanes);
    // well at top
    ctx.fillStyle = '#1c2a22'; ctx.fillRect(x - size * 0.05, 4, size * 0.1, 8);
    // migrating bands per lane, drifting down with offset
    for (let b = 0; b < 4; b++) {
      const base = size * (0.18 + b * 0.18) + (offset * size * 0.5) % (size * 0.7);
      const y = 14 + (base % (size - 28));
      const w = size * 0.07 * (1 - b * 0.12);
      const a = 0.85 - b * 0.15;
      ctx.fillStyle = `rgba(140,255,180,${a})`;
      ctx.fillRect(x - w, y, w * 2, size * 0.022);
    }
  }
}

export function build() {
  const group = new THREE.Group();
  group.name = 'rna-thermocycler-1953';

  // ── Cycler body (boxy bakelite + steel) ────────────────────────────────────
  const body = part(new THREE.BoxGeometry(3.4, 1.6, 2.4), bakeliteMat(0x2a221a), 'cycler-body', V(-0.6, 0.8, 0));
  group.add(body);
  // steel front fascia
  group.add(part(new THREE.BoxGeometry(3.42, 0.9, 0.06), steelMat(), 'cycler-fascia', V(-0.6, 0.55, 1.21)));

  // ── Heat block on top, recessed ────────────────────────────────────────────
  // Emissive-capable steel so the block itself can glow hot during denature and
  // go dark/cold at anneal — this is the visible heart of the thermal cycle.
  const blockMat = new THREE.MeshStandardMaterial({
    color: 0x8c8f96, metalness: 0.9, roughness: 0.45,
    emissive: new THREE.Color(0xffb866), emissiveIntensity: 0,
  });
  const block = part(new THREE.BoxGeometry(2.6, 0.4, 1.2), blockMat, 'heat-block', V(-0.6, 1.6, 0));
  group.add(block);

  // ── 8-tube strip seated in the block ──────────────────────────────────────
  const tubeMat = glassMat();
  const tubeXs = [];
  const reactMats = [];      // per-tube reaction-fluid materials (warm when hot)
  for (let i = 0; i < 8; i++) {
    const tx = -0.6 - 1.0 + i * (2.0 / 7);
    tubeXs.push(tx);
    const t = part(new THREE.CylinderGeometry(0.1, 0.05, 0.42, 16), tubeMat, `tube-${i}`, V(tx, 1.78, 0));
    group.add(t);
    // reaction fluid inside each tube (unnamed) — emissive ramps with the block
    const rMat = new THREE.MeshStandardMaterial({
      color: 0x163a30, roughness: 0.3, metalness: 0.0, transparent: true, opacity: 0.85,
      emissive: new THREE.Color(0x3fe0d0), emissiveIntensity: 0.0,
    });
    const fluid = new THREE.Mesh(new THREE.CylinderGeometry(0.075, 0.045, 0.28, 14), rMat);
    fluid.position.set(tx, 1.71, 0);
    group.add(fluid);
    reactMats.push(rMat);
    // cap
    group.add(part(new THREE.CylinderGeometry(0.12, 0.1, 0.08, 16), darkMetalMat(), `tube-cap-${i}`, V(tx, 2.0, 0)));
  }
  // named "tube-strip" connector spine
  group.add(part(new THREE.BoxGeometry(2.1, 0.06, 0.16), plasticSpine(), 'tube-strip', V(-0.6, 2.02, 0.0)));

  // ── Hinged heated lid (angled open) ────────────────────────────────────────
  const lid = new THREE.Group();
  lid.name = 'lid';
  const lidPlate = part(new THREE.BoxGeometry(2.8, 0.18, 1.4), steelMat(), 'lid-plate', V(0, 0, 0));
  lid.add(lidPlate);
  // Heater face is emissive-capable so the underside of the lid glows hot with
  // the block during denature, then fades as it cools.
  const lidFaceMat = new THREE.MeshStandardMaterial({
    color: 0x1b1b1f, metalness: 0.7, roughness: 0.5,
    emissive: new THREE.Color(0xffb866), emissiveIntensity: 0,
  });
  lid.add(part(new THREE.BoxGeometry(2.6, 0.1, 1.2), lidFaceMat, 'lid-heater-face', V(0, -0.12, 0)));
  // hinge at back edge, lid raised at an angle
  lid.position.set(-0.6, 1.95, -0.6);
  lid.rotation.x = -0.9;
  // shift so it rotates about the back hinge
  lidPlate.position.y = 0.0; lid.children.forEach(c => { c.position.z += 0.6; c.position.y += 0.1; });
  group.add(lid);
  // heat-glow plane under the lid heater
  const glow = part(new THREE.PlaneGeometry(2.5, 1.1),
    new THREE.MeshBasicMaterial({ color: 0xff6a2a, transparent: true, opacity: 0.0 }), 'lid-glow', V(-0.6, 1.84, 0));
  glow.rotation.x = -Math.PI / 2;
  group.add(glow);
  const heatLight = new THREE.PointLight(0xff7a30, 0, 3, 2);
  heatLight.position.set(-0.6, 2.0, 0);
  group.add(heatLight);

  // ── Front control panel + glowing display ─────────────────────────────────
  group.add(part(new THREE.BoxGeometry(1.4, 0.7, 0.05), darkMetalMat(), 'control-panel', V(-1.2, 0.55, 1.24)));
  const dispTex = makeDynamicTexture(256);
  drawDisplay(dispTex.ctx, dispTex.size, PROGRAM[0], 1, 'DENATURE');
  dispTex.tex.needsUpdate = true;
  group.add(part(new THREE.PlaneGeometry(0.85, 0.5),
    new THREE.MeshBasicMaterial({ map: dispTex.tex }), 'display', V(-1.2, 0.62, 1.27)));
  // a couple of brass knobs on the panel
  for (const kx of [-0.35, 0.0]) {
    group.add(part(new THREE.CylinderGeometry(0.1, 0.1, 0.1, 18), brassMat(), `panel-knob-${kx}`, V(-0.6 + kx + 0.55, 0.4, 1.27)));
  }

  // ── Gel-doc beside the cycler (right) ──────────────────────────────────────
  group.add(part(new THREE.BoxGeometry(1.7, 2.2, 1.2), bakeliteMat(0x1d1712), 'gel-doc', V(2.2, 1.1, 0)));
  const gelTex = makeDynamicTexture(256);
  drawGel(gelTex.ctx, gelTex.size, 0);
  gelTex.tex.needsUpdate = true;
  group.add(part(new THREE.PlaneGeometry(1.3, 1.3),
    new THREE.MeshBasicMaterial({ map: gelTex.tex }), 'gel-screen', V(2.2, 1.4, 0.61)));
  group.add(part(new THREE.TorusGeometry(0.68, 0.04, 10, 40), steelMat(), 'gel-bezel', V(2.2, 1.4, 0.62)));

  // ── Bubbles inside the reaction tubes (rise during the hot/denature phase) ──
  // Unnamed dynamic meshes; each is bound to a tube column and resets to the
  // bottom of the fluid once it reaches the surface.
  const bubbleGeo = new THREE.SphereGeometry(0.022, 8, 8);
  const bubbleMat = new THREE.MeshStandardMaterial({
    color: 0xeafff8, roughness: 0.2, metalness: 0.0, transparent: true, opacity: 0.7,
  });
  const TUBE_BASE = 1.60, TUBE_TOP = 1.86;   // fluid span inside a tube
  const bubbles = [];
  for (let i = 0; i < 8; i++) {
    const tx = tubeXs[i];
    for (let k = 0; k < 4; k++) {
      const b = new THREE.Mesh(bubbleGeo, bubbleMat);
      b.userData.tx = tx;
      b.userData.reset = () => {
        b.position.set(tx + (Math.random() - 0.5) * 0.06, TUBE_BASE + Math.random() * 0.04,
          (Math.random() - 0.5) * 0.06);
        b.userData.v = 0.10 + Math.random() * 0.16;
        b.userData.wob = Math.random() * Math.PI * 2;
      };
      b.userData.reset();
      b.visible = false;
      group.add(b);
      bubbles.push(b);
    }
  }

  group.position.y = 0;

  // ── Animation ──────────────────────────────────────────────────────────────
  let running = true, progress = 0, clock = 0, cycle = 1, gelOffset = 0;
  let phaseClock = 0;          // advances only while running → pulse stops on Stop
  let heat = 0;                // smoothed 0..1 thermal value (denature=1, anneal=0)
  const TOTAL_CYCLES = 30;
  const phaseNames = ['DENATURE', 'ANNEAL', 'EXTEND'];
  const COLD = new THREE.Color(0x14141a);     // block colour when cold
  const HOT = new THREE.Color(0xffb866);      // warm heat-glow colour
  const blockBaseRGB = { r: 0x8c / 255, g: 0x8f / 255, b: 0x96 / 255 };

  // Smoothly interpolate the setpoint program so temperature RAMPS between
  // steps (a real block has thermal inertia) rather than snapping — this gives
  // the emissive a continuous driver across the whole loop.
  function smoothTemp(c) {
    const fStep = c / STEP_T;
    const i = Math.floor(fStep) % PROGRAM.length;
    const frac = fStep - Math.floor(fStep);
    const a = PROGRAM[i];
    const b = PROGRAM[(i + 1) % PROGRAM.length];
    const e = frac * frac * (3 - 2 * frac);   // smoothstep ease
    return { temp: a + (b - a) * e, stepIdx: i };
  }

  group.userData.anim = {
    setRunning(on) { running = on; },
    getProgress() { return progress; },
    reset() {
      progress = 0; clock = 0; cycle = 1; gelOffset = 0; phaseClock = 0; heat = 0;
      drawDisplay(dispTex.ctx, dispTex.size, PROGRAM[0], 1, phaseNames[0]); dispTex.tex.needsUpdate = true;
      drawGel(gelTex.ctx, gelTex.size, 0); gelTex.tex.needsUpdate = true;
      glow.material.opacity = 0; heatLight.intensity = 0;
      blockMat.emissiveIntensity = 0; lidFaceMat.emissiveIntensity = 0;
      blockMat.color.setRGB(blockBaseRGB.r, blockBaseRGB.g, blockBaseRGB.b);
      for (const rMat of reactMats) rMat.emissiveIntensity = 0;
      for (const b of bubbles) b.visible = false;
    },
    update(dt, t) {
      if (!running) {
        // Idle: relax the whole thermal display toward cold/dark and freeze bubbles.
        heat *= 0.9;
        glow.material.opacity *= 0.9;
        heatLight.intensity *= 0.9;
        blockMat.emissiveIntensity *= 0.9;
        lidFaceMat.emissiveIntensity *= 0.9;
        blockMat.color.lerp(new THREE.Color(blockBaseRGB.r, blockBaseRGB.g, blockBaseRGB.b), 0.1);
        for (const rMat of reactMats) rMat.emissiveIntensity *= 0.9;
        for (const b of bubbles) b.visible = false;
        return;
      }
      clock += dt;
      phaseClock += dt;
      const { temp, stepIdx } = smoothTemp(clock);
      const totalSteps = Math.floor(clock / STEP_T);
      cycle = 1 + Math.floor(totalSteps / PROGRAM.length);
      drawDisplay(dispTex.ctx, dispTex.size, temp, Math.min(cycle, TOTAL_CYCLES), phaseNames[stepIdx]);
      dispTex.tex.needsUpdate = true;

      // Smoothed thermal value (95→1, 55→0) drives every hot element.
      const target = (temp - 55) / 40;          // 0..1
      heat += (target - heat) * Math.min(1, dt * 6);
      const pulse = 0.55 + 0.45 * Math.sin(phaseClock * 5);   // shimmer of the heater

      // Heat block glows hot and shifts colour toward warm at denature.
      blockMat.emissiveIntensity = heat * (0.9 + 0.25 * pulse);
      blockMat.color.copy(COLD).lerp(HOT, 0.15 + heat * 0.55).lerp(
        new THREE.Color(blockBaseRGB.r, blockBaseRGB.g, blockBaseRGB.b), 0.35 * (1 - heat));
      // Lid heater face + glow plane + point light pulse in lock-step.
      lidFaceMat.emissiveIntensity = heat * (0.8 + 0.3 * pulse);
      glow.material.opacity = 0.1 + heat * 0.55 * pulse;
      heatLight.intensity = 0.4 + heat * 2.6 * pulse;
      // Reaction fluid brightens (teal → warm) as it heats.
      for (const rMat of reactMats) {
        rMat.emissiveIntensity = 0.05 + heat * 0.6 * pulse;
        rMat.emissive.copy(new THREE.Color(0x3fe0d0)).lerp(HOT, heat * 0.7);
      }

      // Bubbles boil up the tubes during the hot phase (heat > ~0.4).
      const boiling = heat > 0.4;
      for (const b of bubbles) {
        if (!boiling) { b.visible = false; continue; }
        b.visible = true;
        b.userData.wob += dt * 6;
        b.position.y += b.userData.v * heat * dt;
        b.position.x = b.userData.tx + Math.sin(b.userData.wob) * 0.012;
        if (b.position.y > TUBE_TOP) b.userData.reset();
      }

      // Gel bands migrate downward (driven by replication over cycles).
      gelOffset += dt * 0.04;
      drawGel(gelTex.ctx, gelTex.size, gelOffset); gelTex.tex.needsUpdate = true;
      // progress over cycles
      progress = Math.min(1, (clock / STEP_T / PROGRAM.length) / TOTAL_CYCLES);
    },
  };
  return group;
}

// thin plastic spine for the tube strip
function plasticSpine() {
  return new THREE.MeshStandardMaterial({ color: 0xcfd6da, roughness: 0.5, metalness: 0.0, transparent: true, opacity: 0.7 });
}

export const meta = {
  id: 'stage7-rna',
  label: 'Stage 7 — RNA world',
  title: 'Ribozyme replication assay',
  blurb: 'RNA is dual-role — it stores information AND catalyses (ribozymes). Below the error threshold ε_c it replicates; above it the quasispecies melts down.',
  build,
};
