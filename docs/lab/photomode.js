// photomode.js — PHOTO-DEVELOP MODE: the real breakthrough.
//
// Everything else in the lab is *rasterized* WebGL — fast, but it FAKES the two
// things that make glassware read as a photograph: refraction through the glass
// and caustics cast onto the bench. This module drops in a real **GPU path
// tracer** (three-gpu-pathtracer, on three-mesh-bvh) that computes true light
// transport — real refraction, real caustics, real global illumination, real
// soft contact shadows — and converges progressively.
//
// Behaviour is "photo-develop": while the sim runs or the camera moves we stay
// on the fast raster composer. The instant the sim is stopped AND the camera is
// held still, the apparatus "develops" — accumulating path-traced samples over
// ~1–2 s into a genuinely photographic still — then snaps back to the live view
// on any interaction.
//
// ── Why this file is isolated ────────────────────────────────────────────────
// It is the ONLY module that references the path tracer. The heavy tracer bundle
// is pulled in by a *lazy dynamic import* the first time you develop, so nothing
// is fetched at page load. And because the zero-dependency test gates import the
// apparatus modules (never this one), they never try to resolve the extra CDN
// deps. main.js dynamic-import()s createPhotoMode after the lab boots.

import * as THREE from 'three';

// ── A procedural studio environment ──────────────────────────────────────────
// The light the path tracer samples. Built entirely in code (no HDRI asset, no
// network): an obsidian-to-grey vertical gradient with three bright soft "boxes"
// (two warm keys + a cool rim). Their reflections rolling across the glass are
// what read as a real product-photography shoot. Deterministic + canvas-free.
const _dir = new THREE.Vector3();
function studioEnvironment(GradientEquirectTexture) {
  const env = new GradientEquirectTexture(1024);
  env.topColor.set(0x2b3038);      // soft grey ceiling bounce
  env.bottomColor.set(0x05060a);   // obsidian floor — matches the scene background
  env.exponent = 1.6;

  const key = new THREE.Color(0xfff1dc);   // warm tungsten softboxes
  const cool = new THREE.Color(0xbcd6ff);  // cool rim
  const boxes = [
    { d: new THREE.Vector3(-0.75, 0.72, 0.45).normalize(), spread: 0.20, c: key,  i: 9.0 }, // key
    { d: new THREE.Vector3( 0.85, 0.48, 0.55).normalize(), spread: 0.26, c: key,  i: 5.0 }, // fill
    { d: new THREE.Vector3( 0.15, 0.42, -0.95).normalize(), spread: 0.22, c: cool, i: 5.5 }, // rim
  ];

  env.generationCallback = (polar, _uv, _coord, color) => {
    _dir.setFromSpherical(polar);
    const t = _dir.y * 0.5 + 0.5;
    color.lerpColors(env.bottomColor, env.topColor, Math.pow(t, env.exponent));
    for (const b of boxes) {
      const d = _dir.dot(b.d);                       // 1 = looking straight at the box
      const edge = 1 - b.spread;
      if (d <= edge) continue;
      const m = Math.pow((d - edge) / b.spread, 2) * b.i;
      color.r += b.c.r * m; color.g += b.c.g * m; color.b += b.c.b * m;
    }
  };
  env.update();
  return env;
}

// ── The status chip ──────────────────────────────────────────────────────────
// Lives in the existing token system (teal accent, Plex Mono) so the design gate
// is untouched; created in JS, positioned bottom-centre of the viewport.
function makeChip(mount) {
  if (getComputedStyle(mount).position === 'static') mount.style.position = 'relative';
  const el = document.createElement('div');
  el.className = 'photo-chip';
  Object.assign(el.style, {
    position: 'absolute', left: '50%', bottom: '16px', transform: 'translateX(-50%)',
    display: 'none', alignItems: 'center', gap: '8px', padding: '7px 15px',
    font: "600 10.5px/1 'IBM Plex Mono', ui-monospace, monospace",
    letterSpacing: '.16em', textTransform: 'uppercase', whiteSpace: 'nowrap',
    color: 'var(--ink, #e9e4d6)', background: 'rgba(8,10,14,.74)',
    backdropFilter: 'blur(8px)', WebkitBackdropFilter: 'blur(8px)',
    border: '1px solid rgba(120,220,205,.30)', borderRadius: '999px',
    boxShadow: '0 12px 34px rgba(0,0,0,.5)', zIndex: '7', pointerEvents: 'none',
    opacity: '0', transition: 'opacity .35s ease, border-color .35s ease',
  });
  mount.appendChild(el);
  let visible = false, hideT = 0;
  return {
    get visible() { return visible; },
    show(text) {
      el.textContent = text; el.style.display = 'flex';
      clearTimeout(hideT); requestAnimationFrame(() => (el.style.opacity = '1'));
      visible = true;
    },
    done() {
      el.textContent = '✓ photoreal plate';
      el.style.borderColor = 'rgba(120,220,205,.65)';
    },
    hide() {
      el.style.opacity = '0'; el.style.borderColor = 'rgba(120,220,205,.30)';
      visible = false;
      hideT = setTimeout(() => { if (!visible) el.style.display = 'none'; }, 380);
    },
  };
}

