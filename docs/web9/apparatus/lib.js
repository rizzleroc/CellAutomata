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

// ── Materials (fresh instance per call so meshes can diverge) ───────────────
export const glassMat = () => new THREE.MeshPhysicalMaterial({
  color: 0xffffff, metalness: 0, roughness: 0.04,
  transmission: 1.0, thickness: 0.35, ior: 1.5,
  transparent: true, envMapIntensity: 1.4, clearcoat: 0.3, clearcoatRoughness: 0.1,
});
export const steelMat = () => new THREE.MeshStandardMaterial({ color: 0x8c8f96, metalness: 0.95, roughness: 0.42 });
export const brassMat = () => new THREE.MeshStandardMaterial({ color: 0xb8893f, metalness: 1.0, roughness: 0.32 });
export const darkMetalMat = () => new THREE.MeshStandardMaterial({ color: 0x1b1b1f, metalness: 0.7, roughness: 0.5 });
export const copperMat = () => new THREE.MeshStandardMaterial({ color: 0xb5703a, metalness: 0.9, roughness: 0.35 });
export const ceramicMat = () => new THREE.MeshStandardMaterial({ color: 0x141414, roughness: 0.85, metalness: 0.05 });
export const bakeliteMat = (c = 0x241c14) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.55, metalness: 0.1 });
export const plasticMat = (c = 0xded6c6) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.6, metalness: 0.0 });
export const rubberMat = (c = 0x2a2a2e) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.85, metalness: 0.0 });
// translucent liquid; pass a hex colour. transmission gives the meniscus glow.
export const liquidMat = (color = 0x3a1d08, opts = {}) => new THREE.MeshPhysicalMaterial({
  color, roughness: 0.2, transmission: 0.6, thickness: 1.0, ior: 1.34, transparent: true, ...opts,
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
