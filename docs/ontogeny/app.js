// cellauto · ontogeny — controller. Wires the conditions + parameters to the
// conception engine, plays the developmental clock, and keeps the live diagnosis
// (zygosity · chorionicity · membranes) in sync.
import {
  conceive, PRESETS, getPreset, DEFAULTS, PHASES, LIFE_STAGES, multipleName,
} from './sim.js';
import { drawSpecimen, drawMembranes } from './render.js';

const $ = (id) => document.getElementById(id);
const lerp = (a, b, t) => a + (b - a) * t;
const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

// developmental "chapters" = prenatal phases + postnatal life stages
const CH = [
  ...PHASES.map((p) => ({ t: p.t, d: p.d, day: p.day, label: 'Stage' })),
  ...LIFE_STAGES.map((s) => ({ t: s.t, d: s.d, day: 266, life: true, label: 'Life' })),
];
const LAST = CH.length - 1;
function dayAt(cf) {
  const i = Math.floor(cf), f = cf - i, a = CH[i], b = CH[Math.min(LAST, i + 1)];
  if (!a || a.life) return 266;
  return lerp(a.day, b.life ? 266 : b.day, f);
}

// ── parameter schema (the live, stochastic knobs) ─────────────────────────────
const PARAMS = [
  { key: 'oocytes', label: 'eggs ovulated', min: 1, max: 6, step: 1, fmt: (v) => `${v}` },
  { key: 'fertility', label: 'fertility', min: 0, max: 1, step: 0.05, fmt: (v) => v.toFixed(2) },
  { key: 'zonaBlock', label: 'zona block (vs polyspermy)', min: 0, max: 1, step: 0.02, fmt: (v) => v.toFixed(2) },
  { key: 'splitHazard', label: 'split hazard · per day', min: 0, max: 0.05, step: 0.002, fmt: (v) => v.toFixed(3) },
  { key: 'splitDayBias', label: 'split day (→ chorionicity)', min: 1, max: 14, step: 1, fmt: (v) => `day ${v}` },
  { key: 'nondisjunction', label: 'non-disjunction (aneuploidy)', min: 0, max: 0.05, step: 0.002, fmt: (v) => v.toFixed(3) },
];
const ART = ['natural', 'ovulation-induction', 'ivf-2', 'ivf-3'];

const FLAG = {
  triploidy: { t: 'triploidy · 69 · non-viable', warn: true },
  trisomy21: { t: 'trisomy 21', warn: false },
  chimera: { t: 'chimera · two cell lines', warn: false },
  conjoined: { t: 'conjoined', warn: true },
  'vanishing-twin': { t: 'vanishing twin', warn: false },
};

// ── state ─────────────────────────────────────────────────────────────────────
let params = { ...DEFAULTS };
let presetId = null;
let seed = 7;
let outcome = conceive(params, seed);
let chapterF = 1;            // start at fertilisation
let playing = false;
let time = 0;
const paramRefs = {};

// ── canvases (HiDPI) ──────────────────────────────────────────────────────────
const stage = $('stage'), sctx = stage.getContext('2d');
const memb = $('membranes'), mctx = memb.getContext('2d');
let SW = 0, SH = 0, MW = 0, MH = 0;
function fit() {
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  for (const [cv, ctx, setW] of [[stage, sctx, (w, h) => { SW = w; SH = h; }], [memb, mctx, (w, h) => { MW = w; MH = h; }]]) {
    const r = cv.getBoundingClientRect();
    const w = Math.max(10, Math.round(r.width)), h = Math.max(10, Math.round(r.height));
    cv.width = w * dpr; cv.height = h * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0); setW(w, h);
  }
  drawMembranes(mctx, MW, MH, outcome);
}
window.addEventListener('resize', fit);

// ── build the conditions list ─────────────────────────────────────────────────
const presetList = $('presetList');
PRESETS.forEach((p) => {
  const b = document.createElement('button');
  b.className = 'preset-btn' + (p.id === 'singleton' || p.id === 'dz' ? '' : ' event');
  b.type = 'button'; b.dataset.id = p.id; b.textContent = p.label;
  b.onclick = () => applyPreset(p.id);
  presetList.appendChild(b);
});

