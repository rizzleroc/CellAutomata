// web4 lab scene core — photoreal vintage-lab renderer.
//
// Glass apparatus is the subject, so this leans on three things to read as a
// real 1953 photograph rather than "generated" CG:
//   1. Physically based glass (MeshPhysicalMaterial transmission, IOR 1.5).
//   2. Image-based lighting from a neutral RoomEnvironment, plus a warm
//      tungsten key light for the period feel.
//   3. ACES Filmic tone-mapping + UnrealBloom so the electric spark blooms
//      the way a plasma discharge does on film.

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

export function createLab(container) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.95;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  container.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x14100c); // warm near-black lab gloom

  // Neutral IBL for crisp glass reflections/refractions.
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

  const camera = new THREE.PerspectiveCamera(
    42, container.clientWidth / container.clientHeight, 0.1, 100,
  );
  camera.position.set(4.6, 3.4, 6.4);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.06;
  controls.target.set(0, 2.6, 0);
  controls.minDistance = 3;
  controls.maxDistance = 16;
  controls.maxPolarAngle = Math.PI * 0.52;

  // ── Lighting: warm tungsten key + cool rim + soft fill ──────────────────
  const key = new THREE.DirectionalLight(0xffdca8, 2.4);
  key.position.set(-5, 7, 5);
  key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048);
  key.shadow.camera.near = 1;
  key.shadow.camera.far = 30;
  key.shadow.camera.left = -8; key.shadow.camera.right = 8;
  key.shadow.camera.top = 8; key.shadow.camera.bottom = -8;
  key.shadow.bias = -0.0004;
  key.shadow.radius = 4;
  scene.add(key);

  const rim = new THREE.DirectionalLight(0x9fb4ff, 0.5);
  rim.position.set(6, 4, -5);
  scene.add(rim);

  const hemi = new THREE.HemisphereLight(0xffe7c4, 0x241a12, 0.35);
  scene.add(hemi);

  // ── Bench + backdrop so the glass has a real environment to refract ─────
  const bench = new THREE.Mesh(
    new THREE.BoxGeometry(40, 0.4, 24),
    new THREE.MeshStandardMaterial({ color: 0x3a2a1c, roughness: 0.75, metalness: 0.05 }),
  );
  bench.position.y = -0.2;
  bench.receiveShadow = true;
  scene.add(bench);

  const wall = new THREE.Mesh(
    new THREE.PlaneGeometry(40, 24),
    new THREE.MeshStandardMaterial({ color: 0x2b2519, roughness: 0.95 }),
  );
  wall.position.set(0, 8, -7);
  wall.receiveShadow = true;
  scene.add(wall);
  scene.add(makeChalkboard());

  // ── Postprocessing: bloom tuned so only the spark blooms ────────────────
  const composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, camera));
  const bloom = new UnrealBloomPass(
    new THREE.Vector2(container.clientWidth, container.clientHeight),
    0.75, 0.5, 0.82,
  );
  composer.addPass(bloom);
  composer.addPass(new OutputPass());

  function setSize() {
    const w = container.clientWidth, h = container.clientHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
    composer.setSize(w, h);
  }
  window.addEventListener('resize', setSize);

  return { THREE, renderer, scene, camera, controls, composer, setSize };
}

// Period chalkboard reading "MILLER–UREY EXPERIMENT 1953", as in the reference.
function makeChalkboard() {
  const c = document.createElement('canvas');
  c.width = 1024; c.height = 640;
  const g = c.getContext('2d');
  g.fillStyle = '#13312a'; g.fillRect(0, 0, c.width, c.height);
  g.fillStyle = 'rgba(255,255,255,0.05)';
  for (let i = 0; i < 400; i++) g.fillRect(Math.random() * c.width, Math.random() * c.height, 2, 1);
  g.fillStyle = '#e8e6d8';
  g.font = '92px Georgia, serif';
  g.textAlign = 'center';
  g.fillText('MILLER–UREY', c.width / 2, 220);
  g.fillText('EXPERIMENT', c.width / 2, 340);
  g.font = '120px Georgia, serif';
  g.fillText('1953', c.width / 2, 500);
  g.strokeStyle = '#e8e6d8'; g.lineWidth = 4;
  g.beginPath(); g.moveTo(c.width / 2 - 150, 540); g.lineTo(c.width / 2 + 150, 540); g.stroke();
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  const board = new THREE.Mesh(
    new THREE.PlaneGeometry(7, 4.4),
    new THREE.MeshStandardMaterial({ map: tex, roughness: 0.9 }),
  );
  board.position.set(-5.0, 4.4, -6.9);
  return board;
}
