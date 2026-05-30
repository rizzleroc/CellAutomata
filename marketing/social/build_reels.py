#!/usr/bin/env python3
"""Build 30 vertical cellauto reels. Each reel = hook card -> real footage
scene -> branded end card (~10s). Footage comes from exports/*.gif (run
marketing/social/render_footage.sh first) and the docs/ museum plates.

Usage:
  python3 marketing/social/build_reels.py                 # build all 30
  python3 marketing/social/build_reels.py --only 0,3,7     # build a subset
  python3 marketing/social/build_reels.py --only 0 --force # rebuild
Designed so several processes/subagents can each build a disjoint --only
slice in parallel (distinct output files, per-reel temp dirs).
"""
from __future__ import annotations
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reel_lib as R  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
G = lambda n: os.path.join(ROOT, "exports", n + ".gif")
D = lambda n: os.path.join(ROOT, "docs", n)
GN = lambda n: os.path.join(ROOT, "docs", "generated", n)
OUT = os.path.join(ROOT, "marketing", "social", "reels")

# slug, hook, hooksub, hook_plate, foot, is_video, ss, title, sub, end_small
REELS = [
    ("hero-division", "Chemistry that divides", "no biology required", D("hero.png"),
     G("grayscott_mitosis"), True, 1.0, "Self-replicating spots", "Gray–Scott · Pearson 1993", "open source · star us ★"),
    ("reaction-diffusion", "Two chemicals.", "Four numbers.", GN("stage1_reaction_diffusion.png"),
     G("grayscott_spots"), True, 0.5, "Reaction–diffusion", "Turing predicted it in 1952", "the math of patterns"),
    ("five-regimes", "Change two numbers,", "change the world", D("pipeline.png"),
     G("grayscott_labyrinth"), True, 0.5, "One equation, five regimes", "spots · stripes · waves · mazes", "drag the F/k sliders"),
    ("primordial-soup", "Before life:", "soup + a spark", GN("stage0_soup.png"),
     G("soup"), True, 0.5, "Primordial soup", "weighted by Miller–Urey 1953", "it starts with chemistry"),
    ("hydrothermal-vent", "Life plugged into", "a battery", D("genesis.png"),
     G("vent"), True, 0.6, "Hydrothermal vent", "live PMF & ΔG · Lane–Martin", "energy came first"),
    ("autocatalytic-sets", "Molecules that make", "each other", GN("stage2_autocatalytic.png"),
     G("raf"), True, 0.5, "Autocatalytic sets", "Kauffman · Hordijk–Steel RAF", "chemistry that bootstraps"),
    ("homochirality", "Why is life", "left-handed?", D("genesis.png"),
     G("homochirality"), True, 0.6, "Homochirality", "Frank 1953 symmetry breaking", "one hand wins"),
    ("rna-world", "The RNA world,", "on a knife-edge", D("genesis.png"),
     G("rna_world"), True, 0.6, "Eigen quasispecies", "error catastrophe, live", "replicate or melt"),
    ("genetic-code", "How the code", "wrote itself", GN("stage7_genetic_code_plate.png"),
     G("genetic"), True, 0.5, "Genetic-code coevolution", "Vetsigian–Woese–Goldenfeld", "the code converges"),
    ("coacervates", "Droplets before", "membranes", D("prima-materia.png"),
     G("coacervate"), True, 0.5, "Coacervates", "Cahn–Hilliard · Oparin", "life's first blobs"),
    ("mineral-catalysis", "Life on the rocks —", "literally", D("genesis.png"),
     G("minerals"), True, 0.5, "Mineral catalysis", "Na-montmorillonite · Ferris", "clay as a workbench"),
    ("vesicles", "The first", "cell walls", GN("stage3_vesicles.png"),
     G("vesicles"), True, 0.5, "Vesicle self-assembly", "Helfrich · measured CMC", "membranes from soap"),
    ("protocell-selection", "Survival of the", "fittest protocell", GN("stage4_selection.png"),
     G("selection"), True, 0.5, "Protocell selection", "Eigen–Schuster hypercycle", "Darwin, pre-DNA"),
    ("luca", "Meet your 4-billion-", "year-old ancestor", GN("stage11_luca_plate.png"),
     G("luca"), True, 0.5, "LUCA distillation", "Weiss et al. 2016 parsimony", "the last common root"),
    ("pipeline-tour", "Soup → LUCA", "in 12 steps", D("genesis.png"),
     D("pipeline.png"), False, 0, "12 coupled stages", "one continuous narrative", "the whole arc"),
    ("conway", "The classic:", "Conway's Life", GN("pipeline_poster.png"),
     G("conway"), True, 0.5, "Game of Life", "B3/S23 · shipped for reference", "where it all began"),
    ("wolfram-110", "4 cells of memory,", "Turing-complete", GN("cellauto_twelve_tableaux.png"),
     G("wolfram110"), True, 0.5, "Wolfram rule 110", "elementary, yet universal", "simple → universal"),
    ("science-spine", "Every constant is", "a published number", D("genesis.png"),
     GN("release_poster_v3_4.png"), False, 0, "Real science, cited", "see docs/science.md", "no hand-waving"),
    ("reproducible", "Same seed,", "same universe", D("hero.png"),
     G("grayscott_spots"), True, 1.2, "Deterministic", "bit-for-bit across save/load", "science you can repeat"),
    ("web-demo", "Run it in your", "browser", D("pipeline.png"),
     GN("stage1_reaction_diffusion.png"), False, 0, "Live Stage 1 demo", "no install · vanilla JS", "try it right now"),
    ("honest-gaps", "A project that", "audits itself", D("prima-materia.png"),
     D("prima-materia.png"), False, 0, "Honest-gap-closure", "v3.5 closed its own gaps", "rare honesty"),
    ("twelve-tableaux", "Twelve windows", "into genesis", D("genesis.png"),
     GN("cellauto_twelve_tableaux.png"), False, 0, "Twelve Tableaux", "every panel = real output", "a museum of life"),
    ("genesis-poster", "The magnum-opus", "poster", D("genesis.png"),
     D("genesis.png"), False, 0, "Genesis", "12 stages, one composition", "frame-worthy science"),
    ("prima-materia", "Catalytic Silence", "design", D("prima-materia.png"),
     D("prima-materia.png"), False, 0, "Prima Materia", "museum-style science plate", "where art meets ALife"),
    ("hero-closeup", "The money shot", "", D("hero.png"),
     D("hero.png"), False, 0, "Protocell fission", "Gray–Scott @ step 600", "one frame, one mystery"),
    ("open-source", "Free. Open.", "MIT.", D("genesis.png"),
     GN("pipeline_poster.png"), False, 0, "Open source", "Python · 141 tests · CI green", "fork it today"),
    ("accessibility", "Science for", "everyone", GN("stage3_vesicles.png"),
     G("vesicles"), True, 0.5, "Accessible by design", "CVD-safe · reduced-motion · keys", "built for all"),
    ("chemistry-to-life", "Chemistry → life", "in twelve steps", D("genesis.png"),
     G("raf"), True, 0.5, "The whole arc", "soup to last common ancestor", "abiogenesis, runnable"),
    ("error-catastrophe", "Too many mutations", "= meltdown", D("genesis.png"),
     G("rna_world"), True, 0.6, "Error catastrophe", "ε_c = ln(σ)/L, on screen", "the edge of life"),
    ("final-cta", "Watch life", "build itself", D("genesis.png"),
     G("grayscott_mitosis"), True, 0.8, "cellauto", "12 stages · soup → LUCA", "★ star it on GitHub"),
]

