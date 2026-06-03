// Stage 0 — Miller–Urey spark-discharge apparatus (1953).
//
// Hand-built borosilicate glassware: the geometry is all spheres / cylinders /
// swept tubes, which is exactly what a physical glass material renders
// photoreal. Layout follows the canonical schematic and the period photo:
//   - upper spherical spark chamber with two angled electrodes + plasma arc
//   - tall glass riser arching over from the boiling flask (the gas loop)
//   - water-jacket condenser with side arms + a stopcock
//   - lower collection flask that fills with tea-dark "organic" liquid
//   - boiling flask on a black heating mantle, bubbling
//   - steel ring-stand with clamps
//
// Every part is named so the right-hand parts panel and the exploded view can
// address it individually (à la a real exploded lab diagram).

import * as THREE from 'three';

// ── Shared materials ────────────────────────────────────────────────────────
const glass = () => new THREE.MeshPhysicalMaterial({
  color: 0xffffff, metalness: 0, roughness: 0.04,
  transmission: 1.0, thickness: 0.35, ior: 1.5,
  transparent: true, envMapIntensity: 1.4, clearcoat: 0.3, clearcoatRoughness: 0.1,
});
const steel = () => new THREE.MeshStandardMaterial({ color: 0x8c8f96, metalness: 0.95, roughness: 0.42 });
const brass = () => new THREE.MeshStandardMaterial({ color: 0xb8893f, metalness: 1.0, roughness: 0.32 });
const darkMetal = () => new THREE.MeshStandardMaterial({ color: 0x1b1b1f, metalness: 0.7, roughness: 0.5 });
const copper = () => new THREE.MeshStandardMaterial({ color: 0xb5703a, metalness: 0.9, roughness: 0.35 });
const ceramic = () => new THREE.MeshStandardMaterial({ color: 0x141414, roughness: 0.85, metalness: 0.05 });

function v(x, y, z = 0) { return new THREE.Vector3(x, y, z); }

// A swept glass tube along a polyline.
function tube(points, radius = 0.085, name = 'tube') {
  const curve = new THREE.CatmullRomCurve3(points);
  const geo = new THREE.TubeGeometry(curve, Math.max(24, points.length * 12), radius, 20, false);
  const m = new THREE.Mesh(geo, glass());
  m.name = name; m.castShadow = true;
  return m;
}