// ── build the parameter sliders ───────────────────────────────────────────────
const paramList = $('paramList');
for (const pr of PARAMS) {
  const row = document.createElement('div'); row.className = 'param-row';
  const head = document.createElement('div'); head.className = 'p-head';
  const lab = document.createElement('span'); lab.className = 'p-label'; lab.textContent = pr.label;
  const val = document.createElement('span'); val.className = 'p-val'; val.textContent = pr.fmt(params[pr.key]);
  head.append(lab, val);
  const inp = document.createElement('input'); inp.type = 'range';
  inp.min = pr.min; inp.max = pr.max; inp.step = pr.step; inp.value = params[pr.key];
  inp.setAttribute('aria-label', pr.label);
  inp.oninput = () => { const v = parseFloat(inp.value); val.textContent = pr.fmt(v); setParam(pr.key, v); };
  row.append(head, inp); paramList.appendChild(row);
  paramRefs[pr.key] = { input: inp, val, fmt: pr.fmt };
}
// ART select
{
  const row = document.createElement('div'); row.className = 'param-row';
  const head = document.createElement('div'); head.className = 'p-head';
  const lab = document.createElement('span'); lab.className = 'p-label'; lab.textContent = 'assisted reproduction';
  head.appendChild(lab);
  const sel = document.createElement('select'); sel.setAttribute('aria-label', 'assisted reproduction');
  for (const a of ART) { const o = document.createElement('option'); o.value = a; o.textContent = a; sel.appendChild(o); }
  sel.value = params.art;
  sel.onchange = () => setParam('art', sel.value);
  row.append(head, sel); paramList.appendChild(row);
  paramRefs.art = { input: sel };
}

// ── interactions ──────────────────────────────────────────────────────────────
function applyPreset(id) {
  const p = getPreset(id); if (!p) return;
  presetId = id;
  params = { ...DEFAULTS, ...p.params };
  syncSliders();
  $('presetHint').textContent = p.hint;
  $('presetMeta').textContent = p.label.length > 22 ? 'scenario' : p.label.toLowerCase();
  highlightPreset();
  reconceive(); resetClock();
  announce(`${p.label}. ${outcome.diagnosis}.`);
}
function setParam(key, v) {
  // a hand-tuned knob drops out of the named scenario and goes stochastic
  if (presetId) { presetId = null; $('presetHint').textContent = 'Custom conditions — re-roll the dice to see how they play out.'; $('presetMeta').textContent = 'custom'; }
  delete params._force;
  params[key] = v;
  highlightPreset();
  reconceive();
}
function syncSliders() {
  for (const pr of PARAMS) {
    const ref = paramRefs[pr.key];
    ref.input.value = params[pr.key]; ref.val.textContent = ref.fmt(params[pr.key]);
  }
  paramRefs.art.input.value = params.art;
}
function highlightPreset() {
  presetList.querySelectorAll('.preset-btn').forEach((b) => b.classList.toggle('active', b.dataset.id === presetId));
}
function reconceive() { outcome = conceive(params, seed); paintDiagnosis(); drawMembranes(mctx, MW, MH, outcome); }
$('reseedBtn').onclick = () => { seed = (Math.random() * 1e9) | 0; $('seedMeta').textContent = `seed ${seed}`; reconceive(); resetClock(); };
$('randomBtn').onclick = () => {
  presetId = null; delete params._force;
  params = { ...DEFAULTS,
    oocytes: 1 + ((Math.random() * 3) | 0),
    splitHazard: [0, 0, 0.01, 0.03][(Math.random() * 4) | 0],
    splitDayBias: 1 + ((Math.random() * 13) | 0),
    nondisjunction: Math.random() < 0.3 ? 0.01 : 0,
    art: ART[(Math.random() * ART.length) | 0],
  };
  seed = (Math.random() * 1e9) | 0;
  syncSliders(); highlightPreset();
  $('presetHint').textContent = 'Custom conditions — surprise roll.'; $('presetMeta').textContent = 'custom';
  $('seedMeta').textContent = `seed ${seed}`;
  reconceive(); resetClock();
};

// ── transport / clock ───────────────────────────────────────────────────────────
function setPlaying(on) {
  playing = on && !(reduceMotion.matches && false);
  $('playBtn').setAttribute('aria-pressed', String(playing));
  $('playBtn').querySelector('.play-lbl').textContent = playing ? 'Pause' : 'Play life';
  $('playBtn').querySelector('.play-ico').textContent = playing ? '❚❚' : '▶';
  document.querySelector('.vitrine').classList.toggle('is-running', playing);
}
$('playBtn').onclick = () => { if (chapterF >= LAST) chapterF = 0; setPlaying(!playing); };
$('stepBtn').onclick = () => { setPlaying(false); chapterF = clamp(Math.floor(chapterF) + 1, 0, LAST); syncScrub(); updateChapterUI(); };
$('resetBtn').onclick = () => { resetClock(); };
function resetClock() { setPlaying(false); chapterF = 1; syncScrub(); updateChapterUI(); }
$('scrub').oninput = () => { setPlaying(false); chapterF = parseFloat($('scrub').value) / 1000 * LAST; updateChapterUI(); };
function syncScrub() { $('scrub').value = String(Math.round(chapterF / LAST * 1000)); }

