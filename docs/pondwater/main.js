// Pond Water Analyzer — orchestration + the infinite-zoom engine.
//
// The experience has two registers:
//   • THE DROP — a field of living microorganisms drifting in the water, at
//     log-compressed relative sizes so bacteria and water fleas are both
//     findable in one view. Free-orbit; wheel-zoom the whole sample.
//   • THE DIVE — click (or pick from the roster) any organism to focus it. The
//     camera flies in to frame it, the rest of the field fades back, and now
//     zooming keeps going *into* the animal: as the magnification climbs, its
//     organs' callout labels fade in one tier at a time — gross body, then
//     organs, then the finest cellular detail — down to organ level.
//
// Magnification is honest to each specimen's real size. Framed, a Daphnia
// (~1.5 mm) reads a few hundred ×; a bacterium (~2 µm) reads many thousands ×,
// exactly as it would under an oil-immersion objective. The number is derived
// from the true field-of-view width in microns: mag = 1e6 / fieldMicrons.

import { createScope } from './scene.js';
import { ROSTER, BY_ID } from './organisms/index.js';
import * as THREE from 'three';

const container = document.getElementById('stage');
const scope = createScope(container);
const { scene, camera, controls, composer, renderer, medium } = scope;

// ── Magnification model ─────────────────────────────────────────────────────
const REF_MICRONS = 1_000_000;          // mag = REF / field-width-in-microns
const DROP_MICRON_PER_WORLD = 60;       // the drop's shared scale bar
const tanHalfFov = () => Math.tan((camera.fov * Math.PI) / 360);

function fieldMicrons(dist, micronPerWorld) {
  return 2 * dist * tanHalfFov() * micronPerWorld;
}
function magAt(dist, micronPerWorld) {
  return REF_MICRONS / Math.max(1e-4, fieldMicrons(dist, micronPerWorld));
}

// ── Sample state ────────────────────────────────────────────────────────────
const instances = [];      // { root, meta, anim, organs, vel, spin, baseScale }
let focus = null;          // the focused instance, or null in drop view
let sampleSeed = 1;
let running = true;
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
let lastPointerDown = null;

function clearSample() {
  for (const inst of instances) {
    scene.remove(inst.root);
    inst.root.traverse((o) => {
      if (o.geometry) o.geometry.dispose?.();
      if (o.material) (Array.isArray(o.material) ? o.material : [o.material]).forEach((m) => m.dispose?.());
    });
  }
  instances.length = 0;
  focus = null;
}

// Deterministic-ish spawn from a seed (Math.random is fine here — a sample is
// meant to feel fresh; the seed just varies the count/mix per "draw").
function loadSample(seed) {
  clearSample();
  sampleSeed = seed;
  const rnd = mulberry(seed);

  // one of each guarantees the full ladder of life is present, then a few
  // extra draws bias toward the abundant small stuff (as a real drop does).
  const draws = [...ROSTER.map((m) => m.id)];
  const abundant = ['bacterium', 'bacterium', 'paramecium', 'rotifer', 'nematode'];
  const extra = 4 + Math.floor(rnd() * 4);
  for (let i = 0; i < extra; i++) draws.push(abundant[Math.floor(rnd() * abundant.length)]);

  for (const id of draws) {
    const meta = BY_ID[id];
    const root = meta.build();
    // log-compressed relative size so every organism is findable in the drop
    const rel = 0.55 + 0.55 * Math.log10(meta.micronLength / 2.0);
    const baseScale = 0.16 * rel;
    root.scale.setScalar(baseScale);
    root.position.set((rnd() - 0.5) * 26, (rnd() - 0.5) * 18, (rnd() - 0.5) * 22);
    root.rotation.set(rnd() * 6.28, rnd() * 6.28, rnd() * 6.28);
    root.userData.instance = true;
    root.userData.meta = meta;
    scene.add(root);
    instances.push({
      root, meta,
      anim: root.userData.anim,
      organs: root.userData.organs || [],
      focusRadius: root.userData.focusRadius || 6,
      baseScale,
      vel: new THREE.Vector3((rnd() - 0.5) * 0.5, (rnd() - 0.5) * 0.3, (rnd() - 0.5) * 0.4),
      spin: new THREE.Vector3((rnd() - 0.5) * 0.2, (rnd() - 0.5) * 0.2, (rnd() - 0.5) * 0.2),
    });
  }
  surface(true);
  buildOrganLabels();
  hud.sampleId.textContent = `SPECIMEN ${String(seed).padStart(3, '0')}`;
  announce(`New sample drawn — ${instances.length} organisms in the field.`);
}

