// web7 lab scene core — photoreal apparatus in a Catalytic-Silence void.
//
// Reused from web6's proven renderer; only the *environment* is recomposed so
// the 3-D pane sits in the same obsidian darkness as the shell. The glass is
// the luminous specimen against a receiving dark — exactly the register the
// design language asks for. Three things still make it read as a real 1953
// photograph rather than "generated" CG:
//   1. Physically based glass (MeshPhysicalMaterial transmission, IOR 1.5).
//   2. STUDIO SOFTBOX LIGHTING — warm RectAreaLight key panels (upper-L/-R) and
//      a cool rim panel behind roll crisp rectangular reflections across the
//      glass, the single biggest "real photo shoot" tell. IBL is now a bespoke
//      softbox env (tight PMREM sigma → crisp reflections) with a RoomEnvironment
//      fallback; the warm tungsten DirectionalLight stays the shadow-caster.
//   3. A photographic post chain: GTAO contact shadows, DoF, restrained
//      UnrealBloom, SMAA clean edges, AgX filmic tone-mapping + a warm optics grade.

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
// RoomEnvironment is kept as a graceful FALLBACK for the studio env below (and so
// older presets still resolve); the primary IBL is now a bespoke softbox scene.
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { RectAreaLightUniformsLib } from 'three/addons/lights/RectAreaLightUniformsLib.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/addons/postprocessing/GTAOPass.js';
import { BokehPass } from 'three/addons/postprocessing/BokehPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { SMAAPass } from 'three/addons/postprocessing/SMAAPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { surfaceNormalMap } from './apparatus/lib.js';

// A warm screen-space "optics" pass: radial chromatic aberration that grows
// toward the edge, a soft vignette, and animated sensor grain. Unlike the
// pondwater dark-field scope this keeps the tungsten warmth (no cool white
// balance) so the 1953 bench reads like warm film, not a microscope feed.
const OpticsShader = {
  uniforms: {
    tDiffuse: { value: null },
    uTime: { value: 0 },
    uAberration: { value: 1.4 },
    uVignette: { value: 0.4 },
    uGrain: { value: 0.03 },
    uResolution: { value: new THREE.Vector2(1, 1) },
  },
  vertexShader: /* glsl */`
    varying vec2 vUv;
    void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }
  `,
  fragmentShader: /* glsl */`
    varying vec2 vUv;
    uniform sampler2D tDiffuse;
    uniform float uTime, uAberration, uVignette, uGrain;
    uniform vec2 uResolution;
    float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
    void main() {
      vec2 c = vUv - 0.5;
      float r = length(c);
      // radial chromatic aberration — clean at centre, fringed at the rim
      vec2 shift = c * r * (uAberration * 4.0 / uResolution.x);
      float cr = texture2D(tDiffuse, vUv + shift).r;
      float cg = texture2D(tDiffuse, vUv).g;
      float cb = texture2D(tDiffuse, vUv - shift).b;
      vec3 col = vec3(cr, cg, cb);
      // a hair of desaturation — keep the warmth, don't cool it
      float l = dot(col, vec3(0.299, 0.587, 0.114));
      col = mix(vec3(l), col, 0.92);
      // vignette
      col *= 1.0 - smoothstep(0.32, 0.82, r) * uVignette;
      // animated sensor grain
      col += (hash(vUv * uResolution + uTime) - 0.5) * uGrain;
      gl_FragColor = vec4(col, 1.0);
    }
  `,
};

// RectAreaLight needs its BRDF LUTs uploaded once before any area light is used.
// Runs only in the browser (needs a GL context); the headless tests never call
// createLab(), so this is import-safe.
RectAreaLightUniformsLib.init();

