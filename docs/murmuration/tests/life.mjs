// Murmuration — RENDER + integration gate. Run with three installed:
//   npm install three@0.162.0 --no-save && node tests/life.mjs
//
// smoke.mjs gates the page statically and flock.mjs gates the physics. This
// builds the render layer against the REAL three.js (geometry/material/mesh
// need no WebGL) and proves it is wired to the simulation:
//   - the flock is ONE InstancedMesh of the right size, with the wingbeat
//     attributes (aWing per-vertex, aPhase per-instance) and a shader hook,
//   - orient() turns a heading+bank into a rigid, non-degenerate matrix whose
//     forward axis actually points where the bird is flying, and whose roll
//     tilts the wings,
//   - the peregrine is an assembled object with named parts and a wingbeat,
//   - driving the InstancedMesh from a live Flock for 60 frames keeps every
//     instance matrix finite and the birds VISIBLY MOVE.
//
// Skips cleanly (exit 0) if three isn't installed, like the lab's runtime gate.

import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, '..');

let THREE;
try { THREE = await import('three'); }
catch { console.log('• three not installed — skipping render verification (install three@0.162.0 to enable)'); process.exit(0); }

const { makeFlock, makePredator, orient, makeScratch } =
  await import(pathToFileURL(path.join(ROOT, 'bird.js')).href);
const { Flock } = await import(pathToFileURL(path.join(ROOT, 'flock.js')).href);

let fails = 0, checks = 0;
const ok = () => { checks++; };
const fail = (m) => { fails++; console.error(`  ✗ ${m}`); };
const assert = (c, m) => (c ? ok() : fail(m));

console.log('Running Murmuration render verification…\n');

// 1. the flock is one InstancedMesh with the wingbeat rig
{
  const N = 500;
  const mesh = makeFlock(THREE, N);
  assert(mesh.isInstancedMesh, 'makeFlock did not return an InstancedMesh');
  assert(mesh.count === N, `InstancedMesh count ${mesh.count} ≠ ${N}`);
  assert(!!mesh.geometry.getAttribute('aWing'), 'geometry missing per-vertex aWing (wing mask)');
  const ph = mesh.geometry.getAttribute('aPhase');
  assert(ph && ph.isInstancedBufferAttribute && ph.count === N, 'missing per-instance aPhase attribute');
  assert(typeof mesh.material.onBeforeCompile === 'function', 'material has no shader wingbeat hook');
  const u = mesh.userData.uniforms;
  assert(u && u.uTime, 'no uTime uniform for the wingbeat clock');
  mesh.userData.tick(3.14);
  assert(u.uTime.value === 3.14, 'tick() did not advance the wingbeat clock');
}

// 2. orient(): heading+bank → a rigid matrix that faces the flight direction
{
  const s = makeScratch(THREE);
  const m = new THREE.Matrix4();
  // fly along +x, no bank
  orient(THREE, m, s, 10, 20, 0, 1, 0, 0, 0, 1);
  const pos = new THREE.Vector3(), quat = new THREE.Quaternion(), scl = new THREE.Vector3();
  m.decompose(pos, quat, scl);
  assert(pos.distanceTo(new THREE.Vector3(10, 20, 0)) < 1e-4, 'orient() lost the position');
  assert(Math.abs(scl.x - 1) < 1e-3 && Math.abs(scl.y - 1) < 1e-3 && Math.abs(scl.z - 1) < 1e-3, 'orient() introduced scale/shear');
  const fwd = new THREE.Vector3(0, 0, 1).applyQuaternion(quat); // local +Z is forward
  assert(fwd.dot(new THREE.Vector3(1, 0, 0)) > 0.99, `bird does not face its heading (fwd·v=${fwd.dot(new THREE.Vector3(1, 0, 0)).toFixed(3)})`);
  const detFinite = Number.isFinite(m.determinant()) && Math.abs(m.determinant()) > 0.5;
  assert(detFinite, 'orient() produced a degenerate matrix');

  // a banked bird rolls: its up-vector tilts off world-up
  const m2 = new THREE.Matrix4();
  orient(THREE, m2, s, 0, 0, 0, 1, 0, 0, 0.6, 1);
  const q2 = new THREE.Quaternion(); m2.decompose(new THREE.Vector3(), q2, new THREE.Vector3());
  const up = new THREE.Vector3(0, 1, 0).applyQuaternion(q2);
  assert(up.dot(new THREE.Vector3(0, 1, 0)) < 0.98, 'bank did not roll the bird (wings stayed level)');
}

// 3. the peregrine is an assembled, animated object
{
  const p = makePredator(THREE);
  assert(p.isObject3D, 'makePredator did not return an Object3D');
  let named = 0;
  p.traverse((o) => { if (o.isMesh && o.name) named++; });
  assert(named >= 2, `peregrine has only ${named} named parts (expected body + wings)`);
  const before = p.getObjectByName('raptor-wings').rotation.z;
  p.userData.tick(0.5);
  assert(p.getObjectByName('raptor-wings').rotation.z !== before, 'peregrine wings do not beat');
}

// 4. drive the InstancedMesh from a live flock — finite + moving
{
  const N = 300;
  const flock = new Flock({ birds: N }, 42);
  const mesh = makeFlock(THREE, N);
  const s = makeScratch(THREE);
  const m = new THREE.Matrix4();
  const writeAll = () => {
    for (let i = 0; i < N; i++) {
      orient(THREE, m, s, flock.px[i], flock.py[i], flock.pz[i], flock.vx[i], flock.vy[i], flock.vz[i], flock.bank[i], 1);
      mesh.setMatrixAt(i, m);
    }
  };
  // warm the flock so it's flowing, then sample a few birds
  for (let i = 0; i < 120; i++) flock.step(0.02);
  writeAll();
  const probes = [0, 50, 120, 200, 299];
  const p0 = probes.map((i) => { const v = new THREE.Vector3(); mesh.getMatrixAt(i, m); v.setFromMatrixPosition(m); return v.clone(); });
  for (let i = 0; i < 60; i++) flock.step(0.02);
  writeAll();
  let moved = 0, bad = 0;
  probes.forEach((idx, k) => {
    mesh.getMatrixAt(idx, m);
    const v = new THREE.Vector3().setFromMatrixPosition(m);
    if (![v.x, v.y, v.z].every(Number.isFinite)) bad++;
    moved += v.distanceTo(p0[k]);
  });
  assert(bad === 0, 'an instance matrix went non-finite while flying');
  assert(moved > 1, `birds did not move over 60 frames (total displacement ${moved.toFixed(2)})`);
  console.log(`    · ${N} birds flown 60 frames, displacement ${moved.toFixed(1)}`);
}

console.log(`\n${checks} checks passed, ${fails} failure(s).`);
process.exit(fails ? 1 : 0);
