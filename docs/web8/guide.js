// web8 — the living amoeba guide (V0: idle breathe / blink / wandering gaze).
//
// Procedural, in web7's Catalytic-Silence dress (a single teal specimen on the
// obsidian ground). Rendered on a pointer-events:none overlay canvas pinned to
// the specimen, so it never blocks the apparatus or controls. Respects
// prefers-reduced-motion. Self-mounts; no dependency on main.js internals (yet).
//
// Later phases (see ../design/WEB8_PLAN.md) add speech bubbles (narration),
// pointing, and the "ask the amoeba" control layer.

import { blobPoints, gazeOffset } from './blobgeom.js';

const TEAL = [57, 212, 200]; // #39d4c8
const TEAL_HI = [94, 231, 220]; // #5ee7dc
const EYE = [253, 246, 227]; // #fdf6e3
const PUPIL = [10, 14, 22]; // #0a0e16
const TAU = Math.PI * 2;
const rgba = (c, a = 1) => `rgba(${c[0]},${c[1]},${c[2]},${a})`;
const reduce = window.matchMedia('(prefers-reduced-motion: reduce)');

function mount() {
  const host = document.querySelector('.specimen') || document.body;
  if (getComputedStyle(host).position === 'static') host.style.position = 'relative';

  const cv = document.createElement('canvas');
  cv.className = 'amoeba-guide';
  cv.setAttribute('aria-hidden', 'true'); // narration (V1) carries the meaning for AT
  host.appendChild(cv);
  const ctx = cv.getContext('2d');

  const SIZE = 120; // CSS px
  function resize() {
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    cv.width = SIZE * dpr;
    cv.height = SIZE * dpr;
    cv.style.width = SIZE + 'px';
    cv.style.height = SIZE + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  resize();
  window.addEventListener('resize', resize);

  const seed = 0xce11;
  let frame = 0;

  const poly = (pts) => {
    ctx.beginPath();
    pts.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
    ctx.closePath();
  };

  function draw() {
    ctx.clearRect(0, 0, SIZE, SIZE);
    const cx = SIZE / 2;
    const cy = SIZE / 2;
    const r = SIZE * 0.36;
    const rx = r;
    const ry = r * 0.96;
    const f = reduce.matches ? 0 : frame; // frozen pose under reduced motion
    const bob = Math.sin(f * 0.11) * (ry * 0.05);
    const breath = Math.sin(f * 0.08) * 0.06;
    const mem = f * 0.06;
    const cyb = cy + bob;
    const bx = rx * (1 + breath);
    const by = ry * (1 - breath * 0.6);

    // membrane + 3D sheen
    poly(blobPoints(cx, cyb, bx, by, { seed, phase: mem }));
    ctx.fillStyle = rgba(TEAL);
    ctx.fill();
    poly(
      blobPoints(cx - bx * 0.3, cyb - by * 0.4, bx * 0.44, by * 0.34, {
        seed: seed ^ 0x5eed,
        phase: mem * 0.8,
        wobble: 0.1,
      }),
    );
    ctx.fillStyle = rgba(TEAL_HI, 0.82);
    ctx.fill();

    // eyes + wandering gaze
    const ew = r * 0.18;
    const pr = ew * 0.5;
    const edx = r * 0.2;
    const edy = -ry * 0.12;
    const blink = !reduce.matches && frame % 220 < 7;
    const [gx, gy] = gazeOffset(f, seed, ew - pr - 1);
    for (const s of [-1, 1]) {
      const ex = cx + s * edx;
      const ey = cyb + edy;
      ctx.fillStyle = rgba(EYE);
      ctx.beginPath();
      ctx.ellipse(ex, ey, ew, blink ? Math.max(1, ew * 0.12) : ew, 0, 0, TAU);
      ctx.fill();
      if (!blink) {
        ctx.fillStyle = rgba(PUPIL);
        ctx.beginPath();
        ctx.arc(ex + gx, ey + gy, pr, 0, TAU);
        ctx.fill();
      }
    }

    // smile
    ctx.strokeStyle = rgba(PUPIL);
    ctx.lineWidth = Math.max(2, r * 0.06);
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.arc(cx, cyb + ry * 0.08, r * 0.26, 0.18 * Math.PI, 0.82 * Math.PI);
    ctx.stroke();
  }

  // Animation controller: loop only when motion is allowed (perf + a11y).
  let running = false;
  function loop() {
    if (!running) return;
    frame++;
    draw();
    requestAnimationFrame(loop);
  }
  function sync() {
    if (reduce.matches) {
      running = false;
      draw();
    } else if (!running) {
      running = true;
      requestAnimationFrame(loop);
    }
  }
  sync();
  reduce.addEventListener?.('change', sync);
}

if (document.readyState !== 'loading') mount();
else window.addEventListener('DOMContentLoaded', mount);
