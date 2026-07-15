// Murmuration — the sky.
//
// The stage is a winter dusk over a roost: a gradient sky dome from deep indigo
// at the zenith to a warm sodium band at the horizon, a low sun the bloom pass
// turns into a soft glare, a dark ground receding into haze, and the same
// photoreal pillars the rest of this lab uses — image-based lighting for the
// faint iridescence on the birds, ACES tone-mapping, exponential fog for aerial
// perspective, and a restrained post chain (bloom → dusk grade → grain +
// vignette) that makes it read as footage rather than a 3-D toy.
//
// createScope() returns everything the controller drives; the composer's render
// is wrapped so grain/optics advance without main.js knowing.

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

// Dusk sky gradient — evaluated on a back-faced dome so it wraps the whole view.
const SkyShader = {
  uniforms: {
    uZenith:  { value: new THREE.Color(0x14183a) }, // deep indigo overhead
    uHorizon: { value: new THREE.Color(0xd98a4a) }, // sodium band at the rim
    uGround:  { value: new THREE.Color(0x0a0a10) }, // dark earth below
    uSunDir:  { value: new THREE.Vector3(0.6, 0.08, -0.8).normalize() },
    uSunCol:  { value: new THREE.Color(0xffd9a0) },
  },
  vertexShader: /* glsl */`
    varying vec3 vDir;
    void main() { vDir = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }
  `,
  fragmentShader: /* glsl */`
    varying vec3 vDir;
    uniform vec3 uZenith, uHorizon, uGround, uSunDir, uSunCol;
    void main() {
      float h = vDir.y;
      vec3 sky = mix(uHorizon, uZenith, smoothstep(0.0, 0.55, h));
      sky = mix(sky, uGround, smoothstep(0.0, -0.18, h));   // fade under the horizon
      // sun glow: a warm halo where the view aligns with the sun
      float sd = max(dot(normalize(vDir), uSunDir), 0.0);
      sky += uSunCol * pow(sd, 10.0) * 0.55;
      sky += uSunCol * pow(sd, 160.0) * 1.8;                // the disc itself, for bloom
      gl_FragColor = vec4(sky, 1.0);
    }
  `,
};

// A single dusk-grade optics pass: a warm filmic tint, gentle vignette, and
// animated sensor grain — cheap, one draw, keeps the footage feel.
const OpticsShader = {
  uniforms: {
    tDiffuse: { value: null },
    uTime: { value: 0 },
    uVignette: { value: 0.42 },
    uGrain: { value: 0.045 },
    uResolution: { value: new THREE.Vector2(1, 1) },
  },
  vertexShader: /* glsl */`
    varying vec2 vUv;
    void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }
  `,
  fragmentShader: /* glsl */`
    varying vec2 vUv;
    uniform sampler2D tDiffuse;
    uniform float uTime, uVignette, uGrain;
    uniform vec2 uResolution;
    float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
    void main() {
      vec3 col = texture2D(tDiffuse, vUv).rgb;
      // warm dusk grade — lift the reds, cool the shadows a touch
      col = pow(col, vec3(0.96, 1.0, 1.05));
      col *= vec3(1.05, 1.0, 0.95);
      float r = length(vUv - 0.5);
      col *= 1.0 - smoothstep(0.42, 0.92, r) * uVignette;
      col += (hash(vUv * uResolution + uTime) - 0.5) * uGrain;
      gl_FragColor = vec4(col, 1.0);
    }
  `,
};

export function createScope(container) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  container.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x1a1c34);
  scene.fog = new THREE.FogExp2(0x2a2340, 0.0016);   // aerial perspective / dusk haze

  // Neutral IBL so the birds' plumage catches a faint metallic sheen.
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.02).texture;
  pmrem.dispose();

  const camera = new THREE.PerspectiveCamera(
    52, container.clientWidth / container.clientHeight, 0.5, 4000,
  );
  camera.position.set(0, 60, 260);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.06;
  controls.minDistance = 12;
  controls.maxDistance = 900;
  controls.maxPolarAngle = Math.PI * 0.52;  // don't drop under the ground
  controls.target.set(0, 40, 0);

  // ── sky dome ───────────────────────────────────────────────────────────
  const sky = new THREE.Mesh(
    new THREE.SphereGeometry(2600, 32, 16),
    new THREE.ShaderMaterial({ ...SkyShader, side: THREE.BackSide, depthWrite: false, fog: false }),
  );
  sky.name = 'sky';
  scene.add(sky);

  // ── ground — a dark plane far below, fading into the haze ────────────────
  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(6000, 6000),
    new THREE.MeshStandardMaterial({ color: 0x0c0e14, roughness: 1.0, metalness: 0 }),
  );
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -4;
  ground.name = 'ground';
  scene.add(ground);

  // ── lighting: a low warm sun key, a cool sky fill, a back rim ────────────
  const sunDir = SkyShader.uniforms.uSunDir.value;
  const sun = new THREE.DirectionalLight(0xffca8a, 2.4);
  sun.position.copy(sunDir).multiplyScalar(400).add(new THREE.Vector3(0, 60, 0));
  scene.add(sun);

  const skyFill = new THREE.HemisphereLight(0x9fb0e0, 0x20222e, 0.9);
  scene.add(skyFill);

  const rim = new THREE.DirectionalLight(0xbcd0ff, 0.7);
  rim.position.set(-300, 120, 300);
  scene.add(rim);

  // ── post: bloom → dusk grade + grain ─────────────────────────────────────
  const composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, camera));

  const bloom = new UnrealBloomPass(
    new THREE.Vector2(container.clientWidth, container.clientHeight),
    0.5, 0.85, 0.78,    // the sun glare + brightest rim-lit birds halo softly
  );
  composer.addPass(bloom);
  composer.addPass(new OutputPass());

  const optics = new ShaderPass(OpticsShader);
  optics.uniforms.uResolution.value.set(container.clientWidth, container.clientHeight);
  composer.addPass(optics);

  const _render = composer.render.bind(composer);
  let frame = 0;
  composer.render = (deltaTime) => {
    optics.uniforms.uTime.value = (frame = (frame + 1) % 100000);
    _render(deltaTime);
  };

  function setSize() {
    const w = container.clientWidth, h = container.clientHeight;
    if (w === 0 || h === 0) return;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
    composer.setSize(w, h);
    optics.uniforms.uResolution.value.set(w, h);
  }
  window.addEventListener('resize', setSize);

  return { THREE, renderer, scene, camera, controls, composer, bloom, optics, sky, sun, setSize };
}
