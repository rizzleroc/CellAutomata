// Pond Water Analyzer — shared anatomy toolkit.
//
// Every organism in this client is *procedural*: no meshes are loaded, the
// whole creature is grown from primitives so it can be inspected at any
// magnification and its internal organs revealed as you dive in. This module
// is the common grammar those builders speak — translucent cuticle, wet organ
// materials, ciliary bands, spline bodies, and the organ-callout registry the
// zoom engine reads to fade labels in at the right scale.
//
// Fidelity is bought procedurally (the runtime is zero-dependency — three via
// an importmap, must run from file://): MeshPhysicalMaterial transmission +
// thickness + attenuation for real volumetric absorption, clearcoat for a wet
// sheen, sheen for a soft cuticle, a Fresnel rim injected through
// onBeforeCompile so glassy edges catch the dark-field condenser, and small
// procedurally-generated normal maps (DataTexture, built once and shared) for
// micro-surface detail — pellicle ridges, cuticle grain, granular cytoplasm.
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

// ── Procedural surface detail ───────────────────────────────────────────────
// Value-noise fbm → a tangent-space normal map, generated as a DataTexture at
// build time (no canvas, so it is identical under the headless test harness).
// Cached by key: all six organisms share a handful of textures, not dozens.
const _normalCache = new Map();

function _hash(ix, iy, seed) {
  let h = (ix * 374761393 + iy * 668265263 + seed * 2246822519) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}
function _valueNoise(x, y, seed) {
  const ix = Math.floor(x), iy = Math.floor(y);
  const fx = x - ix, fy = y - iy;
  const ux = fx * fx * (3 - 2 * fx), uy = fy * fy * (3 - 2 * fy);
  const a = _hash(ix, iy, seed), b = _hash(ix + 1, iy, seed);
  const c = _hash(ix, iy + 1, seed), d = _hash(ix + 1, iy + 1, seed);
  return (a * (1 - ux) + b * ux) * (1 - uy) + (c * (1 - ux) + d * ux) * uy;
}

// height(u,v) shapers by surface "kind" — ridged pellicle rows, grainy
// cytoplasm, segmented cuticle, or plain fbm bumpiness.
function _height(u, v, kind, freq, seed) {
  let n = 0, amp = 1, f = freq, norm = 0;
  for (let o = 0; o < 4; o++) { n += _valueNoise(u * f, v * f, seed + o * 17) * amp; norm += amp; amp *= 0.5; f *= 2; }
  n /= norm;
  if (kind === 'ridges') {
    // longitudinal ciliary rows + a little grain riding on them
    return 0.5 + 0.5 * Math.sin(v * freq * Math.PI * 2) * 0.8 + (n - 0.5) * 0.35;
  }
  if (kind === 'segments') {
    return 0.5 + 0.5 * Math.sin(u * freq * Math.PI) * 0.7 + (n - 0.5) * 0.4;
  }
  if (kind === 'granular') {
    const g = _valueNoise(u * freq * 3, v * freq * 3, seed + 99);
    return n * 0.5 + g * 0.5;
  }
  return n;
}

export function surfaceNormalMap({ size = 128, freq = 6, strength = 1, kind = 'fbm', seed = 1 } = {}) {
  const key = `${size}:${freq}:${strength}:${kind}:${seed}`;
  if (_normalCache.has(key)) return _normalCache.get(key);
  const data = new Uint8Array(size * size * 4);
  const at = (x, y) => _height((x + size) % size / size, (y + size) % size / size, kind, freq, seed);
  const s = strength;
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const hL = at(x - 1, y), hR = at(x + 1, y);
      const hD = at(x, y - 1), hU = at(x, y + 1);
      const nx = (hL - hR) * s, ny = (hD - hU) * s, nz = 1;
      const inv = 1 / Math.hypot(nx, ny, nz);
      const i = (y * size + x) * 4;
      data[i] = (nx * inv * 0.5 + 0.5) * 255;
      data[i + 1] = (ny * inv * 0.5 + 0.5) * 255;
      data[i + 2] = (nz * inv * 0.5 + 0.5) * 255;
      data[i + 3] = 255;
    }
  }
  const tex = new THREE.DataTexture(data, size, size, THREE.RGBAFormat);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.needsUpdate = true;
  _normalCache.set(key, tex);
  return tex;
}