export function createLab(container) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(container.clientWidth, container.clientHeight);
  // AgX is a more photographic, gently-rolled filmic curve than ACES — it holds
  // highlight detail in the softbox reflections instead of clipping them white.
  // AgX renders darker than ACES, so exposure is nudged up to compensate.
  renderer.toneMapping = THREE.AgXToneMapping;
  renderer.toneMappingExposure = 1.15;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  // low-power proxy: SwiftShader / weak GPUs report a small max texture size; we
  // drop the two heaviest passes (GTAO + DoF) on those to keep the lab smooth.
  const lowPower = renderer.capabilities.maxTextureSize < 8192;
  container.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x07090d); // obsidian — the same receiving dark as the shell

  // ── Studio softbox IBL ──────────────────────────────────────────────────
  // The single biggest flat-glass → real-glass win is what the glass has to
  // reflect. Instead of a neutral RoomEnvironment we bake a bespoke STUDIO: a
  // black room with a few emissive softbox panels (warm keys + a cool back
  // panel). Baked at a TIGHT PMREM sigma (0.02) so the panels stay crisp
  // rectangles rolling across the borosilicate — the studio-photo signature.
  // RoomEnvironment is retained as a graceful fallback if the bake ever fails.
  const pmrem = new THREE.PMREMGenerator(renderer);
  pmrem.compileEquirectangularShader();
  let envTex;
  try {
    envTex = pmrem.fromScene(makeStudioEnv(), 0.02).texture;
  } catch (e) {
    // fromScene's 2nd arg is blur SIGMA, not intensity — RoomEnvironment fallback.
    envTex = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  }
  scene.environment = envTex;
  scene.environmentIntensity = 1.2;   // crisp, slightly brighter image-based lighting
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

  // ── Softbox area lights: the crisp rectangular reflections that read as a
  //    real studio shoot. RectAreaLight casts no shadow (the DirectionalLight
  //    above stays the shadow-caster) but delivers physically-soft panel
  //    reflections rolling across the glass and steel. Each faces the specimen.
  const softbox = (color, intensity, w, h, pos) => {
    const l = new THREE.RectAreaLight(color, intensity, w, h);
    l.position.set(pos[0], pos[1], pos[2]);
    l.lookAt(0, 2.6, 0);
    scene.add(l);
    return l;
  };
  const keyL = softbox(0xfff2e0, 11, 6, 4, [-6.5, 6.5, 4.5]);   // warm upper-left key
  const keyR = softbox(0xfff2e0, 9,  6, 4, [ 6.5, 6.0, 4.0]);   // warm upper-right key
  const rimBack = softbox(0xbfd4ff, 6, 5, 3.5, [0, 5.2, -5.5]); // cool rim from behind

  // ── Bench + backdrop so the glass has a real environment to refract ─────
  // Cooled toward obsidian so the surfaces recede into the void; the warm key
  // + lamp still pool on the bench, defining the glass without a brown stage.
  const benchMat = new THREE.MeshStandardMaterial({ color: 0x14110d, roughness: 0.78, metalness: 0.05 });
  // a micro-grain normal so the bench catches the softboxes as a textured wood
  // surface, not a mirror-flat plane (the flat-PBR CG tell). Faint + broad.
  benchMat.normalMap = surfaceNormalMap({ kind: 'fbm', freq: 3, strength: 0.5, seed: 7 });
  benchMat.normalMap.repeat.set(8, 5);
  benchMat.normalScale = new THREE.Vector2(0.15, 0.15);
  const bench = new THREE.Mesh(new THREE.BoxGeometry(40, 0.4, 24), benchMat);
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

  // ── Postprocessing: AO → DoF → bloom → AA → tone → warm optics ──────────
  // RenderPass → GTAOPass (contact-shadow AO: the "grounded" cue) → BokehPass
  // (real photographic focal plane) → UnrealBloomPass (restrained spark halo) →
  // SMAAPass (clean edges — kills the jaggy CG tell) → OutputPass (AgX tone) →
  // OpticsShader (warm-film aberration/vignette/grain). GTAO + DoF are the two
  // heaviest passes and are skipped on the low-power path.
  const W = container.clientWidth, H = container.clientHeight;
  const composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, camera));

  let gtao = null;
  if (!lowPower) {
    gtao = new GTAOPass(scene, camera, W, H);
    gtao.output = GTAOPass.OUTPUT.Default;
    gtao.blendIntensity = 0.9;
    gtao.updateGtaoMaterial({ radius: 0.5, distanceExponent: 1.0, thickness: 1.0, scale: 1.0, samples: 16 });
    composer.addPass(gtao);
  }

  let bokeh = null;
  if (!lowPower) {
    bokeh = new BokehPass(scene, camera, {
      focus: camera.position.distanceTo(controls.target),
      aperture: 0.00025, maxblur: 0.004,
      width: W, height: H,
    });
    composer.addPass(bokeh);
  }

  const bloom = new UnrealBloomPass(new THREE.Vector2(W, H), 0.75, 0.5, 0.82);
  composer.addPass(bloom);

  const smaa = new SMAAPass(W, H);
  composer.addPass(smaa);

  composer.addPass(new OutputPass());

  const optics = new ShaderPass(OpticsShader);
  optics.uniforms.uResolution.value.set(W, H);
  composer.addPass(optics);

  // Retarget the focal plane onto whatever the camera is looking at, and advance
  // the grain — done here so main.js's render call needs no change.
  const _render = composer.render.bind(composer);
  let frame = 0;
  composer.render = (deltaTime) => {
    if (bokeh) bokeh.uniforms.focus.value = camera.position.distanceTo(controls.target);
    optics.uniforms.uTime.value = (frame = (frame + 1) % 100000);
    _render(deltaTime);
  };

  function setSize() {
    const w = container.clientWidth, h = container.clientHeight;
    // In Experiment view the lab pane is display:none → clientWidth/Height are 0.
    // Skip the resize then (camera.aspect would be NaN); the next switch back to
    // lab/split re-runs setSize with real dims. Guards against a 0×0 renderer.
    if (w === 0 || h === 0) return;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
    composer.setSize(w, h);      // cascades to bloom + smaa + optics render targets
    if (gtao) gtao.setSize(w, h);
    if (smaa && typeof smaa.setSize === 'function') smaa.setSize(w, h);
    optics.uniforms.uResolution.value.set(w, h);
  }
  window.addEventListener('resize', setSize);

  return { THREE, renderer, scene, camera, controls, composer, gtao, bokeh, smaa, optics, setSize };
}