let lastChapterIdx = -1;
function updateChapterUI() {
  const i = clamp(Math.floor(chapterF), 0, LAST), ch = CH[i], day = dayAt(chapterF);
  $('capLabel').textContent = ch.label;
  $('capTitle').textContent = ch.t;
  $('capBlurb').textContent = ch.d;
  $('metaPhase').textContent = ch.t.toUpperCase();
  $('metaDay').textContent = ch.life ? 'BORN' : (day < 0 ? 'DAY 0' : `DAY ${Math.round(day)}`);
  $('stageScale').textContent = ch.life ? ch.d : (day < 0 ? 'gametes' : `day ${Math.round(day)}`);
  if (i !== lastChapterIdx) { lastChapterIdx = i; announce(ch.t); }
}

// ── diagnosis panel ─────────────────────────────────────────────────────────────
function paintDiagnosis() {
  $('verdictCount').textContent = String(outcome.n);
  $('verdictLabel').textContent = outcome.label;
  $('verdictZyg').textContent = outcome.n === 0 ? '—'
    : outcome.zygosity + (outcome.choType ? ` · ${outcome.choType}` : '');
  $('statEggs').textContent = String(outcome.nOocytes);
  $('statPlacentas').textContent = String(outcome.placentas);
  $('statSacs').textContent = String(outcome.sacs);
  const chs = [...new Set(outcome.babies.map((b) => b.chromosomes))];
  $('statChromo').textContent = chs.length ? chs.join(' / ') : '—';
  $('membranesCap').textContent = outcome.n >= 2
    ? `${outcome.placentas} placenta${outcome.placentas > 1 ? 's' : ''} · ${outcome.sacs} sac${outcome.sacs > 1 ? 's' : ''}${outcome.choType ? ` · ${outcome.choType}` : ''}`
    : 'one placenta · one sac';
  // flags
  const f = $('flags'); f.innerHTML = ''; const flags = [...new Set(outcome.flags)];
  f.hidden = flags.length === 0;
  for (const key of flags) {
    const meta = FLAG[key] || { t: key };
    const chip = document.createElement('span');
    chip.className = 'flag' + (meta.warn ? ' warn' : '');
    chip.textContent = meta.t; f.appendChild(chip);
  }
  $('diagNote').textContent = note();
}
function note() {
  if (outcome.n === 0) return 'No conception this cycle — fertilisation did not occur.';
  if (presetId) return getPreset(presetId).hint;
  if (outcome.flags.includes('triploidy')) return 'A second sperm entered: 69 chromosomes — almost always non-viable.';
  if (outcome.zygosity === 'monozygotic') {
    const d = outcome.splitEvents[0]?.day;
    return `Identical — one egg split${d ? ` on day ${d}` : ''}, so the babies share a genome (${outcome.choType}).`;
  }
  if (outcome.zygosity.includes('zygotic')) return `${outcome.nOocytes} eggs were each fertilised — siblings who happen to share a womb.`;
  if (outcome.n === 1) return 'A single embryo implants and runs the whole programme to birth.';
  return outcome.diagnosis + '.';
}

function announce(msg) { const s = $('srStatus'); if (s) s.textContent = msg; }

// ── render loop ─────────────────────────────────────────────────────────────────
let raf = 0, lastT = performance.now();
function frame(now) {
  const dt = Math.min(0.05, (now - lastT) / 1000); lastT = now; time += dt;
  if (playing) {
    chapterF += dt * 0.62 * (params.clock / 12);
    if (chapterF >= LAST) { chapterF = LAST; setPlaying(false); }
    syncScrub(); updateChapterUI();
  }
  drawSpecimen(sctx, SW, SH, { outcome, day: dayAt(chapterF), time });
  raf = requestAnimationFrame(frame);
}

// ── boot ──────────────────────────────────────────────────────────────────────
function boot() {
  fit();
  applyPreset('mz-mcda');            // open on a striking, instructive case: identical MCDA twins
  $('seedMeta').textContent = `seed ${seed}`;
  updateChapterUI();
  raf = requestAnimationFrame(frame);
}
boot();
