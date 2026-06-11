// cellauto · ontogeny — the conception engine.
//
// A real, seedable, stochastic model of the origin of an INDIVIDUAL life:
// ovulation → fertilisation (with the zona polyspermy block) → the embryo-
// splitting hazard whose TIMING sets the shared membranes → the multiples.
// This is the scientifically load-bearing core (PRD_ONTOGENY §3 "REAL"): run it
// many times and the outcome distribution emerges from the parameters; it is not
// scripted. Pure ES module, zero deps, so the browser and the test gate share it.
//
// Sources: standard human embryology (Carnegie stages); twin chorionicity-by-
// split-day; Hellin's rule for multiple-birth frequency; ART multiple-gestation.

// ── seeded RNG (mulberry32) — reproducible runs for the UI and the tests ──────
export function mulberry32(seed) {
  let a = (seed >>> 0) || 1;
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ── the real twin rule: the DAY an embryo splits sets the shared membranes ────
export function chorionicityForSplitDay(d) {
  if (d <= 3)  return { type: 'DCDA',      placentas: 2, sacs: 2, label: 'dichorionic diamniotic' };
  if (d <= 8)  return { type: 'MCDA',      placentas: 1, sacs: 2, label: 'monochorionic diamniotic' };
  if (d <= 13) return { type: 'MCMA',      placentas: 1, sacs: 1, label: 'monochorionic monoamniotic' };
  return         { type: 'conjoined', placentas: 1, sacs: 1, label: 'conjoined (incomplete split)' };
}

export const DEFAULTS = {
  oocytes: 1,          // eggs ovulated this cycle (the dizygotic / higher-order root)
  spermMotility: 0.75, // race quality → fertilisation odds
  fertility: 0.9,      // per-oocyte fertilisation probability
  zonaBlock: 0.98,     // polyspermy block efficiency (low → triploidy)
  splitHazard: 0.0,    // per-day probability a conceptus splits (monozygotic propensity)
  splitDayBias: 5,     // WHEN splits cluster → DCDA / MCDA / MCMA / conjoined
  nondisjunction: 0.0, // meiotic error rate → aneuploidy / trisomy
  fusion: 0.0,         // two zygotes merge → chimerism
  vanish: 0.0,         // a conceptus is reabsorbed early → vanishing twin
  art: 'natural',      // natural · ovulation-induction · ivf-2 · ivf-3
  clock: 12,           // developmental-timeline speed (days · s⁻¹)
};

const MULT = ['—', 'singleton', 'twins', 'triplets', 'quadruplets', 'quintuplets',
              'sextuplets', 'septuplets', 'octuplets', 'nonuplets'];
export const multipleName = (n) => MULT[n] || `${n}-tuplets`;

// Triangular bias so splits cluster near splitDayBias (used in free play).
const biasWeight = (day, peak) => Math.max(0, 1 - Math.abs(day - peak) / 3.2);

// ── the conception event — stochastic, returns the determined outcome ─────────
// `params._force` (set by deterministic presets) bypasses the dice so a labelled
// outcome is guaranteed; otherwise everything is rolled from the params + seed.
export function conceive(params = {}, seed = 1) {
  const p = { ...DEFAULTS, ...params };
  const force = p._force || null;
  const rng = mulberry32(seed);

  // 1 · how many oocytes ovulate (ART shifts this)
  let nOocytes = p.oocytes;
  if (!force) {
    if (p.art === 'ovulation-induction') nOocytes += 1 + Math.floor(rng() * 2);
    else if (p.art === 'ivf-2') nOocytes = Math.max(nOocytes, 2);
    else if (p.art === 'ivf-3') nOocytes = Math.max(nOocytes, 3);
  }

  // 2 · fertilisation + ploidy hazards
  const zygotes = [];
  const nTry = force ? force.fertilize : nOocytes;
  for (let i = 0; i < nTry; i++) {
    const ok = force ? true : rng() < p.fertility * (0.55 + 0.45 * p.spermMotility);
    if (!ok) continue;
    const z = { id: i, chromosomes: 46, flags: [], viable: true };
    const blockFail = force ? p.zonaBlock <= 1e-4 : rng() > p.zonaBlock;   // polyspermy
    if (blockFail) { z.chromosomes = 69; z.flags.push('triploidy'); z.viable = false; }
    const ndj = force ? p.nondisjunction >= 0.999 : rng() < p.nondisjunction;
    if (ndj && z.chromosomes === 46) { z.chromosomes = 47; z.flags.push('trisomy21'); }
    zygotes.push(z);
  }

  // 3 · monozygotic splitting (the mechanism that makes "identical" multiples)
  const splitEvents = [];
  let babies = [];
  zygotes.forEach((z, zi) => {
    const mk = (splitDay, cho) => ({ mzGroup: zi, chromosomes: z.chromosomes,
      flags: [...z.flags], viable: z.viable, splits: splitDay ? [splitDay] : [], cho: cho || null });
    const lineage = [mk(null, null)];
    if (force) {
      for (const s of (force.splits || []).filter((s) => (s.zygoteIndex ?? 0) === zi)) {
        const cho = chorionicityForSplitDay(s.day);
        const parent = lineage[0];
        parent.splits.push(s.day); parent.cho = cho;
        lineage.push(mk(s.day, cho));
        splitEvents.push({ day: s.day, zygote: zi, cho });
      }
    } else {
      for (let day = 1; day <= 14; day++) {
        const hz = p.splitHazard * biasWeight(day, p.splitDayBias);
        if (hz <= 0) continue;
        for (const b of [...lineage]) {
          if (b.splits.length === 0 && rng() < hz) {
            const cho = chorionicityForSplitDay(day);
            b.splits.push(day); b.cho = cho;
            lineage.push(mk(day, cho));
            splitEvents.push({ day, zygote: zi, cho });
          }
        }
      }
    }
    babies.push(...lineage);
  });

  // 4 · chimerism — two zygotes fuse into one individual (the inverse of a split)
  const fuse = force ? !!force.fuse : p.fusion > 0 && rng() < p.fusion;
  if (fuse && new Set(babies.map((b) => b.mzGroup)).size >= 2) {
    const i = babies.findIndex((b) => b.mzGroup !== babies[0].mzGroup);
    babies[0].flags.push('chimera');
    babies.splice(i, 1);
  }

  // 5 · vanishing twin — early reabsorption
  let vanished = 0;
  if (force ? force.vanish : p.vanish > 0) {
    const want = force ? force.vanish : Infinity;
    babies = babies.filter((b) => {
      if (vanished < want && babies.length - vanished > 1 &&
          (force ? true : rng() < p.vanish)) { vanished++; return false; }
      return true;
    });
  }

  return classify(babies, vanished, splitEvents, nOocytes);
}

// ── classify the determined outcome (zygosity · chorionicity · membranes) ─────
function classify(babies, vanished, splitEvents, nOocytes) {
  const n = babies.length;
  const groups = new Set(babies.map((b) => b.mzGroup));
  let zygosity;
  if (n <= 1) zygosity = 'singleton';
  else if (groups.size === 1) zygosity = 'monozygotic';
  else if (groups.size === n) zygosity = n === 2 ? 'dizygotic' : 'polyzygotic';
  else zygosity = 'mixed zygosity';

  // membranes — placentas (chorions) + sacs (amnions)
  const byGroup = {};
  for (const b of babies) (byGroup[b.mzGroup] ??= []).push(b);
  let placentas = 0, sacs = 0;
  let choType = null;
  for (const g of Object.values(byGroup)) {
    if (g.length === 1) { placentas++; sacs++; continue; }
    const types = g.map((b) => b.cho?.type).filter(Boolean);
    if (types.includes('conjoined')) { placentas += 1; sacs += 1; choType = 'conjoined'; }
    else if (types.includes('MCMA')) { placentas += 1; sacs += 1; choType ||= 'MCMA'; }
    else if (types.includes('MCDA')) { placentas += 1; sacs += g.length; choType ||= 'MCDA'; }
    else { placentas += g.length; sacs += g.length; choType ||= 'DCDA'; }
  }

  const flags = [...new Set(babies.flatMap((b) => b.flags))];
  if (babies.some((b) => b.cho?.type === 'conjoined')) flags.push('conjoined');
  if (vanished) flags.push('vanishing-twin');
  const viable = babies.length > 0 && babies.every((b) => b.viable);

  const label = multipleName(n);
  const choLabel = zygosity === 'monozygotic' && choType
    ? ` · ${choType}` : '';
  const memb = n >= 2 ? ` — ${placentas} placenta${placentas > 1 ? 's' : ''} / ${sacs} sac${sacs > 1 ? 's' : ''}` : '';
  const diagnosis = n === 0
    ? 'no conception'
    : `${n} ${n === 1 ? 'baby' : 'babies'} · ${zygosity}${choLabel}${memb}`;

  return { n, zygosity, choType, babies, flags, vanished, viable,
    placentas, sacs, label, diagnosis, splitEvents, nOocytes };
}

// ── the conditions, one click each — the heart of the request ─────────────────
// Deterministic presets carry `_force` so the labelled outcome is guaranteed;
// the open-ended ones (typical, ART) only bias the params and let the dice run.
export const PRESETS = [
  { id: 'singleton', label: 'Singleton (typical)',
    hint: 'One egg, one sperm, no split — the ordinary case: a single baby.',
    params: { oocytes: 1, splitHazard: 0, art: 'natural', _force: { fertilize: 1, splits: [] } } },

  { id: 'mz-dcda', label: 'Identical twins — DCDA',
    hint: 'One egg splits on days 1–3 (before the placenta forms): two placentas, two sacs. ~25–30% of identical twins.',
    params: { oocytes: 1, _force: { fertilize: 1, splits: [{ day: 2 }] } } },
  { id: 'mz-mcda', label: 'Identical twins — MCDA',
    hint: 'One egg splits on days 4–8 (blastocyst): a SHARED placenta, two sacs. The most common identical type (~70%), and the one at risk of TTTS.',
    params: { oocytes: 1, _force: { fertilize: 1, splits: [{ day: 6 }] } } },
  { id: 'mz-mcma', label: 'Identical twins — MCMA',
    hint: 'One egg splits on days 8–13 (after the amnion): one placenta, one shared sac. Rare (~1–5%); cord-entanglement risk.',
    params: { oocytes: 1, _force: { fertilize: 1, splits: [{ day: 10 }] } } },
  { id: 'conjoined', label: 'Conjoined (late split)',
    hint: 'The split begins after day 13, once the body axis has formed, so it never completes — the twins remain joined. <1% of identical twins.',
    params: { oocytes: 1, _force: { fertilize: 1, splits: [{ day: 14 }] } } },

  { id: 'dz', label: 'Fraternal twins (2 eggs)',
    hint: 'Two eggs ovulate and each is fertilised by a different sperm — ordinary siblings sharing a womb. Always two placentas, two sacs.',
    params: { oocytes: 2, _force: { fertilize: 2, splits: [] } } },

  { id: 'triplets-tri', label: 'Triplets — trizygotic',
    hint: 'Three eggs, three sperm — three independent zygotes.',
    params: { oocytes: 3, _force: { fertilize: 3, splits: [] } } },
  { id: 'triplets-2-1', label: 'Triplets — 2+1',
    hint: 'Two eggs; one of them splits — a set of identical twins plus a fraternal sibling.',
    params: { oocytes: 2, _force: { fertilize: 2, splits: [{ day: 5, zygoteIndex: 0 }] } } },

  { id: 'quads', label: 'Quadruplets (ART)',
    hint: 'Two transferred embryos that each split — two identical pairs. Higher-order multiples are dominated by fertility treatment.',
    params: { oocytes: 2, art: 'ivf-2', _force: { fertilize: 2, splits: [{ day: 4, zygoteIndex: 0 }, { day: 4, zygoteIndex: 1 }] } } },
  { id: 'quints', label: 'Quintuplets (ART)',
    hint: 'Five zygotes — essentially only seen with ovulation induction or multi-embryo transfer. Spontaneous quintuplets are ~1 in 50 million.',
    params: { oocytes: 5, art: 'ivf-3', _force: { fertilize: 5, splits: [] } } },

  { id: 'triploidy', label: 'Polyspermy → triploidy',
    hint: 'The zona block fails, a second sperm enters, and the zygote has 69 chromosomes (3 sets) — almost always non-viable.',
    params: { oocytes: 1, zonaBlock: 0, _force: { fertilize: 1, splits: [] } } },
  { id: 'trisomy', label: 'Trisomy 21 (nondisjunction)',
    hint: 'A meiotic non-disjunction leaves an extra chromosome 21 (47 total) — Down syndrome.',
    params: { oocytes: 1, nondisjunction: 1, _force: { fertilize: 1, splits: [] } } },
  { id: 'chimerism', label: 'Chimerism (zygote fusion)',
    hint: 'Two zygotes fuse into one individual carrying two cell lines — the inverse of an identical split.',
    params: { oocytes: 2, _force: { fertilize: 2, splits: [], fuse: true } } },
  { id: 'vanishing', label: 'Vanishing twin',
    hint: 'A twin is conceived but reabsorbed in the first weeks, often unnoticed — the pregnancy continues as a singleton.',
    params: { oocytes: 2, _force: { fertilize: 2, splits: [], vanish: 1 } } },
];
export const getPreset = (id) => PRESETS.find((p) => p.id === id) || null;

// ── the developmental timeline (post-fertilisation days) — Carnegie-keyed ─────
// REAL up to blastocyst (the engine simulates it); a guided clock thereafter.
export const PHASES = [
  { key: 'gametes',       day: -0.5, t: 'Gametes',          d: 'Oocyte arrested in meiosis II; ~hundreds of sperm reach the ampulla.' },
  { key: 'fertilisation', day: 0,    t: 'Fertilisation',    d: 'Sperm penetrates; the cortical reaction blocks polyspermy; pronuclei fuse → zygote (46 chromosomes).' },
  { key: 'cleavage',      day: 1,    t: 'Cleavage',         d: 'Mitosis without growth: 2 → 4 → 8 cells. The window in which an embryo can split.' },
  { key: 'morula',        day: 3,    t: 'Morula',           d: '~16 cells compact into a solid ball.' },
  { key: 'blastocyst',    day: 5,    t: 'Blastocyst',       d: 'A fluid cavity forms; inner cell mass (embryo) vs trophoblast (placenta) differentiate; hatches from the zona.' },
  { key: 'implantation',  day: 7,    t: 'Implantation',     d: 'The trophoblast invades the endometrium; the bilaminar disc forms.' },
  { key: 'gastrulation',  day: 16,   t: 'Gastrulation',     d: 'The primitive streak lays down three germ layers — the body plan. After this an embryo can no longer split cleanly.' },
  { key: 'organogenesis', day: 22,   t: 'Organogenesis',    d: 'Neural tube closes; somites form; the heart beats (~day 22); limb buds appear.' },
  { key: 'fetal',         day: 56,   t: 'Fetal',            d: 'End of week 8: all major organs present — now a fetus. Growth and maturation follow.' },
  { key: 'viability',     day: 168,  t: 'Viability',        d: '~24 weeks: lungs can, with help, support life outside the womb.' },
  { key: 'birth',         day: 266,  t: 'Birth',            d: '~38 weeks after fertilisation: parturition.' },
];
export const LIFE_STAGES = [
  { t: 'Neonate', d: '0–1 month' }, { t: 'Infant', d: '1 mo – 1 yr' },
  { t: 'Child', d: '1–10 yr' }, { t: 'Adolescent', d: '10–19 yr' },
  { t: 'Adult', d: '20–65 yr' }, { t: 'Senescence', d: '65 yr +' },
];
export const phaseForDay = (day) => {
  let cur = PHASES[0];
  for (const ph of PHASES) if (day >= ph.day) cur = ph; else break;
  return cur;
};
// Cells at a given day (geometric cleavage, capped at the blastocyst).
export const cellsForDay = (day) => {
  if (day < 0) return 0;
  if (day < 1) return 1;
  if (day >= 5) return 64;
  return Math.min(64, Math.pow(2, Math.floor(day + 0.0001)));
};
