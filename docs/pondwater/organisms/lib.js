// Pond Water Analyzer — shared anatomy toolkit.
//
// Every organism in this client is *procedural*: no meshes are loaded, the
// whole creature is grown from primitives so it can be inspected at any
// magnification and its internal organs revealed as you dive in. This module
// is the common grammar those builders speak — translucent cuticle, wet organ
// materials, ciliary bands, spline bodies, and the organ-callout registry the
// zoom engine reads to fade labels in at the right scale.
//
// Contract every organism exports:
//   export const meta = { id, name, taxon, micronLength, kingdom, build }
//   meta.build() -> THREE.Group whose userData is:
//     { anim: { setRunning, getProgress, update(dt,t), reset },
//       organs: [{ object, name, blurb, revealFrac }],  // revealFrac in [0,1]
//       focusRadius }                                    // frames the whole body
//
// `revealFrac` is "how deep into the dive this organ appears" — 0 shows at the
// organism scale, 1 only at the deepest organ-level zoom. The engine maps the
// live magnification onto that fraction so structure fades in true to life:
// the gross body first, then organs, then the finest cellular detail.

import * as THREE from 'three';

export { THREE };

// ── Deterministic noise so a "sample" re-seeds identically ──────────────────
// mulberry32 — same generator the ontogeny engine uses, for reproducible draws.
export function rng(seed) {
  let a = seed >>> 0;
  return function () {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ── Materials ───────────────────────────────────────────────────────────────

// Translucent cuticle / body wall. Depth-write is off and it renders last so
// the internal organs stay visible through it — the "you can see inside" look
// of a live wet-mount. Physical material gives a faint wet sheen + IOR.
export function cuticle(color = 0xdfeee6, opacity = 0.22, extra = {}) {
  const m = new THREE.MeshPhysicalMaterial({
    color,
    transparent: true,
    opacity,
    roughness: 0.32,
    metalness: 0,
    transmission: 0.35,
    ior: 1.34,               // ~water/protoplasm
    thickness: 0.4,
    depthWrite: false,
    side: THREE.DoubleSide,
    ...extra,
  });
  return m;
}

// A wet internal organ — muscle, gut, gonad. Slightly emissive so it reads
// through the cuticle under the dim dark-field light without being flat.
export function organ(color = 0xb9614d, extra = {}) {
  return new THREE.MeshStandardMaterial({
    color,
    roughness: 0.55,
    metalness: 0.02,
    emissive: new THREE.Color(color).multiplyScalar(0.12),
    ...extra,
  });
}

// Nucleus / dense granular body — faintly self-lit so it pops as the core.
export function nucleus(color = 0x8fb8ff, extra = {}) {
  return new THREE.MeshStandardMaterial({
    color,
    roughness: 0.4,
    emissive: new THREE.Color(color).multiplyScalar(0.35),
    ...extra,
  });
}

// ── Spline body ─────────────────────────────────────────────────────────────
// A tapered tube along a centreline — the skeleton of worms, guts, foot stalks.
// radiusFn(t) in [0,1] lets a body swell and taper true to its anatomy.
export function tubeBody(points, radiusFn, material, { tubular = 96, radial = 20 } = {}) {
  const curve = new THREE.CatmullRomCurve3(points);
  const geo = new THREE.TubeGeometry(curve, tubular, 1, radial, false);
  // TubeGeometry has a constant radius; re-profile it per-ring by scaling each
  // cross-section vertex toward its centre on the curve.
  const pos = geo.attributes.position;
  const rings = tubular + 1;
  for (let i = 0; i <= tubular; i++) {
    const t = i / tubular;
    const c = curve.getPointAt(t);
    const r = Math.max(0.0001, radiusFn(t));
    for (let j = 0; j <= radial; j++) {
      const idx = i * (radial + 1) + j;
      const vx = pos.getX(idx), vy = pos.getY(idx), vz = pos.getZ(idx);
      pos.setXYZ(idx, c.x + (vx - c.x) * r, c.y + (vy - c.y) * r, c.z + (vz - c.z) * r);
    }
  }
  void rings;
  geo.computeVertexNormals();
  const mesh = new THREE.Mesh(geo, material);
  mesh.userData.curve = curve;
  return mesh;
}

// ── Ciliary band ────────────────────────────────────────────────────────────
// A ring of fine beating cilia — the corona of a rotifer, the coat of a
// ciliate. Returned as an InstancedMesh plus an update(t) that runs the
// metachronal wave (the shimmering "conveyor" beat real cilia show).
export function ciliaRing(radius, count, len, material, { axis = 'y', spread = 0.0 } = {}) {
  const geo = new THREE.CapsuleGeometry(len * 0.06, len, 3, 6);
  geo.translate(0, len * 0.5, 0);          // pivot at the base
  const mesh = new THREE.InstancedMesh(geo, material, count);
  const base = [];
  const dummy = new THREE.Object3D();
  for (let i = 0; i < count; i++) {
    const a = (i / count) * Math.PI * 2;
    const x = Math.cos(a) * radius;
    const z = Math.sin(a) * radius;
    const y = (Math.random() - 0.5) * spread;
    base.push({ a, x, y, z });
    dummy.position.set(x, y, z);
    dummy.updateMatrix();
    mesh.setMatrixAt(i, dummy.matrix);
  }
  mesh.userData.beat = (t, amp = 0.5) => {
    const dummy2 = new THREE.Object3D();
    for (let i = 0; i < count; i++) {
      const b = base[i];
      // metachronal wave: phase runs around the ring
      const phase = t * 6 - b.a * 3;
      const bend = Math.sin(phase) * amp;
      dummy2.position.set(b.x, b.y, b.z);
      if (axis === 'y') dummy2.rotation.set(Math.PI * 0.5 + bend * 0.5, b.a, bend);
      else dummy2.rotation.set(bend, b.a, Math.PI * 0.5 + bend * 0.5);
      dummy2.updateMatrix();
      mesh.setMatrixAt(i, dummy2.matrix);
    }
    mesh.instanceMatrix.needsUpdate = true;
  };
  return mesh;
}

// A patch of cilia over a surface region (paramecium coat) — instanced short
// hairs placed on an ellipsoid, beating in a travelling wave.
export function ciliaCoat(rx, ry, rz, count, len, material) {
  const geo = new THREE.ConeGeometry(len * 0.16, len, 5);
  geo.translate(0, len * 0.5, 0);
  const mesh = new THREE.InstancedMesh(geo, material, count);
  const base = [];
  const dummy = new THREE.Object3D();
  const r = rng(1337);
  for (let i = 0; i < count; i++) {
    const u = r() * Math.PI * 2;
    const v = Math.acos(2 * r() - 1);
    const nx = Math.sin(v) * Math.cos(u);
    const ny = Math.cos(v);
    const nz = Math.sin(v) * Math.sin(u);
    const p = new THREE.Vector3(nx * rx, ny * ry, nz * rz);
    const n = new THREE.Vector3(nx / rx, ny / ry, nz / rz).normalize();
    base.push({ p, n, phase: u + v });
    dummy.position.copy(p);
    dummy.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), n);
    dummy.updateMatrix();
    mesh.setMatrixAt(i, dummy.matrix);
  }
  const up = new THREE.Vector3(0, 1, 0);
  mesh.userData.beat = (t) => {
    const d = new THREE.Object3D();
    const q = new THREE.Quaternion();
    for (let i = 0; i < count; i++) {
      const b = base[i];
      const bend = Math.sin(t * 7 - b.phase * 4) * 0.4;
      d.position.copy(b.p);
      q.setFromUnitVectors(up, b.n);
      d.quaternion.copy(q);
      d.rotateX(bend);
      d.updateMatrix();
      mesh.setMatrixAt(i, d.matrix);
    }
    mesh.instanceMatrix.needsUpdate = true;
  };
  return mesh;
}

// ── Organ registry ──────────────────────────────────────────────────────────
// Organisms call registerOrgan() as they add internal parts; the engine reads
// group.userData.organs to fade callout labels in at the right dive depth.
export function registerOrgan(group, object, name, blurb, revealFrac = 0.4) {
  if (!group.userData.organs) group.userData.organs = [];
  object.userData.organName = name;
  group.userData.organs.push({ object, name, blurb, revealFrac });
  return object;
}

// Small helper: soft ellipsoid mesh (used everywhere for vacuoles, nuclei, eggs)
export function blob(rx, ry, rz, material, seg = 24) {
  const geo = new THREE.SphereGeometry(1, seg, seg);
  geo.scale(rx, ry, rz);
  return new THREE.Mesh(geo, material);
}

// Clamp/tuning shared by the animation loops.
export const TAU = Math.PI * 2;
export const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
export const lerp = (a, b, t) => a + (b - a) * t;
export const smooth = (t) => t * t * (3 - 2 * t);
