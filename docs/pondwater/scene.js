// Pond Water Analyzer — the microscope stage.
//
// The look is a dark-field wet-mount: the specimen is lit against a deep
// blue-black field of water, the way a real dark-field condenser throws light
// so only what scatters it glows. Suspended detritus and marine snow drift in
// the medium; a soft caustic gradient stands in for the condenser cone. The
// same photoreal pillars the rest of the lab uses — PBR image-based lighting,
// ACES tone-mapping, a restrained bloom so the wet highlights bloom like glass.

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

export function createScope(container) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  container.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x030608);   // the dark-field: near-black water
  scene.fog = new THREE.FogExp2(0x04080c, 0.028); // the medium recedes into depth

  // Neutral IBL for the wet, glassy sheen on cuticles and shells.
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.03).texture;
  pmrem.dispose();

  const camera = new THREE.PerspectiveCamera(
    40, container.clientWidth / container.clientHeight, 0.01, 400,
  );
  camera.position.set(0, 0, 9);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.minDistance = 0.35;      // deep organ-level dive
  controls.maxDistance = 60;        // the whole drop
  controls.zoomSpeed = 0.9;
  controls.rotateSpeed = 0.7;

  // ── Dark-field lighting ─────────────────────────────────────────────────
  // A cool condenser key from below-left (dark-field light rakes in at a low
  // angle), a warm fill, and a rim to pull glassy edges out of the black.
  const key = new THREE.DirectionalLight(0xcfe8ff, 2.2);
  key.position.set(-4, -3, 6);
  scene.add(key);

  const rim = new THREE.DirectionalLight(0x9fd0ff, 1.1);
  rim.position.set(5, 4, -4);
  scene.add(rim);

  const fill = new THREE.HemisphereLight(0x3a5a7a, 0x02040a, 0.55);
  scene.add(fill);

  // A moving specular "hotspot" — the condenser aperture catching the specimen.
  const spot = new THREE.PointLight(0xbfe6ff, 8, 30, 2);
  spot.position.set(2, 3, 5);
  scene.add(spot);

  // ── The medium: suspended detritus + marine snow drifting in the water ───
  const medium = createMedium();
  scene.add(medium);

  // ── Postprocessing: wet-highlight bloom ─────────────────────────────────
  const composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, camera));
  const bloom = new UnrealBloomPass(
    new THREE.Vector2(container.clientWidth, container.clientHeight),
    0.55, 0.7, 0.85,
  );
  composer.addPass(bloom);
  composer.addPass(new OutputPass());

  function setSize() {
    const w = container.clientWidth, h = container.clientHeight;
    if (w === 0 || h === 0) return;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
    composer.setSize(w, h);
  }
  window.addEventListener('resize', setSize);

  return { THREE, renderer, scene, camera, controls, composer, medium, spot, setSize };
}

// Marine snow: two shells of drifting particulates — coarse detritus near the
// stage, a fine haze farther out — so there is always motion and parallax that
// sells the sense of a fluid volume, and the sense of scale as you dive.
function createMedium() {
  const group = new THREE.Group();
  group.name = 'medium';

  const layers = [
    { n: 900, spread: 55, size: 0.09, color: 0x2b4a5e, opacity: 0.5, drift: 0.4 },
    { n: 600, spread: 22, size: 0.05, color: 0x3f7088, opacity: 0.35, drift: 0.8 },
    { n: 400, spread: 8, size: 0.03, color: 0x6fb0c8, opacity: 0.6, drift: 1.4 },
  ];

  for (const L of layers) {
    const geo = new THREE.BufferGeometry();
    const pos = new Float32Array(L.n * 3);
    for (let i = 0; i < L.n; i++) {
      pos[i * 3] = (Math.random() - 0.5) * L.spread;
      pos[i * 3 + 1] = (Math.random() - 0.5) * L.spread;
      pos[i * 3 + 2] = (Math.random() - 0.5) * L.spread;
    }
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    const mat = new THREE.PointsMaterial({
      color: L.color,
      size: L.size,
      transparent: true,
      opacity: L.opacity,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      sizeAttenuation: true,
    });
    const pts = new THREE.Points(geo, mat);
    pts.userData = { drift: L.drift, spread: L.spread };
    group.add(pts);
  }

  group.userData.update = (dt, t) => {
    for (const pts of group.children) {
      const pos = pts.geometry.attributes.position;
      const d = pts.userData.drift, s = pts.userData.spread;
      for (let i = 0; i < pos.count; i++) {
        let y = pos.getY(i) - d * dt * 0.3;
        if (y < -s / 2) y += s;                     // wrap: endless snowfall
        pos.setY(i, y);
        pos.setX(i, pos.getX(i) + Math.sin(t * 0.2 + i) * dt * 0.05 * d);
      }
      pos.needsUpdate = true;
    }
  };

  return group;
}
