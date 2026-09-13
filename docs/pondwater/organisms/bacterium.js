// Bacillus — a rod bacterium. The floor of the microscope's living hierarchy:
// no nucleus, just a nucleoid of coiled DNA, ribosome granulation, and a
// rotary flagellum that whips it forward. Modelled ~2 µm long in life.

import { THREE, cuticle, organ, nucleus, granuleField, helixFilament, registerOrgan, rng, TAU } from './lib.js';

export const meta = {
  id: 'bacterium',
  name: 'Bacillus',
  taxon: 'Bacillus sp.',
  kingdom: 'Bacteria',
  micronLength: 2.4,
  locomotion: 'run-tumble',   // flagellum-driven runs + abrupt tumbles + Brownian quiver
  blurb: 'A prokaryote — no nucleus, no organelles. DNA lies loose in the cytoplasm and a rotary flagellum drives it.',
  build,
};

function build() {
  const g = new THREE.Group();
  g.name = 'bacterium';
  const r = rng(7);

  // ── Cell wall + membrane: a glassy capsule (rod with hemispherical caps) ──
  // Denser tessellation + the shared cuticle grammar → real transmission, a
  // wet clearcoat film, and a Fresnel edge glow so the rim lights up in the
  // dark field the way a live bacillus does under a condenser.
  const wall = new THREE.Mesh(
    new THREE.CapsuleGeometry(0.42, 1.5, 24, 48),
    cuticle(0xd2ead9, 0.28, {
      transmission: 0.72, roughness: 0.16, thickness: 0.6,
      attenuationColor: new THREE.Color(0x5f9484), attenuationDistance: 1.6,
      rim: { color: 0xdafff0, power: 2.6, intensity: 1.15 },
    }),
  );
  wall.name = 'cell-wall';
  wall.rotation.z = Math.PI / 2;
  wall.renderOrder = 10;
  g.add(wall);
  registerOrgan(g, wall, 'Cell wall & membrane', 'Peptidoglycan wall over the plasma membrane — holds turgor and shape.', 0.0);

  // ── Cytoplasm: a faint inner fill so the granulation reads as suspended ───
  const cyto = new THREE.Mesh(
    new THREE.CapsuleGeometry(0.36, 1.45, 16, 32),
    cuticle(0xa9dcb6, 0.12, { transmission: 0.3, rim: false, normal: false }),
  );
  cyto.rotation.z = Math.PI / 2;
  cyto.renderOrder = 6;
  g.add(cyto);

  // ── Nucleoid: coiled chromosome, a loose supercoiled tangle ──────────────
  const nucGroup = new THREE.Group();
  nucGroup.name = 'nucleoid';
  const pts = [];
  for (let i = 0; i <= 96; i++) {
    const t = i / 96;
    const x = (t - 0.5) * 1.1;
    // two nested twist frequencies read as a supercoil rather than a spring
    const rad = 0.13 + Math.sin(t * TAU * 2) * 0.03;
    pts.push(new THREE.Vector3(
      x,
      Math.sin(t * TAU * 5) * rad,
      Math.cos(t * TAU * 5.3) * rad,
    ));
  }
  const dna = new THREE.Mesh(
    new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 160, 0.028, 7, false),
    nucleus(0x7fa8ff, { emissive: new THREE.Color(0x2a3a7a) }),
  );
  dna.name = 'nucleoid-dna';
  nucGroup.add(dna);
  g.add(nucGroup);
  registerOrgan(g, nucGroup, 'Nucleoid (DNA)', 'A single circular chromosome, supercoiled and free in the cytoplasm — no membrane.', 0.5);

  // ── Ribosomes: dense fine granulation, revealed only at the deepest zoom ──
  const riboMat = nucleus(0xffe0a0, { emissive: new THREE.Color(0x4a3410) });
  const ribo = granuleField(0.68, 0.3, 0.3, 340, 0.028, riboMat, { seed: 7 });
  ribo.name = 'ribosomes';
  g.add(ribo);
  registerOrgan(g, ribo, 'Ribosomes', 'Tens of thousands of protein factories give the cytoplasm its granular texture.', 0.85);

  // ── Flagellum: a rotating helical filament off one pole ──────────────────
  const flag = helixFilament(1.9, 4.2, 0.2,
    organ(0xe6f2ea, { emissive: new THREE.Color(0x141a17), roughness: 0.35, clearcoat: 0.5 }),
    { thickness: 0.022, taper: true, samples: 110 });
  flag.name = 'flagellum';
  flag.position.set(-0.95, 0, 0);
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
      // flagellum spins about its own helix axis (local x) — a real corkscrew
      flag.rotation.x = phase * 9;
      g.rotation.x = Math.sin(phase * 0.6) * 0.05;
      // gentle nucleoid breathing
      const s = 1 + Math.sin(phase * 1.5) * 0.03;
      nucGroup.scale.setScalar(s);
    },
  };
  return g;
}
