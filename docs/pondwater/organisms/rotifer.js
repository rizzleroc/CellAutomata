// Rotifer (Philodina) — the "wheel animalcule". The signature find in any drop
// of pond water. A transparent metazoan you can see straight through: two
// ciliated coronal discs spin like wheels to feed, a muscular mastax grinds
// with hardened trophi, food runs through stomach and gut, a telescoping foot
// grips with two toes, and eggs ripen in the ovary. ~300 µm in life.

import { THREE, cuticle, organ, nucleus, blob, tubeBody, ciliaRing, registerOrgan, rng, TAU } from './lib.js';

export const meta = {
  id: 'rotifer',
  name: 'Rotifer',
  taxon: 'Philodina sp.',
  kingdom: 'Animalia',
  micronLength: 320,
  blurb: 'A true animal small enough to see through. Two ciliated "wheels" spin to sweep in food; a muscular jaw (the mastax) grinds it; a foot with two toes anchors it.',
  build,
};

function build() {
  const g = new THREE.Group();
  g.name = 'rotifer';
  const r = rng(42);

  // ── Body: a vase-shaped translucent trunk, tapering to the foot ──────────
  const spine = [
    new THREE.Vector3(0, 2.4, 0),
    new THREE.Vector3(0, 1.4, 0),
    new THREE.Vector3(0.05, 0.4, 0),
    new THREE.Vector3(0.0, -0.6, 0),
    new THREE.Vector3(-0.05, -1.5, 0),
    new THREE.Vector3(0, -2.2, 0),
  ];
  const bodyMat = cuticle(0xdff0f4, 0.17, { transmission: 0.6 });
  const body = tubeBody(
    spine,
    (t) => 0.9 * Math.sin(Math.min(1, t * 1.15) * Math.PI) ** 0.6 + 0.14,
    bodyMat, { tubular: 120, radial: 28 },
  );
  body.name = 'body-trunk';
  body.renderOrder = 12;
  g.add(body);
  registerOrgan(g, body, 'Trunk (cuticle)', 'A transparent cuticle over the body wall — its clarity is what lets you watch every organ work.', 0.0);

  // ── Corona: two ciliated wheels at the head that spin to feed ────────────
  const corona = new THREE.Group(); corona.name = 'corona';
  corona.position.set(0, 2.45, 0);
  for (const side of [-1, 1]) {
    const disc = new THREE.Group();
    disc.position.set(side * 0.42, 0, 0);
    const rim = new THREE.Mesh(
      new THREE.TorusGeometry(0.42, 0.08, 12, 28),
      organ(0xe7c98a, { emissive: new THREE.Color(0x3a2f14) }),
    );
    rim.rotation.x = Math.PI / 2;
    disc.add(rim);
    const cilia = ciliaRing(0.42, 34, 0.34,
      organ(0xfff4d8, { emissive: new THREE.Color(0x3a3320), transparent: true, opacity: 0.9 }),
      { axis: 'y' });
    cilia.userData.side = side;
    disc.add(cilia);
    disc.userData.cilia = cilia;
    corona.add(disc);
  }
  g.add(corona);
  registerOrgan(g, corona, 'Corona (ciliated wheels)', 'Two rings of cilia beat so fast they look like spinning wheels, drawing a vortex of food into the mouth.', 0.1);

  // ── Mastax + trophi: the muscular pharyngeal jaw with hard grinding pieces
  const mastax = new THREE.Group(); mastax.name = 'mastax';
  mastax.position.set(0, 1.55, 0);
  const bulb = blob(0.42, 0.42, 0.4, organ(0xc98a76, { emissive: new THREE.Color(0x3a1f18) }));
  mastax.add(bulb);
  // trophi: two hardened jaw pieces that clap together
  const trophiMat = nucleus(0xf2e2c0, { emissive: new THREE.Color(0x4a4230), roughness: 0.3 });
  const jawL = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.26, 0.22), trophiMat);
  const jawR = jawL.clone();
  jawL.position.set(-0.12, -0.05, 0);
  jawR.position.set(0.12, -0.05, 0);
  mastax.add(jawL, jawR);
  mastax.userData.jaws = [jawL, jawR];
  g.add(mastax);
  registerOrgan(g, mastax, 'Mastax & trophi', 'A muscular pharynx housing hardened jaws (trophi) that clap and grind captured food.', 0.35);

  // ── Stomach + intestine: the gut running down the trunk ──────────────────
  const gutPts = [
    new THREE.Vector3(0, 1.1, 0.02),
    new THREE.Vector3(0.04, 0.3, 0.05),
    new THREE.Vector3(-0.02, -0.5, 0.03),
    new THREE.Vector3(0, -1.2, 0),
  ];
  const stomach = blob(0.42, 0.55, 0.42, organ(0x8fae5a, { emissive: new THREE.Color(0x243016), transparent: true, opacity: 0.9 }));
  stomach.name = 'stomach';
  stomach.position.set(0, 0.55, 0.03);
  g.add(stomach);
  registerOrgan(g, stomach, 'Stomach', 'A sac of digestive-gland cells — food swept in by the corona is broken down here.', 0.4);

  const gut = tubeBody(gutPts, (t) => 0.16 - t * 0.05, organ(0x7c9a4a, { transparent: true, opacity: 0.85 }), { tubular: 40, radial: 12 });
  gut.name = 'intestine';
  g.add(gut);
  registerOrgan(g, gut, 'Intestine', 'The gut carries digested matter to the cloaca at the foot base.', 0.55);

  // ── Ovary with ripening eggs ─────────────────────────────────────────────
  const ovary = new THREE.Group(); ovary.name = 'ovary';
  ovary.position.set(-0.3, -0.2, 0.2);
  const eggs = [];
  for (let i = 0; i < 4; i++) {
    const e = blob(0.16 + r() * 0.05, 0.14, 0.14, nucleus(0xbfe0ff, { emissive: new THREE.Color(0x1e2c44) }));
    e.position.set((r() - 0.5) * 0.3, (r() - 0.5) * 0.5, (r() - 0.5) * 0.2);
    eggs.push(e); ovary.add(e);
  }
  g.add(ovary);
  registerOrgan(g, ovary, 'Ovary & eggs', 'Rotifers you find are almost all females — eggs ripen here and hatch as clones (parthenogenesis).', 0.6);

  // ── Foot + two toes: the telescoping anchor ──────────────────────────────
  const foot = new THREE.Group(); foot.name = 'foot';
  foot.position.set(0, -2.2, 0);
  const stalk = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.16, 0.6, 12), bodyMat.clone());
  stalk.position.y = -0.3;
  foot.add(stalk);
  for (const s of [-1, 1]) {
    const toe = new THREE.Mesh(new THREE.ConeGeometry(0.06, 0.45, 8), organ(0xd8c9a0, { emissive: new THREE.Color(0x2a2416) }));
    toe.position.set(s * 0.1, -0.75, 0);
    toe.rotation.z = s * 0.2;
    toe.rotation.x = Math.PI;
    foot.add(toe);
  }
  g.add(foot);
  registerOrgan(g, foot, 'Foot & toes', 'A telescoping foot ending in two toes with cement glands — it grips the substrate while the corona feeds.', 0.25);

  g.userData.focusRadius = 7.2;

  let running = true, phase = 0;
  g.userData.anim = {
    setRunning: (v) => { running = v; },
    getProgress: () => (phase * 0.12) % 1,
    reset: () => { phase = 0; },
    update: (dt, t) => {
      if (running) phase += dt;
      // corona wheels spin + cilia beat
      corona.children.forEach((disc, i) => {
        const dir = i === 0 ? 1 : -1;
        disc.rotation.z = phase * 3 * dir;
        disc.userData.cilia.userData.beat(phase, 0.6);
      });
      // mastax jaws clap
      const clap = Math.max(0, Math.sin(phase * 5)) * 0.09;
      mastax.userData.jaws[0].position.x = -0.06 - clap;
      mastax.userData.jaws[1].position.x = 0.06 + clap;
      // stomach churns
      stomach.scale.setScalar(1 + Math.sin(phase * 2.2) * 0.05);
      // whole body inch/telescoping bend + foot probe
      g.rotation.z = Math.sin(phase * 0.8) * 0.06;
      foot.rotation.z = Math.sin(phase * 1.4 + 1) * 0.12;
      // eggs jostle
      eggs.forEach((e, i) => { e.scale.setScalar(1 + Math.sin(phase * 1.6 + i) * 0.04); });
    },
  };
  return g;
}
