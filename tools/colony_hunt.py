"""Colony hunt — search thousands of Gray-Scott sims for the most CREATIVE full
patterns, then render them ZOOMED OUT (whole field visible). No kaleidoscope,
no crop — the complete colony. Outputs full-field hero animations, a 4x4 "wall
of colonies" montage, a reel, and a GIF.

  python3 tools/colony_hunt.py --worker 0/16 --total 3300   # search shard
  python3 tools/colony_hunt.py --render                     # curate + render
"""
from __future__ import annotations
import argparse, glob, json, math, os, subprocess, sys, time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mandala_x as MX                       # PAL + colorize
from cellauto.engine import Engine
from cellauto.rules import REGISTRY

RULE = "abiogenesis-stage1-grayscott"
OUT = "discovery/colony"
FF = imageio_ffmpeg.get_ffmpeg_exe()
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
PALS = ["viridis", "magma", "ocean", "ember", "gold", "emerald", "amethyst", "nebula", "fire", "aqua", "ice", "rose"]
PALS = [p for p in PALS if p in MX.PAL]


def scatter(eng, grid, seed):
    rng = np.random.default_rng(seed)
    u = np.ones((grid, grid), np.float32); v = np.zeros((grid, grid), np.float32); r = 5
    for _ in range(grid // 10):
        cy = int(rng.integers(r, grid - r)); cx = int(rng.integers(r, grid - r))
        u[cy - r:cy + r, cx - r:cx + r] = 0.5; v[cy - r:cy + r, cx - r:cx + r] = 0.25
    v += rng.uniform(0, 0.02, (grid, grid)).astype(np.float32)
    eng.state.u = u; eng.state.v = np.clip(v, 0, 1)


def _entropy(f):
    h, _ = np.histogram(f, bins=24, range=(0, 1)); p = h / (h.sum() + 1e-12); p = p[p > 0]
    return float(-(p * np.log2(p)).sum() / np.log2(24))


def run_one(F, k, seed, grid=80, max_steps=700, sample=25):
    eng = Engine(width=grid, height=grid, rule=REGISTRY[RULE](F=F, k=k), seed=seed)
    scatter(eng, grid, seed)
    prev = None; acts, varis, edges, ents, covs = [], [], [], [], []
    warmup = max(120, max_steps // 6)
    for step in range(1, max_steps + 1):
        eng.step()
        if step % sample and step != max_steps:
            continue
        v = np.asarray(eng.state.v, np.float64)
        gx, gy = np.gradient(v)
        edges.append(float(np.sqrt(gx * gx + gy * gy).mean())); varis.append(float(v.var()))
        ents.append(_entropy(v)); covs.append(float((v > 0.06).mean()))
        acts.append(float(np.abs(v - prev).mean()) if prev is not None else 0.0); prev = v
        if step >= warmup and varis[-1] < 1e-4 and acts[-1] < 5e-5:
            break
    n = len(varis)
    if n < 3:
        return None
    i0 = n // 2
    ent_m = float(np.mean(ents[i0:])); edge_m = float(np.mean(edges[i0:]))
    var_m = float(np.mean(varis[i0:])); act_m = float(np.mean(acts[i0:])); cov = float(np.mean(covs[i0:]))
    var_f, act_f = varis[-1], acts[-1]
    alive = float(np.mean([1.0 if (vv > 1e-3 and aa > 3e-4) else 0.0 for vv, aa in zip(varis, acts)]))
    cls = ("dead" if (var_f < 1.2e-4 and prev is not None and float(prev.mean()) < .05)
           else "uniform" if var_f < 1.2e-4 else "stable" if act_f < 6e-4 else "living" if act_f < 5e-3 else "chaotic")
    structure = 0.5 * min(edge_m / 0.04, 1) + 0.5 * min(var_m / 0.02, 1)
    motion = 1 - math.exp(-act_m / 0.004)
    turb = min(act_m / 0.03, 1) * min(ent_m / 0.6, 1)
    creativity = (0.38 * ent_m + 0.30 * structure + 0.14 * motion + 0.10 * turb) * (0.35 + 0.65 * alive) * (0.4 + 0.6 * min(cov / 0.5, 1))
    if cls in ("dead", "uniform"):
        creativity *= 0.03
    return {"F": round(F, 5), "k": round(k, 5), "seed": seed, "cls": cls,
            "creativity": round(creativity, 4), "ent": round(ent_m, 4), "edge": round(edge_m, 5),
            "act": round(act_m, 5), "cov": round(cov, 3)}


def search_space(nf=66, nk=50):
    Fs = np.round(np.linspace(0.010, 0.098, nf), 5); Ks = np.round(np.linspace(0.038, 0.074, nk), 5)
    return [(float(F), float(k)) for F in Fs for k in Ks]


def worker(shard, nshards, total):
    combos = search_space()
    mine = [c for i, c in enumerate(combos) if i % nshards == shard]
    os.makedirs(OUT, exist_ok=True)
    out = f"{OUT}/c_{shard:02d}.jsonl"; t0, c = time.time(), 0
    with open(out, "w") as fh:
        for j, (F, k) in enumerate(mine):
            try:
                rec = run_one(F, k, 1)
            except Exception as e:  # noqa: BLE001
                rec = None
            if rec:
                fh.write(json.dumps(rec) + "\n"); c += 1
            if (j + 1) % 30 == 0:
                fh.flush(); print(f"shard {shard}: {j+1}/{len(mine)} ({time.time()-t0:.0f}s)", flush=True)
    print(f"DONE shard {shard}: {c} -> {out} ({time.time()-t0:.0f}s) [space={len(combos)}]")


def diverse_top(n):
    rs = []
    for fp in glob.glob(f"{OUT}/c_*.jsonl"):
        for l in open(fp):
            l = l.strip()
            if l:
                rs.append(json.loads(l))
    rs = [r for r in rs if r["cls"] in ("living", "chaotic", "stable")]
    rs.sort(key=lambda r: -r["creativity"])
    best = {}
    for r in rs:
        b = (round(r["F"] / 0.006), round(r["k"] / 0.004))
        if b not in best:
            best[b] = r
    return sorted(best.values(), key=lambda r: -r["creativity"])[:n], len(rs)


def evolve_field(F, k, grid, steps, seed=1):
    eng = Engine(width=grid, height=grid, rule=REGISTRY[RULE](F=F, k=k), seed=seed)
    scatter(eng, grid, seed)
    for _ in range(steps):
        eng.step()
    return eng


def render_hero(rec, pal, out, grid=240, dur=13, fps=30, size=1080):
    eng = evolve_field(rec["F"], rec["k"], grid, 0)
    N = dur * fps
    wr = imageio_ffmpeg.write_frames(out, (size, size), fps=fps, codec="libx264", pix_fmt_in="rgb24",
        pix_fmt_out="yuv420p", macro_block_size=2, output_params=["-crf", "19", "-preset", "medium"])
    wr.send(None)
    lf = ImageFont.truetype(FB, 38); sf = ImageFont.truetype(FR, 24)
    for fi in range(N):
        eng.step()
        v = np.asarray(eng.state.v, np.float32)
        img = Image.fromarray(MX.colorize(v, pal).astype(np.uint8)).resize((size, size), Image.BICUBIC).convert("RGB")
        d = ImageDraw.Draw(img)
        d.text((28, size - 70), f"F={rec['F']:.4f}  k={rec['k']:.4f}", font=lf, fill=(244, 248, 252))
        d.text((30, size - 28), f"{rec['cls']} · creativity {rec['creativity']:.2f}", font=sf, fill=(170, 190, 208))
        af = min(1.0, (fi + 1) / 12, (N - fi) / 12)
        fr = np.asarray(img, np.uint8)
        if af < 0.999:
            fr = (fr.astype(np.float32) * af).astype(np.uint8)
        wr.send(np.ascontiguousarray(fr).tobytes())
    wr.close()
    print(f"  hero -> {out}")


def render_wall(top16, out, dur=16, fps=30, cell=270, cols=4):
    rows = 4; W = cols * cell
    engs = [evolve_field(r["F"], r["k"], 120, 0, seed=1) for r in top16[:16]]
    N = dur * fps
    wr = imageio_ffmpeg.write_frames(out, (W, rows * cell), fps=fps, codec="libx264", pix_fmt_in="rgb24",
        pix_fmt_out="yuv420p", macro_block_size=2, output_params=["-crf", "20", "-preset", "medium"])
    wr.send(None)
    for fi in range(N):
        canvas = Image.new("RGB", (W, rows * cell), (5, 7, 11))
        for i, (e, r) in enumerate(zip(engs, top16[:16])):
            e.step(); v = np.asarray(e.state.v, np.float32)
            til = Image.fromarray(MX.colorize(v, PALS[i % len(PALS)]).astype(np.uint8)).resize((cell, cell), Image.BICUBIC)
            canvas.paste(til, ((i % cols) * cell, (i // cols) * cell))
        d = ImageDraw.Draw(canvas)
        d.rectangle([0, rows * cell - 40, W, rows * cell], fill=(5, 7, 11))
        d.text((16, rows * cell - 34), "WALL OF COLONIES — 16 full patterns, found by searching thousands of sims",
               font=ImageFont.truetype(FB, 22), fill=(235, 240, 248))
        af = min(1.0, (fi + 1) / 12, (N - fi) / 12)
        fr = np.asarray(canvas, np.uint8)
        if af < 0.999:
            fr = (fr.astype(np.float32) * af).astype(np.uint8)
        wr.send(np.ascontiguousarray(fr).tobytes())
    wr.close()
    print(f"  wall -> {out}")


def render():
    top, total = diverse_top(16)
    print(f"{total} alive sims; top 16 diverse creativity:")
    for r in top:
        print(f"  cr={r['creativity']} {r['cls']:7} F={r['F']:.4f} k={r['k']:.4f} ent={r['ent']} cov={r['cov']}")
    os.makedirs("media/colonies", exist_ok=True)
    render_wall(top, "media/colonies/wall_of_colonies.mp4")
    clips = []
    for i, r in enumerate(top[:6]):
        o = f"media/colonies/colony_{i}_F{r['F']:.4f}_k{r['k']:.4f}.mp4"
        render_hero(r, PALS[i % len(PALS)], o); clips.append(os.path.abspath(o))
    lst = "/tmp/colony_reel.txt"; open(lst, "w").write("".join(f"file '{c}'\n" for c in clips))
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", "-movflags", "+faststart", "media/colonies/colonies_reel.mp4"], check=True)
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", clips[0],
                    "-vf", "fps=12,scale=460:-1:flags=lanczos,palettegen=max_colors=80:stats_mode=diff", "/tmp/col_pal.png"], check=True)
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", clips[0], "-i", "/tmp/col_pal.png",
                    "-lavfi", "fps=12,scale=460:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=4",
                    "-loop", "0", "media/colonies/colony_hero.gif"], check=True)
    json.dump({"searched": total, "top": top}, open("discovery/colony_top.json", "w"), indent=2)
    print("DONE — wall + 6 heroes + reel + gif")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", default="")
    ap.add_argument("--total", type=int, default=3300)
    ap.add_argument("--render", action="store_true")
    a = ap.parse_args()
    if a.render:
        render()
    elif a.worker:
        sh, ns = (int(x) for x in a.worker.split("/")); worker(sh, ns, a.total)
    else:
        ap.error("need --worker i/N or --render")


if __name__ == "__main__":
    main()