// ── Studio softbox environment (baked to the IBL via PMREM) ─────────────────
// A black room with a handful of bright emissive panels — the studio the glass
// reflects. Warm key panels upper-left/-right, a cool fill panel behind, and a
// dim floor/ceiling so reflections have vertical structure. Baked at a tight
// PMREM sigma so each panel reads as a crisp rectangle on the borosilicate.
function makeStudioEnv() {
  const env = new THREE.Scene();
  env.background = new THREE.Color(0x000000);
  const panel = (color, intensity, w, h, pos, look) => {
    const m = new THREE.Mesh(
      new THREE.PlaneGeometry(w, h),
      new THREE.MeshBasicMaterial({ color: new THREE.Color(color).multiplyScalar(intensity), side: THREE.DoubleSide }),
    );
    m.position.set(pos[0], pos[1], pos[2]);
    if (look) m.lookAt(look[0], look[1], look[2]);
    env.add(m);
  };
  // warm key softboxes
  panel(0xfff2e0, 3.2, 8, 5, [-7, 6, 5], [0, 2.6, 0]);
  panel(0xfff0dc, 2.4, 8, 5, [ 7, 5.5, 4.5], [0, 2.6, 0]);
  // cool rim/fill from behind
  panel(0xbfd4ff, 1.8, 7, 4, [0, 5, -6], [0, 2.6, 0]);
  // faint warm ground bounce + a soft ceiling wash for vertical reflection structure
  panel(0x2a2016, 0.9, 20, 20, [0, -2, 0], [0, 1, 0]);
  panel(0x141821, 0.6, 20, 20, [0, 12, 0], [0, 1, 0]);
  return env;
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
