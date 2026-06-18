// web9 — the living amoeba GUIDE (V1 narration + V2 ask-to-change).
//
// The amoeba explains each stage and takes requests. It renders procedurally
// (the same blobgeom membrane + gaze as the desktop colony), shows a museum-label
// speech bubble, and an "ask the amoeba…" input + chips. Requests run through the
// pure intent parser and execute against window.WEB9 — a small whitelisted bridge
// main.js exposes — so the guide can only do what the user could do by hand.
//
// Everything degrades gracefully: if the 3-D engine hasn't booted (e.g. offline),
// the guide still explains and answers; control actions report the lab is warming.

import { blobPoints, gazeOffset } from './blobgeom.js';
import { explainStage, citeStage } from './narration.js';
import { parseIntent, SUGGESTIONS } from './intents.js';

const TEAL = [57, 212, 200];
const TEAL_HI = [94, 231, 220];
const EYE = [253, 246, 227];
const PUPIL = [10, 14, 22];
const TAU = Math.PI * 2;
const rgba = (c, a = 1) => `rgba(${c[0]},${c[1]},${c[2]},${a})`;
const reduce = window.matchMedia('(prefers-reduced-motion: reduce)');

let currentStageId = 'stage0-miller-urey';
let mood = 'idle'; // idle | talking | thinking
let talkUntil = 0;
let bubbleText = null;
let bubbleCite = null;
let inputEl = null;

function announce(msg) {
  const sr = document.getElementById('srStatus');
  if (sr) sr.textContent = msg;
}

// ── speech ──────────────────────────────────────────────────────────────────
let typeTimer = 0;
function typewrite(el, text) {
  clearInterval(typeTimer);
  if (reduce.matches) { el.textContent = text; return; }
  el.textContent = '';
  let i = 0;
  typeTimer = setInterval(() => {
    el.textContent = text.slice(0, ++i);
    if (i >= text.length) clearInterval(typeTimer);
  }, 16);
}
function say(text, m = 'talking', cite = '') {
  mood = m;
  talkUntil = performance.now() + Math.min(7000, 1500 + text.length * 26);
  if (bubbleText) typewrite(bubbleText, text);
  if (bubbleCite) bubbleCite.textContent = cite || '';
  announce(text);
}

// ── action execution (V2) ─────────────────────────────────────────────────────
const VIEW_SAY = { lab: 'Apparatus only.', split: 'Split — apparatus and micrograph.', exp: 'Just the micrograph now.' };

function stepStage(dir) {
  const W = window.WEB9;
  if (!W) return null;
  const stages = W.stages();
  const i = stages.findIndex((s) => s.id === (W.state().stage || currentStageId));
  const j = dir === 'next' ? Math.min(stages.length - 1, i + 1) : Math.max(0, i - 1);
  if (j === i || j < 0) { say(dir === 'next' ? "That's the last plate." : "That's the first plate.", 'idle'); return null; }
  W.loadStageById(stages[j].id);
  return stages[j].id;
}

function execute(action) {
  const W = window.WEB9;
  switch (action.kind) {
    case 'noop':
      return;
    case 'help':
      return say("Ask me to: run or pause, go faster/slower, step, reset, take it apart, switch view (lab/split/micrograph), go next/previous, name a stage (e.g. 'show the RNA world'), or 'explain this'.", 'talking');
    case 'explain': {
      const id = action.value || (W && W.state().stage) || currentStageId;
      return say(explainStage(id), 'talking', citeStage(id));
    }
    case 'unknown':
      return say("I didn't quite catch that — try 'run', 'faster', 'split', 'next', 'explain this', or name a stage.", 'idle');
  }

  if (!W) {
    return say("The lab's still warming up — I can explain things now, but I can't drive the apparatus until the 3-D engine loads.", 'idle');
  }

  switch (action.kind) {
    case 'run':
      W.run(action.value);
      return say(action.value ? 'Running it ▶' : 'Paused.', 'talking');
    case 'step':
      W.step();
      return say('Stepped one frame.', 'talking');
    case 'reset':
      W.reset();
      return say('Fresh specimen — reseeded.', 'talking');
    case 'speed': {
      const s = W.state().speed || 30;
      const v = action.value === 'up' ? Math.min(60, Math.round(s * 1.6)) : Math.max(2, Math.round(s / 1.6));
      W.speed(v);
      return say(action.value === 'up' ? `Speeding up — ${v} steps/s.` : `Slowing down — ${v} steps/s.`, 'talking');
    }
    case 'view':
      W.view(action.value);
      return say(VIEW_SAY[action.value] || 'View changed.', 'talking');
    case 'explode':
      W.explode(action.value);
      return say(action.value ? 'Taking the apparatus apart.' : 'Back together.', 'talking');
    case 'stage':
      if (action.value === 'next' || action.value === 'prev') { stepStage(action.value); return; }
      if (!W.loadStageById(action.value)) return say("I couldn't find that stage.", 'idle');
      return; // the web9:stage event will narrate the new plate
  }
}