// ── Fresnel rim ─────────────────────────────────────────────────────────────
// Dark-field organisms glow at their edges where the condenser rakes across
// them. We add a Fresnel term to outgoingLight through onBeforeCompile — no
// extra geometry, no extra draw call. Chains cleanly onto any existing
// onBeforeCompile (e.g. a material that already carries one). Runs only at
// shader-compile time in the browser, so it never touches the headless tests.
export function addRim(mat, { color = 0x9fd0ff, power = 2.6, intensity = 0.65 } = {}) {
  const c = new THREE.Color(color);
  const prev = mat.onBeforeCompile;
  mat.onBeforeCompile = (shader, renderer) => {
    if (prev) prev(shader, renderer);
    shader.uniforms.uRimColor = { value: c };
    shader.uniforms.uRimPow = { value: power };
    shader.uniforms.uRimInt = { value: intensity };
    shader.fragmentShader =
      'uniform vec3 uRimColor;\nuniform float uRimPow;\nuniform float uRimInt;\n' +
      shader.fragmentShader.replace(
        '#include <opaque_fragment>',
        'float _rim = pow(1.0 - clamp(dot(normalize(normal), normalize(vViewPosition)), 0.0, 1.0), uRimPow);\n' +
        '\toutgoingLight += uRimColor * _rim * uRimInt;\n\t#include <opaque_fragment>',
      );
  };
  const tag = `rim${power.toFixed(2)}_${intensity.toFixed(2)}_${c.getHexString()}`;
  const prevKey = mat.customProgramCacheKey?.bind(mat);
  mat.customProgramCacheKey = () => (prevKey ? prevKey() + tag : tag);
  mat.needsUpdate = true;
  return mat;
}

// ── Materials ───────────────────────────────────────────────────────────────

// Translucent cuticle / body wall. Depth-write is off and it renders last so
// the internal organs stay visible through it — the "you can see inside" look
// of a live wet-mount. Physical material: real transmission with volumetric
// attenuation for a wet, thick body; clearcoat for the glassy sheen; sheen for
// the soft protein cuticle; and a Fresnel rim so the edge lights up in the
// dark field. `extra` overrides anything (iridescence, normalMap, rim: false…).
export function cuticle(color = 0xdfeee6, opacity = 0.22, extra = {}) {
  const { rim, normal, ...matExtra } = extra;
  const attenuation = new THREE.Color(color).lerp(new THREE.Color(0x224437), 0.5);
  const m = new THREE.MeshPhysicalMaterial({
    color,
    transparent: true,
    opacity,
    roughness: 0.26,
    metalness: 0,
    transmission: 0.6,
    ior: 1.34,                 // ~water/protoplasm
    thickness: 0.9,
    attenuationColor: attenuation,
    attenuationDistance: 3.2,
    clearcoat: 0.7,
    clearcoatRoughness: 0.28,
    sheen: 0.5,
    sheenRoughness: 0.7,
    sheenColor: new THREE.Color(color).multiplyScalar(1.1),
    specularIntensity: 0.7,
    envMapIntensity: 1.15,
    depthWrite: false,
    side: THREE.DoubleSide,
    ...matExtra,
  });
  if (normal !== false) {
    m.normalMap = normal || surfaceNormalMap({ freq: 7, strength: 0.6, kind: 'fbm', seed: 3 });
    m.normalScale = new THREE.Vector2(0.35, 0.35);
  }
  if (rim !== false) addRim(m, typeof rim === 'object' ? rim : {});
  return m;
}