// ── The controller ───────────────────────────────────────────────────────────
export function createPhotoMode({ lab, mount, getView, isRunning }) {
  const { renderer, scene, camera, controls } = lab;

  // Feature gate: path tracing needs a real WebGL2 GPU. On WebGL1 or a
  // software/low-power context we stay on the (already improved) raster view.
  const gl = renderer.getContext();
  const isWebGL2 = typeof WebGL2RenderingContext !== 'undefined' && gl instanceof WebGL2RenderingContext;
  const lowPower = renderer.capabilities.maxTextureSize < 8192;
  const supported = isWebGL2 && !lowPower;

  const chip = supported ? makeChip(mount) : null;

  const SETTLE_MS = 380;     // hold-still time before we start developing
  const SAMPLE_CAP = 160;    // samples at which we call the plate "converged"

  let tracer = null, env = null, ptlib = null;
  let developing = false, converged = false, loading = false, broken = false;
  let interacting = false, stillMs = 0;
  let savedEnv, envSwapped = false;
  const lastPos = new THREE.Vector3();
  const lastQuat = new THREE.Quaternion();
  let havePose = false;

  // Any interaction drops us to the fast raster view instantly; when it ends the
  // settle timer re-arms. Damping keeps the camera moving a few frames after
  // 'end', which poseMoved() already absorbs before developing begins.
  controls.addEventListener('start', () => { interacting = true; stillMs = 0; invalidate(); });
  controls.addEventListener('end', () => { interacting = false; });
  // A resize invalidates the tracer's render targets — rebuild on the next develop.
  window.addEventListener('resize', () => {
    if (developing || converged) { restoreEnv(); developing = false; converged = false; chip?.hide(); }
  });

  function want() {
    return supported && !broken && getView() === 'lab' && !isRunning() && !interacting;
  }

  // Returns true if the camera moved appreciably since the last check.
  function poseMoved() {
    const p = camera.position, q = camera.quaternion;
    if (!havePose) { lastPos.copy(p); lastQuat.copy(q); havePose = true; return true; }
    const moved = p.distanceToSquared(lastPos) > 1e-8 || Math.abs(lastQuat.dot(q)) < 0.999999;
    if (moved) { lastPos.copy(p); lastQuat.copy(q); }
    return moved;
  }

  function swapEnv() {
    if (envSwapped) return;
    savedEnv = scene.environment;
    if (!env && ptlib) env = studioEnvironment(ptlib.GradientEquirectTexture);
    if (env) scene.environment = env;   // the tracer samples scene.environment
    envSwapped = true;
  }
  function restoreEnv() {
    if (!envSwapped) return;
    scene.environment = savedEnv;
    envSwapped = false;
  }

  function invalidate() {
    restoreEnv();
    if (developing || converged) chip?.hide();
    developing = false; converged = false;
  }

  async function ensureLib() {
    if (ptlib) return ptlib;
    if (loading) return null;
    loading = true;
    chip?.show('◉ loading renderer…');
    try {
      ptlib = await import('three-gpu-pathtracer');   // lazy: only on first develop
    } catch (err) {
      console.warn('[cellauto] path tracer failed to load:', err);
      ptlib = null;
    } finally {
      loading = false;
    }
    return ptlib;
  }

  async function build() {
    const L = await ensureLib();
    if (!L) return false;
    if (!tracer) {
      tracer = new L.WebGLPathTracer(renderer);
      tracer.tiles.set(3, 3);                 // split the frame so the tab stays responsive
      tracer.renderScale = 0.8;               // near-native; the trace is already clean
      tracer.renderDelay = 0;
      tracer.fadeDuration = 0;
      try {
        tracer.bounces = 8;
        tracer.transmissiveBounces = 12;      // deep glass — the caustics live here
        tracer.filterGlossyFactor = 0.5;      // tame fireflies without killing caustics
        tracer.multipleImportanceSampling = true;
      } catch (_) { /* older API — defaults are fine */ }
    }
    try {
      swapEnv();
      tracer.setScene(scene, camera);         // synchronous BVH build (one-time per stop)
      return true;
    } catch (err) {
      // A GPU/driver that can't run the tracer's shaders must never wedge the
      // app — mark it broken and stay on the raster view for good.
      console.warn('[cellauto] path trace unavailable on this GPU — staying rasterized:', err);
      broken = true; restoreEnv(); chip?.hide();
      return false;
    }
  }

  return {
    supported,
    isDeveloping: () => developing,
    active: () => developing && !!tracer,
    sampleCount: () => (tracer ? Math.round(tracer.samples || 0) : 0),
    _diag: () => ({ supported, broken, developing, converged, loading, interacting,
      stillMs: Math.round(stillMs), lib: !!ptlib, want: want(),
      view: getView(), running: isRunning() }),
    // Diagnostic only (headless verification): skip the settle wait and develop now.
    _forceDevelop: async () => { if (await build()) { developing = true; converged = false; } },

    // Called every frame (before the render decision) with the frame delta.
    async update(dt) {
      if (!want()) { if (developing || converged || chip?.visible) invalidate(); return; }

      if (poseMoved()) {                       // camera still settling / user orbiting
        stillMs = 0;
        if (developing || converged) { restoreEnv(); developing = false; converged = false; chip?.hide(); }
        return;
      }

      stillMs += dt * 1000;
      if (developing || loading) return;
      if (stillMs < SETTLE_MS) return;

      if (await build()) {
        developing = true; converged = false;
        chip?.show('◉ developing…  0');
      }
    },

    // Called instead of composer.render() while active().
    render() {
      if (!developing || !tracer) return;
      try {
        tracer.renderSample();
      } catch (err) {
        console.warn('[cellauto] path trace failed mid-render — staying rasterized:', err);
        broken = true; restoreEnv(); developing = false; converged = false; chip?.hide();
        return;
      }
      if (converged) return;
      const s = Math.round(tracer.samples || 0);
      if (s >= SAMPLE_CAP) { converged = true; chip?.done(); }
      else chip?.show('◉ developing…  ' + s);
    },

    dispose() {
      invalidate();
      try { tracer?.dispose?.(); } catch (_) {}
      env?.dispose?.();
    },
  };
}
