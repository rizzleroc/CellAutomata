// cellauto · ontogeny — the renderer. The developmental scene is built as a
// single-channel HEIGHT FIELD (cells/embryos as domes, sperm as ridges, sacs as
// raised rings) and depth-shaded through the SAME SEM pipeline every other lab
// uses (window.SEM, sem.js) — so the specimen is a real warm-sepia micrograph,
// not flat shapes. The true number is overlaid on top. Canvas 2D, zero deps
// (SEM is loaded as a classic script before app.js).
import { cellsForDay } from './sim.js';

const OB = '#07090d', TEAL = '#3fe0d0', TEAL_D = '#1f8f86', TEAL_B = '#74f4e7',
      BONE = '#ece7da', BONE_D = '#9a9280', MAG = '#d77bff', MUTED = '#9a9280';
const lerp = (a, b, t) => a + (b - a) * t;
const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);
const ease = (t) => (t < 0 ? 0 : t > 1 ? 1 : t * t * (3 - 2 * t));

// ── height-field primitives (operate on a Float32 grid, values [0,1]) ─────────
// Stable hash for cytoplasm granularity (deterministic across frames).
function h2(x, y) { const s = Math.sin(x * 12.9898 + y * 78.233) * 43758.5453; return s - Math.floor(s); }

// A rounded CELL — paraboloid cap, so it reads as a raised 3-D sphere. (A flat
// smoothstep plateau gets its centre darkened by the SEM ambient-occlusion term
// and reads as a crater — the "just a depression" problem.) `gran` adds a faint
// granular cytoplasm texture; `core` lifts the centre a touch for roundness.
function sphere(buf, G, cx, cy, r, hgt, gran = 0) {
  if (r <= 0) return;
  const x0 = Math.max(0, Math.floor(cx - r)), x1 = Math.min(G - 1, Math.ceil(cx + r));
  const y0 = Math.max(0, Math.floor(cy - r)), y1 = Math.min(G - 1, Math.ceil(cy + r));
  for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) {
    const dx = x + 0.5 - cx, dy = y + 0.5 - cy, d2 = (dx * dx + dy * dy) / (r * r);
    if (d2 >= 1) continue;
    let z = Math.pow(1 - d2, 0.6);                       // rounded cap (not a plateau)
    if (gran) z *= 1 + (h2(x * 1.7, y * 1.7) - 0.5) * gran;
    const i = y * G + x, v = buf[i] + hgt * z; buf[i] = v > 1 ? 1 : (v < 0 ? 0 : v);
  }
}
// A raised band (the zona pellucida shell wall, amniotic-sac rim).
function ridge(buf, G, cx, cy, r, thick, hgt) {
  const R = r + thick;
  const x0 = Math.max(0, Math.floor(cx - R)), x1 = Math.min(G - 1, Math.ceil(cx + R));
  const y0 = Math.max(0, Math.floor(cy - R)), y1 = Math.min(G - 1, Math.ceil(cy + R));
  for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) {
    const dd = Math.abs(Math.hypot(x + 0.5 - cx, y + 0.5 - cy) - r);
    if (dd >= thick) continue;
    const f = 1 - dd / thick, i = y * G + x, v = buf[i] + hgt * f * f; buf[i] = v > 1 ? 1 : v;
  }
}
// A low mound (placenta).
function bump(buf, G, cx, cy, r, hgt) { sphere(buf, G, cx, cy, r, hgt); }
// A packed ball of `n` blastomere cells inside radius R.
function clusterH(buf, G, cx, cy, n, R, hgt) {
  const cr = n <= 1 ? R * 0.86 : Math.max(R * 0.16, R / Math.sqrt(n) * 0.9);
  for (let i = 0; i < n; i++) {
    if (n === 1) { sphere(buf, G, cx, cy, cr, hgt, 0.06); continue; }
    const ang = i * 2.399963, rr = R * 0.72 * Math.sqrt(i / n);
    sphere(buf, G, cx + rr * Math.cos(ang), cy + rr * Math.sin(ang), cr, hgt, 0.05);
  }
}
// A single egg/zygote cell: zona shell + granular cytoplasm + (optional) nucleus.
function eggH(buf, G, cx, cy, r, opts = {}) {
  ridge(buf, G, cx, cy, r * 0.9, r * 0.14, 0.28);          // zona pellucida (translucent shell)
  sphere(buf, G, cx, cy, r * 0.78, 0.74, 0.04);            // cytoplasm — a smooth, bright sphere
  if (opts.pronuclei != null) {                            // two pronuclei drawing together (fertilisation)
    const sep = r * 0.24 * (1 - opts.pronuclei);
    sphere(buf, G, cx - sep, cy, r * 0.2, 0.16);
    sphere(buf, G, cx + sep, cy, r * 0.2, 0.16);
  } else if (opts.nucleus) {
    sphere(buf, G, cx, cy, r * 0.26, 0.14);               // germinal vesicle
  }
  if (opts.polarBody) sphere(buf, G, cx + r * 0.64, cy - r * 0.56, r * 0.08, 0.14);
}
// A sperm: head sphere + a tapering, wiggling tail.
function spermH(buf, G, x, y, ang, sz, time, phase) {
  sphere(buf, G, x, y, sz, 0.5);
  for (let k = 1; k <= 5; k++) {
    const wob = Math.sin(k * 1.3 + time * 9 + phase) * sz * 0.85;
    sphere(buf, G, x - Math.cos(ang) * k * sz * 1.05 + Math.cos(ang + 1.57) * wob,
                   y - Math.sin(ang) * k * sz * 1.05 + Math.sin(ang + 1.57) * wob,
                   Math.max(sz * 0.3, sz * (1 - k * 0.16)), 0.34);
  }
}
function fetusH(buf, G, x, y, s, hgt) {        // body + head, rounded
  sphere(buf, G, x, y, s * 0.82, hgt, 0.05);
  sphere(buf, G, x + s * 0.42, y - s * 0.58, s * 0.46, hgt * 1.05);
  sphere(buf, G, x - s * 0.5, y + s * 0.4, s * 0.3, hgt * 0.8);   // a limb-bud hint
}

