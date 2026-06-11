// cellauto · ontogeny — the renderer. Draws the determined conception outcome at
// any point on the developmental clock: gametes → fertilisation → cleavage → the
// twinning split → the membranes → fetuses → birth. Canvas 2D, zero deps.
import { cellsForDay } from './sim.js';

const OB = '#07090d', TEAL = '#3fe0d0', TEAL_D = '#1f8f86', TEAL_B = '#74f4e7',
      BONE = '#ece7da', BONE_D = '#9a9280', MAG = '#d77bff';

const lerp = (a, b, t) => a + (b - a) * t;
const clamp = (v, a, b) => v < a ? a : v > b ? b : v;
const ease = (t) => (t < 0 ? 0 : t > 1 ? 1 : t * t * (3 - 2 * t));

function disc(ctx, x, y, r, fill, a = 1) {
  ctx.globalAlpha = a; ctx.fillStyle = fill;
  ctx.beginPath(); ctx.arc(x, y, Math.max(0, r), 0, 7); ctx.fill(); ctx.globalAlpha = 1;
}
function ring(ctx, x, y, r, w, stroke, a = 1) {
  ctx.globalAlpha = a; ctx.strokeStyle = stroke; ctx.lineWidth = w;
  ctx.beginPath(); ctx.arc(x, y, Math.max(0, r), 0, 7); ctx.stroke(); ctx.globalAlpha = 1;
}
function cell(ctx, x, y, r, a = 1) {
  const g = ctx.createRadialGradient(x - r * 0.3, y - r * 0.3, r * 0.1, x, y, r);
  g.addColorStop(0, TEAL_B); g.addColorStop(1, TEAL_D);
  disc(ctx, x, y, r, g, a); ring(ctx, x, y, r, 1, TEAL, a * 0.5);
}
function cluster(ctx, cx, cy, n, R, a = 1) {
  const cr = n <= 1 ? R * 0.92 : Math.max(2.4, R / Math.sqrt(n) * 0.95);
  for (let i = 0; i < n; i++) {
    if (n === 1) { cell(ctx, cx, cy, cr, a); continue; }
    const ang = i * 2.399963, rr = R * 0.74 * Math.sqrt(i / n);
    cell(ctx, cx + rr * Math.cos(ang), cy + rr * Math.sin(ang), cr, a);
  }
}
function oocyte(ctx, x, y, r, a = 1) {
  disc(ctx, x, y, r, TEAL_D, a * 0.55); ring(ctx, x, y, r + 3, 3, BONE_D, a * 0.45);
  disc(ctx, x - r * 0.2, y - r * 0.2, r * 0.3, TEAL_B, a * 0.7);
}
function sperm(ctx, x, y, ang, a, time) {
  disc(ctx, x, y, 2.4, BONE, a);
  for (let k = 1; k <= 4; k++) {
    const wob = Math.sin(k * 1.3 + time * 9 + x * 0.1) * 1.7;
    disc(ctx, x - Math.cos(ang) * k * 2.6 + Math.cos(ang + 1.57) * wob,
             y - Math.sin(ang) * k * 2.6 + Math.sin(ang + 1.57) * wob,
             Math.max(0.6, 1.9 - k * 0.32), BONE_D, a * (1 - k * 0.2));
  }
}
// a stylised curled fetus, scale ~ radius of the curl
function fetus(ctx, x, y, s, a = 1) {
  ctx.save(); ctx.translate(x, y); ctx.globalAlpha = a;
  const g = ctx.createRadialGradient(-s * 0.2, -s * 0.2, s * 0.1, 0, 0, s);
  g.addColorStop(0, TEAL_B); g.addColorStop(1, TEAL_D);
  ctx.fillStyle = g;
  ctx.beginPath();                     // body — a comma/curl
  ctx.arc(0, 0, s, Math.PI * 0.15, Math.PI * 1.55);
  ctx.quadraticCurveTo(-s * 0.2, -s * 0.2, s * 0.55, -s * 0.75);
  ctx.closePath(); ctx.fill();
  disc(ctx, s * 0.45, -s * 0.7, s * 0.42, g, a);   // head
  ring(ctx, 0, 0, s, 1, TEAL, a * 0.4);
  ctx.globalAlpha = 1; ctx.restore();
}

