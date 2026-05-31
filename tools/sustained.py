"""Sustained-change search — the real target: not just survival, but the
LONGEST run of consecutive generations where the pattern keeps meaningfully
changing (no settle, no short cycle). That window is exactly how many seconds
of continuous, non-repeating motion a clip can show.

Same rule as the app's conway (B3/S23, toroidal). Reproducible by seed.

  python3 tools/sustained.py --shard 0/16 --total 2400 --out discovery/sustained/s_00.jsonl
"""
from __future__ import annotations
import argparse, json, os, time, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from monkeys import step, soup


def run(seed, G, S, dens, max_gen, thr_frac=0.004):
    g = soup(seed, G, S, dens)
    thr = thr_frac * G * G
    seen = {}
    peak = int(g.sum()); cur = best = active = 0
    fate, lifespan = "perpetual", max_gen
    for gen in range(max_gen + 1):
        pop = int(g.sum())
        if pop == 0:
            fate, lifespan = "extinct", gen; break
        peak = max(peak, pop)
        h = hash(g.tobytes())
        if h in seen:
            p = gen - seen[h]
            fate, lifespan = (f"period-{p}" if p > 1 else "still-life"), seen[h]; break
        seen[h] = gen
        gn = step(g)
        if int((gn != g).sum()) > thr:
            cur += 1; best = max(best, cur); active += 1
        else:
            cur = 0
        g = gn
    return {"seed": seed, "G": G, "S": S, "dens": dens, "init": int(soup(seed, G, S, dens).sum()),
            "sustained": best, "lifespan": lifespan, "active_gens": active,
            "fate": fate, "peak": peak}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", default="0/1")
    ap.add_argument("--total", type=int, default=2400)
    ap.add_argument("--grid", type=int, default=120)
    ap.add_argument("--soup", type=int, default=36)
    ap.add_argument("--dens", type=float, default=0.40)
    ap.add_argument("--max-gen", type=int, default=2200)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    shard, n = (int(x) for x in a.shard.split("/"))
    out = a.out or f"discovery/sustained/s_{shard:02d}.jsonl"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    seeds = range(shard, a.total, n)
    t0, c = time.time(), 0
    with open(out, "w") as fh:
        for j, s in enumerate(seeds):
            fh.write(json.dumps(run(s, a.grid, a.soup, a.dens, a.max_gen)) + "\n"); c += 1
            if (j + 1) % 50 == 0:
                fh.flush()
                print(f"shard {shard}/{n}: {j+1}/{len(seeds)} ({time.time()-t0:.0f}s)", flush=True)
    print(f"DONE shard {shard}/{n}: {c} soups -> {out} ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
