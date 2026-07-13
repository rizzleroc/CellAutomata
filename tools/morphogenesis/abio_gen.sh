#!/usr/bin/env bash
# ABIOGENESIS — regenerate the twelve SEM stage sources for abiogenesis_film.py.
# Each line is one origin-of-life stage at the configuration a 13-agent swarm found to give the most
# award-grade depth-shaded micrograph (warm-sepia 'w' / cool-mono 'c'). GEN_SC supersamples for a
# crisp micrograph; GEN_RELIEF is set so relief*SC preserves the emboss each agent tuned; GEN_NOISE
# overrides the SEM substrate grain where a flat field would otherwise show screen-door dither.
# Run from the repo root:  bash tools/morphogenesis/abio_gen.sh  &&  python3 tools/morphogenesis/abiogenesis_film.py
# Note: luca and minerals seed with unseeded Math.random — luca's eruption timing / minerals' clay
# layout vary run-to-run; re-run those 1-2× if the take is weak. (A 13th stage, vesicles, was explored
# but dropped: its Allen-Cahn field carries an irreducible diagonal checkerboard weave under the SEM.)
set -e
G="node tools/morphogenesis/gen.mjs"

# I · CHEMISTRY
GEN_OUT=/tmp/g_ab_soup      GEN_SC=3 GEN_RELIEF=12 GEN_PARAMS='{"count":900,"spark":4.0,"reducing":1.0,"boil":0.5}'                         $G soup       20 140 1 w
GEN_OUT=/tmp/g_ab_grayscott GEN_SC=3 GEN_RELIEF=12                                                                                          $G grayscott 150 240 8 c 0.026 0.051

# II · ENERGY & SURFACES
GEN_OUT=/tmp/g_ab_vents     GEN_SC=4 GEN_RELIEF=12 GEN_PARAMS='{"diffusion":0.08,"drift":0.10,"decay":0.002,"pmf":0.90,"feedstock":0.13}'    $G vents       0 110 1 c
GEN_OUT=/tmp/g_ab_minerals  GEN_SC=4 GEN_RELIEF=12 GEN_PARAMS='{"clayPatches":11,"kClay":0.11,"feed":0.04,"hydrolysis":0.005,"substeps":1}'  $G minerals    0 120 1 w

# III · SELF-MAKING
GEN_OUT=/tmp/g_ab_raf       GEN_SC=3 GEN_RELIEF=12 GEN_PARAMS='{"catalysis":3.5,"foodLevel":1,"decay":0.04,"substeps":1}'                    $G raf         0 110 1 w
GEN_OUT=/tmp/g_ab_coacervate GEN_SC=4 GEN_RELIEF=20 GEN_PARAMS='{"kappa":0.10}'                                                             $G coacervate 60 212 2 c

# IV · INFORMATION
GEN_OUT=/tmp/g_ab_chirality GEN_SC=4 GEN_RELIEF=14 GEN_PARAMS='{"alpha":0.12,"beta":0.40,"diffusion":0.30,"noise":0.001}'                    $G chirality 175 238 6 c
GEN_OUT=/tmp/g_ab_rna       GEN_SC=4 GEN_RELIEF=12 GEN_PARAMS='{"mutation":0.0008,"sigma":8,"length":14,"substeps":1}'                       $G rna         8  58 1 c
GEN_OUT=/tmp/g_ab_code      GEN_SC=4 GEN_RELIEF=15 GEN_PARAMS='{"selection":7,"transfer":0.15,"mutationRate":0.05,"classes":4,"sweeps":2}'   $G code        0  56 1 c

# V · LIFE
GEN_OUT=/tmp/g_ab_natsel    GEN_SC=4 GEN_RELIEF=26 GEN_PARAMS='{"amoebaLifespan":200}'                                                      $G natural_selection 2 48 1 c
GEN_OUT=/tmp/g_ab_luca      GEN_SC=4 GEN_RELIEF=14 GEN_PARAMS='{"divergence":0.005,"selection":0.35,"transfer":0.45,"coreThreshold":0.80,"substeps":1}' $G luca 72 66 1 w
GEN_OUT=/tmp/g_ab_life      GEN_SC=4 GEN_RELIEF=16 GEN_PARAMS='{"population":480,"mutationRate":0.012,"substrateRegen":0.20,"initialEnergy":120,"maxPopulation":2000}' $G life 6 48 1 w

echo "=== abiogenesis: 12 stage sources generated -> /tmp/g_ab_*_{w,c}.bin ==="
