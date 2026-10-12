#!/usr/bin/env python3
"""Write <EPN>/SHOTS_BY_OWNER.md: every owner's shots with the dialogue lines inside them (absolute + shot-relative
times) — the sheet each shot-author subagent works from.   python3 shots_by_owner.py ep5 [owner1 owner2 ...]"""
import json, os, sys
from collections import defaultdict
EP = sys.argv[1] if len(sys.argv) > 1 else "ep5"
root = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(root, EP, "timeline.json") if os.path.exists(os.path.join(root, EP, "timeline.json")) else os.path.join(EP, "timeline.json")
tl = json.load(open(path))
own = defaultdict(list)
for s in tl["shots"]:
    ls = [l for l in tl["lines"] if l["t0"] < s["t1"] and l["t1"] > s["t0"]]
    own[s["owner"]].append((s, ls))
owners = sys.argv[2:] or [o for o in own if o != "main"]
out = []
for o in owners:
    out.append(f"### owner `{o}` -> module `eng/shots_{EP}_{o}.py`")
    for s, ls in own[o]:
        out.append(f"- **{s['id']}**  {s['t0']:.2f}-{s['t1']:.2f} s ({s['t1'] - s['t0']:.1f}s): {s['desc']}")
        for l in ls:
            out.append(f"    - {l['id']} {l['spk']:6s} {l['t0']:.2f}-{l['t1']:.2f} (shot-time {l['t0'] - s['t0']:.2f}-{l['t1'] - s['t0']:.2f}): \"{l['text']}\"")
dst = os.path.join(os.path.dirname(path), "SHOTS_BY_OWNER.md")
open(dst, "w").write("\n".join(out) + "\n")
print("wrote", dst, "-", sum(len(own[o]) for o in owners), "shots for", ", ".join(owners))
