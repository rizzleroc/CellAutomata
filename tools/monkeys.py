"""Monkeys at keyboards — Conway's Life soup search.

Spray thousands of RANDOM soups and hunt the freak outcomes: a tiny random
scribble that stays chaotically alive for thousands of generations (a
methuselah) or never settles at all (perpetual motion on the torus). Same rule
as the app's `conway` (B3/S23, toroidal wrap) — just a fast numpy stepper so we
can afford the haystack.

Every find is reproducible from its integer seed.

  python3 tools/monkeys.py --shard 0/16 --total 8000 --out discovery/monkeys/m_00.jsonl
"""
from __future__ import annotations
import argparse, json, os, time
import numpy as np


def step(g):
    a = g.astype(np.uint8)  # sum as ints — summing bools is OR, not a count
    n = (np.roll(a, 1, 0) + np.roll(a, -1, 0) + np.roll(a, 1, 1) + np.roll(a, -1, 1)
         + np.roll(np.roll(a, 1, 0), 1, 1) + np.roll(np.roll(a, 1, 0), -1, 1)
         + np.roll(np.roll(a, -1, 0), 1, 1) + np.roll(np.roll(a, -1, 0), -1, 1))
    return (n == 3) | (g & (n == 2))


def soup(seed, G, S, dens):
    rng = np.random.default_rng(seed)
    g = np.zeros((G, G), bool)
    o = (G - S) // 2
    g[o:o + S, o:o + S] = rng.random((S, S)) < dens
    return g


def run(seed, G, S, dens, max_gen):
    g = soup(seed, G, S, dens)
    init = int(g.sum())
    seen = {}
    peak = init
    longevity, period, fate = max_gen, 0, "perpetual"
    for gen in range(max_gen + 1):
        pop = int(g.sum())
        if pop == 0:
            longevity, period, fate = gen, 0, "extinct"
            break
        peak = max(peak, pop)
        h = hash(g.tobytes())
        if h in seen:
            longevity, period = seen[h], gen - seen[h]
            fate = "still-life" if period == 1 else f"period-{period}"
            break
        seen[h] = gen
        g = step(g)
    final = int(g.sum())
    return {
        "seed": seed, "G": G, "S": S, "dens": dens,
        "init_cells": init, "longevity": longevity, "period": period,
        "fate": fate, "peak": peak, "final": final,
        "growth": round(peak / max(init, 1), 2),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", default="0/1")
    ap.add_argument("--total", type=int, default=8000)
    ap.add_argument("--grid", type=int, default=90)
    ap.add_argument("--soup", type=int, default=22)
    ap.add_argument("--dens", type=float, default=0.44)
    ap.add_argument("--max-gen", type=int, default=2500)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    shard, n = (int(x) for x in a.shard.split("/"))
    out = a.out or f"discovery/monkeys/m_{shard:02d}.jsonl"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    seeds = range(shard, a.total, n)
    t0, c = time.time(), 0
    with open(out, "w") as fh:
        for j, s in enumerate(seeds):
            r = run(s, a.grid, a.soup, a.dens, a.max_gen)
            fh.write(json.dumps(r) + "\n"); c += 1
            if (j + 1) % 100 == 0:
                fh.flush()
                print(f"shard {shard}/{n}: {j+1}/{len(seeds)} ({time.time()-t0:.0f}s)", flush=True)
    print(f"DONE shard {shard}/{n}: {c} soups -> {out} ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
