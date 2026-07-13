// Stage 4 — Alkaline hydrothermal vent · bench-top vent reactor.
//
// Lane–Martin chemiosmosis on the bench: a sealed glass/steel reactor column
// clamped to a ring-stand, packed with a porous FeS mineral chimney lit by a
// candle-warm glow from below. Alkaline fluid percolates up across a proton
// gradient, bubbling, driving Wood–Ljungdahl carbon fixation. A pH probe enters
// the top; copper tubing feeds it; a Bakelite readout panel beside it shows live
// PMF (mV) and ΔG (kJ/mol) on a glowing CanvasTexture display. Parts are named.

import * as THREE from 'three';
import { glassMat, steelMat, brassMat, copperMat, bakeliteMat, liquidMat, ringStand, part, makeDynamicTexture, V } from './lib.js';

export function build() {
  const group = new THREE.Group();
  group.name = 'vent-reactor';

  const cx = 0, colBot = 0.5, colH = 4.0, colR = 0.7;
  const colMid = colBot + colH / 2;

  // ── Ring-stand holding the column ─────────────────────────────────────────
  group.add(ringStand(2.7, -0.3, [colMid + 1.0, colMid - 1.0], 6.0));

  // ── Reactor column: tall glass cylinder with steel end-caps ───────────────
  const column = part(new THREE.CylinderGeometry(colR, colR, colH, 48, 1, true), glassMat(),
    'reactor-column', V(cx, colMid, 0));
  group.add(column);
  const fluid = part(new THREE.CylinderGeometry(colR * 0.95, colR * 0.95, colH * 0.92, 40),
    liquidMat(0x1c3a3a, { transmission: 0.7, roughness: 0.15, opacity: 0.8 }), 'reactor-fluid', V(cx, colMid, 0));
  group.add(fluid);
  const capTop = part(new THREE.CylinderGeometry(colR + 0.06, colR + 0.06, 0.28, 48), steelMat(),
    'end-cap-top', V(cx, colBot + colH + 0.08, 0));
  group.add(capTop);
  const capBot = part(new THREE.CylinderGeometry(colR + 0.08, colR + 0.06, 0.32, 48), steelMat(),
    'end-cap-bottom', V(cx, colBot - 0.1, 0));
  group.add(capBot);

  // ── Porous mineral chimney: stack of irregular dark cones/cylinders ───────
  const chimney = new THREE.Group(); chimney.name = 'chimney';
  // FeS mineral; its emissive pulses with the proton-motive force while running.
  const chimMat = new THREE.MeshStandardMaterial({ color: 0x2a211c, roughness: 0.95, metalness: 0.25, emissive: 0xffb866, emissiveIntensity: 0.12 });
  let cyN = colBot + 0.2;
  for (let i = 0; i < 7; i++) {
    const rTop = 0.34 - i * 0.03 + Math.sin(i * 1.7) * 0.04;
    const rBot = 0.4 - i * 0.025 + Math.cos(i) * 0.04;
    const h = 0.4 + (i % 2) * 0.18;
    const seg = part(new THREE.CylinderGeometry(rTop, rBot, h, 9), chimMat, `chimney-seg-${i}`,
      V(Math.sin(i * 2.1) * 0.06, cyN + h / 2, Math.cos(i * 1.3) * 0.06));
    seg.rotation.y = i * 0.5;
    chimney.add(seg);
    cyN += h * 0.85;
  }
  const chimTop = cyN;
  group.add(chimney);

  // ── Vent glow: emissive plug + warm point light from below ────────────────
  const ventGlow = part(new THREE.SphereGeometry(0.3, 20, 16),
    new THREE.MeshBasicMaterial({ color: 0xffb866 }), 'vent-glow', V(cx, colBot + 0.25, 0));
  group.add(ventGlow);
  const glowLight = new THREE.PointLight(0xffb866, 5, 4, 2);
  glowLight.position.set(cx, colBot + 0.4, 0);
  group.add(glowLight);

  // ── pH probe entering the top ─────────────────────────────────────────────
  const phProbe = part(new THREE.CylinderGeometry(0.05, 0.04, colH * 0.7, 16), steelMat(),
    'ph-probe', V(cx + 0.25, colBot + colH * 0.62, 0));
  group.add(phProbe);
  const phTip = part(new THREE.SphereGeometry(0.06, 12, 10), glassMat(),
    'ph-probe-tip', V(cx + 0.25, colBot + colH * 0.27, 0));
  group.add(phTip);

  // ── Copper gas line from the top cap arcing to the readout panel ──────────
  const gasLine = part(new THREE.TubeGeometry(new THREE.CatmullRomCurve3([
    V(cx + 0.4, colBot + colH + 0.1, 0), V(cx + 1.2, colBot + colH - 0.2, 0.2),
    V(cx + 2.0, 1.6, 0.3), V(cx + 2.3, 1.1, 0.2),
  ]), 40, 0.05, 12, false), copperMat(), 'gas-line');
  group.add(gasLine);

  // ── Readout panel: Bakelite box with a glowing PMF / ΔG display ───────────
  const panelPos = V(cx + 2.6, 0.9, 0.2);
  const panel = part(new THREE.BoxGeometry(1.3, 1.0, 0.6), bakeliteMat(0x1c1510), 'readout-panel', panelPos.clone());
  group.add(panel);
  const dyn = makeDynamicTexture(256);
  const display = part(new THREE.PlaneGeometry(1.0, 0.7),
    new THREE.MeshBasicMaterial({ map: dyn.tex, transparent: true }), 'readout-display',
    V(panelPos.x, panelPos.y + 0.05, panelPos.z + 0.31));
  group.add(display);
  // brass trim knob on the panel
  const panelKnob = part(new THREE.CylinderGeometry(0.08, 0.09, 0.12, 20), brassMat(),
    'panel-knob', V(panelPos.x + 0.45, panelPos.y - 0.35, panelPos.z + 0.3));
  panelKnob.rotation.x = Math.PI / 2;
  group.add(panelKnob);

  group.position.y = 0;

  // ── Bubbles rising through the column ─────────────────────────────────────
  const bubbleMat = new THREE.MeshStandardMaterial({ color: 0xddf2f0, transparent: true, opacity: 0.5, roughness: 0.2 });
  const bubbles = [];
  for (let i = 0; i < 22; i++) {
    const b = part(new THREE.SphereGeometry(0.03 + Math.random() * 0.03, 8, 8), bubbleMat, `bubble-${i}`);
    b.userData.reset = () => {
      b.position.set(cx + (Math.random() - 0.5) * colR * 1.2, colBot + Math.random() * 0.3, (Math.random() - 0.5) * colR * 1.2);
      b.userData.v = 0.5 + Math.random() * 0.8;
    };
    b.userData.reset();
    group.add(b); bubbles.push(b);
  }

  // ── Thin mineral-precipitate plume rising off the chimney top (unnamed) ───
  // Fresh FeS precipitates in the alkaline upwelling: a faint warm thread of
  // fine particles drifting up the column centre, only while the vent runs.
  const plumeTop = colBot + colH * 0.9;
  const plumeMat = new THREE.MeshBasicMaterial({ color: 0xffb866, transparent: true, opacity: 0.0 });
  const plume = [];
  for (let i = 0; i < 26; i++) {
    const p = new THREE.Mesh(new THREE.SphereGeometry(0.012 + Math.random() * 0.016, 6, 6), plumeMat);
    p.userData.reset = () => {
      p.position.set(cx + (Math.random() - 0.5) * 0.1, chimTop + Math.random() * 0.15, (Math.random() - 0.5) * 0.1);
      p.userData.v = 0.22 + Math.random() * 0.3;
      p.userData.ph = Math.random() * Math.PI * 2;          // sway phase
    };
    p.userData.reset();
    group.add(p); plume.push(p);
  }

  // ── Animation ──────────────────────────────────────────────────────────────
  const { ctx, size } = dyn;
  let running = true, progress = 0, pmf = 150, dG = -20;

  function paintDisplay() {
    ctx.fillStyle = '#06120e';
    ctx.fillRect(0, 0, size, size);
    ctx.strokeStyle = '#1f5a3a'; ctx.lineWidth = 6; ctx.strokeRect(8, 8, size - 16, size - 16);
    ctx.textAlign = 'left'; ctx.fillStyle = '#7df0c0';
    ctx.font = '24px monospace'; ctx.fillText('VENT REACTOR', 28, 52);
    ctx.font = 'bold 40px monospace'; ctx.fillStyle = '#9fffe0';
    ctx.fillText('PMF', 30, 120); ctx.fillText(`${pmf.toFixed(0)} mV`, 30, 162);
    ctx.fillStyle = '#ffd24a';
    ctx.fillText('ΔG', 30, 218); ctx.fillText(`${dG.toFixed(1)} kJ`, 30, 256);
    dyn.tex.needsUpdate = true;
  }
  paintDisplay();

  return Object.assign(group, { userData: Object.assign(group.userData, {
    anim: {
      setRunning(on) {
        running = on;
        glowLight.intensity = on ? 5 : 0;
        ventGlow.visible = on;
        for (const b of bubbles) b.visible = on;
        for (const p of plume) p.visible = on;
        if (!on) {
          // settle to a calm, un-pulsing baseline
          glowLight.color.setHex(0xffb866);
          glowLight.position.set(cx, colBot + 0.4, 0);
          chimMat.emissiveIntensity = 0.12;
          plumeMat.opacity = 0.0;
        }
      },
      getProgress() { return progress; },
      reset() { progress = 0; pmf = 150; dG = -20; paintDisplay(); },
      update(dt, t) {
        if (!running) {
          for (const b of bubbles) b.visible = false;
          for (const p of plume) p.visible = false;
          ventGlow.visible = false;
          return;
        }
        progress = Math.min(1, progress + dt / 40);
        // bubbles rise
        for (const b of bubbles) {
          b.visible = true;
          b.position.y += b.userData.v * dt;
          if (b.position.y > colBot + colH * 0.9) b.userData.reset();
        }
        // warm flicker + shimmer: the vent breathes via slow thermal convection,
        // wavering gently in intensity and drifting as the warm plume rolls.
        const flick = 0.9 + Math.random() * 0.2;
        glowLight.intensity = 5 * flick;
        glowLight.position.set(
          cx + Math.sin(t * 1.8) * 0.05,
          colBot + 0.4 + Math.sin(t * 1.3) * 0.06,
          Math.cos(t * 1.5) * 0.05,
        );
        const warm = 0.5 + 0.5 * Math.sin(t * 1.5);                 // slow warm breath
        glowLight.color.setRGB(1.0, 0.69 + 0.04 * warm, 0.38 + 0.04 * warm);
        ventGlow.visible = true;
        ventGlow.scale.setScalar(0.85 + 0.3 * flick);
        // readouts drift as the gradient builds
        pmf = 150 + progress * 60 + Math.sin(t * 1.3) * 8;
        dG = -20 - progress * 25 + Math.cos(t * 0.9) * 3;
        // chimney mineral glows with the proton-motive force: brighter as the
        // gradient steepens, pulsing on the same beat the PMF reading swings.
        const pmfNorm = Math.max(0, Math.min(1, (pmf - 150) / 80));
        chimMat.emissiveIntensity = 0.12 + pmfNorm * 0.55 + 0.12 * (0.5 + 0.5 * Math.sin(t * 1.3));
        // mineral-precipitate plume threads up the column, swaying gently
        const plumeOpacity = 0.12 + pmfNorm * 0.3;
        plumeMat.opacity = plumeOpacity;
        for (const p of plume) {
          p.visible = true;
          p.position.y += p.userData.v * dt;
          p.position.x = cx + Math.sin(t * 1.4 + p.userData.ph) * 0.07;
          p.position.z = Math.cos(t * 1.1 + p.userData.ph) * 0.07;
          if (p.position.y > plumeTop) p.userData.reset();
        }
        paintDisplay();
      },
    },
  }) });
}

export const meta = {
  id: 'stage4-vent',
  label: 'Stage 4 — Hydrothermal vent',
  title: 'Alkaline-vent bench reactor',
  blurb: 'Lane–Martin chemiosmosis: alkaline fluid percolates through an FeS chimney across a '
       + 'proton gradient, driving Wood–Ljungdahl carbon fixation. PMF and ΔG read out live.',
  build,
};
