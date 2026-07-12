// web9 · The Instrument — landing controller.
//
// Two showpieces, both driven by the real engine so nothing here is a mock:
//   1. the SLIME STUDIO — a large, living amoeba (the guide, off-duty) you can
//      play with: it breathes, blinks, follows the pointer, and reacts to a poke.
//      Reuses blobgeom.js — the exact membrane + gaze the desktop colony uses.
//   2. LIVE PREVIEWS — one mini micrograph per experiment, each an actual rule
//      stepping through window.SEM, on a round-robin scheduler that only animates
//      visible tiles and pauses the moment you enter the lab. Click a tile to
//      enter the instrument at that stage.
//
// Zero-dependency ES module; the classic experiment scripts (window.CA.RULES +
// window.SEM) and main.js (window.WEB9) run before it.

import { blobPoints, gazeOffset } from './blobgeom.js';

const reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
const labActive = () => document.body.classList.contains('lab-active');
const $ = (id) => document.getElementById(id);

// ── 1 · the slime studio ─────────────────────────────────────────────────────
function startStudio() {
  const cv = $('slimeStudio');
  if (!cv) return;
  const ctx = cv.getContext('2d');
  const seed = 0x51e;
  let frame = 0;
  let px = 0.5, py = 0.42;          // pointer target, in canvas fractions
  let squash = 0;                    // poke reaction (0..1, decays)
  let excited = false;
  let accent = '#3fe0d0';           // teal by default; magenta on toggle

  function resize() {
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    const r = cv.getBoundingClientRect();
    cv.width = Math.max(1, Math.round(r.width * dpr));
    cv.height = Math.max(1, Math.round(r.height * dpr));
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  window.addEventListener('resize', resize);

  cv.addEventListener('pointermove', (e) => {
    const r = cv.getBoundingClientRect();
    px = (e.clientX - r.left) / r.width;
    py = (e.clientY - r.top) / r.height;
  });
  cv.addEventListener('pointerleave', () => { px = 0.5; py = 0.42; });
  cv.addEventListener('pointerdown', () => { squash = 1; });

  function smoothBlob(pts) {
    ctx.beginPath();
    const n = pts.length;
    let mx = (pts[n - 1][0] + pts[0][0]) / 2, my = (pts[n - 1][1] + pts[0][1]) / 2;
    ctx.moveTo(mx, my);
    for (let i = 0; i < n; i++) {
      const c = pts[i], nx = pts[(i + 1) % n];
      ctx.quadraticCurveTo(c[0], c[1], (c[0] + nx[0]) / 2, (c[1] + nx[1]) / 2);
    }
    ctx.closePath();
  }

  function draw() {
    const r = cv.getBoundingClientRect();
    const W = r.width, H = r.height;
    ctx.clearRect(0, 0, W, H);
    const cx = W * 0.5, cy = H * 0.52;
    const base = Math.min(W, H) * 0.3;
    const breathe = excited ? 0.05 : 0.03;
    const spd = excited ? 0.05 : 0.03;
    const sq = squash * 0.22;
    const rx = base * (1 + breathe * Math.sin(frame * spd)) * (1 + sq);
    const ry = base * (1 + breathe * Math.cos(frame * spd * 1.1)) * (1 - sq);
    const phase = frame * (excited ? 0.06 : 0.035);

    // soft ground glow
    const glow = ctx.createRadialGradient(cx, cy, base * 0.2, cx, cy, base * 1.9);
    glow.addColorStop(0, accent + '22');
    glow.addColorStop(1, 'transparent');
    ctx.fillStyle = glow;
    ctx.fillRect(0, 0, W, H);

    // membrane
    const wob = excited ? 0.18 : 0.12;
    const pts = blobPoints(cx, cy, rx, ry, { seed, phase, n: 18, wobble: wob });
    smoothBlob(pts);
    const body = ctx.createRadialGradient(cx - rx * 0.28, cy - ry * 0.34, base * 0.1, cx, cy, rx * 1.15);
    body.addColorStop(0, accent + 'e6');
    body.addColorStop(0.62, accent + '8c');
    body.addColorStop(1, accent + '2e');
    ctx.fillStyle = body;
    ctx.shadowColor = accent + '66';
    ctx.shadowBlur = 26;
    ctx.fill();
    ctx.shadowBlur = 0;
    // inner nucleus
    smoothBlob(blobPoints(cx - rx * 0.18, cy + ry * 0.12, rx * 0.42, ry * 0.4, { seed: seed ^ 0x77, phase: phase * 0.8, n: 16, wobble: 0.1 }));
    ctx.fillStyle = accent + '3a';
    ctx.fill();
    // rim light
    smoothBlob(pts);
    ctx.strokeStyle = '#eaf7f4cc';
    ctx.lineWidth = 1.4;
    ctx.stroke();

    // eyes with pointer gaze
    const eyeR = base * 0.16, eyeDx = rx * 0.34, eyeY = cy - ry * 0.14;
    const gx = (px - 0.5) * 2, gy = (py - 0.52) * 2;
    const gm = Math.min(1, Math.hypot(gx, gy));
    const [wgx, wgy] = gazeOffset(frame, seed, eyeR * 0.36);
    for (const s of [-1, 1]) {
      const ex = cx + s * eyeDx, ey = eyeY;
      ctx.fillStyle = '#f3efe4';
      ctx.beginPath(); ctx.ellipse(ex, ey, eyeR, eyeR * 1.05, 0, 0, 7); ctx.fill();
      const pxo = (gm ? gx / (gm || 1) : 0) * eyeR * 0.42 + wgx * 0.4;
      const pyo = (gm ? gy / (gm || 1) : 0) * eyeR * 0.42 + wgy * 0.4;
      // blink
      const blink = (frame % 220) < 6 ? 0.12 : 1;
      ctx.fillStyle = '#0b0f16';
      ctx.beginPath(); ctx.ellipse(ex + pxo, ey + pyo, eyeR * 0.5, eyeR * 0.5 * blink, 0, 0, 7); ctx.fill();
      if (blink > 0.5) { ctx.fillStyle = '#ffffffcc'; ctx.beginPath(); ctx.arc(ex + pxo - eyeR * 0.16, ey + pyo - eyeR * 0.18, eyeR * 0.15, 0, 7); ctx.fill(); }
    }
    // mouth — a small content curve, wider when poked
    ctx.strokeStyle = '#0b0f16aa';
    ctx.lineWidth = 2;
    ctx.beginPath();
    const mw = rx * (0.24 + squash * 0.2), my2 = cy + ry * 0.34;
    ctx.moveTo(cx - mw, my2);
    ctx.quadraticCurveTo(cx, my2 + base * (0.14 + squash * 0.12), cx + mw, my2);
    ctx.stroke();
  }

  resize();
  let running = false;
  function loop() {
    if (!running) return;
    if (!labActive()) { frame++; squash *= 0.92; draw(); }
    requestAnimationFrame(loop);
  }
  function sync() {
    if (reduce.matches) { running = false; draw(); }
    else if (!running) { running = true; requestAnimationFrame(loop); }
  }
  reduce.addEventListener?.('change', sync);
  sync();

  // studio tools
  const poke = $('slimePoke'), mood = $('slimeMood'), pal = $('slimePalette');
  if (poke) poke.onclick = () => { squash = 1; sync(); };
  if (mood) mood.onclick = () => { excited = !excited; mood.classList.toggle('on', excited); mood.textContent = excited ? 'excited' : 'calm'; sync(); };
  if (pal) pal.onclick = () => { accent = accent === '#3fe0d0' ? '#d77bff' : '#3fe0d0'; pal.classList.toggle('on', accent === '#d77bff'); sync(); };
}

// ── 2 · live experiment previews ─────────────────────────────────────────────
const DISP = 200; // preview backing resolution

// The stage catalogue. Preferred source is window.WEB9 (from main.js, with the
// lab's numerals/labels). But the previews only need the classic rule scripts +
// SEM — both CDN-free — so if the 3D lab never boots (Three.js CDN blocked, no
// WebGL) we derive the list straight from window.CA.RULES and still show live
// micrographs. Graceful degradation, not a hard dependency on the lab.
function stageList() {
  if (window.WEB9 && window.WEB9.stages && window.WEB9.stages.length) return window.WEB9.stages;
  const CA = window.CA && window.CA.RULES;
  if (!CA) return [];
  const ROMAN = ['0', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', '✦'];
  return Object.keys(CA).map((ruleId, i) => {
    let name = ruleId, label = '', numeral = ROMAN[i] != null ? ROMAN[i] : String(i);
    try {
      const r = CA[ruleId]();
      name = (r.label || ruleId).split('·')[0].trim();
      label = r.shortCaption || '';
      const mm = label.match(/stage\s+([0-9]+|[ivxlcdm]+)/i); // keep the numeral consistent with the caption
      if (mm) numeral = mm[1].toUpperCase();
    } catch (e) { /* fall back to the id/index */ }
    return { id: ruleId, ruleId, name, label, numeral };
  });
}

function buildPreviews() {
  const grid = $('expGrid');
  const stages = stageList();
  const CA = window.CA && window.CA.RULES;
  const SEM = window.SEM;
  if (!grid || !stages.length || grid.childElementCount) return;

  const tiles = [];
  const active = new Set();

  for (const st of stages) {
    const tile = document.createElement('button');
    tile.type = 'button';
    tile.className = 'lp-tile';
    tile.setAttribute('aria-label', `Enter the instrument at ${st.name}`);
    const holder = document.createElement('div');
    holder.className = 'lp-tile-canvas';
    const canvas = document.createElement('canvas');
    canvas.width = DISP; canvas.height = DISP;
    holder.appendChild(canvas);
    holder.insertAdjacentHTML('beforeend',
      `<span class="lp-tile-num">${st.numeral || ''}</span>` +
      `<span class="lp-tile-badge"><span class="rec"></span>live</span>`);
    tile.appendChild(holder);
    tile.insertAdjacentHTML('beforeend',
      `<div class="lp-tile-meta"><div class="lp-tile-name">${st.name}</div>` +
      `<div class="lp-tile-cap">${st.label || ''}</div></div>`);
    tile.onclick = () => enter(st.id);
    grid.appendChild(tile);

    const rec = { st, canvas, tctx: canvas.getContext('2d'), rule: null, off: null, offCtx: null, offImg: null, hbuf: null, warm: 0, ready: false };
    tiles.push(rec);
  }

  function ensure(rec) {
    if (rec.ready || !CA || !SEM) return rec.ready;
    const factory = rec.st.ruleId && CA[rec.st.ruleId];
    if (typeof factory !== 'function') return false;
    try {
      const rule = factory();
      rule.reset();
      const w = rule.width, h = rule.height;
      const off = document.createElement('canvas'); off.width = w; off.height = h;
      const offCtx = off.getContext('2d');
      rec.rule = rule; rec.off = off; rec.offCtx = offCtx;
      rec.offImg = offCtx.createImageData(w, h);
      rec.hbuf = new Float32Array(w * h);
      rec.ready = true;
    } catch (e) { rec.ready = false; }
    return rec.ready;
  }

  function render(rec) {
    const rule = rec.rule;
    try {
      // a few steps per visit → the tiles bloom to life, cheaply
      for (let i = 0; i < 2; i++) rule.step();
      rec.warm += 2;
      rule.renderHeight(rec.hbuf);
      SEM.render(rec.hbuf, rule.width, rule.height, rec.offImg.data, { palette: 'warm-sepia' });
      rec.offCtx.putImageData(rec.offImg, 0, 0);
      rec.tctx.imageSmoothingEnabled = true;
      rec.tctx.imageSmoothingQuality = 'high';
      rec.tctx.drawImage(rec.off, 0, 0, rule.width, rule.height, 0, 0, DISP, DISP);
    } catch (e) { /* a misbehaving rule shouldn't take down the grid */ }
  }

  // Only animate what's on screen; prewarm a little before it scrolls in.
  const io = new IntersectionObserver((entries) => {
    for (const e of entries) {
      const rec = tiles.find((t) => t.canvas === e.target || t.canvas.parentElement === e.target);
      if (!rec) continue;
      if (e.isIntersecting) active.add(rec); else active.delete(rec);
    }
  }, { rootMargin: '120px' });
  tiles.forEach((t) => io.observe(t.canvas));

  // Round-robin scheduler: bounded work per frame, paused inside the lab.
  const BUDGET = 2;
  let cursor = 0;
  function loop() {
    requestAnimationFrame(loop);
    if (reduce.matches || labActive() || !active.size) return;
    const list = [...active];
    for (let k = 0; k < BUDGET; k++) {
      const rec = list[cursor++ % list.length];
      if (rec && (rec.ready || ensure(rec))) render(rec);
    }
  }
  // one static frame each (so nothing is blank) even under reduced motion
  requestAnimationFrame(() => tiles.forEach((rec) => { if (ensure(rec)) render(rec); }));
  requestAnimationFrame(loop);
}

// ── enter the lab ────────────────────────────────────────────────────────────
function enter(stageId) {
  if (window.WEB9 && typeof window.WEB9.enter === 'function') window.WEB9.enter(stageId || null);
  else document.body.classList.add('lab-active');   // failsafe: reveal the lab anyway
  window.scrollTo(0, 0);
}

function init() {
  const enterBtn = $('enterBtn');
  if (enterBtn) enterBtn.onclick = () => enter(null);
  const backBtn = $('toLandingBtn');
  if (backBtn) backBtn.onclick = () => { document.body.classList.remove('lab-active'); };
  startStudio();
  if (!labActive()) buildPreviews(); else requestAnimationFrame(buildPreviews);
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
else init();