function handle(text) {
  if (inputEl) inputEl.value = '';
  if (!text || !text.trim()) return;
  mood = 'thinking';
  setTimeout(() => execute(parseIntent(text)), 180);
}

// ── DOM panel ─────────────────────────────────────────────────────────────────
function buildPanel(host) {
  const root = document.createElement('div');
  root.className = 'guide-root';

  const bubble = document.createElement('div');
  bubble.className = 'guide-bubble';
  bubble.innerHTML = '<p class="guide-bubble-text"></p><span class="guide-bubble-cite"></span>';
  bubbleText = bubble.querySelector('.guide-bubble-text');
  bubbleCite = bubble.querySelector('.guide-bubble-cite');

  const dock = document.createElement('div');
  dock.className = 'guide-dock';

  const cv = document.createElement('canvas');
  cv.className = 'amoeba-guide';
  cv.setAttribute('role', 'img');
  cv.setAttribute('aria-label', 'Amoeba guide');
  cv.tabIndex = 0;
  cv.title = 'Your guide — ask it anything';

  const controls = document.createElement('div');
  controls.className = 'guide-controls';

  const form = document.createElement('form');
  form.className = 'guide-ask';
  form.innerHTML =
    '<input class="guide-input" type="text" autocomplete="off" ' +
    'placeholder="ask the amoeba…" aria-label="Ask the amoeba to change the experiment">' +
    '<button class="guide-send" type="submit" aria-label="Send">→</button>';
  inputEl = form.querySelector('.guide-input');
  form.addEventListener('submit', (e) => { e.preventDefault(); handle(inputEl.value); });

  const chips = document.createElement('div');
  chips.className = 'guide-chips';
  for (const s of SUGGESTIONS) {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'guide-chip';
    b.textContent = s.label;
    b.addEventListener('click', () => handle(s.text));
    chips.appendChild(b);
  }

  const min = document.createElement('button');
  min.type = 'button';
  min.className = 'guide-min';
  min.textContent = '–';
  min.setAttribute('aria-label', 'Minimise the guide');
  min.addEventListener('click', () => {
    const collapsed = root.classList.toggle('collapsed');
    min.textContent = collapsed ? '+' : '–';
    min.setAttribute('aria-label', collapsed ? 'Expand the guide' : 'Minimise the guide');
  });

  cv.addEventListener('click', () => {
    if (root.classList.contains('collapsed')) { root.classList.remove('collapsed'); min.textContent = '–'; }
    inputEl?.focus();
  });

  controls.appendChild(form);
  controls.appendChild(chips);
  dock.appendChild(cv);
  dock.appendChild(controls);
  root.appendChild(min);
  root.appendChild(bubble);
  root.appendChild(dock);
  host.appendChild(root);
  return cv;
}

// ── amoeba rendering (smoothed membrane + talking mouth) ──────────────────────
function smoothClosed(ctx, pts) {
  const n = pts.length;
  const mid = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
  ctx.beginPath();
  let [sx, sy] = mid(pts[n - 1], pts[0]);
  ctx.moveTo(sx, sy);
  for (let i = 0; i < n; i++) {
    const cur = pts[i];
    const [mx, my] = mid(cur, pts[(i + 1) % n]);
    ctx.quadraticCurveTo(cur[0], cur[1], mx, my);
  }
  ctx.closePath();
}

