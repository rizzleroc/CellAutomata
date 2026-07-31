// Shared lab-parts library for web4 apparatus modules.
//
// Every stage apparatus imports its materials + helpers from here so the whole
// lab reads as one continuous vintage-1953 bench: warm brass/steel, aged
// borosilicate glass, Bakelite knobs. Keeping materials here (not per-module)
// is what makes 12 separately-authored apparatus look like one photograph.
//
// ── Apparatus contract (every stage module exports this) ────────────────────
//   export function build(): THREE.Group
//       - children are named meshes (for the parts panel + exploded view)
//       - group sits on the bench at y≈0, roughly 0..6 tall, centred on x≈0
//       - group.userData.anim = {
//             setRunning(on:boolean),     // start/stop the experiment
//             getProgress(): number,      // 0..1 for the readout (or 0)
//             reset(),                    // rewind the experiment
//             update(dt:number, t:number),// per-frame animation
//         }
//   export const meta = { id, label, title, blurb, build }

import * as THREE from 'three';

export { THREE };
export const V = (x, y, z = 0) => new THREE.Vector3(x, y, z);

// ── Procedural surface detail (ported from pondwater/organisms/lib.js) ───────
// Value-noise fbm → a tangent-space normal map, generated as a DataTexture at
// build time (no canvas, so it is identical under the headless test harness).
// Cached by key so the whole bench shares a handful of textures, not dozens.
// Runs only at browser shader-compile → invisible to the node stub, test-safe.
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
// height(u,v) shapers by surface "kind" — ridged rows, grainy field, segmented
// bands, or plain fbm bumpiness.
function _height(u, v, kind, freq, seed) {
  let n = 0, amp = 1, f = freq, norm = 0;
  for (let o = 0; o < 4; o++) { n += _valueNoise(u * f, v * f, seed + o * 17) * amp; norm += amp; amp *= 0.5; f *= 2; }
  n /= norm;
  if (kind === 'ridges') {
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

// ── Fresnel rim (ported from pondwater/organisms/lib.js) ─────────────────────
// A Fresnel term added to outgoingLight through onBeforeCompile — no extra
// geometry, no extra draw call — so glassy edges catch the light and bloom.
// Chains cleanly onto any existing onBeforeCompile. Browser-only (shader
// compile), so it never touches the headless tests.
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

// ── Materials (fresh instance per call so meshes can diverge) ───────────────
// Aged borosilicate: real transmission with a touch of volumetric attenuation
// and a cool Fresnel rim so the glass edges light up against the obsidian void.
export const glassMat = () => addRim(new THREE.MeshPhysicalMaterial({
  color: 0xffffff, metalness: 0, roughness: 0.03,
  transmission: 1.0, thickness: 0.6, ior: 1.5,
  transparent: true, envMapIntensity: 2.2, clearcoat: 0.6, clearcoatRoughness: 0.06,
  attenuationColor: new THREE.Color(0xeaf3f5), attenuationDistance: 6.0,
}), { color: 0xbfe0ff, power: 3.2, intensity: 0.35 });
export const steelMat = () => new THREE.MeshStandardMaterial({ color: 0x8c8f96, metalness: 0.95, roughness: 0.42 });
export const brassMat = () => new THREE.MeshStandardMaterial({ color: 0xb8893f, metalness: 1.0, roughness: 0.32 });
export const darkMetalMat = () => new THREE.MeshStandardMaterial({ color: 0x1b1b1f, metalness: 0.7, roughness: 0.5 });
export const copperMat = () => new THREE.MeshStandardMaterial({ color: 0xb5703a, metalness: 0.9, roughness: 0.35 });
export const ceramicMat = () => new THREE.MeshStandardMaterial({ color: 0x141414, roughness: 0.85, metalness: 0.05 });
export const bakeliteMat = (c = 0x241c14) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.55, metalness: 0.1 });
export const plasticMat = (c = 0xded6c6) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.6, metalness: 0.0 });
export const rubberMat = (c = 0x2a2a2e) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.85, metalness: 0.0 });
// translucent liquid; pass a hex colour. Depth-attenuation gives it a bodied,
// wet look (bodied but NOT muddy — kept light so suspended detail reads through).
export const liquidMat = (color = 0x3a1d08, opts = {}) => new THREE.MeshPhysicalMaterial({
  color, roughness: 0.12, transmission: 0.6, thickness: 1.0, ior: 1.34, transparent: true,
  clearcoat: 0.5, clearcoatRoughness: 0.15,
  attenuationColor: new THREE.Color(color).lerp(new THREE.Color(0x0a1a1a), 0.35),
  attenuationDistance: 2.6, envMapIntensity: 1.4, ...opts,
});
export const emissiveMat = (color = 0xc77dff) => new THREE.MeshBasicMaterial({ color });