// how many distinct conceptuses are visible at `day`
function countAt(outcome, day) {
  const groups = new Set(outcome.babies.map((b) => b.mzGroup)).size || 1;
  if (day < 0) return Math.max(1, outcome.nOocytes);
  if (day < 0.4) return groups;
  const splits = outcome.splitEvents.filter((e) => e.day <= day).length;
  return clamp(groups + splits, 1, outcome.n || 1);
}
// horizontal slots for k specimens across width W
function slots(k, W, H) {
  const out = []; const y = H * 0.5;
  if (k <= 1) return [[W * 0.5, y]];
  for (let i = 0; i < k; i++) out.push([lerp(W * 0.24, W * 0.76, i / (k - 1)), y]);
  return out;
}

// ── the main specimen canvas — the developing embryo(s) at `day` ──────────────
export function drawSpecimen(ctx, W, H, st) {
  const { outcome, day, time = 0 } = st;
  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = OB; ctx.fillRect(0, 0, W, H);
  // vignette
  const vg = ctx.createRadialGradient(W / 2, H / 2, Math.min(W, H) * 0.2, W / 2, H / 2, Math.max(W, H) * 0.62);
  vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,0.55)');
  ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
  if (!outcome || outcome.n === 0) { return; }

  const cx = W / 2, cy = H / 2;

  if (day < 0) {                                   // ── gametes: the race ──
    const k = Math.max(1, outcome.nOocytes);
    for (const [ox, oy] of slots(k, W, H)) {
      oocyte(ctx, ox, oy, 26, 1);
      const p = ease(clamp((time % 3) / 2.4, 0, 1));
      for (let i = 0; i < 12; i++) {
        const ang = i / 12 * 6.283 + 0.2, d = lerp(150, 30, p * (0.8 + 0.3 * ((i * 7) % 5) / 5));
        sperm(ctx, ox + Math.cos(ang) * d, oy + Math.sin(ang) * d, ang + Math.PI, 0.9, time);
      }
    }
    return;
  }

  if (day < 1) {                                   // ── fertilisation flash ──
    const k = new Set(outcome.babies.map((b) => b.mzGroup)).size || 1;
    for (const [ox, oy] of slots(k, W, H)) {
      cell(ctx, ox, oy, 24, 1);
      const u = clamp(day / 0.8, 0, 1);
      ring(ctx, ox, oy, 30 + u * 26, 3, BONE, (1 - u) * 0.9);
      ring(ctx, ox, oy, 18 + u * 34, 2, TEAL_B, (1 - u) * 0.7);
    }
    return;
  }

  if (day < 14) {                                  // ── cleavage → blastocyst → split ──
    const k = countAt(outcome, day);
    const n = cellsForDay(day);
    for (const [ox, oy] of slots(k, W, H)) {
      if (day < 5.2 && k === 1) ring(ctx, ox, oy, 30, 2, BONE_D, clamp(0.35 * (1 - (day - 1) / 4), 0, 0.35)); // zona
      if (n >= 32) { ring(ctx, ox, oy, 24, 2, TEAL, 0.5); cluster(ctx, ox - 6, oy, 8, 12, 1); } // blastocyst: ICM + cavity
      else cluster(ctx, ox, oy, n, 24, 1);
    }
    // a split just happened? pulse the newest pair
    const recent = outcome.splitEvents.filter((e) => Math.abs(e.day - day) < 0.6);
    if (recent.length && k >= 2) {
      const s = slots(k, W, H);
      ring(ctx, s[k - 1][0], s[k - 1][1], 30, 2, MAG, 0.6);
    }
    return;
  }

  // ── implantation → fetal: the womb view (membranes + growing fetuses) ──
  drawWomb(ctx, W, H, outcome, day, time);
}