function startGuide(cv) {
  const ctx = cv.getContext('2d');
  const SIZE = 104;
  function resize() {
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    cv.width = SIZE * dpr; cv.height = SIZE * dpr;
    cv.style.width = SIZE + 'px'; cv.style.height = SIZE + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  resize();
  window.addEventListener('resize', resize);

  const seed = 0xce11;
  let frame = 0;
  function draw() {
    ctx.clearRect(0, 0, SIZE, SIZE);
    const cx = SIZE / 2, cy = SIZE / 2, r = SIZE * 0.36, rx = r, ry = r * 0.96;
    const talking = !reduce.matches && performance.now() < talkUntil;
    const thinking = mood === 'thinking' && !reduce.matches;
    const f = reduce.matches ? 0 : frame;
    const bob = Math.sin(f * 0.11) * (ry * 0.05) + (talking ? Math.sin(f * 0.5) * ry * 0.02 : 0);
    const breath = Math.sin(f * 0.08) * 0.06;
    const mem = f * 0.06;
    const cyb = cy + bob, bx = rx * (1 + breath), by = ry * (1 - breath * 0.6);

    smoothClosed(ctx, blobPoints(cx, cyb, bx, by, { seed, phase: mem, n: 16 }));
    ctx.fillStyle = rgba(TEAL); ctx.fill();
    smoothClosed(ctx, blobPoints(cx - bx * 0.3, cyb - by * 0.4, bx * 0.44, by * 0.34, { seed: seed ^ 0x5eed, phase: mem * 0.8, wobble: 0.1, n: 16 }));
    ctx.fillStyle = rgba(TEAL_HI, 0.82); ctx.fill();

    const ew = r * 0.18, pr = ew * 0.5, edx = r * 0.2, edy = -ry * 0.12;
    const blink = !reduce.matches && frame % 220 < 7;
    let [gx, gy] = gazeOffset(f, seed, ew - pr - 1);
    if (thinking) { gx = ew * 0.4; gy = -(ew - pr - 1); } // glance up while thinking
    for (const s of [-1, 1]) {
      const ex = cx + s * edx, ey = cyb + edy;
      ctx.fillStyle = rgba(EYE);
      ctx.beginPath(); ctx.ellipse(ex, ey, ew, blink ? Math.max(1, ew * 0.12) : ew, 0, 0, TAU); ctx.fill();
      if (!blink) { ctx.fillStyle = rgba(PUPIL); ctx.beginPath(); ctx.arc(ex + gx, ey + gy, pr, 0, TAU); ctx.fill(); }
    }

    ctx.fillStyle = rgba(PUPIL); ctx.strokeStyle = rgba(PUPIL);
    ctx.lineWidth = Math.max(2, r * 0.06); ctx.lineCap = 'round';
    const my = cyb + ry * 0.12;
    if (talking) {
      const open = Math.sin(frame * 0.55) * 0.5 + 0.5;
      ctx.beginPath(); ctx.ellipse(cx, my, r * 0.16, r * 0.05 + r * 0.13 * open, 0, 0, TAU); ctx.fill();
    } else {
      ctx.beginPath(); ctx.arc(cx, cyb + ry * 0.06, r * 0.26, 0.18 * Math.PI, 0.82 * Math.PI); ctx.stroke();
    }
  }

  let running = false;
  function loop() { if (!running) return; frame++; draw(); requestAnimationFrame(loop); }
  function sync() { if (reduce.matches) { running = false; draw(); } else if (!running) { running = true; requestAnimationFrame(loop); } }
  sync();
  reduce.addEventListener?.('change', sync);
}

// ── wiring ────────────────────────────────────────────────────────────────────
function mount() {
  const host = document.querySelector('.panes') || document.querySelector('.specimen') || document.body;
  if (getComputedStyle(host).position === 'static') host.style.position = 'relative';
  const cv = buildPanel(host);
  startGuide(cv);

  // narrate each stage as the lab loads it
  window.addEventListener('web9:stage', (e) => {
    const id = e.detail && e.detail.id;
    if (!id) return;
    currentStageId = id;
    say(explainStage(id), 'talking', citeStage(id));
  });

  // the first stage may have loaded before we were listening — narrate it now
  const st0 = window.WEB9 && window.WEB9.state();
  if (st0 && st0.stage) { currentStageId = st0.stage; say(explainStage(st0.stage), 'talking', citeStage(st0.stage)); }

  // opening line (after the lab has had a beat to announce its first stage)
  setTimeout(() => {
    if (!bubbleText.textContent) {
      say("Hi — I'm your guide. I'll explain each origin-of-life stage; ask me to run it, change speed or view, switch stages, or just say 'explain this'.", 'talking');
    }
  }, 1400);
}

if (document.readyState !== 'loading') mount();
else window.addEventListener('DOMContentLoaded', mount);
