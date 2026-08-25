// Paramecium — a ciliate protist, the "slipper animalcule". A single giant
// cell: coated in cilia it rows with, an oral groove that sweeps food into a
// gullet, two nuclei, pulsing contractile vacuoles that bail out water, and
// food vacuoles circling on the cytoplasmic streaming. ~120 µm in life.

import { THREE, cuticle, organ, nucleus, blob, ciliaCoat, granuleField, refractileMaterial, surfaceNormalMap, registerOrgan, rng, TAU } from './lib.js';

export const meta = {
  id: 'paramecium',
  name: 'Paramecium',
  taxon: 'Paramecium caudatum',
  kingdom: 'Protista',
  micronLength: 130,
  locomotion: 'ciliate-helix',   // smooth spiral glide (rolls on its long axis) + avoiding reactions
  blurb: 'One enormous cell. Cilia row it through the water; an oral groove feeds a gullet; contractile vacuoles pump out the water that floods in.',
  build,
};

function build() {
  const g = new THREE.Group();
  g.name = 'paramecium';
  const r = rng(21);

  // ── Pellicle (the slipper body): an asymmetric ellipsoid, tail end tapered
  const bodyGeo = new THREE.SphereGeometry(1, 56, 40);
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
  // ridged pellicle: the regular rows of alveoli every cilium sprouts from
  const body = new THREE.Mesh(bodyGeo, cuticle(0xd6f0e2, 0.19, {
    transmission: 0.66, thickness: 1.1,
    normal: surfaceNormalMap({ freq: 26, strength: 0.9, kind: 'ridges', seed: 5 }),
    rim: { color: 0xd8fff0, power: 2.6, intensity: 0.6 },
  }));
  body.material.normalScale = new THREE.Vector2(0.5, 0.5);
  body.name = 'pellicle';
  body.renderOrder = 10;
  g.add(body);
  registerOrgan(g, body, 'Pellicle', 'A stiff-but-flexible protein skin that holds the slipper shape and anchors every cilium.', 0.0);

  // ── Endoplasm: the dense field of bright refractile granules (food
  //    vacuoles, storage bodies, crystals) that scatter the condenser light —
  //    the galaxy of white points inside a live protist ─────────────────────
  const endo = granuleField(2.0, 0.72, 0.72, 520, 0.032, refractileMaterial(0xdfeeff), { seed: 77 });
  endo.name = 'endoplasm';
  g.add(endo);

  // ── Cilia coat: a soft fine fringe (real cilia are a faint shimmer at the
  //    rim, not a bright spiky halo) ─────────────────────────────────────────
  const coat = ciliaCoat(2.2, 0.85, 0.85, 1100, 0.13,
    organ(0xdfeee6, { emissive: new THREE.Color(0x0e120f), transparent: true, opacity: 0.4, roughness: 0.5, rim: false }));
  coat.name = 'cilia';
  g.add(coat);
  registerOrgan(g, coat, 'Cilia', 'Thousands of hair-like cilia beat in metachronal waves, rowing the cell and sweeping food to the mouth.', 0.15);

  // ── Oral groove + gullet: a funnel indenting one flank ───────────────────
  const groove = new THREE.Mesh(
    new THREE.CylinderGeometry(0.05, 0.34, 1.1, 28, 1, true),
    organ(0x6f9b8c, { side: THREE.DoubleSide, transparent: true, opacity: 0.65, transmission: 0.3 }),
  );
  groove.name = 'oral-groove';
  groove.position.set(0.2, -0.45, 0.35);
  groove.rotation.set(0.5, 0, -0.3);
  g.add(groove);
  registerOrgan(g, groove, 'Oral groove & gullet', 'A ciliated funnel that sweeps bacteria into the cell, pinching them off as food vacuoles.', 0.3);

  // ── Macronucleus (big, kidney-shaped) + micronucleus (small) ─────────────
  // A soft, dim blue-grey oval in life — not a glowing gem.
  const macro = blob(0.55, 0.4, 0.4, nucleus(0x9aa6c8, { emissive: new THREE.Color(0x1a1e2e) }));
  macro.name = 'macronucleus';
  macro.position.set(0.1, 0, 0);
  g.add(macro);
  registerOrgan(g, macro, 'Macronucleus', 'The large working nucleus — runs the cell\'s day-to-day housekeeping and metabolism.', 0.45);

  const micro = blob(0.16, 0.16, 0.16, nucleus(0x8f9fbf, { emissive: new THREE.Color(0x141a2a) }));
  micro.name = 'micronucleus';
  micro.position.set(0.35, -0.12, 0.08);
  g.add(micro);
  registerOrgan(g, micro, 'Micronucleus', 'The germline nucleus, swapped during conjugation — the cell\'s reproductive archive.', 0.6);

  // ── Contractile vacuoles: two refractive pumps that pulse ────────────────
  // High transmission + a low ior mismatch makes them read as watery blisters
  // that bend the light behind them, the way real pulsing vacuoles glint.
  const cvMat = cuticle(0x9fe8ff, 0.32, {
    transmission: 0.92, roughness: 0.05, thickness: 0.5, ior: 1.42,
    iridescence: 0.5, iridescenceIOR: 1.3, iridescenceThicknessRange: [120, 380],
    normal: false, rim: { color: 0xd6f6ff, power: 2, intensity: 0.7 },
  });
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
    const fv = blob(0.12 + r() * 0.08, 0.12, 0.12, organ(0x7a5a3a, { emissive: new THREE.Color(0x1a1208), transmission: 0.25 }));
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
