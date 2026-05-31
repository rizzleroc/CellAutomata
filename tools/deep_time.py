"""Deep-time evolution: accelerate a regime across log-spaced horizons and
record what it BECOMES. 1 generation = 1 'day'. At each captured horizon we
also measure instantaneous activity (step once, diff) to answer the real
question: is the pattern still moving at 10 days? 1,000? 100,000? — i.e. does
it freeze, coarsen, or churn forever.

  python3 tools/deep_time.py --idx 0 --max-gen 300000 --out discovery/deeptime/r0.npz
"""
from __future__ import annotations
import argparse, os, numpy as np
from cellauto.engine import Engine
from cellauto.rules import REGISTRY

RULE = "abiogenesis-stage1-grayscott"
REGIMES = [
    ("Soliton Lattice", 0.0700, 0.0610),
    ("Plasma Chaos",    0.0264, 0.0579),
    ("Coral",           0.0545, 0.0620),
    ("Wave Storm",      0.0198, 0.0495),
]


def entropy(v):
    h, _ = np.histogram(v, bins=24, range=(0, 1))
    p = h / (h.sum() + 1e-12); p = p[p > 0]
    return float(-(p * np.log2(p)).sum() / np.log2(24))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--idx", type=int, required=True)
    ap.add_argument("--max-gen", type=int, default=300000)
    ap.add_argument("--frames", type=int, default=170)
    ap.add_argument("--grid", type=int, default=60)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    name, F, k = REGIMES[a.idx]
    rule = REGISTRY[RULE](F=F, k=k)
    eng = Engine(width=a.grid, height=a.grid, rule=rule, seed=1)
    rng = np.random.default_rng(7 + a.idx)
    u = np.ones((a.grid, a.grid), np.float32); v = np.zeros((a.grid, a.grid), np.float32)
    r = 4
    for _ in range(24):
        cy = int(rng.integers(r, a.grid - r)); cx = int(rng.integers(r, a.grid - r))
        u[cy - r:cy + r, cx - r:cx + r] = 0.5; v[cy - r:cy + r, cx - r:cx + r] = 0.25
    v += rng.uniform(0, 0.02, (a.grid, a.grid)).astype(np.float32)
    eng.state.u = u; eng.state.v = np.clip(v, 0, 1)

    caps = sorted(set(int(x) for x in np.unique(
        np.round(np.logspace(0, np.log10(a.max_gen), a.frames)))))
    capset = set(caps)
    vs, gens, acts, ents, edges = [], [], [], [], []
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    g = 0
    while g < a.max_gen:
        g += 1
        eng.step()
        if g in capset:
            v0 = np.asarray(eng.state.v, np.float32).copy()
            eng.step(); g += 1                       # one extra step to measure motion
            v1 = np.asarray(eng.state.v, np.float32)
            act = float(np.abs(v1 - v0).mean())
            gx, gy = np.gradient(v0.astype(np.float64))
            vs.append(v0.astype(np.float16)); gens.append(g - 1)
            acts.append(act); ents.append(entropy(v0))
            edges.append(float(np.sqrt(gx * gx + gy * gy).mean()))
    np.savez_compressed(a.out, vs=np.array(vs), gens=np.array(gens),
                        acts=np.array(acts), ents=np.array(ents), edges=np.array(edges),
                        name=name, F=F, k=k, max_gen=a.max_gen)
    print(f"[{a.idx}] {name}: {len(gens)} horizons to gen {gens[-1]} "
          f"(act start={acts[0]:.5f} end={acts[-1]:.5f}) -> {a.out}")


if __name__ == "__main__":
    main()
