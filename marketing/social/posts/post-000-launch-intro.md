# Post 000 — Launch / Intro

**Topic:** What cellauto is — "A four-parameter PDE is enough to make a cell divide."
**Suggested asset:** `docs/hero.png` (Gray-Scott self-replicating spots)
**Date drafted:** 2026-05-29

---

## X / Twitter (thread)

**1/**
🧬 What if the origin of life isn't a miracle — but a math problem you can run on your laptop?

Meet **cellauto**: an open-source sandbox that walks the chemistry-to-life transition across 12 scientific stages, from primordial soup to LUCA. 🧵

**2/**
The hero result: a Gray-Scott reaction-diffusion PDE with just **4 parameters** spontaneously produces self-replicating, *dividing* spots — protocell-like fission from pure chemistry.

Turing (1952) → Gray-Scott (1985) → Pearson (1993). No magic. ⬇️

**3/**
Every stage is real science, not vibes:
• Miller-Urey 1953 yields
• Kauffman autocatalytic sets
• Eigen-Schuster hypercycles
• Lane-Martin hydrothermal vents
Every constant traces to a published measurement.

**4/**
Open source, MIT, Python + a live in-browser demo.
⭐ github.com/rizzleroc/CellAutomata

#ArtificialLife #ALife #abiogenesis #originoflife #cellularautomata #Python #scicomm

---

## LinkedIn

**The origin of life, reframed as emergent behaviour you can run on your laptop.**

I've been exploring **cellauto** — an open-source cellular sandbox that models the chemistry-to-life transition (abiogenesis) across a 12-stage scientific pipeline: primordial soup → hydrothermal vents → autocatalytic sets → RNA world → protocells → LUCA.

The headline result is quietly profound: a Gray-Scott reaction-diffusion equation with just **four parameters** produces self-replicating, dividing "protocell" spots. A handful of numbers is enough to manufacture emergent cellular division — the central mystery of how chemistry became biology.

What makes the project stand out is its scientific discipline. Every constant traces to a published measurement (Miller-Urey 1953 yields, measured fatty-acid CMCs, the Eigen error threshold), and each stage cites the canonical literature.

Built in Python with a desktop app and a static-HTML web demo. MIT licensed.

🔗 https://github.com/rizzleroc/CellAutomata

#ArtificialLife #ComputationalBiology #OpenSource #Python #OriginOfLife

---

## Reddit (r/cellular_automata or r/abiogenesis)

**Title:** cellauto — an open-source sandbox that walks abiogenesis across 12 scientific stages (soup → LUCA), where a 4-parameter PDE produces dividing protocells

**Body:**

I wanted to share a project that treats the origin-of-life problem as a series of runnable simulations rather than a single toy. **cellauto** implements a 12-stage pipeline in scientific order — primordial soup, alkaline hydrothermal vent, Gray-Scott reaction-diffusion, mineral catalysis, Kauffman RAFs, homochirality, RNA world, genetic-code coevolution, coacervates, vesicles, protocell selection, and LUCA distillation.

A few things I appreciated digging through it:

- **Stage 1 (Gray-Scott)** produces self-replicating, dividing spots from a 4-parameter PDE — the Pearson (1993) "spots" regime (F=0.035, k=0.065).
- **Stage 2** uses the *correct* Hordijk-Steel layered closure for RAF detection (catalysis mandatory), not a hand-wavy autocatalysis check.
- The pipeline is genuinely **coupled** — each stage's output field seeds the next stage's initial condition, so it's one continuous narrative.
- Constants are sourced from real measurements (Miller-Urey yields, fatty-acid CMCs, Eigen error threshold), with citations in `docs/science.md`.

Python, Tk GUI + headless CLI + a static-HTML in-browser Stage 1 demo. MIT. 141 tests passing.

Repo: https://github.com/rizzleroc/CellAutomata
