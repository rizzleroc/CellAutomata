// cellauto · ontogeny — the renderer. Draws the determined conception outcome at
// any point on the developmental clock, ZOOMED to fill the stage and labelled
// with the TRUE NUMBER at each phase (cells while cleaving; embryos/babies for
// multiples). Canvas 2D, zero deps.
import { cellsForDay } from './sim.js';

const OB = '#07090d', TEAL = '#3fe0d0', TEAL_D = '#1f8f86', TEAL_B = '#74f4e7',
      BONE = '#ece7da', BONE_D = '#9a9280', MAG = '#d77bff', MUTED = '#9a9280';

const lerp = (a, b, t) => a + (b - a) * t;
const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);
const ease = (t) => (t < 0 ? 0 : t > 1 ? 1 : t * t * (3 - 2 * t));
const plural = (n, w) => `${n} ${w}${n === 1 ? '' : 's'}`;

function disc(ctx, x, y, r, fill, a = 1) {
  if (r <= 0) return;
  ctx.globalAlpha = a; ctx.fillStyle = fill;
  ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill(); ctx.globalAlpha = 1;
}
function ring(ctx, x, y, r, w, stroke, a = 1) {
  if (r <= 0) return;
  ctx.globalAlpha = a; ctx.strokeStyle = stroke; ctx.lineWidth = w;
  ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.stroke(); ctx.globalAlpha = 1;
}
function cell(ctx, x, y, r, a = 1) {
  const g = ctx.createRadialGradient(x - r * 0.3, y - r * 0.3, r * 0.1, x, y, r);
  g.addColorStop(0, TEAL_B); g.addColorStop(1, TEAL_D);
  disc(ctx, x, y, r, g, a); ring(ctx, x, y, r, Math.max(1, r * 0.06), TEAL, a * 0.5);
}
// a packed ball of `n` cells of overall radius R
function cluster(ctx, cx, cy, n, R, a = 1) {
  const cr = n <= 1 ? R * 0.92 : Math.max(R * 0.13, R / Math.sqrt(n) * 0.95);
  for (let i = 0; i < n; i++) {
    if (n === 1) { cell(ctx, cx, cy, cr, a); continue; }
    const ang = i * 2.399963, rr = R * 0.76 * Math.sqrt(i / n);
    cell(ctx, cx + rr * Math.cos(ang), cy + rr * Math.sin(ang), cr, a);
  }
}
function oocyte(ctx, x, y, r, a = 1) {
  disc(ctx, x, y, r, TEAL_D, a * 0.5); ring(ctx, x, y, r + r * 0.12, r * 0.1, BONE_D, a * 0.45);
  disc(ctx, x - r * 0.2, y - r * 0.2, r * 0.3, TEAL_B, a * 0.7);
}
function sperm(ctx, x, y, ang, a, time, sz) {
  disc(ctx, x, y, sz, BONE, a);
  for (let k = 1; k <= 4; k++) {
    const wob = Math.sin(k * 1.3 + time * 9 + x * 0.1) * sz * 0.7;
    disc(ctx, x - Math.cos(ang) * k * sz * 1.1 + Math.cos(ang + 1.57) * wob,
             y - Math.sin(ang) * k * sz * 1.1 + Math.sin(ang + 1.57) * wob,
             Math.max(sz * 0.25, sz * (1 - k * 0.18)), BONE_D, a * (1 - k * 0.2));
  }
}
function fetus(ctx, x, y, s, a = 1) {
  ctx.save(); ctx.translate(x, y); ctx.globalAlpha = a;
  const g = ctx.createRadialGradient(-s * 0.2, -s * 0.2, s * 0.1, 0, 0, s);
  g.addColorStop(0, TEAL_B); g.addColorStop(1, TEAL_D); ctx.fillStyle = g;
  ctx.beginPath(); ctx.arc(0, 0, s, Math.PI * 0.15, Math.PI * 1.55);
  ctx.quadraticCurveTo(-s * 0.2, -s * 0.2, s * 0.55, -s * 0.75); ctx.closePath(); ctx.fill();
  disc(ctx, s * 0.45, -s * 0.7, s * 0.42, g, a);
  ring(ctx, 0, 0, s, Math.max(1, s * 0.05), TEAL, a * 0.4);
  ctx.globalAlpha = 1; ctx.restore();
}

