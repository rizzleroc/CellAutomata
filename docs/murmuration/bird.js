// Murmuration — the bird, as an InstancedMesh with a shader wingbeat.
//
// A murmuration is thousands of birds; that rules out a mesh per bird. Every
// starling is one instance of a single low-poly swept-wing silhouette, and the
// wingbeat happens on the GPU: a vertex-shader dihedral flap keyed to a
// per-instance phase, so 4000 birds beat their wings out of sync for the cost
// of one draw call. `main.js` writes each instance's matrix every frame from
// the flock state (position + heading + bank); this module owns the geometry,
// the flap shader, the peregrine, and the matrix-composition helper so the
// controller stays free of three-math boilerplate.

// ── the shared bird silhouette ─────────────────────────────────────────────
// Local frame: +Z forward (nose), +Y up, +X right. Two swept triangles read as
// a bird from any distance. `aWing` ∈ [0,1] is the spanwise fraction (0 at the
// spine, 1 at the tip) — the shader lifts each vertex by aWing·flap so both
// wings beat up and down together.
function birdGeometry(THREE, size) {
  const s = size;
  //            x         y      z
  const nose  = [0, 0, 0.7 * s];
  const tail  = [0, 0.02 * s, -0.7 * s];
  const rTip  = [1.0 * s, 0, -0.32 * s];
  const lTip  = [-1.0 * s, 0, -0.32 * s];
  const mid   = [0, 0, -0.05 * s];

  // right wing (nose, rTip, mid)(rTip, tail, mid); left mirror — a shallow delta
  const tris = [
    nose, rTip, mid,
    rTip, tail, mid,
    nose, mid, lTip,
    lTip, mid, tail,
  ];
  const pos = new Float32Array(tris.length * 3);
  const wing = new Float32Array(tris.length);
  for (let i = 0; i < tris.length; i++) {
    pos[i * 3] = tris[i][0]; pos[i * 3 + 1] = tris[i][1]; pos[i * 3 + 2] = tris[i][2];
    wing[i] = Math.min(1, Math.abs(tris[i][0]) / (1.0 * s)); // spanwise fraction
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  geo.setAttribute('aWing', new THREE.BufferAttribute(wing, 1));
  geo.computeVertexNormals();
  return geo;
}

// Build the whole flock as one InstancedMesh. Returns the mesh plus a `tick`
// that advances the wingbeat clock. Per-instance flap phase and rate live in
// instanced attributes so every bird is on its own beat.
export function makeFlock(THREE, count, { size = 1.6, rng = Math.random } = {}) {
  const geo = birdGeometry(THREE, size);

  const phase = new Float32Array(count);
  const rate = new Float32Array(count);
  for (let i = 0; i < count; i++) {
    phase[i] = rng() * Math.PI * 2;
    rate[i] = 9 + rng() * 4;          // wingbeats ~1.5–2 Hz worth of angular rate
  }
  geo.setAttribute('aPhase', new THREE.InstancedBufferAttribute(phase, 1));
  geo.setAttribute('aRate', new THREE.InstancedBufferAttribute(rate, 1));

  // Dark, faintly iridescent plumage; the dusk rim light does the shaping.
  const mat = new THREE.MeshStandardMaterial({
    color: 0x14161c,
    roughness: 0.55,
    metalness: 0.35,
    side: THREE.DoubleSide,
    flatShading: true,
  });

  const uniforms = { uTime: { value: 0 }, uFlap: { value: 0.55 } };
  mat.onBeforeCompile = (shader) => {
    shader.uniforms.uTime = uniforms.uTime;
    shader.uniforms.uFlap = uniforms.uFlap;
    shader.vertexShader =
      'attribute float aWing;\nattribute float aPhase;\nattribute float aRate;\n' +
      'uniform float uTime;\nuniform float uFlap;\n' +
      shader.vertexShader.replace(
        '#include <begin_vertex>',
        `#include <begin_vertex>
         float flap = sin(uTime * aRate + aPhase);
         transformed.y += aWing * uFlap * flap;          // dihedral wingbeat
         transformed.z -= aWing * 0.12 * (1.0 - flap);   // tips sweep with the beat`,
      );
  };

  const mesh = new THREE.InstancedMesh(geo, mat, count);
  mesh.frustumCulled = false;   // the flock centroid moves; keep them all drawn
  mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  mesh.name = 'flock';
  mesh.userData.uniforms = uniforms;
  mesh.userData.tick = (t) => { uniforms.uTime.value = t; };
  return mesh;
}

// Compose one instance matrix from a bird's world position, heading and bank.
// Reused scratch objects (passed in) keep this allocation-free in the hot loop.
export function orient(THREE, m, scratch, px, py, pz, fx, fy, fz, bank, scale) {
  const fwd = scratch.fwd.set(fx, fy, fz).normalize();
  // bank rolls the up-vector about the heading, so the wings tilt into turns
  const right = scratch.right.set(fwd.z, 0, -fwd.x).normalize();
  if (!isFinite(right.x) || right.lengthSq() < 1e-6) right.set(1, 0, 0);
  const up = scratch.up.crossVectors(right, fwd).normalize();
  const cb = Math.cos(bank), sb = Math.sin(bank);
  // rolledUp = up·cos + right·sin  (matches the lift tilt in flock.js)
  const rux = up.x * cb + right.x * sb, ruy = up.y * cb + right.y * sb, ruz = up.z * cb + right.z * sb;
  up.set(rux, ruy, ruz).normalize();
  // right-handed basis: X = up × fwd keeps det = +1, so the mesh isn't mirrored
  // (a mirror would flip the wingbeat and reverse every bank on screen).
  const s = scratch.side.crossVectors(up, fwd).normalize();
  // basis columns: X=side, Y=up, Z=fwd
  m.set(
    s.x, up.x, fwd.x, px,
    s.y, up.y, fwd.y, py,
    s.z, up.z, fwd.z, pz,
    0, 0, 0, 1,
  );
  if (scale !== 1) m.scale(scratch.scl.set(scale, scale, scale));
  return m;
}

export function makeScratch(THREE) {
  return {
    fwd: new THREE.Vector3(), right: new THREE.Vector3(), up: new THREE.Vector3(),
    side: new THREE.Vector3(), scl: new THREE.Vector3(),
  };
}

// ── the peregrine ──────────────────────────────────────────────────────────
// A larger, paler raptor with long pointed wings so the hunter reads instantly
// against the dark flock. Same local frame; its own gentle wingbeat.
export function makePredator(THREE, { size = 4.5 } = {}) {
  const g = new THREE.Group();
  g.name = 'peregrine';
  const s = size;

  const bodyGeo = new THREE.ConeGeometry(0.18 * s, 1.3 * s, 6);
  bodyGeo.rotateX(Math.PI / 2);            // point the cone forward (+Z)
  const bodyMat = new THREE.MeshStandardMaterial({ color: 0x6b7280, roughness: 0.5, metalness: 0.2, flatShading: true });
  const body = new THREE.Mesh(bodyGeo, bodyMat);
  body.name = 'raptor-body';
  g.add(body);

  // long swept wings as two thin triangles
  const wingGeo = new THREE.BufferGeometry();
  const wp = new Float32Array([
    0, 0, 0.2 * s, 1.6 * s, 0, -0.5 * s, 0, 0, -0.5 * s,
    0, 0, 0.2 * s, 0, 0, -0.5 * s, -1.6 * s, 0, -0.5 * s,
  ]);
  wingGeo.setAttribute('position', new THREE.BufferAttribute(wp, 3));
  wingGeo.computeVertexNormals();
  const wingMat = new THREE.MeshStandardMaterial({ color: 0x8b93a1, roughness: 0.6, side: THREE.DoubleSide, flatShading: true });
  const wings = new THREE.Mesh(wingGeo, wingMat);
  wings.name = 'raptor-wings';
  g.add(wings);

  g.userData.tick = (t) => { wings.rotation.z = Math.sin(t * 6) * 0.18; };
  return g;
}
