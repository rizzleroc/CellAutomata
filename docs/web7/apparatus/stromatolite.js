// Capstone — Stromatolite hand specimen (~3.5 Ga).
//
// NOT an apparatus: a museum hand specimen on a felt mount under gallery
// lighting. A sawn, slightly-beveled rock slab whose polished front face shows
// wavy laminations (painted via lib.makeDynamicTexture: wavy ochre/cream/grey
// layers + a pale calcite vein). A rough darker crust runs along the top edge,
// a small 1 cm scale-bar plate sits in front, and the whole thing rests on a
// low dark museum mount/plinth.
//
// The rock is a rock — physical, named, never "brass-y". But when the
// experiment RUNS the specimen quietly comes alive, the way the living mat once
// did ~3.5 Ga: a faint translucent sheet of water lies over the microbial mat
// with shimmering teal caustics, the laminae colour breathes, photosynthetic O₂
// bubbles peel off the mat and rise (stromatolites oxygenated the early Earth),
// and the whole specimen turns very slowly on its mount. Press Stop and it
// settles back to a still, dry museum rock. progress stays 0 — this is the
// terminal specimen, not a reaction with a yield.

import * as THREE from 'three';
import { part, V, bakeliteMat, steelMat, makeDynamicTexture, labelSprite } from './lib.js';