// ── the count readout — the TRUE NUMBER, large, on the stage ──────────────────
function showNumber(ctx, W, H, n, unit, sub) {
  const big = clamp(Math.min(W, H) * 0.07, 16, 44);
  ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
  ctx.font = `${big}px "IBM Plex Mono", ui-monospace, monospace`;
  ctx.fillStyle = TEAL;
  const num = `${n}`, numW = ctx.measureText(num).width;
  ctx.font = `${big * 0.42}px "IBM Plex Mono", ui-monospace, monospace`;
  const unitW = ctx.measureText(' ' + unit).width;
  const y = H - big * 0.7, x0 = W / 2 - (numW + unitW) / 2;
  ctx.textAlign = 'left';
  ctx.font = `${big}px "IBM Plex Mono", ui-monospace, monospace`; ctx.fillStyle = TEAL;
  ctx.fillText(num, x0, y);
  ctx.font = `${big * 0.42}px "IBM Plex Mono", ui-monospace, monospace`; ctx.fillStyle = MUTED;
  ctx.fillText(' ' + unit, x0 + numW, y);
  if (sub) {
    ctx.textAlign = 'center'; ctx.font = `${big * 0.3}px "IBM Plex Mono", ui-monospace, monospace`;
    ctx.fillStyle = BONE_D; ctx.fillText(sub.toUpperCase(), W / 2, y + big * 0.42);
  }
  ctx.textAlign = 'left';
}

// how many distinct conceptuses are visible at `day`
function countAt(outcome, day) {
  const groups = new Set(outcome.babies.map((b) => b.mzGroup)).size || 1;
  if (day < 0) return Math.max(1, outcome.nOocytes);
  if (day < 0.4) return groups;
  const splits = outcome.splitEvents.filter((e) => e.day <= day).length;
  return clamp(groups + splits, 1, outcome.n || 1);
}
// k centres + a per-item radius that fills the stage (the "zoom")
function slots(k, W, H, frac = 0.34) {
  const y = H * 0.46;
  const r = clamp(Math.min((W * 0.84) / k * 0.42, H * frac), 8, Math.min(W, H) * 0.32);
  if (k <= 1) return { pts: [[W / 2, y]], r: Math.min(r, Math.min(W, H) * 0.3) };
  const pts = [];
  for (let i = 0; i < k; i++) pts.push([lerp(W * 0.5 - (W * 0.78) / 2 + (W * 0.78) / k / 2, W * 0.5 + (W * 0.78) / 2 - (W * 0.78) / k / 2, k === 1 ? 0.5 : i / (k - 1)), y]);
  return { pts, r };
}

// ── the main specimen canvas ──────────────────────────────────────────────────
export function drawSpecimen(ctx, W, H, st) {
  const { outcome, day, time = 0 } = st;
  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = OB; ctx.fillRect(0, 0, W, H);
  const vg = ctx.createRadialGradient(W / 2, H / 2, Math.min(W, H) * 0.18, W / 2, H / 2, Math.max(W, H) * 0.62);
  vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,0.55)');
  ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
  if (!outcome || outcome.n === 0) { showNumber(ctx, W, H, 0, 'conceived'); return; }
  const U = Math.min(W, H);

  if (day < 0) {                                   // ── gametes ──
    const k = Math.max(1, outcome.nOocytes);
    const { pts, r } = slots(k, W, H);
    const oor = Math.min(r, U * 0.13);
    for (const [ox, oy] of pts) {
      oocyte(ctx, ox, oy, oor, 1);
      const p = ease(clamp((time % 3) / 2.4, 0, 1)), spz = Math.max(2, U * 0.012);
      for (let i = 0; i < 16; i++) {
        const ang = i / 16 * 6.283 + 0.2, d = lerp(U * 0.42, oor * 1.15, p * (0.78 + 0.3 * ((i * 7) % 5) / 5));
        sperm(ctx, ox + Math.cos(ang) * d, oy + Math.sin(ang) * d, ang + Math.PI, 0.9, time, spz);
      }
    }
    showNumber(ctx, W, H, k, k === 1 ? 'egg' : 'eggs', 'sperm racing');
    return;
  }

  if (day < 1) {                                   // ── fertilisation ──
    const k = new Set(outcome.babies.map((b) => b.mzGroup)).size || 1;
    const { pts, r } = slots(k, W, H);
    for (const [ox, oy] of pts) {
      cell(ctx, ox, oy, r * 0.7, 1);
      const u = clamp(day / 0.8, 0, 1);
      ring(ctx, ox, oy, r * (0.8 + u * 0.9), Math.max(2, U * 0.01), BONE, (1 - u) * 0.9);
      ring(ctx, ox, oy, r * (0.5 + u * 1.1), Math.max(1, U * 0.006), TEAL_B, (1 - u) * 0.7);
    }
    showNumber(ctx, W, H, k, k === 1 ? 'zygote' : 'zygotes', '46 chromosomes');
    return;
  }

  if (day < 14) {                                  // ── cleavage → blastocyst → split ──
    const k = countAt(outcome, day);
    const n = cellsForDay(day);
    const { pts, r } = slots(k, W, H);
    for (const [ox, oy] of pts) {
      if (day < 5.2 && k === 1) ring(ctx, ox, oy, r * 1.18, Math.max(1, U * 0.006), BONE_D, clamp(0.35 * (1 - (day - 1) / 4), 0, 0.35));
      if (n >= 32) { ring(ctx, ox, oy, r, Math.max(2, U * 0.008), TEAL, 0.5); cluster(ctx, ox - r * 0.25, oy, 10, r * 0.5, 1); }
      else cluster(ctx, ox, oy, n, r, 1);
    }
    const recent = outcome.splitEvents.filter((e) => Math.abs(e.day - day) < 0.6);
    if (recent.length && k >= 2) ring(ctx, pts[k - 1][0], pts[k - 1][1], r * 1.2, Math.max(2, U * 0.01), MAG, 0.6);
    if (n >= 32) showNumber(ctx, W, H, k, k === 1 ? 'blastocyst' : 'blastocysts', '~64–128 cells each');
    else showNumber(ctx, W, H, n, n === 1 ? 'cell' : 'cells', k > 1 ? `${k} embryos` : 'cleavage');
    return;
  }

  // ── implantation → fetal: the womb view ──
  drawWomb(ctx, W, H, outcome, day, time);
  const unit = day < 56 ? 'embryo' : day < 266 ? 'fetus' : 'baby';
  showNumber(ctx, W, H, outcome.n, outcome.n === 1 ? unit : (unit === 'fetus' ? 'fetuses' : unit + 's'),
    outcome.n >= 2 ? outcome.diagnosis.split(' · ').slice(1).join(' · ') : null);
}

