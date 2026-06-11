// Ontogeny engine contract (zero-dep). Defends PRD_ONTOGENY §8 acceptance:
// the conditions produce the right biology, deterministically where the label
// demands it and in the right distribution where it's stochastic.
import {
  conceive, chorionicityForSplitDay, cellsForDay, phaseForDay,
  PRESETS, getPreset, DEFAULTS,
} from '../sim.js';

let pass = 0; const fails = [];
const ok = (c, m) => { if (c) pass++; else fails.push(m); };
console.log('Running ontogeny engine tests…\n');

// 1 · the real twin rule: split DAY → membranes -------------------------------
ok(chorionicityForSplitDay(2).type === 'DCDA', 'day 1–3 split must be DCDA');
ok(chorionicityForSplitDay(6).type === 'MCDA', 'day 4–8 split must be MCDA');
ok(chorionicityForSplitDay(10).type === 'MCMA', 'day 8–13 split must be MCMA');
ok(chorionicityForSplitDay(14).type === 'conjoined', 'day 13+ split must be conjoined');
ok(chorionicityForSplitDay(6).placentas === 1 && chorionicityForSplitDay(6).sacs === 2,
  'MCDA = 1 placenta / 2 sacs');

// 2 · cleavage clock -----------------------------------------------------------
ok(cellsForDay(-1) === 0 && cellsForDay(0.5) === 1 && cellsForDay(1) === 2 &&
   cellsForDay(3) === 8 && cellsForDay(6) === 64, 'cleavage doubles 1→2→…→blastocyst');
ok(phaseForDay(0).key === 'fertilisation' && phaseForDay(5).key === 'blastocyst' &&
   phaseForDay(266).key === 'birth', 'developmental phases map by day');

// 3 · every preset yields its labelled outcome --------------------------------
const expect = {
  'singleton':     { n: 1, zyg: 'singleton' },
  'mz-dcda':       { n: 2, zyg: 'monozygotic', cho: 'DCDA', placentas: 2, sacs: 2 },
  'mz-mcda':       { n: 2, zyg: 'monozygotic', cho: 'MCDA', placentas: 1, sacs: 2 },
  'mz-mcma':       { n: 2, zyg: 'monozygotic', cho: 'MCMA', placentas: 1, sacs: 1 },
  'conjoined':     { n: 2, zyg: 'monozygotic', flag: 'conjoined' },
  'dz':            { n: 2, zyg: 'dizygotic', placentas: 2, sacs: 2 },
  'triplets-tri':  { n: 3, zyg: 'polyzygotic' },
  'triplets-2-1':  { n: 3 },
  'quads':         { n: 4 },
  'quints':        { n: 5, zyg: 'polyzygotic' },
  'triploidy':     { n: 1, flag: 'triploidy', viable: false },
  'trisomy':       { n: 1, flag: 'trisomy21', viable: true },
  'chimerism':     { n: 1, flag: 'chimera' },
  'vanishing':     { n: 1, flag: 'vanishing-twin' },
};
ok(PRESETS.length === Object.keys(expect).length, `every preset is tested (${PRESETS.length})`);
for (const preset of PRESETS) {
  const e = expect[preset.id];
  ok(!!e, `preset "${preset.id}" has an expectation`);
  if (!e) continue;
  // deterministic where _force is set; otherwise it must hold across many seeds
  const det = !!preset.params._force;
  const seeds = det ? [1] : [1, 2, 3, 7, 42, 99, 1000];
  for (const s of seeds) {
    const r = conceive(preset.params, s);
    ok(r.n === e.n, `${preset.id} (seed ${s}): expected ${e.n} baby/babies, got ${r.n} [${r.diagnosis}]`);
    if (e.zyg) ok(r.zygosity === e.zyg, `${preset.id}: expected ${e.zyg}, got ${r.zygosity}`);
    if (e.cho) ok(r.choType === e.cho, `${preset.id}: expected ${e.cho}, got ${r.choType}`);
    if (e.placentas != null) ok(r.placentas === e.placentas, `${preset.id}: expected ${e.placentas} placentas, got ${r.placentas}`);
    if (e.sacs != null) ok(r.sacs === e.sacs, `${preset.id}: expected ${e.sacs} sacs, got ${r.sacs}`);
    if (e.flag) ok(r.flags.includes(e.flag), `${preset.id}: expected flag ${e.flag}, got [${r.flags}]`);
    if (e.viable != null) ok(r.viable === e.viable, `${preset.id}: expected viable=${e.viable}`);
  }
}