// ── Geometry helpers ────────────────────────────────────────────────────────
// Swept glass tube along a polyline of THREE.Vector3.
export function tube(points, radius = 0.085, name = 'tube', material = null) {
  const curve = new THREE.CatmullRomCurve3(points);
  const geo = new THREE.TubeGeometry(curve, Math.max(24, points.length * 12), radius, 20, false);
  const m = new THREE.Mesh(geo, material || glassMat());
  m.name = name; m.castShadow = true;
  return m;
}

// Named mesh in one call.
export function part(geo, material, name, pos = null) {
  const m = new THREE.Mesh(geo, material);
  m.name = name; m.castShadow = true; m.receiveShadow = false;
  if (pos) m.position.copy(pos);
  return m;
}

// A round-bottom / boiling flask: bulb + neck + collar. Returns a Group.
export function flask(radius = 0.85, name = 'flask', neckH = 0.5) {
  const g = new THREE.Group(); g.name = name;
  const bulb = part(new THREE.SphereGeometry(radius, 48, 36), glassMat(), `${name}-bulb`);
  g.add(bulb);
  g.add(part(new THREE.CylinderGeometry(radius * 0.22, radius * 0.16, neckH, 24), glassMat(),
    `${name}-neck`, V(0, radius + neckH * 0.4, 0)));
  return g;
}

// Museum label card sprite.
export function labelSprite(title, subtitle = '') {
  const c = document.createElement('canvas'); c.width = 1024; c.height = 384;
  const g = c.getContext('2d');
  g.fillStyle = 'rgba(7,9,13,0.92)'; g.fillRect(0, 0, c.width, c.height);   // obsidian card
  g.strokeStyle = 'rgba(63,224,208,0.45)'; g.lineWidth = 1.5; g.strokeRect(20, 20, c.width - 40, c.height - 40);  // teal hairline
  g.fillStyle = '#ece7da'; g.textAlign = 'center'; g.font = '56px "Italiana", Georgia, serif';
  g.fillText(title, c.width / 2, 156);
  if (subtitle) { g.fillStyle = '#9a9280'; g.font = '26px "IBM Plex Mono", monospace'; g.fillText(subtitle, c.width / 2, 244); }
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true }));
  s.scale.set(2.6, 1.0, 1);
  return s;
}

// CanvasTexture you can repaint every frame (for sim surfaces: BZ spirals,
// quasispecies, coacervate fields). drawFn(ctx, t, w, h) paints one frame.
export function makeDynamicTexture(size = 256) {
  const c = document.createElement('canvas'); c.width = c.height = size;
  const ctx = c.getContext('2d');
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  return { canvas: c, ctx, tex, size };
}

