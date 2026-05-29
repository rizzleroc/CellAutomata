# Post 001 — Hero result: Gray-Scott self-replicating spots

**Topic:** Stage 1 Gray-Scott reaction-diffusion — self-replicating, dividing "protocell" spots.
**Suggested asset:** `docs/hero.png` + a `preset=mitosis` GIF (`cellauto export --rule abiogenesis-stage1-grayscott --rule-config preset=mitosis --grid 100 --steps 60 --out exports/mitosis.gif`)
**Date drafted:** 2026-05-29

---

## X / Twitter (thread)

**1/**
This is cell division — with zero biology. 🔬

Just two virtual chemicals obeying a 4-parameter PDE. The spots grow, stretch, and *split*. That's the Gray-Scott reaction-diffusion equation, the hero result of cellauto. 🧵

[attach: docs/hero.png]

**2/**
The recipe: chemical U is fed in, chemical V decays, and the two diffuse at different speeds. That imbalance is all it takes for self-replicating spots to emerge.

Turing predicted patterns like this in 1952. Gray & Scott formalised it in 1985.

**3/**
This exact frame is Pearson's (1993) "spots" regime: F=0.035, k=0.065. Nudge those two numbers and the world flips — stripes, mitosis, waves, labyrinths.

In cellauto you drag the F/k sliders live and watch the regime change.

**4/**
Free & open source (MIT), Python, with a live in-browser demo.
⭐ github.com/rizzleroc/CellAutomata

#ReactionDiffusion #ArtificialLife #ALife #cellularautomata #abiogenesis #Python #scicomm

---

## LinkedIn

**A four-parameter equation that performs cell division.**

The image attached isn't a microscope slide — it's the output of the Gray-Scott reaction-diffusion equation, the hero result of the open-source project **cellauto**. Two notional chemicals, one fed in and one decaying, diffusing at different rates. That asymmetry alone produces spots that grow and split, mimicking protocell division.

The lineage is deep: Alan Turing proposed reaction-diffusion as the basis of biological pattern formation in 1952; Gray and Scott formalised this system in 1985; Pearson catalogued its regimes in 1993. The frame here is Pearson's "spots" regime (F=0.035, k=0.065) — change those two parameters and you get stripes, waves, or labyrinths instead.

What I like about cellauto is that you can manipulate F and k with live sliders and watch the regime transition in real time — turning a classic result into something tactile.

Open source, MIT, Python, with a browser demo.
🔗 https://github.com/rizzleroc/CellAutomata

#ArtificialLife #ComputationalBiology #ReactionDiffusion #OpenSource #Python

---

## Reddit (r/cellular_automata or r/oddlysatisfying)

**Title:** A 4-parameter reaction-diffusion PDE doing protocell-like division (Gray-Scott "spots", F=0.035 k=0.065) — open-source sandbox with live F/k sliders

**Body:**

The Gray-Scott reaction-diffusion system never stops being remarkable: two reacting/diffusing species, four parameters (feed F, kill k, and the two diffusion rates Du/Dv), and you get self-replicating spots that grow and split like dividing cells.

This is from **cellauto**, where Stage 1 of an origin-of-life pipeline is exactly this PDE. The pinned frame is Pearson's (1993) "spots" regime (F=0.035, k=0.065). The fun part is the live F/k sliders + preset chips (spots / stripes / mitosis / waves / labyrinth) — you can walk the parameter space and watch the morphology flip.

Under the hood it's numpy with a PhotoImage blit renderer (~7× faster than the naive canvas approach for the continuous-field stages), and a headless CLI can export GIFs:

    cellauto export --rule abiogenesis-stage1-grayscott --rule-config preset=mitosis \
        --grid 100 --steps 60 --out exports/mitosis.gif

MIT licensed, Python, with a static-HTML browser version of this stage too.

Repo: https://github.com/rizzleroc/CellAutomata

---

## TikTok (@ai.news760) — 30s script

**Format:** screen-capture of the Gray-Scott sim dividing, looped; bold on-screen captions; satisfying ambient sound.

**Hook (0–3s):** Full-screen dividing spots. Caption punches in: **"This equation makes cells divide."**

**Beat 2 (3–8s):** Caption: *"No biology. Just 2 chemicals + 4 numbers."* Spots keep splitting.

**Beat 3 (8–16s):** Caption: *"One chemical feeds. One decays. They spread at different speeds."* Show the F/k sliders being dragged.

**Beat 4 (16–24s):** Caption: *"Change 2 numbers → spots become stripes, waves, mazes."* Quick montage flipping presets (spots → mitosis → labyrinth).

**Beat 5 (24–30s):** Caption: *"Alan Turing predicted this in 1952."* End card: *"Run it yourself — free & open source. Link in bio."*

**Caption text:** A 4-parameter equation that divides like a living cell 🧬 This is the Gray-Scott reaction-diffusion model — the same math Turing theorized in 1952. Free & open source 👀
#LearnOnTikTok #sciencetok #ArtificialLife #originoflife #simulation #oddlysatisfying #STEM #abiogenesis

**Asset to film:** export the `preset=mitosis` GIF (command above) or screen-record the desktop GUI dragging the F/k sliders.