END_PLATE = D("genesis.png")


def reel_scenes(spec):
    (slug, hook, hooksub, plate, foot, is_video, ss,
     title, sub, end_small) = spec
    hook_card = dict(kind="card", dur=2.4, plate=plate, big=hook,
                     smalls=[hooksub] if hooksub else None, big_size=92)
    if is_video:
        foot_scene = dict(kind="video", dur=6.2, src=foot, ss=ss, title=title, sub=sub)
    else:
        foot_scene = dict(kind="image", dur=5.6, src=foot, title=title, sub=sub)
    end_card = dict(kind="card", dur=2.6, plate=END_PLATE, big="cellauto",
                    mono="github.com/rizzleroc/CellAutomata",
                    smalls=[end_small], logo=D("icon.png"), big_size=104)
    return [hook_card, foot_scene, end_card]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="comma list of reel indices")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    idxs = (sorted(int(x) for x in args.only.split(",") if x.strip() != "")
            if args.only else list(range(len(REELS))))
    os.makedirs(OUT, exist_ok=True)
    for i in idxs:
        spec = REELS[i]
        slug = spec[0]
        out = os.path.join(OUT, f"reel_{i:02d}_{slug}.mp4")
        if os.path.exists(out) and not args.force:
            print(f"[skip] {i:02d} {slug} (exists)")
            continue
        try:
            _, total = R.build_reel(reel_scenes(spec), out)
            mb = os.path.getsize(out) / 1e6
            print(f"[ok]   {i:02d} {slug}  {total:.1f}s  {mb:.1f}MB")
        except Exception as e:  # noqa: BLE001
            print(f"[FAIL] {i:02d} {slug}: {e}")
            sys.exit(2)


if __name__ == "__main__":
    main()