// k centres + a per-item radius that fills the field (the "zoom"). Proportional,
// so it works for the height grid AND the pixel membrane diagram.
function slots(k, W, H) {
  const y = H * 0.46;
  const r = clamp((W * 0.82) / k * 0.42, Math.min(W, H) * 0.045, Math.min(W, H) * 0.3);
  if (k <= 1) return { pts: [[W / 2, y]], r };
  const pts = [], span = W * 0.78, x0 = W / 2 - span / 2 + span / k / 2, x1 = W / 2 + span / 2 - span / k / 2;
  for (let i = 0; i < k; i++) pts.push([lerp(x0, x1, i / (k - 1)), y]);
  return { pts, r };
}
function countAt(outcome, day) {
  const groups = new Set(outcome.babies.map((b) => b.mzGroup)).size || 1;
  if (day < 0) return Math.max(1, outcome.nOocytes);
  if (day < 0.4) return groups;
  return clamp(groups + outcome.splitEvents.filter((e) => e.day <= day).length, 1, outcome.n || 1);
}

// ── build the developmental scene as a height field ───────────────────────────
export function buildHeight(buf, G, st) {
  const { outcome, day, time = 0 } = st;
  buf.fill(0.10);                                   // dim substrate; SEM adds its own grain
  if (!outcome || outcome.n === 0) return;

  if (day < 0) {                                    // gametes — the egg + the sperm race
    const k = Math.max(1, outcome.nOocytes), { pts, r } = slots(k, G, G), oor = Math.min(r, G * 0.15);
    for (const [ox, oy] of pts) {
      eggH(buf, G, ox, oy, oor, { nucleus: true });
      const p = ease(clamp((time % 3) / 2.4, 0, 1));
      for (let i = 0; i < 18; i++) {
        const ang = i / 18 * 6.283 + 0.2, d = lerp(G * 0.44, oor * 1.05, p * (0.78 + 0.3 * ((i * 7) % 5) / 5));
        spermH(buf, G, ox + Math.cos(ang) * d, oy + Math.sin(ang) * d, ang + Math.PI, Math.max(1.4, G * 0.012), time, i * 0.6);
      }
    }
    return;
  }
  if (day < 1) {                                    // fertilisation — the pronuclei fuse
    const k = new Set(outcome.babies.map((b) => b.mzGroup)).size || 1, { pts, r } = slots(k, G, G);
    const u = clamp(day / 0.85, 0, 1);
    for (const [ox, oy] of pts) {
      eggH(buf, G, ox, oy, Math.min(r, G * 0.17), { pronuclei: u, polarBody: true });
      ridge(buf, G, ox, oy, r * (0.72 + u * 0.6), Math.max(1, G * 0.008), (1 - u) * 0.4);   // cortical-reaction flash
    }
    return;
  }
  if (day < 14) {                                   // cleavage → blastocyst → split
    const k = countAt(outcome, day), n = cellsForDay(day), { pts, r } = slots(k, G, G);
    for (const [ox, oy] of pts) {
      if (day < 5.2) ridge(buf, G, ox, oy, r * 0.96, r * 0.12, 0.26);     // zona pellucida, until hatching
      if (n >= 32) { ridge(buf, G, ox, oy, r * 0.82, Math.max(1, G * 0.01), 0.34); clusterH(buf, G, ox - r * 0.25, oy, 12, r * 0.42, 0.7); }
      else clusterH(buf, G, ox, oy, n, r * 0.82, 0.85);
    }
    return;
  }
  // implantation → fetal: the womb
  const grow = ease(clamp((day - 14) / (266 - 14), 0, 1)), beat = day >= 22 ? 1 + 0.05 * Math.sin(time * 7) : 1;
  const L = membraneLayout(outcome, G, G);
  for (const u of L.placentas) bump(buf, G, u.x, u.y, u.r, 0.17);
  for (const s of L.sacs) {
    ridge(buf, G, s.x, s.y, s.r, Math.max(1, G * 0.008), 0.26);
    const baby = outcome.babies[s.i], hgt = baby && !baby.viable ? 0.3 : 0.85;
    if (day < 56) clusterH(buf, G, s.x, s.y, 12, Math.max(G * 0.03, s.r * 0.5 * grow + G * 0.02), hgt);
    else fetusH(buf, G, s.x, s.y, s.r * 0.6 * (0.5 + 0.5 * grow) * beat, hgt);
  }
}

