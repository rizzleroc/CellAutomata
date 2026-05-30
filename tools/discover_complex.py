"""Complexity-focused discovery — hunt for INCREDIBLE, sustained, complex
reactions (spatiotemporal chaos, spiral/wave turbulence, soliton gas) rather
than patterns that quietly settle.

Score rewards: high spatial entropy + persistent structure (edges/variance) +
sustained motion that never dies and never freezes. Chaotic regimes are the
prize here, not a penalty.

  python3 tools/discover_complex.py --demo
  python3 tools/discover_complex.py --shard 0/16 --out discovery/complex/cx_00.jsonl
"""
from __future__ import annotations
import argparse, json, os, time
import numpy as np
from cellauto.engine import Engine
from cellauto.rules import REGISTRY

RULE = "abiogenesis-stage1-grayscott"


def search_space(n_f=78, n_k=66, seeds=(1,)):
    Fs = np.round(np.linspace(0.010, 0.094, n_f), 5)
    Ks = np.round(np.linspace(0.038, 0.072, n_k), 5)
    return [(float(F), float(k), int(s)) for F in Fs for k in Ks for s in seeds]


def _entropy(f):
    h, _ = np.histogram(f, bins=24, range=(0.0, 1.0))
    p = h / (h.sum() + 1e-12)
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum() / np.log2(24))


def run_one(F, k, seed, grid, max_steps, sample, Du=0.16, Dv=0.08):
    rule = REGISTRY[RULE](F=F, k=k, Du=Du, Dv=Dv)
    eng = Engine(width=grid, height=grid, rule=rule, seed=seed)
    prev = None
    acts, varis, edges, ents = [], [], [], []
    warmup = max(120, max_steps // 6)
    for step in range(1, max_steps + 1):
        eng.step()
        if step % sample and step != max_steps:
            continue
        v = np.asarray(eng.state.v, np.float64)
        gx, gy = np.gradient(v)
        edges.append(float(np.sqrt(gx * gx + gy * gy).mean()))
        varis.append(float(v.var()))
        ents.append(_entropy(v))
        acts.append(float(np.abs(v - prev).mean()) if prev is not None else 0.0)
        prev = v
        if step >= warmup and varis[-1] < 1e-4 and acts[-1] < 5e-5:
            break

    n = len(varis)
    if n < 3:
        return None
    i0 = n // 2
    ent_m = float(np.mean(ents[i0:]))
    edge_m = float(np.mean(edges[i0:]))
    var_m = float(np.mean(varis[i0:]))
    act_m = float(np.mean(acts[i0:]))
    var_f, act_f = varis[-1], acts[-1]
    alive_frac = float(np.mean([1.0 if (vv > 1e-3 and aa > 3e-4) else 0.0
                                for vv, aa in zip(varis, acts)]))

    if var_f < 1.2e-4 and prev is not None and float(prev.mean()) < 0.05:
        cls = "dead"
    elif var_f < 1.2e-4:
        cls = "uniform"
    elif act_f < 6e-4:
        cls = "stable"
    elif act_f < 5e-3:
        cls = "living"
    else:
        cls = "chaotic"

    structure = 0.5 * min(edge_m / 0.04, 1.0) + 0.5 * min(var_m / 0.02, 1.0)
    motion = 1.0 - float(np.exp(-act_m / 0.004))           # saturating, sustained motion
    turb = min(act_m / 0.03, 1.0) * min(ent_m / 0.6, 1.0)  # high-entropy high-activity bonus
    complexity = (0.40 * ent_m + 0.32 * structure + 0.16 * motion + 0.12 * turb) \
        * (0.35 + 0.65 * alive_frac)
    if cls in ("dead", "uniform"):
        complexity *= 0.03
    elif cls == "stable":
        complexity *= 0.55

    return {
        "rule": RULE,
        "params": {"F": round(F, 5), "k": round(k, 5), "Du": Du, "Dv": Dv},
        "seed": seed, "grid": grid, "steps_run": n * sample,
        "classification": cls,
        "complexity": round(float(complexity), 4),
        "metrics": {
            "entropy_m": round(ent_m, 4), "edge_m": round(edge_m, 5),
            "var_m": round(var_m, 5), "activity_m": round(act_m, 5),
            "alive_frac": round(alive_frac, 3),
            "entropy_f": round(ents[-1], 4), "activity_f": round(act_f, 5),
        },
    }


def demo(grid, max_steps, sample):
    cases = {
        "chaos-α": (0.0162, 0.0448), "spirals": (0.0118, 0.0500),
        "worm-turb": (0.0186, 0.0502), "pulse-chaos": (0.026, 0.054),
        "u-skate": (0.062, 0.0609), "coral": (0.0545, 0.062),
        "labyrinth": (0.029, 0.057), "mitosis": (0.0367, 0.0649),
        "dead": (0.06, 0.07),
    }
    print(f"{'case':12} {'cplx':>6} {'class':8} {'ent':>6} {'edge':>7} {'act':>8} {'alive':>6}")
    out = []
    for name, (F, k) in cases.items():
        r = run_one(F, k, 1, grid, max_steps, sample)
        out.append((r["complexity"], name, r))
    for c, name, r in sorted(out, reverse=True):
        m = r["metrics"]
        print(f"{name:12} {c:6.3f} {r['classification']:8} {m['entropy_m']:6.3f} "
              f"{m['edge_m']:7.4f} {m['activity_m']:8.5f} {m['alive_frac']:6.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", default="0/1")
    ap.add_argument("--grid", type=int, default=82)
    ap.add_argument("--max-steps", type=int, default=1000)
    ap.add_argument("--sample", type=int, default=30)
    ap.add_argument("--out", default="")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()
    if args.demo:
        demo(args.grid, args.max_steps, args.sample)
        return
    shard, nshards = (int(x) for x in args.shard.split("/"))
    combos = search_space()
    mine = [c for i, c in enumerate(combos) if i % nshards == shard]
    out = args.out or f"discovery/complex/cx_shard_{shard:02d}.jsonl"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    t0, n = time.time(), 0
    with open(out, "w") as fh:
        for j, (F, k, s) in enumerate(mine):
            try:
                rec = run_one(F, k, s, args.grid, args.max_steps, args.sample)
            except Exception as e:  # noqa: BLE001
                rec = {"params": {"F": F, "k": k}, "seed": s, "error": str(e)}
            if rec:
                fh.write(json.dumps(rec) + "\n"); fh.flush(); n += 1
            if (j + 1) % 25 == 0:
                print(f"shard {shard}/{nshards}: {j+1}/{len(mine)} ({time.time()-t0:.0f}s)", flush=True)
    print(f"DONE shard {shard}/{nshards}: {n} recs -> {out} ({time.time()-t0:.0f}s) [space={len(combos)}]")


if __name__ == "__main__":
    main()