export function buildMillerUrey() {
  const group = new THREE.Group();
  group.name = 'miller-urey-1953';
  const anim = {};

  // ── Spark chamber (upper sphere) ──────────────────────────────────────────
  const sphereC = v(1.5, 4.7, 0);
  const R = 1.25;
  const chamber = new THREE.Mesh(new THREE.SphereGeometry(R, 64, 48), glass());
  chamber.name = 'spark-chamber';
  chamber.position.copy(sphereC);
  chamber.castShadow = true;
  group.add(chamber);

  // faint gas tint inside the chamber
  const gas = new THREE.Mesh(
    new THREE.SphereGeometry(R * 0.94, 32, 24),
    new THREE.MeshBasicMaterial({ color: 0xb9a6ff, transparent: true, opacity: 0.05 }),
  );
  gas.name = 'gases'; gas.position.copy(sphereC); group.add(gas);

  // ── Electrodes: two black caps with coiled leads, tips meeting at centre ──
  const electrodes = [];
  for (const sgn of [-1, 1]) {
    const dir = v(sgn * 0.72, 0.69, -0.05).normalize();
    const entry = sphereC.clone().add(dir.clone().multiplyScalar(R + 0.05));
    // glass sleeve through the wall
    const sleeve = tube([sphereC.clone().add(dir.clone().multiplyScalar(R * 0.2)),
                         entry.clone().add(dir.clone().multiplyScalar(0.25))], 0.07,
                        `electrode-sleeve-${sgn < 0 ? 'L' : 'R'}`);
    group.add(sleeve);
    // electrode rod to centre (spark gap)
    const rod = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035,
      sphereC.distanceTo(entry) - 0.25, 16), darkMetal());
    rod.name = `electrode-rod-${sgn < 0 ? 'L' : 'R'}`;
    const mid = sphereC.clone().add(dir.clone().multiplyScalar((R - 0.2) / 2 + 0.1));
    rod.position.copy(mid);
    rod.quaternion.setFromUnitVectors(v(0, 1, 0), dir.clone());
    group.add(rod);
    // black connector cap outside
    const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.16, 0.5, 20), darkMetal());
    cap.name = `electrode-cap-${sgn < 0 ? 'L' : 'R'}`;
    cap.position.copy(entry.clone().add(dir.clone().multiplyScalar(0.32)));
    cap.quaternion.setFromUnitVectors(v(0, 1, 0), dir.clone());
    cap.castShadow = true;
    group.add(cap);
    // coiled copper lead
    const coilPts = [];
    const cbase = entry.clone().add(dir.clone().multiplyScalar(0.6));
    for (let i = 0; i <= 60; i++) {
      const a = i / 60 * Math.PI * 6;
      coilPts.push(v(cbase.x + Math.cos(a) * 0.12 - sgn * i / 60 * 0.6,
                     cbase.y + 0.5 + i / 60 * 0.4,
                     cbase.z + Math.sin(a) * 0.12));
    }
    const coil = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(coilPts), 120, 0.02, 8, false), copper());
    coil.name = `electrode-lead-${sgn < 0 ? 'L' : 'R'}`;
    group.add(coil);
    electrodes.push(entry);
  }

  // ── Plasma spark: jagged emissive arcs + flickering point light ───────────
  const sparkMat = new THREE.LineBasicMaterial({ color: 0xc77dff, transparent: true, opacity: 0.9 });
  const sparkGeo = new THREE.BufferGeometry();
  const ARCS = 9, SEG = 7;
  sparkGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(ARCS * SEG * 2 * 3), 3));
  const spark = new THREE.LineSegments(sparkGeo, sparkMat);
  spark.name = 'spark-discharge';
  spark.position.copy(sphereC);
  group.add(spark);

  const sparkLight = new THREE.PointLight(0xc77dff, 6, 6, 2);
  sparkLight.position.copy(sphereC);
  group.add(sparkLight);

  const sparkCore = new THREE.Mesh(
    new THREE.SphereGeometry(0.09, 16, 16),
    new THREE.MeshBasicMaterial({ color: 0xf0d9ff }),
  );
  sparkCore.position.copy(sphereC); sparkCore.name = 'spark-core';
  group.add(sparkCore);

  function reseedSpark() {
    const pos = sparkGeo.attributes.position.array;
    let k = 0;
    for (let a = 0; a < ARCS; a++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      const end = v(Math.sin(phi) * Math.cos(theta), Math.cos(phi), Math.sin(phi) * Math.sin(theta))
        .multiplyScalar(R * 0.92);
      let prev = v(0, 0, 0);
      for (let s = 0; s < SEG; s++) {
        const t1 = s / SEG, t2 = (s + 1) / SEG;
        const jitter = () => (Math.random() - 0.5) * 0.18 * (1 - Math.abs(t1 - 0.5) * 1.2);
        const next = end.clone().multiplyScalar(t2).add(v(jitter(), jitter(), jitter()));
        pos[k++] = prev.x; pos[k++] = prev.y; pos[k++] = prev.z;
        pos[k++] = next.x; pos[k++] = next.y; pos[k++] = next.z;
        prev = next;
      }
    }
    sparkGeo.attributes.position.needsUpdate = true;
  }
  reseedSpark();

  // ── Riser: boiling-flask neck → up → arch over → down toward chamber ──────
  const boilC = v(-2.4, 1.05, 0);
  group.add(tube([
    v(boilC.x, boilC.y + 0.95, 0), v(boilC.x, 3.2, 0), v(boilC.x, 5.5, 0),
    v(-1.6, 6.0, 0), v(-0.2, 6.05, 0), v(0.4, 5.7, 0), v(0.5, 4.9, 0),
    sphereC.clone().add(v(-0.9, 0.55, 0)),
  ], 0.095, 'riser-tube'));

  // little glass relief loop near the top (as in the photo)
  const loop = new THREE.Mesh(new THREE.TorusGeometry(0.22, 0.04, 12, 40), glass());
  loop.name = 'relief-loop';
  loop.position.set(0.55, 5.55, 0); loop.rotation.y = Math.PI / 2;
  group.add(loop);

  // ── Condenser (between chamber and collection flask) ──────────────────────
  const condC = v(1.5, 2.65, 0);
  group.add(tube([sphereC.clone().add(v(0, -R - 0.02, 0)), v(1.5, 3.55, 0)], 0.09, 'chamber-neck'));
  const jacket = new THREE.Mesh(new THREE.CylinderGeometry(0.34, 0.34, 1.7, 40, 1, true), glass());
  jacket.name = 'condenser-jacket'; jacket.position.copy(condC); jacket.castShadow = true;
  group.add(jacket);
  const inner = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.14, 1.95, 24), glass());
  inner.name = 'condenser-inner-tube'; inner.position.copy(condC);
  group.add(inner);
  // water in/out side arms + copper hoses
  for (const [dy, nm] of [[0.6, 'water-out'], [-0.55, 'water-in']]) {
    const arm = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.07, 0.5, 16), glass());
    arm.name = `condenser-${nm}`;
    arm.position.set(condC.x + 0.42, condC.y + dy, 0);
    arm.rotation.z = Math.PI / 2;
    group.add(arm);
    const hose = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3([
      v(condC.x + 0.7, condC.y + dy, 0), v(condC.x + 1.2, condC.y + dy - 0.3, 0.2),
      v(condC.x + 1.3, condC.y + dy - 1.1, 0.3),
    ]), 40, 0.05, 10, false), copper());
    hose.name = `hose-${nm}`;
    group.add(hose);
  }
  // stopcock on the condenser
  const cock = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.34, 12), glass());
  cock.name = 'stopcock'; cock.position.set(condC.x - 0.36, condC.y - 0.7, 0);
  cock.rotation.z = Math.PI / 2; group.add(cock);

  // ── Collection flask (fills with dark organic liquid) ─────────────────────
  const collC = v(1.5, 0.95, 0);
  group.add(tube([v(1.5, 1.78, 0), v(1.5, 1.5, 0)], 0.085, 'collection-neck'));
  const collar = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.13, 0.28, 24), glass());
  collar.name = 'collection-collar'; collar.position.set(1.5, 1.62, 0); group.add(collar);
  const collFlask = new THREE.Mesh(new THREE.SphereGeometry(0.82, 48, 36), glass());
  collFlask.name = 'collection-flask'; collFlask.position.copy(collC); collFlask.castShadow = true;
  group.add(collFlask);
  // dark organic liquid (a clipped sphere cap, level rises + darkens)
  const liquidMat = new THREE.MeshPhysicalMaterial({
    color: 0x3a1d08, roughness: 0.25, transmission: 0.55, thickness: 1.2, ior: 1.35, transparent: true,
  });
  const liquid = new THREE.Mesh(new THREE.SphereGeometry(0.78, 40, 28), liquidMat);
  liquid.name = 'organic-liquid';
  liquid.position.copy(collC);
  liquid.scale.y = 0.5; liquid.position.y = collC.y - 0.34;
  group.add(liquid);
  // bottom stopcock
  const drain = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.32, 12), glass());
  drain.name = 'drain-stopcock'; drain.position.set(1.5, 0.05, 0); group.add(drain);

  // ── Boiling flask + neck + clamp + black mantle ───────────────────────────
  group.add(tube([v(boilC.x, 1.95, 0), v(boilC.x, 1.7, 0)], 0.085, 'boiling-neck'));
  const boilCollar = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.15, 0.3, 24), glass());
  boilCollar.name = 'boiling-collar'; boilCollar.position.set(boilC.x, 1.78, 0); group.add(boilCollar);
  const boilFlask = new THREE.Mesh(new THREE.SphereGeometry(0.95, 48, 36), glass());
  boilFlask.name = 'boiling-flask'; boilFlask.position.copy(boilC); boilFlask.castShadow = true;
  group.add(boilFlask);
  const water = new THREE.Mesh(new THREE.SphereGeometry(0.9, 40, 28),
    new THREE.MeshPhysicalMaterial({ color: 0xcfe6ee, roughness: 0.1, transmission: 0.85, thickness: 1.0, ior: 1.33, transparent: true }));
  water.name = 'boiling-water'; water.position.copy(boilC); water.scale.y = 0.55; water.position.y = boilC.y - 0.42;
  group.add(water);
  const mantle = new THREE.Mesh(new THREE.CylinderGeometry(0.95, 1.05, 0.85, 40), ceramic());
  mantle.name = 'heating-mantle'; mantle.position.set(boilC.x, 0.1, 0); mantle.castShadow = true; mantle.receiveShadow = true;
  group.add(mantle);

  // ── Connecting tube along the bottom (collection → boiling) ───────────────
  group.add(tube([v(1.45, -0.1, 0), v(0.6, -0.18, 0), v(-1.6, -0.18, 0), v(boilC.x, 0.0, 0)], 0.075, 'bottom-loop'));

  // ── Steel ring-stand + clamps ─────────────────────────────────────────────
  const standBase = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.1, 1.0), steel());
  standBase.position.set(3.0, 0.05, -0.3); standBase.castShadow = true; group.add(standBase);
  const rod = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 6.4, 20), steel());
  rod.name = 'ring-stand'; rod.position.set(3.0, 3.2, -0.3); rod.castShadow = true; group.add(rod);
  for (const cy of [4.7, 2.65]) {
    const arm = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 1.7, 12), steel());
    arm.position.set(2.2, cy, -0.15); arm.rotation.z = Math.PI / 2; arm.castShadow = true; group.add(arm);
    // brass clamp boss where the arm meets the rod (period fitting)
    const boss = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 0.22, 16), brass());
    boss.name = `clamp-boss-${cy}`; boss.position.set(3.0, cy, -0.3); boss.castShadow = true; group.add(boss);
    const knurl = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.16, 12), brass());
    knurl.position.set(2.85, cy, -0.05); knurl.rotation.z = Math.PI / 2; group.add(knurl);
  }
  // clamp for the boiling flask on a left rod
  const rod2 = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, 4.6, 16), steel());
  rod2.position.set(-3.5, 2.3, -0.2); rod2.castShadow = true; group.add(rod2);
  const clampArm = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 1.3, 12), steel());
  clampArm.position.set(-2.95, 1.8, 0); clampArm.rotation.z = Math.PI / 2; group.add(clampArm);
  const clampBoss = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 0.22, 16), brass());
  clampBoss.name = 'clamp-boss-boiling'; clampBoss.position.set(-3.5, 1.8, -0.2); clampBoss.castShadow = true; group.add(clampBoss);
  // brass knob/handle on each stopcock
  for (const [sx, sy] of [[condC.x - 0.36, condC.y - 0.7], [1.5, 0.05]]) {
    const knob = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.06, 0.12, 12), brass());
    knob.position.set(sx, sy, 0.14); knob.rotation.x = Math.PI / 2; group.add(knob);
  }

  group.position.y = 0; // sits on bench

  // ── Animation state ───────────────────────────────────────────────────────
  // bubbles in the boiling flask
  const bubbleGeo = new THREE.SphereGeometry(0.04, 8, 8);
  const bubbleMat = new THREE.MeshStandardMaterial({ color: 0xffffff, transparent: true, opacity: 0.5, roughness: 0.2 });
  const bubbles = [];
  for (let i = 0; i < 24; i++) {
    const b = new THREE.Mesh(bubbleGeo, bubbleMat);
    b.userData.reset = () => {
      b.position.set(boilC.x + (Math.random() - 0.5) * 1.1, boilC.y - 0.7, (Math.random() - 0.5) * 1.1);
      b.userData.v = 0.4 + Math.random() * 0.6;
    };
    b.userData.reset();
    group.add(b); bubbles.push(b);
  }
  // falling condensate droplets below the condenser
  const drops = [];
  for (let i = 0; i < 8; i++) {
    const d = new THREE.Mesh(new THREE.SphereGeometry(0.03, 8, 8),
      new THREE.MeshPhysicalMaterial({ color: 0xddeef2, transmission: 0.9, roughness: 0.1, transparent: true }));
    d.userData.reset = () => { d.position.set(1.5, 1.55 - Math.random() * 0.2, 0); d.userData.v = 0; };
    d.userData.reset();
    group.add(d); drops.push(d);
  }

  let running = true;
  let progress = 0; // 0..1 organic accumulation
  anim.setRunning = (on) => { running = on; };
  anim.getProgress = () => progress;
  anim.reset = () => { progress = 0; };

  let sparkTimer = 0;
  anim.update = (dt, t) => {
    // spark
    spark.visible = sparkCore.visible = running;
    if (running) {
      sparkTimer += dt;
      if (sparkTimer > 0.05) { reseedSpark(); sparkTimer = 0; }
      const flick = 0.5 + Math.random() * 0.9;
      sparkLight.intensity = 6 * flick;
      sparkMat.opacity = 0.6 + Math.random() * 0.4;
      sparkCore.scale.setScalar(0.7 + Math.random() * 0.6);
    } else {
      sparkLight.intensity = 0;
    }
    // boiling bubbles
    for (const b of bubbles) {
      if (!running) { b.visible = false; continue; }
      b.visible = true;
      b.position.y += b.userData.v * dt;
      if (b.position.y > boilC.y + 0.2) b.userData.reset();
    }
    // condensate drops
    for (const d of drops) {
      if (!running) { d.visible = false; continue; }
      d.visible = true;
      d.userData.v += 4 * dt;
      d.position.y -= d.userData.v * dt;
      if (d.position.y < 1.0) d.userData.reset();
    }
    // organic accumulation: liquid rises + darkens
    if (running) progress = Math.min(1, progress + dt / 45);
    const fill = 0.42 + progress * 0.42;              // sphere-scale of liquid level
    liquid.scale.y = fill;
    liquid.position.y = collC.y - 0.78 * (1 - fill * 0.5);
    liquidMat.color.setRGB(0.23 * (1 - progress * 0.5), 0.11 * (1 - progress * 0.4), 0.03);
  };

  group.userData.anim = anim;
  return group;
}

export const meta = {
  id: 'stage0-miller-urey',
  label: 'Stage 0 — Miller–Urey',
  title: 'Spark-discharge apparatus · 1953',
  blurb: 'A reducing atmosphere (CH₄, NH₃, H₂, H₂O) sparked by tungsten electrodes; '
       + 'condensate collects in the trap, darkening as amino acids accumulate.',
  build: buildMillerUrey,
};