// ── Focus / dive ────────────────────────────────────────────────────────────
let camFly = null;   // { fromPos, toPos, fromTarget, toTarget, t, dur }

function focusInstance(inst) {
  focus = inst;
  const p = inst.root.getWorldPosition(new THREE.Vector3());
  const frameDist = inst.focusRadius * inst.baseScale * 6.2;
  const dir = camera.position.clone().sub(controls.target).normalize();
  camFly = {
    fromPos: camera.position.clone(),
    toPos: p.clone().add(dir.multiplyScalar(frameDist)),
    fromTarget: controls.target.clone(),
    toTarget: p.clone(),
    t: 0, dur: 0.9,
  };
  document.body.dataset.mode = 'dive';
  hud.specimenName.textContent = inst.meta.name;
  hud.specimenTaxon.textContent = inst.meta.taxon;
  hud.specimenKingdom.textContent = inst.meta.kingdom;
  hud.specimenBlurb.textContent = inst.meta.blurb;
  hud.organCount.textContent = `${inst.organs.length} structures`;
  buildOrganLabels();
  for (const b of hud.roster.children) b.classList.toggle('active', b.dataset.id === inst.meta.id);
  announce(`Focused ${inst.meta.name}. Zoom in to dive to organ level.`);
}

function surface(instant = false) {
  focus = null;
  document.body.dataset.mode = 'drop';
  for (const b of hud.roster.children) b.classList.remove('active');
  hud.specimenName.textContent = 'The drop';
  hud.specimenTaxon.textContent = `${instances.length} organisms`;
  hud.specimenKingdom.textContent = '—';
  hud.specimenBlurb.textContent = 'A field of pond-water life at log-compressed scale. Click any organism, or pick one from the ladder, to dive in.';
  hud.organCount.textContent = '';
  clearOrganLabels();
  if (instant) {
    camera.position.set(0, 0, 34);
    controls.target.set(0, 0, 0);
    camFly = null;
  } else {
    camFly = {
      fromPos: camera.position.clone(),
      toPos: new THREE.Vector3(0, 0, 34),
      fromTarget: controls.target.clone(),
      toTarget: new THREE.Vector3(0, 0, 0),
      t: 0, dur: 0.9,
    };
  }
}

// ── Organ callout labels (DOM overlay, projected each frame) ────────────────
let organLabels = [];
function clearOrganLabels() {
  for (const l of organLabels) { l.el.remove(); l.line.remove(); }
  organLabels = [];
}
function buildOrganLabels() {
  clearOrganLabels();
  if (!focus) return;
  const svg = document.getElementById('organLeaders');
  for (const organ of focus.organs) {
    const el = document.createElement('div');
    el.className = 'organ-callout';
    el.innerHTML = `<span class="txt"><b>${organ.name}</b><i>${organ.blurb}</i></span>`;
    hud.organLayer.appendChild(el);
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    svg.appendChild(line);
    organLabels.push({ el, line, organ, slotY: 0 });
  }
}

// ── HUD wiring ──────────────────────────────────────────────────────────────
const hud = {
  mag: document.getElementById('magReadout'),
  scale: document.getElementById('scaleReadout'),
  scaleBar: document.getElementById('scaleBar'),
  depthFill: document.getElementById('depthFill'),
  specimenName: document.getElementById('specimenName'),
  specimenTaxon: document.getElementById('specimenTaxon'),
  specimenKingdom: document.getElementById('specimenKingdom'),
  specimenBlurb: document.getElementById('specimenBlurb'),
  organCount: document.getElementById('organCount'),
  roster: document.getElementById('roster'),
  organLayer: document.getElementById('organLayer'),
  sampleId: document.getElementById('sampleId'),
  status: document.getElementById('srStatus'),
  btnSample: document.getElementById('btnSample'),
  btnSurface: document.getElementById('btnSurface'),
  btnPlay: document.getElementById('btnPlay'),
};

function announce(msg) { if (hud.status) hud.status.textContent = msg; }

// Build the roster "ladder of life" buttons.
for (const meta of ROSTER) {
  const b = document.createElement('button');
  b.className = 'roster-item';
  b.dataset.id = meta.id;
  b.innerHTML = `<span class="rk">${meta.kingdom}</span><span class="rn">${meta.name}</span><span class="rs">${fmtMicron(meta.micronLength)}</span>`;
  b.addEventListener('click', () => {
    // focus the nearest instance of this species, or spawn-focus the first
    const cands = instances.filter((i) => i.meta.id === meta.id);
    if (cands.length) focusInstance(cands[0]);
  });
  hud.roster.appendChild(b);
}