// A standard brass-fitted steel ring-stand at x, with clamp arms at given heights.
export function ringStand(x = 3.0, z = -0.3, armHeights = [], height = 6.4) {
  const g = new THREE.Group(); g.name = 'ring-stand';
  g.add(part(new THREE.BoxGeometry(1.6, 0.1, 1.0), steelMat(), 'stand-base', V(x, 0.05, z)));
  g.add(part(new THREE.CylinderGeometry(0.05, 0.05, height, 20), steelMat(), 'stand-rod', V(x, height / 2, z)));
  for (const cy of armHeights) {
    const arm = part(new THREE.CylinderGeometry(0.035, 0.035, 1.7, 12), steelMat(), `stand-arm-${cy}`, V(x - 0.8, cy, z + 0.15));
    arm.rotation.z = Math.PI / 2;
    g.add(arm);
    g.add(part(new THREE.CylinderGeometry(0.1, 0.1, 0.22, 16), brassMat(), `clamp-boss-${cy}`, V(x, cy, z)));
  }
  return g;
}

// Standard animation object with sane defaults; pass overrides.
export function makeAnim(overrides = {}) {
  let running = true, progress = 0;
  return {
    setRunning(on) { running = on; if (overrides.onRunning) overrides.onRunning(on); },
    isRunning() { return running; },
    getProgress() { return progress; },
    setProgress(p) { progress = Math.max(0, Math.min(1, p)); },
    reset() { progress = 0; if (overrides.onReset) overrides.onReset(); },
    update(dt, t) { if (overrides.onUpdate) overrides.onUpdate(dt, t, { running, get progress() { return progress; }, set progress(p) { progress = p; } }); },
  };
}

// ── Rolling-boil bubble column ──────────────────────────────────────────────
// The nested-transmission-proof boil. three.js screen-space transmission only
// refracts the OPAQUE backbuffer, so bubbles inside transmissive water must be
// bright, low-roughness, slightly-EMISSIVE, Fresnel-rimmed OPAQUE spheres —
// they live in the opaque pass the water refracts, so they read as bright beads
// and their rims catch the bloom. (Do NOT make them transmissive: they vanish.)
//
// Fixed-count pool (the anim gate compares min-length signatures, so the count
// must never change frame to frame). Returns { group, update(dt,t), setRunning }.
export function bubbleColumn(opts = {}) {
  const center = opts.center || new THREE.Vector3(0, 0, 0);
  const radius = opts.radius ?? 0.8;
  const floorY = opts.floorY ?? (center.y - radius * 0.9);
  const topY = opts.topY ?? (center.y + radius * 0.2);
  const count = opts.count ?? 40;
  const rMin = opts.rMin ?? 0.03;
  const rMax = opts.rMax ?? 0.085;
  const rise = opts.rise ?? 0.5;
  const lateral = opts.lateral ?? 0.03;
  const grow = opts.grow ?? 0.4;
  const span = Math.max(0.001, topY - floorY);

  // deterministic LCG so a build re-seeds identically (no Math.random surprises)
  let _s = (opts.seed ?? 0x2545f491) >>> 0;
  const rnd = () => { _s = (Math.imul(_s, 1664525) + 1013904223) >>> 0; return _s / 4294967296; };

  const group = new THREE.Group();
  group.name = opts.name || 'bubble-column';
  const geo = new THREE.SphereGeometry(1, 10, 10);
  const mat = addRim(new THREE.MeshStandardMaterial({
    color: opts.color ?? 0xf2fbff,
    emissive: new THREE.Color(0xbfe8ff).multiplyScalar(0.35),
    roughness: 0.12, metalness: 0,
  }), { color: 0xffffff, power: 2.2, intensity: 0.8 });

  const pool = [];
  const spawn = (b, atFloor) => {
    const ang = rnd() * Math.PI * 2;
    const rr = Math.sqrt(rnd()) * radius;              // uniform disc, bounded
    b.position.set(center.x + Math.cos(ang) * rr,
                   atFloor ? floorY : floorY + rnd() * span,
                   center.z + Math.sin(ang) * rr);
    const rad = rMin + rnd() * Math.max(0, rMax - rMin);
    b.scale.setScalar(rad);
    b.userData.v = rise * (0.7 + rnd() * 0.6);
    b.userData.phase = rnd() * Math.PI * 2;
    b.userData.w = 1.2 + rnd() * 2.0;
    b.userData.bx = b.position.x; b.userData.bz = b.position.z;
  };
  for (let i = 0; i < count; i++) {
    const b = new THREE.Mesh(geo, mat);
    b.name = 'bubble';
    spawn(b, false);
    group.add(b);
    pool.push(b);
  }

  let running = true;
  return {
    group,
    setRunning(on) { running = !!on; group.visible = !!on; },
    update(dt, t) {
      if (!running) return;
      const d = Number.isFinite(dt) ? dt : 0;
      for (const b of pool) {
        b.position.y += b.userData.v * d;
        // rolling-boil lateral wobble, bounded around the spawn column
        b.position.x = b.userData.bx + Math.sin(t * b.userData.w + b.userData.phase) * lateral;
        b.position.z = b.userData.bz + Math.cos(t * b.userData.w * 0.9 + b.userData.phase) * lateral;
        b.scale.multiplyScalar(1 + d * grow);          // swell slightly as it rises
        if (b.position.y >= topY || b.scale.x > rMax * 3) spawn(b, true);
      }
    },
  };
}

