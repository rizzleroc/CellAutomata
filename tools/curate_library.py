"""Curate discovery results into a PLUS-subscriber replay library.

Reads discovery/results/*.jsonl (from tools/discover.py), keeps the life-like
and stabilised runs, de-duplicates near-identical (F, k) points, ranks by score,
gives each a human title + blurb, and writes:

  replay_library/manifest.json      index of curated "finds" (PLUS tier)
  replay_library/recipes/<id>.json  one deterministic, replayable recipe each
  replay_library/thumbs/<id>.gif    preview clip for featured finds (--render)

Every find is deterministic: replay via
  cellauto export --rule abiogenesis-stage1-grayscott --seed <seed> \
      --rule-config F=<F> --rule-config k=<k> --rule-config Du=<Du> --rule-config Dv=<Dv> \
      --grid <grid> --steps <steps_recommended> --out clip.gif

Usage:
  python3 tools/curate_library.py --top 40 --featured 16 --render
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "discovery", "results")
LIB = os.path.join(ROOT, "replay_library")
KEEP_CLASSES = {"living", "stable"}   # life-like (persistent) + stabilised (settled)


def load_records():
    recs = []
    for fp in sorted(glob.glob(os.path.join(RESULTS, "*.jsonl"))):
        with open(fp) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if "error" in r or "score" not in r:
                    continue
                recs.append(r)
    return recs


def bin_key(r):
    """Coarse F/k bin so we don't keep many near-identical points."""
    p = r["params"]
    return (round(p["F"] / 0.004) * 0.004, round(p["k"] / 0.004) * 0.004)


def gs_name(p, cls, metrics):
    F, k, edge = p["F"], p["k"], metrics["edge"]
    if F < 0.022:
        return "Travelling Waves" if edge > 0.05 else "Drifting Fronts"
    if k > 0.063:
        return "Self-Dividing Spots" if cls == "living" else "Frozen Spots"
    if k > 0.058:
        return "Coral Growth" if edge > 0.05 else "Negative Spots"
    if k > 0.052:
        return "Pulsing Maze" if cls == "living" else "Labyrinth"
    return "Mitosis Bloom" if cls == "living" else "Stripe Field"


def title_blurb(r):
    p, cls = r["params"], r["classification"]
    stab = r.get("stabilized_gen")
    name = gs_name(p, cls, r["metrics"])
    settle = f"stabilises ~gen {stab}" if stab else "persistent, never fully settles"
    blurb = (f"Gray-Scott reaction-diffusion at F={p['F']:.4f}, k={p['k']:.4f}; "
             f"{settle} ({cls}).")
    return name, blurb


def recommended_steps(r):
    stab = r.get("stabilized_gen")
    return int(min(2600, (stab + 900) if stab else 1800))


def export_thumb(find, out_gif):
    p = find["params"]
    cfg = []
    for key in ("F", "k", "Du", "Dv"):
        if key in p:
            cfg += ["--rule-config", f"{key}={p[key]}"]
    steps = min(900, find["steps_recommended"])
    cmd = ["cellauto", "export", "--rule", find["rule"], "--seed", str(find["seed"]),
           "--grid", str(find["grid"]), "--steps", str(steps), "--fps", "16",
           "--canvas", "480", "--out", out_gif, *cfg]
    return subprocess.run(cmd, capture_output=True, text=True).returncode == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=40, help="max finds to curate")
    ap.add_argument("--featured", type=int, default=16, help="how many get rendered thumbs")
    ap.add_argument("--grid", type=int, default=120, help="replay/render grid")
    ap.add_argument("--render", action="store_true")
    args = ap.parse_args()

    recs = load_records()
    print(f"loaded {len(recs)} records")
    kept = [r for r in recs if r.get("classification") in KEEP_CLASSES and r["score"] > 0.3]
    print(f"life-like + stabilised (score>0.3): {len(kept)}")

    # de-dup by coarse bin (best score per bin)
    best = {}
    for r in kept:
        b = bin_key(r)
        if b not in best or r["score"] > best[b]["score"]:
            best[b] = r
    deduped = sorted(best.values(), key=lambda x: x["score"], reverse=True)[:args.top]
    print(f"after de-dup + top-{args.top}: {len(deduped)}")

    os.makedirs(os.path.join(LIB, "recipes"), exist_ok=True)
    os.makedirs(os.path.join(LIB, "thumbs"), exist_ok=True)

    finds = []
    for i, r in enumerate(deduped, 1):
        fid = f"gs_{i:03d}"
        name, blurb = title_blurb(r)
        find = {
            "id": fid, "title": name, "blurb": blurb, "tier": "plus",
            "rule": r["rule"], "grid": args.grid, "seed": r["seed"],
            "params": r["params"],
            "steps_recommended": recommended_steps(r),
            "stabilized_gen": r.get("stabilized_gen"),
            "classification": r["classification"],
            "score": r["score"], "metrics": r["metrics"],
            "preview": f"thumbs/{fid}.gif",
            "replay_cmd": (
                f"cellauto export --rule {r['rule']} --seed {r['seed']} "
                + " ".join(f"--rule-config {k}={v}" for k, v in r["params"].items())
                + f" --grid {args.grid} --steps {recommended_steps(r)} --out {fid}.gif"
            ),
        }
        finds.append(find)
        with open(os.path.join(LIB, "recipes", fid + ".json"), "w") as fh:
            json.dump(find, fh, indent=2)

    manifest = {
        "name": "cellauto PLUS replay library",
        "description": "Curated, deterministic Gray-Scott simulations discovered by "
                       "a parameter sweep, scored for life-like emergence and "
                       "stabilisation. PLUS-subscriber tier.",
        "tier_default": "plus",
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "tools/discover.py sweep -> tools/curate_library.py",
        "count": len(finds),
        "featured": [f["id"] for f in finds[:args.featured]],
        "finds": finds,
    }
    with open(os.path.join(LIB, "manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=2)
    print(f"wrote manifest + {len(finds)} recipes -> {LIB}")

    if args.render:
        t0, ok = time.time(), 0
        for f in finds[:args.featured]:
            gif = os.path.join(LIB, "thumbs", f["id"] + ".gif")
            if export_thumb(f, gif):
                ok += 1
                print(f"  thumb {f['id']} ({f['title']}) ok", flush=True)
            else:
                print(f"  thumb {f['id']} FAILED", flush=True)
        print(f"rendered {ok}/{min(args.featured, len(finds))} thumbs ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
