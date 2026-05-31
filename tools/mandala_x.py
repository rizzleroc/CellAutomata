"""Mind-bending mandalas — push past 'cool'.

Advanced kaleidoscope: COMPOUND symmetry (two fold orders interfering) + MULTI-
OCTAVE self-similar fractal overlays (mandala-within-mandala), on ultra-busy
scatter-seeded reaction-diffusion sources. 16-way search scores candidates by a
complexity metric (high-freq Laplacian detail x entropy x coverage), keeps the
champions, renders 2160 stills + a seamless rotating/breathing GIF.

  python3 tools/mandala_x.py --worker 0      # one of 16 search workers
  python3 tools/mandala_x.py --render        # curate + render winners
"""
from __future__ import annotations
import argparse, glob, json, math, os, subprocess, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mandala as M
import imageio_ffmpeg
from cellauto.engine import Engine
from cellauto.rules import REGISTRY

RULE = M.RULE
OUT = "discovery/mandalax"
FF = imageio_ffmpeg.get_ffmpeg_exe()


def lut(stops):
    g = np.linspace(0, 1, 256); xs = np.array([s[0] for s in stops])
    cols = np.array([s[1] for s in stops], float)
    return np.stack([np.interp(g, xs, cols[:, c]) for c in range(3)], 1).astype(np.uint8)


PAL = dict(M.PALS)
PAL["nebula"] = lut([(0, (2, 2, 12)), (.25, (30, 10, 80)), (.5, (120, 30, 140)), (.7, (220, 70, 120)), (.85, (250, 170, 120)), (1, (250, 245, 230))])
PAL["fire"] = lut([(0, (2, 1, 2)), (.2, (80, 8, 4)), (.45, (190, 40, 8)), (.7, (250, 130, 20)), (.88, (255, 210, 90)), (1, (255, 252, 220))])
PAL["aqua"] = lut([(0, (1, 6, 12)), (.3, (6, 60, 80)), (.55, (10, 150, 150)), (.78, (90, 230, 200)), (1, (225, 255, 240))])

REGIMES = [
    ("chaos", dict(F=0.018, k=0.050)), ("labyrinth", dict(preset="labyrinth")),
    ("maze", dict(F=0.026, k=0.055)), ("turbulence", dict(F=0.022, k=0.051)),
    ("worm", dict(F=0.0186, k=0.0502)), ("coral", dict(F=0.0545, k=0.062)),
    ("plasma", dict(F=0.0264, k=0.0579)), ("stripes", dict(F=0.030, k=0.057)),
]
CONFIGS = [(nm, kw, s) for s in (1, 7) for nm, kw in REGIMES]   # 16


