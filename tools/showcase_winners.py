"""Definitive reel built from the ACTUAL winners of the complexity sweep
(discovery/complex/*.jsonl). Picks the top sustained-complexity finds across
both families — soliton gas + turbulent chaos — and renders each fullscreen,
labelled with its measured complexity score and global rank. The visuals are
the discovery output, not hand-picked."""
from __future__ import annotations
import glob, json, os, numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
from cellauto.engine import Engine
from cellauto.rules import REGISTRY

RULE = "abiogenesis-stage1-grayscott"
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SIZE, FPS, GRID = 1080, 30, 220


def lut(stops):
    g = np.linspace(0, 1, 256); xs = np.array([s[0] for s in stops])
    cols = np.array([s[1] for s in stops], float)
    return np.stack([np.interp(g, xs, cols[:, c]) for c in range(3)], 1).astype(np.uint8)


PAL = [
    lut([(0, (3, 6, 14)), (.3, (12, 60, 70)), (.55, (24, 150, 120)), (.78, (120, 222, 96)), (1, (236, 255, 190))]),   # aurora
    lut([(0, (0, 0, 4)), (.25, (60, 15, 92)), (.5, (152, 30, 112)), (.75, (242, 92, 80)), (.9, (252, 162, 92)), (1, (252, 253, 191))]),  # magma
    lut([(0, (2, 4, 18)), (.3, (6, 42, 84)), (.55, (10, 125, 155)), (.8, (44, 214, 194)), (1, (228, 255, 238))]),     # ocean
    lut([(0, (4, 2, 2)), (.22, (70, 12, 8)), (.5, (175, 35, 12)), (.75, (245, 120, 25)), (1, (255, 240, 175))]),      # ember
    lut([(0, (68, 1, 84)), (.25, (59, 82, 139)), (.5, (33, 145, 140)), (.75, (94, 201, 98)), (1, (253, 231, 37))]),   # viridis
]


def colorize(v, pal, vmax=0.42, gamma=0.82):
    return PAL[pal][(np.clip(v / vmax, 0, 1) ** gamma * 255).astype(np.uint8)]


def name_for(r):
    m = r["metrics"]; a = m["activity_m"]; cls = r["classification"]
    if cls == "chaotic":
        return "HYPERCHAOS" if a > 0.10 else ("WAVE TURBULENCE" if a > 0.05 else "PLASMA CHAOS")
    return "SOLITON LATTICE" if m["edge_m"] > 0.052 else "SOLITON GAS"


def select():
    rs = []
    for fp in glob.glob("discovery/complex/cx_shard_*.jsonl"):
        for l in open(fp):
            l = l.strip()
            if not l:
                continue
            try:
                r = json.loads(l)
            except Exception:
                continue
            if "complexity" in r:
                rs.append(r)
    rs.sort(key=lambda r: -r["complexity"])
    rank = {id(r): i + 1 for i, r in enumerate(rs)}
    total = len(rs)
    # dedup by coarse F/k bin
    best = {}
    for r in rs:
        p = r["params"]; b = (round(p["F"] / 0.007), round(p["k"] / 0.004))
        if b not in best:
            best[b] = r
    ded = sorted(best.values(), key=lambda r: -r["complexity"])
    liv = [r for r in ded if r["classification"] == "living"][:3]
    cha = [r for r in ded if r["classification"] == "chaotic"][:3]
    picks = [x for pair in zip(liv, cha) for x in pair]  # interleave for variety
    return picks, rank, total


def overlay(name, sub):
    ov = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for i in range(160):
        d.line([(0, SIZE - 160 + i), (SIZE, SIZE - 160 + i)], fill=(0, 0, 0, int(155 * (i / 160) ** 1.6)))
    d.text((40, SIZE - 100), name, font=ImageFont.truetype(FB, 46), fill=(245, 249, 253))
    d.text((42, SIZE - 48), sub, font=ImageFont.truetype(FR, 25), fill=(184, 202, 218))
    return ov


def main(out="media/complex_winners.mp4"):
    os.makedirs("media", exist_ok=True)
    picks, rank, total = select()
    print(f"selected {len(picks)} winners of {total}")
    wr = imageio_ffmpeg.write_frames(out, (SIZE, SIZE), fps=FPS, codec="libx264",
        pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=8,
        output_params=["-crf", "18", "-preset", "medium"])
    wr.send(None)
    secs = 10
    for si, r in enumerate(picks):
        p = r["params"]; pal = si % len(PAL)
        nm = name_for(r)
        sub = (f"F={p['F']:.4f}  k={p['k']:.4f}   ·   COMPLEXITY {r['complexity']:.2f}   "
               f"·   #{rank[id(r)]} of {total:,}")
        rule = REGISTRY[RULE](F=p["F"], k=p["k"], Du=p["Du"], Dv=p["Dv"])
        eng = Engine(width=GRID, height=GRID, rule=rule, seed=r.get("seed", 1))
        rng = np.random.default_rng(99 + si)
        u = np.ones((GRID, GRID), np.float32); v = np.zeros((GRID, GRID), np.float32)
        rr = 5
        for _ in range(22):
            cy = int(rng.integers(rr, GRID - rr)); cx = int(rng.integers(rr, GRID - rr))
            u[cy - rr:cy + rr, cx - rr:cx + rr] = 0.5
            v[cy - rr:cy + rr, cx - rr:cx + rr] = 0.25
        v += rng.uniform(0, 0.02, (GRID, GRID)).astype(np.float32)
        eng.state.u = u; eng.state.v = np.clip(v, 0, 1)
        ov = overlay(f"{nm}", sub)
        n = secs * FPS; last = None
        for j in range(n):
            eng.step()
            img = Image.fromarray(colorize(np.asarray(eng.state.v, np.float32), pal)
                                  ).resize((SIZE, SIZE), Image.BICUBIC)
            img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
            a = min(1.0, (j + 1) / 12, (n - j) / 12)
            fr = np.asarray(img, np.uint8)
            if a < 0.999:
                fr = (fr.astype(np.float32) * a).astype(np.uint8)
            wr.send(np.ascontiguousarray(fr).tobytes())
            last = np.asarray(eng.state.v, np.float32)
        Image.fromarray(colorize(last, pal)).resize((900, 900), Image.BICUBIC).save(
            f"media/win_{si}_{nm.split()[0].lower()}.png")
        print(f"  [{si}] {nm:16} cx={r['complexity']:.2f} F={p['F']:.4f} k={p['k']:.4f}")
    wr.close()
    # tiny manifest of the chosen winners
    man = [{"rank": rank[id(r)], "name": name_for(r), "complexity": r["complexity"],
            "classification": r["classification"], "params": r["params"],
            "seed": r.get("seed", 1), "metrics": r["metrics"]} for r in picks]
    json.dump({"total_sims": total, "winners": man},
              open("discovery/complex_top.json", "w"), indent=2)
    print(f"DONE -> {out} ({os.path.getsize(out)/1e6:.1f} MB, {len(picks)*secs}s) + discovery/complex_top.json")


if __name__ == "__main__":
    main()