function membraneLayout(outcome, W, H) {
  const cy = H * 0.46, U = Math.min(W, H), byGroup = {};
  outcome.babies.forEach((b, i) => (byGroup[b.mzGroup] ??= []).push(i));
  const groups = Object.values(byGroup);
  const placentas = [], sacs = [], { pts: gs } = slots(groups.length, W, H);
  const pr = clamp(U * (groups.length > 2 ? 0.2 : 0.32), 0.1 * U, U * 0.42);
  groups.forEach((idxs, gi) => {
    const gx = gs[gi][0], gy = cy, type = outcome.babies[idxs[0]].cho?.type;
    const shared = idxs.length > 1 && ['MCDA', 'MCMA', 'conjoined'].includes(type);
    if (shared) {
      placentas.push({ x: gx, y: gy, r: pr });
      if (type === 'MCMA' || type === 'conjoined') {
        sacs.push({ x: gx, y: gy, r: pr * 0.74, i: idxs[0] });
        idxs.slice(1).forEach((bi, k) => sacs.push({ x: gx + (k - 0.5) * pr * 0.5, y: gy, r: pr * 0.4, i: bi }));
      } else idxs.forEach((bi, k) => sacs.push({ x: gx + (k - (idxs.length - 1) / 2) * pr * 0.6, y: gy, r: pr * 0.46, i: bi }));
    } else idxs.forEach((bi, k) => {
      const off = idxs.length === 1 ? 0 : (k - (idxs.length - 1) / 2) * pr * 1.2;
      placentas.push({ x: gx + off, y: gy, r: pr * 0.7 }); sacs.push({ x: gx + off, y: gy, r: pr * 0.5, i: bi });
    });
  });
  return { placentas, sacs };
}

// the true number at this phase
function countLabel(o, day) {
  if (o.n === 0) return { n: 0, unit: 'conceived' };
  if (day < 0) { const k = Math.max(1, o.nOocytes); return { n: k, unit: k === 1 ? 'egg' : 'eggs', sub: 'sperm racing' }; }
  if (day < 1) { const k = new Set(o.babies.map((b) => b.mzGroup)).size || 1; return { n: k, unit: k === 1 ? 'zygote' : 'zygotes', sub: '46 chromosomes' }; }
  if (day < 14) {
    const k = countAt(o, day), n = cellsForDay(day);
    if (n >= 32) return { n: k, unit: k === 1 ? 'blastocyst' : 'blastocysts', sub: '~64–128 cells' };
    return { n, unit: n === 1 ? 'cell' : 'cells', sub: k > 1 ? `${k} embryos` : 'cleavage' };
  }
  const u = day < 56 ? 'embryo' : day < 266 ? 'fetus' : 'baby';
  return { n: o.n, unit: o.n === 1 ? u : (u === 'fetus' ? 'fetuses' : u + 's'), sub: o.n >= 2 ? o.diagnosis.split(' · ').slice(1).join(' · ') : null };
}
function showNumber(ctx, W, H, n, unit, sub) {
  const big = clamp(Math.min(W, H) * 0.07, 16, 46), y = H - big * 0.7;
  ctx.save(); ctx.shadowColor = 'rgba(0,0,0,0.7)'; ctx.shadowBlur = 8; ctx.textBaseline = 'alphabetic';
  ctx.font = `${big}px "IBM Plex Mono", ui-monospace, monospace`;
  const num = `${n}`, numW = ctx.measureText(num).width;
  ctx.font = `${big * 0.42}px "IBM Plex Mono", ui-monospace, monospace`;
  const unitW = ctx.measureText(' ' + unit).width, x0 = W / 2 - (numW + unitW) / 2;
  ctx.textAlign = 'left';
  ctx.font = `${big}px "IBM Plex Mono", ui-monospace, monospace`; ctx.fillStyle = TEAL_B; ctx.fillText(num, x0, y);
  ctx.font = `${big * 0.42}px "IBM Plex Mono", ui-monospace, monospace`; ctx.fillStyle = '#d8cfb8'; ctx.fillText(' ' + unit, x0 + numW, y);
  if (sub) { ctx.textAlign = 'center'; ctx.font = `${big * 0.3}px "IBM Plex Mono", ui-monospace, monospace`; ctx.fillStyle = '#c9bfa8'; ctx.fillText(sub.toUpperCase(), W / 2, y + big * 0.4); }
  ctx.restore();
}

