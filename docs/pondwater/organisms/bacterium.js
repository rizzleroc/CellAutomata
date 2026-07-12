// Bacillus — a rod bacterium. The floor of the microscope's living hierarchy:
// no nucleus, just a nucleoid of coiled DNA, ribosome granulation, and a
// rotary flagellum that whips it forward. Modelled ~2 µm long in life.

import { THREE, cuticle, organ, nucleus, blob, registerOrgan, rng, TAU } from './lib.js';

export const meta = {
  id: 'bacterium',
  name: 'Bacillus',
  taxon: 'Bacillus sp.',
  kingdom: 'Bacteria',
  micronLength: 2.4,
  blurb: 'A prokaryote — no nucleus, no organelles. DNA lies loose in the cytoplasm and a rotary flagellum drives it.',
  build,
};

function build() {
  const g = new THREE.Group();
  g.name = 'bacterium';
  const r = rng(7);

  // ── Cell wall + membrane: a capsule (rod with hemispherical caps) ─────────
  const wall = new THREE.Mesh(
    new THREE.CapsuleGeometry(0.42, 1.5, 12, 24),
    cuticle(0xbfe9c8, 0.30, { transmission: 0.5, roughness: 0.25 }),
  );
  wall.name = 'cell-wall';
  wall.rotation.z = Math.PI / 2;
  wall.renderOrder = 10;
  g.add(wall);
  registerOrgan(g, wall, 'Cell wall & membrane', 'Peptidoglycan wall over the plasma membrane — holds turgor and shape.', 0.0);

  // ── Cytoplasm: a faint inner fill so the granulation reads as suspended ───
  const cyto = new THREE.Mesh(
    new THREE.CapsuleGeometry(0.36, 1.45, 10, 20),
    cuticle(0xa9dcb6, 0.16, { transmission: 0.2 }),
  );
  cyto.rotation.z = Math.PI / 2;
  cyto.renderOrder = 6;
  g.add(cyto);

  // ── Nucleoid: coiled chromosome, a loose supercoiled tangle ──────────────
  const nucGroup = new THREE.Group();
  nucGroup.name = 'nucleoid';
  const pts = [];
  for (let i = 0; i <= 60; i++) {
    const t = i / 60;
    const x = (t - 0.5) * 1.1;
    pts.push(new THREE.Vector3(
      x,
      Math.sin(t * TAU * 3) * 0.12,
      Math.cos(t * TAU * 3.3) * 0.12,
    ));
  }
  const dna = new THREE.Mesh(
    new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 90, 0.03, 6, false),
    nucleus(0x7fa8ff, { emissive: new THREE.Color(0x2a3a7a) }),
  );
  nucGroup.add(dna);
  g.add(nucGroup);
  registerOrgan(g, nucGroup, 'Nucleoid (DNA)', 'A single circular chromosome, supercoiled and free in the cytoplasm — no membrane.', 0.5);

  // ── Ribosomes: fine granulation, revealed only at the deepest zoom ───────
  const riboMat = nucleus(0xffe0a0, { emissive: new THREE.Color(0x4a3410) });
  const ribo = new THREE.InstancedMesh(new THREE.SphereGeometry(0.03, 6, 6), riboMat, 220);
  const d = new THREE.Object3D();
  for (let i = 0; i < 220; i++) {
    d.position.set((r() - 0.5) * 1.4, (r() - 0.5) * 0.6, (r() - 0.5) * 0.6);
    d.updateMatrix();
    ribo.setMatrixAt(i, d.matrix);
  }
  ribo.name = 'ribosomes';
  g.add(ribo);
  registerOrgan(g, ribo, 'Ribosomes', 'Tens of thousands of protein factories give the cytoplasm its granular texture.', 0.85);

  // ── Flagellum: a helical filament off one pole ───────────────────────────
  const fpts = [];
  for (let i = 0; i <= 40; i++) {
    const t = i / 40;
    fpts.push(new THREE.Vector3(
      -0.95 - t * 1.6,
      Math.sin(t * TAU * 4) * 0.18 * t,
      Math.cos(t * TAU * 4) * 0.18 * t,
    ));
  }
  const flag = new THREE.Mesh(
    new THREE.TubeGeometry(new THREE.CatmullRomCurve3(fpts), 80, 0.02, 5, false),
    organ(0xdfeee6, { emissive: new THREE.Color(0x111511), roughness: 0.4 }),
  );
  flag.name = 'flagellum';
  g.add(flag);
  registerOrgan(g, flag, 'Flagellum', 'A rotary protein propeller, spun by a molecular motor in the wall, drives the cell in a run-and-tumble path.', 0.2);

  g.userData.focusRadius = 3.4;

  let running = true, phase = 0;
  g.userData.anim = {
    setRunning: (v) => { running = v; },
    getProgress: () => (phase % TAU) / TAU,
    reset: () => { phase = 0; },
    update: (dt, t) => {
      if (running) phase += dt;
      // flagellum rotates (whole rod counter-rotates a hair)
      flag.rotation.x = phase * 8;
      g.rotation.x = Math.sin(phase * 0.6) * 0.05;
      // gentle nucleoid breathing
      const s = 1 + Math.sin(phase * 1.5) * 0.03;
      nucGroup.scale.setScalar(s);
    },
  };
  return g;
}