hud.btnSample.addEventListener('click', () => loadSample((sampleSeed % 999) + 1));
hud.btnSurface.addEventListener('click', () => surface());
hud.btnPlay.addEventListener('click', () => {
  running = !running;
  hud.btnPlay.textContent = running ? '❚❚ Pause life' : '▶ Resume life';
  hud.btnPlay.setAttribute('aria-pressed', String(!running));
});

// Click-to-focus picking.
renderer.domElement.addEventListener('pointerdown', (e) => {
  lastPointerDown = { x: e.clientX, y: e.clientY };
});
renderer.domElement.addEventListener('pointerup', (e) => {
  if (!lastPointerDown) return;
  const moved = Math.hypot(e.clientX - lastPointerDown.x, e.clientY - lastPointerDown.y);
  lastPointerDown = null;
  if (moved > 6) return;                       // it was a drag-orbit, not a pick
  const rect = renderer.domElement.getBoundingClientRect();
  pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const hits = raycaster.intersectObjects(instances.map((i) => i.root), true);
  if (hits.length) {
    let obj = hits[0].object;
    while (obj && !obj.userData.instance) obj = obj.parent;
    const inst = instances.find((i) => i.root === obj);
    if (inst) focusInstance(inst);
  }
});

// ── The loop ────────────────────────────────────────────────────────────────
const clock = new THREE.Clock();
const tmpV = new THREE.Vector3();

function tick() {
  const dt = Math.min(0.05, clock.getDelta());
  const t = clock.elapsedTime;

  // camera fly-to easing
  if (camFly) {
    camFly.t += dt / camFly.dur;
    const k = camFly.t >= 1 ? 1 : easeInOut(camFly.t);
    camera.position.lerpVectors(camFly.fromPos, camFly.toPos, k);
    controls.target.lerpVectors(camFly.fromTarget, camFly.toTarget, k);
    if (camFly.t >= 1) camFly = null;
  }

  // medium drift
  medium.userData.update(dt, t);
  scope.spot.position.x = Math.sin(t * 0.3) * 6;
  scope.spot.position.y = Math.cos(t * 0.24) * 5;

  // animate + drift every organism
  for (const inst of instances) {
    if (inst.anim) { inst.anim.setRunning(running); inst.anim.update(running ? dt : 0, t); }
    if (inst !== focus) {
      // gentle brownian drift + tumble in the drop; wrap in a soft box
      inst.root.position.addScaledVector(inst.vel, dt);
      inst.root.rotation.x += inst.spin.x * dt;
      inst.root.rotation.y += inst.spin.y * dt;
      const p = inst.root.position;
      for (const ax of ['x', 'y', 'z']) {
        const lim = ax === 'y' ? 11 : 15;
        if (p[ax] > lim) p[ax] = -lim; else if (p[ax] < -lim) p[ax] = lim;
      }
      // fade non-focused down when diving
      const fade = focus ? 0.12 : 1;
      setOpacity(inst.root, fade);
    } else {
      setOpacity(inst.root, 1);
    }
  }

  controls.update();
  updateReadouts();
  composer.render();
  requestAnimationFrame(tick);
}

function updateReadouts() {
  const dist = camera.position.distanceTo(controls.target);
  let mag, field, mpw;
  if (focus) {
    mpw = focus.meta.micronLength / (focus.focusRadius * focus.baseScale * 1.3);
    mag = magAt(dist, mpw);
    field = fieldMicrons(dist, mpw);
    // dive depth: entry (frame) → deepest
    const entryDist = focus.focusRadius * focus.baseScale * 6.2;
    const deepDist = controls.minDistance;
    const depth = clamp01((entryDist - dist) / (entryDist - deepDist));
    hud.depthFill.style.height = `${(depth * 100).toFixed(1)}%`;
    updateOrganLabels(dist, entryDist, deepDist);
  } else {
    mpw = DROP_MICRON_PER_WORLD;
    mag = magAt(dist, mpw);
    field = fieldMicrons(dist, mpw);
    hud.depthFill.style.height = '0%';
  }
  hud.mag.textContent = `×${fmtNum(Math.round(mag))}`;
  hud.scale.textContent = fmtMicron(field) + ' field';
  // scale bar: width of 100 µm on screen, as a fraction of a 220px track
  const px100 = clamp(220 * (100 / field), 2, 220);
  hud.scaleBar.style.width = `${px100}px`;
  hud.scaleBar.dataset.label = px100 < 30 ? '' : '100 µm';
}

