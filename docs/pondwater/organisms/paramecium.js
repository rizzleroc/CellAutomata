// Paramecium — a ciliate protist, the "slipper animalcule". A single giant
// cell: coated in cilia it rows with, an oral groove that sweeps food into a
// gullet, two nuclei, pulsing contractile vacuoles that bail out water, and
// food vacuoles circling on the cytoplasmic streaming. ~120 µm in life.

import { THREE, cuticle, organ, nucleus, blob, ciliaCoat, registerOrgan, rng, TAU } from './lib.js';

export const meta = {
  id: 'paramecium',
  name: 'Paramecium',
  taxon: 'Paramecium caudatum',
  kingdom: 'Protista',
  micronLength: 130,
  blurb: 'One enormous cell. Cilia row it through the water; an oral groove feeds a gullet; contractile vacuoles pump out the water that floods in.',
  build,
};

function build() {
  const g = new THREE.Group();
  g.name = 'paramecium';
  const r = rng(21);

  // ── Pellicle (the slipper body): an asymmetric ellipsoid, tail end tapered
  const bodyGeo = new THREE.SphereGeometry(1, 40, 28);
  bodyGeo.scale(2.2, 0.85, 0.85);
  // taper one end into the "caudatum" tail and flatten the oral side
  const p = bodyGeo.attributes.position;
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i);
    const taper = x < 0 ? 1 + x * 0.18 : 1 - x * 0.05;
    p.setY(i, p.getY(i) * Math.max(0.35, taper));
    p.setZ(i, p.getZ(i) * Math.max(0.35, taper));
  }
  bodyGeo.computeVertexNormals();
  const body = new THREE.Mesh(bodyGeo, cuticle(0xd6f0e2, 0.20, { transmission: 0.55 }));
  body.name = 'pellicle';
  body.renderOrder = 10;
  g.add(body);
  registerOrgan(g, body, 'Pellicle', 'A stiff-but-flexible protein skin that holds the slipper shape and anchors every cilium.', 0.0);

  // ── Cilia coat: the rows that row it forward ─────────────────────────────
  const coat = ciliaCoat(2.2, 0.85, 0.85, 900, 0.22,
    organ(0xeafff6, { emissive: new THREE.Color(0x1c2a26), transparent: true, opacity: 0.85, roughness: 0.4 }));
  coat.name = 'cilia';
  g.add(coat);
  registerOrgan(g, coat, 'Cilia', 'Thousands of hair-like cilia beat in metachronal waves, rowing the cell and sweeping food to the mouth.', 0.15);

  // ── Oral groove + gullet: a funnel indenting one flank ───────────────────
  const groove = new THREE.Mesh(
    new THREE.CylinderGeometry(0.05, 0.32, 1.1, 20, 1, true),
    organ(0x6f9b8c, { side: THREE.DoubleSide, transparent: true, opacity: 0.7 }),
  );
  groove.name = 'oral-groove';
  groove.position.set(0.2, -0.45, 0.35);
  groove.rotation.set(0.5, 0, -0.3);
  g.add(groove);
  registerOrgan(g, groove, 'Oral groove & gullet', 'A ciliated funnel that sweeps bacteria into the cell, pinching them off as food vacuoles.', 0.3);

  // ── Macronucleus (big, kidney-shaped) + micronucleus (small) ─────────────
  const macro = blob(0.55, 0.4, 0.4, nucleus(0xb69bff, { emissive: new THREE.Color(0x2e2350) }));
  macro.name = 'macronucleus';
  macro.position.set(0.1, 0, 0);
  g.add(macro);
  registerOrgan(g, macro, 'Macronucleus', 'The large working nucleus — runs the cell\'s day-to-day housekeeping and metabolism.', 0.45);

  const micro = blob(0.16, 0.16, 0.16, nucleus(0x8fb8ff, { emissive: new THREE.Color(0x1a2a55) }));
  micro.name = 'micronucleus';
  micro.position.set(0.35, -0.12, 0.08);
  g.add(micro);
  registerOrgan(g, micro, 'Micronucleus', 'The germline nucleus, swapped during conjugation — the cell\'s reproductive archive.', 0.6);

  // ── Contractile vacuoles: two star-shaped pumps that pulse ───────────────
  const cvMat = cuticle(0x9fe8ff, 0.4, { transmission: 0.7, roughness: 0.1 });
  const cv1 = blob(0.3, 0.3, 0.3, cvMat); cv1.name = 'contractile-vacuole-anterior';
  cv1.position.set(-1.1, 0.35, 0);
  const cv2 = blob(0.3, 0.3, 0.3, cvMat.clone()); cv2.name = 'contractile-vacuole-posterior';
  cv2.position.set(1.1, 0.35, 0);
  g.add(cv1, cv2);
  registerOrgan(g, cv1, 'Contractile vacuoles', 'Osmotic bilge pumps: they swell with the water constantly leaking in, then contract to expel it.', 0.35);

  // ── Food vacuoles: pellets circling on the cytoplasmic stream ────────────
  const fvGroup = new THREE.Group(); fvGroup.name = 'food-vacuoles';
  const fvs = [];
  for (let i = 0; i < 7; i++) {
    const fv = blob(0.12 + r() * 0.08, 0.12, 0.12, organ(0x7a5a3a, { emissive: new THREE.Color(0x1a1208) }));
    const a = r() * TAU;
    fvs.push({ mesh: fv, a, rad: 0.9 + r() * 0.5, sp: 0.3 + r() * 0.3, yz: r() * TAU });
    fvGroup.add(fv);
  }
  g.add(fvGroup);
  registerOrgan(g, fvGroup, 'Food vacuoles', 'Ingested bacteria digest inside these travelling pockets as cytoplasmic streaming carries them around the cell.', 0.5);

  g.userData.focusRadius = 5.6;

  let running = true, phase = 0;
  g.userData.anim = {
    setRunning: (v) => { running = v; },
    getProgress: () => (phase * 0.1) % 1,
    reset: () => { phase = 0; },
    update: (dt, t) => {
      if (running) phase += dt;
      coat.userData.beat(phase);
      // whole-cell spiral glide + gentle body flex
      g.rotation.x = phase * 0.4;
      body.rotation.z = Math.sin(phase * 1.3) * 0.04;
      // contractile vacuoles fill then snap (systole) out of phase
      const s1 = 0.5 + 0.5 * Math.abs(Math.sin(phase * 0.9));
      const s2 = 0.5 + 0.5 * Math.abs(Math.sin(phase * 0.9 + 1.6));
      cv1.scale.setScalar(0.5 + s1);
      cv2.scale.setScalar(0.5 + s2);
      // food vacuoles stream in a loop
      for (const f of fvs) {
        const a = f.a + phase * f.sp;
        f.mesh.position.set(Math.cos(a) * 1.6, Math.sin(a) * 0.5, Math.sin(a + f.yz) * 0.5);
      }
      // micronucleus nestles against macro
      macro.scale.setScalar(1 + Math.sin(phase * 1.1) * 0.03);
    },
  };
  return g;
}
