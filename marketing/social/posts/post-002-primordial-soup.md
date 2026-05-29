# Post 002 — Stage 0: Primordial soup (Miller-Urey 1953)

**Topic:** Stage 0 — molecules mixing/condensing; the initial mix is weighted by Miller's 1953 *measured* yields.
**Suggested asset:** `docs/pipeline.png` (leftmost "primordial soup" panel) or the soup medallion in `docs/genesis.png`
**Date drafted:** 2026-05-29

---

## X / Twitter (thread)

**1/**
Before life, there was soup. 🍲⚡

In 1953 Stanley Miller sealed methane, ammonia, hydrogen & water in a flask and ran sparks through it for a week. Out came amino acids. The origin-of-life story begins here — and so does cellauto. 🧵

**2/**
Most "primordial soup" demos just scatter random molecules. Stage 0 of cellauto doesn't: it weights the starting mix by Miller's *actual measured yields* — glycine most abundant, then alanine, and so on down the list.

The soup is built from real data, not vibes.

**3/**
Oparin (1924) and Haldane (1929) imagined the soup. Miller & Urey (1953) measured it. Stage 0 is the opening chapter of a 12-stage pipeline that runs all the way to LUCA — each stage feeding the next.

**4/**
Free & open source, MIT, Python.
⭐ github.com/rizzleroc/CellAutomata

#originoflife #abiogenesis #chemistry #ArtificialLife #cellularautomata #scicomm

---

## LinkedIn

**The origin of life starts with a flask, a spark, and a 1953 measurement.**

Stage 0 of the open-source project **cellauto** is the "primordial soup" — molecules mixing and condensing. What makes it more than a decorative starting point: the initial molecular mix is weighted by the *measured yields* from the Miller-Urey experiment (1953), in which sparking a flask of methane, ammonia, hydrogen and water produced amino acids, with glycine the most abundant.

It's a small but meaningful design choice. Rather than seeding the simulation with arbitrary molecules, cellauto grounds even its first frame in published experimental data — honouring the lineage from Oparin (1924) and Haldane (1929), who proposed the soup, to Miller and Urey, who demonstrated it.

Stage 0 then hands its state forward into an 11-stage continuation that walks the full chemistry-to-life transition, ending at LUCA.

🔗 https://github.com/rizzleroc/CellAutomata

#OriginOfLife #ComputationalBiology #OpenSource #Chemistry #Python

---

## Reddit (r/abiogenesis or r/chemistry)

**Title:** cellauto Stage 0 seeds its "primordial soup" using Miller-Urey's measured 1953 yields instead of arbitrary molecules

**Body:**

Most origin-of-life sandboxes start with a uniformly random soup. The open-source project **cellauto** does something a little more principled at Stage 0: the initial distribution of molecule types is weighted by the *measured yields* from the Miller-Urey experiment (1953) — the classic spark-discharge of CH₄ / NH₃ / H₂ / H₂O that produced amino acids, glycine most abundantly.

It's the first stage of a 12-stage pipeline (soup → hydrothermal vent → reaction-diffusion → mineral catalysis → autocatalytic sets → homochirality → RNA world → genetic code → coacervates → vesicles → selection → LUCA), and the stages are genuinely coupled — Stage 0's output seeds Stage 1's initial condition.

Citations in the repo trace back to Oparin (1924), Haldane (1929), and Miller-Urey (1953). Runs headless too:

    cellauto simulate --rule abiogenesis-stage0-soup --grid 80 --steps 200 --seed 7

MIT licensed, Python. Repo: https://github.com/rizzleroc/CellAutomata

---

## TikTok (@ai.news760) — 30s script

**Format:** flask + spark animation / the soup sim grid; punchy captions; a "did you know" tone.

**Hook (0–3s):** Caption over a flask zap: **"In 1953, a grad student made the ingredients of life with lightning."**

**Beat 2 (3–9s):** Caption: *"Stanley Miller sealed gas + water in glass and sparked it for a week."* Show bubbling flask.

**Beat 3 (9–17s):** Caption: *"Out came amino acids — glycine, alanine… the building blocks."* Show molecules forming.

**Beat 4 (17–25s):** Cut to the cellauto soup grid. Caption: *"This sim starts its 'primordial soup' using Miller's REAL measured amounts."*

**Beat 5 (25–30s):** Caption: *"It's step 0 of building life from scratch — 12 stages to the last common ancestor."* End card: *"Free & open source — link in bio."*

**Caption text:** The most famous experiment in origin-of-life science 🍲⚡ Miller-Urey, 1953 — and a sim that uses its real measured yields as the starting point. #LearnOnTikTok #sciencetok #originoflife #chemistry #abiogenesis #STEM #simulation #oddlysatisfying
