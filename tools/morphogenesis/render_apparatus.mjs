// render_apparatus.mjs — offscreen renderer for the web8 3-D lab apparatus.
// Headless WebGL via node 'gl' (run under xvfb-run) + three. Replicates scene.js lighting/IBL,
// builds one apparatus, runs its animation, orbits the camera, dumps RGBA frames.
//   xvfb-run -a node tools/morphogenesis/render_apparatus.mjs <id> <frames> <W> <H>
//   -> /tmp/app_<id>.bin (RGBA, top-left origin) + /tmp/app_<id>_meta.json
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { createRequire } from 'module';
import fs from 'fs';
const require = createRequire(import.meta.url);
const createGL = require('gl');
// ── DOM shim: the apparatus build dynamic 2-D canvas textures (dish films, gauges, labels) ──
const { createCanvas, Canvas, ImageData: NCImageData, Image: NCImage } = require('canvas');
globalThis.HTMLCanvasElement = Canvas;                 // so three takes the canvas-upload path
globalThis.ImageData = NCImageData; globalThis.Image = NCImage;
globalThis.document = {
  createElement(t) { return t === 'canvas' ? createCanvas(1, 1) : { style: {}, getContext: () => null, appendChild() {}, setAttribute() {} }; },
  createElementNS(ns, t) { return this.createElement(t); },
  body: { appendChild() {} },
};
globalThis.window = { devicePixelRatio: 1, addEventListener() {}, removeEventListener() {}, matchMedia: () => ({ matches: false, addEventListener() {} }) };

const ID = process.argv[2];
const FRAMES = +(process.argv[3] || 120);
const W = +(process.argv[4] || 1000);
const H = +(process.argv[5] || 760);

const gl = createGL(W, H, { preserveDrawingBuffer: true, antialias: true });
if (!gl) { console.error('NULL GL CONTEXT (run under xvfb-run)'); process.exit(1); }
const canvas = { width: W, height: H, style: {}, addEventListener() {}, removeEventListener() {}, getContext() { return gl; } };
const renderer = new THREE.WebGLRenderer({ canvas, context: gl, antialias: true });
renderer.setSize(W, H, false);
renderer.setPixelRatio(1);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.95;
try { renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap; } catch (e) {}

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x07090d);
// IBL — crucial for the physical glass. Guard it: if half-float RTs misbehave on WebGL1, fall back to lights only.
try {
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  pmrem.dispose();
} catch (e) { console.error('PMREM unavailable, lights only:', e.message); }

const camera = new THREE.PerspectiveCamera(42, W / H, 0.1, 100);
const target = new THREE.Vector3(0, 2.6, 0);

// ── lights copied verbatim from scene.js ──
const key = new THREE.DirectionalLight(0xffd29a, 2.6); key.position.set(-5, 7, 5);
key.castShadow = true; key.shadow.mapSize.set(2048, 2048);
key.shadow.camera.near = 1; key.shadow.camera.far = 30;
key.shadow.camera.left = -8; key.shadow.camera.right = 8; key.shadow.camera.top = 8; key.shadow.camera.bottom = -8;
key.shadow.bias = -0.0004; key.shadow.radius = 4; scene.add(key);
const rim = new THREE.DirectionalLight(0xb9c4e0, 0.30); rim.position.set(6, 4, -5); scene.add(rim);
scene.add(new THREE.HemisphereLight(0xffe1b4, 0x0b0e13, 0.35));
const lamp = new THREE.PointLight(0xffb866, 16, 9, 2); lamp.position.set(-4.2, 1.6, 2.2); scene.add(lamp);
// a little extra fill so the apparatus reads even if IBL is weak headless
const fill = new THREE.DirectionalLight(0xfff2e0, 0.5); fill.position.set(2, 5, 7); scene.add(fill);

const bench = new THREE.Mesh(new THREE.BoxGeometry(40, 0.4, 24),
  new THREE.MeshStandardMaterial({ color: 0x14110d, roughness: 0.78, metalness: 0.05 }));
bench.position.y = -0.2; bench.receiveShadow = true; scene.add(bench);
const wall = new THREE.Mesh(new THREE.PlaneGeometry(40, 24),
  new THREE.MeshStandardMaterial({ color: 0x0a0d12, roughness: 0.96 }));
wall.position.set(0, 8, -7); scene.add(wall);

const mod = await import(`../../docs/web8/apparatus/${ID}.js`);
const meta = mod.meta || {};
const group = (meta.build || mod.build)();
// headless-gl is WebGL1 → MeshPhysicalMaterial transmission won't render (glass goes invisible).
// Convert transmissive glass to frosted translucent standard material so the forms read.
group.traverse((o) => {
  if (o.isMesh) {
    o.castShadow = true; o.receiveShadow = true;
    const ms = Array.isArray(o.material) ? o.material : [o.material];
    ms.forEach((m) => {
      if (m && m.transmission > 0) {
        m.transmission = 0; m.transparent = true; m.opacity = 0.55;
        m.roughness = Math.max(0.12, m.roughness || 0.1); m.metalness = 0;
        if (!m.map) m.color = new THREE.Color(0xe8eef0);
        m.needsUpdate = true;
      }
    });
  }
});
scene.add(group);
const anim = group.userData && group.userData.anim;
if (anim && anim.reset) try { anim.reset(); } catch (e) {}
if (anim && anim.setRunning) try { anim.setRunning(true); } catch (e) {}

const buf = new Uint8Array(W * H * 4);
const row = Buffer.alloc(W * 4);
const fd = fs.openSync(`/tmp/app_${ID}.bin`, 'w');
const dt = 1 / 24; let t = 0; const t0 = Date.now();
// warm the animation a little so it isn't mid-pop at frame 0
for (let i = 0; i < 40; i++) { if (anim && anim.update) try { anim.update(dt, t); } catch (e) {} t += dt; }
for (let f = 0; f < FRAMES; f++) {
  const p = f / FRAMES;
  const ang = -0.55 + 1.05 * p;                 // slow turntable, ~90°
  const rad = 7.6 - 0.8 * Math.sin(p * Math.PI); // gentle push-in mid-shot
  camera.position.set(Math.sin(ang) * rad, 3.5 + 0.5 * Math.sin(p * Math.PI), Math.cos(ang) * rad);
  camera.lookAt(target);
  if (anim && anim.update) try { anim.update(dt, t); } catch (e) {} t += dt;
  renderer.render(scene, camera);
  gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, buf);
  const out = Buffer.from(buf.buffer, buf.byteOffset, buf.byteLength);
  for (let y = 0; y < (H >> 1); y++) {           // flip vertically (GL origin = bottom-left)
    const top = y * W * 4, bot = (H - 1 - y) * W * 4;
    out.copy(row, 0, top, top + W * 4);
    out.copy(out, top, bot, bot + W * 4);
    row.copy(out, bot, 0, W * 4);
  }
  fs.writeSync(fd, out);
  if (f % 30 === 0) console.log(ID, 'frame', f, ((Date.now() - t0) / 1000).toFixed(0) + 's');
}
fs.closeSync(fd);
fs.writeFileSync(`/tmp/app_${ID}_meta.json`, JSON.stringify({
  id: ID, frames: FRAMES, W, H,
  title: meta.title || meta.label || ID, blurb: meta.blurb || '',
}));
console.log(ID, 'DONE', FRAMES, 'frames', W + 'x' + H);
