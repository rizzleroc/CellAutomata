// Capstone — Stromatolite hand specimen (~3.5 Ga).
//
// NOT an apparatus: a museum hand specimen on a felt mount under gallery
// lighting. A sawn, slightly-beveled rock slab whose polished front face shows
// wavy laminations (painted via lib.makeDynamicTexture: wavy ochre/cream/grey
// layers + a pale calcite vein). A rough darker crust runs along the top edge,
// a small 1 cm scale-bar plate sits in front, and the whole thing rests on a
// low dark museum mount/plinth. Animation is minimal: progress is always 0;
// setRunning is a no-op; only a very slow raking-light highlight drifts.

import * as THREE from 'three';
import { part, V, bakeliteMat, steelMat, makeDynamicTexture, labelSprite } from './lib.js';

export function build() {
  const group = new THREE.Group();
  group.name = 'stromatolite-specimen';

  // ── Museum mount / plinth (low, dark) ─────────────────────────────────────
  group.add(part(new THREE.BoxGeometry(3.6, 0.5, 2.4), bakeliteMat(0x14110e), 'museum-mount', V(0, 0.25, 0)));
  // felt pad on top of the mount
  group.add(part(new THREE.BoxGeometry(3.2, 0.06, 2.0),
    new THREE.MeshStandardMaterial({ color: 0x3a1414, roughness: 0.95, metalness: 0 }),
    'museum-felt', V(0, 0.53, 0)));

  // ── The slab: an irregular extruded boxy block, slightly beveled ──────────
  // Bevel via a shallow chamfer: a big block + thin angled top/side trims.
  const rockMat = new THREE.MeshStandardMaterial({ color: 0x6b5a44, roughness: 0.85, metalness: 0.05 });
  const slab = part(new THREE.BoxGeometry(2.6, 2.4, 0.8), rockMat, 'slab', V(0, 1.78, -0.1));
  // slight irregular lean so it doesn't read as a perfect box
  slab.rotation.z = 0.02; group.add(slab);

  // ── Polished front face: painted wavy laminations ─────────────────────────
  const dyn = makeDynamicTexture(512);
  const faceMat = new THREE.MeshPhysicalMaterial({
    map: dyn.tex, roughness: 0.12, metalness: 0.0, clearcoat: 0.7, clearcoatRoughness: 0.1,
  });
  const face = part(new THREE.PlaneGeometry(2.5, 2.3), faceMat, 'slab-face', V(0, 1.78, 0.31));
  face.rotation.z = 0.02; group.add(face);

  // ── Rough darker crust along the top edge ─────────────────────────────────
  const crustMat = new THREE.MeshStandardMaterial({ color: 0x2c2218, roughness: 0.98, metalness: 0 });
  const crust = part(new THREE.BoxGeometry(2.7, 0.34, 0.9), crustMat, 'slab-crust', V(0, 3.02, -0.1));
  crust.rotation.z = 0.02;
  // jitter the crust scale to look broken/irregular
  crust.scale.set(1.0, 1.0 + Math.random() * 0.15, 1.0);
  group.add(crust);

  // ── Pale calcite vein (a thin bright crystalline streak on the face) ──────
  const veinMat = new THREE.MeshStandardMaterial({ color: 0xe8e2d0, roughness: 0.3, metalness: 0.1, emissive: 0x161410 });
  const vein = part(new THREE.BoxGeometry(0.07, 2.2, 0.02), veinMat, 'calcite-vein', V(0.55, 1.78, 0.32));
  vein.rotation.z = 0.18; group.add(vein);

  // ── 1 cm scale-bar plate in front ─────────────────────────────────────────
  const barGroup = new THREE.Group(); barGroup.name = 'scale-bar';
  barGroup.position.set(-0.9, 0.6, 0.95);
  barGroup.add(part(new THREE.BoxGeometry(0.7, 0.18, 0.04),
    new THREE.MeshStandardMaterial({ color: 0xf4efe2, roughness: 0.4 }), 'scale-bar-plate'));
  // alternating black/white 1 cm ticks
  for (let i = 0; i < 5; i++) {
    if (i % 2 === 0) continue;
    barGroup.add(part(new THREE.BoxGeometry(0.13, 0.16, 0.02),
      new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.6 }),
      `scale-tick-${i}`, V(-0.28 + i * 0.14, 0, 0.02)));
  }
  group.add(barGroup);

  // ── Museum label card sprite ──────────────────────────────────────────────
  const label = labelSprite('Stromatolite', '~3.5 Ga · microbial laminations');
  label.position.set(0.95, 0.55, 0.95); label.scale.set(1.7, 0.65, 1);
  group.add(label);

  // gallery spotlight on the specimen
  const spot = new THREE.SpotLight(0xfff4e0, 2.2, 9, Math.PI / 7, 0.5, 1.5);
  spot.position.set(-1.5, 5.5, 3.0); spot.target = slab; group.add(spot); group.add(spot.target);

  group.position.y = 0;

  // ── Paint the laminations onto the polished face ──────────────────────────
  // Wavy ochre/cream/grey bands; raking-highlight band drifts very slowly.
  const bandCols = ['#8a6f44', '#b89a63', '#d8c79b', '#6f5d44', '#9a8156', '#cdbf9a', '#5e5440'];
  function paint(highlight) {
    const ctx = dyn.ctx, S = dyn.size;
    ctx.fillStyle = '#5b4a36'; ctx.fillRect(0, 0, S, S);
    const bands = 26;
    for (let i = 0; i < bands; i++) {
      const y = i / bands * S;
      const h = S / bands + 2;
      ctx.fillStyle = bandCols[i % bandCols.length];
      ctx.beginPath();
      ctx.moveTo(0, y);
      // wavy top edge of the band
      for (let x = 0; x <= S; x += 16) {
        const wob = Math.sin(x * 0.018 + i * 0.7) * 9 + Math.sin(x * 0.05 + i) * 4;
        ctx.lineTo(x, y + wob);
      }
      ctx.lineTo(S, y + h); ctx.lineTo(0, y + h); ctx.closePath();
      ctx.fill();
    }
    // pale calcite vein streak on the texture too
    ctx.strokeStyle = 'rgba(232,226,208,0.8)'; ctx.lineWidth = 8;
    ctx.beginPath(); ctx.moveTo(S * 0.62, 0); ctx.lineTo(S * 0.72, S); ctx.stroke();
    // slow raking specular highlight
    const hx = highlight * S;
    const g = ctx.createLinearGradient(hx - 80, 0, hx + 80, 0);
    g.addColorStop(0, 'rgba(255,255,255,0)');
    g.addColorStop(0.5, 'rgba(255,250,235,0.18)');
    g.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, S, S);
    dyn.tex.needsUpdate = true;
  }
  paint(0.3);

  group.userData.anim = {
    setRunning(_on) { /* terminal specimen: no-op */ },
    getProgress() { return 0; },
    reset() { paint(0.3); },
    update(dt, t) {
      // very slow raking-light drift across the polished face
      const h = 0.5 + 0.45 * Math.sin(t * 0.12);
      paint(h);
    },
  };
  return group;
}

export const meta = {
  id: 'capstone-stromatolite',
  label: 'Capstone — Stromatolite',
  title: 'Stromatolite hand specimen · ~3.5 Ga',
  blurb: 'Layered structures built by ancient microbial mats — the oldest physical evidence '
       + 'of life. The terminal specimen: what the whole pipeline leaves in the rock record.',
  build,
};
