# Murmuration — a flocking simulator

A full starling-murmuration simulator, built after Rama Hoetzlein's **Flock2:
A model for orientation-based social flocking** (*Journal of Theoretical
Biology*, 2024 — [arXiv:2404.17804](https://arxiv.org/abs/2404.17804),
[code](https://github.com/ramakarl/Flock2)). It runs thousands of birds at dusk
over a roost, with a stooping peregrine, live flock telemetry, six regimes, and
every parameter exposed — in the same Catalytic-Silence design language as the
rest of the `cellauto` lab.

Live: <https://rizzleroc.github.io/CellAutomata/murmuration/>

## What makes it *Flock2*, not just boids

Two ideas separate this from a classic Reynolds boid, and both are implemented
faithfully in `flock.js`:

1. **Orientation-based social flocking.** A bird does not sum avoidance,
   alignment and cohesion into an acceleration vector. It reads its neighbours
   through a limited **visual field** (a topological cap of ~7 birds, as measured
   in real starlings) and forms a single *desired heading* — a wish to **turn**.
   Social pressure controls orientation, never acceleration directly.

2. **Flightsim — a single-body fixed-wing flight model.** The wish to turn is
   realised the way a bird actually turns: it **banks**. Rolling tilts the lift
   vector sideways; the horizontal component curves the path while the vertical
   component shrinks, so a banked bird **loses altitude in the turn**. Lift,
   gravity, thrust and drag are integrated every step, so birds **speed up in
   dives, slow in climbs, and stall** past the critical angle of attack. These
   behaviours *emerge* — none of them is scripted.

The result is a wheeling, breathing flock that shows spontaneous **orientation
waves** (turning waves that ripple through the mass with no predator present) —
the paper's headline result.

## Using it

- **Regimes** (top-left chips) push the same model into qualitatively different
  flocks: *Starling dusk*, *Defensive ball*, *Loose sheet*, *Orientation waves*,
  *Predator panic*, *Migration line*.
- **Controls** (≡) expose the full knob set — the social rules, the visual field,
  the flight envelope (cruise/stall/max speed, bank limit, agility, turn lift
  compensation, wing power), the roost, wind, and the peregrine.
- **Peregrine.** Toggle the hunter and it stoops through the roost — watch the
  flash-expansion and the void it carves.
- **Camera.** Cycle **orbit** (tracks the flock), **follow** (chases a lead bird),
  and **free**. Drag to orbit, scroll to zoom.
- **Telemetry.** The top-right readout shows the live **order parameter**
  (polarization) with a sparkline, plus cruise speed, nearest-neighbour distance,
  mean bank and how many birds are momentarily stalling.
- **Share.** ⧉ copies a URL whose hash restores the exact regime, camera and any
  hand-tuned parameters.

Keyboard: `space` pause · `r` reset · `c` cycle camera · `p` toggle peregrine.

## Architecture

Zero-dependency ES modules; no build step. Three.js loads via a CDN importmap.

| File | Role |
|---|---|
| `flock.js` | The simulation engine — orientation-based social flocking + the Flightsim aerodynamic model. **Framework-free** (plain `Float32Array`s, spatial-hash neighbour search, seeded RNG) so it runs unchanged headless and in the browser. |
| `presets.js` | The six regimes (parameter overrides). |
| `bird.js` | The birds as one **InstancedMesh** with a GPU vertex-shader wingbeat; the peregrine; the heading+bank → matrix helper. |
| `scene.js` | The dusk-sky scope: gradient dome, low sun, ground, fog, IBL, ACES tone-mapping, bloom, and a dusk-grade + grain optics pass. |
| `main.js` | The controller — builds the panel from the schema, runs the step→render loop, drives the camera modes and telemetry, and keeps the shareable URL. |

The engine scales to a few thousand birds at interactive rates because neighbour
queries go through a uniform spatial hash (O(n)/step) and the render is a single
instanced draw call.

## Tests

Three gates, mirroring the rest of the lab (run from the repo root):

```bash
node docs/murmuration/tests/smoke.mjs   # structural: importmap, modules parse, schema + HUD wiring
node docs/murmuration/tests/flock.mjs   # the SCIENCE: order emerges, bounded/finite, banking, the peregrine scatters
node docs/murmuration/tests/life.mjs    # render: InstancedMesh + wingbeat rig, orient() rigidity, birds move
                                        #   (needs three: npm i three@0.162.0 --no-save)
```

`flock.mjs` is a real science gate, not a blank-output smoke test: it asserts the
*local order parameter* climbs out of disorder, the flock stays finite and inside
its roost, the flight envelope holds, birds bank to turn, and the peregrine both
collapses local alignment and carves a bird-free void — the honest signatures of
a murmuration.
