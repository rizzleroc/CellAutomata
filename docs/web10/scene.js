// web7 lab scene core — photoreal apparatus in a Catalytic-Silence void.
//
// Reused from web6's proven renderer; only the *environment* is recomposed so
// the 3-D pane sits in the same obsidian darkness as the shell. The glass is
// the luminous specimen against a receiving dark — exactly the register the
// design language asks for. Three things still make it read as a real 1953
// photograph rather than "generated" CG:
//   1. Physically based glass (MeshPhysicalMaterial transmission, IOR 1.5).
//   2. Image-based lighting from a neutral RoomEnvironment, plus a warm
//      tungsten key light (kept — it is what makes the glass glow).
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
  renderer.toneMappingExposure = 0.9;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  container.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x07090d); // obsidian — the same receiving dark as the shell

  // Neutral IBL for crisp glass reflections/refractions.
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  pmrem.dispose();   // the render target is only needed to bake the env map once

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

  // ── Lighting: warm tungsten key + subtle rim + warm fill + lamp glow ────
  const key = new THREE.DirectionalLight(0xffd29a, 2.5); // ~3000K tungsten
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

  // a hair of cool rim just to define the glass edges against the gloom
  const rim = new THREE.DirectionalLight(0xb9c4e0, 0.28);
  rim.position.set(6, 4, -5);
  scene.add(rim);

  const hemi = new THREE.HemisphereLight(0xffe1b4, 0x0b0e13, 0.3); // cooler ground bounce → obsidian
  scene.add(hemi);

  // warm desk-lamp pool on the bench (as in the reference photo, lower-left)
  const lamp = new THREE.PointLight(0xffb866, 14, 9, 2);
  lamp.position.set(-4.2, 1.6, 2.2);
  scene.add(lamp);

  // ── Bench + backdrop so the glass has a real environment to refract ─────
  // Cooled toward obsidian so the surfaces recede into the void; the warm key
  // + lamp still pool on the bench, defining the glass without a brown stage.
  const bench = new THREE.Mesh(
    new THREE.BoxGeometry(40, 0.4, 24),
    new THREE.MeshStandardMaterial({ color: 0x14110d, roughness: 0.78, metalness: 0.05 }),
  );
  bench.position.y = -0.2;
  bench.receiveShadow = true;
  scene.add(bench);

  const wall = new THREE.Mesh(
    new THREE.PlaneGeometry(40, 24),
    new THREE.MeshStandardMaterial({ color: 0x0a0d12, roughness: 0.96 }),
  );
  wall.position.set(0, 8, -7);
  wall.receiveShadow = true;
  scene.add(wall);
  scene.add(makeBackdrop());

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
    // In Experiment view the lab pane is display:none → clientWidth/Height are 0.
    // Skip the resize then (camera.aspect would be NaN); the next switch back to
    // lab/split re-runs setSize with real dims. Guards against a 0×0 renderer.
    if (w === 0 || h === 0) return;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
    composer.setSize(w, h);
  }
  window.addEventListener('resize', setSize);

  return { THREE, renderer, scene, camera, controls, composer, setSize };
}

// A quiet, stage-agnostic Catalytic-Silence backdrop: an obsidian field with a
// single teal hairline and a near-microscopic monospace mark. Replaces web6's
// hardcoded green "MILLER–UREY 1953" chalkboard, which only suited Stage 0 and
// clashed everywhere else. No theatrical gesture — composition, not decoration.
function makeBackdrop() {
  const c = document.createElement('canvas');
  c.width = 1024; c.height = 640;
  const g = c.getContext('2d');
  // obsidian, faintly graded so the glass reads against it
  const grad = g.createLinearGradient(0, 0, 0, c.height);
  grad.addColorStop(0, '#080a0f'); grad.addColorStop(1, '#05070a');
  g.fillStyle = grad; g.fillRect(0, 0, c.width, c.height);
  // a hairline rule — a whisper of structure, teal at low alpha
  g.strokeStyle = 'rgba(63,224,208,0.22)'; g.lineWidth = 1.5;
  g.beginPath(); g.moveTo(120, 470); g.lineTo(c.width - 120, 470); g.stroke();
  // registration ticks at the rule's ends
  g.beginPath(); g.moveTo(120, 462); g.lineTo(120, 478);
  g.moveTo(c.width - 120, 462); g.lineTo(c.width - 120, 478); g.stroke();
  // the apparatus's own grammar, set near-microscopic
  g.fillStyle = 'rgba(154,146,128,0.55)';
  g.font = '22px "IBM Plex Mono", monospace';
  g.textAlign = 'center';
  g.fillText('C E L L A U T O   ·   A N   O R I G I N - O F - L I F E   I N S T R U M E N T', c.width / 2, 508);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  const board = new THREE.Mesh(
    new THREE.PlaneGeometry(9, 5.6),
    new THREE.MeshStandardMaterial({ map: tex, roughness: 0.96, metalness: 0 }),
  );
  board.position.set(0, 4.6, -6.92);
  return board;
}
