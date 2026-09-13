// Tardigrade — the water bear. A plump, translucent eight-legged micro-animal
// that lumbers over detritus. Four body segments, eight stubby legs each tipped
// with claws, a buccal tube and piercing stylets that stab algae, a wide gut,
// and a dorsal ovary. Famous for surviving desiccation, vacuum, and radiation.
// ~400 µm in life.

import { THREE, cuticle, organ, nucleus, blob, surfaceNormalMap, registerOrgan, rng, TAU } from './lib.js';

export const meta = {
  id: 'tardigrade',
  name: 'Tardigrade',
  taxon: 'Hypsibius sp.',
  kingdom: 'Animalia',
  micronLength: 420,
  locomotion: 'crawl',        // a very slow eight-legged bumble, with pauses
  blurb: 'The "water bear" — eight clawed legs, a plump translucent body, and stylets that pierce algae. It can dry out completely and come back to life.',
  build,
};

function build() {
  const g = new THREE.Group();
  g.name = 'tardigrade';
  const r = rng(84);

  // ── Body: four fused segments, a fat tapering barrel ─────────────────────
  const bodyGeo = new THREE.CapsuleGeometry(0.85, 1.9, 24, 44);
  bodyGeo.rotateZ(Math.PI / 2);
  // taper the rear + swell the middle for the segmented "gummy bear" look
  const p = bodyGeo.attributes.position;
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i);
    const seg = 1 + Math.cos(x * 3.5) * 0.07;       // segmentation ripples
    const taper = x < -0.9 ? 1 + (x + 0.9) * 0.35 : 1;
    p.setY(i, p.getY(i) * seg * Math.max(0.4, taper));
    p.setZ(i, p.getZ(i) * seg * Math.max(0.4, taper));
  }
  bodyGeo.computeVertexNormals();
  // gummy, subsurface-warm cuticle: high thickness + amber attenuation makes
  // the plump body glow from within and the green gut show through it
  const body = new THREE.Mesh(bodyGeo, cuticle(0xf3ead2, 0.24, {
    transmission: 0.55, thickness: 1.8,
    attenuationColor: new THREE.Color(0xdcae74), attenuationDistance: 1.3,
    normal: surfaceNormalMap({ freq: 10, strength: 0.7, kind: 'segments', seed: 8 }),
    rim: { color: 0xffe4b8, power: 2.7, intensity: 0.95 },
  }));
  body.material.normalScale = new THREE.Vector2(0.4, 0.4);
  body.name = 'body';
  body.renderOrder = 12;
  g.add(body);
  registerOrgan(g, body, 'Cuticle (4 segments)', 'A tough chitinous cuticle in four segments, moulted as the animal grows — translucent enough to see the gut through.', 0.0);

  // ── Eight legs, in four pairs: chubby lobopods ending in claws ────────────
  const legs = [];
  const legMat = cuticle(0xecd9b4, 0.4, {
    transmission: 0.28, thickness: 1.0, normal: false,
    attenuationColor: new THREE.Color(0xd8b982), attenuationDistance: 0.8,
    rim: { color: 0xffe6bc, power: 2.6, intensity: 0.8 },
  });
  const clawMat = nucleus(0x6a5030, { emissive: new THREE.Color(0x1a1206), roughness: 0.4 });
  for (let pair = 0; pair < 4; pair++) {
    const px = 1.1 - pair * 0.62;
    for (const side of [-1, 1]) {
      const leg = new THREE.Group();
      // a plump capsule lobopod, fatter at the base, tapering to the foot
      const seg = new THREE.Mesh(new THREE.CapsuleGeometry(0.2, 0.4, 12, 20), legMat.clone());
      seg.name = `leg-${pair}-${side < 0 ? 'L' : 'R'}`;
      seg.scale.set(1, 1, 1);
      seg.position.y = -0.32;
      // pinch the foot end for a stubby-toe silhouette
      const lp = seg.geometry.attributes.position;
      for (let i = 0; i < lp.count; i++) {
        const y = lp.getY(i);
        if (y < -0.2) { lp.setX(i, lp.getX(i) * 0.7); lp.setZ(i, lp.getZ(i) * 0.7); }
      }
      seg.geometry.computeVertexNormals();
      leg.add(seg);
      // claw cluster at the foot
      for (let c = 0; c < 3; c++) {
        const claw = new THREE.Mesh(new THREE.ConeGeometry(0.045, 0.24, 8), clawMat);
        claw.position.set((c - 1) * 0.08, -0.66, 0);
        claw.rotation.x = Math.PI + 0.2;
        claw.rotation.z = (c - 1) * 0.28;
        leg.add(claw);
      }
      leg.position.set(px, -0.55, side * 0.55);
      leg.userData = { side, pair, phase: pair * 0.7 + (side < 0 ? Math.PI : 0) };
      legs.push(leg);
      g.add(leg);
    }
  }
  const legGroupProxy = legs[0];
  registerOrgan(g, legGroupProxy, 'Legs & claws', 'Four pairs of stubby lobopod legs, each tipped with a cluster of claws for gripping moss and detritus.', 0.2);

  // ── Head: buccal tube + piercing stylets ─────────────────────────────────
  const head = new THREE.Group(); head.name = 'buccal-apparatus';
  head.position.set(1.45, 0, 0);
  const buccal = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.13, 0.55, 16), organ(0xcf9d84, { emissive: new THREE.Color(0x3a1f18), transmission: 0.2 }));
  buccal.name = 'buccal-tube';
  buccal.rotation.z = Math.PI / 2;
  buccal.position.x = 0.2;
  head.add(buccal);
  const stylets = [];
  for (const s of [-1, 1]) {
    const st = new THREE.Mesh(new THREE.ConeGeometry(0.03, 0.4, 8), nucleus(0xf2e2c0, { emissive: new THREE.Color(0x4a4230) }));
    st.rotation.z = -Math.PI / 2;
    st.position.set(0.42, s * 0.05, 0);
    stylets.push(st); head.add(st);
  }
  head.userData.stylets = stylets;
  // sucking pharynx bulb behind the mouth
  const pharynx = blob(0.28, 0.28, 0.28, organ(0xc98a76, { emissive: new THREE.Color(0x3a1f18), transmission: 0.15 }));
  pharynx.position.x = -0.25;
  head.add(pharynx);
  head.userData.pharynx = pharynx;
  g.add(head);
  registerOrgan(g, head, 'Stylets & sucking pharynx', 'A pair of needle-like stylets pierce plant and algal cells; the muscular pharynx then sucks out the contents.', 0.4);

  // ── Gut: a broad tube of green-brown food through the mid-body ────────────
  const gut = new THREE.Mesh(new THREE.CapsuleGeometry(0.34, 1.5, 14, 24), organ(0x6f7a3a, { emissive: new THREE.Color(0x1a2010), transparent: true, opacity: 0.92, transmission: 0.2 }));
  gut.rotation.z = Math.PI / 2;
  gut.position.x = -0.1;
  gut.name = 'midgut';
  g.add(gut);
  registerOrgan(g, gut, 'Midgut', 'A wide gut packed with ingested algae — its colour is often the most obvious thing inside a live water bear.', 0.45);

  // ── Ovary with eggs, dorsal to the gut ───────────────────────────────────
  const ovary = new THREE.Group(); ovary.name = 'ovary';
  ovary.position.set(-0.6, 0.45, 0);
  for (let i = 0; i < 5; i++) {
    const e = blob(0.16, 0.16, 0.16, nucleus(0xbfe0ff, { emissive: new THREE.Color(0x1e2c44) }));
    e.position.set((r() - 0.5) * 0.7, (r() - 0.5) * 0.25, (r() - 0.5) * 0.5);
    ovary.add(e);
  }
  g.add(ovary);
  registerOrgan(g, ovary, 'Ovary & eggs', 'Eggs mature in a single dorsal ovary; many species lay them into the shed cuticle.', 0.6);

  g.userData.focusRadius = 6.4;

  let running = true, phase = 0;
  g.userData.anim = {
    setRunning: (v) => { running = v; },
    getProgress: () => (phase * 0.15) % 1,
    reset: () => { phase = 0; },
    update: (dt, t) => {
      if (running) phase += dt;
      // lumbering gait — each leg lifts and swings on its phase
      for (const leg of legs) {
        const ph = phase * 3 + leg.userData.phase;
        leg.rotation.z = Math.sin(ph) * 0.4;
        leg.position.y = -0.55 + Math.max(0, Math.sin(ph)) * 0.12;
      }
      // body trundles: a slow up-down bob + faint segmentation flex
      body.rotation.z = Math.sin(phase * 1.5) * 0.03;
      g.rotation.y = Math.sin(phase * 0.5) * 0.05;
      // stylets jab, pharynx pumps
      const jab = Math.max(0, Math.sin(phase * 4)) * 0.12;
      head.userData.stylets.forEach((s) => { s.position.x = 0.42 + jab; });
      head.userData.pharynx.scale.setScalar(1 + Math.max(0, Math.sin(phase * 4 - 0.5)) * 0.2);
    },
  };
  return g;
}
