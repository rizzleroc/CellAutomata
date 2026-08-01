// web8 — narration. What each origin-of-life stage IS, why it matters, and a
// citation. Condensed from the desktop tutorial.py / narrative.py / docs/science.md
// so the web guide stays scientifically honest. Pure data + helpers; no DOM.

export const STAGE_NARRATION = {
  'stage0-miller-urey': {
    what: 'Stage 0 — the primordial soup. Lightning in a reducing atmosphere cooks simple molecules; same-species monomers drift together and condense into the first protocells.',
    why: 'Miller & Urey showed in 1953 that sparks alone make amino acids — the soup the whole story starts from.',
    cite: 'Miller 1953 · Oparin 1924 · Haldane 1929',
  },
  'stage1-grayscott': {
    what: 'Stage 1 — reaction–diffusion. Two chemicals feed and inhibit each other across the dish, and self-replicating spots appear that split like dividing cells.',
    why: 'Turing (1952) saw that chemistry + diffusion alone makes pattern; the Gray–Scott spots resemble protocell division.',
    cite: 'Turing 1952 · Gray–Scott 1985 · Pearson 1993',
  },
  'stage2-raf': {
    what: "Stage 2 — autocatalytic sets. In a random reaction network, a closed loop emerges where every molecule's maker is made by another in the set — it sustains itself.",
    why: "Kauffman's 1986 intuition, made rigorous as the RAF by Hordijk & Steel (2004): self-sustaining chemistry crosses a connectivity threshold.",
    cite: 'Kauffman 1986 · Hordijk–Steel 2004',
  },
  'stage3-vesicles': {
    what: 'Stage 3 — lipid vesicles. Above a critical concentration, fatty molecules snap into a bilayer membrane — the first compartment that holds chemistry inside.',
    why: 'A boundary is what turns a patch of chemistry into an individual that selection can act on.',
    cite: 'Deamer 2008 · Hanczyc–Szostak 2003',
  },
  'stage4-vent': {
    what: 'Stage 4 — the alkaline hydrothermal vent. A natural proton gradient across thin mineral walls drives chemistry, exactly as cells still power themselves today.',
    why: 'Lane & Martin argue life began by tapping a vent’s proton-motive force, not by waiting for the soup to find ATP.',
    cite: 'Lane–Martin 2012 · Russell',
  },
  'stage5-minerals': {
    what: 'Stage 5 — mineral catalysis. Montmorillonite clay surfaces line up monomers and template them into longer polymers — a workbench for prebiotic chemistry.',
    why: 'Ferris showed clay can polymerise RNA: mineral surfaces beat the dilution problem of open water.',
    cite: 'Ferris 1996',
  },
  'stage6-chirality': {
    what: 'Stage 6 — homochirality. A tiny imbalance between left- and right-handed molecules amplifies, via autocatalysis, until one handedness wins outright.',
    why: 'Life uses only left-handed amino acids and right-handed sugars; the Soai reaction shows how symmetry breaks (Frank 1953).',
    cite: 'Frank 1953 · Soai 1995',
  },
  'stage7-rna': {
    what: 'Stage 7 — the RNA world. One molecule is both gene and enzyme; strands copy themselves with errors, and the fittest "master" sequence spreads — until mutation overwhelms it.',
    why: "Eigen's error threshold sets how big a genome can get before it dissolves into noise — the limit early replicators had to beat.",
    cite: 'Gilbert 1986 · Eigen 1971',
  },
  'stage8-code': {
    what: 'Stage 8 — the genetic code. A mapping from triplets of RNA letters to amino acids freezes in, so sequence can finally specify protein.',
    why: "The code is nearly universal and error-minimising — evidence it was selected, not frozen by accident.",
    cite: 'Crick 1968 · Koonin–Novozhilov 2009',
  },
  'stage9-coacervate': {
    what: 'Stage 9 — coacervates. Oparin’s liquid droplets concentrate molecules without a membrane — a second, parallel route to compartments.',
    why: 'These membrane-free droplets show compartmentalisation is easy: chemistry crowds together on its own.',
    cite: 'Oparin 1924 · Bartolucci',
  },
  'stage10-selection': {
    what: 'Stage 10 — protocell selection. Compartments with diverse internal chemistry grow and divide, passing on their mix with mutation — heredity with variation.',
    why: "Fitness here is the integrity of the Eigen–Schuster hypercycle: a catalytic loop is only as strong as its weakest member, and Darwinian dynamics appear.",
    cite: 'Eigen–Schuster 1977 · Szostak 2017',
  },
  'stage11-luca': {
    what: 'Stage 11 — LUCA, the last universal common ancestor. Every gene tree converges on one ancestral population from which all life today descends.',
    why: 'LUCA already had DNA, a code, and a vent-style chemiosmotic membrane — the toolkit of the modern cell.',
    cite: 'Weiss et al. 2016',
  },
  'capstone-stromatolite': {
    what: 'Capstone — a stromatolite, ~3.5 billion years old: layered rock built by microbial mats. The first hard evidence that life had taken hold.',
    why: 'From soup to fossil reef — this is where the origin-of-life story hands off to evolution proper.',
    cite: 'Allwood 2006',
  },
};

export function explainStage(id) {
  const n = STAGE_NARRATION[id];
  if (!n) return "This plate doesn't have a guided note yet — but watch the micrograph beside it: that's the real simulation running.";
  return `${n.what} ${n.why}`;
}

export function citeStage(id) {
  return STAGE_NARRATION[id]?.cite || '';
}
