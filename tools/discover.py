"""Discovery harness — sweep Gray-Scott reaction-diffusion parameters, score each
run for life-like emergent structure, and detect WHEN the pattern stabilises.

This is the engine behind the PLUS replay library: it searches thousands of
(F, k, seed) points, keeps the ones that look alive, and records exactly how to
replay each one. Every find is fully deterministic — replay via

    rule = REGISTRY["abiogenesis-stage1-grayscott"](F=.., k=.., Du=.., Dv=..)
    eng  = Engine(width=g, height=g, rule=rule, seed=s); eng.step() * steps

(equivalently: cellauto export --rule abiogenesis-stage1-grayscott --seed s
 --rule-config F=.. --rule-config k=.. ...).

Metrics are numpy-only. Each run is sampled every `--sample` steps; we track
spatial structure (variance, edge/gradient density, histogram entropy) and
temporal activity (mean abs frame-to-frame change of the v field), classify the
end state, find the stabilisation generation, and roll it into one score.

Sharding: the (F, k, seed) enumeration is deterministic; `--shard i/N` runs
every Nth point, so N workers/subagents cover disjoint slices with no overlap.

Validate scoring before scaling:   python3 tools/discover.py --demo
Run a shard:                       python3 tools/discover.py --shard 0/16 --out discovery/results/shard_00.jsonl
"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np

from cellauto.engine import Engine
from cellauto.rules import REGISTRY

RULE = "abiogenesis-stage1-grayscott"


# --------------------------------------------------------------------------
# search space — Gray-Scott Pearson F/k plane x seeds
# --------------------------------------------------------------------------
def search_space(n_f=56, n_k=48, seeds=(1, 7)):
    Fs = np.round(np.linspace(0.010, 0.078, n_f), 5)
    Ks = np.round(np.linspace(0.040, 0.072, n_k), 5)
    combos = []
    for F in Fs:
        for k in Ks:
            for s in seeds:
                combos.append((float(F), float(k), int(s)))
    return combos


# --------------------------------------------------------------------------
# metrics
# --------------------------------------------------------------------------
def _entropy(f):
    h, _ = np.histogram(f, bins=24, range=(0.0, 1.0))
    p = h / (h.sum() + 1e-12)
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum() / np.log2(24))  # normalised 0..1


def run_one(F, k, seed, grid, max_steps, sample, Du=0.16, Dv=0.08):
    rule = REGISTRY[RULE](F=F, k=k, Du=Du, Dv=Dv)
    eng = Engine(width=grid, height=grid, rule=rule, seed=seed)

    prev = None
    gens, acts, varis, edges, ents, means = [], [], [], [], [], []
    warmup = max(160, max_steps // 6)
    for step in range(1, max_steps + 1):
        eng.step()
        if step % sample and step != max_steps:
            continue
        v = np.asarray(eng.state.v, dtype=np.float64)
        gx, gy = np.gradient(v)
        edge = float(np.sqrt(gx * gx + gy * gy).mean())
        var = float(v.var())
        mean = float(v.mean())
        act = float(np.abs(v - prev).mean()) if prev is not None else 0.0
        prev = v
        gens.append(step); acts.append(act); varis.append(var)
        edges.append(edge); ents.append(_entropy(v)); means.append(mean)
        # early exit: structureless + quiet (dead or saturated) after warmup
        if step >= warmup and var < 1e-4 and act < 5e-5:
            break

    n = len(gens)
    if n == 0:
        return None
    var_f, edge_f, ent_f, mean_f, act_f = varis[-1], edges[-1], ents[-1], means[-1], acts[-1]

    # classification of the end state
    if var_f < 1.2e-4 and mean_f < 0.05:
        cls = "dead"            # faded to empty (v->0)
    elif var_f < 1.2e-4:
        cls = "uniform"         # flat non-empty
    elif act_f < 6e-4:
        cls = "stable"          # structured + quasi-frozen  <- "life stabilised"
    elif act_f < 5e-3:
        cls = "living"          # structured + persistent bounded motion
    else:
        cls = "chaotic"         # structured but never settles

    # stabilisation generation: first gen where a trailing window of activity is
    # low while structure (variance) is present and roughly steady.
    stab = None
    w = max(2, n // 8)
    for i in range(w, n):
        win_act = acts[i - w:i]
        win_var = varis[i - w:i]
        mv = float(np.mean(win_var))
        if mv > 2e-3 and float(np.mean(win_act)) < 5e-3 \
                and float(np.std(win_var)) < 0.04 * (mv + 1e-9):
            stab = gens[i - w]
            break

    # score = structure + complexity + life-bonus + stabilisation, minus penalties
    structure = 0.5 * min(var_f / 0.03, 1.0) + 0.5 * min(edge_f / 0.06, 1.0)
    complexity = ent_f
    life = float(np.exp(-((act_f - 0.0020) ** 2) / (2 * 0.0016 ** 2))) if act_f > 1.5e-4 else 0.0
    stab_bonus = 0.0
    if stab is not None:
        frac = stab / max_steps
        stab_bonus = float(np.exp(-((frac - 0.35) ** 2) / (2 * 0.28 ** 2)))
    score = 0.34 * structure + 0.16 * complexity + 0.28 * life + 0.22 * stab_bonus
    if cls in ("dead", "uniform"):
        score *= 0.05
    elif cls == "chaotic":
        score *= 0.6

    return {
        "rule": RULE,
        "params": {"F": round(F, 5), "k": round(k, 5), "Du": Du, "Dv": Dv},
        "seed": seed, "grid": grid,
        "steps_run": gens[-1], "max_steps": max_steps,
        "classification": cls, "stabilized_gen": stab,
        "score": round(float(score), 4),
        "metrics": {
            "var": round(var_f, 6), "edge": round(edge_f, 6), "entropy": round(ent_f, 4),
            "mean": round(mean_f, 4), "activity": round(act_f, 6),
        },
    }


# --------------------------------------------------------------------------
# drivers
# --------------------------------------------------------------------------
def demo(grid, max_steps, sample):
    cases = {
        "mitosis": (0.0367, 0.0649), "spots": (0.035, 0.065),
        "coral": (0.0545, 0.062), "labyrinth": (0.029, 0.057),
        "waves": (0.014, 0.045), "u-skate": (0.062, 0.0609),
        "dead-high-k": (0.06, 0.07), "dead-low-F": (0.011, 0.066),
    }
    print(f"{'preset':12} {'score':>6} {'class':8} {'stab':>6} {'var':>8} {'edge':>7} {'act':>9}")
    for name, (F, k) in cases.items():
        r = run_one(F, k, 1, grid, max_steps, sample)
        m = r["metrics"]
        print(f"{name:12} {r['score']:6.3f} {r['classification']:8} "
              f"{str(r['stabilized_gen']):>6} {m['var']:8.4f} {m['edge']:7.4f} {m['activity']:9.6f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", default="0/1", help="i/N — run every Nth point")
    ap.add_argument("--grid", type=int, default=80)
    ap.add_argument("--max-steps", type=int, default=1500)
    ap.add_argument("--sample", type=int, default=40)
    ap.add_argument("--seeds", default="1,7")
    ap.add_argument("--out", default="")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()

    if args.demo:
        demo(args.grid, args.max_steps, args.sample)
        return

    shard, nshards = (int(x) for x in args.shard.split("/"))
    seeds = tuple(int(s) for s in args.seeds.split(","))
    combos = search_space(seeds=seeds)
    mine = [c for i, c in enumerate(combos) if i % nshards == shard]
    out = args.out or f"discovery/results/gs_shard_{shard:02d}.jsonl"
    os.makedirs(os.path.dirname(out), exist_ok=True)

    t0 = time.time()
    n = 0
    with open(out, "w") as fh:
        for j, (F, k, s) in enumerate(mine):
            try:
                rec = run_one(F, k, s, args.grid, args.max_steps, args.sample)
            except Exception as e:  # noqa: BLE001
                rec = {"rule": RULE, "params": {"F": F, "k": k}, "seed": s, "error": str(e)}
            if rec:
                fh.write(json.dumps(rec) + "\n")
                fh.flush()
                n += 1
            if (j + 1) % 25 == 0:
                print(f"shard {shard}/{nshards}: {j+1}/{len(mine)} ({time.time()-t0:.0f}s)",
                      flush=True)
    print(f"DONE shard {shard}/{nshards}: {n} records -> {out} ({time.time()-t0:.0f}s) "
          f"[total space={len(combos)}]")


if __name__ == "__main__":
    main()
