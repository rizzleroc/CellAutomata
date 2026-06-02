// Stage 11 — LUCA distillation · genomics console + tree of life.
//
// The only abstract stage. A vintage-futurist console: a steel/Bakelite cabinet
// with a large glowing screen (lib.makeDynamicTexture) that distils a list of
// gene families (~16 → a highlighted conserved core), a small "sequencer" unit
// beside it with a keyboard, and a faint glowing "tree of life" hologram above
// built from thin emissive line branches converging downward to a single root —
// LUCA. The branches pulse/converge; the screen highlights surviving core genes
// one by one (Weiss et al. 2016 comparative-genomics parsimony).
// progress = fraction of gene families distilled to the core.

import * as THREE from 'three';
import { part, V, steelMat, bakeliteMat, brassMat, emissiveMat, makeDynamicTexture } from './lib.js';

export function build() {
  const group = new THREE.Group();
  group.name = 'luca-console';

  // ── Console cabinet (steel body, bakelite trim) ───────────────────────────
  const cabinet = part(new THREE.BoxGeometry(3.6, 2.2, 1.4), bakeliteMat(0x20242a), 'console-cabinet', V(0, 1.1, 0));
  group.add(cabinet);
  group.add(part(new THREE.BoxGeometry(3.8, 0.3, 1.6), steelMat(), 'console-plinth', V(0, 0.15, 0)));
  // angled keyboard deck in front
  const keyboard = part(new THREE.BoxGeometry(3.2, 0.5, 0.9), bakeliteMat(0x171a1f), 'keyboard', V(0, 0.55, 0.85));
  keyboard.rotation.x = 0.4; group.add(keyboard);
  for (let i = 0; i < 10; i++) {
    const k = part(new THREE.BoxGeometry(0.18, 0.08, 0.18), bakeliteMat(0x2c3037),
      `key-${i}`, V(-1.3 + (i % 5) * 0.6, 0.78 - (i < 5 ? 0 : 0.18), 0.78 + (i < 5 ? 0 : 0.18)));
    k.rotation.x = 0.4; group.add(k);
  }

  // ── Glowing screen (the distillation readout) ─────────────────────────────
  const dyn = makeDynamicTexture(256);
  const screen = part(new THREE.PlaneGeometry(2.7, 1.5),
    new THREE.MeshBasicMaterial({ map: dyn.tex }), 'screen', V(0, 1.35, 0.72));
  group.add(screen);
  group.add(part(new THREE.BoxGeometry(3.0, 1.8, 0.12), brassMat(), 'screen-bezel', V(0, 1.35, 0.66)));
  const screenLight = new THREE.PointLight(0x66ffcc, 0.8, 3, 2);
  screenLight.position.set(0, 1.35, 1.2); group.add(screenLight);

  // ── Sequencer unit beside the console ─────────────────────────────────────
  const sequencer = part(new THREE.BoxGeometry(1.0, 1.4, 1.0), steelMat(), 'sequencer', V(2.6, 0.85, 0));
  group.add(sequencer);
  group.add(part(new THREE.CylinderGeometry(0.32, 0.32, 0.2, 24), bakeliteMat(0x15171b), 'sequencer-reel', V(2.6, 1.4, 0.45)));
  const seqLamp = part(new THREE.SphereGeometry(0.07, 12, 12), emissiveMat(0x55ff99), 'sequencer-lamp', V(2.6, 1.55, 0.4));
  group.add(seqLamp);

  // ── Tree-of-life hologram above the console ───────────────────────────────
  // Thin emissive line branches converging downward to a single root (LUCA).
  const treeGroup = new THREE.Group(); treeGroup.name = 'tree-hologram';
  treeGroup.position.set(0, 3.1, 0.1);
  const rootY = 0; // local
  const lineMat = new THREE.LineBasicMaterial({ color: 0x7fffd0, transparent: true, opacity: 0.7 });
  // build by levels: 8 tips at top fan in to 1 root
  const levels = 4;
  let nodes = [];
  for (let i = 0; i < 8; i++) nodes.push({ x: -2.1 + i * 0.6, y: 1.8 });
  const allPts = [];
  for (let lvl = 0; lvl < levels; lvl++) {
    const next = [];
    for (let i = 0; i < nodes.length; i += 2) {
      const a = nodes[i], b = nodes[i + 1] || nodes[i];
      const px = (a.x + b.x) / 2, py = a.y - 0.45;
      allPts.push([a.x, a.y, px, py], [b.x, b.y, px, py]);
      next.push({ x: px, y: py });
    }
    nodes = next;
  }
  // final stem to the root
  allPts.push([nodes[0].x, nodes[0].y, 0, rootY - 0.1]);
  const posArr = new Float32Array(allPts.length * 2 * 3);
  let k = 0;
  for (const [x1, y1, x2, y2] of allPts) {
    posArr[k++] = x1; posArr[k++] = y1; posArr[k++] = 0;
    posArr[k++] = x2; posArr[k++] = y2; posArr[k++] = 0;
  }
  const branchGeo = new THREE.BufferGeometry();
  branchGeo.setAttribute('position', new THREE.BufferAttribute(posArr, 3));
  const branches = new THREE.LineSegments(branchGeo, lineMat);
  branches.name = 'branch-lines'; treeGroup.add(branches);
  // glowing root node = LUCA
  const root = part(new THREE.SphereGeometry(0.14, 20, 16), emissiveMat(0xaaffe0), 'root', V(0, rootY - 0.1, 0));
  treeGroup.add(root);
  const rootGlow = new THREE.PointLight(0x7fffd0, 0.6, 2.5, 2);
  rootGlow.position.set(0, rootY - 0.1, 0); treeGroup.add(rootGlow);
  group.add(treeGroup);

  group.position.y = 0;

  // ── Gene-family list (16 → core) painted on the screen ────────────────────
  const GENES = [
    'rpoB', 'rpsC', 'fdhF', 'cooS', 'nifH', 'mtrH', 'ackA', 'fwdB',
    'tRNA-fMet', 'rnpA', 'atpA', 'ribL2', 'hdrA', 'echE', 'porA', 'glyA',
  ];
  // core survivors (highlighted one by one): indices that persist
  const coreOrder = [0, 8, 2, 10, 3, 5, 12, 1];
  let revealed = 0; // how many core genes highlighted

  function paint(t) {
    const ctx = dyn.ctx, S = dyn.size;
    ctx.fillStyle = '#03110d'; ctx.fillRect(0, 0, S, S);
    // scanline flicker
    ctx.fillStyle = 'rgba(80,255,180,0.04)';
    for (let y = 0; y < S; y += 4) ctx.fillRect(0, y + (Math.sin(t * 4) > 0 ? 0 : 2), S, 1);
    ctx.fillStyle = '#3fffb0'; ctx.font = 'bold 16px monospace'; ctx.textAlign = 'left';
    ctx.fillText('LUCA · CORE GENE SET', 14, 24);
    ctx.font = '13px monospace';
    const coreSet = new Set(coreOrder.slice(0, revealed));
    for (let i = 0; i < GENES.length; i++) {
      const col = i < 8 ? 14 : 132, row = (i % 8);
      const y = 50 + row * 24;
      if (coreSet.has(i)) {
        ctx.fillStyle = '#aaffd9';
        ctx.fillText('▶ ' + GENES[i], col, y);
      } else {
        // un-conserved families fade out
        const fade = revealed > 0 && !coreOrder.includes(i) ? 0.25 : 0.6;
        ctx.fillStyle = `rgba(63,255,176,${fade})`;
        ctx.fillText('  ' + GENES[i], col, y);
      }
    }
    ctx.fillStyle = '#3fffb0'; ctx.font = '12px monospace';
    ctx.fillText('parsimony distill: ' + revealed + '/' + coreOrder.length, 14, S - 12);
    dyn.tex.needsUpdate = true;
  }
  paint(0);

  let running = true, progress = 0, timer = 0;
  group.userData.anim = {
    setRunning(on) { running = on; },
    getProgress() { return progress; },
    reset() { revealed = 0; progress = 0; timer = 0; paint(0); },
    update(dt, t) {
      if (running) {
        timer += dt;
        if (timer > 0.9 && revealed < coreOrder.length) { revealed++; timer = 0; }
        progress = revealed / coreOrder.length;
        // tree pulses + converges
        const pulse = 0.45 + 0.35 * (0.5 + 0.5 * Math.sin(t * 2));
        lineMat.opacity = pulse;
        rootGlow.intensity = 0.4 + 0.5 * (0.5 + 0.5 * Math.sin(t * 2 + 1)) + progress * 0.6;
        root.scale.setScalar(1 + 0.15 * Math.sin(t * 3) + progress * 0.4);
        seqLamp.material.color.setHex(Math.sin(t * 6) > 0 ? 0x55ff99 : 0x114422);
        screenLight.intensity = 0.7 + 0.15 * Math.sin(t * 5);
      }
      paint(t);
    },
  };
  return group;
}

export const meta = {
  id: 'stage11-luca',
  label: 'Stage 11 — LUCA',
  title: 'Genomics console · tree of life',
  blurb: 'Weiss et al. (2016) comparative-genomics parsimony distils the conserved core '
       + 'gene set shared by every surviving lineage — the Last Universal Common Ancestor.',
  build,
};