def evolve_scatter(kw, grid, steps, seed):
    eng = Engine(width=grid, height=grid, rule=REGISTRY[RULE](**kw), seed=seed)
    rng = np.random.default_rng(seed)
    u = np.ones((grid, grid), np.float32); v = np.zeros((grid, grid), np.float32); r = 5
    for _ in range(grid // 8):
        cy = int(rng.integers(r, grid - r)); cx = int(rng.integers(r, grid - r))
        u[cy - r:cy + r, cx - r:cx + r] = 0.5; v[cy - r:cy + r, cx - r:cx + r] = 0.25
    v += rng.uniform(0, 0.02, (grid, grid)).astype(np.float32)
    eng.state.u = u; eng.state.v = np.clip(v, 0, 1)
    for _ in range(steps):
        eng.step()
    v = np.asarray(eng.state.v, np.float32)
    return v / (v.max() + 1e-6)


class Kal:
    def __init__(self, K, G):
        yy, xx = np.mgrid[0:K, 0:K]; c = K / 2.0
        self.R = np.hypot(xx - c, yy - c).astype(np.float32)
        self.TH = np.arctan2(yy - c, xx - c).astype(np.float32)
        self.mask = np.clip((0.99 - self.R / (K / 2.0)) / 0.05, 0, 1).astype(np.float32)
        self.scale = G / float(K); self.G = G

    def fold(self, V, n, phase, zoom):
        wedge = 2 * np.pi / n
        a = np.mod(self.TH + phase, wedge); a = np.minimum(a, wedge - a)
        rr = self.R * self.scale * zoom; G = self.G
        sx = np.clip(G / 2 + rr * np.cos(a), 0, G - 1.001)
        sy = np.clip(G / 2 + rr * np.sin(a), 0, G - 1.001)
        x0 = sx.astype(np.int32); y0 = sy.astype(np.int32); fx = sx - x0; fy = sy - y0
        return (V[y0, x0] * (1 - fx) * (1 - fy) + V[y0, x0 + 1] * fx * (1 - fy)
                + V[y0 + 1, x0] * (1 - fx) * fy + V[y0 + 1, x0 + 1] * fx * fy)


def warp(Mf, scale, rot):
    K = Mf.shape[0]; c = K / 2.0
    yy, xx = np.mgrid[0:K, 0:K]; dx = xx - c; dy = yy - c
    ca, sa = np.cos(rot), np.sin(rot)
    sx = c + (dx * ca - dy * sa) * scale; sy = c + (dx * sa + dy * ca) * scale
    inb = (sx >= 0) & (sx < K - 1) & (sy >= 0) & (sy < K - 1)
    sx = np.clip(sx, 0, K - 1.001); sy = np.clip(sy, 0, K - 1.001)
    x0 = sx.astype(np.int32); y0 = sy.astype(np.int32); fx = sx - x0; fy = sy - y0
    out = (Mf[y0, x0] * (1 - fx) * (1 - fy) + Mf[y0, x0 + 1] * fx * (1 - fy)
           + Mf[y0 + 1, x0] * (1 - fx) * fy + Mf[y0 + 1, x0 + 1] * fx * fy)
    return out * inb


def compound(kal, V, n1, n2, octs):
    A = kal.fold(V, n1, 0.0, 0.985)
    B = kal.fold(V, n2, np.pi / max(n2, 1) * 0.5, 0.99)
    Mf = np.maximum(A, 0.82 * B)
    g = math.gcd(n1, n2)
    for oi in range(octs):
        Mf = np.maximum(Mf, (0.6 - 0.13 * oi) * warp(Mf, 2.0 + 1.4 * oi, 2 * np.pi / g * (oi + 1)))
    Mf = Mf * kal.mask
    return Mf / (Mf.max() + 1e-6)


def score(Mf):
    cov = float((Mf > 0.06).mean())
    h, _ = np.histogram(Mf, bins=32, range=(0, 1)); p = h / (h.sum() + 1e-9); p = p[p > 0]
    ent = float(-(p * np.log2(p)).sum() / np.log2(32))
    lap = 4 * Mf - np.roll(Mf, 1, 0) - np.roll(Mf, -1, 0) - np.roll(Mf, 1, 1) - np.roll(Mf, -1, 1)
    hf = float(np.abs(lap).mean())
    gx, gy = np.gradient(Mf); gr = float(np.hypot(gx, gy).mean())
    return hf * ent * (0.3 + cov) * (1 + 4 * gr)


def colorize(Mf, pal, gamma=0.7):
    pos = Mf[Mf > 0.02]
    hi = np.percentile(pos, 99.5) if pos.size else 1.0
    f = np.clip(Mf / (hi + 1e-6), 0, 1) ** gamma
    return PAL[pal][(f * 255).astype(np.uint8)]


def worker(idx):
    nm, kw, seed = CONFIGS[idx]; grid = 360
    V = evolve_scatter(kw, grid, 620, seed)
    os.makedirs(OUT, exist_ok=True)
    np.savez_compressed(f"{OUT}/src_{idx:02d}.npz", V=V.astype(np.float16), regime=nm, grid=grid, seed=seed)
    kal = Kal(420, grid)
    best = None
    for n1 in (8, 10, 12, 16):
        for n2 in (3, 5, 6):
            for octs in (1, 2):
                sc = score(compound(kal, V, n1, n2, octs))
                if best is None or sc > best["score"]:
                    best = {"idx": idx, "regime": nm, "seed": seed, "grid": grid,
                            "n1": n1, "n2": n2, "octs": octs, "score": round(sc, 4)}
    json.dump(best, open(f"{OUT}/best_{idx:02d}.json", "w"))
    print(f"[{idx}] {nm} s{seed}: n1={best['n1']} n2={best['n2']} oct={best['octs']} score={best['score']}")


def build_gif(b, pal, out, K=900, OUTRES=460, dur=7, fps=14, maxcolors=80):
    d = np.load(f"{OUT}/src_{b['idx']:02d}.npz"); V = d["V"].astype(np.float32)
    kal = Kal(K, int(d["grid"]))
    rgb = colorize(compound(kal, V, b["n1"], b["n2"], b["octs"]), pal)
    big = Image.fromarray(rgb)
    fd = "/tmp/mxgif"; os.makedirs(fd, exist_ok=True)
    for f in glob.glob(fd + "/*.png"):
        os.remove(f)
    N = dur * fps
    for fi in range(N):
        p = fi / N
        ang = 360.0 * p                         # full turn -> seamless
        zoom = 1.0 + 0.05 * np.sin(2 * np.pi * p)
        im = big.rotate(ang, resample=Image.BICUBIC, expand=False)
        half = (K / zoom) / 2.0; c = K / 2.0
        im = im.crop((c - half, c - half, c + half, c + half)).resize((OUTRES, OUTRES), Image.BICUBIC)
        im.save(f"{fd}/{fi:04d}.png")
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-framerate", str(fps),
                    "-i", f"{fd}/%04d.png", "-vf", f"palettegen=max_colors={maxcolors}:stats_mode=diff",
                    "/tmp/mxpal.png"], check=True)
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-framerate", str(fps),
                    "-i", f"{fd}/%04d.png", "-i", "/tmp/mxpal.png",
                    "-lavfi", "paletteuse=dither=bayer:bayer_scale=4", "-loop", "0", out], check=True)
    print(f"  GIF -> {out} ({os.path.getsize(out)/1e6:.1f} MB, {OUTRES}px {dur}s {fps}fps)")


