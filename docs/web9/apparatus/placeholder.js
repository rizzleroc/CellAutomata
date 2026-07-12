// Placeholder apparatus for stages whose photoreal GLB hasn't been baked yet
// (needs the touch-app / Tripo backend up). A museum pedestal + a label card,
// so the lab shell is navigable end-to-end before every apparatus exists.

import * as THREE from 'three';

export function buildPlaceholder(meta) {
  const group = new THREE.Group();
  group.name = `placeholder-${meta.id}`;

  const pedestal = new THREE.Mesh(
    new THREE.CylinderGeometry(1.1, 1.3, 0.5, 48),
    new THREE.MeshStandardMaterial({ color: 0x14181f, roughness: 0.82, metalness: 0.1 }),  // obsidian plinth
  );
  pedestal.position.y = 0.25; pedestal.castShadow = true; pedestal.receiveShadow = true;
  group.add(pedestal);

  // slowly rotating wireframe "specimen-pending" form, in luminous teal
  const form = new THREE.Mesh(
    new THREE.IcosahedronGeometry(0.9, 1),
    new THREE.MeshStandardMaterial({ color: 0x2a7d75, roughness: 0.5, metalness: 0.3, wireframe: true }),
  );
  form.position.y = 1.7; group.add(form);

  group.add(makeLabel(meta));

  let t = 0;
  group.userData.anim = {
    setRunning() {},
    getProgress() { return 0; },
    reset() {},
    update(dt) { t += dt; form.rotation.y = t * 0.4; form.position.y = 1.7 + Math.sin(t) * 0.06; },
  };
  return group;
}

function makeLabel(meta) {
  const c = document.createElement('canvas');
  c.width = 1024; c.height = 512;
  const g = c.getContext('2d');
  // Catalytic Silence label card: obsidian ground, a teal hairline, museum type.
  g.fillStyle = 'rgba(7,9,13,0.92)'; g.fillRect(0, 0, c.width, c.height);
  g.strokeStyle = 'rgba(63,224,208,0.45)'; g.lineWidth = 1.5; g.strokeRect(24, 24, c.width - 48, c.height - 48);
  g.fillStyle = '#ece7da'; g.textAlign = 'center';
  g.font = '64px "Italiana", Georgia, serif';
  wrap(g, meta.label, c.width / 2, 160, 70);
  g.fillStyle = '#9a9280'; g.font = '28px "IBM Plex Mono", monospace';
  g.fillText('S P E C I M E N   P E N D I N G', c.width / 2, 300);
  g.fillStyle = '#8a8474'; g.font = '22px "IBM Plex Mono", monospace';
  g.fillText('apparatus not yet baked', c.width / 2, 356);
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true }));
  sprite.scale.set(3.0, 1.5, 1); sprite.position.set(0, 3.2, 0);
  return sprite;
}

function wrap(g, text, x, y, lh) {
  const words = text.split(' '); let line = '', yy = y;
  for (const w of words) {
    if ((line + w).length > 18) { g.fillText(line, x, yy); line = w + ' '; yy += lh; }
    else line += w + ' ';
  }
  g.fillText(line.trim(), x, yy);
}