// shared womb/membrane drawing, scaled to fill the box
function drawWomb(ctx, W, H, outcome, day, time) {
  const grow = ease(clamp((day - 14) / (266 - 14), 0, 1));   // 0 at gastrulation → 1 at birth
  const beat = day >= 22 ? 1 + 0.05 * Math.sin(time * 7) : 1; // heart beats from ~day 22
  const layout = membraneLayout(outcome, W, H);
  for (const u of layout.placentas) disc(ctx, u.x, u.y, u.r, 'rgba(215,123,255,0.13)');
  for (const u of layout.placentas) ring(ctx, u.x, u.y, u.r, 1, 'rgba(215,123,255,0.35)');
  for (const s of layout.sacs) {
    ring(ctx, s.x, s.y, s.r, 1.5, TEAL, 0.5);
    const baby = outcome.babies[s.i];
    const dead = baby && !baby.viable;
    if (day < 56) cluster(ctx, s.x, s.y, 12, Math.max(8, s.r * 0.42 * grow + 6), dead ? 0.4 : 1);
    else fetus(ctx, s.x, s.y, (s.r * 0.62) * (0.5 + 0.5 * grow) * beat, dead ? 0.4 : 1);
  }
}

// place placentas + sacs given the outcome's membranes (visual, in the box)
function membraneLayout(outcome, W, H) {
  const cx = W / 2, cy = H / 2;
  const byGroup = {};
  outcome.babies.forEach((b, i) => (byGroup[b.mzGroup] ??= []).push(i));
  const groups = Object.values(byGroup);
  const placentas = [], sacs = [];
  const gslots = slots(groups.length, W, H);
  groups.forEach((idxs, gi) => {
    const [gx] = gslots[gi]; const gy = cy;
    const shared = idxs.length > 1 && ['MCDA', 'MCMA', 'conjoined'].includes(outcome.babies[idxs[0]].cho?.type);
    const pr = clamp(Math.min(W, H) * (groups.length > 2 ? 0.16 : 0.22), 40, 150);
    if (shared) {
      placentas.push({ x: gx, y: gy, r: pr });
      const mcma = ['MCMA', 'conjoined'].includes(outcome.babies[idxs[0]].cho?.type);
      idxs.forEach((bi, k) => {
        const off = idxs.length === 1 ? 0 : (k - (idxs.length - 1) / 2) * pr * 0.55;
        if (mcma) sacs.push({ x: gx, y: gy, r: pr * 0.7, i: bi });          // one shared sac
        else sacs.push({ x: gx + off, y: gy, r: pr * 0.42, i: bi });        // separate sacs
      });
      if (mcma) { // one big sac for the group
        sacs.length -= idxs.length;
        sacs.push({ x: gx, y: gy, r: pr * 0.72, i: idxs[0] });
        if (idxs.length > 1) idxs.slice(1).forEach((bi, k) =>
          sacs.push({ x: gx + (k - 0.5) * pr * 0.5, y: gy, r: pr * 0.45, i: bi, sub: true }));
      }
    } else {
      idxs.forEach((bi, k) => {
        const off = idxs.length === 1 ? 0 : (k - (idxs.length - 1) / 2) * pr * 1.1;
        placentas.push({ x: gx + off, y: gy, r: pr * 0.66 });
        sacs.push({ x: gx + off, y: gy, r: pr * 0.46, i: bi });
      });
    }
  });
  return { placentas, sacs };
}

// ── the diagnosis-panel membrane diagram (compact, schematic) ─────────────────
export function drawMembranes(ctx, W, H, outcome) {
  ctx.clearRect(0, 0, W, H);
  if (!outcome || outcome.n === 0) return;
  const layout = membraneLayout(outcome, W, H);
  for (const u of layout.placentas) { disc(ctx, u.x, u.y, u.r, 'rgba(215,123,255,0.14)'); ring(ctx, u.x, u.y, u.r, 1, 'rgba(215,123,255,0.4)'); }
  for (const s of layout.sacs) {
    ring(ctx, s.x, s.y, s.r, 1.4, TEAL, 0.6);
    const baby = outcome.babies[s.i];
    fetus(ctx, s.x, s.y, s.r * 0.5, baby && !baby.viable ? 0.4 : 1);
  }
}