def render():
    bests = [json.load(open(f)) for f in glob.glob(f"{OUT}/best_*.json")]
    bests.sort(key=lambda b: -b["score"])
    top = bests[:6]
    pals = ["nebula", "ice", "fire", "amethyst", "aqua", "emerald"]
    os.makedirs("media", exist_ok=True)
    print("top champions:")
    for i, b in enumerate(top):
        d = np.load(f"{OUT}/src_{b['idx']:02d}.npz"); V = d["V"].astype(np.float32)
        kal = Kal(2160, int(d["grid"]))
        img = colorize(compound(kal, V, b["n1"], b["n2"], b["octs"]), pals[i % len(pals)])
        Image.fromarray(img).save(f"media/mx_{i}_{b['regime']}_{b['n1']}x{b['n2']}.jpg", quality=92)
        print(f"  #{i} {b['regime']} {b['n1']}x{b['n2']} oct{b['octs']} score={b['score']} ({pals[i%len(pals)]})")
    build_gif(top[0], "nebula", "media/mandala_x.gif")
    json.dump({"champions": top}, open("discovery/mandalax_top.json", "w"), indent=2)
    print("DONE — 6 stills @2160 + seamless GIF")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", type=int, default=-1)
    ap.add_argument("--render", action="store_true")
    a = ap.parse_args()
    if a.render:
        render()
    elif a.worker >= 0:
        worker(a.worker)
    else:
        ap.error("need --worker N or --render")


if __name__ == "__main__":
    main()