function drawWomb(ctx, W, H, outcome, day, time) {
  const grow = ease(clamp((day - 14) / (266 - 14), 0, 1));
  const beat = day >= 22 ? 1 + 0.05 * Math.sin(time * 7) : 1;
  const L = membraneLayout(outcome, W, H);
  for (const u of L.placentas) disc(ctx, u.x, u.y, u.r, 'rgba(215,123,255,0.13)');
  for (const u of L.placentas) ring(ctx, u.x, u.y, u.r, 1, 'rgba(215,123,255,0.35)');
  for (const s of L.sacs) {
    ring(ctx, s.x, s.y, s.r, 1.5, TEAL, 0.5);
    const baby = outcome.babies[s.i], dead = baby && !baby.viable;
    if (day < 56) cluster(ctx, s.x, s.y, 14, Math.max(8, s.r * 0.5 * grow + 6), dead ? 0.4 : 1);
    else fetus(ctx, s.x, s.y, (s.r * 0.66) * (0.5 + 0.5 * grow) * beat, dead ? 0.4 : 1);
  }
}

function membraneLayout(outcome, W, H) {
  const cy = H * 0.46, U = Math.min(W, H);
  const byGroup = {};
  outcome.babies.forEach((b, i) => (byGroup[b.mzGroup] ??= []).push(i));
  const groups = Object.values(byGroup);
  const placentas = [], sacs = [];
  const { pts: gslots } = slots(groups.length, W, H);
  const pr = clamp(U * (groups.length > 2 ? 0.2 : 0.32), 38, U * 0.42);
  groups.forEach((idxs, gi) => {
    const gx = gslots[gi][0], gy = cy;
    const type = outcome.babies[idxs[0]].cho?.type;
    const shared = idxs.length > 1 && ['MCDA', 'MCMA', 'conjoined'].includes(type);
    if (shared) {
      placentas.push({ x: gx, y: gy, r: pr });
      const mono = type === 'MCMA' || type === 'conjoined';
      if (mono) {
        sacs.push({ x: gx, y: gy, r: pr * 0.74, i: idxs[0] });
        idxs.slice(1).forEach((bi, k) => sacs.push({ x: gx + (k - 0.5) * pr * 0.5, y: gy, r: pr * 0.4, i: bi }));
      } else {
        idxs.forEach((bi, k) => sacs.push({ x: gx + (k - (idxs.length - 1) / 2) * pr * 0.6, y: gy, r: pr * 0.46, i: bi }));
      }
    } else {
      idxs.forEach((bi, k) => {
        const off = idxs.length === 1 ? 0 : (k - (idxs.length - 1) / 2) * pr * 1.2;
        placentas.push({ x: gx + off, y: gy, r: pr * 0.7 });
        sacs.push({ x: gx + off, y: gy, r: pr * 0.5, i: bi });
      });
    }
  });
  return { placentas, sacs };
}

// ── the compact diagnosis-panel membrane diagram ──────────────────────────────
export function drawMembranes(ctx, W, H, outcome) {
  ctx.clearRect(0, 0, W, H);
  if (!outcome || outcome.n === 0) return;
  const L = membraneLayout(outcome, W, H);
  for (const u of L.placentas) { disc(ctx, u.x, u.y, u.r, 'rgba(215,123,255,0.14)'); ring(ctx, u.x, u.y, u.r, 1, 'rgba(215,123,255,0.4)'); }
  for (const s of L.sacs) {
    ring(ctx, s.x, s.y, s.r, 1.4, TEAL, 0.6);
    const baby = outcome.babies[s.i];
    fetus(ctx, s.x, s.y, s.r * 0.52, baby && !baby.viable ? 0.4 : 1);
  }
}