// A wet internal organ — muscle, gut, gonad. Physical, faintly translucent and
// emissive so it reads through the cuticle under the dim dark-field light and
// looks fleshy, not plastic: low specular, a warm sheen, a hint of clearcoat
// for the wet film, and optional transmission (set via `extra`) for the big
// translucent guts you can see food through.
export function organ(color = 0xb9614d, extra = {}) {
  const { rim, ...matExtra } = extra;
  const base = new THREE.Color(color);
  const m = new THREE.MeshPhysicalMaterial({
    color,
    roughness: 0.5,
    metalness: 0,
    emissive: base.clone().multiplyScalar(0.14),
    sheen: 0.35,
    sheenRoughness: 0.8,
    sheenColor: base.clone().lerp(new THREE.Color(0xffd9c0), 0.4),
    clearcoat: 0.3,
    clearcoatRoughness: 0.5,
    specularIntensity: 0.35,
    ior: 1.38,
    attenuationColor: base.clone().multiplyScalar(0.7),
    attenuationDistance: 1.2,
    envMapIntensity: 0.8,
    ...matExtra,
  });
  if (rim) addRim(m, typeof rim === 'object' ? rim : { intensity: 0.4, power: 3 });
  return m;
}

// Nucleus / dense granular body — faintly self-lit so it pops as the core, with
// a wet clearcoat film over it.
export function nucleus(color = 0x8fb8ff, extra = {}) {
  const base = new THREE.Color(color);
  return new THREE.MeshPhysicalMaterial({
    color,
    roughness: 0.38,
    metalness: 0,
    emissive: base.clone().multiplyScalar(0.35),
    clearcoat: 0.4,
    clearcoatRoughness: 0.4,
    specularIntensity: 0.5,
    envMapIntensity: 0.9,
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
  geo.computeVertexNormals();
  const mesh = new THREE.Mesh(geo, material);
  mesh.userData.curve = curve;
  return mesh;
}

// ── Cilia / flagella ─────────────────────────────────────────────────────────
// A single fine cilium: a gently pre-curved, tapered tube built once and shared
// across every instance of an InstancedMesh, so hundreds of hairs cost one
// draw. Pivot sits at the base (y=0); +y is the free tip.
export function filamentGeo(len, { baseR = 0.055, curve = 0.22, tubular = 8, radial = 5 } = {}) {
  const pts = [];
  for (let i = 0; i <= 6; i++) {
    const t = i / 6;
    pts.push(new THREE.Vector3(Math.sin(t * Math.PI * 0.5) * curve * len, t * len, 0));
  }
  const c = new THREE.CatmullRomCurve3(pts);
  const geo = new THREE.TubeGeometry(c, tubular, baseR * len, radial, false);
  const pos = geo.attributes.position;
  for (let i = 0; i <= tubular; i++) {
    const t = i / tubular;
    const cc = c.getPointAt(t);
    const rr = 1 - t * 0.85;                    // taper to a fine tip
    for (let j = 0; j <= radial; j++) {
      const idx = i * (radial + 1) + j;
      const vx = pos.getX(idx), vy = pos.getY(idx), vz = pos.getZ(idx);
      pos.setXYZ(idx, cc.x + (vx - cc.x) * rr, cc.y + (vy - cc.y) * rr, cc.z + (vz - cc.z) * rr);
    }
  }
  geo.computeVertexNormals();
  return geo;
}

// ── Ciliary band ────────────────────────────────────────────────────────────
// A ring of fine beating cilia — the corona of a rotifer, the coat of a
// ciliate. Returned as an InstancedMesh plus a beat(t) that runs the
// metachronal wave (the shimmering "conveyor" real cilia show). No per-frame
// allocation: the pose scratch object is hoisted out of the beat loop.
export function ciliaRing(radius, count, len, material, { axis = 'y', spread = 0.0 } = {}) {
  const geo = filamentGeo(len, { baseR: 0.05, curve: 0.28 });
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
  const pose = new THREE.Object3D();
  mesh.userData.beat = (t, amp = 0.5) => {
    for (let i = 0; i < count; i++) {
      const b = base[i];
      const phase = t * 6 - b.a * 3;             // metachronal wave around the ring
      const bend = Math.sin(phase) * amp;
      pose.position.set(b.x, b.y, b.z);
      if (axis === 'y') pose.rotation.set(Math.PI * 0.5 + bend * 0.5, b.a, bend);
      else pose.rotation.set(bend, b.a, Math.PI * 0.5 + bend * 0.5);
      pose.updateMatrix();
      mesh.setMatrixAt(i, pose.matrix);
    }
    mesh.instanceMatrix.needsUpdate = true;
  };
  return mesh;
}

// A patch of cilia over a surface region (paramecium coat) — instanced fine
// hairs placed on an ellipsoid, beating in a travelling wave.
export function ciliaCoat(rx, ry, rz, count, len, material, { seed = 1337 } = {}) {
  const geo = filamentGeo(len, { baseR: 0.06, curve: 0.2 });
  const mesh = new THREE.InstancedMesh(geo, material, count);
  const base = [];
  const dummy = new THREE.Object3D();
  const r = rng(seed);
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
  const pose = new THREE.Object3D();
  const q = new THREE.Quaternion();
  mesh.userData.beat = (t) => {
    for (let i = 0; i < count; i++) {
      const b = base[i];
      const bend = Math.sin(t * 7 - b.phase * 4) * 0.45;
      pose.position.copy(b.p);
      q.setFromUnitVectors(up, b.n);
      pose.quaternion.copy(q);
      pose.rotateX(bend);
      pose.updateMatrix();
      mesh.setMatrixAt(i, pose.matrix);
    }
    mesh.instanceMatrix.needsUpdate = true;
  };
  return mesh;
}

// A rotating helical filament — a bacterial flagellum, read as a real corkscrew
// rather than a wire. Returns a Mesh whose geometry is a tapered helix tube; the
// caller spins it about the helix axis (its local x) to drive the cell.
export function helixFilament(len, coils, amp, material, { thickness = 0.02, taper = true, samples = 90 } = {}) {
  const pts = [];
  for (let i = 0; i <= samples; i++) {
    const t = i / samples;
    const grow = taper ? t : 1;                  // helix opens out from the pole
    pts.push(new THREE.Vector3(
      -t * len,
      Math.sin(t * Math.PI * 2 * coils) * amp * grow,
      Math.cos(t * Math.PI * 2 * coils) * amp * grow,
    ));
  }
  const curve = new THREE.CatmullRomCurve3(pts);
  const geo = new THREE.TubeGeometry(curve, samples, thickness, 6, false);
  const mesh = new THREE.Mesh(geo, material);
  mesh.userData.curve = curve;
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
export function blob(rx, ry, rz, material, seg = 32) {
  const geo = new THREE.SphereGeometry(1, seg, Math.max(12, seg - 8));
  geo.scale(rx, ry, rz);
  return new THREE.Mesh(geo, material);
}

// A field of granules suspended in a body — ribosomes, yolk, storage droplets.
// One InstancedMesh, so thousands of specks cost a single draw.
export function granuleField(rx, ry, rz, count, rBase, material, { seed = 11 } = {}) {
  const geo = new THREE.SphereGeometry(rBase, 6, 6);
  const mesh = new THREE.InstancedMesh(geo, material, count);
  const d = new THREE.Object3D();
  const r = rng(seed);
  for (let i = 0; i < count; i++) {
    // rejection-sample inside the ellipsoid so density is even, not shelled
    let x, y, z;
    do { x = r() * 2 - 1; y = r() * 2 - 1; z = r() * 2 - 1; } while (x * x + y * y + z * z > 1);
    const s = 0.6 + r() * 0.7;
    d.position.set(x * rx, y * ry, z * rz);
    d.scale.setScalar(s);
    d.updateMatrix();
    mesh.setMatrixAt(i, d.matrix);
  }
  return mesh;
}

// Clamp/tuning shared by the animation loops.
export const TAU = Math.PI * 2;
export const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
export const lerp = (a, b, t) => a + (b - a) * t;
export const smooth = (t) => t * t * (3 - 2 * t);
