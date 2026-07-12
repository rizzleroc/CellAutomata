// Nematode — a free-living roundworm, the most abundant animal on Earth.
// A translucent cylinder that thrashes in an S-wave: a muscular pharynx with a
// pumping bulb draws in bacteria, a straight intestine runs the length of the
// body, a nerve ring circles the pharynx, and the gonad coils alongside the
// gut. ~600 µm in life.

import { THREE, cuticle, organ, nucleus, tubeBody, registerOrgan, rng, TAU } from './lib.js';

export const meta = {
  id: 'nematode',
  name: 'Nematode',
  taxon: 'Rhabditis sp.',
  kingdom: 'Animalia',
  micronLength: 620,
  blurb: 'A roundworm — the most numerous animal alive. It thrashes in an S-shaped wave; a pumping pharynx feeds a straight gut running the whole body.',
  build,
};

const N = 60;               // centreline samples
const LEN = 5.2;

function build() {
  const g = new THREE.Group();
  g.name = 'nematode';
  const r = rng(63);

  // Build the worm around a re-poseable centreline. We keep the curve points
  // and rebuild the tube each frame so the S-wave is real body motion, not a
  // rotation trick.
  const bodyMat = cuticle(0xefe9d8, 0.19, { transmission: 0.5 });
  const state = makeCentreline(0);
  let body = tubeBody(state.points, radiusFn, bodyMat, { tubular: N, radial: 20 });
  body.name = 'body';
  body.renderOrder = 12;
  g.add(body);
  registerOrgan(g, body, 'Cuticle & body wall', 'A tough collagen cuticle over longitudinal muscle — antagonised against the internal pressure, it drives the S-wave.', 0.0);

  // ── Pharynx with terminal bulb (head) ────────────────────────────────────
  const pharynx = new THREE.Group(); pharynx.name = 'pharynx';
  const pharyToggle = new THREE.Mesh(
    new THREE.CylinderGeometry(0.12, 0.18, 0.9, 14),
    organ(0xc98a76, { emissive: new THREE.Color(0x3a1f18), transparent: true, opacity: 0.92 }),
  );
  pharyToggle.rotation.z = Math.PI / 2;
  pharynx.add(pharyToggle);
  const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.24, 18, 14), organ(0xd0937d, { emissive: new THREE.Color(0x3a1f18) }));
  bulb.position.x = -0.55;
  pharynx.add(bulb);
  pharynx.userData.bulb = bulb;
  g.add(pharynx);
  registerOrgan(g, pharynx, 'Pharynx & bulb', 'A muscular pump: the terminal bulb contracts rhythmically to suck in bacteria and drive them into the gut.', 0.35);

  // ── Nerve ring around the pharynx ────────────────────────────────────────
  const nerve = new THREE.Mesh(new THREE.TorusGeometry(0.24, 0.03, 8, 20), nucleus(0xffd27a, { emissive: new THREE.Color(0x4a3410) }));
  nerve.name = 'nerve-ring';
  nerve.rotation.y = Math.PI / 2;
  nerve.position.x = -0.1;
  g.add(nerve);
  registerOrgan(g, nerve, 'Nerve ring', 'The worm\'s brain — a ring of neurons circling the pharynx, coordinating the whole nervous system.', 0.6);

  // ── Intestine (runs the length) + gonad coil ─────────────────────────────
  let gut = tubeBody(state.points, () => 0.06, organ(0x9a7a4a, { transparent: true, opacity: 0.9 }), { tubular: N, radial: 8 });
  gut.name = 'intestine';
  g.add(gut);
  registerOrgan(g, gut, 'Intestine', 'A single tube of gut cells the length of the body, absorbing digested bacteria.', 0.45);

  let gonad = tubeBody(state.points.map((p) => p.clone().add(new THREE.Vector3(0, 0.14, 0.05))), (t) => 0.05 * Math.sin(t * Math.PI), nucleus(0xbfe0ff, { emissive: new THREE.Color(0x1e2c44), transparent: true, opacity: 0.85 }), { tubular: N, radial: 8 });
  gonad.name = 'gonad';
  g.add(gonad);
  registerOrgan(g, gonad, 'Gonad', 'The reproductive tract coils beside the gut — in a gravid female you can see eggs lined up inside.', 0.65);

  g.userData.focusRadius = 7.6;

  let running = true, phase = 0;
  const rebuild = (t) => {
    const s = makeCentreline(t);
    // swap geometries in place (dispose the old to avoid leaks in long runs)
    const nb = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(s.points), N, 1, 20, false);
    reprofile(nb, new THREE.CatmullRomCurve3(s.points), radiusFn, N, 20);
    body.geometry.dispose(); body.geometry = nb;
    const ng = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(s.points), N, 1, 8, false);
    reprofile(ng, new THREE.CatmullRomCurve3(s.points), () => 0.06, N, 8);
    gut.geometry.dispose(); gut.geometry = ng;
    // head follows the leading tangent
    const head = s.points[0], next = s.points[1];
    pharynx.position.copy(head);
    nerve.position.copy(head.clone().lerp(next, 0.4));
    const dir = next.clone().sub(head);
    pharynx.quaternion.setFromUnitVectors(new THREE.Vector3(-1, 0, 0), dir.normalize());
  };

  g.userData.anim = {
    setRunning: (v) => { running = v; },
    getProgress: () => (phase * 0.2) % 1,
    reset: () => { phase = 0; rebuild(0); },
    update: (dt, t) => {
      if (running) phase += dt;
      rebuild(phase);
      // pharyngeal bulb pumps
      pharynx.userData.bulb.scale.setScalar(1 + Math.max(0, Math.sin(phase * 8)) * 0.25);
    },
  };
  rebuild(0);
  return g;
}

function radiusFn(t) {
  // tapered at both ends, fattest at the mid-body
  return 0.32 * Math.sin(Math.min(1, Math.max(0, t)) * Math.PI) ** 0.5 + 0.05;
}

function makeCentreline(t) {
  const points = [];
  for (let i = 0; i <= N; i++) {
    const u = i / N;
    const x = (u - 0.5) * LEN;
    // travelling sinusoid = undulatory swimming
    const y = Math.sin(u * TAU * 1.6 - t * 4) * (0.9 * Math.sin(u * Math.PI));
    points.push(new THREE.Vector3(x, y, 0));
  }
  return { points };
}

// Re-profile a TubeGeometry's rings to a variable radius (shared with lib's
// tubeBody, inlined here because we rebuild every frame and want the curve).
function reprofile(geo, curve, radiusFn, tubular, radial) {
  const pos = geo.attributes.position;
  for (let i = 0; i <= tubular; i++) {
    const tt = i / tubular;
    const c = curve.getPointAt(tt);
    const rr = Math.max(0.0001, radiusFn(tt));
    for (let j = 0; j <= radial; j++) {
      const idx = i * (radial + 1) + j;
      const vx = pos.getX(idx), vy = pos.getY(idx), vz = pos.getZ(idx);
      pos.setXYZ(idx, c.x + (vx - c.x) * rr, c.y + (vy - c.y) * rr, c.z + (vz - c.z) * rr);
    }
  }
  geo.attributes.position.needsUpdate = true;
  geo.computeVertexNormals();
}
