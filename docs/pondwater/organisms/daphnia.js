// Daphnia — the water flea. The largest resident of the drop, and a glass
// animal: through its transparent carapace you can watch a real heart beat, the
// gut peristalse, and eggs develop in the brood pouch. A single big compound
// eye twitches; branched antennae row it through the water in hops. ~1.5 mm.

import { THREE, cuticle, organ, nucleus, blob, registerOrgan, rng, TAU } from './lib.js';

export const meta = {
  id: 'daphnia',
  name: 'Daphnia',
  taxon: 'Daphnia pulex',
  kingdom: 'Animalia',
  micronLength: 1500,
  blurb: 'The water flea — a transparent crustacean. Through its shell you can watch a real heart beat, the gut churn, and eggs grow in the brood pouch.',
  build,
};

function build() {
  const g = new THREE.Group();
  g.name = 'daphnia';
  const r = rng(105);

  // ── Carapace: a rounded transparent shell with a tail spine ──────────────
  const shellGeo = new THREE.SphereGeometry(1.6, 40, 28);
  shellGeo.scale(1.15, 1.25, 0.75);
  const p = shellGeo.attributes.position;
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), y = p.getY(i);
    // draw the rear-bottom into a point (the shell's ventral gape + tail)
    if (x < 0 && y < 0) { p.setX(i, x * (1 + Math.abs(y) * 0.25)); }
  }
  shellGeo.computeVertexNormals();
  const shell = new THREE.Mesh(shellGeo, cuticle(0xe6f2f4, 0.13, { transmission: 0.7, roughness: 0.18 }));
  shell.name = 'carapace';
  shell.renderOrder = 14;
  g.add(shell);
  registerOrgan(g, shell, 'Carapace', 'A transparent bivalved shell of chitin — its clarity is why Daphnia is a classroom window into a living body.', 0.0);

  const tail = new THREE.Mesh(new THREE.ConeGeometry(0.08, 1.1, 10), cuticle(0xe6f2f4, 0.3));
  tail.name = 'tail-spine';
  tail.position.set(-1.7, -0.9, 0);
  tail.rotation.z = Math.PI / 2 + 0.5;
  g.add(tail);
  registerOrgan(g, tail, 'Tail spine', 'A long apical spine — a defensive deterrent that also helps keep the animal upright.', 0.1);

  // ── Compound eye: a single large dark eye that twitches ──────────────────
  const eye = new THREE.Mesh(new THREE.SphereGeometry(0.34, 20, 16), nucleus(0x101014, { emissive: new THREE.Color(0x05050a), roughness: 0.2, metalness: 0.3 }));
  eye.name = 'compound-eye';
  eye.position.set(1.2, 0.55, 0);
  g.add(eye);
  registerOrgan(g, eye, 'Compound eye', 'A single fused compound eye, rotated by tiny muscles — it flicks toward light to steer the animal.', 0.25);

  // small second (naupliar) ocellus below it
  const ocellus = new THREE.Mesh(new THREE.SphereGeometry(0.1, 10, 8), nucleus(0x101014));
  ocellus.position.set(1.15, 0.2, 0);
  g.add(ocellus);

  // ── Heart: a small chamber above the gut that beats fast ─────────────────
  const heart = blob(0.28, 0.32, 0.28, organ(0xd05a4a, { emissive: new THREE.Color(0x4a1410) }));
  heart.name = 'heart';
  heart.position.set(0.5, 0.7, 0.1);
  g.add(heart);
  registerOrgan(g, heart, 'Heart', 'A single muscular chamber on the back that beats 3–6 times a second — visibly, right through the shell.', 0.3);

  // ── Gut: a curved tube from mouth to hindgut ─────────────────────────────
  const gutPts = [
    new THREE.Vector3(1.15, 0.1, 0),
    new THREE.Vector3(0.5, -0.2, 0),
    new THREE.Vector3(-0.2, 0.1, 0),
    new THREE.Vector3(-0.9, -0.2, 0),
    new THREE.Vector3(-1.4, -0.6, 0),
  ];
  const gut = new THREE.Mesh(
    new THREE.TubeGeometry(new THREE.CatmullRomCurve3(gutPts), 60, 0.16, 12, false),
    organ(0x7a5a2a, { emissive: new THREE.Color(0x1a1206), transparent: true, opacity: 0.92 }),
  );
  gut.name = 'gut';
  g.add(gut);
  registerOrgan(g, gut, 'Gut', 'A looping digestive tract, usually packed dark green with the algae the animal filter-feeds.', 0.4);

  // ── Brood pouch: eggs/embryos developing under the dorsal shell ──────────
  const brood = new THREE.Group(); brood.name = 'brood-pouch';
  brood.position.set(-0.5, 0.5, 0);
  const eggs = [];
  for (let i = 0; i < 6; i++) {
    const e = blob(0.22, 0.22, 0.2, nucleus(0xcfe6b0, { emissive: new THREE.Color(0x24301a) }));
    e.position.set((r() - 0.5) * 0.9, (r() - 0.5) * 0.5, (r() - 0.5) * 0.4);
    eggs.push(e); brood.add(e);
  }
  g.add(brood);
  registerOrgan(g, brood, 'Brood pouch & eggs', 'Embryos develop in a chamber under the back of the shell — often clones, produced without a male.', 0.45);

  // ── Antennae: large branched second antennae that row in hops ────────────
  const antennae = [];
  for (const side of [-1, 1]) {
    const ant = new THREE.Group();
    ant.position.set(1.3, 0.3, side * 0.2);
    for (let b = 0; b < 4; b++) {
      const seta = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.05, 1.5, 6), organ(0xd8e2e0, { transparent: true, opacity: 0.8 }));
      seta.position.set(0.7, 0, 0);
      seta.rotation.z = -Math.PI / 2;
      seta.rotation.y = (b - 1.5) * 0.25;
      const holder = new THREE.Group(); holder.add(seta); holder.rotation.y = (b - 1.5) * 0.2;
      ant.add(holder);
    }
    ant.userData.side = side;
    antennae.push(ant); g.add(ant);
  }
  const antProxy = antennae[0];
  registerOrgan(g, antProxy, 'Antennae (rowing)', 'Big branched second antennae sweep down like oars — each stroke is the "flea" hop that names the animal.', 0.2);

  g.userData.focusRadius = 8.4;

  let running = true, phase = 0;
  g.userData.anim = {
    setRunning: (v) => { running = v; },
    getProgress: () => (phase * 0.1) % 1,
    reset: () => { phase = 0; },
    update: (dt, t) => {
      if (running) phase += dt;
      // heart: fast asymmetric beat (systole snap)
      const beat = Math.pow(Math.max(0, Math.sin(phase * 9)), 0.4);
      heart.scale.set(1 + beat * 0.35, 1 - beat * 0.15, 1 + beat * 0.35);
      // gut peristalsis (ripple the tube radius via scale pulses)
      gut.scale.y = 1 + Math.sin(phase * 3) * 0.04;
      // eye twitch
      eye.rotation.z = Math.sin(phase * 2.5) * 0.3;
      // antennae row in synchronised power strokes → the hop
      const stroke = Math.sin(phase * 3);
      for (const ant of antennae) {
        ant.rotation.z = -0.3 + stroke * 0.7;
      }
      // the hop: body rises on the power stroke
      g.position.y += 0; // world drift handled by the field; local bob only
      g.rotation.z = Math.sin(phase * 3) * 0.05;
      // brood eggs jostle
      eggs.forEach((e, i) => e.scale.setScalar(1 + Math.sin(phase * 1.5 + i) * 0.05));
    },
  };
  return g;
}
