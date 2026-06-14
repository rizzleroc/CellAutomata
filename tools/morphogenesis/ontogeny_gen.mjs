// ONTOGENY — render the REAL docs/ontogeny specimen along the developmental clock,
// for the vertical "use the ontogeny UI" reel. Reuses the app's own engine end to end:
//   sim.js   conceive() + PHASES/LIFE_STAGES + cellsForDay   (the science)
//   render.js buildHeight() — the developmental scene as a height field
//   sem.js   the warm-sepia depth-shader (window.SEM) every lab uses
// Dumps the SEM specimen RGB per frame + the per-frame chrome (caption/day/count) to meta.
// Smoke (sample the whole timeline):  ONTO_NF=14 node tools/morphogenesis/ontogeny_gen.mjs
import fs from 'fs';
import { conceive, getPreset, PHASES, LIFE_STAGES, cellsForDay } from '../../docs/ontogeny/sim.js';
import { buildHeight } from '../../docs/ontogeny/render.js';
globalThis.window = globalThis; globalThis.CA = globalThis.CA || { RULES: {} };
const ev = (0, eval);
ev(fs.readFileSync('docs/web8/experiment/viridis.js', 'utf8'));
ev(fs.readFileSync('docs/web8/experiment/sprites.js', 'utf8'));
ev(fs.readFileSync('docs/web8/experiment/sem.js', 'utf8'));   // sets window.SEM

const BASE = 256, SCALE = 2, OUT = BASE * SCALE;   // 512² micrograph (BASE-relative geometry)
const FPS = 24;
const lerp = (a, b, t) => a + (b - a) * t;
const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);

// chapters = prenatal phases + postnatal life stages (mirrors app.js CH/dayAt)
const CH = [...PHASES.map(p => ({ t: p.t, d: p.d, day: p.day, label: 'Stage' })),
            ...LIFE_STAGES.map(s => ({ t: s.t, d: s.d, day: 266, life: true, label: 'Life' }))];
const LAST = CH.length - 1;
function dayAt(cf) {
  const i = Math.floor(cf), f = cf - i, a = CH[i], b = CH[Math.min(LAST, i + 1)];
  if (!a || a.life) return 266;
  return lerp(a.day, b.life ? 266 : b.day, f);
}

// the showcased scenario: identical MCDA twins — the app's own opening default, seed 7,
// so the embryo visibly SPLITS in two (~day 6) and the diagnosis reads monozygotic · MCDA.
const outcome = conceive(getPreset('mz-mcda').params, 7);

// per-chapter frame budgets (24fps) — linger on the visually rich phases & the split
const BUD = [170,165,165,140,180,120,150,205,170,120,180, 84,84,84,84,84,98];  // 17 chapters
const full = []; for (let i = 0; i < CH.length; i++) { const b = BUD[i]; for (let j = 0; j < b; j++) full.push(Math.min(LAST, i + (b <= 1 ? 0 : j / b))); }
let CF = full;
if (process.env.ONTO_NF) { const m = +process.env.ONTO_NF, out = []; for (let j = 0; j < m; j++) out.push(full[Math.floor(j / (m - 1) * (full.length - 1))]); CF = out; }
const NF = CF.length;

// countLabel — the true number at this phase (ported from render.js)
function countAt(o, day) {
  const groups = new Set(o.babies.map(b => b.mzGroup)).size || 1;
  if (day < 0) return Math.max(1, o.nOocytes);
  if (day < 0.4) return groups;
  return clamp(groups + o.splitEvents.filter(e => e.day <= day).length, 1, o.n || 1);
}
function countLabel(o, day) {
  if (o.n === 0) return { n: 0, unit: 'conceived', sub: '' };
  if (day < 0) { const k = Math.max(1, o.nOocytes); return { n: k, unit: k === 1 ? 'egg' : 'eggs', sub: 'sperm racing' }; }
  if (day < 1) { const k = new Set(o.babies.map(b => b.mzGroup)).size || 1; return { n: k, unit: k === 1 ? 'zygote' : 'zygotes', sub: '46 chromosomes' }; }
  if (day < 14) {
    const k = countAt(o, day), n = cellsForDay(day);
    if (n >= 32) return { n: k, unit: k === 1 ? 'blastocyst' : 'blastocysts', sub: '~64–128 cells' };
    return { n, unit: n === 1 ? 'cell' : 'cells', sub: k > 1 ? `${k} embryos` : 'cleavage' };
  }
  const u = day < 56 ? 'embryo' : day < 266 ? 'fetus' : 'baby';
  const plural = u === 'fetus' ? 'fetuses' : u === 'baby' ? 'babies' : u + 's';
  return { n: o.n, unit: o.n === 1 ? u : plural, sub: o.n >= 2 ? outcome.diagnosis.split(' · ').slice(1).join(' · ') : '' };
}

const hbuf = new Float32Array(BASE * BASE);
const rgba = new Uint8ClampedArray(OUT * OUT * 4);
const rgb = Buffer.alloc(OUT * OUT * 3);
const fd = fs.openSync('/tmp/ontogeny_field.bin', 'w');
const meta = {
  W: OUT, BASE, SCALE, NF, LAST,
  outcome: {
    n: outcome.n, label: outcome.label, zygosity: outcome.zygosity, choType: outcome.choType,
    nOocytes: outcome.nOocytes, placentas: outcome.placentas, sacs: outcome.sacs,
    chromosomes: [...new Set(outcome.babies.map(b => b.chromosomes))], diagnosis: outcome.diagnosis,
    flags: [...new Set(outcome.flags)],
  },
  hint: getPreset('mz-mcda').hint, seed: 7, fr: [],
};
const t0 = Date.now();
for (let f = 0; f < NF; f++) {
  const cf = CF[f], i = clamp(Math.floor(cf), 0, LAST), ch = CH[i], day = dayAt(cf), time = f / FPS;
  buildHeight(hbuf, BASE, { outcome, day, time });
  window.SEM.render(hbuf, BASE, BASE, rgba, { palette: 'warm-sepia', scale: SCALE, relief: 10 });
  for (let p = 0, q = 0; p < OUT * OUT; p++) { rgb[q++] = rgba[p * 4]; rgb[q++] = rgba[p * 4 + 1]; rgb[q++] = rgba[p * 4 + 2]; }
  fs.writeSync(fd, rgb);
  const c = countLabel(outcome, day);
  meta.fr.push({
    i, life: !!ch.life, day: +day.toFixed(2), p: f / NF,
    capLabel: ch.label, capTitle: ch.t, capBlurb: ch.d,
    metaDay: ch.life ? 'BORN' : (day < 0 ? 'DAY 0' : `DAY ${Math.round(day)}`),
    metaPhase: ch.t.toUpperCase(), scale: ch.life ? ch.d : (day < 0 ? 'gametes' : `day ${Math.round(day)}`),
    cn: c.n, cu: c.unit, cs: c.sub,
  });
  if (f % 200 === 0) console.log('frame', f, '/', NF, ((Date.now() - t0) / 1000).toFixed(0) + 's', ch.t, 'day', Math.round(day), c.n, c.unit);
}
fs.closeSync(fd);
fs.writeFileSync('/tmp/ontogeny_meta.json', JSON.stringify(meta));
console.log('DONE', NF, 'frames', ((Date.now() - t0) / 1000).toFixed(0) + 's', '·', outcome.diagnosis);
