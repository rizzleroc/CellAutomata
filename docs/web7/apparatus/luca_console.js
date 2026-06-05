// Stage 11 — LUCA distillation · genomics console + tree of life.
//
// The only abstract stage. A vintage-futurist console: a steel/Bakelite cabinet
// with a large glowing screen (lib.makeDynamicTexture) that distils a list of
// gene families (~16 → a highlighted conserved core), a small "sequencer" unit
// beside it with a keyboard, and a faint glowing "tree of life" hologram above
// built from thin emissive line branches converging downward to a single root —
// LUCA. When "Run experiment" is pressed the whole console comes alive: the
// tree-of-life hologram slowly ROTATES (teal, emissive), a bank of indicator
// lamps blinks, a genomic readout ticker scrolls across the panel, and a glowing
// "core" node brightens/condenses as the conserved gene set distils.
// (Weiss et al. 2016 comparative-genomics parsimony.)
// progress = fraction of gene families distilled to the core.

import * as THREE from 'three';
import { part, V, steelMat, bakeliteMat, brassMat, emissiveMat, makeDynamicTexture } from './lib.js';

// Light/emissive palette — teal, magenta, warm (no brass UI lighting).
const TEAL = 0x3fe0d0;
const MAGENTA = 0xd77bff;
const WARM = 0xffb866;
const TEAL_DIM = 0x0e2a27;
const MAGENTA_DIM = 0x2a1430;
const WARM_DIM = 0x2e1f10;

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
  const screenLight = new THREE.PointLight(TEAL, 0.8, 3, 2);
  screenLight.position.set(0, 1.35, 1.2); group.add(screenLight);

  // ── Sequencer unit beside the console ─────────────────────────────────────
  const sequencer = part(new THREE.BoxGeometry(1.0, 1.4, 1.0), steelMat(), 'sequencer', V(2.6, 0.85, 0));
  group.add(sequencer);
  group.add(part(new THREE.CylinderGeometry(0.32, 0.32, 0.2, 24), bakeliteMat(0x15171b), 'sequencer-reel', V(2.6, 1.4, 0.45)));
  const seqLamp = part(new THREE.SphereGeometry(0.07, 12, 12), emissiveMat(TEAL), 'sequencer-lamp', V(2.6, 1.55, 0.4));
  group.add(seqLamp);

  // ── Console indicator-lamp bank (UNNAMED dynamic elements) ─────────────────
  // A row of small emissive lamps along the cabinet face that blink in sequence
  // while the experiment runs (and a soft point light each so the blink reads as
  // light, not just colour). Calm/steady-dim when stopped.
  const lampHexes = [TEAL, MAGENTA, WARM, TEAL, MAGENTA, WARM, TEAL];
  const lampDims = [TEAL_DIM, MAGENTA_DIM, WARM_DIM, TEAL_DIM, MAGENTA_DIM, WARM_DIM, TEAL_DIM];
  const lamps = [];
  for (let i = 0; i < lampHexes.length; i++) {
    const x = -1.5 + i * 0.5;
    const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.06, 12, 12), emissiveMat(lampDims[i]));
    bulb.position.set(x, 0.45, 0.71);
    group.add(bulb);
    const light = new THREE.PointLight(lampHexes[i], 0.0, 1.2, 2);
    light.position.set(x, 0.45, 0.95);
    group.add(light);
    lamps.push({ bulb, light, on: lampHexes[i], off: lampDims[i] });
  }

  // ── Scrolling genomic readout ticker (UNNAMED dynamic elements) ────────────
  // A strip of short emissive bars beneath the screen that march sideways like a
  // sequencer trace ("…ACGT…") while running, looping when they run off the end.
  const tickerY = 0.34, tickerZ = 0.73;
  const tickerX0 = -1.45, tickerX1 = 1.45, tickerSpan = tickerX1 - tickerX0;
  const ticks = [];
  const TICKS = 22;
  for (let i = 0; i < TICKS; i++) {
    const h = 0.05 + 0.10 * ((i * 7) % 5) / 4;          // varied bar heights (the "trace")
    const hex = [TEAL, MAGENTA, WARM][i % 3];
    const bar = new THREE.Mesh(new THREE.BoxGeometry(0.04, h, 0.02), emissiveMat(hex));
    bar.userData.h = h;
    bar.position.set(tickerX0 + (i / TICKS) * tickerSpan, tickerY, tickerZ);
    group.add(bar);
    ticks.push(bar);
  }

  // ── Tree-of-life hologram above the console ───────────────────────────────
  // Thin emissive line branches converging downward to a single root (LUCA).
  const treeGroup = new THREE.Group(); treeGroup.name = 'tree-hologram';
  treeGroup.position.set(0, 3.1, 0.1);
  const rootY = 0; // local
  const lineMat = new THREE.LineBasicMaterial({ color: TEAL, transparent: true, opacity: 0.7 });
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
  // glowing tip nodes at the leaves of the tree (UNNAMED) — they twinkle as the
  // distillation surveys each lineage, so the rotating hologram clearly lives.
  const tipMat = new THREE.MeshBasicMaterial({ color: TEAL, transparent: true, opacity: 0.85 });
  const tips = [];
  for (let i = 0; i < 8; i++) {
    const tip = new THREE.Mesh(new THREE.SphereGeometry(0.05, 10, 8), tipMat.clone());
    tip.position.set(-2.1 + i * 0.6, 1.8, 0);
    treeGroup.add(tip);
    tips.push(tip);
  }
  // glowing root node = LUCA (the distilled "core"): brightens + condenses
  const rootMat = emissiveMat(TEAL);
  const root = part(new THREE.SphereGeometry(0.14, 20, 16), rootMat, 'root', V(0, rootY - 0.1, 0));
  treeGroup.add(root);
  // a soft halo shell around the core that condenses (shrinks) as genes distil
  const coreHalo = new THREE.Mesh(
    new THREE.SphereGeometry(0.34, 20, 16),
    new THREE.MeshBasicMaterial({ color: TEAL, transparent: true, opacity: 0.18 }),
  );
  coreHalo.position.set(0, rootY - 0.1, 0);
  treeGroup.add(coreHalo);
  const rootGlow = new THREE.PointLight(TEAL, 0.6, 2.5, 2);
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
  let scroll = 0;   // genomic-readout scroll offset (chars)
  const BASES = 'ACGT';

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
    // scrolling genomic readout strip along the bottom (a marching sequence)
    let line = '';
    const off = Math.floor(scroll);
    for (let i = 0; i < 30; i++) line += BASES[(i + off) * 2654435761 % 4 & 3];
    ctx.fillStyle = 'rgba(170,255,217,0.85)'; ctx.font = '12px monospace';
    ctx.fillText(line, 14, S - 28);
    ctx.fillStyle = '#3fffb0';
    ctx.fillText('parsimony distill: ' + revealed + '/' + coreOrder.length, 14, S - 12);
    dyn.tex.needsUpdate = true;
  }
  paint(0);

  // helper: 0..1 triangle/blink phase for a lamp index, offset along the bank
  const blink = (t, i) => 0.5 + 0.5 * Math.sin(t * 5 - i * 0.9);

  let running = true, progress = 0, timer = 0, spin = 0;
  group.userData.anim = {
    setRunning(on) { running = on; },
    getProgress() { return progress; },
    reset() {
      revealed = 0; progress = 0; timer = 0; spin = 0; scroll = 0;
      treeGroup.rotation.y = 0;
      paint(0);
    },
    update(dt, t) {
      if (running) {
        timer += dt;
        if (timer > 0.9 && revealed < coreOrder.length) { revealed++; timer = 0; }
        progress = revealed / coreOrder.length;

        // tree-of-life hologram slowly rotates (the headline motion)
        spin += dt * 0.6;
        treeGroup.rotation.y = spin;

        // branches pulse; tips twinkle out of phase
        lineMat.opacity = 0.45 + 0.35 * (0.5 + 0.5 * Math.sin(t * 2));
        for (let i = 0; i < tips.length; i++) {
          tips[i].material.opacity = 0.35 + 0.55 * blink(t * 0.7, i * 1.3);
          tips[i].scale.setScalar(0.8 + 0.5 * blink(t, i));
        }

        // glowing core brightens + condenses as the conserved set distils
        rootGlow.intensity = 0.4 + 0.5 * (0.5 + 0.5 * Math.sin(t * 2 + 1)) + progress * 1.2;
        root.scale.setScalar(1 + 0.15 * Math.sin(t * 3) + progress * 0.5);
        // warmer/brighter core colour as it condenses to LUCA
        rootMat.color.setRGB(0.25 + 0.7 * progress, 0.88, 0.82 - 0.2 * progress);
        coreHalo.scale.setScalar(1.0 - 0.45 * progress + 0.06 * Math.sin(t * 2.5));
        coreHalo.material.opacity = 0.10 + 0.18 * (0.5 + 0.5 * Math.sin(t * 2.5)) + progress * 0.12;

        // console indicator-lamp bank blinks in sequence
        for (let i = 0; i < lamps.length; i++) {
          const b = blink(t, i);
          const lit = b > 0.55;
          lamps[i].bulb.material.color.setHex(lit ? lamps[i].on : lamps[i].off);
          lamps[i].light.intensity = b * 0.8;
        }

        // scrolling genomic readout ticker marches sideways and loops
        scroll += dt * 9;
        for (let i = 0; i < ticks.length; i++) {
          let x = ticks[i].position.x - dt * 0.6;
          if (x < tickerX0) x += tickerSpan;            // wrap to the right edge
          ticks[i].position.x = x;
          // gentle breathing of the trace so a frozen frame still reads as data
          ticks[i].scale.y = 0.7 + 0.6 * (0.5 + 0.5 * Math.sin(t * 6 + i));
        }

        seqLamp.material.color.setHex(Math.sin(t * 6) > 0 ? TEAL : TEAL_DIM);
        screenLight.intensity = 0.7 + 0.3 * Math.sin(t * 5);
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
