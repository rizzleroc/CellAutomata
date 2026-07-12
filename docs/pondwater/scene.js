// Pond Water Analyzer — the microscope stage.
//
// The look is a dark-field wet-mount: the specimen is lit against a deep
// blue-black field of water, the way a real dark-field condenser throws light
// so only what scatters it glows. Suspended detritus and marine snow drift in
// the medium; a soft caustic gradient stands in for the condenser cone. The
// same photoreal pillars the rest of the lab uses — PBR image-based lighting,
// ACES tone-mapping, a restrained bloom so the wet highlights bloom like glass.
//
// What sells "under a microscope" over "a nice 3D model" is the *optics*, not
// the geometry: a real objective has a razor-thin focal plane (everything else
// falls into soft bokeh), it fringes high-contrast edges with chromatic
// aberration, the sensor adds grain, and the field vignettes. Those live in the
// post chain below — depth-of-field (focus tracked to the specimen), a light
// chromatic-aberration + grain + vignette + cool-cast pass, and the bloom that
// turns dark-field's bright refractive edges into glowing haloes.

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { BokehPass } from 'three/addons/postprocessing/BokehPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

// A single screen-space "optics" pass: radial chromatic aberration that grows
// toward the edge, a cool desaturating colour cast (the microscope's white
// balance), a soft vignette, and animated sensor grain. Cheap — one draw.
const OpticsShader = {
  uniforms: {
    tDiffuse: { value: null },
    uTime: { value: 0 },
    uAberration: { value: 2.2 },
    uVignette: { value: 0.55 },
    uGrain: { value: 0.055 },
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
      // cool white balance + gentle desaturation of the whole field
      float l = dot(col, vec3(0.299, 0.587, 0.114));
      col = mix(vec3(l), col, 0.88) * vec3(0.975, 1.0, 1.045);
      // vignette
      col *= 1.0 - smoothstep(0.32, 0.82, r) * uVignette;
      // animated sensor grain
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

  // ── Postprocessing: DoF → bloom → tone → optics ─────────────────────────
  const composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, camera));

  // Depth of field: the thin focal plane that reads as "under a microscope".
  // focus (world distance) is retargeted to the specimen every frame below.
  const bokeh = new BokehPass(scene, camera, {
    focus: 9, aperture: 0.00035, maxblur: 0.006,
    width: container.clientWidth, height: container.clientHeight,
  });
  composer.addPass(bokeh);

  const bloom = new UnrealBloomPass(
    new THREE.Vector2(container.clientWidth, container.clientHeight),
    0.7, 0.75, 0.72,          // dark-field refractive edges bloom into haloes
  );
  composer.addPass(bloom);
  composer.addPass(new OutputPass());

  const optics = new ShaderPass(OpticsShader);
  optics.uniforms.uResolution.value.set(container.clientWidth, container.clientHeight);
  composer.addPass(optics);

  // Drive the focal plane onto whatever the camera is looking at, and advance
  // the grain — done here so main.js's render call needs no change.
  const _render = composer.render.bind(composer);
  let frame = 0;
  composer.render = (deltaTime) => {
    bokeh.uniforms['focus'].value = camera.position.distanceTo(controls.target);
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

  return { THREE, renderer, scene, camera, controls, composer, bokeh, optics, medium, spot, setSize };
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