// 4 · dizygotic from polyovulation is always DCDA-equivalent -------------------
{
  const r = conceive({ oocytes: 2, splitHazard: 0, fertility: 1, zonaBlock: 1, spermMotility: 1 }, 5);
  ok(r.n === 2 && r.zygosity === 'dizygotic', `polyovulation → dizygotic twins (got ${r.diagnosis})`);
  ok(r.placentas === 2 && r.sacs === 2, 'fraternal twins are always 2 placentas / 2 sacs');
}

// 5 · Hellin's-rule order of magnitude (twins ≪ singletons) --------------------
{
  let singles = 0, twins = 0, more = 0, none = 0;
  const N = 3000;
  for (let s = 1; s <= N; s++) {
    const r = conceive({ oocytes: 1, splitHazard: 0.02, splitDayBias: 6, fertility: 0.95, zonaBlock: 1 }, s);
    if (r.n === 0) none++; else if (r.n === 1) singles++; else if (r.n === 2) twins++; else more++;
  }
  ok(twins > 0, 'a low split hazard does produce some monozygotic twins');
  ok(twins < singles / 5, `twins must be far rarer than singletons (twins ${twins} ≪ singletons ${singles})`);
  ok(more <= twins, 'higher-order from a single egg is rarer still');
}

// 6 · split timing steers chorionicity AND the neutral default reproduces the
//     REAL monozygotic chorionicity frequencies (the calibration that matters) -
{
  const tally = (bias, n = 8000) => {
    const t = { DCDA: 0, MCDA: 0, MCMA: 0, conjoined: 0 }; let tw = 0;
    for (let s = 1; s <= n; s++) {
      const r = conceive({ oocytes: 1, splitHazard: 0.5, splitDayBias: bias, fertility: 1, zonaBlock: 1 }, s);
      if (r.zygosity === 'monozygotic' && r.choType) { tw++; t[r.choType]++; }
    }
    return { t, tw };
  };
  const dom = (bias) => { const { t } = tally(bias); return Object.entries(t).sort((a, b) => b[1] - a[1])[0][0]; };
  ok(dom(2) === 'DCDA', 'early split timing → mostly DCDA');
  ok(dom(6) === 'MCDA', 'neutral split timing → mostly MCDA');
  // neutral default must reproduce real frequencies: ~25–30% DCDA, ~70% MCDA, ~1–5% MCMA
  const { t, tw } = tally(6, 40000);
  const f = (k) => t[k] / tw;
  ok(f('DCDA') > 0.20 && f('DCDA') < 0.35, `neutral DCDA ≈ 25-30% (got ${(f('DCDA') * 100).toFixed(1)}%)`);
  ok(f('MCDA') > 0.60 && f('MCDA') < 0.75, `neutral MCDA ≈ 70% (got ${(f('MCDA') * 100).toFixed(1)}%)`);
  ok(f('MCMA') < 0.10, `neutral MCMA ≈ 1-5% (got ${(f('MCMA') * 100).toFixed(1)}%)`);
  const lt = tally(11);
  ok((lt.t.MCMA + lt.t.conjoined) / lt.tw > 0.6, 'late split timing → mostly MCMA / conjoined');
  // realistic spontaneous rate at the default hazard
  let twins = 0, N = 60000;
  for (let s = 1; s <= N; s++) if (conceive({ oocytes: 1, fertility: 1, zonaBlock: 1 }, s).n === 2) twins++;
  const oneIn = N / twins;
  ok(oneIn > 150 && oneIn < 400, `default MZ twin rate ≈ 1/250 (got 1/${Math.round(oneIn)})`);
}

// 7 · zona block failure → triploidy, non-viable ------------------------------
{
  const r = conceive({ oocytes: 1, zonaBlock: 0, _force: { fertilize: 1, splits: [] } }, 1);
  ok(r.flags.includes('triploidy') && !r.viable && r.babies[0].chromosomes === 69,
    'no zona block → 69 chromosomes, non-viable');
}

// ── report ────────────────────────────────────────────────────────────────────
if (fails.length) console.error('\n' + fails.map((f) => '  ✗ ' + f).join('\n'));
console.log(`\n${pass} checks passed, ${fails.length} failure(s).`);
process.exit(fails.length ? 1 : 0);
