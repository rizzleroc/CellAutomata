// web4 controller — wires the lab scene, the stage registry, and the UI.
//
// P1 ships the lab shell + the Stage 0 Miller–Urey hero (hand-built photoreal
// glassware). Every other stage shows a placeholder until its GLB is baked via
// the touch-app / Tripo backend (see docs/PRD_LAB_EXPERIMENTS.md).

import * as THREE from 'three';
import { createLab } from './scene.js';
import { buildPlaceholder } from './apparatus/placeholder.js';
import { meta as millerUrey } from './apparatus/miller_urey.js';
import { meta as grayscott } from './apparatus/grayscott_dish.js';
import { meta as raf } from './apparatus/raf_flask.js';
import { meta as vesicles } from './apparatus/vesicle_microscope.js';
import { meta as vent } from './apparatus/vent_reactor.js';
import { meta as minerals } from './apparatus/mineral_flask.js';
import { meta as chirality } from './apparatus/chirality_polarimeter.js';
import { meta as rna } from './apparatus/rna_thermocycler.js';
import { meta as code } from './apparatus/code_bench.js';
import { meta as coacervate } from './apparatus/coacervate_microscope.js';
import { meta as selection } from './apparatus/microfluidic_chip.js';
import { meta as luca } from './apparatus/luca_console.js';
import { meta as stromatolite } from './apparatus/stromatolite.js';

// ── Stage registry (order = Stage 0 → the 12-stage pipeline → capstone) ─────
const STAGES = [
  millerUrey, grayscott, raf, vesicles, vent, minerals, chirality,
  rna, code, coacervate, selection, luca, stromatolite,
];
// buildPlaceholder remains the fallback for any meta missing a build() (e.g.
// a future stage stubbed before its apparatus exists).

const lab = createLab(document.getElementById('viewport'));
let current = null;
let currentMeta = null;

function loadStage(m) {
  if (current) { lab.scene.remove(current); disposeTree(current); }
  current = m.build ? m.build() : buildPlaceholder(m);
  currentMeta = m;
  lab.scene.add(current);
  frameTo(current);
  buildPartsPanel(current);
  // header / blurb
  document.getElementById('apTitle').textContent = m.title;
  document.getElementById('apLabel').textContent = m.label;
  document.getElementById('apBlurb').textContent = m.blurb;
  const isSpecimen = m.id?.startsWith('capstone');
  document.getElementById('runBtn').style.display = (m.placeholder || isSpecimen) ? 'none' : '';
  document.getElementById('explodeRow').style.display = m.placeholder ? 'none' : '';
  setRunning(true);
  // active nav button
  document.querySelectorAll('.stage-btn').forEach(b => b.classList.toggle('active', b.dataset.id === m.id));
}

// ── Camera framing ──────────────────────────────────────────────────────────
function frameTo(obj) {
  const box = new THREE.Box3().setFromObject(obj);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const maxDim = Math.max(size.x, size.y, size.z);
  const dist = maxDim / (2 * Math.tan(THREE.MathUtils.degToRad(lab.camera.fov) / 2)) * 1.35;
  lab.controls.target.copy(center);
  lab.camera.position.set(center.x + dist * 0.7, center.y + dist * 0.35, center.z + dist);
  lab.controls.update();
}

// ── Parts panel (named GLB parts, à la an exploded lab diagram) ─────────────
function buildPartsPanel(obj) {
  const list = document.getElementById('partsList');
  list.innerHTML = '';
  const named = [];
  obj.traverse(o => { if (o.isMesh && o.name && !o.name.startsWith('placeholder')) named.push(o); });
  if (!named.length) { list.innerHTML = '<div class="muted">No named parts</div>'; return; }
  document.getElementById('partCount').textContent = `${named.length} parts`;
  for (const m of named) {
    const row = document.createElement('button');
    row.className = 'part-row';
    row.textContent = m.name;
    row.onmouseenter = () => highlight(m, true);
    row.onmouseleave = () => highlight(m, false);
    row.onclick = () => { m.visible = !m.visible; row.classList.toggle('hidden', !m.visible); };
    list.appendChild(row);
  }
}
let emissiveCache = null;
function highlight(mesh, on) {
  if (!mesh.material || !mesh.material.emissive) return;
  if (on) { emissiveCache = mesh.material.emissive.getHex(); mesh.material.emissive.setHex(0x2a6cff); }
  else if (emissiveCache !== null) { mesh.material.emissive.setHex(emissiveCache); emissiveCache = null; }
}

// ── Run + explode controls ──────────────────────────────────────────────────
function setRunning(on) {
  current?.userData?.anim?.setRunning(on);
  const btn = document.getElementById('runBtn');
  btn.textContent = on ? '■ Stop experiment' : '▶ Run experiment';
  btn.classList.toggle('running', on);
}
document.getElementById('runBtn').onclick = () => {
  const running = !document.getElementById('runBtn').classList.contains('running');
  setRunning(running);
};
const explodePartsCache = new WeakMap();
document.getElementById('explode').oninput = (e) => {
  const f = parseFloat(e.target.value);
  const center = new THREE.Box3().setFromObject(current).getCenter(new THREE.Vector3());
  current.traverse(o => {
    if (!o.isMesh) return;
    if (!explodePartsCache.has(o)) explodePartsCache.set(o, o.position.clone());
    const home = explodePartsCache.get(o);
    const dir = o.getWorldPosition(new THREE.Vector3()).sub(center).normalize();
    o.position.copy(home).add(dir.multiplyScalar(f * 1.5));
  });
};

// ── Build the stage nav ─────────────────────────────────────────────────────
const nav = document.getElementById('stageNav');
for (const m of STAGES) {
  const b = document.createElement('button');
  b.className = 'stage-btn' + (m.placeholder ? ' pending' : '');
  b.dataset.id = m.id;
  b.innerHTML = `<span>${m.label}</span><small>${m.title}</small>`;
  b.onclick = () => loadStage(m);
  nav.appendChild(b);
}

// Per-stage readout label (defaults to "experiment progress").
const READOUT_LABEL = {
  'stage0-miller-urey': 'organics collected',
  'stage4-vent': 'reaction extent',
  'stage7-rna': 'replication cycles',
  'stage10-selection': 'mean fitness',
  'stage11-luca': 'core distilled',
};

// ── Render loop ─────────────────────────────────────────────────────────────
const clock = new THREE.Clock();
function tick() {
  const dt = Math.min(clock.getDelta(), 0.05);
  current?.userData?.anim?.update(dt, clock.elapsedTime);
  lab.controls.update();
  lab.composer.render();
  // live readout
  const p = current?.userData?.anim?.getProgress?.() ?? 0;
  const ro = document.getElementById('readout');
  const isSpecimen = currentMeta?.id?.startsWith('capstone');
  if (ro && !currentMeta?.placeholder && !isSpecimen) {
    const label = READOUT_LABEL[currentMeta?.id] || 'experiment progress';
    ro.textContent = `${label}: ${(p * 100).toFixed(0)}%`;
  } else if (ro) { ro.textContent = ''; }
  requestAnimationFrame(tick);
}

function disposeTree(obj) {
  obj.traverse(o => {
    if (o.geometry) o.geometry.dispose();
    if (o.material) (Array.isArray(o.material) ? o.material : [o.material]).forEach(mt => mt.dispose());
  });
}

loadStage(STAGES[0]);
tick();