// ── Liquid volume with a flat, rippling meniscus ────────────────────────────
// A real filled volume plus a FLAT glinting surface disc — the thing that kills
// the "squashed sphere" fake. Returns { group, body, meniscus, setLevel, shimmer }.
export function liquidVolume(radius = 0.9, level = 0.5, mat = null, opts = {}) {
  const shape = opts.shape || 'sphere';
  const segments = opts.segments ?? 40;
  const ripple = opts.ripple !== false;
  const name = opts.name || 'liquid';
  const body_r98 = radius * 0.98;
  const material = mat || liquidMat();

  const group = new THREE.Group();
  group.name = name;

  const bodyGeo = shape === 'cylinder'
    ? new THREE.CylinderGeometry(radius, radius, 1, segments)
    : new THREE.SphereGeometry(radius, segments, 28);
  const body = new THREE.Mesh(bodyGeo, material);
  body.name = `${name}-body`;
  group.add(body);

  const menMat = material.clone();
  menMat.clearcoat = 1.0;
  menMat.clearcoatRoughness = 0.06;
  menMat.roughness = 0.04;
  if (ripple) {
    menMat.normalMap = surfaceNormalMap({ kind: 'fbm', freq: 5, strength: 0.4 });
    menMat.normalScale = new THREE.Vector2(0.25, 0.25);
  }
  const meniscus = new THREE.Mesh(new THREE.CircleGeometry(body_r98, segments), menMat);
  meniscus.name = `${name}-meniscus`;
  meniscus.rotation.x = -Math.PI / 2;
  group.add(meniscus);

  let _level = level;
  function setLevel(f) {
    f = Math.max(0, Math.min(1, Number.isFinite(f) ? f : 0));
    _level = f;
    if (shape === 'cylinder') {
      body.scale.y = Math.max(0.001, 2 * radius * f);
      body.position.y = radius * f - radius;
      meniscus.position.y = body.position.y + body.scale.y * 0.5;
      meniscus.scale.setScalar(1);
    } else {
      const yLine = -radius + 2 * radius * f;
      const rr = radius * Math.sqrt(Math.max(0.02, 1 - (2 * f - 1) * (2 * f - 1)));
      body.scale.y = Math.max(0.05, f);
      body.position.y = -radius * (1 - f);
      meniscus.position.y = yLine;
      meniscus.scale.setScalar(rr / body_r98);
    }
  }
  setLevel(level);

  function shimmer(t) {
    const base = shape === 'cylinder'
      ? body.position.y + body.scale.y * 0.5
      : -radius + 2 * radius * _level;
    meniscus.position.y = base + Math.sin(t * 3) * 1e-4;
    if (menMat.normalMap && menMat.normalScale) {
      const s = 0.25 + Math.sin(t * 2) * 0.02;
      menMat.normalScale.set(s, s);
    }
  }

  return { group, body, meniscus, setLevel, shimmer };
}