export function build() {
  const group = new THREE.Group();
  group.name = 'stromatolite-specimen';

  // A hand specimen turns on its mount; the plinth, felt, scale-bar and label
  // do NOT. So ONLY the rock + its living-water overlay live in this sub-group,
  // and the slow `spin` is applied to it — never to the whole `group`.
  const rock = new THREE.Group();
  rock.name = 'specimen-rock';
  group.add(rock);

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
  slab.rotation.z = 0.02; rock.add(slab);

  // ── Polished front face: painted wavy laminations ─────────────────────────
  const dyn = makeDynamicTexture(512);
  const faceMat = new THREE.MeshPhysicalMaterial({
    map: dyn.tex, roughness: 0.12, metalness: 0.0, clearcoat: 0.7, clearcoatRoughness: 0.1,
  });
  const face = part(new THREE.PlaneGeometry(2.5, 2.3), faceMat, 'slab-face', V(0, 1.78, 0.31));
  face.rotation.z = 0.02; rock.add(face);

  // ── Rough darker crust along the top edge ─────────────────────────────────
  const crustMat = new THREE.MeshStandardMaterial({ color: 0x2c2218, roughness: 0.98, metalness: 0 });
  const crust = part(new THREE.BoxGeometry(2.7, 0.34, 0.9), crustMat, 'slab-crust', V(0, 3.02, -0.1));
  crust.rotation.z = 0.02;
  // jitter the crust scale to look broken/irregular
  crust.scale.set(1.0, 1.0 + Math.random() * 0.15, 1.0);
  rock.add(crust);

  // ── Pale calcite vein (a thin bright crystalline streak on the face) ──────
  const veinMat = new THREE.MeshStandardMaterial({ color: 0xe8e2d0, roughness: 0.3, metalness: 0.1, emissive: 0x161410 });
  const vein = part(new THREE.BoxGeometry(0.07, 2.2, 0.02), veinMat, 'calcite-vein', V(0.55, 1.78, 0.32));
  vein.rotation.z = 0.18; rock.add(vein);

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

  // ── Living overlay (all UNNAMED dynamic meshes — only shown while running) ──
  // These sit just in front of the polished face and breathe the mat to life.
  // The face plane normal is +z; everything here lives at z slightly > the face.
  const FACE = V(0, 1.78, 0.31);        // centre of the polished face
  const FW = 2.5, FH = 2.3;             // face plane size

  // Faint translucent water sheet over the mat, with a shimmering caustic map.
  const caustic = makeDynamicTexture(256);
  function paintCaustic(phase) {
    const ctx = caustic.ctx, S = caustic.size;
    ctx.clearRect(0, 0, S, S);
    ctx.fillStyle = 'rgba(63,224,208,0.10)';        // teal water body
    ctx.fillRect(0, 0, S, S);
    // a few drifting interference cells → rippling caustic light
    for (let i = 0; i < 5; i++) {
      const cx = (Math.sin(phase * 0.7 + i * 1.7) * 0.5 + 0.5) * S;
      const cy = (Math.cos(phase * 0.5 + i * 2.3) * 0.5 + 0.5) * S;
      const r = S * (0.18 + 0.06 * Math.sin(phase + i));
      const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, r);
      g.addColorStop(0, 'rgba(190,255,244,0.42)');
      g.addColorStop(1, 'rgba(63,224,208,0)');
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.fill();
    }
    caustic.tex.needsUpdate = true;
  }
  paintCaustic(0);
  const waterMat = new THREE.MeshPhysicalMaterial({
    color: 0x3fe0d0, emissive: 0x3fe0d0, emissiveIntensity: 0.0,
    emissiveMap: caustic.tex, map: caustic.tex,
    roughness: 0.08, metalness: 0.0, transmission: 0.85, thickness: 0.2, ior: 1.33,
    transparent: true, opacity: 0.0, depthWrite: false,
  });
  const water = new THREE.Mesh(new THREE.PlaneGeometry(FW * 0.98, FH * 0.98), waterMat);
  water.position.set(FACE.x, FACE.y, FACE.z + 0.04);
  water.rotation.z = 0.02; water.visible = false;
  rock.add(water);

  // Soft teal underwater glow that breathes with the caustics.
  const matLight = new THREE.PointLight(0x3fe0d0, 0, 4, 2);
  matLight.position.set(FACE.x, FACE.y + 0.2, FACE.z + 0.6);
  rock.add(matLight);

  // O₂ bubbles peeling off the mat and rising through the water film.
  const bubbleMat = new THREE.MeshPhysicalMaterial({
    color: 0xbffff4, emissive: 0x3fe0d0, emissiveIntensity: 0.35,
    roughness: 0.1, metalness: 0, transmission: 0.6, transparent: true, opacity: 0.0,
    depthWrite: false,
  });
  const bubbles = [];
  function seedBubble(b, atBottom) {
    b.userData.x = (Math.random() - 0.5) * FW * 0.82;
    b.userData.y = atBottom ? -FH * 0.5 : (Math.random() - 0.5) * FH;
    b.userData.amp = 0.02 + Math.random() * 0.05;     // sideways wobble
    b.userData.ph = Math.random() * Math.PI * 2;
    b.userData.v = 0.18 + Math.random() * 0.22;        // rise speed
    b.userData.s = 0.6 + Math.random() * 0.9;          // size factor
  }
  // place a bubble on the face from its mat-local (x,y) coordinates
  function placeBubble(b) {
    const wob = Math.sin(b.userData.ph + b.userData.y * 6) * b.userData.amp;
    b.position.set(FACE.x + b.userData.x + wob, FACE.y + b.userData.y, FACE.z + 0.05);
    b.scale.setScalar(b.userData.s);
  }
  for (let i = 0; i < 14; i++) {
    const b = new THREE.Mesh(new THREE.SphereGeometry(0.035, 10, 10), bubbleMat.clone());
    seedBubble(b, false);
    placeBubble(b);            // sit on the face from the start (still invisible)
    b.visible = false;
    rock.add(b); bubbles.push(b);
  }

  let running = true;
  let spin = 0;                 // accumulated slow turn (advances only when running)
  let wphase = 0;               // caustic phase (advances only when running)
  let life = 0;                 // 0..1 eased "aliveness" for fade in/out

  function calm() {
    water.visible = false;
    waterMat.opacity = 0; waterMat.emissiveIntensity = 0;
    matLight.intensity = 0;
    for (const b of bubbles) { b.visible = false; b.material.opacity = 0; }
  }

  group.userData.anim = {
    setRunning(on) { running = on; if (!on) { /* one-off settle handled in update */ } },
    getProgress() { return 0; },             // terminal specimen — no yield to report
    reset() { spin = 0; wphase = 0; life = 0; rock.rotation.y = 0; calm(); paint(0.3); paintCaustic(0); },
    update(dt, t) {
      // ease aliveness toward running state: a gentle fade-in on Run, a quick
      // fade-out on Stop so the specimen settles back to a still, dry rock.
      const target = running ? 1 : 0;
      const rate = running ? dt * 3 : dt * 22;
      life += (target - life) * Math.min(1, rate);
      if (!running && life < 0.04) life = 0;     // snap to fully calm when idle

      // very slow raking-light drift across the polished face (laminae breathe)
      const h = 0.5 + 0.45 * Math.sin(t * 0.12);
      // breathe the laminae colour subtly while alive (counts as a phenomenon)
      const breathe = 0.06 * life * Math.sin(t * 0.9);
      faceMat.color.setRGB(1 + breathe, 1 + breathe * 0.8, 1 + breathe * 0.5);
      paint(h);

      if (running) { spin += dt * 0.06; wphase += dt * 1.2; }   // slow turn + ripples
      rock.rotation.y = spin;   // ONLY the rock + its water overlay turn — mount/scale-bar/label stay put

      // water sheet: shimmering teal caustics, opacity breathing with life
      if (life > 0.002) {
        water.visible = true;
        paintCaustic(wphase);
        const shimmer = 0.5 + 0.5 * Math.sin(t * 1.6);
        waterMat.opacity = 0.22 * life;
        waterMat.emissiveIntensity = (0.25 + 0.35 * shimmer) * life;
        matLight.intensity = (0.4 + 0.5 * shimmer) * life;
      } else {
        calm();
      }

      // O₂ bubbles rising off the mat
      for (const b of bubbles) {
        if (life <= 0.002) { b.visible = false; continue; }
        b.visible = true;
        b.material.opacity = 0.75 * life;
        if (running) {
          b.userData.y += b.userData.v * dt;
          if (b.userData.y > FH * 0.5) seedBubble(b, true);
        }
        placeBubble(b);
      }
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