// Fade each organ's callout in as the dive crosses its reveal threshold, dock
// it to the nearer gutter in a decluttered vertical slot, and draw a leader
// line from the label to the organ's true 3-D anchor — an anatomical plate.
const GUT_L = 328, LABEL_W = 236, SLOT_H = 74;   // left gutter clears the dossier
function updateOrganLabels(dist, entryDist, deepDist) {
  const span = Math.max(1e-3, entryDist - deepDist);
  const depth = clamp01((entryDist - dist) / span);
  const rect = renderer.domElement.getBoundingClientRect();
  const cx = rect.width / 2;

  // 1. gather visible organs with their projected anchors + reveal alpha
  const vis = [];
  for (const l of organLabels) {
    const a = clamp01((depth - l.organ.revealFrac) / 0.14);
    if (a <= 0.01) { l.el.style.opacity = '0'; l.line.style.opacity = '0'; continue; }
    l.organ.object.getWorldPosition(tmpV);
    tmpV.project(camera);
    if (tmpV.z > 1) { l.el.style.opacity = '0'; l.line.style.opacity = '0'; continue; }
    const ax = (tmpV.x * 0.5 + 0.5) * rect.width;
    const ay = (-tmpV.y * 0.5 + 0.5) * rect.height;
    vis.push({ l, a, ax, ay, side: ax < cx ? 'L' : 'R' });
    l.el.style.opacity = '0'; l.line.style.opacity = '0';   // reset; set below
  }

  // 2. per gutter, order by anchor height and push into non-overlapping slots
  const topLim = 96, botLim = rect.height - 60;
  for (const side of ['L', 'R']) {
    const col = vis.filter((v) => v.side === side).sort((a, b) => a.ay - b.ay).slice(0, 6);
    let y = topLim;
    for (const v of col) {
      v.slotY = Math.max(y, Math.min(v.ay, botLim));
      y = v.slotY + SLOT_H;
    }
    // if we overran the bottom, lift the whole stack up
    const over = y - SLOT_H - botLim;
    if (over > 0) for (const v of col) v.slotY = Math.max(topLim, v.slotY - over);

    for (const v of col) {
      const { l } = v;
      const labelX = side === 'L' ? GUT_L : rect.width - GUT_L - LABEL_W;
      l.el.className = `organ-callout side-${side === 'L' ? 'left' : 'right'}`;
      l.el.style.transform = `translate(${labelX}px, ${v.slotY}px)`;
      l.el.style.opacity = v.a.toFixed(2);
      l.el.style.pointerEvents = v.a > 0.6 ? 'auto' : 'none';
      // leader: from the inner edge of the label box to the organ anchor
      const edgeX = side === 'L' ? labelX + LABEL_W : labelX;
      l.line.setAttribute('x1', edgeX); l.line.setAttribute('y1', v.slotY + 12);
      l.line.setAttribute('x2', v.ax); l.line.setAttribute('y2', v.ay);
      l.line.style.opacity = (v.a * 0.7).toFixed(2);
    }
  }
}

function setOpacity(root, target) {
  root.traverse((o) => {
    if (!o.material) return;
    const mats = Array.isArray(o.material) ? o.material : [o.material];
    for (const m of mats) {
      if (m.userData._baseOpacity === undefined) {
        m.userData._baseOpacity = m.opacity !== undefined && m.transparent ? m.opacity : 1;
      }
      const want = m.userData._baseOpacity * target;
      if (target < 0.999) { m.transparent = true; m.opacity += (want - m.opacity) * 0.2; }
      else if (m.userData._baseOpacity >= 1) { m.transparent = m.userData._wasTransparent ?? m.transparent; m.opacity = m.userData._baseOpacity; }
      else { m.opacity += (want - m.opacity) * 0.2; }
    }
  });
}

// ── Helpers ─────────────────────────────────────────────────────────────────
function easeInOut(t) { return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2; }
function clamp01(v) { return Math.min(1, Math.max(0, v)); }
function clamp(v, lo, hi) { return Math.min(hi, Math.max(lo, v)); }
function fmtNum(n) { return n.toLocaleString('en-US'); }
function fmtMicron(um) {
  if (um >= 1000) return `${(um / 1000).toFixed(um >= 10000 ? 0 : 2)} mm`;
  if (um >= 1) return `${um < 10 ? um.toFixed(1) : Math.round(um)} µm`;
  return `${(um * 1000).toFixed(0)} nm`;
}
function mulberry(seed) {
  let a = seed >>> 0;
  return function () {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let x = Math.imul(a ^ (a >>> 15), 1 | a);
    x = (x + Math.imul(x ^ (x >>> 7), 61 | x)) ^ x;
    return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
  };
}

// ── Boot ────────────────────────────────────────────────────────────────────
scope.setSize();
loadSample(1);
tick();

// expose a tiny handle for the smoke/runtime harness + manual poking
window.PONDWATER = { scope, instances, focusInstance, surface, loadSample, ROSTER };