// ── the SEM specimen canvas ───────────────────────────────────────────────────
const BASE = 168, SCALE = 2, OUT = BASE * SCALE;
let hbuf = null, off = null, offCtx = null, semImg = null;
export function drawSpecimen(ctx, W, H, st) {
  const SEM = typeof window !== 'undefined' ? window.SEM : null;
  if (!hbuf) hbuf = new Float32Array(BASE * BASE);
  buildHeight(hbuf, BASE, st);
  ctx.clearRect(0, 0, W, H); ctx.fillStyle = OB; ctx.fillRect(0, 0, W, H);
  if (SEM && SEM.render) {
    if (!off) { off = document.createElement('canvas'); off.width = OUT; off.height = OUT; offCtx = off.getContext('2d'); semImg = offCtx.createImageData(OUT, OUT); }
    SEM.render(hbuf, BASE, BASE, semImg.data, { palette: 'warm-sepia', scale: SCALE, relief: 10 });
    offCtx.putImageData(semImg, 0, 0);
    const side = Math.min(W, H) * 0.97, dx = (W - side) / 2, dy = (H - side) / 2;
    ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(off, 0, 0, OUT, OUT, dx, dy, side, side);
  }
  if (st.outcome && st.outcome.n > 0) { const c = countLabel(st.outcome, st.day); showNumber(ctx, W, H, c.n, c.unit, c.sub); }
  else showNumber(ctx, W, H, 0, 'conceived');
}

// ── the compact diagnosis-panel membrane diagram (clean schematic) ────────────
function disc(ctx, x, y, r, fill, a = 1) { if (r <= 0) return; ctx.globalAlpha = a; ctx.fillStyle = fill; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill(); ctx.globalAlpha = 1; }
function ring2(ctx, x, y, r, w, s, a = 1) { if (r <= 0) return; ctx.globalAlpha = a; ctx.strokeStyle = s; ctx.lineWidth = w; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.stroke(); ctx.globalAlpha = 1; }
function fetus2(ctx, x, y, s, a = 1) {
  ctx.save(); ctx.translate(x, y); ctx.globalAlpha = a;
  const g = ctx.createRadialGradient(-s * 0.2, -s * 0.2, s * 0.1, 0, 0, s); g.addColorStop(0, TEAL_B); g.addColorStop(1, TEAL_D); ctx.fillStyle = g;
  ctx.beginPath(); ctx.arc(0, 0, s, Math.PI * 0.15, Math.PI * 1.55); ctx.quadraticCurveTo(-s * 0.2, -s * 0.2, s * 0.55, -s * 0.75); ctx.closePath(); ctx.fill();
  disc(ctx, s * 0.45, -s * 0.7, s * 0.42, g, a); ctx.globalAlpha = 1; ctx.restore();
}
export function drawMembranes(ctx, W, H, outcome) {
  ctx.clearRect(0, 0, W, H);
  if (!outcome || outcome.n === 0) return;
  const L = membraneLayout(outcome, W, H);
  for (const u of L.placentas) { disc(ctx, u.x, u.y, u.r, 'rgba(215,123,255,0.14)'); ring2(ctx, u.x, u.y, u.r, 1, 'rgba(215,123,255,0.4)'); }
  for (const s of L.sacs) { ring2(ctx, s.x, s.y, s.r, 1.4, TEAL, 0.6); const b = outcome.babies[s.i]; fetus2(ctx, s.x, s.y, s.r * 0.52, b && !b.viable ? 0.4 : 1); }
}
