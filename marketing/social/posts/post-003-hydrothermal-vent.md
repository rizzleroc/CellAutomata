# Post 003 — Alkaline hydrothermal vent (Lane-Martin chemiosmosis)

**Topic:** Proton gradient does the thermodynamic work; live PMF (mV) + ΔG (kJ/mol) from the Nernst equation; Wood-Ljungdahl CO₂ fixation (2 CO₂ + 4 H₂ → acetate, ΔG° = −95 kJ/mol).
**Suggested asset:** the "vent" medallion in `docs/genesis.png`
**Date drafted:** 2026-05-29

---

## X / Twitter (thread)

**1/**
Where did life get its energy *before* there was food to eat? 🔋

The leading answer: it didn't eat — it plugged into a natural battery at the bottom of the ocean. Alkaline hydrothermal vents. 🧵

**2/**
At these vents, alkaline fluid seeps into acidic early ocean across thin mineral walls — creating a proton gradient. That gradient is the *exact* trick every living cell still uses to make ATP today: chemiosmosis.

The energy came first; metabolism wired into it.

**3/**
cellauto's vent stage doesn't fake this. It reads out the **proton-motive force (mV)** and **ΔG (kJ/mol)** live from the Nernst equation, and runs real **Wood-Ljungdahl** carbon fixation:

2 CO₂ + 4 H₂ → acetate  (ΔG° = −95 kJ/mol)

**4/**
Theory: Russell & Hall (1997), Lane & Martin (2012).
Open source, MIT, Python.
⭐ github.com/rizzleroc/CellAutomata

#originoflife #abiogenesis #chemistry #bioenergetics #ArtificialLife #scicomm

---

## LinkedIn

**Life may have started not by eating, but by plugging into a battery.**

One of the most compelling origin-of-life hypotheses (Russell & Hall 1997; Lane & Martin 2012) is that the first metabolism was powered by alkaline hydrothermal vents. Where alkaline vent fluid meets the more acidic early ocean across thin mineral barriers, you get a natural proton gradient — the very same electrochemical mechanism, chemiosmosis, that every living cell uses to generate ATP today. The energy gradient came first; biology learned to tap it.

cellauto's hydrothermal-vent stage models this with real thermodynamics rather than a decorative gradient: it computes the proton-motive force (in mV) and the free-energy change ΔG (in kJ/mol) live from the Nernst equation, and runs Wood-Ljungdahl carbon fixation — 2 CO₂ + 4 H₂ → acetate, ΔG° = −95 kJ/mol — the actual chemistry by which some of the most ancient organisms still fix carbon.

🔗 https://github.com/rizzleroc/CellAutomata

#OriginOfLife #Bioenergetics #ComputationalBiology #OpenSource #Chemistry

---

## Reddit (r/abiogenesis or r/biology)

**Title:** cellauto's hydrothermal-vent stage computes proton-motive force (mV) and ΔG (kJ/mol) live from the Nernst equation, with real Wood-Ljungdahl CO₂ fixation

**Body:**

The alkaline-hydrothermal-vent hypothesis (Russell & Hall 1997; Lane & Martin 2012) argues that the first life harnessed a *geochemical* proton gradient — alkaline vent fluid meeting acidic ocean across thin mineral walls — as a free energy source, predating any enzymatic metabolism. It's chemiosmosis before cells.

What I found neat in **cellauto** is that the vent stage actually instruments this:

- **Proton-motive force** (mV) and **ΔG** (kJ/mol) are read out live via the Nernst equation (ΔG through the Faraday constant), driven by adjustable vent/ocean pH sliders.
- It models **Wood-Ljungdahl** carbon fixation explicitly: 2 CO₂ + 4 H₂ → acetate, ΔG° = −95 kJ/mol — the actual acetyl-CoA pathway chemistry used by acetogens/methanogens.

It's one stage of a coupled 12-stage origin-of-life pipeline. Python, MIT licensed.

Repo: https://github.com/rizzleroc/CellAutomata

---

## TikTok (@ai.news760) — 35s script

**Format:** moody deep-sea vent footage / the sim's pH-gradient field; dramatic captions; low ambient hum.

**Hook (0–3s):** Dark ocean floor, glowing vent. Caption: **"Life might have started by plugging into a battery."**

**Beat 2 (3–10s):** Caption: *"At deep-sea vents, alkaline fluid meets acidic ocean across thin rock walls."* Show the gradient.

**Beat 3 (10–18s):** Caption: *"That makes a proton gradient — the SAME thing your cells use to make energy right now."*

**Beat 4 (18–27s):** Cut to cellauto's vent readout (PMF mV / ΔG kJ/mol ticking). Caption: *"This sim computes the real voltage AND the chemistry: 2 CO₂ + 4 H₂ → acetate."*

**Beat 5 (27–35s):** Caption: *"Energy came first. Metabolism wired in later."* End card: *"Free & open source — link in bio."*

**Caption text:** Life may have started as a battery at the bottom of the sea 🔋🌊 Alkaline hydrothermal vents + chemiosmosis — and a sim that computes the actual proton-motive force. #LearnOnTikTok #sciencetok #originoflife #bioenergetics #abiogenesis #STEM #ocean #simulation
